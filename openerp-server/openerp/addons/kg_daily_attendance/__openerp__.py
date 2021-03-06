
{
    'name': 'KG Daily Attendance',
    'version': '0.1',
    'author': 'sengottuvelu',
    'category': 'HRM',
    'images': ['images/purchase_requisitions.jpeg'],
    'website': 'http://www.openerp.com',
    'description': """
This module allows you to manage your Purchase Requisition.
===========================================================

When a purchase order is created, you now have the opportunity to save the
related requisition. This new object will regroup and will allow you to easily
keep track and order all your purchase orders.
""",
    'depends' : ['base','hr','kg_employee_category'],
    'data': ['kg_daily_attendance_view.xml'],
    'auto_install': False,
    'installable': True,
}

