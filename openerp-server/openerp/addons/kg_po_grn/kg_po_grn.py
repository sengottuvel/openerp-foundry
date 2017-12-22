import math
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from itertools import groupby
import netsvc
import datetime
import urllib
import urllib2
import logging
from datetime import date
from datetime import datetime

UOM_CONVERSATION = [

	('one_dimension','One Dimension'),('two_dimension','Two Dimension')
]

class kg_po_grn(osv.osv):
	
	def _amount_line_tax(self, cr, uid, line, context=None):
		val = 0.0
		if line.price_type == 'per_kg':
			if line.product_id.uom_conversation_factor == 'two_dimension':
				if line.product_id.po_uom_in_kgs > 0:
					qty = line.po_grn_qty * line.product_id.po_uom_in_kgs * line.length * line.breadth
			elif line.product_id.uom_conversation_factor == 'one_dimension':
				if line.product_id.po_uom_in_kgs > 0:
					qty = line.po_grn_qty * line.product_id.po_uom_in_kgs
				else:
					qty = line.po_grn_qty
			else:
				qty = line.po_grn_qty
		else:
			qty = line.po_grn_qty
		
		if line.po_qty == 0.0:
			po_qty = 1.0
		else:
			po_qty = line.po_qty
		if line.po_grn_id.grn_type == 'from_po':
			dis_amt = (line.po_line_id.kg_discount / po_qty) * qty
			amt_to_per = dis_amt / ((po_qty * line.po_line_id.price_unit) / 100)
			kg_discount_per = line.po_line_id.kg_discount_per
			tot_discount_per = amt_to_per + kg_discount_per
			price = line.po_line_id.price_unit - (line.po_line_id.kg_discount / po_qty)
			tax_ids = line.po_line_id.taxes_id
			supplier_id = line.po_id.partner_id
		else:
			dis_amt = (line.kg_discount / po_qty) * qty
			amt_to_per = dis_amt / ((po_qty * line.price_unit) / 100)
			kg_discount_per = line.kg_discount_per
			tot_discount_per = amt_to_per + kg_discount_per
			price = line.price_unit - (line.kg_discount / po_qty)
			tax_ids = line.grn_tax_ids
			supplier_id = line.supplier_id
		
		for c in self.pool.get('account.tax').compute_all(cr, uid, tax_ids,
			price, qty, line.product_id,supplier_id)['taxes']:
			val += c.get('amount', 0.0)
		return val
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		other_charges_amt = 0
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'amount_untaxed': 0.0,
				'amount_tax': 0.0,
				'amount_total': 0.0,
				'discount' : 0.0,
				'other_charge': 0.0,
			}
			val = val1 = val3 = 0.0
			cur = order.supplier_id.property_product_pricelist_purchase.currency_id
			po_charges=order.value1 + order.value2	
			if order.expense_line_id:
				for item in order.expense_line_id:
					other_charges_amt += item.expense_amt
			else:
				other_charges_amt = 0
			for line in order.line_ids:
				if line.po_qty == 0:
					qty = 1.0
				else:
					qty = line.po_qty
				if line.po_grn_id.grn_type == 'from_po':
					per_to_amt = (line.po_grn_qty * line.po_line_id.price_unit) * line.po_line_id.kg_discount_per / 100.00
					tot_discount = ((line.po_line_id.kg_discount / qty) * line.po_grn_qty )+ per_to_amt
					#~ val1 += line.po_line_id.price_subtotal
					val1 += line.price_subtotal
					val += self._amount_line_tax(cr, uid, line, context=context)
					val3 += tot_discount
				else:
					per_to_amt = (line.po_grn_qty * line.price_unit) * line.kg_discount_per / 100.00
					tot_discount = ((line.kg_discount / qty) * line.po_grn_qty )+ per_to_amt
					val1 += line.price_subtotal
					val += self._amount_line_tax(cr, uid, line, context=context)
					val3 += tot_discount
			res[order.id]['other_charge'] = (round(other_charges_amt,0))
			res[order.id]['amount_tax'] = val
			res[order.id]['amount_untaxed'] = val1 - val + val3
			res[order.id]['discount'] = val3
			res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] - res[order.id]['discount'] + res[order.id]['amount_tax'] + res[order.id]['other_charge']
		
		return res
	
	def _get_order(self, cr, uid, ids, context=None):
		result = {}
		for line in self.pool.get('po.grn.line').browse(cr, uid, ids, context=context):
			result[line.po_grn_id.id] = True
		return result.keys()
	
	def button_dummy(self, cr, uid, ids, context=None):
		return True 
	
	_name = "kg.po.grn"
	_description = "PO GRN"
	_order = "grn_date desc,name desc"
	
	_columns = {
		
		## Basic Info
		
		'name': fields.char('GRN NO',readonly=True),
		'grn_date':fields.date('Date',required=True,readonly=True, states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'state': fields.selection([('item_load','Draft'),('draft', 'Draft'), ('confirmed', 'WFA'), ('done', 'Approved'), ('inv', 'Invoiced'), ('cancel', 'Cancelled'),('reject','Rejected')], 'Status',readonly=True),
		'can_remark':fields.text('Cancel Remarks'),
		'reject_remark':fields.text('Reject Remarks', readonly=True, states={'confirmed':[('readonly',False)]}),
		'remark':fields.text('Remarks'),
		'notes':fields.text('Notes'),
		'confirm_flag':fields.boolean('Confirm Flag'),
		'bill_flag':fields.boolean('Bill Flag'),
		'invoice_flag':fields.boolean('Invoice Flag'),
		'inv_flag': fields.boolean('Invoice Flag'),
		
		## Module Requirement Info
		
		'dc_no': fields.char('DC No.', required=True,readonly=True, states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'dc_date':fields.date('DC Date',required=True, readonly=True, states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'po_id':fields.many2one('purchase.order', 'PO NO',
					domain="[('state','=','approved'),'&',('order_line.pending_qty','>','0'),'&',('grn_flag','=',False),'&',('partner_id','=',supplier_id),'&',('order_line.line_state','!=','cancel')]"), 
		'po_ids':fields.many2many('purchase.order', 'multiple_po', 'grn_id', 'po_id', 'PO Nos',
					domain="[('state','=','approved'),('order_line.pending_qty','>','0'),('grn_flag','=',False),('partner_id','=',supplier_id),('order_line.line_state','!=','cancel'),('division','=',division)]",
					readonly=True, states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}), 
		'po_name': fields.char('PO NO',readonly=True),
		'order_no': fields.char('No',readonly=True),
		'order_date': fields.char('Date',readonly=True),
		'pos_date': fields.char('PO Date',readonly=True),
		'po_date':fields.date('PO Date',readonly=True),
		'supplier_id':fields.many2one('res.partner','Supplier',domain=[('supplier','=',True),('partner_state','=','approve')],required=True,readonly=True, states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'billing_status': fields.selection([
			('applicable', 'Applicable'),
			('not_applicable', 'Not Applicable')], 'Billing Status',required=True,readonly=True, states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'inward_type': fields.many2one('kg.inwardmaster','Inward Type',domain="[('state','=','approved')]",readonly=True,states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'department_id': fields.many2one('kg.depmaster','Department',domain="[('state','=','approved')]",readonly=True, states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'type': fields.selection([('in', 'IN'), ('out', 'OUT'), ('internal', 'Internal')], 'Type'),
		'po_so_remark':fields.text('PO/SO Remarks'),
		'other_charge': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Other Charges(+)',
			 multi="sums", help="The amount without tax", track_visibility='always'),	  
		'discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Discount(-)',
			store={
				'kg.po.grn': (lambda self, cr, uid, ids, c={}: ids, ['line_ids'], 10),
				'po.grn.line': (_get_order, ['price_unit', 'grn_tax_ids', 'kg_discount', 'po_grn_qty'], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
			store={
				'kg.po.grn': (lambda self, cr, uid, ids, c={}: ids, ['line_ids'], 10),
				'po.grn.line': (_get_order, ['price_unit', 'grn_tax_ids', 'kg_discount', 'po_grn_qty'], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
			store={
				'kg.po.grn': (lambda self, cr, uid, ids, c={}: ids, ['line_ids'], 10),
				'po.grn.line': (_get_order, ['price_unit', 'grn_tax_ids', 'kg_discount', 'po_grn_qty'], 10),
			}, multi="sums", help="The tax amount"),
		'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total',
			store=True,multi="sums",help="The total amount"),
		'pricelist_id':fields.many2one('product.pricelist', 'Pricelist'),
		'currency_id': fields.many2one('res.currency', 'Currency', readonly=True, states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'po_expenses_type1': fields.selection([('freight','Freight Charges'),('others','Others')], 'Expenses Type1', 
										readonly=True, states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'po_expenses_type2': fields.selection([('freight','Freight Charges'),('others','Others')], 'Expenses Type2', 
								 readonly=True, states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'value1':fields.float('Value1', readonly=True, states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'value2':fields.float('Value2',  readonly=True, states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'grn_type': fields.selection([('from_po','Purchase Order'),('from_so','Service Order'),('from_gp','Gate Pass')], 'GRN From',
										required=True, readonly=True, states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),	
		'grn_dc': fields.selection([('only_grn','Only grn')],'GRN Type',required=True,readonly=True,states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'so_id':fields.many2one('kg.service.order', 'SO NO',
					domain="[('state','=','approved'), '&', ('service_order_line.pending_qty','>','0'), '&', ('grn_flag','=',False), '&', ('partner_id','=',supplier_id),'&',('so_type','=','service')]"),
		'so_ids':fields.many2many('kg.service.order', 'multiple_so', 'grn_id', 'so_id', 'SO Nos',
					domain="[('state','=','approved'), '&', ('service_order_line.pending_qty','>','0'), '&', ('grn_flag','=',False), '&', ('partner_id','=',supplier_id),'&',('so_type','=','service')]",readonly=True, states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}), 
		'gp_line_ids':fields.many2many('kg.gate.pass.line', 'multiple_gp', 'grn_id', 'gp_line_id', 'Gate Pass No',
					domain="[('gate_id.state','=','done'), '&', ('grn_pending_qty','>','0'), '&', ('so_flag','=',False)]"), 
		'gp_ids':fields.many2many('kg.gate.pass', 'multiple_gate', 'grn_id', 'gp_id', 'Gate Pass No',
					domain="[('state','=','done'), '&', ('gate_line.grn_pending_qty','>','0'), '&', ('gate_line.so_flag','=',False),'&', ('partner_id','=',supplier_id)]",readonly=True, states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}), 
		'so_date':fields.date('SO Date',readonly=True),
		'so_name': fields.char('SO NO',readonly=True),
		'gp_date':fields.char('GP Date',readonly=True),
		'gp_name': fields.char('GP NO',readonly=True),
		'sos_date': fields.char('SO Date',readonly=True),
		'payment_type': fields.selection([('cash', 'Cash'), ('credit', 'Credit')], 'Payment Type', readonly=True, states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'sup_invoice_no':fields.char('Supplier Invoice No',size=200, readonly=False, states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
		'sup_invoice_date':fields.date('Supplier Invoice Date', readonly=False, states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
		'vehicle_details':fields.char('Vehicle Details', readonly=False, states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
		'insp_ref_no':fields.char('Insp.Ref.No.', readonly=False, states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
		'division': fields.selection([('ppd','PPD'),('ipd','IPD'),('foundry','Foundry')],'Location',readonly=False, states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
		'location_dest_id': fields.many2one('stock.location', 'Location'),
		'location_dest_code': fields.char('Location Code'),
		'product_id': fields.related('line_ids','product_id', type='many2one', relation='product.product', string='Product'),
		
		## Child Tables Declaration
		
		'line_ids': fields.one2many('po.grn.line','po_grn_id','Line Entry',readonly=True, states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'expense_line_id': fields.one2many('kg.po.grn.expense.track','expense_id','Expense Track',readonly=True, states={'item_load':[('readonly',False)],'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		
		# Entry Info
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company','Company',readonly=True),
		'created_by': fields.many2one('res.users','Created By',readonly=True),
		'creation_date': fields.datetime('Created Date',required=True,readonly=True),
		'confirmed_by': fields.many2one('res.users','Confirmed By',readonly=True),
		'confirmed_date': fields.datetime('Confirmed Date',readonly=True),
		'reject_date': fields.datetime('Rejected Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'approved_by': fields.many2one('res.users','Approved By',readonly=True),
		'approved_date': fields.datetime('Approved Date',readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date' : fields.datetime('Last Updated Date',readonly=True),
		'update_user_id' : fields.many2one('res.users','Last Updated By',readonly=True),
		
	}
	
	_defaults = {
		
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'grn_date': lambda * a: time.strftime('%Y-%m-%d'),
		'created_by': lambda obj, cr, uid, context: uid,
		'state': 'item_load',
		'type': 'in',
		'billing_status': 'applicable',
		'active': True,
		'confirm_flag': False,
		'inv_flag': False,
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.po.grn', context=c),
		'grn_dc': 'only_grn',
		
	}
	
	def onchange_created_by(self, cr, uid, ids, location_dest_code, context=None):
		value = {'location_dest_id':''}
		if location_dest_code:
			loc_ids = self.pool.get('stock.location').search(cr,uid,[('code','=',location_dest_code)])
			if loc_ids:
				loc_rec = self.pool.get('stock.location').browse(cr, uid, loc_ids[0])
				value = {'location_dest_id':loc_rec.id}
		return {'value': value}	
	
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_po_grn, self).write(cr, uid, ids, vals, context)
	
	# GRN LINE Creation #
	
	def update_potogrn(self,cr,uid,ids,picking_id=False,context={}):
		grn_entry_obj = self.browse(cr,uid,ids[0])
		if grn_entry_obj.state in ('draft','item_load'):
			### PO TO GRN ####
			po_id = False
			if grn_entry_obj.grn_type == 'from_po':
				cr.execute(""" select po_id from multiple_po where grn_id = %s """ %(grn_entry_obj.id))
				po_data = cr.dictfetchall()
				po_obj=self.pool.get('purchase.order')
				po_grn_obj=self.pool.get('kg.po.grn')
				po_grn_line_obj=self.pool.get('po.grn.line')
				pol_obj = self.pool.get('purchase.order.line')
				line_ids = map(lambda x:x.id,grn_entry_obj.line_ids)
				for ele in line_ids:
					line_rec = self.pool.get('po.grn.line').browse(cr,uid,ele)
					self.pool.get('purchase.order').write(cr,uid,line_rec.po_id.id,{'grn_flag':False})
				if line_ids:
					po_grn_line_obj.unlink(cr,uid,line_ids)
				
				value1 = 0
				value2 = 0
				po_list = []
				podate_list = []
				poremark_list = []
				for item in po_data:
					po_obj.write(cr,uid,item['po_id'],{'grn_flag':True})
					po_id = item['po_id']
					po_record = po_obj.browse(cr, uid, po_id)
					po_list.append(po_record.name)
					date_order = po_record.date_order
					date_order = datetime.strptime(date_order, '%Y-%m-%d')
					date_order = date_order.strftime('%d/%m/%Y')
					podate_list.append(date_order)
					po_name = ",".join(po_list)
					po_date = ",".join(podate_list)
					
					self.write(cr,uid,ids[0],{
								'order_no':po_name,
								'order_date':po_date,
								'po_name':po_name,
								'pos_name':po_date,
								})
					po_grn_id = grn_entry_obj.id
					order_lines=po_record.order_line
					for order_line in order_lines:
						if order_line.uom_conversation_factor == 'two_dimension':
							weight = order_line.product_qty * order_line.length * order_line.breadth * order_line.product_id.po_uom_in_kgs
						else:
							weight = 0
						if order_line.length <= 0:
							order_line_length = 1
						else:
							order_line_length = order_line.length
						if order_line.breadth <= 0:
							order_line_breadth = 1
						else:
							order_line_breadth = order_line.breadth
						if order_line.pending_qty > 0 and order_line.line_state != 'cancel':
							po_grn_line = po_grn_line_obj.create(cr, uid, {
								'name': order_line.product_id.name or '/',
								'product_id': order_line.product_id.id,
								'brand_id':order_line.brand_id.id,
								'moc_id':order_line.moc_id.id,
								'moc_id_temp':order_line.moc_id_temp.id,
								'po_grn_qty': order_line.pending_qty,
								'length': order_line_length,
								'breadth': order_line_breadth,
								'weight': weight,
								'po_qty':order_line.product_qty,
								'po_pending_qty':order_line.pending_qty,
								'uom_id': order_line.product_uom.id,
								'uom_category': order_line.product_uom.uom_category,
								'po_id': order_line.order_id.id,
								'location_id': po_record.partner_id.property_stock_supplier.id,
								'location_dest_id': grn_entry_obj.location_dest_id.id,
								'po_grn_id': po_grn_id,
								'state': 'confirmed',
								'po_line_id': order_line.id,
								'price_unit': order_line.price_unit,
								'pi_line_id':order_line.pi_line_id.id,
								'grn_tax_ids': [(6, 0, [x.id for x in order_line.taxes_id])],
								'kg_discount_per':order_line.kg_discount_per,
								'kg_discount': order_line.kg_discount,
								'price_subtotal': order_line.price_subtotal,
								'po_grn_date':grn_entry_obj.grn_date,
								'po_flag':'True',
								'billing_type':'cost',
								'order_no': order_line.order_id.name,
								'order_date': order_line.order_id.date_order,
								'price_type': order_line.price_type,
								'uom_conversation_factor': order_line.uom_conversation_factor,
								'inward_type': grn_entry_obj.inward_type.id,
								
							})
							if order_line.line_id:
								for ele in order_line.line_id:
									wo_obj = self.pool.get('ch.purchase.wo').search(cr,uid,[('id','=',ele.id)])
									if wo_obj:
										wo_rec = self.pool.get('ch.purchase.wo').browse(cr,uid,wo_obj[0])
										wo_id = self.pool.get('ch.po.grn.wo').create(cr,uid,{'header_id':po_grn_line,'qty':wo_rec.qty,'w_order_id':wo_rec.w_order_id.id,'wo_id':wo_rec.wo_id})
						else:
							pass
			
			if grn_entry_obj.grn_type == 'from_so':  
				
				### SO TO GRN ####
				so_id = False
				
				cr.execute(""" select so_id from multiple_so where grn_id = %s """ %(grn_entry_obj.id))
				so_data = cr.dictfetchall()
				so_obj=self.pool.get('kg.service.order')
				po_grn_obj=self.pool.get('kg.po.grn')
				po_grn_line_obj=self.pool.get('po.grn.line')
				sol_obj = self.pool.get('kg.service.order.line')
				line_ids = map(lambda x:x.id,grn_entry_obj.line_ids)
				po_grn_line_obj.unlink(cr,uid,line_ids)
				value1 = 0
				value2 = 0
				so_list = []
				sodate_list = []
				soremark_list = []
				for item in so_data:
					so_id = item['so_id']
					so_obj.write(cr,uid,item['so_id'],{'grn_flag':True})
					so_record = so_obj.browse(cr, uid, so_id)
					so_list.append(so_record.name)
					date_order = so_record.date
					date_order = datetime.strptime(date_order, '%Y-%m-%d')
					date_order = date_order.strftime('%d/%m/%Y')
					sodate_list.append(date_order)
					soremark_list.append('--')
					so_name = ",".join(so_list)
					so_date = ",".join(sodate_list)
					so_remark = ",".join(soremark_list)
					
					self.write(cr,uid,ids[0],{
								'order_no':so_name,
								'order_date':so_date,
								'so_name':so_name,
								'sos_date':so_date,
								'po_so_remark':so_remark,
								})
					po_grn_id = grn_entry_obj.id
					order_lines=so_record.service_order_line
					for order_line in order_lines:
						if order_line.pending_qty > 0 and order_line.state != 'cancel':
							po_grn_line_obj.create(cr, uid, {
								'name': order_line.product_id.name or '/',
								'product_id': order_line.product_id.id,
								'brand_id':order_line.brand_id.id,
								'po_grn_qty': order_line.pending_qty,
								'so_qty':order_line.product_qty,
								'so_pending_qty':order_line.pending_qty,
								'uom_id': order_line.product_uom.id,
								'location_id': so_record.partner_id.property_stock_supplier.id,
								'po_grn_id': po_grn_id,
								'state': 'confirmed',
								'so_line_id': order_line.id,
								'so_id': order_line.service_id.id,
								'price_unit': order_line.price_unit,
								'si_line_id':order_line.soindent_line_id.id,
								'grn_tax_ids': [(6, 0, [x.id for x in order_line.taxes_id])],
								'kg_discount_per':order_line.kg_discount_per,
								'kg_discount': order_line.kg_discount,
								'po_grn_date':grn_entry_obj.grn_date,
								'so_flag':'True',
								'billing_type':'cost',
								'ser_no':order_line.ser_no,
								'serial_no':order_line.serial_no.id,
								'order_no': order_line.service_id.name,
								'order_date': order_line.service_id.date,
							})
							
						else:
							print "NO Qty or Cancel"
			
			if grn_entry_obj.grn_type == 'from_gp':  
				
				cr.execute(""" select gp_id from multiple_gate where grn_id = %s """ %(grn_entry_obj.id))
				gp_data = cr.dictfetchall()
				gp_obj=self.pool.get('kg.gate.pass')
				po_grn_obj=self.pool.get('kg.po.grn')
				po_grn_line_obj=self.pool.get('po.grn.line')
				gpl_obj = self.pool.get('kg.gate.pass.line')
				line_ids = map(lambda x:x.id,grn_entry_obj.line_ids)
				po_grn_line_obj.unlink(cr,uid,line_ids)
				value1 = 0
				value2 = 0
				gp_list = []
				gpdate_list = []
				for item in gp_data:
					gp_id = item['gp_id']
					gp_record = gp_obj.browse(cr, uid, gp_id)
					gp_list.append(gp_record.name)
					date_order = gp_record.date
					date_order = datetime.strptime(date_order, '%Y-%m-%d')
					date_order = date_order.strftime('%d/%m/%Y')
					
					gpdate_list.append(date_order)
					gp_name = ",".join(gp_list)
					gp_date = ",".join(gpdate_list)
					self.write(cr,uid,ids[0],{
								'order_no':gp_name,
								'order_date':gp_date,
								'gp_name':gp_name,
								'gp_date':gp_date,
								})
					po_grn_id = grn_entry_obj.id
					order_lines=gp_record.gate_line
					for order_line in order_lines:
						if order_line.grn_pending_qty > 0:
							po_grn_line_obj.create(cr, uid, {
								'name': order_line.product_id.name or '/',
								'product_id': order_line.product_id.id,
								'brand_id':order_line.brand_id.id,
								'po_grn_qty': order_line.grn_pending_qty,
								'gp_qty':order_line.qty,
								'gp_pending_qty':order_line.grn_pending_qty,
								'uom_id': order_line.uom.id,
								'location_id': order_line.gate_id.partner_id.property_stock_supplier.id,
								'po_grn_id': po_grn_id,
								'state': 'confirmed',
								'gp_line_id': order_line.id,
								'price_unit': 0,
								'po_grn_date':grn_entry_obj.grn_date,
								'gp_flag':'True',
								'billing_type':'free',
								'ser_no':order_line.ser_no,
								'serial_no':order_line.serial_no.id,
								'order_no': order_line.gate_id.name,
								'order_date': order_line.gate_id.date,
							})
						else:
							pass
			self.write(cr,uid,ids[0],{'state':'draft'})
		return True
	
	def line_validations(self,cr,uid,ids,context=None):
		grn_entry = self.browse(cr,uid,ids[0])
		if grn_entry.dc_date and grn_entry.dc_date > grn_entry.grn_date:
			raise osv.except_osv(_('Warning !'),_('DC Date Should Be Less Than GRN Date !'))
		if not grn_entry.line_ids:
			raise osv.except_osv(_('Item Line Empty!'),_('You cannot process GRN without Item Line.'))
		for line in grn_entry.line_ids:
			if line.po_grn_qty <= 0:
				raise osv.except_osv(_('Item Qty can not Zero!'),
					_('You cannot process GRN with Item Line Qty Zero for Product %s.' %(line.product_id.name)))
			if line.inward_type.id == False:
				raise osv.except_osv(_('Warning!'),_('Select Inward Type for %s !!' %(line.product_id.name)))
			
			# Expiry date validation starts
			
			if line.product_id.flag_expiry_alert == True:
				if not line.po_exp_id:
					raise osv.except_osv(_('Warning !'),_('System should not be accept without Expiry Date for %s !!'))
			
			if line.po_exp_id:
				exp_grn_qty = line.po_grn_qty
				for item in line.po_exp_id:
					if not item.exp_date:
						raise osv.except_osv(_('Warning!'),_('%s Kindly mention expiry date for this S/N %s !!'%(line.product_id.name,item.batch_no)))
					else:
						if grn_entry.grn_date > item.exp_date:
							raise osv.except_osv(_('Warning !'),
								_('Change the product expiry date to greater than GRN date for Product %s !!' %(line.product_id.name)))
					
					batch_sql = """ 
							select exp.batch_no from kg_po_exp_batch exp
							left join po_grn_line line on(line.id=exp.po_grn_line_id)
							where exp.batch_no = '%s' and exp.po_grn_line_id = %s and line.product_id=%s and line.brand_id = %s and line.moc_id = %s """%(item.batch_no,line.id,line.product_id.id,line.brand_id.id,line.moc_id.id)
					cr.execute(batch_sql)		
					batch_data = cr.dictfetchall()
					if batch_data:
						if len(batch_data) > 1:
							raise osv.except_osv(_('Warning!'),_('%s S/N must be unique per Item') %(line.product_id.name))
						
				cr.execute(""" select sum(product_qty) from kg_po_exp_batch where po_grn_line_id = %s """ %(line.id))
				exp_data = cr.dictfetchone()
				exp_grn_qty = exp_data['sum']
				
				if exp_grn_qty > line.po_grn_qty:
					raise osv.except_osv(_('Warning !'),_('Qty specified in Batch Details should not greater than Received Qty for %s !!'%(line.product_id.name)))
				if exp_grn_qty < line.po_grn_qty:
					raise osv.except_osv(_('Warning !'),_('Qty specified in Batch Details should not less than Received Qty for %s !!'%(line.product_id.name)))
			
			# Expiry date validation ends
			
			if line.product_id.po_uom_coeff <= 0:
				raise osv.except_osv(_('Warning!'),_('PO UOM coeff should be grater than zero for Product (%s) check with Product Master !!'%(line.product_id.name)))
			if line.product_id.uom_conversation_factor == 'two_dimension' and line.uom_category == 'length' and line.length <= 0.00 and line.breadth <= 0.00:
				raise osv.except_osv(_('Warning!'),
					_('%s %s %s You cannot proceed without length and breadth')%(line.product_id.name,line.brand_id.name,line.moc_id.name))
			if line.length <= 0:
				line_length = 1
			else:
				line_length = line.length
			if line.breadth <= 0:
				line_breadth = 1
			else:
				line_breadth = line.breadth
			if grn_entry.grn_type == 'from_po':
				if line.po_line_id:
				# Tolerance validation starts
				
					if line.po_grn_qty > line.po_pending_qty:
						if line.product_id.tolerance_applicable == True:
							tolerance_qty = line.po_qty + ( (line.po_qty/100.00) * line.product_id.tolerance_plus or 1)
							curnt_qty = line.po_line_id.received_qty + line.po_grn_qty
							if curnt_qty > tolerance_qty:
								raise osv.except_osv(_('Warning!'),_('GRN Qty exceed PO Qty Tolerance of %s !!' %(line.product_id.name)))
				
				# Tolerance validation ends
			
			elif grn_entry.grn_type == 'from_so':
				if line.billing_type == 'cost':
					if line.po_grn_qty > line.so_pending_qty:
						raise osv.except_osv(_('Warning!'),_('GRN Qty should not be greater than SO Qty for %s !!' %(line.product_id.name)))
			elif grn_entry.grn_type == 'from_gp':
				if line.po_grn_qty > line.gp_pending_qty:
					raise osv.except_osv(_('Warning!'),_('GRN Qty should not be greater than GP Qty for %s !!' %(line.product_id.name)))
					
		if grn_entry.grn_type == 'from_po':
			for i in range(len(grn_entry.line_ids)):
				if grn_entry.line_ids[i].line_wo_id:
					total = sum(wo.qty for wo in grn_entry.line_ids[i].line_wo_id)
					if total <= grn_entry.line_ids[i].po_grn_qty:
						pass
					wo_sql = """ select count(wo_id) as wo_tot,wo_id as wo_name from ch_po_grn_wo where header_id = %s group by wo_id"""%(grn_entry.line_ids[i].id)
					cr.execute(wo_sql)
					wo_data = cr.dictfetchall()
					for wo in wo_data:
						if wo['wo_tot'] > 1:
							raise osv.except_osv(_('Warning!'),_('%s This WO No. repeated'%(wo['wo_name'])))
						else:
							pass
			line_po_ids = []
			po_ids = map(lambda x:x.id, grn_entry.po_ids)
			line_ids = set(map(lambda x:x.po_line_id.order_id.id, grn_entry.line_ids))
			for x in line_ids:
				line_po_ids.append(x)
			if sorted(po_ids) != sorted(line_po_ids):
				raise osv.except_osv(_('Warning !'),_('Mapped PO and Lines are mismatched !!'))
		return True
	
	# PO GRN Confirm #
	
	def entry_confirm(self, cr, uid, ids,context=None):
		grn_entry = self.browse(cr, uid, ids[0])
		if grn_entry.state == 'draft':
			po_obj=self.pool.get('purchase.order')
			so_obj=self.pool.get('kg.service.order')
			self.line_validations(cr,uid,ids)
			if not grn_entry.name or grn_entry.name == False:
				if grn_entry.location_dest_id.code == 'FOU_Main':
					seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.po.grn.fou')])
				elif grn_entry.location_dest_id.code == 'MS_Main':
					seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.po.grn.ms')])
				elif grn_entry.location_dest_id.code == 'GEN_Main':
					seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.po.grn.gen')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,grn_entry.creation_date))
				seq_name = cr.fetchone();
				self.write(cr,uid,ids[0],{'name':seq_name[0]})

			for line in grn_entry.line_ids:
				if line.billing_type == 'cost':
					if grn_entry.grn_type == 'from_po':
						po_obj.write(cr,uid,line.po_line_id.order_id.id,{'grn_flag': True})
				
				product_id = line.product_id.id
				product_rec = self.pool.get('product.product').browse(cr, uid, product_id)
				
				## Write a tax amount in line
				product_tax_amt = self._amount_line_tax(cr, uid, line, context=context)
				cr.execute("""update po_grn_line set product_tax_amt = %s, line_state='confirmed' where id = %s"""%(product_tax_amt,line.id))
			self.write(cr,uid,ids[0],{'state': 'confirmed',
									  'confirm_flag': 'False',
									  'confirmed_by': uid,
									  'confirmed_date': time.strftime('%Y-%m-%d %H:%M:%S'),
									   })
		return True
	
	# PO GRN Approve #
	
	def entry_approve(self, cr, uid, ids,context=None):
		grn_entry = self.browse(cr, uid, ids[0])
		if grn_entry.state == 'confirmed':
			self.line_validations(cr,uid,ids)
			user_id = self.pool.get('res.users').browse(cr, uid, uid)
			gate_obj = self.pool.get('kg.gate.pass')
			lot_obj = self.pool.get('stock.production.lot')
			stock_move_obj=self.pool.get('stock.move')
			dep_obj = self.pool.get('kg.depmaster')
			po_line_obj = self.pool.get('purchase.order.line')
			po_obj = self.pool.get('purchase.order')
			so_line_obj = self.pool.get('kg.service.order.line')
			so_obj = self.pool.get('kg.service.order')
			gp_line_obj = self.pool.get('kg.gate.pass.line')
			gp_obj = self.pool.get('kg.gate.pass')
			pi_obj = self.pool.get('kg.purchase.invoice')
			pi_po_grn_obj = self.pool.get('kg.pogrn.purchase.invoice.line')
			po_order = grn_entry.po_id
			line_tot = 0
			line_id_list = []
			grn_type = 'service'
			
			for line in grn_entry.line_ids:
				
				# Depreciation creation process start
				
				if line.product_id.is_depreciation == True:
					depre_obj = self.pool.get('kg.depreciation')
					depre_id = depre_obj.create(cr,uid,{'product_id': line.product_id.id,
														'grn_no': grn_entry.name,
														'grn_date': grn_entry.grn_date,
														'qty': line.po_grn_qty,
														'entry_mode': 'auto',
														'each_val_actual': line.po_line_id.price_unit,
														'tot_val_actual': line.po_line_id.price_unit * line.po_grn_qty,
														'each_val_crnt': line.po_line_id.price_unit,
														'tot_val_crnt': line.po_line_id.price_unit * line.po_grn_qty,
														})
				
				# Depreciation creation process end
				
				# This code is to update pending qty in Purchase Order
				if grn_entry.grn_type == 'from_po':
					if line.po_line_id.order_id:
						po_obj.write(cr,uid,line.po_line_id.order_id.id, {'grn_flag': False,'adv_flag':True})
					
						po_line_pending_qty = line.po_pending_qty - line.po_grn_qty
						if po_line_pending_qty < 0:
							po_line_pending_qty = 0
						else:
							po_line_pending_qty = po_line_pending_qty
						po_tot_rec_qty = line.po_line_id.received_qty + line.po_grn_qty
						
						po_line_obj.write(cr, uid, [line.po_line_id.id],
								{
								'pending_qty' : po_line_pending_qty,
								'received_qty' : po_tot_rec_qty,
								})
							
				# This code is to update pending qty in Service Order
				elif grn_entry.grn_type == 'from_so':
					if line.so_line_id:
						so_line_pending_qty = line.so_pending_qty - line.po_grn_qty
						if so_line_pending_qty < 0:
							so_line_pending_qty = 0
						else:
							so_line_pending_qty = so_line_pending_qty
						so_tot_rec_qty = line.so_line_id.received_qty + line.po_grn_qty
						
						so_line_obj.write(cr, uid, [line.so_line_id.id],
								{
								'pending_qty' : so_line_pending_qty,
								'received_qty' : so_tot_rec_qty,
								})
						so_obj.write(cr,uid,line.so_line_id.service_id.id, {'grn_flag': False,'adv_flag':True})
						
					if line.si_line_id and line.so_line_id.service_id.gp_id:
						sql1 = """ update kg_gate_pass_line set grn_pending_qty=(grn_pending_qty - %s) where si_line_id = %s and gate_id = %s"""%(line.po_grn_qty,
															line.si_line_id.id,line.so_line_id.service_id.gp_id.id)
						cr.execute(sql1)
					elif not line.si_line_id and line.so_line_id:
						sql1 = """ update kg_gate_pass_line set grn_pending_qty=(grn_pending_qty - %s) where product_id = %s and gate_id = %s"""%(line.po_grn_qty,
															line.product_id.id,line.so_line_id.service_id.gp_id.id)
						cr.execute(sql1)
					else:
						pass
					
					so_ids = [x.id for x in grn_entry.so_ids]
					
					for i in so_ids:
						so_grn_sea = self.pool.get('kg.service.order').search(cr,uid,[('id','=',i)])
						so_grn_rec = self.pool.get('kg.service.order').browse(cr,uid,so_grn_sea[0])
						if grn_entry.grn_type == 'from_so':
							sql = """ select * from kg_gate_pass_line where grn_pending_qty > 0 and gate_id in (%s)"""%(so_grn_rec.gp_id.id)
							cr.execute(sql)
							data = cr.dictfetchall()
							if data:
								gate_obj.write(cr,uid,so_grn_rec.gp_id.id,{'in_state':'partial'})
							else:
								gate_obj.write(cr,uid,so_grn_rec.gp_id.id,{'in_state':'done'})
				# This code is to update pending qty in Gate Pass
				elif grn_entry.grn_type == 'from_gp':
					if line.gp_line_id:
						gp_line_pending_qty = line.gp_pending_qty - line.po_grn_qty
						if gp_line_pending_qty > 0:
							status = 'partial'
						else:
							status = 'done'
						gp_obj.write(cr, uid, [line.gp_line_id.gate_id.id],
								{
								'in_state' : status
								})
						gp_line_obj.write(cr, uid, [line.gp_line_id.id],
								{
								'grn_pending_qty' : gp_line_pending_qty,
								})
				else:
					pass
				# This code will create PO GRN to Stock Move
				
				if grn_entry.grn_type == 'from_po':
					if line.length == 0.00:
						line_length = 1
					else:
						line_length = line.length
					if line.breadth == 0.00:
						line_breadth = 1
					else:
						line_breadth = line.breadth
					
					store_uom_stk_qty = line.po_grn_qty * line_length * line_breadth * line.product_id.po_uom_coeff				
					po_uom_stk_qty = line.po_grn_qty * line_length * line_breadth
					
					stock_move_obj.create(cr,uid,
						{
						'po_grn_id': grn_entry.id,
						'po_grn_line_id': line.id,
						'purchase_line_id': line.po_line_id.id,
						'po_id': grn_entry.po_id.id,
						'product_id': line.product_id.id,
						'brand_id': line.brand_id.id,
						'moc_id': line.moc_id.id,
						'name': line.product_id.name,
						'product_qty': store_uom_stk_qty,
						'po_to_stock_qty': po_uom_stk_qty,
						'stock_uom': line.product_id.uom_id.id,
						'product_uom': line.product_id.uom_po_id.id,
						'location_id': grn_entry.supplier_id.property_stock_supplier.id,
						'location_dest_id': line.location_dest_id.id,
						'move_type': 'in',
						'state': 'done',
						'price_unit': (line.price_subtotal / line.po_grn_qty) or 0.0,
						'origin': grn_entry.po_id.name,
						'stock_rate': (line.price_subtotal / line.po_grn_qty) or 0.0,
						'billing_type': line.billing_type,
						'uom_conversation_factor': line.uom_conversation_factor,
						'trans_date': grn_entry.grn_date,
						})
					
					line.write({'state':'done'})
					
				elif grn_entry.grn_type == 'from_so':
					if line.length == 0.00:
						line_length = 1
					else:
						line_length = line.length
					if line.breadth == 0.00:
						line_breadth = 1
					else:
						line_breadth = line.breadth
						
					store_uom_stk_qty = line.po_grn_qty * line_length * line_breadth * line.product_id.po_uom_coeff				
					po_uom_stk_qty = line.po_grn_qty * line_length * line_breadth
						
					stock_move_obj.create(cr,uid,
						{
						'po_grn_id': grn_entry.id,
						'po_grn_line_id': line.id,
						'so_line_id': line.so_line_id.id,
						'so_id': grn_entry.so_id.id,
						'product_id': line.product_id.id,
						'brand_id': line.brand_id.id,
						'moc_id': line.moc_id.id,
						'name': line.product_id.name,
						'product_qty': store_uom_stk_qty,
						'po_to_stock_qty': po_uom_stk_qty,
						'stock_uom': line.product_id.uom_id.id,
						'product_uom': line.product_id.uom_po_id.id,
						'location_id': grn_entry.supplier_id.property_stock_supplier.id,
						'location_dest_id': line.location_dest_id.id,
						'move_type': 'in',
						'state': 'done',
						'price_unit': (line.price_subtotal / line.po_grn_qty) or 0.0,
						'origin': grn_entry.so_id.name,
						'stock_rate': (line.price_subtotal / line.po_grn_qty) or 0.0,
						'trans_date': grn_entry.grn_date,
						})
					
					line.write({'state':'done'})
						
				elif grn_entry.grn_type == 'from_gp':
					if line.length == 0.00:
						line_length = 1
					else:
						line_length = line.length
					if line.breadth == 0.00:
						line_breadth = 1
					else:
						line_breadth = line.breadth
						
					store_uom_stk_qty = line.po_grn_qty * line_length * line_breadth * line.product_id.po_uom_coeff				
					po_uom_stk_qty = line.po_grn_qty * line_length * line_breadth
							
					stock_move_obj.create(cr,uid,
					
						{
						
						'po_grn_id': grn_entry.id,
						'po_grn_line_id': line.id,
						'gp_line_id': line.gp_line_id.id,
						'gp_id': line.gp_line_id.gate_id.id,
						'product_id': line.product_id.id,
						'brand_id': line.brand_id.id,
						'moc_id': line.moc_id.id,
						'name': line.product_id.name,
						'product_qty': store_uom_stk_qty,
						'po_to_stock_qty': po_uom_stk_qty,
						'stock_uom': line.product_id.uom_id.id,
						'product_uom': line.product_id.uom_po_id.id,
						'location_id': grn_entry.supplier_id.property_stock_supplier.id,
						'location_dest_id': line.location_dest_id.id,
						'move_type': 'in',
						'state': 'done',
						'price_unit': (line.price_subtotal / line.po_grn_qty) or 0.0,
						'origin': line.gp_line_id.gate_id.name,
						'stock_rate': (line.price_subtotal / line.po_grn_qty) or 0.0,
						'trans_date': grn_entry.grn_date,
						
						})
					line.write({'state':'done'})
				else:
					pass
				
				# This code will create Production lot
				grn_type = 'service'
				if grn_entry.grn_type == 'from_po':
					grn_type = 'material'
				
				if line.po_exp_id:
					for exp in line.po_exp_id:
						if line.length == 0.00:
							line_length = 1
						else:
							line_length = line.length
						if line.breadth == 0.00:
							line_breadth = 1
						else:
							line_breadth = line.breadthbreadth = line.breadth
						
						store_uom_stk_qty = exp.product_qty * line_length * line_breadth * line.product_id.po_uom_coeff				
						po_uom_stk_qty = exp.product_qty * line_length * line_breadth				
											
						lot_obj.create(cr,uid,
							{
							'grn_no':line.po_grn_id.name,
							'product_id':line.product_id.id,
							'brand_id':line.brand_id.id,
							'moc_id':line.moc_id.id,
							'po_uom':line.product_id.uom_po_id.id,
							'product_uom':line.product_id.uom_id.id,
							'location_id':line.location_dest_id.id,
							'location_code': line.location_dest_id.code,
							'po_product_qty':po_uom_stk_qty,
							'product_qty':store_uom_stk_qty,
							'pending_qty':po_uom_stk_qty,
							'store_pending_qty':store_uom_stk_qty,
							'issue_qty':0.00,
							'batch_no':line.po_grn_id.name,
							'expiry_date':exp.exp_date,
							'price_unit':line.price_subtotal / exp.product_qty or 0.0,
							'grn_type':grn_type,
							'reserved_qty':0.00,
							'trans_date': grn_entry.grn_date,
						})
				else:
					if line.length == 0.00:
						line_length = 1
					else:
						line_length = line.length
					if line.breadth == 0.00:
						line_breadth = 1
					else:
						line_breadth = line.breadth_breadth = line.breadth
						
					store_uom_stk_qty = line.po_grn_qty * line_length * line_breadth * line.product_id.po_uom_coeff				
					po_uom_stk_qty = line.po_grn_qty * line_length * line_breadth
					
					lot_obj.create(cr,uid,
						{
						'grn_no':line.po_grn_id.name,
						'product_id':line.product_id.id,
						'brand_id':line.brand_id.id,
						'moc_id':line.moc_id.id,
						'po_uom':line.product_id.uom_po_id.id,
						'product_uom':line.product_id.uom_id.id,
						'location_id':line.location_dest_id.id,
						'location_code': line.location_dest_id.code,
						'po_product_qty':po_uom_stk_qty,
						'product_qty':store_uom_stk_qty,
						'pending_qty':po_uom_stk_qty,
						'store_pending_qty':store_uom_stk_qty,
						'issue_qty':0.00,
						'price_unit':line.price_subtotal / line.po_grn_qty or 0.0,
						'batch_no':line.po_grn_id.name,
						'grn_type':grn_type,
						'trans_date': grn_entry.grn_date,
					})
					
				#~ #Write a tax amount in line
				product_tax_amt = self._amount_line_tax(cr, uid, line, context=context)
				cr.execute("""update po_grn_line set product_tax_amt = %s, line_state = 'done' where id = %s"""%(product_tax_amt,line.id))
				
			self.write(cr,uid,ids[0],{'state': 'done',
									  'approved_by': uid,
									  'approved_date': time.strftime('%Y-%m-%d %H:%M:%S'),
									  })
		
		return True
	
	# GRN Reject #
	
	def entry_reject(self, cr, uid, ids, context=None):
		grn = self.browse(cr, uid, ids[0])
		if grn.state =='confirmed':
			if not grn.reject_remark:
				raise osv.except_osv(_('Warning !'),_('Enter Remarks for GRN Rejection !!'))
			else:
				self.write(cr, uid, ids[0], {'state': 'draft','rej_user_id': uid,'reject_date': time.strftime("%Y-%m-%d %H:%M:%S")})
		return True
	
	# GRN Cancel #
	
	def entry_cancel(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.state == 'done':
			po_id = self.pool.get('purchase.order')
			so_id = self.pool.get('kg.service.order')
			if not rec.can_remark:
				raise osv.except_osv(_('Warning !'),_('Enter Remarks for GRN Cancellation !!'))
			else:
				self.write(cr, uid, ids[0], {'state': 'cancel','cancel_user_id': uid,'cancel_date': time.strftime("%Y-%m-%d %H:%M:%S")})
			for line in rec.line_ids:
				if rec.grn_type == 'from_po':
					po_id.write(cr, uid, line.po_line_id.order_id.id, {'grn_flag': False})
				if rec.grn_type == 'from_so':
					so_id.write(cr, uid, line.so_line_id.service_id.id, {'grn_flag': False})
		return True
	
	# GRN Delete #
	
	def unlink(self, cr, uid, ids, context=None):
		unlink_ids = []		  
		rec = self.browse(cr, uid, ids[0])
		po_id = self.pool.get('purchase.order')
		so_id = self.pool.get('kg.service.order')
		if rec.state not in ('draft','item_load'):
			raise osv.except_osv(_('Delete access denied !'), _('Unable to delete. Draft entry only you can delete !!'))
		else:
			if rec.line_ids:
				for line in rec.line_ids:
					if rec.grn_type == 'from_po':
						po_id.write(cr, uid, line.po_line_id.order_id.id, {'grn_flag': False})
					if rec.grn_type == 'from_so':
						so_id.write(cr, uid, line.so_line_id.service_id.id, {'grn_flag': False})
			unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_po_grn()

class po_grn_line(osv.osv):
	
	_name = "po.grn.line"
	_description = "PO GRN Line"
	
	def _amount_line(self, cr, uid, ids, prop, arg, context=None):
		cur_obj=self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		res = {}
		if context is None:
			context = {}
		for line in self.browse(cr, uid, ids, context=context):
			qty = 0.00
			if line.price_type == 'per_kg':
				if line.product_id.uom_conversation_factor == 'two_dimension':
					if line.product_id.po_uom_in_kgs > 0:
						qty = line.po_grn_qty * line.product_id.po_uom_in_kgs * line.length * line.breadth
				elif line.product_id.uom_conversation_factor == 'one_dimension':
					if line.product_id.po_uom_in_kgs > 0:
						qty = line.po_grn_qty * line.product_id.po_uom_in_kgs
					else:
						qty = line.po_grn_qty
				else:
					qty = line.po_grn_qty
			else:
				qty = line.po_grn_qty
			# Price Calculation
			price_amt = 0
			amt_to_per = 0.00
			if line.po_grn_id.grn_type == 'from_po':
				if line.po_line_id.price_type == 'per_kg':
					if line.product_id.po_uom_in_kgs > 0:
						price_amt = line.po_grn_qty / line.product_id.po_uom_in_kgs * line.price_unit
				else:
					price_amt = qty * line.po_line_id.price_unit
				dis_amt = (line.po_line_id.kg_discount / line.po_grn_qty or 1) * qty
				kg_discount_per = line.po_line_id.kg_discount_per
				tot_discount_per = amt_to_per + kg_discount_per
				price = line.po_line_id.price_unit - (line.po_line_id.kg_discount / line.po_grn_qty)
				taxes = tax_obj.compute_all(cr, uid, line.po_line_id.taxes_id, price, qty, line.product_id, line.po_grn_id.supplier_id)
			else:
				if line.price_type == 'per_kg':
					if line.product_id.po_uom_in_kgs > 0:
						price_amt = line.po_grn_qty / line.product_id.po_uom_in_kgs * line.price_unit
				else:
					price_amt = qty * line.price_unit
				dis_amt = (line.kg_discount / line.po_grn_qty or 1) * qty
				kg_discount_per = line.kg_discount_per
				tot_discount_per = amt_to_per + kg_discount_per
				price = line.price_unit - (line.kg_discount / line.po_grn_qty)
				taxes = tax_obj.compute_all(cr, uid, line.grn_tax_ids, price, qty, line.product_id, line.po_grn_id.supplier_id)
			cur = self.pool.get('res.currency').browse(cr,uid,1)
			res[line.id] = cur_obj.round(cr, uid, cur, taxes['total_included'])
			
		return res
	
	_columns = {
		
		## Basic Info
		
		'po_grn_id':fields.many2one('kg.po.grn','PO GRN Entry', ondelete='cascade'),
		'state': fields.selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),('done', 'Done'), ('cancel', 'Cancelled')], 'Status',readonly=True),
		'line_state': fields.selection([('draft', 'Draft'),('confirmed', 'Confirmed'),('done', 'Done')], 'Status',readonly=True),
		'remark':fields.text('Notes'),
		
		## Module Requirement Fields
		
		'po_grn_date':fields.date('PO GRN Date'),
		'name':fields.char('Product'),
		'product_id':fields.many2one('product.product','Product Name',required=True, domain="[('state','=','approved'),('purchase_ok','=',True)]"),
		'uom_id':fields.many2one('product.uom','PO UOM',domain="[('dummy_state','=','approved')]",required=True),
		'po_grn_qty':fields.float('Received Qty',required=True),
		'recvd_qty':fields.float('Received Qty'),
		'reject_qty':fields.float('Rejected Qty'),
		'po_qty':fields.float('PO Qty'),
		'so_qty':fields.float('SO Qty'),
		'gp_qty':fields.float('GP Qty'),
		'po_pending_qty':fields.float('PO Pending Qty'),
		'so_pending_qty':fields.float('SO Pending Qty'),
		'gp_pending_qty':fields.float('GP Pending Qty'),
		'price_unit':fields.float('Unit Price',required=True),
		'kg_discount_per': fields.float('Discount (%)', digits_compute= dp.get_precision('Discount')),
		'kg_discount': fields.float('Discount Amount'),
		'grn_tax_ids': fields.many2many('account.tax', 'po_grn_tax', 'order_id', 'taxes_id', 'Taxes'),
		'location_id': fields.many2one('stock.location', 'Source Location'),
		'location_dest_id': fields.many2one('stock.location', 'Location'),
		'po_line_id':fields.many2one('purchase.order.line','PO Line'),
		'po_id':fields.many2one('purchase.order','PO NO'),
		'so_line_id':fields.many2one('kg.service.order.line','SO Line'),
		'so_id':fields.many2one('kg.service.order','SO NO'),
		'gp_line_id':fields.many2one('kg.gate.pass.line','GP Line'),
		'gp_id':fields.many2one('kg.gate.pass','GP NO'),
		'pi_line_id':fields.many2one('purchase.requisition.line','PI Line'),
		'si_line_id':fields.many2one('kg.service.indent.line','SI Line'),
		'price_subtotal': fields.function(_amount_line, string='Line Total', digits_compute= dp.get_precision('Account'),store=True),
		#'price_subtotal': fields.function(_amount_line, string='Line Total', digits_compute= dp.get_precision('Account')),
		'brand_id':fields.many2one('kg.brand.master','Brand',domain="[('product_ids','in',(product_id)),('state','=','approved')]"),
		'so_flag':fields.boolean('SO Flag'),
		'po_flag':fields.boolean('PO Flag'),
		'gp_flag':fields.boolean('PO Flag'),
		'billing_type': fields.selection([('free', 'Free'), ('cost', 'Cost')], 'Billing Type'),
		'inward_type': fields.many2one('kg.inwardmaster','Inward Type',domain="[('state','=','approved')]"),
		'ser_no':fields.char('Ser No', size=128, readonly=True),
		'serial_no':fields.many2one('stock.production.lot','Serial No',domain="[('product_id','=',product_id)]", readonly=True),  
		'order_no': fields.char('No.',readonly=True),
		'order_date': fields.char('Order Date',readonly=True),
		'product_tax_amt':fields.float('Tax Amount'),  
		'price_type': fields.selection([('po_uom','PO UOM'),('per_kg','Per Kg')],'Price Type'),
		'uom_conversation_factor': fields.related('product_id','uom_conversation_factor', type='selection',selection=UOM_CONVERSATION, string='UOM Conversation Factor',store=True,readonly=True),
		'length': fields.float('Length',readonly=True),
		'breadth': fields.float('Breadth',readonly=True),
		'weight': fields.float('Weight',readonly=True),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'moc_id_temp': fields.many2one('ch.brandmoc.rate.details','MOC',domain="[('brand_id','=',brand_id),('header_id.product_id','=',product_id),('header_id.state','=','approved')]"),
		'uom_category': fields.selection([('length','Length'),('other','Others')],'UOM Category',required=True),
		
		## Child Tables Declaration
		
		'po_exp_id':fields.one2many('kg.po.exp.batch','po_grn_line_id','Expiry Line'),
		'line_wo_id': fields.one2many('ch.po.grn.wo','header_id','Ch Line Id'),
		
	}
	
	def onchange_qty(self,cr,uid,ids, po_grn_qty,length,breadth,uom_conversation_factor,product_id,uom_id, context=None):
		value = {'weight': 0}
		weight = 0
		if po_grn_qty and length and breadth and uom_conversation_factor and product_id and uom_id:
			prod_rec = self.pool.get('product.product').browse(cr,uid,product_id)
			if uom_id == prod_rec.uom_po_id.id:
				if uom_conversation_factor == 'two_dimension':
					if prod_rec.po_uom_in_kgs > 0:
						weight = po_grn_qty * prod_rec.po_uom_in_kgs * length * breadth
			elif uom_id == prod_rec.uom_id.id:
				if uom_conversation_factor == 'two_dimension':
					if prod_rec.po_uom_in_kgs > 0:
						weight = po_grn_qty / prod_rec.po_uom_in_kgs / length / breadth
			print"weightweight",weight
			value = {'weight': weight}
		return {'value': value}
	
	def onchange_product_id(self,cr,uid,ids, product_id, uom_id,context=None):
		value = {'uom_id': ''}
		if product_id:
			prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			value = {'uom_id': prod.uom_id.id}
		return {'value': value}
	
	def onchange_moc(self, cr, uid, ids, moc_id_temp):
		value = {'moc_id':''}
		if moc_id_temp:
			rate_rec = self.pool.get('ch.brandmoc.rate.details').browse(cr,uid,moc_id_temp)
			value = {'moc_id': rate_rec.moc_id.id}
		return {'value': value}
	
	_defaults = {
		
		'state': 'draft',
		'line_state': 'draft',
		'billing_type': 'free',
		'price_type': 'po_uom',
		
	}   
	
	def _check_weight(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.weight < 0.00:
			return False
		return True
	
	_constraints = [
		
		(_check_weight,'You cannot save with negative weight !',['Weight']),
		
		]
	
po_grn_line()

class kg_po_exp_batch(osv.osv):
	
	_name = "kg.po.exp.batch"
	_description = "Expiry Date and Batch NO"
	
	_columns = {
		
		## Basic Info
		
		'po_grn_line_id':fields.many2one('po.grn.line','PO GRN Entry Line', ondelete='cascade'),
		
		## Module Requirement Fields
		
		'exp_date':fields.date('Expiry Date'),
		'batch_no':fields.char('Batch No'),
		'product_qty':fields.float('Product Qty'),
		
	}
	
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.product_qty <= 0:
			return False
		return True
	
	_constraints = [
		
		(_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
kg_po_exp_batch()

class kg_po_grn_expense_track(osv.osv):
	
	_name = "kg.po.grn.expense.track"
	_description = "kg expense track"
	
	_columns = {
		
		## Basic Info
		
		'expense_id': fields.many2one('kg.po.grn', 'Expense Track', ondelete='cascade'),
		
		## Module Requirement Fields
		
		'name': fields.char('Number', size=128, select=True,readonly=False),
		'date': fields.date('Creation Date'),
		'company_id': fields.many2one('res.company', 'Company Name'),
		'description': fields.char('Description'),
		'expense_amt': fields.float('Amount'),
		
	}
	
	_defaults = {
		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.po.grn.expense.track', context=c),
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
		
		}
	
kg_po_grn_expense_track()

class ch_po_grn_wo(osv.osv):
	
	_name = "ch.po.grn.wo"
	_description = "Ch PO GRN WO"
	
	_columns = {
		
		## Basic Info
		
		'header_id': fields.many2one('po.grn.line', 'PO Line', ondelete='cascade'),
		
		## Module Requirement Fields
		
		'wo_id': fields.char('WO No.'),
		'w_order_id': fields.many2one('kg.work.order','WO',domain="[('state','=','confirmed')]"),
		'w_order_line_id': fields.many2one('ch.work.order.details','WO'),
		'qty': fields.float('Qty'),
		
	}
	
	def onchange_wo(self, cr, uid, ids,w_order_line_id):
		value = {'wo_id': ''}
		if w_order_line_id:
			wo_rec = self.pool.get('ch.work.order.details').browse(cr,uid,w_order_line_id)
			value = {'wo_id':wo_rec.order_no}
		return {'value':value}
	
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False
		return True
	
	_constraints = [
		
		(_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
	
ch_po_grn_wo()
