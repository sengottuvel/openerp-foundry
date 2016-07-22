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
   ('project','Project')
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
		'state': fields.selection([('waiting','Waiting for Accept'),('accept','Accepted'),('complete','Completed')],'Status', readonly=True),
		
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
		
		### HEAT TREATMENT ###
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
		### DECORING ###
		'decoring_user_id':lambda obj, cr, uid, context: uid,
		'decoring_date':lambda * a: time.strftime('%Y-%m-%d'),
		'decoring_accept_user_id':lambda obj, cr, uid, context: uid,
		### Shot Blast ###
		'shot_blast_user_id':lambda obj, cr, uid, context: uid,
		'shot_blast_date':lambda * a: time.strftime('%Y-%m-%d'),
		'shot_blast_accept_user_id':lambda obj, cr, uid, context: uid,
		### Hammering ###
		'hammering_user_id':lambda obj, cr, uid, context: uid,
		'hammering_date':lambda * a: time.strftime('%Y-%m-%d'),
		'hammering_accept_user_id':lambda obj, cr, uid, context: uid,
		### Wheel Cutting ###
		'wheel_cutting_user_id':lambda obj, cr, uid, context: uid,
		'wheel_cutting_date':lambda * a: time.strftime('%Y-%m-%d'),
		'wheel_cutting_accept_user_id':lambda obj, cr, uid, context: uid,
		### Gas Cutting ###
		'gas_cutting_user_id':lambda obj, cr, uid, context: uid,
		'gas_cutting_date':lambda * a: time.strftime('%Y-%m-%d'),
		'gas_cutting_accept_user_id':lambda obj, cr, uid, context: uid,
		### ARC Cutting ###
		'arc_cutting_user_id':lambda obj, cr, uid, context: uid,
		'arc_cutting_date':lambda * a: time.strftime('%Y-%m-%d'),
		'arc_cutting_accept_user_id':lambda obj, cr, uid, context: uid,
		### HEAT TREATMENT ###
		'heat_user_id':lambda obj, cr, uid, context: uid,
		'heat_date':lambda * a: time.strftime('%Y-%m-%d'),
		### Rough Grinding ###
		'rough_grinding_user_id':lambda obj, cr, uid, context: uid,
		'rough_grinding_date':lambda * a: time.strftime('%Y-%m-%d'),
		'rough_grinding_accept_user_id':lambda obj, cr, uid, context: uid,
		### Finish Grinding ###
		'finish_grinding_user_id':lambda obj, cr, uid, context: uid,
		'finish_grinding_date':lambda * a: time.strftime('%Y-%m-%d'),
		'finish_grinding_accept_user_id':lambda obj, cr, uid, context: uid,
		### Re Shot Blasting ###
		'reshot_blasting_user_id':lambda obj, cr, uid, context: uid,
		'reshot_blasting_date':lambda * a: time.strftime('%Y-%m-%d'),
		'reshot_blasting_accept_user_id':lambda obj, cr, uid, context: uid,
		### Re Shot Blasting ###
		'welding_user_id':lambda obj, cr, uid, context: uid,
		'welding_date':lambda * a: time.strftime('%Y-%m-%d'),
		'welding_accept_user_id':lambda obj, cr, uid, context: uid,
		
		
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
	
	
	def ms_inward_update(self,cr,uid,ids,inward_qty,context=None):
		ms_obj = self.pool.get('kg.machineshop')
		entry_rec = self.browse(cr, uid, ids[0])
		
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
			
			### Schedule List Updation ###
			production_obj = self.pool.get('kg.production')
			cr.execute(''' update kg_production set state = 'moved_to_ms' where id = %s ''',[entry_rec.production_id.id])
			#~ production_obj.write(cr, uid, entry_rec.production_id.id, {'state': 'moved_to_ms'})
			
			### Fettling Status Updation ###
			self.write(cr, uid, ids, {'state': 'complete'})
		
		
		return True
		
	
	def fettling_accept(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.pour_qty - entry.inward_accept_qty
		
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
			cr.execute(""" select fettling.stage_id,stage.name as stage_name,fettling.seq_no from ch_fettling_process as fettling
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
					self.ms_inward_update(cr, uid, [entry.id],entry.inward_accept_qty)
					
		if entry.inward_reject_qty > 0:
			
			production_obj.write(cr, uid, entry.production_id.id, {'fettling_reject_qty': entry.production_id.fettling_reject_qty + entry.inward_reject_qty})
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
				'core_qty': entry.inward_reject_qty,
				'core_rem_qty': entry.inward_reject_qty,
				'core_state': 'pending',
				'mould_no': mould_name[0],
				'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
				'mould_qty': entry.inward_reject_qty,
				'mould_rem_qty': entry.inward_reject_qty,
				'mould_state': 'pending',		
			}
			production_id = production_obj.create(cr, uid, production_vals)
			
		
		self.write(cr, uid, ids, {'pre_stage_date':entry.entry_date,'state': 'accept','update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})

		return True
		
		
		
	def knockout_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.knockout_qty - entry.knockout_accept_qty
		
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
		if entry.knockout_accept_qty > 0:
			cr.execute(""" select fettling.stage_id,stage.name as stage_name,fettling.seq_no from ch_fettling_process as fettling
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
						knockout_qty = entry.knockout_accept_qty
						### Sequence Number Generation ###
						knockout_name = ''	
						knockout_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.knock.out')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,knockout_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(knockout_seq_id[0],seq_rec.code))
						knockout_name = cr.fetchone();
						self.write(cr, uid, ids, {'knockout_date':time.strftime('%Y-%m-%d'),'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0]})
					
					if stage_item['stage_name'] == 'DECORING':
						### Next Stage Qty ###
						decoring_qty = entry.knockout_accept_qty
						### Sequence Number Generation ###
						decoring_name = ''	
						decoring_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.decoring')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,decoring_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(decoring_seq_id[0],seq_rec.code))
						decoring_name = cr.fetchone();
						self.write(cr, uid, ids, {'decoring_date':time.strftime('%Y-%m-%d'),'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0]})
					
					if stage_item['stage_name'] == 'SHOT BLAST':
						### Next Stage Qty ###
						shot_blast_qty = entry.knockout_accept_qty
						### Sequence Number Generation ###
						shot_blast_name = ''	
						shot_blast_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.shot.blast')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,shot_blast_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(shot_blast_seq_id[0],seq_rec.code))
						shot_blast_name = cr.fetchone();
						self.write(cr, uid, ids, {'shot_blast_date':time.strftime('%Y-%m-%d'),'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0]})
					
					if stage_item['stage_name'] == 'HAMMERING':
						### Next Stage Qty ###
						hammering_qty = entry.knockout_accept_qty
						### Sequence Number Generation ###
						hammering_name = ''	
						hammering_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.hammering')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,hammering_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(hammering_seq_id[0],seq_rec.code))
						hammering_name = cr.fetchone();
						self.write(cr, uid, ids, {'hammering_date':time.strftime('%Y-%m-%d'),'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0]})
					
					if stage_item['stage_name'] == 'WHEEL CUTTING':
						### Next Stage Qty ###
						wheel_cutting_qty = entry.knockout_accept_qty
						### Sequence Number Generation ###
						wheel_cutting_name = ''	
						wheel_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.wheel.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,wheel_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(wheel_cutting_seq_id[0],seq_rec.code))
						wheel_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'wheel_cutting_date':time.strftime('%Y-%m-%d'),'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0]})
					
					if stage_item['stage_name'] == 'GAS CUTTING':
						### Next Stage Qty ###
						gas_cutting_qty = entry.knockout_accept_qty
						### Sequence Number Generation ###
						gas_cutting_name = ''	
						gas_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.gas.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,gas_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(gas_cutting_seq_id[0],seq_rec.code))
						gas_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'gas_cutting_date':time.strftime('%Y-%m-%d'),'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0]})
					
					if stage_item['stage_name'] == 'ARC CUTTING':
						### Next Stage Qty ###
						arc_cutting_qty = entry.knockout_accept_qty
						### Sequence Number Generation ###
						arc_cutting_name = ''	
						arc_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.arc.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,arc_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(arc_cutting_seq_id[0],seq_rec.code))
						arc_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'arc_cutting_date':time.strftime('%Y-%m-%d'),'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0]})
					
					if stage_item['stage_name'] == 'HEAT TREATMENT':
						### Next Stage Qty ###
						heat_total_qty = entry.knockout_accept_qty
						self.write(cr, uid, ids, {'heat_date':time.strftime('%Y-%m-%d'),'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty})
					
					if stage_item['stage_name'] == 'ROUGH GRINDING':
						### Next Stage Qty ###
						rough_grinding_qty = entry.knockout_accept_qty
						### Sequence Number Generation ###
						rough_grinding_name = ''	
						rough_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.rough.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,rough_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(rough_grinding_seq_id[0],seq_rec.code))
						rough_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'rough_grinding_date':time.strftime('%Y-%m-%d'),'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,'rough_grinding_name':rough_grinding_name[0]})
					
					if stage_item['stage_name'] == 'FINISH GRINDING':
						### Next Stage Qty ###
						finish_grinding_qty = entry.knockout_accept_qty
						### Sequence Number Generation ###
						finish_grinding_name = ''	
						finish_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.finish.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,finish_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(finish_grinding_seq_id[0],seq_rec.code))
						finish_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'finish_grinding_date':time.strftime('%Y-%m-%d'),'finish_grinding_qty': finish_grinding_qty,'finish_grinding_accept_qty': finish_grinding_qty,'finish_grinding_name':finish_grinding_name[0]})
						
					if stage_item['stage_name'] == 'RE SHOT BLASTING':
						### Next Stage Qty ###
						reshot_blasting_qty = entry.knockout_accept_qty
						### Sequence Number Generation ###
						reshot_blasting_name = ''	
						reshot_blasting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.reshot.blasting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,reshot_blasting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(reshot_blasting_seq_id[0],seq_rec.code))
						reshot_blasting_name = cr.fetchone();
						self.write(cr, uid, ids, {'reshot_blasting_date':time.strftime('%Y-%m-%d'),'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0]})
					
					
					self.write(cr, uid, ids, {'pre_stage_date':entry.knockout_date,'stage_id': stage_item['stage_id']})
					
			else:
				### MS Inward Process Creation ###
				self.ms_inward_update(cr, uid, [entry.id],entry.knockout_accept_qty)
			
		if entry.knockout_reject_qty > 0:
			
			### Full Rejection Update ###
			full_reject_qty = entry.knockout_qty - entry.knockout_reject_qty
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
			
			production_vals = {
									
				'name': produc_name[0],
				'schedule_id': entry.schedule_id.id,
				'schedule_date': entry.schedule_date,
				'division_id': entry.division_id.id,
				'location' : entry.location,
				'schedule_line_id': entry.schedule_line_id.id,
				'order_id': entry.order_id.id,
				'order_line_id': entry.order_line_id.id,
				'qty' : entry.knockout_reject_qty,			  
				'schedule_qty' : entry.knockout_reject_qty,			  
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
				'core_qty': entry.knockout_reject_qty,
				'core_state': 'pending',
				'mould_no': mould_name[0],
				'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
				'mould_qty': entry.knockout_reject_qty,
				'mould_state': 'pending',		
			}
			production_id = production_obj.create(cr, uid, production_vals)
		self.write(cr, uid, ids, {'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
		
		
	def decoring_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.decoring_qty - entry.decoring_accept_qty
		
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
			raise osv.except_osv(_('Warning!'),
				_('System not allow to save with future date !!'))
		
		if entry.decoring_accept_qty > 0:
			cr.execute(""" select fettling.stage_id,stage.name as stage_name,fettling.seq_no from ch_fettling_process as fettling
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
						knockout_qty = entry.decoring_accept_qty
						### Sequence Number Generation ###
						knockout_name = ''	
						knockout_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.knock.out')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,knockout_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(knockout_seq_id[0],seq_rec.code))
						knockout_name = cr.fetchone();
						self.write(cr, uid, ids, {'knockout_date':time.strftime('%Y-%m-%d'),'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0]})
					
					if stage_item['stage_name'] == 'DECORING':
						### Next Stage Qty ###
						decoring_qty = entry.decoring_accept_qty
						### Sequence Number Generation ###
						decoring_name = ''	
						decoring_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.decoring')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,decoring_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(decoring_seq_id[0],seq_rec.code))
						decoring_name = cr.fetchone();
						self.write(cr, uid, ids, {'decoring_date':time.strftime('%Y-%m-%d'),'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0]})
					
					if stage_item['stage_name'] == 'SHOT BLAST':
						### Next Stage Qty ###
						shot_blast_qty = entry.decoring_accept_qty
						### Sequence Number Generation ###
						shot_blast_name = ''	
						shot_blast_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.shot.blast')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,shot_blast_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(shot_blast_seq_id[0],seq_rec.code))
						shot_blast_name = cr.fetchone();
						self.write(cr, uid, ids, {'shot_blast_date':time.strftime('%Y-%m-%d'),'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0]})
					
					if stage_item['stage_name'] == 'HAMMERING':
						### Next Stage Qty ###
						hammering_qty = entry.decoring_accept_qty
						### Sequence Number Generation ###
						hammering_name = ''	
						hammering_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.hammering')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,hammering_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(hammering_seq_id[0],seq_rec.code))
						hammering_name = cr.fetchone();
						self.write(cr, uid, ids, {'hammering_date':time.strftime('%Y-%m-%d'),'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0]})
					
					if stage_item['stage_name'] == 'WHEEL CUTTING':
						### Next Stage Qty ###
						wheel_cutting_qty = entry.decoring_accept_qty
						### Sequence Number Generation ###
						wheel_cutting_name = ''	
						wheel_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.wheel.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,wheel_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(wheel_cutting_seq_id[0],seq_rec.code))
						wheel_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'wheel_cutting_date':time.strftime('%Y-%m-%d'),'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0]})
					
					if stage_item['stage_name'] == 'GAS CUTTING':
						### Next Stage Qty ###
						gas_cutting_qty = entry.decoring_accept_qty
						### Sequence Number Generation ###
						gas_cutting_name = ''	
						gas_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.gas.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,gas_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(gas_cutting_seq_id[0],seq_rec.code))
						gas_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'gas_cutting_date':time.strftime('%Y-%m-%d'),'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0]})
					
					if stage_item['stage_name'] == 'ARC CUTTING':
						### Next Stage Qty ###
						arc_cutting_qty = entry.decoring_accept_qty
						### Sequence Number Generation ###
						arc_cutting_name = ''	
						arc_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.arc.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,arc_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(arc_cutting_seq_id[0],seq_rec.code))
						arc_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'arc_cutting_date':time.strftime('%Y-%m-%d'),'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0]})
					
					if stage_item['stage_name'] == 'HEAT TREATMENT':
						### Next Stage Qty ###
						heat_total_qty = entry.decoring_accept_qty
						self.write(cr, uid, ids, {'heat_date':time.strftime('%Y-%m-%d'),'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty})
					
					if stage_item['stage_name'] == 'ROUGH GRINDING':
						### Next Stage Qty ###
						rough_grinding_qty = entry.decoring_accept_qty
						### Sequence Number Generation ###
						rough_grinding_name = ''	
						rough_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.rough.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,rough_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(rough_grinding_seq_id[0],seq_rec.code))
						rough_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'rough_grinding_date':time.strftime('%Y-%m-%d'),'rough_grinding_date':time.strftime('%Y-%m-%d'),'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,'rough_grinding_name':rough_grinding_name[0]})
					
					if stage_item['stage_name'] == 'FINISH GRINDING':
						### Next Stage Qty ###
						finish_grinding_qty = entry.decoring_accept_qty
						### Sequence Number Generation ###
						finish_grinding_name = ''	
						finish_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.finish.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,finish_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(finish_grinding_seq_id[0],seq_rec.code))
						finish_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'finish_grinding_date':time.strftime('%Y-%m-%d'),'finish_grinding_qty': finish_grinding_qty,'finish_grinding_accept_qty': finish_grinding_qty,'finish_grinding_name':finish_grinding_name[0]})
						
					if stage_item['stage_name'] == 'RE SHOT BLASTING':
						### Next Stage Qty ###
						reshot_blasting_qty = entry.decoring_accept_qty
						### Sequence Number Generation ###
						reshot_blasting_name = ''	
						reshot_blasting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.reshot.blasting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,reshot_blasting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(reshot_blasting_seq_id[0],seq_rec.code))
						reshot_blasting_name = cr.fetchone();
						self.write(cr, uid, ids, {'reshot_blasting_date':time.strftime('%Y-%m-%d'),'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0]})
					
					self.write(cr, uid, ids, {'pre_stage_date':entry.decoring_date,'stage_id': stage_item['stage_id']})
					
			else:
				### MS Inward Process Creation ###
				self.ms_inward_update(cr, uid, [entry.id],entry.decoring_accept_qty)
			
		if entry.decoring_reject_qty > 0:
			
			### Full Rejection Update ###
			full_reject_qty = entry.decoring_qty - entry.decoring_reject_qty
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
			
			production_vals = {
									
				'name': produc_name[0],
				'schedule_id': entry.schedule_id.id,
				'schedule_date': entry.schedule_date,
				'division_id': entry.division_id.id,
				'location' : entry.location,
				'schedule_line_id': entry.schedule_line_id.id,
				'order_id': entry.order_id.id,
				'order_line_id': entry.order_line_id.id,
				'qty' : entry.decoring_reject_qty,			  
				'schedule_qty' : entry.decoring_reject_qty,			  
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
				'core_qty': entry.decoring_reject_qty,
				'core_state': 'pending',
				'mould_no': mould_name[0],
				'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
				'mould_qty': entry.decoring_reject_qty,
				'mould_state': 'pending',		
			}
			production_id = production_obj.create(cr, uid, production_vals)
		self.write(cr, uid, ids, {'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
		
	def shot_blast_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.shot_blast_qty - entry.shot_blast_accept_qty
		
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
		
		if entry.shot_blast_accept_qty > 0:
			cr.execute(""" select fettling.stage_id,stage.name as stage_name,fettling.seq_no from ch_fettling_process as fettling
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
						knockout_qty = entry.shot_blast_accept_qty
						### Sequence Number Generation ###
						knockout_name = ''	
						knockout_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.knock.out')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,knockout_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(knockout_seq_id[0],seq_rec.code))
						knockout_name = cr.fetchone();
						self.write(cr, uid, ids, {'knockout_date':time.strftime('%Y-%m-%d'),'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0]})
					
					if stage_item['stage_name'] == 'DECORING':
						### Next Stage Qty ###
						decoring_qty = entry.shot_blast_accept_qty
						### Sequence Number Generation ###
						decoring_name = ''	
						decoring_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.decoring')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,decoring_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(decoring_seq_id[0],seq_rec.code))
						decoring_name = cr.fetchone();
						self.write(cr, uid, ids, {'decoring_date':time.strftime('%Y-%m-%d'),'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0]})
					
					if stage_item['stage_name'] == 'SHOT BLAST':
						### Next Stage Qty ###
						shot_blast_qty = entry.shot_blast_accept_qty
						### Sequence Number Generation ###
						shot_blast_name = ''	
						shot_blast_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.shot.blast')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,shot_blast_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(shot_blast_seq_id[0],seq_rec.code))
						shot_blast_name = cr.fetchone();
						self.write(cr, uid, ids, {'shot_blast_date':time.strftime('%Y-%m-%d'),'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0]})
					
					if stage_item['stage_name'] == 'HAMMERING':
						### Next Stage Qty ###
						hammering_qty = entry.shot_blast_accept_qty
						### Sequence Number Generation ###
						hammering_name = ''	
						hammering_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.hammering')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,hammering_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(hammering_seq_id[0],seq_rec.code))
						hammering_name = cr.fetchone();
						self.write(cr, uid, ids, {'hammering_date':time.strftime('%Y-%m-%d'),'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0]})
					
					if stage_item['stage_name'] == 'WHEEL CUTTING':
						### Next Stage Qty ###
						wheel_cutting_qty = entry.shot_blast_accept_qty
						### Sequence Number Generation ###
						wheel_cutting_name = ''	
						wheel_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.wheel.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,wheel_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(wheel_cutting_seq_id[0],seq_rec.code))
						wheel_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'wheel_cutting_date':time.strftime('%Y-%m-%d'),'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0]})
					
					if stage_item['stage_name'] == 'GAS CUTTING':
						### Next Stage Qty ###
						gas_cutting_qty = entry.shot_blast_accept_qty
						### Sequence Number Generation ###
						gas_cutting_name = ''	
						gas_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.gas.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,gas_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(gas_cutting_seq_id[0],seq_rec.code))
						gas_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'gas_cutting_date':time.strftime('%Y-%m-%d'),'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0]})
					
					if stage_item['stage_name'] == 'ARC CUTTING':
						### Next Stage Qty ###
						arc_cutting_qty = entry.shot_blast_accept_qty
						### Sequence Number Generation ###
						arc_cutting_name = ''	
						arc_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.arc.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,arc_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(arc_cutting_seq_id[0],seq_rec.code))
						arc_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'arc_cutting_date':time.strftime('%Y-%m-%d'),'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0]})
					
					if stage_item['stage_name'] == 'HEAT TREATMENT':
						### Next Stage Qty ###
						heat_total_qty = entry.shot_blast_accept_qty
						self.write(cr, uid, ids, {'heat_date':time.strftime('%Y-%m-%d'),'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty})
					
					if stage_item['stage_name'] == 'ROUGH GRINDING':
						### Next Stage Qty ###
						rough_grinding_qty = entry.shot_blast_accept_qty
						### Sequence Number Generation ###
						rough_grinding_name = ''	
						rough_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.rough.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,rough_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(rough_grinding_seq_id[0],seq_rec.code))
						rough_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'rough_grinding_date':time.strftime('%Y-%m-%d'),'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,'rough_grinding_name':rough_grinding_name[0]})
					
					if stage_item['stage_name'] == 'FINISH GRINDING':
						### Next Stage Qty ###
						finish_grinding_qty = entry.shot_blast_accept_qty
						### Sequence Number Generation ###
						finish_grinding_name = ''	
						finish_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.finish.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,finish_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(finish_grinding_seq_id[0],seq_rec.code))
						finish_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'finish_grinding_date':time.strftime('%Y-%m-%d'),'finish_grinding_qty': finish_grinding_qty,'finish_grinding_accept_qty': finish_grinding_qty,'finish_grinding_name':finish_grinding_name[0]})
						
					if stage_item['stage_name'] == 'RE SHOT BLASTING':
						### Next Stage Qty ###
						reshot_blasting_qty = entry.shot_blast_accept_qty
						### Sequence Number Generation ###
						reshot_blasting_name = ''	
						reshot_blasting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.reshot.blasting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,reshot_blasting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(reshot_blasting_seq_id[0],seq_rec.code))
						reshot_blasting_name = cr.fetchone();
						self.write(cr, uid, ids, {'reshot_blasting_date':time.strftime('%Y-%m-%d'),'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0]})
					
					self.write(cr, uid, ids, {'pre_stage_date':entry.shot_blast_date,'stage_id': stage_item['stage_id']})
					
			else:
				### MS Inward Process Creation ###
				self.ms_inward_update(cr, uid, [entry.id],entry.shot_blast_accept_qty)
			
		if entry.shot_blast_reject_qty > 0:
			
			### Full Rejection Update ###
			full_reject_qty = entry.shot_blast_qty - entry.shot_blast_reject_qty
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
			
			production_vals = {
									
				'name': produc_name[0],
				'schedule_id': entry.schedule_id.id,
				'schedule_date': entry.schedule_date,
				'division_id': entry.division_id.id,
				'location' : entry.location,
				'schedule_line_id': entry.schedule_line_id.id,
				'order_id': entry.order_id.id,
				'order_line_id': entry.order_line_id.id,
				'qty' : entry.shot_blast_reject_qty,			  
				'schedule_qty' : entry.shot_blast_reject_qty,			  
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
				'core_qty': entry.shot_blast_reject_qty,
				'core_state': 'pending',
				'mould_no': mould_name[0],
				'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
				'mould_qty': entry.shot_blast_reject_qty,
				'mould_state': 'pending',		
			}
			production_id = production_obj.create(cr, uid, production_vals)
		self.write(cr, uid, ids, {'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
		
	def hammering_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.hammering_qty - entry.hammering_accept_qty
		
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
		
		if entry.hammering_accept_qty > 0:
			cr.execute(""" select fettling.stage_id,stage.name as stage_name,fettling.seq_no from ch_fettling_process as fettling
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
						knockout_qty = entry.hammering_accept_qty
						### Sequence Number Generation ###
						knockout_name = ''	
						knockout_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.knock.out')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,knockout_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(knockout_seq_id[0],seq_rec.code))
						knockout_name = cr.fetchone();
						self.write(cr, uid, ids, {'knockout_date':time.strftime('%Y-%m-%d'),'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0]})
					
					if stage_item['stage_name'] == 'DECORING':
						### Next Stage Qty ###
						decoring_qty = entry.hammering_accept_qty
						### Sequence Number Generation ###
						decoring_name = ''	
						decoring_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.decoring')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,decoring_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(decoring_seq_id[0],seq_rec.code))
						decoring_name = cr.fetchone();
						self.write(cr, uid, ids, {'decoring_date':time.strftime('%Y-%m-%d'),'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0]})
					
					if stage_item['stage_name'] == 'SHOT BLAST':
						### Next Stage Qty ###
						shot_blast_qty = entry.hammering_accept_qty
						### Sequence Number Generation ###
						shot_blast_name = ''	
						shot_blast_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.shot.blast')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,shot_blast_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(shot_blast_seq_id[0],seq_rec.code))
						shot_blast_name = cr.fetchone();
						self.write(cr, uid, ids, {'shot_blast_date':time.strftime('%Y-%m-%d'),'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0]})
					
					if stage_item['stage_name'] == 'HAMMERING':
						### Next Stage Qty ###
						hammering_qty = entry.hammering_accept_qty
						### Sequence Number Generation ###
						hammering_name = ''	
						hammering_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.hammering')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,hammering_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(hammering_seq_id[0],seq_rec.code))
						hammering_name = cr.fetchone();
						self.write(cr, uid, ids, {'hammering_date':time.strftime('%Y-%m-%d'),'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0]})
					
					if stage_item['stage_name'] == 'WHEEL CUTTING':
						### Next Stage Qty ###
						wheel_cutting_qty = entry.hammering_accept_qty
						### Sequence Number Generation ###
						wheel_cutting_name = ''	
						wheel_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.wheel.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,wheel_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(wheel_cutting_seq_id[0],seq_rec.code))
						wheel_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'wheel_cutting_date':time.strftime('%Y-%m-%d'),'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0]})
					
					if stage_item['stage_name'] == 'GAS CUTTING':
						### Next Stage Qty ###
						gas_cutting_qty = entry.hammering_accept_qty
						### Sequence Number Generation ###
						gas_cutting_name = ''	
						gas_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.gas.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,gas_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(gas_cutting_seq_id[0],seq_rec.code))
						gas_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'gas_cutting_date':time.strftime('%Y-%m-%d'),'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0]})
					
					if stage_item['stage_name'] == 'ARC CUTTING':
						### Next Stage Qty ###
						arc_cutting_qty = entry.hammering_accept_qty
						### Sequence Number Generation ###
						arc_cutting_name = ''	
						arc_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.arc.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,arc_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(arc_cutting_seq_id[0],seq_rec.code))
						arc_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'arc_cutting_date':time.strftime('%Y-%m-%d'),'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0]})
					
					if stage_item['stage_name'] == 'HEAT TREATMENT':
						### Next Stage Qty ###
						heat_total_qty = entry.hammering_accept_qty
						self.write(cr, uid, ids, {'heat_date':time.strftime('%Y-%m-%d'),'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty})
					
					if stage_item['stage_name'] == 'ROUGH GRINDING':
						### Next Stage Qty ###
						rough_grinding_qty = entry.hammering_accept_qty
						### Sequence Number Generation ###
						rough_grinding_name = ''	
						rough_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.rough.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,rough_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(rough_grinding_seq_id[0],seq_rec.code))
						rough_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'rough_grinding_date':time.strftime('%Y-%m-%d'),'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,'rough_grinding_name':rough_grinding_name[0]})
					
					if stage_item['stage_name'] == 'FINISH GRINDING':
						### Next Stage Qty ###
						finish_grinding_qty = entry.hammering_accept_qty
						### Sequence Number Generation ###
						finish_grinding_name = ''	
						finish_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.finish.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,finish_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(finish_grinding_seq_id[0],seq_rec.code))
						finish_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'finish_grinding_date':time.strftime('%Y-%m-%d'),'finish_grinding_qty': finish_grinding_qty,'finish_grinding_accept_qty': finish_grinding_qty,'finish_grinding_name':finish_grinding_name[0]})
						
					if stage_item['stage_name'] == 'RE SHOT BLASTING':
						### Next Stage Qty ###
						reshot_blasting_qty = entry.hammering_accept_qty
						### Sequence Number Generation ###
						reshot_blasting_name = ''	
						reshot_blasting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.reshot.blasting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,reshot_blasting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(reshot_blasting_seq_id[0],seq_rec.code))
						reshot_blasting_name = cr.fetchone();
						self.write(cr, uid, ids, {'reshot_blasting_date':time.strftime('%Y-%m-%d'),'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0]})
					
					self.write(cr, uid, ids, {'pre_stage_date':entry.hammering_date,'stage_id': stage_item['stage_id']})
					
			else:
				### MS Inward Process Creation ###
				self.ms_inward_update(cr, uid, [entry.id],entry.hammering_accept_qty)
			
		if entry.hammering_reject_qty > 0:
			
			### Full Rejection Update ###
			full_reject_qty = entry.hammering_qty - entry.hammering_reject_qty
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
			
			production_vals = {
									
				'name': produc_name[0],
				'schedule_id': entry.schedule_id.id,
				'schedule_date': entry.schedule_date,
				'division_id': entry.division_id.id,
				'location' : entry.location,
				'schedule_line_id': entry.schedule_line_id.id,
				'order_id': entry.order_id.id,
				'order_line_id': entry.order_line_id.id,
				'qty' : entry.hammering_reject_qty,			  
				'schedule_qty' : entry.hammering_reject_qty,			  
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
				'core_qty': entry.hammering_reject_qty,
				'core_state': 'pending',
				'mould_no': mould_name[0],
				'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
				'mould_qty': entry.hammering_reject_qty,
				'mould_state': 'pending',		
			}
			production_id = production_obj.create(cr, uid, production_vals)
		self.write(cr, uid, ids, {'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def wheel_cutting_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.wheel_cutting_qty - entry.wheel_cutting_accept_qty
		
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
		
		if entry.wheel_cutting_accept_qty > 0:
			cr.execute(""" select fettling.stage_id,stage.name as stage_name,fettling.seq_no from ch_fettling_process as fettling
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
						knockout_qty = entry.wheel_cutting_accept_qty
						### Sequence Number Generation ###
						knockout_name = ''	
						knockout_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.knock.out')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,knockout_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(knockout_seq_id[0],seq_rec.code))
						knockout_name = cr.fetchone();
						self.write(cr, uid, ids, {'knockout_date':time.strftime('%Y-%m-%d'),'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0]})
					
					if stage_item['stage_name'] == 'DECORING':
						### Next Stage Qty ###
						decoring_qty = entry.wheel_cutting_accept_qty
						### Sequence Number Generation ###
						decoring_name = ''	
						decoring_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.decoring')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,decoring_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(decoring_seq_id[0],seq_rec.code))
						decoring_name = cr.fetchone();
						self.write(cr, uid, ids, {'decoring_date':time.strftime('%Y-%m-%d'),'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0]})
					
					if stage_item['stage_name'] == 'SHOT BLAST':
						### Next Stage Qty ###
						shot_blast_qty = entry.wheel_cutting_accept_qty
						### Sequence Number Generation ###
						shot_blast_name = ''	
						shot_blast_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.shot.blast')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,shot_blast_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(shot_blast_seq_id[0],seq_rec.code))
						shot_blast_name = cr.fetchone();
						self.write(cr, uid, ids, {'shot_blast_date':time.strftime('%Y-%m-%d'),'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0]})
					
					if stage_item['stage_name'] == 'HAMMERING':
						### Next Stage Qty ###
						hammering_qty = entry.wheel_cutting_accept_qty
						### Sequence Number Generation ###
						hammering_name = ''	
						hammering_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.hammering')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,hammering_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(hammering_seq_id[0],seq_rec.code))
						hammering_name = cr.fetchone();
						self.write(cr, uid, ids, {'hammering_date':time.strftime('%Y-%m-%d'),'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0]})
					
					if stage_item['stage_name'] == 'WHEEL CUTTING':
						### Next Stage Qty ###
						wheel_cutting_qty = entry.wheel_cutting_accept_qty
						### Sequence Number Generation ###
						wheel_cutting_name = ''	
						wheel_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.wheel.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,wheel_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(wheel_cutting_seq_id[0],seq_rec.code))
						wheel_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'wheel_cutting_date':time.strftime('%Y-%m-%d'),'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0]})
					
					if stage_item['stage_name'] == 'GAS CUTTING':
						### Next Stage Qty ###
						gas_cutting_qty = entry.wheel_cutting_accept_qty
						### Sequence Number Generation ###
						gas_cutting_name = ''	
						gas_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.gas.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,gas_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(gas_cutting_seq_id[0],seq_rec.code))
						gas_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'gas_cutting_date':time.strftime('%Y-%m-%d'),'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0]})
					
					if stage_item['stage_name'] == 'ARC CUTTING':
						### Next Stage Qty ###
						arc_cutting_qty = entry.wheel_cutting_accept_qty
						### Sequence Number Generation ###
						arc_cutting_name = ''	
						arc_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.arc.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,arc_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(arc_cutting_seq_id[0],seq_rec.code))
						arc_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'arc_cutting_date':time.strftime('%Y-%m-%d'),'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0]})
					
					if stage_item['stage_name'] == 'HEAT TREATMENT':
						### Next Stage Qty ###
						heat_total_qty = entry.wheel_cutting_accept_qty
						self.write(cr, uid, ids, {'heat_date':time.strftime('%Y-%m-%d'),'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty})
					
					if stage_item['stage_name'] == 'ROUGH GRINDING':
						### Next Stage Qty ###
						rough_grinding_qty = entry.wheel_cutting_accept_qty
						### Sequence Number Generation ###
						rough_grinding_name = ''	
						rough_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.rough.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,rough_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(rough_grinding_seq_id[0],seq_rec.code))
						rough_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'rough_grinding_date':time.strftime('%Y-%m-%d'),'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,'rough_grinding_name':rough_grinding_name[0]})
					
					if stage_item['stage_name'] == 'FINISH GRINDING':
						### Next Stage Qty ###
						finish_grinding_qty = entry.wheel_cutting_accept_qty
						### Sequence Number Generation ###
						finish_grinding_name = ''	
						finish_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.finish.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,finish_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(finish_grinding_seq_id[0],seq_rec.code))
						finish_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'finish_grinding_date':time.strftime('%Y-%m-%d'),'finish_grinding_qty': finish_grinding_qty,'finish_grinding_accept_qty': finish_grinding_qty,'finish_grinding_name':finish_grinding_name[0]})
						
					if stage_item['stage_name'] == 'RE SHOT BLASTING':
						### Next Stage Qty ###
						reshot_blasting_qty = entry.wheel_cutting_accept_qty
						### Sequence Number Generation ###
						reshot_blasting_name = ''	
						reshot_blasting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.reshot.blasting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,reshot_blasting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(reshot_blasting_seq_id[0],seq_rec.code))
						reshot_blasting_name = cr.fetchone();
						self.write(cr, uid, ids, {'reshot_blasting_date':time.strftime('%Y-%m-%d'),'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0]})
					
					self.write(cr, uid, ids, {'pre_stage_date':entry.wheel_cutting_date,'stage_id': stage_item['stage_id']})
					
			else:
				### MS Inward Process Creation ###
				self.ms_inward_update(cr, uid, [entry.id],entry.wheel_cutting_accept_qty)
			
		if entry.wheel_cutting_reject_qty > 0:
			
			### Full Rejection Update ###
			full_reject_qty = entry.wheel_cutting_qty - entry.wheel_cutting_reject_qty
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
			
			production_vals = {
									
				'name': produc_name[0],
				'schedule_id': entry.schedule_id.id,
				'schedule_date': entry.schedule_date,
				'division_id': entry.division_id.id,
				'location' : entry.location,
				'schedule_line_id': entry.schedule_line_id.id,
				'order_id': entry.order_id.id,
				'order_line_id': entry.order_line_id.id,
				'qty' : entry.wheel_cutting_reject_qty,			  
				'schedule_qty' : entry.wheel_cutting_reject_qty,			  
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
				'core_qty': entry.wheel_cutting_reject_qty,
				'core_state': 'pending',
				'mould_no': mould_name[0],
				'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
				'mould_qty': entry.wheel_cutting_reject_qty,
				'mould_state': 'pending',		
			}
			production_id = production_obj.create(cr, uid, production_vals)
		self.write(cr, uid, ids, {'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def gas_cutting_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.gas_cutting_qty - entry.gas_cutting_accept_qty
		
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
		
		if entry.gas_cutting_accept_qty > 0:
			cr.execute(""" select fettling.stage_id,stage.name as stage_name,fettling.seq_no from ch_fettling_process as fettling
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
						knockout_qty = entry.gas_cutting_accept_qty
						### Sequence Number Generation ###
						knockout_name = ''	
						knockout_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.knock.out')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,knockout_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(knockout_seq_id[0],seq_rec.code))
						knockout_name = cr.fetchone();
						self.write(cr, uid, ids, {'knockout_date':time.strftime('%Y-%m-%d'),'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0]})
					
					if stage_item['stage_name'] == 'DECORING':
						### Next Stage Qty ###
						decoring_qty = entry.gas_cutting_accept_qty
						### Sequence Number Generation ###
						decoring_name = ''	
						decoring_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.decoring')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,decoring_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(decoring_seq_id[0],seq_rec.code))
						decoring_name = cr.fetchone();
						self.write(cr, uid, ids, {'decoring_date':time.strftime('%Y-%m-%d'),'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0]})
					
					if stage_item['stage_name'] == 'SHOT BLAST':
						### Next Stage Qty ###
						shot_blast_qty = entry.gas_cutting_accept_qty
						### Sequence Number Generation ###
						shot_blast_name = ''	
						shot_blast_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.shot.blast')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,shot_blast_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(shot_blast_seq_id[0],seq_rec.code))
						shot_blast_name = cr.fetchone();
						self.write(cr, uid, ids, {'shot_blast_date':time.strftime('%Y-%m-%d'),'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0]})
					
					if stage_item['stage_name'] == 'HAMMERING':
						### Next Stage Qty ###
						hammering_qty = entry.gas_cutting_accept_qty
						### Sequence Number Generation ###
						hammering_name = ''	
						hammering_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.hammering')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,hammering_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(hammering_seq_id[0],seq_rec.code))
						hammering_name = cr.fetchone();
						self.write(cr, uid, ids, {'hammering_date':time.strftime('%Y-%m-%d'),'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0]})
					
					if stage_item['stage_name'] == 'WHEEL CUTTING':
						### Next Stage Qty ###
						wheel_cutting_qty = entry.gas_cutting_accept_qty
						### Sequence Number Generation ###
						wheel_cutting_name = ''	
						wheel_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.wheel.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,wheel_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(wheel_cutting_seq_id[0],seq_rec.code))
						wheel_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'wheel_cutting_date':time.strftime('%Y-%m-%d'),'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0]})
					
					if stage_item['stage_name'] == 'GAS CUTTING':
						### Next Stage Qty ###
						gas_cutting_qty = entry.gas_cutting_accept_qty
						### Sequence Number Generation ###
						gas_cutting_name = ''	
						gas_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.gas.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,gas_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(gas_cutting_seq_id[0],seq_rec.code))
						gas_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'gas_cutting_date':time.strftime('%Y-%m-%d'),'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0]})
					
					if stage_item['stage_name'] == 'ARC CUTTING':
						### Next Stage Qty ###
						arc_cutting_qty = entry.gas_cutting_accept_qty
						### Sequence Number Generation ###
						arc_cutting_name = ''	
						arc_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.arc.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,arc_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(arc_cutting_seq_id[0],seq_rec.code))
						arc_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'arc_cutting_date':time.strftime('%Y-%m-%d'),'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0]})
					
					if stage_item['stage_name'] == 'HEAT TREATMENT':
						### Next Stage Qty ###
						heat_total_qty = entry.gas_cutting_accept_qty
						self.write(cr, uid, ids, {'heat_date':time.strftime('%Y-%m-%d'),'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty})
					
					if stage_item['stage_name'] == 'ROUGH GRINDING':
						### Next Stage Qty ###
						rough_grinding_qty = entry.gas_cutting_accept_qty
						### Sequence Number Generation ###
						rough_grinding_name = ''	
						rough_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.rough.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,rough_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(rough_grinding_seq_id[0],seq_rec.code))
						rough_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'rough_grinding_date':time.strftime('%Y-%m-%d'),'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,'rough_grinding_name':rough_grinding_name[0]})
					
					if stage_item['stage_name'] == 'FINISH GRINDING':
						### Next Stage Qty ###
						finish_grinding_qty = entry.gas_cutting_accept_qty
						### Sequence Number Generation ###
						finish_grinding_name = ''	
						finish_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.finish.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,finish_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(finish_grinding_seq_id[0],seq_rec.code))
						finish_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'finish_grinding_date':time.strftime('%Y-%m-%d'),'finish_grinding_qty': finish_grinding_qty,'finish_grinding_accept_qty': finish_grinding_qty,'finish_grinding_name':finish_grinding_name[0]})
						
					if stage_item['stage_name'] == 'RE SHOT BLASTING':
						### Next Stage Qty ###
						reshot_blasting_qty = entry.gas_cutting_accept_qty
						### Sequence Number Generation ###
						reshot_blasting_name = ''	
						reshot_blasting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.reshot.blasting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,reshot_blasting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(reshot_blasting_seq_id[0],seq_rec.code))
						reshot_blasting_name = cr.fetchone();
						self.write(cr, uid, ids, {'reshot_blasting_date':time.strftime('%Y-%m-%d'),'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0]})
					
					self.write(cr, uid, ids, {'pre_stage_date':entry.gas_cutting_date,'stage_id': stage_item['stage_id']})
					
			else:
				### MS Inward Process Creation ###
				self.ms_inward_update(cr, uid, [entry.id],entry.gas_cutting_accept_qty)
			
		if entry.gas_cutting_reject_qty > 0:
			
			### Full Rejection Update ###
			full_reject_qty = entry.gas_cutting_qty - entry.gas_cutting_reject_qty
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
			
			production_vals = {
									
				'name': produc_name[0],
				'schedule_id': entry.schedule_id.id,
				'schedule_date': entry.schedule_date,
				'division_id': entry.division_id.id,
				'location' : entry.location,
				'schedule_line_id': entry.schedule_line_id.id,
				'order_id': entry.order_id.id,
				'order_line_id': entry.order_line_id.id,
				'qty' : entry.gas_cutting_reject_qty,			  
				'schedule_qty' : entry.gas_cutting_reject_qty,			  
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
				'core_qty': entry.gas_cutting_reject_qty,
				'core_state': 'pending',
				'mould_no': mould_name[0],
				'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
				'mould_qty': entry.gas_cutting_reject_qty,
				'mould_state': 'pending',		
			}
			production_id = production_obj.create(cr, uid, production_vals)
		self.write(cr, uid, ids, {'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
		
	def arc_cutting_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.arc_cutting_qty - entry.arc_cutting_accept_qty
		
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
		
		if entry.arc_cutting_accept_qty > 0:
			cr.execute(""" select fettling.stage_id,stage.name as stage_name,fettling.seq_no from ch_fettling_process as fettling
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
						knockout_qty = entry.arc_cutting_accept_qty
						### Sequence Number Generation ###
						knockout_name = ''	
						knockout_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.knock.out')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,knockout_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(knockout_seq_id[0],seq_rec.code))
						knockout_name = cr.fetchone();
						self.write(cr, uid, ids, {'knockout_date':time.strftime('%Y-%m-%d'),'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0]})
					
					if stage_item['stage_name'] == 'DECORING':
						### Next Stage Qty ###
						decoring_qty = entry.arc_cutting_accept_qty
						### Sequence Number Generation ###
						decoring_name = ''	
						decoring_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.decoring')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,decoring_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(decoring_seq_id[0],seq_rec.code))
						decoring_name = cr.fetchone();
						self.write(cr, uid, ids, {'decoring_date':time.strftime('%Y-%m-%d'),'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0]})
					
					if stage_item['stage_name'] == 'SHOT BLAST':
						### Next Stage Qty ###
						shot_blast_qty = entry.arc_cutting_accept_qty
						### Sequence Number Generation ###
						shot_blast_name = ''	
						shot_blast_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.shot.blast')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,shot_blast_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(shot_blast_seq_id[0],seq_rec.code))
						shot_blast_name = cr.fetchone();
						self.write(cr, uid, ids, {'shot_blast_date':time.strftime('%Y-%m-%d'),'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0]})
					
					if stage_item['stage_name'] == 'HAMMERING':
						### Next Stage Qty ###
						hammering_qty = entry.arc_cutting_accept_qty
						### Sequence Number Generation ###
						hammering_name = ''	
						hammering_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.hammering')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,hammering_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(hammering_seq_id[0],seq_rec.code))
						hammering_name = cr.fetchone();
						self.write(cr, uid, ids, {'hammering_date':time.strftime('%Y-%m-%d'),'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0]})
					
					if stage_item['stage_name'] == 'WHEEL CUTTING':
						### Next Stage Qty ###
						wheel_cutting_qty = entry.arc_cutting_accept_qty
						### Sequence Number Generation ###
						wheel_cutting_name = ''	
						wheel_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.wheel.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,wheel_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(wheel_cutting_seq_id[0],seq_rec.code))
						wheel_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'wheel_cutting_date':time.strftime('%Y-%m-%d'),'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0]})
					
					if stage_item['stage_name'] == 'GAS CUTTING':
						### Next Stage Qty ###
						gas_cutting_qty = entry.arc_cutting_accept_qty
						### Sequence Number Generation ###
						gas_cutting_name = ''	
						gas_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.gas.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,gas_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(gas_cutting_seq_id[0],seq_rec.code))
						gas_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'gas_cutting_date':time.strftime('%Y-%m-%d'),'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0]})
					
					if stage_item['stage_name'] == 'ARC CUTTING':
						### Next Stage Qty ###
						arc_cutting_qty = entry.arc_cutting_accept_qty
						### Sequence Number Generation ###
						arc_cutting_name = ''	
						arc_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.arc.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,arc_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(arc_cutting_seq_id[0],seq_rec.code))
						arc_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'arc_cutting_date':time.strftime('%Y-%m-%d'),'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0]})
					
					if stage_item['stage_name'] == 'HEAT TREATMENT':
						### Next Stage Qty ###
						heat_total_qty = entry.arc_cutting_accept_qty
						self.write(cr, uid, ids, {'heat_date':time.strftime('%Y-%m-%d'),'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty})
					
					if stage_item['stage_name'] == 'ROUGH GRINDING':
						### Next Stage Qty ###
						rough_grinding_qty = entry.arc_cutting_accept_qty
						### Sequence Number Generation ###
						rough_grinding_name = ''	
						rough_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.rough.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,rough_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(rough_grinding_seq_id[0],seq_rec.code))
						rough_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'rough_grinding_date':time.strftime('%Y-%m-%d'),'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,'rough_grinding_name':rough_grinding_name[0]})
					
					if stage_item['stage_name'] == 'FINISH GRINDING':
						### Next Stage Qty ###
						finish_grinding_qty = entry.arc_cutting_accept_qty
						### Sequence Number Generation ###
						finish_grinding_name = ''	
						finish_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.finish.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,finish_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(finish_grinding_seq_id[0],seq_rec.code))
						finish_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'finish_grinding_date':time.strftime('%Y-%m-%d'),'finish_grinding_qty': finish_grinding_qty,'finish_grinding_accept_qty': finish_grinding_qty,'finish_grinding_name':finish_grinding_name[0]})
						
					if stage_item['stage_name'] == 'RE SHOT BLASTING':
						### Next Stage Qty ###
						reshot_blasting_qty = entry.arc_cutting_accept_qty
						### Sequence Number Generation ###
						reshot_blasting_name = ''	
						reshot_blasting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.reshot.blasting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,reshot_blasting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(reshot_blasting_seq_id[0],seq_rec.code))
						reshot_blasting_name = cr.fetchone();
						self.write(cr, uid, ids, {'reshot_blasting_date':time.strftime('%Y-%m-%d'),'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0]})
					
					self.write(cr, uid, ids, {'pre_stage_date':entry.arc_cutting_date,'stage_id': stage_item['stage_id']})
					
			else:
				### MS Inward Process Creation ###
				self.ms_inward_update(cr, uid, [entry.id],entry.arc_cutting_accept_qty)
			
		if entry.arc_cutting_reject_qty > 0:
			
			### Full Rejection Update ###
			full_reject_qty = entry.arc_cutting_qty - entry.arc_cutting_reject_qty
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
			
			production_vals = {
									
				'name': produc_name[0],
				'schedule_id': entry.schedule_id.id,
				'schedule_date': entry.schedule_date,
				'division_id': entry.division_id.id,
				'location' : entry.location,
				'schedule_line_id': entry.schedule_line_id.id,
				'order_id': entry.order_id.id,
				'order_line_id': entry.order_line_id.id,
				'qty' : entry.arc_cutting_reject_qty,			  
				'schedule_qty' : entry.arc_cutting_reject_qty,			  
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
				'core_qty': entry.arc_cutting_reject_qty,
				'core_state': 'pending',
				'mould_no': mould_name[0],
				'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
				'mould_qty': entry.arc_cutting_reject_qty,
				'mould_state': 'pending',		
			}
			production_id = production_obj.create(cr, uid, production_vals)
		self.write(cr, uid, ids, {'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def heat_treatment_update(self,cr,uid,ids,context=None):
		total_wt = 0
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
						
		reject_qty = entry.heat_total_qty - entry.heat_qty
		
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
		
		if entry.heat_qty > 0:
			cr.execute(""" select fettling.stage_id,stage.name as stage_name,fettling.seq_no from ch_fettling_process as fettling
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
						knockout_qty = entry.heat_qty
						### Sequence Number Generation ###
						knockout_name = ''	
						knockout_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.knock.out')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,knockout_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(knockout_seq_id[0],seq_rec.code))
						knockout_name = cr.fetchone();
						self.write(cr, uid, ids, {'knockout_date':time.strftime('%Y-%m-%d'),'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0]})
					
					if stage_item['stage_name'] == 'DECORING':
						### Next Stage Qty ###
						decoring_qty = entry.heat_qty
						### Sequence Number Generation ###
						decoring_name = ''	
						decoring_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.decoring')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,decoring_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(decoring_seq_id[0],seq_rec.code))
						decoring_name = cr.fetchone();
						self.write(cr, uid, ids, {'decoring_date':time.strftime('%Y-%m-%d'),'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0]})
					
					if stage_item['stage_name'] == 'SHOT BLAST':
						### Next Stage Qty ###
						shot_blast_qty = entry.heat_qty
						### Sequence Number Generation ###
						shot_blast_name = ''	
						shot_blast_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.shot.blast')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,shot_blast_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(shot_blast_seq_id[0],seq_rec.code))
						shot_blast_name = cr.fetchone();
						self.write(cr, uid, ids, {'shot_blast_date':time.strftime('%Y-%m-%d'),'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0]})
					
					if stage_item['stage_name'] == 'HAMMERING':
						### Next Stage Qty ###
						hammering_qty = entry.heat_qty
						### Sequence Number Generation ###
						hammering_name = ''	
						hammering_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.hammering')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,hammering_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(hammering_seq_id[0],seq_rec.code))
						hammering_name = cr.fetchone();
						self.write(cr, uid, ids, {'hammering_date':time.strftime('%Y-%m-%d'),'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0]})
					
					if stage_item['stage_name'] == 'WHEEL CUTTING':
						### Next Stage Qty ###
						wheel_cutting_qty = entry.heat_qty
						### Sequence Number Generation ###
						wheel_cutting_name = ''	
						wheel_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.wheel.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,wheel_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(wheel_cutting_seq_id[0],seq_rec.code))
						wheel_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'wheel_cutting_date':time.strftime('%Y-%m-%d'),'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0]})
					
					if stage_item['stage_name'] == 'GAS CUTTING':
						### Next Stage Qty ###
						gas_cutting_qty = entry.heat_qty
						### Sequence Number Generation ###
						gas_cutting_name = ''	
						gas_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.gas.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,gas_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(gas_cutting_seq_id[0],seq_rec.code))
						gas_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'gas_cutting_date':time.strftime('%Y-%m-%d'),'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0]})
					
					if stage_item['stage_name'] == 'ARC CUTTING':
						### Next Stage Qty ###
						arc_cutting_qty = entry.heat_qty
						### Sequence Number Generation ###
						arc_cutting_name = ''	
						arc_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.arc.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,arc_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(arc_cutting_seq_id[0],seq_rec.code))
						arc_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'arc_cutting_date':time.strftime('%Y-%m-%d'),'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0]})
					
					if stage_item['stage_name'] == 'HEAT TREATMENT':
						### Next Stage Qty ###
						heat_total_qty = entry.heat_qty
						self.write(cr, uid, ids, {'heat_date':time.strftime('%Y-%m-%d'),'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty})
					
					if stage_item['stage_name'] == 'ROUGH GRINDING':
						### Next Stage Qty ###
						rough_grinding_qty = entry.heat_qty
						### Sequence Number Generation ###
						rough_grinding_name = ''	
						rough_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.rough.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,rough_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(rough_grinding_seq_id[0],seq_rec.code))
						rough_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'rough_grinding_date':time.strftime('%Y-%m-%d'),'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,'rough_grinding_name':rough_grinding_name[0]})
					
					if stage_item['stage_name'] == 'FINISH GRINDING':
						### Next Stage Qty ###
						finish_grinding_qty = entry.heat_qty
						### Sequence Number Generation ###
						finish_grinding_name = ''	
						finish_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.finish.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,finish_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(finish_grinding_seq_id[0],seq_rec.code))
						finish_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'finish_grinding_date':time.strftime('%Y-%m-%d'),'finish_grinding_qty': finish_grinding_qty,'finish_grinding_accept_qty': finish_grinding_qty,'finish_grinding_name':finish_grinding_name[0]})
						
					if stage_item['stage_name'] == 'RE SHOT BLASTING':
						### Next Stage Qty ###
						reshot_blasting_qty = entry.heat_qty
						### Sequence Number Generation ###
						reshot_blasting_name = ''	
						reshot_blasting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.reshot.blasting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,reshot_blasting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(reshot_blasting_seq_id[0],seq_rec.code))
						reshot_blasting_name = cr.fetchone();
						self.write(cr, uid, ids, {'reshot_blasting_date':time.strftime('%Y-%m-%d'),'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0]})
					
					self.write(cr, uid, ids, {'pre_stage_date':entry.heat_date,'stage_id': stage_item['stage_id']})
					
			else:
				### MS Inward Process Creation ###
				self.ms_inward_update(cr, uid, [entry.id],entry.heat_qty)
				
		if entry.heat_reject_qty > 0:
			
			### Full Rejection Update ###
			full_reject_qty = entry.heat_total_qty - entry.heat_reject_qty
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
			
			production_vals = {
									
				'name': produc_name[0],
				'schedule_id': entry.schedule_id.id,
				'schedule_date': entry.schedule_date,
				'division_id': entry.division_id.id,
				'location' : entry.location,
				'schedule_line_id': entry.schedule_line_id.id,
				'order_id': entry.order_id.id,
				'order_line_id': entry.order_line_id.id,
				'qty' : entry.heat_reject_qty,			  
				'schedule_qty' : entry.heat_reject_qty,			  
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
				'core_qty': entry.heat_reject_qty,
				'core_state': 'pending',
				'mould_no': mould_name[0],
				'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
				'mould_qty': entry.heat_reject_qty,
				'mould_state': 'pending',		
			}
			production_id = production_obj.create(cr, uid, production_vals)	
				
			### Updating Total Weight ###
			total_wt = entry.heat_qty * entry.heat_each_weight 
			self.write(cr, uid, ids, {'heat_total_weight': total_wt,'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
		
	def rough_grinding_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.rough_grinding_qty - entry.rough_grinding_accept_qty
		
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
		
		if entry.rough_grinding_accept_qty > 0:
			cr.execute(""" select fettling.stage_id,stage.name as stage_name,fettling.seq_no from ch_fettling_process as fettling
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
						knockout_qty = entry.rough_grinding_accept_qty
						### Sequence Number Generation ###
						knockout_name = ''	
						knockout_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.knock.out')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,knockout_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(knockout_seq_id[0],seq_rec.code))
						knockout_name = cr.fetchone();
						self.write(cr, uid, ids, {'knockout_date':time.strftime('%Y-%m-%d'),'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0]})
					
					if stage_item['stage_name'] == 'DECORING':
						### Next Stage Qty ###
						decoring_qty = entry.rough_grinding_accept_qty
						### Sequence Number Generation ###
						decoring_name = ''	
						decoring_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.decoring')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,decoring_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(decoring_seq_id[0],seq_rec.code))
						decoring_name = cr.fetchone();
						self.write(cr, uid, ids, {'decoring_date':time.strftime('%Y-%m-%d'),'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0]})
					
					if stage_item['stage_name'] == 'SHOT BLAST':
						### Next Stage Qty ###
						shot_blast_qty = entry.rough_grinding_accept_qty
						### Sequence Number Generation ###
						shot_blast_name = ''	
						shot_blast_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.shot.blast')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,shot_blast_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(shot_blast_seq_id[0],seq_rec.code))
						shot_blast_name = cr.fetchone();
						self.write(cr, uid, ids, {'shot_blast_date':time.strftime('%Y-%m-%d'),'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0]})
					
					if stage_item['stage_name'] == 'HAMMERING':
						### Next Stage Qty ###
						hammering_qty = entry.rough_grinding_accept_qty
						### Sequence Number Generation ###
						hammering_name = ''	
						hammering_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.hammering')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,hammering_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(hammering_seq_id[0],seq_rec.code))
						hammering_name = cr.fetchone();
						self.write(cr, uid, ids, {'hammering_date':time.strftime('%Y-%m-%d'),'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0]})
					
					if stage_item['stage_name'] == 'WHEEL CUTTING':
						### Next Stage Qty ###
						wheel_cutting_qty = entry.rough_grinding_accept_qty
						### Sequence Number Generation ###
						wheel_cutting_name = ''	
						wheel_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.wheel.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,wheel_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(wheel_cutting_seq_id[0],seq_rec.code))
						wheel_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'wheel_cutting_date':time.strftime('%Y-%m-%d'),'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0]})
					
					if stage_item['stage_name'] == 'GAS CUTTING':
						### Next Stage Qty ###
						gas_cutting_qty = entry.rough_grinding_accept_qty
						### Sequence Number Generation ###
						gas_cutting_name = ''	
						gas_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.gas.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,gas_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(gas_cutting_seq_id[0],seq_rec.code))
						gas_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'gas_cutting_date':time.strftime('%Y-%m-%d'),'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0]})
					
					if stage_item['stage_name'] == 'ARC CUTTING':
						### Next Stage Qty ###
						arc_cutting_qty = entry.rough_grinding_accept_qty
						### Sequence Number Generation ###
						arc_cutting_name = ''	
						arc_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.arc.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,arc_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(arc_cutting_seq_id[0],seq_rec.code))
						arc_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'arc_cutting_date':time.strftime('%Y-%m-%d'),'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0]})
					
					if stage_item['stage_name'] == 'HEAT TREATMENT':
						### Next Stage Qty ###
						heat_total_qty = entry.rough_grinding_accept_qty
						self.write(cr, uid, ids, {'heat_date':time.strftime('%Y-%m-%d'),'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty})
					
					if stage_item['stage_name'] == 'ROUGH GRINDING':
						### Next Stage Qty ###
						rough_grinding_qty = entry.rough_grinding_accept_qty
						### Sequence Number Generation ###
						rough_grinding_name = ''	
						rough_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.rough.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,rough_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(rough_grinding_seq_id[0],seq_rec.code))
						rough_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'rough_grinding_date':time.strftime('%Y-%m-%d'),'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,'rough_grinding_name':rough_grinding_name[0]})
					
					if stage_item['stage_name'] == 'FINISH GRINDING':
						### Next Stage Qty ###
						finish_grinding_qty = entry.rough_grinding_accept_qty
						### Sequence Number Generation ###
						finish_grinding_name = ''	
						finish_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.finish.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,finish_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(finish_grinding_seq_id[0],seq_rec.code))
						finish_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'finish_grinding_date':time.strftime('%Y-%m-%d'),'finish_grinding_qty': finish_grinding_qty,'finish_grinding_accept_qty': finish_grinding_qty,'finish_grinding_name':finish_grinding_name[0]})
						
					if stage_item['stage_name'] == 'RE SHOT BLASTING':
						### Next Stage Qty ###
						reshot_blasting_qty = entry.rough_grinding_accept_qty
						### Sequence Number Generation ###
						reshot_blasting_name = ''	
						reshot_blasting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.reshot.blasting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,reshot_blasting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(reshot_blasting_seq_id[0],seq_rec.code))
						reshot_blasting_name = cr.fetchone();
						self.write(cr, uid, ids, {'reshot_blasting_date':time.strftime('%Y-%m-%d'),'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0]})
					
					self.write(cr, uid, ids, {'pre_stage_date':entry.rough_grinding_date,'stage_id': stage_item['stage_id']})
					
			else:
				### MS Inward Process Creation ###
				self.ms_inward_update(cr, uid, [entry.id],entry.rough_grinding_accept_qty)
				
				
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
			
		if entry.rough_grinding_reject_qty > 0:
			
			### Full Rejection Update ###
			full_reject_qty = entry.rough_grinding_qty - entry.rough_grinding_reject_qty
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
			
			production_vals = {
									
				'name': produc_name[0],
				'schedule_id': entry.schedule_id.id,
				'schedule_date': entry.schedule_date,
				'division_id': entry.division_id.id,
				'location' : entry.location,
				'schedule_line_id': entry.schedule_line_id.id,
				'order_id': entry.order_id.id,
				'order_line_id': entry.order_line_id.id,
				'qty' : entry.rough_grinding_reject_qty,			  
				'schedule_qty' : entry.rough_grinding_reject_qty,			  
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
				'core_qty': entry.rough_grinding_reject_qty,
				'core_state': 'pending',
				'mould_no': mould_name[0],
				'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
				'mould_qty': entry.rough_grinding_reject_qty,
				'mould_state': 'pending',		
			}
			production_id = production_obj.create(cr, uid, production_vals)
		self.write(cr, uid, ids, {'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def welding_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.welding_qty - entry.welding_accept_qty
		
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
			
			self.write(cr, uid, ids, {'welding_state':'done'})
				
		if entry.welding_reject_qty > 0:
			
			### Full Rejection Update ###
			full_reject_qty = entry.welding_qty - entry.welding_reject_qty
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
			
			production_vals = {
									
				'name': produc_name[0],
				'schedule_id': entry.schedule_id.id,
				'schedule_date': entry.schedule_date,
				'division_id': entry.division_id.id,
				'location' : entry.location,
				'schedule_line_id': entry.schedule_line_id.id,
				'order_id': entry.order_id.id,
				'order_line_id': entry.order_line_id.id,
				'qty' : entry.welding_reject_qty,			  
				'schedule_qty' : entry.welding_reject_qty,			  
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
				'core_qty': entry.welding_reject_qty,
				'core_state': 'pending',
				'mould_no': mould_name[0],
				'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
				'mould_qty': entry.welding_reject_qty,
				'mould_state': 'pending',		
			}
			production_id = production_obj.create(cr, uid, production_vals)
			
		self.write(cr, uid, ids, {'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def finish_grinding_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.finish_grinding_qty - entry.finish_grinding_accept_qty
	
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
		
		
			if entry.finish_grinding_accept_qty > 0:
				cr.execute(""" select fettling.stage_id,stage.name as stage_name,fettling.seq_no from ch_fettling_process as fettling
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
							knockout_qty = entry.finish_grinding_accept_qty
							### Sequence Number Generation ###
							knockout_name = ''	
							knockout_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.knock.out')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,knockout_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(knockout_seq_id[0],seq_rec.code))
							knockout_name = cr.fetchone();
							self.write(cr, uid, ids, {'knockout_date':time.strftime('%Y-%m-%d'),'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0]})
						
						if stage_item['stage_name'] == 'DECORING':
							### Next Stage Qty ###
							decoring_qty = entry.finish_grinding_accept_qty
							### Sequence Number Generation ###
							decoring_name = ''	
							decoring_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.decoring')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,decoring_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(decoring_seq_id[0],seq_rec.code))
							decoring_name = cr.fetchone();
							self.write(cr, uid, ids, {'decoring_date':time.strftime('%Y-%m-%d'),'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0]})
						
						if stage_item['stage_name'] == 'SHOT BLAST':
							### Next Stage Qty ###
							shot_blast_qty = entry.finish_grinding_accept_qty
							### Sequence Number Generation ###
							shot_blast_name = ''	
							shot_blast_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.shot.blast')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,shot_blast_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(shot_blast_seq_id[0],seq_rec.code))
							shot_blast_name = cr.fetchone();
							self.write(cr, uid, ids, {'shot_blast_date':time.strftime('%Y-%m-%d'),'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0]})
						
						if stage_item['stage_name'] == 'HAMMERING':
							### Next Stage Qty ###
							hammering_qty = entry.finish_grinding_accept_qty
							### Sequence Number Generation ###
							hammering_name = ''	
							hammering_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.hammering')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,hammering_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(hammering_seq_id[0],seq_rec.code))
							hammering_name = cr.fetchone();
							self.write(cr, uid, ids, {'hammering_date':time.strftime('%Y-%m-%d'),'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0]})
						
						if stage_item['stage_name'] == 'WHEEL CUTTING':
							### Next Stage Qty ###
							wheel_cutting_qty = entry.finish_grinding_accept_qty
							### Sequence Number Generation ###
							wheel_cutting_name = ''	
							wheel_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.wheel.cutting')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,wheel_cutting_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(wheel_cutting_seq_id[0],seq_rec.code))
							wheel_cutting_name = cr.fetchone();
							self.write(cr, uid, ids, {'wheel_cutting_date':time.strftime('%Y-%m-%d'),'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0]})
						
						if stage_item['stage_name'] == 'GAS CUTTING':
							### Next Stage Qty ###
							gas_cutting_qty = entry.finish_grinding_accept_qty
							### Sequence Number Generation ###
							gas_cutting_name = ''	
							gas_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.gas.cutting')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,gas_cutting_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(gas_cutting_seq_id[0],seq_rec.code))
							gas_cutting_name = cr.fetchone();
							self.write(cr, uid, ids, {'gas_cutting_date':time.strftime('%Y-%m-%d'),'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0]})
						
						if stage_item['stage_name'] == 'ARC CUTTING':
							### Next Stage Qty ###
							arc_cutting_qty = entry.finish_grinding_accept_qty
							### Sequence Number Generation ###
							arc_cutting_name = ''	
							arc_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.arc.cutting')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,arc_cutting_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(arc_cutting_seq_id[0],seq_rec.code))
							arc_cutting_name = cr.fetchone();
							self.write(cr, uid, ids, {'arc_cutting_date':time.strftime('%Y-%m-%d'),'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0]})
						
						if stage_item['stage_name'] == 'HEAT TREATMENT':
							### Next Stage Qty ###
							heat_total_qty = entry.finish_grinding_accept_qty
							self.write(cr, uid, ids, {'heat_date':time.strftime('%Y-%m-%d'),'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty})
						
						if stage_item['stage_name'] == 'ROUGH GRINDING':
							### Next Stage Qty ###
							rough_grinding_qty = entry.finish_grinding_accept_qty
							### Sequence Number Generation ###
							rough_grinding_name = ''	
							rough_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.rough.grinding')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,rough_grinding_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(rough_grinding_seq_id[0],seq_rec.code))
							rough_grinding_name = cr.fetchone();
							self.write(cr, uid, ids, {'rough_grinding_date':time.strftime('%Y-%m-%d'),'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,'rough_grinding_name':rough_grinding_name[0]})
						
						if stage_item['stage_name'] == 'FINISH GRINDING':
							### Next Stage Qty ###
							finish_grinding_qty = entry.finish_grinding_accept_qty
							### Sequence Number Generation ###
							finish_grinding_name = ''	
							finish_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.finish.grinding')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,finish_grinding_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(finish_grinding_seq_id[0],seq_rec.code))
							finish_grinding_name = cr.fetchone();
							self.write(cr, uid, ids, {'finish_grinding_date':time.strftime('%Y-%m-%d'),'finish_grinding_qty': finish_grinding_qty,'finish_grinding_accept_qty': finish_grinding_qty,'finish_grinding_name':finish_grinding_name[0]})
							
						if stage_item['stage_name'] == 'RE SHOT BLASTING':
							### Next Stage Qty ###
							reshot_blasting_qty = entry.finish_grinding_accept_qty
							### Sequence Number Generation ###
							reshot_blasting_name = ''	
							reshot_blasting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.reshot.blasting')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,reshot_blasting_seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(reshot_blasting_seq_id[0],seq_rec.code))
							reshot_blasting_name = cr.fetchone();
							self.write(cr, uid, ids, {'reshot_blasting_date':time.strftime('%Y-%m-%d'),'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0]})
						
						self.write(cr, uid, ids, {'pre_stage_date':entry.finish_grinding_date,'stage_id': stage_item['stage_id']})
						
				else:
					###  MS Inward Process Creation ###
					self.ms_inward_update(cr, uid, [entry.id],entry.finish_grinding_accept_qty)
			
		if entry.finish_grinding_reject_qty > 0:
			
			### Full Rejection Update ###
			full_reject_qty = entry.finish_grinding_qty - entry.finish_grinding_reject_qty
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
			
			production_vals = {
									
				'name': produc_name[0],
				'schedule_id': entry.schedule_id.id,
				'schedule_date': entry.schedule_date,
				'division_id': entry.division_id.id,
				'location' : entry.location,
				'schedule_line_id': entry.schedule_line_id.id,
				'order_id': entry.order_id.id,
				'order_line_id': entry.order_line_id.id,
				'qty' : entry.finish_grinding_reject_qty,			  
				'schedule_qty' : entry.finish_grinding_reject_qty,			  
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
				'core_qty': entry.finish_grinding_reject_qty,
				'core_state': 'pending',
				'mould_no': mould_name[0],
				'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
				'mould_qty': entry.finish_grinding_reject_qty,
				'mould_state': 'pending',		
			}
			production_id = production_obj.create(cr, uid, production_vals)
		self.write(cr, uid, ids, {'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def reshot_blasting_update(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr, uid, ids[0])
		reject_qty = entry.reshot_blasting_qty - entry.reshot_blasting_accept_qty
	
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
		
		if entry.reshot_blasting_accept_qty > 0:
			cr.execute(""" select fettling.stage_id,stage.name as stage_name,fettling.seq_no from ch_fettling_process as fettling
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
						knockout_qty = entry.reshot_blasting_accept_qty
						### Sequence Number Generation ###
						knockout_name = ''	
						knockout_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.knock.out')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,knockout_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(knockout_seq_id[0],seq_rec.code))
						knockout_name = cr.fetchone();
						self.write(cr, uid, ids, {'knockout_date':time.strftime('%Y-%m-%d'),'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0]})
					
					if stage_item['stage_name'] == 'DECORING':
						### Next Stage Qty ###
						decoring_qty = entry.reshot_blasting_accept_qty
						### Sequence Number Generation ###
						decoring_name = ''	
						decoring_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.decoring')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,decoring_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(decoring_seq_id[0],seq_rec.code))
						decoring_name = cr.fetchone();
						self.write(cr, uid, ids, {'decoring_date':time.strftime('%Y-%m-%d'),'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0]})
					
					if stage_item['stage_name'] == 'SHOT BLAST':
						### Next Stage Qty ###
						shot_blast_qty = entry.reshot_blasting_accept_qty
						### Sequence Number Generation ###
						shot_blast_name = ''	
						shot_blast_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.shot.blast')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,shot_blast_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(shot_blast_seq_id[0],seq_rec.code))
						shot_blast_name = cr.fetchone();
						self.write(cr, uid, ids, {'shot_blast_date':time.strftime('%Y-%m-%d'),'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0]})
					
					if stage_item['stage_name'] == 'HAMMERING':
						### Next Stage Qty ###
						hammering_qty = entry.reshot_blasting_accept_qty
						### Sequence Number Generation ###
						hammering_name = ''	
						hammering_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.hammering')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,hammering_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(hammering_seq_id[0],seq_rec.code))
						hammering_name = cr.fetchone();
						self.write(cr, uid, ids, {'hammering_date':time.strftime('%Y-%m-%d'),'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0]})
					
					if stage_item['stage_name'] == 'WHEEL CUTTING':
						### Next Stage Qty ###
						wheel_cutting_qty = entry.reshot_blasting_accept_qty
						### Sequence Number Generation ###
						wheel_cutting_name = ''	
						wheel_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.wheel.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,wheel_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(wheel_cutting_seq_id[0],seq_rec.code))
						wheel_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'wheel_cutting_date':time.strftime('%Y-%m-%d'),'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0]})
					
					if stage_item['stage_name'] == 'GAS CUTTING':
						### Next Stage Qty ###
						gas_cutting_qty = entry.reshot_blasting_accept_qty
						### Sequence Number Generation ###
						gas_cutting_name = ''	
						gas_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.gas.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,gas_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(gas_cutting_seq_id[0],seq_rec.code))
						gas_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'gas_cutting_date':time.strftime('%Y-%m-%d'),'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0]})
					
					if stage_item['stage_name'] == 'ARC CUTTING':
						### Next Stage Qty ###
						arc_cutting_qty = entry.reshot_blasting_accept_qty
						### Sequence Number Generation ###
						arc_cutting_name = ''	
						arc_cutting_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.arc.cutting')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,arc_cutting_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(arc_cutting_seq_id[0],seq_rec.code))
						arc_cutting_name = cr.fetchone();
						self.write(cr, uid, ids, {'arc_cutting_date':time.strftime('%Y-%m-%d'),'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0]})
					
					if stage_item['stage_name'] == 'HEAT TREATMENT':
						### Next Stage Qty ###
						heat_total_qty = entry.reshot_blasting_accept_qty
						self.write(cr, uid, ids, {'heat_date':time.strftime('%Y-%m-%d'),'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty})
					
					if stage_item['stage_name'] == 'ROUGH GRINDING':
						### Next Stage Qty ###
						rough_grinding_qty = entry.reshot_blasting_accept_qty
						### Sequence Number Generation ###
						rough_grinding_name = ''	
						rough_grinding_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.rough.grinding')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,rough_grinding_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(rough_grinding_seq_id[0],seq_rec.code))
						rough_grinding_name = cr.fetchone();
						self.write(cr, uid, ids, {'rough_grinding_date':time.strftime('%Y-%m-%d'),'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,'rough_grinding_name':rough_grinding_name[0]})
					
					if stage_item['stage_name'] == 'FINISH GRINDING':
						### Next Stage Qty ###
						finish_grinding_qty = entry.reshot_blasting_accept_qty
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
						self.write(cr, uid, ids, {'reshot_blasting_date':time.strftime('%Y-%m-%d'),'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0]})
					
					self.write(cr, uid, ids, {'pre_stage_date':entry.reshot_blasting_date,'stage_id': stage_item['stage_id']})
					
			else:
				###  MS Inward Process Creation ###
				self.ms_inward_update(cr, uid, [entry.id],entry.reshot_blasting_accept_qty)
			
		if entry.reshot_blasting_reject_qty > 0:
			
			### Full Rejection Update ###
			full_reject_qty = entry.reshot_blasting_qty - entry.reshot_blasting_reject_qty
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
			
			production_vals = {
									
				'name': produc_name[0],
				'schedule_id': entry.schedule_id.id,
				'schedule_date': entry.schedule_date,
				'division_id': entry.division_id.id,
				'location' : entry.location,
				'schedule_line_id': entry.schedule_line_id.id,
				'order_id': entry.order_id.id,
				'order_line_id': entry.order_line_id.id,
				'qty' : entry.reshot_blasting_reject_qty,			  
				'schedule_qty' : entry.reshot_blasting_reject_qty,			  
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
				'core_qty': entry.reshot_blasting_reject_qty,
				'core_state': 'pending',
				'mould_no': mould_name[0],
				'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
				'mould_qty': entry.reshot_blasting_reject_qty,
				'mould_state': 'pending',		
			}
			production_id = production_obj.create(cr, uid, production_vals)
		self.write(cr, uid, ids, {'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
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
			domain="[('stage_name','=','KNOCK OUT'),('state','=','accept')]"),
			
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
			domain="[('stage_name','=','FINISH GRINDING'),('state','=','accept')]"),
			
		'line_ids': fields.one2many('ch.batch.finish.grinding.line', 'header_id', "Batch Line Details"),
		
		'flag_batchline':fields.boolean('Batch Line Created'),
		
		'finish_grinding_date': fields.date('Date', store=True, required=True),
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
					'remarks':  entry.remarks
				}
				
				line_id = line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_batchline': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
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
			})
			fettling_obj.finish_grinding_update(cr, uid, [item.finish_grinding_id.id])
			
		### Sequence Number Generation  ###
		batch_name = ''	
		batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.batch.finish.grinding')])
		seq_rec = self.pool.get('ir.sequence').browse(cr,uid,batch_seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s','%s') """%(batch_seq_id[0],seq_rec.code,entry.entry_date))
		batch_name = cr.fetchone();
		self.write(cr, uid, ids, {'name':batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
	
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
















