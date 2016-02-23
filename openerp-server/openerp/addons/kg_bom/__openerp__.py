##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).

##############################################################################
{
    'name': 'KG BOM',
    'version': '0.1',
    'author': 'Karthikeyan',
    'category': 'MRP',
    'website': 'http://www.openerp.com',
    'depends' : ['base','product','sale','mrp','kg_pumpmodel_master'],
    'data': ['kg_bom_view.xml'],
    'auto_install': False,
    'installable': True,
}

