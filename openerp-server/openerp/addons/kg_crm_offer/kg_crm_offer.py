from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import base64
from itertools import groupby


from PIL import Image

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

CALL_TYPE_SELECTION = [
    ('service','Service'),
    ('new_enquiry','New Enquiry')
]
PURPOSE_SELECTION = [
    ('pump','Pump'),('spare','Spare'),('prj','Project'),('pump_spare','Pump With Spare')
]
STATE_SELECTION = [
    ('draft','Draft'),('moved_to_offer','Moved To Offer'),('call','Call Back'),('quote','Quote Process'),('wo_created','WO Created'),('wo_released','WO Released'),('reject','Rejected'),('revised','Revised')
]
MARKET_SELECTION = [
	('cp','CP'),('ip','IP')
]

class kg_crm_offer(osv.osv):
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		pump_net_amount = spare_net_amount = access_net_amount = offer_net_amount = 0.00
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'pump_net_amount': 0.0,
				'spare_net_amount': 0.0,
				'access_net_amount': 0.0,
				'offer_net_amount': 0.0,
			
			}
			
			cur = order.customer_id.property_product_pricelist_purchase.currency_id
			
			for line in order.line_pump_ids:
				pump_net_amount += line.net_amount
				print"pump_net_amount",pump_net_amount	
				
			for line in order.line_spare_ids:
				spare_net_amount += line.net_amount
				print"spare_net_amount",spare_net_amount	
				
			for line in order.line_accessories_ids:
				access_net_amount += line.net_amount
				print"access_net_amount",access_net_amount	
				
			res[order.id]['pump_net_amount'] = pump_net_amount
			res[order.id]['spare_net_amount'] = spare_net_amount
			res[order.id]['access_net_amount'] = access_net_amount
			res[order.id]['offer_net_amount'] = pump_net_amount + spare_net_amount + access_net_amount
			
		return res
		
	_name = "kg.crm.offer"
	_description = "CRM Offer Entry"
	_order = "enquiry_date desc"

	_columns = {
	
		### Header Details ####
		'name': fields.char('Offer No', size=128,select=True),
		'enquiry_id': fields.many2one('kg.crm.enquiry','Enquiry No.'),
		'schedule_no': fields.char('Schedule No', size=128,select=True),
		'enquiry_date': fields.date('Enquiry Date',required=True),
		'offer_date': fields.date('Offer Date',required=True),
		'note': fields.char('Notes'),
		'service_det': fields.char('Service Details'),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection(STATE_SELECTION,'Status', readonly=True),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD'),('export','Export')],'Location'),
		'offer_copy': fields.char('Offer Copy'),
		'revision': fields.integer('Revision'),
		'wo_flag': fields.boolean('WO Flag'),
		
		'line_pump_ids': fields.one2many('ch.pump.offer', 'header_id', "Pump Offer"),
		'line_spare_ids': fields.one2many('ch.spare.offer', 'header_id', "Spare Offer"),
		'line_accessories_ids': fields.one2many('ch.accessories.offer', 'header_id', "Accessories Offer"),
		
		#~ 'ch_line_ids': fields.one2many('ch.kg.crm.pumpmodel', 'header_id', "Pump/Spare Details"),
		'due_date': fields.date('Due Date',required=True),
		'call_type': fields.selection(CALL_TYPE_SELECTION,'Call Type', required=True),
		'ref_mode': fields.selection([('direct','Direct'),('dealer','Dealer')],'Reference Mode', required=True),
		'market_division': fields.selection(MARKET_SELECTION,'Marketing Division', required=True),
		'ref_no': fields.char('Reference Number'),
		'segment': fields.selection([('dom','Domestic'),('exp','Export')],'Segment', required=True),
		'customer_id': fields.many2one('res.partner','Customer Name',domain=[('customer','=',True),('contact','=',False)]),
		'dealer_id': fields.many2one('res.partner','Dealer Name',domain=[('dealer','=',True),('contact','=',False)]),
		'industry_id': fields.many2one('kg.industry.master','Sector'),
		'expected_value': fields.float('Expected Value'),
		'del_date': fields.date('Expected Del Date'),
		'purpose': fields.selection(PURPOSE_SELECTION,'Purpose'),
		'chemical_id': fields.many2one('kg.chemical.master','Chemical',domain=[('purpose','=','general')]),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Name'),
		's_no': fields.char('Serial Number'),
		'wo_no': fields.char('WO Number'),
		'requirements': fields.text('Requirements'),
		
		'enquiry_no': fields.char('Enquiry No.', size=128,select=True),
		'scope_of_supply': fields.selection([('bare_pump','Bare Pump'),('pump_with_acces','Pump With Accessories'),('pump_with_acces_motor','Pump With Accessories And Motor')],'Scope of Supply'),
		'pump': fields.selection([('gld_packing','Gland Packing'),('mc_seal','M/C Seal'),('dynamic_seal','Dynamic seal')],'Shaft Sealing', required=True),
		'drive': fields.selection([('motor','Motor'),('vfd','VFD'),('engine','Engine')],'Drive'),
		'transmision': fields.selection([('cpl','Coupling'),('belt','Belt Drive'),('fc','Fluid Coupling'),('gear_box','Gear Box'),('fc_gear_box','Fluid Coupling With Gear Box')],'Transmision', required=True),
		'acces': fields.selection([('yes','Yes'),('no','No')],'Accessories'),
		
		# Pump Offer Fields
		'pump_tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Price',multi="sums",store=True),	
		'pump_sam_ratio': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Sam Ratio',multi="sums",store=True),	
		'pump_dealer_discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),	
		'pump_customer_discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),	
		'pump_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax',multi="sums",store=True),	
		'pump_p_f': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F',multi="sums",store=True),	
		'pump_freight': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),	
		'pump_insurance': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),	
		'pump_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),	
		
		# Spare Offer Fields
		'spare_tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Price',multi="sums",store=True),	
		'spare_sam_ratio': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Sam Ratio',multi="sums",store=True),	
		'spare_dealer_discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),	
		'spare_customer_discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),	
		'spare_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax',multi="sums",store=True),	
		'spare_p_f': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F',multi="sums",store=True),	
		'spare_freight': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),	
		'spare_insurance': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),	
		'spare_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),	
		
		# Accessories Offer Fields
		'access_tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Price',multi="sums",store=True),	
		'access_sam_ratio': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Sam Ratio',multi="sums",store=True),	
		'access_dealer_discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),	
		'access_customer_discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),	
		'access_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax',multi="sums",store=True),	
		'access_p_f': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F',multi="sums",store=True),	
		'access_freight': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),	
		'access_insurance': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),	
		'access_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),	
		
		'offer_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Offer Amount',multi="sums",store=True),
		
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
		
		# Offer Copy 
		
		'rep_data':fields.binary("Offer Copy",readonly=True),
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_crm_offer', context=c),
		'enquiry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'offer_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',
		'pump': 'gld_packing',
		'transmision': 'cpl',
		'ref_mode': 'direct',
		'call_type': 'new_enquiry',
		'active': True,
		'wo_flag': False,
	#	'division_id':_get_default_division,
		'due_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'revision': 0,
	}
	
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
		return super(kg_crm_offer, self).write(cr, uid, ids, vals, context)
	
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		
		#~ for line in entry.line_pump_ids:
		if not entry.name:
			off_no = ''	
			seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.crm.offer')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],rec.code,entry.offer_date))
			off_no = cr.fetchone();
			off_no = off_no[0]
		else:
			off_no = entry.name
		#~ self.wo_creation(cr,uid,entry)
		
		self.write(cr, uid, ids, {
									'name':off_no,
									'state': 'moved_to_offer',
									'confirm_user_id': uid, 
									'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')
								})
		return True
	
	def entry_revision(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		revision = 0
		if entry.wo_flag == False:
			revision = entry.revision + 1
			print"revisionrevisionrevision",revision
			vals = {
					'state' : 'draft',
					'revision' : revision,
					}
			offer_id = self.copy(cr, uid, entry.id,vals, context) 
			print"offer_idoffer_idoffer_id",offer_id
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
	
	def wo_creation(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		wo_id = self.pool.get('kg.work.order').create(cr,uid,{'order_category': entry.purpose,
															  'name': '',
															  'offer_no': entry.name,
															  'location': entry.location,
															  'entry_mode': 'auto',
															  'partner_id': entry.customer_id.id,
																})
		if wo_id:
			if entry.line_pump_ids:
				groups = []
				#~ for item in entry.line_spare_ids:
				for key, group in groupby(entry.line_pump_ids, lambda x: x.enquiry_line_id.id):
					groups.append(map(lambda r:r,group))
				print"ffffffffffffffffffff",groups
				for key,group in enumerate(groups):
					enquiry_line_id = group[0].enquiry_line_id.id
					off_line_id = group[0]
					print"enquiry_line_idenquiry_line_id",enquiry_line_id
					print"off_line_idoff_line_id",off_line_id
					purpose = 'pump'
					pump_vals = self._prepare_pump_details(cr,uid,wo_id,entry,enquiry_line_id,off_line_id,purpose)
					if pump_vals:
						wo_line_id = self.pool.get('ch.work.order.details').create(cr, uid, pump_vals, context=context)
						if wo_line_id:
							item = self.pool.get('ch.kg.crm.pumpmodel').browse(cr,uid,enquiry_line_id)
							if item:
								self.prepare_bom(cr,uid,wo_line_id,item,off_line_id,purpose,context=context)
			if entry.line_spare_ids:
				groups = []
				#~ for item in entry.line_spare_ids:
				for key, group in groupby(entry.line_spare_ids, lambda x: x.pump_id.id):
					groups.append(map(lambda r:r,group))
				print"ffffffffffffffffffff",groups
				for key,group in enumerate(groups):
					enquiry_line_id = group[0].enquiry_line_id.id
					off_line_id = group[0]
					spa_off_obj = self.pool.get('ch.spare.offer').search(cr,uid,[('enquiry_line_id','=',enquiry_line_id)])
					print"spa_off_obj",spa_off_obj
					print"enquiry_line_idenquiry_line_id*************************",enquiry_line_id
					print"enquiry_line_idenquiry_line_id********off_line_id*****************",off_line_id
					purpose = 'spare'
					pump_vals = self._prepare_pump_details(cr,uid,wo_id,entry,enquiry_line_id,off_line_id,purpose)
					if pump_vals:
						wo_line_id = self.pool.get('ch.work.order.details').create(cr, uid, pump_vals, context=context)
						if wo_line_id:
							item = self.pool.get('ch.kg.crm.pumpmodel').browse(cr,uid,enquiry_line_id)
							if item:
								for li in spa_off_obj:
									print"liliii",li
									off_line_id = spa_off_obj
								self.prepare_bom(cr,uid,wo_line_id,item,off_line_id,purpose,context=context)
			
			if entry.line_accessories_ids:
				groups = []
				for key, group in groupby(entry.line_accessories_ids, lambda x: x.pump_id.id):
					groups.append(map(lambda r:r,group))
				print"ffffffffffffffffffff",groups
				for key,group in enumerate(groups):
					enquiry_line_id = group[0].enquiry_line_id.id
					off_line_id = group[0]
					acc_off_obj = self.pool.get('ch.accessories.offer').search(cr,uid,[('enquiry_line_id','=',enquiry_line_id)])
					print"enquiry_line_idenquiry_line_id",enquiry_line_id
					purpose = 'access'
					pump_vals = self._prepare_pump_details(cr,uid,wo_id,entry,enquiry_line_id,off_line_id,purpose)
					if pump_vals:
						wo_line_id = self.pool.get('ch.work.order.details').create(cr, uid, pump_vals, context=context)
						if wo_line_id:
							item = self.pool.get('ch.kg.crm.pumpmodel').browse(cr,uid,enquiry_line_id)
							if item:
								for li in acc_off_obj:
									print"liliii",li
									off_line_id = acc_off_obj
								self.prepare_bom(cr,uid,wo_line_id,item,off_line_id,purpose,context=context)
					
		print"wo_idwo_idwo_id",wo_id
		if wo_id:
			self.write(cr, uid, ids, {'wo_flag': True,'state':'wo_created'})
			self.pool.get('kg.crm.enquiry').write(cr,uid,entry.enquiry_id.id,{'wo_flag':True,'state':'wo_created'})
		return True
	
	#~ def _prepare_pump_details(self,cr,uid,wo_id,entry,item,context=None):		
		#~ print"item.pump_iditem.pump_id.name",item.pump_id.name
		#~ pump_vals = {
			#~ 
			#~ 'header_id': wo_id,
			#~ 'pump_model_id': item.pump_id.id,
			#~ 'order_category': 'pump',
			#~ 'moc_construction_id': item.moc_const_id.id,
			#~ 'unit_price': item.net_amount,
			#~ 'qty': item.qty,
			#~ 'flag_load_bom': True,
			#~ }			
			#~ 
		#~ return pump_vals
			
	def _prepare_pump_details(self,cr,uid,wo_id,entry,enquiry_line_id,off_line_id,purpose,context=None):	
		print"iteiteitieiteitieit",enquiry_line_id
		item = self.pool.get('ch.kg.crm.pumpmodel').browse(cr,uid,enquiry_line_id)
		#~ purpose = item.purpose_categ
		qty = 1
		moc_const_id = m_power = setting_height = 0
		pump_model_type = speed_in_rpm = bush_bearing = shaft_sealing = lubrication_type = rpm = ''
		if purpose == 'pump':
			qty = item.qty
			moc_const_id = item.moc_const_id.id
			pump_id = item.pump_id.id
			pump_model_type = item.pump_model_type
			speed_in_rpm = item.speed_in_rpm
			if item.push_bearing == 'grease_bronze':
				 bush_bearing = 'grease'
			elif item.push_bearing == 'cft':
				 bush_bearing = 'cft_self'
			elif item.push_bearing == 'cut':
				 bush_bearing = 'cut_less_rubber'
			m_power = item.mototr_output_power_rated
			setting_height = float(item.setting_height)
			if item.shaft_sealing == 'gld_packing_tiga':
				 shaft_sealing = 'g_p'
			elif item.shaft_sealing == 'mc_seal':
				 shaft_sealing = 'm_s'
			elif item.shaft_sealing == 'dynamic_seal':
				 shaft_sealing = 'f_s'
			if item.lubrication_type == 'grease':
				 lubrication_type = 'grease'
			if item.speed_in_rpm:
				if item.speed_in_rpm <= 1800  or item.speed_in_rpm == 0.00:
					rpm = '1450'
				elif item.speed_in_rpm >= 1801 and item.speed_in_rpm <= 3600:
					rpm = '2900'
		elif purpose == 'spare':
			purpose == 'spare'
			moc_const_id = item.spare_moc_const_id.id
			pump_id = item.spare_pump_id.id
		elif purpose == 'access':
			purpose == 'access'
			if item.purpose_categ == 'pump':
				moc_const_id = item.moc_const_id.id
				pump_id = item.pump_id.id
			elif item.purpose_categ in ('spare','access'):
				moc_const_id = item.spare_moc_const_id.id
				pump_id = item.spare_pump_id.id
		pump_vals = {
			
			'header_id': wo_id,
			'pump_model_id': item.spare_pump_id.id,
			'order_category': purpose,
			'moc_construction_id': moc_const_id,
			'unit_price': 1,
			'qty': qty,
			'flag_load_bom': True,
			'delivery_date': item.header_id.del_date,
			'pump_offer_line_id': off_line_id,
			'pump_model_type': pump_model_type,
			'rpm': speed_in_rpm,
			'bush_bearing': bush_bearing,
			'm_power': m_power,
			'setting_height': setting_height,
			'shaft_sealing': shaft_sealing,
			'lubrication_type': lubrication_type,
			'rpm': rpm,
			
			}
			
		return pump_vals
			
	def prepare_bom(self,cr,uid,wo_line_id,item,off_line_id,purpose,context=None):	
		prime_cost = 0
		if purpose in ('pump','spare'):
			if item.purpose_categ in ('pump','spare'):
				arr = of_li_id = 0
				if item.line_ids:
					#~ spa_off_obj = self.pool.get('ch.spare.offer').search(cr,uid,[('enquiry_line_id','=',enquiry_line_id)])
					#~ print"spa_off_obj",spa_off_obj
					print"off_line_idoff_line_idoff_line_idoff_line_idoff_line_id",off_line_id
					for ele in item.line_ids:
						if ele.is_applicable == True:
							if purpose == 'spare':
								of_li_id = off_line_id[arr]
								print"of_li_id",of_li_id
							print"ele.position_id.idele.position_id.id",ele.position_id.name
							fou_line = self.pool.get('ch.order.bom.details').create(cr,uid,{'header_id': wo_line_id,
																							'flag_applicable': True,
																							'flag_standard': True,
																							'qty': ele.qty,
																							'position_id': ele.position_id.id,
																							'pattern_id': ele.pattern_id.id,
																							'pattern_name': ele.pattern_name,
																							'unit_price': ele.prime_cost,
																							'moc_id': ele.moc_id.id,
																							'entry_mode': 'auto',
																							'spare_offer_line_id': of_li_id,
																							})
							prime_cost += ele.prime_cost
							print"aaaaaaaaaaaaa",prime_cost
							arr = arr+1
						else:
							if purpose == 'spare':
								of_li_id = 0
				if item.line_ids_a:
					for ele in item.line_ids_a:
						if ele.is_applicable == True:
							if purpose == 'spare':
								of_li_id = off_line_id[arr]
								print"of_li_id",of_li_id
							ms_line = self.pool.get('ch.order.machineshop.details').create(cr,uid,{'header_id': wo_line_id,
																							'flag_applicable': True,
																							'flag_standard': True,
																							'qty': ele.qty,
																							'position_id': ele.position_id.id,
																							'ms_id': ele.ms_id.id,
																							'unit_price': ele.prime_cost,
																							'moc_id': ele.moc_id.id,
																							'entry_mode': 'auto',
																							'spare_offer_line_id': of_li_id,
																							})
							prime_cost += ele.prime_cost
							print"bbbbbbbbbbbbbb",prime_cost
							arr = arr+1
						else:
							if purpose == 'spare':
								of_li_id = 0
				if item.line_ids_b:
					for ele in item.line_ids_b:
						if ele.is_applicable == True:
							if purpose == 'spare':
								of_li_id = off_line_id[arr]
								print"of_li_id",of_li_id
							bot_line = self.pool.get('ch.order.bot.details').create(cr,uid,{'header_id': wo_line_id,
																							'flag_applicable': True,
																							'flag_standard': True,
																							'qty': ele.qty,
																							'position_id': ele.position_id.id,
																							'bot_id': ele.ms_id.id,
																							'unit_price': ele.prime_cost,
																							'moc_id': ele.moc_id.id,
																							'entry_mode': 'auto',
																							'spare_offer_line_id': of_li_id,
																							})
							prime_cost += ele.prime_cost
							print"ccccccccccccccccc",prime_cost
							arr = arr+1
						else:
							if purpose == 'spare':
								of_li_id = 0
				prime_cost = 0.00
				if item.purpose_categ == 'pump':
					self.pool.get('ch.work.order.details').write(cr,uid,wo_line_id,{'unit_price':off_line_id.net_amount})
				elif item.purpose_categ == 'spare':
					off_spare_obj = self.pool.get('ch.spare.offer').search(cr,uid,[('enquiry_line_id','=',item.id),('pump_id','=',item.spare_pump_id.id)])
					if off_spare_obj:
						print"off_spare_obj",off_spare_obj
						for line in off_spare_obj:
							print"linelelelelelle",line
							off_spare_rec = self.pool.get('ch.spare.offer').browse(cr,uid,line)
							prime_cost += off_spare_rec.net_amount
						self.pool.get('ch.work.order.details').write(cr,uid,wo_line_id,{'unit_price':prime_cost})
		if purpose == 'access':
			prime_cost = 0
			print"ddddddddddddddddddddddddddddD",prime_cost
			if item.acces == 'yes':
				arr = of_li_id = 0
				if item.line_ids_access_a:
					for line in item.line_ids_access_a:
						of_li_id = off_line_id[arr]
						print"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",of_li_id
						wo_access_id = self.pool.get('ch.wo.accessories').create(cr,uid,{'header_id':wo_line_id,
																						 'access_id':line.access_id.id,
																						 'moc_id':line.moc_id.id,
																						 'qty':line.qty,
																						 'load_access':line.load_access,
																						 'access_offer_line_id': of_li_id,
																						})
						arr = arr+1
						if wo_access_id:
							if line.line_ids:
								for ele in line.line_ids:
									if ele.is_applicable == True:
										fou_line = self.pool.get('ch.wo.accessories.foundry').create(cr,uid,{'header_id': wo_access_id,
																										'is_applicable': True,
																										'qty': ele.qty,
																										'position_id': ele.position_id.id,
																										'pattern_id': ele.pattern_id.id,
																										'prime_cost': ele.prime_cost,
																										'moc_id': ele.moc_id.id,
																										#~ 'access_offer_line_id': off_line_id,
																										})
										prime_cost += ele.prime_cost
							if line.line_ids_a:
								for ele in line.line_ids_a:
									if ele.is_applicable == True:
										fou_line = self.pool.get('ch.wo.accessories.ms').create(cr,uid,{'header_id': wo_access_id,
																										'is_applicable': True,
																										'qty': ele.qty,
																										'position_id': ele.position_id.id,
																										'ms_id': ele.ms_id.id,
																										'prime_cost': ele.prime_cost,
																										'moc_id': ele.moc_id.id,
																										#~ 'access_offer_line_id': off_line_id,
																										})
										prime_cost += ele.prime_cost
							if line.line_ids_b:
								for ele in line.line_ids_b:
									if ele.is_applicable == True:
										fou_line = self.pool.get('ch.wo.accessories.bot').create(cr,uid,{'header_id': wo_access_id,
																										'is_applicable': True,
																										'qty': ele.qty,
																										'position_id': ele.position_id.id,
																										'csd_no': ele.csd_no,
																										'ms_id': ele.ms_id.id,
																										'prime_cost': ele.prime_cost,
																										'moc_id': ele.moc_id.id,
																										#~ 'access_offer_line_id': off_line_id,
																										})
										prime_cost += ele.prime_cost
							prime_cost = 0.00
							off_access_obj = self.pool.get('ch.accessories.offer').search(cr,uid,[('enquiry_line_id','=',item.id),('pump_id','=',item.pump_id.id)])
							if off_access_obj:
								print"off_access_obj",off_access_obj
								for line in off_access_obj:
									print"linelelelelelle",line
									off_access_rec = self.pool.get('ch.accessories.offer').browse(cr,uid,line)
									prime_cost += off_access_rec.net_amount
								print"*************************************************",prime_cost
								self.pool.get('ch.work.order.details').write(cr,uid,wo_line_id,{'unit_price':prime_cost})
						
		print"prime_costprime_cost",prime_cost
		return True
			
	def offer_copy(self,cr,uid,ids,context=None):
		import StringIO
		import base64
		
		try:
			import xlwt
		except:
		   raise osv.except_osv('Warning !','Please download python xlwt module from\nhttp://pypi.python.org/packages/source/x/xlwt/xlwt-0.7.2.tar.gz\nand install it')
		   
		rec =self.browse(cr,uid,ids[0])
		print"recrec",rec
		
		#######
		line_sql = """
			(select pump.pump_id
			from ch_pump_offer pump
			left join kg_pumpmodel_master pmm on(pmm.id=pump.pump_id)
			where header_id = """+ str(rec.id) +""" order by pump.pump_id)
			union 
			(select pump.pump_id
			from ch_spare_offer pump
			left join kg_pumpmodel_master pmm on(pmm.id=pump.pump_id)
			where header_id = """+ str(rec.id) +""" order by pump.pump_id)
			union 
			(select pump.pump_id
			from ch_accessories_offer pump
			left join kg_pumpmodel_master pmm on(pmm.id=pump.pump_id)
			where header_id = """+ str(rec.id) +""" order by pump.pump_id)

			"""
		cr.execute(line_sql)		
		line_data = cr.dictfetchall()
		print"line_dataline_data",line_data
		enq_line_data = []
		enq_line_data = line_data
		for item in line_data:
			pump_off_obj = self.pool.get('ch.pump.offer').search(cr,uid,[('header_id','=',rec.id),('pump_id','=',item['pump_id'])])
			
			if pump_off_obj:
				off_pump_line_rec = self.pool.get('ch.pump.offer').browse(cr,uid,pump_off_obj[0])
				pump_enq_line_id = off_pump_line_rec.enquiry_line_id.id
				item['enquiry_line_id'] = pump_enq_line_id
				item['name'] = off_pump_line_rec.pump_id.name
				item['id'] = off_pump_line_rec.id
				print"item['enquiry_line_id']",item['enquiry_line_id']
			spare_off_obj = self.pool.get('ch.spare.offer').search(cr,uid,[('header_id','=',rec.id),('pump_id','=',item['pump_id'])])
			if spare_off_obj:
				spare_pump_line_rec = self.pool.get('ch.spare.offer').browse(cr,uid,spare_off_obj[0])
				spr_enq_line_id = spare_pump_line_rec.enquiry_line_id.id
				item['enquiry_line_id'] = spr_enq_line_id
				print"item['enquiry_line_id']",item['enquiry_line_id']
				item['name'] = spare_pump_line_rec.pump_id.name
				item['id'] = spare_pump_line_rec.id
			access_off_obj = self.pool.get('ch.accessories.offer').search(cr,uid,[('header_id','=',rec.id),('pump_id','=',item['pump_id'])])
			if access_off_obj:
				access_pump_line_rec = self.pool.get('ch.accessories.offer').browse(cr,uid,access_off_obj[0])
				acc_enq_line_id = access_pump_line_rec.enquiry_line_id.id
				item['enquiry_line_id'] = acc_enq_line_id
				print"item['enquiry_line_id']",item['enquiry_line_id']
				item['name'] = access_pump_line_rec.pump_id.name
				item['id'] = access_pump_line_rec.id
		
		print"line_data",line_data
		
		print"line_dataline_data",len(line_data)
		
		len_col = 0
		if line_data:
			if len(line_data):
				if len(line_data) <= 1:
					len_col = len(line_data) 
				elif len(line_data) <= 3 or len(line_data) > 3:
					len_col = len(line_data)
		print"len_collen_collen_col",len_col
		
		line_data.sort(key=lambda line_data: line_data['pump_id'])
		record={}
		sno=0
		wbk = xlwt.Workbook()
		style1 = xlwt.easyxf('font: bold on,height 240,color_index red;' 'align: horiz center;''borders: left thin, right thin, top thin, bottom thin') 
		style2 = xlwt.easyxf('font: bold on,height 240,color_index black;' 'align: horiz center;''borders: left thin, right thin, top thin, bottom thin') 
		style3 = xlwt.easyxf('font: height 200,color_index black;' 'align: horiz center;''borders: left thin, right thin, top thin, bottom thin') 
		style4 = xlwt.easyxf('font: height 200,color_index black;' 'align: horiz left;''borders: left thin, right thin, top thin, bottom thin') 
		style5 = xlwt.easyxf('font: bold on,height 200,color_index black;' 'align: horiz left;''borders: left thin, right thin, top thin, bottom thin;''font: underline on;') 
		style6 = xlwt.easyxf('font: height 200,color_index black;' 'align: vert centre, horiz left;''borders: left thin, right thin, top thin, bottom thin') 
		style7 = xlwt.easyxf('font: height 200,color_index black;' 'align: wrap on, vert centre, horiz left;''borders: left thin, right thin, top thin, bottom thin') 
		style8 = xlwt.easyxf('font: height 200,color_index black;' 'align: wrap on, vert centre, horiz centre;''borders: left thin, right thin, top thin, bottom thin') 
		
		
		img = Image.open('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_crm_offer/img/sam.png')
		r, g, b, a = img.split()
		img = Image.merge("RGB", (r, g, b))
		img.save('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_crm_offer/img/sam.bmp')
		img = Image.open('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_crm_offer/img/TUV_NORD.png')
		img.save('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_crm_offer/img/TUV_NORD.bmp')
		
		#~ r, g, b, a = img.split()
		#~ img = Image.merge("RGB", (r, g, b))
		s1=7
		
		"""adding a worksheet along with name"""
		
		sheet1 = wbk.add_sheet('Offer Copy')
		
		s2=8
		if line_data:
			if len_col <= 1:
				sheet1.col(0).width = 8000
				sheet1.col(1).width = 12000
			elif len_col <= 2:
				sheet1.col(0).width = 8000
				sheet1.col(1).width = 7000
				sheet1.col(2).width = 7000
			elif len_col >= 3:
				sheet1.col(0).width = 8000
				sheet1.col(1).width = 7000
				sheet1.col(2).width = 7000
				sheet1.col(3).width = 7000
		else:
			sheet1.col(0).width = 8000
			sheet1.col(1).width = 5000
			sheet1.col(2).width = 5000
		sheet1.col(len_col+1).width = 5000
		sheet1.col(len_col+2).width = 5000
		sheet1.col(len_col+3).width = 5000
		sheet1.col(len_col+4).width = 5000
		sheet1.col(len_col+5).width = 5000
		sheet1.col(len_col+6).width = 5000
		sheet1.col(len_col+7).width = 5000
		
		sheet1.write_merge(0, 0, 0, len_col,"SAM TURBO INDUSTRY PRIVATE LIMITED",style2)
		sheet1.row(0).height = 450
		sheet1.write_merge(1, 1, 0, len_col,"Avinashi Road, Neelambur, Coimbatore - 641062",style3)
		sheet1.write_merge(2, 2, 0, len_col,"Tel:3053555, 3053556,Fax : 0422-3053535",style3)
		sheet1.write_merge(3, 3, 0, len_col,"TECHNICAL CUM PRICED OFFER",style2)
		sheet1.row(3).height = 300
		to = "To : " + str(rec.customer_id.name)
		sheet1.write_merge(4, 4, 0, 0, to, style4)
		enq_ref = "Enquiry Ref : " + str(rec.enquiry_no)
		sheet1.write_merge(4, 4, 1, len_col, enq_ref, style4)
		sheet1.row(4).height = 450
		off_ref_no = "Offer Ref : " + str(rec.name)
		sheet1.write_merge(5, 5, 0, 0, off_ref_no or "-", style4)
		offer_date = rec.offer_date
		offer_date = datetime.strptime(offer_date, '%Y-%m-%d').strftime('%d/%m/%Y')
		date = "Date : " + offer_date
		sheet1.write_merge(5, 5, 1, len_col, date, style4)
		sheet1.row(5).height = 400
		sheet1.write_merge(6, 6, 0, len_col, 'Item Details:', style5)
		sheet1.row(6).height = 400
		sheet1.write_merge(7, 7, 0, 0, 'Application', style4)
		sheet1.write_merge(7, 7, 1, len_col, 'List Of Horizontal Centrifugal pump for Heavy Water Upgradation Plant', style6)
		sheet1.write_merge(13, 13, 0, len_col, 'Liquid details given by the customer:', style5)
		sheet1.row(13).height = 400
		sheet1.write_merge(25, 25, 0, len_col, 'Pump Specification:', style5)
		sheet1.row(25).height = 400
		sheet1.write_merge(73, 73, 0, len_col, 'Material of construction:', style5)
		sheet1.row(43).height = 400
		########
		
		col_1 = ''
		col_no = 1
		logo_size = 0
		for item in line_data:
			""" writing field headings """
			col_1 = item['name']
			
			if len_col == 1:
				logo_size = 250
			elif len_col <= 3:
				logo_size = 120
			elif len_col >= 4:
				logo_size = 100
			sheet1.insert_bitmap('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_crm_offer/img/sam.bmp',0,0)
			sheet1.insert_bitmap('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_crm_offer/img/TUV_NORD.bmp',0,len_col,logo_size)
			#~ print"col_1",col_1
			#~ sheet1.write(s1,col_no,str(col_1),style1)
			col_no = col_no + 1

		"""writing data according to query and filteration in worksheet"""
		
		sheet1.write(s2,0,"Sr.No",style6)
		sheet1.write(s2+1,0,"Tag No",style6)
		sheet1.write(s2+2,0,"Description",style6)
		sheet1.write(s2+3,0,"Quantity in nos",style6)
		sheet1.write(s2+4,0,"Previous Supply Reference",style6)
		sheet1.write(s2+6,0,"Liquid",style6)
		sheet1.write(s2+7,0,"Temperature in C",style6)
		sheet1.write(s2+8,0,"Solid Concentration in %",style6)
		sheet1.write(s2+9,0,"Consistency In %",style6)
		sheet1.write(s2+10,0,"Specific Gravity",style6)
		sheet1.write(s2+11,0,"Density(kg/m3)",style6)
		sheet1.write(s2+12,0,"Viscosity in CST",style6)
		sheet1.write(s2+13,0,"Max Particle Size-mm",style6)
		sheet1.write(s2+14,0,"NPSH-AVL",style6)
		sheet1.write(s2+15,0,"Capacity in M3/hr(Liquid)",style6)
		sheet1.write(s2+16,0,"Total Head in Mlc(Liquid)",style6)
		sheet1.write(s2+18,0,"Pump Type",style6)
		sheet1.row(s2+18).height = 490
		sheet1.write(s2+19,0,"Pump Model",style6)
		#~ sheet1.write(s2+20,0,"Pumpseries",style6)
		#~ sheet1.write(s2+21,0,"Previous Supply Reference",style6)
		sheet1.write(s2+20,0,"Shaft Sealing",style6)
		sheet1.write(s2+21,0,"Scope of Supply",style6)
		sheet1.write(s2+22,0,"Number of stages",style6)
		sheet1.write(s2+23,0,"Impeller Type",style6)
		sheet1.write(s2+24,0,"Impeller Dia Min mm",style6)
		sheet1.write(s2+25,0,"Size-SuctionX Delivery(mm)",style6)
		#~ sheet1.write(s2+26,0,"Flange Type",style6)
		sheet1.write(s2+26,0,"Flange Standard",style6)
		sheet1.write(s2+27,0,"Efficiency in % Wat",style6)
		sheet1.write(s2+28,0,"NPSH R - M",style6)
		sheet1.write(s2+29,0,"Best Efficiency NPSH in M",style6)
		sheet1.write(s2+30,0,"BKW Water",style6)
		sheet1.write(s2+31,0,"BKW Liq",style6)
		sheet1.write(s2+32,0,"Impeller Dia Rated mm",style6)
		sheet1.write(s2+33,0,"Impeller Tip Speed -M/Sec",style6)
		sheet1.write(s2+34,0,"Hydrostatic Test Pressure - Kg/cm2",style6)
		sheet1.write(s2+35,0,"Setting Height",style6)
		sheet1.write(s2+36,0,"Speed in RPM",style6)
		sheet1.write(s2+37,0,"Motor frequency (HZ)",style6)
		sheet1.write(s2+38,0,"Motor KW",style6)
		sheet1.write(s2+39,0,"Motor Margin(%)",style6)
		sheet1.write(s2+40,0,"Speed in RPM-Motor",style6)
		sheet1.write(s2+41,0,"End of the curve - KW(Rated) liquid",style6)
		sheet1.write(s2+42,0,"Critical Speed",style6)
		sheet1.write(s2+43,0,"Maximum Allowable Soild Size - MM",style6)
		sheet1.write(s2+44,0,"Impeller Number of vanes",style6)
		
		sheet1.write(s2+45,0,"Impeller Dia Max mm",style6)
		sheet1.write(s2+46,0,"Max Allowable Test Pressure",style6)
		sheet1.write(s2+47,0,"Pump Design",style6)
		sheet1.write(s2+48,0,"Casing Feet Location",style6)
		sheet1.write(s2+49,0,"Shut off Head in M",style6)
		sheet1.write(s2+50,0,"Shut off Pressure",style6)
		sheet1.write(s2+51,0,"Minimum Contionuous Flow - M3/hr",style6)
		sheet1.write(s2+52,0,"Specific Speed",style6)
		sheet1.write(s2+53,0,"Suction Specific Speed",style6)
		sheet1.write(s2+54,0,"Sealing Water Pressure Kg/cm^2",style6)
		sheet1.write(s2+55,0,"Sealing Water Capcity- m3/hr",style6)
		sheet1.write(s2+56,0,"GD SQ value",style6)
		sheet1.write(s2+57,0,"Bearing Make",style6)
		sheet1.write(s2+58,0,"BEARING NUMBER NDE / DE",style6)
		sheet1.write(s2+59,0,"Bearing Qty NDE / DE",style6)
		sheet1.write(s2+60,0,"Lubrication",style6)
		sheet1.write(s2+61,0,"Primemover Category",style6)
		sheet1.write(s2+62,0,"Transmission",style6)
		sheet1.write(s2+63,0,"Primemover",style6)
		sheet1.write(s2+64,0,"Operation Range",style6)
		
		if line_data:
			coln_no = 1
			s_no = 1
			for item in line_data:
				print"item['enquiry_line_id']--------------------------",item['enquiry_line_id']
				print"item['pump_id']",item['pump_id']
				item_sql = """
					select 
					enq_line.equipment_no as equipment_no,
					enq_line.description as description,
					enq_line.qty as qty,
					liquid.name as liquid_name,
					enq_line.temperature_in_c as temperature_in_c,
					enq_line.solid_concen as solid_concen,
					enq_line.specific_gravity as specific_gravity,
					enq_line.viscosity as viscosity,
					enq_line.max_particle_size_mm as max_particle_size_mm,
					enq_line.npsh_avl as npsh_avl,
					enq_line.density as density,
					enq_line.capacity_in_liquid as capacity_in_liquid,
					enq_line.head_in_liquid as head_in_liquid,
					enq_line.consistency as consistency,
					psm.name as pumpseries,
					psms.name as pumpseries,
					enq_line.pre_suppliy_ref as pre_suppliy_ref,
					(CASE WHEN enq_line.shaft_sealing = 'gld_packing_tiga' 
						THEN 'Gland Packing-TIGA'
						WHEN enq_line.shaft_sealing = 'gld_packing_ptfe' 
						THEN 'Gland Packing-PTFE'
						WHEN enq_line.shaft_sealing = 'mc_seal' 
						THEN 'M/C Seal'
						WHEN enq_line.shaft_sealing = 'dynamic_seal' 
						THEN 'Dynamic Seal'
						ELSE ''
						end ) as shaft_sealing,
					(CASE WHEN enq_line.scope_of_supply = 'bare_pump' 
						THEN 'Bare Pump'
						WHEN enq_line.scope_of_supply = 'pump_with_acces' 
						THEN 'Pump With Accessories'
						WHEN enq_line.scope_of_supply = 'pump_with_acces_motor' 
						THEN 'Pump With Accessories And Motor'
						ELSE ''
						end ) as scope_of_supply,
					enq_line.number_of_stages as number_of_stages,
					(CASE WHEN enq_line.impeller_type = 'open' 
						THEN 'Open'
						WHEN enq_line.impeller_type = 'semi_open' 
						THEN 'Semi Open'
						WHEN enq_line.impeller_type = 'close' 
						THEN 'Closed'
						ELSE ''
						end ) as impeller_type,
					enq_line.impeller_dia_min as impeller_dia_min,
					enq_line.size_suctionx as size_suctionx,
					(CASE WHEN enq_line.flange_type = 'standard' 
						THEN 'Standard'
						WHEN enq_line.flange_type = 'optional' 
						THEN 'Optional'
						ELSE ''
						end ) as flange_type,
					psf.name as flange_standard,
					enq_line.efficiency_in as efficiency_in,
					enq_line.npsh_r_m as npsh_r_m,
					enq_line.best_efficiency as best_efficiency,
					enq_line.bkw_water as bkw_water,
					enq_line.bkw_liq as bkw_liq,
					enq_line.impeller_dia_rated as impeller_dia_rated,
					enq_line.impeller_tip_speed as impeller_tip_speed,
					enq_line.hydrostatic_test_pressure as hydrostatic_test_pressure,
					enq_line.setting_height as setting_height,
					enq_line.full_load_rpm as full_load_rpm,
					(CASE WHEN enq_line.frequency = '50' 
						THEN '50'
						WHEN enq_line.frequency = '60' 
						THEN '60'
						ELSE ''
						end ) as frequency,
					enq_line.motor_kw as motor_kw,
					enq_line.motor_margin as motor_margin,
					enq_line.speed_in_motor as speed_in_motor,
					enq_line.end_of_the_curve as end_of_the_curve,
					enq_line.critical_speed as critical_speed,
					enq_line.maximum_allowable_soild as maximum_allowable_soild,
					enq_line.impeller_number as impeller_number,
					enq_line.impeller_dia_max as impeller_dia_max,
					enq_line.max_allowable_test as max_allowable_test,
					(CASE WHEN enq_line.crm_type = 'pull_out' 
						THEN 'End Suction Back Pull Out'
						WHEN enq_line.crm_type = 'split_case' 
						THEN 'Split Case'
						WHEN enq_line.crm_type = 'multistage' 
						THEN 'Multistage'
						WHEN enq_line.crm_type = 'twin_casing' 
						THEN 'Twin Casing'
						WHEN enq_line.crm_type = 'single_casing' 
						THEN 'Single Casing'
						WHEN enq_line.crm_type = 'self_priming' 
						THEN 'Self Priming'
						WHEN enq_line.crm_type = 'vo_vs4' 
						THEN 'VO-VS4'
						WHEN enq_line.crm_type = 'vg_vs5' 
						THEN 'VG-VS5'
						ELSE ''
						end ) as crm_type,
					(CASE WHEN enq_line.casing_design = 'base' 
						THEN 'Base'
						WHEN enq_line.casing_design = 'center_line' 
						THEN 'Center Line'
						ELSE ''
						end ) as casing_design,
					enq_line.shut_off_head as shut_off_head,
					enq_line.shut_off_pressure as shut_off_pressure,
					enq_line.minimum_contionuous as minimum_contionuous,
					enq_line.specific_speed as specific_speed,
					enq_line.suction_specific_speed as suction_specific_speed,
					enq_line.sealing_water_pressure as sealing_water_pressure,
					enq_line.sealing_water_capacity as sealing_water_capacity,
					enq_line.gd_sq_value as gd_sq_value,
					enq_line.bearing_make as bearing_make,
					enq_line.bearing_number_nde as bearing_number_nde,
					enq_line.bearing_qty_nde as bearing_qty_nde,
					(CASE WHEN enq_line.lubrication_type = 'grease' 
						THEN 'Grease'
						WHEN enq_line.lubrication_type = 'oil' 
						THEN 'Oil'
						ELSE ''
						end ) as lubrication_type,
					(CASE WHEN enq_line.primemover_categ = 'engine' 
						THEN 'Engine'
						WHEN enq_line.primemover_categ = 'motor' 
						THEN 'Motor'
						WHEN enq_line.primemover_categ = 'vfd' 
						THEN 'VFD'
						ELSE ''
						end ) as primemover_categ,
					(CASE WHEN enq_line.type_of_drive = 'motor_direct' 
						THEN 'Motor-direct'
						WHEN enq_line.type_of_drive = 'belt_drive' 
						THEN 'Belt drive'
						WHEN enq_line.type_of_drive = 'fc_gb' 
						THEN 'Fluid Coupling Gear Box'
						ELSE ''
						end ) as type_of_drive,
					(CASE WHEN enq_line.pump_model_type = 'vertical' 
						THEN 'Vertical'
						WHEN enq_line.pump_model_type = 'horizontal' 
						THEN 'Horizontal'
						ELSE ''
						end ) as pump_type,
					pm.name as primemover,
					enq_line.operation_range as operation_range
					
					from ch_kg_crm_pumpmodel enq_line
					
					left join kg_fluid_master liquid on(liquid.id=enq_line.fluid_id)
					left join ch_pumpseries_flange psf on(psf.id=enq_line.flange_standard)
					left join kg_pumpseries_master psm on(psm.id=enq_line.pumpseries_id)
					left join kg_pumpseries_master psms on(psms.id=enq_line.spare_pumpseries_id)
					left join kg_primemover_master pm on(pm.id=enq_line.primemover_id)
					where enq_line.id = """+ str(item['enquiry_line_id']) +""" and enq_line.pump_id = """+ str(item['pump_id']) + """ order by enq_line.pump_id
					"""
				cr.execute(item_sql)		
				item_data = cr.dictfetchall()
				print"item_dataitem_data",item_data
				if item_data:
					for ele in item_data:
						sheet1.write(s2,coln_no,s_no,style8)
						sheet1.write(s2+1,coln_no,ele['equipment_no'] or "-",style8)
						sheet1.write(s2+2,coln_no,ele['description'] or "-",style8)
						sheet1.write(s2+3,coln_no,ele['qty'] or "-",style8)
						sheet1.write(s2+4,coln_no,ele['pre_suppliy_ref'] or "-",style8)
						sheet1.write(s2+6,coln_no,ele['liquid_name'] or "-",style8)
						sheet1.write(s2+7,coln_no,ele['temperature_in_c'] or "-",style8)
						sheet1.write(s2+8,coln_no,ele['solid_concen'] or "-",style8)
						sheet1.write(s2+9,coln_no,ele['consistency'] or "-",style8)
						sheet1.write(s2+10,coln_no,ele['specific_gravity'] or "-",style8)
						sheet1.write(s2+11,coln_no,ele['density'] or "-",style8)
						sheet1.write(s2+12,coln_no,ele['viscosity'] or "-",style8)
						sheet1.write(s2+13,coln_no,ele['max_particle_size_mm'] or "-",style8)
						sheet1.write(s2+14,coln_no,ele['npsh_avl'] or "-",style8)
						sheet1.write(s2+15,coln_no,ele['capacity_in_liquid'] or "-",style8)
						sheet1.write(s2+16,coln_no,ele['head_in_liquid'] or "-",style8)
						sheet1.write(s2+18,coln_no,ele['pump_type'] or "-",style8)
						sheet1.row(s2+18).height = 490
						sheet1.write(s2+19,coln_no,item['name'] or "-",style1)
						#~ sheet1.write(s2+20,coln_no,ele['pumpseries'] or "-",style8)	
						#~ sheet1.write(s2+21,coln_no,ele['pre_suppliy_ref'] or "-",style8)
						sheet1.write(s2+20,coln_no,ele['shaft_sealing'] or "-",style8)
						sheet1.write(s2+21,coln_no,ele['scope_of_supply'] or "-",style8)
						sheet1.write(s2+22,coln_no,ele['number_of_stages'] or "-",style8)
						sheet1.write(s2+23,coln_no,ele['impeller_type'] or "-",style8)
						sheet1.write(s2+24,coln_no,ele['impeller_dia_min'] or "-",style8)
						sheet1.write(s2+25,coln_no,ele['size_suctionx'] or "-",style8)
						#~ sheet1.write(s2+26,coln_no,ele['flange_type'] or "-",style8)
						sheet1.write(s2+26,coln_no,ele['flange_standard'] or "-",style8)
						sheet1.write(s2+27,coln_no,ele['efficiency_in'] or "-",style8)
						sheet1.write(s2+28,coln_no,ele['npsh_r_m'] or "-",style8)
						sheet1.write(s2+29,coln_no,ele['best_efficiency'] or "-",style8)
						sheet1.write(s2+30,coln_no,ele['bkw_water'] or "-",style8)
						sheet1.write(s2+31,coln_no,ele['bkw_liq'] or "-",style8)
						sheet1.write(s2+32,coln_no,ele['impeller_dia_rated'] or "-",style8)
						sheet1.write(s2+33,coln_no,ele['impeller_tip_speed'] or "-",style8)
						sheet1.write(s2+34,coln_no,ele['hydrostatic_test_pressure'] or "-",style8)
						sheet1.write(s2+35,coln_no,ele['setting_height'] or "-",style8)
						sheet1.write(s2+36,coln_no,ele['full_load_rpm'] or "-",style8)
						sheet1.write(s2+37,coln_no,ele['frequency'] or "-",style8)
						sheet1.write(s2+38,coln_no,ele['motor_kw'] or "-",style8)
						sheet1.write(s2+39,coln_no,ele['motor_margin'] or "-",style8)
						sheet1.write(s2+40,coln_no,ele['speed_in_motor'] or "-",style8)
						sheet1.write(s2+41,coln_no,ele['end_of_the_curve'] or "-",style8)
						sheet1.write(s2+42,coln_no,ele['critical_speed'] or "-",style8)
						sheet1.write(s2+43,coln_no,ele['maximum_allowable_soild'] or "-",style8)
						sheet1.write(s2+44,coln_no,ele['impeller_number'] or "-",style8)
					
						sheet1.write(s2+45,coln_no,ele['impeller_dia_max'] or "-",style8)
						sheet1.write(s2+46,coln_no,ele['max_allowable_test'] or "-",style8)
						sheet1.write(s2+47,coln_no,ele['crm_type'] or "-",style8)
						sheet1.write(s2+48,coln_no,ele['casing_design'] or "-",style8)
						sheet1.write(s2+49,coln_no,ele['shut_off_head'] or "-",style8)
						sheet1.write(s2+50,coln_no,ele['shut_off_pressure'] or "-",style8)
						sheet1.write(s2+51,coln_no,ele['minimum_contionuous'] or "-",style8)
						sheet1.write(s2+52,coln_no,ele['specific_speed'] or "-",style8)
						sheet1.write(s2+53,coln_no,ele['suction_specific_speed'] or "-",style8)
						sheet1.write(s2+54,coln_no,ele['sealing_water_pressure'] or "-",style8)
						sheet1.write(s2+55,coln_no,ele['sealing_water_capacity'] or "-",style8)
						sheet1.write(s2+56,coln_no,ele['gd_sq_value'] or "-",style8)
						sheet1.write(s2+57,coln_no,ele['bearing_make'] or "-",style8)
						sheet1.write(s2+58,coln_no,ele['bearing_number_nde'] or "-",style8)
						sheet1.write(s2+59,coln_no,ele['bearing_qty_nde'] or "-",style8)
						sheet1.write(s2+60,coln_no,ele['lubrication_type'] or "-",style8)
						sheet1.write(s2+61,coln_no,ele['primemover_categ'] or "-",style8)
						sheet1.write(s2+62,coln_no,ele['type_of_drive'] or "-",style8)
						sheet1.write(s2+63,coln_no,ele['primemover'] or "-",style8)
						sheet1.write(s2+64,coln_no,ele['operation_range'] or "-",style8)
						
						s_no = s_no + 1
					coln_no = coln_no + 1
				else:
					sheet1.write(s2+1,coln_no,"-",style6)
					sheet1.write(s2+2,coln_no,"-",style6)
					sheet1.write(s2+3,coln_no,"-",style6)
					sheet1.write(s2+5,coln_no,"-",style6)
					sheet1.write(s2+6,coln_no,"-",style6)
					sheet1.write(s2+7,coln_no,"-",style6)
					sheet1.write(s2+8,coln_no,"-",style6)
					sheet1.write(s2+9,coln_no,"-",style6)
					sheet1.write(s2+10,coln_no,"-",style6)
					sheet1.write(s2+11,coln_no,"-",style6)
					sheet1.write(s2+12,coln_no,"-",style6)
					sheet1.write(s2+13,coln_no,"-",style6)
					sheet1.write(s2+14,coln_no,"-",style6)
					sheet1.write(s2+15,coln_no,"-",style6)
					sheet1.write(s2+17,coln_no,"-",style6)
					sheet1.row(s2+17).height = 490
					sheet1.write(s2+18,coln_no,"-",style1)
					sheet1.write(s2+19,coln_no,"-",style6)	
					#~ sheet1.write(s2+20,coln_no,"-",style6)
					#~ sheet1.write(s2+21,coln_no,"-",style6)
					sheet1.write(s2+20,coln_no,"-",style6)
					sheet1.write(s2+21,coln_no,"-",style6)
					sheet1.write(s2+22,coln_no,"-",style6)
					sheet1.write(s2+23,coln_no,"-",style6)
					sheet1.write(s2+24,coln_no,"-",style6)
					sheet1.write(s2+25,coln_no,"-",style6)
					#~ sheet1.write(s2+26,coln_no,"-",style6)
					sheet1.write(s2+26,coln_no,"-",style6)
					sheet1.write(s2+27,coln_no,"-",style6)
					sheet1.write(s2+28,coln_no,"-",style6)
					sheet1.write(s2+29,coln_no,"-",style6)
					sheet1.write(s2+30,coln_no,"-",style6)
					sheet1.write(s2+31,coln_no,"-",style6)
					sheet1.write(s2+32,coln_no,"-",style6)
					sheet1.write(s2+33,coln_no,"-",style6)
					sheet1.write(s2+34,coln_no,"-",style6)
					sheet1.write(s2+35,coln_no,"-",style6)
					sheet1.write(s2+36,coln_no,"-",style6)
					sheet1.write(s2+37,coln_no,"-",style6)
					sheet1.write(s2+38,coln_no,"-",style6)
					sheet1.write(s2+39,coln_no,"-",style6)
					sheet1.write(s2+40,coln_no,"-",style6)
					sheet1.write(s2+41,coln_no,"-",style6)
					sheet1.write(s2+42,coln_no,"-",style6)
					sheet1.write(s2+43,coln_no,"-",style6)
					
					sheet1.write(s2+46,coln_no,"-",style6)
					sheet1.write(s2+47,coln_no,"-",style6)
					sheet1.write(s2+48,coln_no,"-",style6)
					sheet1.write(s2+49,coln_no,"-",style6)
					sheet1.write(s2+50,coln_no,"-",style6)
					sheet1.write(s2+51,coln_no,"-",style6)
					sheet1.write(s2+52,coln_no,"-",style6)
					sheet1.write(s2+53,coln_no,"-",style6)
					sheet1.write(s2+54,coln_no,"-",style6)
					sheet1.write(s2+55,coln_no,"-",style6)
					sheet1.write(s2+56,coln_no,"-",style6)
					sheet1.write(s2+57,coln_no,"-",style6)
					sheet1.write(s2+58,coln_no,"-",style6)
					sheet1.write(s2+59,coln_no,"-",style6)
					sheet1.write(s2+60,coln_no,"-",style6)
					sheet1.write(s2+61,coln_no,"-",style6)
					sheet1.write(s2+62,coln_no,"-",style6)
					sheet1.write(s2+63,coln_no,"-",style6)
					sheet1.write(s2+64,coln_no,"-",style6)
					sheet1.write(s2+65,coln_no,"-",style6)
					coln_no = coln_no+ 1
					
		if line_data:
			em_col = 1
			for item in line_data:
				mat_sql = """
							select 
							omat.name as mat_name,
							moc.name as moc

							from ch_kg_crm_pumpmodel enq_line
							
							join ch_moc_construction mocc on(mocc.header_id=enq_line.id)
							left join kg_offer_materials omat on(omat.id=mocc.offer_id)
							left join kg_moc_master moc on(moc.id=mocc.moc_id)
							where enq_line.id = """+ str(item['enquiry_line_id']) +""" and enq_line.pump_id = """+ str(item['pump_id']) + """ order by enq_line.pump_id,enq_line.id
							"""
				cr.execute(mat_sql)		
				mat_data = cr.dictfetchall()
				print"mat_data",mat_data
				row_no = s2+66
				
				if mat_data:
					for item_1 in mat_data:
						if item_1['mat_name'] or item_1['moc']:
							m_col_no = 0
							sheet1.write(row_no,m_col_no,item_1['mat_name'])
							sheet1.write(row_no,em_col,item_1['moc'] or "-",style8)
							row_no = row_no+1
				else:
					m_col_no = 0
					sheet1.write(row_no,em_col,"-",style8)
					row_no = row_no+1
				em_col = em_col + 1 
		print"row_norow_norow_norow_no",row_no
		
		sheet1.write_merge(row_no, row_no, 0, len_col, 'Mechanical Seal Details : Eagle Burgmann / Flow Serve / Leak Proof:', style5)
		sheet1.row(row_no).height = 400
		row_no = row_no + 1
		
		sheet1.write_merge(row_no, row_no, 0, 0, 'Seal Type / Face Combination', style4)
		print"row_norow_norow_nosssssssssS",row_no
		print"row_norow_norow_nolen_collen_collen_col",len_col
		sheet1.write_merge(row_no+1, row_no+1, 0, 0, 'Gland Plate / API Plan', style4)
		if line_data:
			em_col = 1
			for item in line_data:
				mech_sql = """
							select 
							enq_line.shaft_sealing as shaft_sealing,
							enq_line.shaft_sealing as gland
							
							from ch_kg_crm_pumpmodel enq_line
							
							where enq_line.id = """+ str(item['enquiry_line_id']) +""" and enq_line.pump_id = """+ str(item['pump_id']) + """
							"""
				cr.execute(mech_sql)		
				mech_data = cr.dictfetchall()
				print"mech_data",mech_data
				if mech_data:
					s = 1
					for item_1 in mech_data:
						if item_1['shaft_sealing'] or item_1['gland']:
							m_col_no = 1
							sheet1.write(row_no,em_col,item_1['shaft_sealing'],style8)
							sheet1.write(row_no+1,em_col,item_1['gland'],style8)
							m_col_no = m_col_no+1
						else:
							m_col_no = 1
							sheet1.write(row_no,em_col,"-",style8)
							sheet1.write(row_no+1,em_col,"-",style8)
							m_col_no = m_col_no+1
						s = s + 1
						em_col = em_col + 1
						print"sssssssssssss",s
				else:
					sheet1.write(row_no,em_col,"-",style8)
					sheet1.write(row_no+1,em_col,"-",style8)
					em_col = em_col + 1
					
			print"row_norow_nodddddD",row_no
			row_no = row_no + s
		
		sheet1.write_merge(row_no, row_no, 0, len_col, 'Motor Make Details:', style5)
		sheet1.row(row_no).height = 400
		row_no = row_no + 1
		
		sheet1.write_merge(row_no, row_no, 0, 0, 'Type / Mounting', style4)
		sheet1.write_merge(row_no+1, row_no+1, 0, 0, 'Insulation / protection', style4)
		sheet1.write_merge(row_no+2, row_no+2, 0, 0, 'Voltage / Phase / Frequency', style4)
		if line_data:
			em_col = 1
			for item in line_data:
				mm_sql = """
							select 
							enq_line.shaft_sealing as shaft_sealing,
							enq_line.qty as qty,
							enq_line.qty as qty
							
							from ch_kg_crm_pumpmodel enq_line
							
							where enq_line.id = """+ str(item['enquiry_line_id']) +""" and enq_line.pump_id = """+ str(item['pump_id']) + """ """
				cr.execute(mm_sql)		
				mm_data = cr.dictfetchall()
				print"mm_data",mm_data
				s = 1
				if mm_data:
					for item_1 in mm_data:
						if item_1['shaft_sealing'] or item_1['qty']:
							sheet1.write(row_no,em_col,"-",style8)
							sheet1.write(row_no+1,em_col,"-",style8)
							sheet1.write(row_no+2,em_col,"-",style8)
							#~ sheet1.write(row_no,em_col,item_1['shaft_sealing'] or "-",style8)
							#~ sheet1.write(row_no+1,em_col,item_1['qty'] or "-",style8)
							#~ sheet1.write(row_no+2,em_col,item_1['qty'] or "-",style8)
						else:
							sheet1.write(row_no,em_col,"-",style8)
							sheet1.write(row_no+1,em_col,"-",style8)
							sheet1.write(row_no+2,em_col,"-",style8)
						s = s + 2
						em_col = em_col + 1
				else:
					sheet1.write(row_no,em_col,"-",style8)
					sheet1.write(row_no+1,em_col,"-",style8)
					sheet1.write(row_no+2,em_col,"-",style8)
					em_col = em_col + 1
		row_no = row_no + s
		
		sheet1.write_merge(row_no, row_no, 0, len_col, 'Scope Of Supply / Price per Each in Rs.', style5)
		sheet1.row(row_no).height = 400
		row_no = row_no + 1
		
		sheet1.write_merge(row_no, row_no, 0, 0, 'Bare Pump', style4)
		
		if line_data:
			em_col = 1
			for item in line_data:
				ss_sql = """
							select 
							pump_offer.net_amount as net_amount
							
							from ch_pump_offer pump_offer
							
							where pump_offer.header_id = """+ str(rec.id) +""" and pump_offer.pump_id = """+ str(item['pump_id']) + """ """
				cr.execute(ss_sql)		
				ss_data = cr.dictfetchall()
				print"ss_data",ss_data
				if ss_data:
					for item_1 in ss_data:
						if item_1['net_amount']:
							sheet1.write(row_no,em_col,item_1['net_amount'] or "-",style8)
						else:
							sheet1.write(row_no,em_col,"-",style8)
						em_col = em_col + 1
				else:
					sheet1.write(row_no,em_col,"-",style8)
					em_col = em_col + 1
		row_no = row_no
		print"eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",row_no
		sheet1.write_merge(row_no+1, row_no+1, 0, len_col, 'Accessories', style5)
		sheet1.row(row_no+1).height = 400
		row_no = row_no + 1
		
		if line_data:
			em_col = 1
			for item in line_data:
				access_sql = """
							select 
							acc.name as access_name,
							access_offer.net_amount as net_amount
							
							from ch_accessories_offer access_offer
							left join kg_accessories_master acc on(acc.id=access_offer.access_id)
							where access_offer.header_id = """+ str(rec.id) +""" and access_offer.pump_id = """+ str(item['pump_id']) + """ order by access_offer.pump_id """
				cr.execute(access_sql)		
				access_data = cr.dictfetchall()
				print"access_data",access_data
				if access_data:
					for item_1 in access_data:
						if item_1['net_amount'] or item_1['access_name']:
							sheet1.write(row_no+1,0,item_1['access_name'],style8)
							sheet1.write(row_no+1,em_col,item_1['net_amount'] or "-",style8)
							row_no = row_no+1
					em_col = em_col + 1
				else:
					sheet1.write(row_no+1,em_col,"-",style8)
					em_col = em_col + 1
		row_no = row_no
		
		sheet1.write_merge(row_no+2, row_no+2, 0, len_col, 'Spares:', style5)
		sheet1.row(row_no+1).height = 400
		row_no = row_no + 1
		
		if line_data:
			em_col = 1
			for item in line_data:
				spare_sql = """
							select 
							spare_offer.item_name as spare_name,
							pmm.name as pump_name,
							spare_offer.net_amount as net_amount
							
							from ch_spare_offer spare_offer
							left join kg_pumpmodel_master pmm on(pmm.id=spare_offer.pump_id)
							where spare_offer.header_id = """+ str(rec.id) +""" and spare_offer.pump_id = """+ str(item['pump_id']) + """ order by spare_offer.pump_id """
				cr.execute(spare_sql)		
				spare_data = cr.dictfetchall()
				print"spare_data",spare_data
				if spare_data:
					for item_1 in spare_data:
						if item_1['spare_name'] or item_1['net_amount']:
							m_col_no = 1
							sheet1.write(row_no+2,0,item_1['spare_name'],style8)
							sheet1.write(row_no+2,em_col,item_1['net_amount'] or "-",style8)
							row_no = row_no+1
				else:
					sheet1.write(row_no+2,em_col,"-",style8)
					em_col = em_col + 1
		row_no = row_no
		print"row_norow_norow_norow_norow_norow_no",row_no
				
		"""Parsing data as string """
		file_data=StringIO.StringIO()
		
		sheet1.set_protect(True)
		sheet1.set_password('secret')
		
		o=wbk.save(file_data)		
		"""string encode of data in wksheet"""		
		out=base64.encodestring(file_data.getvalue())
		"""returning the output xls as binary"""
		report_name = 'Offer Copy' + '.' + 'xls'
		
		return self.write(cr, uid, ids, {'rep_data':out,'offer_copy':report_name},context=context)
		
			
		
kg_crm_offer()


class ch_pump_offer(osv.osv):
	

	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		sam_ratio_tot = dealer_discount_tot = customer_discount_tot = spl_discount_tot = tax_tot = p_f_tot = freight_tot = insurance_tot = pump_price_tot = tot_price = net_amount = 0
		i_tot = k_tot = m_tot = p_tot = r_tot = 0
		for line in self.browse(cr, uid, ids, context=context):
			print"linelineline",line
			res[line.id] = {
				
				'sam_ratio_tot': 0.0,
				'dealer_discount_tot': 0.0,
				'customer_discount_tot' : 0.0,
				'spl_discount_tot' : 0.0,
				'tax_tot': 0.0,
				'p_f_tot': 0.0,
				'freight_tot': 0.0,
				'insurance_tot': 0.0,
				'pump_price': 0.0,
				'tot_price': 0.0,
				
			}
			print"line.prime_cost",line.prime_cost
			print"line.sam_ratio",line.sam_ratio
			sam_ratio_tot = line.prime_cost * line.sam_ratio
			print"sam_ratio_totsam_ratio_tot",sam_ratio_tot
			dealer_discount_tot = sam_ratio_tot / (( 100 - line.dealer_discount ) / 100.00 ) - sam_ratio_tot
			print"dealer_discount_totdealer_discount_tot",dealer_discount_tot
			i_tot = sam_ratio_tot + dealer_discount_tot
			customer_discount_tot = i_tot / (( 100 - line.customer_discount ) / 100.00 ) - i_tot
			print"customer_discount_totcustomer_discount_tot",customer_discount_tot
			k_tot = i_tot + customer_discount_tot
			spl_discount_tot = k_tot / (( 100 - line.special_discount ) / 100.00 ) - k_tot
			print"spl_discount_totspl_discount_tot",spl_discount_tot
			m_tot = k_tot + spl_discount_tot
			tax_tot = (m_tot / 100) * line.tax
			print"tax_tottax_tot",tax_tot
			p_f_tot = ( m_tot + tax_tot ) / 100.00 * line.p_f
			print"p_f_totp_f_tot",p_f_tot
			p_tot = m_tot + tax_tot + p_f_tot
			freight_tot = p_tot / (( 100 - line.freight ) / 100.00 ) - p_tot
			print"freight_totfreight_tot",freight_tot
			r_tot = p_tot + freight_tot
			insurance_tot = r_tot / (( 100 - line.insurance ) / 100.00 ) - r_tot
			print"insurance_totinsurance_tot",insurance_tot
			pump_price_tot = r_tot + insurance_tot
			print"pump_price_totpump_price_tot",pump_price_tot
			tot_price = pump_price_tot
			print"tot_pricetot_price",tot_price
			net_amount = tot_price * line.qty
			print"net_amountnet_amount",net_amount
			
			res[line.id]['sam_ratio_tot'] = sam_ratio_tot
			res[line.id]['dealer_discount_tot'] = dealer_discount_tot
			res[line.id]['customer_discount_tot'] = customer_discount_tot
			res[line.id]['spl_discount_tot'] = spl_discount_tot
			res[line.id]['tax_tot'] = tax_tot
			res[line.id]['p_f_tot'] = p_f_tot
			res[line.id]['freight_tot'] = freight_tot
			res[line.id]['insurance_tot'] = insurance_tot
			res[line.id]['pump_price_tot'] = pump_price_tot
			res[line.id]['tot_price'] = tot_price
			res[line.id]['net_amount'] = net_amount
			
		return res
		
	_name = "ch.pump.offer"
	_description = "Ch Pump Offer"
	
	_columns = {
	
		### Pump Details ####
		'header_id':fields.many2one('kg.crm.offer', 'Offer', ondelete='cascade'),
		'offer_id':fields.many2one('kg.crm.offer', 'Offer'),
		'qty':fields.integer('Quantity'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),
		'pumpseries_id': fields.many2one('kg.pumpseries.master','Pump Series'),
		'moc_const_id': fields.many2one('kg.moc.construction','MOC'),
		'prime_cost': fields.float('Prime Cost'),
		'per_pump_prime_cost': fields.float('Per Pump Prime Cost'),
		'sam_ratio': fields.float('Sam Ratio'),
		'dealer_discount': fields.float('Dealer Discount(%)'),
		'customer_discount': fields.float('Customer Discount(%)'),
		'special_discount': fields.float('Special Discount(%)'),
		'tax': fields.float('Tax(%)'),
		'p_f': fields.float('P&F(%)'),
		'freight': fields.float('Freight(%)'),
		'insurance': fields.float('Insurance(%)'),
		'total_price': fields.float('Total Price(%)'),
		
		'tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Price',multi="sums",store=True),	
		'sam_ratio_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Sam Ratio',multi="sums",store=True),	
		'dealer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),	
		'customer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),	
		'spl_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Special Discount Value',multi="sums",store=True),	
		'tax_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax',multi="sums",store=True),	
		'p_f_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F',multi="sums",store=True),	
		'freight_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),	
		'insurance_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),	
		'pump_price_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Pump Price',multi="sums",store=True),	
		'net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),	
		
		'enquiry_line_id': fields.many2one('ch.kg.crm.pumpmodel','Enquiry Line'),
		'off_fou_id': fields.related('enquiry_line_id','line_ids', type='one2many', relation='ch.kg.crm.foundry.item', string='Foundry Items'),
		'off_ms_id': fields.related('enquiry_line_id','line_ids_a', type='one2many', relation='ch.kg.crm.machineshop.item', string='MS Items'),
		'off_bot_id': fields.related('enquiry_line_id','line_ids_b', type='one2many', relation='ch.kg.crm.bot', string='BOT Items'),
		
		
	}
	
	#~ _defaults = {
		#~ 
		#~ 'temperature': 'normal',
		#~ 'flange_type': 'standard',
		#~ 'load_bom':False,
		#~ 
	#~ }

