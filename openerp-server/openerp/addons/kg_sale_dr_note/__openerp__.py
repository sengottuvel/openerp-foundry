##############################################################################
#
#   This is  Sales DR/CR Note Module
#
##############################################################################

{
    'name': 'Sales DR Note',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'BASE',        
    'depends' : ['base','kg_sale_invoice'],
    'data': [
			'kg_sale_dr_note_view.xml',
			'kg_sale_cr_note_view.xml',
			'jasper_report.xml',
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
