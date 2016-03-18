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
	
	def _get_modify(self, cr, uid, ids, field_name, arg, context=None):
		res={}
		ser_obj = self.pool.get('kg.service.order')
		ser_order_obj = self.pool.get('kg.service.order')
		po_amen_obj = self.pool.get('kg.purchase.amendment')
		po_amend_obj = self.pool.get('kg.purchase.amendment')
		po_obj = self.pool.get('purchase.order')
		po_name_obj = self.pool.get('purchase.order')
		ser_ind_obj = self.pool.get('kg.service.indent')
		ser_inv_obj = self.pool.get('kg.service.invoice')
		dep_ind_obj = self.pool.get('kg.depindent')
		pur_ind_obj = self.pool.get('purchase.requisition')
		gate_obj = self.pool.get('kg.gate.pass')
		for h in self.browse(cr, uid, ids, context=None):
			res[h.id] = 'no'
			ser_ids = ser_obj.search(cr,uid,[('origin_project','=',h.id)])
			ser_order_ids = ser_order_obj.search(cr,uid,[('origin','=',h.name)])
			po_amen_ids = po_amen_obj.search(cr,uid,[('dep_project_amend','=',h.id)])
			po_amend_ids = po_amend_obj.search(cr,uid,[('dep_project_name_amend','=',h.name)])
			po_ids = po_obj.search(cr,uid,[('dep_project','=',h.id)])
			po_name_ids = po_name_obj.search(cr,uid,[('dep_project_name','=',h.name)])
			ser_ind_ids = ser_ind_obj.search(cr,uid,[('dep_project','=',h.id)])
			ser_inv_ids = ser_inv_obj.search(cr,uid,[('dep_project','=',h.id)])
			dep_ind_ids = dep_ind_obj.search(cr,uid,[('dep_project','=',h.id)])
			pur_ind_ids = pur_ind_obj.search(cr,uid,[('dep_project','=',h.id)])
			gate_ids = gate_obj.search(cr,uid,[('dep_project','=',h.id)])
			if ser_ids or ser_order_ids or po_amen_ids or po_amend_ids or po_ids or po_name_ids or ser_ind_ids or ser_inv_ids or dep_ind_ids or pur_ind_ids or gate_ids:
				res[h.id] = 'yes'
		print "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",res
		return res
		
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.project.master', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'date':fields.datetime.now,
		'modify': 'no',
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Name must be unique per Company !!'),
		('code', 'unique(code)', 'Code must be unique per Company !!'),
	]

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
		return super(kg_project_master, self).write(cr, uid, ids, vals, context)
	
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
kg_project_master()
