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

class kg_excel_gratuity_report(osv.osv):

	_name = 'kg.excel.gratuity.report'
	_order = 'creation_date desc'
	
	_columns = {
		
		'creation_date': fields.date('Creation Date', readonly=True),
		'emp_categ_id':fields.many2many('kg.employee.category','kg_ex_adv_cat_rep_wiz','report_id','categ_id','Category'),
		'division_id':fields.many2many('kg.division.master','kg_ex_adv_div_rep_wiz','report_id','div_id','Division'),
		'employee_id':fields.many2many('hr.employee','kg_ex_adv_emp_rep_wiz','report_id','emp_id','Employee'),
		'ded_type': fields.selection([('advance', 'Advance'),('loan', 'Loan'),('insurance', 'Insurance'),
						('tax', 'Tax'),('others','Others'),('cloth','Cloth')], 
						'Deduction Type'),
		'department_id':fields.many2many('kg.depmaster','kg_ex_adv_dep_rep_wiz','report_id','dep_id','Department'),
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
			category.append("payslip.emp_categ_id in (%s)"%(emp_categ_ids))
			
			categ_name = [x.name for x in rec.emp_categ_id]
			categ_names = ",".join(str(x) for x in categ_name)
			filter_categ.append("Category : %s"%(categ_names))
			
		if rec.division_id:
			division_id = [x.id for x in rec.division_id]
			division_ids = ",".join(str(x) for x in division_id)
			division.append("payslip.division_id in (%s)"%(division_ids))
			
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
			
		if rec.ded_type:
			ded_type =  'and '+'advance.ded_type = '+"'"+rec.ded_type+"'"
			division =  ded_type+' '
		else:
			ded_type = ''
			
		
		date_from = "'"+rec.date_from+"'"
		date_to = 	"'"+rec.date_to+"'"
		
		
		
		sql = """		

				select 

				distinct(employee.name_related) as employee_name,
				to_char(employee.join_date,'dd/mm/yyyy') as date_of_joining,
				pay.id as pay_id,
				to_char (((case when (select amount from hr_payslip_line where code='BASIC' and slip_id = pay.id) is null then 0.00 
				else (select amount from hr_payslip_line where code='BASIC' and slip_id = pay.id) end)+(case when (select amount from hr_payslip_line where code='FDA' and slip_id = pay.id) is null then 0.00 
				else (select amount from hr_payslip_line where code='FDA' and slip_id = pay.id) end)+(case when (select amount from hr_payslip_line where code='VDA' and slip_id = pay.id) is null then 0.00 
				else (select amount from hr_payslip_line where code='VDA' and slip_id = pay.id) end)),'9G99G990D99') as gratuity_amount



				from hr_payslip payslip

				left join hr_employee employee on (employee.id=payslip.employee_id)
				left join hr_payslip pay on (pay.id=(select max(id) from hr_payslip where date_from >="""+date_from+""" and date_to <= """+date_to+' '+""" and employee_id=employee.id))

				where payslip.date_from >="""+date_from+""" and payslip.date_to <="""+date_to+' '+""" """+ category+ """ """+ division + """  and employee.status in ('resigned','relieve')  """ """ """


				

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
		
		sheet1 = wbk.add_sheet('GRATUITY_PRINT')
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
		#~ date_from=datetime.date_from.strptime('%d-%m-%Y')
		

		date_from = datetime.strptime(rec.date_from, '%Y-%m-%d').strftime('%d/%m/%Y')
		date_to = datetime.strptime(rec.date_to, '%Y-%m-%d').strftime('%d/%m/%Y')
		
		
		sheet1.write_merge(0, 3, 0, 5,"SAM TURBO INDUSTRY PRIVATE LIMITED \n Avinashi Road, Neelambur,\n Coimbatore - 641062 \n Tel:3053555, 3053556,Fax : 0422-3053535",style2)
		sheet1.row(0).height = 450
		sheet1.write_merge(4, 4, 0, 5,"GRATUITY DETAILS - "+ date_from + " "+ "TO "+date_to,style2)
		sheet1.write_merge(5, 5, 0, 5,"",style2)
		#~ sheet1.write_merge(3, 3, 0, 5,"",style2)
		
		sheet1.insert_bitmap('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_reports/img/sam.bmp',0,0)
		sheet1.write(s2,0,"S.NO",style1)
		#~ sheet1.row(s1).height = 490
		sheet1.write(s2,1,"LIC ID",style1)
		sheet1.write(s2,2,"NAME",style1)
		sheet1.write(s2,3,"DATE OF JOINING",style1)
		sheet1.write(s2,4,"SALARY",style1)
		sheet1.write(s2,5,"REMARKS",style1)
		
		for ele in data:
			print "ele['employee_name']ele['employee_name']ele['employee_name']ele['employee_name']",ele['employee_name']
			
			s2+=1
			
			sheet1.write(s2,0,sno,style3)
			sheet1.write(s2,1,'',style3)
			sheet1.write(s2,2,ele['employee_name'],style3)
			sheet1.write(s2,3,ele['date_of_joining'],style3)
			sheet1.write(s2,4,ele['gratuity_amount'],style3)
			sheet1.write(s2,5,'',style3)
			
			
			
			sno = sno + 1
			
		"""Parsing data as string """
		file_data=StringIO.StringIO()
		o=wbk.save(file_data)		
		"""string encode of data in wksheet"""		
		out=base64.encodestring(file_data.getvalue())
		"""returning the output xls as binary"""
		report_name = 'GRATUITY_PRINT' + '.' + 'xls'
		
		return self.write(cr, uid, ids, {'rep_data':out,'state':'done','name':report_name,},context=context)
		
kg_excel_gratuity_report()
