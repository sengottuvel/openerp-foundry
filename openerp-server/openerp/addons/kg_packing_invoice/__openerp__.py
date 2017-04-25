##############################################################################
#
#   Standard Transaction Module
#
##############################################################################

{
    'name': 'Packing Invoice',
    'version': '0.1',
    'author': 'Karthikeyan.S',    
    'depends' : ['base','kg_pump_qap'],
    'data': [
    
			'kg_packing_invoice_view.xml',
			'sequence_data.xml',
			'onscreen_report_data.xml',
			
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

