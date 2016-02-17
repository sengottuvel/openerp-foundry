##############################################################################
#
#   This is New Customized Module
#
##############################################################################

{
    'name': 'Contractor Inward',
    'version': '0.1',
    'author': 'Manjula',
    'category': 'BASE',    
    'depends' : ['base','product','account','kg_brandmaster','kg_inwardmaster'],
    'data': [
		'kg_contractor_inward.xml',
		'contractor_report_view.xml'
		],    
    'auto_install': False,
    'installable': True,
}

