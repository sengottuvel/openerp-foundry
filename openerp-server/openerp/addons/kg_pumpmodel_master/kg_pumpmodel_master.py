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

class kg_pumpmodel_master(osv.osv):

	_name = "kg.pumpmodel.master"
	_description = "SAM PumpModel Master"
	
	
	def _get_modify(self, cr, uid, ids, field_name, arg, context=None):
		res={}		
		stock_line_obj = self.pool.get('ch.stock.inward.details')			
		for item in self.browse(cr, uid, ids, context=None):
			res[item.id] = 'no'			
			stock_line_ids = stock_line_obj.search(cr,uid,[('pump_model_id','=',item.id)])
			
			if stock_line_ids:
				res[item.id] = 'yes'		
		return res
	
	_columns = {
			
		'name': fields.char('Name', size=128, required=True, select=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'code': fields.char('Code', size=128, required=True),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		
		'line_ids':fields.one2many('ch.vo.mapping', 'header_id', "VO Mapping"),
		'line_ids_a':fields.one2many('ch.alpha.value', 'header_id', "Alpha Value"),
		'line_ids_b':fields.one2many('ch.delivery.pipe', 'header_id', "Delivery Pipe"),
		
		'alias_name': fields.char('Alias Name', size=128),
		'make_by': fields.char('Make By', size=128),
		'delivery_lead': fields.integer('Delivery Lead Time(Weeks)', size=128),
		'type': fields.selection([('vertical','Vertical'),('horizontal','Horizontal'),('others','Others')],'Type'),
		'category_id': fields.many2one('kg.pump.category', 'Product Category'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),	
		'pump_mode': fields.selection([('only_spares','Only Spares'),('full_pump','Full Product')],'Product Mode',required=True),	
		
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
		
		######### CRM Data Added ###########
		
		'impeller_type': fields.selection([('open','Open'),('semi_open','Semi Open'),('close','Closed')],'Impeller Type',required=True),
		'crm_type': fields.selection([('pull_out','End Suction Back Pull Out'),('split_case','Split Case'),('multistage','Multistage'),('twin_casing','Twin Casing'),('single_casing','Single Casing'),('self_priming','Self Priming'),('vo_vs4','VO-VS4'),('vg_vs5','VG-VS5')],'Type',required=True),
		'impeller_number': fields.integer('Impeller Number of vanes', required=True),
		'impeller_dia_max': fields.float('Impeller Dia Max mm', required=True),
		'impeller_dia_min': fields.float('Impeller Dia Min mm', required=True),
		'maximum_allowable_soild': fields.float(' Maximum Allowable Solid Size - mm', required=True),
		'max_allowable_test': fields.float('Max Allowable Test Pressure', required=True),
		'number_of_stages': fields.integer('Number of stages', required=True),
		
		'pump_size': fields.char('Size-SuctionX Delivery(mm)', required=True),
		'bearing_no': fields.char('Bearing No', required=True),
		'bearing_qty': fields.float('Bearing qty', required=True),
		'sealing_water_pressure': fields.float('Sealing Water Pressure', required=True),
		'series_id': fields.many2one('kg.pumpseries.master', 'Series',required=True,domain = [('state','not in',('reject','cancel'))]),
		'suction': fields.float('Suction', required=True),
		'discharge': fields.float('Discharge', required=True),
		'stage_type': fields.selection([('single','Single'),('multi','Multi'),('double','Double')],'Stage Type',required=True),
		'rotation_type': fields.selection([('clock_wise','Clock Wise'),('anti_clock_wise','Anti Clock Wise')],'Rotation',required=True),
		'packing_type': fields.selection([('ptfe','PTFE'),('gp','GP'),('mechanical_seal','Mechanical Seal'),('dynamic_seal','Dynamic seal')],'Packing'),
		'wear_ring_type': fields.selection([('yes','Yes'),('no','NO')],'Wear Ring',required=True),
		'lubrication_type': fields.selection([('grease','Grease'),('oil','Oil')],'Lubrication',required=True),
		'feet_location': fields.selection([('base','Base'),('center_line','Center Line')],'Feet Location',required=True),
		'suction_orientation': fields.selection([('axial','Axial'),('side','Side')],'Suction Orientation',required=True),
		'discharge_orientation': fields.selection([('top_side','Top-side'),('bottom_side','Bottom-Side'),('top','Top'),('top_center_line','Top Center line')],'Discharge Orientation',required=True),
		'companion_flange': fields.char('Companion Flange'),
		'employee_id': fields.many2one('res.users', 'User Type'),
		'max_solid_size': fields.char('Max Solid size'),
		'sealing_water_capacity': fields.float('Sealing Water Capacity - m3/hr'),
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.pumpmodel.master', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':fields.datetime.now,	
		'delivery_lead':10,	
		'modify': 'no',
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Name must be unique per Company !!'),
		('code', 'unique(code)', 'Code must be unique per Company !!'),
	]
	
	"""def _Validation(self, cr, uid, ids, context=None):
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
		return True		"""
		
	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.name:
			division_name = rec.name
			name=division_name.upper()			
			cr.execute(""" select upper(name) from kg_pumpmodel_master where upper(name)  = '%s' """ %(name))
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
			division_code = rec.code
			code=division_code.upper()			
			cr.execute(""" select upper(code) from kg_pumpmodel_master where upper(code)  = '%s' """ %(code))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res	
		
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_code = str(rec.code)		
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
		
		url = 'http://192.168.1.7/DMS/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&pummod='+rec_code	
		
		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
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
		line = rec.line_ids	
		if rec.line_ids_b:			
			cr.execute(""" select count from
				( select count(delivery_size),delivery_size from ch_delivery_pipe where header_id = %s group by delivery_size ) as dup
				where count > 1 """ %(rec.id))
			data = cr.dictfetchall()			
			if len(data) > 0:
				raise osv.except_osv(_('Delivery Pipe Check !!'),
				_('Not allow same Delivery Size!!'))
			else:
				pass
			
		if rec.line_ids_a:			
			cr.execute(""" select count from
				( select count(alpha_type),alpha_type from ch_alpha_value where header_id = %s group by alpha_type ) as dup
				where count > 1 """ %(rec.id))
			data = cr.dictfetchall()			
			if len(data) > 0:
				raise osv.except_osv(_('Alpha Value Check !!'),
				_('Not allow same Alpha type!!'))
			else:
				pass	
		if rec.line_ids:
								
			cr.execute(""" select count from
				( select count(rpm),rpm from ch_vo_mapping where header_id = %s group by rpm ) as dup
				where count > 1 """ %(rec.id))
			data = cr.dictfetchall()			
			if len(data) > 0:
				raise osv.except_osv(_('VO Mapping Check !!'),
				_('Not allow same RPM in VO Mapping!!'))
			else:
				pass		
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
		return super(kg_pumpmodel_master, self).write(cr, uid, ids, vals, context)
		
	
	_constraints = [
		#(_Validation, 'Special Character Not Allowed !!!', ['name']),
		#(_CodeValidation, 'Special Character Not Allowed !!!', ['Check Code']),
		(_name_validate, 'PumpModel name must be unique !!', ['name']),		
		(_code_validate, 'PumpModel code must be unique !!', ['code']),	
	]
	
kg_pumpmodel_master()




class ch_alpha_value(osv.osv):
	
	_name = "ch.alpha.value"
	_description = "Alpha Value"
	
	_columns = {
			
		'header_id':fields.many2one('kg.pumpmodel.master', 'Alpha Entry', required=True, ondelete='cascade'),							
		'alpha_type': fields.selection([('a','A'),('a1','A1'),('a2','A2')],'Alpha Type', required=True),
		'alpha_value':fields.float('Alpha Value',required=True),
		'remarks':fields.text('Remarks'),	
		
	}
	
ch_alpha_value()



class ch_delivery_pipe(osv.osv):
	
	_name = "ch.delivery.pipe"
	_description = "Delivery Pipe"
	
	_columns = {
			
		'header_id':fields.many2one('kg.pumpmodel.master', 'Delivery Entry', required=True, ondelete='cascade'),	
		'delivery_size':fields.integer('Delivery Size',required=True),
		'b_value':fields.float('Bend B',required=True),
		'h_value':fields.float('Above BP H',required=True),
		'remarks':fields.text('Remarks'),	
		
	}
	
ch_delivery_pipe()

