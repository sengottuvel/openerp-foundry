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
   ('project','Project'),
   ('access','Accessories')
]


class kg_production(osv.osv):

	_name = "kg.production"
	_description = "Production Updation"
	_order = "order_priority,order_no asc"
	_rec_name = "pattern_code"
	
	def _get_default_division(self, cr, uid, context=None):
		res = self.pool.get('kg.division.master').search(cr, uid, [('code','=','SAM'),('state','=','approved'),('active','=','t')], context=context)
		return res and res[0] or False
		
		
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
			total_weight = entry.qty * entry.each_weight		
		result[entry.id]= total_weight
		return result
		
	def _get_difference_qty(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		diff_qty = 0.00
		for entry in self.browse(cr, uid, ids, context=context):
			diff_qty = entry.total_core_qty - entry.total_mould_qty		
		result[entry.id]= diff_qty
		return result
		
	def _get_pour_pending_qty(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		pending_qty = 0.00
		for entry in self.browse(cr, uid, ids, context=context):
			if entry.total_mould_qty > entry.qty:
				pending_qty = entry.total_mould_qty - entry.pour_qty
			else:
				pending_qty = entry.qty - entry.pour_qty
		
		result[entry.id]= pending_qty
		return result
	
	_columns = {
	
		### Schedule List ####
		'name': fields.char('Production No', size=128,select=True,readonly=True),
		'entry_date': fields.date('Production Date',required=True),
		'division_id': fields.many2one('kg.division.master','Division'),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location'),
		'note': fields.text('Notes'),
		'remarks': fields.text('Remarks'),
		'active': fields.boolean('Active'),
		
		
		### Schedule Details ###
		'schedule_id': fields.many2one('kg.schedule','Schedule No.'),
		'schedule_date': fields.related('schedule_id','entry_date', type='date', string='Schedule Date', store=True, readonly=True),
		'schedule_line_id': fields.many2one('ch.schedule.details','Schedule Line Item'),
		'sch_remarks': fields.text('Remarks'),
		
		### Work Order Details ###
		'order_bomline_id': fields.related('schedule_line_id','order_bomline_id', type='many2one', relation='ch.order.bom.details', string='Order BOM Line Id', store=True, readonly=True),
		'order_id': fields.many2one('kg.work.order','Work Order'),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line'),
		'allocation_id': fields.many2one('ch.stock.allocation.detail','Allocation'),
		'order_no': fields.related('order_line_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('order_line_id','delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'order_date': fields.related('order_id','entry_date', type='date', string='Order Date', store=True, readonly=True),
		'order_category': fields.related('order_line_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.selection(ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		'order_value': fields.related('order_id','order_value', type='float', string='WO Value', store=True, readonly=True),

		
		'pump_model_id': fields.related('order_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('schedule_line_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_code': fields.related('pattern_id','name', type='char', string='Pattern Code', store=True, readonly=True),
		'pattern_name': fields.related('pattern_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('schedule_line_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		#~ 'schedule_qty': fields.related('schedule_line_id','qty', type='integer', size=100, string='Schedule Qty', store=True, readonly=True),
		'schedule_qty': fields.integer('Schedule Qty', readonly=True),
		'qty': fields.integer('Qty', required=True),
		'each_weight': fields.function(_get_each_weight, string='Each Weight(Kgs)', method=True, store=True, type='float'),
		'total_weight': fields.function(_get_total_weight, string='Total Weight(Kgs)', method=True, store=True, type='float'),
		'assembly_id': fields.integer('Assembly Inward', readonly=True),
		'assembly_line_id': fields.integer('Assembly Inward Line', readonly=True),
		
		### Status Field ###
		
		'state': fields.selection([
		('issue_pending','Issue Pending'),
		('issue_done','Issue Done'),
		('mould_com','Moulding Completed'),
		('pour_pending','Pouring Pending'),
		('pour_com','Pouring Completed'),
		('casting_com','Casting Completed'),
		('fettling_inprogress','Fettling In Progress'),
		('fettling_com','Fettling Completed'),
		('moved_to_ms','Moved to MS')],'Status', readonly=True),
		
		
		#### Pattern Request ###
		'request_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')],'Pattern Request Status', readonly=True),
		
		### Pattern Issue ###
		'issue_no': fields.char('Issue No', size=128,readonly=True),
		'issue_date': fields.date('Issue Date'),
		'issue_qty': fields.integer('Issue Qty'),
		'issue_state': fields.selection([('pending','Pending'),('partial','Partial'),('issued','Issued')],'Status', readonly=True),
		'issue_remarks': fields.text('Remarks'),
		
		### Pattern Return ###
		'return_state': fields.selection([('pending','Pending'),('partial','Partial'),('received','Received')],'Status', readonly=True),
		
		### Core Log ###
		'core_no': fields.char('Core Log No.', size=128,readonly=True),
		'core_date': fields.date('Date'),
		'core_shift_id':fields.many2one('kg.shift.master','Shift'),
		'core_contractor':fields.many2one('res.partner','Contractor'),
		'core_moulder': fields.integer('Moulder'),
		'core_helper': fields.integer('Helper'),
		'core_operator': fields.char('Operator',size=128),
		'core_qty': fields.integer('Qty'),
		'total_core_qty': fields.integer('Total Core Qty'),
		'core_rem_qty': fields.integer('Remaining Qty', readonly=True),
		'core_hardness': fields.char('Core Hardness'),
		'core_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')],'Status', readonly=True),
		'core_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'core_pan_no':fields.char('PAN No.', size=128),
		'core_remarks': fields.text('Remarks'),
		
		
		### Mould Log ###
		'mould_no': fields.char('Mould Log No.', size=128,readonly=True),
		'mould_date': fields.date('Date'),
		'mould_shift_id':fields.many2one('kg.shift.master','Shift'),
		'mould_contractor':fields.many2one('res.partner','Contractor'),
		'mould_moulder': fields.integer('Moulder'),
		'mould_box_id': fields.related('pattern_id','box_id', type='many2one', relation='kg.box.master', string='Box Size', store=True),
		'mould_helper': fields.integer('Helper'),
		'mould_operator': fields.char('Operator',size=128),
		'mould_qty': fields.integer('Qty'),
		'total_mould_qty': fields.integer('Total Mould Qty'),
		'mould_rem_qty': fields.integer('Remaining Qty', readonly=True),
		'mould_hardness': fields.char('Mould Hardness'),
		'mould_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')],'Status', readonly=True),
		'mould_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'mould_pan_no':fields.char('PAN No.', size=128),
		'mould_remarks': fields.text('Remarks'),
		
		### Pouring Log ###
		'pour_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')],'Status', readonly=True),
		'pour_qty': fields.integer('Qty'),
		'pour_weight':fields.integer('Weight(kgs)'),
		'pour_heat_id':fields.many2one('kg.melting','Heat Id',domain="[('state','=','confirmed'), ('active','=','t')]"),
		'pour_remarks': fields.text('Remarks'),
		'pour_date': fields.datetime('Pouring Date'),
		'pour_pending_qty': fields.function(_get_pour_pending_qty, string='Pending Qty', store=True, type='integer'),
		'fettling_reject_qty': fields.integer('Rejected Qty'),
		
		'pour_pending_remarks': fields.text('Remarks'),
		'fettling_progress_remarks': fields.text('Remarks'),
		
		### Core vs Mould Qty ###
		'difference_qty': fields.function(_get_difference_qty, string='Difference', store=True, type='float'),
		'allocated_wo': fields.text('Allocated WO'),
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
				
		'issue_user_id': fields.many2one('res.users', 'Issue Done By', readonly=True),
		
		'core_user_id': fields.many2one('res.users', 'Core Done By', readonly=True),
		
		'mould_user_id': fields.many2one('res.users', 'Mould Done By', readonly=True),
		
			
		
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_production', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'issue_pending',		
		'active': True,
		'request_state':'done', 
		'return_state':'received', 
		'pour_state':'pending', 
		'division_id':_get_default_division,
		'issue_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'core_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'mould_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'difference_qty': 0,
		'pour_qty': 0
		
	}
	
	def pattern_issue_update(self,cr,uid,ids,context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		
		if entry_rec.issue_state in ('pending','partial'):
			today = datetime.today()
			issue_date = entry_rec.issue_date
			issue_date = str(issue_date)
			issue_date = datetime.strptime(issue_date, '%Y-%m-%d')
			if issue_date > today:
				raise osv.except_osv(_('Warning!'),
								_('System not allow to save with future date. !!'))
			
			### Core Log Number ###
			core_name = ''	
			core_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.log')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,core_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s',now()::date) """%(core_seq_id[0],rec.code))
			core_name = cr.fetchone();
			
			### Mould Log Number ###
			mould_name = ''	
			mould_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.log')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,mould_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s',now()::date) """%(mould_seq_id[0],rec.code))
			mould_name = cr.fetchone();
			
			self.write(cr, uid, ids,{
			'core_no': core_name[0],
			'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
			'core_qty': entry_rec.qty,
			'core_rem_qty': entry_rec.qty,
			'core_state': 'pending',
			'core_remarks': entry_rec.order_bomline_id.add_spec,
			'mould_no': mould_name[0],
			'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
			'mould_qty': entry_rec.qty,
			'mould_rem_qty': entry_rec.qty,
			'mould_state': 'pending',
			'core_remarks': entry_rec.order_bomline_id.add_spec,
			'state' : 'issue_done',
			'issue_state' : 'issued',
			})
		else:
			pass
		return True
		
	def core_update(self,cr,uid,ids,context=None):
		
		entry_rec = self.browse(cr, uid, ids[0])
		
		if entry_rec.core_state == 'pending':
			
			today = datetime.today()
			core_date = entry_rec.core_date
			core_date = str(core_date)
			core_date = datetime.strptime(core_date, '%Y-%m-%d')
			if core_date > today:
				raise osv.except_osv(_('Warning!'),
								_('System not allow to save with future date. !!'))
			if entry_rec.core_by == 'comp_employee':
				if entry_rec.core_helper <= 0 or entry_rec.core_helper <= 0 or entry_rec.core_qty <=0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative or zero values !!'))
								
			if entry_rec.core_qty <=0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
			
			sch_qty = entry_rec.qty
			total_core_qty = entry_rec.total_core_qty + entry_rec.core_qty
			if total_core_qty < sch_qty:
				core_state = 'partial'
			if total_core_qty >= sch_qty:
				core_state = 'done'
			#~ if total_core_qty > sch_qty:
				#~ raise osv.except_osv(_('Warning!'),
							#~ _('Core Qty should be greater than Schedule Qty !!'))
			if core_state == 'partial':
				core_entry_qty = 0
			else:
				core_entry_qty = entry_rec.core_qty
				
			### PAN No ###
			#~ upper_pan_no = ''
			#~ pan_no = entry_rec.core_pan_no
			#~ if pan_no:
				#~ upper_pan_no = (pan_no.upper())
			
			## Remaining Qty ###
			remain_qty = entry_rec.qty - total_core_qty
			
			if remain_qty < 0:
				remain_qty = 0
			else:
				remain_qty = remain_qty
				
				
			self.write(cr, uid, ids,{
			'core_state': core_state,
			'total_core_qty':total_core_qty,
			'core_qty':core_entry_qty,
			'core_rem_qty':remain_qty,
			'core_user_id':uid,
			#~ 'core_pan_no':upper_pan_no
			})
		else:
			pass
		return True
		
	def mould_update(self,cr,uid,ids,context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		
		if entry_rec.mould_state in ('pending','partial'):
			today = datetime.today()
			mould_date = entry_rec.mould_date
			mould_date = str(mould_date)
			mould_date = datetime.strptime(mould_date, '%Y-%m-%d')
			if mould_date > today:
				raise osv.except_osv(_('Warning!'),
								_('System not allow to save with future date. !!'))
			if entry_rec.mould_by == 'comp_employee':
				if entry_rec.mould_moulder <= 0 or entry_rec.mould_helper <= 0 or entry_rec.mould_qty <=0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative or zero values !!'))
								
			if entry_rec.mould_qty <=0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
			sch_qty = entry_rec.qty
			total_mould_qty = entry_rec.total_mould_qty + entry_rec.mould_qty
			if total_mould_qty < sch_qty:
				mould_state = 'partial'
				state = 'issue_done'
			if total_mould_qty >= sch_qty:
				mould_state = 'done'
				state = 'mould_com'
			#~ if total_mould_qty > sch_qty:
				#~ raise osv.except_osv(_('Warning!'),
							#~ _('Mould Qty should not be greater than Schedule Qty !!'))
							
			if mould_state == 'partial':
				mould_entry_qty = 0
			else:
				mould_entry_qty = entry_rec.mould_qty
				
			### PAN No ###
			#~ upper_pan_no = ''
			#~ pan_no = entry_rec.mould_pan_no
			#~ if pan_no:
				#~ upper_pan_no = (pan_no.upper())
				
			## Remaining Qty ###
			remain_qty = entry_rec.qty - total_mould_qty
			
			if remain_qty < 0:
				remain_qty = 0
			else:
				remain_qty = remain_qty
				
			self.write(cr, uid, ids,{
			
			'mould_state': mould_state,
			'total_mould_qty':total_mould_qty,
			'mould_qty':mould_entry_qty,
			'mould_rem_qty':remain_qty,
			'state':state,
			'mould_user_id':uid,
			#~ 'mould_pan_no':upper_pan_no
			})
		else:
			pass
		return True
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		entry_date = str(rec.entry_date)
		if entry_date > today:
			return False
		issue_date = str(rec.issue_date)
		if issue_date > today:
			return False
		core_date = str(rec.core_date)
		if core_date > today:
			return False
		mould_date = str(rec.mould_date)
		if mould_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		#~ (_future_entry_date_check, 'dddSystem not allow to save with future date. !!',['']),
  
	   ]
		
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):				
			raise osv.except_osv(_('Warning!'),
					_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({
		'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),
		'update_user_id':uid,
			})
		return super(kg_production, self).write(cr, uid, ids, vals, context)
	
	
kg_production()

class kg_pattern_batch_issue(osv.osv):

	_name = "kg.pattern.batch.issue"
	_description = "Pattern Batch Issue"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Batch No.', size=128,select=True),
		'entry_date': fields.date('Batch Date',required=True),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('issue','Issued')],'Status', readonly=True),

		'issue_line_ids':fields.many2many('kg.production','m2m_pattern_batch_issue_details' , 'batch_id', 'issue_id', 'Issue Lines',
			domain="[('state','=','issue_pending'),'&',('issue_state','=','pending')]"),
			
		'line_ids': fields.one2many('ch.pattern.batch.line', 'header_id', "Request Line Details"),
		
		'flag_issueline':fields.boolean('Issue Line Created'),

		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Issued Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Issued By', readonly=True),		
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),	
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_pattern_batch_issue', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
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
		production_obj = self.pool.get('kg.production')
		issue_line_obj = self.pool.get('ch.pattern.batch.line')
		
		del_sql = """ delete from ch_pattern_batch_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.issue_line_ids:
		
			for item in entry.issue_line_ids:
				
				
				vals = {
				
					'header_id': entry.id,
					'production_id':item.id,
					'qty':item.issue_qty,
					'remarks':entry.remarks
					
				}
				
				issue_line_id = issue_line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_issueline': True})
			
		return True
		
	def entry_issue(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			production_obj = self.pool.get('kg.production')		
			if not entry.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to confirm without Issue Items !!'))
							
							
			### Issue Updation against Pattern Issue ###
			
			for issue_item in entry.line_ids:
				production_obj.write(cr, uid,issue_item.production_id.id,{'issue_remarks':issue_item.remarks})
				production_obj.pattern_issue_update(cr, uid, [issue_item.production_id.id])
				
			### Issue Batch Sequence Number Generation  ###
			issue_batch_name = ''	
			issue_batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.batch.pattern.issue')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,issue_batch_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(issue_batch_seq_id[0],rec.code,entry.entry_date))
			issue_batch_name = cr.fetchone();
			self.write(cr, uid, ids, {'name':issue_batch_name[0],'state': 'issue','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_pattern_batch_issue, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_pattern_batch_issue()


class ch_pattern_batch_line(osv.osv):

	_name = "ch.pattern.batch.line"
	_description = "Pattern Batch Line"
	
	_columns = {
	
		'header_id':fields.many2one('kg.pattern.batch.issue', 'Pattern Batch Issue', required=1, ondelete='cascade'),		
		'production_id':fields.many2one('kg.production', 'Production'),
		
		'issue_no': fields.related('production_id','issue_no', type='char', string='Issue No.', store=True, readonly=True),
		'order_no': fields.related('production_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('production_id','order_delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'order_date': fields.related('production_id','order_date', type='date', string='Order Date', store=True, readonly=True),
		
		'pump_model_id': fields.related('production_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('production_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('production_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'qty': fields.related('production_id','issue_qty', type='integer', string='Issue Qty', store=True, readonly=True),
		
		'remarks': fields.text('Remarks'),	
		
		
	}
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_pattern_batch_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_pattern_batch_line, self).write(cr, uid, ids, vals, context)
		
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty == 0 or entry.qty < 0:
			return False
		return True
		
		
	_constraints = [		
			  
		(_check_values, 'System not allow to save with zero and less than zero qty .!!',['Quantity']),
		
	   
		
	   ]
	
ch_pattern_batch_line()

class kg_core_batch(osv.osv):

	_name = "kg.core.batch"
	_description = "Core Batch Update"
	
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Batch No.', size=128,select=True),
		'entry_date': fields.date('Batch Date',required=True),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed')],'Status', readonly=True),

		'core_line_ids':fields.many2many('kg.production','m2m_core_batch_details' , 'batch_id', 'core_id', 'Issue Lines',
			domain="[('core_state','in',('pending','partial'))]"),
			
		'line_ids': fields.one2many('ch.core.batch.line', 'header_id', "Request Line Details"),
		
		'flag_issueline':fields.boolean('Issue Line Created'),
		
		'core_date': fields.date('Core Date'),
		'core_shift_id':fields.many2one('kg.shift.master','Shift'),
		'core_contractor':fields.many2one('res.partner','Contractor'),
		'core_operator': fields.integer('Operator'),
		'core_helper': fields.integer('Helper'),
		'core_hardness': fields.char('Core Hardness'),
		'core_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'core_pan_no':fields.char('PAN No.', size=128),

		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Issued Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Issued By', readonly=True),		
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),	
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_core_batch', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'core_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
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
		production_obj = self.pool.get('kg.production')
		core_line_obj = self.pool.get('ch.core.batch.line')
		
		del_sql = """ delete from ch_core_batch_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.core_line_ids:
		
			for item in entry.core_line_ids:
				
				core_qty = item.qty - item.total_core_qty
				
				vals = {
				
					'header_id': entry.id,
					'production_id':item.id,
					'core_qty':core_qty,
					'production_qty':core_qty,
					'core_date': entry.core_date,
					'core_shift_id': entry.core_shift_id.id,
					'core_contractor':entry.core_contractor.id,
					'core_operator': entry.core_operator,
					'core_helper': entry.core_helper,
					'core_hardness': entry.core_hardness,
					'remarks':entry.remarks,
					'core_by':entry.core_by,
					#~ 'core_pan_no':entry.core_pan_no,
					
				}
				
				core_line_id = core_line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_issueline': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			production_obj = self.pool.get('kg.production')		
			if not entry.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to confirm without Issue Items !!'))
							
							
			### Core Updation ###
			
			for req_item in entry.line_ids:
				production_obj.write(cr, uid,req_item.production_id.id,{'core_remarks':req_item.remarks,'core_date':req_item.core_date,
				'core_shift_id':req_item.core_shift_id.id,'core_contractor':req_item.core_contractor.id,'core_operator':req_item.core_operator,
				'core_helper':req_item.core_helper,'core_qty':req_item.core_qty,'core_hardness':req_item.core_hardness,
				'core_by':req_item.core_by
				})
				production_obj.core_update(cr, uid, [req_item.production_id.id])
				
			### Core Batch Sequence Number Generation  ###
			core_batch_name = ''	
			core_batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.batch')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,core_batch_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_batch_seq_id[0],rec.code,entry.entry_date))
			core_batch_name = cr.fetchone();
			self.write(cr, uid, ids, {'name':core_batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_core_batch, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_core_batch()


class ch_core_batch_line(osv.osv):

	_name = "ch.core.batch.line"
	_description = "Core Batch Line"
	
	
	
	_columns = {
	
		'header_id':fields.many2one('kg.core.batch', 'Core Batch', required=1, ondelete='cascade'),		
		'production_id':fields.many2one('kg.production', 'Production'),
		
		'core_no': fields.related('production_id','core_no', type='char', string='Core No.', store=True, readonly=True),
		'order_no': fields.related('production_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('production_id','order_delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		
		'core_date': fields.date('Core Date'),
		'core_shift_id':fields.many2one('kg.shift.master','Shift'),
		'core_contractor':fields.many2one('res.partner','Contractor'),
		'core_operator': fields.integer('Operator'),
		'core_helper': fields.integer('Helper'),
		'core_qty': fields.integer('Completed Qty'),
		'core_hardness': fields.char('Core Hardness'),
		'core_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'production_qty': fields.integer('Production Qty'),
		'core_pan_no':fields.char('PAN No.', size=128),
		
		'pump_model_id': fields.related('production_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('production_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('production_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('production_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		
		
		'remarks': fields.text('Remarks'),	
		
		
	}
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_core_batch_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_core_batch_line, self).write(cr, uid, ids, vals, context)
		
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.core_qty == 0 or entry.core_qty < 0:
			return False
		return True
		
		
	_constraints = [		
			  
		(_check_values, 'System not allow to save with zero and less than zero qty .!!',['Quantity']),
		
	   
		
	   ]
	
ch_core_batch_line()




class kg_mould_batch(osv.osv):

	_name = "kg.mould.batch"
	_description = "Mould Batch Update"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Batch No.', size=128,select=True),
		'entry_date': fields.date('Batch Date',required=True),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed')],'Status', readonly=True),

		'mould_line_ids':fields.many2many('kg.production','m2m_mould_batch_details' , 'batch_id', 'mould_id', 'Issue Lines',
			domain="[('mould_state','in',('pending','partial'))]"),
			
		'line_ids': fields.one2many('ch.mould.batch.line', 'header_id', "Request Line Details"),
		
		'flag_issueline':fields.boolean('Issue Line Created'),
		
		'mould_date': fields.date('Mould Date'),
		'mould_shift_id':fields.many2one('kg.shift.master','Shift'),
		'mould_contractor':fields.many2one('res.partner','Contractor'),
		'mould_moulder': fields.integer('Moulder'),
		'mould_operator': fields.integer('Operator'),
		'mould_helper': fields.integer('Helper Count'),
		'mould_qty': fields.integer('Qty'),		
		'mould_hardness': fields.char('Mould Hardness'),
		'mould_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'mould_pan_no':fields.char('PAN No.', size=128),

		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Issued Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Issued By', readonly=True),		
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),	
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_mould_batch', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'mould_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
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
		production_obj = self.pool.get('kg.production')
		mould_line_obj = self.pool.get('ch.mould.batch.line')
		
		del_sql = """ delete from ch_mould_batch_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.mould_line_ids:
		
			for item in entry.mould_line_ids:
				
				mould_qty = item.qty - item.total_mould_qty
				
				vals = {
				
					'header_id': entry.id,
					'production_id':item.id,
					'mould_qty':mould_qty,
					'production_qty':mould_qty,
					'mould_date': entry.mould_date,
					'mould_shift_id':entry.mould_shift_id.id,
					'mould_contractor':entry.mould_contractor.id,
					'mould_moulder': entry.mould_moulder,
					'mould_operator': entry.mould_operator,
					'mould_helper': entry.mould_helper,
					'mould_hardness': entry.mould_hardness,
					'remarks':entry.remarks,
					'mould_by':entry.mould_by,
					#~ 'mould_pan_no':entry.mould_pan_no,
					
				}
				
				mould_line_id = mould_line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_issueline': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			production_obj = self.pool.get('kg.production')		
			if not entry.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to confirm without Mould Items !!'))
							
							
			### Issue Creation against Mould Issue ###
			
			for req_item in entry.line_ids:
				production_obj.write(cr, uid,req_item.production_id.id,{'mould_remarks':req_item.remarks,'mould_date':req_item.mould_date,
				'mould_shift_id':req_item.mould_shift_id.id,'mould_contractor':req_item.mould_contractor.id,'mould_moulder':req_item.mould_moulder,
				'mould_helper':req_item.mould_helper,'mould_qty':req_item.mould_qty,'mould_hardness':req_item.mould_hardness,'mould_box_id':req_item.mould_box_id.id,
				'mould_by':req_item.mould_by,'mould_operator':req_item.mould_operator})
				production_obj.mould_update(cr, uid, [req_item.production_id.id])
				
			### Mould Batch Sequence Number Generation  ###
			mould_batch_name = ''	
			mould_batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.batch')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,mould_batch_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_batch_seq_id[0],rec.code,entry.entry_date))
			mould_batch_name = cr.fetchone();
			self.write(cr, uid, ids, {'name':mould_batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_mould_batch, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_mould_batch()


class ch_mould_batch_line(osv.osv):

	_name = "ch.mould.batch.line"
	_description = "Mould Batch Line"

	
	_columns = {
	
		'header_id':fields.many2one('kg.mould.batch', 'Mould Batch', required=1, ondelete='cascade'),		
		'production_id':fields.many2one('kg.production', 'Production'),
		
		'mould_no': fields.related('production_id','mould_no', type='char', string='Mould No.', store=True, readonly=True),
		'order_no': fields.related('production_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('production_id','order_delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
				
		'mould_date': fields.date('Mould Date'),
		'mould_shift_id':fields.many2one('kg.shift.master','Shift'),
		'mould_contractor':fields.many2one('res.partner','Contractor'),
		'mould_moulder': fields.integer('Moulder'),
		'mould_helper': fields.integer('Helper'),
		'mould_operator': fields.integer('Operator'),
		'mould_qty': fields.integer('Completed Qty'),		
		'mould_hardness': fields.char('Mould Hardness'),
		'mould_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'mould_pan_no':fields.char('PAN No.', size=128),
		'production_qty': fields.integer('Production Qty'),		
		
		'pump_model_id': fields.related('production_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('production_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('production_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'mould_box_id': fields.related('pattern_id','box_id', type='many2one', relation='kg.box.master', string='Box Size', store=True, readonly=True),
		'moc_id': fields.related('production_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'remarks': fields.text('Remarks'),	
		
		
	}
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_mould_batch_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_mould_batch_line, self).write(cr, uid, ids, vals, context)
		
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.mould_qty == 0 or entry.mould_qty < 0:
			return False
		return True
		
		
	_constraints = [		
			  
		(_check_values, 'System not allow to save with zero and less than zero qty .!!',['Quantity']),	   
		
	   ]
	
ch_mould_batch_line()














