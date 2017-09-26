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



class kg_fettling_workorder(osv.osv):

	_name = "kg.fettling.workorder"
	_description = "Fettling Work Order"
	_order = "entry_date desc"	
	
	def _get_order_value(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		
		for entry in self.browse(cr, uid, ids, context=context):
			cr.execute(''' select sum(amount) from ch_fettling_wo_line where header_id = %s ''',[entry.id])
			wo_value = cr.fetchone()
			if wo_value[0] == None:
				wo_value = 0.00
			else:
				wo_value=wo_value[0]
			wo_value = wo_value
			result[entry.id] = wo_value
		return result
	
	_columns = {
		
		## Basic Info
		'name': fields.char('Work Order No.', size=24,select=True,readonly=True),
		'entry_date': fields.date('Order Date',required=True),		
		'note': fields.text('Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('approved','Approved'),('approved_dc','Approved & DC'),('cancel','Cancelled')],'Status', readonly=True),		
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_sms': fields.boolean('SMS Notification'),
		'flag_email': fields.boolean('Email Notification'),
		'flag_spl_approve': fields.boolean('Special Approval'),
		
		## Entry Info
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),	
		'active': fields.boolean('Active'),
		'crt_date': fields.datetime('Created Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),		
		'ap_rej_date': fields.datetime('Approved/Rejected Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Rejected By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),			
		
		## Module Requirement Info
		'division_id': fields.many2one('kg.division.master','Division',domain="[('state','=','approved')]"),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location'),
		'contractor_id': fields.many2one('res.partner','Subcontractor',domain="[('contractor','=','t'),('partner_state','=','approve')]"),
		'contact_person': fields.char('Contact Person', size=128),	  
		'phone': fields.char('Phone',size=64),
		'delivery_date': fields.date('Expected Delivery Date'),
		'wo_value': fields.function(_get_order_value, string='Sub Contractor WO Value', method=True, store=True, type='float'),
		'billing_type': fields.selection([('applicable','Applicable'),('not_applicable','Not Applicable')],'Billing Type'),
		
		
				
		## Child Tables Declaration
		
		'fettling_line_ids': fields.many2many('kg.fettling','m2m_fettling_wo_details' , 'order_id', 'fettling_id', 'Fettling Items',
			domain="[('state','=','accept'),('flag_sub_order','=',False)]"),
		'line_ids': fields.one2many('ch.fettling.wo.line','header_id','Fettling WO Line'),   
				
	
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.fettling.workorder', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'delivery_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'billing_type': 'applicable',		
		'state': 'draft',
		'entry_mode': 'manual',
		'flag_sms': False,		
		'flag_email': False,		
		'flag_spl_approve': False,
		
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
		wo_line_obj = self.pool.get('ch.fettling.wo.line')		
		del_sql = """ delete from ch_fettling_wo_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)			
		
		if entry.fettling_line_ids:		
			for item in entry.fettling_line_ids:
				if item.stage_id:
					cr.execute(""" select fettling.stage_id,stage.name as stage_name,fettling.seq_no,fettling.flag_ms from ch_fettling_process as fettling
					left join kg_moc_master moc on fettling.header_id = moc.id
					left join kg_stage_master stage on fettling.stage_id = stage.id
					where moc.id = %s and moc.state = 'approved' and moc.active = 't' and fettling.seq_no <
					(
					select fettling.seq_no from ch_fettling_process as fettling
					left join kg_moc_master moc on fettling.header_id = moc.id
					where moc.id = %s and moc.state = 'approved' and active = 't'and fettling.stage_id = %s
					)
					 
					order by fettling.seq_no desc limit 1 
					 """%(item.moc_id.id,item.moc_id.id,item.stage_id.id))
					fettling_stage_id = cr.dictfetchall();	
					weight = 0.00
					seq_no = 0	
					if fettling_stage_id:			
						for stage_item in fettling_stage_id:
							print"stage_item['stage_name']stage_item['stage_name']",stage_item['stage_name']
							if stage_item['stage_name'] == 'KNOCK OUT':
								weight = item.knockout_weight
							elif stage_item['stage_name'] == 'DECORING':
								weight = item.decoring_weight	
							elif stage_item['stage_name'] == 'SHOT BLAST':
								weight = item.shot_blast_weight	
							elif stage_item['stage_name'] == 'HAMMERING':
								weight = item.hammering_weight	
							elif stage_item['stage_name'] == 'WHEEL CUTTING':
								weight = item.wheel_cutting_weight	
							elif stage_item['stage_name'] == 'GAS CUTTING':
								weight = item.gas_cutting_weight	
							elif stage_item['stage_name'] == 'ARC CUTTING':
								weight = item.arc_cutting_weight	
							elif stage_item['stage_name'] == 'HEAT TREATMENT1':
								weight = item.heat_total_weight	
							elif stage_item['stage_name'] == 'HEAT TREATMENT2':
								weight = item.heat2_total_weight	
							elif stage_item['stage_name'] == 'HEAT TREATMENT3':
								weight = item.heat3_total_weight	
							elif stage_item['stage_name'] == 'ROUGH GRINDING':
								weight = item.rough_grinding_weight	
							elif stage_item['stage_name'] == 'FINISH GRINDING':
								weight = item.finish_grinding_weight	
							elif stage_item['stage_name'] == 'RE SHOT BLASTING':
								weight = item.reshot_blasting_weight
							if stage_item['seq_no']:
								seq_no = stage_item['seq_no'] + 1
					else:
						weight = item.pour_line_id.weight
				else:
					 weight = item.pour_line_id.weight					
				total_weight = 	weight * item.inward_accept_qty						
				vals = {								
					'header_id': entry.id,
					'fettling_id':item.id,
					'pattern_id':item.pattern_id.id,
					'pattern_code':item.pattern_code,
					'pattern_name':item.pattern_name,
					'moc_id':item.moc_id.id,
					'stage_id':item.stage_id.id,
					'stage_name':item.stage_name,
					'pour_id':item.pour_id.id,
					'pour_line_id':item.pour_line_id.id,
					'pump_model_id':item.pump_model_id.id,
					'order_bomline_id':item.order_bomline_id.id,
					'order_id':item.order_id.id,
					'order_line_id':item.order_line_id.id,
					'allocation_id':item.allocation_id.id,
					'schedule_id':item.schedule_id.id,
					'schedule_line_id':item.schedule_line_id.id,
					'qty':item.inward_accept_qty,					
					'seq_no':seq_no,						
															
					}						
				
				wo_line_id = wo_line_obj.create(cr, uid,vals)				
			
		return True
		
		
	def entry_confirm(self,cr,uid,ids,context=None):		
		entry = self.browse(cr,uid,ids[0])	
		if entry.state == 'draft':
			if not entry.line_ids:
				raise osv.except_osv(_('Line Item Details !!'),
				_('Enter the Work Order Details !!'))			
			for item in entry.line_ids:				
				if not item.line_ids:
					raise osv.except_osv(_('Work Order Stage Line Item Details !!'),
					_('Enter the Work Order Stage Details!!'))
				if item.fettling_id.flag_sub_order == True:
					raise osv.except_osv(_('Not Allow to Confirm !!'),
						_('Already fettling process comfirmed same Fettling!!'))
				for line_stage in item.line_ids:
					if line_stage.stage_rate <= 0.00:
						raise osv.except_osv(_('Rate Details!!'),
								_('Enter the Rate configure in Stage Master, After changes the stage id in WO!!'))	
				self.pool.get('kg.fettling').write(cr,uid,item.fettling_id.id,{'flag_sub_order':True})
			### Sequence Number Generation  ###		
			if entry.name == '' or entry.name == False:
				seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.fettling.workorder')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_obj_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_obj_id[0],seq_rec.code,entry.entry_date))
				entry_name = cr.fetchone();
				entry_name = entry_name[0]
			else:
				entry_name = entry.name		
			
			self.write(cr, uid, ids, {'name':entry_name,'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
				
		return True		
		
	def entry_approve(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'confirmed':
			for line in entry.line_ids:
				self.pool.get('ch.fettling.wo.line').write(cr,uid,line.id,{'pending_qty':line.qty})									
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})								
		return True
		
	def approve_dc(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'confirmed':				
			dc_obj = self.pool.get('kg.fettling.dc')
			dc_obj_line = self.pool.get('ch.fettling.dc.line')		
			dc_id = dc_obj.create(cr,uid,{'sub_wo_no':entry.name,'contractor_id':entry.contractor_id.id,'entry_mode': 'auto'})				
			for line_item in entry.line_ids:
				print"line_itemline_itemline_item",line_item.line_ids						
						
				dc_line = dc_obj_line.create(cr,uid,{'header_id': dc_id,'fettling_id':line_item.fettling_id.id,'pattern_id':line_item.pattern_id.id,'pattern_code':line_item.pattern_code,
													'pattern_name':line_item.pattern_name,'moc_id':line_item.moc_id.id,'stage_id':line_item.stage_id.id,'stage_name':line_item.stage_name,
													'pour_id':line_item.pour_id.id,'pour_line_id':line_item.pour_line_id.id,'pump_model_id':line_item.pump_model_id.id,'order_bomline_id':line_item.order_bomline_id.id,
													'order_id':line_item.order_id.id,'order_line_id':line_item.order_line_id.id,'allocation_id':line_item.allocation_id.id,'schedule_id':line_item.schedule_id.id,'schedule_line_id':line_item.schedule_line_id.id,
													'qty':line_item.qty,'each_weight':line_item.each_weight,'seq_no':line_item.seq_no,'sub_wo_id':line_item.header_id.id,'sub_wo_line_id':line_item.id,'entry_mode':'auto'})		
				for line in line_item.line_ids:	
					print"line.operation_id.id",line.stage_id.id
					print"dc_line.id",dc_line
					sql = """ insert into m2m_dc_stage_details (dc_stage_id,dc_sub_id) VALUES(%s,%s) """ %(dc_line,line.moc_stage_id.id)
					cr.execute(sql)			
				
				self.pool.get('ch.fettling.wo.line').write(cr,uid,line_item.id,{'entry_mode':'auto','pending_qty':line_item.qty})			
								
			self.write(cr, uid, ids, {'state': 'approved_dc','flag_app':False})							
							
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
		
	def create(self, cr, uid, vals, context=None):
		return super(kg_fettling_workorder, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_fettling_workorder, self).write(cr, uid, ids, vals, context)
	
kg_fettling_workorder()


class ch_fettling_wo_line(osv.osv):
	
	_name = "ch.fettling.wo.line"
	_description = "Fettling WO Line"	
	
	def _get_oper_value(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		total_value = 0.00
		value = 0.00
		for entry in self.browse(cr, uid, ids, context=context):
			for line in entry.line_ids:				
				total_value= entry.qty * line.stage_rate				
				value += total_value			
			result[entry.id] = value
		return result
	
	_columns = {
		
		'header_id': fields.many2one('kg.fettling.workorder','Header Id'),
		'contractor_id': fields.related('header_id','contractor_id', type='many2one', relation='res.partner', string='Contractor Name', store=True, readonly=True),		
		'fettling_id': fields.many2one('kg.fettling','Fettling Id'),
		
		'pattern_id': fields.many2one('kg.pattern.master','Pattern Number',domain="[('state','=','approved')]"),		
		'pattern_code': fields.char('Pattern Code'),
		'pattern_name': fields.char('Pattern Name'),		
		'moc_id': fields.many2one('kg.moc.master','MOC', required=True,domain="[('state','=','approved')]"),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True,domain="[('state','=','approved')]"),
		
		'stage_id':fields.many2one('kg.stage.master','Stage',domain="[('state','=','approved')]"),
		'stage_name': fields.char('Stage Name'),
		
		'pour_id':fields.many2one('kg.pouring.log','Pour Id'),
		'pour_line_id':fields.many2one('ch.pouring.details','Pour Id'),
		'pour_date': fields.related('pour_id','entry_date', type='datetime', string='Pouring date', store=True, readonly=True),			
		
		## Work Order Details		
		'order_bomline_id': fields.many2one('ch.order.bom.details','Order BOM Line Id',readonly=True),
		'order_id': fields.many2one('kg.work.order','Work Order'),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line'),
		'allocation_id': fields.many2one('ch.stock.allocation.detail','Allocation'),
		'order_no': fields.related('order_line_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('order_line_id','delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'order_date': fields.related('order_id','entry_date', type='date', string='Order Date', store=True, readonly=True),
		'order_category': fields.related('order_line_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.selection(ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		'oth_spec': fields.related('order_bomline_id','add_spec',type='text',string='WO Remarks',store=True,readonly=True),			
		
		### Schedule Details ###
		'schedule_id': fields.many2one('kg.schedule','Schedule No.'),
		'schedule_date': fields.related('schedule_id','entry_date', type='date', string='Schedule Date', store=True, readonly=True),
		'schedule_line_id': fields.many2one('ch.schedule.details','Schedule Line Item'),
			
		'qty': fields.integer('Quantity'),
		'pending_qty': fields.integer('Pending Qty'),		
		'each_weight': fields.related('fettling_id','each_weight', type='float', string='Weight(kgs)', store=True, readonly=True),
		'seq_no':fields.integer('Sequence'),		
				
		'amount': fields.function(_get_oper_value, string='Total Value', method=True, store=True, type='float'),		
		'remarks': fields.text('Remarks'),		
		'dc_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')], 'DC Status', readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),		
		
		## Child Tables Declaration
		
		'line_ids':fields.one2many('ch.wo.stage.details', 'header_id', "WO Stage Details"),		
	}	
	
	_defaults = {
		
		'dc_state': 'pending',		
		'entry_mode': 'manual',		
		
	}	
	
ch_fettling_wo_line()

class ch_wo_stage_details(osv.osv):
	
	_name = "ch.wo.stage.details"
	_description = "WO Stage Details"
	
	_columns = {		
		
		'header_id':fields.many2one('ch.fettling.wo.line', 'WO line Details', required=True, ondelete='cascade'),		
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('state','=','approved')]"),
		'seq_no':fields.integer('Sequence'),		
		'moc_stage_id': fields.many2one('ch.fettling.process','Stage',required=True,domain="[('header_id','=',moc_id),('seq_no','>=',seq_no)]"),		
		'each_weight':fields.integer('Weight(kgs)'),		
		'stage_id': fields.many2one('kg.stage.master','Stage',domain="[('state','=','approved')]"), 			
		'stage_rate':fields.float('Rate(Rs)'),							
		'remarks':fields.text('Remarks'),		
	}	
	
	
	def default_get(self, cr, uid, fields, context=None):
		return context
	
	def onchange_stage_id(self, cr, uid, ids, moc_stage_id, context=None):		
		if moc_stage_id:			
			stage_moc_rec = self.pool.get('ch.fettling.process').browse(cr,uid,moc_stage_id)			
			stage = stage_moc_rec.stage_id.id
		else:
			stage = ''		
		return {'value': {'stage_id': stage}}	
	
	def onchange_stage_rate(self,cr, uid, ids, stage_id,moc_id,each_weight, context=None):		
		moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
		if stage_id:	
			if moc_rec.moc_cate_fetting.id == False:
				raise osv.except_osv(_('MOC Master Configure!!'),
								_('Please mapping in Moc Category in MOC Master!!'))
			cr.execute('''select line.rate from kg_stage_master as header
							left join ch_stage_fettling line on line.header_id = header.id
							where header.id = %s and line.moc_cate_id = %s and line.min_val <= %s and line.max_val >= %s
									  ''',[stage_id,moc_rec.moc_cate_fetting.id,each_weight,each_weight])
			stage_rate= cr.fetchone()	
			print"stage_ratestage_rate"	,stage_rate		
			if stage_rate is not None:
				if stage_rate[0]:
					stage_rate = stage_rate[0]				
				else:
					stage_rate = 0.00					
			else:
				raise osv.except_osv(_('Rate Details !!'),
								_('Enter the Rate configure in Stage Master, After changes the stage id in WO!!'))					
		else:
			stage_rate = 0.00		
		return {'value': {'stage_rate': stage_rate}}
	
	def _check_rate(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])			
		if rec.stage_rate <= 0.00:
			return False					
		return True
		
	def _check_same_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(""" select stage_id from ch_wo_stage_details where stage_id  = '%s' and header_id = '%s' """ %(entry.stage_id.id,entry.header_id.id))
		data = cr.dictfetchall()			
		if len(data) > 1:		
			return False
		return True	
		
	_constraints = [	
		(_check_rate,'System not allow to save Zero and Negative values in Rate field !!',['Rate']),
		(_check_same_values, 'Please Check the same Stage Name not allowed..!!',['Stage']),		
		]	
	   
ch_wo_stage_details()	


class kg_fettling_dc(osv.osv):

	_name = "kg.fettling.dc"
	_description = "Fettling Subcontract DC"
	_order = "entry_date desc"		
		
	_columns = {

		
		## Basic Info
		'name': fields.char('DC No.', size=128,select=True,readonly=True),
		'entry_date': fields.date('DC Date',required=True),		
		'note': fields.text('Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_sms': fields.boolean('SMS Notification'),
		'flag_email': fields.boolean('Email Notification'),
		'flag_spl_approve': fields.boolean('Special Approval'),
		
		## Entry Info
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),	
		'active': fields.boolean('Active'),
		'crt_date': fields.datetime('Created Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),				
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),	
		
		## Module Requirement Info
		'annexure_date': fields.date('Annexure Date'),
		'annexure_no': fields.integer('Annexure 17 No.'),
		'division_id': fields.many2one('kg.division.master','From Division',domain="[('state','=','approved')]"),
		'to_division_id': fields.many2one('kg.division.master','To Division',domain="[('state','=','approved')]"),		
		'contractor_id': fields.many2one('res.partner','Subcontractor',domain="[('contractor','=','t'),('partner_state','=','approve')]"),	
		'phone': fields.char('Phone',size=64),
		'sub_wo_no': fields.char('Sub WO No.'),
		'contact_person': fields.char('Contact Person', size=128),		
		'vehicle_detail': fields.char('Vehicle Detail'),
		
		## Child Tables Declaration
		'dc_sub_line_ids': fields.many2many('ch.fettling.wo.line','m2m_dc_fettling_sub_details' , 'order_id', 'sc_wo_id', 'SC WO Items',
		 domain="[('pending_qty','>',0),('entry_mode','=','manual'),('contractor_id','=',contractor_id)]"),  
			
		'line_ids': fields.one2many('ch.fettling.dc.line','header_id','Fettling Subcontract DC Line'),  	
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_fettling_dc', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),		
		'annexure_date' : lambda * a: time.strftime('%Y-%m-%d'),		
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,			
		'state': 'draft',		
		'entry_mode': 'manual'		
	}
	
	def onchange_contractor(self, cr, uid, ids, contractor_id):
		if contractor_id:
			contractor_rec = self.pool.get('res.partner').browse(cr, uid, contractor_id)
		return {'value': {'contact_person':contractor_rec.contact_person,'phone':contractor_rec.phone  }}
	
	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		wo_line_obj = self.pool.get('ch.fettling.dc.line')	
		wo_obj=self.pool.get('kg.fettling.workorder')
		
		del_sql = """ delete from ch_fettling_dc_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)	
		
		if entry.dc_sub_line_ids:
		
			for item in entry.dc_sub_line_ids:				
				
				vals = {
					
					'header_id': entry.id,
					'fettling_id':item.fettling_id.id,
					'pattern_id':item.pattern_id.id,
					'pattern_code':item.pattern_code,
					'pattern_name':item.pattern_name,
					'moc_id':item.moc_id.id,
					'stage_id':item.stage_id.id,
					'stage_name':item.stage_name,
					'pour_id':item.pour_id.id,
					'pour_line_id':item.pour_line_id.id,
					'pump_model_id':item.pump_model_id.id,
					'order_bomline_id':item.order_bomline_id.id,
					'order_id':item.order_id.id,
					'order_line_id':item.order_line_id.id,
					'allocation_id':item.allocation_id.id,
					'schedule_id':item.schedule_id.id,
					'schedule_line_id':item.schedule_line_id.id,
					'qty':item.pending_qty,
					'each_weight':item.each_weight,
					'seq_no':item.seq_no,			
					'sub_wo_id':item.header_id.id,			
					'sub_wo_line_id':item.id,				
					
				}
				
				wo_line_id = wo_line_obj.create(cr, uid,vals)							
				dc_rec = self.pool.get('ch.fettling.dc.line').browse(cr, uid, wo_line_id)		
				for line_stage in dc_rec.sub_wo_line_id.line_ids:								
					sql = """ insert into m2m_dc_stage_details (dc_stage_id,dc_sub_id) VALUES(%s,%s) """ %(wo_line_id,line_stage.moc_stage_id.id)
					cr.execute(sql)										
				cr.execute(""" select distinct sub_wo_id from ch_fettling_dc_line where header_id = %s """ %(entry.id))
				wo_data = cr.dictfetchall()
				wo_list = []				
				for item in wo_data:
					wo_id = item['sub_wo_id']
					print"wo_idwo_id",wo_id
					wo_record = wo_obj.browse(cr, uid, wo_id)
					print"wo_record",wo_record.name	
					wo_list.append(wo_record.name)
					print"wo_listwo_list",wo_list	
					wo_name = ",".join(wo_list)
					print"wo_namewo_name",wo_name				
					self.write(cr,uid,ids[0],{'sub_wo_no':wo_name,})		
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':		
			sc_wo_line_obj = self.pool.get('ch.fettling.wo.line')			
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
			if entry.line_ids:
				for line_item in entry.line_ids:											
					if line_item.qty <= 0:
						raise osv.except_osv(_('Warning!'),
									_('System not allow to save zero and negative values !!'))									
					if line_item.qty > line_item.sub_wo_line_id.pending_qty:
						raise osv.except_osv(_('Warning!'),
									_('System not allow Excess qty !!'))
					self.pool.get('ch.fettling.dc.line').write(cr,uid,line_item.id,{'pending_qty':line_item.qty})					
					self.pool.get('ch.fettling.wo.line').write(cr,uid,line_item.sub_wo_line_id.id,{'pending_qty':line_item.sub_wo_line_id.pending_qty - line_item.qty})
			
			### Sequence Number Generation  ###		
			if entry.name == '' or entry.name == False:
				seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.fettling.dc')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_obj_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_obj_id[0],seq_rec.code,entry.entry_date))
				entry_name = cr.fetchone();
				entry_name = entry_name[0]
			else:
				entry_name = entry.name	
												
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
		
	def create(self, cr, uid, vals, context=None):
		return super(kg_fettling_dc, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_fettling_dc, self).write(cr, uid, ids, vals, context)
		
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
	
kg_fettling_dc()

class ch_fettling_dc_line(osv.osv):
	
	_name = "ch.fettling.dc.line"
	_description = "Fettling Subcontract DC Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.fettling.dc','Header Id'),
		'sub_wo_id': fields.many2one('kg.fettling.workorder','SUB Work Id'),
		'sub_wo_line_id': fields.many2one('ch.fettling.wo.line','SUB Work Line Id'),
		'contractor_id': fields.related('header_id','contractor_id', type='many2one', relation='res.partner', string='Contractor Name', store=True, readonly=True),
		
		'fettling_id': fields.many2one('kg.fettling','Fettling Id'),		
		'pattern_id': fields.many2one('kg.pattern.master','Pattern Number'),		
		'pattern_code': fields.char('Pattern Code'),
		'pattern_name': fields.char('Pattern Name'),		
		'moc_id': fields.many2one('kg.moc.master','MOC', required=True),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True),
		
		'stage_id':fields.many2one('kg.stage.master','Stage'),
		'stage_name': fields.char('Stage Name'),
		
		'pour_id':fields.many2one('kg.pouring.log','Pour Id'),
		'pour_line_id':fields.many2one('ch.pouring.details','Pour Id'),
		'pour_date': fields.related('pour_id','entry_date', type='datetime', string='Pouring date', store=True, readonly=True),			
		
		## Work Order Details		
		'order_bomline_id': fields.many2one('ch.order.bom.details','Order BOM Line Id',readonly=True),
		'order_id': fields.many2one('kg.work.order','Work Order'),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line'),
		'allocation_id': fields.many2one('ch.stock.allocation.detail','Allocation'),
		'order_no': fields.related('order_line_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('order_line_id','delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'order_date': fields.related('order_id','entry_date', type='date', string='Order Date', store=True, readonly=True),
		'order_category': fields.related('order_line_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.selection(ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		'oth_spec': fields.related('order_bomline_id','add_spec',type='text',string='WO Remarks',store=True,readonly=True),			
		
		### Schedule Details ###
		'schedule_id': fields.many2one('kg.schedule','Schedule No.'),
		'schedule_date': fields.related('schedule_id','entry_date', type='date', string='Schedule Date', store=True, readonly=True),
		'schedule_line_id': fields.many2one('ch.schedule.details','Schedule Line Item'),
		
		'moc_stage_id': fields.many2many('ch.fettling.process', 'm2m_dc_stage_details','dc_stage_id', 'dc_sub_id','Stage', domain="[('header_id','=',moc_id)]"),
			
		'qty': fields.integer('Quantity', required=True),
		'pending_qty': fields.integer('Pending Qty'),
		'each_weight': fields.related('fettling_id','each_weight', type='float', string='Weight(kgs)', store=True, readonly=True),
		'seq_no':fields.integer('Sequence'),				
		'remarks': fields.text('Remarks'),		
		'state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')],'Status', readonly=True),	
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),		
	}
	
	_defaults = {		
		'state': 'pending',
		'entry_mode': 'manual',		
	}

