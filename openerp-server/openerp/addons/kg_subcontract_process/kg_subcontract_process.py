from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

dt_time = lambda * a: time.strftime('%m/%d/%Y %H:%M:%S')

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


class kg_subcontract_process(osv.osv):

	_name = "kg.subcontract.process"
	_description = "Subcontract Process"
	_order = "order_priority,entry_date asc"
	
	def _get_default_division(self, cr, uid, context=None):
		res = self.pool.get('kg.division.master').search(cr, uid, [('code','=','SAM'),('state','=','approved'), ('active','=','t')], context=context)
		return res and res[0] or False
	
	_columns = {
	
		
		'name': fields.char('Subcontract No', size=128,select=True,readonly=True),
		'entry_date': fields.date('Subcontract Date',required=True),
		'division_id': fields.many2one('kg.division.master','Division'),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location'),
		'active': fields.boolean('Active'),
		
		'ms_plan_id': fields.many2one('kg.ms.daily.planning','Planning Id'),
		'ms_plan_line_id': fields.many2one('ch.ms.daily.planning.details','Planning Line Id'),
		'ms_id': fields.related('ms_plan_line_id','ms_id', type='many2one', relation='kg.machineshop', string='MS Id', store=True, readonly=True),
		'production_id': fields.related('ms_id','production_id', type='many2one', relation='kg.production', string='Production No.', store=True, readonly=True),
		'position_id': fields.related('ms_plan_line_id','position_id', type='many2one', relation='kg.position.number', string='Position No.', store=True, readonly=True),
		'order_id': fields.related('ms_plan_line_id','order_id', type='many2one', relation='kg.work.order', string='Work Order', store=True, readonly=True),
		'order_line_id': fields.related('ms_plan_line_id','order_line_id', type='many2one', relation='ch.work.order.details', string='Order Line', store=True, readonly=True),
		'order_no': fields.related('ms_plan_line_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('ms_plan_line_id','order_delivery_date', type='date', string='Delivery Date', store=True, readonly=True),

		'order_category': fields.related('ms_plan_line_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.related('ms_plan_line_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		'pump_model_id': fields.related('ms_plan_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('ms_plan_line_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_code': fields.related('ms_plan_line_id','pattern_code', type='char', string='Pattern Code', store=True, readonly=True),
		'pattern_name': fields.related('ms_plan_line_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'item_code': fields.related('ms_plan_line_id','item_code', type='char', string='Item Code', store=True, readonly=True),
		'item_name': fields.related('ms_plan_line_id','item_name', type='char', string='Item Name', store=True, readonly=True),
		'moc_id': fields.related('ms_plan_line_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'ms_type': fields.related('ms_plan_line_id','ms_type', type='selection', selection=[('foundry_item','Foundry Item'),('ms_item','MS Item')], string='Item Type', store=True, readonly=True),
		'sc_qty': fields.integer('SC Qty'),
		'ms_op_id': fields.many2one('kg.ms.operations','MS Operation Id'),
		
		'sc_wo_qty': fields.integer('SC WO Qty'),
		'wo_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')], 'WO Status'),
		'wo_process_state': fields.selection([('allow','Allow'),('not_allow','Not Allow')], 'WO Process Status'),

		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
				
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_subcontract_process', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'division_id':_get_default_division,
		'wo_state': 'pending',
		'wo_process_state': 'allow',
		
	}
	
	
	
kg_subcontract_process()


class kg_subcontract_wo(osv.osv):

	_name = "kg.subcontract.wo"
	_description = "Subcontract WO"
	_order = "entry_date desc"
	
	def _get_default_division(self, cr, uid, context=None):
		res = self.pool.get('kg.division.master').search(cr, uid, [('code','=','SAM'),('state','=','approved'), ('active','=','t')], context=context)
		return res and res[0] or False
		
	def _get_order_value(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		
		for entry in self.browse(cr, uid, ids, context=context):
			cr.execute(''' select sum(amount) from ch_subcontract_wo_line where header_id = %s ''',[entry.id])
			wo_value = cr.fetchone()
			if wo_value[0] == None:
				wo_value = 0.00
			else:
				wo_value=wo_value[0]
			wo_value = wo_value
			result[entry.id] = wo_value
		return result
		
		
	_columns = {

	
		'name': fields.char('WO No.', size=128,select=True,readonly=True),
		'entry_date': fields.date('WO Date',required=True),
		'division_id': fields.many2one('kg.division.master','Division'),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location'),
		'active': fields.boolean('Active'),
		'contractor_id': fields.many2one('res.partner','Subcontractor'),
		'contact_person': fields.char('Contact Person', size=128),
		'phone': fields.char('Phone',size=64),
		'delivery_date': fields.date('Expected Delivery Date'),
		'wo_value': fields.function(_get_order_value, string='WO Value', method=True, store=True, type='float'),
		'billing_type': fields.selection([('applicable','Applicable'),('not_applicable','Not Applicable')],'Billing Type'),
		'sc_line_ids': fields.many2many('kg.subcontract.process','m2m_sc_details' , 'order_id', 'sc_id', 'SC Items',
			domain="[('wo_state','in',('pending','partial')),('wo_process_state','=','allow')]"),
		'line_ids': fields.one2many('ch.subcontract.wo.line','header_id','Subcontract WO Line'),   
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'flag_order': fields.boolean('Flag Order'),
		
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
				
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_subcontract_wo', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'delivery_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'division_id':_get_default_division,
		'flag_order': False,
		'state': 'draft'
		
	}
	
	def onchange_contractor(self, cr, uid, ids, contractor_id):
		if contractor_id:
			contractor_rec = self.pool.get('res.partner').browse(cr, uid, contractor_id)
		return {'value': {'contact_person':contractor_rec.contact_person,'phone':contractor_rec.phone  }}
	
	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		wo_line_obj = self.pool.get('ch.subcontract.wo.line')
		sc_obj = self.pool.get('kg.subcontract.process')
		
		del_sql = """ delete from ch_subcontract_wo_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.sc_line_ids:
		
			for item in entry.sc_line_ids:
				
				sc_qty = item.sc_qty - item.sc_wo_qty
				
				vals = {
				
					'header_id': entry.id,
					'sc_id':item.id,
					'qty':sc_qty,
					'sc_qty':sc_qty,
					
				}
				
				wo_line_id = wo_line_obj.create(cr, uid,vals)
				
				sc_obj.write(cr, uid, item.id, {'wo_process_state': 'not_allow'})
				
			self.write(cr, uid, ids, {'flag_order': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		sc_obj = self.pool.get('kg.subcontract.process')
		
		for line_item in entry.line_ids:
			
			if line_item.qty < 0 and line_item.rate < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative values !!'))
							
			if line_item.qty == 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save Zero values !!'))
							
			if line_item.qty > line_item.sc_qty:
				raise osv.except_osv(_('Warning!'),
							_('Check the SC Qty !!! '))
			
			if (line_item.sc_id.sc_wo_qty + line_item.qty) == line_item.sc_id.sc_qty:
				wo_state = 'done'
				wo_process_state = 'not_allow'
			if (line_item.sc_id.sc_wo_qty + line_item.qty) < line_item.sc_id.sc_qty:
				wo_state = 'partial'
				wo_process_state = 'allow'
			
			sc_obj.write(cr, uid, line_item.sc_id.id, 
				{'sc_wo_qty': line_item.sc_id.sc_wo_qty + line_item.qty,'wo_state': wo_state,'wo_process_state':wo_process_state})
							
		sc_wo_name = ''	
		sc_wo_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.wo')])
		rec = self.pool.get('ir.sequence').browse(cr,uid,sc_wo_seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s','%s') """%(sc_wo_seq_id[0],rec.code,entry.entry_date))
		sc_wo_name = cr.fetchone();
							
		self.write(cr, uid, ids, {'state': 'confirmed','name':sc_wo_name[0]})
							
							
		return True
		
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		entry_date = rec.entry_date
		entry_date = str(entry_date)
		entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
		delivery_date = rec.delivery_date
		delivery_date = str(delivery_date)
		delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d')
		if entry_date > today:
			return False
		if delivery_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
		
	   ]
	
	
	
kg_subcontract_wo()



class ch_subcontract_wo_line(osv.osv):
	
	_name = "ch.subcontract.wo.line"
	_description = "Subcontract WO Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.subcontract.wo','Header Id'),
		'sc_id': fields.many2one('kg.subcontract.process','Subcontractor List Id'),
		'ms_id': fields.related('sc_id','ms_id', type='many2one', relation='kg.machineshop', string='MS Id', store=True, readonly=True),
		'production_id': fields.related('sc_id','production_id', type='many2one', relation='kg.production', string='Production No.', store=True, readonly=True),
		'position_id': fields.related('sc_id','position_id', type='many2one', relation='kg.position.number', string='Position No.', store=True, readonly=True),
		'order_id': fields.related('sc_id','order_id', type='many2one', relation='kg.work.order', string='Work Order', store=True, readonly=True),
		'order_line_id': fields.related('sc_id','order_line_id', type='many2one', relation='ch.work.order.details', string='Order Line', store=True, readonly=True),
		'order_no': fields.related('sc_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('sc_id','order_delivery_date', type='date', string='Delivery Date', store=True, readonly=True),

		'order_category': fields.related('sc_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.related('sc_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		'pump_model_id': fields.related('sc_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('sc_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_code': fields.related('sc_id','pattern_code', type='char', string='Pattern Code', store=True, readonly=True),
		'pattern_name': fields.related('sc_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'item_code': fields.related('sc_id','item_code', type='char', string='Item Code', store=True, readonly=True),
		'item_name': fields.related('sc_id','item_name', type='char', string='Item Name', store=True, readonly=True),
		'moc_id': fields.related('sc_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'ms_type': fields.related('sc_id','ms_type', type='selection', selection=[('foundry_item','Foundry Item'),('ms_item','MS Item')], string='Item Type', store=True, readonly=True),
		'operation_id': fields.many2one('kg.operation.master','Operation'),
		'sc_qty': fields.integer('SC Qty',readonly=True),
		'qty': fields.integer('Quantity'),
		'rate': fields.float('Rate'),
		'amount': fields.float('Amount'),
		'remarks': fields.text('Remarks'),
		
		
		
	}
	
	def onchange_sc_rate(self, cr, uid, ids, operation_id,position_id,qty,rate):
		amount = 0.00
		sc_cost = 0.00
		if operation_id:
			print "operation_id",operation_id
			print "position_id",position_id
			cr.execute(''' select sc_cost from ch_kg_position_number where operation_id = %s and header_id = %s  ''',[operation_id,position_id])
			sc_cost = cr.fetchone()
			print "sc_cost",sc_cost
			if sc_cost == None:
				sc_cost = rate
			else:
				sc_cost = sc_cost[0]
		if rate:
			sc_cost = rate
		amount = qty * sc_cost
		return {'value': {'rate': sc_cost,'amount':amount}}



ch_subcontract_wo_line()	



class kg_subcontract_dc(osv.osv):

	_name = "kg.subcontract.dc"
	_description = "Subcontract DC"
	_order = "entry_date desc"
	
	def _get_default_division(self, cr, uid, context=None):
		res = self.pool.get('kg.division.master').search(cr, uid, [('code','=','SAM'),('state','=','approved'), ('active','=','t')], context=context)
		return res and res[0] or False
		
	def _get_order_value(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		
		for entry in self.browse(cr, uid, ids, context=context):
			cr.execute(''' select sum(amount) from ch_subcontract_wo_line where header_id = %s ''',[entry.id])
			wo_value = cr.fetchone()
			if wo_value[0] == None:
				wo_value = 0.00
			else:
				wo_value=wo_value[0]
			wo_value = wo_value
			result[entry.id] = wo_value
		return result
		
		
	_columns = {

	
		'name': fields.char('WO No.', size=128,select=True,readonly=True),
		'entry_date': fields.date('WO Date',required=True),
		'division_id': fields.many2one('kg.division.master','Division'),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location'),
		'active': fields.boolean('Active'),
		'contractor_id': fields.many2one('res.partner','Subcontractor'),
		'contact_person': fields.char('Contact Person', size=128),
		'phone': fields.char('Phone',size=64),
		'delivery_date': fields.date('Expected Delivery Date'),
		'wo_value': fields.function(_get_order_value, string='WO Value', method=True, store=True, type='float'),
		'billing_type': fields.selection([('applicable','Applicable'),('not_applicable','Not Applicable')],'Billing Type'),
		'sc_line_ids': fields.many2many('kg.subcontract.process','m2m_sc_details' , 'order_id', 'sc_id', 'SC Items',
			domain="[('wo_state','in',('pending','partial')),('wo_process_state','=','allow')]"),
		'line_ids': fields.one2many('ch.subcontract.wo.line','header_id','Subcontract WO Line'),   
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'flag_order': fields.boolean('Flag Order'),
		
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
				
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_subcontract_wo', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'delivery_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'division_id':_get_default_division,
		'flag_order': False,
		'state': 'draft'
		
	}
	
	def onchange_contractor(self, cr, uid, ids, contractor_id):
		if contractor_id:
			contractor_rec = self.pool.get('res.partner').browse(cr, uid, contractor_id)
		return {'value': {'contact_person':contractor_rec.contact_person,'phone':contractor_rec.phone  }}
	
	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		wo_line_obj = self.pool.get('ch.subcontract.wo.line')
		sc_obj = self.pool.get('kg.subcontract.process')
		
		del_sql = """ delete from ch_subcontract_wo_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.sc_line_ids:
		
			for item in entry.sc_line_ids:
				
				sc_qty = item.sc_qty - item.sc_wo_qty
				
				vals = {
				
					'header_id': entry.id,
					'sc_id':item.id,
					'qty':sc_qty,
					'sc_qty':sc_qty,
					
				}
				
				wo_line_id = wo_line_obj.create(cr, uid,vals)
				
				sc_obj.write(cr, uid, item.id, {'wo_process_state': 'not_allow'})
				
			self.write(cr, uid, ids, {'flag_order': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		sc_obj = self.pool.get('kg.subcontract.process')
		
		for line_item in entry.line_ids:
			
			if line_item.qty < 0 and line_item.rate < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative values !!'))
							
			if line_item.qty == 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save Zero values !!'))
							
			if line_item.qty > line_item.sc_qty:
				raise osv.except_osv(_('Warning!'),
							_('Check the SC Qty !!! '))
			
			if (line_item.sc_id.sc_wo_qty + line_item.qty) == line_item.sc_id.sc_qty:
				wo_state = 'done'
				wo_process_state = 'not_allow'
			if (line_item.sc_id.sc_wo_qty + line_item.qty) < line_item.sc_id.sc_qty:
				wo_state = 'partial'
				wo_process_state = 'allow'
			
			sc_obj.write(cr, uid, line_item.sc_id.id, 
				{'sc_wo_qty': line_item.sc_id.sc_wo_qty + line_item.qty,'wo_state': wo_state,'wo_process_state':wo_process_state})
							
		sc_wo_name = ''	
		sc_wo_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.wo')])
		rec = self.pool.get('ir.sequence').browse(cr,uid,sc_wo_seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s','%s') """%(sc_wo_seq_id[0],rec.code,entry.entry_date))
		sc_wo_name = cr.fetchone();
							
		self.write(cr, uid, ids, {'state': 'confirmed','name':sc_wo_name[0]})
							
							
		return True
		
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		entry_date = rec.entry_date
		entry_date = str(entry_date)
		entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
		delivery_date = rec.delivery_date
		delivery_date = str(delivery_date)
		delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d')
		if entry_date > today:
			return False
		if delivery_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
		
	   ]
	
	
	
kg_subcontract_wo()







