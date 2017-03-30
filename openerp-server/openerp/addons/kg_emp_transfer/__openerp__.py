##############################################################################
#
#   This is Employee Transfer Module
#
##############################################################################

{
    'name': 'Employee Transfer',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'BASE',        
    'depends' : ['base','hr','hr_payroll','kg_employee_category'],
    'data': [
			'kg_emp_transfer_view.xml',
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
