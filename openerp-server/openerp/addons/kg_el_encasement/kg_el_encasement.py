from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
from datetime import date, datetime, timedelta
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')
today = date.today()

class kg_el_encasement(osv.osv):

	_name = "kg.el.encasement"
	_description = "EL Encasement"
	
	### Version 0.1
	
	def _get_modify(self, cr, uid, ids, field_name, arg,  context=None):
		res={}		
		if field_name == 'modify':
			for h in self.browse(cr, uid, ids, context=None):
				res[h.id] = 'no'
				if h.state == 'approved':
					cr.execute(""" select * from 
					(SELECT tc.table_schema, tc.constraint_name, tc.table_name, kcu.column_name, ccu.table_name
					AS foreign_table_name, ccu.column_name AS foreign_column_name
					FROM information_schema.table_constraints tc
					JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
					JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
					WHERE constraint_type = 'FOREIGN KEY'
					AND ccu.table_name='%s')
					as sam  """ %('kg_el_encasement'))
					data = cr.dictfetchall()	
					if data:
						for var in data:
							data = var
							chk_sql = 'Select COALESCE(count(*),0) as cnt from '+str(data['table_name'])+' where '+data['column_name']+' = '+str(ids[0])							
							cr.execute(chk_sql)			
							out_data = cr.dictfetchone()
							if out_data:								
								if out_data['cnt'] > 0:
									res[h.id] = 'no'
									return res
								else:
									res[h.id] = 'yes'
				else:
					res[h.id] = 'no'	
		return res	
		
		### Version 0.2
		
		
	
	_columns = {
	
		## Basic Info
			
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),

		## Entry Info
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'active': fields.boolean('Active'),
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'ap_rej_date': fields.datetime('Approved/Reject Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Reject By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		
		## Module Requirement Info
		
		'emp_categ_id':fields.many2one('kg.employee.category','Employee Category',domain=[('state','=','approved')]),
		'year':fields.char('Year'),
		'expiry_date':fields.date('Expiry Date'),
		'sal_base': fields.selection([('gross','From Gross'),('comp','From Component')],'Salary Base'),
		'min_el_days':fields.float('Minimum Day Eligible'),
		'mat_leave_app':fields.boolean('Consider Maternity Leave'),
		'set_amt_type': fields.selection([('cash','Cash'),('leave','Leave')],'Settlement Mode'),
		'allow_ded_id':fields.many2many('hr.salary.rule','allow_ded','yr_bns','allow_ids','Bonus Base Components',domain=[('state','=','approved')]),
		
		## Child Tables Declaration
		
		'line_id':fields.one2many('ch.el.encasement','header_id','Line id',readonly=True, states={'draft':[('readonly',False)]}),
		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.master', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		'min_el_days': 240,
		'mat_leave_app': True,
		'set_amt_type': 'cash',
		'year':lambda * a: today.year,
		
	}
	
	####Validations####
	
	def  _validations (self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		check_dup =  self.pool.get('kg.el.encasement').search(cr,uid,([('year','=',rec.year)]))
		if len(check_dup) > 1:
			raise osv.except_osv(_('Warning !!'),
				_('Encasement for  this Year is created already !!'))
		
		if rec.min_el_days <= 0.00:
			raise osv.except_osv(_('Warning !!'),
				_('Minimum Day Eligible should not be less than or equal to zero !!'))
		return True
	_constraints = [

		(_validations, 'validations', [' ']),		
		
	]
	
	## Basic Needs	
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			if rec.cancel_remark:
				self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Cancel remark is must !!'),
					_('Enter the remarks in Cancel remarks field !!'))
		else:
			pass
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			if not rec.line_id:
				raise osv.except_osv(_('Warning!'),
					_('Employee Details should not be empty !!'))
			else:
				self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':			
			self.write(cr, uid, ids, {'state': 'draft'})
		else:
			pass
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		import StringIO
		import base64
		
		try:
			import xlwt
		except:
		   raise osv.except_osv('Warning !','Please download python xlwt module from\nhttp://pypi.python.org/packages/source/x/xlwt/xlwt-0.7.2.tar.gz\nand install it')
		if rec.state == 'confirmed':
			sql = """		

				select 

				distinct(division.name) as division_name,
				(select count(employee_id) from ch_el_encasement where emp_division_id=division.id) as no_of_emp,
				to_char((select sum(encase_amt) from ch_el_encasement where emp_division_id=division.id),'999990D99')as total_amt


				from ch_el_encasement encash

				left join kg_division_master division on (division.id=encash.emp_division_id)"""


				

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
			
			sheet1 = wbk.add_sheet('EL_ENCASHMENT_PRINT')
			s2=6
			sheet1.col(0).width = 2000
			sheet1.col(1).width = 3000
			sheet1.col(2).width = 6000
			sheet1.col(3).width = 7000
			sheet1.col(4).width = 4000
			sheet1.col(5).width = 4000
			sheet1.col(6).width = 4000
			sheet1.col(7).width = 4000
			sheet1.col(8).width = 4000
			
			
			
			""" writing field headings """
			#~ date_from=datetime.date_from.strptime('%d-%m-%Y')
			

			#~ date_from = datetime.strptime(rec.date_from, '%Y-%m-%d').strftime('%d/%m/%Y')
			#~ date_to = datetime.strptime(rec.date_to, '%Y-%m-%d').strftime('%d/%m/%Y')
			
			
			sheet1.write_merge(0, 3, 0, 3,"SAM TURBO INDUSTRY PRIVATE LIMITED \n Avinashi Road, Neelambur,\n Coimbatore - 641062 \n Tel:3053555, 3053556,Fax : 0422-3053535",style2)
			sheet1.row(0).height = 450
			sheet1.write_merge(4, 4, 0, 3,"STAFF EL ENCASHMENT OF "+rec.year,style2)
			sheet1.write_merge(5, 5, 0, 3,"",style2)
			#~ sheet1.write_merge(3, 3, 0, 5,"",style2)
			
			sheet1.insert_bitmap('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_reports/img/sam.bmp',0,0)
			sheet1.write(s2,0,"S.NO",style1)
			#~ sheet1.row(s1).height = 490
			sheet1.write(s2,1,"DIVISION",style1)
			sheet1.write(s2,2,"NO.OF.STAFF",style1)
			sheet1.write(s2,3,"EL ENCASHMENT AMT",style1)
			
			emp_count = 0
			grand_total = 0.00
			
			for ele in data:
				#~ print "ele['employee_name']ele['employee_name']ele['employee_name']ele['employee_name']",ele['employee_name']
				print "ele['total_amt']ele['total_amt']ele['total_amt']",ele['total_amt']
				if ele['total_amt'] is None:
					grand_total = 0.00
				else:
					grand_total += float(ele['total_amt'])
				if ele['no_of_emp'] is None:
					emp_count = 0.00
				else:
					emp_count += ele['no_of_emp']
				s2+=1
				
				sheet1.write(s2,0,sno,style3)
				sheet1.write(s2,1,ele['division_name'],style3)
				sheet1.write(s2,2,ele['no_of_emp'],style3)
				sheet1.write(s2,3,ele['total_amt'],style3)
				
				
				
				sno = sno + 1
			
			s2 = s2+1
			sheet1.write_merge(s2,s2, 0, 1,"Total",style2)
			sheet1.write(s2,2,emp_count,style3)
			sheet1.write(s2,3,grand_total,style3)
			
				
			"""Parsing data as string """
			file_data=StringIO.StringIO()
			o=wbk.save(file_data)		
			"""string encode of data in wksheet"""		
			out=base64.encodestring(file_data.getvalue())
			"""returning the output xls as binary"""
			report_name = 'EL_ENCASHMENT_PRINT' + '.' + 'xls'
		
			self.write(cr, uid, ids, {'rep_data':out,'report_name':report_name,},context=context)
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			if rec.remark:
				self.write(cr, uid, ids, {'state': 'reject','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Rejection remark is must !!'),
					_('Enter the remarks in rejection remark field !!'))
		else:
			pass
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state not in ('draft','cancel'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_el_encasement, self).write(cr, uid, ids, vals, context)	
	
	
	## Module Requirement
	
	def bonus_calc(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		con_obj=self.pool.get('hr.contract')
		emp_obj=self.pool.get('hr.employee')
		payslip_obj=self.pool.get('hr.payslip')
		payslip_line_obj=self.pool.get('hr.payslip.line')
		leaves_obj=self.pool.get('hr.holidays')
		con_ids = con_obj.search(cr,uid,[('emp_categ_id','=',rec.emp_categ_id.id),('active','=',True)])
		cur_year = rec.year
		year_start = date(date.today().year, 01, 01)
		year_end = date(date.today().year, 12, 31)
		print "year_startyear_startyear_startyear_start",year_start
		print "year_endyear_endyear_endyear_endyear_end",year_end
		#~ stop
		if rec.line_id:
			cr.execute('''delete from ch_el_encasement where header_id='%s' '''%(rec.id))
		else:
			pass
		if con_ids:
			if rec.allow_ded_id:
				base_comp_ids = [base_comps.code for base_comps in  rec.allow_ded_id]
				print "compidssssssssssssssss",tuple(base_comp_ids)
			bon_val = 0.00
			
			for cont_ids in con_ids:
				get_emp_categ_id= self.pool.get('kg.employee.category').search(cr,uid,[('code','=','WKP')])
				con_rec = con_obj.browse(cr,uid,cont_ids)
				cr.execute('''select sum(worked_days+od_days) from kg_monthly_attendance where start_date >= '%s' and end_date <= '%s' and employee_id = %s'''%(str(year_start),str(year_end),con_rec.employee_id.id))
				work_days = cr.dictfetchone()
				print"worked days for ",work_days['sum'],con_rec.employee_id.name
				tot_work_days = work_days['sum']
				if work_days['sum'] < rec.min_el_days:
					if rec.mat_leave_app == True:
						leave_ids = leaves_obj.search(cr,uid,[('employee_id','=',con_rec.employee_id.id),('from_date','>=',year_start),('to_date','<=',year_end),('holiday_status_id','=',18)])
						print "LEave ids are ..................................",leave_ids
						if leave_ids:
							for leaves_id in leave_ids:
								cr.execute('''select sum(number_of_days_temp) from hr_holidays where id = %s'''%(leaves_id))
								mat_leave_days = cr.dictfetchone()
								print "No of Maternity Leave days ",mat_leave_days['sum']
								tot_work_days = work_days['sum']+mat_leave_days['sum']
								print "Total Worked days .................................",tot_work_days
						else:
							tot_work_days = work_days['sum']
					else:
						tot_work_days = work_days['sum']
						print "Worked days ssssssssssssssssss.............................",tot_work_days
				if tot_work_days >= rec.min_el_days:
					if rec.sal_base == 'gross':
						yr_end_month = date(date.today().year, 01, 01)
						payslip_ids = payslip_obj.search(cr,uid,[('employee_id','=',con_rec.employee_id.id),('date_to','=',year_end)])
						if payslip_ids:
							payslip_rec = payslip_obj.browse(cr,uid,payslip_ids[0])
							el_eligible_days = work_days['sum']/20
							print "El Eligible Days are ",el_eligible_days
							print "Gross amount of the December month",payslip_rec.cross_amt
							el_amt = (payslip_rec.cross_amt/30)*el_eligible_days
							
					else:
						yr_end_month = date(date.today().year, 01, 01)
						print "capturing work days for the salary comp",work_days['sum']
						el_eligible_days = work_days['sum']/20
						print "el eligible days...........",el_eligible_days
						payslip_ids = payslip_obj.search(cr,uid,[('employee_id','=',con_rec.employee_id.id),('date_to','=',year_end)])
						if payslip_ids:
							base_ids = tuple(base_comp_ids)
							payslip_line_ids = payslip_line_obj.search(cr,uid,[('slip_id','=',payslip_ids[0]),('code','in',(base_ids))])
							if payslip_line_ids:
								sal_comp_amt = 0.00
								for pay_line_ids in payslip_line_ids:
									pay_line_rec = payslip_line_obj.browse(cr,uid,pay_line_ids)
									print "Salary components..............................",pay_line_rec.name,pay_line_rec.amount
									sal_comp_amt += pay_line_rec.amount
								el_amt = (sal_comp_amt/30)*el_eligible_days
					if rec.emp_categ_id.id == get_emp_categ_id[0]:
						if rec.sal_base == 'gross':
							el_amt = (payslip_rec.cross_amt/26)*el_eligible_days
							print "payslip gross amount and el eligible days.......................",payslip_rec.cross_amt,el_eligible_days
							print "el amount ++++++++++++++++++++++++",el_amt
						else:
							el_amt = (sal_comp_amt/26)*el_eligible_days
							print "sal component for the worker permanent.....................",sal_comp_amt,el_eligible_days
							print "el amount ++++++sal amt ++++++++++",el_amt
					self.pool.get('ch.el.encasement').create(cr,uid,
							{
								'header_id':rec.id,
								'employee_id':con_rec.employee_id.id,
								'emp_code':con_rec.code,
								'encase_days':tot_work_days,
								'encase_amt':el_amt,
								
							},context = None)

		return True
	
kg_el_encasement()

class ch_el_encasement(osv.osv):
	
	_name = "ch.el.encasement"
	_description = "EL Encasement Line"
	
	_columns = {

	'header_id':fields.many2one('kg.el.encasement','Header id'),
	'employee_id':fields.many2one('hr.employee','Employee'),
	'emp_code':fields.char('Code'),
	'encase_days':fields.float('Encashment Days'),
	'encase_amt':fields.float('Encashment Amount'),
	
	}
	
ch_el_encasement()	
