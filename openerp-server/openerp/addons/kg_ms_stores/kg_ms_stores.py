from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

ORDER_PRIORITY = [
   ('1','MS NC'),
   ('2','NC'),
   ('3','Service'),
   ('4','Emergency'),
   ('5','Spare'),
   ('6','Normal'),
  
]


ORDER_CATEGORY = [
   ('pump','Pump'),
   ('spare','Spare'),
   ('pump_spare','Pump and Spare'),
   ('service','Service'),
   ('project','Project')
]


class kg_ms_stores(osv.osv):

	_name = "kg.ms.stores"
	_description = "MS Stores Process"
	_order = "entry_date desc"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('MS Store No', size=128,select=True,readonly=True),
		'entry_date': fields.date('MS Store Date',required=True),
		'note': fields.text('Notes'),
		'remarks': fields.text('Remarks'),
		'active': fields.boolean('Active'),
		
		'operation_id': fields.many2one('kg.ms.operations','MS Operation Id'),
		'ms_id': fields.related('operation_id','ms_id', type='many2one', relation='kg.machineshop', string='MS Id', store=True, readonly=True),
		'production_id': fields.related('operation_id','production_id', type='many2one', relation='kg.production', string='Production No.', store=True, readonly=True),
		'ms_plan_id': fields.related('operation_id','ms_plan_id', type='many2one', relation='kg.ms.daily.planning', string='Planning Id', store=True, readonly=True),
		'ms_plan_line_id': fields.related('operation_id','ms_plan_line_id', type='many2one', relation='ch.ms.daily.planning.details', string='Planning Line Id', store=True, readonly=True),
		'position_id': fields.related('operation_id','position_id', type='many2one', relation='kg.position.number', string='Position No.', store=True, readonly=True),
		'order_id': fields.related('operation_id','order_id', type='many2one', relation='kg.work.order', string='Work Order', store=True, readonly=True),
		'order_line_id': fields.related('operation_id','order_line_id', type='many2one', relation='ch.work.order.details', string='Order Line', store=True, readonly=True),
		'order_no': fields.related('operation_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		
		'order_category': fields.related('operation_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.related('operation_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		'pump_model_id': fields.related('operation_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('operation_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_code': fields.related('operation_id','pattern_code', type='char', string='Pattern Code', store=True, readonly=True),
		'pattern_name': fields.related('operation_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'item_code': fields.related('operation_id','item_code', type='char', string='Item Code', store=True, readonly=True),
		'item_name': fields.related('operation_id','item_name', type='char', string='Item Name', store=True, readonly=True),
		'moc_id': fields.related('operation_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'ms_type': fields.related('operation_id','ms_type', type='selection', selection=[('foundry_item','Foundry Item'),('ms_item','MS Item')], string='Item Type', store=True, readonly=True),
		'qty': fields.integer('Qty'),
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),		
		
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_schedule', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		entry_date = rec.entry_date
		entry_date = str(entry_date)
		entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
		if entry_date > today:
			return False
		return True
	
	_constraints = [		
			  
		
		#~ (_future_entry_date_check, 'System not allow to save with future date. !!',['']),   
		
	   ]
	   
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_ms_stores, self).write(cr, uid, ids, vals, context)
		
kg_ms_stores()
