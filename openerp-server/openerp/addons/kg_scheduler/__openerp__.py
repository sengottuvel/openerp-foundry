
{
    'name': 'Auto Scheduler',
    'version': '0.1',
    'author': 'Thangaraj',
    'category': 'General',
    'depends' : ['base'],
    'data': ['kg_scheduler_view.xml','kg_popup_view.xml','kg_mail_queue_view.xml',],
    'js': ['static/src/js/product_expiry_reminder.js'],
    'qweb': ['static/src/xml/product_expiry_reminder.xml'],
    'css' : ['static/src/css/product_expiry_reminder.css'],
    'auto_install': False,
    'installable': True,
}

