##############################################################################
#
#   This is New Customized Module
#
##############################################################################

{
    'name': 'Machine Shop',
    'version': '0.1',
    'author': 'Sangeetha',    
    'depends' : ['base','kg_stock_inward','kg_production','kg_division_master','kg_schedule','kg_work_order','kg_fettling','kg_stage_master','kg_rejection_master'],
    'data': [
		'kg_machineshop_view.xml','jasper_report.xml'
		],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

