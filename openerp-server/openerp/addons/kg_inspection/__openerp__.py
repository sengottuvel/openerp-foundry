##############################################################################
#
#   Standard Transaction Module
#
##############################################################################

{
    'name': 'Inspection',
    'version': '0.1',
    'author': 'Sangeetha',    
    'depends' : ['base','kg_ms_stores','kg_assembly','kg_pump_qap'],
    'data': [
    
			'kg_inspection_view.xml',
			
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