ch_pump_offer()


class ch_spare_offer(osv.osv):

	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		sam_ratio_tot = dealer_discount_tot = customer_discount_tot = spl_discount_tot = tax_tot = p_f_tot = freight_tot = insurance_tot = pump_price_tot = tot_price = net_amount = 0
		i_tot = k_tot = m_tot = p_tot = r_tot = 0
		for line in self.browse(cr, uid, ids, context=context):
			print"linelineline",line
			res[line.id] = {
				
				'sam_ratio_tot': 0.0,
				'dealer_discount_tot': 0.0,
				'customer_discount_tot' : 0.0,
				'spl_discount_tot' : 0.0,
				'tax_tot': 0.0,
				'p_f_tot': 0.0,
				'freight_tot': 0.0,
				'insurance_tot': 0.0,
				'pump_price': 0.0,
				'tot_price': 0.0,
				
			}
			print"line.prime_cost",line.prime_cost
			print"line.sam_ratio",line.sam_ratio
			sam_ratio_tot = line.prime_cost * line.sam_ratio
			print"sam_ratio_totsam_ratio_tot",sam_ratio_tot
			dealer_discount_tot = sam_ratio_tot / (( 100 - line.dealer_discount ) / 100.00 ) - sam_ratio_tot
			print"dealer_discount_totdealer_discount_tot",dealer_discount_tot
			i_tot = sam_ratio_tot + dealer_discount_tot
			customer_discount_tot = i_tot / (( 100 - line.customer_discount ) / 100.00 ) - i_tot
			print"customer_discount_totcustomer_discount_tot",customer_discount_tot
			k_tot = i_tot + customer_discount_tot
			spl_discount_tot = k_tot / (( 100 - line.special_discount ) / 100.00 ) - k_tot
			print"spl_discount_totspl_discount_tot",spl_discount_tot
			m_tot = k_tot + spl_discount_tot
			tax_tot = (m_tot / 100) * line.tax
			print"tax_tottax_tot",tax_tot
			p_f_tot = ( m_tot + tax_tot ) / 100.00 * line.p_f
			print"p_f_totp_f_tot",p_f_tot
			p_tot = m_tot + tax_tot + p_f_tot
			freight_tot = p_tot / (( 100 - line.freight ) / 100.00 ) - p_tot
			print"freight_totfreight_tot",freight_tot
			r_tot = p_tot + freight_tot
			insurance_tot = r_tot / (( 100 - line.insurance ) / 100.00 ) - r_tot
			print"insurance_totinsurance_tot",insurance_tot
			pump_price_tot = r_tot + insurance_tot
			print"pump_price_totpump_price_tot",pump_price_tot
			tot_price = pump_price_tot 
			print"tot_pricetot_price",tot_price
			net_amount = tot_price * 1
			print"net_amountnet_amount",net_amount
			
			res[line.id]['sam_ratio_tot'] = sam_ratio_tot
			res[line.id]['dealer_discount_tot'] = dealer_discount_tot
			res[line.id]['customer_discount_tot'] = customer_discount_tot
			res[line.id]['spl_discount_tot'] = spl_discount_tot
			res[line.id]['tax_tot'] = tax_tot
			res[line.id]['p_f_tot'] = p_f_tot
			res[line.id]['freight_tot'] = freight_tot
			res[line.id]['insurance_tot'] = insurance_tot
			res[line.id]['pump_price_tot'] = pump_price_tot
			res[line.id]['tot_price'] = tot_price
			res[line.id]['net_amount'] = net_amount
			
		return res
		
	_name = "ch.spare.offer"
	_description = "Ch Spare Offer"
	
	_columns = {
	
		### Pump Details ####
		'header_id':fields.many2one('kg.crm.offer', 'Offer', ondelete='cascade'),
		'offer_id':fields.many2one('kg.crm.offer', 'Offer'),
		'qty':fields.integer('Quantity'),
		'item_code': fields.char('Item Code'),
		'item_name': fields.char('Item Name'),
		'moc_id': fields.many2one('kg.moc.master','MOC Name'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No'),
		'ms_id': fields.many2one('kg.machine.shop','MS Name'),
		'bot_id': fields.many2one('kg.machine.shop','BOT Name'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),
		'pumpseries_id': fields.many2one('kg.pumpseries.master','Pump Series'),
		'moc_const_id': fields.many2one('kg.moc.construction','MOC'),
		'prime_cost': fields.float('Prime Cost'),
		'sam_ratio': fields.float('Sam Ratio'),
		'dealer_discount': fields.float('Dealer Discount(%)'),
		'customer_discount': fields.float('Customer Discount(%)'),
		'special_discount': fields.float('Special Discount(%)'),
		'tax': fields.float('Tax(%)'),
		'p_f': fields.float('P&F(%)'),
		'freight': fields.float('Freight(%)'),
		'insurance': fields.float('Insurance(%)'),
		'total_price': fields.float('Total Price'),
		
		'tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Price',multi="sums",store=True),	
		'sam_ratio_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Sam Ratio',multi="sums",store=True),	
		'dealer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),	
		'customer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),	
		'spl_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Special Discount Value',multi="sums",store=True),	
		'tax_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax',multi="sums",store=True),	
		'p_f_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F',multi="sums",store=True),	
		'freight_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),	
		'insurance_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),	
		'pump_price_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Pump Price',multi="sums",store=True),	
		'net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),	
		
		'enquiry_line_id': fields.many2one('ch.kg.crm.pumpmodel','Enquiry Line'),
		'off_fou_id': fields.related('enquiry_line_id','line_ids', type='one2many', relation='ch.kg.crm.foundry.item', string='Foundry Items'),
		'off_ms_id': fields.related('enquiry_line_id','line_ids_a', type='one2many', relation='ch.kg.crm.machineshop.item', string='MS Items'),
		'off_bot_id': fields.related('enquiry_line_id','line_ids_b', type='one2many', relation='ch.kg.crm.bot', string='BOT Items'),
		
		
	}
	

