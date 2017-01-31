##############################################################################
#
#   This is New Master Module
#
##############################################################################

{
    'name': 'Standard Master',
    'version': '0.1',
    'author': 'Sengottuvelu',
    'category': 'BASE',        
    'depends' : ['base','hr_payroll'],
    'data': [
			'kg_allowance_deduction_master_view.xml',
			#~ 'default_data.xml'
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
