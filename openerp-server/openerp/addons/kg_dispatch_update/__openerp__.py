##############################################################################
#
#   Standard Transaction Module
#
##############################################################################

{
    'name': 'Dispatch Update',
    'version': '0.1',
    'author': 'Karthikeyan.S',    
    'depends' : ['base','kg_division_master','kg_po_masters','kg_transport','kg_sale_invoice','kg_assembly'],
    'data': [
    
			'kg_dispatch_update_view.xml',
			'sequence_data.xml',
			'onscreen_report_data.xml',
			
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

