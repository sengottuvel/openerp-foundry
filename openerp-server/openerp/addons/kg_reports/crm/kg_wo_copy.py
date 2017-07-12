from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import os
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_wo_copy(osv.osv):
	
	_name = "kg.wo.copy"
	_description = "WO Copy"
	_order = "entry_date desc"
	
	_columns = {
		
		## Version 0.1
		
		## Basic Info
		
		'name': fields.char('No', size=12,select=True,readonly=True),
		'entry_date': fields.date('Entry Date',required=True,readonly=True),		
		'note': fields.text('Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		
		## Entry Info
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),	
		'active': fields.boolean('Active'),
		'crt_date': fields.datetime('Created Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),		
		'ap_rej_date': fields.datetime('Approved/Rejected Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Rejected By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),			
		
		## Module Requirement Info
		
		'wo_id': fields.many2one('kg.work.order','WO No.',required=True),
		'enq_id': fields.many2one('kg.crm.enquiry','Enq No.'),
		'report_template': fields.selection([('1','Horizontal non slurry'),('2','Horizontal slurry'),('3','Vertical non slurry'),('4','Vertical slurry')],'Template',required=True),
		
		'attachment':fields.binary('Soft Copy 1'),
		'attachment_1':fields.binary('Soft Copy 2'),
		
		'line_ids': fields.related('enq_id','ch_line_ids', type='one2many', relation='ch.kg.crm.pumpmodel', string='Items Details'),
		
	}
		
	_defaults = {
		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_wo_copy', context=c),			
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',		
		'active': True,
		'entry_mode': 'manual',
		
	}
	
	def onchange_wo(self,cr,uid,ids,wo_id,report_template, context=None):
		value = {'enq_id':0}
		print"wo_idwo_id",wo_id
		print"report_templatereport_template",report_template		
		if wo_id:
			wo_rec = self.pool.get('kg.work.order').browse(cr,uid,wo_id)
			print"wo_rec.line_ids[0]",wo_rec.line_ids[0]
			print"wo_rec.line_ids[0]enquiry_line_id",wo_rec.line_ids[0].enquiry_line_id
			if wo_rec.line_ids:
				wo_enquiry_line_id = wo_rec.line_ids[0].enquiry_line_id
				print"wo_enquiry_line_idwo_enquiry_line_id",wo_enquiry_line_id
				enq_line_ids = self.pool.get('ch.kg.crm.pumpmodel').search(cr,uid,[('id','=',wo_enquiry_line_id)])
				print"enq_line_idsenq_line_ids",enq_line_ids
				if enq_line_ids:
					enq_line_rec = self.pool.get('ch.kg.crm.pumpmodel').browse(cr,uid,enq_line_ids[0])
					enq_id = enq_line_rec.header_id.id
					print"enq_line_rec.idenq_line_rec.id-----------",enq_line_rec.id
					self.pool.get('ch.kg.crm.pumpmodel').write(cr,uid,enq_line_rec.id,{'report_template':report_template})
					print"enq_idenq_idenq_idenq_id",enq_id
					print"report_templatereport_template",report_template,type(report_template)
					value = {'enq_id': enq_id}
		print"valuevaluevalue",value
		return {'value': value}
	
	def print_wo(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])		
		if rec.state == 'draft':		
			rec = self.browse(cr,uid,ids[0])	
			data = self.read(cr,uid,ids,)[-1]
			myfile = '/OPENERP/Sam_Turbo/sam_turbo_dev/openerp-server/openerp/addons/kg_reports/planning/images/attachment_1.png'
			if os.path.isfile(myfile) == True:
				os.remove(myfile)
			myfile = '/OPENERP/Sam_Turbo/sam_turbo_dev/openerp-server/openerp/addons/kg_reports/planning/images/attachment_2.png'
			if os.path.isfile(myfile) == True:
				os.remove(myfile)
			if data['attachment']:
				myfile = '/OPENERP/Sam_Turbo/sam_turbo_dev/openerp-server/openerp/addons/kg_reports/planning/images/attachment_1.png'
				if os.path.isfile(myfile) == True:
					os.remove(myfile)
				else:
					pass
				filepath = os.path.join('/OPENERP/Sam_Turbo/sam_turbo_dev/openerp-server/openerp/addons/kg_reports/planning/images', 'attachment_1.png')
				f = open(filepath, "a")
				f.write(data['attachment'].decode('base64'))
			else:
				pass		
			print "CCCCCCCCCCCCCCCCCCCCCCCCC ================="
			
			if data['attachment_1']:
				myfile = '/OPENERP/Sam_Turbo/sam_turbo_dev/openerp-server/openerp/addons/kg_reports/planning/images/attachment_2.png'
				if os.path.isfile(myfile) == True:
					os.remove(myfile)
				else:
					pass
				filepath = os.path.join('/OPENERP/Sam_Turbo/sam_turbo_dev/openerp-server/openerp/addons/kg_reports/planning/images', 'attachment_2.png')
				f = open(filepath, "a")
				f.write(data['attachment_1'].decode('base64'))
			else:
				pass		
			print "CCCCCCCCCCCCCCCCCCCCCCCCC ================="
			
					
			print data,' create_report('
			return {
				'type'		 : 'ir.actions.report.xml',
				'report_name'   : 'jasper_workorder_report',
				'datas': {
						'model':'kg.wo.copy',
						'id': context.get('active_ids') and context.get('active_ids')[0] or False,
						'ids': context.get('active_ids') and context.get('active_ids') or [],
						'report_type': 'pdf',
						'form':data
					},
				'nodestroy': False
				}
		else:
			pass
		return True
	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
	def create(self, cr, uid, vals, context=None):
		return super(kg_wo_copy, self).create(cr, uid, vals, context=context)
	
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_wo_copy, self).write(cr, uid, ids, vals, context)
	
