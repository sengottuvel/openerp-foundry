{
    'name': 'Debit Note',
    'version': '0.1',
    'author': 'Thangaraj',
    'category': 'Item Details',
   
    'website': 'http://www.openerp.com',
    'description': """
This module allows you to track the stock movement activity.
===========================================================
""",
    'depends' : ['base', 'product','account','kg_purchase_invoice'],
    'data': [
			 'kg_debit_note_view.xml',
			 'jasper_report.xml',
		
			],
	
    'auto_install': False,
    'installable': True,
}
