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
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('boring_inprogress','Boring In Progress'),('boring_complete','Boring Complete')
				,('casting_inprogress','Casting In Progress'),('casting_complete','Casting Complete'),('cancel','Cancelled')],'Status', readonly=True),
		
		'planning_line_id': fields.many2one('ch.daily.planning.details','Planning Line Item'),
		
		'bom_id': fields.related('planning_line_id','bom_id', type='many2one', relation='kg.bom', string='BOM Id', store=True, readonly=True),
		'bom_line_id': fields.related('planning_line_id','bom_line_id', type='many2one', relation='ch.bom.line', string='BOM Line Id', store=True, readonly=True),
		'sch_bomline_id': fields.related('planning_line_id','sch_bomline_id', type='many2one', relation='ch.sch.bom.details', string='Schedule BOM Line Id', store=True, readonly=True),
		
		'schedule_id': fields.many2one('kg.weekly.schedule','Schedule Header'),
		'schedule_line_id': fields.many2one('ch.weekly.schedule.details','Schedule Line'),
		'allocation_id': fields.many2one('ch.stock.allocation.details','Allocation'),
		'qc_id': fields.many2one('kg.qc.verification','QC'),
		'order_ref_no': fields.related('schedule_line_id','order_ref_no', type='char', string='Order Reference', store=True, readonly=True),
		'pump_model_id': fields.related('schedule_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('planning_line_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		#'part_name_id': fields.related('schedule_line_id','part_name_id', type='many2one', relation='product.product', string='Part Name', store=True, readonly=True),
		'type': fields.related('schedule_line_id','type', type='char', string='Purpose', store=True, readonly=True),
		'moc_id': fields.related('planning_line_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		
		'stage_id': fields.many2one('kg.stage.master','Stage',domain="[('state','=','approved'), ('active','=','t')]"),
		'planning_qty': fields.related('planning_line_id','qty', type='float', size=100, string='Planning Qty', store=True, readonly=True),
		'production_qty': fields.float('Production Qty', size=100, required=True),
		'qty': fields.float('Produced Qty', size=100, required=True),
		'excess_qty': fields.float('Excess Qty', size=100, required=True),
		'cancel_remark': fields.text('Cancel Remarks'),
		
		'line_ids': fields.one2many('ch.boring.details', 'header_id', "Boring Details"),
		'line_ids_a': fields.one2many('ch.casting.details', 'header_id', "Casting Details"),
		
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
		if entry_date > today:
			return False
		return True
		
		
			
	
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
  
	   ]
	   
	   
	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),
			'name' :self.pool.get('ir.sequence').get(cr, uid, 'kg.production') or '/'})
		return True
		

	def entry_update(self,cr,uid,ids,context=None):
		schedule_line_obj = self.pool.get('ch.weekly.schedule.details')
		planning_line_obj = self.pool.get('ch.daily.planning.details')
		qc_obj = self.pool.get('kg.qc.verification')
		sch_bomline_obj = self.pool.get('ch.sch.bom.details')
		entry = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		
		### Boring Vs Production
		
		cr.execute(''' select sum(qty) from ch_boring_details where header_id = %s''',[entry.id])
		boring_qty = cr.fetchone()
		
		cr.execute(''' select sum(qty) from ch_casting_details where header_id = %s''',[entry.id])
		casting_qty = cr.fetchone()
		
		if boring_qty:
			if boring_qty[0] != None:
				if boring_qty[0] >= entry.qty:
					self.write(cr, uid, ids, {'state': 'boring_complete'})
				if boring_qty[0] < entry.qty :
					self.write(cr, uid, ids, {'state': 'boring_inprogress'})
					
		### Casting Vs Production
		
		if casting_qty:
			if casting_qty[0] != None:
				if boring_qty[0] == None and casting_qty[0] > 0.00:
					raise osv.except_osv(_('Warning!'),
						_('Casting cannot be done befor Bouring!!'))
				if casting_qty[0] > boring_qty[0]:
					raise osv.except_osv(_('Warning!'),
						_('Casting Qty should not be greater than Bouring Qty!!'))
				if casting_qty[0] >= entry.qty:
					if casting_qty[0] > entry.qty:
						excess_qty = casting_qty[0] - entry.qty
					else:
						excess_qty = 0.00
					self.write(cr, uid, ids, {'state': 'casting_complete','excess_qty':excess_qty,'qty':casting_qty[0]})
					
					### Production Qty Updation 
					production_qty = casting_qty[0]
					
					bom_produc_qty = entry.sch_bomline_id.production_qty + production_qty

					if entry.sch_bomline_id.planning_qty == 0.00:
						sch_bomline_obj.write(cr, uid, entry.sch_bomline_id.id, 
					
						{
						
						'transac_state':'complete',
						'production_qty': bom_produc_qty,
						
						
						})
					if entry.sch_bomline_id.planning_qty > 0.00:
						sch_bomline_obj.write(cr, uid, entry.sch_bomline_id.id,  
					
						{
						
						'transac_state':'partial',
						'production_qty': bom_produc_qty,
						
						
						})
						
						
						
					planning_line_obj.write(cr, uid, entry.planning_line_id.id, {'transac_state':'complete'})
				
					if excess_qty > 0.00:
						
						
						#### Stock Updation Block Starts Here ###
						
								
						cr.execute(''' insert into kg_foundry_stock(company_id,division_id,location,pump_model_id,pattern_id,
								moc_id,trans_type,qty,alloc_qty,type,schedule_id,schedule_line_id,planning_id,planning_line_id,
								allocation_id,qc_id,production_id ,creation_date,schedule_date,
								planning_date,qc_date,production_date,remarks,bom_id,bom_line_id,sch_bomline_id)
							
								values(%s,%s,%s,%s,%s,%s,%s,%s,0.00,'IN',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
								''',[entry.company_id.id,entry.division_id.id or None,entry.location,entry.pump_model_id.id, entry.pattern_id.id,
								entry.moc_id.id,entry.type,excess_qty,entry.schedule_id.id,entry.schedule_line_id.id,
								entry.planning_id.id,entry.planning_line_id.id,entry.allocation_id.id or None, entry.qc_id.id or None,
								entry.id,today,entry.schedule_id.entry_date,
								entry.planning_id.entry_date,entry.qc_id.entry_date or None, entry.entry_date,entry.note,entry.bom_id.id,entry.bom_line_id.id,entry.sch_bomline_id.id ])
									
						#### Stock Updation Block Ends Here ###
						
				if casting_qty[0] < entry.qty:
					self.write(cr, uid, ids, {'state': 'casting_inprogress'})

		return True
		
	def entry_cancel(self,cr,uid,ids,context=None):
		schedule_line_obj = self.pool.get('ch.weekly.schedule.details')
		planning_line_obj = self.pool.get('ch.daily.planning.details')
		qc_obj = self.pool.get('kg.qc.verification')
		entry = self.browse(cr,uid,ids[0])
		if entry.cancel_remark == False:
			raise osv.except_osv(_('Warning!'),
						_('Cancellation Remarks is must !!'))
		
		cr.execute(''' select id from ch_daily_planning_details where schedule_line_id = %s and id > %s and state = 'confirmed' ''',[entry.schedule_line_id.id,entry.planning_line_id.id])
		planning_id = cr.fetchone()
		if planning_id != None:
			if planning_id[0]:
				raise osv.except_osv(_('Warning!'),
						_('Production cannot be Cancelled!!'))
				
		### Updation in Stock Table
		cr.execute(''' delete from kg_foundry_stock where production_id = %s  ''',[entry.id])
		### Updation in Schedule Table
		production_qty = entry.sch_bomline_id.production_qty - entry.qty
		cr.execute(''' update ch_sch_bom_details set production_qty = %s where id = %s and header_id = %s ''',[production_qty,entry.sch_bomline_id.id, entry.schedule_line_id.id])
		self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S'),'transac_state':'cancel'})
		return True
		
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):				
			raise osv.except_osv(_('Warning!'),
					_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_production, self).write(cr, uid, ids, vals, context)
	
	
