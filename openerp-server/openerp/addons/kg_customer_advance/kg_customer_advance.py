from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_customer_advance(osv.osv):

	_name = "kg.customer.advance"
	_description = "Customer Advance"
	_order = "entry_date desc"
	
	
	def _balance_amount_value(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		bal_value = 0.00
		for entry in self.browse(cr, uid, ids, context=context):
			bal_value = entry.advance_amt - entry.adjusted_amt			
			result[entry.id] = bal_value
		return result
	
	_columns = {
	
		## Version 0.1
	
		## Basic Info
				
		'name': fields.char('Advance No', size=24,select=True,readonly=True),
		'entry_date': fields.date('Advance Date',required=True),		
		'note': fields.text('Notes'),
		'cancel_remark': fields.text('Cancel'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_sms': fields.boolean('SMS Notification'),
		'flag_email': fields.boolean('Email Notification'),
		'flag_spl_approve': fields.boolean('Special Approval'),
		
		### Entry Info ####
			
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),	
		'active': fields.boolean('Active'),	
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),		
		'ap_rej_date': fields.datetime('Approved/Reject Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Reject By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),			
		
		## Module Requirement Info	
		
		'customer_id':fields.many2one('res.partner','Customer',required=True,readonly=False, states={'approved':[('readonly',True)]}, domain=[('customer', '=', True)]),
		
		'order_id':fields.many2one('kg.work.order','Work Order No',
				domain="[('partner_id','=',customer_id), '&', ('state','!=','draft')]",required=True,
				readonly=False, states={'approved':[('readonly',True)]}),
		
		
	    'advance_amt': fields.float('Advance Amount'),			
		'order_value': fields.float('Order Value'),		
		'adjusted_amt': fields.float('Adjusted Amount'),		
		'balance_amt': fields.function(_balance_amount_value, string='Balance Amount',store=True, type='float'),		
		'order_no': fields.char('Order NO',readonly=True),				
		
		## Child Tables Declaration 				
		'line_ids': fields.one2many('ch.cus.advance.line', 'header_id', "Line Details"),		
				
	}
		
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_customer_advance', context=c),			
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),	
		'state': 'draft',		
		'active': True,
		'entry_mode': 'manual',		
		'flag_sms': False,		
		'flag_email': False,		
		'flag_spl_approve': False,					
		
	}
	
	def onchange_order_value(self, cr, uid, ids, order_id, context=None):
		value = {'order_value':0.00}		
		total_value = 0.00
		order_no = ''
		if order_id:			
			work_rec = self.pool.get('kg.work.order').browse(cr,uid,order_id)		
			total_value = work_rec.order_value
			order_no = work_rec.name
			
		return {'value': {'order_value' : total_value,'order_no':order_no}}	
	
	
	def onchange_customer_id(self, cr, uid, ids, customer_id, context=None):
		value = {}		
		sup_ids = self.pool.get('kg.customer.advance').search(cr,uid,[('customer_id','=',customer_id),('state','=','confirmed')])		
		adv_line_vals=[]			
		for ele in sup_ids:			
			adv_rec = self.pool.get('kg.customer.advance').browse(cr,uid,ele)			
			adv_line_vals.append({
							'advance_no':adv_rec.name,
						   'advance_date':adv_rec.entry_date,
						   'order_no':adv_rec.order_no,
						   'advance_amt':adv_rec.advance_amt,
						   'adjusted_amt':adv_rec.adjusted_amt,
						   'balance_amt':adv_rec.balance_amt,
							})
			value['line_ids'] = adv_line_vals			
		return {'value': value}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		entry_date = rec.entry_date
		entry_date = str(entry_date)
		entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
		if entry_date > today:
			return False
		return True
		
		
	def _check_adv_amt(self,cr,uid,ids,context = None):
		rec = self.browse(cr,uid,ids[0])
		total = 0.00
		for line in rec.line_ids:
			if rec.order_no == line.order_no:
				total += line.balance_amt
		total_amt = rec.advance_amt + total
		if rec.advance_amt <= 0.00 or total_amt > rec.order_value:
			return False
		else:
			return True		
	
	_constraints = [                   
        
        (_future_entry_date_check, 'System not allow to save with future date. !!',['Advance Date']),         
        (_check_adv_amt, 'Please Check the advance amount. Advance amount should not be allow zero,negative and greater than Order Value amount !!',['Advance amount']),       
        
       ]
       

	def entry_confirm(self,cr,uid,ids,context=None):		
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			today = date.today()
			today = str(today)
			today = datetime.strptime(today, '%Y-%m-%d')
			entry_date = rec.entry_date
			entry_date = str(entry_date)
			entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
			if entry_date < today:
				raise osv.except_osv(_('Advance Date !!'),
					_('System not allow to save with past date.!!'))	
					
			else:
				pass
			
			### Sequence Number Generation  ###
			
			if rec.name == '' or rec.name == False:
				seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.customer.advance')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_obj_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_obj_id[0],seq_rec.code,rec.entry_date))
				entry_name = cr.fetchone();
				entry_name = entry_name[0]
			else:
				entry_name = rec.name		
			
			self.write(cr, uid, ids, {'name':entry_name,'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		
		return True
		
	def entry_approve(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
		
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True
		
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def create(self, cr, uid, vals, context=None):
		return super(kg_customer_advance, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_customer_advance, self).write(cr, uid, ids, vals, context)
		
	_sql_constraints = [
	
		('name', 'unique(name)', 'No must be Unique !!'),
	]	
	
kg_customer_advance()


class ch_cus_advance_line(osv.osv):

	_name = "ch.cus.advance.line"
	_description = "Advance History"
	
	_columns = {
	
		### Basic Info
		
		'header_id':fields.many2one('kg.customer.advance', 'Advance', required=1, ondelete='cascade'),
		'remark': fields.text('Remarks'),
		'active': fields.boolean('Active'),			
		
		### Module Requirement
		'advance_no':fields.char('Advance No',readonly=True),
		'advance_date':fields.date('Advance Date'),		
		'order_no': fields.char('Order NO',readonly=True),
		'advance_amt': fields.float('Advance Amount',required=True),		
		'adjusted_amt': fields.float('Adjusted Amount',readonly=True),		
		'balance_amt': fields.float('Balance Amount',readonly=True),		
		
		## Child Tables Declaration 			
		
	}
		
	_defaults = {
	
		'active': True,
		
	}
		
ch_cus_advance_line()
