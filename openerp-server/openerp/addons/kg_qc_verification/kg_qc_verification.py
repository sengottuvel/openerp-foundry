from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

ORDER_PRIORITY = [
   ('normal','Normal'),
   ('emergency','Emergency')
]

ORDER_CATEGORY = [
   ('pump','Pump'),
   ('spare','Spare'),
   ('pump_spare','Pump and Spare'),
   ('service','Service'),
   ('project','Project')
]


class kg_qc_verification(osv.osv):

	_name = "kg.qc.verification"
	_description = "QC Verification"
	_order = "entry_date desc"
	
	def _get_each_weight(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		wgt = 0.00
		
		for entry in self.browse(cr, uid, ids, context=context):
			
			if entry.moc_id.weight_type == 'ci':
				wgt = entry.pattern_id.ci_weight
			if entry.moc_id.weight_type == 'ss':
				wgt = entry.pattern_id.pcs_weight
			if entry.moc_id.weight_type == 'non_ferrous':
				wgt = entry.pattern_id.nonferous_weight
				
		result[entry.id]= wgt
		
		return result
		
	def _get_total_weight(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		total_weight = 0.00
		for entry in self.browse(cr, uid, ids, context=context):
			total_weight = entry.qty * entry.each_weight		
		result[entry.id]= total_weight
		return result
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('QC No', size=128,select=True,readonly=True),
		'entry_date': fields.date('QC Date',required=True),
		'schedule_id': fields.many2one('kg.schedule','Schedule No.'),
		'schedule_date': fields.related('schedule_id','entry_date', type='date', string='Schedule Date', store=True, readonly=True),
		'division_id': fields.many2one('kg.division.master','Division'),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location'),
		'remark': fields.text('Remarks'),
		
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled'),('reject','Rejected')],'Status', readonly=True),
		'schedule_line_id': fields.many2one('ch.schedule.details','Schedule Line Item'),
		'allocation_id': fields.many2one('ch.stock.allocation.detail','Allocation'),
		'order_id': fields.many2one('kg.work.order','Work Order No.'),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line'),
		
		
		'bom_id': fields.related('schedule_line_id','bom_id', type='many2one', relation='kg.bom', string='BOM Id', store=True, readonly=True),
		'bom_line_id': fields.related('schedule_line_id','bom_line_id', type='many2one', relation='ch.bom.line', string='BOM Line Id', store=True, readonly=True),
		'order_bomline_id': fields.related('schedule_line_id','order_bomline_id', type='many2one', relation='ch.order.bom.details', string='Schedule BOM Line Id', store=True, readonly=True),
		
		'order_no': fields.related('order_line_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_priority': fields.related('order_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		'order_category': fields.related('order_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),

		
		'pump_model_id': fields.related('schedule_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('schedule_line_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern No.', store=True, readonly=True),
		'pattern_name': fields.related('pattern_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('order_bomline_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		
		'stage_id': fields.many2one('kg.stage.master','Stage', readonly=True),
		
		'stock_qty': fields.related('schedule_line_id','stock_qty', type='integer', string='Stock Qty', store=True, readonly=True),
		'allocated_qty': fields.integer('Allocated Qty',readonly=True),
		'qty': fields.integer('Qty', required=True),
		'rework_qty': fields.integer('Rework Qty'),
		'reject_qty': fields.integer('Rejection Qty'),
		'position_no': fields.char('Pos No.'),
		'diameter': fields.char('Diameter'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'reject_remark': fields.text('Rejection Remarks'),
		'each_weight': fields.function(_get_each_weight, string='Each Weight(Kgs)', method=True, store=True, type='float'),
		'total_weight': fields.function(_get_total_weight, string='Total Weight(Kgs)', method=True, store=True, type='float'),
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		
		'reject_date': fields.datetime('Rejected Date', readonly=True),
		'reject_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),		
		
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_qc_verification', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',	
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
		if entry_date > today or entry_date < today:
			return False
		return True
		
		
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty < 0:
			return False
		return True
		
	
	_constraints = [        
              
        
        (_future_entry_date_check, 'System not allow to save with future date or Past Date. !!',['']),
        (_check_values, 'System not allow to save less than zero qty .!!',['Quantity']),
       
        
       ]
       

	def entry_confirm(self,cr,uid,ids,context=None):
		"""
		production_obj = self.pool.get('kg.production')
		schedule_line_obj = self.pool.get('ch.weekly.schedule.details')
		planning_line_obj = self.pool.get('ch.daily.planning.details')
		sch_bomline_obj = self.pool.get('ch.sch.bom.details')
		pouring_obj = self.pool.get('ch.boring.details')
		casting_obj = self.pool.get('ch.casting.details')
		entry = self.browse(cr,uid,ids[0])
			
		if entry.qty > entry.allocated_qty:
			raise osv.except_osv(_('Warning !'), _('Accepted Qty should not be greater than Allocated Qty !!'))
		if entry.qty < 0:
			raise osv.except_osv(_('Warning !'), _('QC Qty should not be less than zero !!'))
			
		
		
		### Rejection Qty Updation
		
		reject_qty = entry.allocated_qty - (entry.qty + entry.rework_qty)
		
		self.write(cr, uid, ids, {'cancel_remark':False, 'reject_qty':reject_qty or 0})
		
		### Creating Prroduction When Rejection
		
		if reject_qty > 0:
		
			production_vals = {
												
				'name': self.pool.get('ir.sequence').get(cr, uid, 'kg.production') or '/',
				'planning_id': entry.planning_id.id,
				'planning_date': entry.planning_id.entry_date,
				'division_id': entry.division_id.id,
				'location' : entry.location,
				'planning_line_id': entry.planning_line_id.id,
				'schedule_id': entry.schedule_id.id,
				'schedule_line_id': entry.schedule_line_id.id,
				'qc_id': entry.id,
				'production_qty': reject_qty,
				'bal_produc_qty': reject_qty,
				'qty' : 0,	
				'excess_qty' : 0,
				'production_type':'nc',
				'state' : 'draft',
				'order_type':entry.order_type,
				'pattern_id' : entry.planning_line_id.pattern_id.id,
				'pattern_name' : entry.planning_line_id.pattern_id.pattern_name,
								
			}
			
		
			production_id = production_obj.create(cr, uid, production_vals)
				
			sch_bomline_obj.write(cr, uid, entry.sch_bomline_id.id, {'transac_state':'sent_for_produc'})
			
			schedule_line_obj.write(cr, uid, entry.schedule_line_id.id, {'transac_state':'sent_for_produc'})
			
			planning_line_obj.write(cr, uid, entry.planning_line_id.id, {'transac_state':'sent_for_produc'})
		
		#### Stock Table Updatation Block ####
		
		cr.execute(''' select qty,allocation_id from kg_qc_verification where planning_line_id = %s
		''',[entry.planning_line_id.id])
		stock_qc_qty = cr.dictfetchall()
		
		for stock_item in stock_qc_qty:
			

			cr.execute(''' update kg_foundry_stock set 
					qty = %s,qc_id = %s
					where allocation_id = (
					select allocation_id from kg_foundry_stock 
					where 
					schedule_id = %s and 
					schedule_line_id = %s and 
					planning_id = %s and
					planning_line_id = %s and
					allocation_id = %s and
					sch_bomline_id = %s and
					type = 'OUT' and
					alloc_qty > 0)
					''',
					[stock_item['qty'], entry.id, entry.schedule_id.id, entry.schedule_line_id.id, 
					entry.planning_id.id, entry.planning_line_id.id, stock_item['allocation_id'],entry.sch_bomline_id.id])
		"""
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		
		return True
		
	def entry_cancel(self,cr,uid,ids,context=None):
		planning_line_obj = self.pool.get('ch.daily.planning.details')
		entry = self.browse(cr,uid,ids[0])
		if entry.cancel_remark == False:
			raise osv.except_osv(_('Warning!'),
						_('Cancellation Remarks is must !!'))
		cr.execute(''' update kg_foundry_stock set qty = 0 where planning_line_id = %s and allocation_id = %s ''',[entry.planning_line_id.id, entry.allocation_id.id])
		self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True	
		
	def entry_draft(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		self.write(cr, uid, ids, {'state': 'draft'})
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):		
			raise osv.except_osv(_('Warning!'),
					_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_qc_verification, self).write(cr, uid, ids, vals, context)
	
	
kg_qc_verification()









