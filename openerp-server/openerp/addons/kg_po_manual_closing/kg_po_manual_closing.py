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

class kg_po_manual_closing(osv.osv):

	_name = "kg.po.manual.closing"
	_description = "PO Manual Closing Module"
	_order = "trans_date desc"
	
	_columns = {

		'date': fields.datetime('Creation Date', readonly=True)	,
		'c_date': fields.date('Creation Date', readonly=True),
		'user_id': fields.many2one('res.users','Created By', readonly=True),		
		'name': fields.char('No', size=128,select=True,readonly=True),
		'trans_date': fields.date('As On Date', readonly=True, states={'draft':[('readonly',False)]},
											select=True, required=True),						
		'partner_id': fields.many2one('res.partner', 'Supplier', select=True,
					domain=[('supplier', '=', True)], readonly=True, states={'draft':[('readonly',False)]}),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),		
		'line_ids':fields.one2many('kg.po.manual.closing.line', 'header_id', 'Transaction Line',readonly=True, states={'draft':[('readonly',False)]}),
		'remark': fields.text('Remarks', readonly=True, states={'draft':[('readonly',False)]}),		
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
		'active': fields.boolean('Active'),
		'total': fields.float('Total Amount', readonly=True),
		'po_id':fields.many2one('purchase.order','PO No',domain="[('state','=','approved')]",readonly=False, states={'approved':[('readonly',True)]}),
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_po_manual_closing', context=c),			
		'trans_date' : fields.date.context_today,
		'c_date' : fields.date.context_today,
		'date':fields.datetime.now,		
		'state': 'draft',		
		'active': True,
		'user_id': lambda obj, cr, uid, context: uid,
		
	}

	def _future_date_check(self,cr,uid,ids,contaxt=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		trans_date = rec.trans_date
		trans_date = str(trans_date)
		trans_date = datetime.strptime(trans_date, '%Y-%m-%d')
		if trans_date > today:
			return False
		return True		
	
	def _check_line_entry(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if not entry.line_ids:
			return False
		else:
			for line in entry.line_ids:
				if line.unit_price == 0 or line.quantity == 0:
					return False
		return True
	
	_constraints = [        
              
        #(_check_line_entry, 'System not allow to save empty transaction and zero qty .!!',['price']),
        (_future_date_check, 'System not allow to save with future date. !!',['price']),
        
       ]

	
	def load_item(self,cr,uid,ids,context=None):		
		rec =  self.browse(cr,uid,ids[0])
		
		supplier = []
		if rec.line_ids:
			del_sql = """ delete from kg_po_manual_closing_line where header_id=%s """ %(ids[0])
			cr.execute(del_sql)
				
		if rec.partner_id:
			
			supplier.append("partner_id = '%s'"%(rec.partner_id.id))
				
			
		if supplier:
			supplier = 'and ('+' or '.join(supplier)
			supplier =  supplier+')'
			
		else:
			supplier = ''
		
		sql = """ select * from purchase_order_line where state = 'confirmed' and pending_qty > 0 and date_planned >='"""+rec.trans_date+"""'"""+ supplier +""" """
		
		cr.execute(sql)
		data = cr.dictfetchall()
		
		for item in data:
		
			vals = {
				'po_id':item['order_id'],
				'po_line_id':item['id'],
				'product_id':item['product_id'],
				'partner_id':item['partner_id'],
				'uom_id':item['product_uom'],
				'quantity':item['pending_qty'],
				'unit_price':item['price_unit'],
				
				'total':item['pending_qty'] * item['price_unit'],
				'header_id':rec.id,
				'close_state':'open'
				}				
				
			if ids:
				self.write(cr,uid,ids[0],{'line_ids':[(0,0,vals)]})
		
	
		return True	


	def entry_confirm(self,cr,uid,ids,context=None):		
		cr.execute(''' select count(*) from kg_po_manual_closing where state !='draft' ''')
		data = cr.fetchone()
		order_by = data[0] + 1		
		self.write(cr, uid, ids, {
					'state': 'confirm',
					'conf_user_id': uid,
					'confirm_date': dt_time,
					'name' : self.pool.get('ir.sequence').get(cr, uid, 'kg.po.manual.closing'),
					'orderby_no':order_by,
					})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		po_line_obj = self.pool.get('purchase.order.line')		
		po_obj = self.pool.get('purchase.order')
		rec =  self.browse(cr,uid,ids[0])
		for line in rec.line_ids:
			if line.close_state == 'close':
				po_line_obj.write(cr,uid,line.po_line_id.id, {'state':'cancel'})
				po_record = po_obj.browse(cr,uid,line.po_id.id)
				po_line_record = po_line_obj.browse(cr,uid,line.po_line_id.id)
				line_total = po_line_record.price_subtotal
				po_total = po_record.amount_total
				amount_total = po_total - line_total
				print  "---------------------------------->",amount_total
				line_untax = line.total
				po_untax = po_record.amount_untaxed
				amount_untaxed = po_untax - line_untax
				print  "---------------------------------->",amount_untaxed
				if po_record.amount_tax > 0:
				
					line_tax = po_line_record.price_subtotal - (line.total - (po_line_record.kg_discount + po_line_record.kg_discount_per_value))  
					po_tax = po_record.amount_tax
					amount_tax = po_tax - line_tax
				else:
					amount_tax = 0	
				
				if po_record.discount > 0:
					line_discount = (po_line_record.kg_discount + po_line_record.kg_discount_per_value)
					po_discount = po_record.discount
					discount = po_discount - line_discount
					
				else:
					discount = 0		
				
				sql = """ update purchase_order set amount_total=%s,amount_untaxed = %s,amount_tax = %s,discount = %s where id = %s"""%((round(amount_total,0)),(round(amount_untaxed,0)),(round(amount_tax,0)),(round(discount,0)),line.po_id.id)
				cr.execute(sql)
				
						
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
	
kg_po_manual_closing()


class kg_po_manual_closing_line(osv.osv):
	
	_name = "kg.po.manual.closing.line"
	_description = "PO Manual Closing Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.po.manual.closing','Transaction',ondelete='cascade',select=True),
		'product_id': fields.many2one('product.product', 'Item Name', required=True),
		'uom_id': fields.many2one('product.uom', 'UOM', required=True),
		'quantity': fields.float('Quantity', required=True),
		'unit_price': fields.float('Unit Price', required=True),
		'tax_ids': fields.many2many('account.tax','po_close_taxes', 'line_id','tax_id', 'Taxes'),
		'total': fields.float('Total'),
		'remark': fields.text('Remark'),
		'discount': fields.float('Discount(%)'),
		'po_id':fields.many2one('purchase.order', 'PO NO'),
		'po_line_id':fields.many2one('purchase.order.line', 'PO Line'),
		'version':fields.char('Version'),
		'dep_project_name':fields.char('Dept/Project Name',readonly=False),
		'remark': fields.text('Remark'),
		'close_state': fields.selection([('open','Open'),('close','Close')],'Closing state',readonly=False),
		'partner_id': fields.many2one('res.partner', 'Supplier', select=True,
					domain=[('supplier', '=', True)], readonly=True),
	}	
	
kg_po_manual_closing_line()
