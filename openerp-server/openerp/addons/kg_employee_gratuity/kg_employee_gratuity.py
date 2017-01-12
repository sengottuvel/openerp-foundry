from osv import fields,osv 
import datetime
import time, datetime 
from datetime import * 
import calendar 
import math
import re
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
import netsvc


class kg_employee_gratuity(osv.osv):
	_name = 'kg.employee.gratuity'
	_description = 'Employee Gratuity'
	
	#req = True
	
	_columns = {
				
				'from_date':fields.date('Join Date',readonly=True ),
				'to_date':fields.date('To Date',readonly=True ),
				'creation_date':fields.datetime('Creation Date',readonly=True),
				'created_by':fields.many2one('res.users','Created By',readonly=True),
				'active':fields.boolean('Active',readonly=True),
				'employee_id':fields.many2one('hr.employee','Employee Name',readonly=True ),
				'employee_name':fields.char('Employee Code',readonly=True ),
				'state': fields.selection([('draft', 'Draft'),('waiting', 'Confirmed'),('confirm','Approved'),('paid','Paid'),('cancel','Cancelled')],
								'Status', readonly=True, track_visibility='onchange'),
				'gratuity_amount':fields.float('Gratuity Amount',readonly=True ),
				'gratuity_date':fields.date('Gratuity Date',readonly=True ),
				'payment_mode':fields.selection([('bank','Through Bank'),('cash','Through Cash'),('cheque','Through Cheque')],'Payment Mode'
													,readonly=True ,states = {'waiting': [('readonly', False),('required', True)]}),
				'bank': fields.many2one('res.bank','Account Journal Type',readonly = False , states = {'paid': [('readonly', True)],'approved': [('readonly', True)]}),
				'acc_no': fields.char('Account No',readonly = False , states = {'paid': [('readonly', True)],'approved': [('readonly', True)]}),
				'cheque_no':fields.char('Cheque No',states = {'approved': [('readonly', True)]}),
				'confirmed_date':fields.datetime('Confirmed Date',readonly = True ),
				'confirmed_by' : fields.many2one('res.users', 'Confirmed By', readonly= True),
				'paid_date':fields.datetime('Paid Date',readonly = True),
				'paid_by' : fields.many2one('res.users', 'Paid By', readonly= True),
				
				}

	_defaults = {
		'state': 'draft',
		'to_date':fields.date.context_today,
		'active': True,
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'created_by': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
				}
				
	
	def confirm_entry(self, cr, uid, ids,context=None):
		self.write(cr,uid,ids,{'state':'waiting'})
		return True	
	
	def approve_entry(self, cr, uid, ids,context=None):
		timein = str(datetime.now())
		self.write(cr,uid,ids,{'state':'confirm', 'confirmed_date':  timein,
									'confirmed_by' :  uid})	
		return True
		
	def paid_entry(self,cr,uid,ids,context = None):
		timein = str(datetime.now())
		self.write(cr,uid,ids,{'state':'paid', 'paid_date':  timein,
									'paid_by' : uid})
		return True
		
	def _check_entry_line(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if not entry.cont_line_id:
			return False
		else:
			for line in entry.cont_line_id:
				if line.cont_type == 'percent':
					if line.contribution_percentage > 100:
						raise osv.except_osv( _('Warning!'), _('You percentage cannot be more than 100.'))
						return False
				if line.contribution_percentage == 0.00: 
					return False
		return True
	
	
	def compute_gratuity_date(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		emp_sql = """ select id from hr_employee where status = 'in_service' """
		cr.execute(emp_sql)
		data = cr.dictfetchall()
		gratuity_obj = self.pool.get('kg.employee.gratuity')
		gratuity_id = gratuity_obj.search(cr, uid, [('id','!=',entry.id)])
		n=0
		for item in data:
			# Employee Id
			emp_id = self.pool.get('hr.employee').browse(cr,uid,item['id'])
			
			#Contract id for gross salary
			con_id = self.pool.get('hr.contract').search(cr, uid, [('employee_id', '=', item['id'])])
			
			con_gross = 0.00
			tot_grt_amount = 0.00
			if con_id:
				con_rec= self.pool.get('hr.contract').browse(cr, uid,con_id[0])	
				con_gross = con_rec.gross_salary
				sal_det = self.pool.get('kg.salary.detail')
				ctc_ids = sal_det.search(cr,uid,[('salary_id','=',con_id[0])])
			
			
			#Calculation for gratuity amount
			gra_from_date = str( emp_id.join_date)
			crut_date = date.today() 
			crut_date = str(crut_date) 
			d1 = datetime.strptime(gra_from_date, "%Y-%m-%d") 
			d2 = datetime.strptime(crut_date, "%Y-%m-%d") 
			daysDiff = str((d2-d1).days) 
			diff = float(daysDiff)/365
			gratuity_date = d1 + timedelta(days = (5*365))
			if diff >= 5.00:
				for ids in ctc_ids:
					sal_rec = sal_det.browse(cr,uid,ids)
					if sal_rec.salary_type.code == 'BASIC' or sal_rec.salary_type.code == 'DA':
						if sal_rec.type == 'fixed_amt':
							grat_amount = (sal_rec.salary_amount*15*diff)/26
							tot_grt_amount += grat_amount
						else:
							per_grat = (con_gross * sal_rec.salary_amount)/100
							grat_amount = (per_grat*15* diff )/26
							tot_grt_amount += grat_amount
				
				vals = {
								'from_date': gra_from_date,
								'to_date': crut_date,
								'employee_id': emp_id.id,
								'employee_name':emp_id.emp_code,
								'gratuity_amount':  (round(tot_grt_amount,0)),
								'gratuity_date':gratuity_date,
								'state': 'draft',
							}
				grt_search_ids = gratuity_obj.search(cr,uid,[('employee_id','=',item['id'])])
				if not grt_search_ids:
					self.create(cr,uid,vals)
				else:
					self.write(cr,uid,grt_search_ids,vals)
		return data

kg_employee_gratuity()
