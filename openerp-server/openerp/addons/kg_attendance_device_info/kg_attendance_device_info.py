# Attendance Reader Entry Module

from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import time
from dateutil import relativedelta
import datetime
import calendar
from datetime import date, datetime, timedelta
from datetime import date, timedelta as td

# To import file
import csv
import psycopg2


# To delete file
import os, sys

class kg_attendance_device_info(osv.osv):

	_name = "kg.attendance.device.info"
	_description = "Attendance Reader"
	_order = "punch_date desc"
	
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
				WHERE constraint_type = 'FOREIGN KEY' 
				AND ccu.table_name='%s')
				as sam  """ %('kg_attendance_device_info'))
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
		'update_date':fields.date('Last Update On',readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Update By', readonly=True),


		### Entry Info ###
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'active': fields.boolean('Active'),
		'date': fields.date('Date',readonly=False),

		## Module Requirement Info	
		
		'punch_date': fields.datetime('Punch Date'),
		'punch_time': fields.char('Punch Time',size=20),
		'machine_no': fields.integer('Machine NO'),
		'att_code': fields.char('Attendance Code'),
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.attendance.device.info', context=c),
		'active': True,
		'date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
	
	}
	
	### Basic Needs
	
	#~ def unlink(self,cr,uid,ids,context=None):
		#~ raise osv.except_osv(_('Warning!'),
				#~ _('You can not delete Entry !!'))
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_attendance_device_info, self).write(cr, uid, ids, vals, context)

	## Module Requirement
	
	def data_upload(self,cr,uid,ids=0,context=None):
		
		# To import file

		conn_string = "dbname='sam_phaseI' user='sujith' password='kgisl@123'"

		conn = psycopg2.connect(conn_string)
		cursor = conn.cursor()
		
		#~ wb = xlrd.open_workbook('/home/sujith/SVN_Projects/sam_turbo_dev/openerp-server/openerp/Exports.xls')
		#~ sh = wb.sheet_by_name('Sheet1')
		#~ your_csv_file = open('/home/sujith/SVN_Projects/sam_turbo_dev/openerp-server/openerp/Exports.csv', 'wb')
		#~ wr = csv.writer(your_csv_file, quoting=csv.QUOTE_ALL)
#~ 
		#~ for rownum in xrange(sh.nrows):
			#~ wr.writerow(sh.row_values(rownum))
#~ 
		#~ your_csv_file.close()

		reader = csv.reader(open('/home/sujith/SVN_Projects/sam_turbo_dev/openerp-server/openerp/Exports.csv','rb'),delimiter=';')
		print reader
		statement = ''
		i = 0;
		for row in reader:
			print "_________________________________________________________________________________",row[0]
			print "_________________________________________________________________________________",row[1]
			print "_________________________________________________________________________________",row[2]
			print "_________________________________________________________________________________",row[3]
			print "_________________________________________________________________________________",row[4]
			
			if i!=0:
				statement = "INSERT INTO kg_attendance_device_info (machine_no,date,punch_date,punch_time,att_code,active) VALUES ('"+str(row[0])+"','"+row[1]+"','"+row[2]+"','"+str(row[3])+"','"+str(row[4])+"','t') RETURNING id"
				cursor.execute(statement)
			conn.commit()
			i=1;
		
		# To delete file

		#~ os.remove("/home/sujith/SVN_Projects/sam_turbo_dev/openerp-server/openerp/Exports.csv")
		
		return True

	def attendance_entry_move(self,cr,uid,ids=0,context=None):
		print "function caught---------------------------------------------------------------------------"
		FMT = '%H:%M:%S'
		#~ month_obj = self.pool.get('kg.month')
		daily_obj = self.pool.get('kg.daily.attendance')
		line_obj = self.pool.get('ch.daily.attendance')
		att_device_obj = self.pool.get('kg.attendance.device.info')
		today = date.today()
		yesterday = today - timedelta(1)
		cur_month = yesterday.strftime('%B')
		cur_year = yesterday.year
		day_name = yesterday.strftime('%A')
		
		#~ month_id = month_obj.search(cr,uid,[('code','=',cur_month)])
		#~ print "_------------------------------",cur_month
		#~ stop
		daily_id = daily_obj.search(cr,uid,[('month','=',cur_month),('year','=',cur_year)])
		#~ print "------------------------------------------",month_id[0]
		print "------------------------------------------",cur_year
		#~ print "daily_iddaily_iddaily_iddaily_iddaily_iddaily_iddaily_iddaily_id",daily_id
		if daily_id:			
			for ele in daily_id:
				daily_rec = daily_obj.browse(cr,uid,ele)
				emp_id = daily_rec.employee_id.id
				att_code = '0000' + daily_rec.employee_id.att_code				
				print "------------------------------------------",yesterday
				
				#~ entry_ids = att_device_obj.search(cr,uid,[('att_code','=',att_code),
								#~ ('date','=',yesterday)])
				#~ entry_ids.sort()
				
				cr.execute("""select id,punch_time from kg_attendance_device_info where date ='%s' and att_code='%s'"""%(yesterday,att_code))
				entry_ids=cr.dictfetchall()
				entry_ids.sort(key=lambda entry_ids: (entry_ids['punch_time']),reverse=False)
				
				add_ids = line_obj.search(cr,uid,[('employee_id','=',emp_id),
									('date','=',yesterday),('header_id','=',ele)])
				if not add_ids:									
					if entry_ids:
						in1,in2,in3,in4,in5,in6,in7,in8 = 0,0,0,0,0,0,0,0
						out1,out2,out3,out4,out5,out6,out7,out8 = 0,0,0,0,0,0,0,0
						line_in1,line_in2,line_in3,line_in4,line_in5,line_in6,line_in7,line_in8 = '','','','','','','',''
						line_out1,line_out2,line_out3,line_out4,line_out5,line_out6,line_out7,line_out8 = '','','','','','','',''
						for pos1, item1 in enumerate(entry_ids):
							device_rec = att_device_obj.browse(cr,uid,item1['id'])
							#~ punch = 
							print "device_rec.punch_timedevice_rec.punch_timedevice_rec.punch_time",device_rec.punch_time[0:5]
							in_time_val = datetime.strptime(device_rec.punch_time[0:5], "%H:%M")
							out_time_val = datetime.strptime(device_rec.punch_time[0:5], "%H:%M")

							if pos1 == 0:
								in1=in_time_val
								line_in1 = device_rec.punch_time[0:5]
							elif pos1 == 2:
								in2 = in_time_val
								line_in2 = device_rec.punch_time[0:5]
							elif pos1 == 4:
								in3 = in_time_val
								line_in3 = device_rec.punch_time[0:5]
							elif pos1 == 6:
								in4 = in_time_val
								line_in4 = device_rec.punch_time[0:5]
							elif pos1 == 8:
								in5 = in_time_val
								line_in5 = device_rec.punch_time[0:5]
							elif pos1 == 10:								
								in6 = in_time_val
								line_in6 = device_rec.punch_time[0:5]
							elif pos1 == 12:								
								in7 = in_time_val
								line_in7 = device_rec.punch_time[0:5]
							elif pos1 == 14:								
								in8 = in_time_val
								line_in8 = device_rec.punch_time[0:5]					

							## IN PUNCH COMPLETED ##
							
							elif pos1 == 1:
								out1 = out_time_val
								line_out1 = device_rec.punch_time[0:5]
							elif pos1 == 3:
								out2 = out_time_val
								line_out2 = device_rec.punch_time[0:5]
							elif pos1 == 5:
								out3 = out_time_val
								line_out3 = device_rec.punch_time[0:5]
							elif pos1 == 7:
								out4 = out_time_val
								line_out4 = device_rec.punch_time[0:5]
							elif pos1 == 9:
								out5 = out_time_val
								line_out5 = device_rec.punch_time[0:5]
							elif pos1 == 11:
								out6 = out_time_val
								line_out6 = device_rec.punch_time[0:5]
							elif pos1 == 13:
								out7 = out_time_val
								line_out7 = device_rec.punch_time[0:5]
							elif pos1 == 15:
								out8 = out_time_val
								line_out8 = device_rec.punch_time[0:5]

						## OUT PUNCH COMPLETED
						
						######### TIME CALCULATION BETWEEN 2 PUNCH TIME #########
						
						time_list = []
						if out1 !=0:
							a1 = out1.strftime(FMT)
							b1 = in1.strftime(FMT)
							if a1 > b1:
								test1 = datetime.strptime(a1, FMT) - datetime.strptime(b1, FMT)
							else:
								test1 = datetime.strptime(b1, FMT) - datetime.strptime(a1, FMT)
								
							test1 = str(test1)
							print "test1test1test1test1test1",test1
							time_list.append(test1)
						else:
							tot_hrs1 = 0							
						
						if out2 !=0:
							a2 = out2.strftime(FMT)
							b2 = in2.strftime(FMT)
							if a2 > b2:
								test2 = datetime.strptime(a2, FMT) - datetime.strptime(b2, FMT)
							else:
								test2 = datetime.strptime(b2, FMT) - datetime.strptime(a2, FMT)
								
							test2 = str(test2)
							print "test2test2test2test2test2",test2
							time_list.append(test2)							
						else:
							tot_hrs2 = 0						
						
						if out3 !=0:
							a3 = out3.strftime(FMT)
							b3 = in3.strftime(FMT)
							if a3 > b3:
								test3 = datetime.strptime(a3, FMT) - datetime.strptime(b3, FMT)
							else:
								test3 = datetime.strptime(b3, FMT) - datetime.strptime(a3, FMT)
							test3 = str(test3)
							print "test3test3test3test3test3",test3
							time_list.append(test3)
						else:
							tot_hrs3 = 0

						if out4 !=0:							
							a4 = out4.strftime(FMT)
							b4 = in4.strftime(FMT)
							if a4 > b4:
								test4 = datetime.strptime(a4, FMT) - datetime.strptime(b4, FMT)
							else:
								test4 = datetime.strptime(b4, FMT) - datetime.strptime(a4, FMT)
								
							test4 = str(test4)
							print "test4test4test4test4test4",test4
							time_list.append(test4)
						else:
							tot_hrs4 = 0

						if out5 != 0:							
							a5 = out5.strftime(FMT)
							b5 = in5.strftime(FMT)
							if a5 > b5:
								test5 = datetime.strptime(a5, FMT) - datetime.strptime(b5, FMT)
							else:
								test5 = datetime.strptime(b5, FMT) - datetime.strptime(a5, FMT)
								
							test5 = str(test5)
							print "test5test5test5test5",test5
							time_list.append(test5)
						else:
							tot_hrs5 = 0						
						
						if out6 != 0:							
							a6 = out6.strftime(FMT)
							b6 = in6.strftime(FMT)
							if a6 > b6:
								test6 = datetime.strptime(a6, FMT) - datetime.strptime(b6, FMT)
							else:
								test6 = datetime.strptime(b6, FMT) - datetime.strptime(a6, FMT)
								
							test6 = str(test6)
							print "test6test6test6test6test6test6test6",test6
							time_list.append(test6)
						else:
							tot_hrs6 = 0
						
						if out7 != 0:							
							a7 = out7.strftime(FMT)
							b7 = in7.strftime(FMT)
							if a7 > b7:
								test7 = datetime.strptime(a7, FMT) - datetime.strptime(b7, FMT)
							else:
								test7 = datetime.strptime(b7, FMT) - datetime.strptime(a7, FMT)
								
							test7 = str(test7)
							print "test7test7test7test7test7",test7
							time_list.append(test7)
						else:
							tot_hrs7 = 0
						
						if out8 !=0:							
							#val8 = (out8 - in8) / 12
							a8 = out8.strftime(FMT)
							b8 = in8.strftime(FMT)
							if a8 > b8:
								test8 = datetime.strptime(a8, FMT) - datetime.strptime(b8, FMT)
							else:
								test8 = datetime.strptime(b8, FMT) - datetime.strptime(a8, FMT)
								
							test8 = str(test8)
							print "test8test8test8test8test8test8",test8
							time_list.append(test8)
							
							#if type(val8).__name__!='int':
								#tot_mins8 = (val8.seconds)
								#tot_hrs8 = tot_mins8 / 300.00
						else:
							tot_hrs8 = 0
							
						totalSecs = 0
						for tm in time_list:
							print "tmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm",tm
							timeParts = [int(s) for s in tm.split(':')]
							print "timepartnsssssssssssss",timeParts
							totalSecs += (timeParts[0] * 60 + timeParts[1]) * 60 + timeParts[2]
						
						totalSecs, sec = divmod(totalSecs, 60)
						hr, min = divmod(totalSecs, 60)
						tot_hrs = hr
						wk_hrs = "%d:%02d" % (hr, min)
						
						### Validating Using Shift Hours####
						
						#~ rec=self.browse(cr,uid,ids[0])
						check_emp = self.pool.get('hr.employee').search(cr,uid,[('att_code','=',att_code[4:8])])
						check_cont = self.pool.get('hr.contract').search(cr,uid,[('employee_id','=',check_emp[0])])
						if check_cont:
							print "************************************************",check_emp
							check_emp_1 = self.pool.get('hr.employee').browse(cr,uid,check_emp[0])
							check_con_1 = self.pool.get('hr.contract').browse(cr,uid,check_cont[0])
							check_emp_categ = self.pool.get('kg.employee.category').browse(cr,uid,check_emp_1.emp_categ_id.id)
							check_shift = self.pool.get('kg.shift.master').browse(cr,uid,check_emp_categ.shift_id.id)
							print "=========================",check_shift.shift_hours
							print "=========================",check_shift.start_time + check_shift.grace_period
							print "========tot_hrstot_hrs=================",tot_hrs
							
							line_in1_f = str(line_in1) .replace(':', '.')
						
							print "------------------------------------------------",float(line_in1_f)
							ot_hrs=0.00
							wk_hrs_f = str(wk_hrs) .replace(':', '.')
							print "sssssssssssssssssssssssssssssssssssssssssss",wk_hrs_f
							print "sssssssssssssssssssssssssssssssssssssssssss",check_shift.shift_hours
							print "sssssssssssssssssssssssssssssssssssssssssss",float(line_in1_f)
							print "sssssssssssssssssssssssssssssssssssssssssss",type(check_shift.start_time + check_shift.grace_period)
							
							### Validating Using Shift Hours####
							
							### OT hours calculation ###
							rmks=' '
							if  wk_hrs_f >= check_shift.shift_hours and  float(line_in1_f) <= check_shift.start_time + check_shift.grace_period:
								if check_con_1.ot_status is True:
									print "tot_hrstot_hrstot_hrstot_hrstot_hrstot_hrs",wk_hrs
									print "check_shift.shift_hourscheck_shift.shift_hours",check_shift.shift_hours
									
									a = float(wk_hrs_f) - check_shift.shift_hours
									if a > check_shift.min_ot_hours :
										b = a - check_shift.min_ot_hours
										print "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",b
										ot_hrs = b
										status = 'present'
									else:
										ot_hrs = '0.00'
										status = 'present'
								else:
									ot_hrs = '0.00'
									status = 'present'
								
							else:
								
								get_permission_id= self.pool.get('hr.holidays.status').search(cr,uid,[('code','=','PR')])
								perm_req=self.pool.get('hr.holidays').search(cr,uid,[('from_date','=',yesterday),('employee_id','=',emp_id),('holiday_status_id','=',get_permission_id[0]),('status','=','approved')])
								print "permission request --------------------------------------------------->>>>>>>>>>>>>>>>",perm_req
								if perm_req:
									perm_req_1=self.pool.get('hr.holidays').browse(cr,uid,perm_req)
									print "*****************",perm_req_1.permission_hrs
									total_hrs_1 = (perm_req_1.permission_hrs + wk_hrs_f)/2
									half_shift=(check_shift.shift_hours)/2
									if half_shift == total_hrs_1:
										status='halfday'
										rmks = 'Permission'+'='+perm_req_1.permission_hrs + wk_hrs_f
									else:
										ot_hrs = '0.00'
										status='absent'
										rmks='-'
								else:
									ot_hrs = '0.00'
									status = 'absent'
									rmks='-'
							
							### OT hours calculation ###
							
							line_vals = {

									'employee_id':emp_id,
									'date': device_rec.date,
									'in_time1': line_in1,
									'in_time2': line_in2,
									'in_time3': line_in3,
									'in_time4': line_in4,
									'in_time5': line_in5,
									'in_time6': line_in6,
									'in_time7': line_in7,
									'in_time8': line_in8,
									'out_time1': line_out1,
									'out_time2': line_out2,
									'out_time3': line_out3,
									'out_time4': line_out4,
									'out_time5': line_out5,
									'out_time6': line_out6,
									'out_time7': line_out7,
									'out_time8': line_out8,
									'header_id':ele,
									'tot_hrs': tot_hrs,
									'wk_time': wk_hrs,
									'status': status,
									'cur_day':day_name,
									'ot_hrs':ot_hrs,
									'remarks':rmks,

									}

							line_id = line_obj.create(cr,uid,line_vals)
					else:
						if day_name =='Sunday':
							status = 'weekoff'
						else:
							#~ status = 'absent'
							
							
							##### Checking the leave request and updating the daily attendance status as leave ######
							
							start_date = datetime(today.year, today.month, 1)
							end_date = datetime(today.year, today.month, calendar.mdays[today.month])
							print "***************************************",start_date
							print "***************************************",end_date

							lev_req= self.pool.get('hr.holidays').search(cr,uid,[('employee_id','=',emp_id),('from_date','>=',start_date),('to_date','<=',end_date),('status','=','approved')])
							print "emp_idemp_idemp_idemp_idemp_id",emp_id
							print "Leave request for current month",lev_req
							if lev_req:								
								for ii in lev_req:
									holi_rec = self.pool.get('hr.holidays').browse(cr,uid,ii)
									print "Leave type",holi_rec.holiday_status_id.name
									print "from_date",holi_rec.from_date
									print "to_date",holi_rec.to_date
									d1 = datetime.strptime(holi_rec.from_date, "%Y-%m-%d")
									d2 = datetime.strptime(holi_rec.to_date, "%Y-%m-%d")
									delta = d2 - d1
									print "delta -----------------------",delta
									
									for i in range(delta.days + 1):
										betw_days = d1 + td(days=i)
										d3 = datetime.strftime(yesterday, "%Y-%m-%d %H:%M:%S")
										print "*******d3d3d3d3d3******",d3
										print "***********betw_daysbetw_daysbetw_days**************",betw_days
										print "*******yesterdayyesterday******************",yesterday
										if str(d3) == str(betw_days):
											print "Updated++++++++%%%%%%%%%%%%%%%%%%%%%++++++++"
											get_on_duty_id= self.pool.get('hr.holidays.status').search(cr,uid,[('code','=','PR')])
											get_lop_id= self.pool.get('hr.holidays.status').search(cr,uid,[('code','=','LOP')])
											if holi_rec.holiday_status_id.id == get_on_duty_id[0]:
												status = 'onduty'
												rmks = holi_rec.holiday_status_id.name
											elif holi_rec.holiday_status_id.id == get_lop_id[0]:
												status = 'absent'
												rmks = holi_rec.holiday_status_id.name
												print "Updated++++++++++++++++++++++++++++++++++++++++++++++"
											else:
												status = 'leave'
												rmks = holi_rec.holiday_status_id.name
											break;
										else:
											status = 'absent'
											rmks = '-'
											
							##### Checking the leave request and updating the daily attendance status as leave ######
							
							else:
								status = 'absent'
								rmks = '-'
							
								#~ holidays =  self.pool.get('kg.holiday.master')
								#~ holiday_line =  self.pool.get('ch.holiday.master')
								#~ holidays_ids =  holidays.search(cr,uid,[('active','=',True)])
								#~ if holidays_ids:
									#~ holidays_line_ids = holiday_line.search(cr,uid,[('header_id','=',holidays_ids[0])])
									#~ for idsss in holidays_line_ids:
										#~ holiday_line_rec = holiday_line.browse(cr,uid,idsss)
										#~ if holiday_line_rec.leave_date == yesterday:
											#~ print "Holidays are caught---------------------------------------------------------->>>>>>>>>>>>"
											#~ print "Holidays are caught---------------------------------------------------------->>>>>>>>>>>>",holiday_line_rec.leave_date
											#~ status='holiday'
											#~ rmks = holiday_line_rec.note
									
							#~ 
							
						line_vals = {
									'employee_id':emp_id,
									'date': yesterday,
									'cur_day':day_name,
									'tot_hrs': 0,
									'wk_time':'00:00',
									'header_id':ele,
									'status': status,
									'ot_hrs':'00:00',
									'remarks':rmks,
									}
						ab_line_id = line_obj.create(cr,uid,line_vals)
				else:
					print "DATA UPDATED ALREADY !!!!!!!!!!"					

			return True

	


kg_attendance_device_info()
