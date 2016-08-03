from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

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
			domain="[('schedule_status','=','allow'),'&',('header_id.order_priority','=','normal'),'&',('header_id.order_category','in',('pump','pump_spare','project')),'&',('header_id.state','=','confirmed'),'&',('state','=','confirmed'),'&',('header_id.division_id','=',division_id),('header_id.location','=',location)]"),
		'flag_schedule': fields.boolean('Schedule'),
		'flag_cancel': fields.boolean('Cancellation Flag'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'delivery_date': fields.date('Delivery Date',required=True),
		'order_priority': fields.selection(ORDER_PRIORITY,'Priority'),
		'order_category': fields.selection(ORDER_CATEGORY,'Category'),
		
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

	}
	
	_sql_constraints = [
        ('name_uniq', 'unique(name)', 'Schedule No. must be unique !!'),
    ]
	
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
	   
	   
	def update_line_items(self,cr,uid,ids,context=False):
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
				for bom_item in order_item.line_ids:
					if bom_item.flag_applicable == True:
						schedule_item_vals = {
													
							'header_id': entry.id,
							'order_id': order_item.header_id.id,
							'order_line_id': order_item.id,										
							'bom_id': bom_item.bom_id.id,
							'bom_line_id': bom_item.bom_line_id.id,																	
							'order_bomline_id': bom_item.id,									
							'qty' : bom_item.qty,
							'stock_qty' : 0,
							'line_status': 'schedule',
							'order_priority': order_item.order_priority,
							'order_category': order_item.order_category,
							'order_no':	order_item.order_no,			
							}
						
						schedule_line_id = schedule_line_obj.create(cr, uid, schedule_item_vals)
						
						self.write(cr, uid, ids, {'flag_schedule':True})
						order_line_obj.write(cr, uid, order_item.id, {'schedule_status':'not_allow'})		
						tot_stock = 0
						
						cr.execute(''' select 

							((select case when sum (qty) > 0 then sum (qty) else 0 end  
							
							from  kg_foundry_stock 
							
							where 
							
							moc_id = %s and
							pattern_id = %s and
							type = 'IN' and
							qty > 0) 

							-

							(select case when sum (qty) > 0 then sum (qty) else 0 end 
										
							from  kg_foundry_stock

							where
							
							moc_id = %s and
							pattern_id = %s and
							type = 'OUT' and
							qty > 0)) as stock_qty

							from kg_foundry_stock

							limit 1
						
						''',[bom_item.moc_id.id, bom_item.pattern_id.id
							,bom_item.moc_id.id, bom_item.pattern_id.id])
						result_stock_qty = cr.fetchone()
						
						schedule_rec = schedule_line_obj.browse(cr, uid, schedule_line_id)
					
						if result_stock_qty == None:
							stock_qty = 0
							if schedule_rec.line_status == 'schedule':
								line_status = 'schedule'
							else:
								line_status = 'schedule_alloc'
						if result_stock_qty != None:
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

							if schedule_rec.order_priority == 'emergency' and order_item.header_id.order_category == 'project':
								flag_allocate = False
								flag_manual = True
								allocation_qty = 0
							elif bom_item.flag_pattern_check == True or bom_item.pattern_id.pattern_state != 'active':
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
							
							schedule_line_obj.write(cr, uid, schedule_line_id, {'stock_qty':tot_stock,'line_status':line_status})
							
							allocation_id = allocation_line_obj.create(cr, uid, allocation_item_vals)

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
							if schedule_item.qty < alloc_qty[0]:
								raise osv.except_osv(_('Warning !'), _('Allocation Qty should not be greater than Schedule Qty for Order %s !!')%(schedule_item.order_no))
						
				
					
				cr.execute(''' select sum(qty) from ch_stock_allocation_detail
				
				where
				header_id = %s and
				qty > 0
				
				''',[schedule_item.id])
				allocation_qty = cr.fetchone()
				
				if allocation_qty:
					if allocation_qty[0] != None:
						if schedule_item.qty > allocation_qty[0]:
							schedule_qty = schedule_item.qty - allocation_qty[0]
						else:
							schedule_qty = allocation_qty[0] - schedule_item.qty
						
						### QC Creation When Allocation ###
						
						### QC Sequence Number Generation  ###
						qc_name = ''	
						qc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.qc.verification')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,qc_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(qc_seq_id[0],rec.code,entry.entry_date))
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
								'qty' : allocation_qty[0],
								'stock_qty':schedule_item.stock_qty,				   
								'allocated_qty':allocation_qty[0],				 
								'state' : 'draft',
								'order_category':schedule_item.order_id.order_category,
								'order_priority':schedule_item.order_id.order_priority,
								'pattern_id' : schedule_item.pattern_id.id,
								'pattern_name' : schedule_item.pattern_id.pattern_name,	
								'moc_id' : schedule_item.moc_id.id,
									
							}
						
						qc_id = qc_verf_obj.create(cr, uid, qc_vals)
						
					else:
						schedule_qty = schedule_item.qty
				else:
					schedule_qty = schedule_item.qty
					
				schedule_line_obj.write(cr, uid,schedule_item.id,{'qty':schedule_qty})
				### Production Creation When No Allocation ####
					
				if schedule_item.order_id.order_category in ('pump','pump_spare','project'):
					if schedule_item.order_id.order_priority == 'normal':
						priority = '6'
					if schedule_item.order_id.order_priority == 'emergency':
						priority = '4'
				if schedule_item.order_id.order_category == 'service':
					priority = '3'
				if schedule_item.order_id.order_category == 'spare':
					priority = '5'
				
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
							'order_line_id': schedule_item.order_line_id.id,
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
							'core_remarks': schedule_item.order_bomline_id.add_spec,
							'mould_no': mould_name[0],
							'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
							'mould_qty': schedule_qty,
							'mould_rem_qty': schedule_qty,
							'mould_state': 'pending',
							'mould_remarks': schedule_item.order_bomline_id.add_spec,	
						}
						
						
					production_id = production_obj.create(cr, uid, production_vals)
					
					if ms_no == 1:
						### Machine shop Item Creation ####
						cr.execute("""
							select id as order_ms_line_id,qty as sch_qty,ms_id as ms_id,name as item_name,
								bom_id as ms_bom_id,ms_line_id as ms_bom_line_id ,position_id,
								moc_id
								from ch_order_machineshop_details
								where flag_applicable = 't' and header_id in 
								(select order_line_id from ch_schedule_details where header_id = %s
								) """%(entry.id))
						order_ms_details = cr.dictfetchall();
						
						if order_ms_details:
						
							for ms_item in order_ms_details:
								ms_obj = self.pool.get('kg.machineshop')
								ms_master_obj = self.pool.get('kg.machine.shop')
								ms_rec = ms_master_obj.browse(cr, uid, ms_item['ms_id'])
								
								### Sequence Number Generation ###
								ms_name = ''	
								ms_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.ms.inward')])
								seq_rec = self.pool.get('ir.sequence').browse(cr,uid,ms_seq_id[0])
								cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(ms_seq_id[0],seq_rec.code))
								ms_name = cr.fetchone();
								
								ms_vals = {
								
								'order_ms_line_id': ms_item['order_ms_line_id'],
								'name': ms_name[0],
								'location': entry.location,
								'schedule_id': entry.id,
								'schedule_date': entry.entry_date,
								'schedule_line_id': schedule_item.id,
								'order_id': schedule_item.order_id.id,
								'order_line_id': schedule_item.order_line_id.id,
								'order_no': schedule_item.order_line_id.order_no,
								'order_delivery_date': schedule_item.order_line_id.delivery_date,
								'order_date': schedule_item.order_line_id.header_id.entry_date,
								'order_category': schedule_item.order_id.order_category,
								'order_priority': priority,
								'pump_model_id':schedule_item.pump_model_id.id,
								'moc_id':ms_item['moc_id'],
								'schedule_qty':ms_item['sch_qty'],
								'ms_sch_qty':ms_item['sch_qty'],
								'ms_type': 'ms_item',
								'ms_state': 'in_plan',
								'state':'accept',
								'ms_id': ms_item['ms_id'],
								'ms_bom_id': ms_item['ms_bom_id'],
								'ms_bom_line_id': ms_item['ms_bom_line_id'],
								'position_id': ms_item['position_id'],
								'item_code': ms_rec.code,
								'item_name': ms_item['item_name' ],
								
								}
								
								
								ms_no = ms_no + 1
								ms_id = ms_obj.create(cr, uid, ms_vals)
			
			#### Department Indent Creation for MOC Raw materials  ###
			
			### Foundry Items ###
					
			cr.execute("""
				select product_id,sum(indent_qty) as indent_qty from 

					(

					select (raw.qty * order_bom.qty) as indent_qty,raw.product_id
					from ch_moc_raw_material as raw
					left join ch_order_bom_details order_bom on raw.header_id = order_bom.moc_id
					where order_bom.flag_applicable = 't' and order_bom.header_id in (select distinct order_line_id 
					from ch_schedule_details  where header_id = %s and qty > 0
					) 

					)

					as sub_query
					group by product_id"""%(entry.id))
			foundry_indent_moc_details = cr.dictfetchall();
			
			if foundry_indent_moc_details:
			
				### Creation of Department Indent Header ###
				
				dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP15')])
				
				seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry.entry_date))
				seq_name = cr.fetchone();

				dep_indent_obj = self.pool.get('kg.depindent')
				foundry_dep_indent_vals = {
					'name':'',
					'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
					'dep_name':dep_id[0],
					'entry_mode':'auto',
					'state': 'approved',
					'indent_type': 'production',
					'name': seq_name[0]
					}
					
				indent_id = dep_indent_obj.create(cr, uid, foundry_dep_indent_vals)
				for foundry_indent_item in foundry_indent_moc_details:
					dep_indent_line_obj = self.pool.get('kg.depindent.line')
					product_rec = self.pool.get('product.product').browse(cr, uid, foundry_indent_item['product_id'])
					
					foundry_dep_indent_line_vals = {
						'indent_id':indent_id,
						'product_id':foundry_indent_item['product_id'],
						'uom':product_rec.uom_id.id,
						'qty':foundry_indent_item['indent_qty'],
						'pending_qty':foundry_indent_item['indent_qty'],
					}
					
					indent_line_id = dep_indent_line_obj.create(cr, uid, foundry_dep_indent_line_vals)
					
					
					cr.execute("""
						select product_id,order_line_id,sum(indent_qty) as indent_qty from 

						(

						select (raw.qty * order_bom.qty) as indent_qty,raw.product_id,order_bom.header_id as order_line_id
						from ch_moc_raw_material as raw
						left join ch_order_bom_details order_bom on raw.header_id = order_bom.moc_id
						where order_bom.flag_applicable = 't' and order_bom.header_id in (select order_line_id from 
						ch_schedule_details where header_id = %s and qty > 0
						)

						)
						as sub_query
						where product_id = %s
						group by product_id,order_line_id
						"""%(entry.id,foundry_indent_item['product_id']))
					foundry_indent_wo_details = cr.dictfetchall();
					
					for foundry_indent_wo_item in foundry_indent_wo_details:
						
						indent_wo_line_obj = self.pool.get('ch.depindent.wo')
						order_line_rec = self.pool.get('ch.work.order.details').browse(cr, uid, foundry_indent_wo_item['order_line_id'])
						
						foundry_indent_wo_line_vals = {
							'header_id':indent_line_id,
							'wo_id':order_line_rec.order_no,
							'w_order_id':order_line_rec.header_id.id,
							'w_order_line_id':order_line_rec.id,
							'qty':foundry_indent_wo_item['indent_qty'],
						}
						indent_wo_line_id = indent_wo_line_obj.create(cr, uid, foundry_indent_wo_line_vals)
					
					
			#### Machine shop Items ###		
					
			cr.execute("""
				select product_id,sum(indent_qty) as indent_qty from 

					(


					select (raw.qty * order_ms.qty) as indent_qty,raw.product_id
					from ch_ms_raw_material as raw
					left join ch_order_machineshop_details order_ms on raw.header_id = order_ms.ms_id
					where order_ms.flag_applicable = 't' and order_ms.header_id in (select distinct order_line_id 
					from ch_schedule_details  where header_id = %s and qty > 0
					) 


					)

					as sub_query
					group by product_id"""%(entry.id))
			ms_indent_moc_details = cr.dictfetchall();
			
			if ms_indent_moc_details:
				### Creation of Department Indent Header ###
				
				dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP2')])
				
				seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry.entry_date))
				seq_name = cr.fetchone();
				
				dep_indent_obj = self.pool.get('kg.depindent')
				ms_dep_indent_vals = {
					'name':'',
					'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
					'dep_name':dep_id[0],
					'entry_mode':'auto',
					'state': 'approved',
					'indent_type': 'production',
					'name': seq_name[0]
					}
					
				indent_id = dep_indent_obj.create(cr, uid, ms_dep_indent_vals)
				for ms_indent_item in ms_indent_moc_details:
					dep_indent_line_obj = self.pool.get('kg.depindent.line')
					product_rec = self.pool.get('product.product').browse(cr, uid, ms_indent_item['product_id'])
					ms_dep_indent_line_vals = {
					'indent_id':indent_id,
					'product_id':ms_indent_item['product_id'],
					'uom':product_rec.uom_id.id,
					'qty':ms_indent_item['indent_qty'],
					'pending_qty':ms_indent_item['indent_qty'],
					}
					
					indent_line_id = dep_indent_line_obj.create(cr, uid, ms_dep_indent_line_vals)
					
					
					cr.execute("""
						select product_id,order_line_id,sum(indent_qty) as indent_qty from 

						(
						select (raw.qty * order_ms.qty) as indent_qty,raw.product_id,order_ms.header_id as order_line_id
						from ch_ms_raw_material as raw
						left join ch_order_machineshop_details order_ms on raw.header_id = order_ms.ms_id
						where order_ms.flag_applicable = 't' and order_ms.header_id in (select distinct order_line_id 
						from ch_schedule_details where header_id = %s and qty > 0
						)
						)
						as sub_query
						where product_id = %s
						group by product_id,order_line_id
						"""%(entry.id,ms_indent_item['product_id']))
					ms_indent_wo_details = cr.dictfetchall();
					
					for ms_indent_wo_item in ms_indent_wo_details:
						
						indent_wo_line_obj = self.pool.get('ch.depindent.wo')
						order_line_rec = self.pool.get('ch.work.order.details').browse(cr, uid, ms_indent_wo_item['order_line_id'])
						
						ms_indent_wo_line_vals = {
						'header_id':indent_line_id,
						'wo_id':order_line_rec.order_no,
						'w_order_id':order_line_rec.header_id.id,
						'w_order_line_id':order_line_rec.id,
						'qty':ms_indent_wo_item['indent_qty'],
						}
						
						indent_wo_line_id = indent_wo_line_obj.create(cr, uid, ms_indent_wo_line_vals)
					
					
			### BOT Items ###
					
			cr.execute("""
				select product_id,sum(indent_qty) as indent_qty from 

					(

					select (raw.qty * order_bot.qty) as indent_qty,raw.product_id
					from ch_ms_raw_material as raw
					left join ch_order_bot_details order_bot on raw.header_id = order_bot.bot_id
					where order_bot.flag_applicable = 't' and order_bot.header_id in (select distinct order_line_id 
					from ch_schedule_details  where header_id = %s and qty > 0
					)

					)

					as sub_query
					group by product_id"""%(entry.id))
			bot_indent_moc_details = cr.dictfetchall();
			
			if bot_indent_moc_details:
			
				### Creation of Department Indent Header ###
				dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP3')])
				
				seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry.entry_date))
				seq_name = cr.fetchone();
				
				dep_indent_obj = self.pool.get('kg.depindent')
				bot_dep_indent_vals = {
					'name':'',
					'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
					'dep_name':dep_id[0],
					'entry_mode':'auto',
					'state': 'approved',
					'indent_type': 'production',
					'name': seq_name[0]
					}
					
				indent_id = dep_indent_obj.create(cr, uid, bot_dep_indent_vals)
				for bot_indent_item in bot_indent_moc_details:
					dep_indent_line_obj = self.pool.get('kg.depindent.line')
					product_rec = self.pool.get('product.product').browse(cr, uid, bot_indent_item['product_id'])
					
					bot_dep_indent_line_vals = {
					'indent_id':indent_id,
					'product_id':bot_indent_item['product_id'],
					'uom':product_rec.uom_id.id,
					'qty':bot_indent_item['indent_qty'],
					'pending_qty':bot_indent_item['indent_qty'],
					}
					
					indent_line_id = dep_indent_line_obj.create(cr, uid, bot_dep_indent_line_vals)
					
					
					cr.execute("""
						select product_id,order_line_id,sum(indent_qty) as indent_qty from 

						(

						select (raw.qty * order_bot.qty) as indent_qty,raw.product_id,order_bot.header_id as order_line_id
						from ch_ms_raw_material as raw
						left join ch_order_bot_details order_bot on raw.header_id = order_bot.bot_id
						where order_bot.flag_applicable = 't' and order_bot.header_id in (select distinct order_line_id 
						from ch_schedule_details  where header_id = %s and qty > 0
						)  
						)
						as sub_query
						where product_id = %s
						group by product_id,order_line_id
						"""%(entry.id,bot_indent_item['product_id']))
					bot_indent_wo_details = cr.dictfetchall();
					
					for bot_indent_wo_item in bot_indent_wo_details:
						
						indent_wo_line_obj = self.pool.get('ch.depindent.wo')
						order_line_rec = self.pool.get('ch.work.order.details').browse(cr, uid, bot_indent_wo_item['order_line_id'])
						
						bot_indent_wo_line_vals = {
						'header_id':indent_line_id,
						'wo_id':order_line_rec.order_no,
						'w_order_id':order_line_rec.header_id.id,
						'w_order_line_id':order_line_rec.id,
						'qty':bot_indent_wo_item['indent_qty'],
						}
						
						indent_wo_line_id = indent_wo_line_obj.create(cr, uid, bot_indent_wo_line_vals)
				
			
		
		else:
			raise osv.except_osv(_('Warning !'), _('System not allow to confirm an entry without Schedule details!!'))
			
		
		### Sequence Number Generation  ###
		#~ sch_name = ''
		#~ if not entry.name:		
			#~ sch_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.schedule')])
			#~ rec = self.pool.get('ir.sequence').browse(cr,uid,sch_id[0])
			#~ cr.execute("""select generatesequenceno(%s,'%s','%s') """%(sch_id[0],rec.code,entry.entry_date))
			#~ sch_name = cr.fetchone();
		
		self.write(cr, uid, ids, {'state': 'confirmed','flag_cancel':1,'confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),
			#~ 'name' :sch_name[0]
			})
		cr.execute(''' update ch_schedule_details set state = 'confirmed' where header_id = %s ''',[ids[0]])
		
		
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
		'pattern_id': fields.related('order_bomline_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('pattern_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('order_bomline_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'order_qty': fields.related('order_bomline_id','qty', type='integer', size=100, string='Order Qty', store=True, readonly=True),
		
		'stock_qty': fields.integer('Stock Qty', readonly=True),
		'temp_stock_qty': fields.integer('Stock Qty'),
		'temp_schedule_qty': fields.integer('Schedule Qty'),
		'qty': fields.integer('Qty', required=True),
		'line_status': fields.selection([('schedule','Schedule'),('schedule_alloc','Schedule and Allocation')],'Line Status'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'note': fields.text('Notes'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'remarks': fields.text('Remarks'),
		'active': fields.boolean('Active'),
		
	
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
			if rec.state != 'draft':			
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











