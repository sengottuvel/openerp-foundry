##############################################################################
#
#   This is New Customized Module
#
##############################################################################

{
    'name': 'KG MS Stores',
    'version': '0.1',
    'author': 'Sangeetha',    
    'depends' : ['base', 'kg_ms_operations'],
    'data': [
		'kg_ms_stores_view.xml',
		'wizard/kg_ms_partlist_wiz_view.xml',
		],
	'test': [
        'test/kg_ms_partlist_wiz.yml',
        
    ],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

