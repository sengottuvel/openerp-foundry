##############################################################################
#
#   Standard Transaction Module
#
##############################################################################

{
    'name': 'Primecost View',
    'version': '0.1',
    'author': 'Thangaraj',    
    'depends' : ['base','kg_moc_construction','kg_pumpmodel_master','kg_position_number','kg_pattern_master','kg_moc_master','kg_machine_shop','kg_po_masters','kg_bom'],
    'data': [
    
			'kg_primecost_view.xml',
			'sequence_data.xml',
			#~ 'onscreen_report_data.xml',
			
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

