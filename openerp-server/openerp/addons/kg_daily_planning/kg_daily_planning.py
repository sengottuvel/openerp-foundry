from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')


class kg_daily_planning(osv.osv):

	_name = "kg.daily.planning"
	_description = "Planning (BOM)"
	_order = "entry_date desc"
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Planning No', size=128,select=True,readonly=True),
		'entry_date': fields.date('Planning Date',required=True),
		'division_id': fields.many2one('kg.division.master','Division',required=True,domain="[('state','=','approved'), ('active','=','t')]"),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location',required=True),
		'note': fields.text('Notes'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'line_ids': fields.one2many('ch.daily.planning.details', 'header_id', "Planning Details"),
		
		'schedule_line_ids':fields.many2many('ch.weekly.schedule.details','m2m_weekly_schedule_details' , 'planning_id', 'schedule_id', 'Weekly Schedule Lines',
			domain="[('header_id.state','=','confirmed'),'&',('state','=','confirmed'),'&', ('line_ids.planning_qty','>','0'),'&', ('line_ids.transac_state','in',('in_schedule','partial','sent_for_produc')),'&', ('line_ids.flag_applicable','=',('True')),'|',('header_id.division_id','=',division_id),('header_id.location','=',location)]"),
		'flag_planning': fields.boolean('Planning'),
		'flag_cancel': fields.boolean('Cancellation Flag'),
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_daily_planning', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',	
		'active': True,
		'flag_planning': False,
		

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
		
	def _entry_duplicates(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		cr.execute(''' select id from kg_daily_planning 
		where 
		id != %s and
		entry_date = %s and
		state = 'confirmed'
		
		''',[rec.id,str(rec.entry_date) ])
		dup_id = cr.fetchone()
		if dup_id:
			return False
		return True	
	
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),   
		(_entry_duplicates, 'System not allow to create duplicate Entry. !!',['']),   
		
	   ]
	   
	   
	def update_line_items(self,cr,uid,ids,product_id,context=False):
		entry = self.browse(cr,uid,ids[0])
		schedule_obj = self.pool.get('kg.weekly.schedule')
		schedule_line_obj = self.pool.get('ch.weekly.schedule.details')
		planning_line_obj = self.pool.get('ch.daily.planning.details')
		allocation_line_obj = self.pool.get('ch.stock.allocation.details')
		sch_bomline_obj = self.pool.get('ch.sch.bom.details')
		
		del_sql = """ delete from ch_daily_planning_details where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		if entry.schedule_line_ids:
			for sch_item in entry.schedule_line_ids:
				
				for bom_item in sch_item.line_ids:
					if bom_item.flag_applicable == True and bom_item.planning_qty > 0.00:
						planning_item_vals = {
													
							'header_id': entry.id,
							'schedule_id': sch_item.header_id.id,
							'schedule_line_id': sch_item.id,										
							'bom_id': bom_item.bom_id.id,
							'bom_line_id': bom_item.bom_line_id.id,																	
							'sch_bomline_id': bom_item.id,									
							'qty' : bom_item.planning_qty,
							'stock_qty' : 0.00,
							'line_status': 'planning'									
							}
						
						planning_line_id = planning_line_obj.create(cr, uid, planning_item_vals)
					
						self.write(cr, uid, ids, {'flag_planning':True})
					
						sch_bomline_obj.write(cr, uid, bom_item.id, {'transac_state':'sent_for_plan'})

						tot_stock = 0.00
						
						cr.execute(''' select 

							((select case when sum (qty) > 0.00 then sum (qty) else 0.00 end  
							
							from  kg_foundry_stock 
							
							where 
							
							moc_id = %s and
							pump_model_id = %s and
							pattern_id = %s and
							type = 'IN' and
							qty > 0.00) 

							-

							(select case when sum (qty) > 0.00 then sum (qty) else 0.00 end 
										
							from  kg_foundry_stock

							where
							
							moc_id = %s and
							pump_model_id = %s and
							pattern_id = %s and
							type = 'OUT' and
							qty > 0.00)) as stock_qty

							from kg_foundry_stock

							limit 1
						
						''',[bom_item.moc_id.id,sch_item.pump_model_id.id, bom_item.pattern_id.id
							,bom_item.moc_id.id, sch_item.pump_model_id.id, bom_item.pattern_id.id])
						result_stock_qty = cr.fetchone()
						
						plan_rec = planning_line_obj.browse(cr, uid, planning_line_id)
					
						if result_stock_qty == None:
							stock_qty = 0.00
							if plan_rec.line_status == 'planning':
								line_status = 'planning'
							else:
								line_status = 'plan_alloc'
						if result_stock_qty != None:
							if result_stock_qty[0] > 0.00:
								stock_qty = result_stock_qty[0]
								if plan_rec.line_status == 'planning':
									line_status = 'plan_alloc'
								else:
									line_status = 'plan_alloc'
							if result_stock_qty[0] == 0.00:
								stock_qty = 0.00
								if plan_rec.line_status == 'planning':
									line_status = 'plan_alloc'
								else:
									line_status = 'plan_alloc'
								
						#### Allocation Creation When stock exists ####
						
						tot_stock += stock_qty
						

						if stock_qty > 0.00:
							
							if plan_rec.qty == stock_qty:
								alloc_qty = plan_rec.qty
							if plan_rec.qty > stock_qty:
								alloc_qty = stock_qty
							if plan_rec.qty < stock_qty:
								alloc_qty = plan_rec.qty
							
							allocation_item_vals = {
													
								'header_id': planning_line_id,
								'schedule_id': sch_item.header_id.id,
								'schedule_line_id': sch_item.id,
								'planning_qty' : bom_item.planning_qty,										
								'qty' : alloc_qty,											
								'stock_qty' : stock_qty,
								#'stage_id':stage_id			
							}
							
							planning_line_obj.write(cr, uid, planning_line_id, {'stock_qty':tot_stock,'line_status':line_status})
							
							allocation_id = allocation_line_obj.create(cr, uid, allocation_item_vals)

		return True
	   

	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		qc_verf_obj = self.pool.get('kg.qc.verification')
		production_obj = self.pool.get('kg.production')
		planning_line_obj = self.pool.get('ch.daily.planning.details')
		allocation_line_obj = self.pool.get('ch.stock.allocation.details')
		schedule_line_obj = self.pool.get('ch.weekly.schedule.details')
		sch_bomline_obj = self.pool.get('ch.sch.bom.details')
		today = date.today()
		today = str(today)

		if entry.line_ids:
			
			for plan_item in entry.line_ids:
				
				### Planning Details Validation ###
				if plan_item.qty == 0.00:
					raise osv.except_osv(_('Warning !'), _('Planning Qty should not be Zero !!'))
							
				if plan_item.qty > plan_item.schedule_qty:
					raise osv.except_osv(_('Warning !'), _('Planning Qty should not be greater than Schedule Qty!!'))
				
				### Allocation Details Validation ###
				if plan_item.line_ids:
					for alloc_item in plan_item.line_ids:
						if alloc_item.qty > 0.00:
							if alloc_item.qty > alloc_item.stock_qty:
								raise osv.except_osv(_('Warning !'), _('Allocation Qty should not be greater than Stock Qty for Order %s !!')%(plan_item.order_ref_no))
							
						cr.execute(''' select sum(qty) from ch_stock_allocation_details where header_id = %s ''',[plan_item.id])
						alloc_qty = cr.fetchone()
						if alloc_qty[0] != None:
							if plan_item.qty < alloc_qty[0]:
								raise osv.except_osv(_('Warning !'), _('Allocation Qty should not be greater than Planning Qty for Order %s !!')%(plan_item.order_ref_no))
						
						
						#### QC Creation When Allocation ###
						
						if alloc_item.qty > 0.00: 
				
							qc_item_vals = {
													
								'name': '',
								'planning_id': entry.id,
								'planning_date': entry.entry_date,
								'division_id': entry.division_id.id,
								'location' : entry.location,
								'planning_line_id': plan_item.id,
								'allocation_id': alloc_item.id,
								'schedule_id': plan_item.schedule_id.id,
								'schedule_line_id': plan_item.schedule_line_id.id,		
								#'stage_id' : alloc_item.stage_id.id,		
								'qty' : alloc_item.qty,
								'state' : 'draft'						
							}
						
							qc_id = qc_verf_obj.create(cr, uid, qc_item_vals)
							
							sch_bomline_obj.write(cr, uid, plan_item.sch_bomline_id.id, {'transac_state':'sent_for_qc'})
							
							planning_line_obj.write(cr, uid, plan_item.id, {'transac_state':'sent_for_qc'})
							
							
							cr.execute(''' update ch_stock_allocation_details set state = 'confirmed' where header_id = %s ''',[alloc_item.header_id.id])
						
							#### Stock Updation Block Starts Here ###
						
							cr.execute(''' insert into kg_foundry_stock(company_id,division_id,location,bom_id,bom_line_id,sch_bomline_id,pump_model_id,pattern_id,
							moc_id,trans_type,qty,alloc_qty,type,schedule_id,schedule_line_id,planning_id,planning_line_id,
							allocation_id,creation_date,schedule_date,planning_date)
							
							values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0.00,%s,'OUT',%s,%s,%s,%s,%s,%s,%s,%s)
							''',[entry.company_id.id,entry.division_id.id or None,entry.location,plan_item.bom_id.id,plan_item.bom_line_id.id,plan_item.sch_bomline_id.id,plan_item.pump_model_id.id, plan_item.pattern_id.id,
							plan_item.moc_id.id,plan_item.type,alloc_item.qty,plan_item.schedule_id.id,plan_item.schedule_line_id.id,
							entry.id,plan_item.id,alloc_item.id,today,plan_item.schedule_id.entry_date,entry.entry_date ])
									
							#### Stock Updation Block Ends Here ###
							
							production_qty = plan_item.qty - alloc_qty[0]
							
							if production_qty > 0:
								
								### Planning Qty Updation in Weekly Schedule ###
								sch_bomline_rec = sch_bomline_obj.browse(cr, uid, plan_item.sch_bomline_id.id)
								
								planned_qty = sch_bomline_rec.planning_qty - plan_item.qty
								
								sch_bomline_rec.write({
								
									'planning_qty': planned_qty,
									'transac_state':'sent_for_produc'
									
									})
								
								#### Production Creation When No Allocation ####

								production_vals = {
														
									'name': '',
									'planning_id': entry.id,
									'planning_date': entry.entry_date,
									'division_id': entry.division_id.id,
									'location' : entry.location,
									'planning_line_id': plan_item.id,
									'schedule_id': plan_item.schedule_id.id,
									'schedule_line_id': plan_item.schedule_line_id.id,
									'production_qty': production_qty,	
									'qty' : production_qty,	
									'excess_qty' : 0.00,
									'state' : 'draft',
													
								}
							
								production_id = production_obj.create(cr, uid, production_vals)
								
								sch_bomline_obj.write(cr, uid, plan_item.sch_bomline_id.id, {'transac_state':'sent_for_produc'})
								
								planning_line_obj.write(cr, uid, plan_item.id, {'transac_state':'sent_for_produc'})
								
							else:
								
								### Planning Qty Updation in Weekly Schedule ###
								sch_bomline_rec = sch_bomline_obj.browse(cr, uid, plan_item.sch_bomline_id.id)
								
								planned_qty = sch_bomline_rec.planning_qty - plan_item.qty
								
								sch_bomline_rec.write({
								
									'planning_qty': planned_qty,
									'transac_state':'sent_for_qc'
									
									})
								
									
							
							
				### Production Creation When No Allocation ####
					
				cr.execute(''' select id from ch_stock_allocation_details
				
				where
				header_id = %s and
				qty > 0.00
				
				''',[plan_item.id])
				allocation_id = cr.fetchone()
				
				if not allocation_id or allocation_id == None:
					
					### Planning Qty Updation in Weekly Schedule ###
					sch_bomline_rec = sch_bomline_obj.browse(cr, uid, plan_item.sch_bomline_id.id)
					
					planned_qty = sch_bomline_rec.planning_qty - plan_item.qty
					
					sch_bomline_rec.write({
					
						'planning_qty': planned_qty,
						'transac_state':'sent_for_produc'
						
						})
					
					production_vals = {
											
						'name': '',
						'planning_id': entry.id,
						'planning_date': entry.entry_date,
						'division_id': entry.division_id.id,
						'location' : entry.location,
						'planning_line_id': plan_item.id,
						'schedule_id': plan_item.schedule_id.id,
						'schedule_line_id': plan_item.schedule_line_id.id,
						'production_qty': plan_item.qty,	
						'qty' : plan_item.qty,	
						'excess_qty' : 0.00,	
						'state' : 'draft',
										
					}
				
					production_id = production_obj.create(cr, uid, production_vals)
					
					sch_bomline_obj.write(cr, uid, plan_item.sch_bomline_id.id, {'transac_state':'sent_for_produc'})
					
					planning_line_obj.write(cr, uid, plan_item.id, {'transac_state':'sent_for_produc'})
					
		else:
			raise osv.except_osv(_('Warning !'), _('System not allow to confirm an entry without planning details!!'))
			
			
		### Status Updation ###
		
		self.write(cr, uid, ids, {'state': 'confirmed','flag_cancel':1,'confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),
			'name' :self.pool.get('ir.sequence').get(cr, uid, 'kg.daily.planning') or '/'})
		cr.execute(''' update ch_daily_planning_details set state = 'confirmed' where header_id = %s ''',[ids[0]])
		
		
		return True
		
		
	def entry_cancel(self,cr,uid,ids,context=None):
		qc_obj = self.pool.get('kg.qc.verification')
		entry = self.browse(cr,uid,ids[0])
		if entry.cancel_remark == False:
			raise osv.except_osv(_('Warning!'),
						_('Cancellation Remarks is must !!'))
		
		for plan_item in entry.line_ids:
		
			### Updation for QC
			cr.execute(''' delete from kg_qc_verification where planning_line_id = %s and state = 'draft' ''',[plan_item.id])
			
			cr.execute(''' select id from kg_qc_verification where planning_line_id = %s and state = 'confirmed' ''',[plan_item.id])
			qc_id = cr.fetchone()
			if qc_id:
				if qc_id[0] != None:
					qc_obj.write(cr, uid, qc_id[0], {'cancel_remark':entry.cancel_remark})
					qc_obj.entry_cancel(cr, uid, [qc_id[0]])
			
			if plan_item.sch_bomline_id.qty == plan_item.sch_bomline_id.planning_qty:
				cr.execute(''' update ch_sch_bom_details set transac_state = 'in_schedule' where id = %s and header_id = %s ''',[plan_item.sch_bomline_id.id, plan_item.schedule_line_id.id])
			if plan_item.sch_bomline_id.planning_qty < plan_item.sch_bomline_id.qty:
				cr.execute(''' update ch_sch_bom_details set transac_state = 'partial' where id = %s and header_id = %s ''',[plan_item.sch_bomline_id.id, plan_item.schedule_line_id.id])
			if plan_item.sch_bomline_id.planning_qty == 0.00:
				cr.execute(''' update ch_sch_bom_details set transac_state = 'complete' where id = %s and header_id = %s ''',[plan_item.sch_bomline_id.id, plan_item.schedule_line_id.id])
			
			### Updation for production ####
			planning_qty = plan_item.sch_bomline_id.planning_qty + plan_item.qty
			cr.execute(''' delete from kg_production where planning_line_id = %s and state = 'draft' ''',[plan_item.id])
			cr.execute(''' select sum(qty) from ch_stock_allocation_details where header_id = %s  and qty > 0.00  ''',[plan_item.id])
			alloc_qty = cr.fetchone()
			if alloc_qty[0] == None:
				if plan_item.sch_bomline_id.qty == planning_qty:
					cr.execute(''' update ch_sch_bom_details set planning_qty = %s, transac_state = 'in_schedule' where id = %s and header_id = %s ''',[planning_qty,plan_item.sch_bomline_id.id, plan_item.schedule_line_id.id])
				if planning_qty < plan_item.sch_bomline_id.qty:
					cr.execute(''' update ch_sch_bom_details set planning_qty = %s, transac_state = 'partial' where id = %s and header_id = %s ''',[planning_qty,plan_item.sch_bomline_id.id, plan_item.schedule_line_id.id])
				if plan_item.sch_bomline_id.planning_qty == 0.00:
					cr.execute(''' update ch_sch_bom_details set planning_qty = %s, transac_state = 'complete' where id = %s and header_id = %s ''',[planning_qty,plan_item.sch_bomline_id.id, plan_item.schedule_line_id.id])

		self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid,'flag_cancel':0, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		cr.execute(''' update ch_daily_planning_details set transac_state = 'cancel' where header_id = %s ''',[ids[0]])
		
		return True

		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []
		sch_bomline_obj = self.pool.get('ch.sch.bom.details')
		for rec in self.browse(cr,uid,ids):
			for sch_item in rec.schedule_line_ids:
				for bom_item in sch_item.line_ids:
					if bom_item.planning_qty == bom_item.qty:
						sch_bomline_obj.write(cr, uid, bom_item.id, {'transac_state':'in_schedule'})
					if bom_item.qty > bom_item.planning_qty:
						sch_bomline_obj.write(cr, uid, bom_item.id, {'transac_state':'partial'})
					if bom_item.planning_qty == 0.00:
						sch_bomline_obj.write(cr, uid, bom_item.id, {'transac_state':'complete'})
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_daily_planning, self).write(cr, uid, ids, vals, context)
		
	
	
	
kg_daily_planning()


class ch_daily_planning_details(osv.osv):

	_name = "ch.daily.planning.details"
	_description = "Planning (BOM) Details"
	
	
	_columns = {
	
		'header_id':fields.many2one('kg.daily.planning', 'Daily Planning', ondelete='cascade',required=True),
		'line_ids': fields.one2many('ch.stock.allocation.details', 'header_id', "Allocation Details"),
		'planning_date': fields.related('header_id','entry_date', type='date', string='Date', store=True, readonly=True),
		'schedule_id': fields.many2one('kg.weekly.schedule','Schedule Id'),
		'schedule_line_id': fields.many2one('ch.weekly.schedule.details','Schedule Line Id'),
		'bom_id': fields.many2one('kg.bom','BOM Id'),
		'bom_line_id': fields.many2one('ch.bom.line','BOM Line Id'),
		'sch_bomline_id': fields.many2one('ch.sch.bom.details','Schedule BOM Line Id'),
		'order_ref_no': fields.related('schedule_line_id','order_ref_no', type='char', string='Order Reference', store=True, readonly=True),
		'pump_model_id': fields.related('schedule_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('sch_bomline_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		#'part_name_id': fields.related('schedule_line_id','part_name_id', type='many2one', relation='product.product', string='Part Name', store=True, readonly=True),
		'type': fields.related('schedule_line_id','type', type='char', string='Purpose', store=True, readonly=True),
		'moc_id': fields.related('sch_bomline_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'schedule_qty': fields.related('sch_bomline_id','qty', type='float', size=100, string='Schedule Qty', store=True, readonly=True),
		
		'stock_qty': fields.float('Stock Qty', size=100, readonly=True),
		'temp_stock_qty': fields.float('Stock Qty', size=100),
		'temp_planning_qty': fields.float('Planning Qty', size=100),
		'qty': fields.float('Planning Qty', size=100, required=True),
		'line_status': fields.selection([('planning','Planning'),('plan_alloc','Planning and Allocation')],'Line Status'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'transac_state': fields.selection([('in_draft','In Draft'),('in_plan','In Planning'),('sent_for_qc','In QC'),('sent_for_produc','In Production')
			 ,('re_allocate','Re Allocate'),('complete','Completed'),('cancel','Cancelled')],'Transaction Status', readonly=True),
		'note': fields.text('Notes'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'remarks': fields.text('Remarks'),
		'active': fields.boolean('Active'),
		
	
	}
	
	_defaults = {
	
		'state': 'draft',
		'transac_state':'in_draft',		
		'active': True,
	}
	
	def onchange_planning_qty(self, cr, uid, ids, schedule_qty,qty, context=None):
		entry = self.browse(cr,uid,ids[0])
		allocation_line_obj = self.pool.get('ch.stock.allocation.details')
		if entry.line_ids:
			if qty > 0.00:
				if qty == entry.line_ids[0].stock_qty:
					alloc_qty = qty
				if qty > entry.line_ids[0].stock_qty:
					alloc_qty = entry.line_ids[0].stock_qty
				if qty < entry.line_ids[0].stock_qty:
					alloc_qty = qty
				allocation_line_obj.write(cr, uid, entry.line_ids[0].id, {'qty':alloc_qty})
				
		if qty > schedule_qty:
			raise osv.except_osv(_('Warning!'),
						_('Planning Qty should not be greater than Schedule Qty !!'))
		cr.execute(''' update ch_stock_allocation_details set planning_qty = %s where header_id = %s ''',[qty,ids[0]])
		return True
		
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty == 0.00 or entry.qty < 0.00:
			return False
		return True
		
	def entry_cancel(self,cr,uid,ids,context=None):
		qc_obj = self.pool.get('kg.qc.verification')
		entry = self.browse(cr,uid,ids[0])
		if entry.cancel_remark == False:
			raise osv.except_osv(_('Warning!'),
						_('Cancellation Remarks is must !!'))
						
		### Updation for QC
		cr.execute(''' delete from kg_qc_verification where planning_line_id = %s and state = 'draft' ''',[entry.id])
		cr.execute(''' select id from kg_qc_verification where planning_line_id = %s and state = 'confirmed' ''',[entry.id])
		qc_id = cr.fetchone()
		if qc_id:
			if qc_id[0] != None:
				qc_obj.write(cr, uid, qc_id[0], {'cancel_remark':entry.cancel_remark})
				qc_obj.entry_cancel(cr, uid, [qc_id[0]])
		
		if entry.sch_bomline_id.qty == entry.sch_bomline_id.planning_qty:
			cr.execute(''' update ch_sch_bom_details set transac_state = 'in_schedule' where id = %s and header_id = %s ''',[entry.sch_bomline_id.id, entry.schedule_line_id.id])
		if entry.sch_bomline_id.planning_qty < entry.sch_bomline_id.qty:
			cr.execute(''' update ch_sch_bom_details set transac_state = 'partial' where id = %s and header_id = %s ''',[entry.sch_bomline_id.id, entry.schedule_line_id.id])
		if entry.sch_bomline_id.planning_qty == 0.00:
			cr.execute(''' update ch_sch_bom_details set transac_state = 'complete' where id = %s and header_id = %s ''',[entry.sch_bomline_id.id, entry.schedule_line_id.id])
		### Updation for production ####
		planning_qty = entry.sch_bomline_id.planning_qty + entry.qty
		cr.execute(''' delete from kg_production where planning_line_id = %s and state = 'draft' ''',[entry.id])
		cr.execute(''' select sum(qty) from ch_stock_allocation_details where header_id = %s and qty > 0.00  ''',[entry.id])
		alloc_qty = cr.fetchone()
		if alloc_qty[0] == None:
			if entry.sch_bomline_id.qty == planning_qty:
				cr.execute(''' update ch_sch_bom_details set planning_qty = %s, transac_state = 'in_schedule' where id = %s and header_id = %s ''',[planning_qty,entry.sch_bomline_id.id, entry.schedule_line_id.id])
			if planning_qty < entry.sch_bomline_id.qty:
				cr.execute(''' update ch_sch_bom_details set planning_qty = %s, transac_state = 'partial' where id = %s and header_id = %s ''',[planning_qty,entry.sch_bomline_id.id, entry.schedule_line_id.id])
			if planning_qty == 0.00:
				cr.execute(''' update ch_sch_bom_details set planning_qty = %s, transac_state = 'complete' where id = %s and header_id = %s ''',[planning_qty,entry.sch_bomline_id.id, entry.schedule_line_id.id])
		
		self.write(cr, uid, ids, {'state': 'cancel','transac_state':'cancel'})
		
		
		return True
		
	"""def entry_reallocate(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		qc_verf_obj = self.pool.get('kg.qc.verification')
		production_obj = self.pool.get('kg.production')
		planning_line_obj = self.pool.get('ch.daily.planning.details')
		allocation_line_obj = self.pool.get('ch.stock.allocation.details')
		schedule_line_obj = self.pool.get('ch.weekly.schedule.details')
		sch_bomline_obj = self.pool.get('ch.sch.bom.details')
		today = date.today()
		today = str(today)
		### Allocation Details Validation ###
		if entry.line_ids:
			for alloc_item in entry.line_ids:
				if alloc_item.qty > 0.00:
					if alloc_item.qty > alloc_item.stock_qty:
						raise osv.except_osv(_('Warning !'), _('Allocation Qty should not be greater than Stock Qty !!'))
					
				cr.execute(''' select sum(qty) from ch_stock_allocation_details where header_id = %s ''',[entry.id])
				alloc_qty = cr.fetchone()
				if alloc_qty[0] != None:
					if entry.qty < alloc_qty[0]:
						raise osv.except_osv(_('Warning !'), _('Allocation Qty should not be greater than Planning Qty for Order %s !!')%(entry.order_ref_no))
							
				#### QC Creation When Allocation ###
				
				if alloc_item.qty > 0.00: 
		
					qc_item_vals = {
											
						'name': '',
						'planning_id': entry.header_id.id,
						'planning_date': entry.header_id.entry_date,
						'division_id': entry.header_id.division_id.id,
						'location' : entry.header_id.location,
						'planning_line_id': entry.id,
						'allocation_id': alloc_item.id,
						'schedule_id': entry.schedule_id.id,
						'schedule_line_id': entry.schedule_line_id.id,		
						'stage_id' : alloc_item.stage_id.id,		
						'qty' : alloc_item.qty,
						'state' : 'draft'						
					}
				
					qc_id = qc_verf_obj.create(cr, uid, qc_item_vals)
					
					sch_bomline_obj.write(cr, uid, plan_item.sch_bomline_id.id, {'transac_state':'sent_for_qc'})
					
					planning_line_obj.write(cr, uid, entry.id, {'transac_state':'sent_for_qc'})
					
					
					cr.execute(''' update ch_stock_allocation_details set state = 'confirmed' where header_id = %s ''',[alloc_item.header_id.id])
				
					#### Stock Updation Block Starts Here ###
						
					cr.execute(''' insert into kg_foundry_stock(company_id,division_id,location,pump_model_id,pattern_id,part_name_id,
					moc_id,trans_type,qty,alloc_qty,type,schedule_id,schedule_line_id,planning_id,planning_line_id,
					allocation_id,creation_date,schedule_date,planning_date,stage_id)
					
					values(%s,%s,%s,%s,%s,%s,%s,%s,0.00,%s,'OUT',%s,%s,%s,%s,%s,%s,%s,%s,%s)
					''',[entry.header_id.company_id.id,entry.header_id.division_id.id or None,entry.header_id.location,entry.pump_model_id.id, entry.pattern_id.id,entry.part_name_id.id,
					entry.moc_id.id,entry.type,alloc_item.qty,entry.schedule_id.id,entry.schedule_line_id.id,
					entry.header_id.id,entry.id,alloc_item.id,today,entry.schedule_id.entry_date,entry.header_id.entry_date,alloc_item.stage_id.id ])
							
					#### Stock Updation Block Ends Here ###
					
					### Production Creation ###
					
					production_qty = entry.qty - alloc_qty
					
					if production_qty > 0:
					
						### Planning Qty Updation in Weekly Schedule ###
						sch_bomline_rec = sch_bomline_obj.browse(cr, uid, entry.sch_bomline_id.id)
						
						planned_qty = sch_bomline_rec.planning_qty - entry.qty
						
						sch_bomline_rec.write({
						
							'planning_qty': planned_qty,
							'transac_state':'sent_for_produc'
							
							})
						
						#### Production Creation When No Allocation ####

						production_vals = {
												
							'name': '',
							'planning_id': entry.header_id.id,
							'planning_date': entry.header_id.entry_date,
							'division_id': entry.header_id.division_id.id,
							'location' : entry.header_id.location,
							'planning_line_id': entry.id,
							'schedule_id': entry.schedule_id.id,
							'schedule_line_id': entry.schedule_line_id.id,
							'production_qty': production_qty,	
							'qty' : production_qty,	
							'excess_qty' : 0.00,	
							'state' : 'draft',
											
						}
					
						production_id = production_obj.create(cr, uid, production_vals)
							
						planning_line_obj.write(cr, uid, entry.id, {'transac_state':'sent_for_produc'})
							
		
		### Production Creation When No Allocation ####
					
		cr.execute(''' select id from ch_stock_allocation_details
		
		where
		header_id = %s and
		qty > 0.00
		
		''',[entry.id])
		allocation_id = cr.fetchone()
		
		if not allocation_id or allocation_id == None:
			
			### Planning Qty Updation in Weekly Schedule ###
			sch_bomline_rec = sch_bomline_obj.browse(cr, uid, entry.sch_bomline_id.id)
			
			planned_qty = sch_bomline_rec.planning_qty - entry.qty
			
			sch_bomline_rec.write({
			
				'planning_qty': planned_qty,
				'transac_state':'sent_for_produc'
				
				})
			
			#### Production Creation When No Allocation ####

			production_vals = {
									
				'name': '',
				'planning_id': entry.header_id.id,
				'planning_date': entry.header_id.entry_date,
				'division_id': entry.header_id.division_id.id,
				'location' : entry.header_id.location,
				'planning_line_id': entry.id,
				'schedule_id': entry.schedule_id.id,
				'schedule_line_id': entry.schedule_line_id.id,
				'production_qty': entry.qty,	
				'qty' : entry.qty,	
				'excess_qty' : 0.00,	
				'state' : 'draft',
								
			}
		
			production_id = production_obj.create(cr, uid, production_vals)
			
			planning_line_obj.write(cr, uid, entry.id, {'transac_state':'sent_for_produc'})
				
		return True
		
	"""
		
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_daily_planning_details, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		if not type(ids) is list:
			entry = self.browse(cr,uid,ids)
			if vals.get('transac_state'):
				transac_state = vals.get('transac_state')
				if transac_state in ('sent_for_qc','sent_for_produc','re_allocate','in_plan'):
					cr.execute(''' select id from ch_daily_planning_details where transac_state in ('complete','sent_for_produc','sent_for_qc') and header_id = %s and id != %s ''',
					[entry.header_id.id,entry.id])
					plan_line_id = cr.fetchone()
					if plan_line_id == None:
						cr.execute(''' update kg_daily_planning set flag_cancel = 't' where id = %s ''',[entry.header_id.id])
					else:
						cr.execute(''' update kg_daily_planning set flag_cancel = 'f' where id = %s ''',[entry.header_id.id])
				else:
					cr.execute(''' update kg_daily_planning set flag_cancel = 'f' where id = %s ''',[entry.header_id.id])
		return super(ch_daily_planning_details, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []
		sch_bomline_obj = self.pool.get('ch.sch.bom.details')
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete Planning Details after confirmation !!'))
			else:
				sch_bomline_obj.write(cr, uid, rec.sch_bomline_id.id, {'transac_state':'in_schedule'})
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
		
	def _check_line_items(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft' and entry.header_id.state == 'confirmed':
			return False
		return True
		
	
	
	_constraints = [		
			  
		(_check_values, 'System not allow to save with zero and less than zero qty .!!',['Quantity']),
		(_check_line_items, 'Planning cannot be created after confirmation !! ', ['']),
		
	   ]
	
ch_daily_planning_details()


class ch_stock_allocation_details(osv.osv):

	_name = "ch.stock.allocation.details"
	_description = "Stock Allocation"
	
	
	_columns = {
	
		
		'header_id':fields.many2one('ch.daily.planning.details', 'Planning Detail', required=1, ondelete='cascade'),
		'schedule_id': fields.many2one('kg.weekly.schedule','Schedule Id'),
		'schedule_line_id': fields.many2one('ch.weekly.schedule.details','Schedule Line Id'),
		'order_ref_no': fields.related('schedule_line_id','order_ref_no', type='char', string='Order Reference', store=True, readonly=True),
		'pump_model_id': fields.related('schedule_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('header_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		#'part_name_id': fields.related('schedule_line_id','part_name_id', type='many2one', relation='product.product', string='Part Name', store=True, readonly=True),
		'moc_id': fields.related('header_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		
		'planning_qty': fields.float('Planning Qty', size=100, readonly=True),
		'stock_qty': fields.float('Stock Qty', size=100, readonly=True),
		'qty': fields.float('Allocation Qty', size=100,required=False),
		'stage_id': fields.many2one('kg.stage.master','Stage', readonly=True),
		'stage_sequence': fields.related('stage_id','stage_seq_id', type='integer', string='Stage Sequence', store=True, readonly=True),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed')],'Status', readonly=True),
		'remarks': fields.text('Remarks'),
		'active': fields.boolean('Active'),
		
	
	}

	
	_defaults = {
	
		'state': 'draft',
		'active': True,
		
	}
		
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty == 0.00:
			return False
		return True
		
	def onchange_allocation_qty(self, cr, uid, ids, planning_qty, stock_qty, qty, context=None):
		if stock_qty == 0.00:
			raise osv.except_osv(_('Warning !'), _('Allocation Qty cannot be done without Stock Qty !!'))
		entry = self.browse(cr,uid,ids[0])
		if qty > stock_qty:
			raise osv.except_osv(_('Warning !'), _('Allocation Qty should not be greater than Stock Qty !!'))
		
		cr.execute(''' select sum(qty) from ch_stock_allocation_details where header_id = %s and id != %s ''',[entry.header_id.id, entry.id])
		alloc_qty = cr.fetchone()
		
		if alloc_qty[0] != None:
			tot_alloc = alloc_qty[0] + qty
			if tot_alloc > planning_qty:
				raise osv.except_osv(_('Warning !'), _('Allocation Qty should not be greater than Planning Qty !!'))
		else:
			if qty > planning_qty:
				raise osv.except_osv(_('Warning !'), _('Allocation Qty should not be greater than Planning Qty !!'))
		return True

		
	def create(self, cr, uid, vals, context=None):
		return super(ch_stock_allocation_details, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_stock_allocation_details, self).write(cr, uid, ids, vals, context)
		
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete an entry after confirmation !!'))
						
			if rec.stock_qty > 0.00 and rec.qty > 0.00:			
				raise osv.except_osv(_('Warning!'),
						_('Allocation cannot be deleted !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	
	
	_constraints = [		
			  
		#(_check_values, 'System not allow to save with zero qty .!!',['Quantity']),
		
	   ]
	
ch_stock_allocation_details()