kg_production()

class ch_boring_details(osv.osv):

	_name = "ch.boring.details"
	_description = "Boring Details"
	
	_columns = {
	
		'header_id':fields.many2one('kg.production', 'Production', required=1, ondelete='cascade'),
		'production_qty': fields.related('header_id','qty', type='float', string='Production Qty', store=True, readonly=True),
		'entry_date': fields.date('Date'),
		'qty': fields.float('Qty', size=100),
		'heat_no': fields.char('Heat No'),
		'remark': fields.text('Remarks'),
	
	}
	
	_defaults = {
		
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		
	}
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty < 0.00:
			return False
		return True
		
	def _check_heatno(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(''' select id from ch_boring_details where heat_no = %s and id != %s and header_id = %s ''',[entry.heat_no,entry.id, entry.header_id.id])
		boring_id = cr.fetchone()
		if boring_id:
			if boring_id[0] != None:
				return False
		return True
		
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		entry_date = entry.entry_date
		entry_date = str(entry_date)
		entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
		if entry_date > today:
			return False
		return True
		
	_constraints = [        
              
        
        (_check_values, 'System not allow to save less than zero qty .!!',['']),
        (_future_entry_date_check, 'Boring Date cannot be in Future Date .!!',['']),
        (_check_heatno, 'Heat No. must be Unique .!!',['']),
       
        
       ]
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_boring_details, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_boring_details, self).write(cr, uid, ids, vals, context)
	
