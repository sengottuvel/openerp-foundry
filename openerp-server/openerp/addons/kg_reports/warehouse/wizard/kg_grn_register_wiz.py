import time
from lxml import etree
from osv import fields, osv
from tools.translate import _
import pooler
import logging
import netsvc
logger = logging.getLogger('server')
import datetime
from datetime import datetime
from datetime import date

class kg_grn_register_wiz(osv.osv_memory):
	
	_name = 'kg.grn.register.wiz'
	_columns = {
		
		'fis_year': fields.many2one('account.fiscalyear','Fiscal year',readonly=True),
		'product_id':fields.many2many('product.product','kg_grn_wiz_pro','order_id','product_id','Product Name',domain="[('state','in',('draft','confirm','approved'))]"),
		'supplier_id':fields.many2many('res.partner','kg_grn_wiz_sup','order_id','supplier_id','Supplier',domain="[('partner_state','not in',('cancel','reject')),('supplier','=',True)]"),
		'division': fields.selection([('ppd','PPD'),('ipd','IPD'),('foundry','Foundry')],'Division'),
		'filter': fields.selection([('filter_no', 'No Filters'), ('filter_date', 'Date')], "Filter by", required=True),
		'from_date': fields.date("Start Date"),
		'to_date': fields.date("End Date"),
		'print_date': fields.datetime('Creation Date', readonly=True),
		'printed_by': fields.many2one('res.users','Printed By',readonly=True),
		'status': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('done', 'Done'),('inv','Invoiced'),('cancel','Cancelled'),('reject','Rejected')], "Status"),
		'company_id': fields.many2one('res.company', 'Company Name'),
		'user_id': fields.many2one('res.users', 'User ID'),
		
	}
	
	_defaults = {
		
		'filter'    : 'filter_date', 
		'from_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'to_date'   : lambda * a: time.strftime('%Y-%m-%d'),
		'print_date': fields.datetime.now,
		'printed_by': lambda obj, cr, uid, context: uid,
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.grn.register.wiz', context=c),
		'user_id'   : lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id,
		
	}
	
	def create_report(self, cr, uid, ids, context={}):
		data = self.read(cr,uid,ids,)[-1]
		print data,' create_report('
		return {
			'type'		  : 'ir.actions.report.xml',
			'report_name' : 'jasper_kg_grn_register',
			'datas'       : {
							'model'		  : 'kg.grn.register.wiz',
							'id'		  : context.get('active_ids') and context.get('active_ids')[0] or False,
							'ids'		  : context.get('active_ids') and context.get('active_ids') or [],
							'report_type' : 'pdf',
							'form' 		  : data
								},
			'nodestroy'   : False
			}
	
	def _enddate_check(self,cr,uid,ids,context=None):
		rec=self.browse(cr,uid,ids[0])
		if rec.to_date < rec.from_date:
			raise osv.except_osv(_('Warning!'),_('End Date is lesser than Start Date!!'))
		return True
	
	_constraints = [
		
		(_enddate_check, 'Future Dates are Not Allowed !!!', ['Check Date']),
		
	]
	
kg_grn_register_wiz()
