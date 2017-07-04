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

class kg_excel_pf_report(osv.osv):

	_name = 'kg.excel.pf.report'
	_order = 'creation_date desc'
	
	_columns = {
		
		'creation_date': fields.date('Creation Date', readonly=True),
		'emp_categ_id':fields.many2many('kg.employee.category','kg_ex_ctc_rep_wiz','report_id','categ_id','Category'),
		'division_id':fields.many2many('kg.division.master','kg_ex_div_rep_wiz','report_id','div_id','Division'),
		'employee_id':fields.many2many('hr.employee','kg_ex_emp_rep_wiz','report_id','emp_id','Employee'),
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
		product=[]
		supplier = []
		
		
		
		sql = """		
			select 

			contract.uan_no as uan_no,
			emp.name_related as employee_name,
			payslip.cross_amt as gross_amt,
			(select sum(amount) from hr_payslip_line where code in('BASIC','VDA','FDA')) as epf_wages,
			(select sum(amount) from hr_payslip_line where code in('BASIC','VDA','FDA')) as eps_wages,
			(select sum(amount) from hr_payslip_line where code in('BASIC','VDA','FDA')) as edli_wages,
			(select trim(TO_CHAR(((sum(amount)*12.00)/100)::float, '99999999G999G99G99990D99')) from hr_payslip_line where code in('BASIC','VDA','FDA')) as epf_contri,
			(select trim(TO_CHAR(((sum(amount)*8.33)/100)::float, '99999999G999G99G99990D99')) from hr_payslip_line where code in('BASIC','VDA','FDA')) as eps_contri,
			(select trim(TO_CHAR((((sum(amount)*12.00)/100)-((sum(amount)*8.33)/100))::float, '99999999G999G99G99990D99')) from hr_payslip_line where code in('BASIC','VDA','FDA')) as epf_eps_diff


			from hr_payslip payslip

			left join hr_employee emp on (emp.id = payslip.employee_id)
			left join hr_contract contract on (contract.employee_id = payslip.employee_id)
			left join hr_payslip_line payslip_line on (payslip_line.slip_id = payslip.id)

			where month="""+month_yr+""" 

			group by 1,2,3"""
		cr.execute(sql)		
		data = cr.dictfetchall()
		
		#~ data.sort(key=lambda data: data['date'])		
		record={}
		sno=1
		wbk = xlwt.Workbook()
		style1 = xlwt.easyxf('font: bold off,height 240,color_index 0x95;' 'align: horiz left;''borders: left thin, right thin, top thin') 
		s1=0
		
		"""adding a worksheet along with name"""
		
		sheet1 = wbk.add_sheet('PF_REPORT')
		s2=1
		sheet1.col(0).width = 4000
		sheet1.col(1).width = 6000
		sheet1.col(2).width = 5000
		sheet1.col(3).width = 8000
		sheet1.col(4).width = 5000
		sheet1.col(5).width = 5000
		sheet1.col(6).width = 8500
		sheet1.col(7).width = 9000
		sheet1.col(8).width = 8000
		sheet1.col(9).width = 4000
		sheet1.col(10).width = 8000
		
		
		""" writing field headings """
		
		sheet1.write(s1,0,"UAN",style1)
		sheet1.row(s1).height = 490
		sheet1.write(s1,1,"MEMBER_NAME",style1)
		sheet1.write(s1,2,"GROSS_WAGES",style1)
		sheet1.write(s1,3,"EPF_WAGES CEIL:15000/-",style1)
		sheet1.write(s1,4,"EPS_WAGES",style1)
		sheet1.write(s1,5,"EDLI_WAGES",style1)
		sheet1.write(s1,6,"EPF_CONTRI_REMITTED 12%",style1)
		sheet1.write(s1,7,"ESF_CONTRI_REMITTED 8.33%",style1)
		sheet1.write(s1,8,"EPF_ESF_DIFF_REMITTED",style1)
		sheet1.write(s1,9,"NCP_DAYS",style1)
		sheet1.write(s1,10,"REFUND_OF_ADVANCES",style1)
		

		for ele in data:
			
			sheet1.write(s2,0,ele['uan_no'])
			sheet1.write(s2,1,ele['employee_name'])
			sheet1.write(s2,2,ele['gross_amt'])
			sheet1.write(s2,3,ele['epf_wages'])
			sheet1.write(s2,4,ele['eps_wages'])
			sheet1.write(s2,5,ele['edli_wages'])
			sheet1.write(s2,6,float(ele['epf_contri']))
			sheet1.write(s2,7,float(ele['eps_contri']))
			sheet1.write(s2,8,float(ele['epf_eps_diff']))
			sheet1.write(s2,9,float(0))
			sheet1.write(s2,10,float(0))
			
																	
			s2+=1
			sno = sno + 1
			
		"""Parsing data as string """
		file_data=StringIO.StringIO()
		o=wbk.save(file_data)		
		"""string encode of data in wksheet"""		
		out=base64.encodestring(file_data.getvalue())
		"""returning the output xls as binary"""
		report_name = 'PF_REPORT' + '.' + 'xls'
		
		return self.write(cr, uid, ids, {'rep_data':out, 'name':report_name,'state': 'done'},context=context)
		
kg_excel_pf_report()
