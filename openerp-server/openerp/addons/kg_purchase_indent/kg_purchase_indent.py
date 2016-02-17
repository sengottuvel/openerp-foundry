## KG Purchase Indent Module ##

import math
import re
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import datetime
from itertools import groupby
import openerp.addons.decimal_precision as dp
import logging
logger = logging.getLogger('server')

class kg_purchase_indent(osv.osv):
	
	_name = "purchase.requisition"
	_inherit = "purchase.requisition"
	_order = "date_start desc"	
	
	_columns = {
	
		'name': fields.char('Indent No', size=64, readonly=True, states={'draft': [('readonly', False)],'in_progress':[('readonly',False)]}),
		'kg_store': fields.selection([('sub','Sub Store'), ('main','Main Store')], 'Store', readonly=True, states={'draft': [('readonly', False)],'in_progress':[('readonly',False)]}),
		'dep_name' : fields.many2one('kg.depmaster', 'Dep.Name', readonly=True, states={'draft': [('readonly', False)],'in_progress':[('readonly',False)]}),
		'state': fields.selection([('draft','Waiting for Confirmation'),('in_progress','Waiting for Approval'),('cancel','Cancelled'),('done','Purchase Done'),('approved','Approved')],
			'Status', track_visibility='onchange', required=True, readonly=True, states={'draft': [('readonly', False)],'in_progress':[('readonly',False)]}),
		'date_start':fields.date('Indent Date', readonly=True, states={'draft': [('readonly', False)],'in_progress':[('readonly',False)]}),
		'line_ids' : fields.one2many('purchase.requisition.line','requisition_id','Products to Purchase', readonly=True, states={'draft': [('readonly', False)],'in_progress':[('readonly',False)]}),
		'pi_type': fields.selection([('direct','Direct'),('fromdep','From Dep Indent')], 'Type'),
		'pi_flag': fields.boolean('pi flag'),
		'kg_seq_id':fields.many2one('ir.sequence','Document Type',domain=[('code','=','kg.purchase.indent')],
			readonly=True, states={'draft': [('readonly', False)],'in_progress':[('readonly',False)]}),			
		'remark': fields.text('Remarks',readonly=False,states={'cancel':[('readonly',True)]}),
		'dep_project':fields.many2one('kg.project.master','Dept/Project Name',readonly=True,states={'draft': [('readonly', False)],'in_progress':[('readonly',False)]}),
		'approved_date' : fields.date('Indent Date'),
		'creation_date':fields.datetime('Creation Date'),
		'confirmed_by' : fields.many2one('res.users', 'Confirmed By', readonly=False,select=True),
		'approved_by' : fields.many2one('res.users', 'Approved By', readonly=False,select=True),

	}
	
	_defaults = {
		'exclusive': 'exclusive',
		'kg_store': 'main',
		'name':'',
		'creation_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
	}
	
	_sql_constraints = [
	
		('name_uniq', 'unique(name, company_id)', 'Indent Reference must be unique per Company!'),
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
			if mail_form_rec.doc_name.model == 'kg.purchase.indent':
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
	
	"""def onchange_seq_id(self, cr, uid, ids, kg_seq_id,name):
		print "kgggggggggggggggggg --  onchange_seq_id called"		
		value = {'name':''}
		if kg_seq_id:
			next_seq_num = self.pool.get('ir.sequence').kg_get_id(cr, uid, kg_seq_id,'id',{'noupdate':False})
			print "next_seq_num:::::::::::", next_seq_num
			value = {'name': next_seq_num}
		return {'value': value}"""

	"""
	def create(self, cr, uid, vals, context=None):
		print "callled create from KG"
		if vals.get('name','/')=='/':
			vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'purchase.requisition') or '/'
		order =  super(kg_purchase_indent, self).create(cr, uid, vals, context=context)
		return order
	"""
		
	def unlink(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		pi_indent = self.read(cr, uid, ids, ['state'], context=context)
		unlink_ids = []
		for t in pi_indent:
			if t['state'] in ('draft'):
				unlink_ids.append(t['id'])
			else:
				raise osv.except_osv(_('Invalid action !'), _('System not allow to delete a UN-DRAFT state Purchase Indent!!'))
		pi_indent_lines_to_del = self.pool.get('purchase.requisition.line').search(cr, uid, [('requisition_id','in',unlink_ids)])
		self.pool.get('purchase.requisition.line').unlink(cr, uid, pi_indent_lines_to_del)
		osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		return True
		
	def tender_in_progress(self, cr, uid, ids, context=None):
		
		obj = self.browse(cr,uid,ids[0])
		if obj.name == '':
			indent_no = self.pool.get('ir.sequence').get(cr, uid, 'purchase.requisition')
			self.write(cr,uid,ids,{'name':indent_no})
			
		self.write(cr,uid,ids,{'state':'in_progress','confirmed_by':uid})
#		cr.execute("""select all_transaction_mails('Purchase Indent Request Approval',%s)"""%(ids[0]))
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
					subject = "Purchase Indent Request - Waiting For Approval",
					body = data[0][0],
					email_cc = vals['email_cc'],
					object_id = ids[0] and ('%s-%s' % (ids[0], 'purchase.requisition')),
					subtype = 'html',
					subtype_alternative = 'plain')
			res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
		"""
		return True
		   
	def tender_for_approve(self, cr, uid, ids,kg_seq_id, context=None):
		print "callled tender_for_approve from KG"
		product_obj = self.pool.get('product.product')
		pi_line_obj = self.pool.get('purchase.requisition.line')
		obj = self.browse(cr,uid,ids[0])
		"""Raj
		if obj.confirmed_by.id == uid:
			raise osv.except_osv(
					_('Warning'),
					_('Approve cannot be done by Confirmed user'))
		else:
		"""
		for t in self.browse(cr,uid,ids):
			indent_line_obj = self.pool.get('kg.depindent.line')
			if not t.line_ids:
				raise osv.except_osv(
						_('Empty Purchase Indent'),
						_('You can not confirm an empty Purchase Indent'))
			for line in t.line_ids:
				pi_line_obj.write(cr,uid,line.id, {'line_state' : 'process'})
				if line.product_qty==0:
					raise osv.except_osv(
						_('Error'),
						_('Purchase Indent quantity can not be zero'))
				else:
					print "Line have enough Qty"
					
			self.write(cr,uid,ids,{'state':'approved','approved_by':uid,'approved_date':time.strftime("%Y-%m-%d")})
			cr.execute(""" select depindent_line_id from kg_depindent_pi_line where pi_id = %s """ %(str(ids[0])))
			data = cr.dictfetchall()
			val = [d['depindent_line_id'] for d in data if 'depindent_line_id' in d] # Get a values form list of dict if the dict have with empty values
			pi_lines = obj.line_ids
			for i in range(len(pi_lines)):
				product_id = pi_lines[i].product_id.id
				product_record = product_obj.browse(cr, uid, product_id)
				product = pi_lines[i].product_id.name
				if pi_lines[i].depindent_line_id and pi_lines[i].group_flag == False:
					depindent_line_id=pi_lines[i].depindent_line_id
					orig_depindent_qty = pi_lines[i].dep_indent_qty
					pi_used_qty = pi_lines[i].product_qty
					po_uom_qty = pi_lines[i].po_uom_qty
					pending_stock_depindent_qty = pi_lines[i].dep_indent_qty -  pi_lines[i].po_uom_qty
					pending_po_depindent_qty = pi_lines[i].po_uom_qty - pi_lines[i].po_uom_qty
					tmp_qty = pi_used_qty * product_record.po_uom_coeff
					if pi_lines[i].product_uom_id.id != pi_lines[i].default_uom_id.id:
						if tmp_qty > orig_depindent_qty or pi_used_qty > po_uom_qty :
							pending_stock_depindent_qty = 0.0
							pending_po_depindent_qty = po_uom_qty - pi_used_qty
							sql = """ update kg_depindent_line set po_qty=%s, pending_qty=%s where id = %s"""%(pending_po_depindent_qty,
										pending_stock_depindent_qty,pi_lines[i].depindent_line_id.id)
							cr.execute(sql)
							#indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'noprocess'})
							if pending_po_depindent_qty == 0:
								indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'process'})
							elif pending_po_depindent_qty > 0:
								indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'noprocess'})
						else:
							pending_stock_depindent_qty = orig_depindent_qty - tmp_qty
							pending_po_depindent_qty = po_uom_qty - pi_used_qty
							if pi_used_qty > po_uom_qty:
								pending_stock_depindent_qty = 0.0
								pending_po_depindent_qty = 0.0
								print "depindent_line_id.id*****222222222222222222222**************", depindent_line_id.id, "pending_po_depindent_qty ======>", pending_po_depindent_qty
								sql = """ update kg_depindent_line set po_qty=%s, pending_qty=%s where id = %s """%(pending_po_depindent_qty,
												pending_stock_depindent_qty,pi_lines[i].depindent_line_id.id)
								cr.execute(sql)
								#indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'noprocess'})
								if pending_po_depindent_qty == 0:
									print "pi_lines[i].pending_qty...............",pi_lines[i].pending_qty
									indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'process'})
								elif pending_po_depindent_qty > 0:
									print "pi_lines[i].pending_qty...............",pi_lines[i].pending_qty
									indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'noprocess'})
							else:
								print "depindent_line_id.id**********3333333333333333333333333333*********", depindent_line_id.id, "pending_po_depindent_qty ======>", pending_po_depindent_qty
								sql = """ update kg_depindent_line set po_qty=%s, pending_qty=%s where id = %s """%(pending_po_depindent_qty,
													pending_stock_depindent_qty,pi_lines[i].depindent_line_id.id)
								cr.execute(sql)
								#indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'noprocess'})
								if pending_po_depindent_qty == 0:
									print "pi_lines[i].pending_qty...............",pi_lines[i].pending_qty
									indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'process'})
								elif pending_po_depindent_qty > 0:
									print "pi_lines[i].pending_qty...............",pi_lines[i].pending_qty
									indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'noprocess'})
					else:
						
						
						if pi_used_qty > po_uom_qty:
							pending_stock_depindent_qty = 0.0
							pending_po_depindent_qty = 0.0
							print "depindent_line_id.id*******44444444444444444444444444************", depindent_line_id.id, "pending_po_depindent_qty ======>", pending_po_depindent_qty
							sql1 = """ update kg_depindent_line set po_qty=%s, pending_qty=%s where id = %s """%(pending_po_depindent_qty,
										pending_stock_depindent_qty,pi_lines[i].depindent_line_id.id)
							cr.execute(sql1)
							#indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'noprocess'})
							if pending_po_depindent_qty == 0:
								print "pi_lines[i].pending_qty.....if..........",pi_lines[i].pending_qty
								indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'process'})
							elif pending_po_depindent_qty > 0:
								print "pi_lines[i].pending_qty.......else........",pi_lines[i].pending_qty
								indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'noprocess'})
						else:
							pending_stock_depindent_qty = orig_depindent_qty - pi_used_qty
							pending_po_depindent_qty = po_uom_qty - pi_used_qty
							print "depindent_line_id.id********555555555555555555555555***********", depindent_line_id.id , "pending_po_depindent_qty ======>", pending_po_depindent_qty
							sql1 = """ update kg_depindent_line set po_qty=%s, pending_qty=%s where id = %s """%(pending_po_depindent_qty,
										pending_stock_depindent_qty,pi_lines[i].depindent_line_id.id)
							cr.execute(sql1)
							#indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'noprocess'})
							if pending_po_depindent_qty == 0:
								print "pi_lines[i].pending_qty........if.......",pi_lines[i].pending_qty
								indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'process'})
							elif pending_po_depindent_qty > 0:
								print "pi_lines[i].pending_qty.......else........",pi_lines[i].pending_qty
								indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'noprocess'})
								
				else:
					if not pi_lines[i].depindent_line_id:
						raise osv.except_osv(
							_('Direct Purchase Indent System Not Allow'),
							_('System not allow to raise Purchase Indent with out Dep.Indent Line for %s' %(product)))
					if pi_lines[i].group_flag == True:
						self.update_product_group(cr,uid,ids,line=pi_lines[i])
					else:
						print "All are correct Values"
			#cr.execute("""select all_transaction_mails('Purchase Indent Request Approval',%s)"""%(ids[0]))
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
						subject = "Purchase Indent Request - Approved",
						body = data[0][0],
						email_cc = vals['email_cc'],
						object_id = ids[0] and ('%s-%s' % (ids[0], 'purchase.requisition')),
						subtype = 'html',
						subtype_alternative = 'plain')
				res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
			return True
			cr.close()
			"""
	def tender_cancel(self, cr, uid, ids, context=None):
		print "callled tender_cancel from KG"
		purchase_order_obj = self.pool.get('purchase.order')
		pi_line_obj = self.pool.get('purchase.requisition.line')
		piindent = self.browse(cr, uid, ids[0], context=context)
	
		if piindent.state == 'approved':					
			for line in piindent.line_ids:
				pi_line_obj.write(cr,uid,line.id, {'line_state' : 'noprocess'})
				if line.product_qty != line.pending_qty:
					raise osv.except_osv(
						_('Unable to cancel this Purchase Indent.'),
						_('First cancel all PO related to this Purchase Indent.'))
				else:
					if line.depindent_line_id and line.group_flag == False:
						orig_pending_qty = line.depindent_line_id.pending_qty
						pi_qty = line.product_qty
						orig_pending_qty += pi_qty
						line.depindent_line_id.write({'pending_qty':orig_pending_qty })
						line.depindent_line_id.write({'line_state':'noprocess' })
					else:
						pass
						# Need to do cancel process if a PI line is product Grouping
		else:			
			for line in piindent.line_ids:
				line.depindent_line_id.write({'line_state' : 'noprocess'})			
		
		return self.write(cr, uid, ids, {'state': 'cancel'})
		
		
	def pi_approval(self, cr, uid, ids, context=None):
		
		self.write(cr, uid, ids, {'state': 'approved'})
		return True	
			

	def _check_line(self, cr, uid, ids, context=None):
		logger.info('[KG ERP] Class: kg_purchase_indent, Method: _check_line called...')
		for pi in self.browse(cr,uid,ids):
			print "pi.kg_depindent_lines...........", pi.kg_depindent_lines
			if pi.kg_depindent_lines==[]:
				tot = 0.0
				for line in pi.line_ids:
					tot += line.product_qty
					print "tot ===============================>>>>", tot
				if tot <= 0.0:			
					return False
			
			return True
			
	_constraints = [
	
		(_check_line,'You can not save this Purchase Indent with out Line and Zero Qty !',['line_ids']),
	]   	   	
		
kg_purchase_indent()

class kg_purchase_indent_line(osv.osv):
	
	_name = "purchase.requisition.line"
	_inherit = "purchase.requisition.line"
	_rec_name = 'name'
	
	_columns = {
	
	'rate': fields.float('Last Purchase Rate',readonly=True, state={'draft': [('readonly', False)]}),
	'note': fields.text('Remarks'),
	'line_date':fields.datetime('Date'),
	'line_state': fields.selection([('process', 'Approved'),('noprocess', 'Confirmed'),
					('cancel', 'Cancel')], 'Status'),
	'pending_qty': fields.float('Pending Qty'),
	'current_qty':fields.float('Current Stock Quantity'),
	'dep_indent_qty': fields.float('Dep.Indent Qty'),
	'name': fields.char('Name', size=64),
	'depindent_line_id':fields.many2one('kg.depindent.line', 'Dep.Indent Line'),
	'default_uom_id': fields.many2one('product.uom', 'PO UOM'),
	'po_uom_qty': fields.float('PO.Qty'),
	'group_flag':fields.boolean('Group By'),
	'dep_id':fields.many2one('kg.depmaster', 'Department'),
	'user_id': fields.many2one('res.users', 'Users'),
	'cancel_remark': fields.text('Cancel Remarks'),
	'brand_id': fields.many2one('kg.brand.master', 'Brand Name'),
	'draft_flag':fields.boolean('Draft Flag'),
	}
	
	_defaults = {
	
	'line_state' : 'noprocess',
	'name': 'PILINE',
	'line_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
	'draft_flag': False,
	
	}		
	
	def onchange_product_id(self, cr, uid, ids, product_id, product_uom_id, context=None):
		print "callled onchange_product_id from KG"

		value = {'product_uom_id': ''}
		if product_id:
			prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			value = {'product_uom_id': prod.uom_po_id.id}
		return {'value': value}
			
	def onchange_qty(self, cr, uid, ids, product_qty, pending_qty, context=None):
		print "callled onchange_qty from KG"

		value = {'pending_qty': ''}
		if product_qty:
			value = {'pending_qty': product_qty}
		return {'value': value}
		
	def create(self,cr,uid,vals,context={}):
		print "Line create called............"
		if vals['product_id']:
			prod_record = self.pool.get('product.product').browse(cr,uid,vals['product_id'])
			vals.update({'product_uom_id':prod_record.uom_po_id.id})	  
		return super(kg_purchase_indent_line,self).create(cr,uid,vals,context)
		
	def write(self,cr,uid,ids,vals,context={}):
		if vals.has_key('product_id') and vals['product_id']:
			product_record = self.pool.get('product.product').browse(cr,uid,vals['product_id'])
			if product_record.uom_po_id:
					vals.update({'product_uom_id':prod_record.uom_po_id.id})
		return super(kg_purchase_indent_line,self).write(cr,uid,ids,vals,context)		

	def unlink(self, cr, uid, ids, context=None):
		print "kgggggggggggggg line unlike called ids ===", ids
		if context is None:
			context = {}
		for rec in self.browse(cr, uid, ids, context=context):
			print "rec ===================>>>>>", rec, "ids====>", context
			parent_rec = rec.requisition_id
			print "parent_rec.state", parent_rec.state
			if parent_rec.state not in ['draft','in_progress']:
				print "iffffffffffff"
				raise osv.except_osv(_('Invalid Action!'), _('Cannot delete a purchase indent line which is in state \'%s\'.') %(parent_rec.state,))
			else:
				pi_id = parent_rec.id
				dep_line_rec = rec.depindent_line_id				
				dep_line_id = rec.depindent_line_id.id
				dep_line_rec.write({'line_state' : 'noprocess'})
				del_sql = """ delete from kg_depindent_pi_line where pi_id=%s and depindent_line_id=%s """ %(pi_id,dep_line_id)
				cr.execute(del_sql)				
				return super(kg_purchase_indent_line, self).unlink(cr, uid, ids, context=context)
				
	def line_cancel(self, cr, uid, ids, context=None):
		line = self.browse(cr, uid, ids[0])
		print "line........................", line
		if not line.cancel_remark:
			raise osv.except_osv(_('Remarks is must !!'), _('Enter cancel remarks !!!'))
		else:							
			print "depindent_line_id//////////////////"	, line.depindent_line_id
			line.write({'line_state' : 'cancel'})
			line.depindent_line_id.write({'pi_cancel' : True})
		return True

kg_purchase_indent_line()
