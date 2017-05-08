from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re 
dt_time = lambda * a: time.strftime('%m/%d/%Y %H:%M:%S')


class kg_drawing_indent(osv.osv):

	_name = "kg.drawing.indent"
	_description = "Drawing Indent"
	_order = "entry_date desc"
	
	def _get_default_division(self, cr, uid, context=None):
		res = self.pool.get('kg.division.master').search(cr, uid, [('code','=','SAM'),('state','=','approved'), ('active','=','t')], context=context)
		return res and res[0] or False	
		
	_columns = {

		
		## Basic Info
		'name': fields.char('Indent No.', size=128,select=True),
		'entry_date': fields.date('Indent Date',required=True),		
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
		'order_line_id': fields.many2one('ch.work.order.details','WO No.',domain="[('header_id.state','=','confirmed')]"),
		'pump_model_type': fields.related('order_line_id','pump_model_type', type='selection', selection=[('vertical','Vertical'),('horizontal','Horizontal'),('others','Others')], string='Pump Type', store=True, readonly=True),
		
		## Child Tables Declaration	
			
		'line_ids': fields.one2many('ch.drawing.indent.line','header_id','Drawing details'),  	
	
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_drawing_indent', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),		
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,			
		'state': 'draft',		
		'entry_mode': 'manual',
		'division_id':_get_default_division,	
	}
	
	def onchange_order_line_id(self, cr, uid, ids, order_line_id):
		if order_line_id:
			order_rec = self.pool.get('ch.work.order.details').browse(cr, uid, order_line_id)
			print "order_recorder_rec",order_rec
		return {'value': {'pump_model_type':order_rec.pump_model_type}}
	
	
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':		
			
			### Sequence Number Generation  ###		
			if entry.name == '' or entry.name == False:
				seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.drawing.indent')])
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
		return super(kg_drawing_indent, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_drawing_indent, self).write(cr, uid, ids, vals, context)
		
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
	
kg_drawing_indent()

class ch_drawing_indent_line(osv.osv):
	
	_name = "ch.drawing.indent.line"
	_description = "Drawing Indent Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.drawing.indent','Header Id', required=True, ondelete='cascade'),
		'order_line_id': fields.related('header_id','order_line_id',type='many2one',relation='ch.work.order.details',string='WO No.',store=True, readonly=True),
		'pump_model_type': fields.related('order_line_id','pump_model_type', type='selection', selection=[('vertical','Vertical'),('horizontal','Horizontal'),('others','Others')], string='Pump Type', store=True, readonly=True),
		'order_foundry_id': fields.many2one('ch.order.bom.details','Foundry Item'),
		'order_foundry_acc_id': fields.many2one('ch.wo.accessories.foundry','Acc Foundry Item'),
		'order_ms_id': fields.many2one('ch.order.machineshop.details','MS Item'),
		'order_ms_acc_id': fields.many2one('ch.wo.accessories.ms','Acc MS Item'),
		'order_bot_id': fields.many2one('ch.order.bot.details','BOT Item'),
		'order_bot_acc_id': fields.many2one('ch.wo.accessories.bot','Acc BOT Item'),
		'position_id': fields.many2one('kg.position.number','Position No.',domain="[('state','=','approved')]"),	
		'item_code':fields.char('Item Code'),
		'item_name':fields.char('Item Name'),				
		'commit_date': fields.date('Drawing Commitment date'),						
		'remarks': fields.text('Remarks'),
		'issue_status':fields.selection([('allow','Allow to Issue'),('not_allow','Not Allow to Issue')],'Issue Status', readonly=True),		
	}
	
	_defaults = {			
		'commit_date' : lambda * a: time.strftime('%Y-%m-%d'),	
		'issue_status': 'allow'
	}
	
	def onchange_position_id(self, cr, uid, ids, position_id):
		item_code = ''
		item_name = ''
		if position_id:
			position_rec = self.pool.get('kg.position.number').browse(cr, uid, position_id)
			if position_rec.item_type == 'pattern':
				item_code = position_rec.pattern_id.name
				item_name = position_rec.pattern_id.pattern_name
			if position_rec.item_type == 'ms':
				item_code = position_rec.ms_id.code
				item_name = position_rec.ms_id.name
			if position_rec.item_type == 'bot':
				item_code = position_rec.bot_id.code
				item_name = position_rec.bot_id.name
			
		return {'value': {'item_code':item_code,'item_name':item_name}}
		
		
	def _position_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.position_id:					
			cr.execute(""" select position_id from ch_drawing_indent_line where position_id  = '%s' and header_id =%s 				
			""" %(rec.position_id.id,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
	
		
	_constraints = [						
		#~ (_position_validate, 'Please Check Position No should be unique!!!',['Position No.']),			
	   ]
	

ch_drawing_indent_line()	

