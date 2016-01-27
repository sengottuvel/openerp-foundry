from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time

import openerp.addons.decimal_precision as dp

class kg_scheduler(osv.osv):

	_name = "kg.scheduler"
	_description = "Scheduler Time Master"
	
	def planning_vs_production_register_scheduler_mail(self,cr,uid,ids=0,context = None):		
		cr.execute("""select all_daily_scheduler_mails('Planning Vs Production')""")
		data = cr.fetchall();
		print "data<<<<<<<<<", data
		if data[0][0] is None:
			return False		
		if data[0][0] is not None:	
			maildet = (str(data[0])).rsplit('~');
			cont = data[0][0].partition('UNWANTED.')		
			email_from = maildet[1]	
			if maildet[2]:	
				email_to = [maildet[2]]
			else:
				email_to = ['']			
			if maildet[3]:
				email_cc = [maildet[3]]	
			else:
				email_cc = ['']		
			ir_mail_server = self.pool.get('ir.mail_server')			
			if maildet[4] != '':
				msg = ir_mail_server.build_email(
					email_from = email_from,
					email_to = email_to,
					subject = maildet[4],
					body = cont[0],
					email_cc = email_cc,
					object_id = ids and ('%s-%s' % (ids, 'kg.mail.settings')),
					subtype = 'html',
					subtype_alternative = 'plain')
				res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
			else:
				pass
			return True
		
	def daily_stock_statement_scheduler_mail(self,cr,uid,ids=0,context = None):
	
		cr.execute("""select all_daily_scheduler_mails('Daily Stock Statement')""")
		data = cr.fetchall();		
		if data[0][0] is None:
			return False
		if data[0][0] is not None:
			maildet = (str(data[0])).rsplit('~');
			cont = data[0][0].partition('UNWANTED.')		
			email_from = maildet[1]		
			if maildet[2]:	
				email_to = [maildet[2]]
			else:
				email_to = ['']	
			if maildet[3]:
				email_cc = [maildet[3]]	
			else:
				email_cc = ['']		
			ir_mail_server = self.pool.get('ir.mail_server')
			if maildet[4] != '':
				msg = ir_mail_server.build_email(
					email_from = email_from,
					email_to = email_to,
					subject = maildet[4],
					body = cont[0],
					email_cc = email_cc,
					object_id = ids and ('%s-%s' % (ids, 'kg.mail.settings')),
					subtype = 'html',
					subtype_alternative = 'plain')
				res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
			else:
				pass
			return True
				
			
	def transaction_summary_list_scheduler_mail(self,cr,uid,ids=0,context = None):		
		cr.execute("""select all_daily_scheduler_mails('Transaction Summary List')""")
		data = cr.fetchall();
		print "data<<<<<<<<<", data
		
		
		if data[0][0] is None:
			return False
		if data[0][0] is not None:	
			maildet = (str(data[0])).rsplit('~');
			cont = data[0][0].partition('UNWANTED.')		
			email_from = maildet[1]	
			if maildet[2]:	
				email_to = [maildet[2]]
			else:
				email_to = ['']			
			if maildet[3]:
				email_cc = [maildet[3]]	
			else:
				email_cc = ['']		
			ir_mail_server = self.pool.get('ir.mail_server')
			if maildet[4] != '':
				msg = ir_mail_server.build_email(
					email_from = email_from,
					email_to = email_to,
					subject = maildet[4],
					body = cont[0],
					email_cc = email_cc,
					object_id = ids and ('%s-%s' % (ids, 'kg.mail.settings')),
					subtype = 'html',
					subtype_alternative = 'plain')
				res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
			else:
				pass
			return True
		

kg_scheduler()
