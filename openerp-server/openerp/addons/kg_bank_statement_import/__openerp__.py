##############################################################################
#
#  Bank Statement (Accounts)
#
##############################################################################

{
    'name': 'Bank Statement Import',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'Accounts',        
    'depends' : ['base','account','hr'],
    'data': [
			'kg_bank_statement_import_view.xml',
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
