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
		
	'line_ids':fields.one2many('ch.pumpspare.invoice', 'header_id', "Pump Invoice"),
	'line_ids_a': fields.one2many('ch.spare.invoice', 'header_id', "Spare Invoice"),
	'line_ids_b': fields.one2many('ch.accessories.invoice', 'header_id', "Accessories Invoice"),
	'line_ids_c': fields.one2many('ch.invoice.additional.charge', 'header_id', "Invoice Additional Charge"),
	'line_ids_d': fields.one2many('ch.customer.advance.invoice.line', 'header_id', "Invoice Advance Details"),
	
	
	'work_order_ids': fields.many2many('kg.work.order', 'invoice_work_order_ids', 'invoice_id','work_order_id', 'Work Order', delete=False,
			 domain="[('state','=','confirmed'),('partner_id','=',customer_id)]"),		
			 
	'total_amt': fields.float('Total Amount'),
	'add_charge': fields.float('Additional Charges(+)'),
	'advance_amt': fields.float('Adjected Advance Amount(-)'),
	'net_amt': fields.float('Net Amount'),
	'round_off_amt': fields.float('Round off(+/-)'),
	}

	_defaults = {
	
		
		'proforma_invoice_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'invoice_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'state' : 'draft',
		
	}
	
	def onchange_customer_details(self,cr,uid,ids,customer_id,context=None):
		cust_rec = self.pool.get('res.partner').browse(cr,uid,customer_id)
		contact_person = ''		
		values = {'contact_person':''}
		if cust_rec.contact_person :
			contact_person = cust_rec.contact_person		
		values = {'contact_person':contact_person}		
		return {'value' : values}
	
	def load_wo_details(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		cr.execute(""" delete from ch_pumpspare_invoice where header_id  = %s """ %(ids[0]))
		cr.execute(""" delete from ch_spare_invoice where header_id  = %s """ %(ids[0]))		
		for item in [x.id for x in rec.work_order_ids]:
			print"item",item
			work_rec = self.pool.get('kg.work.order').browse(cr,uid,item)
			print"line_idsline_ids",work_rec.line_ids
			
			for line in work_rec.line_ids:
				print"line",line.id
				if line.order_category == 'pump':			
										
					invoice_line = self.pool.get('ch.pumpspare.invoice').create(cr,uid,{
					   'header_id':rec.id,
					   'pump_model_id':line.pump_model_id.id,
					   'order_category':line.order_category,
					   'qty':line.qty,
					   'unit_price':line.unit_price,
					   })
				
				
				if line.order_category == 'spare':					
					for bom_line in line.line_ids:	
						print"bom_line",bom_line
												
						print"bom_line_rec.pattern_id",bom_line.pattern_id
						invoice_line = self.pool.get('ch.spare.invoice').create(cr,uid,{
						   'header_id':rec.id,
						   'pump_id':line.pump_model_id.id,
						   'order_category':line.order_category,
						   'pattern_id':bom_line.pattern_id.id,
						   'item_name':bom_line.pattern_id.name,
						   'item_code':bom_line.pattern_id.pattern_name,
						   'moc_id':bom_line.moc_id.id,
						   'qty':bom_line.qty,
						   'unit_price':bom_line.unit_price,
						   })						
						
						for machine_shop_line in line.line_ids_a:								
							machine_shop_line = self.pool.get('ch.spare.invoice').create(cr,uid,{
							   'header_id':rec.id,
							   'pump_id':line.pump_model_id.id,
							   'order_category':line.order_category,
							   'ms_id':machine_shop_line.ms_id.id,							   
							   'moc_id':machine_shop_line.moc_id.id,
							   'item_name':machine_shop_line.ms_id.name,
							   'item_code':machine_shop_line.ms_id.code,
							   'unit_price':0.00,
							   'qty':machine_shop_line.qty})
						   
							for bot_line in line.line_ids_b:								
								bot_line = self.pool.get('ch.spare.invoice').create(cr,uid,{
								   'header_id':rec.id,
								   'pump_id':line.pump_model_id.id,
								   'order_category':line.order_category,
								   'bot_id':bot_line.bot_id.id,
								   'item_name':bot_line.bot_id.name,
								   'item_code':bot_line.bot_id.code,								  
								   'moc_id':bot_line.moc_id.id,
								   'unit_price':0.00,
								   'qty':bot_line.qty})					   
						   
					
				else:
					pass
					
	def invoice_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		print"rec.name",rec.name
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
		self.write(cr, uid, ids, {'state': 'approved'})
		return True
		
	def invoice_process(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])		
		invoice_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.sale.invoice')])
		invoice_rec = self.pool.get('ir.sequence').browse(cr,uid,invoice_id[0])
		cr.execute("""select generatesequenceno(%s,'%s','%s') """%(invoice_id[0],invoice_rec.code,rec.invoice_date))
		invoice_name = cr.fetchone();			
		
		self.write(cr, uid, ids, {'state': 'invoice','invoice_no':invoice_name[0]})
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
			cr.execute(""" select * from kg_customer_advance where order_id = %s and bal_adv > 0 and state='approved'""" %(work_rec.id))
			grn_data = cr.dictfetchall()			
			for inv in grn_data:
				cus_inadv_obj.create(cr,uid,{
					'order_id' : inv['order_id'],
					'cus_advance_id' : inv['id'],
					'cus_advance_date' : inv['advance_date'],
					'tot_advance_amt' : inv['advance_amt'],
					'balance_amt' : inv['bal_adv'],
					'current_adv_amt' : 0.0,
					'header_id' : invoice_rec.id,
					})
				
		return True
	

	def unlink(self,cr,uid,ids,context=None):
		raise osv.except_osv(_('Warning!'),
				_('You can not delete Entry !!'))
					
	
