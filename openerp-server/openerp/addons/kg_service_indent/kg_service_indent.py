import math
import re
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp


class kg_service_indent(osv.osv):

	_name = "kg.service.indent"
	_description = "KG Service Indent"
	_order = "date desc"

	
	_columns = {
	
		'name': fields.char('Indent No', size=64, readonly=True),
		'dep_name': fields.many2one('kg.depmaster','Department', translate=True,required=True, select=True,readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'date': fields.date('Indent Date',required=True,readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'service_indent_line': fields.one2many('kg.service.indent.line', 'service_id',
					'Indent Lines',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'active': fields.boolean('Active',readonly=True),
		'user_id' : fields.many2one('res.users', 'Created By', readonly=True),
		'state': fields.selection([('draft', 'Draft'),('confirm','Waiting For Approval'),('approved','Approved'),('done','Done'),('cancel','Cancel')], 'Status', track_visibility='onchange', required=True),
		'gate_pass': fields.boolean('Gate Pass', readonly=True, states={'draft':[('readonly', False)],'confirm':[('readonly',False)]}),
		'creation_date':fields.datetime('Creation Date',required=True,readonly=True),
		'origin': fields.char('Source Location', size=264,readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'remark': fields.text('Remarks'),
		'confirmed_by' : fields.many2one('res.users', 'Confirmed By', readonly=False,select=True),
		'approved_by' : fields.many2one('res.users', 'Approved By', readonly=False,select=True),
		'approved_date' : fields.date('Approved Date'),
		'dep_project':fields.many2one('kg.project.master','Dept/Project Name',readonly=True,states={'draft': [('readonly', False)],'confirm':[('readonly',False)]}),	

	}
	
	_sql_constraints = [('code_uniq','unique(name)', 'Indent number must be unique!')]

	_defaults = {
		
		'state' : 'draft',
		'active' : 'True',
		'date' : fields.date.context_today,
		'user_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),

	}
	
	def email_ids(self,cr,uid,ids,context = None):
		email_from = []
		email_to = []
		email_cc = []
		val = {'email_from':'','email_to':'','email_cc':''}
		ir_model = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		mail_form_ids = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		for ids in mail_form_ids:
			mail_form_rec = self.pool.get('kg.mail.settings').browse(cr,uid,ids)
			if mail_form_rec.doc_name.model == 'kg.service.indent':
				email_from.append(mail_form_rec.name)
				mail_line_id = self.pool.get('kg.mail.settings.line').search(cr,uid,[('line_entry','=',ids)])
				for mail_id in mail_line_id:
					mail_line_rec = self.pool.get('kg.mail.settings.line').browse(cr,uid,mail_id)
					if mail_line_rec.to_address:
						email_to.append(mail_line_rec.mail_id)
					if mail_line_rec.cc_address:
						email_cc.append(mail_line_rec.mail_id)
						
			else:
				pass		
		val['email_from'] = email_from
		val['email_to'] = email_to
		val['email_cc'] = email_cc
		return val
	
	def draft_indent(self, cr, uid, ids,context=None):
		
		self.write(cr,uid,ids,{'state':'draft'})
		return True
		
	def confirm_indent(self, cr, uid, ids,context=None):
		self.write(cr,uid,ids,{
			'name':self.pool.get('ir.sequence').get(cr, uid, 'kg.service.indent') or False,
			'state': 'confirm',
			'confirmed_by':uid
			})	
		
		#cr.execute("""select all_transaction_mails('Service Indent Request Approval',%s)"""%(ids[0]))
		"""Raj
		data = cr.fetchall();
		vals = self.email_ids(cr,uid,ids,context = context)
		if (not vals['email_to']) or (not vals['email_cc']):
			pass
		else:
			ir_mail_server = self.pool.get('ir.mail_server')
			msg = ir_mail_server.build_email(
					email_from = vals['email_from'][0],
					email_to = vals['email_to'],
					subject = "Service Indent Request - Waiting For Approval",
					body = data[0][0],
					email_cc = vals['email_cc'],
					object_id = ids[0] and ('%s-%s' % (ids[0], 'kg.service.indent')),
					subtype = 'html',
					subtype_alternative = 'plain')
			res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
		"""
		return True
			
	def approve_indent(self, cr, uid, ids,context=None):
		obj = self.browse(cr,uid,ids[0])
		
		#if obj.confirmed_by.id == uid:
		#	raise osv.except_osv(
		#			_('Warning'),
		#			_('Approve cannot be done by Confirmed user'))
		#else:
		self.write(cr,uid,ids,{'state':'approved','approved_by':uid,'approved_date':time.strftime('%Y-%m-%d')})
		#cr.execute("""select all_transaction_mails('Service Indent Request Approval',%s)"""%(ids[0]))
		"""Raj
		data = cr.fetchall();
		vals = self.email_ids(cr,uid,ids,context = context)
		if (not vals['email_to']) or (not vals['email_cc']):
			pass
		else:
			ir_mail_server = self.pool.get('ir.mail_server')
			msg = ir_mail_server.build_email(
					email_from = vals['email_from'][0],
					email_to = vals['email_to'],
					subject = "Service Indent Request - Approved",
					body = data[0][0],
					email_cc = vals['email_cc'],
					object_id = ids[0] and ('%s-%s' % (ids[0], 'kg.service.indent')),
					subtype = 'html',
					subtype_alternative = 'plain')
			res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
		"""
		return True
	
	def cancel_indent(self, cr, uid, ids, context=None):		
		self.write(cr, uid,ids,{'state' : 'cancel'})
		return True

	def unlink(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		indent = self.read(cr, uid, ids, ['state'], context=context)
		unlink_ids = []
		for t in indent:
			if t['state'] in ('draft'):
				unlink_ids.append(t['id'])
			else:
				raise osv.except_osv(_('Invalid action !'), _('System not allow to delete a UN-DRAFT state Department Indent!!'))
		indent_lines_to_del = self.pool.get('kg.service.indent.line').search(cr, uid, [('service_id','in',unlink_ids)])
		self.pool.get('kg.service.indent.line').unlink(cr, uid, indent_lines_to_del)
		osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		return True
		
	def _check_lineitem(self, cr, uid, ids, context=None):
		for si in self.browse(cr,uid,ids):
			if si.service_indent_line==[] or si.service_indent_line:
					tot = 0.0
					for line in si.service_indent_line:
						tot += line.qty
					if tot <= 0.0:			
						return False
						
			return True
	
	_constraints = [
	
		(_check_lineitem, 'You can not save this Service Indent with out Line and Zero Qty  !!',['qty']),

		]	

kg_service_indent()

class kg_service_indent_line(osv.osv):
	
	_name = "kg.service.indent.line"
	_description = "Service Indent"

	def onchange_product_id(self, cr, uid, ids, product_id, uom,context=None):
			
		value = {'uom': ''}
		if product_id:
			prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			value = {'uom': prod.uom_id.id}

		return {'value': value}
		
	def onchange_qty(self,cr,uid,ids,qty,pending_qty,issue_pending_qty,context=None):
		print "called onchange_qty................."
		value = {'pending_qty': '', 'issue_pending_qty':'','gate_pending_qty':'',}
		if qty:
			pending_qty = qty
			value = {'pending_qty' : pending_qty, 'issue_pending_qty' : pending_qty,'gate_pending_qty':pending_qty}
		return {'value': value}
	
	
	_columns = {

	'service_id': fields.many2one('kg.service.indent', 'Indent No', required=True, ondelete='cascade'),
	'product_id': fields.many2one('product.product', 'Product', required=True,domain = [('state','=','approved')]),
	'uom': fields.many2one('product.uom', 'UOM', required=True),
	'qty': fields.float('Quantity', required=True),
	'pending_qty':fields.float('Pending Qty'),
	'issue_pending_qty':fields.float('Issue Pending Qty'),
	'gate_pending_qty':fields.float('Gate Pass Pending Qty'),
	'note': fields.text('Remarks'),	
	'line_state': fields.selection([('process','Processing'),('noprocess','NoProcess'),('pi_done','PI-Done'),('done','Done')], 'Status'),
	'line_date': fields.date('Indent Date'),
	'brand_id':fields.many2one('kg.brand.master','Brand'),
	'ser_no':fields.char('Ser No', size=128),
	'serial_no':fields.many2one('stock.production.lot','Serial No',domain="[('product_id','=',product_id)]"),
	'return_qty':fields.float('Return Qty'),
	}

	_defaults = {

		'line_date' : fields.date.context_today,

	}
	
	
	
		
	
	
kg_service_indent_line()	
