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
			
		'name': fields.char('Position No', required=True, select=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'code': fields.char('Code', size=128),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'position_type': fields.selection([('new','NEW'),('copy','COPY')],'Type',required=True),
		'position_no': fields.many2one('kg.position.number','Source Position',domain="[('active','=',True),('state','=','approved')]"),
		'line_ids': fields.one2many('ch.kg.position.number','header_id','Operation Configuration',readonly=False,states={'approved':[('readonly',True)]}),
		'copy_flag':fields.boolean('Copy Flag'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No'),
		'pumpmodel_id': fields.many2one('kg.pumpmodel.master','Pump Model'),
		'pattern_name': fields.char('Pattern Name'),
		
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
		
	def onchange_pattern(self, cr, uid, ids,pattern_id):
		value = {'pattern_name': ''}
		if pattern_id:
			pattern_rec = self.pool.get('kg.pattern.master').browse(cr,uid,pattern_id)
			value = {'pattern_name':pattern_rec.pattern_name}
		return {'value':value}
		
			
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
		
		if rec.name == rec.position_no.name:
			raise osv.except_osv(_('Warning !!'),
				_('Kindly Change Position No. !!'))
			
		self.write(cr, uid, ids[0], {
									'copy_flag': True,
									#~ 'name':rec.position_no.name,
									'notes':rec.position_no.notes,
									
									})		
									
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		
		operation_sql = """ select count(id) from ch_kg_position_number where header_id = %s and is_last_operation = True """%(rec.id)
		cr.execute(operation_sql)		
		operation_data = cr.dictfetchall()
		
		if not operation_data[0]['count'] == 1:
			raise osv.except_osv(_('Warning!'),
				_('Please select anynoe operation is last operation !!'))
		
		if rec.position_type == 'copy':
			
			cr.execute('''select 
					position_line.clamping_area,
					position_line.operation_id,
					position_line.stage_id,
					position_line.is_last_operation,
					position_line.total_cost,
					position_line.remark,
					position_line.time_consumption,
					position_line.in_house_cost,
					position_line.sc_cost
					from ch_kg_position_number position_line 
					left join kg_position_number header on header.id  = position_line.header_id
					where header.position_type = 'copy' and header.id = %s''',[rec.id])
			source_position_ids = cr.fetchall()
			source_position_len = len(source_position_ids)
			print"dddddddllll",source_position_len
			cr.execute('''select 
					position_line.clamping_area,
					position_line.operation_id,
					position_line.stage_id,
					position_line.is_last_operation,
					position_line.total_cost,
					position_line.remark,
					position_line.time_consumption,
					position_line.in_house_cost,
					position_line.sc_cost
					from ch_kg_position_number position_line 
					where position_line.header_id  = %s''',[rec.position_no.id])
			source_old_position_ids = cr.fetchall()
			source_old_position_len = len(source_old_position_ids)	
			print"ddddssssssss",source_old_position_len
			cr.execute('''select 

					position_line.clamping_area,
					position_line.operation_id,
					position_line.stage_id,
					position_line.is_last_operation,
					position_line.total_cost,
					position_line.remark,
					position_line.time_consumption,
					position_line.in_house_cost,
					position_line.sc_cost
					from ch_kg_position_number position_line 
					left join kg_position_number header on header.id  = position_line.header_id
					where header.position_type = 'copy' and header.id = %s

					INTERSECT

					select 
					position_line.clamping_area,
					position_line.operation_id,
					position_line.stage_id,
					position_line.is_last_operation,
					position_line.total_cost,
					position_line.remark,
					position_line.time_consumption,
					position_line.in_house_cost,
					position_line.sc_cost
					from ch_kg_position_number position_line 
					where position_line.header_id  = %s ''',[rec.id,rec.position_no.id])
			repeat_ids = cr.fetchall()
			new_position_len = len(repeat_ids)
			print"ddddddddddddddd",new_position_len
			pos_dup = ''
			if new_position_len  == source_position_len == source_old_position_len:
				pos_dup = 'yes'
			
			if pos_dup == 'yes':
				raise osv.except_osv(_('Warning!'),
								_('Same Operation Details are already exist !!'))
		####################
		if rec.position_type == 'copy':
			
			obj = self.search(cr,uid,[('position_no','=',rec.position_no.id)])
			if obj:
				for item in obj:
					if rec.id != item:
						obj_rec = self.browse(cr,uid,item)
						print"aaaaaaaaaaaaaa",obj_rec.id
						
						cr.execute('''select 
								position_line.clamping_area,
								position_line.operation_id,
								position_line.stage_id,
								position_line.is_last_operation,
								position_line.total_cost,
								position_line.remark,
								position_line.time_consumption,
								position_line.in_house_cost,
								position_line.sc_cost
								from ch_kg_position_number position_line 
								left join kg_position_number header on header.id  = position_line.header_id
								where header.position_type = 'copy' and header.id = %s''',[rec.id])
						source_position_ids = cr.fetchall()
						source_position_len = len(source_position_ids)
						print"source_position_len",source_position_len
						cr.execute('''select 
								position_line.clamping_area,
								position_line.operation_id,
								position_line.stage_id,
								position_line.is_last_operation,
								position_line.total_cost,
								position_line.remark,
								position_line.time_consumption,
								position_line.in_house_cost,
								position_line.sc_cost
								from ch_kg_position_number position_line 
								where position_line.header_id  = %s''',[obj_rec.id])
						source_old_position_ids = cr.fetchall()
						source_old_position_len = len(source_old_position_ids)	
						print"source_old_position_len",source_old_position_len
						cr.execute('''select 

								position_line.clamping_area,
								position_line.operation_id,
								position_line.stage_id,
								position_line.is_last_operation,
								position_line.total_cost,
								position_line.remark,
								position_line.time_consumption,
								position_line.in_house_cost,
								position_line.sc_cost
								from ch_kg_position_number position_line 
								left join kg_position_number header on header.id  = position_line.header_id
								where header.position_type = 'copy' and header.id = %s

								INTERSECT

								select 
								position_line.clamping_area,
								position_line.operation_id,
								position_line.stage_id,
								position_line.is_last_operation,
								position_line.total_cost,
								position_line.remark,
								position_line.time_consumption,
								position_line.in_house_cost,
								position_line.sc_cost
								from ch_kg_position_number position_line 
								where position_line.header_id  = %s ''',[rec.id,obj_rec.id])
						repeat_ids = cr.fetchall()
						new_position_len = len(repeat_ids)
						print"new_position_len",new_position_len
						pos_dup = ''
						if new_position_len == source_position_len == source_old_position_len:
							pos_dup = 'yes'
						print"pos_duppos_dup",pos_dup
						if pos_dup == 'yes':
							raise osv.except_osv(_('Warning!'),
											_('Same Operation Details are already exist !!'))
								
			
								
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		
		operation_sql = """ select count(id) from ch_kg_position_number where header_id = %s and is_last_operation = True """%(rec.id)
		cr.execute(operation_sql)		
		operation_data = cr.dictfetchall()
		
		if not operation_data[0]['count'] == 1:
			raise osv.except_osv(_('Warning!'),
				_('Please select anynoe operation is last operation !!'))
				
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
	
	def _check_line(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if not rec.line_ids:			
			return False
		return True	
	
	_constraints = [
		#(_Validation, 'Special Character Not Allowed !!!', ['Check Name']),
		#(_CodeValidation, 'Special Character Not Allowed !!!', ['Check Code']),
		(_name_validate, 'Position No must be unique !!', ['Position No']),		
		(_code_validate, 'Position code must be unique !!', ['code']),		
		#~ (_check_line,'You can not save this with out Operation Details !',['line_ids']),
		
	]
	
kg_position_number()



class ch_kg_position_number(osv.osv):
	
	_name = 'ch.kg.position.number'
	
	_columns = {
		
		'header_id':fields.many2one('kg.position.number', 'Position No', required=True, ondelete='cascade'),  
		'operation_id': fields.many2one('kg.operation.master','Operation', required=True,domain="[('state','not in',('reject','cancel'))]"), 		
		'is_last_operation': fields.boolean('Is Last Operation'), 
		'time_consumption':fields.float('Time Consumption(Hrs)'),
		'in_house_cost': fields.float('In-house Cost/hr'),
		'total_cost': fields.float('Total Cost'),
		'sc_cost': fields.float('Sub-Contractor Cost'),
		'stage_id': fields.many2one('kg.stage.master','Stage', required=True,domain="[('state','not in',('reject','cancel'))]"), 		
		'clamping_area': fields.char('Clamping Area', required=True), 	
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
		'dimension_id': fields.many2one('kg.dimension.master','Dimension', required=True,domain="[('state','not in',('reject','cancel'))]"),
		'description': fields.char('Description', required=True), 		
		'min_val': fields.float('Minimum Value'), 
		'max_val': fields.float('Maximum Value'), 
		'min_tolerance': fields.integer('Min Tolerance(%)'), 
		'max_tolerance': fields.integer('Maximum Tolerance(%)'), 
		'remark': fields.text('Remarks'),
		
	}
	
	def _check_total(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
			
		if rec.max_val < rec.min_val:
			return False					
		return True
	
	def _check_max_val(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.max_val <= 0:
			return False					
		return True
	
	def _check_min_val(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.min_val <= 0:
			return False					
		return True
	
	def _check_dimension(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])		
		cr.execute("""select id,dimension_id from kg_dimension where header_id = %s"""%(rec.header_id.id))
		line_data = cr.dictfetchall()
		for line in line_data :			
			for sub_line in line_data:				
				if line['id'] == sub_line['id']:					
					pass
				else:
					if (line['dimension_id'] == sub_line['dimension_id']):
						return False
		return True
			
	_constraints = [
	
		(_check_total,'Maximum Value Should Be Greater Than Minimum Value !',['Minimum Value']),
		(_check_dimension, 'System not allow to save duplicate Dimension value !',['Dimension']),	
		(_check_max_val, 'Maximum Value Should Be Greater Than Zero Value !',['Maximum']),	
		(_check_min_val, 'Minimum Value Should Be Greater Than Zero Value !',['Minimum']),	
		
		]
		
kg_dimension()
