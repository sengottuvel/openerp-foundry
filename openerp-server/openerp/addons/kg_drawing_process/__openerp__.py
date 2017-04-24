##############################################################################
#
#   This is New Customized Module
#
##############################################################################

{
    'name': 'Drawing Process',
    'version': '0.1',
    'author': 'Karthikeyan',    
    'depends' : ['base','kg_division_master','kg_position_number','kg_equipment_master'],
    'data': [
		'kg_drawing_process_view.xml',		
		'sequence_data.xml',
		'onscreen_report_data.xml',	
		],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

