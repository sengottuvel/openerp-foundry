##############################################################################
#
#  Bank Statement (Accounts)
#
##############################################################################

{
    'name': 'TDS Process',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'Accounts',        
    'depends' : ['base','account','hr'],
    'data': [
			'kg_tds_process_view.xml',
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
