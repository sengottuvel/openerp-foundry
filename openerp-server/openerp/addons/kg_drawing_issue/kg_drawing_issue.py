from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re 
dt_time = lambda * a: time.strftime('%m/%d/%Y %H:%M:%S')


class kg_drawing_issue(osv.osv):

	_name = "kg.drawing.issue"
	_description = "Drawing Issue"
	_order = "entry_date desc"
	
	def _get_default_division(self, cr, uid, context=None):
		res = self.pool.get('kg.division.master').search(cr, uid, [('code','=','SAM'),('state','=','approved'), ('active','=','t')], context=context)
		return res and res[0] or False	
		
	_columns = {

		
		## Basic Info
		'name': fields.char('Issue No.', size=128,select=True,readonly=True),
		'entry_date': fields.date('Issue Date',required=True),		
		'note': fields.text('Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_sms': fields.boolean('SMS Notification'),
		'flag_email': fields.boolean('Email Notification'),
		'flag_spl_approve': fields.boolean('Special Approval'),
		
		## Entry Info
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),	
		'active': fields.boolean('Active'),
		'crt_date': fields.datetime('Created Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),				
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),	
		
		## Module Requirement Info
		'issue_mode': fields.selection([('direct','Direct'),('from_indent','From Indent')],'Issue Mode',),
		'division_id': fields.many2one('kg.division.master','Division',readonly=True,required=True,domain="[('active','=','t')]"),
		'dep_id': fields.many2one('kg.depmaster','Department', domain="[('item_request','=',True),('state','in',('draft','confirmed','approved'))]"),
		'indent_line_ids':fields.many2many('ch.drawing.indent.line','m2m_drawing_indent_details' , 'issue_id', 'indent_id', 'Indent Lines',
			domain="[('issue_status','=','allow'),'&',('header_id.state','=','confirmed'),'&',('header_id.dep_id','=',dep_id)]"),
		'flag_issue': fields.boolean('Flag Issue'),
		## Child Tables Declaration	
			
		'line_ids': fields.one2many('ch.drawing.issue.line','header_id','Drawing details'),  	
	
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_drawing_issue', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),		
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,			
		'state': 'draft',		
		'entry_mode': 'manual',
		'issue_mode': 'from_indent',
		'flag_issue': False,
		'division_id':_get_default_division,	
	}
	
	def update_line_items(self,cr,uid,ids,context=False):
		
		entry = self.browse(cr,uid,ids[0])
		issue_line_obj = self.pool.get('ch.drawing.issue.line')
		indent_line_obj = self.pool.get('ch.drawing.indent.line')
	
		
		del_sql = """ delete from ch_drawing_issue_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		if entry.indent_line_ids:
			for indent_item in entry.indent_line_ids:
				print "indent_item",indent_item
				
				issue_details = {
											
					'header_id': entry.id,
					'order_line_id': indent_item.header_id.order_line_id.id,
					'pump_model_type': indent_item.header_id.pump_model_type,
					'position_id': indent_item.position_id.id,	
					'item_code': indent_item.item_code,
					'item_name': indent_item.item_name,				
					'indent_id': indent_item.id,				
					
					}
				issue_line_id = issue_line_obj.create(cr, uid, issue_details)
				self.write(cr, uid, ids, {'flag_issue':True})
				indent_line_obj.write(cr, uid, indent_item.id, {'issue_status':'not_allow'})	
							
		return True
	

	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		position_obj = self.pool.get('kg.position.number')
		if entry.state == 'draft':
			### Drawing No. Updation ##
			if not entry.line_ids:
				raise osv.except_osv(_('Line Item Details !!'),_('Enter the Issue Details !!'))
			for issue_item in entry.line_ids:
				position_obj.write(cr,uid,issue_item.position_id.id,{'drawing_no':issue_item.drawing_no})
				self.pool.get('ch.drawing.issue.line').write(cr,uid,issue_item.id,{'pending_qty':issue_item.qty})				
			
			### Sequence Number Generation  ###		
			if entry.name == '' or entry.name == False:
				seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.drawing.issue')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_obj_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_obj_id[0],seq_rec.code,entry.entry_date))
				entry_name = cr.fetchone();
				entry_name = entry_name[0]
			else:
				entry_name = entry.name	
												
			self.write(cr, uid, ids, {'name':entry_name,'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
							
		return True	
	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state not in ('draft'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)	
		
	def create(self, cr, uid, vals, context=None):
		return super(kg_drawing_issue, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_drawing_issue, self).write(cr, uid, ids, vals, context)
		
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		entry_date = rec.entry_date
		entry_date = str(entry_date)
		entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
		
		if entry_date > today:
			return False	
		return True
		
	_constraints = [			
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
		
	   ]	
	
kg_drawing_issue()

class ch_drawing_issue_line(osv.osv):
	
	_name = "ch.drawing.issue.line"
	_description = "Drawing Issue Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.drawing.issue','Header Id', required=True, ondelete='cascade'),
		'indent_id': fields.many2one('ch.drawing.indent.line','Indent Line Id'),
		'order_line_id': fields.many2one('ch.work.order.details','WO No.',domain="[('header_id.state','=','confirmed')]"),
		'pump_model_type': fields.related('order_line_id','pump_model_type', type='selection', selection=[('vertical','Vertical'),('horizontal','Horizontal'),('others','Others')], string='Pump Type', store=True, readonly=True),
		'position_id': fields.many2one('kg.position.number','Position No.',domain="[('state','=','approved')]"),	
		'item_code':fields.char('Item Code'),
		'item_name':fields.char('Item Name'),				
		'drawing_no':fields.char('Drawing No.'),						
		'qty':fields.integer('Quantity'),						
		'pending_qty':fields.integer('Pending Qty'),						
		'remarks': fields.text('Remarks'),
		'drawing_copy': fields.binary('Drawing Copy'),
		'filename':fields.char('File Name'),
			
	}
	
	_defaults = {			
		'qty' : 1,		
	}
	
	def onchange_order_line_id(self, cr, uid, ids, order_line_id):
		if order_line_id:
			order_rec = self.pool.get('ch.work.order.details').browse(cr, uid, order_line_id)
		return {'value': {'pump_model_type':order_rec.pump_model_type}}
		
		
	def _position_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.position_id:					
			cr.execute(""" select position_id from ch_drawing_issue_line where position_id  = '%s' and header_id =%s 				
			""" %(rec.position_id.id,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
		
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty <= 0.00:
			return False
		return True	
	
		
	_constraints = [						
		(_position_validate, 'Please Check Position No should be unique!!!',['Position No.']),	
		(_check_values, 'System not allow to save negative and zero values..!!',['Qty']),		
	   ]
	

ch_drawing_issue_line()	





class kg_drawing_return(osv.osv):

	_name = "kg.drawing.return"
	_description = "Drawing Return"
	_order = "entry_date desc"
	
	def _get_default_division(self, cr, uid, context=None):
		res = self.pool.get('kg.division.master').search(cr, uid, [('code','=','SAM'),('state','=','approved'), ('active','=','t')], context=context)
		return res and res[0] or False	
		
	_columns = {

		
		## Basic Info
		'name': fields.char('Issue Return No.', size=128,select=True,readonly=True),
		'entry_date': fields.date('Issue Return Date',required=True),		
		'note': fields.text('Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_sms': fields.boolean('SMS Notification'),
		'flag_email': fields.boolean('Email Notification'),
		'flag_spl_approve': fields.boolean('Special Approval'),
		
		## Entry Info
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),	
		'active': fields.boolean('Active'),
		'crt_date': fields.datetime('Created Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),				
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),	
		
		## Module Requirement Info
		
		'division_id': fields.many2one('kg.division.master','Division',readonly=True,required=True,domain="[('active','=','t')]"),
		'dep_id': fields.many2one('kg.depmaster','Department', domain="[('item_request','=',True),('state','in',('draft','confirmed','approved'))]"),
		'issue_line_ids':fields.many2many('ch.drawing.issue.line','m2m_drawing_issue_details' , 'return_id', 'issue_id', 'Issue Lines',
			domain="[('pending_qty','>', 0),'&',('header_id.state','=','confirmed'),'&',('header_id.dep_id','=',dep_id)]"),
		'flag_return': fields.boolean('Flag Return'),
		## Child Tables Declaration	
			
		'line_ids': fields.one2many('ch.drawing.return.line','header_id','Drawing details'),  	
	
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_drawing_return', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),		
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,			
		'state': 'draft',		
		'entry_mode': 'manual',		
		'flag_return': False,
		'division_id':_get_default_division,	
	}
	
	def update_line_items(self,cr,uid,ids,context=False):
		
		entry = self.browse(cr,uid,ids[0])
		return_line_obj = self.pool.get('ch.drawing.return.line')
		issue_line_obj = self.pool.get('ch.drawing.issue.line')
	
		
		del_sql = """ delete from ch_drawing_return_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		if entry.issue_line_ids:
			for issue_item in entry.issue_line_ids:
				print "indent_item",issue_item
				
				return_details = {
											
					'header_id': entry.id,
					'issue_line_id': issue_item.id,
					'order_line_id': issue_item.order_line_id.id,
					'pump_model_type': issue_item.pump_model_type,
					'position_id': issue_item.position_id.id,	
					'drawing_no': issue_item.drawing_no,
					'item_code': issue_item.item_code,
					'item_name': issue_item.item_name,				
					'qty': issue_item.pending_qty,				
					
					}
				return_line_id = return_line_obj.create(cr, uid, return_details)
				self.write(cr, uid, ids, {'flag_return':True})
				#~ indent_line_obj.write(cr, uid, indent_item.id, {'issue_status':'not_allow'})	
							
		return True
	

	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])	
		issue_line_obj = self.pool.get('ch.drawing.issue.line')	
		if entry.state == 'draft':
			if not entry.line_ids:
				raise osv.except_osv(_('Line Item Details !!'),_('Enter the Return Details !!'))	
			for line in entry.line_ids:
				if line.issue_line_id.pending_qty < line.qty:
					raise osv.except_osv(_('Excess Qty Not Allowed'),
					_('Kindly verify Excess Qty!!'))
			### Sequence Number Generation  ###		
			if entry.name == '' or entry.name == False:
				seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.drawing.return')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_obj_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_obj_id[0],seq_rec.code,entry.entry_date))
				entry_name = cr.fetchone();
				entry_name = entry_name[0]
			else:
				entry_name = entry.name	
			
			for line in entry.line_ids:
				issue_line_obj.write(cr, uid, line.issue_line_id.id, {'pending_qty':line.issue_line_id.pending_qty - line.qty})	
												
			self.write(cr, uid, ids, {'name':entry_name,'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
							
		return True	
	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state not in ('draft'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)	
		
	def create(self, cr, uid, vals, context=None):
		return super(kg_drawing_return, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_drawing_return, self).write(cr, uid, ids, vals, context)
		
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		entry_date = rec.entry_date
		entry_date = str(entry_date)
		entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
		
		if entry_date > today:
			return False	
		return True
		
	_constraints = [			
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
		
	   ]	
	
kg_drawing_return()

class ch_drawing_return_line(osv.osv):
	
	_name = "ch.drawing.return.line"
	_description = "Drawing Return Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.drawing.return','Header Id', required=True, ondelete='cascade'),
		'issue_line_id': fields.many2one('ch.drawing.issue.line','Issue Line Id', required=True, ondelete='cascade'),
		'order_line_id': fields.many2one('ch.work.order.details','WO No.',domain="[('header_id.state','=','confirmed')]"),
		'pump_model_type': fields.related('order_line_id','pump_model_type', type='selection', selection=[('vertical','Vertical'),('horizontal','Horizontal'),('others','Others')], string='Pump Type', store=True, readonly=True),
		'position_id': fields.many2one('kg.position.number','Position No.',domain="[('state','=','approved')]"),	
		'item_code':fields.char('Item Code'),
		'item_name':fields.char('Item Name'),				
		'drawing_no':fields.char('Drawing No.'),						
		'qty':fields.integer('Quantity'),						
		'remarks': fields.text('Remarks'),
		
			
	}	
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty <= 0.00:
			return False
		return True	
		
	_constraints = [			
		(_check_values, 'System not allow to save negative and zero values..!!',['Qty']),		
	   ]
	

ch_drawing_return_line()	

