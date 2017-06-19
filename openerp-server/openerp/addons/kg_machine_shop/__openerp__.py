##############################################################################
#
#   This is New Customized Pump Model Master
#
##############################################################################

{
    'name': 'Machine Shop Master',
    'version': '0.1',
    'author': 'karthikeyan',
    'category': 'BASE',        
    'depends' : ['base','product','kg_pumpmodel_master','kg_moc_master','kg_moc_construction'],
    'data': ['kg_machine_shop_view.xml'],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

