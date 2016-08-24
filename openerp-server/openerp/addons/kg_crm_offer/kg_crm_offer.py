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
		other_charges_amt = 0
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'pump_tot_price': 0.0,
				'pump_sam_ratio': 0.0,
				'pump_dealer_discount': 0.0,
				'pump_customer_discount' : 0.0,
				'pump_tax': 0.0,
			}
			val = val1 = val3 = 0.0
			cur = order.customer_id.property_product_pricelist_purchase.currency_id
			
			other_charges_amt = 0
				
			per_to_amt = 0
			tot_discount = 0
			val1 += 0
			val += 0
			val3 += 0
			res[order.id]['pump_tot_price']=(round(other_charges_amt,0))
			res[order.id]['pump_sam_ratio']=(round(val,0))
			res[order.id]['pump_dealer_discount']=(round(val1,0))
			#res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] 
			res[order.id]['pump_customer_discount']=(round(val + val1 + 0))
			res[order.id]['pump_tax']=(round(val3,0))   
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
		
kg_crm_offer()


class ch_pump_offer(osv.osv):
	

	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		other_charges_amt = 0
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'tot_price': 0.0,
				'sam_ratio_tot': 0.0,
				'dealer_discount_tot': 0.0,
				'customer_discount_tot' : 0.0,
				'tax_tot': 0.0,
			}
			val = val1 = val3 = 0.0
			
			other_charges_amt = 0
				
			per_to_amt = 0
			tot_discount = 0
			val1 += 0
			val += 0
			val3 += 0
			res[order.id]['tot_price']=(round(other_charges_amt,0))
			res[order.id]['sam_ratio_tot']=(round(val,0))
			res[order.id]['dealer_discount_tot']=(round(val1,0))
			#res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] 
			res[order.id]['customer_discount_tot']=(round(val + val1 + 0))
			res[order.id]['tax_tot']=(round(val3,0))   
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
		'sam_ratio': fields.float('Sam Ratio'),
		'dealer_discount': fields.float('Dealer Discount'),
		'customer_discount': fields.float('Customer Discount'),
		'special_discount': fields.float('Special Discount'),
		'tax': fields.float('Tax'),
		'p_f': fields.float('P&F'),
		'freight': fields.float('Freight'),
		'insurance': fields.float('Insurance'),
		'pump_price': fields.float('Pump Price'),
		'total_price': fields.float('Total Price'),
		
		'tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Price',multi="sums",store=True),	
		'sam_ratio_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Sam Ratio',multi="sums",store=True),	
		'dealer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),	
		'customer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),	
		'tax_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax',multi="sums",store=True),	
		'p_f_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F',multi="sums",store=True),	
		'freight_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),	
		'insurance_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),	
		'net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),	
			 
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
	
	_name = "ch.spare.offer"
	_description = "Ch Spare Offer"
	
	_columns = {
	
		### Spare Details ####
		'header_id':fields.many2one('kg.crm.offer', 'Offer', ondelete='cascade'),
		'offer_id':fields.many2one('kg.crm.offer', 'Offer'),
		'spare_count':fields.integer('Spare Count'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),
		'pumpseries_id': fields.many2one('kg.pumpseries.master','Pump Series'),
		'price_cost': fields.float('Price Cost'),
		'total_price': fields.float('Total Price'),
		
		'line_fou_ids': fields.one2many('ch.spare.offer.fou', 'header_id', "FOU"),
		'line_ms_ids': fields.one2many('ch.spare.offer.ms', 'header_id', "FOU"),
		'line_bot_ids': fields.one2many('ch.spare.offer.bot', 'header_id', "BOT"),
		
	}
	
ch_spare_offer()


