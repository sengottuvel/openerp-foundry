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

class kg_foundry_partlist_print(osv.osv_memory):
	_name = "kg.foundry.partlist.print"
	_description = "Foundry Part List"
	
	_columns = {
		
		## Basic Info
		
		'company_id': fields.many2one('res.company', 'Company'),
		'print_date': fields.datetime('print Date', readonly=True),
		'printed_by': fields.many2one('res.users','Printed By',readonly=True),  
		
		## If any filter it should be many2many only. Don't use many2one filter unless it's must	
		'order_type': fields.selection([('schedule_wise','Schedule Wise'),('wo_wise','WO Wise')],'Type',required=True),
		'order_id': fields.many2many('kg.work.order', 'm2m_work_order_report_details', 'foundry_wiz_id', 'order_id','WO No' ,domain="[('state','=','confirmed')]"),
		'schedule_id': fields.many2many('kg.schedule', 'm2m_schedule_report_details', 'sche_wiz_id', 'schedule_id','Schedule No', domain="[('state','=','confirmed')]"),
		
	}
	
		
	_defaults = {		
		'order_type': 'wo_wise',
		'print_date': time.strftime('%Y-%m-%d %H:%M:%S'),
		'printed_by': lambda obj, cr, uid, context: uid,		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.foundry.partlist.print', context=c),
	 }
	
	
	
	def create_report(self, cr, uid, ids, context={}):	
	
		rec = self.browse(cr,uid,ids[0])	
		data = self.read(cr,uid,ids,)[-1]		
		print data,' create_report('
		return {
			'type'		 : 'ir.actions.report.xml',
			'report_name'   : 'jasper_foundry_partlist_report',
			'datas': {
					'model':'kg.foundry.partlist.print',
					'id': context.get('active_ids') and context.get('active_ids')[0] or False,
					'ids': context.get('active_ids') and context.get('active_ids') or [],
					'report_type': 'pdf',
					'form':data
				},
			'nodestroy': False
			}	
	
	
kg_foundry_partlist_print()

