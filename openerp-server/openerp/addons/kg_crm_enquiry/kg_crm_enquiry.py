from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import base64

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

CALL_TYPE_SELECTION = [
    ('service','Service'),
    ('product','Product')
]
PURPOSE_SELECTION = [
    ('pump','Pump'),('spare','Spare'),('prj','Project'),('pump_spare','Pump With Spare')
]
STATE_SELECTION = [
    ('draft','Draft'),('moved_to_offer','Moved To Offer'),('call','Call Back'),('quote','Quote Process'),('wo_released','WO Released'),('reject','Rejected')
]
MARKET_SELECTION = [
	('cp','CP'),('ip','IP')
]

class kg_crm_enquiry(osv.osv):

	_name = "kg.crm.enquiry"
	_description = "CRM Enquiry Entry"
	_order = "enquiry_date desc"

	_columns = {
	
		### Header Details ####
		'name': fields.char('Offer No', size=128,select=True),
		'schedule_no': fields.char('Schedule No', size=128,select=True),
		'enquiry_date': fields.date('Enquiry Date',required=True),
		'offer_date': fields.date('Offer Date'),
		'note': fields.char('Notes'),
		'service_det': fields.char('Service Details'),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection(STATE_SELECTION,'Status', readonly=True),
		'line_ids': fields.one2many('ch.kg.crm.enquiry', 'header_id', "Child Enquiry"),
		'ch_line_ids': fields.one2many('ch.kg.crm.pumpmodel', 'header_id', "Child Pump Enquiry"),
		'due_date': fields.date('Due Date',required=True),
		'call_type': fields.selection(CALL_TYPE_SELECTION,'Call Type', required=True),
		'ref_mode': fields.selection([('direct','Direct'),('dealer','Dealer')],'Reference Mode', required=True),
		'market_division': fields.selection(MARKET_SELECTION,'Marketing Division', required=True),
		'ref_no': fields.char('Reference Number'),
		'segment': fields.selection([('dom','Domestic'),('exp','Export')],'Segment', required=True),
		'customer_id': fields.many2one('res.partner','Customer Name',domain=[('customer','=',True),('contact','=',False)]),
		'dealer_id': fields.many2one('res.partner','Dealer Name',domain=[('dealer','=',True),('contact','=',False)]),
		'industry_id': fields.many2one('kg.industry.master','Sector'),
		'expected_value': fields.float('Expected Value'),
		'del_date': fields.date('Expected Del Date', required=True),
		'purpose': fields.selection(PURPOSE_SELECTION,'Purpose'),
		'capacity': fields.float('Capacity'),
		'head': fields.float('Head'),
		'chemical_id': fields.many2one('kg.chemical.master','Chemical',domain=[('purpose','=','general')]),
		'pump_list': fields.text('Pump List'),
		'gravity': fields.float('Gravity'),
		'spl_gravity': fields.float('Special Gravity'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Name'),
		's_no': fields.char('Serial Number'),
		'wo_no': fields.char('WO Number'),
		'requirements': fields.text('Requirements'),
		
		
		########## Karthikeyan Added Start here ################
		'enquiry_no': fields.char('Enquiry No.', size=128,select=True,required=True),
		'scope_of_supply': fields.selection([('bare_pump','Bare Pump'),('pump_with_acces','Pump With Accessories'),('pump_with_acces_motor','Pump With Accessories And Motor')],'Scope of Supply'),
		'pump': fields.selection([('gld_packing','Gland Packing'),('mc_seal','M/C Seal'),('dynamic_seal','Dynamic seal')],'Shaft Sealing', required=True),
		'drive': fields.selection([('motor','Motor'),('vfd','VFD'),('engine','Engine')],'Drive'),
		'transmision': fields.selection([('cpl','Coupling'),('belt','Belt Drive'),('fc','Fluid Coupling'),('gear_box','Gear Box'),('fc_gear_box','Fluid Coupling With Gear Box')],'Transmision', required=True),
		'acces': fields.selection([('yes','Yes'),('no','No')],'Accessories'),
		
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_crm_enquiry', context=c),
		'enquiry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',
		'pump': 'gld_packing',
		'transmision': 'cpl',
		'ref_mode': 'direct',
		'call_type': 'service',
		'active': True,
	#	'division_id':_get_default_division,
		'due_date' : lambda * a: time.strftime('%Y-%m-%d'),
		
	}
	
	def onchange_due_date(self,cr,uid,ids,due_date,context=None):
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		due_date = str(due_date)
		due_date = datetime.strptime(due_date, '%Y-%m-%d')
		if due_date >= today:
			return False
		else:
			raise osv.except_osv(_('Warning!'),
						_('System not allow to save with past date !!'))
		
	def _future_enquiry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		enquiry_date = rec.enquiry_date
		enquiry_date = str(enquiry_date)
		enquiry_date = datetime.strptime(enquiry_date, '%Y-%m-%d')
		if enquiry_date <= today:
			return True
		return False
		
	def _future_due_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		due_date = rec.due_date
		due_date = str(due_date)
		due_date = datetime.strptime(due_date, '%Y-%m-%d')
		if due_date <= today:
			return False
		return True
		
	def _check_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(''' select id from kg_weekly_schedule where entry_date = %s
			and division_id = %s and location = %s and id != %s and active = 't' and state = 'confirmed' ''',[str(entry.entry_date),entry.division_id.id,entry.location, ids[0]])
		duplicate_id = cr.fetchone()
		if duplicate_id:
			return False
		return True 
		
	def _check_lineitems(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if not entry.line_ids:
			return False
		return True
		
	def _Validation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		special_char = ''.join( c for c in flds.name if  c in '!@#$%^~*{}?+=' )
		if special_char:
			return False
		return True
		
	def _check_name(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(""" select name from kg_crm_enquiry where name  = '%s' """ %(entry.name))
		data = cr.dictfetchall()
			
		if len(data) > 1:
			res = False
		else:
			res = True	
		return res 
			
	
	_constraints = [		
		
		(_future_enquiry_date_check, 'System not allow to save with past date. !!',['Enquiry Date']),
		(_future_due_date_check, 'System not allow to save with past date. !!',['Due Date']),
		#(_check_duplicates, 'System not allow to do duplicate entry !!',['']),
		#(_check_lineitems, 'System not allow to save with empty Work Order Details !!',['']),
		#(_Validation, 'Special Character Not Allowed in Work Order No.', ['']),
		#(_check_name, 'Work Order No. must be Unique', ['']),
		
	   ]
	   
	"""   
	def onchange_delivery_date(self, cr, uid, ids, delivery_date):
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		if delivery_date:
			delivery_date = str(delivery_date)
			delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d')
			if delivery_date < today:
				raise osv.except_osv(_('Warning!'),
						_('Delivery Date should not be less than current date!!'))
		return True
	  """

	def list_details(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		obj = self.search(cr,uid,[('id','!=',rec.id),('customer_id','=',rec.customer_id.id)])
		if obj:
			cr.execute(''' delete from ch_kg_crm_enquiry where header_id = %s '''%(rec.id))
			
			for item in obj:
				obj_rec = self.browse(cr,uid,item)
				child_id = self.pool.get('ch.kg.crm.enquiry').create(cr,uid,{'header_id':rec.id,'enquiry_id':item})
		else:
			pass
		return True
		
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_number = str(rec.enquiry_no)
		#~ url = 'http://iasqa1.kgisl.com/?uname='+rec_user+'&s='+rec_work_order
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
		
		url = 'http://10.100.9.60/DMS/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&wo_no='+rec_number
		
		#url = 'http://192.168.1.150:81/pbxclick2call.php?exten='+exe_no+'&phone='+str(m_no)
		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
		
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.call_type == 'service':		
			off_no = ''	
			qc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.crm.enquiry')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,qc_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(qc_seq_id[0],rec.code,entry.enquiry_date))
			off_no = cr.fetchone();
		elif entry.call_type == 'product':
			if entry.market_division == 'cp':				
				off_no = ''	
				qc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','crm.enquiry.cp')])
				rec = self.pool.get('ir.sequence').browse(cr,uid,qc_seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(qc_seq_id[0],rec.code,entry.enquiry_date))
				off_no = cr.fetchone();
			elif entry.market_division == 'ip':				
				off_no = ''	
				qc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','crm.enquiry.ip')])
				rec = self.pool.get('ir.sequence').browse(cr,uid,qc_seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(qc_seq_id[0],rec.code,entry.enquiry_date))
				off_no = cr.fetchone();
			else:
				pass
		else:
			pass
	
		self.write(cr, uid, ids, {
									#'name':self.pool.get('ir.sequence').get(cr, uid, 'kg.crm.enquiry'),
									'name':off_no[0],
									'state': 'moved_to_offer',
									'confirm_user_id': uid, 
									'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')
								})
		return True
			
	def entry_call_back(self,cr,uid,ids,context=None):
		
		self.write(cr, uid, ids, {'state': 'call','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
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
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_crm_enquiry, self).write(cr, uid, ids, vals, context)
		
kg_crm_enquiry()


class ch_kg_crm_enquiry(osv.osv):

	_name = "ch.kg.crm.enquiry"
	_description = "Child CRM Enquiry Details"
	_order = "enquiry_id"
	
	_columns = {
	
		### Enquiry History Details ####
		'header_id':fields.many2one('kg.crm.enquiry', 'Enquiry', ondelete='cascade'),
		'enquiry_id':fields.many2one('kg.crm.enquiry', 'Enquiry'),
		#'purpose': fields.related('enquiry_id','purpose', type='char', string='Purpose', store=True),
		'purpose': fields.related('enquiry_id','purpose', type='selection',selection=PURPOSE_SELECTION, string='Purpose'),
		'due_date': fields.related('enquiry_id','due_date', type='date', string='Due Date'),
		#'state': fields.related('enquiry_id','state', type='char', string='Status'),
		'state': fields.related('enquiry_id','state', type='selection', selection=STATE_SELECTION, string='Status'),
		#'call_type': fields.related('enquiry_id','call_type', type='char', string='Call Type', store=True),
		'call_type': fields.related('enquiry_id', 'call_type', type='selection', selection=CALL_TYPE_SELECTION, string='Call Type'),
		
		
	}
	
	"""
	def default_get(self, cr, uid, fields, context=None):
		return context
	
	def create(self, cr, uid, vals, context=None):
		header_rec = self.pool.get('kg.crm.enquiry').browse(cr, uid,vals['header_id'])
		if header_rec.state == 'draft':
			res = super(ch_kg_crm_enquiry, self).create(cr, uid, vals, context=context)
		else:
			res = False
		return res
	"""	
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_kg_crm_enquiry, self).write(cr, uid, ids, vals, context)
		
	
ch_kg_crm_enquiry()


class ch_kg_crm_pumpmodel(osv.osv):

	_name = "ch.kg.crm.pumpmodel"
	_description = "Child Pump Model Details"
	
	_columns = {
	
		### Pump Details ####
		'header_id':fields.many2one('kg.crm.enquiry', 'Enquiry', ondelete='cascade'),
		'enquiry_id':fields.many2one('kg.crm.enquiry', 'Enquiry'),
		'pump_id':fields.many2one('kg.pumpmodel.master', 'Pump'),
		'qty':fields.integer('Quantity'),
		'del_date':fields.date('Delivery Date'),
		'oth_spec':fields.char('Other Specification'),
		'purpose_categ': fields.selection([('pump','Pump'),('spare','Spare'),('prj','Project'),('pump_spare','Pump With Spare')],'Purpose Category'),
		'line_ids': fields.one2many('ch.kg.crm.foundry.item', 'header_id', "Foundry Details"),
		'line_ids_a': fields.one2many('ch.kg.crm.machineshop.item', 'header_id', "Machineshop Details"),
		'line_ids_b': fields.one2many('ch.kg.crm.bot', 'header_id', "BOT Details"),
		'line_ids_moc_a': fields.one2many('ch.moc.construction', 'header_id', "MOC Construction"),
		
		########## Karthikeyan Item Details Added Start here ################
		'equipment_no': fields.char('Equipment No'),
		'quantity_in_no': fields.integer('Quantity in No'),
		'description': fields.char('Description'),
		
		########## Karthikeyan Liquid Specifications Added Start here ################
		'solid_concen': fields.float('Solid Concentration in %'),
		'max_particle_size_mm': fields.float('Max Particle Size-mm'),
		'fluid_id': fields.many2one('kg.fluid.master','Liquid',domain="[('state','not in',('reject','cancel'))]"),
		'temperature_in_c': fields.char('Temperature in C'),
		'density': fields.integer('Density(kg/m3)'),
		'specific_gravity': fields.float('Specific Gravity'),
		'viscosity': fields.integer('Viscosity in CST'),
		'npsh_avl': fields.integer('NPSH-AVL'),
		'capacity_in_liquid': fields.integer('Capacity in M3/hr(Liquid)'),
		'head_in_liquid': fields.float('Total Head in Mlc(Liquid)'),
		'consistency': fields.float('Consistency In %'),
		
		########## Karthikeyan Duty Parameters Added Start here ################	
		
		'capacity_in': fields.integer('Capacity in M3/hr(Water)',),
		'head_in': fields.float('Total Head in Mlc(Water)'),
		'viscosity_crt_factor': fields.float('Viscosity correction factors'),
		'suction_pressure': fields.selection([('normal','Normal'),('centre_line','Centre Line')],'Suction pressure'),
		'differential_pressure_kg': fields.float('Differential Pressure - kg/cm2'),
		'slurry_correction_in': fields.float('Slurry Correction in'),
		'temperature': fields.selection([('normal','NORMAL'),('jacketting','JACKETTING'),('centre_line','CENTRE LINE')],'Temperature Condition'),
		'suction_condition': fields.selection([('positive','Positive'),('negative','Negative')],'Suction Condition'),
		'discharge_pressure_kg': fields.float('Discharge Pressure - kg/cm2'),
		'suction_pressure_kg': fields.float('Suction Pressure - kg/cm2'),
		
		########## Karthikeyan Pump Specification Added Start here ################	
		'pump_type': fields.char('Pump Model'),		
		'casing_design': fields.selection([('base','Base'),('center_line','Center Line')],'Casing Feet Location'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type', required=True,domain="[('active','=','t')]"),		
		'size_suctionx': fields.char('Size-SuctionX Delivery(mm)'),
		'flange_standard': fields.many2one('ch.pumpseries.flange','Flange Standard',domain="[('flange_type','=',flange_type),('header_id','=',pumpseries_id)]"),
		'efficiency_in': fields.float('Efficiency in % Wat'),
		'npsh_r_m': fields.float('NPSH R - M'),
		'best_efficiency': fields.float('Best Efficiency NPSH in M'),
		'bkw_water': fields.float('BKW Water'),
		'bkw_liq': fields.float('BKW Liq'),		
		'impeller_dia_rated': fields.float('Impeller Dia Rated mm'),
		'impeller_tip_speed': fields.float('Impeller Tip Speed -M/Sec'),		
		'hydrostatic_test_pressure': fields.float('Hydrostatic Test Pressure - Kg/cm2'),		
		'shut_off_head': fields.float('Shut off Head in M'),
		'minimum_contionuous': fields.float('Minimum Contionuous Flow - M3/hr'),
		'specific_speed': fields.float('Specific Speed'),
		'suction_specific_speed': fields.float('Suction Specific Speed'),
		'sealing_water_pressure': fields.float('Sealing Water Pressure Kg/cm^2'),
		'sealing_water_capacity': fields.float('Sealing Water Capcity- m3/hr'),
		'gd_sq_value': fields.float('GD SQ value'),
		'critical_speed': fields.float('Critical Speed'),
		'bearing_make': fields.many2one('kg.brand.master','Bearing Make'),
		'bearing_number_nde': fields.char('BEARING NUMBER NDE / DE'),
		'bearing_qty_nde': fields.float('Bearing qty NDE / DE'),
		'type_of_drive': fields.selection([('motor_direct','Motor-direct'),('belt_drive','Belt drive'),('fc_gb','FC GB')],'Transmission'),
		'end_of_the_curve': fields.float('End of the curve - KW(Rated) liquid'),
		'motor_frequency_hz': fields.float('Motor frequency HZ'),
		'frequency': fields.selection([('50','50'),('60','60')],'Motor frequency (HZ)'),
		'motor_margin': fields.float('Motor Margin(%)'),
		'motor_kw': fields.float('Motor KW'),
		'speed_in_pump': fields.float('Speed in RPM-Pump'),
		'speed_in_motor': fields.float('Speed in RPM-Motor'),
		'full_load_rpm': fields.float('Speed in RPM'),
		'engine_kw': fields.float('Engine KW'),
		'belt_loss_in_kw': fields.float('Belt Loss in Kw - 3% of BKW'),
		'type_make_selection': fields.selection([('base','Base'),('center_line','Center Line')],'Type Make Selection'),
		'engine_rpm': fields.float('Engine(RPM)'),
		'shaft_sealing': fields.selection([('gld_packing_tiga','Gland Packing-TIGA'),('gld_packing_ptfe','Gland Packing-PTFE'),('mc_seal','M/C Seal'),('dynamic_seal','Dynamic seal')],'Shaft Sealing'),
		'scope_of_supply': fields.selection([('bare_pump','Bare Pump'),('pump_with_acces','Pump With Accessories'),('pump_with_acces_motor','Pump With Accessories And Motor')],'Scope of Supply'),
		'drive': fields.selection([('motor','MOTOR'),('vfd','VFD'),('engine','ENGINE')],'Drive'),
		'flange_type': fields.selection([('standard','Standard'),('optional','Optional')],'Flange Type',required=True),
		'pre_suppliy_ref': fields.char('Previous Supply Reference'),
		'flag_standard': fields.boolean('Non Standard'),
		
		##### Product model values ##########
		#'impeller_type': fields.char('Impeller Type', readonly=True),
		'impeller_type': fields.selection([('open','Open'),('semi_open','Semi Open'),('close','Closed')],'Impeller Type'),
		'impeller_number': fields.float('Impeller Number of vanes'),
		'impeller_dia_max': fields.float('Impeller Dia Max mm'),
		'impeller_dia_min': fields.float('Impeller Dia Min mm'),
		'maximum_allowable_soild': fields.float('Maximum Allowable Soild Size - MM'),
		'max_allowable_test': fields.float('Max Allowable Test Pressure'),
		'number_of_stages': fields.integer('Number of stages'),
		#'crm_type': fields.char('Type', readonly=True),
		'crm_type': fields.selection([('pull_out','End Suction Back Pull Out'),('split_case','Split Case'),('multistage','Multistage'),('twin_casing','Twin Casing'),('single_casing','Single Casing'),('self_priming','Self Priming'),('vo_vs4','VO-VS4'),('vg_vs5','VG-VS5')],'Type'),
		'pumpseries_id': fields.many2one('kg.pumpseries.master','Pumpseries',required=True),
		'primemover_id': fields.many2one('kg.primemover.master','Primemover'),
		'primemover_categ': fields.selection([('engine','ENGINE'),('motor','MOTOR'),('vfd','VFD')],'Primemover Category'),
		'moc_const_id':fields.many2one('kg.moc.construction', 'MOC Construction',domain = [('active','=','t')],required=True),
		
		# FC GB
		#~ 'gear_box_loss': fields.float('Gear Box Loss **'),
		#~ 'fluid_coupling_loss': fields.float('Fluid Coupling Loss **'),
		#~ 'mototr_out_put_power': fields.float('Motor Out Put Power'),
		#~ 'higher_speed_rpm': fields.float('Higher Speed(rpm)'),
		#~ 'head_higher_speed': fields.float('Head At Higher Speed'),
		#~ 'effy_hign_speed_point': fields.float('Efficiency At High Speed Point'),
		#~ 'pump_input_hign_speed_point': fields.float('Pump Input At High Speed Point'),
		#~ 'gearbox_loss' fields.float('Gear Box Loss'),
		#~ 'fluidcoupling_loss': fields.float('Fluid Coupling Loss'),
		#~ 'lower_speed_rpm': fields.float('Lower Speed(rpm)'),
		#~ 'head_lower_speed': fields.float('Head At Lower Speed'),
		#~ 'effy_lower_speed_point': fields.float('Efficiency At Lower Speed Point'),
		#~ 'pump_input_lower_speed_point': fields.float('Pump Input At Lower Speed'),
		
		# Accesssories 
		'acces': fields.selection([('yes','Yes'),('no','No')],'Accessories'),
		'acces_type': fields.selection([('coupling','Coupling'),('coupling_guard','Coupling Guard'),('base_plate','Base Plate')],'Type'),
		
	}
	
	_defaults = {
		
		'temperature': 'normal',
		'flange_type': 'standard',
		
	}
	
	"""
	def default_get(self, cr, uid, fields, context=None):
		return context
	
	def create(self, cr, uid, vals, context=None):
		header_rec = self.pool.get('kg.crm.enquiry').browse(cr, uid,vals['header_id'])
		if header_rec.state == 'draft':
			res = super(ch_kg_crm_enquiry, self).create(cr, uid, vals, context=context)
		else:
			res = False
		return res
	"""	
	"""
	def default_get(self, cr, uid, fields, context=None):
		print"contextcontextcontext",context
		if context['purpose_categ']:
			if context['purpose_categ'] == 'pump_spare':
				context['purpose_categ'] = ''
			else:
				pass
		else:
			pass
		return context
		"""
	
	def onchange_moc(self, cr, uid, ids, moc_const_id,flag_standard):
		moc_const_vals=[]
		if moc_const_id != False:
			moc_const_rec = self.pool.get('kg.moc.construction').browse(cr, uid, moc_const_id)
			for item in moc_const_rec.line_ids:
				moc_const_vals.append({
																
								'moc_id': item.moc_id.id,
								'offer_id': item.offer_id.id,
								'remarks': item.remarks,
								'flag_standard':flag_standard,
								
								})
		return {'value': {'line_ids_moc_a': moc_const_vals}}
	
	def onchange_flange_type(self, cr, uid, ids, flange_standard, flange_type, context=None):
		value = {'flange_standard': ''}
		if flange_standard:
			value = {'flange_standard': ''}
			
		return {'value': value}
			
	def onchange_bkw_liq(self, cr, uid, ids, bkw_water, bkw_liq, capacity_in, head_in, specific_gravity, efficiency_in, motor_margin, context=None):
		value = {'bkw_water': '','bkw_liq': '','capacity_in': '','head_in': '','specific_gravity': '','efficiency_in': '','motor_margin': ''}
		total = 0.00
		water_total = 0.00
		if efficiency_in:
			total = ((capacity_in * head_in * specific_gravity) / 367.00 ) / efficiency_in
			total = round(total,2)
			water_total = ((capacity_in * head_in * 1) / 367.00 ) / efficiency_in
			water_total = round(water_total,2)
			value = {'bkw_liq': total * 100 ,'bkw_water':water_total * 100, 'motor_margin':total}
		return {'value': value}
			
	def onchange_impeller_tip_speed(self, cr, uid, ids, impeller_tip_speed, impeller_dia_rated, full_load_rpm, context=None):
		value = {'impeller_tip_speed': '','impeller_dia_rated': '','full_load_rpm': ''}
		total = 0.00
		if full_load_rpm or impeller_dia_rated:
			total = ((3.14 * impeller_dia_rated * full_load_rpm) / 60.00 ) / 100.00
			total = round(total,2)
			value = {'impeller_tip_speed': total}
		return {'value': value}
			
	def onchange_belt_loss_in_kw(self, cr, uid, ids, belt_loss_in_kw, bkw_liq, context=None):
		value = {'belt_loss_in_kw': '','bkw_liq': ''}
		total = 0.00
		if belt_loss_in_kw or bkw_liq:
			total = (bkw_liq / 100.00) * 103.00
			total = round(total,2)
			value = {'belt_loss_in_kw': total}
		return {'value': value}
			
	#~ def onchange_type_of_drive(self,cr,uid,ids,type_of_drive,primemover_categ,context=None):
		#~ 
		#~ value = {'primemover_categ':''}
		#~ if type_of_drive == 'engine':
			#~ value = {'primemover_categ':'engine'}
		#~ else:
			#~ value = {'primemover_categ':primemover_categ}
		#~ return {'value': value}
		
	#~ def onchange_prime_categ(self,cr,uid,ids,primemover_categ,type_of_drive,context=None):
		#~ 
		#~ value = {'type_of_drive':''}
		#~ if primemover_categ == 'engine':
			#~ value = {'type_of_drive':'engine'}
		#~ else:
			#~ value = {'type_of_drive':type_of_drive}
		#~ return {'value': value}
	
	def onchange_primemover(self, cr, uid, ids, primemover_id, context=None):
		
		value = {'frequency':'','motor_kw': '','speed_in_motor': '','engine_kw':''}
		if primemover_id:
			prime_rec = self.pool.get('kg.primemover.master').browse(cr, uid, primemover_id, context=context)
			value = {'frequency': prime_rec.frequency,'motor_kw': prime_rec.power_kw,'speed_in_motor': prime_rec.speed,'engine_kw': prime_rec.power_kw}
			
		return {'value': value}
			
	def onchange_liquid(self, cr, uid, ids, fluid_id, context=None):
		
		value = {'viscosity': '','temperature_in_c': '','specific_gravity': '','solid_concen':'','max_particle_size_mm':'','consistency':''}
		if fluid_id:
			liquid_rec = self.pool.get('kg.fluid.master').browse(cr, uid, fluid_id, context=context)
			value = {'viscosity': liquid_rec.viscosity,'temperature_in_c': liquid_rec.temperature,
					 'specific_gravity': liquid_rec.specific_gravity,'solid_concen':liquid_rec.solid_concentration,
					 'max_particle_size_mm':liquid_rec.max_particle_size_mm,'consistency':liquid_rec.consistency}
			
		return {'value': value}
		
	def onchange_head_in(self, cr, uid, ids, head_in, discharge_pressure_kg, sealing_water_pressure, context=None):
		value = {'head_in': '','discharge_pressure_kg': '','sealing_water_pressure':''}
		total = 0.00
		if head_in or discharge_pressure_kg:
			total = (head_in / 10.00) + 1
			value = {'head_in': head_in,'discharge_pressure_kg': head_in / 10.00,'sealing_water_pressure': total}
			
		return {'value': value}
		
	def onchange_pumpmodel(self, cr, uid, ids, pump_id, context=None):
		
		value = {'impeller_type': '','impeller_number': '','impeller_dia_max': '','impeller_dia_min': '','maximum_allowable_soild': '',
				'max_allowable_test': '','number_of_stages': '','crm_type': '','bearing_number_nde':'','bearing_qty_nde':'',
				'sealing_water_pressure':'','pumpseries_id':'','crm_type':'','casing_design':'','sealing_water_capacity':'','size_suctionx':''}
		if pump_id:
			pump_rec = self.pool.get('kg.pumpmodel.master').browse(cr, uid, pump_id, context=context)
			value = {'impeller_type': pump_rec.impeller_type,'impeller_number': pump_rec.impeller_number,'impeller_dia_max': pump_rec.impeller_dia_max,
			'impeller_dia_min': pump_rec.impeller_dia_min,'maximum_allowable_soild': pump_rec.maximum_allowable_soild,'max_allowable_test': pump_rec.max_allowable_test,
			'number_of_stages': pump_rec.number_of_stages,'crm_type': pump_rec.crm_type,'bearing_number_nde':pump_rec.bearing_no,'bearing_qty_nde':pump_rec.bearing_qty,
			'sealing_water_pressure':pump_rec.sealing_water_pressure,'pumpseries_id':pump_rec.series_id.id,'crm_type':pump_rec.crm_type,'casing_design':pump_rec.feet_location,
			'sealing_water_capacity':pump_rec.sealing_water_capacity,'size_suctionx':pump_rec.pump_size}
			
		return {'value': value}
		
	def onchange_pumpseries(self, cr, uid, ids, pumpseries_id, flange_standard, flange_type, context=None):
		
		value = {'flange_standard': '','flange_type': ''}
		if pumpseries_id:
			pumpseries_rec = self.pool.get('kg.pumpseries.master').browse(cr, uid, pumpseries_id, context=context)
			for item in pumpseries_rec.line_ids:
				if item.flange_type == 'standard':
					value = {'flange_standard': item.id,'flange_type': item.flange_type}
					return {'value': value}
				
		return True
		
	def onchange_scope_of_supply(self, cr, uid, ids, scope_of_supply, primemover_categ, context=None):
		
		value = {'primemover_categ': ''}
		if scope_of_supply == 'pump_with_acces_motor':
			value = {'primemover_categ': 'motor'}
		return {'value': value}

		
	def create(self, cr, uid, vals, context=None):
		pump_obj = self.pool.get('kg.pumpmodel.master')
		if vals.get('pump_id'):		  
			pump_rec = pump_obj.browse(cr, uid, vals.get('pump_id'))			
			vals.update({'impeller_type': pump_rec.impeller_type,'impeller_number': pump_rec.impeller_number,'impeller_dia_max': pump_rec.impeller_dia_max,
			'impeller_dia_min': pump_rec.impeller_dia_min,'maximum_allowable_soild': pump_rec.maximum_allowable_soild,'max_allowable_test': pump_rec.max_allowable_test,
			'number_of_stages': pump_rec.number_of_stages,'crm_type': pump_rec.crm_type})
		return super(ch_kg_crm_pumpmodel, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		pump_obj = self.pool.get('kg.pumpmodel.master')
		if vals.get('pump_id'):
			pump_rec = pump_obj.browse(cr, uid, vals.get('pump_id'))			
			vals.update({'impeller_type': pump_rec.impeller_type,'impeller_number': pump_rec.impeller_number,'impeller_dia_max': pump_rec.impeller_dia_max,
			'impeller_dia_min': pump_rec.impeller_dia_min,'maximum_allowable_soild': pump_rec.maximum_allowable_soild,'max_allowable_test': pump_rec.max_allowable_test,
			'number_of_stages': pump_rec.number_of_stages,'crm_type': pump_rec.crm_type})
		return super(ch_kg_crm_pumpmodel, self).write(cr, uid, ids, vals, context)  
	
	def load_non_standard(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		
		if rec.flag_standard == True:
			cons_obj = self.pool.get('ch.moc.construction').search(cr,uid,[('header_id','=',rec.id)])
			if cons_obj:
				for item in cons_obj:
					cons_rec = self.pool.get('ch.moc.construction').browse(cr,uid,item)
					self.pool.get('ch.moc.construction').write(cr, uid, cons_rec.id, {'flag_standard': True})
		elif rec.flag_standard == False:
			cons_obj = self.pool.get('ch.moc.construction').search(cr,uid,[('header_id','=',rec.id)])
			if cons_obj:
				for item in cons_obj:
					cons_rec = self.pool.get('ch.moc.construction').browse(cr,uid,item)
					self.pool.get('ch.moc.construction').write(cr, uid, cons_rec.id, {'flag_standard': False})
		return True	
	
ch_kg_crm_pumpmodel()


class ch_kg_crm_foundry_item(osv.osv):

	_name = "ch.kg.crm.foundry.item"
	_description = "Child Foundry Item Details"
	
	_columns = {
	
		### Foundry Item Details ####
		'header_id':fields.many2one('ch.kg.crm.pumpmodel', 'Pump Model Id', ondelete='cascade'),
		'enquiry_id':fields.many2one('kg.crm.enquiry', 'Enquiry'),
		'pump_id':fields.many2one('kg.pumpmodel.master', 'Pump'),
		'qty':fields.integer('Quantity'),
		'oth_spec':fields.char('Other Specification'),
		'pattern_code': fields.many2one('kg.pattern.master','Pattern No'),
		'pattern_name': fields.char('Pattern Name'),
		
	}
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_kg_crm_foundry_item, self).write(cr, uid, ids, vals, context)
	
	def onchange_pattern_name(self, cr, uid, ids, pattern_code,pattern_name):
		value = {'pattern_name':''}
		pattern_obj = self.pool.get('kg.pattern.master').search(cr,uid,([('id','=',pattern_code)]))
		if pattern_obj:
			pattern_rec = self.pool.get('kg.pattern.master').browse(cr,uid,pattern_obj[0])
			value = {'pattern_name':pattern_rec.pattern_name}
		return {'value': value}
	
ch_kg_crm_foundry_item()

class ch_kg_crm_machineshop_item(osv.osv):

	_name = "ch.kg.crm.machineshop.item"
	_description = "Macine Shop Item Details"
	
	_columns = {
	
		### machineshop Item Details ####
		'header_id':fields.many2one('ch.kg.crm.pumpmodel', 'Pump Model Id', ondelete='cascade'),
		'enquiry_id':fields.many2one('kg.crm.enquiry', 'Enquiry'),
		'ms_line_id':fields.many2one('ch.machineshop.details', 'Machine Shop Id'),
		'pos_no': fields.related('ms_line_id','pos_no', type='integer', string='Position No', store=True),
		'bom_id': fields.many2one('kg.bom','BOM'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','ms')], ondelete='cascade',required=True),
		'name':fields.char('Item Name', size=128),	  
		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
		#'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'remarks':fields.text('Remarks'),   
		
	}
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_kg_crm_machineshop_item, self).write(cr, uid, ids, vals, context)
		
	
ch_kg_crm_machineshop_item()

class ch_kg_crm_bot(osv.osv):

	_name = "ch.kg.crm.bot"
	_description = "BOT Details"
	
	_columns = {
	
		### machineshop Item Details ####
		'header_id':fields.many2one('ch.kg.crm.pumpmodel', 'Pump Model Id', ondelete='cascade'),
		'enquiry_id':fields.many2one('kg.crm.enquiry', 'Enquiry'),
		'product_temp_id':fields.many2one('product.product', 'Item Name',domain = [('type','=','bot')], ondelete='cascade',required=True),
		'bot_line_id':fields.many2one('ch.bot.details', 'BOT Line Id'),
		'bom_id': fields.many2one('kg.bom','BOM'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','bot')], ondelete='cascade',required=True),
		'code':fields.char('Item Code', size=128),	  
		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
		#'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'remarks':fields.text('Remarks'),   
		
	}
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_kg_crm_bot, self).write(cr, uid, ids, vals, context)
		
	
ch_kg_crm_bot()

class ch_moc_construction(osv.osv):

	_name = "ch.moc.construction"
	_description = "MOC Construction Details"
	
	_columns = {
	
		
		'header_id':fields.many2one('ch.kg.crm.pumpmodel', 'Header Id', ondelete='cascade'),
		'moc_id':fields.many2one('kg.moc.master', 'MOC Name',domain = "[('active','=','t'),'&',('state','not in',('raject','cancel')]",required=True),
		'offer_id':fields.many2one('kg.offer.materials', 'Offer Name',domain = "[('active','=','t'),'&',('state','not in',('raject','cancel')]",required=True),
		#~ 'pattern_id': fields.many2one('kg.pattern.master','Pattern No', required=True,domain="[('active','=','t')]"), 		
		#~ 'pattern_name': fields.char('Pattern Name'), 	
		'remarks':fields.text('Remarks'),   
		'flag_standard': fields.boolean('Non Standard'),
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		
		return context
		
	#~ def onchange_pattern_name(self, cr, uid, ids, pattern_id, context=None):
		#~ 
		#~ value = {'pattern_name': ''}
		#~ if pattern_id:
			#~ pro_rec = self.pool.get('kg.pattern.master').browse(cr, uid, pattern_id, context=context)
			#~ value = {'pattern_name': pro_rec.pattern_name}
			#~ 
		#~ return {'value': value}
		
		
	#~ def create(self, cr, uid, vals, context=None):
		#~ pattern_obj = self.pool.get('kg.pattern.master')
		#~ if vals.get('pattern_id'):		  
			#~ pattern_rec = pattern_obj.browse(cr, uid, vals.get('pattern_id') )
			#~ pattern_name = pattern_rec.pattern_name
			#~ vals.update({'pattern_name': pattern_name})
		#~ return super(ch_moc_construction, self).create(cr, uid, vals, context=context)
		#~ 
	#~ def write(self, cr, uid, ids, vals, context=None):
		#~ pattern_obj = self.pool.get('kg.pattern.master')
		#~ if vals.get('pattern_id'):
			#~ pattern_rec = pattern_obj.browse(cr, uid, vals.get('pattern_id') )
			#~ pattern_name = pattern_rec.pattern_name
			#~ vals.update({'pattern_name': pattern_name})		
		#~ return super(ch_moc_construction, self).write(cr, uid, ids, vals, context)  
		
	
	
ch_moc_construction()
