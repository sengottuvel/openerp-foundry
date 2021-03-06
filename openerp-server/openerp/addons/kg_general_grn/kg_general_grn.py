import math
import re
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
import netsvc
import datetime
import calendar
import urllib
import urllib2
import logging
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
today = datetime.now()

class kg_general_grn(osv.osv):
	
	_name = "kg.general.grn"
	_description = "General GRN"
	_order = "grn_date desc,name desc"
	
	def _amount_line_tax(self, cr, uid, line, context=None):
		grn_qty = val = 0.0
		if line.grn_qty == 0:
			grn_qty = 1
		else:
			grn_qty = line.grn_qty
		new_amt_to_per = line.kg_discount or 0.0 / grn_qty
		amt_to_per = (line.kg_discount / (line.grn_qty * line.price_unit or 1.0 )) * 100
		kg_discount_per = line.kg_discount_per
		tot_discount_per = amt_to_per + kg_discount_per
		for c in self.pool.get('account.tax').compute_all(cr, uid, line.grn_tax_ids,
			line.price_unit * (1-(tot_discount_per or 0.0)/100.0), line.grn_qty, line.product_id,
			 line.grn_id.supplier_id)['taxes']:
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
			po_charges=order.value1 + order.value2
			if order.expense_line_id:
				for item in order.expense_line_id:
					other_charges_amt += item.expense_amt
			else:
				other_charges_amt = 0
			for line in order.grn_line:
				per_to_amt = (line.grn_qty * line.price_unit) * line.kg_discount_per / 100.00
				tot_discount = line.kg_discount + per_to_amt
				val1 += line.price_subtotal
				val += self._amount_line_tax(cr, uid, line, context=context)
				val3 += tot_discount
			res[order.id]['other_charge']=(round(other_charges_amt,0))
			res[order.id]['amount_tax']=(round(val,0))
			res[order.id]['amount_untaxed']=(round(val1,0))
			res[order.id]['amount_total']=(round(val + val1 + res[order.id]['other_charge'],0))
			res[order.id]['discount']=(round(val3,0))
		return res
	
	def _get_journal(self, cr, uid, context=None):
		journal_obj = self.pool.get('account.journal')
		res = journal_obj.search(cr, uid, [('type','=','sale')], limit=1)
		return res and res[0] or False
	
	def _get_currency(self, cr, uid, context=None):
		res = False
		journal_id = self._get_journal(cr, uid, context=context)
		if journal_id:
			journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
			res = journal.currency and journal.currency.id or journal.company_id.currency_id.id
		return res
	
	def _get_order(self, cr, uid, ids, context=None):
		result = {}
		for line in self.pool.get('kg.general.grn.line').browse(cr, uid, ids, context=context):
			result[line.grn_id.id] = True
		return result.keys()
	
	def button_dummy(self, cr, uid, ids, context=None):
		return True
	
	_columns = {
		
		## Basic Info
		
		'name': fields.char('GRN NO',readonly=True),
		'grn_date':fields.date('GRN Date',required=True,readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'state': fields.selection([('draft', 'Draft'), ('confirmed', 'WFA'), ('done', 'Approved'), ('cancel', 'Cancelled'),('inv','Invoiced'),('reject','Rejected')], 'Status',readonly=True),
		'remark':fields.text('Remarks'),
		'notes':fields.text('Notes'),
		'can_remark':fields.text('Cancel Remarks'),
		'reject_remark':fields.text('Reject Remarks'),
		
		## Module Requirement Info
		
		'supplier_id':fields.many2one('res.partner','Supplier',domain=[('supplier','=',True)],readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'dc_no': fields.char('DC NO', required=True,readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'dc_date':fields.date('DC Date',required=True, readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'bill': fields.selection([
			('applicable', 'Applicable'),
			('not_applicable', 'Not Applicable')], 'Bill Type',required=True,readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'other_charge': fields.float('Other Charges',readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'amount_total': fields.float('Total Amount',readonly=True),
		'sub_total': fields.float('Line Total',readonly=True),
		'expiry_flag':fields.boolean('Expiry Flag'),
		'dep_name': fields.many2one('kg.depmaster','Department',readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'inward_type': fields.many2one('kg.inwardmaster', 'Inward Type',readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'other_charge': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Other Charges(+)',
			 multi="sums", help="The amount without tax", track_visibility='always'),
		'discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Discount(-)',
			store={
				'kg.general.grn': (lambda self, cr, uid, ids, c={}: ids, ['grn_line'], 10),
				'kg.general.grn.line': (_get_order, ['price_unit', 'grn_tax_ids', 'kg_discount', 'grn_qty'], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
			store={
				'kg.general.grn': (lambda self, cr, uid, ids, c={}: ids, ['grn_line'], 10),
				'kg.general.grn.line': (_get_order, ['price_unit', 'grn_tax_ids', 'kg_discount', 'grn_qty'], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
			store={
				'kg.general.grn': (lambda self, cr, uid, ids, c={}: ids, ['grn_line'], 10),
				'kg.general.grn.line': (_get_order, ['price_unit', 'grn_tax_ids', 'kg_discount', 'grn_qty'], 10),
			}, multi="sums", help="The tax amount"),
		'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total',
			store=True,multi="sums",help="The total amount"),
		'pricelist_id':fields.many2one('product.pricelist', 'Pricelist'),
		'currency_id': fields.many2one('res.currency', 'Currency', readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'po_expenses_type1': fields.selection([('freight','Freight Charges'),('others','Others')], 'Expenses Type1',
										readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'po_expenses_type2': fields.selection([('freight','Freight Charges'),('others','Others')], 'Expenses Type2',
								readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'value1':fields.float('Value1', readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'value2':fields.float('Value2', readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'type':fields.selection([('out','out'),('in','in')], 'Type'),
		'invoice_flag':fields.boolean('Invoice Flag'),
		'po_id':fields.many2one('purchase.order', 'PO NO',
					domain="[('state','=','approved'), '&', ('order_line.pending_qty','>','0'), '&', ('grn_flag','=',False), '&', ('partner_id','=',supplier_id), '&', ('order_line.line_state','!=','cancel')]"),
		'po_date':fields.date('PO Date',readonly=True),
		'order_no': fields.char('Order NO'),
		'order_date':fields.char('Order Date'),
		'payment_type': fields.selection([('cash', 'Cash'), ('credit', 'Credit')], 'Payment Type',readonly=True,states={'confirmed':[('readonly',False)],'draft': [('readonly', False)]}),
		'grn_dc': fields.selection([('only_grn','Only grn')], 'GRN Type',required=True),
		'sup_invoice_no':fields.char('Supplier Invoice No',size=200, readonly=False, states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
		'sup_invoice_date':fields.date('Supplier Invoice Date', readonly=False, states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
		'vehicle_details':fields.char('Vehicle Details', readonly=False, states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
		'insp_ref_no':fields.char('Insp.Ref.No.', readonly=False, states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
		'location_dest_id': fields.many2one('stock.location','Location',domain="[('location_type','=','main')]"),
		'location_dest_code': fields.char('Location Code'),
		'division': fields.selection([('ppd','PPD'),('ipd','IPD'),('foundry','Foundry')],'Division'),
		'product_id': fields.related('grn_line','product_id', type='many2one', relation='product.product', string='Product'),
		
		## Child Tables Declaration
		
		'grn_line':fields.one2many('kg.general.grn.line','grn_id','Line Entry',readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'expense_line_id': fields.one2many('kg.gen.grn.expense.track','expense_id','Expense Track',readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		
		## Entry Info
		
		'active': fields.boolean('Active'),
		'company_id':fields.many2one('res.company','Company',readonly=True),
		'user_id':fields.many2one('res.users','Created By',readonly=True),
		'creation_date':fields.datetime('Created Date',required=True,readonly=True),
		'confirmed_by' : fields.many2one('res.users', 'Confirmed By',readonly=True),
		'approved_by' : fields.many2one('res.users', 'Approved By',readonly=True),
		'confirmed_date' : fields.datetime('Confirmed date',readonly=True),
		'approved_date' : fields.datetime('Approved date',readonly=True),
		'reject_date': fields.datetime('Rejected Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date' : fields.datetime('Last Updated Date',readonly=True),
		'update_user_id' : fields.many2one('res.users','Last Updated By',readonly=True),
		
	}
	
	def onchange_user_id(self, cr, uid, ids, location_dest_code, context=None):
		value = {'location_dest_id': ''}
		if location_dest_code:
			loc_ids = self.pool.get('stock.location').search(cr, uid,[('code','=',location_dest_code)])
			if loc_ids:
				loc_rec = self.pool.get('stock.location').browse(cr, uid, loc_ids[0])
				value = {'location_dest_id':loc_rec.id}
		return {'value': value}
	
	def _check_line_validations(self, cr, uid, ids, context=None):
		grn = self.browse(cr, uid, ids[0])
		if not grn.grn_line:
			raise osv.except_osv(_('Warning!'),_('Without product details should not be proceed further !!'))
		for line in grn.grn_line:
			if line.inward_type.id == False:
				raise osv.except_osv(_('Warning!'),_('Kindly Give Inward Type for %s !!' %(line.product_id.name)))
			if line.uom_id.id == line.product_id.uom_po_id.id or line.uom_id.id == line.product_id.uom_id.id:
				pass
			else:
				raise osv.except_osv(_('UOM Mismatching Error !'),
					_('You choosed wrong UOM and you can choose either %s or %s for %s !!') % (line.product_id.uom_id.name,line.product_id.uom_po_id.name,line.product_id.name))
			if line.grn_qty <= 0:
				raise osv.except_osv(_('Warning !'),_('%s Qty should be greater than zero !!'%(line.product_id.name)))
			
			# Expiry date validation starts
			if line.product_id.flag_expiry_alert == True:
				if not line.exp_batch_id:
					raise osv.except_osv(_('Warning!'),_('System should not be accept without Expiry Date for (%s) !!'%(line.product_id.name)))
			if line.exp_batch_id:
				for item in line.exp_batch_id:
					if not item.exp_date:
						raise osv.except_osv(_('Warning!'),_('%s Configure expiry date for this S/N %s '%(line.product_id.name,item.batch_no)))
					else:
						if grn.grn_date > item.exp_date:
							raise osv.except_osv(_('Warning !'),
								_('Change the product expiry date to greater than GRN date for Product %s !!' %(line.product_id.name)))
					sql = """ 
							select exp.batch_no from kg_exp_batch exp
							left join kg_general_grn_line line on(line.id=exp.grn_line_id)
							where exp.batch_no = '%s' and exp.grn_line_id = %s and line.product_id=%s and line.brand_id = %s and line.moc_id = %s """%(item.batch_no,line.id,line.product_id.id,line.brand_id.id,line.moc_id.id)
					cr.execute(sql)		
					data = cr.dictfetchall()
					if data:
						if len(data) > 1:
							raise osv.except_osv(_('Warning!'),_('%s S/N must be unique per Item') %(line.product_id.name))
				if line.length <= 0 or line.breadth <= 0:
					line_length = 1
					line_breadth = 1
				else:
					line_length = line.length
					line_breadth = line.breadth
				exp_grn_qty = line.grn_qty
				if line.uom_conversation_factor == 'one_dimension':
					exp_grn_qty = sum(exp_line.product_qty * line_length * line_breadth for exp_line in line.exp_batch_id)
				elif line.uom_conversation_factor == 'two_dimension':
					exp_grn_qty = sum(exp_line.product_qty for exp_line in line.exp_batch_id)
				
				if exp_grn_qty > line.grn_qty:
					raise osv.except_osv(_('Warning!'),_('Qty specified in S/N Details should not greater than Received Qty for %s !!'%(line.product_id.name)))
				elif exp_grn_qty < line.grn_qty:
					raise osv.except_osv(_('Warning!'),_('Qty specified in S/N Details should not less than Received Qty for %s !!'%(line.product_id.name)))
			
			# Expiry date validation ends
			
			if line.product_id.uom_conversation_factor == 'two_dimension' and line.uom_category == 'length' and line.length <= 0.00 and line.breadth <= 0.00:
				raise osv.except_osv(_('Warning!'),
					_('%s %s %s You cannot proceed without length and breadth')%(line.product_id.name,line.brand_id.name,line.moc_id.name))
			if not line.product_id.po_uom_coeff or line.product_id.po_uom_coeff <= 0:
				raise osv.except_osv(_('Warning!'),_('%s Kindly configure PO coeff in Product Master !!'%(line.product_id.name)))
		
		tot_price = sum(line.price_unit for line in grn.grn_line)
		if tot_price > 500:
			raise osv.except_osv(_('Warning !'),_('GRN Price should be less than 500rs!!'))
		return True
	
	_constraints = [
		
		(_check_line_validations, 'You can not save an GRN with 0 received qty !',['']),
		
		]
	
	def write(self, cr, uid, ids, vals, context=None):		
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_general_grn, self).write(cr, uid, ids, vals, context)	
	
	def entry_confirm(self, cr, uid, ids,context=None):
		grn_entry = self.browse(cr, uid, ids[0])
		if grn_entry.state == 'draft':
			if not grn_entry.name or grn_entry.name == False:
				if grn_entry.location_dest_id.code == 'FOU_Main':
					seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.gen.grn.fou')])
				elif grn_entry.location_dest_id.code == 'MS_Main':
					seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.gen.grn.ms')])
				elif grn_entry.location_dest_id.code == 'GEN_Main':
					seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.gen.grn.gen')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,grn_entry.creation_date))
				seq_name = cr.fetchone();
				self.write(cr,uid,ids[0],{'name':seq_name[0]})
			line_tot = 0
			for line in grn_entry.grn_line:
				product_tax_amt = self._amount_line_tax(cr, uid, line, context=context)
				cr.execute("""update kg_general_grn_line set product_tax_amt = %s where id = %s"""%(product_tax_amt,line.id))
				grn_price = line.grn_qty * line.price_unit
				line.write({'state':'confirmed','line_total':grn_price})
				line_tot += grn_price
			tot_amt = line_tot + grn_entry.other_charge
			self.write(cr,uid,ids[0],{'sub_total': line_tot,
									  'amount_total': tot_amt,
									  'state': 'confirmed',
									  'confirmed_by': uid,
									  'confirmed_date': time.strftime('%Y-%m-%d %H:%M:%S')
									  })
		
		return True
	
	def entry_approve(self, cr, uid, ids,context=None):
		grn_entry = self.browse(cr, uid, ids[0])
		if grn_entry.state == 'confirmed':
			gate_obj = self.pool.get('kg.gate.pass')
			gp_line_obj = self.pool.get('kg.gate.pass.line')
			user_id = self.pool.get('res.users').browse(cr, uid, uid)
			lot_obj = self.pool.get('stock.production.lot')
			stock_move_obj=self.pool.get('stock.move')
			dep_obj = self.pool.get('kg.depmaster')			
			pi_obj = self.pool.get('kg.purchase.invoice')
			pi_gen_grn_obj = self.pool.get('kg.gengrn.purchase.invoice.line')
			line_tot = 0	
			
			for line in grn_entry.grn_line:
				# Depreciation creation process start
				if line.product_id.is_depreciation == True:
					depre_obj = self.pool.get('kg.depreciation')
					depre_id = depre_obj.create(cr,uid,{'product_id': line.product_id.id,
														'grn_no': grn_entry.name,
														'grn_date': grn_entry.grn_date,
														'qty': line.grn_qty,
														'entry_mode': 'auto',
														'each_val_actual': line.price_unit,
														'tot_val_actual': line.price_unit * line.grn_qty,
														'each_val_crnt': line.price_unit,
														'tot_val_crnt': line.price_unit * line.grn_qty,
														})
				# Depreciation creation process end
				
				# This code will create General GRN to Stock Move
				
				if line.length == 0.00:
					line_length = 1
				else:
					line_length = line.length
				if line.breadth == 0.00:
					line_breadth = 1
				else:
					line_breadth = line.breadth
				if line.product_id.uom_id == line.uom_id:
					store_uom_stk_qty = line.grn_qty * line_length * line_breadth				
					po_uom_stk_qty = line.grn_qty * line_length * line_breadth / line.product_id.po_uom_coeff
				elif line.product_id.uom_id != line.uom_id:
					po_uom_stk_qty = line.grn_qty * line_length * line_breadth				
					store_uom_stk_qty = line.grn_qty * line_length * line_breadth * line.product_id.po_uom_coeff
				else:
					po_uom_stk_qty = line.grn_qty
					store_uom_stk_qty = line.grn_qty
				
				stock_move_obj.create(cr,uid,
					{
					'general_grn_id': line.id,
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
					'price_unit': line.price_unit or 0.0,
					'origin': 'General GRN',
					'stock_rate': line.price_unit or 0.0,
					'uom_conversation_factor': line.uom_conversation_factor,
					'trans_date': grn_entry.grn_date,
					
					})	
					
				line.write({'state':'done'})
				
				# This code will create Production lot				
				
				if line.exp_batch_id:
					for exp in line.exp_batch_id:
						if line.product_id.uom_id == line.uom_id:
							store_uom_stk_qty = exp.product_qty * line_length * line_breadth				
							po_uom_stk_qty = exp.product_qty * line_length * line_breadth / line.product_id.po_uom_coeff
						elif line.product_id.uom_id != line.uom_id:
							po_uom_stk_qty = exp.product_qty * line_length * line_breadth				
							store_uom_stk_qty = exp.product_qty * line_length * line_breadth * line.product_id.po_uom_coeff
						else:
							po_uom_stk_qty = exp.product_qty
							store_uom_stk_qty = exp.product_qty
						
						lot_id = lot_obj.create(cr,uid,
							
							{
							'grn_no':line.grn_id.name,
							'product_id':line.product_id.id,
							'brand_id':line.brand_id.id,
							'moc_id':line.moc_id.id,
							'location_id':line.location_dest_id.id,
							'location_code': line.location_dest_id.code,
							'product_uom':line.product_id.uom_id.id,
							'po_product_qty':po_uom_stk_qty,
							'product_qty':store_uom_stk_qty,
							'pending_qty':po_uom_stk_qty,
							'store_pending_qty':store_uom_stk_qty,
							'issue_qty':0.00,
							'batch_no':line.grn_id.name,
							'price_unit':line.price_unit or 0.0,
							'po_uom':line.product_id.uom_po_id.id,
							'grn_type':'material',
							'reserved_qty': 0.00,
							'expiry_date': exp.exp_date,
							'trans_date': grn_entry.grn_date,
							
						})
				else:
					
					lot_id = lot_obj.create(cr,uid,
						{
						
						'grn_no':line.grn_id.name,
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
						'batch_no':line.grn_id.name,
						'price_unit':line.price_unit or 0.0,
						'grn_type':'material',
						'reserved_qty': 0.00,
						'trans_date': grn_entry.grn_date,
						
					})
				
				grn_price = line.grn_qty * line.price_unit
				line.write({'line_total':grn_price})
				line_tot += grn_price
				total_price = line.price_unit * line.grn_qty
				product_tax_amt = self._amount_line_tax(cr, uid, line, context=context)
				cr.execute("""update kg_general_grn_line set product_tax_amt = %s where id = %s"""%(product_tax_amt,line.id))
			self.write(cr,uid,ids[0],{'state':'done','approved_by':uid,'approved_date':time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
	def entry_cancel(self, cr, uid, ids, context=None):
		grn = self.browse(cr, uid, ids[0])
		if grn.state == 'done':
			if not grn.can_remark:
				raise osv.except_osv(_('Warning !'),_('Enter Remarks for GRN Cancel !!'))
			else:
				self.write(cr, uid, ids[0], {'state':'cancel','cancel_user_id': uid,'cancel_date': time.strftime("%Y-%m-%d %H:%M:%S")})
			for line in grn.grn_line:
				line.write({'state':'cancel'})
		return True
	
	def entry_reject(self, cr, uid, ids, context=None):
		grn = self.browse(cr, uid, ids[0])
		if grn.state == 'confirmed':
			if not grn.reject_remark:
				raise osv.except_osv(_('Warning !'),_('Enter Remarks for GRN Rejection !!'))
			else:
				self.write(cr, uid, ids[0], {'state':'draft','rej_user_id': uid,'reject_date': time.strftime("%Y-%m-%d %H:%M:%S")})
		return True
	
	_defaults = {
		
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'user_id': lambda obj, cr, uid, context: uid,
		'bill': 'not_applicable',
		'state': 'draft',
		'grn_date': lambda * a: time.strftime('%Y-%m-%d'),
		'dc_date': lambda * a: time.strftime('%Y-%m-%d'),
		'name': '',
		'type': 'in',
		'company_id' : lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.general.grn', context=c),
		'active': True,
		'grn_dc': 'only_grn',
		
	}
	
	def _get_invoice_type(self, pick):
		src_usage = dest_usage = None
		inv_type = None
		if pick.state == 'done':
			src_usage = 'supplier'
			if pick.type == 'in' and src_usage == 'supplier':
				inv_type = 'in_invoice'
			elif pick.type == 'in' and src_usage == 'customer':
				inv_type = 'out_refund'
			else:
				inv_type = 'out_invoice'
		return inv_type
	
	def action_invoice_create(self, cr, uid, ids, journal_id=False,
			group=False, type='out_invoice', context=None):
		if context is None:
			context = {}
		
		invoice_obj = self.pool.get('account.invoice')
		invoice_line_obj = self.pool.get('account.invoice.line')
		partner_obj = self.pool.get('res.partner')
		line_obj = self.pool.get('kg.general.grn.line')
		picking_obj = self.pool.get('stock.picking')
		invoices_group = {}
		res = {}
		inv_type = type
		for picking in self.browse(cr, uid, ids, context=context):
			partner = picking.supplier_id
			if isinstance(partner, int):
				partner = partner_obj.browse(cr, uid, [partner], context=context)[0]
			if not partner:
				raise osv.except_osv(_('Error, no partner!'),_('Please put a partner on the GRN if you want to generate invoice.'))
			if not inv_type:
				inv_type = self._get_invoice_type(picking)
			if group and partner.id in invoices_group:
				invoice_id = invoices_group[partner.id]
				invoice = invoice_obj.browse(cr, uid, invoice_id)
				invoice_vals_group = self._prepare_invoice_group(cr, uid, picking, partner, invoice, context=context)
				invoice_obj.write(cr, uid, [invoice_id], invoice_vals_group, context=context)
			else:
				invoice_vals = self._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
				invoice_id = invoice_obj.create(cr, uid, invoice_vals, context=context)
				invoices_group[partner.id] = invoice_id
			res[picking.id] = invoice_id

			for move_id in picking.grn_line:
				move_line = line_obj.browse(cr, uid, move_id.id)
				if move_line.state == 'cancel':
					continue
				vals = self._prepare_invoice_line(cr, uid, group, picking, move_line,
								invoice_id, invoice_vals, context=context)
				if vals:
					invoice_line_id = invoice_line_obj.create(cr, uid, vals, context=context)
					#picking_obj._invoice_line_hook(cr, uid, move_line, invoice_line_id)

			invoice_obj.button_compute(cr, uid, [invoice_id], context=context,
					set_total=(inv_type in ('in_invoice', 'in_refund')))
			self.write(cr, uid, [picking.id], {
				'state': 'inv',
				}, context=context)
			#picking_obj._invoice_hook(cr, uid, picking, invoice_id)
		self.write(cr, uid, res.keys(), {
			'state': 'inv',
			'invoice_flag': 'False'
			}, context=context)
		return res
	
	def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):

		val1 = picking.value1 or 0.0
		val2 = picking.value2 or 0.0
		other_ch1 = picking.po_expenses_type1 or False
		other_ch2 = picking.po_expenses_type2 or False
		sub = picking.amount_untaxed
		dis = picking.discount
		tax = picking.amount_tax
		total = picking.amount_total
		other_charge = val1 + val2
		if isinstance(partner, int):
			partner = self.pool.get('res.partner').browse(cr, uid, partner, context=context)
		if inv_type in ('out_invoice', 'out_refund'):
			account_id = 13
			payment_term = partner.property_payment_term.id or False
		else:
			account_id = 13
			payment_term = partner.property_supplier_payment_term.id or False
		comment = 'Invoice'
		
		invoice_vals = {
			'name': self.pool.get('ir.sequence').get(cr, uid, 'account.invoice'),
			'origin': (picking.name or ''),
			'type': inv_type,
			'partner_id': partner.id,
			'comment': comment,
			'payment_term': payment_term,
			'fiscal_position': partner.property_account_position.id,
			'date_invoice': context.get('date_inv', False),
			'company_id': picking.company_id.id,
			'user_id': uid,
			'general_grn_id':picking.id,
			'po_expenses_type1':other_ch1,
			'po_expenses_type2':other_ch2,
			'value1':val1,
			'value2':val2,
			'state':'proforma',
			'supplier_invoice_number': context.get('sup_inv_no', False),
			'sup_inv_date': context.get('sup_inv_date', False),
			'bill_type':'cash',
			'grn_date':picking.grn_date,
			'amount_untaxed':picking.amount_untaxed,
			'amount_tax':picking.amount_tax,
			'tot_discount':picking.discount,
			'other_charge':other_charge
			
		}
		
		if journal_id:
			invoice_vals['journal_id'] = journal_id
		return invoice_vals
	
	def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id,
		invoice_vals, context=None):
		if invoice_vals['fiscal_position']:
			fp_obj = self.pool.get('account.fiscal.position')
			fiscal_position = fp_obj.browse(cr, uid, invoice_vals['fiscal_position'], context=context)
			account_id = fp_obj.map_account(cr, uid, fiscal_position, account_id)
		# set UoS if it's a sale and the picking doesn't have one
		uos_id = move_line.uom_id.id
		return {
			'name': picking.name,
			'origin': picking.name,
			'invoice_id': invoice_id,
			'uos_id': uos_id,
			'product_id': move_line.product_id.id,
			'brand_id': move_line.brand_id.id,
			'price_unit': move_line.price_unit,
			'quantity': move_line.grn_qty or 0.00,
			'invoice_line_tax_id': [(6, 0, [x.id for x in move_line.grn_tax_ids])],
			'discount':move_line.kg_discount_per,
			'kg_disc_amt':move_line.kg_discount,
		}
	
	def unlink(self, cr, uid, ids, context=None):
		unlink_ids = []
		grn_rec = self.browse(cr, uid, ids[0])
		if grn_rec.state != 'draft':
			raise osv.except_osv(_('Delete access denied !'), _('Unable to delete. Draft entry only you can delete !!'))
		else:
			unlink_ids.append(grn_rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
	def expiry_alert(self, cr, uid, ids, context=None):
		now = time.strftime("%Y-%m-%d")
		cr.execute(""" select id,grn_line_id,product_qty,exp_date,batch_no from kg_exp_batch """)
		data = cr.dictfetchall()
		value_data = []
		rep=[]
		new_list = []
		for item in data:
			now = time.strftime("%Y-%m-%d")
			# Product Name
			grn_line_rec = self.pool.get('kg.general.grn.line').browse(cr, uid, item['grn_line_id'])
			product_name = grn_line_rec.product_id.name_template
			grn_no = grn_line_rec.grn_id.name
			exp_date = item['exp_date']
			exp_day = datetime.strptime(exp_date, "%Y-%m-%d")
			today = datetime.strptime(now, "%Y-%m-%d")
			pre_day = exp_day - timedelta(hours=24)
			if pre_day == today:
				rep=[product_name,grn_no,item['exp_date'],item['batch_no']]
				value_data.append(rep)
		return value_data
	
kg_general_grn()


class kg_general_grn_line(osv.osv):

	_name = "kg.general.grn.line"
	_description = "General GRN Provision Line"

	def _amount_line(self, cr, uid, ids, prop, arg, context=None):
		cur_obj=self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		res = {}
		if context is None:
			context = {}
		for line in self.browse(cr, uid, ids, context=context):
			# Qty Calculation
			if line.price_type == 'per_kg':								
				if line.product_id.po_uom_in_kgs > 0:
					qty = line.grn_qty * line.product_id.po_uom_in_kgs
				else:
					qty = line.grn_qty
			else:
				qty = line.grn_qty
			# Price Calculation
			price_amt = 0
			if line.price_type == 'per_kg':
				if line.product_id.po_uom_in_kgs > 0:
					price_amt = line.grn_qty / line.product_id.po_uom_in_kgs * line.price_unit
			else:
				price_amt = qty * line.price_unit
			amt_to_per = (line.kg_discount / (qty * line.price_unit or 1.0 )) * 100
			kg_discount_per = line.kg_discount_per
			tot_discount_per = amt_to_per + kg_discount_per
			price = line.price_unit * (1 - (tot_discount_per or 0.0) / 100.0)
			taxes = tax_obj.compute_all(cr, uid, line.grn_tax_ids, price, qty, line.product_id, line.grn_id.supplier_id)
			cur = line.grn_id.supplier_id.property_product_pricelist_purchase.currency_id
			res[line.id] = (round(taxes['total'],0))
		return res
	
	_columns = {
		
		## Basic Info
		
		'grn_id':fields.many2one('kg.general.grn','GRN Entry'),
		
		## Module Requirement Fields
		
		'product_id': fields.many2one('product.product','Item Name',required=True,readonly=False, states={'done':[('readonly',True)],'calcel':[('readonly',True)]}, domain="[('state','=','approved'),('purchase_ok','=',True)]"),
		'supplier_id':fields.many2one('res.partner','Supplier',domain=[('supplier','=',True)]),
		'uom_id': fields.many2one('product.uom','Store UOM',readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'grn_qty': fields.float('Received Qty',required=True,readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'recvd_qty': fields.float('Received Qty'),
		'reject_qty': fields.float('Rejected Qty'),
		'price_unit': fields.float('Unit Price',readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'price_subtotal': fields.function(_amount_line, string='Line Total', digits_compute= dp.get_precision('Account'),store=True),
		'state': fields.selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),('done', 'Done'), ('cancel', 'Cancelled')], 'Status',readonly=True),
		'cancel_remark': fields.text('Cancel Remarks'),
		'kg_discount_per': fields.float('Discount (%)', digits_compute= dp.get_precision('Discount')),
		'kg_discount': fields.float('Discount Amount'),
		'grn_tax_ids': fields.many2many('account.tax', 'po_gen_grn_tax', 'order_id', 'taxes_id', 'Taxes'),
		'brand_id':fields.many2one('kg.brand.master','Brand',domain="[('product_ids','in',(product_id)),('state','in',('draft','confirmed','approved'))]"),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'moc_id_temp': fields.many2one('ch.brandmoc.rate.details','MOC',domain="[('brand_id','=',brand_id),('header_id.product_id','=',product_id),('header_id.state','in',('draft','confirmed','approved'))]"),
		'inward_type': fields.many2one('kg.inwardmaster', 'Inward Type'),
		'product_tax_amt': fields.float('Tax Amount'),
		'price_type': fields.selection([('po_uom','PO UOM'),('per_kg','Per Kg')],'Price Type'),
		'weight': fields.float('Weight',readonly=True),
		'location_dest_id': fields.many2one('stock.location','Location',domain="[('location_type','=','main')]"),
		'length': fields.float('Length',digits=(16,4)),
		'breadth': fields.float('Breadth',digits=(16,4)),
		'uom_conversation_factor': fields.selection([('one_dimension','One Dimension'),('two_dimension','Two Dimension')],'UOM Conversation Factor',required=True,readonly=True),
		'uom_category': fields.selection([('length','Length'),('other','Others')],'UOM Category',required=True),
		
		## Child Tables Declaration
		
		'exp_batch_id':fields.one2many('kg.exp.batch','grn_line_id','Exp Batch No',readonly=True,states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		
	}
	
	_defaults = {
		
		'state': 'draft',
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
	
	def default_get(self, cr, uid, fields, context=None):
		if not context.get('supplier_id'):
			pass
		else:
			if not context['supplier_id']:
				raise osv.except_osv(_('Warning!'),_('Select Supplier !!'))
		return context
	
	def onchange_product_id(self, cr, uid, ids, product_id, uom_id, supplier_id):
		value = {'uom_conversation_factor':'','uom_category':'','grn_tax_ids':'','brand_id':'','moc_id_temp':'','price_type':''}
		
		if product_id and uom_id:
			prod_rec = self.pool.get('product.product').browse(cr,uid,product_id)
			uom_rec = self.pool.get('product.uom').browse(cr, uid, uom_id)
			tax = []
			if prod_rec.hsn_no.id and supplier_id:
				partner_rec = self.pool.get('res.partner').browse(cr,uid,supplier_id)
				if partner_rec.state_id.id:
					if partner_rec.state_id.code == 'TN':
						if prod_rec.hsn_no.cgst_id.id and prod_rec.hsn_no.sgst_id.id:
							tax = [prod_rec.hsn_no.cgst_id.id,prod_rec.hsn_no.sgst_id.id]
					elif partner_rec.state_id.code != 'TN':
						if prod_rec.hsn_no.igst_id.id:
							tax = [prod_rec.hsn_no.igst_id.id] 
				elif not partner_rec.state_id.id:
					tax = []
				else:
					pass
			value = {'uom_conversation_factor': prod_rec.uom_conversation_factor,'uom_category':uom_rec.uom_category,'price_type':prod_rec.price_type,'grn_tax_ids':[(6, 0, tax)]}
		elif product_id:
			prod_rec = self.pool.get('product.product').browse(cr,uid,product_id)
			tax = []
			if prod_rec.hsn_no.id and supplier_id:
				partner_rec = self.pool.get('res.partner').browse(cr,uid,supplier_id)
				if partner_rec.state_id.id:
					if partner_rec.state_id.code == 'TN':
						if prod_rec.hsn_no.cgst_id.id and prod_rec.hsn_no.sgst_id.id:
							tax = [prod_rec.hsn_no.cgst_id.id,prod_rec.hsn_no.sgst_id.id]
					elif partner_rec.state_id.code != 'TN':
						if prod_rec.hsn_no.igst_id.id:
							tax = [prod_rec.hsn_no.igst_id.id] 
				elif not partner_rec.state_id.id:
					tax = []
				else:
					pass
			value = {'uom_conversation_factor': prod_rec.uom_conversation_factor,'uom_category':'','price_type':prod_rec.price_type,'brand_id':'','moc_id_temp':'','grn_tax_ids':[(6, 0, tax)]}
		return {'value': value}
	
	def onchange_weight(self, cr, uid, ids, grn_qty,length,breadth,uom_conversation_factor,product_id,uom_id):
		value = {'weight':''}
		weight = 0
		if grn_qty and length and breadth and uom_conversation_factor and product_id and uom_id:
			prod_rec = self.pool.get('product.product').browse(cr,uid,product_id)
			if uom_id == prod_rec.uom_po_id.id:
				if uom_conversation_factor == 'two_dimension':
					if prod_rec.po_uom_in_kgs > 0:
						weight = grn_qty * prod_rec.po_uom_in_kgs * length * breadth
			elif uom_id == prod_rec.uom_id.id:
				if uom_conversation_factor == 'two_dimension':
					if prod_rec.po_uom_in_kgs > 0:
						weight = grn_qty / prod_rec.po_uom_in_kgs / length / breadth
			value = {'weight': weight}
		return {'value': value}
	
	def onchange_moc(self, cr, uid, ids, moc_id_temp):
		value = {'moc_id':''}
		if moc_id_temp:
			rate_rec = self.pool.get('ch.brandmoc.rate.details').browse(cr,uid,moc_id_temp)
			value = {'moc_id': rate_rec.moc_id.id}
		return {'value': value}
	
	def onchange_uom_id(self, cr, uid, ids, product_id,uom_id, context=None):
		value = {'price_unit': '','uom_category':'','uom_conversation_factor':'','length':0,'bradth':0,'grn_qty':0}
		if product_id and uom_id:
			pro_rec = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			uom_rec = self.pool.get('product.uom').browse(cr, uid, uom_id)
			if uom_id == pro_rec.uom_id.id or uom_id == pro_rec.uom_po_id.id:
				pass
			else:
				raise osv.except_osv(_('UOM Mismatching Error !'),
					_('You choosed wrong UOM and you can choose either %s or %s for %s !!') % (pro_rec.uom_id.name,pro_rec.uom_po_id.name,pro_rec.name))
			value = {'price_unit':pro_rec.standard_price,'uom_category':uom_rec.uom_category,'uom_conversation_factor': pro_rec.uom_conversation_factor,'length':0,'breadth':0,'grn_qty':0}
		return {'value': value}
	
	def create(self, cr, uid, vals,context=None):
		if vals.has_key('product_id') and vals['product_id']:
			product_rec = self.pool.get('product.product').browse(cr,uid,vals['product_id'])
		grn_line =  super(kg_general_grn_line, self).create(cr, uid, vals, context=context)
		return grn_line
	
	#~ def grn_line_cancel(self, cr, uid, ids, context=None):
		#~ grn_line = self.browse(cr, uid, ids[0])
		#~ if not grn_line.cancel_remark:
			#~ raise osv.except_osv(_('Remarks is must !!'), _('Enter Cancel Remarks for GRN Line Cancel !!!'))
		#~ else:
			#~ self.write(cr, uid, ids[0], {'state' : 'cancel'})
		#~ return True
	
kg_general_grn_line()


class kg_exp_batch(osv.osv):
	
	_name = "kg.exp.batch"
	_description = "Expiry Date and Batch NO"
	
	_columns = {
		
		## Basic Info
		
		'grn_line_id':fields.many2one('kg.general.grn.line','GRN Entry Line'),
		
		## Module Requirement Fields
		
		'exp_date':fields.date('Expiry Date'),
		'batch_no':fields.char('Batch No'),
		'product_qty':fields.integer('Product Qty'),
		
	}
	
	
kg_exp_batch()


class kg_gen_grn_expense_track(osv.osv):
	
	_name = "kg.gen.grn.expense.track"
	_description = "kg expense track"
	
	_columns = {
		
		## Basic Info
		
		'expense_id': fields.many2one('kg.general.grn', 'Expense Track'),
		
		## Module Requirement Fields
		
		'name': fields.char('Number', size=128, select=True,readonly=False),
		'date': fields.date('Creation Date'),
		'company_id': fields.many2one('res.company', 'Company Name'),
		'description': fields.char('Description'),
		'expense_amt': fields.float('Amount'),
		
	}
	
	_defaults = {
		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.gen.grn.expense.entry', context=c),
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
		
		}
	
kg_gen_grn_expense_track()
