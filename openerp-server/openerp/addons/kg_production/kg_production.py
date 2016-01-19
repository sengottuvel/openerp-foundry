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
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('pouring_inprogress','Pouring In Progress'),('pouring_complete','Pouring Complete')
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
		'order_type': fields.selection([('work_order','Normal'),('emergency','Emergency')],'Type'),
		'pump_model_id': fields.related('schedule_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('planning_line_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('pattern_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		#'part_name_id': fields.related('schedule_line_id','part_name_id', type='many2one', relation='product.product', string='Part Name', store=True, readonly=True),
		'type': fields.related('schedule_line_id','type', type='char', string='Purpose', store=True, readonly=True),
		'moc_id': fields.related('planning_line_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		
		'stage_id': fields.many2one('kg.stage.master','Stage',domain="[('state','=','approved'), ('active','=','t')]"),
		'planning_qty': fields.related('planning_line_id','qty', type='integer', size=100, string='Planning Qty', store=True, readonly=True),
		'production_qty': fields.integer('Production Qty', required=True),
		'qty': fields.integer('Qty', required=True),
		'excess_qty': fields.integer('Excess Qty', required=True),
		'bal_produc_qty': fields.integer('Balance Production Qty'),
		'cancel_remark': fields.text('Cancel Remarks'),
		
		'line_ids': fields.one2many('ch.boring.details', 'header_id', "Pouring Details"),
		'line_ids_a': fields.one2many('ch.casting.details', 'header_id', "Casting Details"),
		
		'production_type': fields.selection([('schedule','Schedule'),('nc','MS NC'),('floor_nc','Floor NC')],'Type'),
		
		'pouring_qty': fields.integer('Pouring Qty'),
		'reject_qty': fields.integer('Rejection Qty'),
		'casting_qty': fields.integer('Casting Qty'),
		
		'pouring_date': fields.date('Pouring Date'),
		'casting_date': fields.date('Casting Date'),
		
		'pouring_remark': fields.text('Remarks'),
		'casting_remark': fields.text('Remarks'),
		
		'flag_save':fields.boolean('Save'),
		
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
		
		schedule_line_obj = self.pool.get('ch.weekly.schedule.details')
		planning_line_obj = self.pool.get('ch.daily.planning.details')
		qc_obj = self.pool.get('kg.qc.verification')
		sch_bomline_obj = self.pool.get('ch.sch.bom.details')
		pouring_obj = self.pool.get('ch.boring.details')
		casting_obj = self.pool.get('ch.casting.details')
		entry = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		
		### Pouring Details
		pouring_qty = vals.get('pouring_qty')
		reject_qty = vals.get('reject_qty')
		pouring_date = vals.get('pouring_date')
		pouring_remark = vals.get('pouring_remark')
		
		### Casting Details
		casting_qty = vals.get('casting_qty')
		casting_date = vals.get('casting_date')
		casting_remark = vals.get('casting_remark')
		
		
		### Pouring Vs Production
		
		cr.execute(''' select sum(qty) from ch_boring_details where header_id = %s''',[entry.id])
		pre_pouring_qty = cr.fetchone()
		
		cr.execute(''' select sum(qty) from ch_casting_details where header_id = %s''',[entry.id])
		pre_casting_qty = cr.fetchone()
		

		if pre_pouring_qty:
			if pre_pouring_qty[0] != None and pouring_qty != None:
				produced_qty = pre_pouring_qty[0] + pouring_qty
			else:
				produced_qty = pouring_qty
				
		if pre_casting_qty:
			if pre_casting_qty[0] != None and casting_qty != None:
				pre_casting_qty = pre_casting_qty[0] + casting_qty
			else:
				pre_casting_qty = casting_qty
		
		if pouring_qty > 0:
			
			### Pouring Line Entry Creation in Production
			cr.execute(''' insert into ch_boring_details(header_id,entry_date,qty,remark)
				values(%s,%s,%s,%s)
				''',[entry.id,pouring_date,pouring_qty,pouring_remark])
			
			### Production Creation When Rejection
			
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
					'pattern_name':entry.planning_line_id.pattern_id.name,
					'production_qty': reject_qty ,
					'bal_produc_qty': reject_qty,	
					'qty' : 0,	
					'excess_qty' : 0,
					'production_type':'floor_nc',
					'state' : 'draft',
					'order_type':entry.order_type,
								
				}
			
				production_id = self.create(cr, uid, production_vals)
				
				
			produced_qty = entry.qty + pouring_qty
				
			if produced_qty > entry.production_qty:
				bal_produc_qty = 0
			else:
				bal_produc_qty =  entry.production_qty - produced_qty
			
			if produced_qty >= entry.production_qty:

				if produced_qty > entry.production_qty:
					excess_qty = produced_qty - entry.production_qty
				else:
					excess_qty = 0
				
				if pre_casting_qty == None or 0:
					cr.execute(''' update kg_production set state = 'pouring_complete', excess_qty=%s,qty=%s,
						bal_produc_qty = %s where id = %s
					''',[excess_qty,produced_qty,bal_produc_qty,entry.id])
				
				### Production Qty Updation ###
				if entry.sch_bomline_id.planning_qty == 0:
					sch_bomline_obj.write(cr, uid, entry.sch_bomline_id.id, 
					{'transac_state':'complete','production_qty': pouring_qty})
					schedule_line_obj.write(cr, uid, entry.schedule_line_id.id, {'transac_state':'complete'})
				if entry.sch_bomline_id.planning_qty > 0:
					sch_bomline_obj.write(cr, uid, entry.sch_bomline_id.id,  
					{'transac_state':'partial','production_qty': pouring_qty})
					schedule_line_obj.write(cr, uid, entry.schedule_line_id.id, {'transac_state':'partial'})
					
				planning_line_obj.write(cr, uid, entry.planning_line_id.id, {'transac_state':'complete'})
				
				if excess_qty > 0:
						
						
					#### Stock Updation Block Starts Here ###
					
							
					cr.execute(''' insert into kg_foundry_stock(company_id,division_id,location,pump_model_id,pattern_id,
						moc_id,trans_type,qty,alloc_qty,type,schedule_id,schedule_line_id,planning_id,planning_line_id,
						allocation_id,qc_id,production_id ,creation_date,schedule_date,
						planning_date,qc_date,production_date,remarks,bom_id,bom_line_id,sch_bomline_id,order_type,production_type)
					
						values(%s,%s,%s,%s,%s,%s,%s,%s,0,'IN',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
						''',[entry.company_id.id,entry.division_id.id or None,entry.location,entry.pump_model_id.id, entry.pattern_id.id,
						entry.moc_id.id,entry.type,excess_qty,entry.schedule_id.id,entry.schedule_line_id.id,entry.planning_id.id,
						entry.planning_line_id.id,entry.allocation_id.id or None, entry.qc_id.id or None,entry.id,today,
						entry.schedule_id.entry_date,entry.planning_id.entry_date,entry.qc_id.entry_date or None, entry.entry_date,
						entry.note,entry.bom_id.id,entry.bom_line_id.id,entry.sch_bomline_id.id, entry.order_type, entry.production_type ])
								
					#### Stock Updation Block Ends Here ###
			if produced_qty < entry.production_qty :
				
				cr.execute(''' update kg_production set state = 'pouring_inprogress', qty=%s,
				    bal_produc_qty = %s where id = %s
				''',[produced_qty,bal_produc_qty,entry.id])
				### Production Qty Updation
				sch_bomline_obj.write(cr, uid, entry.sch_bomline_id.id, {'production_qty': pouring_qty})
		
		
		### Casting Vs Production
		if casting_qty > 0:
			
			### Casting Line Entry Creation in Production
			
			cr.execute(''' insert into ch_casting_details(header_id,entry_date,qty,remark)
				values(%s,%s,%s,%s)
				''',[entry.id,casting_date,casting_qty,casting_remark])
			
			### Production Creation When Rejection
			if pre_casting_qty > entry.qty:
				raise osv.except_osv(_('Warning!'),
					_('Casting Qty should not be greater than Pouring Qty!!'))
			if pre_casting_qty >= entry.qty:
				if entry.qty >= entry.production_qty:
					cr.execute(''' update kg_production set state = 'casting_complete' where id = %s''',[entry.id])
			
			if pre_casting_qty < entry.qty:
				
				if entry.qty >= entry.production_qty:
					cr.execute(''' update kg_production set state = 'casting_inprogress' where id = %s''',[entry.id])

		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid,
			'pouring_qty':0,'pouring_date':False,'reject_qty':0,'pouring_remark':'','casting_qty':0,'casting_date':False,'casting_remark':''})
		return super(kg_production, self).write(cr, uid, ids, vals, context)
	
	
