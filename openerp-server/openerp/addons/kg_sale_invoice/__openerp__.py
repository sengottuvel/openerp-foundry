##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).

##############################################################################
{
    'name': 'Sale Invoice',
    'version': '0.1',
    'author': 'Kaerhikeyan S',
    'category': 'CRM',
    'website': 'http://www.openerp.com',
    'depends' : ['base','account','kg_partners','kg_work_order','kg_patten_master','kg_moc_master','kg_pumpmodel_master','kg_accessories_master','kg_expense_master','kg_customer_advance'],
    'data': ['kg_sale_invoice_view.xml'],
    'auto_install': False,
    'installable': True,
}

