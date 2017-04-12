from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
from dateutil import relativedelta as rdelta
from datetime import date, datetime, timedelta
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')
#~ today = datetime.now()

class kg_yos_bonus(osv.osv):

	_name = "kg.yos.bonus"
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
					as sam  """ %('kg_yos_bonus'))
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
		'fiscal_yr':fields.many2one('account.fiscalyear','Fiscal Year'),
		'emp_categ_id':fields.many2one('kg.employee.category','Employee Category'),

		## Child Tables Declaration
		
		'line_id':fields.one2many('ch.yos.bonus.values','header_id','Line id',readonly=True, states={'draft':[('readonly',False)]}),
		'line_id_1':fields.one2many('ch.yos.bonus.emp','header_id_1','Line id 1',readonly=True, states={'draft':[('readonly',False)]}),
	
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
			
		check_dup =  self.pool.get('kg.yos.bonus').search(cr,uid,([('from_date','=',rec.from_date),('to_date','=',rec.to_date)]))
		if len(check_dup) > 1:
			raise osv.except_osv(_('Warning !!'),
				_('Bonus for  this duration is created already !!'))
				
		if rec.line_id:
			for lin_id in rec.line_id:
				if lin_id.bonus_val <= 0.00:
					raise osv.except_osv(_('Warning!'),
						_('Value for Year Of Service should not be less than or equal to zero !!'))
			line_yos = [ line.yos for line in rec.line_id ]
			a= [line_yos.count(i) for i in line_yos ]
			for j in a:
				if j > 1:
					raise osv.except_osv(_('Warning!'),
								_('Duplicate Entries in YOS are not allowed !!'))
								
		if rec.line_id_1:
			line_emp = [ line.employee_id for line in rec.line_id_1 ]
			a= [line_emp.count(i) for i in line_emp ]
			for j in a:
				if j > 1:
					raise osv.except_osv(_('Warning!'),
								_('Duplicate Employee entries are not allowed !!'))
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
					_('Value for YOS should not be empty !!'))
			if not rec.line_id_1:
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
		return super(kg_yos_bonus, self).write(cr, uid, ids, vals, context)	

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
		emp_obj=self.pool.get('hr.employee')
		payslip_obj=self.pool.get('hr.payslip')
		payslip_line_obj=self.pool.get('hr.payslip.line')
		con_ids = con_obj.search(cr,uid,[('emp_categ_id','=',rec.emp_categ_id.id),('active','=',True)])
		if rec.line_id_1:
			cr.execute('''delete from ch_yos_bonus_emp where header_id_1='%s' '''%(rec.id))
		else:
			pass
		if con_ids:
			bon_val = 0.00
			for cont_ids in con_ids:
				today = date.today()
				con_rec = con_obj.browse(cr,uid,cont_ids)
				emp_rec = emp_obj.browse(cr,uid,con_rec.employee_id.id)
				print "Employee Name..........................................",emp_rec.name
				print "join Date..........................................",emp_rec.join_date
				print "Today's Date....................................",today
				d1 =  datetime.strptime(str(today), "%Y-%m-%d")
				d2 =  datetime.strptime(emp_rec.join_date, "%Y-%m-%d")
				rd = rdelta.relativedelta(d1,d2)
				years= "{0.years}.{0.months}".format(rd)
				months = "{0.months}".format(rd)
				print "Years of service.................................",years
				a = float(years)
				if a > 1:
					cr.execute('''select max(bonus_val) from ch_yos_bonus_values where header_id = %s and yos::float <= %s '''%(rec.id,a))
					max_bon = cr.dictfetchone()
					print"max_bonmax_bonmax_bon",max_bon
					if max_bon:
						bon_val = max_bon['max']
					else:
						bon_val =0.00
				else:
					cr.execute('''select min(bonus_val) from ch_yos_bonus_values where header_id = %s'''%(rec.id))
					max_bon = cr.dictfetchone()
					bon_val = int(months) * max_bon['min']
				self.pool.get('ch.yos.bonus.emp').create(cr,uid,
						{
							'header_id_1':rec.id,
							'employee_id':con_rec.employee_id.id,
							'emp_code':con_rec.code,
							'yos':years,
							'bonus_amt':bon_val,
							
						},context = None)
		return True
	
kg_yos_bonus()

class ch_yos_bonus_values(osv.osv):
	
	_name = "ch.yos.bonus.values"
	_description = "Year of Service Bonus values"
	
	_columns = {

	'header_id':fields.many2one('kg.yos.bonus','Header id'),
	'yos': fields.selection([('.12','Below 1 Year'),('1.0','More than 1 yr'),('2.0','More than 2 yrs'),('3.0','More than 3 yrs'),('4.0','More than 4 yrs'),('5.0','More than 5 yrs'),('6.0','More than 6 yrs'),('7.0','More than 7 yrs')
			,('8.0','More than 8 yrs'),('9.0','More than 9 yrs'),('10.0','More than 10 yrs'),('11.0','More than 11 yrs'),('12.0','More than 12 yrs')],'YOS'),
	'bonus_val':fields.float('Value'),
	}
	
ch_yos_bonus_values()	

class ch_yos_bonus_emp(osv.osv):
	
	_name = "ch.yos.bonus.emp"
	_description = "Employee Details"
	
	_columns = {

	'header_id_1':fields.many2one('kg.yos.bonus','Header id 1'),
	'employee_id':fields.many2one('hr.employee','Employee'),
	'emp_code':fields.char('Code'),
	'yos':fields.char('YOS'),
	'bonus_amt':fields.float('Bonus Amount'),
	}
	
ch_yos_bonus_emp()	
