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

class kg_excel_staff_ctc_report(osv.osv):

	_name = 'kg.excel.staff.ctc.report'
	_order = 'creation_date desc'
	
	_columns = {
		
		'creation_date': fields.date('Creation Date', readonly=True),
		'emp_categ_id':fields.many2many('kg.employee.category','kg_ex_staff_ctc_cat_rep_wiz','report_id','categ_id','Category'),
		'division_id':fields.many2many('kg.division.master','kg_ex_staff_ctc_div_rep_wiz','report_id','div_id','Division'),
		'employee_id':fields.many2many('hr.employee','kg_ex_staff_ctc_emp_rep_wiz','report_id','emp_id','Employee'),
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
				edu_line.ug_degree as qualification,
				job.name AS designation,
				to_char(emp.join_date,'dd/mm/yyyy') AS date_of_join,
				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='BASIC') is null
				then 0.00 else (select amount from hr_payslip_line where slip_id = payslip.id and code='BASIC')end as basic_amt,
				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='VDA') is null
				then 0.00 else (select amount from hr_payslip_line where slip_id = payslip.id and code='VDA') end as vda_amt,
				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='FDA') is null
				then 0.00 else (select amount from hr_payslip_line where slip_id = payslip.id and code='FDA') end as fda_amt,
				case when (select amount from ch_kg_allowance_deduction where header_id=allow_ded.id and employee_id=payslip.employee_id ) is null
				then 0.00 else (select amount from ch_kg_allowance_deduction where header_id=allow_ded.id and employee_id=payslip.employee_id ) end as allow,

				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='FI') is null
				then (case when (select amount from ch_other_salary_comp where slip_id = payslip.id and code='FI')is null then
				0.00 else (select amount from ch_other_salary_comp where slip_id = payslip.id and code='FI') end) else 
				(select amount from hr_payslip_line where slip_id = payslip.id and code='FI')end as fi_inc_amt,

				case when (select amount from hr_payslip_line where slip_id = payslip.id and name='Special Incentive') is null
				then (case when (select amount from ch_other_salary_comp where slip_id = payslip.id and name='Special Incentive')is null then
				0.00 else (select amount from ch_other_salary_comp where slip_id = payslip.id and name='Special Incentive') end) else 
				(select amount from hr_payslip_line where slip_id = payslip.id and name='Special Incentive') end as spi_inc_amt,

				case when (select amount from hr_payslip_line where slip_id = payslip.id and name='Special Incentive ( 4.01 to 5.0 ) Crs') is null
				then (case when (select amount from ch_other_salary_comp where slip_id = payslip.id and name='Special Incentive ( 4.01 to 5.0 ) Crs')is null then
				0.00 else (select amount from ch_other_salary_comp where slip_id = payslip.id and name='Special Incentive ( 4.01 to 5.0 ) Crs') end) else 
				(select amount from hr_payslip_line where slip_id = payslip.id and name='Special Incentive ( 4.01 to 5.0 ) Crs')
				end as spi_five_inc_amt,

				case when (select amount from hr_payslip_line where slip_id = payslip.id and name='Special Incentive ( 5.01 to 6.0 ) Crs') is null
				then (case when (select amount from ch_other_salary_comp where slip_id = payslip.id and name='Special Incentive ( 5.01 to 6.0 ) Crs')is null then
				0.00 else (select amount from ch_other_salary_comp where slip_id = payslip.id and name='Special Incentive ( 5.01 to 6.0 ) Crs') end) else
				(select amount from hr_payslip_line where slip_id = payslip.id and name='Special Incentive ( 5.01 to 6.0 ) Crs') end as spi_six_inc_amt,

				case when (select amount from hr_payslip_line where slip_id = payslip.id and name='Special Incentive ( 6.01 to 7.0 ) Crs') is null
				then (case when (select amount from ch_other_salary_comp where slip_id = payslip.id and name='Special Incentive ( 6.01 to 7.0 ) Crs')is null then
				0.00 else (select amount from ch_other_salary_comp where slip_id = payslip.id and name='Special Incentive ( 6.01 to 7.0 ) Crs') end) else
				(select amount from hr_payslip_line where slip_id = payslip.id and name='Special Incentive ( 6.01 to 7.0 ) Crs') end as spi_seven_inc_amt,


				(select max(gross_salary) from ch_kg_contract_pre_salary where header_id_pre_salary=contract.id) as last_inc_amt,
				(select to_char(max(updated_date),'dd/mm/yyyy') from ch_kg_contract_pre_salary where header_id_pre_salary=contract.id) as last_inc_date,
				case when (select amount from hr_payslip_line where slip_id = payslip.id and category_id=8) is null
				then 0.00 else (select amount from hr_payslip_line where slip_id = payslip.id and category_id=8) end as bonus_amt,
				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='PF') is null
				then 0.00 else (select amount from hr_payslip_line where slip_id = payslip.id and code='PF') end as pf_amt,
				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='ESI') is null
				then 0.00 else (select amount from hr_payslip_line where slip_id = payslip.id and code='ESI') end as esi_amt,

				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='SHOE') is null
				then (case when (select amount from ch_other_salary_comp where slip_id = payslip.id and code='SHOE')is null then
				0.00 else (select amount from ch_other_salary_comp where slip_id = payslip.id and code='SHOE') end) else
				(select amount from hr_payslip_line where slip_id = payslip.id and code='SHOE') end as shoe_amt,

				case when (select amount from hr_payslip_line where slip_id = payslip.id and code='COFFEE ALLOW') is null
				then (case when (select amount from ch_other_salary_comp where slip_id = payslip.id and code='COFFEE ALLOW')is null then
				0.00 else (select amount from ch_other_salary_comp where slip_id = payslip.id and code='COFFEE ALLOW') end) else
				(select amount from hr_payslip_line where slip_id = payslip.id and code='COFFEE ALLOW') end as coff_allow_amt,
				(select worked_days from kg_monthly_attendance where start_date = payslip.date_from and end_date=payslip.date_to and employee_id = payslip.employee_id and state='approved') as worked_days



				from hr_payslip payslip

				left join hr_employee emp on (emp.id=payslip.employee_id)
				left join hr_contract contract on (contract.employee_id=payslip.employee_id)
				left join hr_job job on (job.id=emp.job_id)
				left join kg_job_nature job_nature on (job_nature.id=emp.nature_of_job_id)
				left join kg_allowance_deduction allow_ded on (allow_ded.id=(select id from kg_allowance_deduction where start_date=payslip.date_from and end_date=payslip.date_to and state='approved' ))
				left join ch_kg_allowance_deduction allow_ded_line on (allow_ded_line.header_id=allow_ded.id)
				left join ch_kg_employee_ref_edu edu_line on (edu_line.id=(select max(id)from ch_kg_employee_ref_edu where header_id_ref_edu=emp.id))

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
		
		sheet1 = wbk.add_sheet('STAFF_CTC_PRINT')
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
		sheet1.col(25).width = 4000
		sheet1.col(26).width = 4000
		sheet1.col(27).width = 4000
		sheet1.col(28).width = 4000
		sheet1.col(29).width = 4000
		
		
		
		""" writing field headings """
		#~ date_from=datetime.date_from.strptime('%d-%m-%Y')
		

		date_from = datetime.strptime(rec.date_from, '%Y-%m-%d').strftime('%d/%m/%Y')
		date_to = datetime.strptime(rec.date_to, '%Y-%m-%d').strftime('%d/%m/%Y')
		
		
		sheet1.write_merge(0, 3, 0, 29,"SAM TURBO INDUSTRY PRIVATE LIMITED \n Avinashi Road, Neelambur,\n Coimbatore - 641062 \n Tel:3053555, 3053556,Fax : 0422-3053535",style2)
		sheet1.row(0).height = 450
		sheet1.write_merge(4, 4, 0, 29,"CTC DETAILS - "+ rec.month+'-'+rec.year,style2)
		sheet1.write_merge(5, 5, 0, 29,"",style2)
		#~ sheet1.write_merge(3, 3, 0, 5,"",style2)
		
		sheet1.insert_bitmap('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_reports/img/sam.bmp',0,0)
		sheet1.write(s2,0,"S.NO",style1)
		#~ sheet1.row(s1).height = 490
		sheet1.write(s2,1,"NAME",style1)
		sheet1.write(s2,2,"QUAL.",style1)
		sheet1.write(s2,3,"DESG.",style1)
		sheet1.write(s2,4,"DOJ",style1)
		sheet1.write(s2,5,"WD",style1)
		sheet1.write(s2,6,"BASIC",style1)
		sheet1.write(s2,7,"D.A.",style1)
		sheet1.write(s2,8,"F.D.A",style1)
		sheet1.write(s2,9,"ALLW..",style1)
		sheet1.write(s2,10,"SALARY",style1)
		sheet1.write(s2,11,"FIXED INCENTIVE",style1)
		sheet1.write(s2,12,"SPL.INC.",style1)
		sheet1.write(s2,13,"TOTAL",style1)
		sheet1.write(s2,14,"5C",style1)
		sheet1.write(s2,15,"6C",style1)
		sheet1.write(s2,16,"7C",style1)
		sheet1.write(s2,17,"TOTAL WITH SPL INC.",style1)
		sheet1.write(s2,18,"LAST INCR.",style1)
		sheet1.write(s2,19,"INCR.DATE.",style1)
		sheet1.write(s2,20,"EL",style1)
		sheet1.write(s2,21,"BONUS",style1)
		sheet1.write(s2,22,"GRATUITY",style1)
		sheet1.write(s2,23,"PF WAGE",style1)
		sheet1.write(s2,24,"PF",style1)
		sheet1.write(s2,25,"ESI",style1)
		sheet1.write(s2,26,"SHOE",style1)
		sheet1.write(s2,27,"TEA",style1)
		sheet1.write(s2,28,"CTC/MON",style1)
		sheet1.write(s2,29,"CTC/DAY",style1)
		
		
		salary=0.00
		total_spl_inc=0.00
		total=0.00
		ctc_per_mon=0.00
		gratuity=0.00
		el=0.00
		basic_amt = 0.00
		vda_amt = 0.00
		fda_amt = 0.00
		allow_amt = 0.00
		bonus_amt = 0.00
		pf_amt = 0.00
		esi_amt = 0.00
		shoe_amt = 0.00
		coff_allow_amt = 0.00
		for ele in data:
			basic_amt += ele['basic_amt']
			vda_amt += ele['vda_amt']
			fda_amt += ele['fda_amt']
			allow_amt += ele['allow']
			bonus_amt += ele['bonus_amt']
			pf_amt += ele['pf_amt']
			esi_amt += ele['esi_amt']
			shoe_amt += ele['shoe_amt']
			coff_allow_amt += ele['coff_allow_amt']
			s2+=1
			salary = ele['basic_amt']+ele['vda_amt']+ele['fda_amt']+ele['allow']
			
			total = salary + ele['fi_inc_amt'] + ele['spi_inc_amt']
			total_spl_inc = total + ele['spi_five_inc_amt'] + ele['spi_six_inc_amt']+ ele['spi_seven_inc_amt']
			gratuity = round((((ele['basic_amt']+ele['vda_amt']+ele['fda_amt'])/26)*(15/12)),2)
			el = round(((salary/30)*15/12),0)
			ctc_per_mon = total_spl_inc + el + ele['bonus_amt']+gratuity+ ele['pf_amt']+ele['esi_amt'] + ele['shoe_amt']+ ele['coff_allow_amt']
			sheet1.write(s2,0,sno,style3)
			sheet1.write(s2,1,ele['employee_name'],style3)
			sheet1.write(s2,2,ele['qualification'],style3)
			sheet1.write(s2,3,ele['designation'],style3)
			sheet1.write(s2,4,ele['date_of_join'],style3)
			sheet1.write(s2,5,ele['worked_days'],style3)
			sheet1.write(s2,6,ele['basic_amt'],style3)
			sheet1.write(s2,7,ele['vda_amt'],style3)
			sheet1.write(s2,8,ele['fda_amt'],style3)
			sheet1.write(s2,9,ele['allow'],style3)
			sheet1.write(s2,10,salary,style3)
			sheet1.write(s2,11,ele['fi_inc_amt'],style3)
			sheet1.write(s2,12,ele['spi_inc_amt'],style3)
			sheet1.write(s2,13,total,style3)
			sheet1.write(s2,14,ele['spi_five_inc_amt'],style3)
			sheet1.write(s2,15,ele['spi_six_inc_amt'],style3)
			sheet1.write(s2,16,ele['spi_seven_inc_amt'],style3)
			sheet1.write(s2,17,total_spl_inc,style3)
			sheet1.write(s2,18,ele['last_inc_amt'],style3)
			sheet1.write(s2,19,ele['last_inc_date'],style3)
			sheet1.write(s2,20,el,style3)
			sheet1.write(s2,21,ele['bonus_amt'],style3)
			sheet1.write(s2,22,gratuity,style3)
			sheet1.write(s2,23,(ele['basic_amt']+ele['vda_amt']+ele['fda_amt']),style3)
			sheet1.write(s2,24,ele['pf_amt'],style3)
			sheet1.write(s2,25,ele['esi_amt'],style3)
			sheet1.write(s2,26,ele['shoe_amt'],style3)
			sheet1.write(s2,27,ele['coff_allow_amt'],style3)
			sheet1.write(s2,28,(ctc_per_mon),style3)
			sheet1.write(s2,29,round((ctc_per_mon/30),2),style3)
		
			#~ ss2 = 
			
																	
			
			sno = sno + 1
		sheet1.write_merge(s2+2, s2+2, 0, 5,"Total",style3)
		sheet1.write(s2+2,6,basic_amt,style3)
		sheet1.write(s2+2,7,vda_amt,style3)
		sheet1.write(s2+2,8,fda_amt,style3)
		sheet1.write(s2+2,9,allow_amt,style3)
		sheet1.write(s2+2,10,'',style3)
		sheet1.write(s2+2,11,'',style3)
		sheet1.write(s2+2,12,'',style3)
		sheet1.write(s2+2,13,'',style3)
		sheet1.write(s2+2,14,'',style3)
		sheet1.write(s2+2,15,'',style3)
		sheet1.write(s2+2,16,'',style3)
		sheet1.write(s2+2,17,'',style3)
		sheet1.write(s2+2,18,'',style3)
		sheet1.write(s2+2,19,'',style3)
		sheet1.write(s2+2,20,'',style3)
		sheet1.write(s2+2,21,bonus_amt,style3)
		sheet1.write(s2+2,22,bonus_amt,style3)
		sheet1.write(s2+2,23,bonus_amt,style3)
		sheet1.write(s2+2,24,pf_amt,style3)
		sheet1.write(s2+2,25,esi_amt,style3)
		sheet1.write(s2+2,26,shoe_amt,style3)
		sheet1.write(s2+2,27,coff_allow_amt,style3)
		sheet1.write(s2+2,28,'',style3)
		sheet1.write(s2+2,29,'',style3)
		print "lassssssssssssssssssssssssssssssssssssssssssssssssssssssssss",s2
			
		"""Parsing data as string """
		file_data=StringIO.StringIO()
		o=wbk.save(file_data)		
		"""string encode of data in wksheet"""		
		out=base64.encodestring(file_data.getvalue())
		"""returning the output xls as binary"""
		report_name = 'STAFF_CTC_PRINT' + '.' + 'xls'
		
		return self.write(cr, uid, ids, {'rep_data':out,'state':'done','name':report_name,},context=context)
		
kg_excel_staff_ctc_report()
