import time
from osv import fields, osv
import netsvc
import pooler
from datetime import datetime
from datetime import date
from osv.orm import browse_record, browse_null
from tools.translate import _

class dep_issue_register_wizard(osv.osv_memory):
	_name = "dep.issue.register.wizard"
	_description = "Issue Register Wiz"
	
	_columns = {
	
				'fis_year': fields.many2one('account.fiscalyear','Fiscal year',readonly=True),
				'user_id': fields.many2one('res.users', 'User ID'),
				'company_id': fields.many2one('res.company', 'Company Name',required=True),
				'from_date': fields.date('From Date'),
				'to_date': fields.date('To Date'),
				'dep_id':fields.many2many('kg.depmaster','dep_issue_register2','wiz_id','dep_id','Department Name',domain="[('state','in',('draft','confirm','approved'))]"),
				'product':fields.many2many('product.product','dep_issue_product2','product_wiz_id','product_dep_id','Product',domain="[('state','in',('draft','confirm','approved'))]"),
				'issue_status': fields.selection([('approved', 'Approved'),('cancelled','Cancelled')], "Status"),
				'filter': fields.selection([('filter_no', 'No Filters'), ('filter_date', 'Date')], "Filter by"),
				'print_date': fields.datetime('Creation Date', readonly=True),
			}
	
	def _get_from_date(self, cr, uid, context=None):
		today = date.today()
		fis_obj = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start','<=',today),('date_stop','>=',today)])
		fis_id = self.pool.get('account.fiscalyear').browse(cr,uid,fis_obj[0])
		from_date = fis_id.date_start
		d2 = datetime.strptime(from_date,'%Y-%m-%d')
		res = d2.strftime('%Y-%m-%d')
		
		return res
	
	def _get_fis(self, cr, uid, context=None):
		today = date.today()
		fis_obj = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start','<=',today),('date_stop','>=',today)])
		fis_id = self.pool.get('account.fiscalyear').browse(cr,uid,fis_obj[0])
		fisyear_id = fis_id.id
		return fisyear_id
		
		
						
	_defaults = {
				
				'user_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id,
				'company_id':1,
				'from_date': lambda * a: time.strftime('%Y-%m-%d'),
				'to_date': lambda * a: time.strftime('%Y-%m-%d'),
				'fis_year': _get_fis,
				'filter':'filter_date',
				'print_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
				
				}
		
	def create_report(self, cr, uid, ids, context={}):
		data = self.read(cr,uid,ids,)[-1]
		return {
			'type'		 : 'ir.actions.report.xml',
			'report_name'   : 'jasper_kg_dep_issue',
			'datas': {
					'model':'dep.issue.register.wizard',
					'id': context.get('active_ids') and context.get('active_ids')[0] or False,
					'ids': context.get('active_ids') and context.get('active_ids') or [],
					'report_type':'pdf',
					'form':data
				},
			'nodestroy': False
			}
			
	def _date_check(self,cr,uid,ids,context=None):
		rec=self.browse(cr,uid,ids[0])
		current_date=time.strftime('%Y-%m-%d')
		if rec.from_date > current_date or rec.to_date > current_date:
			raise osv.except_osv(_('Warning!'),
						_('Future Date are not allowed in Start Date and End Date!!'))
			return False
		return True
		
	def _enddate_check(self,cr,uid,ids,context=None):
		rec=self.browse(cr,uid,ids[0])
		if rec.to_date < rec.from_date:
			raise osv.except_osv(_('Warning!'),
						_('End Date is lesser than Start Date!!'))
			return False
		return True
		
	_constraints = [
	
		(_date_check, 'Future Dates are Not Allowed !!!', ['Check Date']),
		(_enddate_check, 'Future Dates are Not Allowed !!!', ['Check Date']),

	]
	
dep_issue_register_wizard()

