##############################################################################
#
#   This is New Customized Module
#
##############################################################################

{
    'name': 'Packing Slip',
    'version': '0.1',
    'author': 'Sangeetha',    
    'depends' : ['base','kg_assembly','kg_part_qap'],
    'data': [
		'kg_packing_slip_view.xml',
		'onscreen_report.xml'
		],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