kg_production()

class ch_boring_details(osv.osv):

	_name = "ch.boring.details"
	_description = "Pouring Details"
	
	_columns = {
	
		'header_id':fields.many2one('kg.production', 'Production', required=1, ondelete='cascade'),
		'production_qty': fields.related('header_id','qty', type='integer', string='Production Qty', store=True, readonly=True),
		'production_type': fields.related('header_id','production_type', type='char', string='Type', store=True, readonly=True),
		'order_ref_no': fields.related('header_id','order_ref_no', type='char', string='Work Order', store=True, readonly=True),
		'pump_model_id': fields.related('header_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('header_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('header_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('header_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'production_qty': fields.related('header_id','qty', type='integer', string='Produced Qty', store=True, readonly=True),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('pouring_inprogress','Pouring In Progress'),('pouring_complete','Pouring Complete')
				,('casting_inprogress','Casting In Progress'),('casting_complete','Casting Complete'),('cancel','Cancelled')],'Status', readonly=True),
		'entry_date': fields.date('Date'),
		'qty': fields.integer('Qty'),
		'heat_no': fields.char('Heat No'),
		'remark': fields.text('Remarks'),
	
	}
	
	_defaults = {
	
		'state': 'draft',
		
	}
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty < 0:
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
		#(_future_entry_date_check, 'Boring Date cannot be in Future Date .!!',['']),
		#(_check_heatno, 'Heat No. must be Unique .!!',['']),
	   
		
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
		'production_qty': fields.related('header_id','qty', type='integer', string='Production Qty', store=True, readonly=True),
		'production_type': fields.related('header_id','production_type', type='char', string='Type', store=True, readonly=True),
		'order_ref_no': fields.related('header_id','order_ref_no', type='char', string='Work Order', store=True, readonly=True),
		'pump_model_id': fields.related('header_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('header_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('header_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('header_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'production_qty': fields.related('header_id','qty', type='integer', string='Produced Qty', store=True, readonly=True),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('pouring_inprogress','Pouring In Progress'),('pouring_complete','Pouring Complete')
				,('casting_inprogress','Casting In Progress'),('casting_complete','Casting Complete'),('cancel','Cancelled')],'Status', readonly=True),
		'entry_date': fields.date('Date'),
		'qty': fields.integer('Qty'),
		'remark': fields.text('Remarks'),
		'visible_state': fields.selection([('visible','Visible'),('in_visible','Invisble')],'Visible Status'),
	
	}
	
	_defaults = {
	
		'visible_state': 'visible',
		'state': 'draft',
		
	}
	
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty < 0:
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
		#(_future_entry_date_check, 'Casting Date cannot be in Future Date .!!',['']),
		
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
		'order_type': fields.selection([('work_order','Normal'),('emergency','Emergency')],'Order Type'),
		'production_type': fields.selection([('schedule','Schedule'),('nc','NC'),('floor_nc','Floor NC')],'Production Type'),
		'qty': fields.integer('Qty'),
		'alloc_qty': fields.integer('Allocation Qty'),
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











