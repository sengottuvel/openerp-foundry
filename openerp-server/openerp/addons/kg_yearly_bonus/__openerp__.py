##############################################################################
#
#   This is New Master Module
#
##############################################################################

{
    'name': 'Yearly Bonus',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'BASE',        
    'depends' : ['base','hr','account','kg_employee_category'],
    'data': [
			'kg_yearly_bonus_view.xml',
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
