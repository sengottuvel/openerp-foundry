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

class kg_pouring_pending_print(osv.osv_memory):
	_name = "kg.pouring.pending.print"
	_description = "Pouring Pending"
	
	_columns = {
		
		## Basic Info
		'as_on_date': fields.date("As On Date",required=True),		
		'company_id': fields.many2one('res.company', 'Company'),
		'print_date': fields.datetime('print Date', readonly=True),
		'printed_by': fields.many2one('res.users','Printed By',readonly=True),  
		
		## If any filter it should be many2many only. Don't use many2one filter unless it's must	
		'pattern_id': fields.many2many('kg.pattern.master', 'm2m_pattern_master_details', 'pour_wiz_id', 'pattern_id','Pattern No', domain="[('active','=','t')]"),
		#~ 'schedule_id': fields.many2many('kg.schedule', 'm2m_schedule_detail', 'sche_wiz_id', 'schedule_id','Schedule No', domain="[('state','=','confirmed')]"),
		'moc_id': fields.many2many('kg.moc.master', 'm2m_moc_master_details', 'pour_wiz_id', 'moc_id','MOC', domain="[('active','=','t')]"),
		'category': fields.selection([('1','MS NC'),('2','NC'),('3','Service'),('4','Emergency'),('5','Spare'),('6','Normal')],'Category'),
	}
	
		
	_defaults = {
		'as_on_date': time.strftime('%Y-%m-%d'),		
		'print_date': time.strftime('%Y-%m-%d %H:%M:%S'),
		'printed_by': lambda obj, cr, uid, context: uid,		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.pouring.pending.print', context=c),
	 }
	
	
	
	def create_report(self, cr, uid, ids, context={}):	
	
		rec = self.browse(cr,uid,ids[0])	
		data = self.read(cr,uid,ids,)[-1]		
		print data,' create_report('
		return {
			'type'		 : 'ir.actions.report.xml',
			'report_name'   : 'jasper_pouring_pending_report',
			'datas': {
					'model':'kg.pouring.pending.print',
					'id': context.get('active_ids') and context.get('active_ids')[0] or False,
					'ids': context.get('active_ids') and context.get('active_ids') or [],
					'report_type': 'pdf',
					'form':data
				},
			'nodestroy': False
			}	
	
	
kg_pouring_pending_print()

