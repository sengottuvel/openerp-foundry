from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
import base64
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_bank_statement(osv.osv):
	
	_name = "kg.bank.statement"
	_description = "Bank Statement"
	
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
					as sam  """ %('kg_bank_statement'))
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
		'acc_journal_id':fields.many2one('account.journal','Bank Account'),
		'clear_date':fields.date('Clearing Date'),
		'open_bal':fields.float('Opening Balance'),
		'calc_close_bal':fields.float('Calculated Closing Balance'),
		'actual_close_bal':fields.float('Actual Closing Balance'),
		'open_bal_type':fields.selection([('dr','Dr'),('cr','Cr')],'Dr/Cr'),
		'calc_close_bal_type':fields.selection([('dr','Dr'),('cr','Cr')],'Dr/Cr'),
		'actual_close_bal_type':fields.selection([('dr','Dr'),('cr','Cr')],'Dr/Cr'),
		'division_id':fields.many2one('kg.division.master','Division'),
		'acct_name':fields.many2one('account.account','Account Name'),
		#~ 'bnk_imp_id':fields.many2one('kg.bank.statement.import','Bank Statement Import'),
		
		## Child Tables Declaration
		
		'line_id':fields.one2many('ch.bank.statement','header_id','Line id',readonly=True, states={'draft':[('readonly',False)]}),
		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.bank.statement', context=c),
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
		if not rec.line_id:
			raise osv.except_osv(_('Warning!'),
				_('Bank Statement Details should not be empty !!'))
		for line_ids in rec.line_id:
			if (line_ids.debit == 0.00 and line_ids.credit == 0.00):
				raise osv.except_osv(_('Warning!'),
					_('Debit and credit should not be zero for Cheque No/Ref No %s !!'%(line_ids.cheque_no)))
			elif (line_ids.debit != 0.00 and line_ids.credit != 0.00):
				raise osv.except_osv(_('Warning!'),
					_('Both Debit and credit should not contain value for Cheque No/Ref No %s !!'%(line_ids.cheque_no)))
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
		return super(kg_bank_statement, self).write(cr, uid, ids, vals, context)	

	## Module Requirement
	
	def onchange_account(self,cr,uid,ids,acc_journal_id,acct_name,context=None):
		led_rec = self.pool.get('account.journal').browse(cr,uid,acc_journal_id)
		value = {'acct_name':led_rec.default_debit_account_id.id}
		return {'value': value}
	
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_code = str(rec.clear_date)		
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
			
		url = 'http://192.168.1.7/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&bank_statement_entry='+rec_code

		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
	
kg_bank_statement()

class ch_bank_statement(osv.osv):
	
	_name = "ch.bank.statement"
	_description = "Bank Statement Line"
	
	_columns = {

	'header_id':fields.many2one('kg.bank.statement','Header id'),
	'partner_id':fields.many2one('res.partner','Party Name',domain=[('partner_state','=','approve')]),
	'employee_id':fields.many2one('hr.employee','Employee',domain=[('status','=','approved')]),
	'cheque_no':fields.char('Cheque No/Ref No'),
	'debit':fields.float('Debit'),
	'credit':fields.float('Credit'),
	'narration':fields.text('Narration'),
	'partner_flag':fields.boolean('Partner Flag'),
	'employee_flag':fields.boolean('Employee Flag'),
	
	}
	
	def onchange_partner_id(self,cr,uid,ids,partner_id):
		return {'value': {'partner_flag':True}}
		
	def onchange_employee_id(self,cr,uid,ids,employee_id):
		return {'value': {'employee_flag':True}}
		
ch_bank_statement()	
