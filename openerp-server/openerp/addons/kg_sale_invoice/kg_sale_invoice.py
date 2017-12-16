from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
import netsvc
import datetime as dt
import datetime
import base64

class kg_sale_invoice(osv.osv):
	
	_name = 'kg.sale.invoice'	
	_order = "name"	
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		pump_net_amount = spare_net_amount = access_net_amount = advance_net_amt = add_net_amount = net_amt = total_amt = 0.00
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'pump_net_amount': 0.0,
				'spare_net_amount': 0.0,
				'access_net_amount': 0.0,
				'net_amt': 0.0,				
				'total_amt': 0.0,
				'add_charge': 0.0,
				'advance_amt': 0.0,
			
			}
			
			cur = order.customer_id.property_product_pricelist_purchase.currency_id
			
			for line in order.line_ids:
				pump_net_amount += line.r_net_amount
				print"pump_net_amount",pump_net_amount	
				
			for line in order.line_ids_a:
				spare_net_amount += line.r_net_amount
				print"spare_net_amount",spare_net_amount	
				
			for line in order.line_ids_b:
				access_net_amount += line.r_net_amount
				print"access_net_amount",access_net_amount	
			for line in order.line_ids_c:
				add_net_amount += line.expense_amt
				print"add_net_amount",add_net_amount	
				
			for line in order.line_ids_d:					
				advance_net_amt += line.current_adv_amt 
				print"advance_net_amt",advance_net_amt	
				
			res[order.id]['pump_net_amount'] = pump_net_amount
			res[order.id]['spare_net_amount'] = spare_net_amount
			res[order.id]['access_net_amount'] = access_net_amount
			res[order.id]['add_charge'] = add_net_amount
			res[order.id]['advance_amt'] = advance_net_amt
			
			
			res[order.id]['net_amt'] = (pump_net_amount + spare_net_amount + access_net_amount + add_net_amount + order.round_off_amt) - advance_net_amt
			res[order.id]['total_amt'] = pump_net_amount + spare_net_amount + access_net_amount
			
		return res
	
	_columns = {

	'name': fields.char('Proforma Invoice No',size=128,readonly=True),
	'proforma_invoice_date': fields.date('Proforma Invoice Date'),
	'invoice_no': fields.char('Invoice No',size=128,readonly=True),
	'invoice_date': fields.date('Invoice Date',readonly=True),
	'contact_person': fields.char('Contact Person', size=128,readonly=True),
	'del_address': fields.many2one('kg.delivery.address', 'Delivery Address' ,domain="[('src_id','=',customer_id)]"),
	'billing_address': fields.many2one('kg.billing.address', 'Billing Address' ,domain="[('bill_id','=',customer_id)]"),
	'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('approved','Approved'),('invoice','Invoiced'),('cancel','Cancelled')],'Status', readonly=True),
	'customer_id': fields.many2one('res.partner','Customer Name',domain=[('customer','=',True)]),
	'accounts_state': fields.selection([('pending','Pending'),('received','Received')],'Accounts State', readonly=True),
	'balance_receivable': fields.float('Balance Receivable'),			
	
	
	
	'customer_po_no': fields.char('Customer PO No.',readonly=True),
	'cust_po_date': fields.date('Customer PO Date',readonly=True),
	
	'work_order_id': fields.many2one('kg.work.order','WO No.', domain="[('partner_id','=',customer_id),'&',('invoice_flag','=',False),'&', ('state','!=','draft'),'&', ('entry_mode','=','auto')]"),
	
	
	'round_off_amt': fields.float('Round off(+/-)' ),
	
	'pump_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),	
	'spare_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),	
	'access_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),
	
	'net_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True ,readonly=True),
	'total_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Amount',multi="sums",store=True ,readonly=True),
	'add_charge': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Additional Charges(+)',multi="sums",store=True ,readonly=True),
	'advance_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Adjected Advance Amount(-)',multi="sums",store=True ,readonly=True),
	
	'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
	
	'invoice_issue_date': fields.datetime('Invoice Issue Date'),
	'invoice_removal_date': fields.datetime('Invoice Removal Date'),
	'vehicle_no': fields.char('Vehicle No.',size=128),
	'place_of_supply': fields.char('Place Of Supply'),
	
	'bill_address':fields.text('Billing Address'),
	
	'delivery_address':fields.text('Delivery Address'),
	
	### Child Tables Declarations
	
	'line_ids':fields.one2many('ch.pumpspare.invoice', 'header_id', "Pump Invoice"),
	'line_ids_a': fields.one2many('ch.spare.invoice', 'header_id', "Spare Invoice"),
	'line_ids_b': fields.one2many('ch.accessories.invoice', 'header_id', "Accessories Invoice"),
	'line_ids_c': fields.one2many('ch.invoice.additional.charge', 'header_id', "Invoice Additional Charge"),
	'line_ids_d': fields.one2many('ch.customer.advance.invoice.line', 'header_id', "Invoice Advance Details"),
	'line_ids_e': fields.one2many('ch.customer.invoice.copy.rpt', 'header_id', "Invoice Copy Details"),
	'line_ids_f': fields.one2many('ch.annexure.invoice.copy.rpt', 'header_id', "Invoice Annexure Details"),
	
	}

	_defaults = {
	
		
		'proforma_invoice_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'invoice_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'state' : 'draft',
		'accounts_state': 'pending',
		'invoice_issue_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),		
		'invoice_removal_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),		
		
	}
	
	def onchange_customer_details(self,cr,uid,ids,customer_id,context=None):
		cust_rec = self.pool.get('res.partner').browse(cr,uid,customer_id)
		contact_person = ''		
		billing_address = ''		
		del_address = ''		
		values = {'contact_person':'','billing_address':'','del_address':'','place_of_supply':''}
		if cust_rec.id:
			for bill in cust_rec.billing_ids:	
				bill_ids = self.pool.get('kg.billing.address').search(cr, uid, [('bill_id','=',cust_rec.id),('default','=',True)])	
				if bill_ids:							
					bill_rec = self.pool.get('kg.billing.address').browse(cr, uid,bill_ids[0])			
					billing_address = bill_rec.id			
			for delivery in cust_rec.delivery_ids:
				del_ids = self.pool.get('kg.delivery.address').search(cr, uid, [('src_id','=',cust_rec.id),('default','=',True)])
				if del_ids:									
					del_rec = self.pool.get('kg.delivery.address').browse(cr, uid,del_ids[0])			
					del_address = del_rec.id				
			if cust_rec.contact_person :
				contact_person = cust_rec.contact_person
			place_of_supply_add = (cust_rec.city_id.name or '') +'-'+(cust_rec.zip or '' )
			values = {'contact_person':contact_person,'billing_address':billing_address,'del_address':del_address,'place_of_supply':place_of_supply_add}		
		return {'value' : values}
		
	def onchange_billing_details(self,cr,uid,ids,billing_address,context=None):
		bill_rec = self.pool.get('kg.billing.address').browse(cr,uid,billing_address)				
		values = {'bill_address':''}
		if bill_rec.id:
				
			bill_add = (bill_rec.name or '') +'\n' +(bill_rec.landmark or '' )+'\n'+(bill_rec.street or '' )+'\n'+(bill_rec.city_id.name or '' )+'\n'+(bill_rec.state_id.name or '' )+'\n'+(bill_rec.country_id.name or '' )+'\n'+(bill_rec.zip or '' )+'\n'+(str(bill_rec.contact_no) or '' )	
			values = {'bill_address':bill_add}		
		return {'value' : values}
		
	def onchange_del_details(self,cr,uid,ids,del_address,context=None):
		del_rec = self.pool.get('kg.delivery.address').browse(cr,uid,del_address)				
		values = {'delivery_address':''}
		if del_rec.id:			
			del_add = (del_rec.name or '') +'\n' +(del_rec.landmark or '' )+'\n'+(del_rec.street or '' )+'\n'+(del_rec.city_id.name or '' )+'\n'+(del_rec.state_id.name or '' )+'\n'+(del_rec.country_id.name or '' )+'\n'+(del_rec.zip or '' )+'\n'+(str(del_rec.contact_no) or '' )	
			values = {'delivery_address':del_add}		
		return {'value' : values}
	
	def load_wo_details(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		cr.execute(""" delete from ch_pumpspare_invoice where header_id  = %s """ %(ids[0]))
		cr.execute(""" delete from ch_spare_invoice where header_id  = %s """ %(ids[0]))		
		cr.execute(""" delete from ch_accessories_invoice where header_id  = %s """ %(ids[0]))			
		
		print"item",rec.work_order_id.id
		work_obj = self.pool.get('kg.work.order')
		work_rec = self.pool.get('kg.work.order').browse(cr,uid,rec.work_order_id.id)			
		for line in work_rec.line_ids:				
			if line.order_category == 'pump':						
				offer_rec = self.pool.get('ch.pump.offer').browse(cr,uid,line.pump_offer_line_id)
				offer_hea_rec = self.pool.get('kg.crm.offer').browse(cr,uid,offer_rec.header_id.id)
				
				if offer_rec.hsn_no.id is False:
					raise osv.except_osv(_('Warning!'),
						_('HSN Code not mapping in Pump Model!!'))
				else:
					
					list_id = []
					if rec.customer_id.state_id.code == 'TN':							
						if offer_rec.hsn_no.sgst_id.id:
							if offer_rec.hsn_no.sgst_id.id is False:
								raise osv.except_osv(_('Warning!'),
									_('Kindly map in HSN master SGST Tax!!'))
							else:									
								list_id.append(offer_rec.hsn_no.sgst_id.id)
						if offer_rec.hsn_no.cgst_id.id:
							if offer_rec.hsn_no.cgst_id.id is False:
								raise osv.except_osv(_('Warning!'),
									_('Kindly map in HSN master CGST Tax!!'))
							else:
								list_id.append(offer_rec.hsn_no.cgst_id.id)								
					else:
						if offer_rec.hsn_no.igst_id.id:
							if offer_rec.hsn_no.igst_id.id is False:
								raise osv.except_osv(_('Warning!'),
									_('Kindly map in HSN master IGST Tax!!'))
							else:
								list_id.append(offer_rec.hsn_no.igst_id.id)				
				if offer_rec.invoice_pending_qty > 0:				
					invoice_line = self.pool.get('ch.pumpspare.invoice').create(cr,uid,{
					   'header_id':rec.id,
					   'work_order_id':work_rec.id,
					   'order_line_id':line.id,
					   'pump_offer_id':offer_rec.id,
					   'pump_model_id':line.pump_model_id.id,
					   'order_category':line.order_category,
					   'qty':offer_rec.invoice_pending_qty,
					   'offer_qty':offer_rec.qty,
					   'pending_qty':offer_rec.invoice_pending_qty,					  
					   'prime_cost':offer_rec.prime_cost,
					   'per_pump_prime_cost':offer_rec.per_pump_prime_cost,
					   'sam_ratio':offer_rec.sam_ratio,
					   'dealer_discount':offer_rec.dealer_discount,
					   'customer_discount':offer_rec.customer_discount,
					   'special_discount':offer_rec.special_discount,					   
					   'p_f':offer_rec.p_f,
					   'freight':offer_rec.freight,
					   'insurance':offer_rec.insurance,
					   'net_offer_amt':offer_rec.r_net_amt_tot,
					   'net_amount':offer_rec.net_amount,
					   'r_net_amount':offer_rec.r_net_amount,
					   'tax_id':[(6, 0, [x for x in list_id])],
					   'hsn_no':offer_rec.hsn_no.id,
					   })
				   
			for access_line in line.line_ids_d:		
				offer_rec = self.pool.get('ch.accessories.offer').browse(cr,uid,access_line.access_offer_line_id)
				offer_hea_rec = self.pool.get('kg.crm.offer').browse(cr,uid,offer_rec.header_id.id)
				print"offer_rec.prime_costoffer_rec.prime_cost",offer_rec.prime_cost
				
				if offer_rec.hsn_no.id is False:
					raise osv.except_osv(_('Warning!'),
						_('HSN Code not mapping in Pump Model!!'))
				else:
					
					list_id = []
					if rec.customer_id.state_id.code == 'TN':							
						if offer_rec.hsn_no.sgst_id.id:
							if offer_rec.hsn_no.sgst_id.id is False:
								raise osv.except_osv(_('Warning!'),
									_('Kindly map in HSN master SGST Tax!!'))
							else:									
								list_id.append(offer_rec.hsn_no.sgst_id.id)
						if offer_rec.hsn_no.cgst_id.id:
							if offer_rec.hsn_no.cgst_id.id is False:
								raise osv.except_osv(_('Warning!'),
									_('Kindly map in HSN master CGST Tax!!'))
							else:
								list_id.append(offer_rec.hsn_no.cgst_id.id)								
					else:
						if offer_rec.hsn_no.igst_id.id:
							if offer_rec.hsn_no.igst_id.id is False:
								raise osv.except_osv(_('Warning!'),
									_('Kindly map in HSN master IGST Tax!!'))
							else:
								list_id.append(offer_rec.hsn_no.igst_id.id)
				if offer_rec.invoice_pending_qty > 0:						
					acc_line = self.pool.get('ch.accessories.invoice').create(cr,uid,{
					   'header_id':rec.id,
					   'acc_offer_id':offer_rec.id,
					   'work_order_id':work_rec.id,
					   'order_line_id':line.id,
					   'pump_id':line.pump_model_id.id,
					   'order_category':line.order_category,
					   'access_id':access_line.access_id.id,							   
					   'moc_id':access_line.moc_id.id,							   
					  
					   'qty':offer_rec.invoice_pending_qty,
					   'offer_qty':offer_rec.qty,
					   'pending_qty':offer_rec.invoice_pending_qty,			
					   'prime_cost':offer_rec.prime_cost,						   
					   'per_access_prime_cost':offer_rec.per_access_prime_cost,						   
					   'sam_ratio':offer_rec.sam_ratio,
					   'dealer_discount':offer_rec.dealer_discount,
					   'customer_discount':offer_rec.customer_discount,
					   'special_discount':offer_rec.special_discount,
					  
					   'p_f':offer_rec.p_f,
					   'freight':offer_rec.freight,
					   'insurance':offer_rec.insurance,
					   'net_acc_amt':offer_rec.r_net_amt_tot,
					   'net_amount':offer_rec.r_net_amt_tot,
					   'r_net_amount':offer_rec.r_net_amount,
					   'tax_id':[(6, 0, [x for x in list_id])],
					   'hsn_no':offer_rec.hsn_no.id,
					   'off_name':offer_rec.off_name,	
					   })					   
				
				self.write(cr, uid, ids, {'customer_po_no':offer_hea_rec.customer_po_no,
									'cust_po_date': offer_hea_rec.cust_po_date,})
			
			if line.order_category == 'spare':					
				for bom_line in line.line_ids:								
					offer_rec = self.pool.get('ch.spare.offer').browse(cr,uid,bom_line.spare_offer_line_id)	
					offer_hea_rec = self.pool.get('kg.crm.offer').browse(cr,uid,offer_rec.header_id.id)
					if offer_rec.hsn_no.id is False:
						raise osv.except_osv(_('Warning!'),
							_('HSN Code not mapping in Pump Model!!'))
					else:
						
						list_id = []
						if rec.customer_id.state_id.code == 'TN':							
							if offer_rec.hsn_no.sgst_id.id:
								if offer_rec.hsn_no.sgst_id.id is False:
									raise osv.except_osv(_('Warning!'),
										_('Kindly map in HSN master SGST Tax!!'))
								else:									
									list_id.append(offer_rec.hsn_no.sgst_id.id)
							if offer_rec.hsn_no.cgst_id.id:
								if offer_rec.hsn_no.cgst_id.id is False:
									raise osv.except_osv(_('Warning!'),
										_('Kindly map in HSN master CGST Tax!!'))
								else:
									list_id.append(offer_rec.hsn_no.cgst_id.id)								
						else:
							if offer_rec.hsn_no.igst_id.id:
								if offer_rec.hsn_no.igst_id.id is False:
									raise osv.except_osv(_('Warning!'),
										_('Kindly map in HSN master IGST Tax!!'))
								else:
									list_id.append(offer_rec.hsn_no.igst_id.id)
					if offer_rec.invoice_pending_qty > 0:									
						invoice_line = self.pool.get('ch.spare.invoice').create(cr,uid,{
						   'header_id':rec.id,
						   'spare_offer_id':offer_rec.id,
						   'work_order_id':work_rec.id,
						   'order_line_id':line.id,
						   'pump_id':line.pump_model_id.id,
						   'order_category':line.order_category,
						   'pattern_id':bom_line.pattern_id.id,
						   'item_name':bom_line.pattern_id.name,
						   'item_code':bom_line.pattern_id.pattern_name,
						   'moc_id':bom_line.moc_id.id,
						   'qty':offer_rec.invoice_pending_qty,
						   'offer_qty':offer_rec.qty,
						   'pending_qty':offer_rec.invoice_pending_qty,								  
						   'per_prime_cost':offer_rec.prime_cost,						   
						   'prime_cost':offer_rec.prime_cost,						   
						   'sam_ratio':offer_rec.sam_ratio,
						   'dealer_discount':offer_rec.dealer_discount,
						   'customer_discount':offer_rec.customer_discount,
						   'special_discount':offer_rec.special_discount,						   
						   'p_f':offer_rec.p_f,
						   'freight':offer_rec.freight,
						   'insurance':offer_rec.insurance,
						   'net_spare_amt':offer_rec.r_net_amt_tot,
						   'r_net_amount':offer_rec.r_net_amount,
						   'net_amount':offer_rec.r_net_amt_tot,
						   'tax_id':[(6, 0, [x for x in list_id])],
						   'hsn_no':offer_rec.hsn_no.id,
						   'off_name':offer_rec.off_name,				  
						   })						
					
				for machine_shop_line in line.line_ids_a:
					print"machine_shop_line.spare_offer_line_id",machine_shop_line.spare_offer_line_id	
					offer_rec = self.pool.get('ch.spare.offer').browse(cr,uid,machine_shop_line.spare_offer_line_id)
					offer_hea_rec = self.pool.get('kg.crm.offer').browse(cr,uid,offer_rec.header_id.id)
					if offer_rec.hsn_no.id is False:
						raise osv.except_osv(_('Warning!'),
							_('HSN Code not mapping in Pump Model!!'))
					else:
						
						list_id = []
						if rec.customer_id.state_id.code == 'TN':							
							if offer_rec.hsn_no.sgst_id.id:
								if offer_rec.hsn_no.sgst_id.id is False:
									raise osv.except_osv(_('Warning!'),
										_('Kindly map in HSN master SGST Tax!!'))
								else:									
									list_id.append(offer_rec.hsn_no.sgst_id.id)
							if offer_rec.hsn_no.cgst_id.id:
								if offer_rec.hsn_no.cgst_id.id is False:
									raise osv.except_osv(_('Warning!'),
										_('Kindly map in HSN master CGST Tax!!'))
								else:
									list_id.append(offer_rec.hsn_no.cgst_id.id)								
						else:
							if offer_rec.hsn_no.igst_id.id:
								if offer_rec.hsn_no.igst_id.id is False:
									raise osv.except_osv(_('Warning!'),
										_('Kindly map in HSN master IGST Tax!!'))
								else:
									list_id.append(offer_rec.hsn_no.igst_id.id)
					if offer_rec.invoice_pending_qty > 0:								
						machine_shop_line = self.pool.get('ch.spare.invoice').create(cr,uid,{
						   'header_id':rec.id,
						   'spare_offer_id':offer_rec.id,
						   'work_order_id':work_rec.id,
						   'order_line_id':line.id,
						   'pump_id':line.pump_model_id.id,
						   'order_category':line.order_category,
						   'ms_id':machine_shop_line.ms_id.id,							   
						   'moc_id':machine_shop_line.moc_id.id,
						   'item_name':machine_shop_line.ms_id.name,
						   'item_code':machine_shop_line.ms_id.code,
						   
						   'qty':offer_rec.invoice_pending_qty,
						   'offer_qty':offer_rec.qty,
						   'pending_qty':offer_rec.invoice_pending_qty,	
						   'per_prime_cost':offer_rec.prime_cost,			
						   'prime_cost':offer_rec.prime_cost,						   
						   'sam_ratio':offer_rec.sam_ratio,
						   'dealer_discount':offer_rec.dealer_discount,
						   'customer_discount':offer_rec.customer_discount,
						   'special_discount':offer_rec.special_discount,
						  
						   'p_f':offer_rec.p_f,
						   'freight':offer_rec.freight,
						   'insurance':offer_rec.insurance,
						   'net_spare_amt':offer_rec.r_net_amt_tot,
						   'r_net_amount':offer_rec.r_net_amount,
						   'net_amount':offer_rec.r_net_amt_tot,
						   'tax_id':[(6, 0, [x for x in list_id])],
						   'hsn_no':offer_rec.hsn_no.id,
						   'off_name':offer_rec.off_name,	
						   })
					   
				for bot_line in line.line_ids_b:
					print"bot_line.spare_offer_line_id",bot_line.spare_offer_line_id	
					offer_rec = self.pool.get('ch.spare.offer').browse(cr,uid,bot_line.spare_offer_line_id)
					offer_hea_rec = self.pool.get('kg.crm.offer').browse(cr,uid,offer_rec.header_id.id)
					
					if offer_rec.hsn_no.id is False:
						raise osv.except_osv(_('Warning!'),
							_('HSN Code not mapping in Pump Model!!'))
					else:
						
						list_id = []
						if rec.customer_id.state_id.code == 'TN':							
							if offer_rec.hsn_no.sgst_id.id:
								if offer_rec.hsn_no.sgst_id.id is False:
									raise osv.except_osv(_('Warning!'),
										_('Kindly map in HSN master SGST Tax!!'))
								else:									
									list_id.append(offer_rec.hsn_no.sgst_id.id)
							if offer_rec.hsn_no.cgst_id.id:
								if offer_rec.hsn_no.cgst_id.id is False:
									raise osv.except_osv(_('Warning!'),
										_('Kindly map in HSN master CGST Tax!!'))
								else:
									list_id.append(offer_rec.hsn_no.cgst_id.id)								
						else:
							if offer_rec.hsn_no.igst_id.id:
								if offer_rec.hsn_no.igst_id.id is False:
									raise osv.except_osv(_('Warning!'),
										_('Kindly map in HSN master IGST Tax!!'))
								else:
									list_id.append(offer_rec.hsn_no.igst_id.id)
					
					if offer_rec.invoice_pending_qty > 0:									
						bot_line = self.pool.get('ch.spare.invoice').create(cr,uid,{
						   'header_id':rec.id,
						   'spare_offer_id':offer_rec.id,
						   'work_order_id':work_rec.id,
						   'order_line_id':line.id,
						   'pump_id':line.pump_model_id.id,
						   'order_category':line.order_category,
						   'bot_id':bot_line.bot_id.id,
						   'item_name':bot_line.bot_id.name,
						   'item_code':bot_line.bot_id.code,								  
						   'moc_id':bot_line.moc_id.id,
						  
						   'qty':offer_rec.invoice_pending_qty,
						   'offer_qty':offer_rec.qty,
						   'pending_qty':offer_rec.invoice_pending_qty,
						   'per_prime_cost':offer_rec.prime_cost,				
						   'prime_cost':offer_rec.prime_cost,						   
						   'sam_ratio':offer_rec.sam_ratio,
						   'dealer_discount':offer_rec.dealer_discount,
						   'customer_discount':offer_rec.customer_discount,
						   'special_discount':offer_rec.special_discount,
						   
						   'p_f':offer_rec.p_f,
						   'freight':offer_rec.freight,
						   'insurance':offer_rec.insurance,
						   'net_spare_amt':offer_rec.r_net_amt_tot,
						   'net_amount':offer_rec.r_net_amt_tot,
						   'r_net_amount':offer_rec.r_net_amount,
						   'tax_id':[(6, 0, [x for x in list_id])],
						   'hsn_no':offer_rec.hsn_no.id,
						   'off_name':offer_rec.off_name,	
							})
						
				self.write(cr, uid, ids, {'customer_po_no':offer_hea_rec.customer_po_no,
									'cust_po_date': offer_hea_rec.cust_po_date,})
							   
			if line.order_category == 'access':											
					
					for access_line in line.line_ids_d:		
						offer_rec = self.pool.get('ch.accessories.offer').browse(cr,uid,access_line.access_offer_line_id)
						offer_hea_rec = self.pool.get('kg.crm.offer').browse(cr,uid,offer_rec.header_id.id)
						print"offer_rec.prime_costoffer_rec.prime_cost",offer_rec.prime_cost
						
						if offer_rec.hsn_no.id is False:
							raise osv.except_osv(_('Warning!'),
								_('HSN Code not mapping in Pump Model!!'))
						else:
							
							list_id = []
							if rec.customer_id.state_id.code == 'TN':							
								if offer_rec.hsn_no.sgst_id.id:
									if offer_rec.hsn_no.sgst_id.id is False:
										raise osv.except_osv(_('Warning!'),
											_('Kindly map in HSN master SGST Tax!!'))
									else:									
										list_id.append(offer_rec.hsn_no.sgst_id.id)
								if offer_rec.hsn_no.cgst_id.id:
									if offer_rec.hsn_no.cgst_id.id is False:
										raise osv.except_osv(_('Warning!'),
											_('Kindly map in HSN master CGST Tax!!'))
									else:
										list_id.append(offer_rec.hsn_no.cgst_id.id)								
							else:
								if offer_rec.hsn_no.igst_id.id:
									if offer_rec.hsn_no.igst_id.id is False:
										raise osv.except_osv(_('Warning!'),
											_('Kindly map in HSN master IGST Tax!!'))
									else:
										list_id.append(offer_rec.hsn_no.igst_id.id)
										
						if offer_rec.invoice_pending_qty > 0:						
							acc_line = self.pool.get('ch.accessories.invoice').create(cr,uid,{
							   'header_id':rec.id,
							   'acc_offer_id':offer_rec.id,
							   'work_order_id':work_rec.id,
							   'order_line_id':line.id,
							   'pump_id':line.pump_model_id.id,
							   'order_category':line.order_category,
							   'access_id':access_line.access_id.id,							   
							   'moc_id':access_line.moc_id.id,							   
							  
							   'qty':offer_rec.invoice_pending_qty,
							   'offer_qty':offer_rec.qty,
							   'pending_qty':offer_rec.invoice_pending_qty,			
							   'prime_cost':offer_rec.prime_cost,						   
							   'per_access_prime_cost':offer_rec.per_access_prime_cost,						   
							   'sam_ratio':offer_rec.sam_ratio,
							   'dealer_discount':offer_rec.dealer_discount,
							   'customer_discount':offer_rec.customer_discount,
							   'special_discount':offer_rec.special_discount,
							  
							   'p_f':offer_rec.p_f,
							   'freight':offer_rec.freight,
							   'insurance':offer_rec.insurance,
							   'net_acc_amt':offer_rec.r_net_amt_tot,
							   'net_amount':offer_rec.r_net_amt_tot,
							   'r_net_amount':offer_rec.r_net_amount,
							   'tax_id':[(6, 0, [x for x in list_id])],
							   'hsn_no':offer_rec.hsn_no.id,
							   'off_name':offer_rec.off_name,	
							   })					   
														   
					self.write(cr, uid, ids, {'customer_po_no':offer_hea_rec.customer_po_no,'cust_po_date': offer_hea_rec.cust_po_date,})	   
				
			else:
				pass
					
	def update_actual_values(self, cr, uid, ids,context=None):
		invoice_rec = self.browse(cr,uid,ids[0])		
		pump_net_amount = spare_net_amount = access_net_amount = advance_net_amt = add_net_amount = net_amt = total_amt = 0.00
		for order in self.browse(cr, uid, ids, context=context):		
			
			for line in order.line_ids:
				pump_net_amount += line.net_amount
				print"pump_net_amount",pump_net_amount	
				
			for line in order.line_ids_a:
				spare_net_amount += line.net_amount
				print"spare_net_amount",spare_net_amount	
				
			for line in order.line_ids_b:
				access_net_amount += line.net_amount
				print"access_net_amount",access_net_amount	
			for line in order.line_ids_c:
				add_net_amount += line.expense_amt
				print"add_net_amount",add_net_amount	
				
			for line in order.line_ids_d:					
				advance_net_amt += line.current_adv_amt 
				print"advance_net_amt",advance_net_amt				
		
		self.write(cr, uid, ids[0], {
					'pump_net_amount': pump_net_amount,
					'spare_net_amount': spare_net_amount,
					'access_net_amount':access_net_amount,
					'add_charge':add_net_amount,
					'advance_amt' : advance_net_amt, 
					'net_amt' : (pump_net_amount + spare_net_amount + access_net_amount + add_net_amount + order.round_off_amt) - advance_net_amt, 					
					'total_amt' : pump_net_amount + spare_net_amount + access_net_amount, 
					})
			

		return True	
					
	def invoice_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		
		work_obj = self.pool.get('kg.work.order')
		work_rec = self.pool.get('kg.work.order').browse(cr,uid,rec.work_order_id.id)
		crm_offer_id = self.pool.get('kg.crm.offer').search(cr, uid, [('name','=',work_rec.offer_no)])	
		
		if rec.state == 'draft':					
			print"crm_offer_id",crm_offer_id[0]
			for offer_invoice in rec.line_ids:
				if offer_invoice.qty > offer_invoice.pump_offer_id.invoice_pending_qty:
					raise osv.except_osv(_('Warning!'),_('Excess qty not allowd'))
				else:					
					self.pool.get('ch.pump.offer').write(cr,uid,offer_invoice.pump_offer_id.id,{'invoice_pending_qty':offer_invoice.pump_offer_id.invoice_pending_qty - offer_invoice.qty})				
			for spare_invoice in rec.line_ids_a:
				if spare_invoice.qty > spare_invoice.spare_offer_id.invoice_pending_qty:
					raise osv.except_osv(_('Warning!'),_('Excess qty not allowd'))
				else:					
					self.pool.get('ch.spare.offer').write(cr,uid,spare_invoice.spare_offer_id.id,{'invoice_pending_qty':spare_invoice.spare_offer_id.invoice_pending_qty - spare_invoice.qty})				
			for acc_invoice in rec.line_ids_b:
				if acc_invoice.qty > acc_invoice.acc_offer_id.invoice_pending_qty:
					raise osv.except_osv(_('Warning!'),_('Excess qty not allowd'))
				else:					
					self.pool.get('ch.accessories.offer').write(cr,uid,acc_invoice.acc_offer_id.id,{'invoice_pending_qty':acc_invoice.acc_offer_id.invoice_pending_qty - acc_invoice.qty})				
			
			cr.execute(''' 
				select sum(pending_qty) as qty from (
				select invoice_pending_qty as pending_qty
				from ch_pump_offer
				where header_id = %s 
				union all
				select invoice_pending_qty as pending_qty
				from ch_spare_offer
				where header_id = %s 
				union all
				select invoice_pending_qty as pending_qty
				from ch_accessories_offer
				where header_id = %s ) as test ''',[crm_offer_id[0],crm_offer_id[0],crm_offer_id[0]])
				
			pending_qty_details = cr.dictfetchall()	
			
			print"pending_qty_details",pending_qty_details[0]['qty']
			
			if pending_qty_details[0]['qty'] == 0:
			
				work_obj.write(cr, uid, work_rec.id, {'invoice_flag': True})
			
			if rec.name == False:					
				proforma_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.proforma.invoice')])
				proforma_rec = self.pool.get('ir.sequence').browse(cr,uid,proforma_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(proforma_id[0],proforma_rec.code,rec.invoice_date))
				proforma_name = cr.fetchone();	
			
			if rec.line_ids_d:
				for line in rec.line_ids_d:
					print"line",line
					cus_advance_line_rec = self.pool.get('kg.customer.advance').browse(cr, uid, line.cus_advance_id.id)
					cus_advance_bal_amt = cus_advance_line_rec.bal_adv - line.current_adv_amt				
					cus_advance_line_rec.write({'bal_adv':cus_advance_bal_amt})				
			self.write(cr, uid, ids, {'state': 'confirmed','name':proforma_name[0]})
		return True
		
	def invoice_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			cus_adv_obj = self.pool.get('kg.customer.advance')			
			cus_adv_inv_obj = self.pool.get('ch.customer.advance.invoice.line')				
			work_rec = self.pool.get('kg.work.order').browse(cr,uid,rec.work_order_id.id)				
			for line in rec.line_ids_d:	
				print"line.order_id",line.order_id
				adv_ids = self.pool.get('kg.customer.advance').search(cr, uid, [('order_id','=',line.order_id.id)])
				print"adv_ids",adv_ids							
				adv_rec = self.pool.get('kg.customer.advance').browse(cr, uid,adv_ids[0])				
				adjusted_amt = adv_rec.adjusted_amt + line.current_adv_amt 
				balance_amt = line.current_adv_amt - adjusted_amt
				cus_adv_obj.write(cr, uid, line.cus_advance_id.id, {'adjusted_amt': adjusted_amt,'balance_amt':balance_amt})	
			self.write(cr, uid, ids, {'state': 'approved'})
		return True
		
	def invoice_process(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':		
			invoice_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.sale.invoice')])
			invoice_rec = self.pool.get('ir.sequence').browse(cr,uid,invoice_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(invoice_id[0],invoice_rec.code,rec.invoice_date))
			invoice_name = cr.fetchone();			
			
			self.write(cr, uid, ids, {'state': 'invoice','invoice_no':invoice_name[0],'balance_receivable':rec.net_amt})
		return True
	
	def load_advance(self, cr, uid, ids,context=None):
		invoice_rec = self.browse(cr,uid,ids[0])
		cus_adv_obj = self.pool.get('kg.customer.advance')		
		cus_inadv_obj = self.pool.get('ch.customer.advance.invoice.line')	
		del_sql = """delete from ch_customer_advance_invoice_line where header_id=%s"""%(ids[0])
		cr.execute(del_sql)					
		work_rec = self.pool.get('kg.work.order').browse(cr,uid,invoice_rec.work_order_id.id)			
		adv_search = self.pool.get('kg.customer.advance').search(cr, uid, [('order_id','=',work_rec.id)])
		cr.execute(""" select * from kg_customer_advance where order_id = %s and balance_amt > 0 and state='done'""" %(work_rec.id))
		adv_data = cr.dictfetchall()			
		for adv in adv_data:
			cus_inadv_obj.create(cr,uid,{
				'order_id' : adv['order_id'],
				'cus_advance_id' : adv['id'],
				'cus_advance_date' : adv['advance_date'],
				'tot_advance_amt' : adv['advance_amt'],
				'balance_amt' : adv['balance_amt'],
				'current_adv_amt' : 0.0,
				'header_id' : invoice_rec.id,
				})
				
		return True
		
		
	def load_invoice_copy(self, cr, uid, ids,context=None):
		invoice_rec = self.browse(cr,uid,ids[0])		
		cus_invcopy_obj = self.pool.get('ch.customer.invoice.copy.rpt')	
		del_sql = """delete from ch_customer_invoice_copy_rpt where header_id=%s"""%(ids[0])
		cr.execute(del_sql)
		for item in invoice_rec.line_ids:		
			
			cus_invcopy_obj.create(cr,uid,{
				'header_id' : invoice_rec.id,
				'description' : item.pump_model_id.name,
				'hsn_id' : item.hsn_no.id,
				'qty' : item.qty,
				'unit_price' : item.net_offer_amt/item.offer_qty,
				'deductions' : 0.0,
				'additions' : 0.0,
				'taxable_value' : item.net_offer_amt/item.offer_qty,
				'total_taxable_value' : item.net_offer_amt/item.offer_qty,
				})
				
		for item in invoice_rec.line_ids_a:		
			
			cus_invcopy_obj.create(cr,uid,{
				'header_id' : invoice_rec.id,
				'description' : item.pump_id.name,
				'hsn_id' : item.hsn_no.id,
				'qty' : item.qty,
				'unit_price' : item.net_spare_amt/item.offer_qty,
				'deductions' : 0.0,
				'additions' : 0.0,
				'taxable_value' : item.net_spare_amt/item.offer_qty,
				'total_taxable_value' : item.net_spare_amt/item.offer_qty,
				})
		for item in invoice_rec.line_ids_b:		
			
			cus_invcopy_obj.create(cr,uid,{
				'header_id' : invoice_rec.id,
				'description' : item.pump_id.name,
				'hsn_id' : item.hsn_no.id,
				'qty' : item.qty,
				'unit_price' : item.net_acc_amt/item.offer_qty,
				'deductions' : 0.0,
				'additions' : 0.0,
				'taxable_value' : item.net_acc_amt/item.offer_qty,
				'total_taxable_value' : item.net_acc_amt/item.offer_qty,
				})
				
		return True
		
	def load_annexure_copy(self, cr, uid, ids,context=None):
		invoice_rec = self.browse(cr,uid,ids[0])		
		cus_invanne_obj = self.pool.get('ch.annexure.invoice.copy.rpt')	
		product_uom_id = self.pool.get('product.uom').search(cr, uid, [('name','=','Nos')])		
		del_sql = """delete from ch_annexure_invoice_copy_rpt where header_id=%s"""%(ids[0])
		cr.execute(del_sql)
		for item in invoice_rec.line_ids:		
			
			cus_invanne_obj.create(cr,uid,{
				'header_id' : invoice_rec.id,				
				'hsn_id' : item.hsn_no.id,
				'hsn_code' : item.hsn_no.name,
				'item_code' : item.pump_model_id.name,
				'tag_no' : item.pump_offer_id.enquiry_line_id.equipment_no,
				'description' : item.pump_offer_id.enquiry_line_id.description,
				'pump_model_id' : item.pump_model_id.id,
				'pump_serial_no' : item.pump_offer_id.enquiry_line_id.s_no,
				'qty' : item.qty,
				'uom_id' : product_uom_id[0],
				'each_price' : item.net_offer_amt/item.offer_qty,
				'total_value' : (item.net_offer_amt/item.offer_qty) * item.qty,
				
				})
				
		for item in invoice_rec.line_ids_a:		
			
			cus_invanne_obj.create(cr,uid,{
				'header_id' : invoice_rec.id,				
				'hsn_id' : item.hsn_no.id,
				'hsn_code' : item.hsn_no.name,
				'item_code' : item.pump_id.name,
				'tag_no' : item.spare_offer_id.enquiry_line_id.equipment_no,
				'description' : item.spare_offer_id.enquiry_line_id.description,
				'pump_model_id' : item.pump_id.id,
				'pump_serial_no' : item.spare_offer_id.enquiry_line_id.s_no,
				'qty' : item.qty,
				'uom_id' : product_uom_id[0],
				'each_price' : item.net_spare_amt/item.offer_qty,
				'total_value' : (item.net_spare_amt/item.offer_qty) * item.qty,
				})
		for item in invoice_rec.line_ids_b:		
			
			cus_invanne_obj.create(cr,uid,{
				'header_id' : invoice_rec.id,				
				'hsn_id' : item.hsn_no.id,
				'hsn_code' : item.hsn_no.name,
				'item_code' : item.pump_id.name,
				'tag_no' : item.acc_offer_id.enquiry_line_id.equipment_no,
				'description' : item.acc_offer_id.enquiry_line_id.description,
				'pump_model_id' : item.pump_id.id,
				'pump_serial_no' : item.acc_offer_id.enquiry_line_id.s_no,
				'qty' : item.qty,
				'uom_id' : product_uom_id[0],
				'each_price' : item.net_acc_amt/item.offer_qty,
				'total_value' : (item.net_acc_amt/item.offer_qty) * item.qty,
				})
				
				
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
	
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_code = str(rec.name)		
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
	
		if rec.state == 'invoice':
			
			url = 'http://10.100.9.32/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&customer_invoice='+rec_code
		
		else:

			url = 'http://10.100.9.32/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&proforma_invoice='+rec_code

		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
					
	
kg_sale_invoice()



class ch_pumpspare_invoice(osv.osv):

	_name = "ch.pumpspare.invoice"
	_description = "Pump Spare Invoice"
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		prime_cost = net_amount = val = tax_tot = r_net_amount = 0		
		for line in self.browse(cr, uid, ids, context=context):
			
			res[line.id] = {
				
				'prime_cost': 0.0,
				'net_amount': 0.0,
				'tax_tot': 0.0,
				'r_net_amount' : 0.0,
				
				
			}
			
			for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id,
				line.net_offer_amt/line.offer_qty, line.qty,1,1)['taxes']:				
				val += c.get('amount', 0.0)				
				tax_tot = val	
			
			net_amount = (line.net_offer_amt/line.offer_qty) * line.qty
			net_grand_amount = net_amount + tax_tot			
			prime_cost = line.per_pump_prime_cost * line.qty
			
			res[line.id]['prime_cost'] = prime_cost
			res[line.id]['net_amount'] = net_amount
			res[line.id]['tax_tot'] = tax_tot
			res[line.id]['r_net_amount'] = net_grand_amount
			
			
		return res
	
	
	_columns = {
	
		'header_id':fields.many2one('kg.sale.invoice', 'Invoice Detail', required=1, ondelete='cascade'),
		'pump_offer_id':fields.many2one('ch.pump.offer', 'Offer'),	
		'work_order_id':fields.many2one('kg.work.order', 'Work Order'),	
		'order_line_id': fields.many2one('ch.work.order.details','Order Line'),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True,domain="[('active','=','t')]"),		
		'order_category': fields.selection([('pump','Pump'),('spare','Spare')],'Purpose', required=True),
		'qty': fields.integer('Qty', required=True),
		'offer_qty': fields.integer('Offer Qty'),
		'pending_qty': fields.integer('Pending Qty'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'note': fields.text('Notes'),
		'remarks': fields.text('Approve/Reject Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),	
		
		'hsn_no': fields.many2one('kg.hsn.master','HSN No.'),
		'tax_id': fields.many2many('account.tax', 'pump_invoice_taxes', 'pump_invoice_id', 'tax_id', 'GST Taxes'),
		
		
		### Used for value		
		
		'per_pump_prime_cost': fields.float('Per Pump Prime Cost'),
		'sam_ratio': fields.float('Sam Ratio(%)'),
		'dealer_discount': fields.float('Dealer Discount(%)'),
		'customer_discount': fields.float('Customer Discount(%)'),
		'special_discount': fields.float('Special Discount(%)'),		
		'p_f': fields.float('P&F(%)'),
		'freight': fields.float('Freight(%)'),
		'insurance': fields.float('Insurance(%)'),
		'net_offer_amt': fields.float('Net Offer Amount'),
		
		### Function used value update
		
		'prime_cost': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Prime Cost',multi="sums",store=True),		
		
		'tax_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax',multi="sums",store=True),	
		
		'net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),
		
		'r_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Grand Total',multi="sums",store=True),	
		
		
		
	}
	
	
	_defaults = {
	
		'state': 'draft',	
		
	}
	
	
