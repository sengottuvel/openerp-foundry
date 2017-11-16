from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
import base64
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_qap_plan(osv.osv):

	_name = "kg.qap.plan"
	_description = "QAP Plan Master"
	
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
					as sam  """ %('kg_qap_plan'))
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
	
		### Basic Info
			
		'name': fields.char('Name', size=128, required=True, select=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'code': fields.char('Code', size=128, required=True),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		
		### Entry Info ###
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
		
		## Child Tables Declaration	
		'line_ids': fields.one2many('ch.dynamic.balancing', 'header_id', "Dynamic Balancing Line"),		
		'line_ids_a':fields.one2many('ch.hydro.pressure', 'header_id', "Hydro Pressure Line"),
		'line_ids_b':fields.one2many('ch.dimentional.inspection', 'header_id', "Dimentional Inspection Line"),
		'line_ids_c':fields.one2many('ch.painting', 'header_id', "Painting Line"),			
		'line_ids_d':fields.one2many('ch.packing', 'header_id', "Packing Line"),			
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.qap.plan', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Name must be unique per Company !!'),
		('code', 'unique(code)', 'Code must be unique per Company !!'),
	]
	
	### Basic Needs
	

	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.name:
			qap_name = rec.name
			name=qap_name.upper()			
			cr.execute(""" select upper(name) from kg_qap_plan where upper(name)  = '%s' """ %(name))
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
			qap_code = rec.code
			code=qap_code.upper()			
			cr.execute(""" select upper(code) from kg_qap_plan where upper(code)  = '%s' """ %(code))
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

	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if not rec.line_ids and not rec.line_ids_a and not rec.line_ids_b and not rec.line_ids_c and not rec.line_ids_d:
			raise osv.except_osv(_('Line details !!'),
				_('Enter the atleast one line entry must !!'))
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
		return super(kg_qap_plan, self).write(cr, uid, ids, vals, context)
	
	
	def _Validation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		special_char = ''.join( c for c in flds.name if  c in '!@#$%^~*{}?+/=' )
		if special_char:
			return False
		return True
	
	def _CodeValidation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		if flds.code:			
			code_special_char = ''.join( c for c in flds.code if  c in '!@#$%^~*{}?+/=' )		
			if code_special_char:
				return False
		return True
		
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_code = str(rec.code)		
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
			
		url = 'http://192.168.1.7/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&Chemical='+rec_code

		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
	
		
	
	_constraints = [
		
		(_name_validate, 'QAP name must be unique !!', ['name']),		
		(_code_validate, 'QAP code must be unique !!', ['code']),
		
		(_Validation, 'Special Character Not Allowed !!!', ['name']),
		(_CodeValidation, 'Special Character Not Allowed !!!', ['Check Code']),		
		
	]
	
	## Module Requirement
	
	
kg_qap_plan()

class ch_dynamic_balancing(osv.osv):
	
	_name = 'ch.dynamic.balancing'
	_description = "Dynamic Balancing Details"
	
	
	_columns = {
		
		'header_id':fields.many2one('kg.qap.plan', 'QAP Name', required=True, ondelete='cascade'), 		
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No', required=True,domain="[('active','=','t')]"),		
		'pattern_name': fields.char('Pattern Name', readonly=True),		
		'min_weight': fields.float('Min Weight(Gms)' ,required=True),
		'max_weight': fields.float('Max Weight(Gms)' ,required=True),
		'remarks':fields.text('Remarks'),		
		
	}	
	
	def onchange_pattern_name(self, cr, uid, ids, pattern_id, context=None):
		
		value = {'pattern_name': ''}
		if pattern_id:
			pro_rec = self.pool.get('kg.pattern.master').browse(cr, uid, pattern_id, context=context)
			value = {'pattern_name': pro_rec.pattern_name}
			
		return {'value': value}
	
	def _check_line_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(""" select pattern_id from ch_dynamic_balancing where pattern_id  = '%s' and header_id = '%s' """ %(entry.pattern_id.id,entry.header_id.id))
		data = cr.dictfetchall()			
		if len(data) > 1:		
			return False
		return True		
		
		
	def _check_line_weight(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])		
		if entry.min_weight <= 0 or entry.max_weight <= 0 or entry.min_weight > entry.max_weight:			
			return False
		return True
	
		
	_constraints = [
		
		(_check_line_weight, 'Dynamic Balancing min and max Zero,negative and Min value greater than Max value not accept', ['Min weight & Max weight']),	   
		(_check_line_duplicates, 'Dynamic Balancing same pattern No. not accept', ['Pattern No']),	   		
	]

	
ch_dynamic_balancing()

class ch_hydro_pressure(osv.osv):
	
	_name = 'ch.hydro.pressure'
	_description = "Hydro Pressure Details"
	
	
	_columns = {
		
		'header_id':fields.many2one('kg.qap.plan', 'QAP Name', required=True, ondelete='cascade'), 		
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No', required=True,domain="[('active','=','t')]"),		
		'moc_id': fields.many2one('kg.moc.master','MOC', required=True,domain="[('active','=','t')]"),		
		'pattern_name': fields.char('Pattern Name', readonly=True),		
		'min_weight': fields.float('Min Weight' ,required=True),
		'max_weight': fields.float('Max Weight' ,required=True),
		'remarks':fields.text('Remarks'),		
		
	}	
	
	def onchange_pattern_name(self, cr, uid, ids, pattern_id, context=None):
		
		value = {'pattern_name': ''}
		if pattern_id:
			pro_rec = self.pool.get('kg.pattern.master').browse(cr, uid, pattern_id, context=context)
			value = {'pattern_name': pro_rec.pattern_name}
			
		return {'value': value}
	
	def _check_line_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(""" select pattern_id from ch_hydro_pressure where pattern_id  = '%s' and header_id = '%s' """ %(entry.pattern_id.id,entry.header_id.id))
		data = cr.dictfetchall()			
		if len(data) > 1:		
			return False
		return True		
		
		
	def _check_line_weight(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])		
		if entry.min_weight <= 0 or entry.max_weight <= 0 or entry.min_weight > entry.max_weight:			
			return False
		return True
	
		
	_constraints = [		
		(_check_line_weight, 'Hydro Pressure min and max Zero,negative and Min value greater than Max value not accept', ['Min weight & Max weight']),	   
		(_check_line_duplicates, 'Hydro Pressure same pattern No. not accept', ['Pattern No']),			
	]
	
ch_hydro_pressure()


class ch_dimentional_inspection(osv.osv):
		
	_name = 'ch.dimentional.inspection'
	_description = "Dimentional Inspection Details"
	
	_columns = {
		
		'header_id':fields.many2one('kg.qap.plan', 'QAP Name', required=True, ondelete='cascade'), 		
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True,domain="[('active','=','t')]"),		
		'remarks':fields.text('Remarks'),	
		
		## Child Tables Declaration	
		'line_ids': fields.one2many('ch.dimentional.details', 'header_id', "Dimention Details Line"),		
		
	}	
	
	def _check_line_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(""" select pump_model_id from ch_dimentional_inspection where pump_model_id  = '%s' and header_id = '%s' """ %(entry.pump_model_id.id,entry.header_id.id))
		data = cr.dictfetchall()			
		if len(data) > 1:		
			return False
		return True	
		
	_constraints = [		
		   
		(_check_line_duplicates, 'Dimentional Inspection same Pump Model not accept', ['Pump Model']),		
		
	]

	
ch_dimentional_inspection()

class ch_dimentional_details(osv.osv):
	
	_name = 'ch.dimentional.details'
	_description = "Dimentional Details"
	
	
	_columns = {
		
		'header_id':fields.many2one('ch.dimentional.inspection', 'Dimentional Inspection Details', required=True, ondelete='cascade'), 		
		'dimentional_details': fields.selection([('suction_face','Suction Face to Delivery Centre'),
												('delivery_centre','Delivery Centre to Shaft End'),
												('delivery_face','Delivery Face to Suction Centre'),
												('leg_face','Leg face to Suction Centre'),
												('coupling_seating','Coupling Seating OD'),
												('suction_flange','Suction Flange Details'),
												('delivery_flange','Delivery Flange Details')],'Dimention Details', required=True),
		'min_weight': fields.float('Min' ,required=True),
		'max_weight': fields.float('Max' ,required=True),		
		'remarks':fields.text('Remarks'),

		
	}	
	
	def _check_line_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(""" select dimentional_details from ch_dimentional_details where dimentional_details  = '%s' and header_id = '%s' """ %(entry.dimentional_details,entry.header_id.id))
		data = cr.dictfetchall()			
		if len(data) > 1:		
			return False
		return True	
	def _check_line_weight(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])		
		if entry.min_weight <= 0 or entry.max_weight <= 0 or entry.min_weight > entry.max_weight:			
			return False
		return True
		
	_constraints = [
		
		   
		(_check_line_duplicates, 'Dimentional Details same Dimention Details selection not accept', ['Dimention Details']),	   
		(_check_line_weight, 'Dimentional Details min and max Zero,negative and Min value greater than Max value not accept', ['Min & Max']),	   
	]

	
ch_dimentional_details()

class ch_painting(osv.osv):
	
	_name = 'ch.painting'
	_description = "Painting Details"
	
	
	_columns = {
		
		'header_id':fields.many2one('kg.qap.plan', 'QAP Name', required=True, ondelete='cascade'), 			
		'paint_color': fields.char('Paint Color',required=True),
		'surface_preparation': fields.char('Surface Preparation'),
		'primer': fields.char('Primer'),
		'primer_ratio': fields.float('Primer Ratio'),
		'inter_mediater': fields.char('Intermediater'),
		'intermediater_ratio': fields.float('Intermediater Ratio'),
		'final_paint': fields.char('Final Paint'),
		'final_paint_ratio': fields.float('Final Paint Ratio'),
		'flim_thickness': fields.float('Flim Thickness(DFT)'),
		'remarks':fields.text('Remarks'),		
		
	}
		
		
	def _check_line_weight(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])		
		if entry.primer_ratio <= 0 or entry.intermediater_ratio <= 0 or entry.final_paint_ratio <= 0 or entry.flim_thickness <= 0:			
			return False
		return True
		
	def _paintcolorValidation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		if flds.paint_color:			
			paint_color_special_char = ''.join( c for c in flds.paint_color if  c in '!@#$%^~*{}?+/=' )		
			if paint_color_special_char:
				return False
		return True
	def _surfacepreparationValidation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		if flds.surface_preparation:			
			surface_preparation_special_char = ''.join( c for c in flds.surface_preparation if  c in '!@#$%^~*{}?+/=' )		
			if surface_preparation_special_char:
				return False
		return True
	def _primerValidation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		if flds.primer:			
			primer_special_char = ''.join( c for c in flds.primer if  c in '!@#$%^~*{}?+/=' )		
			if primer_special_char:
				return False
		return True
	def _finalpaintValidation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		if flds.final_paint:			
			finalpaint_special_char = ''.join( c for c in flds.final_paint if  c in '!@#$%^~*{}?+/=' )		
			if finalpaint_special_char:
				return False
		return True
	def _intermediaterValidation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		if flds.inter_mediater:			
			inter_mediater_special_char = ''.join( c for c in flds.inter_mediater if  c in '!@#$%^~*{}?+/=' )		
			if inter_mediater_special_char:
				return False
		return True
	
		
	_constraints = [		
		(_check_line_weight, 'Painting Details valus Zero and negative not accept', ['Values']),	   
		
		(_paintcolorValidation, 'Special Character Not Allowed !!!', ['Paint Color']),
		(_surfacepreparationValidation, 'Special Character Not Allowed !!!', ['Surface Preparation']),	
		(_primerValidation, 'Special Character Not Allowed !!!', ['Primer']),
		(_finalpaintValidation, 'Special Character Not Allowed !!!', ['Final Paint']),
		(_intermediaterValidation, 'Special Character Not Allowed !!!', ['Intermediater']),
			
	]
	
ch_painting()

class ch_packing(osv.osv):
	
	_name = 'ch.packing'
	_description = "Packing Details"	
	
	_columns = {
		
		'header_id':fields.many2one('kg.qap.plan', 'QAP Name', required=True, ondelete='cascade'), 			
		'packing_id': fields.many2one('kg.packing.type','Packing Type', required=True,domain="[('active','=','t')]"),		
		'wood_type': fields.char('Wood Type',required=True),
		'box_size': fields.char('Box Size (L*B*H)',required=True),
		'remarks':fields.text('Remarks'),		
	}
	
	def _check_line_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(""" select packing_id from ch_packing where packing_id  = '%s' and header_id = '%s' """ %(entry.packing_id.id,entry.header_id.id))
		data = cr.dictfetchall()			
		if len(data) > 1:		
			return False
		return True	
		
	def _woodtypeValidation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		if flds.wood_type:			
			woodtype_special_char = ''.join( c for c in flds.wood_type if  c in '!@#$%^~*{}?+/=' )		
			if woodtype_special_char:
				return False
		return True	
	def _boxsizeValidation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		if flds.box_size:			
			boxsize_special_char = ''.join( c for c in flds.box_size if  c in '!@#$%^~*{}?+/=' )		
			if boxsize_special_char:
				return False
		return True	
		
	_constraints = [		
		(_check_line_duplicates, 'Packing Details same Packing Type not accept', ['Packing Details']),	  
		
		(_woodtypeValidation, 'Special Character Not Allowed !!!', ['Wood Type']), 
		(_boxsizeValidation, 'Special Character Not Allowed !!!', ['Box Size (L*B*H)']), 
				
	]
	
ch_packing()

