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

class kg_drawing_sc_print(osv.osv_memory):
	_name = "kg.drawing.sc.print"
	_description = "Drawing SC Details"
	
	_columns = {
		
		## Basic Info
		'as_on_date': fields.date("As On Date",required=True),			
		'company_id': fields.many2one('res.company', 'Company'),
		'print_date': fields.datetime('print Date', readonly=True),
		'printed_by': fields.many2one('res.users','Printed By',readonly=True),  
		
		## If any filter it should be many2many only. Don't use many2one filter unless it's must	
		'contractor_id': fields.many2many('res.partner', 'm2m_drawing_sc_details', 'drawing_wiz_id', 'contractor_id','Contractor Name', domain="[('contractor','=','t')]"),
		
	}
	
		
	_defaults = {
		'as_on_date': time.strftime('%Y-%m-%d'),		
		'print_date': time.strftime('%Y-%m-%d %H:%M:%S'),
		'printed_by': lambda obj, cr, uid, context: uid,		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.drawing.sc.print', context=c),
	 }
	
	
	
	def create_report(self, cr, uid, ids, context={}):	
	
		rec = self.browse(cr,uid,ids[0])	
		data = self.read(cr,uid,ids,)[-1]		
		print data,' create_report('
		return {
			'type'		 : 'ir.actions.report.xml',
			'report_name'   : 'jasper_drawing_sc_report',
			'datas': {
					'model':'kg.drawing.sc.print',
					'id': context.get('active_ids') and context.get('active_ids')[0] or False,
					'ids': context.get('active_ids') and context.get('active_ids') or [],
					'report_type': 'pdf',
					'form':data
				},
			'nodestroy': False
			}	
	
	
kg_drawing_sc_print()

