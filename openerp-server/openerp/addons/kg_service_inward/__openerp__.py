##############################################################################
#
#   Standard Transaction Module
#
##############################################################################

{
    'name': 'Service Inward',
    'version': '0.1',
    'author': 'Thangaraj',    
    'depends' : ['base','kg_work_order'],
    'data': [
    
			'kg_service_inward_view.xml',
			'sequence_data.xml',
			#~ 'onscreen_report_data.xml',
			
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

