import math
import re
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
from itertools import groupby
import openerp.addons.decimal_precision as dp
import netsvc
import pooler
import logging
from tools import number_to_text_convert_india
logger = logging.getLogger('server')
today = datetime.now()
import urllib
import urllib2
import logging
import base64

class kg_service_order(osv.osv):

	_name = "kg.service.order"
	_description = "KG Service Order"
	_order = "date desc"

	def _amount_line_tax(self, cr, uid, line, context=None):
		val = 0.0
		#new_amt_to_per = line.kg_discount or 0.0 / line.product_qty
		amt_to_per = (line.kg_discount / (line.product_qty * line.price_unit or 1.0 )) * 100
		kg_discount_per = line.kg_discount_per
		tot_discount_per = amt_to_per + kg_discount_per
		for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id,
			line.price_unit * (1-(tot_discount_per or 0.0)/100.0), line.product_qty, line.product_id,
			line.service_id.partner_id)['taxes']:
				 
			val += c.get('amount', 0.0)
		return val
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		other_charges_amt = 0
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'total_amount': 0.0,
				'amount_untaxed': 0.0,
				'amount_tax': 0.0,
				'amount_total': 0.0,
				'grand_total': 0.0,
				'discount' : 0.0,
				'other_charge': 0.0,
			}
			val = val1 = val3 = 0.0
			cur = order.pricelist_id.currency_id
			po_charges=order.value1 + order.value2
			
			if order.expense_line_id:
				for item in order.expense_line_id:
					other_charges_amt += item.expense_amt
			else:
				other_charges_amt = 0
				
			for line in order.service_order_line:
				discount_per_value = ((line.product_qty * line.price_unit) / 100.00) * line.kg_discount_per
				tot_discount = line.kg_discount + discount_per_value
				val1 += line.price_subtotal
				val += self._amount_line_tax(cr, uid, line, context=context)
				val3 += tot_discount
			res[order.id]['total_amount'] = (val1 + val3) - val
			res[order.id]['other_charge'] = (round(other_charges_amt,0))
			res[order.id]['amount_tax'] = val
			res[order.id]['amount_untaxed'] = val1 - val
			res[order.id]['discount'] = val3
			res[order.id]['grand_total'] = val1
			res[order.id]['round_off'] = order.round_off
			res[order.id]['amount_total'] = val1 + order.round_off or 0.00
			
		
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
		for line in self.pool.get('kg.service.order.line').browse(cr, uid, ids, context=context):
			result[line.service_id.id] = True
		return result.keys()
	
	_columns = {
		
		## Basic Info
		
		'name': fields.char('SO No', size=64,readonly=True),
		'date': fields.date('SO Date', required=True,readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'state': fields.selection([('draft', 'Draft'),('confirm','WFA'),('approved','Approved'),('inv','Invoiced'),('cancel','Cancelled'),('reject','Rejected')], 'Status', track_visibility='onchange'),
		'note': fields.text('Notes',readonly=True, states={'confirm':[('readonly',False)]}),
		'remark': fields.text('Remarks', readonly=True, states={'approved': [('readonly', False)],'done':[('readonly',False)],'confirm':[('readonly',False)]}),
		
		## Module Requirement Info
		
		'dep_name': fields.many2one('kg.depmaster','Department Name', translate=True, select=True,readonly=True, 
					domain="[('item_request','=',True),('state','in',('draft','confirmed','approved'))]", states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'partner_id':fields.many2one('res.partner', 'Supplier', required=True,readonly=True, 
					states={'draft':[('readonly',False)],'confirm':[('readonly',False)]},domain="[('supplier','=',True)]"),
		'pricelist_id':fields.many2one('product.pricelist', 'Pricelist'),
		'partner_address':fields.char('Supplier Address', size=128, readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'payment_mode': fields.many2one('kg.payment.master', 'Mode of Payment',readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		#~ 'delivery_type':fields.many2one('kg.deliverytype.master', 'Delivery Schedule', 
		             #~ required=False, readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'delivery_mode': fields.many2one('kg.delivery.master','Delivery Schedule', 
		               required=True, readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'po_expenses_type1': fields.selection([('freight','Freight Charges'),('others','Others')], 'Expenses Type1', 
										readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'po_expenses_type2': fields.selection([('freight','Freight Charges'),('others','Others')], 'Expenses Type2', 
								readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'value1':fields.float('Value1', readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'value2':fields.float('Value2', readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'round_off': fields.float('Round off',size=5,readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'other_charge': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Other Charges(+)',
			 multi="sums", help="The amount without tax", track_visibility='always'),		
		'total_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Amount',
			 multi="sums", store=True, help="The amount without tax", track_visibility='always'),
		'grand_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Grand Total',
			 multi="sums", store=True, help="The amount without tax", track_visibility='always'),
		'discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Discount(-)',
			store={
				'kg.service.order': (lambda self, cr, uid, ids, c={}: ids, ['service_order_line'], 10),
				'kg.service.order.line': (_get_order, ['price_unit', 'tax_id', 'kg_discount', 'product_qty'], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
			store={
				'kg.service.order': (lambda self, cr, uid, ids, c={}: ids, ['service_order_line'], 10),
				'kg.service.order.line': (_get_order, ['price_unit', 'tax_id', 'kg_discount', 'product_qty'], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
			store={
				'kg.service.order': (lambda self, cr, uid, ids, c={}: ids, ['service_order_line'], 10),
				'kg.service.order.line': (_get_order, ['price_unit', 'tax_id', 'kg_discount', 'product_qty'], 10),
			}, multi="sums", help="The tax amount"),
		'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',
			store=True, multi="sums",help="The total amount"),
		'kg_serindent_lines':fields.many2many('kg.service.indent.line','kg_serindent_so_line' , 'so_id', 'serindent_line_id', 'ServiceIndent Lines',
			domain="[('service_id.state','=','approved'), '&', ('pending_qty','>','0')]", 
			readonly=True, states={'draft': [('readonly', False)],'confirm':[('readonly',False)]}),
		'so_flag': fields.boolean('SO Flag'),
		'amend_flag': fields.boolean('Amend Flag'),
		
		'so_bill': fields.boolean('SO Bill', readonly=True),
		'currency_id': fields.many2one('res.currency', 'Currency', readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'specification':fields.text('Specification'),
		'freight_charges':fields.selection([('Inclusive','Inclusive'),('Extra','Extra'),('To Pay','To Pay'),('Paid','Paid'),
						  ('Extra at our Cost','Extra at our Cost')],'Freight Charges',readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'price':fields.selection([('inclusive','Inclusive of all Taxes and Duties'),('exclusive','Excluding All Taxes and Duties')],'Price',readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'today_date':fields.date('Date'),
		'text_amt':fields.text('Amount In Text'),
		'quot_ref_no':fields.char('Quot.Ref',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'quot_date':fields.date('Quot.Date',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'so_type': fields.selection([('amc','AMC'),('service', 'Service'),('labor', 'Labor Only')], 'Type',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'amc_from': fields.date('AMC From Date',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'amc_to': fields.date('AMC To Date',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		
		'gp_id': fields.many2one('kg.gate.pass', 'Gate Pass No',domain="[('state','=','done'), '&',('partner_id','=',partner_id),'&',('mode','=','frm_indent')]",
					readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'warranty': fields.char('Warranty', size=256,readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'grn_flag':fields.boolean('GRN Flag'),
		'button_flag':fields.boolean('Button Flag',invisible=True),
		'so_reonly_flag':fields.boolean('SO Flag'),
		'payment_type': fields.selection([('cash', 'Cash'),('credit', 'Credit'),('advance','Advance')], 'Payment Mode',readonly=True,states={'draft':[('readonly',False)]}),
		'version':fields.char('Version'),
		'adv_flag': fields.boolean('Advance Flag'),
		'advance_amt': fields.float('Advance(%)',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'delivery_address': fields.text('Delivery Address',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'mode_of_dispatch': fields.many2one('kg.dispatch.master','Mode of Dispatch',domain="[('state','not in',('cancel','reject'))]",readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		
		## Child Tables Declaration
		
		'service_order_line': fields.one2many('kg.service.order.line', 'service_id', 'Order Lines', 
					readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'expense_line_id': fields.one2many('kg.service.order.expense.track','expense_id','Expense Track'),
		
		## Entry Info
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company','Company',readonly=True),
		'user_id' : fields.many2one('res.users', 'Created By', readonly=True),
		'creation_date':fields.datetime('Created Date',readonly=True),
		'confirmed_by': fields.many2one('res.users', 'Confirmed By',readonly=True),
		'confirmed_date': fields.datetime('Confirmed Date',readonly=True),
		'approved_by': fields.many2one('res.users', 'Approved By', readonly=True),
		'approved_date': fields.datetime('Approved Date',readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'reject_date': fields.datetime('Rejected Date', readonly=True),
		'update_user_id' : fields.many2one('res.users','Last Updated By',readonly=True),
		'update_date' : fields.datetime('Last Updated Date',readonly=True),
		
	}
	
	_defaults = {
		
		'state': 'draft',
		'active': 'True',
		'button_flag': False,
		'date': lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
		'currency_id': _get_currency,
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.service.order', context=c),
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'version': '00',
		'pricelist_id': 2,
		'adv_flag': False,
		
	}
	
	def onchange_type(self,cr,uid,ids,so_type,so_flag,context=None):
		value = {'so_flag':'','so_reonly_flag':''}
		if so_type == 'amc' or so_type == 'labor':
			value = {'so_flag': True}
		else:
			value = {'so_flag': False}
		return {'value':value}
	
	def onchange_partner_id(self, cr, uid, ids, partner_id,company_id):
		partner = self.pool.get('res.partner')
		if not partner_id:
			return {'value': {
				'fiscal_position': False,
				'payment_term_id': False,
				}}
		supplier_address = partner.address_get(cr, uid, [partner_id], ['default'])
		supplier = partner.browse(cr, uid, partner_id)
		street = supplier.street or ''
		street2 = supplier.street2 or ''
		landmark = supplier.landmark or ''
		city = supplier.city_id.name or ''
		zip_code = supplier.zip or ''
		address = street+','+street2+','+landmark+','+city+','+zip_code or ''
		
		company_rec = self.pool.get('res.company').browse(cr,uid,company_id)
		
		supplier_address = partner.address_get(cr, uid, [company_rec.partner_id.id], ['default'])
		company = partner.browse(cr, uid, company_rec.partner_id.id)
		com_street = company.street or ''
		com_street2 = company.street2 or ''
		com_landmark = company.landmark or ''
		com_city = company.city_id.name or ''
		com_zip_code = company.zip or ''
		delivery_address = com_street+','+com_street2+','+com_landmark+','+com_city+','+com_zip_code or ''
		
		return {'value': {
			'pricelist_id': supplier.property_product_pricelist_purchase.id,
			'partner_address' : address,
			'delivery_address' : delivery_address,
			}}
	
	def write(self, cr, uid, ids, vals, context=None):		
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_service_order, self).write(cr, uid, ids, vals, context)
				
	def button_dummy(self, cr, uid, ids, context=None):
		return True
	
	def draft_order(self, cr, uid, ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'cancel':
			self.write(cr,uid,ids,{'state':'draft'})
		return True
		
	def confirm_order(self, cr, uid, ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			service_line_obj = self.pool.get('kg.service.order.line')
			today_date = datetime.date(today)
			for t in self.browse(cr,uid,ids):
				date_order = t.date
				date_order1 = datetime.strptime(date_order, '%Y-%m-%d')
				date_order1 = datetime.date(date_order1)
				if date_order1 > today_date:
					raise osv.except_osv(_('Warning'),
						_('SO Date should be less than or equal to current date!'))	
				if not t.service_order_line:
					raise osv.except_osv(_('Empty Service Order'),
						_('You can not confirm an empty Service Order'))
				for line in t.service_order_line:
					if line.product_qty==0:
						raise osv.except_osv(_('Warning'),
							_('Service Order quantity can not be zero'))
					if line.price_unit==0.00:
						raise osv.except_osv(_('Warning'),
							_('You can not confirm Service Order with Zero Value'))
					if t.so_type == 'service':
						if line.product_qty > line.soindent_qty:
							raise osv.except_osv(_('If Service Order From Service Indent'),
								_('Service Order Qty can not greater than Service Indent Qty For Product --> %s'%(line.product_id.name)))
					product_tax_amt = self._amount_line_tax(cr, uid, line, context=context)
					cr.execute("""update kg_service_order_line set product_tax_amt = %s where id = %s"""%(product_tax_amt,line.id))	
					service_line_obj.write(cr,uid,line.id,{'state':'confirm'})		
				seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.service.order')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,rec.date))
				seq_name = cr.fetchone();
				self.write(cr,uid,ids,{ 'state':'confirm',
										'confirmed_by':uid,
										'confirmed_date':time.strftime('%Y-%m-%d %H:%M:%S'),
										'so_reonly_flag':'True',
										'name': seq_name[0],
										})
				
		return True
			
	def approve_order(self, cr, uid, ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirm':
			if rec.payment_type == 'advance':
				obj = rec
				self.advance_creation(cr,uid,obj)
			
			if rec.payment_mode.term_category == 'advance':
				cr.execute("""select * from kg_supplier_advance where state='confirmed' and so_id= %s"""  %(str(ids[0])))
				data = cr.dictfetchall()
				if not data:
					raise osv.except_osv(_('Warning'),
						_('Advance is mandate for this SO'))
				else:
					pass
			text_amount = number_to_text_convert_india.amount_to_text_india(rec.amount_total,"INR:")
			self.write(cr,uid,ids,{'state':'approved','approved_by':uid,'text_amt':text_amount,'approved_date':time.strftime('%Y-%m-%d %H:%M:%S')})
			obj = self.browse(cr,uid,ids[0])
			product_obj = self.pool.get('product.product')
			cr.execute(""" select serindent_line_id from kg_serindent_so_line where so_id = %s """ %(str(ids[0])))
			data = cr.dictfetchall()
			val = [d['serindent_line_id'] for d in data if 'serindent_line_id' in d] # Get a values form list of dict if the dict have with empty values
			so_lines = obj.service_order_line
			if not so_lines:
				raise osv.except_osv(_('Empty Service Order'),
					_('System not allow to approve without Service Order Line'))
			else:
				for i in range(len(so_lines)):
					self.pool.get('kg.service.order.line').write(cr, uid,so_lines[i].id,{'so_type_flag':'True','service_flag':'True','state':'approved'})
					product_id = so_lines[i].product_id.id
					product_record = product_obj.browse(cr, uid, product_id)
					product = so_lines[i].product_id.name
					if rec.so_type == 'service':
						if so_lines[i].soindent_line_id:
							soindent_line_id=so_lines[i].soindent_line_id
							orig_soindent_qty = so_lines[i].soindent_qty
							so_used_qty = so_lines[i].product_qty
							pending_soindent_qty = orig_soindent_qty -  so_used_qty
							sql = """ update kg_service_indent_line set pending_qty=%s where id = %s """%(pending_soindent_qty,
														soindent_line_id.id)
							cr.execute(sql)

							sql1 = """ update kg_gate_pass_line set so_pending_qty=(so_pending_qty - %s),so_flag = 't' where si_line_id = %s and gate_id = %s"""%(so_used_qty,
														soindent_line_id.id,obj.gp_id.id)
							cr.execute(sql1)
							
							sql2 = """ update kg_service_order_line set gp_line_id=(select id from kg_gate_pass_line where si_line_id = %s and gate_id = %s limit 1)"""%(soindent_line_id.id,obj.gp_id.id)
							cr.execute(sql2)
						else:
							raise osv.except_osv(_('Direct Service Order Not Allow'),
								_('System not allow to raise a Service Order with out Service Indent for %s' %(product)))
					else:
						rec.write({'button_flag':True})
			for line in rec.service_order_line:
				product_tax_amt = self._amount_line_tax(cr, uid, line, context=context)
				cr.execute("""update kg_service_order_line set product_tax_amt = %s where id = %s"""%(product_tax_amt,line.id))
			
		return True
		cr.close()
	
	def advance_creation(self,cr,uid,obj,context=None):
		
		advance_amt = (obj.amount_total / 100.00) * obj.advance_amt
		print"advance_amt",advance_amt
		sup_adv_id = self.pool.get('kg.supplier.advance').create(cr,uid,{'supplier_id': obj.partner_id.id,
															'order_category': 'service',
															'so_id': obj.id,
															'advance_amt': advance_amt,
															'order_value': obj.amount_total,
															'order_no': obj.name,
															'entry_mode': 'auto',
															})
		sup_ids = self.pool.get('kg.supplier.advance').search(cr,uid,[('supplier_id','=',obj.partner_id.id),('state','=','confirmed')])		
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
			
	def cancel_order(self, cr, uid, ids, context=None):		
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			if not rec.remark:
				raise osv.except_osv(_('Remarks Needed !!'),
					_('Enter Remark in Remarks Tab....'))
			self.write(cr, uid,ids,{'state' : 'cancel','cancel_date':time.strftime('%Y-%m-%d %H:%M:%S'),'cancel_user_id':uid})
		return True
			
	def reject_order(self, cr, uid, ids, context=None):		
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirm':
			if not rec.remark:
				raise osv.except_osv(_('Remarks Needed !!'),
					_('Enter Remark in Remarks Tab....'))
			self.write(cr, uid,ids,{'state' : 'cancel','reject_date':time.strftime('%Y-%m-%d %H:%M:%S'),'rej_user_id':uid})
		return True
			
	def unlink(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		indent = self.read(cr, uid, ids, ['state'], context=context)
		unlink_ids = []
		for t in indent:
			if t['state'] in ('draft'):
				unlink_ids.append(t['id'])
			else:
				raise osv.except_osv(_('Invalid action !'), _('System not allow to delete a UN-DRAFT state Service Order !!'))
		indent_lines_to_del = self.pool.get('kg.service.order.line').search(cr, uid, [('service_id','in',unlink_ids)])
		self.pool.get('kg.service.order.line').unlink(cr, uid, indent_lines_to_del)
		osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		return True
	
	def update_soindent(self,cr,uid,ids,context=False,):

		soindent_line_obj = self.pool.get('kg.service.indent.line')
		so_line_obj = self.pool.get('kg.service.order.line')
		prod_obj = self.pool.get('product.product')
		res={}
		service_order_line = []
		res['service_order_line'] = []
		res['so_flag'] = True
		res['so_reonly_flag'] = True
		obj =  self.browse(cr,uid,ids[0])
		if obj.service_order_line:
			service_order_line = map(lambda x:x.id,obj.service_order_line)
			so_line_obj.unlink(cr,uid,service_order_line)
		if obj.kg_serindent_lines:
			soindent_line_ids = map(lambda x:x.id,obj.kg_serindent_lines)
			soindent_line_browse = soindent_line_obj.browse(cr,uid,soindent_line_ids)
			
			soindent_line_browse = sorted(soindent_line_browse, key=lambda k: k.product_id.id)
			groups = []
			for key, group in groupby(soindent_line_browse, lambda x: x.product_id.id):
				groups.append(map(lambda r:r,group))
			for key,group in enumerate(groups):
				qty = sum(map(lambda x:float(x.qty),group)) #TODO: qty
				soindent_line_ids = map(lambda x:x.id,group)
				prod_browse = group[0].product_id
				serial_no = group[0].serial_no.id
				ser_no = group[0].ser_no			
				uom =False
				for ele in group:
					uom = (ele.uom.id) or False
					qty = sum(map(lambda x:float(x.pending_qty),group))
					soindent_id= ele.id
					break
				vals = {
				'product_id':prod_browse.id,
				'product_uom':uom,
				'product_qty':qty,
				'pending_qty':qty,
				'soindent_qty':qty,
				'soindent_line_id':soindent_id,
				'service_flag':'False',
				'ser_no':ser_no,
				'serial_no':serial_no,
				'indent_flag':True,
				}				
				
				if ids:
					self.write(cr,uid,ids[0],{'service_order_line':[(0,0,vals)]})
			if ids:
				if obj.service_order_line:
					service_order_line = map(lambda x:x.id,obj.service_order_line)
					for line_id in service_order_line:
						self.write(cr,uid,ids,{'service_order_line':[]})
		self.write(cr,uid,ids,res)			
		return True

	def _check_line(self, cr, uid, ids, context=None):
		for so in self.browse(cr,uid,ids):
			if so.kg_serindent_lines==[]:
				tot = 0.0
				for line in so.service_order_line:
					tot += line.product_qty
				if tot <= 0.0:			
					return False
			return True
			
	def so_direct_print(self, cr, uid, ids, context=None):
		assert len(ids) == 1, 'This option should only be used for a single id at a time'
		wf_service = netsvc.LocalService("workflow")
		wf_service.trg_validate(uid, 'kg.service.order', ids[0], 'send_rfq', cr)
		datas = {
				 'model': 'kg.service.order',
				 'ids': ids,
				 'form': self.read(cr, uid, ids[0], context=context),
		}
		return {'type': 'ir.actions.report.xml', 'report_name': 'service.order.report', 'datas': datas, 'nodestroy': True}
	
	def _check_advance(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.payment_type == 'advance':
			if rec.advance_amt <= 0.00:
				raise osv.except_osv(_('Warning !'),
					_('System sholud not be accecpt with out Advance !'))
			elif rec.advance_amt > 100:
				raise osv.except_osv(_('Warning !'),
					_('System sholud not be greater than 100 !'))
			else:
				pass
		return True
	
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_code = str(rec.name)		
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
			
		url = 'http://192.168.1.7/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&Service_Order='+rec_code


		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
	
	_constraints = [
		
		(_check_line,'You can not save this Service Order with out Line and Zero Qty !',['line_ids']),
		(_check_advance,'System sholud not be accecpt with out Advance !',['']),
		
	]
	
kg_service_order()

class kg_service_order_line(osv.osv):
	
	_name = "kg.service.order.line"
	_description = "Service Order"
	
	def onchange_discount_value_calc(self, cr, uid, ids, kg_discount_per, product_qty, price_unit):
		discount_value = (product_qty * price_unit) * kg_discount_per / 100
		return {'value': {'kg_discount_per_value': discount_value}}
	
	def onchange_product_id(self, cr, uid, ids, product_id, product_uom,context=None):
		value = {'product_uom': ''}
		if product_id:
			prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			value = {'product_uom': prod.uom_id.id}
		return {'value': value}
		
	def onchange_qty(self,cr,uid,ids,product_qty,soindent_qty,pending_qty,service_flag,context=None):
		value = {'pending_qty' : ''}
		if service_flag == True:
			if product_qty and product_qty > soindent_qty:
				raise osv.except_osv(_('If Service Order From Service Indent !'),
					_('Service Order Qty can not greater than Service Indent Qty !!'))
				value = {'pending_qty' : 0.0}
			else:
				pending_qty = product_qty
				value = {'pending_qty' : pending_qty}
		else:
			pending_qty = product_qty
			value = {'pending_qty' : pending_qty}
		return {'value' : value}
		
	def _amount_line(self, cr, uid, ids, prop, arg, context=None):
		cur_obj=self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		res = {}
		if context is None:
			context = {}
		for line in self.browse(cr, uid, ids, context=context):
			amt_to_per = (line.kg_discount / (line.product_qty * line.price_unit or 1.0 )) * 100
			kg_discount_per = line.kg_discount_per
			tot_discount_per = amt_to_per + kg_discount_per
			price = line.price_unit * (1 - (tot_discount_per or 0.0) / 100.0)
			taxes = tax_obj.compute_all(cr, uid, line.taxes_id, price, line.product_qty, line.product_id, line.service_id.partner_id)
			cur = line.service_id.pricelist_id.currency_id
			res[line.id] = cur_obj.round(cr, uid, cur, taxes['total_included'])
		return res
	
	_columns = {
	
	## Basic Info
	
	'service_id': fields.many2one('kg.service.order', 'Service.order.NO', required=True, ondelete='cascade'),
	'note': fields.text('Remarks'),
	
	## Module Requirement Fields
	
	'so_date': fields.related('service_id','date', type='date', string='SO Date',store=True),
	'partner_id': fields.related('service_id','partner_id', type='many2one',relation="res.partner", string='Supplier',store=True),
	'price_subtotal': fields.function(_amount_line, string='Linetotal', digits_compute= dp.get_precision('Account'),store=True),
	'product_id': fields.many2one('product.product', 'Product', domain="[('state','not in',('reject','cancel')),('purchase_ok','=',True)]"),
	'product_uom': fields.many2one('product.uom', 'UOM'),
	'product_qty': fields.float('Quantity'),
	'soindent_qty':fields.float('Indent Qty'),
	'pending_qty':fields.float('Pending Qty'),
	'received_qty':fields.float('Received Qty'),
	'taxes_id': fields.many2many('account.tax', 'service_order_tax', 'tax_id','service_order_line_id', 'Taxes'),
	'soindent_line_id':fields.many2one('kg.service.indent.line', 'Indent Line'),
	'kg_discount': fields.float('Discount Amount', digits_compute= dp.get_precision('Discount')),
	'kg_disc_amt_per': fields.float('Disc Amt(%)', digits_compute= dp.get_precision('Discount')),
	'price_unit': fields.float('Unit Price', digits_compute= dp.get_precision('Product Price')),
	'kg_discount_per': fields.float('Discount (%)', digits_compute= dp.get_precision('Discount')),
	'kg_discount_per_value': fields.float('Discount(%)Value', digits_compute= dp.get_precision('Discount')),
	'brand_id': fields.many2one('kg.brand.master','Brand'),
	'service_flag':fields.boolean('Service Flag'),
	'so_type_flag':fields.boolean('Type Flag'),
	'indent_flag':fields.boolean('Indent Flag'),
	'ser_no':fields.char('Ser No', size=128, readonly=True),
	'serial_no':fields.many2one('stock.production.lot','Serial No',domain="[('product_id','=',product_id)]", readonly=True),	
	'state': fields.selection([('draft', 'Draft'),('confirm','Waiting For Approval'),('approved','Approved'),('inv','Invoiced'),('cancel','Cancel')], 'Status'),
	'gp_line_id':fields.many2one('kg.gate.pass.line', 'Indent Line'),	
	'product_tax_amt':fields.float('Tax Amount'), 
	
	}
	
	def onchange_disc_amt(self, cr, uid, ids, kg_discount,product_qty,price_unit,kg_disc_amt_per):
		if kg_discount:
			kg_discount = kg_discount + 0.00
			amt_to_per = (kg_discount / (product_qty * price_unit or 1.0 )) * 100
			print "amt_to_peramt_to_peramt_to_per", amt_to_per
			return {'value': {'kg_disc_amt_per': amt_to_per}}
		else:
			return {'value': {'kg_disc_amt_per': 0.0}}
			
	_defaults  = {
	
		'received_qty': 0.00,
		'state':'draft'
	}
	
kg_service_order_line()	

class kg_service_order_expense_track(osv.osv):

	_name = "kg.service.order.expense.track"
	_description = "kg expense track"
	
	_columns = {
		
		## Basic Info
		
		'expense_id': fields.many2one('kg.service.order', 'Expense Track'),
		
		## Module Requirement Fields
		
		'name': fields.char('Number', size=128, select=True,readonly=False),
		'date': fields.date('Creation Date'),
		'company_id': fields.many2one('res.company', 'Company Name'),
		'description': fields.char('Description'),
		'expense_amt': fields.float('Amount'),
		
	}
	
	_defaults = {
		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.service.order.expense.entry', context=c),
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
	
		}
	
kg_service_order_expense_track()
