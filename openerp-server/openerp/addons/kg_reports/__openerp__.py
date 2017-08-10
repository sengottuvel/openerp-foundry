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
		'planning/wizard/kg_foundry_partlist_print_view.xml',
		'planning/wizard/kg_casting_list_view.xml',	
		'planning/wizard/kg_machine_list_print_view.xml',		
		'planning/wizard/kg_workorder_print_view.xml',	
		'planning/wizard/kg_spare_print_view.xml',
		'planning/wizard/kg_casting_completion_view.xml',		
		'planning/wizard/kg_pouring_over_view.xml',
		'planning/wizard/kg_purchase_list_view.xml',
		'planning/wizard/kg_accessories_list_view.xml',
		'planning/wizard/kg_supplied_order_print_view.xml',
								
		'purchase/excel/kg_excel_po_register_view.xml',
		'purchase/wizard/kg_po_register_wiz.xml',
		'purchase/wizard/kg_vendor_profile_wiz_view.xml',
		'warehouse/wizard/main_closing_stock_wizard.xml',
		'warehouse/wizard/grn_register_report_wizard.xml',
		'warehouse/wizard/dep_issue_register_wizard.xml',
		'warehouse/wizard/kg_grn_register_wiz_view.xml',
		'crm/kg_wo_copy_view.xml',
		
		'hrms/excel/kg_excel_worker_ctc_report_view.xml',
		'hrms/excel/kg_excel_pf_report_view.xml',
		'hrms/excel/kg_excel_esi_report_view.xml',
		'hrms/excel/kg_excel_permission_report_view.xml',
		'hrms/excel/kg_excel_on_duty_report_view.xml',
		'hrms/excel/kg_excel_attendance_report_view.xml',
		'hrms/excel/kg_excel_staff_ctc_report_view.xml',
		'hrms/excel/kg_excel_advance_report_view.xml',
		'planning/excel_report/kg_machine_list_excel_view.xml',
		'planning/excel_report/kg_foundry_partlist_excel_view.xml',
		],
    'installable': True,
    'auto_install': True,
}
