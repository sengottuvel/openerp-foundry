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

class kg_moc_master(osv.osv):
	
	_name = "kg.moc.master"
	_description = "SAM MOC Master"
	
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
					as sam  """ %('kg_moc_master'))
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
	
	def _production_cost(self, cursor, user, ids, name, arg, context=None):	
		res = {}
		total_pro_cost = 0.00
		for purchase in self.browse(cursor, user, ids, context=context):			
			pro_cost = 0	
			for item in purchase.line_ids:				
				pro_cost_line=item.rate * item.qty			
				pro_cost += pro_cost_line
				total_pro_cost=pro_cost/100			
			res[purchase.id] = total_pro_cost
		return res
		
		
		
	
	_columns = {
			
		'name': fields.char('Name', size=128, required=True, select=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'code': fields.char('Code', size=128, required=True),
		'active': fields.boolean('Active'),
		'rate': fields.float('Design Rate(Rs)', required=True),		
		'pro_cost': fields.function(_production_cost, string='Production Cost(Rs)', type='float'),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'line_ids':fields.one2many('ch.moc.raw.material', 'header_id', "Raw Materials"),
		'line_ids_a':fields.one2many('ch.chemical.chart', 'header_id', "Chemical Chart"),
		'line_ids_b':fields.one2many('ch.mechanical.chart', 'header_id', "Mechanical Chart"),
		'line_ids_c':fields.one2many('ch.fettling.process', 'header_id', "Fettling Process"),
		
		'weight_type': fields.selection([('ci','CI'),('ss','SS'),('non_ferrous','Non-Ferrous')],'Family Type' ,required=True),
		'alias_name': fields.char('Alias Name', size=128),
		'moc_type': fields.selection([('foundry_moc','Foundry MOC'),('purchase_moc','Purchase MOC'),('both','Both')],'Type'),
		'product_id': fields.many2one('product.product','Equivalent Rejection Material'),	
		'moc_cate_id': fields.many2one('kg.moc.category','MS MOC Category',domain="[('state','not in',('reject','cancel')),('type_moc_cate','=','ms')]"),	
		'moc_cate_fetting': fields.many2one('kg.moc.category','Fettling MOC Category',domain="[('state','not in',('reject','cancel')),('type_moc_cate','=','fettling')]"),	
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),	
		
		
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.moc.master', context=c),
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
			cr.execute(""" select upper(name) from kg_moc_master where upper(name)  = '%s' """ %(name))
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
			cr.execute(""" select upper(code) from kg_moc_master where upper(code)  = '%s' """ %(code))
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
		url = 'http://192.168.1.7/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&wo_no='+rec_code	
		
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
		
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		chemical_obj = self.pool.get('kg.chemical.master')		
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
		return super(kg_moc_master, self).write(cr, uid, ids, vals, context)
		
	
	_constraints = [
		#(_Validation, 'Special Character Not Allowed !!!', ['name']),
		#(_CodeValidation, 'Special Character Not Allowed !!!', ['Check Code']),
		(_name_validate, 'MOC name must be unique !!', ['name']),		
		(_code_validate, 'MOC code must be unique !!', ['code']),	
	]
	
kg_moc_master()


class ch_moc_raw_material(osv.osv):
	
	_name = "ch.moc.raw.material"
	_description = "SAM MOC Raw Materials Master"
	
	def _purchase_rate(self, cursor, user, ids, name, arg, context=None):	
		res = {}
		total_pro_cost = 0.00
		for purchase in self.browse(cursor, user, ids, context=context):			
			cursor.execute(""" select purchase_price from ch_brandmoc_rate_details as line

				left join kg_brandmoc_rate header on header.id = line.header_id

				where header.product_id = %s ORDER BY line.id ASC limit 1 """ %(purchase.product_id.id))
			purchase_cost = cursor.fetchone()			
			if purchase_cost is not None:
				if purchase_cost[0]:				
					total_pro_cost = purchase_cost[0]
			else:
				total_pro_cost = 0.00	
			res[purchase.id] = total_pro_cost
		return res
	
	_columns = {
			
		'header_id':fields.many2one('kg.moc.master', 'MOC Entry', required=True, ondelete='cascade'),	
		'product_id': fields.many2one('product.product','Raw Material', required=True),	
		#~ 'rate': fields.related('product_id','latest_price', type='float', string='Rate(Rs)', store=True),
		'rate': fields.function(_purchase_rate, string='Rate(Rs)', type='float', store=True),	
		'uom':fields.char('UOM',size=128),
		'qty':fields.float('Qty',required=True),
		'remarks':fields.text('Remarks'),		
	}
	
	def onchange_uom(self, cr, uid, ids, product_id, context=None):
		
		value = {'uom': ''}
		if product_id:
			uom_rec = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			value = {'uom': uom_rec.uom_id.name}
			
		return {'value': value}
		
	def create(self, cr, uid, vals, context=None):
		pro_obj = self.pool.get('product.product')
		if vals.get('product_id'):		  
			uom_rec = pro_obj.browse(cr, uid, vals.get('product_id') )
			uom_name = uom_rec.uom_id.name
			vals.update({'uom': uom_name})
		return super(ch_moc_raw_material, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):		
		pro_obj = self.pool.get('product.product')
		if vals.get('product_id'):
			uom_rec = pro_obj.browse(cr, uid, vals.get('product_id') )
			uom_name = uom_rec.uom_id.name
			vals.update({'uom': uom_name})
		return super(ch_moc_raw_material, self).write(cr, uid, ids, vals, context)  
	
ch_moc_raw_material()



class ch_chemical_chart(osv.osv):
	
	_name = "ch.chemical.chart"
	_description = "Chemical Chart"
	
	_columns = {
			
		'header_id':fields.many2one('kg.moc.master', 'MOC Entry', required=True, ondelete='cascade'),				
		'chemical_id': fields.many2one('kg.chemical.master','Name', required=True,domain="[('active','=','t')]"),		
		'min':fields.float('Min',required=True,digits_compute=dp.get_precision('Min Value')),		
		'max':fields.float('Max',required=True,digits_compute=dp.get_precision('Max Value')),	
		'range_flag': fields.boolean('Range Limit'),	
	}
	def _check_same_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(""" select chemical_id from ch_chemical_chart where chemical_id  = '%s' and header_id = '%s' """ %(entry.chemical_id.id,entry.header_id.id))
		data = cr.dictfetchall()			
		if len(data) > 1:		
			return False
		return True	
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.min > entry.max:
			return False
		return True
		
	_constraints = [		
			  
		(_check_values, 'Please Check the Min & Max values ,Min value should be less than Max value.!!',['Chemical Chart']),	
		(_check_same_values, 'Please Check the same Chemical Name not allowed..!!',['Chemical Name']),	
		
	   ]
	
ch_chemical_chart()

class ch_mechanical_chart(osv.osv):
	
	_name = "ch.mechanical.chart"
	_description = "Mechanical Chart"
	
	_columns = {
			
		'header_id':fields.many2one('kg.moc.master', 'MOC Entry', required=True, ondelete='cascade'),
		'uom': fields.char('UOM',size=128),						
		'mechanical_id': fields.many2one('kg.mechanical.master','Name', required=True,domain="[('active','=','t')]"),	
		'min':fields.float('Min',required=True,digits_compute=dp.get_precision('Min Value')),
		'max':fields.float('Max',required=True,digits_compute=dp.get_precision('Max Value')),
		'range_flag': fields.boolean('No Max Range'),			
		
	}
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.range_flag == False:			
			if entry.min > entry.max:
				return False
		return True
		
	def onchange_uom_name(self, cr, uid, ids, mechanical_id, context=None):
		
		value = {'uom': ''}
		if mechanical_id:
			uom_rec = self.pool.get('kg.mechanical.master').browse(cr, uid, mechanical_id, context=context)
			value = {'uom': uom_rec.uom.name}
			
		return {'value': value}
		
	def create(self, cr, uid, vals, context=None):
		mech_obj = self.pool.get('kg.mechanical.master')
		if vals.get('mechanical_id'):		  
			uom_rec = mech_obj.browse(cr, uid, vals.get('mechanical_id') )
			uom_name = uom_rec.uom.name
			vals.update({'uom': uom_name})
		return super(ch_mechanical_chart, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		mech_obj = self.pool.get('kg.mechanical.master')
		if vals.get('mechanical_id'):
			uom_rec = mech_obj.browse(cr, uid, vals.get('mechanical_id') )
			uom_name = uom_rec.uom.name
			vals.update({'uom': uom_name})
		return super(ch_mechanical_chart, self).write(cr, uid, ids, vals, context)  
		
	_constraints = [		
			  
		(_check_values, 'Please Check the Min & Max values ,Min value should be less than Max value.!!',['Mechanical Chart']),		
	   ]
	
ch_mechanical_chart()



class ch_fettling_process(osv.osv):
	
	_name = "ch.fettling.process"
	_description = "Fettling Process"
	
	_columns = {
			
		'header_id':fields.many2one('kg.moc.master', 'Fettling Entry', required=True, ondelete='cascade'),							
		'stage_id': fields.many2one('kg.stage.master','Name', required=True,domain="[('active','=','t')]"),	
		'seq_no':fields.integer('Sequence',required=True),
		'remarks':fields.text('Remarks'),
		'flag_ms':fields.boolean('Simultaneously create MS'),
		
	}
	
	
	
	def _seq_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.seq_no:
			seq_no = rec.seq_no					
			cr.execute(""" select seq_no from ch_fettling_process where seq_no  = '%s' and header_id =%s """ %(seq_no,rec.header_id.id))			
			data = cr.dictfetchall()						
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
			
	def _stage_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.stage_id:
			stage_id = rec.stage_id			
			cr.execute(""" select stage_id from ch_fettling_process where stage_id  = '%s' and header_id =%s """ %(stage_id.id,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res		
	
		
	_constraints = [		
			  
		(_seq_validate, 'Please Check Sequence No and should be unique!!!',['Sequence No.']),		
		(_stage_validate, 'Please Check Stage Name and should be unique!!!',['Stage Name']),		
	   ]
	
ch_fettling_process()
