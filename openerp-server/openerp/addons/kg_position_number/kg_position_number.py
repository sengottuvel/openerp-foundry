from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
import base64

class kg_position_number(osv.osv):

	_name = "kg.position.number"
	_description = "Position Number Master"
	
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
					as sam  """ %('kg_position_number'))
					data = cr.dictfetchall()
					if data:
						for var in data:
							data = var
							chk_sql = 'Select COALESCE(count(*),0) as cnt from '+str(data['table_name'])+' where '+data['column_name']+' = '+str(ids[0])
							cr.execute(chk_sql)
							out_data = cr.dictfetchone()
							if out_data:
								if out_data['cnt'] > 0:
									res[h.id] = 'yes'
									return res
								else:
									res[h.id] = 'no'
				else:
					res[h.id] = 'yes'
		return res
	
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
		'item_type': fields.selection([('pattern','Pattern'),('ms','MS'),('bot','BOT')],'Item Type',required=True),
		'position_no': fields.many2one('kg.position.number','Source Position',domain="[('active','=',True),('state','=','approved')]"),
		'line_ids': fields.one2many('ch.kg.position.number','header_id','Operation Configuration',readonly=False,states={'approved':[('readonly',True)]}),
		'copy_flag':fields.boolean('Copy Flag'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No'),
		'pumpmodel_id': fields.many2one('kg.pumpmodel.master','Pump Model'),
		'pattern_name': fields.char('Pattern Name'),
		'ms_id': fields.many2one('kg.machine.shop','MS Code',domain="[('type','=','ms')]"),
		'ms_code': fields.char('MS Name'),
		'bot_id': fields.many2one('kg.machine.shop','BOT Code',domain="[('type','=','bot')]"),
		'bot_code': fields.char('BOT Name'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),
		'drawing_no': fields.char('Drawing No.'),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		
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
		'crt_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'position_type': 'new',
		'copy_flag' : False,
		'modify': 'yes',
		'entry_mode': 'manual',
	}
	
	def onchange_pattern(self, cr, uid, ids,pattern_id):
		value = {'pattern_name': ''}
		if pattern_id:
			pattern_rec = self.pool.get('kg.pattern.master').browse(cr,uid,pattern_id)
			value = {'pattern_name':pattern_rec.pattern_name}
		return {'value':value}
	
	def onchange_ms_id(self, cr, uid, ids,ms_id):
		value = {'ms_id': ''}
		if ms_id:
			ms_rec = self.pool.get('kg.machine.shop').browse(cr,uid,ms_id)
			value = {'ms_code':ms_rec.name}
		return {'value':value}
	
	def onchange_bot_id(self, cr, uid, ids,bot_id):
		value = {'bot_code': ''}
		if bot_id:
			bot_rec = self.pool.get('kg.machine.shop').browse(cr,uid,bot_id)
			value = {'bot_code':bot_rec.name}
		return {'value':value}
	
	def _drawing_no_name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.drawing_no:
			drawing_no = rec.drawing_no
			drawing_nos = drawing_no.upper()
			cr.execute(""" select upper(drawing_no) from kg_position_number where upper(drawing_no)  = '%s' """ %(drawing_nos))
			data = cr.dictfetchall()
			if len(data) > 1:
				raise osv.except_osv(_('Warning !'),_('Drawing No. must be unique !!'))
		
		if rec.name:
			dispatch_name = rec.name
			name=dispatch_name.upper()
			cr.execute(""" select upper(name) from kg_position_number where upper(name)  = '%s' """ %(name))
			data = cr.dictfetchall()
			if len(data) > 1:
				raise osv.except_osv(_('Warning !'),_('Position name must be unique !!'))
		return True
	
	def line_validations(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		source_position_len = source_old_position_len = ''
		new_position_len = 0
		if not rec.line_ids:
			raise osv.except_osv(_('Warning !'),_('Operation is must !!'))
		for line in rec.line_ids:
			if not line.line_ids:
				raise osv.except_osv(_('Warning !'),_('Operation (%s) Configure Dimension Details !!'%(line.operation_id.name)))
			if line.line_ids:
				for item in line.line_ids:
					if item.min_val <= 0 or item.max_val <= 0:
						if item.min_tolerance > 0 or item.max_tolerance > 0:
							raise osv.except_osv(_('Warning !'),_('Operation (%s) Dimension (%s) Min and Max Value should be greater than Zero !!'%(line.operation_id.name,item.dimension_id.name)))
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
					position_line.sc_cost,
					dim.dimension_id,
					dim.description,
					dim.min_val,
					dim.max_val,
					dim.min_tolerance,
					dim.max_tolerance
					from ch_kg_position_number position_line 
					left join kg_position_number header on header.id = position_line.header_id
					left join kg_dimension dim on dim.header_id = position_line.id
					where header.position_type = 'copy' and header.id = %s''',[rec.id])
			source_position_ids = cr.fetchall()
			source_position_len = len(source_position_ids)
			cr.execute('''select 
					position_line.clamping_area,
					position_line.operation_id,
					position_line.stage_id,
					position_line.is_last_operation,
					position_line.total_cost,
					position_line.remark,
					position_line.time_consumption,
					position_line.in_house_cost,
					position_line.sc_cost,
					dim.dimension_id,
					dim.description,
					dim.min_val,
					dim.max_val,
					dim.min_tolerance,
					dim.max_tolerance
					from ch_kg_position_number position_line
					left join kg_dimension dim on dim.header_id = position_line.id 
					where position_line.header_id  = %s''',[rec.position_no.id])
			source_old_position_ids = cr.fetchall()
			source_old_position_len = len(source_old_position_ids)
			cr.execute('''select 

					position_line.clamping_area,
					position_line.operation_id,
					position_line.stage_id,
					position_line.is_last_operation,
					position_line.total_cost,
					position_line.remark,
					position_line.time_consumption,
					position_line.in_house_cost,
					position_line.sc_cost,dim.dimension_id,
					dim.description,
					dim.min_val,
					dim.max_val,
					dim.min_tolerance,
					dim.max_tolerance
					from ch_kg_position_number position_line 
					left join kg_position_number header on header.id = position_line.header_id
					left join kg_dimension dim on dim.header_id = position_line.id
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
					position_line.sc_cost,
					dim.dimension_id,
					dim.description,
					dim.min_val,
					dim.max_val,
					dim.min_tolerance,
					dim.max_tolerance
					from ch_kg_position_number position_line
					left join kg_dimension dim on dim.header_id = position_line.id
					where position_line.header_id  = %s ''',[rec.id,rec.position_no.id])
			repeat_ids = cr.fetchall()
			new_position_len = len(repeat_ids)
		
		if rec.position_type == 'copy':
			obj = self.search(cr,uid,[('position_no','=',rec.position_no.id)])
			if obj:
				for item in obj:
					if rec.id != item:
						obj_rec = self.browse(cr,uid,item)
						cr.execute('''select 
								position_line.clamping_area,
								position_line.operation_id,
								position_line.stage_id,
								position_line.is_last_operation,
								position_line.total_cost,
								position_line.remark,
								position_line.time_consumption,
								position_line.in_house_cost,
								position_line.sc_cost,
								dim.dimension_id,
								dim.description,
								dim.min_val,
								dim.max_val,
								dim.min_tolerance,
								dim.max_tolerance
								from ch_kg_position_number position_line 
								left join kg_position_number header on header.id = position_line.header_id
								left join kg_dimension dim on dim.header_id = position_line.id
								where header.position_type = 'copy' and header.id = %s''',[rec.id])
						source_position_ids = cr.fetchall()
						source_position_len = len(source_position_ids)
						cr.execute('''select 
								position_line.clamping_area,
								position_line.operation_id,
								position_line.stage_id,
								position_line.is_last_operation,
								position_line.total_cost,
								position_line.remark,
								position_line.time_consumption,
								position_line.in_house_cost,
								position_line.sc_cost,
								dim.dimension_id,
								dim.description,
								dim.min_val,
								dim.max_val,
								dim.min_tolerance,
								dim.max_tolerance
								from ch_kg_position_number position_line 
								left join kg_dimension dim on dim.header_id = position_line.id
								where position_line.header_id  = %s''',[obj_rec.id])
						source_old_position_ids = cr.fetchall()
						source_old_position_len = len(source_old_position_ids)
						cr.execute('''select 
								
								position_line.clamping_area,
								position_line.operation_id,
								position_line.stage_id,
								position_line.is_last_operation,
								position_line.total_cost,
								position_line.remark,
								position_line.time_consumption,
								position_line.in_house_cost,
								position_line.sc_cost,dim.dimension_id,
								dim.description,
								dim.min_val,
								dim.max_val,
								dim.min_tolerance,
								dim.max_tolerance
								from ch_kg_position_number position_line 
								left join kg_position_number header on header.id = position_line.header_id
								left join kg_dimension dim on dim.header_id = position_line.id
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
								position_line.sc_cost,dim.dimension_id,
								dim.description,
								dim.min_val,
								dim.max_val,
								dim.min_tolerance,
								dim.max_tolerance
								from ch_kg_position_number position_line 
								left join kg_dimension dim on dim.header_id = position_line.id
								where position_line.header_id  = %s ''',[rec.id,obj_rec.id])
						repeat_ids = cr.fetchall()
						new_position_len = len(repeat_ids)
		if source_position_len == source_old_position_len == new_position_len:
			raise osv.except_osv(_('Warning !'),_('Change anyone details !!'))
		else:
			pass
		return True
	
	_constraints = [
		
		(_drawing_no_name_validate, 'Drawing No and Name must be unique !!', ['Drawing No and Name']),
		
	]
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid,'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Warning !'),_('Enter the remarks in Cancel remarks field !!'))
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
			raise osv.except_osv(_('Warning !'),_('Change Position No. !!'))
		self.write(cr, uid, ids[0], {
									'copy_flag': True,
									'notes':rec.position_no.notes,
									})		
									
		return True
	
	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			
			self.line_validations(cr,uid,ids)
			
			operation_sql = """ select count(id) from ch_kg_position_number where header_id = %s and is_last_operation = True """%(rec.id)
			cr.execute(operation_sql)
			operation_data = cr.dictfetchall()
			if not operation_data[0]['count'] == 1:
				raise osv.except_osv(_('Warning !'),_('Select anyone operation is last operation !!'))
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True
	
	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			
			self.line_validations(cr,uid,ids)
			
			operation_sql = """ select count(id) from ch_kg_position_number where header_id = %s and is_last_operation = True """%(rec.id)
			cr.execute(operation_sql)
			operation_data = cr.dictfetchall()
			if not operation_data[0]['count'] == 1:
				raise osv.except_osv(_('Warning !'),_('Please select anyone operation is last operation !!'))
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			if rec.remark:
				self.write(cr, uid, ids, {'state': 'reject','ap_rej_user_id': uid,'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Warning !'),_('Enter the remarks in rejection remark field !!'))
		return True
	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []
		for rec in self.browse(cr,uid,ids):
			if rec.state not in ('draft','cancel'):
				raise osv.except_osv(_('Delete access denied !'),_('Unable to delete. Draft entry only you can delete !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_position_number, self).write(cr, uid, ids, vals, context)
	
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_code = str(rec.name)
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
		
		url = 'http://10.100.9.32/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&position_number='+rec_code
		
		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  	 : url
			   }
	
kg_position_number()

class ch_kg_position_number(osv.osv):
	
	_name = 'ch.kg.position.number'
	
	_columns = {
		
		'header_id':fields.many2one('kg.position.number', 'Position No', required=True, ondelete='cascade'),
		'operation_id': fields.many2one('kg.operation.master','Operation', required=True,domain="[('state','not in',('reject','cancel'))]"),
		'name': fields.char('Operation Name'),
		'is_last_operation': fields.boolean('Is Last Operation'),
		'time_consumption':fields.float('Time Consumption(Hrs)'),
		'in_house_cost': fields.float('In-house Cost/hr'),
		'total_cost': fields.float('Total Cost'),
		'sc_cost': fields.float('Sub-Contractor Cost'),
		'stage_id': fields.many2one('kg.stage.master','Stage', required=True,domain="[('state','not in',('reject','cancel'))]"),
		'clamping_area': fields.char('Clamping Area', required=True), 	
		'remark': fields.text('Remarks'),
		## child declaration
		'line_ids': fields.one2many('kg.dimension','header_id','Dimension'),
		'line_ids_a': fields.one2many('ch.moccategory.mapping','header_id','MOC Category'),
	}
	
	def onchange_total_cost(self, cr, uid, ids, total_cost,time_consumption,in_house_cost, context=None):
		value = {'total_cost': '','time_consumption': '','in_house_cost': ''}
		total_cost = 0.00
		total_cost = time_consumption * in_house_cost
		value = {'total_cost': total_cost}
		return {'value': value}
	
	def onchange_name(self, cr, uid, ids, operation_id,stage_id, context=None):
		value = {'name': ''}
		name = ''
		if operation_id and stage_id:
			operation_rec = self.pool.get('kg.operation.master').browse(cr,uid,operation_id)
			stage_rec = self.pool.get('kg.stage.master').browse(cr,uid,stage_id)
			name = str(operation_rec.name) + '-' + str(stage_rec.name)
		return {'value': {'name': name}}
	
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
			raise osv.except_osv(_('Warning'), _('Max Weight of (%s) should be greater than Min Weight in Dimensional Details !!')%(rec.dimension_id.name))
		return True	
	
	_constraints = [
		
		(_check_total,' ',['Minimum Value']),
		
		]
	
kg_dimension()

class ch_moccategory_mapping(osv.osv):
	
	_name = 'ch.moccategory.mapping'
	
	_columns = {
		
		'header_id':fields.many2one('ch.kg.position.number', 'Position No', required=True, ondelete='cascade'),
		'moc_cate_id': fields.many2one('kg.moc.category','MOC Category', required=True,domain="[('state','not in',('reject','cancel'))]"),
		'rate': fields.float('Rate' ,required=True),
		'remark': fields.text('Remarks'),
		
	}
	
	def _check_rate_moc(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.rate <= 0.00:
			raise osv.except_osv(_('Warning !'),_('Rate (%s) should be greater than zero !!')%(rec.moc_cate_id.name))
		if rec.moc_cate_id:
			cr.execute(""" select moc_cate_id from ch_moccategory_mapping where moc_cate_id  = '%s' and header_id =%s """ %(rec.moc_cate_id.id,rec.header_id.id))
			data = cr.dictfetchall()
			if len(data) > 1:
				raise osv.except_osv(_('Warning !'),_('MOC Category (%s) should be unique !!')%(rec.moc_cate_id.name))
		return True
	
	_constraints = [
		
		(_check_rate_moc,' ',['Rate and MOC']),
		
		]
	
ch_moccategory_mapping()
