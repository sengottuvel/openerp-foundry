##############################################################################
#
#  Employee Cash Issue Module (Accounts)
#
##############################################################################

{
    'name': 'Cash Voucher',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'Accounts',        
    'depends' : ['base','account','hr','kg_depmaster'],
    'data': [
			'kg_cash_voucher_view.xml',
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
