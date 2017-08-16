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
#~ from datetime import date, datetime, timedelta
#~ from datetime import date, timedelta as td
logger = logging.getLogger('server')
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')
today = date.today()

class kg_excel_punching_report(osv.osv):

	_name = 'kg.excel.punching.report'
	_order = 'creation_date desc'
	
	_columns = {
		
		'creation_date': fields.date('Creation Date', readonly=True),
		'emp_categ_id':fields.many2many('kg.employee.category','kg_ex_pun_cat_rep_wiz','report_id','categ_id','Category'),
		'division_id':fields.many2many('kg.division.master','kg_ex_pun_div_rep_wiz','report_id','div_id','Division'),
		'employee_id':fields.many2many('hr.employee','kg_ex_pun_emp_rep_wiz','report_id','emp_id','Employee'),
		'report_type': fields.selection([('punching', 'Punching'),('late_punch', 'Late Punch'),('early_punch', 'Early Punch')],'Report Type'),
		'department_id':fields.many2many('kg.depmaster','kg_ex_adv_dep_rep_wiz','report_id','dep_id','Department'),
		'date_from': fields.date("Start Date",required=True),
		'date_to': fields.date("End Date",required=True),		
		#~ 'status': fields.selection([('approved', 'Approved'),('cancelled','Cancelled'),('pending','Pending')], "Status"),
		"rep_data":fields.binary("File",readonly=True),
		'state': fields.selection([('draft', 'Draft'),('done','Done')], 'Status', readonly=True),
		'company_id': fields.many2one('res.company', 'Company'),
		'name': fields.char("Report Name"),
		'month':fields.selection([('January','January'),('February','February'),('March','March'),('April','April'),('May','May'),
		('June','June'),('July','July'),('August','August'),('September','September'),('October','October'),('November','November'),('December','December')], 'Month'),
		'year': fields.selection([('2017','2017'),('2018','2018'),('2019','2019')], 'Year', readonly=False),
		
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
		
	def produce_xls(self, cr, uid, ids, context={}):
		
		rec = self.browse(cr,uid,ids[0])
		print "month filter..............................................",rec.month+'-'+rec.year
		
		month_yr = "'"+rec.month+'-'+rec.year+"'"
	
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
		department=[]
		employee = []
		employee_categ= []
		employee_div= []
		filter_emp = []
		filter_categ = []
		filter_div = []
		filter_dep = []
		
		if rec.employee_id:
			emp = [x.id for x in rec.employee_id]
			employee_ids = ",".join(str(x) for x in emp)
			employee.append("payslip.employee_id in (%s)"%(employee_ids))
			
			emp_name = [x.name_related for x in rec.employee_id]
			emp_names = ",".join(str(x) for x in emp_name)
			filter_emp.append("Employee : %s"%(emp_names))
		
		if rec.emp_categ_id:
			categ_id = [x.id for x in rec.emp_categ_id]
			emp_categ_ids = ",".join(str(x) for x in categ_id)
			category.append("emp_categ_id in (%s)"%(emp_categ_ids))
			sql = """select id from hr_employee where %s """%(category[0])
			cr.execute(sql)		
			data = cr.dictfetchall()
			emp_ids = [x['id'] for x in data]
			employee_ids_cat = ",".join(str(x) for x in emp_ids)
			employee_categ.append("employee_id in (%s)"%(employee_ids_cat))

		if rec.division_id:
			division_id = [x.id for x in rec.division_id]
			division_ids = ",".join(str(x) for x in division_id)
			division.append("division_id in (%s)"%(division_ids))
			sql = """select id from hr_employee where %s """%(division[0])
			cr.execute(sql)		
			data = cr.dictfetchall()
			emp_ids_div = [x['id'] for x in data]
			employee_ids_div= ",".join(str(x) for x in emp_ids_div)
			employee_div.append("employee_id in (%s)"%(employee_ids_div))
			
			
		if employee:
			employee = 'and '+' or '.join(employee)
			employee =  employee+' '
			
			filter_emp = filter_emp
		else:
			employee = ''
			filter_emp = ''
		
		if employee_categ:
			employee_categ = 'and '+' or '.join(employee_categ)
			employee_categ =  employee_categ+' '
	
		else:
			employee_categ = ''
			
		if employee_div:
			employee_div = 'and '+' or '.join(employee_div)
			employee_div =  employee_div+' '
			
			#~ filter_div = filter_div
		else:
			employee_div = ''
			#~ filter_div = ''
			
		if rec.report_type:
			report_type = rec.report_type
		else:
			report_type = ''
			
		
		date_from = "'"+rec.date_from+"'"
		date_to = 	"'"+rec.date_to+"'"
		
		
		if report_type == 'punching':
			sql = """	
			
									select 

					ROW_NUMBER() OVER(PARTITION BY employee.name_related) as row,
					case when ROW_NUMBER() OVER(PARTITION BY employee.name_related) = 1 then employee.name_related else '' end as emp_name,
					case when ROW_NUMBER() OVER(PARTITION BY category.name) = 1 then category.name else '' end as employee_category,
					case when ROW_NUMBER() OVER(PARTITION BY division.name) = 1 then division.name else '' end as employee_division,
					case when ROW_NUMBER() OVER(PARTITION BY employee.code) = 1 then employee.code else '' end as emp_code,
					to_char(daily_att.date,'dd/mm/yyyy') as punch_date,
					daily_att.cur_day as punch_day,
					daily_att.in_time1 as in_time1,
					daily_att.out_time1 as out_time1,
					daily_att.in_time2 as in_time2,
					daily_att.out_time2 as out_time2,
					daily_att.in_time3 as in_time3,
					daily_att.out_time3 as out_time3,
					daily_att.in_time4 as in_time4,
					daily_att.out_time4 as out_time4,
					daily_att.in_time5 as in_time5,
					daily_att.out_time5 as out_time5,
					daily_att.in_time6 as in_time6,
					daily_att.out_time6 as out_time6

					from ch_daily_attendance daily_att

					left join hr_employee employee on (employee.id=daily_att.employee_id)
					left join kg_employee_category category on (category.id=employee.emp_categ_id)
					left join kg_division_master division on (division.id=employee.division_id)

					where date >="""+date_from+""" and date<="""+date_to+' '+""" """+ employee_categ +""" """+ employee_div +""" """

					

			cr.execute(sql)		
			data = cr.dictfetchall()
			
			record={}
			sno=1
			wbk = xlwt.Workbook()
			style1 = xlwt.easyxf('font: bold on,height 240,color_index 0x95;' 'align: horiz left,vertical center;''borders: left thin, right thin, top thin,bottom thin') 
			style3 = xlwt.easyxf('font: bold off,height 240,color_index 0x95;' 'align: horiz left,vertical center;''borders: left thin, right thin, top thin,bottom thin') 
			style2 = xlwt.easyxf('font: bold on,height 240,color_index 0x95;' 'align: horiz center,vertical center;''borders: left thin, right thin, top thin ,bottom thin') 
			s1=0
			
			"""adding a worksheet along with name"""
			
			sheet1 = wbk.add_sheet('PUNCHING_REPORT')
			s2=6
			sheet1.col(0).width = 2000
			sheet1.col(1).width = 3000
			sheet1.col(2).width = 6000
			sheet1.col(3).width = 4000
			sheet1.col(4).width = 4000
			sheet1.col(5).width = 4000
			sheet1.col(6).width = 4000
			sheet1.col(7).width = 4000
			sheet1.col(8).width = 4000
			
			
			
			""" writing field headings """		

			date_from = datetime.strptime(rec.date_from, '%Y-%m-%d').strftime('%d/%m/%Y')
			date_to = datetime.strptime(rec.date_to, '%Y-%m-%d').strftime('%d/%m/%Y')
			
			
			sheet1.write_merge(0, 3, 0, 14,"SAM TURBO INDUSTRY PRIVATE LIMITED \n Avinashi Road, Neelambur,\n Coimbatore - 641062 \n Tel:3053555, 3053556,Fax : 0422-3053535",style2)
			sheet1.row(0).height = 450
			sheet1.write_merge(4, 4, 0, 14,"IN & OUT DETAILS - "+ date_from + " "+ "TO "+date_to,style2)
			sheet1.write_merge(5, 5, 0, 14,"",style2)
			#~ sheet1.write_merge(3, 3, 0, 5,"",style2)
			
			sheet1.insert_bitmap('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_reports/img/sam.bmp',0,0)
			sheet1.write(s2,0,"S.NO",style1)
			#~ sheet1.row(s1).height = 490
			sheet1.write(s2,1,"Emp.No",style1)
			sheet1.write(s2,2,"NAME",style1)
			sheet1.write(s2,3,"CATEGORY",style1)
			sheet1.write(s2,4,"DIVISION",style1)
			sheet1.write(s2,5,"PUNCH DATE",style1)
			sheet1.write(s2,6,"PUNCH DAY",style1)
			sheet1.write(s2,7,"IN",style1)
			sheet1.write(s2,8,"OUT",style1)
			sheet1.write(s2,9,"IN",style1)
			sheet1.write(s2,10,"OUT",style1)
			sheet1.write(s2,11,"IN",style1)
			sheet1.write(s2,12,"OUT",style1)
			sheet1.write(s2,13,"IN",style1)
			sheet1.write(s2,14,"OUT",style1)
			
			for ele in data:
			
				s2 = s2 + 1

				sheet1.write(s2,0,sno,style3)
				sheet1.write(s2,1,ele['emp_code'],style3)
				sheet1.write(s2,2,ele['emp_name'],style3)
				sheet1.write(s2,3,ele['employee_category'],style3)
				sheet1.write(s2,4,ele['employee_division'],style3)
				sheet1.write(s2,5,ele['punch_date'],style3)
				sheet1.write(s2,6,ele['punch_day'],style3)
				sheet1.write(s2,7,ele['in_time1'],style3)
				sheet1.write(s2,8,ele['out_time1'],style3)
				sheet1.write(s2,9,ele['in_time2'],style3)
				sheet1.write(s2,10,ele['out_time2'],style3)
				sheet1.write(s2,11,ele['in_time3'],style3)
				sheet1.write(s2,12,ele['out_time3'],style3)
				sheet1.write(s2,13,ele['in_time4'],style3)
				sheet1.write(s2,14,ele['out_time4'],style3)
				
				
				sno = sno + 1
			
			"""Parsing data as string """
			file_data=StringIO.StringIO()
			o=wbk.save(file_data)		
			"""string encode of data in wksheet"""		
			out=base64.encodestring(file_data.getvalue())
			"""returning the output xls as binary"""
			report_name = 'PUNCHING_REPORT' + '.' + 'xlsx'
		elif report_type == 'late_punch':
			sql = """	
			
							select 

			ROW_NUMBER() OVER(PARTITION BY employee.name_related) as row,
			case when ROW_NUMBER() OVER(PARTITION BY employee.name_related) = 1 then employee.name_related else '' end as emp_name,
			case when ROW_NUMBER() OVER(PARTITION BY category.name) = 1 then category.name else '' end as employee_category,
			case when ROW_NUMBER() OVER(PARTITION BY division.name) = 1 then division.name else '' end as employee_division,
			case when ROW_NUMBER() OVER(PARTITION BY employee.code) = 1 then employee.code else '' end as emp_code,
			to_char(daily_att.date,'dd/mm/yyyy') as punch_date,
			daily_att.cur_day as punch_day,
			daily_att.in_time1 as in_time1,
			shift.start_time as shift_time


			from ch_daily_attendance daily_att

			left join hr_employee employee on (employee.id=daily_att.employee_id)
			left join hr_contract contract on (contract.employee_id=employee.id)
			left join kg_shift_master shift on (shift.id=contract.shift_id)
			left join kg_employee_category category on (category.id=employee.emp_categ_id)
			left join kg_division_master division on (division.id=employee.division_id)

			where date >="""+date_from+""" and date<="""+date_to+' '+""" """+ employee_categ +""" """+ employee_div +""" """

					

			cr.execute(sql)		
			data = cr.dictfetchall()
			
			record={}
			sno=1
			wbk = xlwt.Workbook()
			style1 = xlwt.easyxf('font: bold on,height 240,color_index 0x95;' 'align: horiz left,vertical center;''borders: left thin, right thin, top thin,bottom thin') 
			style3 = xlwt.easyxf('font: bold off,height 240,color_index 0x95;' 'align: horiz left,vertical center;''borders: left thin, right thin, top thin,bottom thin') 
			style2 = xlwt.easyxf('font: bold on,height 240,color_index 0x95;' 'align: horiz center,vertical center;''borders: left thin, right thin, top thin ,bottom thin') 
			s1=0
			
			"""adding a worksheet along with name"""
			
			sheet1 = wbk.add_sheet('LATE_PUNCHING_REPORT')
			s2=6
			sheet1.col(0).width = 2000
			sheet1.col(1).width = 3000
			sheet1.col(2).width = 6000
			sheet1.col(3).width = 4000
			sheet1.col(4).width = 4000
			sheet1.col(5).width = 4000
			sheet1.col(6).width = 4000
			sheet1.col(7).width = 4000
			sheet1.col(8).width = 4000
			
			
			
			""" writing field headings """		

			date_from = datetime.strptime(rec.date_from, '%Y-%m-%d').strftime('%d/%m/%Y')
			date_to = datetime.strptime(rec.date_to, '%Y-%m-%d').strftime('%d/%m/%Y')
			
			
			sheet1.write_merge(0, 3, 0, 14,"SAM TURBO INDUSTRY PRIVATE LIMITED \n Avinashi Road, Neelambur,\n Coimbatore - 641062 \n Tel:3053555, 3053556,Fax : 0422-3053535",style2)
			sheet1.row(0).height = 450
			sheet1.write_merge(4, 4, 0, 14,"LATE PUNCH DETAILS - "+ date_from + " "+ "TO "+date_to,style2)
			sheet1.write_merge(5, 5, 0, 14,"",style2)
			#~ sheet1.write_merge(3, 3, 0, 5,"",style2)
			
			sheet1.insert_bitmap('/home/sujith/SVN_Projects/sam_turbo_dev/openerp-server/openerp/addons/kg_crm_offer/img/sam.bmp',0,0)
			sheet1.write(s2,0,"S.NO",style1)
			#~ sheet1.row(s1).height = 490
			sheet1.write(s2,1,"Emp.No",style1)
			sheet1.write(s2,2,"NAME",style1)
			sheet1.write(s2,3,"CATEGORY",style1)
			sheet1.write(s2,4,"DIVISION",style1)
			sheet1.write(s2,5,"PUNCH DATE",style1)
			sheet1.write(s2,6,"PUNCH DAY",style1)
			sheet1.write(s2,7,"RT.Time",style1)
			sheet1.write(s2,8,"IN",style1)
			sheet1.write(s2,9,"Late",style1)
			
			
			for ele in data:
			
				s2 = s2 + 1

				sheet1.write(s2,0,sno,style3)
				sheet1.write(s2,1,ele['emp_code'],style3)
				sheet1.write(s2,2,ele['emp_name'],style3)
				sheet1.write(s2,3,ele['employee_category'],style3)
				sheet1.write(s2,4,ele['employee_division'],style3)
				sheet1.write(s2,5,ele['punch_date'],style3)
				sheet1.write(s2,6,ele['punch_day'],style3)
				sheet1.write(s2,7,ele['in_time1'],style3)
				sheet1.write(s2,8,ele['shift_time'],style3)
				in_time = str(ele['in_time1']) .replace(':', '.')
				late_time = float(in_time)-ele['shift_time']
				if late_time < 0.00:
					late_time = 0.00
				
				sheet1.write(s2,9,late_time,style3)

			
			"""Parsing data as string """
			file_data=StringIO.StringIO()
			o=wbk.save(file_data)		
			"""string encode of data in wksheet"""		
			out=base64.encodestring(file_data.getvalue())
			"""returning the output xls as binary"""
			report_name = 'PUNCHING_REPORT' + '.' + 'xlsx'
		else:
			sql = """	
			
							select 

			ROW_NUMBER() OVER(PARTITION BY employee.name_related) as row,
			case when ROW_NUMBER() OVER(PARTITION BY employee.name_related) = 1 then employee.name_related else '' end as emp_name,
			case when ROW_NUMBER() OVER(PARTITION BY category.name) = 1 then category.name else '' end as employee_category,
			case when ROW_NUMBER() OVER(PARTITION BY division.name) = 1 then division.name else '' end as employee_division,
			case when ROW_NUMBER() OVER(PARTITION BY employee.code) = 1 then employee.code else '' end as emp_code,
			to_char(daily_att.date,'dd/mm/yyyy') as punch_date,
			daily_att.cur_day as punch_day,
			daily_att.out_time6 as out_time4,
			shift.end_time as shift_time


			from ch_daily_attendance daily_att

			left join hr_employee employee on (employee.id=daily_att.employee_id)
			left join hr_contract contract on (contract.employee_id=employee.id)
			left join kg_shift_master shift on (shift.id=contract.shift_id)
			left join kg_employee_category category on (category.id=employee.emp_categ_id)
			left join kg_division_master division on (division.id=employee.division_id)

			where daily_att.date >="""+date_from+""" and daily_att.date<="""+date_to+' '+""" """+ employee_categ +""" """+ employee_div +""" """

					

			cr.execute(sql)		
			data = cr.dictfetchall()
			
			record={}
			sno=1
			wbk = xlwt.Workbook()
			style1 = xlwt.easyxf('font: bold on,height 240,color_index 0x95;' 'align: horiz left,vertical center;''borders: left thin, right thin, top thin,bottom thin') 
			style3 = xlwt.easyxf('font: bold off,height 240,color_index 0x95;' 'align: horiz left,vertical center;''borders: left thin, right thin, top thin,bottom thin') 
			style2 = xlwt.easyxf('font: bold on,height 240,color_index 0x95;' 'align: horiz center,vertical center;''borders: left thin, right thin, top thin ,bottom thin') 
			s1=0
			
			"""adding a worksheet along with name"""
			
			sheet1 = wbk.add_sheet('EARLY_GOING_PUNCHING_REPORT')
			s2=6
			sheet1.col(0).width = 2000
			sheet1.col(1).width = 3000
			sheet1.col(2).width = 6000
			sheet1.col(3).width = 4000
			sheet1.col(4).width = 4000
			sheet1.col(5).width = 4000
			sheet1.col(6).width = 4000
			sheet1.col(7).width = 4000
			sheet1.col(8).width = 4000
			
			
			
			""" writing field headings """		

			date_from = datetime.strptime(rec.date_from, '%Y-%m-%d').strftime('%d/%m/%Y')
			date_to = datetime.strptime(rec.date_to, '%Y-%m-%d').strftime('%d/%m/%Y')
			
			
			sheet1.write_merge(0, 3, 0, 14,"SAM TURBO INDUSTRY PRIVATE LIMITED \n Avinashi Road, Neelambur,\n Coimbatore - 641062 \n Tel:3053555, 3053556,Fax : 0422-3053535",style2)
			sheet1.row(0).height = 450
			sheet1.write_merge(4, 4, 0, 14,"EARLY GOING PUNCH DETAILS - "+ date_from + " "+ "TO "+date_to,style2)
			sheet1.write_merge(5, 5, 0, 14,"",style2)
			#~ sheet1.write_merge(3, 3, 0, 5,"",style2)
			
			sheet1.insert_bitmap('/home/sujith/SVN_Projects/sam_turbo_dev/openerp-server/openerp/addons/kg_crm_offer/img/sam.bmp',0,0)
			sheet1.write(s2,0,"S.NO",style1)
			#~ sheet1.row(s1).height = 490
			sheet1.write(s2,1,"Emp.No",style1)
			sheet1.write(s2,2,"NAME",style1)
			sheet1.write(s2,3,"CATEGORY",style1)
			sheet1.write(s2,4,"DIVISION",style1)
			sheet1.write(s2,5,"PUNCH DATE",style1)
			sheet1.write(s2,6,"PUNCH DAY",style1)
			sheet1.write(s2,7,"RT.Time",style1)
			sheet1.write(s2,8,"IN",style1)
			sheet1.write(s2,9,"Late",style1)
			
			
			for ele in data:
			
				s2 = s2 + 1

				sheet1.write(s2,0,sno,style3)
				sheet1.write(s2,1,ele['emp_code'],style3)
				sheet1.write(s2,2,ele['emp_name'],style3)
				sheet1.write(s2,3,ele['employee_category'],style3)
				sheet1.write(s2,4,ele['employee_division'],style3)
				sheet1.write(s2,5,ele['punch_date'],style3)
				sheet1.write(s2,6,ele['punch_day'],style3)
				sheet1.write(s2,7,ele['out_time4'],style3)
				sheet1.write(s2,8,ele['shift_time'],style3)
				out_time4 = str(ele['out_time4']) .replace(':', '.')
				print "out_time4out_time4out_time4",out_time4
				if out_time4 == 'None':
					out_time4 =0.0
					print "&&&&&&&&&&&&&&&&&&&&"
				else:
					out_time4 =out_time4
					print "__________________________________________"
				print "out_time4out_time4out_time4",out_time4
				early_time = float(out_time4)-ele['shift_time']
				if early_time < 0.00:
					early_time = 0.00
				
				sheet1.write(s2,9,early_time,style3)

			
			"""Parsing data as string """
			file_data=StringIO.StringIO()
			o=wbk.save(file_data)		
			"""string encode of data in wksheet"""		
			out=base64.encodestring(file_data.getvalue())
			"""returning the output xls as binary"""
			report_name = 'EARLY_GOING_PUNCHING_REPORT' + '.' + 'xlsx'
		
		return self.write(cr, uid, ids, {'rep_data':out,'state':'done','name':report_name,},context=context)
		
kg_excel_punching_report()