##############################################################################
#
#   This is New Master Module
#
##############################################################################

{
    'name': 'Accessories Category Master',
    'version': '0.1',
    'author': 'Karthikeyan S',
    'category': 'BASE',        
    'depends' : ['base'],
    'data': [
			'kg_accessories_category_view.xml',
			'default_data.xml'
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