kg_wo_copy()

class ch_kg_crm_pumpmodel_inherit(osv.osv):
	
	_name = "ch.kg.crm.pumpmodel"
	_inherit = "ch.kg.crm.pumpmodel"
	_description = "Ch Enquiry"
	
	_columns = {
	
	'report_template': fields.selection([('1','Horizontal non slurry'),('2','Horizontal slurry'),('3','Vertical non slurry'),('4','Vertical slurry')],'Template'),
	
	## Liquid Paramenters
	
	'wo_line_id_flag' : fields.boolean('WO'),
	'equipment_no_flag' : fields.boolean('Equipment/Tag No.'),
	'description_flag': fields.boolean('Description'),
	'fluid_id_flag': fields.boolean('Liquid'),
	'temperature_in_c_flag': fields.boolean('Temperature in c'),
	'solid_concen_flag': fields.boolean('Solid Concern'),
	'solid_concen_vol_flag': fields.boolean('Solid Val Concern'),
	'viscosity_flag': fields.boolean('Viscosity in CST'),
	'specific_gravity_flag': fields.boolean('Specific Gravity'),
	'npsh_avl_flag': fields.boolean('NPSH-AVL'),
	'max_particle_size_mm_flag': fields.boolean('Max Particle Size-mm'),
	'capacity_in_liquid_flag': fields.boolean('Capacity in M3/hr(Liquid)'),
	'density_flag': fields.boolean('Density(kg/m3)'),
	'consistency_flag': fields.boolean('Consistency In %'),
	'head_in_liquid_flag': fields.boolean('Total Head in Mlc(Liquid)'),
	'suction_condition_flag': fields.boolean('Suction Condition'),
	'liquid_flag': fields.boolean('Liquid Remarks'),
	
	## Duty Paramenters
	
	'capacity_in_flag': fields.boolean('Capacity in M3/hr(Water)'),
	'head_in_flag': fields.boolean('Total Head in Mlc(Water)'),
	'suction_pressure_flag': fields.boolean('Suction pressure'),
	'differential_pressure_kg_flag': fields.boolean('Differential Pressure - kg/cm2'),
	'slurry_correction_in_flag': fields.boolean('Slurry Correction in'),
	'discharge_pressure_kg_flag': fields.boolean('Discharge Pressure - kg/cm2'),
	'suction_pressure_kg_flag': fields.boolean('Suction Pressure - kg/cm2'),
	'temperature_flag': fields.boolean('Temperature Condition'),
	'viscosity_crt_factor_flag': fields.boolean('Viscosity correction factors'),
	'duty_flag': fields.boolean('Duty Remarks'),
	
	## Pump Specifications
	
	'pump_id_flag': fields.boolean('Pump Model'),
	'alias_name_flag': fields.boolean('Alias Name'),
	'qty_flag': fields.boolean('Quantity'),
	'pumpseries_id_flag': fields.boolean('Pump Series'),
	'qap_plan_id_flag': fields.boolean('QAP Standard'),
	'ph_value_flag': fields.boolean('PH Value'),
	'motor_power_flag': fields.boolean('Motor Frame size(vertical)'),
	'del_pipe_size_flag': fields.boolean('Delivery Pipe Size(MM)'),
	'sump_depth_flag': fields.boolean('Sump Depth'),
	'pre_suppliy_ref_flag': fields.boolean('Previous Supply Reference'),
	'shaft_sealing_flag': fields.boolean('Shaft Sealing'),
	'scope_of_supply_flag': fields.boolean('Scope of Supply'),
	'number_of_stages_flag': fields.boolean('Number of stages'),
	'impeller_type_flag': fields.boolean('Impeller Type'),
	'impeller_dia_min_flag': fields.boolean('Impeller Dia Min mm'),
	'size_suctionx_flag': fields.boolean('Size-SuctionX Delivery(mm)'),
	'flange_type_flag': fields.boolean('Flange Type'),
	'flange_standard_flag': fields.boolean('Flange Standard'),
	'efficiency_in_flag': fields.boolean('Efficiency in % W/L'),
	'npsh_r_m_flag': fields.boolean('NPSH R - M'),
	'best_efficiency_flag': fields.boolean('Best Efficiency NPSH in M'),
	'bkw_water_flag': fields.boolean('BKW Water'),
	'bkw_liq_flag': fields.boolean('BKW Liq'),		
	'impeller_dia_rated_flag': fields.boolean('Impeller Dia Rated mm'),
	'impeller_tip_speed_flag': fields.boolean('Impeller Tip Speed -M/Sec'),		
	'hydrostatic_test_pressure_flag': fields.boolean('Hydrostatic Test Pressure - Kg/cm2'),		
	'setting_height_flag': fields.boolean('Setting Height'),
	'full_load_rpm_flag': fields.boolean('Speed in RPM - Engine'),
	'insulation_flag': fields.boolean('Insulation'),
	'protection_flag': fields.boolean('Protection'),
	'voltage_flag': fields.boolean('Voltage'),
	'phase_flag': fields.boolean('Phase'),
	'engine_make_flag': fields.boolean('Engine Make'),
	'engine_type_flag': fields.boolean('Engine Type'),
	'belt_loss_in_kw_flag': fields.boolean('Belt Loss in Kw - 3% of BKW'),
	'frequency_flag': fields.boolean('Motor frequency (HZ)'),
	'motor_kw_flag': fields.boolean('Motor KW'),
	'motor_margin_flag': fields.boolean('Motor Margin(%)'),
	'speed_in_motor_flag': fields.boolean('Speed in RPM-Motor'),
	'engine_rpm_flag': fields.boolean('Engine(RPM)'),
	'end_of_the_curve_flag': fields.boolean('End of the curve - KW(Rated) liquid'),
	'critical_speed_flag': fields.boolean('Critical Speed'),
	'engine_kw_flag': fields.boolean('Engine KW'),
	'gear_box_loss_rated_flag': fields.boolean('Gear Box Loss-Rated'),
	
	'fluid_coupling_loss_rated_flag': fields.boolean('Fluid Coupling Loss-Rated'),
	'mototr_output_power_rated_flag': fields.boolean('Motor Output Power-Rated'),
	'higher_speed_rpm_flag': fields.boolean('Higher Speed(Rpm)'),
	'head_higher_speed_flag': fields.boolean('Head At Higher Speed'),
	'effy_high_speed_flag': fields.boolean('Efficiency At High Speed'),
	'pump_input_higher_speed_flag': fields.boolean('Pump Input At Higher Speed'),
	'mech_seal_make_flag':fields.boolean('Mech. Seal Make'),
	'seal_type_flag': fields.boolean('Seal Type'),
	'face_combination_flag': fields.boolean('Face Combination'),
	
	
	'maximum_allowable_soild_flag': fields.boolean('Maximum Allowable Soild Size - MM'),
	'impeller_number_flag': fields.boolean('Impeller Number of vanes'),
	'impeller_dia_max_flag': fields.boolean('Impeller Dia Max mm'),
	'max_allowable_test_flag': fields.boolean('Max Allowable Casing design Pressure'),
	'crm_type_flag': fields.boolean('Pump Design'),
	'bush_bearing_lubrication_flag':fields.boolean('Bush Bearing Lubrication'),
	'push_bearing_flag': fields.boolean('Bush Bearing'),
	'suction_size_flag': fields.boolean('Suction Size'),
	'rpm_flag': fields.boolean('RPM'),
	'speed_in_rpm_flag': fields.boolean('Speed in RPM - Pump'),
	'casing_design_flag': fields.boolean('Casing Feet Location'),
	'shut_off_head_flag': fields.boolean('Shut off Head in M'),
	'shut_off_pressure_flag': fields.boolean('Shut off Pressure'),
	'minimum_contionuous_flag': fields.boolean('Minimum Contionuous Flow - M3/hr'),
	'specific_speed_flag': fields.boolean('Specific Speed'),
	'suction_specific_speed_flag': fields.boolean('Suction Specific Speed'),
	'sealing_water_pressure_flag': fields.boolean('Sealing Water Pressure Kg/cm^2'),
	'sealing_water_capacity_flag': fields.boolean('Sealing Water Capcity- m3/hr'),
	'gd_sq_value_flag': fields.boolean('GD SQ value'),
	'bearing_make_flag': fields.boolean('Bearing Make'),
	'bearing_number_nde_flag': fields.boolean('BEARING NUMBER NDE / DE'),
	'bearing_qty_nde_flag': fields.boolean('Bearing qty NDE / DE'),
	'lubrication_type_flag': fields.boolean('Lubrication'),
	'primemover_categ_flag': fields.boolean('Primemover Category'),
	'type_of_drive_flag': fields.boolean('Transmission'),
	'primemover_id_flag': fields.boolean('Prime Mover'),
	'framesize_flag': fields.boolean('Motor Frame Size'),
	'operation_range_flag': fields.boolean('Operation Range'),
	'motor_make_flag': fields.boolean('Motor Make'),
	'motor_type_flag': fields.boolean('Motor Type'),
	'motor_mounting_flag': fields.boolean('Motor Mounting'),
	'gear_box_loss_high_speed_flag': fields.boolean('Gear Box Loss-High Speed'),
	'fluid_coupling_loss_flag': fields.boolean('Fluid Coupling Loss-High Speed'),
	'motor_output_power_high_speed_flag': fields.boolean('Motor Output Power-High Speed'),
	'lower_speed_rpm_flag': fields.boolean('Lower Speed(Rpm)'),
	'head_lower_speed_flag': fields.boolean('Head At Lower Speed'),
	'effy_lower_speed_point_flag': fields.boolean('Efficiency At Lower Speed Point'),
	'pump_input_lower_speed_flag': fields.boolean('Pump Input At Lower Speed'),
	'gear_box_loss_lower_speed_flag': fields.boolean('Gear Box Loss-Lower Speed'),
	'fluid_coupling_loss_lower_speed_flag': fields.boolean('Fluid Coupling Loss-Lower Speed'),
	'motor_output_power_lower_speed_flag': fields.boolean('Motor Output Power-Lower Speed'),
	'gland_plate_flag': fields.boolean('Gland Plate'),
	'api_plan_flag': fields.boolean('API Plan'),
	
	}
	
ch_kg_crm_pumpmodel_inherit()