ch_pumpspare_invoice()


class ch_spare_invoice(osv.osv):	
		
	_name = "ch.spare.invoice"
	_description = "Ch Spare Invoice"
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		prime_cost = net_amount = val = tax_tot = r_net_amount = 0		
		for line in self.browse(cr, uid, ids, context=context):
			
			res[line.id] = {
				
				'prime_cost': 0.0,
				'net_amount': 0.0,
				'tax_tot': 0.0,
				'r_net_amount' : 0.0,
				
				
			}
			
			for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id,
				line.net_offer_amt/line.offer_qty, line.qty,1,1)['taxes']:				
				val += c.get('amount', 0.0)				
				tax_tot = val	
			
			net_amount = (line.net_offer_amt/line.offer_qty) * line.qty
			net_grand_amount = net_amount + tax_tot			
			per_prime_cost = line.per_prime_cost / line.offer_qty
			prime_cost = per_prime_cost / line.qty
			
			res[line.id]['prime_cost'] = prime_cost
			res[line.id]['net_amount'] = net_amount
			res[line.id]['tax_tot'] = tax_tot
			res[line.id]['r_net_amount'] = net_grand_amount
			
			
		return res
	
	_columns = {
	
		### Pump Details ####
		'header_id':fields.many2one('kg.sale.invoice', 'Offer', ondelete='cascade'),
		'spare_offer_id':fields.many2one('ch.spare.offer', 'Offer'),	
		'work_order_id':fields.many2one('kg.work.order', 'Offer'),	
		'order_line_id': fields.many2one('ch.work.order.details','Order Line'),		
		'qty':fields.integer('Quantity'),
		'offer_qty': fields.integer('Offer Qty'),
		'pending_qty': fields.integer('Pending Qty'),
		'item_code': fields.char('Item Code'),
		'item_name': fields.char('Item Name'),
		'moc_id': fields.many2one('kg.moc.master','MOC Name'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No'),
		'ms_id': fields.many2one('kg.machine.shop','MS Name'),
		'bot_id': fields.many2one('kg.machine.shop','BOT Name'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),	
			
		'off_name': fields.char('Offer Name'),
		'hsn_no': fields.many2one('kg.hsn.master','HSN No.'),
		'tax_id': fields.many2many('account.tax', 'spare_invoice_taxes', 'spare_invoice_id', 'tax_id', 'GST Taxes'),
		
		### Used for value		
		
		'sam_ratio': fields.float('Sam Ratio(%)'),
		'dealer_discount': fields.float('Dealer Discount(%)'),
		'customer_discount': fields.float('Customer Discount(%)'), 
		'special_discount': fields.float('Special Discount(%)'),		
		'p_f': fields.float('P&F(%)'),
		'freight': fields.float('Freight(%)'),
		'insurance': fields.float('Insurance(%)'),
		'net_spare_amt': fields.float('Total Price'),	
		'per_prime_cost': fields.float('Refer Prime cost'),	
		
		### Function used value update
		'prime_cost': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Prime Cost',multi="sums",store=True),		
		
		'tax_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax',multi="sums",store=True),	
		
		'net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),
		
		'r_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Grand Total',multi="sums",store=True),		
		
		
	}
	

