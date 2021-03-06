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

class kg_excel_bank_copy_report(osv.osv):

	_name = 'kg.excel.bank.copy.report'
	_order = 'creation_date desc'
	
	_columns = {
		
		'creation_date': fields.date('Creation Date', readonly=True),
		'emp_categ_id':fields.many2many('kg.employee.category','kg_ex_bank_cat_rep_wiz','report_id','categ_id','Category'),
		'division_id':fields.many2many('kg.division.master','kg_ex_bank_div_rep_wiz','report_id','div_id','Division'),
		'employee_id':fields.many2many('hr.employee','kg_ex_bank_emp_rep_wiz','report_id','emp_id','Employee'),
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
		
		
		
		if rec.month and rec.year:
			year = "'"+rec.month+'-'+rec.year+"'"
		
		date_from = "'"+rec.date_from+"'"
		date_to = 	"'"+rec.date_to+"'"
		
		sql = """		
		
			select

			employee.name_related as employee_name,
			contract.sal_acc_no as acc_no,
			payslip.month as month,
			payslip.round_val as net_salary,
			division.name as div_name,
			ROW_NUMBER() OVER(PARTITION BY division.name) as row,
			case when ROW_NUMBER() OVER(PARTITION BY division.name) = 1 then division.name else '' end as division_name

			from

			hr_payslip payslip

			left join hr_employee employee on (employee.id = payslip.employee_id)
			left join hr_contract contract on (contract.employee_id = employee.id)
			left join kg_division_master division on (division.id = contract.division_id)

			where payslip.month = """+year+' '+""" """+division+"""  group by 1,2,3,4,5 """

		cr.execute(sql)		
		data = cr.dictfetchall()
		
		record={}
		sno=1
		wbk = xlwt.Workbook()
		style1 = xlwt.easyxf('font: bold off,height 240,color_index 0x95;' 'align: horiz left,vertical center;''borders: left thin, right thin, top thin,bottom thin') 
		style2 = xlwt.easyxf('font: bold on,height 240,color_index 0x95;' 'align: horiz center;''borders: left thin, right thin, top thin ,bottom thin') 
		style3 = xlwt.easyxf('font: bold off,height 240,color_index 0x95;' 'align: horiz center,vertical center;''borders: left thin, right thin, top thin,bottom thin') 
		s1=0
		
		"""adding a worksheet along with name"""
		
		sheet1 = wbk.add_sheet('BANK_COPY_REPORT')
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
		
		sheet1.write_merge(0, 3, 0, 4,"SAM TURBO INDUSTRY PRIVATE LIMITED \n Avinashi Road, Neelambur,\n Coimbatore - 641062 \n Tel:3053555, 3053556,Fax : 0422-3053535",style2)
		sheet1.row(0).height = 450
		sheet1.write_merge(4, 4, 0,4,"STAFF SALARY FOR THE MONTH "+rec.month+'-'+rec.year,style3)
		sheet1.write_merge(5, 5, 0,4,"",style2)
		sheet1.insert_bitmap('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_reports/img/sam.bmp',0,0)
		sheet1.write(s2,0,"S.NO",style1)
		sheet1.write(s2,1,"DIVISION",style1)
		sheet1.write(s2,2,"ACCOUNT NO",style1)
		sheet1.write(s2,3,"NAME",style1)
		sheet1.write(s2,4,"TOTAL",style1)
		
		for ele in data:
			s2+=1
			sheet1.write(s2,0,sno,style1)
			sheet1.write(s2,1,ele['division_name'],style1)
			sheet1.write(s2,2,ele['acc_no'],style1)
			sheet1.write(s2,3,ele['employee_name'],style1)
			sheet1.write(s2,4,ele['net_salary'],style1)
			
			sno = sno + 1
			
		"""Parsing data as string """
		file_data=StringIO.StringIO()
		o=wbk.save(file_data)		
		"""string encode of data in wksheet"""		
		out=base64.encodestring(file_data.getvalue())
		"""returning the output xls as binary"""
		report_name = 'BANK_COPY_REPORT' + '.' + 'xls'

		
		return self.write(cr, uid, ids, {'rep_data':out,'state':'done','name':report_name,},context=context)
		
kg_excel_bank_copy_report()
