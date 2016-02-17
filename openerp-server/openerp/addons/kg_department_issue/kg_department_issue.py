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

class kg_department_issue(osv.osv):

	_name = "kg.department.issue"
	_description = "Department Issue"
	_order = "issue_date desc"

			
	_columns = {
		
		'created_by':fields.many2one('res.users','Created By',readonly=True),
		'creation_date':fields.datetime('Creation Date',required=True,readonly=True),
		
		'confirmed_by':fields.many2one('res.users','Confirmed By',readonly=True),
		'confirmed_date':fields.datetime('Confirmed Date',required=True,readonly=True),
		
		'approved_by':fields.many2one('res.users','Approved By',readonly=True),
		'approved_date':fields.datetime('Approved Date',required=True,readonly=True),
		
		'name': fields.char('Issue NO',readonly=True),
		'issue_date':fields.date('Issue Date',required=True,readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		
		'issue_line_ids':fields.one2many('kg.department.issue.line','issue_id','Line Entry',
						 readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		
		'kg_dep_indent_line':fields.many2many('kg.depindent.line', 'kg_department_indent_picking', 'kg_depline_id', 'stock_picking_id', 'Department Indent', 
				 domain="[('indent_id.state','=','approved'), '&', ('indent_id.main_store','=',False),'&', ('indent_id.dep_name','=',department_id),'&', ('issue_pending_qty','>','0'),'&', ('pi_cancel' ,'!=', 'True')]", 
				  readonly=True, states={'draft': [('readonly', False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),

		'outward_type': fields.many2one('kg.outwardmaster', 'Outward Type',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		
		'department_id': fields.many2one('kg.depmaster','Department',required=True,readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		
		'state': fields.selection([('draft', 'Draft'),
			('confirmed', 'Waiting for Confirmation'),
			('approve', 'Waiting for Approval'),
			('done', 'Issued'),('cancel', 'Cancelled')], 'Status',readonly=True),
		
		'type': fields.selection([('in', 'IN'), ('out', 'OUT'), ('internal', 'Internal')], 'Type'),
		
		'active':fields.boolean('Active'),
		
		'company_id':fields.many2one('res.company','Company'),
		
		'confirm_flag':fields.boolean('Confirm Flag'),
		'approve_flag':fields.boolean('Expiry Flag'),
		'products_flag':fields.boolean('Products Flag'),
		'user_id' : fields.many2one('res.users', 'User', readonly=False),
		'remarks': fields.text('Remarks',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		'project':fields.char('Project',size=100,readonly=True,states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		'building':fields.char('Building',size=100,readonly=True,states={'draft':[('readonly',False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
		'issue_type': fields.selection([('material', 'Material'), ('service', 'Service')], 'Issue Type'),
		
		'kg_service_indent_line':fields.many2many('kg.service.indent.line', 'kg_service_indent_picking', 'kg_serviceline_id', 'service_issue', 'Service Indent', 
				 domain="[('service_id.state','=','approved'),'&', ('service_id.dep_name','=',department_id),'&', ('issue_pending_qty','>','0')]", 
				  readonly=True, states={'draft': [('readonly', False)],'confirmed':[('readonly',False)],'approve':[('readonly',False)]}),
	
		#'save_flag':fields.boolean('Save Flag'),
		'issue_return':fields.boolean('Issue Return'),
	
	
	
	}
	
	_defaults = {
		
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'confirmed_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'approved_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'issue_date': fields.date.context_today,
		'created_by': lambda obj, cr, uid, context: uid,
		'state':'draft',
		'type':'out',
		'name':'',
		'active':True,
		'confirm_flag':False,
		'approve_flag':False,
		#'save_flag':False,
		'issue_return':False,
		'company_id' : lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.department.issue', context=c),
		'user_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
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
			if mail_form_rec.doc_name.model == 'kg.department.issue':
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
	
	def sechedular_email_ids(self,cr,uid,ids,context = None):
		email_from = []
		email_to = []
		email_cc = []
		val = {'email_from':'','email_to':'','email_cc':''}
		ir_model = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		mail_form_ids = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		for ids in mail_form_ids:
			mail_form_rec = self.pool.get('kg.mail.settings').browse(cr,uid,ids)
			if mail_form_rec.sch_type == 'scheduler':
				s = mail_form_rec.sch_name
				s = s.lower()
				if s == 'issue register':
					email_sub = mail_form_rec.subject
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
		depindent_line_obj = self.pool.get('kg.depindent.line')
		issue_line_obj = self.pool.get('kg.department.issue.line')
		move_obj = self.pool.get('stock.move')
		prod_obj = self.pool.get('product.product')
		dep_obj = self.pool.get('kg.depmaster')
		line_ids = []			   
		res={}
		line_ids = []
		res['move_lines'] = []
		obj =  self.browse(cr,uid,ids[0])
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
				brand_id = group[0].brand_id.id				
				uom =False
				
				indent = group[0].indent_id
				
				dep = indent.dep_name.id
				
						
				uom = group[0].uom.id or False
				
				depindent_obj = self.pool.get('kg.depindent').browse(cr, uid, indent.id)
				dep_stock_location = depindent_obj.dest_location_id.id
				main_location = depindent_obj.src_location_id.id
									
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
					'indent_line_id' : group[0].id,
					'issue_type':'material'
					}
					
				
					
				
				if ids:
					self.write(cr,uid,ids[0],{'issue_line_ids':[(0,0,vals)]})
			"""	
			if ids:
				if obj.move_lines:
					move_lines = map(lambda x:x.id,obj.move_lines)
					for line_id in move_lines:
						self.write(cr,uid,ids,{'move_lines':[]})
			"""			
		self.write(cr,uid,ids,res)
		return True
		
		
		
	def update_serviceindent_to_issue(self,cr,uid,ids,context=None):
		
		serviceindent_line_obj = self.pool.get('kg.service.indent.line')
		issue_line_obj = self.pool.get('kg.department.issue.line')
		move_obj = self.pool.get('stock.move')
		prod_obj = self.pool.get('product.product')
		dep_obj = self.pool.get('kg.depmaster')
		line_ids = []			   
		res={}
		line_ids = []
		res['move_lines'] = []
		obj =  self.browse(cr,uid,ids[0])
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
			"""	
			if ids:
				if obj.move_lines:
					move_lines = map(lambda x:x.id,obj.move_lines)
					for line_id in move_lines:
						self.write(cr,uid,ids,{'move_lines':[]})
			"""			
		self.write(cr,uid,ids,res)
		return True
		
		
	def confirm_issue(self, cr, uid, ids, context=None):
		
		obj_rec = self.browse(cr, uid, ids[0])	
		lot_obj = self.pool.get('stock.production.lot')
		product_obj = self.pool.get('product.product')
		dep_issue_line_obj = self.pool.get('kg.department.issue.line')
		
		if obj_rec.name == '':
			issue_name = self.pool.get('ir.sequence').get(cr, uid, 'kg.department.issue') or ''
			obj_rec.write({'name': issue_name})
			
		obj_rec.write({'state': 'approve','confirmed_by':uid,'confirmed_date':time.strftime('%Y-%m-%d')})
		#cr.execute("""select all_transaction_mails('Issue Request Approval',%s)"""%(ids[0]))
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
					subject = " Department Issue- Waiting For Approval",
					body = data[0][0],
					email_cc = vals['email_cc'],
					object_id = ids[0] and ('%s-%s' % (ids[0], 'kg.department.issue')),
					subtype = 'html',
					subtype_alternative = 'plain')
			res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
		"""
		if not obj_rec.issue_line_ids:
			raise osv.except_osv(_('Item Line Empty!'),_('You cannot process Issue without Item Line.'))
		else:
			for item in obj_rec.issue_line_ids:
				dep_issue_line_rec = dep_issue_line_obj.browse(cr, uid, item.id)
				product_id = dep_issue_line_rec.product_id.id
				product_uom = dep_issue_line_rec.uom_id.id		
				product_record = product_obj.browse(cr, uid,product_id)
				lot_sql = """ select lot_id from kg_department_issue_details where grn_id=%s""" %(item.id)
				cr.execute(lot_sql)
				lot_data = cr.dictfetchall()
				if not lot_data:
					raise osv.except_osv(
					_('No GRN Entry !!'),
					_('There is no GRN reference for this Issue. You must associate GRN entries '))
				else:					
					val = [d['lot_id'] for d in lot_data if 'lot_id' in d]
					#### Need to check UOM then will write price #####
					stock_tot = 0.0
					po_tot = 0.0
					lot_browse = lot_obj.browse(cr, uid,val[0])
					grn_id = lot_browse.grn_move
					dep_issue_line_rec.write({'price_unit': lot_browse.price_unit or 0.0,
								})											
					for i in val:
						lot_rec = lot_obj.browse(cr, uid, i)
						stock_tot += lot_rec.pending_qty
						po_tot += lot_rec.po_qty
						uom = lot_rec.product_uom.name
					if stock_tot < dep_issue_line_rec.issue_qty:
						raise osv.except_osv(
						_('Stock not available !!'),
						_('Associated GRN have less Qty compare to issue Qty.'))
					else:
						pass
				if dep_issue_line_rec.issue_qty == 0:
					raise osv.except_osv(
					_('Item Line Qty can not Zero!'),
					_('You cannot process Issue with Item Line Qty Zero for Product %s.' %(dep_issue_line_rec.product_id.name)))
			return True
			
	def action_process(self, cr, uid, ids, context=None):
		issue_record = self.browse(cr,uid,ids[0])
		stock_move_obj=self.pool.get('stock.move')
		product_obj = self.pool.get('product.product')
		po_obj = self.pool.get('purchase.order')
		lot_obj = self.pool.get('stock.production.lot')
		item_issue_obj = self.pool.get('kg.item.wise.dept.issue')
		issue_record.write({'state': 'done','approved_by':uid,'approved_date':time.strftime('%Y-%m-%d')})
		#cr.execute("""select all_transaction_mails('Issue Request Approval',%s)"""%(ids[0]))
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
					subject = " Department Issue- Approved",
					body = data[0][0],
					email_cc = vals['email_cc'],
					object_id = ids[0] and ('%s-%s' % (ids[0], 'kg.department.issue')),
					subtype = 'html',
					subtype_alternative = 'plain')
			res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
		"""	
		#### Updating Department Issue to Stock Move ####			
		for line_ids in issue_record.issue_line_ids:
			if issue_record.issue_type == 'material':
				indent_id = line_ids.indent_line_id.indent_id.id
				depindent_obj = self.pool.get('kg.depindent').browse(cr, uid, indent_id)
				dep_stock_location = depindent_obj.dest_location_id.id
				main_location = depindent_obj.src_location_id.id
			if issue_record.issue_type == 'service':
				indent_id = line_ids.service_indent_line_id.service_id.id
				depindent_obj = self.pool.get('kg.service.indent').browse(cr, uid, indent_id)
				dep_stock_location = depindent_obj.dep_name.stock_location.id
				main_location = depindent_obj.dep_name.main_location.id
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
				raise osv.except_osv(
				_('No GRN Entry !!'),
				_('There is no GRN reference for this Issue. You must associate GRN entries '))
			else:
				val = [d['lot_id'] for d in lot_data if 'lot_id' in d]
				tot = 0.0
				for i in val:
					lot_rec = lot_obj.browse(cr, uid, i)
					tot += lot_rec.pending_qty
				if tot < line_ids.issue_qty:
					raise osv.except_osv(
					_('Stock not available !!'),
					_('Associated GRN have less Qty compare to issue Qty.'))
				else:
					pass
				### Updation Issue Pending Qty in Department Issue ###
				if issue_record.issue_type == 'material':
					dep_line_obj = self.pool.get('kg.depindent.line')   
					self.write(cr, uid, ids, {'state': 'done'})
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
								#dep_line_obj.write(cr,uid, bro_record.id, {'line_state' : 'noprocess'})
								break
							else:
								remain_qty = issue_used_qty - issue_pending_qty
								issue_qty = remain_qty
								pending_depindent_qty =  0.0
								sql = """ update kg_depindent_line set issue_pending_qty=%s where id = %s"""%(pending_depindent_qty,bro_record.id)
								cr.execute(sql)
								#dep_line_obj.write(cr,uid, bro_record.id, {'line_state' : 'noprocess'})
								if remain_qty < 0:
									break		   
						else:
							if issue_used_qty <= issue_pending_qty:
								pending_depindent_qty =  issue_pending_qty - issue_used_qty
								sql = """ update kg_depindent_line set issue_pending_qty=%s where id = %s"""%(pending_depindent_qty,bro_record.id)
								cr.execute(sql)
								#dep_line_obj.write(cr,uid, bro_record.id, {'line_state' : 'noprocess'})
								break
							else:
								remain_qty = issue_used_qty - issue_pending_qty
								issue_qty = remain_qty
								pending_depindent_qty =  0.0
								sql = """ update kg_depindent_line set issue_pending_qty=%s where id = %s"""%(pending_depindent_qty,bro_record.id)
								cr.execute(sql)
								#dep_line_obj.write(cr,uid, bro_record.id, {'line_state' : 'noprocess'})
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
								#dep_line_obj.write(cr,uid, bro_record.id, {'line_state' : 'noprocess'})
								break
							else:
								remain_qty = issue_used_qty - issue_pending_qty
								issue_qty = remain_qty
								pending_depindent_qty =  0.0
								sql = """ update kg_service_indent_line set issue_pending_qty=%s where id = %s"""%(pending_depindent_qty,bro_record.id)
								cr.execute(sql)
								#dep_line_obj.write(cr,uid, bro_record.id, {'line_state' : 'noprocess'})
								if remain_qty < 0:
									break		   
						else:
							if issue_used_qty <= issue_pending_qty:
								pending_depindent_qty =  issue_pending_qty - issue_used_qty
								sql = """ update kg_service_indent_line set issue_pending_qty=%s where id = %s"""%(pending_depindent_qty,bro_record.id)
								cr.execute(sql)
								#dep_line_obj.write(cr,uid, bro_record.id, {'line_state' : 'noprocess'})
								break
							else:
								remain_qty = issue_used_qty - issue_pending_qty
								issue_qty = remain_qty
								pending_depindent_qty =  0.0
								sql = """ update kg_service_indent_line set issue_pending_qty=%s where id = %s"""%(pending_depindent_qty,bro_record.id)
								cr.execute(sql)
								#dep_line_obj.write(cr,uid, bro_record.id, {'line_state' : 'noprocess'})
								if remain_qty < 0:
									break
				# The below part will update production lot pending qty while issue stock to sub store #
				sql = """ select lot_id from kg_department_issue_details where grn_id=%s""" %(line_ids.id)
				cr.execute(sql)
				data = cr.dictfetchall()
				if data:
					val = [d['lot_id'] for d in data if 'lot_id' in d]
					issue_qty = line_ids.issue_qty
					for i in val:
						lot_rec = lot_obj.browse(cr,uid,i)
						move_qty = issue_qty
						if move_qty > 0 and move_qty <= lot_rec.pending_qty:
							#move_qty = move_qty - lot_rec.issue_qty
							lot_pending_qty = lot_rec.pending_qty - move_qty
							lot_rec.write({'pending_qty': lot_pending_qty,'issue_qty': 0.0})
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
							break
						else:
							if move_qty > 0:								
								lot_pending_qty = lot_rec.pending_qty
								remain_qty =  move_qty - lot_pending_qty
								lot_rec.write({'pending_qty': 0.0})
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
							else:
								pass
						issue_qty = remain_qty
				else:
					pass
					
		return True
	
	def department_issue_scheduler(self,cr,uid,ids=0,context = None):
		cr.execute(""" SELECT current_database();""")
		db = cr.dictfetchall()
		if db[0]['current_database'] == 'Empereal-KGDS':
			db[0]['current_database'] = 'Empereal-KGDS'
		elif db[0]['current_database'] == 'FSL':
			db[0]['current_database'] = 'FSL'
		elif db[0]['current_database'] == 'IIM':
			db[0]['current_database'] = 'IIM'
		elif db[0]['current_database'] == 'IIM_HOSTEL':
			db[0]['current_database'] = 'IIM Hostel'
		elif db[0]['current_database'] == 'KGISL-SD':
			db[0]['current_database'] = 'KGISL-SD'
		elif db[0]['current_database'] == 'CHIL':
			db[0]['current_database'] = 'CHIL'
		elif db[0]['current_database'] == 'KGCAS':
			db[0]['current_database'] = 'KGCAS'
		elif db[0]['current_database'] == 'KGISL':
			db[0]['current_database'] = 'KGISL'
		elif db[0]['current_database'] == 'KITE':
			db[0]['current_database'] = 'KITE'
		elif db[0]['current_database'] == 'TRUST':
			db[0]['current_database'] = 'TRUST'
		elif db[0]['current_database'] == 'CANTEEN':
			db[0]['current_database'] = 'CANTEEN'
		else:
			db[0]['current_database'] = 'Others'
			
		cr.execute(""" select name from kg_department_issue where to_char(approved_date::date,'dd-mm-yyyy') = '%s' and
		 state in ('done') """
					    %(time.strftime('%d-%m-%Y')))
		grn_data = cr.dictfetchall()	
			
		if grn_data:	
			cr.execute("""select all_daily_auto_scheduler_mails('Issue Register')""")
			data = cr.fetchall();
			cr.execute("""select 
							trim(TO_CHAR(sum(kg_department_issue_line.issue_qty * kg_department_issue_line.price_unit)::float, '999G999G99G999G99G99G990D99')) as sum
							from kg_department_issue
							left join kg_department_issue_line on kg_department_issue_line.issue_id = kg_department_issue.id
							where 
							to_char(kg_department_issue.issue_date,'dd-mm-yyyy') = '%s' and
							kg_department_issue.state in ('done')"""%(time.strftime('%d-%m-%Y')))
			total_sum = cr.dictfetchall();
			db = db[0]['current_database'].encode('utf-8')
			total_sum = str(total_sum[0]['sum'])
			vals = self.sechedular_email_ids(cr,uid,ids,context = context)
			if (not vals['email_to']) and (not vals['email_cc']):
				pass
			else:
				ir_mail_server = self.pool.get('ir.mail_server')
				msg = ir_mail_server.build_email(
						email_from = vals['email_from'][0],
						email_to = vals['email_to'],
						subject = "ERP Issue Register Details for "+db +' as on '+time.strftime('%d-%m-%Y')+'. Total Amount (Rs.):' + total_sum,
						body = data[0][0],
						email_cc = vals['email_cc'],
						object_id = ids and ('%s-%s' % (ids, 'kg.department.issue')),
						subtype = 'html',
						subtype_alternative = 'plain')
				res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
				
		else:
			pass		
				
		return True
	
kg_department_issue()


class kg_department_issue_line(osv.osv):

	_name = "kg.department.issue.line"
	_description = "Department Issue Line"

	
	_columns = {
		
		'issue_date':fields.date('PO GRN Date'),
		'issue_id':fields.many2one('kg.department.issue','Department Issue Entry'),
		'name':fields.char('Product'),
		'product_id':fields.many2one('product.product','Product Name',required=True),
		'uom_id':fields.many2one('product.uom','UOM',readonly=True),
		'issue_qty':fields.float('Issue Quantity',required=True),
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
		#'kg_grn_moves': fields.many2many('stock.production.lot','kg_department_issue_details','grn_id','lot_id', 'GRN Entry',
		#			domain="[('product_id','=',product_id), '&',('grn_type','=','issue_type'), '&', ('pending_qty','>','0'), '&', ('lot_type','!=','out')]",
		#			),
		'kg_grn_moves': fields.many2many('stock.production.lot','kg_department_issue_details','grn_id','lot_id', 'GRN Entry',
							),
		'kg_itemwise_issue_line':fields.one2many('kg.item.wise.dept.issue','issue_line_id','Item wise Department Issue',readonly=True),
		'state': fields.selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),('done', 'Done'), ('cancel', 'Cancelled')], 'Status',readonly=True),
		'remarks': fields.text('Remarks'),
		'brand_id':fields.many2one('kg.brand.master','Brand Name'),
		'issue_return_line':fields.boolean('Excess Return Flag'),
		'excess_return_qty':fields.float('Excess Return Qty'),
		'damage_flag':fields.boolean('Damage Return Flag'),
		'return_qty':fields.float('Returned Qty'),
		
	}
	
	_defaults = {
	
		'state':'draft',
		
		
	}
	
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
			

kg_department_issue_line()



class kg_item_wise_dept_issue(osv.osv):

	_name = "kg.item.wise.dept.issue"
	_description = "Item wise Department Issue"

	
		
		
	_columns = {
		
		'issue_line_id':fields.many2one('kg.department.issue.line','Department Issue Line Entry'),
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



class kg_dept_issue_stock_move(osv.osv):

	_name = "stock.move"
	_inherit = "stock.move"

	
	
	
	_columns = {
		
		'dept_issue_id':fields.many2one('kg.department.issue','Department Issue'),
		'dept_issue_line_id':fields.many2one('kg.department.issue.line','Department Issue Line'),
		
	}
	
	
	
kg_dept_issue_stock_move()










