from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re 

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
		'contractor_id': fields.many2one('res.partner','Contractor Name',required=True),
		
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
		'ms_op_id': fields.many2one('kg.ms.operations','MS Operation Id'),		
		
		'actual_qty': fields.integer('Actual Qty'),		
		'total_qty': fields.integer('Total Qty'),
		'sc_wo_qty': fields.integer('SC WO Qty'),
		'sc_dc_qty': fields.integer('SC DC Qty'),
		'sc_inward_qty': fields.integer('SC Inward Qty'),
		'pending_qty': fields.integer('Pending Qty'),
		
		'state': fields.selection([('draft','Draft'),('wo_inprocess','WO Inprocess'),('dc_inprocess','DC Inprocess'),('inward_inprocess','Inward Inprocess')], 'Status'),
		'wo_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')], 'WO Status'),
		'dc_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')], 'DC Status'),
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
		'dc_state': 'pending',
		'wo_process_state': 'allow',
		'state': 'draft',
		'sc_inward_qty': 0,
		
	}
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):							
			raise osv.except_osv(_('Warning!'),
					_('You can not delete this entry !!'))			
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)	
	
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
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('confirmed_dc','Confirmed & DC'),('cancel','Cancelled')],'Status', readonly=True),
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
		'billing_type': 'applicable',
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
				vals = {								
					'header_id': entry.id,
					'sc_id':item.id,
					'qty':item.pending_qty ,
					'actual_qty':item.actual_qty,
					'dc_qty':item.pending_qty,					
				}
				
				wo_line_id = wo_line_obj.create(cr, uid,vals)
				
				sc_obj.write(cr, uid, item.id, {'wo_process_state': 'not_allow'})
				
			self.write(cr, uid, ids, {'flag_order': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		sc_obj = self.pool.get('kg.subcontract.process')
		if len(entry.line_ids) == 0:
			raise osv.except_osv(_('Warning!'),
							_('System not allow to without line items !!'))
		
		for line_item in entry.line_ids:
			
			if line_item.qty < 0 and line_item.rate < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative values !!'))
			if line_item.rate == 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save Zero values in Rate !!'))							
			if line_item.qty == 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save Zero values !!'))				
			
			
			if (line_item.sc_id.sc_wo_qty + line_item.qty) == line_item.sc_id.total_qty:
				wo_state = 'done'
				wo_process_state = 'not_allow'
			if (line_item.sc_id.sc_wo_qty + line_item.qty) < line_item.sc_id.total_qty:
				wo_state = 'partial'
				wo_process_state = 'allow'
			if (line_item.sc_id.sc_wo_qty + line_item.qty) > line_item.sc_id.total_qty:
				wo_state = 'done'
				wo_process_state = 'not_allow'
			self.pool.get('ch.subcontract.wo.line').write(cr,uid,line_item.id,{'pending_qty':line_item.qty})
			sc_obj.write(cr, uid, line_item.sc_id.id, 
				{'pending_qty':line_item.sc_id.pending_qty - line_item.qty,'sc_wo_qty': line_item.sc_id.sc_wo_qty + line_item.qty,'wo_state': wo_state,'wo_process_state':wo_process_state,'state':'wo_inprocess'})
							
		sc_wo_name = ''	
		sc_wo_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.wo')])
		rec = self.pool.get('ir.sequence').browse(cr,uid,sc_wo_seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s','%s') """%(sc_wo_seq_id[0],rec.code,entry.entry_date))
		sc_wo_name = cr.fetchone();
							
		self.write(cr, uid, ids, {'state': 'confirmed','name':sc_wo_name[0]})		
							
		return True
		
	def confirm_dc(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		sc_obj = self.pool.get('kg.subcontract.process')
		dc_obj = self.pool.get('kg.subcontract.dc')
		dc_obj_line = self.pool.get('ch.subcontract.dc.line')		
		dc_id = dc_obj.create(cr,uid,{'transfer_type':'sub_contractor','contractor_id':entry.contractor_id.id,'flag_dc':True,'entry_mode': 'from_wo'})	
		if len(entry.line_ids) == 0:
			raise osv.except_osv(_('Warning!'),
							_('System not allow to without line items !!'))
		for line_item in entry.line_ids:			
			dc_line = dc_obj_line.create(cr,uid,{'header_id':dc_id,'sc_id':line_item.sc_id.id,'qty':line_item.qty,'sc_dc_qty':line_item.qty,'operation_id':[(6, 0, [x.id for x in line_item.operation_id])],		
			'actual_qty':line_item.actual_qty,'sc_wo_line_id': line_item.id,'entry_mode': 'from_wo','pending_qty':line_item.qty})			
			
			if line_item.qty < 0 and line_item.rate < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative values !!'))
			if line_item.rate == 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save Zero values in Rate !!'))	
							
			if line_item.qty == 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save Zero values !!'))			
			
			if (line_item.sc_id.sc_wo_qty + line_item.qty) == line_item.sc_id.total_qty:
				wo_state = 'done'
				wo_process_state = 'not_allow'
			if (line_item.sc_id.sc_wo_qty + line_item.qty) < line_item.sc_id.total_qty:
				wo_state = 'partial'
				wo_process_state = 'allow'
			if (line_item.sc_id.sc_wo_qty + line_item.qty) > line_item.sc_id.total_qty:
				wo_state = 'done'
				wo_process_state = 'not_allow'
			
			self.pool.get('ch.subcontract.wo.line').write(cr,uid,line_item.id,{'dc_flag':True,'pending_qty':line_item.qty})
			sc_obj.write(cr, uid, line_item.sc_id.id, 
				{'pending_qty':line_item.sc_id.pending_qty - line_item.qty,'sc_wo_qty': line_item.sc_id.sc_wo_qty + line_item.qty,'wo_state': wo_state,'wo_process_state':wo_process_state})
							
		sc_wo_name = ''	
		sc_wo_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.wo')])
		rec = self.pool.get('ir.sequence').browse(cr,uid,sc_wo_seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s','%s') """%(sc_wo_seq_id[0],rec.code,entry.entry_date))
		sc_wo_name = cr.fetchone();
							
		self.write(cr, uid, ids, {'state': 'confirmed','name':sc_wo_name[0]})
							
							
		return True
	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state not in ('draft'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)	
	
		
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
		'contractor_id': fields.related('header_id','contractor_id', type='many2one', relation='res.partner', string='Contractor Name', store=True, readonly=True),
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
		'operation_id': fields.many2many('ch.kg.position.number', 'm2m_wo_operation_details', 'wo_operation_id', 'wo_sub_id','Operation' , domain="[('header_id','=',position_id)]"),
		
		'actual_qty': fields.integer('Actual Qty',readonly=True),
		'sc_dc_qty': fields.integer('DC Qty',readonly=True),		
		'qty': fields.integer('Quantity'),
		'pending_qty': fields.integer('Pending Qty'),
		
		'rate': fields.float('Rate'),
		'amount': fields.float('Amount'),
		'remarks': fields.text('Remarks'),		
		'dc_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')], 'DC Status', readonly=True),
		'dc_flag': fields.boolean('DC Flag'),
		
	}
	
	
	_defaults = {
		
		'dc_state': 'pending',
		'dc_flag': False
		
	}
	
	def onchange_sc_rate(self, cr, uid, ids, operation_id,position_id,qty,rate):
		amount = 0.00
		sc_cost = 0.00
		if operation_id and position_id:
			s= [(6, 0, [x for x in operation_id])]
			d = s[0][2][0][2]			
			a = []
			for ele in d:	
				op_rec = self.pool.get('ch.kg.position.number').browse(cr,uid,ele)
				open_ids = op_rec.operation_id.id
				a.append(open_ids)				
			if len(a) == 1:				
				result2 =  tuple(str(a[0]))
			else:
				result2 = tuple(a)			
			if result2:				
				cr.execute(''' select sum(sc_cost) from ch_kg_position_number where operation_id in %s and header_id = %s  ''',[result2,position_id])
				sc_cost = cr.fetchone()
				print "sc_cost",sc_cost
				if sc_cost[0] == None:
					sc_cost = 0.00
				else:
					sc_cost = sc_cost[0]			
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
		
		
	_columns = {

	
		'name': fields.char('DC No.', size=128,select=True,readonly=True),
		'entry_date': fields.date('DC Date',required=True),
		'division_id': fields.many2one('kg.division.master','From Division'),
		'to_division_id': fields.many2one('kg.division.master','To Division'),
		'transfer_type': fields.selection([('internal','Internal'),('sub_contractor','Sub Contractor')],'Type'),
		'active': fields.boolean('Active'),
		'contractor_id': fields.many2one('res.partner','Subcontractor'),	
		'phone': fields.char('Phone',size=64),
		'contact_person': fields.char('Contact Person', size=128),		
		
		'dc_internal_line_ids': fields.many2many('kg.subcontract.process','m2m_dc_details' , 'order_id', 'sc_id', 'SC Items',
			domain="[('wo_state','in',('pending','partial')),('wo_process_state','=','allow')]"),
		'dc_sub_line_ids': fields.many2many('ch.subcontract.wo.line','m2m_dc_sub_details' , 'order_id', 'sc_id', 'SC Items',
		 domain="[('dc_state','in',('pending','partial')),('contractor_id','=',contractor_id),('dc_flag','=',False)]"),  
			
		'line_ids': fields.one2many('ch.subcontract.dc.line','header_id','Subcontract DC Line'),   
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'flag_dc': fields.boolean('Flag Order'),
		'entry_mode': fields.selection([('direct','Direct'),('from_wo','From WO')],'Entry Mode', readonly=True),
		'vehicle_detail': fields.char('Vehicle Detail'),
		
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
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'flag_dc': False,
		'division_id':_get_default_division,		
		'state': 'draft',
		'transfer_type': 'internal',
		'entry_mode': 'direct'
		
	}
	
	def onchange_contractor(self, cr, uid, ids, contractor_id):
		if contractor_id:
			contractor_rec = self.pool.get('res.partner').browse(cr, uid, contractor_id)
		return {'value': {'contact_person':contractor_rec.contact_person,'phone':contractor_rec.phone  }}
	
	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		wo_line_obj = self.pool.get('ch.subcontract.dc.line')
		sc_obj = self.pool.get('kg.subcontract.process')
		
		del_sql = """ delete from ch_subcontract_dc_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.dc_internal_line_ids:
		
			for item in entry.dc_internal_line_ids:
				
				sc_qty = item.actual_qty 
				
				vals = {
				
					'header_id': entry.id,
					'sc_id':item.id,
					'qty':sc_qty - item.sc_wo_qty,
					'pending_qty':sc_qty - item.sc_wo_qty,
					'sc_dc_qty':sc_qty - item.sc_wo_qty,
					'actual_qty':sc_qty,
					
					
				}
				
				wo_line_id = wo_line_obj.create(cr, uid,vals)
				
				sc_obj.write(cr, uid, item.id, {'wo_process_state': 'not_allow'})
				
			self.write(cr, uid, ids, {'flag_dc': True})
			
		if entry.dc_sub_line_ids:
		
			for item in entry.dc_sub_line_ids:
				
				sc_qty = item.actual_qty 
				
				vals = {
				
					'header_id': entry.id,
					'sc_id':item.sc_id.id,
					'qty':item.qty - item.sc_dc_qty,
					'pending_qty':item.qty - item.sc_dc_qty,
					'actual_qty':sc_qty,					
					'sc_dc_qty':item.qty - item.sc_dc_qty,					
					'sc_wo_line_id': item.id,
					'operation_id':[(6, 0, [x.id for x in item.operation_id])],		
				}
				
				wo_line_id = wo_line_obj.create(cr, uid,vals)
				
				
				
			self.write(cr, uid, ids, {'flag_dc': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		sc_obj = self.pool.get('kg.subcontract.process')
		sc_wo_line_obj = self.pool.get('ch.subcontract.wo.line')
		print"entry.dc_sub_line_ids",entry.dc_sub_line_ids	
		print"entry.dc_internal_line_ids",entry.dc_internal_line_ids
		special_char = ''.join( c for c in entry.vehicle_detail if  c in '!@#$%^~*{}?+/=_-><?/`' )
		if len(entry.line_ids) == 0:
			raise osv.except_osv(_('Warning!'),
							_('System not allow to without line items !!'))
		
		if special_char:
			raise osv.except_osv(_('Vehicle Detail'),
								_('Special Character Not Allowed !!!'))	
				
		if entry.dc_sub_line_ids:
			for line_item in entry.line_ids:				
				if line_item.qty < 0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative values !!'))							
				if line_item.qty == 0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save Zero values !!'))	
								
				if (line_item.sc_id.sc_dc_qty + line_item.qty) == line_item.sc_id.actual_qty:
					dc_state = 'done'					
				if (line_item.sc_id.sc_dc_qty + line_item.qty) < line_item.sc_id.actual_qty:
					dc_state = 'done'									
				if (line_item.sc_id.sc_dc_qty + line_item.qty) > line_item.sc_id.actual_qty:
					dc_state = 'partial'				
										
				if line_item.sc_id.pending_qty <= 0:					
					wo_process_state = 'not_allow'
				if line_item.sc_id.pending_qty > 0:					
					wo_process_state = 'allow'
									
				if (line_item.sc_wo_line_id.sc_dc_qty + line_item.qty) == line_item.sc_wo_line_id.qty:
					wo_dc_state = 'done'
					
				if (line_item.sc_wo_line_id.sc_dc_qty + line_item.qty) < line_item.sc_wo_line_id.qty:
					wo_dc_state = 'partial'
				
				self.pool.get('ch.subcontract.dc.line').write(cr,uid,line_item.id,{'pending_qty':line_item.qty,'entry_type':'sub_contract'})
					
				sc_obj.write(cr, uid, line_item.sc_id.id, 
							{'sc_dc_qty': line_item.sc_id.sc_dc_qty + line_item.qty,'dc_state': dc_state,'wo_process_state':wo_process_state})		
							
				sc_wo_line_obj.write(cr, uid, line_item.sc_wo_line_id.id, 
							{'pending_qty': line_item.sc_wo_line_id.pending_qty - line_item.qty,'sc_dc_qty': line_item.sc_wo_line_id.sc_dc_qty + line_item.qty,'dc_state': wo_dc_state})				
							
		if entry.dc_internal_line_ids:	
			for line_item in entry.line_ids:				
				if line_item.qty < 0 and line_item.rate < 0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative values !!'))								
				if line_item.qty == 0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save Zero values !!'))
								
				
				if (line_item.sc_id.sc_wo_qty + line_item.qty) == line_item.sc_id.actual_qty:
					dc_state = 'done'			
				if (line_item.sc_id.sc_wo_qty + line_item.qty) > line_item.sc_id.actual_qty:
					dc_state = 'done'					
				if (line_item.sc_id.sc_dc_qty + line_item.qty) < line_item.sc_id.actual_qty:
					dc_state = 'partial'									
							
				if line_item.sc_id.pending_qty <= 0:					
					wo_process_state = 'not_allow'
				if line_item.sc_id.pending_qty > 0:					
					wo_process_state = 'allow'
				
				if (line_item.sc_id.sc_wo_qty + line_item.qty) == line_item.sc_id.actual_qty:
					wo_state = 'done'					
					
				if (line_item.sc_id.sc_wo_qty + line_item.qty) < line_item.sc_id.actual_qty:
					wo_state = 'partial'
											
				self.pool.get('ch.subcontract.dc.line').write(cr,uid,line_item.id,{'pending_qty':line_item.qty,'entry_type':'internal'})	
				sc_obj.write(cr, uid, line_item.sc_id.id, 
							{'pending_qty': line_item.sc_id.pending_qty - line_item.qty,'sc_dc_qty': line_item.sc_id.sc_dc_qty + line_item.qty,'dc_state':dc_state,				
							'sc_wo_qty': line_item.sc_id.sc_wo_qty + line_item.qty,'wo_state':wo_state,				
							'wo_process_state':wo_process_state})	
		
		else:
			for line_item in entry.line_ids:				
				if line_item.qty < 0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative values !!'))							
				if line_item.qty == 0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save Zero values !!'))								
												
				if (line_item.sc_id.sc_dc_qty + line_item.qty) == line_item.sc_id.actual_qty:
					dc_state = 'done'					
				if (line_item.sc_id.sc_dc_qty + line_item.qty) < line_item.sc_id.actual_qty:
					dc_state = 'done'									
				if (line_item.sc_id.sc_dc_qty + line_item.qty) > line_item.sc_id.actual_qty:
					dc_state = 'partial'				
										
				if line_item.sc_id.pending_qty <= 0:					
					wo_process_state = 'not_allow'
				if line_item.sc_id.pending_qty > 0:					
					wo_process_state = 'allow'
									
				if (line_item.sc_wo_line_id.sc_dc_qty + line_item.qty) == line_item.sc_wo_line_id.qty:
					wo_dc_state = 'done'
					
				if (line_item.sc_wo_line_id.sc_dc_qty + line_item.qty) < line_item.sc_wo_line_id.qty:
					wo_dc_state = 'partial'
				
				self.pool.get('ch.subcontract.dc.line').write(cr,uid,line_item.id,{'pending_qty':line_item.qty,'entry_type':'sub_contract'})
					
				sc_obj.write(cr, uid, line_item.sc_id.id, 
							{'sc_dc_qty': line_item.sc_id.sc_dc_qty + line_item.qty,'dc_state': dc_state,'wo_process_state':wo_process_state})		
							
				sc_wo_line_obj.write(cr, uid, line_item.sc_wo_line_id.id, 
							{'pending_qty': line_item.sc_wo_line_id.pending_qty - line_item.qty,'sc_dc_qty': line_item.sc_wo_line_id.sc_dc_qty + line_item.qty,'dc_state': wo_dc_state})				
														
				
				
		sc_wo_name = ''	
		sc_wo_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.dc')])
		rec = self.pool.get('ir.sequence').browse(cr,uid,sc_wo_seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s','%s') """%(sc_wo_seq_id[0],rec.code,entry.entry_date))
		sc_wo_name = cr.fetchone();
							
		self.write(cr, uid, ids, {'state': 'confirmed','name':sc_wo_name[0]})
							
							
		return True
	
	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state not in ('draft'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)	
		
		
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
		
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
		
	   ]
	
	
	
