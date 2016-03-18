from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_moc_construction(osv.osv):

	_name = "kg.moc.construction"
	_description = "MOC Construction Master"
	
	def _get_modify(self, cr, uid, ids, field_name, arg, context=None):
		res={}
		ch_weekly_obj = self.pool.get('ch.weekly.schedule.details')			
		for item in self.browse(cr, uid, ids, context=None):
			res[item.id] = 'no'
			ch_weekly_ids = ch_weekly_obj.search(cr,uid,[('moc_construction_id','=',item.id)])			
			if ch_weekly_ids:
				res[item.id] = 'yes'		
		return res
	
	_columns = {
			
		'name': fields.char('Name', size=128, required=True, select=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'code': fields.char('Code', size=128, required=True),		
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),		
		'line_ids': fields.one2many('ch.moc.foundry.details', 'header_id', "Foundry Line"),		
		'line_ids_a':fields.one2many('ch.moc.machineshop.details', 'header_id', "Machine Shop Line"),
		'line_ids_b':fields.one2many('ch.moc.bot.details', 'header_id', "BOT Line"),
		'line_ids_c':fields.one2many('ch.moc.consu.details', 'header_id', "Consumable Line"),		
		
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		'type': fields.selection([('slurry','Slurry'),('non_slurry','Non Slurry')],'Type', required=True),
		
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.moc.construction', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':fields.datetime.now,	
		'modify': 'no',
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Name must be unique!!'),
		('code', 'unique(code)', 'Code must be unique!!'),
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
			moc_name = rec.name
			name=moc_name.upper()			
			cr.execute(""" select upper(name) from kg_moc_construction where upper(name)  = '%s' """ %(name))
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
			moc_code = rec.code
			code=moc_code.upper()			
			cr.execute(""" select upper(code) from kg_moc_construction where upper(code)  = '%s' """ %(code))
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

	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		item_lines = rec.line_ids
		if not item_lines:
			raise osv.except_osv(_('Construction Details is must !!'),
				_('Enter the Construction Details Lines field !!'))
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
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
		return super(kg_moc_construction, self).write(cr, uid, ids, vals, context)
		
	
	_constraints = [
		#(_Validation, 'Special Character Not Allowed !!!', ['Check Name']),
		#(_CodeValidation, 'Special Character Not Allowed !!!', ['Check Code']),
		(_name_validate, 'MOC Construction name must be unique !!', ['name']),		
		(_code_validate, 'MOC Construction code must be unique !!', ['code']),		
		
	]
	
kg_moc_construction()



class ch_moc_foundry_details(osv.osv):
	
	_name = 'ch.moc.foundry.details'
	
	
	_columns = {
		
		'header_id':fields.many2one('kg.moc.construction', 'MOC Construction Name', required=True, ondelete='cascade'),  		
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No', required=True,domain="[('active','=','t')]"), 
		'pattern_name': fields.char('Pattern Name', required=True), 
		'moc_id':fields.many2one('kg.moc.master','MOC',required=True,domain="[('active','=','t')]"),
		'state':fields.selection([('draft','Draft'),('approve','Approved')],'Status'),
		'remarks':fields.text('Remarks'),		
		
		
	}
	
	
	_defaults = {
	
	'state':'draft',
	  
	}
	
	
	
	def onchange_pattern_name(self, cr, uid, ids, pattern_id, context=None):
		
		value = {'pattern_name': ''}
		if pattern_id:
			pro_rec = self.pool.get('kg.pattern.master').browse(cr, uid, pattern_id, context=context)
			value = {'pattern_name': pro_rec.pattern_name}
			
		return {'value': value}
		
		
	def create(self, cr, uid, vals, context=None):
		pattern_obj = self.pool.get('kg.pattern.master')
		if vals.get('pattern_id'):		  
			pattern_rec = pattern_obj.browse(cr, uid, vals.get('pattern_id') )
			pattern_name = pattern_rec.pattern_name
			vals.update({'pattern_name': pattern_name})
		return super(ch_moc_foundry_details, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		pattern_obj = self.pool.get('kg.pattern.master')
		if vals.get('pattern_id'):
			pattern_rec = pattern_obj.browse(cr, uid, vals.get('pattern_id') )
			pattern_name = pattern_rec.pattern_name
			vals.update({'pattern_name': pattern_name})
		return super(ch_moc_foundry_details, self).write(cr, uid, ids, vals, context)  
	
	
ch_moc_foundry_details()


class ch_moc_machineshop_details(osv.osv):

	_name = "ch.moc.machineshop.details"
	_description = "MOC machineshop Details"
	
	
	_columns = {
	
		'header_id':fields.many2one('kg.moc.construction', 'MOC', ondelete='cascade',required=True),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', ondelete='cascade',required=True),
		'name':fields.char('Item Name', size=128),	
		'moc_id':fields.many2one('kg.moc.master','MOC',required=True,domain="[('active','=','t')]"),  		
		'remarks':fields.text('Remarks'),   
	
	}   
	
	def onchange_machineshop_name(self, cr, uid, ids, ms_id, context=None):
		
		value = {'name': ''}
		if ms_id:
			pro_rec = self.pool.get('kg.machine.shop').browse(cr, uid, ms_id, context=context)
			value = {'name': pro_rec.name}
			
		return {'value': value}
		
	def create(self, cr, uid, vals, context=None):	  
		ms_obj = self.pool.get('kg.machine.shop')
		if vals.get('ms_id'):		   
			ms_rec = ms_obj.browse(cr, uid, vals.get('ms_id') )
			ms_name = ms_rec.name		   
			vals.update({'name':ms_name })
		return super(ch_moc_machineshop_details, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		ms_obj = self.pool.get('kg.machine.shop')
		if vals.get('ms_id'):		   
			ms_rec = ms_obj.browse(cr, uid, vals.get('ms_id') )
			ms_name = ms_rec.name		   
			vals.update({'name':ms_name })
		return super(ch_moc_machineshop_details, self).write(cr, uid, ids, vals, context)   

ch_moc_machineshop_details()

class ch_moc_bot_details(osv.osv):
	
	_name = "ch.moc.bot.details"
	_description = "MOC BOT Details"	
	
	_columns = {
	
		'header_id':fields.many2one('kg.moc.construction', 'MOC', ondelete='cascade',required=True),
		'product_temp_id':fields.many2one('product.product', 'Item Name',domain = [('type','=','bot')], ondelete='cascade',required=True),
		'code':fields.char('Item Code', size=128),	
		'moc_id':fields.many2one('kg.moc.master','MOC',required=True,domain="[('active','=','t')]"),  		
		'remarks':fields.text('Remarks'),   
	
	}
	
	def onchange_bot_code(self, cr, uid, ids, product_temp_id, context=None):	   
		value = {'code': ''}
		if product_temp_id:
			pro_rec = self.pool.get('product.product').browse(cr, uid, product_temp_id, context=context)
			value = {'code': pro_rec.product_code}		  
		return {'value': value}
		
	def create(self, cr, uid, vals, context=None):	  
		product_obj = self.pool.get('product.product')
		if vals.get('product_temp_id'):		 
			product_rec = product_obj.browse(cr, uid, vals.get('product_temp_id') )
			product_code = product_rec.product_code		 
			vals.update({'code':product_code })
		return super(ch_moc_bot_details, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		product_obj = self.pool.get('product.product')
		if vals.get('product_temp_id'):		 
			product_rec = product_obj.browse(cr, uid, vals.get('product_temp_id') )
			product_code = product_rec.product_code
			vals.update({'code':product_code })
		return super(ch_moc_bot_details, self).write(cr, uid, ids, vals, context)   

ch_moc_bot_details()

class ch_moc_consu_details(osv.osv):
	
	_name = "ch.moc.consu.details"
	_description = "MOC Consumable Details" 
	
	_columns = {
	
		'header_id':fields.many2one('kg.moc.construction', 'MOC', ondelete='cascade',required=True),
		'product_temp_id':fields.many2one('product.product', 'Item Name',domain = [('type','=','consu')], ondelete='cascade',required=True),
		'code':fields.char('Item Code', size=128), 
		'moc_id':fields.many2one('kg.moc.master','MOC',required=True,domain="[('active','=','t')]"), 	
		'remarks':fields.text('Remarks'),
	
	}
	
	def onchange_consu_code(self, cr, uid, ids, product_temp_id, context=None):
		
		value = {'code': ''}
		if product_temp_id:
			pro_rec = self.pool.get('product.product').browse(cr, uid, product_temp_id, context=context)
			value = {'code': pro_rec.product_code}
			
		return {'value': value}
		
	def create(self, cr, uid, vals, context=None):	  
		product_obj = self.pool.get('product.product')
		if vals.get('product_temp_id'):		 
			product_rec = product_obj.browse(cr, uid, vals.get('product_temp_id') )
			product_code = product_rec.product_code		 
			vals.update({'code':product_code })
		return super(ch_moc_consu_details, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		product_obj = self.pool.get('product.product')
		if vals.get('product_temp_id'):		 
			product_rec = product_obj.browse(cr, uid, vals.get('product_temp_id') )
			product_code = product_rec.product_code
			vals.update({'code':product_code })
		return super(ch_moc_consu_details, self).write(cr, uid, ids, vals, context) 

ch_moc_consu_details()


