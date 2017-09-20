import xmlrpclib
username = 'admin' #the user
pwd = 'admin'      #the password of the user
dbname = 'sam_phaseI'    #the database
# Server Connectivity

sock_common = xmlrpclib.ServerProxy ('http://localhost:8069/xmlrpc/common')

uid = sock_common.login(dbname, username, pwd)

sock = xmlrpclib.ServerProxy('http://localhost:8069/xmlrpc/object')

## Scheduler List#
sock.execute(dbname, uid, pwd, 'kg.daily.attendance', 'month_att_entry_creation')
sock.execute(dbname, uid, pwd, 'kg.monthly.attendance', 'month_att_entry_creation')
sock.execute(dbname, uid, pwd, 'kg.monthly.attendance', 'update_monthly_att')
