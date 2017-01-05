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
		
		'name': fields.char('Issue No.',readonly=True),
		'issue_date':fields.date('Issue Date',required=True,readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		'issue_line_ids':fields.one2many('kg.department.issue.line','issue_id','Line Entry',
						 readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		'kg_dep_indent_line':fields.many2many('kg.depindent.line', 'kg_department_indent_picking', 'kg_depline_id', 'stock_picking_id', 'Department Indent', 
				 domain="[('indent_id.state','=','approved'), '&', ('indent_id.main_store','=',False),'&', ('indent_id.dep_name','=',department_id),'&', ('issue_pending_qty','>','0'),'&', ('pi_cancel' ,'!=', 'True')]", 
				 readonly=True, states={'draft': [('readonly', False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		'outward_type': fields.many2one('kg.outwardmaster', 'Outward Type',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		'department_id': fields.many2one('kg.depmaster','Department',required=True,readonly=True, 
						 domain="[('item_request','=',True),('state','in',('draft','confirmed','approved'))]", states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		'state': fields.selection([('draft', 'Draft'),
			('confirmed', 'WFC'),
			('approve', 'WFA'),
			('done', 'Issued'),('cancel', 'Cancelled'),('reject', 'Rejected')], 'Status',readonly=True),
		
		'type': fields.selection([('in', 'IN'), ('out', 'OUT'), ('internal', 'Internal')], 'Type'),
		'confirm_flag':fields.boolean('Confirm Flag'),
		'approve_flag':fields.boolean('Expiry Flag'),
		'products_flag':fields.boolean('Products Flag'),
		'user_id' : fields.many2one('res.users', 'User', readonly=False),
		'remarks': fields.text('Remarks',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		'can_remark': fields.text('Cancel Remarks'),
		'reject_remark': fields.text('Reject Remarks'),
		'notes': fields.text('Notes'),
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
		
		# Entry Info
		
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
		
	_constraints = [
	
		(_issdate_validation, 'Issue Date should not be greater than current date !!',['issue_date']),
		
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
				move_obj.unlink(cr,uid,issue_lines)
			dep_rec = dep_obj.browse(cr, uid, obj.user_id.dep_name.id)
			issue_dep_id = obj.department_id.id
			
			obj.write({'state': 'confirmed'})
			obj.write({'products_flag': True})
			if obj.kg_dep_indent_line:
				depindent_line_ids = map(lambda x:x.id,obj.kg_dep_indent_line)
				depindent_line_browse = depindent_line_obj.browse(cr,uid,depindent_line_ids)
				depindent_line_browse = sorted(depindent_line_browse, key=lambda k: k.product_id.id)
				groups = []
				for key, group in groupby(depindent_line_browse, lambda x: x.product_id.id):
					groups.append(map(lambda r:r,group))
				for key,group in enumerate(groups):
					qty = sum(map(lambda x:float(x.issue_pending_qty),group)) #TODO: qty
					depindent_line_ids = map(lambda x:x.id,group)
					prod_browse = group[0].product_id
					ms_bot_id = group[0].ms_bot_id.id
					brand_id = group[0].brand_id.id				
					uom =False
					indent = group[0].indent_id
					dep = indent.dep_name.id
					uom = group[0].uom.id or False
					depindent_obj = self.pool.get('kg.depindent').browse(cr, uid, indent.id)
					dep_stock_location = depindent_obj.dest_location_id.id
					main_location = depindent_obj.src_location_id.id
										
					vals = {
					
						'indent_id':depindent_obj.id,
						'w_order_line_id':depindent_obj.order_line_id.id,
						'wo_id':depindent_obj.order_line_id.header_id.id,
						'ms_bot_id':ms_bot_id,
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
						'indent_line_id' : group[0].id,
						'issue_type':'material',
						'wo_state':'accept',
						'dep_issue_type':obj.dep_issue_type,
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
				for key, group in groupby(serviceindent_line_browse, lambda x: x.product_id.id):
					groups.append(map(lambda r:r,group))
				for key,group in enumerate(groups):
					qty = sum(map(lambda x:float(x.issue_pending_qty),group)) #TODO: qty
					depindent_line_ids = map(lambda x:x.id,group)
					prod_browse = group[0].product_id
					brand_id = group[0].brand_id.id				
					uom =False
					indent = group[0].service_id
					dep = indent.dep_name.id
					uom = group[0].uom.id or False
					serviceindent_obj = self.pool.get('kg.service.indent').browse(cr, uid, indent.id)
					dep_stock_location = serviceindent_obj.dep_name.stock_location.id
					main_location = serviceindent_obj.dep_name.main_location.id
										
					vals = {
					
						'product_id':prod_browse.id,
						'brand_id':brand_id,
						'uom_id':uom,
						'issue_qty':qty,
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
					if not lot_data:
						raise osv.except_osv(_('No GRN Entry !!'),_('There is no GRN reference for this Issue. You must associate GRN entries '))
					else:
						#~ if item.wo_state == 'accept':
						if item.issue_qty > 0:
							val = [d['lot_id'] for d in lot_data if 'lot_id' in d]
							#### Need to check UOM then will write price #####
							stock_tot = 0.0
							po_tot = 0.0
							lot_browse = lot_obj.browse(cr, uid,val[0])
							grn_id = lot_browse.grn_move
							dep_issue_line_rec.write({'price_unit': lot_browse.price_unit or 0.0,'confirm_qty':dep_issue_line_rec.issue_qty
										})											
							for i in val:
								lot_rec = lot_obj.browse(cr, uid, i)
								stock_tot += lot_rec.reserved_qty
								po_tot += lot_rec.po_qty
								uom = lot_rec.product_uom.name
							if stock_tot < dep_issue_line_rec.issue_qty:
								raise osv.except_osv(_('Stock not available !!'),
									_('Associated GRN have less Qty compare to issue Qty.'))
							
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
					main_location = depindent_obj.src_location_id.id
				else:
					stock_main_store = self.pool.get('stock.location').search(cr,uid,[('custom','=',True),('location_type','=','main')])
					main_location = stock_main_store[0]
					dep_stock_location = issue_record.department_id.stock_location.id
					
			if issue_record.issue_type == 'service':
				if issue_record.dep_issue_type == 'from_indent':
					indent_id = line_ids.service_indent_line_id.service_id.id
					depindent_obj = self.pool.get('kg.service.indent').browse(cr, uid, indent_id)
					dep_stock_location = depindent_obj.dep_name.stock_location.id
					main_location = depindent_obj.dep_name.main_location.id
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
				self.pool.get('kg.department.issue.line').write(cr,uid,line_ids.id,{'state':'done'})
				if line_ids.issue_id.department_id.name == 'DP2':
					ms_obj = self.pool.get('kg.machineshop').search(cr,uid,[('order_line_id','=',line_ids.w_order_line_id.id),('ms_id','=',line_ids.ms_bot_id.id),('state','=','raw_pending')])
					if ms_obj:
						ms_rec = self.pool.get('kg.machineshop').browse(cr,uid,ms_obj[0])
						self.pool.get('kg.machineshop').write(cr,uid,ms_rec.id,{'state':'accept'})
				
				
				stock_move_obj.create(cr,uid,
				{
				'dept_issue_id':issue_record.id,
				'dept_issue_line_id':line_ids.id,
				'product_id': line_ids.product_id.id,
				'brand_id':line_ids.brand_id.id,
				'name':line_ids.product_id.name,
				'product_qty': line_ids.issue_qty,
				'po_to_stock_qty':line_ids.issue_qty,
				'stock_uom':line_ids.uom_id.id,
				'product_uom': line_ids.uom_id.id,
				'location_id': main_location,
				'location_dest_id': dep_stock_location,
				'move_type': 'out',
				'state': 'done',
				'price_unit': line_ids.price_unit or 0.0,
				'stock_rate':line_ids.price_unit or 0.0,
				
				})
				
				lot_sql = """ select lot_id from kg_department_issue_details where grn_id=%s""" %(line_ids.id)
				cr.execute(lot_sql)
				lot_data = cr.dictfetchall()
				if not lot_data:
					raise osv.except_osv(_('No GRN Entry !!'),
						_('There is no GRN reference for this Issue. You must associate GRN entries '))
				else:
					val = [d['lot_id'] for d in lot_data if 'lot_id' in d]
					tot = 0.0
					for i in val:
						lot_rec = lot_obj.browse(cr, uid, i)
						tot += lot_rec.pending_qty
					if tot < line_ids.issue_qty:
						raise osv.except_osv(_('Stock not available !!'),
							_('Associated GRN have less Qty compare to issue Qty.'))
					else:
						pass
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
									pending_depindent_qty = issue_pending_qty - (issue_used_qty * product_record.po_uom_coeff)
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
					if data:
						val = [d['lot_id'] for d in data if 'lot_id' in d]
						print"valvalvalvalval",val
						issue_qty = line_ids.issue_qty
						remain_qty = 0
						for i in val:
							print'aaaaaaaaaaaaaaaaaa'
							lot_rec = lot_obj.browse(cr,uid,i)
							move_qty = issue_qty
							print"move_qty",move_qty
							print"lot_rec.pending_qty",lot_rec.pending_qty
							if move_qty > 0 and move_qty <= lot_rec.pending_qty:
								lot_pending_qty = lot_rec.pending_qty - move_qty
								
								print"lot_pending_qty",lot_pending_qty
								print"lot_reclot_rec",lot_rec.id
								lot_rec.write({'pending_qty': lot_pending_qty,'issue_qty': 0.0,'reserved_qty': lot_pending_qty})
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
							else:
								if move_qty > 0:								
									lot_pending_qty = lot_rec.pending_qty
									remain_qty =  move_qty - lot_pending_qty
									
									print'remain_qty',remain_qty
									lot_rec.write({'pending_qty': 0.0,'reserved_qty': 0.0})
									#### wrting data into kg_issue_details ###
									lot_issue_qty = lot_rec.pending_qty - lot_pending_qty
									if lot_issue_qty == 0:
										issue_qty = lot_rec.pending_qty
									elif lot_issue_qty > 0:
										issue_qty = lot_issue_qty
									issue_name = 'OUT'
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
								elif move_qty == 0:
									print"issue_record.confirm_qty",line_ids.confirm_qty
									print"issue_record.issue_qty",line_ids.issue_qty
									print"lot_rec.reserved_qty",lot_rec.reserved_qty
									print":ffffffffffff",lot_rec.reserved_qty + (line_ids.confirm_qty - line_ids.issue_qty)
									lot_rec.write({'reserved_qty': lot_rec.reserved_qty + (line_ids.confirm_qty - line_ids.issue_qty)})
								else:
									pass
							issue_qty = remain_qty
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
		'issue_id':fields.many2one('kg.department.issue','Issue No'),
		'name': fields.related('issue_id','name', type='char', string='Issue No'),
		'state': fields.selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),('done', 'Done'), ('cancel', 'Cancelled')], 'Status',readonly=True),
		'remarks': fields.text('Remarks'),
		
		## Module Requirement Fields
		
		'issue_date': fields.related('issue_id','issue_date', type='date', string='Issue Date',store=True),
		'product_id':fields.many2one('product.product','Product Name',required=True,domain="[('state','not in',('reject','cancel')),('purchase_ok','=',True)]"),
		'uom_id':fields.many2one('product.uom','UOM',readonly=True),
		'issue_qty':fields.float('Issue Qty',required=True,readonly=False,states={'done':[('readonly',True)]}),
		'issue_qty_2':fields.float('Issue Qty 2',required=True),
		'indent_qty':fields.float('Indent Quantity'),
		'price_unit':fields.float('Unit Price'),
		'kg_discount_per': fields.float('Discount (%)', digits_compute= dp.get_precision('Discount')),
		'kg_discount': fields.float('Discount Amount'),
		'tax_id': fields.many2many('account.tax', 'department_issue_tax', 'issue_line_id', 'taxes_id', 'Taxes'),
		'location_id': fields.many2one('stock.location', 'Source Location'),
		'location_dest_id': fields.many2one('stock.location', 'Destination Location'),
		'indent_id':fields.many2one('kg.depindent','Department Indent'),
		'indent_line_id':fields.many2one('kg.depindent.line','Department Indent Line'),
		'service_indent_line_id':fields.many2one('kg.service.indent.line','Service Indent Line'),
		'issue_type': fields.selection([('material', 'Material'), ('service', 'Service')], 'Issue Type'),
		'dep_issue_type':fields.selection([('from_indent','From Indent'),('direct','Direct')], string='Issue Type'),
		'kg_grn_moves': fields.many2many('stock.production.lot','kg_department_issue_details','grn_id','lot_id', 'GRN Entry',
					domain="[('product_id','=',product_id),'&',('grn_type','=',issue_type),'&', ('reserved_qty','>',0), '&', ('lot_type','!=','out')]",
					),
		#'kg_grn_moves': fields.many2many('stock.production.lot','kg_department_issue_details','grn_id','lot_id', 'GRN Entry'),
		'brand_id':fields.many2one('kg.brand.master','Brand Name',domain="[('product_ids','in',(product_id)),('state','in',('draft','confirmed','approved'))]"),
		'issue_return_line':fields.boolean('Excess Return Flag'),
		'excess_return_qty':fields.float('Excess Return Qty'),
		'damage_flag':fields.boolean('Damage Return Flag'),
		'return_qty':fields.float('Returned Qty'),
		'wo_state': fields.selection([('accept','Accept'),('reject','Reject')],'Status'),
		'ms_name': fields.char('MS Item Name'),
		'confirm_qty': fields.float('Confirmed Qty'),
		'w_order_line_id': fields.many2one('ch.work.order.details','WO No'),
		'ms_bot_id': fields.many2one('kg.machine.shop', 'MS Item Name'),
		'traceability_no': fields.char('Traceability No'),
		'wo_id': fields.related('w_order_line_id','header_id', type='many2one',relation='kg.work.order', string='WO No.',store=True),
		'wo_delivery_date': fields.related('wo_id','delivery_date', type='date', string='Delivery Date',store=True),
		'wo_pump_model_id': fields.related('w_order_line_id','pump_model_id', type='many2one',relation='kg.pumpmodel.master', string='Pump Model',store=True),
		'wo_moc_id': fields.related('indent_line_id','moc_id', type='many2one',relation='kg.moc.master', string='MOC',store=True),
		'wo_position_id': fields.related('indent_line_id','position_id', type='many2one',relation='kg.position.number', string='Position No.',store=True),
		'order_priority': fields.related('wo_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True),
		
		## Child Tables Declaration
		
		'kg_itemwise_issue_line':fields.one2many('kg.item.wise.dept.issue','issue_line_id','Item wise Department Issue',readonly=True),
		
	}
	
	_defaults = {
	
		'state': 'draft',
		'wo_state': 'accept',
		
	}

	def default_get(self, cr, uid, fields, context=None):
		print"contextcontextcontext",context
		
		return context
		
	def onchange_product_id(self, cr, uid, ids, product_id,context=None):
		value = {'uom_id': ''}
		if product_id:
			prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			value = {'uom_id': prod.uom_id.id}
		return {'value': value}
	
	def onchange_issue_qty_2(self, cr, uid, ids, issue_qty,context=None):
		value = {'issue_qty_2': 0}
		if issue_qty:
			value = {'issue_qty_2': issue_qty}
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
