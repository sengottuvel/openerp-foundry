##############################################################################
#
#   Standard Transaction Module
#
##############################################################################

{
    'name': 'Pump vs Material',
    'version': '0.1',
    'author': 'Thangaraj',    
    'depends' : ['base','kg_moc_construction','kg_pumpmodel_master','kg_position_number','kg_pattern_master','kg_moc_master'],
    'data': [
    
			'kg_pump_vs_material_view.xml',
			'sequence_data.xml',
			#~ 'onscreen_report_data.xml',
			
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

