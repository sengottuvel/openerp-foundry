from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_machine_shop(osv.osv):

	_name = "kg.machine.shop"
	_description = "SAM MOC Master"
	_rec_name = 'code'
	
	
	def _get_modify(self, cr, uid, ids, field_name, arg, context=None):
		res={}
		ms_line_obj = self.pool.get('ch.machineshop.details')
		ms_line_amend_obj = self.pool.get('ch.machineshop.details.amendment')
		moc_const_ms_obj = self.pool.get('ch.moc.machineshop.details')		
		for item in self.browse(cr, uid, ids, context=None):
			res[item.id] = 'no'
			ms_line_ids = ms_line_obj.search(cr,uid,[('ms_id','=',item.id)])
			ms_line_amend_ids = ms_line_amend_obj.search(cr,uid,[('ms_id','=',item.id)])
			moc_const_ms_ids = moc_const_ms_obj.search(cr,uid,[('ms_id','=',item.id)])					
			if ms_line_ids or ms_line_amend_ids or moc_const_ms_ids:
				res[item.id] = 'yes'		
		return res
	
	_columns = {
			
		'name': fields.char('Name', size=128, required=True, select=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'code': fields.char('Code', size=128, required=True),		
		'uom_id': fields.many2one('product.uom', 'Unit of Measure', required=True, domain="[('dummy_state','=','approved'), ('active','=','t')]"),
		'active': fields.boolean('Active'),	
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'line_ids':fields.one2many('ch.ms.raw.material', 'header_id', "Raw Materials"),
		'line_ids_a':fields.one2many('ch.machine.mocwise', 'header_id', "Machine Shop MOC Wise"),
		
		'csd_code': fields.char('CSD Code No.', size=128),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		'type': fields.selection([('ms','MS Item'),('bot','BOT')],'Type'),
		'od': fields.float('OD'),
		'length': fields.float('Length'),
		'breadth': fields.float('Breadth'),
		'thickness': fields.float('Thickness'),
		'weight': fields.float('Weight'),
		
		'moc_type': fields.selection([('slurry','Slurry'),('non_slurry','Non Slurry'),('both','Both')],'Type', required=True),
		'moc_id': fields.many2one('kg.moc.master','Default MOC', required=True,domain="[('active','=','t')]" ),		
		
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.machine.shop', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':fields.datetime.now,	
		'modify': 'no',
		
	}
	
	_sql_constraints = [	
		
		('code', 'unique(code)', 'Code must be unique per Company !!'),
	]	
	
			
	def _code_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.code:
			division_code = rec.code
			code=division_code.upper()			
			cr.execute(""" select upper(code) from kg_machine_shop where upper(code)  = '%s' """ %(code))
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
		
	def list_moc(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.moc_type == 'both':
			moc_const_obj = self.pool.get('kg.moc.construction').search(cr,uid,([('active','=',True),('state','=','approved')]))				
		else:	
			moc_const_obj = self.pool.get('kg.moc.construction').search(cr,uid,([('type','=',rec.moc_type),('state','=','approved')]))		
		cr.execute(""" delete from ch_machine_mocwise where header_id  = %s """ %(ids[0]))
		for item in moc_const_obj:			
			moc_const_rec = self.pool.get('kg.moc.construction').browse(cr,uid,item)				
			line = self.pool.get('ch.machine.mocwise').create(cr,uid,{
			       'header_id':rec.id,
				   'moc_id':rec.moc_id.id,
				   'code':moc_const_rec.code,
						})				
		return True	
		
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
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
		return super(kg_machine_shop, self).write(cr, uid, ids, vals, context)
		
	
	_constraints = [
		
		(_code_validate, 'MOC code must be unique !!', ['code']),	
	]
	
kg_machine_shop()



class ch_ms_raw_material(osv.osv):
	
	_name = "ch.ms.raw.material"
	_description = "MS Raw Materials Master"
	
	_columns = {
			
		'header_id':fields.many2one('kg.machine.shop', 'MS Entry', required=True, ondelete='cascade'),	
		'product_id': fields.many2one('product.product','Raw Material', required=True),			
		'uom':fields.char('UOM',size=128),		
		'qty':fields.float('Qty'),
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
		return super(ch_ms_raw_material, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		pro_obj = self.pool.get('product.product')
		if vals.get('product_id'):
			uom_rec = pro_obj.browse(cr, uid, vals.get('product_id') )
			uom_name = uom_rec.uom_id.name
			vals.update({'uom': uom_name})
		return super(ch_ms_raw_material, self).write(cr, uid, ids, vals, context)  
	
ch_ms_raw_material()


class ch_machine_mocwise(osv.osv):
	
	_name = "ch.machine.mocwise"
	_description = "Machine Shop MOC Wise"
	
	_columns = {
			
		'header_id':fields.many2one('kg.machine.shop', 'Pattern Entry', required=True, ondelete='cascade'),	
		'moc_id': fields.many2one('kg.moc.master','MOC', required=True,domain="[('active','=','t')]" ),		
		'code':fields.char('MOC Construction Code'),		
		'remarks':fields.text('Remarks'),
		
	}
	
	
	
		
ch_machine_mocwise()

