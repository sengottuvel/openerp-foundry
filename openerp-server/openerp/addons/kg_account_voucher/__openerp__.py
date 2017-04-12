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
    'depends' : ['base','kg_sale_invoice','kg_customer_advance','kg_division_master','kg_subcontract_invoice','kg_foundry_invoice'],
    'data': ['kg_account_voucher_view.xml',
				'jasper_report.xml'],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

