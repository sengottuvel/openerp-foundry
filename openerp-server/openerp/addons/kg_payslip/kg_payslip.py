## HRM with Payroll System for Dr.GB Health care  ##

import math
import re
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
import netsvc
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import datetime as lastdate
import calendar
import openerp
#~ import datetime

class kg_payslip(osv.osv):
	
	_name = 'hr.payslip'	
	_inherit = 'hr.payslip'
	_order = "date desc"	
	
	_columns = {
	
	'worked_days_line_ids': fields.one2many('hr.payslip.worked_days', 'payslip_id', 'Payslip Worked Days',
			readonly=True, states={'draft': [('readonly', False)]}),
	'tot_sal': fields.float('Total Salary',readonly=True),
	'round_val': fields.float('Net Salary', readonly=True),
	'balance_val': fields.float('Balance Salary', readonly=True),
	'cross_amt': fields.float('Net Gross Amount',readonly=True),
	'con_cross_amt': fields.float('Gross Amount',readonly=True),
	'date_from': fields.date('Date From', readonly=False, required=True),
	'date_to': fields.date('Date To', readonly=False, required=True),
	'emp_name': fields.char('Employee Code', size=128, readonly=True),
	'tot_paid_days': fields.float('Total Paid Days'),
	'tot_allowance': fields.float('Total Allowance',readonly=True),
	'tot_deduction': fields.float('Total Deduction',readonly=True),
	'tot_contribution': fields.float('Total Contribution',readonly=True),
	
	'att_id': fields.many2one('kg.monthly.attendance','Attendance Ref'),
	'dep_id': fields.many2one('hr.department','Department Name'),
	'cum_ded_id': fields.many2one('kg.advance.deduction','Cumulative Deduction', readonly=True),
	'date': fields.date('Creation Date'),
	'month':fields.char('Month')
	
	}
	
	
			
	def _get_last_month_name(self, cr, uid, context=None):
		today = lastdate.date.today()
		first = lastdate.date(day=1, month=today.month, year=today.year)
		last = first - lastdate.timedelta(days=1)
		res = last.strftime('%B-%Y')
		return res
	
	def _get_last_month_first(self, cr, uid, context=None):
		
		today = lastdate.date.today()
		first = lastdate.date(day=1, month=today.month, year=today.year)
		mon = today.month - 1
		if mon == 0:
			mon = 12
		else:
			mon = mon
		tot_days = calendar.monthrange(today.year,mon)[1]
		test = first - lastdate.timedelta(days=tot_days)
		res = test.strftime('%Y-%m-%d')
		return res
		
	def _get_last_month_end(self, cr, uid, context=None):
		today = lastdate.date.today()
		first = lastdate.date(day=1, month=today.month, year=today.year)
		last = first - lastdate.timedelta(days=1)
		res = last.strftime('%Y-%m-%d')
		return res
	
	_defaults = {
		
		'month':_get_last_month_name,
		'date_from': _get_last_month_first,
		'date_to': _get_last_month_end,
		'date': lambda *a: time.strftime('%Y-%m-%d'),
		
		}	
	
	_order = "month desc"
	
	
		
	def get_contract(self, cr, uid, employee, date_from, date_to, context=None):
		"""
		@param employee: browse record of employee
		@param date_from: date field
		@param date_to: date field
		@return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
		"""
		contract_obj = self.pool.get('hr.contract')
		clause = []	
		clause_final =  [('employee_id', '=', employee.id)] 
		contract_ids = contract_obj.search(cr, uid, clause_final, context=context)
		return contract_ids
	
	def onchange_employee_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False, context=None):
		empolyee_obj = self.pool.get('hr.employee')
		contract_obj = self.pool.get('hr.contract')
		worked_days_obj = self.pool.get('hr.payslip.worked_days')
		input_obj = self.pool.get('hr.payslip.input')
		
		if context is None:
			context = {}
		#delete old worked days lines
		old_worked_days_ids = ids and worked_days_obj.search(cr, uid, [('payslip_id', '=', ids[0])], context=context) or False
		if old_worked_days_ids:
			worked_days_obj.unlink(cr, uid, old_worked_days_ids, context=context)

		#delete old input lines
		old_input_ids = ids and input_obj.search(cr, uid, [('payslip_id', '=', ids[0])], context=context) or False
		if old_input_ids:
			input_obj.unlink(cr, uid, old_input_ids, context=context)


		#defaults
		res = {'value':{
					  'line_ids':[],
					  'input_line_ids': [],
					  'worked_days_line_ids': [],
					  #'details_by_salary_head':[], TODO put me back
					  'name':'',
					  'contract_id': False,
					  'struct_id': False,
					  }
			}
		if (not employee_id) or (not date_from) or (not date_to):
			return res
		ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_from, "%Y-%m-%d")))
		employee_id = empolyee_obj.browse(cr, uid, employee_id, context=context)
		res['value'].update({
					'name': _('Salary Slip of %s for %s') % (employee_id.name, tools.ustr(ttyme.strftime('%B-%Y'))),
					'company_id': employee_id.company_id.id,
					'emp_name': employee_id.code,
		})

		if not context.get('contract', False):
			#fill with the first contract of the employee
			contract_ids = self.get_contract(cr, uid, employee_id, date_from, date_to, context=context)
		else:
			if contract_id:
				#set the list of contract for which the input have to be filled
				contract_ids = [contract_id]
			else:
				#if we don't give the contract, then the input to fill should be for all current contracts of the employee
				contract_ids = self.get_contract(cr, uid, employee_id, date_from, date_to, context=context)

		if not contract_ids:
			return res
		contract_record = contract_obj.browse(cr, uid, contract_ids[0], context=context)
		res['value'].update({
					'contract_id': contract_record and contract_record.id or False
		})
		struct_record = contract_record and contract_record.struct_id or False
		if not struct_record:
			return res
		res['value'].update({
					'struct_id': struct_record.id,
		})
		#computation of the salary input
		worked_days_line_ids = self.get_worked_day_lines(cr, uid, ids,contract_ids, date_from, date_to, context=context)
		input_line_ids = self.get_inputs(cr, uid, contract_ids, date_from, date_to, context=context)
		res['value'].update({
					'worked_days_line_ids': worked_days_line_ids,
					'input_line_idsslip_date': input_line_ids,
		})
		return res
		
	def get_worked_day_lines(self, cr, uid,ids,contract_ids, date_from, date_to, context=None):
		
		def was_on_leave(employee_id, datetime_day, context=None):
			res = False
			day = datetime_day.strftime("%Y-%m-%d")
			holiday_ids = self.pool.get('hr.holidays').search(cr, uid, [('state','=','validate'),('employee_id','=',employee_id),('type','=','remove'),('date_from','<=',day),('date_to','>=',day)])
			if holiday_ids:
				res = self.pool.get('hr.holidays').browse(cr, uid, holiday_ids, context=context)[0].holiday_status_id.name
			return res
		res = []
		for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
			if not contract.working_hours:
				emp_id = contract.employee_id.id
				start_date = "'"+date_from+"'"
				end_date = 	"'"+date_to+"'"
				month_att_obj = self.pool.get('kg.monthly.attendance')				
				sql = """ select mon_tot_days,worked from kg_monthly_attendance where employee_id=%s and start_date=%s and end_date=%s""" %(emp_id,start_date,end_date)
				cr.execute(sql)
				data = cr.dictfetchall()
				val , val1 = 0, 0
				if data:					
					val = [d['mon_tot_days'] for d in data if 'mon_tot_days' in d]
					val = val[0]
					val1 = [d['worked'] for d in data if 'worked' in d]
					val1 = val1[0]
				else:
					pass
								
				ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_from, "%Y-%m-%d")))
				name = tools.ustr(ttyme.strftime('%B-%Y'))
				worked_day_obj = self.pool.get('hr.payslip.worked_days')					
				attendances = {
					 'name': name,
					 'sequence': 1,
					 'code': 'WORK100',
					 'number_of_days': val,
					 'number_of_hours': val,
					 'contract_id': contract.id,
				}				
				res += [attendances] 
			return res	
		
	def salary_slip_calculation(self, cr, uid, ids, context=None):
		
		""" This function have full functionality of payroll process
		based on earnings and deductions, PF, Income Tax and other calculations """
		emp_obj = self.pool.get('hr.employee')
		all_ded_obj = self.pool.get('kg.allowance.deduction')
		all_ded_line_obj = self.pool.get('ch.kg.allowance.deduction')
		line_obj = self.pool.get('hr.payslip.line')
		con_obj = self.pool.get('hr.contract')
		con_line_obj = self.pool.get('ch.kg.contract.salary')
		rule_obj = self.pool.get('hr.salary.rule')
		adv_ded_obj = self.pool.get('kg.advance.deduction')
		emp = self.pool.get('hr.employee')
		#~ sal_det = self.pool.get('kg.salary.detail')
		employee_cont = self.pool.get('kg.contribution')
		employee_cont_line = self.pool.get('ch.contribution')
		
		for slip_rec in self.browse(cr, uid, ids, context=context):
			emp_rec = slip_rec.employee_id
			dep_id = emp_rec.department_id.id
			emp_nam = emp_rec.code
			#~ emp_bal_amt = emp_rec.round_off
			emp_id = slip_rec.employee_id.id
			start_date = "'"+slip_rec.date_from+"'"
			end_date = 	"'"+slip_rec.date_to+"'"
			
			
			# Employee Attendance details calculation
						
			sql = """ select worked_days,total_days,id,absent_days,working_days,ot_days,od_days,salary_days,leave_days from kg_monthly_attendance where employee_id=%s and start_date=%s
									and end_date=%s and state='approved' """ %(emp_id,start_date,end_date,)
			cr.execute(sql)
			data = cr.dictfetchall()
			worked_days, total_days,ot_days = 0,0,0
			att_id = False
			if data:					
				
				val1 = [d['worked_days'] for d in data if 'worked_days' in d]
				worked_days = val1[0]
				
				val3 = [d['working_days'] for d in data if 'working_days' in d]
				working_days= val3[0]
								
				val7 = [d['total_days'] for d in data if 'total_days' in d]
				total_days = val7[0]	
				tot_days = total_days
				
				val4 = [d['ot_days'] for d in data if 'ot_days' in d]
				ot_days = val4[0]
				
				val2 = [d['absent_days'] for d in data if 'absent_days' in d]
				absent = val2[0]
				
				val8 = [d['leave_days'] for d in data if 'leave_days' in d]
				leave_days = val8[0]
				
				val5 = [d['salary_days'] for d in data if 'salary_days' in d]
				salary_days = val5[0]
				####### OT Calculation if OT applicable for the employee in the contract########
				con_src = con_obj.search(cr,uid,[('employee_id','=',emp_id)])
				con_rec = con_obj.browse(cr,uid,con_src[0])
				if con_rec.ot_status:
					salary_days = salary_days + ot_days
				####### OT Calculation if OT applicable for the employee in the contract########
				
				self.write(cr, uid, ids, {'tot_paid_days': salary_days})
				
				
				
				#### Creation of the Salary components Described in the Contract of the employee ####
				
				con_ids = con_obj.search(cr,uid,[('employee_id','=',emp_id)])
				con_ids_1 = con_obj.browse(cr,uid,con_ids[0])
				self.write(cr, uid, ids, {'con_cross_amt': con_ids_1.gross_salary})
				amt_sal=0.00
				esi_amt_sal=0.00
				pf_amt=0.00
				pf_stand_amt=0
				esi_amt=0.00
				esi_stand_amt=0
				for con_line_ids in con_ids_1.line_id_salary:
					print "********************************************",con_line_ids.salary_type.categ_type
					print "********************************************",con_line_ids.salary_type.id
					if con_line_ids.salary_type.categ_type == 'ALW':
						categ_ids = 2
					elif con_line_ids.salary_type.categ_type == 'DED':
						categ_ids = 4
					else:
						categ_ids = 1
					if con_line_ids.salary_type.code == 'BASIC':
						categ_ids = 1
					if con_line_ids.amt_type == 'percentage':
						comp_amt = (((con_ids_1.gross_salary * con_line_ids.salary_amt)/100)/working_days)
					else:
						comp_amt = (con_line_ids.salary_amt/working_days)
						
					mon_sal = (comp_amt*salary_days)
						
					self.pool.get('hr.payslip.line').create(cr,uid,
									{
										'name':con_line_ids.salary_type.name,
										'code':con_line_ids.salary_type.code,
										'category_id':categ_ids,
										'quantity':1,
										'amount':mon_sal,
										'salary_rule_id':con_line_ids.salary_type.id,
										'employee_id':emp_id,
										'contract_id':con_ids[0],
										'slip_id':slip_rec.id,
									},context = None)
					
					if con_ids_1.pf_status and con_ids_1.pf_eff_date <= slip_rec.date_to and con_line_ids.salary_type.app_pf:
						amt_sal += mon_sal
					if con_ids_1.esi_status and con_ids_1.esi_eff_date <= slip_rec.date_to and con_line_ids.salary_type.app_esi:
						esi_amt_sal += mon_sal
							
									
				#### Creation of the Salary components Described in the Contract of the employee ####
				
			#### PF calculation for each employee ####	

				empr_pf_ids = employee_cont.search(cr , uid ,[('active','=',True),('state','=','approved')])
				emp_pf_rec = employee_cont.browse(cr,uid,empr_pf_ids[0])
				if amt_sal > emp_pf_rec.pf_max_amt:
					pf_stand_amt = emp_pf_rec.pf_max_amt
				else:
					pf_stand_amt = amt_sal
				if pf_stand_amt > 0:
					empr_pf_line_ids = employee_cont_line.search(cr , uid ,[('cont_heads','=','pf'),('header_id','=',emp_pf_rec.id)])
					emp_pf_line_rec = employee_cont_line.browse(cr,uid,empr_pf_line_ids[0])
					if emp_pf_line_rec.cont_type == 'percent':
						pf_emp_amt = (pf_stand_amt * emp_pf_line_rec.emp_cont_value)/100
					else:
						pf_emp_amt = emp_pf_line_rec.emp_cont_value
				else:
					pass
				if con_ids_1.pf_status and pf_stand_amt > 0:		
					self.pool.get('hr.payslip.line').create(cr,uid,
							{
								'name':'Employee - '+emp_pf_line_rec.cont_heads,
								'code':'PF',
								'category_id':4,
								'quantity':1,
								'amount':pf_emp_amt,
								'salary_rule_id':1,
								'employee_id':emp_id,
								'contract_id':con_ids[0],
								'slip_id':slip_rec.id,
							},context = None)
				
			#### PF calculation for each employee ####	
			
			#### ESI calculation for each employee ####	
				
				empr_esi_ids = employee_cont.search(cr , uid ,[('active','=',True),('state','=','approved')])
				emp_esi_rec = employee_cont.browse(cr,uid,empr_esi_ids[0])
				if con_ids_1.gross_salary < emp_esi_rec.esi_slab:
					esi_stand_amt = esi_amt_sal
				else:
					esi_stand_amt = 0
				if esi_stand_amt > 0:
					print "*********************************************************************************************",esi_stand_amt
					empr_esi_line_ids = employee_cont_line.search(cr , uid ,[('cont_heads','=','esi'),('header_id','=',emp_esi_rec.id)])
					emp_esi_line_rec = employee_cont_line.browse(cr,uid,empr_esi_line_ids[0])
					if emp_esi_line_rec.cont_type == 'percent':
						esi_emp_amt = (esi_stand_amt * emp_esi_line_rec.emp_cont_value)/100
						esi_emplr_amt = (esi_stand_amt * emp_esi_line_rec.emplr_cont_value)/100
						print "************emp_esi_line_rec.emp_cont_value*********************************",emp_esi_line_rec.emp_cont_value
						print "************esi_stand_amtesi_stand_amtesi_stand_amtesi_stand_amt*********************************",esi_emp_amt
					else:
						esi_emp_amt = emp_esi_line_rec.emp_cont_value
						esi_emplr_amt = emp_esi_line_rec.emplr_cont_value
					if con_ids_1.esi_status and esi_stand_amt > 0:
						self.pool.get('hr.payslip.line').create(cr,uid,
								{
									'name':'Employee - '+emp_esi_line_rec.cont_heads,
									'code':'ESI',
									'category_id':4,
									'quantity':1,
									'amount':esi_emp_amt,
									'salary_rule_id':1,
									'employee_id':emp_id,
									'contract_id':con_ids[0],
									'slip_id':slip_rec.id,
								},context = None)
				else:
					pass
				
				
				
				#### ESI calculation for each employee ####	
				
				#### Creation of the allowance or deduction per month for the employee ####
				
				all_ded_ids = all_ded_obj.search(cr,uid,[('start_date','=',slip_rec.date_from),('end_date','=',slip_rec.date_to),('state','=','approved')])
				if all_ded_ids:
					all_ded_rec = all_ded_obj.browse(cr,uid,all_ded_ids[0])
					all_ded_lines = all_ded_line_obj.search(cr,uid,[('header_id','=',all_ded_ids[0])])
					for line_ids in all_ded_lines:
						all_ded_line_rec = all_ded_line_obj.browse(cr,uid,line_ids)
						if all_ded_line_rec.employee_id.id == emp_id:
							if all_ded_rec.allow_type == 'ALW':
								categ_ids = 2
							elif all_ded_rec.allow_type == 'DED':
								categ_ids = 4
							self.pool.get('hr.payslip.line').create(cr,uid,
								{
									'name':all_ded_rec.pay_type.name,
									'code':all_ded_rec.pay_type.code,
									'category_id':categ_ids,
									'quantity':1,
									'amount':all_ded_line_rec.amount,
									'salary_rule_id':1,
									'employee_id':emp_id,
									'contract_id':con_ids[0],
									'slip_id':slip_rec.id,
								},context = None)
							

				#### Creation of the allowance or deduction per month for the employee ####
				
				#### Creation of the advance deduction per month for the employee ####
				
				adv_ded_ids = adv_ded_obj.search(cr,uid,[('employee_id','=',emp_id),('bal_amt','!=',0.00),('state','=','approved'),('allow','=',True)])
				if adv_ded_ids:
					for idss in adv_ded_ids:
						print "idsssssssssssssssssssssssssssssssssssssss",idss	
						adv_ded_rec = adv_ded_obj.browse(cr,uid,idss)
						self.pool.get('hr.payslip.line').create(cr,uid,
								{
									'name':'Advance - '+adv_ded_rec.ded_type,
									'code':'ADV',
									'category_id':4,
									'quantity':1,
									'amount':adv_ded_rec.pay_amt,
									'salary_rule_id':adv_ded_rec.id,
									'employee_id':emp_id,
									'contract_id':con_ids[0],
									'slip_id':slip_rec.id,
								},context = None)
						allow_update = adv_ded_rec.write({'bal_amt': (adv_ded_rec.bal_amt - adv_ded_rec.pay_amt),'amt_paid': (adv_ded_rec.amt_paid + adv_ded_rec.pay_amt)})

				#### Creation of the advance deduction per month for the employee ####
				
				#### Creation of Incentive for the employee ####
				
				if con_ids_1.special_incentive:
					today = lastdate.date.today()
					first = lastdate.date(day=1, month=today.month, year=today.year)
					last = first - lastdate.timedelta(days=1)
					res = last.strftime('%B')
					datetttt = slip_rec.date_from
					d1 = str(res)
					print "Special incentive called -----------------------------------------------------",d1[:3]
					turn_over_ids = self.pool.get('kg.turn.over').search(cr,uid,[('month','=',d1[:3]),('active','=',True)])
					turn_over_amt = 0.00
					incent_amt = 0.00
					if turn_over_ids:
						turn_over_rec = self.pool.get('kg.turn.over').browse(cr,uid,turn_over_ids[0])
						print "turn_over_recturn_over_recturn_over_recturn_over_rec",turn_over_rec.month
						turn_over_amt = turn_over_rec.amt * 100
						emp_categ_ids = self.pool.get('kg.employee.category').search(cr,uid,[('id','=',con_ids_1.emp_categ_id.id),('state','=','approved')])
						print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%",emp_categ_ids
						if emp_categ_ids:
							emp_categ_rec = self.pool.get('kg.employee.category').browse(cr,uid,emp_categ_ids[0])
							print "emp_categ_recemp_categ_recemp_categ_recemp_categ_rec",emp_categ_rec.id
							inc_ids = self.pool.get('ch.incentive.policy').search(cr,uid,[('header_id_5','=',emp_categ_rec.id)])
							print "inc_idsinc_idsinc_idsinc_idsinc_idsinc_ids",inc_ids
							
							######### Incentive Calculation ###########
							if inc_ids:
								for incentive_ids in inc_ids:
									print "incentive_idsincentive_idsincentive_idsincentive_idsincentive_ids",incentive_ids
									print "turn_over_amtturn_over_amtturn_over_amt",turn_over_amt
									inc_ids = self.pool.get('ch.incentive.policy').browse(cr,uid,incentive_ids)
									if turn_over_amt >= inc_ids.start_value and turn_over_amt <= inc_ids.end_value:
										if inc_ids.type == 'per_lhk_fixed':
											print "*********inc_ids.incentive_value************",inc_ids.incentive_value
											print "*********working_days************",working_days
											print "*********worked_days************",worked_days
											incent_amt = ((turn_over_amt*inc_ids.incentive_value)/working_days)*worked_days
										elif inc_ids.type == 'percentage':
											turn_over_per = (turn_over_amt*inc_ids.incentive_value)/100
											incent_amt = ((turn_over_per)/working_days)*worked_days
										else:
											incent_amt = ((turn_over_per)/working_days)*worked_days
										self.pool.get('hr.payslip.line').create(cr,uid,
												{
													'name':'Incentive',
													'code':'INC',
													'category_id':7,
													'quantity':1,
													'amount':incent_amt,
													'salary_rule_id':1,
													'employee_id':emp_id,
													'contract_id':con_ids[0],
													'slip_id':slip_rec.id,
												},context = None)
						######### Incentive Calculation ###########
						######### Special Incentive Calculation ###########
						turn_over_amt = turn_over_rec.amt 
						spl_inc_ids = self.pool.get('ch.special.incentive.policy').search(cr,uid,[('header_id_1','=',emp_categ_rec.id),('start_value','<=',turn_over_amt)])
						print "^^^^^^^^^^^^^^^^^^^",spl_inc_ids
						if spl_inc_ids:
							get_spl_inc = self.pool.get('hr.payslip.line').search(cr,uid,[('code','=','SPI'),('slip_id','=',slip_rec.id)])
							if get_spl_inc:
								get_spl_inc_rc = self.pool.get('hr.payslip.line').browse(cr,uid,get_spl_inc[0])
							aaaa=0.00	
							for special_inc_ids in spl_inc_ids:
								splss_inc_ids = self.pool.get('ch.special.incentive.policy').browse(cr,uid,special_inc_ids)
								#~ if turn_over_amt >= splss_inc_ids.start_value and turn_over_amt <= splss_inc_ids.end_value:
								#~ if splss_inc_ids.start_value <= turn_over_amt :
								
								if get_spl_inc:
									if splss_inc_ids.type == 'per_cr_fixed':
										print "*********inc_ids.incentive_value************",inc_ids.incentive_value
										print "*********working_days************",working_days
										print "*********worked_days************",worked_days
										spl_incent_amt = ((turn_over_amt*splss_inc_ids.incentive_value)/working_days)*worked_days
									if splss_inc_ids.type == 'percentage':
										get_spl_inc_rec = self.pool.get('hr.payslip.line').browse(cr,uid,get_spl_inc[0])
										aaaa += splss_inc_ids.incentive_value
										spl_inc_amt = (get_spl_inc_rec.amount * aaaa)/100
										spl_incent_amt = get_spl_inc_rec.amount + spl_inc_amt
							if get_spl_inc:
								self.pool.get('hr.payslip.line').write(cr,uid,get_spl_inc_rc.id,
										{
											
											'amount':spl_incent_amt,
										})
								
						######### Special Incentive Calculation ###########
				
				#### Creation of Incentive for the employee ####	
				
				#### Creation of attendance bonus ##########
				
				if con_ids_1.bonus_applicable:
					emp_categ_ids = self.pool.get('kg.employee.category').search(cr,uid,[('id','=',con_ids_1.emp_categ_id.id),('state','=','approved')])
					if emp_categ_ids:
						emp_categ_rec = self.pool.get('kg.employee.category').browse(cr,uid,emp_categ_ids[0])
						if emp_categ_rec.bonus_categ == 'attendance':
							print "absentabsentabsentabsentabsent",absent
							print "leave_daysleave_daysleave_daysleave_days",leave_days
							if (absent+leave_days) <= emp_categ_rec.no_of_days_wage:
								self.pool.get('hr.payslip.line').create(cr,uid,
									{
										'name':'Attendance Bonus',
										'code':'ATTB',
										'category_id':8,
										'quantity':1,
										'amount':(comp_amt * emp_categ_rec.no_of_days_wage),
										'salary_rule_id':1,
										'employee_id':emp_id,
										'contract_id':con_ids[0],
										'slip_id':slip_rec.id,
									},context = None)
							else:
								pass
								
				if salary_days >= working_days:
					emp_categ_ids = self.pool.get('kg.employee.category').search(cr,uid,[('id','=',con_ids_1.emp_categ_id.id),('state','=','approved')])
					if emp_categ_ids:
						emp_categ_rec = self.pool.get('kg.employee.category').browse(cr,uid,emp_categ_ids[0])
						emplo = emp_obj.browse(cr,uid,emp_id)
						if emplo.gender == 'male':
							att_ins = emp_categ_rec.attnd_insentive_male
						else:
							att_ins = emp_categ_rec.attnd_insentive_female
						self.pool.get('hr.payslip.line').create(cr,uid,
								{
									'name':'100% Attendance Bonus',
									'code':'ATTB',
									'category_id':8,
									'quantity':1,
									'amount':att_ins,
									'salary_rule_id':1,
									'employee_id':emp_id,
									'contract_id':con_ids[0],
									'slip_id':slip_rec.id,
								},context = None)
				#### Creation of attendance bonus ##########
				
				#### Creation of the Driver Batta per month for the employee ####	
				
				if con_ids_1.driver_bata_app:
					print "Driver bataa called --------------------------------------------------"
					emp_categ_ids = self.pool.get('kg.employee.category').search(cr,uid,[('id','=',con_ids_1.emp_categ_id.id),('state','=','approved')])
					if emp_categ_ids:
						emp_categ_rec = self.pool.get('kg.employee.category').browse(cr,uid,emp_categ_ids[0])
						if emp_categ_rec.driver_batta > 0.00:
							driv_bata = emp_categ_rec.driver_batta  * salary_days
							self.pool.get('hr.payslip.line').create(cr,uid,
									{
										'name':'Driver Batta',
										'code':'DRB',
										'category_id':2,
										'quantity':1,
										'amount':driv_bata,
										'salary_rule_id':1,
										'employee_id':emp_id,
										'contract_id':con_ids[0],
										'slip_id':slip_rec.id,
									},context = None)
				#### Creation of the Driver Batta per month for the employee ####	
				
				#### Creation of the total allowance and updating the total allowance field in parent ####
				
				serc_chil_ids = self.pool.get('hr.payslip.line').search(cr,uid,[('slip_id','=',slip_rec.id),('category_id','in',(2,8,7))])
				print "serc_chil_idsserc_chil_idsserc_chil_idsserc_chil_idsserc_chil_ids",serc_chil_ids
				tot_allow_amt = 0.00
				for payslip_line_ids_all in serc_chil_ids:
					payslip_line_rec = self.pool.get('hr.payslip.line').browse(cr,uid,payslip_line_ids_all)
					tot_allow_amt += payslip_line_rec.amount
				self.write(cr, uid, ids, {'tot_allowance': tot_allow_amt})
				
				#### Creation of the total allowance and updating the total allowance field in parent ####
				
				#### Creation of the total deduction and updating the total allowance field in parent ####
				
				serc_chil_ids_1 = self.pool.get('hr.payslip.line').search(cr,uid,[('slip_id','=',slip_rec.id),('category_id','=',4)])
				print "serc_chil_idsserc_chil_idsserc_chil_idsserc_chil_idsserc_chil_ids",serc_chil_ids_1
				tot_ded_amt = 0.00
				for payslip_line_ids_ded in serc_chil_ids_1:
					payslip_line_rec = self.pool.get('hr.payslip.line').browse(cr,uid,payslip_line_ids_ded)
					tot_ded_amt += payslip_line_rec.amount
				self.write(cr, uid, ids, {'tot_deduction': tot_ded_amt})
				
				#### Creation of the total deduction and updating the total allowance field in parent ####
				
				#### Creation of the net gross amount in the parent ####
				
				serc_chil_ids_2 = self.pool.get('hr.payslip.line').search(cr,uid,[('slip_id','=',slip_rec.id)])
				net_gross_amt = 0.00	
				for payslip_net_gross in serc_chil_ids_2:
					payslip_line_rec = self.pool.get('hr.payslip.line').browse(cr,uid,payslip_net_gross)
					net_gross_amt += payslip_line_rec.amount
				self.write(cr, uid, ids, {'cross_amt': net_gross_amt,'round_val':net_gross_amt-tot_ded_amt})
				
				#### Creation of the net gross amount in the parent ####
				
				
				
				
					
				
				
				
				
				
				
			else:
				raise osv.except_osv(
						_('Error !!'),
						_('Attendance entry not availabe for employee -  %s !!'%(slip_rec.employee_id.name)))
			
			
			
		
		
			
	def hr_verify_sheet(self, cr, uid, ids, context=None):
		self.salary_slip_calculation(cr, uid, ids, context)
		return self.write(cr, uid, ids, {'state': 'done'}, context=context)
		
	
	def employee_salary_run(self, cr, uid, ids, context=None):
		
		""" This function will generate employee payslip 
		if any changes needed after salary process has done """
		
		slip_obj = self.pool.get('hr.payslip')
		contract_obj = self.pool.get('hr.contract')
		slip_rec = self.browse(cr, uid, ids[0])
		emp_rec = slip_rec.employee_id
		#~ last_mon_bal = slip_rec.employee_id.last_month_bal
		#~ round_bal = slip_rec.employee_id.round_off
		#~ emp_rec.write({'round_off': last_mon_bal})
		self.salary_slip_calculation(cr,uid, ids)
		cont_ids = contract_obj.search(cr,uid,[('employee_id','=',slip_rec.employee_id.id)])
		if cont_ids:
			ex_ids = slip_obj.search(cr, uid, [('employee_id','=', slip_rec.employee_id.id),
						('date_from','=',slip_rec.date_from),('date_to','=',slip_rec.date_to),
						('state','=', 'done')])
			for i in ex_ids:
				sql = """ delete from hr_payslip where id=%s """%(i)
				cr.execute(sql)
				
			slip_rec.write({'state': 'done'})
		else:
			raise osv.except_osv(_('Warning!'),_('Contract is not created for the employee !!'))		
		
		
	def cancel_entry(self,cr,uid,ids,context = None):
		slip_obj = self.pool.get('hr.payslip')
		slip_rec = self.browse(cr, uid, ids[0])
		####### Reverting the advance amount of the employee for this month while cancelling ################
		slip_line=self.pool.get('hr.payslip.line').search(cr,uid,[('slip_id','=',slip_rec.id),('code','=','ADV')])
		for line_ids in slip_line:
			slip_line_rec = self.pool.get('hr.payslip.line').browse(cr,uid,line_ids)
			adv_rec = self.pool.get('kg.advance.deduction').browse(cr,uid,slip_line_rec.salary_rule_id.id)
			print "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$",adv_rec.id
			self.pool.get('kg.advance.deduction').write(cr,uid,adv_rec.id,{'bal_amt':adv_rec.bal_amt+slip_line_rec.amount,'amt_paid':adv_rec.amt_paid-slip_line_rec.amount})
		####### Reverting the advance amount of the employee for this month while cancelling ################
		sql = """ delete from hr_payslip_line where slip_id=%s """%(slip_rec.id)
		cr.execute(sql)
		sql_parent = """ update hr_payslip set tot_deduction=null ,con_cross_amt=null,cross_amt =null,tot_paid_days =null,tot_allowance=null,
		round_val=null where id =%s """%(slip_rec.id)
		cr.execute(sql_parent)
		
		slip_rec.write({'state': 'draft'})		
		
	def print_individual_payslip(self, cr, uid, ids, context=None):		
		rec = self.browse(cr,uid,ids[0])	
		assert len(ids) == 1, 'This option should only be used for a single id at a time'
		wf_service = netsvc.LocalService("workflow")
		wf_service.trg_validate(uid, 'hr.payslip', ids[0], 'send_rfq', cr)
		datas = {
				 'model': 'hr.payslip',
				 'ids': ids,
				 'form': self.read(cr, uid, ids[0], context=context),
		}
		return {'type': 'ir.actions.report.xml', 'report_name': 'onscreen.emp.payslip', 'datas': datas, 'ids' : ids,'name':'Employee_Payslip', 'nodestroy': True}	
		
	
		
		
