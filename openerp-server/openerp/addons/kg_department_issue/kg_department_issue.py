import math
import re
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from itertools import groupby

import datetime
import calendar
from datetime import date
import re
import urllib
import urllib2
import logging
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import calendar
today = datetime.now()

ORDER_PRIORITY = [
   ('normal','Normal'),
   ('emergency','Emergency')
]

class kg_department_issue(osv.osv):
	
	_name = "kg.department.issue"
	_description = "Department Issue"
	_order = "issue_date desc"
	
	_columns = {
		
		## Basic Info
		
		'name': fields.char('Issue No.',readonly=True),
		'issue_date':fields.date('Issue Date',required=True,readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		'state': fields.selection([('draft', 'Draft'),
			('confirmed', 'WFC'),
			('approve', 'WFA'),
			('done', 'Issued'),('cancel', 'Cancelled'),('reject', 'Rejected')], 'Status',readonly=True),
		'remarks': fields.text('Remarks',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		'can_remark': fields.text('Cancel Remarks'),
		'reject_remark': fields.text('Reject Remarks'),
		'notes': fields.text('Notes'),
		
		## Module Requirement Info
		
		'kg_dep_indent_line':fields.many2many('kg.depindent.line', 'kg_department_indent_picking', 'kg_depline_id', 'stock_picking_id', 'Department Indent', 
				 domain="[('indent_id.state','=','approved'), '&', ('indent_id.main_store','=',False),'&', ('indent_id.dep_name','=',department_id),'&', ('issue_pending_qty','>','0'),'&', ('pi_cancel' ,'!=', 'True')]", 
				 readonly=True, states={'draft': [('readonly', False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		'outward_type': fields.many2one('kg.outwardmaster', 'Outward Type',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		'department_id': fields.many2one('kg.depmaster','Department',required=True,readonly=True, 
						 domain="[('item_request','=',True),('state','in',('draft','confirmed','approved'))]", states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		'type': fields.selection([('in', 'IN'), ('out', 'OUT'), ('internal', 'Internal')], 'Type'),
		'confirm_flag':fields.boolean('Confirm Flag'),
		'approve_flag':fields.boolean('Expiry Flag'),
		'products_flag':fields.boolean('Products Flag'),
		'user_id' : fields.many2one('res.users', 'User', readonly=False),
		'project':fields.char('Project',size=100,readonly=True,states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		'building':fields.char('Building',size=100,readonly=True,states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		'issue_type': fields.selection([('material', 'Material'), ('service', 'Service')], 'Issue Type',readonly=True,states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		'kg_service_indent_line':fields.many2many('kg.service.indent.line', 'kg_service_indent_picking', 'kg_serviceline_id', 'service_issue', 'Service Indent', 
				 domain="[('service_id.state','=','approved'),'&', ('service_id.dep_name','=',department_id),'&', ('issue_pending_qty','>','0')]", 
				  readonly=True, states={'draft': [('readonly', False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		#'save_flag':fields.boolean('Save Flag'),
		'issue_return':fields.boolean('Issue Return'),
		'dep_issue_type':fields.selection([('from_indent','From Indent'),('direct','Direct')],'Issue Mode',required=True,
					readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'wo_line_id': fields.many2one('ch.work.order.details','WO No.',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'location_id': fields.many2one('stock.location', 'Source Location',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		
		## Child Tables Declaration
		
		'issue_line_ids':fields.one2many('kg.department.issue.line','issue_id','Line Entry',
						 readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		
		## Entry Info
		
		'active':fields.boolean('Active'),
		'company_id':fields.many2one('res.company','Company',readonly=True),
		'created_by':fields.many2one('res.users','Created By',readonly=True),
		'creation_date':fields.datetime('Created Date',required=True,readonly=True),
		'confirmed_by':fields.many2one('res.users','Confirmed By',readonly=True),
		'confirmed_date':fields.datetime('Confirmed Date',readonly=True),
		'approved_by':fields.many2one('res.users','Approved By',readonly=True),
		'approved_date':fields.datetime('Approved Date',readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'reject_date': fields.datetime('Rejected Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'update_date' : fields.datetime('Last Updated Date',readonly=True),
		'update_user_id' : fields.many2one('res.users','Last Updated By',readonly=True),
		
	}
	
	_defaults = {
		
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'approved_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'issue_date': lambda * a: time.strftime('%Y-%m-%d'),
		'created_by': lambda obj, cr, uid, context: uid,
		'state': 'draft',
		'type': 'out',
		'name': '',
		'active': True,
		'confirm_flag': False,
		'approve_flag': False,
		#'save_flag': False, 
		'issue_return': False,
		'company_id' : lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.department.issue', context=c),
		'user_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
		
	}
	
	def _issdate_validation(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		today = date.today()
		issue_date = datetime.strptime(rec.issue_date,'%Y-%m-%d').date()
		if issue_date > today:
			return False
		return True
	
	def _uom_validation(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.issue_line_ids:
			for item in rec.issue_line_ids:
				if item.product_id.id and item.uom_id.id:
					pro_rec = self.pool.get('product.product').browse(cr,uid,item.product_id.id)
					if item.uom_id.id == pro_rec.uom_id.id or item.uom_id.id == pro_rec.uom_po_id.id:
						pass
					else:
						raise osv.except_osv(_('UOM Mismatching Error !'),
							_('You choosed wrong UOM and you can choose either %s or %s for %s !!') % (pro_rec.uom_id.name,pro_rec.uom_po_id.name,pro_rec.name))
		return True
	
	def _dp2_qty_validation(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.dep_issue_type == 'from_indent' and rec.department_id.name == 'DP2':
			if rec.issue_line_ids:
				for item in rec.issue_line_ids:
					if item.indent_qty > 0 and item.indent_line_id:
						indent_rec = self.pool.get('kg.depindent.line').browse(cr,uid,item.indent_line_id.id)
						if indent_rec.cutting_qty != indent_rec.qty:
							#~ qty = (round(item.issue_qty,2)*100) / ((round(indent_rec.qty,2)*100)/(indent_rec.cutting_qty*100))
							qty = (indent_rec.qty/indent_rec.cutting_qty) * item.issue_qty
							number_dec = str(qty-int(qty))[1:]
							number_dec = float(number_dec)
							if number_dec > 0.00:
								raise osv.except_osv(_('Warning!'),
									_('System not allow to issue %s. Insufficient MS Qty"'%(item.product_id.name)))
							else:
								pass
		return True
	
	_constraints = [
		
		(_issdate_validation, 'Issue Date should not be greater than current date !!',['issue_date']),
		(_uom_validation, 'You choosed wrong UOM !!',['']),
		#~ (_dp2_qty_validation, 'Qty mismatched',['']),
		
		]
	
	def onchange_direct_issue(self,cr,uid,ids,dep_iss_type,products_flag,context = None):
		value = {'products_flag':'','state':''}
		state = 'draft'
		if dep_iss_type == 'from_in' or dep_iss_type == 'direct':
			product_flag = True
			state = 'draft'
		else:
			product_flag = False
		if dep_iss_type == 'direct':
			state = 'confirmed'
		return {'value':{'products_flag':product_flag,'state':state}}
	
	def write(self, cr, uid, ids, vals, context=None):		
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_department_issue, self).write(cr, uid, ids, vals, context)
	
	def entry_reject(self, cr, uid, ids, context=None):		
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approve':
			if not rec.reject_remark:
				raise osv.except_osv(_('Remarks Needed !!'),
					_('Enter Remarks for Issue Rejection..'))
			for item in rec.issue_line_ids:
				if item.kg_grn_moves:
					sql = """ select lot_id from kg_department_issue_details where grn_id=%s""" %(item.id)
					cr.execute(sql)
					data = cr.dictfetchall()
					if data:
						val = [d['lot_id'] for d in data if 'lot_id' in d]
						for i in val:
							lot_rec = self.pool.get('stock.production.lot').browse(cr,uid,i)
							lot_rec.write({'reserved_qty': lot_rec.pending_qty})
					else:
						pass
			self.write(cr, uid,ids,{'state' : 'reject','reject_date':time.strftime('%Y-%m-%d %H:%M:%S'),'rej_user_id':uid})
		return True
	
	def entry_cancel(self, cr, uid, ids, context=None):		
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'done':
			if not rec.can_remark:
				raise osv.except_osv(_('Remarks Needed !!'),
					_('Enter Remarks for Issue Cancellation..'))
			self.write(cr, uid,ids,{'state' : 'cancel','cancel_date':time.strftime('%Y-%m-%d %H:%M:%S'),'cancel_user_id':uid})
		return True
	
	def onchange_user_id(self, cr, uid, ids, user_id, context=None):
		value = {'department_id': ''}
		if user_id:
			user = self.pool.get('res.users').browse(cr, uid, user_id, context=context)
			value = {'department_id': user.dep_name.id}
		return {'value': value}
	
	def print_issue_slip(self, cr, uid, ids, context=None):		
		assert len(ids) == 1, 'This option should only be used for a single id at a time'
		wf_service = netsvc.LocalService("workflow")
		wf_service.trg_validate(uid, 'kg.department.issue', ids[0], 'send_rfq', cr)
		datas = {
				 'model': 'kg.department.issue',
				 'ids': ids,
				 'form': self.read(cr, uid, ids[0], context=context),
		}
		return {'type': 'ir.actions.report.xml', 'report_name': 'issueslip.on.screen.report', 'datas': datas, 'nodestroy': True}
	
	def update_depindent_to_issue(self,cr,uid,ids,context=None):
		obj =  self.browse(cr,uid,ids[0])
		if obj.state in ('draft','confirmed'):
			depindent_line_obj = self.pool.get('kg.depindent.line')
			issue_line_obj = self.pool.get('kg.department.issue.line')
			move_obj = self.pool.get('stock.move')
			prod_obj = self.pool.get('product.product')
			dep_obj = self.pool.get('kg.depmaster')
			line_ids = []			   
			res={}
			line_ids = []
			res['move_lines'] = []
			if obj.issue_line_ids:
				issue_lines = map(lambda x:x.id,obj.issue_line_ids)
				issue_line_obj.unlink(cr,uid,issue_lines)
			dep_rec = dep_obj.browse(cr, uid, obj.user_id.dep_name.id)
			issue_dep_id = obj.department_id.id
			
			obj.write({'state': 'confirmed'})
			obj.write({'products_flag': True})
			if obj.kg_dep_indent_line:
				depindent_line_ids = map(lambda x:x.id,obj.kg_dep_indent_line)
				depindent_line_browse = depindent_line_obj.browse(cr,uid,depindent_line_ids)
				depindent_line_browse = sorted(depindent_line_browse, key=lambda k: k.product_id.id)
				groups = []
				for key, group in groupby(depindent_line_browse, lambda x: x.id):
				#~ for key, group in groupby(depindent_line_browse, lambda x: x.product_id.id):
					groups.append(map(lambda r:r,group))
				for key,group in enumerate(groups):
					#~ qty = sum(map(lambda x:float(x.issue_pending_qty),group)) #TODO: qty
					qty = map(lambda x:float(x.issue_pending_qty),group)[0]
					cutting_qty = 0
					if obj.department_id.name == 'DP2':
						if group[0].qty == group[0].cutting_qty:
							cutting_qty = qty
						elif group[0].qty != group[0].cutting_qty:
							cutting_qty = group[0].issue_pending_qty / (group[0].qty/group[0].cutting_qty)
						else:
							cutting_qty = qty
					else:
						cutting_qty = qty
					depindent_line_ids = map(lambda x:x.id,group)
					prod_browse = group[0].product_id
					ms_bot_id = group[0].ms_bot_id.id
					brand_id = group[0].brand_id.id				
					uom =False
					indent = group[0].indent_id
					dep = indent.dep_name.id
					uom = group[0].uom.id or False
					depindent_obj = self.pool.get('kg.depindent').browse(cr, uid, indent.id)
					if depindent_obj.order_line_id:
						wo_id = depindent_obj.order_line_id.header_id.id
					else:
						wo_id = False
					dep_stock_location = depindent_obj.dest_location_id.id
					#~ main_location = depindent_obj.src_location_id.id
					main_location = obj.location_id.id
					
					vals = {
					
						'indent_id':depindent_obj.id,
						'w_order_line_id':depindent_obj.order_line_id.id or False,
						'wo_id':wo_id,
						'ms_bot_id':ms_bot_id,
						'product_id':prod_browse.id,
						'brand_id':brand_id,
						'uom_id':uom,
						'issue_qty':cutting_qty,
						'issue_qty_2':cutting_qty,
						'indent_qty':qty,
						'length':group[0].length,
						'breadth':group[0].breadth,
						'uom_conversation_factor':group[0].product_id.uom_conversation_factor,
						'name':prod_browse.name,
						'location_id':main_location,
						'location_dest_id':dep_stock_location,
						'state' : 'confirmed',
						'indent_line_id' : group[0].id,
						'wo_moc_id' : group[0].moc_id.id,
						'issue_type':'material',
						'wo_state':'accept',
						'dep_issue_type':obj.dep_issue_type,
						'dep_id':obj.department_id.id,
						'dep_code':obj.department_id.name,
						#~ 'state':'draft',
						}
						
					if ids:
						self.write(cr,uid,ids[0],{'issue_line_ids':[(0,0,vals)]})
			self.write(cr,uid,ids,res)
		
		return True
	
	def update_serviceindent_to_issue(self,cr,uid,ids,context=None):
		obj =  self.browse(cr,uid,ids[0])
		if obj.state in ('draft','confirmed'):
			serviceindent_line_obj = self.pool.get('kg.service.indent.line')
			issue_line_obj = self.pool.get('kg.department.issue.line')
			move_obj = self.pool.get('stock.move')
			prod_obj = self.pool.get('product.product')
			dep_obj = self.pool.get('kg.depmaster')
			line_ids = []			   
			res={}
			line_ids = []
			res['move_lines'] = []
			if obj.issue_line_ids:
				issue_lines = map(lambda x:x.id,obj.issue_line_ids)
				move_obj.unlink(cr,uid,issue_lines)
			
			dep_rec = dep_obj.browse(cr, uid, obj.user_id.dep_name.id)
			issue_dep_id = obj.department_id.id
			obj.write({'state': 'confirmed'})
			obj.write({'products_flag': True})
			if obj.kg_service_indent_line:
				serviceindent_line_ids = map(lambda x:x.id,obj.kg_service_indent_line)
				serviceindent_line_browse = serviceindent_line_obj.browse(cr,uid,serviceindent_line_ids)
				serviceindent_line_browse = sorted(serviceindent_line_browse, key=lambda k: k.product_id.id)
				groups = []
				for key, group in groupby(depindent_line_browse, lambda x: x.id):
				#~ for key, group in groupby(serviceindent_line_browse, lambda x: x.product_id.id):
					groups.append(map(lambda r:r,group))
				for key,group in enumerate(groups):
					qty = map(lambda x:float(x.issue_pending_qty),group)[0]
					#~ qty = sum(map(lambda x:float(x.issue_pending_qty),group)) #TODO: qty
					depindent_line_ids = map(lambda x:x.id,group)
					prod_browse = group[0].product_id
					brand_id = group[0].brand_id.id				
					uom =False
					indent = group[0].service_id
					dep = indent.dep_name.id
					uom = group[0].uom.id or False
					serviceindent_obj = self.pool.get('kg.service.indent').browse(cr, uid, indent.id)
					dep_stock_location = serviceindent_obj.dep_name.stock_location.id
					#~ main_location = serviceindent_obj.dep_name.main_location.id
					main_location = obj.location_id.id
					
					vals = {
					
						'product_id':prod_browse.id,
						'brand_id':brand_id,
						'uom_id':uom,
						'issue_qty':qty,
						'issue_qty_2':qty,
						'indent_qty':qty,
						'name':prod_browse.name,
						'location_id':main_location,
						'location_dest_id':dep_stock_location,
						'state' : 'confirmed',
						'service_indent_line_id' : group[0].id,
						'issue_type':'service'
						}
					if ids:
						self.write(cr,uid,ids[0],{'issue_line_ids':[(0,0,vals)]})
			self.write(cr,uid,ids,res)
		return True
	
	def entry_confirm(self, cr, uid, ids, context=None):
		obj_rec = self.browse(cr, uid, ids[0])
		if obj_rec.state == 'confirmed':	
			lot_obj = self.pool.get('stock.production.lot')
			product_obj = self.pool.get('product.product')
			dep_issue_line_obj = self.pool.get('kg.department.issue.line')
			
			if not obj_rec.name:
				seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.department.issue')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,obj_rec.issue_date))
				seq_name = cr.fetchone();
				issue_name = seq_name[0]
				obj_rec.write({'name': issue_name})
			
			obj_rec.write({'state': 'approve','confirmed_by':uid,'confirmed_date':time.strftime('%Y-%m-%d %H:%M:%S')})
			
			if not obj_rec.issue_line_ids:
				raise osv.except_osv(_('Item Line Empty!'),_('You cannot process Issue without Item Line.'))
			else:
				for item in obj_rec.issue_line_ids:
					if item.issue_qty > 0:
						self.pool.get('kg.department.issue.line').write(cr,uid,item.id,{'state':'confirmed'})
					dep_issue_line_rec = dep_issue_line_obj.browse(cr, uid, item.id)
					product_id = dep_issue_line_rec.product_id.id
					product_uom = dep_issue_line_rec.uom_id.id
					product_record = product_obj.browse(cr, uid,product_id)
					lot_sql = """ select lot_id from kg_department_issue_details where grn_id=%s""" %(item.id)
					cr.execute(lot_sql)
					lot_data = cr.dictfetchall()
					print"lot_datalot_data",lot_data
					if not lot_data:
						raise osv.except_osv(_('No GRN Entry!'), _('There is no GRN reference for this Issue. You must associate GRN entries %s !!' %(item.product_id.name)))
					else:
						#~ if item.wo_state == 'accept':
						if item.issue_qty > 0:
							val = [d['lot_id'] for d in lot_data if 'lot_id' in d]
							#### Need to check UOM then will write price #####
							stock_tot = 0.0
							po_tot = 0.0
							lot_browse = lot_obj.browse(cr, uid,val[0])
							grn_id = lot_browse.grn_move
							cutting_qty = 0
							if obj_rec.department_id.name == 'DP2':
								if item.indent_line_id:
									if item.indent_line_id.qty == item.indent_line_id.cutting_qty:
										cutting_qty = item.issue_qty
									elif item.indent_line_id.qty != item.indent_line_id.cutting_qty:
										cutting_qty = item.indent_qty / (item.indent_line_id.qty/item.indent_line_id.cutting_qty)
									else:
										cutting_qty = 0
							dep_issue_line_rec.write({'price_unit': lot_browse.price_unit or 0.0,'confirm_qty':dep_issue_line_rec.issue_qty,'cutting_qty': cutting_qty})
							tot = 0
							for i in val:
								lot_rec = lot_obj.browse(cr, uid, i)
								stock_tot += lot_rec.reserved_qty
								po_tot += lot_rec.po_qty
								uom = lot_rec.product_uom.name
								tot += lot_rec.pending_qty
							
							## Lot qty check
							#~ if obj_rec.department_id.name != 'DP2':
								#~ sql = """ select
											#~ 
											#~ sum(lot.pending_qty) - (select sum(line.issue_qty) from kg_department_issue issue 
											#~ left join kg_department_issue_line line on(line.issue_id=issue.id) where issue.id = %s and line.product_id = %s and line.brand_id = %s) as qty,
											#~ prod.name_template as product
											#~ 
											#~ from
											#~ 
											#~ stock_production_lot lot
											#~ left join product_product prod on(prod.id=lot.product_id)
											#~ where lot.id in (select lot_id from kg_department_issue_details where grn_id = %s and lot.product_id = %s and lot.brand_id = %s)
											#~ group by 2
											#~ """ %(obj_rec.id,dep_issue_line_rec.product_id.id,dep_issue_line_rec.brand_id.id,dep_issue_line_rec.id,dep_issue_line_rec.product_id.id,dep_issue_line_rec.brand_id.id)
								#~ cr.execute(sql)
								#~ lot_datas = cr.dictfetchall()
								#~ print"dep_issue_line_rec",dep_issue_line_rec.id
								#~ print"obj_recobj_rec",obj_rec.id
								#~ print"lot_datas",lot_datas,lot_datas[0]['qty']
								#~ if lot_datas:
									#~ if lot_datas[0]['qty'] < 0:
										#~ raise osv.except_osv(_('Stock not available!'),
											#~ _('Associated GRN have less Qty compare to issue Qty for Product %s.'%(lot_datas[0]['product'])))
							#~ if obj_rec.department_id.name == 'DP2':
								#~ sql = """ select
											#~ 
											#~ sum(lot.pending_qty) - (select sum(line.issue_qty * line.length) from kg_department_issue issue 
											#~ left join kg_department_issue_line line on(line.issue_id=issue.id) where issue.id = %s and line.product_id = %s and line.brand_id = %s) as qty,
											#~ prod.name_template as product
											#~ 
											#~ from
											#~ 
											#~ stock_production_lot lot
											#~ left join product_product prod on(prod.id=lot.product_id)
											#~ where lot.id in (select lot_id from kg_department_issue_details where grn_id = %s and lot.product_id = %s and lot.brand_id = %s)
											#~ group by 2
											#~ """ %(obj_rec.id,dep_issue_line_rec.product_id.id,dep_issue_line_rec.brand_id.id,dep_issue_line_rec.id,dep_issue_line_rec.product_id.id,dep_issue_line_rec.brand_id.id)
								#~ cr.execute(sql)
								#~ lot_datas = cr.dictfetchall()
								#~ print"dep_issue_line_rec",dep_issue_line_rec.id
								#~ print"obj_recobj_rec",obj_rec.id
								#~ if lot_datas:
									#~ if lot_datas[0]['qty'] < 0:
										#~ raise osv.except_osv(_('Stock not available!'),
											#~ _('Associated GRN have less Qty compare to issue Qty for Product %s.'%(lot_datas[0]['product'])))
							if obj_rec.department_id.name != 'DP2':
								if dep_issue_line_rec.uom_conversation_factor == 'one_dimension':
									if dep_issue_line_rec.uom_id.id == lot_rec.po_uom.id:
										crnt_qty = dep_issue_line_rec.issue_qty
									elif dep_issue_line_rec.uom_id.id == lot_rec.product_uom.id:
										crnt_qty = dep_issue_line_rec.issue_qty / dep_issue_line_rec.product_id.po_uom_coeff
								elif dep_issue_line_rec.uom_conversation_factor == 'two_dimension':
									if dep_issue_line_rec.uom_id.id == lot_rec.po_uom.id:
										crnt_qty = dep_issue_line_rec.issue_qty
									elif dep_issue_line_rec.uom_id.id == lot_rec.product_uom.id:
										crnt_qty = dep_issue_line_rec.issue_qty / dep_issue_line_rec.product_id.po_uom_in_kgs / dep_issue_line_rec.length / dep_issue_line_rec.breadth
								print"tottot",tot
								print"crnt_qty",crnt_qty
								if tot < crnt_qty:
									raise osv.except_osv(_('Stock not available!'),
										_('Associated GRN have less Qty compare to issue Qty for Product %s.'%(item.product_id.name)))
							
							## Reserved Qty update process starts
							sql = """ select lot_id from kg_department_issue_details where grn_id=%s""" %(item.id)
							cr.execute(sql)
							data = cr.dictfetchall()
							if data:
								val = [d['lot_id'] for d in data if 'lot_id' in d]
								issue_qty = item.issue_qty
								remain_qty = 0
								for i in val:
									lot_rec = lot_obj.browse(cr,uid,i)
									move_qty = issue_qty
									if move_qty > 0 and move_qty <= lot_rec.reserved_qty:
										lot_reserved_qty = lot_rec.reserved_qty - move_qty
										lot_rec.write({'reserved_qty': lot_reserved_qty})
									else:
										if move_qty > 0:
											lot_reserved_qty = lot_rec.reserved_qty
											remain_qty =  move_qty - lot_reserved_qty
											if remain_qty >= 0:
												lot_rec.write({'reserved_qty': 0.0})
											else:
												pass
										else:
											pass
									issue_qty = remain_qty
							## Reserved Qty update process ends
							
							else:
								pass
					if dep_issue_line_rec.issue_qty == 0:
						raise osv.except_osv(_('Item Line Qty can not Zero!'),
							_('You cannot process Issue with Item Line Qty Zero for Product %s.' %(dep_issue_line_rec.product_id.name)))
		return True
	
	def action_process(self, cr, uid, ids, context=None):
		issue_record = self.browse(cr,uid,ids[0])
		if issue_record.state == 'approve':
			line_id = []
			for item in issue_record.issue_line_ids:
				line_id.append(item.id)
			issue_line_ids = line_id
			if issue_line_ids:
				self.issue_item_approval(cr,uid,issue_line_ids)
			line_sql = """ select line.issue_qty,line.id from kg_department_issue_line line 
						left join kg_department_issue issue on(issue.id=line.issue_id)
						where line.issue_id = %s and issue.state = 'approve' """ %(issue_record.id)
			cr.execute(line_sql)
			line_data = cr.dictfetchall()
			if line_data:
				if len(line_data) == 1:
					self.write(cr,uid,issue_record.id,{'state': 'done','approved_by':uid,'approved_date':time.strftime('%Y-%m-%d %H:%M:%S')})
				elif len(line_data) > 1:
					approve_line_sql = """ select line.issue_qty from kg_department_issue_line line 
								where line.issue_id = %s and issue_qty >= 0 and state = 'confirmed' """ %(issue_record.id)
					cr.execute(approve_line_sql)
					approve_line_data = cr.dictfetchall()
					if not approve_line_data:
						self.write(cr,uid,issue_record.id,{'state': 'done','approved_by':uid,'approved_date':time.strftime('%Y-%m-%d %H:%M:%S')})
				else:
					pass
			else:
				pass
			self.write(cr,uid,issue_record.id,{'state': 'done','approved_by':uid,'approved_date':time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
	def issue_item_approval(self,cr,uid,issue_line_ids,context=None):
		print"issue_line_idsissue_line_ids***********",issue_line_ids
		stock_move_obj=self.pool.get('stock.move')
		product_obj = self.pool.get('product.product')
		po_obj = self.pool.get('purchase.order')
		lot_obj = self.pool.get('stock.production.lot')
		item_issue_obj = self.pool.get('kg.item.wise.dept.issue')
		
		#### Updating Department Issue to Stock Move ####			
		for line_ids in issue_line_ids:
			print"line_idsline_ids",line_ids
			line_rec = self.pool.get('kg.department.issue.line').browse(cr,uid,line_ids)
			print"line_recline_rec",line_rec
			issue_record = line_rec.issue_id
			line_ids = line_rec
			print"issue_recordissue_recordissue_record",issue_record
			
		#### Updating Department Issue to Stock Move ####			
		#~ for line_ids in issue_record.issue_line_ids:
			if issue_record.issue_type == 'material':
				if issue_record.dep_issue_type == 'from_indent':
					indent_id = line_ids.indent_line_id.indent_id.id
					depindent_obj = self.pool.get('kg.depindent').browse(cr, uid, indent_id)
					dep_stock_location = depindent_obj.dest_location_id.id
					#~ main_location = depindent_obj.src_location_id.id
					main_location = issue_record.location_id.id
				else:
					stock_main_store = self.pool.get('stock.location').search(cr,uid,[('custom','=',True),('location_type','=','main')])
					main_location = stock_main_store[0]
					dep_stock_location = issue_record.department_id.stock_location.id
					
			if issue_record.issue_type == 'service':
				if issue_record.dep_issue_type == 'from_indent':
					indent_id = line_ids.service_indent_line_id.service_id.id
					depindent_obj = self.pool.get('kg.service.indent').browse(cr, uid, indent_id)
					dep_stock_location = depindent_obj.dep_name.stock_location.id
					#~ main_location = depindent_obj.dep_name.main_location.id
					main_location = issue_record.location_id.id
				else:
					stock_main_store = self.pool.get('stock.location').search(cr,uid,[('custom','=',True),('location_type','=','main')])
					main_location = stock_main_store[0]
					dep_stock_location = issue_record.department_id.stock_location.id
					
			if line_ids.issue_qty > line_ids.issue_qty_2:
				raise osv.except_osv(_('Warning!'),
					_('%s Qty is exceeding store issue qty'%(line_ids.product_id.name)))
			print"line_ids.wo_stateline_ids.wo_state",line_ids.wo_state
			
			#~ if line_ids.wo_state == 'accept':
			if line_ids.issue_qty > 0:
				
				if issue_record.dep_issue_type == 'from_indent':
					self.pool.get('kg.department.issue.line').write(cr,uid,line_ids.id,{'state':'done'})
					if line_ids.w_order_line_id:
						## MS store inward process
						if line_ids.issue_id.department_id.name == 'DP2':
							ms_obj = self.pool.get('kg.machineshop').search(cr,uid,[('order_line_id','=',line_ids.w_order_line_id.id),('ms_id','=',line_ids.ms_bot_id.id),('state','=','raw_pending')])
							if ms_obj:
								ms_rec = self.pool.get('kg.machineshop').browse(cr,uid,ms_obj[0])
								self.pool.get('kg.machineshop').write(cr,uid,ms_rec.id,{'state':'accept','ms_plan_rem_qty':line_ids.cutting_qty})
							cr.execute(""" update kg_ms_operations set reject_state = 'issued' where id in (
								select id from kg_ms_operations where state = 'reject' 
								and order_line_id = %s and reject_state = 'not_issued' and ms_type = 'ms_item'
								and item_code = '%s' and moc_id = %s limit 1) """%(line_ids.w_order_line_id.id,line_ids.ms_bot_id.code,line_ids.wo_moc_id.id))
						
						## BOT store inward process
						if line_ids.issue_id.department_id.name == 'DP3':
							ms_obj = self.pool.get('kg.ms.stores').search(cr,uid,[('order_line_id','=',line_ids.w_order_line_id.id),('item_code','=',line_ids.ms_bot_id.code),('moc_id','=',line_ids.wo_moc_id.id),
																				('accept_state','=','pending'),('ms_type','=','bot_item')])
							if ms_obj:
								ms_rec = self.pool.get('kg.ms.stores').browse(cr,uid,ms_obj[0])
								self.pool.get('kg.ms.stores').write(cr,uid,ms_rec.id,{'accept_state':'waiting'})
				length = 1
				breadth = 1
				if line_ids.uom_conversation_factor == 'one_dimension':
					if line_ids.issue_id.department_id.name == 'DP2':
						product_qty = line_ids.issue_qty * line_ids.length * line_ids.product_id.po_uom_coeff
					else:
						if line_ids.uom_id.id == line_ids.product_id.uom_id.id:
							print"*************************"
							product_qty = line_ids.issue_qty
						elif line_ids.uom_id.id == line_ids.product_id.uom_po_id.id:
							print"--------------------------"
							po_coeff = line_ids.product_id.po_uom_coeff
							product_qty = line_ids.issue_qty * po_coeff
				elif line_ids.uom_conversation_factor == 'two_dimension':
					if line_ids.product_id.po_uom_in_kgs > 0:
						if line_ids.issue_id.department_id.name == 'DP2':
							product_qty = line_ids.issue_qty * line_ids.product_id.po_uom_in_kgs * line_ids.length * line_ids.breadth
						else:
							if line_ids.uom_id.id == line_ids.product_id.uom_id.id:
								product_qty = line_ids.issue_qty
							elif line_ids.uom_id.id == line_ids.product_id.uom_po_id.id:
								product_qty = line_ids.issue_qty * line_ids.product_id.po_uom_in_kgs * line_ids.length * line_ids.breadth
						length = line_ids.length
						breadth = line_ids.breadth
						
				print"product_qtyproduct_qty",product_qty
				
				stock_move_obj.create(cr,uid,
				{
				'dept_issue_id': issue_record.id,
				'dept_issue_line_id': line_ids.id,
				'product_id': line_ids.product_id.id,
				'brand_id': line_ids.brand_id.id,
				'moc_id': line_ids.wo_moc_id.id,
				'name': line_ids.product_id.name,
				'product_qty': product_qty,
				'po_to_stock_qty': product_qty,
				'stock_uom': line_ids.product_id.uom_id.id,
				'product_uom': line_ids.product_id.uom_po_id.id,
				#~ 'location_id': main_location,
				#~ 'location_dest_id': dep_stock_location,
				'location_id': line_ids.location_id.id,
				'location_dest_id': dep_stock_location,
				'move_type': 'out',
				'state': 'done',
				'price_unit': line_ids.price_unit or 0.0,
				'stock_rate': line_ids.price_unit or 0.0,
				'uom_conversation_factor': line_ids.uom_conversation_factor,
				'length': length,
				'breadth': breadth,
				
				})
				
				lot_sql = """ select lot_id from kg_department_issue_details where grn_id=%s""" %(line_ids.id)
				cr.execute(lot_sql)
				lot_data = cr.dictfetchall()
				if not lot_data:
					raise osv.except_osv(_('No GRN Entry!'), _('There is no GRN reference for this Issue. You must associate GRN entries %s !!' %(line_ids.product_id.name)))
				else:
					val = [d['lot_id'] for d in lot_data if 'lot_id' in d]
					tot = 0.0
					crnt_qty = 0.0
					for i in val:
						lot_rec = lot_obj.browse(cr, uid, i)
						tot += lot_rec.pending_qty
					if line_ids.uom_conversation_factor == 'one_dimension':
						if line_ids.uom_id.id == lot_rec.po_uom.id:
							crnt_qty = line_ids.issue_qty
						elif line_ids.uom_id.id == lot_rec.product_uom.id:
							crnt_qty = line_ids.issue_qty / line_ids.product_id.po_uom_coeff
					elif line_ids.uom_conversation_factor == 'two_dimension':
						if line_ids.uom_id.id == lot_rec.po_uom.id:
							crnt_qty = line_ids.issue_qty
						elif line_ids.uom_id.id == lot_rec.product_uom.id:
							crnt_qty = line_ids.issue_qty / line_ids.product_id.po_uom_in_kgs / line_ids.length / line_ids.breadth
					print"crnt_qtycrnt_qtycrnt_qty",crnt_qty
					print"tottot",tot
					if tot < crnt_qty:
						raise osv.except_osv(_('Stock not available !!'),
							_('Associated GRN have less Qty compare to issue Qty for Product %s.'%(line_ids.product_id.name)))
					### Updation Issue Pending Qty in Department Issue ###
					if issue_record.issue_type == 'material':
						dep_line_obj = self.pool.get('kg.depindent.line')   
						#~ self.write(cr, uid, ids, {'state': 'done'})
						cr.execute(""" select stock_picking_id from kg_department_indent_picking where kg_depline_id = %s """ %(issue_record.id))
						data = cr.dictfetchall()
						val = [d['stock_picking_id'] for d in data if 'stock_picking_id' in d] 
						product_id = line_ids.product_id.id
						product_obj = self.pool.get('product.product')
						product_record = product_obj.browse(cr, uid, product_id)
						list_line = dep_line_obj.search(cr,uid,[('id', 'in', val), ('product_id', '=', product_id)],context=context)
						issue_qty = line_ids.issue_qty
						for i in list_line:
							bro_record = dep_line_obj.browse(cr, uid,i)
							orig_depindent_qty = bro_record.qty
							issue_pending_qty = bro_record.issue_pending_qty
							issue_used_qty = issue_qty
							indent_uom = bro_record.uom.id
							move_uom = line_ids.uom_id.id
							if indent_uom != move_uom:
								if issue_used_qty <= issue_pending_qty:
									pending_depindent_qty = issue_pending_qty - (issue_used_qty / product_record.po_uom_coeff)
									if issue_record.department_id.name == 'DP2':
										if bro_record.qty == bro_record.cutting_qty:
											pending_depindent_qty = pending_depindent_qty
										elif bro_record.qty != bro_record.cutting_qty:
											pending_depindent_qty = issue_pending_qty - (((bro_record.qty/bro_record.cutting_qty) * issue_qty) * product_record.po_uom_coeff)
										else:
											pending_depindent_qty = pending_depindent_qty
									else:
										pending_depindent_qty =  0.0
										if line_ids.uom_conversation_factor == 'two_dimension':
											pending_depindent_qty = issue_pending_qty - (line_ids.issue_qty / line_ids.length / line_ids.breadth / line_ids.product_id.po_uom_in_kgs)
										elif line_ids.uom_conversation_factor == 'one_dimension':
											pending_depindent_qty = issue_pending_qty - (line_ids.issue_qty * product_id.po_uom_coeff)
									sql = """ update kg_depindent_line set issue_pending_qty=%s where id = %s"""%(pending_depindent_qty,bro_record.id)
									cr.execute(sql)
									break
								else:
									remain_qty = issue_used_qty - issue_pending_qty
									issue_qty = remain_qty
									pending_depindent_qty =  0.0
									sql = """ update kg_depindent_line set issue_pending_qty=%s where id = %s"""%(pending_depindent_qty,bro_record.id)
									cr.execute(sql)
									if remain_qty < 0:
										break
							else:
								if issue_used_qty <= issue_pending_qty:
									pending_depindent_qty =  issue_pending_qty - issue_used_qty
									if issue_record.department_id.name == 'DP2':
										if bro_record.qty == bro_record.cutting_qty:
											pending_depindent_qty = pending_depindent_qty
										elif bro_record.qty != bro_record.cutting_qty:
											pending_depindent_qty = issue_pending_qty - ((bro_record.qty/bro_record.cutting_qty) * issue_qty)
										else:
											pending_depindent_qty = pending_depindent_qty
									sql = """ update kg_depindent_line set issue_pending_qty=%s where id = %s"""%(pending_depindent_qty,bro_record.id)
									cr.execute(sql)
									break
								else:
									remain_qty = issue_used_qty - issue_pending_qty
									issue_qty = remain_qty
									pending_depindent_qty =  0.0
									sql = """ update kg_depindent_line set issue_pending_qty=%s where id = %s"""%(pending_depindent_qty,bro_record.id)
									cr.execute(sql)
									if remain_qty < 0:
										break
					
					if issue_record.issue_type == 'service':
						serviceind_line_obj = self.pool.get('kg.service.indent.line')   
						self.write(cr, uid, ids, {'state': 'done'})
						cr.execute(""" select service_issue from kg_service_indent_picking where kg_serviceline_id = %s """ %(issue_record.id))
						data = cr.dictfetchall()
						val = [d['service_issue'] for d in data if 'service_issue' in d] 
						product_id = line_ids.product_id.id
						product_obj = self.pool.get('product.product')
						product_record = product_obj.browse(cr, uid, product_id)
						list_line = serviceind_line_obj.search(cr,uid,[('id', 'in', val), ('product_id', '=', product_id)],context=context)
						issue_qty = line_ids.issue_qty
						for i in list_line:
							bro_record = serviceind_line_obj.browse(cr, uid,i)
							orig_depindent_qty = bro_record.qty
							issue_pending_qty = bro_record.issue_pending_qty
							issue_used_qty = issue_qty
							indent_uom = bro_record.uom.id
							move_uom = line_ids.uom_id.id
							if indent_uom != move_uom:
								if issue_used_qty <= issue_pending_qty:
									pending_depindent_qty = issue_pending_qty - (issue_used_qty * product_record.po_uom_coeff)
									sql = """ update kg_service_indent_line set issue_pending_qty=%s where id = %s"""%(pending_depindent_qty,bro_record.id)
									cr.execute(sql)
									break
								else:
									remain_qty = issue_used_qty - issue_pending_qty
									issue_qty = remain_qty
									pending_depindent_qty =  0.0
									sql = """ update kg_service_indent_line set issue_pending_qty=%s where id = %s"""%(pending_depindent_qty,bro_record.id)
									cr.execute(sql)
									if remain_qty < 0:
										break
							else:
								if issue_used_qty <= issue_pending_qty:
									pending_depindent_qty =  issue_pending_qty - issue_used_qty
									sql = """ update kg_service_indent_line set issue_pending_qty=%s where id = %s"""%(pending_depindent_qty,bro_record.id)
									cr.execute(sql)
									break
								else:
									remain_qty = issue_used_qty - issue_pending_qty
									issue_qty = remain_qty
									pending_depindent_qty =  0.0
									sql = """ update kg_service_indent_line set issue_pending_qty=%s where id = %s"""%(pending_depindent_qty,bro_record.id)
									cr.execute(sql)
									if remain_qty < 0:
										break
					# The below part will update production lot pending qty while issue stock to sub store #
					sql = """ select lot_id from kg_department_issue_details where grn_id=%s""" %(line_ids.id)
					cr.execute(sql)
					data = cr.dictfetchall()
					print"datadata",data
					
					if data:
						val = [d['lot_id'] for d in data if 'lot_id' in d]
						print"valvalvalvalval",val
						issue_qty = line_ids.issue_qty
						remain_qty = 0
						reserved_qty_in_po_uom = 0
						for i in val:
							print'aaaaaaaaaaaaaaaaaa'
							lot_rec = lot_obj.browse(cr,uid,i)
							#~ move_qty = issue_qty
							#~ print"move_qty",move_qty
							#~ print"lot_rec.pending_qty",lot_rec.pending_qty
							#~ if move_qty > 0 and move_qty <= lot_rec.pending_qty:
							#~ lot_pending_qty = lot_rec.pending_qty - move_qty
							print"lot_reclot_rec",lot_rec.id
							if issue_record.department_id.name == 'DP2':
								lot_pending_qty = lot_rec.pending_qty - (line_ids.issue_qty * line_ids.length)
								store_pending_qty = lot_rec.store_pending_qty - ((line_ids.issue_qty * line_ids.length)*line_ids.product_id.po_uom_coeff)
							else:
								if line_ids.uom_conversation_factor == 'one_dimension':
									if line_ids.uom_id.id == line_ids.product_id.uom_po_id.id:
										print"///////////////////"
										lot_pending_qty = lot_rec.pending_qty - line_ids.issue_qty
										store_pending_qty = lot_rec.store_pending_qty - (line_ids.issue_qty*line_ids.product_id.po_uom_coeff)
									elif line_ids.uom_id.id == line_ids.product_id.uom_id.id:
										print"*-************************"
										store_pending_qty = lot_rec.store_pending_qty - line_ids.issue_qty
										lot_pending_qty = lot_rec.pending_qty - (line_ids.issue_qty / line_ids.product_id.po_uom_coeff)
									else:
										store_pending_qty = 0
								elif line_ids.uom_conversation_factor == 'two_dimension':
									print"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaA"
									if line_ids.product_id.po_uom_in_kgs > 0:
										if line_ids.uom_id.id == line_ids.product_id.uom_id.id:
											store_pending_qty = lot_rec.store_pending_qty - line_ids.issue_qty
											lot_pending_qty = lot_rec.pending_qty - (line_ids.issue_qty / line_ids.product_id.po_uom_in_kgs / line_ids.length / line_ids.breadth)
										elif line_ids.uom_id.id == line_ids.product_id.uom_po_id.id:
											store_pending_qty = lot_rec.store_pending_qty - (line_ids.issue_qty * line_ids.product_id.po_uom_in_kgs * line_ids.length * line_ids.breadth)
											lot_pending_qty = lot_rec.pending_qty - line_ids.issue_qty
								
								print"lot_pending_qtylot_pending_qty",lot_pending_qty
								print"store_pending_qtystore_pending_qty",store_pending_qty
								lot_rec.write({'pending_qty': lot_pending_qty,'store_pending_qty':store_pending_qty,'issue_qty': 0.0})
								#### wrting data into kg_issue_details ###
								lot_issue_qty = lot_rec.pending_qty - lot_pending_qty
								if lot_issue_qty == 0:
									issue_qty = lot_rec.pending_qty
								elif lot_issue_qty > 0:
									issue_qty = lot_issue_qty
								item_issue_obj.create(cr,uid,
										{
										'issue_line_id':line_ids.id,
										'product_id':line_ids.product_id.id,
										'uom_id':line_ids.uom_id.id,
										'grn_qty':lot_rec.pending_qty,
										'issue_qty':issue_qty,
										'price_unit':lot_rec.price_unit,
										'expiry_date':lot_rec.expiry_date,
										'batch_no':lot_rec.batch_no,
										'lot_id':lot_rec.id,
										})
								##### Ends Here ###
								#~ break
							#~ else:
								#~ if move_qty > 0:								
									#~ lot_pending_qty = lot_rec.pending_qty
									#~ remain_qty =  move_qty - lot_pending_qty
									#~ print'remain_qty',remain_qty
									#~ if issue_record.department_id.name == 'DP2':
										#~ reserved_qty_in_po_uom = lot_rec.reserved_qty_in_po_uom - (line_ids.issue_qty * line_ids.length)
									#~ else:
										#~ reserved_qty_in_po_uom = lot_rec.reserved_qty_in_po_uom - line_ids.issue_qty
									#~ lot_rec.write({'pending_qty': 0.0,'reserved_qty': 0.0})
									#~ #### wrting data into kg_issue_details ###
									#~ lot_issue_qty = lot_rec.pending_qty - lot_pending_qty
									#~ if lot_issue_qty == 0:
										#~ issue_qty = lot_rec.pending_qty
									#~ elif lot_issue_qty > 0:
										#~ issue_qty = lot_issue_qty
									#~ issue_name = 'OUT'
									#~ item_issue_obj.create(cr,uid,
										#~ {
										#~ 'issue_line_id':line_ids.id,
										#~ 'product_id':line_ids.product_id.id,
										#~ 'uom_id':line_ids.uom_id.id,
										#~ 'grn_qty':lot_rec.pending_qty,
										#~ 'issue_qty':issue_qty,
										#~ 'price_unit':lot_rec.price_unit,
										#~ 'expiry_date':lot_rec.expiry_date,
										#~ 'batch_no':lot_rec.batch_no,
										#~ 'lot_id':lot_rec.id,
										#~ })
									#~ ##### Ends Here ###
								#~ elif move_qty == 0:
									#~ print"issue_record.confirm_qty",line_ids.confirm_qty
									#~ print"issue_record.issue_qty",line_ids.issue_qty
									#~ print"lot_rec.reserved_qty",lot_rec.reserved_qty
									#~ print":ffffffffffff",lot_rec.reserved_qty + (line_ids.confirm_qty - line_ids.issue_qty)
									#~ if issue_record.department_id.name == 'DP2':
										#~ reserved_qty_in_po_uom = lot_rec.reserved_qty_in_po_uom - (line_ids.issue_qty * line_ids.length)
									#~ else:
										#~ reserved_qty_in_po_uom = lot_rec.reserved_qty_in_po_uom - line_ids.issue_qty
									#~ lot_rec.write({'reserved_qty': lot_rec.reserved_qty + (line_ids.confirm_qty - line_ids.issue_qty)})
								#~ else:
									#~ pass
							#~ issue_qty = remain_qty
					else:
						pass
		
		return True
	
	def unlink(self, cr, uid, ids, context=None):
		unlink_ids = []
		rec = self.browse(cr, uid, ids[0])
		if rec.state == 'draft':
			unlink_ids.append(rec.id)
		else:
			raise osv.except_osv(_('Warning!'),_('System will delete draft entry only!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_department_issue()

class kg_department_issue_line(osv.osv):
	
	_name = "kg.department.issue.line"
	_description = "Department Issue Line"
	
	_columns = {
		
		## Basic Info
		
		#~ 'issue_date':fields.date('PO GRN Date'),
		'issue_id': fields.many2one('kg.department.issue','Issue No'),
		'name': fields.related('issue_id','name', type='char', string='Issue No'),
		'state': fields.selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),('done', 'Done'), ('cancel', 'Cancelled')], 'Status',readonly=True),
		'remarks': fields.text('Remarks'),
		
		## Module Requirement Fields
		
		'issue_date': fields.related('issue_id','issue_date', type='date', string='Issue Date',store=True),
		'product_id': fields.many2one('product.product','Product Name',required=True,domain="[('state','not in',('reject','cancel')),('purchase_ok','=',True)]"),
		'uom_id': fields.many2one('product.uom','UOM'),
		'issue_qty': fields.float('Issue Qty',required=True,readonly=False,states={'done':[('readonly',True)]}),
		'issue_qty_2': fields.float('Issue Qty 2',required=True),
		'cutting_qty': fields.float('Cutting Qty'),
		'indent_qty': fields.float('Indent Quantity'),
		'reject_qty': fields.float('Reject Qty'),
		'price_unit': fields.float('Unit Price'),
		'kg_discount_per': fields.float('Discount (%)', digits_compute= dp.get_precision('Discount')),
		'kg_discount': fields.float('Discount Amount'),
		'tax_id': fields.many2many('account.tax', 'department_issue_tax', 'issue_line_id', 'taxes_id', 'Taxes'),
		'location_id': fields.many2one('stock.location', 'Source Location'),
		'location_dest_id': fields.many2one('stock.location', 'Destination Location'),
		'indent_id': fields.many2one('kg.depindent','Department Indent'),
		'indent_line_id': fields.many2one('kg.depindent.line','Department Indent Line'),
		'service_indent_line_id': fields.many2one('kg.service.indent.line','Service Indent Line'),
		'issue_type': fields.selection([('material', 'Material'), ('service', 'Service')], 'Issue Type'),
		'dep_issue_type': fields.selection([('from_indent','From Indent'),('direct','Direct')], string='Issue Type'),
		'kg_grn_moves': fields.many2many('stock.production.lot','kg_department_issue_details','grn_id','lot_id', 'GRN Entry',
					domain="[('product_id','=',product_id),'&',('grn_type','=',issue_type),'&',('pending_qty','>',0),'&',('store_pending_qty','>',0),'&',('lot_type','!=','out'),'&',('moc_id','=',wo_moc_id),'&',('location_id','=',location_id)]",
					),
		#'kg_grn_moves': fields.many2many('stock.production.lot','kg_department_issue_details','grn_id','lot_id', 'GRN Entry'),
		'brand_id': fields.many2one('kg.brand.master','Brand Name',domain="[('product_ids','in',(product_id)),('state','in',('draft','confirmed','approved'))]"),
		'issue_return_line': fields.boolean('Excess Return Flag'),
		'excess_return_qty': fields.float('Excess Return Qty'),
		'damage_flag': fields.boolean('Damage Return Flag'),
		'return_qty': fields.float('Returned Qty'),
		'wo_state': fields.selection([('accept','Accept'),('reject','Reject')],'Status'),
		'ms_name': fields.char('MS Item Name'),
		'confirm_qty': fields.float('Confirmed Qty'),
		'w_order_line_id': fields.many2one('ch.work.order.details','WO No'),
		'ms_bot_id': fields.many2one('kg.machine.shop', 'MS Item Name'),
		'traceability_no': fields.char('Traceability No'),
		'wo_id': fields.related('w_order_line_id','header_id', type='many2one',relation='kg.work.order', string='WO No.',store=True),
		'wo_delivery_date': fields.related('wo_id','delivery_date', type='date', string='Delivery Date',store=True),
		'wo_pump_model_id': fields.related('w_order_line_id','pump_model_id', type='many2one',relation='kg.pumpmodel.master', string='Pump Model',store=True),
		#~ 'wo_moc_id': fields.related('indent_line_id','moc_id', type='many2one',relation='kg.moc.master', string='MOC',store=True),
		'wo_moc_id': fields.many2one('kg.moc.master','MOC'),
		'moc_id_temp': fields.many2one('ch.brandmoc.rate.details','MOC',domain="[('brand_id','=',brand_id),('header_id.product_id','=',product_id),('header_id.state','in',('draft','confirmed','approved'))]"),
		'wo_position_id': fields.related('indent_line_id','position_id', type='many2one',relation='kg.position.number', string='Position No.',store=True),
		'order_priority': fields.related('wo_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True),
		'accept_date': fields.date('Accepted Date'),
		'remark_id': fields.many2one('kg.rejection.master','Rejection Remarks'),
		#~ 'dep_id': fields.related('issue_id','department_id',relation='kg.depmaster',type='many2one',string='Department Name',store=True),
		#~ 'dep_code': fields.related('dep_id','name',type='char',string='Department Code',store=True),
		'dep_id': fields.many2one('kg.depmaster','Department Name'),
		'dep_code': fields.char('Department Code'),
		'length': fields.float('Length'),
		'breadth': fields.float('Breadth'),
		'uom_conversation_factor': fields.selection([('one_dimension','One Dimension'),('two_dimension','Two Dimension')],'UOM Conversation Factor'),
		
		## Child Tables Declaration
		
		'kg_itemwise_issue_line': fields.one2many('kg.item.wise.dept.issue','issue_line_id','Item wise Department Issue',readonly=True),
		
	}
	
	_defaults = {
		
		'state': 'draft',
		'wo_state': 'accept',
		'accept_date': lambda * a: time.strftime('%Y-%m-%d'),
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		print"contextcontextcontext",context
		if len(context)>7:
			if context['dep_id']:
				dep_rec = self.pool.get('kg.depmaster').browse(cr,uid,context['dep_id'])
				context['dep_code'] = dep_rec.name
			else:
				raise osv.except_osv(_('Warning!'),_('Without Department you cannot issue the items!!'))
		return context
	
	def onchange_product_id(self, cr, uid, ids, product_id,context=None):
		value = {'uom_id': '','uom_conversation_factor':''}
		if product_id:
			prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			value = {'uom_id': prod.uom_id.id,'uom_conversation_factor':prod.uom_conversation_factor}
		return {'value': value}
	
	def onchange_moc(self, cr, uid, ids, moc_id_temp):
		value = {'wo_moc_id':''}
		if moc_id_temp:
			rate_rec = self.pool.get('ch.brandmoc.rate.details').browse(cr,uid,moc_id_temp)
			value = {'wo_moc_id': rate_rec.moc_id.id}
		return {'value': value}
	
	def onchange_uom_id(self, cr, uid, ids, product_id,uom_id, context=None):
		value = {'uom_id': ''}
		if product_id and uom_id:
			pro_rec = self.pool.get('product.product').browse(cr,uid,product_id)
			if uom_id == pro_rec.uom_id.id or uom_id == pro_rec.uom_po_id.id:
				pass
			else:
				raise osv.except_osv(_('UOM Mismatching Error !'),
					_('You choosed wrong UOM and you can choose either %s or %s for %s !!') % (pro_rec.uom_id.name,pro_rec.uom_po_id.name,pro_rec.name))
			value = {'uom_id':uom_id}
		return {'value': value}
	
	def onchange_issue_qty_2(self, cr, uid, ids, issue_qty,context=None):
		value = {'issue_qty_2': 0}
		if issue_qty:
			value = {'issue_qty_2': issue_qty}
		return {'value': value}
	
	def onchange_reject_qty(self, cr, uid, ids,issue_qty_2,issue_qty,context=None):
		value = {'reject_qty': 0}
		if issue_qty_2 > issue_qty:
			value = {'reject_qty': issue_qty_2 - issue_qty}
		return {'value': value}
	
	def onchange_cutting_qty(self, cr, uid, ids,cutting_qty,indent_qty,indent_line_id,context=None):
		value = {'issue_qty': 0}
		qty = 0
		if indent_qty > 0 and indent_line_id:
			indent_rec = self.pool.get('kg.depindent.line').browse(cr,uid,indent_line_id)
			if indent_rec.cutting_qty == indent_rec.qty:
				qty = cutting_qty
			elif indent_rec.cutting_qty != indent_rec.qty:
				qty = (indent_rec.qty/indent_rec.cutting_qty) * cutting_qty
			value = {'issue_qty': qty}
		return {'value': value}
	
	def line_action_process(self, cr, uid, ids, context=None):
		issue_record = self.browse(cr,uid,ids[0])
		if issue_record.state == 'confirmed':
			issue_line_id = [issue_record.id]
			self.action_process(cr,uid,issue_line_id)	
		return True
	
	def action_process(self, cr, uid, issue_line_id, context=None):
		issue_record = self.browse(cr,uid,issue_line_id[0])
		#~ issue_record.write({'state': 'done','approved_by':uid,'approved_date':time.strftime('%Y-%m-%d %H:%M:%S')})
		if issue_record.state == 'confirmed':
			self.pool.get('kg.department.issue').issue_item_approval(cr,uid,issue_line_id)
			
			if issue_record.issue_qty > 0:
				self.write(cr,uid,issue_record.id,{'state':'done'})
				if issue_record.issue_id.department_id.name == 'DP2':
					ms_obj = self.pool.get('kg.machineshop').search(cr,uid,[('order_line_id','=',issue_record.w_order_line_id.id),('ms_id','=',issue_record.ms_bot_id.id),('state','=','raw_pending')])
					if ms_obj:
						ms_rec = self.pool.get('kg.machineshop').browse(cr,uid,ms_obj[0])
						self.pool.get('kg.machineshop').write(cr,uid,ms_rec.id,{'state':'accept'})
				
				
			line_sql = """ select line.issue_qty,line.id from kg_department_issue_line line 
							left join kg_department_issue issue on(issue.id=line.issue_id)
							where line.issue_id = %s and issue.state = 'approve' """ %(issue_record.issue_id.id)
			cr.execute(line_sql)
			line_data = cr.dictfetchall()
			if line_data:
				if len(line_data) == 1:
					self.pool.get('kg.department.issue').write(cr,uid,issue_record.issue_id.id,{'state': 'done','approved_by':uid,'approved_date':time.strftime('%Y-%m-%d %H:%M:%S')})
				elif len(line_data) > 1:
					approve_line_sql = """ select line.issue_qty from kg_department_issue_line line 
								where line.issue_id = %s and issue_qty >= 0 and state = 'confirmed' """ %(issue_record.issue_id.id)
					cr.execute(approve_line_sql)
					approve_line_data = cr.dictfetchall()
					if not approve_line_data:
						self.pool.get('kg.department.issue').write(cr,uid,issue_record.issue_id.id,{'state': 'done','approved_by':uid,'approved_date':time.strftime('%Y-%m-%d %H:%M:%S')})
				else:
					pass
			else:
				pass
		
		return True
	
	def update_lines(self, cr, uid, ids, context=None):
		
		dep_issue_obj = self.pool.get('kg.item.wise.dept.issue')
		obj = self.browse(cr, uid, ids[0])
		
		lot_sql = """ select grn_id,lot_id from kg_department_issue_details where grn_id=%s """ %(obj.id)
		cr.execute(lot_sql)
		lot_data = cr.dictfetchall()
		
		for item in lot_data:
			lot_rec = self.pool.get('stock.production.lot').browse(cr, uid, item['lot_id'])
			dep_issue_obj.create(cr, uid, {
					'issue_line_id': obj.id,
					'product_id': lot_rec.product_id.id,
					'uom_id': lot_rec.product_uom.id,
					'grn_qty':lot_rec.pending_qty,
					'price_unit': lot_rec.price_unit,
					'expiry_date':lot_rec.expiry_date,
					'batch_no': lot_rec.batch_no,
					'lot_id':lot_rec.id
					
				})
				
		return True
	
	#~ def unlink(self, cr, uid, ids, context=None):
		#~ unlink_ids = []
		#~ rec = self.browse(cr, uid, ids[0])
		#~ if grn_rec.issue_id.state == 'confirmed':
			#~ 
			#~ lot_sql = """ select lot_id from kg_department_issue_details where grn_id=%s""" %(rec.id)
			#~ cr.execute(lot_sql)
			#~ lot_data = cr.dictfetchall()
			#~ if not lot_data:
				#~ raise osv.except_osv(
				#~ _('No GRN Entry !!'),
				#~ _('There is no GRN reference for this Issue. You must associate GRN entries '))
			#~ else:
				#~ sql = """ select lot_id from kg_department_issue_details where grn_id=%s""" %(rec.id)
				#~ cr.execute(sql)
				#~ data = cr.dictfetchall()
				#~ if data:
					#~ val = [d['lot_id'] for d in data if 'lot_id' in d]
					#~ issue_qty = rec.issue_qty
					#~ for i in val:
						#~ lot_rec = lot_obj.browse(cr,uid,i)
						#~ lot_rec.write({'reserved_qty': lot_rec.reserved_qty + issue_qty})
					#~ unlink_ids.append(rec.id)
				#~ else:
					#~ pass
			#~ unlink_ids.append(rec.id)
		#~ 
		#~ return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
kg_department_issue_line()

class kg_item_wise_dept_issue(osv.osv):
	
	_name = "kg.item.wise.dept.issue"
	_description = "Item wise Department Issue"
	
	_columns = {
		
		## Basic Info
		
		'issue_line_id':fields.many2one('kg.department.issue.line','Department Issue Line Entry'),
		
		## Module Requirement Fields
		
		'product_id':fields.many2one('product.product','Product Name',required=True),
		'uom_id':fields.many2one('product.uom','UOM',readonly=True),
		'grn_qty':fields.integer('GRN Quantity',required=True),
		'issue_qty':fields.integer('Issue Quantity'),
		'price_unit':fields.float('Price Unit'),
		'expiry_date':fields.date('Expiry Date'),
		'batch_no':fields.char('Batch No',size=120),
		'issue_date':fields.date('Issue Date'),
		'lot_id':fields.many2one('stock.production.lot','Lot Id'),
		
	}
	
kg_item_wise_dept_issue()
