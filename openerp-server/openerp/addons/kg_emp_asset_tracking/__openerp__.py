##############################################################################
#
#   This is Employee Asset Tracking Module
#
##############################################################################

{
    'name': 'Employee Asset Tracking',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'BASE',        
    'depends' : ['base','hr','hr_payroll','kg_employee_category'],
    'data': [
			'kg_emp_asset_tracking_view.xml',
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
