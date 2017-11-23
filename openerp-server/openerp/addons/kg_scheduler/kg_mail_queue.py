from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
import smtplib
from datetime import date
from datetime import datetime

class kg_mail_queue(osv.osv):

	_name = "kg.mail.queue"
	_description = "Mail Queue"
	_order = "crt_date desc"

	_columns = {
				
		'source': fields.char('Source'),	
		'created_date':fields.date('Date'),
		'state': fields.selection([('pending','Pending'),('sent','Sent')],'Status', readonly=True),	
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'active': fields.boolean('Active'),
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'mail_from': fields.char('From'),	
		'mail_to': fields.char('To'),	
		'mail_cc': fields.char('Cc'),	
		'mail_bcc': fields.char('Bcc'),	
		'attachment': fields.binary('Attachments'),	
		'transaction_id': fields.integer('Transaction ID'),	
		'subject': fields.char('Subject'),	
		'body': fields.html('Body'),	
		'sent_time': fields.datetime('Sent Time'),	
		'content_type': fields.selection([('mail','Mail'),('sms','SMS')],'Content Type'),	
		'body_1': fields.char('Body 1'),
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.mail.queue', context=c),
		'active': True,
		'state': 'pending',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'created_date': lambda * a: time.strftime('%Y-%m-%d'),
		'entry_mode': 'auto',
		'content_type': 'mail',
		'mail_from': 'erpmail@kgcloud.org',
		
	}

	### Basic Needs

	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'state': 'reject','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter the remarks in rejection remark field !!'))
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state not in ('draft','cancel'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_mail_queue, self).write(cr, uid, ids, vals, context)
		
		
	def send_mail(self,cr,uid,ids,context = None):	
		today = date.today()
		que_search = self.search(cr,uid,[('created_date','=',today),('state','=','pending')])
		if que_search:	
			for que_rec in self.browse(cr, uid, que_search, context=context):
				if que_rec.state == 'pending':
					email_from = [que_rec.mail_from]
					if que_rec.mail_to:
						email_to = [que_rec.mail_to]
					else:
						email_to = ['']			
					if que_rec.mail_cc:
						email_cc = [que_rec.mail_cc]
					else:
						email_cc = ['']		
					if que_rec.mail_bcc:
						email_bcc = [que_rec.mail_bcc]
					else:
						email_bcc = ['']	
					ir_mail_server = self.pool.get('ir.mail_server')
					msg = ir_mail_server.build_email(
						email_from = email_from[0],
						email_to = email_to,
						subject = que_rec.subject,
						body = que_rec.body_1,
						email_cc = email_cc,
						email_bcc = email_bcc,
						object_id = ids and ('%s-%s' % (ids, 'kg.mail.settings')),
						subtype = 'html',
						subtype_alternative = 'plain')
					res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
					self.write(cr,uid,que_rec.id,{'state':'sent','sent_time':time.strftime('%Y-%m-%d %H:%M:%S')})
				else:
					pass
		else:
			pass
			
		return True
		
	
	_constraints = [
	
	]
	
	
kg_mail_queue()
