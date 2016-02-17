from datetime import *
import time
from osv import fields, osv
from tools.translate import _
import netsvc
import decimal_precision as dp
from itertools import groupby
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
import smtplib
import socket
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
import logging
import netsvc
import pooler
import math
from tools import number_to_text_convert_india
logger = logging.getLogger('server')
today = datetime.now()


class kg_depindent(osv.osv):

	_name = "kg.depindent"
	_description = "Department Indent"
	_rec_name = "name"
	_order = "name desc"
	
	_columns = {
		'name': fields.char('No', size=64, readonly=True,select=True),
		'dep_name': fields.many2one('kg.depmaster','Department', required=True,translate=True, select=True,readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'date': fields.datetime('Creation Date',readonly=True),
		'ind_date': fields.date('Indent Date',readonly=True,states={'draft':[('readonly',False)]}),
		'type': fields.selection([('direct','Direct'), ('from_bom','From BoM')], 'Indent Type',readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'dep_indent_line': fields.one2many('kg.depindent.line', 'indent_id', 'Indent Lines', readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'active': fields.boolean('Active'),
		'user_id' : fields.many2one('res.users', 'Created By', readonly=False,select=True),
		'src_location_id': fields.many2one('stock.location', 'MainStock Location'),
		'dest_location_id': fields.many2one('stock.location', 'DepStock Location'),
		'state': fields.selection([('draft', 'Draft'),('confirm','Waiting For Approval'),('approved','Approved'),('cancel','Cancelled')], 'Status', track_visibility='onchange', required=True),
		'main_store': fields.boolean('For Main Store',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'projection_id':fields.many2one('kg.sale.projection','Projection'),
		'remarks': fields.text('Remarks',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'project':fields.char('Project',size=100,readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'dep_project':fields.many2one('kg.project.master','Dept/Project Name',readonly=True,states={'draft': [('readonly', False)],'confirm':[('readonly',False)]}),
		
		'division':fields.char('Division',size=100,readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'confirmed_by' : fields.many2one('res.users', 'Confirmed By', readonly=False,select=True),
		'approved_by' : fields.many2one('res.users', 'Approved By', readonly=False,select=True),
		'approved_date' : fields.date('Indent Date'),
		'ticket_no':fields.char('Ticket No',size=200,readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'ticket_date':fields.date('Ticket Date',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
	}
	
	_sql_constraints = [('code_uniq','unique(name)', 'Indent number must be unique!')]

	_defaults = {
		'type' : 'direct',
		'state' : 'draft',
		'active' : 'True',
		'date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'user_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
		'ind_date': fields.date.context_today,

	}
	
	
	
	def onchange_ticket_date(self, cr, uid, ids, ticket_date):
		print "kgggggggggggggggggg --  onchange_ticket_date called"
		today_date = today.strftime('%Y-%m-%d')
		bk_date = date.today() - timedelta(days=2)
		back_date = bk_date.strftime('%Y-%m-%d')
		holiday_obj = self.pool.get('kg.holiday.master.line')
		holiday_ids = holiday_obj.search(cr, uid, [('leave_date','=',back_date)])
		
		if ticket_date > today_date:
			raise osv.except_osv(
					_('Warning'),
					_('Ticket Date should be less than or equal to current date!'))	
			
		if holiday_ids:
			hol_bk_date = date.today() - timedelta(days=3)
			hol_back_date = hol_bk_date.strftime('%Y-%m-%d')
			if ticket_date <= hol_back_date:
				raise osv.except_osv(
					_('Warning'),
					_('Department Indent Entry is not allowed for this ticket date!'))
		else:
			if ticket_date <= back_date:
				raise osv.except_osv(
					_('Warning'),
					_('Department Indent Entry is not allowed for this ticket date!'))
			
					
		return True
	
	def _check_lineitem(self, cr, uid, ids, context=None):
		print "called liteitem ___ function"
		indent = self.browse(cr,uid,ids[0])
		if not indent.dep_indent_line:
			return False
		else:
			for line in indent.dep_indent_line:
				if line.qty == 0:
					return False										
		return True
		
	def _check_uomline(self, cr, uid, ids, context=None):
		indent = self.browse(cr,uid,ids[0])
		pro_obj = self.pool.get('product.product')
		if indent.dep_indent_line:			
			for line in indent.dep_indent_line:				
				pro_id = line.product_id.id
				pro_rec = pro_obj.browse(cr,uid,pro_id)
				po_uom = pro_rec.uom_po_id.id
				st_uom = pro_rec.uom_id.id
				uom = line.uom.id
				if uom != po_uom:
					if uom != st_uom:
						return False
				else:
					if uom != st_uom:
						if uom != po_uom:
							return False	
					
			return True
			
	def _check_product_duplicate(self, cr, uid, ids, context=None):
		indent = self.browse(cr,uid,ids[0])
		pro_obj = self.pool.get('product.product')
		if indent.dep_indent_line:			
			for line in indent.dep_indent_line:				
				pro_id = line.product_id
		
	
	_constraints = [
	   #(_check_lineitem, 'Department Indent Line and Qty Can Not Be Empty !!',['qty']),
	   #(_check_uomline, 'Wrong UOM Selection. Check product master and choose correct UOM !!',['uom']),
		]
	
	def email_ids(self,cr,uid,ids,context = None):
		email_from = []
		email_to = []
		email_cc = []
		val = {'email_from':'','email_to':'','email_cc':''}
		ir_model = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		mail_form_ids = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		for ids in mail_form_ids:
			mail_form_rec = self.pool.get('kg.mail.settings').browse(cr,uid,ids)
			if mail_form_rec.doc_name.model == 'kg.depindent':
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
		"""
		Draft Ident
		"""
		self.write(cr,uid,ids,{'state':'draft'})
		return True
		
	def confirm_indent(self, cr, uid, ids,context=None):
		product_obj = self.pool.get('product.product')
		indent_obj = self.browse(cr, uid,ids[0])
		"""
		Indent approve
		"""
		location = self.pool.get('kg.depmaster').browse(cr, uid, indent_obj.dep_name.id, context=context)
		self.write(cr,uid,ids,{'src_location_id' : location.main_location.id,'dest_location_id':location.stock_location.id})
		for t in self.browse(cr,uid,ids):
			if not t.dep_indent_line:
				raise osv.except_osv(
						_('Empty Department Indent'),
						_('You can not confirm an empty Department Indent'))
			depindent_line = t.dep_indent_line[0]
			depindent_line_id = depindent_line.id

			if t.dep_indent_line[0].qty==0:
				raise osv.except_osv(
						_('Error'),
						_('Department Indent quantity can not be zero'))
			for line in t.dep_indent_line:
				product_record = product_obj.browse(cr,uid,line.product_id.id)
				cr.execute("""update kg_depindent_line set uom = %s where id = %s"""%(line.product_id.uom_id.id,line.id))
				if line.uom.id != product_record.uom_po_id.id:
					new_po_qty = line.qty / product_record.po_uom_coeff
					#self.write(cr,uid,line.id,{'po_qty' : new_po_qty})
			self.write(cr,uid,ids,{'state':'confirm',
						'confirmed_by':uid,
						'name' :self.pool.get('ir.sequence').get(cr, uid, 'kg.depindent') or '/'}
						)
			 
			#cr.execute("""select all_transaction_mails('Dept Indent Request Approval',%s)"""%(ids[0]))
			""" Raj
			data = cr.fetchall();
			vals = self.email_ids(cr,uid,ids,context = context)
			if (not vals['email_to']) or (not vals['email_cc']):
				pass
			else:
				ir_mail_server = self.pool.get('ir.mail_server')
				msg = ir_mail_server.build_email(
						email_from = vals['email_from'][0],
						email_to = vals['email_to'],
						subject = "	Department Indent - Waiting For Approval",
						body = data[0][0],
						email_cc = vals['email_cc'],
						object_id = ids[0] and ('%s-%s' % (ids[0], 'kg.depindent')),
						subtype = 'html',
						subtype_alternative = 'plain')
				res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
			return True
			"""
	def approve_indent(self, cr, uid, ids,context=None):
		"""
		Indent approve
		"""
		for t in self.browse(cr,uid,ids):
			#if t.confirmed_by.id == uid:
			#	raise osv.except_osv(
			#			_('Warning'),
			#			_('Approve cannot be done by same user'))
			if not t.dep_indent_line:
				raise osv.except_osv(
						_('Empty Department Indent'),
						_('You can not approve an empty Department Indent'))
			depindent_line = t.dep_indent_line[0]
			depindent_line_id = depindent_line.id
			if t.dep_indent_line[0].qty==0:
				raise osv.except_osv(
						_('Error'),
						_('Department Indent quantity can not be zero'))
		self.write(cr,uid,ids,{'state':'approved','approved_by':uid,'approved_date':time.strftime("%Y-%m-%d")})
		#cr.execute("""select all_transaction_mails('Dept Indent Request Approval',%s)"""%(ids[0]))
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
					subject = "	Department Indent - Approved",
					body = data[0][0],
					email_cc = vals['email_cc'],
					object_id = ids[0] and ('%s-%s' % (ids[0], 'kg.depindent')),
					subtype = 'html',
					subtype_alternative = 'plain')
			res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
		return True
		"""
	def done_indent(self, cr, uid, ids,context=None):
		"""
		Indent Done
		"""
		self.write(cr,uid,ids,{'state':'done'})
		return True
		
	def cancel_indent(self, cr, uid, ids, context=None):
		"""
		Cancel Indent
		"""
		pending_qty = 0
		for indent in self.browse(cr,uid,ids):
			if indent.dep_indent_line[0].qty != indent.dep_indent_line[0].pending_qty or indent.dep_indent_line[0].qty != indent.dep_indent_line[0].issue_pending_qty:
				raise osv.except_osv(
						_('Indent UnderProcessing'),
						_('You can not cancel this Indent because this indent is under processing !!!'))
			else:
				pass
			
		self.write(cr, uid,ids,{'state' : 'cancel'})
		return True
	"""	
	def create(self, cr, uid, vals,context=None):
		print "vals................................",vals
		if vals.get('name','/')=='/':
			vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'kg.depindent') or '/'
		order =  super(kg_depindent, self).create(cr, uid, vals, context=context)
		return order
	"""
	"""	
	def write(self, cr, uid,ids, vals, context=None):
		res = super(kg_depindent, self).write(cr, uid, ids,vals, context)
		
		return res
	"""
		
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
		indent_lines_to_del = self.pool.get('kg.depindent.line').search(cr, uid, [('indent_id','in',unlink_ids)])
		self.pool.get('kg.depindent.line').unlink(cr, uid, indent_lines_to_del)
		osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		return True
		
	def onchange_user_id(self, cr, uid, ids, user_id, context=None):
		value = {'dep_name': ''}
		if user_id:
			user = self.pool.get('res.users').browse(cr, uid, user_id, context=context)
			value = {'dep_name': user.dep_name.id}
		return {'value': value}
	
	def onchange_depname(self, cr, uid, ids, dep_name, src_location_id,dest_location_id,context=None):
		value = {'src_location_id' : '','dest_location_id':''}
		if dep_name:
			location = self.pool.get('kg.depmaster').browse(cr, uid, dep_name, context=context)
			print "locationlocationlocationlocation", location
			value = {'src_location_id' : location.main_location.id,'dest_location_id':location.stock_location.id}
		return {'value' : value}
		
	def print_indent(self, cr, uid, ids, context=None):		
		assert len(ids) == 1, 'This option should only be used for a single id at a time'
		wf_service = netsvc.LocalService("workflow")
		wf_service.trg_validate(uid, 'kg.depindent', ids[0], 'send_rfq', cr)
		datas = {
				 'model': 'kg.depindent',
				 'ids': ids,
				 'form': self.read(cr, uid, ids[0], context=context),
		}
		return {'type': 'ir.actions.report.xml', 'report_name': 'indent.on.screen.report', 'datas': datas, 'nodestroy': True}
	

kg_depindent()

class kg_depindent_line(osv.osv):
	
	_name = "kg.depindent.line"
	_description = "Department Indent Line"
	_rec_name = 'indent_id'
	
	def onchange_product_id(self, cr, uid, ids, product_id, uom, po_uom, context=None):
		print "ids........................",context
		value = {'uom': '', 'po_uom': ''}
		if product_id:
			prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			print "Stock qty ----------------->>>", prod.qty_available
			value = {'uom': prod.uom_id.id, 'po_uom' : prod.uom_po_id.id}
		return {'value': value}
		
	def onchange_product_uom(self, cr, uid, ids, product_id, uom, po_uom,qty, context=None):
			
		value = {'qty': 0.0}
		if qty:			
			value = {'qty': 0.0}
		prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)

		if uom != prod.uom_id.id:
			if uom != prod.uom_po_id.id:				 			
				raise osv.except_osv(
					_('UOM Mismatching Error !'),
					_('You choosed wrong UOM and you can choose either %s or %s for %s !!!') % (prod.uom_id.name,prod.uom_po_id.name,prod.name))
		else:
			if uom != prod.uom_po_id.id:
				if uom != prod.uom_id.id:
								
					raise osv.except_osv(
						_('UOM Mismatching Error !'),
						_('You choosed wrong UOM and you can choose either %s or %s for %s !!!') % (prod.uom_id.name,prod.uom_po_id.name,prod.name))

		return {'value': value}
	
	def onchange_qty(self, cr, uid, ids, uom,product_id, qty, pending_qty, issue_pending_qty,po_qty, context=None):
		value = {'pending_qty': '', 'issue_pending_qty':'', 'po_qty':''}
		prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)

		if product_id and qty:
			if uom != prod.uom_po_id.id:
				dep_po_qty_test = qty / prod.po_uom_coeff
				dep_po_qty = (math.ceil(dep_po_qty_test))
				value = {'pending_qty': qty, 'issue_pending_qty' : qty, 'po_qty' : dep_po_qty }
				print " if value.............................."	, value
			else:
				value = {'pending_qty': qty, 'issue_pending_qty' : qty, 'po_qty' : qty}
				print " elseelse value.............................."	, value

		return {'value': value}
		
		
	"""	
	def onchange_po_uom(self, cr, uid, ids, product_id, uom, po_uom, qty, po_qty, context=None):
		value = {'qty': ''}
		prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
		if product_id and qty:
			po_to_uom_qty = po_qty * prod.po_uom_coeff
			print "po_to_uom_qty;;;;;;;;;;;;;;;;", po_to_uom_qty
			value = {'qty': po_to_uom_qty}
		return True
		"""

			
		
		
	"""
	def _get_prd_qty_pnd(self, cr, uid, ids, name, arg, context=None):
		depindent_obj=self.pool.get('kg.depindent')
		depindent_line_obj=self.pool.get('kg.depindent.line')
		res={}
		for id in ids:
			print "idididi", id
			pen_qty= cr.execute( select qty from kg_depindent_line where id=%s %(str(id)))		 
			data = cr.dictfetchall()
			val = [d['qty'] for d in data if 'qty' in d]
			for num in val:
				dep_indent_line_id =self.pool.get('kg.depindent.line').search(cr, uid, [('id','=',id)])
				for id in dep_indent_line_id:
					depindent_line_obj.write(cr, uid, id, {'pending_qty' : num })
				
		return res
		"""

	def _main_store_qty(self,cr,uid,ids,product_id,context=None):
		print "_main_store_qty,,,,,,,,,,,,,,,,,,"
		
		sql_in = """ select sum(product_qty)
					from stock_move as st_move
					join stock_picking as picking on(picking.id = st_move.picking_id)
					where st_move.state = %s and st_move.product_id = %s and picking.type = %s
					('done',product_id.id,'in')"""
					
		sql_out = """ select sum(product_qty)
					from stock_move as st_move
					join stock_picking as picking on(picking.id = st_move.picking_id)
					where st_move.state = %s and st_move.product_id = %s and picking.type = %s 
					('done',product_id.id,'out') """
		data_in = cr.execute(sql_in)
		data_out = cr.execute(sql_out)
		print "data_in ================>>", data_in
		print "data_out ================>>", data_out
		
	def _get_product_available_func(states, what):
		print "_get_product_available_func~~~~~~~~~~~~~~~~~~~~~~~~"

		def _product_available(self, cr, uid, ids, name, arg, context=None):
			return {}.fromkeys(ids, 0.0)
		return _product_available

	_stock_qty = _get_product_available_func(('done',), ('in', 'out'))
	
	_columns = {

	'indent_id': fields.many2one('kg.depindent', 'Dep.Indent.NO', required=True, ondelete='cascade'),
	'line_date': fields.date('Date', required=True, readonly=True),
	'product_id': fields.many2one('product.product', 'Product', required=True,domain = [('state','=','approved')]),
	'uom': fields.many2one('product.uom', 'UOM', required=True),
	'po_uom': fields.many2one('product.uom', 'PO UOM'),
	'qty': fields.float('Indent Qty', required=True),
	'po_qty': fields.float('PO Qty',),
	'pending_qty': fields.float('PI Pending Qty'),
	'issue_pending_qty': fields.float('Issue.Pending Qty'),
	#'main_store_qty': fields.float('Main Store Qty'),
	'main_store_qty': fields.function(_stock_qty, type='float', string='Quantity On Hand'),
	'dep_id': fields.many2one('kg.depmaster', 'Dep.Name'),
	'line_state': fields.selection([('process','Processing'),('noprocess','NoProcess'),('pi_done','PI-Done'),('done','Done')], 'Status'),
	'note': fields.text('Remarks'),
	'name': fields.char('Name', size=128),
	'state':fields.related('indent_id','state',type='selection',string="State",store=True),
	'dep_id': fields.many2one('kg.depmaster','Department Name'),
	'pi_cancel': fields.boolean('Cancel'),
	'required_date': fields.date('Required Date'),
	'brand_id': fields.many2one('kg.brand.master', 'Brand Name'),
	'return_qty':fields.float('Return Qty'),
	}
	
	_defaults = {
	
	'line_state' : 'noprocess',
	'name': 'Dep.Indent.Line',
	'line_date' : fields.date.context_today,
	
	}
		
	
kg_depindent_line()	