kg_subcontract_dc()




class ch_subcontract_dc_line(osv.osv):
	
	_name = "ch.subcontract.dc.line"
	_description = "Subcontract DC Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.subcontract.dc','Header Id'),
		'contractor_id': fields.related('header_id','contractor_id', type='many2one', relation='res.partner', string='Contractor Name', store=True, readonly=True),
		'sc_id': fields.many2one('kg.subcontract.process','Subcontractor List Id'),
		'sc_wo_line_id': fields.many2one('ch.subcontract.wo.line','Subcontractor WO List Id'),
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
		'operation_id': fields.many2many('ch.kg.position.number', 'm2m_dc_operation_details', 'dc_operation_id', 'dc_sub_id','Operation', domain="[('header_id','=',position_id)]"),
		
		
		'entry_type': fields.selection([('sub_contract','Sub Contract'),('internal','Internal')],'Entry Type', readonly=True),
		
		'actual_qty': fields.integer('Actual Qty',readonly=True),
		'qty': fields.integer('Quantity'),
		'sc_dc_qty': fields.integer('Qty'),
		'sc_in_qty': fields.integer('Quantity'),
		'pending_qty': fields.integer('Pending Qty'),
		
		'each_weight': fields.float('Each Weight'),
		'totel_weight': fields.float('Total weight'),
				
		'remarks': fields.text('Remarks'),
		'state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')],'Status', readonly=True),
		'entry_mode': fields.selection([('direct','Direct'),('from_wo','From WO')],'Entry Mode', readonly=True),
		
	}
	
	_defaults = {
		
		'state': 'pending',
		'entry_mode': 'direct',
		
	}
	
	def onchange_total_weight(self, cr, uid, ids, each_weight,qty):				
		total_weight = qty * each_weight
		return {'value': {'totel_weight': total_weight}}