ch_spare_offer()

class ch_accessories_offer(osv.osv):
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		sam_ratio_tot = dealer_discount_tot = customer_discount_tot = spl_discount_tot = tax_tot = p_f_tot = freight_tot = insurance_tot = pump_price_tot = tot_price = net_amount = 0
		i_tot = k_tot = m_tot = p_tot = r_tot = 0
		for line in self.browse(cr, uid, ids, context=context):
			print"linelineline",line
			res[line.id] = {
				
				'sam_ratio_tot': 0.0,
				'dealer_discount_tot': 0.0,
				'customer_discount_tot' : 0.0,
				'spl_discount_tot' : 0.0,
				'tax_tot': 0.0,
				'p_f_tot': 0.0,
				'freight_tot': 0.0,
				'insurance_tot': 0.0,
				'pump_price': 0.0,
				'tot_price': 0.0,
				
			}
			print"line.prime_cost",line.prime_cost
			print"line.sam_ratio",line.sam_ratio
			sam_ratio_tot = line.prime_cost * line.sam_ratio
			print"sam_ratio_totsam_ratio_tot",sam_ratio_tot
			dealer_discount_tot = sam_ratio_tot / (( 100 - line.dealer_discount ) / 100.00 ) - sam_ratio_tot
			print"dealer_discount_totdealer_discount_tot",dealer_discount_tot
			i_tot = sam_ratio_tot + dealer_discount_tot
			customer_discount_tot = i_tot / (( 100 - line.customer_discount ) / 100.00 ) - i_tot
			print"customer_discount_totcustomer_discount_tot",customer_discount_tot
			k_tot = i_tot + customer_discount_tot
			spl_discount_tot = k_tot / (( 100 - line.special_discount ) / 100.00 ) - k_tot
			print"spl_discount_totspl_discount_tot",spl_discount_tot
			m_tot = k_tot + spl_discount_tot
			tax_tot = (m_tot / 100) * line.tax
			print"tax_tottax_tot",tax_tot
			p_f_tot = ( m_tot + tax_tot ) / 100.00 * line.p_f
			print"p_f_totp_f_tot",p_f_tot
			p_tot = m_tot + tax_tot + p_f_tot
			freight_tot = p_tot / (( 100 - line.freight ) / 100.00 ) - p_tot
			print"freight_totfreight_tot",freight_tot
			r_tot = p_tot + freight_tot
			insurance_tot = r_tot / (( 100 - line.insurance ) / 100.00 ) - r_tot
			print"insurance_totinsurance_tot",insurance_tot
			pump_price_tot = r_tot + insurance_tot
			print"pump_price_totpump_price_tot",pump_price_tot
			tot_price = pump_price_tot 
			print"tot_pricetot_price",tot_price
			net_amount = tot_price * line.qty
			print"net_amountnet_amount",net_amount
			
			res[line.id]['sam_ratio_tot'] = sam_ratio_tot
			res[line.id]['dealer_discount_tot'] = dealer_discount_tot
			res[line.id]['customer_discount_tot'] = customer_discount_tot
			res[line.id]['spl_discount_tot'] = spl_discount_tot
			res[line.id]['tax_tot'] = tax_tot
			res[line.id]['p_f_tot'] = p_f_tot
			res[line.id]['freight_tot'] = freight_tot
			res[line.id]['insurance_tot'] = insurance_tot
			res[line.id]['pump_price_tot'] = pump_price_tot
			res[line.id]['tot_price'] = tot_price
			res[line.id]['net_amount'] = net_amount
			
		return res
		
	_name = "ch.accessories.offer"
	_description = "Ch Accessories Offer"
	
	_columns = {
	
		### Spare Details ####
		'header_id':fields.many2one('kg.crm.offer', 'Offer', ondelete='cascade'),
		'offer_id':fields.many2one('kg.crm.offer', 'Offer'),
		'enquiry_line_id': fields.many2one('ch.kg.crm.pumpmodel','Enquiry Line'),
		'access_id':fields.many2one('kg.accessories.master', 'Item Name'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),
		'moc_id':fields.many2one('kg.moc.master', 'MOC'),
		'qty':fields.integer('Quantity'),
		'prime_cost': fields.float('Prime Cost'),
		'per_access_prime_cost': fields.float('Per Access Prime Cost'),
		'sam_ratio': fields.float('Sam Ratio'),
		'dealer_discount': fields.float('Dealer Discount(%)'),
		'customer_discount': fields.float('Customer Discount(%)'),
		'special_discount': fields.float('Special Discount(%)'),
		'tax': fields.float('Tax(%)'),
		'p_f': fields.float('P&F(%)'),
		'freight': fields.float('Freight(%)'),
		'insurance': fields.float('Insurance(%)'),
		'pump_price': fields.float('Pump Price'),
		'total_price': fields.float('Total Price'),
		
		'tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Price',multi="sums",store=True),	
		'sam_ratio_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Sam Ratio',multi="sums",store=True),	
		'dealer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),	
		'customer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),	
		'spl_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Special Discount Value',multi="sums",store=True),	
		'tax_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax',multi="sums",store=True),	
		'p_f_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F',multi="sums",store=True),	
		'freight_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),	
		'insurance_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),	
		'pump_price_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Pump Price',multi="sums",store=True),	
		'net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),	
		
		'enquiry_line_access_id': fields.many2one('ch.kg.crm.accessories','Enquiry Line'),
		'off_fou_id': fields.related('enquiry_line_access_id','line_ids', type='one2many', relation='ch.crm.access.fou', string='Foundry Items'),
		'off_ms_id': fields.related('enquiry_line_access_id','line_ids_a', type='one2many', relation='ch.crm.access.ms', string='MS Items'),
		'off_bot_id': fields.related('enquiry_line_access_id','line_ids_b', type='one2many', relation='ch.crm.access.bot', string='BOT Items'),
		
		
	}
	
ch_accessories_offer()

