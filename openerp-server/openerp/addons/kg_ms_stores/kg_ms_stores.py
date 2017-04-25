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
   ('project','Project')
]



class kg_ms_stores(osv.osv):

	_name = "kg.ms.stores"
	_description = "MS Stores Process"
	_order = "entry_date desc"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('MS Store No', size=128,select=True,readonly=True),
		'entry_date': fields.date('MS Store Date',required=True),
		'note': fields.text('Notes'),
		'remarks': fields.text('Remarks'),
		'active': fields.boolean('Active'),
		
		'operation_id': fields.many2one('kg.ms.operations','MS Operation Id'),
		'ms_id': fields.many2one('kg.machineshop','MS Id', readonly=True),
		'production_id': fields.many2one('kg.production', 'Production No.', readonly=True),
		'ms_plan_id': fields.many2one('kg.ms.daily.planning','Planning Id', readonly=True),
		'ms_plan_line_id': fields.many2one('ch.ms.daily.planning.details','Planning Line Id',readonly=True),
		'position_id': fields.many2one('kg.position.number', 'Position No.', readonly=True),
		'order_id': fields.many2one('kg.work.order', 'Work Order', readonly=True),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line', readonly=True),
		'order_no': fields.related('order_line_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'oth_spec': fields.text('WO Remarks', readonly=True),
		'order_category': fields.selection(ORDER_CATEGORY,'Category',readonly=True),
		'order_priority': fields.selection(ORDER_PRIORITY,'Priority', readonly=True),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', readonly=True),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern Number',readonly=True),
		'pattern_code': fields.related('pattern_id','name', type='char', string='Pattern Code', store=True, readonly=True),
		'pattern_name': fields.related('pattern_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'item_code': fields.char('Item Code', readonly=True),
		'item_name': fields.char('Item Name', readonly=True),
		'moc_id': fields.many2one('kg.moc.master', 'MOC', readonly=True),
		'ms_type': fields.selection([('foundry_item','Foundry Item'),('ms_item','MS Item'),('bot_item','BOT Item')], 'Item Type', store=True, readonly=True),
		'qty': fields.integer('Qty'),
		'state': fields.selection([
			('in_store','In Store'),
			('sent_to_ass','Sent to Assembly'),
			],'Status', readonly=True),
			
		'foundry_assembly_id': fields.related('production_id','assembly_id', type='integer', string='Assembly Inward', store=True, readonly=True),
		'foundry_assembly_line_id': fields.related('production_id','assembly_line_id', type='integer', string='Assembly Inward Line', store=True, readonly=True),
		'ms_assembly_id': fields.related('ms_id','assembly_id', type='integer', string='Assembly Inward', store=True, readonly=True),
		'ms_assembly_line_id': fields.related('ms_id','assembly_line_id', type='integer', string='Assembly Inward Line', store=True, readonly=True),
		'accept_state': fields.selection([
			('pending','Pending'),
			('waiting','Waiting for Acceptance'),
			('received','Received'),
			],'Status', readonly=True),
			
		'bot_id':fields.many2one('kg.machine.shop', 'Item Code',domain = [('type','=','bot')]),
		'brand_id': fields.many2one('kg.brand.master','Brand'),	
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),		
		
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_schedule', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'in_store',
		
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
			  
		
		#~ (_future_entry_date_check, 'System not allow to save with future date. !!',['']),   
		
	   ]
	   
	def entry_accept(self,cr,uid,ids,context=None):
		entry_rec = self.browse(cr,uid,ids[0])
		if entry_rec.accept_state == 'waiting':
			self.write(cr,uid,ids,{'accept_state':'received'})
		return True

	def assembly_update(self,cr,uid,ids,entry_mode,order_line_id=False,pump_model_id=False,context=None):
		
		entry_rec = self.browse(cr, uid, ids[0])
		assembly_obj = self.pool.get('kg.assembly.inward')
		assembly_foundry_obj = self.pool.get('ch.assembly.bom.details')
		assembly_ms_obj = self.pool.get('ch.assembly.machineshop.details')
		assembly_bot_obj = self.pool.get('ch.assembly.bot.details')
		order_bot_obj = self.pool.get('ch.order.bot.details')
		
		if entry_mode != 'manual':
			entry_mode = 'auto'

		if entry_mode == 'auto':
			inward_list = []
			assembly_list = []
			completion_list = []
			#~ ms_completion_list = {}
			
			### Assembly Foundry Re process Checking ###
			cr.execute(''' select 

				ms_store.order_line_id,
				ms_store.order_id,
				ms_store.pump_model_id,
				order_line.moc_construction_id,
				ms_store.pattern_id,
				ms_item.order_bomline_id,
				ms_store.foundry_assembly_id,
				ms_store.foundry_assembly_line_id,
				sum(ms_store.qty) as ms_qty

				from kg_ms_stores  ms_store

				left join ch_work_order_details order_line on order_line.id = ms_store.order_line_id
				left join kg_machineshop ms_item on ms_item.id = ms_store.ms_id

				where ms_store.ms_type = 'foundry_item' and ms_store.state = 'in_store' and ms_store.accept_state = 'received'
				and ms_store.foundry_assembly_id > 0 and ms_store.foundry_assembly_line_id > 0

				group by 1,2,3,4,5,6,7,8 ''')
			reprocess_foundry_details = cr.dictfetchall()
			print "reprocess_foundry_details",reprocess_foundry_details
			for reprocess_item in reprocess_foundry_details:
		
				assembly_id = assembly_obj.search(cr, uid, [
				('order_id','=',reprocess_item['order_id']),
				('order_line_id','=',reprocess_item['order_line_id']),
				('pump_model_id','=',reprocess_item['pump_model_id']),
				('moc_construction_id','=',reprocess_item['moc_construction_id']),
				('id','=',reprocess_item['foundry_assembly_id'])
				])
				print "sdzfffffffffffffffffffffffffffccccfff",assembly_id
				if assembly_id:
					assembly_foundry_id = assembly_foundry_obj.search(cr, uid, [
						('order_bom_id','=',reprocess_item['order_bomline_id']),
						('state','=','re_process'),
						('header_id','=',reprocess_item['foundry_assembly_id']),
						('id','=',reprocess_item['foundry_assembly_line_id'])
						])
					if assembly_foundry_id:
						assembly_foundry_rec = assembly_foundry_obj.browse(cr, uid,assembly_foundry_id[0])
						assembly_foundry_obj.write(cr,uid,reprocess_item['foundry_assembly_line_id'],{'state':'waiting'})
						cr.execute(""" update kg_assembly_inward set state = 'waiting' where 
							id in (select header_id from ch_assembly_bom_details where state != 're_process' and header_id = %s) 
							""" %(reprocess_item['foundry_assembly_id']))
						cr.execute(""" update kg_part_qap set db_state = 'pending', db_result = '', hs_state = 'pending',
								hs_result = '' where assembly_id = %s and assembly_foundry_id = %s and order_bom_id = %s
							""" %(reprocess_item['foundry_assembly_id'],reprocess_item['foundry_assembly_line_id'],reprocess_item['order_bomline_id']))
						#~ assembly_obj.entry_approve(cr, uid,[reprocess_item['foundry_assembly_id']])
			
			### Assembly MS Re process Checking ###
			cr.execute(''' select 

					ms_store.order_line_id,
					ms_store.order_id,
					ms_store.pump_model_id,
					order_line.moc_construction_id,
					ms_store.item_name,
					ms_store.item_code,
					ms_item.order_ms_line_id,
					ms_store.ms_assembly_id,
					ms_store.ms_assembly_line_id,
					sum(ms_store.qty) as ms_qty

					from kg_ms_stores  ms_store

					left join ch_work_order_details order_line on order_line.id = ms_store.order_line_id
					left join kg_machineshop ms_item on ms_item.id = ms_store.ms_id

					where ms_store.ms_type = 'ms_item' and ms_store.state = 'in_store' and ms_store.accept_state = 'received'
					and ms_store.ms_assembly_id > 0 and ms_store.ms_assembly_line_id > 0

					group by 1,2,3,4,5,6,7,8,9 ''')
			reprocess_ms_details = cr.dictfetchall()
			print "reprocess_ms_details",reprocess_ms_details
			
			for reprocess_item in reprocess_ms_details:
		
				assembly_id = assembly_obj.search(cr, uid, [
				('order_id','=',reprocess_item['order_id']),
				('order_line_id','=',reprocess_item['order_line_id']),
				('pump_model_id','=',reprocess_item['pump_model_id']),
				('moc_construction_id','=',reprocess_item['moc_construction_id']),
				('id','=',reprocess_item['ms_assembly_id'])
				])
				
				if assembly_id:
					assembly_ms_id = assembly_ms_obj.search(cr, uid, [
						('order_ms_id','=',reprocess_item['order_ms_line_id']),
						('state','=','re_process'),
						('header_id','=',reprocess_item['ms_assembly_id']),
						('id','=',reprocess_item['ms_assembly_line_id'])
						])
					print "assembly_ms_idassembly_ms_id",assembly_ms_id
					
					if assembly_ms_id:
						assembly_ms_rec = assembly_ms_obj.browse(cr, uid,assembly_ms_id[0])
						print "reprocess_item['ms_qty']",reprocess_item['ms_qty']
						print "ssembly_ms_rec.order_ms_qty",assembly_ms_rec.order_ms_qty
						print "reprocess_item['ms_assembly_id']",reprocess_item['ms_assembly_id']
						print "ccccccccccccccccccccccccccccccccccccc"
						assembly_ms_obj.write(cr,uid,reprocess_item['ms_assembly_line_id'],{'state':'waiting'})
						cr.execute(""" update kg_assembly_inward set state = 'waiting' where 
							id in (select header_id from ch_assembly_machineshop_details where state != 're_process' and header_id = %s) 
							""" %(reprocess_item['ms_assembly_id']))
						#~ assembly_obj.entry_approve(cr, uid,[reprocess_item['ms_assembly_id']])
			
			### Select Foundry Items group by Work Order ###
			cr.execute(''' select 

				ms_store.order_line_id,
				ms_store.order_id,
				ms_store.pump_model_id,
				order_line.moc_construction_id,
				ms_store.pattern_id,
				ms_item.order_bomline_id,
				sum(ms_store.qty) as ms_qty

				from kg_ms_stores  ms_store

				left join ch_work_order_details order_line on order_line.id = ms_store.order_line_id
				left join kg_machineshop ms_item on ms_item.id = ms_store.ms_id

				where ms_store.ms_type = 'foundry_item' and ms_store.state = 'in_store' and ms_store.accept_state = 'received'
				and foundry_assembly_id = 0 and foundry_assembly_line_id = 0

				group by 1,2,3,4,5,6 ''')
			foundry_details = cr.dictfetchall()
			print "foundry_details----------------",foundry_details
			for foundry_item in foundry_details:
				
				### Check all the foundry items fully completed ###
				cr.execute(''' select count(order_line_id),order_line_id,order_id,pump_model_id,moc_construction_id
						from
						(select 

						ms_store.order_line_id,
						ms_store.order_id,
						ms_store.pump_model_id,
						order_line.moc_construction_id,
						ms_store.pattern_id,
						ms_item.order_bomline_id,
						sum(ms_store.qty) as ms_qty

						from kg_ms_stores  ms_store

						left join ch_work_order_details order_line on order_line.id = ms_store.order_line_id
						left join kg_machineshop ms_item on ms_item.id = ms_store.ms_id

						where ms_store.ms_type = 'foundry_item' and ms_store.state = 'in_store' and ms_store.accept_state = 'received'
						and foundry_assembly_id = 0 and foundry_assembly_line_id = 0

						group by 1,2,3,4,5,6

						) as foundry
						where order_line_id = %s and pump_model_id = %s and moc_construction_id = %s
						group by 2,3,4,5 ''',[foundry_item['order_line_id'],foundry_item['pump_model_id'],foundry_item['moc_construction_id']])
				foundry_details_count = cr.fetchall()
				store_foundry_items = foundry_details_count[0][0]
				### Count the foundry items in Work Order ###
				cr.execute(''' select count(id)
						from ch_order_bom_details where header_id = %s and flag_applicable = 't' ''',[foundry_item['order_line_id']])
				wo_foundryitems_count = cr.fetchall()
				wo_foundry_items = wo_foundryitems_count[0][0]
				print "store_foundry_items----------------",store_foundry_items
				print "wo_foundry_items----------------",wo_foundry_items
				if store_foundry_items == wo_foundry_items:
					cr.execute(''' select id as order_bom_id,qty as bom_qty from ch_order_bom_details  where header_id = %s and id = %s ''',
					[foundry_item['order_line_id'],foundry_item['order_bomline_id']])
					foundry_item_qty = cr.dictfetchone()
					print "foundry_item['ms_qty']----------------",foundry_item['ms_qty']
					print "foundry_item['bom_qty']----------------",foundry_item_qty['bom_qty']
					if foundry_item['ms_qty'] == foundry_item_qty['bom_qty']:
						
						assembly_list.append({
						'order_line_id':foundry_item['order_line_id'],
						'order_id':foundry_item['order_id'],
						'pump_model_id': foundry_item['pump_model_id'],
						'moc_construction_id': foundry_item['moc_construction_id'],
						'pattern_id': foundry_item['pattern_id'],
						'order_bom_id': foundry_item_qty['order_bom_id'],
						'order_ms_id': '',
						'type': 'foundry'
						})
			
			### Select MS Items group by Work Order ###
			cr.execute(''' select 

					ms_store.order_line_id,
					ms_store.order_id,
					ms_store.pump_model_id,
					order_line.moc_construction_id,
					ms_store.item_name,
					ms_store.item_code,
					ms_item.order_ms_line_id,
					sum(ms_store.qty) as ms_qty

					from kg_ms_stores  ms_store

					left join ch_work_order_details order_line on order_line.id = ms_store.order_line_id
					left join kg_machineshop ms_item on ms_item.id = ms_store.ms_id

					where ms_store.ms_type = 'ms_item' and ms_store.state = 'in_store' and ms_store.accept_state = 'received'
					and ms_store.ms_assembly_id = 0 and ms_store.ms_assembly_line_id = 0

					group by 1,2,3,4,5,6,7
					''')
			ms_details = cr.dictfetchall()
			for ms_item in ms_details:
				### Check all the foundry items fully completed ###
				cr.execute(''' select count(order_line_id),order_line_id,order_id,pump_model_id,moc_construction_id
						from
						(select 

							ms_store.order_line_id,
							ms_store.order_id,
							ms_store.pump_model_id,
							order_line.moc_construction_id,
							ms_store.item_name,
							ms_store.item_code,
							ms_item.order_ms_line_id,
							sum(ms_store.qty) as ms_qty

							from kg_ms_stores  ms_store

							left join ch_work_order_details order_line on order_line.id = ms_store.order_line_id
							left join kg_machineshop ms_item on ms_item.id = ms_store.ms_id

							where ms_store.ms_type = 'ms_item' and ms_store.state = 'in_store' and ms_store.accept_state = 'received'
							and ms_store.ms_assembly_id = 0 and ms_store.ms_assembly_line_id = 0

							group by 1,2,3,4,5,6,7

						) as ms
						where order_line_id = %s and pump_model_id = %s and moc_construction_id = %s
						group by 2,3,4,5 ''',[ms_item['order_line_id'],ms_item['pump_model_id'],ms_item['moc_construction_id']])
				ms_details_count = cr.fetchall()
				store_ms_items = ms_details_count[0][0]
				### Count the foundry items in Work Order ###
				cr.execute(''' select count(id)
						from ch_order_machineshop_details where header_id = %s and flag_applicable='t' ''',[ms_item['order_line_id']])
				wo_msitems_count = cr.fetchall()
				wo_ms_items = wo_msitems_count[0][0]
				if store_ms_items == wo_ms_items:
					
					cr.execute(''' select id as order_ms_id,qty as bom_qty from ch_order_machineshop_details  where header_id = %s and id = %s ''',
					[ms_item['order_line_id'],ms_item['order_ms_line_id']])
					ms_item_qty = cr.dictfetchone()
					
					if ms_item_qty != None:
						if ms_item['ms_qty'] == ms_item_qty['bom_qty']:
							
							assembly_list.append({
							'order_line_id':ms_item['order_line_id'],
							'order_id':ms_item['order_id'],
							'pump_model_id': ms_item['pump_model_id'],
							'moc_construction_id': ms_item['moc_construction_id'],
							'order_ms_id': ms_item_qty['order_ms_id'],
							'pattern_id': '',
							'order_bom_id': '',
							'type': 'ms'
							})
			
			print "assembly_list-----------------------",assembly_list
			if assembly_list:
				groupby_orderid = {v['order_line_id']:v for v in assembly_list}.values()
				
				
				final_assembly_header_list = groupby_orderid
				for ass_header_item in final_assembly_header_list:
					
					completion_list = [element for element in assembly_list if element['order_line_id'] == ass_header_item['order_line_id']]
					print "completion_list",completion_list
					print "leeeeeeeeeeeeeeeeeeeeeeeeeeee",len(completion_list)
					
					cr.execute(""" select sum(count) from (
						select count(id) from ch_order_bom_details  where header_id = %s and flag_applicable = 't'
						union all
						select count(id) from ch_order_machineshop_details where header_id = %s and flag_applicable = 't') as order_count """ %(ass_header_item['order_line_id'],ass_header_item['order_line_id']))
					order_items_count = cr.fetchone()
					print "order_items_count",order_items_count
					
					if len(completion_list) == order_items_count[0]:
						assembly_id = assembly_obj.search(cr, uid, [
						('order_id','=',ass_header_item['order_id']),
						('order_line_id','=',ass_header_item['order_line_id']),
						('pump_model_id','=',ass_header_item['pump_model_id']),
						('moc_construction_id','=',ass_header_item['moc_construction_id']),
						('state','=','waiting'),
						])
						wo_line_rec = self.pool.get('ch.work.order.details').browse(cr, uid, ass_header_item['order_line_id'])
						wo_order_qty = wo_line_rec.qty
						if not assembly_id:
							assembly_create = 'no'
							### Checking bot items are completed are not ### 
							cr.execute(''' select count(id) from ch_order_bot_details where header_id = %s and flag_applicable = 't' ''',[ass_header_item['order_line_id']])
							order_bot_items_count = cr.fetchone()
							cr.execute(''' select count(id) from kg_ms_stores where order_line_id = %s and accept_state = 'received' and state = 'in_store' and ms_type = 'bot_item' ''',[ass_header_item['order_line_id']])
							store_bot_items_count = cr.fetchone()
							print "order_bot_items_count[0]",order_bot_items_count
							print "store_bot_items_count[0]",store_bot_items_count
							if order_bot_items_count != []:
								if order_bot_items_count[0] == store_bot_items_count[0]:
									assembly_create = 'yes'
								else:
									assembly_create = 'no'
							print "assembly_createassembly_create----------------------------------",assembly_create
							for assembly in range(wo_order_qty):
								ass_header_values = {
								'name': '',
								'order_id': ass_header_item['order_id'],
								'order_line_id': ass_header_item['order_line_id'],
								'pump_model_id': ass_header_item['pump_model_id'],
								'moc_construction_id': ass_header_item['moc_construction_id'],
								'state': 'waiting',
								'entry_mode': 'auto',
								'qap_plan_id': wo_line_rec.qap_plan_id.id
								}
								if assembly_create == 'yes':
									assembly_id = assembly_obj.create(cr, uid, ass_header_values)
									inward_list.append({'order_line_id':ass_header_item['order_line_id']})
									### Creating BOT Details ###
									cr.execute(''' select id as order_bot_id,qty as order_bot_qty from ch_order_bot_details where header_id = %s and flag_applicable = 't' ''',[ass_header_item['order_line_id']])
									order_bot_items = cr.dictfetchall()
									if order_bot_items:
										for bot_item in order_bot_items:
											if bot_item['order_bot_qty'] == 1:
												order_bot_qty = bot_item['order_bot_qty']
											if bot_item['order_bot_qty'] > 1:
												order_bot_qty = bot_item['order_bot_qty'] / wo_order_qty
											else:
												pass
											ass_bot_vals = {
											'header_id': assembly_id,
											'order_bot_id': bot_item['order_bot_id'],
											'order_bot_qty': order_bot_qty,
											}
											assembly_bot_id = assembly_bot_obj.create(cr, uid, ass_bot_vals)	
								
							### State Updation in store ###
							store_ids = self.search(cr,uid,[('order_line_id','=',ass_header_item['order_line_id']),('state','=','in_store')])
							for store_item in store_ids:
								self.write(cr, uid,store_item,{'state':'sent_to_ass'})	
							
				for assembly_item in assembly_list:
					assembly_ids = assembly_obj.search(cr, uid, [
					('order_id','=',assembly_item['order_id']),
					('order_line_id','=',assembly_item['order_line_id']),
					('pump_model_id','=',assembly_item['pump_model_id']),
					('moc_construction_id','=',assembly_item['moc_construction_id']),
					('state','=','waiting'),
					])
					
					### Creating Foundry Items ###
					for ass_foundry_id in assembly_ids:
						if assembly_item['type'] == 'foundry':
							order_bom_rec = self.pool.get('ch.order.bom.details').browse(cr, uid, assembly_item['order_bom_id'])
							if order_bom_rec.qty == 1:
								order_bom_qty = order_bom_rec.qty
							if order_bom_rec.qty > 1:
								order_bom_qty = order_bom_rec.qty / wo_order_qty
							ass_foundry_vals = {
								'header_id': ass_foundry_id,
								'order_bom_id': assembly_item['order_bom_id'],
								'order_bom_qty': order_bom_qty,
								'entry_mode': 'auto'
							}
							assembly_foundry_id = assembly_foundry_obj.create(cr, uid, ass_foundry_vals)
							
							### Dynamic Balancing and Pre Hydro Static Test Creation for Pattern ###
							print "assembly_item['order_line_id']",assembly_item['order_line_id']
							order_line_rec = self.pool.get('ch.work.order.details').browse(cr, uid, assembly_item['order_line_id'])
							print "order_line_rec.order_no",order_line_rec.order_no
							print "order_line_rec.qap_plan_id",order_line_rec.qap_plan_id
							print "order_bom_rec.pattern_id",order_bom_rec.pattern_id
							qap_dynamic_bal_id = self.pool.get('ch.dynamic.balancing').search(cr,uid,[('header_id','=',order_line_rec.qap_plan_id.id),
								('pattern_id','=',order_bom_rec.pattern_id.id)])
							if qap_dynamic_bal_id:
								qap_dynamic_bal_rec = self.pool.get('ch.dynamic.balancing').browse(cr,uid,qap_dynamic_bal_id[0])
								print "qap_dynamic_bal_rec",qap_dynamic_bal_rec
								min_weight = qap_dynamic_bal_rec.min_weight
								max_weight = qap_dynamic_bal_rec.max_weight
							else:
								min_weight = 0.00
								max_weight = 0.00
								
							### Hrdro static pressure from marketing Enquiry ###
							if order_line_rec.pump_offer_line_id > 0:
								market_enquiry_rec = self.pool.get('ch.kg.crm.pumpmodel').browse(cr,uid,order_line_rec.pump_offer_line_id)
								if market_enquiry_rec:
									hs_pressure = market_enquiry_rec.hydrostatic_test_pressure
								else:
									hs_pressure = 0.00
							else:
								hs_pressure = 0.00
							
							db_flag = False
							hs_flag = False
							if order_bom_rec.pattern_id.need_dynamic_balancing == True:
								db_flag = True
							if order_bom_rec.pattern_id.need_hydro_test == True:
								hs_flag = True
								
							print "db_flag",db_flag
							print "hs_flag",hs_flag
								
							if db_flag == True or hs_flag == True:
								
								part_qap_vals = {
									
									'qap_plan_id': order_line_rec.qap_plan_id.id,
									'order_id': assembly_item['order_id'],
									'order_line_id': assembly_item['order_line_id'],
									'order_no': order_line_rec.order_no,
									'order_category': order_line_rec.order_category,
									'pattern_id': order_bom_rec.pattern_id.id,
									'pattern_name': order_bom_rec.pattern_id.pattern_name,
									'item_code': order_bom_rec.pattern_id.name,
									'item_name': order_bom_rec.pattern_id.pattern_name,
									'moc_id': order_bom_rec.moc_id.id,
									'db_min_weight': min_weight,
									'db_max_weight': max_weight,
									'assembly_id': ass_foundry_id,
									'assembly_foundry_id': assembly_foundry_id,
									'order_bom_id': assembly_item['order_bom_id'],
									'hs_pressure': hs_pressure,
									'db_flag':db_flag,
									'hs_flag':hs_flag,
									
									
								}
								print "part_qap_vals",part_qap_vals
								
								for pattern in range(order_bom_qty):
								
									part_qap_id = self.pool.get('kg.part.qap').create(cr, uid, part_qap_vals)
							
		
					### Creating Machine Shop Items ###
					if assembly_item['type'] == 'ms':
						assembly_ids = assembly_obj.search(cr, uid, [
						('order_id','=',assembly_item['order_id']),
						('order_line_id','=',assembly_item['order_line_id']),
						('pump_model_id','=',assembly_item['pump_model_id']),
						('moc_construction_id','=',assembly_item['moc_construction_id']),
						('state','=','waiting'),
						])
						for ass_ms_id in assembly_ids:
							order_ms_rec = self.pool.get('ch.order.machineshop.details').browse(cr, uid, assembly_item['order_ms_id'])
							if order_ms_rec.qty == 1:
								order_ms_qty = order_ms_rec.qty
							if order_ms_rec.qty > 1:
								order_ms_qty = order_ms_rec.qty / wo_order_qty
							ass_ms_vals = {
								'header_id': ass_ms_id,
								'order_ms_id': assembly_item['order_ms_id'],
								'order_ms_qty': order_ms_qty,
								'entry_mode': 'auto'
							}
							assembly_ms_id = assembly_ms_obj.create(cr, uid, ass_ms_vals)			
		if entry_mode == 'manual':
			assembly_list = []
			### Assembly Foundry Re process Checking ###
			cr.execute(''' select 

				ms_store.order_line_id,
				ms_store.order_id,
				ms_store.pump_model_id,
				order_line.moc_construction_id,
				ms_store.pattern_id,
				ms_item.order_bomline_id,
				ms_store.foundry_assembly_id,
				ms_store.foundry_assembly_line_id,
				sum(ms_store.qty) as ms_qty

				from kg_ms_stores  ms_store

				left join ch_work_order_details order_line on order_line.id = ms_store.order_line_id
				left join kg_machineshop ms_item on ms_item.id = ms_store.ms_id

				where ms_store.ms_type = 'foundry_item' and ms_store.state = 'in_store' and ms_store.accept_state = 'received' and 
				ms_store.order_line_id = %s and ms_store.pump_model_id = %s
				and ms_store.foundry_assembly_id > 0 and ms_store.foundry_assembly_line_id > 0

				group by 1,2,3,4,5,6,7,8 ''',[order_line_id,pump_model_id])
			reprocess_foundry_details = cr.dictfetchall()
			print "reprocess_foundry_details",reprocess_foundry_details
			for reprocess_item in reprocess_foundry_details:
		
				assembly_id = assembly_obj.search(cr, uid, [
				('order_id','=',reprocess_item['order_id']),
				('order_line_id','=',reprocess_item['order_line_id']),
				('pump_model_id','=',reprocess_item['pump_model_id']),
				('moc_construction_id','=',reprocess_item['moc_construction_id']),
				('id','=',reprocess_item['foundry_assembly_id'])
				])
				
				if assembly_id:
					assembly_foundry_id = assembly_foundry_obj.search(cr, uid, [
						('order_bom_id','=',reprocess_item['order_bomline_id']),
						('state','=','re_process'),
						('header_id','=',reprocess_item['foundry_assembly_id']),
						('id','=',reprocess_item['foundry_assembly_line_id'])
						])
						
					if assembly_foundry_id:
						assembly_foundry_rec = assembly_foundry_obj.browse(cr, uid,assembly_foundry_id[0])
						
						assembly_foundry_obj.write(cr,uid,reprocess_item['foundry_assembly_line_id'],{'state':'waiting'})
						cr.execute(""" update kg_assembly_inward set state = 'waiting' where 
							id in (select header_id from ch_assembly_bom_details where state != 're_process' and header_id = %s) 
							""" %(reprocess_item['foundry_assembly_id']))
						cr.execute(""" update kg_part_qap set db_state = 'pending', db_result = '', hs_state = 'pending',
								hs_result = '' where assembly_id = %s and assembly_foundry_id = %s and order_bom_id = %s
							""" %(reprocess_item['foundry_assembly_id'],reprocess_item['foundry_assembly_line_id'],reprocess_item['order_bomline_id']))
						#~ assembly_obj.entry_approve(cr, uid,[reprocess_item['foundry_assembly_id']])
			
			### Assembly MS Re process Checking ###
			cr.execute(''' select 

					ms_store.order_line_id,
					ms_store.order_id,
					ms_store.pump_model_id,
					order_line.moc_construction_id,
					ms_store.item_name,
					ms_store.item_code,
					ms_item.order_ms_line_id,
					ms_store.ms_assembly_id,
					ms_store.ms_assembly_line_id,
					sum(ms_store.qty) as ms_qty

					from kg_ms_stores  ms_store

					left join ch_work_order_details order_line on order_line.id = ms_store.order_line_id
					left join kg_machineshop ms_item on ms_item.id = ms_store.ms_id

					where ms_store.ms_type = 'ms_item' and ms_store.state = 'in_store' and ms_store.accept_state = 'received' and 
					ms_store.order_line_id = %s and ms_store.pump_model_id = %s
					and ms_store.ms_assembly_id > 0 and ms_store.ms_assembly_line_id > 0

					group by 1,2,3,4,5,6,7,8,9 ''',[order_line_id,pump_model_id])
			reprocess_ms_details = cr.dictfetchall()
			print "reprocess_ms_details",reprocess_ms_details
			for reprocess_item in reprocess_ms_details:
		
				assembly_id = assembly_obj.search(cr, uid, [
				('order_id','=',reprocess_item['order_id']),
				('order_line_id','=',reprocess_item['order_line_id']),
				('pump_model_id','=',reprocess_item['pump_model_id']),
				('moc_construction_id','=',reprocess_item['moc_construction_id']),
				('id','=',reprocess_item['ms_assembly_id'])
				])
				
				if assembly_id:
					assembly_ms_id = assembly_ms_obj.search(cr, uid, [
						('order_ms_id','=',reprocess_item['order_ms_line_id']),
						('state','=','re_process'),
						('header_id','=',reprocess_item['ms_assembly_id']),
						('id','=',reprocess_item['ms_assembly_line_id'])
						])
					if assembly_ms_id:
						assembly_ms_rec = assembly_ms_obj.browse(cr, uid,assembly_ms_id[0])
						assembly_ms_obj.write(cr,uid,reprocess_item['ms_assembly_line_id'],{'state':'waiting'})
						cr.execute(""" update kg_assembly_inward set state = 'waiting' where 
							id in (select header_id from ch_machineshop_bom_details where state != 're_process' and header_id = %s) 
							""" %(reprocess_item['ms_assembly_id']))
						#~ assembly_obj.entry_approve(cr, uid,[reprocess_item['ms_assembly_id']])
						
			
			
			### Select Foundry Items group by Work Order ###
			cr.execute(''' select 

				ms_store.order_line_id,
				ms_store.order_id,
				ms_store.pump_model_id,
				order_line.moc_construction_id,
				ms_store.pattern_id,
				ms_item.order_bomline_id,
				sum(ms_store.qty) as ms_qty

				from kg_ms_stores  ms_store

				left join ch_work_order_details order_line on order_line.id = ms_store.order_line_id
				left join kg_machineshop ms_item on ms_item.id = ms_store.ms_id

				where ms_store.ms_type = 'foundry_item' and ms_store.state = 'in_store' and ms_store.accept_state = 'received' and 
				ms_store.order_line_id = %s and ms_store.pump_model_id = %s
				and ms_store.foundry_assembly_id = 0 and ms_store.foundry_assembly_line_id = 0
				
				group by 1,2,3,4,5,6 ''',[order_line_id,pump_model_id])
			foundry_details = cr.dictfetchall()
			
			for foundry_item in foundry_details:
				### Check all the foundry items fully completed ###
				cr.execute(''' select count(order_line_id),order_line_id,order_id,pump_model_id,moc_construction_id
						from
						(select 

						ms_store.order_line_id,
						ms_store.order_id,
						ms_store.pump_model_id,
						order_line.moc_construction_id,
						ms_store.pattern_id,
						ms_item.order_bomline_id,
						sum(ms_store.qty) as ms_qty

						from kg_ms_stores  ms_store

						left join ch_work_order_details order_line on order_line.id = ms_store.order_line_id
						left join kg_machineshop ms_item on ms_item.id = ms_store.ms_id

						where ms_store.ms_type = 'foundry_item' and ms_store.state = 'in_store' and ms_store.accept_state = 'received' and
						ms_store.order_line_id = %s and ms_store.pump_model_id = %s
						and ms_store.foundry_assembly_id = 0 and ms_store.foundry_assembly_line_id = 0

						group by 1,2,3,4,5,6

						) as foundry
						where order_line_id = %s and pump_model_id = %s and moc_construction_id = %s
						group by 2,3,4,5 ''',[foundry_item['order_line_id'],foundry_item['pump_model_id'],foundry_item['order_line_id'],foundry_item['pump_model_id'],foundry_item['moc_construction_id']])
				foundry_details_count = cr.fetchall()
				store_foundry_items = foundry_details_count[0][0]
				### Count the foundry items in Work Order ###
				cr.execute(''' select count(id)
						from ch_order_bom_details where header_id = %s and flag_applicable = 't' ''',[foundry_item['order_line_id']])
				wo_foundryitems_count = cr.fetchall()
				wo_foundry_items = wo_foundryitems_count[0][0]
				if store_foundry_items == wo_foundry_items:
					cr.execute(''' select id as order_bom_id,qty as bom_qty from ch_order_bom_details  where header_id = %s and id = %s ''',
					[foundry_item['order_line_id'],foundry_item['order_bomline_id']])
					foundry_item_qty = cr.dictfetchone()
					if foundry_item['ms_qty'] == foundry_item_qty['bom_qty']:
						assembly_list.append({
						'order_line_id':foundry_item['order_line_id'],
						'order_id':foundry_item['order_id'],
						'pump_model_id': foundry_item['pump_model_id'],
						'moc_construction_id': foundry_item['moc_construction_id'],
						'pattern_id': foundry_item['pattern_id'],
						'order_bom_id': foundry_item_qty['order_bom_id'],
						'order_ms_id': '',
						'type': 'foundry'
						})
			
			### Select MS Items group by Work Order ###
			cr.execute(''' select 

					ms_store.order_line_id,
					ms_store.order_id,
					ms_store.pump_model_id,
					order_line.moc_construction_id,
					ms_store.item_name,
					ms_store.item_code,
					ms_item.order_ms_line_id,
					sum(ms_store.qty) as ms_qty

					from kg_ms_stores  ms_store

					left join ch_work_order_details order_line on order_line.id = ms_store.order_line_id
					left join kg_machineshop ms_item on ms_item.id = ms_store.ms_id

					where ms_store.ms_type = 'ms_item' and ms_store.state = 'in_store' and ms_store.accept_state = 'received' and
					ms_store.order_line_id = %s and ms_store.pump_model_id = %s
					and ms_store.ms_assembly_id = 0 and ms_store.ms_assembly_line_id = 0

					group by 1,2,3,4,5,6,7
					''',[order_line_id,pump_model_id])
			ms_details = cr.dictfetchall()
			for ms_item in ms_details:
				### Check all the foundry items fully completed ###
				cr.execute(''' select count(order_line_id),order_line_id,order_id,pump_model_id,moc_construction_id
						from
						(select 

							ms_store.order_line_id,
							ms_store.order_id,
							ms_store.pump_model_id,
							order_line.moc_construction_id,
							ms_store.item_name,
							ms_store.item_code,
							ms_item.order_ms_line_id,
							sum(ms_store.qty) as ms_qty

							from kg_ms_stores  ms_store

							left join ch_work_order_details order_line on order_line.id = ms_store.order_line_id
							left join kg_machineshop ms_item on ms_item.id = ms_store.ms_id

							where ms_store.ms_type = 'ms_item' and ms_store.state = 'in_store' and ms_store.accept_state = 'received' and
							ms_store.order_line_id = %s and ms_store.pump_model_id = %s
							and ms_store.ms_assembly_id = 0 and ms_store.ms_assembly_line_id = 0

							group by 1,2,3,4,5,6,7

						) as ms
						where order_line_id = %s and pump_model_id = %s and moc_construction_id = %s
						group by 2,3,4,5 ''',[ms_item['order_line_id'],ms_item['pump_model_id'],ms_item['order_line_id'],ms_item['pump_model_id'],ms_item['moc_construction_id']])
				ms_details_count = cr.fetchall()
				store_ms_items = ms_details_count[0][0]
				### Count the foundry items in Work Order ###
				cr.execute(''' select count(id)
						from ch_order_machineshop_details where header_id = %s and flag_applicable = 't' ''',[ms_item['order_line_id']])
				wo_msitems_count = cr.fetchall()
				wo_ms_items = wo_msitems_count[0][0]
				if store_ms_items == wo_ms_items:
					
					cr.execute(''' select id as order_ms_id,qty as bom_qty from ch_order_machineshop_details  where header_id = %s and id = %s ''',
					[ms_item['order_line_id'],ms_item['order_ms_line_id']])
					ms_item_qty = cr.dictfetchone()
					
					if ms_item['ms_qty'] == ms_item_qty['bom_qty']:
						
						assembly_list.append({
						'order_line_id':ms_item['order_line_id'],
						'order_id':ms_item['order_id'],
						'pump_model_id': ms_item['pump_model_id'],
						'moc_construction_id': ms_item['moc_construction_id'],
						'order_ms_id': ms_item_qty['order_ms_id'],
						'pattern_id': '',
						'order_bom_id': '',
						'type': 'ms'
						})
			print "assembly_list---------------------",assembly_list
			if assembly_list:
				groupby_orderid = {v['order_line_id']:v for v in assembly_list}.values()
				final_assembly_header_list = groupby_orderid
				for ass_header_item in final_assembly_header_list:
					completion_list = [element for element in assembly_list if element['order_line_id'] == ass_header_item['order_line_id']]
					print "completion_list",completion_list
					print "leeeeeeeeeeeeeeeeeeeeeeeeeeee",len(completion_list)
					
					cr.execute(""" select sum(count) from (
						select count(id) from ch_order_bom_details  where header_id = %s and flag_applicable = 't'
						union all
						select count(id) from ch_order_machineshop_details where header_id = %s and flag_applicable = 't' ) as order_count """ %(ass_header_item['order_line_id'],ass_header_item['order_line_id']))
					order_items_count = cr.fetchone()
					print "order_items_count",order_items_count
					
					if len(completion_list) == order_items_count[0]:
					
						assembly_id = assembly_obj.search(cr, uid, [
						('order_id','=',ass_header_item['order_id']),
						('order_line_id','=',ass_header_item['order_line_id']),
						('pump_model_id','=',ass_header_item['pump_model_id']),
						('moc_construction_id','=',ass_header_item['moc_construction_id']),
						('state','=','waiting'),
						])
						wo_line_rec = self.pool.get('ch.work.order.details').browse(cr, uid, ass_header_item['order_line_id'])
						wo_order_qty = wo_line_rec.qty
						if not assembly_id:
							
							for assembly in range(wo_order_qty):
								ass_header_values = {
								'name': '',
								'order_id': ass_header_item['order_id'],
								'order_line_id': ass_header_item['order_line_id'],
								'pump_model_id': ass_header_item['pump_model_id'],
								'moc_construction_id': ass_header_item['moc_construction_id'],
								'state': 'waiting',
								'entry_mode': 'manual'
								}
								assembly_id = assembly_obj.create(cr, uid, ass_header_values)
								### Creating BOT Details ###
								cr.execute(''' select id as order_bot_id,qty as order_bot_qty from ch_order_bot_details where header_id = %s and flag_applicable = 't' ''',[ass_header_item['order_line_id']])
								order_bot_items = cr.dictfetchall()
								if order_bot_items:
									for bot_item in order_bot_items:
										if bot_item['order_bot_qty'] == 1:
											order_bot_qty = bot_item['order_bot_qty']
										if bot_item['order_bot_qty'] > 1:
											order_bot_qty = bot_item['order_bot_qty'] / wo_order_qty
										ass_bot_vals = {
										'header_id': assembly_id,
										'order_bot_id': bot_item['order_bot_id'],
										'order_bot_qty': order_bot_qty,
										}
										assembly_bot_id = assembly_bot_obj.create(cr, uid, ass_bot_vals)	
								
						### State Updation in store ###
						store_ids = self.search(cr,uid,[('order_line_id','=',ass_header_item['order_line_id']),('state','=','in_store')])
						for store_item in store_ids:
							self.write(cr, uid,store_item,{'state':'sent_to_ass'})	
					
					else:
						raise osv.except_osv(_('Warning!'),
							_('In Sufficient Qty to create Assembly Inward !!'))
				
				for assembly_item in assembly_list:
					assembly_ids = assembly_obj.search(cr, uid, [
					('order_id','=',assembly_item['order_id']),
					('order_line_id','=',assembly_item['order_line_id']),
					('pump_model_id','=',assembly_item['pump_model_id']),
					('moc_construction_id','=',assembly_item['moc_construction_id']),
					('state','=','waiting'),
					])
					### Creating Foundry Items ###
					for ass_foundry_id in assembly_ids:
						if assembly_item['type'] == 'foundry':
							order_bom_rec = self.pool.get('ch.order.bom.details').browse(cr, uid, assembly_item['order_bom_id'])
							if order_bom_rec.qty == 1:
								order_bom_qty = order_bom_rec.qty
							if order_bom_rec.qty > 1:
								order_bom_qty = order_bom_rec.qty / wo_order_qty
							ass_foundry_vals = {
								'header_id': ass_foundry_id,
								'order_bom_id': assembly_item['order_bom_id'],
								'order_bom_qty': order_bom_qty,
								'entry_mode': 'manual'
							}
							assembly_foundry_id = assembly_foundry_obj.create(cr, uid, ass_foundry_vals)
					### Creating Machine Shop Items ###
					if assembly_item['type'] == 'ms':
						assembly_ids = assembly_obj.search(cr, uid, [
						('order_id','=',assembly_item['order_id']),
						('order_line_id','=',assembly_item['order_line_id']),
						('pump_model_id','=',assembly_item['pump_model_id']),
						('moc_construction_id','=',assembly_item['moc_construction_id']),
						('state','=','waiting'),
						])
						for ass_ms_id in assembly_ids:
							order_ms_rec = self.pool.get('ch.order.machineshop.details').browse(cr, uid, assembly_item['order_ms_id'])
							if order_ms_rec.qty == 1:
								order_ms_qty = order_ms_rec.qty
							if order_ms_rec.qty > 1:
								order_ms_qty = order_ms_rec.qty / wo_order_qty
							ass_ms_vals = {
								'header_id': ass_ms_id,
								'order_ms_id': assembly_item['order_ms_id'],
								'order_ms_qty': order_ms_qty,
								'entry_mode': 'manual'
							}
							assembly_ms_id = assembly_ms_obj.create(cr, uid, ass_ms_vals)
							
		
		#~ if inward_list:
			#~ groupby_orderid = {v['order_line_id']:v for v in inward_list}.values()
			#~ inward_list = groupby_orderid
			#~ order_items = []
			#~ for inward_item in inward_list:
				#~ order_rec = self.pool.get('ch.work.order.details').browse(cr, uid, inward_item['order_line_id'])
				#~ order_items.append(order_rec.order_no)
			#~ order_items =  map(str, order_items)
			#~ a = ( ", ".join( repr(e) for e in order_items ) )
			#~ 
			#~ raise osv.except_osv(_(''), _(' Wo.No %s moved to assembly successfully !!')%(a))
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
		return super(kg_ms_stores, self).write(cr, uid, ids, vals, context)
		
kg_ms_stores()
