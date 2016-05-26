##############################################################################
#
#   This is New Customized Module
#
##############################################################################

{
    'name': 'KG WO Amendment',
    'version': '0.1',
    'author': 'Sangeetha',    
    'depends' : ['base', 'kg_stock_inward','kg_work_order'],
    'data': [
		'kg_wo_amendment_view.xml'],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

