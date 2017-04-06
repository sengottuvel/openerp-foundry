from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')


ORDER_CATEGORY = [
   ('pump','Pump'),
   ('spare','Spare'),
   ('pump_spare','Pump and Spare'),
   ('service','Service'),
   ('project','Project'),
   ('access','Accessories')
]


class kg_painting_invoice(osv.osv):

	_name = "kg.painting.invoice"
	_description = "Painting Invoice"
	_order = "entry_date desc"
	
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		
		for order in self.browse(cr, uid, ids, context=context):
			
			res[order.id] = {
				'amount_untaxed': 0.0,
				'total_discount': 0.0,
				'amount_tax': 0.0,
				'total_amt' : 0.0,
				'amount_total':0.0,
				'payable_amt':0.0,
				'order_value': 0.0,
				'total_value': 0.0,
				'additional_charges':0.0,
			}
			tax_amt = discount_value = final_other_charges = 0.00
			total_value_amt = 0.00
			for line in order.line_ids:
				total_value_amt += line.total_amt
			for item in order.line_ids_a:				
				final_other_charges += item.expense_amt
			if order.discount > 0.00:
				amt_to_per = (order.discount / (total_value_amt or 1.0 )) * 100
				kg_discount_per = order.discount_per
				tot_discount_per = amt_to_per
			else:
				tot_discount_per = order.discount_per			
			val = 0.00 
			for c in self.pool.get('account.tax').compute_all(cr, uid, order.tax_id,
				total_value_amt * (1-(tot_discount_per or 0.0)/100.0), 1, 1,
				 order.contractor_id)['taxes']:
				val += c.get('amount', 0.0)
				print"valvalval",val
				tax_amt = val	
			
			if order.discount_per > 0.00:					
				discount_value = (total_value_amt /100.00) * order.discount_per	
			else:
				discount_value = order.discount
				
			cr.execute(''' select sum(total_amt) from ch_painting_invoice_line_details where header_id = %s ''',[order.id])
			wo_value = cr.fetchone()
			if wo_value[0] == None:
				wo_value = 0.00
			else:
				wo_value= wo_value[0]
			total_value =  wo_value
			res[order.id]['order_value'] = wo_value
			res[order.id]['total_value'] = total_value + final_other_charges
			res[order.id]['additional_charges'] = final_other_charges
			res[order.id]['amount_untaxed'] = total_value_amt
			res[order.id]['total_discount'] = discount_value
			res[order.id]['amount_tax'] = tax_amt
			res[order.id]['total_amt'] = final_other_charges + total_value_amt + tax_amt
			res[order.id]['amount_total'] = (final_other_charges + total_value_amt + tax_amt + order.round_off_amt) - discount_value
			res[order.id]['payable_amt'] = (final_other_charges + total_value_amt + tax_amt + order.round_off_amt) - discount_value
		return res	
	
	
	_columns = {
	
		## Version 0.1
	
		## Basic Info
				
		'name': fields.char('Invoice No', size=24,select=True,readonly=True),
		'entry_date': fields.date('Invoice Date',required=True),		
		'note': fields.text('Notes'),		
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_sms': fields.boolean('SMS Notification'),
		'flag_email': fields.boolean('Email Notification'),
		'flag_spl_approve': fields.boolean('Special Approval'),
		'narration': fields.char('Narration'),	
		
		### Entry Info ####
			
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),	
		'active': fields.boolean('Active'),	
		'crt_date': fields.datetime('Created Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),		
		'ap_rej_date': fields.datetime('Approved Date', readonly=True),
		'done_date': fields.datetime('Done Date', readonly=True),
		'done_user_id': fields.many2one('res.users', 'Done By', readonly=True),	
		'ap_rej_user_id': fields.many2one('res.users', 'Approved By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),	
		
		'cancel_remark': fields.text('Cancel'),			
		'reject_remark': fields.text('Reject'),			
		
		## Module Requirement Info	
		
		'contractor_id': fields.many2one('res.partner','Subcontractor',required=True),
		'date_from': fields.date('Date From',required=True),	
		'date_to': fields.date('Date To',required=True),	
		'phone': fields.char('Phone',size=64),
		'contact_person': fields.char('Contact Person', size=128),			
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled'),('approved','AC ACK Pending'),('done','AC ACK Done')],'Status', readonly=True),
		'flag_invoice': fields.boolean('Flag Invoice'),
		#~ 'order_value': fields.function(_amount_all, string='Work Value', method=True, store=True, type='float'),
		'order_value': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Work Value',store=True,multi="sums",help="Work Value"),
		'additional_amount': fields.float('Additional Amount'),		
		#~ 'total_value': fields.function(_amount_all, string='Total Value', method=True, store=True, type='float'),
		'total_value': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Value',store=True,multi="sums",help="Total Value"),
		'division_id': fields.many2one('kg.division.master', 'Division',required=True),
		## Calculation process Start now 
		
		'con_invoice_no': fields.char('Contractor Invoice No', size=128,required=True),
		'invoice_date': fields.date('Contractor Invoice Date',required=True),
		'due_date': fields.date('Due Date',required=True),
		'invoice_amt': fields.float('Contractor Invoice Amount',required=True),
		'invoice_copy':fields.binary('Contractor Invoice Copy'),
		'tax_id': fields.many2many('account.tax', 'painting_invoice_taxes', 'invoice_id', 'tax_id', 'Taxes'),
		'discount': fields.float('Discount Amount'),	
		'discount_per': fields.float('Discount(%)'),
		'discount_flag': fields.boolean('Discount Flag'),
		'discount_per_flag': fields.boolean('Discount Amount Flag'),
		
		# Invoice Total and Tax amount calculation	
		'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',store=True,multi="sums",help="Untaxed Amount"),
		'total_discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Discount Amount(-)',store=True,multi="sums",help="Discount Amount"),
		'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax Amount',store=True,multi="sums",help="Tax Amount"),
		'total_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Amount',store=True,multi="sums",help="Total Amount"),
		'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',store=True,multi="sums",help="Net Amount"),
		'payable_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Payable Amount',store=True,multi="sums",help="Payable Amount"),
		'additional_charges': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Additional Charges',store=True,multi="sums",help="Additional Charges"),
		'round_off_amt': fields.float('Round off(+/-)'),		
		
		## Child Tables Declaration 
				
		'line_ids': fields.one2many('ch.painting.invoice.line.details', 'header_id', "Line Details"),
		'line_ids_a': fields.one2many('ch.painting.invoice.expense.track','header_id',"Expense Track"),
		
				
	}
		
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_painting_invoice', context=c),			
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',		
		'active': True,
		'entry_mode': 'manual',		
		'flag_sms': False,		
		'flag_email': False,		
		'flag_spl_approve': False,	
		'discount_flag': False,
		'discount_per_flag': False,		
		
	}
	
	#~ def onchange_invoice_amt(self,cr,uid,ids,invoice_amt,discount_per,context = None):
		#~ discount = 0.00
		#~ if invoice_amt >0.00 and discount_per > 0.00:
			#~ discount = (invoice_amt * discount_per) / 100.0
		#~ return {'value':{'discount':(round(discount,2))}}
		
	def onchange_discount_value(self, cr, uid, ids, invoice_amt,discount_per):		
		discount_value =  invoice_amt * discount_per / 100.00
		if discount_per:
			return {'value': {'discount_flag':True }}
		else:
			return {'value': {'discount_flag':False }}
			
	def onchange_discount_percent(self,cr,uid,ids,invoice_amt,discount):		
		if discount:
			discount = discount + 0.00
			amt_to_per = (discount / (invoice_amt or 1.0 )) * 100.00
			return {'value': {'discount_per_flag':True}}
		else:
			return {'value': {'discount_per_flag':False}}	
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		entry_date = rec.entry_date
		entry_date = str(entry_date)
		entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
		if entry_date > today or entry_date < today:
			return False
		return True
		
	def _future_date_to_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		date_to = rec.date_to
		date_to = str(date_to)
		date_to = datetime.strptime(date_to, '%Y-%m-%d')
		date_from = rec.date_from
		date_from = str(date_from)
		date_from = datetime.strptime(date_from, '%Y-%m-%d')
		if date_to > today:
			return False		
		if date_from > today:
			return False
		return True
	def _future_date_from_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		date_to = rec.date_to
		date_to = str(date_to)
		date_to = datetime.strptime(date_to, '%Y-%m-%d')
		date_from = rec.date_from
		date_from = str(date_from)
		date_from = datetime.strptime(date_from, '%Y-%m-%d')
		if date_from > date_to:
			return False			
		return True
		
	def button_dummy(self, cr, uid, ids, context=None):
		return True
		
	def _same_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		cr.execute(""" select id,date_from,date_to from kg_painting_invoice where  id != %s and contractor_id = %s and
						(date_from = '%s'
						or date_to = '%s'
						or '%s' between date_from and date_to
						or '%s' between date_from and date_to)
								
						"""%(rec.id,rec.contractor_id.id,rec.date_from,rec.date_to,rec.date_from,rec.date_to))
		
		date_id = cr.dictfetchall();		
		if date_id:
			return False
			
		return True
			
			
	
	_constraints = [		
			  
		
		(_future_date_from_check, 'System not allow to greater than Data from!!',['Date To']),	   
		#~ (_future_entry_date_check, 'System not allow to save with future and past date. !!',['Invoice Date']),	   
		(_future_date_to_check, 'System not allow to save with future and past date. !!',['Date To and Date From']),	   
		(_same_date_check, 'System not allow to Same date.Already avaliable in this date !!',['Date From and Date To']),	   
		
	   ]
	   
	def onchange_contractor(self, cr, uid, ids, contractor_id):
		if contractor_id:
			contractor_rec = self.pool.get('res.partner').browse(cr, uid, contractor_id)
		return {'value': {'contact_person':contractor_rec.contact_person,'phone':contractor_rec.phone  }}
		
	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		
		invoice_line_details_obj = self.pool.get('ch.painting.invoice.line.details')
		
		del_details_sql = """ delete from ch_painting_invoice_line_details where header_id=%s """ %(ids[0])
		cr.execute(del_details_sql)
		
		cr.execute(""" (select id,pump_model_id,entry_date from kg_painting where entry_date >= '%s' and entry_date <= '%s'
						and painting_state = 'completed' and contractor_id = %s)
		"""%(entry.date_from,entry.date_to,entry.contractor_id.id))
		
		painting_ids = cr.dictfetchall();
		
		for painting_item in painting_ids:
			
			vals = {
			
				'header_id': entry.id,
				'painting_id':painting_item['id'],
				'qty':1,
				'pump_model_id':painting_item['pump_model_id'],						
				'date':painting_item['entry_date']							
				
			}
			
			invoice_line_id = invoice_line_details_obj.create(cr, uid,vals)
		
		return True
	   

	def entry_confirm(self,cr,uid,ids,context=None):
		
		entry = self.browse(cr,uid,ids[0])
		final_other_charges = 0.00
		for item in entry.line_ids_a:				
			final_other_charges += item.expense_amt	
		if len(entry.line_ids) == 0:		
			raise osv.except_osv(_('Invoice details is must !!'),
				_('Enter the proceed button!!'))
		if entry.state == 'draft':	
			print"entry.invoice_amt",entry.invoice_amt
			print"final_other_charges",final_other_charges
			print"entry.amount_total",entry.amount_total
			if (entry.invoice_amt + final_other_charges) > entry.amount_total:
				raise osv.except_osv(_('Invoice Amount Exceed!!'),
					_('System not allow to Invoice Amount grether than Net Amount !!'))
			if (entry.invoice_amt + final_other_charges) != entry.amount_total:		
				raise osv.except_osv(_('Invoice Amount !!'),
					_('System allow to Invoice Amount is Equal to Net amount !!'))									
			if entry.additional_amount > 0:
				self.write(cr, uid, ids, {'flag_spl_approve': True})		
				
			
			### Sequence Number Generation  ###									
			if entry.name == '' or entry.name == False:
				painting_invoice_name = ''	
				painting_invoice_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.painting.invoice')])
				rec = self.pool.get('ir.sequence').browse(cr,uid,painting_invoice_seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(painting_invoice_seq_id[0],rec.code,entry.entry_date))
				painting_invoice_name = cr.fetchone();
				painting_invoice_name = painting_invoice_name[0]				
			else:
				painting_invoice_name = entry.name		
											
			self.write(cr, uid, ids, {'state': 'confirmed','name':painting_invoice_name,'confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})								
									
		return True
		
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True
		
	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			if rec.reject_remark:
				self.write(cr, uid, ids, {'state': 'confirmed','update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Reject remark is must !!'),
					_('Enter the remarks in Reject remarks field !!'))
			return True
		
	def entry_approved(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		final_other_charges = 0.00
		for item in entry.line_ids_a:				
			final_other_charges += item.expense_amt	
		if len(entry.line_ids) == 0:		
			raise osv.except_osv(_('Invoice details is must !!'),
				_('Enter the proceed button!!'))
		if entry.state == 'confirmed':				
			if (entry.invoice_amt + final_other_charges) > entry.amount_total:
				raise osv.except_osv(_('Invoice Amount Exceed!!'),
					_('System not allow to Invoice Amount grether than Net Amount !!'))
			if (entry.invoice_amt + final_other_charges) != entry.amount_total:		
				raise osv.except_osv(_('Invoice Amount !!'),
					_('System allow to Invoice Amount is Equal to Net amount !!'))	
		
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass		
		return True
		
	def entry_accept(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		journal_obj = self.pool.get('account.journal')
		journal_ids = self.pool.get('account.journal').search(cr,uid,[('type','=','purchase')])	
		if journal_ids == []:
			raise osv.except_osv(_('Book Configuration Warning !!'),
				_('Type is purchase book should be created !!'))		
		journal_rec = self.pool.get('account.journal').browse(cr,uid,journal_ids[0])
		if rec.state == 'approved':
			total_value_amt = 0.00
			for line in rec.line_ids:
				total_value_amt += line.total_amt			
				self.write(cr, uid, ids, {'state': 'done','done_user_id': uid, 'done_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				pass
							
			## Account Posting Process Start
			vou_obj = self.pool.get('account.voucher')				
			move_vals = {
						'name':rec.name,
						'journal_id':journal_rec.id,
						'narration':rec.narration,
						'source_id':rec.id,
						'date':rec.entry_date,
						'division_id':rec.division_id.id,
						'trans_type':'PI',
						}			
			move_id = vou_obj.create_account_move(cr,uid,move_vals)	
			if rec.contractor_id:
				account_id = rec.contractor_id.property_account_payable.id
				if not account_id:
					raise osv.except_osv(_('Contractor Configuration Warning !!'),
						_('Contractor account should be configured !!'))
				credit = rec.amount_total
				debit = 0.00
				move_line_vals = {
						'move_id': move_id,
						'account_id': account_id,
						'credit': credit,
						'debit': debit,					
						'journal_id': journal_rec.id,						
						'date': rec.entry_date,
						'name': rec.name,
						}
				move_line_id = vou_obj.create_account_move_line(cr,uid,move_line_vals)		
			for expense in rec.line_ids_a:
				ex_account_id = expense.expense.account_id.id			
				tax_obj = self.pool.get('account.tax')
				taxes = tax_obj.compute_all(cr, uid, expense.tax_id, expense.amount, 1, 1, partner=rec.contractor_id)			
				for tax in taxes['taxes']:
					print "taxtax",tax
					tax_rec = self.pool.get('account.tax').browse(cr,uid,tax['id'])				
					credit = 0.00
					debit = ((tax['amount']))					
					tax_account = tax['account_collected_id']				
					if not tax_account:
						raise osv.except_osv(_('Account Configuration Warning !!'),
							_('Tax account should be configured !!'))
					move_line_vals = {
						'move_id': move_id,
						'account_id': tax_account,
						'credit': credit,
						'debit': debit,					
						'journal_id': journal_rec.id,						
						'date': rec.entry_date,
						'name': rec.name,
						}
					move_line_id = vou_obj.create_account_move_line(cr,uid,move_line_vals)			
				if not ex_account_id:
					raise osv.except_osv(_('Expense Configuration Warning !!'),
						_('Expense account should be configured !!'))
				move_line_vals = {
						'move_id': move_id,
						'account_id': ex_account_id,
						'credit': 0.00,
						'debit': expense.amount,				
						'journal_id': journal_rec.id,						
						'date': rec.entry_date,
						'name': rec.name,
						}
				
				move_line_id = vou_obj.create_account_move_line(cr,uid,move_line_vals)		
			
			discount = 0.00
			if rec.tax_id:				
				if rec.discount > 0:
					discount = rec.discount
				else:
					discount = (total_value_amt * rec.discount_per) / 100			
				price_amt_val = total_value_amt	- discount			
				tax_obj = self.pool.get('account.tax')
				taxes = tax_obj.compute_all(cr, uid, rec.tax_id, price_amt_val, 1, product=rec.contractor_id, partner=rec.contractor_id)			
				for tax in taxes['taxes']:
					tax_rec = self.pool.get('account.tax').browse(cr,uid,tax['id'])
					credit = 0.00
					debit = ((tax['amount']))					
					tax_account = tax['account_collected_id']				
					if not tax_account:
						raise osv.except_osv(_('Account Configuration Warning !!'),
							_('Tax account should be configured !!'))
					move_line_vals = {
						'move_id': move_id,
						'account_id': tax_account,
						'credit': credit,
						'debit': debit,					
						'journal_id': journal_rec.id,						
						'date': rec.entry_date,
						'name': rec.name,
						}
					move_line_id = vou_obj.create_account_move_line(cr,uid,move_line_vals)
			
			if rec.amount_untaxed > 0:
				discount = 0.00
				if rec.discount > 0:
					discount = rec.discount
				else:
					discount = (total_value_amt * rec.discount_per) / 100
				account_ids = self.pool.get('account.account').search(cr,uid,[('code','=','CON INV')])	
				if account_ids == []:
					raise osv.except_osv(_('Account Configuration Warning !!'),
						_('code name is CON INV account should be created !!'))		
				account_rec = self.pool.get('account.account').browse(cr,uid,account_ids[0])
				account_id = account_rec.id			
				if not account_id:
					raise osv.except_osv(_('Invoice Configuration Warning !!'),
						_('Invoice account should be configured !!'))
				credit = 0.00
				debit = (rec.amount_untaxed + rec.round_off_amt) - discount
				move_line_vals = {
						'move_id': move_id,
						'account_id': account_id,
						'credit': credit,
						'debit': debit,					
						'journal_id': journal_rec.id,						
						'date': rec.entry_date,
						'name': rec.name,
						}
				
				move_line_id = vou_obj.create_account_move_line(cr,uid,move_line_vals)			

				
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
		return super(kg_painting_invoice, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_painting_invoice, self).write(cr, uid, ids, vals, context)
		
	_sql_constraints = [
	
		('name', 'unique(name)', 'No must be Unique !!'),
	]	
	
kg_painting_invoice()


class ch_painting_invoice_line_details(osv.osv):

	_name = "ch.painting.invoice.line.details"
	_description = "Painting Invoice Line details"
	
	def _get_total_value(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		
		for entry in self.browse(cr, uid, ids, context=context):
			total_value = entry.qty * entry.each_rate
			result[entry.id] = total_value
		return result
	
	_columns = {
	
		### Basic Info
		
		'header_id':fields.many2one('kg.painting.invoice', 'Transaction', required=1, ondelete='cascade'),
		'remark': fields.text('Remarks'),
		'active': fields.boolean('Active'),			
		
		### Module Requirement Fields
		'date': fields.date('Date',required=True),
		'painting_id': fields.many2one('kg.painting','Painting Id'),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model',required=True),
		'qty': fields.integer('Quantity',required=True),
		'each_rate': fields.related('pump_model_id','painting_cost', type='float', string='Each Rate', store=True),		
		'total_amt': fields.function(_get_total_value, string='Total', method=True, store=True, type='float'),
		## Child Tables Declaration 				
		
	}
		
	_defaults = {
	
		'active': True,
		
		
	}
	
		
ch_painting_invoice_line_details()


class ch_painting_invoice_expense_track(osv.osv):

	_name = "ch.painting.invoice.expense.track"
	_description = "Expense track"
	
	
	def _get_total_amt(self, cr, uid, ids, field_name, arg, context=None):
		result = {}	
		val = 0.00
		total_value = 0.00
		tot_discount_per = 0.00
		for entry in self.browse(cr, uid, ids, context=context):
			for c in self.pool.get('account.tax').compute_all(cr, uid, entry.tax_id,
				entry.amount * (1-(tot_discount_per or 0.0)/100.0), 1, 1,
				entry.expense)['taxes']:
				val += c.get('amount', 0.0)								
			result[entry.id] = val + entry.amount
		return result
	
	_columns = {
		
		'header_id': fields.many2one('kg.painting.invoice', 'Expense Track'),
		'name': fields.char('Number', size=128, select=True,readonly=False),
		'date': fields.date('Creation Date'),
		'amount': fields.float('Amount'),		
		'tax_id': fields.many2many('account.tax', 'painting_invoice_expense_taxe', 'invoice_id', 'tax_id', 'Tax'),
		'company_id': fields.many2one('res.company', 'Company Name'),
		'description': fields.char('Description'),
		'remark': fields.text('Remarks'),		
		'expense_amt': fields.function(_get_total_amt, string='Total Amount',digits=(16,2), method=True, store=True, type='float'),		
		'expense': fields.many2one('kg.expense.master','Expense'),
		
	}
	
	_defaults = {
		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'ch.painting.invoice.expense.track', context=c),
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
	
		}	
	
ch_painting_invoice_expense_track()




