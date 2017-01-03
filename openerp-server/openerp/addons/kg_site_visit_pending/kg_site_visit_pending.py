from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import base64

PURPOSE_SELECTION = [
    ('pump','Pump'),('spare','Spare')
]

STATE_SELECTION = [
    ('pending','Pending'),('plan','Planned'),('close','Closed')
]

class kg_site_visit_pending(osv.osv):

	_name = "kg.site.visit.pending"
	_description = "Site Visit Pending Entry"
	_order = "registration_date desc"

	_columns = {
	
		### Header Details ####
		'name': fields.char('Name', size=128,select=True),
		'complaint_no': fields.many2one('kg.service.enquiry','Complaint No',required=True,readonly=True),
		'registration_date': fields.date('Complaint Date',required=True,readonly=True),
		'customer_id': fields.many2one('res.partner','Customer Name',domain=[('customer','=',True),('contact','=',False)],required=True),
		'purpose': fields.selection(PURPOSE_SELECTION,'Purpose',required=True,readonly=True),
		's_no': fields.char('Serial Number'),
		'wo_no': fields.char('Old WO No'),
		'wo_line_id': fields.many2one('ch.work.order.details','WO No'),
		'complaint_line_id': fields.many2one('ch.service.enquiry','Ch Service Enquiry'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Model'),
		'moc_const_id': fields.many2one('kg.moc.construction','MOC Construction'),
		'item_code': fields.char('Item Code'),
		'item_name': fields.char('Item Name'),
		'defect_id': fields.many2one('kg.defect.master','Pump Defect Type'),
		'complaint_due_to': fields.selection([('sam','SAM'),('customer','Customer')],'Complaint Due To'),
		'decision': fields.selection([('no_fault','No Fault'),('replace','Replacement'),('site_visit','Site Visit')],'Decision'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No',domain="[('active','=','t')]"),
		'pattern_name': fields.char('Pattern Name'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code',domain = [('type','=','ms')], ondelete='cascade'),
		'ms_name_id': fields.related('ms_id','name', type='char',size=128,string='Item Name', store=True),
		'bot_id':fields.many2one('kg.machine.shop', 'Item Code',domain = [('type','=','bot')], ondelete='cascade'),
		'bot_name': fields.related('bot_id','name', type='char', size=128, string='Item Name', store=True),
		'state': fields.selection(STATE_SELECTION,'Status', readonly=True),
		'remarks': fields.text('Remarks'),
		'note': fields.char('Notes'),
		'cancel_remark': fields.text('Cancel Remarks'),
		
		'line_ids': fields.one2many('ch.site.pending.fou', 'header_id', "Item Details"),
		'line_ids_a': fields.one2many('ch.site.pending.ms', 'header_id', "Item Details"),
		'line_ids_b': fields.one2many('ch.site.pending.bot', 'header_id', "Item Details"),
		
		#~ 'complaint_fou_id': fields.related('complaint_line_id','line_ids_fou', type='one2many', relation='ch.service.enquiry.fou', string='Foundry Items'),
		#~ 'complaint_ms_id': fields.related('complaint_line_id','line_ids_ms', type='one2many', relation='ch.service.enquiry.ms', string='MS Items'),
		#~ 'complaint_bot_id': fields.related('complaint_line_id','line_ids_bot', type='one2many', relation='ch.service.enquiry.bot', string='BOT Items'),
			
		### Entry Info ####
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'approve_user_id': fields.many2one('res.users', 'Approved By', readonly=True),
		'close_date': fields.datetime('Closed Date', readonly=True),
		'close_user_id': fields.many2one('res.users', 'Closed By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),	   
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_site_visit_pending', context=c),
		'registration_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date': time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'pending',
		'active': True,
		
	}
	
	#~ primecost_vals = self._prepare_primecost(cr,uid,item,catg)
	
	def _close_status(self,cr,uid,sv_pen_ids,context=None):
		rec = self.browse(cr,uid,sv_pen_ids)
		close_status = ch_com_header = 0
		complaint_line_id = rec.complaint_line_id.id
		print"complaint_line_idcomplaint_line_id",complaint_line_id
		ch_com_rec = self.pool.get('ch.service.enquiry').browse(cr,uid,complaint_line_id)
		complaint_id = ch_com_rec.header_id.id
		close_len = 0
		if rec.complaint_line_id:
			close_obj = self.search(cr,uid,[('complaint_no','=',complaint_id),('state','=','close')])
			print"close_obj",close_obj
			if close_obj:
				close_len = len(close_obj)
			print"close_lenclose_len",close_len
			unclose_obj = self.search(cr,uid,[('complaint_no','=',complaint_id)])
			print"unclose_obj",unclose_obj
			if unclose_obj:
				unclose_len = len(unclose_obj)
			print"unclose_lenunclose_len",unclose_len
			if unclose_len == close_len:
				ch_com_rec = self.pool.get('ch.service.enquiry').browse(cr,uid,complaint_line_id)
				ch_com_header = ch_com_rec.header_id.id
				
		close_status = ch_com_header
		print"ch_com_headerch_com_header",ch_com_header
		print"close_statusclose_status",close_status
		
		return close_status
	 
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	#~ def write(self, cr, uid, ids, vals, context=None):
		#~ vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		#~ return super(kg_site_visit_pending, self).write(cr, uid, ids, vals, context)
								
kg_site_visit_pending()

class ch_site_pending_fou(osv.osv):

	_name = "ch.site.pending.fou"
	_description = "Ch Site Visit Pending FOU Details"
	
	_columns = {
	
		'header_id':fields.many2one('kg.site.visit.pending', 'SV Pending', ondelete='cascade'),
		'is_applicable': fields.boolean('Applicable'),
		'position_id': fields.many2one('kg.position.number', 'Position No'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No',domain="[('active','=','t')]"),
		'pattern_name': fields.char('Pattern Name'),
		'qty': fields.integer('Qty'),
		'complaint_categ': fields.selection([('pump','Pump'),('parts','Parts'),('access','Access')],'Complaint Category'),
		'defect_id': fields.many2one('kg.defect.master','Defect Type'),
		'complaint_due_to': fields.selection([('sam','SAM'),('customer','Customer')],'Complaint Due To'),
		'decision': fields.selection([('no_fault','No Fault'),('replace','Replacement(Cost)'),('replace_free','Replacement(Free)'),('site_visit','Site Visit')],'Decision'),
		'remark': fields.text('Complaint Remarks'),
		
	}
	
ch_site_pending_fou()

class ch_site_pending_ms(osv.osv):

	_name = "ch.site.pending.ms"
	_description = "Ch Site Visit Pending MS Details"
	
	_columns = {
	
		'header_id':fields.many2one('kg.site.visit.pending', 'SV Pending', ondelete='cascade'),
		'is_applicable': fields.boolean('Applicable'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code',domain = [('type','=','ms')], ondelete='cascade'),
		'ms_name_id': fields.related('ms_id','name', type='char',size=128,string='Item Name', store=True),
		'qty': fields.integer('Qty'),
		'complaint_categ': fields.selection([('pump','Pump'),('parts','Parts'),('access','Access')],'Complaint Category'),
		'defect_id': fields.many2one('kg.defect.master','Defect Type'),
		'complaint_due_to': fields.selection([('sam','SAM'),('customer','Customer')],'Complaint Due To'),
		'decision': fields.selection([('no_fault','No Fault'),('replace','Replacement(Cost)'),('replace_free','Replacement(Free)'),('site_visit','Site Visit')],'Decision'),
		'remark': fields.text('Complaint Remarks'),
				
	}
	
ch_site_pending_ms()

class ch_site_pending_bot(osv.osv):

	_name = "ch.site.pending.bot"
	_description = "Ch Site Visit Pending BOT Details"
	
	_columns = {
	
		'header_id':fields.many2one('kg.site.visit.pending', 'SV Pending', ondelete='cascade'),
		'is_applicable': fields.boolean('Applicable'),
		'bot_id':fields.many2one('kg.machine.shop', 'Item Code',domain = [('type','=','bot')], ondelete='cascade'),
		'bot_name': fields.related('bot_id','name', type='char', size=128, string='Item Name', store=True),
		'qty': fields.integer('Qty'),
		'complaint_categ': fields.selection([('pump','Pump'),('parts','Parts'),('access','Access')],'Complaint Category'),
		'defect_id': fields.many2one('kg.defect.master','Defect Type'),
		'complaint_due_to': fields.selection([('sam','SAM'),('customer','Customer')],'Complaint Due To'),
		'decision': fields.selection([('no_fault','No Fault'),('replace','Replacement(Cost)'),('replace_free','Replacement(Free)'),('site_visit','Site Visit')],'Decision'),
		'remark': fields.text('Complaint Remarks'),
		
	}

ch_site_pending_bot()
