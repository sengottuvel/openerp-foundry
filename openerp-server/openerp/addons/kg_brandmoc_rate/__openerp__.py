##############################################################################
#
#   This is New Customized Pump Model Master
#
##############################################################################

{
    'name': 'Brand MOC Rate Master',
    'version': '0.1',
    'author': 'karthikeyan',
    'category': 'BASE',        
    'depends' : ['base','product','kg_moc_master','kg_brandmaster'],
    'data': ['kg_brandmoc_rate_view.xml'],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

