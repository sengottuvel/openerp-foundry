from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math

class kg_primemover_master(osv.osv):

	_name = "kg.primemover.master"
	_description = "Prime Mover Master"
	
	def _get_modify(self, cr, uid, ids, field_name, arg,  context=None):
		res={}
		if field_name == 'modify':
			for h in self.browse(cr, uid, ids, context=None):	
				res[h.id] = 'no'
				cr.execute(""" select * from
				(SELECT tc.table_schema, tc.constraint_name, tc.table_name, kcu.column_name, ccu.table_name
				AS foreign_table_name, ccu.column_name AS foreign_column_name
				FROM information_schema.table_constraints tc
				JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
				JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
				WHERE constraint_type = 'FOREIGN KEY'
				AND ccu.table_name='%s')
				as sam  """ %('kg_primemover_master'))
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
		
	_columns = {
		
		## Basic Info
		
		'name': fields.char('Name', size=128, required=True, select=True),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		
		## Module Requirement Info
		
		'manufacturer': fields.many2one('kg.brand.master','Manufacturer',required=True),
		'frequency': fields.selection([('50','50'),('60','60')],'Frequency(Hz)',required=True),
		'effclass': fields.char('Effclass',required=True),
		'pole': fields.integer('Pole',required=True),
		'series': fields.char('Series',required=True),
		'framesize': fields.char('Framesize',required=True),
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
		'product_id': fields.many2one('product.product','Item Name',domain="[('product_type','not in',('raw','capital','service'))]"),
		
		## Entry Info
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.primemover.master', context=c),
		'active': True,		
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),	
		'modify': 'no',
		
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
			prime_name = rec.name
			name=prime_name.upper()			
			cr.execute(""" select upper(name) from kg_primemover_master where upper(name)  = '%s' """ %(name))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
		
	def _check_pole(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.pole <= 0:
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
		return True				
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
	
	def _spl_name(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.name:
			name_special_char = ''.join(c for c in rec.name if c in '!@#$%^~*{}?+/=')
			if name_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Name!'))
		if rec.effclass:
			eff_special_char = ''.join(c for c in rec.effclass if c in '!@#$%^~*{}?+/=')
			if eff_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Effclass!'))
		if rec.series:
			series_special_char = ''.join(c for c in rec.series if c in '!@#$%^~*{}?+/=')
			if series_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Series!'))
		if rec.mounting:
			mount_special_char = ''.join(c for c in rec.mounting if c in '!@#$%^~*{}?+/=')
			if mount_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Mounting!'))
		if rec.specification:
			spe_special_char = ''.join(c for c in rec.specification if c in '!@#$%^~*{}?+/=')
			if spe_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Specification!'))
		if rec.temprise_class:
			temp_special_char = ''.join(c for c in rec.temprise_class if c in '!@#$%^~*{}?+/=')
			if temp_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Temprise Class!'))
		if rec.gd2:
			gd2_special_char = ''.join(c for c in rec.gd2 if c in '!@#$%^~*{}?+/=')
			if gd2_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Gd2!'))
		if rec.space_heater:
			space_special_char = ''.join(c for c in rec.space_heater if c in '!@#$%^~*{}?+/=')
			if space_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Space Heater!'))
		if rec.characteristics:
			cha_special_char = ''.join(c for c in rec.characteristics if c in '!@#$%^~*{}?+/=')
			if cha_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Characteristics!'))
		if rec.noise_level:
			noise_special_char = ''.join(c for c in rec.noise_level if c in '!@#$%^~*{}?+/=')
			if noise_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Noise level (DB)!'))
		
		return True
		
	_constraints = [
		
		#(_Validation, 'Special Character Not Allowed !!!', ['Check Name']),
		#(_CodeValidation, 'Special Character Not Allowed !!!', ['Check Code']),
		(_name_validate, 'Primemover name must be unique !!', ['name']),		
		(_check_pole,'You can not save this Pole with Zero value !',['Pole']),
		(_check_power_kw,'You can not save this Power KW with Zero value !',['Power KW']),
		(_check_efficiency,'You can not save this Efficiency with Zero value !',['Efficiency']),
		(_check_speed,'You can not save this Speed with Zero value !',['Speed']),
		(_check_power_hp,'You can not save this Power HP with Zero value !',['Power HP']),
		(_check_ambient_temp,'You can not save this Ambient Temp with Zero value !',['Ambient Temp']),
		(_check_price,'You can not save this Price with Zero value !',['Price']),
		(_check_shaft_dia,'You can not save this Shaft Dia with Zero value !',['Shaft Dia']),
		(_spl_name, 'Special Character Not Allowed!', ['']),
		
	]
		
	## Basic Needs
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			if rec.cancel_remark:
				self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Cancel remark is must !!'),
					_('Enter the remarks in Cancel remarks field !!'))
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
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
	
kg_primemover_master()
