##############################################################################
#
#   This is New Master Module
#
##############################################################################

{
    'name': 'KG Compensation',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'BASE',        
    'depends' : ['base','hr','kg_employee_category'],
    'data': [
			'kg_compensation_view.xml',
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
