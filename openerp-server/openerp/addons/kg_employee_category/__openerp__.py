##############################################################################
#
#   This is New Master Module
#
##############################################################################

{
    'name': 'Employee Category Master',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'BASE',        
    'depends' : ['base','kg_allowance_deduction'],
    'data': [
			'kg_employee_category_view.xml',
			#~ 'default_data.xml'
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
