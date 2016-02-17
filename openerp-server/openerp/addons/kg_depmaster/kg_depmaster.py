from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import re
from operator import itemgetter
from itertools import groupby

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

class kg_depmaster(osv.osv):

	_name = "kg.depmaster"
	_description = "Department Master"
	_rec_name = 'dep_name' 
	
	_columns = {
		'name': fields.char('Dep.Code', size=64, required=True, readonly=True),
		'dep_name': fields.char('Dep.Name', size=64, required=True, translate=True,readonly=False,states={'approved':[('readonly',True)]}),
		'consumerga': fields.many2one('account.account', 'Consumer GL/AC', size=64, translate=True, select=2),
		'cost': fields.many2one('account.account','Cost Centre', size=64, translate=True, select=2),
		'stock_location': fields.many2one('stock.location', 'Dep.Stock Location', size=64, translate=True, 
					select=True, required=True, domain=[('usage','<>','view')],readonly=False,states={'approved':[('readonly',True)]}),
					
		'main_location': fields.many2one('stock.location', 'Main Stock Location', size=64, translate=True, 
					select=True, required=True, domain=[('usage','<>','view')],readonly=False,states={'approved':[('readonly',True)]}),
		'used_location': fields.many2one('stock.location', 'Used Stock Location', size=64, translate=True, 
					select=True, required=True, domain=[('usage','<>','view')],readonly=False,states={'approved':[('readonly',True)]}),
		'creation_date':fields.datetime('Creation Date',readonly=True),
		'product_id': fields.many2many('product.product', 'product_deparment', 'depmaster_id', 'product_depid', 'Product'),
		'issue_period': fields.selection([('weekly','Weekly'), ('15th','15th Once'), ('monthly', 'Monthly')], 'Stock Issue Period'),
		'issue_date': fields.float('Stock Issue Days'),
		'active': fields.boolean("Active"),
		'sub_indent': fields.boolean("Sub.Store.Ind"),
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
		'name':'/',
	}
	_sql_constraints = [
		('code_uniq', 'unique(name)', 'Department code must be unique!'),
		('name_uniq', 'unique(dep_name)', 'Department name must be unique !'),
	]
	
	def create(self, cr, uid, vals, context=None):
		v_name = None 
		if vals.get('name','/')=='/':
			vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'kg.depmaster') or '/'
		if vals.get('dep_name'): 
			v_name = vals['dep_name'].strip() 
			vals['dep_name'] = v_name.capitalize() 
		order =  super(kg_depmaster, self).create(cr, uid, vals, context=context) 
		return order
		
	def write(self, cr, uid, ids, vals, context=None):
		v_name = None 
		if vals.get('dep_name'): 
			v_name = vals['dep_name'].strip() 
			vals['dep_name'] = v_name.capitalize()
		order =  super(kg_depmaster, self).write(cr, uid, ids, vals, context=context) 
		return order
	
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

kg_depmaster()


class custom_sequence_generate_det(osv.osv):
    _name = 'custom.sequence.generate.det'
    _order = 'name'
    _columns = {
        'name': fields.char('Name',size=64),
        'ir_sequence_id': fields.many2one('ir.sequence', 'Sequence'),
        'seq_month' : fields.integer('Sequence Month'),
        'seq_year' : fields.integer('Sequence Year'),
        'seq_next_number' : fields.integer('Sequence Next Number'),
        'fiscal_year_code' : fields.char('Fiscal Year Code',size=64),
        'fiscal_year_id' : fields.integer('Fiscal Year ID'),
    }
custom_sequence_generate_det()
