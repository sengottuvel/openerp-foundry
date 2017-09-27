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

class kg_fettling_invoice_print(osv.osv_memory):
	_name = "kg.fettling.invoice.print"
	_description = "Fettling Invoice Details"
	
	_columns = {
		
		## Basic Info
		'from_date': fields.date("From Date",required=True),			
		'to_date': fields.date("To Date",required=True),			
		'company_id': fields.many2one('res.company', 'Company'),
		'print_date': fields.datetime('print Date', readonly=True),
		'printed_by': fields.many2one('res.users','Printed By',readonly=True),  
		
		## If any filter it should be many2many only. Don't use many2one filter unless it's must	
		'contractor_id': fields.many2many('res.partner', 'm2m_sc_invoice_details', 'invoice_wiz_id', 'contractor_id','Contractor Name', domain="[('contractor','=','t')]"),
		
	}
	
		
	_defaults = {
		'from_date': time.strftime('%Y-%m-%d'),		
		'to_date': time.strftime('%Y-%m-%d'),		
		'print_date': time.strftime('%Y-%m-%d %H:%M:%S'),
		'printed_by': lambda obj, cr, uid, context: uid,		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.fettling.invoice.print', context=c),
	 }
	
	
	
	def create_report(self, cr, uid, ids, context={}):	
	
		rec = self.browse(cr,uid,ids[0])	
		data = self.read(cr,uid,ids,)[-1]		
		print data,' create_report('
		return {
			'type'		 : 'ir.actions.report.xml',
			'report_name'   : 'jasper_fettling_invoice_report',
			'datas': {
					'model':'kg.fettling.invoice.print',
					'id': context.get('active_ids') and context.get('active_ids')[0] or False,
					'ids': context.get('active_ids') and context.get('active_ids') or [],
					'report_type': 'pdf',
					'form':data
				},
			'nodestroy': False
			}	
	
	
kg_fettling_invoice_print()

