from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import re
from operator import itemgetter
from itertools import groupby
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import calendar
today = datetime.now()
#~ import MySQLdb

class kg_purchase_invoice(osv.osv):
	
	def _amount_line_tax(self, cr, uid, line, context=None):
		val = 0.0
		if line.price_type == 'per_kg':
			if line.product_id.uom_conversation_factor == 'two_dimension':
				if line.product_id.po_uom_in_kgs > 0:
					qty = line.rec_qty * line.product_id.po_uom_in_kgs * line.length * line.breadth
			elif line.product_id.uom_conversation_factor == 'one_dimension':
				if line.product_id.po_uom_in_kgs > 0:
					qty = line.rec_qty * line.product_id.po_uom_in_kgs
				else:
					qty = line.rec_qty
			else:
				qty = line.rec_qty
		else:
			qty = line.rec_qty
			
		amt_to_per = (line.discount / (qty * line.price_unit or 1.0 )) * 100
		kg_discount_per = line.kg_discount_per
		tot_discount_per = amt_to_per + kg_discount_per
		for c in self.pool.get('account.tax').compute_all(cr, uid, line.invoice_tax_ids,
			line.price_unit * (1-(tot_discount_per or 0.0)/100.0), qty, line.product_id,
			 line.header_id.supplier_id)['taxes']:			 
			val += c.get('amount', 0.0)
		return val
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		advance_net_amt = 0.00
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'amount_untaxed': 0.0,
				'amount_tax': 0.0,
				'amount_total': 0.0,
				'discount' : 0.0,
				'other_charge': 0.0,
				'advance_adjusted_amt': 0.0,
				'credit_amt': 0.0,
				'bal_amt': 0.0,
			}
			val = val1 = val3 = line_total = 0.0
			cur = order.supplier_id.property_product_pricelist_purchase.currency_id
	
			for line in order.line_ids:
				per_to_amt = (line.rec_qty * line.price_unit) * line.kg_discount_per / 100.00
				tot_discount = line.discount + per_to_amt
				val1 += line.price_subtotal
				line_total += line.rec_qty * line.price_unit
				val += self._amount_line_tax(cr, uid, line, context=context)
				val3 += tot_discount
			if order.credit_note_ids:
				credit_amt = (round(sum(map(lambda c:c.credit_amt,order.credit_note_ids))))
			else:
				credit_amt = 0.00
				
			if order.expense_line_ids:
				other_charges = (round(sum(map(lambda c:c.price_subtotal,order.expense_line_ids))))
			else:
				other_charges = 0.00
			
			for line in order.advance_line_ids:
				advance_net_amt += line.current_adv_amt 
				
			res[order.id]['other_charge'] = other_charges
			res[order.id]['advance_adjusted_amt'] = advance_net_amt
			res[order.id]['credit_amt'] = credit_amt
			res[order.id]['amount_tax'] = (round(val,0))
			res[order.id]['amount_untaxed'] = (round(line_total,0))
			res[order.id]['amount_total'] = ((round(val1 + res[order.id]['other_charge'],0)) - credit_amt + order.round_off_amt) - advance_net_amt
			res[order.id]['discount'] = val3
			
		return res
		
	def _get_order(self, cr, uid, ids, context=None):
		result = {}
		for line in self.pool.get('ch.invoice.line').browse(cr, uid, ids, context=context):
			result[line.header_id.id] = True
		return result.keys()

	_name = "kg.purchase.invoice"
	_order = "invoice_date desc"
	_description = "Purchase Invoice"
	_columns = {
	
		'name':fields.char('Invoice No',readonly=True),
		'invoice_date':fields.date('Invoice Date',readonly=True,required=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'type': fields.selection([('from_po', 'Product'), ('from_so', 'Service'),('from_gp','Gate Pass')], 'Product/Service',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'purpose': fields.selection([('consu', 'Consumables'), ('project', 'Project'), ('asset', 'Asset')], 'Purpose',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'grn_type': fields.selection([('from_po_grn', 'PO/SO GRN'), ('from_general_grn', 'General GRN'), ('others', 'Others')], 'GRN Type',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'state': fields.selection([('draft','Draft'),('confirmed','Waiting for approval'),('approved','Approved'),
				('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True,track_visibility='onchange',select=True),	
		'his_state':fields.selection([('pending', 'Pending'), ('paid', 'Paid')],'Payment Status'),
		'payment_date':fields.date('Payment Date', readonly=True),
		
		#Entry Info
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),	
		'created_by' : fields.many2one('res.users', 'Created By', readonly=True),
		'creation_date':fields.datetime('Created Date',required=True,readonly=True),
		'confirmed_date': fields.datetime('Confirmed Date', readonly=True),
		'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'approved_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Approved By', readonly=True),
		'reject_date': fields.datetime('Rejected Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'cancel_date': fields.datetime('Canceled Date', readonly=True),
		'can_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		
		## Vendor Information ##
		
		'supplier_id':fields.many2one('res.partner','Supplier',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'sup_address':fields.text('Supplier Address',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'sup_invoice_no':fields.char('Supplier Invoice No',size=200,readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'sup_invoice_date':fields.date('Supplier Invoice Date',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'payment_id':fields.many2one('kg.payment.master','Payment Terms',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'payment_due_date':fields.date('Payment Due Date',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'remarks': fields.text('Remarks',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'payment_type': fields.selection([('cash', 'Cash'), ('credit', 'Credit')], 'Payment Type',readonly=True),
		'can_remark': fields.text('Cancel Remarks'),
		'reject_remark': fields.text('Reject Remarks'),
			 
		### Order Details ###
		
		'order_no': fields.char('Order NO',readonly=True),
		'order_date': fields.char('Order Date',readonly=True),
		'grn_no': fields.char('GRN NO',readonly=True),
		
		#### GRN Search #######
		
		'po_grn_ids': fields.many2many('kg.po.grn', 'purchase_invoice_grn_ids', 'invoice_id','grn_id', 'GRN', delete=False,
			 domain="[('state','=','done'),'&',('supplier_id','=',supplier_id),'&',('grn_type','=',type),'&',('billing_status','=','applicable'),'&',('inv_flag','=',False)]"),
			 
		'general_grn_ids': fields.many2many('kg.general.grn', 'purchase_invoice_general_grn_ids', 'invoice_id','grn_id', 'GRN', delete=False,
			 domain="[('supplier_id','=',supplier_id), '&', ('state','=','done'), '&', ('bill','=','applicable'),'&',('purpose','=',purpose)]"),
			 
		'labour_ids': fields.many2many('kg.service.invoice', 'service_invoice_grn_ids', 'invoice_id','service_id', 'GRN', delete=False,domain="[('state','=','approved'),'&',('partner_id','=',supplier_id)]"),
		
		### LINE IDS #####
		
		'line_ids':fields.one2many('ch.invoice.line','header_id','Purchase Line Id',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		
		'expense_line_ids':fields.one2many('ch.expense.details','header_id','Expense Line Id',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
			
		'credit_note_ids':fields.one2many('ch.kg.credit.note','header_id','Credit Note',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		
		'history_line_ids':fields.one2many('kg.purchase.payment.history','header_id','History_Line_ids'),
		
		'advance_line_ids':fields.one2many('ch.poadvance.purchase.invoice.line','header_id','History_Line_ids'),
		
		### Amount Calculation fields ### 
		
		'other_charge': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Other Charges(+)',
			 multi="sums", help="The amount without tax", track_visibility='always'),	
		
		'advance_adjusted_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Advanced Adjustment Amount(-)',
			 multi="sums", help="The amount with tax", track_visibility='always',store=True),	
			 
		'credit_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Credit Note Amount',
			 multi="sums", help="The amount with tax", track_visibility='always',store=True),	
		
		'discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Discount(-)',
			store={
				'kg.purchase.invoice': (lambda self, cr, uid, ids, c={}: ids, ['line_ids'], 10),
				'ch.invoice.line': (_get_order, ['price_unit', 'invoice_tax_ids', 'kg_discount', 'rec_qty'], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
			store={
				'kg.purchase.invoice': (lambda self, cr, uid, ids, c={}: ids, ['line_ids'], 10),
				'ch.invoice.line': (_get_order, ['price_unit', 'invoice_tax_ids', 'kg_discount', 'rec_qty'], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
			store={
				'kg.purchase.invoice': (lambda self, cr, uid, ids, c={}: ids, ['line_ids'], 10),
				'ch.invoice.line': (_get_order, ['price_unit', 'invoice_tax_ids', 'kg_discount', 'rec_qty'], 10),
			}, multi="sums", help="The tax amount"),
		'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total',
			store=True,multi="sums",help="The total amount"),
				
		'round_off_amt': fields.float('Round off(+/-)',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'net_amt': fields.float('Net Amount',readonly=True),
		'bal_amt': fields.float('Balance Amount',readonly=True),
		
		'pricelist_id':fields.many2one('product.pricelist', 'Pricelist'),
		'currency_id': fields.many2one('res.currency', 'Currency', readonly=True),
		
		### Flags ##
		
		'load_items_flag':fields.boolean('load_items_flag'),
		
		### Other fields ###
		'specification': fields.text('Specification',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		#~ 'dep_project':fields.many2one('kg.project.master','Dept/Project Name',readonly=True,states={'draft': [('readonly', False)],'confirmed':[('readonly',False)]}),	
		'po_so_name': fields.char('PO/SO NO',readonly=True,states={'draft': [('readonly', False)],'confirmed':[('readonly',False)]}),
		'po_so_date': fields.char('PO/SO Date'),
		'product_id': fields.related('line_ids','product_id', type='many2one', relation='product.product', string='Product'),
		
		}
	
	_defaults = {
		
		'created_by': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'invoice_date': lambda * a: time.strftime('%Y-%m-%d'),
		'payment_due_date': lambda * a: time.strftime('%Y-%m-%d'),
		'load_items_flag': False,
		'state': 'draft',
		'his_state': 'pending',
		'purpose': 'consu',
		'name': '',
		'active': True,
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_purchase_invoice', context=c),
		'bal_amt': 0,
		
	}
	
	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.sup_invoice_no:
			sup_invoice_no = rec.sup_invoice_no
			name=sup_invoice_no.upper()			
			cr.execute(""" select upper(sup_invoice_no) from kg_purchase_invoice where upper(sup_invoice_no) = '%s' and supplier_id = %s """ %(name,rec.supplier_id.id))
			data = cr.dictfetchall()	
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
		
	def paid(self,cr,uid,ids,context=None):
		mast_dt = self.browse(cr,uid,ids[0])
		cr.execute(""" select sum(amt) as amtt from kg_purchase_payment_history as a  where a.header_id = %d """ %(mast_dt))
		rr = cr.fetchall();	
		if rr:
			for t in rr:
				mast_dtt = self.browse(cr,uid,ids[0])
				today_date = today.strftime('%Y-%m-%d')
				calll = mast_dtt.amount_total - t[0]
				if calll == 0:
					cr.execute(""" select id from kg_purchase_payment_history as a  where a.header_id = %d """ %(mast_dt))
					rrr = cr.fetchall();
					ran=tuple(rrr)
					for tt in rrr:
						cr.execute("""update kg_purchase_payment_history set pay_flag = 't' where id = %d """%(tt[0]))
					
					self.write(cr, uid, ids[0],{'his_state':'paid','payment_date':today_date,'bal_amt':calll})
					return False
				else:
					cr.execute(""" select id from kg_purchase_payment_history as a  where a.header_id = %d """ %(mast_dt))
					rrr = cr.fetchall();
					ran=tuple(rrr)
					
					for tt in rrr:
						cr.execute("""update kg_purchase_payment_history set pay_flag = 't' where id = %d """%(tt[0]))
			
					self.write(cr,uid,ids,{'his_state':'pending','bal_amt':calll})
					return True	
			
		return True
	
	def _future_date_check(self,cr,uid,ids,contaxt=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		invoice_date = rec.invoice_date
		sup_invoice_date = rec.sup_invoice_date
		invoice_date = str(invoice_date)
		sup_invoice_date = str(sup_invoice_date)
		invoice_date = datetime.strptime(invoice_date, '%Y-%m-%d')
		sup_invoice_date = datetime.strptime(sup_invoice_date, '%Y-%m-%d')
		if invoice_date > today:
			return False
		if sup_invoice_date > today:
			return False
		return True
		
	_constraints = [		
					  
		(_future_date_check, 'System not allow to save with future date. !!',['price']),
		(_name_validate, 'Supplier Inv No. must be unique !!', ['Supplier Invoice No.']),
		
	   ]
	
	###  Onchange for Supplier Address ###
	
	def onchange_supplier_id(self, cr, uid, ids, supplier_id):
		partner = self.pool.get('res.partner')
		supplier_address = partner.address_get(cr, uid, [supplier_id], ['default'])
		supplier = partner.browse(cr, uid, supplier_id)
		tot_add = (supplier.street or '')+ ' ' + (supplier.street2 or '') + '\n'+(supplier.city_id.name or '')+ ',' +(supplier.state_id.name or '') + '-' +(supplier.zip or '') + '\nPh:' + (supplier.phone or '')+ '\n' +(supplier.mobile or '')
		return {'value': {
			'sup_address' : tot_add or False
			}}
	
	def write(self, cr, uid, ids, vals, context=None):		
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_purchase_invoice, self).write(cr, uid, ids, vals, context)
		
	def load_details(self, cr, uid, ids,context=None):
		invoice_rec = self.browse(cr,uid,ids[0])
		if invoice_rec.state == 'draft':
			invoice_line_obj = self.pool.get('ch.invoice.line')
			po_grn_obj = self.pool.get('kg.po.grn')
			po_grn_line_obj = self.pool.get('po.grn.line')
			general_grn_obj = self.pool.get('kg.general.grn')
			general_grn_line_obj = self.pool.get('kg.general.grn.line')
			
			service_grn_line_obj = self.pool.get('kg.service.invoice.line')
			service_grn_obj = self.pool.get('kg.service.invoice')
			po_name = ''
			po_date = ''
			po_list = []
			podate_list = []
			so_list = []
			sodate_list = []
			gp_list = []
			gpdate_list = []
			ch_line_ids = map(lambda x:x.id,invoice_rec.line_ids)
			invoice_line_obj.unlink(cr,uid,ch_line_ids)
			if invoice_rec.grn_type == 'from_po_grn':
				self.write(cr, uid, ids[0], {'load_items_flag' : True})
				cr.execute(""" select grn_id from purchase_invoice_grn_ids where invoice_id = %s """ %(invoice_rec.id))
				grn_data = cr.dictfetchall()
				
				for item in grn_data:
					grn_id = item['grn_id']
					grn_record = po_grn_obj.browse(cr, uid, grn_id)
					self.write(cr, uid, ids[0], {'payment_type' : grn_record.payment_type})
					cr.execute(""" select id from po_grn_line where po_grn_id = %s and billing_type='cost' order by id """ %(grn_id))
					grn_line_data = cr.dictfetchall()
					for line_item in grn_line_data:
						
						grn_line_record = po_grn_line_obj.browse(cr, uid, line_item['id'])
						if grn_record.grn_type == 'from_po':
							if grn_line_record.po_line_id.order_id.name not in po_list:
								po_list.append(grn_line_record.po_line_id.order_id.name)
								date_order = grn_line_record.po_line_id.order_id.date_order
								date_order = datetime.strptime(date_order, '%Y-%m-%d')
								date_order = date_order.strftime('%d/%m/%Y')
								
								podate_list.append(date_order)
							po_name = ", ".join(po_list)
							po_date = ", ".join(podate_list)
							po_so_name = grn_line_record.po_line_id.order_id.name
							po_so_qty = grn_line_record.po_qty
						if grn_record.grn_type == 'from_gp':
							if grn_line_record.gp_line_id.gate_id:
								if grn_line_record.gp_line_id.gate_id.name not in gp_list:
									gp_list.append(grn_line_record.gp_line_id.gate_id.name)
									date_order = grn_line_record.gp_line_id.gate_id.date
									date_order = datetime.strptime(date_order, '%Y-%m-%d')
									date_order = date_order.strftime('%d/%m/%Y')
									gpdate_list.append(date_order)
								po_name = ", ".join(gp_list)
								po_date = ", ".join(gpdate_list)
								po_so_name = grn_line_record.gp_line_id.gate_id.name
								po_so_qty = grn_line_record.po_qty	
						elif grn_record.grn_type == 'from_so':
							if grn_line_record.so_line_id.service_id.name not in so_list:
								so_list.append(grn_line_record.so_line_id.service_id.name)
								date_order = grn_line_record.so_line_id.service_id.date
								date_order = datetime.strptime(date_order, '%Y-%m-%d')
								date_order = date_order.strftime('%d/%m/%Y')
								sodate_list.append(date_order)
							po_so_name = grn_line_record.so_line_id.service_id.name
							po_so_qty = grn_line_record.so_qty
							po_name = ",".join(so_list)
							po_date = ",".join(sodate_list)
							
						invoice_line_obj.create(cr, uid, {
								'header_id': invoice_rec.id,
								'order_no': po_so_name,
								'grn_no': grn_line_record.po_grn_id.name or '',
								'po_id': grn_line_record.po_id.id or False,
								'so_id': grn_line_record.so_id.id or False,
								'gp_id': grn_line_record.gp_id.id or False,
								'po_line_id': grn_line_record.po_line_id.id or False,
								'so_line_id': grn_line_record.so_line_id.id or False,
								'gp_line_id': grn_line_record.gp_line_id.id or False,
								'po_grn_id': grn_line_record.po_grn_id.id or False,
								'po_grn_line_id': grn_line_record.id or False,
							
								'dc_no': grn_record.dc_no,
								'product_id': grn_line_record.product_id.id,
								'qty':po_so_qty,
								'rec_qty':grn_line_record.po_grn_qty,
								'uom_id': grn_line_record.uom_id.id,
								'price_unit': grn_line_record.price_unit,
								'total_amt': grn_line_record.po_grn_qty * grn_line_record.price_unit,
								'discount': (grn_line_record.kg_discount / grn_line_record.po_qty) * grn_line_record.po_grn_qty,
								'kg_discount_per': grn_line_record.kg_discount_per,
								'invoice_tax_ids': [(6, 0, [x.id for x in grn_line_record.grn_tax_ids])],
							})						
				self.write(cr, uid, ids[0], {'po_so_name' :po_name ,'po_so_date':po_date})			
			if invoice_rec.grn_type == 'from_general_grn':
				self.write(cr, uid, ids[0], {'load_items_flag' : True})
				cr.execute(""" select grn_id from purchase_invoice_general_grn_ids where invoice_id = %s """ %(invoice_rec.id))
				general_grn_data = cr.dictfetchall()
				
				for item in general_grn_data:
					grn_id = item['grn_id']
					grn_record = general_grn_obj.browse(cr, uid, grn_id)
					self.write(cr, uid, ids[0], {'payment_type' : grn_record.payment_type})
					cr.execute(""" select id from kg_general_grn_line where grn_id = %s order by id """ %(grn_id))
					grn_line_data = cr.dictfetchall()
					for line_item in grn_line_data:
						
						grn_line_record = general_grn_line_obj.browse(cr, uid, line_item['id'])
						invoice_line_obj.create(cr, uid, {
								'header_id': invoice_rec.id,
								'order_no': '',
								'grn_no': grn_line_record.grn_id.name or '',
								'general_grn_id': grn_line_record.grn_id.id or False,
								'general_grn_line_id': grn_line_record.id or False,
								'dc_no': grn_record.dc_no,
								'product_id': grn_line_record.product_id.id,
								'qty':grn_line_record.grn_qty,
								'rec_qty':grn_line_record.grn_qty,
								'uom_id': grn_line_record.uom_id.id,
								'price_unit': grn_line_record.price_unit,
								'total_amt': grn_line_record.grn_qty * grn_line_record.price_unit,
								'discount': (grn_line_record.kg_discount / grn_line_record.grn_qty) * grn_line_record.grn_qty,
								'kg_discount_per': grn_line_record.kg_discount_per,
								'invoice_tax_ids': [(6, 0, [x.id for x in grn_line_record.grn_tax_ids])],
								})
			if invoice_rec.grn_type == 'others':
				self.write(cr, uid, ids[0], {'load_items_flag' : True})
				cr.execute(""" select service_id from service_invoice_grn_ids where invoice_id = %s """ %(invoice_rec.id))
				service_grn_data = cr.dictfetchall()
				
				for item in service_grn_data:
					service_id = item['service_id']
					service_record = service_grn_obj.browse(cr, uid, service_id)
					self.write(cr, uid, ids[0], {'payment_type' : service_record.payment_type})
					cr.execute(""" select id from kg_service_invoice_line where service_id = %s order by id """ %(service_id))
					service_line_data = cr.dictfetchall()
					for line_item in service_line_data:
						
						service_line_record = service_grn_line_obj.browse(cr, uid, line_item['id'])
						invoice_line_obj.create(cr, uid, {
								'header_id': invoice_rec.id,
								'order_no': service_record.service_order_id.name or '',
								'grn_no': '',
								'soi_id': service_record.id or False,
								'so_id': service_record.service_order_id.id or False,
								'soi_line_id': service_line_record.id or False,
								'dc_no': '',
								'product_id': service_line_record.product_id.id,
								'qty':service_line_record.product_qty,
								'rec_qty':service_line_record.product_qty,
								'uom_id': service_line_record.product_uom.id,
								'price_unit': service_line_record.price_unit,
								'total_amt':service_line_record.product_qty * service_line_record.price_unit,
								'discount': service_line_record.kg_discount,
								'discount': (service_line_record.kg_discount / service_line_record.product_qty) * grn_line_record.product_qty,
								'kg_discount_per': service_line_record.kg_discount_per,
								'invoice_tax_ids': [(6, 0, [x.id for x in service_line_record.taxes_id])],
								})
			
		return True
		
	def compute_values(self, cr, uid, ids,context=None):
		return True		
	
	def load_advance(self, cr, uid, ids,context=None):
		invoice_rec = self.browse(cr,uid,ids[0])
		if invoice_rec.state == 'confirmed':
			sup_adv_obj = self.pool.get('kg.supplier.advance')
			sup_inadv_obj = self.pool.get('ch.poadvance.purchase.invoice.line')	
			del_sql = """delete from ch_poadvance_purchase_invoice_line where header_id=%s"""%(ids[0])
			cr.execute(del_sql)
			
			for item in invoice_rec.line_ids:
				if invoice_rec.type == 'from_po':
					po_obj = self.pool.get('purchase.order').search(cr,uid,[('name','=',item.order_no)])
				elif invoice_rec.type == 'from_so':
					po_obj = self.pool.get('kg.service.order').search(cr,uid,[('name','=',item.order_no)])
				if po_obj:
					if invoice_rec.type == 'from_po':
						po_rec = self.pool.get('purchase.order').browse(cr,uid,po_obj[0])	
					elif invoice_rec.type == 'from_so':
						po_rec = self.pool.get('kg.service.order').browse(cr,uid,po_obj[0])	
					if invoice_rec.type == 'from_po':
						adv_search = self.pool.get('kg.supplier.advance').search(cr, uid, [('po_id','=',po_rec.id)])
						cr.execute(""" select * from kg_supplier_advance where po_id = %s and balance_amt > 0 and state='confirmed'""" %(po_rec.id))
					elif invoice_rec.type == 'from_so':
						adv_search = self.pool.get('kg.supplier.advance').search(cr, uid, [('po_id','=',po_rec.id)])
						cr.execute(""" select * from kg_supplier_advance where so_id = %s and balance_amt > 0 and state='confirmed'""" %(po_rec.id))
					adv_data = cr.dictfetchall()			
					for adv in adv_data:
						sup_inadv_obj.create(cr,uid,{
							'po_id' : adv['po_id'],
							'sup_advance_id' : adv['id'],
							'sup_advance_date' : adv['entry_date'],
							'tot_advance_amt' : adv['advance_amt'],
							'balance_amt' : adv['balance_amt'],
							'current_adv_amt' : 0.0,
							'header_id' : invoice_rec.id,
							})
				
		return True
			
	def entry_confirm(self, cr, uid, ids,context=None):
		invoice_rec = self.browse(cr,uid,ids[0])
		if invoice_rec.state == 'draft':
		### Credit Note Checking ###
			credit_amt = 0

			if invoice_rec.credit_note_ids:
				for credit in invoice_rec.credit_note_ids:
					credit_amt += credit.credit_amt
					if credit_amt > invoice_rec.amount_total:
						raise osv.except_osv(_('Warning!'),
							_('Credit Note amount should not be greater than Invoice amount'))

			### Checking Advance date ###
			
			today_date = today.strftime('%Y-%m-%d')
			
			if invoice_rec.invoice_date > today_date:
				raise osv.except_osv(_('Warning!'),
					_('Invoice Date should not be greater than current date'))
						
			if invoice_rec.sup_invoice_date > today_date:
				raise osv.except_osv(_('Warning!'),
					_('Supplier Invoice Date should not be greater than current date'))
				
			### Check Advance Amount greater than Zero ###
				
			if not invoice_rec.line_ids:
				raise osv.except_osv(_('Warning!'),
					_('You cannot confirm the entry without Invoice Line'))
							
			else:
				for line in invoice_rec.line_ids:
					if line.price_unit == 0.00:
						raise osv.except_osv(_('Price Unit Cannot be zero!'),
							_('You cannot process Invoice with Price Unit Zero for Product %s.' %(line.product_id.name)))
			
			if invoice_rec.grn_type == 'from_po_grn':
				cr.execute(""" select grn_id from purchase_invoice_grn_ids where invoice_id = %s """ %(invoice_rec.id))
				grn_data = cr.dictfetchall()
				for item in grn_data:
					grn_sql = """ update kg_po_grn set inv_flag = True where id = %s  """ %(item['grn_id'])
					cr.execute(grn_sql)
			
			if invoice_rec.advance_line_ids:
				for line in rec.advance_line_ids:
					sup_advance_line_rec = self.pool.get('kg.supplier.advance').browse(cr, uid, line.cus_advance_id.id)
					sup_advance_bal_amt = sup_advance_line_rec.bal_adv - line.current_adv_amt				
					sup_advance_line_rec.write({'bal_adv': sup_advance_bal_amt})		
													
			inv_no = ''
			if not invoice_rec.name:
				seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.purchase.invoice')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,invoice_rec.invoice_date))
				seq_name = cr.fetchone();
				inv_no = seq_name[0]
			elif invoice_rec.name:
				inv_no = invoice_rec.name
			self.write(cr,uid,ids[0],{'state': 'confirmed',
									  'conf_user_id': uid,
									  'confirmed_date': time.strftime('%Y-%m-%d %H:%M:%S'),
									  'name': inv_no,
									   })
		return True
		
	def entry_approve(self, cr, uid, ids,context=None):
		invoice_rec = self.browse(cr,uid,ids[0])
		if invoice_rec.state == 'confirmed':
			credit_obj = self.pool.get('kg.credit.note')
			
			credit_amt = 0
			
			if invoice_rec.credit_note_ids:
				for credit in invoice_rec.credit_note_ids:
					credit_amt += credit.credit_amt
					if credit_amt > invoice_rec.amount_total:
						raise osv.except_osv(_('Warning!'),
							_('Credit Note amount should not be greater than Invoice amount'))
			
			if invoice_rec.grn_type == 'from_po_grn':
				cr.execute(""" select grn_id from purchase_invoice_grn_ids where invoice_id = %s """ %(invoice_rec.id))
				grn_data = cr.dictfetchall()
				
				for item in grn_data:
					grn_sql = """ update kg_po_grn set state='inv' where id = %s  """ %(item['grn_id'])
					cr.execute(grn_sql)
					
			if invoice_rec.grn_type == 'from_general_grn':
				cr.execute(""" select grn_id from purchase_invoice_general_grn_ids where invoice_id = %s """ %(invoice_rec.id))
				grn_data = cr.dictfetchall()
				
				for item in grn_data:
					grn_sql = """ update kg_general_grn set state='inv' where id = %s  """ %(item['grn_id'])
					cr.execute(grn_sql)
					
			if invoice_rec.labour_ids == 'from_general_grn':		
				cr.execute(""" select service_id from service_invoice_grn_ids where invoice_id = %s """ %(invoice_rec.id))
				service_data = cr.dictfetchall()
				
				for item in service_data:
					service_sql = """ update kg_service_invoice set state='inv' where id = %s  """ %(item['service_id'])
					cr.execute(service_sql)
			
			sup_adv_obj = self.pool.get('kg.supplier.advance')			
			sup_adv_inv_obj = self.pool.get('ch.poadvance.purchase.invoice.line')			
			
			for item in invoice_rec.line_ids:
				if invoice_rec.type == 'from_po':
					po_obj = self.pool.get('purchase.order').search(cr,uid,[('name','=',item.order_no)])
				elif invoice_rec.type == 'from_so':
					po_obj = self.pool.get('kg.service.order').search(cr,uid,[('name','=',item.order_no)])
				if po_obj:
					if invoice_rec.type == 'from_po':
						po_rec = self.pool.get('purchase.order').browse(cr,uid,po_obj[0])	
					elif invoice_rec.type == 'from_so':
						po_rec = self.pool.get('kg.service.order').browse(cr,uid,po_obj[0])
						
					for line in invoice_rec.advance_line_ids:
						if invoice_rec.type == 'from_po':
							adv_search = self.pool.get('kg.supplier.advance').search(cr, uid, [('po_id','=',po_rec.id)])
							adv_ids = self.pool.get('kg.supplier.advance').search(cr, uid, [('po_id','=',line.po_id.id)])
						elif invoice_rec.type == 'from_so':
							adv_search = self.pool.get('kg.supplier.advance').search(cr, uid, [('so_id','=',po_rec.id)])
							adv_ids = self.pool.get('kg.supplier.advance').search(cr, uid, [('so_id','=',line.so_id.id)])
						adv_rec = self.pool.get('kg.supplier.advance').browse(cr, uid,adv_ids[0])				
						adjusted_amt = adv_rec.adjusted_amt + line.current_adv_amt 
						balance_amt = line.current_adv_amt - adjusted_amt
						sup_adv_obj.write(cr, uid, line.sup_advance_id.id, {'adjusted_amt': adjusted_amt,'balance_amt':balance_amt})
			
			total = sum(line.current_adv_amt for line in invoice_rec.advance_line_ids)
			if invoice_rec.amount_untaxed < total:
				raise osv.except_osv(_('Warning!'),
					_('Adjust amount should not be greater than total amount'))
			
			self.write(cr,uid,ids[0],{'state': 'approved',
									  'app_user_id': uid,
									  'approved_date': time.strftime('%Y-%m-%d %H:%M:%S'),
									   })	
		return True
	
	def entry_cancel(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			if not rec.can_remark:
				raise osv.except_osv(_('Remarks Needed !!'),
					_('Enter Remark in Remarks ....'))
			if rec.type == 'from_po':
				if rec.grn_type == 'from_po_grn':
					cr.execute(""" select grn_id from purchase_invoice_grn_ids where invoice_id = %s """ %(rec.id))
					grn_data = cr.dictfetchall()
					for item in grn_data:
						grn_sql = """ update kg_po_grn set state='done',inv_flag=False where id = %s  """ %(item['grn_id'])
						cr.execute(grn_sql)
				if rec.grn_type == 'from_general_grn':
					cr.execute(""" select grn_id from purchase_invoice_general_grn_ids where invoice_id = %s """ %(rec.id))
					grn_data = cr.dictfetchall()
					for item in grn_data:
						grn_sql = """ update kg_general_grn set state='done' where id = %s  """ %(item['grn_id'])
						cr.execute(grn_sql)
			self.write(cr, uid,ids,{'state' : 'cancel',
									'cancel_user_id': uid,
									'cancel_date': time.strftime("%Y-%m-%d %H:%M:%S"),
									})
		return True
	
	def entry_reject(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			if not rec.reject_remark:
				raise osv.except_osv(_('Remarks Needed !!'),
					_('Enter Remark in Remarks ....'))
			self.write(cr, uid,ids,{'state' : 'draft',
									'rej_user_id': uid,
									'reject_date': time.strftime("%Y-%m-%d %H:%M:%S"),
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
		
kg_purchase_invoice()


class ch_invoice_line(osv.osv):

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
						qty = line.rec_qty * line.product_id.po_uom_in_kgs * line.length * line.breadth
				elif line.product_id.uom_conversation_factor == 'one_dimension':
					if line.product_id.po_uom_in_kgs > 0:
						qty = line.rec_qty * line.product_id.po_uom_in_kgs
					else:
						qty = line.rec_qty
				else:
					qty = line.rec_qty
			else:
				qty = line.rec_qty
				
			amt_to_per = (line.discount / (qty * line.price_unit or 1.0 )) * 100
			#~ amt_to_per = ((line.discount/100.00) * (qty/100.00) * (line.price_unit/100.00)) * 100
			
			#~ dis_amt = (line.discount / line.qty) * qty
			#~ amt_to_per = dis_amt / ((line.qty * line.price_unit) / 100)
			#~ kg_discount_per = line.kg_discount_per
			#~ tot_discount_per = amt_to_per + kg_discount_per
			
			kg_discount_per = line.kg_discount_per
			tot_discount_per = amt_to_per + kg_discount_per
			price = line.price_unit * (1 - (tot_discount_per or 0.0) / 100.0)
			taxes = tax_obj.compute_all(cr, uid, line.invoice_tax_ids, price, line.rec_qty, line.product_id, line.header_id.supplier_id)
			cur = line.header_id.supplier_id.property_product_pricelist_purchase.currency_id
			res[line.id] = cur_obj.round(cr, uid, cur, taxes['total_included'])
		return res  

	_name = "ch.invoice.line"
	_description = "Purchase Invoice Line"
	_columns = {
	
		'po_grn_id' : fields.many2one('kg.po.grn', 'GRN NO.'),	
		'po_grn_line_id':fields.many2one('po.grn.line','PO GRN Entry Line'),
		
		'general_grn_id' : fields.many2one('kg.general.grn', 'GRN NO.'),
		'general_grn_line_id' : fields.many2one('kg.general.grn.line', 'GRN Line NO.'),	
		
		'soi_id' : fields.many2one('kg.service.invoice', 'Service Invoice No.'),		
		'soi_line_id' : fields.many2one('kg.service.invoice.line','Service Order Line'),
		
		'dc_no' : fields.char('VENDOR DC NO.'),
		'name' : fields.char('invoice no'),
		'grn_no' : fields.char('GRN No'),
		'order_no' : fields.char('Order NO.'),
		'po_id' : fields.many2one('purchase.order','Purchase Order'),
		'so_id' : fields.many2one('kg.service.order','Service Order'),
		'gp_id' : fields.many2one('kg.gate.pass','Gate Pass'),
		'po_line_id':fields.many2one('purchase.order.line','PO Line'),
		'so_line_id':fields.many2one('kg.service.order.line','SO Line'),
		'gp_line_id':fields.many2one('kg.gate.pass.line','SO Line'),
		'product_id' : fields.many2one('product.product','PRODUCT'),
		'qty': fields.float('PO/SO QTY'),
		'rec_qty': fields.float('RECEIVED QTY'),
		'uom_id': fields.many2one('product.uom','RECEIVED UOM'),
		'price_unit': fields.float('RATE'),
		'total_amt': fields.float('TOTAL AMOUNT'),
		'discount': fields.float('DISCOUNT(-)'),
		'kg_discount_per': fields.float('DISCOUNT%(-)'),
		'invoice_tax_ids': fields.many2many('account.tax', 'ch_invoice_tax', 'invoice_line_id', 'taxes_id', 'Taxes(+)'),
		
		'header_id' : fields.many2one('kg.purchase.invoice', 'Header ID'),
		
		'brand_id':fields.many2one('kg.brand.master','Brand'),
		'price_subtotal': fields.function(_amount_line,string='Line Total', digits_compute= dp.get_precision('Account')),
		'price_type': fields.selection([('po_uom','PO UOM'),('per_kg','Per KG')],'Price Type'),
		'length': fields.float('Length'),
		'breadth': fields.float('Breadth'),
		
	}
	
	_defaults = {
	
		'price_type': 'po_uom',
	
	}
	
ch_invoice_line()


class ch_kg_purchase_payment_history(osv.osv):
	
	_name = 'kg.purchase.payment.history'
	_description = 'This module is about the history of the payment by the customer'
		
	_columns = {
	
		'header_id':fields.many2one('kg.purchase.invoice','Header_id'),
		'pay_mode':fields.selection([('cheque','Cheque'),('cash','Cash'),('neft','NEFT'),('rtgs','RTGS')],'Mode of Payment'),
		'reference':fields.char('Reference'),
		'dop':fields.date('Date of Payment'),
		'amt':fields.float('Amount'),
		'pay_flag':fields.boolean('Active'),
	}
	
	_defaults = {
		
		'pay_flag':False
	
	}
	
	def _check_lineitem(self, cr, uid, ids, context=None):	
		indent = self.browse(cr,uid,ids[0])
		if not indent.line_ids:
			return False
												
		return True
	
	def check_amountpaid(self,cr,uid,ids,context=None):
		mast_dt = self.browse(cr,uid,ids[0])
		cr.execute(""" select net_amt from kg_purchase_invoice  where id = %d """ %(mast_dt.header_id.id))
		rr = cr.fetchall();	
		for t in rr:
			mast_dtt = self.browse(cr,uid,ids[0])
			today = date.today()
			today = str(today)
			today = datetime.strptime(today, '%Y-%m-%d')
			ent_d = mast_dt.dop
			ent_dd = str(ent_d)
			ent_dd = datetime.strptime(ent_dd, '%Y-%m-%d')
			if t[0]:
				if mast_dtt.amt > t[0]:
					return False
			elif ent_dd > today:
				return False
			else:
				return True
				
	_constraints = [(check_amountpaid,'Please check the paid amount,it is may exceed the Net Amount!! or check the payment date it should not be the future date',['']),]
		
ch_kg_purchase_payment_history()


class ch_kg_credit_note(osv.osv):
	
	_name = 'ch.kg.credit.note'
	_description = 'This module is about the details of credit note'
	
	_columns = {
	
		'header_id':fields.many2one('kg.purchase.invoice','Header_id'),
		'credit_id':fields.many2one('kg.credit.note','Credit Note No'),
		'credit_date':fields.date('Credit Note Date'),
		'supplier_id':fields.many2one('res.partner','Supplier',domain = [('supplier','=',True),('sup_state','=','approved')],readonly=True),
		'supplier_invoice_no':fields.char('Supplier Invoice No',readonly=True),
		'supplier_invoice_date':fields.date('Supplier Invoice Date',readonly=True),	
		'credit_amt':fields.float('Credit Note Amount'),
		
	}
	
	def onchange_credit_id(self, cr, uid, ids, credit_id):
		credit_obj = self.pool.get('kg.credit.note')
	
		if credit_id:
			credit_rec = credit_obj.browse(cr, uid, credit_id)
			return {'value': {
				'credit_date' : credit_rec.date,
				'supplier_id' : credit_rec.supplier_id.id,
				'supplier_invoice_no' : credit_rec.supplier_invoice_no,
				'supplier_invoice_date' : credit_rec.supplier_invoice_date,
				'credit_amt' : credit_rec.amount_total,
				
				}}
	
ch_kg_credit_note()


class ch_expense_details(osv.osv):
	
	def _amount_line(self, cr, uid, ids, prop, arg, context=None):
		cur_obj=self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		res = {}
		if context is None:
			context = {}
		for line in self.browse(cr, uid, ids, context=context):
			taxes = tax_obj.compute_all(cr, uid, line.expense_tax_ids, line.expense_amt, 1,False, line.header_id.supplier_id.id)
			cur = line.header_id.supplier_id.property_product_pricelist_purchase.currency_id
			res[line.id] = cur_obj.round(cr, uid, cur, taxes['total_included'])
		return res  
		
	_name = 'ch.expense.details'
	_description = 'This module is used to track the expense details'
	
	_columns = {
	
		'header_id':fields.many2one('kg.purchase.invoice','Header_id'),
		'expense_id': fields.many2one('kg.expense.master','Expense',domain="[('state','not in',('cancel','reject'))]"),
		'expense': fields.char('Expense'),
		'expense_amt': fields.float('Amount'),
		'expense_tax_ids': fields.many2many('account.tax', 'ch_expense_tax', 'expense_line_id', 'taxes_id', 'Taxes(+)'),
		'price_subtotal': fields.function(_amount_line,string='Line Total', digits_compute= dp.get_precision('Account')),
		
	}
	
ch_expense_details()

class ch_poadvance_purchase_invoice_line(osv.osv):

	_name = "ch.poadvance.purchase.invoice.line"
	_description = "PO Advance Purchase Invoice Line"
	
	_columns = {
		
		'header_id' : fields.many2one('kg.purchase.invoice', 'Header ID'),
		'sup_advance_id' : fields.many2one('kg.supplier.advance', 'Supplier Advance No', readonly=True),
		'sup_advance_date': fields.date('Supplier Advance Date'),
		'sup_advance_line_id' : fields.many2one('ch.advance.line', 'PO Advance Line', readonly=True),		
		'po_id': fields.many2one('purchase.order','PO No'),		
		'so_id': fields.many2one('kg.service.order','SO No'),		
		'po_amt': fields.float('PO Amount', readonly=True),
		'tot_advance_amt': fields.float('Total Advance Amount', readonly=True),
		'already_adjusted_amt': fields.float('Already Adjusted Advance Amount', readonly=True),
		'balance_amt': fields.float('Balance Advance to be adjusted', readonly=True),
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
	   
ch_poadvance_purchase_invoice_line()
