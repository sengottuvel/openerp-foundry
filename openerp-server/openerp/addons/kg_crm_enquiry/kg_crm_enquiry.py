from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

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
		'name': fields.char('Offer Number', size=128,select=True),
		'schedule_no': fields.char('Schedule No', size=128,select=True),
		'enquiry_date': fields.date('Enquiry Date',required=True),
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
		'industry_id': fields.many2one('kg.industry.master','Industry'),
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
		'scope_of_supply': fields.selection([('bare_pump','Bare pump'),('pump_with_acces','Pump with Accessories')],'Scope of Supply', required=True),
		'pump': fields.selection([('gld_packing','Gland Packing'),('mc_seal','M/C Seal'),('dynamic_seal','Dynamic seal')],'Shaft Shalling', required=True),
		'drive': fields.selection([('motor','Motor'),('vfd','VFD'),('engine','Engine')],'Drive', required=True),
		'transmision': fields.selection([('cpl','Coupling'),('belt','Belt Drive'),('fc','Fluid Coupling'),('gear_box','Gear Box'),('fc_gear_box','Fluid Coupling With Gear Box')],'Transmision', required=True),
		'acces': fields.selection([('yes','Yes'),('no','No')],'Accessories', required=True),
		
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
			return True
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
			return True
		return False
		
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
		'fluid_id': fields.many2one('kg.fluid.master','Fluid'),
		'primemover_id': fields.many2one('kg.primemover.master','Primemover'),
		'pumpseries_id': fields.many2one('kg.pumpseries.master','Pumpseries'),
		
		########## Karthikeyan Item Details Added Start here ################
		'equipment_no': fields.char('Equipment No', required=True),
		'quantity_in_no': fields.integer('Quantity in No', required=True),
		'description': fields.char('Description', required=True),
		
		########## Karthikeyan Liquid Specifications Added Start here ################
		'solid_concen': fields.float('Solid Concentration in %', required=True),
		'viscosity': fields.float('Viscosity correction factors', required=True),
		'max_size_mm': fields.float('Max Size-mm', required=True),
		'slurry_correction_in': fields.float('Slurry Correction in', required=True),
		'temperature': fields.selection([('normal','NORMAL'),('jacketting','JACKETTING'),('centre_line','CENTRE LINE')],'Temperature in C', required=True),
		'suction_condition': fields.selection([('positive','Positive'),('negative','Negative')],'Suction Condition', required=True),
		'suction_pressure': fields.selection([('normal','Normal'),('centre_line','Centre Line')],'Suction pressure', required=True),
		'npsh_avl': fields.integer('NPSH-AVL', required=True),		
		'suction_pressure_kg': fields.float('Suction Pressure - kg/cm2', required=True),
		'discharge_pressure_kg': fields.float('Discharge Pressure - kg/cm2', required=True),
		'differential_pressure_kg': fields.float('Differential Pressure - kg/cm2', required=True),
		
		########## Karthikeyan Duty Parameters Added Start here ################	
		
		'capacity_in': fields.integer('Capacity in M3 / hr', required=True),
		'head_in': fields.integer('Total Head in Mlc', required=True),
		
		########## Karthikeyan Pump Specification Added Start here ################	
		'pump_type': fields.char('Pump Model', required=True),		
		'casing_design': fields.selection([('base','Base'),('center_line','Center Line')],'Casing Feet Location', required=True),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type', required=True,domain="[('active','=','t')]"),		
		'size_suctionx': fields.char('Size-SuctionX Delivery- in mm', required=True),
		'flange_standard': fields.char('Flange Standard', required=True),
		'efficiency_in': fields.float('Efficiency in % Wat/Liq', required=True),
		'npsh_r_m': fields.float('NPSH R - M', required=True),
		'best_efficiency': fields.float('Best Efficiency NPSH in M', required=True),
		'bkw_water': fields.float('BKW Water', required=True),
		'bkw_liq': fields.float('BKW Liq', required=True),		
		'impeller_dia_rated': fields.float('Impeller Dia Rated mm', required=True),
		'impeller_tip_speed': fields.float('Impeller Tip Speed -M/Sec', required=True),		
		'hydrostatic_test_pressure': fields.float('Hydrostatic Test Pressure - Kg/cm2', required=True),		
		'shut_off_head': fields.float('Shut off Head in M', required=True),
		'minimum_contionuous': fields.float('Minimum Contionuous Flow - M3/hr', required=True),
		'specific_speed': fields.float('Specific Speed', required=True),
		'suction_specific_speed': fields.float('Suction Specific Speed', required=True),
		'sealing_water_pressure': fields.float('Sealing Water Pressure Kg/cm^2', required=True),
		'sealing_water_capcity': fields.float('Sealing Water Capcity- m3/hr', required=True),
		'gd_sq_value': fields.float('GD SQ value', required=True),
		'critical_speed': fields.float('Critical Speed', required=True),
		'bearing_make': fields.float('Bearing Make', required=True),
		'bearing_number_nde': fields.float('BEARING NUMBER NDE / DE', required=True),
		'bearing_qty_nde': fields.float('Bearing qty NDE / DE', required=True),
		'type_of_drive': fields.selection([('motor_direct','Motor-direct'),('vfd','VFD'),('belt_drive','Belt drive'),('fc_gb','FC GB'),('engine','ENGINE')],'Type of Drive', required=True),
		'end_of_the_curve': fields.float('End of the curve - KW(Rated) liquid', required=True),
		'motor_frequency_hz': fields.float('Motor frequency HZ', required=True),
		'motor_margin': fields.integer('Motor Margin(%)', required=True),
		'motor_kw': fields.float('Motor KW', required=True),
		'speed_in_pump': fields.float('Speed in RPM-Pump', required=True),
		'speed_in_motor': fields.float('Speed in RPM-Motor', required=True),
		'full_load_rpm': fields.float('Full Load RPM', required=True),
		'engine_kw': fields.float('Engine KW', required=True),
		'belt_loss_in_kw': fields.float('Belt Loss in Kw - 3% of BKW', required=True),
		'type_make_selection': fields.selection([('base','Base'),('center_line','Center Line')],'Type Make Selection', required=True),
		
		
		##### Product model values ##########
		#'impeller_type': fields.char('Impeller Type', readonly=True),
		'impeller_type': fields.selection([('open','Open'),('semi_open','Semi Open'),('close','Closed')],'Impeller Type',readonly=True),
		'impeller_number': fields.float('Impeller Number of vanes', readonly=True),
		'impeller_dia_max': fields.float('Impeller Dia Max mm', readonly=True),
		'impeller_dia_min': fields.float('Impeller Dia Min mm', readonly=True),
		'maximum_allowable_soild': fields.float('Maximum Allowable Soild Size - MM', readonly=True),
		'max_allowable_test': fields.float('Max Allowable Test Pressure', readonly=True),
		'number_of_stages': fields.integer('Number of stages', readonly=True),
		#'crm_type': fields.char('Type', readonly=True),
		'crm_type': fields.selection([('pull_out','End Suction Back Pull Out'),('split_case','Split Case'),('multistage','Multistage'),('twin_casing','Twin Casing'),('single_casing','Single Casing'),('self_priming','Self Priming'),('vo_vs4','VO-VS4'),('vg_vs5','VG-VS5')],'Type',readonly=True),
		
		
		'moc_const_id':fields.many2one('kg.moc.construction', 'MOC Construction',domain = [('active','=','t')],required=True),
		
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
		
		
	def onchange_pumpmodel(self, cr, uid, ids, pump_id, context=None):
		
		value = {'impeller_type': '','impeller_number': '','impeller_dia_max': '','impeller_dia_min': '','maximum_allowable_soild': '','max_allowable_test': '','number_of_stages': '','crm_type': ''}
		if pump_id:
			pump_rec = self.pool.get('kg.pumpmodel.master').browse(cr, uid, pump_id, context=context)
			value = {'impeller_type': pump_rec.impeller_type,'impeller_number': pump_rec.impeller_number,'impeller_dia_max': pump_rec.impeller_dia_max,
			'impeller_dia_min': pump_rec.impeller_dia_min,'maximum_allowable_soild': pump_rec.maximum_allowable_soild,'max_allowable_test': pump_rec.max_allowable_test,
			'number_of_stages': pump_rec.number_of_stages,'crm_type': pump_rec.crm_type}
			
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
		'moc_id':fields.many2one('kg.moc.construction', 'MOC Construction',domain = [('active','=','t')],required=True),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No', required=True,domain="[('active','=','t')]"), 		
		'pattern_name': fields.char('Pattern Name'), 	
		'remarks':fields.text('Remarks'),   
		
	}
	
	def onchange_pattern_name(self, cr, uid, ids, pattern_id, context=None):
		
		value = {'pattern_name': ''}
		if pattern_id:
			pro_rec = self.pool.get('kg.pattern.master').browse(cr, uid, pattern_id, context=context)
			value = {'pattern_name': pro_rec.pattern_name}
			
		return {'value': value}
		
		
	def create(self, cr, uid, vals, context=None):
		pattern_obj = self.pool.get('kg.pattern.master')
		if vals.get('pattern_id'):		  
			pattern_rec = pattern_obj.browse(cr, uid, vals.get('pattern_id') )
			pattern_name = pattern_rec.pattern_name
			vals.update({'pattern_name': pattern_name})
		return super(ch_moc_construction, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		pattern_obj = self.pool.get('kg.pattern.master')
		if vals.get('pattern_id'):
			pattern_rec = pattern_obj.browse(cr, uid, vals.get('pattern_id') )
			pattern_name = pattern_rec.pattern_name
			vals.update({'pattern_name': pattern_name})		
		return super(ch_moc_construction, self).write(cr, uid, ids, vals, context)  
		
	
	
ch_moc_construction()
