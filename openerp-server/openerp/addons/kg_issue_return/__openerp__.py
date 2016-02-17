##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).

##############################################################################
{
    'name': 'kg Issue Return',
    'version': '0.1',
    'author': 'Ramya V',
    'category': 'Warehouse',
    'images': ['images/purchase_requisitions.jpeg'],
    'website': 'http://www.openerp.com',
    'description': """
This module allows you to manage your Purchase Requisition.
===========================================================

When a purchase order is created, you now have the opportunity to save the
related requisition. This new object will regroup and will allow you to easily
keep track and order all your purchase orders.
""",
    'depends' : ['base', 'product','kg_depmaster','kg_department_issue'],
    'data': ['kg_issue_return_view.xml',
			'issue_return_report_view.xml'],
    'auto_install': False,
    'installable': True,
}

