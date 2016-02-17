from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import re
from operator import itemgetter
from itertools import groupby
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import calendar
today = datetime.now()

a = datetime.now()
dt_time = a.strftime('%m/%d/%Y %H:%M:%S')


class kg_po_advance(osv.osv):

	_name = "kg.po.advance"
	_description = "PO Advance"
	_columns = {
	
		'created_by' : fields.many2one('res.users', 'Created By', readonly=True),
		'creation_date':fields.datetime('Creation Date',required=True,readonly=True),
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),		
		
		'approved_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Approved By', readonly=True),
		
		'confirmed_date': fields.datetime('Confirmed Date', readonly=True),
		'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		
		'reject_date': fields.datetime('Rejected Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		
		'cancel_date': fields.datetime('Canceled Date', readonly=True),
		'can_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		
		'confirm_flag':fields.boolean('Confirm Flag'),
		'approve_flag':fields.boolean('Expiry Flag'),
		
		'name':fields.char('Advance No',readonly=True),
		'advance_date':fields.date('Advance Date',readonly=False, states={'approved':[('readonly',True)]}),
		'state': fields.selection([('draft','Draft'),('confirmed','Waiting for approval'),('approved','Approved'),('update','Update'),
				('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True,track_visibility='onchange',select=True),
		'line_ids':fields.one2many('kg.po.advance.line','advance_header_id','Line Id',readonly=True),
		'active': fields.boolean('Active',readonly=True),
		'remark': fields.text('Remarks'),
		'supplier_id':fields.many2one('res.partner','Supplier',required=True,readonly=False, states={'approved':[('readonly',True)]}),
		'po_id':fields.many2one('purchase.order','PO No',
				domain="[('partner_id','=',supplier_id), '&', ('state','!=','draft')]",required=True,
				readonly=False, states={'approved':[('readonly',True)]}),
		'po_date':fields.date('PO Date',readonly=True),
		'net_amt': fields.float('Total Net Amount',readonly=True),
		'advance_amt': fields.float('Advance Amount',required=True,readonly=False, states={'approved':[('readonly',True)]}),
		'balance_advance_amt': fields.float('Balance Net Amount',readonly=True),
		'amt_paid_so_far':fields.float('Advance Paid So far',readonly=True),
		'bal_adv':fields.float('Balance Advance',readonly=True),
		'line_state':fields.selection([('draft','Draft'),('loaded','Loaded')],'Status'),
	}
		
	def _future_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		advance_date = rec.advance_date
		advance_date = str(advance_date)
		advance_date = datetime.strptime(advance_date, '%Y-%m-%d')
		if advance_date > today:
			return False
		return True		
		
	def _check_adv_amt(self,cr,uid,ids,context = None):
		rec = self.browse(cr,uid,ids[0])
		if rec.advance_amt <= 0.00:
			return False
		else:
			return True
			
	_constraints = [		
			  
		(_future_date_check, 'System not allow to save with future date. !!',['date']),
		(_check_adv_amt, 'Please Check the advance amount. Advance amount should be greater than Zero!!',['Advance amount']),

	   ]
	 
	_defaults = {
		
		'created_by': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'advance_date': fields.date.context_today,
		'state': 'draft',
		'name':'',
		'active': True,
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_po_advance', context=c),			
		'line_state':'draft'
	}
	
	
	def email_ids(self,cr,uid,ids,context = None):
		email_from = []
		email_to = []
		email_cc = []
		val = {'email_from':'','email_to':'','email_cc':''}
		ir_model = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		mail_form_ids = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		for ids in mail_form_ids:
			mail_form_rec = self.pool.get('kg.mail.settings').browse(cr,uid,ids)
			if mail_form_rec.doc_name.model == 'kg.po.advance':
				email_from.append(mail_form_rec.name)
				mail_line_id = self.pool.get('kg.mail.settings.line').search(cr,uid,[('line_entry','=',ids)])
				for mail_id in mail_line_id:
					mail_line_rec = self.pool.get('kg.mail.settings.line').browse(cr,uid,mail_id)
					if mail_line_rec.to_address:
						email_to.append(mail_line_rec.mail_id)
					if mail_line_rec.cc_address:
						email_cc.append(mail_line_rec.mail_id)
			else:
				pass			
		val['email_from'] = email_from
		val['email_to'] = email_to
		val['email_cc'] = email_cc
		return val
	
	def load_po_details(self,cr,uid,ids,context = None):
		rec = self.browse(cr,uid,ids[0])
		adv_amt = 0.00
		bal_amt = 0.00
		net_amt = 0.00
		cr.execute("""select name,advance_date,advance_amt,net_amt,balance_advance_amt from kg_po_advance where po_id = %s and state = 'approved'"""%(rec.po_id.id))
		data = cr.dictfetchall()
		cr.execute("""delete from kg_po_advance_line where advance_header_id = %s"""%(ids[0]))
		for pre_rec in data:
			self.pool.get('kg.po.advance.line').create(cr,uid,{
				'advance_header_id':ids[0],
				'advance_no':pre_rec['name'],
				'advance_date':pre_rec['advance_date'],
				'adv_amt':pre_rec['advance_amt'],
				'balance_net_amt':pre_rec['balance_advance_amt'],
				})
			adv_amt += pre_rec['advance_amt']
			net_amt = pre_rec['net_amt']
		bal_amt = net_amt - adv_amt
		rec.write({'line_state':'loaded','balance_advance_amt':bal_amt,'amt_paid_so_far':adv_amt})
		return True	
	
	def onchange_po_id(self, cr, uid, ids, po_id,advance_amt):
		value = {'po_date':'','net_amt':0.00}
		adv_amt = 0.00
		bal_amt = 0.00
		net_amt = 0.00
		po_rec = self.pool.get('purchase.order').browse(cr,uid,po_id)
		cr.execute("""select name,advance_date,advance_amt,net_amt,balance_advance_amt from kg_po_advance where po_id = %s and state = 'approved'"""%(po_id))
		data = cr.dictfetchall()
		for pre_rec in data:
			adv_amt += pre_rec['advance_amt']
			net_amt = pre_rec['net_amt']
		bal_amt = net_amt - adv_amt
		return {'value': {
			'po_date' : po_rec.date_order,
			'net_amt':po_rec.amount_total,
			'amt_paid_so_far':adv_amt,
			'balance_advance_amt':bal_amt
		}}
	
	def onchane_adv_amt(self,cr,uid,ids,po_id,advance_amt,net_amt):
		po_rec = self.pool.get('purchase.order').browse(cr,uid,po_id)
		adv_amt = 0.00
		cr.execute("""select name,advance_date,advance_amt,net_amt from kg_po_advance where po_id = %s and state = 'approved'"""%(po_id))
		data = cr.dictfetchall()
		for pre_rec in data:
			adv_amt += pre_rec['advance_amt']
		adv_amt += advance_amt
		if adv_amt > net_amt:
			raise osv.except_osv(
					_('Please check the advance amount.'),
					_('Advance Amount Should not be greater than Net Amount!'))
		else:
			return True
			
	def entry_confirm(self, cr, uid, ids,context=None):
		advance_rec = self.browse(cr,uid,ids[0])
		### Checking Advance date ###
		today_date = today.strftime('%Y-%m-%d')
		adv_amt = 0.00
		po_id = 0
		search_po_grn_id = self.pool.get('kg.po.grn').search(cr,uid,[('po_id','=',advance_rec.po_id.id)])
		if search_po_grn_id:
			raise osv.except_osv(
								_('GRN is created for this PO'),
								_('You can not give advance to this PO'))
		else:
			cr.execute("""select name,advance_date,advance_amt,net_amt from kg_po_advance where po_id = %s and state = 'approved'"""%(advance_rec.po_id.id))
			data = cr.dictfetchall()
			adv_amt = 0.00
			adv_amt_2 = 0.00
			for pre_rec in data:
				adv_amt += pre_rec['advance_amt']
				adv_amt_2 = adv_amt
			adv_amt_2 += advance_rec.advance_amt
			bal_amt = advance_rec.net_amt - adv_amt 
			if adv_amt_2 > advance_rec.net_amt:
				raise osv.except_osv(
					_('Please check the advance amount.'),
					_('Advance Amount Should not be greater than Net Amount!'))
					
		self.write(cr,uid,ids[0],{'state':'confirmed',
								  'confirm_flag':'True',
								  'conf_user_id':uid,
								  'confirmed_date':dt_time,
								  'balance_advance_amt':bal_amt,
								  'amt_paid_so_far':adv_amt,
								  'name': self.pool.get('ir.sequence').get(cr, uid, 'kg.po.advance') or '',
								   })
		cr.execute("""select all_transaction_mails('PO Advance Approval',%s)"""%(ids[0]))
		data = cr.fetchall();
		vals = self.email_ids(cr,uid,ids,context = context)
		if (not vals['email_to']) or (not vals['email_cc']):
			pass
		else:
			ir_mail_server = self.pool.get('ir.mail_server')
			msg = ir_mail_server.build_email(
					email_from = vals['email_from'][0],
					email_to = vals['email_to'],
					subject = "	PO Advance - Waiting For Approval",
					body = data[0][0],
					email_cc = vals['email_cc'],
					object_id = ids[0] and ('%s-%s' % (ids[0], 'kg.po.advance')),
					subtype = 'html',
					subtype_alternative = 'plain')
			res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
		return True	
	
	def entry_approve(self, cr, uid, ids,context=None):
		advance_rec = self.browse(cr,uid,ids[0])
		if advance_rec.conf_user_id.id == uid:
				raise osv.except_osv(
						_('Warning'),
						_('Approve cannot be done by same user'))
		else:
			adv_amt = 0.00
			sql = """select name,advance_date,advance_amt,net_amt from kg_po_advance where po_id = %s and state = 'approved'"""%(advance_rec.po_id.id)
			cr.execute(sql)			
			data = cr.dictfetchall()
			adv_amt = 0.00
			for pre_rec in data:
				adv_amt += pre_rec['advance_amt']
			bal_amt = advance_rec.net_amt - (advance_rec.advance_amt + adv_amt)
			self.write(cr,uid,ids[0],{'state':'approved',
									  'approve_flag':'True',
									  'app_user_id':uid,
									  'approved_date':dt_time,
									  'amt_paid_so_far':adv_amt,
									  'balance_advance_amt':bal_amt,
									  'bal_adv':advance_rec.advance_amt,
									  'update':True
									   })	
			cr.execute("""select all_transaction_mails('PO Advance Approval',%s)"""%(ids[0]))
			data = cr.fetchall();
			vals = self.email_ids(cr,uid,ids,context = context)
			if (not vals['email_to']) or (not vals['email_cc']):
				pass
			else:
				ir_mail_server = self.pool.get('ir.mail_server')
				msg = ir_mail_server.build_email(
						email_from = vals['email_from'][0],
						email_to = vals['email_to'],
						subject = "	PO Advance - Approved",
						body = data[0][0],
						email_cc = vals['email_cc'],
						object_id = ids[0] and ('%s-%s' % (ids[0], 'kg.po.advance')),
						subtype = 'html',
						subtype_alternative = 'plain')
				res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
		return True
	
	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {
						'state': 'reject',
						'rej_user_id': uid,
						'reject_date': dt_time})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter rejection remark in remark field !!'))
		return True

	def entry_cancel(self,cr,uid,ids,context=None):
		## Don't allow to cancel if this id linked with other transaction or master
		rec = self.browse(cr,uid,ids[0])
		if not rec.remark :
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter Cancel remark in remark field !!'))
		else:
			self.write(cr, uid, ids, {'state': 'cancel','can_user_id': uid,
				'cancel_date': dt_time})
		return True
	
	def create(self, cr, uid,vals,context=None):
		po_rec = self.pool.get('purchase.order').browse(cr,uid,vals['po_id'])
		
		vals.update({'net_amt':po_rec.amount_total,
					'po_date':po_rec.date_order,
							})						  
		order =  super(kg_po_advance, self).create(cr, uid, vals, context=context)
		return order
	
	def entry_draft(self,cr,uid,ids,context=None):
		# While change state corresponding back updated to be done
		self.write(cr, uid, ids, {'state': 'draft'})
		return True
	
	def unlink(self,cr,uid,ids,context = None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def copy(self, cr, uid, id, default=None, context=None):
		raise osv.except_osv(_('Forbbiden to duplicate'), _('Is not possible to duplicate the record, please create a new one.'))
		
kg_po_advance()

class kg_po_advance_line(osv.osv):

	_name = "kg.po.advance.line"
	_description = "PO Advance Line"
	_order = "advance_date"
	_columns = {
		
		'advance_no':fields.char('Advance No',readonly=True),
		'advance_date':fields.date('Advance Date'),
		'advance_header_id' : fields.many2one('kg.po.advance', 'Header ID'),
		'adv_amt':fields.float('Advance Amount'),
		'balance_net_amt':fields.float('Balance Net Amount'),
	}
	
kg_po_advance_line()
