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

class kg_part_qap(osv.osv):

	_name = "kg.part.qap"
	_description = "Part QAP"
	_order = "entry_date desc"
	
	
	_columns = {
	
		## Version 0.1
	
		## Basic Info
				
		'name': fields.char('Dynamic Balancing No', size=12,select=True,readonly=True),
		'entry_date': fields.date('Date',required=True),		
		'note': fields.text('Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_sms': fields.boolean('SMS Notification'),
		'flag_email': fields.boolean('Email Notification'),
		'flag_spl_approve': fields.boolean('Special Approval'),
		'pump_serial_no': fields.char('Pump Serial No.'),
		
		### Entry Info ####
			
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True), 
		'active': fields.boolean('Active'), 
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),	   
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),	 
		'ap_rej_date': fields.datetime('Approved/Reject Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Reject By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),		   
		
		## Module Requirement Info
		
		
		'qap_plan_id': fields.many2one('kg.qap.plan', 'QAP Standard',readonly=True,required=True),
		'order_id': fields.many2one('kg.work.order','Work Order',required=True),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line',required=True),
		'order_no': fields.related('order_line_id','order_no', type='char', string='WO No.', store=True, readonly=True,required=True),
		'order_category': fields.related('order_line_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Order Category', store=True, readonly=True,required=True),
		'order_bom_id': fields.many2one('ch.order.bom.details','Foundry Item'),
		'pump_model_id': fields.related('order_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No', readonly=True,required=True),
		'pattern_name': fields.char('Pattern Name',readonly=True,required=True),
		'item_code': fields.char('Item Code', readonly=True,required=True),
		'item_name': fields.char('Item Name', readonly=True,required=True),
		'moc_id': fields.many2one('kg.moc.master','MOC', readonly=True,required=True),
		'assembly_id': fields.many2one('kg.assembly.inward','Assembly', readonly=True,required=True),
		'assembly_foundry_id': fields.many2one('ch.assembly.bom.details','Assembly Foundry', readonly=True,required=True),
		
	
		
		## Dynamic Balancing ##
		
		'db_date': fields.date('Date',required=True),   
		'db_min_weight': fields.float('Min Weight' ,required=True),
		'db_max_weight': fields.float('Max Weight' ,required=True),
		'db_actual_unbal_weight': fields.float('Actual Un Balanced Weight in (gms)' ),
		'db_machinery_id': fields.many2one('kg.machinery.master','Machinery'),
		'db_shift_id': fields.many2one('kg.shift.master','Shift'),
		'db_operator': fields.char('Operator'),
		'db_verified_by': fields.char('Verified By'),
		'db_result': fields.selection([('accept','Accept'),('reject','Reject')],'Result'),
		'db_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'db_remarks': fields.text('Remarks'),
		'flag_db_customer_specific': fields.boolean('Customer Specific'),
		'db_state': fields.selection([('pending','Pending'),('completed','Completed')],'DB State'),
		'db_flag': fields.boolean('DB Staus in Pattern'),
		
		## Hydro Static Test ##
		
		'hs_date': fields.date('Date',required=True),   
		'hs_pressure': fields.float('Hydro static test pressure (Kg/cm2)' ),
		'hs_testing_time': fields.selection([('0.30','0.5'),('0.45','0.75'),('1','1'),('1.15','1.15'),('1.30','1.30'),('1.45','1.45'),('2','2')],
						'Testing time (Hrs)'),
		'hs_actual_unbal_weight': fields.float('Actual Un Balanced Weight in (gms)' ),
		'hs_machinery_id': fields.many2one('kg.machinery.master','Machinery'),
		'hs_shift_id': fields.many2one('kg.shift.master','Shift'),
		'hs_operator': fields.char('Operator'),
		'hs_verified_by': fields.char('Verified By'),
		'hs_result': fields.selection([('accept','Accept'),('reject','Reject'),('leak','Leak')],'Result'),
		'hs_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'hs_leak_remarks': fields.char('Leak Remarks'),
		'hs_action': fields.char('Action to be taken'),
		'hs_remarks': fields.text('Remarks'),
		'flag_hs_customer_specific': fields.boolean('Customer Specific'),
		'hs_state': fields.selection([('pending','Pending'),('completed','Completed')],'HS State'),
		'hs_flag': fields.boolean('HS Staus in Pattern'),
	
				
	}
		
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_part_qap', context=c),		   
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',	   
		'active': True,
		'entry_mode': 'manual',	 
		'flag_sms': False,	  
		'flag_email': False,		
		'flag_spl_approve': False,
		'db_date':  lambda * a: time.strftime('%Y-%m-%d'),
		'db_state':  'pending',
		'hs_date':  lambda * a: time.strftime('%Y-%m-%d'),
		'hs_state':  'pending',
		'db_flag':  False,
		'hs_flag':  False,
		
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
	   
	def reject_process(self,cr,uid,ids,reject_qty,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		if reject_qty > 0:
			
			if entry.order_id.flag_for_stock == False:
			
				reject_rem_qty = reject_qty
			
				### Checking in Stock Inward for Ready for MS ###
				
				cr.execute(""" select id,available_qty as stock_qty,stock_location_id 
					from ch_stock_inward_details  
					where pattern_id = %s and moc_id = %s
					and  foundry_stock_state = 'ready_for_ms' and available_qty > 0 and stock_type = 'pattern'  """%(entry.pattern_id.id,entry.moc_id.id))
				stock_inward_items = cr.dictfetchall();
				
				if stock_inward_items:
					print "reject_rem_qty",reject_rem_qty
					if reject_rem_qty > 0:
						for stock_item in  stock_inward_items:
							if reject_rem_qty > 0:
								if stock_item['stock_qty'] != None:
									allocate_qty =  reject_rem_qty - stock_item['stock_qty']
									
									if allocate_qty <= 0:
										qc_qty = reject_rem_qty
										reject_rem_qty = 0
									else:
										reject_rem_qty = allocate_qty
										qc_qty = stock_item['stock_qty']
										
									
									### Creating QC Verification ###
									
									qc_obj = self.pool.get('kg.qc.verification')
									
									### QC Sequence Number Generation  ###
									qc_name = ''	
									qc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.qc.verification')])
									rec = self.pool.get('ir.sequence').browse(cr,uid,qc_seq_id[0])
									cr.execute("""select generatesequenceno(%s,'%s','%s') """%(qc_seq_id[0],rec.code,entry.entry_date))
									qc_name = cr.fetchone();
									
									### Order Priority ###
														
									if entry.order_id.order_category in ('pump','pump_spare','project'):
										if entry.order_id.order_priority == 'normal':
											priority = '6'
										if entry.order_id.order_priority == 'emergency':
											priority = '4'
									if entry.order_id.order_category == 'service':
										priority = '3'
									if entry.order_id.order_category == 'spare':
										priority = '5'
									qc_vals = {
																	
										'name': qc_name[0],
										'division_id': entry.order_id.division_id.id,
										'location' : entry.order_id.location,
										'order_id': entry.order_id.id,
										'order_line_id': entry.order_line_id.id,
										'pump_model_id': entry.pump_model_id.id,
										'qty' : qc_qty,
										'stock_qty':qc_qty,		  
										'allocated_qty':qc_qty,		
										'state' : 'draft',
										'order_category':entry.order_category,
										'order_priority':priority,
										'pattern_id' : entry.pattern_id.id,
										'pattern_name' : entry.pattern_id.pattern_name, 
										'moc_id' : entry.moc_id.id,
										'stock_type': 'pattern',
										'order_bomline_id': entry.assembly_foundry_id.order_bom_id.id,
										'stock_location_id': stock_item['stock_location_id'],
										'stock_inward_id': stock_item['id']
												
										}
									
									qc_id = qc_obj.create(cr, uid, qc_vals)
									
									### Qty Updation in Stock Inward ###
											
									inward_line_obj = self.pool.get('ch.stock.inward.details')
									
									stock_updation_qty = qc_qty
									
									if stock_updation_qty > 0:
										
										if stock_item['stock_qty'] <= stock_updation_qty:
											stock_avail_qty = 0
											inward_line_obj.write(cr, uid, [stock_item['id']],{'available_qty': stock_avail_qty})
										if stock_item['stock_qty'] > stock_updation_qty:
											stock_avail_qty = stock_item['stock_qty'] - stock_updation_qty
											inward_line_obj.write(cr, uid, [stock_item['id']],{'available_qty': stock_avail_qty})
										
							
						
				### Checking in Stock Inward for Foundry In Progress ###
			
				cr.execute(""" select sum(available_qty) as stock_qty
					from ch_stock_inward_details  
					where pattern_id = %s and moc_id = %s
					and  foundry_stock_state = 'foundry_inprogress' and available_qty > 0  and stock_type = 'pattern' """%(entry.pattern_id.id,entry.moc_id.id))
				stock_inward_qty = cr.fetchone();
				
				rem_qty = reject_rem_qty
				if stock_inward_qty:
					if stock_inward_qty[0] != None:
						
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
									and  foundry_stock_state = 'foundry_inprogress' 
									and available_qty > 0 and stock_type = 'pattern' """%(entry.pattern_id.id,entry.moc_id.id))
									
								stock_inward_items = cr.dictfetchall();
								
								stock_updation_qty = rem_qty
								
								for stock_inward_item in stock_inward_items:
									if stock_updation_qty > 0:
										
										if stock_inward_item['available_qty'] <= stock_updation_qty:
											stock_avail_qty = 0
											inward_line_obj.write(cr, uid, [stock_inward_item['id']],{'available_qty': stock_avail_qty})
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
									'location':entry.order_id.location,
									'order_bomline_id':entry.order_bomline_id.id,
									'order_id':entry.order_id.id,
									'order_line_id':entry.order_line_id.id,
									'order_no':entry.order_no,
									'order_delivery_date':entry.order_id.order_delivery_date,
									'order_date':entry.order_date,
									'order_category':entry.order_category,
									'order_priority':entry.order_id.order_priority,
									'pump_model_id':entry.pump_model_id.id,
									'pattern_id':entry.pattern_id.id,
									'pattern_code':entry.pattern_code,
									'pattern_name':entry.pattern_name,
									'moc_id':entry.moc_id.id,
									'schedule_qty':rem_qty,
									'pour_qty':rem_qty,
									'inward_accept_qty': rem_qty,
									'state':'waiting',
									}
								   
								fettling_id = fettling_obj.create(cr, uid, fettling_vals)
								
								
								if stk_item['stage_name'] == None:
									
									### Updation in STK WO ###
									stk_rem_qty =  stk_item_rec.inward_accept_qty - rem_qty
									
									if stk_rem_qty > 0:
										self.write(cr, uid, stk_item['id'], {'inward_accept_qty': stk_rem_qty,'pour_qty':stk_rem_qty})
									else:
										self.write(cr, uid, stk_item['id'], {'state':'complete'})
										
									if rem_qty <= stk_item_rec.inward_accept_qty:
										inward_accept_qty = rem_qty
									if rem_qty > stk_item_rec.inward_accept_qty:
										inward_accept_qty = stk_item_rec.inward_accept_qty
										
									self.write(cr, uid, fettling_id, {'inward_accept_qty': inward_accept_qty,'allocated_qty':inward_accept_qty,
									'flag_allocated':'t'})
										
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
									self.write(cr, uid, fettling_id, {'state':'accept','stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'knockout_date':time.strftime('%Y-%m-%d'),
									'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0],
									'allocated_qty':knockout_qty,'flag_allocated':'t','allocated_accepted_qty':knockout_qty,'allocation_state':'waiting'})
									
									### Updation in STK WO ###
									stk_rem_qty =  stk_knockout_qty - knockout_qty
									if stk_rem_qty > 0:
										self.write(cr, uid, stk_item['id'], {'knockout_qty': stk_rem_qty,'knockout_accept_qty':stk_rem_qty})
									else:
										self.write(cr, uid, stk_item['id'], {'state':'complete'})
										
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
									self.write(cr, uid, fettling_id, {'state':'accept','stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'decoring_date':time.strftime('%Y-%m-%d'),'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0],'allocated_qty':decoring_qty,'flag_allocated':'t','allocated_accepted_qty':decoring_qty,'allocation_state':'waiting'})
									
									### Updation in STK WO ###
									stk_rem_qty =  stk_decoring_qty - decoring_qty
									if stk_rem_qty > 0:
										self.write(cr, uid, stk_item['id'], {'decoring_qty': stk_rem_qty,'decoring_accept_qty':stk_rem_qty})
									else:
										self.write(cr, uid, stk_item['id'], {'state':'complete'})
									
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
									self.write(cr, uid, fettling_id, {'state':'accept','stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'shot_blast_date':time.strftime('%Y-%m-%d'),'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0],'allocated_qty':shot_blast_qty,'flag_allocated':'t','allocated_accepted_qty':shot_blast_qty,'allocation_state':'waiting'})
								
									### Updation in STK WO ###
									stk_rem_qty =  stk_shot_blast_qty - shot_blast_qty
									if stk_rem_qty > 0:
										self.write(cr, uid, stk_item['id'], {'shot_blast_qty': stk_rem_qty,'shot_blast_accept_qty':stk_rem_qty})
									else:
										self.write(cr, uid, stk_item['id'], {'state':'complete'})
								
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
									self.write(cr, uid, fettling_id, {'state':'accept','stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'hammering_date':time.strftime('%Y-%m-%d'),'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0],'allocated_qty':hammering_qty,'flag_allocated':'t','allocated_accepted_qty':hammering_qty,'allocation_state':'waiting'})
								
									### Updation in STK WO ###
									stk_rem_qty =  stk_hammering_qty - hammering_qty
									if stk_rem_qty > 0:
										self.write(cr, uid, stk_item['id'], {'hammering_qty': stk_rem_qty,'hammering_accept_qty':stk_rem_qty})
									else:
										self.write(cr, uid, stk_item['id'], {'state':'complete'})
										
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
									self.write(cr, uid, fettling_id, {'state':'accept','stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'wheel_cutting_date':time.strftime('%Y-%m-%d'),'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0],'allocated_qty':wheel_cutting_qty,'flag_allocated':'t','allocated_accepted_qty':wheel_cutting_qty,'allocation_state':'waiting'})
								
									### Updation in STK WO ###
									stk_rem_qty =  stk_wheel_cutting_qty - wheel_cutting_qty
									if stk_rem_qty > 0:
										self.write(cr, uid, stk_item['id'], {'wheel_cutting_qty': stk_rem_qty,'wheel_cutting_accept_qty':stk_rem_qty})
									else:
										self.write(cr, uid, stk_item['id'], {'state':'complete'})
										
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
									self.write(cr, uid, fettling_id, {'state':'accept','stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'gas_cutting_date':time.strftime('%Y-%m-%d'),'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0],'allocated_qty':gas_cutting_qty,'flag_allocated':'t','allocated_accepted_qty':gas_cutting_qty,'allocation_state':'waiting'})
								
									### Updation in STK WO ###
									stk_rem_qty =  stk_gas_cutting_qty - gas_cutting_qty
									if stk_rem_qty > 0:
										self.write(cr, uid, stk_item['id'], {'gas_cutting_qty': stk_rem_qty,'gas_cutting_accept_qty':stk_rem_qty})
									else:
										self.write(cr, uid, stk_item['id'], {'state':'complete'})
										
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
									self.write(cr, uid, fettling_id, {'state':'accept','stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'arc_cutting_date':time.strftime('%Y-%m-%d'),'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0],'allocated_qty':arc_cutting_qty,'flag_allocated':'t','allocated_accepted_qty':arc_cutting_qty,'allocation_state':'waiting'})
								
									### Updation in STK WO ###
									stk_rem_qty =  stk_arc_cutting_qty - arc_cutting_qty
									if stk_rem_qty > 0:
										self.write(cr, uid, stk_item['id'], {'arc_cutting_qty': stk_rem_qty,'arc_cutting_accept_qty':stk_rem_qty})
									else:
										self.write(cr, uid, stk_item['id'], {'state':'complete'})
										
									allocated_qty = arc_cutting_qty
								
								
								if stk_item['stage_name'] == 'HEAT TREATMENT1':
									
									stk_heat_qty = stk_item_rec.heat_qty
									
									if rem_qty <= stk_heat_qty:
										heat_total_qty = rem_qty
									if rem_qty > stk_heat_qty:
										heat_total_qty = stk_heat_qty
									
									self.write(cr, uid, fettling_id, {'state':'accept','stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'heat_date':time.strftime('%Y-%m-%d'),'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty,'allocated_qty':heat_total_qty,'flag_allocated':'t','allocated_accepted_qty':heat_total_qty,'allocation_state':'waiting'})
								
									### Updation in STK WO ###
									stk_rem_qty =  stk_heat_qty - heat_total_qty
									if stk_rem_qty > 0:
										self.write(cr, uid, stk_item['id'], {'heat_total_qty': stk_rem_qty,'heat_qty':stk_rem_qty})
									else:
										self.write(cr, uid, stk_item['id'], {'state':'complete'})
										
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
									self.write(cr, uid, fettling_id, {'state':'accept','stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'rough_grinding_date':time.strftime('%Y-%m-%d'),'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,'rough_grinding_name':rough_grinding_name[0],'allocated_qty':rough_grinding_qty,'flag_allocated':'t','allocated_accepted_qty':rough_grinding_qty,'allocation_state':'waiting'})
								
									### Updation in STK WO ###
									stk_rem_qty =  stk_rough_grinding_qty - rough_grinding_qty
									if stk_rem_qty > 0:
										self.write(cr, uid, stk_item['id'], {'rough_grinding_qty': stk_rem_qty,'rough_grinding_accept_qty':stk_rem_qty})
									else:
										self.write(cr, uid, stk_item['id'], {'state':'complete'})
										
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
									self.write(cr, uid, fettling_id, {'state':'accept','stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'finish_grinding_date':time.strftime('%Y-%m-%d'),'finish_grinding_qty': finish_grinding_qty,'finish_grinding_accept_qty': finish_grinding_qty,'finish_grinding_name':finish_grinding_name[0],'allocated_qty':finish_grinding_qty,'flag_allocated':'t','allocated_accepted_qty':finish_grinding_qty,'allocation_state':'waiting'})
									
									### Updation in STK WO ###
									stk_rem_qty =  stk_finish_grinding_qty - finish_grinding_qty
									if stk_rem_qty > 0:
										self.write(cr, uid, stk_item['id'], {'finish_grinding_qty': stk_rem_qty,'finish_grinding_accept_qty':stk_rem_qty})
									else:
										self.write(cr, uid, stk_item['id'], {'state':'complete'})
										
									allocated_qty = finish_grinding_qty
								
								
								if stage_item['stage_name'] == 'RE SHOT BLASTING':
									
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
									self.write(cr, uid, fettling_id, {'state':'accept','stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'reshot_blasting_date':time.strftime('%Y-%m-%d'),'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0],'allocated_qty':reshot_blasting_qty,'flag_allocated':'t','allocated_accepted_qty':reshot_blasting_qty,'allocation_state':'waiting'})
							
									### Updation in STK WO ###
									stk_rem_qty =  stk_reshot_blasting_qty - reshot_blasting_qty
									if stk_rem_qty > 0:
										self.write(cr, uid, stk_item['id'], {'reshot_blasting_qty': stk_rem_qty,'reshot_blasting_accept_qty':stk_rem_qty})
									else:
										self.write(cr, uid, stk_item['id'], {'state':'complete'})
										
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
									self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':welding_qty,'inward_accept_qty': welding_qty,'stage_id':stk_item['stage_id'],
									'stage_name':stk_item['stage_name'],'welding_date':time.strftime('%Y-%m-%d'),
									'welding_qty': welding_qty,'welding_accept_qty': welding_qty,
									'welding_name':welding_name[0],'allocated_qty':welding_qty,'flag_allocated':'t','allocated_accepted_qty':welding_qty,'allocation_state':'waiting'})
							
									### Updation in STK WO ###
									stk_rem_qty =  stk_welding_qty - welding_qty
									if stk_rem_qty > 0:
										self.write(cr, uid, stk_item['id'], {'welding_qty': stk_rem_qty,'welding_accept_qty':stk_rem_qty})
									else:
										self.write(cr, uid, stk_item['id'], {'state':'complete'})
										
									allocated_qty = welding_qty
								
								rem_qty = rem_qty - allocated_qty
					
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
								'division_id': entry.order_id.division_id.id,
								'location' : entry.order_id.location,
								'order_id': entry.order_id.id,
								'order_line_id': entry.order_line_id.id,
								'order_bomline_id': entry.order_bom_id.id,
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
								'assembly_id': entry.assembly_id.id,
								'assembly_line_id': entry.assembly_foundry_id.id,
							}
							production_id = production_obj.create(cr, uid, production_vals)
	
			else:
				
				### Qty Updation in Stock Inward ###
						
				inward_line_obj = self.pool.get('ch.stock.inward.details')
				
				cr.execute(""" select id,available_qty
					from ch_stock_inward_details  
					where pattern_id = %s and moc_id = %s
					and  foundry_stock_state = 'foundry_inprogress'
					and available_qty > 0 and stock_type = 'pattern' """%(entry.pattern_id.id,entry.moc_id.id))
					
				stock_inward_items = cr.dictfetchall();
				stock_updation_qty = reject_qty
				
				for stock_inward_item in stock_inward_items:
					if stock_updation_qty > 0:
						
						if stock_inward_item['available_qty'] <= stock_updation_qty:
							stock_avail_qty = 0
							inward_line_obj.write(cr, uid, [stock_inward_item['id']],{'available_qty': stock_avail_qty})
						if stock_inward_item['available_qty'] > stock_updation_qty:
							stock_avail_qty = stock_inward_item['available_qty'] - stock_updation_qty
							inward_line_obj.write(cr, uid, [stock_inward_item['id']],{'available_qty': stock_avail_qty})
							
						if stock_inward_item['available_qty'] <= stock_updation_qty:
							stock_updation_qty = stock_updation_qty - stock_inward_item['available_qty']
						elif stock_inward_item['available_qty'] > stock_updation_qty:
							stock_updation_qty = 0

		return True
	   

	def db_update(self,cr,uid,ids,context=None):
		assembly_obj = self.pool.get('kg.assembly.inward')
		ass_foundry_obj = self.pool.get('ch.assembly.bom.details')
		rec = self.browse(cr,uid,ids[0])		
		
		### Validations  ###
		### Actual weight checking ###
		cr.execute(''' 
				select db_actual_unbal_weight from kg_part_qap where id = %s
				and db_actual_unbal_weight BETWEEN db_min_weight AND db_max_weight and db_actual_unbal_weight <= db_max_weight ''',[rec.id])
		actual_weight = cr.fetchone()
		print "actual_weight",actual_weight
		if actual_weight == None:
			raise osv.except_osv(_('Warning !!'),
				_('Actual weight should be with in Min and Max weight. !!'))
		if rec.db_actual_unbal_weight <= 0:
			raise osv.except_osv(_('Warning !!'),
				_('Actual weight should be greater than zero. !!'))
		if rec.db_state == 'pending':
			if rec.db_result == 'reject':
				### Rejection Process Function Calling ###
				self.reject_process(cr,uid,ids,1)
				### Updation in next sequence Hydro static test ###
				self.write(cr, uid, ids, {'hs_state':'completed','hs_result':'reject'})
				### Changing Assembly state to reprocess ###
				assembly_obj.write(cr,uid,rec.assembly_id.id,{'state':'re_process'})
				ass_foundry_obj.write(cr,uid,rec.assembly_foundry_id.id,{'state':'re_process'})
			self.write(cr, uid, ids, {'db_state':'completed','update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
				
		return True
		
	def hs_update(self,cr,uid,ids,context=None):
		
		rec = self.browse(cr,uid,ids[0])
		
		### Validations  ###
		### Actual weight checking ###	
		
		if rec.hs_actual_unbal_weight <= 0.00:
			raise osv.except_osv(_('Warning !!'),
				_('Actual weight should be greater than zero. !!'))
				
		if rec.hs_pressure <= 0.00:
			raise osv.except_osv(_('Warning !!'),
				_('Test Pressure should be greater than zero. !!'))
		
		if rec.hs_state == 'pending':
			if rec.hs_result == 'reject':
				### Rejection Process Function Calling ###
				self.reject_process(cr,uid,ids,1)
				### Updation in previous sequence Dynamic Balancing ###
				self.write(cr, uid, ids, {'db_state':'completed','db_result':'reject'})
				### Changing Assembly state to reprocess ###
				assembly_obj.write(cr,uid,rec.assembly_id.id,{'state':'re_process'})
				ass_foundry_obj.write(cr,uid,rec.assembly_foundry_id.id,{'state':'re_process'})
			if rec.hs_result == 'leak':
				self.write(cr, uid, ids, {'hs_state':'pending'})
			if rec.hs_result == 'accept':
				self.write(cr, uid, ids, {'hs_state':'completed'})
			self.write(cr, uid, ids, {'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
				
		return True
		
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []	 
		for rec in self.browse(cr,uid,ids): 
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def create(self, cr, uid, vals, context=None):
		return super(kg_part_qap, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_part_qap, self).write(cr, uid, ids, vals, context)
		
	_sql_constraints = [
	
		('name', 'unique(name)', 'No must be Unique !!'),
	]   
	
kg_part_qap()
