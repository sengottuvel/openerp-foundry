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
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_debit_note(osv.osv):
	
	def _amount_line_tax(self, cr, uid, line, context=None):
		val = 0.0
		qty = line.qty
			
		amt_to_per = 0
		kg_discount_per = 0
		tot_discount_per = 0
		for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id,
			line.price_unit * (1-(tot_discount_per or 0.0)/100.0), qty, line.product_id,
			 line.header_id.supplier_id)['taxes']:			 
			val += c.get('amount', 0.0)
		return val
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'amount_total': 0.0,
			}
			val = val1 = line_total = 0.0
			for line in order.line_ids:
				val1 += self._amount_line_tax(cr, uid, line, context=context)
				val += line.price_subtotal
				line_total += line.qty * line.price_unit
			res[order.id]['tax_amount'] = val1
			res[order.id]['tot_amount'] = line_total
			res[order.id]['amount_total'] = line_total + val1
			
		return res
	
	def _get_modify(self, cr, uid, ids, field_name, arg,  context=None):
		res={}
		if field_name == 'modify':
			for h in self.browse(cr, uid, ids, context=None):
				res[h.id] = 'no'
				if h.state == 'approved':
					cr.execute(""" select count(*) as cnt from kg_purchase_invoice where id in (select header_id from ch_kg_debit_note where debit_id = %s) and state = 'approved'  """ %(ids[0]))
					data = cr.dictfetchall()	
					if data:
						data = data[0]
						if data['cnt'] > 0:
							res[h.id] = 'yes'
							return res
						else:
							res[h.id] = 'no'
				else:
					res[h.id] = 'yes'								   
		return res	
		
	_name = 'kg.debit.note'
	_description = "This form is to enter the debit note details"
	_order = "date desc"
	
	_columns = {
		
		## Basic Info
		
		'name':fields.char('Debit Note No', readonly=True),
		'date':fields.date('Debit Note Date'),
		'state': fields.selection([('draft','Draft'),('confirm','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'remark':fields.text('Remarks',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'cancel_remark':fields.text('Cancel Remarks'),	
		
		## Module Requirement Info
		
		'supplier_id':fields.many2one('res.partner','Supplier',domain = [('supplier','=',True)],readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'supplier_invoice_no':fields.char('Supplier Invoice No',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'supplier_invoice_date':fields.date('Supplier Invoice Date',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'line_ids':fields.one2many('ch.debit.note','header_id','Debit Note',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),   
		'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount', multi="sums", store=True, track_visibility='always'),		
		'tot_amount':fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Amount', multi="sums", store=True, track_visibility='always'),		
		'tax_amount':fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax Amount', multi="sums", store=True, track_visibility='always'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=3),
		'reason': fields.selection([('item_terun','Item Return'),('price','Price Deviation'),('both','Both')],'Reason',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		
		## Entry Info
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'cancel_date': fields.datetime('Cancel Date', readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Approved By', readonly=True),  
		'reject_date': fields.datetime('Rejected Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		
	}
	
	_defaults = {
		
		'active': True,
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_debit_note', context=c),
		'state': 'draft',
		'date': lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'yes',
		
	}
	
	def entry_draft(self,cr,uid,ids,context=None):
		entry = self.browse(cr, uid, ids[0])
		if entry.state == 'cancel':
			self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr, uid, ids[0])
		if entry.state == 'draft':
			if len(entry.line_ids) == 0:
				raise osv.except_osv(_('Warning!'),
								_('System not allow to without line items !!'))
			db_name = ''	
			db_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.debit.note')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,db_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(db_seq_id[0],rec.code,entry.date))
			db_name = cr.fetchone();
			self.write(cr, uid, ids, {'name': db_name[0],'state': 'confirm','confirm_user_id': uid, 'confirm_date': dt_time})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.state == 'confirm':
			self.write(cr, uid, ids, {'state': 'approved','app_user_id': uid, 'approve_date': dt_time})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirm':
			if rec.remark:
				self.write(cr, uid, ids, {'state': 'reject','rej_user_id': uid, 'reject_date': dt_time})
			else:
				raise osv.except_osv(_('Rejection remark is must !!'),
					_('Enter the remarks in rejection remark field !!'))
		return True

	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approve':
			if rec.cancel_remark:
				self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': dt_time})
			else:
				raise osv.except_osv(_('Cancel remark is must !!'),
					_('Enter the remarks in cancel remark field !!'))
		return True
		
	def _check_date(self,cr,uid,ids,context=None):
		read_date = self.read(cr,uid,ids,['crt_date','date'],context=context)
		for t in read_date:
			bk_date = date.today() - timedelta(days=(10))
			back_date = bk_date.strftime('%Y-%m-%d')
			if t['date'] < back_date:
				raise osv.except_osv(
					_('Warning'),
					_('Past date not allowed. Check & change the entry date !!'))
			if t['crt_date']<t['date']:
				return False
			else:
				return True
		return True	
		
	def _check_lineitem(self, cr, uid, ids, context=None):
		indent = self.browse(cr,uid,ids[0])
		if indent.line_ids:
			for line in indent.line_ids:
				if line.price_unit <= 0:
					raise osv.except_osv(
					_('Warning'),
					_('Unit Price should be greater than zero for product %s')%(line.product_id.name_template))
				if line.qty <= 0:
					raise osv.except_osv(
					_('Warning'),
					_('Quantity should be greater than zero for product %s')%(line.product_id.name_template))	
		if not indent.line_ids:
			return False
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		if context is None:
			context={}
		indent = self.read(cr, uid, ids, ['state'], context=context)
		unlink_ids = []
		for t in indent:
			if t['state'] in ('draft'):
				unlink_ids.append(t['id'])
			else:
				raise osv.except_osv(('Invalid action !'),('System not allow to delete a UN-DRAFT state !!'))
		osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		return True
	
	_constraints = [
					(_check_lineitem,'Please enter the Item Details',['']),
					]
	
kg_debit_note()

class ch_debit_note(osv.osv):
	
	def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		ed_total_val = 0
		ed_total = 0
		sale_total = 0
		service_total = 0
		
		for entry in self.browse(cr, uid, ids, context=context):
			total_value = (entry.qty * entry.price_unit )	
			amount = (entry.qty * entry.price_unit )	
			for item in [x.id for x in entry.tax_id]:				
				tax_rec = self.pool.get('account.tax').browse(cr,uid,item)				
				if tax_rec.type_tax_use == 'ed':								
					ed_tax_amt = (amount/100.00)*(tax_rec.amount*100.00)
					ed_total += ed_tax_amt	
					ed_total_val += ed_tax_amt												
				if tax_rec.type_tax_use == 'sale':											
					sale_tax_amt = ((amount+ed_total_val)/100.00)*(tax_rec.amount*100.00)					
					sale_total += sale_tax_amt									
				if tax_rec.type_tax_use == 'service':					
					service_tax_amt = (amount/100.00)*(tax_rec.amount*100.00)
					service_total += service_tax_amt	
			if ed_total:						
				total_value += ed_total
			if sale_total:						
				total_value += sale_total
			if service_total:						
				total_value += service_total			
			else:
				pass
			result[entry.id] = total_value
		return result
	
	_name='ch.debit.note'
	_description='This is used to track the product against this debit note'
	
	_columns={
		
		## Basic Info
		
		'header_id':fields.many2one('kg.debit.note','debit Note No'),
		'remark':fields.text('Remarks'),
		
		## Module Requirement Fields
		
		'product_id':fields.many2one('product.product','Item Name',domain = [('active','=',True)]),
		'reason_note': fields.selection([('excess_price','Excess Price'),('rejection','Rejection')],'Reason'),
		'reason': fields.selection([('item_terun','Item Return'),('price','Price Deviation'),('both','Both')],'Reason'),
		'uom': fields.many2one('product.uom', 'UOM', required=True),
		'qty': fields.float('Quantity', required=True),
		'price_unit':fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price')),		
		'tax_id': fields.many2many('account.tax', 'debit_note_taxes', 'debit_id', 'tax_id', 'Tax'),
		'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account'),store=True),
		
	}   
	
	def onchange_product_id(self, cr, uid, ids, product_id,context=None):
		value = {'uom': ''}
		if product_id:
			prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			value = {'uom': prod.uom_id.id}
		return {'value': value}
	
	def default_get(self, cr, uid, fields, context=None):
		return context
		
ch_debit_note()
