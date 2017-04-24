from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re 
dt_time = lambda * a: time.strftime('%m/%d/%Y %H:%M:%S')

ENTRY_TYPE = [
   ('sc','SC'),
   ('internal','Internal')  
]

class kg_drawing_dc(osv.osv):

	_name = "kg.drawing.dc"
	_description = "Drawing DC"
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
		'contact_person': fields.char('Contact Person', size=128),		
		'vehicle_detail': fields.char('Vehicle Detail'),
		'entry_type': fields.selection([('sc','SC'),('internal','Internal')],'Type', required=True),
		'flag_inward': fields.boolean('Inward Flag'),
		
		## Child Tables Declaration	
			
		'line_ids': fields.one2many('ch.drawing.details','header_id','Drawing details'),  	
		'line_ids_a': fields.one2many('ch.equipment.details','header_id','Equipment details'),  	
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_drawing_dc', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),		
		'annexure_date' : lambda * a: time.strftime('%Y-%m-%d'),		
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,			
		'flag_inward': False,			
		'state': 'draft',		
		'entry_mode': 'manual',
		'entry_type': 'sc'			
	}
	
	def onchange_contractor(self, cr, uid, ids, contractor_id):
		if contractor_id:
			contractor_rec = self.pool.get('res.partner').browse(cr, uid, contractor_id)
		return {'value': {'contact_person':contractor_rec.contact_person,'phone':contractor_rec.phone  }}
	
	
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':		
			sc_wo_line_obj = self.pool.get('ch.fettling.wo.line')			
			special_char = ''.join( c for c in entry.vehicle_detail if  c in '!@#$%^~*{}?+/=_-><?/`' )
			if entry.annexure_no <= 0:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to Annexure 17 No. Zero and negative values!!'))			
			if len(entry.line_ids) == 0:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to without Drawing details line items !!'))	
			if len(entry.line_ids_a) == 0:
				raise osv.except_osv(_('Warning!'),
					_('System not allow to without Equipment details line items !!'))				
			if special_char:
				raise osv.except_osv(_('Vehicle Detail'),
					_('Special Character Not Allowed !!!'))						
			if entry.line_ids:
				for line_item in entry.line_ids:											
					if line_item.qty <= 0:
						raise osv.except_osv(_('Warning!'),
									_('System not allow to save zero and negative values !!'))
					self.pool.get('ch.drawing.details').write(cr,uid,line_item.id,{'pending_qty':line_item.qty})
			if entry.line_ids_a:
				for equ_line_item in entry.line_ids_a:											
					if equ_line_item.qty <= 0:
						raise osv.except_osv(_('Warning!'),
									_('System not allow to save zero and negative values !!'))								
					self.pool.get('ch.equipment.details').write(cr,uid,equ_line_item.id,{'pending_qty':equ_line_item.qty})					
					
			
			### Sequence Number Generation  ###		
			if entry.name == '' or entry.name == False:
				seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.drawing.dc')])
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
		return super(kg_drawing_dc, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_drawing_dc, self).write(cr, uid, ids, vals, context)
		
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
	
kg_drawing_dc()

