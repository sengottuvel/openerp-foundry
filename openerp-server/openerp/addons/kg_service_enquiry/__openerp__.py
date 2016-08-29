##############################################################################
#
#   This is New Customized Service Enquiry Module
#
##############################################################################

{

    'name': 'Service Enquiry',
    'version': '0.1',
    'author': 'Thangaraj',    
    'depends' : ['base','kg_industry_master','kg_machine_shop','kg_work_order'],
    'data': ['kg_service_enquiry_view.xml'],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
    
}

