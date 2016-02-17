## KG Purchase Order ##

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
import socket
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
import logging


from tools import number_to_text_convert_india
logger = logging.getLogger('server')
today = datetime.now()

import urllib
import urllib2
import logging
import base64

class kg_purchase_order(osv.osv):
	
	def _amount_line_tax(self, cr, uid, line, context=None):
		logger.info('[KG OpenERP] Class: kg_purchase_order, Method: _amount_line_tax called...')
		val = 0.0
		new_amt_to_per = line.kg_discount / line.product_qty
		amt_to_per = (line.kg_discount / (line.product_qty * line.price_unit or 1.0 )) * 100
		kg_discount_per = line.kg_discount_per
		tot_discount_per = amt_to_per + kg_discount_per
		for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id,
			line.price_unit * (1-(tot_discount_per or 0.0)/100.0), line.product_qty, line.product_id,
				line.order_id.partner_id)['taxes']:
			 
			val += c.get('amount', 0.0)
		return val	
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		logger.info('[KG OpenERP] Class: kg_purchase_order, Method: _amount_all called...')
		res = {}
		cur_obj=self.pool.get('res.currency')
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'amount_untaxed': 0.0,
				'amount_tax': 0.0,
				'amount_total': 0.0,
				'discount' : 0.0,
				'other_charge': 0.0,
			}
			val = val1 = val3 = 0.0
			cur = order.pricelist_id.currency_id
			po_charges=order.value1 + order.value2
			pol = self.pool.get('purchase.order.line')
			for line in order.order_line:
				tot_discount = line.kg_discount + line.kg_discount_per_value
				val1 += line.price_subtotal
				#for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, order.partner_id)['taxes']:
				val += self._amount_line_tax(cr, uid, line, context=context)
				val3 += tot_discount
			res[order.id]['other_charge']= po_charges or 0
			res[order.id]['amount_tax']=(round(val,0))
			res[order.id]['amount_untaxed']=(round(val1,0)) - (round(val,0)) + (round(val3,0))
			res[order.id]['discount']=(round(val3,0))
			res[order.id]['amount_total']=res[order.id]['amount_untaxed'] - res[order.id]['discount'] + res[order.id]['amount_tax'] + res[order.id]['other_charge']
			
		return res
		
	def _get_order(self, cr, uid, ids, context=None):
		logger.info('[KG OpenERP] Class: kg_purchase_order, Method: _get_order called...')
		result = {}
		for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
			result[line.order_id.id] = True
		return result.keys()

	_name = "purchase.order"
	_inherit = "purchase.order"
	_order = "creation_date desc"

	_columns = {
		
		'po_type': fields.selection([('direct', 'Direct'),('frompi', 'From PI')], 'PO Type'),
		'bill_type': fields.selection([('cash','CASH BILL'),('credit','CREDIT BILL')], 'Bill Type',states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'po_expenses_type1': fields.selection([('freight','Freight Charges'),('others','Others')], 'Expenses Type1', readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'po_expenses_type2': fields.selection([('freight','Freight Charges'),('others','Others')], 'Expenses Type2', readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'value1':fields.float('Value1',readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'value2':fields.float('Value2',readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'note': fields.text('Remarks'),
		'vendor_bill_no': fields.float('Vendor.Bill.No',readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'vendor_bill_date': fields.date('Vendor.Bill.Date',readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'location_id': fields.many2one('stock.location', 'Destination', required=True, domain=[('usage','=','internal')], states={'approved':[('readonly',True)],'done':[('readonly',True)]} ),		
		'payment_term_id': fields.many2one('account.payment.term', 'Payment Term', readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'pricelist_id':fields.many2one('product.pricelist', 'Pricelist', states={'approved':[('readonly',True)],'done':[('readonly',True)]}, help="The pricelist sets the currency used for this purchase order. It also computes the supplier price for the selected products/quantities."),	
		'date_order': fields.date('PO Date',readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'payment_mode': fields.many2one('kg.payment.master', 'Mode of Payment', required=True,readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'delivery_type':fields.many2one('kg.deliverytype.master', 'Delivery Schedule',readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'delivery_mode': fields.many2one('kg.delivery.master','Delivery Type', required=True,readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'partner_address':fields.char('Supplier Address', size=128,readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'email':fields.char('Contact Email', size=128,readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'contact_person':fields.char('Contact Person', size=128),
		'other_charge': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Other Charges(+)',
			 multi="sums", help="The amount without tax", track_visibility='always'),		
		
		'discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Discount(-)',
			store={
				'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
				'purchase.order.line': (_get_order, ['price_unit', 'tax_id', 'kg_discount', 'product_qty'], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
			store={
				'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
				'purchase.order.line': (_get_order, ['price_unit', 'tax_id', 'kg_discount', 'product_qty'], 10),
			}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
			store=True, multi="sums", help="The tax amount"),
		'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Amount',
			 multi="sums", store=True, help="The amount without tax", track_visibility='always'),		
		'po_flag': fields.boolean('PO Flag'),
		'grn_flag': fields.boolean('GRN'),
		'kg_seq_id':fields.many2one('ir.sequence','Document Type',domain=[('code','=','purchase.order')],
			readonly=True, states={'draft': [('readonly', False)]}),
		'name': fields.char('PO NO', size=64, select=True,readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'user_id': fields.many2one('res.users', 'Created by'),
		'bill_flag':fields.boolean('PO Bill'),
		'amend_flag': fields.boolean('Amendment', select=True),
		'add_text': fields.text('Address',readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'type_flag':fields.boolean('Type Flag'),
		'pi_flag':fields.boolean('Type Flag'),
		'creation_date':fields.datetime('Creation Date'),
		'delivery_address':fields.text('Delivery Address',readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'term_price':fields.selection([('inclusive','Inclusive of all Taxes and Duties')], 'Price',readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}), 
		'term_warranty':fields.char('Warranty',readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'term_freight':fields.selection([('Inclusive','Inclusive'),('Extra','Extra'),('To Pay','To Pay'),('Paid','Paid'),
						  ('Extra at our Cost','Extra at our Cost')], 'Freight'), 
		'quot_ref_no':fields.char('Quot. Ref.',readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'dep_project_name':fields.char('Dept/Project Name',readonly=False),
		'dep_project':fields.many2one('kg.project.master','Dept/Project Name',readonly=False, states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
		'text_amt':fields.char('Amount in Words'),
		'confirmed_by':fields.many2one('res.users','Confirmed By',readonly=True),
		'confirmed_date':fields.datetime('Confirmed Date',readonly=True),
		'approved_by':fields.many2one('res.users','Approved By',readonly=True),
		'approved_date':fields.datetime('Approved Date',readonly=True),
		'confirm_flag':fields.boolean('Confirm Flag'),
		'approve_flag':fields.boolean('Expiry Flag'),
		'frieght_flag':fields.boolean('Expiry Flag'),
		'version':fields.char('Version'),
		'purpose':fields.selection([('for_sale','For Sale'),('own_use','Own use')], 'Purpose'), 
		
	}
	
	_defaults = {
	
	'bill_type' :'credit',
	'date_order': fields.date.context_today,
	'po_type': 'frompi',
	'name': lambda self, cr, uid, c: self.pool.get('purchase.order').browse(cr, uid, id, c).id,
	'user_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id,
	'creation_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
	'confirm_flag':False,
	'approve_flag':False,
	'frieght_flag':False,
	'version':'00',
	'pricelist_id': 2,
	
	}
	
	def email_ids(self,cr,uid,ids,context = None):
		email_from = []
		email_to = []
		email_cc = []
		val = {'email_from':'','email_to':'','email_cc':''}
		ir_model = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		mail_form_ids = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		for ids in mail_form_ids:
			mail_form_rec = self.pool.get('kg.mail.settings').browse(cr,uid,ids)
			if mail_form_rec.doc_name.model == 'purchase.order':
				email_from.append(mail_form_rec.name)
				mail_line_id = self.pool.get('kg.mail.settings.line').search(cr,uid,[('line_entry','=',ids)])
				for mail_id in mail_line_id:
					mail_line_rec = self.pool.get('kg.mail.settings.line').browse(cr,uid,mail_id)
					if mail_line_rec.to_address:
						email_to.append(mail_line_rec.mail_id)
					if mail_line_rec.cc_address:
						email_cc.append(mail_line_rec.mail_id)
			else:
				pass		
		val['email_from'] = email_from
		val['email_to'] = email_to
		val['email_cc'] = email_cc
		return val
	
	def sechedular_email_ids(self,cr,uid,ids,context = None):
		email_from = []
		email_to = []
		email_cc = []
		val = {'email_from':'','email_to':'','email_cc':''}
		ir_model = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		mail_form_ids = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		for ids in mail_form_ids:
			mail_form_rec = self.pool.get('kg.mail.settings').browse(cr,uid,ids)
			if mail_form_rec.sch_type == 'scheduler':
				s = mail_form_rec.sch_name
				s = s.lower()
				if s == 'po register':
					email_sub = mail_form_rec.subject
					email_from.append(mail_form_rec.name)
					mail_line_id = self.pool.get('kg.mail.settings.line').search(cr,uid,[('line_entry','=',ids)])
					for mail_id in mail_line_id:
						mail_line_rec = self.pool.get('kg.mail.settings.line').browse(cr,uid,mail_id)
						if mail_line_rec.to_address:
							email_to.append(mail_line_rec.mail_id)
						if mail_line_rec.cc_address:
							email_cc.append(mail_line_rec.mail_id)
		val['email_from'] = email_from
		val['email_to'] = email_to
		val['email_cc'] = email_cc
		return val
	
	def create(self, cr, uid, vals,context=None):
		"""inv_seq = vals['kg_seq_id']
		next_seq_num = self.pool.get('ir.sequence').kg_get_id(cr, uid, inv_seq,'id',{'noupdate':False})
		print "next_seq_num...........................", next_seq_num
		vals.update({
						'name':next_seq_num,
						
						})"""
		
		order =  super(kg_purchase_order, self).create(cr, uid, vals, context=context)
		return order
	
	
	def onchange_seq_id(self, cr, uid, ids, kg_seq_id,name):
		print "kgggggggggggggggggg --  onchange_seq_id called"		
		"""value = {'name':''}
		if kg_seq_id:
			next_seq_num = self.pool.get('ir.sequence').kg_get_id(cr, uid, kg_seq_id,'id',{'noupdate':False})
			print "next_seq_num:::::::::::", next_seq_num
			value = {'name': next_seq_num}"""
		return True
		
	def onchange_type_flag(self, cr, uid, ids, po_type):
		value = {'type_flag':False}
		if po_type == 'direct':
			value = {'type_flag': True}
		else:
			value = {'pi_flag': True}
		return {'value': value}
		
		
	### Back Entry Date #####	
		
	def onchange_date_order(self, cr, uid, ids, date_order):
		today_date = today.strftime('%Y-%m-%d')
		back_list = []
		today_new = today.date()
		bk_date = date.today() - timedelta(days=2)
		back_date = bk_date.strftime('%Y-%m-%d')
		d1 = today_new
		d2 = bk_date
		delta = d1 - d2
		for i in range(delta.days + 1):
			bkk_date = d1 - timedelta(days=i)
			backk_date = bkk_date.strftime('%Y-%m-%d')
			back_list.append(backk_date)
		holiday_obj = self.pool.get('kg.holiday.master.line')
		holiday_ids = holiday_obj.search(cr, uid, [('leave_date','in',back_list)])
		if date_order > today_date:
			raise osv.except_osv(
					_('Warning'),
					_('PO Date should be less than or equal to current date!'))	
		if holiday_ids:
			hol_bk_date = date.today() - timedelta(days=(2+len(holiday_ids)))
			hol_back_date = hol_bk_date.strftime('%Y-%m-%d')
			if date_order < hol_back_date:
				raise osv.except_osv(
					_('Warning'),
					_('PO Entry is not allowed for this date!'))
		elif (x for x in back_list if calendar.day_name[x.weekday()]  == 'Sunday'):
			hol_bk_date = date.today() - timedelta(days=3)
			hol_back_date = hol_bk_date.strftime('%Y-%m-%d')
			if date_order < hol_back_date:
				raise osv.except_osv(
					_('Warning'),
					_('PO Entry is not allowed for this date!'))
		else:
			if date_order <= back_date:
				raise osv.except_osv(
					_('Warning'),
					_('PO Entry is not allowed!'))
		return True
		
		
		
	def onchange_frieght_flag(self, cr, uid, ids, term_freight):
		value = {'frieght_flag':False}
		if term_freight == 'Extra':
			value = {'frieght_flag': True}
		return {'value': value}
	
	
	def onchange_partner_id(self, cr, uid, ids, partner_id,add_text):
		logger.info('[KG OpenERP] Class: kg_purchase_order, Method: onchange_partner_id called...')
		partner = self.pool.get('res.partner')
		if not partner_id:
			return {'value': {
				'fiscal_position': False,
				'payment_term_id': False,
				}}
		supplier_address = partner.address_get(cr, uid, [partner_id], ['default'])
		supplier = partner.browse(cr, uid, partner_id)
		tot_add = (supplier.street or '')+ ' ' + (supplier.street2 or '') + '\n'+(supplier.city_id.name or '')+ ',' +(supplier.state_id.name or '') + '-' +(supplier.zip or '') + '\nPh:' + (supplier.phone or '')+ '\n' +(supplier.mobile or '')		
		return {'value': {
			'pricelist_id': supplier.property_product_pricelist_purchase.id,
			'fiscal_position': supplier.property_account_position and supplier.property_account_position.id or False,
			'payment_term_id': supplier.property_supplier_payment_term.id or False,
			'add_text' : tot_add or False
			}}
			
	def onchange_user(self, cr, uid, ids, user_id,location_id):
		value = {'location_id': ''}
		if user_id:			
			user_obj = self.pool.get('res.users')
			user_rec = user_obj.browse(cr,uid,user_id)
			dep_rec = user_rec.dep_name
			location = dep_rec.main_location.id
			value = {'location_id': location}
		return {'value':value}
		
	def confirm_po(self,cr,uid,ids, context=None):
		print "POOOOO Confirm"
		back_list = []
		obj = self.browse(cr,uid,ids[0])
		
		date_order = obj.date_order
		date_order1 = datetime.strptime(date_order, '%Y-%m-%d')
		date_order1 = datetime.date(date_order1)
		today_date = datetime.date(today)
		today_new = today.date()
		bk_date = date.today() - timedelta(days=2)
		back_date = bk_date.strftime('%Y-%m-%d')
		d1 = today_new
		d2 = bk_date
		delta = d1 - d2
		for i in range(delta.days + 1):
			bkk_date = d1 - timedelta(days=i)
			backk_date = bkk_date.strftime('%Y-%m-%d')
			back_list.append(backk_date)
		holiday_obj = self.pool.get('kg.holiday.master.line')
		holiday_ids = holiday_obj.search(cr, uid, [('leave_date','in',back_list)])
		sql = """ select id,name,date_order from purchase_order where state != 'draft' and state != 'cancel 'order by id desc limit 1 """
		cr.execute(sql)
		data = cr.dictfetchall()
		if date_order1 > today_date:
			raise osv.except_osv(
					_('Warning'),
					_('PO Date should be less than or equal to current date!'))
		if data:
			if data[0]['date_order'] > date_order:
				raise osv.except_osv(
					_('Warning'),
					_('Current PO Date should be greater than or equal to Previous PO date!'))				
			
		if holiday_ids:
			hol_bk_date = date.today() - timedelta(days=(2+len(holiday_ids)))
			hol_back_date = hol_bk_date.strftime('%Y-%m-%d')
			if date_order < hol_back_date:
				raise osv.except_osv(
					_('Warning'),
					_('PO Entry is not allowed for this date!'))
		elif (x for x in back_list if calendar.day_name[x.weekday()]  == 'Sunday'):
			hol_bk_date = date.today() - timedelta(days=3)
			hol_back_date = hol_bk_date.strftime('%Y-%m-%d')
			if date_order < hol_back_date:
				raise osv.except_osv(
					_('Warning'),
					_('PO Entry is not allowed for this date!'))		
		else:
			if date_order <= back_date:
				raise osv.except_osv(
					_('Warning'),
					_('PO Entry is not allowed!'))
		if obj.name == False:
			po_no = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order')
			self.write(cr,uid,ids,{'name':po_no})
		"""if obj.frieght_flag == True and obj.value1 == 0.00: 
			raise osv.except_osv(
					_('Warning'),
					_('You should specify Frieght charges!'))"""
		for i in obj.order_line:
			if not i.pi_line_id:
				raise osv.except_osv(_('PO From PI Only!'),_("You must select a PO lines From PI !") )
		if obj.amount_total <= 0:
			raise osv.except_osv(
					_('Purchase Order Value Error !'),
					_('System not allow to confirm a Purchase Order with Zero Value'))	
		for order_line in obj.order_line:
			product_tax_amt = self._amount_line_tax(cr, uid, order_line, context=context)
			cr.execute("""update purchase_order_line set product_tax_amt = %s where id = %s"""%(product_tax_amt,order_line.id))
		self.write(cr, uid, ids, {'state': 'confirmed',
								  'confirm_flag':'True',
								  'confirmed_by':uid,
								  'confirmed_date':today})
		#cr.execute("""select all_transaction_mails('Purchase Order Approval',%s)"""%(ids[0]))
		"""Raj
		data = cr.fetchall();
		vals = self.email_ids(cr,uid,ids,context = context)
		if (not vals['email_to']) and (not vals['email_cc']):
			pass
		else:
			ir_mail_server = self.pool.get('ir.mail_server')
			msg = ir_mail_server.build_email(
					email_from = vals['email_from'][0],
					email_to = vals['email_to'],
					subject = "	Purchase Order - Waiting For Approval",
					body = data[0][0],
					email_cc = vals['email_cc'],
					object_id = ids[0] and ('%s-%s' % (ids[0], 'purchase.order')),
					subtype = 'html',
					subtype_alternative = 'plain')
			res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
		"""
		return True
			
	def wkf_approve_order(self, cr, uid, ids, context=None):
		logger.info('[KG OpenERP] Class: kg_purchase_order, Method: wkf_approve_order called...')
		obj = self.browse(cr,uid,ids[0])
		"""Raj
		if obj.confirmed_by.id == uid:
			raise osv.except_osv(
					_('Warning'),
					_('Approve cannot be done by Confirmed user'))
		else:
		"""
		if obj.payment_mode.term_category == 'advance':
			cr.execute("""select * from kg_po_advance where state='approved' and po_id= %s"""  %(str(ids[0])))
			data = cr.dictfetchall()
			if not data:
				raise osv.except_osv(
					_('Warning'),
					_('Advance is mandate for this PO'))
			else:
				pass		
		print obj.order_line
		text_amount = number_to_text_convert_india.amount_to_text_india(obj.amount_total,"INR:")
		self.write(cr,uid,ids[0],{'text_amt':text_amount})
		line_obj = self.pool.get('purchase.order.line')
		line_rec = line_obj.search(cr, uid, [('order_id','=',obj.id)])
		for order_line in line_rec:
			order_line_rec = line_obj.browse(cr, uid, order_line)
			product_tax_amt = self._amount_line_tax(cr, uid, order_line_rec, context=context)
			cr.execute("""update purchase_order_line set product_tax_amt = %s where id = %s"""%(product_tax_amt,order_line_rec.id))
			line_obj.write(cr,uid,order_line,{'cancel_flag':'True','line_flag':'True'})
				
		self.write(cr, uid, ids, {'state': 'approved', 'date_approve': fields.date.context_today(self,cr,uid,context=context),'order_line.line_state' : 'confirm'})
		self.write(cr, uid, ids, {'approve_flag':'True',
								  'approved_by':uid,
								  'approved_date':today})
								  
		po_order_obj=self.pool.get('purchase.order')
		po_id=obj.id
		po_lines = obj.order_line
		cr.execute("""select piline_id from kg_poindent_po_line where po_order_id = %s"""  %(str(ids[0])))
		data = cr.dictfetchall()
		val = [d['piline_id'] for d in data if 'piline_id' in d] # Get a values form list of dict if the dict have with empty values
		for i in range(len(po_lines)):
			if obj.po_type == 'frompi':
				if po_lines[i].pi_line_id and po_lines[i].group_flag == False:
					pi_line_id=po_lines[i].pi_line_id
					product = po_lines[i].product_id.name
					po_qty=po_lines[i].product_qty
					po_pending_qty=po_lines[i].pi_qty
					pi_pending_qty= po_pending_qty - po_qty
					if po_qty > po_pending_qty:
						raise osv.except_osv(
						_('If PO from Purchase Indent'),
						_('PO Qty should not be greater than purchase indent Qty. You can raise this PO Qty upto %s --FOR-- %s.'
									%(po_pending_qty, product)))
													
					pi_obj=self.pool.get('purchase.requisition.line')
					pi_line_obj=pi_obj.search(cr, uid, [('id','=',val[i])])
					pi_obj.write(cr,uid,pi_line_id.id,{'draft_flag' : False})
					sql = """ update purchase_requisition_line set pending_qty=%s where id = %s"""%(pi_pending_qty,pi_line_id.id)
					cr.execute(sql)
					
					if pi_pending_qty == 0:
						pi_obj.write(cr,uid,pi_line_id.id,{'line_state' : 'noprocess'})
					
					if po_lines[i].group_flag == True:
							self.update_product_pending_qty(cr,uid,ids,line=po_lines[i])
					else:
						print "All are correct Values and working fine"
			else:
				# Tax Updation #
				tax_struct_obj =  self.pool.get('kg.tax.structure')
				if po_lines[i].tax_structure_id:
					stru_rec = tax_struct_obj.browse(cr, uid,po_lines[i].tax_structure_id.id)					
					for line in stru_rec.tax_line:
						tax_id = line.tax_id.id
						sql = """ insert into purchase_order_taxe (ord_id,tax_id) VALUES(%s,%s) """ %(po_lines[i].id,tax_id)
						cr.execute(sql)
					
				line_obj.write(cr,uid,po_lines[i].id,{'pending_qty':po_lines[i].product_qty})
				
		#self.send_email(cr,uid,ids)
		#cr.execute("""select all_transaction_mails('Purchase Order Approval',%s)"""%(ids[0]))
		"""Raj
		data = cr.fetchall();
		vals = self.email_ids(cr,uid,ids,context = context)
		if (not vals['email_to']) and (not vals['email_cc']):
			pass
		else:
			ir_mail_server = self.pool.get('ir.mail_server')
			msg = ir_mail_server.build_email(
					email_from = vals['email_from'][0],
					email_to = vals['email_to'],
					subject = "	Purchase Order - Approved",
					body = data[0][0],
					email_cc = vals['email_cc'],
					object_id = ids[0] and ('%s-%s' % (ids[0], 'purchase.order')),
					subtype = 'html',
					subtype_alternative = 'plain')
			res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
		return True
		cr.close()
		"""
	def po_register_scheduler(self,cr,uid,ids=0,context = None):
		cr.execute(""" SELECT current_database();""")
		db = cr.dictfetchall()
		if db[0]['current_database'] == 'Empereal-KGDS':
			db[0]['current_database'] = 'Empereal-KGDS'
		elif db[0]['current_database'] == 'FSL':
			db[0]['current_database'] = 'FSL'
		elif db[0]['current_database'] == 'IIM':
			db[0]['current_database'] = 'IIM'
		elif db[0]['current_database'] == 'IIM_HOSTEL':
			db[0]['current_database'] = 'IIM Hostel'
		elif db[0]['current_database'] == 'KGISL-SD':
			db[0]['current_database'] = 'KGISL-SD'
		elif db[0]['current_database'] == 'CHIL':
			db[0]['current_database'] = 'CHIL'
		elif db[0]['current_database'] == 'KGCAS':
			db[0]['current_database'] = 'KGCAS'
		elif db[0]['current_database'] == 'KGISL':
			db[0]['current_database'] = 'KGISL'
		elif db[0]['current_database'] == 'KITE':
			db[0]['current_database'] = 'KITE'
		elif db[0]['current_database'] == 'TRUST':
			db[0]['current_database'] = 'TRUST'
		elif db[0]['current_database'] == 'CANTEEN':
			db[0]['current_database'] = 'CANTEEN'
		else:
			db[0]['current_database'] = 'Others'
		
		line_rec = self.pool.get('purchase.order').search(cr, uid, [('state','in',('confirmed','approved')),('date_approve','=',time.strftime('%Y-%m-%d'))])
		
		
		print "---------------------------->",line_rec
		

		
		if line_rec:
			
			cr.execute("""select all_daily_auto_scheduler_mails('PO Register')""")
			data = cr.fetchall();
			cr.execute("""select trim(TO_CHAR(round(sum(amount_total),2)::float, '999G999G99G999G99G99G990D99')) as sum
							from purchase_order where 	
							to_char(purchase_order.date_order,'dd-mm-yyyy') = '%s' and
							purchase_order.state in ('approved')"""%(time.strftime('%d-%m-%Y')))
			total_sum = cr.dictfetchall();
			
			db = db[0]['current_database'].encode('utf-8')
			total_sum = str(total_sum[0]['sum'])
			vals = self.sechedular_email_ids(cr,uid,ids,context = context)
			if (not vals['email_to']) and (not vals['email_cc']):
				pass
			else:
				
				
					
				ir_mail_server = self.pool.get('ir.mail_server')
				msg = ir_mail_server.build_email(
						email_from = vals['email_from'][0],
						email_to = vals['email_to'],
						subject = "ERP Purchase Order Register Details for "+db +' on '+time.strftime('%d-%m-%Y')+' Total Amount (Rs.):' + total_sum,
						body = data[0][0],
						email_cc = vals['email_cc'],
						object_id = ids and ('%s-%s' % (ids, 'kg.purchase.order')),
						subtype = 'html',
						subtype_alternative = 'plain')
				res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
		else:
			pass			
					
		return True
		
	def poindent_line_move(self, cr, uid,ids, poindent_lines , context=None):
		logger.info('[KG OpenERP] Class: kg_purchase_order, Method: poindent_line_move called...')
		return {}
		
	def _create_pickings(self, cr, uid, order, order_lines, picking_id=False, context=None):
		logger.info('[KG OpenERP] Class: kg_purchase_order, Method: _create_pickings called...')
		return {}
		# Default Openerp workflow stopped and inherited the function
		
	def action_cancel(self, cr, uid, ids, context=None):
		logger.info('[KG OpenERP] Class: kg_purchase_order, Method: action_cancel called...')
		wf_service = netsvc.LocalService("workflow")
		product_obj = self.pool.get('product.product')
		pi_line_obj = self.pool.get('purchase.requisition.line')
		po_grn_obj = self.pool.get('kg.po.grn')
	
		purchase = self.browse(cr, uid, ids[0], context=context)
		
		if purchase.state == 'approved': 
		
			cr.execute(""" select grn_id from multiple_po where po_id = %s """ %(ids[0]))
			multi_po = cr.dictfetchall()
			
			
			if multi_po:
				for pick in multi_po:
					pick = po_grn_obj.browse(cr, uid, pick['grn_id'])
					if pick.state not in ('draft','cancel'):
						raise osv.except_osv(
							_('Unable to cancel this purchase order.'),
							_('First cancel all GRN related to this purchase order.'))
				
			for line in purchase.order_line:
				if line.pi_line_id and line.group_flag == False:
							pi_obj=self.pool.get('purchase.requisition.line')
							pi_line_obj=pi_obj.search(cr, uid, [('id','=',line.pi_line_id.id)])
							orig_pending_qty = line.pi_line_id.pending_qty
							po_qty = line.product_qty
							orig_pending_qty += po_qty
							sql = """ update purchase_requisition_line set pending_qty=%s where id = %s"""%(orig_pending_qty,line.pi_line_id.id)
							cr.execute(sql)
				else:
					if line.pi_line_id and line.group_flag == True:
						cr.execute(""" select piline_id from kg_poindent_po_line where po_order_id = %s """ %(str(ids[0])))
						data = cr.dictfetchall()
						val = [d['piline_id'] for d in data if 'piline_id' in d] 
						product_id = line.product_id.id
						product_record = product_obj.browse(cr, uid, product_id)
						list_line = pi_line_obj.search(cr,uid,[('id', 'in', val), ('product_id', '=', product_id)],context=context)
						po_used_qty = line.product_qty
						orig_pi_qty = line.group_qty
						for i in list_line:
							bro_record = pi_line_obj.browse(cr, uid,i)
							pi_pen_qty = bro_record.pending_qty
							pi_qty = orig_pi_qty + pi_pen_qty
							orig_pi_qty +=pi_pen_qty
							po_qty = po_used_qty
													 
							if po_qty < pi_qty:
								pi_qty = pi_pen_qty + po_qty
								sql = """ update purchase_requisition_line set pending_qty=%s where id = %s"""%(pi_qty,bro_record.id)
								cr.execute(sql)
								break		
							
							else:
								remain_qty = po_used_qty - orig_pi_qty
								sql = """ update purchase_requisition_line set pending_qty=%s where id = %s"""%(orig_pi_qty,bro_record.id)
								cr.execute(sql)
								if remain_qty < 0:
									break
								po_used_qty = remain_qty
								orig_pi_qty = pi_pen_qty + remain_qty
		
		else:
			for line in purchase.order_line:
				pi_line_obj.write(cr,uid,line.pi_line_id.id,{'line_state' : 'noprocess'})		
		"""		
		for inv in purchase.invoice_ids:
			
			if inv:
				wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_cancel', cr)
				"""
		if not purchase.notes:
			raise osv.except_osv(
						_('Remarks Needed !!'),
						_('Enter remark in Remarks Tab....'))
		else:
			self.write(cr,uid,ids,{'state':'cancel'})
		for (id, name) in self.name_get(cr, uid, ids):
			wf_service.trg_validate(uid, 'purchase.order', id, 'purchase_cancel', cr)
		return True			
	
	def kg_email_attachment(self,cr,uid,ids,context=None):
		ir_model_data = self.pool.get('ir.model.data')
		email_tmp_obj = self.pool.get('email.template')
		att_obj = self.pool.get('ir.attachment')
		#template = email_tmp_obj.get_email_template(cr, uid, template_id, ids, context)
		template = email_tmp_obj.browse(cr, uid, 8)
		report_xml_pool = self.pool.get('ir.actions.report.xml')		
		attachments = []
		# Add report in attachments				
		if template.report_template:
			report_name = email_tmp_obj.render_template(cr, uid, template.report_name, template.model, ids, context=context)
			report_service = 'report.' + report_xml_pool.browse(cr, uid, template.report_template.id, context).report_name
			# Ensure report is rendered using template's language
			ctx = context.copy()
			if template.lang:
				ctx['lang'] = email_tmp_obj.render_template(cr, uid, template.lang, template.model, ids, context)
			service = netsvc.LocalService(report_service)
			
			(result, format) = service.create(cr, uid, ids, {'model': template.model}, ctx)
			result = base64.b64encode(result)
			attachment_id = att_obj.create(cr, uid,
                    {
                        'name': 'PO.pdf',
                        'datas': result,
                        'datas_fname': 'PO_Confirmation.pdf',
                        'res_model': self._name,
                        'res_id': ids[0],
                        'type': 'binary'
                    }, context=context)
			self.send_mail(cr,uid,ids,attachment_id,template,context)
			
	def send_mail(self, cr, uid, ids,attachment_id,template,context=None):
		
		ir_attachment_obj = self.pool.get('ir.attachment')
		rec = self.pool.get('purchase.order').browse(cr, uid, ids[0])
		sub = ""
		email_from = []
		email_to = []
		email_cc = []
		ir_model = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		#to_mails = []
		#hr_mail_id = '' 
		mail_form_ids = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		for ids in mail_form_ids:
			mail_form_rec = self.pool.get('kg.mail.settings').browse(cr,uid,ids)
			if mail_form_rec.doc_name.model == 'purchase.order':
				email_from.append(mail_form_rec.name)
				mail_line_id = self.pool.get('kg.mail.settings.line').search(cr,uid,[('line_entry','=',ids)])
				for mail_id in mail_line_id:
					mail_line_rec = self.pool.get('kg.mail.settings.line').browse(cr,uid,mail_id)
					if mail_line_rec.to_address:
						email_to.append(mail_line_rec.mail_id)
					if mail_line_rec.cc_address:
						email_cc.append(mail_line_rec.mail_id)
		if isinstance(self.browse(cr, uid, ids, context=context),list):
			var = self.browse(cr, uid, ids, context=context)
		else:
			var = [self.browse(cr, uid, ids, context=context)]
		
		for wizard in var:
			active_model_pool_name = 'purchase.order'
			active_model_pool = self.pool.get(active_model_pool_name)		
			
			# wizard works in batch mode: [res_id] or active_ids
			if isinstance(ids,int):
				res_ids = [ids]
			else:
				res_ids = ids
			for res_id in res_ids:			
				attach = ir_attachment_obj.browse(cr,uid,attachment_id)
				attachments = []
				attachments.append((attach.datas_fname, base64.b64decode(attach.datas)))
				ir_mail_server = self.pool.get('ir.mail_server')
				msg = ir_mail_server.build_email(
		                email_from = " ".join(str(x) for x in email_from),
		                email_to = email_to,
		                subject = template.subject + "  " +sub,
		                body = template.body_html,
		                email_cc = email_cc,
		                attachments = attachments,
		                object_id = res_id and ('%s-%s' % (res_id, 'purchase.order')),
		                subtype = 'html',
		                subtype_alternative = 'plain')
				res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)			
		return True

			
	def _check_line(self, cr, uid, ids, context=None):
		logger.info('[KG ERP] Class: kg_purchase_order, Method: _check_line called...')
		for po in self.browse(cr,uid,ids):
			if po.po_type != 'direct': 
				if po.kg_poindent_lines==[]:
					tot = 0.0
					for line in po.order_line:
						tot += line.price_subtotal
					if tot <= 0.0 or po.amount_total <=0:			
						return False
				return True
			
	def _check_total(self, cr, uid, ids, context=None):		
		po_rec = self.browse(cr, uid, ids[0])
		if po_rec.kg_seq_id:
			for line in po_rec.order_line:				
				if line.price_subtotal <= 0:
					return False					
		return True
			
	_constraints = [
	
		#(_check_line,'You can not save this Purchase Order with out Line and Zero Qty !',['order_line']),
		#(_check_total,'You can not save this Purchase Order with Zero value !',['order_line']),
	
	]
	
	def print_quotation(self, cr, uid, ids, context=None):		
		assert len(ids) == 1, 'This option should only be used for a single id at a time'
		wf_service = netsvc.LocalService("workflow")
		wf_service.trg_validate(uid, 'purchase.order', ids[0], 'send_rfq', cr)
		datas = {
				 'model': 'purchase.order',
				 'ids': ids,
				 'form': self.read(cr, uid, ids[0], context=context),
		}
		#print "datas ------------------------", datas
		return {'type': 'ir.actions.report.xml', 'report_name': 'onscreen.po.report', 'datas': datas, 'ids' : ids, 'nodestroy': True}
	
kg_purchase_order()


class kg_purchase_order_line(osv.osv):
	
	def onchange_discount_value_calc(self, cr, uid, ids, kg_discount_per, product_qty, price_unit):
		logger.info('[KG OpenERP] Class: kg_purchase_order_line, Method: onchange_discount_value_calc called...')
		discount_value = (product_qty * price_unit) * kg_discount_per / 100.00
		print "discount_value ------------------------->>>>", discount_value
		return {'value': {'kg_discount_per_value': discount_value }}
		
	def onchange_disc_amt(self,cr,uid,ids,kg_discount,product_qty,price_unit,kg_disc_amt_per):
		logger.info('[KG OpenERP] Class: kg_purchase_order_line, Method: onchange_disc_amt called...')
		if kg_discount:
			print "kg_discount..........", 
			kg_discount = kg_discount + 0.00
			amt_to_per = (kg_discount / (product_qty * price_unit or 1.0 )) * 100.00
			print "amt_to_peramt_to_peramt_to_per*******************", amt_to_per
			return {'value': {'kg_disc_amt_per': amt_to_per}}	
		else:
			return {'value': {'kg_disc_amt_per': 0.0}}	
	
	def _amount_line(self, cr, uid, ids, prop, arg, context=None):
		logger.info('[KG OpenERP] Class: kg_purchase_order_line, Method: _amount_line called...')
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
			taxes = tax_obj.compute_all(cr, uid, line.taxes_id, price, line.product_qty, line.product_id, line.order_id.partner_id)
			cur = line.order_id.pricelist_id.currency_id
			res[line.id] = taxes['total_included']
		return res
		
	_name = "purchase.order.line"
	_inherit = "purchase.order.line"
	
	_columns = {

	'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
	'kg_discount': fields.float('Discount Amount'),
	'kg_disc_amt_per': fields.float('Disc Amt(%)', digits_compute= dp.get_precision('Discount')),
	'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price')),
	'product_qty': fields.float('Quantity'),
	'pending_qty': fields.float('Pending Qty'),
	'received_qty':fields.float('Received Qty'),
	'tax_amt':fields.float('tax amt'),
	'cancel_qty':fields.float('Cancel Qty'),
	'pi_qty':fields.float('PI Qty'),
	'group_qty':fields.float('Group Qty'),
	'product_uom': fields.many2one('product.uom', 'UOM', readonly=True),
	'name': fields.text('Description'),
	'date_planned': fields.date('Scheduled Date', select=True),
	'note': fields.text('Remarks'),
	'pi_line_id':fields.many2one('purchase.requisition.line','PI Line'),
	'po_order':fields.one2many('kg.po.line','line_id','PO order Line'),
	'kg_discount_per': fields.float('Discount (%)', digits_compute= dp.get_precision('Discount')),
	'kg_discount_per_value': fields.float('Discount(%)Value', digits_compute= dp.get_precision('Discount')),
	'line_state': fields.selection([('draft', 'Active'),('confirm','Confirmed'),('cancel', 'Cancel')], 'State'),
	'group_flag': fields.boolean('Group By'),
	'total_disc': fields.float('Discount Amt'),
	'line_bill': fields.boolean('PO Bill'),
	'tax_structure_id':fields.many2one('kg.tax.structure', 'Tax Structure',
			domain="[('state','=','app'),'&',('type','=','po')]"),
	'cancel_remark':fields.text('Cancel Remarks'),
	'cancel_flag':fields.boolean('Cancel Flag'),
	'move_line_id':fields.many2one('stock.move','Move Id'),
	'line_flag':fields.boolean('Line Flag'),
	'po_specification':fields.text('Specification'),
	'product_tax_amt':fields.float('Tax Amount'),
	'brand_id':fields.many2one('kg.brand.master','Brand'),

	
	}
	
	_defaults = {
	
	'date_planned' : fields.date.context_today,
	'line_state' : 'draft',
	'name':'PO',
	'cancel_flag': False
	
	}
	
	def create(self, cr, uid, vals,context=None):
		if vals['product_id']:
			product_obj =  self.pool.get('product.product')
			product_rec = product_obj.browse(cr,uid,vals['product_id'])
			if product_rec.uom_id.id != product_rec.uom_po_id.id:
				vals.update({
							'product_uom':product_rec.uom_po_id.id,
							})
			elif  product_rec.uom_id.id == product_rec.uom_po_id.id:
				vals.update({
							'product_uom':product_rec.uom_id.id,
							})
		order =  super(kg_purchase_order_line, self).create(cr, uid, vals, context=context)
		return order
	
	def get_taxes_structure(self,cr,uid,struct_id):		
		logger.info('[KG OpenERP] Class: kg_purchase_order_line, Method: get_taxes_structure called...')
		if isinstance(struct_id,int):
			tax_struct_obj =  self.pool.get('kg.tax.structure')
			tax_struct_browse = tax_struct_obj.browse(cr,uid,struct_id)
			tax_ids  = map(lambda x:{'tax_id':x.tax_id.id},tax_struct_browse.tax_line)
			return tax_ids
		return []
		
	def onchange_tax_structure(self, cr, uid,ids, tax_structure_id):
		if ids:
			tax_struct_obj =  self.pool.get('kg.tax.structure')
			sql_check = """ select tax_id from purchase_order_taxe where ord_id=%s """ %(ids[0])
			cr.execute(sql_check)
			data = cr.dictfetchall()
			if data:
				del_sql = """ delete from purchase_order_taxe where ord_id=%s """ %(ids[0])
				cr.execute(del_sql)
			if tax_structure_id:
				stru_rec = tax_struct_obj.browse(cr, uid,tax_structure_id)					
				for line in stru_rec.tax_line:
					tax_id = line.tax_id.id
					sql = """ insert into purchase_order_taxe (ord_id,tax_id) VALUES(%s,%s) """ %(ids[0],tax_id)
					cr.execute(sql)
		else:
			pass
			
		return True
	
	def onchange_qty(self, cr, uid, ids,product_qty,pending_qty,pi_line_id,pi_qty):
		logger.info('[KG OpenERP] Class: kg_purchase_order_line, Method: onchange_qty called...')
		if pi_line_id == False:
			raise osv.except_osv(_('PO From PI Only!'),_("You must select a PO lines From PI !") )
		# Need to do block flow
		value = {'pending_qty': ''}
		if product_qty and product_qty > pi_qty:
			raise osv.except_osv(_(' If PO From PI !!'),_("PO Qty can not be greater than Indent Qty !") )
		
		else:
			value = {'pending_qty': product_qty}
		return {'value': value}
		
	def pol_cancel(self, cr, uid, ids, context=None):
		logger.info('[KG OpenERP] Class: kg_purchase_order_line, Method: pol_cancel called...')
		line_rec = self.browse(cr,uid,ids)
		
		if line_rec[0].product_qty != line_rec[0].pending_qty:
			raise osv.except_osv(
				_('Few Quanties are Received !! '),
				_('You can cancel a PO line before receiving product'))
				
		if not line_rec[0].cancel_remark:
			
			raise osv.except_osv(
				_('Remarks !! '),
				_('Enter the remarks for po line cancel'))
		else:				
			self.write(cr,uid,ids,{'line_state':'cancel'})
		return True

			
	def unlink(self, cr, uid, ids, context=None):
		print "Purchase order line unlink method calling--->>", ids
		if context is None:
			context = {}
		for rec in self.browse(cr, uid, ids, context=context):
			print "rec ===================>>>>>", rec, "context====>", context
			parent_rec = rec.order_id
			print "parent_rec.state", parent_rec.state
			if parent_rec.state not in ['draft']:
				print "iffffffffffff"
				raise osv.except_osv(_('Invalid Action!'), _('Cannot delete a purchase order line which is in state \'%s\'.') %(parent_rec.state,))
			else:
				order_id = parent_rec.id
				pi_line_rec = rec.pi_line_id
				pi_line_id = rec.pi_line_id.id
				pi_line_rec.write({'line_state' : 'process','draft_flag':False})
				del_sql = """ delete from kg_poindent_po_line where po_order_id=%s and piline_id=%s """ %(order_id,pi_line_id)
				cr.execute(del_sql)				
				return super(kg_purchase_order_line, self).unlink(cr, uid, ids, context=context)
				
	def get_old_details(self,cr,uid,ids,context=None):
		print "ids..................",ids
		rec = self.browse(cr, uid, ids[0])
		last_obj = self.pool.get('kg.po.line')
		print "rec............................", rec.product_id.id		
		sql = """ select id,price_unit,order_id,kg_discount,kg_discount_per,tax_structure_id from purchase_order_line where product_id=%s and order_id != %s order by id desc limit 5 """%(rec.product_id.id,rec.order_id.id)
		cr.execute(sql)
		data = cr.dictfetchall()
		print "data.......................", data
		
		last_ids = last_obj.search(cr, uid, [('line_id','=',rec.id)])
		print "last_ids............>>>",last_ids
		if last_ids:
			for i in last_ids:
				last_obj.unlink(cr, uid, i, context=context)
		for item in data:
			print "item....................", item
			po_rec = self.pool.get('purchase.order').browse(cr,uid,item['order_id'])
			print "po_rec......................", po_rec
			
			vals = {
			
				'line_id':item['id'],
				'supp_name':po_rec.partner_id.id,
				'date_order':po_rec.date_order,
				'tax':item['tax_structure_id'],
				'other_ch':po_rec.other_charge,
				'kg_discount':item['kg_discount'],
				'kg_discount_per':item['kg_discount_per'],
				'price_unit':item['price_unit']
			
			
			}
			
			print "price..........",vals
			
			po_entry = self.write(cr,uid,rec.id,{'po_order':[(0,0,vals)]})
	
		return data
			
			
			
		
	
		
	
kg_purchase_order_line()

class kg_po_line(osv.osv):
		
	_name = "kg.po.line"
	
	_columns = {
	
	
	'line_id': fields.many2one('purchase.order.line', 'PO No'),
	'kg_discount': fields.float('Discount Amount'),
	'kg_discount_per': fields.float('Discount (%)', digits_compute= dp.get_precision('Discount')),
	'price_unit': fields.float('Unit Price', size=120),
	'date_order':fields.date('Date'),
	'supp_name':fields.many2one('res.partner','Supplier Name',size=120),
	'tax':fields.many2one('kg.tax.structure', 'Tax Structure'),
	'other_ch':fields.float('Other Charges',size=128),
		
	}
	
	
kg_po_line()

	




