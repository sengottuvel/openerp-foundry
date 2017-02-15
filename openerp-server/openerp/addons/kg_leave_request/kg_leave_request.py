from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime, date, timedelta
import re
import math
import calendar
import time
from dateutil import relativedelta
import datetime
import calendar
from datetime import date, datetime, timedelta
from datetime import date, timedelta as td
#~ import datetime 
#~ 
#~ from dateutil import relativedelta
from dateutil import relativedelta as rdelta
from datetime import datetime
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_leave_request(osv.osv):

	_name = "hr.holidays"
	_inherit = "hr.holidays"
	_description = "Leave Request"
	
	### Version 0.1
	
	def _get_modify(self, cr, uid, ids, field_name, arg,  context=None):
		res={}		
		if field_name == 'modify':
			for h in self.browse(cr, uid, ids, context=None):
				res[h.id] = 'no'
				if h.status == 'approved':
					cr.execute(""" select * from 
					(SELECT tc.table_schema, tc.constraint_name, tc.table_name, kcu.column_name, ccu.table_name
					AS foreign_table_name, ccu.column_name AS foreign_column_name
					FROM information_schema.table_constraints tc
					JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
					JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
					WHERE constraint_type = 'FOREIGN KEY'
					AND ccu.table_name='%s')
					as sam  """ %('hr_holidays'))
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
	
		### Basic Info
			
		'code': fields.char('Code', size=10, required=False),		
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),


		### Entry Info ###
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'active': fields.boolean('Active'),
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'create_user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'ap_rej_date': fields.datetime('Approved/Reject Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Reject By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		
		## Module Requirement Info	
		'description':fields.text('Reason'),
		'approved_by':fields.many2one('hr.employee','Approved By'),
		'in_time':fields.float('In Time'),
		'out_time':fields.float('Out Time'),
		'permission_hrs':fields.float('Permission Hours'),
		'from_date':fields.date('From Date'),
		'to_date':fields.date('To Date'),
		'holiday_status_name': fields.related('holiday_status_id','name',type='char', string='Leave Type Name', store=True),
		## Child Tables Declaration		
		'line_id_1': fields.one2many('ch.leave.request', 'header_id_1','Leave Allocation'),
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.master', context=c),
		'active': True,
		'create_user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		
	}
	
	### Basic Needs
	
	def onchange_leave_type(self, cr, uid, ids, holiday_status_id,context=None):
		value = {'holiday_status_name': ''}
		if holiday_status_id:
			hol_status_rec = self.pool.get('hr.holidays.status').browse(cr, uid, holiday_status_id, context=context)
			value = {'holiday_status_name': hol_status_rec.name}
		return {'value': value}
		
	def _Validation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		name_special_char = ''.join( c for c in flds.description if  c in '!@#$%^~*{}?+/=' )		
		if name_special_char:
			return False		
		return True	
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'status': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		
		self.write(cr, uid, ids, {'status': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'status': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		ccc=0
		#~ date=''
		leave_requests = self.pool.get('hr.holidays')
		employee_obj = self.pool.get('hr.employee')
		employee_category = self.pool.get('kg.employee.category')
		leave_allocation = self.pool.get('kg.leave.allocation')
		leave_allocation_line = self.pool.get('ch.leave.allocation')
		
		### Validating Leave Allocation#####
		rec = self.browse(cr,uid,ids[0])
		leave_allocation = self.pool.get('kg.leave.allocation')
		leave_allocation_line = self.pool.get('ch.leave.allocation')
		
		emp_leave_allo = leave_allocation.search(cr,uid,[('employee_id','=',rec.employee_id.id),
						('valid_from','<=',rec.from_date),('valid_to','>=',rec.to_date),('state','=','approved')])
		if emp_leave_allo:
			leave_alloc = leave_allocation_line.search(cr,uid,[('header_id_1','=',emp_leave_allo[0])])
			if leave_alloc:
				leave_types = [leave_allocation_line.browse(cr,uid,ids).id for ids in  leave_alloc if leave_allocation_line.browse(cr,uid,ids).leave_type_id.id ==  rec.holiday_status_id.id]
				if leave_types:
					leave_rec = leave_allocation_line.browse(cr,uid,leave_types[0])					
					if rec.number_of_days_temp <= leave_rec.balc_days:
						leave_rec.write({'balc_days': leave_rec.balc_days - rec.number_of_days_temp,
												'used_days':leave_rec.used_days + rec.number_of_days_temp})
					else:
						raise osv.except_osv(_('No of days are exceeding !! '),
							_('Balance %s for this employee is %s!!')%(leave_rec.leave_type_id.name,leave_rec.balc_days))
		elif rec.holiday_status_id.id == 25 or rec.holiday_status_id.id == 31:
			pass
		else:
			raise osv.except_osv(_('Warning'),
				_('Leave is not allocated for the this employee !!'))				
				
		### Validating Leave Allocation#####
		
		
		
		
		### Validating Permission Hours for a month #####
		aaa = employee_obj.browse(cr,uid,rec.employee_id.id)
		bbb = employee_category.browse(cr,uid,aaa.emp_categ_id.id)
		today = date.today()
		start_date = datetime(today.year, today.month, 1)
		end_date = datetime(today.year, today.month, calendar.mdays[today.month])
		emp_leave_allosss = leave_requests.search(cr,uid,[('employee_id','=',rec.employee_id.id),('holiday_status_id','=',rec.holiday_status_id.id),
						('from_date','>=',start_date),('to_date','<=',end_date),('status','=','approved')])
		for i in emp_leave_allosss:
			aaa = leave_requests.browse(cr,uid,i)
			ccc += aaa.permission_hrs
		if bbb.monthly_per_hrs < rec.permission_hrs + ccc :
			raise osv.except_osv(_('Warning'),
				_('Permission for this month is exceed the allocated permission hours !!'))	
		else:	
			pass
		
		### Validating Permission Hours for a month #####
		
		
		
		
		### Updating leaves in daily attendance #####
		print "From date ----------------------------------->>>>>>>>>>>>>",rec.from_date
		print "To date ----------------------------------->>>>>>>>>>>>>",rec.to_date
		d1 = datetime.strptime(rec.from_date, "%Y-%m-%d")
		d2 = datetime.strptime(rec.to_date, "%Y-%m-%d")
		delta = d2 - d1
		print "delta -----------------------",delta
		for i in range(delta.days + 1):
			betw_days = d1 + td(days=i)
			print "*******************************",betw_days
			daily_rec = self.pool.get('ch.daily.attendance').search(cr,uid,[('employee_id','=',rec.employee_id.id),('date','=',betw_days),])
			if daily_rec:
				for d_rec in daily_rec:
					daily_rec_1 = self.pool.get('ch.daily.attendance').browse(cr,uid,d_rec)
					wk_hrs_f = str(daily_rec_1.wk_time) .replace(':', '.')
					if rec.holiday_status_id.id == 29:
						tot_times = float(wk_hrs_f) + rec.permission_hrs
						wk_hrs_s = str(tot_times) .replace('.', ';')
						daily_rec_1.write({'wk_time':tot_times ,'remarks':rec.holiday_status_id.name +'='+str(rec.permission_hrs)})
					elif rec.holiday_status_id.id == 25:
						daily_rec_1.write({'status': 'onduty','remarks':rec.holiday_status_id.name})
					elif rec.holiday_status_id.id == 31:
						daily_rec_1.write({'status': 'absent','remarks':rec.holiday_status_id.name})
					else:
						daily_rec_1.write({'status': 'leave','remarks':rec.holiday_status_id.name})
		#~ stop
			else:
				pass
		### Updating leaves in daily attendance #####
		
		
		rec.write({'status': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'status': 'reject','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter the remarks in rejection remark field !!'))
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.status not in ('draft','cancel'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_leave_request, self).write(cr, uid, ids, vals, context)
		
	
	_constraints = [
	
		(_Validation, 'Special Character Not Allowed !!!', ['Check Description']),

	]
	
	###Validations
	
	def val_negative(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.number_of_days_temp < 0:
			raise osv.except_osv(_('Warning!'),
						_('To Date should not be less than From Date !! !!'))
		if rec.in_time < 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values are not allowed in In TIme  !!'))
		if rec.out_time < 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values are not allowed in Out Time !!'))
		if rec.out_time < rec.in_time:
			raise osv.except_osv(_('Warning!'),
						_('Out TIme should not be less than In Time !!'))
		if rec.permission_hrs > 5:
			raise osv.except_osv(_('Warning!'),
						_('Permission Hours should not exceed 5 hrs !!'))
		if rec.permission_hrs < 0:
			raise osv.except_osv(_('Warning!'),
						_('Permission Hours should not Zero or less than Zero !!'))
		if rec.to_date < rec.from_date:
			raise osv.except_osv(_('Warning!'),
						_('To Date should not be less than From Date !!'))

		return True
		
	_constraints = [

		(val_negative, 'Negative Values are not allowed!!', [' ']),		
		
	]
	
	## Module Requirement
	def onchange_employee_id(self, cr, uid, ids, employee_id,code, context=None):
		moc_const_vals=[]
		le_all = self.pool.get('kg.leave.allocation').search(cr,uid,[('employee_id','=',employee_id)])
		lev_rec_all = self.pool.get('kg.leave.allocation').browse(cr,uid,le_all[0])
		
		for ssss in lev_rec_all.line_id_1:
			moc_const_vals.append({
																
								'leave_type_id':ssss.leave_type_id.id,
								'no_of_days':ssss.no_of_days,
								'used_days':ssss.used_days,
								'balc_days':ssss.balc_days,
						
								})
			
		if employee_id:
			emp = self.pool.get('hr.employee').browse(cr,uid,employee_id)
			value = {'code': emp.code,
					'department_id':emp.department_id.id,
					}
		return {'value': {'line_id_1': moc_const_vals, 'code': emp.code,
					'department_id':emp.department_id.id,}}
		
	def onchange_to_date(self, cr, uid, ids,to_date,from_date,context=None):
		value = {'from_date':'','to_date':''}
		d1 =  datetime.strptime(from_date, "%Y-%m-%d")
		d2 =  datetime.strptime(to_date, "%Y-%m-%d")
		rd = rdelta.relativedelta(d2,d1)
		print "-----------------------no of days-----------------------------------",rd
		no_of_days= "{0.days}".format(rd)
		print "-----------------------no of days-----------------------------------",no_of_days
		if no_of_days=='0':
			value = {
				'number_of_days_temp':1,
				}
		else:
		
			value = {
				'number_of_days_temp':int(no_of_days) + 1,
				}
				
		return {'value': value}
        
	
	
kg_leave_request()

class ch_leave_request(osv.osv):
	
	_name = "ch.leave.request"
	_description = "Allocation lists"
	
	_columns = {

	'header_id_1': fields.many2one('hr.holidays','Header_id_1'),
	'leave_type_id': fields.many2one('hr.holidays.status', 'Leave Type'),
	'no_of_days': fields.float('No Of Days'),	
	'used_days': fields.float('Used Days'),	
	'balc_days': fields.float('Balance Days'),
	
	}
	
ch_leave_request()	
