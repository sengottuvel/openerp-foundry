from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_contractor_master(osv.osv):

	_name = "kg.contractor.master"
	_description = "Contractor Master"
	
	"""
	def _get_modify(self, cr, uid, ids, field_name, arg, context=None):
		res={}
		stock_obj = self.pool.get('kg.stock.inward')
		weekly_sch_obj = self.pool.get('kg.weekly.schedule')				
		for item in self.browse(cr, uid, ids, context=None):
			res[item.id] = 'no'
			stock_ids = stock_obj.search(cr,uid,[('contractor_id','=',item.id)])
			weekly_sch_ids = weekly_sch_obj.search(cr,uid,[('contractor_id','=',item.id)])			
			if stock_ids or weekly_sch_ids:
				res[item.id] = 'yes'		
		return res
	"""
	_columns = {
			
		'name': fields.char('Name', size=128, required=True, select=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'pan_no': fields.char('PAN', size=128, required=True),
		'aadhar_no': fields.char('Aadhar', size=128),
		'service_type': fields.selection([('self','Self'),('labour_supply','Labour Supply')],'Service Type', required=True),	
		'category_id': fields.many2one('kg.contractor.category', 'Category' , required=True ,domain="[('active','=','t')]"),
		'shift_id': fields.many2one('kg.shift.master', 'Shift' ,domain="[('active','=','t')]"),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'line_ids':fields.one2many('ch.contractor.rate.details', 'header_id', "Contractor Rate Details"),
		#'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.contractor.master', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':fields.datetime.now,	
		#'modify': 'no',
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Name must be unique per Company !!'),
		
	]
			
	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.name:
			contractor_name = rec.name
			name=contractor_name.upper()			
			cr.execute(""" select upper(name) from kg_contractor_master where upper(name)  = '%s' """ %(name))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
	
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
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
		return super(kg_contractor_master, self).write(cr, uid, ids, vals, context)
		
	
	_constraints = [
		(_name_validate, 'Contractor name must be unique !!', ['name']),			
		
	]
	
kg_contractor_master()



class ch_contractor_rate_details(osv.osv):
	
	_name = "ch.contractor.rate.details"
	_description = "Contractor Rate Details"
	
	_columns = {
			
		'header_id':fields.many2one('kg.contractor.master', 'Contractor Entry', required=True, ondelete='cascade'),				
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=',True)]"),		
		'rate':fields.float('Rate'),		
		'remarks':fields.text('Remarks'),		
	}
	
	
ch_contractor_rate_details()
