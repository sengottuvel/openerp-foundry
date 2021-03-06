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

class kg_spare_print(osv.osv_memory):
	_name = "kg.spare.print"
	_description = "Spare Report"
	
	_columns = {
		
		## Basic Info
		
		'company_id': fields.many2one('res.company', 'Company'),
		'print_date': fields.datetime('print Date', readonly=True),
		'printed_by': fields.many2one('res.users','Printed By',readonly=True),  
		'report_type': fields.selection([('pdf','PDF'),('xls','XLS')],'Report Type'), 
		
		## If any filter it should be many2many only. Don't use many2one filter unless it's must			
		'order_id': fields.many2many('ch.work.order.details', 'm2m_work_order_spare_print_report_details', 'foundry_wiz_id', 'order_id','WO No' ,domain="[('order_category','=','spare')]"),
		
		
	}
	
		
	_defaults = {		
		
		'print_date': time.strftime('%Y-%m-%d %H:%M:%S'),
		'printed_by': lambda obj, cr, uid, context: uid,	
		'report_type': 'pdf',	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.spare.print', context=c),
	 }
	
	
	
	def create_report(self, cr, uid, ids, context={}):	
	
		rec = self.browse(cr,uid,ids[0])	
		data = self.read(cr,uid,ids,)[-1]	
		if rec.report_type == 'pdf':
			 report_format = 'pdf'
		else:
			report_format = 'xls'		
		print data,' create_report('
		return {
			'type'		 : 'ir.actions.report.xml',
			'report_name'   : 'jasper_spare_report',
			'datas': {
					'model':'kg.spare.print',
					'id': context.get('active_ids') and context.get('active_ids')[0] or False,
					'ids': context.get('active_ids') and context.get('active_ids') or [],
					'report_type': report_format,
					'form':data
				},
			'nodestroy': False
			}	
	
	
kg_spare_print()

