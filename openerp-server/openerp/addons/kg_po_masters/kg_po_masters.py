from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import datetime
a = datetime.now()
dt_time = a.strftime('%m/%d/%Y %H:%M:%S')
import openerp.addons.decimal_precision as dp

class kg_payment_master(osv.osv):

	_name = "kg.payment.master"
	_description = "Payment Masters"
	
	def _get_modify(self, cr, uid, ids, field_name, arg, context=None):
		res={}
		so_obj = self.pool.get('kg.service.order')
		pur_inv_obj = self.pool.get('kg.purchase.invoice')
		pur_amd_obj = self.pool.get('kg.purchase.amendment')
		po_obj = self.pool.get('purchase.order')
		ser_inv_obj = self.pool.get('kg.service.invoice')
		partner_obj = self.pool.get('res.partner')
		so_amd_obj = self.pool.get('kg.so.amendment')
		for h in self.browse(cr, uid, ids, context=None):
			res[h.id] = 'no'
			so_ids = so_obj.search(cr,uid,[('payment_mode','=',h.id)])
			pur_inv_ids = pur_inv_obj.search(cr,uid,[('payment_id','=',h.id)])
			pur_amd_ids = pur_amd_obj.search(cr,uid,[('payment_mode_amend','=',h.id)])
			po_ids = po_obj.search(cr,uid,[('payment_mode','=',h.id)])
			ser_inv_ids = ser_inv_obj.search(cr,uid,[('payment_mode','=',h.id)])
			partner_ids = partner_obj.search(cr,uid,[('payment_id','=',h.id)])
			so_amd_ids = so_amd_obj.search(cr,uid,[('payment_mode_amend','=',h.id)])
			if so_ids or pur_inv_ids or pur_amd_ids or po_ids or ser_inv_ids or partner_ids or so_amd_ids:
				res[h.id] = 'yes'
		print "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",res
		return res
		
	_columns = {
		
		'name': fields.char('Payment Name', size=128, required=True,readonly=False,states={'approved':[('readonly',True)]}),
		'code': fields.char('Code', size=128, readonly=False,states={'approved':[('readonly',True)]}),
		'active':fields.boolean('Active'),
		'creation_date':fields.datetime('Creation Date',readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Approved By', readonly=True),
		'confirm_date': fields.datetime('Confirm Date', readonly=True),
		'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'reject_date': fields.datetime('Reject Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'term_category': fields.selection([('advance','Advance'),('payment','Payment'),('Invoice Process','invoice_process'),
				('Others','others')],'Term Category',required=True,readonly=False,states={'approved':[('readonly',True)]}),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=3),
		
		
	}
	
	_defaults = {
		
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.segment', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'modify': 'no',
		
	}
	
	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'confirmed','conf_user_id': uid, 'confirm_date': dt_time})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'approved','app_user_id': uid, 'approve_date': dt_time})
		return True
	
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True
		
	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'state': 'reject','rej_user_id': uid, 'reject_date': dt_time})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter rejection remark in remark field !!'))
		return True
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': dt_time})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True
		
	def write(self, cr, uid, ids, vals, context=None):	  
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_payment_master, self).write(cr, uid, ids, vals, context)
	
	def unlink(self,cr,uid,ids,context=None):
		raise osv.except_osv(_('Warning!'),
				_('You can not delete Entry !!'))		
					
	"""	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	"""
	
kg_payment_master()


class kg_delivery_master(osv.osv):

	_name = "kg.delivery.master"
	_description = "Delivery Masters"
	
	def _get_modify(self, cr, uid, ids, field_name, arg, context=None):
		res={}
		so_obj = self.pool.get('kg.service.order')
		pur_amd_obj = self.pool.get('kg.purchase.amendment')
		po_obj = self.pool.get('purchase.order')
		partner_obj = self.pool.get('res.partner')
		for h in self.browse(cr, uid, ids, context=None):
			res[h.id] = 'no'
			so_ids = so_obj.search(cr,uid,[('delivery_mode','=',h.id)])
			pur_amd_ids = pur_amd_obj.search(cr,uid,[('delivery_mode_amend','=',h.id)])
			po_ids = po_obj.search(cr,uid,[('delivery_mode','=',h.id)])
			partner_ids = partner_obj.search(cr,uid,[('delivery_id','=',h.id)])
			if so_ids or pur_amd_ids or po_ids or partner_ids	:
				res[h.id] = 'yes'
		print "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",res
		return res
		
	_columns = {
		
		'name': fields.char('Name', size=128, required=True,readonly=False,states={'approved':[('readonly',True)]}),
		'active':fields.boolean('Active'),
		'creation_date':fields.datetime('Creation Date',readonly=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Approved By', readonly=True),
		'confirm_date': fields.datetime('Confirm Date', readonly=True),
		'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'reject_date': fields.datetime('Reject Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=3),
		
	}
	
	_defaults = {
		
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.segment', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'modify': 'no',
		
	}
	
	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'confirmed','conf_user_id': uid, 'confirm_date': dt_time})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'approved','app_user_id': uid, 'approve_date': dt_time})
		return True
	
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True
		
	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'state': 'reject','rej_user_id': uid, 'reject_date': dt_time})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter rejection remark in remark field !!'))
		return True
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': dt_time})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True
			
	def write(self, cr, uid, ids, vals, context=None):	  
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_delivery_master, self).write(cr, uid, ids, vals, context)
	
	def unlink(self,cr,uid,ids,context=None):
		raise osv.except_osv(_('Warning!'),
				_('You can not delete Entry !!'))		
		
	"""	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	"""
	
