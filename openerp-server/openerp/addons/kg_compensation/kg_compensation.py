from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
from datetime import date, timedelta as td
from datetime import timedelta
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')
today = date.today()
days_back = today - timedelta(today.day)		
last_month = days_back.strftime('%B')
cur_year = days_back.year
month_1 = str(last_month) + '-' + str(cur_year)


class kg_compensation(osv.osv):

	_name = "kg.compensation"
	_description = "Compensation"
	
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
					as sam  """ %('kg_compensation'))
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
		
		'comp_of':fields.date('Compensation Of ', states={'draft':[('readonly',False)]}),
		'comp_on':fields.date('Compensated On ', states={'draft':[('readonly',False)]}),
		'type':fields.selection([('emp_categ','Employee Category'),('emp','Employee'),],'Type'),
		'emp_categ_id':fields.many2many('kg.employee.category','emp_categ','comp_id','emp_categ_id','Employee Category',),
		'employee_id':fields.many2many('hr.employee','employees','comp_id','emp_id','Employee',),
		'month':fields.char('Month'),	
		
		## Child Tables Declaration
		
		'line_id':fields.one2many('ch.compensation','header_id','Line id',readonly=True, states={'draft':[('readonly',False)]}),
		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.master', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		'month': month_1,
		
	}
	
	####Validations####
	
	def  _validations (self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.comp_on <= rec.comp_of:
			raise osv.except_osv(_('Warning!'),
				_('Compensated date should not be same or less than Compensation date!!'))
			return False
		
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
		
		if rec.type =='emp_categ':
			if not rec.line_id:
				raise osv.except_osv(_('Warning!'),
					_('Employees should not be empty !!'))
		else:
			pass
		
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
		if  rec.line_id:
			for emp_ids in rec.line_id:
				comp_of = self.pool.get('ch.daily.attendance').search(cr,uid,[('employee_id','=',emp_ids.employee_id.id),('date','=',rec.comp_of)])
				print "^^^^^^^^^^^^^^^^^^^^",rec.comp_of
				print "************************",comp_of
				if comp_of:
					get_wrk_hrs = self.pool.get('ch.daily.attendance').browse(cr,uid,comp_of[0])
					print "_____________________wrk hrs______________________________",get_wrk_hrs.wk_time
					daily_ids = self.pool.get('ch.daily.attendance').search(cr,uid,[('employee_id','=',emp_ids.employee_id.id),('date','=',rec.comp_on)])
					if daily_ids:
							for lin_ids in daily_ids:
								daily_rec =  self.pool.get('ch.daily.attendance').browse(cr,uid,lin_ids)
								wk_hrs_s = str(get_wrk_hrs.wk_time) .replace(':', '.')
								dat_frmt = datetime.strptime(rec.comp_of,'%Y-%m-%d')
								print "&&&&&&&&&&&&&&&&&&&&",wk_hrs_s
								if float(wk_hrs_s) >= 8.00:
									daily_rec.write({'status':'compoff_full','remarks':'Compenstion of :' + dat_frmt.strftime('%d-%m-%Y')})
								elif  float(wk_hrs_s) >= 3.00:
									daily_rec.write({'status':'compoff_half','remarks':'Compenstion of :' + dat_frmt.strftime('%d-%m-%Y')})
								else:
									raise osv.except_osv(_(' '),
										_('Compensation should be more than 3 or 5 hours for %s !!'%(daily_rec.employee_id.name)))
				else:
					raise osv.except_osv(_(' '),
						_('Daily Attendance is not created for this employee on %s !!'%(rec.comp_of)))
									
					
		if rec.employee_id:
			for empl_ids in rec.employee_id:
				print "@@@@@@@@@@@",empl_ids.id
				comp_of_1 = self.pool.get('ch.daily.attendance').search(cr,uid,[('employee_id','=',empl_ids.id),('date','=',rec.comp_of)])
				if comp_of_1:
					get_wrk_hrs = self.pool.get('ch.daily.attendance').browse(cr,uid,comp_of_1[0])
					daily_ids_1 = self.pool.get('ch.daily.attendance').search(cr,uid,[('employee_id','=',empl_ids.id),('date','=',rec.comp_on)])
					print "daily_recdaily_recdaily_rec",daily_ids_1
					if daily_ids_1:
						for lin_ids in daily_ids_1:
							daily_rec_1 =  self.pool.get('ch.daily.attendance').browse(cr,uid,lin_ids)
							wk_hrs_s = str(get_wrk_hrs.wk_time) .replace(':', '.')
							dat_frmt = datetime.strptime(rec.comp_of,'%Y-%m-%d')
							if float(wk_hrs_s) >= 8.00:
								daily_rec_1.write({'status':'compoff_full','remarks':'Compenstion of :' + dat_frmt.strftime('%d-%m-%Y')})
							elif  float(wk_hrs_s) >= 3.00:
								daily_rec_1.write({'status':'compoff_half','remarks':'Compenstion of :' + dat_frmt.strftime('%d-%m-%Y')})
							else:
								raise osv.except_osv(_(' '),
									_('Compensation should be more than 3 or 5 hours for %s !!'%(daily_rec_1.employee_id.name)))
				else:
					raise osv.except_osv(_(' '),
						_('Daily Attendance is not created for this employee on %s !!'%(rec.comp_of)))
						
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
		rec = self.browse(cr,uid,ids[0])
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
		return super(kg_compensation, self).write(cr, uid, ids, vals, context)
	
	def emp_list(self,cr,uid,ids,context=None)	:
		rec = self.browse(cr,uid,ids[0])
		if rec.emp_categ_id :
			cr.execute('''delete from ch_compensation where header_id = %s '''%(rec.id))
			for i in rec.emp_categ_id:
				emp_ids = self.pool.get('hr.employee').search(cr,uid,[('emp_categ_id','=',i.id)])
				for j in emp_ids:
					self.pool.get('ch.compensation').create(cr,uid,
									{
										'header_id':rec.id,
										'employee_id':j,
									},context = None)
		return 
		
	
	
	## Module Requirement
	
kg_compensation()

class ch_compensation(osv.osv):
	
	_name = "ch.compensation"
	_description = "Employee list"
	
	_columns = {

	'header_id':fields.many2one('kg.compensation','Header id'),
	'employee_id':fields.many2one('hr.employee','Employee'),
	'note':fields.text('Description')
	
	}
	
ch_compensation()	
