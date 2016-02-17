import math
import re
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import openerp.addons.decimal_precision as dp


class kg_issue_return(osv.osv):

	_name = "kg.issue.return"
	_description = "KG Issue Return"
	_order = "date desc"

	
	_columns = {
	
		'name': fields.char('Issue Return No', size=64, readonly=True),
		'dep_name': fields.many2one('kg.depmaster','Department',required=True, select=True,readonly=True,states={'draft':[('readonly',False)]}),
		'date': fields.date('Issue Return Date',required=True,readonly=True,states={'draft':[('readonly',False)]}),
		'issue_return_line': fields.one2many('kg.issue.return.line', 'issue_return_id',
					'Issue Return Lines',readonly=True,states={'draft':[('readonly',False)]}),
		'active': fields.boolean('Active'),
		'user_id' : fields.many2one('res.users', 'Created By', readonly=True),
		'state': fields.selection([('draft', 'Draft'),('confirm','Waiting For Approval'),('approved','Approved'),('done','Done'),('cancel','Cancel')], 'Status', track_visibility='onchange', required=True),
		'gate_pass': fields.boolean('Gate Pass', readonly=False,states={'approved':[('readonly',True)]}),
		'creation_date':fields.datetime('Creation Date',required=True,readonly=True),
		'origin': fields.char('Source Location', size=264,readonly=True,states={'draft':[('readonly',False)]}),
		'remark': fields.text('Remarks'),
		
		'confirmed_by' : fields.many2one('res.users', 'Confirmed By', readonly=False,select=True),
		'approved_by' : fields.many2one('res.users', 'Approved By', readonly=False,select=True),
		'dep_issue_no':fields.many2one('kg.department.issue','Department Issue No',domain = "[('state','=','done'),('department_id','=',dep_name),('issue_return','=',False)]", readonly=True,states={'draft':[('readonly',False)]}),
		'depissue_date':fields.date('Department Issue Date',readonly=True),
		'return_type':fields.selection([('replacement','Excess Return'),('noreturn','Damage/Replacement Return')],'Return Type',readonly=True,states={'draft':[('readonly',False)]}),
		'reject_location':fields.many2one('stock.location','Reject Location',domain = [('scrap_location','=',True)],readonly=True,states={'draft':[('readonly',False)]}),
		'rj_flag':fields.boolean('Reject Flag'),
		'excess_flag':fields.boolean('Excess Flag'),
		'list_flag':fields.boolean('List Flag'),
		'company_id':fields.many2one('res.company','Company'),
		
	}
	
	_sql_constraints = [('code_uniq','unique(name)', 'Indent number must be unique!')]

	_defaults = {
		
		'state' : 'draft',
		'active' : 'True',
		'date' : fields.date.context_today,
		'user_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'rj_flag':False,
		'excess_flag':False,
		'company_id' : lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.issue.return', context=c),
		
	}
	
	def onchange_didate(self,cr,uid,ids,dep_issue_no,context=None):
		value = {'depissue_date': ''}
		issue_browse = self.pool.get('kg.department.issue').browse(cr,uid,dep_issue_no)
		value = {'depissue_date' : issue_browse.issue_date}
		return {'value':value}


	def onchange_qty(self,cr,uid,ids,return_type,context=None):
		value = {'rj_flag': '','excess_flag':'','excess_flag' : False}
		if return_type == 'noreturn':	
			value = {'rj_flag' : True}

		if return_type == 'replacement':
			value = {'excess_flag' : True,'rj_flag':False}

		return {'value': value}


	def list_issue(self, cr, uid, ids,context=None):
		
		rec  = self.browse(cr,uid,ids[0])
		print "rec",rec
		return_qty = 0
		excess_return_qty = 0
		if rec.list_flag == False:
			for line in rec.dep_issue_no.issue_line_ids:
				if line.return_qty == None or line.return_qty == False:
					return_qty = 0
				else:
					return_qty = line.return_qty
				
				if line.excess_return_qty == None or line.excess_return_qty == False:
					excess_return_qty = 0
				else:
					excess_return_qty = line.excess_return_qty
				print "excess_return_qty + return_qty",excess_return_qty + return_qty
				print "line.issue_qty",line.issue_qty
				qty = line.issue_qty - (excess_return_qty + return_qty)
				print "qty",qty
				#atop
				if qty == 0:
					rec.dep_issue_no.write({'issue_return':True})
				else:
					rec.dep_issue_no.write({'issue_return':False})

				if qty > 0:
					line_vals = {
						'issue_return_id':rec.id,
						'dep_issue_no_line':line.id,
						'product_id':line.product_id.id,
						'uom':line.uom_id.id,
						'qty':qty,
						'requested_by':rec.dep_issue_no.user_id.id,
						'line_state':'process',
						'issue_pending_qty':qty,
						'price_unit':line.price_unit,
						'returned_qty':qty,
						'return_type':rec.return_type,	
						'reject_location':rec.reject_location.id or False,
					}

					if line_vals:
						form_receipt = self.write(cr,uid,rec.id,{'issue_return_line':[(0,0,line_vals)]})

		rec.write({'list_flag':True})
		return True
		
	def confirm_issue_return(self, cr, uid, ids,context=None):
		rec  = self.browse(cr,uid,ids[0])
		if not rec.issue_return_line:
			raise osv.except_osv(
				_('Warning'),
				_('Line item cannot be empty'))
		if rec.return_type == None or rec.return_type == False:
			raise osv.except_osv(
				_('Warning'),
				_('Return Type cannot be empty.'))
		if rec.return_type == 'noreturn':
			if rec.reject_location == None or rec.reject_location == False:
				raise osv.except_osv(
					_('Warning'),
					_('Select Reject Location to proceed'))
		qty = 0
		for line in rec.issue_return_line:
			if line.return_type == None or line.return_type == False:
				raise osv.except_osv(
					_('Warning'),
					_('Return Type cannot be empty for the product %s')%(line.product_id.name))
			qty = line.dep_issue_no_line.issue_qty - (line.dep_issue_no_line.excess_return_qty + line.dep_issue_no_line.return_qty) 
			if qty < line.issue_pending_qty:
				raise osv.except_osv(
					_('Warning'),
					_('Return Qty is greater than issued Qty for the product %s')%(line.product_id.name))
			if line.return_type == 'noreturn':
				if line.reject_location == None:
					raise osv.except_osv(
						_('Warning'),
						_('Select Reject Location for %s to proceed')%(line.product_id.name))

		self.write(cr,uid,ids,{
			'name':self.pool.get('ir.sequence').get(cr, uid, 'kg.issue.return') or False,
			'state': 'confirm',
			'confirmed_by':uid
			})	
		return True
			
	def approve_indent(self, cr, uid, ids,context=None):
		obj = self.browse(cr,uid,ids[0])
		#print "obj.dep_name.reject_location.id",obj.dep_name.reject_location.id
		#obj.dep_issue_no.write({'issue_return':True})
		issue_pending_qty = 0
		pending_qty = 0
		return_qty = 0
		excess_return_qty = 0
		issue_return_qty = 0

		for line in obj.issue_return_line:
			if line.return_type == 'noreturn':
				# None value check for damage return
				if line.dep_issue_no_line.return_qty == None:
					issue_return_qty = 0
				else:
					issue_return_qty = issue_return_qty + line.dep_issue_no_line.return_qty
				line.dep_issue_no_line.write({'return_qty':issue_return_qty+line.issue_pending_qty})
				line.dep_issue_no_line.write({'issue_return_line':True})


				# Updating the department indent pending qty with damaged qty to proceed further
				if line.dep_issue_no_line.indent_line_id.issue_pending_qty == None:
					issue_pending_qty = 0
				else:
					issue_pending_qty = line.dep_issue_no_line.indent_line_id.issue_pending_qty
				if line.dep_issue_no_line.indent_line_id.pending_qty == None:
					pending_qty = 0
				else:
					pending_qty = line.dep_issue_no_line.indent_line_id.pending_qty
				if line.dep_issue_no_line.indent_line_id.return_qty == None:
					return_qty = 0
				else:
					return_qty = line.dep_issue_no_line.indent_line_id.return_qty
				line.dep_issue_no_line.indent_line_id.write({'issue_pending_qty':issue_pending_qty+line.issue_pending_qty})
				line.dep_issue_no_line.indent_line_id.write({'pending_qty':pending_qty + line.issue_pending_qty})
				line.dep_issue_no_line.indent_line_id.write({'return_qty':return_qty+line.issue_pending_qty})
				
				if line.dep_issue_no_line.indent_line_id.indent_id.state == 'done':
					
					line.dep_issue_no_line.indent_line_id.indent_id.write({'state':'inprogress'})
					line.dep_issue_no_line.indent_line_id.write({'state':'inprogress'})
					line.dep_issue_no_line.indent_line_id.write({'line_state':'noprocess'})
				if line.dep_issue_no_line.indent_line_id.indent_id.state == 'inprogress':
					line.dep_issue_no_line.indent_line_id.write({'state':'inprogress'})
					line.dep_issue_no_line.indent_line_id.write({'line_state':'noprocess'})


				#if line.dep_issue_no_line.indent_line_id.indent_id.state not in ['draft','save','confirm','approved']:
					#raise osv.except_osv(
						#_('Warning'),
						#_('You're not allowed to update the DI which in the state %s') % (line.dep_issue_no_line.indent_line_id.indent_id.state))
				
				

				lot_vals = {
					'product_id':line.product_id.id,
					'product_uom':line.uom.id,
					'price_unit':line.price_unit,
					'product_qty':line.issue_pending_qty,
					'pending_qty':line.issue_pending_qty,
					'issue_qty':line.issue_pending_qty,
					'grn_type':'material',
					'lot_type':'out',
					#'return_remarks':'Lot from issue Return line id'+str(line.id),
				}
				if lot_vals:
					self.pool.get('stock.production.lot').create(cr,uid,lot_vals,context=None)
				else:
					raise osv.except_osv(
						_('Warning!!'),
						_('There no line information to load!!'))
				print"line.idline.idline.id",line.id
				print"obj.idobj.idobj.id",obj.id
				form_vals = {
			
					'product_id':line.product_id.id,
					'product_uom':line.uom.id,
					'product_uos':line.uom.id,
					'product_qty':line.issue_pending_qty,
					'product_uos_qty':line.issue_pending_qty,
					'name':line.product_id.name,
					'location_id':14,
					'location_dest_id':line.reject_location.id,
					'state':'done',
					'move_type':'out',
					#'return_id':obj.id,
					#'return_line_id':line.id,
					'stock_rate':line.price_unit,
					'stock_uom':line.uom.id,
					'po_to_stock_qty':line.issue_pending_qty,
					
				}
				if form_vals:
					self.pool.get('stock.move').create(cr,uid,form_vals,context=None)
				else:
					raise osv.except_osv(
						_('Warning!!'),
						_('There no line information to load!!'))
			if line.return_type == 'replacement':
				# None value check for Excess return
				if line.dep_issue_no_line.excess_return_qty == None:
					excess_return_qty = 0
				else:
					excess_return_qty = excess_return_qty + line.dep_issue_no_line.excess_return_qty

				line.dep_issue_no_line.write({'excess_return_qty':excess_return_qty+line.issue_pending_qty})
				line.dep_issue_no_line.write({'excess_flag':True})
				qty = 0
				issue_pending = line.issue_pending_qty
				for lot in line.dep_issue_no_line.kg_grn_moves:
					if lot.product_qty > line.issue_pending_qty:
						lot.write({'pending_qty':lot.pending_qty+line.issue_pending_qty})
						lot.write({'return_remarks':'Lot from Excess Return line id'+str(line.id)})
					if lot.product_qty < line.issue_pending_qty:
						lot.write({'pending_qty':lot.product_qty})
						issue_pending = issue_pending - lot.product_qty
						lot.write({'return_remarks':'Lot from Excess Return line id'+str(line.id)})
						if issue_pending == 0:
							break

				form_vals = {
			
					'product_id':line.product_id.id,
					'product_uom':line.uom.id,
					'product_uos':line.uom.id,
					'product_qty':line.issue_pending_qty,
					'product_uos_qty':line.issue_pending_qty,
					'name':line.product_id.name,
					'location_id':223,
					'location_dest_id':47,
					'state':'done',
					'move_type':'in',
					'return_id':obj.id,
					'return_line_id':line.id,
					'stock_rate':line.price_unit,
					'stock_uom':line.uom.id,
					'po_to_stock_qty':line.issue_pending_qty,
				}
				if form_vals:
					self.pool.get('stock.move').create(cr,uid,form_vals,context=None)
				else:
					raise osv.except_osv(
						_('Warning!!'),
						_('There no line information to load!!'))

		self.write(cr,uid,ids,{'state':'approved','approved_by':uid})
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
			if si.issue_return_line==[] or si.issue_return_line:
					tot = 0.0
					for line in si.issue_return_line:
						tot += line.qty
					if tot <= 0.0:			
						return False
						
			return True
	
	#_constraints = [
	
		#(_check_lineitem, 'You can not save this Service Indent with out Line and Zero Qty  !!',['qty']),

		#]	

