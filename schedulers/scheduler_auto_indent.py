import xmlrpclib

username = 'admin' 
pwd = 'admin'      
dbname = 'sam_phase_I'    

# Server Connectivity

sock_common = xmlrpclib.ServerProxy ('http://localhost:8069/xmlrpc/common')
uid = sock_common.login(dbname, username, pwd)
sock = xmlrpclib.ServerProxy('http://localhost:8069/xmlrpc/object')

sock.execute(dbname, uid, pwd, 'kg.scheduler', 'auto_purchase_indent')

