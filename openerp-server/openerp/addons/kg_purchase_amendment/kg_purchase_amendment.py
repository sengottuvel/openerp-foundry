from datetime import *
import time
from osv import fields, osv
from tools.translate import _
import netsvc
import decimal_precision as dp
from itertools import groupby
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import netsvc
logger = logging.getLogger('server')
today = datetime.now()

UOM_CONVERSATION = [
    ('one_dimension','One Dimension'),('two_dimension','Two Dimension')
]
class kg_purchase_amendment(osv.osv):	
	
	_name = "kg.purchase.amendment"	
	_order = "date desc"
	
	def _amount_line_tax(self, cr, uid, line, context=None):
		#~ val = 0.0
		#~ new_amt_to_per = line.kg_discount_amend or 0.0 / line.product_qty_amend
		#~ amt_to_per = (line.kg_discount_amend or 0.0 / (line.product_qty_amend * line.price_unit_amend or 1.0 )) * 100
		#~ kg_discount_per = line.kg_discount_per_amend
		#~ tot_discount_per = amt_to_per + kg_discount_per
		#~ for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id_amend,
			#~ line.price_unit_amend * (1-(tot_discount_per or 0.0)/100.0), line.product_qty_amend, line.product_id,
			#~ line.amendment_id.partner_id)['taxes']:
			#~ val += c.get('amount', 0.0)
			
		val = 0.0
		qty = 0
		if line.price_type_amend == 'per_kg':
			if line.product_id_amend.uom_conversation_factor == 'two_dimension':
				if line.product_id_amend.po_uom_in_kgs > 0:
					qty = line.product_qty_amend * line.product_id_amend.po_uom_in_kgs * line.length_amend * line.breadth_amend
			elif line.product_id_amend.uom_conversation_factor == 'one_dimension':
				if line.product_id_amend.po_uom_in_kgs > 0:
					qty = line.product_qty_amend * line.product_id_amend.po_uom_in_kgs
				else:
					qty = line.product_qty_amend
			else:
				qty = line.product_qty_amend
		else:
			qty = line.product_qty_amend
			
		new_amt_to_per = line.kg_discount_amend / qty
		amt_to_per = (line.kg_discount_amend / (qty * line.price_unit_amend or 1.0 )) * 100
		kg_discount_per = line.kg_discount_per_amend
		tot_discount_per = amt_to_per + kg_discount_per

		for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id_amend,
			line.price_unit_amend * (1-(tot_discount_per or 0.0)/100.0), qty, line.product_id_amend,
				line.amendment_id.partner_id_amend)['taxes']:
			 
			val += c.get('amount', 0.0)
			
		return val
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		discount_per_value = other_charges_amt = 0
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'total_amount_amend': 0.0,
				'discount_amend': 0.0,
				'amount_untaxed_amend': 0.0,
				'amount_tax_amend': 0.0,
				'grand_total_amend': 0.0,
				'round_off_amend': 0.0,
				'amount_total_amend': 0.0,
				'other_charge_amend': 0.0,
			}
			#~ val = val1 = val3 = 0.0
			#~ cur = order.pricelist_id.currency_id
			#~ for line in order.amendment_line:
				#~ tot_discount = line.kg_discount_amend + line.kg_discount_per_value_amend
				#~ val1 += line.price_subtotal
				#~ val += self._amount_line_tax(cr, uid, line, context=context)
				#~ val3 += tot_discount
			#~ po_charges=order.value1_amend + order.value2_amend
			#~ print "po_charges :::", po_charges , "val ::::", val, "val1::::", val1, "val3:::::", val3
			#~ #res[order.id]['other_charge']=cur_obj.round(cr, uid, cur, po_charges)
			#~ res[order.id]['total_amount'] = (val1 + val3) - val
			#~ res[order.id]['grand_total']=cur_obj.round(cr, uid, cur, val)
			#~ res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
			#~ res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
			#~ res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] + res[order.id]['other_charge']
			#~ res[order.id]['discount']=cur_obj.round(cr, uid, cur, val3)
			#~ #self.write(cr, uid,order.id, {'other_charge' : po_charges})
		#~ print "res ^^^^^^^^^^^^^,", "amount_total====", res[order.id]['amount_total'], "^^^^^^^^^^^^^^", res
			val = val1 = val3 = 0.0
			
			pol = self.pool.get('kg.purchase.amendment.line')
			for line in order.amendment_line:
				discount_per_value = ((line.product_qty_amend * line.price_unit_amend) / 100.00) * line.kg_discount_per_amend
				tot_discount = line.kg_discount_amend + discount_per_value
				val1 += line.price_subtotal
				val += self._amount_line_tax(cr, uid, line, context=context)
				val3 += tot_discount
			res[order.id]['total_amount_amend'] = (val1 + val3) - val
			print"res[order.id]['total_amount_amend']",res[order.id]['total_amount_amend']
			res[order.id]['other_charge'] = other_charges_amt or 0
			res[order.id]['amount_tax_amend'] = val
			res[order.id]['amount_untaxed_amend'] = val1 - val 
			res[order.id]['discount_amend'] = val3
			res[order.id]['grand_total_amend'] = val1
			res[order.id]['round_off_amend'] = order.round_off
			res[order.id]['amount_total_amend'] = val1 + order.round_off or 0.00
			
		return res
		
	def _get_order(self, cr, uid, ids, context=None):
		result = {}
		for line in self.pool.get('kg.purchase.amendment.line').browse(cr, uid, ids, context=context):
			print "line :::::::::::::::::::::::ids:::",ids, line
			result[line.amendment_id.id] = True
		return result.keys()
	
	_columns = {
		
		'name': fields.char('Amendment NO', size=128, readonly=True),
		'date':fields.date('Amendment Date',readonly=False,states={'draft':[('readonly',False)]}),
		'po_id':fields.many2one('purchase.order','PO.NO', required=True,
			domain="[('state','=','approved'),'&',('order_line.line_state','!=','cancel'),'&',('order_line.line_bill','=', False),'&',('order_line.pending_qty','>',0)]",
			readonly=True,states={'amend':[('readonly',False)]}),
		'po_date':fields.date('PO Date', readonly=True),
		'partner_id':fields.many2one('res.partner', 'Supplier', readonly=True),
		'pricelist_id':fields.many2one('product.pricelist', 'Pricelist', required=True, states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)]}),
		'currency_id': fields.related('pricelist_id', 'currency_id', type="many2one", relation="res.currency", string="Currency",readonly=True, required=True),
		'po_expenses_type1': fields.selection([('freight','Freight Charges'),('others','Others')], 'Expenses Type1',readonly=True),
		'po_expenses_type2': fields.selection([('freight','Freight Charges'),('others','Others')], 'Expenses Type2',readonly=True),
		'value1':fields.float('Value1', readonly=True),
		'value2':fields.float('Value2', readonly=True),
		'bill_type': fields.selection([('cash','Cash'),('credit','Credit'),('advance','Advance')], 'Payment Mode', readonly=True),
		'price':fields.selection([('inclusive','Inclusive of all Taxes and Duties')], 'Price', readonly=True),
		'payment_mode': fields.many2one('kg.payment.master','Payment Term', readonly=True),
		'advance_amt': fields.float('Advance Amount(%)',readonly=True),
		'delivery_mode': fields.many2one('kg.delivery.master', 'Delivery Term', readonly=True),
		'term_warranty':fields.char('Warranty', readonly=True),
		'term_freight':fields.selection([('Inclusive','Inclusive'),('Extra','Extra'),('To Pay','To Pay'),('Paid','Paid'),
						  ('Extra at our Cost','Extra at our Cost')], 'Freight',readonly=True),
		'quot_ref_no':fields.char('Your Quot. Ref.'),
		'note': fields.text('Remarks'),
		'cancel_note': fields.text('Cancel Remarks'),
		
		'amend_flag':fields.boolean('Amend Flag'),
		'state':fields.selection([('draft', 'Draft'),('amend', 'Processing'),('confirm', 'Confirmed'),('approved', 'Approved'),('cancel','Cancel')], 'Status'),
		'amendment_line':fields.one2many('kg.purchase.amendment.line', 'amendment_id', 'Amendment Line'),
		'add_text': fields.text('Address',readonly=True),
		'delivery_address':fields.text('Delivery Address'),
		'other_charge': fields.float('Other Charges(+)',readonly=True),
		'total_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Amount',
			 multi="sums", store=True, help="The amount without tax", track_visibility='always'),
		'discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Discount(-)',
			store={
				'kg.purchase.amendment': (lambda self, cr, uid, ids, c={}: ids, ['amendment_line'], 10),
				'kg.purchase.amendment.line': (_get_order, ['price_unit_amend', 'tax_id', 'kg_discount_amend', 'product_qty_amend'], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
			store={
				'kg.purchase.amendment': (lambda self, cr, uid, ids, c={}: ids, ['amendment_line'], 10),
				'kg.purchase.amendment.line': (_get_order, ['price_unit_amend', 'tax_id', 'kg_discount_amend', 'product_qty_amend'], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
			store={
				'kg.purchase.amendment': (lambda self, cr, uid, ids, c={}: ids, ['amendment_line'], 10),
				'kg.purchase.amendment.line': (_get_order, ['price_unit_amend', 'tax_id', 'kg_discount_amend', 'product_qty_amend'], 10),
			}, multi="sums", help="The tax amount"),
		'grand_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Grand Total',
			 multi="sums", store=True, help="The amount without tax", track_visibility='always'),
		'round_off': fields.float('Round off',size=5,readonly=False, states={'approved':[('readonly',True)]}),
		'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',
			store={
				'kg.purchase.amendment': (lambda self, cr, uid, ids, c={}: ids, ['amendment_line'], 10),
				'kg.purchase.amendment.line': (_get_order, ['price_unit_amend', 'tax_id', 'kg_discount_amend', 'product_qty_amend'], 10),
				
			}, multi="sums",help="The total amount"),
		'grn_flag': fields.boolean('GRN'),
		'po_type': fields.selection([('direct', 'Direct'),('frompi', 'From PI')], 'PO Type',readonly=True),
		'item_quality_term_id': fields.many2many('kg.item.quality.master','general_term','po_id','term_id','Item Quality Term',readonly=True),
		'mode_of_dispatch': fields.many2one('kg.dispatch.master','Mode of Dispatch',readonly=True),
		'insurance': fields.selection([('sam','By Sam'),('supplier','By Supplier'),('na','N/A')],'Insurance',readonly=True),
		'purpose':fields.selection([('for_sale','For Production'),('own_use','Own use')], 'Purpose',readonly=True), 
		'quotation_date': fields.date('Quotation Date',readonly=True),
		'excise_duty': fields.selection([('inclusive','Inclusive'),('extra','Extra'),('nil','Nil')],'Excise Duty',readonly=True),
		'division': fields.selection([('ppd','PPD'),('ipd','IPD'),('foundry','Foundry')],'Division',readonly=True),
		
		# Amendment Fields:
		
		'po_date_amend':fields.date('Amend PO Date',readonly=False,states={'approved':[('readonly',True)]}),
		'quot_ref_no_amend':fields.char('Amend Your Quot. Ref.',readonly=False,states={'approved':[('readonly',True)]}),
		'partner_id_amend':fields.many2one('res.partner', 'Amend Supplier',readonly=False,states={'approved':[('readonly',True)]}),
		'add_text_amend': fields.text('Amend Address',readonly=False,states={'approved':[('readonly',True)]}),
		'price_amend':fields.selection([('inclusive','Inclusive of all Taxes and Duties')], 'Amend Price',readonly=False,states={'approved':[('readonly',True)]}),
		'delivery_address_amend':fields.text('Amend Delivery Address'),
		'bill_type_amend': fields.selection([('cash','Cash'),('credit','Credit'),('advance','Advance')], 'Amend Payment Mode',readonly=False,states={'approved':[('readonly',True)]}),
		'payment_mode_amend': fields.many2one('kg.payment.master','Amend Payment Term',readonly=False,states={'approved':[('readonly',True)]}),
		'advance_amt_amend': fields.float('Amend Advance(%)',readonly=False,states={'approved':[('readonly',True)]}),
		'delivery_mode_amend': fields.many2one('kg.delivery.master', 'Amend Delivery Term',readonly=False,states={'approved':[('readonly',True)]}),
		'po_expenses_type1_amend': fields.selection([('freight','Freight Charges'),('others','Others')], 'Amend Expenses Type1',
			states={'confirm':[('readonly', True)]}),
		'po_expenses_type2_amend': fields.selection([('freight','Freight Charges'),('others','Others')], 'Amend Expenses Type2',
			states={'confirm':[('readonly', True)]}),
		'value1_amend':fields.float('Amend Value1', states={'confirm':[('readonly', True)]}),
		'value2_amend':fields.float('Amend Value2', states={'confirm':[('readonly', True)]}),
		'remark': fields.text('Remarks', states={'confirm':[('readonly', True)]}),
		'terms': fields.text('Notes', states={'confirm':[('readonly', True)]}),
		'term_warranty_amend':fields.char('Amend Warranty',readonly=False,states={'approved':[('readonly',True)]}),
		'term_freight_amend':fields.selection([('Inclusive','Inclusive'),('Extra','Extra'),('To Pay','To Pay'),('Paid','Paid'),
						  ('Extra at our Cost','Extra at our Cost')], 'Amend Freight',readonly=False,states={'approved':[('readonly',True)]}),
		'po_type_amend': fields.selection([('direct', 'Direct'),('frompi', 'From PI')], 'PO Type',readonly=True),
		'item_quality_term_id_amend': fields.many2many('kg.item.quality.master','general_term','po_id','term_id','Amend Item Quality Term',readonly=False, states={'approved':[('readonly',True)]}),
		'mode_of_dispatch_amend': fields.many2one('kg.dispatch.master','Amend Mode of Dispatch',readonly=False, states={'approved':[('readonly',True)]}),
		'insurance_amend': fields.selection([('sam','By Sam'),('supplier','By Supplier'),('na','N/A')],'Amend Insurance',readonly=False, states={'approved':[('readonly',True)]}),
		'purpose_amend':fields.selection([('for_sale','For Production'),('own_use','Own use')], 'Amend Purpose',readonly=False, states={'approved':[('readonly',True)]}), 
		'quotation_date_amend': fields.date('Amend Quotation Date',readonly=False, states={'approved':[('readonly',True)]}),
		'excise_duty_amend': fields.selection([('inclusive','Inclusive'),('extra','Extra'),('nil','Nil')],'Excise Duty',readonly=False, states={'approved':[('readonly',True)]}),
		'division_amend': fields.selection([('ppd','PPD'),('ipd','IPD'),('foundry','Foundry')],'Amend Division',readonly=False, states={'approved':[('readonly',True)]}),
		
		'other_charge_amend': fields.float('Other Charges(+)',readonly=True),
		'total_amount_amend': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Amount',
			 multi="sums", store=True, help="The amount without tax", track_visibility='always'),
		'discount_amend': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Discount(-)',
			store={
				'kg.purchase.amendment': (lambda self, cr, uid, ids, c={}: ids, ['amendment_line'], 10),
				'kg.purchase.amendment.line': (_get_order, ['price_unit_amend', 'tax_id', 'kg_discount_amend', 'product_qty_amend'], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_untaxed_amend': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
			store={
				'kg.purchase.amendment': (lambda self, cr, uid, ids, c={}: ids, ['amendment_line'], 10),
				'kg.purchase.amendment.line': (_get_order, ['price_unit_amend', 'tax_id', 'kg_discount_amend', 'product_qty_amend'], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_tax_amend': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
			store={
				'kg.purchase.amendment': (lambda self, cr, uid, ids, c={}: ids, ['amendment_line'], 10),
				'kg.purchase.amendment.line': (_get_order, ['price_unit_amend', 'tax_id', 'kg_discount_amend', 'product_qty_amend'], 10),
			}, multi="sums", help="The tax amount"),
		'grand_total_amend': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Grand Total',
			 multi="sums", store=True, help="The amount without tax", track_visibility='always'),
		'round_off_amend': fields.float('Round off',size=5,readonly=False, states={'approved':[('readonly',True)]}),
		'amount_total_amend': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',
			store={
				'kg.purchase.amendment': (lambda self, cr, uid, ids, c={}: ids, ['amendment_line'], 10),
				'kg.purchase.amendment.line': (_get_order, ['price_unit_amend', 'tax_id', 'kg_discount_amend', 'product_qty_amend'], 10),
				
			}, multi="sums",help="The total amount"),
			
		# Entry Info
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'created_by':fields.many2one('res.users','Created By',readonly=True),
		'creation_date':fields.datetime('Created Date',readonly=True),
		'confirmed_by':fields.many2one('res.users','Confirmed By',readonly=True),
		'confirmed_date':fields.datetime('Confirmed Date',readonly=True),
		'approved_by':fields.many2one('res.users','Approved By',readonly=True),
		'approved_date':fields.datetime('Approved Date',readonly=True),
		'update_user_id':fields.many2one('res.users','Last Updated By',readonly=True),
		'update_date':fields.datetime('Last Updated Date',readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		
	}
	
	_defaults = {
	
		'date': lambda * a: time.strftime('%Y-%m-%d'),
		'state': 'amend',
		'active': True,
		'name': '/',
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'created_by': lambda obj, cr, uid, context: uid,
		'pricelist_id': 2,
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.purchase.amendment', context=c),
	
	}
	
	def _check_advance(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state not in ('draft','amend'):
			if rec.bill_type_amend == 'advance':
				if rec.advance_amt_amend <= 0.00:
					raise osv.except_osv(_('Warning !'),
						_('System sholud not be accecpt with out Advance !'))
				elif rec.advance_amt_amend > 100:
					raise osv.except_osv(_('Warning !'),
						_('System sholud not be greater than 100 !'))
				else:
					pass
		return True
	
	_constraints = [
	
		(_check_advance,'System sholud not be accecpt with out Advance !',['']),
	
	]
	
	def onchange_poid(self, cr, uid, ids,po_id, pricelist_id):
		po_obj = self.pool.get('purchase.order')
		value = {'pricelist_id': ''}
		if po_id:
			po_record = po_obj.browse(cr,uid,po_id)
			price_id = po_record.pricelist_id.id
			value = {'pricelist_id': price_id}
			return {'value':value}	
		else:
			print "No Change"
			
	def unlink(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		amend = self.read(cr, uid, ids, ['state'], context=context)
		unlink_ids = []
		for t in amend:
			if t['state'] in ('amend'):
				unlink_ids.append(t['id'])
			else:
				raise osv.except_osv(_('Invalid action !'), _('System not allow to delete a UN-DRAFT state Purchase Amendment!!'))
		amend_lines_to_del = self.pool.get('kg.purchase.amendment.line').search(cr, uid, [('amendment_id','in',unlink_ids)])
		self.pool.get('kg.purchase.amendment.line').unlink(cr, uid, amend_lines_to_del)
		osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		return True
	
	def _prepare_amend_line(self, cr, uid, po_order, order_line, amend_id, context=None):
		return {
		
			'order_id':po_order.id,
			'po_type': po_order.po_type,
			'product_id': order_line.product_id.id,
			'product_id_amend': order_line.product_id.id,
			'product_uom': order_line.product_uom.id,
			'product_uom_amend': order_line.product_uom.id,
			'brand_id':order_line.brand_id.id,
			'brand_id_amend':order_line.brand_id.id,
			'moc_id':order_line.moc_id.id,
			'moc_id_amend':order_line.moc_id.id,
			'moc_id_temp':order_line.moc_id_temp.id,
			'moc_id_temp_amend':order_line.moc_id_temp.id,
			'product_qty': order_line.product_qty,
			'product_qty_amend' : order_line.product_qty,
			'pending_qty' : order_line.pending_qty,
			'pending_qty_amend' : order_line.pending_qty,
			'received_qty' : order_line.product_qty - order_line.pending_qty,
			'price_unit' : order_line.price_unit or 0.0,
			'price_unit_amend' : order_line.price_unit or 0.0,
			
			'length' : order_line.length,
			'length_amend' : order_line.length,
			'breadth' : order_line.breadth,
			'breadth_amend' : order_line.breadth,
			'quantity' : order_line.quantity,
			'quantity_amend' : order_line.quantity,
			'price_type' : order_line.price_type,
			'price_type_amend' : order_line.price_type,
			'uom_conversation_factor' : order_line.uom_conversation_factor,
			'uom_conversation_factor_amend' : order_line.uom_conversation_factor,
			
			'pi_qty' : order_line.pi_qty,
			
			'kg_discount' : order_line.kg_discount,
			'kg_discount_amend' : order_line.kg_discount,
			'kg_discount_per' : order_line.kg_discount_per,
			'kg_discount_per_amend' : order_line.kg_discount_per,
			'kg_discount_per_value' : order_line.kg_discount_per_value,
			'kg_discount_per_value_amend' : order_line.kg_discount_per_value,
			'kg_disc_amt_per':order_line.kg_disc_amt_per,
			'kg_disc_amt_per_amend':order_line.kg_disc_amt_per,
			'po_price_subtotal': order_line.price_subtotal,
			'price_subtotal': order_line.price_subtotal,
			
			'note' : order_line.name or '',
			'note_amend' : order_line.name or '',			
			'amendment_id': amend_id,
			'po_line_id': order_line.id,
			'line_bill':order_line.line_bill,
			'pi_line_id': order_line.pi_line_id.id,
			
		}
	
	def make_amend(self,cr,uid,ids,amendment_id=False,context={}):
		
		po_id = False
		obj = self.browse(cr,uid,ids[0])
		print "Amend Obj ::::::::::",obj
		if obj.state == 'amend':
			po_obj=self.pool.get('purchase.order')
			amend_obj=self.pool.get('kg.purchase.amendment')
			amend_po_id = amend_obj.browse(cr,uid,obj.po_id.id)
			po_order = obj.po_id
			total_amends=amend_obj.search(cr,uid,[('po_id','=',obj.po_id.id)])
			draft_amends=amend_obj.search(cr,uid,[('po_id','=',obj.po_id.id),('state','not in',('approved','reject'))])
			if len(draft_amends) > 1:
				raise osv.except_osv(_('Amendment has been created for this PO!'),
					_('Please approve that for proceed another Amendment!!')) 
			
			sql = """delete from kg_purchase_amendment where state='amend' and id !=%s"""%(str(ids[0]))
			cr.execute(sql)
			if po_order.picking_ids:
				grn = True
			else:
				grn = False			
			if len(total_amends) == 1:
				amend_no = po_order.name + '-01'
			else:
				amend_no = po_order.name + '-' + '%02d' % int(str(len(total_amends)))
			
			if obj.partner_id.id is False:
			
				vals = {
				
							'amend_flag': True,
							'name' : amend_no, 
							'po_date': po_order.date_order,
							'po_date_amend': po_order.date_order,
							'partner_id': po_order.dest_address_id.id or po_order.partner_id.id,
							'partner_id_amend': po_order.dest_address_id.id or po_order.partner_id.id,
							'pricelist_id': po_order.pricelist_id.id,
							'currency_id': po_order.currency_id.id,
							'bill_type': po_order.bill_type,
							'bill_type_amend' : po_order.bill_type,
							'payment_mode' : po_order.payment_mode.id,
							'payment_mode_amend' : po_order.payment_mode.id,
							'delivery_mode' : po_order.delivery_mode.id,
							'delivery_mode_amend' : po_order.delivery_mode.id,
							'po_type': po_order.po_type,
							'po_type_amend': po_order.po_type,
							'po_expenses_type1' : po_order.po_expenses_type1,
							'po_expenses_type1_amend' : po_order.po_expenses_type1,
							'po_expenses_type2' : po_order.po_expenses_type2,
							'po_expenses_type2_amend' : po_order.po_expenses_type2,
							'value1' : po_order.value1,
							'value1_amend' : po_order.value1,
							'value2' : po_order.value2,
							'value2_amend' : po_order.value2,			
							'other_charge':po_order.other_charge,
							'grn_flag': grn,
							'remark':po_order.note,
							'terms':po_order.notes,
							'add_text':po_order.add_text,
							'add_text_amend':po_order.add_text,
							'delivery_address':po_order.delivery_address,
							'delivery_address_amend':po_order.delivery_address,
							'price':po_order.term_price,
							'price_amend':po_order.term_price,
							'quot_ref_no':po_order.quot_ref_no,
							'quot_ref_no_amend':po_order.quot_ref_no,
							'term_warranty':po_order.term_warranty,
							'term_warranty_amend':po_order.term_warranty,
							'term_freight':po_order.term_freight,
							'term_freight_amend':po_order.term_freight,
							'mode_of_dispatch':po_order.mode_of_dispatch.id,
							'mode_of_dispatch_amend':po_order.mode_of_dispatch.id,
							'insurance':po_order.insurance,
							'insurance_amend':po_order.insurance,
							'purpose':po_order.purpose,
							'purpose_amend':po_order.purpose,
							'quotation_date':po_order.quotation_date,
							'quotation_date_amend':po_order.quotation_date,
							'excise_duty':po_order.excise_duty,
							'excise_duty_amend':po_order.excise_duty,
							'item_quality_term_id':[(6, 0, [x.id for x in po_order.item_quality_term_id])],
							'item_quality_term_id_amend':[(6, 0, [x.id for x in po_order.item_quality_term_id])],
							'division':po_order.division,
							'division_amend':po_order.division,
							'amendment_line' : [],
							'total_amount':po_order.total_amount,
							'total_amount_amend':po_order.total_amount,
							'discount':po_order.discount,
							'discount_amend':po_order.discount,
							'amount_untaxed':po_order.amount_untaxed,
							'amount_untaxed_amend':po_order.amount_untaxed,
							'amount_tax':po_order.amount_tax,
							'amount_tax_amend':po_order.amount_tax,
							'grand_total':po_order.grand_total,
							'grand_total_amend':po_order.grand_total,
							'round_off':po_order.round_off,
							'round_off_amend':po_order.round_off,
							'amount_total':po_order.amount_total,
							'amount_total_amend':po_order.amount_total,
							
							}
				print "vals ..........",vals
				self.pool.get('kg.purchase.amendment').write(cr,uid,ids,vals)
					
				amend_id = obj.id
				todo_lines = []
				amend_line_obj = self.pool.get('kg.purchase.amendment.line')
				wf_service = netsvc.LocalService("workflow")
				order_lines=po_order.order_line
				self.write(cr,uid,ids[0],{'state':'draft',})
				for order_line in order_lines:
					if order_line.line_state != 'cancel' and order_line.line_bill == False:
						amend_line = amend_line_obj.create(cr, uid, self._prepare_amend_line(cr, uid, po_order, order_line, amend_id,
										context=context))
						cr.execute(""" select tax_id from purchase_order_taxe where ord_id = %s """  %(str(order_line.id)))
						data = cr.dictfetchall()
						val = [d['tax_id'] for d in data if 'tax_id' in d]
						for i in range(len(val)):
							cr.execute(""" INSERT INTO purchase_order_tax (amend_line_id,tax_id) VALUES(%s,%s) """ %(amend_line,val[i]))
							cr.execute(""" INSERT INTO amendment_order_tax (amend_line_id,tax_id) VALUES(%s,%s) """ %(amend_line,val[i]))
						todo_lines.append(amend_line_obj)
					else:
						print "NO Qty or Cancel"
					
				wf_service.trg_validate(uid, 'kg.purchase.amendment', amend_id, 'button_confirm', cr)
				return [amend_id]
				cr.close()
			else:
				raise osv.except_osv(_('Amendment Created Already!'),
					_('System not allow to create Amendment again !!')) 
				
	def confirm_amend(self, cr, uid, ids,context=None):
		amend_obj = self.browse(cr,uid,ids[0])
		if amend_obj.state == 'draft':
			po_obj = self.pool.get('purchase.order')
			product_obj = self.pool.get('product.product')
			po_line_obj = self.pool.get('purchase.order.line')
			amend_line_obj = self.pool.get('kg.purchase.amendment.line')
			pi_line_obj = self.pool.get('purchase.requisition.line')
			stock_move_obj = self.pool.get('stock.move')
			for amend_line in amend_obj.amendment_line:
				po_line_id = amend_line.po_line_id.id
				po_rec = amend_obj.po_id
				pol_record = amend_line.po_line_id
				diff_qty = amend_line.product_qty - amend_line.product_qty_amend
				pending_diff_qty = amend_line.product_qty - amend_line.pending_qty
				if amend_obj.po_type == 'frompi':
					if amend_line.product_qty < amend_line.product_qty_amend:
						pi_line_record = pi_line_obj.browse(cr, uid,pol_record.pi_line_id.id)
						if pi_line_record.pending_qty <= 0:
							if not amend_line.kg_poindent_lines:
								raise osv.except_osv(_('If you want to increase PO Qty'),
									_('Select PI for this Product')) 
							else:
								for ele in amend_line.kg_poindent_lines:
									if ele.product_id.id == amend_line.product_id.id:
										if (amend_line.product_qty_amend - amend_line.product_qty) <= ele.pending_qty:
											pi_line_obj.write(cr,uid,pi_line_record.id,{'pending_qty': 0}) 
											amend_line_obj.write(cr,uid,amend_line.id,{'pi_line_id':ele.id})
											line_pending = ele.pending_qty - (amend_line.product_qty_amend - amend_line.product_qty)
											print"line_pending",line_pending
											pi_line_obj.write(cr,uid,ele.id,{'pending_qty': line_pending}) 
										else:
											raise osv.except_osv(_('Warning!'),
												_('Amendment Qty is greater than indent qty'))
						else:
							pass
					else:
						grn_id = self.pool.get('po.grn.line').search(cr, uid, [('po_line_id','=',amend_line.po_line_id.id)])
						if grn_id:
							grn_bro = self.pool.get('po.grn.line').browse(cr, uid, grn_id[0])
							if grn_bro.po_grn_qty <= amend_line.product_qty_amend:
								pass
							else:
								raise osv.except_osv(_('You can not decrease PO Qty'),
									_('Because GRN is already created'))
						else:
							pass
					if amend_line.product_qty != amend_line.product_qty_amend:
						if amend_line.pending_qty == 0 and not amend_line.kg_poindent_lines:
							raise osv.except_osv(_('All Qty has received for this PO !'),
								_('You can not increase PO Qty for product %s')%(amend_line.product_id.name))
					else:
						pass
					if amend_line.product_id != amend_line.product_id_amend:
						if not amend_line.kg_poindent_lines:
							raise osv.except_osv(_('If you want to change PO Product'),
								_('Select PI for this Product')) 
				elif amend_obj.po_type == 'direct' or amend_obj.po_type == 'fromquote':
					grn_id = self.pool.get('po.grn.line').search(cr, uid, [('po_line_id','=',amend_line.po_line_id.id)])
					if grn_id:
						grn_bro = self.pool.get('po.grn.line').browse(cr, uid, grn_id[0])
						if grn_bro.po_grn_qty <= amend_line.product_qty_amend:
							pass
						else:
							raise osv.except_osv(_('You can not decrease PO Qty'),
								_('Because GRN is already created'))
					else:
						pass
					if amend_line.product_qty != amend_line.product_qty_amend:
						if amend_line.pending_qty == 0 and not amend_line.kg_poindent_lines:
							raise osv.except_osv(_('All Qty has received for this PO !'),
								_('You can not increase PO Qty for product %s')%(amend_line.product_id.name))
					else:
						pass
					#~ if amend_line.product_id != amend_line.product_id_amend:
						#~ if not amend_line.kg_poindent_lines:
							#~ raise osv.except_osv(
								#~ _('If you want to change PO Product'),
								#~ _('Select PI for this Product')) 
				if amend_line.price_type == 'per_kg':
					if amend_line.product_id_amend.uom_conversation_factor == 'two_dimension':
						if amend_line.product_id_amend.po_uom_in_kgs > 0:
							qty = amend_line.product_qty_amend * amend_line.product_id_amend.po_uom_in_kgs * amend_line.length_amend * amend_line.breadth_amend
					elif amend_line.product_id_amend.uom_conversation_factor == 'one_dimension':
						if amend_line.product_id_amend.po_uom_in_kgs > 0:
							qty = amend_line.product_qty_amend * amend_line.product_id_amend.po_uom_in_kgs
						else:
							qty = amend_line.product_qty_amend
					else:
						qty = amend_line.product_qty_amend
				else:
					qty = amend_line.product_qty_amend
				
				self.pool.get('kg.purchase.amendment.line').write(cr,uid,amend_line.id,{'quantity_amend':qty})
								
			self.write(cr,uid,ids[0],{
									  'state':'confirm',
									  'confirmed_by':uid,
									  'confirmed_date':time.strftime('%Y-%m-%d %H:%M:%S'),
									   })
						
		return True
	
	def cancel_amend(self, cr, uid, ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state in ('confirm','amend'):
			if not rec.cancel_note:
				raise osv.except_osv(_('Warning!'),
					_('Please give reason for this cancellation'))
			else:	
				self.write(cr,uid,ids[0],{'state':'cancel'})
		
		return True
	
	def write(self, cr, uid, ids, vals, context=None):		
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_purchase_amendment, self).write(cr, uid, ids, vals, context)
			
	def approve_amend(self,cr,uid,ids,context={}):
		
		amend_obj = self.browse(cr,uid,ids[0])
		if amend_obj.state == 'confirm':
			po_obj = self.pool.get('purchase.order')
			grn_obj = self.pool.get('kg.po.grn')
			grn_line_obj = self.pool.get('po.grn.line')
			invoice_obj = self.pool.get('kg.purchase.invoice')
			invoice_line_obj = self.pool.get('ch.invoice.line')
			product_obj = self.pool.get('product.product')
			po_line_obj = self.pool.get('purchase.order.line')
			amend_line_obj = self.pool.get('kg.purchase.amendment.line')
			pi_line_obj = self.pool.get('purchase.requisition.line')
			stock_move_obj = self.pool.get('stock.move')
			stock_lot_obj = self.pool.get('stock.production.lot')
			po_id = False 
			
			#~ if amend_obj.bill_type_amend == 'advance':
				#~ pre_obj = self.pool.get('kg.supplier.advance').search(cr,uid,[('po_id','=',amend_obj.po_id.id),('state','!=','cancel')])
				#~ if not pre_obj:
					#~ self.advance_creation(cr,uid,amend_obj)
			#~ elif amend_obj.bill_type_amend in ('cash','credit'):
				#~ if amend_obj.bill_type == 'advance':
					#~ pre_obj = self.pool.get('kg.supplier.advance').search(cr,uid,[('po_id','=',amend_obj.po_id.id),('state','!=','cancel')])
					#~ if pre_obj:
						#~ raise osv.except_osv(_('Warning!'),
							#~ _('Please cancel or delete supplier advance for this PO %s!'%(amend_obj.po_id.name)))
			#~ else:
				#~ pass
				
			if amend_obj.amendment_line ==[]:
				raise osv.except_osv(_('Empty Purchase Amendment!'),
					_('System not allow to confirm a PO Amendment without Amendment Line !!'))
			#if amend_obj.po_id.bill_flag == True:
				#raise osv.except_osv(
				#_('System not allow for Amendment!'),
				#_('This Purchase Order has invoiced already..!!'))			
			else:			
				po_id = amend_obj.po_id.id
				po_record = po_obj.browse(cr,uid,po_id)
				po_obj.write(cr,uid,po_id,{'amend_flag': True})
				if amend_obj.partner_id.id != amend_obj.partner_id_amend.id:
					po_obj.write(cr,uid,po_id,{'partner_id': amend_obj.partner_id_amend.id,'add_test':amend_obj.add_text_amend})
				if amend_obj.po_date != amend_obj.po_date_amend:
					po_obj.write(cr,uid,po_id,{'date_order': amend_obj.po_date_amend})
				if amend_obj.quot_ref_no != amend_obj.quot_ref_no_amend:
					po_obj.write(cr,uid,po_id,{'quot_ref_no': amend_obj.quot_ref_no_amend})
				if amend_obj.price != amend_obj.price_amend:
					po_obj.write(cr,uid,po_id,{'price': amend_obj.price_amend})
				
				if amend_obj.total_amount != amend_obj.total_amount_amend:
					po_obj.write(cr,uid,po_id,{'total_amount': amend_obj.total_amount_amend})
				if amend_obj.discount != amend_obj.discount_amend:
					po_obj.write(cr,uid,po_id,{'discount': amend_obj.discount_amend})
				if amend_obj.amount_untaxed != amend_obj.amount_untaxed_amend:
					po_obj.write(cr,uid,po_id,{'amount_untaxed': amend_obj.amount_untaxed_amend})
				if amend_obj.amount_tax != amend_obj.amount_tax_amend:
					po_obj.write(cr,uid,po_id,{'amount_tax': amend_obj.amount_tax_amend})
				if amend_obj.grand_total != amend_obj.grand_total_amend:
					po_obj.write(cr,uid,po_id,{'grand_total': amend_obj.grand_total_amend})
				if amend_obj.round_off != amend_obj.round_off_amend:
					po_obj.write(cr,uid,po_id,{'round_off': amend_obj.round_off_amend})
				if amend_obj.amount_total != amend_obj.amount_total_amend:
					po_obj.write(cr,uid,po_id,{'amount_total': amend_obj.amount_total_amend})
				
				if amend_obj.payment_mode.id != amend_obj.payment_mode_amend.id:
					po_obj.write(cr,uid,po_id,{'payment_mode': amend_obj.payment_mode_amend.id})
				if amend_obj.mode_of_dispatch.id != amend_obj.mode_of_dispatch_amend.id:
					po_obj.write(cr,uid,po_id,{'mode_of_dispatch': amend_obj.mode_of_dispatch_amend.id})
				if amend_obj.insurance != amend_obj.insurance_amend:
					po_obj.write(cr,uid,po_id,{'insurance': amend_obj.insurance_amend})
				if amend_obj.purpose != amend_obj.purpose_amend:
					po_obj.write(cr,uid,po_id,{'purpose': amend_obj.purpose_amend})
				if amend_obj.quotation_date != amend_obj.quotation_date_amend:
					po_obj.write(cr,uid,po_id,{'quotation_date': amend_obj.quotation_date_amend})
				if amend_obj.excise_duty != amend_obj.excise_duty_amend:
					po_obj.write(cr,uid,po_id,{'excise_duty': amend_obj.excise_duty_amend})
				if amend_obj.division != amend_obj.division_amend:
					po_obj.write(cr,uid,po_id,{'division': amend_obj.division_amend})
				if amend_obj.item_quality_term_id != amend_obj.item_quality_term_id_amend:
					po_obj.write(cr,uid,po_id,{'item_quality_term_id': [(6, 0, [x.id for x in amend_obj.item_quality_term_id_amend])]})
				if amend_obj.advance_amt != amend_obj.advance_amt_amend:
					po_obj.write(cr,uid,po_id,{'advance_amt': amend_obj.advance_amt_amend})
				if amend_obj.delivery_mode.id != amend_obj.delivery_mode_amend.id:
					po_obj.write(cr,uid,po_id,{'delivery_mode': amend_obj.delivery_mode_amend.id})
				if amend_obj.term_freight != amend_obj.term_freight_amend:
					po_obj.write(cr,uid,po_id,{'term_freight': amend_obj.term_freight_amend})	
				if amend_obj.term_warranty != amend_obj.term_warranty_amend:
					po_obj.write(cr,uid,po_id,{'term_warranty': amend_obj.term_warranty_amend})		
				if amend_obj.po_expenses_type1 != amend_obj.po_expenses_type1_amend:
					po_obj.write(cr,uid,po_id,{'po_expenses_type1': amend_obj.po_expenses_type1_amend})
				if amend_obj.po_expenses_type2 != amend_obj.po_expenses_type2_amend:
					po_obj.write(cr,uid,po_id,{'po_expenses_type2': amend_obj.po_expenses_type2_amend})
				if amend_obj.value1 != amend_obj.value1_amend or amend_obj.value2 != amend_obj.value2_amend:
					tot_value = amend_obj.value1_amend + amend_obj.value2_amend
					po_obj.write(cr,uid,po_id,{
						'value1': amend_obj.value1_amend,
						'value2': amend_obj.value2_amend,
						'other_charge' : tot_value,
							})
				version = amend_obj.name[-2:]			
				po_obj.write(cr,uid,po_id,{
						'notes':amend_obj.terms,
						'note':amend_obj.remark,
						'version':version,
						})
			
			for amend_line in amend_obj.amendment_line:
				po_line_id = amend_line.po_line_id.id
				po_rec = amend_obj.po_id
				pol_record = amend_line.po_line_id
				diff_qty = amend_line.product_qty - amend_line.product_qty_amend
				pending_diff_qty = amend_line.product_qty - amend_line.pending_qty
				if pol_record.pi_line_id.id:
					if amend_line.product_qty < amend_line.product_qty_amend:
						pi_line_record = pi_line_obj.browse(cr, uid,pol_record.pi_line_id.id)
						if pi_line_record.pending_qty <= 0:
							if not amend_line.kg_poindent_lines:
								raise osv.except_osv(_('If you want to increase PO Qty'),
									_('Select PI for this Product')) 
						else:
							pi_product_qty = pi_line_record.product_qty
							pi_pending_qty = pi_line_record.pending_qty
							re_qty = amend_line.product_qty_amend-amend_line.product_qty
							if pi_pending_qty >= re_qty:
								amend_pend = pi_pending_qty - re_qty
								pi_line_obj.write(cr,uid,pol_record.pi_line_id.id,{'pending_qty' : amend_pend})
							else: 
								amend_pro_qty = re_qty - pi_pending_qty 
								pi_product_qty += amend_pro_qty
								pi_line_obj.write(cr,uid,pol_record.pi_line_id.id,{'pending_qty' : 0,'product_qty' : pi_product_qty})
					else:
						grn_id = self.pool.get('po.grn.line').search(cr, uid, [('po_line_id','=',amend_line.po_line_id.id)])
						if grn_id:
							grn_bro = self.pool.get('po.grn.line').browse(cr, uid, grn_id[0])
							if grn_bro.po_grn_qty <= amend_line.product_qty_amend:
								pi_line_record = pi_line_obj.browse(cr, uid,pol_record.pi_line_id.id)
								pi_pending_qty = pi_line_record.pending_qty
								re_qty = amend_line.product_qty - amend_line.product_qty_amend
								pi_pending_qty += re_qty
								pi_line_obj.write(cr,uid,pol_record.pi_line_id.id,{'pending_qty' : pi_pending_qty})
							else:
								raise osv.except_osv(_('You can not decrease PO Qty'),
									_('Because GRN is already created'))
						else:
							pi_line_record = pi_line_obj.browse(cr, uid,pol_record.pi_line_id.id)
							pi_pending_qty = pi_line_record.pending_qty
							re_qty = amend_line.product_qty - amend_line.product_qty_amend
							pi_pending_qty += re_qty
							pi_line_obj.write(cr,uid,pol_record.pi_line_id.id,{'pending_qty' : pi_pending_qty})
							
					if amend_line.line_state == 'cancel':
						if pol_record.pi_line_id:					
							pi_line_record = pi_line_obj.browse(cr, uid,pol_record.pi_line_id.id)
							pi_product_qty = pi_line_record.product_qty
							pi_pending_qty = pi_line_record.pending_qty
							pi_product_qty += pol_record.product_qty
							pi_pending_qty += pol_record.pending_qty
							pi_line_obj.write(cr,uid,pol_record.pi_line_id.id,{'pending_qty' : pi_pending_qty})
							po_line_obj.write(cr,uid,po_line_id,{'line_state': amend_line.line_state,
																 'cancel_qty' :amend_line.cancel_qty,
																 'received_qty':amend_line.received_qty,
																  })
						else:
							po_line_obj.write(cr,uid,po_line_id,{'line_state': amend_line.line_state,
																 'cancel_qty' :amend_line.cancel_qty,
																 'received_qty':amend_line.received_qty,
																 })
					if amend_line.product_qty != amend_line.product_qty_amend:
						grn_sql = """ select sum(po_qty) - sum(po_grn_qty) as bal_po_grn_qty from po_grn_line where po_id = %s and product_id = %s """%(amend_obj.po_id.id,amend_line.product_id.id)
						cr.execute(grn_sql)		
						grn_data = cr.dictfetchall()
						if grn_data:
							if grn_data[0]['bal_po_grn_qty'] == 0:
								raise osv.except_osv(_('Please Check GRN!'),
									_('GRN Already Created For This PO!!'))
						if amend_line.pending_qty == 0 and not amend_line.kg_poindent_lines:
							raise osv.except_osv(_('All Qty has received for this PO !'),
								_('You can not increase PO Qty for product %s')%(amend_line.product_id.name))
						disc_value = (amend_line.product_qty_amend * amend_line.price_unit_amend) * amend_line.kg_discount_per_amend / 100
						print "kg_discount_per_value :::::::::::::::", disc_value
						po_line_obj.write(cr,uid,po_line_id,{
								'product_qty': amend_line.product_qty_amend,
								'pending_qty': amend_line.pending_qty_amend,
								'kg_discount_per_value' : disc_value,
									})
					
					if amend_line.price_unit != amend_line.price_unit_amend:
						pinv_obj = self.pool.get('kg.purchase.invoice').search(cr,uid,[('po_so_name','=',amend_obj.po_id.name),('state','=','approved')])
						print"pinv_objpinv_obj",pinv_obj
						if pinv_obj:
							raise osv.except_osv(_('Please Check Invoice!'),
								_('Invoice Already Created For This PO!!'))
						po_line_obj.write(cr,uid,po_line_id,{
							'price_unit': amend_line.price_unit_amend})
					if amend_line.brand_id.id != amend_line.brand_id_amend.id:
						grn_sql = """ select sum(po_qty) - sum(po_grn_qty) as bal_po_grn_qty from po_grn_line where po_id = %s and product_id = %s """%(amend_obj.po_id.id,amend_line.product_id.id)
						cr.execute(grn_sql)		
						grn_data = cr.dictfetchall()
						if grn_data:
							if grn_data[0]['po_grn_qty'] == 0:
								raise osv.except_osv(_('Please Check GRN!'),
									_('GRN Already Created For This PO!!'))
						po_line_obj.write(cr,uid,po_line_id,{
							'brand_id': amend_line.brand_id_amend.id})	
					if amend_line.price_type_amend == 'per_kg':
						if amend_line.product_id_amend.uom_conversation_factor == 'two_dimension':
							if amend_line.product_id_amend.po_uom_in_kgs > 0:
								qty = amend_line.product_qty_amend * amend_line.product_id_amend.po_uom_in_kgs * amend_line.length_amend * amend_line.breadth_amend
						elif amend_line.product_id_amend.uom_conversation_factor == 'one_dimension':
							if amend_line.product_id_amend.po_uom_in_kgs > 0:
								qty = amend_line.product_qty_amend * amend_line.product_id_amend.po_uom_in_kgs
							else:
								qty = amend_line.product_qty_amend
						else:
							qty = amend_line.product_qty_amend
					else:
						qty = amend_line.product_qty_amend
					self.pool.get('kg.purchase.amendment.line').write(cr,uid,amend_line.id,{'quantity_amend':qty})	
					
				else:
					
					if amend_line.product_qty != amend_line.product_qty_amend:
						grn_sql = """ select sum(po_qty) - sum(po_grn_qty) as bal_po_grn_qty from po_grn_line where po_id = %s and product_id = %s """%(amend_obj.po_id.id,amend_line.product_id.id)
						cr.execute(grn_sql)		
						grn_data = cr.dictfetchall()
						if grn_data:
							if grn_data[0]['bal_po_grn_qty'] == 0:
								raise osv.except_osv(_('Please Check GRN!'),
									_('GRN Already Created For This PO!!'))
						if amend_line.pending_qty == 0 and not amend_line.kg_poindent_lines:
							raise osv.except_osv(_('All Qty has received for this PO !'),
								_('You can not increase PO Qty for product %s')%(amend_line.product_id.name))
						disc_value = (amend_line.product_qty_amend * amend_line.price_unit_amend) * amend_line.kg_discount_per_amend / 100
						po_line_obj.write(cr,uid,po_line_id,{
								'product_qty': amend_line.product_qty_amend,
								'pending_qty': amend_line.pending_qty_amend,
								'kg_discount_per_value' : disc_value,
									})
					
					if amend_line.price_unit != amend_line.price_unit_amend:
						pinv_obj = self.pool.get('kg.purchase.invoice').search(cr,uid,[('po_so_name','=',amend_obj.po_id.name),('state','=','approved')])
						if pinv_obj:
							raise osv.except_osv(_('Please Check Invoice!'),
								_('Invoice Already Created For This PO!!'))
						
						po_line_obj.write(cr,uid,po_line_id,{
							'price_unit': amend_line.price_unit_amend})
					if amend_line.brand_id.id != amend_line.brand_id_amend.id:
						grn_sql = """ select sum(po_qty) - sum(po_grn_qty) as bal_po_grn_qty from po_grn_line where po_id = %s and product_id = %s """%(amend_obj.po_id.id,amend_line.product_id.id)
						cr.execute(grn_sql)		
						grn_data = cr.dictfetchall()
						if grn_data:
							if grn_data[0]['bal_po_grn_qty'] == 0:
								raise osv.except_osv(_('Please Check GRN!'),
									_('GRN Already Created For This PO!!'))
						po_line_obj.write(cr,uid,po_line_id,{
							'brand_id': amend_line.brand_id_amend.id})
					if amend_line.moc_id.id != amend_line.moc_id_amend.id:
						po_line_obj.write(cr,uid,po_line_id,{
							'moc_id': amend_line.moc_id_amend.id})
					if amend_line.moc_id_temp.id != amend_line.moc_id_temp_amend.id:
						po_line_obj.write(cr,uid,po_line_id,{
							'moc_id_temp': amend_line.moc_id_temp_amend.id})
					if amend_line.product_id.id != amend_line.product_id_amend.id:
						po_grn_obj = self.pool.get('po.grn.line').search(cr,uid,[('po_id','=',amend_obj.po_id.id)])
						if po_grn_obj:
							raise osv.except_osv(_('Please Check GRN!'),
								_('GRN Already Created For This PO!!'))
						po_line_obj.write(cr,uid,po_line_id,{'product_id': amend_line.product_id_amend.id})
				
				# PO Line updation
				
				if amend_line.kg_discount != amend_line.kg_discount_amend:
					po_line_obj.write(cr,uid,po_line_id,{'kg_discount': amend_line.kg_discount_amend})
				if amend_line.kg_discount_per != amend_line.kg_discount_per_amend:
					po_line_obj.write(cr,uid,po_line_id,{'kg_discount_per': amend_line.kg_discount_per_amend}) 
				if amend_line.kg_disc_amt_per != amend_line.kg_disc_amt_per_amend:
					po_line_obj.write(cr,uid,po_line_id,{'kg_disc_amt_per': amend_line.kg_disc_amt_per_amend})
				if amend_line.kg_discount_per_value != amend_line.kg_discount_per_value_amend:
					po_line_obj.write(cr,uid,po_line_id,{'kg_discount_per_value': amend_line.kg_discount_per_value_amend})
				if amend_line.note != amend_line.note_amend:
					po_line_obj.write(cr,uid,po_line_id,{'name': amend_line.note_amend})
				
				if amend_line.brand_id.id != amend_line.brand_id_amend.id:
					po_line_obj.write(cr,uid,po_line_id,{'brand_id': amend_line.brand_id_amend.id})
				if amend_line.moc_id_temp.id != amend_line.moc_id_temp_amend.id:
					po_line_obj.write(cr,uid,po_line_id,{'moc_id_temp': amend_line.moc_id_temp_amend.id})
				if amend_line.moc_id.id != amend_line.moc_id_amend.id:
					po_line_obj.write(cr,uid,po_line_id,{'moc_id': amend_line.moc_id_amend.id})
				if amend_line.product_qty != amend_line.product_qty_amend:
					po_line_obj.write(cr,uid,po_line_id,{'product_qty': amend_line.product_qty_amend})
				if amend_line.product_uom != amend_line.product_uom_amend:
					po_line_obj.write(cr,uid,po_line_id,{'product_uom': amend_line.product_uom_amend})
				if amend_line.price_unit != amend_line.price_unit_amend:
					po_line_obj.write(cr,uid,po_line_id,{'price_unit': amend_line.price_unit_amend})
				if amend_line.quantity != amend_line.quantity_amend:
					po_line_obj.write(cr,uid,po_line_id,{'quantity': amend_line.quantity_amend})
				if amend_line.price_type != amend_line.price_type_amend:
					po_line_obj.write(cr,uid,po_line_id,{'price_type': amend_line.price_type_amend})
					
				if amend_line.product_id.id != amend_line.product_id_amend.id:
					po_grn_obj = self.pool.get('po.grn.line').search(cr,uid,[('po_id','=',amend_obj.po_id.id)])
					if po_grn_obj:
						raise osv.except_osv(_('Please Check GRN!'),
							_('GRN Already Created For This PO!!'))
					po_line_obj.write(cr,uid,po_line_id,{'product_id': amend_line.product_id_amend.id})
				cr.execute(""" select tax_id from amendment_order_tax where amend_line_id = %s """ %(amend_line.id))
				data = cr.dictfetchall()
				val = [d['tax_id'] for d in data if 'tax_id' in d]
				cr.execute(""" delete from purchase_order_taxe where ord_id=%s """ %(po_line_id))
				for i in range(len(val)):
					cr.execute(""" INSERT INTO purchase_order_taxe (ord_id,tax_id) VALUES(%s,%s) """ %(po_line_id,val[i]))
				else:
					print "NO PO Line Changs"
				amend_line.write({'line_state': 'done'})
				
				
			cr.execute(""" select count(id) from kg_purchase_amendment where state = 'approved' and po_id = %s """ %(amend_obj.po_id.id))
			revision_data = cr.dictfetchall()
			if revision_data:
				po_obj.write(cr,uid,amend_obj.po_id.id,{'revision': revision_data[0]['count']+1})
			print "Tax Calculation Methods are Going to Call"
			#po_line_obj._amount_line(cr,uid,[po_id],prop=None,arg=None,context=None)
			po_obj._amount_line_tax(cr,uid,pol_record,context=None)
			po_obj._amount_all(cr,uid,[po_id],field_name=None,arg=False,context=None)
			self.write(cr,uid,ids,{'state' : 'approved' ,'approved_by':uid,'approved_date':time.strftime('%Y-%m-%d %H:%M:%S'),})
			
			cr.execute(""" select grn_id from multiple_po where po_id = %s """ %(po_record.id))
			grn_data = cr.dictfetchall()
			if grn_data:
				for item in grn_data:
					grn_search = grn_obj.search(cr,uid,[('id','=',item['grn_id']),('state','not in',('inv','cancel','reject'))])
					if grn_search:
						grn_browse = grn_obj.browse(cr,uid,grn_search[0])
						grn_obj.write(cr,uid,grn_search[0],{'supplier_id': amend_obj.partner_id.id})
						for line_amend in amend_obj.amendment_line:
							grn_line_search = self.pool.get('po.grn.line').search(cr, uid, [('po_line_id','=',line_amend.po_line_id.id),('po_grn_id','=',grn_search[0])])
							if grn_line_search:
								grn_line_browse = self.pool.get('po.grn.line').browse(cr, uid, grn_line_search[0])
								grn_line_obj.write(cr,uid,grn_line_search[0],{'price_unit':line_amend.price_unit_amend,
									'kg_discount_per':line_amend.kg_discount_per_amend,'kg_discount':line_amend.kg_discount_amend,
									'grn_tax_ids':[(6, 0, [x.id for x in line_amend.taxes_id_amend])],'brand_id':line_amend.brand_id_amend.id or False})
								
								stock_move_search = stock_move_obj.search(cr,uid,[('po_grn_line_id','=',grn_line_search[0])])
								if stock_move_search:
									stock_move_browse = stock_move_obj.browse(cr,uid,stock_move_search[0])
									stock_move_obj.write(cr,uid,stock_move_search[0],{'price_unit':line_amend.price_unit_amend,'brand_id':line_amend.brand_id_amend.id or False})
								
								stock_lot_search = self.pool.get('stock.move').search(cr,uid,[('po_grn_line_id','=',grn_line_browse.id)])
								if stock_lot_search:
									stock_move_browse = stock_move_obj.browse(cr,uid,stock_move_search[0])
									for i in stock_lot_search:
										
										self.pool.get('stock.move').write(cr,uid,i,{'price_unit':line_amend.price_unit_amend,'brand_id':line_amend.brand_id_amend.id or False})
								
								inv_line_search = invoice_line_obj.search(cr,uid,[('po_line_id','=',line_amend.po_line_id.id),('po_grn_line_id','=',grn_line_search[0])])
								if inv_line_search:
									inv_line_browse = invoice_line_obj.browse(cr,uid,inv_line_search[0])
									invoice_line_obj.write(cr,uid,inv_line_search[0],{'price_unit':line_amend.price_unit_amend,
										'kg_discount_per':line_amend.kg_discount_per_amend,'discount':line_amend.kg_discount_amend,
										'invoice_tax_ids':[(6, 0, [x.id for x in line_amend.taxes_id_amend])],'brand_id':line_amend.brand_id_amend.id or False})
									ids =[]
									ids.append(inv_line_browse.invoice_header_id.id)
									invoice_obj.update_actual_values(cr, uid, ids,context=None)
					else:
						pass
		
		return True
		cr.close()
	
	def advance_creation(self,cr,uid,amend_obj,context=None):
		advance_amt = (amend_obj.po_id.amount_total / 100.00) * amend_obj.advance_amt_amend
		print"advance_amt",advance_amt
		sup_adv_id = self.pool.get('kg.supplier.advance').create(cr,uid,{'supplier_id': amend_obj.partner_id_amend.id,
															'order_category': 'purchase',
															'po_id': amend_obj.po_id.id,
															'advance_amt': advance_amt,
															'order_value': amend_obj.po_id.amount_total,
															'order_no': amend_obj.po_id.name,
															'entry_mode': 'auto',
															})
		sup_ids = self.pool.get('kg.supplier.advance').search(cr,uid,[('supplier_id','=',amend_obj.partner_id_amend.id),('state','=','confirmed')])
		if sup_ids:
			for ele in sup_ids:			
				adv_rec = self.pool.get('kg.supplier.advance').browse(cr,uid,ele)
				self.pool.get('ch.advance.line').create(cr,uid,{'header_id': sup_adv_id,
															   'advance_no':adv_rec.name,
															   'advance_date':adv_rec.entry_date,
															   'order_no':adv_rec.order_no,
															   'advance_amt':adv_rec.advance_amt,
															   'adjusted_amt':adv_rec.adjusted_amt,
															   'balance_amt':adv_rec.balance_amt,
																})
		
		return True
			
	def onchange_partner_id(self, cr, uid, ids, partner_id_amend,add_text_amend):
		logger.info('[KG OpenERP] Class: kg_purchase_order, Method: onchange_partner_id called...')
		partner = self.pool.get('res.partner')
		if not partner_id_amend:
			return {'value': {
				'add_text_amend': False,
				
				}}
		supplier_address = partner.address_get(cr, uid, [partner_id_amend], ['default'])
		supplier = partner.browse(cr, uid, partner_id_amend)
		tot_add = (supplier.street or '')+ ' ' + (supplier.street2 or '') + '\n'+(supplier.city_id.name or '')+ ',' +(supplier.state_id.name or '') + '-' +(supplier.zip or '') + '\nPh:' + (supplier.phone or '')+ '\n' +(supplier.mobile or '')		
		return {'value': {
			'add_text_amend' : tot_add or False
			}}
	
kg_purchase_amendment()


class kg_purchase_amendment_line(osv.osv):
	
	_name = "kg.purchase.amendment.line"
	
	def _amount_line(self, cr, uid, ids, prop, arg, context=None):
		cur_obj=self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		res = {}
		if context is None:
			context = {}
		#~ for line in self.browse(cr, uid, ids, context=context):
			#~ amt_to_per = (line.kg_discount_amend / (line.product_qty_amend * line.price_unit_amend or 1.0 )) * 100
			#~ kg_discount_per = line.kg_discount_per_amend
			#~ tot_discount_per = amt_to_per + kg_discount_per
			#~ price = line.price_unit_amend * (1 - (tot_discount_per or 0.0) / 100.0)
			#~ print"line.taxes_id_amend",line.taxes_id_amend
			#~ print"price",price
			#~ print"line.product_qty_amend",line.product_qty_amend
			#~ print"line.product_id_amend",line.product_id_amend
			#~ print"line.amendment_id.partner_id_amend",line.amendment_id.partner_id_amend
			#~ taxes = tax_obj.compute_all(cr, uid, line.taxes_id_amend, price, line.product_qty_amend, line.product_id_amend, 
								#~ line.amendment_id.partner_id_amend)
			#~ cur = line.amendment_id.pricelist_id.currency_id
			#~ res[line.id] = cur_obj.round(cr, uid, cur, taxes['total_included'])
		for line in self.browse(cr, uid, ids, context=context):
			# Qty Calculation
			qty = 0.00
			if line.price_type_amend == 'per_kg':
				if line.product_id_amend.uom_conversation_factor == 'two_dimension':
					if line.product_id_amend.po_uom_in_kgs > 0:
						qty = line.product_qty_amend * line.product_id_amend.po_uom_in_kgs * line.length_amend * line.breadth_amend
				elif line.product_id_amend.uom_conversation_factor == 'one_dimension':
					if line.product_id_amend.po_uom_in_kgs > 0:
						qty = line.product_qty_amend * line.product_id_amend.po_uom_in_kgs
					else:
						qty = line.product_qty_amend
				else:
					qty = line.product_qty_amend
			else:
				qty = line.product_qty_amend
			
			# Price Calculation
			price_amt = 0
			if line.price_type_amend == 'per_kg':
				if line.product_id_amend.po_uom_in_kgs > 0:
					price_amt = line.product_qty_amend / line.product_id_amend.po_uom_in_kgs * line.price_unit_amend
			else:
				price_amt = qty * line.price_unit_amend
			
			amt_to_per = (line.kg_discount_amend / (qty * line.price_unit_amend or 1.0 )) * 100
			kg_discount_per = line.kg_discount_per_amend
			tot_discount_per = amt_to_per + kg_discount_per
			price = line.price_unit_amend * (1 - (tot_discount_per or 0.0) / 100.0)
			taxes = tax_obj.compute_all(cr, uid, line.taxes_id_amend, price, qty, line.product_id_amend, line.amendment_id.partner_id_amend)
			cur = line.amendment_id.pricelist_id.currency_id
			res[line.id] = cur_obj.round(cr, uid, cur, taxes['total_included'])
		return res
	
	_columns = {
	
	'po_price_subtotal': fields.float('Subtotal'),
	'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
	'order_id': fields.many2one('purchase.order', 'Order ID'),
	'amendment_id':fields.many2one('kg.purchase.amendment','Amendment', select=True, required=True, ondelete='cascade'),
	'pi_line_id':fields.many2one('purchase.requisition.line','PI Line', invisible=True),
	'product_id':fields.many2one('product.product', 'Product', required=True,domain="[('state','not in',('reject','cancel')),('purchase_ok','=',True)]"),
	'kg_discount': fields.float('Discount Amount', digits_compute= dp.get_precision('Discount')),
	'price_unit': fields.float('Unit Price', digits_compute= dp.get_precision('Product Price')),
	'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
	'pending_qty': fields.float('Pending Qty'),
	'po_qty':fields.float('PI Qty'),
	'received_qty':fields.float('Received Qty'),
	'cancel_qty':fields.float('Cancel Qty'),
	'product_uom': fields.many2one('product.uom', 'UOM',required=True,readonly=True),
	'note': fields.text('Remarks'),
	'kg_discount_per': fields.float('Discount (%)', digits_compute= dp.get_precision('Discount')),
	'kg_discount_per_value': fields.float('Discount(%)Value', digits_compute= dp.get_precision('Discount')),
	'kg_disc_amt_per': fields.float('Discount(%)', digits_compute= dp.get_precision('Discount')),
	'po_line_id':fields.many2one('purchase.order.line', 'PO Line'),
	'taxes_id': fields.many2many('account.tax', 'purchase_order_tax', 'amend_line_id', 'tax_id','Taxes',readonly=True),
	'line_state': fields.selection([('draft', 'Draft'),('cancel', 'Cancel'),('done', 'Done')], 'Status'),
	'line_bill': fields.boolean('PO Bill'),
	'po_type': fields.selection([('direct', 'Direct'),('frompi', 'From PI')], 'PO Type',readonly=True),
	'brand_id':fields.many2one('kg.brand.master','Brand'),
	'moc_id': fields.many2one('kg.moc.master','MOC'),
	'moc_id_temp': fields.many2one('ch.brandmoc.rate.details','MOC',domain="[('brand_id','=',brand_id_amend),('header_id.product_id','=',product_id_amend),('header_id.state','in',('draft','confirmed','approved'))]"),
	
	'length': fields.float('Length',digits=(16,4),),
	'breadth': fields.float('Breadth',digits=(16,4)),
	'quantity': fields.float("Weight(Kg's)"),
	'price_type': fields.selection([('po_uom','PO UOM'),('per_kg','Per Kg')],'Price Type'),
	'pi_qty':fields.float('Indent Qty'),
	'uom_conversation_factor': fields.related('product_id','uom_conversation_factor', type='selection',selection=UOM_CONVERSATION, string='UOM Conversation Factor',store=True,required=True),
	
	'discount_per_flag': fields.boolean('Discount Amount Flag'),
	'discount_flag': fields.boolean('Discount Flag'),
	
	# Amendment Fields:
	
	'product_id_amend': fields.many2one('product.product','Amend Product'),
	'kg_discount_amend': fields.float('Amend Discount Amount', digits_compute= dp.get_precision('Discount')),
	'price_unit_amend': fields.float('Amend Unit Price', digits_compute= dp.get_precision('Product Price')),
	'product_qty_amend': fields.float('Amend Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
	'pending_qty_amend': fields.float('Amend Pending Qty',line_state={'cancel':[('readonly', True)]}),
	'po_qty_amend':fields.float('Amend PI Qty'),
	'kg_discount_per_amend': fields.float('Amend Discount (%)', digits_compute= dp.get_precision('Discount')),
	'kg_discount_per_value_amend': fields.float('Amend Discount(%)Value', digits_compute= dp.get_precision('Discount')),
	'kg_disc_amt_per_amend': fields.float('Amend Discount(%)', digits_compute= dp.get_precision('Discount')),
	'note_amend': fields.text('Amend Remarks'),
	'taxes_id_amend': fields.many2many('account.tax', 'amendment_order_tax', 'amend_line_id', 'tax_id','Amend Taxes'),
	'cancel_flag':fields.boolean('Flag'),
	'brand_id_amend':fields.many2one('kg.brand.master','Amend Brand',required=True,domain="[('product_ids','in',(product_id_amend)),('state','in',('draft','confirmed','approved'))]"),
	'moc_id_amend': fields.many2one('kg.moc.master','Amend MOC'),
	'moc_id_temp_amend': fields.many2one('ch.brandmoc.rate.details','Amend MOC',domain="[('brand_id','=',brand_id_amend),('header_id.product_id','=',product_id_amend),('header_id.state','in',('draft','confirmed','approved'))]"),
	'qty_flag': fields.boolean('QTY'),
	'kg_poindent_lines':fields.many2many('purchase.requisition.line','kg_poindent_po_line' , 'po_order_id', 'piline_id','POIndent Lines',
			domain="[('pending_qty','>','0'), '&',('line_state','=','process'), '&',('draft_flag','=', False),'&',('product_id','=',product_id)]"),
	
	'length_amend': fields.float('Amend Length',digits=(16,4)),
	'breadth_amend': fields.float('Amend Breadth',digits=(16,4)),
	'quantity_amend': fields.float("Amend Weight(Kg's)"),
	'product_uom_amend': fields.many2one('product.uom', 'Amend UOM'),
	'price_type_amend': fields.selection([('po_uom','PO UOM'),('per_kg','Per Kg')],'Amend Price Type'),
	'uom_conversation_factor_amend': fields.related('product_id_amend','uom_conversation_factor', type='selection',selection=UOM_CONVERSATION, string='UOM Conversation Factor',store=True,required=True),
	
	}
	
	_defaults = {
	
		'line_state': 'draft',
		'qty_flag': True,
		'discount_per_flag': False,
		'discount_flag': False,
		
		}
		
	def onchange_price_unit(self,cr,uid,price_unit,price_unit_amend,
					kg_discount_per_amend,kg_discount_per_value_amend,product_qty_amend):
						
		if price_unit != price_unit_amend:
			disc_value = (product_qty_amend * price_unit_amend) * kg_discount_per_amend / 100.00
			return {'value': {'kg_discount_per_value_amend': disc_value}}
		else:
			print "NO changes"
			
	def onchange_discount_value_calc(self, cr, uid, ids, kg_discount_per_amend,product_qty_amend,price_unit_amend):
		discount_value = (product_qty_amend * price_unit_amend) * kg_discount_per_amend / 100.00
		
		if discount_value:
			return {'value': {'kg_discount_per_value_amend': discount_value,'discount_flag':True}}
		else:
			return {'value': {'kg_discount_per_value_amend': discount_value,'discount_flag':False}}
		
	def onchange_disc_amt(self,cr,uid,ids,kg_discount_amend,product_qty_amend,price_unit_amend,kg_disc_amt_per_amend):
		logger.info('[KG OpenERP] Class: kg_purchase_order_line, Method: onchange_disc_amt called...')
		if kg_discount_amend:
			kg_discount_amend = kg_discount_amend + 0.00
			amt_to_per = (kg_discount_amend / (product_qty_amend * price_unit_amend or 1.0 )) * 100.00
			return {'value': {'kg_disc_amt_per_amend': amt_to_per,'discount_per_flag':True}}
		else:
			return {'value': {'kg_disc_amt_per_amend': 0.0,'discount_per_flag':False}}
		
	def onchange_qty(self, cr, uid, ids,product_qty,product_qty_amend,pending_qty,pending_qty_amend,pi_line_id,pi_qty,uom_conversation_factor_amend,length_amend,breadth_amend,price_type_amend,product_id_amend):	
		# Need to do block flow
		value = {'pending_qty_amend': '','quantity_amend': 0}
		quantity = 0
		if price_type_amend == 'per_kg':
			prod_rec = self.pool.get('product.product').browse(cr,uid,product_id_amend)
			if uom_conversation_factor_amend == 'two_dimension':
				if prod_rec.po_uom_in_kgs > 0:
					quantity = product_qty_amend * prod_rec.po_uom_in_kgs * length_amend * breadth_amend
			elif uom_conversation_factor_amend == 'one_dimension':
				if prod_rec.po_uom_in_kgs > 0:
					quantity = product_qty_amend * prod_rec.po_uom_in_kgs
				else:
					quantity = product_qty_amend
			else:
				quantity = product_qty_amend
		else:
			quantity = product_qty_amend
		if pi_line_id:
			if product_qty_amend and product_qty_amend > pi_qty:
				raise osv.except_osv(_('If PO From PI!'),_("PO Qty can not be greater than Indent Qty!") )
			else:
				if product_qty == pending_qty:
					value = {'pending_qty_amend': product_qty_amend,'quantity_amend': quantity}			
				else:
					if product_qty != product_qty_amend:
						po_pen_qty = product_qty - pending_qty
						amend_pen_qty = product_qty_amend - po_pen_qty
						value = {'pending_qty_amend': amend_pen_qty}
		else:
			if product_qty == pending_qty:
				value = {'pending_qty_amend': product_qty_amend,'quantity_amend': quantity}			
			else:
				if product_qty != product_qty_amend:
					po_pen_qty = product_qty - pending_qty
					amend_pen_qty = product_qty_amend - po_pen_qty
					value = {'pending_qty_amend': amend_pen_qty}
		if uom_conversation_factor_amend == 'two_dimension':
			if length_amend <= 0:
				raise osv.except_osv(_('Warning!'),_("You can not save this Length with Zero value!") )
			if breadth_amend <= 0:
				raise osv.except_osv(_('Warning!'),_("You can not save this Breadth with Zero value!") )
			
		#~ value = {'pending_qty_amend': ''}
		#~ if product_qty == pending_qty:
			#~ value = {'pending_qty_amend': product_qty_amend }			
		#~ else:
			#~ if product_qty != product_qty_amend:
				#~ po_pen_qty = product_qty - pending_qty
				#~ amend_pen_qty = product_qty_amend - po_pen_qty
				#~ value = {'pending_qty_amend': amend_pen_qty}
			#~ else:
				#~ value = {'pending_qty_amend': pending_qty}
		return {'value': value}
	
	def onchange_price_type(self, cr, uid, ids,product_qty_amend,uom_conversation_factor_amend,length_amend,breadth_amend,price_type_amend,product_id_amend):
		value = {'quantity': 0}
		quantity = 0
		if price_type_amend == 'per_kg':
			prod_rec = self.pool.get('product.product').browse(cr,uid,product_id_amend)
			if uom_conversation_factor_amend == 'two_dimension':
				if prod_rec.po_uom_in_kgs > 0:
					quantity = product_qty_amend * prod_rec.po_uom_in_kgs * length_amend * breadth_amend
			elif uom_conversation_factor_amend == 'one_dimension':
				if prod_rec.po_uom_in_kgs > 0:
					quantity = product_qty_amend * prod_rec.po_uom_in_kgs
				else:
					quantity = product_qty_amend
			else:
				quantity = product_qty_amend
		else:
			quantity = product_qty_amend
		value = {'quantity': quantity}
		return {'value': value}
		
	def onchange_moc(self, cr, uid, ids, moc_id_temp_amend):
		value = {'moc_id_amend':''}
		if moc_id_temp_amend:
			rate_rec = self.pool.get('ch.brandmoc.rate.details').browse(cr,uid,moc_id_temp_amend)
			value = {'moc_id_amend': rate_rec.moc_id.id}
		return {'value': value}
		
	def onchange_brand_moc(self, cr, uid, ids, product_id_amend):
		value = {'brand_id_amend':'','moc_id_amend':'','moc_id_temp_amend':''}
		return {'value': value}
		
	def pol_cancel(self, cr, uid, ids, context=None):
		line_rec = self.browse(cr,uid,ids)
		if line_rec[0].amendment_id.state == 'draft':			
			if line_rec[0].note_amend == '' or line_rec[0].note_amend == False:
				raise osv.except_osv(_('Remarks Required !! '),
					_('Without remarks you can not cancel a PO Item...'))				
			if line_rec[0].pending_qty == 0.0:
				raise osv.except_osv(_('All Quanties are Received !! '),
					_('You can cancel a PO line before receiving product'))					
			else:				
				self.write(cr,uid,ids,{'line_state':'cancel', 
										'cancel_flag': True,
										'cancel_qty' : line_rec[0].pending_qty,
										})
		else:
			raise osv.except_osv(_('Amendment Confirmed Already !! '),
				_('System allow to cancel a line Item in draft state only !!!...'))
						
		return True
		
	def pol_draft(self,cr,uid,ids,context=None):
		self.write(cr,uid,ids,{'line_state':'draft', 'cancel_flag': False})
		return True
		
	"""	
	def unlink(self,cr,uid,ids,context=None):
		print "Amend =======>unlink called"
		if context is None:
			context = {}
			Allows to delete sales order lines in draft,cancel states
		for rec in self.browse(cr, uid, ids, context=context):
			if rec.line_state in ['draft', 'confirm']:
				raise osv.except_osv(_('Invalid Action!'), _('Cannot delete a sales order line which is in state \'%s\'.') %(rec.line_state,))
		return super(kg_purchase_amendment_line, self).unlink(cr, uid, ids, context=context)	
		"""
	
kg_purchase_amendment_line()
