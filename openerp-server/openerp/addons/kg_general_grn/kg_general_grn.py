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
from datetime import date
import re
import urllib
import urllib2
import logging
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import calendar
today = datetime.now()

class kg_general_grn(osv.osv):

	_name = "kg.general.grn"
	_description = "General GRN Provision"
	_order = "grn_date desc,name desc"

	def _amount_line_tax(self, cr, uid, line, context=None):
		val = 0.0
		new_amt_to_per = line.kg_discount or 0.0 / line.grn_qty
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
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'amount_untaxed': 0.0,
				'amount_tax': 0.0,
				'amount_total': 0.0,
				'discount' : 0.0,
				'other_charge': 0.0,
			}
			val = val1 = val3 = 0.0
			#cur = order.supplier_id.property_product_pricelist_purchase.currency_id
			po_charges=order.value1 + order.value2
			for line in order.grn_line:
				per_to_amt = (line.grn_qty * line.price_unit) * line.kg_discount_per / 100.00
				tot_discount = line.kg_discount + per_to_amt
				val1 += line.price_subtotal
				val += self._amount_line_tax(cr, uid, line, context=context)
				val3 += tot_discount
			res[order.id]['other_charge']=(round(po_charges,0))
			res[order.id]['amount_tax']=(round(val,0))
			res[order.id]['amount_untaxed']=(round(val1,0))
			#res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
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
		'name': fields.char('GRN NO',readonly=True),
		'creation_date':fields.date('Creation Date',required=True,readonly=True),

		'grn_date':fields.date('GRN Date',required=True,readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'supplier_id':fields.many2one('res.partner','Supplier',domain=[('supplier','=',True)],readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'dc_no': fields.char('DC NO', required=True,readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'dc_date':fields.date('DC Date',required=True, readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'bill': fields.selection([
			('applicable', 'Applicable'),
			('not_applicable', 'Not Applicable')], 'Bill',required=True,readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'user_id':fields.many2one('res.users','Created By',readonly=True),
		'grn_line':fields.one2many('kg.general.grn.line','grn_id','Line Entry',readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'other_charge': fields.float('Other Charges',readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'amount_total': fields.float('Total Amount',readonly=True),

		'sub_total': fields.float('Line Total',readonly=True),
		'state': fields.selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('done', 'Done'), ('cancel', 'Cancelled'),('inv','Invoiced'),('reject','Reject')], 'Status',readonly=True),
		'expiry_flag':fields.boolean('Expiry Flag'),
		'dep_name': fields.many2one('kg.depmaster','Department',readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'remark':fields.text('Remarks',required=True),
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
		'company_id':fields.many2one('res.company','Company'),
		'invoice_flag':fields.boolean('Invoice Flag'),

		'confirmed_by' : fields.many2one('res.users', 'Confirmed By'),
		'approved_by' : fields.many2one('res.users', 'Approved By'),
		'confirmed_date' : fields.date('Confirmed date'),
		'approved_date' : fields.date('Approved date'),
		'po_id':fields.many2one('purchase.order', 'PO NO',
					domain="[('state','=','approved'), '&', ('order_line.pending_qty','>','0'), '&', ('grn_flag','=',False), '&', ('partner_id','=',supplier_id), '&', ('order_line.line_state','!=','cancel')]"),
		'po_date':fields.date('PO Date',readonly=True),
		'order_no': fields.char('Order NO'),
		'order_date':fields.char('Order Date'),
		'payment_type': fields.selection([('cash', 'Cash'), ('credit', 'Credit')], 'Payment Type'),
		'dep_project':fields.many2one('kg.project.master','Dept/Project Name',readonly=True,states={'draft': [('readonly', False)]}),
		'reject_remark':fields.text('Cancel Remarks', readonly=True, states={'confirmed':[('readonly',False)]}),

		'grn_dc': fields.selection([('dc_invoice','DC & Invoice'),('only_grn','Only grn')], 'GRN Type',
										required=True, readonly=False, states={'done':[('readonly',True)]}),

		'sup_invoice_no':fields.char('Supplier Invoice No',size=200, readonly=False, states={'done':[('readonly',True)]}),
		'sup_invoice_date':fields.date('Supplier Invoice Date', readonly=False, states={'done':[('readonly',True)]}),

	}

	"""def create(self, cr, uid, vals,context=None):
		print "vals........hhhhhhhhhhhhhhhh......................",vals
				if vals.get('name','')=='':
			vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'kg.general.grn') or ''
						print "name,,,,,,,,,,,,",vals['name']
		grn =  super(kg_general_grn, self).create(cr, uid, vals, context=context)
		return grn"""


	### Back Entry Date ###

	def email_ids(self,cr,uid,ids,context = None):
		email_from = []
		email_to = []
		email_cc = []
		val = {'email_from':'','email_to':'','email_cc':''}
		ir_model = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		mail_form_ids = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		for ids in mail_form_ids:
			mail_form_rec = self.pool.get('kg.mail.settings').browse(cr,uid,ids)
			if mail_form_rec.doc_name.model == 'kg.general.grn':
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
	
	def sechedular_email_ids(self,cr,uid,ids,reg_string,context = None):
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
				if s == reg_string:
					email_sub = mail_form_rec.subject
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
	
	def onchange_grn_date(self, cr, uid, ids, grn_date):

		exp_grn_qty = 0
		line_tot = 0
		#if grn_entry.name == '':
		#grn_no = self.pool.get('ir.sequence').get(cr, uid, 'kg.po.grn')
		#self.write(cr,uid,ids,{'name':grn_no})
		today_date = today.strftime('%Y-%m-%d')
		back_list = []
		today_new = today.date()
		print "---------------------------->",today_new
		bk_date = date.today() - timedelta(days=3)
		back_date = bk_date.strftime('%Y-%m-%d')

		d1 = today_new
		d2 = bk_date

		delta = d1 - d2

		for i in range(delta.days + 1):
			bkk_date = d1 - timedelta(days=i)
			backk_date = bkk_date.strftime('%Y-%m-%d')
			back_list.append(backk_date)
		print "---------------------------->",back_list

		holiday_obj = self.pool.get('kg.holiday.master.line')
		holiday_ids = holiday_obj.search(cr, uid, [('leave_date','in',back_list)])
		print "holiday_ids........dcwedwed.......",holiday_ids


		if grn_date > today_date:
			raise osv.except_osv(
					_('Warning'),
					_('GRN Date should be less than or equal to current date!'))
		if holiday_ids:
			hol_bk_date = date.today() - timedelta(days=(3+len(holiday_ids)))
			hol_back_date = hol_bk_date.strftime('%Y-%m-%d')
			if grn_date < hol_back_date:
				raise osv.except_osv(
					_('Warning'),
					_('GRN Entry is not allowed for this date!'))
		elif (x for x in back_list if calendar.day_name[x.weekday()]  == 'Sunday'):
			hol_bk_date = date.today() - timedelta(days=4)
			hol_back_date = hol_bk_date.strftime('%Y-%m-%d')
			print "-------------------------------hai>"
			if grn_date < hol_back_date:
				raise osv.except_osv(
					_('Warning'),
					_('GRN Entry is not allowed for this date!'))
		else:
			if grn_date <= back_date:
				raise osv.except_osv(
					_('Warning'),
					_('GRN Entry is not allowed for this date!'))
		return True


	def onchange_user_id(self, cr, uid, ids, user_id, context=None):

		value = {'dep_name': ''}
		if user_id:
			user = self.pool.get('res.users').browse(cr, uid, user_id, context=context)
			value = {'dep_name': user.dep_name.id}
		return {'value': value}		
		
	def kg_grn_confirm(self, cr, uid, ids,context=None):
		grn_entry = self.browse(cr, uid, ids[0])
		if not grn_entry.name:
			self.write(cr,uid,ids[0],{'name':self.pool.get('ir.sequence').get(cr, uid, 'kg.po.grn')})
		exp_grn_qty = 0
		line_tot = 0
		grn_date = grn_entry.grn_date
		today_date = today.strftime('%Y-%m-%d')
		back_list = []
		today_new = today.date()
		print "---------------------------->",today_new
		bk_date = date.today() - timedelta(days=3)
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
		if grn_date > today_date:
			raise osv.except_osv(
					_('Warning'),
					_('GRN Date should be less than or equal to current date!'))
		if holiday_ids:
			hol_bk_date = date.today() - timedelta(days=(3+len(holiday_ids)))
			hol_back_date = hol_bk_date.strftime('%Y-%m-%d')
			if grn_date < hol_back_date:
				raise osv.except_osv(
					_('Warning'),
					_('GRN Entry is not allowed for this date!'))
		elif (x for x in back_list if calendar.day_name[x.weekday()]  == 'Sunday'):
			hol_bk_date = date.today() - timedelta(days=4)
			hol_back_date = hol_bk_date.strftime('%Y-%m-%d')
			if grn_date < hol_back_date:
				raise osv.except_osv(
					_('Warning'),
					_('GRN Entry is not allowed for this date!'))
		else:
			if grn_date <= back_date:
				raise osv.except_osv(
					_('Warning'),
					_('GRN Entry is not allowed for this date!'))

		for line in grn_entry.grn_line:
			if line.inward_type.id == False:
				raise osv.except_osv(_('Warning!'), _('Kindly Give Inward Type for %s !!' %(line.product_id.name)))
			product_id = line.product_id.id
			pro_rec = self.pool.get('product.product').browse(cr, uid, product_id)
			if pro_rec.expiry == True:
				if not line.exp_batch_id:
					raise osv.except_osv(_('Warning!'), _('You should specify Expiry date and batch no for this item!!'))

			if line.exp_batch_id:
				for exp_line in line.exp_batch_id:
					exp_grn_qty += exp_line.product_qty

					if exp_grn_qty > line.grn_qty:
						raise osv.except_osv(_('Please Check!'), _('Quantity should not exceed than GRN Quantity !!'))

			line.write({'state':'confirmed'})
		for line in grn_entry.grn_line:
			product_tax_amt = self._amount_line_tax(cr, uid, line, context=context)
			cr.execute("""update kg_general_grn_line set product_tax_amt = %s where id = %s"""%(product_tax_amt,line.id))
			grn_price = line.grn_qty * line.price_unit
			line.write({'line_total':grn_price})
			line_tot += grn_price
		tot_amt = line_tot + grn_entry.other_charge
		self.write(cr,uid,ids[0],{'sub_total':line_tot,'amount_total':tot_amt,'state':'confirmed','confirmed_by':uid,
									'confirmed_date':time.strftime('%Y-%m-%d')})
		cr.execute("""select all_transaction_mails('General GRN Approval',%s)"""%(ids[0]))
		data = cr.fetchall();
		vals = self.email_ids(cr,uid,ids,context = context)
		if (not vals['email_to']) and (not vals['email_cc']):
			pass
		else:
			ir_mail_server = self.pool.get('ir.mail_server')
			msg = ir_mail_server.build_email(
					email_from = vals['email_from'][0],
					email_to = vals['email_to'],
					subject = " General GRN - Waiting For Approval",
					body = data[0][0],
					email_cc = vals['email_cc'],
					object_id = ids[0] and ('%s-%s' % (ids[0], 'kg.general.grn')),
					subtype = 'html',
					subtype_alternative = 'plain')
			res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
		return True

	def kg_grn_approve(self, cr, uid, ids,context=None):
		user_id = self.pool.get('res.users').browse(cr, uid, uid)
		grn_entry = self.browse(cr, uid, ids[0])
		if grn_entry.confirmed_by.id == uid:
			raise osv.except_osv(
					_('Warning'),
					_('Approve cannot be done by Confirmed user'))
		else:
			lot_obj = self.pool.get('stock.production.lot')
			self.write(cr,uid,ids[0],{'state':'done','approved_by':uid,'approved_date':time.strftime('%Y-%m-%d')})
			if grn_entry.bill == 'applicable':
				self.write(cr,uid,ids[0],{'invoice_flag':'True'})
			stock_move_obj=self.pool.get('stock.move')
			dep_obj = self.pool.get('kg.depmaster')
			dep_id = grn_entry.dep_name.id
			dep_record = dep_obj.browse(cr,uid,dep_id)
			dest_location_id = dep_record.main_location.id

			pi_obj = self.pool.get('kg.purchase.invoice')
			pi_gen_grn_obj = self.pool.get('kg.gengrn.purchase.invoice.line')
			if grn_entry.grn_dc == 'dc_invoice' and grn_entry.bill == 'applicable':
				partner = self.pool.get('res.partner')
				supplier = partner.browse(cr, uid, grn_entry.supplier_id.id)
				tot_add = (supplier.street or '')+ ' ' + (supplier.street2 or '') + '\n'+(supplier.city.name or '')+ ',' +(supplier.state_id.name or '') + '-' +(supplier.zip or '') + '\nPh:' + (supplier.phone or '')+ '\n' +(supplier.mobile or '')
				invoice_no = pi_obj.create(cr, uid, {
							'created_by': uid,
							'creation_date': today,
							'type':'from_po',
							'purpose': 'consu',
							'grn_type':'from_general_grn',
							'supplier_id':grn_entry.supplier_id.id,
							'grn_no':grn_entry.name,
							'sup_address': tot_add,
							'sup_invoice_date' : today,
							'sup_invoice_no':grn_entry.sup_invoice_no,
							'sup_invoice_date':grn_entry.sup_invoice_date,
						})

				sql1 = """ insert into purchase_invoice_general_grn_ids(invoice_id,grn_id) values(%s,%s)"""%(invoice_no,grn_entry.id)
				cr.execute(sql1)

			line_tot = 0
			for line in grn_entry.grn_line:
				# This code will create General GRN to Stock Move
				brand = []
				if line.brand_id:
					brand.append("brand_id = %s"%(line.brand_id.id))
				if brand:
					brand = 'and ('+' or '.join(brand)
					brand =  brand+')'
				else:
					brand = ''
				sql = """select * from stock_move where product_id="""+str(line.product_id.id)+""" and move_type='in' """+ brand +""" and general_grn_id="""+str(line.id)+""" """
				cr.execute(sql)
				data = cr.dictfetchall()
				if data:
					del_sql = """delete from stock_move where product_id="""+str(line.product_id.id)+""" and move_type='in'  """+ brand +"""  and general_grn_id="""+str(line.id)+""" """
					cr.execute(del_sql)

				sql1 = """select * from stock_production_lot where lot_type='in' """+ brand +""" and product_id="""+str(line.product_id.id)+""" and grn_no='"""+str(line.grn_id.name)+"""'"""
				cr.execute(sql1)
				data1 = cr.dictfetchall()
				if data1:
					del_sql1 = """delete from stock_production_lot where lot_type='in' """+ brand +""" and product_id="""+str(line.product_id.id)+""" and grn_no='"""+str(line.grn_id.name)+"""'"""
					cr.execute(del_sql1)

				print data1
				stock_move_obj.create(cr,uid,
					{
					'general_grn_id':line.id,
					'product_id': line.product_id.id,
					'brand_id':line.brand_id.id,
					'name':line.product_id.name,
					'product_qty': line.grn_qty,
					'po_to_stock_qty':line.grn_qty,
					'stock_uom':line.uom_id.id,
					'product_uom': line.uom_id.id,
					'location_id': grn_entry.supplier_id.property_stock_supplier.id,
					'location_dest_id': dest_location_id,
					'move_type': 'in',
					'state': 'done',
					'price_unit': line.price_unit or 0.0,
					'origin':'General GRN',
					'stock_rate':line.price_unit or 0.0,
					})
				if grn_entry.grn_dc == 'dc_invoice' and grn_entry.bill == 'applicable':

						pi_gen_grn_obj.create(cr,uid,
								{

								'general_grn_id':grn_entry.id,
								'general_grn_line_id':line.id,
								'product_id': line.product_id.id,
								'dc_no':grn_entry.dc_no,
								'tot_rec_qty':line.grn_qty,
								'uom_id':line.uom_id.id,
								'total_amt': line.grn_qty * line.price_unit,
								'price_unit': line.price_unit or 0.0,
								'discount': line.kg_discount,
								'kg_discount_per': line.kg_discount_per,
								'invoice_tax_ids': [(6, 0, [x.id for x in line.grn_tax_ids])],
								'net_amt':  line.price_subtotal or 0.0,
								'invoice_header_id' :invoice_no
								})

				line.write({'state':'done'})
				# This code will create Production lot
				if line.exp_batch_id:
					for exp in line.exp_batch_id:
						lot_obj.create(cr,uid,
							{
							'grn_no':line.grn_id.name,
							'product_id':line.product_id.id,
							'brand_id':line.brand_id.id,
							'product_uom':line.uom_id.id,
							'product_qty':exp.product_qty,
							'pending_qty':exp.product_qty,
							'issue_qty':exp.product_qty,
							'batch_no':exp.batch_no,
							'expiry_date':exp.exp_date,
							'price_unit':line.price_unit or 0.0,
							'po_uom':line.uom_id.id,
							'grn_type':'material'
							#'po_qty':move_record.po_to_stock_qty,
						})

				else:
					lot_obj.create(cr,uid,

						{

						'grn_no':line.grn_id.name,
						'product_id':line.product_id.id,
						'brand_id':line.brand_id.id,
						'product_uom':line.uom_id.id,
						'product_qty':line.grn_qty,
						'pending_qty':line.grn_qty,
						'issue_qty':line.grn_qty,
						'batch_no':line.grn_id.name,
						#'expiry_date':exp.exp_date,
						'price_unit':line.price_unit or 0.0,
						'po_uom':line.uom_id.id,
						'batch_no':line.grn_id.name,
						'grn_type':'material'
						#'po_qty':move_record.po_to_stock_qty,
					})
				grn_price = line.grn_qty * line.price_unit
				line.write({'line_total':grn_price})
				line_tot += grn_price
				total_price = line.price_unit * line.grn_qty
				product_tax_amt = self._amount_line_tax(cr, uid, line, context=context)
				cr.execute("""update kg_general_grn_line set product_tax_amt = %s where id = %s"""%(product_tax_amt,line.id))
			cr.execute("""select all_transaction_mails('General GRN Approval',%s)"""%(ids[0]))
			data = cr.fetchall();
			vals = self.email_ids(cr,uid,ids,context = context)
			if (not vals['email_to']) and (not vals['email_cc']):
				pass
			else:
				ir_mail_server = self.pool.get('ir.mail_server')
				msg = ir_mail_server.build_email(
						email_from = vals['email_from'][0],
						email_to = vals['email_to'],
						subject = " General GRN - Approved",
						body = data[0][0],
						email_cc = vals['email_cc'],
						object_id = ids[0] and ('%s-%s' % (ids[0], 'kg.general.grn')),
						subtype = 'html',
						subtype_alternative = 'plain')
				res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
			return True
			
			
	def dead_stock_register_scheduler(self,cr,uid,ids=0,context = None):
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
		else:
			db[0]['current_database'] = 'Others'
		cr.execute("""select all_daily_scheduler_mails('Unused Stock Register')""")
		data = cr.fetchall();
		cr.execute("""SELECT to_date(to_char(now()::date - interval '1 month', 'YYYY/MM/DD'), 'YYYY/MM/DD') as last_dt""")
		last_dt = cr.fetchall();
		cr.execute("""select sum(tot_name) from (select product_product.name_template,product_uom.name,stock_production_lot.pending_qty,
				stock_production_lot.grn_no,stock_production_lot.price_unit,(stock_production_lot.price_unit * stock_production_lot.pending_qty) as tot_name
				
				from stock_production_lot
				
				left join product_product on product_product.id = stock_production_lot.product_id
				left join product_uom on product_uom.id = stock_production_lot.product_uom
				where 
				to_char(stock_production_lot.write_date,'yyyy-mm-dd') <= '%s' and stock_production_lot.pending_qty = stock_production_lot.product_qty and stock_production_lot.pending_qty > 0
				order by stock_production_lot.date,stock_production_lot.grn_no) as p	"""%(last_dt[0]))
		total_sum = cr.dictfetchall();
		db = db[0]['current_database'].encode('utf-8')
		total_sum = str(total_sum[0]['sum'])
		vals = self.sechedular_email_ids(cr,uid,ids,reg_string = 'dead stock',context = context)
		if (not vals['email_to']) and (not vals['email_cc']):
			pass
		else:
			ir_mail_server = self.pool.get('ir.mail_server')
			msg = ir_mail_server.build_email(
					email_from = vals['email_from'][0],
					email_to = vals['email_to'],
					subject = "ERP Non-Movable stock (for last 30 days) Details for "+db+' as on ' + time.strftime('%d-%m-%Y') + '. Total Values is ' +  total_sum,
					body = data[0][0],
					email_cc = vals['email_cc'],
					object_id = ids and ('%s-%s' % (ids, 'kg.general.grn')),
					subtype = 'html',
					subtype_alternative = 'plain')
			res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
		return True
			
	
	def unaccounted_cash_GRN_register_scheduler(self,cr,uid,ids=0,context = None):
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
			
		cr.execute(""" select pg.id from kg_po_grn pg where pg.state in ('done','inv') and pg.approved_date::date='%s' and pg.billing_status = 'applicable' and
						pg.payment_type = 'cash'
					   union
					   select gg.id from kg_general_grn gg where gg.state in ('done','inv') and gg.approved_date::date='%s' and gg.bill = 'applicable' and
						gg.payment_type = 'cash'"""
					    %(time.strftime('%Y-%m-%d'),time.strftime('%Y-%m-%d')))
		grn_data = cr.dictfetchall()	
			
		if grn_data:
				
			cr.execute("""select all_daily_auto_scheduler_mails('Unaccount Goods Receipt Cash Register')""")
			data = cr.fetchall();
			cr.execute("""select sum(name) from ((select
							round(cast(po_grn_line.po_grn_qty * po_grn_line.price_unit as numeric),2) as name
							from kg_po_grn
							left join po_grn_line on po_grn_line.po_grn_id = kg_po_grn.id
							where kg_po_grn.billing_status = 'applicable' and
							kg_po_grn.payment_type = 'cash' and
							to_char(kg_po_grn.grn_date,'dd-mm-yyyy') = '%s' and
							kg_po_grn.state in ('done') )
						union
							(select 
							round(cast(kg_general_grn_line.grn_qty * kg_general_grn_line.price_unit as numeric),2) as name
							from kg_general_grn
							left join kg_general_grn_line on kg_general_grn_line.grn_id = kg_general_grn.id
							where kg_general_grn.bill = 'applicable' and
							kg_general_grn.payment_type = 'cash' and
							to_char(kg_general_grn.grn_date,'dd-mm-yyyy') = '%s' and
							kg_general_grn.state in ('done')))  as p1   """%(time.strftime('%d-%m-%Y'),time.strftime('%d-%m-%Y')))
			total_sum = cr.dictfetchall();
			db = db[0]['current_database'].encode('utf-8')
			total_sum = str(total_sum[0]['sum'])
			vals = self.sechedular_email_ids(cr,uid,ids,reg_string = 'unaccounted cash register',context = context)
			if (not vals['email_to']) and (not vals['email_cc']):
				pass
			else:
				ir_mail_server = self.pool.get('ir.mail_server')
				msg = ir_mail_server.build_email(
						email_from = vals['email_from'][0],
						email_to = vals['email_to'],
						subject = "ERP Unaccounted GRN - Cash for "+db +' as on '+time.strftime('%d-%m-%Y')+' Total Amount (Rs.):' + total_sum,
						body = data[0][0],
						email_cc = vals['email_cc'],
						object_id = ids and ('%s-%s' % (ids, 'kg.general.grn')),
						subtype = 'html',
						subtype_alternative = 'plain')
				res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
				
		else:
			pass		
		return True
		
	
	def grn_register_scheduler_mail(self,cr,uid,ids=0,context = None):
		cr.execute("""SELECT current_database();""")
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
			
		cr.execute(""" select pg.id from kg_po_grn pg where pg.state in ('done','inv') and pg.approved_date::date='%s'
					   union
					   select gg.id from kg_general_grn gg where gg.state in ('done','inv') and gg.approved_date::date='%s' """
					    %(time.strftime('%Y-%m-%d'),time.strftime('%Y-%m-%d')))
		grn_data = cr.dictfetchall()
		
		if grn_data:	
		
			
			cr.execute("""select all_daily_auto_scheduler_mails('Goods Receipt Register')""")
			data = cr.fetchall();
			cr.execute("""select sum(total) from ((select 
							round(cast(po_grn_line.po_grn_qty*po_grn_line.price_unit as numeric) ,2) as total
							from kg_po_grn
							left join po_grn_line on po_grn_line.po_grn_id = kg_po_grn.id
							left join product_product on product_product.id = po_grn_line.product_id
							left join product_uom on product_uom.id = po_grn_line.uom_id
							left join kg_brand_master on kg_brand_master.id = po_grn_line.brand_id
							left join purchase_order on purchase_order.id = kg_po_grn.po_id
							left join kg_service_order on kg_service_order.id = kg_po_grn.so_id
							where to_char(kg_po_grn.grn_date,'dd-mm-yyyy') = '%s' and
							kg_po_grn.state in ('done','inv') order by kg_po_grn.grn_date,kg_po_grn.name)
						union
							(select
							round(cast(kg_general_grn_line.grn_qty*kg_general_grn_line.price_unit as numeric),2) as total
							from kg_general_grn
							left join kg_general_grn_line on kg_general_grn_line.grn_id = kg_general_grn.id
							left join product_product on product_product.id = kg_general_grn_line.product_id
							left join product_uom on product_uom.id = kg_general_grn_line.uom_id
							left join kg_brand_master on kg_brand_master.id = kg_general_grn_line.brand_id
							left join purchase_order on purchase_order.id = kg_general_grn.po_id
							where to_char(kg_general_grn.grn_date,'dd-mm-yyyy') = '%s' and
							kg_general_grn.state in ('done','inv') order by kg_general_grn.grn_date,kg_general_grn.name)) as pp1
						"""%(time.strftime('%d-%m-%Y'),time.strftime('%d-%m-%Y')))
			total_sum = cr.dictfetchall();
			db = db[0]['current_database'].encode('utf-8')
			total_sum = str(total_sum[0]['sum'])
			vals = self.sechedular_email_ids(cr,uid,ids,reg_string = 'goods receipt register',context = context)
			if (not vals['email_to']) and (not vals['email_cc']):
				pass
			else:
				ir_mail_server = self.pool.get('ir.mail_server')
				msg = ir_mail_server.build_email(
						email_from = vals['email_from'][0],
						email_to = vals['email_to'],
						subject = "ERP Goods Reciept Notes for "+db +' as on '+time.strftime('%d-%m-%Y')+' Total Amount (Rs.):' + total_sum,
						body = data[0][0],
						email_cc = vals['email_cc'],
						object_id = ids and ('%s-%s' % (ids, 'kg.general.grn')),
						subtype = 'html',
						subtype_alternative = 'plain')
				res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
		else:
			pass		
				
		return True
	
	def grn_cancel(self, cr, uid, ids, context=None):
		grn = self.browse(cr, uid, ids[0])
		if not grn.remark:
			raise osv.except_osv(_('Remarks is must !!'), _('Enter Remarks for GRN Cancel !!!'))
		else:
			self.write(cr, uid, ids[0], {'state' : 'cancel'})
		for line in grn.grn_line:
			line.write({'state':'cancel'})
		return True

	def grn_reject(self, cr, uid, ids, context=None):
		grn = self.browse(cr, uid, ids[0])
		print "grn........................", grn
		if not grn.reject_remark:
			raise osv.except_osv(_('Remarks is must !!'), _('Enter Remarks for GRN Rejection !!!'))
		else:
			self.write(cr, uid, ids[0], {'state' : 'draft'})

		return True


	def print_grn(self, cr, uid, ids, context=None):
		assert len(ids) == 1, 'This option should only be used for a single id at a time'
		wf_service = netsvc.LocalService("workflow")
		wf_service.trg_validate(uid, 'kg.general.grn', ids[0], 'send_rfq', cr)
		datas = {
				 'model': 'kg.general.grn',
				 'ids': ids,
				 'form': self.read(cr, uid, ids[0], context=context),
		}
		return {'type': 'ir.actions.report.xml', 'report_name': 'general.grn.print', 'datas': datas, 'nodestroy': True,'name': 'GRN'}

	_defaults = {

		'creation_date':fields.date.context_today,
		'user_id': lambda obj, cr, uid, context: uid,
		'bill':'not_applicable',
		'state':'draft',
		'grn_date':fields.date.context_today,
		'dc_date':fields.date.context_today,
		'name':'',
		'type':'in',
		'company_id' : lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.general.grn', context=c),

	}


	def _get_invoice_type(self, pick):
		print "_get_invoice_type called from PICKING^^^^^^^^^^^^^^^^^^^^66"
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

		print "action_invoice_create =============================FROM KGGGGG>>>"

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
			print "picking ------------------>>>>>", picking
			partner = picking.supplier_id
			if isinstance(partner, int):
				partner = partner_obj.browse(cr, uid, [partner], context=context)[0]
			if not partner:
				raise osv.except_osv(_('Error, no partner!'),
					_('Please put a partner on the GRN if you want to generate invoice.'))

			if not inv_type:
				inv_type = self._get_invoice_type(picking)
			print "invoices_group ::::::::::::; =====>>>>>>>>........", invoices_group
			if group and partner.id in invoices_group:
				invoice_id = invoices_group[partner.id]
				print "invoice_id ---------------------------...........", invoice_id
				invoice = invoice_obj.browse(cr, uid, invoice_id)
				invoice_vals_group = self._prepare_invoice_group(cr, uid, picking, partner, invoice, context=context)
				invoice_obj.write(cr, uid, [invoice_id], invoice_vals_group, context=context)
			else:
				print "elsepart..................."
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
		print "_prepare_invoice called from PICKING^^^^^^^^^^^^^^^^^^^^FROM KGGG"
		print "picking =========================>>>>",picking.type

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
			#'account_id': account_id,
			'partner_id': partner.id,
			'comment': comment,
			'payment_term': payment_term,
			'fiscal_position': partner.property_account_position.id,
			'date_invoice': context.get('date_inv', False),
			'company_id': picking.company_id.id,
			'user_id': uid,
			#'po_id':picking.po_id.id,
			'general_grn_id':picking.id,
			'po_expenses_type1':other_ch1,
			'po_expenses_type2':other_ch2,
			'value1':val1,
			'value2':val2,
			'state':'proforma',
			'supplier_invoice_number': context.get('sup_inv_no', False),
			'sup_inv_date': context.get('sup_inv_date', False),
			'bill_type':'cash',
			#'po_date':po_rec.date_order,
			'grn_date':picking.grn_date,
			'amount_untaxed':picking.amount_untaxed,
			'amount_tax':picking.amount_tax,
			'tot_discount':picking.discount,
			'other_charge':other_charge




		}
		#cur_id = self.get_currency_id(cr, uid, picking)
		#if cur_id:
			#invoice_vals['currency_id'] = cur_id
		if journal_id:
			invoice_vals['journal_id'] = journal_id
		return invoice_vals

	def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id,
		invoice_vals, context=None):
		print "_prepare_invoice_line called from PICKING^^^^^^^^^^^^^^^^^^^^FROM KGGG"

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
			#'poline_id':move_line.purchase_line_id,
			'product_id': move_line.product_id.id,
			'brand_id': move_line.brand_id.id,
			#'account_id': account_id,
			'price_unit': move_line.price_unit,
			'quantity': move_line.grn_qty or 0.00,
			'invoice_line_tax_id': [(6, 0, [x.id for x in move_line.grn_tax_ids])],
			#'account_analytic_id': picking_obj._get_account_analytic_invoice(cr, uid, picking, move_line),
			'discount':move_line.kg_discount_per,
			'kg_disc_amt':move_line.kg_discount,
		}

	def _check_lineqty(self, cr, uid, ids, context=None):
		print "called _check_lineqty ___ function"
		grn = self.browse(cr, uid, ids[0])
		for line in grn.grn_line:
			if line.grn_qty <= 0:
				return False
			else:
				return True

	def _check_lineprice(self, cr, uid, ids, context=None):
		print "called _check_lineprice ___ function"
		grn = self.browse(cr, uid, ids[0])
		for line in grn.grn_line:
			if line.price_unit <= 0:
				return False
			else:
				return True

	def _grndate_validation(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		print "rec...................", rec
		today = date.today()
		print "today................", type(today), today
		grn_date = datetime.strptime(rec.grn_date,'%Y-%m-%d').date()
		print "rec.grn_date...........", type(grn_date), grn_date
		if grn_date > today:
			return False
		return True

	def _dcdate_validation(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		print "rec...................", rec
		today = date.today()
		print "today................", type(today), today
		dc_date = datetime.strptime(rec.dc_date,'%Y-%m-%d').date()
		print "rec.grn_date...........", type(dc_date), dc_date
		if dc_date > today:
			return False
		return True

	def unlink(self, cr, uid, ids, context=None):
		unlink_ids = []
		grn_rec = self.browse(cr, uid, ids[0])
		if grn_rec.state != 'draft':
			raise osv.except_osv(_('Invalid action !'), _('System not allow to delete Confirmed and Done state GRN !!'))
		else:
			unlink_ids.append(grn_rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)

	def expiry_alert(self, cr, uid, ids, context=None):

		now = time.strftime("%Y-%m-%d")
		cr.execute(""" select id,grn_line_id,product_qty,exp_date,batch_no from kg_exp_batch """)
		data = cr.dictfetchall()
		print "data",data
		value_data = []
		rep=[]
		new_list = []
		for item in data:
			now = time.strftime("%Y-%m-%d")
			print "now",now


			# Product Name
			grn_line_rec = self.pool.get('kg.general.grn.line').browse(cr, uid, item['grn_line_id'])

			product_name = grn_line_rec.product_id.name_template
			print "grn_record",grn_line_rec.grn_id
			grn_no = grn_line_rec.grn_id.name

			exp_date = item['exp_date']
			exp_day = datetime.strptime(exp_date, "%Y-%m-%d")
			today = datetime.strptime(now, "%Y-%m-%d")
			print "exp_rec.exp_date",exp_day,type(exp_day)

			pre_day = exp_day - timedelta(hours=24)
			print "pre_day of exp_day",pre_day
			print "today............",today
			if pre_day == today:

				print "sssssssssss",item['exp_date']
				rep=[product_name,grn_no,item['exp_date'],item['batch_no']]
				value_data.append(rep)
		print "new_list----------->>>>>>",value_data
		return value_data




	_constraints = [
		(_check_lineqty, 'You can not save an GRN with 0 product qty!!',['grn_qty']),
		#(_check_lineprice, 'You can not save an GRN with 0 price_unit!!',['price_unit']),
		(_grndate_validation, 'GRN date should not be greater than current date !!',['grn_date']),
		(_dcdate_validation, 'DC date should not be greater than current date !!',['dc_date']),
		]






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
			amt_to_per = (line.kg_discount / (line.grn_qty * line.price_unit or 1.0 )) * 100
			kg_discount_per = line.kg_discount_per
			tot_discount_per = amt_to_per + kg_discount_per
			price = line.price_unit * (1 - (tot_discount_per or 0.0) / 100.0)
			taxes = tax_obj.compute_all(cr, uid, line.grn_tax_ids, price, line.grn_qty, line.product_id, line.grn_id.supplier_id)
			#cur = line.grn_id.supplier_id.property_product_pricelist_purchase.currency_id
			res[line.id] = (round(taxes['total'],0))
		return res

	_columns = {

		'grn_id':fields.many2one('kg.general.grn','GRN Entry'),
		'product_id':fields.many2one('product.product','Item Name',required=True,readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}, domain=[('state','=','approved')]),
		'uom_id':fields.many2one('product.uom','UOM',readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'grn_qty':fields.float('GRN Quantity',required=True,readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'price_unit':fields.float('Unit Price',readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'price_subtotal': fields.function(_amount_line, string='Line Total', digits_compute= dp.get_precision('Account')),
		'exp_batch_id':fields.one2many('kg.exp.batch','grn_line_id','Exp Batch No',readonly=True, states={'confirmed':[('readonly',False)],'draft':[('readonly',False)]}),
		'state': fields.selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),('done', 'Done'), ('cancel', 'Cancelled')], 'Status',readonly=True),
		'cancel_remark':fields.text('Cancel Remarks'),
		'kg_discount_per': fields.float('Discount (%)', digits_compute= dp.get_precision('Discount')),
		'kg_discount': fields.float('Discount Amount'),
		'grn_tax_ids': fields.many2many('account.tax', 'po_gen_grn_tax', 'order_id', 'taxes_id', 'Taxes'),

		'brand_id':fields.many2one('kg.brand.master','Brand'),
		'inward_type': fields.many2one('kg.inwardmaster', 'Inward Type'),
		'product_tax_amt':fields.float('Tax Amount')

	}

	_defaults = {

		'state':'draft',


	}

	def onchange_uom_id(self, cr, uid, ids, product_id, context=None):

		value = {'uom_id': ''}
		if product_id:
			pro_rec = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			value = {'uom_id': pro_rec.uom_id.id,'price_unit':pro_rec.standard_price}
		return {'value': value}

	def create(self, cr, uid, vals,context=None):
		print "vals..............................",vals
		if vals.has_key('product_id') and vals['product_id']:
			product_rec = self.pool.get('product.product').browse(cr,uid,vals['product_id'])
			if product_rec:
				vals.update({'uom_id':product_rec.uom_id.id})
		grn_line =  super(kg_general_grn_line, self).create(cr, uid, vals, context=context)
		return grn_line

	def grn_line_cancel(self, cr, uid, ids, context=None):
		grn_line = self.browse(cr, uid, ids[0])
		print "grn_line........................", grn_line
		if not grn_line.cancel_remark:
			raise osv.except_osv(_('Remarks is must !!'), _('Enter Cancel Remarks for GRN Line Cancel !!!'))
		else:
			self.write(cr, uid, ids[0], {'state' : 'cancel'})
		return True

kg_general_grn_line()


class kg_exp_batch(osv.osv):

	_name = "kg.exp.batch"
	_description = "Expiry Date and Batch NO"


	_columns = {

		'grn_line_id':fields.many2one('kg.general.grn.line','GRN Entry Line'),
		'exp_date':fields.date('Expiry Date'),
		'batch_no':fields.char('Batch No'),
		'product_qty':fields.integer('Product Qty'),


	}
	_sql_constraints = [

		('batch_no', 'unique(batch_no)', 'S/N must be unique per Item !!'),
	]



kg_exp_batch()

class kg_general_grn_stock_move(osv.osv):

	_name = "stock.move"
	_inherit = "stock.move"


	_columns = {

		'general_grn_id':fields.many2one('kg.general.grn.line', 'General GRN Line Id'),



	}

kg_general_grn_stock_move()










