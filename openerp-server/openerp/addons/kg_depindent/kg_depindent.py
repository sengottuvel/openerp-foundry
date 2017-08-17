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
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_depindent(osv.osv):
	
	_name = "kg.depindent"
	_description = "Department Indent"
	_rec_name = "name"
	_order = "name desc"
	
	_columns = {
		
		## Basic Info
		
		'name': fields.char('No', size=64, readonly=True,select=True),
		'ind_date': fields.date('Indent Date',readonly=True,states={'draft':[('readonly',False)]}),
		'state': fields.selection([('draft', 'Draft'),('confirm','Waiting For Approval'),('approved','Approved'),('rejected','Rejected'),('cancel','Cancelled')], 'Status', track_visibility='onchange', required=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode',required=True,readonly=True),
		'remarks': fields.text('Reject Remarks',readonly=True,states={'confirm':[('readonly',False)]}),
		'cancel_remark': fields.text('Cancel Remarks',readonly=True,states={'approved':[('readonly',False)]}),
		
		## Module Requirement Info
		
		'dep_name': fields.many2one('kg.depmaster','Department', required=True,translate=True, select=True,readonly=True,
					domain="[('item_request','=',True),('state','in',('draft','confirmed','approved'))]", states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'type': fields.selection([('direct','Direct'), ('from_bom','From BoM')], 'Indent Type',readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'src_location_id': fields.many2one('stock.location', 'MainStock Location'),
		'dest_location_id': fields.many2one('stock.location', 'DepStock Location'),
		'main_store': fields.boolean('For Main Store',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'division':fields.many2one('kg.division.master','Division',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'indent_type': fields.selection([('production','For Production'),('own_use','For Own Use')],'Indent Type',required=True,readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		'order_id': fields.many2one('kg.work.order','Work Order'),
		'order_line_id': fields.many2one('ch.work.order.details','WO No.',readonly=True,states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		
		## Child Tables Declaration
		
		'dep_indent_line': fields.one2many('kg.depindent.line', 'indent_id', 'Indent Lines', readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
		
		### Entry Info
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True,select=True),
		'date': fields.datetime('Created Date',readonly=True),
		'confirmed_by': fields.many2one('res.users', 'Confirmed By', readonly=True,select=True),
		'confirmed_date': fields.datetime('Confirmed Date',readonly=True),
		'reject_date': fields.datetime('Rejected Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'approved_by': fields.many2one('res.users', 'Approved By', readonly=True,select=True),
		'approved_date': fields.datetime('Approved Date',readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date',readonly=True),
		'update_user_id': fields.many2one('res.users','Last Updated By',readonly=True),
		
	}
	
	#_sql_constraints = [('code_uniq','unique(name)', 'Indent number must be unique!')]
	
	_defaults = {
		
		'type': 'direct',
		'state': 'draft',
		'active': True,
		'date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'user_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
		'ind_date': lambda * a: time.strftime('%Y-%m-%d'),
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.depindent', context=c),
		'entry_mode': 'manual',
		
			}
	
	def _check_lineitem(self, cr, uid, ids, context=None):
		indent = self.browse(cr,uid,ids[0])
		if not indent.dep_indent_line:
			return False
		else:
			for line in indent.dep_indent_line:
				if line.qty == 0:
					return False										
		return True
	 
	def _check_lineuom(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.dep_indent_line:
			for line in rec.dep_indent_line:		
				if line.uom.id == line.product_id.uom_id.id or line.uom.id == line.product_id.uom_po_id.id:
					pass
				else:
					raise osv.except_osv(_('UOM Mismatching Error !'),
						_('You choosed wrong UOM and you can choose either %s or %s for %s !!!') % (line.product_id.uom_id.name,line.product_id.uom_po_id.name,line.product_id.name))
		return True
	
	_constraints = [
		#(_check_lineitem, 'Department Indent Line and Qty Can Not Be Empty !!',['qty']),
		(_check_lineuom, '',[]),
		]
	
	def confirm_indent(self, cr, uid, ids,context=None):
		indent_obj = self.browse(cr, uid,ids[0])
		if indent_obj.state == 'draft':
			product_obj = self.pool.get('product.product')
			total = 0
			indent_lines = indent_obj.dep_indent_line
			for i in range(len(indent_lines)):
				indent_qty=indent_lines[i].qty
				if indent_lines[i].line_id:
					total = sum(wo.qty for wo in indent_lines[i].line_id)
					if total <= indent_qty:
						pass
					else:
						raise osv.except_osv(_('Warning!'),
							_('Please Check WO Qty'))
					wo_sql = """ select count(wo_id) as wo_tot,wo_id as wo_name from ch_depindent_wo where header_id = %s group by wo_id"""%(indent_lines[i].id)
					cr.execute(wo_sql)		
					wo_data = cr.dictfetchall()
					for wo in wo_data:
						if wo['wo_tot'] > 1:
							raise osv.except_osv(_('Warning!'),
								_('%s This WO No. repeated'%(wo['wo_name'])))
						else:
							pass
			
			location = self.pool.get('kg.depmaster').browse(cr, uid, indent_obj.dep_name.id, context=context)
			self.write(cr,uid,ids,{'src_location_id' : location.main_location.id,'dest_location_id':location.stock_location.id})
			for t in self.browse(cr,uid,ids):
				if not t.dep_indent_line:
					raise osv.except_osv(_('Empty Department Indent'),
							_('You can not confirm an empty Department Indent'))
				depindent_line = t.dep_indent_line[0]
				depindent_line_id = depindent_line.id
				
				if t.dep_indent_line[0].qty==0:
					raise osv.except_osv(_('Error'),
							_('Department Indent quantity can not be zero'))
				for line in t.dep_indent_line:
					product_record = product_obj.browse(cr,uid,line.product_id.id)
					cr.execute("""update kg_depindent_line set uom = %s where id = %s"""%(line.product_id.uom_po_id.id,line.id))
					if line.uom.id != product_record.uom_po_id.id:
						new_po_qty = line.qty / product_record.po_uom_coeff
				seq_name = ''
				if not t.name:
					seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
					cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,indent_obj.ind_date))
					seq_name = cr.fetchone();
					seq_name = seq_name[0]
				else:
					seq_name = t.seq_name
				self.write(cr,uid,ids,{'state': 'confirm',
									   'confirmed_by': uid,
									   'confirmed_date': dt_time,
									   'name': seq_name
									   })
			
			return True
	
	def reject_indent(self, cr, uid, ids,context=None):
		rec = self.browse(cr, uid,ids[0])
		if rec.state == 'confirm':
			if rec.remarks:
				self.write(cr,uid,ids,{'state': 'rejected','rej_user_id': uid,'reject_date': dt_time})
			else:
				raise osv.except_osv(_('Rejection remark is must !!'),
					_('Enter rejection remark in remark field !!'))
	
	def set_to_draft(self, cr, uid, ids,context=None):
		rec = self.browse(cr, uid,ids[0])
		if rec.state == 'cancel':
			self.write(cr,uid,ids,{'state': 'draft'})
		return True
	
	def approve_indent(self, cr, uid, ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirm':
			total = 0
			indent_lines = rec.dep_indent_line
			for i in range(len(indent_lines)):
				indent_qty=indent_lines[i].qty
				if indent_lines[i].line_id:
					total = sum(wo.qty for wo in indent_lines[i].line_id)
					if total <= indent_qty:
						pass
					else:
						raise osv.except_osv(_('Warning!'),
							_('Please Check WO Qty'))
					wo_sql = """ select count(wo_id) as wo_tot,wo_id as wo_name from ch_depindent_wo where header_id = %s group by wo_id"""%(indent_lines[i].id)
					cr.execute(wo_sql)		
					wo_data = cr.dictfetchall()
					for wo in wo_data:
						if wo['wo_tot'] > 1:
							raise osv.except_osv(_('Warning!'),
							_('%s This WO No. repeated'%(wo['wo_name'])))
						else:
							pass
			for t in self.browse(cr,uid,ids):
				if not t.dep_indent_line:
					raise osv.except_osv(_('Empty Department Indent'),
							_('You can not approve an empty Department Indent'))
				depindent_line = t.dep_indent_line[0]
				depindent_line_id = depindent_line.id
				if t.dep_indent_line[0].qty==0:
					raise osv.except_osv(_('Error'),
							_('Department Indent quantity can not be zero'))
			if rec.dep_indent_line:
				for line in rec.dep_indent_line:
					indent_qty = line.qty
					if line.line_id:
						total = sum(wo.qty for wo in line.line_id)
						if total <= indent_qty:
							pass
						else:
							raise osv.except_osv(_('Warning!'),
								_('Please Check WO Qty'))
			self.write(cr,uid,ids,{'state':'approved','approved_by':uid,'approved_date':dt_time})
		
		return True
	
	def cancel_indent(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			pending_qty = 0
			for indent in self.browse(cr,uid,ids):
				if indent.dep_indent_line[0].qty != indent.dep_indent_line[0].pending_qty or indent.dep_indent_line[0].qty != indent.dep_indent_line[0].issue_pending_qty:
					raise osv.except_osv(_('Indent UnderProcessing'),
						_('You can not cancel this Indent because this indent is under processing !!!'))
				else:
					pass
			self.write(cr, uid,ids,{'state' : 'cancel','cancel_user_id': uid,'cancel_date': dt_time})
		return True
	
	def write(self, cr, uid, ids, vals, context=None):		
		vals.update({'update_date': dt_time,'update_user_id':uid})
		return super(kg_depindent, self).write(cr, uid, ids, vals, context)
	
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
		value = {'uom': '', 'po_uom': ''}
		if product_id:
			prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			value = {'uom': prod.uom_id.id, 'po_uom' : prod.uom_po_id.id,'uom_conversation_factor':prod.uom_conversation_factor}
		return {'value': value}
	
	def onchange_product_uom(self, cr, uid, ids, product_id, uom, po_uom,qty, context=None):
		value = {'qty': 0.0}
		if qty:		
			value = {'qty': 0.0}
		prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
		if uom == prod.uom_id.id or uom == prod.uom_po_id.id:
			pass
		else:
			if uom != prod.uom_po_id.id:				 			
				raise osv.except_osv(_('UOM Mismatching Error !'),
					_('You choosed wrong UOM and you can choose either %s or %s for %s !!!') % (prod.uom_id.name,prod.uom_po_id.name,prod.name))
		return {'value': value}
	
	def onchange_qty(self, cr, uid, ids, uom,product_id, qty, pending_qty, issue_pending_qty,po_qty, context=None):
		value = {'pending_qty': '', 'issue_pending_qty':'', 'po_qty':''}
		prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
		if product_id and qty:
			if uom != prod.uom_po_id.id:
				dep_po_qty_test = qty / prod.po_uom_coeff
				dep_po_qty = (math.ceil(dep_po_qty_test))
				value = {'pending_qty': qty, 'issue_pending_qty' : qty, 'po_qty' : dep_po_qty,'cutting_qty': qty}
			else:
				value = {'pending_qty': qty, 'issue_pending_qty' : qty, 'po_qty' : qty,'cutting_qty': qty}
		return {'value': value}
	
	def _get_product_available_func(states, what):
		def _product_available(self, cr, uid, ids, name, arg, context=None):
			return {}.fromkeys(ids, 0.0)
		return _product_available
	
	_stock_qty = _get_product_available_func(('done',), ('in', 'out'))
	
	_columns = {
		
		## Basic Info
		
		'indent_id': fields.many2one('kg.depindent', 'Indent No', required=True, ondelete='cascade'),
		
		## Module Requirement Fields
		
		'line_date': fields.date('Indent Date', required=True, readonly=True),
		'product_id': fields.many2one('product.product', 'Product', required=True,domain="[('state','not in',('reject','cancel')),('purchase_ok','=',True)]"),
		'uom': fields.many2one('product.uom', 'UOM', required=True),
		'po_uom': fields.many2one('product.uom', 'PO UOM'),
		'qty': fields.float('Indent Qty', required=True),
		'po_qty': fields.float('PO Qty',),
		'pending_qty': fields.float('Pending Qty'),
		'issue_pending_qty': fields.float('Issue.Pending Qty'),
		'cutting_qty': fields.float('Cutting Qty'),
		'main_store_qty': fields.function(_stock_qty, type='float', string='Quantity On Hand'),
		'line_state': fields.selection([('process','Processing'),('noprocess','NoProcess'),('pi_done','PI-Done'),('done','Done')], 'Status'),
		'note': fields.text('Remarks'),
		'name': fields.char('Name', size=128),
		'state':fields.related('indent_id','state',type='selection',string="State",store=True),
		'dep_id': fields.related('indent_id','dep_name',relation='kg.depmaster',type='many2one',string='Department Name',store=True),
		'dep_code': fields.related('dep_id','name',type='char',string='Department Code',store=True),
		'pi_cancel': fields.boolean('Cancel'),
		'required_date': fields.date('Required Date'),
		'brand_id': fields.many2one('kg.brand.master', 'Brand Name',domain="[('product_ids','in',(product_id)),('state','in',('draft','confirmed','approved'))]"),
		'return_qty':fields.float('Return Qty'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'moc_id_temp': fields.many2one('ch.brandmoc.rate.details','MOC',domain="[('brand_id','=',brand_id),('header_id.product_id','=',product_id),('header_id.state','in',('draft','confirmed','approved'))]"),
		'pattern_id': fields.many2one('kg.pattern.master', 'Pattern No'),
		'fns_item_name': fields.char('Foundry/MS/BOT', size=128),
		'order_line_id': fields.related('indent_id','order_line_id', type='many2one', relation='ch.work.order.details', string='WO.No', store=True, readonly=True),
		'ms_bot_id': fields.many2one('kg.machine.shop', 'MS/BOT Item'),
		'fns_item_name': fields.char('Foundry/MS/BOT', size=128),
		'position_id': fields.many2one('kg.position.number', string='Position No'),
		'length': fields.float('Length',readonly=True),
		'breadth': fields.float('Breadth',readonly=True),
		'flag_dynamic_length': fields.boolean('Dynamic Length'),
		'uom_conversation_factor': fields.selection([('one_dimension','One Dimension'),('two_dimension','Two Dimension')],'UOM Conversation Factor',readonly=True),
		
		## Child Tables Declaration
		
		'line_id': fields.one2many('ch.depindent.wo','header_id','Ch Line Id'),
		
	}
	
	_defaults = {
		
		'line_state': 'noprocess',
		'name': 'Dep.Indent.Line',
		'line_date': lambda * a: time.strftime('%Y-%m-%d'),
		'flag_dynamic_length': False
		
	}
	
	def onchange_moc(self, cr, uid, ids, moc_id_temp):
		value = {'moc_id':''}
		if moc_id_temp:
			rate_rec = self.pool.get('ch.brandmoc.rate.details').browse(cr,uid,moc_id_temp)
			value = {'moc_id': rate_rec.moc_id.id}
		return {'value': value}
	
	def confirm_indent_line(self, cr, uid, ids, context=None):
		entry_rec = self.browse(cr,uid,ids[0])
		self.write(cr, uid, ids,{'pending_qty':entry_rec.qty,'issue_pending_qty':entry_rec.qty,'po_qty':entry_rec.qty})
		return True
	
kg_depindent_line()

class ch_depindent_wo(osv.osv):
	
	_name = "ch.depindent.wo"
	_description = "Ch Depindent WO"
	
	_columns = {
		
		## Basic Info
		
		'header_id': fields.many2one('kg.depindent.line', 'Dept Indent Line', required=True, ondelete='cascade'),		
		'wo_id': fields.char('WO', required=True),
		#~ 'w_order_id': fields.many2one('kg.work.order','WO',required=True, domain="[('state','=','confirmed')]"),
		'w_order_id': fields.related('w_order_line_id','header_id', type='many2one', string='WO', store=True),
		'w_order_line_id': fields.many2one('ch.work.order.details','WO',required=True),
		'qty': fields.float('Indent Qty', required=True),
		
	}
	
	def _check_qty(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False					
		return True
	
	_constraints = [
		
		(_check_qty,'You cannot save with zero qty !',['WO Qty']),
		
		]
	
	def onchange_wo(self, cr, uid, ids,w_order_line_id):
		value = {'wo_id': ''}
		if w_order_line_id:
			wo_rec = self.pool.get('ch.work.order.details').browse(cr,uid,w_order_line_id)
			value = {'wo_id':wo_rec.order_no}
		return {'value':value}
	
ch_depindent_wo()
