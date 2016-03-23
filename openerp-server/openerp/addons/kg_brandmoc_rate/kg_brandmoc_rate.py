from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_brandmoc_rate(osv.osv):

	_name = "kg.brandmoc.rate"
	_description = "Brand Moc Rate Master"
	
	
	"""
	def _get_modify(self, cr, uid, ids, field_name, arg, context=None):
		res={}
		ms_line_obj = self.pool.get('ch.machineshop.details')
		ms_line_amend_obj = self.pool.get('ch.machineshop.details.amendment')
		moc_const_ms_obj = self.pool.get('ch.moc.machineshop.details')		
		for item in self.browse(cr, uid, ids, context=None):
			res[item.id] = 'no'
			ms_line_ids = ms_line_obj.search(cr,uid,[('ms_id','=',item.id)])
			ms_line_amend_ids = ms_line_amend_obj.search(cr,uid,[('ms_id','=',item.id)])
			moc_const_ms_ids = moc_const_ms_obj.search(cr,uid,[('ms_id','=',item.id)])					
			if ms_line_ids or ms_line_amend_ids or moc_const_ms_ids:
				res[item.id] = 'yes'		
		return res"""
	
	_columns = {
			
		'product_id': fields.many2one('product.product','Product Name', required=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'eff_date': fields.date('Effective date',required=True),		
		'active': fields.boolean('Active'),	
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'line_ids':fields.one2many('ch.brandmoc.rate.details', 'header_id', "Raw Materials"),
		
		
		#'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		'latest_price':fields.float('Latest Price(Rs)',readonly=True),
		'category_type': fields.selection([('purchase_item','Purchase Item'),('design_item','Design Item')],'Category'),
		
		### Entry Info ###
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'ap_rej_date': fields.datetime('Approved/Reject Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Reject By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.brandmoc.rate', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':fields.datetime.now,	
		'eff_date':fields.datetime.now,	
		#'modify': 'no',
		
	}
	
	_sql_constraints = [
	
		('product_id', 'unique(product_id)', 'Product Name must be unique per Company !!'),
		
	]
			
		
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'state': 'reject','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter the remarks in rejection remark field !!'))
		return True
		
	def onchange_latest_price(self, cr, uid, ids, product_id, context=None):		
		value = {'latest_price': ''}
		if product_id:
			pro_rec = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			value = {'latest_price': pro_rec.latest_price}			
		return {'value': value}
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state not in ('draft','cancel'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	def create(self, cr, uid, vals, context=None):
		product_obj = self.pool.get('product.product')
		if vals.get('product_id'):		  
			product_rec = product_obj.browse(cr, uid, vals.get('product_id') )
			latest_price = product_rec.latest_price
			vals.update({'latest_price': latest_price})
		return super(kg_brandmoc_rate, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		product_obj = self.pool.get('product.product')
		if vals.get('product_id'):		  
			product_rec = product_obj.browse(cr, uid, vals.get('product_id') )
			latest_price = product_rec.latest_price
			vals.update({'latest_price': latest_price})
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_brandmoc_rate, self).write(cr, uid, ids, vals, context)
		
	
		
kg_brandmoc_rate()



class ch_brandmoc_rate_details(osv.osv):
	
	_name = "ch.brandmoc.rate.details"
	_description = "Brand MOC Rate Details Master"
	
	_columns = {
			
		'header_id':fields.many2one('kg.brandmoc.rate', 'Brand MOC Entry', required=True, ondelete='cascade'),	
		'brand_id': fields.many2one('kg.brand.master','Brand'),			
		'moc_id':fields.many2one('kg.moc.master','MOC'),	
		'rate':fields.float('Design Rate(Rs)',required=True),
		'remarks':fields.text('Remarks'),		
	}
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.rate <= 0.00:
			return False
		return True
		
	_constraints = [		
			  
		(_check_values, 'System not allow to save negative and zero values..!!',['Rate']),	
		
	   ]
		
	
ch_brandmoc_rate_details()