ch_fettling_dc_line()	




class kg_fettling_inward(osv.osv):

	_name = "kg.fettling.inward"
	_description = "Fettling Subcontract Inward"
	_order = "entry_date desc"		
		
	_columns = {

		
		## Basic Info
		'name': fields.char('Inward No.', size=128,select=True,readonly=True),
		'entry_date': fields.date('Inward Date',required=True),		
		'note': fields.text('Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_sms': fields.boolean('SMS Notification'),
		'flag_email': fields.boolean('Email Notification'),
		'flag_spl_approve': fields.boolean('Special Approval'),
		
		## Entry Info
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),	
		'active': fields.boolean('Active'),
		'crt_date': fields.datetime('Created Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),				
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),	
		
		## Module Requirement Info
		
		'division_id': fields.many2one('kg.division.master','From Division',domain="[('state','=','approved')]"),
		'to_division_id': fields.many2one('kg.division.master','To Division',domain="[('state','=','approved')]"),		
		'contractor_id': fields.many2one('res.partner','Subcontractor',domain="[('contractor','=','t'),('partner_state','=','approve')]"),	
		'phone': fields.char('Phone',size=64),		
		'contact_person': fields.char('Contact Person', size=128),			
		
		## Child Tables Declaration
		'inward_sub_line_ids': fields.many2many('ch.fettling.dc.line','m2m_inward_fettling_sub_details' , 'order_id', 'sc_dc_id', 'SC DC Items',
		 domain="[('pending_qty','>',0),('contractor_id','=',contractor_id)]"),  
			
		'line_ids': fields.one2many('ch.fettling.inward.line','header_id','Fettling Subcontract Inward Line'),  	
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_fettling_inward', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),		
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,			
		'state': 'draft',		
		'entry_mode': 'manual'		
	}
	
	def onchange_contractor(self, cr, uid, ids, contractor_id):
		if contractor_id:
			contractor_rec = self.pool.get('res.partner').browse(cr, uid, contractor_id)
		return {'value': {'contact_person':contractor_rec.contact_person,'phone':contractor_rec.phone  }}
	
	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		inward_line_obj = self.pool.get('ch.fettling.inward.line')			
		del_sql = """ delete from ch_fettling_inward_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)	
		
		if entry.inward_sub_line_ids:
		
			for item in entry.inward_sub_line_ids:				
				
				vals = {
					
					'header_id': entry.id,
					'fettling_id':item.fettling_id.id,
					'pattern_id':item.pattern_id.id,
					'pattern_code':item.pattern_code,
					'pattern_name':item.pattern_name,
					'moc_id':item.moc_id.id,
					'stage_id':item.stage_id.id,
					'stage_name':item.stage_name,
					'pour_id':item.pour_id.id,
					'pour_line_id':item.pour_line_id.id,
					'pump_model_id':item.pump_model_id.id,
					'order_bomline_id':item.order_bomline_id.id,
					'order_id':item.order_id.id,
					'order_line_id':item.order_line_id.id,
					'allocation_id':item.allocation_id.id,
					'schedule_id':item.schedule_id.id,
					'schedule_line_id':item.schedule_line_id.id,
					'qty':item.pending_qty,
					'each_weight':item.each_weight,
					'seq_no':item.seq_no,			
					'sub_dc_id':item.header_id.id,			
					'sub_dc_line_id':item.id,
					'sub_wo_line_id':item.sub_wo_line_id.id,
					'moc_stage_id':[(6, 0, [x.id for x in item.moc_stage_id])],
					'com_moc_stage_id':[(6, 0, [x.id for x in item.moc_stage_id])],				
					
				}
				
				inward_line_id = inward_line_obj.create(cr, uid,vals)							
					
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':		
			sc_dc_line_obj = self.pool.get('ch.fettling.dc.line')					
			if len(entry.line_ids) == 0:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to without line items !!'))								
			if entry.line_ids:
				for item in entry.line_ids:						
					## from Stage ##					
					if item.fettling_id.id > 0:						
						print "FROM Stage>>>>>>>>>>>>>>>"
						for i in entry.line_ids:							
							com_test = [x.id for x in i.com_moc_stage_id]
							first_test = [x.id for x in i.moc_stage_id]								
							check_stage = set(com_test) - set(first_test)									
							if check_stage:
								raise osv.except_osv(_('Warning!'),
									_('System no need allow to add additional stage in Completed Stage field !!'))
							else:
								pass										
							if i.com_moc_stage_id:
								s = [(6, 0, [x.id for x in i.com_moc_stage_id])]							
								ss = [x.id for x in i.com_moc_stage_id]															
								for x in ss:									
									moc_stage_rec = self.pool.get('ch.fettling.process').browse(cr,uid,x)
									stage_name = moc_stage_rec.stage_id.name																
									fettling_id = item.fettling_id.id									
									done_by = 'contractor'
									contractor_id = item.contractor_id.id
									accept_qty = item.qty
									weight = item.each_weight
									if stage_name == 'KNOCK OUT':
										self.pool.get('kg.fettling').write(cr,uid,fettling_id,{
										'knockout_by':done_by,'knockout_contractor':contractor_id,'knockout_accept_qty':accept_qty,'knockout_weight':weight,'flag_sub_order':False})
										self.pool.get('kg.fettling').knockout_update(cr, uid, [fettling_id])
									elif stage_name == 'DECORING':
										self.pool.get('kg.fettling').write(cr,uid,fettling_id,{
										'decoring_by':done_by,'decoring_contractor':contractor_id,'decoring_accept_qty':accept_qty,'decoring_weight':weight,'flag_sub_order':False})
										self.pool.get('kg.fettling').decoring_update(cr, uid, [fettling_id])
									elif stage_name == 'SHOT BLAST':
										self.pool.get('kg.fettling').write(cr,uid,fettling_id,{
										'shot_blast_by':done_by,'shot_blast_contractor':contractor_id,'shot_blast_accept_qty':accept_qty,'shot_blast_weight':weight,'flag_sub_order':False})
										self.pool.get('kg.fettling').shot_blast_update(cr, uid, [fettling_id])
									elif stage_name == 'HAMMERING':
										self.pool.get('kg.fettling').write(cr,uid,fettling_id,{
										'hammering_by':done_by,'hammering_contractor':contractor_id,'hammering_accept_qty':accept_qty,'hammering_weight':weight,'flag_sub_order':False})
										self.pool.get('kg.fettling').hammering_update(cr, uid, [fettling_id])
									elif stage_name == 'WHEEL CUTTING':
										self.pool.get('kg.fettling').write(cr,uid,fettling_id,{
										'wheel_cutting_by':done_by,'wheel_cutting_contractor':contractor_id,'wheel_cutting_accept_qty':accept_qty,'wheel_cutting_weight':weight,'flag_sub_order':False})
										self.pool.get('kg.fettling').wheel_cutting_update(cr, uid, [fettling_id])
									elif stage_name == 'GAS CUTTING':
										self.pool.get('kg.fettling').write(cr,uid,fettling_id,{
										'gas_cutting_by':done_by,'gas_cutting_contractor':contractor_id,'gas_cutting_accept_qty':accept_qty,'gas_cutting_weight':weight,'flag_sub_order':False})
										self.pool.get('kg.fettling').gas_cutting_update(cr, uid, [fettling_id])
									elif stage_name == 'ARC CUTTING':
										self.pool.get('kg.fettling').write(cr,uid,fettling_id,{
										'arc_cutting_by':done_by,'arc_cutting_contractor':contractor_id,'arc_cutting_accept_qty':accept_qty,'arc_cutting_weight':weight,'flag_sub_order':False})
										self.pool.get('kg.fettling').arc_cutting_update(cr, uid, [fettling_id])
									elif stage_name == 'HEAT TREATMENT1':
										self.pool.get('kg.fettling').write(cr,uid,fettling_id,{'heat_specification':item.remarks,
										'heat_by':done_by,'heat_contractor':contractor_id,'heat_qty':accept_qty,'heat_total_weight':weight,'heat_each_weight':weight/accept_qty,'flag_sub_order':False})
										self.pool.get('kg.fettling').heat_treatment_update(cr, uid, [fettling_id])
									elif stage_name == 'HEAT TREATMENT2':
										self.pool.get('kg.fettling').write(cr,uid,fettling_id,{'heat2_specification':item.remarks,
										'heat2_by':done_by,'heat2_contractor':contractor_id,'heat2_qty':accept_qty,'heat2_each_weight':weight/accept_qty,'flag_sub_order':False})
										self.pool.get('kg.fettling').heat_treatment2_update(cr, uid, [fettling_id])
									elif stage_name == 'HEAT TREATMENT3':
										self.pool.get('kg.fettling').write(cr,uid,fettling_id,{'knockout_shift_id':item.remarks,
										'heat3_by':done_by,'heat3_contractor':contractor_id,'heat3_qty':accept_qty,'heat3_each_weight':weight/accept_qty,'flag_sub_order':False})
										self.pool.get('kg.fettling').heat_treatment3_update(cr, uid, [fettling_id])
									elif stage_name == 'ROUGH GRINDING':
										self.pool.get('kg.fettling').write(cr,uid,fettling_id,{
										'rough_grinding_by':done_by,'rough_grinding_contractor':contractor_id,'rough_grinding_accept_qty':accept_qty,'rough_grinding_weight':weight})
										self.pool.get('kg.fettling').rough_grinding_update(cr, uid, [fettling_id])
									elif stage_name == 'WELDING':
										self.pool.get('kg.fettling').write(cr,uid,fettling_id,{
										'welding_by':done_by,'welding_contractor':contractor_id,'welding_accept_qty':accept_qty,'welding_weight':weight,'flag_sub_order':False})
										self.pool.get('kg.fettling').welding_update(cr, uid, [fettling_id])
									elif stage_name == 'FINISH GRINDING':
										self.pool.get('kg.fettling').write(cr,uid,fettling_id,{
										'finish_grinding_by':done_by,'finish_grinding_contractor':contractor_id,'finish_grinding_accept_qty':accept_qty,'finish_grinding_qty':accept_qty,'finish_grinding_weight':weight,'flag_sub_order':False})
										self.pool.get('kg.fettling').finish_grinding_update(cr, uid, [fettling_id])
									elif stage_name == 'RE SHOT BLASTING':
										self.pool.get('kg.fettling').write(cr,uid,fettling_id,{
										'reshot_blasting_by':done_by,'reshot_blasting_contractor':contractor_id,'reshot_blasting_accept_qty':accept_qty,'reshot_blasting_weight':weight,'flag_sub_order':False})
										self.pool.get('kg.fettling').reshot_blasting_update(cr, uid, [fettling_id])		
				
				
				for line_item in entry.line_ids:				
					if line_item.qty <= 0:
						raise osv.except_osv(_('Warning!'),
									_('System not allow to save zero and negative values !!'))									
					if line_item.qty > line_item.sub_dc_line_id.pending_qty:
						raise osv.except_osv(_('Warning!'),
									_('System not allow Excess qty !!'))					
					self.pool.get('ch.fettling.dc.line').write(cr,uid,line_item.sub_dc_line_id.id,{'pending_qty':line_item.sub_dc_line_id.pending_qty - line_item.qty})
		
			### Sequence Number Generation  ###		
			if entry.name == '' or entry.name == False:
				seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.fettling.sc.inward')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_obj_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_obj_id[0],seq_rec.code,entry.entry_date))
				entry_name = cr.fetchone();
				entry_name = entry_name[0]
			else:
				entry_name = entry.name													
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
		
	def create(self, cr, uid, vals, context=None):
		return super(kg_fettling_inward, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_fettling_inward, self).write(cr, uid, ids, vals, context)
		
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
	
kg_fettling_inward()

class ch_fettling_inward_line(osv.osv):
	
	_name = "ch.fettling.inward.line"
	_description = "Fettling Subcontract Inward Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.fettling.inward','Header Id'),
		'sub_dc_id': fields.many2one('kg.fettling.dc','DC Id'),
		'sub_dc_line_id': fields.many2one('ch.fettling.dc.line','DC Line Id'),
		'sub_wo_line_id': fields.many2one('ch.fettling.wo.line','SUB Work Line Id'),
		'contractor_id': fields.related('header_id','contractor_id', type='many2one', relation='res.partner', string='Contractor Name', store=True, readonly=True),
		
		'fettling_id': fields.many2one('kg.fettling','Fettling Id'),		
		'pattern_id': fields.many2one('kg.pattern.master','Pattern Number'),		
		'pattern_code': fields.char('Pattern Code'),
		'pattern_name': fields.char('Pattern Name'),		
		'moc_id': fields.many2one('kg.moc.master','MOC', required=True),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True),
		
		'stage_id':fields.many2one('kg.stage.master','Stage'),
		'stage_name': fields.char('Stage Name'),
		
		'pour_id':fields.many2one('kg.pouring.log','Pour Id'),
		'pour_line_id':fields.many2one('ch.pouring.details','Pour Id'),
		'pour_date': fields.related('pour_id','entry_date', type='datetime', string='Pouring date', store=True, readonly=True),			
		
		## Work Order Details		
		'order_bomline_id': fields.many2one('ch.order.bom.details','Order BOM Line Id',readonly=True),
		'order_id': fields.many2one('kg.work.order','Work Order'),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line'),
		'allocation_id': fields.many2one('ch.stock.allocation.detail','Allocation'),
		'order_no': fields.related('order_line_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('order_line_id','delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'order_date': fields.related('order_id','entry_date', type='date', string='Order Date', store=True, readonly=True),
		'order_category': fields.related('order_line_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.selection(ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		'oth_spec': fields.related('order_bomline_id','add_spec',type='text',string='WO Remarks',store=True,readonly=True),			
		
		### Schedule Details ###
		'schedule_id': fields.many2one('kg.schedule','Schedule No.'),
		'schedule_date': fields.related('schedule_id','entry_date', type='date', string='Schedule Date', store=True, readonly=True),
		'schedule_line_id': fields.many2one('ch.schedule.details','Schedule Line Item'),
		
		'moc_stage_id': fields.many2many('ch.fettling.process', 'm2m_inward_stage_details','inward_sub_id','inward_stage_id','Stage', domain="[('header_id','=',moc_id)]"),
		'com_moc_stage_id': fields.many2many('ch.fettling.process', 'm2m_inward_com_stage_details','com_inward_sub_id','com_inward_stage_id','Completed Stage', domain="[('header_id','=',moc_id)]"),
			
		'qty': fields.integer('Quantity', required=True),
		'pending_qty': fields.integer('Pending Qty'),
		'each_weight': fields.related('fettling_id','each_weight', type='float', string='Weight(kgs)', store=True, readonly=True),
		'seq_no':fields.integer('Sequence'),				
		'remarks': fields.text('Remarks'),		
		'state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')],'Status', readonly=True),	
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_invoice': fields.boolean('Invoice Flag'),		
	}
	
	_defaults = {		
		'state': 'pending',
		'entry_mode': 'manual',		
		'flag_invoice': False,		
	}

ch_fettling_inward_line()	


