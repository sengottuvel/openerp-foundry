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

class kg_machine_list_report(osv.osv_memory):
	_name = "kg.machine.list.report"
	_description = "Machine List Report"
	
	_columns = {
		
		## Basic Info
		
		'company_id': fields.many2one('res.company', 'Company'),
		'print_date': fields.datetime('print Date', readonly=True),
		'printed_by': fields.many2one('res.users','Printed By',readonly=True),  
		
		## If any filter it should be many2many only. Don't use many2one filter unless it's must			
		'order_id': fields.many2many('ch.work.order.details', 'm2m_work_order_machine_list_report_details', 'foundry_wiz_id', 'order_id','WO No' ,domain="[('state','=','confirmed')]"),
		'order_category': fields.selection([('pump','Pump'),('spare','Spare'),('access','Accessories')],'Purpose', required=True),
		
	}
	
		
	_defaults = {		
		
		'print_date': time.strftime('%Y-%m-%d %H:%M:%S'),
		'printed_by': lambda obj, cr, uid, context: uid,		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.machine.list.report', context=c),
	 }
	
	
	
	def create_report(self, cr, uid, ids, context={}):	
	
		rec = self.browse(cr,uid,ids[0])
		
		cr.execute(""" select distinct order_id
						from m2m_work_order_machine_list_report_details  
						where foundry_wiz_id = %s """%(rec.id))
						
		access_items = cr.dictfetchone();
		
		print"access_items['order_id']",access_items['order_id']
		access_id = self.pool.get('ch.wo.accessories').search(cr,uid,[('header_id','=',access_items['order_id'])])
		
		
		
		print"access_idaccess_idaccess_id",access_id
		print"access_items00",access_items
		
		
		
		if rec.order_category == 'access':		
		
					
			data = self.read(cr,uid,ids,)[-1]		
			print data,' create_report('
			return {
				'type'		 : 'ir.actions.report.xml',
				'report_name'   : 'jasper_access_list_report',
				'datas': {
						'model':'kg.machine.list.report',
						'id': context.get('active_ids') and context.get('active_ids')[0] or False,
						'ids': context.get('active_ids') and context.get('active_ids') or [],
						'report_type': 'pdf',
						'form':data
					},
				'nodestroy': False
				}
						
		
		else:		
		
			data = self.read(cr,uid,ids,)[-1]		
			print data,' create_report('
			return {
				'type'		 : 'ir.actions.report.xml',
				'report_name'   : 'jasper_machine_list_report',
				'datas': {
						'model':'kg.machine.list.report',
						'id': context.get('active_ids') and context.get('active_ids')[0] or False,
						'ids': context.get('active_ids') and context.get('active_ids') or [],
						'report_type': 'pdf',
						'form':data
					},
				'nodestroy': False
				}	
		
	
	
kg_machine_list_report()

