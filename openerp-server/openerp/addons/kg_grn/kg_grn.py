from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
import logging
logger = logging.getLogger('server')

class kg_stock_move(osv.osv):
	
	_name = "stock.move"
	_inherit = "stock.move"
	_rec_name = "product_id"	
	
	_columns = {
	
	'name': fields.char('Description', select=True),
	'date': fields.date('Date'),
	'trans_date': fields.date('Trans Date'),
	'po_qty': fields.float('Pending Qty', readonly=True),
	'cons_qty': fields.float('Available Qty', readonly=True),
	'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'),
			required=False, states={'done':[('readonly', True)], 'cancel':[('readonly',True)], 'assigned':[('readonly',False)]}),
	'product_id': fields.many2one('product.product', 'Product', required=True, select=True, domain=[('type','<>','service')],
		readonly=True, states={'draft':[('readonly', False)]}),
	'product_uom': fields.many2one('product.uom', 'Unit of Measure',
		readonly=True, states={'draft':[('readonly', False)]}),
	'name': fields.char('Description', required=True, select=True,
		readonly=True, states={'draft':[('readonly', False)]}),
	'location_dest_id': fields.many2one('stock.location', 'Destination Location', required=True,
		readonly=True, states={'draft':[('readonly', False)]}, 
		select=True, help="Location where the system will stock the finished products."),
	'location_id': fields.many2one('stock.location', 'Source Location', required=True, select=True,
		readonly=True, states={'draft':[('readonly', False)]}),
	'po_to_stock_qty' : fields.float('Quantity'),
	'stock_uom': fields.many2one('product.uom', 'Stock UOM'),
	
	'state': fields.selection([('draft', 'Draft'),
								   ('cancel', 'Cancelled'),
								   ('confirmed', 'Waiting for Confirmation'),
								   ('assigned', 'Waiting for Approval'),
								   ('done', 'Done'),
								   ], 'Status', readonly=True, select=True),
	
	'move_type': fields.selection([('in', 'IN'),('out','out'),('cons','Cons'),('dummy','Dummy')], 'Move Type'),
	'depindent_line_id': fields.many2one('kg.depindent.line','Indent Line'),
	'notes': fields.text('Remarks'),
	'expiry_date': fields.text('Expiry Date'),
	'batch_no':fields.text('Batch No'),
	'kg_grn_moves': fields.many2many('stock.production.lot','kg_out_grn_lines','grn_id','lot_id', 'GRN Entry',
					domain="[('product_id','=',product_id), '&', ('pending_qty','>','0'), '&', ('lot_type','!=','out')]",
					readonly=True, states={'confirmed':[('readonly', False)],'assigned':[('readonly',False)]}),
	'expiry_flag': fields.boolean('Expiry'),
	'pi_id': fields.many2one('purchase.requisition.line', 'PI ID'),
	'gp_id': fields.many2one('kg.gate.pass', 'GP NO'),
	'gp_line_id': fields.many2one('kg.gate.pass.line', 'GP Line No'),
	'sa_id': fields.many2one('sale.order', 'Sale NO'),
	'sa_line_id': fields.many2one('sale.order.line', 'Sale Line'),
	'src_id': fields.many2one('stock.move', 'SRC'),
	'stock_rate':fields.float('Stock Rate'),
	'tax_id': fields.many2many('account.tax', 'purchase_order_taxxes', 'order_id', 'taxes_id', 'Taxes'),
	'kg_discount_per': fields.float('Discount (%)', digits_compute= dp.get_precision('Discount')),
	'kg_discount': fields.float('Discount Amount'),
	'exp_line_id':fields.one2many('kg.grn.exp.batch', 'grn_line_id','Expiry Batch Line'),
	'flag_opening':fields.boolean('Opening Flag'),
	'transaction_type':fields.char('Transaction Type'),
	'uom_conversation_factor': fields.selection([('one_dimension','One Dimension'),('two_dimension','Two Dimension')],'UOM Conversation Factor'),
	'length': fields.float('Length'),
	'breadth': fields.float('Breadth'),
	
	# General GRN Line
	
	'general_grn_id':fields.many2one('kg.general.grn.line', 'General GRN Line Id'),
	
	# PO GRN Line
	
	'po_grn_line_id':fields.many2one('po.grn.line','PO GRN Entry Line'),
	'po_grn_id':fields.many2one('kg.po.grn','PO GRN Entry'),
	'po_id':fields.many2one('purchase.order','Purchase Order'),
	'so_id':fields.many2one('kg.service.order','Service Order'),
	'so_line_id':fields.many2one('kg.service.order.line','Service Order Line'),
	'billing_type': fields.selection([('free', 'Free'), ('cost', 'Cost')], 'Billing Type'),
	'brand_id':fields.many2one('kg.brand.master','Brand Name'),
	'moc_id':fields.many2one('kg.moc.master','MOC Name'),
	
	# Store Issue
	
	'dept_issue_id':fields.many2one('kg.department.issue','Department Issue'),
	'dept_issue_line_id':fields.many2one('kg.department.issue.line','Department Issue Line'),
	
	# Stock Movements
	
	'stock_move_id': fields.many2one('kg.stock.movement','Stock Movement'),
	}
	
	_defaults = {
		
		'move_type': 'dummy',
		'flag_opening': False,
		'length': 1,
		'breadth': 1,
		
	}	  
			
				
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			raise osv.except_osv(_('Delete access denied !'), _('Unable to delete. Draft entry only you can delete !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
kg_stock_move()

class kg_stock_production_lot(osv.osv):
	
	_name = "stock.production.lot"
	_inherit="stock.production.lot"
	_order = 'date' 
	_rec_name = 'batch_no'   
		
	_columns = {
		
		'grn_move':fields.many2one('stock.move','GRN Move'),
		'grn_no':fields.char('GRN NO', char=128),
		'product_qty':fields.float('Quantity'),
		'po_product_qty':fields.float('Quantity'),
		'pending_qty':fields.float('PO UOM Pending Qty',digits=(16,4)),
		'store_pending_qty':fields.float('Store UOM Pending Qty',digits=(16,4)),
		'issue_qty':fields.float('Issued Qty'),
		'product_uom':fields.many2one('product.uom', 'UOM'),
		'expiry_date':fields.date('Expiry Date'),
		'trans_date':fields.date('Transaction Date'),
		'batch_no':fields.char('Batch No', size=128),
		'price_unit': fields.float('Unit Price'),
		'po_uom': fields.many2one('product.uom', 'PO UOM'),
		'po_qty': fields.float('PO Qty'),
		'user_id':fields.many2one('res.users','LOT User'),
		'grn_type': fields.selection([('material', 'Material'), ('service', 'Service')], 'GRN Type'),
		'brand_id': fields.many2one('kg.brand.master','Brand'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'reserved_qty': fields.float('Reserved Qty'),
		'reserved_qty_in_po_uom': fields.float('Reserved Qty'),
		'location_id': fields.many2one('stock.location','Location'),
		
	}
	
	def name_get(self, cr, uid, ids, context={}):
		if not len(ids):
			return []
		res=[]
		for emp in self.browse(cr, uid, ids,context=context):
			res.append((emp.id, emp.batch_no or ''))	   
		return res   
	
kg_stock_production_lot()

class kg_grn_exp_batch(osv.osv):
	
	_name = "kg.grn.exp.batch"
	_description = "Expiry Date and Batch NO"
	
	_columns = {
		
		'grn_line_id':fields.many2one('stock.move','Move Line'),
		'exp_date':fields.date('Expiry Date'),
		'batch_no':fields.char('Batch No'),
		'product_qty':fields.integer('Product Qty'),
		
	}
	
kg_grn_exp_batch()
