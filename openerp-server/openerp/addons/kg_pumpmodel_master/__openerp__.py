##############################################################################
#
#   This is New Customized Pump Model Master
#
##############################################################################

{
    'name': 'Pump Model Master',
    'version': '0.1',
    'author': 'karthikeyan',
    'category': 'BASE',        
    'depends' : ['base','kg_pump_category','kg_pumpseries_master','kg_hsn_master'],
    'data': ['kg_pumpmodel_master_view.xml'],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

