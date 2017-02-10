##############################################################################
#
#   This is New Master Module
#
##############################################################################

{
    'name': 'Turn Over',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'BASE',        
    'depends' : ['base','hr','hr_payroll'],
    'data': [
			'kg_turn_over_view.xml',
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