ch_spare_invoice()


class ch_accessories_invoice(osv.osv):	
	
		
	_name = "ch.accessories.invoice"
	_description = "Ch Accessories Invoice"
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		prime_cost = net_amount = val = tax_tot = r_net_amount = 0		
		for line in self.browse(cr, uid, ids, context=context):
			
			res[line.id] = {
				
				'prime_cost': 0.0,
				'net_amount': 0.0,
				'tax_tot': 0.0,
				'r_net_amount' : 0.0,
				
				
			}
			
			for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id,
				line.net_acc_amt/line.offer_qty, line.qty,1,1)['taxes']:				
				val += c.get('amount', 0.0)				
				tax_tot = val	
			
			net_amount = (line.net_acc_amt/line.offer_qty) * line.qty
			net_grand_amount = net_amount + tax_tot			
			prime_cost = line.per_access_prime_cost * line.qty
			
			res[line.id]['prime_cost'] = prime_cost
			res[line.id]['net_amount'] = net_amount
			res[line.id]['tax_tot'] = tax_tot
			res[line.id]['r_net_amount'] = net_grand_amount
			
			
		return res
	
	_columns = {
	
		### Spare Details ####
		'header_id':fields.many2one('kg.sale.invoice', 'Invoice', ondelete='cascade'),
		'acc_offer_id':fields.many2one('ch.accessories.offer', 'Offer'),	
		'work_order_id':fields.many2one('kg.work.order', 'Offer'),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line'),
		'access_id':fields.many2one('kg.accessories.master', 'Item Name'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),
		'moc_id':fields.many2one('kg.moc.master', 'MOC'),
		'qty':fields.integer('Quantity'),
		'offer_qty': fields.integer('Offer Qty'),
		'pending_qty': fields.integer('Pending Qty'),
		
		'off_name': fields.char('Offer Name'),
		'hsn_no': fields.many2one('kg.hsn.master','HSN No.'),
		'tax_id': fields.many2many('account.tax', 'acc_invoice_taxes', 'acc_invoice_id', 'tax_id', 'GST Taxes'),
		
		### Used for value		
		'per_access_prime_cost': fields.float('Per Access Prime Cost'),
		'sam_ratio': fields.float('Sam Ratio(%)'),
		'dealer_discount': fields.float('Dealer Discount(%)'),
		'customer_discount': fields.float('Customer Discount(%)'),
		'special_discount': fields.float('Special Discount(%)'),		
		'p_f': fields.float('P&F(%)'),
		'freight': fields.float('Freight(%)'),
		'insurance': fields.float('Insurance(%)'),
		'pump_price': fields.float('Pump Price'),
		'total_price': fields.float('Total Price'),
		'net_acc_amt': fields.float('Total Acc Price'),	
		
		### Function used value update
		'prime_cost': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Prime Cost',multi="sums",store=True),		
		
		'tax_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax',multi="sums",store=True),	
		
		'net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),
		
		'r_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Grand Total',multi="sums",store=True),
			
		
		
	}
	
