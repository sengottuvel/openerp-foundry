from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re 
dt_time = lambda * a: time.strftime('%m/%d/%Y %H:%M:%S')

class kg_packing_workorder(osv.osv):

	_name = "kg.packing.workorder"
	_description = "Packing Work Order"
	_order = "entry_date desc"	
	
	def _get_order_value(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		
		for entry in self.browse(cr, uid, ids, context=context):
			cr.execute(''' select sum(amount) from ch_packing_wo_line where header_id = %s ''',[entry.id])
			wo_value = cr.fetchone()
			if wo_value[0] == None:
				wo_value = 0.00
			else:
				wo_value=wo_value[0]
			wo_value = wo_value
			result[entry.id] = wo_value
		return result
	
	_columns = {
		
		## Basic Info
		'name': fields.char('Work Order No.', size=24,select=True,readonly=True),
		'entry_date': fields.date('Order Date',required=True),		
		'note': fields.text('Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('approved','Approved'),('approved_dc','Approved & DC'),('cancel','Cancelled')],'Status', readonly=True),		
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
		'ap_rej_date': fields.datetime('Approved/Rejected Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Rejected By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),			
		
		## Module Requirement Info
		
		'division_id': fields.many2one('kg.division.master','Division'),		
		'contractor_id': fields.many2one('res.partner','Subcontractor',domain="[('contractor','=','t')]"),
		'contact_person': fields.char('Contact Person', size=128),	  
		'phone': fields.char('Phone',size=64),
		'delivery_date': fields.date('Expected Delivery Date'),
		'wo_value': fields.function(_get_order_value, string='Sub Contractor WO Value', method=True, store=True, type='float'),
		'billing_type': fields.selection([('applicable','Applicable'),('not_applicable','Not Applicable')],'Billing Type'),
		
		
				
		## Child Tables Declaration
		
		'line_ids': fields.one2many('ch.packing.wo.line','header_id','Packing WO Line'),   
				
	
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.packing.workorder', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'delivery_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'billing_type': 'applicable',		
		'state': 'draft',
		'entry_mode': 'manual',
		'flag_sms': False,		
		'flag_email': False,		
		'flag_spl_approve': False,
		
	}	
	
	
	def onchange_contractor(self, cr, uid, ids, contractor_id):
		if contractor_id:
			contractor_rec = self.pool.get('res.partner').browse(cr, uid, contractor_id)
			contact_person = contractor_rec.contact_person
			phone = contractor_rec.phone
		else:
			contact_person = ''
			phone = ''
		return {'value': {'contact_person':contact_person,'phone':phone  }}
		
	
		
		
	def entry_confirm(self,cr,uid,ids,context=None):		
		entry = self.browse(cr,uid,ids[0])	
		if entry.state == 'draft':
			if not entry.line_ids:
				raise osv.except_osv(_('Line Item Details !!'),
				_('Enter the Work Order Details !!'))				
			### Sequence Number Generation  ###		
			if entry.name == '' or entry.name == False:
				seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.packing.workorder')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_obj_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_obj_id[0],seq_rec.code,entry.entry_date))
				entry_name = cr.fetchone();
				entry_name = entry_name[0]
			else:
				entry_name = entry.name		
			
			self.write(cr, uid, ids, {'name':entry_name,'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
				
		return True		
		
	def entry_approve(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'confirmed':
			for line in entry.line_ids:
				self.pool.get('ch.packing.wo.line').write(cr,uid,line.id,{'pending_qty':line.qty})									
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})								
		return True
		
	def approve_dc(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'confirmed':				
			dc_obj = self.pool.get('kg.packing.dc')
			dc_obj_line = self.pool.get('ch.packing.dc.line')		
			dc_id = dc_obj.create(cr,uid,{'sub_wo_no':entry.name,'contractor_id':entry.contractor_id.id,'entry_mode': 'auto'})				
			for line_item in entry.line_ids:					
				dc_line = dc_obj_line.create(cr,uid,{'header_id': dc_id,'packing_id':line_item.packing_id.id,'rate':line_item.rate,													
													'qty':line_item.qty,'sub_wo_id':line_item.header_id.id,'sub_wo_line_id':line_item.id,'entry_mode':'auto'})					
				self.pool.get('ch.packing.wo.line').write(cr,uid,line_item.id,{'entry_mode':'auto','pending_qty':line_item.qty})			
								
			self.write(cr, uid, ids, {'state': 'approved_dc','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})							
							
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
		return super(kg_packing_workorder, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_packing_workorder, self).write(cr, uid, ids, vals, context)
	
kg_packing_workorder()


class ch_packing_wo_line(osv.osv):
	
	_name = "ch.packing.wo.line"
	_description = "Packing WO Line"	
	
	def _get_oper_value(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		total_value = 0.00
		value = 0.00
		for entry in self.browse(cr, uid, ids, context=context):					
			result[entry.id] = entry.qty * entry.rate
		return result
	
	_columns = {
		
		'header_id': fields.many2one('kg.packing.workorder','Work Order No.'),
		'contractor_id': fields.related('header_id','contractor_id', type='many2one', relation='res.partner', string='Contractor Name', store=True, readonly=True),	
		'packing_id':fields.many2one('kg.packing.type','Packing Box', domain="[('state','=','approved')]"),
		'rate': fields.float('Rate'),			
		'qty': fields.integer('Quantity'),				
		'pending_qty': fields.integer('Pending QTY'),				
		'amount': fields.function(_get_oper_value, string='Total Amount', method=True, store=True, type='float'),		
		'remarks': fields.text('Remarks'),	
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),		
		
		## Child Tables Declaration
		
		
	}	
	
	_defaults = {		
		
		'entry_mode': 'manual',		
		
	}	
	
	def onchange_rate(self, cr, uid, ids, packing_id):
		rate = 0.00
		if packing_id:
			packing_rec = self.pool.get('kg.packing.type').browse(cr, uid, packing_id)
			rate = packing_rec.rate_box			
		return {'value': {'rate':rate}}
		
	def _packing_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.packing_id:					
			cr.execute(""" select packing_id from ch_packing_wo_line where packing_id  = '%s' and header_id =%s 				
			""" %(rec.packing_id.id,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
	
		
	_constraints = [						
		(_packing_validate, 'Please Check Packing Box should be unique!!!',['Packing Box']),			
	   ]
		
	
ch_packing_wo_line()



class kg_packing_dc(osv.osv):

	_name = "kg.packing.dc"
	_description = "Packing Subcontract DC"
	_order = "entry_date desc"		
		
	_columns = {

		
		## Basic Info
		'name': fields.char('DC No.', size=128,select=True,readonly=True),
		'entry_date': fields.date('DC Date',required=True),		
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
		'annexure_date': fields.date('Annexure Date'),
		'annexure_no': fields.integer('Annexure 17 No.'),
		'division_id': fields.many2one('kg.division.master','Division'),				
		'contractor_id': fields.many2one('res.partner','Subcontractor',domain="[('contractor','=','t')]"),	
		'phone': fields.char('Phone',size=64),
		'sub_wo_no': fields.char('Sub WO No.'),
		'contact_person': fields.char('Contact Person', size=128),		
		'vehicle_detail': fields.char('Vehicle Detail'),
		
		## Child Tables Declaration
		'dc_sub_line_ids': fields.many2many('ch.packing.wo.line','m2m_dc_packing_sub_details' , 'order_id', 'sc_wo_id', 'SC WO Items',
		 domain="[('pending_qty','>',0),('entry_mode','=','manual'),('contractor_id','=',contractor_id)]"),  
			
		'line_ids': fields.one2many('ch.packing.dc.line','header_id','Packing Subcontract DC Line'),  	
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_packing_dc', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),		
		'annexure_date' : lambda * a: time.strftime('%Y-%m-%d'),		
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,			
		'state': 'draft',		
		'entry_mode': 'manual'		
	}
	
	def onchange_contractor(self, cr, uid, ids, contractor_id):
		if contractor_id:
			contractor_rec = self.pool.get('res.partner').browse(cr, uid, contractor_id)
		return {'value': {'contact_person':contractor_rec.contact_person,'phone':contractor_rec.phone  }}
	
	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		dc_line_obj = self.pool.get('ch.packing.dc.line')	
		wo_obj=self.pool.get('kg.packing.workorder')
		
		del_sql = """ delete from ch_packing_dc_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)	
		
		if entry.dc_sub_line_ids:
		
			for item in entry.dc_sub_line_ids:				
				
				vals = {
					
					'header_id': entry.id,
					'sub_wo_id':item.header_id.id,			
					'sub_wo_line_id':item.id,					
					'qty':item.pending_qty,
					'rate':item.rate,
					'packing_id':item.packing_id.id				
					
				}
				
				dc_line_id = dc_line_obj.create(cr, uid,vals)							
				cr.execute(""" select distinct sub_wo_id from ch_packing_dc_line where header_id = %s """ %(entry.id))
				wo_data = cr.dictfetchall()
				wo_list = []				
				for item in wo_data:
					wo_id = item['sub_wo_id']
					wo_record = wo_obj.browse(cr, uid, wo_id)
					wo_list.append(wo_record.name)
					wo_name = ",".join(wo_list)
					print"wo_namewo_name",wo_name
					self.write(cr,uid,ids[0],{
							'sub_wo_no':wo_name,							
							})			
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':		
			sc_wo_line_obj = self.pool.get('ch.packing.wo.line')			
			special_char = ''.join( c for c in entry.vehicle_detail if  c in '!@#$%^~*{}?+/=_-><?/`' )
			if entry.annexure_no <= 0:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to Annexure 17 No. Zero and negative values!!'))			
			if len(entry.line_ids) == 0:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to without line items !!'))				
			if special_char:
				raise osv.except_osv(_('Vehicle Detail'),
					_('Special Character Not Allowed !!!'))						
			if entry.line_ids:
				for line_item in entry.line_ids:											
					if line_item.qty <= 0:
						raise osv.except_osv(_('Warning!'),
									_('System not allow to save zero and negative values !!'))									
					if line_item.qty > line_item.sub_wo_line_id.pending_qty:
						raise osv.except_osv(_('Warning!'),
									_('System not allow Excess qty !!'))
					self.pool.get('ch.packing.dc.line').write(cr,uid,line_item.id,{'pending_qty':line_item.qty})					
					self.pool.get('ch.packing.wo.line').write(cr,uid,line_item.sub_wo_line_id.id,{'pending_qty':line_item.sub_wo_line_id.pending_qty - line_item.qty})
			
			### Sequence Number Generation  ###		
			if entry.name == '' or entry.name == False:
				seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.packing.dc')])
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
		return super(kg_packing_dc, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_packing_dc, self).write(cr, uid, ids, vals, context)
		
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
	
kg_packing_dc()

class ch_packing_dc_line(osv.osv):
	
	_name = "ch.packing.dc.line"
	_description = "Packing Subcontract DC Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.packing.dc','Header Id'),
		'sub_wo_id': fields.many2one('kg.packing.workorder','Work Order No.'),
		'sub_wo_line_id': fields.many2one('ch.packing.wo.line','SUB Work Line Id'),
		'contractor_id': fields.related('header_id','contractor_id', type='many2one', relation='res.partner', string='Contractor Name', store=True, readonly=True),
		'packing_id':fields.many2one('kg.packing.type','Packing Box', domain="[('state','=','approved')]"),		
		'qty': fields.integer('Quantity'),
		'rate': fields.float('Rate'),				
		'pending_qty': fields.integer('Pending QTY'),			
		'remarks': fields.text('Remarks'),		
		'state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')],'Status', readonly=True),	
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),		
	}
	
	_defaults = {		
		'state': 'pending',
		'entry_mode': 'manual',		
	}

ch_packing_dc_line()	



class kg_packing_inward(osv.osv):

	_name = "kg.packing.inward"
	_description = "Packing Subcontract Inward"
	_order = "entry_date desc"		
		
	_columns = {

		
		## Basic Info
		'name': fields.char('Inward No.', size=128,select=True,readonly=True),
		'entry_date': fields.date('Inward Date',required=True),		
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
		
		'division_id': fields.many2one('kg.division.master','Division'),	
		'contractor_id': fields.many2one('res.partner','Subcontractor',domain="[('contractor','=','t')]"),	
		'phone': fields.char('Phone',size=64),		
		'contact_person': fields.char('Contact Person', size=128),			
		
		## Child Tables Declaration
		'inward_sub_line_ids': fields.many2many('ch.packing.dc.line','m2m_inward_packing_sub_details' , 'order_id', 'sc_dc_id', 'SC DC Items',
		 domain="[('pending_qty','>',0),('contractor_id','=',contractor_id)]"),  
			
		'line_ids': fields.one2many('ch.packing.inward.line','header_id','Packing Subcontract Inward Line'),  	
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_packing_inward', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),		
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,			
		'state': 'draft',		
		'entry_mode': 'manual'		
	}
	
	def onchange_contractor(self, cr, uid, ids, contractor_id):
		if contractor_id:
			contractor_rec = self.pool.get('res.partner').browse(cr, uid, contractor_id)
		return {'value': {'contact_person':contractor_rec.contact_person,'phone':contractor_rec.phone  }}
	
	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		inward_line_obj = self.pool.get('ch.packing.inward.line')			
		del_sql = """ delete from ch_packing_inward_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)	
		
		if entry.inward_sub_line_ids:
		
			for item in entry.inward_sub_line_ids:				
				
				vals = {
					
					'header_id': entry.id,
					'packing_id':item.packing_id.id,
					'qty':item.pending_qty,						
					'rate':item.rate,						
					'pending_qty':item.pending_qty,						
					'inward_qty':item.pending_qty,						
					'sub_dc_id':item.header_id.id,			
					'sub_dc_line_id':item.id,
					'sub_wo_id':item.sub_wo_id.id,
					'sub_wo_line_id':item.sub_wo_line_id.id,					
				}
				
				inward_line_id = inward_line_obj.create(cr, uid,vals)						
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':		
			sc_dc_line_obj = self.pool.get('ch.packing.dc.line')					
			if len(entry.line_ids) == 0:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to without line items !!'))			
			for line_item in entry.line_ids:				
				if line_item.qty <= 0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save zero and negative values !!'))									
				if line_item.qty > line_item.sub_dc_line_id.pending_qty:
					raise osv.except_osv(_('Warning!'),
								_('System not allow Excess qty !!'))	
				self.pool.get('ch.packing.inward.line').write(cr,uid,line_item.id,{'pending_qty':line_item.qty})				
				self.pool.get('ch.packing.dc.line').write(cr,uid,line_item.sub_dc_line_id.id,{'pending_qty':line_item.sub_dc_line_id.pending_qty - line_item.qty})
		
			### Sequence Number Generation  ###		
			if entry.name == '' or entry.name == False:
				seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.packing.sc.inward')])
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
		return super(kg_packing_inward, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_packing_inward, self).write(cr, uid, ids, vals, context)
		
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
	
kg_packing_inward()

class ch_packing_inward_line(osv.osv):
	
	_name = "ch.packing.inward.line"
	_description = "Packing Subcontract Inward Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.packing.inward','Header Id'),
		'sub_dc_id': fields.many2one('kg.packing.dc','DC Id'),
		'sub_dc_line_id': fields.many2one('ch.packing.dc.line','DC Line Id'),
		'sub_wo_line_id': fields.many2one('ch.packing.wo.line','SUB Work Line Id'),
		'sub_wo_id': fields.many2one('kg.packing.workorder','Work Order No.'),
		'contractor_id': fields.related('header_id','contractor_id', type='many2one', relation='res.partner', string='Contractor Name', store=True, readonly=True),
		
		'packing_id':fields.many2one('kg.packing.type','Packing Box', domain="[('state','=','approved')]"),		
		'qty': fields.integer('Accepted QTY'),
		'rate': fields.float('Rate'),	
		'pending_qty': fields.integer('Pending QTY'),			
		'inward_qty': fields.integer('Inward QTY'),	
		'reject_qty': fields.integer('Rejected QTY'),	
		'remarks': fields.text('Remarks'),		
		'state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')],'Status', readonly=True),	
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_invoice': fields.boolean('Invoice Flag'),		
	}
	
	_defaults = {		
		'state': 'pending',
		'entry_mode': 'manual',		
		'flag_invoice': False,		
	}
	
	def onchange_qty(self, cr, uid, ids, qty,inward_qty):		
		rejected_qty = 0.00
		if qty:			
			rejected_qty = inward_qty - qty
		return {'value': {'reject_qty':rejected_qty}}

ch_packing_inward_line()	