ch_boring_details()


class ch_casting_details(osv.osv):

	_name = "ch.casting.details"
	_description = "Casting Details"
	
	_columns = {
	
		'header_id':fields.many2one('kg.production', 'Production', required=1, ondelete='cascade'),
		'production_qty': fields.related('header_id','qty', type='float', string='Production Qty', store=True, readonly=True),
		'entry_date': fields.date('Date'),
		'qty': fields.float('Qty', size=100),
		'remark': fields.text('Remarks'),
	
	}
	
	
	_defaults = {
		
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		
	}
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty < 0.00:
			return False
		return True
		
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		entry_date = entry.entry_date
		entry_date = str(entry_date)
		entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
		if entry_date > today:
			return False
		return True
		
	_constraints = [        
              
        
        (_check_values, 'System not allow to save less than zero qty .!!',['']),
        (_future_entry_date_check, 'Casting Date cannot be in Future Date .!!',['']),
        
       ]
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_casting_details, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_casting_details, self).write(cr, uid, ids, vals, context)
	
ch_casting_details()

class kg_foundry_stock(osv.osv):

	_name = "kg.foundry.stock"
	_description = "Foundry Stock"
	
	_columns = {
	
		'company_id': fields.many2one('res.company', 'Company Name'),
		'division_id': fields.many2one('kg.division.master','Division'),
		'stock_inward_id': fields.many2one('ch.stock.inward.details','Stock Inward Line'),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location'),
		'stage_id': fields.many2one('kg.stage.master','Stage Master'),
		'remarks': fields.text('Remarks'),
		'bom_id': fields.many2one('kg.bom', 'BOM Id'),
		'bom_line_id': fields.many2one('ch.bom.line','BOM Line Id'),
		'sch_bomline_id': fields.many2one('ch.sch.bom.details','Schedule BOM Line Id'),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'trans_type': fields.selection([('production','Production'),('spare','Spare')],'Purpose'),
		'qty': fields.float('Qty', size=100),
		'alloc_qty': fields.float('Allocation Qty', size=100),
		'type': fields.char('Type', size=5),
		'schedule_id': fields.many2one('kg.weekly.schedule','Schedule Header'),
		'schedule_line_id': fields.many2one('ch.weekly.schedule.details','Schedule Line'),
		'planning_id': fields.many2one('kg.daily.planning','Planning'),
		'planning_line_id': fields.many2one('ch.daily.planning.details','Planning Line Item'),
		'allocation_id': fields.many2one('ch.stock.allocation.details','Allocation'),
		'qc_id': fields.many2one('kg.qc.verification','QC'),
		'production_id': fields.many2one('kg.production','Production'),
		'creation_date': fields.date('Creation Date'),
		'schedule_date': fields.date('Schedule Date'),
		'planning_date': fields.date('Planning Date'),
		'allocation_date': fields.date('Allocation Date'),
		'qc_date': fields.date('Qc Date'),
		'production_date': fields.date('Production Date'),
		
		
	
	}
	
	
	_defaults = {
		
		'creation_date' : lambda * a: time.strftime('%Y-%m-%d'),
		
	}
	
	
kg_foundry_stock()











