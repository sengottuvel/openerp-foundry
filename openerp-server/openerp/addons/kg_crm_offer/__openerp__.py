##############################################################################
#
#   This is New Customized CRM Offer Module
#
##############################################################################

{

    'name': 'CRM Offer',
    'version': '0.1',
    'author': 'Thangaraj',    
    'depends' : ['base','kg_industry_master','kg_machine_shop','kg_bom','kg_crm_enquiry'],
    'data': [
				'kg_crm_offer_view.xml','jasper_report.xml',
			],
    'js': ['static/src/js/offer_reminder.js'],
    'qweb': ['static/src/xml/offer_reminder.xml'],
    'css' : ['static/src/css/offer_reminder.css'],
    'auto_install': False,
    'installable': True,
    
}

