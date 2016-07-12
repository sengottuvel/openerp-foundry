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
	
	"""
	def _get_modify(self, cr, uid, ids, field_name, arg, context=None):
		res={}
		enq_obj = self.pool.get('purchase.order')			
		for item in self.browse(cr, uid, ids, context=None):
			res[item.id] = 'no'
			enq_ids = enq_obj.search(cr,uid,[('mode_of_dispatch','=',item.id)])			
			if enq_ids:
				res[item.id] = 'yes'		
		return res
	"""
	
	_columns = {
			
		'name': fields.char('Name', required=True, select=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'code': fields.char('Code', size=128,required=True),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'access_type': fields.selection([('new','NEW'),('copy','COPY')],'Type',required=True),
		'accessories_type': fields.selection([('bot','BOT'),('fabrication','Fabrication'),('foundry','Foundry')],'Accessories Type',required=True),
		'access_id': fields.many2one('kg.accessories.master','Source Accessories',domain="[('active','=',True),('state','=','approved')]"),
		'line_ids': fields.one2many('ch.kg.accessories.master','header_id','Line Details',readonly=False,states={'approved':[('readonly',True)]}),
		'copy_flag':fields.boolean('Copy Flag'),		
		
		#'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),
		
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
		#'modify': 'no',
		
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



class ch_kg_accessories_master(osv.osv):
	
	_name = 'ch.kg.accessories.master'
	
	_columns = {
		
		'header_id':fields.many2one('kg.accessories.master', 'Accessories No', required=True, ondelete='cascade'),  
		'product_id': fields.many2one('product.product','Item Name', required=True,domain="[('state','not in',('reject','cancel'))]"), 		
		'brand_id': fields.many2one('kg.brand.master','Brand', domain="[('state','not in',('reject','cancel'))]"), 		
		'moc_id': fields.many2one('kg.moc.master','MOC', domain="[('state','not in',('reject','cancel'))]"), 		
		'uom_id': fields.many2one('product.uom','UOM'),
		'uom_conversation_factor': fields.selection([('one_dimension','One Dimension'),('two_dimension','Two Dimension')],'UOM Conversation Factor'),
		'length': fields.float('Length'),
		'breadth': fields.float('Breadth'),
		'qty': fields.float('Qty',required=True),
		'remark': fields.text('Remarks'),
		
	}
	
	def onchange_uom(self, cr, uid, ids, product_id, context=None):
		value = {'uom_id': '','uom_conversation_factor':''}
		if product_id:
			prod_rec = self.pool.get('product.product').browse(cr,uid,product_id)
			print"prod_rec.uom_po_id.id",prod_rec.uom_po_id.id
			value = {'uom_id': prod_rec.uom_po_id.id,'uom_conversation_factor':prod_rec.uom_conversation_factor}
		return {'value': value}
	
	def _check_length(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.uom_conversation_factor == 'two_dimension':
			if rec.length <= 0.00:
				return False
		return True
		
	def _check_breadth(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.uom_conversation_factor == 'two_dimension':
			if rec.breadth <= 0.00:
				return False
		return True
		
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False
		return True
	
	def _check_item(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])		
		cr.execute("""select id,product_id from ch_kg_accessories_master where header_id = %s"""%(rec.header_id.id))
		line_data = cr.dictfetchall()
		for line in line_data :			
			for sub_line in line_data:				
				if line['id'] == sub_line['id']:					
					pass
				else:
					if line['product_id'] == sub_line['product_id']:						
						return False
		return True	
			
	_constraints = [
	
		(_check_qty,'You cannot save with zero qty !',['Qty']),
		(_check_length,'You cannot save with zero length !',['Length']),
		(_check_breadth,'You cannot save with zero breadth !',['Breadth']),
		(_check_item,'System not allow to same Item !',['Raw Material Details']),	
		
		]
			
ch_kg_accessories_master()


