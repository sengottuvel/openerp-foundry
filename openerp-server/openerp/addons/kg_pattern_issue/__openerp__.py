##############################################################################
#
#   This is New Customized Module
#
##############################################################################

{
    'name': 'Pattern Issue',
    'version': '0.1',
    'author': 'Sangeetha',    
    'depends' : ['base', 'kg_pattern_request','kg_stock_inward'],
    'data': ['kg_pattern_issue_view.xml'],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}

