from datetime import *
import time
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import decimal_precision as dp
from itertools import groupby
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import netsvc
import pooler
import logging
logger = logging.getLogger('server')
today = datetime.now()
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_so_amendment(osv.osv):
	
	_name = "kg.so.amendment"
	_description = "SO Amendment"
	_order = "trans_date desc"
	
	def _amount_line_tax(self, cr, uid, line, context=None):
		val = 0.0
		new_amt_to_per = line.kg_discount_amend or 0.0 / line.product_qty_amend
		amt_to_per = (line.discount_amend or 0.0 / (line.product_qty_amend * line.price_unit_amend or 1.0 )) * 100
		kg_discount_per = line.kg_discount_per_amend
		tot_discount_per = amt_to_per + kg_discount_per
		for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id_amend,
			line.price_unit_amend * (1-(tot_discount_per or 0.0)/100.0), line.product_qty_amend, line.product_id,
			line.amendment_id.partner_id)['taxes']:
			val += c.get('amount', 0.0)
		return val
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		so_obj=self.pool.get('kg.service.order')
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
			val = val1 = val3 = 0.0
			for line in order.line_ids:
				discount_per_value = ((line.product_qty_amend * line.price_unit_amend) / 100.00) * line.kg_discount_per_amend
				tot_discount = line.kg_discount_amend + discount_per_value
				val1 += line.price_subtotal
				val += self._amount_line_tax(cr, uid, line, context=context)
				val3 += tot_discount
			
			res[order.id]['total_amount_amend'] = (val1 + val3) - val
			res[order.id]['other_charge'] = other_charges_amt or 0
			res[order.id]['amount_tax_amend'] = val
			res[order.id]['amount_untaxed_amend'] = val1 - val 
			res[order.id]['discount_amend'] = val3
			res[order.id]['grand_total_amend'] = val1
			res[order.id]['round_off_amend'] = order.round_off
			res[order.id]['amount_total_amend'] = val1 + order.round_off_amend or 0.00
			#~ so_obj.write(cr, uid,order.so_id.id, {'amount_total': val1})
		
		return res
	
	def _get_order(self, cr, uid, ids, context=None):
		result = {}
		for line in self.pool.get('kg.so.amendment.line').browse(cr, uid, ids, context=context):
			result[line.amendment_id.id] = True
		return result.keys()	
	
	_columns = {
		
		## Basic Info
		
		'name': fields.char('Amendment SO No', size=128,select=True,readonly=True),
		'state': fields.selection([('amend','Processing'),('draft','Draft'),('confirm','confirmed'),('approved','Approved'),
				('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True,track_visibility='onchange',select=True),
		'remark': fields.text('Remarks',readonly=True,required=True,states={'confirm':[('readonly',False)]}),
		'note': fields.text('Notes'),
		
		## Module Requirement Info
		
		'trans_date': fields.date('Amend SO Date', readonly=True, states={'draft':[('readonly',False)]}),						
		'partner_id': fields.many2one('res.partner', 'Supplier', select=True,domain=[('supplier', '=', True)], readonly=True),
		'partner_id_amend':fields.many2one('res.partner', 'Amend Supplier',domain=[('supplier', '=', True)], readonly=True, states={'draft':[('readonly',False)]}),
		'orderby_no': fields.integer('Order By',readonly=True),
		'total': fields.float('Total Amount', readonly=True),
		'so_id':fields.many2one('kg.service.order','SO.NO', required=True,domain="[('state','=','approved'),'&',('service_order_line.pending_qty','>',0),'&',('so_bill','=',False)]",readonly=True,states={'amend':[('readonly',False)]}),
		'amend_flag':fields.boolean('Amend Flag'),
		'so_date':fields.date('SO Date', readonly=True),
		'so_date_amend':fields.date('Amend SO Date',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'quot_ref_no':fields.char('Quot.Ref',readonly=True),
		'quot_ref_no_amend':fields.char('Amend Quot. Ref.',readonly=True, states={'draft':[('readonly', False)],'confirm':[('readonly', False)]}),
		'partner_address':fields.char('Supplier Address', size=128, readonly=True),
		'partner_address_amend':fields.char('Amend Supplier Address', size=128, readonly=True, states={'draft':[('readonly',False)]}),
		'payment_mode': fields.many2one('kg.payment.master', 'Mode of Payment', readonly=True),
		'payment_mode_amend': fields.many2one('kg.payment.master', 'Amend Mode of Payment', readonly=True, states={'draft':[('readonly',False)]}),
		'payment_type': fields.selection([('cash', 'Cash'),('credit', 'Credit'),('advance','Advance')], 'Payment Mode',readonly=True),
		'payment_type_amend': fields.selection([('cash', 'Cash'),('credit', 'Credit'),('advance','Advance')], 'Amend Payment Mode',readonly=True, states={'draft':[('readonly',False)]}),
		'advance_amt': fields.float('Advance Amount(%)',readonly=True),
		'advance_amt_amend': fields.float('Amend Advance(%)',readonly=True, states={'draft':[('readonly',False)]}),
		'freight_charges':fields.selection([('Inclusive','Inclusive'),('Extra','Extra'),('To Pay','To Pay'),('Paid','Paid'),
						  ('Extra at our Cost','Extra at our Cost')],'Freight Charges',readonly=True),
		'freight_charges_amend':fields.selection([('Inclusive','Inclusive'),('Extra','Extra'),('To Pay','To Pay'),('Paid','Paid'),
						  ('Extra at our Cost','Extra at our Cost')],'Amend Freight Charges',readonly=True, states={'draft':[('readonly',False)]}),
		'dep_name': fields.many2one('kg.depmaster','Department Name', translate=True, domain="[('item_request','=',True)('state','in',('draft','confirmed','approved'))]", select=True,readonly=True),
		'dep_name_amend': fields.many2one('kg.depmaster','Amend Department Name', translate=True, domain="[('item_request','=',True),('state','in',('draft','confirmed','approved'))]", select=True,readonly=True, states={'draft':[('readonly',False)]}),
		'price':fields.selection([('inclusive','Inclusive of all Taxes and Duties'),('exclusive','Excluding All Taxes and Duties')],'Price',readonly=True),
		'price_amend':fields.selection([('inclusive','Inclusive of all Taxes and Duties'),('exclusive','Excluding All Taxes and Duties')],'Amend Price',readonly=True, states={'draft':[('readonly',False)]}),
		'warranty': fields.char('Warranty', size=256,readonly=True),
		'warranty_amend': fields.char('Amend Warranty', size=256,readonly=True,states={'draft':[('readonly',False)]}),
		'other_charge': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Other Charges(+)',
			 multi="sums", help="The amount without tax", track_visibility='always'),
		'total_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Amount',
			 multi="sums", store=True, help="The amount without tax", track_visibility='always'),
		'discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Discount(-)',
			store={
				'kg.so.amendment': (lambda self, cr, uid, ids, c={}: ids, ['line_ids'], 10),
				'kg.so.amendment.line': (_get_order, ['price_unit_amend', 'tax_id', 'kg_discount_amend', 'product_qty_amend'], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
			store={
				'kg.so.amendment': (lambda self, cr, uid, ids, c={}: ids, ['line_ids'], 10),
				'kg.so.amendment.line': (_get_order, ['price_unit_amend', 'tax_id', 'kg_discount_amend', 'product_qty_amend'], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
			store={
				'kg.so.amendment': (lambda self, cr, uid, ids, c={}: ids, ['line_ids'], 10),
				'kg.so.amendment.line': (_get_order, ['price_unit_amend', 'tax_id', 'kg_discount_amend', 'product_qty_amend'], 10),
			}, multi="sums", help="The tax amount"),
		'grand_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Grand Total',
			 multi="sums", store=True, help="The amount without tax", track_visibility='always'),
		'round_off': fields.float('Round off',size=5,readonly=False, states={'approved':[('readonly',True)]}),
		'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total',
			store={
				'kg.so.amendment': (lambda self, cr, uid, ids, c={}: ids, ['line_ids'], 10),
				'kg.so.amendment.line': (_get_order, ['price_unit_amend', 'tax_id', 'kg_discount_amend', 'product_qty_amend'], 10),
			}, multi="sums",help="The total amount"),
			
		# Amendment Fields
		
		'other_charge_amend': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Other Charges(+)',
			 multi="sums", help="The amount without tax", track_visibility='always'),
		'total_amount_amend': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Amount',
			 multi="sums", store=True, help="The amount without tax", track_visibility='always'),
		'discount_amend': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Discount(-)',
			store={
				'kg.so.amendment': (lambda self, cr, uid, ids, c={}: ids, ['line_ids'], 10),
				'kg.so.amendment.line': (_get_order, ['price_unit_amend', 'tax_id', 'kg_discount_amend', 'product_qty_amend'], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_untaxed_amend': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
			store={
				'kg.so.amendment': (lambda self, cr, uid, ids, c={}: ids, ['line_ids'], 10),
				'kg.so.amendment.line': (_get_order, ['price_unit_amend', 'tax_id', 'kg_discount_amend', 'product_qty_amend'], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_tax_amend': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
			store={
				'kg.so.amendment': (lambda self, cr, uid, ids, c={}: ids, ['line_ids'], 10),
				'kg.so.amendment.line': (_get_order, ['price_unit_amend', 'tax_id', 'kg_discount_amend', 'product_qty_amend'], 10),
			}, multi="sums", help="The tax amount"),
		'grand_total_amend': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Grand Total',
			 multi="sums", store=True, help="The amount without tax", track_visibility='always'),
		'round_off_amend': fields.float('Round off',size=5,readonly=False, states={'approved':[('readonly',True)]}),
		'amount_total_amend': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total',
			store={
				'kg.so.amendment': (lambda self, cr, uid, ids, c={}: ids, ['line_ids'], 10),
				'kg.so.amendment.line': (_get_order, ['price_unit_amend', 'tax_id', 'kg_discount_amend', 'product_qty_amend'], 10),
			}, multi="sums",help="The total amount"),
		
		'grn_flag': fields.boolean('GRN'),
		'pricelist_id':fields.many2one('product.pricelist', 'Pricelist', required=True, states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)]}),
		'currency_id': fields.related('pricelist_id', 'currency_id', type="many2one", relation="res.currency", string="Currency",readonly=True, required=True),
		
		## Child Tables Declaration
		
		'line_ids':fields.one2many('kg.so.amendment.line', 'amendment_id', 'SO Amendment Line',readonly=True, states={'draft':[('readonly',False)]}),
		
		# Entry Info
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'date': fields.datetime('Creation Date', readonly=True)	,
		'user_id': fields.many2one('res.users','Created By', readonly=True),
		'confirm_date': fields.datetime('Confirm Date', readonly=True),
		'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Approved By', readonly=True),
		'reject_date': fields.datetime('Reject Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'cancel_date': fields.datetime('Cancel Date', readonly=True),
		'can_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date' : fields.datetime('Last Updated Date',readonly=True),
		'update_user_id' : fields.many2one('res.users','Last Updated By',readonly=True),
		
	}
	
	_defaults = {
		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_so_amendment', context=c),
		'trans_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'amend',
		'remark': '.',	
		'active': True,
		'amend_flag': False,
		'user_id': lambda obj, cr, uid, context: uid,
		'pricelist_id': 2,
		
	}
	
	def _check_advance(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state not in ('draft','amend'):
			if rec.payment_type_amend == 'advance':
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
	
	def button_dummy(self, cr, uid, ids,context=None):
		return True		
	
	def _prepare_amend_line(self, cr, uid, so_order, order_line, amend_id, context=None):
		
		return {
		
			'order_id':so_order.id,
			'product_id': order_line.product_id.id,
			'product_id_amend': order_line.product_id.id,
			'uom_id': order_line.product_uom.id,
			'uom_id_amend': order_line.product_uom.id,
			'amendment_id': amend_id,
			'so_line_id': order_line.id,
			'price_unit' : order_line.price_unit or 0.0,
			'price_unit_amend' : order_line.price_unit or 0.0,
			'product_qty' : order_line.product_qty,
			'product_qty_amend' : order_line.product_qty,
			'pending_qty' : order_line.pending_qty,
			'pending_qty_amend' : order_line.pending_qty,
			'brand_id': order_line.brand_id.id,
			'brand_id_amend': order_line.brand_id.id,
			'note' : order_line.note,
			'note_amend' : order_line.note,
			'kg_discount' : order_line.kg_discount,
			'discount_amend' : order_line.kg_discount,
			'kg_discount_amend' : order_line.kg_discount,
			'kg_discount_per' : order_line.kg_discount_per,
			'kg_discount_per_amend' : order_line.kg_discount_per,
			'kg_discount_per_value' : order_line.kg_discount_per_value,
			'kg_discount_per_value_amend' : order_line.kg_discount_per_value,
			'kg_disc_amt_per':order_line.kg_disc_amt_per,
			'kg_disc_amt_per_amend':order_line.kg_disc_amt_per,
			'taxes_id':[(6, 0, [x.id for x in order_line.taxes_id])],
			'taxes_id_amend':[(6, 0, [x.id for x in order_line.taxes_id])],
			'price_subtotal' : order_line.price_subtotal,
		}
	
	def make_amend(self,cr,uid,ids,amendment_id=False,context={}):
		so_id = False
		amend_obj=self.pool.get('kg.so.amendment')
		obj = self.browse(cr,uid,ids[0])
		if obj.state == 'amend':
			so_obj=self.pool.get('kg.service.order')
			so_order = obj.so_id
			total_amends=amend_obj.search(cr,uid,[('so_id','=',obj.so_id.id)])
			draft_amends=amend_obj.search(cr,uid,[('so_id','=',obj.so_id.id),('state','not in',('approved','reject'))])
			if len(draft_amends) > 1:
				raise osv.except_osv(_('Amendment has been created for this SO!'),
					_('Please approve that for proceed another Amendment!!')) 
			
			sql = """delete from kg_so_amendment where state='amend' and id !=%s"""%(str(ids[0]))
			cr.execute(sql)
			if len(total_amends) == 1:
				amend_no = so_order.name + '-01'
			else:
				amend_no = so_order.name + '-' + '%02d' % int(str(len(total_amends)))
			
			if obj.partner_id.id is False:
				
				vals = {
						'amend_flag': True,
						'name' : amend_no, 
						'so_id' : so_order.id, 
						'so_date' : so_order.date, 
						'so_date_amend' : so_order.date, 
						'quot_ref_no' : so_order.quot_ref_no, 
						'quot_ref_no_amend' : so_order.quot_ref_no, 
						'partner_id' : so_order.partner_id.id, 
						'partner_id_amend' : so_order.partner_id.id, 
						'partner_address' : so_order.partner_address, 
						'partner_address_amend' : so_order.partner_address, 
						'payment_mode' : so_order.payment_mode.id, 
						'payment_mode_amend' : so_order.payment_mode.id, 
						'freight_charges' : so_order.freight_charges, 
						'freight_charges_amend' : so_order.freight_charges, 
						'dep_name' : so_order.dep_name.id, 
						'dep_name_amend' : so_order.dep_name.id, 
						'warranty' : so_order.warranty, 
						'warranty_amend' : so_order.warranty, 
						'price' : so_order.price, 
						'price_amend' : so_order.price,
						'pricelist_id': so_order.pricelist_id.id,
						'line_ids' : [],	
						'amount_untaxed':so_order.amount_untaxed,
						'amount_tax':so_order.amount_tax,
						'amount_total':so_order.amount_total,
						'discount':so_order.discount,		
							
						}
				print "vals ..........",vals
				self.pool.get('kg.so.amendment').write(cr,uid,ids,vals)
				amend_id = obj.id
				todo_lines = []
				amend_line_obj = self.pool.get('kg.so.amendment.line')
				wf_service = netsvc.LocalService("workflow")
				order_lines=so_order.service_order_line
				self.write(cr,uid,ids[0],{'state':'draft'})
				for order_line in order_lines:
					if order_line:
						amend_line = amend_line_obj.create(cr, uid, self._prepare_amend_line(cr, uid, so_order, order_line, amend_id,
										context=context))
						cr.execute(""" select service_order_line_id from service_order_tax where tax_id = %s """  %(str(order_line.id)))
						data = cr.dictfetchall()
						val = [d['service_order_line_id'] for d in data if 'service_order_line_id' in d]
					else:
						print "NO Line"

				wf_service.trg_validate(uid, 'kg.so.amendment', amend_id, 'button_confirm', cr)
				return [amend_id]
				cr.close()
			else:
				raise osv.except_osv(_('Amendment Created Already!'),
					_('System not allow to create Amendment again !!')) 
		
		return True
	
	def write(self, cr, uid, ids, vals, context=None):		
		vals.update({'update_date': dt_time,'update_user_id':uid})
		return super(kg_so_amendment, self).write(cr, uid, ids, vals, context)
	
	def confirm_amend(self, cr, uid, ids,context=None):
		amend_obj = self.browse(cr,uid,ids[0])
		if amend_obj.state == 'draft':
			so_obj = self.pool.get('kg.service.order')
			product_obj = self.pool.get('product.product')
			so_line_obj = self.pool.get('kg.service.order.line')
			amend_line_obj = self.pool.get('kg.so.amendment.line')
			si_line_obj = self.pool.get('kg.service.indent.line')
			stock_move_obj = self.pool.get('stock.move')
			for amend_line in amend_obj.line_ids:
				so_line_id = amend_line.so_line_id.id
				so_rec = amend_obj.so_id
				sol_record = amend_line.so_line_id
				diff_qty = amend_line.product_qty - amend_line.product_qty_amend
				pending_diff_qty = amend_line.product_qty - amend_line.pending_qty
				if so_rec.so_type == 'service':
					if amend_line.product_qty < amend_line.product_qty_amend:
							si_line_record = si_line_obj.browse(cr, uid,sol_record.soindent_line_id.id)
							if si_line_record.pending_qty <= 0:
								if not amend_line.kg_soindent_lines:
									raise osv.except_osv(_('If you want to increase SO Qty'),
										_('Select SI for this Product')) 
								else:
									for ele in amend_line.kg_soindent_lines:
										if ele.product_id.id == amend_line.product_id.id:
											if (amend_line.product_qty_amend - amend_line.product_qty) <= ele.pending_qty:
												si_line_obj.write(cr,uid,si_line_record.id,{'pending_qty': ele.pending_qty}) 
												amend_line_obj.write(cr,uid,amend_line.id,{'si_line_id':ele.id})
												line_pending = ele.pending_qty - (amend_line.product_qty_amend - amend_line.product_qty)
												si_line_obj.write(cr,uid,ele.id,{'pending_qty': line_pending}) 
											else:
												raise osv.except_osv(_('Warning'),
													_('Amendment Qty is greater than indent qty')) 	
					else:
						grn_id = self.pool.get('po.grn.line').search(cr, uid, [('so_line_id','=',amend_line.so_line_id.id)])
						if grn_id:
							grn_bro = self.pool.get('po.grn.line').browse(cr, uid, grn_id[0])
							if grn_bro.po_grn_qty <= amend_line.product_qty_amend:
								pass
							else:
								raise osv.except_osv(_('You can not decrease SO Qty'),
									_('Because GRN is already created'))
						else:
							pass
					if amend_line.product_qty != amend_line.product_qty_amend:
						if amend_line.pending_qty == 0 and not amend_line.kg_soindent_lines:
							raise osv.except_osv(_('All Qty has received for this SO !'),
								_('You can not increase SO Qty for product %s')%(amend_line.product_id.name))
					else:
						pass		
				else:
					if so_rec.so_bill == 't':
						raise osv.except_osv(_('You cannot change SO Qty'),
							_('Because Invoice is already created'))
					else:
						pass
			self.write(cr,uid,ids[0],{'state':'confirm','conf_user_id': uid,'confirm_date': dt_time})							   
		return True						   		
	
	def approve_amend(self, cr, uid, ids,context=None):
		amend_obj = self.browse(cr,uid,ids[0])
		if amend_obj.state == 'confirm':
			so_obj = self.pool.get('kg.service.order')
			gate_obj = self.pool.get('kg.gate.pass')
			product_obj = self.pool.get('product.product')
			so_line_obj = self.pool.get('kg.service.order.line')
			amend_line_obj = self.pool.get('kg.so.amendment.line')
			si_line_obj = self.pool.get('kg.service.indent.line')
			gate_line_obj = self.pool.get('kg.gate.pass')
			stock_move_obj = self.pool.get('stock.move')
			
			#~ if amend_obj.payment_type_amend == 'advance':
				#~ pre_obj = self.pool.get('kg.supplier.advance').search(cr,uid,[('po_id','=',amend_obj.po_id.id),('state','!=','cancel')])
				#~ if not pre_obj:
					#~ self.advance_creation(cr,uid,amend_obj)
			#~ elif amend_obj.payment_type_amend in ('cash','credit'):
				#~ if amend_obj.payment_type == 'advance':
					#~ pre_obj = self.pool.get('kg.supplier.advance').search(cr,uid,[('po_id','=',amend_obj.so_id.id),('state','!=','cancel')])
					#~ if pre_obj:
						#~ raise osv.except_osv(_('Warning!'),
							#~ _('Please cancel or delete supplier advance for this PO %s!'%(amend_obj.so_id.name)))
			#~ else:
				#~ pass
			
			if amend_obj.line_ids ==[]:
				raise osv.except_osv(_('Empty Purchase Amendment!'),
					_('System not allow to confirm a SO Amendment without Amendment Line !!'))
			else:
				so_id = amend_obj.so_id.id
				so_record = so_obj.browse(cr,uid,so_id)
				so_obj.write(cr,uid,so_id,{'amend_flag': True})	
				if amend_obj.partner_id.id != amend_obj.partner_id_amend.id:
					so_obj.write(cr,uid,so_id,{'partner_id': amend_obj.partner_id_amend.id,'partner_address':amend_obj.partner_address_amend})
				if amend_obj.advance_amt != amend_obj.advance_amt_amend:
					so_obj.write(cr,uid,so_id,{'advance_amt': amend_obj.advance_amt_amend})
				if amend_obj.payment_type != amend_obj.payment_type_amend:
					so_obj.write(cr,uid,so_id,{'payment_type': amend_obj.payment_type_amend})
				if amend_obj.payment_mode != amend_obj.payment_mode_amend:
					so_obj.write(cr,uid,so_id,{'payment_mode': amend_obj.payment_mode_amend})
				version = amend_obj.name[-2:]
				
				so_obj.write(cr,uid,so_id,{'date': amend_obj.so_date_amend,'quot_ref_no':amend_obj.quot_ref_no_amend,
											'payment_mode':amend_obj.payment_mode_amend.id,
											'freight_charges':amend_obj.freight_charges_amend,'dep_name':amend_obj.dep_name_amend.id,
											'warranty':amend_obj.warranty_amend,'price':amend_obj.price_amend,'amount_total':amend_obj.amount_total,
											'version':version,
											
											})
				for amend_line in amend_obj.line_ids:
					so_line_id = amend_line.so_line_id.id
					so_rec = amend_obj.so_id
					sol_record = amend_line.so_line_id
					diff_qty = amend_line.product_qty - amend_line.product_qty_amend
					pending_diff_qty = amend_line.product_qty - amend_line.pending_qty
					if so_rec.so_type == 'service':
						if amend_line.product_qty < amend_line.product_qty_amend:
							si_line_record = si_line_obj.browse(cr, uid,sol_record.soindent_line_id.id)
							if si_line_record.pending_qty <= 0:
								if not amend_line.kg_soindent_lines:
									raise osv.except_osv(_('If you want to increase SO Qty'),
										_('Select SI for this Product')) 
							else:
								si_product_qty = si_line_record.qty
								si_pending_qty = si_line_record.pending_qty
								re_qty = amend_line.product_qty_amend-amend_line.product_qty
								sql = """ update kg_gate_pass_line set qty=(qty + %s),grn_pending_qty=(grn_pending_qty + %s),so_pending_qty=(so_pending_qty + %s) where gate_id=%s and si_line_id= %s """%(re_qty,re_qty,re_qty,so_rec.gp_id.id,si_line_record.id)
								cr.execute(sql)
								if amend_line.kg_soindent_lines:
									if si_pending_qty >= re_qty:
										amend_pend = si_pending_qty - re_qty
										si_line_obj.write(cr,uid,sol_record.soindent_line_id.id,{'pending_qty' : amend_pend})
									else: 
										amend_pro_qty = re_qty - si_pending_qty 
										si_product_qty += amend_pro_qty
										si_line_obj.write(cr,uid,sol_record.soindent_line_id.id,{'pending_qty' : 0,'product_qty' : si_product_qty})
						else:
							grn_id = self.pool.get('po.grn.line').search(cr, uid, [('so_line_id','=',amend_line.so_line_id.id)])
							if grn_id:
								grn_bro = self.pool.get('po.grn.line').browse(cr, uid, grn_id[0])
								if grn_bro.po_grn_qty <= amend_line.product_qty_amend:
									si_line_record = si_line_obj.browse(cr, uid,sol_record.soindent_line_id.id)
									si_pending_qty = si_line_record.pending_qty
									re_qty = amend_line.product_qty - amend_line.product_qty_amend
									pend_qty = amend_line.product_qty_amend - amend_line.product_qty
									si_pending_qty += re_qty
									si_line_obj.write(cr,uid,sol_record.soindent_line_id.id,{'pending_qty' : si_pending_qty})
									sql = """ update kg_gate_pass_line set qty=(qty + %s),grn_pending_qty=(grn_pending_qty + %s),so_pending_qty=(so_pending_qty + %s) where gate_id=%s and si_line_id= %s """%(pend_qty,pend_qty,pend_qty,so_rec.gp_id.id,si_line_record.id)
									cr.execute(sql)
								else:
									raise osv.except_osv(_('You can not decrease SO Qty'),
										_('Because GRN is already created'))
							else:
								si_line_record = si_line_obj.browse(cr, uid,sol_record.soindent_line_id.id)
								si_pending_qty = si_line_record.pending_qty
								re_qty = amend_line.product_qty - amend_line.product_qty_amend
								si_pending_qty += re_qty
								si_line_obj.write(cr,uid,sol_record.soindent_line_id.id,{'pending_qty' : si_pending_qty})
								sql = """ update kg_gate_pass_line set qty=%s,grn_pending_qty=%s,so_pending_qty=%s where gate_id=%s and si_line_id= %s """%(amend_line.product_qty_amend,amend_line.product_qty_amend,amend_line.product_qty_amend,so_rec.gp_id.id,si_line_record.id)
								cr.execute(sql)
						if amend_line.product_qty != amend_line.product_qty_amend:
							if amend_line.pending_qty == 0 and not amend_line.kg_soindent_lines:
								raise osv.except_osv(_('All Qty has received for this SO !'),
									_('You can not increase SO Qty for product %s')%(amend_line.product_id.name))
					else:
						if so_rec.so_bill == 't':
							raise osv.except_osv(_('You cannot change SO Qty'),
								_('Because Invoice is already created'))
						else:
							pass
					disc_value = (amend_line.product_qty_amend * amend_line.price_unit_amend) * amend_line.kg_discount_per_amend / 100
					so_line_obj.write(cr,uid,so_line_id,{'product_qty': amend_line.product_qty_amend,'brand_id': amend_line.brand_id_amend.id,
															'product_id': amend_line.product_id_amend.id,'uom_id': amend_line.uom_id_amend.id,
															'note': amend_line.note_amend,'taxes_id': [(6, 0, [x.id for x in amend_line.taxes_id_amend])],
															'price_unit' : amend_line.price_unit_amend or 0.0,'pending_qty': amend_line.pending_qty_amend,
															'kg_discount_per_value' : disc_value,'kg_discount': amend_line.discount_amend,
															'kg_discount_per': amend_line.kg_discount_per_amend,'kg_disc_amt_per': amend_line.kg_disc_amt_per_amend,
															'kg_discount_per_value': amend_line.kg_discount_per_value_amend,
															})
					
					cr.execute(""" select tax_id from amendment_so_order_tax where amend_line_id = %s """ %(amend_line.id))
					data = cr.dictfetchall()
					val = [d['tax_id'] for d in data if 'tax_id' in d]
					
					cr.execute(""" delete from service_order_tax where tax_id=%s """ %(so_line_id))
					
					for i in range(len(val)):
						cr.execute(""" INSERT INTO service_order_tax (tax_id,service_order_line_id) VALUES(%s,%s) """ %(so_line_id,val[i]))
					else:
						print "NO SO Line Changs"
					amend_line.write({'line_state': 'done'})
				print "Tax Calculation Methods are Going to Call"
				
				#po_line_obj._amount_line(cr,uid,[po_id],prop=None,arg=None,context=None)
				so_obj._amount_line_tax(cr,uid,sol_record,context=None)
				so_obj._amount_all(cr,uid,[so_id],field_name=None,arg=False,context=None)
			self.write(cr,uid,ids[0],{'state':'approved','app_user_id': uid,'approve_date': dt_time})				
		
		return True		
		
	def advance_creation(self,cr,uid,amend_obj,context=None):
		advance_amt = (amend_obj.so_id.amount_total / 100.00) * amend_obj.advance_amt_amend
		print"advance_amt",advance_amt
		sup_adv_id = self.pool.get('kg.supplier.advance').create(cr,uid,{'supplier_id': amend_obj.partner_id_amend.id,
															'order_category': 'purchase',
															'po_id': amend_obj.so_id.id,
															'advance_amt': advance_amt,
															'order_value': amend_obj.so_id.amount_total,
															'order_no': amend_obj.so_id.name,
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
	
	def onchange_partner_id(self, cr, uid, ids, partner_id_amend,partner_address_amend):
		logger.info('[KG OpenERP] Class: kg_service_order, Method: onchange_partner_id called...')
		partner = self.pool.get('res.partner')
		if not partner_id_amend:
			return {'value': {
				'partner_address': False,
				}}
		supplier_address = partner.address_get(cr, uid, [partner_id_amend], ['default'])
		supplier = partner.browse(cr, uid, partner_id_amend)
		tot_add = (supplier.street or '')+ ' ' + (supplier.street2 or '') + '\n'+(supplier.city.name or '')+ ',' +(supplier.state_id.name or '') + '-' +(supplier.zip or '') + '\nPh:' + (supplier.phone or '')+ '\n' +(supplier.mobile or '')		
		return {'value': {
			'partner_address_amend' : tot_add or False
			}}
	
	def _future_date_check(self,cr,uid,ids,contaxt=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		trans_date = rec.trans_date
		trans_date = str(trans_date)
		trans_date = datetime.strptime(trans_date, '%Y-%m-%d')
		if trans_date > today:
			return False
		return True		
	
	def _check_line_entry(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if not entry.line_ids:
			return False
		else:
			for line in entry.line_ids:
				if line.price_unit == 0 or line.product_qty == 0:
					return False
		return True
	
	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirm':
			if rec.remark:
				self.write(cr, uid, ids, {
							'state': 'reject',
							'rej_user_id': uid,
							'reject_date': time.strftime("%Y-%m-%d %H:%M:%S")})
			else:
				raise osv.except_osv(_('Warning!'),
					_('Enter rejection remark in remark field'))
		return True
	
	def entry_cancel(self,cr,uid,ids,context=None):
		## Don't allow to cancel if this id linked with other transaction or master
		self.write(cr, uid, ids, {'state': 'cancel','can_user_id': uid,
				'cancel_date': time.strftime("%Y-%m-%d %H:%M:%S")})
		return True
	
	def entry_draft(self,cr,uid,ids,context=None):
		# While change state corresponding back updated to be done
		self.write(cr, uid, ids, {'state': 'draft'})
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
	
kg_so_amendment()


class kg_so_amendment_line(osv.osv):
	
	_name = "kg.so.amendment.line"
	_description = "SO Amendment Line"
	
	def _amount_line(self, cr, uid, ids, prop, arg, context=None):
		cur_obj=self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		res = {}
		if context is None:
			context = {}
		for line in self.browse(cr, uid, ids, context=context):
			amt_to_per = (line.discount_amend / (line.product_qty_amend * line.price_unit_amend or 1.0 )) * 100
			print"amt_to_peramt_to_peramt_to_per",amt_to_per
			kg_discount_per = line.kg_discount_per_amend
			tot_discount_per = amt_to_per + kg_discount_per
			price = line.price_unit_amend * (1 - (tot_discount_per or 0.0) / 100.0)
			taxes = tax_obj.compute_all(cr, uid, line.taxes_id_amend, price, line.product_qty_amend, line.product_id_amend, 
								line.amendment_id.partner_id_amend)
			cur = line.amendment_id.pricelist_id.currency_id
			res[line.id] = cur_obj.round(cr, uid, cur, taxes['total_included'])
		return res
	
	_columns = {
		
		## Basic Info
		
		'amendment_id': fields.many2one('kg.so.amendment','SO Amendment',ondelete='cascade',select=True),
		'remark': fields.text('Remark'),
		
		## Module Requirement Fields
		
		'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
		'product_id': fields.many2one('product.product', 'Item Name', required=True,domain="[('state','not in',('reject','cancel')),('purchase_ok','=',True)]"),
		'product_id_amend': fields.many2one('product.product', 'Amend Item Name', required=True,domain="[('state','not in',('reject','cancel')),('purchase_ok','=',True)]"),
		'uom_id': fields.many2one('product.uom', 'UOM', required=True),
		'uom_id_amend': fields.many2one('product.uom', 'Amend UOM', required=True),
		'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
		'product_qty_amend': fields.float('Amend Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
		'total': fields.float('Total'),
		'discount': fields.float('Discount(%)'),
		'discount_amend': fields.float('Amend Discount'),
		'order_id': fields.many2one('kg.service.order', 'Order ID'),
		
		'brand_id':fields.many2one('kg.brand.master','Brand'),
		'brand_id_amend':fields.many2one('kg.brand.master','Amend Brand'),
		
		'si_line_id':fields.many2one('kg.service.indent.line','SI Line', invisible=True),
		'so_line_id':fields.many2one('kg.service.order.line', 'SO Line'),
		
		'kg_discount': fields.float('Discount Amount', digits_compute= dp.get_precision('Discount')),
		'price_unit': fields.float('Unit Price', digits_compute= dp.get_precision('Product Price')),
		
		'pending_qty': fields.float('Pending Qty'),
		'pending_qty_amend': fields.float('Amend Pending Qty',line_state={'cancel':[('readonly', True)]}),
		
		'po_qty':fields.float('PI Qty'),
		'received_qty':fields.float('Received Qty'),
		'cancel_qty':fields.float('Cancel Qty'),
		#'product_uom': fields.many2one('product.uom', 'Product Unit of Measure',required=True,readonly=True),
		
		'note': fields.text('Remarks'),
		'note_amend': fields.text('Amend Remarks'),
		
		'kg_discount_per': fields.float('Discount (%)', digits_compute= dp.get_precision('Discount')),
		'kg_discount_per_value': fields.float('Discount(%)Value', digits_compute= dp.get_precision('Discount')),
		'kg_disc_amt_per': fields.float('Discount(%)', digits_compute= dp.get_precision('Discount')),
		
		'taxes_id': fields.many2many('account.tax', 'service_order_taxe', 'amend_line_id', 'tax_id','Taxes',readonly=True),
		'line_state': fields.selection([('draft', 'Draft'),('cancel', 'Cancel'),('done', 'Done')], 'Status'),
		'line_bill': fields.boolean('PO Bill'),
		# Amendment Fields:
		'kg_discount_amend': fields.float('Amend Discount Amount', digits_compute= dp.get_precision('Discount')),
		'price_unit_amend': fields.float('Amend Price', digits_compute= dp.get_precision('Product Price')),
		
		'po_qty_amend':fields.float('Amend PI Qty'),
		'kg_discount_per_amend': fields.float('Amend Discount', digits_compute= dp.get_precision('Discount')),
		'kg_discount_per_value_amend': fields.float('Amend Discount Value', digits_compute= dp.get_precision('Discount')),
		'kg_disc_amt_per_amend': fields.float('Amend Discount', digits_compute= dp.get_precision('Discount')),
		
		'taxes_id_amend': fields.many2many('account.tax', 'amendment_so_order_tax', 'amend_line_id', 'tax_id','Amend Taxes'),
		'cancel_flag':fields.boolean('Flag'),
		
		'qty_flag': fields.boolean('QTY'),
		'kg_soindent_lines':fields.many2many('kg.service.indent.line','kg_soindent_so_line' , 'so_order_id', 'siline_id','SOIndent Lines',
				domain="[('service_id.state','=','approved'), '&', ('pending_qty','>','0'),'&',('product_id','=',product_id)]"),
		
	}	
	
kg_so_amendment_line()