ch_accessories_invoice()	



class ch_invoice_additional_charge(osv.osv):

	_name = "ch.invoice.additional.charge"
	_description = "Invoice Additional Charge Track"
	
	
	def _get_total_amt(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		ed_total_val = 0
		ed_total = 0
		sale_total = 0
		service_total = 0
		
		for entry in self.browse(cr, uid, ids, context=context):
			total_value = entry.amount		
			amount = entry.amount
			tax_total= 0.00		
			for item in [x.id for x in entry.tax_id]:				
				tax_rec = self.pool.get('account.tax').browse(cr,uid,item)											
				tax_amt = (amount/100.00)*(tax_rec.amount*100.00)
				tax_total += tax_amt
				print"tax_total",tax_total					
			if tax_total:						
				total_value += tax_total
					
			else:
				pass
			
			result[entry.id] = total_value
		return result
	
	_columns = {
		
		'header_id': fields.many2one('kg.sale.invoice', 'Additional Charge Track'),
		'name': fields.char('Number', size=128, select=True,readonly=False),
		'date': fields.date('Creation Date'),
		'amount': fields.float('Amount'),		
		'tax_id': fields.many2many('account.tax', 'invoice_order_expense_tax', 'ord_id', 'tax_id', 'Tax' ,domain=[('active','=','t')]),
		'company_id': fields.many2one('res.company', 'Company Name'),
		'description': fields.char('Description'),		
		'expense_amt': fields.function(_get_total_amt, string='Total Amount',digits=(16,2), method=True, store=True, type='float'),		
		'expense': fields.many2one('kg.expense.master','Expense'),
		
	}
	
	_defaults = {
		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'ch.invoice.additional.charge', context=c),
		'date' : fields.date.context_today,
	
		}
		
	
	
