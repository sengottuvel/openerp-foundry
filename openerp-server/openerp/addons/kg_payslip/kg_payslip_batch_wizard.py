
import time
from datetime import datetime
from dateutil import relativedelta
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv
from openerp.tools.translate import _

class kg_payslip_batch_wizard(osv.osv_memory):

	_name ='hr.payslip.employees'
	_inherit = 'hr.payslip.employees'
	
	_columns = {
        
        'employee_ids': fields.many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 
				'employee_id', 'Employees'),
		}	
	
	def compute_sheet(self, cr, uid, ids, context=None):
		emp_pool = self.pool.get('hr.employee')
		slip_pool = self.pool.get('hr.payslip')
		run_pool = self.pool.get('hr.payslip.run')				
		slip_ids = []
		if context is None:
			context = {}
		data = self.read(cr, uid, ids, context=context)[0]
		run_data = {}
		if context and context.get('active_id', False):
			run_data = run_pool.read(cr, uid, context['active_id'], ['date_start', 'date_end', 'credit_note'])
			print "run_data ---------------run_data =========>>>", run_data
			batch_rec = run_pool.browse(cr, uid,run_data['id'])	
			sear_dup_runs = run_pool.search(cr,uid,[('date_start','=',batch_rec.date_start),('date_end','=',batch_rec.date_end),('id','!=',batch_rec.id),('state','=','done')])
			if sear_dup_runs:
				print "Getting Deleted........................................................................................................"
				for dup_ids in sear_dup_runs:
					print "dup_idsdup_idsdup_idsdup_idsdup_idsdup_ids",dup_ids
					sql = """delete from hr_payslip_run where id =%s """%(dup_ids)
					cr.execute(sql)
			else:
				pass		
		from_date =  run_data.get('date_start', False)
		to_date = run_data.get('date_end', False)
		credit_note = run_data.get('credit_note', False)
		if not data['employee_ids']:
			raise osv.except_osv(_("Warning!"), _("You must select employee(s) to generate payslip(s)."))
		print "All Employee's :::::::::;", emp_pool.browse(cr, uid, data['employee_ids'], context=context)
		
		for emp in emp_pool.browse(cr, uid, data['employee_ids'], context=context):
			slip_data = slip_pool.onchange_employee_id(cr, uid, [], from_date, to_date, emp.id, contract_id=False, context=context)
			res = {
				'employee_id': emp.id,
				'emp_name': emp.code,
				'emp_categ_id': emp.emp_categ_id.id,
				'division_id': emp.division_id.id,
				'number': self.pool.get('ir.sequence').get(cr, uid, 'hr.payslip'),
				'struct_id': slip_data['value'].get('struct_id', False),
				'contract_id': slip_data['value'].get('contract_id', False),
				'payslip_run_id': context.get('active_id', False),
				'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids', False)],
				'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids', False)],
				'date_from': from_date,
				'date_to': to_date,
				'credit_note': credit_note,
			}
			slip_ids.append(slip_pool.create(cr, uid, res, context=context))
			

		batch_rec.write({'state' : 'done'})
		print "slip_ids---------------------------", slip_ids		
		val = slip_pool.hr_verify_sheet(cr, uid, slip_ids, context=context)
		
		total_value = 0.00
		for s_ids in slip_ids:
			pay_rec = slip_pool.browse(cr,uid,s_ids)
			total_value += pay_rec.round_val
		batch_rec.write({'tot_val' : total_value})	
		return {'type': 'ir.actions.act_window_close'}

kg_payslip_batch_wizard()

