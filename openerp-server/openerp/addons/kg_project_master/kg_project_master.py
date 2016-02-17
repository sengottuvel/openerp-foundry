from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
a = datetime.now()
dt_time = a.strftime('%m/%d/%Y %H:%M:%S')

### All many2one field should end with _id. Ex : user_id, partner_id, employee_id
### All one2many fields name should line_ids
### All many2many field should end with _ids. EX : tax_ids, user_ids
### All date fields should end with date
### Parent table id in child table should be in "header_id"
### Quantity filed should be "float"


class kg_project_master(osv.osv):

	_name = "kg.project.master"
	_description = "KG Project Master"
	
	_columns = {

		'date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'name': fields.char('Name', size=128, required=True, select=True,
						readonly=True, states={'draft':[('readonly',False)]}),
		
		'code': fields.char('Code', size=3, required=True,readonly=True, states={'draft':[('readonly',False)]}),
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Apprved By', readonly=True),
		'confirm_date': fields.datetime('Confirm Date', readonly=True),
		'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'reject_date': fields.datetime('Reject Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'state': fields.selection([('draft','Draft'),('confirm','Waiting for approval'),('approved','Approved'),
				('reject','Rejected')],'Status', readonly=True),
		'remark': fields.text('Remarks',readonly=False, states={'approved':[('readonly',True)]}),
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.segment', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'date':fields.datetime.now,
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Name must be unique per Company !!'),
		('code', 'unique(code)', 'Code must be unique per Company !!'),
	]

	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

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
kg_project_master()
