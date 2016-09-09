from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import base64

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

CALL_TYPE_SELECTION = [
    ('service','Service'),
    ('new_enquiry','New Enquiry')
]
PURPOSE_SELECTION = [
    ('pump','Pump'),('spare','Spare'),('prj','Project'),('pump_spare','Pump With Spare')
]
STATE_SELECTION = [
    ('draft','Draft'),('moved_to_offer','Moved To Offer'),('call','Call Back'),('quote','Quote Process'),('wo_released','WO Released'),('reject','Rejected')
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
	#	'division_id':_get_default_division,
		'due_date' : lambda * a: time.strftime('%Y-%m-%d'),
		
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
			
		
		off_no = ''	
		seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.crm.offer')])
		rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],rec.code,entry.offer_date))
		off_no = cr.fetchone();
		self.write(cr, uid, ids, {
									'name':off_no[0],
									'state': 'moved_to_offer',
									'confirm_user_id': uid, 
									'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')
								})
		return True
		
			
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
		'sam_ratio': fields.float('Sam Ratio(%)'),
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
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),
		'pumpseries_id': fields.many2one('kg.pumpseries.master','Pump Series'),
		'moc_const_id': fields.many2one('kg.moc.construction','MOC'),
		'prime_cost': fields.float('Prime Cost'),
		'sam_ratio': fields.float('Sam Ratio(%)'),
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
		'access_id':fields.many2one('kg.accessories.master', 'Item Name'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),
		'moc_id':fields.many2one('kg.moc.master', 'MOC'),
		'qty':fields.integer('Quantity'),
		'prime_cost': fields.float('Prime Cost'),
		'per_access_prime_cost': fields.float('Per Access Prime Cost'),
		'sam_ratio': fields.float('Sam Ratio(%)'),
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

