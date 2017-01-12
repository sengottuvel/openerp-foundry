from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
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

		'code': fields.char('Code', size=4, required=True),		
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
		'ot_status': fields.boolean('OT Applicable'),
		'pt_status': fields.boolean('PT Applicable'),
		'pan_no': fields.char('PAN NO', size=32),
		'pf_status': fields.boolean('PF Applicable', size=32),
		'esi_status': fields.boolean('ESI Applicable', size=32),
		'pf_eff_date': fields.date('PF Effective From'),
		'esi_eff_date': fields.date('ESI Effective From'),
		'pf_acc_no': fields.char('PF NO', size=32),
		'esi_acc_no': fields.char('ESI NO', size=32),
			
		
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

	def _gross_salary_check(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.gross_salary <= 0:
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
	
	def _sal_acc_no_validation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		if flds.sal_acc_no:
			name_special_char = ''.join( c for c in flds.sal_acc_no if  c in '!@#$%^~*{}?+/=' )		
			if name_special_char:
				return False	
		return True
		
	def _pan_no_validation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		if flds.pan_no:
			name_special_char = ''.join( c for c in flds.pan_no if  c in '!@#$%^~*{}?+/=' )		
			if name_special_char:
				return False		
		return True	
		
	def _pf_acc_no_validation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		if flds.pf_acc_no:
			name_special_char = ''.join( c for c in flds.pf_acc_no if  c in '!@#$%^~*{}?+/=' )		
			if name_special_char:
				return False		
		return True		
	
	def _esi_acc_no_validation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		if flds.esi_acc_no:
			name_special_char = ''.join( c for c in flds.esi_acc_no if  c in '!@#$%^~*{}?+/=' )		
			if name_special_char:
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
					'designation': emp.job_id.name,
					}
		return {'value': value}
		
	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
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
	
		(_sal_acc_no_validation, 'Special Characters are not allowed for Salary Account No !!!', [' ']),
		(_pan_no_validation, 'Special Characters are not allowed for PAN No !!!', [' ']),
		(_pf_acc_no_validation, 'Special Characters are not allowed for PF Acc No !!!', ['  ']),		
		(_esi_acc_no_validation, 'Special Characters are not allowed for ESI Acc No !!!', ['  ']),		
		(_gross_salary, 'The break ups are not matching the gross salary !!!', ['  ']),		
		(_gross_salary_check, 'System will not allow to process with zero gross salary !!!', ['  ']),		

	]
		
	
kg_contract()

class ch_kg_contract_salary(osv.osv):
	
	_name = 'ch.kg.contract.salary'
	_columns = {
		'header_id_salary':fields.many2one('hr.contract','Header Id Salary',invisible= True),
		'salary_type':fields.many2one('hr.salary.rule','Salary'),
		'amt_type':fields.selection([('fixed_amt','Fixed Amount'),('percent','Percentage')],'Type'),
		'salary_amt':fields.float('Amount')
				}
	_defaults = {
				'amt_type':'fixed_amt',
				}
	
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
	
	

