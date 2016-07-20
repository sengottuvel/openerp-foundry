from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
from datetime import date
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_consumable_rate(osv.osv):

	_name = "kg.consumable.rate"
	_description = "Consumable Rate Master"
	
	#~ def _get_modify(self, cr, uid, ids, field_name, arg, context=None):
		#~ res={}
		#~ stock_obj = self.pool.get('kg.stock.inward')
		#~ weekly_sch_obj = self.pool.get('kg.weekly.schedule')				
		#~ for item in self.browse(cr, uid, ids, context=None):
			#~ res[item.id] = 'no'
			#~ stock_ids = stock_obj.search(cr,uid,[('division_id','=',item.id)])
			#~ weekly_sch_ids = weekly_sch_obj.search(cr,uid,[('division_id','=',item.id)])			
			#~ if stock_ids or weekly_sch_ids:
				#~ res[item.id] = 'yes'		
		#~ return res
	
	_columns = {
	
	
			
		'effective_from': fields.date('Effective From', size=128, required=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'category': fields.selection([('power','Power(Per Unit)'),('petrol','Petrol(Per Ltr)'),('diesel','Diesel(Per Ltr)'),('km','KM')],'Category', required=True),
		'value': fields.float('Value', required=True),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled'),('expire','Expired')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		#~ 'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.consumable.rate', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':fields.datetime.now,	
		'effective_from' : lambda * a: time.strftime('%Y-%m-%d'),
		#~ 'modify': 'no',
		
	}
	
		
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])		
		obj_ids = self.search(cr,uid,[('category','=',rec.category),('id','!=',rec.id),('state','!=','expire')])
		if obj_ids:
			obj_rec = self.browse(cr,uid,obj_ids[0])			
			if rec.effective_from < obj_rec.effective_from:
				raise osv.except_osv(_('Effective From Date !!'),
				_('Previous date not Allow to save !!'))
			self.write(cr,uid,obj_rec.id,{'state':'expire'})	
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
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state not in ('draft','cancel'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_consumable_rate, self).write(cr, uid, ids, vals, context)
		
	def _check_value(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.value <= 0.00:			
			return False
		return True	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)		
		if rec.effective_from > today:			
			return False
		return True	
	
	_constraints = [		
		
		(_check_value, 'System not allow to save negative and zero values !!',['Value']),  
		(_future_entry_date_check, 'System not allow to save with future date. !!',['Effective From']), 		
		
	   ]	
	
	
kg_consumable_rate()
