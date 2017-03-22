##############################################################################
#
#   This is New Customized Pump Model Master
#
##############################################################################

{
    'name': 'Account Voucher',
    'version': '0.1',
    'author': 'karthikeyan',
    'category': 'BASE',        
    'depends' : ['base','kg_sale_invoice','kg_customer_advance'],
    'data': ['kg_account_voucher_view.xml'],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

