from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')


class kg_weekly_schedule(osv.osv):

	_name = "kg.weekly.schedule"
	_description = "Weekly Schedule Entry"
	_order = "entry_date desc"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Schedule No', size=128,select=True,readonly=True),
		'entry_date': fields.date('Schedule Date',required=True),
		'division_id': fields.many2one('kg.division.master','Division', required=True,domain="[('state','=','approved'), ('active','=','t')]"),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location', required=True),
		'note': fields.text('Notes'),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'line_ids': fields.one2many('ch.weekly.schedule.details', 'header_id', "Schedule Details"),
		'flag_cancel': fields.boolean('Cancellation Flag'),
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_weekly_schedule', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',
		'active': True,
		
		
		
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
		
		
		
	def _check_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(''' select id from kg_weekly_schedule where entry_date = %s
			and division_id = %s and location = %s and id != %s and active = 't' and state = 'confirmed' ''',[str(entry.entry_date),entry.division_id.id,entry.location, ids[0]])
		duplicate_id = cr.fetchone()
		if duplicate_id:
			return False
		return True	
		
	def _check_lineitems(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if not entry.line_ids:
			return False
		return True
			
	
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
		(_check_duplicates, 'System not allow to do duplicate entry !!',['']),
		(_check_lineitems, 'System not allow to save with empty Schedule Details !!',['']),
	   
		
	   ]
	   

	def entry_confirm(self,cr,uid,ids,context=None):
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		entry = self.browse(cr,uid,ids[0])
		for item in entry.line_ids:
			delivery_date = str(item.delivery_date)
			delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d')
			if delivery_date < today:
				raise osv.except_osv(_('Warning!'),
						_('Delivery Date should not be less than current date for Order %s !!')%(item.order_ref_no))
						
			
			if not item.line_ids:
				raise osv.except_osv(_('Warning!'),
							_('Specify BOM Details for Order %s')%(item.order_ref_no))
				
			else:
				cr.execute(''' select id from ch_sch_bom_details where flag_applicable = 't' and moc_id is null and header_id = %s ''',[item.id])		
				sch_bom_id = cr.fetchone()
				
				if sch_bom_id:
					if sch_bom_id[0] != None:
						raise osv.except_osv(_('Warning!'),
							_('Specify MOC for Order %s!!')%(item.order_ref_no))
					
			
			cr.execute(''' update ch_sch_bom_details set state = 'confirmed',transac_state = 'in_schedule' where header_id = %s and flag_applicable = 't' ''',[item.id])
			
			cr.execute(''' update ch_sch_bom_details set state = 'confirmed' where header_id = %s ''',[item.id])
		self.write(cr, uid, ids, {'state': 'confirmed','flag_cancel':1,'confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),
			'name' :self.pool.get('ir.sequence').get(cr, uid, 'kg.weekly.schedule') or '/'})
		cr.execute(''' update ch_weekly_schedule_details set state = 'confirmed', flag_cancel='t' where header_id = %s ''',[ids[0]])
		return True
		
	def entry_cancel(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.cancel_remark == False:
			raise osv.except_osv(_('Warning!'),
						_('Cancel Remarks is must !!'))
		
		for line_item in entry.line_ids:				
							
			cr.execute(''' select id from kg_qc_verification where schedule_line_id = %s and state = 'draft' ''',[line_item.id])
			qc_id = cr.fetchone()
			if qc_id != None:
				if qc_id[0] != None:
					raise osv.except_osv(_('Warning!'),
								_('Cannot be cancelled. Schedule is referred in QC !!'))
							
			cr.execute(''' select id from kg_production where schedule_line_id = %s and state = 'draft' ''',[line_item.id])
			production_id = cr.fetchone()
			if production_id != None:
				if production_id[0] != None:
					raise osv.except_osv(_('Warning!'),
								_('Cannot be cancelled. Schedule is referred in Production !!'))
								
			cr.execute(''' update ch_sch_bom_details set state = 'cancel' where header_id = %s ''',[line_item.id])
						
		else:
			self.write(cr, uid, ids, {'state': 'cancel','flag_cancel':0,'cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			cr.execute(''' update ch_weekly_schedule_details set state = 'cancel',flag_cancel='f' where header_id = %s ''',[entry.id])
			
		
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
		return super(kg_weekly_schedule, self).write(cr, uid, ids, vals, context)
	
	
kg_weekly_schedule()


class ch_weekly_schedule_details(osv.osv):

	_name = "ch.weekly.schedule.details"
	_description = "Weekly Schedule Details"
	
	_columns = {
	
		### Schedule Details ####
		'header_id':fields.many2one('kg.weekly.schedule', 'Weekly Schedule', required=1, ondelete='cascade'),
		'schedule_date': fields.related('header_id','entry_date', type='date', string='Date', store=True, readonly=True),
		'order_ref_no': fields.char('Order Reference', size=128, required=True),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True,domain="[('state','=','approved'), ('active','=','t')]"),
		'type': fields.selection([('production','Production'),('spare','Spare')],'Purpose', required=True),
		'qty': fields.float('Schedule Qty', size=100, required=True),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'note': fields.text('Notes'),
		'remarks': fields.text('Approve/Reject Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'delivery_date': fields.date('Delivery Date',required=True),
		'line_ids': fields.one2many('ch.sch.bom.details', 'header_id', "BOM Details"),
		'flag_cancel': fields.boolean('Cancellation Flag'),
		
		
	
	}
	
	
	_defaults = {
	
		'state': 'draft',
		'active': True,
		'delivery_date' : fields.date.context_today,
		
	}
	
	def onchange_delivery_date(self, cr, uid, ids, delivery_date):
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		if delivery_date:
			delivery_date = str(delivery_date)
			delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d')
			if delivery_date < today:
				raise osv.except_osv(_('Warning!'),
						_('Delivery Date should not be less than current date!!'))
		return True
		
	def onchange_schedule_qty(self, cr, uid, ids, pump_model_id, qty, type):
		bom_vals=[]
		sch_bom_obj = self.pool.get('ch.sch.bom.details')
		cr.execute(''' select id,header_id,pattern_id,pattern_name,qty from ch_bom_line 
		where header_id = (select id from kg_bom where pump_model_id = %s and state='approved' and active='t') ''',[pump_model_id])
		bom_details = cr.dictfetchall()
		for bom_details in bom_details:
			if type == 'production':
				applicable = True
			if type == 'spare':
				applicable = False
			bom_vals.append({
												
				'bom_id': bom_details['header_id'],
				'bom_line_id': bom_details['id'],
				'pattern_id': bom_details['pattern_id'],
				'pattern_name': bom_details['pattern_name'],							
				'qty' : qty * bom_details['qty'],					
				'planning_qty' : qty * bom_details['qty'],					
				'production_qty' : 0.00,					
				'flag_applicable' : applicable							
				})
		return {'value': {'line_ids': bom_vals}}
		
	def onchange_order_refno(self, cr, uid, ids, order_ref_no):
		if order_ref_no:
			special_char = ''.join( c for c in order_ref_no if  c in '!@#$%^~*{}?+/=' )
			if special_char:
				raise osv.except_osv(_('Warning!'),
						_('Special Character not allowed in Order reference No !!'))
		return True
	
	def list_bom(self,cr,uid,ids,context=None):
		bom_obj = self.pool.get('kg.bom')
		bom_line_obj = self.pool.get('ch.bom.line')
		sch_bom_obj = self.pool.get('ch.sch.bom.details')
		entry = self.browse(cr,uid,ids[0])
		
		cr.execute(''' select id,header_id,pattern_id,pattern_name,qty from ch_bom_line 
		where header_id = (select id from kg_bom where pump_model_id = %s and state='approved' and active='t') ''',[entry.pump_model_id.id])
		bom_details = cr.dictfetchall()
		line_ids = map(lambda x:x.id,entry.line_ids)
		sch_bom_obj.unlink(cr,uid,line_ids)
		
		if bom_details:
			for bom_details in bom_details:
				if entry.type == 'production':
					applicable = True
				if entry.type == 'spare':
					applicable = False
				bom_vals = {
												
						'header_id': entry.id,
						'bom_id': bom_details['header_id'],
						'bom_line_id': bom_details['id'],
						'pattern_id': bom_details['pattern_id'],
						'pattern_name': bom_details['pattern_name'],							
						'qty' : entry.qty * bom_details['qty'],					
						'planning_qty' : entry.qty * bom_details['qty'],					
						'production_qty' : 0.00,					
						'flag_applicable' : applicable							
						}
					
				sch_bom_id = sch_bom_obj.create(cr, uid, bom_vals)
		else:
			raise osv.except_osv(_('Warning!'),
						_('BOM Details not refered for this Pump Model !!'))
			

		return True
	
	def entry_cancel(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.cancel_remark == False:
			raise osv.except_osv(_('Warning!'),
						_('Cancel Remarks is must !!'))
											
		cr.execute(''' select id from kg_qc_verification where schedule_line_id = %s and state = 'draft' ''',[entry.id])
		qc_id = cr.fetchone()
		if qc_id != None:
			if qc_id[0] != None:
				raise osv.except_osv(_('Warning!'),
							_('Cannot be cancelled. Schedule is referred in QC !!'))
						
		cr.execute(''' select id from kg_production where schedule_line_id = %s and state = 'draft' ''',[entry.id])
		production_id = cr.fetchone()
		if production_id != None:
			if production_id[0] != None:
				raise osv.except_osv(_('Warning!'),
							_('Cannot be cancelled. Schedule is referred in Production !!'))
		else:
			self.write(cr, uid, ids, {'state': 'cancel'})
			cr.execute(''' update ch_weekly_schedule_details set state = 'cancel' where id = %s ''',[entry.id])
			cr.execute(''' update ch_sch_bom_details set state = 'cancel' where header_id = %s ''',[entry.id])
		
		return True
		
	
	def _Validation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		special_char = ''.join( c for c in flds.order_ref_no if  c in '!@#$%^~*{}?+/=' )
		if special_char:
			return False
		return True
		
		
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty == 0.00 or entry.qty < 0.00:
			return False
		return True
		
	def _check_line_items(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft' and entry.header_id.state == 'confirmed':
			return False
		return True
		
	def _check_line_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(''' select id from ch_weekly_schedule_details where order_ref_no = %s and pump_model_id = %s and
			type = %s and id != %s and header_id = %s ''',[entry.order_ref_no, entry.pump_model_id.id, 
			entry.type, entry.id, entry.header_id.id,])
		duplicate_id = cr.fetchone()
		if duplicate_id:
			return False
		return True
		
		
	def create(self, cr, uid, vals, context=None):
		return super(ch_weekly_schedule_details, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_weekly_schedule_details, self).write(cr, uid, ids, vals, context)
		
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete Schedule Details after confirmation !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	
	
	_constraints = [		
			  
		(_check_values, 'System not allow to save with zero and less than zero qty .!!',['Quantity']),
		(_Validation, 'Special Character Not Allowed', ['Order Reference']),
		(_check_line_duplicates, 'Schedule Details are duplicate. Kindly check !! ', ['']),
		(_check_line_items, 'Schedule Detail cannot be created after confirmation !! ', ['']),
	   
		
	   ]
	
ch_weekly_schedule_details()


class ch_sch_bom_details(osv.osv):

	_name = "ch.sch.bom.details"
	_description = "BOM Details"
	
	_columns = {
	
		'header_id':fields.many2one('ch.weekly.schedule.details', 'Schedule Detail', required=1, ondelete='cascade'),
		'schedule_id': fields.related('header_id','header_id', type='many2one',relation='kg.weekly.schedule', string='Schedule No', store=True, readonly=True),
		'schedule_date': fields.related('header_id','schedule_date', type='date', string='Schedule Date', store=True, readonly=True),
		'delivery_date': fields.related('header_id','delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'order_ref_no': fields.related('header_id','order_ref_no', type='char', string='Order Reference', store=True, readonly=True),
		'pump_model_id': fields.related('header_id','pump_model_id', type='many2one',relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'type': fields.related('header_id','type', type='char', string='Purpose', store=True, readonly=True),
		'schedule_qty': fields.related('header_id','qty', type='float', string='Schedule Qty', store=True, readonly=True),
		
		'bom_id': fields.many2one('kg.bom','BOM'),
		'bom_line_id': fields.many2one('ch.bom.line','BOM Line'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No',domain="[('state','=','approved'), ('active','=','t')]"),
		'pattern_name': fields.char('Pattern Name'),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('state','=','approved'), ('active','=','t')]"),
		'qty': fields.float('BOM Qty', size=100),
		'planning_qty': fields.float('Planning Pending Qty', size=100),
		'production_qty': fields.float('Produced Qty', size=100),
		'flag_applicable': fields.boolean('Is Applicable'),
		'add_spec': fields.text('Others Specification'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'transac_state': fields.selection([('in_draft','In Draft'),('in_schedule','In Schedule'),('partial','Partial'),('sent_for_plan','In Planning'),('sent_for_qc','In QC'),
					   ('sent_for_produc','In Production'),('complete','Completed')],'Transaction Status', readonly=True),
	
	}
	
	
	_defaults = {
		
		
		'state': 'draft',
		'transac_state': 'in_draft',
		'flag_applicable': False
	
		
	}
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_sch_bom_details, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		if not type(ids) is list:
			entry = self.browse(cr,uid,ids)
			if vals.get('transac_state'):
				transac_state = vals.get('transac_state')
				if transac_state in ('in_schedule','sent_for_plan','partial'):
					cr.execute(''' select id from ch_sch_bom_details where transac_state in ('complete','sent_for_produc','sent_for_qc')  and header_id = %s and id != %s ''',
					[entry.header_id.id,entry.id])
					sch_line_id = cr.fetchone()
					if sch_line_id == None:
						cr.execute(''' update kg_weekly_schedule set flag_cancel = 't' where id = %s ''',[entry.header_id.header_id.id])
						cr.execute(''' update ch_weekly_schedule_details set flag_cancel = 't' where id = %s ''',[entry.header_id.id])
					else:
						cr.execute(''' update kg_weekly_schedule set flag_cancel = 'f' where id = %s ''',[entry.header_id.header_id.id])
						cr.execute(''' update ch_weekly_schedule_details set flag_cancel = 'f' where id = %s ''',[entry.header_id.id])
				else:
					cr.execute(''' update kg_weekly_schedule set flag_cancel = 'f' where id = %s ''',[entry.header_id.header_id.id])
					cr.execute(''' update ch_weekly_schedule_details set flag_cancel = 'f' where id = %s ''',[entry.header_id.id])
		return super(ch_sch_bom_details, self).write(cr, uid, ids, vals, context)
	
ch_sch_bom_details()






