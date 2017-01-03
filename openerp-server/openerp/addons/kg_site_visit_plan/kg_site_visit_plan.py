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
		#~ 'payment': fields.selection([('sam','SAM'),('customer','Customer'),('both','Both')],'Payment',readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		#~ 'sam_amt': fields.float('SAM Amount',readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		#~ 'customer_amt': fields.float('Customer Amount',readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'allowance_date': fields.date('Amount Required On',readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'purpose_of_visit': fields.selection([('service','Service')],'Purpose of Visit'),
		'remarks': fields.text('Remarks',readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'state': fields.selection(STATE_SELECTION,'Status', readonly=True),
		'note': fields.char('Notes'),
		'cancel_remark': fields.text('Cancel Remarks'),
		#~ 'day_charge': fields.float('Charges/Day',readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		
		'sv_pending_ids': fields.many2many('kg.site.visit.pending', 'm2m_svp', 'plan_id','pending_id', 'Site Visit Pending', delete=False,
			 domain="[('state','=','pending')]",readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}	),
		'line_ids': fields.one2many('ch.site.visit.plan', 'header_id', "Allowance Breakup", readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		
		'customer_id': fields.many2one('res.partner','Customer Name',domain=[('customer','=',True),('contact','=',False)]),
		'engineer_id': fields.many2one('hr.employee','Engineer Name',required=True, readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'purpose': fields.selection(PURPOSE_SELECTION,'Purpose',readonly=True),
		
		'allowance_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Allowance Amount',
			store=True,multi="sums",help="The total amount",readonly=True),
		'tot_plan_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Plan Amount',
			store=True,multi="sums",help="The total amount",readonly=True),
			
		### Entry Info ####
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'crt_date': fields.datetime('Created Date',readonly=True),
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
		'crt_date': time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',
		'active': True,
		'purpose_of_visit': 'service',
		'cr_date' : lambda * a: time.strftime('%Y-%m-%d'),
		
	}
	  
	def _to_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		from_date = str(rec.from_date)
		from_date = datetime.strptime(from_date, '%Y-%m-%d')
		to_date = str(rec.to_date)
		to_date = datetime.strptime(to_date, '%Y-%m-%d')
		if to_date <= from_date:
			return False
		return True
	
	def _past_date(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = str(date.today())
		today = datetime.strptime(today, '%Y-%m-%d')
		allowance_date = str(rec.allowance_date)
		allowance_date = datetime.strptime(allowance_date, '%Y-%m-%d')
		if allowance_date >= today:
			return True
		return False
		
	def _from_past_date(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = str(date.today())
		today = datetime.strptime(today, '%Y-%m-%d')
		from_date = str(rec.from_date)
		from_date = datetime.strptime(from_date, '%Y-%m-%d')
		if from_date >= today:
			return True
		return False
		
	def _check_lineitems(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'plan':
			if not entry.line_ids:
				return False
		return True
		
	def _check_sv_pending(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if not entry.sv_pending_ids:
			raise osv.except_osv(_('Warning!'),
				_('System should not be save with out plan details !'))
		return True
		
	def _check_allowance(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		total = 0
		if entry.state in ('plan'):
			if entry.line_ids:
				for item in entry.line_ids:
					if not item.ch_line_ids:
						raise osv.except_osv(_('Warning!'),
							_('System should not be save with out Allowance Breakups !'))
					elif item.ch_line_ids:
						for ele in item.ch_line_ids:
							if ele.date >= entry.from_date and ele.date <= entry.to_date:
								pass
							else:
								invalid_date = datetime.strptime(ele.date, '%Y-%m-%d')
								invalid_date = invalid_date.strftime('%d/%m/%Y')
								raise osv.except_osv(_('Warning!'),
									_('%s Allowance date should be greater than or equal From date or less than or equal To date !'%(invalid_date)))
				
				total = sum(ele.no_of_days for ele in entry.line_ids)
				if total > entry.no_of_days:
					raise osv.except_osv(_('Warning!'),
						_('No.of days exceeds from Total no.of days !'))
		
		return True
	
	_constraints = [		
		
		#~ (_to_date_check, 'Should be greater than from date !!',['To Date']),
		#~ (_past_date, 'System not allow to save with past date. !!',['Amount Required On']),
		#~ (_from_past_date, 'System not allow to save with past date. !!',['From Date']),
		(_check_lineitems, 'System not allow to save with empty Plan List !',['']),
		(_check_sv_pending, 'System not allow to save with empty Plan Details !',['']),
		(_check_allowance, 'System not allow to save with empty Allowance Breakups !',['']),
		
	   ]
	   	 
	def onchange_no_of_days(self,cr,uid,ids,from_date,to_date,context=None):
		value = {'no_of_days':0}
		no_of_days = 0
		if not from_date:
			raise osv.except_osv(_('Warning!'),
				_('Please enter From date'))
		if from_date and to_date:
			d1 = datetime.strptime(from_date, '%Y-%m-%d')
			d2 = datetime.strptime(to_date, '%Y-%m-%d')
			no_of_days = str((d2-d1).days)
			no_of_days = int(no_of_days)
			if no_of_days == 0:
				no_of_days = 1
			elif no_of_days > 0:
				no_of_days = no_of_days + 1
		value = {'no_of_days': no_of_days}
		if from_date and to_date:
			if to_date < from_date:
				raise osv.except_osv(_('Warning!'),
					_('To Date should not be less than From Date! '))
			
		print"value",value
	
		return {'value': value}
		
	def onchange_allowance_date(self,cr,uid,ids,from_date,to_date,allowance_date,context=None):
		if from_date and to_date and allowance_date:
			if allowance_date >= from_date and allowance_date <= to_date:
				pass
			else:
				raise osv.except_osv(_('Warning!'),
					_('Amount Required On should be greater than or equal From date or less than or equal To date! '))
		return True
		
	def onchange_from_date(self,cr,uid,ids,from_date,context=None):
		value = {'to_date':''}
		if from_date:
			from_date = from_date
			curnt_date = time.strftime('%Y-%m-%d')
			if from_date < curnt_date:
				raise osv.except_osv(_('Warning!'),
					_('From date not accept with past date! '))
		return {'value': value}
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			ser_no = ''	
			qc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.site.visit.plan')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,qc_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s',now()::date) """%(qc_seq_id[0],seq_rec.code))
			ser_no = cr.fetchone();
			
			self.date_validation(cr,uid,entry)
			
			self.write(cr, uid, ids, {
										'name':ser_no[0],
										'state': 'confirm',
										'confirm_user_id': uid, 
										'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')
				
										})
		 												
		return True
	
	def update_plan_line(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state in ('draft','confirm'):
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
		if entry.state == 'confirm':
			cr.execute(""" select pending_id from m2m_svp where plan_id = %s """ %(entry.id))
			pen_data = cr.dictfetchall()
			print"pen_datapen_data",pen_data
			for item in pen_data:
				pen_sql = """ update kg_site_visit_pending set state='plan' where id = %s """ %(item['pending_id'])
				cr.execute(pen_sql)
			for item in entry.line_ids:
				if item.no_of_days <= 0:
					raise osv.except_osv(_('Warning!'),
						_('%s System not allow to save without no of days'%(item.complaint_no.name)))
				self.pool.get('ch.site.visit.plan').write(cr,uid,item.id,{'state':'pending'})
			#~ if entry.payment == 'both':
				#~ tot_amt = 0
				#~ tot_amt = entry.sam_amt + entry.customer_amt
				#~ if tot_amt > entry.tot_plan_amt:
					#~ raise osv.except_osv(
						#~ _('Warning!'),
						#~ _('System should not be accept greater than total plan amount'))
			
			if not entry.line_ids:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to save with empty Plan Details'))
			
			today = str(date.today())
			today = datetime.strptime(today, '%Y-%m-%d')
			from_date = str(entry.from_date)
			from_date = datetime.strptime(from_date, '%Y-%m-%d')
			to_date = str(entry.to_date)
			to_date = datetime.strptime(to_date, '%Y-%m-%d')
			allowance_date = str(entry.allowance_date)
			allowance_date = datetime.strptime(allowance_date, '%Y-%m-%d')
			if from_date < today:
				raise osv.except_osv(_('Warning!'),
					_('From date not accept with past date! '))
			elif allowance_date < today:
				raise osv.except_osv(_('Warning!'),
					_('Amount Required On not accept with past date! '))
			elif from_date > to_date:
				raise osv.except_osv(_('Warning!'),
					_('To Date should not be greater than From date! '))
			elif allowance_date > to_date:
				raise osv.except_osv(_('Warning!'),
					_('Amount Required On should not be greater than To date! '))
			
			self.date_validation(cr,uid,entry)
			
			self.write(cr, uid, ids, {
										'state': 'plan',
										'approve_user_id': uid, 
										'approve_date': time.strftime('%Y-%m-%d %H:%M:%S')
										})
		 												
		return True
	
	def date_validation(self,cr,uid,entry,context=None):
		
		today = str(date.today())
		today = datetime.strptime(today, '%Y-%m-%d')
		from_date = str(entry.from_date)
		from_date = datetime.strptime(from_date, '%Y-%m-%d')
		to_date = str(entry.to_date)
		to_date = datetime.strptime(to_date, '%Y-%m-%d')
		allowance_date = str(entry.allowance_date)
		allowance_date = datetime.strptime(allowance_date, '%Y-%m-%d')
		if from_date < today:
			raise osv.except_osv(_('Warning!'),
				_('From date not accept with past date! '))
		elif allowance_date < today:
			raise osv.except_osv(_('Warning!'),
				_('Amount Required On not accept with past date! '))
		elif from_date > to_date:
			raise osv.except_osv(_('Warning!'),
				_('To Date should not be greater than From date! '))
		elif allowance_date > to_date:
			raise osv.except_osv(_('Warning!'),
				_('Amount Required On should not be greater than To date! '))
		
		return True
			
	def entry_reject(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'confirm':
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
		total = expense = 0
		line_ids = ''
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'tot_plan_amt' : 0.0,
				'expense_amt' : 0.0,
				'bal_amt' : 0.0,
			}
			val = val1 = val3 = 0.0
			if order.ch_line_ids:
				total = sum(line.total_amt for line in order.ch_line_ids)
			if order.ch_line_ids:
				expense = sum(line.total_amt for line in order.ch_line_ids_a)
			res[order.id]['tot_plan_amt'] = total
			res[order.id]['expense_amt'] = expense
			res[order.id]['bal_amt'] = total - expense
		return res
		
	_name = "ch.site.visit.plan"
	_description = "Ch Site Visit Plan Details"
	
	_columns = {
	
		'header_id': fields.many2one('kg.site.visit.plan', 'Plan No.', ondelete='cascade'),
		'ch_line_ids': fields.one2many('ch.site.visit.plan.allowance', 'header_id', "Allowance Breakup"),
		'ch_line_ids_a': fields.one2many('ch.site.visit.plan.expense', 'header_id', "Expense Details"),
		'line_ids': fields.one2many('ch.sv.foundry.item', 'header_id', "Foundry Item"),
		'line_ids_a': fields.one2many('ch.sv.ms.item', 'header_id', "MS Item"),
		'line_ids_b': fields.one2many('ch.sv.bot.item', 'header_id', "BOT Item"),
		'line_ids_c': fields.one2many('ch.sv.access', 'header_id', "Accessories",readonly=True, states={'pending':[('readonly',False)]}),
		
		'sv_pending_id': fields.many2one('kg.site.visit.pending','Site Visit Pending', ondelete='cascade'),
		'complaint_no': fields.many2one('kg.service.enquiry','Complaint No'),
		'customer_id': fields.many2one('res.partner','Customer Name',domain=[('customer','=',True),('contact','=',False)]),
		'dealer_id': fields.many2one('res.partner','Dealer Name',domain=[('dealer','=',True),('contact','=',False)]),
		'registration_date': fields.date('Complaint Date'),
		'wo_no': fields.char('Old WO No'),
		'wo_line_id': fields.many2one('ch.work.order.details','WO No'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Model'),
		'moc_const_id': fields.many2one('kg.moc.construction','MOC Construction'),
		'item_code': fields.char('Item Code'),
		'item_name': fields.char('Item Name'),
		'defect_id': fields.many2one('kg.defect.master','Pump Defect type'),
		'no_of_days': fields.integer('No Of Days'),
		's_no': fields.char('Serial No.'),
		'payment': fields.selection([('sam','SAM'),('customer','Customer'),('both','Both')],'Payment'),
		'sam_amt': fields.float('SAM Amount'),
		'customer_amt': fields.float('Customer Amount'),
		'day_charge': fields.float('Charges/Day'),
		'decision': fields.selection([('attended','Attended - Not Completed'),('not_attended','Not Attended'),('replace','Replacement(Cost)'),('replace_free','Replacement(Free)'),('completed','Completed')],'Decision',readonly=True, states={'pending':[('readonly',False)]}),
		'defect_id': fields.many2one('kg.defect.master','Defect Type',domain="[('is_full_pump','=',True)]"),
		'complaint_due_to': fields.selection([('sam','SAM'),('customer','Customer')],'Complaint Due To',readonly=True, states={'pending':[('readonly',False)]}),
		'remarks': fields.text('Remarks'),
		'state': fields.selection([('draft','Draft'),('pending','Pending'),('close','Closed')],'Status',readonly=True),
		'plan_date': fields.related('header_id','cr_date', type='date', string='Plan Date'),
		'load_bom': fields.boolean('Load BOM',readonly=True, states={'pending':[('readonly',False)]}),
		'purpose': fields.selection([('pump','Pump'),('spare','Spare')],'Purpose'),
		'replace_categ': fields.selection([('pump','Pump'),('spare','Spare')],'Replace Category',readonly=True, states={'pending':[('readonly',False)]}),
		'returnable': fields.selection([('yes','Yes'),('no','No')],'Returnable',readonly=True, states={'pending':[('readonly',False)]}),
		
		'tot_plan_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Plan Amount',
			store=True,multi="sums",help="The total amount",readonly=True),
		'expense_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Expense Amount',
			store=True,multi="sums",help="The total amount",readonly=True),
		'bal_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Balance Amount',
			store=True,multi="sums",help="The total amount",readonly=True),
		
		# Entry Info
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		
	}
	
	_defaults = {
	
		'load_bom': False,
		'state': 'draft',
		
	}
	
	def _duplicate_removed(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.replace_categ in ('pump','spare') and rec.load_bom != True:
			cr.execute(''' delete from ch_sv_foundry_item where header_id = %s '''%(rec.id))
			cr.execute(''' delete from ch_sv_ms_item where header_id = %s '''%(rec.id))
			cr.execute(''' delete from ch_sv_bot_item where header_id = %s '''%(rec.id))
			
		return True
		
	#~ def _check_no_of_days(self, cr, uid, ids, context=None):
		#~ entry = self.browse(cr,uid,ids[0])
		#~ if entry.no_of_days <= 0:
			#~ return False
		#~ return True
	
	_constraints = [		
		
		#~ (_check_no_of_days, 'System not allow to save with zero value !!',['No Of Days']),
		(_duplicate_removed, 'Duplcates removed !',['']),
	   ]
	
	def onchange_load_bom(self, cr, uid, ids, load_bom,pump_id,wo_line_id,purpose,moc_const_id,decision,replace_categ,defect_id,complaint_due_to):
		fou_vals=[]
		ms_vals=[]
		bot_vals=[]
		data_rec = ''
		print"pump_id",pump_id
		print"load_bom",load_bom
		if load_bom == True:
			if replace_categ == 'pump' or replace_categ == 'spare':
				if wo_line_id:
					print"wo_line_idwo_line_id",wo_line_id
					wo_obj = self.pool.get('ch.work.order.details').search(cr,uid,[('id','=',wo_line_id)])
					if wo_obj:
						data_rec = self.pool.get('ch.work.order.details').browse(cr, uid, wo_obj[0])
				else:
					bom_obj = self.pool.get('kg.bom').search(cr, uid, [('pump_model_id','=',pump_id)])
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
												'decision': decision,
												'defect_id': defect_id,
												'complaint_due_to': complaint_due_to,
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
											'decision': decision,
											'defect_id': defect_id,
											'complaint_due_to': complaint_due_to,
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
											'decision': decision,
											'defect_id': defect_id,
											'complaint_due_to': complaint_due_to,
											})
						print"bot_valsbot_vals",bot_vals

		return {'value': {'line_ids': fou_vals,'line_ids_a': ms_vals,'line_ids_b': bot_vals}}
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'pending':
			source = ''
			
			if entry.replace_categ == 'spare' and not entry.load_bom:
				raise osv.except_osv(_('Warning!'),
					_('Please enable Load Bom !'))	
						
			if entry.replace_categ and entry.purpose == 'spare' and entry.decision in ('attended','not_attended','replace','replace_free'):
				applicable = 'no'
				applicable_a = 'no'
				applicable_b = 'no'
				if entry.line_ids:
					fou_data = [x for x in entry.line_ids if x.is_applicable == True]
					if fou_data:
						applicable='yes'
					else:
						applicable='no'
				if entry.line_ids_a:
					ms_data = [x for x in entry.line_ids_a if x.is_applicable == True]
					if ms_data:
						applicable_a='yes'
					else:
						applicable_a='no'
				if entry.line_ids_b:
					bot_data = [x for x in entry.line_ids_b if x.is_applicable == True]
					if bot_data:
						applicable_b='yes'
					else:
						applicable_b='no'
				if applicable == 'no' and applicable_a == 'no' and applicable_b == 'no':
					raise osv.except_osv(_('Warning!'),
						_('System should not accept without BOM Details !'))
			mkt = ser = 0
			if entry.replace_categ == 'pump':
				if entry.decision in ('replace','replace_free'):
				
					mkt = ser = 0
					if entry.decision == 'replace' and entry.replace_categ == 'pump':
						decision = 'replace'
						self.enquiry_creation(cr,uid,entry,decision)
						mkt = 1
					elif entry.decision == 'replace_free' and entry.replace_categ == 'pump':
						decision = 'replace_free'
						self.enquiry_creation(cr,uid,entry,decision)
						ser = 1
					else:
						pass
					print"mktmkt",mkt
					print"serser",ser
				elif entry.decision in ('attended','not_attended'):
					#~ if entry.decision in ('attended','not_attended'):
						#~ self.site_visit_pending_creation(cr,uid,entry)
					self.pool.get('kg.site.visit.pending').write(cr,uid,entry.sv_pending_id.id,{'state':'pending'})
				elif entry.decision == 'completed':
					#~ if entry.decision in ('attended','not_attended'):
						#~ self.site_visit_pending_creation(cr,uid,entry)
					self.pool.get('kg.site.visit.pending').write(cr,uid,entry.sv_pending_id.id,{'state':'close'})
				else:
					pass	
			elif entry.replace_categ == 'spare':
				if mkt == 0:
					print"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaA"
					spr_mkt = [x.decision for x in entry.line_ids or entry.line_ids_a or entry.line_ids_b if x.decision == 'replace' and x.is_applicable == True]
					print"spr_mktspr_mkt",spr_mkt
					if spr_mkt:
						decision = 'replace'
						self.enquiry_creation(cr,uid,entry,decision)
				if ser == 0:
					print"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
					spr_ser = [x.decision for x in entry.line_ids or entry.line_ids_a or entry.line_ids_b if x.decision == 'replace_free' and x.is_applicable == True]
					print"spr_serspr_ser",spr_ser
					if spr_ser:
						decision = 'replace_free'
						self.enquiry_creation(cr,uid,entry,decision)
				
				spr_svp = [x.decision for x in entry.line_ids or entry.line_ids_a or entry.line_ids_b if x.decision in ('attended','not_attended') and x.is_applicable == True]
				print"spr_svp",spr_svp
				if spr_svp:
					#~ self.site_visit_pending_creation(cr,uid,entry)
					self.pool.get('kg.site.visit.pending').write(cr,uid,entry.sv_pending_id.id,{'state':'pending'})
				else:
					self.pool.get('kg.site.visit.pending').write(cr,uid,entry.sv_pending_id.id,{'state':'close'})	
			else:
				pass
				
			#~ # Service Inward Entry Creation
			limit = len_is_apl = 0	
			if entry.returnable == 'yes':
				if entry.replace_categ == 'pump':
					replace_categ = 'pump'
					service_inward_id = self.pool.get('kg.service.inward').create(cr,uid,{'customer_id': entry.customer_id.id,
																				  'complaint_no': entry.complaint_no.id,
																				  'complaint_date': entry.registration_date,
																				  's_no': entry.s_no,
																				  'wo_no': entry.wo_no,
																				  'wo_line_id': entry.wo_line_id.id,
																				  'pump_id': entry.pump_id.id,
																				  'moc_const_id': entry.moc_const_id.id,
																				  'defect_id': entry.defect_id.id,
																				  'purpose_categ': replace_categ,
																				  'entry_mode': 'auto',
																					})
				elif entry.replace_categ == 'spare':
					replace_categ = 'part'
					for item in entry.line_ids:
						if item.is_applicable == True:
							for ele in range(item.qty):
								service_inward_id = self.pool.get('kg.service.inward').create(cr,uid,{'customer_id': entry.customer_id.id,
																				  'complaint_no': entry.complaint_no.id,
																				  'complaint_date': entry.registration_date,
																				  's_no': entry.s_no,
																				  'wo_no': entry.wo_no,
																				  'wo_line_id': entry.wo_line_id.id,
																				  'pump_id': entry.pump_id.id,
																				  'moc_const_id': entry.moc_const_id.id,
																				  'defect_id': entry.defect_id.id,
																				  'purpose_categ': replace_categ,
																				  'entry_mode': 'auto',
																				  'item_code': item.pattern_id.name,
																				  'item_name': item.pattern_name,
																					})
							
					for item in entry.line_ids_a:
						if item.is_applicable == True:
							for ele in range(item.qty):
								service_inward_id = self.pool.get('kg.service.inward').create(cr,uid,{'customer_id': entry.customer_id.id,
																				  'complaint_no': entry.complaint_no.id,
																				  'complaint_date': entry.registration_date,
																				  's_no': entry.s_no,
																				  'wo_no': entry.wo_no,
																				  'wo_line_id': entry.wo_line_id.id,
																				  'pump_id': entry.pump_id.id,
																				  'moc_const_id': entry.moc_const_id.id,
																				  'defect_id': entry.defect_id.id,
																				  'purpose_categ': replace_categ,
																				  'entry_mode': 'auto',
																				  'item_code': item.ms_id.name,
																				  'item_name': item.ms_id.code,
																					})
					for item in entry.line_ids_b:
						if item.is_applicable == True:
							for ele in range(item.qty):
								service_inward_id = self.pool.get('kg.service.inward').create(cr,uid,{'customer_id': entry.customer_id.id,
																				  'complaint_no': entry.complaint_no.id,
																				  'complaint_date': entry.registration_date,
																				  's_no': entry.s_no,
																				  'wo_no': entry.wo_no,
																				  'wo_line_id': entry.wo_line_id.id,
																				  'pump_id': entry.pump_id.id,
																				  'moc_const_id': entry.moc_const_id.id,
																				  'defect_id': entry.defect_id.id,
																				  'purpose_categ': replace_categ,
																				  'entry_mode': 'auto',
																				  'item_code': item.ms_id.name,
																				  'item_name': item.ms_id.code,
																					})
			
			#~ self.pool.get('kg.site.visit.pending').write(cr,uid,entry.sv_pending_id.id,{'state':'close'})
			
			
			ch_len = part_len = 0
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
			
			self.write(cr, uid, ids, {
										'state': 'close',
										'confirm_user_id': uid, 
										'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')
										})
										
		
		return True
	
	def site_visit_pending_creation(self,cr,uid,entry,context=None):
		ser_no = ''
		qc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.site.visit.pending')])
		seq_rec = self.pool.get('ir.sequence').browse(cr,uid,qc_seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s',now()::date) """%(qc_seq_id[0],seq_rec.code))
		ser_no = cr.fetchone();
		sv_pen_obj = self.pool.get('kg.site.visit.pending')
		svp_id = sv_pen_obj.create(cr,uid,{'name': ser_no[0],
										   'complaint_no': entry.complaint_no.id,
										   'purpose': entry.purpose,
										   'registration_date': entry.complaint_no.complaint_date,
										   'customer_id': entry.customer_id.id,
										   's_no': entry.s_no,
										   'wo_no': entry.wo_no,
										   'wo_line_id': entry.wo_line_id.id,
										   'pump_id': entry.pump_id.id,
										   'moc_const_id': entry.moc_const_id.id,
										   'defect_id': entry.defect_id.id,
										   'complaint_due_to': entry.complaint_due_to,
										   'decision': 'site_visit',
										   #~ 'complaint_line_id': entry.id,
										   'remarks': entry.remarks,
											})
		print"svp_idsvp_idsvp_idsvp_id",svp_id
		if svp_id:
			if entry.replace_categ == 'pump':
				complaint_categ = 'pump'
			elif entry.replace_categ == 'spare':
				complaint_categ = 'parts'
			if entry.line_ids:
				for line in entry.line_ids:
					if line.decision in ('attended','not_attended') and line.is_applicable == True:
						self.pool.get('ch.site.pending.fou').create(cr,uid,{'header_id': svp_id,
																			'is_applicable': line.is_applicable,
																			'position_id': line.position_id.id,
																			'pattern_id': line.pattern_id.id,
																			'qty': line.qty,
																			'complaint_categ': complaint_categ,
																			'defect_id': line.defect_id.id,
																			'complaint_due_to': line.complaint_due_to,
																			'decision': 'site_visit',
																			'remark': line.remarks,
																			})
			if entry.line_ids_a:
				for line in entry.line_ids_a:
					if line.decision in ('attended','not_attended') and line.is_applicable == True:
						self.pool.get('ch.site.pending.ms').create(cr,uid,{'header_id': svp_id,
																		   'is_applicable': line.is_applicable,
																		   'ms_id': line.ms_id.id,
																		   'qty': line.qty,
																		   'complaint_categ': complaint_categ,
																		   'defect_id': line.defect_id.id,
																		   'complaint_due_to': line.complaint_due_to,
																		   'decision': 'site_visit',
																		   'remark': line.remarks,
																			})
			if entry.line_ids_b:
				for line in entry.line_ids_b:
					if line.decision in ('attended','not_attended') and line.is_applicable == True:
						self.pool.get('ch.site.pending.bot').create(cr,uid,{'header_id': svp_id,
																		   'is_applicable': line.is_applicable,
																		   'ms_id': line.ms_id.id,
																		   'qty': line.qty,
																		   'complaint_categ': complaint_categ,
																		   'defect_id': line.defect_id.id,
																		   'complaint_due_to': line.complaint_due_to,
																		   'decision': 'site_visit',
																		   'remark': line.remarks,
																			})
		
		return True
	
	def enquiry_creation(self,cr,uid,entry,decision,context=None):
		print"entryentry",entry
		print"decisiondecision",decision
		crm_obj = self.pool.get('kg.crm.enquiry')
		crm_line_obj = self.pool.get('ch.kg.crm.pumpmodel')
		crm_line_fou = self.pool.get('ch.kg.crm.foundry.item')
		crm_line_ms = self.pool.get('ch.kg.crm.machineshop.item')
		crm_line_bot = self.pool.get('ch.kg.crm.bot')
		
		if decision == 'replace':
			source = 'market'
		if decision == 'replace_free':
			source = 'service'
		print"source",source
		
		crm_id = crm_obj.create(cr,uid,{'customer_id': entry.customer_id.id,
									   'purpose': entry.replace_categ,
									   'source': source,
									   'entry_mode': 'auto',
									   'enquiry_no': entry.id,
									   'market_division': 'ip',
										})
		print"crm_idcrm_id",crm_id
		print"entry.line_ids",entry.line_ids
		if crm_id:
			enquiry_line_id = 0
			#~ for item in entry.line_ids:
			if entry.replace_categ == 'pump':
				if entry.decision == decision:
					print"aaaaaaaaaaAA"
					enquiry_line_id = crm_line_obj.create(cr,uid,{'header_id': crm_id,
																   'pump_id': entry.pump_id.id,
																   'moc_const_id': entry.moc_const_id.id,
																   'qty': 1,
																   'wo_line_id': entry.wo_line_id.id,
																   'pumpseries_id': entry.pump_id.series_id.id,
																   'load_bom': True,
																   'purpose_categ': entry.replace_categ,
																   'acces': 'no',
																   'wo_no': entry.wo_no,
																   'spare_pump_id': entry.pump_id.id,
																   's_no': entry.s_no,
																   'spare_moc_const_id': entry.moc_const_id.id,
																   'spare_pumpseries_id': entry.pump_id.series_id.id,
																   'spare_load_bom': True,
																	})
					print"enquiry_line_idenquiry_line_id",enquiry_line_id
			elif entry.replace_categ == 'spare':
				bom_mkt = [x.decision for x in entry.line_ids or entry.line_ids_a or entry.line_ids_b if x.decision == decision and x.is_applicable == True]
				print"bom_mktbom_mktbom_mkt",bom_mkt
				bom_ser = [x.decision for x in entry.line_ids or entry.line_ids_a or entry.line_ids_b if x.decision == decision and x.is_applicable == True]
				print"bom_serbom_erbom_ser",bom_ser
				
				if bom_mkt or bom_ser:
					enquiry_line_id = crm_line_obj.create(cr,uid,{'header_id': crm_id,
																   'pump_id': entry.pump_id.id,
																   'moc_const_id': entry.moc_const_id.id,
																   'qty': 1,
																   'wo_line_id': entry.wo_line_id.id,
																   'pumpseries_id': entry.pump_id.series_id.id,
																   'load_bom': True,
																   'purpose_categ': 'spare',
																   'acces': 'no',
																   'wo_no': entry.wo_no,
																   'spare_pump_id': entry.pump_id.id,
																   's_no': entry.s_no,
																   'spare_moc_const_id': entry.moc_const_id.id,
																   'spare_pumpseries_id': entry.pump_id.series_id.id,
																   'spare_load_bom': True,
																	})
				#~ if item.decision == decision:
			else:
				pass		
			if enquiry_line_id > 0:
				for ele in entry.line_ids:
					if ele.is_applicable == True and ele.decision == decision:
						line_fou_id = crm_line_fou.create(cr,uid,{'header_id': enquiry_line_id,
																  'is_applicable': ele.is_applicable,
																  'position_id': ele.position_id.id,
																  'pattern_id': ele.pattern_id.id,
																  'pattern_name': ele.pattern_name,
																  'qty': ele.qty,
																  
																	})
						print"line_fou_idline_fou_id",line_fou_id
				for ele in entry.line_ids_a:
					if ele.is_applicable == True and ele.decision == decision:
						line_fou_id = crm_line_ms.create(cr,uid,{'header_id': enquiry_line_id,
																  'is_applicable': ele.is_applicable,
																  'ms_id': ele.ms_id.id,
																  'qty': ele.qty,
																  
																	})
				for ele in entry.line_ids_b:
					if ele.is_applicable == True and ele.decision == decision:
						line_fou_id = crm_line_bot.create(cr,uid,{'header_id': enquiry_line_id,
																'is_applicable': ele.is_applicable,
																'ms_id': ele.ms_id.id,
																'qty': ele.qty,
															  
																})
						
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
	
	def _check_line_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute('''select id from ch_site_visit_plan_allowance where date = %s and description = %s and mode_of_travel = %s and id != %s and header_id = %s 
						''',[entry.date,entry.description,entry.mode_of_travel,entry.id,entry.header_id.id])
		duplicate_id = cr.fetchone()
		if duplicate_id:
			if duplicate_id[0] != None:
				return False
		return True 
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.id:
			today = date.today()
			today = str(today)
			today = datetime.strptime(today, '%Y-%m-%d')
			entry_date = rec.date
			entry_date = str(entry_date)
			entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
			if entry_date > today:
				return False
		return True
		
	_constraints = [
		
		(_check_line_duplicates, 'Duplicate allowance entry not aollowed', ['']),	   
		(_future_entry_date_check, 'System not allow to save with future date!',['Allowance Date']),
		
	]
	
ch_site_visit_plan_allowance()

class ch_site_visit_plan_expense(osv.osv):

	_name = "ch.site.visit.plan.expense"
	_description = "Ch Site Visit Plan Expense Details"
	
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
	
	def _check_line_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute('''select id from ch_site_visit_plan_allowance where date = %s and description = %s and mode_of_travel = %s and id != %s and header_id = %s 
						''',[entry.date,entry.description,entry.mode_of_travel,entry.id,entry.header_id.id])
		duplicate_id = cr.fetchone()
		if duplicate_id:
			if duplicate_id[0] != None:
				return False
		return True 
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.id:
			today = date.today()
			today = str(today)
			today = datetime.strptime(today, '%Y-%m-%d')
			entry_date = rec.date
			entry_date = str(entry_date)
			entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
			if entry_date > today:
				return False
		return True
		
	_constraints = [
		
		(_check_line_duplicates, 'Duplicate allowance entry not aollowed', ['']),	   
		(_future_entry_date_check, 'System not allow to save with future date!',['Expense Date']),
		
	]
	
ch_site_visit_plan_expense()


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
		'decision': fields.selection([('attended','Attended - Not Completed'),('not_attended','Not Attended'),('replace','Replacement(Cost)'),('replace_free','Replacement(Free)'),('completed','Completed')],'Decision'),
		'defect_id': fields.many2one('kg.defect.master','Defect Type',domain="[('is_full_pump','=',True)]"),
		'complaint_due_to': fields.selection([('sam','SAM'),('customer','Customer')],'Complaint Due To'),
		'returnable': fields.selection([('yes','Yes'),('no','No')],'Returnable'),
		
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
		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
		#'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'remarks':fields.text('Remarks'),   
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		'decision': fields.selection([('attended','Attended - Not Completed'),('not_attended','Not Attended'),('replace','Replacement(Cost)'),('replace_free','Replacement(Free)'),('completed','Completed')],'Decision'),
		'defect_id': fields.many2one('kg.defect.master','Defect Type',domain="[('is_full_pump','=',True)]"),
		'complaint_due_to': fields.selection([('sam','SAM'),('customer','Customer')],'Complaint Due To'),
		'returnable': fields.selection([('yes','Yes'),('no','No')],'Returnable'),
		
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
		'decision': fields.selection([('attended','Attended - Not Completed'),('not_attended','Not Attended'),('replace','Replacement(Cost)'),('replace_free','Replacement(Free)'),('completed','Completed')],'Decision'),
		'defect_id': fields.many2one('kg.defect.master','Defect Type',domain="[('is_full_pump','=',True)]"),
		'complaint_due_to': fields.selection([('sam','SAM'),('customer','Customer')],'Complaint Due To'),
		'returnable': fields.selection([('yes','Yes'),('no','No')],'Returnable'),
		
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
