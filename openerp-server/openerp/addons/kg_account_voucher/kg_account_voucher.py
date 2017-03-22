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
		'sub_mode':fields.selection([('dd', 'DD'),('cheque', 'Cheque'),('neft', 'NEFT'),('rtgs', 'RTGS'),('others', 'Others')], 'Sub Mode', required=True),
		'reference_no': fields.char('Ref.No'),
		'cheque_in_favor': fields.char('CHEQUE IN FAVOR OF'),
		'receipt_source':fields.selection([('advance', 'Advance'),('sales_invoice', 'Sales Invoice')], 'Receipt Source'),
		
		'book_current_bal': fields.float('Book Current Balance', readonly=True),
		'default_type':fields.selection([('receipt', 'Receipt'),('payment', 'Payment')], 'Default Type'),
		'voucher_amt': fields.float('Voucher Amount', readonly=True),
		
		
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
	
	
	def onchange_cheque_in_favor(self, cr, uid, ids, partner_id,sub_mode, context=None):
		
		value = {'cheque_in_favor': ''}
		
		if sub_mode == 'cheque':
			if partner_id:				
				cheque_rec = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
				value = {'cheque_in_favor': cheque_rec.name}
			
		return {'value': value}
	
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])		
		voucher_name = ''
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
		self.write(cr, uid, ids, {'name':voucher_name,'state': 'proforma','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
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
	
ch_fettling_bill_details()

class ch_ms_sc_bill_details(osv.osv):
	
	_name = "ch.ms.sc.bill.details"
	_description = "MS SC Bill Details"
	
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




