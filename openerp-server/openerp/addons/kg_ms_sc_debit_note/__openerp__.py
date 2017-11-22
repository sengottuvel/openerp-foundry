
{
    'name': 'MS Subcontractor Debit Note',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'BASE',        
    'depends' : ['base','kg_work_order','kg_subcontract_process','kg_subcontract_invoice'],
    'data': [
			'kg_ms_sc_debit_note_view.xml',
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
