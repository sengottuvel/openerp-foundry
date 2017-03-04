##############################################################################
#
#   Standard Transaction Module
#
##############################################################################

{
    'name': 'Pump QAP',
    'version': '0.1',
    'author': 'Sangeetha',    
    'depends' : ['base','kg_ms_stores','kg_assembly'],
    'data': [
    
			'kg_pump_qap_view.xml',
			
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

