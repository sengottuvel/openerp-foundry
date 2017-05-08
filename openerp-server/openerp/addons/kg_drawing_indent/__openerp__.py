##############################################################################
#
#   This is New Customized Module
#
##############################################################################

{
    'name': 'Drawing Indent',
    'version': '0.1',
    'author': 'Sangeetha',    
    'depends' : ['base','kg_work_order'],
    'data': [
		'kg_drawing_indent_view.xml',		
		'sequence_data.xml',
		],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

