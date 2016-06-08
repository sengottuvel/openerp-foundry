from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_position_number(osv.osv):

	_name = "kg.position.number"
	_description = "Position Number Master"
	
	"""
	def _get_modify(self, cr, uid, ids, field_name, arg, context=None):
		res={}
		enq_obj = self.pool.get('purchase.order')			
		for item in self.browse(cr, uid, ids, context=None):
			res[item.id] = 'no'
			enq_ids = enq_obj.search(cr,uid,[('mode_of_dispatch','=',item.id)])			
			if enq_ids:
				res[item.id] = 'yes'		
		return res
	"""
	_columns = {
			
		'name': fields.char('Position No', size=128, required=True, select=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'code': fields.char('Code', size=128),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'position_type': fields.selection([('new','NEW'),('copy','COPY')],'Type',required=True),
		'position_no': fields.many2one('kg.position.number','Source Position',domain="[('active','=',True)]"),
		'line_ids': fields.one2many('ch.kg.position.number','header_id','Operation Configuration',readonly=False,states={'approved':[('readonly',True)]}),
		'copy_flag':fields.boolean('Copy Flag'),		
		
		#'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),
		
		### Entry Info ###
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
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.position.number', context=c),
		'active': True,		
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date': fields.datetime.now,	
		'position_type': 'new',
		'copy_flag' : False,
		#'modify': 'no',
	}
	
	_sql_constraints = [
	
		#~ ('name', 'unique(name)', 'Name must be unique!!'),
		('code', 'unique(code)', 'Code must be unique!!'),
	]
	
	"""def _Validation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		name_special_char = ''.join( c for c in flds.name if  c in '!@#$%^~*{}?+/=' )		
		if name_special_char:
			return False		
		return True	
		
	def _CodeValidation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])	
		if flds.code:		
			code_special_char = ''.join( c for c in flds.code if  c in '!@#$%^~*{}?+/=' )		
			if code_special_char:
				return False
		return True		"""
		
	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.name:
			dispatch_name = rec.name
			name=dispatch_name.upper()			
			cr.execute(""" select upper(name) from kg_position_number where upper(name)  = '%s' """ %(name))
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
			dispatch_code = rec.code
			code=dispatch_code.upper()			
			cr.execute(""" select upper(code) from kg_position_number where upper(code)  = '%s' """ %(code))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res	
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True
	
	def copy_position(self, cr, uid, ids, context=None):
		
		rec = self.browse(cr,uid,ids[0])
		position_line_obj = self.pool.get('ch.kg.position.number')
		dimension_obj = self.pool.get('kg.dimension')
				
		cr.execute(""" delete from ch_kg_position_number where header_id  = %s """ %(ids[0]))
				
		for position_line_item in rec.position_no.line_ids:	
			vals = {
				'header_id' : ids[0]
				}			
			copy_rec = position_line_obj.copy(cr, uid, position_line_item.id, vals, context) 
			cr.execute(""" delete from kg_dimension where header_id  = %s """ %(copy_rec))
			for dimension_line_item in position_line_item.line_ids:	
				vals = {
					'header_id' : copy_rec
					}			
				copy_recs = dimension_obj.copy(cr, uid, dimension_line_item.id, vals, context) 
			
		self.write(cr, uid, ids[0], {
									'copy_flag': True,
									'name':rec.position_no.name,
									'notes':rec.position_no.notes,
									
									})		
									
		return True
		
	def _pump_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.name:
			pump_name = rec.pump_model_id						
			cr.execute(""" select * from kg_bom where pump_model_id  = '%s' and state != '%s' """ %(pump_name.id,'reject'))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
		
	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
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
		return super(kg_position_number, self).write(cr, uid, ids, vals, context)
		
	
	_constraints = [
		#(_Validation, 'Special Character Not Allowed !!!', ['Check Name']),
		#(_CodeValidation, 'Special Character Not Allowed !!!', ['Check Code']),
		#~ (_name_validate, 'Position name must be unique !!', ['name']),		
		(_code_validate, 'Position code must be unique !!', ['code']),		
		
	]
	
kg_position_number()



class ch_kg_position_number(osv.osv):
	
	_name = 'ch.kg.position.number'
	
	_columns = {
		
		'header_id':fields.many2one('kg.position.number', 'Position No', required=True, ondelete='cascade'),  
		'operation_id': fields.many2one('kg.operation.master','Operation', required=True), 		
		'is_last_operation': fields.boolean('Is Last Operation'), 
		'time_consumption':fields.float('Time Consumption'),
		'in_house_cost': fields.float('In-House Cost'),
		'total_cost': fields.float('Total Cost'),
		'sc_cost': fields.float('Sub-Contractor Cost'),
		'remark': fields.text('Remarks'),
		'line_ids': fields.one2many('kg.dimension','header_id','Dimension'),
	}
	
	def onchange_total_cost(self, cr, uid, ids, total_cost,time_consumption,in_house_cost, context=None):
		value = {'total_cost': '','time_consumption': '','in_house_cost': ''}
		total_cost = 0.00
		total_cost = time_consumption * in_house_cost
		value = {'total_cost': total_cost}
		return {'value': value}
		
ch_kg_position_number()

class kg_dimension(osv.osv):
	
	_name = 'kg.dimension'
	
	_columns = {
		
		'header_id':fields.many2one('ch.kg.position.number', 'Position No', required=True, ondelete='cascade'),  
		'dimension_id': fields.many2one('kg.dimension.master','Dimension', required=True), 		
		'stage_id': fields.many2one('kg.stage.master','Stage', required=True), 		
		'clamping_area': fields.char('Clamping Area', required=True), 		
		'description': fields.char('Description', required=True), 		
		'min_val': fields.float('Minimum Value'), 
		'max_val': fields.float('Maximum Value'), 
		'remark': fields.text('Remarks'),
		
	}
	
kg_dimension()
