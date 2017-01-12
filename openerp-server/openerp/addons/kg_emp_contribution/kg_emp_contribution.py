from datetime import date
from osv import fields,osv 
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import datetime
import calendar

class kg_emp_contribution(osv.osv):
	_name = 'kg.emp.contribution'
	_description = 'Enables you to verify employee contribution'
	_columns = {
				'from_date':fields.datetime('Creation Date',readonly = True),
				'active':fields.boolean('Active'),
				'expiry_date':fields.datetime('Expiry Date'),
				'state': fields.selection([('draft', 'To Submit'),('confirm', 'To Approve'),('validate', 'Approved')],
						'Status', readonly=True, track_visibility='onchange'),
				'emp_cont_line_id':fields.one2many('kg.emp.contribution.line','emp_cont_line_entry','Line id',readonly=True ,states = {'draft': [('readonly', False)]})
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
		entry_obj = self.pool.get('kg.emp.contribution')
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
		
		
	def _check_entry_line(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if not entry.emp_cont_line_id:
			return False
		else:
			for line in entry.emp_cont_line_id:
				if line.cont_type == 'percent':
					if line.emp_cont_value > 100:
						raise osv.except_osv( ('Warning!'), ('You percentage cannot be more than 100.'))
						return False
				if line.emp_cont_value == 0.00:
					return False
		return True
	
	"""def _check_dup_vals(self,cr,uid,ids,context = None):
		entry = self.browse(cr,uid,ids[0])
		if entry.emp_cont_line_id:
			for line in entry.emp_cont_line_id:
				if line.emp_contribution == """ 
	
	_constraints = [
		
		(_check_entry_line, 'Line entry can not be empty !!',['Line Entry']),
				
		]
	
kg_emp_contribution()

class kg_emp_contribution_line(osv.osv):
	
	_name = 'kg.emp.contribution.line'		
	_columns = {
				'emp_cont_line_entry':fields.many2one('kg.emp.contribution','Line Entry'),
				'emp_contribution':fields.selection([('pf','PF'),('esi','ESI'),('insurance','Insurance')],'Contribution Heads',required = True),
				'cont_type':fields.selection([('fixed_amt','Fixed Amount'),('percent','Percentage')],'Type',required=True),
				'emp_cont_value':fields.float('Value',required=True)
	}
	_defaults = {
			'cont_type':'percent'
			}
kg_emp_contribution_line()
