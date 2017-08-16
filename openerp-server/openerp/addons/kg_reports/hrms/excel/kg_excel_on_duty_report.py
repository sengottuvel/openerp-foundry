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

class kg_excel_on_duty_report(osv.osv):

	_name = 'kg.excel.on.duty.report'
	_order = 'creation_date desc'
	
	_columns = {
		
		'creation_date': fields.date('Creation Date', readonly=True),
		'emp_categ_id':fields.many2many('kg.employee.category','kg_ex_per_rep_wiz','report_id','categ_id','Category'),
		'division_id':fields.many2many('kg.division.master','kg_ex_per_div_rep_wiz','report_id','div_id','Division'),
		'employee_id':fields.many2many('hr.employee','kg_ex_per_emp_rep_wiz','report_id','emp_id','Employee'),
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
			employee.append("leaves.employee_id in (%s)"%(employee_ids))
			
			emp_name = [x.name_related for x in rec.employee_id]
			emp_names = ",".join(str(x) for x in emp_name)
			filter_emp.append("Employee : %s"%(emp_names))
		
		if rec.emp_categ_id:
			categ_id = [x.id for x in rec.emp_categ_id]
			emp_categ_ids = ",".join(str(x) for x in categ_id)
			category.append("leaves.emp_categ_id in (%s)"%(emp_categ_ids))
			
			categ_name = [x.name for x in rec.emp_categ_id]
			categ_names = ",".join(str(x) for x in categ_name)
			filter_categ.append("Category : %s"%(categ_names))
			
		if rec.division_id:
			division_id = [x.id for x in rec.division_id]
			division_ids = ",".join(str(x) for x in division_id)
			division.append("leaves.division_id in (%s)"%(division_ids))
			
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
		
		
		
		sql = """		
			select

			emp.code as employee_code,
			emp.name_related as employee_name,
			department.name as dep_name,
			division.name as div_name,
			leaves.out_time as out_time,
			leaves.in_time as in_time,
			leaves.permission_hrs as per_hrs,
			to_char(leaves.from_date,'dd/mm/yyyy') AS from_date,
			to_char(leaves.to_date,'dd/mm/yyyy') AS to_date,
			leaves.number_of_days_temp as no_days


			from hr_holidays leaves

			left join hr_employee emp on (emp.id=leaves.employee_id)
			left join kg_division_master division on (division.id=leaves.division_id)
			left join kg_employee_category category on (category.id=leaves.emp_categ_id)
			left join kg_depmaster department on (department.id=emp.dep_id)

			where leaves.from_date >="""+date_from+""" and leaves.to_date <="""+date_to+' '+""" """+ employee +""" """+ category+ """ """+ division+ """ and leaves.status='approved'
			and leaves.holiday_status_id = 25 """

			
		cr.execute(sql)		
		data = cr.dictfetchall()
		
		record={}
		sno=1
		wbk = xlwt.Workbook()
		style1 = xlwt.easyxf('font: bold off,height 240,color_index 0x95;' 'align: horiz left,vertical center;''borders: left thin, right thin, top thin,bottom thin') 
		style2 = xlwt.easyxf('font: bold on,height 240,color_index 0x95;' 'align: horiz center;''borders: left thin, right thin, top thin ,bottom thin') 
		s1=0
		
		"""adding a worksheet along with name"""
		
		sheet1 = wbk.add_sheet('ON_DUTY_REPORT')
		s2=6
		sheet1.col(0).width = 3000
		sheet1.col(1).width = 3000
		sheet1.col(2).width = 7000
		sheet1.col(3).width = 4500
		sheet1.col(4).width = 4000
		sheet1.col(5).width = 2000
		sheet1.col(6).width = 2000
		sheet1.col(7).width = 2000
		sheet1.col(8).width = 2000
		sheet1.col(9).width = 2000
		sheet1.col(10).width = 2000
		
		
		
		""" writing field headings """
		#~ date_from=datetime.date_from.strptime('%d-%m-%Y')
		

		date_from = datetime.strptime(rec.date_from, '%Y-%m-%d').strftime('%d/%m/%Y')
		date_to = datetime.strptime(rec.date_to, '%Y-%m-%d').strftime('%d/%m/%Y')
		
		
		sheet1.write_merge(0, 3, 0, 10,"SAM TURBO INDUSTRY PRIVATE LIMITED \n Avinashi Road, Neelambur,\n Coimbatore - 641062 \n Tel:3053555, 3053556,Fax : 0422-3053535",style2)
		sheet1.row(0).height = 450
		sheet1.write_merge(4, 4, 0, 10,"ON DUTY REPORT FOR THE PERIOD "+ date_from + " "+ "TO "+date_to,style1)
		sheet1.write_merge(5, 5, 0, 10,"",style2)
		#~ sheet1.write_merge(3, 3, 0, 5,"",style2)
		
		sheet1.insert_bitmap('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_reports/img/sam.bmp',0,0)
		sheet1.write(s2,0,"S.NO",style1)
		#~ sheet1.row(s1).height = 490
		sheet1.write(s2,1,"EMP.ID",style1)
		sheet1.write(s2,2,"NAME",style1)
		sheet1.write(s2,3,"DEPARTMENT",style1)
		sheet1.write(s2,4,"DIVISION",style1)
		sheet1.write(s2,5,"OUT",style1)
		sheet1.write(s2,6,"IN",style1)
		sheet1.write(s2,7,"HRS",style1)
		sheet1.write(s2,8,"FROM",style1)
		sheet1.write(s2,9,"TO",style1)
		sheet1.write(s2,10,"DAYS",style1)
		
		

		for ele in data:
			s2+=1
			
			in_time = str(ele['in_time']) .replace('.', ':')
			out_time = str(ele['out_time']) .replace('.', ':')
			per_hrs = str(ele['per_hrs']) .replace('.', ':')
			
			print "in_timein_time",in_time
			print "in_timein_time",out_time
			
			sheet1.write(s2,0,sno,style1)
			sheet1.write(s2,1,ele['employee_code'],style1)
			sheet1.write(s2,2,ele['employee_name'],style1)
			sheet1.write(s2,3,ele['dep_name'],style1)
			sheet1.write(s2,4,ele['div_name'],style1)
			sheet1.write(s2,5,out_time,style1)
			sheet1.write(s2,6,in_time,style1)
			sheet1.write(s2,7,per_hrs,style1)
			sheet1.write(s2,8,ele['from_date'],style1)
			sheet1.write(s2,9,ele['to_date'],style1)
			sheet1.write(s2,10,ele['no_days'],style1)
			
			
																	
			
			sno = sno + 1
			
		"""Parsing data as string """
		file_data=StringIO.StringIO()
		o=wbk.save(file_data)		
		"""string encode of data in wksheet"""		
		out=base64.encodestring(file_data.getvalue())
		"""returning the output xls as binary"""
		report_name = 'ON_DUTY_REPORT' + '.' + 'xls'
		
		return self.write(cr, uid, ids, {'rep_data':out, 'name':report_name,},context=context)
		
kg_excel_on_duty_report()
