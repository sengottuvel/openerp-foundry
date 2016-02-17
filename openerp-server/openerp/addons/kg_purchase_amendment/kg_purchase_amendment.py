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

class kg_purchase_amendment(osv.osv):	
	
	_name = "kg.purchase.amendment"	
	_order = "date desc"

	
	def _amount_line_tax(self, cr, uid, line, context=None):
		val = 0.0
		new_amt_to_per = line.kg_discount_amend or 0.0 / line.product_qty_amend
		amt_to_per = (line.kg_discount_amend or 0.0 / (line.product_qty_amend * line.price_unit_amend or 1.0 )) * 100
		kg_discount_per = line.kg_discount_per_amend
		tot_discount_per = amt_to_per + kg_discount_per
		for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id_amend,
			line.price_unit_amend * (1-(tot_discount_per or 0.0)/100.0), line.product_qty_amend, line.product_id,
			line.amendment_id.partner_id)['taxes']:
			#print "ccccccccccccccccccccccccccccccc===========>>>", c
			val += c.get('amount', 0.0)
			#print "valvalvalvalvalvalvalvalvalvalvalvalvalval =============>>", val
		return val
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		for order in self.browse(cr, uid, ids, context=context):
			print "order=========================>>>>", order
			res[order.id] = {
				'amount_untaxed': 0.0,
				'amount_tax': 0.0,
				'amount_total': 0.0,
				'discount' : 0.0,
				'other_charge': 0.0,
			}
			val = val1 = val3 = 0.0
			cur = order.pricelist_id.currency_id
			for line in order.amendment_line:
				tot_discount = line.kg_discount_amend + line.kg_discount_per_value_amend
				val1 += line.price_subtotal
				val += self._amount_line_tax(cr, uid, line, context=context)
				val3 += tot_discount
			po_charges=order.value1_amend + order.value2_amend
			print "po_charges :::", po_charges , "val ::::", val, "val1::::", val1, "val3:::::", val3
			#res[order.id]['other_charge']=cur_obj.round(cr, uid, cur, po_charges)
			res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
			res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
			res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] + res[order.id]['other_charge']
			res[order.id]['discount']=cur_obj.round(cr, uid, cur, val3)
			self.write(cr, uid,order.id, {'other_charge' : po_charges})
		print "res ^^^^^^^^^^^^^,", "amount_total====", res[order.id]['amount_total'], "^^^^^^^^^^^^^^", res
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
		'po_date_amend':fields.date('Amend PO Date',states={'draft':[('readonly',False)]}),
		'partner_id':fields.many2one('res.partner', 'Supplier', readonly=True),
		'pricelist_id':fields.many2one('product.pricelist', 'Pricelist', required=True, states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)]}),
		'currency_id': fields.related('pricelist_id', 'currency_id', type="many2one", relation="res.currency", string="Currency",readonly=True, required=True),
		'po_expenses_type1': fields.selection([('freight','Freight Charges'),('others','Others')], 'Expenses Type1',readonly=True),
		'po_expenses_type2': fields.selection([('freight','Freight Charges'),('others','Others')], 'Expenses Type2',readonly=True),
		'value1':fields.float('Value1', readonly=True),
		'value2':fields.float('Value2', readonly=True),
		'bill_type': fields.selection([('cash','Cash Bill'),('credit','Credit Bill')], 'Bill Type', readonly=True),
		'price':fields.selection([('inclusive','Inclusive of all Taxes and Duties')], 'Price', readonly=True),
		'payment_mode': fields.many2one('kg.payment.master',
			'Mode of Payment', readonly=True),
		'delivery_type':fields.many2one('kg.deliverytype.master', 'Delivery Schedule', readonly=True),
		'delivery_mode': fields.many2one('kg.delivery.master', 'Delivery Type', readonly=True),
		'term_warranty':fields.char('Warranty', readonly=True),
		'term_freight':fields.selection([('Inclusive','Inclusive'),('Extra','Extra'),('To Pay','To Pay'),('Paid','Paid'),
						  ('Extra at our Cost','Extra at our Cost')], 'Freight',readonly=True),
		'quot_ref_no':fields.char('Your Quot. Ref.'),
		'note': fields.text('Remarks'),
		'cancel_note': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'amend_flag':fields.boolean('Amend Flag'),
		'state':fields.selection([('draft', 'Draft'),('amend', 'Processing'),('confirm', 'Confirmed'),('approved', 'Approved'),('cancel','Cancel')], 'Status'),
		'amendment_line':fields.one2many('kg.purchase.amendment.line', 'amendment_id', 'Amendment Line'),
		
		'add_text': fields.text('Address',readonly=True),
		'add_text_amend': fields.text('Amend Address'),
		
		'delivery_address':fields.text('Delivery Address'),
				
		'other_charge': fields.float('Other Charges(+)',readonly=True),
		'discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Discount(-)',
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
		'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total',
			store={
				'kg.purchase.amendment': (lambda self, cr, uid, ids, c={}: ids, ['amendment_line'], 10),
				'kg.purchase.amendment.line': (_get_order, ['price_unit_amend', 'tax_id', 'kg_discount_amend', 'product_qty_amend'], 10),
				
			}, multi="sums",help="The total amount"),
		'grn_flag': fields.boolean('GRN'),
		
			
		# Amendment Fields:
		'partner_id_amend':fields.many2one('res.partner', 'Amend Supplier'),
		'delivery_address_amend':fields.text('Amend Delivery Address'),
		'bill_type_amend': fields.selection([('cash','Cash Bill'),('credit','Credit Bill')], 'Amend Bill Type', 
			states={'confirm':[('readonly', True)]}),
		'payment_mode_amend': fields.many2one('kg.payment.master',
			'Amend Mode of Payment', states={'confirm':[('readonly', True)]}),
		'delivery_type_amend':fields.many2one('kg.deliverytype.master', 'Amend Delivery Schedule',
					states={'confirm':[('readonly', True)]}),
		'delivery_mode_amend': fields.many2one('kg.delivery.master', 'Amend Delivery Type',
			states={'confirm':[('readonly', True)]}),
		'po_expenses_type1_amend': fields.selection([('freight','Freight Charges'),('others','Others')], 'Amend Expenses Type1',
			states={'confirm':[('readonly', True)]}),
		'po_expenses_type2_amend': fields.selection([('freight','Freight Charges'),('others','Others')], 'Amend Expenses Type2',
			states={'confirm':[('readonly', True)]}),
		'value1_amend':fields.float('Amend Value1', states={'confirm':[('readonly', True)]}),
		'value2_amend':fields.float('Amend Value2', states={'confirm':[('readonly', True)]}),
		'remark': fields.text('Remarks', states={'confirm':[('readonly', True)]}),
		'terms': fields.text('Terms & Conditions', states={'confirm':[('readonly', True)]}),
		'term_warranty_amend':fields.char('Amend Warranty', states={'confirm':[('readonly', True)]}),
		'term_freight_amend':fields.selection([('Inclusive','Inclusive'),('Extra','Extra'),('To Pay','To Pay'),('Paid','Paid'),
						  ('Extra at our Cost','Extra at our Cost')], 'Amend Freight', states={'confirm':[('readonly', True)]}),
		'quot_ref_no_amend':fields.char('Amend Your Quot. Ref.', states={'confirm':[('readonly', True)]}),
		'price_amend':fields.selection([('inclusive','Inclusive of all Taxes and Duties')], 'Amend Price', states={'confirm':[('readonly', True)]}),
		'created_by':fields.many2one('res.users','Created By',readonly=True),
		'creation_date':fields.datetime('Creation Date',readonly=True),
		
		'confirmed_by':fields.many2one('res.users','Confirmed By',readonly=True),
		'confirmed_date':fields.datetime('Confirmed Date',readonly=True),
		
		'approved_by':fields.many2one('res.users','Approved By',readonly=True),
		'approved_date':fields.datetime('Approved Date',readonly=True),
		
		'dep_project_name':fields.char('Dept/Project Name',readonly=True),
		'dep_project_name_amend':fields.char('Amend Dept/Project Name', states={'confirm':[('readonly', True)]}),
		
		'dep_project':fields.many2one('kg.project.master','Dept/Project Name',readonly=True),
		'dep_project_amend':fields.many2one('kg.project.master','Amend Dept/Project Name', states={'confirm':[('readonly', True)]}),
		
			
		
		
	}
	
	_defaults = {
	
	'date': fields.date.context_today,
	'state': 'amend',
	'active' : True,
	'name' : '/',
	'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
	
	'created_by': lambda obj, cr, uid, context: uid,
	'pricelist_id': 2,
	
	}
	
	
			
	
	
	def onchange_poid(self, cr, uid, ids,po_id, pricelist_id):
		print "onchange_poid called***************************", ids
		po_obj = self.pool.get('purchase.order')
		value = {'pricelist_id': ''}
		if po_id:
			po_record = po_obj.browse(cr,uid,po_id)
			price_id = po_record.pricelist_id.id
			print "price_id==========>>", price_id
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
			if t['state'] in ('draft'):
				unlink_ids.append(t['id'])
			else:
				raise osv.except_osv(_('Invalid action !'), _('System not allow to delete a UN-DRAFT state Purchase Amendment!!'))
		amend_lines_to_del = self.pool.get('kg.purchase.amendment.line').search(cr, uid, [('amendment_id','in',unlink_ids)])
		self.pool.get('kg.purchase.amendment.line').unlink(cr, uid, amend_lines_to_del)
		osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		return True
	
	def _prepare_amend_line(self, cr, uid, po_order, order_line, amend_id, context=None):
		print "po_order ::::::::>>>>>>>>>>>>>>>>>>>>", po_order, "===ID ====", po_order.id
		print "order_line ::::::::::::<<<<<<<<<<<<<<<", order_line

		return {
		
			'order_id':po_order.id,
			'product_id': order_line.product_id.id,
			'product_uom': order_line.product_uom.id,
			'brand_id':order_line.brand_id.id,
			'brand_id_amend':order_line.brand_id.id,
			'product_qty': order_line.product_qty,
			'product_qty_amend' : order_line.product_qty,
			'pending_qty' : order_line.pending_qty,
			'pending_qty_amend' : order_line.pending_qty,
			'received_qty' : order_line.product_qty - order_line.pending_qty,
			'price_unit' : order_line.price_unit or 0.0,
			'price_unit_amend' : order_line.price_unit or 0.0,
			'kg_discount' : order_line.kg_discount,
			'kg_discount_amend' : order_line.kg_discount,
			'kg_discount_per' : order_line.kg_discount_per,
			'kg_discount_per_amend' : order_line.kg_discount_per,
			'kg_discount_per_value' : order_line.kg_discount_per_value,
			'kg_discount_per_value_amend' : order_line.kg_discount_per_value,
			'kg_disc_amt_per':order_line.kg_disc_amt_per,
			'kg_disc_amt_per_amend':order_line.kg_disc_amt_per,
			'note' : order_line.name or '',
			'note_amend' : order_line.name or '',			
			'amendment_id': amend_id,
			'po_line_id': order_line.id,
			'line_bill':order_line.line_bill,
			
		}
	
	def make_amend(self,cr,uid,ids,amendment_id=False,context={}):
		
		po_id = False
		obj = self.browse(cr,uid,ids[0])
		print "Amend Obj ::::::::::",obj
		po_obj=self.pool.get('purchase.order')
		amend_obj=self.pool.get('kg.purchase.amendment')
		amend_po_id = amend_obj.browse(cr,uid,obj.po_id.id)
		print "amend_po_id:::::::::", amend_po_id
		po_order = obj.po_id
		print "po_order :::::::::", po_order
		
		total_amends=amend_obj.search(cr,uid,[('po_id','=',obj.po_id.id)])
		print "total_amends ===================>>>", total_amends
		
		draft_amends=amend_obj.search(cr,uid,[('po_id','=',obj.po_id.id),('state','not in',('approved','reject'))])
		if len(draft_amends) > 1:
			raise osv.except_osv(
				_('Amendment has been created for this PO!'),
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
						'delivery_type' : po_order.delivery_type.id,
						'delivery_type_amend' : po_order.delivery_type.id,
						'delivery_mode' : po_order.delivery_mode.id,
						'delivery_mode_amend' : po_order.delivery_mode.id,
						'po_expenses_type1' : po_order.po_expenses_type1,
						'po_expenses_type1_amend' : po_order.po_expenses_type1,
						'po_expenses_type2' : po_order.po_expenses_type2,
						'po_expenses_type2_amend' : po_order.po_expenses_type2,
						'dep_project' : po_order.dep_project.id,
						'dep_project_amend' : po_order.dep_project.id,
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
						'amendment_line' : [],
							
						'amount_untaxed':po_order.amount_untaxed,
						'amount_tax':po_order.amount_tax,
						'amount_total':po_order.amount_total,
						'discount':po_order.discount,
			
						}
			print "vals ..........",vals
			self.pool.get('kg.purchase.amendment').write(cr,uid,ids,vals)
				
			amend_id = obj.id
			todo_lines = []
			amend_line_obj = self.pool.get('kg.purchase.amendment.line')
			wf_service = netsvc.LocalService("workflow")
			order_lines=po_order.order_line
			self.write(cr,uid,ids[0],{'state':'draft',
								  
								  
								  
								   })
			for order_line in order_lines:
				if order_line.line_state != 'cancel' and order_line.line_bill == False:
					amend_line = amend_line_obj.create(cr, uid, self._prepare_amend_line(cr, uid, po_order, order_line, amend_id,
									context=context))
					print "amend_line ==========================>>", amend_line
					cr.execute(""" select tax_id from purchase_order_taxe where ord_id = %s """  %(str(order_line.id)))
					data = cr.dictfetchall()
					val = [d['tax_id'] for d in data if 'tax_id' in d]
					print "val::::::::::::::::", val
					for i in range(len(val)):
						print "IIIIIIIIIIIIIIIIIIIII", val[i]
						cr.execute(""" INSERT INTO purchase_order_tax (amend_line_id,tax_id) VALUES(%s,%s) """ %(amend_line,val[i]))
						cr.execute(""" INSERT INTO amendment_order_tax (amend_line_id,tax_id) VALUES(%s,%s) """ %(amend_line,val[i]))
					todo_lines.append(amend_line_obj)
				else:
					print "NO Qty or Cancel"
				

			wf_service.trg_validate(uid, 'kg.purchase.amendment', amend_id, 'button_confirm', cr)
			return [amend_id]
			cr.close()
		else:
			raise osv.except_osv(
				_('Amendment Created Already!'),
				_('System not allow to create Amendment again !!')) 
				
	def confirm_amend(self, cr, uid, ids,context=None):
		grn_entry = self.browse(cr, uid, ids[0])
		amend_obj = self.browse(cr,uid,ids[0])
		po_obj = self.pool.get('purchase.order')
		product_obj = self.pool.get('product.product')
		po_line_obj = self.pool.get('purchase.order.line')
		amend_line_obj = self.pool.get('kg.purchase.amendment.line')
		pi_line_obj = self.pool.get('purchase.requisition.line')
		stock_move_obj = self.pool.get('stock.move')
		for amend_line in amend_obj.amendment_line:
			print "amend_line================>>", amend_line
			po_line_id = amend_line.po_line_id.id
			po_rec = amend_obj.po_id
			pol_record = amend_line.po_line_id
			diff_qty = amend_line.product_qty - amend_line.product_qty_amend
			print "diff_qty :::::::::::::::", diff_qty
			pending_diff_qty = amend_line.product_qty - amend_line.pending_qty
			print "pending_diff_qty :::::::::::", pending_diff_qty
			
			if amend_line.product_qty < amend_line.product_qty_amend:
				pi_line_record = pi_line_obj.browse(cr, uid,pol_record.pi_line_id.id)
				if pi_line_record.pending_qty <= 0:
					if not amend_line.kg_poindent_lines:
						
						raise osv.except_osv(
						_('If you want to increase PO Qty'),
						_('Select PI for this Product')) 
						
					else:
						for ele in amend_line.kg_poindent_lines:
							
							
							if ele.product_id.id == amend_line.product_id.id:
								if (amend_line.product_qty_amend - amend_line.product_qty) <= ele.pending_qty:
									pi_line_obj.write(cr,uid,pi_line_record.id,{'pending_qty': ele.pending_qty}) 
									amend_line_obj.write(cr,uid,amend_line.id,{'pi_line_id':ele.id})
									line_pending = ele.pending_qty - (amend_line.product_qty_amend - amend_line.product_qty)
									pi_line_obj.write(cr,uid,ele.id,{'pending_qty': line_pending}) 
								
									
								else:
									raise osv.except_osv(
										_('Amendment Qty is greater than indent qty'),
										_('')) 	
					
				else:
					pass
						
					
			else:
				grn_id = self.pool.get('po.grn.line').search(cr, uid, [('po_line_id','=',amend_line.po_line_id.id)])
				print "-------------------------------------------------------------grn_id---->",grn_id
				print "-------------------------------------------------------------grn_id---->",amend_line.po_line_id.id
				
				if grn_id:
					grn_bro = self.pool.get('po.grn.line').browse(cr, uid, grn_id[0])
					if grn_bro.po_grn_qty <= amend_line.product_qty_amend:
						pass
						
						
					else:
						
						raise osv.except_osv(
								_('You can not decrease PO Qty'),
								_('Because GRN is already created'))
								
				else:
					pass
					
					
			if amend_line.product_qty != amend_line.product_qty_amend:
				if amend_line.pending_qty == 0 and not amend_line.kg_poindent_lines:
					raise osv.except_osv(
					_('All Qty has received for this PO !'),
					_('You can not increase PO Qty for product %s')%(amend_line.product_id.name))
			
			else:
				pass		
			
		
		self.write(cr,uid,ids[0],{'state':'confirm',
								  
								  'confirmed_by':uid,
								  'confirmed_date':today,
								  
								   })
						
		
		return True
	
	def cancel_amend(self, cr, uid, ids,context=None):
		
		amend_obj = self.browse(cr,uid,ids[0])
		if not amend_obj.cancel_note:
			raise osv.except_osv(
					_('Please give reason for this cancellation'),
					_(''))
		else:	
	
		
			self.write(cr,uid,ids[0],{'state':'cancel'})
						
		
		return True
		
		
	def approve_amend(self,cr,uid,ids,context={}):
		
			
		amend_obj = self.browse(cr,uid,ids[0])
		po_obj = self.pool.get('purchase.order')
		product_obj = self.pool.get('product.product')
		po_line_obj = self.pool.get('purchase.order.line')
		amend_line_obj = self.pool.get('kg.purchase.amendment.line')
		pi_line_obj = self.pool.get('purchase.requisition.line')
		stock_move_obj = self.pool.get('stock.move')
		
		po_id = False 
		#if amend_obj.confirmed_by.id == uid:
		#	raise osv.except_osv(
		#			_('Warning'),
		#			_('Approve cannot be done by Confirmed user'))
					
		if amend_obj.amendment_line ==[]:
			raise osv.except_osv(
			_('Empty Purchase Amendment!'),
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
				
			if amend_obj.dep_project.id != amend_obj.dep_project_amend.id:
				po_obj.write(cr,uid,po_id,{'dep_project': amend_obj.dep_project_amend.id})	
				
			if amend_obj.payment_mode.id != amend_obj.payment_mode_amend.id:
				po_obj.write(cr,uid,po_id,{'payment_mode': amend_obj.payment_mode_amend.id})
				
			if amend_obj.delivery_type.id != amend_obj.delivery_type_amend.id:
				po_obj.write(cr,uid,po_id,{'delivery_type': amend_obj.delivery_type_amend.id})
				
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
			print "amend_line================>>", amend_line
			po_line_id = amend_line.po_line_id.id
			po_rec = amend_obj.po_id
			pol_record = amend_line.po_line_id
			diff_qty = amend_line.product_qty - amend_line.product_qty_amend
			print "diff_qty :::::::::::::::", diff_qty
			pending_diff_qty = amend_line.product_qty - amend_line.pending_qty
			print "pending_diff_qty :::::::::::", pending_diff_qty
			
			if amend_line.product_qty < amend_line.product_qty_amend:
				pi_line_record = pi_line_obj.browse(cr, uid,pol_record.pi_line_id.id)
				if pi_line_record.pending_qty <= 0:
					if not amend_line.kg_poindent_lines:
						
						raise osv.except_osv(
						_('If you want to increase PO Qty'),
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
				print "-------------------------------------------------------------grn_id---->",grn_id
				print "-------------------------------------------------------------grn_id---->",amend_line.po_line_id.id
				
				if grn_id:
					grn_bro = self.pool.get('po.grn.line').browse(cr, uid, grn_id[0])
					if grn_bro.po_grn_qty <= amend_line.product_qty_amend:
						pi_line_record = pi_line_obj.browse(cr, uid,pol_record.pi_line_id.id)
						pi_pending_qty = pi_line_record.pending_qty
						re_qty = amend_line.product_qty - amend_line.product_qty_amend
						pi_pending_qty += re_qty
						pi_line_obj.write(cr,uid,pol_record.pi_line_id.id,{'pending_qty' : pi_pending_qty})
						
					else:
						
						raise osv.except_osv(
								_('You can not decrease PO Qty'),
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
					print "pi_line_record ======================>>", pi_line_record
					print "pi_pending_qty ===================>>", pi_pending_qty
					print "**************************************"
					pi_product_qty += pol_record.product_qty
					pi_pending_qty += pol_record.pending_qty
					print "pi_pending_qty ===================>>", pi_pending_qty
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
				
				if amend_line.pending_qty == 0 and not amend_line.kg_poindent_lines:
					raise osv.except_osv(
					_('All Qty has received for this PO !'),
					_('You can not increase PO Qty for product %s')%(amend_line.product_id.name))
					
				disc_value = (amend_line.product_qty_amend * amend_line.price_unit_amend) * amend_line.kg_discount_per_amend / 100
				print "kg_discount_per_value :::::::::::::::", disc_value
				po_line_obj.write(cr,uid,po_line_id,{
						'product_qty': amend_line.product_qty_amend,
						'pending_qty': amend_line.pending_qty_amend,
						'kg_discount_per_value' : disc_value,
							})
					
			if amend_line.price_unit != amend_line.price_unit_amend:
				po_line_obj.write(cr,uid,po_line_id,{
					'price_unit': amend_line.price_unit_amend})
					
			if amend_line.brand_id.id != amend_line.brand_id_amend.id:
				po_line_obj.write(cr,uid,po_line_id,{
					'brand_id': amend_line.brand_id_amend.id})	

				
			if amend_line.kg_discount != amend_line.kg_discount_amend:
				
				print "kg_disc_amt_per_amend...................", amend_line.kg_disc_amt_per_amend
				print "kg_discount_amend...........", amend_line.kg_discount_amend
				
				po_line_obj.write(cr,uid,po_line_id,{'kg_discount': amend_line.kg_discount_amend})
				
				
			if amend_line.kg_discount_per != amend_line.kg_discount_per_amend:
				print "kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk",amend_line.kg_disc_amt_per_amend
				po_line_obj.write(cr,uid,po_line_id,{'kg_discount_per': amend_line.kg_discount_per_amend}) 
				
			if amend_line.kg_disc_amt_per != amend_line.kg_disc_amt_per_amend:
				print "kg_disc&&&&&&&&&",amend_line.kg_disc_amt_per
				print "kg_disc********",amend_line.kg_disc_amt_per_amend
				po_line_obj.write(cr,uid,po_line_id,{'kg_disc_amt_per': amend_line.kg_disc_amt_per_amend})
				
			if amend_line.kg_discount_per_value != amend_line.kg_discount_per_value_amend:
				po_line_obj.write(cr,uid,po_line_id,{'kg_discount_per_value': amend_line.kg_discount_per_value_amend})
			
			if amend_line.note != amend_line.note_amend:
				po_line_obj.write(cr,uid,po_line_id,{'name': amend_line.note_amend})
			
			print "amend_line.id::::::::::", amend_line.taxes_id
			print "amend_line.id:::taxes_id_amend:::::::", amend_line.taxes_id_amend
			
			cr.execute(""" select tax_id from amendment_order_tax where amend_line_id = %s """ %(amend_line.id))
			data = cr.dictfetchall()
			val = [d['tax_id'] for d in data if 'tax_id' in d]
			print "val::::::::::::::::", val
					
			cr.execute(""" delete from purchase_order_taxe where ord_id=%s """ %(po_line_id))
			
			for i in range(len(val)):
				print "IIIIIIIIIIIIIIIIIIIII", val[i]
				cr.execute(""" INSERT INTO purchase_order_taxe (ord_id,tax_id) VALUES(%s,%s) """ %(po_line_id,val[i]))
					
				
			else:
				print "NO PO Line Changs"
			amend_line.write({'line_state': 'done'})
			
			
		print "Tax Calculation Methods are Going to Call"
		
		#po_line_obj._amount_line(cr,uid,[po_id],prop=None,arg=None,context=None)
		po_obj._amount_line_tax(cr,uid,pol_record,context=None)
		po_obj._amount_all(cr,uid,[po_id],field_name=None,arg=False,context=None)
		self.write(cr,uid,ids,{'state' : 'approved' ,'approved_by':uid,
								  'approved_date':today,})
		
		return True
		cr.close()
		
	def onchange_partner_id(self, cr, uid, ids, partner_id_amend,add_text_amend):
		logger.info('[KG OpenERP] Class: kg_purchase_order, Method: onchange_partner_id called...')
		partner = self.pool.get('res.partner')
		if not partner_id_amend:
			return {'value': {
				'add_text_amend': False,
				
				}}
		supplier_address = partner.address_get(cr, uid, [partner_id_amend], ['default'])
		supplier = partner.browse(cr, uid, partner_id_amend)
		tot_add = (supplier.street or '')+ ' ' + (supplier.street2 or '') + '\n'+(supplier.city.name or '')+ ',' +(supplier.state_id.name or '') + '-' +(supplier.zip or '') + '\nPh:' + (supplier.phone or '')+ '\n' +(supplier.mobile or '')		
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
		for line in self.browse(cr, uid, ids, context=context):
			amt_to_per = (line.kg_discount_amend / (line.product_qty_amend * line.price_unit_amend or 1.0 )) * 100
			kg_discount_per = line.kg_discount_per_amend
			tot_discount_per = amt_to_per + kg_discount_per
			price = line.price_unit_amend * (1 - (tot_discount_per or 0.0) / 100.0)
			taxes = tax_obj.compute_all(cr, uid, line.taxes_id_amend, price, line.product_qty, line.product_id, 
								line.amendment_id.partner_id)
			cur = line.amendment_id.pricelist_id.currency_id
			res[line.id] = cur_obj.round(cr, uid, cur, taxes['total_included'])
		return res
	
	_columns = {
	
	'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
	'order_id': fields.many2one('purchase.order', 'Order ID'),
	'amendment_id':fields.many2one('kg.purchase.amendment','Amendment', select=True, required=True, ondelete='cascade'),
	'pi_line_id':fields.many2one('purchase.requisition.line','PI Line', invisible=True),
	'product_id':fields.many2one('product.product', 'Product', required=True,readonly=True),
	'kg_discount': fields.float('Discount Amount', digits_compute= dp.get_precision('Discount')),
	'price_unit': fields.float('Unit Price', digits_compute= dp.get_precision('Product Price')),
	'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
	'pending_qty': fields.float('Pending Qty'),
	'po_qty':fields.float('PI Qty'),
	'received_qty':fields.float('Received Qty'),
	'cancel_qty':fields.float('Cancel Qty'),
	'product_uom': fields.many2one('product.uom', 'Product Unit of Measure',required=True,readonly=True),
	'note': fields.text('Remarks'),
	'kg_discount_per': fields.float('Discount (%)', digits_compute= dp.get_precision('Discount')),
	'kg_discount_per_value': fields.float('Discount(%)Value', digits_compute= dp.get_precision('Discount')),
	'kg_disc_amt_per': fields.float('Discount(%)', digits_compute= dp.get_precision('Discount')),
	'po_line_id':fields.many2one('purchase.order.line', 'PO Line'),
	'taxes_id': fields.many2many('account.tax', 'purchase_order_tax', 'amend_line_id', 'tax_id','Taxes',readonly=True),
	'line_state': fields.selection([('draft', 'Draft'),('cancel', 'Cancel'),('done', 'Done')], 'Status'),
	'line_bill': fields.boolean('PO Bill'),
	# Amendment Fields:
	'kg_discount_amend': fields.float('Amend Discount Amount', digits_compute= dp.get_precision('Discount')),
	'price_unit_amend': fields.float('Amend Price', digits_compute= dp.get_precision('Product Price')),
	'product_qty_amend': fields.float('Amend Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
	'pending_qty_amend': fields.float('Amend Pending Qty',line_state={'cancel':[('readonly', True)]}),
	'po_qty_amend':fields.float('Amend PI Qty'),
	'kg_discount_per_amend': fields.float('Amend Discount (%)', digits_compute= dp.get_precision('Discount')),
	'kg_discount_per_value_amend': fields.float('Amend Discount(%)Value', digits_compute= dp.get_precision('Discount')),
	'kg_disc_amt_per_amend': fields.float('Amend Discount(%)', digits_compute= dp.get_precision('Discount')),
	'note_amend': fields.text('Amend Remarks'),
	'taxes_id_amend': fields.many2many('account.tax', 'amendment_order_tax', 'amend_line_id', 'tax_id','Amend Taxes'),
	'cancel_flag':fields.boolean('Flag'),
	'brand_id':fields.many2one('kg.brand.master','Brand'),
	'brand_id_amend':fields.many2one('kg.brand.master','Amend Brand'),
	'qty_flag': fields.boolean('QTY'),
	'kg_poindent_lines':fields.many2many('purchase.requisition.line','kg_poindent_po_line' , 'po_order_id', 'piline_id','POIndent Lines',
			domain="[('pending_qty','>','0'), '&',('line_state','=','process'), '&',('draft_flag','=', False),'&',('product_id','=',product_id)]"),
		
	}
	
	_defaults = {
	
		'line_state': 'draft',
		'qty_flag' :True,
		}
		
	def onchange_price_unit(self,cr,uid,price_unit,price_unit_amend,
					kg_discount_per_amend,kg_discount_per_value_amend,product_qty_amend):
						
		if price_unit != price_unit_amend:
			disc_value = (product_qty_amend * price_unit_amend) * kg_discount_per_amend / 100.00
			return {'value': {'kg_discount_per_value_amend': disc_value}}
		else:
			print "NO changes"
			
	
	def onchange_discount_value_calc(self, cr, uid, ids, kg_discount_per_amend,product_qty_amend,price_unit_amend):
		print "Amend =======>onchange_discount_value_calc called"

		discount_value = (product_qty_amend * price_unit_amend) * kg_discount_per_amend / 100.00
		print "discount_value::::::::::::", discount_value
		return {'value': {'kg_discount_per_value_amend': discount_value}}
		
	def onchange_disc_amt(self,cr,uid,ids,kg_discount_amend,product_qty_amend,price_unit_amend,kg_disc_amt_per_amend):
		logger.info('[KG OpenERP] Class: kg_purchase_order_line, Method: onchange_disc_amt called...')
		print "kg_discount_amend..........", 
		kg_discount_amend = kg_discount_amend + 0.00
		amt_to_per = (kg_discount_amend / (product_qty_amend * price_unit_amend or 1.0 )) * 100.00
		print "amt_to_peramt_to_peramt_to_per%%%%%%%%%%%%%%%%%%%%%%%%%%%%%", amt_to_per
		return {'value': {'kg_disc_amt_per_amend': amt_to_per}}
		
	def onchange_qty(self, cr, uid, ids,product_qty,product_qty_amend,pending_qty,pending_qty_amend):
		print "Amend =======>onchange_qty called"
	
		value = {'pending_qty_amend': ''}
		
		if product_qty == pending_qty:
			value = {'pending_qty_amend': product_qty_amend }			
		else:
			if product_qty != product_qty_amend:
				po_pen_qty = product_qty - pending_qty
				amend_pen_qty = product_qty_amend - po_pen_qty
				value = {'pending_qty_amend': amend_pen_qty}
			else:
				value = {'pending_qty_amend': pending_qty}
		return {'value': value}
		
	def pol_cancel(self, cr, uid, ids, context=None):
		print "pol_cancel from KGGGGGGG<><><><><>"

		line_rec = self.browse(cr,uid,ids)
		if line_rec[0].amendment_id.state == 'draft':			
			print "line_rec-------------------", line_rec
			print "line_rec[0].note_amend----------", line_rec[0].note_amend
			if line_rec[0].note_amend == '' or line_rec[0].note_amend == False:
				raise osv.except_osv(
					_('Remarks Required !! '),
					_('Without remarks you can not cancel a PO Item...'))				
			if line_rec[0].pending_qty == 0.0:
				raise osv.except_osv(
					_('All Quanties are Received !! '),
					_('You can cancel a PO line before receiving product'))					
			else:				
				self.write(cr,uid,ids,{'line_state':'cancel', 
										'cancel_flag': True,
										'cancel_qty' : line_rec[0].pending_qty,
										})
		else:
			raise osv.except_osv(
					_('Amendment Confirmed Already !! '),
					_('System allow to cancel a line Item in draft state only !!!...'))
						
		return True
		
	def pol_draft(self,cr,uid,ids,context=None):
		print "Amend =======>pol_draft called"
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

