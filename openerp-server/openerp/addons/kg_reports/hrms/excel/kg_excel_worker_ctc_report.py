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

class kg_excel_worker_ctc_report(osv.osv):

	_name = 'kg.excel.worker.ctc.report'
	_order = 'creation_date desc'
	
	_columns = {
		
		'creation_date': fields.date('Creation Date', readonly=True),
		'emp_categ_id':fields.many2many('kg.employee.category','kg_ex_wor_ctc_cat_rep_wiz','report_id','categ_id','Category'),
		'division_id':fields.many2many('kg.division.master','kg_ex_wor_ctc_div_rep_wiz','report_id','div_id','Division'),
		'employee_id':fields.many2many('hr.employee','kg_ex_wor_ctc_emp_rep_wiz','report_id','emp_id','Employee'),
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
		employee = []
		filter_emp = []
		filter_categ = []
		filter_div = []
		
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
		
		date_from = "'"+rec.date_from+"'"
		date_to = 	"'"+rec.date_to+"'"
		
		
		
		sql = """		

				select 


				emp.name_related as employee_name,
				to_char(emp.join_date,'dd/mm/yyyy') AS date_of_join,
				job_nature.name AS job_nature,
				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='BASIC') is null
				then 0.00 else (select amount from hr_payslip_line where slip_id = payslip.id and code='BASIC')end as basic_amt,
				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='VDA') is null
				then 0.00 else (select amount from hr_payslip_line where slip_id = payslip.id and code='VDA') end as vda_amt,
				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='FDA') is null
				then 0.00 else (select amount from hr_payslip_line where slip_id = payslip.id and code='FDA') end as fda_amt,
				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='HRA')is null
				then 0.00 else (select amount from hr_payslip_line where slip_id = payslip.id and code='HRA') end as hra_amt,
				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='CONV') is null
				then 0.00 else (select amount from hr_payslip_line where slip_id = payslip.id and code='CONV') end as conv_amt,
				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='ATTN.ALLOW') is null 
				then 0.00 else (select amount from hr_payslip_line where slip_id = payslip.id and code='ATTN.ALLOW') end as att_allow_amt,
				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='CA') is null
				then 0.00 else (select amount from hr_payslip_line where slip_id = payslip.id and code='CA') end as ca_amt,

				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='INC') is null
				then (case when (select amount from ch_other_salary_comp where slip_id = payslip.id and code='INC')is null then
				0.00 else (select amount from ch_other_salary_comp where slip_id = payslip.id and code='INC') end) else 00 
				end as inc_amt,

				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='Attendance Bonus') is null
				then (case when (select amount from ch_other_salary_comp where slip_id = payslip.id and code='Attendance Bonus') is null then
				0.00 else (select amount from ch_other_salary_comp where slip_id = payslip.id and code='Attendance Bonus') end) else 00 
				end as att_bon_amt,

				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='PF') is null
				then 0.00 else (select amount from hr_payslip_line where slip_id = payslip.id and code='PF') end as pf_amt,

				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='SHOE') is null
				then (case when (select amount from ch_other_salary_comp where slip_id = payslip.id and code='SHOE') is null then
				0.00 else (select amount from ch_other_salary_comp where slip_id = payslip.id and code='SHOE') end) else 00 
				end as shoe_amt,

				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='UNI') is null
				then (case when (select amount from ch_other_salary_comp where slip_id = payslip.id and code='UNI') is null then
				0.00 else (select amount from ch_other_salary_comp where slip_id = payslip.id and code='UNI') end) else 00 
				end as uni_amt,

				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='COFFEE ALLOW') is null
				then (case when (select amount from ch_other_salary_comp where slip_id = payslip.id and code='COFFEE ALLOW') is null then
				0.00 else (select amount from ch_other_salary_comp where slip_id = payslip.id and code='COFFEE ALLOW') end) else 00 
				end as coff_allow_amt,

				case when (select amount from hr_payslip_line where slip_id = payslip.id and category_id=8) is null
				then (case when (select amount from ch_other_salary_comp where slip_id = payslip.id and category_id=8) is null then
				0.00 else (select amount from ch_other_salary_comp where slip_id = payslip.id and category_id=8) end) else 00 
				end as bonus_amt,


				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='NA') is null
				then (case when (select amount from ch_other_salary_comp where slip_id = payslip.id and code='NA') is null then
				0.00 else (select amount from ch_other_salary_comp where slip_id = payslip.id and code='NA') end) else 00 
				end as na_amt




				from hr_payslip payslip

				left join hr_employee emp on (emp.id=payslip.employee_id)
				left join kg_job_nature job_nature on (job_nature.id=emp.nature_of_job_id)

				where payslip.month="""+month_yr+' '+""" """+ employee +""" """+ category+ """ """+ division+ """"""

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
		
		sheet1 = wbk.add_sheet('WORKER_CTC_PRINT')
		s2=6
		sheet1.col(0).width = 2000
		sheet1.col(1).width = 5000
		sheet1.col(2).width = 4000
		sheet1.col(3).width = 4000
		sheet1.col(4).width = 2000
		sheet1.col(5).width = 2000
		sheet1.col(6).width = 2000
		sheet1.col(7).width = 2000
		sheet1.col(8).width = 2000
		sheet1.col(9).width = 2000
		sheet1.col(10).width = 2000
		sheet1.col(11).width = 2000
		sheet1.col(12).width = 2000
		sheet1.col(13).width = 2000
		sheet1.col(14).width = 4000
		sheet1.col(15).width = 2000
		sheet1.col(16).width = 2000
		sheet1.col(17).width = 2000
		sheet1.col(18).width = 2000
		sheet1.col(19).width = 2000
		sheet1.col(20).width = 2000
		sheet1.col(21).width = 2000
		sheet1.col(22).width = 2000
		sheet1.col(23).width = 4000
		sheet1.col(24).width = 4000
		
		
		
		""" writing field headings """
		#~ date_from=datetime.date_from.strptime('%d-%m-%Y')
		

		date_from = datetime.strptime(rec.date_from, '%Y-%m-%d').strftime('%d/%m/%Y')
		date_to = datetime.strptime(rec.date_to, '%Y-%m-%d').strftime('%d/%m/%Y')
		
		
		sheet1.write_merge(0, 3, 0, 24,"SAM TURBO INDUSTRY PRIVATE LIMITED \n Avinashi Road, Neelambur,\n Coimbatore - 641062 \n Tel:3053555, 3053556,Fax : 0422-3053535",style2)
		sheet1.row(0).height = 450
		sheet1.write_merge(4, 4, 0, 24,"CTC DETAILS - "+ rec.month+'-'+rec.year,style2)
		sheet1.write_merge(5, 5, 0, 24,"",style2)
		#~ sheet1.write_merge(3, 3, 0, 5,"",style2)
		
		sheet1.insert_bitmap('/home/sujith/SVN_Projects/sam_turbo_dev/openerp-server/openerp/addons/kg_crm_offer/img/sam.bmp',0,0)
		sheet1.write(s2,0,"S.NO",style1)
		#~ sheet1.row(s1).height = 490
		sheet1.write(s2,1,"NAME",style1)
		sheet1.write(s2,2,"DATE OF JOINING",style1)
		sheet1.write(s2,3,"NATURE OF WORK",style1)
		sheet1.write(s2,4,"BASIC",style1)
		sheet1.write(s2,5,"VDA",style1)
		sheet1.write(s2,6,"FDA",style1)
		sheet1.write(s2,7,"HRA",style1)
		sheet1.write(s2,8,"CONV.",style1)
		sheet1.write(s2,9,"ATT.ALLOW",style1)
		sheet1.write(s2,10,"CA",style1)
		sheet1.write(s2,11,"SALARY",style1)
		sheet1.write(s2,12,"INCENTIVE",style1)
		sheet1.write(s2,13,"ATTN.BONUS",style1)
		sheet1.write(s2,14,"GRAND TOTAL",style1)
		sheet1.write(s2,15,"PF",style1)
		sheet1.write(s2,16,"SHOE",style1)
		sheet1.write(s2,17,"UNI",style1)
		sheet1.write(s2,18,"TEA",style1)
		sheet1.write(s2,19,"GRATUITY",style1)
		sheet1.write(s2,20,"BONUS",style1)
		sheet1.write(s2,21,"EL",style1)
		sheet1.write(s2,22,"NA",style1)
		sheet1.write(s2,23,"CTC Per Month",style1)
		sheet1.write(s2,24,"CTC Per Day",style1)
		
		
		salary=0.00
		grand_total=0.00
		ctc_per_mon=0.00
		gratuity=0.00
		el=0.00
		for ele in data:
			s2+=1
			salary = ele['basic_amt']+ele['vda_amt']+ele['fda_amt']+ele['hra_amt']+ele['conv_amt']+ele['att_allow_amt']+ele['ca_amt']
			grand_total = salary + ele['inc_amt'] + ele['att_bon_amt']
			gratuity = round((((ele['basic_amt']+ele['vda_amt']+ele['fda_amt'])/26)*(15/12)),2)
			el = round((((ele['basic_amt']+ele['vda_amt']+ele['fda_amt'])/26)*(15/12)),2)
			ctc_per_mon = grand_total + ele['pf_amt'] + ele['shoe_amt']+ ele['uni_amt']+ ele['coff_allow_amt']+ gratuity+el
			sheet1.write(s2,0,sno,style3)
			sheet1.write(s2,1,ele['employee_name'],style3)
			sheet1.write(s2,2,ele['date_of_join'],style3)
			sheet1.write(s2,3,ele['job_nature'],style3)
			sheet1.write(s2,4,ele['basic_amt'],style3)
			sheet1.write(s2,5,ele['vda_amt'],style3)
			sheet1.write(s2,6,ele['fda_amt'],style3)
			sheet1.write(s2,7,ele['hra_amt'],style3)
			sheet1.write(s2,8,ele['conv_amt'],style3)
			sheet1.write(s2,9,ele['att_allow_amt'],style3)
			sheet1.write(s2,10,ele['ca_amt'],style3)
			sheet1.write(s2,11,salary,style2)
			sheet1.write(s2,12,ele['inc_amt'],style3)
			sheet1.write(s2,13,ele['att_bon_amt'],style3)
			sheet1.write(s2,14,grand_total,style2)
			sheet1.write(s2,15,ele['pf_amt'],style3)
			sheet1.write(s2,16,ele['shoe_amt'],style3)
			sheet1.write(s2,17,ele['uni_amt'],style3)
			sheet1.write(s2,18,ele['coff_allow_amt'],style3)
			sheet1.write(s2,19,gratuity,style3)
			sheet1.write(s2,20,ele['bonus_amt'],style3)
			sheet1.write(s2,21,el,style3)
			sheet1.write(s2,22,ele['na_amt'],style3)
			sheet1.write(s2,23,(ctc_per_mon),style2)
			sheet1.write(s2,24,round((ctc_per_mon/26),2),style2)
			
			
																	
			
			sno = sno + 1
			
		"""Parsing data as string """
		file_data=StringIO.StringIO()
		o=wbk.save(file_data)		
		"""string encode of data in wksheet"""		
		out=base64.encodestring(file_data.getvalue())
		"""returning the output xls as binary"""
		report_name = 'WORKER_CTC_PRINT' + '.' + 'xls'
		
		return self.write(cr, uid, ids, {'rep_data':out,'state':'done','name':report_name,},context=context)
		
kg_excel_worker_ctc_report()
