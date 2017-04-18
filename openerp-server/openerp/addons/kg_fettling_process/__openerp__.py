##############################################################################
#
#   This is New Customized Module
#
##############################################################################

{
    'name': 'Fettling Process',
    'version': '0.1',
    'author': 'Karthikeyan',    
    'depends' : ['base','kg_fettling','kg_pattern_master','kg_moc_master','kg_division_master','kg_pumpmodel_master','kg_stage_master'],
    'data': [
		'kg_fettling_process_view.xml',		
		'sequence_data.xml',
		'onscreen_report_data.xml',	
		],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

