##############################################################################
#
#  Employee Cash Issue Module (Accounts)
#
##############################################################################

{
    'name': 'Employee Cash Issue',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'Accounts',        
    'depends' : ['base','account','kg_depmaster','kg_employee_category','hr'],
    'data': [
			'kg_emp_cash_issue_view.xml',
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
