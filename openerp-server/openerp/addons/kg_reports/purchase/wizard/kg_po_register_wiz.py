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

class kg_po_register_wiz(osv.osv_memory):
	
	_name = 'kg.po.register.wiz'
	_columns = {
		
		'fis_year'  : fields.many2one('account.fiscalyear','Fiscal year',readonly=True),
		'product_id': fields.many2many('product.product','kg_po_stm_pro','order_id','product_id','Product Name',domain="[('state','in',('draft','confirm','approved'))]"),
		'supplier'  : fields.many2many('res.partner','kg_po_stm_sup','order_id','supplier_id','Supplier',domain="[('partner_state','not in',('cancel','reject')),('supplier','=',True)]"),
		'po_no'		: fields.many2many('purchase.order','kg_po_stm_pono','order_id','po_no_id','PO No',domain="[('state','!=','draft')]"),
		'filter'	: fields.selection([('filter_no', 'No Filters'), ('filter_date', 'Date')], "Filter by", required=True),
		'date_from'	: fields.date("Start Date"),
		'date_to'	: fields.date("End Date"),
		'division'	: fields.selection([('ppd','PPD'),('ipd','IPD'),('foundry','Foundry')],'Division'),
		'print_date': fields.datetime('Creation Date', readonly=True),
		'printed_by': fields.many2one('res.users','Printed By',readonly=True),
		'status'	: fields.selection([('confirmed','Confirmed'),('verified','Verified'),('approved', 'Approved'),('cancel','Cancelled'),('reject','Rejected')], "Status"),
		'company_id': fields.many2one('res.company', 'Company Name'),
		'user_id'	: fields.many2one('res.users', 'User ID'),
		
	}
	
	_defaults = {
		
		'filter'    : 'filter_date', 
		'date_from' : lambda * a: time.strftime('%Y-%m-%d'),
		'date_to'   : lambda * a: time.strftime('%Y-%m-%d'),
		'print_date': fields.datetime.now,
		'printed_by': lambda obj, cr, uid, context: uid,
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.po.register.wiz', context=c),
		'user_id'   : lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id,
		
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
	
	def create_report(self, cr, uid, ids, context={}):
		data = self.read(cr,uid,ids,)[-1]
		print data,' create_report('
		return {
			'type'		 : 'ir.actions.report.xml',
			'report_name': 'jasper_kg_po_register',
			'datas'		 : {
							'model':'kg.po.register.wiz',
							'id': context.get('active_ids') and context.get('active_ids')[0] or False,
							'ids': context.get('active_ids') and context.get('active_ids') or [],
							'report_type':'pdf',
							'form':data
							},
			'nodestroy'  : False
			}
	
	def _enddate_check(self,cr,uid,ids,context=None):
		rec=self.browse(cr,uid,ids[0])
		if rec.date_to < rec.date_from:
			raise osv.except_osv(_('Warning!'),_('End Date is lesser than Start Date!!'))
		return True
	
	_constraints = [
					
					(_enddate_check, 'End Date is lesser than Start Date!!', ['']),
					
					]
	
kg_po_register_wiz()
