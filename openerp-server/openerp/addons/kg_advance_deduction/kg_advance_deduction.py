from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_advance_deduction(osv.osv):

	_name = "kg.advance.deduction"
	_description = "Advance Detection"
	
	
	
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
					as sam  """ %('kg_advance_deduction'))
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
		
		
		
	
	_columns = {
	
		### Basic Info
			
		'code': fields.char('Code', size=10, required=True),		
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','AC ACK Pending'),('done','AC ACK Done'),('reject','AC Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),


		### Entry Info ###
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
		'done_date': fields.datetime('AC ACK Date', readonly=True),
		'done_user_id': fields.many2one('res.users', 'AC ACK By', readonly=True),
		
		## Module Requirement Info
		
		'employee_id': fields.many2one('hr.employee','Employee', required=True,readonly=True),
		'ded_type': fields.selection([('advance', 'Advance'),('loan', 'Loan'),('insurance', 'Insurance'),
						('tax', 'Tax'),('others','Others'),('cloth','Cloth')], 
						'Deduction Type'),
		'tot_amt': fields.float('Total Amount',),	
		'allow': fields.boolean('Applicable This Month'),
		'period': fields.integer('Repay Period'),
		'pay_amt': fields.float('Repay Amount'),
		'amt_paid': fields.float('Amount Paid So Far'),
		'bal_amt': fields.float('Balance Amount'),
		'round_bal': fields.float('Round Balance'),
		'emp_categ_id':fields.many2one('kg.employee.category','Employee Category'),
		
		## Child Tables Declaration		
		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.master', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		'allow': True,
		
	}
	
	
	### Basic Needs
	
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			if rec.cancel_remark:
				self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Cancel remark is must !!'),
					_('Enter the remarks in Cancel remarks field !!'))
		else:
			raise osv.except_osv(_('Warning!!!'),
				_('Confirm the record to proceed further'))
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state ==  'draft':
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Warning!!!'),
					_('The Record is not in draft !!!!!!'))
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'cancel':
			self.write(cr, uid, ids, {'state': 'draft'})
		else:
			raise osv.except_osv(_('Warning!!!'),
					_('Confirm the record to proceed further'))
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Warning!!!'),
					_('Confirm the record to proceed further'))
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			if rec.remark:
				self.write(cr, uid, ids, {'state': 'reject','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Rejection remark is must !!'),
					_('Enter the remarks in rejection remark field !!'))
		else:
			raise osv.except_osv(_('Warning!!!'),
					_('Confirm the record to proceed further'))
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
		return super(kg_advance_deduction, self).write(cr, uid, ids, vals, context)
		
	
	
	## Module Requirement
	
	def onchange_employee_id(self, cr, uid, ids, employee_id,code, context=None):
		value = {'code': '','emp_categ_id':''}
		if employee_id:
			emp = self.pool.get('hr.employee').browse(cr, uid, employee_id, context=context)
			value = {'code': emp.code,'emp_categ_id':emp.emp_categ_id.id}
		return {'value': value}
		
	def onchange_repay_amount(self,cr,uid,ids ,tot_amt, period,context = None):
		value = {'pay_amt' : (tot_amt/period),
						'bal_amt' : tot_amt,}
		return {'value' : value}
		
	def entry_accept(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			self.write(cr, uid, ids, {'state': 'done','done_user_id': uid, 'done_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
	
	###Validations###
	
	def _duplicate_validation(self, cr, uid, ids, context=None):
		ded_obj = self.pool.get('kg.advance.deduction')
		for entry in self.browse(cr, uid, ids):
			dup_ids = ded_obj.search(cr, uid,[('employee_id','=',entry.employee_id.id),
						('ded_type','=',entry.ded_type),('state','=','confirm')])
			if len(dup_ids) > 1:
				return False
		return True		
		
	def _total_amount_validation(self, cr, uid, ids, context=None):
		for entry in self.browse(cr, uid, ids):
			if entry.tot_amt > 0:
				return True
		return False
		
	def _repay_validation(self,cr,uid,ids,context=None):
		for entry in self.browse(cr, uid, ids):
			due_amt = entry.period * entry.pay_amt
			if due_amt > entry.tot_amt:
				return False
		return True
		
	_constraints = [
		
		(_duplicate_validation, 'System not allow to save duplicate entries. Check Employee and Deduction Type !!',['amount']),
		(_total_amount_validation, 'Total Amount should be greater than zero !!',['  ']),
		(_repay_validation, 'Repay amount and periods are not matching !!',['  ']),
		
		] 
	
kg_advance_deduction()