kg_payslip()


class kg_batch_payslip(osv.osv): 
	
	_name = 'hr.payslip.run'	
	_inherit = 'hr.payslip.run'	
	
	_columns = {
	
	'name': fields.char('Month', size=64, readonly=True),
	'date_start': fields.date('Date From', required=True, readonly=False),
	'date_end': fields.date('Date To', required=True, readonly=False),
	'slip_date': fields.date('Creation Date'),
	'slip_ids': fields.one2many('hr.payslip', 'payslip_run_id', 'Payslips', required=False, readonly=True),
	'state': fields.selection([
			('draft', 'Draft'),			
			('done', 'Done'),
			('close', 'Close'),
		], 'Status', select=True, readonly=True),
	
	}
	
	def _get_last_month_first(self, cr, uid, context=None):
		
		today = lastdate.date.today()
		first = lastdate.date(day=1, month=today.month, year=today.year)
		mon = today.month - 1
		if mon == 0:
			mon = 12
		else:
			mon = mon
		tot_days = calendar.monthrange(today.year,mon)[1]
		test = first - lastdate.timedelta(days=tot_days)
		res = test.strftime('%Y-%m-%d')
		return res
		
	def _get_last_month_end(self, cr, uid, context=None):
		today = lastdate.date.today()
		first = lastdate.date(day=1, month=today.month, year=today.year)
		last = first - lastdate.timedelta(days=1)
		res = last.strftime('%Y-%m-%d')
		return res
		
	def _get_last_month_name(self, cr, uid, context=None):
		today = lastdate.date.today()
		first = lastdate.date(day=1, month=today.month, year=today.year)
		last = first - lastdate.timedelta(days=1)
		res = last.strftime('%B-%Y')
		return res
		
	def _check_employee_slip_dup(self, cr, uid, ids, context=None):		
		obj = self.pool.get('hr.payslip.run')
		slip = self.browse(cr, uid, ids[0])
		date_from = slip.date_start
		to_date = slip.date_end
		dup_ids = obj.search(cr, uid, [( 'date_start','=',date_from),( 'date_end','=',to_date),
									( 'state','=','done')])
		if len(dup_ids) > 1:
			return False
		return True
		
	def print_monthly_individual_payslip(self, cr, uid, ids, context=None):		
		rec = self.browse(cr,uid,ids[0])	
		assert len(ids) == 1, 'This option should only be used for a single id at a time'
		wf_service = netsvc.LocalService("workflow")
		wf_service.trg_validate(uid, 'hr.payslip.run', ids[0], 'send_rfq', cr)
		datas = {
				 'model': 'hr.payslip.run',
				 'ids': ids,
				 'form': self.read(cr, uid, ids[0], context=context),
		}
		return {'type': 'ir.actions.report.xml', 'report_name': 'onscreen.all.emp.payslip','name':'Employee_Individual_Payslip','datas': datas, 'ids' : ids, 'nodestroy': True}	
		
	def print_monthly_payslip(self, cr, uid, ids, context=None):		
		rec = self.browse(cr,uid,ids[0])	
		assert len(ids) == 1, 'This option should only be used for a single id at a time'
		wf_service = netsvc.LocalService("workflow")
		wf_service.trg_validate(uid, 'hr.payslip.run', ids[0], 'send_rfq', cr)
		datas = {
				 'model': 'hr.payslip.run',
				 'ids': ids,
				 'form': self.read(cr, uid, ids[0], context=context),
		}
		return {'type': 'ir.actions.report.xml', 'report_name': 'onscreen.salary.muster','name':'Employee_Salary_Muster','datas': datas, 'ids' : ids, 'nodestroy': True}	
		
	#_constraints = [
		
		#(_check_employee_slip_dup, 'Payslip has been created already for this month. Check Month and State !!',['amount']),
		
		#] 
		
	
	_defaults = {
	
		'name' : _get_last_month_name,
		'date_start': _get_last_month_first,
		'date_end': _get_last_month_end,
		'slip_date': lambda *a: time.strftime('%Y-%m-%d'),
		
		}
	

	def unlink(self, cr, uid, ids, context=None):
		for batch in self.browse(cr, uid, ids, context=context):
			if batch.state not in  ['draft']:
				raise osv.except_osv(_('Warning!'),_('You cannot delete this Batch which is not in draft state !!'))
		return super(kg_batch_payslip, self).unlink(cr, uid, ids, context)


kg_batch_payslip()


class kg_salary_structure(osv.osv):
	
	_name = 'hr.payroll.structure'	
	_inherit = 'hr.payroll.structure'
	
	_columns = {
	
	'state': fields.selection([('draft','Draft'),('approved','Approved')], 'Status', readonly=True),
		
	}
	
	_defaults = {
	
	'state': 'draft',
	
	}
	
	def unlink(self, cr, uid, ids, context=None):
		contract_obj = self.pool.get('hr.contract')
		data = contract_obj.search(cr, uid, (['struct_id','=', ids[0]]))
		if batch.state not in  ['draft']:
			raise osv.except_osv(_('Warning!'),_('You cannot delete this Batch which is not draft state !!'))
		return super(kg_batch_payslip, self).unlink(cr, uid, ids, context)
	
kg_salary_structure()