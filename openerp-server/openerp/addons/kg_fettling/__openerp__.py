##############################################################################
#
#   This is New Customized Module
#
##############################################################################

{
    'name': 'Fettling Process',
    'version': '0.1',
    'author': 'Sangeetha',    
    'depends' : ['base','kg_stock_inward','kg_production','kg_pouring_log'],
    'data': [
		'kg_fettling_view.xml'
		],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

