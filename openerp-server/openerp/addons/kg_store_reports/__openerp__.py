##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).

##############################################################################
{
    'name': 'Store_Reports',
    'version': '0.1',
    'author': 'sengottuvel',
    'category': 'KG_GRN',
    'website': 'http://www.openerp.com',
    'description': """
This module allows you to manage your Purchase Requisition.
===========================================================

When a purchase order is created, you now have the opportunity to save the
related requisition. This new object will regroup and will allow you to easily
keep track and order all your purchase orders.
""",
    'depends' : ['base','purchase','stock','kg_depindent'],
    'data': [
		
		#~ 'wizard/grn_register_report_wizard.xml',
		#~ 'wizard/store_issue_slip_wizard.xml',
		#~ 'wizard/pobill_from_store_wizard.xml',
		#~ 'wizard/dep_issue_register_wizard.xml',
		#~ 'wizard/dep_indent_to_issue_wizard.xml',
		#~ 'wizard/grn_to_issue_wizard.xml',
		#~ 'wizard/pobill_from_purchase_wizard.xml',
		#~ 'wizard/issue_summary_from_mainst.xml',
		#~ 'wizard/opening_stock_wizard.xml',
		#~ 'wizard/new_opening_stock_wizard.xml',
		#~ 'wizard/consumption_summary_wizard.xml',
		#~ 'wizard/consumption_details_wizard.xml',
		#~ 'wizard/closing_stock_wizard.xml',
		#~ 'wizard/major_closing_stock_wizard.xml',
		#~ 'wizard/open_stock_wizard.xml',
		#~ 'wizard/main_closing_stock_wizard.xml',
		#~ 'wizard/kg_depindent_detail_wizard.xml',
		#~ 'wizard/kg_pi_detail_wizard.xml',
		#~ 'wizard/gate_pass_register_wizard.xml',
		#~ 'wizard/kg_product_reg_wizard.xml',
		#~ 'wizard/kg_serindent_detail_wizard.xml',
		#~ 'wizard/kg_supplier_register.xml',
		#~ 'wizard/kg_product_warranty_wiz.xml',
		#~ 'wizard/profit_loss_wiz.xml',
		#~ 'wizard/sales_register_wiz.xml',
		#'wizard/kg_sales_reg_wiz.xml',
	],
	
	'css': [
        'static/src/css/state.css', 
        
    ],
    'auto_install': False,
    'installable': True,
}

