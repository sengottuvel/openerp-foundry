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


class kg_machineshop(osv.osv):

	_name = "kg.machineshop"
	_description = "MS Inward"
	_order = "order_priority,entry_date asc"
	
	def _get_default_division(self, cr, uid, context=None):
		res = self.pool.get('kg.division.master').search(cr, uid, [('code','=','SAM'),('state','=','approved'), ('active','=','t')], context=context)
		return res and res[0] or False
		
	def _get_pending_qty(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		for entry in self.browse(cr, uid, ids, context=context):
			if entry.ms_type == 'foundry_item':
				pending_qty = entry.fettling_qty - entry.inward_accept_qty
				result[entry.id] = pending_qty
			else:
				result[entry.id] = 0
		return result
		
	def _get_each_weight(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		wgt = 0.00
		
		for entry in self.browse(cr, uid, ids, context=context):
			
			if entry.moc_id.weight_type == 'ci':
				wgt = entry.pattern_id.ci_weight
			if entry.moc_id.weight_type == 'ss':
				wgt = entry.pattern_id.pcs_weight
			if entry.moc_id.weight_type == 'non_ferrous':
				wgt = entry.pattern_id.nonferous_weight
				
		result[entry.id]= wgt
		
		return result
		
	def _get_total_weight(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		total_weight = 0.00
		for entry in self.browse(cr, uid, ids, context=context):
			total_weight = entry.inward_accept_qty * entry.each_weight		
		result[entry.id]= total_weight
		return result
	
	_columns = {
	
		### Schedule List ####
		'name': fields.char('MS Inward No', size=128,select=True,readonly=True),
		'entry_date': fields.date('MS Inward Date',required=True),
		'division_id': fields.many2one('kg.division.master','Division'),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location'),
		'active': fields.boolean('Active'),
		
		### Schedule Details ###
		'schedule_id': fields.many2one('kg.schedule','Schedule No.'),
		'schedule_date': fields.related('schedule_id','entry_date', type='date', string='Schedule Date', store=True, readonly=True),
		'schedule_line_id': fields.many2one('ch.schedule.details','Schedule Line Item'),
		
		### Work Order Details ###
		'order_bomline_id': fields.many2one('ch.order.bom.details','Order BOM Line Id',readonly=True),
		'order_id': fields.many2one('kg.work.order','Work Order'),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line'),
		'order_no': fields.related('order_line_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('order_line_id','delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'order_date': fields.related('order_id','entry_date', type='date', string='Order Date', store=True, readonly=True),
		'order_category': fields.related('order_line_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.selection(ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		
		'pump_model_id': fields.related('order_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		#~ 'pattern_id': fields.related('schedule_line_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_id':fields.many2one('kg.pattern.master','Pattern Number', readonly=True),
		'pattern_code': fields.related('pattern_id','name', type='char', string='Pattern Code', store=True, readonly=True),
		'pattern_name': fields.related('pattern_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		#~ 'moc_id': fields.related('schedule_line_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'moc_id':fields.many2one('kg.moc.master','MOC'),
		'schedule_qty': fields.related('schedule_line_id','qty', type='integer', size=100, string='Schedule Qty', store=True, readonly=True),
		'fettling_id':fields.many2one('kg.fettling','Fettling'),
		'melting_id': fields.related('fettling_id','melting_id', type='many2one', relation='kg.melting', string='Heat No.', store=True, readonly=True),
		'production_id': fields.related('fettling_id','production_id', type='many2one', relation='kg.production', string='Production No.', store=True, readonly=True),
		'fettling_qty': fields.integer('Fettling Qty',readonly=True),
		'stage_id':fields.many2one('kg.stage.master','Stage'),
		'stage_name': fields.related('stage_id','name', type='char', size=128, string='Stage Name', store=True, readonly=True ),
		
		#### MS Inward ####
		'inward_accept_qty': fields.integer('Accepted Qty'),
		'inward_reject_qty': fields.integer('Rejected Qty'),
		'inward_accept_user_id': fields.many2one('res.users', 'Accepted By'),
		'inward_reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		'inward_remarks': fields.text('Remarks'),
		'inward_pending_qty': fields.function(_get_pending_qty, string='Pending Qty', method=True, store=True, type='integer'),
		'each_weight': fields.function(_get_each_weight, string='Each Weight(Kgs)', method=True, store=True, type='float'),
		'total_weight': fields.function(_get_total_weight, string='Total Weight(Kgs)', method=True, store=True, type='float'),
		'state': fields.selection([('waiting','Waiting for Accept'),('raw_pending','Pending'),('accept','Accepted')],'Status', readonly=True),
		'accept_date': fields.date('Accepted Date',required=True),
		
		### MS Inward Schedule List ###
		'ms_sch_qty': fields.integer('Schedule Qty', required=True),
		'ms_type': fields.selection([('foundry_item','Foundry Item'),('ms_item','MS Item')],'MS Type'),
		'order_ms_line_id': fields.many2one('ch.order.machineshop.details','Machine shop Line Id'),
		'acc_ms_line_id': fields.many2one('ch.wo.accessories.ms','Acc Machine shop Line Id'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code'),
		'ms_bom_id': fields.many2one('kg.bom','BOM'),
		'ms_bom_line_id':fields.many2one('ch.machineshop.details', 'Machine Shop Id'),
		'position_id': fields.many2one('kg.position.number','Position No',domain="[('active','=','t')]"),
		'ms_state': fields.selection([
		('in_plan','Planning In Progress'),
		('op_progress','Operation In Progress'),
		('op_completed','Operations Completed'),
		('op_rejected','Operations Rejected'),
		('sent_to_store','Sent to MS Store'),
		
		],'MS Status', readonly=True),
		'item_code': fields.char('Item Code', size=128),
		'item_name': fields.char('Item Name', size=128),
		'ms_completed_qty': fields.integer('MS Operation Completed Qty'),
		'ms_rejected_qty': fields.integer('MS Operation Rejected Qty'),
		'ms_plan_qty': fields.integer('Planning Completed Qty'),
		'assembly_id': fields.integer('Assembly Inward', readonly=True),
		'assembly_line_id': fields.integer('Assembly Inward Line', readonly=True),
		

		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
				
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_machineshop', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'division_id':_get_default_division,
		### MS Inward ###
		#~ 'inward_accept_user_id':lambda obj, cr, uid, context: uid,
		'accept_date': lambda * a: time.strftime('%Y-%m-%d'),
		
		
	}
	
	def _check_qty(self, cr, uid, ids, context=None):		
		entry_rec = self.browse(cr, uid, ids[0])
		if (entry_rec.inward_accept_qty + entry_rec.inward_reject_qty) > entry_rec.fettling_qty:
			return False
		if (entry_rec.inward_accept_qty + entry_rec.inward_reject_qty) < entry_rec.fettling_qty:
			return False					
		return True
		
	_constraints = [
	
		(_check_qty,'Accept and Reject qty should not exceed Schedule Qty !',['Accept and Reject Qty']),
		
		]
	
	def ms_accept(self,cr,uid,ids, context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		reject_qty = entry_rec.fettling_qty - entry_rec.inward_accept_qty 
		production_obj = self.pool.get('kg.production')
		
		if entry_rec.state == 'waiting':
			
			today = date.today()
			today = str(today)
			today = datetime.strptime(today, '%Y-%m-%d')
			accept_date = entry_rec.accept_date
			accept_date = str(accept_date)
			accept_date = datetime.strptime(accept_date, '%Y-%m-%d')
			if accept_date > today:
				raise osv.except_osv(_('Warning!'),
						_('Accepted date should be less than or equal to current date !!'))
						
			if entry_rec.inward_accept_qty < 0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative values !!'))
			
			if (entry_rec.inward_accept_qty + entry_rec.inward_reject_qty) > entry_rec.fettling_qty:
				raise osv.except_osv(_('Warning!'),
							_('Accept and Reject qty should not exceed Schedule Qty !!'))
							
			if (entry_rec.inward_accept_qty + entry_rec.inward_reject_qty) < entry_rec.fettling_qty:
				raise osv.except_osv(_('Warning!'),
							_('Accept and Reject qty should be equal to Schedule Qty !!'))
							
			if entry_rec.inward_reject_qty > 0 and not entry_rec.inward_reject_remarks_id:
				raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
			
			if reject_qty > 0:
				#### NC Creation for reject Qty ###
				
				### Production Number ###
				produc_name = ''	
				produc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.production')])
				rec = self.pool.get('ir.sequence').browse(cr,uid,produc_seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(produc_seq_id[0],rec.code,entry_rec.entry_date))
				produc_name = cr.fetchone();
				
				### Issue Number ###
				issue_name = ''	
				issue_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pattern.issue')])
				rec = self.pool.get('ir.sequence').browse(cr,uid,issue_seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(issue_seq_id[0],rec.code,entry_rec.entry_date))
				issue_name = cr.fetchone();
				
				### Core Log Number ###
				core_name = ''	
				core_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.log')])
				rec = self.pool.get('ir.sequence').browse(cr,uid,core_seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_seq_id[0],rec.code,entry_rec.entry_date))
				core_name = cr.fetchone();
				
				### Mould Log Number ###
				mould_name = ''	
				mould_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.log')])
				rec = self.pool.get('ir.sequence').browse(cr,uid,mould_seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_seq_id[0],rec.code,entry_rec.entry_date))
				mould_name = cr.fetchone();
				
				production_vals = {
										
					'name': produc_name[0],
					'schedule_id': entry_rec.schedule_id.id,
					'schedule_date': entry_rec.schedule_date,
					'division_id': entry_rec.division_id.id,
					'location' : entry_rec.location,
					'schedule_line_id': entry_rec.schedule_line_id.id,
					'order_id': entry_rec.order_id.id,
					'order_line_id': entry_rec.order_line_id.id,
					'qty' : reject_qty,			  
					'schedule_qty' : reject_qty,				  
					'state' : 'issue_done',
					'order_category':entry_rec.order_category,
					'order_priority': '2',
					'pattern_id' : entry_rec.pattern_id.id,
					'pattern_name' : entry_rec.pattern_id.pattern_name,	
					'moc_id' : entry_rec.moc_id.id,
					'request_state': 'done',
					'issue_no': issue_name[0],
					'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
					'issue_qty': 1,
					'issue_state': 'issued',
					'core_no': core_name[0],
					'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
					'core_qty': reject_qty,		
					'core_rem_qty': reject_qty,	
					'core_state': 'pending',
					'mould_no': mould_name[0],
					'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
					'mould_qty': reject_qty,	
					'mould_rem_qty': reject_qty,	
					'mould_state': 'pending',		
				}
				production_id = production_obj.create(cr, uid, production_vals) 
			
			self.write(cr,uid, ids,{'state':'accept','ms_state':'in_plan','ms_sch_qty':entry_rec.inward_accept_qty,'inward_reject_qty':reject_qty,
			'accept_date':today})
		else:
			pass
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(kg_machineshop, self).write(cr, uid, ids, vals, context)
	
kg_machineshop()


class kg_ms_batch_accept(osv.osv):

	_name = "kg.ms.batch.accept"
	_description = "MS Batch Accept"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Batch No.', size=128,select=True),
		'entry_date': fields.date('Batch Date',required=True),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed')],'Status', readonly=True),

		'ms_line_ids':fields.many2many('kg.machineshop','m2m_ms_inward_details' , 'batch_id', 'ms_id', 'MS Lines',
			domain="[('state','=','waiting')]"),
			
		'ms_inward_date': fields.date('MS Inward Date',required=True),
		'inward_accept_user_id': fields.many2one('res.users', 'QC By',required=True),
			
		'line_ids': fields.one2many('ch.ms.batch.accept.line', 'header_id', "MS Line Details"),
		
		'flag_msline':fields.boolean('MS Line Created'),
		
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_ms_batch_accept', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'ms_inward_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft'
		
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.entry_date)
		if entry_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
  
	   ]	

	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])		
		ms_obj = self.pool.get('kg.machineshop')
		line_obj = self.pool.get('ch.ms.batch.accept.line')
		
		del_sql = """ delete from ch_ms_batch_accept_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.ms_line_ids:
		
			for item in entry.ms_line_ids:
				
				
				vals = {
				
					'header_id': entry.id,
					'ms_id':item.id,
					'accept_qty':item.inward_accept_qty,
					'reject_qty':0,
					'remarks':entry.remarks,
					'ms_inward_date': entry.ms_inward_date,
					'accept_user_id': entry.inward_accept_user_id.id
				}
				
				line_id = line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_msline': True})
			
		return True
		
	def entry_accept(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		ms_obj = self.pool.get('kg.machineshop')
		if entry.state == 'draft':		
			if not entry.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to confirm without Line Items !!'))
							
							
			### Updation against Bactch Fettling Accept ###
			for accept_item in entry.line_ids:
				reject_qty = accept_item.schedule_qty - accept_item.accept_qty
				if accept_item.reject_qty > 0 and accept_item.reject_remarks_id.id == False:
					raise osv.except_osv(_('Warning!'),
					_('Remarks is must for Rejection !!'))
				
				ms_obj.write(cr, uid,accept_item.ms_id.id,{
				'inward_remarks':accept_item.remarks,
				'inward_accept_qty': accept_item.accept_qty,
				'inward_reject_qty': accept_item.reject_qty,
				'inward_accept_user_id': accept_item.accept_user_id.id,
				'inward_reject_remarks_id': accept_item.reject_remarks_id.id,
				'entry_date': accept_item.ms_inward_date,
				'inward_accept_user_id': accept_item.accept_user_id.id
				})
				ms_obj.ms_accept(cr, uid, [accept_item.ms_id.id])
				
			### Sequence Number Generation  ###
			ms_batch_name = ''	
			ms_batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.ms.batch.accept')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,ms_batch_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(ms_batch_seq_id[0],rec.code,entry.entry_date))
			ms_batch_name = cr.fetchone();
			self.write(cr, uid, ids, {'name':ms_batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_ms_batch_accept, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_ms_batch_accept()


class ch_ms_batch_accept_line(osv.osv):

	_name = "ch.ms.batch.accept.line"
	_description = "MS Batch Accept Line"
	
	_columns = {
	
		'header_id':fields.many2one('kg.ms.batch.accept', 'MS Batch Accept', required=1, ondelete='cascade'),		
		'ms_id':fields.many2one('kg.machineshop', 'MS Item'),
		
		'ms_inward_no': fields.related('ms_id','name', type='char', string='MS Inward No.', store=True, readonly=True),
		'ms_inward_date': fields.date('MS Inward Date',required=True),
		'schedule_qty': fields.related('ms_id','inward_accept_qty', type='integer', size=100, string='Schedule Qty', store=True, readonly=True),
		'accept_qty': fields.integer('Accepted Qty', required=True),
		'reject_qty': fields.integer('Rejected Qty'),
		'reject_user_id': fields.many2one('res.users', 'Rejected By'),
		'accept_user_id': fields.many2one('res.users', 'QC By'),
		'remarks': fields.text('Remarks'),
		'reject_remarks_id': fields.many2one('kg.rejection.master', 'Rejection Remarks'),
		
		
	}
	
	_defaults = {
	
		'reject_user_id':lambda obj, cr, uid, context: uid,
		'accept_user_id':lambda obj, cr, uid, context: uid,
		
	}
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_ms_batch_accept_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_ms_batch_accept_line, self).write(cr, uid, ids, vals, context)
		
		
	
ch_ms_batch_accept_line()
