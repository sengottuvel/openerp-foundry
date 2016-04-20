from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import re
from operator import itemgetter
from itertools import groupby
from datetime import datetime
a = datetime.now()
dt_time = a.strftime('%m/%d/%Y %H:%M:%S')
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)


class kg_inwardmaster(osv.osv):

	_name = "kg.inwardmaster"
	_description = "Inward Master"
	
	def _get_modify(self, cr, uid, ids, field_name, arg, context=None):
		res={}
		acc_vou_obj = self.pool.get('kg.contractor.inward.line')
		stock_obj = self.pool.get('stock.picking')
		po_grn_obj = self.pool.get('kg.po.grn')
		po_grn_line_obj = self.pool.get('po.grn.line')
		gen_grn_obj = self.pool.get('kg.general.grn')
		gen_grn_line_obj = self.pool.get('kg.general.grn.line')
		for h in self.browse(cr, uid, ids, context=None):
			res[h.id] = 'no'
			acc_vou_ids = acc_vou_obj.search(cr,uid,[('inward_type','=',h.id)])
			stock_ids = stock_obj.search(cr,uid,[('inward_type','=',h.id)])
			po_grn_ids = po_grn_obj.search(cr,uid,[('inward_type','=',h.id)])
			po_grn_line_ids = po_grn_line_obj.search(cr,uid,[('inward_type','=',h.id)])
			gen_grn_ids = gen_grn_obj.search(cr,uid,[('inward_type','=',h.id)])
			gen_grn_line_ids = gen_grn_line_obj.search(cr,uid,[('inward_type','=',h.id)])
			if acc_vou_ids or stock_ids or po_grn_ids or po_grn_line_ids or gen_grn_ids or gen_grn_line_ids:
				res[h.id] = 'yes'
		print "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",res
		return res
		
	_columns = {
		
		'name': fields.char('Name', size=128, required=True, select=True,readonly=False,states={'approved':[('readonly',True)]}),
		'code': fields.char('Code',readonly=False,states={'approved':[('readonly',True)]}),
		'creation_date':fields.datetime('Creation Date',readonly=True),
		'bill': fields.boolean('Bill Indication',readonly=False,states={'approved':[('readonly',True)]}),
		'return': fields.boolean('Return Indication',readonly=False,states={'approved':[('readonly',True)]}),
		'valid': fields.boolean('Valid Indication',readonly=False,states={'approved':[('readonly',True)]}),
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Apprved By', readonly=True),
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
	
	_sql_constraints = [
		('name', 'unique(name)', 'Inward Type must be unique!'),
	]
	
	
	_defaults = {
	
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.inwardmaster', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'modify': 'no',
		
	}
	
	def write(self, cr, uid, ids, vals, context=None): 
		v_name = None 
		
		if vals.get('name'): 
			v_name = vals['name'].strip() 
			vals['name'] = v_name.capitalize()
						
		result = super(kg_inwardmaster,self).write(cr, uid, ids, vals, context=context) 
		return result
		
	def create(self, cr, uid, vals, context=None): 
		v_name = None 
		if vals.get('name'): 
			v_name = vals['name'].strip() 
			vals['name'] = v_name.capitalize() 
		
		result = super(kg_inwardmaster,self).create(cr, uid, vals, context=context) 
		return result

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
		return super(kg_inwardmaster, self).write(cr, uid, ids, vals, context)
	"""	
	def unlink(self,cr,uid,ids,context=None):
		raise osv.except_osv(_('Warning!'),
				_('You can not delete Entry !!'))		
	
	
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
	
kg_inwardmaster()
