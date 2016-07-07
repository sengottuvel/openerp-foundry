##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).

##############################################################################
{
    'name': 'Sam Turbo User Management',
    'version': '0.1',
    'author': 'Karthikeyan',
    'category': 'User_Management',
    'website': 'http://www.openerp.com',
    'description': """
		Sam Turbo User Management
		""",
    'depends' : ['base','kg_menus'],
    'data': [
    
			'kg_groups.xml',
			'foundry/kg_foundry_transactions.xml',
			'foundry/kg_foundry_masters_access.xml',
			'foundry/kg_foundry_masters.xml',
			'machineshop/kg_ms_masters.xml',
			'purchase/kg_purchase_transactions.xml',
			'purchase/kg_purchase_masters.xml',
			'purchase/kg_vendor_quote_transactions.xml',
			'purchase/kg_purchase_masters_admin.xml',
			'purchase/kg_purchase_spl_apl.xml',
			'inventory/kg_inventory_transactions.xml',
			'inventory/kg_inventory_masters.xml',
			'inventory/kg_inventory_masters_admin.xml',
			
			],
    'auto_install': False,
    'installable': True,
}

