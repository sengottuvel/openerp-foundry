from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_emp_cash_issue(osv.osv):
	
	_name = "kg.emp.cash.issue"
	_description = "Employee Cash Issue"
	
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
					as sam  """ %('kg_emp_cash_isssue'))
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
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),

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
		
		'employee_id':fields.many2one('hr.employee','Employee'),
		'emp_code':fields.char('Code'),
		'dep_id':fields.many2one('kg.depmaster','Department'),
		'given_bal_amt':fields.float('Given Balance Amount'),
		'amount':fields.float('Amount'),
		'entry_date':fields.date('Date'),
		'acc_journal_id':fields.many2one('account.journal','Cash Account',domain=[('type','=','cash')]),
		'bal_amt':fields.float('Balance Amount'),
		'narration': fields.text('Narration'),
		'division_id':fields.many2one('kg.division.master','Division'),
		
		## Child Tables Declaration
		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.emp.cash.issue', context=c),
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
		if rec.amount != rec.bal_amt:
			raise osv.except_osv(_('Warning'),
					_('Record refered in Cash Voucher !!'))
		else:
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
			
			###### Account Posting occurs #########
			
			journal_obj = self.pool.get('account.journal')
			journal_ids = self.pool.get('account.journal').search(cr,uid,[('type','=','purchase')])	
			if journal_ids == []:
				raise osv.except_osv(_('Book Configuration Warning !!'),
					_('Type is purchase book should be created !!'))		
			journal_rec = self.pool.get('account.journal').browse(cr,uid,journal_ids[0])
			
			vou_obj = self.pool.get('account.voucher')				
			move_vals = {
						'name':'Employee Cash Issue',
						'journal_id':journal_rec.id,
						'narration':rec.narration,
						'source_id':rec.id,
						'date':rec.entry_date,
						'division_id':rec.division_id.id,
						'trans_type':'EC',
						}			
			move_id = vou_obj.create_account_move(cr,uid,move_vals)	
	
			ex_account_id = rec.acc_journal_id.default_debit_account_id.id	
			if not ex_account_id:
				raise osv.except_osv(_('Cash Account Configuration Warning !!'),
					_('Cash Account should be configured !!'))
			move_line_vals = {
					'move_id': move_id,
					'account_id': ex_account_id,
					'credit': rec.amount,
					'debit': 0.00,					
					'journal_id': journal_rec.id,						
					'date': rec.entry_date,
					'name': 'Employee Cash Issue',
					}
			move_line_id = vou_obj.create_account_move_line(cr,uid,move_line_vals)		
			if rec.employee_id:
				account_id = rec.employee_id.account_id.id
				print"account_idaccount_id",account_id
				if not account_id:
					raise osv.except_osv(_('Employee Configuration Warning !!'),
						_('Employee account should be configured !!'))
				credit = 0.00
				debit = rec.amount
				move_line_vals = {
						'move_id': move_id,
						'account_id': account_id,
						'credit': credit,
						'debit': debit,					
						'journal_id': journal_rec.id,						
						'date': rec.entry_date,
						'name': 'Employee Cash Issue',
						}
				move_line_id = vou_obj.create_account_move_line(cr,uid,move_line_vals)
			
			###### Account Posting occurs #########
			
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
		return super(kg_emp_cash_issue, self).write(cr, uid, ids, vals, context)	
		
	####Validations####
	
	def  _validations (self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.amount <= 0.00:
			raise osv.except_osv(_('Warning!'),
				_('The Amount should not be less than or equal to zero !!'))
			return False
		return True
		
	_constraints = [

		(_validations, 'validations', [' ']),		
		
	]
	
	
	## Module Requirement
	
	def onchange_employee_id(self,cr,uid,ids,employee_id,emp_code,dep_id,context=None):
		value = {'emp_code': '','dep_id': '','given_bal_amt':'','division_id':''}
		emp = self.pool.get('hr.employee').browse(cr, uid, employee_id, context=context)
		cr.execute('''select sum(bal_amt) from kg_emp_cash_issue where employee_id=%s'''%(employee_id))
		bal_amount = cr.dictfetchone()
		if bal_amount['sum'] == None:
			bal_amount['sum']=0.00
		value = {
			'emp_code':emp.code,
			'dep_id':emp.dep_id.id,
			'given_bal_amt':bal_amount['sum'],
			'division_id':emp.division_id.id
		}
		return {'value': value}
		
	def onchange_amount(self,cr,uid,ids,amount,bal_amt,context=None):
		print "amount",amount
		value = {'bal_amt':amount}
		return {'value': value}
	
kg_emp_cash_issue()