ch_subcontract_dc_line()	





class kg_subcontract_inward(osv.osv):

	_name = "kg.subcontract.inward"
	_description = "Subcontract Inward"
	_order = "entry_date desc"		
		
	_columns = {

	
		'name': fields.char('Inward No.', size=128,select=True,readonly=True),
		'entry_date': fields.date('Inward Date',required=True),		
		'active': fields.boolean('Active'),		
		'division_id': fields.many2one('kg.division.master','From Division'),
		'to_division_id': fields.many2one('kg.division.master','To Division'),
		'transfer_type': fields.selection([('internal','Internal'),('sub_contractor','Sub Contractor')],'Type'),
		'contractor_id': fields.many2one('res.partner','Subcontractor'),
		'phone': fields.char('Phone',size=64),
		'contact_person': fields.char('Contact Person', size=128),	
		
		'dc_line_ids': fields.many2many('ch.subcontract.dc.line','m2m_inward_details' , 'order_id', 'sc_id', 'SC Items',
			domain="[('state','in',('pending','partial')),('entry_type','=','internal')]"),			
		'inward_sub_line_ids': fields.many2many('ch.subcontract.dc.line','m2m_inward_sub_details' , 'order_id', 'sc_id', 'SC Items',
		 domain="[('state','in',('pending','partial')),('contractor_id','=',contractor_id),('entry_type','=','sub_contract')]"),  
		 
		 			
		'line_ids': fields.one2many('ch.subcontract.inward.line','header_id','Subcontract Inward Line'),   
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'flag_inward': fields.boolean('Flag Order'),		
		'vehicle_detail': fields.char('Vehicle Detail'),
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
				
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_subcontract_inward', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),		
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'flag_inward': False,
		'transfer_type': 'internal',				
		'state': 'draft',		
	}
	
	def onchange_contractor(self, cr, uid, ids, contractor_id):
		if contractor_id:
			contractor_rec = self.pool.get('res.partner').browse(cr, uid, contractor_id)
		return {'value': {'contact_person':contractor_rec.contact_person,'phone':contractor_rec.phone  }}
	
	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		wo_line_obj = self.pool.get('ch.subcontract.inward.line')
			
		del_sql = """ delete from ch_subcontract_inward_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		for item in entry.dc_line_ids:			
			
			
			vals = {
			
				'header_id': entry.id,
				'sc_id':item.sc_id.id,
				'qty':item.qty - item.sc_in_qty,								
				'actual_qty':item.actual_qty,		
				'each_weight':item.each_weight,					
				'sc_dc_line_id':item.id,	
				'operation_id':[(6, 0, [x.id for x in item.operation_id])],
				
			}
			
			in_line_id = wo_line_obj.create(cr, uid,vals)	
		
		for item in entry.inward_sub_line_ids:			
			
			
			vals = {
			
				'header_id': entry.id,
				'sc_id':item.sc_id.id,
				'qty':item.qty - item.sc_in_qty,								
				'actual_qty':item.actual_qty,		
				'each_weight':item.each_weight,					
				'sc_dc_line_id':item.id,	
				'operation_id':[(6, 0, [x.id for x in item.operation_id])],
				
			}
			
			in_line_id = wo_line_obj.create(cr, uid,vals)			
			
		self.write(cr, uid, ids, {'flag_inward': True})
		
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])		
		sc_dc_line_obj = self.pool.get('ch.subcontract.dc.line')
		sc_obj = self.pool.get('kg.subcontract.process')
		ms_operation_obj = self.pool.get('kg.ms.operations')
		ms_dimension_obj = self.pool.get('ch.ms.dimension.details')
		ms_obj = self.pool.get('kg.machineshop')			
		sql_check = """select sc_id,actual_qty,position_id from ch_subcontract_inward_line where header_id = %s group by sc_id,actual_qty,position_id""" %(entry.id)
		cr.execute(sql_check)
		data = cr.dictfetchall()
		print"datadata",data
		if len(entry.line_ids) == 0:
			raise osv.except_osv(_('Warning!'),
							_('System not allow to without line items !!'))
		if data:
			for ele in data:
				sql_id = """select id from ch_subcontract_inward_line where sc_id = %s limit 1""" %(ele['sc_id'])
				cr.execute(sql_id)
				data_id = cr.dictfetchone()				
				sc_in_qty = """select sc_inward_qty from kg_subcontract_process where id = %s""" %(ele['sc_id'])
				cr.execute(sc_in_qty)
				sc_inward_qty = cr.dictfetchone()	
				print"sc_inward_qty",sc_inward_qty				
				line_item = self.pool.get('ch.subcontract.inward.line').browse(cr,uid,data_id['id'])				
				sql_qty = """ select sum(qty) from ch_subcontract_inward_line where sc_id = %s """ %(ele['sc_id'])
				cr.execute(sql_qty)
				data_qty = cr.dictfetchone()				
				total_qty = data_qty['sum'] - ele['actual_qty']
				total = total_qty - sc_inward_qty['sc_inward_qty']
				print"totaltotal",total							
				
				op1_status = ''
				op2_status = ''
				op3_status = ''
				op4_status = ''
				op5_status = ''
				op6_status = ''
				op7_status = ''
				op8_status = ''
				op9_status = ''
				op10_status = ''
				op11_status = ''
				op12_status = ''
				op1_id = False
				op2_id = False
				op3_id = False
				op4_id = False
				op5_id = False
				op6_id = False
				op7_id = False
				op8_id = False
				op9_id = False
				op10_id = False
				op11_id = False
				op12_id = False
				op1_stage_id = False
				op2_stage_id = False
				op3_stage_id = False
				op4_stage_id = False
				op5_stage_id = False
				op6_stage_id = False
				op7_stage_id = False
				op8_stage_id = False
				op9_stage_id = False
				op10_stage_id = False
				op11_stage_id = False
				op12_stage_id = False
				op1_clamping_area = ''
				op2_clamping_area = ''
				op3_clamping_area = ''
				op4_clamping_area = ''
				op5_clamping_area = ''
				op6_clamping_area = ''
				op7_clamping_area = ''
				op8_clamping_area = ''
				op9_clamping_area = ''
				op10_clamping_area = ''
				op11_clamping_area = ''
				op12_clamping_area = ''
				### MS Operation Creation ###
				if ele['actual_qty'] > 0:
					if ele['position_id'] != False:
						position_id = self.pool.get('kg.position.number').browse(cr,uid,ele['position_id'])
						for pos_line_item in position_id.line_ids:
							
							if pos_line_item.operation_id.name == 'Operation 1':
								op1_status = 'pending'
								op1_id = pos_line_item.operation_id.id
								op1_stage_id = pos_line_item.stage_id.id
								op1_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == 'Operation 2':
								op2_status = 'pending'
								op2_id = pos_line_item.operation_id.id
								op2_stage_id = pos_line_item.stage_id.id
								op2_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == 'Operation 3':
								op3_status = 'pending'
								op3_id = pos_line_item.operation_id.id
								op3_stage_id = pos_line_item.stage_id.id
								op3_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == 'Operation 4':
								op4_status = 'pending'
								op4_id = pos_line_item.operation_id.id
								op4_stage_id = pos_line_item.stage_id.id
								op4_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == 'Operation 5':
								op5_status = 'pending'
								op5_id = pos_line_item.operation_id.id
								op5_stage_id = pos_line_item.stage_id.id
								op5_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == 'Operation 6':
								op6_status = 'pending'
								op6_id = pos_line_item.operation_id.id
								op6_stage_id = pos_line_item.stage_id.id
								op6_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == 'Operation 7':
								op7_status = 'pending'
								op7_id = pos_line_item.operation_id.id
								op7_stage_id = pos_line_item.stage_id.id
								op7_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == 'Operation 8':
								op8_status = 'pending'
								op8_id = pos_line_item.operation_id.id
								op8_stage_id = pos_line_item.stage_id.id
								op8_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == 'Operation 9':
								op9_status = 'pending'
								op9_id = pos_line_item.operation_id.id
								op9_stage_id = pos_line_item.stage_id.id
								op9_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == 'Operation 10':
								op10_status = 'pending'
								op10_id = pos_line_item.operation_id.id
								op10_stage_id = pos_line_item.stage_id.id
								op10_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == 'Operation 11':
								op11_status = 'pending'
								op11_id = pos_line_item.operation_id.id
								op11_stage_id = pos_line_item.stage_id.id
								op11_clamping_area = pos_line_item.clamping_area
								
							if pos_line_item.operation_id.name == 'Operation 12':
								op12_status = 'pending'
								op12_id = pos_line_item.operation_id.id
								op12_stage_id = pos_line_item.stage_id.id
								op12_clamping_area = pos_line_item.clamping_area
						
						### Operation Creation ###
						
						for operation in range(ele['actual_qty']):
														
							operation_vals = {
								'ms_id': line_item.ms_id.id,													
								'ms_plan_id': line_item.sc_id.ms_plan_id.id,													
								'ms_plan_line_id': line_item.sc_id.ms_plan_line_id.id,																		
								'inhouse_qty': 1,
								'op1_stage_id': op1_stage_id,
								'op1_clamping_area': op1_clamping_area,
								'op1_id': op1_id,
								'op1_state':op1_status,
								'op2_stage_id': op2_stage_id,
								'op2_clamping_area': op2_clamping_area,
								'op2_id': op2_id,
								'op2_state': op2_status,
								'op3_stage_id': op3_stage_id,
								'op3_clamping_area': op3_clamping_area,
								'op3_id': op3_id,
								'op3_state': op3_status,
								'op4_stage_id': op4_stage_id,
								'op4_clamping_area': op4_clamping_area,
								'op4_id': op4_id,
								'op4_state': op4_status,
								'op5_stage_id': op5_stage_id,
								'op5_clamping_area': op5_clamping_area,
								'op5_id': op5_id,
								'op5_state': op5_status,
								'op6_stage_id': op6_stage_id,
								'op6_clamping_area': op6_clamping_area,
								'op6_id': op6_id,
								'op6_state': op6_status,
								'op7_stage_id': op7_stage_id,
								'op7_clamping_area': op7_clamping_area,
								'op7_id': op7_id,
								'op7_state': op7_status,
								'op8_stage_id': op8_stage_id,
								'op8_clamping_area': op8_clamping_area,
								'op8_id': op8_id,
								'op8_state': op8_status,
								'op9_stage_id': op9_stage_id,
								'op9_clamping_area': op9_clamping_area,
								'op9_id': op9_id,
								'op9_state': op9_status,
								'op10_stage_id': op10_stage_id,
								'op10_clamping_area': op10_clamping_area,
								'op10_id': op10_id,
								'op10_state': op10_status,
								'op11_stage_id': op11_stage_id,
								'op11_clamping_area': op11_clamping_area,
								'op11_id': op11_id,
								'op11_state': op11_status,
								'op12_stage_id': op12_stage_id,
								'op12_clamping_area': op12_clamping_area,
								'op12_id': op12_id,
								'op12_state': op12_status,
								
							}
							
							ms_operation_id = ms_operation_obj.create(cr, uid, operation_vals)
							
							ms_operation_obj.write(cr, uid, ms_operation_id, {'last_operation_check_id':ms_operation_id})
							
							### Creating Dimension Details ###
							
							if ele['position_id'] != False:
								position_id = self.pool.get('kg.position.number').browse(cr,uid,ele['position_id'])
								for pos_line_item in position_id.line_ids:
									
									
									if pos_line_item.operation_id.name == 'Operation 1':
										
										for op1_dimen_item in pos_line_item.line_ids:
											op1_dimen_vals = {
												
												'header_id': ms_operation_id,
												'position_id': pos_line_item.header_id.id,
												'operation_id': pos_line_item.operation_id.id,
												'operation_name': pos_line_item.operation_id.name,
												'position_line': op1_dimen_item.header_id.id,
												'pos_dimension_id': op1_dimen_item.id,
												'dimension_id': op1_dimen_item.dimension_id.id,
												#~ 'clamping_area': op1_dimen_item.clamping_area,
												'description': op1_dimen_item.description,
												'min_val': op1_dimen_item.min_val,
												'max_val': op1_dimen_item.max_val,
												'remark': op1_dimen_item.remark,
												
												}
											
											op1_ms_dimension_id = ms_dimension_obj.create(cr, uid,op1_dimen_vals)
											
									
									if pos_line_item.operation_id.name == 'Operation 2':
										
										for op2_dimen_item in pos_line_item.line_ids:
											
											op2_dimen_vals = {
												
												'header_id': ms_operation_id,
												'position_id': pos_line_item.header_id.id,
												'operation_id': pos_line_item.operation_id.id,
												'operation_name': pos_line_item.operation_id.name,
												'position_line': op2_dimen_item.header_id.id,
												'pos_dimension_id': op2_dimen_item.id,
												'dimension_id': op2_dimen_item.dimension_id.id,
												#~ 'clamping_area': op2_dimen_item.clamping_area,
												'description': op2_dimen_item.description,
												'min_val': op2_dimen_item.min_val,
												'max_val': op2_dimen_item.max_val,
												'remark': op2_dimen_item.remark,
												
												}
											
											op2_ms_dimension_id = ms_dimension_obj.create(cr, uid,op2_dimen_vals)
											
											
									if pos_line_item.operation_id.name == 'Operation 3':
										
										for op3_dimen_item in pos_line_item.line_ids:
											
											op3_dimen_vals = {
												
												'header_id': ms_operation_id,
												'position_id': pos_line_item.header_id.id,
												'operation_id': pos_line_item.operation_id.id,
												'operation_name': pos_line_item.operation_id.name,
												'position_line': op3_dimen_item.header_id.id,
												'pos_dimension_id': op3_dimen_item.id,
												'dimension_id': op3_dimen_item.dimension_id.id,
												#~ 'clamping_area': op2_dimen_item.clamping_area,
												'description': op3_dimen_item.description,
												'min_val': op3_dimen_item.min_val,
												'max_val': op3_dimen_item.max_val,
												'remark': op3_dimen_item.remark,
												
												}
											
											op3_ms_dimension_id = ms_dimension_obj.create(cr, uid,op3_dimen_vals)
											
											
									if pos_line_item.operation_id.name == 'Operation 4':
										
										for op4_dimen_item in pos_line_item.line_ids:
											
											op4_dimen_vals = {
												
												'header_id': ms_operation_id,
												'position_id': pos_line_item.header_id.id,
												'operation_id': pos_line_item.operation_id.id,
												'operation_name': pos_line_item.operation_id.name,
												'position_line': op4_dimen_item.header_id.id,
												'pos_dimension_id': op4_dimen_item.id,
												'dimension_id': op4_dimen_item.dimension_id.id,
												#~ 'clamping_area': op2_dimen_item.clamping_area,
												'description': op4_dimen_item.description,
												'min_val': op4_dimen_item.min_val,
												'max_val': op4_dimen_item.max_val,
												'remark': op4_dimen_item.remark,
												
												}
											
											op4_ms_dimension_id = ms_dimension_obj.create(cr, uid,op4_dimen_vals)
											
											
									if pos_line_item.operation_id.name == 'Operation 5':
										
										for op5_dimen_item in pos_line_item.line_ids:
											
											op5_dimen_vals = {
												
												'header_id': ms_operation_id,
												'position_id': pos_line_item.header_id.id,
												'operation_id': pos_line_item.operation_id.id,
												'operation_name': pos_line_item.operation_id.name,
												'position_line': op5_dimen_item.header_id.id,
												'pos_dimension_id': op5_dimen_item.id,
												'dimension_id': op5_dimen_item.dimension_id.id,
												#~ 'clamping_area': op2_dimen_item.clamping_area,
												'description': op5_dimen_item.description,
												'min_val': op5_dimen_item.min_val,
												'max_val': op5_dimen_item.max_val,
												'remark': op5_dimen_item.remark,
												
												}
											
											op5_ms_dimension_id = ms_dimension_obj.create(cr, uid,op5_dimen_vals)
											
											
									if pos_line_item.operation_id.name == 'Operation 6':
										
										for op6_dimen_item in pos_line_item.line_ids:
											
											op6_dimen_vals = {
												
												'header_id': ms_operation_id,
												'position_id': pos_line_item.header_id.id,
												'operation_id': pos_line_item.operation_id.id,
												'operation_name': pos_line_item.operation_id.name,
												'position_line': op6_dimen_item.header_id.id,
												'pos_dimension_id': op6_dimen_item.id,
												'dimension_id': op6_dimen_item.dimension_id.id,
												#~ 'clamping_area': op2_dimen_item.clamping_area,
												'description': op6_dimen_item.description,
												'min_val': op6_dimen_item.min_val,
												'max_val': op6_dimen_item.max_val,
												'remark': op6_dimen_item.remark,
												
												}
											
											op6_ms_dimension_id = ms_dimension_obj.create(cr, uid,op6_dimen_vals)
											
											
									if pos_line_item.operation_id.name == 'Operation 7':
										
										for op7_dimen_item in pos_line_item.line_ids:
											
											op7_dimen_vals = {
												
												'header_id': ms_operation_id,
												'position_id': pos_line_item.header_id.id,
												'operation_id': pos_line_item.operation_id.id,
												'operation_name': pos_line_item.operation_id.name,
												'position_line': op7_dimen_item.header_id.id,
												'pos_dimension_id': op7_dimen_item.id,
												'dimension_id': op7_dimen_item.dimension_id.id,
												#~ 'clamping_area': op2_dimen_item.clamping_area,
												'description': op7_dimen_item.description,
												'min_val': op7_dimen_item.min_val,
												'max_val': op7_dimen_item.max_val,
												'remark': op7_dimen_item.remark,
												
												}
											
											op7_ms_dimension_id = ms_dimension_obj.create(cr, uid,op7_dimen_vals)
											
											
									if pos_line_item.operation_id.name == 'Operation 8':
										
										for op8_dimen_item in pos_line_item.line_ids:
											
											op8_dimen_vals = {
												
												'header_id': ms_operation_id,
												'position_id': pos_line_item.header_id.id,
												'operation_id': pos_line_item.operation_id.id,
												'operation_name': pos_line_item.operation_id.name,
												'position_line': op8_dimen_item.header_id.id,
												'pos_dimension_id': op8_dimen_item.id,
												'dimension_id': op8_dimen_item.dimension_id.id,
												#~ 'clamping_area': op2_dimen_item.clamping_area,
												'description': op8_dimen_item.description,
												'min_val': op8_dimen_item.min_val,
												'max_val': op8_dimen_item.max_val,
												'remark': op8_dimen_item.remark,
												
												}
											
											op8_ms_dimension_id = ms_dimension_obj.create(cr, uid,op8_dimen_vals)
											
											
									if pos_line_item.operation_id.name == 'Operation 9':
										
										for op9_dimen_item in pos_line_item.line_ids:
											
											op9_dimen_vals = {
												
												'header_id': ms_operation_id,
												'position_id': pos_line_item.header_id.id,
												'operation_id': pos_line_item.operation_id.id,
												'operation_name': pos_line_item.operation_id.name,
												'position_line': op9_dimen_item.header_id.id,
												'pos_dimension_id': op9_dimen_item.id,
												'dimension_id': op9_dimen_item.dimension_id.id,
												#~ 'clamping_area': op2_dimen_item.clamping_area,
												'description': op9_dimen_item.description,
												'min_val': op9_dimen_item.min_val,
												'max_val': op9_dimen_item.max_val,
												'remark': op9_dimen_item.remark,
												
												}
											
											op9_ms_dimension_id = ms_dimension_obj.create(cr, uid,op9_dimen_vals)
											
											
									if pos_line_item.operation_id.name == 'Operation 10':
										
										for op10_dimen_item in pos_line_item.line_ids:
											
											op10_dimen_vals = {
												
												'header_id': ms_operation_id,
												'position_id': pos_line_item.header_id.id,
												'operation_id': pos_line_item.operation_id.id,
												'operation_name': pos_line_item.operation_id.name,
												'position_line': op10_dimen_item.header_id.id,
												'pos_dimension_id': op10_dimen_item.id,
												'dimension_id': op10_dimen_item.dimension_id.id,
												#~ 'clamping_area': op2_dimen_item.clamping_area,
												'description': op10_dimen_item.description,
												'min_val': op10_dimen_item.min_val,
												'max_val': op10_dimen_item.max_val,
												'remark': op10_dimen_item.remark,
												
												}
											
											op10_ms_dimension_id = ms_dimension_obj.create(cr, uid,op10_dimen_vals)
											
											
									if pos_line_item.operation_id.name == 'Operation 11':
										
										for op11_dimen_item in pos_line_item.line_ids:
											
											op11_dimen_vals = {
												
												'header_id': ms_operation_id,
												'position_id': pos_line_item.header_id.id,
												'operation_id': pos_line_item.operation_id.id,
												'operation_name': pos_line_item.operation_id.name,
												'position_line': op11_dimen_item.header_id.id,
												'pos_dimension_id': op11_dimen_item.id,
												'dimension_id': op11_dimen_item.dimension_id.id,
												#~ 'clamping_area': op2_dimen_item.clamping_area,
												'description': op11_dimen_item.description,
												'min_val': op11_dimen_item.min_val,
												'max_val': op11_dimen_item.max_val,
												'remark': op11_dimen_item.remark,
												
												}
											
											op11_ms_dimension_id = ms_dimension_obj.create(cr, uid,op11_dimen_vals)
											
											
									if pos_line_item.operation_id.name == 'Operation 12':
										
										for op12_dimen_item in pos_line_item.line_ids:
											
											op12_dimen_vals = {
												
												'header_id': ms_operation_id,
												'position_id': pos_line_item.header_id.id,
												'operation_id': pos_line_item.operation_id.id,
												'operation_name': pos_line_item.operation_id.name,
												'position_line': op12_dimen_item.header_id.id,
												'pos_dimension_id': op12_dimen_item.id,
												'dimension_id': op12_dimen_item.dimension_id.id,
												#~ 'clamping_area': op2_dimen_item.clamping_area,
												'description': op12_dimen_item.description,
												'min_val': op12_dimen_item.min_val,
												'max_val': op12_dimen_item.max_val,
												'remark': op12_dimen_item.remark,
												
												}
											
											op12_ms_dimension_id = ms_dimension_obj.create(cr, uid,op12_dimen_vals)
							
							for i in entry.line_ids:
								
								s = [(6, 0, [x.id for x in i.com_operation_id])]
								ss = [x.id for x in i.com_operation_id]
								print"ssssssssssssssss",s
								print"ssssssssssssssss",ss
								for x in ss:
									print"xxxxxxxxxxxx",x
									op_rec = self.pool.get('ch.kg.position.number').browse(cr,uid,x)
									op_name = op_rec.name
									print"op_nameop_nameop_nameop_name",op_name
									print"ms_operation_idms_operation_id",ms_operation_id
									ms_op_id = []
									ms_op_id.append(ms_operation_id);
									#~ ms_op_id= list[ms_operation_id]
									print"ms_op_id",ms_op_id
									
									if op_name == 'Operation 1':
											self.pool.get('kg.ms.operations').operation1_update(cr, uid, ms_op_id)	
									if op_name == 'Operation 2':
											self.pool.get('kg.ms.operations').operation2_update(cr, uid, ms_op_id)	
									if op_name == 'Operation 3':
											self.pool.get('kg.ms.operations').operation3_update(cr, uid, ms_op_id)
									if op_name == 'Operation 4':
											self.pool.get('kg.ms.operations').operation4_update(cr, uid, ms_op_id)
									if op_name == 'Operation 5':
											self.pool.get('kg.ms.operations').operation5_update(cr, uid, ms_op_id)
									if op_name == 'Operation 6':
											self.pool.get('kg.ms.operations').operation6_update(cr, uid, ms_op_id)											
									if op_name == 'Operation 7':
											self.pool.get('kg.ms.operations').operation7_update(cr, uid, ms_op_id)
									if op_name == 'Operation 8':
											self.pool.get('kg.ms.operations').operation8_update(cr, uid, ms_op_id)
									if op_name == 'Operation 9':
											self.pool.get('kg.ms.operations').operation9_update(cr, uid, ms_op_id)
									if op_name == 'Operation 10':
											self.pool.get('kg.ms.operations').operation10_update(cr, uid, ms_op_id)
									if op_name == 'Operation 11':
											self.pool.get('kg.ms.operations').operation11_update(cr, uid, ms_op_id)
									if op_name == 'Operation 12':
											self.pool.get('kg.ms.operations').operation12_update(cr, uid, ms_op_id)											
											
				if total > 0:							
					for operation in range(total):								
						ms_store_vals = {
							'operation_id': 170,
							'production_id': line_item.production_id.id,
							'foundry_assembly_id': line_item.production_id.assembly_id,
							'foundry_assembly_line_id': line_item.production_id.assembly_line_id,
							'ms_assembly_id': line_item.ms_id.assembly_id,
							'ms_assembly_line_id': line_item.ms_id.assembly_line_id,
							'qty': 1,
						}
						ms_store_id = self.pool.get('kg.ms.stores').create(cr, uid, ms_store_vals)
	
		for line_item in entry.line_ids:				
			if line_item.qty < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative values !!'))
							
			if line_item.qty == 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save Zero values !!'))	
			
							
			if line_item.qty > line_item.sc_dc_line_id.qty:
				raise osv.except_osv(_('Warning!'),
							_('Check the Qty !!! '))	
							
								
								
			if (line_item.sc_dc_line_id.sc_in_qty + line_item.qty) == line_item.sc_dc_line_id.qty:
				inward_state = 'done'
			if (line_item.sc_dc_line_id.sc_in_qty + line_item.qty) < line_item.sc_dc_line_id.qty:
				inward_state = 'partial'			
			
			self.pool.get('ch.subcontract.inward.line').write(cr,uid,line_item.id,{'pending_qty':line_item.qty})							
			sc_dc_line_obj.write(cr, uid, line_item.sc_dc_line_id.id, 
						{'sc_in_qty': line_item.sc_dc_line_id.sc_in_qty + line_item.qty,'state': inward_state,'pending_qty':line_item.sc_dc_line_id.pending_qty - line_item.qty})				
			
			sc_obj.write(cr, uid, line_item.sc_id.id, 
				{'sc_inward_qty':line_item.sc_id.sc_inward_qty + line_item.qty})
											
		
		sc_inward_name = ''	
		sc_inward_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.inward')])
		rec = self.pool.get('ir.sequence').browse(cr,uid,sc_inward_seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s','%s') """%(sc_inward_seq_id[0],rec.code,entry.entry_date))
		sc_inward_name = cr.fetchone();
							
		self.write(cr, uid, ids, {'state': 'confirmed','name':sc_inward_name[0]})
							
							
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state not in ('draft'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)	
	
		
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
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
		
	   ]
	
	
	
