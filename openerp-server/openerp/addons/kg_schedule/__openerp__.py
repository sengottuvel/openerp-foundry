##############################################################################
#
#   This is New Customized Module
#
##############################################################################

{
    'name': 'KG Schedule',
    'version': '0.1',
    'author': 'Sangeetha',    
    'depends' : ['base', 'kg_stock_inward','product','kg_pumpmodel_master', 'kg_pattern_master', 'kg_moc_master', 'kg_division_master', 'kg_work_order'],
    'data': [
		'kg_schedule_view.xml'
		],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

