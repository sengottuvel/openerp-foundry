##############################################################################
#
#  Bank Statement (Accounts)
#
##############################################################################

{
    'name': 'Bank Reconcile',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'Accounts',        
    'depends' : ['base','account','hr'],
    'data': [
			'kg_bank_reconcile_view.xml',
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