kg_subcontract_inward()




class ch_subcontract_inward_line(osv.osv):
	
	_name = "ch.subcontract.inward.line"
	_description = "Subcontract Inward Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.subcontract.inward','Header Id'),
		
		'contractor_id': fields.related('header_id','contractor_id', type='many2one', relation='res.partner', string='Contractor Name', store=True, readonly=True),
		'inward_no': fields.related('header_id','name', type='char', string='Inward No', store=True, readonly=True),
		
		'sc_id': fields.many2one('kg.subcontract.process','Subcontractor List Id'),
		'sc_dc_line_id': fields.many2one('ch.subcontract.dc.line','Subcontractor dc List Id'),
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
		
		'operation_id': fields.many2many('ch.kg.position.number', 'm2m_inward_operation_details', 'in_operation_id', 'in_sub_id','Operation', domain="[('header_id','=',position_id)]"),
		'com_operation_id': fields.many2many('ch.kg.position.number', 'm2m_in_com_operation_details', 'in_com_operation_id', 'in_com_sub_id','Completed Operation', domain="[('header_id','=',position_id)]"),
		'actual_qty': fields.integer('Actual Qty',readonly=True),
		'qty': fields.integer('Quantity'),
		'sc_dc_qty': fields.integer('Quantity'),
		'pending_qty': fields.integer('Pending Qty'),
		'sc_invoice_qty': fields.integer('Invoice Qty'),
		
		'each_weight': fields.float('Each Weight'),
		'totel_weight': fields.float('Total weight'),
		'com_weight': fields.float('Completed weight'),
				
		'remarks': fields.text('Remarks'),
		'state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')],'Status', readonly=True),
		
		
	}
	
	_defaults = {
		
		'state': 'pending',
		
		
	}
	def onchange_com_weight(self, cr, uid, ids, com_weight,qty):				
		total_weight = qty * com_weight
		return {'value': {'totel_weight': total_weight}}


