##############################################################################
#
#   This is New Customized Module
#
##############################################################################

{
    'name': 'Drawing Issue',
    'version': '0.1',
    'author': 'Sangeetha',    
    'depends' : ['base','kg_work_order','kg_drawing_indent'],
    'data': [
		'kg_drawing_issue_view.xml',		
		'sequence_data.xml',
		],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

