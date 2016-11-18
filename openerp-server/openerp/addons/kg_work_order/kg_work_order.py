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
   ('project','Project'),
   ('access','Accessories')
   
]


class kg_work_order(osv.osv):

	_name = "kg.work.order"
	_description = "Work Order Entry"
	_order = "entry_date desc"
	
	def _get_default_division(self, cr, uid, context=None):
		res = self.pool.get('kg.division.master').search(cr, uid, [('code','=','SAM'),('state','=','approved'), ('active','=','t')], context=context)
		return res and res[0] or False
		
	def _get_order_value(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		
		for entry in self.browse(cr, uid, ids, context=context):
			cr.execute(''' select sum(qty * unit_price) from ch_work_order_details where header_id = %s
			and  order_category = 'pump' ''',[entry.id])
			pump_wo_value = cr.fetchone()
			
			cr.execute(''' select sum(line.qty * header.unit_price) from ch_order_bom_details as line
				left join ch_work_order_details header on header.id = line.header_id where header.header_id = %s 
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
	
		### Header Details ####
		'name': fields.char('WO No.', size=128,select=True,required=True),
		'entry_date': fields.date('WO Date',required=True),
		'division_id': fields.many2one('kg.division.master','Division',readonly=True,required=True,domain="[('active','=','t')]"),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD'),('export','Export')],'Location', required=True),
		'note': fields.text('Notes'),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'WO Status', readonly=True),
		'line_ids': fields.one2many('ch.work.order.details', 'header_id', "Work Order Details"),
		'flag_cancel': fields.boolean('Cancellation Flag'),
		'order_priority': fields.selection(ORDER_PRIORITY,'Priority', required=True),
		'delivery_date': fields.date('Delivery Date',required=True),
		'order_value': fields.function(_get_order_value, string='WO Value', method=True, store=True, type='float'),
		'order_category': fields.selection(ORDER_CATEGORY,'Category'),
		'partner_id': fields.many2one('res.partner','Customer'),
		'progress_state': fields.selection([
		('mould_com','Moulding Completed'),
		('pour_com','Pouring Completed'),
		('casting_com','Casting Completed'),
		('moved_to_ms','Moved to MS'),
		('assembly','Assembly'),
		('qc','QC'),
		('rfd','RFD'),
		('dispatched','Dispatched'),
		],'Progress Status', readonly=True),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode', readonly=True),
		'version':fields.char('Version'),
		'flag_for_stock': fields.boolean('For Stock'),
		'invoice_flag': fields.boolean('For Invoice'),
		'offer_no': fields.char('Offer No'),
		
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_work_order', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',
		'order_priority': 'normal',
		'entry_mode': 'manual',
		'active': True,
		'division_id':_get_default_division,
		'delivery_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'version': '00',
		'flag_for_stock': False,
		'invoice_flag': False,
	}
	
	def onchange_priority(self, cr, uid, ids, order_category):
		if order_category in ('pump','project','pump_spare'):
			priority = 'normal'
		else:
			priority = 'emergency'
		return {'value': {'order_priority': priority}}

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
		
		
		
	def _check_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(''' select id from kg_work_order where entry_date = %s
			and division_id = %s and location = %s and id != %s and active = 't' and state = 'confirmed' ''',[str(entry.entry_date),entry.division_id.id,entry.location, ids[0]])
		duplicate_id = cr.fetchone()
		if duplicate_id:
			return False
		return True 
		
	def _check_lineitems(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.entry_mode == 'manual':
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
		res = True	
		if entry.entry_mode == 'manual':
			cr.execute(""" select name from kg_work_order where name  = '%s' """ %(entry.name))
			data = cr.dictfetchall()
				
			if len(data) > 1:
				res = False
			else:
				res = True	
		return res 
			
	
	_constraints = [		
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
		#(_check_duplicates, 'System not allow to do duplicate entry !!',['']),
		(_check_lineitems, 'System not allow to save with empty Work Order Details !!',['']),
		(_Validation, 'Special Character Not Allowed in Work Order No.', ['']),
		(_check_name, 'Work Order No. must be Unique', ['']),
	   
		
	   ]
	   
	   
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
		
	#~ def mail_test(self,cr,uid,ids,context=None):
	   #~ ### Mail Testing ###
		#~ scheduler_obj = self.pool.get('kg.scheduler')
		#~ body = '<html><body><p>The below mentioned Material Requisition is waiting for approval.</p></body></html>'
		#~ scheduler_obj.send_mail(cr, uid,ids,'sangeetha.subramaniam@kggroup.com',['sangeetha.subramaniam@kggroup.com'],
			#~ [],[],'Test',body,'')
		#~ ###
		#~ return True
	
	def entry_confirm(self,cr,uid,ids,context=None):
		
		schedule_obj = self.pool.get('kg.schedule')
		line_obj = self.pool.get('ch.work.order.details')
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			order_line_ids = []
			
			delivery_date = str(entry.delivery_date)
			delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d')
			if delivery_date < today:
				raise osv.except_osv(_('Warning!'),
							_('Delivery Date should not be less than current date for Order !!'))
							
			number = 1
			for item in entry.line_ids:
				
				### Work Order Number Generation in Line Details
				cr.execute(''' select to_char(%s, 'FMRN') ''',[number])	  
				roman = cr.fetchone()
				order_name = entry.name + '-' + str(roman[0])
				line_obj.write(cr, uid, item.id, {'order_no': order_name})
				number = number + 1
				
				order_line_ids.append(item.id)
				line_delivery_date = str(item.delivery_date)
				line_delivery_date = datetime.strptime(line_delivery_date, '%Y-%m-%d')
				if line_delivery_date < today:
					raise osv.except_osv(_('Warning!'),
							_('Delivery Date should not be less than current date for Pump Model %s !!')%(item.pump_model_id.name))
							
				
				if item.order_category != 'access':
					if not item.line_ids:
						raise osv.except_osv(_('Warning!'),
									_('Specify BOM Details for Pump Model %s !!')%(item.pump_model_id.name))
					
				else:
					cr.execute(''' select id from ch_order_bom_details where flag_applicable = 't' and header_id = %s ''',[item.id])	  
					bom_check_id = cr.fetchone()
					
					if item.order_category != 'access':
						if item.line_ids: 
							if bom_check_id == None:
								raise osv.except_osv(_('Warning!'),
										_('Kindly enable BOM Details for Pump Model %s!!')%(item.pump_model_id.name))
						
					
					cr.execute(''' select id from ch_order_bom_details where flag_applicable = 't' and moc_id is null and header_id = %s ''',[item.id])	   
					order_bom_id = cr.fetchone()
					if order_bom_id:
						if order_bom_id[0] != None:
							raise osv.except_osv(_('Warning!'),
								_('Specify MOC for Pump Model %s!!')%(item.pump_model_id.name))
							
				cr.execute(''' update ch_order_bom_details set state = 'confirmed' where header_id = %s and flag_applicable = 't' ''',[item.id])
				
				rem_qty = item.qty
				
				if item.order_category in 'pump':
				
					### Checking the Pump Stock ###
								
					### Checking in Stock Inward for Ready for MS ###
					
					cr.execute(""" select sum(available_qty) as stock_qty
						from ch_stock_inward_details  
						where pump_model_id = %s
						and foundry_stock_state = 'ready_for_ms' and available_qty > 0 and stock_type = 'pump' and stock_mode = 'manual' """%(item.pump_model_id.id))
					stock_inward_qty = cr.fetchone();
					
					if stock_inward_qty:
						if stock_inward_qty[0] != None:
							rem_qty =  item.qty - stock_inward_qty[0]
							
							if rem_qty <= 0:
								rem_qty = 0
								qc_qty = item.qty
							else:
								rem_qty = rem_qty
								qc_qty = stock_inward_qty[0]
							
							print "qc_qty",qc_qty
							
							### Order Priority ###
									
							if entry.order_category in ('pump','pump_spare','project'):
								if entry.order_priority == 'normal':
									priority = '6'
								if entry.order_priority == 'emergency':
									priority = '4'
							if entry.order_category == 'service':
								priority = '3'
							if entry.order_category == 'spare':
								priority = '5'
							
							print "priority",priority
							
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
								#~ 'schedule_id': entry.id,
								#~ 'schedule_date': entry.entry_date,
								'division_id': entry.division_id.id,
								'location' : entry.location,
								#~ 'schedule_line_id': schedule_item.id,
								'order_id': entry.id,
								'order_line_id': item.id,
								'qty' : qc_qty,
								'stock_qty': qc_qty,                   
								'allocated_qty':qc_qty,                 
								'state' : 'draft',
								'order_category':entry.order_category,
								'order_priority':priority,
								'pump_model_id' : item.pump_model_id.id,
								'moc_construction_id' : item.moc_construction_id.id,
								'stock_type': 'pump'
										
								}
								
							print "qc_vals",qc_vals
							
							qc_id = qc_obj.create(cr, uid, qc_vals)
							
							### Qty Updation in Stock Inward ###
							
							inward_line_obj = self.pool.get('ch.stock.inward.details')
							
							cr.execute(""" select id,available_qty
								from ch_stock_inward_details  
								where pump_model_id = %s
								and foundry_stock_state = 'ready_for_ms' and available_qty > 0 
								and stock_type = 'pump' and stock_mode = 'manual' """%(item.pump_model_id.id))
								
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
									print "stock_avail_qty",stock_avail_qty
			
								
				line_obj.write(cr, uid, item.id, {'pump_rem_qty':rem_qty})
				
				if entry.order_priority == 'normal' and entry.order_category in ('spare','service'):
				
					### Schedule Creation ###
					
					schedule_item_vals = {
													
						'name': '',
						'location' : entry.location,
						'order_priority': 'normal',
						'delivery_date': entry.delivery_date,
						'order_line_ids': [(6, 0, order_line_ids)],
						'state' : 'draft',
						'entry_mode' : 'auto',				   
					}
					
					schedule_id = schedule_obj.create(cr, uid, schedule_item_vals)
					
					### Schedule Line Item Creation ###
					
					if item.order_category == 'pump':
					
						schedule_obj.update_line_items(cr, uid, [schedule_id],rem_qty)
					else:
						schedule_obj.update_line_items(cr, uid, [schedule_id],0)
					
					### Schedule Confirmation ###
					
					schedule_obj.entry_confirm(cr, uid, [schedule_id])
					
				if entry.order_priority == 'emergency' and entry.order_category in ('pump','spare','pump_spare','service'):
					
					### Schedule Creation ###
					
					schedule_item_vals = {
													
						'name': '',
						'location' : entry.location,
						'order_priority': 'emergency',
						'delivery_date': entry.delivery_date,
						'order_line_ids': [(6, 0, order_line_ids)],
						'state' : 'draft',			   
						'entry_mode' : 'auto',			   
					}
					
					schedule_id = schedule_obj.create(cr, uid, schedule_item_vals)
					
					### Schedule Line Item Creation ###
					
					if item.order_category == 'pump':
					
						schedule_obj.update_line_items(cr, uid, [schedule_id],rem_qty)
					else:
						schedule_obj.update_line_items(cr, uid, [schedule_id],0)
					
					### Schedule Confirmation ###
					
					schedule_obj.entry_confirm(cr, uid, [schedule_id])
					
				if entry.order_priority == 'emergency' and entry.order_category in ('project'):
					
					### Schedule Creation ###
					
					schedule_item_vals = {
													
						'name': '',
						'location' : entry.location,
						'order_priority': 'emergency',
						'delivery_date': entry.delivery_date,
						'order_line_ids': [(6, 0, order_line_ids)],
						'state' : 'draft',
						'entry_mode' : 'auto',				   
					}
					
					schedule_id = schedule_obj.create(cr, uid, schedule_item_vals)
					
					### Schedule Line Item Creation ###
					
					if item.order_category == 'pump':
					
						schedule_obj.update_line_items(cr, uid, [schedule_id],rem_qty)
					else:
						schedule_obj.update_line_items(cr, uid, [schedule_id],0)
				
				
			cr.execute(''' select sum(unit_price) from ch_work_order_details where header_id = %s ''',[entry.id])	   
			order_value = cr.fetchone()
			self.write(cr, uid, ids, {'order_value':order_value[0],'state': 'confirmed','flag_cancel':1,'confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			cr.execute(''' update ch_work_order_details set state = 'confirmed', flag_cancel='t', schedule_status = 'allow' where header_id = %s ''',[ids[0]])
		else:
			pass
		return True
		
	def entry_cancel(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.cancel_remark == False:
			raise osv.except_osv(_('Warning!'),
						_('Cancel Remarks is must !!'))
		
		for line_item in entry.line_ids:				

			cr.execute(''' select id from kg_production where order_line_id = %s and state = 'draft' ''',[line_item.id])
			production_id = cr.fetchone()
			if production_id != None:
				if production_id[0] != None:
					raise osv.except_osv(_('Warning!'),
								_('Cannot be cancelled. Work Order is referred in Production !!'))
								
			cr.execute(''' update ch_order_bom_details set state = 'cancel' where header_id = %s ''',[line_item.id])
						
		else:
			self.write(cr, uid, ids, {'state': 'cancel','flag_cancel':0,'cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			cr.execute(''' update ch_work_order_details set state = 'cancel',flag_cancel='f' where header_id = %s ''',[entry.id])			
		
		return True
		
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_work_order = str(rec.name)		
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
		
		url = 'http://192.168.1.7/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&wo_no='+rec_work_order	
		
		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
		
		
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
		return super(kg_work_order, self).write(cr, uid, ids, vals, context)
		
kg_work_order()


class ch_work_order_details(osv.osv):

	_name = "ch.work.order.details"
	_description = "Work Order Details"
	_rec_name = 'order_no'
	
	_columns = {
	
		### Order Details ####
		'header_id':fields.many2one('kg.work.order', 'Work Order', required=1, ondelete='cascade'),
		'order_date': fields.related('header_id','entry_date', type='date', string='Date', store=True, readonly=True),
		'order_priority': fields.related('header_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		'order_ref_no': fields.related('header_id','name', type='char', string='Work Order No.', store=True, readonly=True),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True,domain="[('active','=','t')]"),
		'pump_model_type':fields.selection([('vertical','Vertical'),('horizontal','Horizontal'),('others','Others')], 'Type',required=True),
		'order_no': fields.char('Order No.', size=128,select=True),
		'order_category': fields.selection([('pump','Pump'),('spare','Spare'),('access','Accessories')],'Purpose', required=True),
		'qty': fields.integer('Qty', required=True),
		'pump_rem_qty': fields.integer('Pump Remaining Qty'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'note': fields.text('Notes'),
		'remarks': fields.text('Approve/Reject Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'delivery_date': fields.date('Delivery Date'),
		'line_ids': fields.one2many('ch.order.bom.details', 'header_id', "BOM Details"),
		'line_ids_a': fields.one2many('ch.order.machineshop.details', 'header_id', "Machine Shop Details"),
		'line_ids_b': fields.one2many('ch.order.bot.details', 'header_id', "BOT Details"),
		'line_ids_c': fields.one2many('ch.order.consu.details', 'header_id', "Consumale Details"),
		'flag_cancel': fields.boolean('Cancellation Flag'),
		'flag_standard': fields.boolean('Non Standard'),
		'unit_price': fields.float('Unit Price',required=True),
		### Used for Schedule Purpose
		'schedule_status':fields.selection([('allow','Allow to Schedule'),('not_allow','Not Allow to Schedule'),('completed','Schedule Completed')],'Schedule Status', readonly=True),
		'moc_construction_id':fields.many2one('kg.moc.construction','MOC Construction Code',domain="[('active','=','t')]"),
		'moc_construction_name':fields.related('moc_construction_id','name', type='char', string='MOC Construction Name.', store=True, readonly=True),
		### Used for VO ###
		'rpm': fields.selection([('1450','1450'),('2900','2900')],'RPM', required=True),
		'setting_height':fields.float('Setting Height (MM)',required=True),
		'bed_length':fields.float('Bed Length(MM)',required=True),
		'shaft_sealing': fields.selection([('g_p','Gland Packing'),('m_s','Mechanical Seal'),('f_s','Felt Seal')],'Shaft Sealing',required=True),
		#~ 'motor_power':fields.float('Motor Power',required=True),
		'motor_power': fields.selection([('90','90'),('100','100'),('112','112'),('132','132'),('160','160'),('180','180'),('200','200'),('225','225'),
				('250','250'),('280','280'),('315','315'),('315_l','315L')],'Motor Frame size',required=True),
				
		'm_power': fields.float('Motor power in KW'),
		
		#~ 'bush_bearing': fields.selection([('grease','Grease'),('cft_ext','CFT-EXT'),
			#~ ('cft_self','CFT-SELF'),('cut_less_rubber','Cut less Rubber')],'Bush Bearing',required=True),
			
		'bush_bearing': fields.selection([('grease','Grease'),('cft_self','CFT'),('cut_less_rubber','Cut less Rubber')],'Bush Bearing',required=True),
		#~ 'delivery_pipe_size':fields.float('Delivery Pipe Size(MM)',required=True),
		'delivery_pipe_size': fields.selection([('32','32'),('40','40'),('50','50'),('65','65'),('80','80'),('100','100'),('125','125'),('150','150'),('200','200'),('250','250'),('300','300')],'Delivery Pipe Size(MM)',required=True),
		
		'lubrication': fields.selection([('grease','Grease'),('cft_ext','External'),
			('cft_self','Self'),('cut_less_rubber','External Under Pressure')],'Bush bearing Lubrication',required=True),
			
		'flag_load_bom': fields.boolean('Load BOM'),
		### Used for Dynamic Length Calculation
		'bp':fields.float('BP',required=True),
		'shaft_ext':fields.float('Shaft Ext',required=True),
		'flag_for_stock': fields.boolean('For Stock'),
		### Offer Details ###
		'pump_offer_line_id': fields.integer('Pump Offer'),
		'line_ids_d': fields.one2many('ch.wo.accessories', 'header_id', "Accessories"),
		
	}
	
	
	_defaults = {
	
		'state': 'draft',
		'schedule_status': 'allow',
		'delivery_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'flag_load_bom':False,
		'flag_for_stock':False
		
	}
	
	
	def default_get(self, cr, uid, fields, context=None):
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
		rpm,setting_height,shaft_sealing,motor_power,bush_bearing,delivery_pipe_size,lubrication,unit_price,delivery_date,note,pump_model_type):
		
		
		bom_vals=[]
		machine_shop_vals=[]
		bot_vals=[]
		consu_vals=[]
		moc_obj = self.pool.get('kg.moc.master')
		if pump_model_id != False:
			
			pump_model_rec = self.pool.get('kg.pumpmodel.master').browse(cr, uid, pump_model_id)
				
			#### Loading Foundry Items
			
			order_bom_obj = self.pool.get('ch.order.bom.details')
			cr.execute(''' select bom.id,bom.header_id,bom.pattern_id,bom.pattern_name,bom.qty, bom.pos_no,bom.position_id,pattern.pcs_weight, pattern.ci_weight,pattern.nonferous_weight
					from ch_bom_line as bom
					LEFT JOIN kg_pattern_master pattern on pattern.id = bom.pattern_id
					where bom.header_id = (select id from kg_bom where pump_model_id = %s and active='t') ''',[pump_model_id])
			bom_details = cr.dictfetchall()
			
			
			for bom_details in bom_details:
				if bom_details['position_id'] == None:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Configure Position No. in Foundry Items for respective Pump Bom and proceed further !!'))
				
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
						LEFT JOIN kg_moc_construction const on const.id = pat_moc.code
						where pat_moc.header_id = %s and const.id = %s ''',[bom_details['pattern_id'],moc_construction_id])
					const_moc_id = cr.fetchone()
					if const_moc_id != None:
						moc_id = const_moc_id[0]
					else:
						moc_id = False
				else:
					moc_id = False
				wgt = 0.00	
				if moc_id != False:
					print "moc_id",moc_id
					moc_rec = moc_obj.browse(cr, uid, moc_id)
					print "moc_rec",moc_rec
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
					'position_id': bom_details['position_id'],				  
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
			cr.execute(''' select id,pos_no,position_id,ms_id,name,qty,header_id as bom_id
					from ch_machineshop_details
					where header_id = (select id from kg_bom where pump_model_id = %s and active='t') ''',[pump_model_id])
			bom_ms_details = cr.dictfetchall()
			for bom_ms_details in bom_ms_details:
				if bom_ms_details['position_id'] == None:
					raise osv.except_osv(_('Warning!'),
					_('Kindly Configure Position No. in MS Items for respective Pump Bom and proceed further !!'))
				if qty == 0:
					bom_ms_qty = bom_ms_details['qty']
				if qty > 0:
					bom_ms_qty = qty * bom_ms_details['qty']
					
				if bom_ms_details['pos_no'] == None:
					pos_no = 0
				else:
					pos_no = bom_ms_details['pos_no']
					
				machine_shop_vals.append({
					
					'pos_no': bom_ms_details['pos_no'],
					'position_id': bom_ms_details['position_id'],
					'bom_id': bom_ms_details['bom_id'],
					'ms_id': bom_ms_details['ms_id'],
					'name': bom_ms_details['name'],
					'qty': bom_ms_qty,
					'flag_applicable' : applicable,
					'flag_standard':flag_standard,
					'entry_mode':'auto',
					'order_category':	order_category,
							  
					})
					
			#### Loading BOT Details
			
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
					
					
				bot_vals.append({
					
					'bot_line_id': bom_bot_details['id'],
					'bom_id': bom_bot_details['bom_id'],							
					'bot_id': bom_bot_details['bot_id'],
					'qty': bom_bot_qty,
					'flag_applicable' : applicable,
					'flag_standard':flag_standard,
					'entry_mode':'auto',
					'order_category':order_category,
							  
					})
							
				
			bed_bom_obj = self.pool.get('ch.order.bom.details')
			
			
			if rpm != False:
				
				
				if shaft_sealing != False and motor_power != False and bush_bearing != False and setting_height > 0 and delivery_pipe_size != False and lubrication != False:
					
					#### Load Foundry Items ####
					
					if setting_height < 3000:
						limitation = 'upto_3000'
					if setting_height >= 3000:
						limitation = 'above_3000'

					cr.execute('''
					
						
						-- Bed Assembly ----
						select bom.id,
						bom.header_id,
						bom.pattern_id,
						bom.pattern_name,
						bom.qty, 
						bom.pos_no,
						bom.position_id,
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
						bom.position_id,
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
						bom.position_id,
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
						where %s BETWEEN min AND max and %s <= max
						
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
						bom.position_id,
						pattern.pcs_weight, 
						pattern.ci_weight,
						pattern.nonferous_weight

						from ch_bom_line as bom

						LEFT JOIN kg_pattern_master pattern on pattern.id = bom.pattern_id

						where bom.header_id = 
						(
						select id from kg_bom 
						where id = (select partlist_id from ch_deliverypipe_assembly 
						where size = %s and star = (select star from ch_power_series 
						where %s BETWEEN min AND max and %s <= max
						
						and header_id = ( select vo_id from ch_vo_mapping
						where rpm = %s and header_id = %s)
						
						) and header_id = 

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
						bom.position_id,
						pattern.pcs_weight, 
						pattern.ci_weight,
						pattern.nonferous_weight

						from ch_bom_line as bom

						LEFT JOIN kg_pattern_master pattern on pattern.id = bom.pattern_id

						where bom.header_id = 
						(
						select id from kg_bom 
						where id = (select partlist_id from ch_lubricant 
						where type = %s and star = (select star from ch_power_series 
						where %s BETWEEN min AND max and %s <= max
						
						and header_id = ( select vo_id from ch_vo_mapping
						where rpm = %s and header_id = %s)
						
						) and header_id = 

						( select vo_id from ch_vo_mapping
						where rpm = %s and header_id = %s))
						and active='t'
						) 
						
						
						  ''',[limitation,shaft_sealing,rpm,pump_model_id,motor_power,rpm,pump_model_id,
						  bush_bearing,setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,delivery_pipe_size,
						  setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,lubrication,setting_height,setting_height,
						  rpm,pump_model_id,rpm,pump_model_id])
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
									LEFT JOIN kg_moc_construction const on const.id = pat_moc.code
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
									
							if qty == 0:
								bom_qty = vertical_foundry['qty']
							if qty > 0:
								bom_qty = qty * vertical_foundry['qty']
							
							
							if vertical_foundry['position_id'] == None:
								raise osv.except_osv(_('Warning!'),
								_('Kindly Configure Position No. in Foundry Items for respective Pump Bom and proceed further !!'))
							
							
							bom_vals.append({
																
								'bom_id': vertical_foundry['header_id'],
								'bom_line_id': vertical_foundry['id'],
								'pattern_id': vertical_foundry['pattern_id'],
								'pattern_name': vertical_foundry['pattern_name'],						
								'weight': wgt or 0.00,								  
								'pos_no': vertical_foundry['pos_no'],
								'position_id': vertical_foundry['position_id'],			  
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
								
								-- Bed Assembly ----
								select id,pos_no,position_id,ms_id,name,qty,header_id as bom_id
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
								select id,pos_no,position_id,ms_id,name,qty,header_id as bom_id
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

								select id,pos_no,position_id,ms_id,name,qty,header_id as bom_id
								from ch_machineshop_details
								where header_id = 
								(
								select id from kg_bom 
								where id = (select partlist_id from ch_columnpipe_assembly 
								where pipe_type = %s and star = (select star from ch_power_series 
								where %s BETWEEN min AND max and %s <= max
								
								and header_id = ( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s)
								
								) and header_id = 

								( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s))
								and active='t'
								)
								
						

								union all


								-- Delivery Pipe ------

								select id,pos_no,position_id,ms_id,name,qty,header_id as bom_id
								from ch_machineshop_details
								where header_id =  
								(
								select id from kg_bom 
								where id = (select partlist_id from ch_deliverypipe_assembly 
								where size = %s and star = (select star from ch_power_series 
								where %s BETWEEN min AND max and %s <= max
								
								and header_id = ( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s)
								
								) and header_id = 

								( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s))
								and active='t'
								) 
								
								

								union all


								-- Lubrication ------

								select id,pos_no,position_id,ms_id,name,qty,header_id as bom_id
								from ch_machineshop_details
								where header_id = 
								(
								select id from kg_bom 
								where id = (select partlist_id from ch_lubricant 
								where type = %s and star = (select star from ch_power_series 
								where %s BETWEEN min AND max and %s <= max
								
								and header_id = ( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s)
								
								) and header_id = 

								( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s ))
								and active='t'
								) 
								
								

						  ''',[limitation,shaft_sealing,rpm,pump_model_id,motor_power,rpm,pump_model_id,
						  bush_bearing,setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,delivery_pipe_size,
						  setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,lubrication,setting_height,setting_height,
						  rpm,pump_model_id,rpm,pump_model_id])
					vertical_ms_details = cr.dictfetchall()
					for vertical_ms_details in vertical_ms_details:
						
							
						if vertical_ms_details['pos_no'] == None:
							pos_no = 0
						else:
							pos_no = vertical_ms_details['pos_no']
							
							
						### Dynamic Length Calculation ###
						length = 0.00
						a_value = 0.00
						a1_value = 0.00
						a2_value = 0.00
						star_value = 0
						ms_rec = self.pool.get('kg.machine.shop').browse(cr, uid, vertical_ms_details['ms_id'])
						if ms_rec.dynamic_length == True and ms_rec.length_type != False:
							
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
								where %s BETWEEN min AND max and %s <= max
								and header_id = ( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s) ''',[setting_height,setting_height,rpm,pump_model_id])
							star_val = cr.fetchone()
							star_value = star_val[0]
							
							
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
							
							if ms_rec.length_type == 'single_column_pipe':
								
								if star_value == 0:
								 
									### Formula ###
									#3.5+BP+SETTING HEIGHT-A1
									###
									length = 3.5 + bp + setting_height - a1_value
									
							### Getting BP and Shaft Ext from VO Master ###
							cr.execute('''
				
								 (select bp,shaft_ext from ch_bed_assembly 
								where limitation = %s and packing = %s and header_id = 

								( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s))
								
								
								  ''',[limitation,shaft_sealing,rpm,pump_model_id])
							bed_ass_details = cr.dictfetchone()
							if not bed_ass_details:
								bp = 0
								shaft_ext = 0
							else:
								if bed_ass_details['bp'] == None:
									bp = 0
								else:
									bp = bed_ass_details['bp']
								if bed_ass_details['shaft_ext'] == None:
									shaft_ext = 0
								else:
									shaft_ext = bed_ass_details['shaft_ext']
							
							### Getting Star Value ###
							cr.execute('''
							
								select star,lcp,ls from kg_vo_master 
								where id in 

								( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s)
								
								
								  ''',[rpm,pump_model_id])
							vo_star_value = cr.dictfetchone()
							
								
							if ms_rec.length_type == 'single_shaft':
								
								if star_value == 0:
								
									### Formula ###
									#SINGLE COL.PIPE+A2-3.5+SHAFT EXT
									###
									### Getting Single Column Pipe Length ###
									single_colpipe_length = 3.5 + bp + setting_height - a1_value
									length = single_colpipe_length + a2_value -3.5 + shaft_ext
								
							if ms_rec.length_type == 'delivery_pipe':
								if star_value == 0.0:
									### Formula ###
									#ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-1.5
									###
									length = h_value + bp + setting_height - a_value - b_value - 1.5
									
								if star_value == 1:
									### Formula ###
									#(ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-3)/2
									###
									length = (h_value + bp + setting_height - a_value - b_value - 3)/2
									
								if star_value > 1:
									### Formula ###
									#(ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-1.5)-(NO OF STAR SUPPORT*1.5)/NO OF STAR SUPPORT+1
									###
									length = ((h_value+bp+setting_height-a_value-b_value-1.5)-(star_value*1.5))/(star_value+1)
									
							if ms_rec.length_type == 'drive_column_pipe':
								
								if star_value == 1:
									### Formula ###
									#(3.5+bp+setting height-a1-no of star support)/2
									###
									length = (3.5+bp+setting_height-a1_value-vo_star_value['star'])/2
									
									
								if star_value > 1:
									### Formula ###
									#(3.5+bp+setting height-a1-(No. of star support * star support value)-((No. Of star support-1) * LINE COLUMN PIPE value))/2
									###
									### Calculating Line Column Pipe ###
									### Formula = Standard Length ###
									line_column_pipe = vo_star_value['lcp']
									length = (3.5+bp+setting_height-a1_value-(star_value * vo_star_value['star'])-((star_value-1)*line_column_pipe))/2
									
									
							if ms_rec.length_type == 'pump_column_pipe':
								
								if star_value == 1:
									### Formula ###
									#(3.5+bp+setting height-a1-no of star support)/2
									###
									length = (3.5+bp+setting_height-a1_value-vo_star_value['star'])/2
									
									
								if star_value > 1:
									### Formula ###
									#(3.5+bp+setting height-a1-no of star support-NO OF LINE COLUMN PIPE)/2
									###
									### Calculating Line Column Pipe ###
									### Formula = Standard Length ###
									line_column_pipe = vo_star_value['lcp']
									length = (3.5+bp+setting_height-a1_value-(star_value * vo_star_value['star'])-((star_value-1)*line_column_pipe))/2
									
									
							if ms_rec.length_type == 'pump_shaft':
								
								if star_value == 1:
									### Formula ###
									#(STAR SUPPORT/2-1)+PUMP COLOUMN PIPE+A2
									###
									pump_column_pipe = (3.5+bp+setting_height-a1_value-vo_star_value['star'])/2
									length = (star_value/2-1)+pump_column_pipe+a2_value
									
									
								if star_value > 1:
									### Formula ###
									#(STAR SUPPORT/2-1)+PUMP COLOUMN PIPE+A2
									###
									line_column_pipe = vo_star_value['lcp']
									pump_column_pipe = (3.5+bp+setting_height-a1_value-(star_value * vo_star_value['star'])-((star_value-1)*line_column_pipe))/2
									length = ((vo_star_value['star']/2)-1)+pump_column_pipe+a2_value
									
							if ms_rec.length_type == 'drive_shaft':
								
								if star_value == 1:
									### Formula ###
									#(STAR SUPPORT/2-1)+DRIVE COLOUMN PIPE-3.5+SHAFT EXT
									###
									drive_col_pipe = (3.5+bp+setting_height-a1_value-vo_star_value['star'])/2
									length = (star_value/2-1)+drive_col_pipe-3.5+shaft_ext
									
								if star_value > 1:
									### Formula ###
									#(STAR SUPPORT/2-1)+DRIVE COLOUMN PIPE-3.5+SHAFT EXT
									###
									line_column_pipe = vo_star_value['lcp']
									drive_col_pipe = (3.5+bp+setting_height-a1_value-(star_value * vo_star_value['star'])-((star_value-1)*line_column_pipe))/2
									length = ((vo_star_value['star']/2)-1)+drive_col_pipe-3.5+shaft_ext
						
						print "length---------------------------->>>>",length
						if length > 0:
							ms_bom_qty = round(length,0)
						else:
							ms_bom_qty = 0
						print "ms_bom_qty---------------------------->>>>",ms_bom_qty
						print "qty---------------------------->>>>",qty
						if qty == 0:
							vertical_ms_qty = vertical_ms_details['qty']
						if qty > 0:
							vertical_ms_qty = qty * ms_bom_qty
							
						print "vertical_ms_qty---------------------------->>>>",vertical_ms_qty
						
						if vertical_ms_details['position_id'] == None:
							raise osv.except_osv(_('Warning!'),
							_('Kindly Configure Position No. in MS Items for respective Pump Bom and proceed further !!'))
							
						machine_shop_vals.append({
							
							'pos_no':pos_no,
							'position_id':vertical_ms_details['position_id'],						
							'ms_line_id': vertical_ms_details['id'],
							'bom_id': vertical_ms_details['bom_id'],
							'ms_id': vertical_ms_details['ms_id'],
							'name': vertical_ms_details['name'],
							'qty': qty * vertical_ms_details['qty'],
							'length': vertical_ms_qty,
							'flag_applicable' : applicable,
							'flag_standard':flag_standard,
							'entry_mode':'auto',
							'order_category':	order_category,
									  
							})
					
					
					#### Load BOT Items ####
					
					bom_bot_obj = self.pool.get('ch.machineshop.details')
					cr.execute(''' 
								
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
								where %s BETWEEN min AND max and %s <= max
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
								where size = %s and star = (select star from ch_power_series 
								where %s BETWEEN min AND max and %s <= max
								
								and header_id = ( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s)
								
								)and header_id = 

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
								where type = %s and star = (select star from ch_power_series 
								where %s BETWEEN min AND max and %s <= max
								
								and header_id = ( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s)
								
								)and header_id = 

								( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s))
								and active='t'
								) 
								
								

						  ''',[limitation,shaft_sealing,rpm,pump_model_id,motor_power,rpm,pump_model_id,
						  bush_bearing,setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,delivery_pipe_size,
						  setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,lubrication,setting_height,setting_height,
						  rpm,pump_model_id,rpm,pump_model_id])
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
							'entry_mode':'auto',
							'order_category':	order_category,
									  
							})
				
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
		if entry.header_id.entry_mode == 'manual':
			if entry.unit_price == 0.00 or entry.unit_price < 0:
				return False
		return True
		
	def _check_line_items(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft' and entry.header_id.state == 'confirmed':
			return False
		return True
		
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
		header_rec = self.pool.get('kg.work.order').browse(cr, uid,vals['header_id'])
		#~ if header_rec.state == 'draft':
		res = super(ch_work_order_details, self).create(cr, uid, vals, context=context)
		#~ else:
			#~ res = False
		return res
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_work_order_details, self).write(cr, uid, ids, vals, context)
		
		
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []
		for rec in self.browse(cr,uid,ids): 
			if rec.state != 'draft' and rec.state != False:
				raise osv.except_osv(_('Warning!'),
						_('You can not delete Work Order Details after confirmation !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	
	
	_constraints = [		
			  
		(_check_qty_values, 'System not allow to save with zero and less than zero qty .!!',['Quantity']),
		(_check_unit_price, 'System not allow to save with zero and less than zero Unit Price .!!',['Unit Price']),
		#~ (_check_line_duplicates, 'Work Order Details are duplicate. Kindly check !! ', ['']),
		(_check_line_items, 'Work Order Detail cannot be created after confirmation !! ', ['']),
	   
		
	   ]
	
ch_work_order_details()


class ch_order_bom_details(osv.osv):

	_name = "ch.order.bom.details"
	_description = "BOM Details"
	
	_columns = {
	
		'header_id':fields.many2one('ch.work.order.details', 'Work Order Detail', required=1, ondelete='cascade'),
		'order_id': fields.related('header_id','header_id', type='many2one',relation='kg.work.order', string='Order No', store=True, readonly=True),
		'order_date': fields.related('header_id','order_date', type='date', string='Order Date', store=True, readonly=True),
		'delivery_date': fields.related('header_id','delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'order_ref_no': fields.related('header_id','order_ref_no', type='char', string='Work Order No', store=True, readonly=True),
		'pump_model_id': fields.related('header_id','pump_model_id', type='many2one',relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_qty': fields.related('header_id','qty', type='integer', string='Order Qty', store=True, readonly=True),
		
		'bom_id': fields.many2one('kg.bom','BOM'),
		'bom_line_id': fields.many2one('ch.bom.line','BOM Line'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No',domain="[('active','=','t')]"),
		'pattern_name': fields.char('Pattern Name'),
		'weight': fields.float('Weight(kgs)'),
		#~ 'pcs_weight': fields.related('pattern_id','pcs_weight', type='float', string='SS Weight(kgs)', store=True),
		#~ 'ci_weight': fields.related('pattern_id','ci_weight', type='float', string='CI Weight(kgs)', store=True),
		#~ 'nonferous_weight': fields.related('pattern_id','nonferous_weight', type='float', string='Non-Ferrous Weight(kgs)', store=True),
		'pos_no': fields.related('bom_line_id','pos_no', type='integer', string='Position No', store=True),
		'position_id': fields.many2one('kg.position.number', string='Position No'),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		'qty': fields.integer('Qty'),
		'unit_price': fields.float('Unit Price'),
		'schedule_qty': fields.integer('Schedule Pending Qty'),
		'production_qty': fields.integer('Produced Qty'),
		'flag_applicable': fields.boolean('Is Applicable'),
		'add_spec': fields.text('Others Specification'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),			   
		'flag_standard': fields.boolean('Non Standard'),
		'flag_pattern_check': fields.boolean('Is Pattern Check'),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		### Offer Details ###
		'spare_offer_line_id': fields.integer('Spare Offer'),
	
	}
	
	_defaults = {
		
		
		'state': 'draft',
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
		return super(ch_order_bom_details, self).create(cr, uid, vals, context=context)
	
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
		return super(ch_order_bom_details, self).write(cr, uid, ids, vals, context)
		
		
	def _check_qty_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty == 0 or entry.qty < 0:
			return False
		return True
		
	_constraints = [		
			  
		(_check_qty_values, 'System not allow to save with zero and less than zero qty .!!',['Quantity']),
		
	   ]
	
ch_order_bom_details()

class ch_order_machineshop_details(osv.osv):

	_name = "ch.order.machineshop.details"
	_description = "Order machineshop Details"
	
	
	_columns = {
	
		'header_id':fields.many2one('ch.work.order.details', 'Work Order Detail', required=1, ondelete='cascade'),
		'ms_line_id':fields.many2one('ch.machineshop.details', 'Machine Shop Id'),
		'pos_no': fields.related('ms_line_id','pos_no', type='integer', string='Position No', store=True),
		'position_id': fields.many2one('kg.position.number','Position No'),
		'bom_id': fields.many2one('kg.bom','BOM'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code',domain = [('type','=','ms')], ondelete='cascade',required=True),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		#~ 'name':fields.char('Item Name', size=128),
		'name': fields.related('ms_id','name', type='char',size=128,string='Item Name', store=True), 	  
		'qty': fields.integer('Qty', required=True),
		'unit_price': fields.float('Unit Price'),
		'length': fields.float('Length(mm)'),
		'flag_applicable': fields.boolean('Is Applicable'),
		'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'remarks':fields.text('Remarks'), 
		'flag_standard': fields.boolean('Non Standard'), 
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		### Offer Details ###
		'spare_offer_line_id': fields.integer('Spare Offer'),
	
	}  
	
	_defaults = {
		
		'entry_mode':'manual'
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		
		context.update({'entry_mode': 'manual'})
		return context
		
	def create(self, cr, uid, vals, context=None):
		return super(ch_order_machineshop_details, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_order_machineshop_details, self).write(cr, uid, ids, vals, context)   

ch_order_machineshop_details()

class ch_order_bot_details(osv.osv):
	
	_name = "ch.order.bot.details"
	_description = "Order BOT Details"	
	
	_columns = {
	
		'header_id':fields.many2one('ch.work.order.details', 'Work Order Detail', required=1, ondelete='cascade'),
		'bot_line_id':fields.many2one('ch.bot.details', 'BOT Line Id'),
		'bot_id':fields.many2one('kg.machine.shop', 'Item Code',domain = [('type','=','bot')], ondelete='cascade',required=True),
		'item_name': fields.related('bot_id','name', type='char', size=128, string='Item Name', store=True, readonly=True),
		'bom_id': fields.many2one('kg.bom','BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		'qty': fields.integer('Qty', required=True),
		'unit_price': fields.float('Unit Price'),
		'flag_applicable': fields.boolean('Is Applicable'),
		'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'remarks':fields.text('Remarks'),
		'flag_standard': fields.boolean('Non Standard'),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		### Offer Details ###
		'spare_offer_line_id': fields.integer('Spare Offer'),
	
	}
	
	_defaults = {
		
		'entry_mode':'manual'
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		context.update({'entry_mode': 'manual'})
		return context
	
		
	def create(self, cr, uid, vals, context=None):
		return super(ch_order_bot_details, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_order_bot_details, self).write(cr, uid, ids, vals, context)   

ch_order_bot_details()

class ch_order_consu_details(osv.osv):
	
	_name = "ch.order.consu.details"
	_description = "Order Consumable Details" 
	
	_columns = {
	
		'header_id':fields.many2one('ch.work.order.details', 'Order Detail', required=1, ondelete='cascade'),
		'product_temp_id':fields.many2one('product.product', 'Item Name',domain = [('type','=','consu')], ondelete='cascade',required=True),
		'consu_line_id':fields.many2one('ch.consu.details', 'Consumable Line Id'),
		'bom_id': fields.many2one('kg.bom','BOM'),
		'code':fields.char('Item Code', size=128),  
		'qty': fields.integer('Qty',required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
		'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'remarks':fields.text('Remarks'),
	
	}
	
	def default_get(self, cr, uid, fields, context=None):
		return context
	
		
	def create(self, cr, uid, vals, context=None):	  
		return super(ch_order_consu_details, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_order_consu_details, self).write(cr, uid, ids, vals, context) 

ch_order_consu_details()

### For Accessories ###

class ch_wo_accessories(osv.osv):

	_name = "ch.wo.accessories"
	_description = "Ch WO Accessories"
	
	_columns = {
	
		
		'header_id':fields.many2one('ch.work.order.details', 'Header Id', ondelete='cascade'),
		'access_id': fields.many2one('kg.accessories.master','Accessories',domain="[('active','=','t'),('state','not in',('draft','reject','cancal'))]"),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t'),('state','not in',('reject','cancal'))]"),
		'qty': fields.float('Qty'),
		'oth_spec': fields.char('Other Specification'),
		'load_access': fields.boolean('Load BOM'),
		
		'line_ids': fields.one2many('ch.wo.accessories.foundry', 'header_id', 'Accessories Foundry'),
		'line_ids_a': fields.one2many('ch.wo.accessories.ms', 'header_id', 'Accessories MS'),
		'line_ids_b': fields.one2many('ch.wo.accessories.bot', 'header_id', 'Accessories BOT'),
		'access_offer_line_id': fields.integer('Accessories Offer'),
		
	}
	
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False
		return True
	
	_constraints = [
	
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
		
	def onchange_load_access(self, cr, uid, ids, load_access,access_id,moc_id,qty):
		fou_vals=[]
		ms_vals=[]
		bot_vals=[]
		data_rec = ''
		
		if load_access == True and access_id:
			access_obj = self.pool.get('kg.accessories.master').search(cr, uid, [('id','=',access_id)])
			if access_obj:
				data_rec = self.pool.get('kg.accessories.master').browse(cr, uid, access_obj[0])
		print"data_recdata_rec",data_rec
		if data_rec:
			if data_rec.line_ids_b:
				for item in data_rec.line_ids_b:
					fou_vals.append({
									'position_id': item.position_id.id,
									'pattern_id': item.pattern_id.id,
									'pattern_name': item.pattern_name,
									'moc_id': moc_id,
									'qty': item.qty * qty,
									'load_bom': True,
									'is_applicable': True,
									
									})
				print"fou_valsfou_vals",fou_vals
			if data_rec.line_ids_a:
				for item in data_rec.line_ids_a:	
					ms_vals.append({
									'name': item.name,
									'position_id': item.position_id.id,							
									'ms_id': item.ms_id.id,
									'moc_id': moc_id,
									'qty': item.qty * qty,
									'load_bom': True,
									'is_applicable': True,
									
									})
					print"ms_valsms_vals",ms_vals	
			if data_rec.line_ids:
				for item in data_rec.line_ids:	
					bot_vals.append({
									'name': item.item_name,
									'position_id': item.position_id.id,							
									'ms_id': item.ms_id.id,
									'moc_id': moc_id,
									'qty': item.qty * qty,
									'load_bom': True,
									'is_applicable': True,
									'csd_no': item.csd_no,
									'remarks': item.remark,
									})
					print"bot_valsbot_vals",bot_vals	
		return {'value': {'line_ids': fou_vals,'line_ids_a': ms_vals,'line_ids_b': bot_vals}}
		
		
ch_wo_accessories()


class ch_wo_accessories_foundry(osv.osv):

	_name = "ch.wo.accessories.foundry"
	_description = "WO Accessories Foundry Details"
	
	_columns = {
	
		### Foundry Item Details ####
		'header_id':fields.many2one('ch.wo.accessories', 'Header Id', ondelete='cascade'),
		
		'pump_id':fields.many2one('kg.pumpmodel.master', 'Pump'),
		'qty':fields.integer('Quantity'),
		'oth_spec':fields.char('Other Specification'),
		'position_id': fields.many2one('kg.position.number','Position No'),
		'csd_no': fields.char('CSD No.', size=128),
		'pattern_name': fields.char('Pattern Name'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No'),
		'remarks': fields.char('Remarks'),
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		'prime_cost': fields.float('Prime Cost'),
		
	}
	
ch_wo_accessories_foundry()

class ch_wo_accessories_ms(osv.osv):

	_name = "ch.wo.accessories.ms"
	_description = "WO Accessories MS"
	
	_columns = {
	
		### machineshop Item Details ####
		'header_id':fields.many2one('ch.wo.accessories', 'Header Id', ondelete='cascade'),
		
		'pos_no': fields.related('position_id','name', type='integer', string='Position No', store=True),
		'position_id': fields.many2one('kg.position.number','Position No'),
		'csd_no': fields.char('CSD No.'),
		'bom_id': fields.many2one('kg.bom','BOM'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','ms')], ondelete='cascade',required=True),
		'name': fields.related('ms_id','name', type='char',size=128,string='Item Name', store=True),
		
		'qty': fields.integer('Qty', required=True),
		'remarks':fields.text('Remarks'),   
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		'prime_cost': fields.float('Prime Cost'),
		
	}
	
	
	_defaults = {
		
		'is_applicable':False,
		'load_bom':False,
		
	}
	
ch_wo_accessories_ms()

class ch_wo_accessories_bot(osv.osv):

	_name = "ch.wo.accessories.bot"
	_description = "WO Accessories BOT"
	
	_columns = {
	
		### BOT Item Details ####
		'header_id':fields.many2one('ch.wo.accessories', 'Header Id', ondelete='cascade'),
		'position_id': fields.many2one('kg.position.number','Position No'),
		'csd_no': fields.char('CSD No.'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','bot')], ondelete='cascade',required=True),
		'item_name': fields.related('ms_id','name', type='char',size=128,string='Item Name', store=True),
		'qty': fields.integer('Qty', required=True),
		'remarks':fields.text('Remarks'),   
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		'prime_cost': fields.float('Prime Cost'),
		
	}
	
ch_wo_accessories_bot()


### For Sequence No Generation ###

class kg_sequence_generate_det(osv.osv):
	_name = 'kg.sequence.generate.det'
	_order = 'name'
	_columns = {
		'name': fields.char('Name',size=64),
		'ir_sequence_id': fields.many2one('ir.sequence', 'Sequence'),
		'seq_month' : fields.integer('Sequence Month'),
		'seq_year' : fields.integer('Sequence Year'),
		'seq_next_number' : fields.integer('Sequence Next Number'),
		'fiscal_year_code' : fields.char('Fiscal Year Code',size=64),
		'fiscal_year_id' : fields.integer('Fiscal Year ID'),
	}
kg_sequence_generate_det()





	
	








