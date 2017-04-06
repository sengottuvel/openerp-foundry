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


class kg_foundry_invoice(osv.osv):

	_name = "kg.foundry.invoice"
	_description = "Foundry Invoice"
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
			tax_amt = discount_value = final_other_charges = 0.00
			total_value_amt = 0.00
			for line in order.line_ids:
				total_value_amt += line.total_value
			for item in order.line_ids_b:				
				final_other_charges += item.expense_amt
			
			
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
		'division_id': fields.many2one('kg.division.master', 'Division',required=True),
		
		## Calculation process Start now 
		
		'con_invoice_no': fields.char('Contractor Invoice No', size=128,required=True),
		'invoice_date': fields.date('Contractor Invoice Date',required=True),
		'due_date': fields.date('Due Date',required=True),
		'invoice_amt': fields.float('Contractor Invoice Amount',required=True),
		'invoice_copy':fields.binary('Contractor Invoice Copy'),
		'filename':fields.char('File Name'),
		'tax_id': fields.many2many('account.tax', 'foundry_invoice_taxes', 'invoice_id', 'tax_id', 'Taxes'),
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
		
		##Accounts Process
		'balance_receivable': fields.float('Balance Receivable'),		
		'accounts_state': fields.selection([('pending','Pending'),('paid','Paid')],'Accounts State', readonly=True),
		## Child Tables Declaration 
				
		'line_ids': fields.one2many('ch.foundry.invoice.line.details', 'header_id', "Line Details"),
		'line_ids_a': fields.one2many('ch.foundry.invoice.line.summary', 'header_id', "Line Summary "),
		'line_ids_b': fields.one2many('ch.foundry.invoice.expense.track','header_id',"Expense Track"),
		
				
	}
		
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_foundry_invoice', context=c),			
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
		cr.execute(""" select id,date_from,date_to from kg_foundry_invoice where  id != %s and contractor_id = %s and
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
		print"entry.contractor_id",entry.contractor_id.id		
		invoice_line_details_obj = self.pool.get('ch.foundry.invoice.line.details')
		invoice_line_summary_obj = self.pool.get('ch.foundry.invoice.line.summary')
			
		del_details_sql = """ delete from ch_foundry_invoice_line_details where header_id=%s """ %(ids[0])
		del_sql_summary = """ delete from ch_foundry_invoice_line_summary where header_id=%s """ %(ids[0])
		cr.execute(del_details_sql)
		cr.execute(del_sql_summary)
		
		cr.execute(""" (select moc_id,id,knockout_name as stage_code,knockout_date,knockout_weight as each_weight,knockout_accept_qty as qty,knockout_state,'KNOCK OUT' as stage_name from kg_fettling where  knockout_date >= '%s' and knockout_date <= '%s'
						and knockout_state = 'complete' and state != 'complete' and knockout_contractor = %s)

						UNION

						(select moc_id,id,decoring_name as stage_code,decoring_date,decoring_weight as each_weight,decoring_accept_qty as qty,decoring_state,'DECORING' as stage_name from kg_fettling where  decoring_date >= '%s' and decoring_date <= '%s'
						and decoring_state = 'complete' and state != 'complete' and decoring_contractor = %s) 
						
						UNION
						
						(select moc_id,id,shot_blast_name as stage_code,shot_blast_date,shot_blast_weight as each_weight,shot_blast_accept_qty as qty,shot_blast_state,'SHOT BLAST' as stage_name from kg_fettling where  shot_blast_date >= '%s' and shot_blast_date <= '%s'
						and shot_blast_state = 'complete' and state != 'complete' and shot_blast_contractor = %s) 
						
						UNION
						
						(select moc_id,id,hammering_name as stage_code,hammering_date,hammering_weight as each_weight,hammering_accept_qty as qty,hammering_state,'HAMMERING' as stage_name from kg_fettling where  hammering_date >= '%s' and hammering_date <= '%s'
						and hammering_state = 'complete' and state != 'complete' and hammering_contractor = %s) 
						
						UNION
						
						(select moc_id,id,wheel_cutting_name as stage_code,wheel_cutting_date,wheel_cutting_weight as each_weight,wheel_cutting_accept_qty as qty,wheel_cutting_state,'WHEEL CUTTING' as stage_name from kg_fettling where  wheel_cutting_date >= '%s' and wheel_cutting_date <= '%s'
						and wheel_cutting_state = 'complete' and state != 'complete' and wheel_cutting_contractor = %s) 
						
						UNION
						
						(select moc_id,id,gas_cutting_name as stage_code,gas_cutting_date,gas_cutting_weight as each_weight,gas_cutting_accept_qty as qty,gas_cutting_state,'GAS CUTTING' as stage_name from kg_fettling where  gas_cutting_date >= '%s' and gas_cutting_date <= '%s'
						and gas_cutting_state = 'complete' and state != 'complete' and gas_cutting_contractor = %s) 
						
						UNION
						
						(select moc_id,id,arc_cutting_name as stage_code,arc_cutting_date,arc_cutting_weight as each_weight,arc_cutting_accept_qty as qty,arc_cutting_state,'ARC CUTTING' as stage_name from kg_fettling where  arc_cutting_date >= '%s' and arc_cutting_date <= '%s'
						and arc_cutting_state = 'complete' and state != 'complete' and arc_cutting_contractor = %s) 
						
						UNION
						
						(select moc_id,id,heat_cycle_no as stage_code,heat_date,heat_each_weight as each_weight,heat_qty as qty,heat_state,'HEAT TREATMENT 1' as stage_name from kg_fettling where  heat_date >= '%s' and heat_date <= '%s'
						and heat_state = 'complete' and state != 'complete' and heat_contractor = %s) 
						
						UNION
						
						(select moc_id,id,heat2_cycle_no as stage_code,heat2_date,heat2_each_weight as each_weight,heat2_qty as qty,heat2_state,'HEAT TREATMENT 2' as stage_name from kg_fettling where  heat2_date >= '%s' and heat2_date <= '%s'
						and heat2_state = 'complete' and state != 'complete' and heat2_contractor = %s) 
						
						UNION
						
						(select moc_id,id,heat3_cycle_no as stage_code,heat3_date,heat3_each_weight as each_weight,heat3_qty as qty,heat3_state,'HEAT TREATMENT 3' as stage_name from kg_fettling where  heat3_date >= '%s' and heat3_date <= '%s'
						and heat3_state = 'complete' and state != 'complete' and heat3_contractor = %s) 
						
						UNION
						
						(select moc_id,id,rough_grinding_name as stage_code,rough_grinding_date,rough_grinding_weight as each_weight,rough_grinding_accept_qty as qty,rough_grinding_state,'ROUGH GRINDING' as stage_name from kg_fettling where  rough_grinding_date >= '%s' and rough_grinding_date <= '%s'
						and rough_grinding_state = 'complete' and state != 'complete' and rough_grinding_contractor = %s)
						
						UNION
						
						(select moc_id,id,welding_name as stage_code,welding_date,welding_weight as each_weight,welding_accept_qty as qty,welding_state,'WELDING' as stage_name from kg_fettling where  welding_date >= '%s' and welding_date <= '%s'
						and welding_state = 'complete' and state != 'complete' and welding_contractor = %s)
						
						UNION
						
						(select moc_id,id,finish_grinding_name as stage_code,finish_grinding_date,finish_grinding_weight as each_weight,finish_grinding_accept_qty as qty,finish_grinding_state,'FINISH GRINDING' as stage_name from kg_fettling where  finish_grinding_date >= '%s' and finish_grinding_date <= '%s'
						and finish_grinding_state = 'complete' and state != 'complete' and finish_grinding_contractor = %s)						
						
						UNION
												
						(select moc_id,id,reshot_blasting_name as stage_code,reshot_blasting_date,reshot_blasting_weight as each_weight,reshot_blasting_accept_qty as qty,reshot_blasting_state,'RE SHOT BLASTING' as stage_name from kg_fettling where  reshot_blasting_date >= '%s' and finish_grinding_date <= '%s'
						and reshot_blasting_state = 'complete' and state != 'complete' and reshot_blasting_contractor = %s)
						
											
						
						"""%(entry.date_from,entry.date_to,entry.contractor_id.id,entry.date_from,entry.date_to,entry.contractor_id.id,entry.date_from,entry.date_to,entry.contractor_id.id,entry.date_from,entry.date_to,entry.contractor_id.id,entry.date_from,entry.date_to,entry.contractor_id.id,entry.date_from,entry.date_to,entry.contractor_id.id,entry.date_from,entry.date_to,entry.contractor_id.id,entry.date_from,entry.date_to,entry.contractor_id.id,entry.date_from,entry.date_to,entry.contractor_id.id,entry.date_from,entry.date_to,entry.contractor_id.id,entry.date_from,entry.date_to,entry.contractor_id.id,entry.date_from,entry.date_to,entry.contractor_id.id,entry.date_from,entry.date_to,entry.contractor_id.id,entry.date_from,entry.date_to,entry.contractor_id.id))
		
		fettling_id = cr.dictfetchall();		
		
		for item in fettling_id:				
			
			vals = {
			
				'header_id': entry.id,
				'fettling_id':item['id'],
				'qty':item['qty'],
				'moc_id':item['moc_id'],								
				'stage_name':item['stage_name'],								
				'each_weight':item['each_weight'],									
				
			}
			
			foundry_line_id = invoice_line_details_obj.create(cr, uid,vals)		
		
		
		for item in fettling_id:			
			
			
			vals = {
			
				'header_id': entry.id,
				'fettling_id':item['id'],
				'qty':item['qty'],								
				'moc_id':item['moc_id'],								
				'stage_name':item['stage_name'],								
				'each_weight':item['each_weight'],								
				
			}
			
			foundry_line_id = invoice_line_summary_obj.create(cr, uid,vals)		
		
			
		return True
	   

	def entry_confirm(self,cr,uid,ids,context=None):
		
		entry = self.browse(cr,uid,ids[0])	
		final_other_charges = 0.00
		for item in entry.line_ids_b:				
			final_other_charges += item.expense_amt
		if len(entry.line_ids) == 0:		
			raise osv.except_osv(_('Invoice details is must !!'),
				_('Enter the proceed button!!'))
		if entry.state == 'draft':
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
			
			### Sequence Number Generation  ###									
			if entry.name == '' or entry.name == False:
				foundry_invoice_name = ''	
				foundry_invoice_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.foundry.invoice')])
				rec = self.pool.get('ir.sequence').browse(cr,uid,foundry_invoice_seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(foundry_invoice_seq_id[0],rec.code,entry.entry_date))
				foundry_invoice_name = cr.fetchone();
				foundry_invoice_name = foundry_invoice_name[0]				
			else:
				foundry_invoice_name = entry.name		
											
			self.write(cr, uid, ids, {'state': 'confirmed','name':foundry_invoice_name,'confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})								
									
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
		for item in entry.line_ids_b:				
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
				total_value_amt += line.total_value			
				self.write(cr, uid, ids, {'balance_receivable':rec.amount_total,'state': 'done','done_user_id': uid, 'done_date': time.strftime('%Y-%m-%d %H:%M:%S')})
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
			for expense in rec.line_ids_b:
				ex_account_id = expense.expense.account_id.id			
				tax_obj = self.pool.get('account.tax')
				taxes = tax_obj.compute_all(cr, uid, expense.tax_id, expense.amount, 1, 1, partner=rec.contractor_id)			
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
		return super(kg_foundry_invoice, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_foundry_invoice, self).write(cr, uid, ids, vals, context)
		
	_sql_constraints = [
	
		('name', 'unique(name)', 'No must be Unique !!'),
	]	
	
kg_foundry_invoice()


class ch_foundry_invoice_line_details(osv.osv):

	_name = "ch.foundry.invoice.line.details"
	_description = "Foundry Invoice Line details"
	
	def _get_rate_value(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		total_value = 0.00
		rate = 0.00
		total_value = 0.00
		total_weight = 0.00
		for entry in self.browse(cr, uid, ids, context=context):
			result[entry.id] = {
				'rate': 0.00,
				'total_weight': 0.00,
				'total_value': 0.00,				
			}				
			invoice_id = self.pool.get('kg.stage.master').search(cr,uid,[('name','=',entry.stage_name)])	
			total_weight = 	entry.qty * entry.each_weight			
			if invoice_id:				
				inv_rate = self.pool.get('kg.stage.master').browse(cr,uid,invoice_id[0])														
				if entry.moc_id.moc_cate_fetting:						
					in_id = self.pool.get('ch.stage.fettling').search(cr,uid,[('header_id','=',inv_rate.id),('moc_cate_id','=',entry.moc_id.moc_cate_fetting.id)])				
					if in_id:						
						is_rate = self.pool.get('ch.stage.fettling').browse(cr,uid,in_id[0])										
						rate = is_rate.rate							
						total_value = 	entry.qty * entry.each_weight* is_rate.rate			
			result[entry.id]['rate'] = rate						
			result[entry.id]['total_weight'] = total_weight						
			result[entry.id]['total_value'] = total_value
		return result
	
	_columns = {
	
		### Basic Info
		
		'header_id':fields.many2one('kg.foundry.invoice', 'Transaction', required=1, ondelete='cascade'),
		'remark': fields.text('Remarks'),
		'active': fields.boolean('Active'),			
		
		### Module Requirement Fields
		
		'fettling_id': fields.many2one('kg.fettling','Fettling Items'),
		
		'order_no': fields.related('fettling_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('fettling_id','order_delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'order_date': fields.related('fettling_id','entry_date', type='date', string='Order Date', store=True, readonly=True),
		'order_category': fields.related('fettling_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),		
		'pump_model_id': fields.related('fettling_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('fettling_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_code': fields.related('fettling_id','pattern_code', type='char', string='Pattern Code', store=True, readonly=True),
		'pattern_name': fields.related('fettling_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),		
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'schedule_qty': fields.related('fettling_id','schedule_qty', type='integer', size=100, string='Schedule Qty', store=True, readonly=True),	
		'melting_id': fields.related('fettling_id','melting_id', type='many2one', relation='kg.melting', string='Heat No.', store=True, readonly=True),
		'stage_id': fields.related('fettling_id','stage_id', type='many2one', relation='kg.stage.master', string='Stage Name', store=True, readonly=True),
		'stage_name': fields.char('Stage Name', select=True,readonly=True),		
		'qty': fields.integer('QTY'),
		'each_weight': fields.float('Each Weight'),			
		'state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')],'Status', readonly=True),
		
		'rate': fields.function(_get_rate_value, digits_compute= dp.get_precision('Account'), string='Rate',
			store={
				'ch.foundry.invoice.line.details': (lambda self, cr, uid, ids, c={}: ids, ['header_id'], 10),				
			}, multi="sums", help="The Rate Value", track_visibility='always'),				
			
		'total_weight': fields.function(_get_rate_value, digits_compute= dp.get_precision('Account'), string='Total Weight',
			store={
				'ch.foundry.invoice.line.details': (lambda self, cr, uid, ids, c={}: ids, ['header_id'], 10),				
			}, multi="sums", help="The Total Weight Value", track_visibility='always'),	
		
		'total_value': fields.function(_get_rate_value, digits_compute= dp.get_precision('Account'), string='Total Value',
			store={
				'ch.foundry.invoice.line.details': (lambda self, cr, uid, ids, c={}: ids, ['header_id'], 10),				
			}, multi="sums", help="The Total Value", track_visibility='always'),		
		
		## Child Tables Declaration 				
		
	}
		
	_defaults = {
	
		'active': True,
		'state': 'pending',	
		
	}
	
		
ch_foundry_invoice_line_details()



class ch_foundry_invoice_line_summary(osv.osv):

	_name = "ch.foundry.invoice.line.summary"
	_description = "Foundry Invoice Line Summary"
	
	def _get_rate_value(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		total_value = 0.00
		rate = 0.00
		total_value = 0.00
		total_weight = 0.00
		for entry in self.browse(cr, uid, ids, context=context):
			result[entry.id] = {
				'rate': 0.00,
				'total_weight': 0.00,
				'total_value': 0.00,				
			}				
			invoice_id = self.pool.get('kg.stage.master').search(cr,uid,[('name','=',entry.stage_name)])	
			total_weight = 	entry.qty * entry.each_weight			
			if invoice_id:				
				inv_rate = self.pool.get('kg.stage.master').browse(cr,uid,invoice_id[0])														
				if entry.moc_id.moc_cate_fetting:						
					in_id = self.pool.get('ch.stage.fettling').search(cr,uid,[('header_id','=',inv_rate.id),('moc_cate_id','=',entry.moc_id.moc_cate_fetting.id)])				
					if in_id:						
						is_rate = self.pool.get('ch.stage.fettling').browse(cr,uid,in_id[0])										
						rate = is_rate.rate							
						total_value = 	entry.qty * entry.each_weight* is_rate.rate			
			result[entry.id]['rate'] = rate						
			result[entry.id]['total_weight'] = total_weight						
			result[entry.id]['total_value'] = total_value
		return result
	
	_columns = {
	
		### Basic Info
		
		'header_id':fields.many2one('kg.foundry.invoice', 'Transaction', required=1, ondelete='cascade'),
		'remark': fields.text('Remarks'),
		'active': fields.boolean('Active'),			
		
		### Module Requirement Fields
		
		'fettling_id': fields.many2one('kg.fettling','Fettling Items'),
		
		'order_no': fields.related('fettling_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('fettling_id','order_delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'order_date': fields.related('fettling_id','entry_date', type='date', string='Order Date', store=True, readonly=True),
		'order_category': fields.related('fettling_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),		
		'pump_model_id': fields.related('fettling_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('fettling_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_code': fields.related('fettling_id','pattern_code', type='char', string='Pattern Code', store=True, readonly=True),
		'pattern_name': fields.related('fettling_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),		
		'schedule_qty': fields.related('fettling_id','schedule_qty', type='integer', size=100, string='Schedule Qty', store=True, readonly=True),	
		'melting_id': fields.related('fettling_id','melting_id', type='many2one', relation='kg.melting', string='Heat No.', store=True, readonly=True),
		'stage_id': fields.related('fettling_id','stage_id', type='many2one', relation='kg.stage.master', string='Stage Name', store=True, readonly=True),
		'stage_name': fields.char('Stage Name', select=True,readonly=True),
		
		'moc_id': fields.many2one('kg.moc.master','MOC'),

		'qty': fields.integer('QTY'),
		'each_weight': fields.float('Each Weight'),		
		
		'rate': fields.function(_get_rate_value, digits_compute= dp.get_precision('Account'), string='Rate',
			store={
				'ch.foundry.invoice.line.summary': (lambda self, cr, uid, ids, c={}: ids, ['header_id'], 10),				
			}, multi="sums", help="The Rate Value", track_visibility='always'),				
			
		'total_weight': fields.function(_get_rate_value, digits_compute= dp.get_precision('Account'), string='Total Weight',
			store={
				'ch.foundry.invoice.line.summary': (lambda self, cr, uid, ids, c={}: ids, ['header_id'], 10),				
			}, multi="sums", help="The Total Weight Value", track_visibility='always'),	
		
		'total_value': fields.function(_get_rate_value, digits_compute= dp.get_precision('Account'), string='Total Value',
			store={
				'ch.foundry.invoice.line.summary': (lambda self, cr, uid, ids, c={}: ids, ['header_id'], 10),				
			}, multi="sums", help="The Total Value", track_visibility='always'),		
		
		
		'state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')],'Status', readonly=True),
		
		## Child Tables Declaration 
				
		
	}
		
	_defaults = {
	
		'active': True,
		'state': 'pending',		
		
	}
	
		
ch_foundry_invoice_line_summary()


class ch_foundry_invoice_expense_track(osv.osv):

	_name = "ch.foundry.invoice.expense.track"
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
		
		'header_id': fields.many2one('kg.foundry.invoice', 'Expense Track'),
		'name': fields.char('Number', size=128, select=True,readonly=False),
		'date': fields.date('Creation Date'),
		'amount': fields.float('Amount'),		
		'tax_id': fields.many2many('account.tax', 'foundry_invoice_expense_taxe', 'invoice_id', 'tax_id', 'Tax'),
		'company_id': fields.many2one('res.company', 'Company Name'),
		'description': fields.char('Description'),
		'remark': fields.text('Remarks'),		
		'expense_amt': fields.function(_get_total_amt, string='Total Amount',digits=(16,2), method=True, store=True, type='float'),		
		'expense': fields.many2one('kg.expense.master','Expense'),
		
	}
	
	_defaults = {
		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'ch.foundry.invoice.expense.track', context=c),
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
	
		}	
	
ch_foundry_invoice_expense_track()
