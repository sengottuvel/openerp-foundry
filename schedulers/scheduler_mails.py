import xmlrpclib
username = 'admin' #the user
pwd = 'admin'      #the password of the user
dbname = 'sam_phaseI'    #the database
# Server Connectivity

sock_common = xmlrpclib.ServerProxy ('http://localhost:8069/xmlrpc/common')

uid = sock_common.login(dbname, username, pwd)

sock = xmlrpclib.ServerProxy('http://localhost:8069/xmlrpc/object')

## Scheduler List#
#~ sock.execute(dbname, uid, pwd, 'kg.scheduler', 'planning_vs_production_register_scheduler_mail')

#~ sock.execute(dbname, uid, pwd, 'kg.scheduler', 'daily_stock_statement_scheduler_mail')

#~ sock.execute(dbname, uid, pwd, 'kg.scheduler', 'transaction_summary_list_scheduler_mail')

sock.execute(dbname, uid, pwd, 'kg.scheduler', 'daily_approved_po_grn_summary')

sock.execute(dbname, uid, pwd, 'kg.scheduler', 'userwise_summary_list_scheduler_mail')
