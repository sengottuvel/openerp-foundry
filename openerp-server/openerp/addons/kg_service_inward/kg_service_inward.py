from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import base64
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_service_inward(osv.osv):

	_name = "kg.service.inward"
	_description = "Service Inward Details"
	_order = "entry_date desc"
	
	_columns = {
	
		## Version 0.1
	
		## Basic Info
				
		'name': fields.char('Inward No', size=12,select=True,readonly=True),
		'entry_date': fields.date('Inward Date',required=True),		
		'note': fields.text('Notes'),
		'state': fields.selection([('pending','Pending'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
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
		
		'customer_id': fields.many2one('res.partner', 'Customer Name'),
		'complaint_no': fields.many2one('kg.service.enquiry', 'Complaint No'),
		'complaint_date': fields.date('Complaint Date'),
		's_no': fields.char('Serial No.'),
		'wo_no': fields.char('WO No'),
		'wo_line_id': fields.many2one('ch.work.order.details','WO No'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Model'),
		'moc_const_id': fields.many2one('kg.moc.construction','MOC Construction'),
		'item_code': fields.char('Item Code'),
		'item_name': fields.char('Item Name'),
		'defect_id': fields.many2one('kg.defect.master', 'Pump/Item Defect type'),
		'purpose_categ': fields.selection([('pump','Pump'),('part','Part')], 'Type'),
		'move_to': fields.selection([('stock','Stock'),('scrap','Scrap'),('no_return','No Return')], 'Move To'),
		'weight': fields.float('Weight'),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location'),
		
		## Child Tables Declaration 
				
		#~ 'line_ids': fields.one2many('ch.transactions', 'header_id', "Line Details"),
		
	}
		
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_service_inward', context=c),			
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'pending',		
		'active': True,
		'entry_mode': 'manual',		
		'flag_sms': False,		
		'flag_email': False,		
		'flag_spl_approve': False,		
		
	}
	
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
			
		
	def _check_lineitems(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if not entry.line_ids:
			return False
		return True
			
	
	_constraints = [        
              
        (_future_entry_date_check, 'System not allow to save with future date. !!',['']),
        #~ (_check_lineitems, 'System not allow to save with empty Details !!',['']),
        
       ]

	def entry_confirm(self,cr,uid,ids,context=None):
		
		rec = self.browse(cr,uid,ids[0])		
		
		### Sequence Number Generation  ###
		
		if rec.name == '' or rec.name == False:
			seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.service.inward')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_obj_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_obj_id[0],seq_rec.code,rec.entry_date))
			entry_name = cr.fetchone();
			entry_name = entry_name[0]
		else:
			entry_name = rec.name		
		
		# Stock Inward Creation Process
		if rec.move_to == 'stock':
			stock_inward_id = self.pool.get('kg.stock.inward').create(cr,uid,{'entry_date': time.strftime('%Y-%m-%d'),'location':rec.location})
			print"stock_inward_idstock_inward_id",stock_inward_id
			pattern_id = moc_id = 0
			if stock_inward_id:
				if rec.purpose_categ == 'pump':
					stock_type = 'pump'
					item_code = ''
					item_name = ''
					pattern_id = ''
					moc_id = ''
				elif rec.purpose_categ == 'part':
					stock_type = 'pattern'
					item_code = rec.item_code
					item_name = rec.item_name
					pat_obj = self.pool.get('kg.pattern.master').search(cr,uid,[('pattern_name','=',rec.item_name)])
					if pat_obj:
						pat_rec = self.pool.get('kg.pattern.master').browse(cr,uid,pat_obj[0])
						pattern_id = pat_rec.id
						moc_id = pat_rec.moc_id.id
					
				stock_inward_line_id = self.pool.get('ch.stock.inward.details').create(cr,uid,{'header_id': stock_inward_id,
																							   'location': rec.location,
																							   'stock_type': stock_type,
																							   'pump_model_id': rec.pump_id.id,
																							   'moc_construction_id': rec.moc_const_id.id,
																							   'each_wgt': rec.weight,
																							   'stock_mode': 'manual',
																							   'state': 'confirmed',
																							   'qty': 1,
																							   'available_qty': 1,
																							   'item_code': item_code,
																							   'item_name': item_name,
																							   'pattern_name': item_name,
																							   'pattern_id': pattern_id,
																							   'moc_id': moc_id,
																							   'serial_no': rec.s_no,
																							   })
				
			
		self.write(cr, uid, ids, {'name':entry_name,'state':'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		
		return True
		
	def entry_approve(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def entry_cancel(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'pending':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def create(self, cr, uid, vals, context=None):
		return super(kg_service_inward, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_service_inward, self).write(cr, uid, ids, vals, context)
	
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_code = str(rec.name)		
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
			
		url = 'http://192.168.1.7/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&Service_Inward='+rec_code


		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
		
	_sql_constraints = [
	
		('name', 'unique(name)', 'No must be Unique !!'),
	]	
	
kg_service_inward()

