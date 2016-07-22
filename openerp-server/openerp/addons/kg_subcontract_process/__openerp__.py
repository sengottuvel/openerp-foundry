##############################################################################
#
#   This is New Customized Module
#
##############################################################################

{
    'name': 'Subcontract Process',
    'version': '0.1',
    'author': 'Sangeetha',    
    'depends' : ['base', 'kg_machineshop','kg_ms_planning', 'kg_ms_operations'],
    'data': [
		'kg_subcontract_process_view.xml'
		],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

