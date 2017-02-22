from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from dateutil import relativedelta as rdelta
from datetime import date

from datetime import datetime
import re
import math

from dateutil import relativedelta
from dateutil import relativedelta as rdelta
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
			#~ cr.execute('''SELECT column_create('hr_employee','ch_kg_employee_his')''')
			#~ data = cr.fetchall();
			#~ print "_________________________________________________________________________", data
			for h in self.browse(cr, uid, ids, context=None):
				res[h.id] = 'no'
				if h.status == 'approved':
					cr.execute(""" select * from 
					(SELECT tc.table_schema, tc.constraint_name, tc.table_name, kcu.column_name, ccu.table_name
					AS foreign_table_name, ccu.column_name AS foreign_column_name
					FROM information_schema.table_constraints tc
					JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
					JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
					WHERE constraint_type = 'FOREIGN KEY' and tc.table_name not in ('ch_kg_employee_ref','ch_kg_employee_ref_edu','ch_kg_employee_ref_emp','ch_kg_employee_his'
					,'ch_kg_employee_ref_his','ch_kg_employee_ref_edu_his','ch_kg_employee_ref_emp_his')
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
			
		'code': fields.char('Code', size=10, required=True),		
		'status': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled'),('relieve','Relieve In-Progress'),('resigned','Resigned')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10,store=True),		
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
		'pre_city': fields.many2one('res.city', 'City',select=True),
		'pre_state_id': fields.many2one('res.country.state', 'State',domain=[('active','=',True)] ),
		'pre_country_id': fields.many2one('res.country', 'Country', ),
		'pre_pin_code': fields.integer('Postal Code',size=8),
		'pre_phone_no': fields.char('Phone Number',size=15),
		'same_pre_add': fields.boolean('Same as Present Address'),
		'permanent_add': fields.char('Permanent Address', size=256,),
		'city_id': fields.many2one('res.city', 'City', ),
		'state_id': fields.many2one('res.country.state', 'State',),
		'country_id': fields.many2one('res.country', 'Country',),
		'pin_code': fields.integer('Postal Code',size=8),
		'phone_no': fields.char('Phone Number',size=15),
		'ann_date': fields.date('Anniversery Date'),
		'wife_hus_name': fields.char('Wife/Husband Name'),
		'adhar_data': fields.binary('Adhar Copy'),
		'pan_data': fields.binary('Pan Copy'),
		'license_data': fields.binary('License Copy'),
		'voter_data': fields.binary('Voter Copy'),
		'sample_data': fields.char('Voter Copy'),
		'sample_data1': fields.char('Voter Copy'),
		'sample_data2': fields.char('Voter Copy'),
		'sample_data3': fields.char('Voter Copy'),
		'sample_data4': fields.char('Voter Copy'),
		'sample_data5': fields.char('Voter Copy'),
		'sample_data6': fields.char('Voter Copy'),
		
		'att_code': fields.char('Attendance Code'),
		'join_mode': fields.selection([('new','New'),('rejoin','Re-Join')],'Joining Mode'),
		'mode_of_att': fields.selection([('manual','Manual'),('electronic','Electronic'),('both','Both')],'Mode of Attendance'),
		'personal_email': fields.char('Personal Email'),
		'emp_categ_id':fields.many2one('kg.employee.category','Employee Category'),
		'bank_acc_no': fields.char('Bank Account No',size=15),
		'children_1': fields.integer('Children',),
		'nationality': fields.char('Nationality',),
		'wrk_address': fields.char('Working Address',),
		'dep_id':fields.many2one('kg.depmaster','Department'),
		'pan_no':fields.char('Pan No',size=12),
		'division_id':fields.many2one('kg.division.master','Division'),
		'nature_of_job_id':fields.many2one('kg.job.nature','Nature Of Job'),
		
		## Child Tables Declaration	
			
		'line_id_ref':fields.one2many('ch.kg.employee.ref','header_id_ref','Line Id Ref'),	
		'line_id_ref_edu':fields.one2many('ch.kg.employee.ref.edu','header_id_ref_edu','Line Id Ref Edu'),	
		'line_id_ref_emp':fields.one2many('ch.kg.employee.ref.emp','header_id_ref_emp','Line Id Ref Emp'),
		
		'line_id_his':fields.one2many('ch.kg.employee.his','header_id_his','Line Id History'),	
		
		'line_id_ref_his':fields.one2many('ch.kg.employee.ref.his','header_id_ref_his','Line Id Ref History'),	
		'line_id_ref_edu_his':fields.one2many('ch.kg.employee.ref.edu.his','header_id_ref_edu_his','Line Id Ref Edu History'),	
		'line_id_ref_emp_his':fields.one2many('ch.kg.employee.ref.emp.his','header_id_ref_emp_his','Line Id Ref Emp History'),	

	
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
		'join_mode': 'new',
		'wrk_address': 'SAM TURBO INDUSTRY PRIVATE LIMITED',
		'nationality': 'INDIA',
		
	}
	
	_sql_constraints = [
	
		('code', 'unique(code)', 'Employee Code must be unique !!'),
		('adhar_data', 'unique(adhar_data)', 'Adhar No must be unique !!'),
		('pan_data', 'unique(pan_data)', 'PAN No must be unique !!'),
		('bank_acc_no', 'unique(bank_acc_no)', 'Bank Account No must be unique !!'),
		('mobile_phone', 'unique(mobile_phone)', 'Mobile No must be unique per employee !!'),
	]
	
	
	### Basic Needs###
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.status =='approved':
			if rec.cancel_remark:
				self.write(cr, uid, ids, {'status': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Cancel remark is must !!'),
					_('Enter the remarks in Cancel remarks field !!'))
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.status =='draft':
			self.write(cr, uid, ids, {'status': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.status == 'approved':			
			self.write(cr, uid, ids, {'status': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.status =='confirmed':
			emp_obj_1 = self.pool.get('hr.contract')
			emp_categ_obj = self.pool.get('kg.employee.category')
			emp_categ_line = self.pool.get('ch.salary.policy')
			contract_salary = self.pool.get('ch.kg.contract.salary')
			emp_categ_line_1 = emp_categ_obj.browse(cr,uid,rec.emp_categ_id.id)
			emp_cntrct_ids = emp_obj_1.search(cr,uid,[('employee_id','=',rec.id)])
			if emp_cntrct_ids:
				pass
			else:
				emp_vals = {

						'employee_id': rec.id,
						'code':rec.code,
						'dep_id':rec.dep_id.id,
						'job_id':rec.job_id.id,
						'emp_categ_id':rec.emp_categ_id.id,
						'shift_id':emp_categ_line_1.shift_id.id,
						'driver_batta':rec.emp_categ_id.driver_batta,
						}
				att_id = emp_obj_1.create(cr,uid,emp_vals)
				emp_obj = self.pool.get('hr.contract')
				emp_con_1 = emp_obj.search(cr,uid,[('employee_id','=',rec.id)])
				for i in emp_categ_line_1.line_id_3:

					emp_con_vals = {

						'header_id_salary': emp_con_1[0],
						'salary_type':i.allow_deduction_id.id,
						'amt_type':i.type,
						'salary_amt':i.value,

						}
					salary_policy = contract_salary.create(cr,uid,emp_con_vals)

			self.write(cr, uid, ids, {'status': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.status =='confirmed':
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
		rec = self.browse(cr,uid,ids[0])
		#~ vals['header_id_his'] = ids[0]
		#~ vals['update_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
		#~ vals['update_user_id'] = uid
		#~ search_rec = self.pool.get('ch.kg.employee.his')
		#~ search_rec.create(cr,uid,vals)
		a=vals.keys()
		b=vals.items()
		c=[]
		for i in a:
			print "++++++++++++++++++++++++++++++",i
			aa=i+','
		print "()())()()()()()()())",aa
		print"333333333333333333333333333333333333333333",b
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid,'line_id_his':[(0,0,vals)]})
		return super(kg_employee, self).write(cr, uid, ids, vals, context)
		
	###Validataions###
	
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

		#~ (_dob_validation, 'Future dates/Age less than 18 are not allowed for Date of Birth!!', [' ']),		
		(_joindate_validation, 'Future dates are not allowed for Date of Joining!!', [' ']),		
		
	]
	
	## Module Requirement
	
	def onchange_address(self, cr, uid, ids,same_pre_add,pre_add,pre_city,pre_state_id,country_id,pre_pin_code,pre_phone_no,context=None):
		value = {'permanent_add':'','city_id':'','state_id':'','pre_country_id':'','pin_code':'','phone_no':''}
		if same_pre_add == True:
			value = {
					'permanent_add':pre_add,
					'city_id':pre_city,
					'state_id':pre_state_id,
					'pre_country_id':country_id,
					'pin_code':pre_pin_code,
					'phone_no':pre_phone_no
					}
					
		return {'value': value}
		
	def onchange_city(self, cr, uid, ids, pre_city, context=None):
		value = {'pre_city':'','pre_state_id':''}
		if pre_city:
			state_id = self.pool.get('res.city').browse(cr, uid, pre_city, context).state_id.id
			country_id = self.pool.get('res.city').browse(cr, uid,pre_city, context).country_id.id
			return {'value':{'pre_state_id':state_id,'pre_country_id':country_id}}
		return {}
		
	def emp_relieve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.status=='approved':
			self.write(cr, uid, ids, {'status': 'relieve'})
		return True
		
	def emp_resigned(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.status=='approved':
			if rec.releaving_date and rec.releaving_reason:
				self.write(cr, uid, ids, {'status': 'resigned'})
			else:
				raise osv.except_osv(_('Warning!'),
							_('Please Enter the Releaving Date and Releaving Reason'))
		return True

kg_employee()

class ch_kg_employee_ref(osv.osv):
		
	_name = 'ch.kg.employee.ref'

	_columns = {
	
				'header_id_ref' : fields.many2one('hr.employee','Header ID Ref'),
				'name':fields.char('Name',required = True),
				'contact_no':fields.char('Contact Number',required = True,size=15),
				'relation_ship':fields.char('Relation Ship',required = True),
				'designation':fields.char('Designation',),
				'address':fields.text('Address',required = True)
			}

ch_kg_employee_ref()	

class ch_kg_employee_ref_edu(osv.osv):
	
	_name = 'ch.kg.employee.ref.edu'	
	
	_columns = {
	
	'header_id_ref_edu':fields.many2one('hr.employee','Header ID Ref Edu'),
	'ug_degree': fields.char('Graduation/Degree', size=128,required=True),
	'ug_study': fields.char('Field Of Study', size=128 ,required=True),
	'ug_grade': fields.char('Grade', size=128,required=True),
	'ug_institute': fields.char('Institute', size=128 ,required=True),
	'ug_uni': fields.char('University', size=128 ,required=True),
	'ug_date': fields.date('Provision Date' ,required=True),
	
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
	'work_exp': fields.char('Experience (Y / M / D)', size=128,required=True),
	'cmp_name': fields.char('Company', size=128 ,required=True),
	'position': fields.char('Position', size=128 ,required=True),
	'spec': fields.char('Specialization', size=128 ,required=True),
	'from_date': fields.date('From Date' ,required=True),
	'to_date': fields.date('To Date' ,required=True),
	
	}
	
	###Validations###
	
	
	def _fromto_date_validation(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		today = date.today()
		start_date = datetime.strptime(rec.from_date,'%Y-%m-%d').date()
		end_date = datetime.strptime(rec.to_date,'%Y-%m-%d').date()
		if start_date > today:
			raise osv.except_osv(_('Warning !!'),
					_('Current Date not accepted in Start Date !!'))
		if end_date > today:
			raise osv.except_osv(_('Warning !!'),
					_('Current Date not accepted in End Date !!'))
		if start_date == end_date:
			raise osv.except_osv(_('Warning !!'),
					_('Start and End Date should not be equal !!'))
		if start_date > end_date:
			raise osv.except_osv(_('Warning !!'),
					_('End Date should be greater than Start Date !!'))
			return False
		return True

	_constraints = [
		
		(_fromto_date_validation, 'From date and To Date should be less than current date for Work History !!',[' ']),

		]  
	
	def onchange_to_date(self, cr, uid, ids,to_date,from_date,context=None):
		value = {'from_date':'','to_date':''}
		d1 =  datetime.strptime(from_date, "%Y-%m-%d")
		d2 =  datetime.strptime(to_date, "%Y-%m-%d")
		rd = rdelta.relativedelta(d1,d2)
		years= "{0.years} / {0.months} / {0.days}".format(rd)
		value = {
				'work_exp':years,
				}
		return {'value': value}
		
ch_kg_employee_ref_emp()

##History Tracking starts###

class ch_kg_employee_his(osv.osv):
	
	_name = 'ch.kg.employee.his'	
	
	_columns = {
	
			### Basic Info
		'header_id_his':fields.many2one('hr.employee','Header Id'),
		'code': fields.char('Code', size=4, required=False),		
		'status': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
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
		'pre_pin_code': fields.integer('Postal Code',size=8),
		'pre_phone_no': fields.char('Phone Number',size=15),
		'same_pre_add': fields.boolean('Same as Present Address'),
		'permanent_add': fields.char('Permanent Address', size=256,),
		'city_id': fields.char('City', size=128,),
		'state_id': fields.many2one('res.country.state', 'State',),
		'country_id': fields.many2one('res.country', 'Country',),
		'pin_code': fields.integer('Postal Code',size=8),
		'phone_no': fields.char('Phone Number',size=15),
		'ann_date': fields.date('Anniversery Date'),
		'wife_hus_name': fields.char('Wife/Husband Name'),
		'adhar_data': fields.binary('Adhar Copy'),
		'pan_data': fields.binary('Pan Copy'),
		'license_data': fields.binary('License Copy'),
		'voter_data': fields.binary('Voter Copy'),
		'name': fields.char('Employee Name'),
		'work_location': fields.char('Work Location'),
		'work_phone': fields.char('Work Phone'),
		'mobile_phone': fields.char('Mobile Phone'),
		'department_id': fields.many2one('hr.department', 'Department', readonly=True),
		'job_id': fields.many2one('hr.job', 'Designation', readonly=True),
		'marital': fields.char('Marital Status', readonly=True),
		'gender': fields.char('Gender', readonly=True),
		'children': fields.integer('Children', readonly=True),
		'remaining_leaves': fields.integer('Remaining Leaves', readonly=True),
		'identification_id': fields.char('Adhar ID', readonly=True),
		'bank_account_id': fields.char('bank name', readonly=True),
		'children_1': fields.integer('Children',),
	}
	
	_defaults = {
		
		'entry_mode': 'auto',
		
			
	}
	
ch_kg_employee_his()



class ch_kg_employee_ref_his(osv.osv):

	_name = 'ch.kg.employee.ref.his'
	
	_columns = {
	
				'header_id_ref_his' : fields.many2one('hr.employee','Header ID Ref History'),
				'name':fields.char('Name'),
				'contact_no':fields.char('Contact Number',size=15),
				'relation_ship':fields.char('Relation Ship'),
				'designation':fields.char('Designation'),
				'address':fields.text('Address')
			}

ch_kg_employee_ref_his()

class ch_kg_employee_ref_edu_his(osv.osv):
	
	_name = 'ch.kg.employee.ref.edu.his'	
	
	_columns = {
	
	'header_id_ref_edu_his':fields.many2one('hr.employee','Header ID Ref Edu History'),
	'ug_degree': fields.char('Graduation/Degree', size=128),
	'ug_study': fields.char('Field Of Study', size=128 ),
	'ug_grade': fields.char('Grade', size=128),
	'ug_institute': fields.char('Institute', size=128),
	'ug_uni': fields.char('University', size=128),
	'ug_date': fields.date('Provision Date'),
	
	}

ch_kg_employee_ref_edu_his()

class ch_kg_employee_ref_emp_his(osv.osv):
	
	_name = 'ch.kg.employee.ref.emp.his'	
	
	_columns = {
	
	'header_id_ref_emp_his':fields.many2one('hr.employee','Header ID Ref Emp History'),
	'work_exp': fields.char('Experience', size=128),
	'cmp_name': fields.char('Company', size=128),
	'position': fields.char('Position', size=128),
	'spec': fields.char('Specialization', size=128),
	'from_date': fields.date('From Date'),
	'to_date': fields.date('To Date'),
	
	}

ch_kg_employee_ref_emp_his()

##History Tracking Ends###


