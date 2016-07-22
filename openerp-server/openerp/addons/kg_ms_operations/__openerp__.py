##############################################################################
#
#   This is New Customized Module
#
##############################################################################

{
    'name': 'KG MS Operations',
    'version': '0.1',
    'author': 'Sangeetha',    
    'depends' : ['base', 'kg_machineshop','kg_ms_planning'],
    'data': [
		'kg_ms_operations_view.xml'
		],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

