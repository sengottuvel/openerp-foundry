from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

dt_time = lambda * a: time.strftime('%m/%d/%Y %H:%M:%S')

today = date.today()
today = str(today)
today = datetime.strptime(today, '%Y-%m-%d')


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


class kg_fettling(osv.osv):

	_name = "kg.fettling"
	_description = "Fettling Inward"
	_order = "order_priority asc"
	
	def _get_default_division(self, cr, uid, context=None):
		res = self.pool.get('kg.division.master').search(cr, uid, [('code','=','SAM'),('state','=','approved'), ('active','=','t')], context=context)
		return res and res[0] or False
	
	_columns = {
	
		### Schedule List ####
		'name': fields.char('Fettling Inward No', size=128,select=True,readonly=True),
		'entry_date': fields.date('Fettling Inward Date',required=True),
		'division_id': fields.many2one('kg.division.master','Division'),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location'),
		'active': fields.boolean('Active'),
		
		### Schedule Details ###
		'schedule_id': fields.many2one('kg.schedule','Schedule No.'),
		'schedule_date': fields.related('schedule_id','entry_date', type='date', string='Schedule Date', store=True, readonly=True),
		'schedule_line_id': fields.many2one('ch.schedule.details','Schedule Line Item'),
		
		### Work Order Details ###
		'order_bomline_id': fields.related('schedule_line_id','order_bomline_id', type='many2one', relation='ch.order.bom.details', string='Order BOM Line Id', store=True, readonly=True),
		'order_id': fields.many2one('kg.work.order','Work Order'),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line'),
		'allocation_id': fields.many2one('ch.stock.allocation.detail','Allocation'),
		'order_no': fields.related('order_line_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('order_line_id','delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'order_date': fields.related('order_id','entry_date', type='date', string='Order Date', store=True, readonly=True),
		'order_category': fields.related('order_line_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.selection(ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		
		'pump_model_id': fields.related('order_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('schedule_line_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_code': fields.related('pattern_id','name', type='char', string='Pattern Code', store=True, readonly=True),
		'pattern_name': fields.related('pattern_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('schedule_line_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'schedule_qty': fields.related('schedule_line_id','qty', type='integer', size=100, string='Schedule Qty', store=True, readonly=True),
		'production_id':fields.many2one('kg.production','Production'),
		'pour_qty': fields.integer('Poured Qty'),
		#~ 'pour_qty': fields.related('production_id','pour_qty', type='integer', size=100, string='Poured Qty', store=True, readonly=True),
		'stage_id':fields.many2one('kg.stage.master','Stage'),
		'stage_name': fields.related('stage_id','name', type='char', size=128, string='Stage Name', store=True, readonly=True),
		'melting_id': fields.related('production_id','pour_heat_id', type='many2one', relation='kg.melting', string='Heat No.', store=True, readonly=True),
		'pre_stage_date': fields.date('Previous stage completed on'),
		'pour_id':fields.many2one('kg.pouring.log','Pour Id'),
		'pour_line_id':fields.many2one('ch.pouring.details','Pour Id'),
		'pour_date': fields.related('pour_id','entry_date', type='datetime', string='Pouring date', store=True, readonly=True),
		
		#### Fettling Inward ####
		'inward_accept_qty': fields.integer('Accepted Qty', required=True),  
		'inward_reject_qty': fields.integer('Rejected Qty'),
		'inward_accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'inward_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'inward_reject_date': fields.date('Rejection Date'),
		'inward_remarks': fields.text('Remarks'),
		'state': fields.selection([('waiting','Waiting for Accept'),('accept','Accepted'),('complete','Completed'),('reject','Rejected')],'Status', readonly=True),
		
		### KNOCK OUT ###
		'knockout_name': fields.char('Production Entry Code', size=128,select=True,readonly=True),
		'knockout_date': fields.date('Date'),
		'knockout_shift_id':fields.many2one('kg.shift.master','Shift'),
		'knockout_contractor':fields.many2one('res.partner','Contractor'),
		'knockout_employee': fields.char('Employee',size=128),
		'knockout_qty': fields.integer('Total Qty'),
		'knockout_accept_qty': fields.integer('Accepted Qty'),
		'knockout_reject_qty': fields.integer('Rejected Qty'),
		'knockout_weight':fields.integer('Weight(kgs)'),
		'knockout_remarks': fields.text('Remarks'),
		'knockout_user_id': fields.many2one('res.users', 'Updated By', readonly=True),
		'knockout_accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'knockout_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'knockout_reject_date': fields.date('Rejection Date'),
		'knockout_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'flag_ko_special_app': fields.boolean('Special Approval'),
		'knockout_state': fields.selection([('pending','Pending'),('complete','Completed')],'Knockout State', readonly=True),
		
		### DECORING ###
		'decoring_name': fields.char('Production Entry Code', size=128,select=True,readonly=True),
		'decoring_date': fields.date('Date'),
		'decoring_shift_id':fields.many2one('kg.shift.master','Shift'),
		'decoring_contractor':fields.many2one('res.partner','Contractor'),
		'decoring_employee': fields.char('Employee',size=128),
		'decoring_qty': fields.integer('Total Qty'),
		'decoring_accept_qty': fields.integer('Accepted Qty'),
		'decoring_reject_qty': fields.integer('Rejected Qty'),
		'decoring_weight':fields.integer('Weight(kgs)'),
		'decoring_remarks': fields.text('Remarks'),
		'decoring_user_id': fields.many2one('res.users', 'Updated By', readonly=True),
		'decoring_accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'decoring_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'decoring_reject_date': fields.date('Rejection Date'),
		'decoring_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'decoring_state': fields.selection([('pending','Pending'),('complete','Completed')],'Decoring State', readonly=True),
		
		### Shot Blast ###
		'shot_blast_name': fields.char('Production Entry Code', size=128,select=True,readonly=True),
		'shot_blast_date': fields.date('Date'),
		'shot_blast_shift_id':fields.many2one('kg.shift.master','Shift'),
		'shot_blast_contractor':fields.many2one('res.partner','Contractor'),
		'shot_blast_employee': fields.char('Employee',size=128),
		'shot_blast_qty': fields.integer('Total Qty'),
		'shot_blast_accept_qty': fields.integer('Accepted Qty'),
		'shot_blast_reject_qty': fields.integer('Rejected Qty'),
		'shot_blast_weight':fields.integer('Weight(kgs)'),
		'shot_blast_remarks': fields.text('Remarks'),
		'shot_blast_user_id': fields.many2one('res.users', 'Updated By', readonly=True),
		'shot_blast_accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'shot_blast_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'shot_blast_reject_date': fields.date('Rejection Date'),
		'shot_blast_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'shot_blast_state': fields.selection([('pending','Pending'),('complete','Completed')],'Shot Blast State', readonly=True),
		
		### Hammering ###
		'hammering_name': fields.char('Production Entry Code', size=128,select=True,readonly=True),
		'hammering_date': fields.date('Date'),
		'hammering_shift_id':fields.many2one('kg.shift.master','Shift'),
		'hammering_contractor':fields.many2one('res.partner','Contractor'),
		'hammering_employee': fields.char('Employee',size=128),
		'hammering_qty': fields.integer('Total Qty'),
		'hammering_accept_qty': fields.integer('Accepted Qty'),
		'hammering_reject_qty': fields.integer('Rejected Qty'),
		'hammering_weight':fields.integer('Weight(kgs)'),
		'hammering_remarks': fields.text('Remarks'),
		'hammering_user_id': fields.many2one('res.users', 'Updated By', readonly=True),
		'hammering_accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'hammering_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'hammering_reject_date': fields.date('Rejection Date'),
		'hammering_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'hammering_state': fields.selection([('pending','Pending'),('complete','Completed')],'Hammering State', readonly=True),
		
		### Wheel Cutting ###
		'wheel_cutting_name': fields.char('Production Entry Code', size=128,select=True,readonly=True),
		'wheel_cutting_date': fields.date('Date'),
		'wheel_cutting_shift_id':fields.many2one('kg.shift.master','Shift'),
		'wheel_cutting_contractor':fields.many2one('res.partner','Contractor'),
		'wheel_cutting_employee': fields.char('Employee',size=128),
		'wheel_cutting_qty': fields.integer('Total Qty'),
		'wheel_cutting_accept_qty': fields.integer('Accepted Qty'),
		'wheel_cutting_reject_qty': fields.integer('Rejected Qty'),
		'wheel_cutting_weight':fields.integer('Weight(kgs)'),
		'wheel_cutting_remarks': fields.text('Remarks'),
		'wheel_cutting_user_id': fields.many2one('res.users', 'Updated By', readonly=True),
		'wheel_cutting_accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'wheel_cutting_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'wheel_cutting_reject_date': fields.date('Rejection Date'),
		'wheel_cutting_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'wheel_cutting_state': fields.selection([('pending','Pending'),('complete','Completed')],'Wheel Cutting State', readonly=True),
		
		### Gas Cutting ###
		'gas_cutting_name': fields.char('Production Entry Code', size=128,select=True,readonly=True),
		'gas_cutting_date': fields.date('Date'),
		'gas_cutting_shift_id':fields.many2one('kg.shift.master','Shift'),
		'gas_cutting_contractor':fields.many2one('res.partner','Contractor'),
		'gas_cutting_employee': fields.char('Employee',size=128),
		'gas_cutting_qty': fields.integer('Total Qty'),
		'gas_cutting_accept_qty': fields.integer('Accepted Qty'),
		'gas_cutting_reject_qty': fields.integer('Rejected Qty'),
		'gas_cutting_weight':fields.integer('Weight(kgs)'),
		'gas_cutting_remarks': fields.text('Remarks'),
		'gas_cutting_user_id': fields.many2one('res.users', 'Updated By', readonly=True),
		'gas_cutting_accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'gas_cutting_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'gas_cutting_reject_date': fields.date('Rejection Date'),
		'gas_cutting_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'gas_cutting_state': fields.selection([('pending','Pending'),('complete','Completed')],'Gas Cutting State', readonly=True),
		
		### ARC Cutting ###
		'arc_cutting_name': fields.char('Production Entry Code', size=128,select=True,readonly=True),
		'arc_cutting_date': fields.date('Date'),
		'arc_cutting_shift_id':fields.many2one('kg.shift.master','Shift'),
		'arc_cutting_contractor':fields.many2one('res.partner','Contractor'),
		'arc_cutting_employee': fields.char('Employee',size=128),
		'arc_cutting_qty': fields.integer('Total Qty'),
		'arc_cutting_accept_qty': fields.integer('Accepted Qty'),
		'arc_cutting_reject_qty': fields.integer('Rejected Qty'),
		'arc_cutting_weight':fields.integer('Weight(kgs)'),
		'arc_cutting_remarks': fields.text('Remarks'),
		'arc_cutting_user_id': fields.many2one('res.users', 'Updated By', readonly=True),
		'arc_cutting_accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'arc_cutting_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'arc_cutting_reject_date': fields.date('Rejection Date'),
		'arc_cutting_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'arc_cutting_state': fields.selection([('pending','Pending'),('complete','Completed')],'Arc Cutting State', readonly=True),
		
		### HEAT TREATMENT 1 ###
		'heat_cycle_no':fields.char('Heat Cycle No.', size=128,select=True),
		'heat_date': fields.date('Date'),
		'heat_specification':fields.char('Specification', size=128),
		'heat_fc_temp':fields.char('F/c initial temperature', size=128),
		'heat_fc_off_time': fields.float('F/c switch off at'),
		'heat_furnace_on_time': fields.float('Furnace switched on time'),
		'heat_treatment_type':fields.char('Treatment type', size=128),
		'heat_cooling_type':fields.char('Cooling type', size=128),
		'heat_set_temp':fields.char('Set temperature', size=128),
		'heat_set_temp_time':fields.float('Set temperature reached on (hrs.)'),
		'heat_socking_hr':fields.char('Socking hours(hrs.)', size=128),
		'heat_socking_comp_time':fields.float('Socking completed at(hrs.)'),
		'heat_quencing_time':fields.float('Quenching time(Sec.)'),
		'heat_quenc_time':fields.integer('Quenching time(Sec.)'),
		'heat_quencing_before_temp':fields.char('Quenching temp Before', size=128),
		'heat_quencing_after_temp':fields.char('Quenching temp After', size=128),
		'heat_chloride_content':fields.char('Chloride Content', size=128),
		'heat_total_qty': fields.integer('Total Qty'),
		'heat_qty':fields.integer('Qty'),
		'heat_reject_qty': fields.integer('Rejected Qty'),
		'heat_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'heat_each_weight':fields.integer('Each Weight'),
		'heat_total_weight':fields.integer('Total Weight'),
		'heat_remarks': fields.text('Remarks'),
		'heat_user_id': fields.many2one('res.users', 'Updated By', readonly=True),
		'heat_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'heat_contractor':fields.many2one('res.partner','Contractor'),
		'heat_employee': fields.char('Employee',size=128),
		'heat_state': fields.selection([('pending','Pending'),('complete','Completed')],'Heat State', readonly=True),
		
		### HEAT TREATMENT 2 ###
		'heat2_cycle_no':fields.char('Heat Cycle No.', size=128,select=True),
		'heat2_date': fields.date('Date'),
		'heat2_specification':fields.char('Specification', size=128),
		'heat2_fc_temp':fields.char('F/c initial temperature', size=128),
		'heat2_fc_off_time': fields.float('F/c switch off at'),
		'heat2_furnace_on_time': fields.float('Furnace switched on time'),
		'heat2_treatment_type':fields.char('Treatment type', size=128),
		'heat2_cooling_type':fields.char('Cooling type', size=128),
		'heat2_set_temp':fields.char('Set temperature', size=128),
		'heat2_set_temp_time':fields.float('Set temperature reached on (hrs.)'),
		'heat2_socking_hr':fields.char('Socking hours(hrs.)', size=128),
		'heat2_socking_comp_time':fields.float('Socking completed at(hrs.)'),
		'heat2_quencing_time':fields.float('Quenching time(Sec.)'),
		'heat2_quenc_time':fields.integer('Quenching time(Sec.)'),
		'heat2_quencing_before_temp':fields.char('Quenching temp Before', size=128),
		'heat2_quencing_after_temp':fields.char('Quenching temp After', size=128),
		'heat2_chloride_content':fields.char('Chloride Content', size=128),
		'heat2_total_qty': fields.integer('Total Qty'),
		'heat2_qty':fields.integer('Qty'),
		'heat2_reject_qty': fields.integer('Rejected Qty'),
		'heat2_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'heat2_each_weight':fields.integer('Each Weight'),
		'heat2_total_weight':fields.integer('Total Weight'),
		'heat2_remarks': fields.text('Remarks'),
		'heat2_user_id': fields.many2one('res.users', 'Updated By', readonly=True),
		'heat2_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'heat2_contractor':fields.many2one('res.partner','Contractor'),
		'heat2_employee': fields.char('Employee',size=128),
		'heat2_state': fields.selection([('pending','Pending'),('complete','Completed')],'Heat2 State', readonly=True),
		
		### HEAT TREATMENT 3 ###
		'heat3_cycle_no':fields.char('Heat Cycle No.', size=128,select=True),
		'heat3_date': fields.date('Date'),
		'heat3_specification':fields.char('Specification', size=128),
		'heat3_fc_temp':fields.char('F/c initial temperature', size=128),
		'heat3_fc_off_time': fields.float('F/c switch off at'),
		'heat3_furnace_on_time': fields.float('Furnace switched on time'),
		'heat3_treatment_type':fields.char('Treatment type', size=128),
		'heat3_cooling_type':fields.char('Cooling type', size=128),
		'heat3_set_temp':fields.char('Set temperature', size=128),
		'heat3_set_temp_time':fields.float('Set temperature reached on (hrs.)'),
		'heat3_socking_hr':fields.char('Socking hours(hrs.)', size=128),
		'heat3_socking_comp_time':fields.float('Socking completed at(hrs.)'),
		'heat3_quencing_time':fields.float('Quenching time(Sec.)'),
		'heat3_quenc_time':fields.integer('Quenching time(Sec.)'),
		'heat3_quencing_before_temp':fields.char('Quenching temp Before', size=128),
		'heat3_quencing_after_temp':fields.char('Quenching temp After', size=128),
		'heat3_chloride_content':fields.char('Chloride Content', size=128),
		'heat3_total_qty': fields.integer('Total Qty'),
		'heat3_qty':fields.integer('Qty'),
		'heat3_reject_qty': fields.integer('Rejected Qty'),
		'heat3_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'heat3_each_weight':fields.integer('Each Weight'),
		'heat3_total_weight':fields.integer('Total Weight'),
		'heat3_remarks': fields.text('Remarks'),
		'heat3_user_id': fields.many2one('res.users', 'Updated By', readonly=True),
		'heat3_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'heat3_contractor':fields.many2one('res.partner','Contractor'),
		'heat3_employee': fields.char('Employee',size=128),
		'heat3_state': fields.selection([('pending','Pending'),('complete','Completed')],'Heat3 State', readonly=True),
		
		
		### Rough Grinding ###
		'rough_grinding_name': fields.char('Production Entry Code', size=128,select=True,readonly=True),
		'rough_grinding_date': fields.date('Date'),
		'rough_grinding_shift_id':fields.many2one('kg.shift.master','Shift'),
		'rough_grinding_contractor':fields.many2one('res.partner','Contractor'),
		'rough_grinding_employee': fields.char('Employee',size=128),
		'rough_grinding_qty': fields.integer('Total Qty'),
		'rough_grinding_accept_qty': fields.integer('Accepted Qty'),
		'rough_grinding_reject_qty': fields.integer('Rejected Qty'),
		'rough_grinding_rework_qty': fields.integer('Re-work Qty'),
		'rough_grinding_weight':fields.integer('Weight(kgs)'),
		'rough_grinding_remarks': fields.text('Remarks'),
		'rough_grinding_user_id': fields.many2one('res.users', 'Updated By', readonly=True),
		'rough_grinding_accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'rough_grinding_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'rough_grinding_reject_date': fields.date('Rejection Date'),
		'rough_grinding_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'rough_grinding_state': fields.selection([('pending','Pending'),('complete','Completed')],'Rough Grinding State', readonly=True),
		
		### Welding ###
		'welding_name': fields.char('Production Entry Code', size=128,select=True,readonly=True),
		'welding_date': fields.date('Date'),
		'welding_shift_id':fields.many2one('kg.shift.master','Shift'),
		'welding_contractor':fields.many2one('res.partner','Contractor'),
		'welding_employee': fields.char('Employee',size=128),
		'welding_qty': fields.integer('Total Qty'),
		'welding_accept_qty': fields.integer('Accepted Qty'),
		'welding_reject_qty': fields.integer('Rejected Qty'),
		'welding_weight':fields.integer('Weight(kgs)'),
		'welding_remarks': fields.text('Remarks'),
		'welding_user_id': fields.many2one('res.users', 'Updated By', readonly=True),
		'welding_accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'welding_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'welding_reject_date': fields.date('Rejection Date'),
		'welding_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'welding_stage_id':fields.many2one('kg.stage.master','Stage'),
		'welding_stage_name': fields.related('welding_stage_id','name', type='char', size=128, string='Stage Name', store=True, readonly=True),
		'welding_state': fields.selection([('progress','Progress'),('done','Done')],'Welding Status'),
		
		
		### Finish Grinding ###
		'finish_grinding_name': fields.char('Production Entry Code', size=128,select=True),
		'finish_grinding_date': fields.date('Date'),
		'finish_grinding_shift_id':fields.many2one('kg.shift.master','Shift'),
		'finish_grinding_contractor':fields.many2one('res.partner','Contractor'),
		'finish_grinding_employee': fields.char('Employee',size=128),
		'finish_grinding_qty': fields.integer('Total Qty'),
		'finish_grinding_accept_qty': fields.integer('Accepted Qty'),
		'finish_grinding_reject_qty': fields.integer('Rejected Qty'),
		'finish_grinding_weight':fields.integer('Weight(kgs)'),
		'finish_grinding_remarks': fields.text('Remarks'),
		'finish_grinding_user_id': fields.many2one('res.users', 'Updated By', readonly=True),
		'finish_grinding_accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'finish_grinding_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'finish_grinding_reject_date': fields.date('Rejection Date'),
		'finish_grinding_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'flag_reshot_blast_applicable': fields.boolean('Re-Shot Blasting Applicable'),
		'flag_fg_special_app': fields.boolean('Special Approval'),
		'finish_grinding_state': fields.selection([('pending','Pending'),('complete','Completed')],'Finish Grinding State', readonly=True),
		
		### Re shot Blasting ###
		'reshot_blasting_name': fields.char('Production Entry Code', size=128,select=True),
		'reshot_blasting_date': fields.date('Date'),
		'reshot_blasting_shift_id':fields.many2one('kg.shift.master','Shift'),
		'reshot_blasting_contractor':fields.many2one('res.partner','Contractor'),
		'reshot_blasting_employee': fields.char('Employee',size=128),
		'reshot_blasting_qty': fields.integer('Total Qty'),
		'reshot_blasting_accept_qty': fields.integer('Accepted Qty'),
		'reshot_blasting_reject_qty': fields.integer('Rejected Qty'),
		'reshot_blasting_weight':fields.integer('Weight(kgs)'),
		'reshot_blasting_remarks': fields.text('Remarks'),
		'reshot_blasting_user_id': fields.many2one('res.users', 'Updated By', readonly=True),
		'reshot_blasting_accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'reshot_blasting_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'reshot_blasting_reject_date': fields.date('Rejection Date'),
		'reshot_blasting_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'reshot_blasting_state': fields.selection([('pending','Pending'),('complete','Completed')],'Reshot Blasting State', readonly=True),
		
		### Stock Allocation ###
		'allocated_qty': fields.integer('Allocated Qty'),
		'allocated_accepted_qty': fields.integer('Accepted Qty'),
		'flag_allocated': fields.boolean('Allocated from Stock'),
		'allocation_state': fields.selection([('waiting','Waiting'),('accept','Accepted'),('reject','Rejected')],'Allocation Status'),
		'allocation_user_id': fields.many2one('res.users', 'Accepted By'), 
		'allocation_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		
		'ms_state': fields.selection([('created','Created'),('not_created','Not Created')],'MS Status'),
		
	
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
				
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_fettling', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'division_id':_get_default_division,
		'state':'waiting',
		### Fettling Inward ###
		'inward_accept_user_id':lambda obj, cr, uid, context: uid,
		### Knock Out ###
		'knockout_user_id':lambda obj, cr, uid, context: uid,
		'knockout_date':lambda * a: time.strftime('%Y-%m-%d'),
		'knockout_accept_user_id':lambda obj, cr, uid, context: uid,
		'knockout_state':'pending',
		### DECORING ###
		'decoring_user_id':lambda obj, cr, uid, context: uid,
		'decoring_date':lambda * a: time.strftime('%Y-%m-%d'),
		'decoring_accept_user_id':lambda obj, cr, uid, context: uid,
		'decoring_state':'pending',
		### Shot Blast ###
		'shot_blast_user_id':lambda obj, cr, uid, context: uid,
		'shot_blast_date':lambda * a: time.strftime('%Y-%m-%d'),
		'shot_blast_accept_user_id':lambda obj, cr, uid, context: uid,
		'shot_blast_state':'pending',
		### Hammering ###
		'hammering_user_id':lambda obj, cr, uid, context: uid,
		'hammering_date':lambda * a: time.strftime('%Y-%m-%d'),
		'hammering_accept_user_id':lambda obj, cr, uid, context: uid,
		'hammering_state':'pending',
		### Wheel Cutting ###
		'wheel_cutting_user_id':lambda obj, cr, uid, context: uid,
		'wheel_cutting_date':lambda * a: time.strftime('%Y-%m-%d'),
		'wheel_cutting_accept_user_id':lambda obj, cr, uid, context: uid,
		'wheel_cutting_state':'pending',
		### Gas Cutting ###
		'gas_cutting_user_id':lambda obj, cr, uid, context: uid,
		'gas_cutting_date':lambda * a: time.strftime('%Y-%m-%d'),
		'gas_cutting_accept_user_id':lambda obj, cr, uid, context: uid,
		'gas_cutting_state':'pending',
		### ARC Cutting ###
		'arc_cutting_user_id':lambda obj, cr, uid, context: uid,
		'arc_cutting_date':lambda * a: time.strftime('%Y-%m-%d'),
		'arc_cutting_accept_user_id':lambda obj, cr, uid, context: uid,
		'arc_cutting_state':'pending',
		### HEAT TREATMENT 1###
		'heat_user_id':lambda obj, cr, uid, context: uid,
		'heat_date':lambda * a: time.strftime('%Y-%m-%d'),
		'heat_state':'pending',
		### HEAT TREATMENT 2 ###
		'heat2_user_id':lambda obj, cr, uid, context: uid,
		'heat2_date':lambda * a: time.strftime('%Y-%m-%d'),
		'heat2_state':'pending',
		### HEAT TREATMENT 3 ###
		'heat3_user_id':lambda obj, cr, uid, context: uid,
		'heat3_date':lambda * a: time.strftime('%Y-%m-%d'),
		'heat3_state':'pending',
		### Rough Grinding ###
		'rough_grinding_user_id':lambda obj, cr, uid, context: uid,
		'rough_grinding_date':lambda * a: time.strftime('%Y-%m-%d'),
		'rough_grinding_accept_user_id':lambda obj, cr, uid, context: uid,
		'rough_grinding_state':'pending',
		### Finish Grinding ###
		'finish_grinding_user_id':lambda obj, cr, uid, context: uid,
		'finish_grinding_date':lambda * a: time.strftime('%Y-%m-%d'),
		'finish_grinding_accept_user_id':lambda obj, cr, uid, context: uid,
		'finish_grinding_state':'pending',
		### Re Shot Blasting ###
		'reshot_blasting_user_id':lambda obj, cr, uid, context: uid,
		'reshot_blasting_date':lambda * a: time.strftime('%Y-%m-%d'),
		'reshot_blasting_accept_user_id':lambda obj, cr, uid, context: uid,
		'reshot_blasting_state':'pending',
		### Welding ###
		'welding_user_id':lambda obj, cr, uid, context: uid,
		'welding_date':lambda * a: time.strftime('%Y-%m-%d'),
		'welding_accept_user_id':lambda obj, cr, uid, context: uid,
		### Stock Allocation ###
		'flag_allocated': False,
		'allocation_user_id':lambda obj, cr, uid, context: uid,
		'ms_state': 'not_created'
		
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.entry_date)
		if entry_date > today:
			return False
		knockout_date = str(rec.knockout_date)
		if knockout_date > today:
			return False
		decoring_date = str(rec.decoring_date)
		if decoring_date > today:
			return False
		shot_blast_date = str(rec.shot_blast_date)
		if shot_blast_date > today:
			return False
		hammering_date = str(rec.hammering_date)
		if hammering_date > today:
			return False
		wheel_cutting_date = str(rec.wheel_cutting_date)
		if wheel_cutting_date > today:
			return False
		gas_cutting_date = str(rec.gas_cutting_date)
		if gas_cutting_date > today:
			return False
		arc_cutting_date = str(rec.arc_cutting_date)
		if arc_cutting_date > today:
			return False
		heat_date = str(rec.heat_date)
		if heat_date > today:
			return False
		rough_grinding_date = str(rec.rough_grinding_date)
		if rough_grinding_date > today:
			return False
		welding_date = str(rec.welding_date)
		if welding_date > today:
			return False
		finish_grinding_date = str(rec.finish_grinding_date)
		if finish_grinding_date > today:
			return False
		reshot_blasting_date = str(rec.reshot_blasting_date)
		if reshot_blasting_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		#~ (_future_entry_date_check, 'System not allow to save with future date. !!',['']),
  
	   ]
	
	
	def ms_inward_update(self,cr,uid,ids,inward_qty,ms_state,context=None):
		ms_obj = self.pool.get('kg.machineshop')
		entry_rec = self.browse(cr, uid, ids[0])
		if entry_rec.ms_state != 'created':
			### Sequence Number Generation ###
			ms_name = ''	
			ms_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.ms.inward')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,ms_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(ms_seq_id[0],seq_rec.code))
			ms_name = cr.fetchone();
			
			ms_vals = {
			'name': ms_name[0],
			'location':entry_rec.location,
			'schedule_id':entry_rec.schedule_id.id,
			'schedule_date':entry_rec.schedule_date,
			'schedule_line_id':entry_rec.schedule_line_id.id,
			'order_bomline_id':entry_rec.order_bomline_id.id,
			'order_id':entry_rec.order_id.id,
			'order_line_id':entry_rec.order_line_id.id,
			'order_no':entry_rec.order_no,
			'order_delivery_date':entry_rec.order_delivery_date,
			'order_date':entry_rec.order_date,
			'order_category':entry_rec.order_category,
			'order_priority':entry_rec.order_priority,
			'pump_model_id':entry_rec.pump_model_id.id,
			'pattern_id':entry_rec.pattern_id.id,
			'pattern_code':entry_rec.pattern_code,
			'pattern_name':entry_rec.pattern_name,
			'moc_id':entry_rec.moc_id.id,
			'schedule_qty':entry_rec.schedule_qty,
			'fettling_id':entry_rec.id,
			'fettling_qty':inward_qty,
			'inward_accept_qty':inward_qty,
			'state':'waiting',
			'ms_sch_qty': inward_qty,
			'ms_type': 'foundry_item',
			'item_code': entry_rec.pattern_code,
			'item_name': entry_rec.pattern_name,
			'position_id': entry_rec.order_bomline_id.position_id.id,
			
			}
			
			if entry_rec.state != 'complete':
				
				ms_id = ms_obj.create(cr, uid, ms_vals)
			
				### Status Updation ###
				if entry_rec.production_id.id != False:
					### Schedule List Updation ###
					production_obj = self.pool.get('kg.production')
					cr.execute(''' update kg_production set state = 'moved_to_ms' where id = %s ''',[entry_rec.production_id.id])
				self.write(cr, uid, ids, {'ms_state': 'created'})
			
		### Fettling Status Updation ###
		if ms_state == 'not_created':
			self.write(cr, uid, ids, {'state': 'complete'})
		
		
		return True
		
	
	def fettling_accept(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.pour_qty - entry.inward_accept_qty
		
		if entry.state == 'waiting':
			if entry.inward_accept_qty < 0 or entry.inward_reject_qty < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
							
			if entry.inward_accept_qty == 0 and entry.inward_reject_qty == 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
							
			if (entry.inward_accept_qty + entry.inward_reject_qty) > entry.pour_qty:
				raise osv.except_osv(_('Warning!'),
							_('Accept and Reject qty should not exceed Pour Qty !!'))
							
			if (entry.inward_accept_qty + entry.inward_reject_qty) < entry.pour_qty:
				raise osv.except_osv(_('Warning!'),
							_('Accept and Reject qty should be equal to Pour Qty !!'))
							
			if reject_qty > 0:
				if entry.inward_reject_qty == 0:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Enter Rejection Qty !!'))
				if entry.inward_reject_qty < reject_qty:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Check Rejection Qty !!'))
					
						
			if entry.inward_reject_qty > 0 and not entry.inward_reject_remarks_id:
				raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
					
			if entry.inward_reject_qty > reject_qty:
				raise osv.except_osv(_('Warning!'),
					_('Kindly check the rejection Qty !!'))
					
			entry_date = entry.entry_date
			entry_date = str(entry_date)
			entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
			
			if entry_date > today:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to save with future date !!'))
			
			if entry.inward_accept_qty > 0:
				cr.execute(""" select fettling.stage_id,stage.name as stage_name,fettling.seq_no,fettling.flag_ms from ch_fettling_process as fettling
					left join kg_moc_master moc on fettling.header_id = moc.id
					left join kg_stage_master stage on fettling.stage_id = stage.id
					where moc.id = %s and moc.state = 'approved' and moc.active = 't'
					order by fettling.seq_no asc limit 1 """%(entry.moc_id.id))
				fettling_stage_id = cr.dictfetchall();
				
				if fettling_stage_id:
				
					for stage_item in fettling_stage_id:
						if stage_item['stage_name'] == 'KNOCK OUT':
							knockout_qty = entry.inward_accept_qty
							### Sequence Number Generation ###
							knockout_name = ''  
							knockout_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.knock.out')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,knockout_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(knockout_seq_id[0],seq_rec.code))
							knockout_name = cr.fetchone();
							self.write(cr, uid, ids, {'knockout_date':time.strftime('%Y-%m-%d'),'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0]})
						if stage_item['stage_name'] == 'DECORING':
							decoring_qty = entry.inward_accept_qty
							### Sequence Number Generation ###
							decoring_name = ''  
							decoring_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.decoring')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,decoring_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(decoring_seq_id[0],seq_rec.code))
							decoring_name = cr.fetchone();
							self.write(cr, uid, ids, {'decoring_date':time.strftime('%Y-%m-%d'),'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0]})
						if stage_item['stage_name'] == 'SHOT BLAST':
							shot_blast_qty = entry.inward_accept_qty
							### Sequence Number Generation ###
							shot_blast_name = ''	
							shot_blast_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.shot.blast')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,shot_blast_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(shot_blast_seq_id[0],seq_rec.code))
							shot_blast_name = cr.fetchone();
							self.write(cr, uid, ids, {'shot_blast_date':time.strftime('%Y-%m-%d'),'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0]})
						if stage_item['stage_name'] == 'HAMMERING':
							hammering_qty = entry.inward_accept_qty
							### Sequence Number Generation ###
							hammering_name = '' 
							hammering_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.hammering')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,hammering_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(hammering_seq_id[0],seq_rec.code))
							hammering_name = cr.fetchone();
							self.write(cr, uid, ids, {'hammering_date':time.strftime('%Y-%m-%d'),'hammering_date':time.strftime('%Y-%m-%d'),'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0]})
						if stage_item['stage_name'] == 'WHEEL CUTTING':
							wheel_cutting_qty = entry.inward_accept_qty
							### Sequence Number Generation ###
							wheel_cutting_name = '' 
							wheel_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.wheel.cutting')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,wheel_cutting_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(wheel_cutting_seq_id[0],seq_rec.code))
							wheel_cutting_name = cr.fetchone();
							self.write(cr, uid, ids, {'wheel_cutting_date':time.strftime('%Y-%m-%d'),'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0]})
						if stage_item['stage_name'] == 'GAS CUTTING':
							gas_cutting_qty = entry.inward_accept_qty
							### Sequence Number Generation ###
							gas_cutting_name = ''   
							gas_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.gas.cutting')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,gas_cutting_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(gas_cutting_seq_id[0],seq_rec.code))
							gas_cutting_name = cr.fetchone();
							self.write(cr, uid, ids, {'gas_cutting_date':time.strftime('%Y-%m-%d'),'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0]})
						if stage_item['stage_name'] == 'ARC CUTTING':
							arc_cutting_qty = entry.inward_accept_qty
							### Sequence Number Generation ###
							arc_cutting_name = ''   
							arc_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.arc.cutting')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,arc_cutting_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(arc_cutting_seq_id[0],seq_rec.code))
							arc_cutting_name = cr.fetchone();
							self.write(cr, uid, ids, {'arc_cutting_date':time.strftime('%Y-%m-%d'),'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0]})
						if stage_item['stage_name'] == 'HEAT TREATMENT':
							heat_total_qty = entry.inward_accept_qty
							self.write(cr, uid, ids, {'heat_date':time.strftime('%Y-%m-%d'),'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty})
						if stage_item['stage_name'] == 'HEAT TREATMENT2':
							heat2_total_qty = entry.inward_accept_qty
							self.write(cr, uid, ids, {'heat2_date':time.strftime('%Y-%m-%d'),'heat2_total_qty': heat2_total_qty,'heat2_qty':heat2_total_qty})
						if stage_item['stage_name'] == 'HEAT TREATMENT3':
							heat3_total_qty = entry.inward_accept_qty
							self.write(cr, uid, ids, {'heat3_date':time.strftime('%Y-%m-%d'),'heat3_total_qty': heat3_total_qty,'heat3_qty':heat3_total_qty})
							
							if entry.order_id.flag_for_stock == False:
								if stage_item['flag_ms'] == True: 
									self.ms_inward_update(cr, uid, [entry.id],entry.inward_accept_qty,'created')
							
						if stage_item['stage_name'] == 'ROUGH GRINDING':
							rough_grinding_qty = entry.inward_accept_qty
							### Sequence Number Generation ###
							rough_grinding_name = ''	
							rough_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.rough.grinding')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,rough_grinding_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(rough_grinding_seq_id[0],seq_rec.code))
							rough_grinding_name = cr.fetchone();
							self.write(cr, uid, ids, {'rough_grinding_date':time.strftime('%Y-%m-%d'),'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,'rough_grinding_name':rough_grinding_name[0]})
						if stage_item['stage_name'] == 'FINISH GRINDING':
							finish_grinding_qty = entry.inward_accept_qty
							### Sequence Number Generation ###
							finish_grinding_name = ''   
							finish_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.finish.grinding')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,finish_grinding_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(finish_grinding_seq_id[0],seq_rec.code))
							finish_grinding_name = cr.fetchone();
							self.write(cr, uid, ids, {'finish_grinding_date':time.strftime('%Y-%m-%d'),'finish_grinding_qty': finish_grinding_qty,'finish_grinding_accept_qty': finish_grinding_qty,'finish_grinding_name':finish_grinding_name[0]})
							
						if stage_item['stage_name'] == 'RE SHOT BLASTING':
							### Next Stage Qty ###
							reshot_blasting_qty = entry.reshot_blasting_accept_qty
							### Sequence Number Generation ###
							reshot_blasting_name = ''   
							reshot_blasting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.reshot.blasting')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,reshot_blasting_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(reshot_blasting_seq_id[0],seq_rec.code))
							reshot_blasting_name = cr.fetchone();
							self.write(cr, uid, ids, {'reshot_blasting_date':time.strftime('%Y-%m-%d'),'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0]})
							
						self.write(cr, uid, ids, {'stage_id': stage_item['stage_id']})
				else:
					### MS Inward Process Creation ###
					if entry.stage_id.id == False:
						raise osv.except_osv(_('Warning!'),
						_('Kindly configure Stages in MOC %s !!')%(entry.moc_id.name))
					else:
						if entry.order_id.flag_for_stock == False:
							self.ms_inward_update(cr, uid, [entry.id],entry.inward_accept_qty,'not_created')
						else:
							### Stock Inward Creation ###
							inward_obj = self.pool.get('kg.stock.inward')
							inward_line_obj = self.pool.get('ch.stock.inward.details')
							
							inward_vals = {
								'location': entry.location
							}
							
							inward_id = inward_obj.create(cr, uid, inward_vals)
							
							inward_line_vals = {
								'header_id': inward_id,
								'location': entry.location,
								'stock_type': 'pattern',
								'pump_model_id': entry.pump_model_id.id,
								'pattern_id': entry.pattern_id.id,
								'pattern_name': entry.pattern_name,
								'moc_id': entry.moc_id.id,
								'stage_id': entry.stage_id.id,
								'qty': rem_qty,
								'available_qty': rem_qty,
								'each_wgt': entry.production_id.each_weight,
								'total_weight': entry.production_id.total_weight,
								'stock_mode': 'excess',
								'stock_state': 'ready_for_ms'
							}
							
							inward_line_id = inward_line_obj.create(cr, uid, inward_line_vals)
							
							self.write(cr,uid, ids,{'state':'complete'})
						
			if entry.inward_reject_qty > 0:
				
				if entry.order_id.flag_for_stock == False:
				
					reject_rem_qty = entry.inward_reject_qty
					
					### Checking in Stock Inward for Ready for MS ###
					
					cr.execute(""" select sum(available_qty) as stock_qty
						from ch_stock_inward_details  
						where pattern_id = %s and moc_id = %s
						and foundry_stock_state = 'ready_for_ms' and available_qty > 0 and stock_type = 'pattern'  """%(entry.pattern_id.id,entry.moc_id.id))
					stock_inward_qty = cr.fetchone();
					
					
					if stock_inward_qty:
						if stock_inward_qty[0] != None:
							reject_rem_qty =  entry.inward_reject_qty - stock_inward_qty[0]
							
							if reject_rem_qty <= 0:
								reject_rem_qty = 0
								qc_qty = entry.inward_reject_qty
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
								and  foundry_stock_state = 'ready_for_ms' 
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
						and  foundry_stock_state = 'foundry_inprogress' and available_qty > 0 and stock_type = 'pattern'  """%(entry.pattern_id.id,entry.moc_id.id))
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
										'schedule_qty':entry.schedule_qty,
										'production_id':entry.production_id.id,
										'pour_qty':rem_qty,
										'inward_accept_qty': rem_qty,
										'state':'waiting',
										'pour_id': entry.pour_id.id,
										'pour_line_id': entry.pour_line_id.id,
										
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':knockout_qty,'inward_accept_qty': knockout_qty,
										'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'knockout_date':time.strftime('%Y-%m-%d'),'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0]
										,'allocated_qty':knockout_qty,'flag_allocated':'t','allocated_accepted_qty':knockout_qty,'allocation_state':'waiting'})
										
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':decoring_qty,'inward_accept_qty': decoring_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'decoring_date':time.strftime('%Y-%m-%d'),'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0],'allocated_qty':decoring_qty,'flag_allocated':'t','allocated_accepted_qty':decoring_qty,'allocation_state':'waiting'})
										
										
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':shot_blast_qty,'inward_accept_qty': shot_blast_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'shot_blast_date':time.strftime('%Y-%m-%d'),'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0],'allocated_qty':shot_blast_qty,'flag_allocated':'t','allocated_accepted_qty':shot_blast_qty,'allocation_state':'waiting'})
										
									
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':hammering_qty,'inward_accept_qty': hammering_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'hammering_date':time.strftime('%Y-%m-%d'),'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0],'allocated_qty':hammering_qty,'flag_allocated':'t','allocated_accepted_qty':hammering_qty,'allocation_state':'waiting'})
										
									
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':wheel_cutting_qty,'inward_accept_qty': wheel_cutting_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'wheel_cutting_date':time.strftime('%Y-%m-%d'),'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0],'allocated_qty':wheel_cutting_qty,'flag_allocated':'t','allocated_accepted_qty':wheel_cutting_qty,'allocation_state':'waiting'})
									
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':gas_cutting_qty,'inward_accept_qty': gas_cutting_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'gas_cutting_date':time.strftime('%Y-%m-%d'),'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0],'allocated_qty':gas_cutting_qty,'flag_allocated':'t','allocated_accepted_qty':gas_cutting_qty,'allocation_state':'waiting'})
									
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':arc_cutting_qty,'inward_accept_qty': arc_cutting_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'arc_cutting_date':time.strftime('%Y-%m-%d'),'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0],'allocated_qty':arc_cutting_qty,'flag_allocated':'t','allocated_accepted_qty':arc_cutting_qty,'allocation_state':'waiting'})
									
										### Updation in STK WO ###
										stk_rem_qty =  stk_arc_cutting_qty - arc_cutting_qty
										if stk_rem_qty > 0:
											self.write(cr, uid, stk_item['id'], {'arc_cutting_qty': stk_rem_qty,'arc_cutting_accept_qty':stk_rem_qty})
										else:
											self.write(cr, uid, stk_item['id'], {'state':'complete'})
											
										allocated_qty = arc_cutting_qty
									
									
									if stk_item['stage_name'] == 'HEAT TREATMENT':
										
										stk_heat_qty = stk_item_rec.heat_qty
										
										if rem_qty <= stk_heat_qty:
											heat_total_qty = rem_qty
										if rem_qty > stk_heat_qty:
											heat_total_qty = stk_heat_qty
										
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':heat_total_qty,'inward_accept_qty': heat_total_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'heat_date':time.strftime('%Y-%m-%d'),'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty,'allocated_qty':heat_total_qty,'flag_allocated':'t','allocated_accepted_qty':heat_total_qty,'allocation_state':'waiting'})
									
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':rough_grinding_qty,'inward_accept_qty': rough_grinding_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'rough_grinding_date':time.strftime('%Y-%m-%d'),'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,'rough_grinding_name':rough_grinding_name[0],'allocated_qty':rough_grinding_qty,'flag_allocated':'t','allocated_accepted_qty':rough_grinding_qty,'allocation_state':'waiting'})
									
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':finish_grinding_qty,'inward_accept_qty': finish_grinding_qty,'pour_qty':finish_grinding_qty,'inward_accept_qty': finish_grinding_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'finish_grinding_date':time.strftime('%Y-%m-%d'),'finish_grinding_qty': finish_grinding_qty,'finish_grinding_accept_qty': finish_grinding_qty,'finish_grinding_name':finish_grinding_name[0]})
										
										### Updation in STK WO ###
										stk_rem_qty =  stk_finish_grinding_qty - finish_grinding_qty
										if stk_rem_qty > 0:
											self.write(cr, uid, stk_item['id'], {'finish_grinding_qty': stk_rem_qty,'finish_grinding_accept_qty':stk_rem_qty})
										else:
											self.write(cr, uid, stk_item['id'], {'state':'complete'})
											
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':reshot_blasting_qty,'inward_accept_qty': reshot_blasting_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'reshot_blasting_date':time.strftime('%Y-%m-%d'),'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0],'allocated_qty':reshot_blasting_qty,'flag_allocated':'t','allocated_accepted_qty':reshot_blasting_qty,'allocation_state':'waiting'})
								
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
						
							production_obj.write(cr, uid, entry.production_id.id, {'fettling_reject_qty': entry.production_id.fettling_reject_qty + rem_qty})
							
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
									'qty' : entry.inward_reject_qty,			  
									'schedule_qty' : entry.inward_reject_qty,		   
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
							
						
				else:
					
					### Qty Updation in Stock Inward ###
							
					inward_line_obj = self.pool.get('ch.stock.inward.details')
					
					cr.execute(""" select id,available_qty
						from ch_stock_inward_details  
						where pattern_id = %s and moc_id = %s
						and  foundry_stock_state = 'foundry_inprogress'
						and available_qty > 0 and stock_type = 'pattern' """%(entry.pattern_id.id,entry.moc_id.id))
						
					stock_inward_items = cr.dictfetchall();
					stock_updation_qty = entry.inward_reject_qty
					
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
												
						
					
			if entry.inward_reject_qty > 0:
				
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
					'stage_name': 'Fettling Inward',
					'qty': entry.inward_reject_qty,
					'reject_remarks_id': entry.inward_reject_remarks_id.id
				}
				
				foundry_rejection_id = foundry_rejection_obj.create(cr, uid, rejection_vals)
				
			
			self.write(cr, uid, ids, {'pre_stage_date':entry.entry_date,'state': 'accept','update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def fettling_accept_process(self,cr,uid,ids,fettling_qty,fettling_accept_qty,fettling_weight,fettling_date,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		
		if fettling_accept_qty > 0:
			cr.execute(""" select fettling.stage_id,stage.name as stage_name,fettling.seq_no,fettling.flag_ms from ch_fettling_process as fettling
				left join kg_moc_master moc on fettling.header_id = moc.id
				left join kg_stage_master stage on fettling.stage_id = stage.id
				where moc.id = %s and moc.state = 'approved' and moc.active = 't' and fettling.seq_no >
				(
				select fettling.seq_no from ch_fettling_process as fettling
				left join kg_moc_master moc on fettling.header_id = moc.id
				where moc.id = %s and moc.state = 'approved' and active = 't'and fettling.stage_id = %s
				)
				 
				order by fettling.seq_no asc limit 1 
				 """%(entry.moc_id.id,entry.moc_id.id,entry.stage_id.id))
			fettling_stage_id = cr.dictfetchall();
			
			if fettling_stage_id:
			
				for stage_item in fettling_stage_id:
					
					if stage_item['stage_name'] == 'KNOCK OUT':
						### Next Stage Qty ###
						knockout_qty = fettling_accept_qty
						### Sequence Number Generation ###
						knockout_name = ''  
						knockout_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.knock.out')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,knockout_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(knockout_seq_id[0],seq_rec.code))
						knockout_name = cr.fetchone();
						self.write(cr, uid, ids, {'knockout_date':time.strftime('%Y-%m-%d'),'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0]})
					
					if stage_item['stage_name'] == 'DECORING':
						### Next Stage Qty ###
						decoring_qty = fettling_accept_qty
						### Sequence Number Generation ###
						decoring_name = ''  
						decoring_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.decoring')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,decoring_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(decoring_seq_id[0],seq_rec.code))
						decoring_name = cr.fetchone();
						self.write(cr, uid, ids, {'decoring_date':time.strftime('%Y-%m-%d'),'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0]})
					
					if stage_item['stage_name'] == 'SHOT BLAST':
						### Next Stage Qty ###
						shot_blast_qty = fettling_accept_qty
						### Sequence Number Generation ###
						shot_blast_name = ''	
						shot_blast_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.shot.blast')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,shot_blast_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(shot_blast_seq_id[0],seq_rec.code))
						shot_blast_name = cr.fetchone();
						self.write(cr, uid, ids, {'shot_blast_date':time.strftime('%Y-%m-%d'),'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0]})
					
					if stage_item['stage_name'] == 'HAMMERING':
						### Next Stage Qty ###
						hammering_qty = fettling_accept_qty
						### Sequence Number Generation ###
						hammering_name = '' 
						hammering_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.hammering')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,hammering_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(hammering_seq_id[0],seq_rec.code))
						hammering_name = cr.fetchone();
						self.write(cr, uid, ids, {'hammering_date':time.strftime('%Y-%m-%d'),'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0]})
					
					if stage_item['stage_name'] == 'WHEEL CUTTING':
						### Next Stage Qty ###
						wheel_cutting_qty = fettling_accept_qty
						### Sequence Number Generation ###
						wheel_cutting_name = '' 
						wheel_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.wheel.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,wheel_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(wheel_cutting_seq_id[0],seq_rec.code))
						wheel_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'wheel_cutting_date':time.strftime('%Y-%m-%d'),'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0]})
					
					if stage_item['stage_name'] == 'GAS CUTTING':
						### Next Stage Qty ###
						gas_cutting_qty = fettling_accept_qty
						### Sequence Number Generation ###
						gas_cutting_name = ''   
						gas_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.gas.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,gas_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(gas_cutting_seq_id[0],seq_rec.code))
						gas_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'gas_cutting_date':time.strftime('%Y-%m-%d'),'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0]})
					
					if stage_item['stage_name'] == 'ARC CUTTING':
						### Next Stage Qty ###
						arc_cutting_qty = fettling_accept_qty
						### Sequence Number Generation ###
						arc_cutting_name = ''   
						arc_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.arc.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,arc_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(arc_cutting_seq_id[0],seq_rec.code))
						arc_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'arc_cutting_date':time.strftime('%Y-%m-%d'),'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0]})
					
					if stage_item['stage_name'] == 'HEAT TREATMENT':
						### Next Stage Qty ###
						heat_total_qty = fettling_accept_qty
						self.write(cr, uid, ids, {'heat_date':time.strftime('%Y-%m-%d'),'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty})
					if stage_item['stage_name'] == 'HEAT TREATMENT2':
						heat2_total_qty = fettling_accept_qty
						self.write(cr, uid, ids, {'heat2_date':time.strftime('%Y-%m-%d'),'heat2_total_qty': heat2_total_qty,'heat2_qty':heat2_total_qty})
					if stage_item['stage_name'] == 'HEAT TREATMENT3':
						heat3_total_qty = fettling_accept_qty
						self.write(cr, uid, ids, {'heat3_date':time.strftime('%Y-%m-%d'),'heat3_total_qty': heat3_total_qty,'heat3_qty':heat3_total_qty})
						if entry.order_id.flag_for_stock == False:
							if stage_item['flag_ms'] == True: 
								self.ms_inward_update(cr, uid, [entry.id],fettling_accept_qty,'created')
	
					if stage_item['stage_name'] == 'ROUGH GRINDING':
						### Next Stage Qty ###
						rough_grinding_qty = fettling_accept_qty
						### Sequence Number Generation ###
						rough_grinding_name = ''	
						rough_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.rough.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,rough_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(rough_grinding_seq_id[0],seq_rec.code))
						rough_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'rough_grinding_date':time.strftime('%Y-%m-%d'),'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,'rough_grinding_name':rough_grinding_name[0]})
					
					if stage_item['stage_name'] == 'FINISH GRINDING':
						### Next Stage Qty ###
						finish_grinding_qty = fettling_accept_qty
						### Sequence Number Generation ###
						finish_grinding_name = ''   
						finish_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.finish.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,finish_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(finish_grinding_seq_id[0],seq_rec.code))
						finish_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'finish_grinding_date':time.strftime('%Y-%m-%d'),'finish_grinding_qty': finish_grinding_qty,'finish_grinding_accept_qty': finish_grinding_qty,'finish_grinding_name':finish_grinding_name[0]})
						
					if stage_item['stage_name'] == 'RE SHOT BLASTING':
						### Next Stage Qty ###
						reshot_blasting_qty = fettling_accept_qty
						### Sequence Number Generation ###
						reshot_blasting_name = ''   
						reshot_blasting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.reshot.blasting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,reshot_blasting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(reshot_blasting_seq_id[0],seq_rec.code))
						reshot_blasting_name = cr.fetchone();
						self.write(cr, uid, ids, {'reshot_blasting_date':time.strftime('%Y-%m-%d'),'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0]})
					
					
					self.write(cr, uid, ids, {'pre_stage_date': fettling_date,'stage_id': stage_item['stage_id']})
					
			else:
				### MS Inward Process Creation ###
				if entry.order_id.flag_for_stock == False:
					self.ms_inward_update(cr, uid, [entry.id],fettling_accept_qty,'not_created')
				else:
					### Stock Inward Creation ###
					inward_obj = self.pool.get('kg.stock.inward')
					inward_line_obj = self.pool.get('ch.stock.inward.details')
					
					inward_vals = {
						'location': entry.location
					}
					
					inward_id = inward_obj.create(cr, uid, inward_vals)
					
					inward_line_vals = {
						'header_id': inward_id,
						'location': entry.location,
						'stock_type': 'pattern',
						'pump_model_id': entry.pump_model_id.id,
						'pattern_id': entry.pattern_id.id,
						'pattern_name': entry.pattern_name,
						'moc_id': entry.moc_id.id,
						'stage_id': entry.stage_id.id,
						'qty': fettling_accept_qty,
						'available_qty': fettling_accept_qty,
						'each_wgt': fettling_weight,
						'total_weight': fettling_accept_qty * fettling_weight,
						'stock_mode': 'excess',
						'stock_state': 'ready_for_ms'
					}
					
					inward_line_id = inward_line_obj.create(cr, uid, inward_line_vals)
					
					self.write(cr,uid, ids,{'state':'complete'})
		return True
		
	def fettling_reject_process(self,cr,uid,ids,fettling_qty,fettling_reject_qty,fettling_weight,fettling_date,fettling_reject_remarks_id,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		if fettling_reject_qty > 0:
			
			if entry.order_id.flag_for_stock == False:
			
				reject_rem_qty = fettling_reject_qty
			
				### Checking in Stock Inward for Ready for MS ###
				
				cr.execute(""" select sum(available_qty) as stock_qty
					from ch_stock_inward_details  
					where pattern_id = %s and moc_id = %s
					and  foundry_stock_state = 'ready_for_ms' and available_qty > 0 and stock_type = 'pattern'  """%(entry.pattern_id.id,entry.moc_id.id))
				stock_inward_qty = cr.fetchone();
				
				if stock_inward_qty:
					if stock_inward_qty[0] != None:
						reject_rem_qty =  fettling_reject_qty - stock_inward_qty[0]
						
						if reject_rem_qty <= 0:
							reject_rem_qty = 0
							qc_qty = fettling_reject_qty
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
							and  foundry_stock_state = 'ready_for_ms' 
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
									'schedule_qty':entry.schedule_qty,
									'production_id':entry.production_id.id,
									'pour_qty':rem_qty,
									'inward_accept_qty': rem_qty,
									'state':'waiting',
									'pour_id': entry.pour_id.id,
									'pour_line_id': entry.pour_line_id.id,
									
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
								
								
								if stk_item['stage_name'] == 'HEAT TREATMENT':
									
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
				
						### Full Rejection Update ###
						full_reject_qty = fettling_qty - rem_qty
						if full_reject_qty == 0:
							self.write(cr, uid, ids, {'state':'complete'})
							
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
	
			else:
				
				### Qty Updation in Stock Inward ###
						
				inward_line_obj = self.pool.get('ch.stock.inward.details')
				
				cr.execute(""" select id,available_qty
					from ch_stock_inward_details  
					where pattern_id = %s and moc_id = %s
					and  foundry_stock_state = 'foundry_inprogress'
					and available_qty > 0 and stock_type = 'pattern' """%(entry.pattern_id.id,entry.moc_id.id))
					
				stock_inward_items = cr.dictfetchall();
				stock_updation_qty = fettling_reject_qty
				
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
										
	
		if fettling_reject_qty > 0:
			
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
				'stage_name': entry.stage_name,
				'qty': fettling_reject_qty,
				'each_weight': fettling_weight,
				'reject_remarks_id': fettling_reject_remarks_id
			}
			
			foundry_rejection_id = foundry_rejection_obj.create(cr, uid, rejection_vals)

		return True
		
	def knockout_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.knockout_qty - entry.knockout_accept_qty
		if entry.knockout_state == 'pending':
			if entry.knockout_qty <= 0 or entry.knockout_accept_qty < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
							
			if (entry.knockout_accept_qty + entry.knockout_reject_qty) > entry.knockout_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should not exceed Production Qty !!'))
							
			if (entry.knockout_accept_qty + entry.knockout_reject_qty) < entry.knockout_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should be equal to Production Qty !!'))
							
			if reject_qty > 0:
				if entry.knockout_reject_qty == 0:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Enter Rejection Qty !!'))
				if entry.knockout_reject_qty < reject_qty:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Check Rejection Qty !!'))
							
			if entry.knockout_reject_qty > 0 and not entry.knockout_reject_remarks_id:
				raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
					
			knockout_date = entry.knockout_date
			knockout_date = str(knockout_date)
			knockout_date = datetime.strptime(knockout_date, '%Y-%m-%d')
			
			if knockout_date > today:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to save with future date !!'))
					
			### Weight Logic ###
			
			#~ casting_wgt_result = ''
			#~ design_wgt_result = ''
			### Getting the MOC Family type ###
			
			#~ moc_family_type = entry.moc_id.weight_type
			
			### Checking the Rough Casting Weight ###
			#~ pat_wgt_obj = self.pool.get('ch.latest.weight')
			#~ 
			#~ if moc_family_type == False:
				#~ raise osv.except_osv(_('Warning!'),
					#~ _('Kindly configure family type in moc !!'))
			#~ pat_wgt_id = pat_wgt_obj.search(cr, uid, [('weight_type','=',moc_family_type),('header_id','=',entry.pattern_id.id)])
			#~ 
			#~ if pat_wgt_id == []:
				#~ raise osv.except_osv(_('Warning!'),
					#~ _('Kindly configure Production Weight in Pattern !!'))
			#~ 
			#~ pat_wgt_rec = pat_wgt_obj.browse(cr, uid, pat_wgt_id[0])
			#~ 
			#~ casting_wgt = pat_wgt_rec.casting_weight
			#~ casting_wgt_tol_per = pat_wgt_rec.casting_tolerance
			#~ casting_wgt_tol_val = (casting_wgt * casting_wgt_tol_per) / 100
			#~ 
			#~ total_casting_val = casting_wgt + casting_wgt_tol_val
			#~ 
			#~ if entry.finish_grinding_weight > total_casting_val:
				#~ casting_wgt_result = 'fail'
			#~ if entry.finish_grinding_weight <= total_casting_val:
				#~ casting_wgt_result = 'pass'
			#~ 
			#~ 
			#~ ### Checking the Design Weight ###
			#~ if moc_family_type == 'ci':
				#~ design_wgt = entry.pattern_id.ci_weight
			#~ if moc_family_type == 'ss':
				#~ design_wgt = entry.pattern_id.pcs_weight
			#~ if moc_family_type == 'non_ferrous':
				#~ design_wgt = entry.pattern_id.nonferous_weight
			#~ 
			#~ design_wgt_tol_per = entry.pattern_id.tolerance
			#~ design_wgt_tol_val = (design_wgt * design_wgt_tol_per) / 100
			#~ 
			#~ total_design_val = design_wgt + design_wgt_tol_val
			#~ 
			#~ if entry.finish_grinding_weight > total_design_val:
				#~ design_wgt_result = 'fail'
			#~ if entry.finish_grinding_weight <= total_design_val:
				#~ design_wgt_result = 'pass'
			#~ 
			#~ if casting_wgt_result == 'fail' or design_wgt_result == 'fail':
				#~ self.write(cr, uid, ids, {'flag_ko_special_app':True})
				#~ 
			#~ else:
			
			self.fettling_accept_process(cr,uid,ids,entry.knockout_qty,entry.knockout_accept_qty,
				entry.knockout_weight,entry.knockout_date)
			self.fettling_reject_process(cr,uid,ids,entry.knockout_qty,entry.knockout_reject_qty,
				entry.knockout_weight,entry.knockout_date,entry.knockout_reject_remarks_id.id)
			self.write(cr, uid, ids, {'knockout_state':'complete'})
		else:
			pass
		return True
		
		
		
	def decoring_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.decoring_qty - entry.decoring_accept_qty
		if entry.decoring_state == 'pending':
			if entry.decoring_qty <= 0 or entry.decoring_accept_qty < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
							
			if (entry.decoring_accept_qty + entry.decoring_reject_qty) > entry.decoring_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should not exceed Production Qty !!'))
							
			if (entry.decoring_accept_qty + entry.decoring_reject_qty) < entry.decoring_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should be equal to Production Qty !!'))
							
			if reject_qty > 0:
				if entry.decoring_reject_qty == 0:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Enter Rejection Qty !!'))
				if entry.decoring_reject_qty < reject_qty:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Check Rejection Qty !!'))
					
			if entry.decoring_reject_qty > 0 and not entry.decoring_reject_remarks_id:
				raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
					
					
			decoring_date = entry.decoring_date
			decoring_date = str(decoring_date)
			decoring_date = datetime.strptime(decoring_date, '%Y-%m-%d')
			
			if decoring_date > today:
				
				raise osv.except_osv(_('Warnings!'),
					_('System not allow to save with future date !!'))
			
			self.fettling_accept_process(cr,uid,ids,entry.decoring_qty,entry.decoring_accept_qty,
				entry.decoring_weight,entry.decoring_date)
			self.fettling_reject_process(cr,uid,ids,entry.decoring_qty,entry.decoring_reject_qty,
				entry.decoring_weight,entry.decoring_date,entry.decoring_reject_remarks_id.id)
			self.write(cr, uid, ids, {'decoring_state':'complete'})
		else:
			pass
		return True
		
		
	def shot_blast_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.shot_blast_qty - entry.shot_blast_accept_qty
		
		if entry.shot_blast_state == 'pending':
			if entry.shot_blast_qty <= 0 or entry.shot_blast_accept_qty < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
							
			if (entry.shot_blast_accept_qty + entry.shot_blast_reject_qty) > entry.shot_blast_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should not exceed Production Qty !!'))
							
			if (entry.shot_blast_accept_qty + entry.shot_blast_reject_qty) < entry.shot_blast_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should be equal to Production Qty !!'))
							
							
			if reject_qty > 0:
				if entry.shot_blast_reject_qty == 0:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Enter Rejection Qty !!'))
				if entry.shot_blast_reject_qty < reject_qty:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Check Rejection Qty !!'))
							
			if entry.shot_blast_reject_qty > 0 and not entry.shot_blast_reject_remarks_id:
				raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
					
			shot_blast_date = entry.shot_blast_date
			shot_blast_date = str(shot_blast_date)
			shot_blast_date = datetime.strptime(shot_blast_date, '%Y-%m-%d')
			
			if shot_blast_date > today:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to save with future date !!'))
			
			self.fettling_accept_process(cr,uid,ids,entry.shot_blast_qty,entry.shot_blast_accept_qty,
				entry.shot_blast_weight,entry.shot_blast_date)
			self.fettling_reject_process(cr,uid,ids,entry.shot_blast_qty,entry.shot_blast_reject_qty,
				entry.shot_blast_weight,entry.shot_blast_date,entry.shot_blast_reject_remarks_id.id)
			
			self.write(cr, uid, ids, {'shot_blast_state':'complete'})
		else:
			pass
		return True
		
		
	def hammering_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.hammering_qty - entry.hammering_accept_qty
		
		if entry.hammering_state == 'pending':
			if entry.hammering_qty <= 0 or entry.hammering_accept_qty < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
							
			if (entry.hammering_accept_qty + entry.hammering_reject_qty) > entry.hammering_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should not exceed Production Qty !!'))
							
			if (entry.hammering_accept_qty + entry.hammering_reject_qty) < entry.hammering_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should be equal to Production Qty !!'))
							
			if reject_qty > 0:
				if entry.hammering_reject_qty == 0:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Enter Rejection Qty !!'))
				if entry.hammering_reject_qty < reject_qty:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Check Rejection Qty !!'))
							
			if entry.hammering_reject_qty > 0 and not entry.hammering_reject_remarks_id:
				raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
					
			
			hammering_date = entry.hammering_date
			hammering_date = str(hammering_date)
			hammering_date = datetime.strptime(hammering_date, '%Y-%m-%d')
			
			if hammering_date > today:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to save with future date !!'))
			
			self.fettling_accept_process(cr,uid,ids,entry.hammering_qty,entry.hammering_accept_qty,
				entry.hammering_weight,entry.hammering_date)
			self.fettling_reject_process(cr,uid,ids,entry.hammering_qty,entry.hammering_reject_qty,
				entry.hammering_weight,entry.hammering_date,entry.hammering_reject_remarks_id.id)
			
			self.write(cr, uid, ids, {'hammering_state':'complete'})
		else:
			pass
		return True
		
	def wheel_cutting_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.wheel_cutting_qty - entry.wheel_cutting_accept_qty
		
		if entry.wheel_cutting_state == 'pending':
			if entry.wheel_cutting_qty <= 0 or entry.wheel_cutting_accept_qty < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
							
			if (entry.wheel_cutting_accept_qty + entry.wheel_cutting_reject_qty) > entry.wheel_cutting_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should not exceed Production Qty !!'))
							
			if (entry.wheel_cutting_accept_qty + entry.wheel_cutting_reject_qty) < entry.wheel_cutting_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should be equal to Production Qty !!'))
							
			if reject_qty > 0:
				if entry.wheel_cutting_reject_qty == 0:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Enter Rejection Qty !!'))
				if entry.wheel_cutting_reject_qty < reject_qty:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Check Rejection Qty !!'))
							
			if entry.wheel_cutting_reject_qty > 0 and not entry.wheel_cutting_reject_remarks_id:
				raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
					
					
			wheel_cutting_date = entry.wheel_cutting_date
			wheel_cutting_date = str(wheel_cutting_date)
			wheel_cutting_date = datetime.strptime(wheel_cutting_date, '%Y-%m-%d')
			
			if wheel_cutting_date > today:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to save with future date !!'))
			
			self.fettling_accept_process(cr,uid,ids,entry.wheel_cutting_qty,entry.wheel_cutting_accept_qty,
				entry.wheel_cutting_weight,entry.wheel_cutting_date)
			self.fettling_reject_process(cr,uid,ids,entry.wheel_cutting_qty,entry.wheel_cutting_reject_qty,
				entry.wheel_cutting_weight,entry.wheel_cutting_date,entry.wheel_cutting_reject_remarks_id.id)
			
			self.write(cr, uid, ids, {'wheel_cutting_state':'complete'})
		else:
			pass
		return True
		
	def gas_cutting_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.gas_cutting_qty - entry.gas_cutting_accept_qty
		
		if entry.gas_cutting_state == 'pending':
			if entry.gas_cutting_qty <= 0 or entry.gas_cutting_accept_qty < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
							
			if (entry.gas_cutting_accept_qty + entry.gas_cutting_reject_qty) > entry.gas_cutting_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should not exceed Production Qty !!'))
							
			if (entry.gas_cutting_accept_qty + entry.gas_cutting_reject_qty) < entry.gas_cutting_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should be equal to Production Qty !!'))
							
			if reject_qty > 0:
				if entry.gas_cutting_reject_qty == 0:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Enter Rejection Qty !!'))
				if entry.gas_cutting_reject_qty < reject_qty:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Check Rejection Qty !!'))
							
			if entry.gas_cutting_reject_qty > 0 and not entry.gas_cutting_reject_remarks_id:
				raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
					
			
			gas_cutting_date = entry.gas_cutting_date
			gas_cutting_date = str(gas_cutting_date)
			gas_cutting_date = datetime.strptime(gas_cutting_date, '%Y-%m-%d')
			
			if gas_cutting_date > today:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to save with future date !!'))
			
			self.fettling_accept_process(cr,uid,ids,entry.gas_cutting_qty,entry.gas_cutting_accept_qty,
				entry.gas_cutting_weight,entry.gas_cutting_date)
			self.fettling_reject_process(cr,uid,ids,entry.gas_cutting_qty,entry.gas_cutting_reject_qty,
				entry.gas_cutting_weight,entry.gas_cutting_date,entry.gas_cutting_reject_remarks_id.id)
			
			self.write(cr, uid, ids, {'gas_cutting_state':'complete'})
		else:
			pass
		return True
		
		
	def arc_cutting_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.arc_cutting_qty - entry.arc_cutting_accept_qty
		
		if entry.arc_cutting_state == 'pending':
			if entry.arc_cutting_qty <= 0 or entry.arc_cutting_accept_qty < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
							
			if (entry.arc_cutting_accept_qty + entry.arc_cutting_reject_qty) > entry.arc_cutting_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should not exceed Production Qty !!'))
							
			if (entry.arc_cutting_accept_qty + entry.arc_cutting_reject_qty) < entry.arc_cutting_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should be equal to Production Qty !!'))
							
							
			if reject_qty > 0:
				if entry.arc_cutting_reject_qty == 0:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Enter Rejection Qty !!'))
				if entry.arc_cutting_reject_qty < reject_qty:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Check Rejection Qty !!'))
							
			if entry.arc_cutting_reject_qty > 0 and not entry.arc_cutting_reject_remarks_id:
				raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
					
			
			arc_cutting_date = entry.arc_cutting_date
			arc_cutting_date = str(arc_cutting_date)
			arc_cutting_date = datetime.strptime(arc_cutting_date, '%Y-%m-%d')
			
			if arc_cutting_date > today:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to save with future date !!'))
			
			self.fettling_accept_process(cr,uid,ids,entry.arc_cutting_qty,entry.arc_cutting_accept_qty,
				entry.arc_cutting_weight,entry.arc_cutting_date)
			self.fettling_reject_process(cr,uid,ids,entry.arc_cutting_qty,entry.arc_cutting_reject_qty,
				entry.arc_cutting_weight,entry.arc_cutting_date,entry.arc_cutting_reject_remarks_id.id)
			
			self.write(cr, uid, ids, {'arc_cutting_state':'complete'})
		else:
			pass
		return True
		
	def heat_treatment_update(self,cr,uid,ids,context=None):
		total_wt = 0
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
						
		reject_qty = entry.heat_total_qty - entry.heat_qty
		if entry.heat_state == 'pending':
			if entry.heat_qty <= 0 or entry.heat_each_weight < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
							
			if (entry.heat_qty + entry.heat_reject_qty) > entry.heat_total_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should not exceed Production Qty !!'))
							
			if (entry.heat_qty + entry.heat_reject_qty) < entry.heat_total_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should be equal to Production Qty !!'))
							
						
			if reject_qty > 0:
				if entry.heat_reject_qty == 0:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Enter Rejection Qty !!'))
				if entry.heat_reject_qty < reject_qty:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Check Rejection Qty !!')) 
					
					
			if entry.heat_reject_qty > 0 and not entry.heat_reject_remarks_id:
				raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))  
											
			heat_date = entry.heat_date
			heat_date = str(heat_date)
			heat_date = datetime.strptime(heat_date, '%Y-%m-%d')
			
			if heat_date > today:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to save with future date !!'))
			
			self.fettling_accept_process(cr,uid,ids,entry.heat_qty,entry.heat_qty,
				entry.heat_each_weight,entry.heat_date)
			self.fettling_reject_process(cr,uid,ids,entry.heat_qty,entry.heat_reject_qty,
				entry.heat_each_weight,entry.heat_date,entry.heat_reject_remarks_id.id)
				
				
			### Updating Total Weight ###
			total_wt = entry.heat_qty * entry.heat_each_weight 
			self.write(cr, uid, ids, {'heat_state': 'complete','heat_total_weight': total_wt,'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def heat_treatment2_update(self,cr,uid,ids,context=None):
		total_wt = 0
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
						
		reject_qty = entry.heat2_total_qty - entry.heat2_qty
		
		if entry.heat2_state == 'pending':
		
			if entry.heat2_qty <= 0 or entry.heat2_each_weight < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
							
			if (entry.heat2_qty + entry.heat2_reject_qty) > entry.heat2_total_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should not exceed Production Qty !!'))
							
			if (entry.heat2_qty + entry.heat2_reject_qty) < entry.heat2_total_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should be equal to Production Qty !!'))
							
						
			if reject_qty > 0:
				if entry.heat2_reject_qty == 0:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Enter Rejection Qty !!'))
				if entry.heat2_reject_qty < reject_qty:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Check Rejection Qty !!')) 
					
					
			if entry.heat2_reject_qty > 0 and not entry.heat2_reject_remarks_id:
				raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))  
											
			heat_date = entry.heat2_date
			heat_date = str(heat_date)
			heat_date = datetime.strptime(heat_date, '%Y-%m-%d')
			
			if heat_date > today:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to save with future date !!'))
			
			
			self.fettling_accept_process(cr,uid,ids,entry.heat2_qty,entry.heat2_qty,
				entry.heat2_each_weight,entry.heat_date)
			self.fettling_reject_process(cr,uid,ids,entry.heat2_qty,entry.heat2_reject_qty,
				entry.heat2_each_weight,entry.heat_date,entry.heat2_reject_remarks_id.id)
				
				
			### Updating Total Weight ###
			total_wt = entry.heat2_qty * entry.heat2_each_weight 
			self.write(cr, uid, ids, {'heat2_state': 'complete','heat2_total_weight': total_wt,'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def heat_treatment3_update(self,cr,uid,ids,context=None):
		total_wt = 0
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
						
		reject_qty = entry.heat3_total_qty - entry.heat3_qty
		
		if entry.heat3_state == 'pending':
			if entry.heat3_qty <= 0 or entry.heat3_each_weight < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
							
			if (entry.heat3_qty + entry.heat3_reject_qty) > entry.heat3_total_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should not exceed Production Qty !!'))
							
			if (entry.heat3_qty + entry.heat3_reject_qty) < entry.heat3_total_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should be equal to Production Qty !!'))
							
						
			if reject_qty > 0:
				if entry.heat3_reject_qty == 0:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Enter Rejection Qty !!'))
				if entry.heat3_reject_qty < reject_qty:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Check Rejection Qty !!')) 
					
					
			if entry.heat3_reject_qty > 0 and not entry.heat3_reject_remarks_id:
				raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))  
											
			heat_date = entry.heat3_date
			heat_date = str(heat_date)
			heat_date = datetime.strptime(heat_date, '%Y-%m-%d')
			
			if heat_date > today:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to save with future date !!'))
			
			self.fettling_accept_process(cr,uid,ids,entry.heat3_qty,entry.heat3_qty,
				entry.heat3_each_weight,entry.heat_date)
			self.fettling_reject_process(cr,uid,ids,entry.heat3_qty,entry.heat3_reject_qty,
				entry.heat3_each_weight,entry.heat_date,entry.heat3_reject_remarks_id.id)
				
				
			### Updating Total Weight ###
			total_wt = entry.heat3_qty * entry.heat3_each_weight 
			self.write(cr, uid, ids, {'heat3_state': 'complete','heat3_total_weight': total_wt,'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
		
		
	def rough_grinding_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.rough_grinding_qty - entry.rough_grinding_accept_qty
		
		if entry.rough_grinding_state == 'pending':
			if entry.rough_grinding_qty <= 0 or entry.rough_grinding_accept_qty < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
							
			
			total_qty = entry.rough_grinding_accept_qty + entry.rough_grinding_reject_qty + entry.rough_grinding_rework_qty
			
			if total_qty > entry.rough_grinding_qty:
				raise osv.except_osv(_('Warning!'),
						_('Kindly Check the Quantities !!'))
						
			if total_qty < entry.rough_grinding_qty:
				raise osv.except_osv(_('Warning!'),
							_('Kindly Check the Quantities !'))
			
			if entry.rough_grinding_rework_qty == 0:		
			
				if reject_qty > 0:
					if entry.rough_grinding_reject_qty == 0:
						raise osv.except_osv(_('Warning!'),
						_('Kindly Enter Rejection Qty !!'))
					if entry.rough_grinding_reject_qty < reject_qty:
						raise osv.except_osv(_('Warning!'),
						_('Kindly Check Rejection Qty !!'))
							
			if entry.rough_grinding_reject_qty > 0 and not entry.rough_grinding_reject_remarks_id:
				raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
					
			rough_grinding_date = entry.rough_grinding_date
			rough_grinding_date = str(rough_grinding_date)
			rough_grinding_date = datetime.strptime(rough_grinding_date, '%Y-%m-%d')
			
			if rough_grinding_date > today:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to save with future date !!'))
			
			self.fettling_accept_process(cr,uid,ids,entry.rough_grinding_qty,entry.rough_grinding_accept_qty,
				entry.rough_grinding_weight,entry.rough_grinding_date)
			self.fettling_reject_process(cr,uid,ids,entry.rough_grinding_qty,entry.rough_grinding_reject_qty,
				entry.rough_grinding_weight,entry.rough_grinding_date,entry.rough_grinding_reject_remarks_id.id)
					
			if entry.rough_grinding_rework_qty:
				### Next Stage Qty ###
				welding_qty = entry.rough_grinding_rework_qty
				### Sequence Number Generation ###
				welding_name = ''   
				welding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.welding')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,welding_seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(welding_seq_id[0],seq_rec.code))
				welding_name = cr.fetchone();
				welding_stage_id = self.pool.get('kg.stage.master').search(cr, uid, [('name','=','WELDING')])
				self.write(cr, uid, ids, {'welding_date':time.strftime('%Y-%m-%d'),'welding_state':'progress','welding_stage_id':welding_stage_id[0], 'welding_qty': welding_qty,'welding_accept_qty': welding_qty,'welding_name':welding_name[0]})
			
			self.write(cr, uid, ids, {'rough_grinding_state':'complete','update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def welding_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.welding_qty - entry.welding_accept_qty
		
		if entry.welding_state != 'done':
			if entry.welding_qty <= 0 or entry.welding_accept_qty <= 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
							
			if (entry.welding_accept_qty + entry.welding_reject_qty) > entry.welding_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should not exceed Production Qty !!'))
							
			if (entry.welding_accept_qty + entry.welding_reject_qty) < entry.welding_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should be equal to Production Qty !!'))
							
			if reject_qty > 0:
				if entry.welding_reject_qty == 0:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Enter Rejection Qty !!'))
				if entry.welding_reject_qty < reject_qty:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Check Rejection Qty !!'))
							
			if entry.welding_reject_qty > 0 and not entry.welding_reject_remarks_id:
				raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
					
			
					
			welding_date = entry.welding_date
			welding_date = str(welding_date)
			welding_date = datetime.strptime(welding_date, '%Y-%m-%d')
			
			if welding_date > today:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to save with future date !!'))
			
			if entry.welding_accept_qty > 0:
				
				fettling_obj = self.pool.get('kg.fettling')
			
				### Sequence Number Generation ###
				fettling_name = ''  
				fettling_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.fettling.inward')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,fettling_seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(fettling_seq_id[0],seq_rec.code))
				fettling_name = cr.fetchone();
				
				### Rough Grinding Details ###
				
				### Next Stage Qty ###
				rough_grinding_qty = entry.welding_accept_qty
				### Sequence Number Generation ###
				rough_grinding_name = ''	
				rough_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.rough.grinding')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,rough_grinding_seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(rough_grinding_seq_id[0],seq_rec.code))
				rough_grinding_name = cr.fetchone();
				rough_grinding_stage_id = self.pool.get('kg.stage.master').search(cr, uid, [('name','=','ROUGH GRINDING')])
				
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
				'schedule_qty':entry.schedule_qty,
				'production_id':entry.production_id.id,
				'pour_qty':entry.pour_qty,
				'inward_accept_qty':entry.inward_accept_qty,
				'state':'accept',
				'stage_id':rough_grinding_stage_id[0],
				'rough_grinding_qty': rough_grinding_qty,
				'rough_grinding_accept_qty': rough_grinding_qty,
				'rough_grinding_name':rough_grinding_name[0],
				
				}
					
				fettling_id = fettling_obj.create(cr, uid, fettling_vals)
				
				self.write(cr, uid, ids, {'welding_state':'done','welding_stage_id':rough_grinding_stage_id[0]})
					
			if entry.welding_reject_qty > 0:
				
				if entry.order_id.flag_for_stock == False:		  
								
					reject_rem_qty = entry.welding_reject_qty
				
					### Checking in Stock Inward for Ready for MS ###
					
					cr.execute(""" select sum(available_qty) as stock_qty
						from ch_stock_inward_details  
						where pattern_id = %s and moc_id = %s
						and  foundry_stock_state = 'ready_for_ms' and available_qty > 0 and stock_type = 'pattern'  """%(entry.pattern_id.id,entry.moc_id.id))
					stock_inward_qty = cr.fetchone();
					
					if stock_inward_qty:
						if stock_inward_qty[0] != None:
							reject_rem_qty =  entry.welding_reject_qty - stock_inward_qty[0]
							
							if reject_rem_qty <= 0:
								reject_rem_qty = 0
								qc_qty = entry.welding_reject_qty
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
								and  foundry_stock_state = 'ready_for_ms' 
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
						and  foundry_stock_state = 'foundry_inprogress' and available_qty > 0 and stock_type = 'pattern'  """%(entry.pattern_id.id,entry.moc_id.id))
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
										and  foundry_stock_state = 'foundry_inprogress' 
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
										'schedule_qty':entry.schedule_qty,
										'production_id':entry.production_id.id,
										'pour_qty':rem_qty,
										'inward_accept_qty': rem_qty,
										'state':'waiting',
										'pour_id': entry.pour_id.id,
										'pour_line_id': entry.pour_line_id.id,
										
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':knockout_qty,'inward_accept_qty': knockout_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'knockout_date':time.strftime('%Y-%m-%d'),'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0],'allocated_qty':knockout_qty,'flag_allocated':'t','allocated_accepted_qty':knockout_qty,'allocation_state':'waiting'})
										
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':decoring_qty,'inward_accept_qty': decoring_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'decoring_date':time.strftime('%Y-%m-%d'),'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0],'allocated_qty':decoring_qty,'flag_allocated':'t','allocated_accepted_qty':decoring_qty,'allocation_state':'waiting'})
										
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':shot_blast_qty,'inward_accept_qty': shot_blast_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'shot_blast_date':time.strftime('%Y-%m-%d'),'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0],'allocated_qty':shot_blast_qty,'flag_allocated':'t','allocated_accepted_qty':shot_blast_qty,'allocation_state':'waiting'})
									
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':hammering_qty,'inward_accept_qty': hammering_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'hammering_date':time.strftime('%Y-%m-%d'),'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0],'allocated_qty':hammering_qty,'flag_allocated':'t','allocated_accepted_qty':hammering_qty,'allocation_state':'waiting'})
									
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':wheel_cutting_qty,'inward_accept_qty': wheel_cutting_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'wheel_cutting_date':time.strftime('%Y-%m-%d'),'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0],'allocated_qty':wheel_cutting_qty,'flag_allocated':'t','allocated_accepted_qty':wheel_cutting_qty,'allocation_state':'waiting'})
									
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':gas_cutting_qty,'inward_accept_qty': gas_cutting_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'gas_cutting_date':time.strftime('%Y-%m-%d'),'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0],'allocated_qty':gas_cutting_qty,'flag_allocated':'t','allocated_accepted_qty':gas_cutting_qty,'allocation_state':'waiting'})
									
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':arc_cutting_qty,'inward_accept_qty': arc_cutting_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'arc_cutting_date':time.strftime('%Y-%m-%d'),'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0],'allocated_qty':arc_cutting_qty,'flag_allocated':'t','allocated_accepted_qty':arc_cutting_qty,'allocation_state':'waiting'})
									
										### Updation in STK WO ###
										stk_rem_qty =  stk_arc_cutting_qty - arc_cutting_qty
										if stk_rem_qty > 0:
											self.write(cr, uid, stk_item['id'], {'arc_cutting_qty': stk_rem_qty,'arc_cutting_accept_qty':stk_rem_qty})
										else:
											self.write(cr, uid, stk_item['id'], {'state':'complete'})
											
										allocated_qty = arc_cutting_qty
									
									
									if stk_item['stage_name'] == 'HEAT TREATMENT':
										
										stk_heat_qty = stk_item_rec.heat_qty
										
										if rem_qty <= stk_heat_qty:
											heat_total_qty = rem_qty
										if rem_qty > stk_heat_qty:
											heat_total_qty = stk_heat_qty
										
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':heat_total_qty,'inward_accept_qty': heat_total_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'heat_date':time.strftime('%Y-%m-%d'),'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty,'allocated_qty':heat_total_qty,'flag_allocated':'t','allocated_accepted_qty':heat_total_qty,'allocation_state':'waiting'})
									
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':rough_grinding_qty,'inward_accept_qty': rough_grinding_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'rough_grinding_date':time.strftime('%Y-%m-%d'),'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,'rough_grinding_name':rough_grinding_name[0],'allocated_qty':rough_grinding_qty,'flag_allocated':'t','allocated_accepted_qty':rough_grinding_qty,'allocation_state':'waiting'})
									
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':finish_grinding_qty,'inward_accept_qty': finish_grinding_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'finish_grinding_date':time.strftime('%Y-%m-%d'),'finish_grinding_qty': finish_grinding_qty,'finish_grinding_accept_qty': finish_grinding_qty,'finish_grinding_name':finish_grinding_name[0],'allocated_qty':finish_grinding_qty,'flag_allocated':'t','allocated_accepted_qty':finish_grinding_qty,'allocation_state':'waiting'})
										
										### Updation in STK WO ###
										stk_rem_qty =  stk_finish_grinding_qty - finish_grinding_qty
										if stk_rem_qty > 0:
											self.write(cr, uid, stk_item['id'], {'finish_grinding_qty': stk_rem_qty,'finish_grinding_accept_qty':stk_rem_qty})
										else:
											self.write(cr, uid, stk_item['id'], {'state':'complete'})
											
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
										self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':reshot_blasting_qty,'inward_accept_qty': reshot_blasting_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'reshot_blasting_date':time.strftime('%Y-%m-%d'),'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0],'allocated_qty':reshot_blasting_qty,'flag_allocated':'t','allocated_accepted_qty':reshot_blasting_qty,'allocation_state':'waiting'})
								
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
					
							### Full Rejection Update ###
							full_reject_qty = entry.welding_qty - rem_qty
							if full_reject_qty == 0:
								self.write(cr, uid, ids, {'state':'complete'})
								
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
					
				else:
					
					### Qty Updation in Stock Inward ###
							
					inward_line_obj = self.pool.get('ch.stock.inward.details')
					
					cr.execute(""" select id,available_qty
						from ch_stock_inward_details  
						where pattern_id = %s and moc_id = %s
						and  foundry_stock_state = 'foundry_inprogress'
						and available_qty > 0 and stock_type = 'pattern' """%(entry.pattern_id.id,entry.moc_id.id))
						
					stock_inward_items = cr.dictfetchall();
					stock_updation_qty = entry.welding_reject_qty
					
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
			
			if entry.welding_reject_qty > 0:
				
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
					'stage_name': entry.stage_name,
					'qty': entry.welding_reject_qty,
					'each_weight': entry.welding_weight,
					'reject_remarks_id': entry.welding_reject_remarks_id.id
				}
				
				foundry_rejection_id = foundry_rejection_obj.create(cr, uid, rejection_vals)
			
			self.write(cr, uid, ids, {'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def finish_grinding_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.finish_grinding_qty - entry.finish_grinding_accept_qty
		
		if entry.finish_grinding_state == 'pending':
			if entry.finish_grinding_qty <= 0 or entry.finish_grinding_accept_qty < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
							
			if (entry.finish_grinding_accept_qty + entry.finish_grinding_reject_qty) > entry.finish_grinding_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should not exceed Production Qty !!'))
							
			if (entry.finish_grinding_accept_qty + entry.finish_grinding_reject_qty) < entry.finish_grinding_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should be equal to Production Qty !!'))
							
			if reject_qty > 0:
				if entry.finish_grinding_reject_qty == 0:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Enter Rejection Qty !!'))
				if entry.finish_grinding_reject_qty < reject_qty:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Check Rejection Qty !!'))
							
			if entry.finish_grinding_reject_qty > 0 and not entry.finish_grinding_reject_remarks_id:
				raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
			
					
			finish_grinding_date = entry.finish_grinding_date
			finish_grinding_date = str(finish_grinding_date)
			finish_grinding_date = datetime.strptime(finish_grinding_date, '%Y-%m-%d')
			
			if finish_grinding_date > today:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to save with future date !!'))
					
					
			### Weight Logic ###
			
			#~ casting_wgt_result = ''
			#~ design_wgt_result = ''
			### Getting the MOC Family type ###
			
			#~ moc_family_type = entry.moc_id.weight_type
			
			### Checking the Rough Casting Weight ###
			#~ pat_wgt_obj = self.pool.get('ch.latest.weight')
			#~ 
			#~ if moc_family_type == False:
				#~ raise osv.except_osv(_('Warning!'),
					#~ _('Kindly configure family type in moc !!'))
			#~ 
			#~ pat_wgt_id = pat_wgt_obj.search(cr, uid, [('weight_type','=',moc_family_type),('header_id','=',entry.pattern_id.id)])
			#~ 
			#~ if pat_wgt_id == []:
				#~ raise osv.except_osv(_('Warning!'),
					#~ _('Kindly configure Production Weight in Pattern !!'))
			#~ 
			#~ pat_wgt_rec = pat_wgt_obj.browse(cr, uid, pat_wgt_id[0])
			#~ 
			#~ casting_wgt = pat_wgt_rec.casting_weight
			#~ casting_wgt_tol_per = pat_wgt_rec.casting_tolerance
			#~ casting_wgt_tol_val = (casting_wgt * casting_wgt_tol_per) / 100
			#~ 
			#~ total_casting_val = casting_wgt + casting_wgt_tol_val
			#~ 
			#~ if entry.finish_grinding_weight > total_casting_val:
				#~ casting_wgt_result = 'fail'
			#~ if entry.finish_grinding_weight <= total_casting_val:
				#~ casting_wgt_result = 'pass'
			
			
			### Checking the Design Weight ###
			#~ if moc_family_type == 'ci':
				#~ design_wgt = entry.pattern_id.ci_weight
			#~ if moc_family_type == 'ss':
				#~ design_wgt = entry.pattern_id.pcs_weight
			#~ if moc_family_type == 'non_ferrous':
				#~ design_wgt = entry.pattern_id.nonferous_weight
			#~ 
			#~ design_wgt_tol_per = entry.pattern_id.tolerance
			#~ design_wgt_tol_val = (design_wgt * design_wgt_tol_per) / 100
			#~ 
			#~ total_design_val = design_wgt + design_wgt_tol_val
			#~ 
			#~ if entry.finish_grinding_weight > total_design_val:
				#~ design_wgt_result = 'fail'
			#~ if entry.finish_grinding_weight <= total_design_val:
				#~ design_wgt_result = 'pass'
			#~ 
			#~ if casting_wgt_result or design_wgt_result == 'fail':
				#~ 
				#~ self.write(cr, uid, ids, {'flag_fg_special_app':True})
				#~ 
			#~ else:
			
					
			if entry.flag_reshot_blast_applicable == True and entry.finish_grinding_accept_qty > 0:
				### Next Stage Qty ###
				reshot_blasting_qty = entry.finish_grinding_accept_qty
				### Sequence Number Generation ###
				reshot_blasting_name = ''   
				reshot_blasting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.reshot.blasting')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,reshot_blasting_seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(reshot_blasting_seq_id[0],seq_rec.code))
				reshot_blasting_name = cr.fetchone();
				stage_id = self.pool.get('kg.stage.master').search(cr, uid, [('name','=','RE SHOT BLASTING')])
				self.write(cr, uid, ids, {'stage_id':stage_id[0],'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0]})
			
			else:   
			
				self.fettling_accept_process(cr,uid,ids,entry.finish_grinding_qty,entry.finish_grinding_accept_qty,
					entry.finish_grinding_weight,entry.finish_grinding_date)
				self.fettling_reject_process(cr,uid,ids,entry.finish_grinding_qty,entry.finish_grinding_reject_qty,
					entry.finish_grinding_weight,entry.finish_grinding_date,entry.finish_grinding_reject_remarks_id.id)
			
			self.write(cr, uid, ids, {'finish_grinding_state':'complete','update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def reshot_blasting_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.reshot_blasting_qty - entry.reshot_blasting_accept_qty
		
		if entry.reshot_blasting_state == 'pending':
			if entry.reshot_blasting_qty <= 0 or entry.reshot_blasting_accept_qty < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
							
			if (entry.reshot_blasting_accept_qty + entry.reshot_blasting_reject_qty) > entry.reshot_blasting_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should not exceed Production Qty !!'))
							
			if (entry.reshot_blasting_accept_qty + entry.reshot_blasting_reject_qty) < entry.reshot_blasting_qty:
				raise osv.except_osv(_('Warning!'),
							_('Completed and Rejected qty should be equal to Production Qty !!'))
							
			if reject_qty > 0:
				if entry.reshot_blasting_reject_qty == 0:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Enter Rejection Qty !!'))
				if entry.reshot_blasting_reject_qty < reject_qty:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Check Rejection Qty !!'))
							
			if entry.reshot_blasting_reject_qty > 0 and not entry.reshot_blasting_reject_remarks_id:
				raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
					
			
					
			reshot_blasting_date = entry.reshot_blasting_date
			reshot_blasting_date = str(reshot_blasting_date)
			reshot_blasting_date = datetime.strptime(reshot_blasting_date, '%Y-%m-%d')
			
			if reshot_blasting_date > today:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to save with future date !!'))
			
			self.fettling_accept_process(cr,uid,ids,entry.reshot_blasting_qty,entry.reshot_blasting_accept_qty,
					entry.reshot_blasting_weight,entry.reshot_blasting_date)
			self.fettling_reject_process(cr,uid,ids,entry.reshot_blasting_qty,entry.reshot_blasting_reject_qty,
					entry.reshot_blasting_weight,entry.reshot_blasting_date,entry.reshot_blasting_reject_remarks_id.id)
			
			self.write(cr, uid, ids, {'reshot_blasting_state':'complete','update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
		
	def stock_allocation_update(self,cr,uid,ids,context=None):
		entry = self.browse(cr, uid, ids[0])
		production_obj = self.pool.get('kg.production')
		### Process for Accept Qty ###
		if entry.allocation_state == 'waiting':
			if entry.allocated_accepted_qty < 0:
				raise osv.except_osv(_('Warning!'),
							_('Check the Accepted Qty !!'))
			if entry.allocated_accepted_qty > entry.allocated_qty:
				raise osv.except_osv(_('Warning!'),
							_('Accepted Qty should not be greater than Allocated Qty !!'))
			if entry.allocated_accepted_qty > 0:
				
				if entry.stage_name == None or entry.stage_name == False:
					
					self.write(cr, uid, ids, {'inward_accept_qty': entry.allocated_accepted_qty,
						'flag_allocated': False,'allocation_state':'accept'})
					
				if entry.stage_name == 'KNOCK OUT':
					
					self.write(cr, uid, ids, {'knockout_qty':entry.allocated_accepted_qty,'knockout_accept_qty': entry.allocated_accepted_qty,
					'flag_allocated': False,'allocation_state':'accept'})
				
				if entry.stage_name == 'DECORING':
					
					self.write(cr, uid, ids, {'decoring_accept_qty': entry.allocated_accepted_qty,'decoring_qty': entry.allocated_accepted_qty,
					'flag_allocated': False,'allocation_state':'accept'})
					
				if entry.stage_name == 'SHOT BLAST':
					
					self.write(cr, uid, ids, {'shot_blast_accept_qty': entry.allocated_accepted_qty,'shot_blast_qty': entry.allocated_accepted_qty,
					'flag_allocated': False,'allocation_state':'accept'})
				
				if entry.stage_name == 'HAMMERING':
					
					self.write(cr, uid, ids, {'hammering_accept_qty': entry.allocated_accepted_qty,'hammering_qty': entry.allocated_accepted_qty,
					'flag_allocated': False,'allocation_state':'accept'})
					
				if entry.stage_name == 'WHEEL CUTTING':
					
					self.write(cr, uid, ids, {'wheel_cutting_accept_qty': entry.allocated_accepted_qty,'wheel_cutting_qty': entry.allocated_accepted_qty,
					'flag_allocated': False,'allocation_state':'accept'})
					
				if entry.stage_name == 'GAS CUTTING':
					
					self.write(cr, uid, ids, {'gas_cutting_accept_qty': entry.allocated_accepted_qty,'gas_cutting_qty': entry.allocated_accepted_qty,
					'flag_allocated': False,'allocation_state':'accept'})
					
				if entry.stage_name == 'ARC CUTTING':
					
					self.write(cr, uid, ids, {'arc_cutting_accept_qty': entry.allocated_accepted_qty,'arc_cutting_qty': entry.allocated_accepted_qty,
					'flag_allocated': False,'allocation_state':'accept'})
					
				if entry.stage_name == 'HEAT TREATMENT':
					
					self.write(cr, uid, ids, {'heat_qty':entry.allocated_accepted_qty,'heat_total_qty': entry.allocated_accepted_qty,
					'flag_allocated': False,'allocation_state':'accept'})
					
				if entry.stage_name == 'HEAT TREATMENT2':
					
					self.write(cr, uid, ids, {'heat2_qty':entry.allocated_accepted_qty,'heat2_total_qty': entry.allocated_accepted_qty,
					'flag_allocated': False,'allocation_state':'accept'})
					
				if entry.stage_name == 'HEAT TREATMENT3':
					
					self.write(cr, uid, ids, {'heat3_qty':entry.allocated_accepted_qty,'heat3_total_qty': entry.allocated_accepted_qty,
					'flag_allocated': False,'allocation_state':'accept'})
					
				if entry.stage_name == 'ROUGH GRINDING':
					
					self.write(cr, uid, ids, {'rough_grinding_accept_qty': entry.allocated_accepted_qty,'rough_grinding_qty': entry.allocated_accepted_qty,
					'flag_allocated': False,'allocation_state':'accept'})
					
				if entry.stage_name == 'FINISH GRINDING':
					
					self.write(cr, uid, ids, {'finish_grinding_accept_qty': entry.allocated_accepted_qty,'finish_grinding_qty': entry.allocated_accepted_qty,
					'flag_allocated': False,'allocation_state':'accept'})
				
				if entry.stage_name == 'RE SHOT BLASTING':
					
					self.write(cr, uid, ids, {'reshot_blasting_accept_qty': entry.allocated_accepted_qty,'reshot_blasting_qty': entry.allocated_accepted_qty,
					'flag_allocated': False,'allocation_state':'accept'})
				
				if entry.stage_name == 'WELDING':
					
					self.write(cr, uid, ids, {'welding_accept_qty': entry.allocated_accepted_qty,'welding_qty': entry.allocated_accepted_qty,
					'flag_allocated': False,'allocation_state':'accept'})
					
				
			reject_qty = entry.allocated_qty - entry.allocated_accepted_qty
			
			if reject_qty == entry.allocated_qty:
				self.write(cr, uid, ids, {'allocated_qty':0,'flag_allocated':'f','allocation_state':'reject'})
				
				
			if reject_qty > 0 and entry.allocation_reject_remarks_id.id == False:
				raise osv.except_osv(_('Warning !'), _('Kindly give rejection remarks !!'))
				
			if reject_qty > 0:
				reject_rem_qty = reject_qty
				
				### Checking in Stock Inward for Ready for MS ###
				
				cr.execute(""" select sum(available_qty) as stock_qty
					from ch_stock_inward_details  
					where pattern_id = %s and moc_id = %s
					and  foundry_stock_state = 'ready_for_ms' and available_qty > 0 and stock_type = 'pattern'  """%(entry.pattern_id.id,entry.moc_id.id))
				stock_inward_qty = cr.fetchone();
				
				if stock_inward_qty:
					if stock_inward_qty[0] != None:
						reject_rem_qty =  entry.reshot_blasting_reject_qty - stock_inward_qty[0]
						
						if reject_rem_qty <= 0:
							reject_rem_qty = 0
							qc_qty = entry.reshot_blasting_reject_qty
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
							and  foundry_stock_state = 'ready_for_ms' 
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
					and  foundry_stock_state = 'foundry_inprogress' and available_qty > 0 and stock_type = 'pattern'  """%(entry.pattern_id.id,entry.moc_id.id))
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
									'schedule_qty':entry.schedule_qty,
									'production_id':entry.production_id.id,
									'pour_qty':rem_qty,
									'inward_accept_qty': rem_qty,
									'state':'waiting',
									'pour_id': entry.pour_id.id,
									'pour_line_id': entry.pour_line_id.id,
									
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
									'flag_allocated':'t','allocated_accepted_qty':inward_accept_qty,'allocation_state':'waiting','pour_qty':inward_accept_qty})
										
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
									self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':knockout_qty,'inward_accept_qty': knockout_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'knockout_date':time.strftime('%Y-%m-%d'),'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0],'allocated_qty':knockout_qty,'flag_allocated':'t','allocated_accepted_qty':knockout_qty,'allocation_state':'waiting'})
									
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
									self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':decoring_qty,'inward_accept_qty': decoring_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'decoring_date':time.strftime('%Y-%m-%d'),'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0],'allocated_qty':decoring_qty,'flag_allocated':'t','allocated_accepted_qty':decoring_qty,'allocation_state':'waiting'})
									
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
									self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':shot_blast_qty,'inward_accept_qty': shot_blast_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'shot_blast_date':time.strftime('%Y-%m-%d'),'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0],'allocated_qty':shot_blast_qty,'flag_allocated':'t','allocated_accepted_qty':shot_blast_qty,'allocation_state':'waiting'})
								
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
									self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':hammering_qty,'inward_accept_qty': hammering_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'hammering_date':time.strftime('%Y-%m-%d'),'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0],'allocated_qty':hammering_qty,'flag_allocated':'t','allocated_accepted_qty':hammering_qty,'allocation_state':'waiting'})
								
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
									self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':wheel_cutting_qty,'inward_accept_qty': wheel_cutting_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'wheel_cutting_date':time.strftime('%Y-%m-%d'),'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0],'allocated_qty':wheel_cutting_qty,'flag_allocated':'t','allocated_accepted_qty':wheel_cutting_qty,'allocation_state':'waiting'})
									
								
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
									self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':gas_cutting_qty,'inward_accept_qty': gas_cutting_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'gas_cutting_date':time.strftime('%Y-%m-%d'),'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0],'allocated_qty':gas_cutting_qty,'flag_allocated':'t','allocated_accepted_qty':gas_cutting_qty,'allocation_state':'waiting'})
									
									
								
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
									self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':arc_cutting_qty,'inward_accept_qty': arc_cutting_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'arc_cutting_date':time.strftime('%Y-%m-%d'),'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0],'allocated_qty':arc_cutting_qty,'flag_allocated':'t','allocated_accepted_qty':arc_cutting_qty,'allocation_state':'waiting'})
									
								
									### Updation in STK WO ###
									stk_rem_qty =  stk_arc_cutting_qty - arc_cutting_qty
									if stk_rem_qty > 0:
										self.write(cr, uid, stk_item['id'], {'arc_cutting_qty': stk_rem_qty,'arc_cutting_accept_qty':stk_rem_qty})
									else:
										self.write(cr, uid, stk_item['id'], {'state':'complete'})
										
									allocated_qty = arc_cutting_qty
								
								
								if stk_item['stage_name'] == 'HEAT TREATMENT':
									
									stk_heat_qty = stk_item_rec.heat_qty
									
									if rem_qty <= stk_heat_qty:
										heat_total_qty = rem_qty
									if rem_qty > stk_heat_qty:
										heat_total_qty = stk_heat_qty
									
									self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':heat_total_qty,'inward_accept_qty': heat_total_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'heat_date':time.strftime('%Y-%m-%d'),'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty,'allocated_qty':heat_total_qty,'flag_allocated':'t','allocated_accepted_qty':heat_total_qty,'allocation_state':'waiting'})
									
								
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
									self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':rough_grinding_qty,'inward_accept_qty': rough_grinding_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'rough_grinding_date':time.strftime('%Y-%m-%d'),'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,'rough_grinding_name':rough_grinding_name[0],'allocated_qty':rough_grinding_qty,'flag_allocated':'t','allocated_accepted_qty':rough_grinding_qty,'allocation_state':'waiting'})
									
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
									self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':finish_grinding_qty,'inward_accept_qty': finish_grinding_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'finish_grinding_date':time.strftime('%Y-%m-%d'),'finish_grinding_qty': finish_grinding_qty,'finish_grinding_accept_qty': finish_grinding_qty,'finish_grinding_name':finish_grinding_name[0],'allocated_qty':finish_grinding_qty,'flag_allocated':'t','allocated_accepted_qty':finish_grinding_qty,'allocation_state':'waiting'})
									
									
									### Updation in STK WO ###
									stk_rem_qty =  stk_finish_grinding_qty - finish_grinding_qty
									if stk_rem_qty > 0:
										self.write(cr, uid, stk_item['id'], {'finish_grinding_qty': stk_rem_qty,'finish_grinding_accept_qty':stk_rem_qty})
									else:
										self.write(cr, uid, stk_item['id'], {'state':'complete'})
										
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
									self.write(cr, uid, fettling_id, {'state':'accept','pour_qty':reshot_blasting_qty,'inward_accept_qty': reshot_blasting_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'reshot_blasting_date':time.strftime('%Y-%m-%d'),'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0],'allocated_qty':reshot_blasting_qty,'flag_allocated':'t','allocated_accepted_qty':reshot_blasting_qty,'allocation_state':'waiting'})
							
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
								
					else:
						rem_qty = reject_rem_qty
					
					if rem_qty > 0:
				
						### Full Rejection Update ###
						full_reject_qty = rem_qty
						if full_reject_qty == 0:
							self.write(cr, uid, ids, {'state':'complete'})
							
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
					'stage_name': 'Stock Allocation',
					'qty': reject_qty,
					'reject_remarks_id': entry.allocation_reject_remarks_id.id
				}
				
				foundry_rejection_id = foundry_rejection_obj.create(cr, uid, rejection_vals)
			
			
			self.write(cr, uid, ids, {'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		
		return True
	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []  
		raise osv.except_osv(_('Warning!'),
				_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_fettling()

class kg_fettling_batch_accept(osv.osv):

	_name = "kg.fettling.batch.accept"
	_description = "Fettling Batch Accept"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Batch No.', size=128,select=True),
		'entry_date': fields.date('Batch Date',required=True),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed')],'Status', readonly=True),

		'fettling_line_ids':fields.many2many('kg.fettling','m2m_fettling_inward_details' , 'batch_id', 'fettling_id', 'Fettling Lines',
			domain="[('state','=','waiting')]"),
			
		'line_ids': fields.one2many('ch.fettling.batch.accept.line', 'header_id', "Fettling Line Details"),
		
		'flag_fettlingline':fields.boolean('Fettling Line Created'),
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),  
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),   
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_fettling_batch_accept', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft'
		
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.entry_date)
		if entry_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
  
	   ]	

	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])  
		fettling_obj = self.pool.get('kg.fettling')
		line_obj = self.pool.get('ch.fettling.batch.accept.line')
		
		del_sql = """ delete from ch_fettling_batch_accept_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.fettling_line_ids:
		
			for item in entry.fettling_line_ids:
				
				
				vals = {
				
					'header_id': entry.id,
					'fettling_id':item.id,
					'accept_qty':item.pour_qty,
					'reject_qty':0,
					'remarks':entry.remarks
				}
				
				line_id = line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_fettlingline': True})
			
		return True
		
	def entry_accept(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			fettling_obj = self.pool.get('kg.fettling')  
			if not entry.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to confirm without Line Items !!'))
							
							
			### Updation against Bactch Fettling Accept ###
			for accept_item in entry.line_ids:
				reject_qty = accept_item.pour_qty - accept_item.accept_qty
				if accept_item.reject_qty > 0 and accept_item.reject_remarks_id.id == False:
					raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
				
				fettling_obj.write(cr, uid,accept_item.fettling_id.id,{
				'inward_remarks':accept_item.remarks,
				'inward_accept_qty': accept_item.accept_qty,
				'inward_reject_qty': accept_item.reject_qty,
				'inward_accept_user_id': accept_item.accept_user_id.id,
				'inward_reject_remarks_id': accept_item.reject_remarks_id.id
				})
				fettling_obj.fettling_accept(cr, uid, [accept_item.fettling_id.id])
				
			### Sequence Number Generation  ###
			fettling_batch_name = ''	
			fettling_batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.fettling.batch.accept')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,fettling_batch_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(fettling_batch_seq_id[0],rec.code,entry.entry_date))
			fettling_batch_name = cr.fetchone();
			self.write(cr, uid, ids, {'name':fettling_batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_fettling_batch_accept, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []  
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_fettling_batch_accept()


class ch_fettling_batch_accept_line(osv.osv):

	_name = "ch.fettling.batch.accept.line"
	_description = "Fettling Batch Accept Line"
	
	_columns = {
	
		'header_id':fields.many2one('kg.fettling.batch.accept', 'Fettling Batch Accept', required=1, ondelete='cascade'),	 
		'fettling_id':fields.many2one('kg.fettling', 'Fettling'),
		
		'fettling_inward_no': fields.related('fettling_id','name', type='char', string='Fettling Inward No.', store=True, readonly=True),
		'pour_qty': fields.related('fettling_id','pour_qty', type='integer', size=100, string='Poured Qty', store=True, readonly=True),
		'accept_qty': fields.integer('Accepted Qty', required=True),
		'reject_qty': fields.integer('Rejected Qty'),
		'reject_user_id': fields.many2one('res.users', 'Rejected By'),
		'accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'remarks': fields.text('Remarks'),
		'reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		
		
	}
	
	_defaults = {
	
		'reject_user_id':lambda obj, cr, uid, context: uid,
		'accept_user_id':lambda obj, cr, uid, context: uid,
		
	}
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_fettling_batch_accept_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_fettling_batch_accept_line, self).write(cr, uid, ids, vals, context)
		
		
	
ch_fettling_batch_accept_line()



class kg_batch_knock_out(osv.osv):

	_name = "kg.batch.knock.out"
	_description = "Knock Out Batch"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Batch No.', size=128,select=True),
		'entry_date': fields.date('Batch Date',required=True),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed')],'Status', readonly=True),

		'knock_out_ids':fields.many2many('kg.fettling','m2m_knockout_details' , 'batch_id', 'knockout_id', 'Knockout Items',
			domain="[('stage_name','=','KNOCK OUT'),('state','=','accept'),('flag_ko_special_app','!=','t')]"),
			
		'line_ids': fields.one2many('ch.batch.knockout.line', 'header_id', "Batch Line Details"),
		
		'flag_batchline':fields.boolean('Batch Line Created'),
		
		'knockout_date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'employee_name': fields.char('Employee',size=128),
		'weight':fields.integer('Weight(kgs)'),
		

		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),  
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),   
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_batch_knock_out', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'knockout_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft'
		
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.entry_date)
		knockout_date = str(rec.knockout_date)
		if entry_date > today:
			return False
		if knockout_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
  
	   ]	

	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])  
		fettling_obj = self.pool.get('kg.fettling')
		line_obj = self.pool.get('ch.batch.knockout.line')
		
		del_sql = """ delete from ch_batch_knockout_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.knock_out_ids:
		
			for item in entry.knock_out_ids:
				
				
				vals = {
				
					'header_id': entry.id,
					'knockout_id':item.id,
					'qty': item.knockout_qty,
					'accept_qty': item.knockout_qty,
					'date': entry.knockout_date,
					'shift_id': entry.shift_id.id,
					'done_by': entry.done_by,
					'contractor_id': entry.contractor_id.id,
					'employee_name': entry.employee_name,
					'weight': entry.weight,
					'remarks':  entry.remarks
				}
				
				line_id = line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_batchline': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			fettling_obj = self.pool.get('kg.fettling')  
			if not entry.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to confirm without Line Items !!'))
							
							
			### Updation against Bactch Knock Out ###
			for item in entry.line_ids:
				reject_qty = item.qty - item.accept_qty
				if item.reject_qty > 0 and item.reject_remarks_id.id == False:
					raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
				
				fettling_obj.write(cr, uid,item.knockout_id.id,{
				'knockout_remarks':item.remarks,
				'knockout_accept_qty': item.accept_qty,
				'knockout_reject_qty': item.reject_qty,
				'knockout_accept_user_id': item.accept_user_id.id,
				'knockout_reject_remarks_id': item.reject_remarks_id.id,
				'knockout_date': item.date,
				'knockout_shift_id': item.shift_id.id,
				'knockout_contractor': item.contractor_id.id,
				'knockout_employee': item.employee_name,
				'knockout_by': item.done_by,
				'knockout_weight': item.weight,
				})
				fettling_obj.knockout_update(cr, uid, [item.knockout_id.id])
				
			### Sequence Number Generation  ###
			batch_name = '' 
			batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.batch.knock.out')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,batch_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(batch_seq_id[0],seq_rec.code,entry.entry_date))
			batch_name = cr.fetchone();
			self.write(cr, uid, ids, {'name':batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_batch_knock_out, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []  
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_batch_knock_out()


class ch_batch_knockout_line(osv.osv):

	_name = "ch.batch.knockout.line"
	_description = "Knock Out Batch Line"
	
	_columns = {
	
		'header_id':fields.many2one('kg.batch.knock.out', 'Header', required=1, ondelete='cascade'),		
		'knockout_id':fields.many2one('kg.fettling', 'Fettling'),
		'name': fields.related('knockout_id','knockout_name', type='char', string='Production Entry Code', store=True, readonly=True),
		'order_no': fields.related('knockout_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'pattern_id': fields.related('knockout_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('knockout_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('knockout_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'qty': fields.integer('Total Qty'),
		'accept_qty': fields.integer('Accepted Qty'),
		'reject_qty': fields.integer('Rejected Qty'),
		'weight':fields.integer('Weight(kgs)'),
		'remarks': fields.text('Remarks'),
		'reject_user_id': fields.many2one('res.users', 'Rejected By'),
		'accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'employee_name': fields.char('Employee',size=128),
		'reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		
		
	}
	
	_defaults = {
		
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
		'reject_user_id':lambda obj, cr, uid, context: uid,
		'accept_user_id':lambda obj, cr, uid, context: uid,
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.date)
		if entry_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['Line Items']),
  
	   ]
	
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_batch_knockout_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_batch_knockout_line, self).write(cr, uid, ids, vals, context)
		
		
	
ch_batch_knockout_line()



class kg_batch_decoring(osv.osv):

	_name = "kg.batch.decoring"
	_description = "Decoring Batch"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Batch No.', size=128,select=True),
		'entry_date': fields.date('Batch Date',required=True),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed')],'Status', readonly=True),

		'decoring_ids':fields.many2many('kg.fettling','m2m_decoring_details' , 'batch_id', 'decoring_id', 'Decoring Items',
			domain="[('stage_name','=','DECORING'),('state','=','accept')]"),
			
		'line_ids': fields.one2many('ch.batch.decoring.line', 'header_id', "Batch Line Details"),
		
		'flag_batchline':fields.boolean('Batch Line Created'),
		
		'decoring_date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'employee_name': fields.char('Employee',size=128),
		'weight':fields.integer('Weight(kgs)'),

		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),  
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),   
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_batch_decoring', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'decoring_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft'
		
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.entry_date)
		decoring_date = str(rec.decoring_date)
		if entry_date > today:
			return False
		if decoring_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
  
	   ]	

	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])  
		fettling_obj = self.pool.get('kg.fettling')
		line_obj = self.pool.get('ch.batch.decoring.line')
		
		del_sql = """ delete from ch_batch_decoring_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.decoring_ids:
		
			for item in entry.decoring_ids:
				
				
				vals = {
				
					'header_id': entry.id,
					'decoring_id':item.id,
					'qty': item.decoring_qty,
					'accept_qty': item.decoring_qty,
					'date': entry.decoring_date,
					'shift_id': entry.shift_id.id,
					'done_by': entry.done_by,
					'contractor_id': entry.contractor_id.id,
					'employee_name': entry.employee_name,
					'weight': entry.weight,
					'remarks':  entry.remarks
				}
				
				line_id = line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_batchline': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			fettling_obj = self.pool.get('kg.fettling')  
			if not entry.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to confirm without Line Items !!'))
							
							
			### Updation against Bactch Decoring ###
			for item in entry.line_ids:
				reject_qty = item.qty - item.accept_qty
				if item.reject_qty > 0 and item.reject_remarks_id.id == False:
					raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
				
				fettling_obj.write(cr, uid,item.decoring_id.id,{
				'decoring_remarks':item.remarks,
				'decoring_accept_qty': item.accept_qty,
				'decoring_reject_qty': item.reject_qty,
				'decoring_accept_user_id': item.accept_user_id.id,
				'decoring_reject_remarks_id': item.reject_remarks_id.id,
				'decoring_date': item.date,
				'decoring_shift_id': item.shift_id.id,
				'decoring_contractor': item.contractor_id.id,
				'decoring_employee': item.employee_name,
				'decoring_by': item.done_by,
				'decoring_weight': item.weight,
				})
				fettling_obj.decoring_update(cr, uid, [item.decoring_id.id])
				
			### Sequence Number Generation  ###
			batch_name = '' 
			batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.batch.decoring')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,batch_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(batch_seq_id[0],seq_rec.code,entry.entry_date))
			batch_name = cr.fetchone();
			self.write(cr, uid, ids, {'name':batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_batch_decoring, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []  
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_batch_decoring()


class ch_batch_decoring_line(osv.osv):

	_name = "ch.batch.decoring.line"
	_description = "Decoring Batch Line"
	
	_columns = {
	
		'header_id':fields.many2one('kg.batch.decoring', 'Header', required=1, ondelete='cascade'),  
		'decoring_id':fields.many2one('kg.fettling', 'Fettling'),
		'name': fields.related('decoring_id','decoring_name', type='char', string='Production Entry Code', store=True, readonly=True),
		'order_no': fields.related('decoring_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'pattern_id': fields.related('decoring_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('decoring_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('decoring_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'qty': fields.integer('Total Qty'),
		'accept_qty': fields.integer('Accepted Qty'),
		'reject_qty': fields.integer('Rejected Qty'),
		'weight':fields.integer('Weight(kgs)'),
		'remarks': fields.text('Remarks'),
		'reject_user_id': fields.many2one('res.users', 'Rejected By'),
		'accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'employee_name': fields.char('Employee',size=128),
		'reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),   
		
		
	}
	
	_defaults = {
		
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
		'reject_user_id':lambda obj, cr, uid, context: uid,
		'accept_user_id':lambda obj, cr, uid, context: uid,
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.date)
		if entry_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['Line Items']),
  
	   ]
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_batch_decoring_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_batch_decoring_line, self).write(cr, uid, ids, vals, context)
		
		
	
ch_batch_decoring_line()


class kg_batch_shot_blast(osv.osv):

	_name = "kg.batch.shot.blast"
	_description = "Shot Blast Batch"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Batch No.', size=128,select=True),
		'entry_date': fields.date('Batch Date',required=True),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed')],'Status', readonly=True),

		'shot_blast_ids':fields.many2many('kg.fettling','m2m_shot_blast_details' , 'batch_id', 'shot_blast_id', 'Shot Blast Items',
			domain="[('stage_name','=','SHOT BLAST'),('state','=','accept')]"),
			
		'line_ids': fields.one2many('ch.batch.shot.blast.line', 'header_id', "Batch Line Details"),
		
		'flag_batchline':fields.boolean('Batch Line Created'),
		
		'shot_blast_date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'employee_name': fields.char('Employee',size=128),
		'weight':fields.integer('Weight(kgs)'),

		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),  
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),   
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_batch_shot_blast', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'shot_blast_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft'
		
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.entry_date)
		shot_blast_date = str(rec.shot_blast_date)
		if entry_date > today:
			return False
		if shot_blast_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
  
	   ]		

	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])  
		fettling_obj = self.pool.get('kg.fettling')
		line_obj = self.pool.get('ch.batch.shot.blast.line')
		
		del_sql = """ delete from ch_batch_shot_blast_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.shot_blast_ids:
		
			for item in entry.shot_blast_ids:
				
				
				vals = {
				
					'header_id': entry.id,
					'shot_blast_id':item.id,
					'qty': item.shot_blast_qty,
					'accept_qty': item.shot_blast_qty,
					'date': entry.shot_blast_date,
					'shift_id': entry.shift_id.id,
					'done_by': entry.done_by,
					'contractor_id': entry.contractor_id.id,
					'employee_name': entry.employee_name,
					'weight': entry.weight,
					'remarks':  entry.remarks
				}
				
				line_id = line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_batchline': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			fettling_obj = self.pool.get('kg.fettling')  
			if not entry.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to confirm without Line Items !!'))
							
							
			### Updation against Bactch Shot Blast ###
			for item in entry.line_ids:
				reject_qty = item.qty - item.accept_qty
				if item.reject_qty > 0 and item.reject_remarks_id.id == False:
					raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
				
				fettling_obj.write(cr, uid,item.shot_blast_id.id,{
				'shot_blast_remarks':item.remarks,
				'shot_blast_accept_qty': item.accept_qty,
				'shot_blast_reject_qty': item.reject_qty,
				'shot_blast_accept_user_id': item.accept_user_id.id,
				'shot_blast_reject_remarks_id': item.reject_remarks_id.id,
				'shot_blast_date': item.date,
				'shot_blast_shift_id': item.shift_id.id,
				'shot_blast_contractor': item.contractor_id.id,
				'shot_blast_employee': item.employee_name,
				'shot_blast_by': item.done_by,
				'shot_blast_weight': item.weight,
				})
				fettling_obj.shot_blast_update(cr, uid, [item.shot_blast_id.id])
				
			### Sequence Number Generation  ###
			batch_name = '' 
			batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.batch.shot.blast')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,batch_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(batch_seq_id[0],seq_rec.code,entry.entry_date))
			batch_name = cr.fetchone();
			self.write(cr, uid, ids, {'name':batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_batch_shot_blast, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []  
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_batch_shot_blast()


class ch_batch_shot_blast_line(osv.osv):

	_name = "ch.batch.shot.blast.line"
	_description = "Shot Blast Batch Line"
	
	_columns = {
	
		'header_id':fields.many2one('kg.batch.shot.blast', 'Header', required=1, ondelete='cascade'),	 
		'shot_blast_id':fields.many2one('kg.fettling', 'Fettling'),
		'name': fields.related('shot_blast_id','shot_blast_name', type='char', string='Production Entry Code', store=True, readonly=True),
		'order_no': fields.related('shot_blast_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'pattern_id': fields.related('shot_blast_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('shot_blast_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('shot_blast_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'qty': fields.integer('Total Qty'),
		'accept_qty': fields.integer('Accepted Qty'),
		'reject_qty': fields.integer('Rejected Qty'),
		'weight':fields.integer('Weight(kgs)'),
		'remarks': fields.text('Remarks'),
		'reject_user_id': fields.many2one('res.users', 'Rejected By'),
		'accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'employee_name': fields.char('Employee',size=128),
		'reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		
		
	}
	
	_defaults = {
		
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
		'reject_user_id':lambda obj, cr, uid, context: uid,
		'accept_user_id':lambda obj, cr, uid, context: uid,
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.date)
		if entry_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['Line Items']),
  
	   ]
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_batch_shot_blast_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_batch_shot_blast_line, self).write(cr, uid, ids, vals, context)
		
		
	
ch_batch_shot_blast_line()

class kg_batch_hammering(osv.osv):

	_name = "kg.batch.hammering"
	_description = "Hammering Batch"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Batch No.', size=128,select=True),
		'entry_date': fields.date('Batch Date',required=True),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed')],'Status', readonly=True),

		'hammering_ids':fields.many2many('kg.fettling','m2m_hammering_details' , 'batch_id', 'hammering_id', 'Hammering Items',
			domain="[('stage_name','=','HAMMERING'),('state','=','accept')]"),
			
		'line_ids': fields.one2many('ch.batch.hammering.line', 'header_id', "Batch Line Details"),
		
		'flag_batchline':fields.boolean('Batch Line Created'),
		
		'hammering_date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'employee_name': fields.char('Employee',size=128),
		'weight':fields.integer('Weight(kgs)'),

		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),  
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),   
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_batch_hammering', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'hammering_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft'
		
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.entry_date)
		hammering_date = str(rec.hammering_date)
		if entry_date > today:
			return False
		if hammering_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
  
	   ]		

	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])  
		fettling_obj = self.pool.get('kg.fettling')
		line_obj = self.pool.get('ch.batch.hammering.line')
		
		del_sql = """ delete from ch_batch_hammering_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.hammering_ids:
		
			for item in entry.hammering_ids:
				
				
				vals = {
				
					'header_id': entry.id,
					'hammering_id':item.id,
					'qty': item.hammering_qty,
					'accept_qty': item.hammering_qty,
					'date': entry.hammering_date,
					'shift_id': entry.shift_id.id,
					'done_by': entry.done_by,
					'contractor_id': entry.contractor_id.id,
					'employee_name': entry.employee_name,
					'weight': entry.weight,
					'remarks':  entry.remarks
				}
				
				line_id = line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_batchline': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			fettling_obj = self.pool.get('kg.fettling')  
			if not entry.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to confirm without Line Items !!'))
							
							
			### Updation against Bactch Hammering ###
			for item in entry.line_ids:
				reject_qty = item.qty - item.accept_qty
				if item.reject_qty > 0 and item.reject_remarks_id.id == False:
					raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
				
				fettling_obj.write(cr, uid,item.hammering_id.id,{
				'hammering_remarks':item.remarks,
				'hammering_accept_qty': item.accept_qty,
				'hammering_reject_qty': item.reject_qty,
				'hammering_accept_user_id': item.accept_user_id.id,
				'hammering_reject_remarks_id': item.reject_remarks_id.id,
				'hammering_date': item.date,
				'hammering_shift_id': item.shift_id.id,
				'hammering_contractor': item.contractor_id.id,
				'hammering_employee': item.employee_name,
				'hammering_by': item.done_by,
				'hammering_weight': item.weight,
				})
				fettling_obj.hammering_update(cr, uid, [item.hammering_id.id])
				
			### Sequence Number Generation  ###
			batch_name = '' 
			batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.batch.hammering')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,batch_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(batch_seq_id[0],seq_rec.code,entry.entry_date))
			batch_name = cr.fetchone();
			self.write(cr, uid, ids, {'name':batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_batch_hammering, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []  
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_batch_hammering()


class ch_batch_hammering_line(osv.osv):

	_name = "ch.batch.hammering.line"
	_description = "Hammering Batch Line"
	
	_columns = {
	
		'header_id':fields.many2one('kg.batch.hammering', 'Header', required=1, ondelete='cascade'),		
		'hammering_id':fields.many2one('kg.fettling', 'Fettling'),
		'name': fields.related('hammering_id','hammering_name', type='char', string='Production Entry Code', store=True, readonly=True),
		'order_no': fields.related('hammering_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'pattern_id': fields.related('hammering_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('hammering_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('hammering_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'qty': fields.integer('Total Qty'),
		'accept_qty': fields.integer('Accepted Qty'),
		'reject_qty': fields.integer('Rejected Qty'),
		'weight':fields.integer('Weight(kgs)'),
		'remarks': fields.text('Remarks'),
		'reject_user_id': fields.many2one('res.users', 'Rejected By'),
		'accept_user_id': fields.many2one('res.users', 'Accepted By'),  
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'employee_name': fields.char('Employee',size=128),
		'reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		
		
	}
	
	_defaults = {
		
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
		'reject_user_id':lambda obj, cr, uid, context: uid,
		'accept_user_id':lambda obj, cr, uid, context: uid,
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.date)
		if entry_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['Line Items']),
  
	   ]
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_batch_hammering_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_batch_hammering_line, self).write(cr, uid, ids, vals, context)
		
		
	
ch_batch_hammering_line()


class kg_batch_wheel_cutting(osv.osv):

	_name = "kg.batch.wheel.cutting"
	_description = "Wheel Cutting Batch"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Batch No.', size=128,select=True),
		'entry_date': fields.date('Batch Date',required=True),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed')],'Status', readonly=True),

		'wheel_cutting_ids':fields.many2many('kg.fettling','m2m_wheel_cutting_details' , 'batch_id', 'wheel_cutting_id', 'Wheel Cutting Items',
			domain="[('stage_name','=','WHEEL CUTTING'),('state','=','accept')]"),
			
		'line_ids': fields.one2many('ch.batch.wheel.cutting.line', 'header_id', "Batch Line Details"),
		
		'flag_batchline':fields.boolean('Batch Line Created'),
		
		'wheel_cutting_date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'employee_name': fields.char('Employee',size=128),
		'weight':fields.integer('Weight(kgs)'),

		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),  
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),   
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_batch_wheel_cutting', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'wheel_cutting_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft'
		
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.entry_date)
		wheel_cutting_date = str(rec.wheel_cutting_date)
		if entry_date > today:
			return False
		if wheel_cutting_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
  
	   ]	

	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])  
		fettling_obj = self.pool.get('kg.fettling')
		line_obj = self.pool.get('ch.batch.wheel.cutting.line')
		
		del_sql = """ delete from ch_batch_wheel_cutting_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.wheel_cutting_ids:
		
			for item in entry.wheel_cutting_ids:
				
				
				vals = {
				
					'header_id': entry.id,
					'wheel_cutting_id':item.id,
					'qty': item.wheel_cutting_qty,
					'accept_qty': item.wheel_cutting_qty,
					'date': entry.wheel_cutting_date,
					'shift_id': entry.shift_id.id,
					'done_by': entry.done_by,
					'contractor_id': entry.contractor_id.id,
					'employee_name': entry.employee_name,
					'weight': entry.weight,
					'remarks':  entry.remarks
				}
				
				line_id = line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_batchline': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			fettling_obj = self.pool.get('kg.fettling')  
			if not entry.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to confirm without Line Items !!'))
							
							
			### Updation against Bactch Wheel Cutting ###
			for item in entry.line_ids:
				reject_qty = item.qty - item.accept_qty
				if item.reject_qty > 0 and item.reject_remarks_id.id == False:
					raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
				
				fettling_obj.write(cr, uid,item.wheel_cutting_id.id,{
				'wheel_cutting_remarks':item.remarks,
				'wheel_cutting_accept_qty': item.accept_qty,
				'wheel_cutting_reject_qty': item.reject_qty,
				'wheel_cutting_accept_user_id': item.accept_user_id.id,
				'wheel_cutting_reject_remarks_id': item.reject_remarks_id.id,
				'wheel_cutting_date': item.date,
				'wheel_cutting_shift_id': item.shift_id.id,
				'wheel_cutting_contractor': item.contractor_id.id,
				'wheel_cutting_employee': item.employee_name,
				'wheel_cutting_by': item.done_by,
				'wheel_cutting_weight': item.weight,
				})
				fettling_obj.wheel_cutting_update(cr, uid, [item.wheel_cutting_id.id])
				
			### Sequence Number Generation  ###
			batch_name = '' 
			batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.batch.wheel.cutting')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,batch_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(batch_seq_id[0],seq_rec.code,entry.entry_date))
			batch_name = cr.fetchone();
			self.write(cr, uid, ids, {'name':batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_batch_wheel_cutting, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []  
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_batch_wheel_cutting()


class ch_batch_wheel_cutting_line(osv.osv):

	_name = "ch.batch.wheel.cutting.line"
	_description = "Wheel Cutting Batch Line"
	
	_columns = {
	
		'header_id':fields.many2one('kg.batch.wheel.cutting', 'Header', required=1, ondelete='cascade'),		
		'wheel_cutting_id':fields.many2one('kg.fettling', 'Fettling'),
		'name': fields.related('wheel_cutting_id','wheel_cutting_name', type='char', string='Production Entry Code', store=True, readonly=True),
		'order_no': fields.related('wheel_cutting_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'pattern_id': fields.related('wheel_cutting_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('wheel_cutting_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('wheel_cutting_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'qty': fields.integer('Total Qty'),
		'accept_qty': fields.integer('Accepted Qty'),
		'reject_qty': fields.integer('Rejected Qty'),
		'weight':fields.integer('Weight(kgs)'),
		'remarks': fields.text('Remarks'),
		'reject_user_id': fields.many2one('res.users', 'Rejected By'),
		'accept_user_id': fields.many2one('res.users', 'Accepted By'),  
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'employee_name': fields.char('Employee',size=128),
		'reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		
		
	}
	
	_defaults = {
		
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
		'reject_user_id':lambda obj, cr, uid, context: uid,
		'accept_user_id':lambda obj, cr, uid, context: uid,
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.date)
		if entry_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['Line Items']),
  
	   ]
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_batch_wheel_cutting_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_batch_wheel_cutting_line, self).write(cr, uid, ids, vals, context)
		
		
	
ch_batch_wheel_cutting_line()


class kg_batch_gas_cutting(osv.osv):

	_name = "kg.batch.gas.cutting"
	_description = "Gas Cutting Batch"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Batch No.', size=128,select=True),
		'entry_date': fields.date('Batch Date',required=True),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed')],'Status', readonly=True),

		'gas_cutting_ids':fields.many2many('kg.fettling','m2m_gas_cutting_details' , 'batch_id', 'gas_cutting_id', 'gas Cutting Items',
			domain="[('stage_name','=','GAS CUTTING'),('state','=','accept')]"),
			
		'line_ids': fields.one2many('ch.batch.gas.cutting.line', 'header_id', "Batch Line Details"),
		
		'flag_batchline':fields.boolean('Batch Line Created'),
		
		'gas_cutting_date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'employee_name': fields.char('Employee',size=128),
		'weight':fields.integer('Weight(kgs)'),

		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),  
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),   
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_batch_gas_cutting', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'gas_cutting_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft'
		
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.entry_date)
		gas_cutting_date = str(rec.gas_cutting_date)
		if entry_date > today:
			return False
		if gas_cutting_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
  
	   ]		

	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])  
		fettling_obj = self.pool.get('kg.fettling')
		line_obj = self.pool.get('ch.batch.gas.cutting.line')
		
		del_sql = """ delete from ch_batch_gas_cutting_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.gas_cutting_ids:
		
			for item in entry.gas_cutting_ids:
				
				
				vals = {
				
					'header_id': entry.id,
					'gas_cutting_id':item.id,
					'qty': item.gas_cutting_qty,
					'accept_qty': item.gas_cutting_qty,
					'date': entry.gas_cutting_date,
					'shift_id': entry.shift_id.id,
					'done_by': entry.done_by,
					'contractor_id': entry.contractor_id.id,
					'employee_name': entry.employee_name,
					'weight': entry.weight,
					'remarks':  entry.remarks
				}
				
				line_id = line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_batchline': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			fettling_obj = self.pool.get('kg.fettling')  
			if not entry.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to confirm without Line Items !!'))
							
							
			### Updation against Bactch Gas Cutting ###
			for item in entry.line_ids:
				reject_qty = item.qty - item.accept_qty
				if item.reject_qty > 0 and item.reject_remarks_id.id == False:
					raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
				
				fettling_obj.write(cr, uid,item.gas_cutting_id.id,{
				'gas_cutting_remarks':item.remarks,
				'gas_cutting_accept_qty': item.accept_qty,
				'gas_cutting_reject_qty': item.reject_qty,
				'gas_cutting_accept_user_id': item.accept_user_id.id,
				'gas_cutting_reject_remarks_id': item.reject_remarks_id.id,
				'gas_cutting_date': item.date,
				'gas_cutting_shift_id': item.shift_id.id,
				'gas_cutting_contractor': item.contractor_id.id,
				'gas_cutting_employee': item.employee_name,
				'gas_cutting_by': item.done_by,
				'gas_cutting_weight': item.weight,
				})
				fettling_obj.gas_cutting_update(cr, uid, [item.gas_cutting_id.id])
				
			### Sequence Number Generation  ###
			batch_name = '' 
			batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.batch.gas.cutting')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,batch_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(batch_seq_id[0],seq_rec.code,entry.entry_date))
			batch_name = cr.fetchone();
			self.write(cr, uid, ids, {'name':batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_batch_gas_cutting, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []  
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_batch_gas_cutting()


class ch_batch_gas_cutting_line(osv.osv):

	_name = "ch.batch.gas.cutting.line"
	_description = "Gas Cutting Batch Line"
	
	_columns = {
	
		'header_id':fields.many2one('kg.batch.gas.cutting', 'Header', required=1, ondelete='cascade'),  
		'gas_cutting_id':fields.many2one('kg.fettling', 'Fettling'),
		'name': fields.related('gas_cutting_id','gas_cutting_name', type='char', string='Production Entry Code', store=True, readonly=True),
		'order_no': fields.related('gas_cutting_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'pattern_id': fields.related('gas_cutting_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('gas_cutting_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('gas_cutting_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'qty': fields.integer('Total Qty'),
		'accept_qty': fields.integer('Accepted Qty'),
		'reject_qty': fields.integer('Rejected Qty'),
		'weight':fields.integer('Weight(kgs)'),
		'remarks': fields.text('Remarks'),
		'reject_user_id': fields.many2one('res.users', 'Rejected By'),
		'accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'employee_name': fields.char('Employee',size=128),
		'reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),   
		
		
	}
	
	_defaults = {
		
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
		'reject_user_id':lambda obj, cr, uid, context: uid,
		'accept_user_id':lambda obj, cr, uid, context: uid,
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.date)
		if entry_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['Line Items']),
  
	   ]
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_batch_gas_cutting_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_batch_gas_cutting_line, self).write(cr, uid, ids, vals, context)
		
		
	
ch_batch_gas_cutting_line()

class kg_batch_arc_cutting(osv.osv):

	_name = "kg.batch.arc.cutting"
	_description = "Arc Cutting Batch"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Batch No.', size=128,select=True),
		'entry_date': fields.date('Batch Date',required=True),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed')],'Status', readonly=True),

		'arc_cutting_ids':fields.many2many('kg.fettling','m2m_arc_cutting_details' , 'batch_id', 'arc_cutting_id', 'Arc Cutting Items',
			domain="[('stage_name','=','ARC CUTTING'),('state','=','accept')]"),
			
		'line_ids': fields.one2many('ch.batch.arc.cutting.line', 'header_id', "Batch Line Details"),
		
		'flag_batchline':fields.boolean('Batch Line Created'),
		
		'arc_cutting_date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'employee_name': fields.char('Employee',size=128),
		'weight':fields.integer('Weight(kgs)'),

		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),  
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),   
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_batch_arc_cutting', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'arc_cutting_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft'
		
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.entry_date)
		arc_cutting_date = str(rec.arc_cutting_date)
		if entry_date > today:
			return False
		if arc_cutting_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
  
	   ]	

	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])  
		fettling_obj = self.pool.get('kg.fettling')
		line_obj = self.pool.get('ch.batch.arc.cutting.line')
		
		del_sql = """ delete from ch_batch_arc_cutting_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.arc_cutting_ids:
		
			for item in entry.arc_cutting_ids:
				
				
				vals = {
				
					'header_id': entry.id,
					'arc_cutting_id':item.id,
					'qty': item.arc_cutting_qty,
					'accept_qty': item.arc_cutting_qty,
					'date': entry.arc_cutting_date,
					'shift_id': entry.shift_id.id,
					'done_by': entry.done_by,
					'contractor_id': entry.contractor_id.id,
					'employee_name': entry.employee_name,
					'weight': entry.weight,
					'remarks':  entry.remarks
				}
				
				line_id = line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_batchline': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			fettling_obj = self.pool.get('kg.fettling')  
			if not entry.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to confirm without Line Items !!'))
							
							
			### Updation against Bactch Arc Cutting ###
			for item in entry.line_ids:
				reject_qty = item.qty - item.accept_qty
				if item.reject_qty > 0 and item.reject_remarks_id.id == False:
					raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
				
				fettling_obj.write(cr, uid,item.arc_cutting_id.id,{
				'arc_cutting_remarks':item.remarks,
				'arc_cutting_accept_qty': item.accept_qty,
				'arc_cutting_reject_qty': item.reject_qty,
				'arc_cutting_accept_user_id': item.accept_user_id.id,
				'arc_cutting_reject_remarks_id': item.reject_remarks_id.id,
				'arc_cutting_date': item.date,
				'arc_cutting_shift_id': item.shift_id.id,
				'arc_cutting_contractor': item.contractor_id.id,
				'arc_cutting_employee': item.employee_name,
				'arc_cutting_by': item.done_by,
				'arc_cutting_weight': item.weight,
				})
				fettling_obj.arc_cutting_update(cr, uid, [item.arc_cutting_id.id])
				
			### Sequence Number Generation  ###
			batch_name = '' 
			batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.batch.arc.cutting')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,batch_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(batch_seq_id[0],seq_rec.code,entry.entry_date))
			batch_name = cr.fetchone();
			self.write(cr, uid, ids, {'name':batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_batch_arc_cutting, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []  
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_batch_arc_cutting()


class ch_batch_arc_cutting_line(osv.osv):

	_name = "ch.batch.arc.cutting.line"
	_description = "Arc Cutting Batch Line"
	
	_columns = {
	
		'header_id':fields.many2one('kg.batch.arc.cutting', 'Header', required=1, ondelete='cascade'),  
		'arc_cutting_id':fields.many2one('kg.fettling', 'Fettling'),
		'name': fields.related('arc_cutting_id','arc_cutting_name', type='char', string='Production Entry Code', store=True, readonly=True),
		'order_no': fields.related('arc_cutting_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'pattern_id': fields.related('arc_cutting_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('arc_cutting_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('arc_cutting_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'qty': fields.integer('Total Qty'),
		'accept_qty': fields.integer('Accepted Qty'),
		'reject_qty': fields.integer('Rejected Qty'),
		'weight':fields.integer('Weight(kgs)'),
		'remarks': fields.text('Remarks'),
		'reject_user_id': fields.many2one('res.users', 'Rejected By'),
		'accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'employee_name': fields.char('Employee',size=128),
		'reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),   
		
		
	}
	
	_defaults = {
		
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
		'reject_user_id':lambda obj, cr, uid, context: uid,
		'accept_user_id':lambda obj, cr, uid, context: uid,
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.date)
		if entry_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['Line Items']),
  
	   ]
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_batch_arc_cutting_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_batch_arc_cutting_line, self).write(cr, uid, ids, vals, context)
		
		
	
ch_batch_arc_cutting_line()


class kg_batch_heat_treatment(osv.osv):

	_name = "kg.batch.heat.treatment"
	_description = "Heat Treatment Batch"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Batch No.', size=128,select=True),
		'entry_date': fields.date('Batch Date',required=True),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed')],'Status', readonly=True),

		'heat_treatment_ids':fields.many2many('kg.fettling','m2m_heat_treatment_details' , 'batch_id', 'heat_treatment_id', 'Heat Treatment Items',
			domain="[('stage_name','=','HEAT TREATMENT'),('state','=','accept')]"),
			
		'line_ids': fields.one2many('ch.batch.heat.treatment.line', 'header_id', "Batch Line Details"),
		
		'flag_batchline':fields.boolean('Batch Line Created'),
		
		'heat_cycle_no':fields.char('Heat Cycle No.', size=128),
		'heat_treatment_date': fields.date('Date',required=True),
		'heat_specification':fields.char('Specification', size=128),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'employee_name': fields.char('Employee',size=128),
		'each_weight':fields.integer('Each Weight(kgs)'),
		
		
		'heat_fc_temp':fields.char('F/c initial temperature', size=128),
		'heat_fc_off_time': fields.float('F/c switch off at'),
		'heat_furnace_on_time': fields.float('Furnace switched on time'),
		'heat_treatment_type':fields.char('Treatment type', size=128),
		'heat_cooling_type':fields.char('Cooling type', size=128),
		'heat_set_temp':fields.char('Set temperature', size=128),
		'heat_set_temp_time':fields.float('Set temperature reached on (hrs.)'),
		'heat_socking_hr':fields.char('Socking hours(hrs.)', size=128),
		'heat_socking_comp_time':fields.float('Socking completed at(hrs.)'),
		'heat_quenc_time':fields.integer('Quenching time(Sec.)'),
		'heat_quencing_before_temp':fields.char('Quenching temp Before', size=128),
		'heat_quencing_after_temp':fields.char('Quenching temp After', size=128),
		'heat_chloride_content':fields.char('Chloride Content', size=128),
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),  
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),   
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_batch_heat_treatment', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'heat_treatment_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft'
		
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.entry_date)
		heat_treatment_date = str(rec.heat_treatment_date)
		if entry_date > today:
			return False
		if heat_treatment_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
  
	   ]	

	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])  
		fettling_obj = self.pool.get('kg.fettling')
		line_obj = self.pool.get('ch.batch.heat.treatment.line')
		
		del_sql = """ delete from ch_batch_heat_treatment_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.heat_treatment_ids:
		
			for item in entry.heat_treatment_ids:
				
				
				vals = {
				
					'header_id': entry.id,
					'heat_treatment_id':item.id,
					'qty': item.heat_total_qty,
					'accept_qty': item.heat_total_qty,
					'date': entry.heat_treatment_date,
					'done_by': entry.done_by,
					'contractor_id': entry.contractor_id.id,
					'employee_name': entry.employee_name,
					'each_weight': entry.each_weight,
					'remarks':  entry.remarks,
					'heat_cycle_no': entry.heat_cycle_no,
					'heat_specification': entry.heat_specification,
					'heat_fc_temp':entry.heat_fc_temp,
					'heat_fc_off_time': entry.heat_fc_off_time,
					'heat_furnace_on_time': entry.heat_furnace_on_time,
					'heat_treatment_type': entry.heat_treatment_type,
					'heat_cooling_type': entry.heat_cooling_type,
					'heat_set_temp': entry.heat_set_temp,
					'heat_set_temp_time': entry.heat_set_temp_time,
					'heat_socking_hr': entry.heat_socking_hr,
					'heat_socking_comp_time': entry.heat_socking_comp_time,
					'heat_quenc_time': entry.heat_quenc_time,
					'heat_quencing_before_temp': entry.heat_quencing_before_temp,
					'heat_quencing_after_temp': entry.heat_quencing_after_temp,
					'heat_chloride_content': entry.heat_chloride_content,
				}
				
				
				
				line_id = line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_batchline': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			fettling_obj = self.pool.get('kg.fettling')  
			if not entry.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to confirm without Line Items !!'))
							
							
			### Updation against Bactch Heat Treatment ###
			for item in entry.line_ids:
				#~ reject_qty = item.qty - item.accept_qty
				#~ if item.reject_qty > 0 and item.reject_remarks_id.id == False:
					#~ raise osv.except_osv(_('Warning!'),
					#~ _('Remarks is must for Rejection !!'))
				
				fettling_obj.write(cr, uid,item.heat_treatment_id.id,{
				'heat_remarks':item.remarks,
				'heat_qty': item.accept_qty,
				'heat_reject_qty': item.reject_qty,
				'heat_reject_remarks_id': item.reject_remarks_id.id,
				'heat_date': item.date,
				'heat_contractor': item.contractor_id.id,
				'heat_employee': item.employee_name,
				'heat_by': item.done_by,
				'heat_each_weight': item.each_weight,
				'heat_cycle_no': item.heat_cycle_no,
				'heat_specification': item.heat_specification,
				'heat_fc_temp':item.heat_fc_temp,
				'heat_fc_off_time': item.heat_fc_off_time,
				'heat_furnace_on_time': item.heat_furnace_on_time,
				'heat_treatment_type': item.heat_treatment_type,
				'heat_cooling_type': item.heat_cooling_type,
				'heat_set_temp': item.heat_set_temp,
				'heat_set_temp_time': item.heat_set_temp_time,
				'heat_socking_hr': item.heat_socking_hr,
				'heat_socking_comp_time': item.heat_socking_comp_time,
				'heat_quenc_time': item.heat_quenc_time,
				'heat_quencing_before_temp': item.heat_quencing_before_temp,
				'heat_quencing_after_temp': item.heat_quencing_after_temp,
				'heat_chloride_content': item.heat_chloride_content,
				})
				fettling_obj.heat_treatment_update(cr, uid, [item.heat_treatment_id.id])
				
			### Sequence Number Generation  ###
			batch_name = '' 
			batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.batch.heat.treatment')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,batch_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(batch_seq_id[0],seq_rec.code,entry.entry_date))
			batch_name = cr.fetchone();
			self.write(cr, uid, ids, {'name':batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_batch_heat_treatment, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []  
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_batch_heat_treatment()


class ch_batch_heat_treatment_line(osv.osv):

	_name = "ch.batch.heat.treatment.line"
	_description = "Heat Treatment Batch Line"
	
	_columns = {
	
		'header_id':fields.many2one('kg.batch.heat.treatment', 'Header', required=1, ondelete='cascade'),	 
		'heat_treatment_id':fields.many2one('kg.fettling', 'Fettling'),
		'order_no': fields.related('heat_treatment_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'pattern_id': fields.related('heat_treatment_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('heat_treatment_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('heat_treatment_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'date': fields.date('Date', store=True, required=True),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'qty': fields.integer('Total Qty'),
		'accept_qty': fields.integer('Accepted Qty'),
		'reject_qty': fields.integer('Rejected Qty'),
		'reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'each_weight':fields.integer('Each Weight(kgs)'),
		'remarks': fields.text('Remarks'),
		'accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'employee_name': fields.char('Employee',size=128),
		'heat_cycle_no':fields.char('Heat Cycle No.', size=128),
		'heat_specification':fields.char('Specification', size=128),
		
		'heat_fc_temp':fields.char('F/c initial temperature', size=128),
		'heat_fc_off_time': fields.float('F/c switch off at'),
		'heat_furnace_on_time': fields.float('Furnace switched on time'),
		'heat_treatment_type':fields.char('Treatment type', size=128),
		'heat_cooling_type':fields.char('Cooling type', size=128),
		'heat_set_temp':fields.char('Set temperature', size=128),
		'heat_set_temp_time':fields.float('Set temperature reached on (hrs.)'),
		'heat_socking_hr':fields.char('Socking hours(hrs.)', size=128),
		'heat_socking_comp_time':fields.float('Socking completed at(hrs.)'),
		'heat_quenc_time':fields.integer('Quenching time(Sec.)'),
		'heat_quencing_before_temp':fields.char('Quenching temp Before', size=128),
		'heat_quencing_after_temp':fields.char('Quenching temp After', size=128),
		'heat_chloride_content':fields.char('Chloride Content', size=128),
			
		
		
	}
	
	_defaults = {
		
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
		'accept_user_id':lambda obj, cr, uid, context: uid,
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.date)
		if entry_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['Line Items']),
  
	   ]
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_batch_heat_treatment_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_batch_heat_treatment_line, self).write(cr, uid, ids, vals, context)
		
		
	
ch_batch_heat_treatment_line()


class kg_batch_rough_grinding(osv.osv):

	_name = "kg.batch.rough.grinding"
	_description = "Rough Grinding Batch"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Batch No.', size=128,select=True),
		'entry_date': fields.date('Batch Date',required=True),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed')],'Status', readonly=True),

		'rough_grinding_ids':fields.many2many('kg.fettling','m2m_rough_grinding_details' , 'batch_id', 'rough_grinding_id', 'Rough Grinding Items',
			domain="[('stage_name','=','ROUGH GRINDING'),('state','=','accept')]"),
			
		'line_ids': fields.one2many('ch.batch.rough.grinding.line', 'header_id', "Batch Line Details"),
		
		'flag_batchline':fields.boolean('Batch Line Created'),
		
		'rough_grinding_date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'employee_name': fields.char('Employee',size=128),
		'weight':fields.integer('Weight(kgs)'),

		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),  
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),   
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_batch_rough_grinding', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'rough_grinding_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft'
		
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.entry_date)
		rough_grinding_date = str(rec.rough_grinding_date)
		if entry_date > today:
			return False
		if rough_grinding_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
  
	   ]		

	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])  
		fettling_obj = self.pool.get('kg.fettling')
		line_obj = self.pool.get('ch.batch.rough.grinding.line')
		
		del_sql = """ delete from ch_batch_rough_grinding_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.rough_grinding_ids:
		
			for item in entry.rough_grinding_ids:
				
				
				vals = {
				
					'header_id': entry.id,
					'rough_grinding_id':item.id,
					'qty': item.rough_grinding_qty,
					'accept_qty': item.rough_grinding_qty,
					'date': entry.rough_grinding_date,
					'shift_id': entry.shift_id.id,
					'done_by': entry.done_by,
					'contractor_id': entry.contractor_id.id,
					'employee_name': entry.employee_name,
					'weight': entry.weight,
					'remarks':  entry.remarks
				}
				
				line_id = line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_batchline': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			fettling_obj = self.pool.get('kg.fettling')  
			if not entry.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to confirm without Line Items !!'))
							
							
			### Updation against Bactch Rough Grinding ###
			for item in entry.line_ids:
				reject_qty = item.qty - item.accept_qty
				if item.reject_qty > 0 and item.reject_remarks_id.id == False:
					raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
				
				fettling_obj.write(cr, uid,item.rough_grinding_id.id,{
				'rough_grinding_remarks':item.remarks,
				'rough_grinding_accept_qty': item.accept_qty,
				'rough_grinding_reject_qty': item.reject_qty,
				'rough_grinding_rework_qty': item.rework_qty,
				'rough_grinding_accept_user_id': item.accept_user_id.id,
				'rough_grinding_reject_remarks_id': item.reject_remarks_id.id,
				'rough_grinding_date': item.date,
				'rough_grinding_shift_id': item.shift_id.id,
				'rough_grinding_contractor': item.contractor_id.id,
				'rough_grinding_employee': item.employee_name,
				'rough_grinding_by': item.done_by,
				'rough_grinding_weight': item.weight,
				})
				fettling_obj.rough_grinding_update(cr, uid, [item.rough_grinding_id.id])
				
			### Sequence Number Generation  ###
			batch_name = '' 
			batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.batch.rough.grinding')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,batch_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(batch_seq_id[0],seq_rec.code,entry.entry_date))
			batch_name = cr.fetchone();
			self.write(cr, uid, ids, {'name':batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_batch_rough_grinding, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []  
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_batch_rough_grinding()


class ch_batch_rough_grinding_line(osv.osv):

	_name = "ch.batch.rough.grinding.line"
	_description = "Rough Grinding Batch Line"
	
	_columns = {
	
		'header_id':fields.many2one('kg.batch.rough.grinding', 'Header', required=1, ondelete='cascade'),	 
		'rough_grinding_id':fields.many2one('kg.fettling', 'Fettling'),
		'name': fields.related('rough_grinding_id','rough_grinding_name', type='char', string='Production Entry Code', store=True, readonly=True),
		'order_no': fields.related('rough_grinding_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'pattern_id': fields.related('rough_grinding_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('rough_grinding_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('rough_grinding_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'qty': fields.integer('Total Qty'),
		'accept_qty': fields.integer('Accepted Qty'),
		'reject_qty': fields.integer('Rejected Qty'),
		'rework_qty': fields.integer('Rework Qty'),
		'weight':fields.integer('Weight(kgs)'),
		'remarks': fields.text('Remarks'),
		'reject_user_id': fields.many2one('res.users', 'Rejected By'),
		'accept_user_id': fields.many2one('res.users', 'Accepted By'),  
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'employee_name': fields.char('Employee',size=128),
		'reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		
		
	}
	
	_defaults = {
		
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
		'reject_user_id':lambda obj, cr, uid, context: uid,
		'accept_user_id':lambda obj, cr, uid, context: uid,
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.date)
		if entry_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['Line Items']),
  
	   ]
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_batch_rough_grinding_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_batch_rough_grinding_line, self).write(cr, uid, ids, vals, context)
		
		
	
ch_batch_rough_grinding_line()



class kg_batch_welding(osv.osv):

	_name = "kg.batch.welding"
	_description = "Welding Batch"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Batch No.', size=128,select=True),
		'entry_date': fields.date('Batch Date',required=True),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed')],'Status', readonly=True),

		'welding_ids':fields.many2many('kg.fettling','m2m_welding_details' , 'batch_id', 'welding_id', 'Welding Items',
			domain="[('welding_stage_name','=','WELDING'),('welding_state','=','progress')]"),
			
		'line_ids': fields.one2many('ch.batch.welding.line', 'header_id', "Batch Line Details"),
		
		'flag_batchline':fields.boolean('Batch Line Created'),
		
		'welding_date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'employee_name': fields.char('Employee',size=128),
		'weight':fields.integer('Weight(kgs)'),

		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),  
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),   
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_batch_welding', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'welding_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft'
		
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.entry_date)
		welding_date = str(rec.welding_date)
		if entry_date > today:
			return False
		if welding_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
  
	   ]	

	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])  
		fettling_obj = self.pool.get('kg.fettling')
		line_obj = self.pool.get('ch.batch.welding.line')
		
		del_sql = """ delete from ch_batch_welding_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.welding_ids:
		
			for item in entry.welding_ids:
				
				
				vals = {
				
					'header_id': entry.id,
					'welding_id':item.id,
					'qty': item.welding_qty,
					'accept_qty': item.welding_qty,
					'date': entry.welding_date,
					'shift_id': entry.shift_id.id,
					'done_by': entry.done_by,
					'contractor_id': entry.contractor_id.id,
					'employee_name': entry.employee_name,
					'weight': entry.weight,
					'remarks':  entry.remarks
				}
				
				line_id = line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_batchline': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			fettling_obj = self.pool.get('kg.fettling')  
			if not entry.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to confirm without Line Items !!'))
							
							
			### Updation against Bactch WELDING ###
			for item in entry.line_ids:
				reject_qty = item.qty - item.accept_qty
				if item.reject_qty > 0 and item.reject_remarks_id.id == False:
					raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
				
				fettling_obj.write(cr, uid,item.welding_id.id,{
				'welding_remarks':item.remarks,
				'welding_accept_qty': item.accept_qty,
				'welding_reject_qty': item.reject_qty,
				'welding_accept_user_id': item.accept_user_id.id,
				'welding_reject_remarks_id': item.reject_remarks_id.id,
				'welding_date': item.date,
				'welding_shift_id': item.shift_id.id,
				'welding_contractor': item.contractor_id.id,
				'welding_employee': item.employee_name,
				'welding_by': item.done_by,
				'welding_weight': item.weight,
				})
				fettling_obj.welding_update(cr, uid, [item.welding_id.id])
				
			### Sequence Number Generation  ###
			batch_name = '' 
			batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.batch.welding')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,batch_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(batch_seq_id[0],seq_rec.code,entry.entry_date))
			batch_name = cr.fetchone();
			self.write(cr, uid, ids, {'name':batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_batch_welding, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []  
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_batch_welding()


class ch_batch_welding_line(osv.osv):

	_name = "ch.batch.welding.line"
	_description = "Welding Batch Line"
	
	_columns = {
	
		'header_id':fields.many2one('kg.batch.welding', 'Header', required=1, ondelete='cascade'),  
		'welding_id':fields.many2one('kg.fettling', 'Fettling'),
		'name': fields.related('welding_id','welding_name', type='char', string='Production Entry Code', store=True, readonly=True),
		'order_no': fields.related('welding_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'pattern_id': fields.related('welding_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('welding_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('welding_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'qty': fields.integer('Total Qty'),
		'accept_qty': fields.integer('Accepted Qty'),
		'reject_qty': fields.integer('Rejected Qty'),
		'weight':fields.integer('Weight(kgs)'),
		'remarks': fields.text('Remarks'),
		'reject_user_id': fields.many2one('res.users', 'Rejected By'),
		'accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'employee_name': fields.char('Employee',size=128),
		'reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),   
		
		
	}
	
	_defaults = {
		
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
		'reject_user_id':lambda obj, cr, uid, context: uid,
		'accept_user_id':lambda obj, cr, uid, context: uid,
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.date)
		if entry_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['Line Items']),
  
	   ]
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_batch_welding_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_batch_welding_line, self).write(cr, uid, ids, vals, context)
		
		
	
ch_batch_welding_line()


class kg_batch_finish_grinding(osv.osv):

	_name = "kg.batch.finish.grinding"
	_description = "Finish Grinding Batch"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Batch No.', size=128,select=True),
		'entry_date': fields.date('Batch Date',required=True),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed')],'Status', readonly=True),

		'finish_grinding_ids':fields.many2many('kg.fettling','m2m_finish_grinding_details' , 'batch_id', 'finish_grinding_id', 'Finish Grinding Items',
			domain="[('stage_name','=','FINISH GRINDING'),('state','=','accept'),('flag_fg_special_app','!=','t')]"),
			
		'line_ids': fields.one2many('ch.batch.finish.grinding.line', 'header_id', "Batch Line Details"),
		
		'flag_batchline':fields.boolean('Batch Line Created'),
		
		'finish_grinding_date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'employee_name': fields.char('Employee',size=128),
		'weight':fields.integer('Weight(kgs)'),
		'flag_reshot_blast_applicable': fields.boolean('Re-Shot Blasting Applicable'),

		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),  
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),   
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_batch_finish_grinding', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'finish_grinding_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft'
		
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.entry_date)
		finish_grinding_date = str(rec.finish_grinding_date)
		if entry_date > today:
			return False
		if finish_grinding_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
  
	   ]	

	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])  
		fettling_obj = self.pool.get('kg.fettling')
		line_obj = self.pool.get('ch.batch.finish.grinding.line')
		
		del_sql = """ delete from ch_batch_finish_grinding_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.finish_grinding_ids:
		
			for item in entry.finish_grinding_ids:
				
				vals = {
				
					'header_id': entry.id,
					'finish_grinding_id':item.id,
					'qty': item.finish_grinding_qty,
					'accept_qty': item.finish_grinding_qty,
					'date': entry.finish_grinding_date,
					'shift_id': entry.shift_id.id,
					'done_by': entry.done_by,
					'contractor_id': entry.contractor_id.id,
					'employee_name': entry.employee_name,
					'weight': entry.weight,
					'remarks':  entry.remarks,
					'flag_reshot_blast_applicable': entry.flag_reshot_blast_applicable
				}
				
				print "vals",vals
				line_id = line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_batchline': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			fettling_obj = self.pool.get('kg.fettling')  
			if not entry.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to confirm without Line Items !!'))
							
							
			### Updation against Bactch Finish Grinding ###
			for item in entry.line_ids:
				reject_qty = item.qty - item.accept_qty
				if item.reject_qty > 0 and item.reject_remarks_id.id == False:
					raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
				
				fettling_obj.write(cr, uid,item.finish_grinding_id.id,{
				'finish_grinding_remarks':item.remarks,
				'finish_grinding_accept_qty': item.accept_qty,
				'finish_grinding_reject_qty': item.reject_qty,
				'finish_grinding_accept_user_id': item.accept_user_id.id,
				'finish_grinding_reject_remarks_id': item.reject_remarks_id.id,
				'finish_grinding_date': item.date,
				'finish_grinding_shift_id': item.shift_id.id,
				'finish_grinding_contractor': item.contractor_id.id,
				'finish_grinding_employee': item.employee_name,
				'finish_grinding_by': item.done_by,
				'finish_grinding_weight': item.weight,
				'flag_reshot_blast_applicable': item.flag_reshot_blast_applicable
				})
				fettling_obj.finish_grinding_update(cr, uid, [item.finish_grinding_id.id])
				
			### Sequence Number Generation  ###
			batch_name = '' 
			batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.batch.finish.grinding')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,batch_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(batch_seq_id[0],seq_rec.code,entry.entry_date))
			batch_name = cr.fetchone();
			self.write(cr, uid, ids, {'name':batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_batch_finish_grinding, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []  
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_batch_finish_grinding()


class ch_batch_finish_grinding_line(osv.osv):

	_name = "ch.batch.finish.grinding.line"
	_description = "Finish Grinding Batch Line"
	
	_columns = {
	
		'header_id':fields.many2one('kg.batch.finish.grinding', 'Header', required=1, ondelete='cascade'),  
		'finish_grinding_id':fields.many2one('kg.fettling', 'Fettling'),
		'name': fields.related('finish_grinding_id','finish_grinding_name', type='char', string='Production Entry Code', store=True, readonly=True),
		'order_no': fields.related('finish_grinding_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'pattern_id': fields.related('finish_grinding_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('finish_grinding_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('finish_grinding_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'qty': fields.integer('Total Qty'),
		'accept_qty': fields.integer('Accepted Qty'),
		'reject_qty': fields.integer('Rejected Qty'),
		'weight':fields.integer('Weight(kgs)'),
		'remarks': fields.text('Remarks'),
		'reject_user_id': fields.many2one('res.users', 'Rejected By'),
		'accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'employee_name': fields.char('Employee',size=128),
		'reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'flag_reshot_blast_applicable': fields.boolean('Re-Shot Blasting Applicable'),  
		
		
	}
	
	_defaults = {
		
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
		'reject_user_id':lambda obj, cr, uid, context: uid,
		'accept_user_id':lambda obj, cr, uid, context: uid,
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.date)
		if entry_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['Line Items']),
  
	   ]
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_batch_finish_grinding_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_batch_finish_grinding_line, self).write(cr, uid, ids, vals, context)
		
		
	
ch_batch_finish_grinding_line()

class kg_batch_reshot_blasting(osv.osv):

	_name = "kg.batch.reshot.blasting"
	_description = "Reshot Blasting Batch"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Batch No.', size=128,select=True),
		'entry_date': fields.date('Batch Date',required=True),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed')],'Status', readonly=True),

		'reshot_blasting_ids':fields.many2many('kg.fettling','m2m_reshot_blasting_details' , 'batch_id', 'reshot_blasting_id', 'Reshot Blasting Items',
			domain="[('stage_name','=','RE SHOT BLASTING'),('state','=','accept')]"),
			
		'line_ids': fields.one2many('ch.batch.reshot.blasting.line', 'header_id', "Batch Line Details"),
		
		'flag_batchline':fields.boolean('Batch Line Created'),
		
		'reshot_blasting_date': fields.date('Date', required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'employee_name': fields.char('Employee',size=128),
		'weight':fields.integer('Weight(kgs)'),

		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),  
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),   
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_batch_reshot_blasting', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'reshot_blasting_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft'
		
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.entry_date)
		reshot_blasting_date = str(rec.reshot_blasting_date)
		if entry_date > today:
			return False
		if reshot_blasting_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
  
	   ]	

	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])  
		fettling_obj = self.pool.get('kg.fettling')
		line_obj = self.pool.get('ch.batch.reshot.blasting.line')
		
		del_sql = """ delete from ch_batch_reshot_blasting_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.reshot_blasting_ids:
		
			for item in entry.reshot_blasting_ids:
				
				
				vals = {
				
					'header_id': entry.id,
					'reshot_blasting_id':item.id,
					'qty': item.reshot_blasting_qty,
					'accept_qty': item.reshot_blasting_qty,
					'date': entry.reshot_blasting_date,
					'shift_id': entry.shift_id.id,
					'done_by': entry.done_by,
					'contractor_id': entry.contractor_id.id,
					'employee_name': entry.employee_name,
					'weight': entry.weight,
					'remarks':  entry.remarks
				}
				
				line_id = line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_batchline': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			fettling_obj = self.pool.get('kg.fettling')  
			if not entry.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to confirm without Line Items !!'))
							
							
			### Updation against Bactch Reshot Blast ###
			for item in entry.line_ids:
				reject_qty = item.qty - item.accept_qty
				if item.reject_qty > 0 and item.reject_remarks_id.id == False:
					raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
				
				fettling_obj.write(cr, uid,item.reshot_blasting_id.id,{
				'reshot_blasting_remarks':item.remarks,
				'reshot_blasting_accept_qty': item.accept_qty,
				'reshot_blasting_reject_qty': item.reject_qty,
				'reshot_blasting_accept_user_id': item.accept_user_id.id,
				'reshot_blasting_reject_remarks_id': item.reject_remarks_id.id,
				'reshot_blasting_date': item.date,
				'reshot_blasting_shift_id': item.shift_id.id,
				'reshot_blasting_contractor': item.contractor_id.id,
				'reshot_blasting_employee': item.employee_name,
				'reshot_blasting_by': item.done_by,
				'reshot_blasting_weight': item.weight,
				})
				fettling_obj.reshot_blasting_update(cr, uid, [item.reshot_blasting_id.id])
				
			### Sequence Number Generation  ###
			batch_name = '' 
			batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.batch.reshot.blasting')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,batch_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(batch_seq_id[0],seq_rec.code,entry.entry_date))
			batch_name = cr.fetchone();
			self.write(cr, uid, ids, {'name':batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_batch_reshot_blasting, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []  
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_batch_reshot_blasting()


class ch_batch_reshot_blasting_line(osv.osv):

	_name = "ch.batch.reshot.blasting.line"
	_description = "Reshot Blasting Batch Line"
	
	_columns = {
	
		'header_id':fields.many2one('kg.batch.reshot.blasting', 'Header', required=1, ondelete='cascade'),  
		'reshot_blasting_id':fields.many2one('kg.fettling', 'Fettling'),
		'name': fields.related('reshot_blasting_id','reshot_blasting_name', type='char', string='Production Entry Code', store=True, readonly=True),
		'order_no': fields.related('reshot_blasting_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'pattern_id': fields.related('reshot_blasting_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('reshot_blasting_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('reshot_blasting_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'date': fields.date('Date', store=True, required=True),
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'contractor_id':fields.many2one('res.partner','Contractor'),
		'qty': fields.integer('Total Qty'),
		'accept_qty': fields.integer('Accepted Qty'),
		'reject_qty': fields.integer('Rejected Qty'),
		'weight':fields.integer('Weight(kgs)'),
		'remarks': fields.text('Remarks'),
		'reject_user_id': fields.many2one('res.users', 'Rejected By'),
		'accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'done_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'employee_name': fields.char('Employee',size=128),
		'reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),   
		
		
	}
	
	_defaults = {
		
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
		'reject_user_id':lambda obj, cr, uid, context: uid,
		'accept_user_id':lambda obj, cr, uid, context: uid,
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.date)
		if entry_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['Line Items']),
  
	   ]
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_batch_reshot_blasting_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_batch_reshot_blasting_line, self).write(cr, uid, ids, vals, context)
		
		
	
ch_batch_reshot_blasting_line()

class kg_foundry_rejection_list(osv.osv):

	_name = "kg.foundry.rejection.list"
	_description = "Foundry Rejection List"
	_order = "order_priority asc"
	
	def _get_total_weight(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		total_weight = 0.00
		for entry in self.browse(cr, uid, ids, context=context):
			total_weight = entry.qty * entry.each_weight		
		result[entry.id]= total_weight
		return result
	
	
	_columns = {
	
		
		'entry_date': fields.date('Date',required=True),
		'division_id': fields.many2one('kg.division.master','Division'),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location'),
		'active': fields.boolean('Active'),
	
		### Work Order Details ###
		
		'order_id': fields.many2one('kg.work.order','Work Order'),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line'),
		'order_no': fields.related('order_line_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('order_line_id','delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'order_date': fields.related('order_id','entry_date', type='date', string='Order Date', store=True, readonly=True),
		'order_category': fields.related('order_line_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.selection(ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		
		'pump_model_id': fields.related('order_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern Number', readonly=True),
		'pattern_code': fields.related('pattern_id','name', type='char', string='Pattern Code', store=True, readonly=True),
		'pattern_name': fields.related('pattern_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.many2one('kg.moc.master', 'MOC', readonly=True),
		'stage_id':fields.many2one('kg.stage.master','Stage'),
		'stage_name': fields.char('Rejected Stage', size=100),
		'active': fields.boolean('Active'),
		'qty': fields.integer('Qty'),
		'each_weight': fields.float('Each Weight(Kgs)'),
		'total_weight': fields.function(_get_total_weight, string='Total Weight(Kgs)', method=True, store=True, type='float'),
		'reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		
		
	}
	
	_defaults = {
	
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'active': True,
		
		
	}
	
kg_foundry_rejection_list()
		

















