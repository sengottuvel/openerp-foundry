from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
import base64

class kg_pumpseries_master(osv.osv):

	_name = "kg.pumpseries.master"
	_description = "Pumpseries Master"
	
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
				as sam  """ %('kg_pumpseries_master'))
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
			
		'name': fields.char('Name', size=128, required=True, select=True),
		'code': fields.char('Code',required=True, size=128),
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
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		
		### Entry Info ###
		
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.pumpseries.master', context=c),
		'active': True,		
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),	
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
		if rec.name:
			pumpseries_name = rec.name
			name=pumpseries_name.upper()			
			cr.execute(""" select upper(name) from kg_pumpseries_master where upper(name)  = '%s' """ %(name))
			data = cr.dictfetchall()			
			if len(data) > 1:
				raise osv.except_osv(_('Warning!'),
						_('Pumpseries name must be unique!'))
			name_special_char = ''.join(c for c in rec.name if c in '!@#$%^~*{}?+/=')
			if name_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Name!'))
		return True
			
	def _code_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.code:
			pumpseries_code = rec.code
			code=pumpseries_code.upper()
			cr.execute(""" select upper(code) from kg_pumpseries_master where upper(code) = '%s' """ %(code))
			data = cr.dictfetchall()			
			if len(data) > 1:
				raise osv.except_osv(_('Warning!'),
						_('Pumpseries code must be unique!'))
			code_special_char = ''.join(c for c in rec.code if c in '!@#$%^~*{}?+/=')
			if code_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Code!'))			
		return True	
	
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_code = str(rec.code)
		#~ url = 'http://iasqa1.kgisl.com/?uname='+rec_user+'&s='+rec_work_order
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
		
		url = 'http://10.100.9.60/DMS/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&wo_no='+rec_code
		
		#url = 'http://192.168.1.150:81/pbxclick2call.php?exten='+exe_no+'&phone='+str(m_no)
		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
	
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
		if rec.state == 'confirmed':
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
		(_name_validate, 'Pumpseries name must be unique!', ['']),		
		(_code_validate, 'Pumpseries code must be unique!', ['']),		
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
	
	def _check_flange(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(""" select flange_id from ch_pumpseries_flange where flange_id  = '%s' and header_id = '%s' """ %(entry.flange_id.id,entry.header_id.id))
		data = cr.dictfetchall()			
		if len(data) > 1:		
			return False
		return True	
	
	_constraints = [		
			  
		(_check_flange, 'System should not accept same flange details!',['']),	
		
	   ]
	
	
ch_pumpseries_flange()
