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


class kg_outwardmaster(osv.osv):

	_name = "kg.outwardmaster"
	_description = "Outward Master"
	_columns = {
		
		'name': fields.char('Outward Type', size=128, required=True, select=True,readonly=False,states={'approved':[('readonly',True)]}),
		'creation_date':fields.datetime('Creation Date',readonly=True),
		'bill': fields.boolean('Bill Indication',readonly=False,states={'approved':[('readonly',True)]}),
		'return': fields.boolean('Return Indication',readonly=False,states={'approved':[('readonly',True)]}),
		'valid': fields.boolean('Valid Indication',readonly=False,states={'approved':[('readonly',True)]}),
		'active': fields.boolean('Active',readonly=True),
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
	
	_sql_constraints = [
		('name', 'unique(name)', 'Outward Type must be unique!'),
	]
	
	_defaults = {
	
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.segment', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
	
	
	}
	
	def write(self, cr, uid, ids, vals, context=None): 
		v_name = None 
		
		if vals.get('name'): 
			v_name = vals['name'].strip() 
			vals['name'] = v_name.capitalize()
						
		result = super(kg_outwardmaster,self).write(cr, uid, ids, vals, context=context) 
		return result
		
	def create(self, cr, uid, vals, context=None): 
		v_name = None 
		if vals.get('name'): 
			v_name = vals['name'].strip() 
			vals['name'] = v_name.capitalize() 
		
			
		result = super(kg_outwardmaster,self).create(cr, uid, vals, context=context) 
		return result

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
	
kg_outwardmaster()
