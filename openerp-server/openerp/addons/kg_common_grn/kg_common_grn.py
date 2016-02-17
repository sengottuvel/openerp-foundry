from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import re
from operator import itemgetter
from itertools import groupby

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

class kg_common_grn(osv.osv):

	_name = "kg.common.grn"
	_description = "Common GRN"
	
	
	_columns = {
		
		'supplier_id':fields.many2one('res.partner','Supplier',domain=[('supplier','=',True)]),
		'active': fields.boolean("Active"),
		'state': fields.selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('done', 'Done'), ('cancel', 'Cancelled'),('inv','Invoiced')], 'Status',readonly=True),
		'line_ids' : fields.one2many('kg.common.grn.line','order_id','GRN',readonly=True),
		'payment_type': fields.selection([('cash', 'Cash'), ('credit', 'Credit')], 'Payment Type',required=False),
	}


	_defaults = {
		'active': True,
		
	}
		
	def load_grn(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		payment = []
		supplier = []
		where_sql = []
				
		if rec.supplier_id:
			
			supplier.append("gg.supplier_id = %s"%(rec.supplier_id.id))
				
		if rec.payment_type:
			
			payment.append("gg.payment_type ='%s'"%(rec.payment_type))
			
		
		if supplier:
			supplier = 'and ('+' or '.join(supplier)
			supplier =  supplier+')'
			
		else:
			supplier = ''
		
		if payment:
			payment = 'and ('+' or '.join(payment)
			payment =  payment+')'
		else:
			payment = ''			
		
		sql_delete = """delete from kg_common_grn_line"""
		cr.execute(sql_delete)
		
		sql="""select gg.name as grn_no,gg.grn_date as grn_date,gg.order_no as order_no,gg.order_date as order_date,
			ac.name as invoice_no,ac.date_invoice as invoice_date,
			gg.dc_no as dc_no,gg.dc_date as dc_date,
			gg.payment_type,
			gg.supplier_id as supplier,gg.remark as remark,gg.state as state
			from kg_general_grn gg 
			left join account_invoice ac on (ac.grn_id=gg.id)
			where gg.state != 'draft' """ + supplier + payment + """ 
			
			union
			
			select gg.name as grn_no,gg.grn_date as grn_date,gg.order_no as order_no,gg.order_date as order_date,
			ac.name as invoice_no,ac.date_invoice as invoice_date,
			gg.dc_no as dc_no,gg.dc_date as dc_date,
			gg.payment_type,
			gg.supplier_id as supplier,gg.po_so_remark as remark,gg.state as state
			from kg_po_grn gg 
			left join account_invoice ac on (ac.grn_id=gg.id)
			where gg.state != 'draft' """+ supplier + payment + """ """
		cr.execute(sql)
		data = cr.dictfetchall()
		data.sort(key=lambda data: data['grn_no'])
		
		for item in data:
		
			line_vals = {
			'grn_no':item['grn_no'],
			'grn_date':item['grn_date'],
			'order_no':item['order_no'],
			'order_date':item['order_date'],
			'dc_no':item['dc_no'],
			'dc_date':item['dc_date'],
			'payment_type':item['payment_type'],
			'supplier_id':item['supplier'],
			'note':item['remark'],
			'order_id':rec.id,
			'state':item['state']
			}
			if line_vals:
				common_line = self.pool.get('kg.common.grn.line').create(cr,uid,line_vals,context=None)
		return True		
		
		
		
kg_common_grn()

class kg_common_grn_line(osv.osv):
	
	_name = "kg.common.grn.line"
	
	
	_columns = {
	
	'order_id':fields.many2one('kg.common.grn','GRN'),
	'note': fields.text('Remarks'),
	'grn_date':fields.date('GRN Date'),
	'grn_no': fields.char('GRN No', size=64),
	'invoice_no': fields.char('Invoice No', size=64),
	'invoice_date':fields.date('Invoice Date'),
	'supplier_id':fields.many2one('res.partner','Supplier',domain=[('supplier','=',True)]),
	'state': fields.selection([('item_load','Draft'),('draft', 'Waiting for Confirmation'), ('confirmed', 'Waiting for Approval'), ('done', 'Done'), ('inv', 'Invoiced'), ('cancel', 'Cancelled')], 'Status'),
	'po_id':fields.many2one('purchase.order', 'PO NO',
					domain="[('state','=','approved'), '&', ('order_line.pending_qty','>','0'), '&', ('grn_flag','=',False), '&', ('partner_id','=',supplier_id), '&', ('order_line.line_state','!=','cancel')]"), 
	'po_date':fields.date('PO Date'),
	'dc_no': fields.char('DC NO'),
	'dc_date':fields.date('DC Date'),
	'order_no': fields.char('Order NO'),
	'order_date':fields.char('Order Date'),
	'payment_type': fields.selection([('cash', 'Cash'), ('credit', 'Credit')], 'Payment Type'),		
	}
	
	
kg_common_grn_line()

