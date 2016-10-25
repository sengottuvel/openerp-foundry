##############################################################################
#
#   Standard Transaction Module
#
##############################################################################

{
    'name': 'Subcontract Invoice',
    'version': '0.1',
    'author': 'Karthikeyan.S',    
    'depends' : ['base','kg_subcontract_process'],
    'data': [
    
			'kg_subcontract_invoice_view.xml',
			'sequence_data.xml',
			'onscreen_report_data.xml',
			
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

