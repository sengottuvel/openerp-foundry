from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
from datetime import date

class kg_brandmoc_rate(osv.osv):

	_name = "kg.brandmoc.rate"
	_description = "Brand Moc Rate Master"
	
	def _get_modify(self, cr, uid, ids, field_name, arg,  context=None):
		res={}		
		if field_name == 'modify':
			for h in self.browse(cr, uid, ids, context=None):
				res[h.id] = 'no'
				if h.state == 'approved':
					cr.execute(""" select * from 
					(SELECT tc.table_schema, tc.constraint_name, tc.table_name, kcu.column_name, ccu.table_name
					AS foreign_table_name, ccu.column_name AS foreign_column_name
					FROM information_schema.table_constraints tc
					JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
					JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
					WHERE constraint_type = 'FOREIGN KEY'
					AND ccu.table_name='%s')
					as sam  """ %('kg_brandmoc_rate'))
					data = cr.dictfetchall()	
					if data:
						for var in data:
							data = var
							chk_sql = 'Select COALESCE(count(*),0) as cnt from '+str(data['table_name'])+' where '+data['column_name']+' = '+str(ids[0])							
							cr.execute(chk_sql)			
							out_data = cr.dictfetchone()
							if out_data:								
								if out_data['cnt'] > 0:
									res[h.id] = 'no'
									return res
								else:
									res[h.id] = 'yes'
				else:
					res[h.id] = 'no'	
		return res	
	
	_columns = {
			
		'product_id': fields.many2one('product.product','Product Name', required=True),
		'uom_id': fields.many2one('product.uom','UOM',required=True),
		'name': fields.char('Name'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'eff_date': fields.date('Effective date',required=True),		
		'active': fields.boolean('Active'),	
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled'),('expire','Expired')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'line_ids':fields.one2many('ch.brandmoc.rate.details', 'header_id', "Raw Materials"),
		
		
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),	
		'latest_price': fields.related('product_id','latest_price', type='float', string='Latest Price(Rs)', store=True,readonly=True),
		'category_type': fields.selection([('purchase_item','Purchase Item'),('design_item','Design Item'),('mkt_item','MKT Item')],'Category'),
		
		
		'brand_type': fields.selection([('new_brand','New'),('copy_brand','Copy')],'Type', required=True),	
		'source_brand': fields.many2one('kg.brandmoc.rate', 'Source',domain="[('category_type','!=','expire'),('category_type','=',category_type)]"),
		'copy_flag':fields.boolean('Copy Flag'),
		
		### Entry Info ###
		'crt_date': fields.datetime('Created Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'ap_rej_date': fields.datetime('Approved/Rejected Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Rejected By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.brandmoc.rate', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'eff_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),	
		'modify': 'no',
		'copy_flag' : False,
		'brand_type':'new_brand',
		
	}
	
	#~ _sql_constraints = [
	#~ 
		#~ ('product_id', 'unique(product_id)', 'Product Name must be unique per Company !!'),
		#~ 
	#~ ]
	
	def onchange_product_uom(self, cr, uid, ids, product_id, uom_id,  context=None):			
		
		prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)		
		if uom_id != prod.uom_id.id:
			if uom_id != prod.uom_po_id.id:				 			
				raise osv.except_osv(
					_('UOM Mismatching Error !'),
					_('You choosed wrong UOM and you can choose either %s or %s for %s !!!') % (prod.uom_id.name,prod.uom_po_id.name,prod.name))	

		return True	
		
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			if rec.product_id:
				for item in rec.line_ids:
					brand_rec = self.pool.get('kg.brand.master').browse(cr,uid,item.brand_id.id)				
					sql_check = """ select brd_id,prod_id from prod_brnd where brd_id=%s and prod_id=%s""" %(brand_rec.id,rec.product_id.id)
					cr.execute(sql_check)
					data = cr.dictfetchall()
					
					if data:
						sql = """ delete from prod_brnd where brd_id =%s and prod_id=%s """ %(brand_rec.id,rec.product_id.id)
						cr.execute(sql)
					else:				
						#~ self.pool.get('kg.brand.master').write(cr,uid,brand_rec.id,{'product_ids':[(6, 0, [rec.product_id.id])]})				
						pass
			if rec.cancel_remark:
				self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Cancel remark is must !!'),
					_('Enter the remarks in Cancel remarks field !!'))
		return True
		
	def onchange_product(self, cr, uid, ids, product_id, context=None):		
		value = {'name': '',}
		if product_id:
			pro_rec = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			value = {'name': pro_rec.name_template,}			
		return {'value': value}
		
	def copy_brand(self, cr, uid, ids, context=None):	
		
		rec = self.browse(cr,uid,ids[0])
		brand_rate_line_obj = self.pool.get('ch.brandmoc.rate.details')			
		cr.execute(""" delete from ch_brandmoc_rate_details where header_id  = %s """ %(ids[0]))			
		for brand_rate_line_item in rec.source_brand.line_ids:			
			vals = {
				'header_id' : ids[0]
				}			
			copy_rec = brand_rate_line_obj.copy(cr, uid, brand_rate_line_item.id,vals, context) 	
		
		self.write(cr, uid, ids[0], {'copy_flag': True,	})		
		
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			if not rec.line_ids:
				raise osv.except_osv(_('Line Item Details !!'),
				_('Enter the Brand MOC Rate Details !!'))
				
			prod = self.pool.get('product.product').browse(cr, uid, rec.product_id.id, context=context)		
			if rec.uom_id.id != prod.uom_id.id:
				if rec.uom_id.id != prod.uom_po_id.id:				 			
					raise osv.except_osv(
						_('UOM Mismatching Error !'),
						_('You choosed wrong UOM and you can choose either %s or %s for %s !!!') % (prod.uom_id.name,prod.uom_po_id.name,prod.name))		
			#~ pro_ids = self.search(cr,uid,[('product_id','=',rec.product_id.id),('state','!=','expire')])		
			#~ if pro_ids:	
				#~ raise osv.except_osv(_('Same product !!'),
					#~ _('Enter the same product not allow!!'))	
						
			
				
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			obj_ids = self.search(cr,uid,[('product_id','=',rec.product_id.id),('id','!=',rec.id),('state','=','approved')])
			if obj_ids:
				obj_rec = self.browse(cr,uid,obj_ids[0])
				print"obj_rec",obj_rec.id
				for item in obj_rec.line_ids:
					#~ obj_rec = self.browse(cr,uid,obj_ids[0])
					print"item.brand_id.id",item.brand_id.id
					brand_rec = self.pool.get('kg.brand.master').browse(cr,uid,item.brand_id.id)
					print"brand_rec.id",brand_rec.id			
					sql_check = """ select brd_id,prod_id from prod_brnd where brd_id=%s and prod_id=%s""" %(brand_rec.id,obj_rec.product_id.id)
					cr.execute(sql_check)
					data = cr.dictfetchall()
					
					if data:
						sql = """ delete from prod_brnd where brd_id =%s and prod_id=%s """ %(brand_rec.id,obj_rec.product_id.id)
						cr.execute(sql)
					else:				
						#~ self.pool.get('kg.brand.master').write(cr,uid,brand_rec.id,{'product_ids':[(6, 0, [rec.product_id.id])]})				
						pass
				
				self.write(cr,uid,obj_rec.id,{'state':'expire'})
			if rec.product_id:
				for item in rec.line_ids:
					if item.brand_id.id:
						brand_rec = self.pool.get('kg.brand.master').browse(cr,uid,item.brand_id.id)				
						sql_check = """ select brd_id,prod_id from prod_brnd where brd_id=%s and prod_id=%s""" %(brand_rec.id,rec.product_id.id)
						cr.execute(sql_check)
						data = cr.dictfetchall()
						
						if data:
							pass
						else:				
							#~ self.pool.get('kg.brand.master').write(cr,uid,brand_rec.id,{'product_ids':[(6, 0, [rec.product_id.id])]})				
							sql = """ insert into prod_brnd (brd_id,prod_id) VALUES(%s,%s) """ %(brand_rec.id,rec.product_id.id)
							cr.execute(sql)
					else:
						pass
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_reject(self,cr,uid,ids,context=None):		
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			if rec.product_id:
				for item in rec.line_ids:
					brand_rec = self.pool.get('kg.brand.master').browse(cr,uid,item.brand_id.id)				
					sql_check = """ select brd_id,prod_id from prod_brnd where brd_id=%s and prod_id=%s""" %(brand_rec.id,rec.product_id.id)
					cr.execute(sql_check)
					data = cr.dictfetchall()
					
					if data:
						sql = """ delete from prod_brnd where brd_id =%s and prod_id=%s """ %(brand_rec.id,rec.product_id.id)
						cr.execute(sql)
					else:				
						#~ self.pool.get('kg.brand.master').write(cr,uid,brand_rec.id,{'product_ids':[(6, 0, [rec.product_id.id])]})				
						pass
			if rec.remark:
				self.write(cr, uid, ids, {'state': 'draft','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Rejection remark is must !!'),
					_('Enter the remarks in rejection remark field !!'))
		return True
	
	
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state not in ('draft','cancel'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	def create(self, cr, uid, vals, context=None):
		product_obj = self.pool.get('product.product')
		if vals.get('product_id'):		  
			product_rec = product_obj.browse(cr, uid, vals.get('product_id') )
			latest_price = product_rec.latest_price
			vals.update({'latest_price': latest_price})
		return super(kg_brandmoc_rate, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		product_obj = self.pool.get('product.product')
		if vals.get('product_id'):		  
			product_rec = product_obj.browse(cr, uid, vals.get('product_id') )
			latest_price = product_rec.latest_price
			vals.update({'latest_price': latest_price})
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_brandmoc_rate, self).write(cr, uid, ids, vals, context)
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		eff_date = rec.eff_date
		eff_date = str(eff_date)
		eff_date = datetime.strptime(eff_date, '%Y-%m-%d')
		if eff_date > today:
			return False
		return True
	
	
	_constraints = [		
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),   
		
		
	   ]	
	
		
