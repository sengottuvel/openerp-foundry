from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import base64


CALL_TYPE_SELECTION = [
    ('service','Service'),
    ('new_enquiry','New Enquiry')
]
PURPOSE_SELECTION = [
    ('pump','Pump'),('spare','Spare'),('prj','Project'),('pump_spare','Pump and Spare'),('access','Only Accessories')
]
STATE_SELECTION = [
    ('draft','Draft'),('moved_to_offer','Moved To Offer'),('call','Call Back'),('quote','Quote Process'),('wo_created','WO Created'),('wo_released','WO Released'),('reject','Rejected'),('revised','Revised')
]
MARKET_SELECTION = [
	('cp','CP'),('ip','IP')
]

class kg_crm_enquiry(osv.osv):

	_name = "kg.crm.enquiry"
	_description = "CRM Enquiry Entry"
	_order = "enquiry_date desc"

	_columns = {
	
		### Header Details ####
		'name': fields.char('Enquiry No.', size=128,select=True),
		'schedule_no': fields.char('Schedule No', size=128,select=True),
		'enquiry_date': fields.date('Customer Enquiry Date',required=True,readonly=True, states={'draft':[('readonly',False)]}),
		'offer_date': fields.date('Enquiry Date',required=True,readonly=True, states={'draft':[('readonly',False)]}),
		'note': fields.char('Notes',readonly=True, states={'draft':[('readonly',False)]}),
		'service_det': fields.char('Service Details'),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'revision_remarks': fields.text('Revision Remarks'),
		'state': fields.selection(STATE_SELECTION,'Status', readonly=True),
		'line_ids': fields.one2many('ch.kg.crm.enquiry', 'header_id', "Child Enquiry"),
		'ch_line_ids': fields.one2many('ch.kg.crm.pumpmodel', 'header_id', "Pump/Spare Details",readonly=True, states={'draft':[('readonly',False)]}),
		'due_date': fields.date('Due Date',readonly=True, states={'draft':[('readonly',False)]}),
		'call_type': fields.selection(CALL_TYPE_SELECTION,'Call Type', required=True),
		'ref_mode': fields.selection([('direct','Direct'),('dealer','Dealer')],'Reference Mode', required=True,readonly=True, states={'draft':[('readonly',False)]}),
		'market_division': fields.selection(MARKET_SELECTION,'Marketing Division',readonly=True, states={'draft':[('readonly',False)]}),
		'ref_no': fields.char('Reference Number'),
		'segment': fields.selection([('dom','Domestic'),('exp','Export')],'Segment',readonly=True, states={'draft':[('readonly',False)]}),
		'customer_id': fields.many2one('res.partner','Customer Name',domain=[('customer','=',True),('contact','=',False)],readonly=True, states={'draft':[('readonly',False)]}),
		'dealer_id': fields.many2one('res.partner','Dealer Name',domain=[('dealer','=',True),('contact','=',False)]),
		'industry_id': fields.many2one('kg.industry.master','Sector',readonly=True, states={'draft':[('readonly',False)]}),
		'expected_value': fields.float('Expected Value',readonly=True, states={'draft':[('readonly',False)]}),
		'del_date': fields.date('Expected Delivery Date',readonly=True, states={'draft':[('readonly',False)]}),
		'purpose': fields.selection(PURPOSE_SELECTION,'Purpose',readonly=True, states={'draft':[('readonly',False)]}),
		'capacity': fields.float('Capacity'),
		'head': fields.float('Head'),
		'chemical_id': fields.many2one('kg.chemical.master','Chemical',domain=[('purpose','=','general')]),
		'pump_list': fields.text('Pump List'),
		'gravity': fields.float('Gravity'),
		'spl_gravity': fields.float('Special Gravity'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Name'),
		's_no': fields.char('Serial Number'),
		'wo_no': fields.char('WO Number'),
		'requirements': fields.text('Requirements'),
		'source': fields.selection([('service','Service'),('market','Marketing')],'Source'),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		'revision': fields.integer('Revision'),
		'wo_flag': fields.boolean('WO Flag'),
		
		'enquiry_no': fields.char('Customer Enquiry No.', size=128,select=True,readonly=True, states={'draft':[('readonly',False)]}),
		'scope_of_supply': fields.selection([('bare_pump','Bare Pump'),('pump_with_acces','Pump With Accessories'),('pump_with_acces_motor','Pump With Accessories And Motor')],'Scope of Supply'),
		'pump': fields.selection([('gld_packing','Gland Packing'),('mc_seal','M/C Seal'),('dynamic_seal','Dynamic seal')],'Shaft Sealing', required=True),
		'drive': fields.selection([('motor','Motor'),('vfd','VFD'),('engine','Engine')],'Drive'),
		'transmision': fields.selection([('cpl','Coupling'),('belt','Belt Drive'),('fc','Fluid Coupling'),('gear_box','Gear Box'),('fc_gear_box','Fluid Coupling With Gear Box')],'Transmision', required=True),
		'acces': fields.selection([('yes','Yes'),('no','No')],'Accessories'),
		
		### Entry Info ####
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'crt_date': fields.datetime('Created Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),	   
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_crm_enquiry', context=c),
		'enquiry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'offer_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date': time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',
		'pump': 'gld_packing',
		'transmision': 'cpl',
		'ref_mode': 'direct',
		'call_type': 'new_enquiry',
		'active': True,
		'entry_mode': 'manual',
		'revision': 0,
		'wo_flag': False,
		#~ 'division_id':_get_default_division,
		#~ 'due_date' : lambda * a: time.strftime('%Y-%m-%d'),
		
	}
	
	def onchange_due_date(self,cr,uid,ids,due_date,context=None):
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		due_date = str(due_date)
		due_date = datetime.strptime(due_date, '%Y-%m-%d')
		if due_date > today:
			return False
		else:
			raise osv.except_osv(_('Warning!'),
						_('System should allow only past date !!'))
						
	def onchange_del_date(self,cr,uid,ids,del_date,context=None):
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		del_date = str(del_date)
		del_date = datetime.strptime(del_date, '%Y-%m-%d')
		if del_date >= today:
			return False
		else:
			raise osv.except_osv(_('Warning!'),
						_('System not allow to save with past date !!'))
		
	def _future_enquiry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.entry_mode == 'manual':
			today = date.today()
			today = str(today)
			today = datetime.strptime(today, '%Y-%m-%d')
			enquiry_date = rec.enquiry_date
			enquiry_date = str(enquiry_date)
			enquiry_date = datetime.strptime(enquiry_date, '%Y-%m-%d')
			if enquiry_date > today:
				return False
		return True
		
	def _future_due_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.entry_mode == 'manual':
			today = date.today()
			today = str(today)
			today = datetime.strptime(today, '%Y-%m-%d')
			due_date = rec.due_date
			due_date = str(due_date)
			due_date = datetime.strptime(due_date, '%Y-%m-%d')
			if due_date <= today:
				return False
		return True
		
	def _future_del_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.entry_mode == 'manual':
			today = date.today()
			today = str(today)
			today = datetime.strptime(today, '%Y-%m-%d')
			del_date = rec.del_date
			del_date = str(del_date)
			del_date = datetime.strptime(del_date, '%Y-%m-%d')
			if del_date < today:
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
		
	def _check_is_applicable(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.entry_mode == 'manual':
			if entry.ch_line_ids:
				for rec in entry.ch_line_ids:
					applicable = 'no'
					applicable_a = 'no'
					applicable_b = 'no'
					if rec.purpose_categ == 'spare' or rec.purpose_categ == 'pump':
						if rec.line_ids:
							fou_data = [x for x in rec.line_ids if x.is_applicable == True]
							print"fou_datafou_datafou_data------------",
							if fou_data:
								applicable='yes'
							else:
								applicable='no'
						if rec.line_ids_a:
							ms_data = [x for x in rec.line_ids_a if x.is_applicable == True]
							if ms_data:
								applicable_a='yes'
							else:
								applicable_a='no'
						if rec.line_ids_b:
							bot_data = [x for x in rec.line_ids_b if x.is_applicable == True]
							if bot_data:
								applicable_b='yes'
							else:
								applicable_b='no'
						print"rec.spare_pump_id.namerec.spare_pump_id.name",rec.spare_pump_id.name
						print"rec.pump_id.namerec.pump_id.name",rec.pump_id.name
						print"applicableapplicable",applicable		
						print"applicableapplicable",applicable_a		
						print"applicableapplicable",applicable_b	
						if applicable == 'no' and applicable_a == 'no' and applicable_b == 'no':
							if rec.purpose_categ == 'spare':
								raise osv.except_osv(
									_('Warning!'),
									_('Spare %s You cannot save without Component'%(rec.spare_pump_id.name)))
							elif rec.purpose_categ == 'pump':
								raise osv.except_osv(
									_('Warning!'),
									_('Pump %s You cannot save without Component'%(rec.pump_id.name)))
		return True
		
	def _check_lineitems(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.entry_mode == 'manual':
			if not entry.ch_line_ids:
				return False
		return True
		
	def _Validation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		special_char = ''.join( c for c in flds.name if  c in '!@#$%^~*{}?+=' )
		if special_char:
			return False
		return True
		
	def _check_name(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(""" select name from kg_crm_enquiry where name  = '%s' """ %(entry.name))
		data = cr.dictfetchall()
			
		if len(data) > 1:
			res = False
		else:
			res = True	
		return res 
	
	_constraints = [		
		
		(_future_enquiry_date_check, 'System not allow to save with past date!',['Enquiry Date']),
		(_future_due_date_check, 'Should be greater than current date!',['Due Date']),
		(_future_del_date_check, 'System not allow to save with past date!',['Expected Del Date']),
		(_check_lineitems, 'System not allow to save with empty Pump/Spare Details!',['']),
		(_check_is_applicable, 'Kindly select anyone is applicable!',['']),
		#(_check_duplicates, 'System not allow to do duplicate entry !!',['']),
		#(_Validation, 'Special Character Not Allowed in Work Order No.', ['']),
		#(_check_name, 'Work Order No. must be Unique', ['']),
		
	   ]
	   
	"""   
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
	  """
	
	def entry_revision(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'moved_to_offer':
			if not entry.revision_remarks:
				raise osv.except_osv(_('Warning!'),
					_('System should not accept without revision remarks'))
			revision = 0
			if entry.wo_flag == False:
				del_sql = """ delete from kg_crm_offer where enquiry_id = %s """ %(entry.id)
				cr.execute(del_sql)
				revision = entry.revision + 1
				print"revisionrevisionrevision",revision
				vals = {
						'state' : 'draft',
						'revision' : revision,
						}
				enquiry_id = self.copy(cr, uid, entry.id,vals, context) 
				print"enquiry_idenquiry_id",enquiry_id
				#~ offer_id = self.create(cr,uid,{'name': entry.name,
									#~ 'enquiry_no': entry.enquiry_no,
									#~ 'offer_date': entry.offer_date,
									#~ 'enquiry_date': entry.enquiry_date,
									#~ 'customer_id': entry.customer_id.id,
									#~ 'segment': entry.segment,
									#~ 'ref_mode': entry.ref_mode,
									#~ 'location': entry.location,
									#~ 'market_division': entry.market_division,
									#~ 'state': 'draft',
									#~ 'revision': revision,
									#~ 'note': entry.note,
									#~ 'purpose': entry.purpose,
									#~ 'wo_flag': entry.wo_flag,
									#~ 'offer_net_amount': entry.offer_net_amount,
									#~ })
						
				self.write(cr, uid, ids, {
										  'state': 'revised',
										})
								
		return True
		
	def list_details(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		obj = self.search(cr,uid,[('id','!=',rec.id),('customer_id','=',rec.customer_id.id)])
		if obj:
			cr.execute(''' delete from ch_kg_crm_enquiry where header_id = %s '''%(rec.id))
			for item in obj:
				obj_rec = self.browse(cr,uid,item)
				child_id = self.pool.get('ch.kg.crm.enquiry').create(cr,uid,{'header_id':rec.id,'enquiry_id':item})
		else:
			pass
		return True
		
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_number = str(rec.enquiry_no)
		#~ url = 'http://iasqa1.kgisl.com/?uname='+rec_user+'&s='+rec_work_order
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
		
		url = 'http://192.168.1.7/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&wo_no='+rec_number
		
		#url = 'http://192.168.1.150:81/pbxclick2call.php?exten='+exe_no+'&phone='+str(m_no)
		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			if not entry.name:
				if entry.call_type == 'service':		
					off_no = ''	
					qc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.crm.enquiry')])
					rec = self.pool.get('ir.sequence').browse(cr,uid,qc_seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s','%s') """%(qc_seq_id[0],rec.code,entry.enquiry_date))
					off_no = cr.fetchone();
					off_no = off_no[0]
				elif entry.call_type == 'new_enquiry':
					if entry.market_division == 'cp':				
						off_no = ''	
						qc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','crm.enquiry.cp')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,qc_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(qc_seq_id[0],rec.code,entry.enquiry_date))
						off_no = cr.fetchone();
						off_no = off_no[0]
					elif entry.market_division == 'ip':				
						off_no = ''	
						qc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','crm.enquiry.ip')])
						rec = self.pool.get('ir.sequence').browse(cr,uid,qc_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s','%s') """%(qc_seq_id[0],rec.code,entry.enquiry_date))
						off_no = cr.fetchone();
						off_no = off_no[0]
					else:
						pass
				else:
					pass
			elif entry.name:
				off_no = entry.name
			
			offer_id = self.pool.get('kg.crm.offer').create(cr,uid,{
																	'enquiry_id': entry.id,
																	'enquiry_no': off_no,
																	'enquiry_date': entry.offer_date,
																	'customer_id': entry.customer_id.id,
																	'ref_mode': entry.ref_mode,
																	'market_division': entry.market_division,
																	'purpose': entry.purpose,
																	'segment': entry.segment,
																	})
			print"offer_idoffer_idoffer_idoffer_id",offer_id
			print"entry.line_idsentry.line_idsentry.line_ids",entry.ch_line_ids
			if entry.ch_line_ids:
				print"entryssssssssssssssssssss",entry
				for item in entry.ch_line_ids:
					print"iiiiiiiiiiiiiiiiiiiiii",item
					if item.purpose_categ == 'pump':
						catg='non_acc'
						bom = ''
						purpose_categ = 'pump'
						primecost_vals = per_pump_prime_cost = 0.00
						primecost_vals = self._prepare_primecost(cr,uid,item,catg,bom,purpose_categ,offer_id)
						print"primecost_valsprimecost_vals",primecost_vals
						if primecost_vals != 0 and item.qty != 0:
							per_pump_prime_cost = primecost_vals / item.qty
						else:
							per_pump_prime_cost = 0
						pump_id = self.pool.get('ch.pump.offer').create(cr,uid,{
																		'header_id': offer_id,
																		'pumpseries_id': item.pumpseries_id.id,
																		'pump_id': item.pump_id.id,
																		'qty': item.qty,
																		'moc_const_id': item.moc_const_id.id,
																		'per_pump_prime_cost': per_pump_prime_cost,
																		'prime_cost': primecost_vals,
																		'enquiry_line_id': item.id,
																		})
						print"pump_idpump_idpump_id",pump_id
					if item.purpose_categ == 'spare':
						catg='non_acc'
						if item.line_ids:
							#~ for item_1 in item.line_ids:
							primecost_vals = 0.00
							#~ if item_1.is_applicable == True:
							bom = 'fou'
							purpose_categ = 'spare'
							primecost_vals = self._prepare_primecost(cr,uid,item,catg,bom,purpose_categ,offer_id)
							#~ print"spare_primecost_vals",primecost_vals
							
							#~ spare_id = self.pool.get('ch.spare.offer').create(cr,uid,{
																			#~ 'header_id': offer_id,
																			#~ 'pumpseries_id': item.spare_pumpseries_id.id,
																			#~ 'pump_id': item.spare_pump_id.id,
																			#~ 'moc_const_id': item.spare_moc_const_id.id,
																			#~ 'prime_cost': primecost_vals,
																			#~ 'enquiry_line_id': item.id,
																			#~ 'item_code': item_1.pattern_id.name,
																			#~ 'item_name': item_1.pattern_id.pattern_name,
																			#~ 'pattern_id': item_1.pattern_id.id,
																			#~ 'moc_id': item_1.moc_id.id,
																			#~ 'qty': item_1.qty,
																			#~ })
									
								
						if item.line_ids_a:
							#~ for item_1 in item.line_ids_a:
							primecost_vals = 0.00
							#~ if item_1.is_applicable == True:
							bom = 'ms'
							purpose_categ = 'spare'
							#~ spare_id = self.pool.get('ch.spare.offer').create(cr,uid,{
																			#~ 'header_id': offer_id,
																			#~ 'pumpseries_id': item.spare_pumpseries_id.id,
																			#~ 'pump_id': item.spare_pump_id.id,
																			#~ 'moc_const_id': item.spare_moc_const_id.id,
																			#~ 'prime_cost': primecost_vals,
																			#~ 'enquiry_line_id': item.id,
																			#~ 'item_code': item_1.ms_id.code,
																			#~ 'item_name': item_1.ms_id.name,
																			#~ 'ms_id': item_1.ms_id.id,
																			#~ 'moc_id': item_1.moc_id.id,
																			#~ 'qty': item_1.qty,
																			#~ })
							primecost_vals = self._prepare_primecost(cr,uid,item,catg,bom,purpose_categ,offer_id)
						if item.line_ids_b:
							#~ for item_1 in item.line_ids_b:
							primecost_vals = 0.00
							#~ if item_1.is_applicable == True:
							bom = 'bot'
							purpose_categ = 'spare'
							#~ spare_id = self.pool.get('ch.spare.offer').create(cr,uid,{
																			#~ 'header_id': offer_id,
																			#~ 'pumpseries_id': item.spare_pumpseries_id.id,
																			#~ 'pump_id': item.spare_pump_id.id,
																			#~ 'moc_const_id': item.spare_moc_const_id.id,
																			#~ 'prime_cost': item_1.prime_cost,
																			#~ 'enquiry_line_id': item.id,
																			#~ 'item_code': item_1.ms_id.code,
																			#~ 'item_name': item_1.ms_id.name,
																			#~ 'bot_id': item_1.ms_id.id,
																			#~ 'moc_id': item_1.moc_id.id,
																			#~ 'qty': item_1.qty,
																			#~ })
							primecost_vals = self._prepare_primecost(cr,uid,item,catg,bom,purpose_categ,offer_id)
					if item.acces == 'yes':
						ite = item
						pump_id = ''
						if item.purpose_categ == 'pump':
							pump_id = item.pump_id.id
							purpose_categ = 'pump'
						elif item.purpose_categ == 'spare' or item.purpose_categ == 'access':
							pump_id = item.spare_pump_id.id
							purpose_categ = 'spare'
						if item.line_ids_access_a:
							for item_1 in item.line_ids_access_a:
								item = item_1
								per_access_prime_cost = 0.00
								catg='acc'
								bom = ''
								primecost_vals = self._prepare_primecost(cr,uid,item,catg,bom,purpose_categ,offer_id)
								print"primecost_valsprimecost_vals====access=======",primecost_vals
								if primecost_vals != 0 and item.qty != 0:
									per_access_prime_cost = primecost_vals / item.qty
								else:
									per_access_prime_cost = 0
								self.pool.get('ch.kg.crm.accessories').write(cr,uid,item_1.id,{'prime_cost':primecost_vals})
								access_id = self.pool.get('ch.accessories.offer').create(cr,uid,{
																			'header_id': offer_id,
																			'access_id': item_1.access_id.id,
																			'pump_id': pump_id,
																			'moc_id': item_1.moc_id.id,
																			'qty': item_1.qty,
																			'prime_cost': primecost_vals,
																			'per_access_prime_cost': per_access_prime_cost,
																			'enquiry_line_access_id': item_1.id,
																			'enquiry_line_id': ite.id,
																			})
				
			self.write(cr, uid, ids, {
										#'name':self.pool.get('ir.sequence').get(cr, uid, 'kg.crm.enquiry'),
										'name':off_no,
										'state': 'moved_to_offer',
										'confirm_user_id': uid, 
										'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')
									})
		return True
	
	def _prepare_primecost(self,cr,uid,item,catg,bom,purpose_categ,offer_id,context=None):
		
		#~ for item in entry.ch_line_ids:
		
		design_rate = 0.00
		moc_rate = 0.00
		brandmoc_rate = 0.00
		h_brandmoc_rate = 0.00
		pat_amt = 0.00
		prime_cost = 0.00
		prime_cost_1 = 0.00
		qty = 0.00
		price = 0.00
		ms_price = 0.00
		tot_price = 0.00
		bot_price = 0.00
		
		price_1 = 0.00
		price_2 = 0.00
		if catg == 'non_acc':
			#~ if item.purpose_categ == 'pump':
				#~ bom_line_id = item.line_ids
				#~ bom_ms_line_id = item.line_ids_a
				#~ bom_bot_line_id = item.line_ids_b
			#~ elif item.purpose_categ == 'spare':
			bom_line_ids = item.line_ids
			bom_ms_line_ids = item.line_ids_a
			bom_bot_line_ids = item.line_ids_b
			bom_line_id = []
			bom_ms_line_id = []
			bom_bot_line_id = []
			for bm_line in bom_line_ids:
				if bm_line.is_applicable == True:
					if bom == 'prime':
						bom_line_rec = self.pool.get('ch.primecost.view.fou').browse(cr,uid,bm_line.id)
					else:
						bom_line_rec = self.pool.get('ch.kg.crm.foundry.item').browse(cr,uid,bm_line.id)
					bom_line_id.append(bom_line_rec)
			for ms_line in bom_ms_line_ids:
				if ms_line.is_applicable == True:
					if bom == 'prime':
						ms_line_rec = self.pool.get('ch.primecost.view.ms').browse(cr,uid,ms_line.id)
					else:
						ms_line_rec = self.pool.get('ch.kg.crm.machineshop.item').browse(cr,uid,ms_line.id)
					bom_ms_line_id.append(ms_line_rec)
			for bt_line in bom_bot_line_ids:
				if bt_line.is_applicable == True:
					if bom == 'prime':
						bot_line_rec = self.pool.get('ch.primecost.view.bot').browse(cr,uid,bt_line.id)
					else:
						bot_line_rec = self.pool.get('ch.kg.crm.bot').browse(cr,uid,bt_line.id)
					bom_bot_line_id.append(bot_line_rec)
		elif catg == 'acc':
			bom_line_id = item.line_ids
			bom_ms_line_id = item.line_ids_a
			bom_bot_line_id = item.line_ids_b
			
		# FOU Item
		
		for fou_line in bom_line_id:
			if fou_line.is_applicable == True:
				
				design_rate = qty = moc_id = 0
				pattern_rec = self.pool.get('kg.pattern.master').browse(cr,uid,fou_line.pattern_id.id)
				if not fou_line.moc_id:
					pattern_line_id = pattern_rec.line_ids
					if pattern_line_id:
						if catg == 'non_acc':
							if bom == 'prime':
								item_moc_const_id = item.moc_const_id.id
							else:
								if item.purpose_categ == 'pump':
									item_moc_const_id = item.moc_const_id.id
								elif item.purpose_categ == 'spare':
									item_moc_const_id = item.spare_moc_const_id.id
							pat_line_obj = self.pool.get('ch.mocwise.rate').search(cr,uid,[('code','=',item_moc_const_id),('header_id','=',pattern_rec.id)])
							if pat_line_obj:
								pat_line_rec = self.pool.get('ch.mocwise.rate').browse(cr,uid,pat_line_obj[0])
								moc_id = pat_line_rec.moc_id.id
						elif catg == 'acc':
							moc_id = item.moc_id.id
				else:
					moc_id = fou_line.moc_id.id
				if moc_id > 0:
					moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
					if moc_rec.weight_type == 'ci':
						qty = fou_line.qty * pattern_rec.ci_weight
					elif moc_rec.weight_type == 'ss':
						qty = fou_line.qty * pattern_rec.pcs_weight
					elif moc_rec.weight_type == 'non_ferrous':
						qty = fou_line.qty * pattern_rec.nonferous_weight
					else:
						qty = 0
					moc_line_id = moc_rec.line_ids
					design_rate = moc_rec.rate
					
				if catg == 'non_acc':
					if bom == 'prime':
						self.pool.get('ch.primecost.view.fou').write(cr,uid,fou_line.id,{'prime_cost': design_rate * qty})
					else:
						self.pool.get('ch.kg.crm.foundry.item').write(cr,uid,fou_line.id,{'prime_cost': design_rate * qty})
					print"design_rate * qtydesign_rate * qty",design_rate * qty
				elif catg == 'acc':
					self.pool.get('ch.crm.access.fou').write(cr,uid,fou_line.id,{'prime_cost': design_rate * qty})
				else:
					pass
				
				pat_amt += design_rate * qty
				print"pat_amtpat_amtpat_amt",pat_amt
			
			if bom == 'fou':
				if item.purpose_categ == 'spare' and catg == 'non_acc':
					spare_id = self.pool.get('ch.spare.offer').create(cr,uid,{
													'header_id': offer_id,
													'pumpseries_id': item.spare_pumpseries_id.id,
													'pump_id': item.spare_pump_id.id,
													'moc_const_id': item.spare_moc_const_id.id,
													'prime_cost': design_rate * qty or 0,
													'enquiry_line_id': item.id,
													'item_code': fou_line.pattern_id.name,
													'item_name': fou_line.pattern_id.pattern_name,
													'pattern_id': fou_line.pattern_id.id,
													'moc_id': fou_line.moc_id.id,
													'qty': fou_line.qty,
													})
											
		prime_cost_1 = pat_amt 
		print"vvvvvvvvvvvvvvvvvvvvvvvvvvv",prime_cost_1
		prime_cost += prime_cost_1
		print"prime_costprime_costprime_cost",prime_cost
		
		#~ if bom == 'fou' and purpose_categ == 'spare' and catg == 'non_acc':
			#~ primecost_vals = prime_cost
			#~ return primecost_vals
			
		# MS Item 
		
		ms_price = 0.00
		for ms_line in bom_ms_line_id:
			if ms_line.is_applicable == True:
				moc_id = 0
				tot_price = 0.00
				ms_rec = self.pool.get('kg.machine.shop').browse(cr,uid,ms_line.ms_id.id)
				if not ms_line.moc_id:
					if catg == 'non_acc':
						if bom == 'prime':
							item_moc_const_id = item.moc_const_id.code
						else:
							if item.purpose_categ == 'pump':
								item_moc_const_id = item.moc_const_id.code
							elif item.purpose_categ == 'spare':
								item_moc_const_id = item.spare_moc_const_id.code
						ms_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',item_moc_const_id),('header_id','=',ms_rec.id)])
						if ms_line_obj:
							ms_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,ms_line_obj[0])
							moc_id = ms_line_rec.moc_id.id
					elif catg == 'acc':
						moc_id = ms_line.moc_id.id
				else:
					moc_id = ms_line.moc_id.id
				if moc_id > 0:	
					if ms_rec.line_ids:
						for raw_line in ms_rec.line_ids:
							brandmoc_obj = self.pool.get('kg.brandmoc.rate').search(cr,uid,[('product_id','=',raw_line.product_id.id),('state','=','approved')])
							if brandmoc_obj:
								brandmoc_rec = self.pool.get('kg.brandmoc.rate').browse(cr,uid,brandmoc_obj[0])
								brandmoc_line_sql = """ select rate from ch_brandmoc_rate_details where moc_id =  %s and header_id = %s order by rate desc limit 1"""%(moc_id,brandmoc_rec.id)
								cr.execute(brandmoc_line_sql)		
								brandmoc_line_data = cr.dictfetchall()
								if brandmoc_line_data:
									design_rate = brandmoc_line_data[0]['rate']
									if raw_line.product_id.uom_conversation_factor == 'one_dimension':
										if raw_line.uom.id == brandmoc_rec.uom_id.id:
											qty = raw_line.qty
											
										elif raw_line.uom.id != brandmoc_rec.uom_id.id:
											qty = raw_line.weight
									elif raw_line.product_id.uom_conversation_factor == 'two_dimension':
										qty = raw_line.weight
									price = design_rate * qty
								else:
									qty = design_rate = price = 0
								tot_price += price
								if catg == 'non_acc':
									if bom == 'prime':
										self.pool.get('ch.primecost.view.ms').write(cr,uid,ms_line.id,{'prime_cost': tot_price * ms_line.qty})
									else:
										self.pool.get('ch.kg.crm.machineshop.item').write(cr,uid,ms_line.id,{'prime_cost': tot_price * ms_line.qty})
								elif catg == 'acc':
									print"tot_price",tot_price
									print"tot_price",type(tot_price)
									print"tot_price",ms_line.qty
									print"tot_price",type(ms_line.qty)
									ss= tot_price * ms_line.qty
									print"ssssssssssssssssssssssssssssssS",ss
									self.pool.get('ch.crm.access.ms').write(cr,uid,ms_line.id,{'prime_cost': tot_price * ms_line.qty})
								else:
									pass
						if bom == 'ms':
							if item.purpose_categ == 'spare' and catg == 'non_acc':
								spare_id = self.pool.get('ch.spare.offer').create(cr,uid,{
																'header_id': offer_id,
																'pumpseries_id': item.spare_pumpseries_id.id,
																'pump_id': item.spare_pump_id.id,
																'moc_const_id': item.spare_moc_const_id.id,
																'prime_cost': tot_price * ms_line.qty,
																'enquiry_line_id': item.id,
																'item_code': ms_line.ms_id.code,
																'item_name': ms_line.ms_id.name,
																'ms_id': ms_line.ms_id.id,
																'moc_id': ms_line.moc_id.id,
																'qty': ms_line.qty,
																})
																
				ms_price += tot_price * ms_line.qty
				#~ if catg == 'non_acc':
					#~ self.pool.get('ch.kg.crm.machineshop.item').write(cr,uid,ms_line.id,{'prime_cost': design_rate * qty * ms_line.qty})
				#~ elif catg == 'acc':
					#~ self.pool.get('ch.crm.access.ms').write(cr,uid,ms_line.id,{'prime_cost': design_rate * qty * ms_line.qty})
			print"ms_pricems_price",ms_price
		#~ if bom == 'ms' and purpose_categ == 'spare' and catg == 'non_acc':
			#~ primecost_vals = ms_price
			#~ return primecost_vals
			
		# BOT Item 
		
		bot_price = 0.00
		for bot_line in bom_bot_line_id:
			if bot_line.is_applicable == True:
				if catg == 'non_acc':
					if bot_line.flag_is_bearing == True:
						if not bot_line.brand_id:
							raise osv.except_osv(_('Warning!'),
								_('%s You cannot save without Brand'%(bot_line.ms_id.code)))
				
				moc_id = 0
				tot_price = 0.00
				if catg == 'non_acc':
					if bom == 'prime':
						ms_id = bot_line.bot_id.id
					else:
						ms_id = bot_line.ms_id.id
				elif catg == 'acc':
					ms_id = bot_line.ms_id.id
				
				ms_obj = self.pool.get('kg.machine.shop').search(cr,uid,[('id','=',ms_id)])
				if ms_obj:
					ms_rec = self.pool.get('kg.machine.shop').browse(cr,uid,ms_obj[0])
					if bom == 'prime':
						if not bot_line.bot_id:
							if bom == 'prime':
								item_moc_const_id = item.moc_const_id.code
							else:
								if item.purpose_categ == 'pump':
									item_moc_const_id = item.moc_const_id.code
								elif item.purpose_categ == 'spare':
									item_moc_const_id = item.spare_moc_const_id.code
							ms_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',item_moc_const_id),('header_id','=',ms_rec.id)])
							if ms_line_obj:
								ms_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,ms_line_obj[0])
								moc_id = ms_line_rec.moc_id.id
						else:
							moc_id = bot_line.moc_id.id
					else:
						if not bot_line.ms_id:
							if item.purpose_categ == 'pump':
								item_moc_const_id = item.moc_const_id.code
							elif item.purpose_categ == 'spare':
								item_moc_const_id = item.spare_moc_const_id.code
							ms_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',item_moc_const_id),('header_id','=',ms_rec.id)])
							if ms_line_obj:
								ms_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,ms_line_obj[0])
								moc_id = ms_line_rec.moc_id.id
						else:
							moc_id = bot_line.moc_id.id
					if moc_id > 0:
						if ms_rec.line_ids:
							for raw_line in ms_rec.line_ids:
								brandmoc_obj = self.pool.get('kg.brandmoc.rate').search(cr,uid,[('product_id','=',raw_line.product_id.id),('state','=','approved')])
								if brandmoc_obj:
									brandmoc_rec = self.pool.get('kg.brandmoc.rate').browse(cr,uid,brandmoc_obj[0])
									if bot_line.brand_id.id:
										brandmoc_line_sql = """ select rate from ch_brandmoc_rate_details where moc_id =  %s and header_id = %s and brand_id = %s order by rate desc limit 1"""%(moc_id,brandmoc_rec.id,bot_line.brand_id.id)
										cr.execute(brandmoc_line_sql)		
										brandmoc_line_data = cr.dictfetchall()
									else:
										brandmoc_line_sql = """ select rate from ch_brandmoc_rate_details where moc_id =  %s and header_id = %s order by rate desc limit 1"""%(moc_id,brandmoc_rec.id)
										cr.execute(brandmoc_line_sql)		
										brandmoc_line_data = cr.dictfetchall()
									if brandmoc_line_data:
										design_rate = brandmoc_line_data[0]['rate']
										if raw_line.product_id.uom_conversation_factor == 'one_dimension':
											if raw_line.uom.id == brandmoc_rec.uom_id.id:
												qty = raw_line.qty
											elif raw_line.uom.id != brandmoc_rec.uom_id.id:
												qty = raw_line.weight
										elif raw_line.product_id.uom_conversation_factor == 'two_dimension':
											qty = raw_line.weight
										price = design_rate * qty
									else:
										qty = design_rate = price = 0
									tot_price += price
									
									if catg == 'non_acc':
										if bom == 'prime':
											self.pool.get('ch.primecost.view.bot').write(cr,uid,bot_line.id,{'prime_cost': tot_price * bot_line.qty})		
										else:
											self.pool.get('ch.kg.crm.bot').write(cr,uid,bot_line.id,{'prime_cost': tot_price * bot_line.qty})		
									elif catg == 'acc':
										self.pool.get('ch.crm.access.bot').write(cr,uid,bot_line.id,{'prime_cost': tot_price * bot_line.qty})
									else:
										pass
							if bom == 'bot':
								if item.purpose_categ == 'spare' and catg == 'non_acc':
									spare_id = self.pool.get('ch.spare.offer').create(cr,uid,{
																'header_id': offer_id,
																'pumpseries_id': item.spare_pumpseries_id.id,
																'pump_id': item.spare_pump_id.id,
																'moc_const_id': item.spare_moc_const_id.id,
																'prime_cost': tot_price * bot_line.qty,
																'enquiry_line_id': item.id,
																'item_code': bot_line.ms_id.code,
																'item_name': bot_line.ms_id.name,
																'bot_id': bot_line.ms_id.id,
																'moc_id': bot_line.moc_id.id,
																'qty': bot_line.qty,
																})
					bot_price += tot_price * bot_line.qty
					#~ if catg == 'non_acc':
						#~ self.pool.get('ch.kg.crm.bot').write(cr,uid,bot_line.id,{'prime_cost': design_rate * qty * bot_line.qty})		
					#~ elif catg == 'acc':
						#~ self.pool.get('ch.crm.access.bot').write(cr,uid,bot_line.id,{'prime_cost': design_rate * qty * bot_line.qty})
					print"bot_pricebot_price",bot_price
					
		print"prime_cost",prime_cost
		print"ms_price",ms_price
		print"bot_price",bot_price
		#~ if bom == 'bot' and purpose_categ == 'spare' and catg == 'non_acc':
			#~ primecost_vals = bot_price
			#~ return primecost_vals
		if catg == 'non_acc':
			if bom == 'prime':
				item_qty = item.qty
			else:
				if item.purpose_categ == 'pump':
					item_qty = item.qty
				elif item.purpose_categ == 'spare':
					item_qty = 1
		elif catg == 'acc':
			item_qty = item.qty
		print"item_qtyitem_qty",item_qty
		primecost_tot = (prime_cost + ms_price + bot_price) 
		primecost_vals = primecost_tot
		print"primecost_valsprimecost_vals",primecost_vals
		
		return primecost_vals
				
	def entry_call_back(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			self.write(cr, uid, ids, {'state': 'call','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
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
		return super(kg_crm_enquiry, self).write(cr, uid, ids, vals, context)
		
kg_crm_enquiry()


class ch_kg_crm_enquiry(osv.osv):

	_name = "ch.kg.crm.enquiry"
	_description = "Child CRM Enquiry Details"
	_order = "enquiry_id"
	
	_columns = {
	
		### Enquiry History Details ####
		'header_id':fields.many2one('kg.crm.enquiry', 'Enquiry', ondelete='cascade'),
		'enquiry_id':fields.many2one('kg.crm.enquiry', 'Enquiry'),
		#'purpose': fields.related('enquiry_id','purpose', type='char', string='Purpose', store=True),
		'purpose': fields.related('enquiry_id','purpose', type='selection',selection=PURPOSE_SELECTION, string='Purpose'),
		'due_date': fields.related('enquiry_id','due_date', type='date', string='Due Date'),
		#'state': fields.related('enquiry_id','state', type='char', string='Status'),
		'state': fields.related('enquiry_id','state', type='selection', selection=STATE_SELECTION, string='Status'),
		#'call_type': fields.related('enquiry_id','call_type', type='char', string='Call Type', store=True),
		'call_type': fields.related('enquiry_id', 'call_type', type='selection', selection=CALL_TYPE_SELECTION, string='Call Type'),
		
		
	}
	
	"""
	def default_get(self, cr, uid, fields, context=None):
		return context
	
	def create(self, cr, uid, vals, context=None):
		header_rec = self.pool.get('kg.crm.enquiry').browse(cr, uid,vals['header_id'])
		if header_rec.state == 'draft':
			res = super(ch_kg_crm_enquiry, self).create(cr, uid, vals, context=context)
		else:
			res = False
		return res
	"""	
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_kg_crm_enquiry, self).write(cr, uid, ids, vals, context)
		
	
ch_kg_crm_enquiry()


class ch_kg_crm_pumpmodel(osv.osv):

	_name = "ch.kg.crm.pumpmodel"
	_description = "Child Pump Model Details"
	
	_columns = {
	
		# Pump Details
		'header_id':fields.many2one('kg.crm.enquiry', 'Enquiry', ondelete='cascade'),
		'enquiry_id':fields.many2one('kg.crm.enquiry', 'Enquiry'),
		#~ 'pump_id':fields.many2one('kg.pumpmodel.master', 'Pump'),
		'qty':fields.integer('Quantity'),
		'del_date':fields.date('Delivery Date'),
		'oth_spec':fields.char('Other Specification'),
		'purpose_categ': fields.selection([('pump','Pump'),('spare','Spare'),('access','Accessories')],'Purpose Category'),
		#~ 'purpose_categ': fields.selection([('pump','Pump'),('spare','Spare'),('prj','Project'),('pump_spare','Pump With Spare')],'Purpose Category'),
		'line_ids': fields.one2many('ch.kg.crm.foundry.item', 'header_id', "Foundry Details"),
		'line_ids_a': fields.one2many('ch.kg.crm.machineshop.item', 'header_id', "Machineshop Details"),
		'line_ids_b': fields.one2many('ch.kg.crm.bot', 'header_id', "BOT Details"),
		'line_ids_moc_a': fields.one2many('ch.moc.construction', 'header_id', "MOC Construction"),
		'line_ids_access_a': fields.one2many('ch.kg.crm.accessories', 'header_id', "Accessories"),
		
		# Item Details
		's_no': fields.char('Serial Number'),
		'equipment_no': fields.char('Equipment/Tag No.'),
		'quantity_in_no': fields.integer('Quantity in No.'),
		'description': fields.char('Description'),
		
		# Liquid Specifications
		'solid_concen': fields.float('Solid Concentration by weight %'),
		'solid_concen_vol': fields.float('Solid Concentration by Volume %'),
		'max_particle_size_mm': fields.float('Max Particle Size-mm'),
		'fluid_id': fields.many2one('kg.fluid.master','Liquid',domain="[('state','not in',('reject','cancel'))]"),
		'temperature_in_c': fields.char('Temperature in C'),
		'density': fields.integer('Density(kg/m3)'),
		'specific_gravity': fields.float('Specific Gravity'),
		'viscosity': fields.integer('Viscosity in CST'),
		'npsh_avl': fields.integer('NPSH-AVL'),
		'capacity_in_liquid': fields.integer('Capacity in M3/hr(Liquid)'),
		'head_in_liquid': fields.float('Total Head in Mlc(Liquid)'),
		'consistency': fields.float('Consistency In %'),
		
		# Duty Parameters
		
		'capacity_in': fields.integer('Capacity in M3/hr(Water)',),
		'head_in': fields.float('Total Head in Mlc(Water)'),
		'viscosity_crt_factor': fields.float('Viscosity correction factors'),
		'suction_pressure': fields.selection([('normal','Normal'),('centre_line','Centre Line')],'Suction pressure'),
		'differential_pressure_kg': fields.float('Differential Pressure - kg/cm2'),
		'slurry_correction_in': fields.float('Slurry Correction in'),
		'temperature': fields.selection([('normal','NORMAL'),('jacketting','JACKETTING'),('centre_line','CENTRE LINE')],'Temperature Condition'),
		'suction_condition': fields.selection([('positive','Positive'),('negative','Negative'),('flooded','Flooded'),('sub_merged','Submerged')],'Suction Condition'),
		'discharge_pressure_kg': fields.float('Discharge Pressure - kg/cm2'),
		'suction_pressure_kg': fields.float('Suction Pressure - kg/cm2'),
		
		# Pump Specification
		'pump_type': fields.char('Pump Model'),		
		'casing_design': fields.selection([('base','Base'),('center_line','Center Line')],'Casing Feet Location'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True),		
		'spare_pump_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True),		
		'size_suctionx': fields.char('Size-SuctionX Delivery(mm)'),
		'flange_standard': fields.many2one('ch.pumpseries.flange','Flange Standard',domain="[('flange_type','=',flange_type),('header_id','=',pumpseries_id)]"),
		'efficiency_in': fields.float('Efficiency in % Wat'),
		'npsh_r_m': fields.float('NPSH R - M'),
		'best_efficiency': fields.float('Best Efficiency NPSH in M'),
		'bkw_water': fields.float('BKW Water'),
		'bkw_liq': fields.float('BKW Liq'),		
		'impeller_dia_rated': fields.float('Impeller Dia Rated mm'),
		'impeller_tip_speed': fields.float('Impeller Tip Speed -M/Sec'),		
		'hydrostatic_test_pressure': fields.float('Hydrostatic Test Pressure - Kg/cm2'),		
		'setting_height': fields.char('Setting Height'),		
		'shut_off_head': fields.float('Shut off Head in M'),
		'shut_off_pressure': fields.float('Shut off Pressure'),
		'minimum_contionuous': fields.float('Minimum Contionuous Flow - M3/hr'),
		'specific_speed': fields.float('Specific Speed'),
		'suction_specific_speed': fields.float('Suction Specific Speed'),
		'sealing_water_pressure': fields.float('Sealing Water Pressure Kg/cm^2'),
		'sealing_water_capacity': fields.float('Sealing Water Capcity- m3/hr'),
		'gd_sq_value': fields.float('GD SQ value'),
		'critical_speed': fields.float('Critical Speed'),
		'bearing_make': fields.many2one('kg.brand.master','Bearing Make'),
		'engine_make': fields.many2one('kg.brand.master','Engine Make'),
		'motor_make': fields.many2one('kg.brand.master','Motor Make'),
		'engine_type': fields.char('Engine Type'),
		'motor_type': fields.selection([('eff_1','EFF-1'),('eff_2','EFF-2'),('eff_3','EFF-3')],'Motor Type'),
		'motor_mounting': fields.selection([('foot','Foot'),('flange','Flange')],'Motor Mounting'),
		'bearing_number_nde': fields.char('BEARING NUMBER NDE / DE'),
		'bearing_qty_nde': fields.float('Bearing qty NDE / DE'),
		'type_of_drive': fields.selection([('motor_direct','Direct'),('belt_drive','Belt drive'),('fc_gb','Fluid Coupling Gear Box')],'Transmission'),
		'end_of_the_curve': fields.float('End of the curve - KW(Rated) liquid'),
		'motor_frequency_hz': fields.float('Motor frequency HZ'),
		'frequency': fields.selection([('50','50'),('60','60')],'Motor frequency (HZ)'),
		'motor_margin': fields.float('Motor Margin(%)'),
		'motor_kw': fields.float('Motor KW'),
		'speed_in_pump': fields.float('Speed in RPM-Pump'),
		'speed_in_motor': fields.float('Speed in RPM-Motor'),
		'full_load_rpm': fields.float('Speed in RPM - Engine'),
		'engine_kw': fields.float('Engine KW'),
		'belt_loss_in_kw': fields.float('Belt Loss in Kw - 3% of BKW'),
		'type_make_selection': fields.selection([('base','Base'),('center_line','Center Line')],'Type Make Selection'),
		'engine_rpm': fields.float('Engine(RPM)'),
		'shaft_sealing': fields.selection([('gld_packing_tiga','Gland Packing-TIGA'),('gld_packing_ptfe','Gland Packing-PTFE'),('mc_seal','M/C Seal'),('dynamic_seal','Dynamic seal')],'Shaft Sealing'),
		'scope_of_supply': fields.selection([('bare_pump','Bare Pump'),('pump_with_acces','Pump With Accessories'),('pump_with_acces_motor','Pump With Accessories And Motor')],'Scope of Supply'),
		'drive': fields.selection([('motor','MOTOR'),('vfd','VFD'),('engine','ENGINE')],'Drive'),
		'flange_type': fields.selection([('standard','Standard'),('optional','Optional')],'Flange Type'),
		'pre_suppliy_ref': fields.char('Previous Supply Reference'),
		'market_division': fields.selection([('cp','CP'),('ip','IP')],'Market Division'),
		'lubrication_type': fields.selection([('grease','Grease'),('oil','Oil')],'Lubrication'),
		'flag_standard': fields.boolean('Non Standard'),
		'push_bearing': fields.selection([('grease_bronze','Grease'),('cft','CFT'),('cut','Cut Less Rubber')],'Bush Bearing'),
		'suction_size': fields.selection([('32','32'),('40','40'),('50','50'),('65','65'),('80','80'),('100','100'),('125','125'),('150','150'),('200','200'),('250','250'),('300','300')],'Suction Size'),
		'speed_in_rpm': fields.float('Speed in RPM - Pump'),
		'pump_model_type':fields.selection([('vertical','Vertical'),('horizontal','Horizontal')], 'Pump Type'),
		'bush_bearing_lubrication':fields.selection([('grease','Grease'),('external','External'),('self','Self'),('ex_pressure','External Under Pressure')], 'Bush Bearing Lubrication'),
		'del_pipe_size': fields.selection([('32','32'),('40','40'),('50','50'),('65','65'),('80','80'),('100','100'),('125','125'),('150','150'),('200','200'),('250','250'),('300','300')],'Delivery Pipe Size(MM)'),
		
		# Product model values
		#'impeller_type': fields.char('Impeller Type', readonly=True),
		'impeller_type': fields.selection([('open','Open'),('semi_open','Semi Open'),('close','Closed')],'Impeller Type'),
		'impeller_number': fields.float('Impeller Number of vanes'),
		'impeller_dia_max': fields.float('Impeller Dia Max mm'),
		'impeller_dia_min': fields.float('Impeller Dia Min mm'),
		'maximum_allowable_soild': fields.float('Maximum Allowable Soild Size - MM'),
		'max_allowable_test': fields.float('Max Allowable Casing design Pressure'),
		'number_of_stages': fields.integer('Number of stages'),
		#'crm_type': fields.char('Type', readonly=True),
		'crm_type': fields.selection([('pull_out','End Suction Back Pull Out'),('split_case','Split Case'),('multistage','Multistage'),('twin_casing','Twin Casing'),('single_casing','Single Casing'),('self_priming','Self Priming'),('vo_vs4','VO-VS4'),('vg_vs5','VG-VS5')],'Pump Design'),
		'pumpseries_id': fields.many2one('kg.pumpseries.master','Pump Series'),
		'spare_pumpseries_id': fields.many2one('kg.pumpseries.master','Pump Series'),
		'primemover_id': fields.many2one('kg.primemover.master','Prime Mover'),
		'operation_range': fields.char('Operation Range'),
		'primemover_categ': fields.selection([('engine','ENGINE'),('motor','MOTOR'),('vfd','VFD')],'Primemover Category'),
		'moc_const_id':fields.many2one('kg.moc.construction', 'MOC Construction'),
		'spare_moc_const_id':fields.many2one('kg.moc.construction', 'MOC Construction'),
		'mech_seal_make':fields.many2one('kg.brand.master', 'Mech. Seal Make'),
		'seal_type': fields.selection([('sums','Single Unbalanced Multiple Spring'),('suss','Single Unbalanced Single Spring'),
										('sbsm','Single Balanced Spring Stationary Mounted'),('cs','Cartridge Seal'),
										('sbms','Single Balanced Multiple Spring'),('sbss','Single Balanced Single Spring'),
										('sc','Single Cartridge'),('dubtb','Double Unbalanced Back to Back'),
										('dbbtb','Double Balanced Back to Back'),('ts','Tandem Seal'),
										('dc','Double Cartridge'),('drsu','Dry Running - Single Unbalanced'),
										('mbi','Metallic Bellow Inside'),('tbs','Teflon Bellow Seal-Outside Mounted Dry Running')],'Seal Type'),
		'face_combination': fields.selection([('c_vs_sic','C VS SIC'),('sic_vs_sic','SIC VS SIC'),('c_vs_sic','SIC VS SIC / C VS SIC'),('gft_vs_ceramic','GFT VS CERAMIC')],'Face Combination'),
		'gland_plate': fields.char('Gland Plate'),
		'api_plan': fields.char('API Plan'),
		
		# FC GB
		'gear_box_loss_rated': fields.float('Gear Box Loss-Rated'),
		'fluid_coupling_loss_rated': fields.float('Fluid Coupling Loss-Rated'),
		'mototr_output_power_rated': fields.float('Motor Output Power-Rated'),
		'higher_speed_rpm': fields.float('Higher Speed(Rpm)'),
		'head_higher_speed': fields.float('Head At Higher Speed'),
		'effy_high_speed': fields.float('Efficiency At High Speed'),
		'pump_input_higher_speed': fields.float('Pump Input At Higher Speed'),
		'gear_box_loss_high_speed': fields.float('Gear Box Loss-High Speed'),
		'fluid_coupling_loss': fields.float('Fluid Coupling Loss-High Speed'),
		'motor_output_power_high_speed': fields.float('Motor Output Power-High Speed'),
		'lower_speed_rpm': fields.float('Lower Speed(Rpm)'),
		'head_lower_speed': fields.float('Head At Lower Speed'),
		'effy_lower_speed_point': fields.float('Efficiency At Lower Speed Point'),
		'pump_input_lower_speed': fields.float('Pump Input At Lower Speed'),
		'gear_box_loss_lower_speed': fields.float('Gear Box Loss-Lower Speed'),
		'fluid_coupling_loss_lower_speed': fields.float('Fluid Coupling Loss-Lower Speed'),
		'motor_output_power_lower_speed': fields.float('Motor Output Power-Lower Speed'),
		
		# Accesssories 
		'acces': fields.selection([('yes','Yes'),('no','No')],'Accessories'),
		'acces_type': fields.selection([('coupling','Coupling'),('coupling_guard','Coupling Guard'),('base_plate','Base Plate')],'Type'),
		
		'wo_line_id': fields.many2one('ch.work.order.details','WO'),
		'wo_no': fields.char('WO Number'),
		
		'load_bom': fields.boolean('Load BOM'),
		'spare_load_bom': fields.boolean('Load BOM'),
		
		
	}
	
	_defaults = {
		
		'temperature': 'normal',
		'flange_type': 'standard',
		'load_bom': False,
		'spare_load_bom': False,
		
	}
	
	#~ 
	#~ def default_get(self, cr, uid, fields, context=None):
		#~ return context
	"""
	def create(self, cr, uid, vals, context=None):
		header_rec = self.pool.get('kg.crm.enquiry').browse(cr, uid,vals['header_id'])
		if header_rec.state == 'draft':
			res = super(ch_kg_crm_enquiry, self).create(cr, uid, vals, context=context)
		else:
			res = False
		return res
	"""	

	def default_get(self, cr, uid, fields, context=None):
		print"contextcontextcontext",context
		
		if len(context)>7:
			if not context['purpose_categ']:
				raise osv.except_osv(_('Warning!'),
						_('Kindly select Purpose !!'))
			if context['purpose_categ']:
				if context['purpose_categ'] == 'pump':
					context['purpose_categ'] = 'pump'
				if context['purpose_categ'] == 'spare':
					context['purpose_categ'] = 'spare'
				if context['purpose_categ'] == 'access':
					context['purpose_categ'] = 'access'
					context['acces'] = 'yes'
				if context['purpose_categ'] == 'pump_spare':
					context['purpose_categ'] = ''
				else:
					pass
			else:
				pass
		return context
		
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.purpose_categ == 'pump':
			if rec.qty <= 0.00:
				raise osv.except_osv(_('Warning!'),
					_('%s You cannot save with zero qty'%(rec.pump_id.name)))
		return True
		
	def _check_access(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.acces == 'yes' and not rec.line_ids_access_a:
			if rec.purpose_categ == 'pump':
				raise osv.except_osv(_('Warning!'),
					_('%s You cannot save without accessories'%(rec.pump_id.name)))
			elif rec.purpose_categ == 'spare':
				raise osv.except_osv(_('Warning!'),
					_('%s You cannot save without accessories'%(rec.spare_pump_id.name)))
		return True
		
	def _check_access_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.acces == 'yes' and rec.line_ids_access_a:
			for item in rec.line_ids_access_a:
				if item.qty == 0:
					if rec.purpose_categ == 'pump':
						raise osv.except_osv(_('Warning!'),
							_('%s %s You cannot save with zero qty'%(rec.pump_id.name,item.access_id.name)))
					elif rec.purpose_categ == 'spare':
						raise osv.except_osv(_('Warning!'),
							_('%s %s You cannot save with zero qty'%(rec.spare_pump_id.name,item.access_id.name)))
		
		return True
		
	def _check_is_applicable(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		applicable = ''
		applicable_a = ''
		applicable_b = ''
		if rec.purpose_categ == 'spare':
			print"ssssssssssssssssss",rec.line_ids
			if rec.line_ids:
				fou_data = [x for x in rec.line_ids if x.is_applicable == True]
				print"fou_datafou_datafou_datafou_datafou_data",fou_data
				if fou_data:
					applicable='yes'
				else:
					applicable='no'
			if rec.line_ids_a:
				ms_data = [x for x in rec.line_ids_a if x.is_applicable == True]
				if ms_data:
					applicable_a='yes'
				else:
					applicable_a='no'
			if rec.line_ids_b:
				bot_data = [x for x in rec.line_ids_b if x.is_applicable == True]
				if bot_data:
					applicable_b='yes'
				else:
					applicable_b='no'
		if applicable == 'no' and applicable_a == 'no' and applicable_b == 'no':
			return False
		return True
	
	def _check_lineitems(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if not entry.line_ids_access_a and entry.acces == 'yes':
			return False
		return True
	
	_constraints = [
	
		(_check_qty,'You cannot save with zero qty !',['Qty']),
		(_check_access,'You cannot save without accessories !',['']),
		(_check_access_qty,'You cannot save with zero qty !',['Qty']),
		#~ (_check_lineitems, 'System not allow to save with empty Accessories Details !!',['']),
		#~ (_check_is_applicable,'You cannot save without Is applicable !',['Is Applicable']),
		
		]
		
	def onchange_purpose_categ(self, cr, uid, ids, purpose_categ, context=None):
		value = {'acces':''}
		if purpose_categ == 'access':
			value = {'acces': 'yes'}
		elif purpose_categ:
			value = {'acces': ''}
		print"valuevalue",value
		return {'value': value}
		
	def onchange_capacity_in_liquid(self, cr, uid, ids, capacity_in_liquid, head_in_liquid, context=None):
		value = {'capacity_in_liquid':'','head_in_liquid': ''}
		if capacity_in_liquid or head_in_liquid:
			value = {'capacity_in': capacity_in_liquid,'head_in':head_in_liquid}
		return {'value': value}
		
	def onchange_wo(self, cr, uid, ids, wo_no, context=None):
		value = {'wo_line_id':'','spare_moc_const_id':''}
		if wo_no:
			wo_obj = self.pool.get('ch.work.order.details').search(cr,uid,[('order_no','=',wo_no)])
			if wo_obj:
				wo_rec = self.pool.get('ch.work.order.details').browse(cr,uid,wo_obj[0])
				print"wo_rec",wo_rec
				value = {'wo_line_id': wo_rec.id,'spare_moc_const_id':wo_rec.moc_construction_id.id}
		return {'value': value}
		
	def onchange_wo_line(self, cr, uid, ids, wo_line_id, context=None):
		value = {'spare_pump_id':'','spare_moc_const_id':'','wo_no':''}
		if wo_line_id:
			wo_obj = self.pool.get('ch.work.order.details').search(cr,uid,[('id','=',wo_line_id)])
			if wo_obj:
				wo_rec = self.pool.get('ch.work.order.details').browse(cr,uid,wo_obj[0])
				value = {'spare_pump_id': wo_rec.pump_model_id.id,'spare_moc_const_id':wo_rec.moc_construction_id.id,'wo_no':wo_rec.order_no}
		return {'value': value}
		
	def onchange_moc(self, cr, uid, ids, moc_const_id,flag_standard,purpose_categ):
		moc_const_vals=[]
		load_bom = ''
		if moc_const_id != False:
			if purpose_categ == 'pump':
				load_bom = True
			moc_const_rec = self.pool.get('kg.moc.construction').browse(cr, uid, moc_const_id)
			for item in moc_const_rec.line_ids:
				moc_const_vals.append({
																
								'moc_id': item.moc_id.id,
								'offer_id': item.offer_id.id,
								'remarks': item.remarks,
								'flag_standard':flag_standard,
								
								})
		return {'value': {'line_ids_moc_a': moc_const_vals}}
		
	def onchange_spare_moc(self, cr, uid, ids, spare_moc_const_id,purpose_categ):
		spare_load_bom = ''
		if spare_moc_const_id != False:
			if purpose_categ == 'spare':
				spare_load_bom = False
			
		return {'value': {'spare_load_bom':spare_load_bom}}
	
	def onchange_load_bom(self, cr, uid, ids, load_bom,spare_load_bom,spare_pump_id,pump_id,wo_line_id,purpose_categ,spare_moc_const_id,moc_const_id,qty):
		fou_vals=[]
		ms_vals=[]
		bot_vals=[]
		data_rec = ''
		if not moc_const_id and purpose_categ == 'pump' and load_bom == True:
			raise osv.except_osv(_('Warning!'),
				_('System sholud not be accept without MOC Construction'))
		if not spare_moc_const_id and purpose_categ == 'spare' and spare_load_bom == True:
			raise osv.except_osv(_('Warning!'),
				_('System sholud not be accept without MOC Construction'))
		
		print"spare_pump_id",spare_pump_id
		print"pump_id",pump_id
		print"load_bom",load_bom
		print"spare_load_bom",spare_load_bom
		if load_bom == True:
			if purpose_categ == 'pump':
				print"aaaaaaaaaa"
				bom_obj = self.pool.get('kg.bom').search(cr, uid, [('pump_model_id','=',pump_id),('state','in',('draft','confirmed','approved'))])
				if bom_obj:
					data_rec = self.pool.get('kg.bom').browse(cr, uid, bom_obj[0])
		elif spare_load_bom == True:
			if purpose_categ == 'spare':
				if wo_line_id:
					print"wo_line_idwo_line_id",wo_line_id
					wo_obj = self.pool.get('ch.work.order.details').search(cr,uid,[('id','=',wo_line_id)])
					if wo_obj:
						data_rec = self.pool.get('ch.work.order.details').browse(cr, uid, wo_obj[0])
				else:
					bom_obj = self.pool.get('kg.bom').search(cr, uid, [('pump_model_id','=',spare_pump_id),('state','in',('draft','confirmed','approved'))])
					if bom_obj:
						data_rec = self.pool.get('kg.bom').browse(cr, uid, bom_obj[0])
		print"data_recdata_rec",data_rec
		
		if data_rec:
			if purpose_categ == 'spare' and spare_pump_id:
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
									pat_line_obj = self.pool.get('ch.mocwise.rate').search(cr,uid,[('code','=',spare_moc_const_id),('header_id','=',pat_rec.id)])
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
										'is_applicable': False,
										'purpose_categ': purpose_categ,
										#~ 'csd_no': item.csd_no,
										#~ 'remarks': item.remarks,
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
									cons_rec = self.pool.get('kg.moc.construction').browse(cr,uid,spare_moc_const_id)
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
										'is_applicable': False,
										'purpose_categ': purpose_categ,
										#~ 'csd_no': item.csd_no,
										#~ 'remarks': item.remarks,
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
									cons_rec = self.pool.get('kg.moc.construction').browse(cr,uid,spare_moc_const_id)
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
										'is_applicable': False,
										'flag_is_bearing': bot_rec.is_bearing,
										'purpose_categ': purpose_categ,
										#~ 'position_id': item.position_id.id,
										#~ 'remarks': item.remarks,
										})
					print"bot_valsbot_vals",bot_vals
			if purpose_categ == 'pump' and pump_id:
				if qty <= 0:
					raise osv.except_osv(_('Warning!'),
						_('System sholud not be accept without Quantity'))	
				if data_rec.line_ids:
					for item in data_rec.line_ids:
						print"moc_const_id",moc_const_id
						moc_id = ''
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
						print"moc_idmoc_id",moc_id	
								
						fou_vals.append({
										'position_id': item.position_id.id,
										'pattern_id': item.pattern_id.id,
										'pattern_name': item.pattern_name,
										'moc_id': moc_id,
										'qty': item.qty * qty,
										'load_bom': True,
										'is_applicable': True,
										'purpose_categ': purpose_categ,
										#~ 'csd_no': item.csd_no,
										#~ 'remarks': item.remarks,
										})
						print"fou_valsfou_vals",fou_vals
				if data_rec.line_ids_a:
					for item in data_rec.line_ids_a:
						moc_id = ''
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
										'qty': item.qty * qty,
										'load_bom': True,
										'is_applicable': True,
										'purpose_categ': purpose_categ,
										#~ 'csd_no': item.csd_no,
										#~ 'remarks': item.remarks,
										})
						print"ms_valsms_vals",ms_vals
				if data_rec.line_ids_b:
					for item in data_rec.line_ids_b:
						moc_id = ''
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
										'qty': item.qty * qty,
										'load_bom': True,
										'is_applicable': True,
										'flag_is_bearing': bot_rec.is_bearing,
										'purpose_categ': purpose_categ,
										#~ 'position_id': item.position_id.id,
										#~ 'remarks': item.remarks,
										})
						print"bot_valsbot_vals",bot_vals
					
		return {'value': {'line_ids': fou_vals,'line_ids_a': ms_vals,'line_ids_b': bot_vals}}
		
	def onchange_flange_type(self, cr, uid, ids, flange_type, flange_standard, context=None):
		value = {'flange_standard': ''}
		if flange_type:
			value = {'flange_standard': ''}
			
		return {'value': value}
			
	def onchange_differential_pressure_kg(self,cr,uid,ids,head_in,suction_pressure_kg,discharge_pressure_kg,sealing_water_pressure,context=None):
		value = {'differential_pressure_kg': 0,'discharge_pressure_kg': 0}
		total = 0.00
		total = head_in / 10.00
		value = {'differential_pressure_kg': total}
		return {'value': value}
		
	def onchange_bkw_liq(self, cr, uid, ids, bkw_water, bkw_liq, capacity_in, head_in, specific_gravity, efficiency_in, motor_margin, context=None):
		value = {'bkw_water': '','bkw_liq': '','capacity_in': '','head_in': '','specific_gravity': '','efficiency_in': ''}
		total = 0.00
		water_total = 0.00
		if efficiency_in:
			total = ((capacity_in * head_in * specific_gravity) / 367.00 ) / efficiency_in
			water_total = ((capacity_in * head_in * 1) / 367.00 ) / efficiency_in
			#~ water_total = round(water_total,2)
			value = {'bkw_liq': total * 100 ,'bkw_water':water_total * 100}
		return {'value': value}
			
	def onchange_shut_off_pressure(self, cr, uid, ids, shut_off_head, context=None):
		value = {'shut_off_pressure': 0}
		total = 0.00
		if shut_off_head:
			total = shut_off_head / 10.00
			value = {'shut_off_pressure': total}
		return {'value': value}
			
	def onchange_hydrostatic_test_pressure(self, cr, uid, ids, shut_off_pressure, discharge_pressure_kg, context=None):
		value = {'hydrostatic_test_pressure': 0}
		tot_1 = 0.00
		tot_2 = 0.00
		total = 0.00
		if shut_off_pressure and discharge_pressure_kg:
			tot_1 = shut_off_pressure * 1.5
			tot_2 = discharge_pressure_kg * 2
			if tot_1 < tot_2:
				total = tot_2
			elif tot_2 < tot_1:
				total = tot_1
			else:
				total = total
			value = {'hydrostatic_test_pressure': total}
		return {'value': value}
			
	def onchange_motor_margin(self, cr, uid, ids, motor_kw, bkw_liq,context=None):
		value = {'motor_margin': 0}
		total = 0.00
		total = (100 - ((bkw_liq / motor_kw) * 100))
		value = {'motor_margin': total}
		return {'value': value}
			
	def onchange_impeller_tip_speed(self, cr, uid, ids, impeller_tip_speed, impeller_dia_rated, full_load_rpm, context=None):
		value = {'impeller_tip_speed': '','impeller_dia_rated': '','full_load_rpm': ''}
		total = 0.00
		if full_load_rpm or impeller_dia_rated:
			total = ((3.14 * impeller_dia_rated * full_load_rpm) / 60.00 ) / 1000.00
			total = round(total,2)
			value = {'impeller_tip_speed': total}
		return {'value': value}
			
	def onchange_belt_loss_in_kw(self, cr, uid, ids, belt_loss_in_kw, bkw_liq, context=None):
		value = {'belt_loss_in_kw': '','bkw_liq': ''}
		total = 0.00
		if belt_loss_in_kw or bkw_liq:
			total = (bkw_liq / 100.00) * 103.00
			total = round(total,2)
			value = {'belt_loss_in_kw': total}
		return {'value': value}
			
	#~ def onchange_type_of_drive(self,cr,uid,ids,type_of_drive,primemover_categ,context=None):
		#~ 
		#~ value = {'primemover_categ':''}
		#~ if type_of_drive == 'engine':
			#~ value = {'primemover_categ':'engine'}
		#~ else:
			#~ value = {'primemover_categ':primemover_categ}
		#~ return {'value': value}
		
	#~ def onchange_prime_categ(self,cr,uid,ids,primemover_categ,type_of_drive,context=None):
		#~ 
		#~ value = {'type_of_drive':''}
		#~ if primemover_categ == 'engine':
			#~ value = {'type_of_drive':'engine'}
		#~ else:
			#~ value = {'type_of_drive':type_of_drive}
		#~ return {'value': value}
	
	def onchange_primemover(self, cr, uid, ids, primemover_id, context=None):
		
		value = {'frequency':'','motor_kw': '','speed_in_motor': '','engine_kw':''}
		if primemover_id:
			prime_rec = self.pool.get('kg.primemover.master').browse(cr, uid, primemover_id, context=context)
			value = {'frequency': prime_rec.frequency,'motor_kw': prime_rec.power_kw,'speed_in_motor': prime_rec.speed,'engine_kw': prime_rec.power_kw}
			
		return {'value': value}
			
	def onchange_liquid(self, cr, uid, ids, fluid_id, context=None):
		
		value = {'viscosity': '','temperature_in_c': '','specific_gravity': '','solid_concen':'','max_particle_size_mm':'','consistency':''}
		if fluid_id:
			liquid_rec = self.pool.get('kg.fluid.master').browse(cr, uid, fluid_id, context=context)
			value = {'viscosity': liquid_rec.viscosity,'temperature_in_c': liquid_rec.temperature,
					 'specific_gravity': liquid_rec.specific_gravity,'solid_concen':liquid_rec.solid_concentration,
					 'max_particle_size_mm':liquid_rec.max_particle_size_mm,'consistency':liquid_rec.consistency}
			
		return {'value': value}
		
	def onchange_head_in(self, cr, uid, ids, head_in, discharge_pressure_kg, sealing_water_pressure, context=None):
		value = {'head_in': '','sealing_water_pressure':''}
		total = 0.00
		if head_in:
			total = (head_in / 10.00) + 1
			value = {'head_in': head_in,'sealing_water_pressure': total}
			
		return {'value': value}
		
	def onchange_pumpmodel(self, cr, uid, ids, pump_id, market_division,suction_pressure_kg,discharge_pressure_kg,purpose_categ, context=None):
		print"pump_idpump_idpump_idpump_idpump_id",pump_id
		value = {'impeller_type': '','impeller_number': '','impeller_dia_max': '','impeller_dia_min': '','maximum_allowable_soild': '',
				'max_allowable_test': '','number_of_stages': '','crm_type': '','bearing_number_nde':'','bearing_qty_nde':'',
				'pumpseries_id':'','crm_type':'','casing_design':'','sealing_water_capacity':'','size_suctionx':'','gd_sq_value':'',
				'sealing_water_pressure':'','lubrication_type':'','spare_pump_id':'','del_pipe_size':''}
		total = 0.00
		
		if pump_id:
			pump_rec = self.pool.get('kg.pumpmodel.master').browse(cr, uid, pump_id, context=context)
			print"pump_recpump_recpump_rec",pump_rec
			if market_division == 'cp':
				total = suction_pressure_kg + ((discharge_pressure_kg / 100.00) * 40) + pump_rec.sealing_water_pressure
			if market_division == 'ip':
				total = suction_pressure_kg + discharge_pressure_kg + pump_rec.sealing_water_pressure
				
			value = {'impeller_type': pump_rec.impeller_type,'impeller_number': pump_rec.impeller_number,'impeller_dia_max': pump_rec.impeller_dia_max,
			'impeller_dia_min': pump_rec.impeller_dia_min,'maximum_allowable_soild': pump_rec.maximum_allowable_soild,'max_allowable_test': pump_rec.max_allowable_test,
			'number_of_stages': pump_rec.number_of_stages,'crm_type': pump_rec.crm_type,'bearing_number_nde':pump_rec.bearing_no,'bearing_qty_nde':pump_rec.bearing_qty,
			'pumpseries_id':pump_rec.series_id.id,'crm_type':pump_rec.crm_type,'casing_design':pump_rec.feet_location,
			'sealing_water_capacity':pump_rec.sealing_water_capacity,'size_suctionx':pump_rec.pump_size,'gd_sq_value':pump_rec.gd_sq_value,
			'sealing_water_pressure':total,'lubrication_type':pump_rec.lubrication_type,'spare_pump_id':pump_id,'del_pipe_size':pump_rec.delivery_pipe_size}
		print"valuevaluevalue",value
		return {'value': value}
		
	def onchange_pumpseries(self, cr, uid, ids, pumpseries_id, flange_standard, flange_type, context=None):
		
		value = {'flange_standard': '','flange_type': '','spare_pumpseries_id':''}
		if pumpseries_id:
			pumpseries_rec = self.pool.get('kg.pumpseries.master').browse(cr, uid, pumpseries_id, context=context)
			for item in pumpseries_rec.line_ids:
				if item.flange_type == 'standard':
					value = {'flange_standard': item.id,'flange_type': item.flange_type,'spare_pumpseries_id':pumpseries_id}
					return {'value': value}
				
		return True
	
	def onchange_spare_pump_id(self, cr, uid, ids, spare_pump_id,purpose_categ, context=None):
		value = {'pump_id': '','spare_pumpseries_id':''}
		series_id = ''
		
		if spare_pump_id:
			pump_obj = self.pool.get('kg.pumpmodel.master').search(cr,uid,[('id','=',spare_pump_id)])
			if pump_obj:
				pump_rec = self.pool.get('kg.pumpmodel.master').browse(cr,uid,pump_obj[0])
				series_id = pump_rec.series_id.id
			value = {'pump_id': spare_pump_id,'spare_pumpseries_id': series_id}
		return {'value': value}

	def onchange_spare_pumpseries_id(self, cr, uid, ids, spare_pumpseries_id,purpose_categ, context=None):
		value = {'primemover_categ': ''}
		if spare_pumpseries_id:
			value = {'pumpseries_id': spare_pumpseries_id}
		return {'value': value}
		
	def onchange_scope_of_supply(self, cr, uid, ids, scope_of_supply, primemover_categ, context=None):
		
		value = {'primemover_categ': ''}
		if scope_of_supply == 'pump_with_acces_motor':
			value = {'primemover_categ': 'motor'}
		return {'value': value}

	#~ def onchange_type_of_drive(self, cr, uid, ids, type_of_drive, bkw_liq, context=None):
		#~ value = {'gear_box_loss_high_speed':''}
		#~ total = 0.00
		#~ if type_of_drive == 'fc_gb':
			#~ total = bkw_liq * 0.02
			#~ value = {'gear_box_loss_high_speed':total}
		#~ return {'value': value}
			
	def onchange_pump_input_higher_speed(self,cr,uid,ids,capacity_in,head_higher_speed,specific_gravity,effy_high_speed,type_of_drive,context=None):
		value = {'pump_input_higher_speed': 0.00}
		total = 0.00
		if type_of_drive == 'fc_gb' and head_higher_speed != 0.00 and effy_high_speed != 0.00:
			total = (((capacity_in * head_higher_speed * specific_gravity) / 367.00) / (effy_high_speed / 100.00))
			value = {'pump_input_higher_speed': total}
		return {'value': value}
			
	def onchange_mototr_output_power_rated(self, cr, uid, ids, gear_box_loss_rated, fluid_coupling_loss_rated, bkw_liq, type_of_drive, context=None):
		value = {'mototr_output_power_rated': ''}
		total = 0.00
		if type_of_drive == 'fc_gb':
			total = bkw_liq + gear_box_loss_rated + fluid_coupling_loss_rated 
			value = {'mototr_output_power_rated': total}
		return {'value': value}
			
	def onchange_motor_output_power_high_speed(self,cr,uid,ids,pump_input_higher_speed,gear_box_loss_high_speed,fluid_coupling_loss,type_of_drive,context=None):
		value = {'motor_output_power_high_speed': ''}
		total = 0.00
		if type_of_drive == 'fc_gb':
			total = pump_input_higher_speed + gear_box_loss_high_speed + fluid_coupling_loss 
			value = {'motor_output_power_high_speed': total}
		return {'value': value}
			
	def onchange_pump_input_lower_speed(self,cr,uid,ids,effy_lower_speed_point,specific_gravity,head_lower_speed,capacity_in,type_of_drive,context=None):
		value = {'pump_input_lower_speed': ''}
		total = 0.00
		gear_total = 0.00
		if type_of_drive == 'fc_gb' and effy_lower_speed_point != 0.00 and specific_gravity != 0.00 and capacity_in != 0.00 and effy_lower_speed_point != 0.00:
			total = (((capacity_in * head_lower_speed * specific_gravity) / 367.00) / (effy_lower_speed_point / 100.00))
			value = {'pump_input_lower_speed': total}
		if total > 0.00:
			gear_total = (total / 100.00 ) * 2.00
			value = {'pump_input_lower_speed': total}
		return {'value': value}
			
	def onchange_motor_output_power_lower_speed(self,cr,uid,ids,pump_input_lower_speed,gear_box_loss_lower_speed,fluid_coupling_loss_lower_speed,type_of_drive,context=None):
		value = {'motor_output_power_lower_speed': 0}
		total = 0.00
		if type_of_drive == 'fc_gb' and pump_input_lower_speed != 0.00 and gear_box_loss_lower_speed != 0.00 and fluid_coupling_loss_lower_speed != 0.00:
			total = pump_input_lower_speed + gear_box_loss_lower_speed + fluid_coupling_loss_lower_speed
			value = {'motor_output_power_lower_speed': total}
		return {'value': value}
			
	def create(self, cr, uid, vals, context=None):
		pump_obj = self.pool.get('kg.pumpmodel.master')
		if vals.get('pump_id'):		  
			pump_rec = pump_obj.browse(cr, uid, vals.get('pump_id'))			
			vals.update({'impeller_type': pump_rec.impeller_type,'impeller_number': pump_rec.impeller_number,'impeller_dia_max': pump_rec.impeller_dia_max,
			'impeller_dia_min': pump_rec.impeller_dia_min,'maximum_allowable_soild': pump_rec.maximum_allowable_soild,'max_allowable_test': pump_rec.max_allowable_test,
			'number_of_stages': pump_rec.number_of_stages,'crm_type': pump_rec.crm_type})
		return super(ch_kg_crm_pumpmodel, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		pump_obj = self.pool.get('kg.pumpmodel.master')
		if vals.get('pump_id'):
			pump_rec = pump_obj.browse(cr, uid, vals.get('pump_id'))			
			vals.update({'impeller_type': pump_rec.impeller_type,'impeller_number': pump_rec.impeller_number,'impeller_dia_max': pump_rec.impeller_dia_max,
			'impeller_dia_min': pump_rec.impeller_dia_min,'maximum_allowable_soild': pump_rec.maximum_allowable_soild,'max_allowable_test': pump_rec.max_allowable_test,
			'number_of_stages': pump_rec.number_of_stages,'crm_type': pump_rec.crm_type})
		return super(ch_kg_crm_pumpmodel, self).write(cr, uid, ids, vals, context)  
	
	def load_non_standard(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		
		if rec.flag_standard == True:
			cons_obj = self.pool.get('ch.moc.construction').search(cr,uid,[('header_id','=',rec.id)])
			if cons_obj:
				for item in cons_obj:
					cons_rec = self.pool.get('ch.moc.construction').browse(cr,uid,item)
					self.pool.get('ch.moc.construction').write(cr, uid, cons_rec.id, {'flag_standard': True})
		elif rec.flag_standard == False:
			cons_obj = self.pool.get('ch.moc.construction').search(cr,uid,[('header_id','=',rec.id)])
			if cons_obj:
				for item in cons_obj:
					cons_rec = self.pool.get('ch.moc.construction').browse(cr,uid,item)
					self.pool.get('ch.moc.construction').write(cr, uid, cons_rec.id, {'flag_standard': False})
		return True	
	
ch_kg_crm_pumpmodel()


class ch_kg_crm_foundry_item(osv.osv):

	_name = "ch.kg.crm.foundry.item"
	_description = "Child Foundry Item Details"
	
	_columns = {
	
		### Foundry Item Details ####
		'header_id':fields.many2one('ch.kg.crm.pumpmodel', 'Pump Model Id', ondelete='cascade'),
		'enquiry_id':fields.many2one('kg.crm.enquiry', 'Enquiry'),
		'pump_id':fields.many2one('kg.pumpmodel.master', 'Pump'),
		'qty':fields.integer('Quantity'),
		'oth_spec':fields.char('Other Specification'),
		'position_id': fields.many2one('kg.position.number','Position No.'),
		'csd_no': fields.char('CSD No.', size=128),
		'pattern_name': fields.char('Pattern Name'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No.'),
		'remarks': fields.char('Remarks'),
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'prime_cost': fields.float('Prime Cost'),
		'purpose_categ': fields.selection([('pump','Pump'),('spare','Spare'),('access','Accessories')],'Purpose Category'),
		
	}
	
	_defaults = {
		
		'is_applicable': False,
		'load_bom': False,
		
	}
	
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_kg_crm_foundry_item, self).write(cr, uid, ids, vals, context)
	
	#~ def _check_qty(self, cr, uid, ids, context=None):
		#~ rec = self.browse(cr, uid, ids[0])
		#~ if rec.qty <= 0.00:
			#~ return False
		#~ return True
	
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
	
ch_kg_crm_foundry_item()

class ch_kg_crm_machineshop_item(osv.osv):

	_name = "ch.kg.crm.machineshop.item"
	_description = "Macine Shop Item Details"
	
	_columns = {
	
		### machineshop Item Details ####
		'header_id':fields.many2one('ch.kg.crm.pumpmodel', 'Pump Model Id', ondelete='cascade'),
		'enquiry_id':fields.many2one('kg.crm.enquiry', 'Enquiry'),
		'pos_no': fields.related('position_id','name', type='char', string='Position No.', store=True),
		'position_id': fields.many2one('kg.position.number','Position No.'),
		'csd_no': fields.char('CSD No.'),
		'bom_id': fields.many2one('kg.bom','BOM'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','ms')], ondelete='cascade',required=True),
		'name': fields.related('ms_id','name', type='char',size=128,string='Item Name', store=True),
		#~ 'ms_line_id':fields.many2one('ch.machineshop.details', 'Item Name'),
		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
		#'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'remarks':fields.text('Remarks'),   
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'prime_cost': fields.float('Prime Cost'),
		'purpose_categ': fields.selection([('pump','Pump'),('spare','Spare'),('access','Accessories')],'Purpose Category'),
		
	}
	
	
	_defaults = {
		
		'is_applicable': False,
		'load_bom': False,
		
	}
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_kg_crm_machineshop_item, self).write(cr, uid, ids, vals, context)
		
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False
		return True
	
	_constraints = [
	
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
ch_kg_crm_machineshop_item()

class ch_kg_crm_bot(osv.osv):

	_name = "ch.kg.crm.bot"
	_description = "BOT Details"
	
	_columns = {
	
		### BOT Item Details ####
		'header_id':fields.many2one('ch.kg.crm.pumpmodel', 'Pump Model Id', ondelete='cascade'),
		'enquiry_id':fields.many2one('kg.crm.enquiry', 'Enquiry'),
		'product_temp_id':fields.many2one('product.product', 'Product Name',domain = [('type','=','bot')], ondelete='cascade'),
		#~ 'bot_line_id':fields.many2one('ch.bot.details', 'Item Name'),
		'position_id': fields.many2one('kg.position.number','Position No.'),
		'bom_id': fields.many2one('kg.bom','BOM'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','bot')], ondelete='cascade',required=True),
		'item_name': fields.related('ms_id','name', type='char', size=128, string='Item Name', store=True, readonly=True),
		'code':fields.char('Item Code', size=128),	  
		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
		#'order_category': fields.related('header_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'remarks':fields.text('Remarks'),   
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'prime_cost': fields.float('Prime Cost'),
		'brand_id': fields.many2one('kg.brand.master','Brand '),
		'flag_is_bearing': fields.boolean('Is Bearing'),
		'purpose_categ': fields.selection([('pump','Pump'),('spare','Spare'),('access','Accessories')],'Purpose Category'),
		
	}
	
	_defaults = {
		
		'is_applicable': False,
		'load_bom': False,
		'flag_is_bearing': False,
		
	}
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_kg_crm_bot, self).write(cr, uid, ids, vals, context)
		
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False
		return True
	
	_constraints = [
	
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
ch_kg_crm_bot()

class ch_moc_construction(osv.osv):

	_name = "ch.moc.construction"
	_description = "MOC Construction Details"
	
	_columns = {
	
		
		'header_id':fields.many2one('ch.kg.crm.pumpmodel', 'Header Id', ondelete='cascade'),
		'moc_id':fields.many2one('kg.moc.master', 'MOC Name',domain = "[('state','not in',('raject','cancel'))]",required=True),
		'offer_id':fields.many2one('kg.offer.materials', 'Material Name',domain = "[('state','not in',('raject','cancel'))]",required=True),
		#~ 'pattern_id': fields.many2one('kg.pattern.master','Pattern No', required=True), 		
		#~ 'pattern_name': fields.char('Pattern Name'), 	
		'remarks':fields.text('Remarks'),   
		'flag_standard': fields.boolean('Non Standard'),
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		
		return context
		
	#~ def onchange_pattern_name(self, cr, uid, ids, pattern_id, context=None):
		#~ 
		#~ value = {'pattern_name': ''}
		#~ if pattern_id:
			#~ pro_rec = self.pool.get('kg.pattern.master').browse(cr, uid, pattern_id, context=context)
			#~ value = {'pattern_name': pro_rec.pattern_name}
			#~ 
		#~ return {'value': value}
		
		
	#~ def create(self, cr, uid, vals, context=None):
		#~ pattern_obj = self.pool.get('kg.pattern.master')
		#~ if vals.get('pattern_id'):		  
			#~ pattern_rec = pattern_obj.browse(cr, uid, vals.get('pattern_id') )
			#~ pattern_name = pattern_rec.pattern_name
			#~ vals.update({'pattern_name': pattern_name})
		#~ return super(ch_moc_construction, self).create(cr, uid, vals, context=context)
		#~ 
	#~ def write(self, cr, uid, ids, vals, context=None):
		#~ pattern_obj = self.pool.get('kg.pattern.master')
		#~ if vals.get('pattern_id'):
			#~ pattern_rec = pattern_obj.browse(cr, uid, vals.get('pattern_id') )
			#~ pattern_name = pattern_rec.pattern_name
			#~ vals.update({'pattern_name': pattern_name})		
		#~ return super(ch_moc_construction, self).write(cr, uid, ids, vals, context)  
	
ch_moc_construction()

class ch_kg_crm_accessories(osv.osv):

	_name = "ch.kg.crm.accessories"
	_description = "Ch KG CRM Accessories"
	
	#~ def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		#~ res = {}
		#~ prime_cost = fou_tot = ms_tot = bot_tot = 0.00
		#~ for order in self.browse(cr, uid, ids, context=context):
			#~ res[order.id] = {
				#~ 'prime_cost': 0.0,
			#~ }
#~ 
			#~ fou_tot = sum(line.prime_cost for line in order.line_ids)
			#~ ms_tot = sum(line.prime_cost for line in order.line_ids_a)
			#~ bot_tot = sum(line.prime_cost for line in order.line_ids_b)
			#~ prime_cost = fou_tot + ms_tot + bot_tot
			#~ res[order.id]['prime_cost'] = prime_cost
		#~ print"res[order.id]['prime_cost']res[order.id]['prime_cost']****************",res[order.id]['prime_cost']
		#~ return res
		
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('ch.kg.crm.pumpmodel', 'Header Id', ondelete='cascade'),
		
		## Module Requirement Fields
		
		'access_categ_id': fields.many2one('kg.accessories.category','Accessories Categ',domain="[('state','not in',('reject','cancel'))]"),
		'access_id': fields.many2one('kg.accessories.master','Accessories',domain="[('state','not in',('reject','cancel')),('access_cate_id','=',access_categ_id)]"),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('state','not in',('reject','cancel'))]"),
		'qty': fields.float('Qty'),
		'oth_spec': fields.char('Other Specification'),
		'load_access': fields.boolean('Load BOM'),
		#~ 'prime_cost': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Prime Cost',
			 #~ multi="sums", help="The amount without tax", track_visibility='always',store=True),
		'prime_cost': fields.float('Prime Cost'),
		
		## Child Tables Declaration
		
		'line_ids': fields.one2many('ch.crm.access.fou', 'header_id', 'Access FOU'),
		'line_ids_a': fields.one2many('ch.crm.access.ms', 'header_id', 'Access MS'),
		'line_ids_b': fields.one2many('ch.crm.access.bot', 'header_id', 'Access BOT'),
		
	}
	
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False
		return True
	
	_constraints = [
	
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
	
	def onchange_access_id(self, cr, uid, ids, access_categ_id,access_id):
		value = {'access_id':access_id}
		if access_categ_id:
			value = {'access_id':''}
		else:
			raise osv.except_osv(_('Warning!'),
				_('System should allow without accessories category!'))
		return {'value': value}
		
	def onchange_load_access(self,cr,uid,ids,load_access,access_id,moc_id,qty):
		fou_vals=[]
		ms_vals=[]
		bot_vals=[]
		data_rec = ''
		
		if load_access == True and access_id:
			access_obj = self.pool.get('kg.accessories.master').search(cr, uid, [('id','=',access_id)])
			if access_obj:
				data_rec = self.pool.get('kg.accessories.master').browse(cr, uid, access_obj[0])
		print"data_recdata_rec",data_rec
		if data_rec:
			if data_rec.line_ids_b:
				for item in data_rec.line_ids_b:
					fou_vals.append({
									'position_id': item.position_id.id,
									'pattern_id': item.pattern_id.id,
									'pattern_name': item.pattern_name,
									'moc_id': moc_id,
									'qty': item.qty * qty,
									'load_bom': True,
									'is_applicable': True,
									'csd_no': item.csd_no,
									'remarks': item.remarks,
									})
				print"fou_valsfou_vals",fou_vals
			if data_rec.line_ids_a:
				for item in data_rec.line_ids_a:	
					ms_vals.append({
									'name': item.name,
									'position_id': item.position_id.id,							
									'ms_id': item.ms_id.id,
									'moc_id': moc_id,
									'qty': item.qty * qty,
									'load_bom': True,
									'is_applicable': True,
									'csd_no': item.csd_no,
									'remarks': item.remarks,
									})
					print"ms_valsms_vals",ms_vals	
			if data_rec.line_ids:
				for item in data_rec.line_ids:	
					bot_vals.append({
									#~ 'product_id': item.product_id.id,
									#~ 'brand_id': item.brand_id.id,
									#~ 'uom_id': item.uom_id.id,
									#~ 'uom_conversation_factor': item.uom_conversation_factor,
									'name': item.item_name,
									'position_id': item.position_id.id,							
									'ms_id': item.ms_id.id,
									'moc_id': moc_id,
									'qty': item.qty * qty,
									'load_bom': True,
									'is_applicable': True,
									'csd_no': item.csd_no,
									'remarks': item.remark,
									})
					print"bot_valsbot_vals",bot_vals	
		return {'value': {'line_ids': fou_vals,'line_ids_a': ms_vals,'line_ids_b': bot_vals}}
		
		
ch_kg_crm_accessories()


class ch_crm_access_fou(osv.osv):

	_name = "ch.crm.access.fou"
	_description = "Child Foundry Item Details"
	
	_columns = {
	
		### Foundry Item Details ####
		'header_id':fields.many2one('ch.kg.crm.accessories', 'Access Id', ondelete='cascade'),
		'enquiry_id':fields.many2one('kg.crm.enquiry', 'Enquiry'),
		'pump_id':fields.many2one('kg.pumpmodel.master', 'Pump'),
		'qty':fields.integer('Quantity'),
		'oth_spec':fields.char('Other Specification'),
		'position_id': fields.many2one('kg.position.number','Position No.'),
		'csd_no': fields.char('CSD No.', size=128),
		'pattern_name': fields.char('Pattern Name'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No.'),
		'remarks': fields.char('Remarks'),
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'prime_cost': fields.float('Prime Cost'),
		
	}
	
ch_crm_access_fou()

class ch_crm_access_ms(osv.osv):

	_name = "ch.crm.access.ms"
	_description = "ch crm Access MS"
	
	_columns = {
	
		### machineshop Item Details ####
		'header_id':fields.many2one('ch.kg.crm.accessories', 'Access Id', ondelete='cascade'),
		'enquiry_id':fields.many2one('kg.crm.enquiry', 'Enquiry'),
		'pos_no': fields.related('position_id','name', type='char', string='Position No.', store=True),
		'position_id': fields.many2one('kg.position.number','Position No.'),
		'csd_no': fields.char('CSD No.'),
		'bom_id': fields.many2one('kg.bom','BOM'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','ms')], ondelete='cascade',required=True),
		'name': fields.related('ms_id','name', type='char',size=128,string='Item Name', store=True),
		'name':fields.char('Item Name', size=128),	  
		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
		'remarks':fields.text('Remarks'),   
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'prime_cost': fields.float('Prime Cost'),
		
	}
	
	_defaults = {
		
		'is_applicable':False,
		'load_bom':False,
		
	}
	
ch_crm_access_ms()

class ch_crm_access_bot(osv.osv):

	_name = "ch.crm.access.bot"
	_description = "Ch Crm Access BOT"
	
	_columns = {
	
		### machineshop Item Details ####
		'header_id':fields.many2one('ch.kg.crm.accessories', 'Access Id', ondelete='cascade'),
		'enquiry_id':fields.many2one('kg.crm.enquiry', 'Enquiry'),
		#~ 'product_id':fields.many2one('product.product', 'Item Name',domain="[('state','not in',('reject','cancel'))]"),
		#~ 'brand_id': fields.many2one('kg.brand.master','Brand', domain="[('state','not in',('reject','cancel'))]"), 
		#~ 'uom_id': fields.many2one('product.uom','UOM'),		
		#~ 'uom_conversation_factor': fields.selection([('one_dimension','One Dimension'),('two_dimension','Two Dimension')],'UOM Conversation Factor'),
		'position_id': fields.many2one('kg.position.number','Position No.'),
		'csd_no': fields.char('CSD No.'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','bot')], ondelete='cascade',required=True),
		'name': fields.related('ms_id','name', type='char',size=128,string='Item Name', store=True),
		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
		'remarks':fields.text('Remarks'),   
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'prime_cost': fields.float('Prime Cost'),
		'brand_id': fields.many2one('kg.brand.master','Brand'),
		
	}
	
ch_crm_access_bot()
