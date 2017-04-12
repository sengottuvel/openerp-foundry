##############################################################################
#
#   This is YOS Bonus Module
#
##############################################################################

{
    'name': 'YOS Bonus',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'BASE',        
    'depends' : ['base','hr','kg_employee_category'],
    'data': [
			'kg_el_encasement_view.xml',
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