kg_brandmoc_rate()



class ch_brandmoc_rate_details(osv.osv):
	
	_name = "ch.brandmoc.rate.details"
	_description = "Brand MOC Rate Details Master"
	
	_columns = {
		
		'name': fields.char('Name'),
		'header_id':fields.many2one('kg.brandmoc.rate', 'Brand MOC Entry', required=True, ondelete='cascade'),	
		'brand_id': fields.many2one('kg.brand.master','Brand'),			
		'moc_id':fields.many2one('kg.moc.master','MOC'),	
		'rate':fields.float('Design Rate(Rs)',required=True),
		'purchase_price':fields.float('Purchase Price(Rs)',readonly=True),
		'remarks':fields.text('Remarks'),		
	}
	
	
	def onchange_moc(self, cr, uid, ids, moc_id):
		value = {'name':''}
		if moc_id:
			moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
			value = {'name': moc_rec.name}
		return {'value': value}
		
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.rate <= 0.00:
			return False
		return True	
	
	
	def _check_brand_moc(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])		
		cr.execute("""select id,brand_id,moc_id from ch_brandmoc_rate_details where header_id = %s"""%(entry.header_id.id))
		line_data = cr.dictfetchall()
		for line in line_data :			
			for sub_line in line_data:				
				if line['id'] == sub_line['id']:					
					pass
				else:
					if ((line['brand_id'] == sub_line['brand_id']) and (line['moc_id'] == sub_line['moc_id'])):						
						return False
		return True	
			
			
	_constraints = [		
			  
		(_check_brand_moc, 'System not allow to same Brand and MOC..!!',['Brand MOC Details']),	
		(_check_values, 'System not allow to save negative and zero values..!!',['Design Rate']),
		
	   ]
	   
ch_brandmoc_rate_details()