ch_subcontract_inward_line()





class kg_subcontract_advance(osv.osv):

	_name = "kg.subcontract.advance"
	_description = "Subcontract Advance"
	_order = "entry_date desc"		
		
	_columns = {

	
		'name': fields.char('Advance No.', size=128,select=True,readonly=True),
		'entry_date': fields.date('Advance Date',required=True),		
		'active': fields.boolean('Active'),		
		'contractor_id': fields.many2one('res.partner','Sub Contractor',required=True,),				
		
			
		'wo_ids': fields.many2many('kg.subcontract.wo','m2m_sub_wo_details' , 'order_id', 'wo_id', 'WO Items',
			domain="[('contractor_id','=',contractor_id), '&', ('state','!=','draft')]",required=True),
		'total_amt': fields.float('Total WO Amount'),
		'advance_amt': fields.float('Advance Amount'),		
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
				
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_subcontract_advance', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),		
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,				
		'state': 'draft',		
	}
	
	
	
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])		
		wo_value = 0.00
		if len(entry.wo_ids) == 0:
			raise osv.except_osv(_('Warning!'),
							_('System not allow to without line items !!'))
		for item in entry.wo_ids:			
			wo_rec = self.pool.get('kg.subcontract.wo').browse(cr,uid,item.id)			
			wo_value += wo_rec.wo_value
			
		
		if entry.advance_amt > wo_value:
			raise osv.except_osv(_('Advance Amount!'),
							_('Advance Amount Should not be greater than Work Order Amount!!'))
		
		
		
		
				
		sc_advance_name = ''	
		sc_advance_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.inward')])
		rec = self.pool.get('ir.sequence').browse(cr,uid,sc_advance_seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s','%s') """%(sc_advance_seq_id[0],rec.code,entry.entry_date))
		sc_advance_name = cr.fetchone();
							
		self.write(cr, uid, ids, {'state': 'confirmed','name':sc_advance_name[0],'total_amt':wo_value})
							
							
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state not in ('draft'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)	
	
		
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
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['Advance Date']),
		
	   ]
	
	
