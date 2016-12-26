
{
    'name': 'KG Department Issue',
    'version': '0.1',
    'author': 'Thangaraj',
    'category': 'Department Issue',
   
    'website': 'http://www.openerp.com',
    'description': """
This module allows you to manage your Item Details.
===========================================================
""",
    'depends' : ['base', 'product','stock','kg_depmaster','kg_outwardmaster','kg_depindent'],
    'data': [
			'kg_department_issue_view.xml',
			'dep_issue_report.xml',
			'wizard/kg_dep_issue_wiz_view.xml',
			],
	 'test': [
        'test/kg_dep_issue_wiz.yml',
        
    ],
    'auto_install': False,
    'installable': True,
}

