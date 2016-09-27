from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import base64
from itertools import groupby

PURPOSE_SELECTION = [
    ('pump','Pump'),('spare','Spare')
]

STATE_SELECTION = [
    ('draft','Draft'),('confirm','WFA'),('plan','Planned'),('close','Closed'),('reject','Rejected')
]

class kg_site_visit_plan(osv.osv):
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		total = 0
		line_ids = ''
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'tot_plan_amt' : 0.0,
			}
			val = val1 = val3 = 0.0
			if order.line_ids:
				total = sum(line.tot_plan_amt for line in order.line_ids)
			res[order.id]['tot_plan_amt'] = total
		return res
		
	_name = "kg.site.visit.plan"
	_description = "Site Visit Plan Entry"
	_order = "from_date desc"

	_columns = {
	
		### Header Details ####
		'name': fields.char('Plan No.', size=128,select=True),
		'region': fields.char('Region',required=True,readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'cr_date': fields.date('Plan Date',readonly=False),
		'from_date': fields.date('From Date',required=True,readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'to_date': fields.date('To Date',required=True,readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'no_of_days': fields.integer('No.of Days',required=True),
		'payment': fields.selection([('sam','SAM'),('customer','Customer'),('both','Both')],'Payment',readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'sam_amt': fields.float('SAM Amount',readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'customer_amt': fields.float('Customer Amount',readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'allowance_date': fields.date('Amount Required On',readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'purpose_of_visit': fields.selection([('service','Service')],'Purpose of Visit'),
		'remarks': fields.text('Remarks',readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'state': fields.selection(STATE_SELECTION,'Status', readonly=True),
		'note': fields.char('Notes'),
		'cancel_remark': fields.text('Cancel Remarks'),
		
		'sv_pending_ids': fields.many2many('kg.site.visit.pending', 'm2m_svp', 'plan_id','pending_id', 'Site Visit Pending', delete=False,
			 domain="[('state','=','pending')]",readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}	),
		'line_ids': fields.one2many('ch.site.visit.plan', 'header_id', "Allowance Breakup", readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
			
		'customer_id': fields.many2one('res.partner','Customer Name',domain=[('customer','=',True),('contact','=',False)]),
		'engineer_id': fields.many2one('hr.employee','Engineer Name',readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'purpose': fields.selection(PURPOSE_SELECTION,'Purpose',readonly=True),
		
		'allowance_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Allowance Amount',
			store=True,multi="sums",help="The total amount",readonly=True),
		'tot_plan_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Plan Amount',
			store=True,multi="sums",help="The total amount",readonly=True),
			
		### Entry Info ####
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'approve_user_id': fields.many2one('res.users', 'Approved By', readonly=True),
		'close_date': fields.datetime('Closed Date', readonly=True),
		'close_user_id': fields.many2one('res.users', 'Closed By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),	   
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_site_visit_plan', context=c),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',
		'active': True,
		'purpose_of_visit': 'service',
		'cr_date' : lambda * a: time.strftime('%Y-%m-%d'),
		
	}
	  
	def _to_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		from_date = rec.from_date
		from_date = str(from_date)
		from_date = datetime.strptime(from_date, '%Y-%m-%d')
		to_date = rec.to_date
		to_date = str(to_date)
		to_date = datetime.strptime(to_date, '%Y-%m-%d')
		print"from_date",from_date
		print"to_date",to_date
		if to_date <= from_date:
			return False
		return True
	
	def _past_date(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		allowance_date = rec.allowance_date
		allowance_date = str(allowance_date)
		allowance_date = datetime.strptime(allowance_date, '%Y-%m-%d')
		if allowance_date >= today:
			return True
		return False
		
	def _check_lineitems(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'plan':
			if not entry.line_ids:
				return False
		return True
		
	_constraints = [		
		
		(_to_date_check, 'Should be greater than from date !!',['To Date']),
		(_past_date, 'System not allow to save with past date. !!',['Amount Required On']),
		(_check_lineitems, 'System not allow to save with empty Plan List !!',['']),
		
	   ]
	   	 
	def onchange_no_of_days(self,cr,uid,ids,from_date,to_date,context=None):
		value = {'no_of_days':0}
		if from_date and to_date:
			d1 = datetime.strptime(from_date, '%Y-%m-%d')
			d2 = datetime.strptime(to_date, '%Y-%m-%d')
			no_of_days = str((d2-d1).days)
			no_of_days = int(no_of_days)
		value = {'no_of_days': no_of_days}
		print"value",value
	
		return {'value': value}
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		ser_no = ''	
		qc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.site.visit.plan')])
		seq_rec = self.pool.get('ir.sequence').browse(cr,uid,qc_seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s',now()::date) """%(qc_seq_id[0],seq_rec.code))
		ser_no = cr.fetchone();
		self.write(cr, uid, ids, {
									'name':ser_no[0],
									'state': 'confirm',
									'confirm_user_id': uid, 
									'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')
			
		 							})
		 												
		return True
	
	def update_plan_line(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		ser_no = ''	
		qc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.site.visit.plan')])
		seq_rec = self.pool.get('ir.sequence').browse(cr,uid,qc_seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s',now()::date) """%(qc_seq_id[0],seq_rec.code))
		ser_no = cr.fetchone();
		self.write(cr, uid, ids,{
								'name':ser_no[0],
								'state': 'confirm',
								})
								
		site_visit_pen_obj = self.pool.get('kg.site.visit.pending')
		plan_line_obj = self.pool.get('ch.site.visit.plan')
		line_ids = []
		if entry.line_ids:
			plan_lines = map(lambda x:x.id,entry.line_ids)
			plan_line_obj.unlink(cr,uid,plan_lines)
			
		if entry.sv_pending_ids:
			site_visit_pen_ids = map(lambda x:x.id,entry.sv_pending_ids)
			site_visit_pen_browse = site_visit_pen_obj.browse(cr,uid,site_visit_pen_ids)
			site_visit_pen_browse = sorted(site_visit_pen_browse, key=lambda k: k.complaint_no.id)
			groups = []
			for key, group in groupby(site_visit_pen_browse, lambda x: x.complaint_line_id.id):
				groups.append(map(lambda r:r,group))
			for key,group in enumerate(groups):
				#~ qty = sum(map(lambda x:float(x.issue_pending_qty),group)) #TODO: qty
				pen_line_ids = map(lambda x:x.id,group)
				customer = group[0].customer_id.id
				pump_id = group[0].pump_id.id
				complaint_no = group[0].complaint_no.id
				registration_date = group[0].registration_date
				sv_pending_id = group[0].id
				wo_no = group[0].wo_no
				wo_line_id = group[0].wo_line_id.id
				moc_const_id = group[0].moc_const_id.id
				item_code = group[0].item_code
				item_name = group[0].item_name
				defect_id = group[0].defect_id.id
				s_no = group[0].s_no
				dealer_id = group[0].complaint_line_id.dealer_id.id
				purpose = group[0].purpose
				vals = {
				
					'customer_id':customer,
					'complaint_no':complaint_no,
					'pump_id':pump_id,
					'registration_date':registration_date,
					'sv_pending_id':sv_pending_id,
					'wo_no':wo_no,
					'wo_line_id':wo_line_id,
					'moc_const_id':moc_const_id,
					'item_code':item_code,
					'item_name':item_name,
					'defect_id':defect_id,
					's_no':s_no,
					'dealer_id':dealer_id,
					'purpose':purpose,
					
					}
				if ids:
					self.write(cr,uid,ids[0],{'line_ids':[(0,0,vals)]})
		
		return True
			
	def entry_approve(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		
		cr.execute(""" select pending_id from m2m_svp where plan_id = %s """ %(entry.id))
		pen_data = cr.dictfetchall()
		print"pen_datapen_data",pen_data
		for item in pen_data:
			pen_sql = """ update kg_site_visit_pending set state='plan' where id = %s """ %(item['pending_id'])
			cr.execute(pen_sql)
		for item in entry.line_ids:
			if item.no_of_days <= 0:
				raise osv.except_osv(
					_('Warning!'),
					_('%s System not allow to save without no of days'%(item.complaint_no.name)))
			self.pool.get('ch.site.visit.plan').write(cr,uid,item.id,{'state':'pending'})
		if entry.payment == 'both':
			tot_amt = 0
			tot_amt = entry.sam_amt + entry.customer_amt
			if tot_amt > entry.tot_plan_amt:
				raise osv.except_osv(
					_('Warning!'),
					_('System should not be accept greater than total plan amount'))
		
		if not entry.line_ids:
			raise osv.except_osv(
				_('Warning!'),
				_('System not allow to save with empty Plan Details'))
		self.write(cr, uid, ids, {
									'state': 'plan',
									'approve_user_id': uid, 
									'approve_date': time.strftime('%Y-%m-%d %H:%M:%S')
		 							})
		 												
		return True
		
	def entry_reject(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		
		self.write(cr, uid, ids, {
									'state': 'reject',
									'close_user_id': uid, 
									'close_date': time.strftime('%Y-%m-%d %H:%M:%S')
								})
		
		return True
		
	def entry_close(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		
		self.write(cr, uid, ids, {
									'state': 'close',
									'close_user_id': uid, 
									'close_date': time.strftime('%Y-%m-%d %H:%M:%S')
								})
		
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
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_site_visit_plan, self).write(cr, uid, ids, vals, context)
								
kg_site_visit_plan()


class ch_site_visit_plan(osv.osv):
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		total = 0
		line_ids = ''
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'tot_plan_amt' : 0.0,
			}
			val = val1 = val3 = 0.0
			if order.ch_line_ids:
				total = sum(line.total_amt for line in order.ch_line_ids)
			res[order.id]['tot_plan_amt'] = total
		return res
		
	_name = "ch.site.visit.plan"
	_description = "Ch Site Visit Plan Details"
	
	_columns = {
	
		'header_id': fields.many2one('kg.site.visit.plan', 'Plan No.', ondelete='cascade'),
		'ch_line_ids': fields.one2many('ch.site.visit.plan.allowance', 'header_id', "Allowance Breakup"),
		'line_ids': fields.one2many('ch.sv.foundry.item', 'header_id', "Foundry Item",readonly=True, states={'pending':[('readonly',False)]}),
		'line_ids_a': fields.one2many('ch.sv.ms.item', 'header_id', "MS Item",readonly=True, states={'pending':[('readonly',False)]}),
		'line_ids_b': fields.one2many('ch.sv.bot.item', 'header_id', "BOT Item",readonly=True, states={'pending':[('readonly',False)]}),
		'line_ids_c': fields.one2many('ch.sv.access', 'header_id', "Accessories",readonly=True, states={'pending':[('readonly',False)]}),
		
		'sv_pending_id': fields.many2one('kg.site.visit.pending','Site Visit Pending', ondelete='cascade'),
		'complaint_no': fields.many2one('kg.service.enquiry','Complaint No'),
		'customer_id': fields.many2one('res.partner','Customer Name',domain=[('customer','=',True),('contact','=',False)]),
		'dealer_id': fields.many2one('res.partner','Dealer Name',domain=[('dealer','=',True),('contact','=',False)]),
		'registration_date': fields.date('Complaint Date'),
		'wo_no': fields.char('WO No'),
		'wo_line_id': fields.many2one('ch.work.order.details','WO No'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Model'),
		'moc_const_id': fields.many2one('kg.moc.construction','MOC Construction'),
		'item_code': fields.char('Item Code'),
		'item_name': fields.char('Item Name'),
		'defect_id': fields.many2one('kg.defect.master','Pump Defect type'),
		'no_of_days': fields.integer('No Of Days'),
		's_no': fields.char('Serial No.'),
		
		'decision': fields.selection([('no_fault','No Fault'),('service','Service Done'),('replace','Replacement(Cost)'),('replace_free','Replacement(Free)')],'Decision',readonly=True, states={'pending':[('readonly',False)]}),
		'expense_amt': fields.float('Expense Amount',readonly=True, states={'pending':[('readonly',False)]}),
		'bal_amt': fields.float('Balance Amount'),
		'remarks': fields.text('Remarks'),
		'state': fields.selection([('draft','Draft'),('pending','Pending'),('close','Closed')],'Status',readonly=True),
		'plan_date': fields.related('header_id','cr_date', type='date', string='Plan Date'),
		'load_bom': fields.boolean('Load BOM',readonly=True, states={'pending':[('readonly',False)]}),
		'purpose': fields.selection([('pump','Pump'),('spare','Spare')],'Purpose'),
		'replace_categ': fields.selection([('pump','Pump'),('spare','Spare')],'Replace Category',readonly=True, states={'pending':[('readonly',False)]}),
		'returnable': fields.selection([('yes','Yes'),('no','No')],'Returnable',readonly=True, states={'pending':[('readonly',False)]}),
		
		'tot_plan_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Plan Amount',
			store=True,multi="sums",help="The total amount",readonly=True),
		
		# Entry Info
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		
	}
	
	_defaults = {
	
		'load_bom': False,
		'state': 'draft',
		
	}
	
	#~ def _check_no_of_days(self, cr, uid, ids, context=None):
		#~ entry = self.browse(cr,uid,ids[0])
		#~ if entry.no_of_days <= 0:
			#~ return False
		#~ return True
	
	#~ _constraints = [		
		
		#~ (_check_no_of_days, 'System not allow to save with zero value !!',['No Of Days']),
		
	   #~ ]
	
	def onchange_bal_amt(self, cr, uid, ids, expense_amt,tot_plan_amt):
		value = {'bal_amt':0}
		tot = 0.00
		if expense_amt and tot_plan_amt:
			tot = tot_plan_amt - expense_amt
			value = {'bal_amt': tot}	
		return {'value': value}
		
	def onchange_load_bom(self, cr, uid, ids, load_bom,pump_id,wo_line_id,purpose,moc_const_id,decision,replace_categ):
		fou_vals=[]
		ms_vals=[]
		bot_vals=[]
		data_rec = ''
		print"pump_id",pump_id
		print"load_bom",load_bom
		if load_bom == True and decision in ('replace','replace_free'):
			if replace_categ == 'pump' or replace_categ == 'spare':
				if wo_line_id:
					print"wo_line_idwo_line_id",wo_line_id
					wo_obj = self.pool.get('ch.work.order.details').search(cr,uid,[('id','=',wo_line_id)])
					if wo_obj:
						data_rec = self.pool.get('ch.work.order.details').browse(cr, uid, wo_obj[0])
				else:
					bom_obj = self.pool.get('kg.bom').search(cr, uid, [('pump_model_id','=',pump_id),('state','=','approved')])
					if bom_obj:
						data_rec = self.pool.get('kg.bom').browse(cr, uid, bom_obj[0])
			print"data_recdata_rec",data_rec
			if replace_categ == 'spare':
				is_applicable = False
			elif replace_categ == 'pump':
				is_applicable = True
			if data_rec:
				if pump_id:
					print"-------------------------------"
					if data_rec.line_ids:
						for item in data_rec.line_ids:
							#~ if item.flag_applicable == True:
								moc_id = ''
								if wo_line_id:
									moc_id = item.moc_id.id
								else:
									pat_obj = self.pool.get('kg.pattern.master').search(cr,uid,[('id','=',item.pattern_id.id)])
									print"pat_objpat_obj",pat_obj
									if pat_obj:
										pat_rec = self.pool.get('kg.pattern.master').browse(cr,uid,pat_obj[0])
										if pat_rec.line_ids:
											#~ for ele in pat_rec.line_ids:
											pat_line_obj = self.pool.get('ch.mocwise.rate').search(cr,uid,[('code','=',moc_const_id),('header_id','=',pat_rec.id)])
											if pat_line_obj:
												pat_line_rec = self.pool.get('ch.mocwise.rate').browse(cr,uid,pat_line_obj[0])
												moc_id = pat_line_rec.moc_id.id
								fou_vals.append({
												'position_id': item.position_id.id,
												'pattern_id': item.pattern_id.id,
												'pattern_name': item.pattern_name,
												'moc_id': moc_id,
												'qty': item.qty,
												'load_bom': True,
												'is_applicable': is_applicable,
												})
						print"fou_valsfou_vals",fou_vals
					if data_rec.line_ids_a:
						for item in data_rec.line_ids_a:
							#~ if item.flag_applicable == True:
							moc_id = ''
							if wo_line_id:
								moc_id = item.moc_id.id
							else:
								ms_obj = self.pool.get('kg.machine.shop').search(cr,uid,[('id','=',item.ms_id.id)])
								print"ms_objms_obj",ms_obj
								if ms_obj:
									ms_rec = self.pool.get('kg.machine.shop').browse(cr,uid,ms_obj[0])
									if ms_rec.line_ids_a:
										#~ for ele in ms_rec.line_ids_a:
										cons_rec = self.pool.get('kg.moc.construction').browse(cr,uid,moc_const_id)
										ms_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',cons_rec.code),('header_id','=',ms_rec.id)])
										if ms_line_obj:
											ms_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,ms_line_obj[0])
											moc_id = ms_line_rec.moc_id.id
							ms_vals.append({
											'name': item.name,
											'position_id': item.position_id.id,							
											'ms_id': item.ms_id.id,
											'moc_id': moc_id,
											'qty': item.qty,
											'load_bom': True,
											'is_applicable': is_applicable,
											})
						print"ms_valsms_vals",ms_vals
					if data_rec.line_ids_b:
						for item in data_rec.line_ids_b:
							#~ if item.flag_applicable == True:
							moc_id = ''
							if wo_line_id:
								moc_id = item.moc_id.id
								item_name = item.item_name
							else:
								item_name = item.name
								bot_obj = self.pool.get('kg.machine.shop').search(cr,uid,[('id','=',item.bot_id.id)])
								print"bot_objbot_obj",bot_obj
								if bot_obj:
									bot_rec = self.pool.get('kg.machine.shop').browse(cr,uid,bot_obj[0])
									if bot_rec.line_ids_a:
										#~ for ele in bot_rec.line_ids_a:
										cons_rec = self.pool.get('kg.moc.construction').browse(cr,uid,moc_const_id)
										bot_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',cons_rec.code),('header_id','=',bot_rec.id)])
										if bot_line_obj:
											bot_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,bot_line_obj[0])
											moc_id = bot_line_rec.moc_id.id
							bot_vals.append({
											'item_name': item_name,
											'ms_id': item.bot_id.id,
											'moc_id': moc_id,
											'qty': item.qty,
											'load_bom': True,
											'is_applicable': is_applicable,
											})
						print"bot_valsbot_vals",bot_vals

		return {'value': {'line_ids': fou_vals,'line_ids_a': ms_vals,'line_ids_b': bot_vals}}
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		source = ''
		if entry.decision in ('replace','replace_free'):
			if entry.replace_categ == 'replace_free':
				source = 'service'
			else:
				source = 'market'
			crm_id = self.pool.get('kg.crm.enquiry').create(cr,uid,{'customer_id': entry.customer_id.id,
																	'purpose': entry.replace_categ,
																	'source': source,
																	'entry_mode': 'auto',
																	'enquiry_no': entry.complaint_no.name,
																	'market_division': entry.sv_pending_id.complaint_line_id.market_division,
																				
																	})
			if crm_id:
				if entry.line_ids_c:
					access = 'yes'
				else:
					access = 'no'
				enquiry_line_id = self.pool.get('ch.kg.crm.pumpmodel').create(cr,uid,{'header_id': crm_id,
																					   'pump_id': entry.pump_id.id,
																					   'moc_const_id': entry.moc_const_id.id,
																					   'qty':1,
																					   'wo_line_id':entry.wo_line_id.id,
																					   'pumpseries_id':entry.pump_id.series_id.id,
																					   'load_bom':True,
																					   'purpose_categ':entry.replace_categ,
																					   'acces':access,
																					   'wo_no':entry.wo_no,
																					   'spare_pump_id': entry.pump_id.id,
																					   's_no':entry.s_no,
																					   'spare_moc_const_id': entry.moc_const_id.id,
																					   'spare_pumpseries_id':entry.pump_id.series_id.id,
																					   'spare_load_bom':True,
																						})
				print"enquiry_line_idenquiry_line_id",enquiry_line_id
				if entry.line_ids:
					for item in entry.line_ids:
						if item.is_applicable == True:
							fou_id = self.pool.get('ch.kg.crm.foundry.item').create(cr,uid,{'header_id': enquiry_line_id,
																					'qty': item.qty,
																					'position_id': item.position_id.id,
																					'pattern_name': item.pattern_name,
																					'pattern_id': item.pattern_id.id,
																					'moc_id': item.moc_id.id,
																					'is_applicable': item.is_applicable,
																					})
					if entry.line_ids_a:																		
						for item in entry.line_ids_a:
							if item.is_applicable == True:
								ms_id = self.pool.get('ch.kg.crm.machineshop.item').create(cr,uid,{'header_id': enquiry_line_id,
																					'qty': item.qty,
																					'position_id': item.position_id.id,
																					'ms_id': item.ms_id.id,
																					'moc_id': item.moc_id.id,
																					'is_applicable': item.is_applicable,
																					})
					if entry.line_ids_b:																
						for item in entry.line_ids_b:
							if item.is_applicable == True:
								ms_id = self.pool.get('ch.kg.crm.bot').create(cr,uid,{'header_id': enquiry_line_id,
																					'qty': item.qty,
																					'product_temp_id': item.product_temp_id.id,
																					'position_id': item.position_id.id,
																					'ms_id': item.ms_id.id,
																					'moc_id': item.moc_id.id,
																					'is_applicable': item.is_applicable,
																					})
					if entry.line_ids_c:			
						for item in entry.line_ids_c:	
							if item.is_applicable == True:
								access_id = self.pool.get('ch.kg.crm.accessories').create(cr,uid,{'header_id': enquiry_line_id,
																						  'qty': item.qty,
																						  'access_id': item.access_id.id,
																						  'is_applicable': item.is_applicable,
																						})																	
																					
		self.pool.get('kg.site.visit.pending').write(cr,uid,entry.sv_pending_id.id,{'state':'close'})
		
		self.write(cr, uid, ids, {
									'state': 'close',
									'confirm_user_id': uid, 
									'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')
		 							})
		 
		part_obj = self.pool.get('kg.site.visit.plan').search(cr,uid,[('id','=',entry.header_id.id)])
		if part_obj:
			part_rec = self.pool.get('kg.site.visit.plan').browse(cr,uid,part_obj[0])
			part_len = len(part_rec.line_ids)
		ch_obj = self.search(cr,uid,[('header_id','=',entry.header_id.id),('state','=','close')])
		if ch_obj:
			ch_len = len(ch_obj)
		if ch_len == part_len:
			self.pool.get('kg.site.visit.plan').write(cr,uid,entry.header_id.id,{'state':'close'})
		
		close_status = self.pool.get('kg.site.visit.pending')._close_status(cr,uid,entry.sv_pending_id.id)
		complaint_id = self.pool.get('kg.service.enquiry').write(cr,uid,close_status,{'state':'close'})
		
		return True
		
ch_site_visit_plan()

class ch_site_visit_plan_allowance(osv.osv):

	_name = "ch.site.visit.plan.allowance"
	_description = "Ch Site Visit Plan Allowance Details"
	
	_columns = {
	
		'header_id':fields.many2one('ch.site.visit.plan', 'Ch Site Visit Plan', ondelete='cascade'),
		'date': fields.date('Date'),
		'description': fields.char('Description'),
		'mode_of_travel': fields.selection([('auto','Auto'),('bus','BUS'),('train','Train'),('flight','Flight'),('ship','Ship')],'Mode of Travel'),
		'out_station_amt': fields.float('Out Staion'),
		'local_travel_amt': fields.float('Local Travel Amount'),
		'boarding_amt': fields.float('Boarding Amount'),
		'lodging_amt': fields.float('Lodging Amount'),
		'misc_charge_amt': fields.float('Misc. Charges Amount'),
		'total_amt': fields.float('Total Amount'),
		'details': fields.text('Additional Details'),
		
	}
	
	def onchange_total(self,cr,uid,ids,out_station_amt,local_travel_amt,boarding_amt,lodging_amt,misc_charge_amt,context=None):
		value = {'total_amt':''}
		total = 0.00
		total = out_station_amt + local_travel_amt + boarding_amt + lodging_amt + misc_charge_amt
		print"total",total
		value = {'total_amt': total}
		return {'value': value}
	
ch_site_visit_plan_allowance()


class ch_sv_foundry_item(osv.osv):

	_name = "ch.sv.foundry.item"
	_description = "Ch SV Foundry Item"
	
	_columns = {
	
		### Foundry Item Details ####
		'header_id':fields.many2one('ch.site.visit.plan', 'Ch SV', ondelete='cascade'),
		'plan_id':fields.many2one('kg.site.visit.plan', 'Plan No.'),
		'pump_id':fields.many2one('kg.pumpmodel.master', 'Pump'),
		'qty':fields.integer('Quantity'),
		'oth_spec':fields.char('Other Specification'),
		'position_id': fields.many2one('kg.position.number','Position No'),
		'csd_no': fields.char('CSD No.', size=128),
		'pattern_name': fields.char('Pattern Name'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No'),
		'remarks': fields.char('Remarks'),
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		
	}
	
	_defaults = {
		
		'is_applicable':False,
		'load_bom':False,
		
	}
	
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_sv_foundry_item, self).write(cr, uid, ids, vals, context)
	
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False
		return True
	
	_constraints = [
	
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
		
	def onchange_pattern_name(self, cr, uid, ids, pattern_code,pattern_name):
		value = {'pattern_name':''}
		pattern_obj = self.pool.get('kg.pattern.master').search(cr,uid,([('id','=',pattern_code)]))
		if pattern_obj:
			pattern_rec = self.pool.get('kg.pattern.master').browse(cr,uid,pattern_obj[0])
			value = {'pattern_name':pattern_rec.pattern_name}
		return {'value': value}
	
ch_sv_foundry_item()


class ch_sv_ms_item(osv.osv):

	_name = "ch.sv.ms.item"
	_description = "Ch SV MS Item"
	
	_columns = {
	
		### machineshop Item Details ####
		'header_id':fields.many2one('ch.site.visit.plan', 'Ch SV', ondelete='cascade'),
		'plan_id':fields.many2one('kg.site.visit.plan', 'Plan No.'),
		'pos_no': fields.related('position_id','name', type='integer', string='Position No', store=True),
		'position_id': fields.many2one('kg.position.number','Position No'),
		'csd_no': fields.char('CSD No.'),
		'bom_id': fields.many2one('kg.bom','BOM'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','ms')], ondelete='cascade'),
		'name': fields.related('ms_id','name', type='char',size=128,string='Item Name', store=True),
		#~ 'ms_line_id':fields.many2one('ch.machineshop.details', 'Item Name'),
		'name':fields.char('Item Name', size=128),	  
		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
		#'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'remarks':fields.text('Remarks'),   
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		
	}
	
	_defaults = {
		
		'is_applicable':False,
		'load_bom':False,
		
	}
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_sv_ms_item, self).write(cr, uid, ids, vals, context)
		
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False
		return True
	
	_constraints = [
	
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
		
ch_sv_ms_item()


class ch_sv_bot_item(osv.osv):

	_name = "ch.sv.bot.item"
	_description = "Ch SV BOT Item"
	
	_columns = {
	
		### BOT Item Details ####
		'header_id':fields.many2one('ch.site.visit.plan', 'Ch SV', ondelete='cascade'),
		'plan_id':fields.many2one('kg.site.visit.plan', 'Plan No.'),
		'product_temp_id':fields.many2one('product.product', 'Product Name',domain = [('type','=','bot')], ondelete='cascade'),
		#~ 'bot_line_id':fields.many2one('ch.bot.details', 'Item Name'),
		'position_id': fields.many2one('kg.position.number','Position No'),
		'bom_id': fields.many2one('kg.bom','BOM'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','bot')], ondelete='cascade'),
		'item_name': fields.related('ms_id','name', type='char', size=128, string='Item Name', store=True, readonly=True),
		'code':fields.char('Item Code', size=128),	  
		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
		#'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'remarks':fields.text('Remarks'),   
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		
	}
	
	_defaults = {
		
		'is_applicable':False,
		'load_bom':False,
		
	}
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_sv_bot_item, self).write(cr, uid, ids, vals, context)
		
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False
		return True
	
	_constraints = [
	
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
ch_sv_bot_item()


class ch_sv_access(osv.osv):

	_name = "ch.sv.access"
	_description = "Ch SV Accessories"
	
	_columns = {
	
		### Accessories Item Details ####
		'header_id':fields.many2one('ch.site.visit.plan', 'Plan No', ondelete='cascade'),
		'plan_id':fields.many2one('kg.site.visit.plan', 'Plan No.'),
		'access_id': fields.many2one('kg.accessories.master','Accessories',domain="[('active','=','t'),('state','not in',('draft','reject','cancal'))]"),
		'qty': fields.float('Qty'),
		'is_applicable': fields.boolean('Is Applicable'),
		
	}
	
	_defaults = {
		
		'is_applicable':True,
		
	}
	
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_sv_access, self).write(cr, uid, ids, vals, context)
		
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False
		return True
	
	_constraints = [
	
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
		
ch_sv_access()

