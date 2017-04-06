import math
import re
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
import netsvc
import datetime
import calendar
from datetime import date
import re
import urllib
import urllib2
import logging
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import calendar
today = datetime.now()
a = datetime.now()
dt_time = a.strftime('%m/%d/%Y %H:%M:%S')

class kg_direct_expense_entry(osv.osv):
	
	_name = 'direct.entry.expense'
	_description = "This form is to add the direct expense"
	_order = "expense_date desc"
	
	def _get_modify(self, cr, uid, ids, field_name, arg,  context=None):
		res={}
		if field_name == 'modify':
			for h in self.browse(cr, uid, ids, context=None):
				res[h.id] = 'no'
				if h.state == 'approved':
					cr.execute(""" select * from 
					(SELECT tc.table_schema, tc.constraint_name, tc.table_name, kcu.column_name, ccu.table_name
					AS foreign_table_name, ccu.column_name AS foreign_column_name
					FROM information_schema.table_constraints tc
					JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
					JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
					WHERE constraint_type = 'FOREIGN KEY'
					AND ccu.table_name='%s')
					as sam  """ %('direct_entry_expense'))
					data = cr.dictfetchall()	
					if data:
						for var in data:
							data = var
							chk_sql = 'Select COALESCE(count(*),0) as cnt from '+str(data['table_name'])+' where '+data['column_name']+' = '+str(ids[0])							
							cr.execute(chk_sql)			
							out_data = cr.dictfetchone()
							if out_data:								
								if out_data['cnt'] > 0:
									res[h.id] = 'no'
									return res
								else:
									res[h.id] = 'yes'
				else:
					res[h.id] = 'no'	
		return res	
	
	
	def _amount_line_tax(self, cr, uid, line, context=None):
		val = 0.0
		amt_to_per = (line.dis_amt / (1 * line.total_amt or 1.0 )) * 100
		print "---------------------------------",line.header_id.supplier_id
		for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id,
			line.total_amt * (1-(amt_to_per or 0.0)/100.0), 1, 4099,
			 line.header_id.supplier_id)['taxes']:			 
			val += c.get('amount', 0.0)
		return val
	
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'amount_untaxed': 0.0,
				'amount_tax': 0.0,
				'amount_total': 0.0,
				'discount' : 0.0,
				'other_charge': 0.0,
				'round_off': 0.0,
			}
			val = val1 = val3 = line_total = 0.0
			for line in order.line_ids:
				per_to_amt = line.total_amt
				tot_discount = line.dis_amt
				
				line_total += line.total_amt 
				val += self._amount_line_tax(cr, uid, line, context=context)
				val3 += tot_discount	
			res[order.id]['amount_tax']=val
			res[order.id]['amount_untaxed']=line_total
			res[order.id]['discount']=val3
			res[order.id]['round_off'] = order.round_off
			print "res[order.id]['amount_untaxed']res[order.id]['amount_untaxed']res[order.id]['amount_untaxed']res[order.id]['amount_untaxed']",type(res[order.id]['amount_untaxed'])

			res[order.id]['amount_total']=res[order.id]['amount_untaxed']+ res[order.id]['amount_tax'] - res[order.id]['discount'] + order.round_off or 0.00
		return res
	def _get_order(self, cr, uid, ids, context=None):
		result = {}
		for line in self.pool.get('direct.entry.expense.line').browse(cr, uid, ids, context=context):
			result[line.header_id.id] = True
		return result.keys()
	
	_columns = {
	
		'name':fields.char('Code'),
		'invoice_no':fields.char('Supplier Invoice No'),
		'expense_date':fields.date('Expense Date'),
		'invoice_date':fields.date('Supplier Invoice Date'),
		'supplier_id':fields.many2one('res.partner','Supplier'),
		'Supplier_add':fields.text('Supplier Address'),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'active':fields.boolean('Active'),'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'currency_id': fields.many2one('res.currency', 'Currency', readonly=True),
		'line_ids':fields.one2many('direct.entry.expense.line','header_id','Line Entry'),	
		'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
			store={
				'direct.entry.expense': (lambda self, cr, uid, ids, c={}: ids, ['line_ids'], 10),
				'direct.entry.expense.line': (_get_order, ['total_amt', 'tax_id', 'dis_amt',1], 10),
			}, multi="sums", help="The tax amount"),
		'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total',
			store=True,multi="sums",help="The total amount"),
		'discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Discount(-)',
			store={
				'direct.entry.expense': (lambda self, cr, uid, ids, c={}: ids, ['line_ids'], 10),
				'direct.entry.expense.line': (_get_order, ['total_amt', 'tax_id', 'dis_amt',1], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
			
		'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
			store={
				'direct.entry.expense': (lambda self, cr, uid, ids, c={}: ids, ['line_ids'], 10),
				'direct.entry.expense.line': (_get_order, ['total_amt', 'tax_id', 'dis_amt',1], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'payment_type': fields.selection([('cash', 'Cash'), ('credit', 'Credit')], 'Payment Type'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),	
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'notes': fields.text('Notes'),
		'division_id':fields.many2one('kg.division.master','Division'),	
		'round_off': fields.float('Round off',size=5,readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		
		'balance_receivable': fields.float('Balance Receivable'),		
		'accounts_state': fields.selection([('pending','Pending'),('paid','Paid')],'Accounts State', readonly=True),
			
			
			### Entry Info ###
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'active': fields.boolean('Active'),
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'ap_rej_date': fields.datetime('Approved/Rejected Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Rejected By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
			
	
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'direct.entry.expense', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		'accounts_state': 'pending',
	}
	
	def  _validations (self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.line_ids:
			line_expense = [ line.expense_id for line in rec.line_ids ]
			a= [line_expense.count(i) for i in line_expense ]
			for j in a:
				if j > 1:
					raise osv.except_osv(_('Warning!'),
								_('Duplicates are not allowed in Expense !!'))
			for line in rec.line_ids:
				if line.dis_amt < 0.00:
					raise osv.except_osv(_('Warning!'),
						_('The Discount Amount should not contain negative values !!'))
				if line.total_amt <=0.00:
					raise osv.except_osv(_('Warning!'),
						_('The Amount should not be less than or equal to zero !!'))
				
			#~ return False
		return True
		
	def button_dummy(self,cr,uid,ids,context=None):
		return True
	
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			if rec.cancel_remark:
				self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Cancel remark is must !!'),
					_('Enter the remarks in Cancel remarks field !!'))
		else:
			pass
		return True
	
	def entry_draft(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':	
			self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','direct.entry.expense')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,rec.expense_date))
			dir_exp_no = cr.fetchone();
			dir_exp_no = dir_exp_no[0]
			self.write(cr, uid, ids, {'name':dir_exp_no,'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		journal_obj = self.pool.get('account.journal')
		journal_ids = self.pool.get('account.journal').search(cr,uid,[('type','=','purchase')])	
		if journal_ids == []:
			raise osv.except_osv(_('Book Configuration Warning !!'),
				_('Type is purchase book should be created !!'))		
		journal_rec = self.pool.get('account.journal').browse(cr,uid,journal_ids[0])
		if rec.state == 'confirmed':
			## Account Posting Process Start
			vou_obj = self.pool.get('account.voucher')				
			move_vals = {
						'name':rec.name,
						'journal_id':journal_rec.id,
						'narration':rec.notes,
						'source_id':rec.id,
						'date':rec.expense_date,
						'division_id':rec.division_id.id,
						'trans_type':'DEJ',
						}			
			move_id = vou_obj.create_account_move(cr,uid,move_vals)	
			if rec.supplier_id:
				account_id = rec.supplier_id.property_account_payable.id
				print"account_idaccount_id",account_id
				if not account_id:
					raise osv.except_osv(_('Supplier Configuration Warning !!'),
						_('Supplier account should be configured !!'))
				credit = rec.amount_total
				debit = 0.00
				move_line_vals = {
						'move_id': move_id,
						'account_id': account_id,
						'credit': credit,
						'debit': debit,					
						'journal_id': journal_rec.id,						
						'date': rec.expense_date,
						'name': rec.name,
						}
				move_line_id = vou_obj.create_account_move_line(cr,uid,move_line_vals)	
			for expense in rec.line_ids:
				ex_account_id = expense.expense_id.account_id.id	
				print"ex_account_idex_account_id"	,ex_account_id	
				tax_obj = self.pool.get('account.tax')
				taxes = tax_obj.compute_all(cr, uid, expense.tax_id, (expense.total_amt-expense.dis_amt), 1, 1, partner=rec.supplier_id)			
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
						'date': rec.expense_date,
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
						'debit': expense.total_amt-expense.dis_amt,					
						'journal_id': journal_rec.id,						
						'date': rec.expense_date,
						'name': rec.name,
						}
				
				move_line_id = vou_obj.create_account_move_line(cr,uid,move_line_vals)
			
			self.write(cr, uid, ids, {'balance_receivable':rec.amount_total,'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			if rec.remark:
				self.write(cr, uid, ids, {'state': 'reject','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Rejection remark is must !!'),
					_('Enter the remarks in rejection remark field !!'))
		return True
		
		
	def onchange_supplier(self,cr,uid,ids,supplier_id):
		val = []
		sup_add = self.pool.get('res.partner').browse(cr,uid,supplier_id)
		tot_add = (sup_add.street or '')+ ',' + (sup_add.street2 or '') + ','+(sup_add.city_id.name or '')+ ',' +(sup_add.state_id.name or '') + '-' +(sup_add.zip or '') + 'Ph:' + (sup_add.phone or '')+ ',' +(sup_add.mobile or '')		
		return {'value': {'Supplier_add': tot_add}}

	def check_date(self,cr,uid,ids,context=None):
		read_date = self.read(cr,uid,ids,['invoice_date','expense_date'],context=context)
		for t in read_date:
			if t['invoice_date']>t['expense_date']:
				return False
			else:
				return True
		return True	
		
	def _check_lineitem(self, cr, uid, ids, context=None):
		print "called liteitem ___ function"
		indent = self.browse(cr,uid,ids[0])
		if not indent.line_ids:
			return False
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		if context is None:
			context={}
		indent = self.read(cr, uid, ids, ['state'], context=context)
		unlink_ids = []
		for t in indent:
			if t['state'] in ('draft'):
				unlink_ids.append(t['id'])
			else:
				raise osv.except_osv(('Invalid action !'),('System not allow to delete a UN-DRAFT state !!'))
		osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		return True
	
	_constraints = [(check_date,'The invoice date should not be greater the expense date',['']),
					(_check_lineitem,'Please enter the Expense Details',['']),
					(_validations, 'validations', [' ']),		
					]
	
	

kg_direct_expense_entry()



class ch_direct_expense_entry(osv.osv):
	_name='direct.entry.expense.line'
	_description='This is used to add notes about the company and some remarks'
	
	
	_columns={
	
		'header_id':fields.many2one('direct.entry.expense','Entry'),
		'expense_id':fields.many2one('kg.expense.master','Expense Description'),
		'dis_amt':fields.float('Discount Amount'),
		'tax_id': fields.many2many('account.tax', 'sol_taxes', 'sol_id', 'tax_id', 'Taxes'),
		'total_amt':fields.float('Amount'),
		'remarks':fields.char('Remarks'),
		
		
		
	
	}	
	
	_defaults = {
	
		
	
	}
	
	def _amount_line(self, cr, uid, ids, prop, arg, context=None):
		cur_obj=self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		res = {}
		if context is None:
			context = {}
		for line in self.browse(cr, uid, ids, context=context):
			amt_to_per = (line.dis_amt / (1 * line.total_amt or 1.0 )) * 100
			price = line.total_amt * (1 - (amt_to_per or 0.0) / 100.0)
			taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, 1, 4099, line.header_id.supplier_id)
			cur = line.header_id.supplier_id.property_product_pricelist_purchase.currency_id
			res[line.id] = cur_obj.round(cr, uid, cur, taxes['total_included'])
		return res  
		
ch_direct_expense_entry()
