from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_cash_voucher(osv.osv):
	
	_name = "kg.cash.voucher"
	_description = "Cash Voucher"
	
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
					as sam  """ %('kg_cash_voucher'))
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
		
		'name':fields.char('Voucher Name'),	
		'voucher_date':fields.date('Voucher Date'),	
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
		'name':fields.char('Name'),	
		'voucher_date':fields.date('Date'),
		'pay_mode':fields.selection([('from_ac','From AC'),('from_emp','From Employee')],'Payment Mode'),
		'employee_id':fields.many2one('hr.employee','Employee'),
		'amount':fields.float('Amount'),
		'paid_to':fields.char('Paid To'),	
		'acc_journal_id':fields.many2one('account.journal','Cash Account'),
		'narration': fields.text('Narration'),
		'division_id':fields.many2one('kg.division.master','Division'),
		
		## Child Tables Declaration
		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.cash.voucher', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Name must be unique per Company !!'),
	]
	
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
			seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.cash.voucher')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,rec.voucher_date))
			vou_no = cr.fetchone();
			vou_no = vou_no[0]
			self.write(cr, uid, ids, {'name':vou_no,'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
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
			if rec.pay_mode == 'from_emp':
				print "++++++++++++++++++++++++++",rec.employee_id.id
				cr.execute('''select sum(bal_amt) from kg_emp_cash_issue where employee_id =%s'''%(rec.employee_id.id))
				tot_bal_amt = cr.dictfetchone()
				print "Balance amount...............................",tot_bal_amt['sum']
				if rec.amount > tot_bal_amt['sum']:
					raise osv.except_osv(_('Warning'),
						_('Entered Amount is exceeding the Total Balance amount of %s !!')%(tot_bal_amt['sum']))
				else:
					pay_issue_ser = self.pool.get('kg.emp.cash.issue').search(cr,uid,[('employee_id','=',rec.employee_id.id),('bal_amt','!=',0.00),('state','=','approved')])
					print "----------------------------------------------------------",pay_issue_ser
					if pay_issue_ser:
						index = 0
						for cash_id in pay_issue_ser:
							pay_issue_rec = self.pool.get('kg.emp.cash.issue').browse(cr,uid,pay_issue_ser[index])
							cash_bal_amt = pay_issue_rec.bal_amt
							print"indexindexindex",index
							if index == 0:
								rec_amt = rec.amount
							else:
								rec_amt = -(bal_amt)
							print"rec_amtrec_amt",rec_amt
							if rec_amt <= cash_bal_amt:
								print"aaaaaaaaaaaaaA"
								bal_amt = cash_bal_amt - rec_amt
								self.pool.get('kg.emp.cash.issue').write(cr,uid,pay_issue_rec.id,{'bal_amt':bal_amt})
								break
							elif rec_amt > cash_bal_amt:
								print"bbbbbbbbb"
								bal_amt = cash_bal_amt - rec_amt
							else:
								print"ccccccccccccccccc"
								pass
							if bal_amt < 0:
								self.pool.get('kg.emp.cash.issue').write(cr,uid,pay_issue_rec.id,{'bal_amt':0})
								index = index + 1
								print"index-----------------1",index
					else:
						raise osv.except_osv(_('Warning'),
							_('Amount Not yet Issued !!!'))
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
		return super(kg_cash_voucher, self).write(cr, uid, ids, vals, context)	
	
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

kg_cash_voucher()
