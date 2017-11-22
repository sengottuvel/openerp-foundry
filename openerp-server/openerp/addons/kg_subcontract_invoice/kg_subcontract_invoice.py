from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import base64
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')


	
	
	
	
ORDER_PRIORITY = [
  ('1','MS NC'),
   ('2','Break down'),
   ('3','Emergency'),
   ('4','Service'),
   ('5','FDY-NC'),
   ('6','Spare'),
   ('7','Urgent'),
   ('8','Normal'),
  
]

ORDER_CATEGORY = [
   ('pump','Pump'),
   ('spare','Spare'),
   ('pump_spare','Pump and Spare'),
   ('service','Service'),
   ('project','Project')
]

	


class kg_subcontract_invoice(osv.osv):

	_name = "kg.subcontract.invoice"
	_description = "Subcontract Invoice"
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
				'additional_charges':0.0,
			}
			tax_amt = discount_value = final_other_charges = advance_net_amt = 0.00
			total_value_amt = 0.00
			for line in order.line_ids:
				total_value_amt += line.total_value
			for item in order.line_ids_a:				
				final_other_charges += item.expense_amt
			for line in order.line_ids_b:
				advance_net_amt += line.current_adv_amt 				
			if order.discount > 0:
				discount = order.discount
			else:
				discount = (total_value_amt * order.discount_per) / 100			
			price_amt_val = total_value_amt	- discount	
			val = 0.00 
			for c in self.pool.get('account.tax').compute_all(cr, uid, order.tax_id,
				price_amt_val, 1, 1,
				 order.contractor_id)['taxes']:
				val += c.get('amount', 0.0)
				print"valvalval",val
				tax_amt = val	
			
			if order.discount_per > 0.00:					
				discount_value = (total_value_amt /100.00) * order.discount_per	
			else:
				discount_value = order.discount	
			
			res[order.id]['amount_untaxed'] = total_value_amt
			res[order.id]['total_discount'] = discount_value
			res[order.id]['amount_tax'] = tax_amt
			res[order.id]['additional_charges'] = final_other_charges
			res[order.id]['advance_amt'] = advance_net_amt
			res[order.id]['total_amt'] = final_other_charges + total_value_amt + tax_amt
			res[order.id]['amount_total'] = (final_other_charges + total_value_amt + tax_amt + order.round_off_amt) - (discount_value + advance_net_amt)
			res[order.id]['payable_amt'] = (final_other_charges + total_value_amt + tax_amt + order.round_off_amt) - (discount_value + advance_net_amt)
		return res	
	_columns = {
	
		## Version 0.1
	
		## Basic Info
				
		'name': fields.char('Invoice No', size=24,select=True,readonly=True),
		'entry_date': fields.date('Invoice Date',required=True),		
		'note': fields.text('Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled'),('approved','AC ACK Pending'),('done','AC ACK Done')],'Status', readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_sms': fields.boolean('SMS Notification'),
		'flag_email': fields.boolean('Email Notification'),
		'flag_spl_approve': fields.boolean('Special Approval'),
		'narration': fields.char('Narration'),	
		
		### Entry Info ####
			
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),	
		'active': fields.boolean('Active'),	
		'crt_date': fields.datetime('Creation Date',readonly=True),
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
		
		'contractor_id': fields.many2one('res.partner','Subcontractor',required=True,domain="[('contractor','=','t'),('partner_state','=','approve')]"),		
		'phone': fields.char('Phone',size=64),
		'contact_person': fields.char('Contact Person', size=128),
				
		'inward_subcontract_line_ids': fields.many2many('ch.subcontract.inward.line','m2m_invoice_details' , 'order_id', 'sc_id', 'SC Items',
			domain="[('state','in',('pending','partial')),('contractor_id','=',contractor_id)]"),	 			
		
		
		'flag_invoice': fields.boolean('Flag Invoice'),
		'division_id': fields.many2one('kg.division.master', 'Division',required=True,domain="[('state','=','approved')]"),	
		
		## Calculation process Start now 
		
		'con_invoice_no': fields.char('Contractor Invoice No', size=128,required=True),
		'invoice_date': fields.date('Contractor Invoice Date',required=True),
		'due_date': fields.date('Due Date',required=True),
		'invoice_amt': fields.float('Contractor Invoice Amount',required=True),
		'invoice_copy':fields.binary('Contractor Invoice Copy'),
		'filename':fields.char('File Name'),
		'tax_id': fields.many2many('account.tax', 'subcontract_invoice_taxes', 'invoice_id', 'tax_id', 'Taxes'),
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
		'advance_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Adjected Advance Amount(-)',multi="sums",store=True ,readonly=True),
		'round_off_amt': fields.float('Round off(+/-)'),
				
		##Accounts Process
		'balance_receivable': fields.float('Balance Receivable'),		
		'accounts_state': fields.selection([('pending','Pending'),('paid','Paid')],'Accounts State', readonly=True),
		## Child Tables Declaration 
				
		'line_ids': fields.one2many('ch.subcontract.invoice.line', 'header_id', "Line Details"),
		'line_ids_a': fields.one2many('ch.subcontract.invoice.expense.track','header_id',"Expense Track"),
		'line_ids_b': fields.one2many('ch.ms.advance.details','header_id',"Advance Details"),
		'line_ids_c': fields.one2many('ch.sc.kg.debit.note','header_id',"Debit Details"),
				
	}
		
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_subcontract_invoice', context=c),			
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',		
		'active': True,
		'entry_mode': 'manual',	
		'accounts_state': 'pending',	
		'flag_sms': False,		
		'flag_email': False,		
		'flag_spl_approve': False,	
		'discount_flag': False,
		'discount_per_flag': False,	
		
	}
	
	
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
	
	
	def button_dummy(self, cr, uid, ids, context=None):
		return True
	
		
	
	
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
			
	
	_constraints = [				  
		
		#~ (_future_entry_date_check, 'System not allow to save with future and past date. !!',['Invoice Date']),   
		
	   ]
	   
	def onchange_contractor(self, cr, uid, ids, contractor_id):
		if contractor_id:
			contractor_rec = self.pool.get('res.partner').browse(cr, uid, contractor_id)
		return {'value': {'contact_person':contractor_rec.contact_person,'phone':contractor_rec.phone  }}
		
	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		invoice_line_obj = self.pool.get('ch.subcontract.invoice.line')
			
		del_sql = """ delete from ch_subcontract_invoice_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		for item in entry.inward_subcontract_line_ids:			
			
			
			vals = {
			
				'header_id': entry.id,
				'sc_id':item.sc_id.id,
				'qty':item.qty,								
				'actual_qty':item.actual_qty,		
				'wo_line_id':item.wo_line_id.id,		
				'com_weight':item.com_weight,					
				'sc_inward_line_id':item.id,	
				'operation_id':[(6, 0, [x.id for x in item.com_operation_id])],
				
			}
			
			in_line_id = invoice_line_obj.create(cr, uid,vals)		
			
			
		self.write(cr, uid, ids, {'flag_invoice': True})
		
			
		return True
	   

	def entry_confirm(self,cr,uid,ids,context=None):
		
		entry = self.browse(cr,uid,ids[0])		
		final_other_charges = 0.00
		for item in entry.line_ids_a:				
			final_other_charges += item.expense_amt
		### Sequence Number Generation  ###
		if len(entry.line_ids) == 0:		
			raise osv.except_osv(_('Invoice details is must !!'),
				_('Enter the proceed button!!'))
		if entry.state == 'draft':
			sc_inward_line_obj = self.pool.get('ch.subcontract.inward.line')
			if (entry.invoice_amt + final_other_charges) > entry.amount_total:
				raise osv.except_osv(_('Invoice Amount Exceed!!'),
					_('System not allow to Invoice Amount grether than Net Amount !!'))
			if (entry.invoice_amt + final_other_charges) != entry.amount_total:		
				raise osv.except_osv(_('Invoice Amount !!'),
					_('System allow to Invoice Amount is Equal to Net amount !!'))	
			for line_item in entry.line_ids:								
				if line_item.qty == 0:
					raise osv.except_osv(_('Warning!'),
						_('System not allow to save Zero values !!'))		
		
				
				if (line_item.sc_inward_line_id.sc_invoice_qty + line_item.qty) > line_item.sc_inward_line_id.qty:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to invoice Qty Exceed !!'))						
									
									
				if (line_item.sc_inward_line_id.sc_invoice_qty + line_item.qty) == line_item.sc_inward_line_id.qty:
					invoice_state = 'done'
				if (line_item.sc_inward_line_id.sc_invoice_qty + line_item.qty) < line_item.sc_inward_line_id.qty:
					invoice_state = 'partial'			
				
										
				sc_inward_line_obj.write(cr, uid, line_item.sc_inward_line_id.id, 
							{'sc_invoice_qty': line_item.sc_inward_line_id.sc_invoice_qty + line_item.qty,'state': invoice_state,'pending_qty':line_item.sc_inward_line_id.pending_qty - line_item.qty})				
				
				
												
			if entry.name == '' or entry.name == False:
				sc_invoice_name = ''	
				sc_invoice_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.invoice')])
				rec = self.pool.get('ir.sequence').browse(cr,uid,sc_invoice_seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(sc_invoice_seq_id[0],rec.code,entry.entry_date))
				sc_invoice_name = cr.fetchone();
				sc_invoice_name = sc_invoice_name[0]				
			else:
				sc_invoice_name = entry.name		
											
			self.write(cr, uid, ids, {'state': 'confirmed','name':sc_invoice_name,'confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})								
								
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
			## Advance code added start ##
			adjusted_amt = 0.00
			balance_amt = 0.00
			cus_adv_obj = self.pool.get('kg.subcontract.advance')			
			cus_adv_inv_obj = self.pool.get('ch.ms.advance.details')							
			for line in rec.line_ids_b:	
				print"line.order_id",line.order_id
				adv_ids = self.pool.get('kg.subcontract.advance').search(cr, uid, [('wo_id','=',line.order_id.id)])
				print"adv_ids",adv_ids							
				adv_rec = self.pool.get('kg.subcontract.advance').browse(cr, uid,adv_ids[0])				
				adjusted_amt = adv_rec.adjusted_amt + line.current_adv_amt 
				balance_amt = line.current_adv_amt - adjusted_amt
				cus_adv_obj.write(cr, uid, line.sub_advance_id.id, {'adjusted_amt': adjusted_amt,'balance_amt':balance_amt})	
			
			## Advance code added end ##
		
			
			total_value_amt = 0.00
			for line in rec.line_ids:
				total_value_amt += line.total_value	
			self.write(cr, uid, ids, {'balance_receivable':rec.amount_total,'state': 'done','done_user_id': uid, 'done_date': time.strftime('%Y-%m-%d %H:%M:%S')})			
			
			## Account Posting Process Start
			vou_obj = self.pool.get('account.voucher')				
			move_vals = {
						'name':rec.name,
						'journal_id':journal_rec.id,
						'narration':rec.narration,
						'source_id':rec.id,
						'date':rec.entry_date,
						'division_id':rec.division_id.id,
						'trans_type':'FI',
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
			tax_sql = """ select sub_query.acc_col_id,sum(sub_query.debit) as debit
							from (
							select 
							ac_tax.account_collected_id as acc_col_id,
							sum((line_exp.amount * ac_tax.amount)) as debit
							from 
							subcontract_invoice_expense_taxe line_tax 
							left join ch_subcontract_invoice_expense_track line_exp on(line_exp.id=line_tax.invoice_id)
							left join account_tax ac_tax on(ac_tax.id=line_tax.tax_id)
							left join kg_subcontract_invoice inv on(inv.id=line_exp.header_id)

							where line_exp.header_id = %s
							group by 1

							union all

							select 
							ac_tax.account_collected_id as acc_col_id,
							sum(((inv.amount_untaxed - inv.total_discount) * ac_tax.amount)) as debit
							from 
							subcontract_invoice_taxes line_tax 

							left join kg_subcontract_invoice inv on(inv.id=line_tax.invoice_id)
							left join account_tax ac_tax on(ac_tax.id=line_tax.tax_id)			

							where inv.id = %s
							group by 1) as sub_query

							group by 1"""%(rec.id,rec.id)
			cr.execute(tax_sql)		
			data = cr.dictfetchall()
			for vals in data:			
				if vals['acc_col_id'] is None:
					raise osv.except_osv(_('Account Configuration Warning !!'),
							_('Tax account should be configured !!'))
				move_line_vals = {
					'move_id': move_id,
					'account_id': vals['acc_col_id'],
					'credit': 0.00,
					'debit': vals['debit'],
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
		else:
			pass	
		
	
	def load_advance(self, cr, uid, ids,context=None):
		invoice_rec = self.browse(cr,uid,ids[0])
		cus_adv_obj = self.pool.get('kg.subcontract.advance')		
		cus_inadv_obj = self.pool.get('ch.ms.advance.details')	
		del_sql = """delete from ch_ms_advance_details where header_id=%s"""%(ids[0])
		cr.execute(del_sql)
		for item in [x.id for x in invoice_rec.inward_subcontract_line_ids]:			
			work_rec_obj = self.pool.get('ch.subcontract.inward.line').browse(cr,uid,item)							
			adv_search = self.pool.get('kg.subcontract.advance').search(cr, uid, [('wo_id','=',work_rec_obj.wo_line_id.header_id.id)])
			cr.execute(""" select * from kg_subcontract_advance where wo_id = %s and balance_amt > 0 and state='confirmed'""" %(work_rec_obj.wo_line_id.header_id.id))
			adv_data = cr.dictfetchall()			
			for adv in adv_data:
				print"adv['order_id']0",adv['wo_id']
				cus_inadv_obj.create(cr,uid,{
					'order_id' : adv['wo_id'],
					'sub_advance_id' : adv['id'],
					'sub_advance_date' : adv['entry_date'],
					'tot_advance_amt' : adv['advance_amt'],
					'balance_amt' : adv['balance_amt'],
					'current_adv_amt' : 0.0,
					'header_id' : invoice_rec.id,
					})
				
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
		return super(kg_subcontract_invoice, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_subcontract_invoice, self).write(cr, uid, ids, vals, context)
	
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_code = str(rec.name)		
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
			
		url = 'http://192.168.1.7/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&Subcontract_Invoice='+rec_code


		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
		
	_sql_constraints = [
	
		('name', 'unique(name)', 'No must be Unique !!'),
	]	
	
kg_subcontract_invoice()


class ch_subcontract_invoice_line(osv.osv):

	_name = "ch.subcontract.invoice.line"
	_description = "Subcontract Invoice Line"
	
	def _get_oper_value(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		total_value = 0.00
		value = 0.00
		for entry in self.browse(cr, uid, ids, context=context):
			for line in entry.wo_op_id:
				print"entry.qty",entry.qty
				print"line.op_rate",line.op_rate
				total_value= entry.qty * line.op_rate * entry.com_weight			
				value += total_value
			print"total_value",value
			result[entry.id] = value
		return result
	
	_columns = {
	
		### Basic Info
		
		'header_id':fields.many2one('kg.subcontract.invoice', 'Transaction', required=1, ondelete='cascade'),
		'remark': fields.text('Remarks'),
		'active': fields.boolean('Active'),			
		
		### Module Requirement Fields
		'sc_id': fields.many2one('kg.subcontract.process','Subcontractor List Id'),
		'sc_inward_line_id': fields.many2one('ch.subcontract.inward.line','Subcontractor Inward List Id'),
		'ms_id': fields.related('sc_id','ms_id', type='many2one', relation='kg.machineshop', string='MS Id', store=True, readonly=True),
		'production_id': fields.related('sc_id','production_id', type='many2one', relation='kg.production', string='Production No.', store=True, readonly=True),
		'position_id': fields.related('sc_id','position_id', type='many2one', relation='kg.position.number', string='Position No.', store=True, readonly=True),
		'order_id': fields.related('sc_id','order_id', type='many2one', relation='kg.work.order', string='Work Order', store=True, readonly=True),
		'order_line_id': fields.related('sc_id','order_line_id', type='many2one', relation='ch.work.order.details', string='Order Line', store=True, readonly=True),
		'order_no': fields.related('sc_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('sc_id','order_delivery_date', type='date', string='Delivery Date', store=True, readonly=True),

		'order_category': fields.related('sc_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.related('sc_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		'pump_model_id': fields.related('sc_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('sc_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_code': fields.related('sc_id','pattern_code', type='char', string='Pattern Code', store=True, readonly=True),
		'pattern_name': fields.related('sc_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'item_code': fields.related('sc_id','item_code', type='char', string='Item Code', store=True, readonly=True),
		'item_name': fields.related('sc_id','item_name', type='char', string='Item Name', store=True, readonly=True),
		'moc_id': fields.related('sc_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'ms_type': fields.related('sc_id','ms_type', type='selection', selection=[('foundry_item','Foundry Item'),('ms_item','MS Item')], string='Item Type', store=True, readonly=True),
		'wo_line_id': fields.many2one('ch.subcontract.wo.line','Subcontract Workorder Id'),
		
		'operation_id': fields.many2many('ch.kg.position.number', 'm2m_invoice_operation_details', 'in_operation_id', 'in_sub_id','Operation', domain="[('header_id','=',position_id)]"),
		
		'actual_qty': fields.integer('Actual Qty',readonly=True),
		'qty': fields.integer('Quantity'),
		'value': fields.float('Unit Price'),		
		'total_value': fields.function(_get_oper_value, string='Total Value', method=True, store=True, type='float'),
		'com_weight': fields.float('Completed weight'),				
		
		'state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')],'Status', readonly=True),
		
		## Child Tables Declaration 
		'wo_op_id': fields.related('wo_line_id','line_ids', type='one2many', relation='ch.wo.operation.details', string='Operation Items'),		
		
	}
		
	_defaults = {
	
		'active': True,
		'state': 'pending',
		
	}
	def onchange_total_value(self, cr, uid, ids, qty,value):
		if qty:			
			total_value = qty * value
		return {'value': {'total_value': total_value}}
		
ch_subcontract_invoice_line()


class ch_subcontract_invoice_expense_track(osv.osv):

	_name = "ch.subcontract.invoice.expense.track"
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
		
		'header_id': fields.many2one('kg.subcontract.invoice', 'Expense Track'),
		'name': fields.char('Number', size=128, select=True,readonly=False),
		'date': fields.date('Creation Date'),
		'amount': fields.float('Amount'),		
		'tax_id': fields.many2many('account.tax', 'subcontract_invoice_expense_taxe', 'invoice_id', 'tax_id', 'Tax'),
		'company_id': fields.many2one('res.company', 'Company Name'),
		'description': fields.char('Description'),
		'remark': fields.text('Remarks'),		
		'expense_amt': fields.function(_get_total_amt, string='Total Amount',digits=(16,2), method=True, store=True, type='float'),		
		'expense': fields.many2one('kg.expense.master','Expense'),
		
	}
	
	_defaults = {
		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'ch.subcontract.invoice.expense.track', context=c),
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
	
		}	
	
ch_subcontract_invoice_expense_track()



class ch_ms_advance_details(osv.osv):

	_name = "ch.ms.advance.details"
	_description = "MS Subcontract Advance Details"
	_columns = {
	
		'header_id':fields.many2one('kg.subcontract.invoice', 'Invoice advance', ondelete='cascade'),
		'sub_advance_id' : fields.many2one('kg.subcontract.advance', 'Advance No', readonly=True),
		'sub_advance_date': fields.date('Advance Date'),
		'sub_advance_line_id' : fields.many2one('ch.subcontract.advance.line', 'Contractor Advance Line', readonly=True),		
		'order_id': fields.many2one('kg.subcontract.wo','WO No.'),		
		'order_amt': fields.float('Order Amount', readonly=True),
		'tot_advance_amt': fields.float('Advance Amount', readonly=True),
		'already_adjusted_amt': fields.float('Already Adjusted Advance Amount', readonly=True),
		'balance_amt': fields.float('Balance Advance', readonly=True),
		'current_adv_amt': fields.float('Current Adjustment Amount',required=True),
		
		
	}
	
	def _current_adv_amt(self,cr,uid,ids,context = None):
		rec = self.browse(cr,uid,ids[0])
		if rec.current_adv_amt > rec.balance_amt:
			return False
		else:
			return True
			
	_constraints = [		
			  
		
		(_current_adv_amt, 'Please Check the Current Adjustment Amount. Balance amount should be less than Current Adjustment Amount!!',['Current Adjustment Amount']),

	   ]
				
ch_ms_advance_details()

class ch_sc_kg_debit_note(osv.osv):
	
	_name = 'ch.sc.kg.debit.note'
	_description = 'This module is about the details of Debit note'
	
	_columns = {
		
		'header_id':fields.many2one('kg.subcontract.invoice','Header_id'),
		'debit_date':fields.date('Debit Note Date'),
		'subcontract_id':fields.many2one('res.partner','Subcontract',domain="[('contractor','=','t'),('partner_state','=','approve')]",readonly=True),
		'sc_invoice_no':fields.char('Subcontract Invoice No',readonly=True),
		'sc_invoice_date':fields.date('Debit Invoice Date',readonly=True),	
		'debit_amt':fields.float('Debit Note Amount'),
		
	}
	
ch_sc_kg_debit_note()


