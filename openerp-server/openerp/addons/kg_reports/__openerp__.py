{
    'name': 'SAM Reports',
    'version': '1.0',
    'description': """
===================================================
""",
    'author': 'Karthikeyan',
    'maintainer': 'Karthikeyan',
    'website': 'http://www.openerp.com',
    'depends': ['base','kg_pumpmodel_master','purchase','stock'],
    'data': [		
		'planning/wizard/kg_schedule_register_view.xml',
		'planning/wizard/kg_planning_register_view.xml',
		'planning/wizard/kg_production_register_view.xml',
		'planning/wizard/kg_qc_register_view.xml',
		'planning/wizard/kg_allotted_components_view.xml',
		'planning/wizard/kg_stock_statement_view.xml',
		'planning/wizard/kg_stock_inspection_view.xml',
		'purchase/excel/kg_excel_po_register_view.xml',
		'warehouse/wizard/main_closing_stock_wizard.xml',
		],
    'installable': True,
    'auto_install': True,
}
