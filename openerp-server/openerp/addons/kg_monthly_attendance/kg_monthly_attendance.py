from lxml import etree
import openerp.addons.decimal_precision as dp
import openerp.exceptions
from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import datetime
import calendar

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_monthly_attendance(osv.osv):

	_name = "kg.monthly.attendance"
	_description = "Employee Monthly Attendance"
	
	
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
					as sam  """ %('kg_monthly_attendance'))
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
		
	def _paid_amt(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		for rec in self.browse(cr, uid, ids, context=context):
			res[rec.id] = {
				'salary_days': 0.0,
			}
			#~ var = rec.ot_days+rec.od_days+rec.arrear_days+rec.leave_days+rec.worked_days 
			var = rec.od_days+rec.arrear_days+rec.leave_days+rec.worked_days 
			res[rec.id]['salary_days'] = var
		return res	
		
	
	_columns = {
	
		### Basic Info
			
		'code': fields.char('Code', size=10, required=True),		
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
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
		
		## Module Requirement Info
		
		'employee_id':fields.many2one('hr.employee', 'Employee', readonly=True),
		'start_date': fields.date('Month Start Date'),
		'end_date': fields.date('Month End Date'),
		'worked_days':fields.float('Worked Days'),	
		'arrear_days':fields.float('Arrear'),	
		'half_days':fields.float('Half'),	
		'ot_days':fields.float('OT'),	
		'od_days':fields.float('ON Duty'),	
		'cas_lev_days':fields.float('Casual Leave'),	
		'fes_lev_days':fields.float('Festival Leave'),	
		'ear_lev_days':fields.float('Earned Leave'),	
		'absent_days':fields.float('Absent'),	
		'total_days':fields.float('Total Days of Month'),	
		'leave_days':fields.float('Total Leave Days'),	
		'working_days':fields.float('Total Working Days'),	
		'salary_days': fields.function(_paid_amt, string='Total Paid Days',multi="sums",store=True),		
		'late_days':fields.float('Late'),	
		'month':fields.char('Month'),	
		
		## Child Tables Declaration		
		
		
		
				
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
		if rec.state == 'approved':
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
		if rec.state == 'confirmed':
			if rec.remark:
				self.write(cr, uid, ids, {'state': 'reject','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Rejection remark is must !!'),
					_('Enter the remarks in rejection remark field !!'))
		else:
			raise osv.except_osv(_('Warning!!!'),
					_('Confirm the record to proceed further'))
		return True
		
	#~ def unlink(self,cr,uid,ids,context=None):
		#~ unlink_ids = []		
		#~ for rec in self.browse(cr,uid,ids):	
			#~ if rec.state not in ('draft','cancel'):				
				#~ raise osv.except_osv(_('Warning!'),
						#~ _('You can not delete this entry !!'))
			#~ else:
				#~ unlink_ids.append(rec.id)
		#~ return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_monthly_attendance, self).write(cr, uid, ids, vals, context)
		
	
	## Module Requirement
	
	def _month_total_day(self, cr, uid, context=None):
		today = datetime.date.today()
		first = datetime.date(day=1, month=today.month, year=today.year)
		mon = today.month - 1
		if mon == 0:
			mon = 12
		else:
			mon = mon
		res = calendar.monthrange(today.year,mon)[1]
		return res
	
	def _get_last_month_first(self, cr, uid, context=None):
		today = datetime.date.today()
		first = datetime.date(day=1, month=today.month, year=today.year)
		mon = today.month - 1
		if mon == 0:
			mon = 12
		else:
			mon = mon
		tot_days = calendar.monthrange(today.year,mon)[1]
		test = first - datetime.timedelta(days=tot_days)
		res = test.strftime('%Y-%m-%d')
		return res
		
	def _get_last_month_end(self, cr, uid, context=None):
		today = datetime.date.today()
		first = datetime.date(day=1, month=today.month, year=today.year)
		last = first - datetime.timedelta(days=1)
		res = last.strftime('%Y-%m-%d')
		return res
	
	def onchange_emp_id(self, cr, uid, ids, employee_id,code,context=None):		
		value = {'code': ''}
		emp = self.pool.get('hr.employee').browse(cr, uid, employee_id, context=context)
		value = {'code': emp.code}
		return {'value': value}
		
	def update_monthly_att(self,cr,uid,ids,context=None):
		
		today = datetime.date.today()
		first = datetime.date(day=1, month=today.month, year=today.year)
		mon = today.month - 1
		if mon == 0:
			mon = 12
		else:
			mon = mon
		tot_days = calendar.monthrange(today.year,mon)[1]
		test = first - datetime.timedelta(days=tot_days)
		res_start = test.strftime('%Y-%m-%d')
		last = first - datetime.timedelta(days=1)
		res_end = last.strftime('%Y-%m-%d')

		da_obj = self.pool.get('kg.daily.attendance')
		da_line_obj = self.pool.get('ch.daily.attendance')
		mon_att_obj = self.pool.get('kg.monthly.attendance')
		today = date.today()
		days_back = today - timedelta(today.day)		
		last_month = days_back.strftime('%B')
		cur_year = days_back.year
		month_1 = str(last_month) + '-' + str(cur_year)
		da_ids = da_obj.search(cr,uid,[('month','=',last_month),('year','=',cur_year)])
		check_data = mon_att_obj.search(cr,uid,[('start_date','=',res_start),('end_date','=',res_end)])
		print "-------------------------------------------------------->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>",len(check_data)
		if len(check_data) == 1:
			 
			for item in da_ids:
				da_rec = da_obj.browse(cr,uid,item)
				w_days = da_line_obj.search(cr,uid,[('header_id','=',item),
								('status','not in',('weekoff','absent','halfday','compoff_half','compoff_full'))])
				lev_days = da_line_obj.search(cr,uid,[('header_id','=',item),
								('status','=','leave')])
				od_days = da_line_obj.search(cr,uid,[('header_id','=',item),
								('status','=','onduty')])
				ab_days = da_line_obj.search(cr,uid,[('header_id','=',item),
								('status','=','absent')])
				ot_days = da_line_obj.search(cr,uid,[('header_id','=',item),
								('ot_hrs','!=','00:00')])
				half_days = da_line_obj.search(cr,uid,[('header_id','=',item),
								('status','=','halfday')])
				wrkg_days = da_line_obj.search(cr,uid,[('header_id','=',item),('status','not in',('weekoff','holiday'))])
				
				if half_days:
					tot_hf_day = 0
					for i in half_days:
						tot_hf_day += .5
					tot_half_days = len(w_days) + tot_hf_day
				else:
					tot_half_days = len(w_days)
				
				att_vals = {

							'employee_id':da_rec.employee_id.id,
							'code':da_rec.employee_id.code,
							'worked_days':tot_half_days,
							'working_days':len(wrkg_days),
							#~ 'salary_days':len(w_days),
							'salary_days':tot_half_days,
							'leave_days':len(lev_days),
							'od_days':len(od_days),
							'absent_days':len(ab_days),
							'ot_days':len(ot_days),
							'month':month_1,
			
							'state':'draft',
							
						}
				att_id = mon_att_obj.create(cr,uid,att_vals)
		else:
			raise osv.except_osv(_('Warning!'),
					_('Monthly attendance already created for this month !!'))
		return True
		
	
		
	###Validations###
	def _check_number_of_days(self, cr, uid,ids,context=None):
		rec = self.browse(cr, uid, ids[0])
		mon_total_days = rec.total_days
		all_days = rec.working_days + rec.worked_days + rec.arrear_days + rec.half_days + rec.ot_days + rec.od_days + rec.cas_lev_days 
		+rec.fes_lev_days + rec.ear_lev_days + rec.absent_days + rec.total_days + rec.leave_days + rec.late_days + rec.salary_days or 0.00
		if (all_days > mon_total_days) or (all_days < mon_total_days):
			raise osv.except_osv(_('Warning!'),
						_('Entered days should not exceed of less than the total days in a month!!'))
		check_wrk_days = rec.leave_days + rec.salary_days + rec.worked_days + rec.ot_days + rec.od_days + rec.absent_days
		if (rec.working_days < check_wrk_days) or (rec.working_days > check_wrk_days):
			raise osv.except_osv(_('Warning!'),
						_('Entered days should not exceed or less than the total working days!!'))
			return False
		return  True
		
	_constraints = [
		
		(_check_number_of_days, 'Attendance entry already available for this employee in this month !!',['']),		
		] 
	
		
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.monthly.attendance', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		'start_date': _get_last_month_first,
		'end_date': _get_last_month_end,
		'total_days': _month_total_day,
		
	}
		 
		
	
kg_monthly_attendance()
