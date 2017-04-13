from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

ORDER_PRIORITY = [
   ('1','MS NC'),
   ('2','NC'),
   ('3','Service'),
   ('4','Emergency'),
   ('5','Spare'),
   ('6','Normal'),
  
]

ORDER_CATEGORY = [
   ('pump','Pump'),
   ('spare','Spare'),
   ('pump_spare','Pump and Spare'),
   ('service','Service'),
   ('project','Project'),
   ('access','Accessories')
]

class kg_inspection(osv.osv):

	_name = "kg.inspection"
	_description = "Ready for Inspection"
	_order = "entry_date desc"
	
	
	_columns = {
	
		## Version 0.1
	
		## Basic Info
				
		'entry_date': fields.date('RFI Date',required=True),		
		'note': fields.text('Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_sms': fields.boolean('SMS Notification'),
		'flag_email': fields.boolean('Email Notification'),
		'flag_spl_approve': fields.boolean('Special Approval'),
		
		### Entry Info ####
			
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),	
		'active': fields.boolean('Active'),	
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),		
		'ap_rej_date': fields.datetime('Approved/Reject Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Reject By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),			
		
		## Module Requirement Info
		
		
		'qap_plan_id': fields.many2one('kg.qap.plan', 'QAP Standard',readonly=True,required=True),
		'pump_qap_id': fields.many2one('kg.pump.qap','Pump QAP'),
		'order_id': fields.many2one('kg.work.order','Work Order',required=True),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line',required=True),
		'order_no': fields.related('order_line_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_category': fields.related('order_line_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Scope of Supply', store=True),
		'pump_model_type': fields.related('order_line_id','pump_model_type', type='selection', selection=[('vertical','Vertical'),('horizontal','Horizontal'),('others','Others')], string='Pump Model', store=True, readonly=True),
		'wo_qty': fields.related('order_line_id','qty', type='integer', string='WO Qty', store=True, readonly=True),
		'pump_model_id': fields.related('order_line_id','pump_model_id', type='many2one',relation='kg.pumpmodel.master',string='Pump Model',store=True,readonly=True),
		'moc_construction_id': fields.related('order_line_id','moc_construction_id', type='many2one',relation='kg.moc.construction',string='MOC Construction', store=True,readonly=True),
		'assembly_id': fields.many2one('kg.assembly.inward','Assembly'),
		'pump_serial_no': fields.related('assembly_id','pump_serial_no', type='char', string='Pump Serial No.', store=True, readonly=True),
		'enquiry_line_id': fields.related('order_line_id','enquiry_line_id', type='integer', string='Enquiry Line Id', store=True, readonly=True),
		'equipment_no': fields.char('Equipment/Tag No.'),
		'description': fields.char('Description'),
		'inspection': fields.related('order_line_id','inspection', type='selection', selection=[('yes','Yes'),('no','No'),('tpi','TPI'),('customer','Customer'),('consultant','Consultant'),('stagewise','Stage wise')], string='Inspection Type', store=True, readonly=True),
		
		### DATE Commitments ##
	
		'ins_commit_date': fields.date('Ins. Commit. date'),	
		'ins_conformed_date': fields.date('Ins. Conformed date'),		
		'ins_completed_date': fields.date('Ins. Completed date'),	
		'ins_remarks': fields.char('Ins. Remarks'),	
		'mkd_remarks': fields.char('Mkd. Remarks'),
		'rfd_date': fields.date('RFD Date',required=True),			
		
		### Attachments ###
		
		'line_ids': fields.one2many('ch.inspection.attachments', 'header_id', "Attachments"),
		
	
	}
		
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_pump_qap', context=c),			
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'rfd_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',		
		'active': True,
		'entry_mode': 'manual',		
		'flag_sms': False,		
		'flag_email': False,		
		'flag_spl_approve': False,
		
		
	}
	
	
	_constraints = [		
			  
		
		#~ (_future_entry_date_check, 'System not allow to save with future date. !!',['']),
	   #~ 
		
	]
	
	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			today = date.today()
			today = str(today)
			today = datetime.strptime(today, '%Y-%m-%d')
			rfd_date = rec.rfd_date
			rfd_date = str(rfd_date)
			rfd_date = datetime.strptime(rfd_date, '%Y-%m-%d')
			if rfd_date > today:
				raise osv.except_osv(_('Warning!'),
						_('RFD Date should not in past date !!'))
			self.pool.get('kg.pump.qap').write(cr,uid, rec.pump_qap_id.id,{'test_state':'pt','pt_state':'pending'} )
			self.write(cr, uid, ids, {'state':'confirmed','update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass	
		return True
	   
	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def create(self, cr, uid, vals, context=None):
		return super(kg_inspection, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_inspection, self).write(cr, uid, ids, vals, context)
		
	_sql_constraints = [
	
		('name', 'unique(name)', 'No must be Unique !!'),
	]	
	
kg_inspection()

class ch_inspection_attachments(osv.osv):
	
	_name = "ch.inspection.attachments"
	_description = "Inspection Attachments"	
	
	_columns = {
	
		'header_id':fields.many2one('kg.inspection', 'Inspection', required=1, ondelete='cascade'),
		'remarks': fields.text('Attachment Remarks'),
		'attachment': fields.binary('Attachment'),
		'filename':fields.char('File Name'),

	
	}
	

ch_inspection_attachments()





