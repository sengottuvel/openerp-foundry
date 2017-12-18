from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_equipment_master(osv.osv):

	_name = "kg.equipment.master"
	_description = "Equipment master"
	_rec_name = "code"
	
	def _get_modify(self, cr, uid, ids, field_name, arg,  context=None):
		res={}		
		if field_name == 'modify':
			for h in self.browse(cr, uid, ids, context=None):
				res[h.id] = 'no'
				if h.state == 'approved':
					cr.execute(""" select * from 
					(SELECT tc.table_schema, tc.constraint_name, tc.table_name, kcu.column_name, ccu.table_name
					AS foreign_table_name, ccu.column_name AS foreign_column_name
					FROM information_schema.table_constraints tc
					JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
					JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
					WHERE constraint_type = 'FOREIGN KEY'
					AND ccu.table_name='%s')
					as sam  """ %('kg_equipment_master'))
					data = cr.dictfetchall()	
					if data:
						for var in data:
							data = var
							chk_sql = 'Select COALESCE(count(*),0) as cnt from '+str(data['table_name'])+' where '+data['column_name']+' = '+str(ids[0])							
							cr.execute(chk_sql)			
							out_data = cr.dictfetchone()
							if out_data:								
								if out_data['cnt'] > 0:
									res[h.id] = 'no'
									return res
								else:
									res[h.id] = 'yes'
				else:
					res[h.id] = 'no'	
		return res	
	
	_columns = {
	
		## Basic Info
			
		'name': fields.char('Name', size=128, required=True, select=True),		
		'code': fields.char('Code', size=128, required=True),		
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		
		### Entry Info ###
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
		'equ_type': fields.selection([('gig','Gig'),('cage','Cage'),('dye','Dye')],'Type', required=True),
		
		## Child Tables Declaration
		'line_ids':fields.one2many('ch.equipment.gig', 'header_id', "Gig Details"),
		'line_ids_a':fields.one2many('ch.equipment.cage', 'header_id', "Cage Details"),
		'line_ids_b':fields.one2many('ch.equipment.dye', 'header_id', "Dye Details"),
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.equipment.master', context=c),
		'active': True,
		'state': 'draft',
		#~ 'equ_type': 'gig',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		
	}
		
		
	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.name:
			equ_name = rec.name
			name=equ_name.upper()			
			cr.execute(""" select upper(name) from kg_equipment_master where upper(name)  = '%s' """ %(name))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
			
	def _code_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.code:
			equ_code = rec.code
			code=equ_code.upper()			
			cr.execute(""" select upper(code) from kg_equipment_master where upper(code)  = '%s' """ %(code))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
		
	def _line_item_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.equ_type == 'gig':
			if not rec.line_ids:
				raise osv.except_osv(_('Warning'), _('Empty Line Items are not allowed for Type Gig !!'))
		if rec.equ_type == 'cage':
			if not rec.line_ids_a:
				raise osv.except_osv(_('Warning'), _('Empty Line Items are not allowed for Type Cage !!'))
		if rec.equ_type == 'dye':
			if not rec.line_ids_b:
				raise osv.except_osv(_('Warning'), _('Empty Line Items are not allowed for Type Dye !!'))
		return True
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])			
		if rec.state == 'approved':
			if rec.cancel_remark:
				self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Cancel remark is must !!'),
					_('Enter the remarks in Cancel remarks field !!'))
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])		
		if rec.state == 'draft':
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])		
		if rec.state == 'confirmed':
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			if rec.remark:
				self.write(cr, uid, ids, {'state': 'reject','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Rejection remark is must !!'),
					_('Enter the remarks in rejection remark field !!'))
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state not in ('draft','cancel'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_equipment_master, self).write(cr, uid, ids, vals, context)
		
	
	_constraints = [
		
		(_name_validate, 'Equipment name must be unique !!', ['name']),		
		(_code_validate, 'Equipment code must be unique !!', ['code']),		
		(_line_item_validate, ' ', ['Line Items Validations']),		
		
	]
	
kg_equipment_master()



class ch_equipment_gig(osv.osv):
	
	_name = "ch.equipment.gig"
	_description = "Gig Process"
	
	_columns = {
			
		'header_id':fields.many2one('kg.equipment.master', 'Equipment Entry', required=True, ondelete='cascade'),							
		'position_id': fields.many2one('kg.position.number','Position No.', required=True,domain="[('state','=','approved')]"),	
		'item_code':fields.char('Item Code'),
		'item_name':fields.char('Item Name'),		
		'remarks':fields.text('Remarks'),		
		
	}

	def onchange_item(self, cr, uid, ids, position_id, context=None):
		
		value = {'item_code': '','item_name':''}
		if position_id:
			item_code = ''
			item_name = ''
			pos_rec = self.pool.get('kg.position.number').browse(cr, uid, position_id, context=context)
			if pos_rec.pattern_id:
				item_name = pos_rec.pattern_id.name
				item_code = pos_rec.pattern_name
			elif pos_rec.ms_id:
				item_name = pos_rec.ms_id.name
				item_code = pos_rec.ms_code
			elif pos_rec.bot_id:
				item_name = pos_rec.bot_id.name
				item_code = pos_rec.bot_code
			value = {'item_code': item_code,'item_name':item_name}
		else:
			pass			
		return {'value': value}
				
	def _position_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.position_id:					
			cr.execute(""" select position_id from ch_equipment_gig where position_id  = '%s' and header_id =%s 				
			""" %(rec.position_id.id,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
	
		
	_constraints = [						
		(_position_validate, 'Please Check Position Name should be unique!!!',['Position Name']),			
	   ]
	
ch_equipment_gig()


class ch_equipment_cage(osv.osv):
	
	_name = "ch.equipment.cage"
	_description = "Cage Process"
	
	_columns = {
			
		'header_id':fields.many2one('kg.equipment.master', 'Equipment Entry', required=True, ondelete='cascade'),		
		'size':fields.char('Size', required=True),	
		'remarks':fields.text('Remarks'),		
		
	}

			
	def _size_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.size:					
			cr.execute(""" select size from ch_equipment_cage where size  = '%s' and header_id =%s 				
			""" %(rec.size,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
	
		
	_constraints = [						
		(_size_validate, 'Please Check Size should be unique!!!',['Size']),			
	   ]
	
ch_equipment_cage()


class ch_equipment_dye(osv.osv):
	
	_name = "ch.equipment.dye"
	_description = "Dye Process"
	
	_columns = {
			
		'header_id':fields.many2one('kg.equipment.master', 'Equipment Entry', required=True, ondelete='cascade'),		
		'drawing_no':fields.char('Drawing No.', required=True),	
		'remarks':fields.text('Remarks'),		
		
	}

			
	def _drawing_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.drawing_no:					
			cr.execute(""" select drawing_no from ch_equipment_dye where drawing_no  = '%s' and header_id =%s 				
			""" %(rec.drawing_no,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
	
		
	_constraints = [						
		(_drawing_validate, 'Please Check Drawing No. should be unique!!!',['Drawing No.']),			
	   ]
	
ch_equipment_dye()






