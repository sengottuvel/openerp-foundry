##############################################################################
#
#   This is New Customized Pump Model Master
#
##############################################################################

{
    'name': 'Machinery Master',
    'version': '0.1',
    'author': 'karthikeyan',
    'category': 'BASE',        
    'depends' : ['base','kg_operation_master','kg_stage_master','kg_moc_master'],
    'data': ['kg_machinery_master_view.xml'],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

