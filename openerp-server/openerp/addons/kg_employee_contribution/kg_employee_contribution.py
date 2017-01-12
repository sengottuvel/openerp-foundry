from datetime import date
from osv import fields,osv 
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import datetime
import calendar

class kg_empolyee_contribution(osv.osv):
	_name = 'kg.employee.contribution'
	_description = 'Enables you to verify employee contribution'
	_columns = {
				'from_date':fields.datetime('Creation Date',readonly = True),
				'to_date':fields.date('Valid Date',readonly=True, states={'draft':[('readonly',False)]}),
				'active':fields.boolean('Active',readonly=True),
				'expiry_date':fields.datetime('Expiry Date',readonly=True, states={'draft':[('readonly',False)]}),
				'esi_slab':fields.float('ESI Applicable Upto',readonly=True, states={'draft':[('readonly',False)]},required = True),
				'state': fields.selection([('draft', 'To Submit'),('confirm', 'To Approve'),('validate', 'Approved')],
						'Status', readonly=True, track_visibility='onchange'),
				'cont_line_id':fields.one2many('kg.employee.contribution.line','cont_line_entry','Line id',readonly=True ,states = {'draft': [('readonly', False)]}),
				'pf_max_amt': fields.integer('PF Max Limit', required=True),
				}

	_defaults = {
		'state': 'draft',
		'active': True,
		'from_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
				}
	
	
	def approve_entry(self, cr, uid, ids,context=None):		
		self.write(cr,uid,ids,{'state':'validate'})
		return True
		
	def confirm_entry(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		entry_obj = self.pool.get('kg.employee.contribution')
		start_date = entry.from_date
		entry_id=entry.id	
		duplicate_ids= entry_obj.search(cr, uid, [('id' ,'!=', entry_id)])
		if duplicate_ids:
			dup_rec = entry_obj.browse(cr,uid,duplicate_ids[0])
			today_date = datetime.datetime.today()
			dup_rec.write({'active': False})
			dup_rec.write({'expiry_date':today_date})
		self.write(cr,uid,ids,{'state':'confirm'})	
		return True
		
	def draft_entry(self, cr, uid, ids, context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True
	
	def _esi_check(self, cr, uid, ids, context=None):
		record = self.browse(cr, uid, ids[0])
		if record.esi_slab <= 0:
			return False
		else:
			return True
		
	def _check_entry_line(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if not entry.cont_line_id :
			return False
		else:
			for line in entry.cont_line_id:
				if line.cont_type == 'percent':
					if line.contribution_percentage > 100:
						raise osv.except_osv( ('Warning!'), ('You percentage cannot be more than 100.'))
						return False
				if line.contribution_percentage == 0.00: 
					return False
		return True

	
	
	_constraints = [
		
		(_check_entry_line, 'Entry Lines should not be empty !!',['Line Entry']),
		(_esi_check, 'ESI slab amount can not be empty !!',['Esi Slab']),
				
		]
kg_empolyee_contribution()

class kg_employee_contribution_line(osv.osv):
	_name = 'kg.employee.contribution.line'		
	_columns = {
				'cont_line_entry':fields.many2one('kg.employee.contribution','Line Entry',required=True),
				'emp_contribution':fields.selection([('pf','PF'),('esi','ESI'),('insurance','Insurance')],'Contribution Heads',required = True),
				'cont_type':fields.selection([('fixed_amt','Fixed Amount'),('percent','Percentage')],'Type',required=True),
				'contribution_percentage':fields.float('Value',required=True)
	}
	_defaults = {
			'cont_type':'percent'
			}
kg_employee_contribution_line()
