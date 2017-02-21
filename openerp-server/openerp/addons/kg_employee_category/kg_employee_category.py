from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_employee_category(osv.osv):

	_name = "kg.employee.category"
	_description = "Employee Category Master"
	
	### Version 0.1
	
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
					WHERE constraint_type = 'FOREIGN KEY' and tc.table_name not in ('ch_special_incentive_policy','ch_bonus_policy','ch_salary_policy','ch_leave_policy')
					AND ccu.table_name='%s')
					as sam  """ %('kg_employee_category'))
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
		
		### Version 0.2
		
		
	
	_columns = {
	
		### Basic Info
			
		'name': fields.char('Name', size=128, required=True, select=True),	
		'code': fields.char('Code', size=4, required=True),		
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),


		### Entry Info ###
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'active': fields.boolean('Active'),
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
		
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'monthly_per_hrs':fields.float('Monthly Permission hours'),	
		'max_late_count':fields.integer('Maximum Late in Count'),	
		'attnd_insentive_male':fields.float('100% Attn. Incentive (Male)'),	
		'attnd_insentive_female':fields.float('100% Attn. Incentive (Female)'),	
		'driver_batta':fields.float('Driver Batta(Per Day)'),	
		'bonus_categ': fields.selection([('turn_over','Turn Over'),('attendance','Attendance'),('yrs_of_service','Year Of Service'),('not_applicable','Not Applicable')],'Bonus Category'),
		'no_of_days_wage':fields.integer('No Of Days Wages'),
		'sal_calc': fields.selection([('cal_days','Calendar Days'),('working_days','Working Days')],'Salary Calculation Days'),	
		## Child Tables Declaration		
		
		'line_id_1': fields.one2many('ch.special.incentive.policy', 'header_id_1','Special Incentive Policy'),
		'line_id_2': fields.one2many('ch.bonus.policy', 'header_id_2','Bonus Policy'),
		'line_id_3': fields.one2many('ch.salary.policy', 'header_id_3','Salary Policy'),
		'line_id_4': fields.one2many('ch.leave.policy', 'header_id_4','Leave Policy'),
		'line_id_5': fields.one2many('ch.incentive.policy', 'header_id_5','Incentive Policy'),
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.employee.category', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Name must be unique per Category !!'),
		('code', 'unique(code)', 'Code must be unique per Category !!'),
	]
	
	### Basic Needs
	
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
		rec = self.browse(cr,uid,ids[0])
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
		return super(kg_employee_category, self).write(cr, uid, ids, vals, context)
		
	## Validations 
	def val_negative(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.monthly_per_hrs <= 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values and Zeros are not allowed in Monthly Permission Hours !!'))
		if rec.attnd_insentive_male < 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values and Zeros are not allowed in 100% Attn. Incentive Male !!'))
		if rec.attnd_insentive_female < 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values and Zeros are not allowed in 100% Attn. Incentive Female !!'))
		if rec.max_late_count <= 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values and Zeros are not allowed in Maximum Late in Count !!'))
		if rec.max_late_count > 5:
			raise osv.except_osv(_('Warning!'),
						_('Maximum Late in Count should be less than 5 and Zeros are not allowed !!'))
		if rec.monthly_per_hrs > 10:
			raise osv.except_osv(_('Warning!'),
						_('Monthly Permission hours should be less than 10 and Zeros are not allowed !!'))
		if rec.driver_batta < 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values are not allowed in Driver Batta(Per Day)	 !!'))
		if rec.bonus_categ == 'attendance':
			if rec.no_of_days_wage <= 0 :
				raise osv.except_osv(_('Warning!'),
							_('No of Days Wages should not be zero!!'))
												
		amt = 0.00
		if rec.line_id_3:
			for line in rec.line_id_3:
				if line.type == 'percentage':
					amt += line.value 
			if amt > 100.00:
				raise osv.except_osv(_('Warning!'),
						_('Salary Policy Value should not exceed 100 percentage !!'))
				return False
		
		## dups validations in special intensive
		
		if rec.line_id_1:
			line_value_start = [ line.start_value for line in rec.line_id_1 ]
			line_value_end = [ line.end_value for line in rec.line_id_1 ]
			a= [line_value_start.count(i) for i in line_value_start ]
			b= [line_value_end.count(i) for i in line_value_end ]
			for j in a:
				if j > 1:
					raise osv.except_osv(_('Warning!'),
								_('Duplicate Start Values are not allowed in Special Incentive Policy !!'))
			for k in b:
				if k > 1:
					raise osv.except_osv(_('Warning!'),
								_('Duplicate End Values are not allowed in Special Incentive Policy !!'))
		
		
	## dups validations in Bonus Policy
	
		if rec.line_id_2:
			line_value_year = [ line.year for line in rec.line_id_2 ]
			a= [line_value_year.count(i) for i in line_value_year ]
			for i in a:
				if i > 1:
					raise osv.except_osv(_('Warning!'),
								_('Duplicate Years are not allowed Bonus Policy !!'))
								
	## dups validations in Salary Policy
	
		if rec.line_id_3:
			line_value_name = [ line.allow_deduction_id for line in rec.line_id_3 ]
			a= [line_value_name.count(i) for i in line_value_name ]
			for i in a:
				if i > 1:
					raise osv.except_osv(_('Warning!'),
								_('Duplicate Name are not allowed Salary Policy !!'))
								
	## dups validations in Leave Policy
	
		if rec.line_id_4:
			line_value_type = [ line.leave_type_id for line in rec.line_id_4 ]
			a= [line_value_type.count(i) for i in line_value_type ]
			for i in a:
				if i > 1:
					raise osv.except_osv(_('Warning!'),
								_('Duplicate Leave Types are not allowed Leave Policy !!'))
		
		return True
								
	## Module Requirement

	_constraints = [

		(val_negative, 'Negative Values are not allowed!!', [' ']),		
		
	]
	
kg_employee_category()

class ch_special_incentive_policy(osv.osv):
	
	_name='ch.special.incentive.policy'
	_description = "Special Incentive Policy"
	
	_columns = {
		
		'header_id_1': fields.many2one('kg.employee.category','Header_id_1'),
		'start_value': fields.float('Starting Value(In Crores)'),	
		'end_value': fields.float('Ending Value(In Crores)'),	
		'type': fields.selection([('fixed','Fixed'),('per_cr_fixed','Per Crore - Fixed'),('percentage','Percentage')],'Type'),	
		'incentive_value': fields.float('Value'),	
		'leave_consider': fields.integer('Leave Consideration(days)'),	
		}	
		
	## Module Requirement
		
	def val_negative(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.start_value <= 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values are and Zeros not allowed in Starting Value in Special incentive !!'))
		if rec.end_value <= 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values and Zeros are not allowed in Ending Value in Special incentive  !!'))
		if rec.incentive_value <= 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values and Zeros are not allowed in Special Incentive Value !!'))
		if rec.leave_consider < 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values are not allowed in Leave Consideration in Special incentive !!'))
		if rec.end_value <= rec.start_value :
			raise osv.except_osv(_('Warning!'),
						_('End Value should be greater than Start Value in Special Incentive!!'))
		if rec.leave_consider > 12 :
			raise osv.except_osv(_('Warning!'),
						_('Leave Consideration in Special Incentive should not exceed 12 days!!'))
						
		if rec.type == 'percentage' :
			if rec.incentive_value > 100:
				raise osv.except_osv(_('Warning!'),
							_('Value of the Special Incentive should not exceed 100 % !!'))

		return True

		
	## Module Requirement
	
	_constraints = [

		(val_negative, 'Negative Values are not allowed!!', [' ']),		
		
	]
		
ch_special_incentive_policy()

class ch_incentive_policy(osv.osv):
	
	_name='ch.incentive.policy'
	_description = "Incentive Policy"
	
	_columns = {
		
		'header_id_5': fields.many2one('kg.employee.category','Header_id_1'),
		'start_value': fields.float('Starting Value(In Lakhs)'),	
		'end_value': fields.float('Ending Value(In Lakhs)'),	
		'type': fields.selection([('fixed','Fixed'),('per_lhk_fixed','Per Lakh - Fixed'),('percentage','Percentage')],'Type'),	
		'incentive_value': fields.float('Value'),	
		'leave_consider': fields.integer('Leave Consideration(days)'),	
		}	
		
	## Module Requirement
		
	def val_negative(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.start_value <= 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values are and Zeros not allowed in Starting Value in incentive !!'))
		if rec.end_value <= 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values and Zeros are not allowed in Ending Value in incentive  !!'))
		if rec.incentive_value <= 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values and Zeros are not allowed in Incentive Value !!'))
		if rec.leave_consider < 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values are not allowed in Leave Consideration in incentive !!'))
		if rec.end_value <= rec.start_value :
			raise osv.except_osv(_('Warning!'),
						_('End Value should be greater than Start Value in Incentive!!'))
		if rec.leave_consider > 12 :
			raise osv.except_osv(_('Warning!'),
						_('Leave Consideration in Incentive should not exceed 12 days!!'))
						
		if rec.type == 'percentage' :
			if rec.incentive_value > 100:
				raise osv.except_osv(_('Warning!'),
							_('Value of the Incentive should not exceed 100 % !!'))

		return True

		
	## Module Requirement
	
	_constraints = [

		(val_negative, 'Negative Values are not allowed!!', [' ']),		
		
	]
		
ch_special_incentive_policy()


class ch_bonus_policy(osv.osv):
	
	_name='ch.bonus.policy'
	_description = "Bonus Policy"
	
	_columns = {
	
		'header_id_2': fields.many2one('kg.employee.category','Header_id_2'),
		'year': fields.integer('Years Upto'),	
		'type': fields.selection([('fixed','Fixed'),('no_of_days','No Of Days')],'Type'),	
		'value': fields.float('Value'),	
		}
		
	def val_negative(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.year <= 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values and Zeros are not allowed for Years Upto in Bonus Policy!!'))
		if rec.value <= 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values and Zeros are not allowed in Bonus Value  !!'))
		return True
	## Module Requirement
	
	_constraints = [

		(val_negative, 'Negative Values are not allowed!!', [' ']),		
		
	]	
		
ch_bonus_policy()


class ch_salary_policy(osv.osv):
	
	_name='ch.salary.policy'
	_description = "Salary Policy"
	
	_columns = {
	
		'header_id_3': fields.many2one('kg.employee.category','Header_id_3'),
		'allow_deduction_id': fields.many2one('hr.salary.rule', 'Name'),
		'type': fields.selection([('fixed','Fixed'),('percentage','Percentage')],'Type'),	
		'value': fields.float('Value'),	
		}	
	
	## Validations
		
	def val_negative(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.value <= 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values and Zeros are not allowed in Values in Salary Policy !!'))
		return True

	## Module Requirement
	
	_constraints = [

		(val_negative, 'Negative Values are not allowed!!', [' ']),		
		
	]	
		
ch_salary_policy()


class ch_leave_policy(osv.osv):
	
	_name='ch.leave.policy'
	_description = "Leave Policy"
	
	_columns = {
	
		'header_id_4': fields.many2one('kg.employee.category','Header_id_4'),
		'leave_type_id': fields.many2one('hr.holidays.status', 'Leave Type'),
		'no_of_days': fields.float('No Of Days'),	
		}	
		
	def val_negative(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.no_of_days <= 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values and Zeros are not allowed in No Of Days in Leave Policy !!'))
		if rec.no_of_days > 15:
			raise osv.except_osv(_('Warning!'),
						_('Number Of Days in Leave Policy should not exceed 15 for each Leave Policy !!'))
		return True
	## Module Requirement
	
	_constraints = [

		(val_negative, 'Negative Values are not allowed!!', [' ']),		
		
	]	
		
ch_salary_policy()