kg_issue_return()

class kg_issue_return_line(osv.osv):
	
	_name = "kg.issue.return.line"
	_description = "Issue Return Line"

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

	'issue_return_id': fields.many2one('kg.issue.return', 'Indent No', required=True, ondelete='cascade'),
	'product_id': fields.many2one('product.product', 'Product', required=True,domain = [('state','=','approved'),'|',('type','=','service')]),
	'uom': fields.many2one('product.uom', 'UOM', required=True),
	'qty': fields.float('Issued Quantity', required=True),
	'pending_qty':fields.float('Pending Qty'),
	'issue_pending_qty':fields.float('Return Qty'),
	'gate_pending_qty':fields.float('Gate Pass Pending Qty'),
	'note': fields.text('Remarks'),	
	'line_state': fields.selection([('process','Processing'),('noprocess','NoProcess'),('pi_done','PI-Done'),('done','Done')], 'Status'),
	'line_date': fields.date('Indent Date'),
	'requested_by' : fields.many2one('res.users', 'Approved By', readonly=False,select=True),
	'return_type':fields.selection([('replacement','Excess Return'),('noreturn','Damage/Replacement Return')],'Return Type'),
	'dep_issue_no_line':fields.many2one('kg.department.issue.line','Department Issue Line'),
	'price_unit':fields.float('Unit Price'),
	'reject_location':fields.many2one('stock.location','Reject Location',domain = [('scrap_location','=',True)]),
	'rj_flag':fields.boolean('Reject Flag'),
	'excess_flag':fields.boolean('Excess Flag'),
	'returned_qty':fields.float('Returned Qty'),


	}

	_defaults = {

		'line_date' : fields.date.context_today,
		'rj_flag':False,
		'excess_flag':False,


	}
	def onchange_qty(self,cr,uid,ids,return_type,context=None):
		value = {'rj_flag': '','excess_flag':''}
		if return_type == 'noreturn':	
			value = {'rj_flag' : True}

		if return_type == 'replacement':
			value = {'excess_flag' : True}

		return {'value': value}

	
kg_issue_return_line()	
