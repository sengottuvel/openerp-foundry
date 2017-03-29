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
today = date.today()

class kg_vendor_profile_wiz(osv.osv_memory):
	
	_name = 'kg.vendor.profile.wiz'
	
	_columns = {
		
		## Basic Info
		
		'to_date': fields.date("As on Date", required=True),
		'crt_date': fields.datetime('Creation Date', readonly=True),
		'user_id': fields.many2one('res.users', 'Created By',readonly=True),		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),		
		'flag_footer': fields.boolean('Footer Info', helps='If False footer details should not print'),
		
		## If any filter it should be many2many only. Don't use many2one filter unless it's must	
		'supplier_id': fields.many2many('res.partner','m2m_res_partners','wiz_id','supplier_id', 'Vendor',domain="[('supplier','=','t')]"),
		
	}
	
	_defaults = {
		
		'to_date': lambda * a: time.strftime('%Y-%m-%d'),
		'crt_date': time.strftime('%Y-%m-%d %H:%M:%S'),
		'user_id': lambda obj, cr, uid, context: uid,
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.vendor.profile.wiz', context=c),
		'flag_footer': True,
	}
	
	def _future_date_validation(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if  rec.to_date > str(today):
			raise osv.except_osv('Invalid Action', 'Future Dates are not allowed')  
		return True
	
	def create_report(self, cr, uid, ids, context={}):
		data = self.read(cr,uid,ids,)[-1]
		return {
			'type'		 : 'ir.actions.report.xml',
			'report_name'   : 'jasper_kg_vendor_profile',
			'datas': {
					'model':'kg.vendor.profile.wiz',
					'id': context.get('active_ids') and context.get('active_ids')[0] or False,
					'ids': context.get('active_ids') and context.get('active_ids') or [],
					'report_type':'pdf',
					'form':data
				},
			'nodestroy': False
			}
	
	_constraints = [
		
		(_future_date_validation,'Future Dates are not allowed', ['']),
	  ]
	
kg_vendor_profile_wiz()
