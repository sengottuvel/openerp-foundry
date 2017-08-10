import time
from osv import fields, osv
import netsvc
import pooler
import time
from datetime import date
from osv.orm import browse_record, browse_null
from tools.translate import _
from datetime import datetime
import datetime as lastdate

a = datetime.now()
dt_time = a.strftime('%m/%d/%Y %H:%M:%S')

class kg_supplied_order_print(osv.osv_memory):
	_name = "kg.supplied.order.print"
	_description = "Supplier Order Details"
	
	_columns = {
		
		## Basic Info
		'from_date': fields.date("From Date",required=True),		
		'to_date': fields.date("To Date",required=True),		
		'company_id': fields.many2one('res.company', 'Company'),
		'print_date': fields.datetime('print Date', readonly=True),
		'printed_by': fields.many2one('res.users','Printed By',readonly=True),  
		
		## If any filter it should be many2many only. Don't use many2one filter unless it's must	
		'customer_id': fields.many2many('res.partner', 'm2m_supplied_customer_details', 'supplied_wiz_id', 'customer_id','Customer Name', domain="[('active','=','t')]"),
		'order_id': fields.many2many('ch.work.order.details', 'm2m_work_order_supplied_report_details', 'supplied_wiz_id', 'order_id','WO No' ,domain="[('state','=','confirmed')]"),
	}
	
		
	_defaults = {
		'from_date': time.strftime('%Y-%m-%d'),		
		'to_date': time.strftime('%Y-%m-%d'),		
		'print_date': time.strftime('%Y-%m-%d %H:%M:%S'),
		'printed_by': lambda obj, cr, uid, context: uid,		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.supplied.order.print', context=c),
	 }
	
	
	
	def create_report(self, cr, uid, ids, context={}):	
	
		rec = self.browse(cr,uid,ids[0])	
		data = self.read(cr,uid,ids,)[-1]		
		print data,' create_report('
		return {
			'type'		 : 'ir.actions.report.xml',
			'report_name'   : 'jasper_supplied_order_report',
			'datas': {
					'model':'kg.supplied.order.print',
					'id': context.get('active_ids') and context.get('active_ids')[0] or False,
					'ids': context.get('active_ids') and context.get('active_ids') or [],
					'report_type': 'pdf',
					'form':data
				},
			'nodestroy': False
			}	
	
	
kg_supplied_order_print()

