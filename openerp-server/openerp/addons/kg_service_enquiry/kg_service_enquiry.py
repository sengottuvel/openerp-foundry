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
    ('pump','Pump'),('spare','Spare'),('pump_spare','Pump With Spare')
]

STATE_SELECTION = [
    ('draft','Draft'),('open','Open'),('in_progress','In Progress'),('close','Closed')
]

class kg_service_enquiry(osv.osv):

	_name = "kg.service.enquiry"
	_description = "Service Enquiry Entry"
	_order = "complaint_date desc"

	_columns = {
	
		### Header Details ####
		'name': fields.char('Complaint No', size=128,select=True,readonly=True, states={'draft':[('readonly',False)]}),
		'complaint_date': fields.date('Complaint Date',required=True,readonly=True, states={'draft':[('readonly',False)]}),
		'customer_id': fields.many2one('res.partner','Customer Name',domain=[('customer','=',True),('contact','=',False)],readonly=True, states={'draft':[('readonly',False)]}),
		'purpose': fields.selection(PURPOSE_SELECTION,'Category',required=True,readonly=True, states={'draft':[('readonly',False)]}),
		'state': fields.selection(STATE_SELECTION,'Status', readonly=True),
		'remarks': fields.text('Remarks',readonly=True, states={'draft':[('readonly',False)]}),
		
		'note': fields.char('Notes'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'line_ids': fields.one2many('ch.service.enquiry', 'header_id', "Complaint Details",readonly=True, states={'draft':[('readonly',False)]}),
		'line_ids_feedback': fields.one2many('ch.service.enquiry.feedback', 'header_id', "Complaint Feedback",readonly=True, states={'draft':[('readonly',False)],'open':[('readonly',False)],'in_progress':[('readonly',False)]}),
				
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_service_enquiry', context=c),
		'complaint_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date': time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',
		'active': True,
		
	}
	
	def _current_date(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		complaint_date = rec.complaint_date
		complaint_date = str(complaint_date)
		complaint_date = datetime.strptime(complaint_date, '%Y-%m-%d')
		if complaint_date == today:
			return True
		return False
	
	def _check_lineitems(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if not entry.line_ids:
			return False
		return True
		
	_constraints = [		
		
		#~ (_current_date, 'System not allow to save with past date. !!',['Complaint Date']),
		(_check_lineitems, 'System not allow to save with empty Complaint Details !!',['']),
		
	   ]
	   
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			if entry.line_ids:
				for item in entry.line_ids:
					if item.complaint_categ != 'pump':
						fou_sql = """ select count(id) from ch_service_enquiry_fou where header_id = %s and is_applicable = True """%(item.id)
						cr.execute(fou_sql)		
						fou_data = cr.dictfetchall()
						print"fou_datafou_data",fou_data
						ms_sql = """ select count(id) from ch_service_enquiry_ms where header_id = %s and is_applicable = True """%(item.id)
						cr.execute(ms_sql)		
						ms_data = cr.dictfetchall()
						print"ms_datams_data",ms_data
						bot_sql = """ select count(id) from ch_service_enquiry_bot where header_id = %s and is_applicable = True """%(item.id)
						cr.execute(bot_sql)		
						bot_data = cr.dictfetchall()
						print"bot_databot_data",bot_data
						if fou_data[0]['count'] or ms_data[0]['count'] or bot_data[0]['count']:
							pass
						else:
							raise osv.except_osv(_('Warning!'),
								_('%s Please select item is applicable'%(item.wo_line_id.order_no)))
			
			item_code = ''
			item_name = ''
			decision = ''
			cr_no = cr_no_free = count = 0
			
			if entry.line_ids:
				mkt = [x.decision for x in entry.line_ids if x.decision == 'replace' and x.complaint_categ == 'pump']
				print"mkt",mkt
				if mkt:
					decision = 'replace'
					self.enquiry_creation(cr,uid,entry,decision)
				
				ser = [x.decision for x in entry.line_ids if x.decision == 'replace_free' and x.complaint_categ == 'pump']
				print"ser",ser
				if ser:
					decision = 'replace_free'
					self.enquiry_creation(cr,uid,entry,decision)
				
				for item in entry.line_ids:
					if item.despatch_date:
						today = date.today()
						despatch_date = datetime.strptime(item.despatch_date , '%Y-%m-%d').date()
						if despatch_date > today:
							raise osv.except_osv(_('Warning!'),
								_('%s Despatch date sholud not be greater than current date !'%(item.pump_id.name)))
					if item.complaint_categ == 'parts' and not item.load_bom:
						raise osv.except_osv(_('Warning!'),
							_('Please %s spare enable Load Bom !'%(item.pump_id.name)))
					
					if not mkt:
						spr_mkt = [x.decision for x in item.line_ids_fou or item.line_ids_ms or item.line_ids_bot if x.decision == 'replace']
						print"spr_mktspr_mkt",spr_mkt
						if spr_mkt:
							if cr_no == 0:
								decision = 'replace'
								self.enquiry_creation(cr,uid,entry,decision)
								cr_no = cr_no + 1
					if not ser:
						spr_ser = [x.decision for x in item.line_ids_fou or item.line_ids_ms or item.line_ids_bot if x.decision == 'replace_free']
						print"spr_serspr_ser",spr_ser
						if spr_ser:
							if cr_no_free == 0:
								decision = 'replace_free'
								self.enquiry_creation(cr,uid,entry,decision)
								cr_no_free = cr_no_free + 1
					if item.complaint_categ == 'pump':
						if item.decision == 'site_visit':
							self.site_visit_pending_creation(cr,uid,entry,item)
					if item.complaint_categ == 'parts':
						spr_svp = [x.decision for x in item.line_ids_fou or item.line_ids_ms or item.line_ids_bot if x.decision == 'site_visit' and x.is_applicable == True]
						print"spr_svp",spr_svp
						if spr_svp:
							self.site_visit_pending_creation(cr,uid,entry,item)
						
			status = ''
			if entry.line_ids:
				line_data = [x for x in entry.line_ids if x.decision == 'site_visit']
				for item in entry.line_ids:
					bom_line_data = [x.decision for x in item.line_ids_fou or item.line_ids_ms or item.line_ids_bot if x.decision == 'site_visit']
				if line_data or bom_line_data:
					status = 'open'
				else:
					status = 'close'
			self.write(cr, uid, ids, {
										'state': status,
										'confirm_user_id': uid, 
										'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')
				
										})
														
		return True
	
	def site_visit_pending_creation(self,cr,uid,entry,item,context=None):
		ser_no = ''
		qc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.site.visit.pending')])
		seq_rec = self.pool.get('ir.sequence').browse(cr,uid,qc_seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s',now()::date) """%(qc_seq_id[0],seq_rec.code))
		ser_no = cr.fetchone();
		if item.complaint_categ == 'pump':
			purpose = 'pump'
		elif item.complaint_categ == 'parts':
			purpose = 'spare'
		elif item.complaint_categ == 'access':
			purpose = 'access'
		svp_id = self.pool.get('kg.site.visit.pending').create(cr,uid,{ 'name': ser_no[0],
																	   'complaint_no': entry.id,
																	   'purpose': purpose,
																	   'registration_date': entry.complaint_date,
																	   'customer_id': entry.customer_id.id,
																	   's_no': item.s_no,
																	   'wo_no': item.wo_no,
																	   'wo_line_id': item.wo_line_id.id,
																	   'pump_id': item.pump_id.id,
																	   'moc_const_id': item.moc_const_id.id,
																	   'defect_id': item.defect_id.id,
																	   'complaint_due_to': item.complaint_due_to,
																	   'decision': item.decision,
																	   'complaint_line_id': item.id,
																	   'remarks': entry.remarks,
																		})
		if svp_id:
			if item.line_ids_fou:
				for line in item.line_ids_fou:
					if line.decision == 'site_visit' and line.is_applicable == True:
						self.pool.get('ch.site.pending.fou').create(cr,uid,{'header_id': svp_id,
																			'is_applicable': line.is_applicable,
																			'position_id': line.position_id.id,
																			'pattern_id': line.pattern_id.id,
																			'qty': line.qty,
																			'complaint_categ': line.complaint_categ,
																			'defect_id': line.defect_id.id,
																			'complaint_due_to': line.complaint_due_to,
																			'decision': line.decision,
																			'remark': line.remark,
																			})
			if item.line_ids_ms:
				for line in item.line_ids_ms:
					if line.decision == 'site_visit' and line.is_applicable == True:
						self.pool.get('ch.site.pending.ms').create(cr,uid,{'header_id': svp_id,
																		   'is_applicable': line.is_applicable,
																		   'ms_id': line.ms_id.id,
																		   'qty': line.qty,
																		   'complaint_categ': line.complaint_categ,
																		   'defect_id': line.defect_id.id,
																		   'complaint_due_to': line.complaint_due_to,
																		   'decision': line.decision,
																		   'remark': line.remark,
																			})
			if item.line_ids_bot:
				for line in item.line_ids_bot:
					if line.decision == 'site_visit' and line.is_applicable == True:
						self.pool.get('ch.site.pending.bot').create(cr,uid,{'header_id': svp_id,
																		   'is_applicable': line.is_applicable,
																		   'bot_id': line.bot_id.id,
																		   'qty': line.qty,
																		   'complaint_categ': line.complaint_categ,
																		   'defect_id': line.defect_id.id,
																		   'complaint_due_to': line.complaint_due_to,
																		   'decision': line.decision,
																		   'remark': line.remark,
																			})
			
		return True
		
	def enquiry_creation(self,cr,uid,entry,decision,context=None):
		print"entryentry",entry
		print"decisiondecision",decision
		if decision == 'replace':
			source = 'market'
		if decision == 'replace_free':
			source = 'service'
		print"source",source
		
		crm_id = self.pool.get('kg.crm.enquiry').create(cr,uid,{'customer_id': entry.customer_id.id,
														   'purpose': entry.purpose,
														   'source': source,
														   'entry_mode': 'auto',
														   'enquiry_no': entry.id,
														   'market_division': 'ip',
															})
		print"crm_idcrm_id",crm_id
		print"entry.line_ids",entry.line_ids
		if crm_id:
			enquiry_line_id = 0
			for item in entry.line_ids:
				print"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaAA",decision
				print"item.decision",item.decision
				if item.complaint_categ == 'pump':
					if item.decision == decision:
						print"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaAA"
						enquiry_line_id = self.pool.get('ch.kg.crm.pumpmodel').create(cr,uid,{'header_id': crm_id,
																						   'pump_id': item.pump_id.id,
																						   'moc_const_id': item.moc_const_id.id,
																						   'qty': 1,
																						   'wo_line_id': item.wo_line_id.id,
																						   'pumpseries_id': item.pumpseries_id.id,
																						   'load_bom': True,
																						   'purpose_categ': item.complaint_categ,
																						   'acces': 'no',
																						   'wo_no': item.wo_no,
																						   'spare_pump_id': item.pump_id.id,
																						   's_no': item.s_no,
																						   'spare_moc_const_id': item.moc_const_id.id,
																						   'spare_pumpseries_id': item.pumpseries_id.id,
																						   'spare_load_bom': True,
																							})
						print"enquiry_line_idenquiry_line_id",enquiry_line_id
				elif item.complaint_categ == 'parts':
					bom_mkt = [x.decision for x in item.line_ids_fou or item.line_ids_ms or item.line_ids_bot if x.decision == decision]
					print"bom_mktbom_mktbom_mkt",bom_mkt
					bom_ser = [x.decision for x in item.line_ids_fou or item.line_ids_ms or item.line_ids_bot if x.decision == decision]
					print"bom_serbom_erbom_ser",bom_ser
					
					if bom_mkt or bom_ser:
						enquiry_line_id = self.pool.get('ch.kg.crm.pumpmodel').create(cr,uid,{'header_id': crm_id,
																						   'pump_id': item.pump_id.id,
																						   'moc_const_id': item.moc_const_id.id,
																						   'qty': 1,
																						   'wo_line_id': item.wo_line_id.id,
																						   'pumpseries_id': item.pumpseries_id.id,
																						   'load_bom': True,
																						   'purpose_categ': 'spare',
																						   'acces': 'no',
																						   'wo_no': item.wo_no,
																						   'spare_pump_id': item.pump_id.id,
																						   's_no': item.s_no,
																						   'spare_moc_const_id': item.moc_const_id.id,
																						   'spare_pumpseries_id': item.pumpseries_id.id,
																						   'spare_load_bom': True,
																							})
					#~ if item.decision == decision:
				else:
					pass		
				if enquiry_line_id > 0:
					for ele in item.line_ids_fou:
						if ele.is_applicable == True and ele.decision == decision:
							line_fou_id = self.pool.get('ch.kg.crm.foundry.item').create(cr,uid,{'header_id': enquiry_line_id,
																							  'is_applicable': ele.is_applicable,
																							  'position_id': ele.position_id.id,
																							  'pattern_id': ele.pattern_id.id,
																							  'pattern_name': ele.pattern_name,
																							  'qty': ele.qty,
																							  
																								})
							print"line_fou_idline_fou_id",line_fou_id
					for ele in item.line_ids_ms:
						if ele.is_applicable == True and ele.decision == decision:
							line_fou_id = self.pool.get('ch.kg.crm.machineshop.item').create(cr,uid,{'header_id': enquiry_line_id,
																							  'is_applicable': ele.is_applicable,
																							  'ms_id': ele.ms_id.id,
																							  'qty': ele.qty,
																							  
																								})
					for ele in item.line_ids_bot:
						if ele.is_applicable == True and ele.decision == decision:
							line_fou_id = self.pool.get('ch.kg.crm.bot').create(cr,uid,{'header_id': enquiry_line_id,
																						'is_applicable': ele.is_applicable,
																						'ms_id': ele.bot_id.id,
																						'qty': ele.qty,
																					  
																						})
																										
		return True
								
	def entry_update(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		
		if entry.line_ids:
			for item in entry.line_ids:
				if item.complaint_categ != 'pump':
					fou_sql = """ select count(id) from ch_service_enquiry_fou where header_id = %s and is_applicalbe = True """%(item.id)
					cr.execute(fou_sql)		
					fou_data = cr.dictfetchall()
					print"fou_datafou_data",fou_data
					ms_sql = """ select count(id) from ch_service_enquiry_ms where header_id = %s and is_applicalbe = True """%(item.id)
					cr.execute(ms_sql)		
					ms_data = cr.dictfetchall()
					print"ms_datams_data",ms_data
					bot_sql = """ select count(id) from ch_service_enquiry_bot where header_id = %s and is_applicalbe = True """%(item.id)
					cr.execute(bot_sql)		
					bot_data = cr.dictfetchall()
					print"bot_databot_data",bot_data
					if fou_data[0]['count'] or ms_data[0]['count'] or bot_data[0]['count']:
						pass
					else:
						raise osv.except_osv(_('Warning!'),
							_('%s Please select anyone applicable'%(item.wo_line_id.order_no)))
						
		if entry.line_ids_feedback:
			self.write(cr, uid, ids, {
									#~ 'state': 'in_progress',
									'approve_user_id': uid, 
									'approve_date': time.strftime('%Y-%m-%d %H:%M:%S')
								})
		else:
			raise osv.except_osv(_('Warning!'),
						_('You can not update without feedback entry !!'))
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
		return super(kg_service_enquiry, self).write(cr, uid, ids, vals, context)
	
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_code = str(rec.name)		
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
			
		url = 'http://192.168.1.7/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&Service_Complaint='+rec_code



		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
								
kg_service_enquiry()

class ch_service_enquiry(osv.osv):

	_name = "ch.service.enquiry"
	_description = "Ch Service Enquiry Details"
	
	_columns = {
	
		'header_id':fields.many2one('kg.service.enquiry', 'Enquiry', ondelete='cascade'),
		'enquiry_id':fields.many2one('kg.service.enquiry', 'Enquiry'),
		's_no': fields.char('Serial Number'),
		'wo_no': fields.char('Old WO No'),
		'wo_line_id': fields.many2one('ch.work.order.details','WO No',domain="[('order_category','=',purpose),('header_id.partner_id','=',parent.customer_id),('header_id.state','=','confirmed')]"),
		'load_bom': fields.boolean('Load BOM'),
		'market_division': fields.selection([('cp','CP'),('ip','IP')],'Marketing Division'),
		'ref_mode': fields.selection([('direct','Direct'),('dealer','Dealer')],'Reference Mode'),
		'dealer_id': fields.many2one('res.partner','Dealer Name',domain=[('dealer','=',True),('contact','=',False)]),
		'purpose': fields.selection(PURPOSE_SELECTION,'Purpose'),
		'complaint_categ': fields.selection([('pump','Pump'),('parts','Parts'),('access','Access')],'Complaint Category'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Model'),
		'pumpseries_id': fields.many2one('kg.pumpseries.master','Pump Series'),
		'moc_const_id': fields.many2one('kg.moc.construction','MOC Construction'),
		'despatch_date': fields.date('Despatch Date'),
		'defect_id': fields.many2one('kg.defect.master','Defect Type',domain="[('is_full_pump','=',True)]"),
		'complaint_due_to': fields.selection([('sam','SAM'),('customer','Customer')],'Complaint Due To'),
		'decision': fields.selection([('no_fault','No Fault'),('replace','Replacement(Cost)'),('replace_free','Replacement(Free)'),('site_visit','Site Visit')],'Decision'),
		'nature_of_complaint': fields.text('Complaint Remarks'),
		'line_ids_fou': fields.one2many('ch.service.enquiry.fou', 'header_id', "Complaint Details"),
		'line_ids_ms': fields.one2many('ch.service.enquiry.ms', 'header_id', "Complaint Details"),
		'line_ids_bot': fields.one2many('ch.service.enquiry.bot', 'header_id', "Complaint Details"),
		
	}
	
	_defaults = {

		'complaint_categ': 'pump',
		'load_bom': False,
	}
	
	def default_get(self, cr, uid, fields, context):
		print"contextcontext---------------",context
		if len(context) > 4:
			if context.get('complaint_categ'):
				if context['complaint_categ'] == 'spare':
					context['complaint_categ'] = 'parts'
				if context['complaint_categ'] == 'pump_spare':
					context['complaint_categ'] = ''
			else:
				raise osv.except_osv(_('Warning!'),
					_('Kindly select Purpose !!'))
		print"ccccccccccccccccccc",context
		return context
		
	def onchange_wo_no(self, cr, uid, ids, wo_no):
		value = {'wo_line_id':''}
		if wo_no:
			wo_obj = self.pool.get('ch.work.order.details').search(cr,uid,[('order_no','=',wo_no)])
			if wo_obj:
				wo_rec = self.pool.get('ch.work.order.details').browse(cr,uid,wo_obj[0])
				value = {'wo_line_id': wo_rec.id}
		return {'value': value}
		
	def onchange_wo(self, cr, uid, ids, wo_line_id):
		value = {'pump_id':'','pumpseries_id':'','moc_const_id':''}
		if wo_line_id:
			wo_line_rec = self.pool.get('ch.work.order.details').browse(cr,uid,wo_line_id)
			pump_id = wo_line_rec.pump_model_id.id
			if pump_id:
				pump_rec = self.pool.get('kg.pumpmodel.master').browse(cr,uid,pump_id)
				pumpseries_id = pump_rec.series_id.id
			value = {'pump_id': pump_id,'pumpseries_id':pumpseries_id,'moc_const_id':wo_line_rec.moc_construction_id.id}
		return {'value': value}
	
	def onchange_despatch_date(self, cr, uid, ids, despatch_date):
		if despatch_date:
			today = date.today()
			despatch_date = datetime.strptime(despatch_date , '%Y-%m-%d').date()
			if despatch_date > today:
				raise osv.except_osv(_('Warning!'),
					_('Despatch date sholud not be greater than current date !'))
		return True
	
	def onchange_load_bom(self, cr, uid, ids,pump_id,pumpseries_id,wo_line_id,moc_const_id,load_bom,complaint_categ,purpose,defect_id,complaint_due_to,decision):
		fou_vals=[]
		ms_vals=[]
		bot_vals=[]
		print"========================================",load_bom
		if load_bom == True:
			if wo_line_id:
				wo_line_rec = self.pool.get('ch.work.order.details').browse(cr, uid, wo_line_id)
				purpose = wo_line_rec.order_category
				pump_id = wo_line_rec.pump_model_id.id
				if pump_id:
					pump_rec = self.pool.get('kg.pumpmodel.master').browse(cr,uid,pump_id)
					pumpseries_id = pump_rec.series_id.id
				moc_const_id = wo_line_rec.moc_construction_id.id
				for item in wo_line_rec.line_ids:
					if item.flag_applicable == True:
						fou_vals.append({
										'position_id': item.position_id.id,
										'pattern_id': item.pattern_id.id,
										'pattern_name': item.pattern_name,
										'qty': item.qty,
										'complaint_categ': complaint_categ,
										'is_applicable': item.flag_applicable,
										'complaint_due_to': complaint_due_to,
										'defect_id': defect_id,
										'decision': decision,
										})
				for item in wo_line_rec.line_ids_a:
					if item.flag_applicable == True:
						ms_vals.append({
										'ms_name_id': item.name,
										'ms_id': item.ms_id.id,
										'qty': item.qty,
										'complaint_categ': complaint_categ,
										'is_applicable': item.flag_applicable,
										'complaint_due_to': complaint_due_to,
										'defect_id': defect_id,
										'decision': decision,
										})
				for item in wo_line_rec.line_ids_b:
					if item.flag_applicable == True:
						bot_vals.append({
										'bot_id': item.bot_id.id,
										'bot_name': item.item_name,
										'qty': item.qty,
										'complaint_categ': complaint_categ,
										'is_applicable': item.flag_applicable,
										'complaint_due_to': complaint_due_to,
										'defect_id': defect_id,
										'decision': decision,
										})
			elif pump_id:
				print"--------------------------------"
				purpose = purpose
				moc_const = ''
				bom_obj = self.pool.get('kg.bom').search(cr,uid,[('pump_model_id','=',pump_id)])
				if bom_obj:
					bom_rec = self.pool.get('kg.bom').browse(cr,uid,bom_obj[0])
					pump_rec = self.pool.get('kg.pumpmodel.master').browse(cr, uid, pump_id)
					pumpseries_id = pump_rec.series_id.id
					wo_line_rec = self.pool.get('kg.bom').browse(cr,uid,bom_obj[0])
					for item in wo_line_rec.line_ids:
						fou_vals.append({
										'position_id': item.position_id.id,
										'pattern_id': item.pattern_id.id,
										'pattern_name': item.pattern_name,
										'qty': item.qty,
										'complaint_categ': complaint_categ,
										'is_applicable': True,
										'complaint_due_to': complaint_due_to,
										'defect_id': defect_id,
										'decision': decision,
										})
					for item in wo_line_rec.line_ids_a:
						ms_vals.append({
										'ms_name_id': item.name,
										'ms_id': item.ms_id.id,
										'qty': item.qty,
										'complaint_categ': complaint_categ,
										'is_applicable': True,
										'complaint_due_to': complaint_due_to,
										'defect_id': defect_id,
										'decision': decision,
										})
					for item in wo_line_rec.line_ids_b:
						if wo_line_id:
							bot_name = item.item_name
						elif pump_id:
							bot_name = item.name
						bot_vals.append({
										'bot_id': item.bot_id.id,
										'bot_name': bot_name,
										'qty': item.qty,
										'complaint_categ': complaint_categ,
										'is_applicable': True,
										'complaint_due_to': complaint_due_to,
										'defect_id': defect_id,
										'decision': decision,
										})
		
		return {'value': {'line_ids_fou': fou_vals,'line_ids_ms': ms_vals,'line_ids_bot': bot_vals,'purpose':purpose,'pump_id':pump_id,'moc_const_id':moc_const_id,'pumpseries_id':pumpseries_id}}
	
	def _duplicate_removed(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.complaint_categ in ('pump','parts') and rec.load_bom != True:
			cr.execute(''' delete from ch_service_enquiry_fou where header_id = %s '''%(rec.id))
			cr.execute(''' delete from ch_service_enquiry_ms where header_id = %s '''%(rec.id))
			cr.execute(''' delete from ch_service_enquiry_bot where header_id = %s '''%(rec.id))
			
		return True
		
	_constraints = [		
		
		(_duplicate_removed, 'Duplcates removed !',['']),
		
	   ]
	   	
ch_service_enquiry()

class ch_service_enquiry_fou(osv.osv):

	_name = "ch.service.enquiry.fou"
	_description = "Ch Service Enquiry FOU Details"
	
	_columns = {
	
		'header_id':fields.many2one('ch.service.enquiry', 'Complaint Details', ondelete='cascade'),
		'enquiry_id':fields.many2one('kg.service.enquiry', 'Enquiry'),
		'is_applicable': fields.boolean('Applicable'),
		'position_id': fields.many2one('kg.position.number', 'Position No'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No',domain="[('active','=','t')]"),
		'pattern_name': fields.char('Pattern Name'),
		'qty': fields.integer('Qty'),
		'complaint_categ': fields.selection([('pump','Pump'),('parts','Parts'),('access','Access')],'Complaint Category'),
		'defect_id': fields.many2one('kg.defect.master','Defect Type'),
		'complaint_due_to': fields.selection([('sam','SAM'),('customer','Customer')],'Complaint Due To'),
		'decision': fields.selection([('no_fault','No Fault'),('replace','Replacement(Cost)'),('replace_free','Replacement(Free)'),('site_visit','Site Visit')],'Decision'),
		'remark': fields.text('Complaint Remarks'),
		
	}
	
ch_service_enquiry_fou()


class ch_service_enquiry_ms(osv.osv):

	_name = "ch.service.enquiry.ms"
	_description = "Ch Service Enquiry MS Details"
	
	_columns = {
	
		'header_id':fields.many2one('ch.service.enquiry', 'Complaint Details', ondelete='cascade'),
		'enquiry_id':fields.many2one('kg.service.enquiry', 'Enquiry'),
		'is_applicable': fields.boolean('Applicable'),
		#~ 'ms_name_id': fields.many2one('ch.order.machineshop.details', 'Item Name'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code',domain = [('type','=','ms')], ondelete='cascade'),
		'ms_name_id': fields.related('ms_id','name', type='char',size=128,string='Item Name', store=True),
		'qty': fields.integer('Qty'),
		'complaint_categ': fields.selection([('pump','Pump'),('parts','Parts'),('access','Access')],'Complaint Category'),
		'defect_id': fields.many2one('kg.defect.master','Defect Type'),
		'complaint_due_to': fields.selection([('sam','SAM'),('customer','Customer')],'Complaint Due To'),
		'decision': fields.selection([('no_fault','No Fault'),('replace','Replacement(Cost)'),('replace_free','Replacement(Free)'),('site_visit','Site Visit')],'Decision'),
		'remark': fields.text('Complaint Remarks'),
				
	}
	
ch_service_enquiry_ms()


class ch_service_enquiry_bot(osv.osv):

	_name = "ch.service.enquiry.bot"
	_description = "Ch Service Enquiry BOT Details"
	
	_columns = {
	
		'header_id':fields.many2one('ch.service.enquiry', 'Complaint Details', ondelete='cascade'),
		'enquiry_id':fields.many2one('kg.service.enquiry', 'Enquiry'),
		'is_applicable': fields.boolean('Applicable'),
		'bot_id':fields.many2one('kg.machine.shop', 'Item Code',domain = [('type','=','bot')], ondelete='cascade'),
		'bot_name': fields.related('bot_id','name', type='char', size=128, string='Item Name', store=True),
		'qty': fields.integer('Qty'),
		'complaint_categ': fields.selection([('pump','Pump'),('parts','Parts'),('access','Access')],'Complaint Category'),
		'defect_id': fields.many2one('kg.defect.master','Defect Type'),
		'complaint_due_to': fields.selection([('sam','SAM'),('customer','Customer')],'Complaint Due To'),
		'decision': fields.selection([('no_fault','No Fault'),('replace','Replacement(Cost)'),('replace_free','Replacement(Free)'),('site_visit','Site Visit')],'Decision'),
		'remark': fields.text('Complaint Remarks'),
		
	}

ch_service_enquiry_bot()


class ch_service_enquiry_feedback(osv.osv):

	_name = "ch.service.enquiry.feedback"
	_description = "Ch Service Enquiry Feedback Details"
	
	_columns = {
	
		'header_id':fields.many2one('kg.service.enquiry', 'Enquiry', ondelete='cascade'),
		'enquiry_id':fields.many2one('kg.service.enquiry', 'Enquiry'),
		'crt_date': fields.date('Creation Date'),
		'reminder_date': fields.date('Reminder Date'),
		'feedback': fields.text('Feedback'),
		
	}
	
	_defaults = {
		
		'crt_date': lambda * a: time.strftime('%Y-%m-%d'),
		
	}
	
	def _current_date(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		crt_date = rec.crt_date
		crt_date = str(crt_date)
		crt_date = datetime.strptime(crt_date, '%Y-%m-%d')
		if crt_date == today:
			return True
		return False
	
	def _reminder_date(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		rmd_date = rec.reminder_date
		rmd_date = str(rmd_date)
		rmd_date = datetime.strptime(rmd_date, '%Y-%m-%d')
		if rmd_date > today:
			return True
		return False
	
	_constraints = [		
		
		(_current_date, 'System not allow to save with past date. !!',['Creation Date']),
		(_reminder_date, 'Should be greater than current date !!',['Reminder Date']),
		
	   ]
	   	
ch_service_enquiry_feedback()
