##############################################################################
#
#   Standard Transaction Module
#
##############################################################################

{
    'name': 'Part QAP',
    'version': '0.1',
    'author': 'Sangeetha',    
    'depends' : ['base','kg_ms_stores'],
    'data': [
    
			'kg_part_qap_view.xml',
			
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

