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
		'ms_id': fields.related('operation_id','ms_id', type='many2one', relation='kg.machineshop', string='MS Id', store=True, readonly=True),
		'production_id': fields.related('operation_id','production_id', type='many2one', relation='kg.production', string='Production No.', store=True, readonly=True),
		'ms_plan_id': fields.related('operation_id','ms_plan_id', type='many2one', relation='kg.ms.daily.planning', string='Planning Id', store=True, readonly=True),
		'ms_plan_line_id': fields.related('operation_id','ms_plan_line_id', type='many2one', relation='ch.ms.daily.planning.details', string='Planning Line Id', store=True, readonly=True),
		'position_id': fields.related('operation_id','position_id', type='many2one', relation='kg.position.number', string='Position No.', store=True, readonly=True),
		'order_id': fields.related('operation_id','order_id', type='many2one', relation='kg.work.order', string='Work Order', store=True, readonly=True),
		'order_line_id': fields.related('operation_id','order_line_id', type='many2one', relation='ch.work.order.details', string='Order Line', store=True, readonly=True),
		'order_no': fields.related('operation_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		
		'order_category': fields.related('operation_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.related('operation_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		'pump_model_id': fields.related('operation_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('operation_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_code': fields.related('operation_id','pattern_code', type='char', string='Pattern Code', store=True, readonly=True),
		'pattern_name': fields.related('operation_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'item_code': fields.related('operation_id','item_code', type='char', string='Item Code', store=True, readonly=True),
		'item_name': fields.related('operation_id','item_name', type='char', string='Item Name', store=True, readonly=True),
		'moc_id': fields.related('operation_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'ms_type': fields.related('operation_id','ms_type', type='selection', selection=[('foundry_item','Foundry Item'),('ms_item','MS Item')], string='Item Type', store=True, readonly=True),
		'qty': fields.integer('Qty'),
		'state': fields.selection([
			('in_store','In Store'),
			('sent_to_ass','Sent to Assembly'),
			],'Status', readonly=True),
			
		'foundry_assembly_id': fields.related('production_id','assembly_id', type='integer', string='Assembly Inward', store=True, readonly=True),
		'foundry_assembly_line_id': fields.related('production_id','assembly_line_id', type='integer', string='Assembly Inward Line', store=True, readonly=True),
		'ms_assembly_id': fields.related('ms_id','assembly_id', type='integer', string='Assembly Inward', store=True, readonly=True),
		'ms_assembly_line_id': fields.related('ms_id','assembly_line_id', type='integer', string='Assembly Inward Line', store=True, readonly=True),
		
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

				where ms_store.ms_type = 'foundry_item' and ms_store.state = 'in_store'
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
				
				if assembly_id:
					assembly_foundry_id = assembly_foundry_obj.search(cr, uid, [
						('order_bom_id','=',reprocess_item['order_bomline_id']),
						('state','=','re_process'),
						('header_id','=',reprocess_item['foundry_assembly_id']),
						('id','=',reprocess_item['foundry_assembly_line_id'])
						])
					if assembly_foundry_id:
						assembly_foundry_rec = assembly_foundry_obj.browse(cr, uid,assembly_foundry_id[0])
						if reprocess_item['ms_qty'] == assembly_foundry_rec.order_bom_qty:
							assembly_foundry_obj.write(cr,uid,reprocess_item['foundry_assembly_line_id'],{'state':'waiting'})
							assembly_obj.entry_approve(cr, uid,[reprocess_item['foundry_assembly_id']])
			
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

					where ms_store.ms_type = 'ms_item' and ms_store.state = 'in_store'
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
						if reprocess_item['ms_qty'] == assembly_ms_rec.order_ms_qty:
							print "ccccccccccccccccccccccccccccccccccccc"
							assembly_ms_obj.write(cr,uid,reprocess_item['ms_assembly_line_id'],{'state':'waiting'})
							assembly_obj.entry_approve(cr, uid,[reprocess_item['ms_assembly_id']])
			
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

				where ms_store.ms_type = 'foundry_item' and ms_store.state = 'in_store'
				and foundry_assembly_id = 0 and foundry_assembly_line_id = 0

				group by 1,2,3,4,5,6 ''')
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

						where ms_store.ms_type = 'foundry_item' and ms_store.state = 'in_store'
						and foundry_assembly_id = 0 and foundry_assembly_line_id = 0

						group by 1,2,3,4,5,6

						) as foundry
						where order_line_id = %s and pump_model_id = %s and moc_construction_id = %s
						group by 2,3,4,5 ''',[foundry_item['order_line_id'],foundry_item['pump_model_id'],foundry_item['moc_construction_id']])
				foundry_details_count = cr.fetchall()
				store_foundry_items = foundry_details_count[0][0]
				### Count the foundry items in Work Order ###
				cr.execute(''' select count(id)
						from ch_order_bom_details where header_id = %s ''',[foundry_item['order_line_id']])
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

					where ms_store.ms_type = 'ms_item' and ms_store.state = 'in_store'
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

							where ms_store.ms_type = 'ms_item' and ms_store.state = 'in_store'
							and ms_store.ms_assembly_id = 0 and ms_store.ms_assembly_line_id = 0

							group by 1,2,3,4,5,6,7

						) as ms
						where order_line_id = %s and pump_model_id = %s and moc_construction_id = %s
						group by 2,3,4,5 ''',[ms_item['order_line_id'],ms_item['pump_model_id'],ms_item['moc_construction_id']])
				ms_details_count = cr.fetchall()
				store_ms_items = ms_details_count[0][0]
				### Count the foundry items in Work Order ###
				cr.execute(''' select count(id)
						from ch_order_machineshop_details where header_id = %s ''',[ms_item['order_line_id']])
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
			
			if assembly_list:
				groupby_orderid = {v['order_line_id']:v for v in assembly_list}.values()
				
				
				final_assembly_header_list = groupby_orderid
				for ass_header_item in final_assembly_header_list:
					
					completion_list = [element for element in assembly_list if element['order_line_id'] == ass_header_item['order_line_id']]
					print "completion_list",completion_list
					print "leeeeeeeeeeeeeeeeeeeeeeeeeeee",len(completion_list)
					
					cr.execute(""" select sum(count) from (
						select count(id) from ch_order_bom_details  where header_id = %s
						union all
						select count(id) from ch_order_machineshop_details where header_id = %s) as order_count """ %(ass_header_item['order_line_id'],ass_header_item['order_line_id']))
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
								'entry_mode': 'auto'
								}
								assembly_id = assembly_obj.create(cr, uid, ass_header_values)
								### Creating BOT Details ###
								cr.execute(''' select id as order_bot_id,qty as order_bot_qty from ch_order_bot_details where header_id = %s ''',[ass_header_item['order_line_id']])
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

				where ms_store.ms_type = 'foundry_item' and ms_store.state = 'in_store'and 
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
						if reprocess_item['ms_qty'] == assembly_foundry_rec.order_bom_qty:
							assembly_foundry_obj.write(cr,uid,reprocess_item['foundry_assembly_line_id'],{'state':'waiting'})
							assembly_obj.entry_approve(cr, uid,[reprocess_item['foundry_assembly_id']])
			
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

					where ms_store.ms_type = 'ms_item' and ms_store.state = 'in_store'and 
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
						if reprocess_item['ms_qty'] == assembly_ms_rec.order_ms_qty:
							assembly_ms_obj.write(cr,uid,reprocess_item['ms_assembly_line_id'],{'state':'waiting'})
							assembly_obj.entry_approve(cr, uid,[reprocess_item['ms_assembly_id']])
						
			
			
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

				where ms_store.ms_type = 'foundry_item' and ms_store.state = 'in_store' and 
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

						where ms_store.ms_type = 'foundry_item' and ms_store.state = 'in_store' and
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
						from ch_order_bom_details where header_id = %s ''',[foundry_item['order_line_id']])
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

					where ms_store.ms_type = 'ms_item' and ms_store.state = 'in_store' and
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

							where ms_store.ms_type = 'ms_item' and ms_store.state = 'in_store'and
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
						from ch_order_machineshop_details where header_id = %s ''',[ms_item['order_line_id']])
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
			
			if assembly_list:
				groupby_orderid = {v['order_line_id']:v for v in assembly_list}.values()
				final_assembly_header_list = groupby_orderid
				for ass_header_item in final_assembly_header_list:
					completion_list = [element for element in assembly_list if element['order_line_id'] == ass_header_item['order_line_id']]
					print "completion_list",completion_list
					print "leeeeeeeeeeeeeeeeeeeeeeeeeeee",len(completion_list)
					
					cr.execute(""" select sum(count) from (
						select count(id) from ch_order_bom_details  where header_id = %s
						union all
						select count(id) from ch_order_machineshop_details where header_id = %s) as order_count """ %(ass_header_item['order_line_id'],ass_header_item['order_line_id']))
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
								cr.execute(''' select id as order_bot_id,qty as order_bot_qty from ch_order_bot_details where header_id = %s ''',[ass_header_item['order_line_id']])
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
