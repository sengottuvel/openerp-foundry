##############################################################################
#
# KG HRM System Payslip Module   

##############################################################################
{
    'name': 'KG Employee Payslip',
    'version': '0.1',
    'author': 'sengottuvelu',
    'category': 'HRM',
    'images': ['images/purchase_requisitions.jpeg'],
    'website': 'http://www.openerp.com',
    'description': """
    
This module allows you to manage your Purchase Requisition.
===========================================================

When a purchase order is created, you now have the opportunity to save the
related requisition. This new object will regroup and will allow you to easily
keep track and order all your purchase orders.
""",

    'depends' : ['base', 'hr_payroll','hr','hr_contract',
			     'kg_allowance_deduction','kg_division_master','kg_monthly_attendance','kg_contribution',
			     'kg_turn_over','kg_advance_deduction'
					],
    'data': [
			'kg_payslip.xml',
			'jasper_report.xml',
			#~ 'wizard/kg_employee_salary_muster.xml',
			#~ 'wizard/kg_bank_stm.xml',
			#~ 'wizard/kg_pf_paymuster.xml',
			#~ 'wizard/kg_nonpf_paymuster.xml',
			#~ 'wizard/kg_ot_days.xml',
			#'wizard/kg_esi_wizard.xml',
			#~ 'wizard/kg_bank_list.xml',
			#~ 'wizard/kg_netpayment.xml',
			#~ 'wizard/kg_pay_abstract.xml',
			
			#~ 'wizard/kg_baask_sal_muster.xml',
			#~ 'wizard/kg_leave_balance.xml',
			#'wizard/kg_allowance.xml',
			#~ 'wizard/kg_emp_bouns_pdf.xml',
			
			#~ 'report/kg_banklist_text_report.xml',
			#~ 'report/kg_emp_bouns.xml',
			#~ 'report/customer_report.xml',
			#~ 'wizard/kg_clin_pay_wizard.xml',
			#~ 'wizard/kg_emp_payslip_wiz.xml'
			],
    'css': ['static/src/css/state.css'],
    'auto_install': False,
    'installable': True,
}

