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


class kg_work_order(osv.osv):

	_name = "kg.work.order"
	_description = "Work Order Entry"
	_order = "entry_date desc"
	
	def _get_default_division(self, cr, uid, context=None):
		res = self.pool.get('kg.division.master').search(cr, uid, [('code','=','SAM'), ('active','=','t')], context=context)
		return res and res[0] or False

	_columns = {
	
		### Header Details ####
		'name': fields.char('WO No.', size=128,select=True,required=True),
		'entry_date': fields.date('WO Date',required=True),
		'division_id': fields.many2one('kg.division.master','Division',readonly=True,required=True,domain="[('active','=','t')]"),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location', required=True),
		'note': fields.text('Notes'),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'WO Status', readonly=True),
		'line_ids': fields.one2many('ch.work.order.details', 'header_id', "Work Order Details"),
		'flag_cancel': fields.boolean('Cancellation Flag'),
		'order_priority': fields.selection(ORDER_PRIORITY,'Priority', required=True),
		'delivery_date': fields.date('Delivery Date',required=True),
		'order_value': fields.float('Work Order Value(lakh)'),
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
		'active': True,
		'division_id':_get_default_division,
		'delivery_date' : lambda * a: time.strftime('%Y-%m-%d'),
	
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
		cr.execute(""" select name from kg_work_order where name  = '%s' """ %(entry.name))
		data = cr.dictfetchall()
			
		if len(data) > 1:
			res = False
		else:
			res = True	
		return res 
			
	
	_constraints = [		
		
		#(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
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
	   
	
	def entry_confirm(self,cr,uid,ids,context=None):
		schedule_obj = self.pool.get('kg.schedule')
		line_obj = self.pool.get('ch.work.order.details')
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		entry = self.browse(cr,uid,ids[0])
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
						
			
			if not item.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('Specify BOM Details for Pump Model %s !!')%(item.pump_model_id.name))
				
			else:
				cr.execute(''' select id from ch_order_bom_details where flag_applicable = 't' and header_id = %s ''',[item.id])	  
				bom_check_id = cr.fetchone()
				
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
			
		if entry.order_priority == 'normal' and entry.order_category in ('spare','service'):
			
			### Schedule Creation ###
			
			schedule_item_vals = {
											
				'name': '',
				'location' : entry.location,
				'order_priority': 'normal',
				'delivery_date': entry.delivery_date,
				'order_line_ids': [(6, 0, order_line_ids)],
				'state' : 'draft'					   
			}
			
			schedule_id = schedule_obj.create(cr, uid, schedule_item_vals)
			
			### Schedule Line Item Creation ###
			
			schedule_obj.update_line_items(cr, uid, [schedule_id])
			
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
				'state' : 'draft'					   
			}
			
			schedule_id = schedule_obj.create(cr, uid, schedule_item_vals)
			
			### Schedule Line Item Creation ###
			
			schedule_obj.update_line_items(cr, uid, [schedule_id])
			
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
				'state' : 'draft'					   
			}
			
			schedule_id = schedule_obj.create(cr, uid, schedule_item_vals)
			
			### Schedule Line Item Creation ###
			
			schedule_obj.update_line_items(cr, uid, [schedule_id])
			
			
		cr.execute(''' select sum(unit_price) from ch_work_order_details where header_id = %s ''',[entry.id])	   
		order_value = cr.fetchone()
		self.write(cr, uid, ids, {'order_value':order_value[0],'state': 'confirmed','flag_cancel':1,'confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		cr.execute(''' update ch_work_order_details set state = 'confirmed', flag_cancel='t', schedule_status = 'allow' where header_id = %s ''',[ids[0]])
		return True
		
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_work_order = str(rec.name)
		#~ url = 'http://iasqa1.kgisl.com/?uname='+rec_user+'&s='+rec_work_order
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
		
		url = 'http://192.168.1.7/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&wo_no='+rec_work_order
		
		#url = 'http://192.168.1.150:81/pbxclick2call.php?exten='+exe_no+'&phone='+str(m_no)
		print "url..................................", url
		return {
					  'name'     : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'     : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'      : url
			   }
		
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
		'order_no': fields.char('Order No.', size=128,select=True),
		'order_category': fields.selection([('pump','Pump'),('spare','Spare'),('pump_spare','Pump and Spare')],'Purpose', required=True),
		'qty': fields.integer('Qty', required=True),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'note': fields.text('Notes'),
		'remarks': fields.text('Approve/Reject Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'delivery_date': fields.date('Delivery Date',required=True),
		'line_ids': fields.one2many('ch.order.bom.details', 'header_id', "BOM Details"),
		'line_ids_a': fields.one2many('ch.order.machineshop.details', 'header_id', "Machine Shop Details"),
		'line_ids_b': fields.one2many('ch.order.bot.details', 'header_id', "BOT Details"),
		'line_ids_c': fields.one2many('ch.order.consu.details', 'header_id', "Consumale Details"),
		'flag_cancel': fields.boolean('Cancellation Flag'),
		'flag_standard': fields.boolean('Non Standard'),
		'unit_price': fields.float('Unit Price',required=True),
		### Used for Schedule Purpose
		'schedule_status':fields.selection([('allow','Allow to Schedule'),('not_allow','Not Allow to Schedule')],'Schedule Status', readonly=True),
		'moc_construction_id':fields.many2one('kg.moc.construction','MOC Construction',domain="[('active','=','t')]"),

	}
	
	
	_defaults = {
	
		'state': 'draft',
		'schedule_status': 'allow',
		'delivery_date' : lambda * a: time.strftime('%Y-%m-%d'),
		
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
		

	def onchange_bom_details(self, cr, uid, ids, pump_model_id, qty,moc_construction_id, order_category,flag_standard):
		bom_vals=[]
		machine_shop_vals=[]
		bot_vals=[]
		consu_vals=[]
		
		#~ if order_category == False:
			#~ raise osv.except_osv(_('Warning!'),
						#~ _('Kindly select Purpose and then enter Qty !!'))
						
		if pump_model_id != False:
			
			#### Loading Foundry Items
			
			order_bom_obj = self.pool.get('ch.order.bom.details')
			cr.execute(''' select bom.id,bom.header_id,bom.pattern_id,bom.pattern_name,bom.qty, bom.pos_no,pattern.pcs_weight, pattern.ci_weight,pattern.nonferous_weight
					from ch_bom_line as bom
					LEFT JOIN kg_pattern_master pattern on pattern.id = bom.pattern_id
					where bom.header_id = (select id from kg_bom where pump_model_id = %s  and active='t') ''',[pump_model_id])
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
						
					bom_vals.append({
														
						'bom_id': bom_details['header_id'],
						'bom_line_id': bom_details['id'],
						'pattern_id': bom_details['pattern_id'],
						'pattern_name': bom_details['pattern_name'],						
						'pcs_weight': bom_details['pcs_weight'] or 0.00,						
						'ci_weight': bom_details['ci_weight'] or 0.00,				  
						'nonferous_weight': bom_details['nonferous_weight'] or 0.00,				  
						'pos_no': bom_details['pos_no'],				  
						'qty' : bom_qty,				   
						'schedule_qty' : bom_qty,				  
						'production_qty' : 0,				   
						'flag_applicable' : applicable,
						'order_category':	order_category,
						'moc_id': moc_id,
						'flag_standard':flag_standard	  
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
						
						
					machine_shop_vals.append({
						
						'pos_no':bom_ms_details['pos_no'],					
						'ms_line_id': bom_ms_details['id'],
						'bom_id': bom_ms_details['bom_id'],
						'ms_id': bom_ms_details['ms_id'],
						'name': bom_ms_details['name'],
						'qty': bom_ms_qty,
						'flag_applicable' : applicable,
								  
						})
						
				#### Loading BOT Details
				
				bom_bot_obj = self.pool.get('ch.bot.details')
				cr.execute(''' select id,bot_id,qty,header_id as bom_id
						from ch_bot_details
						where header_id = (select id from kg_bom where pump_model_id = %s and active='t') ''',[pump_model_id])
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
		if header_rec.state == 'draft':
			res = super(ch_work_order_details, self).create(cr, uid, vals, context=context)
		else:
			res = False
		return res
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_work_order_details, self).write(cr, uid, ids, vals, context)
		
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []
		for rec in self.browse(cr,uid,ids): 
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete Work Order Details after confirmation !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	
	
	_constraints = [		
			  
		(_check_qty_values, 'System not allow to save with zero and less than zero qty .!!',['Quantity']),
		(_check_unit_price, 'System not allow to save with zero and less than zero Unit Price .!!',['Unit Price']),
		(_check_line_duplicates, 'Work Order Details are duplicate. Kindly check !! ', ['']),
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
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No',domain="[ ('active','=','t')]"),
		'pattern_name': fields.char('Pattern Name'),
		'pcs_weight': fields.related('pattern_id','pcs_weight', type='float', string='SS Weight(kgs)', store=True),
		'ci_weight': fields.related('pattern_id','ci_weight', type='float', string='CI Weight(kgs)', store=True),
		'nonferous_weight': fields.related('pattern_id','nonferous_weight', type='float', string='Non-Ferrous Weight(kgs)', store=True),
		'pos_no': fields.related('bom_line_id','pos_no', type='integer', string='Position No', store=True),
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
	
	}
	
	_defaults = {
		
		
		'state': 'draft',
		'flag_applicable': False,
		'flag_pattern_check': False,
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		return context
		
	def onchange_pattern_details(self, cr, uid, ids, pattern_id):
		pattern_obj = self.pool.get('kg.pattern.master')
		if pattern_id:
			pattern_rec = pattern_obj.browse(cr, uid, pattern_id)
			pattern_name = pattern_rec.pattern_name
			ss_wgt = pattern_rec.pcs_weight
			ci_wgt = pattern_rec.ci_weight
			non_fer_wgt = pattern_rec.nonferous_weight
		return {'value': {'pattern_name': pattern_name,'pcs_weight':ss_wgt,'ci_weight':ci_wgt,'nonferous_weight':non_fer_wgt}}
	
	def create(self, cr, uid, vals, context=None):
		if vals.get('pattern_id'):
			pattern_obj = self.pool.get('kg.pattern.master')
			pattern_rec = pattern_obj.browse(cr, uid, vals.get('pattern_id'))
			pattern_name = pattern_rec.pattern_name
			ss_wgt = pattern_rec.pcs_weight
			ci_wgt = pattern_rec.ci_weight
			non_fer_wgt = pattern_rec.nonferous_weight
			vals.update({'pattern_name': pattern_name,'pcs_weight':ss_wgt,'ci_weight':ci_wgt,'nonferous_weight':non_fer_wgt})
		return super(ch_order_bom_details, self).create(cr, uid, vals, context=context)
	
	def write(self, cr, uid, ids, vals, context=None):
		if vals.get('pattern_id'):
			pattern_obj = self.pool.get('kg.pattern.master')
			pattern_rec = pattern_obj.browse(cr, uid, vals.get('pattern_id'))
			pattern_name = pattern_rec.pattern_name
			ss_wgt = pattern_rec.pcs_weight
			ci_wgt = pattern_rec.ci_weight
			non_fer_wgt = pattern_rec.nonferous_weight
			vals.update({'pattern_name': pattern_name,'pcs_weight':ss_wgt,'ci_weight':ci_wgt,'nonferous_weight':non_fer_wgt})
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
		'bom_id': fields.many2one('kg.bom','BOM'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', ondelete='cascade',required=True),
		'name':fields.char('Item Name', size=128),	  
		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
		'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'remarks':fields.text('Remarks'),   
	
	}   
	
	def default_get(self, cr, uid, fields, context=None):
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
		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
		'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'remarks':fields.text('Remarks'),   
	
	}
	
	def default_get(self, cr, uid, fields, context=None):
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






