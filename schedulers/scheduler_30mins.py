import xmlrpclib

username = 'admin' 
pwd = 'admin@123'      
dbname = 'sam_phaseI'    

# Server Connectivity

sock_common = xmlrpclib.ServerProxy ('http://localhost:8069/xmlrpc/common')
uid = sock_common.login(dbname, username, pwd)
sock = xmlrpclib.ServerProxy('http://localhost:8069/xmlrpc/object')

sock.execute(dbname, uid, pwd, 'purchase.order', 'approved_po_mail')