class ch_drawing_details(osv.osv):
	
	_name = "ch.drawing.details"
	_description = "Drawing Details Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.drawing.dc','DC Entry', required=True, ondelete='cascade'),
		'contractor_id': fields.related('header_id','contractor_id', type='many2one', relation='res.partner', string='Contractor Name', store=True, readonly=True),
		'entry_type': fields.related('header_id','entry_type', type='selection', selection=ENTRY_TYPE, string='Type', store=True, readonly=True),
		'position_id': fields.many2one('kg.position.number','Position No.', required=True,domain="[('state','=','approved')]"),	
		'drawing_no':fields.char('Drawing No.'),
		'item_code':fields.char('Item Code'),
		'item_name':fields.char('Item Name'),				
		'qty': fields.integer('Quantity', required=True),
		'pending_qty': fields.integer('Pending Qty'),						
		'remarks': fields.text('Remarks'),					
	}
	
	_defaults = {			
		'qty': 1,			
	}
		
	def onchange_item(self, cr, uid, ids, position_id, context=None):
		
		value = {'item_code': '','item_name':'','drawing_no':''}
		if position_id:
			pos_rec = self.pool.get('kg.position.number').browse(cr, uid, position_id, context=context)
			drawing_no = pos_rec.drawing_no
			if pos_rec.pattern_id:
				item_name = pos_rec.pattern_id.name
				item_code = pos_rec.pattern_name
			elif pos_rec.ms_id:
				item_name = pos_rec.ms_id.name
				item_code = pos_rec.ms_code
			elif pos_rec.bot_id:
				item_name = pos_rec.bot_id.name
				item_code = pos_rec.bot_code
			value = {'item_code': item_code,'item_name':item_name,'drawing_no':drawing_no}
		else:
			pass			
		return {'value': value}
		
	def _position_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.position_id:					
			cr.execute(""" select position_id from ch_drawing_details where position_id  = '%s' and header_id =%s 				
			""" %(rec.position_id.id,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
	
		
	_constraints = [						
		(_position_validate, 'Please Check Position No should be unique!!!',['Position No.']),			
	   ]
	

ch_drawing_details()	


class ch_equipment_details(osv.osv):
	
	_name = "ch.equipment.details"
	_description = "Equipment Details Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.drawing.dc','DC Entry', required=True, ondelete='cascade'),
		'contractor_id': fields.related('header_id','contractor_id', type='many2one', relation='res.partner', string='Contractor Name', store=True, readonly=True),
		'entry_type': fields.related('header_id','entry_type', type='selection', selection=ENTRY_TYPE, string='Type', store=True, readonly=True),
		'equ_id': fields.many2one('kg.equipment.master','Equipment Code', required=True,domain="[('state','=','approved')]"),		
		'equ_name':fields.char('Equipment Name'),			
		'qty': fields.integer('Quantity', required=True),
		'pending_qty': fields.integer('Pending Qty'),						
		'remarks': fields.text('Remarks'),					
	}
	
	_defaults = {			
		'qty': 1,			
	}
	
	def onchange_item(self, cr, uid, ids, equ_id, context=None):		
		value = {'equ_name': ''}
		if equ_id:
			equ_rec = self.pool.get('kg.equipment.master').browse(cr, uid, equ_id, context=context)
			equ_name = equ_rec.name			
			value = {'equ_name': equ_name}
		else:
			pass			
		return {'value': value}
		
	def _equ_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.equ_id:					
			cr.execute(""" select equ_id from ch_equipment_details where equ_id  = '%s' and header_id =%s 				
			""" %(rec.equ_id.id,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
	
		
	_constraints = [						
		(_equ_validate, 'Please Check Equipment Code should be unique!!!',['Equipment Code']),			
	   ]
	

ch_equipment_details()	



class kg_drawing_inward(osv.osv):

	_name = "kg.drawing.inward"
	_description = "drawing Inward"
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
		'entry_type': fields.selection([('sc','SC'),('internal','Internal')],'Type', required=True),		
		
		## Child Tables Declaration	
		
		'dc_sc_ids': fields.many2many('kg.drawing.dc','m2m_dc_sc_details' , 'inward_id', 'dc_id', 'DC No.',
		 domain="[('flag_inward','=',False),('entry_type','=',entry_type),('contractor_id','=',contractor_id)]"),
		'dc_internal_ids': fields.many2many('kg.drawing.dc','m2m_dc_internal_details' , 'inward_id', 'dc_id', 'DC No.',
		 domain="[('flag_inward','=',False),('entry_type','=',entry_type),('division_id','=',division_id)]"),
			
		'line_ids': fields.one2many('ch.inward.drawing.details','header_id','Drawing details'),  	
		'line_ids_a': fields.one2many('ch.inward.equipment.details','header_id','Equipment details'),  	
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_drawing_inward', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),		
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,			
		'state': 'draft',		
		'entry_mode': 'manual',	
		'entry_type': 'sc'		
	}
	
	def onchange_contractor(self, cr, uid, ids, contractor_id):
		if contractor_id:
			contractor_rec = self.pool.get('res.partner').browse(cr, uid, contractor_id)
		return {'value': {'contact_person':contractor_rec.contact_person,'phone':contractor_rec.phone  }}
	
	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		inward_drawing_obj = self.pool.get('ch.inward.drawing.details')			
		inward_equ_obj = self.pool.get('ch.inward.equipment.details')			
		del_drawing_sql = """ delete from ch_inward_drawing_details where header_id=%s """ %(ids[0])
		cr.execute(del_drawing_sql)	
		del_equ_sql = """ delete from ch_inward_equipment_details where header_id=%s """ %(ids[0])
		cr.execute(del_equ_sql)	
		
		if entry.dc_sc_ids:
		
			for item in entry.dc_sc_ids:					
				for draw_line in item.line_ids:					
					if draw_line.pending_qty > 0:						
						vals = {
							
							'header_id': entry.id,
							'dc_drawing_id': draw_line.id,
							'position_id': draw_line.position_id.id,
							'drawing_no': draw_line.drawing_no,
							'item_code': draw_line.item_code,
							'item_name': draw_line.item_name,
							'qty': draw_line.pending_qty,
							'dc_qty': draw_line.pending_qty,
							'remarks': draw_line.remarks,							
							
						}
						
						inward_drawing_id = inward_drawing_obj.create(cr, uid,vals)							
				for equ_line in item.line_ids_a:					
					if equ_line.pending_qty > 0:						
						vals = {
							
							'header_id': entry.id,
							'dc_equ_id': equ_line.id,
							'equ_id': equ_line.equ_id.id,
							'equ_name': equ_line.equ_name,							
							'qty': equ_line.pending_qty,
							'dc_qty': equ_line.pending_qty,
							'remarks': equ_line.remarks,							
							
						}
						
						inward_equ_id = inward_equ_obj.create(cr, uid,vals)		
						
		if entry.dc_internal_ids:
		
			for item in entry.dc_internal_ids:					
				for draw_line in item.line_ids:					
					if draw_line.pending_qty > 0:						
						vals = {
							
							'header_id': entry.id,
							'dc_drawing_id': draw_line.id,
							'position_id': draw_line.position_id.id,
							'drawing_no': draw_line.drawing_no,
							'item_code': draw_line.item_code,
							'item_name': draw_line.item_name,
							'qty': draw_line.pending_qty,
							'dc_qty': draw_line.pending_qty,
							'remarks': draw_line.remarks,							
							
						}
						
						inward_drawing_id = inward_drawing_obj.create(cr, uid,vals)							
				for equ_line in item.line_ids_a:					
					if equ_line.pending_qty > 0:						
						vals = {
							
							'header_id': entry.id,
							'dc_equ_id': equ_line.id,
							'equ_id': equ_line.equ_id.id,
							'equ_name': equ_line.equ_name,							
							'qty': equ_line.pending_qty,
							'dc_qty': equ_line.pending_qty,
							'remarks': equ_line.remarks,							
							
						}
						
						inward_equ_id = inward_equ_obj.create(cr, uid,vals)	
			
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':						
			#~ if len(entry.line_ids) == 0:
				#~ raise osv.except_osv(_('Warning!'),
					#~ _('System not allow to without Drawing details line items !!'))	
			#~ if len(entry.line_ids_a) == 0:
				#~ raise osv.except_osv(_('Warning!'),			
					#~ _('System not allow to without Equipment details line items !!'))	
			dc_ids = []		
			for draw_line_item in entry.line_ids:
				dc_id = draw_line_item.dc_drawing_id.header_id.id
				dc_ids.append(dc_id)				
				if draw_line_item.qty <= 0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save zero and negative values !!'))									
				if draw_line_item.qty > draw_line_item.dc_drawing_id.pending_qty:
					raise osv.except_osv(_('Warning!'),
								_('System not allow Excess qty !!'))					
				self.pool.get('ch.drawing.details').write(cr,uid,draw_line_item.dc_drawing_id.id,{'pending_qty':draw_line_item.dc_drawing_id.pending_qty - draw_line_item.qty})
								
			for equ_line_item in entry.line_ids_a:	
				dc_id = equ_line_item.dc_equ_id.header_id.id	
				dc_ids.append(dc_id)	
				if equ_line_item.qty <= 0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save zero and negative values !!'))									
				if equ_line_item.qty > equ_line_item.dc_equ_id.pending_qty:
					raise osv.except_osv(_('Warning!'),
								_('System not allow Excess qty !!'))					
				self.pool.get('ch.equipment.details').write(cr,uid,equ_line_item.dc_equ_id.id,{'pending_qty':equ_line_item.dc_equ_id.pending_qty - equ_line_item.qty})
				
		
			
			for dc_item in dc_ids:					
				cr.execute(""" select id,pending_qty from ch_drawing_details where pending_qty  > 0 and header_id = %s 				
				""" %(dc_item))
				draw_data = cr.dictfetchall()
				
				cr.execute(""" select id,pending_qty from ch_equipment_details where pending_qty  > 0 and header_id =%s 				
				""" %(dc_item))
				equ_data = cr.dictfetchall()
					
				if draw_data or equ_data:
					pass		
				else:
					self.pool.get('kg.drawing.dc').write(cr,uid,dc_item,{'flag_inward':True})			
			
			### Sequence Number Generation  ###		
			if entry.name == '' or entry.name == False:
				seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.drawing.inward')])
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
		return super(kg_drawing_inward, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_drawing_inward, self).write(cr, uid, ids, vals, context)
		
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
	
kg_drawing_inward()



class ch_inward_drawing_details(osv.osv):
	
	_name = "ch.inward.drawing.details"
	_description = "Drawing Inward Details Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.drawing.inward','Inward Entry', required=True, ondelete='cascade'),	
		'dc_drawing_id': fields.many2one('ch.drawing.details','DC Drawing ID'),	
		'position_id': fields.many2one('kg.position.number','Position No.', required=True,domain="[('state','=','approved')]"),	
		'drawing_no':fields.char('Drawing No.'),
		'item_code':fields.char('Item Code'),
		'item_name':fields.char('Item Name'),				
		'qty': fields.integer('Quantity', required=True),
		'dc_qty': fields.integer('DC Pending Qty'),						
		'remarks': fields.text('Remarks'),					
	}		
	

ch_inward_drawing_details()	


class ch_inward_equipment_details(osv.osv):
	
	_name = "ch.inward.equipment.details"
	_description = "Equipment Inward Details Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.drawing.inward','Inward Entry', required=True, ondelete='cascade'),
		'dc_equ_id': fields.many2one('ch.equipment.details','DC Equipment ID'),		
		'equ_id': fields.many2one('kg.equipment.master','Equipment Code', required=True,domain="[('state','=','approved')]"),		
		'equ_name':fields.char('Equipment Name'),			
		'qty': fields.integer('Quantity', required=True),
		'dc_qty': fields.integer('DC Pending Qty'),						
		'remarks': fields.text('Remarks'),					
	}	
	

ch_inward_equipment_details()	
