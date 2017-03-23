##############################################################################
#
#   Standard Transaction Module
#
##############################################################################

{
    'name': 'Moulding Invoice',
    'version': '0.1',
    'author': 'Sangeetha.S',    
    'depends' : ['base','kg_work_order','kg_production'],
    'data': [
			'kg_moulding_invoice_view.xml',
			'sequence_data.xml',
			'onscreen_report_data.xml',
			
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

