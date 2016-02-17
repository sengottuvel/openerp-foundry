import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
from lxml import etree
from osv import fields, osv
from tools.translate import _
import pooler
import logging
import netsvc
logger = logging.getLogger('server')
	
class closing_stock_wizard(osv.osv_memory):
		
	_name = 'closing.stock.wizard'
	_columns = {
		
		'filter': fields.selection([('filter_date', 'Date')], "Filter by", required=True),
		'date': fields.date("Date"),
		'location_dest_id': fields.many2one('stock.location', 'Stores', required=False, domain="[('location_type','=', 'sub')]"),
		'major_name':fields.many2one('product.category', 'Product Category'),
		'product':fields.many2many('product.product','close_stock_product','stock_product_id','close_stock_id','Product', domain="[('state','=','approved'),'&',('sale_ok','=',True)]"),
		'product_type': fields.selection([('consu', 'Consumable Items'),('cap','Capital Goods'),('service','Service Items')], 'Product Type'),
		'print_date': fields.datetime('Creation Date', readonly=True),
		'printed_by': fields.many2one('res.users','Printed By',readonly=True),
		'company_id': fields.many2one('res.company', 'Company Name'),
	}
	
	_defaults = {
		
		'filter': 'filter_date', 
		'date': time.strftime('%Y-%m-%d'),
		'print_date': fields.datetime.now,
		'printed_by': lambda obj, cr, uid, context: uid,
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.pi.detail.wizard', context=c),

	}
 
 
	def _build_contexts(self, cr, uid, ids, data, context=None):
		if context is None:
			context = {}
		result = {}
		result['date'] = 'date' in data['form'] and data['form']['date'] or False
		if data['form']['filter'] == 'filter_date':
			result['date'] = data['form']['date']
		return result
		
	def date_indian_format(self,date_pyformat):
		date_contents = date_pyformat.split("-")
		date_indian = date_contents[2]+"/"+date_contents[1]+"/"+date_contents[0]
		return date_indian
	  
	def check_report(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		data = {}
		data['ids'] = context.get('active_ids', [])
		data['model'] = context.get('active_model', 'ir.ui.menu')
		data['form'] = self.read(cr, uid, ids, [])[0]
		used_context = self._build_contexts(cr, uid, ids, data, context=context)
		data['form']['used_context'] = used_context
		return self._print_report(cr, uid, ids, data, context=context)
		
	def pre_print_report(self, cr, uid, ids, data, context=None):
		if context is None:
			context = {}
		data['form'].update(self.read(cr, uid, ids, [], context=context)[0])
		return data
		
	def _print_report(self, cr, uid, ids, data, context=None):
		rec = self.browse(cr,uid,ids[0])
		today = time.strftime('%Y-%m-%d')
		
		trans_date = rec.date
		trans_date = str(trans_date)
		trans_date = datetime.strptime(trans_date, '%Y-%m-%d')
		trans_date = datetime.strftime(trans_date, '%Y-%m-%d')
		if trans_date > today:
			raise osv.except_osv(
                    _('Warning'),
                    _('System will not allow future date'))
		if context is None:
			context = {}
		data = self.pre_print_report(cr, uid, ids, data, context=context)
		data['form'].update(self.read(cr, uid, ids[0]))
		if data['form']:
			date = str(data['form']['date'])
			data['form']['date_from_ind'] = self.date_indian_format(date)
			
			data['form']['location']='Sales Location'
			
			company_id = data['form']['company_id'][0]
			com_rec = self.pool.get('res.company').browse(cr,uid, company_id)			
			data['form']['company'] = com_rec.name
                        data['form']['company_logo'] = com_rec.logo
			data['form']['printed_by'] = rec.printed_by.name
			
			if data['form']['major_name']:
				stores = data['form']['major_name']
				major_rec=self.pool.get('product.category').browse(cr,uid,stores[0])
				major=major_rec.id.name
				data['form']['category']=major
			
			return {'type': 'ir.actions.report.xml', 'report_name': 'closing.stock.wizard', 'datas': data,  'name': 'Closing Stock'}	
		

closing_stock_wizard()