kg_subcontract_advance()







class kg_subcontract_invoice(osv.osv):

	_name = "kg.subcontract.invoice"
	_description = "Subcontract Invoice"
	_order = "entry_date desc"		
		
	_columns = {

	
		'name': fields.char('Invoice No.', size=128,select=True,readonly=True),
		'entry_date': fields.date('Invoice Date',required=True),		
		'active': fields.boolean('Active'),	
		'contractor_id': fields.many2one('res.partner','Subcontractor',required=True),
		'inward_id': fields.many2one('kg.subcontract.inward','Inward No.',required=True),
		'phone': fields.char('Phone',size=64),
		'contact_person': fields.char('Contact Person', size=128),
				
		'inward_subcontract_line_ids': fields.many2many('ch.subcontract.inward.line','m2m_invoice_details' , 'order_id', 'sc_id', 'SC Items',
			domain="[('state','in',('pending','partial')),('contractor_id','=',contractor_id),('header_id','=',inward_id)]"),		 
		 			
		'line_ids': fields.one2many('ch.subcontract.invoice.line','header_id','Subcontract Invoice Line'),   
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'flag_invoice': fields.boolean('Flag Invoice'),		
		
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
				
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_subcontract_inward', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),		
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'flag_invoice': False,	
		'state': 'draft',		
	}
	
	def onchange_contractor(self, cr, uid, ids, contractor_id):
		if contractor_id:
			contractor_rec = self.pool.get('res.partner').browse(cr, uid, contractor_id)
		return {'value': {'contact_person':contractor_rec.contact_person,'phone':contractor_rec.phone  }}
	
	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		invoice_line_obj = self.pool.get('ch.subcontract.invoice.line')
			
		del_sql = """ delete from ch_subcontract_invoice_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		for item in entry.inward_subcontract_line_ids:			
			
			
			vals = {
			
				'header_id': entry.id,
				'sc_id':item.sc_id.id,
				'qty':item.pending_qty,								
				'actual_qty':item.actual_qty,		
				'com_weight':item.com_weight,					
				'sc_inward_line_id':item.id,	
				'operation_id':[(6, 0, [x.id for x in item.com_operation_id])],
				
			}
			
			in_line_id = invoice_line_obj.create(cr, uid,vals)		
			
			
		self.write(cr, uid, ids, {'flag_invoice': True})
		
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])	
		sc_inward_line_obj = self.pool.get('ch.subcontract.inward.line')
		if len(entry.line_ids) == 0:
			raise osv.except_osv(_('Warning!'),
							_('System not allow to without line items !!'))
		for line_item in entry.line_ids:				
			if line_item.qty < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative values !!'))
							
			if line_item.qty == 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save Zero values !!'))	
			
			if (line_item.sc_inward_line_id.sc_invoice_qty + line_item.qty) > line_item.sc_inward_line_id.qty:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to invoice Qty Exceed !!'))						
								
								
			if (line_item.sc_inward_line_id.sc_invoice_qty + line_item.qty) == line_item.sc_inward_line_id.qty:
				invoice_state = 'done'
			if (line_item.sc_inward_line_id.sc_invoice_qty + line_item.qty) < line_item.sc_inward_line_id.qty:
				invoice_state = 'partial'			
			
									
			sc_inward_line_obj.write(cr, uid, line_item.sc_inward_line_id.id, 
						{'sc_invoice_qty': line_item.sc_inward_line_id.sc_invoice_qty + line_item.qty,'state': invoice_state,'pending_qty':line_item.sc_inward_line_id.pending_qty - line_item.qty})				
			
			
											
		
		sc_invoice_name = ''	
		sc_invoice_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.invoice')])
		rec = self.pool.get('ir.sequence').browse(cr,uid,sc_invoice_seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s','%s') """%(sc_invoice_seq_id[0],rec.code,entry.entry_date))
		sc_invoice_name = cr.fetchone();
							
		self.write(cr, uid, ids, {'state': 'confirmed','name':sc_invoice_name[0]})
							
							
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state not in ('draft'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)	
	
		
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
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),		
	   ]	
	
