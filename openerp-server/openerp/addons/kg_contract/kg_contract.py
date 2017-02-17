from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
from datetime import date
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_contract(osv.osv):

	_name = "hr.contract"
	_inherit = 'hr.contract'
	_order = "code"
	_description = "Employee Contract"

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
					WHERE constraint_type = 'FOREIGN KEY' and tc.table_name not in ('ch_kg_contract_salary','ch_kg_contract_pre_salary','ch_kg_contract_his','ch_kg_contract_salary_his','ch_kg_contract_pre_salary_his')
					AND ccu.table_name = '%s')
					as sam  """ %('hr_contract'))
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
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10,store=True),		
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
		'designation': fields.char('Designation', size=128, readonly=False),
		'department_id': fields.many2one('hr.department', 'Department ', readonly=True),
		'join_date': fields.date('Join Date', readonly=False),
		'gross_salary':fields.float('Gross Salary', help="Please Enter the Gross salary per month."),
		'mobile_allow':fields.float('Mobile Allowance'),
		'increament_type':fields.selection([('yearly','Yearly'),('performance','Performance'),('promotions','Promotion')],'Increment Type'),
		'increament_amt':fields.float('Increment Amount'),
		'payment_mode': fields.selection([('cheque','CHEQUE'),('bank','BANK'),('cash','CASH')], 'Payment Mode'),
		'bank_id': fields.many2one('res.bank','Bank Name'),
		'sal_acc_no': fields.char('Salary Account No', size=32),
		'ot_status': fields.boolean('OT Eligible'),
		'pt_status': fields.boolean('PT Applicable'),
		'pan_no': fields.char('PAN NO', size=32),
		'pf_status': fields.boolean('PF Applicable', size=32),
		'esi_status': fields.boolean('ESI Applicable', size=32),
		'pf_eff_date': fields.date('PF Effective From'),
		'esi_eff_date': fields.date('ESI Effective From'),
		'pf_acc_no': fields.char('PF NO', size=7),
		'esi_acc_no': fields.char('ESI NO', size=17),
		'job_id': fields.many2one('hr.job', 'Designation', readonly=True),
		'bonus_applicable': fields.boolean('Bonus Applicable'),
		'special_incentive': fields.boolean('Special Incentive'),
		'emp_categ_id': fields.many2one('kg.employee.category', 'Employee Category'),
		'rotation':fields.boolean('Rotation Shift Applicable'),
		'driver_bata_app':fields.boolean('Driver Bata Applicable'),
		'shift_id': fields.many2one('kg.shift.master', 'Shift'),
		'dep_id':fields.many2one('kg.depmaster','Department'),
		'vda_status': fields.boolean('VDA Applicable'),
			
		
		## Child Tables Declaration		
		'line_id_salary':fields.one2many('ch.kg.contract.salary','header_id_salary','Line Id Salary'),	
		'line_id_pre_salary':fields.one2many('ch.kg.contract.pre.salary','header_id_pre_salary','Line Id Pre Salary'),	
		'line_id_his':fields.one2many('ch.kg.contract.his','header_id_his','Line Id contract History'),
		'line_id_salary_his':fields.one2many('ch.kg.contract.salary.his','header_id_salary_his','Line Id Salary History'),	
		'line_id_pre_salary_his':fields.one2many('ch.kg.contract.pre.salary.his','header_id_pre_salary_his','Line Id Pre Salary History'),		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.master', context=c),
		'active': True,
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		
	}
	
	_sql_constraints = [
		#~ ('code', 'unique(code)', 'Code must be unique per Company !!'),
	]
	
	### Basic Needs		
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state =='approved':
			if rec.cancel_remark:
				self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Cancel remark is must !!'),
					_('Enter the remarks in Cancel remarks field !!'))
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state =='draft':
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state =='approved':
			self.write(cr, uid, ids, {'state': 'draft'})
		return True

	

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state =='confirmed':
			if rec.state =='approved':
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
		
	#~ def write(self, cr, uid,ids, vals, context=None):
		#~ vals['header_id_his'] = ids[0]
		#~ print "****************************************",vals
		#~ search_rec = self.pool.get('ch.kg.contract.his')
		#~ search_rec.create(cr,uid,vals)
		#~ return super(kg_contract, self).write(cr, uid, ids,vals,context)
		
	def write(self, cr, uid, ids, vals, context=None):
		rec = self.browse(cr,uid,ids[0])
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid,'line_id_his':[(0,0,vals)]})
		return super(kg_contract, self).write(cr, uid, ids, vals, context)
	
	###Validations###
	
	def _salary_brk_validation(self,cr,uid,ids,context = None):
		rec = self.browse(cr,uid,ids[0])
		amt = 0.00
		per = 0.00
		if rec.line_id_salary:
			cr.execute('''select sum(salary_amt) from ch_kg_contract_salary where header_id_salary = %s and amt_type = 'percentage' '''%(rec.id))
			data = cr.dictfetchall()
			print "*************************************",data[0]['sum']
			if data[0]['sum'] != None:
				if data[0]['sum'] != 100.0:
					raise osv.except_osv(_('Warning!'),
						_('Total Percentage Break ups should 100 !!'))
					
					
			cr.execute('''select sum(ch.salary_amt)
					from
					hr_contract cont
					left join ch_kg_contract_salary ch on (ch.header_id_salary=cont.id)
					where cont.id = %s and ch.amt_type = 'fixed' '''%(rec.id))
			data_1 = cr.dictfetchall()
			print"data_1data_1data_1",data_1
			print"data_1data_1data_1",type(data_1[0]['sum'])
			print"data_1data_1data_1",type(rec.gross_salary)
			if data_1[0]['sum'] != None:
				print"data_1[0]['sum'] -------------",data_1[0]['sum'] ,type(data_1[0]['sum'] )
				print"rec.gross_salary -------------",rec.gross_salary,type(rec.gross_salary)
				if data_1[0]['sum'] == rec.gross_salary:
					print"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
					pass
				elif data_1[0]['sum'] != rec.gross_salary:
					print"bbbbbbbbbbbbbbbbbbbb"
					raise osv.except_osv(_('Warning!'),
						_('Salary Break ups are mismatching with Gross Salary !!'))
						
			#~ for line in rec.line_id_salary:
				#~ if line.amt_type == 'percentage':
					#~ amt += line.salary_amt 
				#~ if line.amt_type == 'fixed':
					#~ amt += line.salary_amt
			#~ if amt != 100 :
				#~ print "*************************************",per
				#~ raise osv.except_osv(_('Warning!'),
						#~ _('Total Percentage Break ups should 100 !!'))
			#~ if amt != rec.gross_salary:
				#~ raise osv.except_osv(_('Warning!'),
						#~ _('Salary Break ups are mismatching with Gross Salary !!'))
		
				#~ return False
		return True

		
	def child_dups_val(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.line_id_salary:
			line_salary_type = [ line.salary_type for line in rec.line_id_salary ]
			a= [line_salary_type.count(i) for i in line_salary_type ]
			for j in a:
				if j > 1:
					raise osv.except_osv(_('Warning!'),
								_('Duplicate Salary Types are not allowed !!'))
					return False
		return True	
		
	
	
	def _contract_duplicate(self, cr, uid, ids, context=None):
		obj = self.pool.get('hr.contract')
		record = self.browse(cr, uid, ids[0])
		emp_id = record.employee_id.id
		dup_ids = obj.search(cr, uid,[('employee_id','=',emp_id)])
		if len(dup_ids) > 1:
			return False
		return True
		
	
	## Module Requirement
	
	def onchange_employee_code(self, cr, uid, ids, employee_id,code, context=None):
		value = {'emp_name':'','dep_id':'','join_date':'','designation':''}
		if employee_id:
			emp = self.pool.get('hr.employee').browse(cr, uid, employee_id, context=context)
			value = {'code': emp.code,
					'department_id':emp.department_id.id,
					'join_date': emp.join_date,
					'job_id': emp.job_id.id,
					}
		return {'value': value}
		
	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])

		if rec.gross_salary <= 0:
			raise osv.except_osv(_('Warning!'),
						_('System will not allow to process with zero or Negative Values gross salary !!!'))
		else:
			
			leave_alloc_obj = self.pool.get('kg.leave.allocation')
			emp_categ_obj = self.pool.get('kg.employee.category')
			emp_categ_line = self.pool.get('ch.leave.policy')
			
			if rec.state =='confirmed':
				timein = datetime.today()
				timein = timein.strftime('%Y-%m-%d')
				gross_amt = 0.00
				self.pool.get('ch.kg.contract.pre.salary').create(cr,uid,
								{
									'header_id_pre_salary':rec.id,
									'gross_salary':rec.gross_salary,
									'updated_by':uid,
									'updated_date':timein,
									'increament_amt':rec.increament_amt,
									'mob_allowance':rec.mobile_allow
								},context = None)
				
				if rec.increament_amt > 0.00:
					gross_amt = rec.gross_salary + rec.increament_amt
				else:
					gross_amt = rec.gross_salary
					
				self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S'),'gross_salary':gross_amt,'increament_amt':0})
				
				leave_alloc_ids = leave_alloc_obj.search(cr,uid,[('employee_id','=',rec.employee_id.id)])
				if leave_alloc_ids:
					pass
				else:
					leave_alloc_vals={
									'employee_id':rec.employee_id.id,
									'emp_code':rec.code,
									'emp_categ_id':rec.emp_categ_id.id,
									'valid_from':time.strftime('%Y-%m-%d'),
									'valid_to':date(date.today().year, 12, 31),
									}
					leave_alloc_header = leave_alloc_obj.create(cr,uid,leave_alloc_vals)				
					leave_alloc_obj_1 = self.pool.get('kg.leave.allocation')
					leave_alloc_obj_line = self.pool.get('ch.leave.allocation')
					emp_categ_line_1 = emp_categ_obj.browse(cr,uid,rec.emp_categ_id.id)
					emp_leave_1 = leave_alloc_obj_1.search(cr,uid,[('employee_id','=',rec.employee_id.id)])
					for i in emp_categ_line_1.line_id_4:
						leave_allo_vals = {

							'header_id_1': emp_leave_1[0],
							'leave_type_id':i.leave_type_id.id,
							'no_of_days':i.no_of_days,
							'balc_days':i.no_of_days,

						}
						leave_allocation = leave_alloc_obj_line.create(cr,uid,leave_allo_vals)
		
		return True
		
	def _gross_salary(self,cr,uid,ids,context = None):
		rec = self.browse(cr,uid,ids[0])
		fix_amt,per_amt = 0.00,0.00
		tot_amt = 0.00
		for entry in rec.line_id_salary:
			if entry.amt_type =='fixed_amt':
				fix_amt += entry.salary_amt
			else:
				per_amt += (rec.gross_salary * entry.salary_amt)/100
				
		tot_amt = fix_amt + per_amt
		print "The gross salary is", rec.gross_salary
		print "The gross salary is",tot_amt
		if rec.gross_salary == tot_amt:
			return True
		else:
			return False
			
			
	_constraints = [
	
		#~ (_gross_salary, 'The break ups are not matching the gross salary !!!', ['  ']),		
		(child_dups_val, 'The break ups are not matching the gross salary !!!', ['  ']),		
		(_salary_brk_validation, 'The break ups are not matching the gross salary !!!', ['  ']),		
		#~ (_gross_salary_check, 'System will not allow to process with zero or Negative Values gross salary !!!', ['  ']),		

	]
		
	
kg_contract()

class ch_kg_contract_salary(osv.osv):
	
	_name = 'ch.kg.contract.salary'
	_columns = {
		'header_id_salary':fields.many2one('hr.contract','Header Id Salary',invisible= True),
		'salary_type':fields.many2one('hr.salary.rule','Salary'),
		'amt_type':fields.selection([('fixed','Fixed Amount'),('percentage','Percentage')],'Type'),
		'salary_amt':fields.float('Amount')
				}
	_defaults = {
				
				}
	
	###Validations
	
	def _neg_validation(self,cr,uid,ids,context = None):
		rec = self.browse(cr,uid,ids[0])
		if rec.salary_amt <0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values are not allowed in Salary Amount !!'))
		if rec.amt_type =='percentage':
			if rec.salary_amt > 100:
				raise osv.except_osv(_('Warning!'),
							_('Percentage per Salary type should not exceed 100 !!'))
		return True
	
	_constraints = [
	
		(_neg_validation, '!!!', ['  ']),		

	]
	
ch_kg_contract_salary()

class ch_kg_contract_pre_salary(osv.osv):
	
	_name = 'ch.kg.contract.pre.salary'
	
	_columns = {
		'header_id_pre_salary':fields.many2one('hr.contract','Header Id Pre Salary',invisible=True),
		'gross_salary':fields.float('Gross Salary',readonly=True),
		'updated_by':fields.many2one('res.users','Updated By',readonly=True),
		'updated_date':fields.date('Updated Date',readonly=True),
		'increament_amt':fields.float('Increment Amount',readonly=True),
		'mob_allowance':fields.float('Mobile Allowance',readonly=True)
				}
				
ch_kg_contract_pre_salary()

##History Tracking starts###

class ch_kg_contract_his(osv.osv):
	_name='ch.kg.contract.his'
	_columns = {
	### Basic Info

		'code': fields.char('Code', size=4, required=False),		
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
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
		'designation': fields.char('Designation', size=128, readonly=False),
		'department_id': fields.many2one('hr.department', 'Department ', readonly=True),
		'join_date': fields.date('Join Date', readonly=False),
		'gross_salary':fields.float('Gross Salary', help="Please Enter the Gross salary per month."),
		'mobile_allow':fields.float('Mobile Allowance'),
		'increament_type':fields.selection([('yearly','Yearly'),('performance','Performance'),('promotions','Promotion')],'Increment Type'),
		'increament_amt':fields.float('Increment Amount'),
		'payment_mode': fields.selection([('cheque','CHEQUE'),('bank','BANK'),('cash','CASH')], 'Payment Mode'),
		'bank_id': fields.many2one('res.bank','Bank Name'),
		'sal_acc_no': fields.char('Salary Account No', size=32),
		'ot_status': fields.boolean('OT Applicable'),
		'pt_status': fields.boolean('PT Applicable'),
		'pan_no': fields.char('PAN NO', size=32),
		'pf_status': fields.boolean('PF Applicable', size=32),
		'esi_status': fields.boolean('ESI Applicable', size=32),
		'pf_eff_date': fields.date('PF Effective From'),
		'esi_eff_date': fields.date('ESI Effective From'),
		'pf_acc_no': fields.char('PF NO', size=32),
		'esi_acc_no': fields.char('ESI NO', size=32),
		'employee_id': fields.integer('Employee_id'),
		'header_id_his':fields.many2one('hr.contract','Header Id contract History',invisible=True),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'state', readonly=True),
	}
	
	_defaults ={
	
		'entry_mode':'auto'
		}
	
ch_kg_contract_his()

class ch_kg_contract_salary_his(osv.osv):
	
	_name = 'ch.kg.contract.salary.his'
	_columns = {
		'header_id_salary_his':fields.many2one('hr.contract','Header Id Salary History',invisible= True),
		'salary_type':fields.many2one('hr.salary.rule','Salary'),
		'amt_type':fields.selection([('fixed_amt','Fixed Amount'),('percent','Percentage')],'Type'),
		'salary_amt':fields.float('Amount')
				}

ch_kg_contract_salary_his()

class ch_kg_contract_pre_salary_his(osv.osv):
	
	_name = 'ch.kg.contract.pre.salary.his'
	
	_columns = {
		'header_id_pre_salary_his':fields.many2one('hr.contract','Header Id Pre Salary History',invisible=True),
		'gross_salary':fields.float('Gross Salary',readonly=True),
		'updated_by':fields.many2one('res.users','Updated By',readonly=True),
		'updated_date':fields.date('Updated Date',readonly=True),
		'increament_amt':fields.float('Increment Amount',readonly=True),
		'mob_allowance':fields.float('Mobile Allowance',readonly=True)
				}
				
ch_kg_contract_pre_salary_his()
	
	

