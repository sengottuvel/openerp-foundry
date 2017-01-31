##############################################################################
#
#   This is New Master Module
#
##############################################################################

{
    'name': 'Kg Leave Type',
    'version': '0.1',
    'author': 'Sengottuvelu',
    'category': 'BASE',        
    'depends' : ['base','hr_holidays'],
    'data': [
			'kg_leave_type_view.xml',
			'default_data.xml'
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