kg_subcontract_invoice()




class ch_subcontract_invoice_line(osv.osv):
	
	_name = "ch.subcontract.invoice.line"
	_description = "Subcontract Invoice Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.subcontract.invoice','Header Id'),
		'sc_id': fields.many2one('kg.subcontract.process','Subcontractor List Id'),
		'sc_inward_line_id': fields.many2one('ch.subcontract.inward.line','Subcontractor Inward List Id'),
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
		
		'operation_id': fields.many2many('ch.kg.position.number', 'm2m_invoice_operation_details', 'in_operation_id', 'in_sub_id','Operation', domain="[('header_id','=',position_id)]"),
		
		'actual_qty': fields.integer('Actual Qty',readonly=True),
		'qty': fields.integer('Quantity'),
		'value': fields.float('Unit Price'),
		'total_value': fields.float('Total Value'),	
		'com_weight': fields.float('Completed weight'),
		
				
		'remarks': fields.text('Remarks'),
		'state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')],'Status', readonly=True),
		
		
	}
	
	_defaults = {
		
		'state': 'pending',
		
		
	}
	
	def onchange_total_value(self, cr, uid, ids, qty,value):
		if qty:			
			total_value = qty * value
		return {'value': {'total_value': total_value}}


ch_subcontract_invoice_line()
	







