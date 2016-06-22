from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
import base64
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_pumpseries_master(osv.osv):

	_name = "kg.pumpseries.master"
	_description = "Pumpseries Master"
	
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
		'code': fields.char('Code',required=True, size=128),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'fluid_id': fields.many2one('kg.fluid.master','Liquid Handled',domain="[('state','not in',('reject','cancel'))]"),
		'pump_capacity': fields.float('Pump capacity(M3/hr)'),
		'pump_head': fields.float('Pump Head(Mts)'),
		'temperature': fields.float('Temperature'),
		'working_pressure': fields.float('Working Pressure(Kg/cm2)'),
		'speed': fields.float('Speed(Rpm)'),
		'suction_orientation': fields.selection([('axial','AXIAL'),('side','SIDE')],'Suction Orientation'),
		'discharge_orientation': fields.selection([('top_side','TOP SIDE'),('bot_side','BOTTOM SIDE'),('top','TOP'),('top_cen_line','TOP CENTER LINE')],'Discharge Orientation',required=True),
		'line_ids': fields.one2many('ch.pumpseries.flange', 'header_id', "Child Pumpseries Flange",readonly=False, states={'approved':[('readonly',True)]}),
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.pumpseries.master', context=c),
		'active': True,		
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':fields.datetime.now,	
		#'modify': 'no',
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
			pumpseries_name = rec.name
			name=pumpseries_name.upper()			
			cr.execute(""" select upper(name) from kg_pumpseries_master where upper(name)  = '%s' """ %(name))
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
			pumpseries_code = rec.code
			code=pumpseries_code.upper()
			cr.execute(""" select upper(code) from kg_pumpseries_master where upper(code) = '%s' """ %(code))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res	
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_code = str(rec.code)		
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
		
		url = 'http://192.168.1.7/DMS/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&pumser='+rec_code	
		
		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
	
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
		return super(kg_pumpseries_master, self).write(cr, uid, ids, vals, context)
		
	def _check_code(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.code <= 0:
			return False					
		return True	
		
	_constraints = [
		#(_Validation, 'Special Character Not Allowed !!!', ['Check Name']),
		#(_CodeValidation, 'Special Character Not Allowed !!!', ['Check Code']),
		(_name_validate, 'Pumpseries name must be unique !!', ['name']),		
		(_code_validate, 'Pumpseries code must be unique !!', ['code']),		
		(_check_code,'You can not save this Code with Zero value !',['Code']),
	]
	
kg_pumpseries_master()

class ch_pumpseries_flange(osv.osv):

	_name = "ch.pumpseries.flange"
	_description = "Ch Pumpseries Flange Details"
	
	_columns = {
	
		'name': fields.char('Name'),
		'header_id':fields.many2one('kg.pumpseries.master', 'Header Id', ondelete='cascade'),
		'flange_id':fields.many2one('kg.flange.master', 'Flange Standard',required=True,domain="[('state','not in',('reject','cancel'))]"),
		'flange_type': fields.selection([('standard','Standard'),('optional','Optional')],'Flange Type'),
		
	}
	
	_defaults = {
	
				'flange_type': 'standard',
				
				}
				
	def onchange_flange(self, cr, uid, ids, flange_id, name, context=None):
		value = {'name': ''}
		if flange_id:
			flange_rec = self.pool.get('kg.flange.master').browse(cr, uid, flange_id, context=context)
			value = {'name': flange_rec.name}
			
		return {'value': value}
		
	
ch_pumpseries_flange()
