
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
	
class gate_pass_register_wizard(osv.osv_memory):
		
	_name = 'gate.pass.register.wizard'
	_columns = {
		
		'dep_id':fields.many2many('kg.depmaster','gate_pass_register','wiz_id','dep_id','Department Name'),
		'filter': fields.selection([('filter_no', 'No Filters'), ('filter_date', 'Date')], "Filter by", required=True),
		'product_type': fields.selection([('consu', 'Consumable Items'),('cap','Capital Goods'),('service','Service Items')], 'Product Type'),				
		'date_from': fields.date("Start Date"),
		'date_to': fields.date("End Date"),
		'product':fields.many2many('product.product','gate_pass_product','product_wiz_id','product_dep_id','Product'),
		'company_id': fields.many2one('res.company', 'Company Name'),
		'print_date': fields.datetime('Creation Date', readonly=True),
		'printed_by': fields.many2one('res.users','Printed By',readonly=True),
		'status': fields.selection([('delivered', 'Delivered'),('cancelled','Cancelled'),('closed','Closed'),('pending','Pending')], "Status"),
		
	}
	
	_defaults = {
		
		'filter': 'filter_date', 
		'date_from': time.strftime('%Y-%m-%d'),
		'date_to': time.strftime('%Y-%m-%d'),
		'print_date': fields.datetime.now,
		'printed_by': lambda obj, cr, uid, context: uid,
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'gate.pass.register.wizard', context=c),
	}

	def _date_validation_check(self, cr, uid, ids, context=None):
		for val_date in self.browse(cr, uid, ids, context=context):
			if val_date.date_from <= val_date.date_to:
				return True
		return False
 
	_constraints = [
		(_date_validation_check, 'You must select an correct Start Date and End Date !!', ['Valid_date']),
	  ]
	  
	  
	def _build_contexts(self, cr, uid, ids, data, context=None):
		print "_build_contexts data ^^^^^^^^^^^^^^^^^^^^^^^^", data
		if context is None:
			context = {}
		result = {}
		result['date_from'] = 'date_from' in data['form'] and data['form']['date_from'] or False
		result['date_to'] = 'date_to' in data['form'] and data['form']['date_to'] or False
		if data['form']['filter'] == 'filter_date':
			result['date_from'] = data['form']['date_from']
			result['date_to'] = data['form']['date_to']
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
		if context is None:
			context = {}
		data = self.pre_print_report(cr, uid, ids, data, context=context)
		print "data..................,,,,,,,,,,,,,,", data
		data['form'].update(self.read(cr, uid, ids[0]))
		if data['form']:
			date_from = str(data['form']['date_from'])
			date_to = str(data['form']['date_to'])
			data['form']['date_from_ind'] = self.date_indian_format(date_from)			
			data['form']['date_to_ind'] = self.date_indian_format(date_to)
			
			company_id = data['form']['company_id'][0]
			com_rec = self.pool.get('res.company').browse(cr,uid, company_id)			
			data['form']['company'] = com_rec.name
			data['form']['printed_by'] = rec.printed_by.name
			
			if data['form']['status'] == 'delivered':
				data['form']['status_name'] = 'Delivered'
			
			elif data['form']['status'] == 'cancelled':
				data['form']['status_name'] = 'Cancelled'
				
			elif data['form']['status'] == 'pending':
				data['form']['status_name'] = 'Pending'
			
			elif data['form']['status'] == 'closed':
				data['form']['status_name'] = 'Closed'
			else:
				data['form']['status_name'] = ''
				
			cr_date = datetime.strptime(rec.print_date, '%Y-%m-%d %H:%M:%S')
			date = cr_date.strftime('%d/%m/%Y %H:%M:%S')	
			data['form']['print_date'] = date		
			return {'type': 'ir.actions.report.xml', 'report_name': 'gate.pass.register', 'datas': data,  'name': 'Gate Pass Register'}	
		

gate_pass_register_wizard()

