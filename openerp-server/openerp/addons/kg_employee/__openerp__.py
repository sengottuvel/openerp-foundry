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
    'depends' : ['base','hr','kg_employee_category'],
    'data': [
			'kg_employee_view.xml',
			'default_data.xml'
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
