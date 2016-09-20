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


class kg_customer_advance(osv.osv):

	_name = "kg.customer.advance"
	_description = "Customer Advance"
	_columns = {
	
		
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),		
			
		'confirm_flag':fields.boolean('Confirm Flag'),
		'approve_flag':fields.boolean('Expiry Flag'),
		
		'name':fields.char('Advance No',readonly=True),
		'advance_date':fields.date('Advance Date',readonly=False, states={'approved':[('readonly',True)]}),
		'state': fields.selection([('draft','Draft'),('confirmed','Waiting for approval'),('approved','Approved'),('update','Update'),
				('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True,track_visibility='onchange',select=True),
		'line_ids':fields.one2many('ch.customer.advance.line','header_id','Line Id',readonly=True),
		'active': fields.boolean('Active',readonly=True),
		'remark': fields.text('Remarks'),
		'customer_id':fields.many2one('res.partner','Customer',required=True,readonly=False, states={'approved':[('readonly',True)]}, domain=[('customer', '=', True)]),
		'order_id':fields.many2one('kg.work.order','Work Order No',
				domain="[('partner_id','=',customer_id), '&', ('state','!=','draft')]",required=True,
				readonly=False, states={'approved':[('readonly',True)]}),
		'order_date':fields.date('Order Date',readonly=True),
		'net_amt': fields.float('Total Net Amount',readonly=True),
		'advance_amt': fields.float('Advance Amount',required=True,readonly=False, states={'approved':[('readonly',True)]}),
		'balance_advance_amt': fields.float('Balance Net Amount',readonly=True),
		'amt_paid_so_far':fields.float('Advance Paid So far',readonly=True),
		'bal_adv':fields.float('Balance Advance',readonly=True),
		'line_state':fields.selection([('draft','Draft'),('loaded','Loaded')],'Status'),
		
		'cancel_remark': fields.text('Cancel Remarks',readonly=True,states={'approved':[('readonly',False)]}),
		'created_by' : fields.many2one('res.users', 'Created By', readonly=True),
		'creation_date':fields.datetime('Creation Date',required=True,readonly=True),
		'confirmed_by' : fields.many2one('res.users', 'Confirmed By', readonly=True,select=True),
		'confirmed_date': fields.datetime('Confirmed Date',readonly=True),
		'reject_date': fields.datetime('Reject Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'approved_by' : fields.many2one('res.users', 'Approved By', readonly=True,select=True),
		'approved_date' : fields.datetime('Approved Date',readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date' : fields.datetime('Last Updated Date',readonly=True),
		'update_user_id' : fields.many2one('res.users','Last Updated By',readonly=True),
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
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_customer_advance', context=c),			
		'line_state':'draft'
	}
	
	
	
	def load_order_details(self,cr,uid,ids,context = None):
		rec = self.browse(cr,uid,ids[0])
		adv_amt = 0.00
		bal_amt = 0.00
		net_amt = 0.00
		cr.execute("""select name,advance_date,advance_amt,net_amt,balance_advance_amt from kg_customer_advance where order_id = %s and state = 'approved'"""%(rec.order_id.id))
		data = cr.dictfetchall()
		cr.execute("""delete from ch_customer_advance_line where header_id = %s"""%(ids[0]))
		for pre_rec in data:
			self.pool.get('ch.customer.advance.line').create(cr,uid,{
				'header_id':ids[0],
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
	
	def onchange_order_id(self, cr, uid, ids, order_id,advance_amt):
		value = {'order_date':'','net_amt':0.00}
		adv_amt = 0.00
		bal_amt = 0.00
		net_amt = 0.00
		order_rec = self.pool.get('kg.work.order').browse(cr,uid,order_id)
		cr.execute("""select name,advance_date,advance_amt,net_amt,balance_advance_amt from kg_customer_advance where order_id = %s and state = 'approved'"""%(order_id))
		data = cr.dictfetchall()
		for pre_rec in data:
			adv_amt += pre_rec['advance_amt']
			net_amt = pre_rec['net_amt']
		bal_amt = net_amt - adv_amt
		return {'value': {
			'order_date' : order_rec.entry_date,
			'net_amt':order_rec.order_value,
			'amt_paid_so_far':adv_amt,
			'balance_advance_amt':bal_amt
		}}
	
	def onchane_adv_amt(self,cr,uid,ids,order_id,advance_amt,net_amt):
		order_rec = self.pool.get('kg.work.order').browse(cr,uid,order_id)
		adv_amt = 0.00
		cr.execute("""select name,advance_date,advance_amt,net_amt from kg_customer_advance where order_id = %s and state = 'approved'"""%(order_id))
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
		
		
		cr.execute("""select name,advance_date,advance_amt,net_amt from kg_customer_advance where order_id = %s and state = 'approved'"""%(advance_rec.order_id.id))
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
					
		poa_name = ''		
		if not advance_rec.name:
					
			poa_no = self.pool.get('ir.sequence').get(cr, uid, 'kg.customer.advance') or ''
			poa_no_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.customer.advance')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,poa_no_id[0])
			
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(poa_no_id[0],rec.code,advance_rec.advance_date))
			poa_name = cr.fetchone();	
			self.write(cr,uid,ids,{'name':str(poa_name[0])})			
		
					
		self.write(cr,uid,ids[0],{'state':'confirmed',
								  'confirm_flag':'True',
								  'confirmed_by':uid,
								  'confirmed_date':dt_time,
								  'balance_advance_amt':bal_amt,
								  'amt_paid_so_far':adv_amt,
								  
								   })
		
		return True	
	
	def entry_approve(self, cr, uid, ids,context=None):
		advance_rec = self.browse(cr,uid,ids[0])		
		adv_amt = 0.00
		sql = """select name,advance_date,advance_amt,net_amt from kg_customer_advance where order_id = %s and state = 'approved'"""%(advance_rec.order_id.id)
		cr.execute(sql)			
		data = cr.dictfetchall()
		adv_amt = 0.00
		for pre_rec in data:
			adv_amt += pre_rec['advance_amt']
		bal_amt = advance_rec.net_amt - (advance_rec.advance_amt + adv_amt)
		self.write(cr,uid,ids[0],{'state':'approved',
								  'approve_flag':'True',
								  'approved_by':uid,
								  'approved_date':dt_time,
								  'amt_paid_so_far':adv_amt,
								  'balance_advance_amt':bal_amt,
								  'bal_adv':advance_rec.advance_amt,
								  'update':True
								   })	
		
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
		if not rec.cancel_remark :
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter Cancel remark in remark field !!'))
		else:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid,
				'cancel_date': dt_time})
		return True
	
	def create(self, cr, uid,vals,context=None):
		order_rec = self.pool.get('kg.work.order').browse(cr,uid,vals['order_id'])
		
		vals.update({'net_amt':order_rec.order_value,
					'order_date':order_rec.entry_date,
							})						  
		order =  super(kg_customer_advance, self).create(cr, uid, vals, context=context)
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
		
	
		
	def write(self, cr, uid, ids, vals, context=None):		
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_customer_advance, self).write(cr, uid, ids, vals, context)
		
kg_customer_advance()

class ch_customer_advance_line(osv.osv):

	_name = "ch.customer.advance.line"
	_description = "Customer Advance Line"
	_order = "advance_date"
	_columns = {
		
		'advance_no':fields.char('Advance No',readonly=True),
		'advance_date':fields.date('Advance Date'),
		'header_id' : fields.many2one('kg.customer.advance', 'Header ID'),
		'adv_amt':fields.float('Advance Amount'),
		'balance_net_amt':fields.float('Balance Net Amount'),
	}
	
ch_customer_advance_line()
