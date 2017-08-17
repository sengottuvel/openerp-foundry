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
   ('2','Break down'),
   ('3','Emergency'),
   ('4','Service'),
   ('5','FDY-NC'),
   ('6','Spare'),
   ('7','Urgent'),
   ('8','Normal'),
  
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
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location',domain="[('state','=','approved')]"),
		'active': fields.boolean('Active'),
		'contractor_id': fields.many2one('res.partner','Contractor Name',required=True,domain="[('contractor','=','t'),('partner_state','=','approve')]"),
		
		'ms_plan_id': fields.many2one('kg.ms.daily.planning','Planning Id'),
		'ms_plan_line_id': fields.many2one('ch.ms.daily.planning.details','Planning Line Id'),
		'ms_id': fields.related('ms_plan_line_id','ms_id', type='many2one', relation='kg.machineshop', string='MS Id', store=True, readonly=True),
		'production_id': fields.related('ms_id','production_id', type='many2one', relation='kg.production', string='Production No.', store=True, readonly=True),
		'position_id': fields.related('ms_plan_line_id','position_id', type='many2one', relation='kg.position.number', string='Position No.', store=True, readonly=True),
		'order_id': fields.related('ms_plan_line_id','order_id', type='many2one', relation='kg.work.order', string='Work Order', store=True, readonly=True),
		'order_line_id': fields.related('ms_plan_line_id','order_line_id', type='many2one', relation='ch.work.order.details', string='Order Line', store=True, readonly=True),
		'order_no': fields.related('ms_plan_line_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'oth_spec': fields.related('ms_plan_line_id','oth_spec', type='text', string='WO Remarks', store=True, readonly=True),
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
		
		'operation_id': fields.many2one('kg.operation.master','Operation Name'), 	
		
		'actual_qty': fields.integer('Schedule Qty'),		
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
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
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
		'contractor_id': fields.many2one('res.partner','Subcontractor',domain="[('contractor','=','t'),('partner_state','=','approve')]"),
		'contact_person': fields.char('Contact Person', size=128),	  
		'phone': fields.char('Phone',size=64),
		'delivery_date': fields.date('Expected Delivery Date'),
		'wo_value': fields.function(_get_order_value, string='Sub Contractor WO Value', method=True, store=True, type='float'),
		'billing_type': fields.selection([('applicable','Applicable'),('not_applicable','Not Applicable')],'Billing Type'),
		'sc_line_ids': fields.many2many('kg.subcontract.process','m2m_sc_details' , 'order_id', 'sc_id', 'SC Items',
			domain="[('wo_state','in',('pending','partial')),('wo_process_state','=','allow')]"),
		'line_ids': fields.one2many('ch.subcontract.wo.line','header_id','Subcontract WO Line'),   
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('approved','Approved'),('approved_dc','Approved & DC'),('cancel','Cancelled')],'Status', readonly=True),
		'flag_order': fields.boolean('Flag Order'),
		'flag_spl_app': fields.boolean('Special Approvel'),
		'flag_app': fields.boolean('Approvel'),
		
		
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
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'billing_type': 'applicable',
		'division_id':_get_default_division,
		'flag_order': False,
		'flag_spl_app': False,
		'flag_app': False,
		'state': 'draft'
		
	}
	
	def onchange_contractor(self, cr, uid, ids, contractor_id):
		if contractor_id:
			contractor_rec = self.pool.get('res.partner').browse(cr, uid, contractor_id)
			contact_person = contractor_rec.contact_person
			phone = contractor_rec.phone
		else:
			contact_person = ''
			phone = ''
		return {'value': {'contact_person':contact_person,'phone':phone  }}
	
	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		wo_line_obj = self.pool.get('ch.subcontract.wo.line')
		wo_line_del_obj = self.pool.get('ch.wo.operation.details')
		sc_obj = self.pool.get('kg.subcontract.process')
		
		del_sql = """ delete from ch_subcontract_wo_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)		
		
		if entry.sc_line_ids:		
			for item in entry.sc_line_ids:	
			
				if item.ms_op_id:
					vals = {								
						'header_id': entry.id,
						'sc_id':item.id,
						'entry_type':'direct',
						'order_id':item.order_id.id,
						'order_line_id':item.order_line_id.id,
						'moc_id':item.moc_id.id,
						'position_id':item.position_id.id,
						'pump_model_id':item.pump_model_id.id,
						'pattern_id':item.pattern_id.id,						
						'item_code':item.item_code,
						'item_name':item.item_name,
						'qty':item.pending_qty ,
						'actual_qty':item.actual_qty,
						'dc_qty':item.pending_qty,
						'dc_qty':item.pending_qty,
						'read_flag':True,
											
					}
				else:
					vals = {								
						'header_id': entry.id,
						'sc_id':item.id,
						'entry_type':'direct',
						'order_id':item.order_id.id,
						'order_line_id':item.order_line_id.id,
						'moc_id':item.moc_id.id,
						'position_id':item.position_id.id,
						'pump_model_id':item.pump_model_id.id,
						'pattern_id':item.pattern_id.id,						
						'item_code':item.item_code,
						'item_name':item.item_name,
						'qty':item.pending_qty ,
						'actual_qty':item.actual_qty,
						'dc_qty':item.pending_qty,
											
					}
				
				
				wo_line_id = wo_line_obj.create(cr, uid,vals)
				
				if item.ms_op_id:					
					pos_id = self.pool.get('ch.kg.position.number').search(cr, uid, [('header_id','=',item.position_id.id),('operation_id','=',item.operation_id.id)])					
					pos_rec = self.pool.get('ch.kg.position.number').browse(cr,uid,pos_id[0])
					moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,item.moc_id.id)						
					if moc_rec.moc_cate_id.id == False:
						raise osv.except_osv(_('MOC Master Configure!!'),
										_('Please mapping in Moc Category in MOC Master!!'))
					cr.execute('''select line.rate from ch_kg_position_number as header
									left join ch_moccategory_mapping line on line.header_id = header.id
									where header.header_id = %s and header.operation_id = %s and line.moc_cate_id = %s
											  ''',[item.position_id.id,item.operation_id.id,moc_rec.moc_cate_id.id])
					operation_rate= cr.fetchone()				
					if operation_rate is not None:
						if operation_rate[0]:
							operation_rate = operation_rate[0]				
						else:
							raise osv.except_osv(_('MOC Category Details Configure!!'),
										_('Please mapping in Moc Category in Rate!!'))				
					else:
						raise osv.except_osv(_('MOC Category Details Configure!!'),
										_('Please mapping in Moc Category in Rate!!'))						
					
					vals = {	
												
						'header_id': wo_line_id,
						'position_id':item.position_id.id,
						'moc_id':item.moc_id.id ,
						'operation_id':pos_rec.id,
						'stage_id':pos_rec.stage_id.id,				
						'op_rate':operation_rate,	
						'flag_read':True,			
								
										
									
					}	
					
					wo_line_del_id = wo_line_del_obj.create(cr, uid,vals)
				
				sc_obj.write(cr, uid, item.id, {'wo_process_state': 'not_allow'})
				
			self.write(cr, uid, ids, {'flag_order': True})
			
		return True
		
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])		
		if entry.state == 'draft':
			if not entry.line_ids:
				raise osv.except_osv(_('Line Item Details !!'),
				_('Enter the Work Order Details !!'))		
			if entry.line_ids:
				for line in entry.line_ids:	
					if line.entry_type == 'manual':											
						if line.pattern_id.id == False and line.ms_shop_id.id == False:
							raise osv.except_osv(_('Pattern or MS item must required'),
							_('Kindly verify Pattern Number and MS Item Name!!'))						
						
					if line.entry_type == 'direct':
						print"line.sc_id.sc_wo_qty",line.sc_id.sc_wo_qty
						print"line.qty",line.qty
						print"line.qty",line.qty												
						
						if (line.sc_id.sc_wo_qty + line.qty) > line.actual_qty:
							raise osv.except_osv(_('Excess Qty Not Allowed'),
							_('Kindly verify Excess Qty!!'))	
												
						if (line.sc_id.sc_wo_qty + line.qty) > line.actual_qty:
							raise osv.except_osv(_('Excess Qty Not Allowed'),
							_('Kindly verify Excess Qty!!'))					
					if not line.line_ids:
						raise osv.except_osv(_('Tab Name - Work Order Operation Details'),
							_('Enter the Work Order Operation Details !!'))					
					for op_line in line.line_ids:
						moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,op_line.moc_id.id)
						oper_id_rec = self.pool.get('ch.kg.position.number').browse(cr,uid,op_line.operation_id.id)
						if moc_rec.moc_cate_id.id == False:
							raise osv.except_osv(_('MOC Master Configure!!'),
							_('Please mapping in Moc Category in MOC Master!!'))											
						cr.execute('''select line.rate from ch_kg_position_number as header
										left join ch_moccategory_mapping line on line.header_id = header.id
										where header.header_id = %s and header.operation_id = %s and line.moc_cate_id = %s
												  ''',[op_line.position_id.id,oper_id_rec.operation_id.id,moc_rec.moc_cate_id.id])
						operation_rate= cr.fetchone()
						print"operation_rate",operation_rate					
													
						if operation_rate is not None:
							if operation_rate[0] < op_line.op_rate:
								self.write(cr, uid, ids, {'flag_spl_app': True,'flag_app':True})							
							else:
								pass
						else:
							self.write(cr, uid, ids, {'flag_spl_app': True,'flag_app':True})
							
							line = self.pool.get('ch.moccategory.mapping').create(cr,uid,{
							   'header_id':oper_id_rec.id,
							   'moc_cate_id':moc_rec.moc_cate_id.id,
							   'rate':op_line.op_rate,						 
							  })			
			
			
			sc_wo_name = ''	
			sc_wo_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.wo')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,sc_wo_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(sc_wo_seq_id[0],rec.code,entry.entry_date))
			sc_wo_name = cr.fetchone();
								
			self.write(cr, uid, ids, {'state': 'confirmed','name':sc_wo_name[0]})		
							
		return True
		
	def entry_approve(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'confirmed':			
			sc_obj = self.pool.get('kg.subcontract.process')
			if entry.line_ids:
				for line in entry.line_ids:
					if line.entry_type == 'manual':											
						if line.pattern_id.id == False and line.ms_shop_id.id == False:
							raise osv.except_osv(_('Pattern or MS item must required'),
							_('Kindly verify Pattern Number and MS Item Name!!'))	
					if line.entry_type == 'direct':
						if (line.sc_id.sc_wo_qty + line.qty) > line.qty:
								raise osv.except_osv(_('Excess Qty Not Allowed'),
								_('Kindly verify Excess Qty!!'))
					for op_line in line.line_ids:
						moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,op_line.moc_id.id)
						oper_id_rec = self.pool.get('ch.kg.position.number').browse(cr,uid,op_line.operation_id.id)									
						cr.execute('''select line.rate from ch_kg_position_number as header
										left join ch_moccategory_mapping line on line.header_id = header.id
										where header.header_id = %s and header.operation_id = %s and line.moc_cate_id = %s
												  ''',[op_line.position_id.id,oper_id_rec.operation_id.id,moc_rec.moc_cate_id.id])
						operation_rate= cr.fetchone()					
						if operation_rate is not None:
							if operation_rate[0] < op_line.op_rate:						
								for oper in oper_id_rec.line_ids_a:
									self.pool.get('ch.moccategory.mapping').write(cr,uid,oper.id,{'rate':op_line.op_rate})																					
							else:
								pass
						else:
							pass	
						
			if len(entry.line_ids) == 0:
				raise osv.except_osv(_('Warning!'),
								_('System not allow to without line items !!'))
			
			for line_item in entry.line_ids:
				
				if line_item.qty < 0 and line_item.rate < 0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative values !!'))
											
				if line_item.qty == 0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save Zero values !!'))				
				
				wo_state = ''	
				wo_process_state = ''
				direct_sc_wo_qty = 0.00		
				direct_pending_qty = 0.00		
				if line_item.entry_type == 'direct':
					if (line_item.sc_id.sc_wo_qty + line_item.qty) == line_item.sc_id.total_qty:
						wo_state = 'done'
						wo_process_state = 'not_allow'
					if (line_item.sc_id.sc_wo_qty + line_item.qty) < line_item.sc_id.total_qty:
						wo_state = 'partial'
						wo_process_state = 'allow'
					if (line_item.sc_id.sc_wo_qty + line_item.qty) > line_item.sc_id.total_qty:
						wo_state = 'done'
						wo_process_state = 'not_allow'
						
					direct_sc_wo_qty = line_item.sc_id.sc_wo_qty + line_item.qty
					direct_pending_qty = line_item.sc_id.pending_qty - line_item.qty	
					
				self.pool.get('ch.subcontract.wo.line').write(cr,uid,line_item.id,{'pending_qty':line_item.qty,'app_flag':True})
				sc_obj.write(cr, uid, line_item.sc_id.id, 
					{'pending_qty':direct_pending_qty,'sc_wo_qty': direct_sc_wo_qty,'wo_state': wo_state,'wo_process_state':wo_process_state,'state':'wo_inprocess'})
								
			
								
			self.write(cr, uid, ids, {'state': 'approved','flag_app':False})		
							
		return True
		
	def approve_dc(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'confirmed':			
			sc_obj = self.pool.get('kg.subcontract.process')
			dc_obj = self.pool.get('kg.subcontract.dc')
			dc_obj_line = self.pool.get('ch.subcontract.dc.line')		
			dc_id = dc_obj.create(cr,uid,{'sub_wo_no':entry.name,'transfer_type':'sub_contractor','contractor_id':entry.contractor_id.id,'flag_dc':True,'entry_mode': 'from_wo'})	
			if entry.line_ids:
				for line in entry.line_ids:	
					if line.entry_type == 'manual':											
						if line.pattern_id.id == False and line.ms_shop_id.id == False:
							raise osv.except_osv(_('Pattern or MS item must required'),
							_('Kindly verify Pattern Number and MS Item Name!!'))
					if line.entry_type == 'direct':
						if (line.sc_id.sc_wo_qty + line.qty) > line.qty:
								raise osv.except_osv(_('Excess Qty Not Allowed'),
								_('Kindly verify Excess Qty!!'))
					for op_line in line.line_ids:
						moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,op_line.moc_id.id)
						oper_id_rec = self.pool.get('ch.kg.position.number').browse(cr,uid,op_line.operation_id.id)									
						cr.execute('''select line.rate from ch_kg_position_number as header
										left join ch_moccategory_mapping line on line.header_id = header.id
										where header.header_id = %s and header.operation_id = %s and line.moc_cate_id = %s
												  ''',[op_line.position_id.id,oper_id_rec.operation_id.id,moc_rec.moc_cate_id.id])
						operation_rate= cr.fetchone()					
						if operation_rate is not None:
							if operation_rate[0] < op_line.op_rate:						
								for oper in oper_id_rec.line_ids_a:
									self.pool.get('ch.moccategory.mapping').write(cr,uid,oper.id,{'rate':op_line.op_rate})																					
							else:
								pass
						else:
							pass
			if len(entry.line_ids) == 0:
				raise osv.except_osv(_('Warning!'),
								_('System not allow to without line items !!'))
			for line_item in entry.line_ids:
				print"line_itemline_itemline_item",line_item.line_ids		
					
						
				dc_line = dc_obj_line.create(cr,uid,{'header_id':dc_id,'sc_id':line_item.sc_id.id,'qty':line_item.qty,'sc_dc_qty':line_item.qty,'sc_wo_qty':line_item.qty,					
						'entry_type_stk':line_item.entry_type,'order_id':line_item.order_id.id,'moc_id':line_item.moc_id.id,'position_id':line_item.position_id.id,'order_line_id':line_item.order_line_id.id,
						'pump_model_id':line_item.pump_model_id.id,'pattern_id':line_item.pattern_id.id,'ms_shop_id':line_item.ms_shop_id.id,'pattern_code':line_item.pattern_code,'pattern_name':line_item.pattern_name,
						'item_code':line_item.item_code,'item_name':line_item.item_name,			
						'actual_qty':line_item.actual_qty,'sc_wo_line_id': line_item.id,'entry_mode': 'from_wo','pending_qty':line_item.qty})		
				for line in line_item.line_ids:	
					print"line.operation_id.id",line.operation_id.id
					print"dc_line.id",dc_line
					sql = """ insert into m2m_dc_operation_details (dc_operation_id,dc_sub_id) VALUES(%s,%s) """ %(dc_line,line.operation_id.id)
					cr.execute(sql)

				
				
				if line_item.qty < 0 and line_item.rate < 0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative values !!'))				
								
				if line_item.qty == 0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save Zero values !!'))
				wo_state = ''	
				wo_process_state = ''
				direct_sc_wo_qty = 0.00		
				direct_pending_qty = 0.00		
				if line_item.entry_type == 'direct':
					if (line_item.sc_id.sc_wo_qty + line_item.qty) == line_item.sc_id.total_qty:
						wo_state = 'done'
						wo_process_state = 'not_allow'
					if (line_item.sc_id.sc_wo_qty + line_item.qty) < line_item.sc_id.total_qty:
						wo_state = 'partial'
						wo_process_state = 'allow'
					if (line_item.sc_id.sc_wo_qty + line_item.qty) > line_item.sc_id.total_qty:
						wo_state = 'done'
						wo_process_state = 'not_allow'
						
					direct_sc_wo_qty = line_item.sc_id.sc_wo_qty + line_item.qty
					direct_pending_qty = line_item.sc_id.pending_qty - line_item.qty
				
				self.pool.get('ch.subcontract.wo.line').write(cr,uid,line_item.id,{'dc_flag':True,'pending_qty':line_item.qty})
				sc_obj.write(cr, uid, line_item.sc_id.id, 
					{'pending_qty':direct_pending_qty,'sc_wo_qty': direct_sc_wo_qty,'wo_state': wo_state,'wo_process_state':wo_process_state})
								
			
								
			self.write(cr, uid, ids, {'state': 'approved_dc','flag_app':False})
							
							
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
		
	def _future_delivery_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')		
		delivery_date = rec.delivery_date
		delivery_date = str(delivery_date)
		delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d')		
		if delivery_date < today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['Entry Date']),
		(_future_delivery_date_check, 'System not allow to save with Past date. !!',['Expected Delivery Date']),
		
	   ]
	
	
	
kg_subcontract_wo()



class ch_subcontract_wo_line(osv.osv):
	
	_name = "ch.subcontract.wo.line"
	_description = "Subcontract WO Line"
	
	
	def _get_oper_value(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		total_value = 0.00
		value = 0.00
		for entry in self.browse(cr, uid, ids, context=context):
			for line in entry.line_ids:
				print"entry.qty",entry.qty
				print"line.op_rate",line.op_rate
				total_value= entry.qty * line.op_rate				
				value += total_value
			print"total_value",value
			result[entry.id] = value
		return result
	
	_columns = {
		
		'header_id': fields.many2one('kg.subcontract.wo','Header Id'),
		'contractor_id': fields.related('header_id','contractor_id', type='many2one', relation='res.partner', string='Contractor Name', store=True, readonly=True),
		'sc_id': fields.many2one('kg.subcontract.process','Subcontractor List Id'),
		'ms_id': fields.related('sc_id','ms_id', type='many2one', relation='kg.machineshop', string='MS Id', store=True, readonly=True),
		'production_id': fields.related('sc_id','production_id', type='many2one', relation='kg.production', string='Production No.', store=True, readonly=True),
		#~ 'position_id': fields.related('sc_id','position_id', type='many2one', relation='kg.position.number', string='Position No.', store=True, readonly=True),
		#~ 'order_id': fields.related('sc_id','order_id', type='many2one', relation='kg.work.order', string='Work Order', store=True, readonly=True),
		'order_id': fields.many2one('kg.work.order','Work Order', readonly=True),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line', readonly=True),
		'oth_spec': fields.related('sc_id','oth_spec', type='text', string='WO Remarks', store=True, readonly=True),
		'moc_id': fields.many2one('kg.moc.master','MOC', required=True),
		'position_id': fields.many2one('kg.position.number','Position No.', required=True),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern Number'),
		'ms_shop_id': fields.many2one('kg.machine.shop','MS Item Code', domain="[('type','=','ms')]"),
		'pattern_code': fields.char('MS Item Code'),
		'pattern_name': fields.char('MS Item Name'),
		'item_code': fields.char('Item Code'),
		'item_name': fields.char('Pattern Name'),
		'entry_type': fields.selection([('direct','Direct'),('manual','Manual')], 'Entry Type', readonly=True),
		
		
		#~ 'order_line_id': fields.related('sc_id','order_line_id', type='many2one', relation='ch.work.order.details', string='Order Line', store=True, readonly=True),
		'order_no': fields.related('sc_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('sc_id','order_delivery_date', type='date', string='Delivery Date', store=True, readonly=True),

		'order_category': fields.related('sc_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.related('sc_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		#~ 'pump_model_id': fields.related('sc_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		#~ 'pattern_id': fields.related('sc_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		#~ 'pattern_code': fields.related('sc_id','pattern_code', type='char', string='Pattern Code', store=True, readonly=True),
		#~ 'pattern_name': fields.related('sc_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		#~ 'item_code': fields.related('sc_id','item_code', type='char', string='Item Code', store=True, readonly=True),
		#~ 'item_name': fields.related('sc_id','item_name', type='char', string='Item Name', store=True, readonly=True),
		#~ 'moc_id': fields.related('sc_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'ms_type': fields.related('sc_id','ms_type', type='selection', selection=[('foundry_item','Foundry Item'),('ms_item','MS Item')], string='Item Type', store=True, readonly=True),
		'operation_id': fields.many2many('ch.kg.position.number', 'm2m_wo_operation_details', 'wo_operation_id', 'wo_sub_id','Operation' , domain="[('header_id','=',position_id)]"),
		
		'line_ids':fields.one2many('ch.wo.operation.details', 'header_id', "WO Operation Details"),
		
		'actual_qty': fields.integer('Actual Qty',readonly=True),
		'sc_dc_qty': fields.integer('DC Qty',readonly=True),		
		'qty': fields.integer('Quantity'),
		'pending_qty': fields.integer('Pending Qty'),
		
		'amount': fields.function(_get_oper_value, string='Total Value', method=True, store=True, type='float'),
		
		
		'remarks': fields.text('Remarks'),		
		'dc_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')], 'DC Status', readonly=True),
		'dc_flag': fields.boolean('DC Flag'),
		'app_flag': fields.boolean('Approve Flag'),
		'read_flag': fields.boolean('Read Flag'),
	}
	
	
	_defaults = {
		
		'dc_state': 'pending',
		'entry_type': 'manual',
		'order_id': 520,
		'order_line_id': 855,
		'dc_flag': False,
		'app_flag': False,
		'read_flag': False,
		
	}
	
	
	def onchange_pattern(self, cr, uid, ids,pattern_id, context=None):
		value = {'pattern_code': '','pattern_name': '','item_code': '','item_name': ''}
		if pattern_id:
			print"sssssssssss",pattern_id
			pattern_rec = self.pool.get('kg.pattern.master').browse(cr,uid,pattern_id)
			print"pattern_rec.codepattern_rec.code",pattern_rec.name
			print"pattern_rec.pattern_namepattern_rec.pattern_name",pattern_rec.pattern_name
			value = {'item_code': pattern_rec.name,'item_name':pattern_rec.pattern_name}
		return {'value': value}
		
	def onchange_ms(self, cr, uid, ids,ms_shop_id, context=None):
		value = {'item_code': '','item_name': ''}
		if ms_shop_id:
			print"sssssssssss",ms_shop_id
			ms_rec = self.pool.get('kg.machine.shop').browse(cr,uid,ms_shop_id)
			
			value = {'pattern_code': ms_rec.code,'pattern_name':ms_rec.name}
		return {'value': value}
	
	
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

class ch_wo_operation_details(osv.osv):
	
	_name = "ch.wo.operation.details"
	_description = "WO Operation Details"
	
	_columns = {		
		
		'header_id':fields.many2one('ch.subcontract.wo.line', 'WO line Details', required=True, ondelete='cascade'),		
		'position_id': fields.many2one('kg.position.number','Position No',domain="[('state','=','approved')]"),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('state','=','approved')]"),
		'operation_id': fields.many2one('ch.kg.position.number','Operation',required=True,domain="[('header_id','=',position_id)]"),
		'stage_id': fields.many2one('kg.stage.master','Stage',domain="[('state','in',('approved'))]"), 			
		'op_rate':fields.float('Rate(Rs)',required=True),
		'flag_read': fields.boolean('Read Flag'),					
		'remarks':fields.text('Remarks'),		
	}
	
	_defaults = {
		
		
		'flag_read': False,
		
	}
	
	
	def default_get(self, cr, uid, fields, context=None):
		return context
		
	
	
	def onchange_operation_rate(self,cr, uid, ids, operation_id,position_id,moc_id, context=None):		
		moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
		oper_id_rec = self.pool.get('ch.kg.position.number').browse(cr,uid,operation_id)	
			
		if moc_rec.moc_cate_id.id == False:
			raise osv.except_osv(_('MOC Master Configure!!'),
							_('Please mapping in Moc Category in MOC Master!!'))
		cr.execute('''select line.rate from ch_kg_position_number as header
						left join ch_moccategory_mapping line on line.header_id = header.id
						where header.header_id = %s and header.operation_id = %s and line.moc_cate_id = %s
								  ''',[position_id,oper_id_rec.operation_id.id,moc_rec.moc_cate_id.id])
		operation_rate= cr.fetchone()				
		if operation_rate is not None:
			if operation_rate[0]:
				operation_rate = operation_rate[0]				
			else:
				operation_rate = 0.00					
		else:
			operation_rate = 0.00			
		
		return {'value': {'op_rate': operation_rate,'stage_id':oper_id_rec.stage_id.id}}
	
	def _check_rate(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])			
		if rec.op_rate <= 0.00:
			return False					
		return True
		
	def _check_same_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(""" select operation_id from ch_wo_operation_details where operation_id  = '%s' and header_id = '%s' """ %(entry.operation_id.id,entry.header_id.id))
		data = cr.dictfetchall()			
		if len(data) > 1:		
			return False
		return True	
		
	_constraints = [	
		(_check_rate,'System not allow to save Zero and Negative values in Rate field !!',['Rate']),
		(_check_same_values, 'Please Check the same Operation Name not allowed..!!',['Operation']),		
		]	
	   
ch_wo_operation_details()	



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
		'annexure_date': fields.date('Annexure Date'),
		'annexure_no': fields.integer('Annexure 17 No.'),
		'division_id': fields.many2one('kg.division.master','From Division'),
		'to_division_id': fields.many2one('kg.division.master','To Division'),
		'transfer_type': fields.selection([('internal','Internal'),('sub_contractor','Sub Contractor')],'Type'),
		'active': fields.boolean('Active'),
		'contractor_id': fields.many2one('res.partner','Subcontractor',domain="[('contractor','=','t'),('partner_state','=','approve')]"),	
		'phone': fields.char('Phone',size=64),
		'sub_wo_no': fields.char('Sub WO No.'),
		'contact_person': fields.char('Contact Person', size=128),		
		
		'dc_internal_line_ids': fields.many2many('kg.subcontract.process','m2m_dc_details' , 'order_id', 'sc_id', 'SC Items',
			domain="[('wo_state','in',('pending','partial')),('wo_process_state','=','allow')]"),
		'dc_sub_line_ids': fields.many2many('ch.subcontract.wo.line','m2m_dc_sub_details' , 'order_id', 'sc_id', 'SC Items',
		 domain="[('dc_state','in',('pending','partial')),('contractor_id','=',contractor_id),('dc_flag','=',False),('app_flag','=',True)]"),  
			
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
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
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
		wo_obj=self.pool.get('kg.subcontract.wo')
		
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
					'entry_mode':'direct',
					
					
				}
				
				wo_line_id = wo_line_obj.create(cr, uid,vals)
				
				sc_obj.write(cr, uid, item.id, {'wo_process_state': 'not_allow'})
				
			self.write(cr, uid, ids, {'flag_dc': True})
			
		if entry.dc_sub_line_ids:
			po_id = False
			
			for item in entry.dc_sub_line_ids:
				
				sc_qty = item.actual_qty 
				
				vals = {
				
					'header_id': entry.id,
					'sc_id':item.sc_id.id,
					'qty':item.qty - item.sc_dc_qty,
					'pending_qty':item.qty - item.sc_dc_qty,
					'actual_qty':sc_qty,
					'sc_wo_qty':item.qty,					
					'sc_dc_qty':item.qty - item.sc_dc_qty,					
					'sc_wo_line_id': item.id,
					'sub_wo_id': item.header_id.id,	
					'entry_type_stk':item.entry_type,
					'order_id':item.order_id.id,
					'order_line_id':item.order_line_id.id,
					'moc_id':item.moc_id.id,
					'position_id':item.position_id.id,
					'pump_model_id':item.pump_model_id.id,
					'pattern_id':item.pattern_id.id,
					'ms_shop_id':item.ms_shop_id.id,
					'pattern_code':item.pattern_code,
					'pattern_name':item.pattern_name,
					'item_code':item.item_code,
					'item_name':item.item_name,				
					'entry_mode':'from_wo',
							
				}
				
				wo_line_id = wo_line_obj.create(cr, uid,vals)				
				dc_rec = self.pool.get('ch.subcontract.dc.line').browse(cr, uid, wo_line_id)		
				for line_op in dc_rec.sc_wo_line_id.line_ids:								
					sql = """ insert into m2m_dc_operation_details (dc_operation_id,dc_sub_id) VALUES(%s,%s) """ %(wo_line_id,line_op.operation_id.id)
					cr.execute(sql)										
				cr.execute(""" select distinct sub_wo_id from ch_subcontract_dc_line where header_id = %s """ %(entry.id))
				wo_data = cr.dictfetchall()
				wo_list = []				
				for item in wo_data:
					wo_id = item['sub_wo_id']
					wo_record = wo_obj.browse(cr, uid, wo_id)
					wo_list.append(wo_record.name)
					wo_name = ",".join(wo_list)
					print"wo_namewo_name",wo_name
					self.write(cr,uid,ids[0],{
							'sub_wo_no':wo_name,							
							})		
										
				
			self.write(cr, uid, ids, {'flag_dc': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			sc_obj = self.pool.get('kg.subcontract.process')
			sc_wo_line_obj = self.pool.get('ch.subcontract.wo.line')
			print"entry.dc_sub_line_ids",entry.dc_sub_line_ids	
			print"entry.dc_internal_line_ids",entry.dc_internal_line_ids
			special_char = ''.join( c for c in entry.vehicle_detail if  c in '!@#$%^~*{}?+/=_-><?/`' )
			if entry.annexure_no <= 0:
				raise osv.except_osv(_('Warning!'),
								_('System not allow to Annexure 17 No. Zero and negative values!!'))	
			
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
									
					if line_item.qty > line_item.sc_dc_qty:
						raise osv.except_osv(_('Warning!'),
									_('System not allow Excess qty !!'))							
					if line_item.qty == 0:
						raise osv.except_osv(_('Warning!'),
									_('System not allow to save Zero values !!'))	
					direct_sc_dc_qty = 0.00
					if line_item.entry_type_stk == 'direct':
									
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
						direct_sc_dc_qty = line_item.sc_id.sc_dc_qty + line_item.qty
					
					self.pool.get('ch.subcontract.dc.line').write(cr,uid,line_item.id,{'pending_qty':line_item.qty,'entry_type':'sub_contract'})
						
					sc_obj.write(cr, uid, line_item.sc_id.id, 
								{'sc_dc_qty': direct_sc_dc_qty,'dc_state': dc_state,'wo_process_state':wo_process_state})		
								
					sc_wo_line_obj.write(cr, uid, line_item.sc_wo_line_id.id, 
								{'pending_qty': line_item.sc_wo_line_id.pending_qty - line_item.qty,'sc_dc_qty': line_item.sc_wo_line_id.sc_dc_qty + line_item.qty,'dc_state': wo_dc_state})				
								
			if entry.dc_internal_line_ids:	
				for line_item in entry.line_ids:				
					if line_item.qty < 0 and line_item.rate < 0:
						raise osv.except_osv(_('Warning!'),
									_('System not allow to save negative values !!'))
					if line_item.qty > line_item.sc_dc_qty:
						raise osv.except_osv(_('Warning!'),
									_('System not allow Excess qty !!'))									
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
									
					if line_item.qty > line_item.sc_dc_qty:
						raise osv.except_osv(_('Warning!'),
									_('System not allow Excess qty !!'))							
					if line_item.qty == 0:
						raise osv.except_osv(_('Warning!'),
									_('System not allow to save Zero values !!'))
					direct_sc_dc_qty = 0.00	
					dc_state = ''	
					wo_process_state = ''
					wo_dc_state = ''						
					if line_item.entry_type_stk == 'direct':								
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
						direct_sc_dc_qty = line_item.sc_id.sc_dc_qty + line_item.qty	
					
					
					
					self.pool.get('ch.subcontract.dc.line').write(cr,uid,line_item.id,{'pending_qty':line_item.qty,'entry_type':'sub_contract'})
						
					sc_obj.write(cr, uid, line_item.sc_id.id, 
								{'sc_dc_qty': direct_sc_dc_qty,'dc_state': dc_state,'wo_process_state':wo_process_state})		
								
					sc_wo_line_obj.write(cr, uid, line_item.sc_wo_line_id.id, 
								{'pending_qty': line_item.sc_wo_line_id.pending_qty - line_item.qty,'sc_dc_qty': line_item.sc_wo_line_id.sc_dc_qty + line_item.qty,'dc_state': wo_dc_state})				
															
					
			if 	entry.line_ids:
				for line in entry.line_ids:
					if line.ms_id:
						self.pool.get('kg.machineshop').write(cr, uid, line.ms_id.id,{'ms_state': 'op_in_sc'})						
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
		'sub_wo_id': fields.many2one('kg.subcontract.wo','SUB Work Id'),
		'contractor_id': fields.related('header_id','contractor_id', type='many2one', relation='res.partner', string='Contractor Name', store=True, readonly=True),
		'sc_id': fields.many2one('kg.subcontract.process','Subcontractor List Id'),
		'sc_wo_line_id': fields.many2one('ch.subcontract.wo.line','Subcontractor WO List Id'),
		'ms_id': fields.related('sc_id','ms_id', type='many2one', relation='kg.machineshop', string='MS Id', store=True, readonly=True),
		'oth_spec': fields.related('sc_id','oth_spec', type='text', string='WO Remarks', store=True, readonly=True),
		'production_id': fields.related('sc_id','production_id', type='many2one', relation='kg.production', string='Production No.', store=True, readonly=True),
		#~ 'position_id': fields.related('sc_id','position_id', type='many2one', relation='kg.position.number', string='Position No.', store=True, readonly=True),
		#~ 'order_id': fields.related('sc_id','order_id', type='many2one', relation='kg.work.order', string='Work Order', store=True, readonly=True),
		#~ 'order_line_id': fields.related('sc_id','order_line_id', type='many2one', relation='ch.work.order.details', string='Order Line', store=True, readonly=True),
		'order_no': fields.related('sc_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('sc_id','order_delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line', readonly=True),
		'order_id': fields.many2one('kg.work.order','Work Order', readonly=True),
		'moc_id': fields.many2one('kg.moc.master','MOC', required=True),
		'position_id': fields.many2one('kg.position.number','Position No.', required=True),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern Number'),
		'ms_shop_id': fields.many2one('kg.machine.shop','MS Item Name', domain="[('type','=','ms')]"),
		'pattern_code': fields.char('Pattern Code'),
		'pattern_name': fields.char('Pattern Name'),
		'item_code': fields.char('Item Code'),
		'item_name': fields.char('Item Name'),
		'entry_type_stk': fields.selection([('direct','Direct'),('manual','Manual')], 'Entry Type'),
		

		'order_category': fields.related('sc_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.related('sc_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		#~ 'pump_model_id': fields.related('sc_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		#~ 'pattern_id': fields.related('sc_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		#~ 'pattern_code': fields.related('sc_id','pattern_code', type='char', string='Pattern Code', store=True, readonly=True),
		#~ 'pattern_name': fields.related('sc_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		#~ 'item_code': fields.related('sc_id','item_code', type='char', string='Item Code', store=True, readonly=True),
		#~ 'item_name': fields.related('sc_id','item_name', type='char', string='Item Name', store=True, readonly=True),
		#~ 'moc_id': fields.related('sc_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'ms_type': fields.related('sc_id','ms_type', type='selection', selection=[('foundry_item','Foundry Item'),('ms_item','MS Item')], string='Item Type', store=True, readonly=True),
		'operation_id': fields.many2many('ch.kg.position.number', 'm2m_dc_operation_details', 'dc_operation_id', 'dc_sub_id','Operation', domain="[('header_id','=',position_id)]"),
		
		
		'entry_type': fields.selection([('sub_contract','Sub Contract'),('internal','Internal')],'Entry Type', readonly=True),
		
		'actual_qty': fields.integer('Actual Qty',readonly=True),
		'qty': fields.integer('Quantity'),
		'sc_dc_qty': fields.integer('Qty'),
		'sc_wo_qty': fields.integer('Qty'),
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
		'contractor_id': fields.many2one('res.partner','Subcontractor',domain="[('contractor','=','t'),('partner_state','=','approve')]"),
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
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'flag_inward': False,
		'transfer_type': 'sub_contractor',				
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
				'sc_wo_qty':item.qty,								
				'sub_wo_id':item.sub_wo_id.id,								
				'wo_line_id':item.sc_wo_line_id,		
				'actual_qty':item.actual_qty,		
				'each_weight':item.each_weight,					
				'sc_dc_line_id':item.id,
				'entry_type':item.entry_type_stk,
				'order_id':item.order_id.id,
				'order_line_id':item.order_line_id.id,
				'moc_id':item.moc_id.id,
				'position_id':item.position_id.id,
				'pump_model_id':item.pump_model_id.id,
				'pattern_id':item.pattern_id.id,
				'ms_shop_id':item.ms_shop_id.id,
				'pattern_code':item.pattern_code,
				'pattern_name':item.pattern_name,
				'item_code':item.item_code,
				'item_name':item.item_name,		
				'operation_id':[(6, 0, [x.id for x in item.operation_id])],
				'com_operation_id':[(6, 0, [x.id for x in item.operation_id])],
				
			}
			
			in_line_id = wo_line_obj.create(cr, uid,vals)	
		
		for item in entry.inward_sub_line_ids:			
			
			
			vals = {
			
				'header_id': entry.id,
				'sc_id':item.sc_id.id,
				'qty':item.qty - item.sc_in_qty,
				'sc_wo_qty':item.sc_wo_qty,
				'wo_line_id':item.sc_wo_line_id.id,								
				'actual_qty':item.actual_qty,		
				'each_weight':item.each_weight,					
				'sc_dc_line_id':item.id,
				'entry_type':item.entry_type_stk,
				'order_id':item.order_id.id,
				'order_line_id':item.order_line_id.id,
				'moc_id':item.moc_id.id,
				'position_id':item.position_id.id,
				'pump_model_id':item.pump_model_id.id,
				'pattern_id':item.pattern_id.id,
				'pattern_code':item.pattern_code,
				'pattern_name':item.pattern_name,
				'item_code':item.item_code,
				'item_name':item.item_name,					
				'operation_id':[(6, 0, [x.id for x in item.operation_id])],
				'com_operation_id':[(6, 0, [x.id for x in item.operation_id])],
				
			}
			
			in_line_id = wo_line_obj.create(cr, uid,vals)			
			
		self.write(cr, uid, ids, {'flag_inward': True})
		
			
		return True
	
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])	
		inward_line_obj = self.pool.get('ch.subcontract.inward.line')	
		sc_dc_line_obj = self.pool.get('ch.subcontract.dc.line')
		if entry.state == 'draft':
			if len(entry.line_ids) == 0:
				raise osv.except_osv(_('Warning!'),
								_('System not allow to without line items !!'))			
			
			sc_inward_name = ''	
			sc_inward_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.inward')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,sc_inward_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(sc_inward_seq_id[0],rec.code,entry.entry_date))
			sc_inward_name = cr.fetchone();	
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
										
				sc_dc_line_obj.write(cr, uid, line_item.sc_dc_line_id.id, 
							{'sc_in_qty': line_item.sc_dc_line_id.sc_in_qty + line_item.qty,'state': inward_state,'pending_qty':line_item.sc_dc_line_id.pending_qty - line_item.qty})			
				
				inward_line_obj.write(cr, uid, line_item.id,{'pending_qty':line_item.qty})	
														
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
		'sub_wo_id': fields.many2one('kg.subcontract.wo','SUB Work Id'),
		'contractor_id': fields.related('header_id','contractor_id', type='many2one', relation='res.partner', string='Contractor Name', store=True, readonly=True),
		'inward_no': fields.related('header_id','name', type='char', string='Inward No', store=True, readonly=True),
		
		'sc_id': fields.many2one('kg.subcontract.process','Subcontractor List Id'),
		'sc_dc_line_id': fields.many2one('ch.subcontract.dc.line','Subcontractor dc List Id'),
		'ms_id': fields.related('sc_id','ms_id', type='many2one', relation='kg.machineshop', string='MS Id', store=True, readonly=True),
		'oth_spec': fields.related('sc_id','oth_spec', type='text', string='WO Remarks', store=True, readonly=True),
		'production_id': fields.related('sc_id','production_id', type='many2one', relation='kg.production', string='Production No.', store=True, readonly=True),
		'order_no': fields.related('sc_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('sc_id','order_delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		
		'order_line_id': fields.many2one('ch.work.order.details','Order Line', readonly=True),
		'order_id': fields.many2one('kg.work.order','Work Order', readonly=True),
		'moc_id': fields.many2one('kg.moc.master','MOC', required=True),
		'position_id': fields.many2one('kg.position.number','Position No.', required=True),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern Number'),
		'ms_shop_id': fields.many2one('kg.machine.shop','MS Item Name', domain="[('type','=','ms')]"),
		'pattern_code': fields.char('Pattern Code'),
		'pattern_name': fields.char('Pattern Name'),
		'item_code': fields.char('Item Code'),
		'item_name': fields.char('Item Name'),
		'entry_type': fields.selection([('direct','Direct'),('manual','Manual')], 'Entry Type', readonly=True),	
		
		'order_category': fields.related('sc_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.related('sc_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		
		'ms_type': fields.related('sc_id','ms_type', type='selection', selection=[('foundry_item','Foundry Item'),('ms_item','MS Item')], string='Item Type', store=True, readonly=True),
		'wo_line_id': fields.many2one('ch.subcontract.wo.line','Subcontract Workorder Id'),
		
		'operation_id': fields.many2many('ch.kg.position.number', 'm2m_inward_operation_details', 'in_operation_id', 'in_sub_id','Operation', domain="[('header_id','=',position_id)]"),
		'com_operation_id': fields.many2many('ch.kg.position.number', 'm2m_in_com_operation_details', 'in_com_operation_id', 'in_com_sub_id','Completed Operation', domain="[('header_id','=',position_id)]"),
		'actual_qty': fields.integer('Actual Qty',readonly=True),
		'qty': fields.integer('Received Qty'),
		'sc_dc_qty': fields.integer('SC WO Qty'),
		'sc_wo_qty': fields.integer('SC WO Qty'),
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

class kg_subcontract_inspection(osv.osv):

	_name = "kg.subcontract.inspection"
	_description = "Subcontract Inspection"
	_order = "entry_date desc"		
		
	_columns = {

	
		'name': fields.char('Inspection No.', size=128,select=True,readonly=True),
		'entry_date': fields.date('Inspection Date',required=True),		
		'active': fields.boolean('Active'),			 
		 			
		'line_ids': fields.one2many('ch.subcontract.inspection.line','header_id','Subcontract Inspection Line'),   
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		
		'order_id': fields.many2many('ch.work.order.details', 'm2m_work_order_inspection_details', 'inspection_id', 'order_id','WO No' ,domain="[('state','=','confirmed')]"),
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),	
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
				
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_subcontract_inspection', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),		
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,			
		'state': 'draft',		
	}
	
	
	
	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		ins_line_obj = self.pool.get('ch.subcontract.inspection.line')			
		inward_line_obj = self.pool.get('ch.subcontract.inward.line')
		sub_obj = self.pool.get('ch.subcontract.inspection.operation.line')
		dim_obj = self.pool.get('ch.inspection.dimension.details')
		ch_pos_obj = self.pool.get('ch.kg.position.number')				
		del_sql = """ delete from ch_subcontract_inspection_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		cr.execute(""" select order_id from m2m_work_order_inspection_details where inspection_id = %s """ %(entry.id))
		inward_data = cr.dictfetchall()	
		print"inward_data",inward_data	
		for item in inward_data:						
			order_id = item['order_id']	
			print"order_id",order_id			
			cr.execute(""" select id from ch_subcontract_inward_line where order_line_id = %s and pending_qty > 0 order by id """ %(order_id))
			inward_line_data = cr.dictfetchall()
			print"inward_line_data",inward_line_data	
			for line_item in inward_line_data:						
				inward_line_record = inward_line_obj.browse(cr, uid, line_item['id'])					
				vals = {
				
					'header_id': entry.id,
					'customer_id': inward_line_record.order_id.partner_id.id,
					'sc_inward_line_id': inward_line_record.id,
					'sc_id':inward_line_record.sc_id.id,
					'qty':inward_line_record.pending_qty,								
					'inward_qty':inward_line_record.qty,								
					'sc_wo_qty':inward_line_record.sc_wo_qty,								
					'sub_wo_id':inward_line_record.sub_wo_id.id,								
					'wo_line_id':inward_line_record.wo_line_id.id,		
					'actual_qty':inward_line_record.actual_qty,		
					'each_weight':inward_line_record.each_weight,					
					'sc_dc_line_id':inward_line_record.sc_dc_line_id.id,
					'entry_type':inward_line_record.entry_type,
					'order_id':inward_line_record.order_id.id,
					'order_line_id':inward_line_record.order_line_id.id,
					'moc_id':inward_line_record.moc_id.id,
					'position_id':inward_line_record.position_id.id,
					'pump_model_id':inward_line_record.pump_model_id.id,
					'pattern_id':inward_line_record.pattern_id.id,
					'ms_shop_id':inward_line_record.ms_shop_id.id,
					'pattern_code':inward_line_record.pattern_code,
					'pattern_name':inward_line_record.pattern_name,
					'item_code':inward_line_record.item_code,
					'item_name':inward_line_record.item_name,		
					'totel_weight':inward_line_record.totel_weight,		
					'com_weight':inward_line_record.com_weight,		
					'operation_id':[(6, 0, [x.id for x in inward_line_record.operation_id])],
					'com_operation_id':[(6, 0, [x.id for x in inward_line_record.com_operation_id])],
					
				}
			
				ins_line_id = ins_line_obj.create(cr, uid,vals)	
				print"ins_line_idins_line_id0ins_line_id",ins_line_id
				
				line = ins_line_obj.browse(cr, uid, ins_line_id)	
				if line.com_operation_id:
					s = [(6, 0, [x.id for x in line.com_operation_id])]
					ss = [x.id for x in line.com_operation_id]				
					print"Completed Operations",ss				
					for item in ss:
						print"itemitemitem",item
						sub_id = sub_obj.create(cr,uid,{'header_id':line.id,'operation_id':item})
						if sub_id:
							print"sub_id",sub_id
							ch_po_ids = ch_pos_obj.search(cr,uid,[('id','=',item)])
							if ch_po_ids:
								ch_po_rec = ch_pos_obj.browse(cr,uid,ch_po_ids[0])
								if ch_po_rec.line_ids:
									for dim in ch_po_rec.line_ids:
										dim_obj.create(cr,uid,{'header_id':sub_id,
										'position_id':line.position_id.id,
										'operation_id':ch_po_rec.operation_id.id,
										'operation_name':ch_po_rec.name,
										'position_line_id':ch_po_rec.id,
										'pos_dimension_id':dim.id,									
										'dimension_id':dim.dimension_id.id,
										'description':dim.description,
										'min_val':dim.min_val,
										'max_val':dim.max_val,
										'remark':dim.remark										
										})
			
			
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':		
			sc_dc_line_obj = self.pool.get('ch.subcontract.dc.line')
			sc_obj = self.pool.get('kg.subcontract.process')
			ms_operation_obj = self.pool.get('kg.ms.operations')
			ms_dimension_obj = self.pool.get('ch.ms.dimension.details')
			ms_obj = self.pool.get('kg.machineshop')		
										
			if entry.line_ids:
				for item in entry.line_ids:
					print"item.entry_type",item.entry_type
					if item.entry_type == 'direct':
						print"item.entry_type",item.entry_type
						## from Operation ##
						print"item.sc_id.ms_op_id.id",item.sc_id.ms_op_id.id
						if item.sc_id.ms_op_id.id > 0:						
							print "FROM Operation>>>>>>>>>>>>>>>>>>>>@@@@@@@@@@@@@@@@@@@@@@"
							for i in entry.line_ids:
								if i.entry_type == 'direct':
									if i.com_operation_id:
										s = [(6, 0, [x.id for x in i.com_operation_id])]
										ss = [x.id for x in i.com_operation_id]
										
										print"Completed Operations",ss
										
										for x in ss:
											print"xxxxxxxxxxxx",x
											op_rec = self.pool.get('ch.kg.position.number').browse(cr,uid,x)
											op_name = op_rec.operation_id.name														
											ms_op_id =item.sc_id.ms_op_id.id
											
											if op_name == '10':
												self.pool.get('kg.ms.operations').operation1_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op1_state':'done'})												
											if op_name == '20':
												self.pool.get('kg.ms.operations').operation2_update(cr, uid, [ms_op_id])	
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op2_state':'done'})											
											if op_name == '30':
												self.pool.get('kg.ms.operations').operation3_update(cr, uid, [ms_op_id])									
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op3_state':'done'})											
											if op_name == '40':
												self.pool.get('kg.ms.operations').operation4_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op4_state':'done'})											
											if op_name == '50':
												self.pool.get('kg.ms.operations').operation5_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op5_state':'done'})											
											if op_name == '60':
												self.pool.get('kg.ms.operations').operation6_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op6_state':'done'})																						
											if op_name == '70':
												self.pool.get('kg.ms.operations').operation7_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op7_state':'done'})											
											if op_name == '80':
												self.pool.get('kg.ms.operations').operation8_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op8_state':'done'})											
											if op_name == '90':
												self.pool.get('kg.ms.operations').operation9_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op9_state':'done'})											
											if op_name == '100':
												self.pool.get('kg.ms.operations').operation10_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op10_state':'done'})											
											if op_name == '110':
												self.pool.get('kg.ms.operations').operation11_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op11_state':'done'})											
											if op_name == '120':
												self.pool.get('kg.ms.operations').operation12_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op12_state':'done'})											
										
									else:
										
										s = [(6, 0, [x.id for x in i.operation_id])]
										ss = [x.id for x in i.operation_id]
										print"Pending Operation List"										
										for x in ss:									
											op_rec = self.pool.get('ch.kg.position.number').browse(cr,uid,x)
											op_name = op_rec.operation_id.name														
											ms_op_id =item.sc_id.ms_op_id.id									
											if op_name == '10':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op1_state':'pending','op1_sc_status':'inhouse','op1_button_status':'visible'})										
											if op_name == '20':										
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op2_state':'pending','op2_sc_status':'inhouse','op2_button_status':'visible'})
											if op_name == '30':		
												print"Operation 3333333333"							
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op3_state':'pending','op3_sc_status':'inhouse','op3_button_status':'visible'})										
											if op_name == '40':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op4_state':'pending','op4_sc_status':'inhouse','op4_button_status':'visible'})										
											if op_name == '50':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op5_state':'pending','op5_sc_status':'inhouse','op5_button_status':'visible'})										
											if op_name == '60':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op6_state':'pending','op6_sc_status':'inhouse','op6_button_status':'visible'})										
											if op_name == '70':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op7_state':'pending','op7_sc_status':'inhouse','op7_button_status':'visible'})										
											if op_name == '80':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op8_state':'pending','op8_sc_status':'inhouse','op8_button_status':'visible'})										
											if op_name == '90':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op9_state':'pending','op9_sc_status':'inhouse','op9_button_status':'visible'})										
											if op_name == '100':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op10_state':'pending','op10_sc_status':'inhouse','op10_button_status':'visible'})										
											if op_name == '110':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op11_state':'pending','op11_sc_status':'inhouse','op11_button_status':'visible'})										
											if op_name == '120':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op12_state':'pending','op12_sc_status':'inhouse','op12_button_status':'visible'})
												
										
						else:			  				
							if item.entry_type == 'direct':
								total_qty = item.sc_id.sc_inward_qty + item.qty 
								if total_qty > item.sc_id.actual_qty:							
									ex_qty = total_qty - item.sc_id.actual_qty
									curent_qty = item.sc_id.actual_qty -  item.sc_id.sc_inward_qty
								elif total_qty <= item.sc_id.actual_qty:							
									ex_qty = 0
									curent_qty = item.qty 						
														
								if curent_qty > 0:									
								
									## Daily Planing Operation Creation Process ###			
									print "FROM DAILY Planning>>>>>>>>>>>>>>>>>>>>@@@@@@@@@@@@@@@@@@@@@@"
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
									if item.sc_id.actual_qty > 0:
										if item.position_id.id != False:
											position_id = self.pool.get('kg.position.number').browse(cr,uid,item.position_id.id)
											for pos_line_item in position_id.line_ids:
												
												if pos_line_item.operation_id.name == '10':
													op1_status = 'pending'
													op1_id = pos_line_item.operation_id.id
													op1_stage_id = pos_line_item.stage_id.id
													op1_clamping_area = pos_line_item.clamping_area
													
												if pos_line_item.operation_id.name == '20':
													op2_status = 'pending'
													op2_id = pos_line_item.operation_id.id
													op2_stage_id = pos_line_item.stage_id.id
													op2_clamping_area = pos_line_item.clamping_area
													
												if pos_line_item.operation_id.name == '30':
													op3_status = 'pending'
													op3_id = pos_line_item.operation_id.id
													op3_stage_id = pos_line_item.stage_id.id
													op3_clamping_area = pos_line_item.clamping_area
													
												if pos_line_item.operation_id.name == '40':
													op4_status = 'pending'
													op4_id = pos_line_item.operation_id.id
													op4_stage_id = pos_line_item.stage_id.id
													op4_clamping_area = pos_line_item.clamping_area
													
												if pos_line_item.operation_id.name == '50':
													op5_status = 'pending'
													op5_id = pos_line_item.operation_id.id
													op5_stage_id = pos_line_item.stage_id.id
													op5_clamping_area = pos_line_item.clamping_area
													
												if pos_line_item.operation_id.name == '60':
													op6_status = 'pending'
													op6_id = pos_line_item.operation_id.id
													op6_stage_id = pos_line_item.stage_id.id
													op6_clamping_area = pos_line_item.clamping_area
													
												if pos_line_item.operation_id.name == '70':
													op7_status = 'pending'
													op7_id = pos_line_item.operation_id.id
													op7_stage_id = pos_line_item.stage_id.id
													op7_clamping_area = pos_line_item.clamping_area
													
												if pos_line_item.operation_id.name == '80':
													op8_status = 'pending'
													op8_id = pos_line_item.operation_id.id
													op8_stage_id = pos_line_item.stage_id.id
													op8_clamping_area = pos_line_item.clamping_area
													
												if pos_line_item.operation_id.name == '90':
													op9_status = 'pending'
													op9_id = pos_line_item.operation_id.id
													op9_stage_id = pos_line_item.stage_id.id
													op9_clamping_area = pos_line_item.clamping_area
													
												if pos_line_item.operation_id.name == '100':
													op10_status = 'pending'
													op10_id = pos_line_item.operation_id.id
													op10_stage_id = pos_line_item.stage_id.id
													op10_clamping_area = pos_line_item.clamping_area
													
												if pos_line_item.operation_id.name == '110':
													op11_status = 'pending'
													op11_id = pos_line_item.operation_id.id
													op11_stage_id = pos_line_item.stage_id.id
													op11_clamping_area = pos_line_item.clamping_area
													
												if pos_line_item.operation_id.name == '120':
													op12_status = 'pending'
													op12_id = pos_line_item.operation_id.id
													op12_stage_id = pos_line_item.stage_id.id
													op12_clamping_area = pos_line_item.clamping_area
											
											### Operation Creation ###
											
											for operation in range(curent_qty):							
																	
												operation_vals = {
													'ms_id': item.ms_id.id,
													'position_id': item.position_id.id,		
													'pump_model_id': item.pump_model_id.id,		
													'pattern_id': item.pattern_id.id,		
													'moc_id': item.moc_id.id,		
													'item_code': item.item_code,		
													'item_name': item.item_name,														
													'ms_plan_id': item.sc_id.ms_plan_id.id,													
													'ms_plan_line_id': item.sc_id.ms_plan_line_id.id,	
													'order_id': item.order_id.id,
													'order_line_id': item.order_line_id.id,
													'order_category': item.order_category,
													'order_priority': item.order_priority,
													'ms_type': item.ms_type,												
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
												
												### MS State updation ##
												self.pool.get('kg.ms.daily.planning').op_status_update(cr, uid, 0, item.ms_id.id,ms_operation_id)
												
												### Creating Dimension Details ###
												
												if item.position_id.id != False:
													position_id = self.pool.get('kg.position.number').browse(cr,uid,item.position_id.id)
													for pos_line_item in position_id.line_ids:
														
														
														if pos_line_item.operation_id.name == '10':
															
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
																
														
														if pos_line_item.operation_id.name == '20':
															
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
																
																
														if pos_line_item.operation_id.name == '30':
															
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
																
																
														if pos_line_item.operation_id.name == '40':
															
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
																
																
														if pos_line_item.operation_id.name == '50':
															
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
																
																
														if pos_line_item.operation_id.name == '60':
															
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
																
																
														if pos_line_item.operation_id.name == '70':
															
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
																
																
														if pos_line_item.operation_id.name == '80':
															
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
																
																
														if pos_line_item.operation_id.name == '90':
															
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
																
																
														if pos_line_item.operation_id.name == '100':
															
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
																
																
														if pos_line_item.operation_id.name == '110':
															
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
																
																
														if pos_line_item.operation_id.name == '120':
															
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
													
												
													if item.com_operation_id:									
														s = [(6, 0, [x.id for x in item.com_operation_id])]
														ss = [x.id for x in item.com_operation_id]
														print"sssssssssssssssskkkkkkkkkkk",s
														print"sssssssssssssssskkkkkkkkkk",ss
														for x in ss:
															print"xxxxxxxxxxxxkkkkkkkkkkk",x
															op_rec = self.pool.get('ch.kg.position.number').browse(cr,uid,x)
															op_name = op_rec.operation_id.name
															print"op_nameop_nameop_nameop_name",op_name
															print"ms_operation_idms_operation_id",ms_operation_id
															print"op_nameop_nameop_nameop_name",op_name								
															ms_op_id = ms_operation_id
															
															if op_name == '10':
																self.pool.get('kg.ms.operations').operation1_update(cr, uid, [ms_op_id])
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op1_state':'done'})																
															if op_name == '20':
																self.pool.get('kg.ms.operations').operation2_update(cr, uid, [ms_op_id])
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op2_state':'done'})																
															if op_name == '30':	
																self.pool.get('kg.ms.operations').operation3_update(cr, uid, [ms_op_id])											
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op3_state':'done'})															
															if op_name == '40':
																self.pool.get('kg.ms.operations').operation4_update(cr, uid, [ms_op_id])
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op4_state':'done'})															
															if op_name == '50':
																self.pool.get('kg.ms.operations').operation5_update(cr, uid, [ms_op_id])
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op5_state':'done'})															
															if op_name == '60':
																self.pool.get('kg.ms.operations').operation6_update(cr, uid, [ms_op_id])
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op6_state':'done'})																										
															if op_name == '70':
																self.pool.get('kg.ms.operations').operation7_update(cr, uid, [ms_op_id])
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op7_state':'done'})															
															if op_name == '80':
																self.pool.get('kg.ms.operations').operation8_update(cr, uid, [ms_op_id])
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op8_state':'done'})															
															if op_name == '90':
																self.pool.get('kg.ms.operations').operation9_update(cr, uid, [ms_op_id])
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op9_state':'done'})															
															if op_name == '100':
																self.pool.get('kg.ms.operations').operation10_update(cr, uid, [ms_op_id])
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op10_state':'done'})															
															if op_name == '110':
																self.pool.get('kg.ms.operations').operation11_update(cr, uid, [ms_op_id])
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op11_state':'done'})															
															if op_name == '120':
																self.pool.get('kg.ms.operations').operation12_update(cr, uid, [ms_op_id])
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op12_state':'done'})															
													else:												
														pos_id = self.pool.get('ch.kg.position.number').search(cr, uid, [('header_id','=',item.position_id.id)])
														print"pos_idpos_id",pos_id
														for pos in pos_id:
															print"item",item
															pos_rec = self.pool.get('ch.kg.position.number').browse(cr, uid,pos)
															op_name = pos_rec.operation_id.name																				
															ms_op_id = ms_operation_id													
															if op_name == '10':
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op1_state':'pending'})														
															if op_name == '20':
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op2_state':'pending'})														
															if op_name == '30':												
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op3_state':'pending'})														
															if op_name == '40':
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op4_state':'pending'})														
															if op_name == '50':
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op5_state':'pending'})														
															if op_name == '60':
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op6_state':'pending'})																								
															if op_name == '70':
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op7_state':'pending'})														
															if op_name == '80':
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op8_state':'pending'})														
															if op_name == '90':
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op9_state':'pending'})														
															if op_name == '100':
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op10_state':'pending'})														
															if op_name == '110':
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op11_state':'pending'})														
															if op_name == '120':
																self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op12_state':'pending'})												
																
																					
					else:
						print"item.pattern_id",item.pattern_id
						print"item.pattern_id",item.ms_shop_id
						if item.pattern_id:
							ms_type='foundry_item'
						else:
							ms_type='ms_item'						
						work_id = self.pool.get('kg.work.order').search(cr, uid, [('name','=','STK WO')])
						work_rec = self.pool.get('kg.work.order').browse(cr,uid,work_id[0])
						
						print"work_recwork_rec",work_rec.id							
						print"work_rec.line_ids.idwork_rec.line_ids.id",work_rec.line_ids[0].id
						
						
						if item.qty > 0:						
								
							### Stock Inward Creation ###
							inward_obj = self.pool.get('kg.stock.inward')
							inward_line_obj = self.pool.get('ch.stock.inward.details')						
							print"line_item.order_id.location",item.order_id.location
							
							inward_vals = {
								'location': item.order_id.location
							}
							
							inward_id = inward_obj.create(cr, uid, inward_vals)
							
							inward_line_vals = {
								'header_id': inward_id,
								'location': item.order_id.location,
								'stock_type': 'pattern',
								'pump_model_id': item.pump_model_id.id,
								'pattern_id': item.pattern_id.id,
								'pattern_name': item.pattern_name,
								'item_code': item.item_code,
								'item_name': item.item_name,
								'moc_id': item.moc_id.id,							
								'qty': item.qty,
								'available_qty': item.qty,
								'each_wgt': 0,
								'total_weight': 0,
								'unit_price': 0,
								'stock_mode': 'excess',
								'ms_stock_state': 'operation_inprogress',
								'stock_item': ms_type,
								'position_id': item.position_id.id,
								
							}
							
							inward_line_id = inward_line_obj.create(cr, uid, inward_line_vals)
							print "inward_line_valsinward_line_valsinward_line_vals",inward_line_vals
		
						
						## Daily Planing Operation Creation Process ###			
						print "FROM DAILY Planning>>>>>>>>>>>>>>>>>>>>@@@@@@@@@@@@@@@@@@@@@@"
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
						print"111111111111"
						
						
						if item.position_id.id != False:
							position_id = self.pool.get('kg.position.number').browse(cr,uid,item.position_id.id)
							print"position_id",position_id
							for pos_line_item in position_id.line_ids:
								print"pos_line_item",pos_line_item								
								if pos_line_item.operation_id.name == '10':
									op1_status = 'pending'
									op1_id = pos_line_item.operation_id.id
									op1_stage_id = pos_line_item.stage_id.id
									op1_clamping_area = pos_line_item.clamping_area
									
								if pos_line_item.operation_id.name == '20':
									op2_status = 'pending'
									op2_id = pos_line_item.operation_id.id
									op2_stage_id = pos_line_item.stage_id.id
									op2_clamping_area = pos_line_item.clamping_area
									
								if pos_line_item.operation_id.name == '30':
									op3_status = 'pending'
									op3_id = pos_line_item.operation_id.id
									op3_stage_id = pos_line_item.stage_id.id
									op3_clamping_area = pos_line_item.clamping_area
									
								if pos_line_item.operation_id.name == '40':
									op4_status = 'pending'
									op4_id = pos_line_item.operation_id.id
									op4_stage_id = pos_line_item.stage_id.id
									op4_clamping_area = pos_line_item.clamping_area
									
								if pos_line_item.operation_id.name == '50':
									op5_status = 'pending'
									op5_id = pos_line_item.operation_id.id
									op5_stage_id = pos_line_item.stage_id.id
									op5_clamping_area = pos_line_item.clamping_area
									
								if pos_line_item.operation_id.name == '60':
									op6_status = 'pending'
									op6_id = pos_line_item.operation_id.id
									op6_stage_id = pos_line_item.stage_id.id
									op6_clamping_area = pos_line_item.clamping_area
									
								if pos_line_item.operation_id.name == '70':
									op7_status = 'pending'
									op7_id = pos_line_item.operation_id.id
									op7_stage_id = pos_line_item.stage_id.id
									op7_clamping_area = pos_line_item.clamping_area
									
								if pos_line_item.operation_id.name == '80':
									op8_status = 'pending'
									op8_id = pos_line_item.operation_id.id
									op8_stage_id = pos_line_item.stage_id.id
									op8_clamping_area = pos_line_item.clamping_area
									
								if pos_line_item.operation_id.name == '90':
									op9_status = 'pending'
									op9_id = pos_line_item.operation_id.id
									op9_stage_id = pos_line_item.stage_id.id
									op9_clamping_area = pos_line_item.clamping_area
									
								if pos_line_item.operation_id.name == '100':
									op10_status = 'pending'
									op10_id = pos_line_item.operation_id.id
									op10_stage_id = pos_line_item.stage_id.id
									op10_clamping_area = pos_line_item.clamping_area
									
								if pos_line_item.operation_id.name == '110':
									op11_status = 'pending'
									op11_id = pos_line_item.operation_id.id
									op11_stage_id = pos_line_item.stage_id.id
									op11_clamping_area = pos_line_item.clamping_area
									
								if pos_line_item.operation_id.name == '120':
									op12_status = 'pending'
									op12_id = pos_line_item.operation_id.id
									op12_stage_id = pos_line_item.stage_id.id
									op12_clamping_area = pos_line_item.clamping_area
							
							### Operation Creation ###
							print"inward_line_idinward_line_idinward@@@@@@@@@@@@@@@@@@@@@@#########################_line_id",inward_line_id
							for operation in range(item.qty):
															
								operation_vals = {
									'ms_id': item.ms_id.id,		
									'position_id': item.position_id.id,		
									'pump_model_id': item.pump_model_id.id,		
									'stock_inward_id': inward_line_id,		
									'pattern_id': item.pattern_id.id,		
									'moc_id': item.moc_id.id,		
									'item_code': item.item_code,		
									'item_name': item.item_name,									
									'order_id': work_rec.id,
									'order_line_id': work_rec.line_ids[0].id,		
									'order_category': item.order_category,
									'order_priority': item.order_priority,
									'ms_type': ms_type,																									
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
								
								### MS State updation ##
								self.pool.get('kg.ms.daily.planning').op_status_update(cr, uid, 0, item.ms_id.id,ms_operation_id)
												
								
								### Creating Dimension Details ###
								
								if item.position_id.id != False:
									position_id = self.pool.get('kg.position.number').browse(cr,uid,item.position_id.id)
									for pos_line_item in position_id.line_ids:
										
										
										if pos_line_item.operation_id.name == '10':
											
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
												
										
										if pos_line_item.operation_id.name == '20':
											
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
												
												
										if pos_line_item.operation_id.name == '30':
											
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
												
												
										if pos_line_item.operation_id.name == '40':
											
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
												
												
										if pos_line_item.operation_id.name == '50':
											
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
												
												
										if pos_line_item.operation_id.name == '60':
											
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
												
												
										if pos_line_item.operation_id.name == '70':
											
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
												
												
										if pos_line_item.operation_id.name == '80':
											
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
												
												
										if pos_line_item.operation_id.name == '90':
											
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
												
												
										if pos_line_item.operation_id.name == '100':
											
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
												
												
										if pos_line_item.operation_id.name == '110':
											
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
												
												
										if pos_line_item.operation_id.name == '120':
											
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
							
								
									if item.com_operation_id:										
										s = [(6, 0, [x.id for x in item.com_operation_id])]
										ss = [x.id for x in item.com_operation_id]
										print"ssssssssssssssssqqqqqqqqqqqqqq",s
										print"ssssssssssssssssqqqqqqqqqqq",ss
										for x in ss:
											print"xxxxxxxxxxxxqqqqqqqqqqqqq",x
											op_rec = self.pool.get('ch.kg.position.number').browse(cr,uid,x)
											op_name = op_rec.operation_id.name
											print"op_nameop_nameop_nameop_name",op_name
											print"ms_operation_idms_operation_id",ms_operation_id
											print"op_nameop_nameop_nameop_name",op_name								
											ms_op_id = ms_operation_id
											
											if op_name == '10':
												self.pool.get('kg.ms.operations').operation1_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op1_state':'done'})													
											if op_name == '20':
												self.pool.get('kg.ms.operations').operation2_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op2_state':'done'})													
											if op_name == '30':		
												self.pool.get('kg.ms.operations').operation3_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op3_state':'done'})												
											if op_name == '40':
												self.pool.get('kg.ms.operations').operation4_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op4_state':'done'})												
											if op_name == '50':
												self.pool.get('kg.ms.operations').operation5_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op5_state':'done'})												
											if op_name == '60':
												self.pool.get('kg.ms.operations').operation6_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op6_state':'done'})																							
											if op_name == '70':
												self.pool.get('kg.ms.operations').operation7_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op7_state':'done'})												
											if op_name == '80':
												self.pool.get('kg.ms.operations').operation8_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op8_state':'done'})												
											if op_name == '90':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op9_state':'done'})
												self.pool.get('kg.ms.operations').operation9_update(cr, uid, [ms_op_id])
											if op_name == '100':
												self.pool.get('kg.ms.operations').operation10_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op10_state':'done'})												
											if op_name == '110':
												self.pool.get('kg.ms.operations').operation11_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op11_state':'done'})												
											if op_name == '120':
												self.pool.get('kg.ms.operations').operation12_update(cr, uid, [ms_op_id])
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op12_state':'done'})												
									else:												
										pos_id = self.pool.get('ch.kg.position.number').search(cr, uid, [('header_id','=',item.position_id.id)])
										for pos in pos_id:													
											pos_rec = self.pool.get('ch.kg.position.number').browse(cr, uid,pos)
											op_name = pos_rec.operation_id.name																								
											ms_op_id = ms_operation_id													
											if op_name == '10':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op1_state':'pending'})														
											if op_name == '20':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op2_state':'pending'})														
											if op_name == '30':												
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op3_state':'pending'})														
											if op_name == '40':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op4_state':'pending'})														
											if op_name == '50':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op5_state':'pending'})														
											if op_name == '60':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op6_state':'pending'})																								
											if op_name == '70':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op7_state':'pending'})														
											if op_name == '80':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op8_state':'pending'})														
											if op_name == '90':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op9_state':'pending'})														
											if op_name == '100':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op10_state':'pending'})														
											if op_name == '110':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op11_state':'pending'})														
											if op_name == '120':
												self.pool.get('kg.ms.operations').write(cr,uid,ms_op_id,{'op12_state':'pending'})	
						
												
			direct_sc_inward_qty = 0		
			for line_item in entry.line_ids:				
				if line_item.qty < 0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative values !!'))
								
				if line_item.qty == 0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save Zero values !!'))	
				
								
				if line_item.qty > line_item.sc_inward_line_id.qty:
					raise osv.except_osv(_('Warning!'),
								_('Check the Qty !!! '))	
								
				if line_item.entry_type == 'direct':
					direct_sc_inward_qty = line_item.sc_id.sc_inward_qty + line_item.qty									
						
				
				self.pool.get('ch.subcontract.inward.line').write(cr,uid,line_item.sc_inward_line_id.id,{'pending_qty':line_item.sc_inward_line_id.pending_qty - line_item.qty})							
				
				
				sc_obj.write(cr, uid, line_item.sc_id.id, 
					{'sc_inward_qty':direct_sc_inward_qty})	
			
			### Sequence Number Generation  ###		
			if entry.name == '' or entry.name == False:
				seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.inspection')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_obj_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_obj_id[0],seq_rec.code,entry.entry_date))
				entry_name = cr.fetchone();
				entry_name = entry_name[0]
			else:
				entry_name = rec.name				
			
								
			self.write(cr, uid, ids, {'name':entry_name,'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
								
							
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
	
	def create(self, cr, uid, vals, context=None):
		return super(kg_subcontract_inspection, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_subcontract_inspection, self).write(cr, uid, ids, vals, context)
			
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
		
		
	   ]
		

kg_subcontract_inspection()

class ch_subcontract_inspection_line(osv.osv):
	
	_name = "ch.subcontract.inspection.line"
	_description = "Subcontract Inspection Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.subcontract.inspection','Header Id'),
		'sub_wo_id': fields.many2one('kg.subcontract.wo','SUB Work Id'),
		'customer_id': fields.many2one('res.partner','Customer Name'),
		'contractor_id': fields.related('header_id','contractor_id', type='many2one', relation='res.partner', string='Contractor Name', store=True, readonly=True),
		'inward_no': fields.related('header_id','name', type='char', string='Inward No', store=True, readonly=True),
		
		'sc_id': fields.many2one('kg.subcontract.process','Subcontractor List Id'),
		'sc_dc_line_id': fields.many2one('ch.subcontract.dc.line','Subcontractor dc List Id'),
		'sc_inward_line_id': fields.many2one('ch.subcontract.inward.line','Subcontractor Inward Line Id'),
		'ms_id': fields.related('sc_id','ms_id', type='many2one', relation='kg.machineshop', string='MS Id', store=True, readonly=True),
		'oth_spec': fields.related('sc_id','oth_spec', type='text', string='WO Remarks', store=True, readonly=True),
		'production_id': fields.related('sc_id','production_id', type='many2one', relation='kg.production', string='Production No.', store=True, readonly=True),		
		'order_no': fields.related('sc_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('sc_id','order_delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line', readonly=True),
		'order_id': fields.many2one('kg.work.order','Work Order', readonly=True),
		'moc_id': fields.many2one('kg.moc.master','MOC', required=True),
		'position_id': fields.many2one('kg.position.number','Position No.', required=True),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern Number'),
		'ms_shop_id': fields.many2one('kg.machine.shop','MS Item Name', domain="[('type','=','ms')]"),
		'pattern_code': fields.char('Pattern Code'),
		'pattern_name': fields.char('Pattern Name'),
		'item_code': fields.char('Item Code'),
		'item_name': fields.char('Item Name'),
		'entry_type': fields.selection([('direct','Direct'),('manual','Manual')], 'Entry Type', readonly=True),
		
		'line_ids': fields.one2many('ch.subcontract.inspection.operation.line','header_id','Subcontract DC Line'),
		
		'order_category': fields.related('sc_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.related('sc_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		
		'ms_type': fields.related('sc_id','ms_type', type='selection', selection=[('foundry_item','Foundry Item'),('ms_item','MS Item')], string='Item Type', store=True, readonly=True),
		'wo_line_id': fields.many2one('ch.subcontract.wo.line','Subcontract Workorder Id'),
		
		'operation_id': fields.many2many('ch.kg.position.number', 'm2m_inspection_operation_details', 'in_operation_id', 'in_sub_id','Operation', domain="[('header_id','=',position_id)]"),
		'com_operation_id': fields.many2many('ch.kg.position.number', 'm2m_inspection_com_operation_details', 'in_com_operation_id', 'in_com_sub_id','Completed Operation', domain="[('header_id','=',position_id)]"),
		'actual_qty': fields.integer('Actual Qty',readonly=True),
		'qty': fields.integer('Received Qty'),	
		'inward_qty': fields.integer('Inward Qty'),	
		'sc_wo_qty': fields.integer('SC WO Qty'),
		'pending_qty': fields.integer('Pending Qty'),		
		
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

ch_subcontract_inspection_line()




class ch_subcontract_inspection_operation_line(osv.osv):
	
	_name = "ch.subcontract.inspection.operation.line"
	_description = "Subcontract Inspection Operation Line"
	
	_columns = {
		
		'header_id': fields.many2one('ch.subcontract.inspection.line','Header Id'),	
		'line_ids': fields.one2many('ch.inspection.dimension.details','header_id','Subcontract Inspection Operation Line'),
		'operation_id': fields.many2one('ch.kg.position.number','Operation Name'),		
		
	}	
	
ch_subcontract_inspection_operation_line()

class ch_inspection_dimension_details(osv.osv):
	
	_name = 'ch.inspection.dimension.details'
	
	_columns = {
		
		'header_id':fields.many2one('ch.subcontract.inspection.operation.line', 'Line', required=True, ondelete='cascade'),
		'position_id': fields.many2one('kg.position.number','Position No'),
		'operation_id': fields.many2one('kg.operation.master','Operation'),
		'operation_name': fields.char('Operation Name'),
		'position_line_id': fields.many2one('ch.kg.position.number','Position No Line'),
		'pos_dimension_id': fields.many2one('kg.dimension','Dimension'),	
		'dimension_id': fields.many2one('kg.dimension.master','Dimension'), 				
		'description': fields.char('Description'), 		
		'min_val': fields.float('Minimum Value'), 
		'max_val': fields.float('Maximum Value'), 
		'actual_val': fields.float('Actual Value'), 
		'remark': fields.text('Remarks'),
		
	}
	
	def _entry_val_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])		
		if rec.actual_val >= rec.min_val and rec.actual_val <= rec.max_val:
			pass
		else:
			return False
		return True
	_constraints = [			
		#~ (_entry_val_check, 'Actual value should greater or equal to Minimum value !!',['Actual Value']),		
	   ]
	
ch_inspection_dimension_details()

