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
	_columns = {
		
		'name': fields.char('Payment Name', size=128, required=True,readonly=False,states={'approved':[('readonly',True)]}),
		'active':fields.boolean('Active',readonly=True),
		'creation_date':fields.datetime('Creation Date',readonly=True),
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Apprved By', readonly=True),
		'confirm_date': fields.datetime('Confirm Date', readonly=True),
		'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'reject_date': fields.datetime('Reject Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'state': fields.selection([('draft','Draft'),('confirm','Waiting for approval'),('approved','Approved'),
				('reject','Rejected')],'Status', readonly=True),
		'remark': fields.text('Remarks',readonly=False,states={'approved':[('readonly',True)]}),
		
		'term_category': fields.selection([('advance','Advance'),('payment','Payment'),('Invoice Process','invoice_process'),
				('Others','others')],'Term Category',required=True,readonly=False,states={'approved':[('readonly',True)]}),
		
	}
	
	_defaults = {
		
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.segment', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		

	}
	
	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'confirm','conf_user_id': uid, 'confirm_date': dt_time})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'approved','app_user_id': uid, 'approve_date': dt_time})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'state': 'reject','rej_user_id': uid, 'reject_date': dt_time})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter rejection remark in remark field !!'))
		return True
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
	_columns = {
		
		'name': fields.char('Delivery Type', size=128, required=True,readonly=False,states={'approved':[('readonly',True)]}),
		'active':fields.boolean('Active',readonly=True),
		'creation_date':fields.datetime('Creation Date',readonly=True),
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Apprved By', readonly=True),
		'confirm_date': fields.datetime('Confirm Date', readonly=True),
		'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'reject_date': fields.datetime('Reject Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'state': fields.selection([('draft','Draft'),('confirm','Waiting for approval'),('approved','Approved'),
				('reject','Rejected')],'Status', readonly=True),
		'remark': fields.text('Remarks',readonly=False,states={'approved':[('readonly',True)]}),
		

		
	}
	
	_defaults = {
		
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.segment', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		

	}
	
	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'confirm','conf_user_id': uid, 'confirm_date': dt_time})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'approved','app_user_id': uid, 'approve_date': dt_time})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'state': 'reject','rej_user_id': uid, 'reject_date': dt_time})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter rejection remark in remark field !!'))
		return True
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
	_columns = {
		
		'name': fields.char('Brand', size=128, required=True,readonly=False,states={'approved':[('readonly',True)]}),
		'active':fields.boolean('Active',readonly=True),
		'creation_date':fields.datetime('Creation Date',readonly=True),
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Apprved By', readonly=True),
		'confirm_date': fields.datetime('Confirm Date', readonly=True),
		'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'reject_date': fields.datetime('Reject Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'state': fields.selection([('draft','Draft'),('confirm','Waiting for approval'),('approved','Approved'),
				('reject','Rejected')],'Status', readonly=True),
		'remark': fields.text('Remarks',readonly=False,states={'approved':[('readonly',True)]}),
		

		
	}
	
	_defaults = {
		
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.segment', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		

	}
	
	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'confirm','conf_user_id': uid, 'confirm_date': dt_time})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'approved','app_user_id': uid, 'approve_date': dt_time})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'state': 'reject','rej_user_id': uid, 'reject_date': dt_time})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter rejection remark in remark field !!'))
		return True
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








