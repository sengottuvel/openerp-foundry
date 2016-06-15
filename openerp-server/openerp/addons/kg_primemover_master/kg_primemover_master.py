from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_primemover_master(osv.osv):

	_name = "kg.primemover.master"
	_description = "Primemover Master"
	
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
			
		'name': fields.char('Name', size=128, required=True, select=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'manufacturer': fields.many2one('kg.brand.master','Manufacturer',required=True),
		'frequency': fields.selection([('50','50'),('60','60')],'Frequency(Hz)',required=True),
		'effclass': fields.char('Effclass',required=True),
		'pole': fields.integer('Pole',required=True),
		'series': fields.char('Series',required=True),
		'framesize': fields.integer('Framesize',required=True),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'mounting': fields.char('Mounting',required=True),
		'terminal_box_loc': fields.selection([('front','FRONT'),('top','TOP'),('behind','BEHIND')],'Terminal Box Location',required=True),
		'efficiency': fields.integer('Efficiency',required=True),
		'power_kw': fields.float('Power(Kw)',required=True),
		'power_hp': fields.float('PowerHp(Hp)',required=True),
		'speed': fields.integer('Speed(Rpm)',required=True),
		'specification': fields.char('Specification',required=True),
		'gd2': fields.char('Gd2'),
		'noise_level': fields.char('Noise level (DB)'),
		'primemover_type': fields.selection([('motor','MOTOR'),('engine','ENGINE')],'Prime Mover Type'),
		'weight': fields.float('Weight'),
		'article_no': fields.char('Article No',required=True),
		'price': fields.float('Price',required=True),
		'space_heater': fields.char('Space Heater'),
		'radiator_mtg': fields.char('Radiator Mtg'),
		'characteristics': fields.char('Characteristics'),
		'shaft_dia': fields.float('Shaft Dia',required=True),
		'ambient_temp': fields.float('Ambient Temp',required=True),
		'temprise_class': fields.char('TempRise Class',required=True),
		'primemover_categ': fields.selection([('engine','Engine'),('motor','Motor')],'Primemover Category',required=True),
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.primemover.master', context=c),
		'active': True,		
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':fields.datetime.now,	
		#'modify': 'no',
	}
	
	_sql_constraints = [
	
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
			cr.execute(""" select upper(name) from kg_dispatch_master where upper(name)  = '%s' """ %(name))
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
		return super(kg_primemover_master, self).write(cr, uid, ids, vals, context)
	
	def _check_pole(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.pole <= 0:
			return False					
		return True	
	def _check_framesize(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.framesize <= 0:
			return False					
		return True	
	def _check_power_kw(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.power_kw <= 0:
			return False					
		return True	
	def _check_efficiency(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.efficiency <= 0:
			return False					
		return True	
	def _check_speed(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.power_kw <= 0:
			return False					
		return True	
	def _check_power_hp(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.power_hp <= 0:
			return False					
	def _check_ambient_temp(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.ambient_temp <= 0:
			return False					
		return True	
	def _check_price(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.price<= 0:
			return False					
		return True	
	def _check_shaft_dia(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.shaft_dia <= 0:
			return False					
		return True	
	
	_constraints = [
		#(_Validation, 'Special Character Not Allowed !!!', ['Check Name']),
		#(_CodeValidation, 'Special Character Not Allowed !!!', ['Check Code']),
		(_name_validate, 'Primemover name must be unique !!', ['name']),		
		(_check_pole,'You can not save this Pole with Zero value !',['Pole']),
		(_check_framesize,'You can not save this Framesize with Zero value !',['Framesize']),
		(_check_power_kw,'You can not save this Power KW with Zero value !',['Power KW']),
		(_check_efficiency,'You can not save this Efficiency with Zero value !',['Efficiency']),
		(_check_speed,'You can not save this Speed with Zero value !',['Speed']),
		#~ (_check_power_hp,'You can not save this Power HP with Zero value !',['Power HP']),
		(_check_ambient_temp,'You can not save this Ambient Temp with Zero value !',['Ambient Temp']),
		(_check_price,'You can not save this Price with Zero value !',['Price']),
		(_check_shaft_dia,'You can not save this Shaft Dia with Zero value !',['Shaft Dia']),
		
	]
	
kg_primemover_master()
