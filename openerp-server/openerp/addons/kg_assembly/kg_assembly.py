from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import base64

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')


ORDER_PRIORITY = [
   ('1','MS NC'),
   ('2','FDY-NC'),
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

class kg_assembly_inward(osv.osv):

	_name = "kg.assembly.inward"
	_description = "Assembly Inward Entry"
	_order = "entry_date desc"
	_rec_name = "pump_serial_no"
	
	def _get_default_division(self, cr, uid, context=None):
		res = self.pool.get('kg.division.master').search(cr, uid, [('code','=','SAM'),('state','=','approved'), ('active','=','t')], context=context)
		return res and res[0] or False
		
	_columns = {
	
		### Header Details ####
		'name': fields.char('Inward No.', size=128,select=True),
		'entry_date': fields.date('Inward Date'),
		'note': fields.text('Notes'),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([
			('waiting','Waiting for Accept'),
			('in_progress','Assembly In Progress'),
			('re_process','Assembly Re Process'),
			('completed','Assembly Completed'),
			('rejected','Assembly Rejected'),
			('confirm','Confirmed'),
			],'Status', readonly=True),
		
		### Work Order Details ###
		'order_id': fields.many2one('kg.work.order','Work Order'),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line'),
		'division_id': fields.related('order_id','division_id', type='many2one', relation='kg.division.master', string='Division', store=True, readonly=True),
		'location': fields.related('order_id','location', type='selection', selection=[('ipd','IPD'),('ppd','PPD'),('export','Export')], string='Location', store=True, readonly=True),
		'order_no': fields.related('order_line_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('order_line_id','delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'order_date': fields.related('order_id','entry_date', type='date', string='Order Date', store=True, readonly=True),
		'order_category': fields.related('order_line_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'pump_model_id': fields.related('order_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'moc_construction_id': fields.related('order_line_id','moc_construction_id', type='many2one', relation='kg.moc.construction', string='MOC Construction Code', store=True, readonly=True),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		'line_ids': fields.one2many('ch.assembly.bom.details', 'header_id', "BOM Details"),
		'line_ids_a': fields.one2many('ch.assembly.machineshop.details', 'header_id', "Machine Shop Details"),
		'line_ids_b': fields.one2many('ch.assembly.bot.details', 'header_id', "BOT Details"),
		
		'qap_plan_id': fields.many2one('kg.qap.plan', 'QAP Standard',readonly=True),
		'pump_serial_no': fields.char('Pump Serial No.'),
		'time_taken': fields.float('Time Taken'),
		
		'bed_assembly_state': fields.selection([('pending','Pending'),('completed','Completed')],'State', readonly=True),
		'bed_assembly_date': fields.date('Date'),
		'bed_assembly_shift_id': fields.many2one('kg.shift.master','Shift'),
		'bed_assembly_done_by': fields.many2one('hr.employee','Done By'),
		
		'rotate_assembly_state': fields.selection([('pending','Pending'),('completed','Completed')],'State', readonly=True),
		'rotate_assembly_date': fields.date('Date'),
		'rotate_assembly_shift_id': fields.many2one('kg.shift.master','Shift'),
		'rotate_assembly_done_by': fields.many2one('hr.employee','Done By'),
		
		'runout_test_state': fields.selection([('pending','Pending'),('completed','Completed')],'State', readonly=True),
		'runout_test_date': fields.date('Date'),
		'runout_test_shift_id': fields.many2one('kg.shift.master','Shift'),
		'runout_test_done_by': fields.many2one('hr.employee','Done By'),
		
		'mech_assembly_state': fields.selection([('pending','Pending'),('completed','Completed'),('nill','NILL')],'State', readonly=True),
		'mech_assembly_date': fields.date('Date'),
		'mech_assembly_shift_id': fields.many2one('kg.shift.master','Shift'),
		'mech_assembly_done_by': fields.many2one('hr.employee','Done By'),
		
		'full_assembly_state': fields.selection([('pending','Pending'),('completed','Completed')],'State', readonly=True),
		'full_assembly_date': fields.date('Date'),
		'full_assembly_shift_id': fields.many2one('kg.shift.master','Shift'),
		'full_assembly_done_by': fields.many2one('hr.employee','Done By'),
		
		'rfi_date': fields.date('RFI Date'),
		'partner_id': fields.many2one('res.partner','Customer'),
		'flag_data_bank': fields.boolean('Is Data WO'),
		'flag_not_applicable': fields.boolean('Not applicable'),
		
		
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_assembly_inward', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'bed_assembly_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'rotate_assembly_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'runout_test_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'mech_assembly_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'full_assembly_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'waiting',
		'active': True,
		'division_id':_get_default_division,
		'entry_mode': 'manual',
		'rfi_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'flag_not_applicable' : False
	
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
		
	def _future_rfi_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		rfi_date = rec.rfi_date
		rfi_date = str(rfi_date)
		rfi_date = datetime.strptime(rfi_date, '%Y-%m-%d')
		
		if rfi_date < today:
			return False
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr,uid,ids,{'state':'confirm'})
		return True
		
	def entry_approve(self,cr,uid,ids,context=None):
		ass_bom_obj = self.pool.get('ch.assembly.bom.details')
		ass_ms_obj = self.pool.get('ch.assembly.machineshop.details')
		ass_bot_obj = self.pool.get('ch.assembly.bot.details')
		entry_rec = self.browse(cr,uid,ids[0])
		
		if entry_rec.state in ('waiting','re_process'):
			
			if entry_rec.time_taken <= 0:
				raise osv.except_osv(_('Warning!'),
							_('Time Taken should be greater than zero!!'))
			
			### Heat Details Checking ###
			for foundry_line_item in entry_rec.line_ids:
				#~ if foundry_line_item.pattern_id.need_dynamic_balancing == True:
					#~ if not foundry_line_item.line_ids:
						#~ raise osv.except_osv(_('Warning !'), _('DB Reference No. is required for Pattern %s !!')%(foundry_line_item.pattern_id.name))
					#~ if foundry_line_item.line_ids:
						#~ for foun_item in foundry_line_item.line_ids:
							#~ print "foun_item",foun_item.db_id
							#~ if not foun_item.db_id:
								#~ raise osv.except_osv(_('Warning !'), _('DB Reference No. is required for Pattern %s !!')%(foundry_line_item.pattern_id.name))
				if foundry_line_item.pattern_id.flag_heat_no == True:
					if not foundry_line_item.line_ids:
						raise osv.except_osv(_('Warning !'), _('Heat No. is required for Pattern %s !!')%(foundry_line_item.pattern_id.name))
					if foundry_line_item.line_ids:
						for foun_item in foundry_line_item.line_ids:
							if not foun_item.melting_id:
								raise osv.except_osv(_('Warning !'), _('Heat No. is required for Pattern %s !!')%(foundry_line_item.pattern_id.name))
						cr.execute(''' select qty from ch_assembly_foundry_heat_details where header_id=%s ''',[foundry_line_item.id])
						foundry_heat_qty = cr.fetchone()
						if foundry_heat_qty[0]:
							if foundry_heat_qty[0] != foundry_line_item.order_bom_qty:
								raise osv.except_osv(_('Warning !'), _('Kindly give correct heat qty for Pattern %s !!')%(foundry_line_item.pattern_id.name))
			for ms_line_item in entry_rec.line_ids_a:
				if ms_line_item.ms_id.flag_heat_no == True:
					if not ms_line_item.line_ids:
						raise osv.except_osv(_('Warning !'), _('Heat No. is required for MS Item %s !!')%(ms_line_item.ms_id.name))
					if ms_line_item.line_ids:
						cr.execute(''' select qty from ch_assembly_ms_heat_details where header_id=%s ''',[ms_line_item.id])
						ms_heat_qty = cr.fetchone()
						print "ms_heat_qty",ms_heat_qty
						if ms_heat_qty[0]:
							if ms_heat_qty[0] != ms_line_item.order_ms_qty:
								raise osv.except_osv(_('Warning !'), _('Kindly give correct heat qty for MS Item %s !!')%(ms_line_item.ms_id.name))

			cr.execute(''' select id from ch_assembly_bom_details where state = 're_process' and header_id=%s ''',[ids[0]])
			bom_re_process = cr.fetchone()
			cr.execute(''' select id from ch_assembly_machineshop_details where state = 're_process' and header_id=%s ''',[ids[0]])
			ms_re_process = cr.fetchone()
			cr.execute(''' select id from ch_assembly_bot_details where state = 're_process' and header_id=%s ''',[ids[0]])
			bot_re_process = cr.fetchone()
			
			if bom_re_process or ms_re_process or bot_re_process:
				self.write(cr,uid,ids,{'state':'re_process'})
			else:
				self.write(cr,uid,ids,{'state':'in_progress'})
				for bom_item in entry_rec.line_ids:
					ass_bom_obj.write(cr,uid,bom_item.id,{'state':'in_progress'})
				for ms_item in entry_rec.line_ids_a:
					ass_ms_obj.write(cr,uid,ms_item.id,{'state':'in_progress'})
				for bot_item in entry_rec.line_ids_b:
					ass_bot_obj.write(cr,uid,bot_item.id,{'state':'in_progress'})
				
				### Checking Test process Remaining ###
				cr.execute(''' select id from kg_part_qap where assembly_id = %s and order_id=%s and order_line_id =%s
					and db_state = 'pending' and db_flag='t' ''',[ids[0],entry_rec.order_id.id,entry_rec.order_line_id.id])
				db_test_process_rem = cr.fetchone()
				
				cr.execute(''' select id from kg_part_qap where assembly_id = %s and order_id=%s and order_line_id =%s
					and hs_state='pending' and hs_flag='t' ''',[ids[0],entry_rec.order_id.id,entry_rec.order_line_id.id])
				hs_test_process_rem = cr.fetchone()
				print "ids[0],entry_rec.order_id.id,entry_rec.order_line_id.id",ids[0],entry_rec.order_id.id,entry_rec.order_line_id.id
				print "db_test_process_rem",db_test_process_rem
				print "hs_test_process_rem",hs_test_process_rem
				if db_test_process_rem == None and hs_test_process_rem == None:
					#### Updating pump serial number in Part qap ###
					cr.execute(''' update kg_part_qap set pump_serial_no = %s where assembly_id = %s ''',[entry_rec.pump_serial_no,ids[0]])
					### Dimensional Inspection Creation ###
					pump_qap_header_vals = {
					
						'qap_plan_id': entry_rec.qap_plan_id.id,
						'order_id': entry_rec.order_id.id,
						'order_line_id':  entry_rec.order_line_id.id,
						'order_no': entry_rec.order_line_id.order_no,
						'order_category': entry_rec.order_category,
						'pump_model_id': entry_rec.pump_model_id.id,
						'pump_serial_no': entry_rec.pump_serial_no,
						'moc_construction_id': entry_rec.moc_construction_id.id,
						'test_state':'di',
						'di_state': 'pending',
						'assembly_id': ids[0]
					}
					pump_qap_id = self.pool.get('kg.pump.qap').create(cr, uid, pump_qap_header_vals)
					
					dim_inspection_id = self.pool.get('ch.dimentional.inspection').search(cr,uid,[('pump_model_id','=',entry_rec.pump_model_id.id)])
					if dim_inspection_id:
						dim_inspection_rec = self.pool.get('ch.dimentional.inspection').browse(cr,uid,dim_inspection_id[0])
						for dim_item in dim_inspection_rec.line_ids:
							print "dim_item",dim_item
							pump_dimension_vals = {
								'header_id': pump_qap_id, 		
								'dimentional_details': dim_item.dimentional_details,
								'min_weight': dim_item.min_weight,
								'max_weight': dim_item.max_weight,	
							}
							pump_dimension_id = self.pool.get('ch.pump.dimentional.details').create(cr, uid, pump_dimension_vals)
				else:
					raise osv.except_osv(_('Warning !!'),
					_('Test process remaining !!'))
		else:
			pass
		return True
		
	def entry_reject(self,cr,uid,ids,context=None):
		print "Full Reject"
		ass_bom_obj = self.pool.get('ch.assembly.bom.details')
		ass_ms_obj = self.pool.get('ch.assembly.machineshop.details')
		ass_bot_obj = self.pool.get('ch.assembly.bot.details')
		schedule_line_obj = self.pool.get('ch.schedule.details')
		entry_rec = self.browse(cr,uid,ids[0])
		self.write(cr,uid,ids,{'state':'re_process'})
		
		if entry_rec.time_taken <= 0:
				raise osv.except_osv(_('Warning!'),
							_('Time Taken should be greater than zero!!'))
		for bom_item in entry_rec.line_ids:
			ass_bom_obj.write(cr,uid,bom_item.id,{'state':'re_process'})
			
			schedule_line_id = schedule_line_obj.search(cr, uid,[('order_line_id','=',entry_rec.order_line_id.id),
			('order_id','=',entry_rec.order_id.id),('pattern_id','=',bom_item.pattern_id.id)])
			if schedule_line_id:
				schedule_line_rec = schedule_line_obj.browse(cr, uid, schedule_line_id[0])
				schedule_id = schedule_line_rec.header_id.id
				schedule_line_id = schedule_line_rec.id
				schedule_date = schedule_line_rec.header_id.entry_date
			else:
				schedule_id =  False
				schedule_line_id = False
				schedule_date = False
			print "schedule_line_id",schedule_line_id
			print "schedule_id",schedule_id
			stop
			#### Updation in QAP Process After rejection of Assembly ###
			cr.execute(''' update kg_part_qap set db_state = 'completed', db_result = 'reject', hs_state = 'completed',
				hs_result = 'reject' where assembly_id = %s and order_id = %s and order_line_id = %s ''',[ids[0],entry_rec.order_id.id,entry_rec.order_line_id.id])
				
			### Sending Foundry Items to Schedule List ###
			
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
				'division_id': entry_rec.division_id.id,
				'location' : entry_rec.location,
				'order_id': entry_rec.order_id.id,
				'order_line_id': entry_rec.order_line_id.id,
				'order_bomline_id': bom_item.order_bom_id.id,
				'schedule_id': schedule_id,
				'schedule_line_id': schedule_line_id,
				'schedule_date': schedule_date,
				'qty' : bom_item.order_bom_qty,			  
				'schedule_qty' : bom_item.order_bom_qty,			  
				'state' : 'issue_done',
				'order_category':entry_rec.order_category,
				'order_priority': '1',
				'pattern_id' : bom_item.pattern_id.id,
				'pattern_name' : bom_item.pattern_id.pattern_name,	
				'moc_id' : bom_item.moc_id.id,
				'request_state': 'done',
				'issue_no': issue_name[0],
				'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
				'issue_qty': 1,
				'issue_state': 'issued',
				'core_no': core_name[0],
				'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
				'core_qty': bom_item.order_bom_qty,
				'core_rem_qty': bom_item.order_bom_qty,
				'core_state': 'pending',
				'mould_no': mould_name[0],
				'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
				'mould_qty': bom_item.order_bom_qty,
				'mould_rem_qty': bom_item.order_bom_qty,
				'mould_state': 'pending',
				'assembly_id': entry_rec.id,
				'assembly_line_id': bom_item.id,		
			}
			
			production_id = self.pool.get('kg.production').create(cr, uid, production_vals)
		
		for ms_item in entry_rec.line_ids_a:
			ass_ms_obj.write(cr,uid,ms_item.id,{'state':'re_process'})
			
			ms_obj = self.pool.get('kg.machineshop')
			ms_master_obj = self.pool.get('kg.machine.shop')
			ms_rec = ms_master_obj.browse(cr, uid, ms_item.ms_id.id)
			
			### Sequence Number Generation ###
			ms_name = ''	
			ms_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.ms.inward')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,ms_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(ms_seq_id[0],seq_rec.code))
			ms_name = cr.fetchone();
			
			ms_vals = {
			
			'order_ms_line_id': ms_item.order_ms_id.id,
			'name': ms_name[0],
			'location': entry_rec.location,
			'order_id': entry_rec.order_id.id,
			'order_line_id': entry_rec.order_line_id.id,
			'order_no': entry_rec.order_line_id.order_no,
			'order_delivery_date': entry_rec.order_line_id.delivery_date,
			'order_date': entry_rec.order_line_id.header_id.entry_date,
			'order_category': entry_rec.order_id.order_category,
			'order_priority': '1',
			'pump_model_id':entry_rec.pump_model_id.id,
			'moc_id':ms_item.moc_id.id,
			'schedule_qty':ms_item.order_ms_qty,
			'ms_sch_qty':ms_item.order_ms_qty,
			'ms_type': 'ms_item',
			'ms_state': 'in_plan',
			'state':'accept',
			'ms_id': ms_item.ms_id.id,
			'ms_bom_id': ms_item.bom_id.id,
			'ms_bom_line_id': ms_item.ms_line_id.id,
			'position_id': ms_item.position_id.id,
			'item_code': ms_rec.code,
			'item_name': ms_item.name,
			'assembly_id': entry_rec.id,
			'assembly_line_id': ms_item.id,
			
			}
			
			ms_id = ms_obj.create(cr, uid, ms_vals)
			
		for bot_item in entry_rec.line_ids_b:
			ass_bot_obj.write(cr,uid,bot_item.id,{'state':'re_process'})
				
	
		return True
		
		
	
	
	_constraints = [		
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
		(_future_rfi_date_check, 'RFI Date should be greater than or equal to today date !!',['']),
		
	   ]
	   
	   
	
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
		return super(kg_assembly_inward, self).write(cr, uid, ids, vals, context)
		
kg_assembly_inward()


class ch_assembly_bom_details(osv.osv):

	_name = "ch.assembly.bom.details"
	_description = "Assembly BOM Details"
	
	_columns = {
	
		'header_id':fields.many2one('kg.assembly.inward', 'Assembly Inward', required=1, ondelete='cascade'),
	
		'order_bom_id': fields.many2one('ch.order.bom.details','Foundry Item'),
		'bom_id': fields.related('order_bom_id','bom_id', type='many2one',relation='kg.bom', string='BOM', store=True, readonly=True),
		'bom_line_id': fields.related('order_bom_id','bom_line_id', type='many2one',relation='ch.bom.line', string='BOM Line', store=True, readonly=True),
		'pattern_id': fields.related('order_bom_id','pattern_id', type='many2one',relation='kg.pattern.master', string='Pattern No', store=True, readonly=True),
		'pattern_name': fields.related('order_bom_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'weight': fields.related('order_bom_id','weight', type='float', string='Weight(kgs)', store=True, readonly=True),
		'pos_no': fields.related('order_bom_id','pos_no', type='integer', string='Position No', store=True),
		'position_id': fields.related('order_bom_id','position_id', type='many2one',relation='kg.position.number', string='Position No', store=True, readonly=True),
		'moc_id': fields.related('order_bom_id','moc_id', type='many2one',relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'order_bom_qty': fields.integer('Qty'),
		'unit_price': fields.related('order_bom_id','unit_price', type='float', string='Unit Price', store=True, readonly=True),
		'flag_applicable': fields.related('order_bom_id','flag_applicable', type='boolean', string='Is Applicable', store=True, readonly=True),
		'add_spec': fields.related('order_bom_id','add_spec', type='text', string='WO Remarks', store=True, readonly=True),
		'flag_standard': fields.related('order_bom_id','flag_standard', type='boolean', string='Non Standard', store=True, readonly=True),
		'flag_pattern_check': fields.related('order_bom_id','flag_pattern_check', type='boolean', string='Is Pattern Check', store=True, readonly=True),
		'order_entry_mode': fields.related('order_bom_id','entry_mode', type='selection', selection=[('manual','Manual'),('auto','Auto')],string='Entry Mode', store=True, readonly=True),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		'state': fields.selection([
			('waiting','Waiting for Accept'),
			('in_progress','Assembly In Progress'),
			('re_process','Assembly Re Process'),
			('completed','Assembly Completed'),
			('rejected','Assembly Rejected'),
			],'Status', readonly=True),
		'reject_remarks': fields.text('Rejection Remarks'),
		
		'line_ids': fields.one2many('ch.assembly.foundry.heat.details', 'header_id', "Heat Details"),
		
	
	}
	
	_defaults = {
	
		'state': 'waiting',
		'entry_mode': 'manual',
	
	}
	
	def entry_reject(self,cr,uid,ids,context=None):
		print "Partial Reject"
		header_obj = self.pool.get('kg.assembly.inward')
		schedule_line_obj = self.pool.get('ch.schedule.details')
		entry_rec = self.browse(cr,uid,ids[0])
		
		
		if entry_rec.reject_remarks == False:
			raise osv.except_osv(_('Warning !'), _('Rejection Remarks is Must!!'))
		else:
			self.write(cr,uid,ids,{'state':'re_process'})
			
			schedule_line_id = schedule_line_obj.search(cr, uid,[('order_line_id','=',entry_rec.order_line_id.id),
			('order_id','=',entry_rec.order_id.id),('pattern_id','=',bom_item.pattern_id.id)])
			if schedule_line_id:
				schedule_line_rec = schedule_line_obj.browse(cr, uid, schedule_line_id[0])
				schedule_id = schedule_line_rec.header_id.id
				schedule_line_id = schedule_line_rec.id
				schedule_date = schedule_line_rec.header_id.entry_date
			else:
				schedule_id =  False
				schedule_line_id = False
				schedule_date = False
				
			#### Updation in QAP Process After rejection of Assembly ###
			cr.execute(''' update kg_part_qap set db_state = 'completed', db_result = 'reject', hs_state = 'completed',
				hs_result = 'reject' where assembly_id = %s and order_id = %s and order_line_id = %s and pattern_id = %s and order_bom_id =%s ''',[entry_rec.header_id,entry_rec.order_id.id,
				entry_rec.order_line_id.id,entry_rec.pattern_id.id,entry_rec.order_bom_id.id])

			### Sending Foundry Items to Schedule List ###
			
			#### NC Creation for reject Qty ###
					
			### Production Number ###
			produc_name = ''	
			produc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.production')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,produc_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(produc_seq_id[0],rec.code,entry_rec.header_id.entry_date))
			produc_name = cr.fetchone();
			
			### Issue Number ###
			issue_name = ''	
			issue_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pattern.issue')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,issue_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(issue_seq_id[0],rec.code,entry_rec.header_id.entry_date))
			issue_name = cr.fetchone();
			
			### Core Log Number ###
			core_name = ''	
			core_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.log')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,core_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_seq_id[0],rec.code,entry_rec.header_id.entry_date))
			core_name = cr.fetchone();
			
			### Mould Log Number ###
			mould_name = ''	
			mould_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.log')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,mould_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_seq_id[0],rec.code,entry_rec.header_id.entry_date))
			mould_name = cr.fetchone();
			
			production_vals = {
									
				'name': produc_name[0],
				'division_id': entry_rec.header_id.division_id.id,
				'location' : entry_rec.header_id.location,
				'order_id': entry_rec.header_id.order_id.id,
				'order_line_id': entry_rec.header_id.order_line_id.id,
				'order_bomline_id': entry_rec.order_bom_id.id,
				'schedule_id': schedule_id,
				'schedule_line_id': schedule_line_id,
				'schedule_date': schedule_date,
				'qty' : entry_rec.order_bom_qty,			  
				'schedule_qty' : entry_rec.order_bom_qty,			  
				'state' : 'issue_done',
				'order_category':entry_rec.header_id.order_category,
				'order_priority': '1',
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
				'core_qty': entry_rec.order_bom_qty,
				'core_rem_qty': entry_rec.order_bom_qty,
				'core_state': 'pending',
				'mould_no': mould_name[0],
				'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
				'mould_qty': entry_rec.order_bom_qty,
				'mould_rem_qty': entry_rec.order_bom_qty,
				'mould_state': 'pending',
				'assembly_id': entry_rec.header_id.id,
				'assembly_line_id': entry_rec.id,	
			}
			
			production_id = self.pool.get('kg.production').create(cr, uid, production_vals)
		
		
		return True
	

	
	
ch_assembly_bom_details()

class ch_assembly_machineshop_details(osv.osv):

	_name = "ch.assembly.machineshop.details"
	_description = "Assembly machineshop Details"
	
	
	_columns = {
	
		'header_id':fields.many2one('kg.assembly.inward', 'Assembly Inward', required=1, ondelete='cascade'),
		'order_ms_id': fields.many2one('ch.order.machineshop.details','MS Item'),
		
		'ms_line_id': fields.related('order_ms_id','ms_line_id', type='many2one',relation='ch.machineshop.details', string='Machine Shop Id', store=True, readonly=True),
		'pos_no': fields.related('order_ms_id','pos_no', type='integer', string='Position No', store=True),
		'position_id': fields.related('order_ms_id','position_id', type='many2one',relation='kg.position.number', string='Position No', store=True, readonly=True),
		'bom_id': fields.related('order_ms_id','bom_id', type='many2one',relation='kg.bom', string='BOM', store=True, readonly=True),
		'ms_id': fields.related('order_ms_id','ms_id', type='many2one',relation='kg.machine.shop', string='Item Code', store=True, readonly=True),
		'moc_id': fields.related('order_ms_id','moc_id', type='many2one',relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'name': fields.related('order_ms_id','name', type='char',size=128,string='Item Name', store=True),  
		'order_ms_qty': fields.integer('Qty'), 
		'flag_applicable': fields.related('order_ms_id','flag_applicable', type='boolean', string='Is Applicable', store=True, readonly=True),
		'order_ms_remarks': fields.related('order_ms_id','remarks', type='text', string='WO Remarks', store=True, readonly=True),
		'flag_standard': fields.related('order_ms_id','flag_standard', type='boolean', string='Non Standard', store=True, readonly=True),
		'order_entry_mode': fields.related('order_ms_id','entry_mode', type='selection', selection=[('manual','Manual'),('auto','Auto')],string='Entry Mode', store=True, readonly=True),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		'state': fields.selection([
			('waiting','Waiting for Accept'),
			('in_progress','Assembly In Progress'),
			('re_process','Assembly Re Process'),
			('completed','Assembly Completed'),
			('rejected','Assembly Rejected'),
			],'Status', readonly=True),
		'reject_remarks': fields.text('Rejection Remarks'),
		'line_ids': fields.one2many('ch.assembly.ms.heat.details', 'header_id', "Heat Details"),
		
	}
	
	_defaults = {
	
		'state': 'waiting',
		'entry_mode': 'manual',
	
	}
	
	def entry_reject(self,cr,uid,ids,context=None):
		print "Partial Reject"
		header_obj = self.pool.get('kg.assembly.inward')
		schedule_line_obj = self.pool.get('ch.schedule.details')
		entry_rec = self.browse(cr,uid,ids[0])
		
		
		if entry_rec.reject_remarks == False:
			raise osv.except_osv(_('Warning !'), _('Rejection Remarks is Must!!'))
		else:
			self.write(cr,uid,ids,{'state':'re_process'})
			
			ms_obj = self.pool.get('kg.machineshop')
			ms_master_obj = self.pool.get('kg.machine.shop')
			ms_rec = ms_master_obj.browse(cr, uid, entry_rec.ms_id.id)
			
			### Sequence Number Generation ###
			ms_name = ''	
			ms_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.ms.inward')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,ms_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(ms_seq_id[0],seq_rec.code))
			ms_name = cr.fetchone();
			
			ms_vals = {
			
			'order_ms_line_id': entry_rec.order_ms_id.id,
			'name': ms_name[0],
			'location': entry_rec.header_id.location,
			'order_id': entry_rec.header_id.order_id.id,
			'order_line_id': entry_rec.header_id.order_line_id.id,
			'order_no': entry_rec.header_id.order_line_id.order_no,
			'order_delivery_date': entry_rec.header_id.order_line_id.delivery_date,
			'order_date': entry_rec.header_id.order_line_id.header_id.entry_date,
			'order_category': entry_rec.header_id.order_id.order_category,
			'order_priority': '1',
			'pump_model_id':entry_rec.header_id.pump_model_id.id,
			'moc_id':entry_rec.moc_id.id,
			'schedule_qty':entry_rec.order_ms_qty,
			'ms_sch_qty':entry_rec.order_ms_qty,
			'ms_type': 'ms_item',
			'ms_state': 'in_plan',
			'state':'accept',
			'ms_id': entry_rec.ms_id.id,
			'ms_bom_id': entry_rec.bom_id.id,
			'ms_bom_line_id': entry_rec.ms_line_id.id,
			'position_id': entry_rec.position_id.id,
			'item_code': ms_rec.code,
			'item_name': entry_rec.name,
			'assembly_id': entry_rec.header_id.id,
			'assembly_line_id': entry_rec.id,	
			
			}
			
			ms_id = ms_obj.create(cr, uid, ms_vals)
		
		
		return True
	  

ch_assembly_machineshop_details()

class ch_assembly_bot_details(osv.osv):
	
	_name = "ch.assembly.bot.details"
	_description = "Assembly BOT Details"	
	
	_columns = {
	
		'header_id':fields.many2one('kg.assembly.inward', 'Assembly Inward', required=1, ondelete='cascade'),
		'order_bot_id': fields.many2one('ch.order.bot.details','BOT Item'),
		
		'bot_line_id': fields.related('order_bot_id','bot_line_id', type='many2one',relation='ch.bot.details', string='BOT Shop Id', store=True, readonly=True),
		'bot_id': fields.related('order_bot_id','bot_id', type='many2one',relation='kg.machine.shop', string='Item Code', store=True, readonly=True),
		'item_name': fields.related('order_bot_id','item_name', type='char', size=128, string='Item Name', store=True, readonly=True),
		'bom_id': fields.related('order_bot_id','bom_id', type='many2one',relation='kg.bom', string='BOM', store=True, readonly=True),
		'moc_id': fields.related('order_bot_id','moc_id', type='many2one',relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'order_bot_qty': fields.integer('Qty'),
		'flag_applicable': fields.related('order_bot_id','flag_applicable', type='boolean', string='Is Applicable', store=True, readonly=True),
		'order_bot_remarks': fields.related('order_bot_id','remarks', type='text', string='WO Remarks', store=True, readonly=True),
		'flag_standard': fields.related('order_bot_id','flag_standard', type='boolean', string='Non Standard', store=True, readonly=True),
		'order_entry_mode': fields.related('order_bot_id','entry_mode', type='selection', selection=[('manual','Manual'),('auto','Auto')],string='Entry Mode', store=True, readonly=True),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		'state': fields.selection([
			('waiting','Waiting for Accept'),
			('in_progress','Assembly In Progress'),
			('re_process','Assembly Re Process'),
			('completed','Assembly Completed'),
			('rejected','Assembly Rejected'),
			],'Status', readonly=True),
	
	}
	
	_defaults = {
	
		'state': 'waiting',
		'entry_mode': 'manual',
	
	}
	
	

ch_assembly_bot_details()


class ch_assembly_foundry_heat_details(osv.osv):
	
	_name = "ch.assembly.foundry.heat.details"
	_description = "Assembly Foundry Heat Details"	
	
	_columns = {
	
		'header_id':fields.many2one('ch.assembly.bom.details', 'Assembly Foundry', required=1, ondelete='cascade'),
		'moc_id': fields.related('header_id','moc_id', type='many2one',relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'melting_id': fields.many2one('kg.melting','Heat No.',domain="[('moc_id','=',moc_id)]"),
		#~ 'db_id': fields.many2one('kg.part.qap','DB reference No.',domain="[('name','!=',False),('pattern_id','=',pattern_id)]"),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No.'),
		'qty': fields.float('Qty'),

	
	}
	
	def default_get(self, cr, uid, fields, context=None):
		return context
	

ch_assembly_foundry_heat_details()

class ch_assembly_ms_heat_details(osv.osv):
	
	_name = "ch.assembly.ms.heat.details"
	_description = "Assembly MS Heat Details"	
	
	_columns = {
	
		'header_id':fields.many2one('ch.assembly.machineshop.details', 'Assembly MS', required=1, ondelete='cascade'),
		'moc_id': fields.related('header_id','moc_id', type='many2one',relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'melting_id': fields.many2one('kg.melting','Heat No.',domain="[('moc_id','=',moc_id)]"),
		'qty': fields.float('Qty'),

	
	}
	
	def default_get(self, cr, uid, fields, context=None):
		return context
	
	

ch_assembly_ms_heat_details()


### Manual Assembly Inward ###

class kg_manual_assembly_inward(osv.osv_memory):
	_name = "kg.manual.assembly.inward"
	_description = "Manual Assembly Inward"
	
	_columns = {
		'order_line_id': fields.many2one('ch.work.order.details','WO No.',),
		'pump_model_id': fields.many2one('kg.pumpmodel.master', string='Pump Model'),
		'remarks': fields.text('Remarks'),
	   
	}
	
	def assembly_update(self, cr, uid, ids, context=None):
		print "Create Assembly"
		entry_rec = self.browse(cr, uid, ids[0])
		ms_store_obj = self.pool.get('kg.ms.stores')
		ms_store_obj.assembly_update(cr, uid, [0],'auto',False,False,context=None)
		return True

kg_manual_assembly_inward()

### Performance Testing ###

class kg_performance_testing(osv.osv):

	_name = "kg.performance.testing"
	_description = "Performance Testing"
	_order = "entry_date desc"
	
	def _get_default_division(self, cr, uid, context=None):
		res = self.pool.get('kg.division.master').search(cr, uid, [('code','=','SAM'),('state','=','approved'), ('active','=','t')], context=context)
		return res and res[0] or False
		
	_columns = {
	
		### Header Details ####
		'name': fields.char('Test No.', size=128,select=True),
		'entry_date': fields.date('Date',required=True),
		'note': fields.text('Notes'),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([
			('waiting','Waiting for Accept'),
			('accept','Accepted'),
			('rejected','Rejected'),
			],'Status', readonly=True),
		
		### Work Order Details ###
		'assembly_id': fields.many2one('kg.assembly.inward','Assembly Inward'),
		'order_id': fields.many2one('kg.work.order','Work Order'),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line'),
		'division_id': fields.related('order_id','division_id', type='many2one', relation='kg.division.master', string='Division', store=True, readonly=True),
		'location': fields.related('order_id','location', type='selection', selection=[('ipd','IPD'),('ppd','PPD'),('export','Export')], string='Location', store=True, readonly=True),
		'order_no': fields.related('order_line_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('order_line_id','delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'order_date': fields.related('order_id','entry_date', type='date', string='Order Date', store=True, readonly=True),
		'order_category': fields.related('order_line_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'pump_model_id': fields.related('order_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'moc_construction_id': fields.related('order_line_id','moc_construction_id', type='many2one', relation='kg.moc.construction', string='MOC Construction Code', store=True, readonly=True),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		'line_ids': fields.one2many('ch.test.bom.details', 'header_id', "BOM Details"),
		'line_ids_a': fields.one2many('ch.test.machineshop.details', 'header_id', "Machine Shop Details"),
		'line_ids_b': fields.one2many('ch.test.bot.details', 'header_id', "BOT Details"),
		
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_assembly_inward', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'waiting',
		'active': True,
		'division_id':_get_default_division,
		'entry_mode': 'manual',
	
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
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
		
	   ]
	   
	   
	
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
		return super(kg_performance_testing, self).write(cr, uid, ids, vals, context)
		
kg_performance_testing()


class ch_test_bom_details(osv.osv):

	_name = "ch.test.bom.details"
	_description = "Performance Testing BOM Details"
	
	_columns = {
	
		'header_id':fields.many2one('kg.performance.testing', 'Performance Testing', required=1, ondelete='cascade'),
	
		'assembly_bom_line_id': fields.many2one('ch.assembly.bom.details','Assembly BOM Line ID'),
		'order_bom_id': fields.many2one('ch.order.bom.details','Foundry Item'),
		'bom_id': fields.related('order_bom_id','bom_id', type='many2one',relation='kg.bom', string='BOM', store=True, readonly=True),
		'bom_line_id': fields.related('order_bom_id','bom_line_id', type='many2one',relation='ch.bom.line', string='BOM Line', store=True, readonly=True),
		'pattern_id': fields.related('order_bom_id','pattern_id', type='many2one',relation='kg.pattern.master', string='Pattern No', store=True, readonly=True),
		'pattern_name': fields.related('order_bom_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'weight': fields.related('order_bom_id','weight', type='float', string='Weight(kgs)', store=True, readonly=True),
		'pos_no': fields.related('order_bom_id','pos_no', type='integer', string='Position No', store=True),
		'position_id': fields.related('order_bom_id','position_id', type='many2one',relation='kg.position.number', string='Position No', store=True, readonly=True),
		'moc_id': fields.related('order_bom_id','moc_id', type='many2one',relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'order_bom_qty': fields.integer('Qty'),
		'unit_price': fields.related('order_bom_id','unit_price', type='float', string='Unit Price', store=True, readonly=True),
		'flag_applicable': fields.related('order_bom_id','flag_applicable', type='boolean', string='Is Applicable', store=True, readonly=True),
		'add_spec': fields.related('order_bom_id','add_spec', type='text', string='Others Specification', store=True, readonly=True),
		'flag_standard': fields.related('order_bom_id','flag_standard', type='boolean', string='Non Standard', store=True, readonly=True),
		'flag_pattern_check': fields.related('order_bom_id','flag_pattern_check', type='boolean', string='Is Pattern Check', store=True, readonly=True),
		'order_entry_mode': fields.related('order_bom_id','entry_mode', type='selection', selection=[('manual','Manual'),('auto','Auto')],string='Entry Mode', store=True, readonly=True),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		'state': fields.selection([
			('waiting','Waiting for Accept'),
			('accept','Accepted'),
			('rejected','Rejected'),
			],'Status', readonly=True),
		'reject_remarks': fields.text('Rejection Remarks'),
		
	
	}
	
	_defaults = {
	
		'state': 'waiting',
		'entry_mode': 'manual',
	
	}
	
	
	
ch_test_bom_details()

class ch_test_machineshop_details(osv.osv):

	_name = "ch.test.machineshop.details"
	_description = "Performance Testing machineshop Details"
	
	
	_columns = {
	
		'header_id':fields.many2one('kg.performance.testing', 'Performance Testing', required=1, ondelete='cascade'),
		
		'assembly_ms_line_id': fields.many2one('ch.assembly.machineshop.details','Assembly machineshop Line ID'),
		'order_ms_id': fields.many2one('ch.order.machineshop.details','MS Item'),
		
		'ms_line_id': fields.related('order_ms_id','ms_line_id', type='many2one',relation='ch.machineshop.details', string='Machine Shop Id', store=True, readonly=True),
		'pos_no': fields.related('order_ms_id','pos_no', type='integer', string='Position No', store=True),
		'position_id': fields.related('order_ms_id','position_id', type='many2one',relation='kg.position.number', string='Position No', store=True, readonly=True),
		'bom_id': fields.related('order_ms_id','bom_id', type='many2one',relation='kg.bom', string='BOM', store=True, readonly=True),
		'ms_id': fields.related('order_ms_id','ms_id', type='many2one',relation='kg.machine.shop', string='Item Code', store=True, readonly=True),
		'moc_id': fields.related('order_ms_id','moc_id', type='many2one',relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'name': fields.related('order_ms_id','name', type='char',size=128,string='Item Name', store=True),  
		'order_ms_qty': fields.integer('Qty'), 
		'flag_applicable': fields.related('order_ms_id','flag_applicable', type='boolean', string='Is Applicable', store=True, readonly=True),
		'order_ms_remarks': fields.related('order_ms_id','remarks', type='text', string='Remarks', store=True, readonly=True),
		'flag_standard': fields.related('order_ms_id','flag_standard', type='boolean', string='Non Standard', store=True, readonly=True),
		'order_entry_mode': fields.related('order_ms_id','entry_mode', type='selection', selection=[('manual','Manual'),('auto','Auto')],string='Entry Mode', store=True, readonly=True),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		'state': fields.selection([
			('waiting','Waiting for Accept'),
			('accept','Accepted'),
			('rejected','Rejected'),
			],'Status', readonly=True),
		'reject_remarks': fields.text('Rejection Remarks'),
		
	}
	
	_defaults = {
	
		'state': 'waiting',
		'entry_mode': 'manual',
	
	}
	  

ch_test_machineshop_details()

class ch_test_bot_details(osv.osv):
	
	_name = "ch.test.bot.details"
	_description = "Performance Testing BOT Details"	
	
	_columns = {
	
		'header_id':fields.many2one('kg.performance.testing', 'Performance Testing', required=1, ondelete='cascade'),
		
		'assembly_bot_line_id': fields.many2one('ch.assembly.bot.details','Assembly BOT Line ID'),
		'order_bot_id': fields.many2one('ch.order.bot.details','BOT Item'),
		
		'bot_line_id': fields.related('order_bot_id','bot_line_id', type='many2one',relation='ch.bot.details', string='BOT Shop Id', store=True, readonly=True),
		'bot_id': fields.related('order_bot_id','bot_id', type='many2one',relation='kg.machine.shop', string='Item Code', store=True, readonly=True),
		'item_name': fields.related('order_bot_id','item_name', type='char', size=128, string='Item Name', store=True, readonly=True),
		'bom_id': fields.related('order_bot_id','bom_id', type='many2one',relation='kg.bom', string='BOM', store=True, readonly=True),
		'moc_id': fields.related('order_bot_id','moc_id', type='many2one',relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'order_bot_qty': fields.integer('Qty'),
		'flag_applicable': fields.related('order_bot_id','flag_applicable', type='boolean', string='Is Applicable', store=True, readonly=True),
		'order_bot_remarks': fields.related('order_bot_id','remarks', type='text', string='Remarks', store=True, readonly=True),
		'flag_standard': fields.related('order_bot_id','flag_standard', type='boolean', string='Non Standard', store=True, readonly=True),
		'order_entry_mode': fields.related('order_bot_id','entry_mode', type='selection', selection=[('manual','Manual'),('auto','Auto')],string='Entry Mode', store=True, readonly=True),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		'state': fields.selection([
			('waiting','Waiting for Accept'),
			('accept','Accepted'),
			('rejected','Rejected'),
			],'Status', readonly=True),
	
	}
	
	_defaults = {
	
		'state': 'waiting',
		'entry_mode': 'manual',
	
	}
	
	

ch_test_bot_details()


class kg_spare_assembly(osv.osv):

	_name = "kg.spare.assembly"
	_description = "Spare Assembly"
	_order = "entry_date desc"		
		
	_columns = {

		
		## Basic Info
		'name': fields.char('Assembly reference No.', size=128,select=True),
		'entry_date': fields.date('Date',required=True),		
		'note': fields.text('Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('approve','Approved'),('cancel','Cancelled')],'Status', readonly=True),
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
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'approve_user_id': fields.many2one('res.users', 'Approved By', readonly=True),				
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),	
		
		## Module Requirement Info
		'order_line_id': fields.many2one('ch.work.order.details','WO. No.',required=True,domain="[('order_category','=','spare')]"),
		'delivery_date': fields.date('Delivery date'),
		'qap_plan_id': fields.many2one('kg.qap.plan', 'QAP Standard',required=True),
		'moc_construction_id':fields.many2one('kg.moc.construction','MOC Construction Code',domain="[('active','=','t')]"),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True,domain="[('active','=','t')]"),		
		'order_category': fields.related('order_line_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		
		'spare_bom_id': fields.many2one('ch.wo.spare.bom','Spare BOM',domain="[('header_id','=',order_line_id)]"),
		## Child Tables Declaration	
			
		'line_ids': fields.one2many('ch.spare.assembly.details','header_id','Spare Assembly details'),  	
		
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_spare_assembly', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),		
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,		
		'state': 'draft',		
		'entry_mode': 'manual',
			
	}
	
	def onchange_order_line_id(self, cr, uid, ids, order_line_id):
		value = {}
		if order_line_id:
			order_line_rec = self.pool.get('ch.work.order.details').browse(cr, uid, order_line_id)
			
			value = {	'pump_model_id':order_line_rec.pump_model_id.id,
						'order_category':order_line_rec.order_category,  
						'moc_construction_id':order_line_rec.moc_construction_id.id,  
						'qap_plan_id':order_line_rec.qap_plan_id.id,  
						'delivery_date':order_line_rec.delivery_date,  
					}
		return {'value': value }
		
	def update_list(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		
		if entry.spare_bom_id == False:
			### Checking bot items completed for that WO ##
			
			cr.execute(""" select id from kg_ms_stores where ms_type = 'bot_item'

				and order_line_id = %s and state = 'in_store' and accept_state = 'pending' """%(entry.order_line_id.id))
			bot_item = cr.fetchone()
			print "bot_itembot_item",bot_item
			if bot_item != None:
				raise osv.except_osv(_('Warning!'),
							_('BOT item Issue is pending to receive !!'))
							
			else:
				### Load finished Items ###
				cr.execute(""" delete from ch_spare_assembly_details where header_id = %s """%(ids[0]))
				
				cr.execute(""" select id,ms_type,position_id,moc_id,item_code,item_name,qty,oth_spec from kg_ms_stores where
					order_line_id = %s and state = 'in_store' and accept_state = 'received'
					order by ms_type """%(entry.order_line_id.id))
				finished_items = cr.dictfetchall()
				for item in finished_items:
					
					spare_ass_vals = {
						'header_id': entry.id,
						'ms_type': item['ms_type'],
						'ms_store_id': item['id'],
						'position_id': item['position_id'] or False,
						'moc_id': item['moc_id'],
						'item_code':item['item_code'],
						'item_name':item['item_name'],				
						'qty': item['qty'],		
						'add_spec': item['oth_spec'],			
					}
					ass_line_obj = self.pool.get('ch.spare.assembly.details')
					ass_line_id = ass_line_obj.create(cr, uid, spare_ass_vals)
		else:
			### Checking bot items completed for that WO ##
			
			cr.execute(""" select id from kg_ms_stores where ms_type = 'bot_item'

				and order_line_id = %s and state = 'in_store' and accept_state = 'pending' 
				and bom_type = 'spare' and spare_id = %s """%(entry.order_line_id.id,entry.spare_bom_id.id))
			bot_item = cr.fetchone()
			print "bot_itembot_item",bot_item
			if bot_item != None:
				raise osv.except_osv(_('Warning!'),
							_('BOT item Issue is pending to receive !!'))
							
			else:
				### Load finished Items ###
				cr.execute(""" delete from ch_spare_assembly_details where header_id = %s """%(ids[0]))
				
				cr.execute(""" select id,ms_type,position_id,moc_id,item_code,item_name,qty,oth_spec from kg_ms_stores where
					order_line_id = %s and state = 'in_store' and accept_state = 'received' and bom_type = 'spare' and spare_id = %s
					order by ms_type """%(entry.order_line_id.id,entry.spare_bom_id.id))
				finished_items = cr.dictfetchall()
				for item in finished_items:
					
					spare_ass_vals = {
						'header_id': entry.id,
						'ms_type': item['ms_type'],
						'ms_store_id': item['id'],
						'position_id': item['position_id'] or False,
						'moc_id': item['moc_id'],
						'item_code':item['item_code'],
						'item_name':item['item_name'],				
						'qty': item['qty'],		
						'add_spec': item['oth_spec'],			
					}
					ass_line_obj = self.pool.get('ch.spare.assembly.details')
					ass_line_id = ass_line_obj.create(cr, uid, spare_ass_vals)
			
				
												
		self.write(cr, uid, ids, {'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
							
		return True	
	
	
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			### Dynamic Balancing and Pre Hydro Static Test Creation for Pattern ###
			for line_item in entry.line_ids:
				if line_item.ms_type == 'foundry_item':
					qap_dynamic_bal_id = self.pool.get('ch.dynamic.balancing').search(cr,uid,[('header_id','=',entry.qap_plan_id.id),
						('pattern_id','=',line_item.ms_store_id.pattern_id.id)])
					if qap_dynamic_bal_id:
						qap_dynamic_bal_rec = self.pool.get('ch.dynamic.balancing').browse(cr,uid,qap_dynamic_bal_id[0])
						print "qap_dynamic_bal_rec",qap_dynamic_bal_rec
						min_weight = qap_dynamic_bal_rec.min_weight
						max_weight = qap_dynamic_bal_rec.max_weight
					else:
						min_weight = 0.00
						max_weight = 0.00
						
					### Hrdro static pressure from marketing Enquiry ###
					if entry.order_line_id.pump_offer_line_id > 0:
						market_enquiry_rec = self.pool.get('ch.kg.crm.pumpmodel').browse(cr,uid,entry.order_line_id.pump_offer_line_id)
						if market_enquiry_rec:
							hs_pressure = market_enquiry_rec.hydrostatic_test_pressure
						else:
							hs_pressure = 0.00
					else:
						hs_pressure = 0.00
					
					db_flag = False
					hs_flag = False
					if line_item.ms_store_id.pattern_id.need_dynamic_balancing == True:
						db_flag = True
					if line_item.ms_store_id.pattern_id.need_hydro_test == True:
						hs_flag = True
						
					print "db_flag",db_flag
					print "hs_flag",hs_flag
						
					if db_flag == True or hs_flag == True:
						
						part_qap_vals = {
							
							'qap_plan_id': entry.qap_plan_id.id,
							'order_id': entry.order_line_id.header_id.id,
							'order_line_id': entry.order_line_id.id,
							'order_no': entry.order_line_id.order_no,
							'order_category': entry.order_line_id.order_category,
							'pattern_id': line_item.ms_store_id.pattern_id.id,
							'pattern_name': line_item.ms_store_id.pattern_id.pattern_name,
							'item_code': line_item.item_code,
							'item_name': line_item.item_name,
							'moc_id': line_item.moc_id.id,
							'db_min_weight': min_weight,
							'db_max_weight': max_weight,
							'spare_assembly_id': entry.id,
							'spare_assembly_line_id': line_item.id,
							#~ 'order_bom_id': line_item.ms_store_id.ms_id.order_bomline_id.id,
							'hs_pressure': hs_pressure,
							'db_flag':db_flag,
							'hs_flag':hs_flag,
							
							
						}
						
						part_qap_id = self.pool.get('kg.part.qap').create(cr, uid, part_qap_vals)
						
				### Updation in Store ###
				self.pool.get('kg.ms.stores').write(cr,uid,line_item.ms_store_id.id,{'state':'sent_to_ass'})
													
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
							
		return True	
		
	def entry_approve(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'confirmed':
		
			### Checking Test process Remaining ###
			cr.execute(''' select id from kg_part_qap where spare_assembly_id = %s and order_id=%s and order_line_id =%s
				and db_state = 'pending' and db_flag='t' ''',[ids[0],entry.order_line_id.header_id.id,entry.order_line_id.id])
			db_test_process_rem = cr.fetchone()
			
			cr.execute(''' select id from kg_part_qap where spare_assembly_id = %s and order_id=%s and order_line_id =%s
				and hs_state='pending' and hs_flag='t' ''',[ids[0],entry.order_line_id.header_id.id,entry.order_line_id.id])
			hs_test_process_rem = cr.fetchone()
			
			if db_test_process_rem == None and hs_test_process_rem == None:
				#### Updating pump serial number in Part qap ###
				cr.execute(''' update kg_part_qap set pump_serial_no = %s where spare_assembly_id = %s ''',[entry.name,ids[0]])
				### Dimensional Inspection Creation ###
				pump_qap_header_vals = {
				
					'qap_plan_id': entry.qap_plan_id.id,
					'order_id': entry.order_line_id.header_id.id,
					'order_line_id':  entry.order_line_id.id,
					'order_no': entry.order_line_id.order_no,
					'order_category': entry.order_category,
					'pump_model_id': entry.pump_model_id.id,
					'spare_assembly_id': entry.id,
					'moc_construction_id': entry.order_line_id.moc_construction_id.id,
					'test_state':'di',
					'di_state': 'pending',
					'assembly_id': ids[0]
				}
				print "pump_qap_header_vals",pump_qap_header_vals
				pump_qap_id = self.pool.get('kg.pump.qap').create(cr, uid, pump_qap_header_vals)
				
				dim_inspection_id = self.pool.get('ch.dimentional.inspection').search(cr,uid,[('pump_model_id','=',entry.pump_model_id.id)])
				if dim_inspection_id:
					dim_inspection_rec = self.pool.get('ch.dimentional.inspection').browse(cr,uid,dim_inspection_id[0])
					for dim_item in dim_inspection_rec.line_ids:
						print "dim_item",dim_item
						pump_dimension_vals = {
							'header_id': pump_qap_id, 		
							'dimentional_details': dim_item.dimentional_details,
							'min_weight': dim_item.min_weight,
							'max_weight': dim_item.max_weight,	
						}
						pump_dimension_id = self.pool.get('ch.pump.dimentional.details').create(cr, uid, pump_dimension_vals)
						
				self.write(cr, uid, ids, {'state': 'approve','approve_user_id': uid, 'approve_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Warning !!'),
				_('Test process remaining !!'))		
			
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
		return super(kg_spare_assembly, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_spare_assembly, self).write(cr, uid, ids, vals, context)
		
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
	
kg_spare_assembly()



class ch_spare_assembly_details(osv.osv):
	
	_name = "ch.spare.assembly.details"
	_description = "Spare Assembly Details Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.spare.assembly','Spare Assembly Entry', required=True, ondelete='cascade'),
		'ms_type': fields.selection([('foundry_item','Foundry Item'),('ms_item','MS Item'),('bot_item','BOT Item')], 'Item Type',readonly=True),
		'ms_store_id': fields.many2one('kg.ms.stores','Store',domain="[('active','=','t')]"),		
		'position_id': fields.many2one('kg.position.number','Position No.',domain="[('state','=','approved')]"),	
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),		
		'item_code':fields.char('Item Code'),
		'item_name':fields.char('Item Name'),				
		'qty': fields.integer('Quantity', required=True),		
		'add_spec': fields.text('Others Specification'),					
		'remarks': fields.text('Remarks'),					
	}	
	
	def onchange_item(self, cr, uid, ids, position_id, context=None):
		
		value = {'item_code': '','item_name':''}
		if position_id:
			pos_rec = self.pool.get('kg.position.number').browse(cr, uid, position_id, context=context)			
			if pos_rec.pattern_id:
				item_name = pos_rec.pattern_id.name
				item_code = pos_rec.pattern_name
			elif pos_rec.ms_id:
				item_name = pos_rec.ms_id.name
				item_code = pos_rec.ms_code
			elif pos_rec.bot_id:
				item_name = pos_rec.bot_id.name
				item_code = pos_rec.bot_code
			value = {'item_code': item_code,'item_name':item_name}
		else:
			pass			
		return {'value': value}	
	
		
	def _position_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.position_id:					
			cr.execute(""" select position_id from ch_spare_assembly_details where position_id  = '%s' and header_id =%s 				
			""" %(rec.position_id.id,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
	
		
	_constraints = [						
		#~ (_position_validate, 'Please Check Position No should be unique!!!',['Position No.']),			
	   ]
	

ch_spare_assembly_details()	







