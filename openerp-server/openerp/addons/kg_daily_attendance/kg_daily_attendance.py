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

class kg_daily_attendance(osv.osv):

	_name = "kg.daily.attendance"
	_description = "Daily Attendance"
	
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
					WHERE constraint_type = 'FOREIGN KEY' and tc.table_name not in ('ch_kg_daily_attendance')
					AND ccu.table_name='%s')
					as sam  """ %('kg_daily_attendance'))
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
			
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10 ,store=True),		
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
		
		'date': fields.date('Date'),
		'present_count': fields.integer('Present Count'),
		'absent_count': fields.integer('Absent Count'),
		'on_duty_count': fields.integer('On Duty Count'),
		'half_day_count': fields.integer('Half-Day Count'),
		'late_count': fields.integer('Late Count'),
		'total_count':fields.integer('Total Count'),	
		'in_time':fields.float('In Time'),	
		'out_time':fields.float('Out Time'),	
		'flag_load':fields.boolean('Flag Load'),	
		'copy_att':fields.boolean('Copy Attendance'),	
		'att_status':fields.selection([('present','Present'),('absent','Absent'),('late','Late'),('od','On Duty'),('half_day','Half Day')], 'Status'),		
		'total_hours':fields.float('Total Hours'),	
		## Child Tables Declaration		
		
		'line_id': fields.one2many('ch.kg.daily.attendance','header_id','Line Id'),
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.daily.attendance', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		'date': lambda * a: time.strftime('%Y-%m-%d'),
		'att_status': 'present',
		
	}
	
	
	### Basic Needs
	
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
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
		if rec.state == 'confirmed':
			self.write(cr, uid, ids, {'state': 'draft'})
		else:
			raise osv.except_osv(_('Warning!!!'),
					_('Confirm the record to proceed further'))
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			vals = self.employee_attendance_count(cr,uid,ids,context = context)
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S'),'present_count':vals['present_count'],'total_count':vals['total_count'],
									'absent_count':vals['absent_count'],'on_duty_count':vals['on_duty_count'],
									'half_day_count':vals['half_day_count'],'late_count':vals['late_count']})
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
		return super(kg_daily_attendance, self).write(cr, uid, ids, vals, context)
		
	
	
	
	## Module Requirement
	
	def load_employees(self,cr,uid,ids,context = None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			copy_att = """	
				update ch_kg_daily_attendance set in_time=%s,out_time=%s,status='%s' where header_id = %d
				"""%(rec.in_time,rec.out_time,rec.att_status,ids[0])
			cr.execute(copy_att)
			emp_inservice_sql = """	
					select id,join_date from hr_employee where status = 'approved'
					and join_date <= '%s' """%(rec.date)
			cr.execute(emp_inservice_sql)
			data = cr.dictfetchall()		
			#~ emp_resigned_sql = """	
					#~ select id,join_date from hr_employee where status = 'resigned'
					#~ and releaving_date >= '%s' """%(entry.date)
			#~ cr.execute(emp_resigned_sql)
			#~ data_2 = cr.dictfetchall()
			#~ data.extend(data_2)
			for item in data:
				emp_rec = self.pool.get('hr.employee').browse(cr,uid,item['id'])
				self.pool.get('ch.kg.daily.attendance').create(cr,uid,
							{
							'header_id':ids[0],
							'employee_id': emp_rec.id,
							'code': emp_rec.code,
							'department_id': emp_rec.department_id.id,
							'status': 'present',
							'in_time': rec.in_time,
							'out_time':rec.out_time,
							'total_hours':rec.total_hours,
							},context = None)
			self.write(cr,uid,rec.id,{'flag_load':True})
		else:
			raise osv.except_osv(_('Warning!!!'),
					_('Confirm the record to proceed further'))
		return True
		
	def employee_attendance_count(self,cr,uid,ids,context = None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			line_ids = self.pool.get('ch.kg.daily.attendance').search(cr,uid,[('header_id','=',ids[0])])
			pre_count = 0
			abs_count = 0
			half_day_count = 0
			od_count = 0
			tot_count = 0
			late_count = 0
			ids = 0
			while(ids < len(line_ids)):
				line_rec = self.pool.get('ch.kg.daily.attendance').browse(cr,uid,line_ids[ids])
				if line_rec.status == 'present':
					pre_count += 1
					
				if line_rec.status == 'absent':
					abs_count += 1
				
				if line_rec.status == 'od':
					od_count += 1
				
				if line_rec.status == 'half_day':
					half_day_count += 1
					
				if line_rec.status == 'late':
					late_count += 1
				ids += 1
			tot_count = half_day_count	+ pre_count	+ abs_count + od_count +late_count
			vals = {'present_count':pre_count,'half_day_count':half_day_count,'absent_count':abs_count,'on_duty_count':od_count,
							'total_count':tot_count,'late_count':late_count}
		else:
			raise osv.except_osv(_('Warning!!!'),
					_('Confirm the record to proceed further'))
		return vals
		
	def _get_last_month_first(self, cr, uid,ids, context=None):
		res = {'srt_date':''}
		today = datetime.date.today()
		first = datetime.date(day=1, month=today.month, year=today.year)
		mon = today.month - 1
		if mon == 0:
			mon = 12
		else:
			mon = mon
		tot_days = calendar.monthrange(today.year,mon)[1]
		test = first - datetime.timedelta(days=tot_days)
		res['srt_date']= test.strftime('%Y-%m-%d')
		return res
		
	def _get_last_month_end(self, cr, uid,ids,context=None):
		res = {'lst_date':''}
		today = datetime.date.today()
		first = datetime.date(day=1, month=today.month, year=today.year)
		last = first - datetime.timedelta(days=1)
		res['lst_date'] = last.strftime('%Y-%m-%d')
		return res
		
	def monthly_attendance(self,cr,uid,ids,context=None):
		attenssss_sql = """	select to_char(date,'mm') from kg_daily_attendance where state='approved' and id = %s"""%(ids[0])
		cr.execute(attenssss_sql)
		data = cr.dictfetchall()
		if len(data)==1:
			raise osv.except_osv(_('Warning!'),
					_('Daily Attendance should be more than one for a month !!'))
			return False
		
		self._get_last_month_first(self, cr, uid,ids)
		self._get_last_month_end(self, cr, uid,ids)
		srt_date = self._get_last_month_first(self, cr, uid, ids)
		lst_date = self._get_last_month_end(self, cr, uid,ids)
		srt_date = "'"+srt_date['srt_date']+"'"
		lst_date = "'"+lst_date['lst_date']+"'"
		daily_att_ids = []
		atten_sql = """	select id from kg_daily_attendance where date >= %s and date <= %s
						and state = 'approved'"""%(srt_date,lst_date)
		cr.execute(atten_sql)
		data = cr.dictfetchall()
		
		if data:
			for emp_id in data:	
				daily_att_ids.append(emp_id['id'])
		daily_att_ids = tuple(daily_att_ids)
			
		emp_ids_sql = """ 	select employee_id as id from ch_kg_daily_attendance
							where header_id in (select id from kg_daily_attendance where 
							date >= %s and date <= %s and state = 'approved')
							group by employee_id  """%(srt_date,lst_date)
							
		cr.execute(emp_ids_sql)
		emp_ids = cr.dictfetchall()
		
		half_day = 0.00
		late_day = 0.00
		print "emp_idsemp_idsemp_ids",emp_ids
		for ids in emp_ids:

			emp_rec = self.pool.get('hr.employee').browse(cr,uid,ids['id'])
			if len(ids['id']) == 1:
				idsss=ids['id'][0]
			
			tot_sql = """ select count(id) as tot_count from ch_kg_daily_attendance where employee_id= %s 
							and header_id in %s """%(ids['id'],daily_att_ids)
			cr.execute(tot_sql)
			total_count = cr.dictfetchone()
			
			pre_sql = """ select count(id) as pre_count from ch_kg_daily_attendance where employee_id= %s and 
							status='present' and header_id in %s """%(ids['id'],daily_att_ids)
			cr.execute(pre_sql)
			pre_count = cr.dictfetchone()
			
			absent_sql = """ select count(id) as abs_count from ch_kg_daily_attendance where employee_id= %s and 
							status='absent' and header_id in %s """%(ids['id'],daily_att_ids)
			cr.execute(absent_sql)
			abs_count = cr.dictfetchone()
			
			late_sql = """ select count(id) as late_count from ch_kg_daily_attendance where employee_id= %s and 
							status='late' and header_id in %s """%(ids['id'],daily_att_ids)
			cr.execute(late_sql)
			late_count = cr.dictfetchone()
			
			half_day_sql = """ select count(id) as half_day_count from ch_kg_daily_attendance where employee_id= %s and 
							status='half_day' and header_id in %s """%(ids['id'],daily_att_ids)
			cr.execute(half_day_sql)
			half_day_count = cr.dictfetchone()
			
			od_sql = """ select count(id) as od_count from ch_kg_daily_attendance where employee_id= %s and 
							status='od' and header_id in %s """%(ids['id'],daily_att_ids)
			cr.execute(od_sql)
			od_count = cr.dictfetchone()	
			if total_count['tot_count'] > 0:
				net_count = total_count['tot_count']
				if abs_count['abs_count'] > 0:
					net_count -= abs_count['abs_count']
				if late_count['late_count'] > 2:
					late_ded = late_count['late_count'] / 2.0
					late_ded = late_ded - 1
					net_count -= late_ded
				if half_day_count['half_day_count'] > 0:
					half_ded = half_day_count['half_day_count'] / 2.0
					net_count -= half_ded

				if (abs_count['abs_count'] > 0 or half_day_count['half_day_count'] >= 0.5 or late_count['late_count'] > 2) :
					net_count += 1
				else:
					net_count = net_count

				if net_count > total_count['tot_count']:
					net_count = total_count['tot_count']
				else:
					net_count = net_count
				
				
				daily_att = self.search(cr,uid,[('state','=','approved'),('date','>=',srt_date),
												('date','<=',lst_date)])
				
				
				vals = {
								
								'employee_id':emp_rec.id,
								'code':emp_rec.code,
								'ot_days': 0,
								'worked_days':pre_count['pre_count'] or 0,
								'half_days':(float(half_day_count['half_day_count'] )/2 ) or 0,
								'od_days':od_count['od_count'] or 0,
								'absent_days':abs_count['abs_count'] or 0,
								'late_days':(float(late_count['late_count'])/2) or 0,
								'working_days':len(daily_att),
								'leave_days': 0,
								'arrear_days':0,
								'state':'confirmed',
								'total_days':net_count,
								'entry_mode':'auto',
								}
								
				monthly_att_obj = self.pool.get('kg.monthly.attendance')
				month_attendance = monthly_att_obj.create(cr,uid,vals)
			else:
				pass
				
		return vals
		
	def onchange_hrs(self, cr, uid, ids, in_time,out_time,context=None):		
		value = {'total_hours': ''}
		print "out_timeout_timeout_time",out_time
		print "in_timein_timein_time",in_time		
		value = {'total_hours': out_time - in_time }
		return {'value': value}
	
	
		
	### Validations ###
	
	def _date_check(self,cr,uid,ids,context=None):
		rec=self.browse(cr,uid,ids[0])
		current_date=time.strftime('%Y-%m-%d')
		if rec.date > current_date:
			raise osv.except_osv(_('Warning!'),
						_('Future Dates are Not Allowed !!'))
			return False
		return True
		
	def _attendance_duplicate(self, cr, uid, ids, context=None):
		obj = self.pool.get('kg.daily.attendance')
		rec = self.browse(cr, uid, ids[0])
		dup_ids = obj.search(cr, uid,[('date','=',rec.date)])
		if len(dup_ids) > 1:
			raise osv.except_osv(_('Warning!'),
						_('Attendance already exists for this date !!'))
			return False
		return True
		
	def _check_line_details(self,cr,uid,ids,context=None):
		rec=self.browse(cr,uid,ids[0])
		if not rec.line_id :
			raise osv.except_osv(_('Warning!'),
						_('Employees are not listed , Please load Employees !!'))
			return False
		return True
		
	
		
	_constraints = [
	
		(_date_check, 'Future Dates are Not Allowed !!!', ['Check Date']),
		(_attendance_duplicate, 'Attendance already exists for this date', [' ']),
		#~ (_check_line_details, 'Employees are not listed , Please load Employees', [' ']),

	]
	
kg_daily_attendance()

class ch_kg_daliy_attendance(osv.osv):
	
	_name = "ch.kg.daily.attendance"
	
	
	_columns = {
	
			'header_id':fields.many2one('kg.daily.attendance','Entry Line'),
			'employee_id':fields.many2one('hr.employee','Employee Name',required=True),
			'code':fields.char('Employee Code'),
			'department_id':fields.many2one('hr.department','Department Name'),
			'status':fields.selection([('present','Present'),('absent','Absent'),('late','Late'),('od','On Duty'),('half_day','Half Day')], 'Status'),
			'in_time':fields.float('In Time'),
			'out_time':fields.float('Out Time'),
			'total_hours':fields.float('Total Hours'),
		}
		
	def onchange_hrsss(self, cr, uid, ids, in_time,out_time,context=None):		
		value = {'total_hours': ''}
		print "out_timeout_timeout_time",out_time
		print "in_timein_timein_time",in_time		
		value = {'total_hours': out_time - in_time }
		return {'value': value}
	
		
ch_kg_daliy_attendance()
