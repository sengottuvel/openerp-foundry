import math
import re
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import netsvc
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from itertools import groupby

class kg_gate_pass(osv.osv):
	
	_name = "kg.gate.pass"
	_description = "KG Gate Pass"
	_order = "date desc"
	
	_columns = {
		
		## Basic Info
		
		'name': fields.char('Gate Pass No', size=128, readonly=True),
		'date': fields.date('Gate Pass Date',readonly=True, states={'draft':[('readonly',False)]},required=True),
		'note': fields.text('Remarks',readonly=False, states={'confirmed':[('readonly',False)],'done':[('readonly',False)]}),
		'state': fields.selection([('draft', 'Draft'), ('confirmed', 'WFA'), ('done', 'Delivered'), ('cancel', 'Cancelled'), ('reject', 'Rejected')], 'Out Status',readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'remark': fields.text('Remarks'),
		
		## Module Requirement Info
		
		'dep_id': fields.many2one('kg.depmaster','Source Location', select=True,readonly=True, states={'draft':[('readonly',False)]}),
		'return_date': fields.date('Expected Return Date',readonly=True, states={'draft':[('readonly',False)]},required=True),
		'partner_id': fields.many2one('res.partner', 'Supplier',domain="[('supplier','=',True)]"),
		'out_type': fields.many2one('kg.outwardmaster', 'OutwardType',domain="[('state','not in',(''reject),'cancel')]"),
		'origin': fields.many2one('kg.service.indent', 'Origin', readonly=True),
		'in_state': fields.selection([('pending', 'Pending'), ('partial', 'Partial'), ('done', 'Received'), ('cancel', 'Cancelled')], 'In Status',readonly=True),
		#~ 'in_state': fields.selection([('open', 'OPEN'),('pending', 'Pending'), ('done', 'Received'), ('cancel', 'Cancelled')], 'In Status',readonly=True),
		'si_indent_ids':fields.many2many('kg.service.indent.line','s_indent_gp_entry' , 'si_id', 'gp_id', 'Service Indent Lines',
			domain="[('service_id.state','=','approved'), '&', ('pending_qty','>','0')]", 
			readonly=True, states={'draft': [('readonly', False)]}),
		'indent_flag': fields.boolean('Indent'),
		'transport':fields.char('Transport', size=128,readonly=True, states={'draft':[('readonly',False)]}),
		'transport_id':fields.many2one('kg.transport','Transport',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'taken_by':fields.char('Taken By', size=128,readonly=True, states={'draft':[('readonly',False)]}),
		'received_by':fields.char('Received By', size=128,readonly=True, states={'draft':[('readonly',False)]}),
		'project':fields.char('Project',size=100,readonly=True,states={'draft':[('readonly',False)]}),
		'division':fields.char('Division',size=100,readonly=True,states={'draft':[('readonly',False)]}),
		'confirm_flag':fields.boolean('Confirm Flag'),
		'approve_flag':fields.boolean('Expiry Flag'),
		'mode': fields.selection([('direct', 'Direct'), ('frm_indent', 'From Indent')], 'Entry Mode',required=True,readonly=True, states={'draft':[('readonly',False)]}),
		'gp_type': fields.selection([('from_so', 'From SI'), ('direct', 'Direct')], 'GP Type',readonly=True),
		'vehicle_details':fields.char('Vehicle Details',readonly=True, states={'draft':[('readonly',False)]}),
		'outward_type': fields.selection([('in_reject', 'Inward Rejection'),('service','Send For Service'),('in_transfer','Internal Transfer')], 'Outward Type',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		
		## Child Tables Declaration
		
		'gate_line': fields.one2many('kg.gate.pass.line', 'gate_id', 'Gate Pass Line',readonly=True, states={'draft':[('readonly',False)]},required=True),
		
		## Entry Info
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),		
		'user_id': fields.many2one('res.users', 'Created By',readonly=True),
		'creation_date':fields.datetime('Created Date',readonly=True),
		'confirmed_by' : fields.many2one('res.users', 'Confirmed By', readonly=True,select=True),
		'confirmed_date':fields.datetime('Confirmed Date',readonly=True),
		'reject_date': fields.datetime('Rejected Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'approved_by' : fields.many2one('res.users', 'Approved By', readonly=True,select=True),
		'approved_date':fields.datetime('Approved Date',readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		'cancel_remarks': fields.text('Cancel Remarks'),
		
	}
	
	_defaults = {
		
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
		'state': 'draft',
		'name': '',
		'user_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.gate.pass', context=c),
		'in_state': 'pending',
		'indent_flag': False,
		'gp_type': 'from_so',
		'active': True,
		'mode': 'direct',
		'entry_mode': 'manual',
		
	}
	
	def _check_lineitems(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.entry_mode == 'manual' and entry.mode == 'direct' or entry.indent_flag == True:
			if not entry.gate_line:
				return False
		return True
		
	_constraints = [        
              
        (_check_lineitems, 'System not allow to save with empty Details !!',['']),
       
       ]
       
	def onchange_return_date(self,cr,uid,ids,return_date,context=None):
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		return_date = str(return_date)
		return_date = datetime.strptime(return_date, '%Y-%m-%d')
		if return_date >= today:
			return False
		else:
			raise osv.except_osv(_('Warning!'),
				_('System not allow to save with past date !!'))
							
	def write(self, cr, uid, ids, vals, context=None):		
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_gate_pass, self).write(cr, uid, ids, vals, context)
	
	def cancel_entry(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'done':
			if not rec.cancel_remarks:
				raise osv.except_osv(_('Warning'),
					_('Enter Cancel remark !!'))
			self.write(cr, uid,ids,{'state' : 'cancel',
									'cancel_user_id': uid,
									'cancel_date': time.strftime("%Y-%m-%d %H:%M:%S"),
									})
												
	def reject_entry(self, cr, uid, ids, context=None):
		rec = self.browse(cr.uid.ids[0])
		if rec.state == 'confirmed':
			if not rec.remark:
				raise osv.except_osv(_('Rejection remark is must !!'),
					_('Enter rejection remark in remark field !!'))
			self.write(cr, uid,ids,{'state' : 'draft',
									'rej_user_id': uid,
									'reject_date': time.strftime("%Y-%m-%d %H:%M:%S"),
									})
												
	def confirm_entry(self, cr, uid, ids, context=None):	
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			if not entry.name:
				seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.gate.pass')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry.date))
				seq_name = cr.fetchone();
				self.write(cr,uid,ids[0],{'name':seq_name[0]})
			if entry.mode == 'frm_indent':
				for line in entry.gate_line:
					if line.qty > line.indent_qty:
						raise osv.except_osv(_('Warning!'),
								_('You cannot increase qty more than indent qty'))	
				
			self.write(cr,uid,ids[0],{'state':'confirmed','confirmed_by':uid,
							'confirm_flag':True,'confirmed_date':time.strftime('%Y-%m-%d %H:%M:%S')})
						
		return True
		
	def approve_entry(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			#if rec.confirmed_by.id == uid:
			#	raise osv.except_osv(
			#			_('Warning'),
			#			_('Approve cannot be done by Confirmed user'))
			if rec.mode == 'frm_indent':
				for line in rec.gate_line:
					indent_pen_qty = line.indent_qty - line.qty
					gp_qty = line.qty
					old_indent_pen_qty = line.si_line_id.pending_qty
					new_pen_qty = old_indent_pen_qty - gp_qty
					line.si_line_id.write({'gate_pending_qty':new_pen_qty})
			else:
				pass
			rec.write({'state': 'done','approved_by':uid,'approve_flag':True,'approved_date':time.strftime('%Y-%m-%d %H:%M:%S')})	
		
		return True
		
	def gate_pass_print(self, cr, uid, ids, context=None):
				
		#assert len(ids) == 1, 'This option should only be used for a single id at a time'
		wf_service = netsvc.LocalService("workflow")
		wf_service.trg_validate(uid, 'kg.gate.pass', ids[0], 'send_rfq', cr)
		datas = {
				 'model': 'kg.gate.pass',
				 'ids': ids,
				 'form': self.read(cr, uid, ids[0], context=context),
		}
		return {'type': 'ir.actions.report.xml', 'report_name': 'gate.pass.report', 'datas': datas, 'nodestroy': True}

	def create_gp_line(self,cr,uid,ids,context=False):
				
		indent_line_obj = self.pool.get('kg.service.indent.line')
		gp_line_obj = self.pool.get('kg.gate.pass.line')
		prod_obj = self.pool.get('product.product')		
		user_obj = self.pool.get('res.users')
		line_ids = []			   
		res={}
		res['line_ids'] = []
		res['indent_flag'] = True
		obj =  self.browse(cr,uid,ids[0])
		user_rec = obj.user_id
		user = user_rec.id
		if obj.gate_line:
			for line in obj.gate_line:
				line.si_line_id.write({'line_state' : 'noprocess'})			
			line_ids = map(lambda x:x.id,obj.gate_line)
			gp_line_obj.unlink(cr,uid,line_ids)
		if obj.si_indent_ids:
			indent_line_ids = map(lambda x:x.id,obj.si_indent_ids)
			indent_line_browse = indent_line_obj.browse(cr,uid,indent_line_ids)
			indent_line_browse = sorted(indent_line_browse, key=lambda k: k.product_id.id)
			groups = []
			for key, group in groupby(indent_line_browse, (lambda x: x.product_id.id)  ):
				for key,group in groupby(group,lambda x: x.brand_id.id):
					groups.append(map(lambda r:r,group))
			for key,group in enumerate(groups):
				qty = sum(map(lambda x:float(x.qty),group))
				pending_qty = sum(map(lambda x:float(x.pending_qty),group)) #TODO: qty
				indent_line_ids = map(lambda x:x.id,group)
				if len(indent_line_ids) > 1:
					flag = True
				else:
					flag = False
				prod_browse = group[0].product_id
				brand_id = group[0].brand_id			
				uom = group[0].uom.id or False
				depindent_id= group[0].id
				qty = pending_qty
				remark = group[0].note
				serial_no = group[0].serial_no.id
				ser_no = group[0].ser_no
					
				vals = {
			
				'product_id':prod_browse.id,
				'brand_id':brand_id.id,
				'uom':uom,
				'qty':qty,
				'indent_qty':qty,
				'grn_pending_qty':qty,				
				'so_pending_qty':qty,						
				'si_line_id':depindent_id,				
				'group_flag': flag,
				'note':remark,
				'ser_no':ser_no,
				'serial_no':serial_no,
				}
				
				if pending_qty == 0:				
					indent_line_obj.write(cr,uid,depindent_id,{'line_state' : 'process'})
				
				if ids:
					self.write(cr,uid,ids[0],{'gate_line':[(0,0,vals)]})
								
		self.write(cr,uid,ids,res)			
		return True		
		
	def update_product_group(self,cr,uid,ids,line,context=None):		
		pi_rec = self.browse(cr, uid, ids[0])
		line_obj = self.pool.get('purchase.requisition.line')
		dep_line_obj = self.pool.get('kg.depindent.line')
		product_obj = self.pool.get('product.product')
		cr.execute(""" select depindent_line_id from kg_depindent_pi_line where pi_id = %s """ %(str(ids[0])))
		data = cr.dictfetchall()
		val = [d['depindent_line_id'] for d in data if 'depindent_line_id' in d] 
		product_id = line.product_id.id
		product_record = product_obj.browse(cr, uid, product_id)
		list_line = dep_line_obj.search(cr,uid,[('id', 'in', val), ('product_id', '=', product_id)],context=context)
		depindent_line_id=line.depindent_line_id
		pi_qty = line.product_qty
		
		for i in list_line:
			bro_record = dep_line_obj.browse(cr, uid,i)
			orig_depindent_qty = bro_record.pending_qty
			po_uom_qty = bro_record.po_qty
			pi_used_qty = pi_qty
			uom = bro_record.uom.id
			po_uom = bro_record.po_uom.id
			if uom != po_uom:					
				if pi_used_qty <= po_uom_qty:
					pending_po_depindent_qty =  po_uom_qty - pi_used_qty
					pending_stock_depindent_qty = orig_depindent_qty - (pi_used_qty * product_record.po_uom_coeff)
					sql = """ update kg_depindent_line set po_qty=%s, pending_qty=%s where id = %s"""%(pending_po_depindent_qty,
						pending_stock_depindent_qty,bro_record.id)
					cr.execute(sql)
					#dep_line_obj.write(cr,uid, bro_record.id, {'line_state' : 'noprocess'})
					break
				else:
					remain_qty = pi_used_qty - po_uom_qty
					pi_qty = remain_qty
					pending_po_depindent_qty =  0.0
					pending_stock_depindent_qty = 0.0
					sql = """ update kg_depindent_line set po_qty=%s, pending_qty=%s where id = %s"""%(pending_po_depindent_qty,
						pending_stock_depindent_qty,bro_record.id)
					cr.execute(sql)
					#dep_line_obj.write(cr,uid, bro_record.id, {'line_state' : 'noprocess'})
					if remain_qty < 0:
						break			
			else:
				if pi_used_qty <= po_uom_qty:
					pending_po_depindent_qty =  po_uom_qty - pi_used_qty
					pending_stock_depindent_qty = po_uom_qty - pi_used_qty 
					sql = """ update kg_depindent_line set po_qty=%s, pending_qty=%s where id = %s"""%(pending_po_depindent_qty,
						pending_stock_depindent_qty,bro_record.id)
					cr.execute(sql)
					#dep_line_obj.write(cr,uid, bro_record.id, {'line_state' : 'noprocess'})
					break
				else:
					remain_qty = pi_used_qty - po_uom_qty
					pi_qty = remain_qty
					pending_po_depindent_qty =  0.0
					pending_stock_depindent_qty = 0.0
					sql = """ update kg_depindent_line set po_qty=%s, pending_qty=%s where id = %s"""%(pending_po_depindent_qty,
						pending_stock_depindent_qty,bro_record.id)
					cr.execute(sql)
					#dep_line_obj.write(cr,uid, bro_record.id, {'line_state' : 'noprocess'})
					if remain_qty < 0:
						break		
		return True
	
kg_gate_pass()

class kg_gate_pass_line(osv.osv):
	
	_name = "kg.gate.pass.line"
	_description = "Gate Pass Line"
	
	_columns = {
		
		## Basic Info
		
		'gate_id': fields.many2one('kg.gate.pass', 'Gate Pass', ondelete='cascade'),
		
		## Module Requirement Fields
		
		'product_id': fields.many2one('product.product', 'Item Name',domain=[('state','not in',('reject','cancel'))]),
		'brand_id': fields.many2one('kg.brand.master', 'Brand Name',domain="[('product_ids','in',(product_id)),('state','in',('draft','confirmed','approved'))]"),
		'moc_id': fields.many2one('ch.brandmoc.rate.details','MOC',domain="[('brand_id','=',brand_id),('header_id.product_id','=',product_id),('header_id.state','in',('draft','confirmed','approved'))]"),
		'uom': fields.many2one('product.uom', 'UOM'),
		'qty': fields.float('Quantity'),
		'indent_qty': fields.float('Indent Qty'),
		'grn_pending_qty': fields.float('GRN pending Qty'),
		'so_pending_qty': fields.float('SO pending Qty'),
		'note': fields.text('Remarks'),
		'si_line_id':fields.many2one('kg.service.indent.line', 'Service Indent Line'),
		'group_flag':fields.boolean('Group By'),
		'ser_no':fields.char('Serial No', size=128),
		'so_flag':fields.boolean('SO Flag'),
		'serial_no':fields.many2one('stock.production.lot','Serial No',domain="[('product_id','=',product_id)]"),	
		'mode': fields.selection([('direct', 'Direct'), ('frm_indent', 'From Indent')], 'Mode'),
		'remark_id': fields.many2one('kg.rejection.master','Remarks'),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		
	}
	
	_defaults = {
		
		'entry_mode': 'manual',
		
	}
	
	def onchange_uom(self, cr, uid, ids,product_id):
		if product_id:
			pro_rec = self.pool.get('product.product').browse(cr, uid,product_id)
			uom = pro_rec.uom_po_id.id
			return {'value': {'uom': uom}}
		else:
			return {'value': {'uom': False}}
	
	def onchange_pending_qty(self, cr, uid, ids,qty,grn_pending_qty,so_pending_qty):
		value = {'grn_pending_qty': '','so_pending_qty':''}
		value = {'grn_pending_qty': qty,'so_pending_qty': qty}
		return {'value': value}
		
	def default_get(self, cr, uid, fields, context=None):
		print"contextcontextcontext",context
		
		return context
		
kg_gate_pass_line()
