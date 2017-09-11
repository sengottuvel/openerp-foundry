from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
import netsvc
import datetime as dt
import datetime

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
	'line_ids':fields.one2many('ch.pumpspare.invoice', 'header_id', "Pump Invoice"),
	'line_ids_a': fields.one2many('ch.spare.invoice', 'header_id', "Spare Invoice"),
	'line_ids_b': fields.one2many('ch.accessories.invoice', 'header_id', "Accessories Invoice"),
	'line_ids_c': fields.one2many('ch.invoice.additional.charge', 'header_id', "Invoice Additional Charge"),
	'line_ids_d': fields.one2many('ch.customer.advance.invoice.line', 'header_id', "Invoice Advance Details"),
	
	
	'customer_po_no': fields.char('Customer PO No.',readonly=True),
	'cust_po_date': fields.date('Customer PO Date',readonly=True),
	
	
	'work_order_ids': fields.many2many('kg.work.order', 'invoice_work_order_ids', 'invoice_id','work_order_id', 'WO No.', delete=False,
			 domain="[('partner_id','=',customer_id),'&',('invoice_flag','=',False),'&', ('state','!=','draft'),'&', ('entry_mode','=','auto')]"),
	
	
	'round_off_amt': fields.float('Round off(+/-)' ),
	
	'pump_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),	
	'spare_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),	
	'access_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),
	
	'net_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True ,readonly=True),
	'total_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Amount',multi="sums",store=True ,readonly=True),
	'add_charge': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Additional Charges(+)',multi="sums",store=True ,readonly=True),
	'advance_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Adjected Advance Amount(-)',multi="sums",store=True ,readonly=True),
	
	'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
	}

	_defaults = {
	
		
		'proforma_invoice_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'invoice_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'state' : 'draft',
		'accounts_state': 'pending',	
		
	}
	
	def onchange_customer_details(self,cr,uid,ids,customer_id,context=None):
		cust_rec = self.pool.get('res.partner').browse(cr,uid,customer_id)
		contact_person = ''		
		billing_address = ''		
		del_address = ''		
		values = {'contact_person':'','billing_address':'','del_address':''}
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
			values = {'contact_person':contact_person,'billing_address':billing_address,'del_address':del_address}		
		return {'value' : values}
	
	def load_wo_details(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		cr.execute(""" delete from ch_pumpspare_invoice where header_id  = %s """ %(ids[0]))
		cr.execute(""" delete from ch_spare_invoice where header_id  = %s """ %(ids[0]))		
		cr.execute(""" delete from ch_accessories_invoice where header_id  = %s """ %(ids[0]))		
		for item in [x.id for x in rec.work_order_ids]:
			print"item",item
			work_obj = self.pool.get('kg.work.order')
			work_rec = self.pool.get('kg.work.order').browse(cr,uid,item)			
			for line in work_rec.line_ids:
				print"line",line.id
				if line.order_category == 'pump':	
					
					offer_rec = self.pool.get('ch.pump.offer').browse(cr,uid,line.pump_offer_line_id)
					offer_hea_rec = self.pool.get('kg.crm.offer').browse(cr,uid,offer_rec.header_id.id)
					print"customer_po_no",offer_hea_rec.customer_po_no
					print"cust_po_date",offer_hea_rec.cust_po_date
					
					
					print"offer_rec",offer_rec.prime_cost
					print"per_pump_prime_cost",offer_rec.per_pump_prime_cost
					print"sam_ratio",offer_rec.sam_ratio
					print"hsn_nohsn_no",offer_rec.id
					print"hsn_nohsn_no",offer_rec.hsn_no.id
					
					print"customerrrr",rec.customer_id.state_id.code
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
						print"list_idlist_id",list_id
					
					
										
					invoice_line = self.pool.get('ch.pumpspare.invoice').create(cr,uid,{
					   'header_id':rec.id,
					   'work_order_id':work_rec.id,
					   'order_line_id':line.id,
					   'pump_model_id':line.pump_model_id.id,
					   'order_category':line.order_category,
					   'qty':line.qty,
					   'pending_qty':line.qty,
					   'unit_price':line.unit_price,
					   'prime_cost':offer_rec.prime_cost,
					   'per_pump_prime_cost':offer_rec.per_pump_prime_cost,
					   'sam_ratio':offer_rec.sam_ratio,
					   'dealer_discount':offer_rec.dealer_discount,
					   'customer_discount':offer_rec.customer_discount,
					   'special_discount':offer_rec.special_discount,
					   'tax':offer_rec.tax,
					   'p_f':offer_rec.p_f,
					   'freight':offer_rec.freight,
					   'insurance':offer_rec.insurance,
					   'total_price':offer_rec.total_price,
					   'tax_id':[(6, 0, [x for x in list_id])],
					   'hsn_no':offer_rec.hsn_no.id,
					   })
				
					
					self.write(cr, uid, ids, {'customer_po_no':offer_hea_rec.customer_po_no,
										'cust_po_date': offer_hea_rec.cust_po_date,})
				
				if line.order_category == 'spare':					
					for bom_line in line.line_ids:					
						print"bom_line.spare_of222222222222222222222222222222222@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@2fer_line_id",bom_line.spare_offer_line_id
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
															
						invoice_line = self.pool.get('ch.spare.invoice').create(cr,uid,{
						   'header_id':rec.id,
						   'work_order_id':work_rec.id,
						   'order_line_id':line.id,
						   'pump_id':line.pump_model_id.id,
						   'order_category':line.order_category,
						   'pattern_id':bom_line.pattern_id.id,
						   'item_name':bom_line.pattern_id.name,
						   'item_code':bom_line.pattern_id.pattern_name,
						   'moc_id':bom_line.moc_id.id,
						   'qty':bom_line.qty,
						   'pending_qty':line.qty,
						   'unit_price':bom_line.unit_price,
						   'prime_cost':offer_rec.prime_cost,						   
						   'sam_ratio':offer_rec.sam_ratio,
						   'dealer_discount':offer_rec.dealer_discount,
						   'customer_discount':offer_rec.customer_discount,
						   'special_discount':offer_rec.special_discount,
						   'tax':offer_rec.tax,
						   'p_f':offer_rec.p_f,
						   'freight':offer_rec.freight,
						   'insurance':offer_rec.insurance,
						   'total_price':offer_rec.total_price,	
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
														
						machine_shop_line = self.pool.get('ch.spare.invoice').create(cr,uid,{
						   'header_id':rec.id,
						   'work_order_id':work_rec.id,
						   'order_line_id':line.id,
						   'pump_id':line.pump_model_id.id,
						   'order_category':line.order_category,
						   'ms_id':machine_shop_line.ms_id.id,							   
						   'moc_id':machine_shop_line.moc_id.id,
						   'item_name':machine_shop_line.ms_id.name,
						   'item_code':machine_shop_line.ms_id.code,
						   'unit_price':0.00,
						   'qty':machine_shop_line.qty,
						   'pending_qty':line.qty,
						   'prime_cost':offer_rec.prime_cost,						   
						   'sam_ratio':offer_rec.sam_ratio,
						   'dealer_discount':offer_rec.dealer_discount,
						   'customer_discount':offer_rec.customer_discount,
						   'special_discount':offer_rec.special_discount,
						   'tax':offer_rec.tax,
						   'p_f':offer_rec.p_f,
						   'freight':offer_rec.freight,
						   'insurance':offer_rec.insurance,
						   'total_price':offer_rec.total_price,
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
															
						bot_line = self.pool.get('ch.spare.invoice').create(cr,uid,{
						   'header_id':rec.id,
						   'work_order_id':work_rec.id,
						   'order_line_id':line.id,
						   'pump_id':line.pump_model_id.id,
						   'order_category':line.order_category,
						   'bot_id':bot_line.bot_id.id,
						   'item_name':bot_line.bot_id.name,
						   'item_code':bot_line.bot_id.code,								  
						   'moc_id':bot_line.moc_id.id,
						   'unit_price':0.00,
						   'qty':bot_line.qty,
						   'pending_qty':line.qty,
						   'prime_cost':offer_rec.prime_cost,						   
						   'sam_ratio':offer_rec.sam_ratio,
						   'dealer_discount':offer_rec.dealer_discount,
						   'customer_discount':offer_rec.customer_discount,
						   'special_discount':offer_rec.special_discount,
						   'tax':offer_rec.tax,
						   'p_f':offer_rec.p_f,
						   'freight':offer_rec.freight,
						   'insurance':offer_rec.insurance,
						   'total_price':offer_rec.total_price,
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
													
							machine_shop_line = self.pool.get('ch.accessories.invoice').create(cr,uid,{
							   'header_id':rec.id,
							   'work_order_id':work_rec.id,
							   'order_line_id':line.id,
							   'pump_id':line.pump_model_id.id,
							   'order_category':line.order_category,
							   'access_id':access_line.access_id.id,							   
							   'moc_id':access_line.moc_id.id,							   
							   'unit_price':line.unit_price,
							   'qty':access_line.qty,
							   'pending_qty':line.qty,
							   'prime_cost':offer_rec.prime_cost,						   
							   'per_access_prime_cost':offer_rec.per_access_prime_cost,						   
							   'sam_ratio':offer_rec.sam_ratio,
							   'dealer_discount':offer_rec.dealer_discount,
							   'customer_discount':offer_rec.customer_discount,
							   'special_discount':offer_rec.special_discount,
							   'tax':offer_rec.tax,
							   'p_f':offer_rec.p_f,
							   'freight':offer_rec.freight,
							   'insurance':offer_rec.insurance,
							   'total_price':offer_rec.total_price,
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
		
		if rec.state == 'draft':
			for item in [x.id for x in rec.work_order_ids]:
				print"item",item
				work_obj = self.pool.get('kg.work.order')
				work_rec = self.pool.get('kg.work.order').browse(cr,uid,item)
				print"line_idsline_ids",work_rec.line_ids
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
			for item in [x.id for x in rec.work_order_ids]:			
				work_rec = self.pool.get('kg.work.order').browse(cr,uid,item)				
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
		for item in [x.id for x in invoice_rec.work_order_ids]:			
			work_rec = self.pool.get('kg.work.order').browse(cr,uid,item)			
			adv_search = self.pool.get('kg.customer.advance').search(cr, uid, [('order_id','=',work_rec.id)])
			cr.execute(""" select * from kg_customer_advance where order_id = %s and balance_amt > 0 and state='confirmed'""" %(work_rec.id))
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
	

	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []	 
		for rec in self.browse(cr,uid,ids): 
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
					
	
kg_sale_invoice()



class ch_pumpspare_invoice(osv.osv):

	_name = "ch.pumpspare.invoice"
	_description = "Pump Spare Invoice"
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		sam_ratio_tot = dealer_discount_tot = val = customer_discount_tot = spl_discount_tot = tax_tot = p_f_tot = freight_tot = insurance_tot = pump_price_tot = tot_price = net_amount = 0
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
			print"line.unit_price",line.unit_price
			for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id,
				line.prime_cost, line.qty,1,1)['taxes']:
				print"ccccccc",c
				
				val += c.get('amount', 0.0)
				print"valvalval",val
				tax_tot = val	
			
			
			
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
			res[line.id]['net_amount'] = net_amount + tax_tot
			
		return res
	
	
	_columns = {
	
		'header_id':fields.many2one('kg.sale.invoice', 'Invoice Detail', required=1, ondelete='cascade'),
		'work_order_id':fields.many2one('kg.work.order', 'Offer'),	
		'order_line_id': fields.many2one('ch.work.order.details','Order Line'),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True,domain="[('active','=','t')]"),		
		'order_category': fields.selection([('pump','Pump'),('spare','Spare')],'Purpose', required=True),
		'qty': fields.integer('Qty', required=True),
		'pending_qty': fields.integer('Pending Qty'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'note': fields.text('Notes'),
		'remarks': fields.text('Approve/Reject Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		
		'line_ids': fields.one2many('ch.pumpspare.bom.details', 'header_id', "BOM Details"),
		'line_ids_a': fields.one2many('ch.pumpspare.machineshop.details', 'header_id', "Machine Shop Details"),
		'line_ids_b': fields.one2many('ch.pumpspare.bot.details', 'header_id', "BOT Details"),	
		
		'hsn_no': fields.many2one('kg.hsn.master','HSN No.'),
		'tax_id': fields.many2many('account.tax', 'pump_invoice_taxes', 'pump_invoice_id', 'tax_id', 'GST Taxes'),
		
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),		
		'unit_price': fields.float('Unit Price',required=True),	
		
		### Used for value
		
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
		'total_price': fields.float('Total Price'),
		
		### Function used value update
		'tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Unit Price',multi="sums",store=True),	
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
		sam_ratio_tot = dealer_discount_tot = val = customer_discount_tot = spl_discount_tot = tax_tot = p_f_tot = freight_tot = insurance_tot = pump_price_tot = tot_price = net_amount = 0
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
			
			for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id,
				line.prime_cost, line.qty,1,1)['taxes']:
				val += c.get('amount', 0.0)
				print"valvalval",val
				tax_tot = val	
			
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
			res[line.id]['net_amount'] = net_amount + tax_tot
			
		return res
	
	_columns = {
	
		### Pump Details ####
		'header_id':fields.many2one('kg.sale.invoice', 'Offer', ondelete='cascade'),
		'work_order_id':fields.many2one('kg.work.order', 'Offer'),	
		'order_line_id': fields.many2one('ch.work.order.details','Order Line'),		
		'qty':fields.integer('Quantity'),
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
		
		'unit_price': fields.float('Unit Price',required=True),	
		
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
		
		### Function used value update
		'tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Unit Price',multi="sums",store=True),	
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
		
		
	}
	

ch_spare_invoice()


class ch_accessories_invoice(osv.osv):	
	
		
	_name = "ch.accessories.invoice"
	_description = "Ch Accessories Invoice"
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		sam_ratio_tot = val = dealer_discount_tot = customer_discount_tot = spl_discount_tot = tax_tot = p_f_tot = freight_tot = insurance_tot = pump_price_tot = tot_price = net_amount = 0
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
			for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id,
				line.prime_cost, line.qty,1,1)['taxes']:
				val += c.get('amount', 0.0)
				print"valvalval",val
				tax_tot = val	
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
			res[line.id]['net_amount'] = net_amount + tax_tot
			
		return res
	
	_columns = {
	
		### Spare Details ####
		'header_id':fields.many2one('kg.sale.invoice', 'Invoice', ondelete='cascade'),
		'work_order_id':fields.many2one('kg.work.order', 'Offer'),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line'),
		'access_id':fields.many2one('kg.accessories.master', 'Item Name'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),
		'moc_id':fields.many2one('kg.moc.master', 'MOC'),
		'qty':fields.integer('Quantity'),
		'pending_qty': fields.integer('Pending Qty'),
		
		'off_name': fields.char('Offer Name'),
		'hsn_no': fields.many2one('kg.hsn.master','HSN No.'),
		'tax_id': fields.many2many('account.tax', 'acc_invoice_taxes', 'acc_invoice_id', 'tax_id', 'GST Taxes'),
		
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
		'unit_price': fields.float('Unit Price',required=True),
		
		'tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Unit Price',multi="sums",store=True),	
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


















