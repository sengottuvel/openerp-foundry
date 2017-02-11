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

class kg_pump_qap(osv.osv):

	_name = "kg.pump.qap"
	_description = "Pump QAP"
	_order = "entry_date desc"
	
	
	_columns = {
	
		## Version 0.1
	
		## Basic Info
				
		'entry_date': fields.date('Date',required=True),		
		'note': fields.text('Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_sms': fields.boolean('SMS Notification'),
		'flag_email': fields.boolean('Email Notification'),
		'flag_spl_approve': fields.boolean('Special Approval'),
		
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
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model',readonly=True),
		'pump_serial_no': fields.char('Pump Serial No.',required=True,readonly=True),
		'moc_construction_id': fields.many2one('kg.moc.construction','MOC Construction', readonly=True,required=True),
		'test_state': fields.selection([('di','Dimensional Inspection'),('hs','Hydro Static Test'),('pt','Performance Testing')],'Test State'),
		'assembly_id': fields.many2one('kg.assembly.inward','Assembly'),
		
		## Dimensional Inspection ##
		
		'di_date': fields.date('Date',required=True),
		'di_shift_id': fields.many2one('kg.shift.master','Shift'),
		'di_operator': fields.char('Operator'),
		'di_verified_by': fields.char('Verified By'),
		'di_result': fields.selection([('accept','Accept'),('reject','Reject')],'Result'),
		'di_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'di_remarks': fields.text('Remarks'),
		'line_ids': fields.one2many('ch.pump.dimentional.details', 'header_id', "Dimention Details Line"),
		'flag_di_customer_specific': fields.text('Customer Specific'),
		'di_state': fields.selection([('pending','Pending'),('completed','Completed')],'DI State'),

		
		## Hydro Static Test (After Assembly) ##
		
		'hs_date': fields.date('Date',required=True),	
		'hs_pressure': fields.float('Hydro static test pressure' ),
		'hs_testing_time': fields.selection([('15','15'),('30','30'),('45','45'),('60','60'),('75','75'),('90','90'),('105','105'),('120','120')],
					'Testing time (Mins)'),
		'hs_actual_unbal_weight': fields.float('Actual Un Balanced Weight in (gms)'),
		'hs_machinery_id': fields.many2one('kg.machinery.master','Machinery'),
		'hs_shift_id': fields.many2one('kg.shift.master','Shift'),
		'hs_operator': fields.char('Operator'),
		'hs_verified_by': fields.char('Verified By'),
		'hs_result': fields.selection([('accept','Accept'),('reject','Reject')],'Result'),
		'hs_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'hs_leak_remarks': fields.char('Leak Remarks'),
		'hs_action': fields.char('Action to be taken'),
		'hs_remarks': fields.text('Remarks'),
		'flag_hs_customer_specific': fields.boolean('Customer Specific'),
		'hs_state': fields.selection([('pending','Pending'),('completed','Completed')],'HS State'),

		
		## Performance Testing ##
		
		'pt_date': fields.date('Date',required=True),
		'pt_shift_id': fields.many2one('kg.shift.master','Shift'),
		'pt_operator': fields.char('Operator'),
		'pt_verified_by': fields.char('Verified By'),
		'pt_result': fields.selection([('accept','Accept'),('reject','Reject')],'Result'),
		'pt_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'flag_pt_customer_specific': fields.boolean('Customer Specific'),
		'perforamnce_attach': fields.binary('Performance'),
		'run_attach': fields.binary('Run'),
		'mechanical_attach': fields.binary('Mechanical'),
		'pt_state': fields.selection([('pending','Pending'),('completed','Completed')],'PT State'),
		'pt_remarks': fields.text('Remarks'),

	
				
	}
		
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_pump_qap', context=c),			
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'di_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'hs_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'pt_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',		
		'active': True,
		'entry_mode': 'manual',		
		'flag_sms': False,		
		'flag_email': False,		
		'flag_spl_approve': False,		
		
	}
	
	
	_constraints = [		
			  
		
		#~ (_future_entry_date_check, 'System not allow to save with future date. !!',['']),
	   #~ 
		
	]
	   
	def di_update(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])		
		### Validations Checking  ###
		### Actual weight checking ###
		cr.execute(''' 			
			select actual_weight from ch_pump_dimentional_details where header_id = %s
			and actual_weight BETWEEN min_weight AND max_weight and actual_weight <= max_weight ''',[rec.id])
		actual_weight = cr.fetchone()
		print "actual_weight",actual_weight
		if actual_weight == None:
			raise osv.except_osv(_('Warning !!'),
				_('Actual weight should be with in Min and Max weight. !!'))
		if rec.di_state == 'pending':
			### Hrdro static pressure from marketing Enquiry ###
			if rec.order_line_id.pump_offer_line_id > 0:
				market_enquiry_rec = self.pool.get('ch.kg.crm.pumpmodel').browse(cr,uid,rec.order_line_rec.pump_offer_line_id)
				if market_enquiry_rec:
					hs_pressure = market_enquiry_rec.hydrostatic_test_pressure
				else:
					hs_pressure = 0.00
			else:
				hs_pressure = 0.00
			self.write(cr, uid, ids, {'test_state':'hs','hs_pressure':hs_pressure,'hs_state':'pending','di_state':'completed','update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass	
		return True
		
	def hs_update(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		### Actual weight checking ###
		if rec.hs_actual_unbal_weight <= 0:
			raise osv.except_osv(_('Warning !!'),
				_('Actual weight should be greater than zero. !!'))	
		if rec.hs_pressure <= 0:
			raise osv.except_osv(_('Warning !!'),
				_('Test Pressure should be greater than zero. !!'))	
		### Sequence Number Generation  ###
		if rec.hs_state == 'pending':
			self.write(cr, uid, ids, {'test_state':'pt','pt_state':'pending','hs_state':'completed','update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass	
		return True
		
	def pt_update(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])		
		### Sequence Number Generation  ###
		if rec.pt_state == 'pending':
			### Painting Creation
			
			if rec.pt_result == 'accept':
				qap_painting_id = self.pool.get('ch.painting').search(cr,uid,[('header_id','=',rec.qap_plan_id.id)])
				if qap_painting_id:
					qap_painting_rec = self.pool.get('ch.painting').browse(cr,uid,qap_painting_id[0])
					print "qap_painting_rec",qap_painting_rec
					
				
				painting_vals = {
				
					'qap_plan_id': rec.qap_plan_id.id,
					'order_id': rec.order_id.id,
					'order_line_id':  rec.order_line_id.id,
					'order_no': rec.order_line_id.order_no,
					'order_category': rec.order_category,
					'pump_model_id': rec.pump_model_id.id,
					'pump_serial_no': rec.pump_serial_no,
					'moc_construction_id': rec.moc_construction_id.id,
					'assembly_id': ids[0],
					'paint_color': qap_painting_rec.paint_color,
					'surface_preparation': qap_painting_rec.surface_preparation,
					'primer': qap_painting_rec.primer,
					'primer_ratio': qap_painting_rec.primer_ratio,
					'inter_mediater': qap_painting_rec.inter_mediater,
					'intermediater_ratio': qap_painting_rec.intermediater_ratio,
					'final_paint': qap_painting_rec.final_paint,
					'final_paint_ratio': qap_painting_rec.final_paint_ratio,
					'flim_thickness': qap_painting_rec.flim_thickness,
					'painting_state': 'pending',
					'assembly_id': rec.assembly_id.id,
				}
				painting_id = self.pool.get('kg.painting').create(cr, uid, painting_vals)
			self.write(cr, uid, ids, {'pt_state':'completed','update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
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
		return super(kg_pump_qap, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_pump_qap, self).write(cr, uid, ids, vals, context)
		
	_sql_constraints = [
	
		('name', 'unique(name)', 'No must be Unique !!'),
	]	
	
kg_pump_qap()



class ch_pump_dimentional_details(osv.osv):
	
	_name = 'ch.pump.dimentional.details'
	_description = "Dimentional Details"
	
	
	_columns = {
		
		'header_id':fields.many2one('kg.pump.qap', 'Dimension Inspection Details', required=True, ondelete='cascade'), 		
		'dimentional_details': fields.selection([('suction_face','Suction Face to Delivery Centre'),
												('delivery_centre','Delivery Centre to Shaft End'),
												('delivery_face','Delivery Face to Suction Centre'),
												('leg_face','Leg face to Suction Centre'),
												('coupling_seating','Coupling Seating OD'),
												('suction_flange','Suction Flange Details'),
												('delivery_flange','Delivery Flange Details')],'Dimention Details', required=True),
		'min_weight': fields.float('Min' ,required=True),
		'max_weight': fields.float('Max' ,required=True),	
		'actual_weight': fields.float('Actual' ),	
		'remarks':fields.text('Remarks'),

		
	}	
	
	def _check_line_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(""" select dimentional_details from ch_pump_dimentional_details where dimentional_details  = '%s' and header_id = '%s' """ %(entry.dimentional_details,entry.header_id.id))
		data = cr.dictfetchall()			
		if len(data) > 1:		
			return False
		return True	
		
	def _check_line_weight(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])		
		if entry.min_weight <= 0 or entry.max_weight <= 0 or entry.min_weight > entry.max_weight:			
			return False
		return True
		
	_constraints = [
		
		   
		(_check_line_duplicates, 'Dimentional Details same Dimention Details selection not accept', ['Dimention Details']),	   
		(_check_line_weight, 'Dimentional Details min and max Zero,negative and Min value greater than Max value not accept', ['Min & Max']),	   
	]

	
ch_pump_dimentional_details()

class kg_painting(osv.osv):

	_name = "kg.painting"
	_description = "Painting"
	_order = "entry_date desc"
	
	
	_columns = {
	
		## Version 0.1
	
		## Basic Info
				
		'entry_date': fields.date('Date',required=True),		
		'note': fields.text('Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_sms': fields.boolean('SMS Notification'),
		'flag_email': fields.boolean('Email Notification'),
		'flag_spl_approve': fields.boolean('Special Approval'),
		
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
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model',readonly=True),
		'pump_serial_no': fields.char('Pump Serial No.',required=True,readonly=True),
		'moc_construction_id': fields.many2one('kg.moc.construction','MOC Construction', readonly=True,required=True),
		'assembly_id': fields.many2one('kg.assembly.inward','Assembly'),
		
		## Painting ##
		
		'shift_id': fields.many2one('kg.shift.master','Shift'),
		'operator': fields.char('Operator'),
		'verified_by': fields.char('Verified By'),
		'paint_color': fields.char('Paint Color'),
		'surface_preparation': fields.char('Surface Preparation'),
		'primer': fields.char('Primer'),
		'primer_ratio': fields.float('Primer Ratio'),
		'inter_mediater': fields.char('Intermediater'),
		'intermediater_ratio': fields.float('Intermediater Ratio'),
		'final_paint': fields.char('Final Paint'),
		'final_paint_ratio': fields.float('Final Paint Ratio'),
		'flim_thickness': fields.float('Flim Thickness(DFT)'),
		'remarks':fields.text('Remarks'),
		'flag_customer_specific': fields.boolean('Customer Specific'),
		'painting_state': fields.selection([('pending','Pending'),('completed','Completed')],'Painting State'),
		
	
				
	}
		
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_painting', context=c),			
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',		
		'active': True,
		'entry_mode': 'manual',		
		'flag_sms': False,		
		'flag_email': False,		
		'flag_spl_approve': False,		
		
	}
	
	def painting_update(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])		
		### Sequence Number Generation  ###
		if rec.painting_state == 'pending':
			qap_packing_id = self.pool.get('ch.packing').search(cr,uid,[('header_id','=',rec.qap_plan_id.id)])
			if qap_packing_id:
				qap_packing_rec = self.pool.get('ch.packing').browse(cr,uid,qap_packing_id[0])
				print "qap_packing_rec",qap_packing_rec
				
			
			painting_vals = {
			
				'qap_plan_id': rec.qap_plan_id.id,
				'order_id': rec.order_id.id,
				'order_line_id':  rec.order_line_id.id,
				'order_no': rec.order_line_id.order_no,
				'order_category': rec.order_category,
				'pump_model_id': rec.pump_model_id.id,
				'pump_serial_no': rec.pump_serial_no,
				'moc_construction_id': rec.moc_construction_id.id,
				'assembly_id': ids[0],
				'packing_id': qap_packing_rec.packing_id.id,	
				'wood_type': qap_packing_rec.wood_type,
				'box_size': qap_packing_rec.box_size,
				'packing_state': 'pending',
				'assembly_id': rec.assembly_id.id,
			}
			packing_id = self.pool.get('kg.packing').create(cr, uid, painting_vals)
			self.write(cr, uid, ids, {'painting_state':'completed','update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
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
		
	def create(self, cr, uid, vals, context=None):
		return super(kg_painting, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_painting, self).write(cr, uid, ids, vals, context)
		
	_sql_constraints = [
	
		('name', 'unique(name)', 'No must be Unique !!'),
	]	
	
kg_painting()

class kg_packing(osv.osv):

	_name = "kg.packing"
	_description = "Packing"
	_order = "entry_date desc"
	
	
	_columns = {
	
		## Version 0.1
	
		## Basic Info
				
		'entry_date': fields.date('Date',required=True),		
		'note': fields.text('Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_sms': fields.boolean('SMS Notification'),
		'flag_email': fields.boolean('Email Notification'),
		'flag_spl_approve': fields.boolean('Special Approval'),
		
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
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model',readonly=True),
		'pump_serial_no': fields.char('Pump Serial No.',required=True,readonly=True),
		'moc_construction_id': fields.many2one('kg.moc.construction','MOC Construction', readonly=True,required=True),
		'assembly_id': fields.many2one('kg.assembly.inward','Assembly'),
		
		## PACKING ##
		
		'shift_id': fields.many2one('kg.shift.master','Shift'),
		'operator': fields.char('Operator'),
		'verified_by': fields.char('Verified By'),
		'packing_id': fields.many2one('kg.packing.type','Packing Type',domain="[('active','=','t')]"),	
		'wood_type': fields.char('Wood Type'),
		'box_size': fields.char('Box Size (L*B*H)'),
		'gross_weight': fields.float('Gross Weight'),
		'net_weight': fields.float('Net Weight'),
		'pump_weight': fields.float('Pump Weight'),
		'remarks':fields.text('Remarks'),
		'flag_customer_specific': fields.boolean('Customer Specific'),
		'manual_book_attach': fields.binary('Manual Book'),
		'photos_attach': fields.binary('Photos'),
		'packing_state': fields.selection([('pending','Pending'),('completed','Completed')],'Packing State'),
	}
		
	

		
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_packing', context=c),			
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',		
		'active': True,
		'entry_mode': 'manual',		
		'flag_sms': False,		
		'flag_email': False,		
		'flag_spl_approve': False,		
		
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
	
	def onchange_pump_weight(self, cr, uid, ids, gross_weight, net_weight):
		pump_wgt = net_weight - gross_weight
		return {'value': {'pump_weight':pump_wgt}}
	
	def packing_update(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])		
		### Sequence Number Generation  ###
		if rec.packing_state == 'pending':
			self.write(cr, uid, ids, {'packing_state':'completed','update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
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
		return super(kg_packing, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_packing, self).write(cr, uid, ids, vals, context)
		
	_sql_constraints = [
	
		('name', 'unique(name)', 'No must be Unique !!'),
	]	
	
kg_packing()
