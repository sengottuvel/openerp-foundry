from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_moc_master(osv.osv):
	
	_name = "kg.moc.master"
	_description = "SAM MOC Master"
	
	def _get_modify(self, cr, uid, ids, field_name, arg, context=None):
		res={}
		moc_const_foundry_obj = self.pool.get('ch.moc.foundry.details')
		moc_const_ms_obj = self.pool.get('ch.moc.machineshop.details')
		moc_const_bot_obj = self.pool.get('ch.moc.bot.details')			
		moc_const_consu_obj = self.pool.get('ch.moc.consu.details')	
		stock_line_obj = self.pool.get('ch.stock.inward.details')		
		for item in self.browse(cr, uid, ids, context=None):
			res[item.id] = 'no'
			moc_const_foundry_ids = moc_const_foundry_obj.search(cr,uid,[('moc_id','=',item.id)])
			moc_const_ms_ids = moc_const_ms_obj.search(cr,uid,[('moc_id','=',item.id)])
			moc_const_bot_ids = moc_const_bot_obj.search(cr,uid,[('moc_id','=',item.id)])					
			moc_const_consu_ids = moc_const_consu_obj.search(cr,uid,[('moc_id','=',item.id)])
			stock_line_ids = stock_line_obj.search(cr,uid,[('moc_id','=',item.id)])					
			if moc_const_foundry_ids or moc_const_ms_ids or moc_const_bot_ids or moc_const_consu_ids or stock_line_ids:
				res[item.id] = 'yes'		
		return res
	
	_columns = {
			
		'name': fields.char('Name', size=128, required=True, select=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'code': fields.char('Code', size=128, required=True),
		'active': fields.boolean('Active'),
		'rate': fields.float('Design Rate(Rs)', required=True,),
		'pro_cost': fields.float('Production Cost(Rs)', required=True,),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'line_ids':fields.one2many('ch.moc.raw.material', 'header_id', "Raw Materials"),
		'line_ids_a':fields.one2many('ch.chemical.chart', 'header_id', "Chemical Chart"),
		'line_ids_b':fields.one2many('ch.mechanical.chart', 'header_id', "Mechanical Chart"),
		
		'weight_type': fields.selection([('ci','CI'),('ss','SS'),('non_ferrous','Non-Ferrous')],'Family Type'),
		'alias_name': fields.char('Alias Name', size=128),
		'moc_type': fields.selection([('foundry','Foundry'),('machine_shop','Machine Shop'),('bot','BOT')],'Type'),
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.moc.master', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':fields.datetime.now,	
		'modify': 'no',
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Name must be unique per Company !!'),
		('code', 'unique(code)', 'Code must be unique per Company !!'),
	]
	
	"""def _Validation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		special_char = ''.join( c for c in flds.name if  c in '!@#$%^~*{}?+/=' )
		if special_char:
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
			division_name = rec.name
			name=division_name.upper()			
			cr.execute(""" select upper(name) from kg_moc_master where upper(name)  = '%s' """ %(name))
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
			division_code = rec.code
			code=division_code.upper()			
			cr.execute(""" select upper(code) from kg_moc_master where upper(code)  = '%s' """ %(code))
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
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		chemical_obj = self.pool.get('kg.chemical.master')
		for item in rec.line_ids_a:			
			chemical_obj.write(cr,uid,item.chemical_id.id,{'modify': True})
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
		return super(kg_moc_master, self).write(cr, uid, ids, vals, context)
		
	
	_constraints = [
		#(_Validation, 'Special Character Not Allowed !!!', ['name']),
		#(_CodeValidation, 'Special Character Not Allowed !!!', ['Check Code']),
		(_name_validate, 'MOC name must be unique !!', ['name']),		
		(_code_validate, 'MOC code must be unique !!', ['code']),	
	]
	
kg_moc_master()


class ch_moc_raw_material(osv.osv):
	
	_name = "ch.moc.raw.material"
	_description = "SAM MOC Raw Materials Master"
	
	_columns = {
			
		'header_id':fields.many2one('kg.moc.master', 'MOC Entry', required=True, ondelete='cascade'),	
		'product_id': fields.many2one('product.product','Raw Material', required=True,domain="[('state','=','approved')]"),	
		'rate': fields.related('product_id','latest_price', type='float', string='Rate(Rs)', store=True),		
		'uom':fields.char('UOM',size=128),
		'qty':fields.float('Qty',required=True),
		'remarks':fields.text('Remarks'),		
	}
	
	def onchange_uom(self, cr, uid, ids, product_id, context=None):
		
		value = {'uom': ''}
		if product_id:
			uom_rec = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			value = {'uom': uom_rec.uom_id.name}
			
		return {'value': value}
		
	def create(self, cr, uid, vals, context=None):
		pro_obj = self.pool.get('product.product')
		if vals.get('product_id'):		  
			uom_rec = pro_obj.browse(cr, uid, vals.get('product_id') )
			uom_name = uom_rec.uom_id.name
			vals.update({'uom': uom_name})
		return super(ch_moc_raw_material, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		pro_obj = self.pool.get('product.product')
		if vals.get('product_id'):
			uom_rec = pro_obj.browse(cr, uid, vals.get('product_id') )
			uom_name = uom_rec.uom_id.name
			vals.update({'uom': uom_name})
		return super(ch_moc_raw_material, self).write(cr, uid, ids, vals, context)  
	
ch_moc_raw_material()



class ch_chemical_chart(osv.osv):
	
	_name = "ch.chemical.chart"
	_description = "Chemical Chart"
	
	_columns = {
			
		'header_id':fields.many2one('kg.moc.master', 'MOC Entry', required=True, ondelete='cascade'),				
		'chemical_id': fields.many2one('kg.chemical.master','Name', required=True,domain="[('state','=','approved')]"),		
		'min':fields.float('Min',required=True,digits_compute=dp.get_precision('Min Value')),		
		'max':fields.float('Max',required=True,digits_compute=dp.get_precision('Max Value')),	
		'range_flag': fields.boolean('Range Limit'),	
	}
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.min > entry.max:
			return False
		return True
		
	_constraints = [		
			  
		(_check_values, 'Please Check the Min & Max values ,Min value should be less than Max value.!!',['Chemical Chart']),	
		
	   ]
	
ch_chemical_chart()

class ch_mechanical_chart(osv.osv):
	
	_name = "ch.mechanical.chart"
	_description = "Mechanical Chart"
	
	_columns = {
			
		'header_id':fields.many2one('kg.moc.master', 'MOC Entry', required=True, ondelete='cascade'),
		'uom': fields.char('UOM',size=128),						
		'mechanical_id': fields.many2one('kg.mechanical.master','Name', required=True,domain="[('state','=','approved')]"),	
		'min':fields.float('Min',required=True,digits_compute=dp.get_precision('Min Value')),
		'max':fields.float('Max',required=True,digits_compute=dp.get_precision('Max Value')),
		'range_flag': fields.boolean('Max Range'),			
		
	}
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.range_flag == False:
			print"www"
			if entry.min > entry.max:
				return False
		return True
		
	def onchange_uom_name(self, cr, uid, ids, mechanical_id, context=None):
		
		value = {'uom': ''}
		if mechanical_id:
			uom_rec = self.pool.get('kg.mechanical.master').browse(cr, uid, mechanical_id, context=context)
			value = {'uom': uom_rec.uom.name}
			
		return {'value': value}
		
	def create(self, cr, uid, vals, context=None):
		mech_obj = self.pool.get('kg.mechanical.master')
		if vals.get('mechanical_id'):		  
			uom_rec = mech_obj.browse(cr, uid, vals.get('mechanical_id') )
			uom_name = uom_rec.uom.name
			vals.update({'uom': uom_name})
		return super(ch_mechanical_chart, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		mech_obj = self.pool.get('kg.mechanical.master')
		if vals.get('mechanical_id'):
			uom_rec = mech_obj.browse(cr, uid, vals.get('mechanical_id') )
			uom_name = uom_rec.uom.name
			vals.update({'uom': uom_name})
		return super(ch_mechanical_chart, self).write(cr, uid, ids, vals, context)  
		
	_constraints = [		
			  
		(_check_values, 'Please Check the Min & Max values ,Min value should be less than Max value.!!',['Mechanical Chart']),		
	   ]
	
ch_mechanical_chart()
