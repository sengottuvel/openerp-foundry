##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).

##############################################################################
{
    'name': 'Users Management System',
    'version': '0.1',
    'author': 'Karthikeyan',
    'category': 'User_Management',
    'images': ['images/purchase_requisitions.jpeg'],
    'website': 'http://www.openerp.com',
    'description': """
This module allows you to manage your Purchase Requisition.
===========================================================

When a purchase order is created, you now have the opportunity to save the
related requisition. This new object will regroup and will allow you to easily
keep track and order all your purchase orders.
""",
    'depends' : ['base','kg_depmaster'],
    'data': [
			
			'groups_data.xml',
			'kg_users_view.xml',			
			'module_access/foundry/kg_foundry_admin.xml',
			'module_access/foundry/kg_foundry_admin_read.xml',
			'module_access/foundry/kg_foundry_transactions.xml',
			'module_access/inventory/kg_inventory_masters.xml',
			'module_access/inventory/kg_inventory_masters_admin.xml',
			'module_access/inventory/kg_inventory_transactions.xml',
			'module_access/machineshop/kg_ms_masters.xml',
			'module_access/machineshop/kg_ms_transactions.xml',
			'module_access/purchase/kg_purchase_masters.xml',
			'module_access/purchase/kg_purchase_masters_admin.xml',			
			'module_access/purchase/kg_purchase_transactions.xml',
			'module_access/purchase/kg_vendor_quote_transactions.xml',		
			'module_access/crm/kg_crm_admin.xml',		
				
			
			
			],
			
    'auto_install': False,
    'installable': True,
}