class ch_spare_offer_fou(osv.osv):
	
	_name = "ch.spare.offer.fou"
	_description = "Ch Spare Offer FOU"
	
	_columns = {
	
		### FOU Details ####
		'header_id':fields.many2one('ch.spare.offer', 'Offer', ondelete='cascade'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No', domain="[('active','=','t')]"),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'pattern_name': fields.char('Pattern Name'),
		'qty': fields.integer('Quantity'),
		'prime_cost': fields.float('Prime Cost'),
		'ratio': fields.float('Ratio'),
		'dealer_discount': fields.float('Dealer Discount'),
		'customer_discount': fields.float('Customer Discount'),
		'special_discount': fields.float('Special Discount'),
		'tax': fields.float('Tax'),
		'p_f': fields.float('P&F'),
		'freight': fields.float('Freight'),
		'insurance': fields.float('Insurance'),
		'quote_price': fields.float('Quote Price'),
		'total_price': fields.float('Total Price'),
		
	}
	
	def onchange_pattern_name(self, cr, uid, ids, pattern_id):
		value = {'pattern_name':''}
		pattern_obj = self.pool.get('kg.pattern.master').search(cr,uid,([('id','=',pattern_id)]))
		if pattern_obj:
			pattern_rec = self.pool.get('kg.pattern.master').browse(cr,uid,pattern_obj[0])
			value = {'pattern_name':pattern_rec.pattern_name}
		return {'value': value}
		
ch_spare_offer_fou()

class ch_spare_offer_ms(osv.osv):
	
	_name = "ch.spare.offer.ms"
	_description = "Ch Spare Offer MS"
	
	_columns = {
	
		### MS Details ####
		'header_id':fields.many2one('ch.spare.offer', 'Offer', ondelete='cascade'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','ms')], ondelete='cascade'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'ms_line_id':fields.many2one('ch.machineshop.details', 'Item Name'),
		'qty': fields.integer('Quantity'),
		'prime_cost': fields.float('Prime Cost'),
		'ratio': fields.float('Ratio'),
		'dealer_discount': fields.float('Dealer Discount'),
		'customer_discount': fields.float('Customer Discount'),
		'special_discount': fields.float('Special Discount'),
		'tax': fields.float('Tax'),
		'p_f': fields.float('P&F'),
		'freight': fields.float('Freight'),
		'insurance': fields.float('Insurance'),
		'quote_price': fields.float('Quote Price'),
		'total_price': fields.float('Total Price'),
		
	}
	
		
ch_spare_offer_ms()


class ch_spare_offer_bot(osv.osv):
	
	_name = "ch.spare.offer.bot"
	_description = "Ch Spare Offer BOT"
	
	_columns = {
	
		### MS Details ####
		'header_id':fields.many2one('ch.spare.offer', 'Offer', ondelete='cascade'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','bot')], ondelete='cascade',required=True),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'bot_line_id':fields.many2one('ch.bot.details', 'Item Name'),
		'qty': fields.integer('Quantity'),
		'prime_cost': fields.float('Prime Cost'),
		'ratio': fields.float('Ratio'),
		'dealer_discount': fields.float('Dealer Discount'),
		'customer_discount': fields.float('Customer Discount'),
		'special_discount': fields.float('Special Discount'),
		'tax': fields.float('Tax'),
		'p_f': fields.float('P&F'),
		'freight': fields.float('Freight'),
		'insurance': fields.float('Insurance'),
		'quote_price': fields.float('Quote Price'),
		'total_price': fields.float('Total Price'),
		
	}
	
		
ch_spare_offer_bot()



class ch_accessories_offer(osv.osv):
	
	_name = "ch.accessories.offer"
	_description = "Ch Accessories Offer"
	
	_columns = {
	
		### Spare Details ####
		'header_id':fields.many2one('kg.crm.offer', 'Offer', ondelete='cascade'),
		'offer_id':fields.many2one('kg.crm.offer', 'Offer'),
		'access_id':fields.many2one('kg.accessories.master', 'Item Name'),
		'moc_id':fields.many2one('kg.moc.master', 'MOC'),
		'qty':fields.integer('Quantity'),
		'sam_ratio': fields.float('Sam Ratio'),
		'dealer_discount': fields.float('Dealer Discount'),
		'customer_discount': fields.float('Customer Discount'),
		'special_discount': fields.float('Special Discount'),
		'tax': fields.float('Tax'),
		'p_f': fields.float('P&F'),
		'freight': fields.float('Freight'),
		'insurance': fields.float('Insurance'),
		'pump_price': fields.float('Pump Price'),
		'total_price': fields.float('Total Price'),
		
	}
	
ch_accessories_offer()

