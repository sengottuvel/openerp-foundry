from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_bank_reconcile(osv.osv):
	
	_name = "kg.bank.reconcile"
	_description = "Bank Reconcile"
	
	### Version 0.1
	
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
					as sam  """ %('kg_bank_reconcile'))
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
		
		### Version 0.2
		
	_columns = {
	
		## Basic Info

		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=False),

		## Entry Info
		
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
		
		## Module Requirement Info
		'division_id':fields.many2one('kg.division.master','Division'),
		'acct_name':fields.many2one('account.account','Account Name'),
		'acc_journal_id':fields.many2one('account.journal','Bank Account'),
		'as_on_date':fields.date('As On Date'),
		'trans_type':fields.selection([('all','All'),('payment','Payment'),('receipt','Receipt')],'Transaction Type'),
		'statement_total':fields.float('Statement Total'),
		'state_amt_type':fields.char('Dr/Cr'),
		'book_total':fields.float('Book Total'),
		'book_amt_type':fields.char('Dr/Cr'),
		'bank_charge':fields.float('Bank Charges'),
		'difference':fields.float('Difference'),
		'tolerance_amt':fields.float('Tolerance Amount'),
		'bank_charge_app':fields.boolean('Bank Charges Applicable to Party'),
		
		## Child Tables Declaration
		
		'line_id_1':fields.one2many('ch.bank.reconcile.statement','header_id_1','Line id 1',readonly=True, states={'draft':[('readonly',False)]}),
		'line_id_2':fields.one2many('ch.bank.reconcile.book','header_id_2','Line id 2',readonly=True, states={'draft':[('readonly',False)]}),
		'line_id_3':fields.one2many('ch.bank.reconcile.match','header_id_3','Line id 3',readonly=True, states={'draft':[('readonly',False)]}),
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.bank.reconcile', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		
	}
	
	## Basic Needs	
	
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

	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':			
			self.write(cr, uid, ids, {'state': 'draft'})
		else:
			pass
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			if rec.remark:
				self.write(cr, uid, ids, {'state': 'reject','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Rejection remark is must !!'),
					_('Enter the remarks in rejection remark field !!'))
		else:
			pass
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
		return super(kg_bank_reconcile, self).write(cr, uid, ids, vals, context)	
	
	## Module Requirement
	
	def onchange_account(self,cr,uid,ids,acc_journal_id,acct_name,context=None):
		led_rec = self.pool.get('account.journal').browse(cr,uid,acc_journal_id)
		value = {'acct_name':led_rec.default_debit_account_id.id}
		return {'value': value}
	
	def list(self,cr,uid,ids,context=None):
		return True
		
	def match(self,cr,uid,ids,context=None):
		return True
	
kg_bank_reconcile()

class ch_bank_reconcile_statement(osv.osv):
	
	_name = "ch.bank.reconcile.statement"
	_description = "Bank Statement Entry Line"
	
	_columns = {

	'header_id_1':fields.many2one('kg.bank.reconcile','Header id'),
	'cheque_no':fields.char('Cheque No/Ref No'),
	'cheque_date':fields.date('Cheque Date'),
	'debit':fields.float('Debit'),
	'credit':fields.float('Credit'),
	'amt_type':fields.selection([('cash','Cash'),('cheque','Cheque')],'Type'),
	'narration':fields.text('Narration')
	
	}
	
ch_bank_reconcile_statement()	

class ch_bank_reconcile_book(osv.osv):
	
	_name = "ch.bank.reconcile.book"
	_description = "Company Book Entry Line"
	
	_columns = {

	'header_id_2':fields.many2one('kg.bank.reconcile','Header id'),
	'cheque_no':fields.char('Cheque No/Ref No'),
	'post_no':fields.char('Post No'),
	'date':fields.date('Date'),
	'debit':fields.float('Debit'),
	'credit':fields.float('Credit'),
	'amt_type':fields.selection([('cash','Cash'),('cheque','Cheque')],'Type'),
	'narration':fields.text('Narration')
	
	}
	
ch_bank_reconcile_book()	

class ch_bank_reconcile_match(osv.osv):
	
	_name = "ch.bank.reconcile.match"
	_description = "Match Entry List"
	
	_columns = {

	'header_id_3':fields.many2one('kg.bank.reconcile','Header id'),
	'cheque_no':fields.char('Cheque No/Ref No'),
	'post_no':fields.char('Post No'),
	'bank_book':fields.char('Bank Book Ind'),
	'debit':fields.float('Debit Amount'),
	'credit':fields.float('Credit Amount'),
	'bank_charge':fields.selection([('cash','Cash'),('cheque','Cheque')],'Bank Charges'),
	'group_id':fields.char('Group ID')
	
	}
	
ch_bank_reconcile_book()	