ch_invoice_additional_charge()


class ch_customer_advance_invoice_line(osv.osv):

	_name = "ch.customer.advance.invoice.line"
	_description = "Customer Advance Invoice Line"
	_columns = {
	
		'header_id':fields.many2one('kg.sale.invoice', 'Invoice advance', ondelete='cascade'),
		'cus_advance_id' : fields.many2one('kg.customer.advance', 'Advance No', readonly=True),
		'cus_advance_date': fields.date('Advance Date'),
		'customer_advance_line_id' : fields.many2one('ch.cus.advance.line', 'Customer Advance Line', readonly=True),		
		'order_id': fields.many2one('kg.work.order','WO No.'),		
		'order_amt': fields.float('Order Amount', readonly=True),
		'tot_advance_amt': fields.float('Advance Amount', readonly=True),
		'already_adjusted_amt': fields.float('Already Adjusted Advance Amount', readonly=True),
		'balance_amt': fields.float('Balance Advance', readonly=True),
		'current_adv_amt': fields.float('Current Adjustment Amount',required=True),
		
		
	}
	
	def _current_adv_amt(self,cr,uid,ids,context = None):
		rec = self.browse(cr,uid,ids[0])
		if rec.current_adv_amt > rec.balance_amt:
			return False
		else:
			return True
			
	_constraints = [		
			  
		
		(_current_adv_amt, 'Please Check the Current Adjustment Amount. Balance amount should be less than Current Adjustment Amount!!',['Current Adjustment Amount']),

	   ]
	
	def onchange_order_id(self, cr, uid, ids, order_id):
		cusadvance_obj = self.pool.get('kg.customer.advance.line')
		cusadvance_ids = cusadvance_obj.search(cr, uid, [('order_id','=',order_id)])
		if cusadvance_ids:
			cusadvance_rec = cusadvance_obj.browse(cr, uid, cusadvance_ids[0])
			return {'value': {
				'cus_advance_id' : cusadvance_rec.advance_header_id.id,
				'cus_advance_date' : cusadvance_rec.advance_date,
				'po_amt' : cusadvance_rec.net_amt,
				'tot_advance_amt' : cusadvance_rec.advance_amt,
				'already_adjusted_amt' : cusadvance_rec.advance_amt - cusadvance_rec.balance_advance_amt,
				'balance_amt' : cusadvance_rec.balance_advance_amt,
				}}
		else:
			return True
			
