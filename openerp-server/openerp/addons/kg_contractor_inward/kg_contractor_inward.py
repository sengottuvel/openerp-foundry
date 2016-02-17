from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

a = datetime.now()
dt_time = a.strftime('%m/%d/%Y %H:%M:%S')

### All many2one field should end with _id. Ex : user_id, partner_id, employee_id
### All one2many fields name should line_ids
### All many2many field should end with _ids. EX : tax_ids, user_ids
### All date fields should end with date
### Parent table id in child table should be in "header_id"

class kg_contractor_inward(osv.osv):

	_name = "kg.contractor.inward"
	_description = "Kg Contractor Iinward"
	_order = "inward_date desc"
	
	_columns = {

		'date': fields.datetime('Creation Date', readonly=True)	,
		'user_id': fields.many2one('res.users','Created By', readonly=True),		
		'name': fields.char('Inward No', size=128,select=True,readonly=True),
		'inward_date': fields.date('Inward Date', readonly=True, states={'draft':[('readonly',False)]},select=True, required=True),	
			
		'dc_no': fields.char('DC No', size=128,readonly=True, states={'draft':[('readonly',False)]}, required=True),
		'dc_date': fields.date('DC Date', readonly=True, states={'draft':[('readonly',False)]},select=True, required=True),						
							
		'supplier_id':fields.many2one('res.partner','Supplier',domain=[('supplier','=',True)],readonly=True,required=True, states={'draft':[('readonly',False)]}),
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),		
		'line_ids':fields.one2many('kg.contractor.inward.line', 'header_id', 'Line Entry',readonly=True, states={'draft':[('readonly',False)]}),
		'remark': fields.text('Remarks'),		
		'state': fields.selection([('draft','Draft'),('confirm','Waiting for approval'),('approved','Approved'),
				('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True,track_visibility='onchange',select=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Apprved By', readonly=True),
		'confirm_date': fields.datetime('Confirm Date', readonly=True),
		'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'reject_date': fields.datetime('Reject Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'cancel_date': fields.datetime('Cancel Date', readonly=True),
		'can_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'orderby_no': fields.integer('Order By',readonly=True),
		'active': fields.boolean('Active',readonly=True),
		'total': fields.float('Total Amount', readonly=True),
		
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_contractor_inward', context=c),			
		'inward_date' : fields.date.context_today,
		'date':fields.datetime.now,		
		'state': 'draft',		
		'active': True,
		'user_id': lambda obj, cr, uid, context: uid,
		
	}

	def create(self, cr, uid, vals, context=None):
		v_name = None 
		if vals.get('name','/')=='/':
			vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'kg.contractor.inward') or '/'
		
		order =  super(kg_contractor_inward, self).create(cr, uid, vals, context=context) 
		return order

	def _future_date_check(self,cr,uid,ids,contaxt=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		inward_date = rec.inward_date
		inward_date = str(inward_date)
		inward_date = datetime.strptime(inward_date, '%Y-%m-%d')
		if inward_date > today:
			return False
		return True		
	
	def _check_line_entry(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if not entry.line_ids:
			return False
		else:
			for line in entry.line_ids:
				if line.quantity <= 0:
					return False
		return True
	
	_constraints = [        
              
        (_check_line_entry, 'System not allow to save empty inward and zero qty .!!',['price']),
        (_future_date_check, 'System not allow to save with future date. !!',['price']),
        
       ]

	def entry_confirm(self,cr,uid,ids,context=None):		
		cr.execute(''' select count(*) from kg_contractor_inward where state !='draft' ''')
		data = cr.fetchone()
		order_by = data[0] + 1		
		self.write(cr, uid, ids, {
					'state': 'confirm',
					'conf_user_id': uid,
					'confirm_date': dt_time,
					'name' : self.pool.get('ir.sequence').get(cr, uid, 'kg.contractor.inward'),
					'orderby_no':order_by,
					})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.conf_user_id.id == uid:
			raise osv.except_osv(
					_('Warning'),
					_('Approve cannot be done by Confirmed user'))	
		self.write(cr, uid, ids, {
				'state': 'approved',
				'app_user_id': uid,
				'approve_date': dt_time})

		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {
						'state': 'reject',
						'rej_user_id': uid,
						'reject_date': dt_time})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter rejection remark in remark field !!'))
		return True

	def entry_cancel(self,cr,uid,ids,context=None):
		## Don't allow to cancel if this id linked with other transaction or master
		self.write(cr, uid, ids, {'state': 'cancel','can_user_id': uid,
				'cancel_date': dt_time})
		return True

	def entry_draft(self,cr,uid,ids,context=None):
		# While change state corresponding back updated to be done
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)	
	
kg_contractor_inward()


class kg_contractor_inward_line(osv.osv):
	
	_name = "kg.contractor.inward.line"
	_description = "kg contractor inward Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.contractor.inward','Inward Entry',ondelete='cascade',select=True),
		'product_id': fields.many2one('product.product', 'Item Name', required=True, domain=[('state','=','approved')]),
		'uom_id': fields.many2one('product.uom', 'UOM', required=True),
		'quantity': fields.float('Quantity', required=True),
		'pending_qty': fields.float('Pending Quantity'),
		'brand_id':fields.many2one('kg.brand.master','Brand'),
		'inward_type': fields.many2one('kg.inwardmaster', 'Inward Type'),
		
	}	
	
	def onchange_uom_id(self, cr, uid, ids, product_id, context=None):
		
		value = {'uom_id': ''}
		if product_id:
			pro_rec = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			value = {'uom_id': pro_rec.uom_id.id}
		return {'value': value}	
		
kg_contractor_inward_line()
