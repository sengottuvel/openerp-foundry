##############################################################################
#
#   This is New Master Module
#
##############################################################################

{
    'name': 'Job Nature',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'BASE',        
    'depends' : ['base','hr'],
    'data': [
			'kg_job_nature_view.xml',
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
