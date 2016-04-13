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

class kg_attendance_reader(osv.osv):

	_name = "kg.attendance.reader"
	_description = "Attendance Reader"
	_order = "punch_date desc"
	
	_columns = {
		
		'employee_id':fields.char('Employee code'),
		'active': fields.boolean('Active'),
		'date': fields.date('Date'),
		'punch_date': fields.datetime('Punch Date'),
		'punch_time': fields.char('Punch Time',size=20),
		'punch_type': fields.selection([('IN','IN'),('OUT','OUT')],'Punch Type'),
		'machine_no': fields.integer('Machine NO'),
		'time_in': fields.float('Test Time'),
		
	}
	
	_defaults = {
	
	'active': True,	
	
	}

	def attendance_entry_move(self,cr,uid,ids=0,context=None):
		FMT = '%H:%M:%S'
		month_obj = self.pool.get('kg.month')
		daily_obj = self.pool.get('kg.daily.attendance')
		line_obj = self.pool.get('attendance.line')
		att_device_obj = self.pool.get('kg.attendance.reader')
		today = date.today()
		yesterday = today - timedelta(1)
		cur_month = yesterday.strftime('%B')
		cur_year = yesterday.year
		day_name = yesterday.strftime('%A')
		
		month_id = month_obj.search(cr,uid,[('code','=',cur_month)])
		daily_id = daily_obj.search(cr,uid,[('month','=',month_id[0]),('year','=',cur_year)])
		if daily_id:			
			for ele in daily_id:
				daily_rec = daily_obj.browse(cr,uid,ele)
				emp_id = daily_rec.employee_id.id
				att_code = daily_rec.employee_id.att_code				
				entry_ids = att_device_obj.search(cr,uid,[('employee_id','=',att_code),
								('date','=',yesterday)])
				entry_ids.sort()
				add_ids = line_obj.search(cr,uid,[('employee_id','=',emp_id),
									('date','=',yesterday),('attendance_id','=',ele)])
				if not add_ids:									
					if entry_ids:
						in1,in2,in3,in4,in5,in6,in7,in8 = 0,0,0,0,0,0,0,0
						out1,out2,out3,out4,out5,out6,out7,out8 = 0,0,0,0,0,0,0,0
						line_in1,line_in2,line_in3,line_in4,line_in5,line_in6,line_in7,line_in8 = '','','','','','','',''
						line_out1,line_out2,line_out3,line_out4,line_out5,line_out6,line_out7,line_out8 = '','','','','','','',''
						for pos1, item1 in enumerate(entry_ids):
							device_rec = att_device_obj.browse(cr,uid,item1)
							in_time_val = datetime.strptime(device_rec.punch_time, "%H:%M")
							out_time_val = datetime.strptime(device_rec.punch_time, "%H:%M")

							if pos1 == 0:
								in1=in_time_val
								line_in1 = device_rec.punch_time
							elif pos1 == 2:
								in2 = in_time_val
								line_in2 = device_rec.punch_time
							elif pos1 == 4:
								in3 = in_time_val
								line_in3 = device_rec.punch_time
							elif pos1 == 6:
								in4 = in_time_val
								line_in4 = device_rec.punch_time
							elif pos1 == 8:
								in5 = in_time_val
								line_in5 = device_rec.punch_time
							elif pos1 == 10:								
								in6 = in_time_val
								line_in6 = device_rec.punch_time
							elif pos1 == 12:								
								in7 = in_time_val
								line_in7 = device_rec.punch_time
							elif pos1 == 14:								
								in8 = in_time_val
								line_in8 = device_rec.punch_time						

							## IN PUNCH COMPLETED ##
							
							elif pos1 == 1:
								out1 = out_time_val
								line_out1 = device_rec.punch_time
							elif pos1 == 3:
								out2 = out_time_val
								line_out2 = device_rec.punch_time
							elif pos1 == 5:
								out3 = out_time_val
								line_out3 = device_rec.punch_time
							elif pos1 == 7:
								out4 = out_time_val
								line_out4 = device_rec.punch_time
							elif pos1 == 9:
								out5 = out_time_val
								line_out5 = device_rec.punch_time
							elif pos1 == 11:
								out6 = out_time_val
								line_out6 = device_rec.punch_time
							elif pos1 == 13:
								out7 = out_time_val
								line_out7 = device_rec.punch_time
							elif pos1 == 15:
								out8 = out_time_val
								line_out8 = device_rec.punch_time

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
							time_list.append(test7)
						else:
							tot_hrs7 = 0
						
						if out8 !=0:							
							#val8 = (out8 - in8) / 12
							a8 = out8.strftime(FMT)
							b8 = in8.strftime(FMT)
							if a7 > b7:
								test8 = datetime.strptime(a8, FMT) - datetime.strptime(b8, FMT)
							else:
								test8 = datetime.strptime(b8, FMT) - datetime.strptime(a8, FMT)
								
							test8 = str(test8)
							time_list.append(test8)
							
							#if type(val8).__name__!='int':
								#tot_mins8 = (val8.seconds)
								#tot_hrs8 = tot_mins8 / 300.00
						else:
							tot_hrs8 = 0
							
						totalSecs = 0
						for tm in time_list:
							timeParts = [int(s) for s in tm.split(':')]
							totalSecs += (timeParts[0] * 60 + timeParts[1]) * 60 + timeParts[2]
						totalSecs, sec = divmod(totalSecs, 60)
						hr, min = divmod(totalSecs, 60)
						tot_hrs = hr
						wk_hrs = "%d:%02d" % (hr, min)
						
						if tot_hrs >= 8 and day_name !='Sunday':
							status = 'present'
						elif tot_hrs < 8 and day_name !='Sunday':
							status = 'absent'
						else:
							status = 'weekoff'
						
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
								'attendance_id':ele,
								'tot_hrs': tot_hrs,
								'wk_time': wk_hrs,
								'status': status,
								'cur_day':day_name,

								}

						line_id = line_obj.create(cr,uid,line_vals)
					else:
						if day_name =='Sunday':
							status = 'weekoff'
						else:
							status = 'absent'
							
						line_vals = {
									'employee_id':emp_id,
									'date': yesterday,
									'cur_day':day_name,
									'tot_hrs': 0,
									'wk_time':'00:00',
									'attendance_id':ele,
									'status': status,
									}
						ab_line_id = line_obj.create(cr,uid,line_vals)
				else:
					print "DATA UPDATED ALREADY !!!!!!!!!!"					

			return True

	def unlink(self,cr,uid,ids,context=None):
		raise osv.except_osv(_('Warning!'),
				_('You can not delete Entry !!'))


kg_attendance_reader()
