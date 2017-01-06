{
    'name': 'SAM Reports',
    'version': '1.0',
    'description': """
===================================================
""",
    'author': 'Karthikeyan',
    'maintainer': 'Karthikeyan',
    'website': 'http://www.openerp.com',
    'depends': ['base','kg_pumpmodel_master','purchase','stock','kg_schedule'],
    'data': [		
		'planning/wizard/kg_pouring_pending_print_view.xml',
		'purchase/excel/kg_excel_po_register_view.xml',
		'purchase/wizard/kg_po_register_wiz.xml',
		'warehouse/wizard/main_closing_stock_wizard.xml',
		'warehouse/wizard/grn_register_report_wizard.xml',
		'warehouse/wizard/dep_issue_register_wizard.xml',
		],
    'installable': True,
    'auto_install': True,
}
