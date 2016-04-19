##############################################################################
#
#   This is New Customized Module
#
##############################################################################

{
    'name': 'Machine Shop',
    'version': '0.1',
    'author': 'Sangeetha',    
    'depends' : ['base','kg_stock_inward','kg_production'],
    'data': [
		'kg_machineshop_view.xml'
		],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

