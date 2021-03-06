from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

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


class kg_schedule(osv.osv):

	_name = "kg.schedule"
	_description = "Schedule Entry"
	_order = "entry_date desc"
	
	def _get_default_division(self, cr, uid, context=None):
		res = self.pool.get('kg.division.master').search(cr, uid, [('code','=','SAM'),('state','=','approved'), ('active','=','t')], context=context)
		return res and res[0] or False
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Schedule No', size=128,select=True,required=True),
		'entry_date': fields.date('Schedule Date',required=True),
		'division_id': fields.many2one('kg.division.master','Division',readonly=True,required=True,domain="[('state','=','approved'), ('active','=','t')]"),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location',required=True),
		'note': fields.text('Notes'),
		'remarks': fields.text('Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'line_ids': fields.one2many('ch.schedule.details', 'header_id', "Schedule Details"),
		
		'order_line_ids':fields.many2many('ch.work.order.details','m2m_work_order_details' , 'schedule_id', 'order_id', 'Work Order Lines',
			domain="[('schedule_status','=','allow'),'&',('header_id.state','=','confirmed'),'&',('state','=','confirmed'),('header_id.location','=',location)]"),
		'flag_schedule': fields.boolean('Schedule'),
		'flag_cancel': fields.boolean('Cancellation Flag'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'delivery_date': fields.date('Delivery Date',required=True),
		'order_priority': fields.selection(ORDER_PRIORITY,'Priority'),
		'order_category': fields.selection(ORDER_CATEGORY,'Category'),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_schedule', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',	
		'active': True,
		'flag_schedule': False,
		'division_id':_get_default_division,
		'order_priority': 'normal',
		'delivery_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'entry_mode': 'manual'

	}
	
	#~ _sql_constraints = [
		#~ ('name_uniq', 'unique(name)', 'Schedule No. must be unique !!'),
	#~ ]
	
	
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
		
	def _entry_duplicates(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		cr.execute(''' select id from kg_schedule 
		where 
		id != %s and
		entry_date = %s and
		state = 'confirmed'
		
		''',[rec.id,str(rec.entry_date) ])
		dup_id = cr.fetchone()
		if dup_id:
			return False
		return True	
	
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),   
		#(_entry_duplicates, 'System not allow to create duplicate Entry. !!',['']),   
		
	   ]
	   
	   
	def update_line_items(self,cr,uid,ids,bom_qty=0,context=False):
		
		entry = self.browse(cr,uid,ids[0])
		order_obj = self.pool.get('kg.work.order')
		order_line_obj = self.pool.get('ch.work.order.details')
		schedule_line_obj = self.pool.get('ch.schedule.details')
		allocation_line_obj = self.pool.get('ch.stock.allocation.detail')
		order_bomline_obj = self.pool.get('ch.order.bom.details')
		
		del_sql = """ delete from ch_schedule_details where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		if entry.order_line_ids:
			for order_item in entry.order_line_ids:
				print "order_item",order_item
				### Creating Schedule items for Purpose Pump ###
				for bom_item in order_item.line_ids:
					if type(bom_qty) is dict:
						if order_item.order_category == 'pump':
							if order_item.pump_rem_qty != 0:
								if order_item.pump_rem_qty < order_item.qty:
									real_bom_qty = bom_item.qty / order_item.qty
									sch_bom_qty = real_bom_qty * order_item.pump_rem_qty
								else:
									sch_bom_qty = bom_item.qty
							else:
								sch_bom_qty = bom_item.qty
						else:	
							sch_bom_qty = bom_item.qty
					elif bom_qty == 0:
						sch_bom_qty = bom_item.qty
					else:
						real_bom_qty = bom_item.qty / order_item.qty
						sch_bom_qty = real_bom_qty * order_item.pump_rem_qty
					
					if bom_item.flag_applicable == True:
						print "sch_bom_qty",sch_bom_qty
						schedule_item_vals = {
													
							'header_id': entry.id,
							'order_id': order_item.header_id.id,
							'order_line_id': order_item.id,										
							'bom_id': bom_item.bom_id.id,
							'bom_line_id': bom_item.bom_line_id.id,																	
							'order_bomline_id': bom_item.id,									
							'qty' : sch_bom_qty,
							'order_qty': sch_bom_qty,
							'stock_qty' : 0,
							'line_status': 'schedule',
							'order_priority': order_item.order_priority,
							'order_category': order_item.order_category,
							'order_no':	order_item.order_no,
							'pattern_id': bom_item.pattern_id.id,
							'moc_id': bom_item.moc_id.id,			
							'weight': bom_item.weight,			
							'total_weight': bom_item.weight * sch_bom_qty,			
							}
						
						schedule_line_id = schedule_line_obj.create(cr, uid, schedule_item_vals)
						
						self.write(cr, uid, ids, {'flag_schedule':True})
						order_line_obj.write(cr, uid, order_item.id, {'schedule_status':'not_allow'})		
						tot_stock = 0
						
						if order_item.header_id.order_category != 'project' and order_item.header_id.stock_check != 'no':
							### Checking stock exists for corresponding pattern ###
							cr.execute(''' select sum(available_qty) as stock_qty
								from ch_stock_inward_details  
								where pattern_id = %s and moc_id = %s
								and available_qty > 0 and stock_type = 'pattern'
							
							''',[bom_item.pattern_id.id
								,bom_item.moc_id.id])
							result_stock_qty = cr.fetchone()
							print "result_stock_qty-------------------------------",result_stock_qty
							schedule_rec = schedule_line_obj.browse(cr, uid, schedule_line_id)
						
							if result_stock_qty[0] == None:
								stock_qty = 0
								if schedule_rec.line_status == 'schedule':
									line_status = 'schedule'
								else:
									line_status = 'schedule_alloc'
							if result_stock_qty[0] != None:
								if result_stock_qty[0] > 0:
									stock_qty = result_stock_qty[0]
									if schedule_rec.line_status == 'schedule':
										line_status = 'schedule_alloc'
									else:
										line_status = 'schedule_alloc'
								if result_stock_qty[0] == 0:
									stock_qty = 0
									if schedule_rec.line_status == 'schedule':
										line_status = 'schedule_alloc'
									else:
										line_status = 'schedule_alloc'
									
							#### Allocation Creation When stock exists ####
							
							tot_stock += stock_qty
							

							if stock_qty > 0:
								
								if schedule_rec.qty == stock_qty:
									alloc_qty = schedule_rec.qty
								if schedule_rec.qty > stock_qty:
									alloc_qty = stock_qty
								if schedule_rec.qty < stock_qty:
									alloc_qty = schedule_rec.qty

								if schedule_rec.order_priority in ('emergency','breakdown') and order_item.header_id.order_category == 'project':
									flag_allocate = False
									flag_manual = True
									allocation_qty = 0
								else:
									flag_allocate = True
									flag_manual = False
									allocation_qty = alloc_qty
								if bom_item.flag_pattern_check == True or bom_item.pattern_id.pattern_state != 'active':
									flag_allocate = False
									flag_manual = True
									allocation_qty = 0
								else:
									flag_allocate = True
									flag_manual = False
									allocation_qty = alloc_qty
								
									
								
								allocation_item_vals = {
														
									'header_id': schedule_line_id,
									'order_id': order_item.header_id.id,
									'order_line_id': order_item.id,
									'schedule_qty' : bom_item.schedule_qty,										
									'qty' : allocation_qty,											
									'stock_qty' : stock_qty,
									'flag_allocate' : flag_allocate,			
									'flag_manual' : flag_manual,			
								}
								
								if flag_allocate == True:
									sch_qty = sch_bom_qty - tot_stock
									if sch_qty < 0:
										sch_qty = 0
									else:
										sch_qty = sch_qty
								else:
									sch_qty = bom_item.qty
								schedule_line_obj.write(cr, uid, schedule_line_id, {'stock_qty':tot_stock,'line_status':line_status,'qty':sch_qty})
								
								allocation_id = allocation_line_obj.create(cr, uid, allocation_item_vals)
								print "allocation_item_vals",allocation_item_vals
				
				### Creating Schedule items for Purpose Accessories ###
				for acc_item in order_item.line_ids_d:
					for acc_bom_item in acc_item.line_ids:
						
						if acc_bom_item.is_applicable == True:
							acc_schedule_item_vals = {
														
								'header_id': entry.id,
								'order_id': order_item.header_id.id,
								'order_line_id': order_item.id,																							
								'acc_bomline_id': acc_bom_item.id,									
								'qty' : acc_bom_item.qty,
								'order_qty' : acc_bom_item.qty,
								'stock_qty' : 0,
								'line_status': 'schedule',
								'order_priority': order_item.order_priority,
								'order_category': order_item.order_category,
								'order_no':	order_item.order_no,
								'pattern_id': acc_bom_item.pattern_id.id,
								'moc_id': acc_bom_item.moc_id.id,
								}
							print "acc_schedule_item_vals",acc_schedule_item_vals
							schedule_line_id = schedule_line_obj.create(cr, uid, acc_schedule_item_vals)
							self.write(cr, uid, ids, {'flag_schedule':True})
							order_line_obj.write(cr, uid, order_item.id, {'schedule_status':'not_allow'})	
							tot_stock = 0
							### Checking stock exists for corresponding pattern ###
							cr.execute(''' select sum(available_qty) as stock_qty
								from ch_stock_inward_details  
								where pattern_id = %s and moc_id = %s
								and available_qty > 0 and stock_type = 'pattern'
							
							''',[acc_bom_item.pattern_id.id
								,acc_bom_item.moc_id.id])
							result_stock_qty = cr.fetchone()
							print "result_stock_qty[0]",result_stock_qty[0]
							schedule_rec = schedule_line_obj.browse(cr, uid, schedule_line_id)
						
							if result_stock_qty[0] == None:
								stock_qty = 0
								if schedule_rec.line_status == 'schedule':
									line_status = 'schedule'
								else:
									line_status = 'schedule_alloc'
							if result_stock_qty[0] != None:
								if result_stock_qty[0] > 0:
									stock_qty = result_stock_qty[0]
									if schedule_rec.line_status == 'schedule':
										line_status = 'schedule_alloc'
									else:
										line_status = 'schedule_alloc'
								if result_stock_qty[0] == 0:
									stock_qty = 0
									if schedule_rec.line_status == 'schedule':
										line_status = 'schedule_alloc'
									else:
										line_status = 'schedule_alloc'
									
							#### Allocation Creation When stock exists ####
							
							tot_stock += stock_qty
							

							if stock_qty > 0:
								
								if schedule_rec.qty == stock_qty:
									alloc_qty = schedule_rec.qty
								if schedule_rec.qty > stock_qty:
									alloc_qty = stock_qty
								if schedule_rec.qty < stock_qty:
									alloc_qty = schedule_rec.qty

								if schedule_rec.order_priority in ('emergency','breakdown') and order_item.header_id.order_category == 'project':
									flag_allocate = False
									flag_manual = True
									allocation_qty = 0
								else:
									flag_allocate = True
									flag_manual = False
									allocation_qty = alloc_qty
								if acc_bom_item.pattern_id.pattern_state != 'active':
									flag_allocate = False
									flag_manual = True
									allocation_qty = 0
								else:
									flag_allocate = True
									flag_manual = False
									allocation_qty = alloc_qty
								
									
								
								allocation_item_vals = {
														
									'header_id': schedule_line_id,
									'order_id': order_item.header_id.id,
									'order_line_id': order_item.id,
									'schedule_qty' : acc_bom_item.qty,										
									'qty' : allocation_qty,											
									'stock_qty' : stock_qty,
									'flag_allocate' : flag_allocate,			
									'flag_manual' : flag_manual,			
								}
								
								sch_qty = acc_bom_item.qty - tot_stock
								if sch_qty < 0:
									sch_qty = 0
								else:
									sch_qty = sch_qty
								schedule_line_obj.write(cr, uid, schedule_line_id, {'stock_qty':tot_stock,'line_status':line_status,'qty':sch_qty})
								
								allocation_id = allocation_line_obj.create(cr, uid, allocation_item_vals)
								
				### Creating Schedule items for Spare BOM ###
				#~ for spare_item in order_item.line_ids_e:
					#~ for spare_bom_item in spare_item.line_ids:
						#~ 
						#~ if spare_bom_item.is_applicable == True:
							#~ spare_schedule_item_vals = {
														#~ 
								#~ 'header_id': entry.id,
								#~ 'order_id': order_item.header_id.id,
								#~ 'order_line_id': order_item.id,																							
								#~ 'spare_bomline_id': spare_bom_item.id,									
								#~ 'qty' : spare_bom_item.qty,
								#~ 'order_qty' : spare_bom_item.qty,
								#~ 'stock_qty' : 0,
								#~ 'line_status': 'schedule',
								#~ 'order_priority': order_item.order_priority,
								#~ 'order_category': order_item.order_category,
								#~ 'order_no':	order_item.order_no,
								#~ 'pattern_id': spare_bom_item.pattern_id.id,
								#~ 'moc_id': spare_bom_item.moc_id.id,
								#~ }
							#~ print "spare_schedule_item_vals",spare_schedule_item_vals
							#~ schedule_line_id = schedule_line_obj.create(cr, uid, spare_schedule_item_vals)
							#~ self.write(cr, uid, ids, {'flag_schedule':True})
							#~ order_line_obj.write(cr, uid, order_item.id, {'schedule_status':'not_allow'})	
							#~ tot_stock = 0
							### Checking stock exists for corresponding pattern ###
							#~ cr.execute(''' select sum(available_qty) as stock_qty
								#~ from ch_stock_inward_details  
								#~ where pattern_id = %s and moc_id = %s
								#~ and available_qty > 0 and stock_type = 'pattern'
							#~ 
							#~ ''',[spare_bom_item.pattern_id.id
								#~ ,spare_bom_item.moc_id.id])
							#~ result_stock_qty = cr.fetchone()
							#~ print "result_stock_qty[0]",result_stock_qty[0]
							#~ schedule_rec = schedule_line_obj.browse(cr, uid, schedule_line_id)
						#~ 
							#~ if result_stock_qty[0] == None:
								#~ stock_qty = 0
								#~ if schedule_rec.line_status == 'schedule':
									#~ line_status = 'schedule'
								#~ else:
									#~ line_status = 'schedule_alloc'
							#~ if result_stock_qty[0] != None:
								#~ if result_stock_qty[0] > 0:
									#~ stock_qty = result_stock_qty[0]
									#~ if schedule_rec.line_status == 'schedule':
										#~ line_status = 'schedule_alloc'
									#~ else:
										#~ line_status = 'schedule_alloc'
								#~ if result_stock_qty[0] == 0:
									#~ stock_qty = 0
									#~ if schedule_rec.line_status == 'schedule':
										#~ line_status = 'schedule_alloc'
									#~ else:
										#~ line_status = 'schedule_alloc'
									
							#### Allocation Creation When stock exists ####
							
							#~ tot_stock += stock_qty
							#~ 
#~ 
							#~ if stock_qty > 0:
								#~ 
								#~ if schedule_rec.qty == stock_qty:
									#~ alloc_qty = schedule_rec.qty
								#~ if schedule_rec.qty > stock_qty:
									#~ alloc_qty = stock_qty
								#~ if schedule_rec.qty < stock_qty:
									#~ alloc_qty = schedule_rec.qty
#~ 
								#~ if schedule_rec.order_priority == 'emergency' and order_item.header_id.order_category == 'project':
									#~ flag_allocate = False
									#~ flag_manual = True
									#~ allocation_qty = 0
								#~ else:
									#~ flag_allocate = True
									#~ flag_manual = False
									#~ allocation_qty = alloc_qty
								#~ if acc_bom_item.pattern_id.pattern_state != 'active':
									#~ flag_allocate = False
									#~ flag_manual = True
									#~ allocation_qty = 0
								#~ else:
									#~ flag_allocate = True
									#~ flag_manual = False
									#~ allocation_qty = alloc_qty
								#~ 
									#~ 
								#~ 
								#~ allocation_item_vals = {
														#~ 
									#~ 'header_id': schedule_line_id,
									#~ 'order_id': order_item.header_id.id,
									#~ 'order_line_id': order_item.id,
									#~ 'schedule_qty' : spare_bom_item.qty,										
									#~ 'qty' : allocation_qty,											
									#~ 'stock_qty' : stock_qty,
									#~ 'flag_allocate' : flag_allocate,			
									#~ 'flag_manual' : flag_manual,			
								#~ }
								#~ 
								#~ sch_qty = spare_bom_item.qty - tot_stock
								#~ if sch_qty < 0:
									#~ sch_qty = 0
								#~ else:
									#~ sch_qty = sch_qty
								#~ schedule_line_obj.write(cr, uid, schedule_line_id, {'stock_qty':tot_stock,'line_status':line_status,'qty':sch_qty})
								#~ 
								#~ allocation_id = allocation_line_obj.create(cr, uid, allocation_item_vals)				
									
						
		return True
	   

	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		qc_verf_obj = self.pool.get('kg.qc.verification')
		production_obj = self.pool.get('kg.production')
		schedule_line_obj = self.pool.get('ch.schedule.details')
		allocation_line_obj = self.pool.get('ch.stock.allocation.detail')
		order_line_obj = self.pool.get('ch.work.order.details')
		order_bomline_obj = self.pool.get('ch.order.bom.details')
		pouring_obj = self.pool.get('ch.boring.details')
		casting_obj = self.pool.get('ch.casting.details')
		today = date.today()
		today = str(today)
		
		if entry.state == 'draft':
			
		
			if entry.line_ids:
				
				ms_no = 1
				for schedule_item in entry.line_ids:
					
					### Updation WorK Order ###
					order_line_obj.write(cr, uid, schedule_item.order_line_id.id, {'schedule_status':'completed'})
					### Allocation Details Validation ###
					if schedule_item.line_ids:
						for alloc_item in schedule_item.line_ids:
							if alloc_item.flag_allocate == True and alloc_item.qty == 0:
								raise osv.except_osv(_('Warning !'), _('Allocation Qty is must for Order %s !!')%(schedule_item.order_no))
							if alloc_item.flag_allocate == False and alloc_item.qty > 0:
								raise osv.except_osv(_('Warning !'), _('Kindly check allocation process for Order %s !!')%(schedule_item.order_no))
							if alloc_item.qty > 0:
								if alloc_item.qty > alloc_item.stock_qty:
									raise osv.except_osv(_('Warning !'), _('Allocation Qty should not be greater than Stock Qty for Order %s !!')%(schedule_item.order_no))
								
							cr.execute(''' select sum(qty) from ch_stock_allocation_detail where header_id = %s ''',[schedule_item.id])
							alloc_qty = cr.fetchone()
							
							if alloc_qty[0] != None:
								if (schedule_item.qty + schedule_item.stock_qty) < alloc_qty[0]:
									raise osv.except_osv(_('Warning !'), _('Allocation Qty should not be greater than Schedule Qty and Stock Qty for Order %s !!')%(schedule_item.order_no))

					cr.execute(''' select sum(qty) from ch_stock_allocation_detail
					
					where
					header_id = %s and
					qty > 0 and
					flag_allocate = 't'
					
					''',[schedule_item.id])
					allocation_qty = cr.fetchone()
					print "allocation_qty",allocation_qty
					if allocation_qty:
						if allocation_qty[0] != None:
							
							schedule_qty = schedule_item.order_qty - allocation_qty[0]
							
							
							reject_rem_qty = allocation_qty[0]
							
							### Checking in Stock Inward for Ready for MS ###
							
							cr.execute(""" select id,available_qty as stock_qty,stock_location_id,heat_no
								from ch_stock_inward_details  
								where pattern_id = %s and moc_id = %s
								and foundry_stock_state = 'ready_for_ms' and available_qty > 0  and stock_type = 'pattern' """%(schedule_item.pattern_id.id,schedule_item.moc_id.id))
							stock_inward_items = cr.dictfetchall();
							print "stock_inward_items",stock_inward_items
							
							if stock_inward_items:
								print "reject_rem_qty",reject_rem_qty
								if reject_rem_qty > 0:
									for stock_item in  stock_inward_items:
										if reject_rem_qty > 0:
											if stock_item['stock_qty'] != None:
												allocate_qty =  reject_rem_qty - stock_item['stock_qty']
												print "reject_rem_qty",reject_rem_qty
												if allocate_qty <= 0:
													qc_qty = reject_rem_qty
													reject_rem_qty = 0
													
												else:
													reject_rem_qty = allocate_qty
													qc_qty = stock_item['stock_qty']
											print "qc_qty",qc_qty
											### Order Priority ###
													
											#~ if schedule_item.order_id.order_category in ('pump','pump_spare','project'):
												#~ if schedule_item.order_id.order_priority == 'normal':
													#~ priority = '6'
												#~ if schedule_item.order_id.order_priority == 'emergency':
													#~ priority = '4'
											#~ if schedule_item.order_id.order_category == 'service':
												#~ priority = '3'
											#~ if schedule_item.order_id.order_category == 'spare':
												#~ priority = '5'
												
											if schedule_item.order_id.order_category in ('pump','pump_spare','project','access'):
												if schedule_item.order_id.order_priority == 'normal':
													priority = '8'
												if schedule_item.order_id.order_priority == 'emergency':
													priority = '3'
												if schedule_item.order_id.order_priority == 'breakdown':
													priority = '2'
												if schedule_item.order_id.order_priority == 'urgent':
													priority = '7'
											if schedule_item.order_id.order_category == 'service':
												priority = '4'
											if schedule_item.order_id.order_category == 'spare':
												priority = '6'
											
											### Creating QC Verification ###
											
											qc_obj = self.pool.get('kg.qc.verification')
											
											### QC Sequence Number Generation  ###
											qc_name = ''	
											qc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.qc.verification')])
											rec = self.pool.get('ir.sequence').browse(cr,uid,qc_seq_id[0])
											cr.execute("""select generatesequenceno(%s,'%s','%s') """%(qc_seq_id[0],rec.code,schedule_item.header_id.entry_date))
											qc_name = cr.fetchone();
										
											qc_vals = {
																			
												'name': qc_name[0],
												'schedule_id': entry.id,
												'schedule_date': entry.entry_date,
												'division_id': entry.division_id.id,
												'location' : entry.location,
												'schedule_line_id': schedule_item.id,
												'order_id': schedule_item.order_id.id,
												'order_line_id': schedule_item.order_line_id.id,
												'pump_model_id': schedule_item.order_line_id.pump_model_id.id,
												'qty' : qc_qty,
												'stock_qty': qc_qty,				   
												'allocated_qty':qc_qty,				 
												'state' : 'draft',
												'order_category':schedule_item.order_id.order_category,
												'order_priority':priority,
												'pattern_id' : schedule_item.pattern_id.id,
												'pattern_name' : schedule_item.pattern_id.pattern_name,	
												'moc_id' : schedule_item.moc_id.id,
												'stock_type': 'pattern',
												'order_bomline_id': schedule_item.order_bomline_id.id,
												'stock_location_id': stock_item['stock_location_id'],
												'stock_inward_id': stock_item['id'],
												'qc_type': 'foundry',
												'item_code': schedule_item.pattern_id.name,
												'item_name': schedule_item.pattern_id.pattern_name,
												'heat_no': stock_item['heat_no'],
												
														
												}
												
											
											qc_id = qc_obj.create(cr, uid, qc_vals)
											print "qc_id",qc_id
											### Qty Updation in Stock Inward ###
											
											inward_line_obj = self.pool.get('ch.stock.inward.details')
											
											stock_updation_qty = qc_qty
											
											if stock_updation_qty > 0:
												
												if stock_item['stock_qty'] <= stock_updation_qty:
													stock_avail_qty = 0
													inward_line_obj.write(cr, uid, [stock_item['id']],{'available_qty': stock_avail_qty})
												if stock_item['stock_qty'] > stock_updation_qty:
													stock_avail_qty = stock_item['stock_qty'] - stock_updation_qty
													inward_line_obj.write(cr, uid, [stock_item['id']],{'available_qty': stock_avail_qty})
					
										print "reject_rem_qtyreject_rem_qtyreject_rem_qtyreject_rem_qty",reject_rem_qty								
													
							### Checking in Stock Inward for Foundry In Progress ###
							
							cr.execute(""" select sum(available_qty) as stock_qty
								from ch_stock_inward_details  
								where pattern_id = %s and moc_id = %s
								and foundry_stock_state = 'foundry_inprogress' and available_qty > 0 and stock_type = 'pattern' """%(schedule_item.pattern_id.id,schedule_item.moc_id.id))
							stock_inward_qty = cr.fetchone();

							if stock_inward_qty:
								if stock_inward_qty[0] != None:
									
									allocated_qty = 0
									
									rem_qty = reject_rem_qty
									
									### Checking STK WO ##
									
									cr.execute(""" select id,order_id,order_line_id,order_no,state,inward_accept_qty,
										stage_id,stage_name,state from kg_fettling where order_id = 
										(select id from kg_work_order where flag_for_stock = 't')
										and pattern_id = %s and moc_id = %s and state != 'complete' """%(schedule_item.pattern_id.id,schedule_item.moc_id.id))
									stk_ids = cr.dictfetchall();
									
									if stk_ids:
									
										for stk_item in stk_ids:
											
											### Qty Updation in Stock Inward ###
										
											inward_line_obj = self.pool.get('ch.stock.inward.details')
											
											cr.execute(""" select id,available_qty
												from ch_stock_inward_details  
												where pattern_id = %s and moc_id = %s
												and foundry_stock_state = 'foundry_inprogress' 
												and available_qty > 0 and stock_type = 'pattern' """%(schedule_item.pattern_id.id,schedule_item.moc_id.id))
												
											stock_inward_items = cr.dictfetchall();
											
											stock_updation_qty = rem_qty
											
											for stock_inward_item in stock_inward_items:
												if stock_updation_qty > 0:
													
													if stock_inward_item['available_qty'] <= stock_updation_qty:
														stock_avail_qty = 0
														inward_line_obj.write(cr, uid, [stock_inward_item['id']],{'available_qty': stock_avail_qty})
													if stock_inward_item['available_qty'] > stock_updation_qty:
														stock_avail_qty = stock_inward_item['available_qty'] - stock_updation_qty
														inward_line_obj.write(cr, uid, [stock_inward_item['id']],{'available_qty': stock_avail_qty})
														
													if stock_inward_item['available_qty'] <= stock_updation_qty:
														stock_updation_qty = stock_updation_qty - stock_inward_item['available_qty']
													elif stock_inward_item['available_qty'] > stock_updation_qty:
														stock_updation_qty = 0

											fettling_obj = self.pool.get('kg.fettling')
											
											stk_item_rec = fettling_obj.browse(cr, uid, stk_item['id'])
											
											### Order Priority ###
											
											#~ if schedule_item.order_id.order_category in ('pump','pump_spare','project'):
												#~ if schedule_item.order_id.order_priority == 'normal':
													#~ priority = '6'
												#~ if schedule_item.order_id.order_priority == 'emergency':
													#~ priority = '4'
											#~ if schedule_item.order_id.order_category == 'service':
												#~ priority = '3'
											#~ if schedule_item.order_id.order_category == 'spare':
												#~ priority = '5'
												
											if schedule_item.order_id.order_category in ('pump','pump_spare','project','access'):
												if schedule_item.order_id.order_priority == 'normal':
													priority = '8'
												if schedule_item.order_id.order_priority == 'emergency':
													priority = '3'
												if schedule_item.order_id.order_priority == 'breakdown':
													priority = '2'
												if schedule_item.order_id.order_priority == 'urgent':
													priority = '7'
											if schedule_item.order_id.order_category == 'service':
												priority = '4'
											if schedule_item.order_id.order_category == 'spare':
												priority = '6'
											
											if rem_qty > 0:
												### Sequence Number Generation ###
												fettling_name = ''  
												fettling_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.fettling.inward')])
												seq_rec = self.pool.get('ir.sequence').browse(cr,uid,fettling_seq_id[0])
												cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(fettling_seq_id[0],seq_rec.code))
												fettling_name = cr.fetchone();
												
												fettling_vals = {
													'name': fettling_name[0],
													'location':entry.location,
													'schedule_id':entry.id,
													'schedule_date':entry.entry_date,
													'schedule_line_id':schedule_item.id,
													'order_bomline_id':schedule_item.order_bomline_id.id,
													'order_id':schedule_item.order_id.id,
													'order_line_id':schedule_item.order_line_id.id,
													'order_no':schedule_item.order_no,
													'order_delivery_date':schedule_item.order_line_id.delivery_date,
													'order_date':schedule_item.order_id.entry_date,
													'order_category':schedule_item.order_id.order_category,
													'order_priority':priority,
													'pump_model_id':schedule_item.pump_model_id.id,
													'pattern_id':schedule_item.pattern_id.id,
													'pattern_code':schedule_item.pattern_id.name,
													'pattern_name':schedule_item.pattern_name,
													'moc_id':schedule_item.moc_id.id,
													'schedule_qty':rem_qty,
													'pour_qty':rem_qty,
													'inward_accept_qty': rem_qty,
													'state':'waiting',
													
													
													
													}
												   
												fettling_id = fettling_obj.create(cr, uid, fettling_vals)
												
												
												if stk_item['stage_name'] == None:
													
													### Updation in STK WO ###
													stk_rem_qty =  stk_item_rec.inward_accept_qty - rem_qty
													if stk_rem_qty > 0:
														fettling_obj.write(cr, uid, stk_item['id'], {'inward_accept_qty': stk_rem_qty})
													else:
														fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
														
													if rem_qty <= stk_item_rec.inward_accept_qty:
														inward_accept_qty = rem_qty
													if rem_qty > stk_item_rec.inward_accept_qty:
														inward_accept_qty = stk_item_rec.inward_accept_qty
														
													fettling_obj.write(cr, uid, fettling_id, {'inward_accept_qty': inward_accept_qty,'allocated_qty':inward_accept_qty,
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
													fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':knockout_qty,'inward_accept_qty': knockout_qty,
													'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'knockout_date':time.strftime('%Y-%m-%d'),'knockout_qty': knockout_qty,'knockout_accept_qty':knockout_qty,'knockout_name':knockout_name[0],'allocated_qty':knockout_qty,
															'flag_allocated':'t','allocated_accepted_qty':knockout_qty,'allocation_state':'waiting'})
													
													### Updation in STK WO ###
													stk_rem_qty =  stk_knockout_qty - knockout_qty
													if stk_rem_qty > 0:
														fettling_obj.write(cr, uid, stk_item['id'], {'knockout_qty': stk_rem_qty,'knockout_accept_qty':stk_rem_qty})
													else:
														fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
														
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
													fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':decoring_qty,'inward_accept_qty': decoring_qty,'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'decoring_date':time.strftime('%Y-%m-%d'),
														'decoring_qty': decoring_qty,'decoring_accept_qty':decoring_qty,'decoring_name':decoring_name[0],'allocated_qty':decoring_qty,
																'flag_allocated':'t','allocated_accepted_qty':decoring_qty,'allocation_state':'waiting'})
													
													### Updation in STK WO ###
													stk_rem_qty =  stk_decoring_qty - decoring_qty
													if stk_rem_qty > 0:
														fettling_obj.write(cr, uid, stk_item['id'], {'decoring_qty': stk_rem_qty,'decoring_accept_qty':stk_rem_qty})
													else:
														fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
														
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
													fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':shot_blast_qty,'inward_accept_qty': shot_blast_qty,
														'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'shot_blast_date':time.strftime('%Y-%m-%d'),
														'shot_blast_qty': shot_blast_qty,'shot_blast_accept_qty':shot_blast_qty,'shot_blast_name':shot_blast_name[0],'allocated_qty':shot_blast_qty,
																'flag_allocated':'t','allocated_accepted_qty':shot_blast_qty,'allocation_state':'waiting'})
												
													### Updation in STK WO ###
													stk_rem_qty =  stk_shot_blast_qty - shot_blast_qty
													if stk_rem_qty > 0:
														fettling_obj.write(cr, uid, stk_item['id'], {'shot_blast_qty': stk_rem_qty,'shot_blast_accept_qty':stk_rem_qty})
													else:
														fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
												
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
													fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':hammering_qty,'inward_accept_qty': hammering_qty,
													'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'hammering_date':time.strftime('%Y-%m-%d'),
													'hammering_qty': hammering_qty,'hammering_accept_qty': hammering_qty,'hammering_name':hammering_name[0],'allocated_qty':hammering_qty,
														'flag_allocated':'t','allocated_accepted_qty':hammering_qty,'allocation_state':'waiting'})
												
													### Updation in STK WO ###
													stk_rem_qty =  stk_hammering_qty - hammering_qty
													if stk_rem_qty > 0:
														fettling_obj.write(cr, uid, stk_item['id'], {'hammering_qty': stk_rem_qty,'hammering_accept_qty':stk_rem_qty})
													else:
														fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
														
														
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
													fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':wheel_cutting_qty,'inward_accept_qty': wheel_cutting_qty,
														'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'wheel_cutting_date':time.strftime('%Y-%m-%d'),
														'wheel_cutting_qty': wheel_cutting_qty,'wheel_cutting_accept_qty': wheel_cutting_qty,'wheel_cutting_name':wheel_cutting_name[0],'allocated_qty':wheel_cutting_qty,
															'flag_allocated':'t','allocated_accepted_qty':wheel_cutting_qty,'allocation_state':'waiting'})
												
													### Updation in STK WO ###
													stk_rem_qty =  stk_wheel_cutting_qty - wheel_cutting_qty
													if stk_rem_qty > 0:
														fettling_obj.write(cr, uid, stk_item['id'], {'wheel_cutting_qty': stk_rem_qty,'wheel_cutting_accept_qty':stk_rem_qty})
													else:
														fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
														
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
													fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':gas_cutting_qty,'inward_accept_qty': gas_cutting_qty,
													'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'gas_cutting_date':time.strftime('%Y-%m-%d'),
													'gas_cutting_qty': gas_cutting_qty,'gas_cutting_accept_qty': gas_cutting_qty,'gas_cutting_name':gas_cutting_name[0],'allocated_qty':gas_cutting_qty,
														'flag_allocated':'t','allocated_accepted_qty':gas_cutting_qty,'allocation_state':'waiting'})
												
													### Updation in STK WO ###
													stk_rem_qty =  stk_gas_cutting_qty - gas_cutting_qty
													if stk_rem_qty > 0:
														fettling_obj.write(cr, uid, stk_item['id'], {'gas_cutting_qty': stk_rem_qty,'gas_cutting_accept_qty':stk_rem_qty})
													else:
														fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
														
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
													fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':arc_cutting_qty,'inward_accept_qty': arc_cutting_qty,
													'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'arc_cutting_date':time.strftime('%Y-%m-%d'),
													'arc_cutting_qty': arc_cutting_qty,'arc_cutting_accept_qty': arc_cutting_qty,'arc_cutting_name':arc_cutting_name[0],'allocated_qty':arc_cutting_qty,
														'flag_allocated':'t','allocated_accepted_qty':arc_cutting_qty,'allocation_state':'waiting'})
												
													### Updation in STK WO ###
													stk_rem_qty =  stk_arc_cutting_qty - arc_cutting_qty
													if stk_rem_qty > 0:
														fettling_obj.write(cr, uid, stk_item['id'], {'arc_cutting_qty': stk_rem_qty,'arc_cutting_accept_qty':stk_rem_qty})
													else:
														fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
														
													allocated_qty = arc_cutting_qty
												
												
												if stk_item['stage_name'] == 'HEAT TREATMENT1':
													
													stk_heat_qty = stk_item_rec.heat_qty
													
													if rem_qty <= stk_heat_qty:
														heat_total_qty = rem_qty
													if rem_qty > stk_heat_qty:
														heat_total_qty = stk_heat_qty
													
													fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':heat_total_qty,'inward_accept_qty': heat_total_qty,
													'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'heat_date':time.strftime('%Y-%m-%d'),
													'heat_total_qty': heat_total_qty,'heat_qty':heat_total_qty,'allocated_qty':heat_total_qty,
														'flag_allocated':'t','allocated_accepted_qty':heat_total_qty,'allocation_state':'waiting'})
												
													### Updation in STK WO ###
													stk_rem_qty =  stk_heat_qty - heat_total_qty
													if stk_rem_qty > 0:
														fettling_obj.write(cr, uid, stk_item['id'], {'heat_total_qty': stk_rem_qty,'heat_qty':stk_rem_qty})
													else:
														fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
														
														
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
													fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':rough_grinding_qty,'inward_accept_qty': rough_grinding_qty,
													'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'rough_grinding_date':time.strftime('%Y-%m-%d'),
													'rough_grinding_qty': rough_grinding_qty,'rough_grinding_accept_qty': rough_grinding_qty,
													'rough_grinding_name':rough_grinding_name[0],'allocated_qty':rough_grinding_qty,
														'flag_allocated':'t','allocated_accepted_qty':rough_grinding_qty,'allocation_state':'waiting'})
												
													### Updation in STK WO ###
													stk_rem_qty =  stk_rough_grinding_qty - rough_grinding_qty
													if stk_rem_qty > 0:
														fettling_obj.write(cr, uid, stk_item['id'], {'rough_grinding_qty': stk_rem_qty,'rough_grinding_accept_qty':stk_rem_qty})
													else:
														fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
														
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
													fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':finish_grinding_qty,'inward_accept_qty': finish_grinding_qty,
													'pour_qty':finish_grinding_qty,'inward_accept_qty': finish_grinding_qty,'stage_id':stk_item['stage_id'],
													'stage_name':stk_item['stage_name'],'finish_grinding_date':time.strftime('%Y-%m-%d'),'finish_grinding_qty': finish_grinding_qty,
													'finish_grinding_accept_qty': finish_grinding_qty,'finish_grinding_name':finish_grinding_name[0],'allocated_qty':finish_grinding_qty,
														'flag_allocated':'t','allocated_accepted_qty':finish_grinding_qty,'allocation_state':'waiting'})
													
													### Updation in STK WO ###
													stk_rem_qty =  stk_finish_grinding_qty - finish_grinding_qty
													if stk_rem_qty > 0:
														fettling_obj.write(cr, uid, stk_item['id'], {'finish_grinding_qty': stk_rem_qty,'finish_grinding_accept_qty':stk_rem_qty})
													else:
														fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
														
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
													fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':reshot_blasting_qty,'inward_accept_qty': reshot_blasting_qty,
													'stage_id':stk_item['stage_id'],'stage_name':stk_item['stage_name'],'reshot_blasting_date':time.strftime('%Y-%m-%d'),
													'reshot_blasting_qty': reshot_blasting_qty,'reshot_blasting_accept_qty': reshot_blasting_qty,'reshot_blasting_name':reshot_blasting_name[0],'allocated_qty':reshot_blasting_qty,
														'flag_allocated':'t','allocated_accepted_qty':reshot_blasting_qty,'allocation_state':'waiting'})
											
													### Updation in STK WO ###
													stk_rem_qty =  stk_reshot_blasting_qty - reshot_blasting_qty
													if stk_rem_qty > 0:
														fettling_obj.write(cr, uid, stk_item['id'], {'reshot_blasting_qty': stk_rem_qty,'reshot_blasting_accept_qty':stk_rem_qty})
													else:
														fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
														
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
													fettling_obj.write(cr, uid, fettling_id, {'state':'accept','pour_qty':welding_qty,'inward_accept_qty': welding_qty,'stage_id':stk_item['stage_id'],
													'stage_name':stk_item['stage_name'],'welding_date':time.strftime('%Y-%m-%d'),
													'welding_qty': welding_qty,'welding_accept_qty': welding_qty,
													'welding_name':welding_name[0],'allocated_qty':welding_qty,
														'flag_allocated':'t','allocated_accepted_qty':welding_qty,'allocation_state':'waiting'})
											
													### Updation in STK WO ###
													stk_rem_qty =  stk_welding_qty - welding_qty
													if stk_rem_qty > 0:
														fettling_obj.write(cr, uid, stk_item['id'], {'welding_qty': stk_rem_qty,'welding_accept_qty':stk_rem_qty})
													else:
														fettling_obj.write(cr, uid, stk_item['id'], {'state':'complete'})
														
													allocated_qty = welding_qty
											
											
											rem_qty = rem_qty - allocated_qty
										
							
						else:
							schedule_qty = schedule_item.qty
					else:
						schedule_qty = schedule_item.qty
						
					schedule_line_obj.write(cr, uid,schedule_item.id,{'qty':schedule_qty})
					### Production Creation When No Allocation ####
						
					#~ if schedule_item.order_id.order_category in ('pump','pump_spare','project'):
						#~ if schedule_item.order_id.order_priority == 'normal':
							#~ priority = '6'
						#~ if schedule_item.order_id.order_priority == 'emergency':
							#~ priority = '4'
					#~ if schedule_item.order_id.order_category == 'service':
						#~ priority = '3'
					#~ if schedule_item.order_id.order_category == 'spare':
						#~ priority = '5'
						
					if schedule_item.order_id.order_category in ('pump','pump_spare','project','access'):
						if schedule_item.order_id.order_priority == 'normal':
							priority = '8'
						if schedule_item.order_id.order_priority == 'emergency':
							priority = '3'
						if schedule_item.order_id.order_priority == 'breakdown':
							priority = '2'
						if schedule_item.order_id.order_priority == 'urgent':
							priority = '7'
					if schedule_item.order_id.order_category == 'service':
						priority = '4'
					if schedule_item.order_id.order_category == 'spare':
						priority = '6'
					
					if schedule_item.order_bomline_id.flag_pattern_check == True or schedule_item.pattern_id.pattern_state != 'active':
						issue_state = 'pending'
					else:
						issue_state = 'issued'
						
					if schedule_qty > 0:
						
						if issue_state == 'pending':
							
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
							
						
							production_vals = {
													
								'name': produc_name[0],
								'schedule_id': entry.id,
								'schedule_date': entry.entry_date,
								'division_id': entry.division_id.id,
								'location' : entry.location,
								'schedule_line_id': schedule_item.id,
								'order_id': schedule_item.order_id.id,
								'order_line_id': schedule_item.order_line_id.id,
								'order_bomline_id': schedule_item.order_bomline_id.id,
								'qty' : schedule_qty,			  
								'schedule_qty' : schedule_qty,			  
								'state' : 'issue_pending',
								'order_category':schedule_item.order_id.order_category,
								'order_priority':priority,
								'pattern_id' : schedule_item.pattern_id.id,
								'pattern_name' : schedule_item.pattern_id.pattern_name,	
								'moc_id' : schedule_item.moc_id.id,
								'request_state': 'done',
								'issue_no': issue_name[0],
								'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
								'issue_qty': 1,
								'issue_state': issue_state,
								'sch_remarks': schedule_item.order_bomline_id.add_spec,
								'flag_pattern_check': True,
								
							}
							
						if issue_state == 'issued':
							
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
								'schedule_id': entry.id,
								'schedule_date': entry.entry_date,
								'division_id': entry.division_id.id,
								'location' : entry.location,
								'schedule_line_id': schedule_item.id,
								'order_id': schedule_item.order_id.id,
								'order_value': schedule_item.order_line_id.unit_price,
								'order_line_id': schedule_item.order_line_id.id,
								'order_bomline_id': schedule_item.order_bomline_id.id,
								'qty' : schedule_qty,			  
								'schedule_qty' : schedule_qty,			  
								'state' : 'issue_done',
								'order_category':schedule_item.order_id.order_category,
								'order_priority':priority,
								'pattern_id' : schedule_item.pattern_id.id,
								'pattern_name' : schedule_item.pattern_id.pattern_name,	
								'moc_id' : schedule_item.moc_id.id,
								'sch_remarks': schedule_item.order_bomline_id.add_spec,
								'request_state': 'done',
								'issue_no': issue_name[0],
								'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
								'issue_qty': 1,
								'issue_state': issue_state,
								'core_no': core_name[0],
								'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
								'core_qty': schedule_qty,
								'core_rem_qty': schedule_qty,
								'core_state': 'pending',
								
								'mould_no': mould_name[0],
								'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
								'mould_qty': schedule_qty,
								'mould_rem_qty': schedule_qty,
								'mould_state': 'pending',
								
							}
							
							
					
						production_id = production_obj.create(cr, uid, production_vals)						
					
					if schedule_item.order_bomline_id.id != False:
						position_id = schedule_item.order_bomline_id.position_id.id
						spare_id = schedule_item.order_bomline_id.spare_id.id
					if schedule_item.order_bomline_id.id == False:
						position_id = schedule_item.acc_bomline_id.position_id.id
						spare_id = schedule_item.order_bomline_id.spare_id
					### Foundry Item Machine Shop Creation Process ###
						
					ms_fou_obj = self.pool.get('kg.machineshop')						
					
					### Sequence Number Generation ###
					ms_name = ''	
					ms_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.ms.inward')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,ms_seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(ms_seq_id[0],seq_rec.code))
					ms_name = cr.fetchone();
					
					ms_foun_vals = {
						'name': ms_name[0],
						'location':entry.location,
						'schedule_id':entry.id,
						'schedule_date':entry.entry_date,
						'schedule_line_id':schedule_item.id,
						'order_bomline_id':schedule_item.order_bomline_id.id,
						'order_id':schedule_item.order_id.id,
						'order_line_id':schedule_item.order_line_id.id,
						'order_no':schedule_item.order_no,
						'order_delivery_date':schedule_item.order_line_id.delivery_date,
						'order_date':schedule_item.order_id.entry_date,
						'order_category':schedule_item.order_id.order_category,
						'order_priority':priority,
						'pump_model_id':schedule_item.pump_model_id.id,
						'pattern_id':schedule_item.pattern_id.id,
						'pattern_code':schedule_item.pattern_id.name,
						'pattern_name':schedule_item.pattern_id.pattern_name,
						'moc_id':schedule_item.moc_id.id,
						'schedule_qty':schedule_item.order_qty,						
						'fettling_qty':0,
						'inward_accept_qty':0,
						'state':'pending',
						'ms_sch_qty': schedule_item.order_qty,
						'ms_type': 'foundry_item',
						'item_code': schedule_item.pattern_id.name,
						'item_name': schedule_item.pattern_id.pattern_name,
						'position_id': position_id,
						'oth_spec': schedule_item.order_bomline_id.add_spec,
						'flag_trimming_dia': schedule_item.order_bomline_id.flag_trimming_dia,
						'bom_type': schedule_item.order_bomline_id.bom_type,
						'spare_id': spare_id,
						'ms_plan_rem_qty':schedule_item.order_qty,
					
					}						
						
					ms_fou_id = ms_fou_obj.create(cr, uid, ms_foun_vals)		
					
					### Trimming dia creation for Foundry and Acc ###
					if schedule_item.pattern_id.need_dynamic_balancing == True:
						trim_dia_obj = self.pool.get('kg.trimming.dia')
						enq_line_obj = self.pool.get('ch.kg.crm.pumpmodel')
						enq_line_rec = enq_line_obj.browse(cr,uid,schedule_item.order_line_id.enquiry_line_id)
			
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
						foundry_bom_id = acc_foundry_bom_id = 0
						if schedule_item.order_bomline_id.id > 0:
							foundry_bom_id = schedule_item.order_bomline_id.id
							self.pool.get('ch.order.bom.details').write(cr,uid,schedule_item.order_bomline_id.id,{'flag_trimming_dia':True})
						elif schedule_item.acc_bomline_id.id > 0:
							acc_foundry_bom_id = schedule_item.acc_bomline_id.id
							self.pool.get('ch.wo.accessories.foundry').write(cr,uid,schedule_item.acc_bomline_id.id,{'flag_trimming_dia':True})
						
						dia_vals = { 
							'order_line_id': schedule_item.order_line_id.id,
							'order_bomline_id': foundry_bom_id,
							'acc_bomline_id': acc_foundry_bom_id,
							'order_category': schedule_item.order_line_id.order_category,		
							'pump_model_type': schedule_item.order_line_id.pump_model_type,
							'pump_model_id': schedule_item.order_line_id.pump_model_id.id,
							'pattern_id': schedule_item.pattern_id.id,
							'capacity_in': capacity_in,
							'head_in': head_in,
							'bkw_water': bkw_water,
							'speed_in_rpm': speed_in_rpm,
							'efficiency_in': efficiency_in,
							'motor_kw': motor_kw,
							'trimming_dia': schedule_item.order_line_id.trimming_dia,
							'old_ref': old_ref,
						}
						trim_dia_obj.create(cr,uid,dia_vals)
					
						
						
					if ms_no == 1:					
						
						### Machine shop Item Creation ####
						cr.execute("""
							select order_ms.id as order_ms_line_id,order_ms.qty as sch_qty,order_ms.ms_id as ms_id,order_ms.name as item_name,
							order_ms.bom_id as ms_bom_id,order_ms.ms_line_id as ms_bom_line_id ,order_ms.position_id,
							order_ms.moc_id,'pump' as purpose,wo_line.order_no as order_no,wo_line.id as order_line_id,
							wo_line.header_id as order_id,wo_line.delivery_date,wo.order_category,
							wo_line.pump_model_id,wo.entry_date as order_date

							from ch_order_machineshop_details order_ms
							left join ch_work_order_details wo_line on order_ms.header_id = wo_line.id
							left join kg_work_order wo on wo_line.header_id = wo.id
							where order_ms.flag_applicable = 't' and order_ms.header_id in 
							(select order_line_id from ch_schedule_details where header_id = %s
							)

							union 

							select acc_order_ms.id as order_ms_line_id,acc_order_ms.qty as sch_qty,acc_order_ms.ms_id as ms_id,
							acc_order_ms.name as item_name,
							acc_order_ms.bom_id as ms_bom_id,0 as ms_bom_line_id ,acc_order_ms.position_id,
							acc_order_ms.moc_id,'acc' as purpose,wo_line.order_no as order_no,wo_line.id as order_line_id,
							wo_line.header_id as order_id,wo_line.delivery_date,wo.order_category,
							wo_line.pump_model_id,wo.entry_date as order_date
							from ch_wo_accessories_ms as acc_order_ms
							left join ch_wo_accessories wo_acc_line on acc_order_ms.header_id = wo_acc_line.id
							left join ch_work_order_details wo_line on wo_acc_line.header_id = wo_line.id
							left join kg_work_order wo on wo_line.header_id = wo.id
							where acc_order_ms.is_applicable = 't' and wo_acc_line.header_id in 
							(select order_line_id from ch_schedule_details where header_id = %s
							) """%(entry.id,entry.id))
						order_ms_details = cr.dictfetchall();
						
						if order_ms_details:
						
							for ms_item in order_ms_details:
								
								if ms_item['purpose'] == 'pump':
									order_ms_line_id = ms_item['order_ms_line_id']
									acc_ms_line_id = False
									ms_bom_line_id = ms_item['ms_bom_line_id']
								if ms_item['purpose'] == 'acc':
									order_ms_line_id = False
									acc_ms_line_id = ms_item['order_ms_line_id']
									ms_bom_line_id = False
									
								ms_obj = self.pool.get('kg.machineshop')
								ms_master_obj = self.pool.get('kg.machine.shop')
								ms_rec = ms_master_obj.browse(cr, uid, ms_item['ms_id'])
								
								if ms_item['purpose'] == 'pump':
									if order_ms_line_id != False:
										order_ms_rec = self.pool.get('ch.order.machineshop.details').browse(cr, uid, order_ms_line_id)
										oth_spec = order_ms_rec.remarks
										bom_type = order_ms_rec.bom_type
										spare_id = order_ms_rec.spare_id.id
									else:
										oth_spec = ''
										bom_type = ''
										spare_id = False
								if ms_item['purpose'] == 'acc':
									if order_ms_line_id != False:
										order_ms_rec = self.pool.get('ch.wo.accessories.ms').browse(cr, uid, order_ms_line_id)
										oth_spec = order_ms_rec.remarks
										bom_type = ''
										spare_id = False
									else:
										oth_spec = ''
										bom_type = ''
										spare_id = False
								
								
								### Checking MS Stock list and creating ms qc verification ###
								reject_rem_qty = ms_item['sch_qty']
							
								### Checking in Stock Inward for Ready for MS ###
								item_code = "'"+ms_rec.code+"'"
								item_name = "'"+ms_item['item_name']+"'"
								print "item_code",item_code
								print "item_name",item_name
								print "ms_item['moc_id']",ms_item['moc_id']
								print "ms_item['order_no']",ms_item['order_no']
								cr.execute(""" select id,available_qty as stock_qty,stock_location_id 
									from ch_stock_inward_details  
									where item_code = %s and item_name= %s and moc_id = %s and stock_item = 'ms_item'
									and ms_stock_state != 'reject' and available_qty > 0  and stock_type = 'pattern'
									and position_id = %s 
									order by id asc """%(item_code,item_name,ms_item['moc_id'],ms_item['position_id']))
								stock_inward_items = cr.dictfetchall();
								print "stock_inward_items---------------------------->>>",stock_inward_items
								
								if stock_inward_items:
									print "reject_rem_qty",reject_rem_qty
									if reject_rem_qty > 0:
										for stock_item in  stock_inward_items:
											if reject_rem_qty > 0:
												if stock_item['stock_qty'] != None:
													allocate_qty =  reject_rem_qty - stock_item['stock_qty']
													print "reject_rem_qty",reject_rem_qty
													if allocate_qty <= 0:
														qc_qty = reject_rem_qty
														reject_rem_qty = 0
														
													else:
														reject_rem_qty = allocate_qty
														qc_qty = stock_item['stock_qty']
												print "qc_qty",qc_qty
												
												### Creating QC Verification ###
												
												qc_obj = self.pool.get('kg.qc.verification')
												
												### QC Sequence Number Generation  ###
												qc_name = ''	
												qc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.qc.verification')])
												rec = self.pool.get('ir.sequence').browse(cr,uid,qc_seq_id[0])
												cr.execute("""select generatesequenceno(%s,'%s','%s') """%(qc_seq_id[0],rec.code,schedule_item.header_id.entry_date))
												qc_name = cr.fetchone();
											
												qc_vals = {
																				
													'name': qc_name[0],
													'schedule_id': entry.id,
													'schedule_date': entry.entry_date,
													'division_id': entry.division_id.id,
													'location' : entry.location,
													'schedule_line_id': schedule_item.id,
													'order_id': schedule_item.order_id.id,
													'order_line_id': schedule_item.order_line_id.id,
													'pump_model_id': schedule_item.order_line_id.pump_model_id.id,
													'qty' : qc_qty,
													'stock_qty': qc_qty,				   
													'allocated_qty':qc_qty,				 
													'state' : 'draft',
													'order_category':schedule_item.order_id.order_category,
													'order_priority':priority,
													'item_code': ms_rec.code,
													'item_name': ms_item['item_name' ],
													'moc_id' : schedule_item.moc_id.id,
													'stock_type': 'pattern',
													'order_bomline_id': schedule_item.order_bomline_id.id,
													'stock_location_id': stock_item['stock_location_id'],
													'stock_inward_id': stock_item['id'],
													'qc_type': 'ms',
													'position_id':ms_item['position_id'],
													'order_ms_line_id': order_ms_line_id,
													'acc_ms_line_id': acc_ms_line_id,
													'ms_id': ms_item['ms_id'],
													
															
													}
													
												
												qc_id = qc_obj.create(cr, uid, qc_vals)
												
												### Qty Updation in Stock Inward ###
												
												inward_line_obj = self.pool.get('ch.stock.inward.details')
												
												stock_updation_qty = qc_qty
												
												if stock_updation_qty > 0:
													
													if stock_item['stock_qty'] <= stock_updation_qty:
														stock_avail_qty = 0
														inward_line_obj.write(cr, uid, [stock_item['id']],{'available_qty': stock_avail_qty})
													if stock_item['stock_qty'] > stock_updation_qty:
														stock_avail_qty = stock_item['stock_qty'] - stock_updation_qty
														inward_line_obj.write(cr, uid, [stock_item['id']],{'available_qty': stock_avail_qty})
														
												if ms_item['purpose'] == 'pump':
													if order_ms_line_id != False:
														order_ms_rec = self.pool.get('ch.order.machineshop.details').browse(cr, uid, order_ms_line_id)
														print "order_ms_rec.indent_qty>>>>>>>>>>>>>>>",order_ms_rec.indent_qty,qc_qty
														if order_ms_rec.indent_qty > 0:
															self.pool.get('ch.order.machineshop.details').write(cr, uid, order_ms_line_id,
															{'indent_qty':order_ms_rec.indent_qty - qc_qty})
												if ms_item['purpose'] == 'acc':
													if order_ms_line_id != False:
														order_ms_rec = self.pool.get('ch.wo.accessories.ms').browse(cr, uid, order_ms_line_id)
														if order_ms_rec.indent_qty > 0:
															self.pool.get('ch.wo.accessories.ms').browse(cr, uid, order_ms_line_id,
															{'indent_qty':order_ms_rec.indent_qty - qc_qty})
												
								print "lssssssssss",reject_rem_qty					
								if reject_rem_qty > 0:
									
									### Sequence Number Generation ###
									ms_name = ''	
									ms_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.ms.inward')])
									seq_rec = self.pool.get('ir.sequence').browse(cr,uid,ms_seq_id[0])
									cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(ms_seq_id[0],seq_rec.code))
									ms_name = cr.fetchone();
									
									ms_vals = {
									
									'order_ms_line_id': order_ms_line_id,
									'acc_ms_line_id': acc_ms_line_id,
									'name': ms_name[0],
									'location': entry.location,
									'schedule_id': entry.id,
									'schedule_date': entry.entry_date,
									'schedule_line_id': schedule_item.id,
									'order_id': ms_item['order_id'],
									'order_line_id':ms_item['order_line_id'],
									'order_no': ms_item['order_no'],
									'order_delivery_date': ms_item['delivery_date'],
									'order_date': ms_item['order_date'],
									'order_category': ms_item['order_category'],
									'order_priority': priority,
									'pump_model_id':ms_item['pump_model_id'],
									'moc_id':ms_item['moc_id'],
									'schedule_qty':reject_rem_qty,
									'ms_sch_qty':reject_rem_qty,
									'ms_plan_rem_qty':reject_rem_qty,
									'ms_type': 'ms_item',
									'ms_state': 'in_plan',
									'state':'pending',
									'ms_id': ms_item['ms_id'],
									'ms_bom_id': ms_item['ms_bom_id'],
									'ms_bom_line_id': ms_bom_line_id,
									'position_id': ms_item['position_id'],
									'item_code': ms_rec.code,
									'item_name': ms_item['item_name' ],
									'oth_spec': oth_spec,
									'bom_type': bom_type,
									'spare_id': spare_id,
									
									}
									
									print "ms_vals",ms_vals
									
									ms_no = ms_no + 1
								
									ms_id = ms_obj.create(cr, uid, ms_vals)
									
						
						### BOT Item Creation in Finished part list ###
						
						cr.execute("""
							select order_bot.id as order_bot_line_id,order_bot.qty as bot_qty,order_bot.bot_id as bot_id,order_bot.item_name as item_name,
							order_bot.moc_id,'pump' as purpose,wo_line.order_no as order_no,wo_line.id as order_line_id,
							wo_line.header_id as order_id,wo_line.delivery_date,wo.order_category,
							wo_line.pump_model_id,wo.entry_date as order_date

							from ch_order_bot_details order_bot
							left join ch_work_order_details wo_line on order_bot.header_id = wo_line.id
							left join kg_work_order wo on wo_line.header_id = wo.id
							where order_bot.flag_applicable = 't' and order_bot.header_id in 
							(select order_line_id from ch_schedule_details where header_id = %s
							)

							union 

							select acc_order_bot.id as order_bot_line_id,acc_order_bot.qty as bot_qty,acc_order_bot.ms_id as bot_id,
							acc_order_bot.item_name as item_name,
							acc_order_bot.moc_id,'acc' as purpose,wo_line.order_no as order_no,wo_line.id as order_line_id,
							wo_line.header_id as order_id,wo_line.delivery_date,wo.order_category,
							wo_line.pump_model_id,wo.entry_date as order_date
							from ch_wo_accessories_bot as acc_order_bot
							left join ch_wo_accessories wo_acc_line on acc_order_bot.header_id = wo_acc_line.id
							left join ch_work_order_details wo_line on wo_acc_line.header_id = wo_line.id
							left join kg_work_order wo on wo_line.header_id = wo.id
							where acc_order_bot.is_applicable = 't' and wo_acc_line.header_id in 
							(select order_line_id from ch_schedule_details where header_id = %s
							) """%(entry.id,entry.id))
						order_bot_details = cr.dictfetchall();
						
						for order_bot_item in order_bot_details:
							
							if order_bot_item['purpose'] == 'pump':
								if order_bot_item['order_bot_line_id'] != False:
									order_bot_rec = self.pool.get('ch.order.bot.details').browse(cr, uid, order_bot_item['order_bot_line_id'])
									oth_spec = order_bot_rec.remarks
									bom_type = order_bot_rec.bom_type
									spare_id = order_bot_rec.spare_id.id
								else:
									oth_spec = ''
									bom_type = ''
									spare_id = False
							if order_bot_item['purpose'] == 'acc':
								if order_bot_item['order_bot_line_id'] != False:
									order_bot_rec = self.pool.get('ch.wo.accessories.bot').browse(cr, uid, order_bot_item['order_bot_line_id'])
									oth_spec = order_bot_rec.remarks
									bom_type = ''
									spare_id = False
								else:
									oth_spec = ''
									bom_type = ''
									spare_id = False
									
							
							bot_obj = self.pool.get('kg.machine.shop')
							bot_rec = bot_obj.browse(cr, uid, order_bot_item['bot_id'])
						
							bot_store_vals = {
								
								'order_id': order_bot_item['order_id'],
								'order_line_id': order_bot_item['order_line_id'],
								'oth_spec': oth_spec,
								'order_category': order_bot_item['order_category'],
								'order_priority': priority,
								'pump_model_id': order_bot_item['pump_model_id'],
								'item_code': bot_rec.code,
								'item_name': order_bot_item['item_name'],
								'bot_id': bot_rec.id,
								'moc_id': order_bot_item['moc_id'],
								'ms_type': 'bot_item',
								'qty': order_bot_item['bot_qty'],
								'state': 'in_store',
								'accept_state': 'pending',
								'bom_type': bom_type,
								'spare_id': spare_id,

							}
							bot_store_id = self.pool.get('kg.ms.stores').create(cr, uid, bot_store_vals)
					
				#### Department Indent Creation for MOC Raw materials  ###
				
				## Code Moved to scheduler Form
				
				
							
			else:
				raise osv.except_osv(_('Warning !'), _('System not allow to confirm an entry without Schedule details!!'))
				
			
			if entry.entry_mode == 'auto':
				#~ ### Sequence Number Generation  ###
				sch_name = ''
				if not entry.name:		
					sch_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.schedule')])
					rec = self.pool.get('ir.sequence').browse(cr,uid,sch_id[0])
					cr.execute("""select generatesequenceno(%s,'%s','%s') """%(sch_id[0],rec.code,entry.entry_date))
					sch_name = cr.fetchone();
					
					self.write(cr, uid, ids, {'name' :sch_name[0]})
			
			self.write(cr, uid, ids, {'state': 'confirmed','flag_cancel':1,'confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')
				})
				
			
			## Order Value Zero update code start
			
			cr.execute("""select distinct order_line_id from ch_schedule_details where header_id = %s"""%(entry.id))
			work_order = cr.fetchall();				
			for order_no in work_order:							
				cr.execute(''' update kg_production set order_value = 0 where order_line_id  = %s and id not in (select id from kg_production  where order_line_id  = %s order by id desc limit 1) ''',[order_no[0],order_no[0]])
			
			## Order Value Zero update code End
			
			
			cr.execute(''' update ch_schedule_details set state = 'confirmed' where header_id = %s ''',[ids[0]])
			
			### ID Commitment screen update ###
			cr.execute("""select distinct(order_line_id) from ch_schedule_details where header_id = %s """%(entry.id))
			order_ids = cr.fetchall();
			if order_ids:
				for order_item in order_ids:
					order_line_rec = self.pool.get('ch.work.order.details').browse(cr,uid,order_item[0])
					if order_line_rec.line_ids_d:
						accessories = 'yes'
					else:
						accessories = 'no'
					sch_vals = {
						'order_id': order_line_rec.header_id.id,
						'order_line_id': order_line_rec.id,
						'order_category': order_line_rec.order_category,		
						'pump_model_type':order_line_rec.pump_model_type,
						'order_priority': order_line_rec.order_priority,
						'delivery_date': order_line_rec.delivery_date,
						'inspection': order_line_rec.inspection,
						'spc_remarks': order_line_rec.note,
						'qty': order_line_rec.qty,
						'order_value': order_line_rec.unit_price * order_line_rec.qty,
						'pump_model_id': order_line_rec.pump_model_id.id,
						'division_id': order_line_rec.header_id.division_id.id,
						'location': order_line_rec.header_id.location,
						'schedule_id': entry.id,
						'accessories': accessories
					}
					self.pool.get('kg.id.commitment').create(cr,uid,sch_vals)
		
			
		else:
			pass
		
		self.sch_approval_mail(cr,uid,ids,rec,context)
		
		self.pool.get('kg.indent.queue').create(cr,uid,{
		
										'entry_date': entry.entry_date,									  
										'schedule_no': entry.name,
										'schedule_id': entry.id,
									})
		
		return True
	
	def sch_approval_mail(self,cr,uid,ids,obj,context=None):
		rec = self.browse(cr,uid,ids[0])
		mail_queue = self.pool.get('kg.mail.queue')
		cr.execute("""select trans_sch_approved('approved schedule',"""+str(rec.id)+""")""")
		data = cr.fetchall();
		if data[0][0] is None:
			return False
		if data[0][0] is not None:	
			maildet = (str(data[0])).rsplit('~');
			cont = data[0][0].partition('UNWANTED.')		
			email_from = maildet[1]	
			if maildet[2]:	
				email_to = [maildet[2]][0]
			else:
				email_to = ['']			
			if maildet[3]:
				email_cc = [maildet[3]][0]
			else:
				email_cc = ['']
			mail_queue.create(cr,uid,{'source': 'approved schedule',
									  'mail_to': email_to,
									  'mail_cc': email_cc,
									  'subject': maildet[4],
									  'body': cont[0],
									  'body_1': cont[0],
									  'user_id': uid,
									  'transaction_id': rec.id,
									})
		
		return True
		
		
	def entry_cancel(self,cr,uid,ids,context=None):
		qc_obj = self.pool.get('kg.qc.verification')
		order_line_obj = self.pool.get('ch.work.order.details')
		order_bomline_obj = self.pool.get('ch.order.bom.details')
		entry = self.browse(cr,uid,ids[0])
		if entry.cancel_remark == False:
			raise osv.except_osv(_('Warning!'),
						_('Cancellation Remarks is must !!'))
		
		temp_schedule_qty = 0
		for schedule_item in entry.line_ids:
		
			### Updation for production ####
			schedule_qty = schedule_item.order_bomline_id.schedule_qty + schedule_item.qty
			cr.execute(''' delete from kg_production where schedule_line_id = %s and state = 'draft' ''',[schedule_item.id])
			cr.execute(''' select sum(qty) from ch_stock_allocation_detail where header_id = %s  and qty > 0  ''',[schedule_item.id])
			alloc_qty = cr.fetchone()

			if schedule_item.order_bomline_id.qty == schedule_qty:
				order_bomline_obj.write(cr, uid, schedule_item.order_bomline_id.id, {'schedule_qty':schedule_qty})		
					
			if schedule_qty < schedule_item.order_bomline_id.qty:
				order_bomline_obj.write(cr, uid, schedule_item.order_bomline_id.id, {'schedule_qty':schedule_qty})
				
			if schedule_item.order_bomline_id.schedule_qty == 0:
				order_bomline_obj.write(cr, uid, schedule_item.order_bomline_id.id, {'schedule_qty':schedule_qty})		
		
		#### schedule Qty Updation in Work Order Line Items
		cr.execute(''' select order_line_id,sum(qty) as schedule_qty from ch_schedule_details where header_id = %s group by order_line_id ''',[entry.id])
		schedule_items = cr.dictfetchall()
		if schedule_items:
			for item in schedule_items:
				cr.execute(''' update ch_work_order_details set temp_schedule_qty = (temp_schedule_qty + %s) where id = %s ''',[item['schedule_qty'],item['order_line_id']])
		
		self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid,'flag_cancel':0, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		
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
		return super(kg_schedule, self).write(cr, uid, ids, vals, context)
		
kg_schedule()


class ch_schedule_details(osv.osv):

	_name = "ch.schedule.details"
	_description = "Schedule Details"
	
	
	_columns = {
	
		'header_id':fields.many2one('kg.schedule', 'Schedule', ondelete='cascade',required=True),
		'line_ids': fields.one2many('ch.stock.allocation.detail', 'header_id', "Allocation Details"),
		'schedule_date': fields.related('header_id','entry_date', type='date', string='Date', store=True, readonly=True),
		'order_id': fields.many2one('kg.work.order','Work Order'),
		'order_no':fields.char('Work Order No.'),
		'order_line_id': fields.many2one('ch.work.order.details','Work Order Line Id'),
		'order_priority': fields.related('order_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		'order_category': fields.related('order_line_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Order Category', store=True, readonly=True),
		'bom_id': fields.many2one('kg.bom','BOM Id'),
		'bom_line_id': fields.many2one('ch.bom.line','BOM Line Id'),
		'order_bomline_id': fields.many2one('ch.order.bom.details','Order BOM Line Id'),
		'order_ref_no': fields.related('order_id','name', type='char', string='Order Reference', store=True, readonly=True),
		'pump_model_id': fields.related('order_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		#~ 'pattern_id': fields.related('order_bomline_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern Number',readonly=True),
		'pattern_name': fields.related('pattern_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		#~ 'moc_id': fields.related('order_bomline_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'moc_id': fields.many2one('kg.moc.master','MOC',readonly=True),
		#~ 'order_qty': fields.related('order_bomline_id','qty', type='integer', size=100, string='Order Qty', store=True, readonly=True),
		'order_qty': fields.integer('Order Qty',readonly=True),
		'stock_qty': fields.integer('Stock Qty', readonly=True),
		'temp_stock_qty': fields.integer('Stock Qty'),
		'temp_schedule_qty': fields.integer('Schedule Qty'),
		'qty': fields.integer('Qty', required=True),
		'line_status': fields.selection([('schedule','Schedule'),('schedule_alloc','Schedule and Allocation')],'Line Status'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'note': fields.text('Notes'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'remarks': fields.related('order_bomline_id','add_spec',type='text',string='WO Remarks',store=True,readonly=True),
		'active': fields.boolean('Active'),
		'acc_bomline_id': fields.many2one('ch.wo.accessories.foundry','Acc Foundry Item'),
		'spare_bomline_id': fields.many2one('ch.wo.spare.foundry','Spare Foundry Item'),
		'weight': fields.float('Each Weight(kgs)',readonly=True),
		'total_weight': fields.float('Total Weight(kgs)',readonly=True),
		
	
	}
	
	_defaults = {
	
		'state': 'draft',
		'active': True,
		
	}
	
	def onchange_schedule_qty(self, cr, uid, ids, order_qty,qty, context=None):
		entry = self.browse(cr,uid,ids[0])
		allocation_line_obj = self.pool.get('ch.stock.allocation.detail')
		if entry.line_ids:
			if qty > 0:
				if qty == entry.line_ids[0].stock_qty:
					alloc_qty = qty
				if qty > entry.line_ids[0].stock_qty:
					alloc_qty = entry.line_ids[0].stock_qty
				if qty < entry.line_ids[0].stock_qty:
					alloc_qty = qty
				allocation_line_obj.write(cr, uid, entry.line_ids[0].id, {'qty':alloc_qty})
				
		if qty != order_qty:
			raise osv.except_osv(_('Warning!'),
						_('Schedule Qty & Order Qty should be same !!'))
		cr.execute(''' update ch_stock_allocation_detail set schedule_qty = %s where header_id = %s ''',[qty,ids[0]])
		return True
		
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty == 0 or entry.qty < 0:
			return False
		return True
		
	def entry_cancel(self,cr,uid,ids,context=None):
		qc_obj = self.pool.get('kg.qc.verification')
		order_line_obj = self.pool.get('ch.work.order.details')
		order_bomline_obj = self.pool.get('ch.order.bom.details')
		entry = self.browse(cr,uid,ids[0])
		
		if entry.cancel_remark == False:
			raise osv.except_osv(_('Warning!'),
						_('Cancellation Remarks is must !!'))
									
		#### Schedule Qty Updation in Work Order Line Items
		temp_schedule_qty = entry.order_line_id.temp_schedule_qty + entry.qty
		order_line_obj.write(cr, uid, entry.order_line_id.id, {'temp_schedule_qty':temp_schedule_qty})				
		
		
		### Updation for production ####
		schedule_qty = entry.order_bomline_id.schedule_qty + entry.qty
		cr.execute(''' delete from kg_production where schedule_line_id = %s and state = 'draft' ''',[entry.id])
		cr.execute(''' select sum(qty) from ch_stock_allocation_detail where header_id = %s and qty > 0  ''',[entry.id])
		alloc_qty = cr.fetchone()
	
		if entry.order_bomline_id.qty == schedule_qty:
			order_bomline_obj.write(cr, uid, entry.order_bomline_id.id, {'schedule_qty':schedule_qty})
			
		if schedule_qty < entry.order_bomline_id.qty:
			order_bomline_obj.write(cr, uid, entry.order_bomline_id.id, {'schedule_qty':schedule_qty})
			
		if schedule_qty == 0:
			order_bomline_obj.write(cr, uid, entry.order_bomline_id.id, {'schedule_qty':schedule_qty})
		
		self.write(cr, uid, ids, {'state': 'cancel'})
		
		
		return True
		
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_schedule_details, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		#~ if not type(ids) is list:
			#~ entry = self.browse(cr,uid,ids)
		return super(ch_schedule_details, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []
		order_bomline_obj = self.pool.get('ch.order.bom.details')
		order_line_obj = self.pool.get('ch.work.order.details')
		for rec in self.browse(cr,uid,ids):	
			if rec.header_id.state != 'draft':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete Schedule Details after confirmation !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
		
	def _check_line_items(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft' and entry.header_id.state == 'confirmed':
			return False
		return True
		
	
	
	_constraints = [		
			  
		#(_check_values, 'System not allow to save with zero and less than zero qty .!!',['Quantity']),
		(_check_line_items, 'Schedule cannot be created after confirmation !! ', ['']),
		
	   ]
	
ch_schedule_details()


class ch_stock_allocation_detail(osv.osv):

	_name = "ch.stock.allocation.detail"
	_description = "Stock Allocation"
	
	
	_columns = {
	
		
		'header_id':fields.many2one('ch.schedule.details', 'Schedule Detail', required=1, ondelete='cascade'),
		'order_id': fields.many2one('kg.work.order','Order Id'),
		'order_line_id': fields.many2one('ch.work.order.details','Work Order Line Id'),
		'order_ref_no': fields.related('order_id','name', type='char', string='Order Reference', store=True, readonly=True),
		'order_priority': fields.related('header_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Order Category', store=True, readonly=True),
		'pump_model_id': fields.related('order_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('header_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'moc_id': fields.related('header_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		
		'schedule_qty': fields.integer('Schedule Qty', readonly=True),
		'stock_qty': fields.integer('Stock Qty', readonly=True),
		'qty': fields.integer('Qty'),
		'stage_id': fields.many2one('kg.stage.master','Stage', readonly=True),
		'stage_sequence': fields.related('stage_id','stage_seq_id', type='integer', string='Stage Sequence', store=True, readonly=True),
		'state': fields.related('header_id','state', type='char', string='Status', store=True, readonly=True),
		'remarks': fields.text('Remarks'),
		'active': fields.boolean('Active'),
		'flag_allocate': fields.boolean('Allocate'),
		'flag_manual': fields.boolean('Manual Allocation'),
		
	
	}

	
	_defaults = {
	
		'state': 'draft',
		'active': True,
		'flag_allocate': False,
		
	}
		
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty == 0:
			return False
		return True
		
	def onchange_allocation_qty(self, cr, uid, ids, schedule_qty, stock_qty, qty, flag_allocate, context=None):
		
		if flag_allocate == True and qty == 0:
			raise osv.except_osv(_('Warning !'), _('Allocation Qty is must !!'))
		if flag_allocate == False and qty > 0:
			raise osv.except_osv(_('Warning !'), _('Kindly check allocation process !!'))
		if stock_qty == 0:
			raise osv.except_osv(_('Warning !'), _('Allocation Qty cannot be done without Stock Qty !!'))
		entry = self.browse(cr,uid,ids[0])
		if qty > stock_qty:
			raise osv.except_osv(_('Warning !'), _('Allocation Qty should not be greater than Stock Qty !!'))
		
		cr.execute(''' select sum(qty) from ch_stock_allocation_detail where header_id = %s and id != %s ''',[entry.header_id.id, entry.id])
		alloc_qty = cr.fetchone()
		
		if alloc_qty[0] != None:
			tot_alloc = alloc_qty[0] + qty
			if tot_alloc > schedule_qty:
				raise osv.except_osv(_('Warning !'), _('Allocation Qty should not be greater than Schedule Qty !!'))
		else:
			if qty > schedule_qty:
				raise osv.except_osv(_('Warning !'), _('Allocation Qty should not be greater than Schedule Qty !!'))
		return True

		
	def create(self, cr, uid, vals, context=None):
		return super(ch_stock_allocation_detail, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_stock_allocation_detail, self).write(cr, uid, ids, vals, context)
		
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete an entry after confirmation !!'))
						
			if rec.stock_qty > 0 and rec.qty > 0:			
				raise osv.except_osv(_('Warning!'),
						_('Allocation cannot be deleted !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	
	
	_constraints = [		
			  
		#(_check_values, 'System not allow to save with zero qty .!!',['Quantity']),
		
	   ]
	
ch_stock_allocation_detail()



class kg_fabrication_process(osv.osv):

	_name = "kg.fabrication.process"
	_description = "Fabrication Process"	
	
	_columns = {	
		
	   
		'order_id': fields.many2one('kg.work.order','Order Id'),
		'order_line_id': fields.many2one('ch.work.order.details','Order No.'),
		'order_ref_no': fields.related('order_id','name', type='char', string='Order Reference', store=True, readonly=True),
		'order_priority': fields.related('order_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		'order_category': fields.related('order_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Order Category', store=True, readonly=True),
		'pump_model_id': fields.related('order_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'order_delivery_date': fields.related('order_line_id','delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'note': fields.related('order_line_id','note',type='text',string='WO Remarks',store=True,readonly=True),	
		
		
		'ms_id': fields.many2one('kg.machine.shop','Item Code',readonly=True),
		'name': fields.related('ms_id','name', type='char',size=128,string='Item Name', store=True,readonly=True), 		
		'moc_id': fields.many2one('kg.moc.master','MOC',readonly=True),		
		'ms_line_id': fields.many2one('ch.order.machineshop.details','MS Line Id'),		
		'acc_ms_line_id': fields.many2one('ch.wo.accessories.ms','ACC MS Line Id'),
				
		'schedule_qty': fields.integer('Schedule Qty'),
		'pending_qty': fields.integer('Pending Qty'),		
		'completed_qty': fields.integer('Completed Qty'),		
		'qty': fields.integer('Quantity'),
		
		'inward_accept_qty': fields.integer('Accepted Qty'),		
		'inward_comple_qty': fields.integer('Inward Completed Qty'),		
		'inward_rej_qty': fields.integer('Rejected Qty'),
		
		'rej_reason': fields.char('Reason of Rejection'),
		
		'shift_id':fields.many2one('kg.shift.master','Shift'),
		'operator': fields.many2one('hr.employee','Completed by'),	   
		
		'remarks': fields.text('Remarks'),
		'active': fields.boolean('Active'),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode',required=True,readonly=True),
		
		'state': fields.selection([('pending','Pending'),('partial','Partial'),('complete','Completed'),('accept','Accepted')],'State', readonly=True),
		
		### Entry Info ###
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),	 
		
	
	}

	
	_defaults = {   
		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.fabrication.process', context=c),
		'active': True,
		'state': 'pending',		
		'entry_mode': 'manual',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),	
				
	}
	
	def entry_update(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		print"rec.schedule_qty",rec.schedule_qty		
		print"rec.pending_qty",rec.pending_qty		
		print"rec.completed_qty",rec.completed_qty		
		print"rec.qty	",rec.qty			
		total_avil_qty = rec.schedule_qty - rec.completed_qty			
		if rec.qty <= 0.00:
			raise osv.except_osv(_('Warning !'), _('System not allow to zero andless than zero qty .!!'))
		if total_avil_qty < rec.qty:
			raise osv.except_osv(_('Warning !'), _('Excess Qty not update. Kindly check !!'))			
		total_rem_qty = rec.schedule_qty - (rec.completed_qty + rec.qty )
		if total_rem_qty == 0.00:			
			state = 'complete'
		if total_rem_qty > 0.00:
			state = 'partial'		
		self.write(cr, uid, ids, {'state': state,'pending_qty':rec.pending_qty + rec.qty,'completed_qty':rec.completed_qty + rec.qty})
		return True
		
	def entry_inward(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		ms_shop_id = self.pool.get('kg.machineshop').search(cr,uid,[('order_line_id','=',rec.order_line_id.id),('ms_id','=',rec.ms_id.id)])
		if ms_shop_id != []:
			ms_shop_rec = self.pool.get('kg.machineshop').browse(cr,uid,ms_shop_id[0])			
			total_qty = rec.inward_accept_qty + rec.inward_rej_qty 
			pending_qty = rec.pending_qty - (rec.inward_rej_qty	+ rec.inward_accept_qty)
			print"rec.schedule_qty",rec.schedule_qty		
			print"rec.pending_qty",rec.pending_qty		
			print"rec.completed_qty",rec.completed_qty		
			print"rec.inward_accept_qty	",rec.inward_accept_qty
			print"rec.inward_rej_qty	",rec.inward_rej_qty
							
			if rec.pending_qty < total_qty:
				raise osv.except_osv(_('Warning !'), _('Excess Qty not update. Kindly check !!'))				
			
			if rec.inward_accept_qty <= 0.00 and rec.inward_rej_qty <= 0.00:
				raise osv.except_osv(_('Warning !'), _('System not allow to zero and less than zero qty .!!'))
			if rec.inward_accept_qty < 0.00 or rec.inward_rej_qty < 0.00:
				raise osv.except_osv(_('Warning !'), _('System not allow to negative qty .!!'))		
			
			if rec.schedule_qty == (rec.inward_accept_qty + rec.inward_comple_qty):				
				self.pool.get('kg.machineshop').write(cr, uid, ms_shop_id[0], {'state':'accept'})
				state = 'accept'			
			else:
				state = 'partial'
			
		else:
			raise osv.except_osv(_('Warning !'), _('Records not available in Machineshop Process !!'))
		self.write(cr, uid, ids, {'state': state,'pending_qty':pending_qty,'inward_comple_qty':rec.inward_comple_qty + rec.inward_accept_qty,'completed_qty':rec.completed_qty - rec.inward_rej_qty})
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.id:				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_fabrication_process, self).write(cr, uid, ids, vals, context)
	
kg_fabrication_process()
