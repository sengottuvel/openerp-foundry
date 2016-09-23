from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_accessories_master(osv.osv):

	_name = "kg.accessories.master"
	_description = "Accessories Master"
	
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
					as sam  """ %('kg_accessories_master'))
					data = cr.dictfetchall()	
					if data:
						for var in data:
							data = var
							chk_sql = 'Select COALESCE(count(*),0) as cnt from '+str(data['table_name'])+' where '+data['column_name']+' = '+str(ids[0])
							cr.execute(chk_sql)			
							out_data = cr.dictfetchone()
							if out_data:
								if out_data['cnt'] > 0:
									res[h.id] = 'yes'
									return res
								else:
									res[h.id] = 'no'
				else:
					res[h.id] = 'yes'								
		return res
	
	_columns = {
			
		'name': fields.char('Name', required=True, select=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'code': fields.char('Code', size=128),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'access_type': fields.selection([('new','NEW'),('copy','COPY')],'Type',required=True),
		'accessories_type': fields.selection([('bot','BOT'),('fabrication','Fabrication'),('foundry','Foundry')],'Accessories Type'),
		'access_id': fields.many2one('kg.accessories.master','Source Accessories',domain="[('active','=',True),('state','=','approved')]"),
		
		'line_ids': fields.one2many('ch.kg.accessories.master','header_id','BOT Line Details',readonly=False,states={'approved':[('readonly',True)]}),
		'line_ids_a':fields.one2many('ch.accessories.ms', 'header_id', "Machine Shop Line",readonly=False,states={'approved':[('readonly',True)]}),
		'line_ids_b':fields.one2many('ch.accessories.fou', 'header_id', "FOU Line",readonly=False,states={'approved':[('readonly',True)]}),
		
		'copy_flag':fields.boolean('Copy Flag'),		
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		'product_id': fields.many2one('product.product','Item Name'), 		
		
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),
		
		### Entry Info ###
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'ap_rej_date': fields.datetime('Approved/Reject Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Reject By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),		
			
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.accessories.master', context=c),
		'active': True,		
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date': fields.datetime.now,
		'access_type': 'new',
		'copy_flag' : False,
		'modify': 'yes',
		'entry_mode': 'manual',
		
	}
	
	_sql_constraints = [
	
		#~ ('name', 'unique(name)', 'Name must be unique!!'),
		('code', 'unique(code)', 'Code must be unique!!'),
		('name', 'unique(name)', 'Name must be unique!!'),
	]
	
	"""def _Validation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		name_special_char = ''.join( c for c in flds.name if  c in '!@#$%^~*{}?+/=' )		
		if name_special_char:
			return False		
		return True	
		
	def _CodeValidation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])	
		if flds.code:		
			code_special_char = ''.join( c for c in flds.code if  c in '!@#$%^~*{}?+/=' )		
			if code_special_char:
				return False
		return True		"""
		
	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.name:
			dispatch_name = rec.name
			name=dispatch_name.upper()			
			cr.execute(""" select upper(name) from kg_accessories_master where upper(name)  = '%s' """ %(name))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
			
	def _code_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.code:
			dispatch_code = rec.code
			code=dispatch_code.upper()			
			cr.execute(""" select upper(code) from kg_accessories_master where upper(code)  = '%s' """ %(code))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res	
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			for item in rec.line_ids:
				if item.entry_mode == 'auto' and item.product_id.is_accessories == True:
					self.pool.get('product.product').write(cr,uid,item.product_id.id,{'state':'cancel','remark':'Cancelled from Accessories Master'})
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True
	
	def copy_accessories(self, cr, uid, ids, context=None):
		
		rec = self.browse(cr,uid,ids[0])
		line_obj = self.pool.get('ch.kg.accessories.master')
				
		cr.execute(""" delete from ch_kg_accessories_master where header_id  = %s """ %(ids[0]))
				
		for line_item in rec.access_id.line_ids:	
			vals = {
				'header_id' : ids[0]
				}			
			copy_rec = line_obj.copy(cr, uid, line_item.id, vals, context) 
			#~ cr.execute(""" delete from kg_dimension where header_id  = %s """ %(copy_rec))
			#~ for dimension_line_item in position_line_item.line_ids:	
				#~ vals = {
					#~ 'header_id' : copy_rec
					#~ }			
				#~ copy_recs = dimension_obj.copy(cr, uid, dimension_line_item.id, vals, context) 
		
		if rec.name == rec.access_id.name:
			raise osv.except_osv(_('Warning !!'),
				_('Kindly Change Accessories !!'))
			
		self.write(cr, uid, ids[0], {
									'copy_flag': True,
									#~ 'name':rec.position_no.name,
									'notes':rec.access_id.notes,
									
									})		
									
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		
		if not rec.line_ids:
			raise osv.except_osv(_('Warning !!'),
				_('You can not save this with out Raw material Details !!'))
				
		if rec.access_type == 'copy':
			
			cr.execute('''select 
					access_line.product_id,
					access_line.brand_id,
					access_line.moc_id,
					access_line.uom_id,
					access_line.uom_conversation_factor,
					access_line.length,
					access_line.breadth,
					access_line.qty,
					access_line.remark
					from ch_kg_accessories_master access_line 
					left join kg_accessories_master header on header.id  = access_line.header_id
					where header.access_type = 'copy' and header.id = %s''',[rec.id])
			source_position_ids = cr.fetchall()
			source_position_len = len(source_position_ids)
			print"dddddddllll",source_position_len
			cr.execute('''select 
					access_line.product_id,
					access_line.brand_id,
					access_line.moc_id,
					access_line.uom_id,
					access_line.uom_conversation_factor,
					access_line.length,
					access_line.breadth,
					access_line.qty,
					access_line.remark
					from ch_kg_accessories_master access_line 
					where access_line.header_id  = %s''',[rec.access_id.id])
			source_old_position_ids = cr.fetchall()
			source_old_position_len = len(source_old_position_ids)	
			print"ddddssssssss",source_old_position_len
			cr.execute('''select 

					access_line.product_id,
					access_line.brand_id,
					access_line.moc_id,
					access_line.uom_id,
					access_line.uom_conversation_factor,
					access_line.length,
					access_line.breadth,
					access_line.qty,
					access_line.remark
					from ch_kg_accessories_master access_line 
					left join kg_accessories_master header on header.id  = access_line.header_id
					where header.access_type = 'copy' and header.id = %s

					INTERSECT

					select 
					access_line.product_id,
					access_line.brand_id,
					access_line.moc_id,
					access_line.uom_id,
					access_line.uom_conversation_factor,
					access_line.length,
					access_line.breadth,
					access_line.qty,
					access_line.remark
					from ch_kg_accessories_master access_line 
					where access_line.header_id  = %s ''',[rec.id,rec.access_id.id])
			repeat_ids = cr.fetchall()
			new_position_len = len(repeat_ids)
			print"ddddddddddddddd",new_position_len
			pos_dup = ''
			if new_position_len  == source_position_len == source_old_position_len:
				pos_dup = 'yes'
			
			if pos_dup == 'yes':
				raise osv.except_osv(_('Warning!'),
								_('Same Raw Material Details are already exist !!'))
		####################
		if rec.access_type == 'copy':
			
			obj = self.search(cr,uid,[('access_id','=',rec.access_id.id)])
			if obj:
				for item in obj:
					if rec.id != item:
						obj_rec = self.browse(cr,uid,item)
						print"aaaaaaaaaaaaaa",obj_rec.id
						
						cr.execute('''select 
								access_line.product_id,
								access_line.brand_id,
								access_line.moc_id,
								access_line.uom_id,
								access_line.uom_conversation_factor,
								access_line.length,
								access_line.breadth,
								access_line.qty,
								access_line.remark
								from ch_kg_accessories_master access_line 
								left join kg_accessories_master header on header.id  = access_line.header_id
								where header.access_type = 'copy' and header.id = %s''',[rec.id])
						source_position_ids = cr.fetchall()
						source_position_len = len(source_position_ids)
						print"source_position_len",source_position_len
						cr.execute('''select 
								access_line.product_id,
								access_line.brand_id,
								access_line.moc_id,
								access_line.uom_id,
								access_line.uom_conversation_factor,
								access_line.length,
								access_line.breadth,
								access_line.qty,
								access_line.remark
								from ch_kg_accessories_master access_line 
								where access_line.header_id  = %s''',[obj_rec.id])
						source_old_position_ids = cr.fetchall()
						source_old_position_len = len(source_old_position_ids)	
						print"source_old_position_len",source_old_position_len
						cr.execute('''select 

								access_line.product_id,
								access_line.brand_id,
								access_line.moc_id,
								access_line.uom_id,
								access_line.uom_conversation_factor,
								access_line.length,
								access_line.breadth,
								access_line.qty,
								access_line.remark
								from ch_kg_accessories_master access_line 
								left join kg_accessories_master header on header.id  = access_line.header_id
								where header.access_type = 'copy' and header.id = %s

								INTERSECT

								select 
								access_line.product_id,
								access_line.brand_id,
								access_line.moc_id,
								access_line.uom_id,
								access_line.uom_conversation_factor,
								access_line.length,
								access_line.breadth,
								access_line.qty,
								access_line.remark
								from ch_kg_accessories_master access_line 
								where access_line.header_id  = %s ''',[rec.id,obj_rec.id])
						repeat_ids = cr.fetchall()
						new_position_len = len(repeat_ids)
						print"new_position_len",new_position_len
						pos_dup = ''
						if new_position_len == source_position_len == source_old_position_len:
							pos_dup = 'yes'
						print"pos_duppos_dup",pos_dup
						if pos_dup == 'yes':
							raise osv.except_osv(_('Warning!'),
											_('Same Raw Material Details are already exist !!'))
		
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		
		if not rec.line_ids:
			raise osv.except_osv(_('Warning !!'),
				_('You can not save this with out Raw material Details !!'))
				
		self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'state': 'reject','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
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
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_accessories_master, self).write(cr, uid, ids, vals, context)
	
	def _check_line(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if not rec.line_ids:			
			return False
		return True	
	
	_constraints = [
		#(_Validation, 'Special Character Not Allowed !!!', ['Check Name']),
		#(_CodeValidation, 'Special Character Not Allowed !!!', ['Check Code']),
		(_name_validate, 'Accessories Name must be unique !!', ['Name']),		
		(_code_validate, 'Accessories code must be unique !!', ['code']),		
		#~ (_check_line,'You can not save this with out Operation Details !',['line_ids']),
		
	]
	
kg_accessories_master()


class ch_accessories_fou(osv.osv):
	
	_name = 'ch.accessories.fou'
	
	_columns = {
		
		'header_id':fields.many2one('kg.accessories.master', 'Access',ondelete='cascade'),
		'pos_no': fields.integer('Position No'),
		'position_id': fields.many2one('kg.position.number','Position No', required=True,domain="[('active','=','t')]"), 	
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No', required=True,domain="[('active','=','t')]"), 	
		'csd_no': fields.char('CSD No.', size=128),	
		'pattern_name': fields.char('Pattern Name', required=True),
		'remarks':fields.text('Remarks'),
		'qty': fields.integer('Qty',required=True,),
		'state':fields.selection([('draft','Draft'),('approve','Approved')],'Status'),
		
	}
	
	_defaults = {
	
	'state':'draft',
	'qty': 1,
	  
	}
	
	def _check_line_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute('''select id from ch_accessories_fou where pattern_id = %s and id != %s and header_id = %s ''',[entry.pattern_id.id,entry.id,entry.header_id.id])
		duplicate_id = cr.fetchone()
		if duplicate_id:
			if duplicate_id[0] != None:
				return False
		return True 
		
	def _check_line_qty(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])		
		if entry.qty <= 0:			
			return False
		return True
	
	def onchange_pattern_name(self, cr, uid, ids, pattern_id, context=None):
		value = {'pattern_name': '','csd_no':''}
		if pattern_id:
			pro_rec = self.pool.get('kg.pattern.master').browse(cr, uid, pattern_id, context=context)
			value = {'pattern_name': pro_rec.pattern_name,'csd_no':pro_rec.csd_code}
		return {'value': value}
		
	_constraints = [
		
		(_check_line_qty, 'Foundry Items Qty Zero and negative not accept', ['Qty']),	   
		
	]

	
ch_accessories_fou()


class ch_accessories_ms(osv.osv):

	_name = "ch.accessories.ms"
	_description = "Accessories Machineshop Details"
	
	_columns = {
	
		'header_id':fields.many2one('kg.accessories.master', 'Access', ondelete='cascade',required=True),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code',domain = [('type','=','ms')], ondelete='cascade',required=True),		
		'pos_no': fields.integer('Position No'),
		'position_id': fields.many2one('kg.position.number','Position No', required=True,domain="[('active','=','t')]"), 	
		'csd_no': fields.char('CSD No.'),
		'name':fields.char('Item Name', size=128),	  
		'qty': fields.integer('Qty', required=True),
		'remarks':fields.text('Remarks'),   
	
	}
	
	def onchange_machineshop_name(self, cr, uid, ids, ms_id, context=None):
		value = {'name': '','csd_no':''}
		if ms_id:
			pro_rec = self.pool.get('kg.machine.shop').browse(cr, uid, ms_id, context=context)
			value = {'name': pro_rec.name,'csd_no':pro_rec.csd_code}
		return {'value': value}
	
	def _check_line_qty(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])		
		if entry.qty <= 0:			
			return False
		return True
	
	_constraints = [
		
		(_check_line_qty, 'Machine Shop items Qty Zero and negative not accept', ['Qty']),	   
		
	]   

ch_accessories_ms()


class ch_kg_accessories_master(osv.osv):
	
	_name = 'ch.kg.accessories.master'
	
	_columns = {
		
		'header_id':fields.many2one('kg.accessories.master', 'Accessories No', required=True, ondelete='cascade'),  
		'product_id': fields.many2one('product.product','Item Name', required=True,domain="[('state','not in',('reject','cancel'))]"),
		'brand_id': fields.many2one('kg.brand.master','Brand', required=True,domain="[('state','not in',('reject','cancel'))]"), 		
		'moc_id': fields.many2one('kg.moc.master','MOC', domain="[('state','not in',('reject','cancel'))]"), 		
		'uom_id': fields.many2one('product.uom','UOM'),
		'uom_conversation_factor': fields.selection([('one_dimension','One Dimension'),('two_dimension','Two Dimension')],'UOM Conversation Factor'),
		'length': fields.float('Length'),
		'breadth': fields.float('Breadth'),
		'qty': fields.float('Qty'),
		'weight': fields.float('Weight' ,digits=(16,5)),
		'temp_qty':fields.float('Qty',required=True),
		'remark': fields.text('Remarks'),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		
		
	}
	
	_defaults = {
				'entry_mode': 'manual',
				'length': 1.00,
				
				}
				
	def onchange_product_uom(self, cr, uid, ids, product_id, uom_id,  context=None):		
		prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)		
		if uom_id != prod.uom_id.id:
			if uom_id != prod.uom_po_id.id:				 			
				raise osv.except_osv(
					_('UOM Mismatching Error !'),
					_('You choosed wrong UOM and you can choose either %s or %s for %s !!!') % (prod.uom_id.name,prod.uom_po_id.name,prod.name))	

		return True	
	
	def onchange_uom(self, cr, uid, ids, product_id, context=None):
		
		value = {'uom_id': '','uom_conversation_factor':''}
		if product_id:
			uom_rec = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			value = {'uom_conversation_factor':uom_rec.uom_conversation_factor}
			
		return {'value': value}
		
	def onchange_weight(self, cr, uid, ids, uom_conversation_factor,length,breadth,temp_qty,product_id, context=None):		
		value = {'qty': '','weight': '',}
		prod_rec = self.pool.get('product.product').browse(cr,uid,product_id)
		qty_value = 0.00
		weight=0.00
		if uom_conversation_factor == 'one_dimension':	
			if prod_rec.uom_id.id == prod_rec.uom_po_id.id:
				qty_value = temp_qty
				weight = 0.00
			else:				
				qty_value = length * temp_qty			
				weight = qty_value * prod_rec.po_uom_in_kgs
		if uom_conversation_factor == 'two_dimension':
			qty_value = length * breadth * temp_qty				
			weight = qty_value * prod_rec.po_uom_in_kgs		
		value = {'qty': qty_value,'weight':weight}			
		return {'value': value}
		
	
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(""" select product_id from ch_kg_accessories_master where product_id  = '%s' and header_id = '%s' """ %(entry.product_id.id,entry.header_id.id))
		data = cr.dictfetchall()			
		if len(data) > 1:		
			return False
		return True	
		
	def _check_one_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		prod_rec = self.pool.get('product.product').browse(cr,uid,entry.product_id.id)
		if entry.uom_conversation_factor =='one_dimension':
			if prod_rec.uom_id.id == prod_rec.uom_po_id.id:
				if entry.qty == 0:				
					return False
				return True	
			else:
				if entry.qty == 0 or entry.length == 0:				
					return False				
				return True				
		return True
		
	def _check_two_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.uom_conversation_factor =='two_dimension':
			if entry.length == 0 or entry.qty == 0 or entry.breadth == 0:				
				return False
			return True
		return True
		
	def _check_uom_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		prod = self.pool.get('product.product').browse(cr, uid, entry.product_id.id)						
		if entry.uom_id.id != prod.uom_id.id:
			if entry.uom_id.id  != prod.uom_po_id.id:
				return False			
		return True	
		
	_constraints = [		
			  
		(_check_one_values, 'Check the zero values not allowed..!!',['Qty or Length']),	
		(_check_two_values, 'Check the zero values not allowed..!!',['Breadth or Length or Qty']),
		(_check_values, 'Please Check the same Raw Material not allowed..!!',['Raw Material']),	
		(_check_uom_values, 'UOM Mismatching Error, You choosed wrong UOM !!!',['UOM']),	
		
	   ]
			
ch_kg_accessories_master()


