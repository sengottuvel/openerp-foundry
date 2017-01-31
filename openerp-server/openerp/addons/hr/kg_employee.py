from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import date
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')
today = datetime.now()

class kg_employee(osv.osv):

	_name = "hr.employee"
	_inherit = 'hr.employee'
	_description = "HRMS module"
	_order = "code"
	
	
	def _get_modify(self, cr, uid, ids, field_name, arg,  context=None):
		res={}		
		if field_name == 'modify':
			for h in self.browse(cr, uid, ids, context=None):
				res[h.id] = 'no'
				if h.status == 'approved':
					cr.execute(""" select * from 
					(SELECT tc.table_schema, tc.constraint_name, tc.table_name, kcu.column_name, ccu.table_name
					AS foreign_table_name, ccu.column_name AS foreign_column_name
					FROM information_schema.table_constraints tc
					JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
					JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
					WHERE constraint_type = 'FOREIGN KEY'
					AND ccu.table_name='%s')
					as sam  """ %('hr_employee'))
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
			
		'code': fields.char('Code', size=4, required=True),		
		'status': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),


		### Entry Info ###
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'active': fields.boolean('Active'),
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'create_user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'ap_rej_date': fields.datetime('Approved/Reject Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Reject By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		
		## Module Requirement Info
		
		'payslip': fields.boolean('Appears On Payslip'),
		'join_date': fields.date('Joining Date'),
		'com_catg': fields.selection([
				('com','Applicable'),
				('no_com','Not Applicable'),
				],'Commission Status', ),
		'releaving_date':fields.date('Releaving Date'),
		'releaving_reason':fields.text('Reason for Leaving'),
		'father_name': fields.char('Father Name', size=128),
		'mother_name': fields.char('Mother Name', size=128),
		'father_occ': fields.char('Father Occupation',size=128),
		'mother_occ': fields.char('Mother Occupation', size=128),
		'pre_add': fields.char('Present Address', size=256, ),
		'pre_city': fields.char('City', size=128, ),
		'pre_state_id': fields.many2one('res.country.state', 'State', ),
		'pre_country_id': fields.many2one('res.country', 'Country', ),
		'pre_pin_code': fields.integer('Postal Code',),
		'pre_phone_no': fields.char('Phone Number',),
		'same_pre_add': fields.boolean('Same as Present Address'),
		'permanent_add': fields.char('Permanent Address', size=256,),
		'city': fields.char('City', size=128,),
		'state_id': fields.many2one('res.country.state', 'State',),
		'country_id': fields.many2one('res.country', 'Country',),
		'pin_code': fields.integer('Postal Code',),
		'phone_no': fields.char('Phone Number',),
		'ann_date': fields.date('Anniversery Date'),
		'wife_hus_name': fields.char('Wife/Husband Name'),
		
		## Child Tables Declaration	
			
		'line_id_ref':fields.one2many('ch.kg.employee.ref','header_id_ref','Line Id Ref'),	
		'line_id_ref_edu':fields.one2many('ch.kg.employee.ref.edu','header_id_ref_edu','Line Id Ref Edu'),	
		'line_id_ref_emp':fields.one2many('ch.kg.employee.ref.emp','header_id_ref_emp','Line Id Ref Emp'),	

	
	}

	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'hr.employee', context=c),
		'active': True,
		'status': 'draft',
		'payslip': True,
		'create_user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'join_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		
	}
	
	_sql_constraints = [
	
		('code', 'unique(code)', 'Employee Code must be unique !!'),
	]
	
	
	### Basic Needs
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'status': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'status': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'status': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'status': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'status': 'reject','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter the remarks in rejection remark field !!'))
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.status not in ('draft','cancel'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_employee, self).write(cr, uid, ids, vals, context)

	###Validataions###
	
	def _Validation(self, cr, uid, ids, context=None):
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
		return True		
	
	def _dob_validation(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		today = date.today()
		if rec.birthday:
			dob_date = datetime.strptime(rec.birthday,'%Y-%m-%d').date()
			b_date = datetime.strptime(rec.birthday, '%Y-%m-%d')
			age=((datetime.today() - b_date).days/365)
			if dob_date >= today or age<18:
				return False
			return True
		else:
			pass
			
	def _joindate_validation(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		today = date.today()
		join_date = datetime.strptime(rec.join_date,'%Y-%m-%d').date()
		if join_date > today:
			return False
		return True
	
	_constraints = [
	
		(_Validation, 'Special Characters Not Allowed !!!', ['Check Name']),
		(_CodeValidation, 'Special Characters Not Allowed !!!', ['Check Code']),		
		(_dob_validation, 'Future dates/Age less than 18 are not allowed for Date of Birth!!', [' ']),		
		(_joindate_validation, 'Future dates are not allowed for Date of Joining!!', [' ']),		
		
	]
	
	## Module Requirement
	
	def onchange_address(self, cr, uid, ids,same_pre_add,pre_add,pre_city,pre_state_id,pre_country_id,pre_pin_code,pre_phone_no,context=None):
		value = {'permanent_add':'','city':'','state_id':'','country_id':'','pin_code':'','phone_no':''}
		if same_pre_add == True:
			value = {
					'permanent_add':pre_add,
					'city':pre_city,
					'state_id':pre_state_id,
					'country_id':pre_country_id,
					'pin_code':pre_pin_code,
					'phone_no':pre_phone_no
					}
					
		return {'value': value}

kg_employee()

class ch_kg_employee_ref(osv.osv):
	
	
	_name = 'ch.kg.employee.ref'
	
	
	_columns = {
	
				'header_id_ref' : fields.many2one('hr.employee','Header ID Ref'),
				'name':fields.char('Name',required = True),
				'contact_no':fields.char('Contact Number',required = True),
				'relation_ship':fields.char('Relation Ship',required = True),
				'designation':fields.char('Designation',),
				'address':fields.text('Address',required = True)
			}
			

ch_kg_employee_ref()	

class ch_kg_employee_ref_edu(osv.osv):
	
	_name = 'ch.kg.employee.ref.edu'	
	
	_columns = {
	
	'header_id_ref_edu':fields.many2one('hr.employee','Header ID Ref Edu'),
	'ug_degree': fields.char('Graduation/Degree', size=128),
	'ug_study': fields.char('Field Of Study', size=128),
	'ug_grade': fields.char('Grade', size=128),
	'ug_institute': fields.char('Institute', size=128),
	'ug_uni': fields.char('University', size=128),
	'ug_date': fields.date('Provision Date'),
	
	}
	
	###Validations###
	
	def _provisiondate_validation(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		today = date.today()
		start_date = datetime.strptime(rec.ug_date,'%Y-%m-%d').date()
		if start_date > today:
			return False
		return True
		
	_constraints = [
		
		(_provisiondate_validation, 'Provision Date should be less than current date for Educational Details !!',[' ']),
		
		]
		
ch_kg_employee_ref_edu()


class ch_kg_employee_ref_emp(osv.osv):
	
	_name = 'ch.kg.employee.ref.emp'	
	
	_columns = {
	
	'header_id_ref_emp':fields.many2one('hr.employee','Header ID Ref Emp'),
	'work_exp': fields.char('Experience', size=128),
	'cmp_name': fields.char('Company', size=128),
	'position': fields.char('Position', size=128),
	'spec': fields.char('Specialization', size=128),
	'from_date': fields.date('From Date'),
	'to_date': fields.date('To Date'),
	
	}
	
	###Validations###
	
	def _fromto_date_validation(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		today = date.today()
		start_date = datetime.strptime(rec.from_date,'%Y-%m-%d').date()
		end_date = datetime.strptime(rec.to_date,'%Y-%m-%d').date()
		if start_date > today or end_date > today or start_date == end_date:
			return False
		return True

	_constraints = [
		
		(_fromto_date_validation, 'From date and To Date should be less than current date for Work History !!',[' ']),

		]  
		
ch_kg_employee_ref_emp()
