import time
from lxml import etree
from osv import fields, osv
from tools.translate import _
import pooler
import logging
import netsvc
import datetime as lastdate
import datetime as lastdate
from datetime import datetime
from datetime import timedelta
from datetime import date
from dateutil import relativedelta
import datetime
import calendar
from datetime import datetime
import ast
logger = logging.getLogger('server')
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')
today = date.today()

class kg_excel_ot_report(osv.osv):

	_name = 'kg.excel.ot.report'
	_order = 'creation_date desc'
	
	_columns = {
		
		'creation_date': fields.date('Creation Date', readonly=True),
		'emp_categ_id':fields.many2many('kg.employee.category','kg_ex_att_cat_rep_wiz','report_id','categ_id','Category'),
		'division_id':fields.many2many('kg.division.master','kg_ex_att_div_rep_wiz','report_id','div_id','Division'),
		'employee_id':fields.many2many('hr.employee','kg_ex_att_emp_rep_wiz','report_id','emp_id','Employee'),
		'date_from': fields.date("Start Date",required=True),
		'date_to': fields.date("End Date",required=True),		
		'status': fields.selection([('approved', 'Approved'),('cancelled','Cancelled'),('pending','Pending')], "Status"),
		"rep_data":fields.binary("File",readonly=True),
		'state': fields.selection([('draft', 'Draft'),('done','Done')], 'Status', readonly=True),
		'company_id': fields.many2one('res.company', 'Company'),
		'name': fields.char("Report Name"),
		'month':fields.selection([('January','January'),('February','February'),('March','March'),('April','April'),('May','May'),
		('June','June'),('July','July'),('August','August'),('September','September'),('October','October'),('November','November'),('December','December')], 'Month'),
		'year': fields.selection([('2017','2017'),('2018','2018'),('2019','2019')], 'Year', readonly=False),
		'report_type': fields.selection([('ot_report','OT Report'),('ot_sheet','OT Sheet')], 'Type', readonly=False),
		
		}
	
	
	_defaults = {
		
		'state': 'draft',
		'creation_date' : fields.date.context_today,
		'date_from' : lambda * a: time.strftime('%Y-%m-%d'),
		'date_to' : lambda * a: time.strftime('%Y-%m-%d'),
		'year': '2017',
		'month':lambda * a: today.strftime('%B'),
		}
		
	def _date_validation(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.date_from > rec.date_to:
			raise osv.except_osv(_('Warning!'),
				_('End Date should be greater than Start Date'))
		return True
	
	_constraints = [

		(_date_validation, 'Future dates are not allowed for Date of Joining!!', [' ']),		
		
	]
	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state not in ('draft','cancel'):				
				raise osv.except_osv(_('Warning!'),
						_('You cannot delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def produce_xls(self, cr, uid, ids, context={}):
		
		rec = self.browse(cr,uid,ids[0])
	
		import StringIO
		import base64
		
		try:
			import xlwt
		except:
		   raise osv.except_osv('Warning !','Please download python xlwt module from\nhttp://pypi.python.org/packages/source/x/xlwt/xlwt-0.7.2.tar.gz\nand install it')
		   
		rec =self.browse(cr,uid,ids[0])
		
		where_sql = []
		category=[]
		division=[]
		employee = []
		filter_emp = []
		filter_categ = []
		filter_div = []
		
		if rec.employee_id:
			emp = [x.id for x in rec.employee_id]
			employee_ids = ",".join(str(x) for x in emp)
			employee.append("daily_att_main.employee_id in (%s)"%(employee_ids))
			
			emp_name = [x.name_related for x in rec.employee_id]
			emp_names = ",".join(str(x) for x in emp_name)
			filter_emp.append("Employee : %s"%(emp_names))
		
		if rec.emp_categ_id:
			categ_id = [x.id for x in rec.emp_categ_id]
			emp_categ_ids = ",".join(str(x) for x in categ_id)
			category.append("daily_att_main.emp_categ_id in (%s)"%(emp_categ_ids))
			
			categ_name = [x.name for x in rec.emp_categ_id]
			categ_names = ",".join(str(x) for x in categ_name)
			filter_categ.append("Category : %s"%(categ_names))
			
		if rec.division_id:
			division_id = [x.id for x in rec.division_id]
			division_ids = ",".join(str(x) for x in division_id)
			division.append("daily_att_main.division_id in (%s)"%(division_ids))
			
			div_name = [x.name for x in rec.division_id]
			div_names = ",".join(str(x) for x in div_name)
			filter_div.append("Division : %s"%(div_names))
		
		if employee:
			employee = 'and '+' or '.join(employee)
			employee =  employee+' '
			
			filter_emp = filter_emp
		else:
			employee = ''
			filter_emp = ''
		
		if category:
			category = 'and '+' or '.join(category)
			category =  category+' '
			
			filter_categ = filter_categ 
		else:
			category = ''
			filter_categ = ''
			
		if division:
			division = 'and '+' or '.join(division)
			division =  division+' '
			
			filter_div = filter_div
		else:
			division = ''
			filter_div = ''
		
		date_from = "'"+rec.date_from+"'"
		date_to = 	"'"+rec.date_to+"'"
		
		#### Report seperation occurs ###########
		wbk = xlwt.Workbook()
		style1 = xlwt.easyxf('font: bold off,height 240,color_index 0x95;' 'align: horiz left,vertical center;''borders: left thin, right thin, top thin,bottom thin') 
		style2 = xlwt.easyxf('font: bold on,height 240,color_index 0x95;' 'align: horiz center;''borders: left thin, right thin, top thin ,bottom thin') 		
		if rec.report_type == 'ot_report':
		
			sql = """	
			
				select 

				employee.name_related as employee_name,
				contract.sal_acc_no as account_no,
				payslip.id as pay_id,
				daily_att.employee_id as employee_id,
				shift.shift_hours as shift_hrs,
				sum(replace(daily_att.ot_hrs,':','.')::float) as ot_hrs,

				(select amount from hr_payslip_line where slip_id=payslip.id and code='BASIC') as basic,
				(select amount from hr_payslip_line where slip_id=payslip.id and code='VDA') as vda,
				(select worked_days from kg_monthly_attendance where start_date="""+date_from+""" and end_date="""+date_to+""" and employee_id=daily_att.employee_id) as worked_days


				from ch_daily_attendance daily_att

				left join hr_employee employee on (employee.id=daily_att.employee_id)
				left join kg_daily_attendance daily_att_main on (daily_att_main.id=daily_att.header_id)
				left join hr_contract contract on (contract.employee_id=employee.id)
				left join kg_shift_master shift on (shift.id=contract.shift_id)
				left join hr_payslip payslip on (payslip.id = (select id from hr_payslip where date_from ="""+date_from+""" and date_to="""+date_to+""" and employee_id=daily_att.employee_id))

				where daily_att.date >="""+date_from+""" and daily_att.date <="""+date_to+' '+"""  """+ category+ """ """+ division+ """ group by 1,2,3,4,5 """

			cr.execute(sql)		
			data = cr.dictfetchall()
			
			record={}
			sno=1
			s1=0
			
			"""adding a worksheet along with name"""
			
			sheet1 = wbk.add_sheet('OT_REPORT')
			s2=6
			sheet1.col(0).width = 2000
			sheet1.col(1).width = 6000
			sheet1.col(2).width = 5000
			sheet1.col(3).width = 4000
			sheet1.col(4).width = 5000
			sheet1.col(5).width =6000

			""" writing field headings """
		
			date_from = datetime.strptime(rec.date_from, '%Y-%m-%d').strftime('%d/%m/%Y')
			date_to = datetime.strptime(rec.date_to, '%Y-%m-%d').strftime('%d/%m/%Y')
			
			sheet1.write_merge(0, 3, 0, 5,"SAM TURBO INDUSTRY PRIVATE LIMITED \n Avinashi Road, Neelambur,\n Coimbatore - 641062 \n Tel:3053555, 3053556,Fax : 0422-3053535",style2)
			sheet1.row(0).height = 450
			sheet1.write_merge(4, 4, 0,5,"EXTRA ALLOW FOR THE PERIOD "+ date_from + " "+ "TO "+date_to,style1)
			sheet1.write_merge(5, 5, 0,5,"",style2)
			sheet1.insert_bitmap('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_reports/img/sam.bmp',0,0)
			sheet1.write(s2,0,"S.NO",style1)
			sheet1.write(s2,1,"ACCOUNT NO",style1)
			sheet1.write(s2,2,"STAFF",style1)
			sheet1.write(s2,3,"OT HOURS",style1)
			sheet1.write(s2,4,"RATE PER HOUR",style1)
			sheet1.write(s2,5,"AMOUNT",style1)
			
			for ele in data:
				s2+=1
				if ele['basic'] or ele['vda']:
					
					if ele['worked_days']:
						ele['worked_days'] = ele['worked_days']
					else:
						ele['worked_days'] = 0.00
					if ele['basic']:
						ele['basic'] = ele['basic']
					else:
						ele['basic'] = 0.00
					if ele['vda']:
						ele['vda'] = ele['vda']
					else:
						ele['vda'] = 0.00
					if ele['shift_hrs']:
						ele['shift_hrs'] = ele['shift_hrs']
					else:
						ele['shift_hrs'] = 0.00
					rate_per_hr = ((ele['basic']+ele['vda'])/ele['worked_days'])/ele['shift_hrs']
				else:
					rate_per_hr = 0.00
				sheet1.write(s2,0,sno,style1)
				sheet1.write(s2,1,ele['account_no'],style1)
				sheet1.write(s2,2,ele['employee_name'],style1)
				sheet1.write(s2,3,ele['ot_hrs'],style1)
				sheet1.write(s2,4,round(rate_per_hr,2),style1)
				sheet1.write(s2,5,ele['ot_hrs']*round(rate_per_hr,2),style1)
				sno = sno + 1

			report_name = 'OT_REPORT' + '.' + 'xls'
			
		else:
			sheet1 = wbk.add_sheet('OT_SHEET')
			sqlone = """		
					select 
					employee.name_related as employee_name,
					contract.sal_acc_no as account_no,
					payslip.id as pay_id,
					daily_att.employee_id as employee_id,
					shift.shift_hours as shift_hrs,
					daily_att.ot_hrs as ot_hrs,
					sum(replace(daily_att.ot_hrs,':','.')::float) over (partition by employee.name_related) as ot_hrs_sum,
					(select amount from hr_payslip_line where slip_id=payslip.id and code='BASIC') as basic,
					(select amount from hr_payslip_line where slip_id=payslip.id and code='VDA') as vda,
					(select worked_days from kg_monthly_attendance where start_date="""+date_from+""" and end_date="""+date_to+""" and employee_id=daily_att.employee_id) as worked_days,
					coalesce((extract(day from daily_att.date)),0) as ref_day
					from ch_daily_attendance daily_att
					left join hr_employee employee on (employee.id=daily_att.employee_id)
					left join kg_daily_attendance daily_att_main on (daily_att_main.id=daily_att.header_id)
					left join hr_contract contract on (contract.employee_id=employee.id) 
					left join kg_shift_master shift on (shift.id=contract.shift_id)
					left join hr_payslip payslip on (payslip.id = (select id from hr_payslip where date_from ="""+date_from+""" and date_to="""+date_to+""" and employee_id=daily_att.employee_id))"""
			sqltwo = """ ot_hrs is not null and daily_att.date >="""+date_from+""" and daily_att.date <="""+date_to+' '+"""  """+ category+ """ """+ division
			sqlfin = sqlone+""" where """+sqltwo
			cnt_sql = """ select count(*) from ("""+sqlfin+""" ) as sample """
			cr.execute(cnt_sql)		
			cnt_data = cr.dictfetchall()
			print "cnt_data ===",cnt_data
			if cnt_data:
				cnt_data = cnt_data[0]
				if cnt_data['count'] > 0:
					record={}
					date_to = datetime.strptime(rec.date_to, '%Y-%m-%d').strftime('%d/%m/%Y')
					print "date_todate_todate_todate_todate_to",date_to[:2]
					s2=6
					month_last_day = int(date_to[:2])+1
					sheet1.col(0).width = 2000
					sheet1.col(1).width = 6000
					sheet1.col(2).width = 5000
					ii = 3
					for i in range(1,month_last_day):
						sheet1.col(ii).width = 2000
						ii = ii+1 
					""" writing field headings """
					date_from = datetime.strptime(rec.date_from, '%Y-%m-%d').strftime('%d/%m/%Y')
					date_to = datetime.strptime(rec.date_to, '%Y-%m-%d').strftime('%d/%m/%Y')
					print "date_todate_todate_todate_todate_to",date_to[:2]
					sheet1.write_merge(0, 3, 0, month_last_day+4,"SAM TURBO INDUSTRY PRIVATE LIMITED \n Avinashi Road, Neelambur,\n Coimbatore - 641062 \n Tel:3053555, 3053556,Fax : 0422-3053535",style2)
					sheet1.row(0).height = 450
					sheet1.write_merge(4, 4, 0,month_last_day+4,"EXTRA ALLOW FOR THE PERIOD "+ date_from + " "+ "TO "+date_to,style1)
					sheet1.write_merge(5, 5, 0,month_last_day+4,"",style2)
					sheet1.insert_bitmap('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_reports/img/sam.bmp',0,0)
					sheet1.write(s2,0,"S.NO",style1)
					sheet1.write(s2,1,"ACCOUNT NO",style1)
					sheet1.write(s2,2,"NAME",style1)
					
					for i in range(1,month_last_day):
						print "iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii",i
						sheet1.write(s2,2+i,"Day "+str(i),style1)
					print "month_last_daymonth_last_daymonth_last_day",month_last_day
					sheet1.write(s2,(month_last_day-1)+3,"OT HOURS",style1)
					sheet1.write(s2,(month_last_day-1)+4,"RATE PER HOUR",style1)
					sheet1.write(s2,(month_last_day-1)+5,"AMOUNT",style1)
					
					head_sql = """ select distinct employee_name as emp,account_no as acc_no,sum(basic) over (partition by employee_name) as basic,sum(vda) over (partition by employee_name) as vda,sum(worked_days) over (partition by employee_name) as worked_days,shift_hrs as shift_hrs,
					ot_hrs_sum from ("""+sqlfin+""" ) as sam order by 1"""
					print "head_sqlhead_sqlhead_sqlhead_sql",head_sql
					#~ stop
					cr.execute(head_sql)		
					head_data = cr.dictfetchall()
					if head_data:
						sno = 1
						for head in head_data:
							s2+=1
							c1 = 0
							sheet1.write(s2,c1,sno,style1)
							sheet1.write(s2,c1+1,head['acc_no'],style1)
							sheet1.write(s2,c1+2,head['emp'],style1)								
							cond_chk = """ where employee.name_related = '%s' and """ % (head['emp'])
							sqlloop = sqlone+cond_chk+sqltwo							
							cr.execute(sqlloop)		
							loop_data = cr.dictfetchall()
							if loop_data:
								c1 = c1+3
								for i in range(1,month_last_day):
									sql_day = """ where employee.name_related = '%s' and coalesce((extract(day from daily_att.date)),0) = %s and""" % (head['emp'],i)
									ref_day = sqlone+sql_day+sqltwo
									cr.execute(ref_day)		
									day_data = cr.dictfetchall()
									if day_data:
										for loop in day_data:
											sheet1.write(s2,c1,loop['ot_hrs'],style1)
									else:
										sheet1.write(s2,c1,0,style1)
									c1 = c1 +1
							else:
								pass
							print "head['basic']head['basic']head['basic']head['basic']",head['basic']
							print "head['vda']head['vda']head['vda']head['vda']",head['vda']
							if head['basic'] or head['vda']:
					
								if head['worked_days']:
									head['worked_days'] = head['worked_days']
								else:
									head['worked_days'] = 0.00
								if head['basic']:
									head['basic'] = head['basic']
								else:
									head['basic'] = 0.00
								if head['vda']:
									head['vda'] = head['vda']
								else:
									head['vda'] = 0.00
								if head['shift_hrs']:
									head['shift_hrs'] = head['shift_hrs']
								else:
									head['shift_hrs'] = 0.00
								rate_per_hr = ((head['basic']+head['vda'])/head['worked_days'])/head['shift_hrs']
								print "c1111111111111111111111111111",c1
								sheet1.write(s2,c1,head['ot_hrs_sum'],style1)		
								sheet1.write(s2,c1+1,round(rate_per_hr,2),style1)		
								sheet1.write(s2,c1+2,head['ot_hrs_sum']*round(rate_per_hr,2),style1)
							else:
								sheet1.write(s2,c1,0,style1)		
								sheet1.write(s2,c1+1,0,style1)		
								sheet1.write(s2,c1+2,0,style1)
							sno += 1								
					else:
						pass
				else:
					sheet1.write_merge(0, 3, 0, 10, 'No record Exists', xlwt.easyxf('font: height 220,name Calibri;font: bold on;align: wrap on, horiz center;border: top thin, bottom thin, left thin, right thin;'))
										
		"""Parsing data as string """
		file_data=StringIO.StringIO()
		o=wbk.save(file_data)		
		"""string encode of data in wksheet"""		
		out=base64.encodestring(file_data.getvalue())
		"""returning the output xls as binary"""
		report_name = 'OT_SHEET' + '.' + 'xls'				
		return self.write(cr, uid, ids, {'rep_data':out,'state':'done','name':report_name,},context=context)
		
kg_excel_ot_report()