kg_delivery_master()


class kg_brand_master(osv.osv):

	_name = "kg.brand.master"
	_description = "Brand Masters"
	
	def _get_modify(self, cr, uid, ids, field_name, arg, context=None):
		res={}
		so_obj = self.pool.get('kg.service.order.line')
		pur_inv_obj = self.pool.get('kg.pogrn.purchase.invoice.line')
		dep_is_obj = self.pool.get('kg.department.issue.line')
		pur_amd_obj = self.pool.get('kg.purchase.amendment.line')
		con_inw_obj = self.pool.get('kg.contractor.inward.line')
		po_obj = self.pool.get('purchase.order.line')
		dep_ind_obj = self.pool.get('kg.depindent.line')
		po_grn_obj = self.pool.get('po.grn.line')
		gen_grn_obj = self.pool.get('kg.general.grn.line')
		for h in self.browse(cr, uid, ids, context=None):
			res[h.id] = 'no'
			so_ids = so_obj.search(cr,uid,[('brand_id','=',h.id)])
			pur_inv_ids = pur_inv_obj.search(cr,uid,[('brand_id','=',h.id)])
			dep_is_ids = dep_is_obj.search(cr,uid,[('brand_id','=',h.id)])
			pur_amd_ids = pur_amd_obj.search(cr,uid,[('brand_id_amend','=',h.id)])
			con_inw_ids = con_inw_obj.search(cr,uid,[('brand_id','=',h.id)])
			po_ids = po_obj.search(cr,uid,[('brand_id','=',h.id)])
			dep_ind_ids = dep_ind_obj.search(cr,uid,[('brand_id','=',h.id)])
			po_grn_ids = po_grn_obj.search(cr,uid,[('brand_id','=',h.id)])
			gen_grn_ids = gen_grn_obj.search(cr,uid,[('brand_id','=',h.id)])
			if so_ids or pur_inv_ids or dep_is_ids or pur_amd_ids or con_inw_ids or po_ids or dep_ind_ids or po_grn_ids or gen_grn_ids:
				res[h.id] = 'yes'
		print "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",res
		return res
		
	_columns = {
		
		'name': fields.char('Brand', size=128, required=True,readonly=False,states={'approved':[('readonly',True)]}),
		'active':fields.boolean('Active'),
		'creation_date':fields.datetime('Creation Date',readonly=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Approved By', readonly=True),
		'confirm_date': fields.datetime('Confirm Date', readonly=True),
		'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'reject_date': fields.datetime('Reject Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel Remarks'),
		#~ 'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=3),
		'product_ids': fields.many2many('product.product','prod_brnd','brd_id','prod_id','Product Name',readonly=False,states={'approved':[('readonly',True)]}),
		
	}
	
	_defaults = {
		
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.segment', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		#~ 'modify': 'no',
		
	}
	
	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'confirmed','conf_user_id': uid, 'confirm_date': dt_time})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'approved','app_user_id': uid, 'approve_date': dt_time})
		return True
	
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True
		
	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'state': 'reject','rej_user_id': uid, 'reject_date': dt_time})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter rejection remark in remark field !!'))
		return True
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': dt_time})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True
		
	def write(self, cr, uid, ids, vals, context=None):	  
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_brand_master, self).write(cr, uid, ids, vals, context)
	
	def unlink(self,cr,uid,ids,context=None):
		raise osv.except_osv(_('Warning!'),
				_('You can not delete Entry !!'))		
	
	"""	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
	"""
	
kg_brand_master()