ch_customer_advance_invoice_line()



class ch_customer_invoice_copy_rpt(osv.osv):

	_name = "ch.customer.invoice.copy.rpt"
	_description = "Customer Invoice Copy Report"
	
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		cgst_per = sgst_per = igst_per = ''		
		cgst_amt = sgst_amt = igst_amt = 0		
		for line in self.browse(cr, uid, ids, context=context):			
			res[line.id] = {
				
				'cgst_amt' : 0.0,
				'cgst_amt' : 0.0,
				'cgst_amt' : 0.0,
				'total_taxable_value' : 0.0,				
				
			}			
			sgst_tax_tot = cgst_tax_tot = igst_tax_tot = total_taxable_value = 0
			sgst_tax_per = cgst_tax_per = igst_tax_per = ''			
			if line.header_id.customer_id.state_id.code == 'TN':							
				if line.hsn_id.sgst_id.id:
					if line.hsn_id.sgst_id.id is False:
						raise osv.except_osv(_('Warning!'),
							_('Kindly map in HSN master SGST Tax!!'))
					else:	
						value = line.taxable_value * line.qty
						tax_per = line.hsn_id.sgst_id.amount * 100
						total_tax = (value * tax_per ) / 100									
						sgst_tax_tot = total_tax
						sgst_tax_per = line.hsn_id.sgst_id.name
							
				if line.hsn_id.cgst_id.id:
					if line.hsn_id.cgst_id.id is False:
						raise osv.except_osv(_('Warning!'),
							_('Kindly map in HSN master CGST Tax!!'))
					else:
						value = line.taxable_value * line.qty
						tax_per = line.hsn_id.cgst_id.amount * 100
						total_tax = (value * tax_per ) / 100		
						cgst_tax_tot = total_tax
						cgst_tax_per = line.hsn_id.cgst_id.name							
			else:
				if line.hsn_id.igst_id.id:
					if line.hsn_id.igst_id.id is False:
						raise osv.except_osv(_('Warning!'),
							_('Kindly map in HSN master IGST Tax!!'))
					else:
						value = line.taxable_value * line.qty
						tax_per = line.hsn_id.igst_id.amount * 100
						total_tax = (value * tax_per ) / 100		
						igst_tax_tot = total_tax
						igst_tax_per = line.hsn_id.igst_id.name				
			
			res[line.id]['cgst_amt'] = sgst_tax_tot
			res[line.id]['sgst_amt'] = cgst_tax_tot
			res[line.id]['igst_amt'] = igst_tax_tot
			res[line.id]['total_taxable_value'] = line.taxable_value * line.qty
			cr.execute('''update ch_customer_invoice_copy_rpt set cgst_per = %s,sgst_per = %s,igst_per = %s where id = %s ''',(cgst_tax_per,sgst_tax_per,igst_tax_per,line.id))
			
			
		return res
	
	
	_columns = {
	
		'header_id':fields.many2one('kg.sale.invoice', 'Invoice advance', ondelete='cascade'),
		
		'description' : fields.char('Description'),	
		'hsn_id' : fields.many2one('kg.hsn.master', 'HSN No'),
		'qty':fields.integer('Quantity'),
		'unit_price': fields.float('Unit Price'),	
		'deductions': fields.float('Deductions'),	
		'additions': fields.float('Additions'),	
		'taxable_value': fields.float('Taxable Value(Per Unit)'),		
		
		'cgst_per' : fields.char('CGST(%)'),	
		'sgst_per' : fields.char('SGST(%)'),	
		'igst_per' : fields.char('IGST(%)'),
		
		
		'total_taxable_value': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Taxable Value',multi="sums",store=True),
		'cgst_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='CGST Amt',multi="sums",store=True),
		'sgst_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='SGST Amt',multi="sums",store=True),
		'igst_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='IGST Amt',multi="sums",store=True),
		
		
		
	}	
	
	def onchange_taxable_value(self, cr, uid, ids, deductions,additions,unit_price,qty, context=None):
		value = {'taxable_value': ''}	
		total_value = unit_price		
		sub_final_total = (total_value + additions) - deductions				
		value = {'taxable_value': sub_final_total }
		return {'value': value}
	
			
