##############################################################################
#
#   This is Employee Labour Master Module
#
##############################################################################

{
    'name': 'Employee Labour Master',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'BASE',        
    'depends' : ['base','hr','hr_payroll'],
    'data': [
			'kg_labour_master_view.xml',
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
