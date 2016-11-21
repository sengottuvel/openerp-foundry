{

    'name': 'Credit Note',
    'version': '0.1',
    'author': 'Thangaraj',
    'category': 'Credit Note Details',
   
    'website': 'http://www.openerp.com',
    'description': """
This module allows you to track the credit note entry.
===========================================================
""",
    'depends' : ['base', 'product'],
    'data': [	
				'kg_credit_note_view.xml',
				
			],
			
    'auto_install': False,
    'installable': True,
    
}
