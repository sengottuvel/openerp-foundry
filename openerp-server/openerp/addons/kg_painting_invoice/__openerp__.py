##############################################################################
#
#   Standard Transaction Module
#
##############################################################################

{
    'name': 'Painting Invoice',
    'version': '0.1',
    'author': 'Sangeetha.S',    
    'depends' : ['base','kg_pump_qap'],
    'data': [
    
			'kg_painting_invoice_view.xml',
			'sequence_data.xml',
			'onscreen_report_data.xml',
			
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

