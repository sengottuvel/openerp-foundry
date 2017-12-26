import math
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import netsvc
import urllib
import urllib2
import time
import datetime
from datetime import date
from datetime import datetime
import logging

UOM_CONVERSATION = [
    ('one_dimension','One Dimension'),('two_dimension','Two Dimension')
]

class kg_stock_movement(osv.osv):
	
	_name = 'kg.stock.movement'
	_description = "This form is to track the Stock movement"
	_order = "date desc"
	
	_columns = {
		
		## Basic Info
		
		'name': fields.char('No'),
		'date': fields.date('Date'),
		'state': fields.selection([('draft','Draft'),('confirm','Waiting for approval'),('approved','Approved'),('reject','Rejected')],'Status', readonly=True),
		'remark': fields.text('Remarks'),
		
		## Module Requirement Info
		
		'process_type': fields.selection([('excess_sub2main','Excess Return'),('damage_fromsub','Damage Return From SS'),('damage_frommain','Damage Return From MS'),('purchase_frommain','Purchase Return From MS'),('purchase_fromsub','Purchase Return From SS'),('stock_transfer','Stock Transfer'),('gp_frommain','Gate Pass From MS'),('gp_fromsub','Gate Pass From SS')],'Process Type',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'sub_location': fields.many2one('stock.location','Main Store',domain = [('location_type','=','main'),('state','=','approved')],readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'main_location': fields.many2one('stock.location','Main Store',domain = [('location_type','=','main'),('state','=','approved')],readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'sub_location1': fields.many2one('stock.location','Main Store',domain = [('location_type','=','main'),('state','=','approved')],readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'scrap_location': fields.many2one('stock.location','Scrap Store',domain = [('usage','=','scrap'),('state','=','approved')],readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'supplier_location': fields.many2one('stock.location','Supplier Store',domain = [('usage','=','supplier'),('state','=','approved')],readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'from_location': fields.many2one('stock.location','From Location',domain="[('state','=','approved')]"),
		'to_location': fields.many2one('stock.location','To Location',domain="[('state','=','approved')]"),
		'location_dest_code': fields.char('Location Code'),
		
		## Child Tables Declaration
		
		'line_ids': fields.one2many('ch.stock.movement','header_id','Stock Activity'),
		
		## Entry Info
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'crt_date': fields.datetime('Created Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Approved By', readonly=True),  
		'reject_date': fields.datetime('Rejected Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		
	}
	
	_defaults = {
		
		'active': True,
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.stock.movement', context=c),			
		'state': 'draft',
		'date': lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		
	}
	
	def onchange_main_location(self, cr, uid, ids, location_dest_code, context=None):
		value = {'main_location': ''}
		if location_dest_code:
			loc_ids = self.pool.get('stock.location').search(cr, uid,[('code','=',location_dest_code)])
			if loc_ids:
				loc_rec = self.pool.get('stock.location').browse(cr, uid, loc_ids[0])
				value = {'main_location':loc_rec.id}
		return {'value': value}
	
	def onchange_location(self, cr, uid, ids, process_type,sub_location,main_location,scrap_location,sub_location1,supplier_location):
		value = {'from_location':False,'to_location':False}
		if process_type == 'excess_sub2main':
			from_location = sub_location
			to_location = main_location
			
		elif process_type == 'damage_fromsub':
			from_location = sub_location
			to_location = scrap_location
			
		elif process_type == 'damage_frommain':
			from_location = main_location
			to_location = scrap_location
			
		elif process_type == 'purchase_frommain':
			from_location = main_location
			to_location = supplier_location
			
		elif process_type == 'purchase_fromsub':
			from_location = sub_location
			to_location = supplier_location
			
		elif process_type == 'stock_transfer':
			from_location = sub_location
			to_location = sub_location1
			
		elif process_type == 'gp_frommain':
			from_location = main_location
			to_location = supplier_location
								
		elif process_type == 'gp_fromsub':
			from_location = sub_location
			to_location = supplier_location
		value = {'from_location':from_location,'to_location':to_location}
		
		return {'value': value}
	
	def load_item(self,cr,uid,ids,context=None):
		rec = self.browse(cr, uid, ids[0])
		lot_obj = self.pool.get('stock.production.lot')
		
		from_location = rec.from_location.id
		to_location = rec.to_location.id
		
		## checking stock based on location
		
		for item in rec.line_ids:
			received_qty = 0.00
			pending_qty = 0.00
			product_id = item.product_id.id
			
			out_sql = """ select 
						Sum(case when type = 'in'
						then qty else 0 end) as in_qty,
						Sum(case when type = 'out'
						then qty else 0 end) as out_qty
						from (
						(select sum(product_qty) as qty,'in' as type from stock_move where product_id=%s and state='done' and location_dest_id =%s)
						union
						(select sum(product_qty) as qty ,'out' as type from stock_move where product_id=%s and state='done' and location_id =%s)) as main"""%(product_id,from_location,product_id,from_location)
			cr.execute(out_sql)
			out_data = cr.dictfetchall()
			
			if  not out_data:
				diff = 0
				received = 0
			else:
				in_qty = out_data[0]['in_qty'] or 0
				out_qty = out_data[0]['out_qty'] or 0
				diff = in_qty - out_qty
				received = in_qty
			
			received_qty =  received
			pending_qty =   diff
			
			if  pending_qty <= 0:
				raise osv.except_osv(_('Stock not available for product'),_('%s')%(item.product_id.name))   
			if  pending_qty < item.return_qty :
				raise osv.except_osv(_('Return qty should not be greater than Available Qty for product'),
					_('%s')%(item.product_id.name))
			
			if 	rec.process_type in ('damage_frommain','purchase_frommain','gp_frommain'):
				sql = """ select lot_id from m2m_item_return_details where movement_line_id=%s""" %(item.id)
				cr.execute(sql)
				data = cr.dictfetchall()
				if not data:
					raise osv.except_osv(_('No GRN Entry !!'),
						_('There is no GRN reference for this transaction. You must associate GRN entries for Product %s.' %(item.product_id.name_template)))
				else:
					val = [d['lot_id'] for d in data if 'lot_id' in d]
					tot = 0.0
					for i in val:
						lot_rec = lot_obj.browse(cr, uid, i)
						tot += lot_rec.pending_qty
					if tot < item.return_qty:
						raise osv.except_osv(_('Stock not available !!'),
							_('Associated GRN have less Qty compare to Return Qty for Product %s.' %(item.product_id.name_template)))
					else:
						pass
		
		##  stock checking ends here
		
		self.write(cr, uid, ids, {'state': 'draft','from_location': from_location,'to_location': to_location})
		
		return True
	
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True
	
	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.state == 'draft':
			self.load_item(cr, uid, ids,context=None)
			process_type = rec.process_type
			seq_name = ''
			if not rec.name:
				if process_type == 'excess_sub2main':
					seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.stock.movement')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,rec.date))
					
				elif process_type == 'damage_fromsub':
					seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.stock.movement.damage.fromsub')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,rec.date))
					
				elif process_type == 'damage_frommain':
					seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.stock.movement.damage.fm')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,rec.date))
					
				elif process_type == 'purchase_frommain':
					seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.stock.movement.po.frommain')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,rec.date))
					
				elif process_type == 'purchase_fromsub':
					seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.stock.movement.po.fromsub')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,rec.date))
					
				elif process_type == 'stock_transfer':
					seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.stock.movement.stock.transfer')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,rec.date))
					
				elif process_type == 'gp_frommain':
					seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.stock.movement.gp.frommain')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,rec.date))
					
				elif process_type == 'gp_fromsub':
					seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.stock.movement.gp.fromsub')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,rec.date))
				
				seq_name = cr.fetchone();
			
			self.write(cr, uid, ids, {'state': 'confirm','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'name':seq_name[0]})
		return True
	
	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.state == 'confirm':
			self.load_item(cr, uid, ids,context=None)
			lot_obj = self.pool.get('stock.production.lot')
			
			from_location = rec.from_location.id
			to_location = rec.to_location.id
			process_type = rec.process_type
			
			for line in rec.line_ids:
				
				move_type = ''
				lot_updation = ''
				
				if process_type == 'excess_sub2main':
					move_type = 'in'
					lot_updation = 'not_applicable'
					
				elif process_type == 'damage_fromsub':
					move_type = 'out'
					lot_updation = 'not_applicable'
					
				elif process_type == 'damage_frommain':
					move_type = 'out'
					lot_updation = 'applicable'
					
				elif process_type == 'purchase_frommain':
					move_type = 'out'
					lot_updation = 'applicable'
					
				elif process_type == 'purchase_fromsub':
					move_type = 'out'
					lot_updation = 'not_applicable'
					
				elif process_type == 'stock_transfer':
					move_type = 'out'
					lot_updation = 'not_applicable'
					
				elif process_type == 'gp_frommain':
					move_type = 'out'
					lot_updation = 'applicable'
					
				elif process_type == 'gp_fromsub':
					move_type = 'out'
					lot_updation = 'not_applicable'
				
				if line.length == 0.00:
					line_length = 1
				else:
					line_length = line.length
				if line.breadth == 0.00:
					line_breadth = 1
				else:
					line_breadth = line.breadth
				if line.product_id.uom_id == line.uom_id:
					store_uom_stk_qty = line.grn_qty * line_length * line_breadth
					po_uom_stk_qty = line.grn_qty * line_length * line_breadth / line.product_id.po_uom_coeff
				elif line.product_id.uom_id != line.uom_id:
					po_uom_stk_qty = line.grn_qty * line_length * line_breadth
					store_uom_stk_qty = line.grn_qty * line_length * line_breadth * line.product_id.po_uom_coeff
				else:
					po_uom_stk_qty = line.grn_qty
					store_uom_stk_qty = line.grn_qty
				
				## move creation
				
				form_vals = {
						#~ 'product_id':line.product_id.id,
						#~ 'product_uom':line.uom.id,
						#~ 'product_uos':line.uom.id,
						#~ 'product_qty':line.return_qty,
						#~ 'product_uos_qty':line.return_qty,
						#~ 'name':line.product_id.name,
						#~ 'location_id':from_location,
						#~ 'location_dest_id':to_location,
						#~ 'state':'done',
						#~ 'move_type':move_type,
						#~ 'return_id':rec.id,
						#~ 'return_line_id':line.id,
						#~ 'stock_rate':line.price_unit,
						#~ 'price_unit':line.price_unit,
						#~ 'stock_uom':line.uom.id,
						#~ 'po_to_stock_qty':line.return_qty,
						
						'stock_move_id': rec.id,
						'product_id': line.product_id.id,
						'brand_id': line.brand_id.id,
						'moc_id': line.moc_id.id,
						'name': line.product_id.name,
						'product_qty': store_uom_stk_qty,
						'po_to_stock_qty': po_uom_stk_qty,
						'stock_uom': line.product_id.uom_id.id,
						'product_uom': line.product_id.uom_po_id.id,
						'location_id': from_location,
						'location_dest_id': to_location,
						'move_type': move_type,
						'state': 'done',
						'price_unit': line.price_unit or 0.0,
						'origin': 'Issue Return',
						'stock_rate': line.price_unit or 0.0,
						'uom_conversation_factor': line.uom_conversation_factor,
						'trans_date': rec.date,
					
					}
				if form_vals:
					self.pool.get('stock.move').create(cr,uid,form_vals,context=None)
				
				## lot creation
				
				if move_type == 'in':
					lot_vals = {
						#~ 'product_id':line.product_id.id,
						#~ 'product_uom':line.uom.id,
						#~ 'po_uom':line.uom.id,
						#~ 'price_unit':line.price_unit,
						#~ 'price_unit':line.price_unit,
						#~ 'product_qty':line.return_qty,
						#~ 'pending_qty':line.return_qty,
						#~ 'issue_qty':line.return_qty,
						#~ 'grn_type':'material',
						#~ 'lot_type':'in',
						#~ 'name':'Return',
						#~ 'date':rec.date,
						#~ 'grn_no':'Return',
						#~ 'batch_no':'Return',
						
						'grn_no':line.header_id.name,
						'product_id':line.product_id.id,
						'brand_id':line.brand_id.id,
						'moc_id':line.moc_id.id,
						'po_uom':line.product_id.uom_po_id.id,
						'product_uom':line.product_id.uom_id.id,
						'location_id':to_location,
						'location_code': rec.to_location.code,
						'po_product_qty':po_uom_stk_qty,
						'product_qty':store_uom_stk_qty,
						'pending_qty':po_uom_stk_qty,
						'store_pending_qty':store_uom_stk_qty,
						'issue_qty':0.00,
						'batch_no':line.header_id.name,
						'price_unit':line.price_unit or 0.0,
						'grn_type':'material',
						'reserved_qty': 0.00,
						'trans_date': rec.date,
						
					}
					if lot_vals:
						self.pool.get('stock.production.lot').create(cr,uid,lot_vals,context=None)
				
				## lot updation
				
				if lot_updation == 'applicable':
					sql = """ select lot_id from m2m_item_return_details where movement_line_id=%s""" %(line.id)
					cr.execute(sql)
					data = cr.dictfetchall()
					if not data:
						raise osv.except_osv(_('No GRN Entry !'),
							_('There is no GRN reference for this transaction. You must associate GRN entries for Product %s.' %(line.product_id.name_template)))
					else:
						val = [d['lot_id'] for d in data if 'lot_id' in d]
						tot = 0.0
						for i in val:
							lot_rec = lot_obj.browse(cr, uid, i)
							tot += lot_rec.pending_qty
						if tot < line.return_qty:
							raise osv.except_osv(_('Stock not available !'),
								_('Associated GRN have less Qty compare to Return Qty for Product %s.' %(line.product_id.name_template)))
						else:
							pass
					
					if data:
						val = [d['lot_id'] for d in data if 'lot_id' in d]
						issue_qty = line.return_qty
						for i in val:
							lot_rec = lot_obj.browse(cr,uid,i)
							move_qty = issue_qty
							if move_qty > 0 and move_qty <= lot_rec.pending_qty:
								#move_qty = move_qty - lot_rec.issue_qty
								lot_pending_qty = lot_rec.pending_qty - move_qty
								lot_rec.write({'pending_qty': lot_pending_qty,'issue_qty': 0.0})
								break
							else:
								if move_qty > 0:
									lot_pending_qty = lot_rec.pending_qty
									remain_qty =  move_qty - lot_pending_qty
									lot_rec.write({'pending_qty': 0.0})
								else:
									pass
					else:
						pass
			self.write(cr, uid, ids, {'state':'approved','app_user_id':uid,'approve_date':time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirm':
			if rec.remark:
				self.write(cr, uid, ids, {'state':'reject','rej_user_id':uid,'reject_date':time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Warning !'),_('Enter the remarks in rejection remark field !!'))
		return True
	
	def _check_lineitem(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.process_type == 'stock_transfer' and rec.sub_location.id == rec.sub_location1.id:
			raise osv.except_osv(_('Warning !'),_('Same Stores not accepted !!'))
		if not rec.line_ids:
			return False
		for line in rec.line_ids:
			if line.return_qty <= 0:
				raise osv.except_osv(_('Warning !'),_('Return Qty should be greater than zero for product %s !!')%(line.product_id.name))
		
		return True
	
	def unlink(self,cr,uid,ids,context=None):
		if context is None:
			context={}
		indent = self.read(cr, uid, ids, ['state'], context=context)
		unlink_ids = []
		for t in indent:
			if t['state'] in ('draft'):
				unlink_ids.append(t['id'])
			else:
				raise osv.except_osv(('Warning !'),('System not allow to delete a UN-DRAFT state !!'))
		osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		return True
	
	_constraints = [
					(_check_lineitem,'Please enter the Item Details',['']),
					]
	
kg_stock_movement()


class ch_stock_movement(osv.osv):
	
	_name='ch.stock.movement'
	_description='This is used to track Stock movement'
	
	_columns={
	
		'header_id': fields.many2one('kg.stock.movement','Stock Movement No', ondelete='cascade'),
		'product_id': fields.many2one('product.product','Product',domain = [('state','=','approved')]),
		'brand_id':fields.many2one('kg.brand.master','Brand',domain="[('product_ids','in',(product_id)),('state','=','approved')]"),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'moc_id_temp': fields.many2one('ch.brandmoc.rate.details','MOC',domain="[('brand_id','=',brand_id),('header_id.product_id','=',product_id),('header_id.state','=','approved')]"),
		'uom': fields.many2one('product.uom','UOM',domain="[('state','=','approved')]",required=True),
		'uom_conversation_factor': fields.selection(UOM_CONVERSATION,'UOM Conversation Factor',required=True),
		'uom_category': fields.selection([('length','Length'),('other','Others')],'UOM Category',required=True),
		'qty': fields.float('Received Qty', required=True),
		'length': fields.float('Length',digits=(16,4)),
		'breadth': fields.float('Breadth',digits=(16,4)),
		'pending_qty': fields.float('Available Qty'),
		'return_qty': fields.float('Return Qty'),
		'price_unit': fields.float('Unit Price'),
		'process_type': fields.selection([('excess_sub2main','Excess Return From SS To MS'),('damage_fromsub','Damage Return From SS'),('damage_frommain','Damage Return From MS'),('purchase_frommain','Purchase Return From MS'),('purchase_fromsub','Purchase Return From SS'),('stock_transfer','Stock Transfer'),('gp_frommain','Gate Pass From MS'),('gp_fromsub','Gate Pass From SS')],'Process Type'),
		'from_location': fields.many2one('stock.location','From Location',domain="[('state','=','approved')]"),
		'to_location': fields.many2one('stock.location','To Location',domain="[('state','=','approved')]"),
		'kg_grn_moves': fields.many2many('stock.production.lot','m2m_item_return_details','movement_line_id','lot_id','GRN Entry',
					domain="[('product_id','=',product_id),'&',('pending_qty','>',0),'&',('lot_type','!=','out')]",
					),
		'remark': fields.text('Remarks'),
	
	}
	
	_defaults = {
	
	}
	
	def default_get(self, cr, uid, fields, context=None):
		print "-------------------------",context
		return context
	
	def onchange_product_id(self,cr,uid,ids,product_id,uom,process_type,from_location,to_location,context=None):
		value = {'uom': '','qty':'','pending_qty':'','price_unit':'','brand_id':'','moc_id_temp':'','uom_category':'','uom_conversation_factor':''}
		received_qty = 0
		pending_qty = 0
		print"from_locationfrom_location",from_location
		if not from_location or not to_location:
			raise osv.except_osv(_('Warning !'),_('Kindly enter the store details !!'))
		else:
			out_sql = """ select 
						Sum(case when type = 'in'
						then qty else 0 end) as in_qty,
						Sum(case when type = 'out'
						then qty else 0 end) as out_qty
						from (
						(select sum(product_qty) as qty,'in' as type from stock_move where product_id = %s and state='done' and location_dest_id = %s)
						union
						(select sum(product_qty) as qty,'out' as type from stock_move where product_id = %s and state='done' and location_id = %s)) as main"""%(product_id,from_location,product_id,from_location)
			cr.execute(out_sql)
			out_data = cr.dictfetchall()
			print 	"-------------------------------",out_data
			if  not out_data:
				diff = 0
				received = 0
			else:
				in_qty = out_data[0]['in_qty'] or 0
				out_qty = out_data[0]['out_qty'] or 0
				diff = in_qty - out_qty
				received = in_qty
			received_qty = received
			pending_qty = diff
			
		if pending_qty <= 0:
			raise osv.except_osv(_('Warning !'),_('Stock not available !!'))
		
		if product_id:
			prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			price_sql = """ select price_unit as price from stock_move where product_id = %s order by id desc limit 1 """%(product_id)
			cr.execute(price_sql)		   
			price_data = cr.dictfetchall()
			if price_data:
				price = price_data[0]['price'] or 0.00
			else:
				price = 0.00
			value = {'uom':prod.uom_id.id,'uom_category':prod.uom_id.uom_category,'uom_conversation_factor':prod.uom_conversation_factor,'from_location':from_location,'to_location':to_location,'qty':received_qty,'pending_qty':pending_qty,'price_unit':price}
		return {'value': value}
	
	def onchange_brand(self, cr, uid, ids, brand_id):
		value = {'moc_id_temp':''}
		if brand_id:
			value = {'moc_id_temp': ''}
		return {'value': value}
	
	def onchange_moc(self, cr, uid, ids, moc_id_temp):
		value = {'moc_id':''}
		if moc_id_temp:
			rate_rec = self.pool.get('ch.brandmoc.rate.details').browse(cr,uid,moc_id_temp)
			value = {'moc_id': rate_rec.moc_id.id}
		return {'value': value}
	
	def onchange_qty(self,cr,uid,ids,pending_qty,return_qty,context=None):
		if  pending_qty < return_qty :
			raise osv.except_osv(_('Warning !'),_('Return qty should not be greater than Available Qty !!'))
		return True
	
ch_stock_movement()
