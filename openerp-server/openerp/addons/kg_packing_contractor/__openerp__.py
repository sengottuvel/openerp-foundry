##############################################################################
#
#   This is New Customized Module
#
##############################################################################

{
    'name': 'Packing Contractor Process',
    'version': '0.1',
    'author': 'Karthikeyan.S',    
    'depends' : ['base','kg_packing_type','kg_division_master'],
    'data': [
		'kg_packing_contractor_view.xml',		
		'sequence_data.xml',
		'onscreen_report_data.xml',	
		],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

