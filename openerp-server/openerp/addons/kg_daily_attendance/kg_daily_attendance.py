# Daily Attendance Entry Module

from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import time
from dateutil import relativedelta
import datetime
import calendar
from datetime import date, datetime, timedelta

class kg_daily_attendance(osv.osv):

	_name = "kg.daily.attendance"
	_description = "Daily Attendance"
	_order = "date desc"
	
	def _get_modify(self, cr, uid, ids, field_name, arg,  context=None):
		res={}		
		if field_name == 'modify':
			for h in self.browse(cr, uid, ids, context=None):
				res[h.id] = 'no'
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
			
		'notes': fields.text('Notes'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10 ,store=True),		
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),


		### Entry Info ###
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'active': fields.boolean('Active'),
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'update_date':fields.date('Last Update On',readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Update By', readonly=True),
		
		## Module Requirement Info	
		
		'employee_id':fields.many2one('hr.employee', 'Employee Name'),
		'emp_code': fields.char('Employee Code',size=128,readonly=False),
		'active': fields.boolean('Active'),
		#~ 'month': fields.many2one('kg.month','Month'),
		'month': fields.char('Month'),
		'year': fields.selection([('2017','2017'),('2018','2018'),('2019','2019')], 'Year', readonly=False),
		
		'att_code': fields.char('Attendance Code', size=64),
		'date': fields.date('Creation Date'),
		'emp_categ_id':fields.many2one('kg.employee.category','Category'),
		'division_id':fields.many2one('kg.division.master','Division'),
		
		## Child Tables Declaration		
		'line_id': fields.one2many('ch.daily.attendance', 'header_id','Daily Attendance Line'),
	}
	
	_defaults = {
	
	'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.daily.attendance', context=c),
	'active': True,
	'modify': 'no',
	'entry_mode': 'manual',
	'year': '2017',
	
	}
	
	### Basic Needs
	
	#~ def unlink(self,cr,uid,ids,context=None):
		#~ raise osv.except_osv(_('Warning!'),
				#~ _('You can not delete Entry !!'))
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_daily_attendance, self).write(cr, uid, ids, vals, context)

	## Module Requirement

	def month_att_entry_creation(self,cr,uid,ids=0,contex=None):
		today = date.today()		
		cur_month = today.strftime('%B')
		cur_year = today.year
		#sql = """ select id from hr_employee where att_code !='' and payslip=True """
		sql = """ select hr.id as id
					from hr_employee hr
					left join resource_resource res on(res.id=hr.id)
					where hr.att_code !='' and hr.payslip=True and res.active = True"""
		cr.execute(sql)
		data = cr.dictfetchall()
		cur_month = today.strftime('%B')
		cur_year = today.year
		#~ month_id = self.pool.get('kg.month').search(cr,uid,[('code','=',cur_month)])
		att_obj = self.pool.get('kg.daily.attendance')
		for item in data:
			emp_id = item.values()[0]
			emp_rec = self.pool.get('hr.employee').browse(cr,uid,emp_id)
			att_vals = {

				'employee_id': emp_id,
				'emp_code':emp_rec.code,
				'month':cur_month,
				'att_code':emp_rec.att_code,
				'emp_categ_id':emp_rec.emp_categ_id.id,
				'division_id':emp_rec.division_id.id,
				'date': today,

				}
			att_id = att_obj.create(cr,uid,att_vals)

		return True
	
kg_daily_attendance()

class ch_daily_attendance(osv.osv):

	_name = "ch.daily.attendance"
	_description = "Daily Attendance Line"
	_order = "date"
	
	_columns = {
		
		'header_id': fields.many2one('kg.daily.attendance','Daily Attendance'),
		'employee_id':fields.many2one('hr.employee', 'Employee Name'),
		'date': fields.date('Date'),
		'punch_date': fields.datetime('Punch Date'),
		'in_time1': fields.char('In1',size=5),
		'in_time2': fields.char('In2',size=5),
		'in_time3': fields.char('In3',size=5),
		'in_time4': fields.char('In4',size=5),
		'in_time5': fields.char('In5',size=5),
		'in_time6': fields.char('In6',size=5),
		'in_time7': fields.char('In7',size=5),
		'in_time8': fields.char('In8',size=5),
		'out_time1': fields.char('Out1',size=5),
		'out_time2': fields.char('Out2',size=5),
		'out_time3': fields.char('Out3',size=5),
		'out_time4': fields.char('Out4',size=5),
		'out_time5': fields.char('Out5',size=5),
		'out_time6': fields.char('Out6',size=5),
		'out_time7': fields.char('Out7',size=5),
		'out_time8': fields.char('Out8',size=5),
		'tot_hrs': fields.float('Total Hours'),
		'wk_time': fields.char('Worked Hours'),
		'punch_type': fields.selection([('IN','IN'),('OUT','OUT')], 'Punch Type'),
		'status': fields.selection([('present','Present'),('absent','Absent'),('holiday','Holiday'),
							('leave','Leave'),('compoff_half','CompOff-Half'),('compoff_full','CompOff-Full'),('weekoff','WeekOff'),('onduty','On-Duty'),('halfday','HalfDay')],'Status'),
		'leavetype': fields.selection([('legal','Legal Leaves'),('comp','Compensatory Days'),
								('sl','Sick Leave'),('unpaid','Unpaid'),('cl','Casual Leave')],'Leave Type'),

		'cur_day':fields.char('Day',size=64,readonly=True),
		'ot_hrs':fields.char('OT Hours'),
		'remarks':fields.char('Remarks')
		
		
	}
	
ch_daily_attendance()
