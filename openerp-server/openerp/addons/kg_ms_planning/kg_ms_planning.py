from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

ORDER_PRIORITY =  [
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


class kg_ms_daily_planning(osv.osv):

	_name = "kg.ms.daily.planning"
	_description = "MS Daily Planning Entry"
	_order = "entry_date desc"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Planning No', size=128,select=True,readonly=True),
		'entry_date': fields.date('Planning Date',required=True),
		'note': fields.text('Notes'),
		'remarks': fields.text('Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'line_ids': fields.one2many('ch.ms.daily.planning.details', 'header_id', "Planning Details"),
		
		'ms_line_ids':fields.many2many('kg.machineshop','m2m_ms_planning_details' , 'planning_id', 'ms_id', 'MS Details',
			domain="[('state','=','accept'),'&',('ms_state','=','in_plan'),'&',('flag_planning','=', False),'&',('flag_trimming_dia','=', False)]"),
		'flag_planning': fields.boolean('Schedule'),
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_ms_daily_planning', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',	
		'active': True,
		'flag_planning': False,
		

	}
	
	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])		
		ms_obj = self.pool.get('kg.machineshop')
		line_obj = self.pool.get('ch.ms.daily.planning.details')
		
		del_sql = """ delete from ch_ms_daily_planning_details where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.ms_line_ids:
		
			for item in entry.ms_line_ids:
				csd_no = ''
				if item.ms_type == 'foundry_item':
					csd_no = item.pattern_id.csd_code
				if item.ms_type == 'ms_item':
					csd_no = item.ms_id.csd_code
				
				vals = {
				
					'header_id': entry.id,
					'ms_id': item.id,
					'csd_no': csd_no,
					'schedule_qty': item.ms_sch_qty - item.ms_plan_qty,
				}
				
				line_id = line_obj.create(cr, uid,vals)
				ms_obj.write(cr, uid, item.id, {'flag_planning': True})
				
			self.write(cr, uid, ids, {'flag_planning': True})
			
		return True
		
	def op_status_update(self, cr, uid, ids, ms_id, operation_id, context=None):
		ms_operation_obj = self.pool.get('kg.ms.operations')
		ms_obj = self.pool.get('kg.machineshop')
		
		ms_operation_rec = ms_operation_obj.browse(cr,uid,operation_id)
	
		
		if (ms_operation_rec.op1_state == 'pending' or ms_operation_rec.op2_state == 'pending'  or ms_operation_rec.op3_state  == 'pending' or
			ms_operation_rec.op4_state  == 'pending' or ms_operation_rec.op5_state == 'pending' ) and (ms_operation_rec.op6_state in ('pending','done') or ms_operation_rec.op7_state  in ('pending','done') or 
			ms_operation_rec.op8_state  in ('pending','done')  or ms_operation_rec.op9_state  in ('pending','done')  or ms_operation_rec.op10_state  in ('pending','done')  or ms_operation_rec.op11_state  in ('pending','done')  or 
			ms_operation_rec.op12_state in ('pending','done') ) :
			
			ms_obj.write(cr,uid,ms_id,{'ms_state': 'inhouse_1'})
		if (ms_operation_rec.op1_state in ('','done') and ms_operation_rec.op2_state in ('','done') and ms_operation_rec.op3_state in ('','done') and
			ms_operation_rec.op4_state in ('','done')  and ms_operation_rec.op5_state in ('','done') ) and (ms_operation_rec.op6_state == 'pending' or ms_operation_rec.op7_state == 'pending' or 
			ms_operation_rec.op8_state == 'pending' or ms_operation_rec.op9_state == 'pending' or ms_operation_rec.op10_state == 'pending' or ms_operation_rec.op11_state == 'pending' or 
			ms_operation_rec.op12_state == 'pending'):
			
			ms_obj.write(cr,uid,ms_id,{'ms_state': 'inhouse_2'})
		
		
		return True
		
	def entry_confirm(self, cr, uid, ids, context=None):
		entry_rec = self.browse(cr,uid,ids[0])
		ms_operation_obj = self.pool.get('kg.ms.operations')
		ms_dimension_obj = self.pool.get('ch.ms.dimension.details')
		ms_obj = self.pool.get('kg.machineshop')
		line_obj = self.pool.get('ch.ms.daily.planning.details')
		
		if entry_rec.state == 'draft':
			for line_item in entry_rec.line_ids:
				
				cr.execute(""" select sum(sc_qty)
					from ch_ms_sc_qty_details  
					where header_id = %s """%(line_item.id))
					
				total_sc_qty = cr.fetchone();
				
				line_obj.write(cr, uid, line_item.id, {'sc_qty':total_sc_qty[0]})
				
				if line_item.inhouse_qty < 0 or line_item.sc_qty < 0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative values !!'))
				
				
				if total_sc_qty[0] <= 0:
					if line_item.inhouse_qty == 0 and line_item.sc_qty == 0:
						raise osv.except_osv(_('Warning!'),
									_('System not allow to save Zero values !!'))
				
				if total_sc_qty[0] > 0:
					total_sc_qty = total_sc_qty[0]
				else:
					total_sc_qty = 0
				
				if (line_item.inhouse_qty + total_sc_qty) > line_item.schedule_qty:
					raise osv.except_osv(_('Warning!'),
								_('In house qty and sc qty should not be more than Required Qty !!! '))
								
								
				ms_obj.write(cr, uid, line_item.ms_id.id,{'ms_plan_qty':line_item.ms_id.ms_plan_qty + (line_item.inhouse_qty + line_item.sc_qty)})
				
				
				if (line_item.inhouse_qty + line_item.sc_qty) >= line_item.schedule_qty:
				
					#~ ms_obj.write(cr, uid, line_item.ms_id.id,{'ms_state':'op_progress'})		
					
				
				op1_status = ''
				op2_status = ''
				op3_status = ''
				op4_status = ''
				op5_status = ''
				op6_status = ''
				op7_status = ''
				op8_status = ''
				op9_status = ''
				op10_status = ''
				op11_status = ''
				op12_status = ''
				op1_id = False
				op2_id = False
				op3_id = False
				op4_id = False
				op5_id = False
				op6_id = False
				op7_id = False
				op8_id = False
				op9_id = False
				op10_id = False
				op11_id = False
				op12_id = False
				op1_stage_id = False
				op2_stage_id = False
				op3_stage_id = False
				op4_stage_id = False
				op5_stage_id = False
				op6_stage_id = False
				op7_stage_id = False
				op8_stage_id = False
				op9_stage_id = False
				op10_stage_id = False
				op11_stage_id = False
				op12_stage_id = False
				op1_clamping_area = ''
				op2_clamping_area = ''
				op3_clamping_area = ''
				op4_clamping_area = ''
				op5_clamping_area = ''
				op6_clamping_area = ''
				op7_clamping_area = ''
				op8_clamping_area = ''
				op9_clamping_area = ''
				op10_clamping_area = ''
				op11_clamping_area = ''
				op12_clamping_area = ''
				### MS Operation Creation ###
				actual_qty = 0
				if line_item.inhouse_qty > 0:
					if line_item.position_id.id != False:
						for pos_line_item in line_item.position_id.line_ids:
							
							if pos_line_item.operation_id.name == '10':
								op1_status = 'pending'
								op1_id = pos_line_item.operation_id.id
								op1_stage_id = pos_line_item.stage_id.id
								op1_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == '20':
								op2_status = 'pending'
								op2_id = pos_line_item.operation_id.id
								op2_stage_id = pos_line_item.stage_id.id
								op2_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == '30':
								op3_status = 'pending'
								op3_id = pos_line_item.operation_id.id
								op3_stage_id = pos_line_item.stage_id.id
								op3_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == '40':
								op4_status = 'pending'
								op4_id = pos_line_item.operation_id.id
								op4_stage_id = pos_line_item.stage_id.id
								op4_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == '50':
								op5_status = 'pending'
								op5_id = pos_line_item.operation_id.id
								op5_stage_id = pos_line_item.stage_id.id
								op5_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == '60':
								op6_status = 'pending'
								op6_id = pos_line_item.operation_id.id
								op6_stage_id = pos_line_item.stage_id.id
								op6_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == '70':
								op7_status = 'pending'
								op7_id = pos_line_item.operation_id.id
								op7_stage_id = pos_line_item.stage_id.id
								op7_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == '80':
								op8_status = 'pending'
								op8_id = pos_line_item.operation_id.id
								op8_stage_id = pos_line_item.stage_id.id
								op8_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == '90':
								op9_status = 'pending'
								op9_id = pos_line_item.operation_id.id
								op9_stage_id = pos_line_item.stage_id.id
								op9_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == '100':
								op10_status = 'pending'
								op10_id = pos_line_item.operation_id.id
								op10_stage_id = pos_line_item.stage_id.id
								op10_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == '110':
								op11_status = 'pending'
								op11_id = pos_line_item.operation_id.id
								op11_stage_id = pos_line_item.stage_id.id
								op11_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == '120':
								op12_status = 'pending'
								op12_id = pos_line_item.operation_id.id
								op12_stage_id = pos_line_item.stage_id.id
								op12_clamping_area = pos_line_item.clamping_area
						
						### Operation Creation ###
						
						excess_qty = line_item.inhouse_qty - line_item.schedule_qty
						
						if excess_qty > 0:
							
							### Stock Inward Creation ###
							inward_obj = self.pool.get('kg.stock.inward')
							inward_line_obj = self.pool.get('ch.stock.inward.details')
							
							inward_vals = {
								'location': line_item.order_id.location
							}
							
							inward_id = inward_obj.create(cr, uid, inward_vals)
							
							inward_line_vals = {
								'header_id': inward_id,
								'location': line_item.order_id.location,
								'stock_type': 'pump',
								'pump_model_id': line_item.pump_model_id.id,
								'pattern_id': line_item.pattern_id.id,
								'pattern_name': line_item.pattern_name,
								'item_code': line_item.item_code,
								'item_name': line_item.item_name,
								'moc_id': line_item.moc_id.id,
								'qty': excess_qty,
								'available_qty': excess_qty,
								'each_wgt': 0,
								'total_weight': 0,
								'unit_price': 0,
								'stock_mode': 'excess',
								'ms_stock_state': 'operation_inprogress',
								'stock_item': 'ms_item',
							}
							
							inward_line_id = inward_line_obj.create(cr, uid, inward_line_vals)
							
							actual_qty = line_item.inhouse_qty - excess_qty
							
							wo_id = self.pool.get('kg.work.order').search(cr, uid, [('flag_for_stock','=','t')])
							wo_line_id = self.pool.get('ch.work.order.details').search(cr, uid, [('flag_for_stock','=','t')])
							wo_line_rec = self.pool.get('ch.work.order.details').browse(cr, uid, wo_line_id[0])
							
							
							for operation in range(excess_qty):
				
								operation_vals = {
									'ms_id': line_item.ms_id.id,
									'ms_plan_id': entry_rec.id,
									'ms_plan_line_id': line_item.id,
									'order_id': wo_id[0],
									'order_line_id': wo_line_id[0],
									'order_no': wo_line_rec.order_no,
									'order_category': line_item.order_category,
									'order_priority': line_item.order_priority,
									'position_id': line_item.position_id.id,
									'pump_model_id': line_item.pump_model_id.id,
									'pattern_id': line_item.pattern_id.id,
									'pattern_code': line_item.pattern_code,
									'pattern_name': line_item.pattern_name,
									'item_code': line_item.item_code,
									'item_name': line_item.item_name,
									'moc_id': line_item.moc_id.id,
									'ms_type': line_item.ms_type,

									'inhouse_qty': 1,
									'op1_stage_id': op1_stage_id,
									'op1_clamping_area': op1_clamping_area,
									'op1_id': op1_id,
									'op1_state':op1_status,
									'op2_stage_id': op2_stage_id,
									'op2_clamping_area': op2_clamping_area,
									'op2_id': op2_id,
									'op2_state': op2_status,
									'op3_stage_id': op3_stage_id,
									'op3_clamping_area': op3_clamping_area,
									'op3_id': op3_id,
									'op3_state': op3_status,
									'op4_stage_id': op4_stage_id,
									'op4_clamping_area': op4_clamping_area,
									'op4_id': op4_id,
									'op4_state': op4_status,
									'op5_stage_id': op5_stage_id,
									'op5_clamping_area': op5_clamping_area,
									'op5_id': op5_id,
									'op5_state': op5_status,
									'op6_stage_id': op6_stage_id,
									'op6_clamping_area': op6_clamping_area,
									'op6_id': op6_id,
									'op6_state': op6_status,
									'op7_stage_id': op7_stage_id,
									'op7_clamping_area': op7_clamping_area,
									'op7_id': op7_id,
									'op7_state': op7_status,
									'op8_stage_id': op8_stage_id,
									'op8_clamping_area': op8_clamping_area,
									'op8_id': op8_id,
									'op8_state': op8_status,
									'op9_stage_id': op9_stage_id,
									'op9_clamping_area': op9_clamping_area,
									'op9_id': op9_id,
									'op9_state': op9_status,
									'op10_stage_id': op10_stage_id,
									'op10_clamping_area': op10_clamping_area,
									'op10_id': op10_id,
									'op10_state': op10_status,
									'op11_stage_id': op11_stage_id,
									'op11_clamping_area': op11_clamping_area,
									'op11_id': op11_id,
									'op11_state': op11_status,
									'op12_stage_id': op12_stage_id,
									'op12_clamping_area': op12_clamping_area,
									'op12_id': op12_id,
									'op12_state': op12_status,
									
								}
								
								ms_operation_id = ms_operation_obj.create(cr, uid, operation_vals)
								
								### MS State updation ##
								self.op_status_update(cr, uid, 0, line_item.ms_id.id,ms_operation_id)
								
								ms_operation_obj.write(cr, uid, ms_operation_id, {'last_operation_check_id':ms_operation_id})
								
								### Creating Dimension Details ###
								
								if line_item.position_id.id != False:
							
									for pos_line_item in line_item.position_id.line_ids:
										
										
										if pos_line_item.operation_id.name == '10':
											
											for op1_dimen_item in pos_line_item.line_ids:
												op1_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op1_dimen_item.header_id.id,
													'pos_dimension_id': op1_dimen_item.id,
													'dimension_id': op1_dimen_item.dimension_id.id,
													#~ 'clamping_area': op1_dimen_item.clamping_area,
													'description': op1_dimen_item.description,
													'min_val': op1_dimen_item.min_val,
													'max_val': op1_dimen_item.max_val,
													'remark': op1_dimen_item.remark,
													
													}
												
												op1_ms_dimension_id = ms_dimension_obj.create(cr, uid,op1_dimen_vals)
												
										
										if pos_line_item.operation_id.name == '20':
											
											for op2_dimen_item in pos_line_item.line_ids:
												
												op2_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op2_dimen_item.header_id.id,
													'pos_dimension_id': op2_dimen_item.id,
													'dimension_id': op2_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op2_dimen_item.description,
													'min_val': op2_dimen_item.min_val,
													'max_val': op2_dimen_item.max_val,
													'remark': op2_dimen_item.remark,
													
													}
												
												op2_ms_dimension_id = ms_dimension_obj.create(cr, uid,op2_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '30':
											
											for op3_dimen_item in pos_line_item.line_ids:
												
												op3_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op3_dimen_item.header_id.id,
													'pos_dimension_id': op3_dimen_item.id,
													'dimension_id': op3_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op3_dimen_item.description,
													'min_val': op3_dimen_item.min_val,
													'max_val': op3_dimen_item.max_val,
													'remark': op3_dimen_item.remark,
													
													}
												
												op3_ms_dimension_id = ms_dimension_obj.create(cr, uid,op3_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '40':
											
											for op4_dimen_item in pos_line_item.line_ids:
												
												op4_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op4_dimen_item.header_id.id,
													'pos_dimension_id': op4_dimen_item.id,
													'dimension_id': op4_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op4_dimen_item.description,
													'min_val': op4_dimen_item.min_val,
													'max_val': op4_dimen_item.max_val,
													'remark': op4_dimen_item.remark,
													
													}
												
												op4_ms_dimension_id = ms_dimension_obj.create(cr, uid,op4_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '50':
											
											for op5_dimen_item in pos_line_item.line_ids:
												
												op5_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op5_dimen_item.header_id.id,
													'pos_dimension_id': op5_dimen_item.id,
													'dimension_id': op5_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op5_dimen_item.description,
													'min_val': op5_dimen_item.min_val,
													'max_val': op5_dimen_item.max_val,
													'remark': op5_dimen_item.remark,
													
													}
												
												op5_ms_dimension_id = ms_dimension_obj.create(cr, uid,op5_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '60':
											
											for op6_dimen_item in pos_line_item.line_ids:
												
												op6_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op6_dimen_item.header_id.id,
													'pos_dimension_id': op6_dimen_item.id,
													'dimension_id': op6_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op6_dimen_item.description,
													'min_val': op6_dimen_item.min_val,
													'max_val': op6_dimen_item.max_val,
													'remark': op6_dimen_item.remark,
													
													}
												
												op6_ms_dimension_id = ms_dimension_obj.create(cr, uid,op6_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '70':
											
											for op7_dimen_item in pos_line_item.line_ids:
												
												op7_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op7_dimen_item.header_id.id,
													'pos_dimension_id': op7_dimen_item.id,
													'dimension_id': op7_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op7_dimen_item.description,
													'min_val': op7_dimen_item.min_val,
													'max_val': op7_dimen_item.max_val,
													'remark': op7_dimen_item.remark,
													
													}
												
												op7_ms_dimension_id = ms_dimension_obj.create(cr, uid,op7_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '80':
											
											for op8_dimen_item in pos_line_item.line_ids:
												
												op8_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op8_dimen_item.header_id.id,
													'pos_dimension_id': op8_dimen_item.id,
													'dimension_id': op8_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op8_dimen_item.description,
													'min_val': op8_dimen_item.min_val,
													'max_val': op8_dimen_item.max_val,
													'remark': op8_dimen_item.remark,
													
													}
												
												op8_ms_dimension_id = ms_dimension_obj.create(cr, uid,op8_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '90':
											
											for op9_dimen_item in pos_line_item.line_ids:
												
												op9_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op9_dimen_item.header_id.id,
													'pos_dimension_id': op9_dimen_item.id,
													'dimension_id': op9_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op9_dimen_item.description,
													'min_val': op9_dimen_item.min_val,
													'max_val': op9_dimen_item.max_val,
													'remark': op9_dimen_item.remark,
													
													}
												
												op9_ms_dimension_id = ms_dimension_obj.create(cr, uid,op9_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '100':
											
											for op10_dimen_item in pos_line_item.line_ids:
												
												op10_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op10_dimen_item.header_id.id,
													'pos_dimension_id': op10_dimen_item.id,
													'dimension_id': op10_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op10_dimen_item.description,
													'min_val': op10_dimen_item.min_val,
													'max_val': op10_dimen_item.max_val,
													'remark': op10_dimen_item.remark,
													
													}
												
												op10_ms_dimension_id = ms_dimension_obj.create(cr, uid,op10_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '110':
											
											for op11_dimen_item in pos_line_item.line_ids:
												
												op11_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op11_dimen_item.header_id.id,
													'pos_dimension_id': op11_dimen_item.id,
													'dimension_id': op11_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op11_dimen_item.description,
													'min_val': op11_dimen_item.min_val,
													'max_val': op11_dimen_item.max_val,
													'remark': op11_dimen_item.remark,
													
													}
												
												op11_ms_dimension_id = ms_dimension_obj.create(cr, uid,op11_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '120':
											
											for op12_dimen_item in pos_line_item.line_ids:
												
												op12_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op12_dimen_item.header_id.id,
													'pos_dimension_id': op12_dimen_item.id,
													'dimension_id': op12_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op12_dimen_item.description,
													'min_val': op12_dimen_item.min_val,
													'max_val': op12_dimen_item.max_val,
													'remark': op12_dimen_item.remark,
													
													}
												
												op12_ms_dimension_id = ms_dimension_obj.create(cr, uid,op12_dimen_vals)
						else:
							actual_qty = line_item.inhouse_qty
						
						if actual_qty > 0:
						
							for operation in range(actual_qty):
					
								operation_vals = {
									'ms_id': line_item.ms_id.id,
									'ms_plan_id': entry_rec.id,
									'ms_plan_line_id': line_item.id,
									'order_id': line_item.order_id.id,
									'order_line_id': line_item.order_line_id.id,
									'order_no': line_item.order_no,
									'order_category': line_item.order_category,
									'order_priority': line_item.order_priority,
									
									'pump_model_id': line_item.pump_model_id.id,
									'pattern_id': line_item.pattern_id.id,
									'pattern_code': line_item.pattern_code,
									'pattern_name': line_item.pattern_name,
									'item_code': line_item.item_code,
									'item_name': line_item.item_name,
									'moc_id': line_item.moc_id.id,
									'ms_type': line_item.ms_type,
									'position_id': line_item.position_id.id,
									'inhouse_qty': 1,
									'op1_stage_id': op1_stage_id,
									'op1_clamping_area': op1_clamping_area,
									'op1_id': op1_id,
									'op1_state':op1_status,
									'op2_stage_id': op2_stage_id,
									'op2_clamping_area': op2_clamping_area,
									'op2_id': op2_id,
									'op2_state': op2_status,
									'op3_stage_id': op3_stage_id,
									'op3_clamping_area': op3_clamping_area,
									'op3_id': op3_id,
									'op3_state': op3_status,
									'op4_stage_id': op4_stage_id,
									'op4_clamping_area': op4_clamping_area,
									'op4_id': op4_id,
									'op4_state': op4_status,
									'op5_stage_id': op5_stage_id,
									'op5_clamping_area': op5_clamping_area,
									'op5_id': op5_id,
									'op5_state': op5_status,
									'op6_stage_id': op6_stage_id,
									'op6_clamping_area': op6_clamping_area,
									'op6_id': op6_id,
									'op6_state': op6_status,
									'op7_stage_id': op7_stage_id,
									'op7_clamping_area': op7_clamping_area,
									'op7_id': op7_id,
									'op7_state': op7_status,
									'op8_stage_id': op8_stage_id,
									'op8_clamping_area': op8_clamping_area,
									'op8_id': op8_id,
									'op8_state': op8_status,
									'op9_stage_id': op9_stage_id,
									'op9_clamping_area': op9_clamping_area,
									'op9_id': op9_id,
									'op9_state': op9_status,
									'op10_stage_id': op10_stage_id,
									'op10_clamping_area': op10_clamping_area,
									'op10_id': op10_id,
									'op10_state': op10_status,
									'op11_stage_id': op11_stage_id,
									'op11_clamping_area': op11_clamping_area,
									'op11_id': op11_id,
									'op11_state': op11_status,
									'op12_stage_id': op12_stage_id,
									'op12_clamping_area': op12_clamping_area,
									'op12_id': op12_id,
									'op12_state': op12_status,
									
								}
								
								ms_operation_id = ms_operation_obj.create(cr, uid, operation_vals)
								
								### MS State updation ##
								self.op_status_update(cr, uid, 0,line_item.ms_id.id,ms_operation_id)
								
								ms_operation_obj.write(cr, uid, ms_operation_id, {'last_operation_check_id':ms_operation_id})
								
								### Creating Dimension Details ###
								
								if line_item.position_id.id != False:
							
									for pos_line_item in line_item.position_id.line_ids:
										
										
										if pos_line_item.operation_id.name == '10':
											
											for op1_dimen_item in pos_line_item.line_ids:
												op1_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op1_dimen_item.header_id.id,
													'pos_dimension_id': op1_dimen_item.id,
													'dimension_id': op1_dimen_item.dimension_id.id,
													#~ 'clamping_area': op1_dimen_item.clamping_area,
													'description': op1_dimen_item.description,
													'min_val': op1_dimen_item.min_val,
													'max_val': op1_dimen_item.max_val,
													'remark': op1_dimen_item.remark,
													
													}
												
												op1_ms_dimension_id = ms_dimension_obj.create(cr, uid,op1_dimen_vals)
												
										
										if pos_line_item.operation_id.name == '20':
											
											for op2_dimen_item in pos_line_item.line_ids:
												
												op2_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op2_dimen_item.header_id.id,
													'pos_dimension_id': op2_dimen_item.id,
													'dimension_id': op2_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op2_dimen_item.description,
													'min_val': op2_dimen_item.min_val,
													'max_val': op2_dimen_item.max_val,
													'remark': op2_dimen_item.remark,
													
													}
												
												op2_ms_dimension_id = ms_dimension_obj.create(cr, uid,op2_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '30':
											
											for op3_dimen_item in pos_line_item.line_ids:
												
												op3_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op3_dimen_item.header_id.id,
													'pos_dimension_id': op3_dimen_item.id,
													'dimension_id': op3_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op3_dimen_item.description,
													'min_val': op3_dimen_item.min_val,
													'max_val': op3_dimen_item.max_val,
													'remark': op3_dimen_item.remark,
													
													}
												
												op3_ms_dimension_id = ms_dimension_obj.create(cr, uid,op3_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '40':
											
											for op4_dimen_item in pos_line_item.line_ids:
												
												op4_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op4_dimen_item.header_id.id,
													'pos_dimension_id': op4_dimen_item.id,
													'dimension_id': op4_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op4_dimen_item.description,
													'min_val': op4_dimen_item.min_val,
													'max_val': op4_dimen_item.max_val,
													'remark': op4_dimen_item.remark,
													
													}
												
												op4_ms_dimension_id = ms_dimension_obj.create(cr, uid,op4_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '50':
											
											for op5_dimen_item in pos_line_item.line_ids:
												
												op5_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op5_dimen_item.header_id.id,
													'pos_dimension_id': op5_dimen_item.id,
													'dimension_id': op5_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op5_dimen_item.description,
													'min_val': op5_dimen_item.min_val,
													'max_val': op5_dimen_item.max_val,
													'remark': op5_dimen_item.remark,
													
													}
												
												op5_ms_dimension_id = ms_dimension_obj.create(cr, uid,op5_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '60':
											
											for op6_dimen_item in pos_line_item.line_ids:
												
												op6_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op6_dimen_item.header_id.id,
													'pos_dimension_id': op6_dimen_item.id,
													'dimension_id': op6_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op6_dimen_item.description,
													'min_val': op6_dimen_item.min_val,
													'max_val': op6_dimen_item.max_val,
													'remark': op6_dimen_item.remark,
													
													}
												
												op6_ms_dimension_id = ms_dimension_obj.create(cr, uid,op6_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '70':
											
											for op7_dimen_item in pos_line_item.line_ids:
												
												op7_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op7_dimen_item.header_id.id,
													'pos_dimension_id': op7_dimen_item.id,
													'dimension_id': op7_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op7_dimen_item.description,
													'min_val': op7_dimen_item.min_val,
													'max_val': op7_dimen_item.max_val,
													'remark': op7_dimen_item.remark,
													
													}
												
												op7_ms_dimension_id = ms_dimension_obj.create(cr, uid,op7_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '80':
											
											for op8_dimen_item in pos_line_item.line_ids:
												
												op8_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op8_dimen_item.header_id.id,
													'pos_dimension_id': op8_dimen_item.id,
													'dimension_id': op8_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op8_dimen_item.description,
													'min_val': op8_dimen_item.min_val,
													'max_val': op8_dimen_item.max_val,
													'remark': op8_dimen_item.remark,
													
													}
												
												op8_ms_dimension_id = ms_dimension_obj.create(cr, uid,op8_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '90':
											
											for op9_dimen_item in pos_line_item.line_ids:
												
												op9_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op9_dimen_item.header_id.id,
													'pos_dimension_id': op9_dimen_item.id,
													'dimension_id': op9_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op9_dimen_item.description,
													'min_val': op9_dimen_item.min_val,
													'max_val': op9_dimen_item.max_val,
													'remark': op9_dimen_item.remark,
													
													}
												
												op9_ms_dimension_id = ms_dimension_obj.create(cr, uid,op9_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '100':
											
											for op10_dimen_item in pos_line_item.line_ids:
												
												op10_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op10_dimen_item.header_id.id,
													'pos_dimension_id': op10_dimen_item.id,
													'dimension_id': op10_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op10_dimen_item.description,
													'min_val': op10_dimen_item.min_val,
													'max_val': op10_dimen_item.max_val,
													'remark': op10_dimen_item.remark,
													
													}
												
												op10_ms_dimension_id = ms_dimension_obj.create(cr, uid,op10_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '110':
											
											for op11_dimen_item in pos_line_item.line_ids:
												
												op11_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op11_dimen_item.header_id.id,
													'pos_dimension_id': op11_dimen_item.id,
													'dimension_id': op11_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op11_dimen_item.description,
													'min_val': op11_dimen_item.min_val,
													'max_val': op11_dimen_item.max_val,
													'remark': op11_dimen_item.remark,
													
													}
												
												op11_ms_dimension_id = ms_dimension_obj.create(cr, uid,op11_dimen_vals)
												
												
										if pos_line_item.operation_id.name == '120':
											
											for op12_dimen_item in pos_line_item.line_ids:
												
												op12_dimen_vals = {
													
													'header_id': ms_operation_id,
													'position_id': pos_line_item.header_id.id,
													'operation_id': pos_line_item.operation_id.id,
													'operation_name': pos_line_item.operation_id.name,
													'position_line': op12_dimen_item.header_id.id,
													'pos_dimension_id': op12_dimen_item.id,
													'dimension_id': op12_dimen_item.dimension_id.id,
													#~ 'clamping_area': op2_dimen_item.clamping_area,
													'description': op12_dimen_item.description,
													'min_val': op12_dimen_item.min_val,
													'max_val': op12_dimen_item.max_val,
													'remark': op12_dimen_item.remark,
													
													}
												
												op12_ms_dimension_id = ms_dimension_obj.create(cr, uid,op12_dimen_vals)
											
				print "total_sc_qty",total_sc_qty		
				header_sc_qty = total_sc_qty
				if header_sc_qty > 0:
					
					
					sc_excess_qty = (actual_qty + header_sc_qty) - line_item.schedule_qty
					
					if not line_item.line_ids:
						raise osv.except_osv(_('Warning!'),
							_('Kindly give SC Qty Split Ups !!'))
							
					if line_item.line_ids:
						
						ms_obj.write(cr, uid, line_item.ms_id.id,{'ms_state':'sent_to_sc'})
						
						pending_sc_qty = 0.00
						sc_actual_qty = 0.00
						total_sc_qty = 0.00
						pending_sc_qty = line_item.schedule_qty - line_item.inhouse_qty
						
						for sc_item in line_item.line_ids:
							total_sc_qty += sc_item.sc_qty
							
							sc_obj = self.pool.get('kg.subcontract.process')				
							sc_name = ''	
							sc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.process')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,sc_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(sc_seq_id[0],seq_rec.code))
							sc_name = cr.fetchone();
							
							
							if header_sc_qty > 0:
								
								if pending_sc_qty <= 0:
									sc_actual_qty = 0
								elif pending_sc_qty > sc_item.sc_qty:
									sc_actual_qty = sc_item.sc_qty
								else:
									sc_actual_qty = pending_sc_qty
									
									
							
							sc_vals = {
								'name': sc_name[0],
								'ms_plan_id': entry_rec.id,
								'ms_plan_line_id': line_item.id,
								'total_qty': sc_item.sc_qty,
								'pending_qty': sc_item.sc_qty,
								'actual_qty': sc_actual_qty,
								'contractor_id': sc_item.contractor_id.id,
								
							}
							
							sc_id = sc_obj.create(cr, uid,sc_vals)
							
							pending_sc_qty = pending_sc_qty - sc_actual_qty
							
						
						### Updatind Total Sc Qty ###
						
						
						self.pool.get('ch.ms.daily.planning.details').write(cr, uid, line_item.id, {'sc_qty':total_sc_qty})
						
						inhouse_pending_qty = line_item.schedule_qty - line_item.inhouse_qty
						
						if inhouse_pending_qty > 0:
							sc_excess_qty = total_sc_qty - inhouse_pending_qty
						else:
							sc_excess_qty = total_sc_qty
						
						if sc_excess_qty > 0:
							
							### Stock Inward Creation ###
							inward_obj = self.pool.get('kg.stock.inward')
							inward_line_obj = self.pool.get('ch.stock.inward.details')
							
							inward_vals = {
								'location': line_item.order_id.location
							}
							
							inward_id = inward_obj.create(cr, uid, inward_vals)
							
							inward_line_vals = {
								'header_id': inward_id,
								'location': line_item.order_id.location,
								'stock_type': 'pump',
								'pump_model_id': line_item.pump_model_id.id,
								'pattern_id': line_item.pattern_id.id,
								'pattern_name': line_item.pattern_name,
								'item_code': line_item.item_code,
								'item_name': line_item.item_name,
								'moc_id': line_item.moc_id.id,
								'qty': sc_excess_qty,
								'available_qty': sc_excess_qty,
								'each_wgt': 0,
								'total_weight': 0,
								'unit_price': 0,
								'stock_mode': 'excess',
								'ms_stock_state': 'operation_inprogress',
								'stock_item': 'ms_item',
							}
							
							inward_line_id = inward_line_obj.create(cr, uid, inward_line_vals)					
						
						
			
			plan_name = ''	
			plan_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.ms.daily.planning')])
			plan_seq_rec = self.pool.get('ir.sequence').browse(cr,uid,plan_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(plan_seq_id[0],plan_seq_rec.code))
			plan_name = cr.fetchone();	
			self.write(cr, uid, ids, {'name':plan_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass				
			
		
		return True
	
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
		return super(kg_ms_daily_planning, self).write(cr, uid, ids, vals, context)
		
kg_ms_daily_planning()


class ch_ms_daily_planning_details(osv.osv):

	_name = "ch.ms.daily.planning.details"
	_description = "MS Planning Details"
	
	
	_columns = {
	
		'header_id':fields.many2one('kg.ms.daily.planning', 'MS Planning', ondelete='cascade',required=True),
		'ms_id': fields.many2one('kg.machineshop','MS Id'),
		'production_id': fields.related('ms_id','production_id', type='many2one', relation='kg.production', string='Production No.', store=True, readonly=True),
		'order_id': fields.related('ms_id','order_id', type='many2one', relation='kg.work.order', string='Work Order', store=True, readonly=True),
		'order_line_id': fields.related('ms_id','order_line_id', type='many2one', relation='ch.work.order.details', string='Order Line', store=True, readonly=True),
		'order_no': fields.related('ms_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('ms_id','order_delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'order_date': fields.related('ms_id','order_date', type='date', string='Order Date', store=True, readonly=True),
		'order_category': fields.related('ms_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.related('ms_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		'pump_model_id': fields.related('ms_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('ms_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_code': fields.related('ms_id','pattern_code', type='char', string='Pattern Code', store=True, readonly=True),
		'pattern_name': fields.related('ms_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'item_code': fields.related('ms_id','item_code', type='char', string='Item Code', store=True, readonly=True),
		'item_name': fields.related('ms_id','item_name', type='char', string='Item Name', store=True, readonly=True),
		'moc_id': fields.related('ms_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'position_id': fields.related('ms_id','position_id', type='many2one', relation='kg.position.number', string='Position No.', store=True, readonly=True),
		'csd_no': fields.char('CSD No.', size=128,readonly=True),
		'schedule_qty': fields.integer('Required Qty'),
		'inhouse_qty': fields.integer('In-house Qty'),
		'sc_qty': fields.integer('SC Qty'),
		'ms_type': fields.related('ms_id','ms_type', type='selection', selection=[('foundry_item','Foundry Item'),('ms_item','MS Item')], string='Item Type', store=True, readonly=True),
		'oth_spec': fields.related('ms_id','oth_spec', type='text', string='WO Remarks', store=True, readonly=True),
		'remarks': fields.text('Remarks'),
		'line_ids': fields.one2many('ch.ms.sc.qty.details','header_id', 'MS PLAN SC Line'),
	} 
	
	
ch_ms_daily_planning_details()


class ch_ms_sc_qty_details(osv.osv):

	_name = "ch.ms.sc.qty.details"
	_description = "MS Planning SC Details"
	
	
	_columns = {
	
		'header_id':fields.many2one('ch.ms.daily.planning.details', 'MS SC Details', ondelete='cascade',required=True),
		'contractor_id': fields.many2one('res.partner','Subcontractor', domain="[('contractor','=','t')]"),
		'sc_qty': fields.integer('Qty'),
		'excess_qty': fields.integer('Excess Qty'),
		
	}

ch_ms_sc_qty_details()
