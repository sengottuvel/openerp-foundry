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
		
		## Basic Info
		
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode',required=True,readonly=True),
		'remark': fields.text('Approve/Reject Remarks',readonly=False,states={'cancel':[('readonly',True)]}),
		'state': fields.selection([('draft','Draft'),('in_progress','WFA'),('cancel','Cancelled'),('done','Purchase Done'),('approved','Approved'),('reject','Rejected')],
						'Status', track_visibility='onchange', required=True, readonly=True, states={'draft': [('readonly', False)],'in_progress':[('readonly',False)]}),
		'note': fields.text('Notes'),
		
		## Module Requirement Info
				
		'kg_store': fields.selection([('sub','Sub Store'), ('main','Main Store')], 'Store', readonly=True, states={'draft': [('readonly', False)],'in_progress':[('readonly',False)]}),
		'dep_name' : fields.many2one('kg.depmaster', 'Dep.Name', readonly=True, states={'draft': [('readonly', False)],'in_progress':[('readonly',False)]}),
		'date_start': fields.date('Indent Date', readonly=True, states={'draft': [('readonly', False)],'in_progress':[('readonly',False)]}),
		'pi_type': fields.selection([('direct','Direct'),('fromdep','From Dep Indent')], 'Type'),
		'pi_flag': fields.boolean('pi flag'),
		#~ 'division':fields.many2one('kg.division.master','Division',readonly=True,states={'draft': [('readonly', False)],'in_progress':[('readonly',False)]}),
		#~ 'expected_date':fields.date('Expected Date',required=True,readonly=True,states={'draft': [('readonly', False)],'in_progress':[('readonly',False)]}),
		'indent_type': fields.selection([('fromdi','From Dept'),('direct','Direct')],'Indent Type',required=True,readonly=True,states={'draft': [('readonly', False)],'in_progress':[('readonly',False)]}),
		'division': fields.selection([('ppd','PPD'),('ipd','IPD'),('foundry','Foundry')],'Division',readonly=True,states={'draft': [('readonly', False)],'in_progress':[('readonly',False)]}),
		'due_date': fields.date('Due Date', readonly=True, states={'draft': [('readonly', False)],'in_progress':[('readonly',False)]}),
		
		# Entry Info
		
		'active': fields.boolean('Active'),
		'created_by' : fields.many2one('res.users', 'Created By', readonly=True,select=True),
		'creation_date':fields.datetime('Created Date',readonly=True),
		'confirmed_by' : fields.many2one('res.users', 'Confirmed By', readonly=True,select=True),
		'confirmed_date': fields.datetime('Confirmed Date',readonly=True),
		'approved_by' : fields.many2one('res.users', 'Approved By', readonly=True,select=True),
		'approved_date' : fields.datetime('Apporved Date',readonly=True),
		'update_date' : fields.datetime('Last Updated Date',readonly=True),
		'update_user_id' : fields.many2one('res.users','Last Updated By',readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'reject_date': fields.datetime('Rejected Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		
		}
	
	_defaults = {
		
		'exclusive': 'exclusive',
		'kg_store': 'main',
		'name': '',
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'created_by': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id,
		'active': True,
		'entry_mode': 'manual',
		'indent_type': 'direct',
		
		}
	
	def onchange_entry_mode(self, cr, uid, ids, entry_mode, pi_flag, context=None):
		value = {'pi_flag': ''}
		if entry_mode == 'manual':
			value = {'pi_flag': True}
		else:
			value = {'pi_flag': False}
		return {'value': value}
		
	def onchange_indent_type(self, cr, uid, ids, indent_type, pi_flag,line_ids, context=None):
		fou_vals = []
		if line_ids:
			for ids_a in line_ids:
				cr.execute(''' delete from purchase_requisition_line where id = %s '''%(ids_a[1]))
		if indent_type == 'direct':
			result = True
		else:
			result = False
		return {'value': {'line_ids': fou_vals,'pi_flag':result}}
	
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
		if obj.state == 'draft':
			seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','purchase.order.requisition')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,obj.date_start))
			seq_name = cr.fetchone();
			self.write(cr,uid,ids,{'name':seq_name[0]})
			self.write(cr,uid,ids,{'state':'in_progress','confirmed_by':uid,'confirmed_date':time.strftime("%Y-%m-%d")})
		
		return True
		   
	def tender_for_approve(self, cr, uid, ids, context=None):
		obj = self.browse(cr,uid,ids[0])
		if obj.state == 'in_progress':
			product_obj = self.pool.get('product.product')
			pi_line_obj = self.pool.get('purchase.requisition.line')
			for t in self.browse(cr,uid,ids):
				indent_line_obj = self.pool.get('kg.depindent.line')
				if not t.line_ids:
					raise osv.except_osv(_('Empty Purchase Indent'),
						_('You can not confirm an empty Purchase Indent'))
				for line in t.line_ids:
					pi_line_obj.write(cr,uid,line.id, {'line_state' : 'process'})
					if line.product_qty==0:
						raise osv.except_osv(_('Error'),
							_('Purchase Indent quantity can not be zero'))
					else:
						print "Line have enough Qty"
						
				self.write(cr,uid,ids,{'state':'approved','approved_by':uid,'approved_date':time.strftime('%Y-%m-%d %H:%M:%S')})
				cr.execute(""" select depindent_line_id from kg_depindent_pi_line where pi_id = %s """ %(str(ids[0])))
				data = cr.dictfetchall()
				val = [d['depindent_line_id'] for d in data if 'depindent_line_id' in d] # Get a values form list of dict if the dict have with empty values
				pi_lines = obj.line_ids
				for i in range(len(pi_lines)):
					product_id = pi_lines[i].product_id.id
					product_record = product_obj.browse(cr, uid, product_id)
					product = pi_lines[i].product_id.name
					pi_used_qty = pi_lines[i].product_qty
						
					if pi_lines[i].line_ids:
						total = sum(wo.qty for wo in pi_lines[i].line_ids)
						if total <= pi_used_qty:
							pass
						else:
							raise osv.except_osv(_('Warning!'),
								_('Please Check WO Qty'))
					if pi_lines[i].depindent_line_id and pi_lines[i].group_flag == False:
						depindent_line_id=pi_lines[i].depindent_line_id
						orig_depindent_qty = pi_lines[i].dep_indent_qty
						
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
									sql = """ update kg_depindent_line set po_qty=%s, pending_qty=%s where id = %s """%(pending_po_depindent_qty,
													pending_stock_depindent_qty,pi_lines[i].depindent_line_id.id)
									cr.execute(sql)
									if pending_po_depindent_qty == 0:
										indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'process'})
									elif pending_po_depindent_qty > 0:
										indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'noprocess'})
								else:
									sql = """ update kg_depindent_line set po_qty=%s, pending_qty=%s where id = %s """%(pending_po_depindent_qty,
														pending_stock_depindent_qty,pi_lines[i].depindent_line_id.id)
									cr.execute(sql)
									if pending_po_depindent_qty == 0:
										indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'process'})
									elif pending_po_depindent_qty > 0:
										indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'noprocess'})
						else:
							if pi_used_qty > po_uom_qty:
								pending_stock_depindent_qty = 0.0
								pending_po_depindent_qty = 0.0
								sql1 = """ update kg_depindent_line set po_qty=%s, pending_qty=%s where id = %s """%(pending_po_depindent_qty,
											pending_stock_depindent_qty,pi_lines[i].depindent_line_id.id)
								cr.execute(sql1)
								if pending_po_depindent_qty == 0:
									indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'process'})
								elif pending_po_depindent_qty > 0:
									indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'noprocess'})
							else:
								pending_stock_depindent_qty = orig_depindent_qty - pi_used_qty
								pending_po_depindent_qty = po_uom_qty - pi_used_qty
								sql1 = """ update kg_depindent_line set po_qty=%s, pending_qty=%s where id = %s """%(pending_po_depindent_qty,
											pending_stock_depindent_qty,pi_lines[i].depindent_line_id.id)
								cr.execute(sql1)
								if pending_po_depindent_qty == 0:
									indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'process'})
								elif pending_po_depindent_qty > 0:
									indent_line_obj.write(cr,uid,depindent_line_id.id, {'line_state' : 'noprocess'})
					else:
						if not pi_lines[i].depindent_line_id:
							pass
						if pi_lines[i].group_flag == True:
							self.update_product_group(cr,uid,ids,line=pi_lines[i])
						else:
							print "All are correct Values"
		return True
		
	def write(self, cr, uid, ids, vals, context=None):		
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_purchase_indent, self).write(cr, uid, ids, vals, context)
		
	def tender_cancel(self, cr, uid, ids, context=None):
		piindent = self.browse(cr, uid, ids[0], context=context)
		if piindent.state == 'approved':
			purchase_order_obj = self.pool.get('purchase.order')
			pi_line_obj = self.pool.get('purchase.requisition.line')
			if not piindent.remark:
				raise osv.except_osv(_('Remarks Needed !!'),
					_('Enter Remark in Remarks Tab....'))
					
			if piindent.indent_type == 'di':
				if piindent.state == 'approved':					
					for line in piindent.line_ids:
						pi_line_obj.write(cr,uid,line.id, {'line_state' : 'noprocess'})
						if line.product_qty != line.pending_qty:
							raise osv.except_osv(_('Unable to cancel this Purchase Indent.'),
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
			else:
				pass
			return self.write(cr, uid, ids, {'state': 'cancel','cancel_date':time.strftime('%Y-%m-%d %H:%M:%S'),'cancel_user_id':uid})
		
	def tender_reject(self, cr, uid, ids, context=None):
		piindent = self.browse(cr, uid, ids[0], context=context)
		if piindent.state == 'in_progress':
			purchase_order_obj = self.pool.get('purchase.order')
			pi_line_obj = self.pool.get('purchase.requisition.line')
			if not piindent.remark:
				raise osv.except_osv(_('Remarks Needed !!'),
					_('Enter Remark in Remarks Tab....'))
				
			if piindent.indent_type == 'di':
				for line in piindent.line_ids:
					line.depindent_line_id.write({'line_state' : 'noprocess'})			
			else:
				pass
		return self.write(cr, uid, ids, {'state': 'reject','reject_date':time.strftime('%Y-%m-%d %H:%M:%S'),'rej_user_id':uid})
	
	def _check_line(self, cr, uid, ids, context=None):
		tot = 0.0
		for pi in self.browse(cr,uid,ids):
			if pi.entry_mode == 'manual':
				if not pi.kg_depindent_lines:
					if not pi.line_ids:
						raise osv.except_osv(_('Warning!'),
							_('You can not save this Purchase Indent with out Item Details!'))
					for line in pi.line_ids:
						tot += line.product_qty
					if tot <= 0.0:
						raise osv.except_osv(_('Warning!'),
							_('You can not save this Purchase Indent with Zero Qty!'))
				elif pi.kg_depindent_lines and pi.state != 'draft':
					if not pi.line_ids:
						raise osv.except_osv(_('Warning!'),
							_('You can not save this Purchase Indent with out Item Details!'))
					for line in pi.line_ids:
						tot += line.product_qty
					if tot <= 0.0:			
						raise osv.except_osv(_('Warning!'),
							_('You can not save this Purchase Indent with Zero Qty!'))
			return True
			
	_constraints = [
		
		(_check_line,'You can not save this Purchase Indent with out Line and Zero Qty !',['']),
	]   	   	
	
kg_purchase_indent()

class kg_purchase_indent_line(osv.osv):
	
	_name = "purchase.requisition.line"
	_inherit = "purchase.requisition.line"
	_rec_name = 'name'
	
	_columns = {
	
	'rate': fields.float('Last Purchase Rate',readonly=True, state={'draft': [('readonly', False)]}),
	'line_state': fields.selection([('process', 'Approved'),('noprocess', 'Confirmed'),
					('cancel', 'Cancel')], 'Status'),
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
	'draft_flag':fields.boolean('Draft Flag'),
	'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode'),
	'po_flag':fields.boolean('PO Flag'),
	'src_type': fields.selection([('direct', 'Direct'),('frompi', 'From PI'),('fromquote', 'From Quotation')], 'Soruce Type'),
	
	}
	
	_defaults = {
	
	'line_state' : 'noprocess',
	'name': 'PILINE',
	'draft_flag': False,
	'src_type': 'frompi',
	
	}
	
	def onchange_product_id(self, cr, uid, ids, product_id, product_uom_id, context=None):
		value = {'product_uom_id': '','stock_qty':'','brand_id':'','moc_id_temp':'','moc_id':''}
		uom = brand = moc_id_temp = moc_id = ''
		stock_qty = 0.00
		if product_id:
			prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			uom = prod.uom_po_id.id
		else:
			uom = ''	
		stock_sql = """ select sum(pending_qty) from stock_production_lot where product_id = %s group by product_id """%(product_id)
		cr.execute(stock_sql)		
		stock_data = cr.dictfetchall()
		if stock_data:
			stock_qty = stock_data[0]
			stock_qty = stock_qty.values()[0]
		else:
			stock_qty = 0.00
		value = {'product_uom_id': uom,'stock_qty': stock_qty,'brand_id':brand,'moc_id_temp':moc_id_temp,'moc_id':moc_id}	
		return {'value': value}
			
	def onchange_qty(self, cr, uid, ids, product_qty, pending_qty, context=None):
		value = {'pending_qty': ''}
		if product_qty:
			value = {'pending_qty': product_qty}
		return {'value': value}
	
	def unlink(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		for rec in self.browse(cr, uid, ids, context=context):
			parent_rec = rec.requisition_id
			if parent_rec.state not in ['draft','in_progress']:
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
		if not line.cancel_remark:
			raise osv.except_osv(_('Remarks is must !!'), _('Enter cancel remarks !!!'))
		else:							
			line.write({'line_state' : 'cancel'})
			line.depindent_line_id.write({'pi_cancel' : True})
		return True

kg_purchase_indent_line()
