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

class kg_packing_type(osv.osv):

	_name = "kg.packing.type"
	_description = "Packing Type Master"
	
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
					as sam  """ %('kg_packing_type'))
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
	
		### Basic Info
			
		'name': fields.char('Name', size=128, required=True, select=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),		
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
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
		
		## Module Requirement Info	
		'rate_cft': fields.float('Packing Closing Rate/CFT' ,required=True),
		'rate_box': fields.float('SC WO Rate/Box' ,required=True),
		
		## Child Tables Declaration		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.packing.type', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Name must be unique per Company !!'),
		('code', 'unique(code)', 'Code must be unique per Company !!'),
	]
	
	### Basic Needs
	
	def _Validation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		name_special_char = ''.join( c for c in flds.name if  c in '!@#$%^~*{}?+/=' )		
		if name_special_char:
			return False		
		return True	
	
		
	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.name:
			packing_name = rec.name
			name=packing_name.upper()			
			cr.execute(""" select upper(name) from kg_packing_type where upper(name)  = '%s' """ %(name))
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
		return super(kg_packing_type, self).write(cr, uid, ids, vals, context)
		
	def _check_rate(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])			
		if rec.rate_cft <= 0.00:
			raise osv.except_osv(_('Warning'), _('Packing Closing Rate/CFT should be greater than zero !!'))	
		if rec.rate_box <= 0.00:
			raise osv.except_osv(_('Warning'), _('SC WO Rate/Box should be greater than zero !!'))				
		return True
		
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_code = str(rec.name)		
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
			
		url = 'http://192.168.1.7/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&packing_type='+rec_code

		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
		
	_constraints = [
	
		(_check_rate,'System not allow to save Zero and Negative values in Rate field !!',['Rate']),
		(_Validation, 'Special Character Not Allowed !!!', ['Check Name']),		
		(_name_validate, 'Packing name must be unique !!', ['name']),			
	]
	
	## Module Requirement
	
kg_packing_type()
