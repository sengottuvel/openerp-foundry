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


class kg_production(osv.osv):

	_name = "kg.production"
	_description = "Production Updation"
	_order = "order_priority asc"
	_rec_name = "pattern_code"
	
	def _get_default_division(self, cr, uid, context=None):
		res = self.pool.get('kg.division.master').search(cr, uid, [('code','=','SAM'),('state','=','approved'), ('active','=','t')], context=context)
		return res and res[0] or False
	
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
		
		'pump_model_id': fields.related('order_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('schedule_line_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_code': fields.related('pattern_id','name', type='char', string='Pattern Code', store=True, readonly=True),
		'pattern_name': fields.related('pattern_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'moc_id': fields.related('schedule_line_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'schedule_qty': fields.related('schedule_line_id','qty', type='integer', size=100, string='Schedule Qty', store=True, readonly=True),
		'qty': fields.integer('Qty', required=True),
		
		### Status Field ###
		
		'state': fields.selection([
		('issue_pending','Issue Pending'),
		('issue_done','Issue Done'),
		('mould_com','Moulding Completed'),
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
		'core_date': fields.date('Core Date'),
		'core_shift_id':fields.many2one('kg.shift.master','Shift'),
		'core_contractor':fields.many2one('kg.contractor.master','Contractor'),
		'core_moulder': fields.integer('Moulder'),
		'core_helper': fields.integer('Helper'),
		'core_operator': fields.char('Operator',size=128),
		'core_qty': fields.integer('Qty'),
		'total_core_qty': fields.integer('Total Core Qty'),
		'core_hardness': fields.char('Core Hardness'),
		'core_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')],'Status', readonly=True),
		'core_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Core By'),
		'core_remarks': fields.text('Remarks'),
		
		### Mould Log ###
		'mould_no': fields.char('Mould Log No.', size=128,readonly=True),
		'mould_date': fields.date('Mould Date'),
		'mould_shift_id':fields.many2one('kg.shift.master','Shift'),
		'mould_contractor':fields.many2one('kg.contractor.master','Contractor'),
		'mould_moulder': fields.integer('Moulder'),
		'mould_box_id': fields.related('pattern_id','box_id', type='many2one', relation='kg.box.master', string='Box Size', store=True),
		'mould_helper': fields.integer('Helper'),
		'mould_operator': fields.char('Operator',size=128),
		'mould_qty': fields.integer('Qty'),
		'total_mould_qty': fields.integer('Total Mould Qty'),
		'mould_hardness': fields.char('Mould Hardness'),
		'mould_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')],'Status', readonly=True),
		'mould_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Mould By'),
		'mould_remarks': fields.text('Remarks'),
		
		### Pouring Log ###
		'pour_state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')],'Status', readonly=True),
		'pour_qty': fields.integer('Qty'),
		'pour_weight':fields.integer('Weight(kgs)'),
		'pour_heat_id':fields.many2one('kg.melting','Heat Id',domain="[('state','=','confirmed'), ('active','=','t')]"),
		'pour_remarks': fields.text('Remarks'),
		
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
		
	}
	
	def pattern_issue_update(self,cr,uid,ids,context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		
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
		'core_state': 'pending',
		'mould_no': mould_name[0],
		'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
		'mould_qty': entry_rec.qty,
		'mould_state': 'pending',
		'state' : 'issue_done',
		'issue_state' : 'issued',
		})
		return True
		
	def core_update(self,cr,uid,ids,context=None):
		
		entry_rec = self.browse(cr, uid, ids[0])
		if entry_rec.core_by == 'comp_employee':
			if entry_rec.core_moulder <= 0 or entry_rec.core_helper <= 0 or entry_rec.core_qty <=0:
				raise osv.except_osv(_('Warning!'),
							_('System not allow to save negative or zero values !!'))
							
		if entry_rec.core_qty <=0:
			raise osv.except_osv(_('Warning!'),
						_('System not allow to save negative or zero values !!'))
		
		sch_qty = entry_rec.qty
		total_core_qty = entry_rec.total_core_qty + entry_rec.core_qty
		if total_core_qty < sch_qty:
			core_state = 'partial'
		if total_core_qty == sch_qty:
			core_state = 'done'
		if total_core_qty > sch_qty:
			raise osv.except_osv(_('Warning!'),
						_('Core Qty should be greater than Schedule Qty !!'))
		if core_state == 'partial':
			core_entry_qty = 0
		else:
			core_entry_qty = entry_rec.core_qty
			
		self.write(cr, uid, ids,{
		'core_state': core_state,
		'total_core_qty':total_core_qty,
		'core_qty':core_entry_qty,
		'core_user_id':uid
		})
		return True
		
	def mould_update(self,cr,uid,ids,context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		
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
		if total_mould_qty == sch_qty:
			mould_state = 'done'
			state = 'mould_com'
		if total_mould_qty > sch_qty:
			raise osv.except_osv(_('Warning!'),
						_('Mould Qty should be greater than Schedule Qty !!'))
						
		if mould_state == 'partial':
			mould_entry_qty = 0
		else:
			mould_entry_qty = entry_rec.mould_qty
			
		self.write(cr, uid, ids,{
		
		'mould_state': mould_state,
		'total_mould_qty':total_mould_qty,
		'mould_qty':mould_entry_qty,
		'state':state,
		'mould_user_id':uid
		})
		return True
		
	def fettling_inward_update(self,cr,uid,ids,context=None):
		entry_rec = self.browse(cr, uid, ids[0])
		fettling_obj = self.pool.get('kg.fettling')
		
		### Sequence Number Generation ###
		fettling_name = ''	
		fettling_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.fettling.inward')])
		seq_rec = self.pool.get('ir.sequence').browse(cr,uid,fettling_seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(fettling_seq_id[0],seq_rec.code))
		fettling_name = cr.fetchone();
		
		fettling_vals = {
		'name': fettling_name[0],
		'location':entry_rec.location,
		'schedule_id':entry_rec.schedule_id.id,
		'schedule_date':entry_rec.schedule_date,
		'schedule_line_id':entry_rec.schedule_line_id.id,
		'order_bomline_id':entry_rec.order_bomline_id.id,
		'order_id':entry_rec.order_id.id,
		'order_line_id':entry_rec.order_line_id.id,
		'order_no':entry_rec.order_no,
		'order_delivery_date':entry_rec.order_delivery_date,
		'order_date':entry_rec.order_date,
		'order_category':entry_rec.order_category,
		'order_priority':entry_rec.order_priority,
		'pump_model_id':entry_rec.pump_model_id.id,
		'pattern_id':entry_rec.pattern_id.id,
		'pattern_code':entry_rec.pattern_code,
		'pattern_name':entry_rec.pattern_name,
		'moc_id':entry_rec.moc_id.id,
		'schedule_qty':entry_rec.schedule_qty,
		'production_id':entry_rec.id,
		'pour_qty':entry_rec.pour_qty,
		'inward_accept_qty':entry_rec.pour_qty,
		'state':'waiting'
		
		}
			
		fettling_id = fettling_obj.create(cr, uid, fettling_vals)
		
		self.write(cr, uid, ids, {'state': 'fettling_inprogress'})

		return True
	
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
					
				}
				
				issue_line_id = issue_line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_issueline': True})
			
		return True
		
	def entry_issue(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
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
		'active': True,
		'state':'draft'
		
		
	}	

	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])		
		production_obj = self.pool.get('kg.production')
		core_line_obj = self.pool.get('ch.core.batch.line')
		
		del_sql = """ delete from ch_core_batch_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.core_line_ids:
		
			for item in entry.core_line_ids:
				
				
				vals = {
				
					'header_id': entry.id,
					'production_id':item.id,
					'core_qty':item.qty,
					
				}
				
				core_line_id = core_line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_issueline': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		production_obj = self.pool.get('kg.production')		
		if not entry.line_ids:
			raise osv.except_osv(_('Warning!'),
						_('System not allow to confirm without Issue Items !!'))
						
						
		### Core Updation ###
		
		for req_item in entry.line_ids:
			production_obj.write(cr, uid,req_item.production_id.id,{'core_remarks':req_item.remarks,'core_date':req_item.core_date,
			'core_shift_id':req_item.core_shift_id.id,'core_contractor':req_item.core_contractor.id,'core_moulder':req_item.core_moulder,
			'core_helper':req_item.core_helper,'core_qty':req_item.core_qty,'core_hardness':req_item.core_hardness})
			production_obj.core_update(cr, uid, [req_item.production_id.id])
			
		### Core Batch Sequence Number Generation  ###
		core_batch_name = ''	
		core_batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.batch')])
		rec = self.pool.get('ir.sequence').browse(cr,uid,core_batch_seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_batch_seq_id[0],rec.code,entry.entry_date))
		core_batch_name = cr.fetchone();
		self.write(cr, uid, ids, {'name':core_batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
	
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
		'core_contractor':fields.many2one('kg.contractor.master','Contractor'),
		'core_moulder': fields.integer('Moulder'),
		'core_helper': fields.integer('Helper'),
		'core_qty': fields.integer('Qty'),
		'core_hardness': fields.char('Core Hardness'),
		
		'pump_model_id': fields.related('production_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('production_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('production_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		
		
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
		'active': True,
		'state':'draft'
		
		
	}	

	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])		
		production_obj = self.pool.get('kg.production')
		mould_line_obj = self.pool.get('ch.mould.batch.line')
		
		del_sql = """ delete from ch_mould_batch_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.mould_line_ids:
		
			for item in entry.mould_line_ids:
				
				
				vals = {
				
					'header_id': entry.id,
					'production_id':item.id,
					'mould_qty':item.qty,
					
				}
				
				mould_line_id = mould_line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_issueline': True})
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		production_obj = self.pool.get('kg.production')		
		if not entry.line_ids:
			raise osv.except_osv(_('Warning!'),
						_('System not allow to confirm without Mould Items !!'))
						
						
		### Issue Creation against Mould Issue ###
		
		for req_item in entry.line_ids:
			production_obj.write(cr, uid,req_item.production_id.id,{'mould_remarks':req_item.remarks,'mould_date':req_item.mould_date,
			'mould_shift_id':req_item.mould_shift_id.id,'mould_contractor':req_item.mould_contractor.id,'mould_moulder':req_item.mould_moulder,
			'mould_helper':req_item.mould_helper,'mould_qty':req_item.mould_qty,'mould_hardness':req_item.mould_hardness,'mould_box_id':req_item.mould_box_id.id})
			production_obj.mould_update(cr, uid, [req_item.production_id.id])
			
		### Mould Batch Sequence Number Generation  ###
		mould_batch_name = ''	
		mould_batch_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.batch')])
		rec = self.pool.get('ir.sequence').browse(cr,uid,mould_batch_seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_batch_seq_id[0],rec.code,entry.entry_date))
		mould_batch_name = cr.fetchone();
		self.write(cr, uid, ids, {'name':mould_batch_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
	
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
		'mould_contractor':fields.many2one('kg.contractor.master','Contractor'),
		'mould_moulder': fields.integer('Moulder'),
		'mould_box_id':fields.many2one('kg.box.master','Box Size'),
		'mould_helper': fields.integer('Helper'),
		'mould_qty': fields.integer('Qty'),		
		'mould_hardness': fields.char('Mould Hardness'),		
		
		'pump_model_id': fields.related('production_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('production_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_name': fields.related('production_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		
		
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














