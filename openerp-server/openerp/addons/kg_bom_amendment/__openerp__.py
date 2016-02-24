##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).

##############################################################################
{
    'name': 'KG BOM Amendment',
    'version': '0.1',
    'author': 'Karthikeyan',
    'category': 'MRP',
    'website': 'http://www.openerp.com',
    'depends' : ['base','product','sale','mrp'],
    'data': ['kg_bom_amendment_view.xml'],
    'css': [ 'static/src/css/bom.css' ],
    'auto_install': False,
    'installable': True,
}

