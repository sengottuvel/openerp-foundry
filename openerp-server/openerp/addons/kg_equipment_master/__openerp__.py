##############################################################################
#
#   This is New Customized Pump Model Master
#
##############################################################################

{
    'name': 'Equipment Master',
    'version': '0.1',
    'author': 'Karthikeyan',
    'category': 'BASE',        
    'depends' : ['base','kg_position_number'],
    'data': [
			'kg_equipment_master_view.xml',
			'default_data.xml'
			],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

