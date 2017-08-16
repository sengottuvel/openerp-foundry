from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_yearly_bonus(osv.osv):

	_name = "kg.yearly.bonus"
	_description = "Yearly Bonus"
	
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
					as sam  """ %('kg_yearly_bonus'))
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
		'ap_rej_date': fields.datetime('Approved/Reject Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Reject By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		
		## Module Requirement Info
		
		'from_date':fields.date('From',readonly=True, states={'draft':[('readonly',False)]}),
		'to_date':fields.date('To',readonly=True, states={'draft':[('readonly',False)]}),
		'expiry_date':fields.date('Expiry Date'),
		'fiscal_yr':fields.many2one('account.fiscalyear','Fiscal Year',domain=[('state','=','approved')]),
		'emp_categ_id':fields.many2one('kg.employee.category','Employee Category',domain=[('state','=','approved')]),
		'allow_ded_id':fields.many2many('hr.salary.rule','allow_ded','yr_bns','allow_ids','Bonus Base Components',domain=[('state','=','approved')]),
		'bonus_per':fields.float('Bonus Percentage'),
		'gross_sal_per':fields.float('% From Gross'),
		
		## Child Tables Declaration
		
		'line_id':fields.one2many('ch.yearly.bonus','header_id','Line id',readonly=True, states={'draft':[('readonly',False)]}),
		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.master', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		
	}
	
	####Validations####
	
	def  _validations (self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.to_date <= rec.from_date:
			raise osv.except_osv(_('Warning!'),
				_('Valid Till date should not be same or less than Valid From date!!'))
			return False
		if rec.bonus_per <= 0.00:
			raise osv.except_osv(_('Warning!'),
				_('Bonus Percentage value should not be less than or equal to zero'))
			return False
		if rec.emp_categ_id.id == 1:
			if rec.gross_sal_per <= 0.00:
				raise osv.except_osv(_('Warning!'),
					_('% From Gross value should not be less than or equal to zero'))
				return False
			
		check_dup =  self.pool.get('kg.yearly.bonus').search(cr,uid,([('from_date','=',rec.from_date),('to_date','=',rec.to_date)]))
		if len(check_dup) > 1:
			raise osv.except_osv(_('Warning !!'),
				_('Bonus for  this duration is created already !!'))
	
		return True
						
	_constraints = [

		(_validations, 'validations', [' ']),		
		
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
			if not rec.line_id:
				raise osv.except_osv(_('Warning!'),
					_('Employee Details should not be empty !!'))
			else:
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
		return super(kg_yearly_bonus, self).write(cr, uid, ids, vals, context)	
	
	
	## Module Requirement
	
	def onchange_fiscal_yr(self, cr, uid, ids, fiscal_yr,from_date,to_date, context=None):
		value = {'from_date':'','to_date':''}
		fis_yr_rec = self.pool.get('account.fiscalyear').browse(cr, uid, fiscal_yr, context=context)
		value = {
				'from_date': fis_yr_rec.date_start,
				'to_date':fis_yr_rec.date_stop,
				}
		return {'value': value}
		
	def bonus_calc(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		con_obj=self.pool.get('hr.contract')
		payslip_obj=self.pool.get('hr.payslip')
		payslip_line_obj=self.pool.get('hr.payslip.line')
		con_ids = con_obj.search(cr,uid,[('emp_categ_id','=',rec.emp_categ_id.id),('active','=',True)])
		if rec.line_id:
			cr.execute('''delete from ch_yearly_bonus where header_id='%s' '''%(rec.id))
		else:
			pass
		if con_ids:
			base_comp_ids = [base_comps.code for base_comps in  rec.allow_ded_id]
			print "compidssssssssssssssss",tuple(base_comp_ids)
			for cont_ids in con_ids:
				con_rec = con_obj.browse(cr,uid,cont_ids)
				pay_slip_ids = payslip_obj.search(cr,uid,[('date_from','>=',rec.from_date),('date_to','<=',rec.to_date),('employee_id','=',con_rec.employee_id.id)])
				if pay_slip_ids:
					if con_rec.emp_categ_id.id == 13:
						tot_gross_amt=0
						bonus_amt=0
						for pay_ids in pay_slip_ids:
							pay_slip_rec= payslip_obj.browse(cr,uid,pay_ids)
							print "Gross amount",pay_slip_rec.cross_amt
							tot_gross_amt += pay_slip_rec.cross_amt
						print "Total Gross amount...................",tot_gross_amt
						bonus_amt = (((tot_gross_amt*rec.bonus_per)/100)*rec.gross_sal_per)/100
						self.pool.get('ch.yearly.bonus').create(cr,uid,
								{
									'header_id':rec.id,
									'employee_id':con_rec.employee_id.id,
									'emp_code':con_rec.code,
									'bonus_wages':tot_gross_amt,
									'bonus_amt':bonus_amt,
									
								},context = None)
					else:
						bonus_wages=0
						bonus_amount=0
						for pay_ids in pay_slip_ids:
							base_ids = tuple(base_comp_ids)
							payslip_line_ids = payslip_line_obj.search(cr,uid,[('slip_id','=',pay_ids),('code','in',(base_ids))])
							print "payslipidssssssssssssssssssssssssssssss",payslip_line_ids
							if payslip_line_ids:
								for pay_line_ids in payslip_line_ids:
									pay_line_rec = payslip_line_obj.browse(cr,uid,pay_line_ids)
									print "Salary components..............................",pay_line_rec.name,pay_line_rec.amount
									bonus_wages += pay_line_rec.amount
						print "BOnus values are .....................................",bonus_wages
						bonus_amount = (bonus_wages*rec.bonus_per)/100
						self.pool.get('ch.yearly.bonus').create(cr,uid,
								{
									'header_id':rec.id,
									'employee_id':con_rec.employee_id.id,
									'emp_code':con_rec.code,
									'bonus_wages':bonus_wages,
									'bonus_amt':bonus_amount,
									
								},context = None)
						
						
						
		return True
	
kg_yearly_bonus()

class ch_yearly_bonus(osv.osv):
	
	_name = "ch.yearly.bonus"
	_description = "Employee Details"
	
	_columns = {

	'header_id':fields.many2one('kg.yearly.bonus','Header id'),
	'employee_id':fields.many2one('hr.employee','Employee'),
	'emp_code':fields.char('Code'),
	'bonus_wages':fields.float('Bonus Wages'),
	'bonus_amt':fields.float('Bonus Amount'),
	}
	
ch_yearly_bonus()	
