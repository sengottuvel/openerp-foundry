##############################################################################
#
#   This is Employee Labour Master Module
#
##############################################################################

{
    'name': 'Labours Weekly Attendance',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'BASE',        
    'depends' : ['base','hr','hr_payroll'],
    'data': [
			'kg_weekly_attendance_view.xml',
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