kg_sale_invoice()



class ch_pumpspare_invoice(osv.osv):

	_name = "ch.pumpspare.invoice"
	_description = "Pump Spare Invoice"
	
	
	_columns = {
	
		'header_id':fields.many2one('kg.sale.invoice', 'Invoice Detail', required=1, ondelete='cascade'),	
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True,domain="[('active','=','t')]"),		
		'order_category': fields.selection([('pump','Pump'),('spare','Spare')],'Purpose', required=True),
		'qty': fields.integer('Qty', required=True),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'note': fields.text('Notes'),
		'remarks': fields.text('Approve/Reject Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		
		'line_ids': fields.one2many('ch.pumpspare.bom.details', 'header_id', "BOM Details"),
		'line_ids_a': fields.one2many('ch.pumpspare.machineshop.details', 'header_id', "Machine Shop Details"),
		'line_ids_b': fields.one2many('ch.pumpspare.bot.details', 'header_id', "BOT Details"),	
		
		'unit_price': fields.float('Unit Price',required=True),	
		
		### Used for value
		
		'dealer_discount': fields.float('Dealer Discount(%)'),
		'customer_discount': fields.float('Customer Discount(%)'),
		'special_discount': fields.float('Special Discount(%)'),
		'tax': fields.float('Tax(%)'),
		'p_f': fields.float('P&F(%)'),
		'freight': fields.float('Freight(%)'),
		'insurance': fields.float('Insurance(%)'),
		'total_price': fields.float('Total Price'),
		
	}
	
	
	_defaults = {
	
		'state': 'draft',	
		
	}
	
	
ch_pumpspare_invoice()


class ch_spare_invoice(osv.osv):	
		
	_name = "ch.spare.invoice"
	_description = "Ch Spare Invoice"
	
	_columns = {
	
		### Pump Details ####
		'header_id':fields.many2one('kg.sale.invoice', 'Offer', ondelete='cascade'),			
		'qty':fields.integer('Quantity'),
		'item_code': fields.char('Item Code'),
		'item_name': fields.char('Item Name'),
		'moc_id': fields.many2one('kg.moc.master','MOC Name'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No'),
		'ms_id': fields.many2one('kg.machine.shop','MS Name'),
		'bot_id': fields.many2one('kg.machine.shop','BOT Name'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),		
		
		'unit_price': fields.float('Unit Price',required=True),	
		
		'dealer_discount': fields.float('Dealer Discount(%)'),
		'customer_discount': fields.float('Customer Discount(%)'), 
		'special_discount': fields.float('Special Discount(%)'),
		'tax': fields.float('Tax(%)'),
		'p_f': fields.float('P&F(%)'),
		'freight': fields.float('Freight(%)'),
		'insurance': fields.float('Insurance(%)'),
		'total_price': fields.float('Total Price'),	
		
		
	}
	

ch_spare_invoice()



class ch_accessories_invoice(osv.osv):	
	
		
	_name = "ch.accessories.invoice"
	_description = "Ch Accessories Invoice"
	
	_columns = {
	
		### Spare Details ####
		'header_id':fields.many2one('kg.sale.invoice', 'Invoice', ondelete='cascade'),
		'work_order_id':fields.many2one('kg.work.order', 'Offer'),
		
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
		'unit_price': fields.float('Unit Price',required=True),	
		
		
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
		'cus_advance_id' : fields.many2one('kg.customer.advance', 'Customer Advance No', readonly=True),
		'cus_advance_date': fields.date('PO Advance Date'),
		'customer_advance_line_id' : fields.many2one('ch.customer.advance.line', 'Customer Advance Line', readonly=True),		
		'order_id': fields.many2one('kg.work.order','Work Order No.'),		
		'order_amt': fields.float('Order Amount', readonly=True),
		'tot_advance_amt': fields.float('Total Advance Amount', readonly=True),
		'already_adjusted_amt': fields.float('Already Adjusted Advance Amount', readonly=True),
		'balance_amt': fields.float('Balance Advance to be adjusted', readonly=True),
		'current_adv_amt': fields.float('Current Adjustment Amount',required=True),
		
		
	}
	
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


















