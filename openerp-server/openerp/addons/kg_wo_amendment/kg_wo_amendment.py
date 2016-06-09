from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import base64

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')


ORDER_PRIORITY = [
   ('normal','Normal'),
   ('emergency','Emergency')
]

ORDER_CATEGORY = [
   ('pump','Pump'),
   ('spare','Spare'),
   ('pump_spare','Pump and Spare'),
   ('service','Service'),
   ('project','Project')
]


class kg_wo_amendment(osv.osv):

	_name = "kg.wo.amendment"
	_description = "Work Order Amendment"
	_order = "entry_date desc"
	
	def _get_order_value(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		
		for entry in self.browse(cr, uid, ids, context=context):
			cr.execute(''' select sum(qty * amend_unit_price) from ch_amend_work_order_details where header_id = %s
			and  order_category = 'pump' ''',[entry.id])
			pump_wo_value = cr.fetchone()
			
			cr.execute(''' select sum(line.qty * header.amend_unit_price) from ch_amend_order_bom_details as line
				left join ch_amend_work_order_details header on header.id = line.header_id where header.header_id = %s 
				and header.order_category='spare' ''',[entry.id])
			spare_wo_value = cr.fetchone()
			if pump_wo_value[0] == None:
				pump_value = 0.00
			else:
				pump_value= pump_wo_value[0]
			if spare_wo_value[0] == None:
				spare_value = 0.00
			else:
				spare_value=spare_wo_value[0]
			wo_value = pump_value + spare_value
			result[entry.id] = wo_value
		return result
	

	_columns = {
	
		### Work Order Header Details ####
		
		'wo_id': fields.many2one('kg.work.order','WO No.',domain="[('state','=','confirmed')]",required=True),
		'wo_date': fields.date('WO Date'),
		'wo_division_id': fields.many2one('kg.division.master','Division',readonly=True,domain="[('active','=','t')]"),
		'wo_location': fields.selection([('ipd','IPD'),('ppd','PPD'),('export','Export')],'Location'),
		'wo_order_priority': fields.selection(ORDER_PRIORITY,'Priority'),
		'wo_delivery_date': fields.date('Delivery Date'),
		'wo_order_value': fields.float('WO Value'),
		'wo_order_category': fields.selection(ORDER_CATEGORY,'Category'),
		'wo_partner_id': fields.many2one('res.partner','Customer'),
		'wo_remarks': fields.text('Remarks'),
		
		### Amendment Details ###
		'name': fields.char('Amendment No.', size=128,select=True),
		'entry_date': fields.date('Amendment Date',required=True),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'wo_amend_date': fields.date('Amend Date'),
		'wo_amend_division_id': fields.many2one('kg.division.master','Amend Division',readonly=True,domain="[('active','=','t')]"),
		'wo_amend_location': fields.selection([('ipd','IPD'),('ppd','PPD'),('export','Export')],'Amend Location'),
		'wo_amend_order_priority': fields.selection(ORDER_PRIORITY,'Amend Priority'),
		'wo_amend_delivery_date': fields.date('Amend Delivery Date'),
		'wo_amend_order_value': fields.function(_get_order_value, string='Amend WO Value', method=True, store=True, type='float'),
		'wo_amend_order_category': fields.selection(ORDER_CATEGORY,'Amend Category'),
		'wo_amend_partner_id': fields.many2one('res.partner','Amend Customer'),
		'wo_amend_remarks': fields.text('Amend Remarks'),
		'flag_amend': fields.boolean('Load WO'),
		'flag_confirm': fields.boolean('Confirm Flag'),
		'line_ids': fields.one2many('ch.amend.work.order.details', 'header_id', "Work Order Details"),
		
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_wo_amendment', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',
		'active': True,
		'flag_amend': False,
		#~ 'division_id':_get_default_division,
		'wo_amend_delivery_date' : lambda * a: time.strftime('%Y-%m-%d'),
	
	}
	
	def load_wo_data(self, cr, uid, ids, context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		if entry_rec.wo_id:
			### Check WO ###
			cr.execute(''' select header.id from ch_schedule_details line
							left join kg_schedule header on header.id = line.header_id
							where header.state = 'confirmed'
							and line.order_id = %s
							limit 1 ''',[entry_rec.wo_id.id])
			wo_mapping = cr.fetchone()
			
			if wo_mapping != None:
				raise osv.except_osv(_('Warning!'),
					_('Amendment not allowed. Work Order is in next process !!'))
			### Loading Header Details ###
			self.write(cr, uid, ids,{
			'wo_date':entry_rec.wo_id.entry_date,
			'wo_division_id':entry_rec.wo_id.division_id.id,
			'wo_location':entry_rec.wo_id.location,
			'wo_order_category':entry_rec.wo_id.order_category,
			'wo_order_priority':entry_rec.wo_id.order_priority,
			'wo_partner_id':entry_rec.wo_id.partner_id.id,
			'wo_delivery_date':entry_rec.wo_id.delivery_date,
			'wo_order_value':entry_rec.wo_id.order_value,
			'wo_remarks':entry_rec.wo_id.remarks,
			'wo_amend_date':entry_rec.wo_id.entry_date,
			'wo_amend_division_id':entry_rec.wo_id.division_id.id,
			'wo_amend_location':entry_rec.wo_id.location,
			'wo_amend_order_category':entry_rec.wo_id.order_category,
			'wo_amend_order_priority':entry_rec.wo_id.order_priority,
			'wo_amend_partner_id':entry_rec.wo_id.partner_id.id,
			'wo_amend_delivery_date':entry_rec.wo_id.delivery_date,
			'wo_amend_order_value':entry_rec.wo_id.order_value,
			'wo_amend_remarks':entry_rec.wo_id.remarks,
			'flag_amend':True,
			'flag_confirm':True
			
			})
			#### Loading WO Details ###
			for line_item in entry_rec.wo_id.line_ids:
				
				amend_wo_line_obj = self.pool.get('ch.amend.work.order.details')
				amend_line_vals = {
				
					'header_id': ids[0],
					'wo_line_id': line_item.id,
					'order_priority': line_item.order_priority,
					'pump_model_id': line_item.pump_model_id.id,
					'pump_model_type': line_item.pump_model_type,
					'order_no': line_item.order_no,
					'order_category': line_item.order_category,
					'qty': line_item.qty,
					'note': line_item.note,
					'delivery_date': line_item.delivery_date,
					'flag_standard': line_item.flag_standard,
					'unit_price': line_item.unit_price,
					'moc_construction_id': line_item.moc_construction_id.id,
					'rpm': line_item.rpm,
					'setting_height': line_item.setting_height,
					'bed_length': line_item.bed_length,
					'shaft_sealing': line_item.shaft_sealing,
					'motor_power': line_item.motor_power,
					'bush_bearing': line_item.bush_bearing,
					'delivery_pipe_size': line_item.delivery_pipe_size,
					'lubrication': line_item.lubrication,
					'flag_load_bom': line_item.flag_load_bom,
					'bp': line_item.bp,
					'shaft_ext': line_item.shaft_ext,
					'amend_mode': 'from_wo',
					'amend_unit_price': line_item.unit_price,
				}
				line_item_id = amend_wo_line_obj.create(cr, uid, amend_line_vals)
				### Loading Foundry Items ###
				
				for foundry_item in line_item.line_ids:
					
					foundry_vals = {
						'header_id': line_item_id,
						'wo_foundry_id': foundry_item.id,
						'bom_id': foundry_item.bom_id.id,
						'bom_line_id': foundry_item.bom_line_id.id,
						'pattern_id': foundry_item.pattern_id.id,
						'pattern_name': foundry_item.pattern_name,
						'weight': foundry_item.weight,
						'pos_no': foundry_item.pos_no,
						'moc_id': foundry_item.moc_id.id,
						'qty': foundry_item.qty,
						'unit_price': foundry_item.unit_price,
						'schedule_qty': foundry_item.schedule_qty,
						'production_qty': foundry_item.production_qty,
						'flag_applicable': foundry_item.flag_applicable,
						'add_spec': foundry_item.add_spec,		   
						'flag_standard': foundry_item.flag_standard,
						'flag_pattern_check': foundry_item.flag_pattern_check,
						'entry_mode': foundry_item.entry_mode,
					}
					amend_foundry_line_obj = self.pool.get('ch.amend.order.bom.details')
					foundry_item_id = amend_foundry_line_obj.create(cr, uid, foundry_vals)
				
				### Loading Machine Shop Items ###
				
				for ms_item in line_item.line_ids_a:
					
					ms_vals = {
						
						'header_id': line_item_id,
						'wo_ms_id': ms_item.id,
						'ms_line_id': ms_item.ms_line_id.id,
						'pos_no': ms_item.pos_no,
						'bom_id': ms_item.bom_id.id,
						'ms_id': ms_item.ms_id.id,
						'moc_id':  ms_item.moc_id.id,
						'name': ms_item.name,	  
						'qty':  ms_item.qty,
						'flag_applicable': ms_item.flag_applicable,
						'order_category':  ms_item.order_category,
						'remarks': ms_item.remarks, 
						'flag_standard':  ms_item.flag_standard, 
						'entry_mode':  ms_item.entry_mode,
					}
					amend_ms_line_obj = self.pool.get('ch.amend.order.machineshop.details')
					ms_item_id = amend_ms_line_obj.create(cr, uid, ms_vals)
				
				### Loading BOT Items ###
				
				for bot_item in line_item.line_ids_b:
					
					bot_vals = {
					
						'header_id': line_item_id,
						'wo_bot_id': bot_item.id,
						'bot_line_id': bot_item.bot_line_id.id,
						'bot_id': bot_item.bot_id.id,
						'item_name': bot_item.item_name,
						'bom_id': bot_item.bom_id.id,
						'moc_id': bot_item.moc_id.id,
						'qty': bot_item.qty,
						'flag_applicable': bot_item.flag_applicable,
						'order_category': bot_item.order_category,
						'remarks': bot_item.remarks,
						'flag_standard': bot_item.flag_standard,
						'entry_mode': bot_item.entry_mode,
					}
					amend_bot_line_obj = self.pool.get('ch.amend.order.bot.details')
					bot_item_id = amend_bot_line_obj.create(cr, uid, bot_vals)
				
				
		return True
		
	def entry_confirm(self, cr, uid, ids, context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		amend_line_obj = self.pool.get('ch.amend.work.order.details')
		
		### Amendment No. Generation ###
		total_amends=self.search(cr,uid,[('wo_id','=',entry_rec.wo_id.id)])
		if len(total_amends) == 1:
			amend_no = entry_rec.wo_id.name + '-01'
		else:
			amend_no = entry_rec.wo_id.name + '-' + '%02d' % int(str(len(total_amends)))
		self.write(cr, uid, entry_rec.id,{'flag_confirm':False,'name': amend_no,'state':'confirmed','confirm_user_id':uid,'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		
		### Header Details Amedment ###
		version = amend_no[-2:]
		wo_obj = self.pool.get('kg.work.order')
		wo_obj.write(cr, uid, entry_rec.wo_id.id,{
			
			'entry_date': entry_rec.wo_amend_date,
			'location': entry_rec.wo_amend_location,
			'order_category': entry_rec.wo_amend_order_category,
			'order_priority': entry_rec.wo_amend_order_priority,
			'partner_id': entry_rec.wo_amend_partner_id.id,
			'delivery_date': entry_rec.wo_amend_delivery_date,
			'remarks': entry_rec.wo_amend_remarks,
			'version': version,
			'order_value': entry_rec.wo_amend_order_value
			})
			
		####
		cr.execute(''' update kg_work_order set order_value = %s  where id = %s ''',[entry_rec.wo_amend_order_value,entry_rec.wo_id.id])
		
		### Line Details Amendment ###
		
		### Line Deletion ###
		cr.execute(''' delete from  ch_work_order_details where id in (

			select id from ch_work_order_details where
			id not in
			(select wo_line_id from ch_amend_work_order_details  where header_id = %s
			INTERSECT
			select id from ch_work_order_details  where header_id = %s)
			and header_id = %s) ''',[entry_rec.id,entry_rec.wo_id.id,entry_rec.wo_id.id])
		
		number = 1
		for amend_line_item in entry_rec.line_ids:
			
			wo_line_obj = self.pool.get('ch.work.order.details')
			### Unit Price ###
			if amend_line_item.wo_line_id.id != False:
				wo_line_obj.write(cr, uid, amend_line_item.wo_line_id.id,{
					'unit_price': amend_line_item.amend_unit_price
					})
			
			### Line Addtion ###
			if amend_line_item.wo_line_id.id == False:
				
				### Order No ###
				if number == 1:
					cr.execute(''' select count(id) from ch_amend_work_order_details  
						where header_id = %s and id != %s ''',[entry_rec.id,amend_line_item.id])	  
					wo_count = cr.fetchone()
					number = wo_count[0] + 1
				cr.execute(''' select to_char(%s, 'FMRN') ''',[number])	  
				roman = cr.fetchone()
				order_name = entry_rec.wo_id.name + '-' + str(roman[0])
				number = number + 1
				
				amend_line_obj.write(cr, uid, amend_line_item.id,{'order_no': order_name})
				
				line_vals = {
				
					'header_id': entry_rec.wo_id.id,
					'order_priority': amend_line_item.order_priority,
					'pump_model_id': amend_line_item.pump_model_id.id,
					'pump_model_type': amend_line_item.pump_model_type,
					'order_no': order_name,
					'order_category': amend_line_item.order_category,
					'qty': amend_line_item.qty,
					'note': amend_line_item.note,
					'delivery_date': amend_line_item.delivery_date,
					'flag_standard': amend_line_item.flag_standard,
					'unit_price': amend_line_item.unit_price,
					'moc_construction_id': amend_line_item.moc_construction_id.id,
					'rpm': amend_line_item.rpm,
					'setting_height': amend_line_item.setting_height,
					'bed_length': amend_line_item.bed_length,
					'shaft_sealing': amend_line_item.shaft_sealing,
					'motor_power': amend_line_item.motor_power,
					'bush_bearing': amend_line_item.bush_bearing,
					'delivery_pipe_size': amend_line_item.delivery_pipe_size,
					'lubrication': amend_line_item.lubrication,
					'flag_load_bom': amend_line_item.flag_load_bom,
					'bp': amend_line_item.bp,
					'shaft_ext': amend_line_item.shaft_ext,
				}
				
				line_item_id = wo_line_obj.create(cr, uid, line_vals)
				
				### Loading Foundry Items ###
				
				for foundry_item in amend_line_item.line_ids:
					
					foundry_vals = {
						'header_id': line_item_id,
						'bom_id': foundry_item.bom_id.id,
						'bom_line_id': foundry_item.bom_line_id.id,
						'pattern_id': foundry_item.pattern_id.id,
						'pattern_name': foundry_item.pattern_name,
						'weight': foundry_item.weight,
						'pos_no': foundry_item.pos_no,
						'moc_id': foundry_item.moc_id.id,
						'qty': foundry_item.qty,
						'unit_price': foundry_item.unit_price,
						'schedule_qty': foundry_item.schedule_qty,
						'production_qty': foundry_item.production_qty,
						'flag_applicable': foundry_item.flag_applicable,
						'add_spec': foundry_item.add_spec,		   
						'flag_standard': foundry_item.flag_standard,
						'flag_pattern_check': foundry_item.flag_pattern_check,
						'entry_mode': foundry_item.entry_mode,
					}
					foundry_line_obj = self.pool.get('ch.order.bom.details')
					foundry_item_id = foundry_line_obj.create(cr, uid, foundry_vals)
				
				### Loading Machine Shop Items ###
				
				for ms_item in amend_line_item.line_ids_a:
					
					ms_vals = {
						
						'header_id': line_item_id,
						'wo_ms_id': ms_item.id,
						'ms_line_id': ms_item.ms_line_id.id,
						'pos_no': ms_item.pos_no,
						'bom_id': ms_item.bom_id.id,
						'ms_id': ms_item.ms_id.id,
						'moc_id':  ms_item.moc_id.id,
						'name': ms_item.name,	  
						'qty':  ms_item.qty,
						'flag_applicable': ms_item.flag_applicable,
						'order_category':  ms_item.order_category,
						'remarks': ms_item.remarks, 
						'flag_standard':  ms_item.flag_standard, 
						'entry_mode':  ms_item.entry_mode,
					}
					ms_line_obj = self.pool.get('ch.order.machineshop.details')
					ms_item_id = ms_line_obj.create(cr, uid, ms_vals)
				
				### Loading BOT Items ###
				
				for bot_item in amend_line_item.line_ids_b:
					
					bot_vals = {
					
						'header_id': line_item_id,
						'wo_bot_id': bot_item.id,
						'bot_line_id': bot_item.bot_line_id.id,
						'bot_id': bot_item.bot_id.id,
						'item_name': bot_item.item_name,
						'bom_id': bot_item.bom_id.id,
						'moc_id': bot_item.moc_id.id,
						'qty': bot_item.qty,
						'flag_applicable': bot_item.flag_applicable,
						'order_category': bot_item.order_category,
						'remarks': bot_item.remarks,
						'flag_standard': bot_item.flag_standard,
						'entry_mode': bot_item.entry_mode,
					}
					bot_line_obj = self.pool.get('ch.order.bot.details')
					bot_item_id = bot_line_obj.create(cr, uid, bot_vals)
				
			
			
		return True
	

kg_wo_amendment()

class ch_amend_work_order_details(osv.osv):

	_name = "ch.amend.work.order.details"
	_description = "Work Order Details Amendment"
	_rec_name = 'order_no'
	
	_columns = {
	
		### Order Details ####
		'header_id':fields.many2one('kg.wo.amendment', 'WO Amendment', required=1, ondelete='cascade'),
		'amend_date': fields.related('header_id','entry_date', type='date', string='Date', store=True, readonly=True),
		'wo_id': fields.related('header_id','wo_id',type='many2one', relation='kg.work.order', string='WO No.', store=True, readonly=True),
		'wo_line_id': fields.many2one('ch.work.order.details',string='Work Order Line'),
		'order_priority': fields.related('header_id','wo_order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True,domain="[('active','=','t')]"),
		'pump_model_type':fields.related('pump_model_id','type', type='selection',selection=[('vertical','Vertical'),('horizontal','Horizontal'),('others','Others')], string='Pump Model Type.', store=True, readonly=True),
		'order_no': fields.char('Order No.', size=128,select=True),
		'order_category': fields.selection([('pump','Pump'),('spare','Spare')],'Purpose', required=True),
		'qty': fields.integer('Qty', required=True),
		'note': fields.text('Notes'),
		'delivery_date': fields.date('Delivery Date',required=True),
		
		'line_ids': fields.one2many('ch.amend.order.bom.details', 'header_id', "BOM Details"),
		'line_ids_a': fields.one2many('ch.amend.order.machineshop.details', 'header_id', "Machine Shop Details"),
		'line_ids_b': fields.one2many('ch.amend.order.bot.details', 'header_id', "BOT Details"),
		
		'flag_standard': fields.boolean('Non Standard'),
		'unit_price': fields.float('Unit Price',required=True),
		### Used for Schedule Purpose
		'moc_construction_id':fields.many2one('kg.moc.construction','MOC Construction Code',domain="[('active','=','t')]"),
		'moc_construction_name':fields.related('moc_construction_id','name', type='char', string='MOC Construction Name.', store=True, readonly=True),
		### Used for VO ###
		'rpm': fields.selection([('1450','1450'),('2900','2900')],'RPM'),
		'setting_height':fields.float('Setting Height (MM)'),
		'bed_length':fields.float('Bed Length(MM)'),
		'shaft_sealing': fields.selection([('g_p','G.P'),('m_s','M.S'),('f_s','F.S')],'Shaft Sealing'),
		'motor_power':fields.float('Motor Power'),
		'bush_bearing': fields.selection([('grease','Grease'),('cft_ext','CFT-EXT'),
			('cft_self','CFT-SELF'),('cut_less_rubber','Cut less Rubber')],'Bush Bearing'),
		'delivery_pipe_size':fields.float('Delivery Pipe Size(MM)'),
		'lubrication': fields.selection([('grease','Grease'),('cft_ext','CFT-EXT'),
			('cft_self','CFT-SELF'),('cut_less_rubber','Cut less Rubber')],'Lubrication'),
			
		'flag_load_bom': fields.boolean('Load BOM'),
		### Used for Dynamic Length Calculation
		'bp':fields.float('BP'),
		'shaft_ext':fields.float('Shaft Ext'),
		
		### Amendment Details ###
		'amend_mode': fields.selection([('from_wo','Created from WO'),('from_wo_amend','Created in Amend')],'Amendment Mode'),
		'amend_unit_price' : fields.float('Amend Unit Price'),
		
	}
	
	
	_defaults = {
	
		'delivery_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'flag_load_bom':False,
		
	}
	
	
	def default_get(self, cr, uid, fields, context=None):
		context.update({'amend_mode': 'from_wo_amend'})
		return context
	
	
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
		
	def onchange_pumpmodel_type(self, cr, uid, ids, pump_model_id):
		pump_model_type = False
		if pump_model_id:
			pump_model_rec = self.pool.get('kg.pumpmodel.master').browse(cr, uid, pump_model_id)
			if pump_model_rec.type == 'horizontal':
				pump_model_type = 'horizontal'
			elif pump_model_rec.type == 'vertical':
				pump_model_type = 'vertical'
			elif pump_model_rec.type == 'others':
				pump_model_type = 'others'
			else:
				raise osv.except_osv(_('Warning !'), _('Kindly specify type of the Pump Model in Master and then Proceed !!'))
		return {'value': {'pump_model_type': pump_model_type}}
		
	def onchange_moccons_name(self, cr, uid, ids, moc_construction_id):
		moc_construction_name = ''
		if moc_construction_id:
			if moc_construction_id:
				moc_cons_rec = self.pool.get('kg.moc.construction').browse(cr, uid, moc_construction_id)
				moc_construction_name = moc_cons_rec.name
			else:
				moc_construction_name = ''
		return {'value': {'moc_construction_name': moc_construction_name}}
		
	def onchange_bom_details(self, cr, uid, ids, pump_model_id, qty,moc_construction_id, order_category,flag_standard,
		rpm,setting_height,bed_length,shaft_sealing,motor_power,bush_bearing,delivery_pipe_size,lubrication,unit_price,delivery_date,note,
		bp,shaft_ext):
		
		
		bom_vals=[]
		machine_shop_vals=[]
		bot_vals=[]
		consu_vals=[]
		moc_obj = self.pool.get('kg.moc.master')
		if pump_model_id != False:
			
			pump_model_rec = self.pool.get('kg.pumpmodel.master').browse(cr, uid, pump_model_id)
			
			if pump_model_rec.type == 'horizontal':
				
				#### Loading Foundry Items
				
				order_bom_obj = self.pool.get('ch.order.bom.details')
				cr.execute(''' select bom.id,bom.header_id,bom.pattern_id,bom.pattern_name,bom.qty, bom.pos_no,pattern.pcs_weight, pattern.ci_weight,pattern.nonferous_weight
						from ch_bom_line as bom
						LEFT JOIN kg_pattern_master pattern on pattern.id = bom.pattern_id
						where bom.header_id = (select id from kg_bom where pump_model_id = %s and active='t') ''',[pump_model_id])
				bom_details = cr.dictfetchall()
				if order_category == 'pump' :
					for bom_details in bom_details:
						if order_category == 'pump' :
							applicable = True
						if order_category in ('spare','pump_spare'):
							applicable = False
							
						if qty == 0:
							bom_qty = bom_details['qty']
						if qty > 0:
							bom_qty = qty * bom_details['qty']
							
						### Loading MOC from MOC Construction
						
						if moc_construction_id != False:
							
							cr.execute(''' select pat_moc.moc_id
								from ch_mocwise_rate pat_moc
								LEFT JOIN kg_moc_construction const on const.code = pat_moc.code
								where pat_moc.header_id = %s and const.id = %s
								  ''',[bom_details['pattern_id'],moc_construction_id])
							const_moc_id = cr.fetchone()
							if const_moc_id != None:
								moc_id = const_moc_id[0]
							else:
								moc_id = False
						else:
							moc_id = False
						wgt = 0.00	
						if moc_id != False:
							moc_rec = moc_obj.browse(cr, uid, moc_id)
							if moc_rec.weight_type == 'ci':
								wgt =  bom_details['ci_weight']
							if moc_rec.weight_type == 'ss':
								wgt = bom_details['pcs_weight']
							if moc_rec.weight_type == 'non_ferrous':
								wgt = bom_details['nonferous_weight']
							
							
						bom_vals.append({
															
							'bom_id': bom_details['header_id'],
							'bom_line_id': bom_details['id'],
							'pattern_id': bom_details['pattern_id'],
							'pattern_name': bom_details['pattern_name'],						
							'weight': wgt or 0.00,								  
							'pos_no': bom_details['pos_no'],				  
							'qty' : bom_qty,				   
							'schedule_qty' : bom_qty,				  
							'production_qty' : 0,				   
							'flag_applicable' : applicable,
							'order_category':	order_category,
							'moc_id': moc_id,
							'flag_standard':flag_standard,
							'entry_mode':'auto'	  
							})
							
					#### Loading Machine Shop details
					
					bom_ms_obj = self.pool.get('ch.machineshop.details')
					cr.execute(''' select id,pos_no,ms_id,name,qty,header_id as bom_id
							from ch_machineshop_details
							where header_id = (select id from kg_bom where pump_model_id = %s and active='t') ''',[pump_model_id])
					bom_ms_details = cr.dictfetchall()
					for bom_ms_details in bom_ms_details:
						if qty == 0:
							bom_ms_qty = bom_ms_details['qty']
						if qty > 0:
							bom_ms_qty = qty * bom_ms_details['qty']
							
						if bom_ms_details['pos_no'] == None:
							pos_no = 0
						else:
							pos_no = bom_ms_details['pos_no']
							
						machine_shop_vals.append({
							
							'pos_no':pos_no,					
							'ms_line_id': bom_ms_details['id'],
							'bom_id': bom_ms_details['bom_id'],
							'ms_id': bom_ms_details['ms_id'],
							'name': bom_ms_details['name'],
							'qty': bom_ms_qty,
							'flag_applicable' : applicable,
							'flag_standard':flag_standard,
							'entry_mode':'auto'
									  
							})
							
					#### Loading BOT Details
					print "pump_model_id",pump_model_id
					bom_bot_obj = self.pool.get('ch.bot.details')
					cr.execute(''' select id,bot_id,qty,header_id as bom_id
							from ch_bot_details
							where header_id = (select id from kg_bom where pump_model_id = %s and  active='t') ''',[pump_model_id])
					bom_bot_details = cr.dictfetchall()
					for bom_bot_details in bom_bot_details:
						if qty == 0:
							bom_bot_qty = bom_bot_details['qty']
						if qty > 0:
							bom_bot_qty = qty * bom_bot_details['qty']
							
						print "bom_bot_details",bom_bot_details	
						bot_vals.append({
							
							'bot_line_id': bom_bot_details['id'],
							'bom_id': bom_bot_details['bom_id'],							
							'bot_id': bom_bot_details['bot_id'],
							'qty': bom_bot_qty,
							'flag_applicable' : applicable,
							'flag_standard':flag_standard,
							'entry_mode':'auto'	
									  
							})
							
						print "bot_vals---------------------------",bot_vals
							
			
			if pump_model_rec.type == 'vertical':
				
				bed_bom_obj = self.pool.get('ch.order.bom.details')
				
				
				if rpm != False:
					
					
					if bed_length > 0 and shaft_sealing != False and motor_power > 0 and bush_bearing != False and setting_height > 0 and delivery_pipe_size > 0 and lubrication != False:
						
						#### Load Foundry Items ####
						
						if bed_length <= 3000:
							limitation = 'upto_3000'
						if bed_length > 3000:
							limitation = 'above_3000'

						cr.execute('''
							-- Power Series --
							select bom.id,
							bom.header_id,
							bom.pattern_id,
							bom.pattern_name,
							bom.qty, 
							bom.pos_no,
							pattern.pcs_weight, 
							pattern.ci_weight,
							pattern.nonferous_weight

							from ch_bom_line as bom

							LEFT JOIN kg_pattern_master pattern on pattern.id = bom.pattern_id

							where bom.header_id = 
							(
							select id from kg_bom 
							where id = (select part_list_id from ch_power_series   
							where %s BETWEEN min AND max and %s < max
							and header_id = ( select vo_id from ch_vo_mapping
							where rpm = %s and header_id = %s)
							)
							and active='t'
							)
							
							union all
							
							-- Bed Assembly ----
							select bom.id,
							bom.header_id,
							bom.pattern_id,
							bom.pattern_name,
							bom.qty, 
							bom.pos_no,
							pattern.pcs_weight, 
							pattern.ci_weight,
							pattern.nonferous_weight

							from ch_bom_line as bom

							LEFT JOIN kg_pattern_master pattern on pattern.id = bom.pattern_id

							where bom.header_id = 
							(
							select id from kg_bom 
							where id = (select partlist_id from ch_bed_assembly 
							where limitation = %s and packing = %s and header_id = 

							( select vo_id from ch_vo_mapping
							where rpm = %s and header_id = %s))
							and active='t'
							) 
							
							union all


							--- Motor Assembly ---
							select bom.id,
							bom.header_id,
							bom.pattern_id,
							bom.pattern_name,
							bom.qty, 
							bom.pos_no,
							pattern.pcs_weight, 
							pattern.ci_weight,
							pattern.nonferous_weight

							from ch_bom_line as bom

							LEFT JOIN kg_pattern_master pattern on pattern.id = bom.pattern_id

							where bom.header_id = 
							(
							select id from kg_bom 
							where id = (select partlist_id from ch_motor_assembly 
							where value = %s and header_id = 

							( select vo_id from ch_vo_mapping
							where rpm = %s and header_id = %s ))
							and active='t'
							) 
							
							

							union all


							-- Column Pipe ------

							select bom.id,
							bom.header_id,
							bom.pattern_id,
							bom.pattern_name,
							bom.qty, 
							bom.pos_no,
							pattern.pcs_weight, 
							pattern.ci_weight,
							pattern.nonferous_weight

							from ch_bom_line as bom

							LEFT JOIN kg_pattern_master pattern on pattern.id = bom.pattern_id

							where bom.header_id = 
							(
							select id from kg_bom 
							where id = (select partlist_id from ch_columnpipe_assembly 
							where pipe_type = %s and star = (select star from ch_power_series 
							where %s BETWEEN min AND max and %s < max
							
							and header_id = ( select vo_id from ch_vo_mapping
							where rpm = %s and header_id = %s)
							
							) and header_id = 

							( select vo_id from ch_vo_mapping
							where rpm = %s and header_id = %s ))
							and active='t'
							)
							
					

							union all


							-- Delivery Pipe ------

							select bom.id,
							bom.header_id,
							bom.pattern_id,
							bom.pattern_name,
							bom.qty, 
							bom.pos_no,
							pattern.pcs_weight, 
							pattern.ci_weight,
							pattern.nonferous_weight

							from ch_bom_line as bom

							LEFT JOIN kg_pattern_master pattern on pattern.id = bom.pattern_id

							where bom.header_id = 
							(
							select id from kg_bom 
							where id = (select partlist_id from ch_deliverypipe_assembly 
							where size = %s and header_id = 

							( select vo_id from ch_vo_mapping
							where rpm = %s and header_id = %s))
							and active='t'
							) 
							
							

							union all


							-- Lubrication ------

							select bom.id,
							bom.header_id,
							bom.pattern_id,
							bom.pattern_name,
							bom.qty, 
							bom.pos_no,
							pattern.pcs_weight, 
							pattern.ci_weight,
							pattern.nonferous_weight

							from ch_bom_line as bom

							LEFT JOIN kg_pattern_master pattern on pattern.id = bom.pattern_id

							where bom.header_id = 
							(
							select id from kg_bom 
							where id = (select partlist_id from ch_lubricant 
							where type = %s and header_id = 

							( select vo_id from ch_vo_mapping
							where rpm = %s and header_id = %s))
							and active='t'
							) 
							
							
							  ''',[setting_height,setting_height,rpm,pump_model_id,limitation,shaft_sealing,rpm,pump_model_id,motor_power,rpm,pump_model_id,
							  bush_bearing,setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,delivery_pipe_size,
							  rpm,pump_model_id,lubrication,rpm,pump_model_id])
						vertical_foundry_details = cr.dictfetchall()
						if order_category == 'pump' :
							for vertical_foundry in vertical_foundry_details:
								if order_category == 'pump' :
									applicable = True
								if order_category in ('spare','pump_spare'):
									applicable = False
									
								### Loading MOC from MOC Construction
								
								if moc_construction_id != False:
									
									cr.execute(''' select pat_moc.moc_id
										from ch_mocwise_rate pat_moc
										LEFT JOIN kg_moc_construction const on const.code = pat_moc.code
										where pat_moc.header_id = %s and const.id = %s
										  ''',[vertical_foundry['pattern_id'],moc_construction_id])
									const_moc_id = cr.fetchone()
									if const_moc_id != None:
										moc_id = const_moc_id[0]
									else:
										moc_id = False
								else:
									moc_id = False
								wgt = 0.00	
								if moc_id != False:
									moc_rec = moc_obj.browse(cr, uid, moc_id)
									if moc_rec.weight_type == 'ci':
										wgt =  vertical_foundry['ci_weight']
									if moc_rec.weight_type == 'ss':
										wgt = vertical_foundry['pcs_weight']
									if moc_rec.weight_type == 'non_ferrous':
										wgt = vertical_foundry['nonferous_weight']
										
										
								### Dynamic Length Calculation ###
								length = 0.00
								a_value = 0.00
								a1_value = 0.00
								a2_value = 0.00
								star_value = 0
								pattern_rec = self.pool.get('kg.pattern.master').browse(cr, uid, vertical_foundry['pattern_id'])
								if pattern_rec.dynamic_length == True and pattern_rec.length_type != False:
									
									### Getting Alpha Values from Pump Model ###
									cr.execute(''' select alpha_type,alpha_value
											from ch_alpha_value
											where header_id = %s ''',[pump_model_id])
									alpha_val = cr.dictfetchall()
									
									if alpha_val:
										for alpha_item in alpha_val:
											
											if alpha_item['alpha_type'] == 'a':
												a_value = alpha_item['alpha_value']
											elif alpha_item['alpha_type'] == 'a1':
												a1_value = alpha_item['alpha_value']
											elif alpha_item['alpha_type'] == 'a2':
												a2_value = alpha_item['alpha_value']
											else:
												a_value = 0.00
												a1_value = 0.00
												a2_value = 0.00
									else:
										a_value = 0.00
										a1_value = 0.00
										a2_value = 0.00
									
									### Getting No of Star Support from VO ###
									
									cr.execute(''' select (case when star = 'nil' then '0' else star end)::int as star from ch_power_series 
										where %s BETWEEN min AND max and %s < max
										and header_id = ( select vo_id from ch_vo_mapping
										where rpm = %s and header_id = %s) ''',[setting_height,setting_height,rpm,pump_model_id])
									star_val = cr.fetchone()
									star_value = star_val[0]
									print "star_valuestar_valuestar_value",star_value
									### Getting ABOVE BP(H),BEND from pump model ###
									cr.execute(''' select h_value,b_value from ch_delivery_pipe
										where header_id = %s and delivery_size = %s ''',[pump_model_id,delivery_pipe_size])
									h_b_val = cr.dictfetchone()
									
									if h_b_val:
										h_value = h_b_val['h_value']
										b_value = h_b_val['b_value']
									else:
										h_value = 0.00
										b_value = 0.00
									
									if pattern_rec.length_type == 'single_column_pipe':
										
										if star_value == 0:
										 
											### Formula ###
											#3.5+BP+SETTING HEIGHT-A1
											###
											length = 3.5 + bp + setting_height - a1_value
										
									if pattern_rec.length_type == 'single_shaft':
										
										if star_value == 0:
										
											### Formula ###
											#SINGLE COL.PIPE+A2-3.5+SHAFT EXT
											###
											### Getting Single Column Pipe Length ###
											single_colpipe_length = 3.5 + bp + setting_height - a1_value
											length = single_colpipe_length + a2_value -3.5 + shaft_ext
										
									if pattern_rec.length_type == 'delivery_pipe':
										if star_value == 0.0:
											### Formula ###
											#ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-1.5
											###
											length = h_value + bp + setting_height - a_value - b_value - 1.5
											
										if star_value == 1:
											### Formula ###
											#(ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-3)/2
											###
											print "h_value",h_value
											print "bp",bp
											print "setting_height",setting_height
											print "a_value",a_value
											print "b_value",b_value
											length = (h_value + bp + setting_height - a_value - b_value - 3)/2
											
										if star_value > 1:
											### Formula ###
											#(ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-1.5)-(NO OF STAR SUPPORT*1.5)/NO OF STAR SUPPORT+1
											###
											length = (h_value+bp+setting_height-a_value-b_value-1.5)-(star_value*1.5)/1.5+1
												
									if pattern_rec.length_type == 'drive_column_pipe':
										
										if star_value == 1:
											### Formula ###
											#(3.5+bp+setting height-a1-no of star support)/2
											###
											length = (3.5+bp+setting_height-a1_value-star_value)/2
											
											
										if star_value > 1:
											### Formula ###
											#(3.5+bp+setting height-a1-no of star support-NO OF LINE COLUMN PIPE)/2
											###
											### Calculating Line Column Pipe ###
											### Formula = Standard Length ###
											line_column_pipe = vertical_foundry['qty']
											length = (3.5+bp+setting_height-a1_value-star_value-line_column_pipe)/2
											
											
									if pattern_rec.length_type == 'pump_column_pipe':
										
										if star_value == 1:
											### Formula ###
											#(3.5+bp+setting height-a1-no of star support)/2
											###
											length = (3.5+bp+setting_height-a1_value-star_value)/2
											
											
										if star_value > 1:
											### Formula ###
											#(3.5+bp+setting height-a1-no of star support-NO OF LINE COLUMN PIPE)/2
											###
											### Calculating Line Column Pipe ###
											### Formula = Standard Length ###
											line_column_pipe = vertical_foundry['qty']
											length = (3.5+bp+setting_height-a1_value-star_value-line_column_pipe)/2
											
											
									if pattern_rec.length_type == 'pump_shaft':
										
										if star_value == 1:
											### Formula ###
											#(STAR SUPPORT/2-1)+PUMP COLOUMN PIPE+A2
											###
											pump_column_pipe = (3.5+bp+setting_height-a1_value-star_value)/2
											length = (star_value/2-1)+pump_column_pipe+a2_value
											
											
										if star_value > 1:
											### Formula ###
											#(STAR SUPPORT/2-1)+PUMP COLOUMN PIPE+A2
											###
											line_column_pipe = vertical_foundry['qty']
											pump_column_pipe = (3.5+bp+setting_height-a1_value-star_value-line_column_pipe)/2
											length = (star_value/2-1)+pump_column_pipe+a2_value
											
									if pattern_rec.length_type == 'drive_shaft':
										
										if star_value == 1:
											### Formula ###
											#(STAR SUPPORT/2-1)+DRIVE COLOUMN PIPE-3.5+SHAFT EXT
											###
											drive_col_pipe = (3.5+bp+setting_height-a1_value-star_value)/2
											length = (star_value/2-1)+drive_col_pipe-3.5+shaft_ext
											
										if star_value > 1:
											### Formula ###
											#(STAR SUPPORT/2-1)+DRIVE COLOUMN PIPE-3.5+SHAFT EXT
											###
											line_column_pipe = vertical_foundry['qty']
											drive_col_pipe = (3.5+bp+setting_height-a1_value-star_value-line_column_pipe)/2
											length = (star_value/2-1)+drive_col_pipe-3.5+shaft_ext
								print "lengthlengthlength",length
								if length > 0:
									foundry_bom_qty = round(length,0)
								else:
									foundry_bom_qty = vertical_foundry['qty']
								print "qty",qty
								print "foundry_bom_qty",foundry_bom_qty
								if qty == 0:
									bom_qty = foundry_bom_qty
								if qty > 0:
									bom_qty = qty * foundry_bom_qty
								print "bom_qty",bom_qty
								bom_vals.append({
																	
									'bom_id': vertical_foundry['header_id'],
									'bom_line_id': vertical_foundry['id'],
									'pattern_id': vertical_foundry['pattern_id'],
									'pattern_name': vertical_foundry['pattern_name'],						
									'weight': wgt or 0.00,								  
									'pos_no': vertical_foundry['pos_no'],				  
									'qty' : bom_qty,				   
									'schedule_qty' : bom_qty,				  
									'production_qty' : 0,				   
									'flag_applicable' : applicable,
									'order_category':	order_category,
									'moc_id': moc_id,
									'flag_standard':flag_standard,
									'entry_mode':'auto'	  
						
									})
									
									
						#### Load Machine Shop Items ####
						
						bom_ms_obj = self.pool.get('ch.machineshop.details')
						cr.execute(''' 
									-- Power Series --
									select id,pos_no,ms_id,name,qty,header_id as bom_id
									from ch_machineshop_details
									where header_id = 
									(
									select id from kg_bom 
									where id = (select part_list_id from ch_power_series   
									where %s BETWEEN min AND max and %s < max
									and header_id = ( select vo_id from ch_vo_mapping
									where rpm = %s and header_id = %s)
									)
									and active='t'
									)
									
									union all
									
									-- Bed Assembly ----
									select id,pos_no,ms_id,name,qty,header_id as bom_id
									from ch_machineshop_details
									where header_id = 
									(
									select id from kg_bom 
									where id = (select partlist_id from ch_bed_assembly 
									where limitation = %s and packing = %s and header_id = 

									( select vo_id from ch_vo_mapping
									where rpm = %s and header_id = %s))
									and active='t'
									) 
									
								

									union all


									--- Motor Assembly ---
									select id,pos_no,ms_id,name,qty,header_id as bom_id
									from ch_machineshop_details
									where header_id =  
									(
									select id from kg_bom 
									where id = (select partlist_id from ch_motor_assembly 
									where value = %s and header_id = 

									( select vo_id from ch_vo_mapping
									where rpm = %s and header_id = %s ))
									and active='t'
									) 
									
									

									union all


									-- Column Pipe ------

									select id,pos_no,ms_id,name,qty,header_id as bom_id
									from ch_machineshop_details
									where header_id = 
									(
									select id from kg_bom 
									where id = (select partlist_id from ch_columnpipe_assembly 
									where pipe_type = %s and star = (select star from ch_power_series 
									where %s BETWEEN min AND max and %s < max
									
									and header_id = ( select vo_id from ch_vo_mapping
									where rpm = %s and header_id = %s)
									
									) and header_id = 

									( select vo_id from ch_vo_mapping
									where rpm = %s and header_id = %s))
									and active='t'
									)
									
							

									union all


									-- Delivery Pipe ------

									select id,pos_no,ms_id,name,qty,header_id as bom_id
									from ch_machineshop_details
									where header_id =  
									(
									select id from kg_bom 
									where id = (select partlist_id from ch_deliverypipe_assembly 
									where size = %s and header_id = 

									( select vo_id from ch_vo_mapping
									where rpm = %s and header_id = %s))
									and active='t'
									) 
									
									

									union all


									-- Lubrication ------

									select id,pos_no,ms_id,name,qty,header_id as bom_id
									from ch_machineshop_details
									where header_id = 
									(
									select id from kg_bom 
									where id = (select partlist_id from ch_lubricant 
									where type = %s and header_id = 

									( select vo_id from ch_vo_mapping
									where rpm = %s and header_id = %s ))
									and active='t'
									) 
									
									

							  ''',[setting_height,setting_height,rpm,pump_model_id,limitation,shaft_sealing,rpm,pump_model_id,motor_power,rpm,pump_model_id,
							  bush_bearing,setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,delivery_pipe_size,
							  rpm,pump_model_id,lubrication,rpm,pump_model_id])
						vertical_ms_details = cr.dictfetchall()
						for vertical_ms_details in vertical_ms_details:
							if qty == 0:
								vertical_ms_qty = vertical_ms_details['qty']
							if qty > 0:
								vertical_ms_qty = qty * vertical_ms_details['qty']
								
							if vertical_ms_details['pos_no'] == None:
								pos_no = 0
							else:
								pos_no = vertical_ms_details['pos_no']
								
							machine_shop_vals.append({
								
								'pos_no':pos_no,					
								'ms_line_id': vertical_ms_details['id'],
								'bom_id': vertical_ms_details['bom_id'],
								'ms_id': vertical_ms_details['ms_id'],
								'name': vertical_ms_details['name'],
								'qty': vertical_ms_qty,
								'flag_applicable' : applicable,
								'flag_standard':flag_standard,
								'entry_mode':'auto'
										  
								})
						
						
						#### Load BOT Items ####
						
						bom_bot_obj = self.pool.get('ch.machineshop.details')
						cr.execute(''' 
									-- Power Series --
									
									select id,bot_id,qty,header_id as bom_id
									from ch_bot_details
									where header_id =
									(
									select id from kg_bom 
									where id =(select part_list_id from ch_power_series   
									where %s BETWEEN min AND max and %s < max
									and header_id = ( select vo_id from ch_vo_mapping
									where rpm = %s and header_id = %s)
									)
									and active='t'
									)
									
									union all
									
									-- Bed Assembly ----
									select id,bot_id,qty,header_id as bom_id
									from ch_bot_details
									where header_id =
									(
									select id from kg_bom 
									where id = (select partlist_id from ch_bed_assembly 
									where limitation = %s and packing = %s and header_id = 

									( select vo_id from ch_vo_mapping
									where rpm = %s and header_id = %s))
									and active='t'
									) 
									
									union all


									--- Motor Assembly ---
									select id,bot_id,qty,header_id as bom_id
									from ch_bot_details
									where header_id =
									(
									select id from kg_bom 
									where id = (select partlist_id from ch_motor_assembly 
									where value = %s and header_id = 

									( select vo_id from ch_vo_mapping
									where rpm = %s and header_id = %s))
									and active='t'
									) 
									
									union all


									-- Column Pipe ------

									select id,bot_id,qty,header_id as bom_id
									from ch_bot_details
									where header_id =
									(
									select id from kg_bom 
									where id = (select partlist_id from ch_columnpipe_assembly 
									where pipe_type = %s and star = (select star from ch_power_series 
									where %s BETWEEN min AND max and %s < max
									and header_id = ( select vo_id from ch_vo_mapping
									where rpm = %s and header_id = %s)
									
									) and header_id = 

									( select vo_id from ch_vo_mapping
									where rpm = %s and header_id = %s))
									and active='t'
									)
									
									union all


									-- Delivery Pipe ------

									select id,bot_id,qty,header_id as bom_id
									from ch_bot_details
									where header_id =  
									(
									select id from kg_bom 
									where id = (select partlist_id from ch_deliverypipe_assembly 
									where size = %s and header_id = 

									( select vo_id from ch_vo_mapping
									where rpm = %s and header_id = %s))
									and active='t'
									) 
									
									union all


									-- Lubrication ------

									select id,bot_id,qty,header_id as bom_id
									from ch_bot_details
									where header_id =
									(
									select id from kg_bom 
									where id = (select partlist_id from ch_lubricant 
									where type = %s and header_id = 

									( select vo_id from ch_vo_mapping
									where rpm = %s and header_id = %s))
									and active='t'
									) 
									
									

							  ''',[setting_height,setting_height,rpm,pump_model_id,limitation,shaft_sealing,rpm,pump_model_id,motor_power,rpm,pump_model_id,
							  bush_bearing,setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,delivery_pipe_size,
							  rpm,pump_model_id,lubrication,rpm,pump_model_id])
						vertical_bot_details = cr.dictfetchall()
						
						for vertical_bot_details in vertical_bot_details:
							if qty == 0:
								vertical_bot_qty = vertical_bot_details['qty']
							if qty > 0:
								vertical_bot_qty = qty * vertical_bot_details['qty']
						
							bot_vals.append({
								
								'bot_line_id': vertical_bot_details['id'],
								'bom_id': vertical_bot_details['bom_id'],							
								'bot_id': vertical_bot_details['bot_id'],
								'qty': vertical_bot_qty,
								'flag_applicable' : applicable,
								'flag_standard':flag_standard,
								'entry_mode':'auto'	
										  
								})
							print "bot_vals---------------------------",bot_vals
				
		if order_category in ('spare','pump_spare'):
			header_qty = 1
		else:
			header_qty = qty
		

		return {'value': {'qty':header_qty,'line_ids': bom_vals,'line_ids_a':machine_shop_vals,'line_ids_b':bot_vals,'line_ids_c':consu_vals}}
	
	def entry_cancel(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.cancel_remark == False:
			raise osv.except_osv(_('Warning!'),
						_('Cancel Remarks is must !!'))
											
		cr.execute(''' select id from kg_production where order_line_id = %s and state = 'draft' ''',[entry.id])
		production_id = cr.fetchone()
		if production_id != None:
			if production_id[0] != None:
				raise osv.except_osv(_('Warning!'),
							_('Cannot be cancelled. Work Order is referred in Production !!'))
		else:
			self.write(cr, uid, ids, {'state': 'cancel'})
			cr.execute(''' update ch_work_order_details set state = 'cancel' where id = %s ''',[entry.id])
			cr.execute(''' update ch_order_bom_details set state = 'cancel' where header_id = %s ''',[entry.id])
		
		return True
		
		
	def _check_qty_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty == 0 or entry.qty < 0:
			return False
		return True
		
	def _check_unit_price(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.unit_price == 0.00 or entry.unit_price < 0:
			return False
		return True
		
	#~ def _check_line_items(self, cr, uid, ids, context=None):
		#~ entry = self.browse(cr,uid,ids[0])
		#~ if entry.state == 'draft' and entry.header_id.state == 'confirmed':
			#~ return False
		#~ return True
		
	def _check_line_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(''' select id from ch_work_order_details where pump_model_id = %s and
			order_category = %s and id != %s and header_id = %s ''',[entry.pump_model_id.id, 
			entry.order_category, entry.id, entry.header_id.id,])
		duplicate_id = cr.fetchone()
		if duplicate_id:
			return False
		return True
		
		
	def create(self, cr, uid, vals, context=None):
		header_rec = self.pool.get('kg.wo.amendment').browse(cr, uid,vals['header_id'])
		if header_rec.state == 'draft':
			res = super(ch_amend_work_order_details, self).create(cr, uid, vals, context=context)
		else:
			res = False
		return res
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_amend_work_order_details, self).write(cr, uid, ids, vals, context)
		
	
	
	_constraints = [		
			  
		(_check_qty_values, 'System not allow to save with zero and less than zero qty .!!',['Quantity']),
		(_check_unit_price, 'System not allow to save with zero and less than zero Unit Price .!!',['Unit Price']),
		#~ (_check_line_duplicates, 'Work Order Details are duplicate. Kindly check !! ', ['']),
		#~ (_check_line_items, 'Work Order Detail cannot be created after confirmation !! ', ['']),
	   
		
	   ]
	
ch_amend_work_order_details()


class ch_amend_order_bom_details(osv.osv):

	_name = "ch.amend.order.bom.details"
	_description = "BOM Details Amendment"
	
	_columns = {
	
		'header_id': fields.many2one('ch.amend.work.order.details', 'Work Order Detail', required=1, ondelete='cascade'),
		'wo_foundry_id': fields.many2one('ch.order.bom.details', 'WO Foundry Detail',),
		'pump_model_id': fields.related('header_id','pump_model_id', type='many2one',relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_qty': fields.related('header_id','qty', type='integer', string='Order Qty', store=True, readonly=True),
	
		'bom_id': fields.many2one('kg.bom','BOM'),
		'bom_line_id': fields.many2one('ch.bom.line','BOM Line'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No',domain="[('active','=','t')]"),
		'pattern_name': fields.char('Pattern Name'),
		'weight': fields.float('Weight(kgs)'),
		'pos_no': fields.related('bom_line_id','pos_no', type='integer', string='Position No', store=True),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		'qty': fields.integer('Qty'),
		'unit_price': fields.float('Unit Price'),
		'schedule_qty': fields.integer('Schedule Pending Qty'),
		'production_qty': fields.integer('Produced Qty'),
		'flag_applicable': fields.boolean('Is Applicable'),
		'add_spec': fields.text('Others Specification'),		   
		'flag_standard': fields.boolean('Non Standard'),
		'flag_pattern_check': fields.boolean('Is Pattern Check'),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
	
	}
	
	_defaults = {
		
		
		'flag_applicable': False,
		'flag_pattern_check': False,
		'entry_mode': 'manual'
		
	}
	
	
	def default_get(self, cr, uid, fields, context=None):
		context.update({'entry_mode': 'manual'})
		return context
		
	def onchange_pattern_details(self, cr, uid, ids, pattern_id, moc_id):
		wgt = 0.00
		pattern_obj = self.pool.get('kg.pattern.master')
		moc_obj = self.pool.get('kg.moc.master')
		pattern_rec = pattern_obj.browse(cr, uid, pattern_id)
		pattern_name = pattern_rec.pattern_name
		if moc_id:
			moc_rec = moc_obj.browse(cr, uid, moc_id)
			if moc_rec.weight_type == 'ci':
				wgt = pattern_rec.ci_weight
			if moc_rec.weight_type == 'ss':
				wgt = pattern_rec.pcs_weight
			if moc_rec.weight_type == 'non_ferrous':
				wgt = pattern_rec.nonferous_weight
			
		return {'value': {'pattern_name': pattern_name,'weight':wgt}}
	
	def create(self, cr, uid, vals, context=None):
		wgt = 0.00
		pattern_obj = self.pool.get('kg.pattern.master')
		moc_obj = self.pool.get('kg.moc.master')
		if vals.get('pattern_id') and vals.get('moc_id'):
			pattern_rec = pattern_obj.browse(cr, uid, vals.get('pattern_id'))
			pattern_name = pattern_rec.pattern_name
			moc_rec = moc_obj.browse(cr, uid, vals.get('moc_id'))
			if moc_rec.weight_type == 'ci':
				wgt = pattern_rec.ci_weight
			if moc_rec.weight_type == 'ss':
				wgt = pattern_rec.pcs_weight
			if moc_rec.weight_type == 'non_ferrous':
				wgt = pattern_rec.nonferous_weight
			vals.update({'pattern_name': pattern_name,'weight':wgt})
		return super(ch_amend_order_bom_details, self).create(cr, uid, vals, context=context)
	
	def write(self, cr, uid, ids, vals, context=None):
		wgt = 0.00
		pattern_obj = self.pool.get('kg.pattern.master')
		moc_obj = self.pool.get('kg.moc.master')
		if vals.get('pattern_id') and vals.get('moc_id'):
			pattern_rec = pattern_obj.browse(cr, uid, vals.get('pattern_id'))
			pattern_name = pattern_rec.pattern_name
			moc_rec = moc_obj.browse(cr, uid, vals.get('moc_id'))
			if moc_rec.weight_type == 'ci':
				wgt = pattern_rec.ci_weight
			if moc_rec.weight_type == 'ss':
				wgt = pattern_rec.pcs_weight
			if moc_rec.weight_type == 'non_ferrous':
				wgt = pattern_rec.nonferous_weight
			vals.update({'pattern_name': pattern_name,'weight':wgt})
		return super(ch_amend_order_bom_details, self).write(cr, uid, ids, vals, context)
		
		
	def _check_qty_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty == 0 or entry.qty < 0:
			return False
		return True
		
	_constraints = [		
			  
		(_check_qty_values, 'System not allow to save with zero and less than zero qty .!!',['Quantity']),
		
	   ]
	
ch_amend_order_bom_details()

class ch_amend_order_machineshop_details(osv.osv):

	_name = "ch.amend.order.machineshop.details"
	_description = "Order machineshop Details Amendment"
	
	
	_columns = {
	
		'header_id':fields.many2one('ch.amend.work.order.details', 'Work Order Detail', required=1, ondelete='cascade'),
		'wo_ms_id': fields.many2one('ch.order.machineshop.details', 'MS Line Id'),
		'ms_line_id':fields.many2one('ch.machineshop.details', 'Machine Shop Id'),
		'pos_no': fields.related('ms_line_id','pos_no', type='integer', string='Position No', store=True),
		'bom_id': fields.many2one('kg.bom','BOM'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', ondelete='cascade',required=True),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		'name':fields.char('Item Name', size=128),	  
		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
		'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'remarks':fields.text('Remarks'), 
		'flag_standard': fields.boolean('Non Standard'), 
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
	
	}  
	
	_defaults = {
		
		'entry_mode':'manual'
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		context.update({'entry_mode': 'manual'})
		return context
		
	def create(self, cr, uid, vals, context=None):
		return super(ch_amend_order_machineshop_details, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_amend_order_machineshop_details, self).write(cr, uid, ids, vals, context)   

ch_amend_order_machineshop_details()

class ch_amend_order_bot_details(osv.osv):
	
	_name = "ch.amend.order.bot.details"
	_description = "Order BOT Details Amendment"	
	
	_columns = {
	
		'header_id':fields.many2one('ch.amend.work.order.details', 'Work Order Detail', required=1, ondelete='cascade'),
		'wo_bot_id': fields.many2one('ch.order.bot.details', 'BOT Line Id'),
		'bot_line_id':fields.many2one('ch.bot.details', 'BOT Line Id'),
		'bot_id':fields.many2one('kg.machine.shop', 'Item Code',domain = [('type','=','bot')], ondelete='cascade',required=True),
		'item_name': fields.related('bot_id','name', type='char', size=128, string='Item Name', store=True, readonly=True),
		'bom_id': fields.many2one('kg.bom','BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
		'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'remarks':fields.text('Remarks'),
		'flag_standard': fields.boolean('Non Standard'),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
	
	}
	
	_defaults = {
		
		'entry_mode':'manual'
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		context.update({'entry_mode': 'manual'})
		return context
	
		
	def create(self, cr, uid, vals, context=None):
		return super(ch_amend_order_bot_details, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_amend_order_bot_details, self).write(cr, uid, ids, vals, context)   

ch_amend_order_bot_details()


	
	








