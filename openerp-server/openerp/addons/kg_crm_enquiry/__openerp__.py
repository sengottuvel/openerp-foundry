##############################################################################
#
#   This is New Customized CRM Enquiry Module
#
##############################################################################

{

    'name': 'CRM Enquiry',
    'version': '0.1',
    'author': 'Thangaraj',    
    'depends' : ['base','kg_industry_master','kg_machine_shop','kg_bom','kg_work_order'],
    'data': ['kg_crm_enquiry_view.xml'],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
    
}

