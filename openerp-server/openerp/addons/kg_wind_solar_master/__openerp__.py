##############################################################################
#
#   This is Wind Solar Master Module
#
##############################################################################

{
    'name': 'Wind Solar Master',
    'version': '0.1',
    'author': 'Sujith',
    'category': 'BASE',        
    'depends' : ['base'],
    'data': [
			'kg_wind_solar_master_view.xml',
			#~ 'default_data.xml'
			],
			
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}
