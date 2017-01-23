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


class kg_ms_operations(osv.osv):

	_name = "kg.ms.operations"
	_description = "MS Operations"
	_order = "entry_date desc"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Operation No', size=128,select=True,readonly=True),
		'entry_date': fields.date('Operation Date',required=True),
		'note': fields.text('Notes'),
		'remarks': fields.text('Remarks'),
		'active': fields.boolean('Active'),
		
		'ms_id': fields.many2one('kg.machineshop','MS Id'),
		'production_id': fields.related('ms_id','production_id', type='many2one', relation='kg.production', string='Production No.', store=True, readonly=True),
		'ms_plan_id': fields.many2one('kg.ms.daily.planning','Planning Id'),
		'ms_plan_line_id': fields.many2one('ch.ms.daily.planning.details','Planning Line Id'),
		'position_id': fields.related('ms_plan_line_id','position_id', type='many2one', relation='kg.position.number', string='Position No.', store=True, readonly=True),
		#~ 'order_id': fields.related('ms_plan_line_id','order_id', type='many2one', relation='kg.work.order', string='Work Order', store=True, readonly=True),
		#~ 'order_line_id': fields.related('ms_plan_line_id','order_line_id', type='many2one', relation='ch.work.order.details', string='Order Line', store=True, readonly=True),
		
		'order_id': fields.many2one('kg.work.order','Work Order',readonly=True),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line',readonly=True),
		'order_no': fields.related('order_line_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		
		'order_category': fields.related('ms_plan_line_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.related('ms_plan_line_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		
		'pump_model_id': fields.related('ms_plan_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('ms_plan_line_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_code': fields.related('ms_plan_line_id','pattern_code', type='char', string='Pattern Code', store=True, readonly=True),
		'pattern_name': fields.related('ms_plan_line_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'item_code': fields.related('ms_plan_line_id','item_code', type='char', string='Item Code', store=True, readonly=True),
		'item_name': fields.related('ms_plan_line_id','item_name', type='char', string='Item Name', store=True, readonly=True),
		'moc_id': fields.related('ms_plan_line_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'ms_type': fields.related('ms_plan_line_id','ms_type', type='selection', selection=[('foundry_item','Foundry Item'),('ms_item','MS Item')], string='Item Type', store=True, readonly=True),
		'inhouse_qty': fields.integer('In-house Qty'),
		'parent_id': fields.integer('Parent Id'),
		'last_operation_check_id': fields.integer('Last Operation Check Id'),
		'state': fields.selection([('active','Active'),('reject','Reject')],'Status'),
		
		### Operation 1 ###
		'op1_stage_id': fields.many2one('kg.stage.master','Stage'),
		'op1_shift_id': fields.many2one('kg.shift.master','Shift'),
		'op1_machine_id': fields.many2one('kg.machinery.master','Machine'),
		'op1_operator': fields.char('Operator', size=128),
		'op1_start_time': fields.float('Start Time'),
		'op1_start_time_type': fields.selection([('am','AM'),('pm','PM')],'Start Time Type'),
		'op1_end_time': fields.float('End Time'),
		'op1_end_time_type': fields.selection([('am','AM'),('pm','PM')],'End Time Type'),
		'op1_setting_time': fields.float('End Time'),
		'op1_setting_time_type': fields.selection([('am','AM'),('pm','PM')],'Setting Time Type'),
		'op1_total_time': fields.float('Total Time(hrs)'),
		'op1_idle_time': fields.float('Idle Time'),
		'op1_idle_time_type': fields.selection([('am','AM'),('pm','PM')],'Idle Time Type'),
		'op1_idle_reason': fields.char('Reason for Idle'),
		'op1_comp_wgt': fields.float('Component weight'),
		'op1_process_result': fields.selection([('accept','Accept'),('reject','Reject'),('rework','Rework')],'Process Result'),
		'op1_cost_incurred': fields.float('Cost Incurred'),
		'op1_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done'),('reject','Reject')],'Status'),
		'op1_date': fields.datetime('Operation1 Updated Date', readonly=True),
		'op1_user_id': fields.many2one('res.users', 'Operation1 Updated By', readonly=True),
		'op1_line_ids': fields.one2many('ch.ms.dimension.details','header_id','Dimension Details',domain=[('operation_name','=','10')]),
		'op1_id': fields.many2one('kg.operation.master','Operation'),
		'op1_sc_status': fields.selection([('sc','Suncontractor'),('inhouse','Inhouse')],'OP SC Status'),
		'op1_flag_sc': fields.boolean('Assign to Subcontract'),
		'op1_contractor_id': fields.many2one('res.partner','Subcontractor'),
		'op1_button_status': fields.selection([('visible','Visible'),('invisible','Invisible')],'Button Status'),
		'op1_clamping_area': fields.char('Clamping Area'),
		'op1_start_date': fields.date('Start Date'),
		'op1_end_date': fields.date('End Date'),
		
		 
		### Operation 2 ###
		'op2_stage_id': fields.many2one('kg.stage.master','Stage'),
		'op2_shift_id': fields.many2one('kg.shift.master','Shift'),
		'op2_machine_id': fields.many2one('kg.machinery.master','Machine'),
		'op2_operator': fields.char('Operator', size=128),
		'op2_start_time': fields.float('Start Time'),
		'op2_start_time_type': fields.selection([('am','AM'),('pm','PM')],'Start Time Type'),
		'op2_end_time': fields.float('End Time'),
		'op2_end_time_type': fields.selection([('am','AM'),('pm','PM')],'End Time Type'),
		'op2_setting_time': fields.float('End Time'),
		'op2_setting_time_type': fields.selection([('am','AM'),('pm','PM')],'Setting Time Type'),
		'op2_total_time': fields.float('Total Time(hrs)'),
		'op2_idle_time': fields.float('Idle Time'),
		'op2_idle_time_type': fields.selection([('am','AM'),('pm','PM')],'Idle Time Type'),
		'op2_idle_reason': fields.char('Reason for Idle'),
		'op2_comp_wgt': fields.float('Component weight'),
		'op2_process_result': fields.selection([('accept','Accept'),('reject','Reject'),('rework','Rework')],'Process Result'),
		'op2_cost_incurred': fields.float('Cost Incurred'),
		'op2_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done'),('reject','Reject')],'Status'),
		'op2_date': fields.datetime('Operation1 Updated Date', readonly=True),
		'op2_user_id': fields.many2one('res.users', 'Operation1 Updated By', readonly=True),
		'op2_line_ids': fields.one2many('ch.ms.dimension.details','header_id','Dimension Details',domain=[('operation_name','=','20')]),
		'op2_id': fields.many2one('kg.operation.master','Operation'), 
		'op2_sc_status': fields.selection([('sc','Suncontractor'),('inhouse','Inhouse')],'OP SC Status'),
		'op2_flag_sc': fields.boolean('Assign to Subcontract'),
		'op2_contractor_id': fields.many2one('res.partner','Subcontractor'),
		'op2_button_status': fields.selection([('visible','Visible'),('invisible','Invisible')],'Button Status'),
		'op2_clamping_area': fields.char('Clamping Area'),
		'op2_start_date': fields.date('Start Date'),
		'op2_end_date': fields.date('End Date'),
		
		### Operation 3 ###
		'op3_stage_id': fields.many2one('kg.stage.master','Stage'),
		'op3_shift_id': fields.many2one('kg.shift.master','Shift'),
		'op3_machine_id': fields.many2one('kg.machinery.master','Machine'),
		'op3_operator': fields.char('Operator', size=128),
		'op3_start_time': fields.float('Start Time'),
		'op3_start_time_type': fields.selection([('am','AM'),('pm','PM')],'Start Time Type'),
		'op3_end_time': fields.float('End Time'),
		'op3_end_time_type': fields.selection([('am','AM'),('pm','PM')],'End Time Type'),
		'op3_setting_time': fields.float('End Time'),
		'op3_setting_time_type': fields.selection([('am','AM'),('pm','PM')],'Setting Time Type'),
		'op3_total_time': fields.float('Total Time(hrs)'),
		'op3_idle_time': fields.float('Idle Time'),
		'op3_idle_time_type': fields.selection([('am','AM'),('pm','PM')],'Idle Time Type'),
		'op3_idle_reason': fields.char('Reason for Idle'),
		'op3_comp_wgt': fields.float('Component weight'),
		'op3_process_result': fields.selection([('accept','Accept'),('reject','Reject'),('rework','Rework')],'Process Result'),
		'op3_cost_incurred': fields.float('Cost Incurred'),
		'op3_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done'),('reject','Reject')],'Status'),
		'op3_date': fields.datetime('Operation1 Updated Date', readonly=True),
		'op3_user_id': fields.many2one('res.users', 'Operation1 Updated By', readonly=True),
		'op3_line_ids': fields.one2many('ch.ms.dimension.details','header_id','Dimension Details',domain=[('operation_name','=','30')]),
		'op3_id': fields.many2one('kg.operation.master','Operation'), 
		'op3_sc_status': fields.selection([('sc','Suncontractor'),('inhouse','Inhouse')],'OP SC Status'),
		'op3_flag_sc': fields.boolean('Assign to Subcontract'),
		'op3_contractor_id': fields.many2one('res.partner','Subcontractor'),
		'op3_button_status': fields.selection([('visible','Visible'),('invisible','Invisible')],'Button Status'),
		'op3_clamping_area': fields.char('Clamping Area'),
		'op3_start_date': fields.date('Start Date'),
		'op3_end_date': fields.date('End Date'),
		
		### Operation 4 ###
		'op4_stage_id': fields.many2one('kg.stage.master','Stage'),
		'op4_shift_id': fields.many2one('kg.shift.master','Shift'),
		'op4_machine_id': fields.many2one('kg.machinery.master','Machine'),
		'op4_operator': fields.char('Operator', size=128),
		'op4_start_time': fields.float('Start Time'),
		'op4_start_time_type': fields.selection([('am','AM'),('pm','PM')],'Start Time Type'),
		'op4_end_time': fields.float('End Time'),
		'op4_end_time_type': fields.selection([('am','AM'),('pm','PM')],'End Time Type'),
		'op4_setting_time': fields.float('End Time'),
		'op4_setting_time_type': fields.selection([('am','AM'),('pm','PM')],'Setting Time Type'),
		'op4_total_time': fields.float('Total Time(hrs)'),
		'op4_idle_time': fields.float('Idle Time'),
		'op4_idle_time_type': fields.selection([('am','AM'),('pm','PM')],'Idle Time Type'),
		'op4_idle_reason': fields.char('Reason for Idle'),
		'op4_comp_wgt': fields.float('Component weight'),
		'op4_process_result': fields.selection([('accept','Accept'),('reject','Reject'),('rework','Rework')],'Process Result'),
		'op4_cost_incurred': fields.float('Cost Incurred'),
		'op4_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done'),('reject','Reject')],'Status'),
		'op4_date': fields.datetime('Operation1 Updated Date', readonly=True),
		'op4_user_id': fields.many2one('res.users', 'Operation1 Updated By', readonly=True),
		'op4_line_ids': fields.one2many('ch.ms.dimension.details','header_id','Dimension Details',domain=[('operation_name','=','40')]),
		'op4_id': fields.many2one('kg.operation.master','Operation'), 
		'op4_sc_status': fields.selection([('sc','Suncontractor'),('inhouse','Inhouse')],'OP SC Status'),
		'op4_flag_sc': fields.boolean('Assign to Subcontract'),
		'op4_contractor_id': fields.many2one('res.partner','Subcontractor'),
		'op4_button_status': fields.selection([('visible','Visible'),('invisible','Invisible')],'Button Status'),
		'op4_clamping_area': fields.char('Clamping Area'), 
		'op4_start_date': fields.date('Start Date'),
		'op4_end_date': fields.date('End Date'),
		
		### Operation 5 ###
		'op5_stage_id': fields.many2one('kg.stage.master','Stage'),
		'op5_shift_id': fields.many2one('kg.shift.master','Shift'),
		'op5_machine_id': fields.many2one('kg.machinery.master','Machine'),
		'op5_operator': fields.char('Operator', size=128),
		'op5_start_time': fields.float('Start Time'),
		'op5_start_time_type': fields.selection([('am','AM'),('pm','PM')],'Start Time Type'),
		'op5_end_time': fields.float('End Time'),
		'op5_end_time_type': fields.selection([('am','AM'),('pm','PM')],'End Time Type'),
		'op5_setting_time': fields.float('End Time'),
		'op5_setting_time_type': fields.selection([('am','AM'),('pm','PM')],'Setting Time Type'),
		'op5_total_time': fields.float('Total Time(hrs)'),
		'op5_idle_time': fields.float('Idle Time'),
		'op5_idle_time_type': fields.selection([('am','AM'),('pm','PM')],'Idle Time Type'),
		'op5_idle_reason': fields.char('Reason for Idle'),
		'op5_comp_wgt': fields.float('Component weight'),
		'op5_process_result': fields.selection([('accept','Accept'),('reject','Reject'),('rework','Rework')],'Process Result'),
		'op5_cost_incurred': fields.float('Cost Incurred'),
		'op5_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done'),('reject','Reject')],'Status'),
		'op5_date': fields.datetime('Operation1 Updated Date', readonly=True),
		'op5_user_id': fields.many2one('res.users', 'Operation1 Updated By', readonly=True),
		'op5_line_ids': fields.one2many('ch.ms.dimension.details','header_id','Dimension Details',domain=[('operation_name','=','50')]),
		'op5_id': fields.many2one('kg.operation.master','Operation'), 
		'op5_sc_status': fields.selection([('sc','Suncontractor'),('inhouse','Inhouse')],'OP SC Status'),
		'op5_flag_sc': fields.boolean('Assign to Subcontract'),
		'op5_contractor_id': fields.many2one('res.partner','Subcontractor'),
		'op5_button_status': fields.selection([('visible','Visible'),('invisible','Invisible')],'Button Status'),
		'op5_clamping_area': fields.char('Clamping Area'),
		'op5_start_date': fields.date('Start Date'),
		'op5_end_date': fields.date('End Date'), 
		
		### Operation 6 ###
		'op6_stage_id': fields.many2one('kg.stage.master','Stage'),
		'op6_shift_id': fields.many2one('kg.shift.master','Shift'),
		'op6_machine_id': fields.many2one('kg.machinery.master','Machine'),
		'op6_operator': fields.char('Operator', size=128),
		'op6_start_time': fields.float('Start Time'),
		'op6_start_time_type': fields.selection([('am','AM'),('pm','PM')],'Start Time Type'),
		'op6_end_time': fields.float('End Time'),
		'op6_end_time_type': fields.selection([('am','AM'),('pm','PM')],'End Time Type'),
		'op6_setting_time': fields.float('End Time'),
		'op6_setting_time_type': fields.selection([('am','AM'),('pm','PM')],'Setting Time Type'),
		'op6_total_time': fields.float('Total Time(hrs)'),
		'op6_idle_time': fields.float('Idle Time'),
		'op6_idle_time_type': fields.selection([('am','AM'),('pm','PM')],'Idle Time Type'),
		'op6_idle_reason': fields.char('Reason for Idle'),
		'op6_comp_wgt': fields.float('Component weight'),
		'op6_process_result': fields.selection([('accept','Accept'),('reject','Reject'),('rework','Rework')],'Process Result'),
		'op6_cost_incurred': fields.float('Cost Incurred'),
		'op6_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done'),('reject','Reject')],'Status'),
		'op6_date': fields.datetime('Operation1 Updated Date', readonly=True),
		'op6_user_id': fields.many2one('res.users', 'Operation1 Updated By', readonly=True),
		'op6_line_ids': fields.one2many('ch.ms.dimension.details','header_id','Dimension Details',domain=[('operation_name','=','60')]),
		'op6_id': fields.many2one('kg.operation.master','Operation'), 
		'op6_sc_status': fields.selection([('sc','Suncontractor'),('inhouse','Inhouse')],'OP SC Status'),
		'op6_flag_sc': fields.boolean('Assign to Subcontract'),
		'op6_contractor_id': fields.many2one('res.partner','Subcontractor'),
		'op6_button_status': fields.selection([('visible','Visible'),('invisible','Invisible')],'Button Status'),
		'op6_clamping_area': fields.char('Clamping Area'),
		'op6_start_date': fields.date('Start Date'),
		'op6_end_date': fields.date('End Date'), 
		
		### Operation 7 ###
		'op7_stage_id': fields.many2one('kg.stage.master','Stage'),
		'op7_shift_id': fields.many2one('kg.shift.master','Shift'),
		'op7_machine_id': fields.many2one('kg.machinery.master','Machine'),
		'op7_operator': fields.char('Operator', size=128),
		'op7_start_time': fields.float('Start Time'),
		'op7_start_time_type': fields.selection([('am','AM'),('pm','PM')],'Start Time Type'),
		'op7_end_time': fields.float('End Time'),
		'op7_end_time_type': fields.selection([('am','AM'),('pm','PM')],'End Time Type'),
		'op7_setting_time': fields.float('End Time'),
		'op7_setting_time_type': fields.selection([('am','AM'),('pm','PM')],'Setting Time Type'),
		'op7_total_time': fields.float('Total Time(hrs)'),
		'op7_idle_time': fields.float('Idle Time'),
		'op7_idle_time_type': fields.selection([('am','AM'),('pm','PM')],'Idle Time Type'),
		'op7_idle_reason': fields.char('Reason for Idle'),
		'op7_comp_wgt': fields.float('Component weight'),
		'op7_process_result': fields.selection([('accept','Accept'),('reject','Reject'),('rework','Rework')],'Process Result'),
		'op7_cost_incurred': fields.float('Cost Incurred'),
		'op7_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done'),('reject','Reject')],'Status'),
		'op7_date': fields.datetime('Operation1 Updated Date', readonly=True),
		'op7_user_id': fields.many2one('res.users', 'Operation1 Updated By', readonly=True),
		'op7_line_ids': fields.one2many('ch.ms.dimension.details','header_id','Dimension Details',domain=[('operation_name','=','70')]),
		'op7_id': fields.many2one('kg.operation.master','Operation'), 
		'op7_sc_status': fields.selection([('sc','Suncontractor'),('inhouse','Inhouse')],'OP SC Status'),
		'op7_flag_sc': fields.boolean('Assign to Subcontract'),
		'op7_contractor_id': fields.many2one('res.partner','Subcontractor'),
		'op7_button_status': fields.selection([('visible','Visible'),('invisible','Invisible')],'Button Status'),
		'op7_clamping_area': fields.char('Clamping Area'),
		'op7_start_date': fields.date('Start Date'),
		'op7_end_date': fields.date('End Date'), 
		
		### Operation 8 ###
		'op8_stage_id': fields.many2one('kg.stage.master','Stage'),
		'op8_shift_id': fields.many2one('kg.shift.master','Shift'),
		'op8_machine_id': fields.many2one('kg.machinery.master','Machine'),
		'op8_operator': fields.char('Operator', size=128),
		'op8_start_time': fields.float('Start Time'),
		'op8_start_time_type': fields.selection([('am','AM'),('pm','PM')],'Start Time Type'),
		'op8_end_time': fields.float('End Time'),
		'op8_end_time_type': fields.selection([('am','AM'),('pm','PM')],'End Time Type'),
		'op8_setting_time': fields.float('End Time'),
		'op8_setting_time_type': fields.selection([('am','AM'),('pm','PM')],'Setting Time Type'),
		'op8_total_time': fields.float('Total Time(hrs)'),
		'op8_idle_time': fields.float('Idle Time'),
		'op8_idle_time_type': fields.selection([('am','AM'),('pm','PM')],'Idle Time Type'),
		'op8_idle_reason': fields.char('Reason for Idle'),
		'op8_comp_wgt': fields.float('Component weight'),
		'op8_process_result': fields.selection([('accept','Accept'),('reject','Reject'),('rework','Rework')],'Process Result'),
		'op8_cost_incurred': fields.float('Cost Incurred'),
		'op8_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done'),('reject','Reject')],'Status'),
		'op8_date': fields.datetime('Operation1 Updated Date', readonly=True),
		'op8_user_id': fields.many2one('res.users', 'Operation1 Updated By', readonly=True),
		'op8_line_ids': fields.one2many('ch.ms.dimension.details','header_id','Dimension Details',domain=[('operation_name','=','80')]),
		'op8_id': fields.many2one('kg.operation.master','Operation'), 
		'op8_sc_status': fields.selection([('sc','Suncontractor'),('inhouse','Inhouse')],'OP SC Status'),
		'op8_flag_sc': fields.boolean('Assign to Subcontract'),
		'op8_contractor_id': fields.many2one('res.partner','Subcontractor'),
		'op8_button_status': fields.selection([('visible','Visible'),('invisible','Invisible')],'Button Status'),
		'op8_clamping_area': fields.char('Clamping Area'),
		'op8_start_date': fields.date('Start Date'),
		'op8_end_date': fields.date('End Date'),
		
		### Operation 9 ###
		'op9_stage_id': fields.many2one('kg.stage.master','Stage'),
		'op9_shift_id': fields.many2one('kg.shift.master','Shift'),
		'op9_machine_id': fields.many2one('kg.machinery.master','Machine'),
		'op9_operator': fields.char('Operator', size=128),
		'op9_start_time': fields.float('Start Time'),
		'op9_start_time_type': fields.selection([('am','AM'),('pm','PM')],'Start Time Type'),
		'op9_end_time': fields.float('End Time'),
		'op9_end_time_type': fields.selection([('am','AM'),('pm','PM')],'End Time Type'),
		'op9_setting_time': fields.float('End Time'),
		'op9_setting_time_type': fields.selection([('am','AM'),('pm','PM')],'Setting Time Type'),
		'op9_total_time': fields.float('Total Time(hrs)'),
		'op9_idle_time': fields.float('Idle Time'),
		'op9_idle_time_type': fields.selection([('am','AM'),('pm','PM')],'Idle Time Type'),
		'op9_idle_reason': fields.char('Reason for Idle'),
		'op9_comp_wgt': fields.float('Component weight'),
		'op9_process_result': fields.selection([('accept','Accept'),('reject','Reject'),('rework','Rework')],'Process Result'),
		'op9_cost_incurred': fields.float('Cost Incurred'),
		'op9_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done'),('reject','Reject')],'Status'),
		'op9_date': fields.datetime('Operation1 Updated Date', readonly=True),
		'op9_user_id': fields.many2one('res.users', 'Operation1 Updated By', readonly=True),
		'op9_line_ids': fields.one2many('ch.ms.dimension.details','header_id','Dimension Details',domain=[('operation_name','=','90')]),
		'op9_id': fields.many2one('kg.operation.master','Operation'), 
		'op9_sc_status': fields.selection([('sc','Suncontractor'),('inhouse','Inhouse')],'OP SC Status'),
		'op9_flag_sc': fields.boolean('Assign to Subcontract'),
		'op9_contractor_id': fields.many2one('res.partner','Subcontractor'),
		'op9_button_status': fields.selection([('visible','Visible'),('invisible','Invisible')],'Button Status'),
		'op9_clamping_area': fields.char('Clamping Area'),
		'op9_start_date': fields.date('Start Date',required=True),
		'op9_end_date': fields.date('End Date',required=True),
		 
		### Operation 10 ###
		'op10_stage_id': fields.many2one('kg.stage.master','Stage'),
		'op10_shift_id': fields.many2one('kg.shift.master','Shift'),
		'op10_machine_id': fields.many2one('kg.machinery.master','Machine'),
		'op10_operator': fields.char('Operator', size=128),
		'op10_start_time': fields.float('Start Time'),
		'op10_start_time_type': fields.selection([('am','AM'),('pm','PM')],'Start Time Type'),
		'op10_end_time': fields.float('End Time'),
		'op10_end_time_type': fields.selection([('am','AM'),('pm','PM')],'End Time Type'),
		'op10_setting_time': fields.float('End Time'),
		'op10_setting_time_type': fields.selection([('am','AM'),('pm','PM')],'Setting Time Type'),
		'op10_total_time': fields.float('Total Time(hrs)'),
		'op10_idle_time': fields.float('Idle Time'),
		'op10_idle_time_type': fields.selection([('am','AM'),('pm','PM')],'Idle Time Type'),
		'op10_idle_reason': fields.char('Reason for Idle'),
		'op10_comp_wgt': fields.float('Component weight'),
		'op10_process_result': fields.selection([('accept','Accept'),('reject','Reject'),('rework','Rework')],'Process Result'),
		'op10_cost_incurred': fields.float('Cost Incurred'),
		'op10_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done'),('reject','Reject')],'Status'),
		'op10_date': fields.datetime('Operation1 Updated Date', readonly=True),
		'op10_user_id': fields.many2one('res.users', 'Operation1 Updated By', readonly=True),
		'op10_line_ids': fields.one2many('ch.ms.dimension.details','header_id','Dimension Details',domain=[('operation_name','=','100')]),
		'op10_id': fields.many2one('kg.operation.master','Operation'), 
		'op10_sc_status': fields.selection([('sc','Suncontractor'),('inhouse','Inhouse')],'OP SC Status'),
		'op10_flag_sc': fields.boolean('Assign to Subcontract'),
		'op10_contractor_id': fields.many2one('res.partner','Subcontractor'),
		'op10_button_status': fields.selection([('visible','Visible'),('invisible','Invisible')],'Button Status'),
		'op10_clamping_area': fields.char('Clamping Area'),
		'op10_start_date': fields.date('Start Date'),
		'op10_end_date': fields.date('End Date'),
		
		### Operation 11 ###
		'op11_stage_id': fields.many2one('kg.stage.master','Stage'),
		'op11_shift_id': fields.many2one('kg.shift.master','Shift'),
		'op11_machine_id': fields.many2one('kg.machinery.master','Machine'),
		'op11_operator': fields.char('Operator', size=128),
		'op11_start_time': fields.float('Start Time'),
		'op11_start_time_type': fields.selection([('am','AM'),('pm','PM')],'Start Time Type'),
		'op11_end_time': fields.float('End Time'),
		'op11_end_time_type': fields.selection([('am','AM'),('pm','PM')],'End Time Type'),
		'op11_setting_time': fields.float('End Time'),
		'op11_setting_time_type': fields.selection([('am','AM'),('pm','PM')],'Setting Time Type'),
		'op11_total_time': fields.float('Total Time(hrs)'),
		'op11_idle_time': fields.float('Idle Time'),
		'op11_idle_time_type': fields.selection([('am','AM'),('pm','PM')],'Idle Time Type'),
		'op11_idle_reason': fields.char('Reason for Idle'),
		'op11_comp_wgt': fields.float('Component weight'),
		'op11_process_result': fields.selection([('accept','Accept'),('reject','Reject'),('rework','Rework')],'Process Result'),
		'op11_cost_incurred': fields.float('Cost Incurred'),
		'op11_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done'),('reject','Reject')],'Status'),
		'op11_date': fields.datetime('Operation1 Updated Date', readonly=True),
		'op11_user_id': fields.many2one('res.users', 'Operation1 Updated By', readonly=True),
		'op11_line_ids': fields.one2many('ch.ms.dimension.details','header_id','Dimension Details',domain=[('operation_name','=','110')]),
		'op11_id': fields.many2one('kg.operation.master','Operation'), 
		'op11_sc_status': fields.selection([('sc','Suncontractor'),('inhouse','Inhouse')],'OP SC Status'),
		'op11_flag_sc': fields.boolean('Assign to Subcontract'),
		'op11_contractor_id': fields.many2one('res.partner','Subcontractor'),
		'op11_button_status': fields.selection([('visible','Visible'),('invisible','Invisible')],'Button Status'),
		'op11_clamping_area': fields.char('Clamping Area'),
		'op11_start_date': fields.date('Start Date'),
		'op11_end_date': fields.date('End Date'),
		
		### Operation 12 ###
		'op12_stage_id': fields.many2one('kg.stage.master','Stage'),
		'op12_shift_id': fields.many2one('kg.shift.master','Shift'),
		'op12_machine_id': fields.many2one('kg.machinery.master','Machine'),
		'op12_operator': fields.char('Operator', size=128),
		'op12_start_time': fields.float('Start Time'),
		'op12_start_time_type': fields.selection([('am','AM'),('pm','PM')],'Start Time Type'),
		'op12_end_time': fields.float('End Time'),
		'op12_end_time_type': fields.selection([('am','AM'),('pm','PM')],'End Time Type'),
		'op12_setting_time': fields.float('End Time'),
		'op12_setting_time_type': fields.selection([('am','AM'),('pm','PM')],'Setting Time Type'),
		'op12_total_time': fields.float('Total Time(hrs)'),
		'op12_idle_time': fields.float('Idle Time'),
		'op12_idle_time_type': fields.selection([('am','AM'),('pm','PM')],'Idle Time Type'),
		'op12_idle_reason': fields.char('Reason for Idle'),
		'op12_comp_wgt': fields.float('Component weight'),
		'op12_process_result': fields.selection([('accept','Accept'),('reject','Reject'),('rework','Rework')],'Process Result'),
		'op12_cost_incurred': fields.float('Cost Incurred'),
		'op12_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done'),('reject','Reject')],'Status'),
		'op12_date': fields.datetime('Operation1 Updated Date', readonly=True),
		'op12_user_id': fields.many2one('res.users', 'Operation1 Updated By', readonly=True),
		'op12_line_ids': fields.one2many('ch.ms.dimension.details','header_id','Dimension Details',domain=[('operation_name','=','120')]),
		'op12_id': fields.many2one('kg.operation.master','Operation'), 
		'op12_sc_status': fields.selection([('sc','Suncontractor'),('inhouse','Inhouse')],'OP SC Status'),
		'op12_flag_sc': fields.boolean('Assign to Subcontract'),
		'op12_contractor_id': fields.many2one('res.partner','Subcontractor'),
		'op12_button_status': fields.selection([('visible','Visible'),('invisible','Invisible')],'Button Status'),
		'op12_clamping_area': fields.char('Clamping Area'),
		'op12_start_date': fields.date('Start Date'),
		'op12_end_date': fields.date('End Date'),
		
		
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
		### Operation 1 ###
		'op1_sc_status':'inhouse',
		'op1_button_status': 'visible',
		'op1_start_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op1_end_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op1_start_time_type': 'am',
		'op1_end_time_type': 'am',
		'op1_setting_time_type': 'am',
		'op1_idle_time_type': 'am',
		'op1_process_result': 'accept',
		### Operation 2 ###
		'op2_sc_status':'inhouse',
		'op2_button_status': 'visible',
		'op2_start_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op2_end_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op2_start_time_type': 'am',
		'op2_end_time_type': 'am',
		'op2_setting_time_type': 'am',
		'op2_idle_time_type': 'am',
		'op2_process_result': 'accept',
		### Operation 3 ###
		'op3_sc_status':'inhouse',
		'op3_button_status': 'visible',
		'op3_start_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op3_end_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op3_start_time_type': 'am',
		'op3_end_time_type': 'am',
		'op3_setting_time_type': 'am',
		'op3_idle_time_type': 'am',
		'op3_process_result': 'accept',
		### Operation 4 ###
		'op4_sc_status':'inhouse',
		'op4_button_status': 'visible',
		'op4_start_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op4_end_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op4_start_time_type': 'am',
		'op4_end_time_type': 'am',
		'op4_setting_time_type': 'am',
		'op4_idle_time_type': 'am',
		'op4_process_result': 'accept',
		### Operation 5 ###
		'op5_sc_status':'inhouse',
		'op5_button_status': 'visible',
		'op5_start_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op5_end_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op5_start_time_type': 'am',
		'op5_end_time_type': 'am',
		'op5_setting_time_type': 'am',
		'op5_idle_time_type': 'am',
		'op5_process_result': 'accept',
		### Operation 6 ###
		'op6_sc_status':'inhouse',
		'op6_button_status': 'visible',
		'op6_start_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op6_end_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op6_start_time_type': 'am',
		'op6_end_time_type': 'am',
		'op6_setting_time_type': 'am',
		'op6_idle_time_type': 'am',
		'op6_process_result': 'accept',
		### Operation 7 ###
		'op7_sc_status':'inhouse',
		'op7_button_status': 'visible',
		'op7_start_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op7_end_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op7_start_time_type': 'am',
		'op7_end_time_type': 'am',
		'op7_setting_time_type': 'am',
		'op7_idle_time_type': 'am',
		'op7_process_result': 'accept',
		### Operation 8 ###
		'op8_sc_status':'inhouse',
		'op8_button_status': 'visible',
		'op8_start_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op8_end_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op8_start_time_type': 'am',
		'op8_end_time_type': 'am',
		'op8_setting_time_type': 'am',
		'op8_idle_time_type': 'am',
		'op8_process_result': 'accept',
		### Operation 9 ###
		'op9_sc_status':'inhouse',
		'op9_button_status': 'visible',
		'op9_start_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op9_end_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op9_start_time_type': 'am',
		'op9_end_time_type': 'am',
		'op9_setting_time_type': 'am',
		'op9_idle_time_type': 'am',
		'op9_process_result': 'accept',
		### Operation 10 ###
		'op10_sc_status':'inhouse',
		'op10_button_status': 'visible',
		'op10_start_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op10_end_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op10_start_time_type': 'am',
		'op10_end_time_type': 'am',
		'op10_setting_time_type': 'am',
		'op10_idle_time_type': 'am',
		'op10_process_result': 'accept',
		### Operation 11 ###
		'op11_sc_status':'inhouse',
		'op11_button_status': 'visible',
		'op11_start_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op11_end_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op11_start_time_type': 'am',
		'op11_end_time_type': 'am',
		'op11_setting_time_type': 'am',
		'op11_idle_time_type': 'am',
		'op11_process_result': 'accept',
		### Operation 12 ###
		'op12_sc_status':'inhouse',
		'op12_button_status': 'visible',
		'op12_start_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op12_end_date': lambda * a: time.strftime('%Y-%m-%d'),
		'op12_start_time_type': 'am',
		'op12_end_time_type': 'am',
		'op12_setting_time_type': 'am',
		'op12_idle_time_type': 'am',
		'op12_process_result': 'accept',
		
		'state': 'active',
		
	}
	
	### Operation 1 ###
	
	def onchange_operation1_sc(self, cr, uid, ids,op1_flag_sc, context=None):
		value = {'op1_sc_status': 'inhouse'}
		if op1_flag_sc == True:
			value = {'op1_sc_status': 'sc'}
		return {'value': value}
		
	def onchange_operation1_time(self, cr, uid, ids,op1_start_time,op1_end_time, context=None):
		
		value = {'op1_total_time': 0.00}
		total_time = 0.00
		total_time = op1_end_time - op1_start_time
		value = {'op1_total_time': total_time}
		return {'value': value}
		
	def onchange_operation1_cost_incurred(self, cr, uid, ids,op1_id,op1_stage_id,position_id,op1_total_time, context=None):
		value = {'op1_cost_incurred': 0.00}
		### Cost Incurred Calculation ###
		cr.execute(""" select in_house_cost from ch_kg_position_number 
			where operation_id = %s and stage_id = %s
			and header_id = %s limit 1 """ %(op1_id,op1_stage_id,position_id))
		inhouse_cost = cr.fetchone()
		cost_incurred = 0.00
		if inhouse_cost:
			
			if inhouse_cost[0] >= 0:
				cost_incurred = op1_total_time * inhouse_cost[0]
		value = {'op1_cost_incurred': cost_incurred}
		return {'value': value}
		
	def operation1_update(self, cr, uid, ids, context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		ms_obj = self.pool.get('kg.machineshop')
		
		if entry_rec.op1_state == 'pending':
			if entry_rec.op1_flag_sc != True:
			
				for dim_item in entry_rec.op1_line_ids:
					
					today = date.today()
					today = str(today)
					today = datetime.strptime(today, '%Y-%m-%d')
					start_date = entry_rec.op1_start_date
					start_date = str(start_date)
					start_date = datetime.strptime(start_date, '%Y-%m-%d')
					end_date = entry_rec.op1_end_date
					end_date = str(end_date)
					end_date = datetime.strptime(end_date, '%Y-%m-%d')
					if start_date > today or end_date > today:
						raise osv.except_osv(_('Warning!'),
								_('Start and End date should be less than or equal to current date !!'))
				
					if entry_rec.op1_start_time == entry_rec.op1_end_time:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not be equal !!'))
								
					if entry_rec.op1_start_time > 24 or entry_rec.op1_end_time > 24:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not exceed 24 hrs !!'))
								
					if dim_item.actual_val < 0:
						raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative. Check the actual value !!'))
					
					#~ if entry_rec.op1_process_result != 'reject':			
						#~ 
						#~ if dim_item.actual_val == 0:
							#~ raise osv.except_osv(_('Warning!'),
									#~ _('System not allow to save zero values. Check the actual value !!'))
									
						#### Min and Max Tolerance Checking ####
						
						if dim_item.pos_dimension_id != None:
						
							min_tol_value = (dim_item.min_val * dim_item.pos_dimension_id.min_tolerance) / 100
							max_tol_value = (dim_item.max_val * dim_item.pos_dimension_id.max_tolerance) / 100
									
							if dim_item.actual_val < (dim_item.min_val - min_tol_value):
								print ""
								raise osv.except_osv(_('Warning!'),
										_('Actual value should greater or equal to Minimum value !!'))
										
							if dim_item.actual_val > (dim_item.max_val + max_tol_value):
								print ""
								raise osv.except_osv(_('Warning!'),
										_('Actual value should lesser or equal to Maximum value !!'))
								
				### Last Operation Check ###
				cr.execute(""" select id from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s and is_last_operation = 't' """ %(entry_rec.op1_id.id,entry_rec.op1_stage_id.id,entry_rec.position_id.id))
				last_operation_id = cr.fetchone()
				print "last_operation_id------------------>>>",last_operation_id
				pending_operation_id = []
				if last_operation_id:
					cr.execute(""" select id from kg_ms_operations

						where

						op2_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op2_state in ('pending','partial')  and  op2_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op3_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op3_state in ('pending','partial')  and  op3_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op4_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op4_state in ('pending','partial')  and  op4_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op5_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op5_state in ('pending','partial')  and  op5_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op6_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op6_state in ('pending','partial')  and  op6_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op7_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op7_state in ('pending','partial')  and  op7_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op8_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op8_state in ('pending','partial')  and  op8_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op9_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op9_state in ('pending','partial')  and  op9_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op10_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op10_state in ('pending','partial')  and  op10_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op11_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op11_state in ('pending','partial')  and  op11_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op12_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op12_state in ('pending','partial')  and  op12_sc_status = 'inhouse' and last_operation_check_id = %s


						limit 1
						""" 
						%(
						entry_rec.position_id.id,entry_rec.op1_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op1_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op1_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op1_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op1_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op1_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op1_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op1_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op1_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op1_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op1_id.id,
						entry_rec.position_id.id,entry_rec.id,
						))
					pending_operation_id = cr.fetchone()
					if pending_operation_id:
						if pending_operation_id[0] > 0:
							if entry_rec.op1_process_result != 'reject':
								raise osv.except_osv(_('Warning!'),
										_('This is last operation. Previous operations yet to be complete. !!'))
									
				### Cost Incurred Calculation ###
				cr.execute(""" select in_house_cost from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s limit 1 """ %(entry_rec.op1_id.id,entry_rec.op1_stage_id.id,entry_rec.position_id.id))
				inhouse_cost = cr.fetchone()
				cost_incurred = 0.00
				if inhouse_cost:
					
					if inhouse_cost[0] >= 0:
						cost_incurred = entry_rec.op1_total_time * inhouse_cost[0]
				
				self.write(cr,uid, ids,{'op1_cost_incurred':cost_incurred})
				if entry_rec.op1_process_result != 'rework':
					self.write(cr,uid, ids,{'op1_state': 'done','op1_button_status':'invisible'})
					
				### Operation Completion ###
				if last_operation_id:
					print "pending_operation_id",pending_operation_id
					print "last_operation_id[0]",last_operation_id[0]
					if pending_operation_id == None and last_operation_id[0] > 0:
						cr.execute(""" select id from kg_ms_operations

							where

							op2_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op2_state in ('pending','partial')  and  op2_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op3_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op3_state in ('pending','partial')  and  op3_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op4_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op4_state in ('pending','partial')  and  op4_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op5_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op5_state in ('pending','partial')  and  op5_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op6_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op6_state in ('pending','partial')  and  op6_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op7_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op7_state in ('pending','partial')  and  op7_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op8_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op8_state in ('pending','partial')  and  op8_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op9_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op9_state in ('pending','partial')  and  op9_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op10_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op10_state in ('pending','partial')  and  op10_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op11_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op11_state in ('pending','partial')  and  op11_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op12_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op12_state in ('pending','partial')  and  op12_sc_status = 'sc' and last_operation_check_id = %s


							limit 1
							""" 
							%(
							entry_rec.position_id.id,entry_rec.op1_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op1_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op1_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op1_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op1_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op1_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op1_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op1_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op1_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op1_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op1_id.id,
							entry_rec.position_id.id,entry_rec.id,
							))
						pending_operation = cr.fetchone()
						print "pending_operation",pending_operation
						if pending_operation == None:
							if entry_rec.op1_process_result == 'accept':
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_completed_qty': entry_rec.ms_id.ms_completed_qty + entry_rec.inhouse_qty})
								ms_store_vals = {
									'operation_id': entry_rec.id,
									'production_id': entry_rec.production_id.id,
									'foundry_assembly_id': entry_rec.production_id.assembly_id,
									'foundry_assembly_line_id': entry_rec.production_id.assembly_line_id,
									'ms_assembly_id': entry_rec.ms_id.assembly_id,
									'ms_assembly_line_id': entry_rec.ms_id.assembly_line_id,
									'qty': entry_rec.inhouse_qty
								}
								ms_store_id = self.pool.get('kg.ms.stores').create(cr, uid, ms_store_vals)
							if (entry_rec.ms_id.ms_completed_qty + entry_rec.ms_id.ms_rejected_qty) == entry_rec.ms_id.ms_sch_qty:
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_state':'op_completed'})
				
				if entry_rec.op1_process_result == 'reject':
				
					
					### Department Indent Creation when process result is reject for ms item ###
					if entry_rec.ms_type == 'ms_item':
						
						## Operation 1 Status Updation ###
						if entry_rec.op1_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op1_state':'reject'})
						self.write(cr, uid, ids, {'state':'reject'})
						if entry_rec.ms_id.ms_id.line_ids:
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP2')])
							
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry_rec.entry_date))
							seq_name = cr.fetchone();

							dep_indent_obj = self.pool.get('kg.depindent')
							dep_indent_vals = {
								'name':'',
								'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
								'dep_name':1,
								'entry_mode':'auto',
								'state': 'approved',
								'indent_type': 'production',
								'name': seq_name[0],
								'order_id': entry_rec.order_id.id,
								'order_line_id': entry_rec.order_line_id.id,
								'src_location_id': location.main_location.id,
								'dest_location_id': location.stock_location.id
								}
								
							indent_id = dep_indent_obj.create(cr, uid, dep_indent_vals)
							for indent_item in entry_rec.ms_id.ms_id.line_ids:
								dep_indent_line_obj = self.pool.get('kg.depindent.line')
								product_rec = self.pool.get('product.product').browse(cr, uid, indent_item.product_id.id)
								dep_indent_line_vals = {
								'indent_id':indent_id,
								'product_id': indent_item.product_id.id,
								'uom': product_rec.uom_id.id,
								'qty': indent_item.qty * entry_rec.inhouse_qty,
								'pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								'issue_pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								#~ 'cutting_qty':ms_raw_rec.temp_qty,
								'ms_bot_id':entry_rec.ms_id.ms_id.id,
								'fns_item_name':entry_rec.item_name,
								'position_id': entry_rec.position_id.id,
								'moc_id': entry_rec.moc_id.id,
								'length': indent_item.length,
								'breadth': indent_item.breadth
								}
								
								indent_line_id = dep_indent_line_obj.create(cr, uid, dep_indent_line_vals)
								
								indent_wo_line_obj = self.pool.get('ch.depindent.wo')
							
								indent_wo_line_vals = {
									'header_id':indent_line_id,
									'wo_id':entry_rec.order_no,
									'w_order_id':entry_rec.order_id.id,
									'w_order_line_id':entry_rec.order_line_id.id,
									'qty':indent_item.qty * entry_rec.inhouse_qty,
								}
								indent_wo_line_id = indent_wo_line_obj.create(cr, uid, indent_wo_line_vals)
						
						### New Entry Creation for same Operation ###
						
						op_vals = {
							'ms_id': entry_rec.ms_id.id,
							'ms_plan_id': entry_rec.ms_plan_id.id,
							'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
							'inhouse_qty': 1,
							'op1_stage_id': entry_rec.op1_stage_id.id,
							'op1_clamping_area': entry_rec.op1_clamping_area,
							'op1_id': entry_rec.op1_id.id,
							'parent_id' : ids[0],
							'last_operation_check_id': entry_rec.last_operation_check_id,
							'state': 'active',
							'op1_state': 'pending',
							'op1_process_result':'',
							}			
						copy_id = self.copy(cr, uid, entry_rec.id,op_vals, context)
						
						copy_rec = self.browse(cr, uid, copy_id)
						
						for dimen_item in copy_rec.op1_line_ids:
							
							dimen_vals = {
								'actual_val': 0,
								'remark': False,
							}
							
							dimension_obj = self.pool.get('ch.ms.dimension.details')
							dimension_obj.write(cr, uid, dimen_item.id, dimen_vals, context)
						
					if entry_rec.ms_type == 'foundry_item':
						
						ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_rejected_qty': entry_rec.ms_id.ms_rejected_qty + entry_rec.inhouse_qty})
						
						## Operation 1 Status Updation ###
						if entry_rec.op1_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op1_state':'reject'})
							
						self.write(cr, uid, ids, {'state':'reject'})
								
						#### NC Creation for reject Qty ###
						
						### Production Number ###
						produc_name = ''	
						produc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.production')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,produc_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(produc_seq_id[0],rec.code,entry_rec.entry_date))
						produc_name = cr.fetchone();
						
						### Issue Number ###
						issue_name = ''	
						issue_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pattern.issue')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,issue_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(issue_seq_id[0],rec.code,entry_rec.entry_date))
						issue_name = cr.fetchone();
						
						### Core Log Number ###
						core_name = ''	
						core_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,core_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_seq_id[0],rec.code,entry_rec.entry_date))
						core_name = cr.fetchone();
						
						### Mould Log Number ###
						mould_name = ''	
						mould_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,mould_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_seq_id[0],rec.code,entry_rec.entry_date))
						mould_name = cr.fetchone();
						
						production_vals = {
												
							'name': produc_name[0],
							'schedule_id': entry_rec.ms_id.schedule_id.id,
							'schedule_date': entry_rec.ms_id.schedule_date,
							'division_id': entry_rec.ms_id.division_id.id,
							'location' : entry_rec.ms_id.location,
							'schedule_line_id': entry_rec.ms_id.schedule_line_id.id,
							'order_id': entry_rec.ms_id.order_id.id,
							'order_line_id': entry_rec.ms_id.order_line_id.id,
							'order_bomline_id': entry_rec.ms_id.order_bomline_id.id,
							'qty' : entry_rec.inhouse_qty,			  
							'schedule_qty' : entry_rec.inhouse_qty,			  
							'state' : 'issue_done',
							'order_category':entry_rec.ms_id.order_category,
							'order_priority': '1',
							'pattern_id' : entry_rec.ms_id.pattern_id.id,
							'pattern_name' : entry_rec.ms_id.pattern_id.pattern_name,	
							'moc_id' : entry_rec.ms_id.moc_id.id,
							'request_state': 'done',
							'issue_no': issue_name[0],
							'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'issue_qty': 1,
							'issue_state': 'issued',
							'core_no': core_name[0],
							'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'core_qty': entry_rec.inhouse_qty,	
							'core_rem_qty': entry_rec.inhouse_qty,	
							'core_state': 'pending',
							'mould_no': mould_name[0],
							'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'mould_qty': entry_rec.inhouse_qty,	
							'mould_rem_qty': entry_rec.inhouse_qty,	
							'mould_state': 'pending',		
						}
						
						production_id = self.pool.get('kg.production').create(cr, uid, production_vals)
					
			else:
				if entry_rec.op1_button_status == 'visible':	
					sc_obj = self.pool.get('kg.subcontract.process')
				
					self.write(cr, uid, ids, {'op1_sc_status': 'sc','op1_button_status': 'invisible'})	
					sc_name = ''	
					sc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.process')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,sc_seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(sc_seq_id[0],seq_rec.code))
					sc_name = cr.fetchone();
					
					wo_id = self.pool.get('kg.work.order').search(cr, uid, [('flag_for_stock','=','t')])
					if entry_rec.order_id.id == wo_id[0]:
						sc_actual_qty = 0
					else:
						sc_actual_qty = entry_rec.inhouse_qty
					
					
					sc_vals = {
						'name': sc_name[0],
						'ms_plan_id': entry_rec.ms_plan_id.id,
						'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
						'sc_qty': entry_rec.inhouse_qty,
						'total_qty': entry_rec.inhouse_qty,
						'pending_qty': entry_rec.inhouse_qty,
						'actual_qty': sc_actual_qty,
						'ms_op_id': entry_rec.id,
						'contractor_id': entry_rec.op1_contractor_id.id,
					}
					sc_id = sc_obj.create(cr, uid,sc_vals)
		else:
			pass	
		
		
		return True
		
		
	### Operation 2 ###
		
	
	def onchange_operation2_sc(self, cr, uid, ids,op2_flag_sc, context=None):
		value = {'op2_sc_status': 'inhouse'}
		if op2_flag_sc == True:
			value = {'op2_sc_status': 'sc'}
		return {'value': value}
		
	def onchange_operation2_time(self, cr, uid, ids,op2_start_time,op2_end_time, context=None):
		value = {'op2_total_time': 0.00}
		total_time = 0.00
		total_time = op2_end_time - op2_start_time
		value = {'op2_total_time': total_time}
		return {'value': value}
		
	def onchange_operation2_cost_incurred(self, cr, uid, ids,op2_id,op2_stage_id,position_id,op2_total_time, context=None):
		value = {'op2_cost_incurred': 0.00}
		### Cost Incurred Calculation ###
		cr.execute(""" select in_house_cost from ch_kg_position_number 
			where operation_id = %s and stage_id = %s
			and header_id = %s limit 1 """ %(op2_id,op2_stage_id,position_id))
		inhouse_cost = cr.fetchone()
		cost_incurred = 0.00
		if inhouse_cost:
			
			if inhouse_cost[0] >= 0:
				cost_incurred = op2_total_time * inhouse_cost[0]
		value = {'op2_cost_incurred': cost_incurred}
		return {'value': value}
		
	
		
	def operation2_update(self, cr, uid, ids, context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		ms_obj = self.pool.get('kg.machineshop')
		
		if entry_rec.op2_state == 'pending':
			if entry_rec.op2_flag_sc != True:
			
				for dim_item in entry_rec.op2_line_ids:
					
					today = date.today()
					today = str(today)
					today = datetime.strptime(today, '%Y-%m-%d')
					start_date = entry_rec.op2_start_date
					start_date = str(start_date)
					start_date = datetime.strptime(start_date, '%Y-%m-%d')
					end_date = entry_rec.op2_end_date
					end_date = str(end_date)
					end_date = datetime.strptime(end_date, '%Y-%m-%d')
					if start_date > today or end_date > today:
						raise osv.except_osv(_('Warning!'),
								_('Start and End date should be less than or equal to current date !!'))
								
					if entry_rec.op2_start_time == entry_rec.op2_end_time:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not be equal !!'))
								
					if entry_rec.op2_start_time > 24 or entry_rec.op2_end_time > 24:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not exceed 24 hrs !!'))
					
					if dim_item.actual_val < 0:
						raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative. Check the actual value !!'))
					
					#~ if entry_rec.op2_process_result != 'reject':			
						#~ 
						#~ if dim_item.actual_val == 0:
							#~ raise osv.except_osv(_('Warning!'),
									#~ _('System not allow to save zero values. Check the actual value !!'))
									
						#### Min and Max Tolerance Checking ####
						
						if dim_item.pos_dimension_id != None:
						
							min_tol_value = (dim_item.min_val * dim_item.pos_dimension_id.min_tolerance) / 100
							max_tol_value = (dim_item.max_val * dim_item.pos_dimension_id.max_tolerance) / 100
									
							if dim_item.actual_val < (dim_item.min_val - min_tol_value):
								print ""
								raise osv.except_osv(_('Warning!'),
										_('Actual value should greater or equal to Minimum value !!'))
										
							if dim_item.actual_val > (dim_item.max_val + max_tol_value):
								print ""
								raise osv.except_osv(_('Warning!'),
										_('Actual value should lesser or equal to Maximum value !!'))
				
				### Last Operation Check ###
				cr.execute(""" select id from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s and is_last_operation = 't' """ %(entry_rec.op2_id.id,entry_rec.op2_stage_id.id,entry_rec.position_id.id))
				last_operation_id = cr.fetchone()
				
				pending_operation_id = []
				if last_operation_id:
					cr.execute(""" select id from kg_ms_operations

						where

						op1_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op2_state in ('pending','partial')  and  op2_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op3_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op3_state in ('pending','partial')  and  op3_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op4_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op4_state in ('pending','partial')  and  op4_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op5_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op5_state in ('pending','partial')  and  op5_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op6_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op6_state in ('pending','partial')  and  op6_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op7_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op7_state in ('pending','partial')  and  op7_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op8_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op8_state in ('pending','partial')  and  op8_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op9_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op9_state in ('pending','partial')  and  op9_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op10_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op10_state in ('pending','partial')  and  op10_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op11_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op11_state in ('pending','partial')  and  op11_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op12_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op12_state in ('pending','partial')  and  op12_sc_status = 'inhouse' and last_operation_check_id = %s


						limit 1
						""" 
						%(
						entry_rec.position_id.id,entry_rec.op2_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op2_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op2_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op2_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op2_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op2_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op2_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op2_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op2_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op2_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op2_id.id,
						entry_rec.position_id.id,entry_rec.id,
						))
					pending_operation_id = cr.fetchone()
					if pending_operation_id:
						if pending_operation_id[0] > 0:
							if entry_rec.op2_process_result != 'reject':
								raise osv.except_osv(_('Warning!'),
										_('This is last operation. Previous operations yet to be complete. !!'))
									
				### Cost Incurred Calculation ###
				cr.execute(""" select in_house_cost from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s limit 1 """ %(entry_rec.op2_id.id,entry_rec.op2_stage_id.id,entry_rec.position_id.id))
				inhouse_cost = cr.fetchone()
				cost_incurred = 0.00
				if inhouse_cost:
					
					if inhouse_cost[0] >= 0:
						cost_incurred = entry_rec.op2_total_time * inhouse_cost[0]
				
				self.write(cr,uid, ids,{'op2_cost_incurred':cost_incurred})
				if entry_rec.op2_process_result != 'rework':
					self.write(cr,uid, ids,{'op2_state': 'done','op2_button_status':'invisible'})
				### Operation Completion ###
				if last_operation_id:
					if pending_operation_id == None and last_operation_id[0] > 0:
						cr.execute(""" select id from kg_ms_operations

							where

							op1_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op1_state in ('pending','partial')  and  op1_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op3_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op3_state in ('pending','partial')  and  op3_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op4_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op4_state in ('pending','partial')  and  op4_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op5_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op5_state in ('pending','partial')  and  op5_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op6_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op6_state in ('pending','partial')  and  op6_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op7_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op7_state in ('pending','partial')  and  op7_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op8_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op8_state in ('pending','partial')  and  op8_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op9_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op9_state in ('pending','partial')  and  op9_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op10_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op10_state in ('pending','partial')  and  op10_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op11_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op11_state in ('pending','partial')  and  op11_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op12_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op12_state in ('pending','partial')  and  op12_sc_status = 'sc' and last_operation_check_id = %s


							limit 1
							""" 
							%(
							entry_rec.position_id.id,entry_rec.op2_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op2_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op2_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op2_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op2_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op2_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op2_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op2_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op2_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op2_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op2_id.id,
							entry_rec.position_id.id,entry_rec.id,
							))
						pending_operation = cr.fetchone()
						if pending_operation == None:
							if entry_rec.op2_process_result == 'accept':
								print "entry_rec.ms_id.assembly_line_id",entry_rec.ms_id.assembly_line_id
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_completed_qty': entry_rec.ms_id.ms_completed_qty + entry_rec.inhouse_qty})
								ms_store_vals = {
									'operation_id': entry_rec.id,
									'production_id': entry_rec.production_id.id,
									'foundry_assembly_id': entry_rec.production_id.assembly_id,
									'foundry_assembly_line_id': entry_rec.production_id.assembly_line_id,
									'ms_assembly_id': entry_rec.ms_id.assembly_id,
									'ms_assembly_line_id': entry_rec.ms_id.assembly_line_id,
									'qty': entry_rec.inhouse_qty
								}
								ms_store_id = self.pool.get('kg.ms.stores').create(cr, uid, ms_store_vals)
							if (entry_rec.ms_id.ms_completed_qty + entry_rec.ms_id.ms_rejected_qty) == entry_rec.ms_id.ms_sch_qty:
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_state':'op_completed'})
				
				if entry_rec.op2_process_result == 'reject':
				
					
					### Department Indent Creation when process result is reject for ms item ###
					if entry_rec.ms_type == 'ms_item':
						
						## Operation 2 Status Updation ###
						if entry_rec.op2_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op2_state':'reject'})
						self.write(cr, uid, ids, {'state':'reject'})
						if entry_rec.ms_id.ms_id.line_ids:
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP2')])
							
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry_rec.entry_date))
							seq_name = cr.fetchone();

							dep_indent_obj = self.pool.get('kg.depindent')
							dep_indent_vals = {
								'name':'',
								'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
								'dep_name':1,
								'entry_mode':'auto',
								'state': 'approved',
								'indent_type': 'production',
								'name': seq_name[0],
								'order_id': entry_rec.order_id.id,
								'order_line_id': entry_rec.order_line_id.id,
								'src_location_id': location.main_location.id,
								'dest_location_id': location.stock_location.id
								}
								
							indent_id = dep_indent_obj.create(cr, uid, dep_indent_vals)
							for indent_item in entry_rec.ms_id.ms_id.line_ids:
								dep_indent_line_obj = self.pool.get('kg.depindent.line')
								product_rec = self.pool.get('product.product').browse(cr, uid, indent_item.product_id.id)
								dep_indent_line_vals = {
								'indent_id':indent_id,
								'product_id': indent_item.product_id.id,
								'uom': product_rec.uom_id.id,
								'qty': indent_item.qty * entry_rec.inhouse_qty,
								'pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								'issue_pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								#~ 'cutting_qty':ms_raw_rec.temp_qty,
								'ms_bot_id':entry_rec.ms_id.ms_id.id,
								'fns_item_name':entry_rec.item_name,
								'position_id': entry_rec.position_id.id
								}
								indent_line_id = dep_indent_line_obj.create(cr, uid, dep_indent_line_vals)
								
								indent_wo_line_obj = self.pool.get('ch.depindent.wo')
							
								indent_wo_line_vals = {
									'header_id':indent_line_id,
									'wo_id':entry_rec.order_no,
									'w_order_id':entry_rec.order_id.id,
									'w_order_line_id':entry_rec.order_line_id.id,
									'qty':indent_item.qty * entry_rec.inhouse_qty,
								}
								indent_wo_line_id = indent_wo_line_obj.create(cr, uid, indent_wo_line_vals)
						
						### New Entry Creation for same Operation ###
						op_vals = {
							'ms_id': entry_rec.ms_id.id,
							'ms_plan_id': entry_rec.ms_plan_id.id,
							'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
							'inhouse_qty': 1,
							'op2_stage_id': entry_rec.op2_stage_id.id,
							'op2_clamping_area': entry_rec.op2_clamping_area,
							'op2_id': entry_rec.op2_id.id,
							'parent_id' : ids[0],
							'last_operation_check_id': entry_rec.last_operation_check_id,
							'state': 'active',
							'op2_state': 'pending',
							'op2_process_result':'',
							}			
						copy_id = self.copy(cr, uid, entry_rec.id,op_vals, context)
						
						copy_rec = self.browse(cr, uid, copy_id)
						
						for dimen_item in copy_rec.op2_line_ids:
							
							dimen_vals = {
								'actual_val': 0,
								'remark': False,
							}
							
							dimension_obj = self.pool.get('ch.ms.dimension.details')
							dimension_obj.write(cr, uid, dimen_item.id, dimen_vals, context)
						
					if entry_rec.ms_type == 'foundry_item':
						
						ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_rejected_qty': entry_rec.ms_id.ms_rejected_qty + entry_rec.inhouse_qty})
						
						## Operation 1 Status Updation ###
						if entry_rec.op2_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op2_state':'reject'})
							
						self.write(cr, uid, ids, {'state':'reject'})
								
						#### NC Creation for reject Qty ###
						
						### Production Number ###
						produc_name = ''	
						produc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.production')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,produc_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(produc_seq_id[0],rec.code,entry_rec.entry_date))
						produc_name = cr.fetchone();
						
						### Issue Number ###
						issue_name = ''	
						issue_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pattern.issue')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,issue_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(issue_seq_id[0],rec.code,entry_rec.entry_date))
						issue_name = cr.fetchone();
						
						### Core Log Number ###
						core_name = ''	
						core_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,core_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_seq_id[0],rec.code,entry_rec.entry_date))
						core_name = cr.fetchone();
						
						### Mould Log Number ###
						mould_name = ''	
						mould_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,mould_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_seq_id[0],rec.code,entry_rec.entry_date))
						mould_name = cr.fetchone();
						
						production_vals = {
												
							'name': produc_name[0],
							'schedule_id': entry_rec.ms_id.schedule_id.id,
							'schedule_date': entry_rec.ms_id.schedule_date,
							'division_id': entry_rec.ms_id.division_id.id,
							'location' : entry_rec.ms_id.location,
							'schedule_line_id': entry_rec.ms_id.schedule_line_id.id,
							'order_id': entry_rec.ms_id.order_id.id,
							'order_line_id': entry_rec.ms_id.order_line_id.id,
							'order_bomline_id': entry_rec.ms_id.order_bomline_id.id,
							'qty' : entry_rec.inhouse_qty,			  
							'schedule_qty' : entry_rec.inhouse_qty,			  
							'state' : 'issue_done',
							'order_category':entry_rec.ms_id.order_category,
							'order_priority': '1',
							'pattern_id' : entry_rec.ms_id.pattern_id.id,
							'pattern_name' : entry_rec.ms_id.pattern_id.pattern_name,	
							'moc_id' : entry_rec.ms_id.moc_id.id,
							'request_state': 'done',
							'issue_no': issue_name[0],
							'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'issue_qty': 1,
							'issue_state': 'issued',
							'core_no': core_name[0],
							'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'core_qty': entry_rec.inhouse_qty,	
							'core_rem_qty': entry_rec.inhouse_qty,	
							'core_state': 'pending',
							'mould_no': mould_name[0],
							'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'mould_qty': entry_rec.inhouse_qty,	
							'mould_rem_qty': entry_rec.inhouse_qty,	
							'mould_state': 'pending',		
						}
						
						production_id = self.pool.get('kg.production').create(cr, uid, production_vals)
					
			else:
				if entry_rec.op2_button_status == 'visible':	
					sc_obj = self.pool.get('kg.subcontract.process')
					
					self.write(cr, uid, ids, {'op2_sc_status': 'sc','op2_button_status': 'invisible'})	
					sc_name = ''	
					sc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.process')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,sc_seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(sc_seq_id[0],seq_rec.code))
					sc_name = cr.fetchone();
					
					wo_id = self.pool.get('kg.work.order').search(cr, uid, [('flag_for_stock','=','t')])
					if entry_rec.order_id.id == wo_id[0]:
						sc_actual_qty = 0
					else:
						sc_actual_qty = entry_rec.inhouse_qty
					
					sc_vals = {
						'name': sc_name[0],
						'ms_plan_id': entry_rec.ms_plan_id.id,
						'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
						'sc_qty': entry_rec.inhouse_qty,
						'total_qty': entry_rec.inhouse_qty,
						'pending_qty': entry_rec.inhouse_qty,
						'actual_qty': sc_actual_qty,
						'ms_op_id': entry_rec.id,
						'contractor_id': entry_rec.op2_contractor_id.id,
					}
					sc_id = sc_obj.create(cr, uid,sc_vals)
		else:
			pass			
				
		return True
		
	### Operation 3 ###
		
	
	def onchange_operation3_sc(self, cr, uid, ids,op3_flag_sc, context=None):
		value = {'op3_sc_status': 'inhouse'}
		if op3_flag_sc == True:
			value = {'op3_sc_status': 'sc'}
		return {'value': value}
		
	def onchange_operation3_time(self, cr, uid, ids,op3_start_time,op3_end_time, context=None):
		value = {'op3_total_time': 0.00}
		total_time = 0.00
		total_time = op3_end_time - op3_start_time
		value = {'op3_total_time': total_time}
		return {'value': value}
		
	def onchange_operation3_cost_incurred(self, cr, uid, ids,op3_id,op3_stage_id,position_id,op3_total_time, context=None):
		value = {'op3_cost_incurred': 0.00}
		### Cost Incurred Calculation ###
		cr.execute(""" select in_house_cost from ch_kg_position_number 
			where operation_id = %s and stage_id = %s
			and header_id = %s limit 1 """ %(op3_id,op3_stage_id,position_id))
		inhouse_cost = cr.fetchone()
		cost_incurred = 0.00
		if inhouse_cost:
			
			if inhouse_cost[0] >= 0:
				cost_incurred = op3_total_time * inhouse_cost[0]
		value = {'op3_cost_incurred': cost_incurred}
		return {'value': value}
			
	def operation3_update(self, cr, uid, ids, context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		ms_obj = self.pool.get('kg.machineshop')
		
		if entry_rec.op3_state == 'pending':
			if entry_rec.op3_flag_sc != True:
			
				for dim_item in entry_rec.op3_line_ids:
					
					today = date.today()
					today = str(today)
					today = datetime.strptime(today, '%Y-%m-%d')
					start_date = entry_rec.op3_start_date
					start_date = str(start_date)
					start_date = datetime.strptime(start_date, '%Y-%m-%d')
					end_date = entry_rec.op3_end_date
					end_date = str(end_date)
					end_date = datetime.strptime(end_date, '%Y-%m-%d')
					if start_date > today or end_date > today:
						raise osv.except_osv(_('Warning!'),
								_('Start and End date should be less than or equal to current date!!'))
								
					if entry_rec.op3_start_time == entry_rec.op3_end_time:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not be equal !!'))
								
					if entry_rec.op3_start_time > 24 or entry_rec.op3_end_time > 24:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not exceed 24 hrs !!'))
					
					if dim_item.actual_val < 0:
						raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative. Check the actual value !!'))
					
					#~ if entry_rec.op3_process_result != 'reject':			
						#~ 
						#~ if dim_item.actual_val == 0:
							#~ raise osv.except_osv(_('Warning!'),
									#~ _('System not allow to save zero values. Check the actual value !!'))
									
						#### Min and Max Tolerance Checking ####
						
						if dim_item.pos_dimension_id != None:
						
							min_tol_value = (dim_item.min_val * dim_item.pos_dimension_id.min_tolerance) / 100
							max_tol_value = (dim_item.max_val * dim_item.pos_dimension_id.max_tolerance) / 100
									
							if dim_item.actual_val < (dim_item.min_val - min_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should greater or equal to Minimum value !!'))
										
							if dim_item.actual_val > (dim_item.max_val + max_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should lesser or equal to Maximum value !!'))
								
				### Last Operation Check ###
				cr.execute(""" select id from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s and is_last_operation = 't' """ %(entry_rec.op3_id.id,entry_rec.op3_stage_id.id,entry_rec.position_id.id))
				last_operation_id = cr.fetchone()
				
				pending_operation_id = []
				if last_operation_id:
					cr.execute(""" select id from kg_ms_operations

						where

						op1_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op1_state in ('pending','partial')  and  op1_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op2_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op2_state in ('pending','partial')  and  op2_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op4_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op4_state in ('pending','partial')  and  op4_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op5_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op5_state in ('pending','partial')  and  op5_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op6_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op6_state in ('pending','partial')  and  op6_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op7_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op7_state in ('pending','partial')  and  op7_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op8_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op8_state in ('pending','partial')  and  op8_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op9_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op9_state in ('pending','partial')  and  op9_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op10_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op10_state in ('pending','partial')  and  op10_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op11_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op11_state in ('pending','partial')  and  op11_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op12_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op12_state in ('pending','partial')  and  op12_sc_status = 'inhouse' and last_operation_check_id = %s


						limit 1
						""" 
						%(
						entry_rec.position_id.id,entry_rec.op3_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op3_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op3_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op3_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op3_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op3_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op3_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op3_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op3_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op3_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op3_id.id,
						entry_rec.position_id.id,entry_rec.id,
						))
					pending_operation_id = cr.fetchone()
					if pending_operation_id:
						if pending_operation_id[0] > 0:
							if entry_rec.op3_process_result != 'reject':
								raise osv.except_osv(_('Warning!'),
										_('This is last operation. Previous operations yet to be complete. !!'))
									
				### Cost Incurred Calculation ###
				cr.execute(""" select in_house_cost from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s limit 1 """ %(entry_rec.op3_id.id,entry_rec.op3_stage_id.id,entry_rec.position_id.id))
				inhouse_cost = cr.fetchone()
				cost_incurred = 0.00
				if inhouse_cost:
					
					if inhouse_cost[0] >= 0:
						cost_incurred = entry_rec.op3_total_time * inhouse_cost[0]
				
				self.write(cr,uid, ids,{'op3_cost_incurred':cost_incurred})
				if entry_rec.op3_process_result != 'rework':
					self.write(cr,uid, ids,{'op3_state': 'done','op3_button_status':'invisible'})
				### Operation Completion ###
				if last_operation_id:
					if pending_operation_id == None and last_operation_id[0] > 0:
						cr.execute(""" select id from kg_ms_operations

							where

							op1_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op1_state in ('pending','partial')  and  op1_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op2_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op2_state in ('pending','partial')  and  op2_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op4_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op4_state in ('pending','partial')  and  op4_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op5_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op5_state in ('pending','partial')  and  op5_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op6_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op6_state in ('pending','partial')  and  op6_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op7_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op7_state in ('pending','partial')  and  op7_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op8_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op8_state in ('pending','partial')  and  op8_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op9_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op9_state in ('pending','partial')  and  op9_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op10_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op10_state in ('pending','partial')  and  op10_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op11_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op11_state in ('pending','partial')  and  op11_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op12_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op12_state in ('pending','partial')  and  op12_sc_status = 'sc' and last_operation_check_id = %s


							limit 1
							""" 
							%(
							entry_rec.position_id.id,entry_rec.op3_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op3_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op3_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op3_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op3_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op3_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op3_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op3_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op3_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op3_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op3_id.id,
							entry_rec.position_id.id,entry_rec.id,
							))
						pending_operation = cr.fetchone()
						if pending_operation == None:
							if entry_rec.op3_process_result == 'accept':
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_completed_qty': entry_rec.ms_id.ms_completed_qty + entry_rec.inhouse_qty})
								ms_store_vals = {
									'operation_id': entry_rec.id,
									'production_id': entry_rec.production_id.id,
									'foundry_assembly_id': entry_rec.production_id.assembly_id,
									'foundry_assembly_line_id': entry_rec.production_id.assembly_line_id,
									'ms_assembly_id': entry_rec.ms_id.assembly_id,
									'ms_assembly_line_id': entry_rec.ms_id.assembly_line_id,
									'qty': entry_rec.inhouse_qty
								}
								ms_store_id = self.pool.get('kg.ms.stores').create(cr, uid, ms_store_vals)
							if (entry_rec.ms_id.ms_completed_qty + entry_rec.ms_id.ms_rejected_qty) == entry_rec.ms_id.ms_sch_qty:
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_state':'op_completed'})
				
				if entry_rec.op3_process_result == 'reject':
				
					
					### Department Indent Creation when process result is reject for ms item ###
					if entry_rec.ms_type == 'ms_item':
						
						## Operation 2 Status Updation ###
						if entry_rec.op3_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op3_state':'reject'})
						self.write(cr, uid, ids, {'state':'reject'})
						if entry_rec.ms_id.ms_id.line_ids:
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP2')])
							
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry_rec.entry_date))
							seq_name = cr.fetchone();

							dep_indent_obj = self.pool.get('kg.depindent')
							dep_indent_vals = {
								'name':'',
								'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
								'dep_name':1,
								'entry_mode':'auto',
								'state': 'approved',
								'indent_type': 'production',
								'name': seq_name[0],
								'order_id': entry_rec.order_id.id,
								'order_line_id': entry_rec.order_line_id.id,
								'src_location_id': location.main_location.id,
								'dest_location_id': location.stock_location.id
								}
								
							indent_id = dep_indent_obj.create(cr, uid, dep_indent_vals)
							for indent_item in entry_rec.ms_id.ms_id.line_ids:
								dep_indent_line_obj = self.pool.get('kg.depindent.line')
								product_rec = self.pool.get('product.product').browse(cr, uid, indent_item.product_id.id)
								dep_indent_line_vals = {
								'indent_id':indent_id,
								'product_id': indent_item.product_id.id,
								'uom': product_rec.uom_id.id,
								'qty': indent_item.qty * entry_rec.inhouse_qty,
								'pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								'issue_pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								#~ 'cutting_qty':ms_raw_rec.temp_qty,
								'ms_bot_id':entry_rec.ms_id.ms_id.id,
								'fns_item_name':entry_rec.item_name,
								'position_id': entry_rec.position_id.id
								}
								
								indent_line_id = dep_indent_line_obj.create(cr, uid, dep_indent_line_vals)
								
								indent_wo_line_obj = self.pool.get('ch.depindent.wo')
							
								indent_wo_line_vals = {
									'header_id':indent_line_id,
									'wo_id':entry_rec.order_no,
									'w_order_id':entry_rec.order_id.id,
									'w_order_line_id':entry_rec.order_line_id.id,
									'qty':indent_item.qty * entry_rec.inhouse_qty,
								}
								indent_wo_line_id = indent_wo_line_obj.create(cr, uid, indent_wo_line_vals)
						
						### New Entry Creation for same Operation ###
						op_vals = {
							'ms_id': entry_rec.ms_id.id,
							'ms_plan_id': entry_rec.ms_plan_id.id,
							'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
							'inhouse_qty': 1,
							'op3_stage_id': entry_rec.op3_stage_id.id,
							'op3_clamping_area': entry_rec.op3_clamping_area,
							'op3_id': entry_rec.op3_id.id,
							'parent_id' : ids[0],
							'last_operation_check_id': entry_rec.last_operation_check_id,
							'state': 'active',
							'op3_state': 'pending',
							'op3_process_result':'',
							}			
						copy_id = self.copy(cr, uid, entry_rec.id,op_vals, context)
						
						copy_rec = self.browse(cr, uid, copy_id)
						
						for dimen_item in copy_rec.op3_line_ids:
							
							dimen_vals = {
								'actual_val': 0,
								'remark': False,
							}
							
							dimension_obj = self.pool.get('ch.ms.dimension.details')
							dimension_obj.write(cr, uid, dimen_item.id, dimen_vals, context)
						
					if entry_rec.ms_type == 'foundry_item':
						
						ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_rejected_qty': entry_rec.ms_id.ms_rejected_qty + entry_rec.inhouse_qty})
						
						## Operation 3 Status Updation ###
						if entry_rec.op3_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op3_state':'reject'})
							
						self.write(cr, uid, ids, {'state':'reject'})
								
						#### NC Creation for reject Qty ###
						
						### Production Number ###
						produc_name = ''	
						produc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.production')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,produc_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(produc_seq_id[0],rec.code,entry_rec.entry_date))
						produc_name = cr.fetchone();
						
						### Issue Number ###
						issue_name = ''	
						issue_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pattern.issue')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,issue_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(issue_seq_id[0],rec.code,entry_rec.entry_date))
						issue_name = cr.fetchone();
						
						### Core Log Number ###
						core_name = ''	
						core_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,core_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_seq_id[0],rec.code,entry_rec.entry_date))
						core_name = cr.fetchone();
						
						### Mould Log Number ###
						mould_name = ''	
						mould_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,mould_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_seq_id[0],rec.code,entry_rec.entry_date))
						mould_name = cr.fetchone();
						
						production_vals = {
												
							'name': produc_name[0],
							'schedule_id': entry_rec.ms_id.schedule_id.id,
							'schedule_date': entry_rec.ms_id.schedule_date,
							'division_id': entry_rec.ms_id.division_id.id,
							'location' : entry_rec.ms_id.location,
							'schedule_line_id': entry_rec.ms_id.schedule_line_id.id,
							'order_id': entry_rec.ms_id.order_id.id,
							'order_line_id': entry_rec.ms_id.order_line_id.id,
							'order_bomline_id': entry_rec.ms_id.order_bomline_id.id,
							'qty' : entry_rec.inhouse_qty,			  
							'schedule_qty' : entry_rec.inhouse_qty,			  
							'state' : 'issue_done',
							'order_category':entry_rec.ms_id.order_category,
							'order_priority': '1',
							'pattern_id' : entry_rec.ms_id.pattern_id.id,
							'pattern_name' : entry_rec.ms_id.pattern_id.pattern_name,	
							'moc_id' : entry_rec.ms_id.moc_id.id,
							'request_state': 'done',
							'issue_no': issue_name[0],
							'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'issue_qty': 1,
							'issue_state': 'issued',
							'core_no': core_name[0],
							'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'core_qty': entry_rec.inhouse_qty,	
							'core_rem_qty': entry_rec.inhouse_qty,	
							'core_state': 'pending',
							'mould_no': mould_name[0],
							'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'mould_qty': entry_rec.inhouse_qty,	
							'mould_rem_qty': entry_rec.inhouse_qty,	
							'mould_state': 'pending',		
						}
						
						production_id = self.pool.get('kg.production').create(cr, uid, production_vals)
					
			else:
				if entry_rec.op3_button_status == 'visible':
					sc_obj = self.pool.get('kg.subcontract.process')
					
					self.write(cr, uid, ids, {'op3_sc_status': 'sc','op3_button_status': 'invisible'})	
					sc_name = ''	
					sc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.process')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,sc_seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(sc_seq_id[0],seq_rec.code))
					sc_name = cr.fetchone();
					
					wo_id = self.pool.get('kg.work.order').search(cr, uid, [('flag_for_stock','=','t')])
					if entry_rec.order_id.id == wo_id[0]:
						sc_actual_qty = 0
					else:
						sc_actual_qty = entry_rec.inhouse_qty
					
					sc_vals = {
						'name': sc_name[0],
						'ms_plan_id': entry_rec.ms_plan_id.id,
						'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
						'sc_qty': entry_rec.inhouse_qty,
						'total_qty': entry_rec.inhouse_qty,
						'pending_qty': entry_rec.inhouse_qty,
						'actual_qty': sc_actual_qty,
						'ms_op_id': entry_rec.id,
						'contractor_id': entry_rec.op3_contractor_id.id,
					}
					sc_id = sc_obj.create(cr, uid,sc_vals)
				
		else:
			pass
						
				
		return True
		
	### Operation 4 ###
		
	
	def onchange_operation4_sc(self, cr, uid, ids,op4_flag_sc, context=None):
		value = {'op4_sc_status': 'inhouse'}
		if op4_flag_sc == True:
			value = {'op4_sc_status': 'sc'}
		return {'value': value}
		
	def onchange_operation4_time(self, cr, uid, ids,op4_start_time,op4_end_time, context=None):
		value = {'op4_total_time': 0.00}
		total_time = 0.00
		total_time = op4_end_time - op4_start_time
		value = {'op4_total_time': total_time}
		return {'value': value}
		
	def onchange_operation4_cost_incurred(self, cr, uid, ids,op4_id,op4_stage_id,position_id,op4_total_time, context=None):
		value = {'op4_cost_incurred': 0.00}
		### Cost Incurred Calculation ###
		cr.execute(""" select in_house_cost from ch_kg_position_number 
			where operation_id = %s and stage_id = %s
			and header_id = %s limit 1 """ %(op4_id,op4_stage_id,position_id))
		inhouse_cost = cr.fetchone()
		cost_incurred = 0.00
		if inhouse_cost:
			
			if inhouse_cost[0] >= 0:
				cost_incurred = op4_total_time * inhouse_cost[0]
		value = {'op4_cost_incurred': cost_incurred}
		return {'value': value}
			
	def operation4_update(self, cr, uid, ids, context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		ms_obj = self.pool.get('kg.machineshop')
		
		if entry_rec.op4_state == 'pending':
			if entry_rec.op4_flag_sc != True:
			
				for dim_item in entry_rec.op4_line_ids:
					
					today = date.today()
					today = str(today)
					today = datetime.strptime(today, '%Y-%m-%d')
					start_date = entry_rec.op4_start_date
					start_date = str(start_date)
					start_date = datetime.strptime(start_date, '%Y-%m-%d')
					end_date = entry_rec.op4_end_date
					end_date = str(end_date)
					end_date = datetime.strptime(end_date, '%Y-%m-%d')
					if start_date > today or end_date > today:
						raise osv.except_osv(_('Warning!'),
								_('Start and End date should be less than or equal to current date!!'))
								
					if entry_rec.op4_start_time == entry_rec.op4_end_time:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not be equal !!'))
								
					if entry_rec.op4_start_time > 24 or entry_rec.op4_end_time > 24:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not exceed 24 hrs !!'))
					
					if dim_item.actual_val < 0:
						raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative. Check the actual value !!'))
					
					#~ if entry_rec.op4_process_result != 'reject':			
						#~ 
						#~ if dim_item.actual_val == 0:
							#~ raise osv.except_osv(_('Warning!'),
									#~ _('System not allow to save zero values. Check the actual value !!'))
									
						#### Min and Max Tolerance Checking ####
						
						if dim_item.pos_dimension_id != None:
						
							min_tol_value = (dim_item.min_val * dim_item.pos_dimension_id.min_tolerance) / 100
							max_tol_value = (dim_item.max_val * dim_item.pos_dimension_id.max_tolerance) / 100
									
							if dim_item.actual_val < (dim_item.min_val - min_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should greater or equal to Minimum value !!'))
										
							if dim_item.actual_val > (dim_item.max_val + max_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should lesser or equal to Maximum value !!'))
								
				### Last Operation Check ###
				cr.execute(""" select id from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s and is_last_operation = 't' """ %(entry_rec.op4_id.id,entry_rec.op4_stage_id.id,entry_rec.position_id.id))
				last_operation_id = cr.fetchone()
				
				pending_operation_id = []
				if last_operation_id:
					cr.execute(""" select id from kg_ms_operations

						where

						op2_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op2_state in ('pending','partial')  and  op2_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op3_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op3_state in ('pending','partial')  and  op3_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op1_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op1_state in ('pending','partial')  and  op1_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op5_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op5_state in ('pending','partial')  and  op5_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op6_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op6_state in ('pending','partial')  and  op6_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op7_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op7_state in ('pending','partial')  and  op7_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op8_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op8_state in ('pending','partial')  and  op8_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op9_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op9_state in ('pending','partial')  and  op9_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op10_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op10_state in ('pending','partial')  and  op10_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op11_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op11_state in ('pending','partial')  and  op11_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op12_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op12_state in ('pending','partial')  and  op12_sc_status = 'inhouse' and last_operation_check_id = %s


						limit 1
						""" 
						%(
						entry_rec.position_id.id,entry_rec.op4_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op4_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op4_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op4_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op4_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op4_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op4_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op4_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op4_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op4_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op4_id.id,
						entry_rec.position_id.id,entry_rec.id,
						))
					pending_operation_id = cr.fetchone()
					if pending_operation_id:
						if pending_operation_id[0] > 0:
							if entry_rec.op4_process_result != 'reject':
								raise osv.except_osv(_('Warning!'),
										_('This is last operation. Previous operations yet to be complete. !!'))
									
				### Cost Incurred Calculation ###
				cr.execute(""" select in_house_cost from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s limit 1 """ %(entry_rec.op4_id.id,entry_rec.op4_stage_id.id,entry_rec.position_id.id))
				inhouse_cost = cr.fetchone()
				cost_incurred = 0.00
				if inhouse_cost:
					
					if inhouse_cost[0] >= 0:
						cost_incurred = entry_rec.op4_total_time * inhouse_cost[0]
				
				self.write(cr,uid, ids,{'op4_cost_incurred':cost_incurred})
				if entry_rec.op4_process_result != 'rework':
					self.write(cr,uid, ids,{'op4_state': 'done','op4_button_status':'invisible'})
				### Operation Completion ###
				if last_operation_id:
					if pending_operation_id == None and last_operation_id[0] > 0:
						cr.execute(""" select id from kg_ms_operations

							where

							op1_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op1_state in ('pending','partial')  and  op1_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op2_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op2_state in ('pending','partial')  and  op2_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op3_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op3_state in ('pending','partial')  and  op3_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op5_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op5_state in ('pending','partial')  and  op5_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op6_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op6_state in ('pending','partial')  and  op6_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op7_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op7_state in ('pending','partial')  and  op7_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op8_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op8_state in ('pending','partial')  and  op8_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op9_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op9_state in ('pending','partial')  and  op9_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op10_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op10_state in ('pending','partial')  and  op10_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op11_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op11_state in ('pending','partial')  and  op11_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op12_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op12_state in ('pending','partial')  and  op12_sc_status = 'sc' and last_operation_check_id = %s


							limit 1
							""" 
							%(
							entry_rec.position_id.id,entry_rec.op4_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op4_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op4_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op4_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op4_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op4_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op4_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op4_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op4_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op4_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op4_id.id,
							entry_rec.position_id.id,entry_rec.id,
							))
						pending_operation = cr.fetchone()
						if pending_operation == None:
							if entry_rec.op4_process_result == 'accept':
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_completed_qty': entry_rec.ms_id.ms_completed_qty + entry_rec.inhouse_qty})
								ms_store_vals = {
									'operation_id': entry_rec.id,
									'production_id': entry_rec.production_id.id,
									'foundry_assembly_id': entry_rec.production_id.assembly_id,
									'foundry_assembly_line_id': entry_rec.production_id.assembly_line_id,
									'ms_assembly_id': entry_rec.ms_id.assembly_id,
									'ms_assembly_line_id': entry_rec.ms_id.assembly_line_id,
									'qty': entry_rec.inhouse_qty
								}
								ms_store_id = self.pool.get('kg.ms.stores').create(cr, uid, ms_store_vals)
							if (entry_rec.ms_id.ms_completed_qty + entry_rec.ms_id.ms_rejected_qty) == entry_rec.ms_id.ms_sch_qty:
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_state':'op_completed'})
				
				if entry_rec.op4_process_result == 'reject':
				
					
					### Department Indent Creation when process result is reject for ms item ###
					if entry_rec.ms_type == 'ms_item':
						
						## Operation 4 Status Updation ###
						if entry_rec.op4_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op4_state':'reject'})
						self.write(cr, uid, ids, {'state':'reject'})
						if entry_rec.ms_id.ms_id.line_ids:
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP2')])
							
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry_rec.entry_date))
							seq_name = cr.fetchone();

							dep_indent_obj = self.pool.get('kg.depindent')
							dep_indent_vals = {
								'name':'',
								'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
								'dep_name':1,
								'entry_mode':'auto',
								'state': 'approved',
								'indent_type': 'production',
								'name': seq_name[0],
								'order_id': entry_rec.order_id.id,
								'order_line_id': entry_rec.order_line_id.id,
								'src_location_id': location.main_location.id,
								'dest_location_id': location.stock_location.id
								}
								
							indent_id = dep_indent_obj.create(cr, uid, dep_indent_vals)
							for indent_item in entry_rec.ms_id.ms_id.line_ids:
								dep_indent_line_obj = self.pool.get('kg.depindent.line')
								product_rec = self.pool.get('product.product').browse(cr, uid, indent_item.product_id.id)
								dep_indent_line_vals = {
								'indent_id':indent_id,
								'product_id': indent_item.product_id.id,
								'uom': product_rec.uom_id.id,
								'qty': indent_item.qty * entry_rec.inhouse_qty,
								'pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								'issue_pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								#~ 'cutting_qty':ms_raw_rec.temp_qty,
								'ms_bot_id':entry_rec.ms_id.ms_id.id,
								'fns_item_name':entry_rec.item_name,
								'position_id': entry_rec.position_id.id
								}
								
								indent_line_id = dep_indent_line_obj.create(cr, uid, dep_indent_line_vals)
								
								indent_wo_line_obj = self.pool.get('ch.depindent.wo')
							
								indent_wo_line_vals = {
									'header_id':indent_line_id,
									'wo_id':entry_rec.order_no,
									'w_order_id':entry_rec.order_id.id,
									'w_order_line_id':entry_rec.order_line_id.id,
									'qty':indent_item.qty * entry_rec.inhouse_qty,
								}
								indent_wo_line_id = indent_wo_line_obj.create(cr, uid, indent_wo_line_vals)
						
						### New Entry Creation for same Operation ###
						op_vals = {
							'ms_id': entry_rec.ms_id.id,
							'ms_plan_id': entry_rec.ms_plan_id.id,
							'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
							'inhouse_qty': 1,
							'op4_stage_id': entry_rec.op4_stage_id.id,
							'op4_clamping_area': entry_rec.op4_clamping_area,
							'op4_id': entry_rec.op4_id.id,
							'parent_id' : ids[0],
							'last_operation_check_id': entry_rec.last_operation_check_id,
							'state': 'active',
							'op4_state': 'pending',
							'op4_process_result':'',
						
						}			
						copy_id = self.copy(cr, uid, entry_rec.id,op_vals, context)
						
						copy_rec = self.browse(cr, uid, copy_id)
						
						for dimen_item in copy_rec.op4_line_ids:
							
							dimen_vals = {
								'actual_val': 0,
								'remark': False,
							}
							
							dimension_obj = self.pool.get('ch.ms.dimension.details')
							dimension_obj.write(cr, uid, dimen_item.id, dimen_vals, context)
						
					if entry_rec.ms_type == 'foundry_item':
						
						ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_rejected_qty': entry_rec.ms_id.ms_rejected_qty + entry_rec.inhouse_qty})
						
						## Operation 4 Status Updation ###
						if entry_rec.op4_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op4_state':'reject'})
							
						self.write(cr, uid, ids, {'state':'reject'})
								
						#### NC Creation for reject Qty ###
						
						### Production Number ###
						produc_name = ''	
						produc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.production')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,produc_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(produc_seq_id[0],rec.code,entry_rec.entry_date))
						produc_name = cr.fetchone();
						
						### Issue Number ###
						issue_name = ''	
						issue_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pattern.issue')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,issue_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(issue_seq_id[0],rec.code,entry_rec.entry_date))
						issue_name = cr.fetchone();
						
						### Core Log Number ###
						core_name = ''	
						core_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,core_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_seq_id[0],rec.code,entry_rec.entry_date))
						core_name = cr.fetchone();
						
						### Mould Log Number ###
						mould_name = ''	
						mould_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,mould_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_seq_id[0],rec.code,entry_rec.entry_date))
						mould_name = cr.fetchone();
						
						production_vals = {
												
							'name': produc_name[0],
							'schedule_id': entry_rec.ms_id.schedule_id.id,
							'schedule_date': entry_rec.ms_id.schedule_date,
							'division_id': entry_rec.ms_id.division_id.id,
							'location' : entry_rec.ms_id.location,
							'schedule_line_id': entry_rec.ms_id.schedule_line_id.id,
							'order_id': entry_rec.ms_id.order_id.id,
							'order_line_id': entry_rec.ms_id.order_line_id.id,
							'order_bomline_id': entry_rec.ms_id.order_bomline_id.id,
							'qty' : entry_rec.inhouse_qty,			  
							'schedule_qty' : entry_rec.inhouse_qty,			  
							'state' : 'issue_done',
							'order_category':entry_rec.ms_id.order_category,
							'order_priority': '1',
							'pattern_id' : entry_rec.ms_id.pattern_id.id,
							'pattern_name' : entry_rec.ms_id.pattern_id.pattern_name,	
							'moc_id' : entry_rec.ms_id.moc_id.id,
							'request_state': 'done',
							'issue_no': issue_name[0],
							'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'issue_qty': 1,
							'issue_state': 'issued',
							'core_no': core_name[0],
							'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'core_qty': entry_rec.inhouse_qty,	
							'core_rem_qty': entry_rec.inhouse_qty,	
							'core_state': 'pending',
							'mould_no': mould_name[0],
							'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'mould_qty': entry_rec.inhouse_qty,	
							'mould_rem_qty': entry_rec.inhouse_qty,	
							'mould_state': 'pending',		
						}
						
						production_id = self.pool.get('kg.production').create(cr, uid, production_vals)
					
			else:
				if entry_rec.op4_button_status == 'visible':
					sc_obj = self.pool.get('kg.subcontract.process')
					
					self.write(cr, uid, ids, {'op4_sc_status': 'sc','op4_button_status': 'invisible'})	
					sc_name = ''	
					sc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.process')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,sc_seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(sc_seq_id[0],seq_rec.code))
					sc_name = cr.fetchone();
					
					wo_id = self.pool.get('kg.work.order').search(cr, uid, [('flag_for_stock','=','t')])
					if entry_rec.order_id.id == wo_id[0]:
						sc_actual_qty = 0
					else:
						sc_actual_qty = entry_rec.inhouse_qty
					
					sc_vals = {
						'name': sc_name[0],
						'ms_plan_id': entry_rec.ms_plan_id.id,
						'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
						'sc_qty': entry_rec.inhouse_qty,
						'total_qty': entry_rec.inhouse_qty,
						'pending_qty': entry_rec.inhouse_qty,
						'actual_qty': sc_actual_qty,
						'ms_op_id': entry_rec.id,
						'contractor_id': entry_rec.op4_contractor_id.id,
					}
					sc_id = sc_obj.create(cr, uid,sc_vals)
				
		else:
			pass
						
				
		return True
		
	### Operation 5 ###
		
	def onchange_operation5_sc(self, cr, uid, ids,op5_flag_sc, context=None):
		value = {'op5_sc_status': 'inhouse'}
		if op5_flag_sc == True:
			value = {'op5_sc_status': 'sc'}
		return {'value': value}
		
	def onchange_operation5_time(self, cr, uid, ids,op5_start_time,op5_end_time, context=None):
		value = {'op5_total_time': 0.00}
		total_time = 0.00
		total_time = op5_end_time - op5_start_time
		value = {'op5_total_time': total_time}
		return {'value': value}
		
	def onchange_operation5_cost_incurred(self, cr, uid, ids,op5_id,op5_stage_id,position_id,op5_total_time, context=None):
		value = {'op5_cost_incurred': 0.00}
		### Cost Incurred Calculation ###
		cr.execute(""" select in_house_cost from ch_kg_position_number 
			where operation_id = %s and stage_id = %s
			and header_id = %s limit 1 """ %(op5_id,op5_stage_id,position_id))
		inhouse_cost = cr.fetchone()
		cost_incurred = 0.00
		if inhouse_cost:
			
			if inhouse_cost[0] >= 0:
				cost_incurred = op5_total_time * inhouse_cost[0]
		value = {'op5_cost_incurred': cost_incurred}
		return {'value': value}
			
	def operation5_update(self, cr, uid, ids, context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		ms_obj = self.pool.get('kg.machineshop')
		
		if entry_rec.op5_state == 'pending':
			if entry_rec.op5_flag_sc != True:
			
				for dim_item in entry_rec.op5_line_ids:
					
					today = date.today()
					today = str(today)
					today = datetime.strptime(today, '%Y-%m-%d')
					start_date = entry_rec.op5_start_date
					start_date = str(start_date)
					start_date = datetime.strptime(start_date, '%Y-%m-%d')
					end_date = entry_rec.op5_end_date
					end_date = str(end_date)
					end_date = datetime.strptime(end_date, '%Y-%m-%d')
					if start_date > today or end_date > today:
						raise osv.except_osv(_('Warning!'),
								_('Start and End date should be less than or equal to current date!!'))
								
					if entry_rec.op5_start_time == entry_rec.op5_end_time:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not be equal !!'))
								
					if entry_rec.op5_start_time > 24 or entry_rec.op5_end_time > 24:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not exceed 24 hrs !!'))
					
					if dim_item.actual_val < 0:
						raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative. Check the actual value !!'))
					
					#~ if entry_rec.op5_process_result != 'reject':			
						#~ 
						#~ if dim_item.actual_val == 0:
							#~ raise osv.except_osv(_('Warning!'),
									#~ _('System not allow to save zero values. Check the actual value !!'))
									
						#### Min and Max Tolerance Checking ####
						
						if dim_item.pos_dimension_id != None:
						
							min_tol_value = (dim_item.min_val * dim_item.pos_dimension_id.min_tolerance) / 100
							max_tol_value = (dim_item.max_val * dim_item.pos_dimension_id.max_tolerance) / 100
									
							if dim_item.actual_val < (dim_item.min_val - min_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should greater or equal to Minimum value !!'))
										
							if dim_item.actual_val > (dim_item.max_val + max_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should lesser or equal to Maximum value !!'))
								
				### Last Operation Check ###
				cr.execute(""" select id from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s and is_last_operation = 't' """ %(entry_rec.op5_id.id,entry_rec.op5_stage_id.id,entry_rec.position_id.id))
				last_operation_id = cr.fetchone()
				
				pending_operation_id = []
				if last_operation_id:
					cr.execute(""" select id from kg_ms_operations

						where

						op2_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op2_state in ('pending','partial')  and  op2_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op3_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op3_state in ('pending','partial')  and  op3_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op4_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op4_state in ('pending','partial')  and  op4_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op1_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op1_state in ('pending','partial')  and  op1_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op6_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op6_state in ('pending','partial')  and  op6_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op7_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op7_state in ('pending','partial')  and  op7_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op8_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op8_state in ('pending','partial')  and  op8_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op9_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op9_state in ('pending','partial')  and  op9_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op10_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op10_state in ('pending','partial')  and  op10_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op11_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op11_state in ('pending','partial')  and  op11_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op12_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op12_state in ('pending','partial')  and  op12_sc_status = 'inhouse' and last_operation_check_id = %s


						limit 1
						""" 
						%(
						entry_rec.position_id.id,entry_rec.op5_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op5_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op5_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op5_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op5_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op5_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op5_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op5_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op5_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op5_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op5_id.id,
						entry_rec.position_id.id,entry_rec.id,
						))
					pending_operation_id = cr.fetchone()
					if pending_operation_id:
						if pending_operation_id[0] > 0:
							if entry_rec.op5_process_result != 'reject':
								raise osv.except_osv(_('Warning!'),
										_('This is last operation. Previous operations yet to be complete. !!'))
									
				### Cost Incurred Calculation ###
				cr.execute(""" select in_house_cost from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s limit 1 """ %(entry_rec.op5_id.id,entry_rec.op5_stage_id.id,entry_rec.position_id.id))
				inhouse_cost = cr.fetchone()
				cost_incurred = 0.00
				if inhouse_cost:
					
					if inhouse_cost[0] >= 0:
						cost_incurred = entry_rec.op5_total_time * inhouse_cost[0]
				
				self.write(cr,uid, ids,{'op5_cost_incurred':cost_incurred})
				if entry_rec.op5_process_result != 'rework':
					self.write(cr,uid, ids,{'op5_state': 'done','op5_button_status':'invisible'})
				### Operation Completion ###
				if last_operation_id:
					if pending_operation_id == None and last_operation_id[0] > 0:
						cr.execute(""" select id from kg_ms_operations

							where

							op1_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op1_state in ('pending','partial')  and  op1_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op2_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op2_state in ('pending','partial')  and  op2_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op4_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op4_state in ('pending','partial')  and  op4_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op3_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op3_state in ('pending','partial')  and  op3_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op6_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op6_state in ('pending','partial')  and  op6_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op7_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op7_state in ('pending','partial')  and  op7_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op8_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op8_state in ('pending','partial')  and  op8_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op9_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op9_state in ('pending','partial')  and  op9_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op10_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op10_state in ('pending','partial')  and  op10_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op11_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op11_state in ('pending','partial')  and  op11_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op12_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op12_state in ('pending','partial')  and  op12_sc_status = 'sc' and last_operation_check_id = %s


							limit 1
							""" 
							%(
							entry_rec.position_id.id,entry_rec.op5_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op5_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op5_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op5_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op5_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op5_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op5_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op5_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op5_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op5_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op5_id.id,
							entry_rec.position_id.id,entry_rec.id,
							))
						pending_operation = cr.fetchone()
						if pending_operation == None:
							if entry_rec.op5_process_result == 'accept':
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_completed_qty': entry_rec.ms_id.ms_completed_qty + entry_rec.inhouse_qty})
								ms_store_vals = {
									'operation_id': entry_rec.id,
									'production_id': entry_rec.production_id.id,
									'foundry_assembly_id': entry_rec.production_id.assembly_id,
									'foundry_assembly_line_id': entry_rec.production_id.assembly_line_id,
									'ms_assembly_id': entry_rec.ms_id.assembly_id,
									'ms_assembly_line_id': entry_rec.ms_id.assembly_line_id,
									'qty': entry_rec.inhouse_qty
								}
								ms_store_id = self.pool.get('kg.ms.stores').create(cr, uid, ms_store_vals)
							if (entry_rec.ms_id.ms_completed_qty + entry_rec.ms_id.ms_rejected_qty) == entry_rec.ms_id.ms_sch_qty:
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_state':'op_completed'})
				
				if entry_rec.op5_process_result == 'reject':
				
					
					### Department Indent Creation when process result is reject for ms item ###
					if entry_rec.ms_type == 'ms_item':
						
						## Operation 5 Status Updation ###
						if entry_rec.op5_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op5_state':'reject'})
						self.write(cr, uid, ids, {'state':'reject'})
						if entry_rec.ms_id.ms_id.line_ids:
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP2')])
							
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry_rec.entry_date))
							seq_name = cr.fetchone();

							dep_indent_obj = self.pool.get('kg.depindent')
							dep_indent_vals = {
								'name':'',
								'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
								'dep_name':1,
								'entry_mode':'auto',
								'state': 'approved',
								'indent_type': 'production',
								'name': seq_name[0],
								'order_id': entry_rec.order_id.id,
								'order_line_id': entry_rec.order_line_id.id,
								'src_location_id': location.main_location.id,
								'dest_location_id': location.stock_location.id
								}
								
							indent_id = dep_indent_obj.create(cr, uid, dep_indent_vals)
							for indent_item in entry_rec.ms_id.ms_id.line_ids:
								dep_indent_line_obj = self.pool.get('kg.depindent.line')
								product_rec = self.pool.get('product.product').browse(cr, uid, indent_item.product_id.id)
								dep_indent_line_vals = {
								'indent_id':indent_id,
								'product_id': indent_item.product_id.id,
								'uom': product_rec.uom_id.id,
								'qty': indent_item.qty * entry_rec.inhouse_qty,
								'pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								'issue_pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								#~ 'cutting_qty':ms_raw_rec.temp_qty,
								'ms_bot_id':entry_rec.ms_id.ms_id.id,
								'fns_item_name':entry_rec.item_name,
								'position_id': entry_rec.position_id.id
								}
								
								indent_line_id = dep_indent_line_obj.create(cr, uid, dep_indent_line_vals)
								
								indent_wo_line_obj = self.pool.get('ch.depindent.wo')
							
								indent_wo_line_vals = {
									'header_id':indent_line_id,
									'wo_id':entry_rec.order_no,
									'w_order_id':entry_rec.order_id.id,
									'w_order_line_id':entry_rec.order_line_id.id,
									'qty':indent_item.qty * entry_rec.inhouse_qty,
								}
								indent_wo_line_id = indent_wo_line_obj.create(cr, uid, indent_wo_line_vals)
						
						### New Entry Creation for same Operation ###
						op_vals = {
							'ms_id': entry_rec.ms_id.id,
							'ms_plan_id': entry_rec.ms_plan_id.id,
							'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
							'inhouse_qty': 1,
							'op5_stage_id': entry_rec.op5_stage_id.id,
							'op5_clamping_area': entry_rec.op5_clamping_area,
							'op5_id': entry_rec.op5_id.id,
							'parent_id' : ids[0],
							'last_operation_check_id': entry_rec.last_operation_check_id,
							'state': 'active',
							'op5_state': 'pending',
							'op5_process_result':'',
						
						}			
						copy_id = self.copy(cr, uid, entry_rec.id,op_vals, context)
						
						copy_rec = self.browse(cr, uid, copy_id)
						
						for dimen_item in copy_rec.op5_line_ids:
							
							dimen_vals = {
								'actual_val': 0,
								'remark': False,
							}
							
							dimension_obj = self.pool.get('ch.ms.dimension.details')
							dimension_obj.write(cr, uid, dimen_item.id, dimen_vals, context)
						
					if entry_rec.ms_type == 'foundry_item':
						
						ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_rejected_qty': entry_rec.ms_id.ms_rejected_qty + entry_rec.inhouse_qty})
						
						## Operation 5 Status Updation ###
						if entry_rec.op5_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op5_state':'reject'})
							
						self.write(cr, uid, ids, {'state':'reject'})
								
						#### NC Creation for reject Qty ###
						
						### Production Number ###
						produc_name = ''	
						produc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.production')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,produc_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(produc_seq_id[0],rec.code,entry_rec.entry_date))
						produc_name = cr.fetchone();
						
						### Issue Number ###
						issue_name = ''	
						issue_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pattern.issue')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,issue_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(issue_seq_id[0],rec.code,entry_rec.entry_date))
						issue_name = cr.fetchone();
						
						### Core Log Number ###
						core_name = ''	
						core_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,core_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_seq_id[0],rec.code,entry_rec.entry_date))
						core_name = cr.fetchone();
						
						### Mould Log Number ###
						mould_name = ''	
						mould_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,mould_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_seq_id[0],rec.code,entry_rec.entry_date))
						mould_name = cr.fetchone();
						
						production_vals = {
												
							'name': produc_name[0],
							'schedule_id': entry_rec.ms_id.schedule_id.id,
							'schedule_date': entry_rec.ms_id.schedule_date,
							'division_id': entry_rec.ms_id.division_id.id,
							'location' : entry_rec.ms_id.location,
							'schedule_line_id': entry_rec.ms_id.schedule_line_id.id,
							'order_id': entry_rec.ms_id.order_id.id,
							'order_line_id': entry_rec.ms_id.order_line_id.id,
							'order_bomline_id': entry_rec.ms_id.order_bomline_id.id,
							'qty' : entry_rec.inhouse_qty,			  
							'schedule_qty' : entry_rec.inhouse_qty,			  
							'state' : 'issue_done',
							'order_category':entry_rec.ms_id.order_category,
							'order_priority': '1',
							'pattern_id' : entry_rec.ms_id.pattern_id.id,
							'pattern_name' : entry_rec.ms_id.pattern_id.pattern_name,	
							'moc_id' : entry_rec.ms_id.moc_id.id,
							'request_state': 'done',
							'issue_no': issue_name[0],
							'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'issue_qty': 1,
							'issue_state': 'issued',
							'core_no': core_name[0],
							'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'core_qty': entry_rec.inhouse_qty,	
							'core_rem_qty': entry_rec.inhouse_qty,	
							'core_state': 'pending',
							'mould_no': mould_name[0],
							'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'mould_qty': entry_rec.inhouse_qty,	
							'mould_rem_qty': entry_rec.inhouse_qty,	
							'mould_state': 'pending',		
						}
						
						production_id = self.pool.get('kg.production').create(cr, uid, production_vals)
					
			else:
				if entry_rec.op5_button_status == 'visible':
					sc_obj = self.pool.get('kg.subcontract.process')
					
					self.write(cr, uid, ids, {'op5_sc_status': 'sc','op5_button_status': 'invisible'})	
					sc_name = ''	
					sc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.process')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,sc_seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(sc_seq_id[0],seq_rec.code))
					sc_name = cr.fetchone();
					
					wo_id = self.pool.get('kg.work.order').search(cr, uid, [('flag_for_stock','=','t')])
					if entry_rec.order_id.id == wo_id[0]:
						sc_actual_qty = 0
					else:
						sc_actual_qty = entry_rec.inhouse_qty
					
					sc_vals = {
						'name': sc_name[0],
						'ms_plan_id': entry_rec.ms_plan_id.id,
						'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
						'sc_qty': entry_rec.inhouse_qty,
						'total_qty': entry_rec.inhouse_qty,
						'pending_qty': entry_rec.inhouse_qty,
						'actual_qty': sc_actual_qty,
						'ms_op_id': entry_rec.id,
						'contractor_id': entry_rec.op5_contractor_id.id,
					}
					sc_id = sc_obj.create(cr, uid,sc_vals)
		else:
			pass
						
				
		return True
		
	### Operation 6 ###
		
	def onchange_operation6_sc(self, cr, uid, ids,op6_flag_sc, context=None):
		value = {'op6_sc_status': 'inhouse'}
		if op6_flag_sc == True:
			value = {'op6_sc_status': 'sc'}
		return {'value': value}
		
	def onchange_operation6_time(self, cr, uid, ids,op6_start_time,op6_end_time, context=None):
		value = {'op6_total_time': 0.00}
		total_time = 0.00
		total_time = op6_end_time - op6_start_time
		value = {'op6_total_time': total_time}
		return {'value': value}
		
	def onchange_operation6_cost_incurred(self, cr, uid, ids,op6_id,op6_stage_id,position_id,op6_total_time, context=None):
		value = {'op6_cost_incurred': 0.00}
		### Cost Incurred Calculation ###
		cr.execute(""" select in_house_cost from ch_kg_position_number 
			where operation_id = %s and stage_id = %s
			and header_id = %s limit 1 """ %(op6_id,op6_stage_id,position_id))
		inhouse_cost = cr.fetchone()
		cost_incurred = 0.00
		if inhouse_cost:
			
			if inhouse_cost[0] >= 0:
				cost_incurred = op6_total_time * inhouse_cost[0]
		value = {'op6_cost_incurred': cost_incurred}
		return {'value': value}
			
	def operation6_update(self, cr, uid, ids, context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		ms_obj = self.pool.get('kg.machineshop')
		
		if entry_rec.op6_state == 'pending':
			if entry_rec.op6_flag_sc != True:
			
				for dim_item in entry_rec.op6_line_ids:
					
					today = date.today()
					today = str(today)
					today = datetime.strptime(today, '%Y-%m-%d')
					start_date = entry_rec.op6_start_date
					start_date = str(start_date)
					start_date = datetime.strptime(start_date, '%Y-%m-%d')
					end_date = entry_rec.op6_end_date
					end_date = str(end_date)
					end_date = datetime.strptime(end_date, '%Y-%m-%d')
					if start_date > today or end_date > today:
						raise osv.except_osv(_('Warning!'),
								_('Start and End date should be less than or equal to current date!!'))
								
					if entry_rec.op6_start_time == entry_rec.op6_end_time:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not be equal !!'))
								
					if entry_rec.op6_start_time > 24 or entry_rec.op6_end_time > 24:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not exceed 24 hrs !!'))
					
					if dim_item.actual_val < 0:
						raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative. Check the actual value !!'))
					
					#~ if entry_rec.op6_process_result != 'reject':			
						#~ 
						#~ if dim_item.actual_val == 0:
							#~ raise osv.except_osv(_('Warning!'),
									#~ _('System not allow to save zero values. Check the actual value !!'))
									
						#### Min and Max Tolerance Checking ####
						
						if dim_item.pos_dimension_id != None:
						
							min_tol_value = (dim_item.min_val * dim_item.pos_dimension_id.min_tolerance) / 100
							max_tol_value = (dim_item.max_val * dim_item.pos_dimension_id.max_tolerance) / 100
									
							if dim_item.actual_val < (dim_item.min_val - min_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should greater or equal to Minimum value !!'))
										
							if dim_item.actual_val > (dim_item.max_val + max_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should lesser or equal to Maximum value !!'))
								
				### Last Operation Check ###
				cr.execute(""" select id from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s and is_last_operation = 't' """ %(entry_rec.op6_id.id,entry_rec.op6_stage_id.id,entry_rec.position_id.id))
				last_operation_id = cr.fetchone()
				
				pending_operation_id = []
				if last_operation_id:
					cr.execute(""" select id from kg_ms_operations

						where

						op2_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op2_state in ('pending','partial')  and  op2_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op3_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op3_state in ('pending','partial')  and  op3_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op4_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op4_state in ('pending','partial')  and  op4_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op5_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op5_state in ('pending','partial')  and  op5_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op1_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op1_state in ('pending','partial')  and  op1_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op7_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op7_state in ('pending','partial')  and  op7_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op8_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op8_state in ('pending','partial')  and  op8_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op9_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op9_state in ('pending','partial')  and  op9_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op10_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op10_state in ('pending','partial')  and  op10_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op11_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op11_state in ('pending','partial')  and  op11_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op12_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op12_state in ('pending','partial')  and  op12_sc_status = 'inhouse' and last_operation_check_id = %s


						limit 1
						""" 
						%(
						entry_rec.position_id.id,entry_rec.op6_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op6_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op6_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op6_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op6_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op6_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op6_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op6_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op6_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op6_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op6_id.id,
						entry_rec.position_id.id,entry_rec.id,
						))
					pending_operation_id = cr.fetchone()
					if pending_operation_id:
						if pending_operation_id[0] > 0:
							if entry_rec.op6_process_result != 'reject':
								raise osv.except_osv(_('Warning!'),
										_('This is last operation. Previous operations yet to be complete. !!'))
									
				### Cost Incurred Calculation ###
				cr.execute(""" select in_house_cost from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s limit 1 """ %(entry_rec.op6_id.id,entry_rec.op6_stage_id.id,entry_rec.position_id.id))
				inhouse_cost = cr.fetchone()
				cost_incurred = 0.00
				if inhouse_cost:
					
					if inhouse_cost[0] >= 0:
						cost_incurred = entry_rec.op6_total_time * inhouse_cost[0]
				
				self.write(cr,uid, ids,{'op6_cost_incurred':cost_incurred})
				if entry_rec.op6_process_result != 'rework':
					self.write(cr,uid, ids,{'op6_state': 'done','op6_button_status':'invisible'})
				### Operation Completion ###
				if last_operation_id:
					if pending_operation_id == None and last_operation_id[0] > 0:
						cr.execute(""" select id from kg_ms_operations

							where

							op1_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op1_state in ('pending','partial')  and  op1_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op2_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op2_state in ('pending','partial')  and  op2_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op4_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op4_state in ('pending','partial')  and  op4_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op3_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op3_state in ('pending','partial')  and  op3_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op5_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op5_state in ('pending','partial')  and  op5_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op7_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op7_state in ('pending','partial')  and  op7_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op8_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op8_state in ('pending','partial')  and  op8_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op9_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op9_state in ('pending','partial')  and  op9_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op10_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op10_state in ('pending','partial')  and  op10_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op11_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op11_state in ('pending','partial')  and  op11_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op12_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op12_state in ('pending','partial')  and  op12_sc_status = 'sc' and last_operation_check_id = %s


							limit 1
							""" 
							%(
							entry_rec.position_id.id,entry_rec.op6_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op6_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op6_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op6_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op6_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op6_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op6_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op6_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op6_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op6_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op6_id.id,
							entry_rec.position_id.id,entry_rec.id,
							))
						pending_operation = cr.fetchone()
						if pending_operation == None:
							if entry_rec.op6_process_result == 'accept':
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_completed_qty': entry_rec.ms_id.ms_completed_qty + entry_rec.inhouse_qty})
								ms_store_vals = {
									'operation_id': entry_rec.id,
									'production_id': entry_rec.production_id.id,
									'foundry_assembly_id': entry_rec.production_id.assembly_id,
									'foundry_assembly_line_id': entry_rec.production_id.assembly_line_id,
									'ms_assembly_id': entry_rec.ms_id.assembly_id,
									'ms_assembly_line_id': entry_rec.ms_id.assembly_line_id,
									'qty': entry_rec.inhouse_qty
								}
								ms_store_id = self.pool.get('kg.ms.stores').create(cr, uid, ms_store_vals)
							if (entry_rec.ms_id.ms_completed_qty + entry_rec.ms_id.ms_rejected_qty) == entry_rec.ms_id.ms_sch_qty:
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_state':'op_completed'})
				
				if entry_rec.op6_process_result == 'reject':
				
					
					### Department Indent Creation when process result is reject for ms item ###
					if entry_rec.ms_type == 'ms_item':
						
						## Operation 6 Status Updation ###
						if entry_rec.op6_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op6_state':'reject'})
						self.write(cr, uid, ids, {'state':'reject'})
						if entry_rec.ms_id.ms_id.line_ids:
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP2')])
							
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry_rec.entry_date))
							seq_name = cr.fetchone();

							dep_indent_obj = self.pool.get('kg.depindent')
							dep_indent_vals = {
								'name':'',
								'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
								'dep_name':1,
								'entry_mode':'auto',
								'state': 'approved',
								'indent_type': 'production',
								'name': seq_name[0],
								'order_id': entry_rec.order_id.id,
								'order_line_id': entry_rec.order_line_id.id,
								'src_location_id': location.main_location.id,
								'dest_location_id': location.stock_location.id
								}
								
							indent_id = dep_indent_obj.create(cr, uid, dep_indent_vals)
							for indent_item in entry_rec.ms_id.ms_id.line_ids:
								dep_indent_line_obj = self.pool.get('kg.depindent.line')
								product_rec = self.pool.get('product.product').browse(cr, uid, indent_item.product_id.id)
								dep_indent_line_vals = {
								'indent_id':indent_id,
								'product_id': indent_item.product_id.id,
								'uom': product_rec.uom_id.id,
								'qty': indent_item.qty * entry_rec.inhouse_qty,
								'pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								'issue_pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								#~ 'cutting_qty':ms_raw_rec.temp_qty,
								'ms_bot_id':entry_rec.ms_id.ms_id.id,
								'fns_item_name':entry_rec.item_name,
								'position_id': entry_rec.position_id.id
								}
								
								indent_line_id = dep_indent_line_obj.create(cr, uid, dep_indent_line_vals)
								
								indent_wo_line_obj = self.pool.get('ch.depindent.wo')
							
								indent_wo_line_vals = {
									'header_id':indent_line_id,
									'wo_id':entry_rec.order_no,
									'w_order_id':entry_rec.order_id.id,
									'w_order_line_id':entry_rec.order_line_id.id,
									'qty':indent_item.qty * entry_rec.inhouse_qty,
								}
								indent_wo_line_id = indent_wo_line_obj.create(cr, uid, indent_wo_line_vals)
						
						### New Entry Creation for same Operation ###
						op_vals = {
							'ms_id': entry_rec.ms_id.id,
							'ms_plan_id': entry_rec.ms_plan_id.id,
							'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
							'inhouse_qty': 1,
							'op6_stage_id': entry_rec.op6_stage_id.id,
							'op6_clamping_area': entry_rec.op6_clamping_area,
							'op6_id': entry_rec.op6_id.id,
							'parent_id' : ids[0],
							'last_operation_check_id': entry_rec.last_operation_check_id,
							'state': 'active',
							'op6_state': 'pending',
							'op6_process_result':'',
						
						}			
						copy_id = self.copy(cr, uid, entry_rec.id,op_vals, context)
						
						copy_rec = self.browse(cr, uid, copy_id)
						
						for dimen_item in copy_rec.op6_line_ids:
							
							dimen_vals = {
								'actual_val': 0,
								'remark': False,
							}
							
							dimension_obj = self.pool.get('ch.ms.dimension.details')
							dimension_obj.write(cr, uid, dimen_item.id, dimen_vals, context)
						
					if entry_rec.ms_type == 'foundry_item':
						
						ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_rejected_qty': entry_rec.ms_id.ms_rejected_qty + entry_rec.inhouse_qty})
						
						## Operation 5 Status Updation ###
						if entry_rec.op6_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op6_state':'reject'})
							
						self.write(cr, uid, ids, {'state':'reject'})
								
						#### NC Creation for reject Qty ###
						
						### Production Number ###
						produc_name = ''	
						produc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.production')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,produc_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(produc_seq_id[0],rec.code,entry_rec.entry_date))
						produc_name = cr.fetchone();
						
						### Issue Number ###
						issue_name = ''	
						issue_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pattern.issue')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,issue_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(issue_seq_id[0],rec.code,entry_rec.entry_date))
						issue_name = cr.fetchone();
						
						### Core Log Number ###
						core_name = ''	
						core_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,core_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_seq_id[0],rec.code,entry_rec.entry_date))
						core_name = cr.fetchone();
						
						### Mould Log Number ###
						mould_name = ''	
						mould_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,mould_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_seq_id[0],rec.code,entry_rec.entry_date))
						mould_name = cr.fetchone();
						
						production_vals = {
												
							'name': produc_name[0],
							'schedule_id': entry_rec.ms_id.schedule_id.id,
							'schedule_date': entry_rec.ms_id.schedule_date,
							'division_id': entry_rec.ms_id.division_id.id,
							'location' : entry_rec.ms_id.location,
							'schedule_line_id': entry_rec.ms_id.schedule_line_id.id,
							'order_id': entry_rec.ms_id.order_id.id,
							'order_line_id': entry_rec.ms_id.order_line_id.id,
							'order_bomline_id': entry_rec.ms_id.order_bomline_id.id,
							'qty' : entry_rec.inhouse_qty,			  
							'schedule_qty' : entry_rec.inhouse_qty,			  
							'state' : 'issue_done',
							'order_category':entry_rec.ms_id.order_category,
							'order_priority': '1',
							'pattern_id' : entry_rec.ms_id.pattern_id.id,
							'pattern_name' : entry_rec.ms_id.pattern_id.pattern_name,	
							'moc_id' : entry_rec.ms_id.moc_id.id,
							'request_state': 'done',
							'issue_no': issue_name[0],
							'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'issue_qty': 1,
							'issue_state': 'issued',
							'core_no': core_name[0],
							'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'core_qty': entry_rec.inhouse_qty,	
							'core_rem_qty': entry_rec.inhouse_qty,	
							'core_state': 'pending',
							'mould_no': mould_name[0],
							'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'mould_qty': entry_rec.inhouse_qty,	
							'mould_rem_qty': entry_rec.inhouse_qty,	
							'mould_state': 'pending',		
						}
						
						production_id = self.pool.get('kg.production').create(cr, uid, production_vals)
					
			else:
				if entry_rec.op6_button_status == 'visible':
					sc_obj = self.pool.get('kg.subcontract.process')
					
					self.write(cr, uid, ids, {'op6_sc_status': 'sc','op6_button_status': 'invisible'})	
					sc_name = ''	
					sc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.process')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,sc_seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(sc_seq_id[0],seq_rec.code))
					sc_name = cr.fetchone();
					
					wo_id = self.pool.get('kg.work.order').search(cr, uid, [('flag_for_stock','=','t')])
					if entry_rec.order_id.id == wo_id[0]:
						sc_actual_qty = 0
					else:
						sc_actual_qty = entry_rec.inhouse_qty
					
					sc_vals = {
						'name': sc_name[0],
						'ms_plan_id': entry_rec.ms_plan_id.id,
						'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
						'sc_qty': entry_rec.inhouse_qty,
						'total_qty': entry_rec.inhouse_qty,
						'pending_qty': entry_rec.inhouse_qty,
						'actual_qty': sc_actual_qty,
						'ms_op_id': entry_rec.id,
						'contractor_id': entry_rec.op6_contractor_id.id,
					}
					sc_id = sc_obj.create(cr, uid,sc_vals)
		else:
			pass
						
				
		return True
		
	### Operation 7 ###
		
	def onchange_operation7_sc(self, cr, uid, ids,op7_flag_sc, context=None):
		value = {'op7_sc_status': 'inhouse'}
		if op7_flag_sc == True:
			value = {'op7_sc_status': 'sc'}
		return {'value': value}
		
	def onchange_operation7_time(self, cr, uid, ids,op7_start_time,op7_end_time, context=None):
		value = {'op7_total_time': 0.00}
		total_time = 0.00
		total_time = op7_end_time - op7_start_time
		value = {'op7_total_time': total_time}
		return {'value': value}
		
	def onchange_operation7_cost_incurred(self, cr, uid, ids,op7_id,op7_stage_id,position_id,op7_total_time, context=None):
		value = {'op7_cost_incurred': 0.00}
		### Cost Incurred Calculation ###
		cr.execute(""" select in_house_cost from ch_kg_position_number 
			where operation_id = %s and stage_id = %s
			and header_id = %s limit 1 """ %(op7_id,op7_stage_id,position_id))
		inhouse_cost = cr.fetchone()
		cost_incurred = 0.00
		if inhouse_cost:
			
			if inhouse_cost[0] >= 0:
				cost_incurred = op7_total_time * inhouse_cost[0]
		value = {'op7_cost_incurred': cost_incurred}
		return {'value': value}
			
	def operation7_update(self, cr, uid, ids, context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		ms_obj = self.pool.get('kg.machineshop')
		
		if entry_rec.op7_state == 'pending':
			if entry_rec.op7_flag_sc != True:
			
				for dim_item in entry_rec.op7_line_ids:
					
					today = date.today()
					today = str(today)
					today = datetime.strptime(today, '%Y-%m-%d')
					start_date = entry_rec.op7_start_date
					start_date = str(start_date)
					start_date = datetime.strptime(start_date, '%Y-%m-%d')
					end_date = entry_rec.op7_end_date
					end_date = str(end_date)
					end_date = datetime.strptime(end_date, '%Y-%m-%d')
					if start_date > today or end_date > today:
						raise osv.except_osv(_('Warning!'),
								_('Start and End date should be less than or equal to current date!!'))
								
					if entry_rec.op7_start_time == entry_rec.op7_end_time:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not be equal !!'))
								
					if entry_rec.op7_start_time > 24 or entry_rec.op7_end_time > 24:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not exceed 24 hrs !!'))
					
					if dim_item.actual_val < 0:
						raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative. Check the actual value !!'))
					
					#~ if entry_rec.op7_process_result != 'reject':			
						#~ 
						#~ if dim_item.actual_val == 0:
							#~ raise osv.except_osv(_('Warning!'),
									#~ _('System not allow to save zero values. Check the actual value !!'))
									
						#### Min and Max Tolerance Checking ####
						
						if dim_item.pos_dimension_id != None:
						
							min_tol_value = (dim_item.min_val * dim_item.pos_dimension_id.min_tolerance) / 100
							max_tol_value = (dim_item.max_val * dim_item.pos_dimension_id.max_tolerance) / 100
									
							if dim_item.actual_val < (dim_item.min_val - min_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should greater or equal to Minimum value !!'))
										
							if dim_item.actual_val > (dim_item.max_val + max_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should lesser or equal to Maximum value !!'))
								
				### Last Operation Check ###
				cr.execute(""" select id from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s and is_last_operation = 't' """ %(entry_rec.op7_id.id,entry_rec.op7_stage_id.id,entry_rec.position_id.id))
				last_operation_id = cr.fetchone()
				
				pending_operation_id = []
				if last_operation_id:
					cr.execute(""" select id from kg_ms_operations

						where

						op2_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op2_state in ('pending','partial')  and  op2_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op3_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op3_state in ('pending','partial')  and  op3_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op4_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op4_state in ('pending','partial')  and  op4_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op5_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op5_state in ('pending','partial')  and  op5_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op6_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op6_state in ('pending','partial')  and  op6_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op1_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op1_state in ('pending','partial')  and  op1_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op8_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op8_state in ('pending','partial')  and  op8_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op9_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op9_state in ('pending','partial')  and  op9_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op10_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op10_state in ('pending','partial')  and  op10_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op11_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op11_state in ('pending','partial')  and  op11_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op12_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op12_state in ('pending','partial')  and  op12_sc_status = 'inhouse' and last_operation_check_id = %s


						limit 1
						""" 
						%(
						entry_rec.position_id.id,entry_rec.op7_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op7_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op7_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op7_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op7_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op7_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op7_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op7_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op7_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op7_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op7_id.id,
						entry_rec.position_id.id,entry_rec.id,
						))
					pending_operation_id = cr.fetchone()
					if pending_operation_id:
						if pending_operation_id[0] > 0:
							if entry_rec.op7_process_result != 'reject':
								raise osv.except_osv(_('Warning!'),
										_('This is last operation. Previous operations yet to be complete. !!'))
									
				### Cost Incurred Calculation ###
				cr.execute(""" select in_house_cost from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s limit 1 """ %(entry_rec.op7_id.id,entry_rec.op7_stage_id.id,entry_rec.position_id.id))
				inhouse_cost = cr.fetchone()
				cost_incurred = 0.00
				if inhouse_cost:
					
					if inhouse_cost[0] >= 0:
						cost_incurred = entry_rec.op7_total_time * inhouse_cost[0]
				
				self.write(cr,uid, ids,{'op7_cost_incurred':cost_incurred})
				if entry_rec.op7_process_result != 'rework':
					self.write(cr,uid, ids,{'op7_state': 'done','op7_button_status':'invisible'})
				### Operation Completion ###
				if last_operation_id:
					if pending_operation_id == None and last_operation_id[0] > 0:
						cr.execute(""" select id from kg_ms_operations

							where

							op1_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op1_state in ('pending','partial')  and  op1_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op2_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op2_state in ('pending','partial')  and  op2_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op4_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op4_state in ('pending','partial')  and  op4_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op3_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op3_state in ('pending','partial')  and  op3_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op5_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op5_state in ('pending','partial')  and  op5_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op6_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op6_state in ('pending','partial')  and  op6_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op8_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op8_state in ('pending','partial')  and  op8_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op9_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op9_state in ('pending','partial')  and  op9_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op10_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op10_state in ('pending','partial')  and  op10_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op11_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op11_state in ('pending','partial')  and  op11_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op12_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op12_state in ('pending','partial')  and  op12_sc_status = 'sc' and last_operation_check_id = %s


							limit 1
							""" 
							%(
							entry_rec.position_id.id,entry_rec.op7_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op7_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op7_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op7_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op7_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op7_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op7_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op7_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op7_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op7_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op7_id.id,
							entry_rec.position_id.id,entry_rec.id,
							))
						pending_operation = cr.fetchone()
						if pending_operation == None:
							if entry_rec.op7_process_result == 'accept':
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_completed_qty': entry_rec.ms_id.ms_completed_qty + entry_rec.inhouse_qty})
								ms_store_vals = {
									'operation_id': entry_rec.id,
									'production_id': entry_rec.production_id.id,
									'foundry_assembly_id': entry_rec.production_id.assembly_id,
									'foundry_assembly_line_id': entry_rec.production_id.assembly_line_id,
									'ms_assembly_id': entry_rec.ms_id.assembly_id,
									'ms_assembly_line_id': entry_rec.ms_id.assembly_line_id,
									'qty': entry_rec.inhouse_qty
								}
								ms_store_id = self.pool.get('kg.ms.stores').create(cr, uid, ms_store_vals)
							if (entry_rec.ms_id.ms_completed_qty + entry_rec.ms_id.ms_rejected_qty) == entry_rec.ms_id.ms_sch_qty:
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_state':'op_completed'})
				
				if entry_rec.op7_process_result == 'reject':
				
					
					### Department Indent Creation when process result is reject for ms item ###
					if entry_rec.ms_type == 'ms_item':
						
						## Operation 7 Status Updation ###
						if entry_rec.op7_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op7_state':'reject'})
						self.write(cr, uid, ids, {'state':'reject'})
						if entry_rec.ms_id.ms_id.line_ids:
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP2')])
							
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry_rec.entry_date))
							seq_name = cr.fetchone();

							dep_indent_obj = self.pool.get('kg.depindent')
							dep_indent_vals = {
								'name':'',
								'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
								'dep_name':1,
								'entry_mode':'auto',
								'state': 'approved',
								'indent_type': 'production',
								'name': seq_name[0],
								'order_id': entry_rec.order_id.id,
								'order_line_id': entry_rec.order_line_id.id,
								'src_location_id': location.main_location.id,
								'dest_location_id': location.stock_location.id
								}
								
							indent_id = dep_indent_obj.create(cr, uid, dep_indent_vals)
							for indent_item in entry_rec.ms_id.ms_id.line_ids:
								dep_indent_line_obj = self.pool.get('kg.depindent.line')
								product_rec = self.pool.get('product.product').browse(cr, uid, indent_item.product_id.id)
								dep_indent_line_vals = {
								'indent_id':indent_id,
								'product_id': indent_item.product_id.id,
								'uom': product_rec.uom_id.id,
								'qty': indent_item.qty * entry_rec.inhouse_qty,
								'pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								'issue_pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								#~ 'cutting_qty':ms_raw_rec.temp_qty,
								'ms_bot_id':entry_rec.ms_id.ms_id.id,
								'fns_item_name':entry_rec.item_name,
								'position_id': entry_rec.position_id.id
								}
								
								indent_line_id = dep_indent_line_obj.create(cr, uid, dep_indent_line_vals)
								
								indent_wo_line_obj = self.pool.get('ch.depindent.wo')
							
								indent_wo_line_vals = {
									'header_id':indent_line_id,
									'wo_id':entry_rec.order_no,
									'w_order_id':entry_rec.order_id.id,
									'w_order_line_id':entry_rec.order_line_id.id,
									'qty':indent_item.qty * entry_rec.inhouse_qty,
								}
								indent_wo_line_id = indent_wo_line_obj.create(cr, uid, indent_wo_line_vals)
						
						### New Entry Creation for same Operation ###
						op_vals = {
							'ms_id': entry_rec.ms_id.id,
							'ms_plan_id': entry_rec.ms_plan_id.id,
							'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
							'inhouse_qty': 1,
							'op7_stage_id': entry_rec.op7_stage_id.id,
							'op7_clamping_area': entry_rec.op7_clamping_area,
							'op7_id': entry_rec.op7_id.id,
							'parent_id' : ids[0],
							'last_operation_check_id': entry_rec.last_operation_check_id,
							'state': 'active',
							'op7_state': 'pending',
							'op7_process_result':'',
						
						}			
						copy_id = self.copy(cr, uid, entry_rec.id,op_vals, context)
						
						copy_rec = self.browse(cr, uid, copy_id)
						
						for dimen_item in copy_rec.op7_line_ids:
							
							dimen_vals = {
								'actual_val': 0,
								'remark': False,
							}
							
							dimension_obj = self.pool.get('ch.ms.dimension.details')
							dimension_obj.write(cr, uid, dimen_item.id, dimen_vals, context)
						
					if entry_rec.ms_type == 'foundry_item':
						
						ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_rejected_qty': entry_rec.ms_id.ms_rejected_qty + entry_rec.inhouse_qty})
						
						## Operation 7 Status Updation ###
						if entry_rec.op7_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op7_state':'reject'})
							
						self.write(cr, uid, ids, {'state':'reject'})
								
						#### NC Creation for reject Qty ###
						
						### Production Number ###
						produc_name = ''	
						produc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.production')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,produc_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(produc_seq_id[0],rec.code,entry_rec.entry_date))
						produc_name = cr.fetchone();
						
						### Issue Number ###
						issue_name = ''	
						issue_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pattern.issue')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,issue_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(issue_seq_id[0],rec.code,entry_rec.entry_date))
						issue_name = cr.fetchone();
						
						### Core Log Number ###
						core_name = ''	
						core_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,core_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_seq_id[0],rec.code,entry_rec.entry_date))
						core_name = cr.fetchone();
						
						### Mould Log Number ###
						mould_name = ''	
						mould_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,mould_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_seq_id[0],rec.code,entry_rec.entry_date))
						mould_name = cr.fetchone();
						
						production_vals = {
												
							'name': produc_name[0],
							'schedule_id': entry_rec.ms_id.schedule_id.id,
							'schedule_date': entry_rec.ms_id.schedule_date,
							'division_id': entry_rec.ms_id.division_id.id,
							'location' : entry_rec.ms_id.location,
							'schedule_line_id': entry_rec.ms_id.schedule_line_id.id,
							'order_id': entry_rec.ms_id.order_id.id,
							'order_line_id': entry_rec.ms_id.order_line_id.id,
							'order_bomline_id': entry_rec.ms_id.order_bomline_id.id,
							'qty' : entry_rec.inhouse_qty,			  
							'schedule_qty' : entry_rec.inhouse_qty,			  
							'state' : 'issue_done',
							'order_category':entry_rec.ms_id.order_category,
							'order_priority': '1',
							'pattern_id' : entry_rec.ms_id.pattern_id.id,
							'pattern_name' : entry_rec.ms_id.pattern_id.pattern_name,	
							'moc_id' : entry_rec.ms_id.moc_id.id,
							'request_state': 'done',
							'issue_no': issue_name[0],
							'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'issue_qty': 1,
							'issue_state': 'issued',
							'core_no': core_name[0],
							'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'core_qty': entry_rec.inhouse_qty,	
							'core_rem_qty': entry_rec.inhouse_qty,	
							'core_state': 'pending',
							'mould_no': mould_name[0],
							'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'mould_qty': entry_rec.inhouse_qty,	
							'mould_rem_qty': entry_rec.inhouse_qty,	
							'mould_state': 'pending',		
						}
						
						production_id = self.pool.get('kg.production').create(cr, uid, production_vals)
					
			else:
				if entry_rec.op7_button_status == 'visible':
					sc_obj = self.pool.get('kg.subcontract.process')
					
					self.write(cr, uid, ids, {'op7_sc_status': 'sc','op7_button_status': 'invisible'})	
					sc_name = ''	
					sc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.process')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,sc_seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(sc_seq_id[0],seq_rec.code))
					sc_name = cr.fetchone();
					
					wo_id = self.pool.get('kg.work.order').search(cr, uid, [('flag_for_stock','=','t')])
					if entry_rec.order_id.id == wo_id[0]:
						sc_actual_qty = 0
					else:
						sc_actual_qty = entry_rec.inhouse_qty
					
					sc_vals = {
						'name': sc_name[0],
						'ms_plan_id': entry_rec.ms_plan_id.id,
						'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
						'sc_qty': entry_rec.inhouse_qty,
						'total_qty': entry_rec.inhouse_qty,
						'pending_qty': entry_rec.inhouse_qty,
						'actual_qty': sc_actual_qty,
						'ms_op_id': entry_rec.id,
						'contractor_id': entry_rec.op7_contractor_id.id,
					}
					sc_id = sc_obj.create(cr, uid,sc_vals)
		else:
			pass
						
				
		return True
		
	### Operation 8 ###
		
	def onchange_operation8_sc(self, cr, uid, ids,op8_flag_sc, context=None):
		value = {'op8_sc_status': 'inhouse'}
		if op8_flag_sc == True:
			value = {'op8_sc_status': 'sc'}
		return {'value': value}
		
	def onchange_operation8_time(self, cr, uid, ids,op8_start_time,op8_end_time, context=None):
		value = {'op8_total_time': 0.00}
		total_time = 0.00
		total_time = op8_end_time - op8_start_time
		value = {'op8_total_time': total_time}
		return {'value': value}
		
	def onchange_operation8_cost_incurred(self, cr, uid, ids,op8_id,op8_stage_id,position_id,op8_total_time, context=None):
		value = {'op8_cost_incurred': 0.00}
		### Cost Incurred Calculation ###
		cr.execute(""" select in_house_cost from ch_kg_position_number 
			where operation_id = %s and stage_id = %s
			and header_id = %s limit 1 """ %(op8_id,op8_stage_id,position_id))
		inhouse_cost = cr.fetchone()
		cost_incurred = 0.00
		if inhouse_cost:
			
			if inhouse_cost[0] >= 0:
				cost_incurred = op8_total_time * inhouse_cost[0]
		value = {'op8_cost_incurred': cost_incurred}
		return {'value': value}
			
	def operation8_update(self, cr, uid, ids, context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		ms_obj = self.pool.get('kg.machineshop')
		
		if entry_rec.op8_state == 'pending':
			if entry_rec.op8_flag_sc != True:
			
				for dim_item in entry_rec.op8_line_ids:
					
					today = date.today()
					today = str(today)
					today = datetime.strptime(today, '%Y-%m-%d')
					start_date = entry_rec.op8_start_date
					start_date = str(start_date)
					start_date = datetime.strptime(start_date, '%Y-%m-%d')
					end_date = entry_rec.op8_end_date
					end_date = str(end_date)
					end_date = datetime.strptime(end_date, '%Y-%m-%d')
					if start_date > today or end_date > today:
						raise osv.except_osv(_('Warning!'),
								_('Start and End date should be less than or equal to current date!!'))
								
					if entry_rec.op8_start_time == entry_rec.op8_end_time:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not be equal !!'))
								
					if entry_rec.op8_start_time > 24 or entry_rec.op8_end_time > 24:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not exceed 24 hrs !!'))
					
					if dim_item.actual_val < 0:
						raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative. Check the actual value !!'))
					
					#~ if entry_rec.op8_process_result != 'reject':			
						#~ 
						#~ if dim_item.actual_val == 0:
							#~ raise osv.except_osv(_('Warning!'),
									#~ _('System not allow to save zero values. Check the actual value !!'))
									
						#### Min and Max Tolerance Checking ####
						
						if dim_item.pos_dimension_id != None:
						
							min_tol_value = (dim_item.min_val * dim_item.pos_dimension_id.min_tolerance) / 100
							max_tol_value = (dim_item.max_val * dim_item.pos_dimension_id.max_tolerance) / 100
									
							if dim_item.actual_val < (dim_item.min_val - min_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should greater or equal to Minimum value !!'))
										
							if dim_item.actual_val > (dim_item.max_val + max_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should lesser or equal to Maximum value !!'))
								
				### Last Operation Check ###
				cr.execute(""" select id from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s and is_last_operation = 't' """ %(entry_rec.op8_id.id,entry_rec.op8_stage_id.id,entry_rec.position_id.id))
				last_operation_id = cr.fetchone()
				
				pending_operation_id = []
				if last_operation_id:
					cr.execute(""" select id from kg_ms_operations

						where

						op2_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op2_state in ('pending','partial')  and  op2_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op3_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op3_state in ('pending','partial')  and  op3_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op4_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op4_state in ('pending','partial')  and  op4_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op5_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op5_state in ('pending','partial')  and  op5_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op6_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op6_state in ('pending','partial')  and  op6_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op7_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op7_state in ('pending','partial')  and  op7_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op1_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op1_state in ('pending','partial')  and  op1_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op9_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op9_state in ('pending','partial')  and  op9_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op10_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op10_state in ('pending','partial')  and  op10_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op11_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op11_state in ('pending','partial')  and  op11_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op12_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op12_state in ('pending','partial')  and  op12_sc_status = 'inhouse' and last_operation_check_id = %s


						limit 1
						""" 
						%(
						entry_rec.position_id.id,entry_rec.op8_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op8_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op8_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op8_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op8_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op8_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op8_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op8_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op8_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op8_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op8_id.id,
						entry_rec.position_id.id,entry_rec.id,
						))
					pending_operation_id = cr.fetchone()
					if pending_operation_id:
						if pending_operation_id[0] > 0:
							if entry_rec.op8_process_result != 'reject':
								raise osv.except_osv(_('Warning!'),
										_('This is last operation. Previous operations yet to be complete. !!'))
									
				### Cost Incurred Calculation ###
				cr.execute(""" select in_house_cost from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s limit 1 """ %(entry_rec.op8_id.id,entry_rec.op8_stage_id.id,entry_rec.position_id.id))
				inhouse_cost = cr.fetchone()
				cost_incurred = 0.00
				if inhouse_cost:
					
					if inhouse_cost[0] >= 0:
						cost_incurred = entry_rec.op8_total_time * inhouse_cost[0]
				
				self.write(cr,uid, ids,{'op8_cost_incurred':cost_incurred})
				if entry_rec.op8_process_result != 'rework':
					self.write(cr,uid, ids,{'op8_state': 'done','op8_button_status':'invisible'})
				### Operation Completion ###
				if last_operation_id:
					if pending_operation_id == None and last_operation_id[0] > 0:
						cr.execute(""" select id from kg_ms_operations

							where

							op1_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op1_state in ('pending','partial')  and  op1_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op2_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op2_state in ('pending','partial')  and  op2_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op4_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op4_state in ('pending','partial')  and  op4_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op3_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op3_state in ('pending','partial')  and  op3_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op5_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op5_state in ('pending','partial')  and  op5_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op6_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op6_state in ('pending','partial')  and  op6_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op7_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op7_state in ('pending','partial')  and  op7_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op9_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op9_state in ('pending','partial')  and  op9_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op10_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op10_state in ('pending','partial')  and  op10_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op11_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op11_state in ('pending','partial')  and  op11_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op12_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op12_state in ('pending','partial')  and  op12_sc_status = 'sc' and last_operation_check_id = %s


							limit 1
							""" 
							%(
							entry_rec.position_id.id,entry_rec.op8_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op8_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op8_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op8_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op8_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op8_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op8_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op8_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op8_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op8_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op8_id.id,
							entry_rec.position_id.id,entry_rec.id,
							))
						pending_operation = cr.fetchone()
						if pending_operation == None:
							if entry_rec.op8_process_result == 'accept':
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_completed_qty': entry_rec.ms_id.ms_completed_qty + entry_rec.inhouse_qty})
								ms_store_vals = {
									'operation_id': entry_rec.id,
									'production_id': entry_rec.production_id.id,
									'foundry_assembly_id': entry_rec.production_id.assembly_id,
									'foundry_assembly_line_id': entry_rec.production_id.assembly_line_id,
									'ms_assembly_id': entry_rec.ms_id.assembly_id,
									'ms_assembly_line_id': entry_rec.ms_id.assembly_line_id,
									'qty': entry_rec.inhouse_qty
								}
								ms_store_id = self.pool.get('kg.ms.stores').create(cr, uid, ms_store_vals)
							if (entry_rec.ms_id.ms_completed_qty + entry_rec.ms_id.ms_rejected_qty) == entry_rec.ms_id.ms_sch_qty:
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_state':'op_completed'})
				
				if entry_rec.op8_process_result == 'reject':
				
					
					### Department Indent Creation when process result is reject for ms item ###
					if entry_rec.ms_type == 'ms_item':
						
						## Operation 8 Status Updation ###
						if entry_rec.op8_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op8_state':'reject'})
						self.write(cr, uid, ids, {'state':'reject'})
						if entry_rec.ms_id.ms_id.line_ids:
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP2')])
							
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry_rec.entry_date))
							seq_name = cr.fetchone();

							dep_indent_obj = self.pool.get('kg.depindent')
							dep_indent_vals = {
								'name':'',
								'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
								'dep_name':1,
								'entry_mode':'auto',
								'state': 'approved',
								'indent_type': 'production',
								'name': seq_name[0],
								'order_id': entry_rec.order_id.id,
								'order_line_id': entry_rec.order_line_id.id,
								'src_location_id': location.main_location.id,
								'dest_location_id': location.stock_location.id
								}
								
							indent_id = dep_indent_obj.create(cr, uid, dep_indent_vals)
							for indent_item in entry_rec.ms_id.ms_id.line_ids:
								dep_indent_line_obj = self.pool.get('kg.depindent.line')
								product_rec = self.pool.get('product.product').browse(cr, uid, indent_item.product_id.id)
								dep_indent_line_vals = {
								'indent_id':indent_id,
								'product_id': indent_item.product_id.id,
								'uom': product_rec.uom_id.id,
								'qty': indent_item.qty * entry_rec.inhouse_qty,
								'pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								'issue_pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								#~ 'cutting_qty':ms_raw_rec.temp_qty,
								'ms_bot_id':entry_rec.ms_id.ms_id.id,
								'fns_item_name':entry_rec.item_name,
								'position_id': entry_rec.position_id.id
								}
								
								indent_line_id = dep_indent_line_obj.create(cr, uid, dep_indent_line_vals)
								
								indent_wo_line_obj = self.pool.get('ch.depindent.wo')
							
								indent_wo_line_vals = {
									'header_id':indent_line_id,
									'wo_id':entry_rec.order_no,
									'w_order_id':entry_rec.order_id.id,
									'w_order_line_id':entry_rec.order_line_id.id,
									'qty':indent_item.qty * entry_rec.inhouse_qty,
								}
								indent_wo_line_id = indent_wo_line_obj.create(cr, uid, indent_wo_line_vals)
						
						### New Entry Creation for same Operation ###
						op_vals = {
							'ms_id': entry_rec.ms_id.id,
							'ms_plan_id': entry_rec.ms_plan_id.id,
							'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
							'inhouse_qty': 1,
							'op8_stage_id': entry_rec.op8_stage_id.id,
							'op8_clamping_area': entry_rec.op8_clamping_area,
							'op8_id': entry_rec.op8_id.id,
							'parent_id' : ids[0],
							'last_operation_check_id': entry_rec.last_operation_check_id,
							'state': 'active',
							'op8_state': 'pending',
							'op8_process_result':'',
							
						}			
						copy_id = self.copy(cr, uid, entry_rec.id,op_vals, context)
						
						copy_rec = self.browse(cr, uid, copy_id)
						
						for dimen_item in copy_rec.op8_line_ids:
							
							dimen_vals = {
								'actual_val': 0,
								'remark': False,
							}
							
							dimension_obj = self.pool.get('ch.ms.dimension.details')
							dimension_obj.write(cr, uid, dimen_item.id, dimen_vals, context)
						
					if entry_rec.ms_type == 'foundry_item':
						
						ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_rejected_qty': entry_rec.ms_id.ms_rejected_qty + entry_rec.inhouse_qty})
						
						## Operation 8 Status Updation ###
						if entry_rec.op8_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op8_state':'reject'})
							
						self.write(cr, uid, ids, {'state':'reject'})
								
						#### NC Creation for reject Qty ###
						
						### Production Number ###
						produc_name = ''	
						produc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.production')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,produc_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(produc_seq_id[0],rec.code,entry_rec.entry_date))
						produc_name = cr.fetchone();
						
						### Issue Number ###
						issue_name = ''	
						issue_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pattern.issue')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,issue_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(issue_seq_id[0],rec.code,entry_rec.entry_date))
						issue_name = cr.fetchone();
						
						### Core Log Number ###
						core_name = ''	
						core_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,core_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_seq_id[0],rec.code,entry_rec.entry_date))
						core_name = cr.fetchone();
						
						### Mould Log Number ###
						mould_name = ''	
						mould_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,mould_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_seq_id[0],rec.code,entry_rec.entry_date))
						mould_name = cr.fetchone();
						
						production_vals = {
												
							'name': produc_name[0],
							'schedule_id': entry_rec.ms_id.schedule_id.id,
							'schedule_date': entry_rec.ms_id.schedule_date,
							'division_id': entry_rec.ms_id.division_id.id,
							'location' : entry_rec.ms_id.location,
							'schedule_line_id': entry_rec.ms_id.schedule_line_id.id,
							'order_id': entry_rec.ms_id.order_id.id,
							'order_line_id': entry_rec.ms_id.order_line_id.id,
							'order_bomline_id': entry_rec.ms_id.order_bomline_id.id,
							'qty' : entry_rec.inhouse_qty,			  
							'schedule_qty' : entry_rec.inhouse_qty,			  
							'state' : 'issue_done',
							'order_category':entry_rec.ms_id.order_category,
							'order_priority': '1',
							'pattern_id' : entry_rec.ms_id.pattern_id.id,
							'pattern_name' : entry_rec.ms_id.pattern_id.pattern_name,	
							'moc_id' : entry_rec.ms_id.moc_id.id,
							'request_state': 'done',
							'issue_no': issue_name[0],
							'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'issue_qty': 1,
							'issue_state': 'issued',
							'core_no': core_name[0],
							'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'core_qty': entry_rec.inhouse_qty,	
							'core_rem_qty': entry_rec.inhouse_qty,	
							'core_state': 'pending',
							'mould_no': mould_name[0],
							'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'mould_qty': entry_rec.inhouse_qty,	
							'mould_rem_qty': entry_rec.inhouse_qty,	
							'mould_state': 'pending',		
						}
						
						production_id = self.pool.get('kg.production').create(cr, uid, production_vals)
					
			else:
				if entry_rec.op8_button_status == 'visible':
					sc_obj = self.pool.get('kg.subcontract.process')
					
					self.write(cr, uid, ids, {'op8_sc_status': 'sc','op8_button_status': 'invisible'})	
					sc_name = ''	
					sc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.process')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,sc_seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(sc_seq_id[0],seq_rec.code))
					sc_name = cr.fetchone();
					
					wo_id = self.pool.get('kg.work.order').search(cr, uid, [('flag_for_stock','=','t')])
					if entry_rec.order_id.id == wo_id[0]:
						sc_actual_qty = 0
					else:
						sc_actual_qty = entry_rec.inhouse_qty
					
					sc_vals = {
						'name': sc_name[0],
						'ms_plan_id': entry_rec.ms_plan_id.id,
						'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
						'sc_qty': entry_rec.inhouse_qty,
						'total_qty': entry_rec.inhouse_qty,
						'pending_qty': entry_rec.inhouse_qty,
						'actual_qty': sc_actual_qty,
						'ms_op_id': entry_rec.id,
						'contractor_id': entry_rec.op8_contractor_id.id,
					}
					sc_id = sc_obj.create(cr, uid,sc_vals)
		else:
			pass
						
				
		return True
		
	### Operation 9 ###
		
	def onchange_operation9_sc(self, cr, uid, ids,op9_flag_sc, context=None):
		value = {'op9_sc_status': 'inhouse'}
		if op9_flag_sc == True:
			value = {'op9_sc_status': 'sc'}
		return {'value': value}
		
	def onchange_operation9_time(self, cr, uid, ids,op9_start_time,op9_end_time, context=None):
		value = {'op9_total_time': 0.00}
		total_time = 0.00
		total_time = op9_end_time - op9_start_time
		value = {'op9_total_time': total_time}
		return {'value': value}
		
	def onchange_operation9_cost_incurred(self, cr, uid, ids,op9_id,op9_stage_id,position_id,op9_total_time, context=None):
		value = {'op9_cost_incurred': 0.00}
		### Cost Incurred Calculation ###
		cr.execute(""" select in_house_cost from ch_kg_position_number 
			where operation_id = %s and stage_id = %s
			and header_id = %s limit 1 """ %(op9_id,op9_stage_id,position_id))
		inhouse_cost = cr.fetchone()
		cost_incurred = 0.00
		if inhouse_cost:
			
			if inhouse_cost[0] >= 0:
				cost_incurred = op9_total_time * inhouse_cost[0]
		value = {'op9_cost_incurred': cost_incurred}
		return {'value': value}
			
	def operation9_update(self, cr, uid, ids, context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		ms_obj = self.pool.get('kg.machineshop')
		
		if entry_rec.op9_state == 'pending':
			if entry_rec.op9_flag_sc != True:
			
				for dim_item in entry_rec.op9_line_ids:
					
					today = date.today()
					today = str(today)
					today = datetime.strptime(today, '%Y-%m-%d')
					start_date = entry_rec.op9_start_date
					start_date = str(start_date)
					start_date = datetime.strptime(start_date, '%Y-%m-%d')
					end_date = entry_rec.op9_end_date
					end_date = str(end_date)
					end_date = datetime.strptime(end_date, '%Y-%m-%d')
					if start_date > today or end_date > today:
						raise osv.except_osv(_('Warning!'),
								_('Start and End date should be less than or equal to current date!!'))
								
					if entry_rec.op9_start_time == entry_rec.op9_end_time:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not be equal !!'))
								
					if entry_rec.op9_start_time > 24 or entry_rec.op9_end_time > 24:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not exceed 24 hrs !!'))
					
					if dim_item.actual_val < 0:
						raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative. Check the actual value !!'))
					
					#~ if entry_rec.op9_process_result != 'reject':			
						#~ 
						#~ if dim_item.actual_val == 0:
							#~ raise osv.except_osv(_('Warning!'),
									#~ _('System not allow to save zero values. Check the actual value !!'))
									
						#### Min and Max Tolerance Checking ####
						
						if dim_item.pos_dimension_id != None:
						
							min_tol_value = (dim_item.min_val * dim_item.pos_dimension_id.min_tolerance) / 100
							max_tol_value = (dim_item.max_val * dim_item.pos_dimension_id.max_tolerance) / 100
									
							if dim_item.actual_val < (dim_item.min_val - min_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should greater or equal to Minimum value !!'))
										
							if dim_item.actual_val > (dim_item.max_val + max_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should lesser or equal to Maximum value !!'))
								
				### Last Operation Check ###
				cr.execute(""" select id from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s and is_last_operation = 't' """ %(entry_rec.op9_id.id,entry_rec.op9_stage_id.id,entry_rec.position_id.id))
				last_operation_id = cr.fetchone()
				
				pending_operation_id = []
				if last_operation_id:
					cr.execute(""" select id from kg_ms_operations

						where

						op2_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op2_state in ('pending','partial')  and  op2_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op3_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op3_state in ('pending','partial')  and  op3_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op4_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op4_state in ('pending','partial')  and  op4_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op5_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op5_state in ('pending','partial')  and  op5_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op6_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op6_state in ('pending','partial')  and  op6_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op7_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op7_state in ('pending','partial')  and  op7_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op8_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op8_state in ('pending','partial')  and  op8_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op1_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op1_state in ('pending','partial')  and  op1_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op10_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op10_state in ('pending','partial')  and  op10_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op11_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op11_state in ('pending','partial')  and  op11_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op12_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op12_state in ('pending','partial')  and  op12_sc_status = 'inhouse' and last_operation_check_id = %s


						limit 1
						""" 
						%(
						entry_rec.position_id.id,entry_rec.op9_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op9_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op9_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op9_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op9_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op9_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op9_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op9_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op9_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op9_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op9_id.id,
						entry_rec.position_id.id,entry_rec.id,
						))
					pending_operation_id = cr.fetchone()
					if pending_operation_id:
						if pending_operation_id[0] > 0:
							if entry_rec.op9_process_result != 'reject':
								raise osv.except_osv(_('Warning!'),
										_('This is last operation. Previous operations yet to be complete. !!'))
									
				### Cost Incurred Calculation ###
				cr.execute(""" select in_house_cost from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s limit 1 """ %(entry_rec.op9_id.id,entry_rec.op9_stage_id.id,entry_rec.position_id.id))
				inhouse_cost = cr.fetchone()
				cost_incurred = 0.00
				if inhouse_cost:
					
					if inhouse_cost[0] >= 0:
						cost_incurred = entry_rec.op9_total_time * inhouse_cost[0]
				
				self.write(cr,uid, ids,{'op9_cost_incurred':cost_incurred})
				if entry_rec.op9_process_result != 'rework':
					self.write(cr,uid, ids,{'op9_state': 'done','op9_button_status':'invisible'})
				### Operation Completion ###
				if last_operation_id:
					if pending_operation_id == None and last_operation_id[0] > 0:
						cr.execute(""" select id from kg_ms_operations

							where

							op1_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op1_state in ('pending','partial')  and  op1_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op2_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op2_state in ('pending','partial')  and  op2_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op4_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op4_state in ('pending','partial')  and  op4_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op3_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op3_state in ('pending','partial')  and  op3_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op5_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op5_state in ('pending','partial')  and  op5_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op6_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op6_state in ('pending','partial')  and  op6_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op7_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op7_state in ('pending','partial')  and  op7_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op8_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op8_state in ('pending','partial')  and  op8_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op10_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op10_state in ('pending','partial')  and  op10_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op11_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op11_state in ('pending','partial')  and  op11_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op12_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op12_state in ('pending','partial')  and  op12_sc_status = 'sc' and last_operation_check_id = %s


							limit 1
							""" 
							%(
							entry_rec.position_id.id,entry_rec.op9_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op9_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op9_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op9_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op9_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op9_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op9_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op9_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op9_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op9_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op9_id.id,
							entry_rec.position_id.id,entry_rec.id,
							))
						pending_operation = cr.fetchone()
						if pending_operation == None:
							if entry_rec.op9_process_result == 'accept':
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_completed_qty': entry_rec.ms_id.ms_completed_qty + entry_rec.inhouse_qty})
								ms_store_vals = {
									'operation_id': entry_rec.id,
									'production_id': entry_rec.production_id.id,
									'foundry_assembly_id': entry_rec.production_id.assembly_id,
									'foundry_assembly_line_id': entry_rec.production_id.assembly_line_id,
									'ms_assembly_id': entry_rec.ms_id.assembly_id,
									'ms_assembly_line_id': entry_rec.ms_id.assembly_line_id,
									'qty': entry_rec.inhouse_qty
								}
								ms_store_id = self.pool.get('kg.ms.stores').create(cr, uid, ms_store_vals)
							if (entry_rec.ms_id.ms_completed_qty + entry_rec.ms_id.ms_rejected_qty) == entry_rec.ms_id.ms_sch_qty:
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_state':'op_completed'})
				
				if entry_rec.op9_process_result == 'reject':
				
					
					### Department Indent Creation when process result is reject for ms item ###
					if entry_rec.ms_type == 'ms_item':
						
						## Operation 8 Status Updation ###
						if entry_rec.op9_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op9_state':'reject'})
						self.write(cr, uid, ids, {'state':'reject'})
						if entry_rec.ms_id.ms_id.line_ids:
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP2')])
							
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry_rec.entry_date))
							seq_name = cr.fetchone();

							dep_indent_obj = self.pool.get('kg.depindent')
							dep_indent_vals = {
								'name':'',
								'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
								'dep_name':1,
								'entry_mode':'auto',
								'state': 'approved',
								'indent_type': 'production',
								'name': seq_name[0],
								'order_id': entry_rec.order_id.id,
								'order_line_id': entry_rec.order_line_id.id,
								'src_location_id': location.main_location.id,
								'dest_location_id': location.stock_location.id
								}
								
							indent_id = dep_indent_obj.create(cr, uid, dep_indent_vals)
							for indent_item in entry_rec.ms_id.ms_id.line_ids:
								dep_indent_line_obj = self.pool.get('kg.depindent.line')
								product_rec = self.pool.get('product.product').browse(cr, uid, indent_item.product_id.id)
								dep_indent_line_vals = {
								'indent_id':indent_id,
								'product_id': indent_item.product_id.id,
								'uom': product_rec.uom_id.id,
								'qty': indent_item.qty * entry_rec.inhouse_qty,
								'pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								'issue_pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								#~ 'cutting_qty':ms_raw_rec.temp_qty,
								'ms_bot_id':entry_rec.ms_id.ms_id.id,
								'fns_item_name':entry_rec.item_name,
								'position_id': entry_rec.position_id.id
								}
								
								indent_line_id = dep_indent_line_obj.create(cr, uid, dep_indent_line_vals)
								
								indent_wo_line_obj = self.pool.get('ch.depindent.wo')
							
								indent_wo_line_vals = {
									'header_id':indent_line_id,
									'wo_id':entry_rec.order_no,
									'w_order_id':entry_rec.order_id.id,
									'w_order_line_id':entry_rec.order_line_id.id,
									'qty':indent_item.qty * entry_rec.inhouse_qty,
								}
								indent_wo_line_id = indent_wo_line_obj.create(cr, uid, indent_wo_line_vals)
						
						### New Entry Creation for same Operation ###
						op_vals = {
							'ms_id': entry_rec.ms_id.id,
							'ms_plan_id': entry_rec.ms_plan_id.id,
							'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
							'inhouse_qty': 1,
							'op9_stage_id': entry_rec.op9_stage_id.id,
							'op9_clamping_area': entry_rec.op9_clamping_area,
							'op9_id': entry_rec.op9_id.id,
							'parent_id' : ids[0],
							'last_operation_check_id': entry_rec.last_operation_check_id,
							'state': 'active',
							'op9_state': 'pending',
							'op9_process_result':'',
						
						}			
						copy_id = self.copy(cr, uid, entry_rec.id,op_vals, context)
						
						copy_rec = self.browse(cr, uid, copy_id)
						
						for dimen_item in copy_rec.op9_line_ids:
							
							dimen_vals = {
								'actual_val': 0,
								'remark': False,
							}
							
							dimension_obj = self.pool.get('ch.ms.dimension.details')
							dimension_obj.write(cr, uid, dimen_item.id, dimen_vals, context)
						
					if entry_rec.ms_type == 'foundry_item':
						
						ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_rejected_qty': entry_rec.ms_id.ms_rejected_qty + entry_rec.inhouse_qty})
						
						## Operation 9 Status Updation ###
						if entry_rec.op9_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op9_state':'reject'})
							
						self.write(cr, uid, ids, {'state':'reject'})
								
						#### NC Creation for reject Qty ###
						
						### Production Number ###
						produc_name = ''	
						produc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.production')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,produc_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(produc_seq_id[0],rec.code,entry_rec.entry_date))
						produc_name = cr.fetchone();
						
						### Issue Number ###
						issue_name = ''	
						issue_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pattern.issue')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,issue_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(issue_seq_id[0],rec.code,entry_rec.entry_date))
						issue_name = cr.fetchone();
						
						### Core Log Number ###
						core_name = ''	
						core_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,core_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_seq_id[0],rec.code,entry_rec.entry_date))
						core_name = cr.fetchone();
						
						### Mould Log Number ###
						mould_name = ''	
						mould_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,mould_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_seq_id[0],rec.code,entry_rec.entry_date))
						mould_name = cr.fetchone();
						
						production_vals = {
												
							'name': produc_name[0],
							'schedule_id': entry_rec.ms_id.schedule_id.id,
							'schedule_date': entry_rec.ms_id.schedule_date,
							'division_id': entry_rec.ms_id.division_id.id,
							'location' : entry_rec.ms_id.location,
							'schedule_line_id': entry_rec.ms_id.schedule_line_id.id,
							'order_id': entry_rec.ms_id.order_id.id,
							'order_line_id': entry_rec.ms_id.order_line_id.id,
							'order_bomline_id': entry_rec.ms_id.order_bomline_id.id,
							'qty' : entry_rec.inhouse_qty,			  
							'schedule_qty' : entry_rec.inhouse_qty,			  
							'state' : 'issue_done',
							'order_category':entry_rec.ms_id.order_category,
							'order_priority': '1',
							'pattern_id' : entry_rec.ms_id.pattern_id.id,
							'pattern_name' : entry_rec.ms_id.pattern_id.pattern_name,	
							'moc_id' : entry_rec.ms_id.moc_id.id,
							'request_state': 'done',
							'issue_no': issue_name[0],
							'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'issue_qty': 1,
							'issue_state': 'issued',
							'core_no': core_name[0],
							'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'core_qty': entry_rec.inhouse_qty,	
							'core_rem_qty': entry_rec.inhouse_qty,	
							'core_state': 'pending',
							'mould_no': mould_name[0],
							'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'mould_qty': entry_rec.inhouse_qty,	
							'mould_rem_qty': entry_rec.inhouse_qty,	
							'mould_state': 'pending',		
						}
						
						production_id = self.pool.get('kg.production').create(cr, uid, production_vals)
					
			else:
				if entry_rec.op9_button_status == 'visible':
					sc_obj = self.pool.get('kg.subcontract.process')
					
					self.write(cr, uid, ids, {'op9_sc_status': 'sc','op9_button_status': 'invisible'})	
					sc_name = ''	
					sc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.process')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,sc_seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(sc_seq_id[0],seq_rec.code))
					sc_name = cr.fetchone();
					
					wo_id = self.pool.get('kg.work.order').search(cr, uid, [('flag_for_stock','=','t')])
					if entry_rec.order_id.id == wo_id[0]:
						sc_actual_qty = 0
					else:
						sc_actual_qty = entry_rec.inhouse_qty
					
					sc_vals = {
						'name': sc_name[0],
						'ms_plan_id': entry_rec.ms_plan_id.id,
						'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
						'sc_qty': entry_rec.inhouse_qty,
						'total_qty': entry_rec.inhouse_qty,
						'pending_qty': entry_rec.inhouse_qty,
						'actual_qty': sc_actual_qty,
						'ms_op_id': entry_rec.id,
						'contractor_id': entry_rec.op9_contractor_id.id,
					}
					sc_id = sc_obj.create(cr, uid,sc_vals)
		else:
			pass
						
				
		return True
		
	### Operation 10 ###
		
	def onchange_operation10_sc(self, cr, uid, ids,op10_flag_sc, context=None):
		value = {'op10_sc_status': 'inhouse'}
		if op10_flag_sc == True:
			value = {'op10_sc_status': 'sc'}
		return {'value': value}
		
	def onchange_operation10_time(self, cr, uid, ids,op10_start_time,op10_end_time, context=None):
		value = {'op10_total_time': 0.00}
		total_time = 0.00
		total_time = op10_end_time - op10_start_time
		value = {'op10_total_time': total_time}
		return {'value': value}
		
	def onchange_operation10_cost_incurred(self, cr, uid, ids,op10_id,op10_stage_id,position_id,op10_total_time, context=None):
		value = {'op10_cost_incurred': 0.00}
		### Cost Incurred Calculation ###
		cr.execute(""" select in_house_cost from ch_kg_position_number 
			where operation_id = %s and stage_id = %s
			and header_id = %s limit 1 """ %(op10_id,op10_stage_id,position_id))
		inhouse_cost = cr.fetchone()
		cost_incurred = 0.00
		if inhouse_cost:
			
			if inhouse_cost[0] >= 0:
				cost_incurred = op10_total_time * inhouse_cost[0]
		value = {'op10_cost_incurred': cost_incurred}
		return {'value': value}
			
	def operation10_update(self, cr, uid, ids, context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		ms_obj = self.pool.get('kg.machineshop')
		
		if entry_rec.op10_state == 'pending':
			if entry_rec.op10_flag_sc != True:
			
				for dim_item in entry_rec.op10_line_ids:
					
					today = date.today()
					today = str(today)
					today = datetime.strptime(today, '%Y-%m-%d')
					start_date = entry_rec.op10_start_date
					start_date = str(start_date)
					start_date = datetime.strptime(start_date, '%Y-%m-%d')
					end_date = entry_rec.op10_end_date
					end_date = str(end_date)
					end_date = datetime.strptime(end_date, '%Y-%m-%d')
					if start_date > today or end_date > today:
						raise osv.except_osv(_('Warning!'),
								_('Start and End date should be less than or equal to current date!!'))
								
					if entry_rec.op10_start_time == entry_rec.op10_end_time:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not be equal !!'))
								
					if entry_rec.op10_start_time > 24 or entry_rec.op10_end_time > 24:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not exceed 24 hrs !!'))
					
					if dim_item.actual_val < 0:
						raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative. Check the actual value !!'))
					
					#~ if entry_rec.op10_process_result != 'reject':			
						#~ 
						#~ if dim_item.actual_val == 0:
							#~ raise osv.except_osv(_('Warning!'),
									#~ _('System not allow to save zero values. Check the actual value !!'))
									
						#### Min and Max Tolerance Checking ####
						
						if dim_item.pos_dimension_id != None:
						
							min_tol_value = (dim_item.min_val * dim_item.pos_dimension_id.min_tolerance) / 100
							max_tol_value = (dim_item.max_val * dim_item.pos_dimension_id.max_tolerance) / 100
									
							if dim_item.actual_val < (dim_item.min_val - min_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should greater or equal to Minimum value !!'))
										
							if dim_item.actual_val > (dim_item.max_val + max_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should lesser or equal to Maximum value !!'))
								
				### Last Operation Check ###
				cr.execute(""" select id from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s and is_last_operation = 't' """ %(entry_rec.op10_id.id,entry_rec.op10_stage_id.id,entry_rec.position_id.id))
				last_operation_id = cr.fetchone()
				
				pending_operation_id = []
				if last_operation_id:
					cr.execute(""" select id from kg_ms_operations

						where

						op2_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op2_state in ('pending','partial')  and  op2_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op3_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op3_state in ('pending','partial')  and  op3_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op4_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op4_state in ('pending','partial')  and  op4_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op5_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op5_state in ('pending','partial')  and  op5_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op6_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op6_state in ('pending','partial')  and  op6_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op7_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op7_state in ('pending','partial')  and  op7_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op8_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op8_state in ('pending','partial')  and  op8_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op9_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op9_state in ('pending','partial')  and  op9_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op1_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op1_state in ('pending','partial')  and  op1_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op11_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op11_state in ('pending','partial')  and  op11_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op12_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op12_state in ('pending','partial')  and  op12_sc_status = 'inhouse' and last_operation_check_id = %s


						limit 1
						""" 
						%(
						entry_rec.position_id.id,entry_rec.op10_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op10_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op10_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op10_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op10_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op10_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op10_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op10_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op10_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op10_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op10_id.id,
						entry_rec.position_id.id,entry_rec.id,
						))
					pending_operation_id = cr.fetchone()
					if pending_operation_id:
						if pending_operation_id[0] > 0:
							if entry_rec.op10_process_result != 'reject':
								raise osv.except_osv(_('Warning!'),
										_('This is last operation. Previous operations yet to be complete. !!'))
									
				### Cost Incurred Calculation ###
				cr.execute(""" select in_house_cost from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s limit 1 """ %(entry_rec.op10_id.id,entry_rec.op10_stage_id.id,entry_rec.position_id.id))
				inhouse_cost = cr.fetchone()
				cost_incurred = 0.00
				if inhouse_cost:
					
					if inhouse_cost[0] >= 0:
						cost_incurred = entry_rec.op10_total_time * inhouse_cost[0]
				
				self.write(cr,uid, ids,{'op10_cost_incurred':cost_incurred})
				if entry_rec.op10_process_result != 'rework':
					self.write(cr,uid, ids,{'op10_state': 'done','op10_button_status':'invisible'})
				### Operation Completion ###
				if last_operation_id:
					if pending_operation_id == None and last_operation_id[0] > 0:
						cr.execute(""" select id from kg_ms_operations

							where

							op1_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op1_state in ('pending','partial')  and  op1_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op2_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op2_state in ('pending','partial')  and  op2_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op4_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op4_state in ('pending','partial')  and  op4_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op3_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op3_state in ('pending','partial')  and  op3_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op5_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op5_state in ('pending','partial')  and  op5_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op6_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op6_state in ('pending','partial')  and  op6_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op7_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op7_state in ('pending','partial')  and  op7_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op8_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op8_state in ('pending','partial')  and  op8_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op9_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op9_state in ('pending','partial')  and  op9_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op11_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op11_state in ('pending','partial')  and  op11_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op12_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op12_state in ('pending','partial')  and  op12_sc_status = 'sc' and last_operation_check_id = %s


							limit 1
							""" 
							%(
							entry_rec.position_id.id,entry_rec.op10_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op10_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op10_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op10_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op10_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op10_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op10_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op10_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op10_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op10_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op10_id.id,
							entry_rec.position_id.id,entry_rec.id,
							))
						pending_operation = cr.fetchone()
						if pending_operation == None:
							if entry_rec.op10_process_result == 'accept':
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_completed_qty': entry_rec.ms_id.ms_completed_qty + entry_rec.inhouse_qty})
								ms_store_vals = {
									'operation_id': entry_rec.id,
									'production_id': entry_rec.production_id.id,
									'foundry_assembly_id': entry_rec.production_id.assembly_id,
									'foundry_assembly_line_id': entry_rec.production_id.assembly_line_id,
									'ms_assembly_id': entry_rec.ms_id.assembly_id,
									'ms_assembly_line_id': entry_rec.ms_id.assembly_line_id,
									'qty': entry_rec.inhouse_qty
								}
								ms_store_id = self.pool.get('kg.ms.stores').create(cr, uid, ms_store_vals)
							if (entry_rec.ms_id.ms_completed_qty + entry_rec.ms_id.ms_rejected_qty) == entry_rec.ms_id.ms_sch_qty:
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_state':'op_completed'})
				
				if entry_rec.op10_process_result == 'reject':
				
					
					### Department Indent Creation when process result is reject for ms item ###
					if entry_rec.ms_type == 'ms_item':
						
						## Operation 10 Status Updation ###
						if entry_rec.op10_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op10_state':'reject'})
						self.write(cr, uid, ids, {'state':'reject'})
						if entry_rec.ms_id.ms_id.line_ids:
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP2')])
							
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry_rec.entry_date))
							seq_name = cr.fetchone();

							dep_indent_obj = self.pool.get('kg.depindent')
							dep_indent_vals = {
								'name':'',
								'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
								'dep_name':1,
								'entry_mode':'auto',
								'state': 'approved',
								'indent_type': 'production',
								'name': seq_name[0],
								'order_id': entry_rec.order_id.id,
								'order_line_id': entry_rec.order_line_id.id,
								'src_location_id': location.main_location.id,
								'dest_location_id': location.stock_location.id
								}
								
							indent_id = dep_indent_obj.create(cr, uid, dep_indent_vals)
							for indent_item in entry_rec.ms_id.ms_id.line_ids:
								dep_indent_line_obj = self.pool.get('kg.depindent.line')
								product_rec = self.pool.get('product.product').browse(cr, uid, indent_item.product_id.id)
								dep_indent_line_vals = {
								'indent_id':indent_id,
								'product_id': indent_item.product_id.id,
								'uom': product_rec.uom_id.id,
								'qty': indent_item.qty * entry_rec.inhouse_qty,
								'pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								'issue_pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								#~ 'cutting_qty':ms_raw_rec.temp_qty,
								'ms_bot_id':entry_rec.ms_id.ms_id.id,
								'fns_item_name':entry_rec.item_name,
								'position_id': entry_rec.position_id.id
								}
								
								indent_line_id = dep_indent_line_obj.create(cr, uid, dep_indent_line_vals)
								
								indent_wo_line_obj = self.pool.get('ch.depindent.wo')
							
								indent_wo_line_vals = {
									'header_id':indent_line_id,
									'wo_id':entry_rec.order_no,
									'w_order_id':entry_rec.order_id.id,
									'w_order_line_id':entry_rec.order_line_id.id,
									'qty':indent_item.qty * entry_rec.inhouse_qty,
								}
								indent_wo_line_id = indent_wo_line_obj.create(cr, uid, indent_wo_line_vals)
						
						### New Entry Creation for same Operation ###
						op_vals = {
							'ms_id': entry_rec.ms_id.id,
							'ms_plan_id': entry_rec.ms_plan_id.id,
							'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
							'inhouse_qty': 1,
							'op10_stage_id': entry_rec.op10_stage_id.id,
							'op10_clamping_area': entry_rec.op10_clamping_area,
							'op10_id': entry_rec.op10_id.id,
							'parent_id' : ids[0],
							'last_operation_check_id': entry_rec.last_operation_check_id,
							'state': 'active',
							'op10_state': 'pending',
							'op10_process_result':'',
							
						}			
						copy_id = self.copy(cr, uid, entry_rec.id,op_vals, context)
						
						copy_rec = self.browse(cr, uid, copy_id)
						
						for dimen_item in copy_rec.op10_line_ids:
							
							dimen_vals = {
								'actual_val': 0,
								'remark': False,
							}
							
							dimension_obj = self.pool.get('ch.ms.dimension.details')
							dimension_obj.write(cr, uid, dimen_item.id, dimen_vals, context)
						
					if entry_rec.ms_type == 'foundry_item':
						
						ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_rejected_qty': entry_rec.ms_id.ms_rejected_qty + entry_rec.inhouse_qty})
						
						## Operation 10 Status Updation ###
						if entry_rec.op10_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op10_state':'reject'})
							
						self.write(cr, uid, ids, {'state':'reject'})
								
						#### NC Creation for reject Qty ###
						
						### Production Number ###
						produc_name = ''	
						produc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.production')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,produc_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(produc_seq_id[0],rec.code,entry_rec.entry_date))
						produc_name = cr.fetchone();
						
						### Issue Number ###
						issue_name = ''	
						issue_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pattern.issue')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,issue_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(issue_seq_id[0],rec.code,entry_rec.entry_date))
						issue_name = cr.fetchone();
						
						### Core Log Number ###
						core_name = ''	
						core_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,core_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_seq_id[0],rec.code,entry_rec.entry_date))
						core_name = cr.fetchone();
						
						### Mould Log Number ###
						mould_name = ''	
						mould_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,mould_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_seq_id[0],rec.code,entry_rec.entry_date))
						mould_name = cr.fetchone();
						
						production_vals = {
												
							'name': produc_name[0],
							'schedule_id': entry_rec.ms_id.schedule_id.id,
							'schedule_date': entry_rec.ms_id.schedule_date,
							'division_id': entry_rec.ms_id.division_id.id,
							'location' : entry_rec.ms_id.location,
							'schedule_line_id': entry_rec.ms_id.schedule_line_id.id,
							'order_id': entry_rec.ms_id.order_id.id,
							'order_line_id': entry_rec.ms_id.order_line_id.id,
							'order_bomline_id': entry_rec.ms_id.order_bomline_id.id,
							'qty' : entry_rec.inhouse_qty,			  
							'schedule_qty' : entry_rec.inhouse_qty,			  
							'state' : 'issue_done',
							'order_category':entry_rec.ms_id.order_category,
							'order_priority': '1',
							'pattern_id' : entry_rec.ms_id.pattern_id.id,
							'pattern_name' : entry_rec.ms_id.pattern_id.pattern_name,	
							'moc_id' : entry_rec.ms_id.moc_id.id,
							'request_state': 'done',
							'issue_no': issue_name[0],
							'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'issue_qty': 1,
							'issue_state': 'issued',
							'core_no': core_name[0],
							'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'core_qty': entry_rec.inhouse_qty,	
							'core_rem_qty': entry_rec.inhouse_qty,	
							'core_state': 'pending',
							'mould_no': mould_name[0],
							'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'mould_qty': entry_rec.inhouse_qty,	
							'mould_rem_qty': entry_rec.inhouse_qty,	
							'mould_state': 'pending',		
						}
						
						production_id = self.pool.get('kg.production').create(cr, uid, production_vals)
					
			else:
				if entry_rec.op10_button_status == 'visible':
					sc_obj = self.pool.get('kg.subcontract.process')
					
					self.write(cr, uid, ids, {'op10_sc_status': 'sc','op10_button_status': 'invisible'})	
					sc_name = ''	
					sc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.process')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,sc_seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(sc_seq_id[0],seq_rec.code))
					sc_name = cr.fetchone();
					
					wo_id = self.pool.get('kg.work.order').search(cr, uid, [('flag_for_stock','=','t')])
					if entry_rec.order_id.id == wo_id[0]:
						sc_actual_qty = 0
					else:
						sc_actual_qty = entry_rec.inhouse_qty
					
					sc_vals = {
						'name': sc_name[0],
						'ms_plan_id': entry_rec.ms_plan_id.id,
						'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
						'sc_qty': entry_rec.inhouse_qty,
						'total_qty': entry_rec.inhouse_qty,
						'pending_qty': entry_rec.inhouse_qty,
						'actual_qty': sc_actual_qty,
						'ms_op_id': entry_rec.id,
						'contractor_id': entry_rec.op10_contractor_id.id,
					}
					sc_id = sc_obj.create(cr, uid,sc_vals)
		else:
			pass
						
				
		return True
		
	### Operation 11 ###
		
	def onchange_operation11_sc(self, cr, uid, ids,op11_flag_sc, context=None):
		value = {'op11_sc_status': 'inhouse'}
		if op11_flag_sc == True:
			value = {'op11_sc_status': 'sc'}
		return {'value': value}
		
	def onchange_operation11_time(self, cr, uid, ids,op11_start_time,op11_end_time, context=None):
		value = {'op11_total_time': 0.00}
		total_time = 0.00
		total_time = op11_end_time - op11_start_time
		value = {'op11_total_time': total_time}
		return {'value': value}
		
	def onchange_operation11_cost_incurred(self, cr, uid, ids,op11_id,op11_stage_id,position_id,op11_total_time, context=None):
		value = {'op11_cost_incurred': 0.00}
		### Cost Incurred Calculation ###
		cr.execute(""" select in_house_cost from ch_kg_position_number 
			where operation_id = %s and stage_id = %s
			and header_id = %s limit 1 """ %(op11_id,op11_stage_id,position_id))
		inhouse_cost = cr.fetchone()
		cost_incurred = 0.00
		if inhouse_cost:
			
			if inhouse_cost[0] >= 0:
				cost_incurred = op11_total_time * inhouse_cost[0]
		value = {'op11_cost_incurred': cost_incurred}
		return {'value': value}
			
	def operation11_update(self, cr, uid, ids, context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		ms_obj = self.pool.get('kg.machineshop')
		
		if entry_rec.op11_state == 'pending':
			if entry_rec.op11_flag_sc != True:
			
				for dim_item in entry_rec.op11_line_ids:
					
					today = date.today()
					today = str(today)
					today = datetime.strptime(today, '%Y-%m-%d')
					start_date = entry_rec.op11_start_date
					start_date = str(start_date)
					start_date = datetime.strptime(start_date, '%Y-%m-%d')
					end_date = entry_rec.op11_end_date
					end_date = str(end_date)
					end_date = datetime.strptime(end_date, '%Y-%m-%d')
					if start_date > today or end_date > today:
						raise osv.except_osv(_('Warning!'),
								_('Start and End date should be less than or equal to current date!!'))
								
					if entry_rec.op11_start_time == entry_rec.op11_end_time:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not be equal !!'))
								
					if entry_rec.op11_start_time > 24 or entry_rec.op11_end_time > 24:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not exceed 24 hrs !!'))
					
					if dim_item.actual_val < 0:
						raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative. Check the actual value !!'))
					
					#~ if entry_rec.op11_process_result != 'reject':			
						#~ 
						#~ if dim_item.actual_val == 0:
							#~ raise osv.except_osv(_('Warning!'),
									#~ _('System not allow to save zero values. Check the actual value !!'))
									
						#### Min and Max Tolerance Checking ####
						
						if dim_item.pos_dimension_id != None:
						
							min_tol_value = (dim_item.min_val * dim_item.pos_dimension_id.min_tolerance) / 100
							max_tol_value = (dim_item.max_val * dim_item.pos_dimension_id.max_tolerance) / 100
									
							if dim_item.actual_val < (dim_item.min_val - min_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should greater or equal to Minimum value !!'))
										
							if dim_item.actual_val > (dim_item.max_val + max_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should lesser or equal to Maximum value !!'))
								
				### Last Operation Check ###
				cr.execute(""" select id from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s and is_last_operation = 't' """ %(entry_rec.op11_id.id,entry_rec.op11_stage_id.id,entry_rec.position_id.id))
				last_operation_id = cr.fetchone()
				
				pending_operation_id = []
				if last_operation_id:
					cr.execute(""" select id from kg_ms_operations

						where

						op2_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op2_state in ('pending','partial')  and  op2_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op3_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op3_state in ('pending','partial')  and  op3_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op4_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op4_state in ('pending','partial')  and  op4_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op5_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op5_state in ('pending','partial')  and  op5_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op6_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op6_state in ('pending','partial')  and  op6_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op7_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op7_state in ('pending','partial')  and  op7_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op8_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op8_state in ('pending','partial')  and  op8_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op9_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op9_state in ('pending','partial')  and  op9_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op10_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op10_state in ('pending','partial')  and  op10_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op1_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op1_state in ('pending','partial')  and  op1_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op12_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op12_state in ('pending','partial')  and  op12_sc_status = 'inhouse' and last_operation_check_id = %s


						limit 1
						""" 
						%(
						entry_rec.position_id.id,entry_rec.op11_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op11_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op11_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op11_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op11_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op11_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op11_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op11_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op11_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op11_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op11_id.id,
						entry_rec.position_id.id,entry_rec.id,
						))
					pending_operation_id = cr.fetchone()
					if pending_operation_id:
						if pending_operation_id[0] > 0:
							if entry_rec.op11_process_result != 'reject':
								raise osv.except_osv(_('Warning!'),
										_('This is last operation. Previous operations yet to be complete. !!'))
									
				### Cost Incurred Calculation ###
				cr.execute(""" select in_house_cost from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s limit 1 """ %(entry_rec.op11_id.id,entry_rec.op11_stage_id.id,entry_rec.position_id.id))
				inhouse_cost = cr.fetchone()
				cost_incurred = 0.00
				if inhouse_cost:
					
					if inhouse_cost[0] >= 0:
						cost_incurred = entry_rec.op11_total_time * inhouse_cost[0]
				
				self.write(cr,uid, ids,{'op11_cost_incurred':cost_incurred})
				if entry_rec.op11_process_result != 'rework':
					self.write(cr,uid, ids,{'op11_state': 'done','op11_button_status':'invisible'})
				### Operation Completion ###
				if last_operation_id:
					if pending_operation_id == None and last_operation_id[0] > 0:
						cr.execute(""" select id from kg_ms_operations

							where

							op1_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op1_state in ('pending','partial')  and  op1_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op2_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op2_state in ('pending','partial')  and  op2_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op4_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op4_state in ('pending','partial')  and  op4_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op3_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op3_state in ('pending','partial')  and  op3_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op5_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op5_state in ('pending','partial')  and  op5_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op6_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op6_state in ('pending','partial')  and  op6_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op7_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op7_state in ('pending','partial')  and  op7_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op8_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op8_state in ('pending','partial')  and  op8_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op9_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op9_state in ('pending','partial')  and  op9_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op10_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op10_state in ('pending','partial')  and  op10_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op12_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op12_state in ('pending','partial')  and  op12_sc_status = 'sc' and last_operation_check_id = %s


							limit 1
							""" 
							%(
							entry_rec.position_id.id,entry_rec.op11_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op11_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op11_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op11_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op11_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op11_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op11_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op11_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op11_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op11_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op11_id.id,
							entry_rec.position_id.id,entry_rec.id,
							))
						pending_operation = cr.fetchone()
						if pending_operation == None:
							if entry_rec.op11_process_result == 'accept':
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_completed_qty': entry_rec.ms_id.ms_completed_qty + entry_rec.inhouse_qty})
								ms_store_vals = {
									'operation_id': entry_rec.id,
									'production_id': entry_rec.production_id.id,
									'foundry_assembly_id': entry_rec.production_id.assembly_id,
									'foundry_assembly_line_id': entry_rec.production_id.assembly_line_id,
									'ms_assembly_id': entry_rec.ms_id.assembly_id,
									'ms_assembly_line_id': entry_rec.ms_id.assembly_line_id,
									'qty': entry_rec.inhouse_qty
								}
								ms_store_id = self.pool.get('kg.ms.stores').create(cr, uid, ms_store_vals)
							if (entry_rec.ms_id.ms_completed_qty + entry_rec.ms_id.ms_rejected_qty) == entry_rec.ms_id.ms_sch_qty:
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_state':'op_completed'})
				
				if entry_rec.op11_process_result == 'reject':
				
					
					### Department Indent Creation when process result is reject for ms item ###
					if entry_rec.ms_type == 'ms_item':
						
						## Operation 11 Status Updation ###
						if entry_rec.op11_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op11_state':'reject'})
						self.write(cr, uid, ids, {'state':'reject'})
						if entry_rec.ms_id.ms_id.line_ids:
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP2')])
							
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry_rec.entry_date))
							seq_name = cr.fetchone();

							dep_indent_obj = self.pool.get('kg.depindent')
							dep_indent_vals = {
								'name':'',
								'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
								'dep_name':1,
								'entry_mode':'auto',
								'state': 'approved',
								'indent_type': 'production',
								'name': seq_name[0],
								'order_id': entry_rec.order_id.id,
								'order_line_id': entry_rec.order_line_id.id,
								'src_location_id': location.main_location.id,
								'dest_location_id': location.stock_location.id
								}
								
							indent_id = dep_indent_obj.create(cr, uid, dep_indent_vals)
							for indent_item in entry_rec.ms_id.ms_id.line_ids:
								dep_indent_line_obj = self.pool.get('kg.depindent.line')
								product_rec = self.pool.get('product.product').browse(cr, uid, indent_item.product_id.id)
								dep_indent_line_vals = {
								'indent_id':indent_id,
								'product_id': indent_item.product_id.id,
								'uom': product_rec.uom_id.id,
								'qty': indent_item.qty * entry_rec.inhouse_qty,
								'pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								'issue_pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								#~ 'cutting_qty':ms_raw_rec.temp_qty,
								'ms_bot_id':entry_rec.ms_id.ms_id.id,
								'fns_item_name':entry_rec.item_name,
								'position_id': entry_rec.position_id.id
								}
								
								indent_line_id = dep_indent_line_obj.create(cr, uid, dep_indent_line_vals)
								
								indent_wo_line_obj = self.pool.get('ch.depindent.wo')
							
								indent_wo_line_vals = {
									'header_id':indent_line_id,
									'wo_id':entry_rec.order_no,
									'w_order_id':entry_rec.order_id.id,
									'w_order_line_id':entry_rec.order_line_id.id,
									'qty':indent_item.qty * entry_rec.inhouse_qty,
								}
								indent_wo_line_id = indent_wo_line_obj.create(cr, uid, indent_wo_line_vals)
						
						### New Entry Creation for same Operation ###
						op_vals = {
							'ms_id': entry_rec.ms_id.id,
							'ms_plan_id': entry_rec.ms_plan_id.id,
							'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
							'inhouse_qty': 1,
							'op11_stage_id': entry_rec.op11_stage_id.id,
							'op11_clamping_area': entry_rec.op11_clamping_area,
							'op11_id': entry_rec.op11_id.id,
							'parent_id' : ids[0],
							'last_operation_check_id': entry_rec.last_operation_check_id,
							'state': 'active',
							'op11_state': 'pending',
							'op11_process_result':'',
							
						}			
						copy_id = self.copy(cr, uid, entry_rec.id,op_vals, context)
						
						copy_rec = self.browse(cr, uid, copy_id)
						
						for dimen_item in copy_rec.op11_line_ids:
							
							dimen_vals = {
								'actual_val': 0,
								'remark': False,
							}
							
							dimension_obj = self.pool.get('ch.ms.dimension.details')
							dimension_obj.write(cr, uid, dimen_item.id, dimen_vals, context)
						
					if entry_rec.ms_type == 'foundry_item':
						
						ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_rejected_qty': entry_rec.ms_id.ms_rejected_qty + entry_rec.inhouse_qty})
						
						## Operation 11 Status Updation ###
						if entry_rec.op11_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op11_state':'reject'})
							
						self.write(cr, uid, ids, {'state':'reject'})
								
						#### NC Creation for reject Qty ###
						
						### Production Number ###
						produc_name = ''	
						produc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.production')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,produc_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(produc_seq_id[0],rec.code,entry_rec.entry_date))
						produc_name = cr.fetchone();
						
						### Issue Number ###
						issue_name = ''	
						issue_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pattern.issue')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,issue_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(issue_seq_id[0],rec.code,entry_rec.entry_date))
						issue_name = cr.fetchone();
						
						### Core Log Number ###
						core_name = ''	
						core_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,core_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_seq_id[0],rec.code,entry_rec.entry_date))
						core_name = cr.fetchone();
						
						### Mould Log Number ###
						mould_name = ''	
						mould_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,mould_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_seq_id[0],rec.code,entry_rec.entry_date))
						mould_name = cr.fetchone();
						
						production_vals = {
												
							'name': produc_name[0],
							'schedule_id': entry_rec.ms_id.schedule_id.id,
							'schedule_date': entry_rec.ms_id.schedule_date,
							'division_id': entry_rec.ms_id.division_id.id,
							'location' : entry_rec.ms_id.location,
							'schedule_line_id': entry_rec.ms_id.schedule_line_id.id,
							'order_id': entry_rec.ms_id.order_id.id,
							'order_line_id': entry_rec.ms_id.order_line_id.id,
							'order_bomline_id': entry_rec.ms_id.order_bomline_id.id,
							'qty' : entry_rec.inhouse_qty,			  
							'schedule_qty' : entry_rec.inhouse_qty,			  
							'state' : 'issue_done',
							'order_category':entry_rec.ms_id.order_category,
							'order_priority': '1',
							'pattern_id' : entry_rec.ms_id.pattern_id.id,
							'pattern_name' : entry_rec.ms_id.pattern_id.pattern_name,	
							'moc_id' : entry_rec.ms_id.moc_id.id,
							'request_state': 'done',
							'issue_no': issue_name[0],
							'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'issue_qty': 1,
							'issue_state': 'issued',
							'core_no': core_name[0],
							'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'core_qty': entry_rec.inhouse_qty,	
							'core_rem_qty': entry_rec.inhouse_qty,	
							'core_state': 'pending',
							'mould_no': mould_name[0],
							'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'mould_qty': entry_rec.inhouse_qty,	
							'mould_rem_qty': entry_rec.inhouse_qty,	
							'mould_state': 'pending',		
						}
						
						production_id = self.pool.get('kg.production').create(cr, uid, production_vals)
					
			else:
				if entry_rec.op11_button_status == 'visible':
					sc_obj = self.pool.get('kg.subcontract.process')
					
					self.write(cr, uid, ids, {'op11_sc_status': 'sc','op11_button_status': 'invisible'})	
					sc_name = ''	
					sc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.process')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,sc_seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(sc_seq_id[0],seq_rec.code))
					sc_name = cr.fetchone();
					
					wo_id = self.pool.get('kg.work.order').search(cr, uid, [('flag_for_stock','=','t')])
					if entry_rec.order_id.id == wo_id[0]:
						sc_actual_qty = 0
					else:
						sc_actual_qty = entry_rec.inhouse_qty
					
					sc_vals = {
						'name': sc_name[0],
						'ms_plan_id': entry_rec.ms_plan_id.id,
						'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
						'sc_qty': entry_rec.inhouse_qty,
						'total_qty': entry_rec.inhouse_qty,
						'pending_qty': entry_rec.inhouse_qty,
						'actual_qty': sc_actual_qty,
						'ms_op_id': entry_rec.id,
						'contractor_id': entry_rec.op11_contractor_id.id,
					}
					sc_id = sc_obj.create(cr, uid,sc_vals)
		else:
			pass
						
				
		return True
		
	### Operation 12 ###
		
	def onchange_operation12_sc(self, cr, uid, ids,op12_flag_sc, context=None):
		value = {'op12_sc_status': 'inhouse'}
		if op12_flag_sc == True:
			value = {'op12_sc_status': 'sc'}
		return {'value': value}
		
	def onchange_operation12_time(self, cr, uid, ids,op12_start_time,op12_end_time, context=None):
		value = {'op12_total_time': 0.00}
		total_time = 0.00
		total_time = op12_end_time - op12_start_time
		value = {'op12_total_time': total_time}
		return {'value': value}
		
	def onchange_operation12_cost_incurred(self, cr, uid, ids,op12_id,op12_stage_id,position_id,op12_total_time, context=None):
		value = {'op12_cost_incurred': 0.00}
		### Cost Incurred Calculation ###
		cr.execute(""" select in_house_cost from ch_kg_position_number 
			where operation_id = %s and stage_id = %s
			and header_id = %s limit 1 """ %(op12_id,op12_stage_id,position_id))
		inhouse_cost = cr.fetchone()
		cost_incurred = 0.00
		if inhouse_cost:
			
			if inhouse_cost[0] >= 0:
				cost_incurred = op12_total_time * inhouse_cost[0]
		value = {'op12_cost_incurred': cost_incurred}
		return {'value': value}
			
	def operation12_update(self, cr, uid, ids, context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		ms_obj = self.pool.get('kg.machineshop')
		
		if entry_rec.op12_state == 'pending':
			if entry_rec.op12_flag_sc != True:
			
				for dim_item in entry_rec.op12_line_ids:
					
					today = date.today()
					today = str(today)
					today = datetime.strptime(today, '%Y-%m-%d')
					start_date = entry_rec.op12_start_date
					start_date = str(start_date)
					start_date = datetime.strptime(start_date, '%Y-%m-%d')
					end_date = entry_rec.op12_end_date
					end_date = str(end_date)
					end_date = datetime.strptime(end_date, '%Y-%m-%d')
					if start_date > today or end_date > today:
						raise osv.except_osv(_('Warning!'),
								_('Start and End date should be less than or equal to current date!!'))
								
					if entry_rec.op12_start_time == entry_rec.op12_end_time:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not be equal !!'))
								
					if entry_rec.op12_start_time > 24 or entry_rec.op12_end_time > 24:
						raise osv.except_osv(_('Warning!'),
								_('Start and End time should not exceed 24 hrs !!'))
					
					if dim_item.actual_val < 0:
						raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative. Check the actual value !!'))
					
					#~ if entry_rec.op12_process_result != 'reject':			
						#~ 
						#~ if dim_item.actual_val == 0:
							#~ raise osv.except_osv(_('Warning!'),
									#~ _('System not allow to save zero values. Check the actual value !!'))
									
						#### Min and Max Tolerance Checking ####
						
						if dim_item.pos_dimension_id != None:
						
							min_tol_value = (dim_item.min_val * dim_item.pos_dimension_id.min_tolerance) / 100
							max_tol_value = (dim_item.max_val * dim_item.pos_dimension_id.max_tolerance) / 100
									
							if dim_item.actual_val < (dim_item.min_val - min_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should greater or equal to Minimum value !!'))
										
							if dim_item.actual_val > (dim_item.max_val + max_tol_value):
								raise osv.except_osv(_('Warning!'),
										_('Actual value should lesser or equal to Maximum value !!'))
								
				### Last Operation Check ###
				cr.execute(""" select id from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s and is_last_operation = 't' """ %(entry_rec.op12_id.id,entry_rec.op12_stage_id.id,entry_rec.position_id.id))
				last_operation_id = cr.fetchone()
				
				pending_operation_id = []
				if last_operation_id:
					cr.execute(""" select id from kg_ms_operations

						where

						op2_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op2_state in ('pending','partial')  and  op2_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op3_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op3_state in ('pending','partial')  and  op3_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op4_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op4_state in ('pending','partial')  and  op4_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op5_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op5_state in ('pending','partial')  and  op5_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op6_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op6_state in ('pending','partial')  and  op6_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op7_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op7_state in ('pending','partial')  and  op7_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op8_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op8_state in ('pending','partial')  and  op8_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op9_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op9_state in ('pending','partial')  and  op9_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op10_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op10_state in ('pending','partial')  and  op10_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op11_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op11_state in ('pending','partial')  and  op11_sc_status = 'inhouse' and last_operation_check_id = %s
						
						or
						
						op1_id in (

						select operation_id from ch_kg_position_number
						where header_id = %s 
						and operation_id not in (select operation_id from ch_kg_position_number 
						where operation_id = %s
						and header_id = %s and is_last_operation = 't')) 

						and  op1_state in ('pending','partial')  and  op1_sc_status = 'inhouse' and last_operation_check_id = %s


						limit 1
						""" 
						%(
						entry_rec.position_id.id,entry_rec.op12_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op12_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op12_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op12_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op12_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op12_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op12_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op12_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op12_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op12_id.id,
						entry_rec.position_id.id,entry_rec.id,
						entry_rec.position_id.id,entry_rec.op12_id.id,
						entry_rec.position_id.id,entry_rec.id,
						))
					pending_operation_id = cr.fetchone()
					if pending_operation_id:
						if pending_operation_id[0] > 0:
							if entry_rec.op12_process_result != 'reject':
								raise osv.except_osv(_('Warning!'),
										_('This is last operation. Previous operations yet to be complete. !!'))
									
				### Cost Incurred Calculation ###
				cr.execute(""" select in_house_cost from ch_kg_position_number 
					where operation_id = %s and stage_id = %s
					and header_id = %s limit 1 """ %(entry_rec.op12_id.id,entry_rec.op12_stage_id.id,entry_rec.position_id.id))
				inhouse_cost = cr.fetchone()
				cost_incurred = 0.00
				if inhouse_cost:
					
					if inhouse_cost[0] >= 0:
						cost_incurred = entry_rec.op12_total_time * inhouse_cost[0]
				
				self.write(cr,uid, ids,{'op12_cost_incurred':cost_incurred})
				if entry_rec.op12_process_result != 'rework':
					self.write(cr,uid, ids,{'op12_state': 'done','op12_button_status':'invisible'})
				### Operation Completion ###
				if last_operation_id:
					if pending_operation_id == None and last_operation_id[0] > 0:
						cr.execute(""" select id from kg_ms_operations

							where

							op1_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op1_state in ('pending','partial')  and  op1_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op2_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op2_state in ('pending','partial')  and  op2_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op4_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op4_state in ('pending','partial')  and  op4_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op3_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op3_state in ('pending','partial')  and  op3_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op5_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op5_state in ('pending','partial')  and  op5_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op6_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op6_state in ('pending','partial')  and  op6_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op7_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op7_state in ('pending','partial')  and  op7_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op8_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op8_state in ('pending','partial')  and  op8_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op9_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op9_state in ('pending','partial')  and  op9_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op10_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op10_state in ('pending','partial')  and  op10_sc_status = 'sc' and last_operation_check_id = %s
							
							or
							
							op11_id in (

							select operation_id from ch_kg_position_number
							where header_id = %s 
							and operation_id not in (select operation_id from ch_kg_position_number 
							where operation_id = %s 
							and header_id = %s and is_last_operation = 't')) 

							and  op11_state in ('pending','partial')  and  op11_sc_status = 'sc' and last_operation_check_id = %s


							limit 1
							""" 
							%(
							entry_rec.position_id.id,entry_rec.op12_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op12_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op12_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op12_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op12_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op12_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op12_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op12_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op12_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op12_id.id,
							entry_rec.position_id.id,entry_rec.id,
							entry_rec.position_id.id,entry_rec.op12_id.id,
							entry_rec.position_id.id,entry_rec.id,
							))
						pending_operation = cr.fetchone()
						if pending_operation == None:
							if entry_rec.op12_process_result == 'accept':
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_completed_qty': entry_rec.ms_id.ms_completed_qty + entry_rec.inhouse_qty})
								ms_store_vals = {
									'operation_id': entry_rec.id,
									'production_id': entry_rec.production_id.id,
									'foundry_assembly_id': entry_rec.production_id.assembly_id,
									'foundry_assembly_line_id': entry_rec.production_id.assembly_line_id,
									'ms_assembly_id': entry_rec.ms_id.assembly_id,
									'ms_assembly_line_id': entry_rec.ms_id.assembly_line_id,
									'qty': entry_rec.inhouse_qty
								}
								ms_store_id = self.pool.get('kg.ms.stores').create(cr, uid, ms_store_vals)
							if (entry_rec.ms_id.ms_completed_qty + entry_rec.ms_id.ms_rejected_qty) == entry_rec.ms_id.ms_sch_qty:
								ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_state':'op_completed'})
				
				if entry_rec.op12_process_result == 'reject':
				
					
					### Department Indent Creation when process result is reject for ms item ###
					if entry_rec.ms_type == 'ms_item':
						
						## Operation 12 Status Updation ###
						if entry_rec.op12_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op12_state':'reject'})
						self.write(cr, uid, ids, {'state':'reject'})
						if entry_rec.ms_id.ms_id.line_ids:
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP2')])
							
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry_rec.entry_date))
							seq_name = cr.fetchone();

							dep_indent_obj = self.pool.get('kg.depindent')
							dep_indent_vals = {
								'name':'',
								'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
								'dep_name':1,
								'entry_mode':'auto',
								'state': 'approved',
								'indent_type': 'production',
								'name': seq_name[0],
								'order_id': entry_rec.order_id.id,
								'order_line_id': entry_rec.order_line_id.id,
								'src_location_id': location.main_location.id,
								'dest_location_id': location.stock_location.id
								}
								
							indent_id = dep_indent_obj.create(cr, uid, dep_indent_vals)
							for indent_item in entry_rec.ms_id.ms_id.line_ids:
								dep_indent_line_obj = self.pool.get('kg.depindent.line')
								product_rec = self.pool.get('product.product').browse(cr, uid, indent_item.product_id.id)
								dep_indent_line_vals = {
								'indent_id':indent_id,
								'product_id': indent_item.product_id.id,
								'uom': product_rec.uom_id.id,
								'qty': indent_item.qty * entry_rec.inhouse_qty,
								'pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								'issue_pending_qty':indent_item.qty * entry_rec.inhouse_qty,
								#~ 'cutting_qty':ms_raw_rec.temp_qty,
								'ms_bot_id':entry_rec.ms_id.ms_id.id,
								'fns_item_name':entry_rec.item_name,
								'position_id': entry_rec.position_id.id
								}
								
								indent_line_id = dep_indent_line_obj.create(cr, uid, dep_indent_line_vals)
								
								indent_wo_line_obj = self.pool.get('ch.depindent.wo')
							
								indent_wo_line_vals = {
									'header_id':indent_line_id,
									'wo_id':entry_rec.order_no,
									'w_order_id':entry_rec.order_id.id,
									'w_order_line_id':entry_rec.order_line_id.id,
									'qty':indent_item.qty * entry_rec.inhouse_qty,
								}
								indent_wo_line_id = indent_wo_line_obj.create(cr, uid, indent_wo_line_vals)
						
						### New Entry Creation for same Operation ###
						op_vals = {
							'ms_id': entry_rec.ms_id.id,
							'ms_plan_id': entry_rec.ms_plan_id.id,
							'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
							'inhouse_qty': 1,
							'op12_stage_id': entry_rec.op12_stage_id.id,
							'op12_clamping_area': entry_rec.op12_clamping_area,
							'op12_id': entry_rec.op12_id.id,
							'parent_id' : ids[0],
							'last_operation_check_id': entry_rec.last_operation_check_id,
							'state': 'active',
							'op12_state': 'pending',
							'op12_process_result':'',
							
						}			
						copy_id = self.copy(cr, uid, entry_rec.id,op_vals, context)
						
						copy_rec = self.browse(cr, uid, copy_id)
						
						for dimen_item in copy_rec.op12_line_ids:
							
							dimen_vals = {
								'actual_val': 0,
								'remark': False,
							}
							
							dimension_obj = self.pool.get('ch.ms.dimension.details')
							dimension_obj.write(cr, uid, dimen_item.id, dimen_vals, context)
						
					if entry_rec.ms_type == 'foundry_item':
						
						ms_obj.write(cr, uid, entry_rec.ms_id.id, {'ms_rejected_qty': entry_rec.ms_id.ms_rejected_qty + entry_rec.inhouse_qty})
						
						## Operation 11 Status Updation ###
						if entry_rec.op12_state in ('pending','partial','done'):
							self.write(cr, uid, ids, {'op12_state':'reject'})
							
						self.write(cr, uid, ids, {'state':'reject'})
								
						#### NC Creation for reject Qty ###
						
						### Production Number ###
						produc_name = ''	
						produc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.production')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,produc_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(produc_seq_id[0],rec.code,entry_rec.entry_date))
						produc_name = cr.fetchone();
						
						### Issue Number ###
						issue_name = ''	
						issue_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pattern.issue')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,issue_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(issue_seq_id[0],rec.code,entry_rec.entry_date))
						issue_name = cr.fetchone();
						
						### Core Log Number ###
						core_name = ''	
						core_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,core_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_seq_id[0],rec.code,entry_rec.entry_date))
						core_name = cr.fetchone();
						
						### Mould Log Number ###
						mould_name = ''	
						mould_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.log')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,mould_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_seq_id[0],rec.code,entry_rec.entry_date))
						mould_name = cr.fetchone();
						
						production_vals = {
												
							'name': produc_name[0],
							'schedule_id': entry_rec.ms_id.schedule_id.id,
							'schedule_date': entry_rec.ms_id.schedule_date,
							'division_id': entry_rec.ms_id.division_id.id,
							'location' : entry_rec.ms_id.location,
							'schedule_line_id': entry_rec.ms_id.schedule_line_id.id,
							'order_id': entry_rec.ms_id.order_id.id,
							'order_line_id': entry_rec.ms_id.order_line_id.id,
							'order_bomline_id': entry_rec.ms_id.order_bomline_id.id,
							'qty' : entry_rec.inhouse_qty,			  
							'schedule_qty' : entry_rec.inhouse_qty,			  
							'state' : 'issue_done',
							'order_category':entry_rec.ms_id.order_category,
							'order_priority': '1',
							'pattern_id' : entry_rec.ms_id.pattern_id.id,
							'pattern_name' : entry_rec.ms_id.pattern_id.pattern_name,	
							'moc_id' : entry_rec.ms_id.moc_id.id,
							'request_state': 'done',
							'issue_no': issue_name[0],
							'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'issue_qty': 1,
							'issue_state': 'issued',
							'core_no': core_name[0],
							'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'core_qty': entry_rec.inhouse_qty,	
							'core_rem_qty': entry_rec.inhouse_qty,	
							'core_state': 'pending',
							'mould_no': mould_name[0],
							'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'mould_qty': entry_rec.inhouse_qty,	
							'mould_rem_qty': entry_rec.inhouse_qty,	
							'mould_state': 'pending',		
						}
						
						production_id = self.pool.get('kg.production').create(cr, uid, production_vals)
					
			else:
				if entry_rec.op12_button_status == 'visible':
					sc_obj = self.pool.get('kg.subcontract.process')
					
					self.write(cr, uid, ids, {'op12_sc_status': 'sc','op12_button_status': 'invisible'})	
					sc_name = ''	
					sc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.process')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,sc_seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(sc_seq_id[0],seq_rec.code))
					sc_name = cr.fetchone();
					
					wo_id = self.pool.get('kg.work.order').search(cr, uid, [('flag_for_stock','=','t')])
					if entry_rec.order_id.id == wo_id[0]:
						sc_actual_qty = 0
					else:
						sc_actual_qty = entry_rec.inhouse_qty
					
					sc_vals = {
						'name': sc_name[0],
						'ms_plan_id': entry_rec.ms_plan_id.id,
						'ms_plan_line_id': entry_rec.ms_plan_line_id.id,
						'sc_qty': entry_rec.inhouse_qty,
						'total_qty': entry_rec.inhouse_qty,
						'pending_qty': entry_rec.inhouse_qty,
						'actual_qty': sc_actual_qty,
						'ms_op_id': entry_rec.id,
						'contractor_id': entry_rec.op12_contractor_id.id,
					}
					sc_id = sc_obj.create(cr, uid,sc_vals)
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
		return super(kg_ms_operations, self).write(cr, uid, ids, vals, context)
		
kg_ms_operations()


class ch_ms_dimension_details(osv.osv):
	
	_name = 'ch.ms.dimension.details'
	
	_columns = {
		
		'header_id':fields.many2one('kg.ms.operations', 'MS Operations', required=True, ondelete='cascade'),
		'position_id': fields.many2one('kg.position.number','Position No'),
		'operation_id': fields.many2one('kg.operation.master','Operation'),
		'operation_name': fields.char('Operation Name'),
		'position_line_id': fields.many2one('ch.kg.position.number','Position No Line'),
		'pos_dimension_id': fields.many2one('kg.dimension','Dimension'),	
		'dimension_id': fields.many2one('kg.dimension.master','Dimension'), 				
		'description': fields.char('Description'), 		
		'min_val': fields.float('Minimum Value'), 
		'max_val': fields.float('Maximum Value'), 
		'actual_val': fields.float('Actual Value'), 
		'remark': fields.text('Remarks'),
		
	}
	
ch_ms_dimension_details()