ch_customer_invoice_copy_rpt()


class ch_annexure_invoice_copy_rpt(osv.osv):

	_name = "ch.annexure.invoice.copy.rpt"
	_description = "Customer Annexure Copy Report"
	
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')			
		cgst_amt = sgst_amt = igst_amt = total_value = 0		
		for line in self.browse(cr, uid, ids, context=context):			
			res[line.id] = {
				
				'cgst_amt' : 0.0,
				'cgst_amt' : 0.0,
				'cgst_amt' : 0.0,
				'total_value' : 0.0,				
				
			}			
			sgst_tax_tot = cgst_tax_tot = igst_tax_tot = total_taxable_value = 0
			sgst_tax_per = cgst_tax_per = igst_tax_per = ''			
			if line.header_id.customer_id.state_id.code == 'TN':							
				if line.hsn_id.sgst_id.id:
					if line.hsn_id.sgst_id.id is False:
						raise osv.except_osv(_('Warning!'),
							_('Kindly map in HSN master SGST Tax!!'))
					else:	
						value = line.each_price * line.qty
						tax_per = line.hsn_id.sgst_id.amount * 100
						total_tax = (value * tax_per ) / 100									
						sgst_tax_tot = total_tax
						sgst_tax_per = line.hsn_id.sgst_id.name
							
				if line.hsn_id.cgst_id.id:
					if line.hsn_id.cgst_id.id is False:
						raise osv.except_osv(_('Warning!'),
							_('Kindly map in HSN master CGST Tax!!'))
					else:
						value = line.each_price * line.qty
						tax_per = line.hsn_id.cgst_id.amount * 100
						total_tax = (value * tax_per ) / 100		
						cgst_tax_tot = total_tax
						cgst_tax_per = line.hsn_id.cgst_id.name							
			else:
				if line.hsn_id.igst_id.id:
					if line.hsn_id.igst_id.id is False:
						raise osv.except_osv(_('Warning!'),
							_('Kindly map in HSN master IGST Tax!!'))
					else:
						value = line.each_price * line.qty
						tax_per = line.hsn_id.igst_id.amount * 100
						total_tax = (value * tax_per ) / 100		
						igst_tax_tot = total_tax
						igst_tax_per = line.hsn_id.igst_id.name				
			
			res[line.id]['cgst_amt'] = sgst_tax_tot
			res[line.id]['sgst_amt'] = cgst_tax_tot
			res[line.id]['igst_amt'] = igst_tax_tot
			res[line.id]['total_value'] = line.each_price * line.qty
			
			
			
		return res
	
	_columns = {
	
		'header_id':fields.many2one('kg.sale.invoice', 'Invoice advance', ondelete='cascade'),
		
		'hsn_id' : fields.many2one('kg.hsn.master', 'HSN No'),
		'hsn_code' : fields.char('HSN Code'),
		'item_code' : fields.char('Item Code'),
		'tag_no' : fields.char('Tag No.'),
		'description' : fields.char('Description'),			
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model'),
		'pump_serial_no' : fields.char('Pump SL. No.'),
		'qty':fields.integer('Quantity'),
		'uom_id': fields.many2one('product.uom','UOM'),
		'each_price': fields.float('Each Price'),			
		
		
		'total_value': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Value',multi="sums",store=True),
		'cgst_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='CGST Amt',multi="sums",store=True),
		'sgst_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='SGST Amt',multi="sums",store=True),
		'igst_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='IGST Amt',multi="sums",store=True),	
		
		
	}	
	
	
	def onchange_hsn_code(self, cr, uid, ids, hsn_id, context=None):
		value = {'hsn_code': ''}
		if hsn_id:
			hsn_rec = self.pool.get('kg.hsn.master').browse(cr, uid, hsn_id, context=context)
			value = {'hsn_code': hsn_rec.name}
		return {'value': value}
	
			
ch_annexure_invoice_copy_rpt()


















