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
			'kg_planning_admin.xml',
			
			],
    'auto_install': False,
    'installable': True,
}

