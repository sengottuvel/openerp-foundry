from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

dt_time = lambda * a: time.strftime('%m/%d/%Y %H:%M:%S')


class kg_foundry_stock(osv.osv):

	_name = "kg.foundry.stock"
	_description = "Foundry Stock"
	
	def _get_default_division(self, cr, uid, context=None):
		res = self.pool.get('kg.division.master').search(cr, uid, [('code','=','SAM'),('state','=','approved'), ('active','=','t')], context=context)
		return res and res[0] or False
	
	_columns = {
	
		'company_id': fields.many2one('res.company', 'Company Name'),
		'division_id': fields.many2one('kg.division.master','Division'),
		'stock_inward_id': fields.many2one('ch.stock.inward.details','Stock Inward Line'),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location'),
		'stage_id': fields.many2one('kg.stage.master','Stage Master'),
		'remarks': fields.text('Remarks'),
		'bom_id': fields.many2one('kg.bom', 'BOM Id'),
		'bom_line_id': fields.many2one('ch.bom.line','BOM Line Id'),
		'sch_bomline_id': fields.many2one('ch.order.bom.details','Schedule BOM Line Id'),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'qty': fields.integer('Qty'),
		'alloc_qty': fields.integer('Allocation Qty'),
		'type': fields.char('Type', size=5),
		'order_id': fields.many2one('kg.work.order','Work Order'),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line'),
		'schedule_id': fields.many2one('kg.schedule','Schedule'),
		'schedule_line_id': fields.many2one('ch.schedule.details','Schedule Line Item'),
		'allocation_id': fields.many2one('ch.stock.allocation.detail','Allocation'),
		'qc_id': fields.many2one('kg.qc.verification','QC'),
		'production_id': fields.many2one('kg.production','Production'),
		'pouring_id': fields.many2one('kg.pouring.log','Pouring Log'),
		'pouring_line_id': fields.many2one('ch.pouring.details','Pouring Lines'),
		'creation_date': fields.date('Creation Date'),
		'schedule_date': fields.date('Schedule Date'),
		'planning_date': fields.date('Planning Date'),
		'allocation_date': fields.date('Allocation Date'),
		'qc_date': fields.date('Qc Date'),
		'production_date': fields.date('Production Date'),
		'unit_price': fields.float('Unit Price'),
		
		
	
	}
	
	
	_defaults = {
		
		'creation_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_foundry_stock', context=c),
		'division_id':_get_default_division,
		
	}
	
	
kg_foundry_stock()











