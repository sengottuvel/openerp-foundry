from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_account_voucher(osv.osv):

	_name = "account.voucher"
	_inherit = "account.voucher"
	_description = "Account Voucher"
	
	
	def _voucher_amount_value(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		voucher_amt = 0.00
		for entry in self.browse(cr, uid, ids, context=context):	
			for item in entry.line_ids:			
				voucher_amt += item.debit			
			result[entry.id] = voucher_amt
		return result
	
	_columns = {	
			
		### Entry Info ###
		
		
		'crt_date': fields.datetime('Created Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'post_date': fields.datetime('Posted Date', readonly=True),
		'post_user_id': fields.many2one('res.users', 'Posted By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),		
		
		
		### Receipt Entry Provision start here
		
		
		'entry_date':fields.date('Voucher Date'),
		'payment_mode':fields.selection([('bank', 'Bank'),('cash', 'Cash')], 'Payment Mode', required=True),				
		'sub_mode':fields.selection([('dd', 'DD'),('cheque', 'Cheque'),('neft', 'NEFT'),('rtgs', 'RTGS'),('others', 'Others')], 'Sub Mode'),
		'reference_no': fields.char('Ref.No'),
		'cheque_in_favor': fields.char('Cheque In Favor Of'),
		'receipt_source':fields.selection([('advance', 'Advance'),('sales_invoice', 'Sales Invoice')], 'Receipt Source'),
		'division_id': fields.many2one('kg.division.master', 'Division',required=True),
		'book_current_bal': fields.float('Book Current Balance', readonly=True),
		'default_type':fields.selection([('receipt', 'Receipt'),('payment', 'Payment')], 'Default Type'),		
		'voucher_amt': fields.function(_voucher_amount_value, string='Voucher Amount',store=True, type='float',readonly=True),
		'narration': fields.char('Narration'),
		
		## Receipt Child Tables Declaration	
		
		'line_ids_a':fields.one2many('ch.sale.invoice.details', 'header_id', "Sales Invoice Details"),
		'line_ids_b':fields.one2many('ch.customer.advance.details', 'header_id', "Advance Details"),	
				
		### Payment Entry Provision start here
		'tds_flag': fields.boolean('TDS Not Applicable'),
		'payment_source':fields.selection([('purchase_bills', 'Purchase Bills'),('po_advance', 'PO Advance'),('fettling_bills', 'Fettling Bills')
		,('ms_sc_bills', 'MS SC Bills'),('salary', 'Salary'),('direct_bills', 'Direct Bills'),('credit_note', 'Credit Note')], 'Payment Source'),
		
		## Payment Child Tables Declaration	
		'line_ids_c':fields.one2many('ch.purchase.bill.details', 'header_id', "Purchase Bill Details"),	
		'line_ids_d':fields.one2many('ch.supplier.advance.details', 'header_id', "Advance Details"),	
		'line_ids_e':fields.one2many('ch.fettling.bill.details', 'header_id', "Fettling Bill Details"),	
		'line_ids_f':fields.one2many('ch.ms.sc.bill.details', 'header_id', "MS SC Bill Details"),	
		'line_ids_g':fields.one2many('ch.salary.details', 'header_id', "Salary Details"),	
		'line_ids_h':fields.one2many('ch.direct.bill.details', 'header_id', "Direct Bill Details"),	
		'line_ids_i':fields.one2many('ch.tds.details', 'header_id', "TDS Details"),	
		'line_ids_j':fields.one2many('ch.credit.note.details', 'header_id', "Credit Note Details"),			
				
	}
	
	_defaults = {
		
		'entry_date': lambda *a: time.strftime('%Y-%m-%d'),		
		'tds_flag': False,	
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),	
		
	}		
	
	def onchange_book_value(self, cr, uid, ids, journal_id, context=None):
		book_amt = 0.00
		if journal_id:
			journal_rec = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)			
			if journal_rec.default_debit_account_id.id is False:
				raise osv.except_osv(_('Account Configure!!'),
							_('Please mapping account in Book Master!!'))
			cr.execute(''' select sum(debit) - sum(credit) as balance from account_move_line where account_id = %s ''' ,[journal_rec.default_debit_account_id.id])
			book_value = cr.fetchone()				
			if book_value[0] is not None:
				book_amt = 	book_value[0]				
			else:
				book_amt = 0.00
		else:
			book_amt = 0.00		
		return {'value': {'book_current_bal':book_amt}}
	
	def onchange_cheque_in_favor(self, cr, uid, ids, partner_id,sub_mode, context=None):
		
		value = {'cheque_in_favor': ''}
		
		if sub_mode == 'cheque':
			if partner_id:				
				cheque_rec = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
				value = {'cheque_in_favor': cheque_rec.name}
			
		return {'value': value}
		
	def load_data(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])		
		customer_line_obj = self.pool.get('ch.customer.advance.details')
		
		### Receipt Process Start here		
		if entry.default_type == 'receipt':			
			if entry.receipt_source == 'sales_invoice':				
				del_sql = """ delete from ch_sale_invoice_details where header_id=%s """ %(ids[0])
				cr.execute(del_sql)	
				sale_invoice_line_obj = self.pool.get('ch.sale.invoice.details')
				sale_ids = self.pool.get('kg.sale.invoice').search(cr, uid, [('customer_id','=',entry.partner_id.id),('state','=','invoice'),('balance_receivable','>',0.00)])				
				if sale_ids == []:
					raise osv.except_osv(_('Warning!'),
						_('No Data Available !!'))
				for item in sale_ids:					
					sale_rec = self.pool.get('kg.sale.invoice').browse(cr, uid,item)						
					vals = {					
						'header_id': entry.id,
						'invoice_id':sale_rec.id,
						'invoice_date':sale_rec.invoice_date,								
						'invoice_amt':sale_rec.net_amt,		
						'balance_amt':sale_rec.balance_receivable,		
						'current_amt':sale_rec.balance_receivable,							
						}
						
					sale_invoice_line_id = sale_invoice_line_obj.create(cr, uid,vals)		
			elif entry.receipt_source == 'advance':				
				del_sql = """ delete from ch_customer_advance_details where header_id=%s """ %(ids[0])
				cr.execute(del_sql)	
				adv_line_obj = self.pool.get('ch.customer.advance.details')
				adv_ids = self.pool.get('kg.customer.advance').search(cr, uid, [('customer_id','=',entry.partner_id.id),('state','=','done'),('balance_receivable','>',0.00)])				
				if adv_ids == []:
					raise osv.except_osv(_('Warning!'),
						_('No Data Available !!'))	
				for item in adv_ids:					
					adv_rec = self.pool.get('kg.customer.advance').browse(cr, uid,item)							
					vals = {					
						'header_id': entry.id,
						'advance_id':adv_rec.id,
						'advance_date':adv_rec.entry_date,								
						'advance_amt':adv_rec.advance_amt,		
						'balance_amt':adv_rec.balance_receivable,		
						'current_amt':adv_rec.balance_receivable,						
						}						
					adv_line_id = adv_line_obj.create(cr, uid,vals)
		
		### Payment Process Start here					
		elif entry.default_type == 'payment':	
			if entry.payment_source == 'purchase_bills':				
				del_sql = """ delete from ch_purchase_bill_details where header_id=%s """ %(ids[0])
				cr.execute(del_sql)	
				purchase_invoice_line_obj = self.pool.get('ch.purchase.bill.details')
				pur_inv_ids = self.pool.get('kg.purchase.invoice').search(cr, uid, [('supplier_id','=',entry.partner_id.id),('state','=','approved'),('bal_amt','>',0.00)])				
				if pur_inv_ids == []:
					raise osv.except_osv(_('Warning!'),
						_('No Data Available !!'))
				for item in pur_inv_ids:					
					purchase_rec = self.pool.get('kg.purchase.invoice').browse(cr, uid,item)						
					vals = {					
						'header_id': entry.id,
						'invoice_id':purchase_rec.id,
						'invoice_date':purchase_rec.invoice_date,								
						'due_date':purchase_rec.payment_due_date,								
						'sup_invoice_no':purchase_rec.sup_invoice_no,								
						'invoice_amt':purchase_rec.amount_total,		
						'balance_amt':purchase_rec.bal_amt,		
						'current_amt':purchase_rec.bal_amt,							
						}
						
					purchase_invoice_line_id = purchase_invoice_line_obj.create(cr, uid,vals)	
					
			elif entry.payment_source == 'po_advance':				
				del_sql = """ delete from ch_supplier_advance_details where header_id=%s """ %(ids[0])
				cr.execute(del_sql)	
				po_adv_line_obj = self.pool.get('ch.supplier.advance.details')
				sup_adv_ids = self.pool.get('kg.supplier.advance').search(cr, uid, [('supplier_id','=',entry.partner_id.id),('state','=','approve'),('paid_amt','>',0.00)])				
				if sup_adv_ids == []:
					raise osv.except_osv(_('Warning!'),
						_('No Data Available !!'))
				for item in sup_adv_ids:					
					sup_adv_rec = self.pool.get('kg.supplier.advance').browse(cr, uid,item)						
					vals = {					
						'header_id': entry.id,
						'advance_id':sup_adv_rec.id,
						'advance_date':sup_adv_rec.entry_date,													
						'advance_amt':sup_adv_rec.advance_amt,		
						'balance_amt':sup_adv_rec.paid_amt,		
						'current_amt':sup_adv_rec.paid_amt,							
						}
						
					po_adv_line_id = po_adv_line_obj.create(cr, uid,vals)
					
			elif entry.payment_source == 'fettling_bills':				
				del_sql = """ delete from ch_fettling_bill_details where header_id=%s """ %(ids[0])
				cr.execute(del_sql)	
				fettling_bills_line_obj = self.pool.get('ch.fettling.bill.details')
				fettling_bills_ids = self.pool.get('kg.foundry.invoice').search(cr, uid, [('contractor_id','=',entry.partner_id.id),('state','=','done'),('balance_receivable','>',0.00)])				
				if fettling_bills_ids == []:
					raise osv.except_osv(_('Warning!'),
						_('No Data Available !!'))
				for item in fettling_bills_ids:					
					fettling_bills_rec = self.pool.get('kg.foundry.invoice').browse(cr, uid,item)						
					vals = {					
						'header_id': entry.id,
						'invoice_id':fettling_bills_rec.id,
						'invoice_date':fettling_bills_rec.entry_date,								
						'due_date':fettling_bills_rec.due_date,								
						'sup_invoice_no':fettling_bills_rec.con_invoice_no,								
						'invoice_amt':fettling_bills_rec.amount_total,		
						'balance_amt':fettling_bills_rec.balance_receivable,		
						'current_amt':fettling_bills_rec.balance_receivable,							
						}
						
					fettling_bills_line_id = fettling_bills_line_obj.create(cr, uid,vals)
					
					
			elif entry.payment_source == 'ms_sc_bills':				
				del_sql = """ delete from ch_ms_sc_bill_details where header_id=%s """ %(ids[0])
				cr.execute(del_sql)	
				ms_sc_line_obj = self.pool.get('ch.ms.sc.bill.details')
				ms_sc_ids = self.pool.get('kg.subcontract.invoice').search(cr, uid, [('contractor_id','=',entry.partner_id.id),('state','=','done'),('balance_receivable','>',0.00)])				
				if ms_sc_ids == []:
					raise osv.except_osv(_('Warning!'),
						_('No Data Available !!'))
				for item in ms_sc_ids:					
					ms_sc_rec = self.pool.get('kg.subcontract.invoice').browse(cr, uid,item)						
					vals = {					
						'header_id': entry.id,
						'invoice_id':ms_sc_rec.id,
						'invoice_date':ms_sc_rec.entry_date,								
						'due_date':ms_sc_rec.due_date,								
						'sup_invoice_no':ms_sc_rec.con_invoice_no,								
						'invoice_amt':ms_sc_rec.amount_total,		
						'balance_amt':ms_sc_rec.balance_receivable,		
						'current_amt':ms_sc_rec.balance_receivable,							
						}
						
					ms_sc_line_id = ms_sc_line_obj.create(cr, uid,vals)
					
			elif entry.payment_source == 'salary':
				raise osv.except_osv(_('Warning!'),
						_('Under Development Process for Employee Salary !!'))					
				del_sql = """ delete from ch_salary_details where header_id=%s """ %(ids[0])
				cr.execute(del_sql)	
				emp_sal_line_obj = self.pool.get('ch.salary.details')
				emp_sal_ids = self.pool.get('hr.payslip').search(cr, uid, [('employee_id','=',entry.employee.id),('state','=','done'),('balance_receivable','>',0.00)])				
				if emp_sal_ids == []:
					raise osv.except_osv(_('Warning!'),
						_('No Data Available !!'))
				for item in emp_sal_ids:					
					emp_sal_rec = self.pool.get('hr.payslip').browse(cr, uid,item)						
					vals = {					
						'header_id': entry.id,
						'employee_id':emp_sal_rec.id,
						'employee_code':emp_sal_rec.emp_name,								
						'month':emp_sal_rec.month,								
						'salary_amt':emp_sal_rec.round_val,								
						'current_amt':emp_sal_rec.balance_receivable,													
						}
						
					emp_sal_line_id = emp_sal_line_obj.create(cr, uid,vals)
					
					
			elif entry.payment_source == 'direct_bills':				
				del_sql = """ delete from ch_direct_bill_details where header_id=%s """ %(ids[0])
				cr.execute(del_sql)	
				direct_exp_line_obj = self.pool.get('ch.direct.bill.details')
				direct_exp_ids = self.pool.get('direct.entry.expense').search(cr, uid, [('supplier_id','=',entry.partner_id.id),('state','=','approved'),('balance_receivable','>',0.00)])				
				if direct_exp_ids == []:
					raise osv.except_osv(_('Warning!'),
						_('No Data Available !!'))
				for item in direct_exp_ids:					
					direct_exp_rec = self.pool.get('direct.entry.expense').browse(cr, uid,item)						
					vals = {					
						'header_id': entry.id,
						'invoice_id':direct_exp_rec.id,
						'invoice_date':direct_exp_rec.expense_date,								
						'due_date':direct_exp_rec.invoice_date,								
						'sup_invoice_no':direct_exp_rec.invoice_no,								
						'invoice_amt':direct_exp_rec.amount_total,		
						'balance_amt':direct_exp_rec.balance_receivable,		
						'current_amt':direct_exp_rec.balance_receivable,							
						}
						
					direct_exp_line_id = direct_exp_line_obj.create(cr, uid,vals)
					
			elif entry.payment_source == 'credit_note':				
				del_sql = """ delete from ch_credit_note_details where header_id=%s """ %(ids[0])
				cr.execute(del_sql)	
				credit_line_obj = self.pool.get('ch.credit.note.details')
				credit_ids = self.pool.get('kg.credit.note').search(cr, uid, [('supplier_id','=',entry.partner_id.id),('state','=','approved'),('balance_receivable','>',0.00)])				
				if credit_ids == []:
					raise osv.except_osv(_('Warning!'),
						_('No Data Available !!'))
				for item in credit_ids:					
					credit_rec = self.pool.get('kg.credit.note').browse(cr, uid,item)						
					vals = {					
						'header_id': entry.id,
						'credit_id':credit_rec.id,
						'credit_date':credit_rec.date,													
						'credit_amt':credit_rec.amount_total,		
						'balance_amt':credit_rec.balance_receivable,		
						'current_amt':credit_rec.balance_receivable,							
						}
						
					credit_line_id = credit_line_obj.create(cr, uid,vals)
			
		return True
	
	
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])	
		voucher_line_obj = self.pool.get('account.voucher.line')			
		advance_obj = self.pool.get('kg.customer.advance')			
		sale_invoice_obj = self.pool.get('kg.sale.invoice')			
		voucher_name = entry.name		
		if entry.name is False:
			if entry.default_type == 'receipt':				
				receipt_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.account.voucher.receipt')])
				rec = self.pool.get('ir.sequence').browse(cr,uid,receipt_seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(receipt_seq_id[0],rec.code,entry.entry_date))
				vouchers_name = cr.fetchone();
				voucher_name = vouchers_name[0]
			else:				
				receipt_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.account.voucher.payment')])
				rec = self.pool.get('ir.sequence').browse(cr,uid,receipt_seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(receipt_seq_id[0],rec.code,entry.entry_date))
				vouchers_name = cr.fetchone();
				voucher_name = vouchers_name[0]
		if entry.default_type == 'receipt':			
			if entry.receipt_source == 'advance':
				cr.execute(""" select sum(id)
					from ch_customer_advance_details  
					where flag_select = 't' and header_id = %s """%(entry.id))					
				total_lds = cr.fetchone();		
				if total_lds[0] is None:
					raise osv.except_osv(_('Warning!'),
						_('System not allow to without advance items !!'))				
				for adv_item in entry.line_ids_b:
					if adv_item.flag_select == True:
						if entry.partner_id.id !=  adv_item.advance_id.customer_id.id:
							raise osv.except_osv(_('Warning!'),
								_('System not allow to different Customer, Kindly Verify!!'))	
						if entry.partner_id:
							account_id = entry.partner_id.property_account_receivable.id
							if not account_id:
								raise osv.except_osv(_('Customer Configuration Warning !!'),
									_('Customer account should be configured !!'))											
							vals = {							
									'voucher_id': entry.id,
									'doc_no':adv_item.advance_id.name,
									'doc_date':adv_item.advance_date,								
									'account_id':account_id,		
									'credit':adv_item.current_amt,		
									'debit':0.00,		
									'source':'customer_advance',										
									'narration':entry.narration,								
									}
									
							voucher_line_id = voucher_line_obj.create(cr, uid,vals)	
						if entry.journal_id:							
							bank_account_id = entry.journal_id.default_debit_account_id.id 						
							if not bank_account_id:
								raise osv.except_osv(_('Bank Configuration Warning !!'),
									_('Bank account should be configured !!'))
							vals = {							
									'voucher_id': entry.id,
									'doc_no':adv_item.advance_id.name,
									'doc_date':adv_item.advance_date,								
									'account_id':bank_account_id,		
									'debit':adv_item.current_amt,
									'credit':0.00,			
									'source':'customer_advance',										
									'narration':entry.narration,							
									}
							voucher_line_id = voucher_line_obj.create(cr, uid,vals)
						if adv_item.advance_id.balance_receivable < adv_item.current_amt:
							raise osv.except_osv(_('Current Amount Warning !!'),
									_('Current Amount greater than advance amount !!'))
						balance_amt = adv_item.advance_id.balance_receivable - adv_item.current_amt	
						accounts_state = 'pending'
						if balance_amt == 0.00:
							accounts_state = 'paid'					
						advance_obj.write(cr, uid, adv_item.advance_id.id, {'balance_receivable': balance_amt,'accounts_state':accounts_state})									
			elif entry.receipt_source == 'sales_invoice':	
				cr.execute(""" select sum(id)
					from ch_sale_invoice_details  
					where flag_select = 't' and header_id = %s """%(entry.id))					
				total_lds = cr.fetchone();								
				if total_lds[0] is None:
					raise osv.except_osv(_('Warning!'),
						_('System not allow to without Sale Invoice items !!'))				
				for sale_invoice_item in entry.line_ids_a:					 
					if sale_invoice_item.flag_select == True:
						if entry.partner_id.id !=  sale_invoice_item.invoice_id.customer_id.id:
							raise osv.except_osv(_('Warning!'),
								_('System not allow to different Customer, Kindly Verify!!'))
						if entry.partner_id:
							account_id = entry.partner_id.property_account_receivable.id
							if not account_id:
								raise osv.except_osv(_('Customer Configuration Warning !!'),
									_('Customer account should be configured !!'))											
							vals = {							
									'voucher_id': entry.id,
									'doc_no':sale_invoice_item.invoice_id.name,
									'doc_date':sale_invoice_item.invoice_date,								
									'account_id':account_id,		
									'credit':sale_invoice_item.current_amt,		
									'debit':0.00,		
									'source':'sale_invoice',										
									'narration':entry.narration,								
									}
									
							voucher_line_id = voucher_line_obj.create(cr, uid,vals)	
						if entry.journal_id:							
							bank_account_id = entry.journal_id.default_debit_account_id.id 							
							if not bank_account_id:
								raise osv.except_osv(_('Bank Configuration Warning !!'),
									_('Bank account should be configured !!'))
							vals = {							
									'voucher_id': entry.id,
									'doc_no':sale_invoice_item.invoice_id.name,
									'doc_date':sale_invoice_item.invoice_date,								
									'account_id':bank_account_id,		
									'debit':sale_invoice_item.current_amt,
									'credit':0.00,			
									'source':'sale_invoice',										
									'narration':entry.narration,							
									}
							voucher_line_id = voucher_line_obj.create(cr, uid,vals)
						if sale_invoice_item.invoice_id.balance_receivable < sale_invoice_item.current_amt:
							raise osv.except_osv(_('Current Amount Warning !!'),
									_('Current Amount greater than Invoice amount !!'))
						balance_amt = sale_invoice_item.invoice_id.balance_receivable - sale_invoice_item.current_amt	
						accounts_state = 'pending'
						if balance_amt == 0.00:
							accounts_state = 'paid'							
						sale_invoice_obj.write(cr, uid, sale_invoice_item.invoice_id.id, {'balance_receivable': balance_amt,'accounts_state':accounts_state})												
		elif entry.default_type == 'payment':	
			if entry.payment_source == 'purchase_bills':
				purchase_obj = self.pool.get('kg.purchase.invoice')	
				cr.execute(""" select sum(id)
					from ch_purchase_bill_details  
					where flag_select = 't' and header_id = %s """%(entry.id))					
				total_lds = cr.fetchone();		
				if total_lds[0] is None:
					raise osv.except_osv(_('Warning!'),
						_('System not allow to without Purchase bill items !!'))				
				for purchase_item in entry.line_ids_c:
					if purchase_item.flag_select == True:
						if entry.partner_id.id !=  purchase_item.invoice_id.supplier_id.id:
							raise osv.except_osv(_('Warning!'),
								_('System not allow to different Supplier, Kindly Verify!!'))
						if entry.partner_id:
							account_id = entry.partner_id.property_account_payable.id
							if not account_id:
								raise osv.except_osv(_('Supplier Configuration Warning !!'),
									_('Supplier account should be configured !!'))											
							vals = {							
									'voucher_id': entry.id,
									'doc_no':purchase_item.invoice_id.name,
									'doc_date':purchase_item.invoice_date,								
									'account_id':account_id,		
									'credit':0.00,		
									'debit':purchase_item.current_amt,		
									'source':'purchase_bills',										
									'narration':entry.narration,								
									}
									
							voucher_line_id = voucher_line_obj.create(cr, uid,vals)	
						if entry.journal_id:							
							bank_account_id = entry.journal_id.default_debit_account_id.id 						
							if not bank_account_id:
								raise osv.except_osv(_('Bank Configuration Warning !!'),
									_('Bank account should be configured !!'))
							vals = {							
									'voucher_id': entry.id,
									'doc_no':purchase_item.invoice_id.name,
									'doc_date':purchase_item.invoice_date,								
									'account_id':bank_account_id,		
									'debit':0.00,
									'credit':purchase_item.current_amt,			
									'source':'purchase_bills',										
									'narration':entry.narration,							
									}
							voucher_line_id = voucher_line_obj.create(cr, uid,vals)
						if purchase_item.invoice_id.bal_amt < purchase_item.current_amt:
							raise osv.except_osv(_('Current Amount Warning !!'),
									_('Current Amount greater than Invoice amount !!'))
						balance_amt = purchase_item.invoice_id.bal_amt - purchase_item.current_amt	
						accounts_state = 'pending'
						if balance_amt == 0.00:
							accounts_state = 'paid'					
						purchase_obj.write(cr, uid, purchase_item.invoice_id.id, {'bal_amt': balance_amt,'accounts_state':accounts_state})									
		
			elif entry.payment_source == 'po_advance':
				sup_adv_obj = self.pool.get('kg.supplier.advance')		
				cr.execute(""" select sum(id)
					from ch_supplier_advance_details  
					where flag_select = 't' and header_id = %s """%(entry.id))					
				total_lds = cr.fetchone();		
				if total_lds[0] is None:
					raise osv.except_osv(_('Warning!'),
						_('System not allow to without supplier advance items !!'))				
				for sup_adv_item in entry.line_ids_d:
					if sup_adv_item.flag_select == True:
						if entry.partner_id.id !=  sup_adv_item.advance_id.supplier_id.id:
							raise osv.except_osv(_('Warning!'),
								_('System not allow to different Supplier, Kindly Verify!!'))
						if entry.partner_id:
							account_id = entry.partner_id.property_account_payable.id
							if not account_id:
								raise osv.except_osv(_('Supplier Configuration Warning !!'),
									_('Supplier account should be configured !!'))											
							vals = {							
									'voucher_id': entry.id,
									'doc_no':sup_adv_item.advance_id.name,
									'doc_date':sup_adv_item.advance_date,								
									'account_id':account_id,		
									'credit':0.00,		
									'debit':sup_adv_item.current_amt,		
									'source':'po_advance',										
									'narration':entry.narration,								
									}
									
							voucher_line_id = voucher_line_obj.create(cr, uid,vals)	
						if entry.journal_id:							
							bank_account_id = entry.journal_id.default_debit_account_id.id 						
							if not bank_account_id:
								raise osv.except_osv(_('Bank Configuration Warning !!'),
									_('Bank account should be configured !!'))
							vals = {							
									'voucher_id': entry.id,
									'doc_no':sup_adv_item.advance_id.name,
									'doc_date':sup_adv_item.advance_date,								
									'account_id':bank_account_id,		
									'debit':0.00,
									'credit':sup_adv_item.current_amt,			
									'source':'po_advance',										
									'narration':entry.narration,							
									}
							voucher_line_id = voucher_line_obj.create(cr, uid,vals)
						if sup_adv_item.advance_id.paid_amt < sup_adv_item.current_amt:
							raise osv.except_osv(_('Current Amount Warning !!'),
									_('Current Amount greater than Invoice amount !!'))
						balance_amt = sup_adv_item.advance_id.paid_amt - sup_adv_item.current_amt	
						accounts_state = 'pending'
						if balance_amt == 0.00:
							accounts_state = 'paid'					
						sup_adv_obj.write(cr, uid, sup_adv_item.advance_id.id, {'paid_amt': balance_amt,'accounts_state':accounts_state})
						
			elif entry.payment_source == 'fettling_bills':
				fettling_obj = self.pool.get('kg.foundry.invoice')	
				cr.execute(""" select sum(id)
					from ch_fettling_bill_details  
					where flag_select = 't' and header_id = %s """%(entry.id))					
				total_lds = cr.fetchone();		
				if total_lds[0] is None:
					raise osv.except_osv(_('Warning!'),
						_('System not allow to without Purchase bill items !!'))				
				for fettling_item in entry.line_ids_e:
					if fettling_item.flag_select == True:
						if entry.partner_id.id !=  fettling_item.invoice_id.contractor_id.id:
							raise osv.except_osv(_('Warning!'),
								_('System not allow to different Contractor, Kindly Verify!!'))
						if entry.partner_id:
							account_id = entry.partner_id.property_account_payable.id
							if not account_id:
								raise osv.except_osv(_('Contractor Configuration Warning !!'),
									_('Contractor account should be configured !!'))											
							vals = {							
									'voucher_id': entry.id,
									'doc_no':fettling_item.invoice_id.name,
									'doc_date':fettling_item.invoice_date,								
									'account_id':account_id,		
									'credit':0.00,		
									'debit':fettling_item.current_amt,		
									'source':'fettling_bills',										
									'narration':entry.narration,								
									}
									
							voucher_line_id = voucher_line_obj.create(cr, uid,vals)	
						if entry.journal_id:							
							bank_account_id = entry.journal_id.default_debit_account_id.id 						
							if not bank_account_id:
								raise osv.except_osv(_('Bank Configuration Warning !!'),
									_('Bank account should be configured !!'))
							vals = {							
									'voucher_id': entry.id,
									'doc_no':fettling_item.invoice_id.name,
									'doc_date':fettling_item.invoice_date,								
									'account_id':bank_account_id,		
									'debit':0.00,
									'credit':fettling_item.current_amt,			
									'source':'fettling_bills',										
									'narration':entry.narration,							
									}
							voucher_line_id = voucher_line_obj.create(cr, uid,vals)
						if fettling_item.invoice_id.balance_receivable < fettling_item.current_amt:
							raise osv.except_osv(_('Current Amount Warning !!'),
									_('Current Amount greater than Invoice amount !!'))
						balance_amt = fettling_item.invoice_id.balance_receivable - fettling_item.current_amt	
						accounts_state = 'pending'
						if balance_amt == 0.00:
							accounts_state = 'paid'					
						fettling_obj.write(cr, uid, fettling_item.invoice_id.id, {'balance_receivable': balance_amt,'accounts_state':accounts_state})
						
			elif entry.payment_source == 'ms_sc_bills':	
				ms_cs_obj = self.pool.get('kg.subcontract.invoice')	
				cr.execute(""" select sum(id)
					from ch_ms_sc_bill_details  
					where flag_select = 't' and header_id = %s """%(entry.id))					
				total_lds = cr.fetchone();		
				if total_lds[0] is None:
					raise osv.except_osv(_('Warning!'),
						_('System not allow to without Purchase bill items !!'))				
				for ms_sc_item in entry.line_ids_f:
					if ms_sc_item.flag_select == True:
						if entry.partner_id.id !=  ms_sc_item.invoice_id.contractor_id.id:
							raise osv.except_osv(_('Warning!'),
								_('System not allow to different Contractor, Kindly Verify!!'))
						if entry.partner_id:
							account_id = entry.partner_id.property_account_payable.id
							if not account_id:
								raise osv.except_osv(_('Contractor Configuration Warning !!'),
									_('Contractor account should be configured !!'))											
							vals = {							
									'voucher_id': entry.id,
									'doc_no':ms_sc_item.invoice_id.name,
									'doc_date':ms_sc_item.invoice_date,								
									'account_id':account_id,		
									'credit':0.00,		
									'debit':ms_sc_item.current_amt,		
									'source':'ms_sc_bills',										
									'narration':entry.narration,								
									}
									
							voucher_line_id = voucher_line_obj.create(cr, uid,vals)	
						if entry.journal_id:							
							bank_account_id = entry.journal_id.default_debit_account_id.id 						
							if not bank_account_id:
								raise osv.except_osv(_('Bank Configuration Warning !!'),
									_('Bank account should be configured !!'))
							vals = {							
									'voucher_id': entry.id,
									'doc_no':ms_sc_item.invoice_id.name,
									'doc_date':ms_sc_item.invoice_date,								
									'account_id':bank_account_id,		
									'debit':0.00,
									'credit':ms_sc_item.current_amt,			
									'source':'ms_sc_bills',										
									'narration':entry.narration,							
									}
							voucher_line_id = voucher_line_obj.create(cr, uid,vals)
						if ms_sc_item.invoice_id.balance_receivable < ms_sc_item.current_amt:
							raise osv.except_osv(_('Current Amount Warning !!'),
									_('Current Amount greater than Invoice amount !!'))
						balance_amt = ms_sc_item.invoice_id.balance_receivable - ms_sc_item.current_amt	
						accounts_state = 'pending'
						if balance_amt == 0.00:
							accounts_state = 'paid'					
						ms_cs_obj.write(cr, uid, ms_sc_item.invoice_id.id, {'balance_receivable': balance_amt,'accounts_state':accounts_state})
			elif entry.payment_source == 'salary':	
				cr.execute(""" select sum(id)
					from ch_salary_details  
					where flag_select = 't' and header_id = %s """%(entry.id))					
				total_lds = cr.fetchone();		
				if total_lds[0] is None:
					raise osv.except_osv(_('Warning!'),
						_('System not allow to without Salary items !!'))			
			elif entry.payment_source == 'direct_bills':
				direct_exp_obj = self.pool.get('direct.entry.expense')		
				cr.execute(""" select sum(id)
					from ch_direct_bill_details  
					where flag_select = 't' and header_id = %s """%(entry.id))					
				total_lds = cr.fetchone();		
				if total_lds[0] is None:
					raise osv.except_osv(_('Warning!'),
						_('System not allow to without Purchase bill items !!'))				
				for direct_exp_item in entry.line_ids_h:
					if direct_exp_item.flag_select == True:
						if entry.partner_id.id !=  direct_exp_item.invoice_id.supplier_id.id:
							raise osv.except_osv(_('Warning!'),
								_('System not allow to different Supplier, Kindly Verify!!'))
						if entry.partner_id:
							account_id = entry.partner_id.property_account_payable.id
							if not account_id:
								raise osv.except_osv(_('Supplier Configuration Warning !!'),
									_('Supplier account should be configured !!'))											
							vals = {							
									'voucher_id': entry.id,
									'doc_no':direct_exp_item.invoice_id.name,
									'doc_date':direct_exp_item.invoice_date,								
									'account_id':account_id,		
									'credit':0.00,		
									'debit':direct_exp_item.current_amt,		
									'source':'purchase_bills',										
									'narration':entry.narration,								
									}
									
							voucher_line_id = voucher_line_obj.create(cr, uid,vals)	
						if entry.journal_id:							
							bank_account_id = entry.journal_id.default_debit_account_id.id 						
							if not bank_account_id:
								raise osv.except_osv(_('Bank Configuration Warning !!'),
									_('Bank account should be configured !!'))
							vals = {							
									'voucher_id': entry.id,
									'doc_no':direct_exp_item.invoice_id.name,
									'doc_date':direct_exp_item.invoice_date,								
									'account_id':bank_account_id,		
									'debit':0.00,
									'credit':direct_exp_item.current_amt,			
									'source':'purchase_bills',										
									'narration':entry.narration,							
									}
							voucher_line_id = voucher_line_obj.create(cr, uid,vals)
						if direct_exp_item.invoice_id.balance_receivable < direct_exp_item.current_amt:
							raise osv.except_osv(_('Current Amount Warning !!'),
									_('Current Amount greater than Invoice amount !!'))
						balance_amt = direct_exp_item.invoice_id.balance_receivable - direct_exp_item.current_amt	
						accounts_state = 'pending'
						if balance_amt == 0.00:
							accounts_state = 'paid'					
						direct_exp_obj.write(cr, uid, direct_exp_item.invoice_id.id, {'balance_receivable': balance_amt,'accounts_state':accounts_state})
						
			elif entry.payment_source == 'credit_note':	
				credit_obj = self.pool.get('kg.credit.note')
				cr.execute(""" select sum(id)
					from ch_credit_note_details  
					where flag_select = 't' and header_id = %s """%(entry.id))					
				total_lds = cr.fetchone();		
				if total_lds[0] is None:
					raise osv.except_osv(_('Warning!'),
						_('System not allow to without Purchase bill items !!'))				
				for credit_item in entry.line_ids_j:
					if credit_item.flag_select == True:
						if entry.partner_id.id !=  credit_item.credit_id.supplier_id.id:
							raise osv.except_osv(_('Warning!'),
								_('System not allow to different Supplier, Kindly Verify!!'))
						if entry.partner_id:
							account_id = entry.partner_id.property_account_payable.id
							if not account_id:
								raise osv.except_osv(_('Supplier Configuration Warning !!'),
									_('Supplier account should be configured !!'))											
							vals = {							
									'voucher_id': entry.id,
									'doc_no':credit_item.credit_id.name,
									'doc_date':credit_item.credit_date,								
									'account_id':account_id,		
									'credit':0.00,		
									'debit':credit_item.current_amt,		
									'source':'purchase_bills',										
									'narration':entry.narration,								
									}
									
							voucher_line_id = voucher_line_obj.create(cr, uid,vals)	
						if entry.journal_id:							
							bank_account_id = entry.journal_id.default_debit_account_id.id 						
							if not bank_account_id:
								raise osv.except_osv(_('Bank Configuration Warning !!'),
									_('Bank account should be configured !!'))
							vals = {							
									'voucher_id': entry.id,
									'doc_no':credit_item.credit_id.name,
									'doc_date':credit_item.credit_date,								
									'account_id':bank_account_id,		
									'debit':0.00,
									'credit':credit_item.current_amt,			
									'source':'purchase_bills',										
									'narration':entry.narration,							
									}
							voucher_line_id = voucher_line_obj.create(cr, uid,vals)
						if credit_item.credit_id.balance_receivable < credit_item.current_amt:
							raise osv.except_osv(_('Current Amount Warning !!'),
									_('Current Amount greater than Invoice amount !!'))
						balance_amt = credit_item.credit_id.balance_receivable - credit_item.current_amt	
						accounts_state = 'pending'
						if balance_amt == 0.00:
							accounts_state = 'paid'					
						credit_obj.write(cr, uid, credit_item.credit_id.id, {'balance_receivable': balance_amt,'accounts_state':accounts_state})
						
		
		self.write(cr, uid, ids, {'name':voucher_name,'state': 'proforma','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True	
	
	def entry_post(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])			
		if rec.state == 'proforma':	
			if rec.default_type == 'receipt':											
				## Receipt Account Posting Process Start here
				vou_obj = self.pool.get('account.voucher')				
				move_vals = {
							'name':rec.name,
							'journal_id':rec.journal_id.id,
							'narration':rec.narration,
							'source_id':rec.id,
							'date':rec.entry_date,
							'division_id':rec.division_id.id,
							'trans_type':'REC',
							}			
				move_id = vou_obj.create_account_move(cr,uid,move_vals)				
				cr.execute(""" select account_id,sum(credit),sum(debit)
								from account_voucher_line  
								where voucher_id = %s
								group by account_id """%(rec.id))					
				account_create= cr.fetchall();						
				for voucher in account_create:							
					if voucher[2] > 0.00:
						debit_amt = voucher[2]
						account_ids = voucher[0]
						credit_amt = 0.00
					if voucher[1] > 0.00:
						debit_amt = 0.00
						account_ids = voucher[0]
						credit_amt = voucher[1]				
					move_line_vals = {
						'move_id': move_id,
						'account_id': account_ids,
						'credit': credit_amt,
						'debit': debit_amt,					
						'journal_id': rec.journal_id.id,						
						'date': rec.entry_date,
						'name': rec.name,
						}
					move_line_id = vou_obj.create_account_move_line(cr,uid,move_line_vals)
				## Receipt Account Posting Process End Here			
			elif rec.default_type == 'payment':	
				## Payment Account Posting Process Start here
				vou_obj = self.pool.get('account.voucher')				
				move_vals = {
							'name':rec.name,
							'journal_id':rec.journal_id.id,
							'narration':rec.narration,
							'source_id':rec.id,
							'date':rec.entry_date,
							'division_id':rec.division_id.id,
							'trans_type':'PAY',
							}			
				move_id = vou_obj.create_account_move(cr,uid,move_vals)				
				cr.execute(""" select account_id,sum(credit),sum(debit)
								from account_voucher_line  
								where voucher_id = %s
								group by account_id """%(rec.id))					
				account_create= cr.fetchall();						
				for voucher in account_create:						
					if voucher[1] > 0.00:
						debit_amt = 0.00
						account_ids = voucher[0]
						credit_amt = voucher[1]	
					if voucher[2] > 0.00:
						debit_amt = voucher[2]
						account_ids = voucher[0]
						credit_amt = 0.00			
					move_line_vals = {
						'move_id': move_id,
						'account_id': account_ids,
						'credit': credit_amt,
						'debit': debit_amt,					
						'journal_id': rec.journal_id.id,						
						'date': rec.entry_date,
						'name': rec.name,
						}
					move_line_id = vou_obj.create_account_move_line(cr,uid,move_line_vals)
				## Payment Account Posting Process End Here
			self.write(cr, uid, ids, {'state': 'posted','post_user_id': uid, 'post_date': time.strftime('%Y-%m-%d %H:%M:%S')})	
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
		return super(kg_account_voucher, self).write(cr, uid, ids, vals, context)
	
	
	## Account Move and Move Line General Create Function
	
	def create_account_move(self,cr,uid,move_vals,context=None):		
		move_obj = self.pool.get('account.move')
		perd_obj = self.pool.get('account.period')
		period_ids = perd_obj.search(cr,uid,[('date_start','<=',move_vals['date']),('date_stop','>=',move_vals['date']),('special','!=',True)])
		if period_ids:
			perd_rec = perd_obj.browse(cr,uid,period_ids[0])			
		move_id = move_obj.create(cr,uid,{
										'name': move_vals['name'],
										'journal_id': move_vals['journal_id'],
										'period_id': perd_rec.id,
										'narration': move_vals['narration'],
										'source_id': move_vals['source_id'],
										'date': move_vals['date'],
										'division_id': move_vals['division_id'],
										'trans_type': move_vals['trans_type'],
										'entry_mode': 'auto',
										'state': 'posted',
										})

		return move_id
	
	def create_account_move_line(self,cr,uid,move_line_vals,context=None):
		move_line_obj = self.pool.get('account.move.line')
		perd_obj = self.pool.get('account.period')
		period_ids = perd_obj.search(cr,uid,[('date_start','<=',move_line_vals['date']),('date_stop','>=',move_line_vals['date']),('special','!=',True)])
		if period_ids:
			perd_rec = perd_obj.browse(cr,uid,period_ids[0])
		move_line_id = move_line_obj.create(cr,uid,{
										'move_id': move_line_vals['move_id'],
										'account_id': move_line_vals['account_id'],
										'credit': move_line_vals['credit'],
										'debit': move_line_vals['debit'],										
										'state': 'draft',
										'journal_id': move_line_vals['journal_id'],
										'period_id': perd_rec.id,
										'date': move_line_vals['date'],
										'name': move_line_vals['name'],
										})
		
		return True
	
	
kg_account_voucher()


 ### Receipt Child Tables start here 
   
class ch_sale_invoice_details(osv.osv):
	
	_name = "ch.sale.invoice.details"
	_description = "Sales Invoice Details"
	
	_columns = { 
				
		'header_id':fields.many2one('account.voucher', 'Account Voucher', required=True, ondelete='cascade'),
		'invoice_id': fields.many2one('kg.sale.invoice','Invoice No', required=True),	
		'invoice_date': fields.date('Invoice Date',required=True),			
		'invoice_amt': fields.float('Invoice Amount' ),	
		'balance_amt': fields.float('Balance Amount' ),	
		'current_amt': fields.float('Current Amount' ),	
		'flag_select': fields.boolean('Select'),		
		
	}
	
	_defaults = {
	
		'flag_select': True,
		
	}	
	
ch_sale_invoice_details()


class ch_customer_advance_details(osv.osv):
	
	_name = "ch.customer.advance.details"
	_description = "Advance Details"
	
	_columns = {  
			
		'header_id':fields.many2one('account.voucher', 'Account Voucher', required=True, ondelete='cascade'),
		'advance_id': fields.many2one('kg.customer.advance','Advance No', required=True),	
		'advance_date': fields.date('Advance Date',required=True),			
		'advance_amt': fields.float('Advance Amount' ),	
		'balance_amt': fields.float('Balance Amount' ),	
		'current_amt': fields.float('Current Amount' ),	
		'flag_select': fields.boolean('Select'),		
		
	}
	
	_defaults = {
	
		'flag_select': True,
		
	}	
	
ch_customer_advance_details()


 ### Payment Child Tables start here 

class ch_purchase_bill_details(osv.osv):
	
	_name = "ch.purchase.bill.details"
	_description = "Purchase Bill Details"
	
	_columns = {  
			
		'header_id':fields.many2one('account.voucher', 'Account Voucher', required=True, ondelete='cascade'),
		'invoice_id': fields.many2one('kg.purchase.invoice','Invoice No', required=True),	
		'invoice_date': fields.date('Invoice Date',required=True),			
		'due_date': fields.date('Due Date',required=True),			
		'sup_invoice_no': fields.char('Sup.Invoice No.',required=True),			
		'invoice_amt': fields.float('Invoice Amount' ),	
		'balance_amt': fields.float('Balance Amount' ),	
		'current_amt': fields.float('Current Amount' ),	
		'flag_select': fields.boolean('Select'),		
		
	}
	
	_defaults = {
	
		'flag_select': True,
		
	}	
	
ch_purchase_bill_details()

class ch_supplier_advance_details(osv.osv):
	
	_name = "ch.supplier.advance.details"
	_description = "Advance Details"
	
	_columns = {  
			
		'header_id':fields.many2one('account.voucher', 'Account Voucher', required=True, ondelete='cascade'),
		'advance_id': fields.many2one('kg.supplier.advance','Advance No', required=True),	
		'advance_date': fields.date('Advance Date',required=True),			
		'advance_amt': fields.float('Advance Amount' ),	
		'balance_amt': fields.float('Balance Amount' ),	
		'current_amt': fields.float('Current Amount' ),	
		'flag_select': fields.boolean('Select'),		
		
	}
	
	_defaults = {
	
		'flag_select': True,
		
	}	
	
ch_supplier_advance_details()

class ch_fettling_bill_details(osv.osv):
	
	_name = "ch.fettling.bill.details"
	_description = "Fettling Bill Details"
	
	_columns = {  
			
		'header_id':fields.many2one('account.voucher', 'Account Voucher', required=True, ondelete='cascade'),
		'invoice_id': fields.many2one('kg.foundry.invoice','Invoice No', required=True),	
		'invoice_date': fields.date('Invoice Date',required=True),			
		'due_date': fields.date('Due Date',required=True),			
		'sup_invoice_no': fields.char('Sup.Invoice No.',required=True),			
		'invoice_amt': fields.float('Invoice Amount' ),	
		'balance_amt': fields.float('Balance Amount' ),	
		'current_amt': fields.float('Current Amount' ),	
		'flag_select': fields.boolean('Select'),		
		
	}
	
	_defaults = {
	
		'flag_select': True,
		
	}	
	
ch_fettling_bill_details()

class ch_ms_sc_bill_details(osv.osv):
	
	_name = "ch.ms.sc.bill.details"
	_description = "MS SC Bill Details"
	
	_columns = {  
			
		'header_id':fields.many2one('account.voucher', 'Account Voucher', required=True, ondelete='cascade'),
		'invoice_id': fields.many2one('kg.subcontract.invoice','Invoice No', required=True),	
		'invoice_date': fields.date('Invoice Date',required=True),			
		'due_date': fields.date('Due Date',required=True),			
		'sup_invoice_no': fields.char('Sup.Invoice No.',required=True),			
		'invoice_amt': fields.float('Invoice Amount' ),	
		'balance_amt': fields.float('Balance Amount' ),	
		'current_amt': fields.float('Current Amount' ),	
		'flag_select': fields.boolean('Select'),		
		
	}
	
	_defaults = {
	
		'flag_select': True,
		
	}	
	
ch_ms_sc_bill_details()

class ch_salary_details(osv.osv):
	
	_name = "ch.salary.details"
	_description = "Salary Details"
	
	_columns = {  
			
		'header_id':fields.many2one('account.voucher', 'Account Voucher', required=True, ondelete='cascade'),
		'employee_id': fields.many2one('hr.employee','Employee Name', required=True),	
		'employee_code': fields.char('Employee code',required=True),			
		'month': fields.char('Month',required=True),	
		'salary_amt': fields.float('Salary Amount' ),	
		'current_amt': fields.float('Current Amount' ),	
		'flag_select': fields.boolean('Select'),		
		
	}
	
	_defaults = {
	
		'flag_select': True,
		
	}	
	
ch_salary_details()

class ch_direct_bill_details(osv.osv):
	
	_name = "ch.direct.bill.details"
	_description = "Direct Bill Details"
	
	_columns = {  
			
		'header_id':fields.many2one('account.voucher', 'Account Voucher', required=True, ondelete='cascade'),
		'invoice_id': fields.many2one('direct.entry.expense','Invoice No', required=True),	
		'invoice_date': fields.date('Invoice Date',required=True),			
		'due_date': fields.date('Due Date',required=True),			
		'sup_invoice_no': fields.char('Sup.Invoice No.',required=True),			
		'invoice_amt': fields.float('Invoice Amount' ),	
		'balance_amt': fields.float('Balance Amount' ),	
		'current_amt': fields.float('Current Amount' ),	
		'flag_select': fields.boolean('Select'),			
	}	
	
	_defaults = {	
		'flag_select': True,		
	}	
		
ch_direct_bill_details()

class ch_tds_details(osv.osv):
	
	_name = "ch.tds.details"
	_description = "TDS Details"
	
	_columns = {  
			
		'header_id':fields.many2one('account.voucher', 'Account Voucher', required=True, ondelete='cascade'),		
		'tds_section_no': fields.char('TDS Section No',required=True),			
		'basis_type': fields.char('Basis Type',required=True),			
		'tds_deducted': fields.float('Total Amount To Be Deducted For TDS' ),	
		'tds_deducted_amt': fields.float('TDS Deducted Amount' ),		
		'flag_select': fields.boolean('Select'),			
	}	
	
	_defaults = {	
		'flag_select': True,		
	}	
		
ch_tds_details()

class ch_credit_note_details(osv.osv):
	
	_name = "ch.credit.note.details"
	_description = "Credit Note Details"
	
	_columns = {  
			
		'header_id':fields.many2one('account.voucher', 'Account Voucher', required=True, ondelete='cascade'),
		'credit_id': fields.many2one('kg.credit.note','Credit Note No', required=True),	
		'credit_date': fields.date('Credit Date',required=True),				
		'credit_amt': fields.float('Amount' ),	
		'balance_amt': fields.float('Balance Amount' ),	
		'current_amt': fields.float('Current Amount' ),	
		'flag_select': fields.boolean('Select'),			
	}	
	
	_defaults = {	
		'flag_select': True,		
	}		
	
ch_credit_note_details()




