import math
import re
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import openerp.addons.decimal_precision as dp


class kg_physical_stock(osv.osv):

	_name = "kg.physical.stock"
	_description = "KG Issue Return"
	_order = "date desc"

	
	_columns = {
	
		'name': fields.char('Issue Return No', size=64, readonly=True),
		'date': fields.date('Issue Return Date',readonly=True,states={'draft':[('readonly',False)]}),
		'stock_line': fields.one2many('kg.physical.stock.line', 'stock_pid',
					'Physical Stock Lines',readonly=True,states={'draft':[('readonly',False)]}),
		'active': fields.boolean('Active'),
		'load': fields.boolean('Load'),
		'user_id' : fields.many2one('res.users', 'Created By', readonly=True),
		'state': fields.selection([('load','Load'),('draft', 'Draft'),('confirm','Waiting For Approval'),('approved','Approved'),('cancel','Cancel')], 'Status', track_visibility='onchange',states={'draft':[('readonly',False)]}),
		'creation_date':fields.datetime('Creation Date',readonly=True),
		'remark': fields.text('Remarks',states={'cancel':[('readonly',True)]}),
		
		'confirmed_by' : fields.many2one('res.users', 'Confirmed By', readonly=False,select=True),
		'approved_by' : fields.many2one('res.users', 'Approved By', readonly=False,select=True),
		'company_id':fields.many2one('res.company','Company'),
		'stock_type': fields.selection([('main','Main'),('sale', 'Sale')], 'Stock Type',readonly=True),
		
	}
	
	_sql_constraints = [('code_uniq','unique(name)', 'Indent number must be unique!')]

	_defaults = {
		
		'state' : 'load',
		'active' : 'True',
		'load' : True,
		'date' : fields.date.context_today,
		'user_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'company_id' : lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.general.grn', context=c),

	}
	
	
	def load_stock(self, cr, uid, ids = 0,context=None):
		#rec  = self.browse(cr,uid,ids[0])
		sql = """delete from kg_physical_stock where state='load'"""
		cr.execute(sql)		
				
		"""
		draft_amends=self.search(cr,uid,[('date','=',rec.date)])
		if len(draft_amends) > 1:
			raise osv.except_osv(
				_('Physical stock has been already done'),
				_('for this Date')) 
		"""
		
		vals={
			'stock_type':'main',
			'state':'draft',
			
			}
		
		stock = self.pool.get('kg.physical.stock').create(cr,uid,vals,context=None)		
		sql="""SELECT 
				distinct spl.product_id as in_pro_id,
				brand.name as brand,
				spl.product_uom as uom,
				pp.type as purpose,
				pp.name_template as product,
				sum(pending_qty) as in_qty

				FROM stock_production_lot spl

				left JOIN product_product pp ON (pp.id=spl.product_id)
				left JOIN kg_brand_master brand ON (brand.id=spl.brand_id)


				where spl.pending_qty > 0 and spl.lot_type = 'in'


				group by spl.product_id,brand.name,spl.product_uom,pp.type,pp.name_template """
		cr.execute(sql)
		data = cr.dictfetchall()		
		data.sort(key=lambda data: data['product'])
		
		for item in data:
		
			line_vals = {
			'product_id':item['in_pro_id'],
			'brand':item['brand'] or '',
			'uom':item['uom'],
			'qty':item['in_qty'],
			'physical_stock':item['in_qty'],
			'stock_pid':stock,
			
			}
			if line_vals:
				common_line = self.pool.get('kg.physical.stock.line').create(cr,uid,line_vals,context=None)
				
		#self.write(cr,uid,ids[0],{'state':'draft'})		
		return True	


	def load_sale_stock(self, cr, uid, ids,context=None):
		#rec  = self.browse(cr,uid,ids[0])
		sql = """delete from kg_physical_stock where state='load'"""
		cr.execute(sql)		
				
		"""
		draft_amends=self.search(cr,uid,[('date','=',rec.date)])
		if len(draft_amends) > 1:
			raise osv.except_osv(
				_('Physical stock has been already done'),
				_('for this Date')) 
				
				
		"""		
		
		vals={
			'stock_type':'sale',
			'state':'draft',
			
			}
		
		stock = self.pool.get('kg.physical.stock').create(cr,uid,vals,context=None)	
		

		
		sql="""select a_product_id,
				
				pp.name_template as product,
				uom.id as uom,
				bm.name as brand,
				CASE WHEN (a_prod_qty - b_prod_qty) is NULL THEN (round(a_prod_qty::numeric, 2)) ELSE (round((a_prod_qty - b_prod_qty)::numeric, 2)) END as close_qty
				
				
				
				 from

				(select a.product_id as a_product_id,a.product_uom as a_uom,sum(a.product_qty) as a_prod_qty,a.location_dest_id as a_location,
				a.brand_id as a_brand 
				from stock_move a where a.move_type='out' and a.state='done'
				group by a.product_id,a.location_dest_id,a.product_uom,a.brand_id) as query1
				left outer join
				(select b_product_id,b_prod_qty from
				(select b.product_id as b_product_id,sum(b.product_qty) as b_prod_qty
				from stock_move b where b.move_type='cons' and b.state='done'
				group by b.product_id ) as query2) as query2 on query2.b_product_id = query1.a_product_id
				left join stock_location loc on (loc.id = query1.a_location)
				left join product_product pp on (pp.id = query1.a_product_id)
				left join kg_brand_master bm on (bm.id = query1.a_brand)
				left join product_uom uom on (uom.id = query1.a_uom)
				where loc.name = 'Sales location'"""
		cr.execute(sql)
		data = cr.dictfetchall()		
		data.sort(key=lambda data: data['product'])
		
		for item in data:
		
			line_vals = {
			'product_id':item['a_product_id'],
			'brand':item['brand'] or '',
			'uom':item['uom'],
			'qty':item['close_qty'],
			'physical_stock':item['close_qty'],
			'stock_pid':stock,
			
			}
			if line_vals:
				common_line = self.pool.get('kg.physical.stock.line').create(cr,uid,line_vals,context=None)
				
		#self.write(cr,uid,ids[0],{'state':'draft'})		
		return True	


		
	def confirm_stock(self, cr, uid, ids,context=None):
		rec  = self.browse(cr,uid,ids[0])
		if not rec.stock_line:
			raise osv.except_osv(
				_('Warning'),
				_('Line item cannot be empty'))
		self.write(cr,uid,ids,{
			'name':self.pool.get('ir.sequence').get(cr, uid, 'kg.physical.stock') or False,
			'state': 'confirm',
			'confirmed_by':uid
			})	
		return True
	
	def approve_stock(self, cr, uid, ids,context=None):
		obj = self.browse(cr,uid,ids[0])
		#print "obj.dep_name.reject_location.id",obj.dep_name.reject_location.id

		self.write(cr,uid,ids,{'state':'approved','approved_by':uid})
		return True
	
	def cancel_stock(self, cr, uid, ids, context=None):
		rec  = self.browse(cr,uid,ids[0])
		if rec.remark == None or rec.remark == False:
			raise osv.except_osv(_('Invalid action !'), _('Enter remarks to cancel!!'))

		self.write(cr, uid,ids,{'state' : 'cancel'})
		return True

	def unlink(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		indent = self.read(cr, uid, ids, ['state'], context=context)
		unlink_ids = []
		for t in indent:
			if t['state'] in ('draft'):
				unlink_ids.append(t['id'])
			else:
				raise osv.except_osv(_('Invalid action !'), _('System not allow to delete a UN-DRAFT state Department Indent!!'))
		indent_lines_to_del = self.pool.get('kg.physical.stock.line').search(cr, uid, [('stock_line','in',unlink_ids)])
		self.pool.get('kg.physical.stock.line').unlink(cr, uid, indent_lines_to_del)
		osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		return True
		
	def _check_lineitem(self, cr, uid, ids, context=None):
		for si in self.browse(cr,uid,ids):
			if si.issue_return_line==[] or si.issue_return_line:
					tot = 0.0
					for line in si.issue_return_line:
						tot += line.qty
					if tot <= 0.0:			
						return False
						
			return True
	
	#_constraints = [
	
		#(_check_lineitem, 'You can not save this Service Indent with out Line and Zero Qty  !!',['qty']),

		#]	

kg_physical_stock()

class kg_physical_stock_line(osv.osv):
	
	_name = "kg.physical.stock.line"
	_description = "Issue Return Line"

	def onchange_product_id(self, cr, uid, ids, product_id, uom,context=None):
			
		value = {'uom': ''}
		if product_id:
			prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			value = {'uom': prod.uom_id.id}

		return {'value': value}
		
	
	
	_columns = {

	'stock_pid': fields.many2one('kg.physical.stock', 'Stock No', required=True, ondelete='cascade'),
	'product_id': fields.many2one('product.product', 'Product', required=False),
	'uom': fields.many2one('product.uom', 'UOM', required=False),
	#'brand_id': fields.many2one('kg.brand.master', 'Brand', required=True),
	'brand': fields.char('Brand', required=True),
	'qty': fields.float('Current Stock', required=True),
	'physical_stock':fields.float('Physical Stock Qty'),
	'diff_qty':fields.float('Diff Qty'),
	'note': fields.text('Remarks'),	
	'line_state': fields.selection([('process','Processing'),('noprocess','NoProcess'),('pi_done','PI-Done'),('done','Done')], 'Status'),
	'line_date': fields.date('Indent Date'),
	'price_unit':fields.float('Unit Price'),
	
	}
	
	_defaults = {

		'line_date' : fields.date.context_today,
		
	}

kg_physical_stock_line()	
