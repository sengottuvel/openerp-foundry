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
   ('project','Project'),
   ('access','Accessories')
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
		
		'moc_construction_id':fields.related('order_line_id','moc_construction_id', type='many2one', relation="kg.moc.construction", string='MOC Construction Code.', store=True, readonly=True),
		'moc_construction_name':fields.related('moc_construction_id','name', type='char', string='MOC Construction Name.', store=True, readonly=True),
		'bom_id': fields.related('schedule_line_id','bom_id', type='many2one', relation='kg.bom', string='BOM Id', store=True, readonly=True),
		'bom_line_id': fields.related('schedule_line_id','bom_line_id', type='many2one', relation='ch.bom.line', string='BOM Line Id', store=True, readonly=True),
		'order_bomline_id': fields.related('schedule_line_id','order_bomline_id', type='many2one', relation='ch.order.bom.details', string='Schedule BOM Line Id', store=True, readonly=True),
		
		'order_no': fields.related('order_line_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_priority': fields.selection(ORDER_PRIORITY, string='Priority', readonly=True),
		'order_category': fields.related('order_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),

		
		#~ 'pump_model_id': fields.related('schedule_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', readonly=True),
		
		'pattern_id': fields.related('schedule_line_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern No.', store=True, readonly=True),
		'pattern_name': fields.related('pattern_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('order_bomline_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		
		'stage_id': fields.many2one('kg.stage.master','Stage', readonly=True),
		
		#~ 'stock_qty': fields.related('schedule_line_id','stock_qty', type='integer', string='Stock Qty', store=True, readonly=True),
		'stock_qty': fields.integer('Stock Qty', readonly=True),
		'allocated_qty': fields.integer('Allocated Qty',readonly=True),
		'qty': fields.integer('Accepted Qty', required=True),
		'rework_qty': fields.integer('Rework Qty'),
		'reject_qty': fields.integer('Rejection Qty'),
		'position_no': fields.char('Pos No.'),
		'diameter': fields.char('Diameter'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'reject_remark': fields.text('Rejection Remarks'),
		'each_weight': fields.function(_get_each_weight, string='Each Weight(Kgs)', method=True, store=True, type='float'),
		'total_weight': fields.function(_get_total_weight, string='Total Weight(Kgs)', method=True, store=True, type='float'),
		'reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'stock_type':fields.selection([('pump','Pump'),('pattern','Part')],'Type', required=True),
		'sent_to':fields.selection([('assembly','Assembly'),('dispatch','Dispatch')],'Sent to'),
		
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
		'stock_type': 'part',
		
		
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
	
		production_obj = self.pool.get('kg.production')
		schedule_line_obj = self.pool.get('ch.weekly.schedule.details')
		planning_line_obj = self.pool.get('ch.daily.planning.details')
		sch_bomline_obj = self.pool.get('ch.sch.bom.details')
		pouring_obj = self.pool.get('ch.boring.details')
		casting_obj = self.pool.get('ch.casting.details')
		assembly_obj = self.pool.get('kg.assembly.inward')
		assembly_foundry_obj = self.pool.get('ch.assembly.bom.details')
		assembly_ms_obj = self.pool.get('ch.assembly.machineshop.details')
		assembly_bot_obj = self.pool.get('ch.assembly.bot.details')
		entry = self.browse(cr,uid,ids[0])
		
		if entry.state == 'draft':
			
			if entry.qty > entry.allocated_qty:
				raise osv.except_osv(_('Warning !'), _('Accepted Qty should not be greater than Allocated Qty !!'))
			if entry.qty < 0:
				raise osv.except_osv(_('Warning !'), _('QC Qty should not be less than zero !!'))
				
			
			
			### Rejection Qty Updation
			
			reject_qty = entry.allocated_qty - entry.qty
			
			if reject_qty > 0 and entry.reject_remarks_id.id == False:
				raise osv.except_osv(_('Warning !'), _('Kindly give rejection remarks !!'))
				
			self.write(cr, uid, ids, {'cancel_remark':False, 'reject_qty':reject_qty or 0})
			
			### Creating MS Inward for Accept Qty ###
			
			if entry.qty > 0:
				
				if entry.stock_type == 'part':
					ms_obj = self.pool.get('kg.machineshop')
					
					### Sequence Number Generation ###
					ms_name = ''    
					ms_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.ms.inward')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,ms_seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(ms_seq_id[0],seq_rec.code))
					ms_name = cr.fetchone();
					
					ms_vals = {
						'name': ms_name[0],
						'location':entry.location,
						'schedule_id':entry.schedule_id.id,
						'schedule_date':entry.schedule_date,
						'schedule_line_id':entry.schedule_line_id.id,
						'order_bomline_id':entry.order_bomline_id.id,
						'order_id':entry.order_id.id,
						'order_line_id':entry.order_line_id.id,
						'order_no':entry.order_no,
						'order_delivery_date':entry.order_line_id.delivery_date,
						'order_date':entry.order_id.entry_date,
						'order_category':entry.order_category,
						'order_priority':entry.order_priority,
						'pump_model_id':entry.pump_model_id.id,
						'pattern_id':entry.pattern_id.id,
						'pattern_name':entry.pattern_name,
						'moc_id':entry.moc_id.id,
						'schedule_qty':entry.qty,
						'fettling_qty':entry.qty,
						'inward_accept_qty':entry.qty,
						'state':'waiting',
						'ms_sch_qty': entry.qty,
						'ms_type': 'foundry_item',
						'item_code': entry.pattern_id.code,
						'item_name': entry.pattern_name,
						'position_id': entry.order_bomline_id.position_id.id,
					
					}
					
					ms_id = ms_obj.create(cr, uid, ms_vals)
					
				if entry.stock_type == 'pump':
					
					if entry.sent_to == 'assembly':
					
						for accepted_qty in range(entry.qty):
							
							### Assembly Header Creation ###
							
							ass_header_values = {
								'name': '',
								'order_id': entry.order_id.id,
								'order_line_id': entry.order_line_id.id,
								'pump_model_id': entry.pump_model_id.id,
								'moc_construction_id': entry.moc_construction_id.id,
								'state': 'waiting',
								'entry_mode': 'auto'
								}
							assembly_id = assembly_obj.create(cr, uid, ass_header_values)
							print "assembly_id//////////////////////////",assembly_id
							### Assembly Foundry Items Creation ###
							
							order_bom_ids = self.pool.get('ch.order.bom.details').search(cr, uid, [('header_id','=',entry.order_line_id.id)])
							
							if order_bom_ids:
								for order_item in order_bom_ids:
									order_bom_rec = self.pool.get('ch.order.bom.details').browse(cr, uid, order_item)
									if order_bom_rec.qty == 1:
										order_bom_qty = order_bom_rec.qty
									if order_bom_rec.qty > 1:
										order_bom_qty = order_bom_rec.qty / entry.order_line_id.qty
									
									ass_foundry_vals = {
										'header_id': assembly_id,
										'order_bom_id': order_bom_rec.id,
										'order_bom_qty': order_bom_qty,
										'entry_mode': 'auto'
										}
									print "ass_foundry_vals----------------",ass_foundry_vals
									assembly_foundry_id = assembly_foundry_obj.create(cr, uid, ass_foundry_vals)
								
							### Assembly MS Items Creation ###
							
							order_ms_ids = self.pool.get('ch.order.machineshop.details').search(cr, uid, [('header_id','=',entry.order_line_id.id)])
							if order_ms_ids:
								for ms_item in order_ms_ids:
									order_ms_rec = self.pool.get('ch.order.machineshop.details').browse(cr, uid, ms_item)
									if order_ms_rec.qty == 1:
										order_ms_qty = order_ms_rec.qty
									if order_ms_rec.qty > 1:
										order_ms_qty = order_ms_rec.qty / entry.order_line_id.qty
									ass_ms_vals = {
										'header_id': assembly_id,
										'order_ms_id': order_ms_rec.id,
										'order_ms_qty': order_ms_qty,
										'entry_mode': 'auto'
									}
									print "ass_ms_vals----------------",ass_ms_vals
									assembly_ms_id = assembly_ms_obj.create(cr, uid, ass_ms_vals)	
							
							### Assembly BOT Items Creation ###
							
							order_bot_ids = self.pool.get('ch.order.bot.details').search(cr, uid, [('header_id','=',entry.order_line_id.id)])
							if order_bot_ids:
								for bot_item in order_bot_ids:
									order_bot_rec = self.pool.get('ch.order.bot.details').browse(cr, uid, bot_item)
									
									if order_bot_rec.qty == 1:
										order_bot_qty = order_bot_rec.qty
									if order_bot_rec.qty > 1:
										order_bot_qty = order_bot_rec.qty / entry.order_line_id.qty
									ass_bot_vals = {
									'header_id': assembly_id,
									'order_bot_id': order_bot_rec.id,
									'order_bot_qty': order_bot_qty,
									}
									print "ass_bot_vals----------------",ass_bot_vals
									assembly_bot_id = assembly_bot_obj.create(cr, uid, ass_bot_vals)

			### Creating QC or Stock Allocation When Rejection
			
			if reject_qty > 0:
				
				if entry.stock_type == 'part':
				
					reject_rem_qty = reject_qty
						
					### Checking in Stock Inward for Ready for MS ###
					
					cr.execute(""" select sum(available_qty) as stock_qty
						from ch_stock_inward_details  
						where pattern_id = %s and moc_id = %s
						and foundry_stock_state = 'ready_for_ms' and available_qty > 0 and stock_type = 'pattern'  """%(entry.pattern_id.id,entry.moc_id.id))
					stock_inward_qty = cr.fetchone();
					
					if stock_inward_qty:
						if stock_inward_qty[0] != None:
							reject_rem_qty =  reject_qty - stock_inward_qty[0]
							
							if reject_rem_qty <= 0:
								reject_rem_qty = 0
								qc_qty = reject_qty
							else:
								reject_rem_qty = reject_rem_qty
								qc_qty = stock_inward_qty[0]
							
							### Creating QC Verification ###
							
							qc_obj = self.pool.get('kg.qc.verification')
							
							### QC Sequence Number Generation  ###
							qc_name = ''    
							qc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.qc.verification')])
							rec = self.pool.get('ir.sequence').browse(cr,uid,qc_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(qc_seq_id[0],rec.code,entry.entry_date))
							qc_name = cr.fetchone();
						
							qc_vals = {
															
								'name': qc_name[0],
								'schedule_id': entry.schedule_id.id,
								'schedule_date': entry.schedule_date,
								'division_id': entry.division_id.id,
								'location' : entry.location,
								'schedule_line_id': entry.schedule_line_id.id,
								'order_id': entry.order_id.id,
								'order_line_id': entry.order_line_id.id,
								'pump_model_id': entry.pump_model_id.id,
								'qty' : qc_qty,
								'stock_qty':qc_qty,                
								'allocated_qty':qc_qty,              
								'state' : 'draft',
								'order_category':entry.order_category,
								'order_priority':entry.order_priority,
								'pattern_id' : entry.pattern_id.id,
								'pattern_name' : entry.pattern_id.pattern_name, 
								'moc_id' : entry.moc_id.id,
								'stock_type': 'pattern'
										
								}
							
							qc_id = qc_obj.create(cr, uid, qc_vals)
							
							### Qty Updation in Stock Inward ###
							
							inward_line_obj = self.pool.get('ch.stock.inward.details')
							
							cr.execute(""" select id,available_qty
								from ch_stock_inward_details  
								where pattern_id = %s and moc_id = %s
								and foundry_stock_state = 'ready_for_ms' 
								and available_qty > 0 and stock_type = 'pattern' """%(entry.pattern_id.id,entry.moc_id.id))
								
							stock_inward_items = cr.dictfetchall();
							
							stock_updation_qty = qc_qty
							
							
							for stock_inward_item in stock_inward_items:
								if stock_updation_qty > 0:
									
									if stock_inward_item['available_qty'] <= stock_updation_qty:
										stock_avail_qty = 0
										inward_line_obj.write(cr, uid, [stock_inward_item['id']],{'available_qty': stock_avail_qty,'foundry_stock_state':'reject'})
									if stock_inward_item['available_qty'] > stock_updation_qty:
										stock_avail_qty = stock_inward_item['available_qty'] - stock_updation_qty
										inward_line_obj.write(cr, uid, [stock_inward_item['id']],{'available_qty': stock_avail_qty})
										
									if stock_inward_item['available_qty'] <= stock_updation_qty:
										stock_updation_qty = stock_updation_qty - stock_inward_item['available_qty']
									elif stock_inward_item['available_qty'] > stock_updation_qty:
										stock_updation_qty = 0
													
									 
					### Checking in Stock Inward for Foundry In Progress ###
					
					cr.execute(""" select sum(available_qty) as stock_qty
						from ch_stock_inward_details  
						where pattern_id = %s and moc_id = %s
						and foundry_stock_state = 'foundry_inprogress' and available_qty > 0 and stock_type = 'pattern'  """%(entry.pattern_id.id,entry.moc_id.id))
					stock_inward_qty = cr.fetchone();
					
					if stock_inward_qty:
						if stock_inward_qty[0] != None:
							
							rem_qty = reject_rem_qty
							
							### Checking STK WO ##
							
							cr.execute(""" select id,order_id,order_line_id,order_no,state,inward_accept_qty,
								stage_id,stage_name,state from kg_fettling where order_id = 
								(select id from kg_work_order where flag_for_stock = 't')
								and pattern_id = %s and moc_id = %s and state != 'complete' """%(entry.pattern_id.id,entry.moc_id.id))
							stk_ids = cr.dictfetchall();
							
							if stk_ids:
							
								for stk_item in stk_ids:
									
									### Qty Updation in Stock Inward ###
								
									inward_line_obj = self.pool.get('ch.stock.inward.details')
									
									cr.execute(""" select id,available_qty
										from ch_stock_inward_details  
										where pattern_id = %s and moc_id = %s
										and foundry_stock_state = 'foundry_inprogress' 
										and available_qty > 0 and stock_type = 'pattern' """%(entry.pattern_id.id,entry.moc_id.id))
										
									stock_inward_items = cr.dictfetchall();
									
									stock_updation_qty = rem_qty
									
									
									for stock_inward_item in stock_inward_items:
										if stock_updation_qty > 0:
											
											if stock_inward_item['available_qty'] <= stock_updation_qty:
												stock_avail_qty = 0
												inward_line_obj.write(cr, uid, [stock_inward_item['id']],{'available_qty': stock_avail_qty,'foundry_stock_state':'reject'})
											if stock_inward_item['available_qty'] > stock_updation_qty:
												stock_avail_qty = stock_inward_item['available_qty'] - stock_updation_qty
												inward_line_obj.write(cr, uid, [stock_inward_item['id']],{'available_qty': stock_avail_qty})
												
											if stock_inward_item['available_qty'] <= stock_updation_qty:
												stock_updation_qty = stock_updation_qty - stock_inward_item['available_qty']
											elif stock_inward_item['available_qty'] > stock_updation_qty:
												stock_updation_qty = 0
													
									
									fettling_obj = self.pool.get('kg.fettling')
									
									stk_item_rec = fettling_obj.browse(cr, uid, stk_item['id'])

									### Sequence Number Generation ###
									fettling_name = ''  
									fettling_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.fettling.inward')])
									seq_rec = self.pool.get('ir.sequence').browse(cr,uid,fettling_seq_id[0])
									cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(fettling_seq_id[0],seq_rec.code))
									fettling_name = cr.fetchone();
									
									fettling_vals = {
										'name': fettling_name[0],
										'location':entry.location,
										'schedule_id':entry.schedule_id.id,
										'schedule_date':entry.schedule_date,
										'schedule_line_id':entry.schedule_line_id.id,
										'order_bomline_id':entry.order_bomline_id.id,
										'order_id':entry.order_id.id,
										'order_line_id':entry.order_line_id.id,
										'order_no':entry.order_no,
										'order_delivery_date':entry.order_delivery_date,
										'order_date':entry.order_date,
										'order_category':entry.order_category,
										'order_priority':entry.order_priority,
										'pump_model_id':entry.pump_model_id.id,
										'pattern_id':entry.pattern_id.id,
										'pattern_code':entry.pattern_code,
										'pattern_name':entry.pattern_name,
										'moc_id':entry.moc_id.id,
										'schedule_qty':rem_qty,
										'production_id':entry.production_id.id,
										'pour_qty':rem_qty,
										'inward_accept_qty': rem_qty,
										'state':'waiting',
										
										}
									   
									fettling_id = fettling_obj.create(cr, uid, fettling_vals)
									
									if stk_item['stage_name'] == None:
										
										### Updation in STK WO ###
										stk_rem_qty =  stk_item_rec.inward_accept_qty - rem_qty
										if stk_rem_qty > 0:
											fettling_obj.write(cr, uid, stk_item['id'], {'inward_accept_qty': stk_rem_qty,'pour_qty':stk_rem_qty})
										else:
											fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
											
										if rem_qty <= stk_item_rec.inward_accept_qty:
											inward_accept_qty = rem_qty
										if rem_qty > stk_item_rec.inward_accept_qty:
											inward_accept_qty = stk_item_rec.inward_accept_qty
											
										fettling_obj.write(cr, uid, fettling_id, {'inward_accept_qty': inward_accept_qty,'allocated_qty':inward_accept_qty,
											'flag_allocated':'t','allocated_accepted_qty':inward_accept_qty,'allocation_state':'waiting'})
											
										allocated_qty = inward_accept_qty
									
									if stk_item['stage_name'] == 'KNOCK OUT':
										
										stk_knockout_qty = stk_item_rec.knockout_qty
										
										if rem_qty <= stk_knockout_qty:
											knockout_qty = rem_qty
										if rem_qty > stk_knockout_qty:
											knockout_qty = stk_knockout_qty

										### Sequence Number Generation ###
										knockout_name = ''  
										knockout_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.knock.out')])
										seq_rec = self.pool.get('ir.sequence').browse(cr,uid,knockout_seq_id[0])
										cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(knockout_seq_id[0],seq_rec.code))
										knockout_name = cr.fetchone();
										fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':knockout_qty,'inward_accept_qty': knockout_qty,
										'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'knockout_date':time.strftime('%Y-%m-%d'),'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0],'allocated_qty':knockout_qty,
												'flag_allocated':'t','allocated_accepted_qty':knockout_qty,'allocation_state':'waiting'})
										
										### Updation in STK WO ###
										stk_rem_qty =  stk_knockout_qty - knockout_qty
										if stk_rem_qty > 0:
											fettling_obj.write(cr, uid, stk_item['id'], {'knockout_qty': stk_rem_qty,'knockout_accept_qty':stk_rem_qty})
										else:
											fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
											
										allocated_qty = knockout_qty
									
									if stk_item['stage_name'] == 'DECORING':
										
										stk_decoring_qty = stk_item_rec.decoring_qty
										
										if rem_qty <= stk_decoring_qty:
											decoring_qty = rem_qty
										if rem_qty > stk_decoring_qty:
											decoring_qty = stk_decoring_qty
										### Sequence Number Generation ###
										decoring_name = ''  
										decoring_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.decoring')])
										seq_rec = self.pool.get('ir.sequence').browse(cr,uid,decoring_seq_id[0])
										cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(decoring_seq_id[0],seq_rec.code))
										decoring_name = cr.fetchone();
										fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':decoring_qty,'inward_accept_qty': decoring_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'decoring_date':time.strftime('%Y-%m-%d'),
										'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0],'allocated_qty':decoring_qty,
												'flag_allocated':'t','allocated_accepted_qty':decoring_qty,'allocation_state':'waiting'})
										
										### Updation in STK WO ###
										stk_rem_qty =  stk_decoring_qty - decoring_qty
										if stk_rem_qty > 0:
											fettling_obj.write(cr, uid, stk_item['id'], {'decoring_qty': stk_rem_qty,'decoring_accept_qty':stk_rem_qty})
										else:
											fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
											
										allocated_qty = decoring_qty
									
									
									if stk_item['stage_name'] == 'SHOT BLAST':
										
										stk_shot_blast_qty = stk_item_rec.shot_blast_qty
										
										if rem_qty <= stk_shot_blast_qty:
											shot_blast_qty = rem_qty
										if rem_qty > stk_shot_blast_qty:
											shot_blast_qty = stk_shot_blast_qty
										### Sequence Number Generation ###
										shot_blast_name = ''    
										shot_blast_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.shot.blast')])
										seq_rec = self.pool.get('ir.sequence').browse(cr,uid,shot_blast_seq_id[0])
										cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(shot_blast_seq_id[0],seq_rec.code))
										shot_blast_name = cr.fetchone();
										fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':shot_blast_qty,'inward_accept_qty': shot_blast_qty,
										'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'shot_blast_date':time.strftime('%Y-%m-%d'),
										'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0],'allocated_qty':shot_blast_qty,
												'flag_allocated':'t','allocated_accepted_qty':shot_blast_qty,'allocation_state':'waiting'})
									
										### Updation in STK WO ###
										stk_rem_qty =  stk_shot_blast_qty - shot_blast_qty
										if stk_rem_qty > 0:
											fettling_obj.write(cr, uid, stk_item['id'], {'shot_blast_qty': stk_rem_qty,'shot_blast_accept_qty':stk_rem_qty})
										else:
											fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
									
										allocated_qty = shot_blast_qty
									
									if stk_item['stage_name'] == 'HAMMERING':
										
										stk_hammering_qty = stk_item_rec.hammering_qty
										
										if rem_qty <= stk_hammering_qty:
											hammering_qty = rem_qty
										if rem_qty > stk_hammering_qty:
											hammering_qty = stk_hammering_qty
										### Sequence Number Generation ###
										hammering_name = '' 
										hammering_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.hammering')])
										seq_rec = self.pool.get('ir.sequence').browse(cr,uid,hammering_seq_id[0])
										cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(hammering_seq_id[0],seq_rec.code))
										hammering_name = cr.fetchone();
										fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':hammering_qty,'inward_accept_qty': hammering_qty,
										'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'hammering_date':time.strftime('%Y-%m-%d'),
										'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0],'allocated_qty':hammering_qty,
											'flag_allocated':'t','allocated_accepted_qty':hammering_qty,'allocation_state':'waiting'})
									
										### Updation in STK WO ###
										stk_rem_qty =  stk_hammering_qty - hammering_qty
										if stk_rem_qty > 0:
											fettling_obj.write(cr, uid, stk_item['id'], {'hammering_qty': stk_rem_qty,'hammering_accept_qty':stk_rem_qty})
										else:
											fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
											
											
										allocated_qty = hammering_qty
									
									if stk_item['stage_name'] == 'WHEEL CUTTING':
										
										stk_wheel_cutting_qty = stk_item_rec.wheel_cutting_qty
										
										if rem_qty <= stk_wheel_cutting_qty:
											wheel_cutting_qty = rem_qty
										if rem_qty > stk_wheel_cutting_qty:
											wheel_cutting_qty = stk_wheel_cutting_qty
										### Sequence Number Generation ###
										wheel_cutting_name = '' 
										wheel_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.wheel.cutting')])
										seq_rec = self.pool.get('ir.sequence').browse(cr,uid,wheel_cutting_seq_id[0])
										cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(wheel_cutting_seq_id[0],seq_rec.code))
										wheel_cutting_name = cr.fetchone();
										fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':wheel_cutting_qty,'inward_accept_qty': wheel_cutting_qty,
										'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'wheel_cutting_date':time.strftime('%Y-%m-%d'),
										'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0],'allocated_qty':wheel_cutting_qty,
											'flag_allocated':'t','allocated_accepted_qty':wheel_cutting_qty,'allocation_state':'waiting'})
									
										### Updation in STK WO ###
										stk_rem_qty =  stk_wheel_cutting_qty - wheel_cutting_qty
										if stk_rem_qty > 0:
											fettling_obj.write(cr, uid, stk_item['id'], {'wheel_cutting_qty': stk_rem_qty,'wheel_cutting_accept_qty':stk_rem_qty})
										else:
											fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
											
										allocated_qty = wheel_cutting_qty
									
									if stk_item['stage_name'] == 'GAS CUTTING':
										
										stk_gas_cutting_qty = stk_item_rec.gas_cutting_qty
										
										if rem_qty <= stk_gas_cutting_qty:
											gas_cutting_qty = rem_qty
										if rem_qty > stk_gas_cutting_qty:
											gas_cutting_qty = stk_gas_cutting_qty
										### Sequence Number Generation ###
										gas_cutting_name = ''   
										gas_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.gas.cutting')])
										seq_rec = self.pool.get('ir.sequence').browse(cr,uid,gas_cutting_seq_id[0])
										cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(gas_cutting_seq_id[0],seq_rec.code))
										gas_cutting_name = cr.fetchone();
										fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':gas_cutting_qty,'inward_accept_qty': gas_cutting_qty,
										'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'gas_cutting_date':time.strftime('%Y-%m-%d'),
										'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0],'allocated_qty':gas_cutting_qty,
											'flag_allocated':'t','allocated_accepted_qty':gas_cutting_qty,'allocation_state':'waiting'})
									
										### Updation in STK WO ###
										stk_rem_qty =  stk_gas_cutting_qty - gas_cutting_qty
										if stk_rem_qty > 0:
											fettling_obj.write(cr, uid, stk_item['id'], {'gas_cutting_qty': stk_rem_qty,'gas_cutting_accept_qty':stk_rem_qty})
										else:
											fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
											
										allocated_qty = gas_cutting_qty
									
									if stk_item['stage_name'] == 'ARC CUTTING':
										
										stk_arc_cutting_qty = stk_item_rec.arc_cutting_qty
										
										if rem_qty <= stk_arc_cutting_qty:
											arc_cutting_qty = rem_qty
										if rem_qty > stk_arc_cutting_qty:
											arc_cutting_qty = stk_arc_cutting_qty
										### Sequence Number Generation ###
										arc_cutting_name = ''   
										arc_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.arc.cutting')])
										seq_rec = self.pool.get('ir.sequence').browse(cr,uid,arc_cutting_seq_id[0])
										cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(arc_cutting_seq_id[0],seq_rec.code))
										arc_cutting_name = cr.fetchone();
										fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':arc_cutting_qty,'inward_accept_qty': arc_cutting_qty,
										'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'arc_cutting_date':time.strftime('%Y-%m-%d'),
										'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0],'allocated_qty':arc_cutting_qty,
											'flag_allocated':'t','allocated_accepted_qty':arc_cutting_qty,'allocation_state':'waiting'})
									
										### Updation in STK WO ###
										stk_rem_qty =  stk_arc_cutting_qty - arc_cutting_qty
										if stk_rem_qty > 0:
											fettling_obj.write(cr, uid, stk_item['id'], {'arc_cutting_qty': stk_rem_qty,'arc_cutting_accept_qty':stk_rem_qty})
										else:
											fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
											
										allocated_qty = arc_cutting_qty
									
									
									if stk_item['stage_name'] == 'HEAT TREATMENT':
										
										stk_heat_qty = stk_item_rec.heat_qty
										
										if rem_qty <= stk_heat_qty:
											heat_total_qty = rem_qty
										if rem_qty > stk_heat_qty:
											heat_total_qty = stk_heat_qty
										### Next Stage Qty ###
										fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':heat_total_qty,'inward_accept_qty': heat_total_qty,
										'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'heat_date':time.strftime('%Y-%m-%d'),
										'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty,'allocated_qty':heat_total_qty,
											'flag_allocated':'t','allocated_accepted_qty':heat_total_qty,'allocation_state':'waiting'})
									
										### Updation in STK WO ###
										stk_rem_qty =  stk_heat_qty - heat_total_qty
										if stk_rem_qty > 0:
											fettling_obj.write(cr, uid, stk_item['id'], {'heat_total_qty': stk_rem_qty,'heat_qty':stk_rem_qty,})
										else:
											fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
											
											
										allocated_qty = heat_total_qty
										
									if stk_item['stage_name'] == 'HEAT TREATMENT2':
										
										stk_heat2_qty = stk_item_rec.heat2_qty
										
										if rem_qty <= stk_heat2_qty:
											heat2_total_qty = rem_qty
										if rem_qty > stk_heat2_qty:
											heat2_total_qty = stk_heat2_qty
										
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':heat2_total_qty,'inward_accept_qty': heat2_total_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'heat_date':time.strftime('%Y-%m-%d'),'heat2_total_qty': heat2_total_qty,'heat2_qty':heat2_total_qty,'allocated_qty':heat2_total_qty,'flag_allocated':'t','allocated_accepted_qty':heat2_total_qty,'allocation_state':'waiting'})
									
										### Updation in STK WO ###
										stk_rem_qty =  stk_heat2_qty - heat2_total_qty
										if stk_rem_qty > 0:
											self.write(cr, uid, stk_item['id'], {'heat2_total_qty': stk_rem_qty,'heat2_qty':stk_rem_qty})
										else:
											self.write(cr, uid, stk_item['id'], {'state':'complete'})
											
											
										allocated_qty = heat2_total_qty
										
									if stk_item['stage_name'] == 'HEAT TREATMENT3':
										
										stk_heat3_qty = stk_item_rec.heat3_qty
										
										if rem_qty <= stk_heat3_qty:
											heat3_total_qty = rem_qty
										if rem_qty > stk_heat3_qty:
											heat3_total_qty = stk_heat3_qty
										
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':heat3_total_qty,'inward_accept_qty': heat3_total_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'heat_date':time.strftime('%Y-%m-%d'),'heat3_total_qty': heat3_total_qty,'heat3_qty':heat3_total_qty,'allocated_qty':heat3_total_qty,'flag_allocated':'t','allocated_accepted_qty':heat3_total_qty,'allocation_state':'waiting'})
									
										### Updation in STK WO ###
										stk_rem_qty =  stk_heat3_qty - heat3_total_qty
										if stk_rem_qty > 0:
											self.write(cr, uid, stk_item['id'], {'heat3_total_qty': stk_rem_qty,'heat3_qty':stk_rem_qty})
										else:
											self.write(cr, uid, stk_item['id'], {'state':'complete'})
											
											
										allocated_qty = heat3_total_qty
									
									
									if stk_item['stage_name'] == 'ROUGH GRINDING':
										
										stk_rough_grinding_qty = stk_item_rec.rough_grinding_qty
										
										if rem_qty <= stk_rough_grinding_qty:
											rough_grinding_qty = rem_qty
										if rem_qty > stk_rough_grinding_qty:
											rough_grinding_qty = stk_rough_grinding_qty
										### Sequence Number Generation ###
										rough_grinding_name = ''    
										rough_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.rough.grinding')])
										seq_rec = self.pool.get('ir.sequence').browse(cr,uid,rough_grinding_seq_id[0])
										cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(rough_grinding_seq_id[0],seq_rec.code))
										rough_grinding_name = cr.fetchone();
										fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':rough_grinding_qty,'inward_accept_qty': rough_grinding_qty,
										'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'rough_grinding_date':time.strftime('%Y-%m-%d'),
										'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,
										'rough_grinding_name':rough_grinding_name[0],'allocated_qty':rough_grinding_qty,
											'flag_allocated':'t','allocated_accepted_qty':rough_grinding_qty,'allocation_state':'waiting'})
									
										### Updation in STK WO ###
										stk_rem_qty =  stk_rough_grinding_qty - rough_grinding_qty
										if stk_rem_qty > 0:
											fettling_obj.write(cr, uid, stk_item['id'], {'rough_grinding_qty': stk_rem_qty,'rough_grinding_accept_qty':stk_rem_qty})
										else:
											fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
											
										allocated_qty = rough_grinding_qty
									
									if stk_item['stage_name'] == 'FINISH GRINDING':
										
										stk_finish_grinding_qty = stk_item_rec.finish_grinding_qty
										
										if rem_qty <= stk_finish_grinding_qty:
											finish_grinding_qty = rem_qty
										if rem_qty > stk_finish_grinding_qty:
											finish_grinding_qty = stk_finish_grinding_qty
										### Sequence Number Generation ###
										finish_grinding_name = ''   
										finish_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.finish.grinding')])
										seq_rec = self.pool.get('ir.sequence').browse(cr,uid,finish_grinding_seq_id[0])
										cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(finish_grinding_seq_id[0],seq_rec.code))
										finish_grinding_name = cr.fetchone();
										fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':finish_grinding_qty,'inward_accept_qty': finish_grinding_qty,
										'pour_qty':finish_grinding_qty,'inward_accept_qty': finish_grinding_qty,'stage_id':stk_item['stage_id'],
										'stage_name':stk_item['stage_name'],'finish_grinding_date':time.strftime('%Y-%m-%d'),'finish_grinding_qty': finish_grinding_qty,
										'finish_grinding_accept_qty': finish_grinding_qty,'finish_grinding_name':finish_grinding_name[0],'allocated_qty':finish_grinding_qty,
											'flag_allocated':'t','allocated_accepted_qty':finish_grinding_qty,'allocation_state':'waiting'})
										
										### Updation in STK WO ###
										stk_rem_qty =  stk_finish_grinding_qty - finish_grinding_qty
										if stk_rem_qty > 0:
											fettling_obj.write(cr, uid, stk_item['id'], {'finish_grinding_qty': stk_rem_qty,'finish_grinding_accept_qty':stk_rem_qty})
										else:
											fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
											
										allocated_qty = finish_grinding_qty
									
									
									if stk_item['stage_name'] == 'RE SHOT BLASTING':
										
										stk_reshot_blasting_qty = stk_item_rec.reshot_blasting_qty
										
										if rem_qty <= stk_reshot_blasting_qty:
											reshot_blasting_qty = rem_qty
										if rem_qty > stk_reshot_blasting_qty:
											reshot_blasting_qty = stk_reshot_blasting_qty
										### Sequence Number Generation ###
										reshot_blasting_name = ''   
										reshot_blasting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.reshot.blasting')])
										seq_rec = self.pool.get('ir.sequence').browse(cr,uid,reshot_blasting_seq_id[0])
										cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(reshot_blasting_seq_id[0],seq_rec.code))
										reshot_blasting_name = cr.fetchone();
										fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':reshot_blasting_qty,'inward_accept_qty': reshot_blasting_qty,
										'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'reshot_blasting_date':time.strftime('%Y-%m-%d'),
										'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0],'allocated_qty':reshot_blasting_qty,
											'flag_allocated':'t','allocated_accepted_qty':reshot_blasting_qty,'allocation_state':'waiting'})
								
										### Updation in STK WO ###
										stk_rem_qty =  stk_reshot_blasting_qty - reshot_blasting_qty
										if stk_rem_qty > 0:
											fettling_obj.write(cr, uid, stk_item['id'], {'reshot_blasting_qty': stk_rem_qty,'reshot_blasting_accept_qty':stk_rem_qty})
										else:
											fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
											
										allocated_qty = reshot_blasting_qty
										
									if stk_item['stage_name'] == 'WELDING':
										
										stk_welding_qty = stk_item_rec.welding_qty
										
										if rem_qty <= stk_welding_qty:
											welding_qty = rem_qty
										if rem_qty > stk_welding_qty:
											welding_qty = stk_welding_qty
										### Sequence Number Generation ###
										welding_name = ''   
										welding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.welding')])
										seq_rec = self.pool.get('ir.sequence').browse(cr,uid,welding_seq_id[0])
										cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(welding_seq_id[0],seq_rec.code))
										welding_name = cr.fetchone();
										fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':welding_qty,'inward_accept_qty': welding_qty,'stage_id':stk_item['stage_id'],
										'stage_name':stk_item['stage_name'],'welding_date':time.strftime('%Y-%m-%d'),
										'welding_qty': welding_qty,'welding_accept_qty': welding_qty,
										'welding_name':welding_name[0],'allocated_qty':welding_qty,
											'flag_allocated':'t','allocated_accepted_qty':welding_qty,'allocation_state':'waiting'})
								
										### Updation in STK WO ###
										stk_rem_qty =  stk_welding_qty - welding_qty
										if stk_rem_qty > 0:
											fettling_obj.write(cr, uid, stk_item['id'], {'welding_qty': stk_rem_qty,'welding_accept_qty':stk_rem_qty})
										else:
											fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
											
										allocated_qty = welding_qty
									
									rem_qty = rem_qty - allocated_qty
							
						else:
							rem_qty = reject_rem_qty
						
						if rem_qty > 0:
							
							#### NC Creation for reject Qty ###
							
							### Production Number ###
							produc_name = ''    
							produc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.production')])
							rec = self.pool.get('ir.sequence').browse(cr,uid,produc_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(produc_seq_id[0],rec.code,entry.entry_date))
							produc_name = cr.fetchone();
							
							### Issue Number ###
							issue_name = '' 
							issue_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pattern.issue')])
							rec = self.pool.get('ir.sequence').browse(cr,uid,issue_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(issue_seq_id[0],rec.code,entry.entry_date))
							issue_name = cr.fetchone();
							
							### Core Log Number ###
							core_name = ''  
							core_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.log')])
							rec = self.pool.get('ir.sequence').browse(cr,uid,core_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_seq_id[0],rec.code,entry.entry_date))
							core_name = cr.fetchone();
							
							### Mould Log Number ###
							mould_name = '' 
							mould_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.log')])
							rec = self.pool.get('ir.sequence').browse(cr,uid,mould_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_seq_id[0],rec.code,entry.entry_date))
							mould_name = cr.fetchone();
							
							if entry.order_id.flag_for_stock == False:
							
								production_vals = {
														
									'name': produc_name[0],
									'schedule_id': entry.schedule_id.id,
									'schedule_date': entry.schedule_date,
									'division_id': entry.division_id.id,
									'location' : entry.location,
									'schedule_line_id': entry.schedule_line_id.id,
									'order_id': entry.order_id.id,
									'order_line_id': entry.order_line_id.id,
									'qty' : rem_qty,              
									'schedule_qty' : rem_qty,            
									'state' : 'issue_done',
									'order_category':entry.order_category,
									'order_priority': '2',
									'pattern_id' : entry.pattern_id.id,
									'pattern_name' : entry.pattern_id.pattern_name, 
									'moc_id' : entry.moc_id.id,
									'request_state': 'done',
									'issue_no': issue_name[0],
									'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
									'issue_qty': 1,
									'issue_state': 'issued',
									'core_no': core_name[0],
									'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
									'core_qty': rem_qty,
									'core_rem_qty': rem_qty,
									'core_state': 'pending',
									'mould_no': mould_name[0],
									'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
									'mould_qty': rem_qty,
									'mould_rem_qty': rem_qty,
									'mould_state': 'pending',      
								}
								production_id = production_obj.create(cr, uid, production_vals)
				
				order_line_ids = []
				if entry.stock_type == 'pump':
					
					pump_rem_qty = entry.order_line_id.qty - entry.qty
					
					self.pool.get('ch.work.order.details').write(cr, uid, entry.order_line_id.id, {'pump_rem_qty':pump_rem_qty})
					
					if pump_rem_qty > 0:				
						order_line_ids.append(entry.order_line_id.id)
						
						### Schedule Creation ###
					
						schedule_item_vals = {
														
							'name': '',
							'location' : entry.location,
							'order_priority': 'normal',
							'delivery_date': entry.order_line_id.delivery_date,
							'order_line_ids': [(6, 0, order_line_ids)],
							'state' : 'draft',
							'entry_mode' : 'auto',				   
						}
						
						schedule_id = self.pool.get('kg.schedule').create(cr, uid, schedule_item_vals)
						
						### Schedule Line Item Creation ###
						
						self.pool.get('kg.schedule').update_line_items(cr, uid, [schedule_id],pump_rem_qty)
						
						### Schedule Confirmation ###
						
						self.pool.get('kg.schedule').entry_confirm(cr, uid, [schedule_id])
				
			if reject_qty > 0:
				
				### Entry Creation in Foundry Rejection List ###
				foundry_rejection_obj = self.pool.get('kg.foundry.rejection.list')
				
				rejection_vals = {
					
					'division_id': entry.division_id.id,
					'location': entry.location,
					'order_id': entry.order_id.id,
					'order_line_id': entry.order_line_id.id,
					'order_priority': entry.order_priority,
					'pattern_id': entry.pattern_id.id,
					'moc_id': entry.moc_id.id,
					'stage_id':entry.stage_id.id,
					'stage_name': 'QC Verification',
					'qty': reject_qty,
					'each_weight': entry.each_weight,
					'reject_remarks_id': entry.reject_remarks_id.id
				}
				
				foundry_rejection_id = foundry_rejection_obj.create(cr, uid, rejection_vals)	
			
			
			
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		
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









