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

class kg_excel_advance_report(osv.osv):

	_name = 'kg.excel.advance.report'
	_order = 'creation_date desc'
	
	_columns = {
		
		'creation_date': fields.date('Creation Date', readonly=True),
		'emp_categ_id':fields.many2many('kg.employee.category','kg_ex_adv_cat_rep_wiz','report_id','categ_id','Category'),
		'division_id':fields.many2many('kg.division.master','kg_ex_adv_div_rep_wiz','report_id','div_id','Division'),
		'employee_id':fields.many2many('hr.employee','kg_ex_adv_emp_rep_wiz','report_id','emp_id','Employee'),
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
			
			
		#~ if rec.department_id:
			#~ department_id = [x.id for x in rec.department_id]
			#~ department_ids = ",".join(str(x) for x in department_id)
			#~ department.append("payslip.division_id in (%s)"%(department_id))
			#~ 
			#~ div_name = [x.name for x in rec.division_id]
			#~ div_names = ",".join(str(x) for x in div_name)
			#~ filter_div.append("Division : %s"%(div_names))
		
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
			
		#~ if division:
			#~ division = 'and '+' or '.join(division)
			#~ division =  division+' '
			#~ 
			#~ filter_dep = filter_dep
		#~ else:
			#~ division = ''
			#~ filter_dep = ''
		
		date_from = "'"+rec.date_from+"'"
		date_to = 	"'"+rec.date_to+"'"
		
		
		
		sql = """		

				select

				emp.code as employee_code,
				emp.name_related as employee_name,
				division.name as div_name,
				department.name as dep_name,
				advance.ded_type as type,
				advance.tot_amt as total_amt,
				payslip.date_from as due_month,
				(select amount from hr_payslip_line where code='ADV' and slip_id=payslip.id) as due_amt

				from hr_payslip payslip

				left join hr_employee emp on (emp.id=payslip.employee_id)
				left join kg_division_master division on (division.id=payslip.division_id)
				left join kg_employee_category category on (category.id=payslip.emp_categ_id)
				left join kg_depmaster department on (department.id=emp.dep_id)
				left join kg_advance_deduction advance on (advance.id=(select COALESCE(cum_ded_id,0) from hr_payslip_line where slip_id=payslip.id and employee_id=payslip.employee_id and cum_ded_id!=0))

				where payslip.date_from >="""+date_from+""" and payslip.date_to <="""+date_to+' '+""" """+ employee +""" """+ category+ """ """+ division + """"""

				

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
		
		sheet1 = wbk.add_sheet('ADVANCE_PRINT')
		s2=6
		sheet1.col(0).width = 2000
		sheet1.col(1).width = 3000
		sheet1.col(2).width = 5000
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
		
		
		sheet1.write_merge(0, 3, 0, 8,"SAM TURBO INDUSTRY PRIVATE LIMITED \n Avinashi Road, Neelambur,\n Coimbatore - 641062 \n Tel:3053555, 3053556,Fax : 0422-3053535",style2)
		sheet1.row(0).height = 450
		sheet1.write_merge(4, 4, 0, 8,"ADVANCE DETAILS - "+ date_from + " "+ "TO "+date_to,style2)
		sheet1.write_merge(5, 5, 0, 8,"",style2)
		#~ sheet1.write_merge(3, 3, 0, 5,"",style2)
		
		sheet1.insert_bitmap('/home/sujith/SVN_Projects/sam_turbo_dev/openerp-server/openerp/addons/kg_crm_offer/img/sam.bmp',0,0)
		sheet1.write(s2,0,"S.NO",style1)
		#~ sheet1.row(s1).height = 490
		sheet1.write(s2,1,"CODE",style1)
		sheet1.write(s2,2,"NAME",style1)
		sheet1.write(s2,3,"DIVISION",style1)
		sheet1.write(s2,4,"DEPARTMENT",style1)
		sheet1.write(s2,5,"DETECTION TYPE",style1)
		sheet1.write(s2,6,"ADVANCE AMOUNT",style1)
		sheet1.write(s2,7,"DUE MONTH",style1)
		sheet1.write(s2,8,"DUE AMOUNT",style1)
		
		
		for ele in data:
			if ele['type'] != None:
				s2+=1
				
				sheet1.write(s2,0,sno,style3)
				sheet1.write(s2,1,ele['employee_code'],style3)
				sheet1.write(s2,2,ele['employee_name'],style3)
				sheet1.write(s2,3,ele['div_name'],style3)
				sheet1.write(s2,4,ele['dep_name'],style3)
				sheet1.write(s2,5,ele['type'],style3)
				sheet1.write(s2,6,ele['total_amt'],style3)
				sheet1.write(s2,7,ele['due_month'],style3)
				sheet1.write(s2,8,ele['due_amt'],style3)
				
				
				sno = sno + 1
			else:
				pass
			
		"""Parsing data as string """
		file_data=StringIO.StringIO()
		o=wbk.save(file_data)		
		"""string encode of data in wksheet"""		
		out=base64.encodestring(file_data.getvalue())
		"""returning the output xls as binary"""
		report_name = 'ADVANCE_PRINT' + '.' + 'xls'
		
		return self.write(cr, uid, ids, {'rep_data':out,'state':'done','name':report_name,},context=context)
		
kg_excel_advance_report()
