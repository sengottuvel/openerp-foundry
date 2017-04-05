##############################################################################
#
#   This is Labour Weekly Wages Module
#
##############################################################################

{
    'name': 'Labours Weekly Wages',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'BASE',        
    'depends' : ['base','hr','hr_payroll'],
    'data': [
			'kg_weekly_wages_view.xml',
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
