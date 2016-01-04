from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')


class kg_production(osv.osv):

	_name = "kg.production"
	_description = "Production Updation"
	_order = "entry_date desc"
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Production No', size=128,select=True,readonly=True),
		'entry_date': fields.date('Production Date',required=True),
		'planning_id': fields.many2one('kg.daily.planning','Planning No.'),
		'planning_date': fields.related('planning_id','entry_date', type='date', string='Planning Date', store=True, readonly=True),
		'division_id': fields.many2one('kg.division.master','Division'),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location'),
		'note': fields.text('Notes'),
		'remarks': fields.text('Approve/Reject'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		
		'planning_line_id': fields.many2one('ch.daily.planning.details','Planning Line Item'),
		'schedule_id': fields.many2one('kg.weekly.schedule','Schedule Header'),
		'schedule_line_id': fields.many2one('ch.weekly.schedule.details','Schedule Line'),
		'allocation_id': fields.many2one('ch.stock.allocation.details','Allocation'),
		'qc_id': fields.many2one('kg.qc.verification','QC'),
		'order_ref_no': fields.related('schedule_line_id','order_ref_no', type='char', string='Order Reference', store=True, readonly=True),
		'pump_model_id': fields.related('schedule_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('schedule_line_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'part_name_id': fields.related('schedule_line_id','part_name_id', type='many2one', relation='product.product', string='Part Name', store=True, readonly=True),
		'type': fields.related('schedule_line_id','type', type='char', string='Purpose', store=True, readonly=True),
		'moc_id': fields.related('schedule_line_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		
		'stage_id': fields.many2one('kg.stage.master','Stage',domain="[('state','=','approved'), ('active','=','t')]"),
		'planning_qty': fields.related('planning_line_id','qty', type='float', size=100, string='Planning Qty', store=True, readonly=True),
		'production_qty': fields.float('Production Qty', size=100, required=True),
		'qty': fields.float('Produced Qty', size=100, required=True),
		'excess_qty': fields.float('Excess Qty', size=100, required=True),
		'cancel_remark': fields.text('Cancel Remarks'),
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),		
		
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_production', context=c),
		'entry_date' : fields.date.context_today,
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',		
		'active': True,
		
		
	}
	
	def onchange_excess_qty(self, cr, uid, ids, qty, production_qty):
		val = {}
		if qty > 0.00 and qty > production_qty:
			excess_qty = qty - production_qty
		else:
			excess_qty = 0.00
		val = {'excess_qty': excess_qty }	
		return {'value': val}
	
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
		
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty == 0.00:
			return False
		return True
		
			
	
	_constraints = [        
              
        
        (_future_entry_date_check, 'System not allow to save with future date. !!',['']),
         (_check_values, 'System not allow to save with zero qty .!!',['Quantity']),
       
        
       ]
       

	def entry_confirm(self,cr,uid,ids,context=None):
		schedule_line_obj = self.pool.get('ch.weekly.schedule.details')
		planning_line_obj = self.pool.get('ch.daily.planning.details')
		qc_obj = self.pool.get('kg.qc.verification')
		entry = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		### Validation and Qty Updation
			
		if entry.qty < entry.production_qty:
			raise osv.except_osv(_('Warning !'), _('Production Qty should not be less than Planning Qty !!'))
	
		
		### Production Qty Updation 
		production_qty = entry.qty
		
		sch_produc_qty = entry.schedule_line_id.production_qty + production_qty

		if entry.schedule_line_id.planning_qty == 0.00:
			schedule_line_obj.write(cr, uid, entry.schedule_line_id.id, 
		
			{
			
			'transac_state':'complete',
			'production_qty': sch_produc_qty,
			
			
			})
		if entry.schedule_line_id.planning_qty > 0.00:
			schedule_line_obj.write(cr, uid, entry.schedule_line_id.id, 
		
			{
			
			'transac_state':'partial',
			'production_qty': sch_produc_qty,
			
			
			})
			
			
			
		planning_line_obj.write(cr, uid, entry.planning_line_id.id, {'transac_state':'complete'})
		
		self.write(cr, uid, ids, {'cancel_remark': False})
		
		if entry.qc_id:
			qc_obj.write(cr, uid, entry.qc_id.id, {'transac_state':'complete'})
			
		
			
		#### Stock Updation Block Starts Here ###
		
		if entry.excess_qty > 0.00:
				
			cr.execute(''' insert into kg_foundry_stock(company_id,division_id,location,pump_model_id,pattern_id,part_name_id,
							moc_id,trans_type,qty,alloc_qty,type,schedule_id,schedule_line_id,planning_id,planning_line_id,
							allocation_id,qc_id,production_id ,creation_date,schedule_date,
							planning_date,qc_date,production_date,stage_id,remarks)
						
						values(%s,%s,%s,%s,%s,%s,%s,%s,%s,0.00,'IN',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
						''',[entry.company_id.id,entry.division_id.id or None,entry.location,entry.pump_model_id.id, entry.pattern_id.id,entry.part_name_id.id,
						entry.moc_id.id,entry.type,entry.excess_qty,entry.schedule_id.id,entry.schedule_line_id.id,
						entry.planning_id.id,entry.planning_line_id.id,entry.allocation_id.id or None, entry.qc_id.id or None,
						entry.id,today,entry.schedule_id.entry_date,
						entry.planning_id.entry_date,entry.qc_id.entry_date or None, entry.entry_date,entry.stage_id.id,entry.note ])
					
		#### Stock Updation Block Ends Here ###
			
				
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),
			'name' :self.pool.get('ir.sequence').get(cr, uid, 'kg.production') or '/'})
		
		
		return True
		
	def entry_cancel(self,cr,uid,ids,context=None):
		schedule_line_obj = self.pool.get('ch.weekly.schedule.details')
		planning_line_obj = self.pool.get('ch.daily.planning.details')
		qc_obj = self.pool.get('kg.qc.verification')
		entry = self.browse(cr,uid,ids[0])
		if entry.cancel_remark == False:
			raise osv.except_osv(_('Warning!'),
						_('Cancellation Remarks is must !!'))
		
		### 
		cr.execute(''' select id from ch_daily_planning_details where schedule_line_id = %s and id > %s and state = 'confirmed' ''',[entry.schedule_line_id.id,entry.planning_line_id.id])
		planning_id = cr.fetchone()
		if planning_id != None:
			if planning_id[0]:
				raise osv.except_osv(_('Warning!'),
						_('Production cannot be Cancelled!!'))
				
		### Updation in Stock Table
		cr.execute(''' delete from kg_foundry_stock where production_id = %s  ''',[entry.id])
		### Updation in Schedule Table
		production_qty = entry.schedule_line_id.production_qty - entry.qty
		cr.execute(''' update ch_weekly_schedule_details set production_qty = %s where id = %s and header_id = %s ''',[production_qty,entry.schedule_line_id.id, entry.schedule_id.id])
		
		### Updation in QC
		qc_obj.write(cr, uid, entry.qc_id.id, 
		
			{
			
			'cancel_remark':entry.cancel_remark
			
			})
		if entry.qc_id:
			qc_obj.entry_cancel(cr, uid, [entry.qc_id.id])
		### Updation in Planning
		planning_line_obj.write(cr, uid, entry.planning_line_id.id, 
		
			{
			
			'cancel_remark':entry.cancel_remark
			
			})
		planning_line_obj.entry_cancel(cr, uid, [entry.planning_line_id.id])
		
		
		self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S'),'transac_state':'cancel'})
		return True
		
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):				
			raise osv.except_osv(_('Warning!'),
					_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		entry = self.browse(cr,uid,ids[0])
		if vals.get('qty'):
			produced_qty = vals.get('qty')
			excess_qty = produced_qty - entry.production_qty
			vals.update({'excess_qty': excess_qty })	
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_production, self).write(cr, uid, ids, vals, context)
	
	
kg_production()











