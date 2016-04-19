##############################################################################
#
#   This is New Customized Module
#
##############################################################################

{
    'name': 'Pouring Log',
    'version': '0.1',
    'author': 'Sangeetha',    
    'depends' : ['base',
    'kg_stock_inward','kg_work_order','kg_production'
    ],
    'data': ['kg_pouring_log_view.xml'],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

