##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).

##############################################################################
{
    'name': 'KG PO Reports',
    'version': '0.1',
    'author': 'sengottuvel',
    'category': 'KG_Purchase_Order',
    'website': 'http://www.openerp.com',
    'description': """
This module allows you to manage your Purchase Requisition.
===========================================================

When a purchase order is created, you now have the opportunity to save the
related requisition. This new object will regroup and will allow you to easily
keep track and order all your purchase orders.
""",
    'depends' : ['base', 'product', 'purchase','purchase_requisition','kg_purchase_indent','kg_purchase_invoice'],
    'external_dependencies': {'python': ['xlwt']},
    'data': [
			#~ 'wizard/kg_purchase_order_wizard.xml',
			#~ 'wizard/kg_po_pending_stm_wizard.xml',
			#~ 'wizard/po_indent_to_order_wizard.xml',
			#~ 'wizard/po_indent_to_grn_wizard.xml',
			#~ 'wizard/po_to_grn_wizard.xml',
			#~ 'wizard/po_to_issue_wizard.xml',
			#~ 'wizard/kg_po_register_wiz.xml',
			#~ 'wizard/kg_so_register_wiz.xml',
			#~ 'wizard/kg_po_bill_register_wiz.xml',
            #~ 'wizard/kg_so_bill_register_wiz.xml',
            #~ 'wizard/kg_category_count_wizard.xml',
            #~ 'wizard/kg_purchase_invoice_reg_wiz.xml',
            #~ 'report/excel/kg_gate_pass_excel.xml',
            #~ 'excel/kg_excel_po_register.xml',
			],
			
	'test': [
        'test/ui/print_report.yml',
          ],
    #'css': ['static/src/css/state.css'],
    'auto_install': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

