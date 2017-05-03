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
	'othr_sal_amt': fields.float('Other Salary Amount',readonly=True),
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
	'month':fields.char('Month'),
	'emp_categ_id':fields.many2one('kg.employee.category','Category'),
	'division_id':fields.many2one('kg.division.master','Division'),
	
	###### Line Declarations ########
	'line_id_other_sal':fields.one2many('ch.other.salary.comp','slip_id','Line Id Other Salary'),
	
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
					'emp_categ_id': employee_id.emp_categ_id.id,
					'division_id': employee_id.division_id.id,
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
				sql = """ select total_days,worked_days from kg_monthly_attendance where employee_id=%s and start_date=%s and end_date=%s""" %(emp_id,start_date,end_date)
				cr.execute(sql)
				data = cr.dictfetchall()
				val , val1 = 0, 0
				if data:					
					val = [d['total_days'] for d in data if 'total_days' in d]
					val = val[0]
					val1 = [d['worked_days'] for d in data if 'worked_days' in d]
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
			
			cont_ids = con_obj.search(cr,uid,[('employee_id','=',slip_rec.employee_id.id)])
			if cont_ids:
				ex_ids = self.pool.get('hr.payslip').search(cr, uid, [('employee_id','=', slip_rec.employee_id.id),
							('date_from','=',slip_rec.date_from),('date_to','=',slip_rec.date_to),
							('state','=', 'done')])
				for i in ex_ids:
					sql = """ delete from hr_payslip where id=%s """%(i)
					cr.execute(sql)
			
			
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
				con_src = con_obj.search(cr,uid,[('employee_id','=',emp_id),('state','=','approved')])
				if not con_src:
					raise osv.except_osv(_('Warning'),
							_('Contract is not approved for %s'%(slip_rec.employee_id.name)))
				con_rec = con_obj.browse(cr,uid,con_src[0])
				if con_rec.ot_status:
					salary_days = salary_days + ot_days
				####### OT Calculation if OT applicable for the employee in the contract########
				
				self.write(cr, uid, slip_rec.id, {'tot_paid_days': salary_days})
				
				
				
				#### Creation of the Salary components Described in the Contract of the employee ####
				
				con_ids = con_obj.search(cr,uid,[('employee_id','=',emp_id),('state','=','approved')])
				con_ids_1 = con_obj.browse(cr,uid,con_ids[0])
				self.write(cr, uid, ids, {'con_cross_amt': con_ids_1.gross_salary})
				amt_sal=0.00
				esi_amt_sal=0.00
				pf_amt=0.00
				pf_stand_amt=0
				esi_amt=0.00
				esi_stand_amt=0
				bns_att = 0.00
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
					if con_ids_1.emp_categ_id.sal_calc == 'cal_days':
						calulation_days = total_days
					else:
						calulation_days = working_days
					if con_line_ids.amt_type == 'percentage':
						comp_amt = (((con_ids_1.gross_salary * con_line_ids.salary_amt)/100)/calulation_days)
					else:
						comp_amt = (con_line_ids.salary_amt/calulation_days)
						
					mon_sal = (comp_amt*salary_days)
						
					if con_line_ids.salary_type.appears_on_payslip == True:
						
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
					else:
						self.pool.get('ch.other.salary.comp').create(cr,uid,
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
							
					bns_att += comp_amt				
				#### Creation of the Salary components Described in the Contract of the employee ####
			#### VDA calculation for each employee ####
				
				if con_ids_1.vda_status:
					
					emp_recs = emp_obj.browse(cr,uid,con_ids_1.employee_id.id)
					div_rec = self.pool.get('kg.division.master').browse(cr,uid,emp_recs.division_id.id)
					print "___________points from division master____________________",div_rec.da_ded_points
					today = lastdate.date.today()
					first = lastdate.date(day=1, month=today.month, year=today.year)
					last = first - lastdate.timedelta(days=1)
					res = last.strftime('%B')
					datetttt = slip_rec.date_from
					print "+++++++date from++++++++++++",datetttt[5:7]
					a = datetttt[5:7]
					b = (calendar.month_abbr[int(a)])
					print "+++++++date Month++++++++++++",b
					d1 = str(res)
					print "Special incentive called -----------------------------------------------------",b
					turn_over_idss = self.pool.get('kg.turn.over').search(cr,uid,[('month','=',b),('active','=',True)])
					if turn_over_idss:
						turn_over_recs = self.pool.get('kg.turn.over').browse(cr,uid,turn_over_idss[0])
						print "$$$$$$---------- Chamber in turn over -------$$$$$$$$$",turn_over_recs.da_chamber
						vda_value_1 = (turn_over_recs.da_chamber - div_rec.da_ded_points)
						emp_cont_id = self.pool.get('kg.contribution').search(cr,uid,[('active','=',True),('state','=','approved')])
						print "^^^^^^^^^^^^^^^^^^^^^",emp_cont_id
						#~ stop
						emp_contt_ids = self.pool.get('ch.contribution').search(cr,uid,[('header_id','=',emp_cont_id),('cont_heads','=','vda')])
						if emp_contt_ids:
							emp_contt_rec = self.pool.get('ch.contribution').browse(cr,uid,emp_contt_ids[0])
							print "*********vda value in paise*****************",emp_contt_rec.emplr_cont_value
							
							vda_for_att_bon = vda_value_1*emp_contt_rec.emplr_cont_value
							print "*********vda value For Attendance Bonus*****************",vda_for_att_bon
							acc_vda_value = ((vda_value_1*emp_contt_rec.emplr_cont_value)/calulation_days)*salary_days
							self.pool.get('hr.payslip.line').create(cr,uid,
								{
									'name':'VDA',
									'code':'VDA',
									'category_id':2,
									'quantity':1,
									'amount':acc_vda_value,
									'salary_rule_id':1,
									'employee_id':emp_id,
									'contract_id':con_ids[0],
									'slip_id':slip_rec.id,
								},context = None)
					else:
						raise osv.except_osv(_('Warning'),
							_('Turn Over is not fixed for last month for VDA Calculation !!'))				
				else:
					acc_vda_value = 0.00
					pass
					
					
				
				
				#### VDA calculation for each employee ####
				
			#### PF calculation for each employee ####	

				empr_pf_ids = employee_cont.search(cr , uid ,[('active','=',True),('state','=','approved')])
				emp_pf_rec = employee_cont.browse(cr,uid,empr_pf_ids[0])
				if amt_sal:
					if amt_sal + acc_vda_value > emp_pf_rec.pf_max_amt:
						pf_stand_amt = emp_pf_rec.pf_max_amt
					else:
						pf_stand_amt = amt_sal + acc_vda_value
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
				if esi_amt_sal:
					if esi_amt_sal + acc_vda_value < emp_esi_rec.esi_slab:
						esi_stand_amt = esi_amt_sal + acc_vda_value
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
				for iiii in all_ded_ids:
					#~ if all_ded_ids:
					all_ded_rec = all_ded_obj.browse(cr,uid,iiii)
					all_ded_lines = all_ded_line_obj.search(cr,uid,[('header_id','=',iiii)])
					for line_ids in all_ded_lines:
						all_ded_line_rec = all_ded_line_obj.browse(cr,uid,line_ids)
						if all_ded_line_rec.employee_id.id == emp_id:
							if all_ded_rec.allow_type == 'ALW':
								categ_ids = 2
							elif all_ded_rec.allow_type == 'DED':
								categ_ids = 4
							if all_ded_rec.pay_type.appears_on_payslip is True:
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
							else:
								self.pool.get('ch.other.salary.comp').create(cr,uid,
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
									'salary_rule_id':1,
									'cum_ded_id':adv_ded_rec.id,
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
					print "+++++++date from++++++++++++",datetttt[5:7]
					a = datetttt[5:7]
					b = (calendar.month_abbr[int(a)])
					print "+++++++date Month++++++++++++",b
					d1 = str(res)
					print "Special incentive called -----------------------------------------------------",b
					turn_over_ids = self.pool.get('kg.turn.over').search(cr,uid,[('month','=',b),('active','=',True)])
					turn_over_amt = 0.00
					turn_over_per = 0.00
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
								inc_rec = self.pool.get('ch.incentive.policy').browse(cr,uid,inc_ids[0])
								for incentive_ids in inc_ids:
									#~ cal_days = salary_days - leave_days
									#~ if (absent+leave_days) >= inc_rec.leave_consider:
										#~ wor_days =  cal_days + inc_rec.leave_consider
										#~ print "wor_dayswor_dayswor_dayswor_days",wor_days
									#~ else:
										#~ wor_days = salary_days + absent
										#~ print "wor_dayswor_dayswor_dayswor_days",wor_days
									print "incentive_idsincentive_idsincentive_idsincentive_idsincentive_ids",incentive_ids
									print "turn_over_amtturn_over_amtturn_over_amt",turn_over_amt
									inc_ids = self.pool.get('ch.incentive.policy').browse(cr,uid,incentive_ids)
									if emp_categ_rec.id == 15:
										calculation_days = working_days
										inc_worked_days = worked_days
									else:
										calculation_days = calulation_days
										inc_worked_days = salary_days
									if turn_over_amt >= inc_ids.start_value and turn_over_amt <= inc_ids.end_value:
										if inc_ids.type == 'per_lhk_fixed':
											print "*********inc_ids.incentive_value************",inc_ids.incentive_value
											print "*********working_days************",calculation_days
											print "*********worked_days************",worked_days
											print "*********inc_worked_daysinc_worked_daysinc_worked_days************",inc_worked_days
											incent_amt = ((turn_over_amt*inc_ids.incentive_value)/calculation_days)*inc_worked_days
										elif inc_ids.type == 'percentage':
											turn_over_per = (turn_over_amt*inc_ids.incentive_value)/100
											incent_amt = ((turn_over_per)/calculation_days)*inc_worked_days
										else:
											incent_amt = ((inc_ids.incentive_value)/calculation_days)*inc_worked_days
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
					else:
						raise osv.except_osv(_('Warning'),
							_('Turn Over is not fixed for last month for Incentive Calculation !!'))
						######### Incentive Calculation ###########
						######### Special Incentive Calculation ###########
				if con_ids_1.spl_inc:
					today = lastdate.date.today()
					first = lastdate.date(day=1, month=today.month, year=today.year)
					last = first - lastdate.timedelta(days=1)
					res = last.strftime('%B')
					datetttt = slip_rec.date_from
					print "+++++++date from++++++++++++",datetttt[5:7]
					a = datetttt[5:7]
					b = (calendar.month_abbr[int(a)])
					print "+++++++date Month++++++++++++",b
					d1 = str(res)
					print "Special incentive called -----------------------------------------------------",b
					turn_over_ids = self.pool.get('kg.turn.over').search(cr,uid,[('month','=',b),('active','=',True)])
					turn_over_amt = 0.00
					turn_over_per = 0.00
					incent_amt = 0.00
					if turn_over_ids:
						turn_over_rec = self.pool.get('kg.turn.over').browse(cr,uid,turn_over_ids[0])
						print "turn_over_recturn_over_recturn_over_recturn_over_rec",turn_over_rec.month
						turn_over_amt = turn_over_rec.amt * 100
						if con_ids_1.line_id_inc:
							turn_over_amt = turn_over_rec.amt 
							spec_amount  = 0 
							spec_amount_1 = 0
							spec_amount_2 = 0
							final_amt = 0
							get_spl_inc = self.pool.get('hr.salary.rule').search(cr,uid,[('code','=','SPI')])							
							for con_incs in con_ids_1.line_id_inc:
								cal_days = salary_days - leave_days
								if (absent+leave_days) >= con_incs.leave_consider:
									wor_days =  cal_days + con_incs.leave_consider
									print "wor_dayswor_dayswor_dayswor_days",wor_days
								else:
									wor_days = salary_days + absent
									print "wor_dayswor_dayswor_dayswor_days",wor_days
								#~ spec_amt = (spec_rec.salary_amt / calulation_days) * wor_days
								spec_amt = (con_incs.base_amt / calulation_days) * wor_days
								print "___Special Incentive as per attendance__________________",spec_amt
								if con_incs.type == 'percentage':
									print"Turn Over amount ----------------------------------------",turn_over_amt
									if con_incs.start_value <= turn_over_amt:
										print "Incentive percentage value-----------------------------------",con_incs.incentive_value
										#~ spec_amount = (spec_rec.salary_amt /100)*con_incs.incentive_value
										spec_amount = (con_incs.base_amt /100)*con_incs.incentive_value
										print "Actual Amount ---------------------",spec_amount
										laks = float(str(turn_over_amt-int(turn_over_amt))[1:])
										if con_incs.start_value < turn_over_amt and con_incs.end_value > turn_over_amt:
											#~ spec_amount_2 = ((((spec_rec.salary_amt/100)*con_incs.incentive_value) / 100) * laks) * 100 
											spec_amount_2 = ((((con_incs.base_amt/100)*con_incs.incentive_value) / 100) * laks) * 100 
											spec_amount = spec_amount_2
											print "________mid value_____________",spec_amount_2
									print"************spec_amount",spec_amount
									print"************spec_amount",spec_amount_2
									spec_amount_1 += spec_amount
									print "_______whole_____________",spec_amount_1
									if spec_amount_1 != 0.00:
										final_amt =  ((spec_amount_1+con_incs.base_amt)/calulation_days)* wor_days
									else:
										final_amt = (con_incs.base_amt/calulation_days)* wor_days
									if con_incs.criteria == 'non-hierarchy':
										final_amt=(((con_incs.base_amt /100)*con_incs.incentive_value)/calulation_days)* wor_days
									print "------------------------------spcial componenet ssssssssssssssssssss--------------------------------------------------",get_spl_inc
								if get_spl_inc:
									get_spl_inc_rc = self.pool.get('hr.salary.rule').browse(cr,uid,get_spl_inc[0])
									if get_spl_inc_rc.appears_on_payslip is True:
										if spec_amount_1 != 0.00:
											self.pool.get('hr.payslip.line').create(cr,uid,
												{
													'name':get_spl_inc_rc.name + ' ( ' + str(con_incs.start_value) + ' to ' + str(con_incs.end_value) + ' )' + ' Crs',
													'code':get_spl_inc_rc.code,
													'category_id':7,
													'quantity':1,
													#~ 'amount':((spec_amount_1+spec_rec.salary_amt)/calulation_days)* wor_days,
													'amount':final_amt,
													'salary_rule_id':1,
													'employee_id':emp_id,
													'contract_id':con_ids[0],
													'slip_id':slip_rec.id,
												},context = None)
											
										else:
											self.pool.get('hr.payslip.line').create(cr,uid,
												{
													'name':get_spl_inc_rc.name + ' ( ' + str(con_incs.start_value) + ' to ' + str(con_incs.end_value) + ' )' + ' Crs',
													'code':get_spl_inc_rc.code,
													'category_id':7,
													'quantity':1,
													#~ 'amount':(spec_rec.salary_amt/calulation_days)* wor_days,
													'amount':final_amt,
													'salary_rule_id':1,
													'employee_id':emp_id,
													'contract_id':con_ids[0],
													'slip_id':slip_rec.id,
												},context = None)
											
									else:
										if spec_amount_1 != 0.00:
											self.pool.get('ch.other.salary.comp').create(cr,uid,
													{
														'name':get_spl_inc_rc.name + ' ( ' + str(con_incs.start_value) + ' to ' + str(con_incs.end_value) + ' )' + ' Crs',
														'code':get_spl_inc_rc.code,
														'category_id':7,
														'quantity':1,
														#~ 'amount':((spec_amount_1+spec_rec.salary_amt)/calulation_days)* wor_days,
														'amount':final_amt,
														'salary_rule_id':1,
														'employee_id':emp_id,
														'contract_id':con_ids[0],
														'slip_id':slip_rec.id,
													},context = None)
											
										else:
											self.pool.get('ch.other.salary.comp').create(cr,uid,
													{
														'name':get_spl_inc_rc.name + '( ' + str(con_incs.start_value) + 'to' + str(con_incs.end_value) + ')' + ' Crs',
														'code':get_spl_inc_rc.code,
														'category_id':7,
														'quantity':1,
														#~ 'amount':(spec_rec.salary_amt/calulation_days)* wor_days,
														'amount':final_amt,
														'salary_rule_id':1,
														'employee_id':emp_id,
														'contract_id':con_ids[0],
														'slip_id':slip_rec.id,
													},context = None)
										
					else:
						raise osv.except_osv(_('Warning'),
							_('Turn Over is not fixed for last month for Special Incentive Calculation !!'))				
						######### Special Incentive Calculation ###########
						
				#### Creation of Fixed Incentive for the employee ####
				
				fix_inc_id = self.pool.get('ch.kg.contract.salary').search(cr,uid,[('header_id_salary','=',con_ids[0]),('salary_type','=',38)])
				fix_inc_pay_id = self.pool.get('hr.payslip.line').search(cr,uid,[('code','=','FI'),('slip_id','=',slip_rec.id)])
				fix_inc_pay_id_othr = self.pool.get('ch.other.salary.comp').search(cr,uid,[('code','=','FI'),('slip_id','=',slip_rec.id)])
				if fix_inc_id:
					fix_inc_rec = self.pool.get('ch.kg.contract.salary').browse(cr,uid,fix_inc_id[0])
					print "Fixed Incentive in Contract Master ",fix_inc_rec.salary_amt
					cal_days = salary_days - leave_days
					if (absent+leave_days) >= 2:
						wor_days =  cal_days + 2
						print "Leave Exceeded",wor_days
					else:
						wor_days = salary_days + absent
						print "Leaves within consideration",wor_days
					fix_inc_val = (fix_inc_rec.salary_amt/calulation_days)*wor_days
					print "Net Fixed Incentive value(Calculated)",fix_inc_val
					if fix_inc_pay_id:
						fix_inc_pay_rec = self.pool.get('hr.payslip.line').browse(cr,uid,fix_inc_pay_id[0])
						self.pool.get('hr.payslip.line').write(cr,uid,fix_inc_pay_rec.id,
											{
												'amount':fix_inc_val,
											})
					elif fix_inc_pay_id_othr:
						print "********************************"
						fix_inc_pay_rec_othr = self.pool.get('ch.other.salary.comp').browse(cr,uid,fix_inc_pay_id_othr[0])
						self.pool.get('ch.other.salary.comp').write(cr,uid,fix_inc_pay_rec_othr.id,
											{
												'amount':fix_inc_val,
											})
					else:
						pass
				else:
					pass
					
				#### Creation of Fixed Incentive for the employee ####
				
				#### Creation of Marketing Incentive for the employee ####
				
				mar_inc_id = self.pool.get('ch.kg.contract.salary').search(cr,uid,[('header_id_salary','=',con_ids[0]),('salary_type','=',40)])
				mar_inc_pay_id = self.pool.get('hr.payslip.line').search(cr,uid,[('code','=','MKG INCEN'),('slip_id','=',slip_rec.id)])
				mar_inc_pay_id_othr = self.pool.get('ch.other.salary.comp').search(cr,uid,[('code','=','MKG INCEN'),('slip_id','=',slip_rec.id)])
				if mar_inc_id:
					mar_inc_rec = self.pool.get('ch.kg.contract.salary').browse(cr,uid,mar_inc_id[0])
					print "Marketing Incentive in Contract Master ",mar_inc_rec.salary_amt
					cal_days = salary_days - leave_days
					if (absent+leave_days) >= 2:
						wor_days =  cal_days + 2
						print "Leave Exceeded",wor_days
					else:
						wor_days = salary_days + absent
						print "Leaves within consideration",wor_days
					mar_inc_val = (mar_inc_rec.salary_amt/calulation_days)*wor_days
					print "Net Marketing Incentive value(Calculated)",mar_inc_val
					if mar_inc_pay_id:
						mar_inc_pay_rec = self.pool.get('hr.payslip.line').browse(cr,uid,mar_inc_pay_id[0])
						self.pool.get('hr.payslip.line').write(cr,uid,mar_inc_pay_rec.id,
											{
												'amount':mar_inc_val,
											})
					elif mar_inc_pay_id_othr:
						print "********************************"
						mar_inc_pay_rec_othr = self.pool.get('ch.other.salary.comp').browse(cr,uid,mar_inc_pay_id_othr[0])
						self.pool.get('ch.other.salary.comp').write(cr,uid,mar_inc_pay_rec_othr.id,
											{
												'amount':mar_inc_val,
											})
					else:
						pass
				else:
					pass
				
				#### Creation of Marketing Incentive for the employee ####
				
				#### Creation of Incentive for the employee ####	
				
				#### Creation of attendance bonus ##########
				
				if con_ids_1.bonus_applicable:
					basic_amt = 0.00
					fda_amt = 0.00
					vda_amt = 0.00
					tot_mon_amt = 0.00
					emp_categ_ids = self.pool.get('kg.employee.category').search(cr,uid,[('id','=',con_ids_1.emp_categ_id.id),('state','=','approved')])
					if emp_categ_ids:
						emp_categ_rec = self.pool.get('kg.employee.category').browse(cr,uid,emp_categ_ids[0])
						if emp_categ_rec.bonus_categ == 'attendance':
							print "absentabsentabsentabsentabsent",absent
							print "leave_daysleave_daysleave_daysleave_days",leave_days
							pay_line_ids_bas = self.pool.get('ch.kg.contract.salary').search(cr,uid,[('header_id_salary','=',con_ids_1.id),('salary_type','=',1)])
							pay_line_ids_fda = self.pool.get('ch.kg.contract.salary').search(cr,uid,[('header_id_salary','=',con_ids_1.id),('salary_type','=',8)])
							pay_line_ids_vda = self.pool.get('hr.payslip.line').search(cr,uid,[('slip_id','=',slip_rec.id),('code','=','VDA')])
							if pay_line_ids_bas:
								pay_line_rec_ba = self.pool.get('ch.kg.contract.salary').browse(cr,uid,pay_line_ids_bas[0])
								basic_amt = pay_line_rec_ba.salary_amt
							if pay_line_ids_fda:
								pay_line_rec_fda = self.pool.get('ch.kg.contract.salary').browse(cr,uid,pay_line_ids_fda[0])
								fda_amt = pay_line_rec_fda.salary_amt
							#~ if pay_line_ids_vda:
								#~ pay_line_rec_vda = self.pool.get('hr.payslip.line').browse(cr,uid,pay_line_ids_vda[0])
							if vda_for_att_bon:
								vda_amt = vda_for_att_bon
								print "+++++++++++++++++++++++++++++++++++++",vda_amt
								print "+++++++++++++++++++++++++++++++++++++",basic_amt
								print "+++++++++++++++++++++++++++++++++++++",fda_amt
							tot_mon_amt = (basic_amt + fda_amt + vda_amt)/calulation_days
							if (absent+leave_days) <= 1.5:
								self.pool.get('hr.payslip.line').create(cr,uid,
									{
										'name':'Attendance Bonus',
										'code':'ATTB',
										'category_id':8,
										'quantity':1,
										'amount':(tot_mon_amt * emp_categ_rec.no_of_days_wage),
										'salary_rule_id':1,
										'employee_id':emp_id,
										'contract_id':con_ids[0],
										'slip_id':slip_rec.id,
									},context = None)
							else:
								pass
								
					if salary_days >= calulation_days:
						emp_categ_ids = self.pool.get('kg.employee.category').search(cr,uid,[('id','=',con_ids_1.emp_categ_id.id),('state','=','approved')])
						if emp_categ_ids:
							emp_categ_rec = self.pool.get('kg.employee.category').browse(cr,uid,emp_categ_ids[0])
							emplo = emp_obj.browse(cr,uid,emp_id)
							if emplo.gender == 'male':
								att_ins = emp_categ_rec.attnd_insentive_male
							else:
								att_ins = emp_categ_rec.attnd_insentive_female
							if att_ins != 0.00:
								self.pool.get('ch.other.salary.comp').create(cr,uid,
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
								#~ self.pool.get('hr.payslip.line').create(cr,uid,
										#~ {
											#~ 'name':'100% Attendance Bonus',
											#~ 'code':'ATTB',
											#~ 'category_id':8,
											#~ 'quantity':1,
											#~ 'amount':att_ins,
											#~ 'salary_rule_id':1,
											#~ 'employee_id':emp_id,
											#~ 'contract_id':con_ids[0],
											#~ 'slip_id':slip_rec.id,
										#~ },context = None)
							else:
								pass
					else:
						pass
				#### Creation of attendance bonus ##########
				
				#### Creation of the Driver Batta per month for the employee ####	
				
				if con_ids_1.driver_bata_app:
					print "Driver bataa called --------------------------------------------------",con_ids_1.driver_batta
					if con_ids_1.driver_batta > 0.00:
						driv_bata = con_ids_1.driver_batta  * (worked_days+ot_days)
						drv_id = rule_obj.browse(cr,uid,45)
						if drv_id.appears_on_payslip:
							self.pool.get('hr.payslip.line').create(cr,uid,
									{
										'name':drv_id.name,
										'code':drv_id.code,
										'category_id':2,
										'quantity':1,
										'amount':driv_bata,
										'salary_rule_id':drv_id.id,
										'employee_id':emp_id,
										'contract_id':con_ids[0],
										'slip_id':slip_rec.id,
									},context = None)
						else:
							self.pool.get('ch.other.salary.comp').create(cr,uid,
									{
										'name':drv_id.name,
										'code':drv_id.code,
										'category_id':2,
										'quantity':1,
										'amount':driv_bata,
										'salary_rule_id':drv_id.id,
										'employee_id':emp_id,
										'contract_id':con_ids[0],
										'slip_id':slip_rec.id,
									},context = None)
				#### Creation of the Driver Batta per month for the employee ####
				
				#### Creation of Coffee Allowance per month for the employee ####
				
				
				serc_coff_allow_con	= self.pool.get('hr.contract').search(cr,uid,[('employee_id','=',emp_id)])
				if serc_coff_allow_con:
					src_salry = self.pool.get('ch.kg.contract.salary').search(cr,uid,[('header_id_salary','=',serc_coff_allow_con[0]),('salary_type','=',22)])
					if src_salry:
						src_slary_rec = self.pool.get('ch.kg.contract.salary').browse(cr,uid,src_salry[0])
						if worked_days <= 13.00:
							coffe_allow = src_slary_rec.salary_amt / 2
						else:
							coffe_allow = src_slary_rec.salary_amt
				serc_coff_allow	= self.pool.get('hr.payslip.line').search(cr,uid,[('slip_id','=',slip_rec.id),('code','=','COFFEE ALL')])
				serc_coff_allow_othr	= self.pool.get('ch.other.salary.comp').search(cr,uid,[('slip_id','=',slip_rec.id),('code','=','COFFEE ALL')])
				if serc_coff_allow:
					serc_coff_rec = self.pool.get('hr.payslip.line').browse(cr,uid,serc_coff_allow[0])
					self.pool.get('hr.payslip.line').write(cr,uid,serc_coff_rec.id,
											{
												
												'amount':coffe_allow,
											})
				elif serc_coff_allow_othr:
					serc_coff_rec_othr = self.pool.get('ch.other.salary.comp').browse(cr,uid,serc_coff_allow_othr[0])
					self.pool.get('ch.other.salary.comp').write(cr,uid,serc_coff_rec_othr.id,
											{
												
												'amount':coffe_allow,
											})
				
				#### Creation of Coffee Allowance per month for the employee ####
				
				#### Creation of Worker Allowance per month for the employee ####	
				
				#### Creation of Painting Allowance #####
				paint_sal_id = self.pool.get('ch.kg.contract.salary').search(cr,uid,[('header_id_salary','=',con_ids[0]),('salary_type','=',51)])
				if paint_sal_id:
					paint_sal_rec = self.pool.get('ch.kg.contract.salary').browse(cr,uid,paint_sal_id[0])
					print "-----------Painting Allowance-----------------",paint_sal_rec.salary_amt
					sall_days = worked_days + ot_days + od_days + arrear_days + sundays + nat_fes_days + half_days + leave_days
					paint_allow = (paint_sal_rec.salary_amt/calulation_days)*(sall_days)
					serc_paint_allow	= self.pool.get('hr.payslip.line').search(cr,uid,[('slip_id','=',slip_rec.id),('code','=','PAINT ALL')])
					serc_paint_allow_othr	= self.pool.get('ch.other.salary.comp').search(cr,uid,[('slip_id','=',slip_rec.id),('code','=','PAINT ALL')])
					if serc_paint_allow:
						serc_paint_rec = self.pool.get('hr.payslip.line').browse(cr,uid,serc_paint_allow[0])
						self.pool.get('hr.payslip.line').write(cr,uid,serc_paint_rec.id,
												{
													'amount':paint_allow,
												})
					elif serc_paint_allow_othr:
						serc_paint_rec_othr = self.pool.get('ch.other.salary.comp').browse(cr,uid,serc_paint_allow_othr[0])
						self.pool.get('ch.other.salary.comp').write(cr,uid,serc_paint_rec_othr.id,
												{
													'amount':paint_allow,
												})
					else:
						pass
				#### Creation of Painting Allowance #####
				
				#### Creation of NI Hard Allowance #####
				ni_hard_sal_id = self.pool.get('ch.kg.contract.salary').search(cr,uid,[('header_id_salary','=',con_ids[0]),('salary_type','=',52)])
				if ni_hard_sal_id:
					ni_hard_sal_rec = self.pool.get('ch.kg.contract.salary').browse(cr,uid,ni_hard_sal_id[0])
					print "-----------NIHARD ALL Allowance-----------------",ni_hard_sal_rec.salary_amt
					sall_days = worked_days + ot_days + od_days + arrear_days + sundays + nat_fes_days + half_days+ leave_days
					ni_hard_allow = (ni_hard_sal_rec.salary_amt/calulation_days)*(sall_days)
					serc_ni_hard_allow	= self.pool.get('hr.payslip.line').search(cr,uid,[('slip_id','=',slip_rec.id),('code','=','NIHARD ALL')])
					serc_ni_hard_allow_othr	= self.pool.get('ch.other.salary.comp').search(cr,uid,[('slip_id','=',slip_rec.id),('code','=','NIHARD ALL')])
					if serc_ni_hard_allow:
						serc_ni_hard_rec = self.pool.get('hr.payslip.line').browse(cr,uid,serc_ni_hard_allow[0])
						self.pool.get('hr.payslip.line').write(cr,uid,serc_ni_hard_rec.id,
												{
													'amount':ni_hard_allow,
												})
					elif serc_ni_hard_allow_othr:
						serc_ni_hard_rec_othr = self.pool.get('ch.other.salary.comp').browse(cr,uid,serc_ni_hard_allow_othr[0])
						self.pool.get('ch.other.salary.comp').write(cr,uid,serc_ni_hard_rec_othr.id,
												{
													'amount':ni_hard_allow,
												})
					else:
						pass
				#### Creation of NI Hard Allowance #####	
				
				#### Creation of Night Allowance #####
				
				night_allo_sal_id = self.pool.get('ch.kg.contract.salary').search(cr,uid,[('header_id_salary','=',con_ids[0]),('salary_type','=',57)])
				if night_allo_sal_id:
					night_allow_rec = self.pool.get('ch.kg.contract.salary').browse(cr,uid,night_allo_sal_id[0])
					daily_att_ids = self.pool.get('ch.daily.attendance').search(cr,uid,[('employee_id','=',emp_id),('date','>=', slip_rec.date_from),('date','<=', slip_rec.date_to)])
					pre_days = 0
					if daily_att_ids:
						for daily_ids in daily_att_ids:
							daily_att_rec = self.pool.get('ch.daily.attendance').browse(cr,uid,daily_ids)
							if daily_att_rec.in_time1:
								in_time1 = float(str(daily_att_rec.in_time1) .replace(':', '.'))
							else:
								in_time1=12.00
							if daily_att_rec.in_time2:
								in_time2 = float(str(daily_att_rec.in_time2) .replace(':', '.'))
							else:
								in_time2 = 12.00
							if daily_att_rec.in_time3:
								in_time3 = float(str(daily_att_rec.in_time3) .replace(':', '.'))
							else:
								in_time3 = 12.00
							if daily_att_rec.in_time4:
								in_time4 = float(str(daily_att_rec.in_time4) .replace(':', '.'))
							else:
								in_time4 = 12.00
							if daily_att_rec.out_time1:
								out_time1 = float(str(daily_att_rec.out_time1) .replace(':', '.'))
							else:
								out_time1 = 12.00
							if daily_att_rec.out_time2:
								out_time2 = float(str(daily_att_rec.out_time2) .replace(':', '.'))
							else:
								out_time2 = 12.00
							if daily_att_rec.out_time3:
								out_time3 = float(str(daily_att_rec.out_time3) .replace(':', '.'))
							else:
								out_time3 = 12.00
							if daily_att_rec.out_time4:
								out_time4 = float(str(daily_att_rec.out_time4) .replace(':', '.'))
							else:
								out_time4 = 12.00
							if (daily_att_rec.status == 'present') and (in_time1 >= 19.00 or in_time1 <= 7.00 or in_time2 >= 19.00 or in_time2 <= 7.00 or in_time3 >= 19.00 or in_time3 <= 7.00 or in_time4 >= 19.00 or in_time4 <= 7.00 or out_time1 >= 19.00 or out_time1 <= 7.00 or out_time2 >= 19.00 or out_time2 <= 7.00 or out_time3 >= 19.00 or out_time3 <= 7.00 or out_time4 >= 19.00 or out_time4 <= 7.00):
								print "daily attendance date",daily_att_rec.date
								pre_days += 1
							else:
								print "not with the timing",daily_att_rec.date
						print "present days 8888888888888888888888888888888888",pre_days
						#~ sall_days = pre_days + ot_days + od_days + arrear_days + sundays + nat_fes_days + half_days+ leave_days
						sall_days = pre_days 
						night_allow = (night_allow_rec.salary_amt/calulation_days)*(sall_days)
						serc_night_allow	= self.pool.get('hr.payslip.line').search(cr,uid,[('slip_id','=',slip_rec.id),('code','=','NIGHT ALL')])
						serc_night_allow_othr	= self.pool.get('ch.other.salary.comp').search(cr,uid,[('slip_id','=',slip_rec.id),('code','=','NIGHT ALL')])
						if serc_night_allow:
							serc_night_rec = self.pool.get('hr.payslip.line').browse(cr,uid,serc_night_allow[0])
							self.pool.get('hr.payslip.line').write(cr,uid,serc_night_rec.id,
													{
														'amount':night_allow,
													})
						elif serc_night_allow_othr:
							serc_night_rec_othr = self.pool.get('ch.other.salary.comp').browse(cr,uid,serc_night_allow_othr[0])
							self.pool.get('ch.other.salary.comp').write(cr,uid,serc_night_rec_othr.id,
													{
														'amount':night_allow,
													})
						else:
							pass
					else:
						pass
				
				#### Creation of Night Allowance #####
				
				#### Creation of the total allowance and updating the total allowance field in parent ####
				
				serc_chil_ids = self.pool.get('hr.payslip.line').search(cr,uid,[('slip_id','=',slip_rec.id),('category_id','in',(2,8))])
				serc_incs_chil_ids = self.pool.get('hr.payslip.line').search(cr,uid,[('slip_id','=',slip_rec.id),('category_id','=',7)])
				if serc_incs_chil_ids:
					max_inc_id = max(serc_incs_chil_ids)
					print "------------------------------max id----------------------------------",max(serc_incs_chil_ids)
					payslip_line_rec_inc = self.pool.get('hr.payslip.line').browse(cr,uid,max_inc_id)
					print "------------------------------max incentive----------------------------------",payslip_line_rec_inc.amount
					sp_inc_amt = payslip_line_rec_inc.amount
				else:
					sp_inc_amt = 0.00
				print "serc_chil_idsserc_chil_idsserc_chil_idsserc_chil_idsserc_chil_ids",serc_chil_ids
				tot_allow_amt = 0.00
				for payslip_line_ids_all in serc_chil_ids:
					payslip_line_rec = self.pool.get('hr.payslip.line').browse(cr,uid,payslip_line_ids_all)
					tot_allow_amt += payslip_line_rec.amount
				self.write(cr, uid, slip_rec.id, {'tot_allowance': tot_allow_amt+sp_inc_amt})
				
				#### Creation of the total allowance and updating the total allowance field in parent ####
				
				#### Creation of the total deduction and updating the total allowance field in parent ####
				
				serc_chil_ids_1 = self.pool.get('hr.payslip.line').search(cr,uid,[('slip_id','=',slip_rec.id),('category_id','=',4)])
				print "serc_chil_idsserc_chil_idsserc_chil_idsserc_chil_idsserc_chil_ids",serc_chil_ids_1
				tot_ded_amt = 0.00
				for payslip_line_ids_ded in serc_chil_ids_1:
					payslip_line_rec = self.pool.get('hr.payslip.line').browse(cr,uid,payslip_line_ids_ded)
					tot_ded_amt += payslip_line_rec.amount
				self.write(cr, uid, slip_rec.id, {'tot_deduction': tot_ded_amt})
				
				#### Creation of the total deduction and updating the total allowance field in parent ####
				
				#### Creation of the net gross amount in the parent ####
				
				serc_chil_ids_2 = self.pool.get('hr.payslip.line').search(cr,uid,[('slip_id','=',slip_rec.id),('category_id','!=',4)])
				net_gross_amt = 0.00	
				for payslip_net_gross in serc_chil_ids_2:
					payslip_line_rec = self.pool.get('hr.payslip.line').browse(cr,uid,payslip_net_gross)
					net_gross_amt += payslip_line_rec.amount
				self.write(cr, uid, slip_rec.id, {'cross_amt': net_gross_amt,'round_val':net_gross_amt-tot_ded_amt})
				
				#### Creation of the net gross amount in the parent ####
				
				#### Creation of the other salary component amount in the parent ####
				
				serc_othr_sal_comp = self.pool.get('ch.other.salary.comp').search(cr,uid,[('slip_id','=',slip_rec.id),('category_id','!=',7)])
				if serc_othr_sal_comp:
					serc_incs_othr_sal_ids = self.pool.get('ch.other.salary.comp').search(cr,uid,[('slip_id','=',slip_rec.id),('category_id','=',7)])
					if serc_incs_othr_sal_ids:
						max_inc_othr_id = max(serc_incs_othr_sal_ids)
						print "------------------------------max id----------------------------------",max(serc_incs_othr_sal_ids)
						othr_sal_rec_inc = self.pool.get('ch.other.salary.comp').browse(cr,uid,max_inc_othr_id)
						print "------------------------------max incentive----------------------------------",othr_sal_rec_inc.amount
						sp_othr_inc_amt = othr_sal_rec_inc.amount
					else:
						sp_othr_inc_amt = 0.00
					net_othr_sal_amt = 0.00	
					for payslip_othr_sal in serc_othr_sal_comp:
						payslip_othr_line_rec = self.pool.get('ch.other.salary.comp').browse(cr,uid,payslip_othr_sal)
						net_othr_sal_amt += payslip_othr_line_rec.amount
					self.write(cr, uid, slip_rec.id, {'othr_sal_amt': net_othr_sal_amt+sp_othr_inc_amt})
				
				#### Creation of the other salary component amount in the parent ####
				
				
				
				
					
				
				
				
				
				
				
			else:
				raise osv.except_osv(
						_('Error !!'),
						_('Attendance entry not availabe for employee -  %s !!'%(slip_rec.employee_id.name)))
			
			
			
		
		
			
	def hr_verify_sheet(self, cr, uid, ids, context=None):
		#~ slip_obj = self.pool.get('hr.payslip')
		#~ contract_obj = self.pool.get('hr.contract')
		#~ slip_rec = self.browse(cr, uid, ids[0])
		#~ emp_rec = slip_rec.employee_id
		#~ cont_ids = contract_obj.search(cr,uid,[('employee_id','=',slip_rec.employee_id.id)])
		#~ if cont_ids:
			#~ ex_ids = slip_obj.search(cr, uid, [('employee_id','=', slip_rec.employee_id.id),
						#~ ('date_from','=',slip_rec.date_from),('date_to','=',slip_rec.date_to),
						#~ ('state','=', 'done')])
			#~ for i in ex_ids:
				#~ sql = """ delete from hr_payslip where id=%s """%(i)
				#~ cr.execute(sql)
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
			adv_rec = self.pool.get('kg.advance.deduction').browse(cr,uid,slip_line_rec.cum_ded_id.id)
			print "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$",adv_rec.id
			self.pool.get('kg.advance.deduction').write(cr,uid,adv_rec.id,{'bal_amt':adv_rec.bal_amt+slip_line_rec.amount,'amt_paid':adv_rec.amt_paid-slip_line_rec.amount})
		####### Reverting the advance amount of the employee for this month while cancelling ################
		sql = """ delete from hr_payslip_line where slip_id=%s """%(slip_rec.id)
		cr.execute(sql)
		sql_1 = """ delete from ch_other_salary_comp where slip_id=%s """%(slip_rec.id)
		cr.execute(sql_1)
		sql_parent = """ update hr_payslip set tot_deduction=null ,con_cross_amt=null,cross_amt =null,tot_paid_days =null,tot_allowance=null,
		round_val=null,othr_sal_amt=null where id =%s """%(slip_rec.id)
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
	
	def _tot_sal_amt(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		tot_val = 0
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'tot_val': 0.0,
			}
			if order.slip_ids:
				for item in order.slip_ids:
					tot_val += item.round_val
			else:
				tot_val = 0
			res[order.id]['tot_val'] = tot_val or 0.00
		return res	
	
	_columns = {
	
	'name': fields.char('Month', size=64, readonly=True),
	'date_start': fields.date('Date From', required=True, readonly=False),
	'date_end': fields.date('Date To', required=True, readonly=False),
	'slip_date': fields.date('Creation Date'),
	'slip_ids': fields.one2many('hr.payslip', 'payslip_run_id', 'Payslips', required=False, readonly=True),
	'state': fields.selection([('draft', 'Draft'),('confirmed','WFA'),('approved','AC ACK Pending'),('done','Done'),('ac_accept','AC Accepted'),('reject','AC Rejected'),('cancel','Cancelled')], 'Status', select=True, readonly=True),
	'tot_val':fields.function(_tot_sal_amt, string='Total Value',multi="sums",store=True),
	'remark': fields.text('Approve/Reject'),
	'cancel_remark': fields.text('Cancel'),
	
	}
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			if rec.cancel_remark:
				self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Cancel remark is must !!'),
					_('Enter the remarks in Cancel remarks field !!'))
		else:
			raise osv.except_osv(_('Warning!!!'),
				_('Confirm the record to proceed further'))
		return True	
	
	def entry_accept(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			self.write(cr, uid, ids, {'state': 'ac_accept','done_user_id': uid, 'done_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
	
	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state ==  'done':
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Warning!!!'),
					_('The Record is not in draft !!!!!!'))
		return True
		
	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Warning!!!'),
					_('Confirm the record to proceed further'))
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			if rec.remark:
				self.write(cr, uid, ids, {'state': 'confirmed','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Rejection remark is must !!'),
					_('Enter the remarks in rejection remark field !!'))
		else:
			raise osv.except_osv(_('Warning!!!'),
					_('Approve the record to proceed further'))
		return True
	
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
			raise osv.except_osv(_('Warning !!'),
					_('Payslip for this month already exists !!'))
			#~ return False
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
		
	_constraints = [
		
		(_check_employee_slip_dup, 'Payslip has been created already for this month. Check Month and State !!',['amount']),
		
		] 
		
	
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

class ch_salary_slip(osv.osv):
	_name = 'hr.payslip.line'	
	_inherit = 'hr.payslip.line'
	
	_columns = {
	
	'cum_ded_id': fields.many2one('kg.advance.deduction','Cumulative Deduction', readonly=True),
		
	}
ch_salary_slip()

###### newly added class for capturing the hidden salary component #####

class ch_other_salary_comp(osv.osv):
	_name = 'ch.other.salary.comp'	
	
	
	def _calculate_total(self, cr, uid, ids, name, args, context):
		if not ids: return {}
		res = {}
		for line in self.browse(cr, uid, ids, context=context):
			res[line.id] = float(line.quantity) * line.amount * line.rate / 100
		return res
	
	_columns = {
	
	'name': fields.char('Description', size=256, required=True),
	'code': fields.char('Code', size=52, required=True, help="The code that can be used in the salary rules"),
	'slip_id':fields.many2one('hr.payslip', 'Pay Slip', required=True, ondelete='cascade'),
	'salary_rule_id':fields.many2one('hr.salary.rule', 'Rule', required=True),
	'employee_id':fields.many2one('hr.employee', 'Employee', required=True),
	'contract_id':fields.many2one('hr.contract', 'Contract', required=True, select=True),
	'rate': fields.float('Rate (%)', digits_compute=dp.get_precision('Payroll Rate')),
	'amount': fields.float('Amount', digits_compute=dp.get_precision('Payroll')),
	'quantity': fields.float('Quantity',digits_compute=dp.get_precision('Payroll')),
	'total': fields.function(_calculate_total, method=True, type='float', string='Total', digits_compute=dp.get_precision('Payroll'),store=True ),
	'cum_ded_id': fields.many2one('kg.advance.deduction','Cumulative Deduction', readonly=True),
	'category_id':fields.many2one('hr.salary.rule.category', 'Category', required=False),
		
	}
	
	_defaults = {
		'quantity': 1.0,
		'rate': 100.0,
	}
ch_other_salary_comp()

###### newly added class for capturing the hidden salary component #####

