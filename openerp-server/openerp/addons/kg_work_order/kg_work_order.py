from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import base64
import math
from datetime import timedelta

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')


ORDER_PRIORITY = [
   ('normal','Normal'),
   ('emergency','Emergency'),
   ('breakdown','Break Down'),
   ('urgent','Urgent'),
   
]

ORDER_CATEGORY = [
   ('pump','Pump'),
   ('spare','Spare'),
   ('pump_spare','Pump and Spare'),
   ('service','Service'),
   ('project','Project'),
   ('access','Accessories')
   
]

def roundPartial (value, resolution):
	return round (value / resolution) * resolution



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
			cr.execute(''' select sum(unit_price) from ch_work_order_details where header_id = %s ''',[entry.id])
			pump_wo_value = cr.fetchone()
			
			#~ cr.execute(''' select sum(header.unit_price) from ch_order_bom_details as line
				#~ left join ch_work_order_details header on header.id = line.header_id where header.header_id = %s 
				#~ ''',[entry.id])
			#~ spare_wo_value = cr.fetchone()
			#~ if pump_wo_value[0] == None:
				#~ pump_value = 0.00
			#~ else:
				#~ pump_value= pump_wo_value[0]
			#~ if spare_wo_value[0] == None:
				#~ spare_value = 0.00
			#~ else:
				#~ spare_value=spare_wo_value[0]
			wo_value = pump_wo_value[0]
			result[entry.id] = wo_value
		return result

	_columns = {
	
		### Header Details  ###########
		'name': fields.char('WO No.', size=128,select=True),
		'entry_date': fields.date('WO Date',required=True),
		'division_id': fields.many2one('kg.division.master','Division',readonly=True,required=True,domain="[('active','=','t')]"),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location'),
		'note': fields.text('Notes'),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('mkt_approved','MKT Approved'),('design_approved','Design Approved'),
				('confirmed','MD Approved'),('cancel','Cancelled')],'WO Status', readonly=True),
		'line_ids': fields.one2many('ch.work.order.details', 'header_id', "Work Order Details"),
		'flag_cancel': fields.boolean('Cancellation Flag'),
		'order_priority': fields.selection(ORDER_PRIORITY,'Priority'),
		'delivery_date': fields.date('Delivery Date',required=True),
		'order_value': fields.function(_get_order_value, string='WO Value', method=True, store=True, type='float'),
		'order_category': fields.selection(ORDER_CATEGORY,'Category'),
		'partner_id': fields.many2one('res.partner','Customer'),
		'dealer_id': fields.many2one('res.partner','Dealer Name'),
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
		'delivery_date_flag': fields.boolean('Delivery Date Flag'),
		'offer_no': fields.char('Offer No.'),
		'enquiry_no': fields.char('Enquiry No.'),
		#~'enquiry_id': fields.many2one('kg.crm.enquiry','Enquiry No.'),
		#~ 'offer_id': fields.many2one('kg.crm.offer','Offer No.'),
		'wo_spc_app_flag': fields.boolean('WO Special Approval'),
		'design_flag': fields.boolean('Design Flag'),
		'excise_duty': fields.selection([('inclusive','Inclusive'),('extra','Extra'),('exemted','Exemted - Export'),('pac','PAC'),('sez','SEZ'),('ct1','CT1'),('ct3','CT3')],'EXCISE DUTY'),
		'drawing_approval': fields.selection([('yes','Yes'),('no','No')],'Drawing approval'),
		'road_permit': fields.selection([('yes','Yes'),('no','No')],'Road Permit'),
		'inspection': fields.selection([('yes','Yes'),('no','No'),('tpi','TPI'),('customer','Customer'),('consultant','Consultant'),('stagewise','Stage wise')],'Inspection'),
		#~ 'l_d_clause': fields.selection([('5_1','0.5 - 1.0% of total order value'),('1_10','1 to 10% of total order value'),('nill','Nill')],'L. D. CLAUSE / Penalty'),
		'l_d_clause':fields.char('L. D. CLAUSE / Penalty'),
		'flag_data_bank': fields.boolean('Is Data WO'),
		'project_name':fields.char('Project Name'),
		'stock_check': fields.selection([('yes','Yes'),('no','No')],'Stock Check'),
		
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
		'stock_check': 'yes',
		'active': True,
		'division_id':_get_default_division,
		'delivery_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'version': '00',
		'flag_for_stock': False,
		'invoice_flag': False,
		'wo_spc_app_flag': False,
		'design_flag': False,
		
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
		if flds.name == False:
			raise osv.except_osv(_('Warning!'),
				_('Work Order No. is must !!'))
		special_char = ''.join( c for c in flds.name if  c in '!@#$%^~*{}?+=' )
		if special_char:
			return False
		return True
		
	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])		
		res = True
		if rec.entry_mode == 'manual':
			if rec.name:
				wo_name = rec.name
				name=wo_name.upper()			
				cr.execute(""" select upper(name) from kg_work_order where upper(name)  = '%s' """ %(name))
				data = cr.dictfetchall()			
				if len(data) > 1:
					res = False
				else:
					res = True	
			else:
				res = True	
		else:
			res = True				
		return res
		
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
		(_name_validate, 'Work Order No. must be Unique', ['']),
	   
		
	   ]	   
	   
	def onchange_delivery_date(self, cr, uid, ids, delivery_date,order_category,order_priority):
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		if delivery_date:
			delivery_date = str(delivery_date)
			delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d')
			if order_category == 'spare' and order_priority == 'normal':					
				ends_date = date.today()+timedelta(days=56)
				end_date = ends_date.strftime('%Y-%m-%d')				
				del_date = str(end_date)
				ex_del_date = datetime.strptime(del_date, '%Y-%m-%d')				
				if delivery_date < ex_del_date:
					raise osv.except_osv(_('Warning!'),
						_('Delivery Date should not be less than 56 days!!'))
				else:
					pass
			elif order_category == 'pump' and order_priority == 'normal':				
				ends_date = date.today()+timedelta(days=84)
				end_date = ends_date.strftime('%Y-%m-%d')
				del_date = str(end_date)
				ex_del_date = datetime.strptime(del_date, '%Y-%m-%d')	
				if delivery_date < ex_del_date:
					raise osv.except_osv(_('Warning!'),
						_('Delivery Date should not be less than 84 days!!'))
				else:
					pass			
			elif delivery_date < today:
				raise osv.except_osv(_('Warning!'),
						_('Delivery Date should not be less than current date!!'))
		return True
		
	def onchange_order_category_delivery_date(self, cr, uid, ids, order_category,order_priority):
		today = time.strftime('%Y-%m-%d')	
		value = {'delivery_date': '','delivery_date_flag': ''}
		if order_category != False and order_priority != False:			
			if order_category == 'spare' and order_priority == 'normal':					
				ends_date = date.today()+timedelta(days=56)
				end_date = ends_date.strftime('%Y-%m-%d')				
				delivery_date_flag = True
				value = {'delivery_date': end_date,'delivery_date_flag': delivery_date_flag}			
			elif order_category == 'pump' and order_priority == 'normal':				
				ends_date = date.today()+timedelta(days=84)
				end_date = ends_date.strftime('%Y-%m-%d')	
				delivery_date_flag = True	
				value = {'delivery_date': end_date,'delivery_date_flag': delivery_date_flag}			
			else:				
				delivery_date_flag = False
				value = {'delivery_date': today,'delivery_date_flag': delivery_date_flag}		
				
			return {'value': value}
		else:
			return {'value': value}
		
		
	def onchange_order_priority_delivery_date(self, cr, uid, ids, order_category,order_priority):
		today = time.strftime('%Y-%m-%d')	
		value = {'delivery_date': '','delivery_date_flag': ''}
		if order_category != False and order_priority != False:			
			if order_category == 'spare' and order_priority == 'normal':					
				ends_date = date.today()+timedelta(days=56)
				end_date = ends_date.strftime('%Y-%m-%d')				
				delivery_date_flag = True
				value = {'delivery_date': end_date,'delivery_date_flag': delivery_date_flag}			
			elif order_category == 'pump' and order_priority == 'normal':				
				ends_date = date.today()+timedelta(days=84)
				end_date = ends_date.strftime('%Y-%m-%d')	
				delivery_date_flag = True	
				value = {'delivery_date': end_date,'delivery_date_flag': delivery_date_flag}			
			else:				
				delivery_date_flag = False
				value = {'delivery_date': today,'delivery_date_flag': delivery_date_flag}		
				
			return {'value': value}
		else:
			return {'value': value}
		
	#~ def mail_test(self,cr,uid,ids,context=None):
	   #~ ### Mail Testing ###
		#~ scheduler_obj = self.pool.get('kg.scheduler')
		#~ body = '<html><body><p>The below mentioned Material Requisition is waiting for approval.</p></body></html>'
		#~ scheduler_obj.send_mail(cr, uid,ids,'sangeetha.subramaniam@kggroup.com',['sangeetha.subramaniam@kggroup.com'],
			#~ [],[],'Test',body,'')
		#~ ###
		#~ return True
		
	def mkt_approve(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			today = time.strftime('%Y-%m-%d')
			todays_date = str(today)
			today_date = datetime.strptime(todays_date, '%Y-%m-%d')		
			delivery_date = str(entry.delivery_date)
			delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d')
			if entry.order_category == 'spare' and entry.order_priority == 'normal':					
				ends_date = date.today()+timedelta(days=56)
				end_date = ends_date.strftime('%Y-%m-%d')				
				del_date = str(end_date)
				ex_del_date = datetime.strptime(del_date, '%Y-%m-%d')				
				if delivery_date < ex_del_date:
					raise osv.except_osv(_('Warning!'),
						_('Delivery Date should not be less than 56 days!!'))
				else:
					pass
			elif entry.order_category == 'pump' and entry.order_priority == 'normal':				
				ends_date = date.today()+timedelta(days=84)
				end_date = ends_date.strftime('%Y-%m-%d')
				del_date = str(end_date)
				ex_del_date = datetime.strptime(del_date, '%Y-%m-%d')	
				if delivery_date < ex_del_date:
					raise osv.except_osv(_('Warning!'),
						_('Delivery Date should not be less than 84 days!!'))
				else:
					pass				
			elif delivery_date < today_date:
				raise osv.except_osv(_('Warning!'),
						_('Delivery Date should not be less than current date!!'))
			
			
			# Customer TIN No validation start
			#~ if entry.partner_id.gs_tin_no:
				#~ if len(str(entry.partner_id.gs_tin_no)) == 11 and entry.partner_id.gs_tin_no.isdigit() == True:
					#~ pass
				#~ else:
					#~ raise osv.except_osv(_('Warning!'),_('GS TIN No. should contain 11 digit numerics. Else system not allow to save.!'))
			#~ else:
				#~ raise osv.except_osv(_('Warning!'),_('Update GS TIN no. in Customer master and Proceed for approval!'))
			# Customer TIN No validation end
			
			self.write(cr,uid,ids,{'state':'mkt_approved','design_flag':True})
		return True
		
	def design_approve(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		wo_spc_app_flag = False
		if entry.state in ('draft','mkt_approved'):
			delivery_date = str(entry.delivery_date)
			delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d')
			print "delivery_date",delivery_date
			print "today",today
			if delivery_date < today:
				raise osv.except_osv(_('Warning!'),
							_('Delivery Date should not be less than current date for Order !!'))
							
			
			#### Prime cost Comparison ###
			for item in entry.line_ids:
				
				line_delivery_date = str(item.delivery_date)
				line_delivery_date = datetime.strptime(line_delivery_date, '%Y-%m-%d')
				if line_delivery_date < today:
					raise osv.except_osv(_('Warning!'),
							_('Delivery Date should not be less than current date for Pump Model %s !!')%(item.pump_model_id.name))
							
				
				#~ if item.order_category != 'access':
					#~ if not item.line_ids:
						#~ raise osv.except_osv(_('Warning!'),
									#~ _('Specify BOM Details for Pump Model %s !!')%(item.pump_model_id.name))
					
				#~ else:
				#~ cr.execute(''' select id from ch_order_bom_details where flag_applicable = 't' and header_id = %s ''',[item.id])	  
				#~ bom_check_id = cr.fetchone()
				#~ 
				#~ if item.order_category != 'access':
					#~ if item.line_ids: 
						#~ if bom_check_id == None:
							#~ raise osv.except_osv(_('Warning!'),
									#~ _('Kindly enable BOM Details for Pump Model %s!!')%(item.pump_model_id.name))
					
				
				cr.execute(''' select id from ch_order_bom_details where flag_applicable = 't' and moc_id is null and header_id = %s ''',[item.id])	   
				order_bom_id = cr.fetchone()
				if order_bom_id:
					if order_bom_id[0] != None:
						raise osv.except_osv(_('Warning!'),
							_('Specify MOC for Pump Model %s!!')%(item.pump_model_id.name))
				
				
				self.prime_cost_update(cr,uid,ids,context=None)
				if item.order_category != 'access':
					cr.execute(''' select wo_prime_cost from ch_work_order_details where id = %s ''',[item.id])	   
					wo_prime_cost = cr.fetchone()
					if entry.entry_mode == 'auto':
						if wo_prime_cost[0] > item.mar_prime_cost:
							wo_spc_app_flag = True
						
				elif item.order_category == 'access':
					for acc_item in item.line_ids_d:
						cr.execute(''' select wo_prime_cost from ch_wo_accessories where id = %s ''',[acc_item.id])	   
						wo_acc_prime_cost = cr.fetchone()
						if entry.entry_mode == 'auto':
							if wo_acc_prime_cost[0] > acc_item.mar_prime_cost: 
								wo_spc_app_flag = True
				elif item.order_category == 'service':
					wo_spc_app_flag = True
					
				elif item.order_priority in ('urgent','breakdown','emergency'):
					wo_spc_app_flag = True
				
				if wo_spc_app_flag == True:
					self.write(cr,uid,ids,{'wo_spc_app_flag':True})
					
			self.write(cr,uid,ids,{'state':'design_approved'})
		return True
		
	def special_approve(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'design_approved':
			self.write(cr,uid,ids,{'wo_spc_app_flag':False})
		return True
	
	def entry_confirm(self,cr,uid,ids,context=None):
		
		schedule_obj = self.pool.get('kg.schedule')
		line_obj = self.pool.get('ch.work.order.details')
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		entry = self.browse(cr,uid,ids[0])
		assembly_obj = self.pool.get('kg.assembly.inward')
		assembly_foundry_obj = self.pool.get('ch.assembly.bom.details')
		assembly_ms_obj = self.pool.get('ch.assembly.machineshop.details')
		assembly_bot_obj = self.pool.get('ch.assembly.bot.details')
		
		if entry.state in ('design_approved'):
			
			if entry.name:
				wo_name = entry.name
				name=wo_name.upper()			
				cr.execute(""" select upper(name) from kg_work_order where upper(name)  = '%s' """ %(name))
				data = cr.dictfetchall()			
				if len(data) > 1:
					raise osv.except_osv(_('Warning!'),
						_('Work Order No. must be Unique !!'))
				else:
					pass
			if entry.name:
				cr.execute(""" select name from kg_work_order where name  = '%s'  """ %(entry.name))
				data = cr.dictfetchall()			
				if len(data) > 1:
					raise osv.except_osv(_('Warning!'),
						_('Work Order No. must be Unique !!'))
				else:
					pass
			else:
				pass
			for line in entry.line_ids:
				if line.order_no:				
					cr.execute(""" select wo_order.id as order_id from kg_work_order wo_order
						left join ch_work_order_details ch_work on ch_work.header_id = wo_order.id 
						where ch_work.order_no  = '%s' and ch_work.header_id not in ('%s')   """ %(line.order_no,line.header_id.id))
					data = cr.dictfetchall()			
					if len(data) >= 1:
						raise osv.except_osv(_('Warning!'),
							_('Line Work Order No. must be Unique !!'))
					else:
						pass
				else:
					pass
			
			order_line_ids = []
			
			### Spare BOM Tab Data Creation ###
			for order_line_item in entry.line_ids: 
				if order_line_item.line_ids_e:
					for spare_item in order_line_item.line_ids_e:
						for spare_foundry_item in spare_item.line_ids:
							if spare_foundry_item.is_applicable == True:
								foundry_spare_vals = {
									
									'header_id': order_line_item.id,				
									#~ 'bom_id': bom_details['header_id'],
									#~ 'bom_line_id': bom_details['id'],
									'pattern_id': spare_foundry_item.pattern_id.id,
									'pattern_name': spare_foundry_item.pattern_name,						
									'off_name': spare_foundry_item.off_name,						
									'weight': 0.00,								  
									#~ 'pos_no': bom_details['pos_no'],
									'position_id': spare_foundry_item.position_id.id,				  
									'qty' : spare_foundry_item.qty,				   
									'schedule_qty' : spare_foundry_item.qty,				  
									'production_qty' : 0,				   
									'flag_applicable' : True,
									'order_category': order_line_item.order_category,
									'moc_id': spare_foundry_item.moc_id.id,
									'flag_standard':order_line_item.flag_standard,
									'entry_mode':'auto'	,
									'bom_type': 'spare',
									'spare_bom_id': spare_foundry_item.id,
									'spare_id': spare_item.id,
									'flag_pattern_check': spare_foundry_item.flag_pattern_check,
									'material_code': spare_foundry_item.material_code,
									'sequence_no': spare_foundry_item.sequence_no,
									}
								new_foundry_item_id = self.pool.get('ch.order.bom.details').create(cr,uid,foundry_spare_vals)
								
								
								
						for spare_ms_item in spare_item.line_ids_a:
							if spare_ms_item.is_applicable == True:
								spare_machine_shop_vals = {
									
									'header_id': order_line_item.id,
									#~ 'pos_no': bom_ms_details['pos_no'],
									'position_id': spare_ms_item.position_id.id,
									#~ 'bom_id': bom_ms_details['bom_id'],
									'ms_id': spare_ms_item.ms_id.id,
									'name': spare_ms_item.name,
									'off_name': spare_ms_item.off_name,
									'qty': spare_ms_item.qty,
									'indent_qty':spare_ms_item.qty,
									'flag_applicable' : True,
									'flag_standard':order_line_item.flag_standard,
									'entry_mode':'auto',
									'order_category': order_line_item.order_category,
									'moc_id': spare_ms_item.moc_id.id,
									'bom_type': 'spare',
									'spare_bom_id': spare_ms_item.id,
									'spare_id': spare_item.id, 
									'material_code': spare_ms_item.material_code,
									'sequence_no': spare_ms_item.sequence_no,
											  
									}
									
								new_ms_item_id = self.pool.get('ch.order.machineshop.details').create(cr,uid,spare_machine_shop_vals)
								
								### Raw materials Creation ###
								
								for spare_raw in spare_ms_item.line_ids:
								
									spare_ms_raw_vals = {
									
										'header_id': new_ms_item_id,
										'remarks': spare_raw.remarks,
										'product_id': spare_raw.product_id.id,			
										'uom': spare_raw.uom.id,
										'od': spare_raw.od,
										'length': spare_raw.length,
										'breadth': spare_raw.breadth,
										'thickness': spare_raw.thickness,
										'weight': spare_raw.weight,
										'uom_conversation_factor': spare_raw.uom_conversation_factor,		
										'temp_qty': spare_raw.temp_qty,
										'qty': spare_raw.qty,
										'spare_raw_id': spare_raw.id,
										
									}
									new_ms_spare_item_id = self.pool.get('ch.wo.ms.raw').create(cr,uid,spare_ms_raw_vals)
									

						for spare_bot_item in spare_item.line_ids_b:
							if spare_bot_item.is_applicable == True:
								spare_bot_vals = {
									
									'header_id': order_line_item.id,
									#~ 'bot_line_id': bom_bot_details['id'],
									#~ 'bom_id': bom_bot_details['bom_id'],							
									'position_id': spare_bot_item.position_id.id,							
									'bot_id': spare_bot_item.ms_id.id,
									'item_name': spare_bot_item.item_name,
									'off_name': spare_bot_item.off_name,
									'qty': spare_bot_item.qty,
									'flag_applicable' : True,
									'flag_standard':order_line_item.flag_standard,
									'entry_mode':'auto',
									'order_category':order_line_item.order_category,
									#~ 'flag_is_bearing': bot_rec.is_bearing,
									'moc_id': spare_bot_item.moc_id.id,
									'bom_type': 'spare',
									'spare_bom_id': spare_bot_item.id,
									'spare_id': spare_item.id,
									'material_code': spare_bot_item.material_code,
									'sequence_no': spare_bot_item.sequence_no,
											  
									}
									
								new_bot_item_id = self.pool.get('ch.order.bot.details').create(cr,uid,spare_bot_vals)
								
			
			
			
			if entry.flag_data_bank == False:
							
				#~ number = 1
				print "entry.line_ids",entry.line_ids
				
				for item in entry.line_ids:
					
					### Drawing Indent Creation ###
					indent_foundry = 1
					indent_ms = 1
					indent_bot = 1

					### For Foundry Items ###
					
					
					
					cr.execute(""" select foundry.id as order_bom_id,foundry.position_id,pattern.name as item_code,
							foundry.pattern_name as item_name,'foun' as type
							from ch_order_bom_details foundry
							left join kg_pattern_master pattern on pattern.id = foundry.pattern_id
							where foundry.header_id = %s  and foundry.flag_applicable = 't'
							and foundry.flag_pattern_check = 't' 
							
							union
							
							select foundry.id as order_bom_id,foundry.position_id,pattern.name as item_code,
							foundry.pattern_name as item_name,'foun' as type
							from ch_order_bom_details foundry
							left join kg_pattern_master pattern on pattern.id = foundry.pattern_id
							where foundry.header_id = %s  and foundry.flag_applicable = 't'
							and foundry.flag_pattern_check = 'f' 
							and foundry.position_id not in 
							(select position_id from ch_drawing_indent_line)
							
							union
							
							
							select foundry_acc.id as order_bom_id,foundry_acc.position_id,pattern.name as item_code,
							foundry_acc.pattern_name as item_name,'foun_acc' as type
							from ch_wo_accessories_foundry foundry_acc
							left join kg_pattern_master pattern on pattern.id = foundry_acc.pattern_id
							where foundry_acc.header_id = %s  and foundry_acc.is_applicable = 't'
							and foundry_acc.position_id not in 
							(select position_id from ch_drawing_indent_line)

						 """%(item.id,item.id,item.id))
					draw_foundry_items = cr.dictfetchall();
					print "draw_foundry_items",draw_foundry_items
					
					for foundry_indent_item in draw_foundry_items:
						
						if indent_foundry == 1:
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP15')])
					
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.drawing.indent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry.entry_date))
							seq_name = cr.fetchone();

							draw_indent_obj = self.pool.get('kg.drawing.indent')
							
							draw_indent_vals = {
								'name': seq_name[0],
								'entry_mode': 'auto',
								'division_id': entry.division_id.id,
								'dep_id': dep_id[0],
								'order_line_id': item.id,
								'pump_model_type': item.pump_model_type,
								'state': 'confirmed'
							}
							
							foundry_indent_id = draw_indent_obj.create(cr,uid,draw_indent_vals)
							
							indent_foundry = indent_foundry + 1
							
						if foundry_indent_id:
							
							if foundry_indent_item['type'] == 'foun':
								order_foundry_id = foundry_indent_item['order_bom_id']
								order_foundry_acc_id = False
							if foundry_indent_item['type'] == 'foun_acc':
								order_foundry_id = False
								order_foundry_acc_id = foundry_indent_item['order_bom_id']
							
							draw_indent_line_obj = self.pool.get('ch.drawing.indent.line')
							
							print "order_foundry_id",order_foundry_id
							print "order_foundry_acc_id",order_foundry_acc_id
							
							foundry_indent_line_vals = {
							
								'header_id': foundry_indent_id,
								'order_foundry_id': order_foundry_id,
								'order_foundry_acc_id': order_foundry_acc_id,
								'position_id': foundry_indent_item['position_id'],
								'item_code': foundry_indent_item['item_code'],
								'item_name': foundry_indent_item['item_name'],
							}
							
							draw_indent_line_obj.create(cr,uid,foundry_indent_line_vals)
							
							
					### For MS Items ###
					
					cr.execute(""" select ms.id as order_bom_id,ms.position_id,ms_master.code as item_code,
							ms.name as item_name,'ms' as type
							from ch_order_machineshop_details ms
							left join kg_machine_shop ms_master on ms_master.id = ms.ms_id
							where ms.header_id = %s  and ms.flag_applicable = 't'
							and ms.position_id not in 
							(select position_id from ch_drawing_indent_line)
							
							union
							
							select ms_acc.id as order_bom_id,ms_acc.position_id,ms_acc_master.code as item_code,
							ms_acc.name as item_name,'ms_acc' as type
							from ch_wo_accessories_ms ms_acc
							left join kg_machine_shop ms_acc_master on ms_acc_master.id = ms_acc.ms_id
							where ms_acc.header_id = %s  and ms_acc.is_applicable = 't'
							and ms_acc.position_id not in 
							(select position_id from ch_drawing_indent_line)

						 """%(item.id,item.id))
					draw_ms_items = cr.dictfetchall();
					print "draw_ms_items",draw_ms_items
					
					for ms_indent_item in draw_ms_items:
						
						if indent_ms == 1:
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP2')])
					
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.drawing.indent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry.entry_date))
							seq_name = cr.fetchone();

							draw_indent_obj = self.pool.get('kg.drawing.indent')
							
							draw_indent_vals = {
								'name': seq_name[0],
								'entry_mode': 'auto',
								'division_id': entry.division_id.id,
								'dep_id': dep_id[0],
								'order_line_id': item.id,
								'pump_model_type': item.pump_model_type,
								'state': 'confirmed'
							}
							
							ms_indent_id = draw_indent_obj.create(cr,uid,draw_indent_vals)
							
							indent_ms = indent_ms + 1
							
						if ms_indent_id:
							
							if ms_indent_item['type'] == 'ms':
								order_ms_id = ms_indent_item['order_bom_id']
								order_ms_acc_id = False
							if ms_indent_item['type'] == 'ms_acc':
								order_ms_id = False
								order_ms_acc_id = ms_indent_item['order_bom_id']
							
							draw_indent_line_obj = self.pool.get('ch.drawing.indent.line')
							
							ms_indent_line_vals = {
							
								'header_id': ms_indent_id,
								'order_ms_id': order_ms_id,
								'order_ms_acc_id': order_ms_acc_id,
								'position_id': ms_indent_item['position_id'],
								'item_code': ms_indent_item['item_code'],
								'item_name': ms_indent_item['item_name'],
							}
							
							draw_indent_line_obj.create(cr,uid,ms_indent_line_vals)
							
							
					### For BOT Items ###
					
					cr.execute(""" select bot.id as order_bom_id,bot.position_id,bot_master.code as item_code,
							bot.item_name as item_name,'bot' as type
							from ch_order_bot_details bot
							left join kg_machine_shop bot_master on bot_master.id = bot.bot_id
							where bot.header_id = %s  and bot.flag_applicable = 't'
							and bot.position_id not in 
							(select position_id from ch_drawing_indent_line)
														
							union
							
							select bot_acc.id as order_bom_id,bot_acc.position_id,bot_acc_master.code as item_code,
							bot_acc.item_name as item_name,'bot_acc' as type
							from ch_wo_accessories_bot bot_acc
							left join kg_machine_shop bot_acc_master on bot_acc_master.id = bot_acc.ms_id
							where bot_acc.header_id = %s  and bot_acc.is_applicable = 't'
							and bot_acc.position_id not in 
							(select position_id from ch_drawing_indent_line)

						 """%(item.id,item.id))
					draw_bot_items = cr.dictfetchall();
					print "draw_ms_items",draw_bot_items
					
					for bot_indent_item in draw_bot_items:
						
						if indent_bot == 1:
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP3')])
					
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.drawing.indent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry.entry_date))
							seq_name = cr.fetchone();

							draw_indent_obj = self.pool.get('kg.drawing.indent')
							
							draw_indent_vals = {
								'name': seq_name[0],
								'entry_mode': 'auto',
								'division_id': entry.division_id.id,
								'dep_id': dep_id[0],
								'order_line_id': item.id,
								'pump_model_type': item.pump_model_type,
								'state': 'confirmed'
							}
							
							bot_indent_id = draw_indent_obj.create(cr,uid,draw_indent_vals)
							
							indent_bot = indent_bot + 1
							
						if bot_indent_id:
							
							if bot_indent_item['type'] == 'bot':
								order_bot_id = bot_indent_item['order_bom_id']
								order_bot_acc_id = False
							if bot_indent_item['type'] == 'bot_acc':
								order_bot_id = False
								order_bot_acc_id = bot_indent_item['order_bom_id']
							
							draw_indent_line_obj = self.pool.get('ch.drawing.indent.line')
							
							bot_indent_line_vals = {
							
								'header_id': bot_indent_id,
								'order_bot_id': order_bot_id,
								'order_bot_acc_id': order_bot_acc_id,
								'position_id': bot_indent_item['position_id'],
								'item_code': bot_indent_item['item_code'],
								'item_name': bot_indent_item['item_name'],
							}
							
							draw_indent_line_obj.create(cr,uid,bot_indent_line_vals)

					for foundry_item in item.line_ids:
						
					
						### Trimming dia creation ###
						if foundry_item.pattern_id.need_dynamic_balancing == True and foundry_item.flag_applicable == True:
							trim_dia_obj = self.pool.get('kg.trimming.dia')
							enq_line_obj = self.pool.get('ch.kg.crm.pumpmodel')
							enq_line_rec = enq_line_obj.browse(cr,uid,item.enquiry_line_id)
							print ":",enq_line_rec.id
							if enq_line_rec.id > 0:
								capacity_in = enq_line_rec.capacity_in
								head_in = enq_line_rec.head_in
								bkw_water = enq_line_rec.bkw_water
								speed_in_rpm = enq_line_rec.speed_in_rpm
								efficiency_in = enq_line_rec.efficiency_in
								motor_kw = enq_line_rec.motor_kw
								old_ref = enq_line_rec.wo_no
							else:
								capacity_in = 0
								head_in = 0
								bkw_water = 0
								speed_in_rpm = 0
								efficiency_in = 0
								motor_kw = 0
								old_ref = ''

							dia_vals = { 
								'order_line_id': item.id,
								'order_bomline_id': foundry_item.id,
								'order_category': item.order_category,		
								'pump_model_type': item.pump_model_type,
								'pump_model_id': item.pump_model_id.id,
								'pattern_id': foundry_item.pattern_id.id,
								'capacity_in': capacity_in,
								'head_in': head_in,
								'bkw_water': bkw_water,
								'speed_in_rpm': speed_in_rpm,
								'efficiency_in': efficiency_in,
								'motor_kw': motor_kw,
								'trimming_dia': item.trimming_dia,
								'old_ref': old_ref,
							}
							trim_dia_obj.create(cr,uid,dia_vals)
							self.pool.get('ch.order.bom.details').write(cr,uid,foundry_item.id,{'flag_trimming_dia':True})
						
					qc_created = 'no'
					print "item",item
					
					### Work Order Number Generation in Line Details
					#~ cr.execute(''' select to_char(%s, 'FMRN') ''',[number])	  
					#~ roman = cr.fetchone()
					#~ order_name = entry.name + '-' + str(roman[0])
					#~ line_obj.write(cr, uid, item.id, {'order_no': order_name})
					#~ number = number + 1

					cr.execute(''' update ch_order_bom_details set state = 'confirmed' where header_id = %s and flag_applicable = 't' ''',[item.id])
					
					rem_qty = item.qty					
					if entry.order_category != 'project'  and entry.stock_check != 'no':
						
						if item.order_category in 'pump':
						
							### Checking the Pump Stock ###
										
							### Checking in Stock Inward for Ready for MS ###
							
							cr.execute(""" select id,available_qty as stock_qty,serial_no,stock_location_id
								from ch_stock_inward_details  
								where pump_model_id = %s
								and foundry_stock_state = 'ready_for_ms' and available_qty > 0 and stock_type = 'pump' and stock_mode = 'manual' 
								order by serial_no """%(item.pump_model_id.id))
							stock_inward_items = cr.dictfetchall();
							print "stock_inward_items",stock_inward_items
							
							if stock_inward_items:
								
								for stock_item in stock_inward_items:
									if rem_qty != 0:
										if stock_item['stock_qty'] != None:
											
											if rem_qty < stock_item['stock_qty']:
												rem_qty = 0
												qc_qty = rem_qty
											else:
												rem_qty = rem_qty
												qc_qty = stock_item['stock_qty']
												
											rem_qty =  rem_qty - stock_item['stock_qty']
											
											### Order Priority ###
													
											#~ if entry.order_category in ('pump','pump_spare','project'):
												#~ if entry.order_priority == 'normal':
													#~ priority = '6'
												#~ if entry.order_priority == 'emergency':
													#~ priority = '4'
											#~ if entry.order_category == 'service':
												#~ priority = '3'
											#~ if entry.order_category == 'spare':
												#~ priority = '5'
												
											if entry.order_category in ('pump','pump_spare','project','access'):
												if entry.order_priority == 'normal':
													priority = '8'
												if entry.order_priority == 'emergency':
													priority = '3'
												if entry.order_priority == 'breakdown':
													priority = '2'
												if entry.order_priority == 'urgent':
													priority = '7'
											if entry.order_category == 'service':
												priority = '4'
											if entry.order_category == 'spare':
												priority = '6'
											
											
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
												'stock_type': 'pump',
												'qc_type': 'foundry',
												'serial_no': stock_item['serial_no'],
												'stock_location_id': stock_item['stock_location_id'],
												'stock_inward_id': stock_item['id']
														
												}
											
											print "qc_vals",qc_vals	
											
											qc_id = qc_obj.create(cr, uid, qc_vals)
											qc_created = 'yes'
											
											### Qty Updation in Stock Inward ###
											
											inward_line_obj = self.pool.get('ch.stock.inward.details')
											
											stock_avail_qty = stock_item['stock_qty'] - qc_qty
											print "stock_avail_qtystock_avail_qty",stock_avail_qty
											if stock_avail_qty == 0:
												inward_line_obj.write(cr, uid, [stock_item['id']],{'available_qty': stock_avail_qty})
											else:
												inward_line_obj.write(cr, uid, [stock_item['id']],{'available_qty': stock_avail_qty})
											
									
					line_obj.write(cr, uid, item.id, {'pump_rem_qty':rem_qty})
					
					print "qc_created",qc_created,rem_qty
					if qc_created == 'no': 
						order_line_ids.append(item.id)
					if qc_created == 'yes' and rem_qty > 0: 
						order_line_ids.append(item.id)
					print "order_line_ids",order_line_ids
					
					#~ if entry.order_priority == 'normal' and entry.order_category in ('spare','service'):
					#~ 
						#~ ### Schedule Creation ###
						#~ 
						#~ schedule_item_vals = {
														#~ 
							#~ 'name': '',
							#~ 'location' : entry.location,
							#~ 'order_priority': 'normal',
							#~ 'delivery_date': entry.delivery_date,
							#~ 'order_line_ids': [(6, 0, order_line_ids)],
							#~ 'state' : 'draft',
							#~ 'entry_mode' : 'auto',				   
						#~ }
						#~ 
						#~ schedule_id = schedule_obj.create(cr, uid, schedule_item_vals)
						#~ 
						#~ ### Schedule Line Item Creation ###
						#~ 
						#~ if item.order_category == 'pump':
						#~ 
							#~ schedule_obj.update_line_items(cr, uid, [schedule_id],rem_qty)
						#~ else:
							#~ schedule_obj.update_line_items(cr, uid, [schedule_id],0)
						#~ 
						#~ ### Schedule Confirmation ###
						#~ 
						#~ schedule_obj.entry_confirm(cr, uid, [schedule_id])
						
				if order_line_ids != []:
					if entry.order_priority in ('emergency','breakdown') and entry.order_category in ('pump','spare','pump_spare','service','access'):
						
						### Schedule Creation ###
						
						schedule_item_vals = {
														
							'name': '',
							'location' : entry.location,
							'order_priority': entry.order_priority,
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
						
					if entry.order_priority in ('emergency','breakdown') and entry.order_category in ('project'):
						
						### Schedule Creation ###
						
						schedule_item_vals = {
														
							'name': '',
							'location' : entry.location,
							'order_priority': entry.order_priority,
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
				else:
					pass
			
			if entry.flag_data_bank == True:
				
				### Assembly Inward Creation ###
				
				for order_item in entry.line_ids:
				
					for accepted_qty in range(order_item.qty):
									
						### Assembly Header Creation ###
						
						ass_header_values = {
							'name': '',
							'order_id': entry.id,
							'order_line_id': order_item.id,
							'pump_model_id': order_item.pump_model_id.id,
							'moc_construction_id': order_item.moc_construction_id.id,
							'state': 'completed',
							'entry_mode': 'auto',
							'qap_plan_id': order_item.qap_plan_id.id,
							'partner_id': entry.partner_id.id,
							'flag_data_bank':entry.flag_data_bank
							}
						assembly_id = assembly_obj.create(cr, uid, ass_header_values)
						print "assembly_id//////////////////////////",assembly_id
						### Assembly Foundry Items Creation ###
						
						order_bom_ids = self.pool.get('ch.order.bom.details').search(cr, uid, [('header_id','=',order_item.id)])
						
						if order_bom_ids:
							for foundry_item in order_bom_ids:
								order_bom_rec = self.pool.get('ch.order.bom.details').browse(cr, uid, foundry_item)
								if order_bom_rec.qty == 1:
									order_bom_qty = order_bom_rec.qty
								if order_bom_rec.qty > 1:
									order_bom_qty = order_bom_rec.qty / order_item.qty
								
								ass_foundry_vals = {
									'header_id': assembly_id,
									'order_bom_id': order_bom_rec.id,
									'order_bom_qty': order_bom_qty,
									'entry_mode': 'auto',
									'state': 'completed'
									}
								print "ass_foundry_vals----------------",ass_foundry_vals
								assembly_foundry_id = assembly_foundry_obj.create(cr, uid, ass_foundry_vals)
							
						### Assembly MS Items Creation ###
						
						order_ms_ids = self.pool.get('ch.order.machineshop.details').search(cr, uid, [('header_id','=',order_item.id)])
						if order_ms_ids:
							for ms_item in order_ms_ids:
								order_ms_rec = self.pool.get('ch.order.machineshop.details').browse(cr, uid, ms_item)
								if order_ms_rec.qty == 1:
									order_ms_qty = order_ms_rec.qty
								if order_ms_rec.qty > 1:
									order_ms_qty = order_ms_rec.qty / order_item.qty
								ass_ms_vals = {
									'header_id': assembly_id,
									'order_ms_id': order_ms_rec.id,
									'order_ms_qty': order_ms_qty,
									'entry_mode': 'auto',
									'state': 'completed',
								}
								print "ass_ms_vals----------------",ass_ms_vals
								assembly_ms_id = assembly_ms_obj.create(cr, uid, ass_ms_vals)	
						
						### Assembly BOT Items Creation ###
						
						order_bot_ids = self.pool.get('ch.order.bot.details').search(cr, uid, [('header_id','=',order_item.id)])
						if order_bot_ids:
							for bot_item in order_bot_ids:
								order_bot_rec = self.pool.get('ch.order.bot.details').browse(cr, uid, bot_item)
								
								if order_bot_rec.qty == 1:
									order_bot_qty = order_bot_rec.qty
								if order_bot_rec.qty > 1:
									order_bot_qty = order_bot_rec.qty / order_item.qty
								ass_bot_vals = {
								'header_id': assembly_id,
								'order_bot_id': order_bot_rec.id,
								'order_bot_qty': order_bot_qty,
								'state': 'completed',
								}
								print "ass_bot_vals----------------",ass_bot_vals
								assembly_bot_id = assembly_bot_obj.create(cr, uid, ass_bot_vals)
				
				
				
				
			cr.execute(''' select sum(unit_price) from ch_work_order_details where header_id = %s ''',[entry.id])	   
			order_value = cr.fetchone()
			self.write(cr, uid, ids, {'order_value':order_value[0],'state': 'confirmed','flag_cancel':1,'confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			cr.execute(''' update ch_work_order_details set state = 'confirmed', flag_cancel='t', schedule_status = 'allow' where header_id = %s ''',[ids[0]])
		else:
			pass
		
		return True
		
			
		
	def prime_cost_update(self,cr,uid,ids,context=None):
		entry_rec = self.browse(cr,uid,ids[0])
		primecost = 0.0
		acc_primecost = 0.0
		total_primecost = 0.0
		acc_total_primecost = 0.0
		overall_primecost = 0.00
		if entry_rec.line_ids:
			for order_item in entry_rec.line_ids:
				if order_item.line_ids:
					for foundry_item in order_item.line_ids:
						if foundry_item.flag_applicable == True:
							foundry_prime_cost = self.pool.get('kg.crm.enquiry')._prime_cost_calculation(cr,uid,'foundry',foundry_item.pattern_id.id,
							0,0,0,order_item.moc_construction_id.id,foundry_item.moc_id.id,0)
							self.pool.get('ch.order.bom.details').write(cr,uid,foundry_item.id,{'wo_prime_cost':foundry_prime_cost * foundry_item.qty })
							primecost = foundry_prime_cost * foundry_item.qty
							total_primecost += primecost
				if order_item.line_ids_a:
					for ms_item in order_item.line_ids_a:
						if ms_item.flag_applicable == True:
							ms_prime_cost = self.pool.get('kg.crm.enquiry')._prime_cost_calculation(cr,uid,'ms',0,
							ms_item.ms_id.id,ms_item,0,order_item.moc_construction_id.id,ms_item.moc_id.id,0)
							self.pool.get('ch.order.machineshop.details').write(cr,uid,ms_item.id,{'wo_prime_cost':ms_prime_cost})
							primecost = ms_prime_cost
							#~ primecost = ms_prime_cost * ms_item.qty
							total_primecost += primecost
				if order_item.line_ids_b:
					for bot_item in order_item.line_ids_b:
						if bot_item.flag_applicable == True:
							bot_prime_cost = self.pool.get('kg.crm.enquiry')._prime_cost_calculation(cr,uid,'bot',0,
							0,0,bot_item.bot_id.id,order_item.moc_construction_id.id,bot_item.moc_id.id,bot_item.brand_id.id)
							self.pool.get('ch.order.bot.details').write(cr,uid,bot_item.id,{'wo_prime_cost':bot_prime_cost * bot_item.qty})
							primecost = bot_prime_cost * bot_item.qty
							total_primecost += primecost
				### For Accessories ###
				if order_item.line_ids_d:
					for acc_item in order_item.line_ids_d:
						for acc_foundry_item in acc_item.line_ids:
							if acc_foundry_item.is_applicable == True:
								acc_foundry_prime_cost = self.pool.get('kg.crm.enquiry')._prime_cost_calculation(cr,uid,'foundry',acc_foundry_item.pattern_id.id,
								0,0,0,order_item.moc_construction_id.id,acc_foundry_item.moc_id.id,0)
								self.pool.get('ch.wo.accessories.foundry').write(cr,uid,acc_foundry_item.id,{'wo_prime_cost':acc_foundry_prime_cost * acc_foundry_item.qty })
								acc_primecost = acc_foundry_prime_cost * acc_foundry_item.qty
								acc_total_primecost += acc_primecost
						for acc_ms_item in acc_item.line_ids_a:
							if acc_ms_item.is_applicable == True:
								acc_ms_prime_cost = self.pool.get('kg.crm.enquiry')._prime_cost_calculation(cr,uid,'ms',0,
								acc_ms_item.ms_id.id,0,0,order_item.moc_construction_id.id,acc_ms_item.moc_id.id,0)
								self.pool.get('ch.wo.accessories.ms').write(cr,uid,acc_ms_item.id,{'wo_prime_cost':acc_ms_prime_cost})
								acc_primecost = acc_ms_prime_cost
								#~ acc_primecost = acc_ms_prime_cost * acc_ms_item.qty
								acc_total_primecost += acc_primecost 
						for acc_bot_item in acc_item.line_ids_b:
							if acc_bot_item.is_applicable == True:
								acc_bot_prime_cost = self.pool.get('kg.crm.enquiry')._prime_cost_calculation(cr,uid,'bot',0,
								0,0,acc_bot_item.ms_id.id,order_item.moc_construction_id.id,acc_bot_item.moc_id.id,0)
								self.pool.get('ch.wo.accessories.bot').write(cr,uid,acc_bot_item.id,{'wo_prime_cost':acc_bot_prime_cost * acc_bot_item.qty})
								acc_primecost = acc_bot_prime_cost * acc_bot_item.qty
								acc_total_primecost += acc_primecost 
					
						
						### Accessories total primecost updation ###
						self.pool.get('ch.wo.accessories').write(cr,uid,acc_item.id,{'wo_prime_cost':acc_total_primecost})
						print "acc_total_primecost640",acc_total_primecost
				
				### For Spare BOM ###
				if order_item.line_ids_e:
					for spare_item in order_item.line_ids_e:
						for spare_foundry_item in spare_item.line_ids:
							if spare_foundry_item.is_applicable == True:
								spare_foundry_prime_cost = self.pool.get('kg.crm.enquiry')._prime_cost_calculation(cr,uid,'foundry',spare_foundry_item.pattern_id.id,
								0,0,0,order_item.moc_construction_id.id,spare_foundry_item.moc_id.id,0)
								self.pool.get('ch.wo.spare.foundry').write(cr,uid,spare_foundry_item.id,{'prime_cost':spare_foundry_prime_cost * spare_foundry_item.qty })
						for spare_ms_item in spare_item.line_ids_a:
							if spare_ms_item.is_applicable == True:
								spare_ms_prime_cost = self.pool.get('kg.crm.enquiry')._prime_cost_calculation(cr,uid,'ms',0,
								spare_ms_item.ms_id.id,spare_ms_item,0,order_item.moc_construction_id.id,spare_ms_item.moc_id.id,0)
								self.pool.get('ch.wo.spare.ms').write(cr,uid,spare_ms_item.id,{'wo_prime_cost':spare_ms_prime_cost})
								#~ self.pool.get('ch.wo.spare.ms').write(cr,uid,spare_ms_item.id,{'wo_prime_cost':spare_ms_prime_cost * spare_ms_item.qty})
						for spare_bot_item in spare_item.line_ids_b:
							if spare_bot_item.is_applicable == True:
								spare_bot_prime_cost = self.pool.get('kg.crm.enquiry')._prime_cost_calculation(cr,uid,'bot',0,
								0,0,spare_bot_item.ms_id.id,order_item.moc_construction_id.id,spare_bot_item.moc_id.id,spare_bot_item.brand_id.id)
								self.pool.get('ch.wo.spare.bot').write(cr,uid,spare_bot_item.id,{'wo_prime_cost':spare_bot_prime_cost * spare_bot_item.qty})
								
						
				### Total Pump primecost ###
				overall_primecost = total_primecost
				print "overall_primecost",overall_primecost
				self.pool.get('ch.work.order.details').write(cr,uid,order_item.id,{'wo_prime_cost':overall_primecost})
		
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
		
		off_obj = self.pool.get('kg.crm.offer').search(cr,uid,[('name','=',rec.offer_no),('state','=','wo_created')])
		if off_obj:
			off_rec = self.pool.get('kg.crm.offer').browse(cr,uid,off_obj[0])
			self.pool.get('kg.crm.offer').write(cr,uid,off_rec.id,{'state': 'moved_to_offer','wo_flag': False})
			self.pool.get('kg.crm.enquiry').write(cr,uid,off_rec.enquiry_id.id,{'state': 'moved_to_offer','wo_flag': False})
				
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
				off_obj = self.pool.get('kg.crm.offer').search(cr,uid,[('name','=',rec.offer_no),('state','=','wo_created')])
				if off_obj:
					off_rec = self.pool.get('kg.crm.offer').browse(cr,uid,off_obj[0])
					self.pool.get('kg.crm.offer').write(cr,uid,off_rec.id,{'state': 'moved_to_offer','wo_flag': False})
					self.pool.get('kg.crm.enquiry').write(cr,uid,off_rec.enquiry_id.id,{'state': 'moved_to_offer','wo_flag': False})
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def create(self, cr, uid, vals, context=None):

		if vals.get('state') == 'draft' and vals.get('entry_mode') == 'manual':
			design_flag = True
		else:
			design_flag = False
		vals.update({
		'design_flag': design_flag,
		})
		return super(kg_work_order, self).create(cr, uid, vals, context=context)
		
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
		'unit_price': fields.float('WO Value',required=True),
		### Used for Schedule Purpose
		'schedule_status':fields.selection([('allow','Allow to Schedule'),('not_allow','Not Allow to Schedule'),('completed','Schedule Completed')],'Schedule Status', readonly=True),
		'moc_construction_id':fields.many2one('kg.moc.construction','MOC Construction Code',domain="[('active','=','t')]"),
		'moc_construction_name':fields.related('moc_construction_id','name', type='char', string='MOC Construction Name.', store=True, readonly=True),
		### Used for VO ###
		'rpm': fields.selection([('1450','1450'),('2900','2900')],'RPM', required=True),
		'setting_height':fields.float('Setting Height (MM)',required=True),
		'bed_length':fields.float('Bed Length(MM)',required=True),
		'shaft_sealing': fields.selection([('g_p','Gland packing'),('m_s','Mechanical Seal'),('f_s','Felt Seal'),('d_s','Dynamic seal')],'Shaft Sealing',required=True),
		#~ 'motor_power':fields.float('Motor Power',required=True),
		'motor_power': fields.selection([('90','90'),('100','100'),('112','112'),('132','132'),('160','160'),('180','180'),('200','200'),('225','225'),
				('250','250'),('280','280'),('315','315'),('315_l','315L')],'Motor Frame size',required=True),
				
		'm_power': fields.float('Motor power in KW'),
		
		#~ 'bush_bearing': fields.selection([('grease','Grease'),('cft_ext','CFT-EXT'),
			#~ ('cft_self','CFT-SELF'),('cut_less_rubber','Cut less Rubber')],'Bush Bearing',required=True),
			
		'bush_bearing': fields.selection([('grease','Bronze'),('cft_self','CFT'),('cut_less_rubber','Cut less Rubber')],'Bush Bearing',required=True),
		#~ 'delivery_pipe_size':fields.float('Delivery Pipe Size(MM)',required=True),
		'delivery_pipe_size': fields.selection([('32','32'),('40','40'),('50','50'),('65','65'),('80','80'),('100','100'),('125','125'),('150','150'),('200','200'),('250','250'),('300','300')],'Delivery Pipe Size(MM)',required=True),
		
		'lubrication': fields.selection([('grease','Grease'),('cft_ext','External'),
			('cft_self','Self'),('cut_less_rubber','External Under Pressure')],'Bush bearing Lubrication',required=True),
			
			
		'flag_load_bom': fields.boolean('Load BOM'),
		'flag_offer': fields.boolean('WO from Offer'),
		### Used for Dynamic Length Calculation
		'bp':fields.float('BP',required=True),
		'shaft_ext':fields.float('Shaft Ext',required=True),
		'flag_for_stock': fields.boolean('For Stock'),
		### Offer Details ####
		'pump_offer_line_id': fields.integer('Pump Offer'),
		'enquiry_line_id': fields.integer('Enquiry Line Id'),
		'line_ids_d': fields.one2many('ch.wo.accessories', 'header_id', "Accessories"),
		'drawing_approval': fields.selection([('yes','Yes'),('no','No')],'Drawing approval'),
		'inspection': fields.selection([('yes','Yes'),('no','No'),('tpi','TPI'),('customer','Customer'),('consultant','Consultant'),('stagewise','Stage wise')],'Inspection'),
		
		
		## QAP ##
		'qap_plan_id': fields.many2one('kg.qap.plan', 'QAP Standard',required=True),
		### Prime Cost ###
		'wo_prime_cost': fields.float('WO PC'),
		'mar_prime_cost': fields.float('Marketing PC'),
		'flange_standard': fields.many2one('ch.pumpseries.flange','Flange Standard',),
		'trimming_dia': fields.char('Trimming Dia'),
		'cc_drill': fields.selection([('basic_design','BASIC DESIGN'),('basic_design_a','BASIC DESIGN+A'),
			('basic_design_c','BASIC DESIGN+C'),('nill','NILL')],' C.C. Drill'),
		'order_summary': fields.char('Order Summary'),
		'line_ids_e': fields.one2many('ch.wo.spare.bom', 'header_id', "Spare BOM"),
		'suction_spool': fields.integer('Suction Spool'),
		'flag_select_all': fields.boolean('Select All'),
		'pumpseries_id': fields.many2one('kg.pumpseries.master', 'Pump Series'),
		
	}
	
	
	_defaults = {
	
		'state': 'draft',
		'schedule_status': 'allow',
		'delivery_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'flag_load_bom':False,
		'flag_for_stock':False,
		'flag_offer':False,
		'flag_select_all':False,
		
	}
	
	
	def default_get(self, cr, uid, fields, context=None):
		#~ order_obj = self.pool.get('kg.work.order')
		#~ for line_dict in order_obj.resolve_2many_commands(cr, uid, 'line_ids', context.get('line_ids'), context=context):
			#~ print "line_dict",line_dict
			#~ print "line_dict.get('order_no'),",line_dict.get('order_no'),type(line_dict.get('order_no')),str(line_dict.get('order_no'))
			#~ context.update({
				#~ 'order_no': line_dict.get('order_no'),
			#~ })
		if len(context)>5:
			if context['order_category'] == 'pump':
				context['flag_select_all'] = True
			if context['order_category'] == 'spare':
				context['flag_select_all'] = False
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
		
	def onchange_bom_details(self, cr, uid, ids, flag_load_bom ,pump_model_id, qty,moc_construction_id, order_category,flag_standard,
		rpm,setting_height,shaft_sealing,motor_power,bush_bearing,delivery_pipe_size,lubrication,unit_price,delivery_date,note,pump_model_type,flag_offer,flag_select_all):
		
		
		bom_vals=[]
		machine_shop_vals=[]
		bot_vals=[]
		consu_vals=[]
		ch_ms_vals = []
		moc_obj = self.pool.get('kg.moc.master')
		flag_select_all_val = flag_select_all
		if flag_load_bom == True:
			if flag_offer != True:
				if pump_model_id != False:
					
					pump_model_rec = self.pool.get('kg.pumpmodel.master').browse(cr, uid, pump_model_id)
					
					flag_select_all_val = flag_select_all
					
					if order_category == 'pump':
						flag_select_all_val = True
					if flag_select_all == True:
						flag_select_all_val = True
					if order_category == 'pump' and flag_select_all == False:
						flag_select_all_val = False
					
					
						
					#### Loading Foundry Items
					
					order_bom_obj = self.pool.get('ch.order.bom.details')
					cr.execute(''' select bom.id,bom.header_id,bom.pattern_id,bom.pattern_name,bom.qty, bom.pos_no,bom.position_id,pattern.pcs_weight, pattern.ci_weight,pattern.nonferous_weight
							from ch_bom_line as bom
							LEFT JOIN kg_pattern_master pattern on pattern.id = bom.pattern_id
							where bom.header_id = (select id from kg_bom where pump_model_id = %s and active='t' and category_type = 'pump_bom') 
							order by bom.header_id ''',[pump_model_id])
					bom_details = cr.dictfetchall()
					
					
					for bom_details in bom_details:
						if bom_details['position_id'] == None:
							raise osv.except_osv(_('Warning!'),
							_('Kindly Configure Position No. in Foundry Items for respective Pump Bom and proceed further !!'))
						
							
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
							
							if not moc_rec.line_ids:
								raise osv.except_osv(_('Warning!'),
										_('Raw material are not mapped for MOC %s !!')%(moc_rec.name))
								
						if flag_select_all_val == True:
							applicable = True
						else:
							flag_select_all_val = False
							applicable = False	
							
							
						#~ if order_category == 'pump' and flag_select_all != True:
							#~ aplicable = False
							#~ flag_select_all_val = False
						#~ if order_category == 'pump' and flag_select_all == True:
							#~ aplicable = True
							#~ flag_select_all_val = True
						#~ else:
							#~ aplicable = False
							#~ flag_select_all_val = False
							
							
						bom_vals.append({
															
							'bom_id': bom_details['header_id'],
							'bom_line_id': bom_details['id'],
							'pattern_id': bom_details['pattern_id'],
							'pattern_name': bom_details['pattern_name'],						
							'off_name': bom_details['pattern_name'],						
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
							where header_id = (select id from kg_bom where pump_model_id = %s and active='t' and category_type = 'pump_bom') 
							order by header_id ''',[pump_model_id])
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
							
						### Loading MOC from MOC Construction
						
						if moc_construction_id != False:
							print "bom_ms_details['ms_id'],moc_construction_id",bom_ms_details['ms_id'],moc_construction_id
							cr.execute(''' select machine_moc.moc_id
								from ch_machine_mocwise machine_moc
								LEFT JOIN kg_moc_construction const on const.id = machine_moc.code
								where machine_moc.header_id = %s and const.id = %s ''',[bom_ms_details['ms_id'],moc_construction_id])
							const_moc_id = cr.fetchone()
							if const_moc_id != None:
								moc_id = const_moc_id[0]
							else:
								moc_id = False
						else:
							moc_id = False
							
						if flag_select_all_val == True:
							applicable = True
						else:
							flag_select_all_val = False
							applicable = False
							
						ms_rec = self.pool.get('kg.machine.shop').browse(cr,uid,bom_ms_details['ms_id'])
						if ms_rec.line_ids:
							ch_ms_vals = []
							for raw in ms_rec.line_ids:
								ch_ms_vals.append([0, 0,{
										'product_id': raw.product_id.id,
										'uom': raw.uom.id,
										'od': raw.od,
										'length': raw.length,
										'breadth': raw.breadth,
										'thickness': raw.thickness,
										'weight': raw.weight * bom_ms_qty,
										'uom_conversation_factor': raw.uom_conversation_factor,
										'temp_qty': raw.temp_qty * bom_ms_qty,
										'qty': raw.qty * bom_ms_qty,
										'remarks': raw.remarks,
										}])
						
						if ch_ms_vals == []:
							raise osv.except_osv(_('Warning!'),
									_('Raw material are not mapped for MS Item %s !!')%(bom_ms_details['name']))
							
						machine_shop_vals.append({
							
							'pos_no': bom_ms_details['pos_no'],
							'position_id': bom_ms_details['position_id'],
							'bom_id': bom_ms_details['bom_id'],
							'ms_id': bom_ms_details['ms_id'],
							'name': bom_ms_details['name'],
							'off_name': bom_ms_details['name'],
							'qty': bom_ms_qty,
							'indent_qty':bom_ms_qty,
							'flag_applicable' : applicable,
							'flag_standard':flag_standard,
							'entry_mode':'auto',
							'order_category':	order_category,
							'moc_id': moc_id,
							'line_ids': ch_ms_vals,
									  
							})
							
					#### Loading BOT Details
					
					bom_bot_obj = self.pool.get('ch.bot.details')
					cr.execute(''' select id,position_id,bot_id,qty,header_id as bom_id
							from ch_bot_details
							where header_id = (select id from kg_bom where pump_model_id = %s and  active='t' and category_type = 'pump_bom') 
							order by header_id ''',[pump_model_id])
					bom_bot_details = cr.dictfetchall()
					for bom_bot_details in bom_bot_details:
						if bom_bot_details['position_id'] == None:
							bom_bot_details['position_id'] = False
						if qty == 0:
							bom_bot_qty = bom_bot_details['qty']
						if qty > 0:
							bom_bot_qty = qty * bom_bot_details['qty']
							
						bot_obj = self.pool.get('kg.machine.shop')
						bot_rec = bot_obj.browse(cr, uid, bom_bot_details['bot_id'])
						
						### Loading MOC from MOC Construction
						
						if moc_construction_id != False:
							
							cr.execute(''' select bot_moc.moc_id
								from ch_machine_mocwise bot_moc
								LEFT JOIN kg_moc_construction const on const.id = bot_moc.code
								where bot_moc.header_id = %s and const.id = %s ''',[bom_bot_details['bot_id'],moc_construction_id])
							const_moc_id = cr.fetchone()
							if const_moc_id != None:
								moc_id = const_moc_id[0]
							else:
								moc_id = False
						else:
							moc_id = False
							
						if flag_select_all_val == True:
							applicable = True
						else:
							flag_select_all_val = False
							applicable = False
							
						if not bot_rec.line_ids:
							raise osv.except_osv(_('Warning!'),
									_('Raw material are not mapped for BOT Item %s !!')%(bot_rec.name))
							
						bot_vals.append({
							
							'bot_line_id': bom_bot_details['id'],
							'bom_id': bom_bot_details['bom_id'],							
							'position_id': bom_bot_details['position_id'],							
							'bot_id': bom_bot_details['bot_id'],
							'item_name': bot_rec.name,
							'off_name': bot_rec.name,
							'qty': bom_bot_qty,
							'flag_applicable' : applicable,
							'flag_standard':flag_standard,
							'entry_mode':'auto',
							'order_category':order_category,
							'flag_is_bearing': bot_rec.is_bearing,
							'moc_id': moc_id,
									  
							})
								
						
					bed_bom_obj = self.pool.get('ch.order.bom.details')
					
					
					if rpm != False:
						
						
						if shaft_sealing != False and motor_power != False and bush_bearing != False and setting_height > 0 and delivery_pipe_size != False and lubrication != False:
							
							#### Load Foundry Items ####
							
							if setting_height < 3000:
								limitation = 'upto_3000'
							if setting_height >= 3000:
								limitation = 'above_3000'
								
							### For Base Plate ###
							if setting_height < 3000:
								base_limitation = 'upto_2999'
							if setting_height >= 3000:
								base_limitation = 'above_3000'

							cr.execute('''
							
								
								(-- Bed Assembly ----
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
								
								order by bom.header_id)
								 
								
								union all


								(--- Motor Assembly ---
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
								
								order by bom.header_id)
								
								

								union all


								(-- Column Pipe ------

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
								
								order by bom.header_id)
								
						

								union all


								(-- Delivery Pipe ------

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
								
								order by bom.header_id)
								
								

								union all


								(-- Lubrication ------

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
								
								order by bom.header_id)
								
								union all
								
								(-- Base Plate --
										
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
								where id = (select partlist_id from ch_base_plate
								where limitation = %s and header_id = (select id from kg_bom where pump_model_id = %s and active='t' and category_type = 'pump_bom'))
								and active='t'
								)
								
								order by bom.header_id)

								  ''',[limitation,shaft_sealing,rpm,pump_model_id,motor_power,rpm,pump_model_id,
								  bush_bearing,setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,delivery_pipe_size,
								  setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,lubrication,setting_height,setting_height,
								  rpm,pump_model_id,rpm,pump_model_id,base_limitation,pump_model_id])
							vertical_foundry_details = cr.dictfetchall()
							
							if order_category in ('pump','spare') :
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
									
									print "vertical_foundry['header_id']",vertical_foundry['header_id']
									if vertical_foundry['position_id'] == None:
										raise osv.except_osv(_('Warning!'),
										_('Kindly Configure Position No. in Foundry Items for respective Pump Bom and proceed further !!'))
									
									if flag_select_all_val == True:
										applicable = True
									else:
										flag_select_all_val = False
										applicable = False	
										
									bom_vals.append({
																		
										'bom_id': vertical_foundry['header_id'],
										'bom_line_id': vertical_foundry['id'],
										'pattern_id': vertical_foundry['pattern_id'],
										'pattern_name': vertical_foundry['pattern_name'],						
										'off_name': vertical_foundry['pattern_name'],						
										'weight': wgt or 0.00,								  
										'pos_no': vertical_foundry['pos_no'],
										'position_id': vertical_foundry['position_id'],			  
										'qty' : bom_qty,				   
										'indent_qty' : bom_qty,				   
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
										
										(-- Bed Assembly ----
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
										
										order by header_id)
										
									

										union all


										(--- Motor Assembly ---
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
										
										order by header_id)
										

										union all


										(-- Column Pipe ------

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
										
										order by header_id)
										
								

										union all


										(-- Delivery Pipe ------

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
										
										order by header_id)
										

										union all


										(-- Lubrication ------

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
										
										order by header_id)
										
										union all
										
										(-- Base Plate --
										
										select id,pos_no,position_id,ms_id,name,qty,header_id as bom_id
										from ch_machineshop_details
										where header_id = 
										(
										select id from kg_bom 
										where id = (select partlist_id from ch_base_plate 
										where limitation = %s and header_id = (select id from kg_bom where pump_model_id = %s and active='t' and category_type = 'pump_bom') )
										and active='t'
										) 
										
										order by header_id)

								  ''',[limitation,shaft_sealing,rpm,pump_model_id,motor_power,rpm,pump_model_id,
								  bush_bearing,setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,delivery_pipe_size,
								  setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,lubrication,setting_height,setting_height,
								  rpm,pump_model_id,rpm,pump_model_id,base_limitation,pump_model_id])
							vertical_ms_details = cr.dictfetchall()
							for vertical_ms_details in vertical_ms_details:
								
								### Loading MOC from MOC Construction
						
								if moc_construction_id != False:
									
									cr.execute(''' select machine_moc.moc_id
										from ch_machine_mocwise machine_moc
										LEFT JOIN kg_moc_construction const on const.id = machine_moc.code
										where machine_moc.header_id = %s and const.id = %s ''',[vertical_ms_details['ms_id'],moc_construction_id])
									const_moc_id = cr.fetchone()
									if const_moc_id != None:
										moc_id = const_moc_id[0]
									else:
										moc_id = False
								else:
									moc_id = False
										
									
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
											number_dec = str(length-int(length))[1:]
											if number_dec >= 0.25:
												length = roundPartial (length, 0.50)
											else:
												length = length
											
										if star_value == 1:
											### Formula ###
											#(ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-3)/2
											###
											length = (h_value + bp + setting_height - a_value - b_value - 3)/2
											number_dec = str(length-int(length))[1:]
											if number_dec >= 0.25:
												length = roundPartial (length, 0.50)
											else:
												length = length
											
										if star_value > 1:
											### Formula ###
											#(ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-1.5)-(NO OF STAR SUPPORT*1.5)/NO OF STAR SUPPORT+1
											###
											length = ((h_value+bp+setting_height-a_value-b_value-1.5)-(star_value*1.5))/(star_value+1)
											number_dec = str(length-int(length))[1:]
											if number_dec >= 0.25:
												length = roundPartial (length, 0.50)
											else:
												length = length
											
									if ms_rec.length_type == 'delivery_pipe_middle':
										if star_value == 0.0:
											### Formula ###
											#ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-1.5
											###
											length = h_value + bp + setting_height - a_value - b_value - 1.5
											number_dec = str(length-int(length))[1:]
											if number_dec >= 0.25 and number_dec <= 0.75:
												length = round(length, 0)
											if number_dec >= 0.75:
												length = round(length, 0)
												frac, whole = math.modf(length)
												if frac >= 0.5:
													length = (whole+0.5)
												elif frac < 0.5:
													length = (whole+0.0)
											else:
												length = length
											
										if star_value == 1:
											### Formula ###
											#(ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-3)/2
											###
											length = (h_value + bp + setting_height - a_value - b_value - 3)/2
											number_dec = str(length-int(length))[1:]
											if number_dec >= 0.25 and number_dec < 0.75:
												length = round(length, 0)
											if number_dec >= 0.75:
												frac, whole = math.modf(length)
												if frac >= 0.5:
													length = (whole+0.5)
												elif frac < 0.5:
													length = (whole+0.0)
											else:
												length = length
											
										if star_value > 1:
											### Formula ###
											#(ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-1.5)-(NO OF STAR SUPPORT*1.5)/NO OF STAR SUPPORT+1
											###
											length = ((h_value+bp+setting_height-a_value-b_value-1.5)-(star_value*1.5))/(star_value+1)
											number_dec = str(length-int(length))[1:]
											if number_dec >= 0.25 and number_dec < 0.75:
												length = round(length, 0)
											if number_dec >= 0.75:
												frac, whole = math.modf(length)
												if frac >= 0.5:
													length = (whole+0.5)
												elif frac < 0.5:
													length = (whole+0.0)
											else:
												length = length
											
									if ms_rec.length_type == 'drive_column_pipe':
										
										if star_value == 1:
											### Formula ###
											#(3.5+bp+setting height-a1-no of star support)/2
											###
											length = (3.5+bp+setting_height-a1_value-vo_star_value['star'])/2
											number_dec = str(length-int(length))[1:]
											if number_dec >= 0.25:
												length = roundPartial (length, 0.50)
											else:
												length = length
											
											
										if star_value > 1:
											### Formula ###
											#(3.5+bp+setting height-a1-(No. of star support * star support value)-((No. Of star support-1) * LINE COLUMN PIPE value))/2
											###
											### Calculating Line Column Pipe ###
											### Formula = Standard Length ###
											line_column_pipe = vo_star_value['lcp']
											length = (3.5+bp+setting_height-a1_value-(star_value * vo_star_value['star'])-((star_value-1)*line_column_pipe))/2
											number_dec = str(length-int(length))[1:]
											if number_dec >= 0.25:
												length = roundPartial (length, 0.50)
											else:
												length = length
											
									if ms_rec.length_type == 'pump_column_pipe':
										
										if star_value == 1:
											### Formula ###
											#(3.5+bp+setting height-a1-no of star support)/2
											###
											length = (3.5+bp+setting_height-a1_value-vo_star_value['star'])/2
											number_dec = str(length-int(length))[1:]
											if number_dec >= 0.25 and number_dec < 0.75:
												length = round(length, 0)
											if number_dec >= 0.75:
												frac, whole = math.modf(length)
												if frac >= 0.5:
													length = (whole+0.5)
												elif frac < 0.5:
													length = (whole+0.0)
											else:
												length = length
											
											
										if star_value > 1:
											### Formula ###
											#(3.5+bp+setting height-a1-no of star support-NO OF LINE COLUMN PIPE)/2
											###
											### Calculating Line Column Pipe ###
											### Formula = Standard Length ###
											line_column_pipe = vo_star_value['lcp']
											length = (3.5+bp+setting_height-a1_value-(star_value * vo_star_value['star'])-((star_value-1)*line_column_pipe))/2
											number_dec = str(length-int(length))[1:]
											if number_dec >= 0.25 and number_dec < 0.75:
												length = round(length, 0)
											if number_dec >= 0.75:
												frac, whole = math.modf(length)
												if frac >= 0.5:
													length = (whole+0.5)
												elif frac < 0.5:
													length = (whole+0.0)
											else:
												length = length
											
											
									if ms_rec.length_type == 'pump_shaft':
										
										if star_value == 1:
											### Formula ###
											#(STAR SUPPORT/2-1)+PUMP COLOUMN PIPE+A2
											###
											pump_column_pipe = (3.5+bp+setting_height-a1_value-vo_star_value['star'])/2
											number_dec = str(length-int(pump_column_pipe))[1:]
											if number_dec >= 0.25 and number_dec < 0.75:
												pump_column_pipe = round(pump_column_pipe, 0)
											if number_dec >= 0.75:
												frac, whole = math.modf(pump_column_pipe)
												if frac >= 0.5:
													pump_column_pipe = (whole+0.5)
												elif frac < 0.5:
													pump_column_pipe = (whole+0.0)
											else:
												pump_column_pipe = pump_column_pipe
											length = (star_value/2-1)+pump_column_pipe+a2_value
											
											
										if star_value > 1:
											### Formula ###
											#(STAR SUPPORT/2-1)+PUMP COLOUMN PIPE+A2
											###
											line_column_pipe = vo_star_value['lcp']
											pump_column_pipe = (3.5+bp+setting_height-a1_value-(star_value * vo_star_value['star'])-((star_value-1)*line_column_pipe))/2
											number_dec = str(length-int(pump_column_pipe))[1:]
											if number_dec >= 0.25 and number_dec < 0.75:
												pump_column_pipe = round(pump_column_pipe, 0)
											if number_dec >= 0.75:
												frac, whole = math.modf(pump_column_pipe)
												if frac >= 0.5:
													pump_column_pipe = (whole+0.5)
												elif frac < 0.5:
													pump_column_pipe = (whole+0.0)
											else:
												pump_column_pipe = pump_column_pipe
											
											length = ((vo_star_value['star']/2)-1)+pump_column_pipe+a2_value
											
									if ms_rec.length_type == 'drive_shaft':
										
										if star_value == 1:
											### Formula ###
											#(STAR SUPPORT/2-1)+DRIVE COLOUMN PIPE-3.5+SHAFT EXT
											###
											drive_col_pipe = (3.5+bp+setting_height-a1_value-vo_star_value['star'])/2
											number_dec = str(length-int(drive_col_pipe))[1:]
											if number_dec >= 0.25:
												drive_col_pipe = roundPartial (drive_col_pipe, 0.50)
											else:
												drive_col_pipe = drive_col_pipe
											length = (star_value/2-1)+drive_col_pipe-3.5+shaft_ext
											
										if star_value > 1:
											### Formula ###
											#(STAR SUPPORT/2-1)+DRIVE COLOUMN PIPE-3.5+SHAFT EXT
											###
											line_column_pipe = vo_star_value['lcp']
											drive_col_pipe = (3.5+bp+setting_height-a1_value-(star_value * vo_star_value['star'])-((star_value-1)*line_column_pipe))/2
											number_dec = str(length-int(drive_col_pipe))[1:]
											if number_dec >= 0.25:
												drive_col_pipe = roundPartial (drive_col_pipe, 0.50)
											else:
												drive_col_pipe = drive_col_pipe
											length = ((vo_star_value['star']/2)-1)+drive_col_pipe-3.5+shaft_ext
								
								print "length---------------------------->>>>",length
								if length > 0:
									ms_bom_qty = length
									flag_dynamic_length = True
								else:
									ms_bom_qty = 0
									flag_dynamic_length = False
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
									
								
								if flag_select_all_val == True:
									applicable = True
								else:
									flag_select_all_val = False
									applicable = False	
								
								ms_rec = self.pool.get('kg.machine.shop').browse(cr,uid,vertical_ms_details['ms_id'])
								if ms_rec.line_ids:
									ch_ms_vals = []
									for raw in ms_rec.line_ids:
										ch_ms_vals.append([0, 0,{
												'product_id': raw.product_id.id,
												'uom': raw.uom.id,
												'od': raw.od,
												'length': raw.length,
												'breadth': raw.breadth,
												'thickness': raw.thickness,
												'weight': raw.weight * qty * vertical_ms_details['qty'],
												'uom_conversation_factor': raw.uom_conversation_factor,
												'temp_qty': raw.temp_qty * qty * vertical_ms_details['qty'],
												'qty': raw.qty * qty * vertical_ms_details['qty'],
												'remarks': raw.remarks,
												}])
								
								
								machine_shop_vals.append({
									
									'pos_no':pos_no,
									'position_id':vertical_ms_details['position_id'],						
									'ms_line_id': vertical_ms_details['id'],
									'bom_id': vertical_ms_details['bom_id'],
									'ms_id': vertical_ms_details['ms_id'],
									'name': vertical_ms_details['name'],
									'off_name': vertical_ms_details['name'],
									'qty': qty * vertical_ms_details['qty'],
									'indent_qty': qty * vertical_ms_details['qty'],
									'length': vertical_ms_qty,
									'flag_applicable' : applicable,
									'flag_standard':flag_standard,
									'entry_mode':'auto',
									'order_category':	order_category,
									'moc_id': moc_id,
									'flag_dynamic_length': flag_dynamic_length
									
											  
									})
							
							
							#### Load BOT Items ####
							
							bom_bot_obj = self.pool.get('ch.machineshop.details')
							cr.execute(''' 
										
										(-- Bed Assembly ----
										select id,bot_id,position_id,qty,header_id as bom_id
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
										order by header_id)
										
										union all


										(--- Motor Assembly ---
										select id,bot_id,position_id,qty,header_id as bom_id
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
										order by header_id)
										
										union all


										(-- Column Pipe ------

										select id,bot_id,position_id,qty,header_id as bom_id
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
										order by header_id)
										
										union all


										(-- Delivery Pipe ------

										select id,bot_id,position_id,qty,header_id as bom_id
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
										order by header_id)
										
										union all


										(-- Lubrication ------

										select id,bot_id,position_id,qty,header_id as bom_id
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
										order by header_id)
										
										union all
										
										(-- Base Plate --
										
										select id,bot_id,position_id,qty,header_id as bom_id
										from ch_bot_details
										where header_id =
										(
										select id from kg_bom 
										where id = (select partlist_id from ch_base_plate 
										where limitation = %s and header_id = (select id from kg_bom where pump_model_id = %s and active='t' and category_type = 'pump_bom') )
										and active='t'
										) 
										order by header_id)
										

								  ''',[limitation,shaft_sealing,rpm,pump_model_id,motor_power,rpm,pump_model_id,
								  bush_bearing,setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,delivery_pipe_size,
								  setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,lubrication,setting_height,setting_height,
								  rpm,pump_model_id,rpm,pump_model_id,base_limitation,pump_model_id])
							vertical_bot_details = cr.dictfetchall()
							
							for vertical_bot_details in vertical_bot_details:
								
								### Loading MOC from MOC Construction
						
								if moc_construction_id != False:
									
									cr.execute(''' select bot_moc.moc_id
										from ch_machine_mocwise bot_moc
										LEFT JOIN kg_moc_construction const on const.id = bot_moc.code
										where bot_moc.header_id = %s and const.id = %s ''',[vertical_bot_details['bot_id'],moc_construction_id])
									const_moc_id = cr.fetchone()
									if const_moc_id != None:
										moc_id = const_moc_id[0]
									else:
										moc_id = False
								else:
									moc_id = False
								if qty == 0:
									vertical_bot_qty = vertical_bot_details['qty']
								if qty > 0:
									vertical_bot_qty = qty * vertical_bot_details['qty']
									
								bot_obj = self.pool.get('kg.machine.shop')
								bot_rec = bot_obj.browse(cr, uid, vertical_bot_details['bot_id'])
								
								
								if flag_select_all_val == True:
									applicable = True
								else:
									flag_select_all_val = False
									applicable = False	
								
								bot_vals.append({
									
									'bot_line_id': vertical_bot_details['id'],
									'bom_id': vertical_bot_details['bom_id'],							
									'bot_id': vertical_bot_details['bot_id'],
									'item_name': bot_rec.name,
									'off_name': bot_rec.name,
									'position_id': vertical_bot_details['position_id'] or False,	
									'qty': vertical_bot_qty,
									'flag_applicable' : applicable,
									'flag_standard':flag_standard,
									'entry_mode':'auto',
									'order_category':	order_category,
									'flag_is_bearing': bot_rec.is_bearing,
									'moc_id': moc_id
											  
									})
						
				if order_category in ('spare','pump_spare'):
					header_qty = 1
				else:
					header_qty = qty
				return {'value': {'qty':header_qty,'flag_select_all':flag_select_all_val,'line_ids': bom_vals,'line_ids_a':machine_shop_vals,'line_ids_b':bot_vals,'line_ids_c':consu_vals}}
			else:
				return True
		else:
			return {'value': {'flag_select_all':flag_select_all_val,'line_ids': bom_vals,'line_ids_a':machine_shop_vals,'line_ids_b':bot_vals,'line_ids_c':consu_vals}}
			
	
	
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
		
	def _check_flag_applicable(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.order_category == 'spare' and entry.header_id.entry_mode != 'auto':
			if entry.line_ids:
				cr.execute(''' select id from ch_order_bom_details where flag_applicable = 't' and
					header_id = %s ''',[entry.id])
				applicable_id = cr.fetchone()
				if not applicable_id:
					return False
		return True
		
		
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
		#~ (_check_flag_applicable, 'Kindly select atleast one Foundry Item for spare !! ', ['']),
	   
		
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
		'bom_type': fields.selection([('pump','Pump'),('spare','Spare')],'BOM Type'),
		'spare_bom_id': fields.many2one('ch.wo.spare.foundry','Spare Foundry Id'),
		'spare_id': fields.many2one('ch.wo.spare.bom','Spare Foundry Id'),
		
		### Offer Details ###
		'spare_offer_line_id': fields.integer('Spare Offer'),
		### Prime Cost ###
		'wo_prime_cost': fields.float('WO PC'),
		'mar_prime_cost': fields.float('Marketing PC'),
		'flag_trimming_dia': fields.boolean('Trimming Dia'),
		'material_code': fields.char('Material Code'),
		
		'sequence_no': fields.integer('Sequence No.'),
		'off_name': fields.char('Offer Name'),
	
	}
	
	_defaults = {
		
		
		'state': 'draft',
		'flag_pattern_check': False,
		'entry_mode': 'manual',
		'flag_trimming_dia': False
		
	}
	
	
	def default_get(self, cr, uid, fields, context=None):
		
		context.update({'entry_mode': 'manual','flag_applicable': True})
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
		'indent_qty': fields.integer('Indent Creation Qty'),
		### Offer Details ###
		'spare_offer_line_id': fields.integer('Spare Offer'),
		### Prime Cost ###
		'wo_prime_cost': fields.float('WO PC'),
		'mar_prime_cost': fields.float('Marketing PC'),
		'material_code': fields.char('Material Code'),
		'flag_dynamic_length': fields.boolean('Dynamic Length'),
		
		'sequence_no': fields.integer('Sequence No.'),
		'line_ids': fields.one2many('ch.wo.ms.raw', 'header_id', 'MS Raw'),
		'off_name': fields.char('Offer Name'),
		'bom_type': fields.selection([('pump','Pump'),('spare','Spare')],'BOM Type'),
		'spare_bom_id': fields.many2one('ch.wo.spare.ms','Spare MS Id'),
		'spare_id': fields.many2one('ch.wo.spare.bom','Spare  Id'),
	
	}  
	
	_defaults = {
		
		'entry_mode':'manual', 
		'flag_dynamic_length':False, 
		
	}
	
	def onchange_qty(self, cr, uid, ids, qty):
		return {'value': {'indent_qty': qty}}
	
	def default_get(self, cr, uid, fields, context=None):
		
		context.update({'entry_mode': 'manual','flag_applicable': True})
		return context
		
	def create(self, cr, uid, vals, context=None):
		return super(ch_order_machineshop_details, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_order_machineshop_details, self).write(cr, uid, ids, vals, context)   

ch_order_machineshop_details()


class ch_wo_ms_raw(osv.osv):
	
	_name = "ch.wo.ms.raw"
	_description = "Ch wo raw Details"
	
	_columns = {
		
		### Basic Info
		
		'header_id':fields.many2one('ch.order.machineshop.details', 'MS', ondelete='cascade'),
		'remarks': fields.char('Remarks'),
		'active': fields.boolean('Active'),	
		
		### Module Requirement
		
		'product_id': fields.many2one('product.product','Raw Material',domain="[('product_type','in',['ms','bot','consu','coupling'])]"),			
		'uom':fields.many2one('product.uom','UOM',size=128 ),
		'od': fields.float('OD'),
		'length': fields.float('Length'),
		'breadth': fields.float('Breadth'),
		'thickness': fields.float('Thickness'),
		'weight': fields.float('Weight' ,digits=(16,5)),
		'uom_conversation_factor': fields.selection([('one_dimension','One Dimension'),('two_dimension','Two Dimension')],'UOM Conversation Factor'),		
		'temp_qty':fields.float('Qty'),
		'qty':fields.float('Testing Qty',readonly=True),
		'spare_raw_id': fields.many2one('ch.wo.spare.ms.raw','MS Spare'),
		
	}
	
	_defaults = {
		
		'active': True,
		
	}
	
	def onchange_weight(self, cr, uid, ids, uom_conversation_factor,length,breadth,temp_qty,product_id, context=None):		
		value = {'qty': '','weight': '',}
		prod_rec = self.pool.get('product.product').browse(cr,uid,product_id)
		qty_value = 0.00
		weight=0.00
		if uom_conversation_factor == 'one_dimension':	
			if prod_rec.uom_id.id == prod_rec.uom_po_id.id:
				qty_value = length * temp_qty
				weight = 0.00
			if length == 0.00:
				qty_value = temp_qty
			else:				
				qty_value = length * temp_qty			
				weight = qty_value * prod_rec.po_uom_in_kgs
		if uom_conversation_factor == 'two_dimension':
			qty_value = length * breadth * temp_qty				
			weight = qty_value * prod_rec.po_uom_in_kgs		
		value = {'qty': qty_value,'weight':weight}			
		return {'value': value}
	
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False
		return True
	
	_constraints = [
		
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
	
ch_wo_ms_raw()

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
		'flag_is_bearing': fields.boolean('Is Bearing'),
		'brand_id': fields.many2one('kg.brand.master','Brand'),	
		'position_id': fields.many2one('kg.position.number','Position No'),
		
		### Offer Details ###
		'spare_offer_line_id': fields.integer('Spare Offer'),
		### Prime Cost ###
		'wo_prime_cost': fields.float('WO PC'),
		'mar_prime_cost': fields.float('Marketing PC'),
		'material_code': fields.char('Material Code'),
		
		'sequence_no': fields.integer('Sequence No.'),
		'off_name': fields.char('Offer Name'),
		
		'bom_type': fields.selection([('pump','Pump'),('spare','Spare')],'BOM Type'),
		'spare_bom_id': fields.many2one('ch.wo.spare.bot','Spare BOT Id'),
		'spare_id': fields.many2one('ch.wo.spare.bom','Spare  Id'),
		
	
	}
	
	_defaults = {
		
		'entry_mode':'manual',
		'flag_is_bearing': False,
		
		
		
	}
	
	def onchange_bot(self, cr, uid, ids, bot_id):
		bot_obj = self.pool.get('kg.machine.shop')
		if bot_id:
			bot_rec = bot_obj.browse(cr, uid, bot_id)
		return {'value': {'flag_is_bearing': bot_rec.is_bearing}}
	
	def default_get(self, cr, uid, fields, context=None):
		context.update({'entry_mode': 'manual','flag_applicable': True})
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
		'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'access_id': fields.many2one('kg.accessories.master','Accessories',domain="[('active','=','t'),('state','not in',('draft','reject','cancal'))]"),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t'),('state','not in',('reject','cancal'))]"),
		'moc_const_id':fields.many2one('kg.moc.construction', 'MOC Construction'),
		'qty': fields.float('Qty'),
		'oth_spec': fields.char('Other Specification'),
		'load_access': fields.boolean('Load BOM'),
		
		'line_ids': fields.one2many('ch.wo.accessories.foundry', 'header_id', 'Accessories Foundry'),
		'line_ids_a': fields.one2many('ch.wo.accessories.ms', 'header_id', 'Accessories MS'),
		'line_ids_b': fields.one2many('ch.wo.accessories.bot', 'header_id', 'Accessories BOT'),
		'access_offer_line_id': fields.integer('Accessories Offer'),
		'flag_standard': fields.boolean('Non Standard'),
		### Prime Cost ###
		'wo_prime_cost': fields.float('WO PC'),
		'mar_prime_cost': fields.float('Marketing PC'),
		'off_name': fields.char('Offer Name'),
		
	}
	
	def default_get(self, cr, uid, fields, context=None):		
		return context
	
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False
		return True
	
	_constraints = [
		
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
	
	def onchange_load_access(self, cr, uid, ids, load_access,access_id,moc_const_id,qty,order_category,flag_standard):
		fou_vals=[]
		ms_vals=[]
		bot_vals=[]
		data_rec = ''
		if load_access == True and access_id:
			if moc_const_id is False:
				raise osv.except_osv(_('Warning!'),_('Kindly Configure MOC Construction !!'))
			else:
				pass
			if qty == 0:
				raise osv.except_osv(_('Warning!'),_('Kindly Configure Qty'))
			access_obj = self.pool.get('kg.accessories.master').search(cr, uid, [('id','=',access_id)])
			if access_obj:
				data_rec = self.pool.get('kg.accessories.master').browse(cr, uid, access_obj[0])
		print"data_recdata_rec",data_rec
		moc_id = ''
		moc_name = ''
		if data_rec:
			if data_rec.line_ids_b:
				for item in data_rec.line_ids_b:
					pat_obj = self.pool.get('kg.pattern.master').search(cr,uid,[('id','=',item.pattern_id.id)])
					if pat_obj:
						pat_rec = self.pool.get('kg.pattern.master').browse(cr,uid,pat_obj[0])
						if pat_rec.line_ids:
							pat_line_obj = self.pool.get('ch.mocwise.rate').search(cr,uid,[('code','=',moc_const_id),('header_id','=',pat_rec.id)])
							if pat_line_obj:
								pat_line_rec = self.pool.get('ch.mocwise.rate').browse(cr,uid,pat_line_obj[0])
								moc_id = pat_line_rec.moc_id.id
					fou_vals.append({
									'position_id': item.position_id.id,
									'pattern_id': item.pattern_id.id,
									'pattern_name': item.pattern_name,
									'moc_id': moc_id,
									'qty': item.qty * qty,
									'load_bom': True,
									'is_applicable': True,
									'entry_mode': 'auto',
									'order_category': order_category,
									'flag_standard': flag_standard,
									
									})
				print"fou_valsfou_vals",fou_vals
			if data_rec.line_ids_a:
				for item in data_rec.line_ids_a:
					ms_obj = self.pool.get('kg.machine.shop').search(cr,uid,[('id','=',item.ms_id.id)])
					if ms_obj:
						ms_rec = self.pool.get('kg.machine.shop').browse(cr,uid,ms_obj[0])
						if ms_rec.line_ids_a:
							cons_rec = self.pool.get('kg.moc.construction').browse(cr,uid,moc_const_id)
							ms_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',cons_rec.id),('header_id','=',ms_rec.id)])
							if ms_line_obj:
								ms_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,ms_line_obj[0])
								moc_id = ms_line_rec.moc_id.id
					ms_vals.append({
									'name': item.name,
									'position_id': item.position_id.id,							
									'ms_id': item.ms_id.id,
									'moc_id': moc_id,
									'qty': item.qty * qty,
									'indent_qty': item.qty * qty,
									'load_bom': True,
									'is_applicable': True,
									'entry_mode': 'auto',
									'order_category': order_category,
									'flag_standard': flag_standard,
									
									})
					print"ms_valsms_vals",ms_vals	
			if data_rec.line_ids:
				for item in data_rec.line_ids:
					bot_obj = self.pool.get('kg.machine.shop').search(cr,uid,[('id','=',item.ms_id.id)])
					if bot_obj:
						bot_rec = self.pool.get('kg.machine.shop').browse(cr,uid,bot_obj[0])
						is_bearing = bot_rec.is_bearing
						if bot_rec.line_ids_a:
							cons_rec = self.pool.get('kg.moc.construction').browse(cr,uid,moc_const_id)
							bot_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',cons_rec.id),('header_id','=',bot_rec.id)])
							if bot_line_obj:
								bot_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,bot_line_obj[0])
								moc_id = bot_line_rec.moc_id.id
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
									'entry_mode': 'auto',
									'order_category': order_category,
									'flag_standard': flag_standard,
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
		'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
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
		'wo_prime_cost': fields.float('WO PC'),
		'material_code': fields.char('Material Code'),
		'off_name': fields.char('Offer Name'),
		'flag_standard': fields.boolean('Non Standard'),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		
	}
	
	_defaults = {
		
		'entry_mode': 'manual',
		'flag_standard': False,
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		
		context.update({'entry_mode': 'manual'})
		return context
	
ch_wo_accessories_foundry()

class ch_wo_accessories_ms(osv.osv):

	_name = "ch.wo.accessories.ms"
	_description = "WO Accessories MS"
	
	_columns = {
	
		### machineshop Item Details ####
		'header_id':fields.many2one('ch.wo.accessories', 'Header Id', ondelete='cascade'),
		'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'pos_no': fields.related('position_id','name', type='char', string='Position No', store=True),
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
		'wo_prime_cost': fields.float('WO PC'),
		'indent_qty': fields.integer('Indent Creation Qty'),
		'material_code': fields.char('Material Code'),
		'flag_dynamic_length': fields.boolean('Dynamic Length'),
		'off_name': fields.char('Offer Name'),
		'flag_standard': fields.boolean('Non Standard'),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		
	}
	
	
	_defaults = {
		
		'is_applicable':False,
		'load_bom':False,
		'flag_dynamic_length':False,
		'entry_mode': 'manual',
		'flag_standard': False,
		
	}
	
	def onchange_qty(self, cr, uid, ids, qty):
		return {'value': {'indent_qty': qty}}
		
	def default_get(self, cr, uid, fields, context=None):
		
		context.update({'entry_mode': 'manual'})
		return context
	
ch_wo_accessories_ms()

class ch_wo_accessories_bot(osv.osv):

	_name = "ch.wo.accessories.bot"
	_description = "WO Accessories BOT"
	
	_columns = {
	
		### BOT Item Details ####
		'header_id':fields.many2one('ch.wo.accessories', 'Header Id', ondelete='cascade'),
		'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
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
		'wo_prime_cost': fields.float('WO PC'),
		'material_code': fields.char('Material Code'),
		'off_name': fields.char('Offer Name'),
		'flag_standard': fields.boolean('Non Standard'),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		
	}
	
	_defaults = {
		
		'entry_mode': 'manual',
		'flag_standard': False,
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		
		context.update({'entry_mode': 'manual'})
		return context
	
ch_wo_accessories_bot()


class ch_wo_spare_bom(osv.osv):
	
	_name = "ch.wo.spare.bom"
	_description = "Spare Item Details"
	_rec_name = "off_name"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('ch.work.order.details', 'Header Id', ondelete='cascade'),
		'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'remarks': fields.char('Remarks'),
		
		## Module Requirement Fields
		
		'pump_id':fields.many2one('kg.pumpmodel.master','Pumpmodel'),
		'moc_const_id':fields.many2one('kg.moc.construction','MOC Construction'),
		'bom_id':fields.many2one('kg.bom','BOM Name',domain="[('pump_model_id','=',parent.pump_model_id),('category_type','=','part_list_bom')]"),
		'qty':fields.integer('Qty'),
		'off_name':fields.char('Offer Name'),
		'load_bom':fields.boolean('Load BOM'),
		'flag_standard': fields.boolean('Non Standard'),
		
		## Child Tables Declaration
		
		'line_ids': fields.one2many('ch.wo.spare.foundry', 'header_id', "FOU"),
		'line_ids_a': fields.one2many('ch.wo.spare.ms', 'header_id', "MS"),
		'line_ids_b': fields.one2many('ch.wo.spare.bot', 'header_id', "BOT"),
		
		}
	
	_defaults = {
		'flag_standard': False,
		#~ 'is_applicable': False,
		#~ 'load_bom': False,
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		print"contextcontextcontext",context
		return context
	
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_wo_spare_bom, self).write(cr, uid, ids, vals, context)
	
	#~ def _check_qty(self, cr, uid, ids, context=None):
		#~ rec = self.browse(cr, uid, ids[0])
		#~ if rec.qty <= 0.00:
			#~ return False
		#~ return True
	
	_constraints = [
		
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
	
	def onchange_spare_off_name(self, cr, uid, ids, bom_id):
		value = {'off_name':'','qty':0}
		if bom_id:
			bom_obj = self.pool.get('kg.bom').search(cr,uid,([('id','=',bom_id)]))
			if bom_obj:
				bom_rec = self.pool.get('kg.bom').browse(cr,uid,bom_obj[0])
				value = {'off_name':bom_rec.name,'qty':bom_rec.qty}
		return {'value': value}
	
	def onchange_spare_bom(self, cr, uid, ids, bom_id,off_name,moc_const_id,qty,flag_standard):
		fou_vals=[]
		ms_vals=[]
		bot_vals=[]
		ch_ms_vals = []
		if bom_id:
			bom_obj = self.pool.get('kg.bom').search(cr,uid,([('id','=',bom_id),('name','=',off_name)]))
			if bom_obj:
				bom_rec = self.pool.get('kg.bom').browse(cr,uid,bom_obj[0])
				moc_name = ''
				moc_changed_flag = False
				if bom_rec.line_ids:
					for item in bom_rec.line_ids:
						moc_id = ''
						pat_obj = self.pool.get('kg.pattern.master').search(cr,uid,[('id','=',item.pattern_id.id)])
						if pat_obj:
							pat_rec = self.pool.get('kg.pattern.master').browse(cr,uid,pat_obj[0])
							if pat_rec.line_ids:
								pat_line_obj = self.pool.get('ch.mocwise.rate').search(cr,uid,[('code','=',moc_const_id),('header_id','=',pat_rec.id)])
								if pat_line_obj:
									pat_line_rec = self.pool.get('ch.mocwise.rate').browse(cr,uid,pat_line_obj[0])
									moc_id = pat_line_rec.moc_id.id
						if moc_id:
							moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
							moc_changed_flag = True
							moc_name = moc_rec.name
	
							if not moc_rec.line_ids:
								raise osv.except_osv(_('Warning!'),
										_('Raw material are not mapped for MOC %s !!')%(moc_name))
							
						fou_vals.append({
									'position_id': item.position_id.id,
									'pattern_id': item.pattern_id.id,
									'pattern_name': item.pattern_id.pattern_name,
									'off_name': item.pattern_id.pattern_name,
									'moc_id': moc_id,
									'moc_name': moc_name,
									'moc_changed_flag': moc_changed_flag,
									'qty': item.qty * qty,
									'load_bom': True,
									'is_applicable': True,
									'entry_mode': 'auto',
									'flag_standard': flag_standard,
									#~ 'purpose_categ': purpose_categ,
									#~ 'csd_no': item.csd_no,
									#~ 'remarks': item.remarks,
									})
				
				if bom_rec.line_ids_a:
					for item in bom_rec.line_ids_a:
						moc_id = ''
						ms_obj = self.pool.get('kg.machine.shop').search(cr,uid,[('id','=',item.ms_id.id)])
						print"ms_objms_obj",ms_obj
						if ms_obj:
							ms_rec = self.pool.get('kg.machine.shop').browse(cr,uid,ms_obj[0])
							if ms_rec.line_ids_a:
								#~ for ele in ms_rec.line_ids_a:
								cons_rec = self.pool.get('kg.moc.construction').browse(cr,uid,moc_const_id)
								ms_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',cons_rec.id),('header_id','=',ms_rec.id)])
								if ms_line_obj:
									ms_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,ms_line_obj[0])
									moc_id = ms_line_rec.moc_id.id
									
							if ms_rec.line_ids:
								ch_ms_vals = []
								for raw in ms_rec.line_ids:
									ch_ms_vals.append([0, 0,{
											'product_id': raw.product_id.id,
											'uom': raw.uom.id,
											'od': raw.od,
											'length': raw.length,
											'breadth': raw.breadth,
											'thickness': raw.thickness,
											'weight': raw.weight * item.qty * qty,
											'uom_conversation_factor': raw.uom_conversation_factor,
											'temp_qty': raw.temp_qty * item.qty * qty,
											'qty': raw.qty * item.qty * qty,
											'remarks': raw.remarks,
											}])
						if moc_id:
							moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
							moc_changed_flag = True
							moc_name = moc_rec.name
						
						if ch_ms_vals == []:
							raise osv.except_osv(_('Warning!'),
									_('Raw material are not mapped for MS Item %s !!')%(item.name))
						ms_vals.append({
										'name': item.name,
										'off_name': item.name,
										'position_id': item.position_id.id,							
										'ms_id': item.ms_id.id,
										'moc_id': moc_id,
										'moc_name': moc_name,
										'moc_changed_flag': moc_changed_flag,
										'qty': item.qty * qty,
										'load_bom': True,
										'is_applicable': True,
										'line_ids': ch_ms_vals,
										'entry_mode': 'auto',
										'flag_standard': flag_standard,
										#~ 'purpose_categ': purpose_categ,
										#~ 'line_ids': ch_ms_vals,
										#~ 'csd_no': item.csd_no,
										#~ 'remarks': item.remarks,
										})
				
				
				if bom_rec.line_ids_b:
					for item in bom_rec.line_ids_b:
						moc_id = ''
						item_name = item.name
						bot_obj = self.pool.get('kg.machine.shop').search(cr,uid,[('id','=',item.bot_id.id)])
						if bot_obj:
							bot_rec = self.pool.get('kg.machine.shop').browse(cr,uid,bot_obj[0])
							is_bearing = bot_rec.is_bearing
							if bot_rec.line_ids_a:
								cons_rec = self.pool.get('kg.moc.construction').browse(cr,uid,moc_const_id)
								bot_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',cons_rec.id),('header_id','=',bot_rec.id)])
								if bot_line_obj:
									bot_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,bot_line_obj[0])
									moc_id = bot_line_rec.moc_id.id
						if moc_id:
							moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
							moc_changed_flag = True
							moc_name = moc_rec.name
						if not bot_rec.line_ids:
							raise osv.except_osv(_('Warning!'),
									_('Raw material are not mapped for BOT Item %s !!')%(item_name))
						bot_vals.append({
										'item_name': item_name,
										'off_name': item_name,
										'ms_id': item.bot_id.id,
										'moc_id': moc_id,
										'moc_name': moc_name,
										'moc_changed_flag': moc_changed_flag,
										'qty': item.qty * qty,
										'load_bom': True,
										'flag_is_bearing': is_bearing,
										'is_applicable': True,
										#~ 'purpose_categ': purpose_categ,
										'position_id': item.position_id.id,
										#~ 'remarks': item.remarks,
										'entry_mode': 'auto',
										'flag_standard': flag_standard,
										})
										
		return {'value': {'line_ids': fou_vals,'line_ids_a': ms_vals,'line_ids_b': bot_vals}}
	
ch_wo_spare_bom()

class ch_wo_spare_foundry(osv.osv):
	
	_name = "ch.wo.spare.foundry"
	_description = "Spare Foundry Item Details"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('ch.wo.spare.bom', 'Header Id', ondelete='cascade'),
		'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'remarks': fields.char('Remarks'),
		
		## Module Requirement Fields
		
		'qty':fields.integer('Quantity'),
		'oth_spec':fields.char('Other Specification'),
		'position_id': fields.many2one('kg.position.number','Position No.'),
		'csd_no': fields.char('CSD No.', size=128),
		'pattern_name': fields.char('Pattern Name'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No.'),
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'moc_name': fields.char('MOC Name'),
		'moc_changed_flag': fields.boolean('MOC Changed'),
		'prime_cost': fields.float('Prime Cost'),
		'order_category': fields.selection([('pump','Pump'),('spare','Spare'),('access','Accessories')],'Purpose Category'),
		'material_code': fields.char('Material Code'),
		'off_name': fields.char('Offer Name'),
		'flag_pattern_check': fields.boolean('Is Pattern Check'),
		'sequence_no': fields.integer('Sequence No.'),
		'flag_standard': fields.boolean('Non Standard'),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		
	}
	
	_defaults = {
		
		'is_applicable': False,
		'load_bom': False,
		'flag_pattern_check': False,
		'entry_mode': 'manual',
		'flag_standard': False,
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		
		context.update({'entry_mode': 'manual'})
		return context
	
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_wo_spare_foundry, self).write(cr, uid, ids, vals, context)
	
	#~ def _check_qty(self, cr, uid, ids, context=None):
		#~ rec = self.browse(cr, uid, ids[0])
		#~ if rec.qty <= 0.00:
			#~ return False
		#~ return True
	
	_constraints = [
		
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
	
	def onchange_pattern_name(self, cr, uid, ids, pattern_code,pattern_name):
		value = {'pattern_name':''}
		pattern_obj = self.pool.get('kg.pattern.master').search(cr,uid,([('id','=',pattern_code)]))
		if pattern_obj:
			pattern_rec = self.pool.get('kg.pattern.master').browse(cr,uid,pattern_obj[0])
			value = {'pattern_name':pattern_rec.pattern_name}
		return {'value': value}
	
	def onchange_moc(self,cr,uid,ids,moc_id,moc_name, context=None):
		value = {'moc_changed_flag':''}
		if moc_id:
			moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
			if moc_rec.name == moc_name:
				pass
			else:
				value = {'moc_changed_flag': True}
		return {'value': value}
	
ch_wo_spare_foundry()

class ch_wo_spare_ms(osv.osv):
	
	_name = "ch.wo.spare.ms"
	_description = "Macine Shop Item Details"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('ch.wo.spare.bom', 'Header Id', ondelete='cascade'),
		'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'remarks':fields.text('Remarks'),
		
		## Module Requirement Fields
		
		'pos_no': fields.related('position_id','name', type='char', string='Position No.', store=True),
		'position_id': fields.many2one('kg.position.number','Position No.'),
		'csd_no': fields.char('CSD No.'),
		'bom_id': fields.many2one('kg.bom','BOM'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','ms')], ondelete='cascade',required=True),
		'name': fields.related('ms_id','name', type='char',size=128,string='Item Name', store=True),
		#~ 'ms_line_id':fields.many2one('ch.machineshop.details', 'Item Name'),
		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
		#'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'moc_name': fields.char('MOC Name'),
		'moc_changed_flag': fields.boolean('MOC Changed'),
		'prime_cost': fields.float('Prime Cost'),
		'order_category': fields.selection([('pump','Pump'),('spare','Spare'),('access','Accessories')],'Purpose Category'),
		'length': fields.float('Length'),
		'material_code': fields.char('Material Code'),
		'off_name': fields.char('Offer Name'),
		'sequence_no': fields.integer('Sequence No.'),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		
		'flag_standard': fields.boolean('Non Standard'),
		## Child Tables Declaration
		'line_ids': fields.one2many('ch.wo.spare.ms.raw', 'header_id', "MS Raw material"),
		
		
	}
	
	_defaults = {
		
		'is_applicable': False,
		'load_bom': False,
		'entry_mode': 'manual',
		'flag_standard': False,
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		
		context.update({'entry_mode': 'manual'})
		return context
	
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_wo_spare_ms, self).write(cr, uid, ids, vals, context)
	
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False
		return True
	
	def onchange_moc(self,cr,uid,ids,moc_id,moc_name, context=None):
		value = {'moc_changed_flag':''}
		if moc_id:
			moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
			if moc_rec.name == moc_name:
				pass
			else:
				value = {'moc_changed_flag': True}
		return {'value': value}
	
	_constraints = [
		
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
	
ch_wo_spare_ms()

class ch_wo_spare_ms_raw(osv.osv):
	
	_name = "ch.wo.spare.ms.raw"
	_description = "Ch wo spare raw Details"
	
	_columns = {
		
		### Basic Info
		
		'header_id':fields.many2one('ch.wo.spare.ms', 'Spare MS', ondelete='cascade'),		
		'remarks': fields.char('Remarks'),
		'active': fields.boolean('Active'),	
		
		### Module Requirement
		
		'product_id': fields.many2one('product.product','Raw Material',domain="[('product_type','in',['ms','bot','consu','coupling'])]"),			
		'uom':fields.many2one('product.uom','UOM',size=128 ),
		'od': fields.float('OD'),
		'length': fields.float('Length'),
		'breadth': fields.float('Breadth'),
		'thickness': fields.float('Thickness'),
		'weight': fields.float('Weight' ,digits=(16,5)),
		'uom_conversation_factor': fields.selection([('one_dimension','One Dimension'),('two_dimension','Two Dimension')],'UOM Conversation Factor'),		
		'temp_qty':fields.float('Qty'),
		'qty':fields.float('Testing Qty',readonly=True),
	
		
	}
	
	_defaults = {
		
		'active': True,
		
		
	}
	
	def onchange_weight(self, cr, uid, ids, uom_conversation_factor,length,breadth,temp_qty,product_id, context=None):		
		value = {'qty': '','weight': '',}
		prod_rec = self.pool.get('product.product').browse(cr,uid,product_id)
		qty_value = 0.00
		weight=0.00
		if uom_conversation_factor == 'one_dimension':	
			if prod_rec.uom_id.id == prod_rec.uom_po_id.id:
				qty_value = length * temp_qty
				weight = 0.00
			if length == 0.00:
				qty_value = temp_qty
			else:				
				qty_value = length * temp_qty			
				weight = qty_value * prod_rec.po_uom_in_kgs
		if uom_conversation_factor == 'two_dimension':
			qty_value = length * breadth * temp_qty				
			weight = qty_value * prod_rec.po_uom_in_kgs		
		value = {'qty': qty_value,'weight':weight}			
		return {'value': value}
	
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False
		return True
	
	_constraints = [
		
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
	
ch_wo_spare_ms_raw()

class ch_wo_spare_bot(osv.osv):
	
	_name = "ch.wo.spare.bot"
	_description = "BOT Details"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('ch.wo.spare.bom', 'Header Id', ondelete='cascade'),
		'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'remarks':fields.text('Remarks'),
		
		## Module Requirement Fields
		
		'product_temp_id':fields.many2one('product.product', 'Product Name',domain = [('type','=','bot')], ondelete='cascade'),
		#~ 'bot_line_id':fields.many2one('ch.bot.details', 'Item Name'),
		'position_id': fields.many2one('kg.position.number','Position No.'),
		'bom_id': fields.many2one('kg.bom','BOM'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','bot')], ondelete='cascade',required=True),
		'item_name': fields.related('ms_id','name', type='char', size=128, string='Item Name', store=True, readonly=True),
		'code':fields.char('Item Code', size=128),	  
		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
		#'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'moc_name': fields.char('MOC Name'),
		'moc_changed_flag': fields.boolean('MOC Changed'),
		'prime_cost': fields.float('Prime Cost'),
		'brand_id': fields.many2one('kg.brand.master','Brand '),
		'flag_is_bearing': fields.boolean('Is Bearing'),
		'order_category': fields.selection([('pump','Pump'),('spare','Spare'),('access','Accessories')],'Purpose Category'),
		'material_code': fields.char('Material Code'),
		'off_name': fields.char('Offer Name'),
		'sequence_no': fields.integer('Sequence No.'),
		'flag_standard': fields.boolean('Non Standard'),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		
	}
	
	_defaults = {
		
		'is_applicable': False,
		'load_bom': False,
		'flag_is_bearing': False,
		'entry_mode': 'manual',
		'flag_standard': False,
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		
		context.update({'entry_mode': 'manual'})
		return context
	
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_wo_spare_bot, self).write(cr, uid, ids, vals, context)
	
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False
		return True
	
	def onchange_moc(self,cr,uid,ids,moc_id,moc_name, context=None):
		value = {'moc_changed_flag':''}
		if moc_id:
			moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
			if moc_rec.name == moc_name:
				pass
			else:
				value = {'moc_changed_flag': True}
		return {'value': value}
	
	_constraints = [
		
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
	
ch_wo_spare_bot()



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





	
	








