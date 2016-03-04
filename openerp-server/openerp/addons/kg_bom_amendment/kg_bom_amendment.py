from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
import netsvc
import time
import openerp.exceptions
import datetime
from datetime import date


class kg_bom_amendment(osv.osv):
	
	_name = 'kg.bom.amendment'  
	
	
	_columns = {
	
		'amend_no': fields.char('Amendment No', size=128,select=True,readonly=True),
		'line_ids': fields.one2many('ch.bom.line.amendment', 'header_id', "BOM Line"),	  
		'line_ids_a':fields.one2many('ch.machineshop.details.amendment', 'header_id', "Machine Shop Line"),
		'line_ids_b':fields.one2many('ch.bot.details.amendment', 'header_id', "BOT Line"),
		'line_ids_c':fields.one2many('ch.consu.details.amendment', 'header_id', "Consumable Line"),		
		'bom_id': fields.many2one('kg.bom', 'BOM Name',domain="[('state','=','approved'), ('active','=','t')]",required=True),
		'entry_date':fields.date('Amendment Date',required=True),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved')],'Status', readonly=True),   
		
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model',domain="[('state','=','approved'), ('active','=','t')]",readonly=True),   
		'uom': fields.char('Unit of Measure', readonly=True), 
		'remarks':fields.text('Remarks'),
		'qty': fields.integer('Qty', size=128,readonly=True),
		'revision': fields.integer('Revision',readonly=True),
		'notes': fields.text('Notes',readonly=True),
		'remark': fields.text('Approve/Reject'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
			  
		'active':fields.boolean('Active'),  
		'load_bom':fields.boolean('Load BOM'), 	
		
		### Entry Info ###
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),	
		'ap_date': fields.datetime('Approved/Reject Date', readonly=True),
		'ap_user_id': fields.many2one('res.users', 'Approved/Reject By', readonly=True),	
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
	}
	
	_defaults = {
	'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.bom.amendment', context=c),
	'entry_date': lambda * a: time.strftime('%Y-%m-%d'),
	'active': True,  
	'load_bom': False,  	
	'state': 'draft',
	}
	
	
	def _duplicate_validate(self, cr, uid,ids, context=None):
		obj = self.browse(cr,uid,ids[0])		
		bom_obj=self.pool.get('kg.bom')		
		amend_obj=self.pool.get('kg.bom.amendment')
		
		draft_amends=amend_obj.search(cr,uid,[('bom_id','=',obj.bom_id.id),('state','!=','confirmed')])
		if len(draft_amends) > 1:
			return False
		else:
			return True
		
	_constraints = [
		
		(_duplicate_validate, 'Please approve Draft BOM for proceed another Amendment!!', ['']),		
		
		
	]
			
	
	def bom_amendment(self, cr, uid, ids, context=None):		
		
		obj = self.browse(cr,uid,ids[0])		
		bom_obj=self.pool.get('kg.bom')		
		amend_obj=self.pool.get('kg.bom.amendment')
		amend_bom_id = amend_obj.browse(cr,uid,obj.bom_id.id)		
		bom = obj.bom_id			
		cr.execute(""" select id from kg_bom where state in ('draft','confirmed','approved') and name = '%s' """ %(obj.bom_id.name))
		data = cr.dictfetchall()					
		total_amends=amend_obj.search(cr,uid,[('bom_id','=',obj.bom_id.id)])			
		draft_amends=amend_obj.search(cr,uid,[('bom_id','=',obj.bom_id.id),('state','!=','confirmed')])
		
		
		if obj.bom_id.id:						
			vals = {
						'amend_no': self.pool.get('ir.sequence').get(cr, uid, 'kg.bom.amendment') or '/',
						'bom_id': bom.id,
						'pump_model_id' : bom.pump_model_id.id, 
						'uom': bom.uom,
						'qty': bom.qty,
						'entry_date': obj.entry_date,
						'remarks': bom.remarks,
						'remark': bom.remark,
						'notes': bom.notes,
						'state': 'draft',
						'load_bom': True,
						'revision' : bom.revision + 1,
						'user_id': uid,
						'update_user_id': uid,						
						'crt_date': time.strftime('%Y-%m-%d %H:%M:%S'),
						'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),
					}
			
			self.pool.get('kg.bom.amendment').write(cr,uid,ids,vals)			
			amend_id = obj.id			
			amend_foundry_line_obj = self.pool.get('ch.bom.line.amendment')
			bom_foundry_lines=bom.line_ids
			
			amend_machineshop_line_obj = self.pool.get('ch.machineshop.details.amendment')
			bom_machineshop_lines=bom.line_ids_a
			
			
			amend_bot_line_obj = self.pool.get('ch.bot.details.amendment')
			bom_bot_lines=bom.line_ids_b
			
			amend_consu_line_obj = self.pool.get('ch.consu.details.amendment')
			bom_consu_lines=bom.line_ids_c
			
			for bom_foundry_line in bom_foundry_lines:				
				
				amend_foundry_line_id = amend_foundry_line_obj.create(cr,uid,
					{
						'header_id':obj.id,
						'pos_no': bom_foundry_line.pos_no,
						'pattern_id': bom_foundry_line.pattern_id.id,
						'pattern_name':bom_foundry_line.pattern_name,
						'remarks':bom_foundry_line.remarks,
						'qty': bom_foundry_line.qty,
						'state' : bom_foundry_line.state,
					})
					
			for bom_machineshop_line in bom_machineshop_lines:	
				
				amend_machineshop_line_id = amend_machineshop_line_obj.create(cr,uid,
					{
						'header_id':obj.id,
						'ms_id': bom_machineshop_line.ms_id.id,
						'name': bom_machineshop_line.name,
						'qty':bom_machineshop_line.qty,
						'remarks':bom_machineshop_line.remarks,
						
					})	
			for bom_bot_line in bom_bot_lines:		
				
				amend_bot_line_id = amend_bot_line_obj.create(cr,uid,
					{
						'header_id':obj.id,
						'product_temp_id': bom_bot_line.product_temp_id.id,
						'code': bom_bot_line.code,
						'qty':bom_bot_line.qty,
						'remarks':bom_bot_line.remarks,
						
					})	
					
			for bom_consu_line in bom_consu_lines:	
				
				amend_consu_line_id = amend_consu_line_obj.create(cr,uid,
					{
						'header_id':obj.id,
						'product_temp_id': bom_consu_line.product_temp_id.id,
						'code': bom_consu_line.code,
						'qty':bom_consu_line.qty,
						'remarks':bom_consu_line.remarks,						
					})	
						
		
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):		
		rec = self.browse(cr,uid,ids[0])
		bom_obj = self.pool.get('kg.bom.amendment')		
		bom_foundry_lines=rec.line_ids			 
		machine_shop_lines=rec.line_ids_a			 
		bot_lines=rec.line_ids_b			 
		consu_lines=rec.line_ids_c	

		
		for bom_foundry_item in bom_foundry_lines:			
			if bom_foundry_item.qty == 0:
				raise osv.except_osv(
					_('Warning !'),
					_('Please foundry items zero qty not accepted!!')) 					
		for machine_shop_item in machine_shop_lines:			
			if machine_shop_item.qty == 0:
				raise osv.except_osv(
					_('Warning !'),
					_('Please machine shop items zero qty not accepted!!'))
		for bot_item in bot_lines:			
			if bot_item.qty == 0:
				raise osv.except_osv(
					_('Warning !'),
					_('Please BOT zero qty not accepted!!')) 
		
		for consu_item in consu_lines:			
			if consu_item.qty == 0:
				raise osv.except_osv(
					_('Warning !'),
					_('Please Consumable items zero qty not accepted!!'))		 
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid,'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),	})
		return True
		
	def entry_approve(self, cr, uid, ids, context=None):		
		
		obj = self.browse(cr,uid,ids[0])		
		bom_obj=self.pool.get('kg.bom.amendment')		
		amend_obj=self.pool.get('kg.bom')		
		amend_bom_id = amend_obj.browse(cr,uid,obj.bom_id.id)			
		bom = obj.id	
		approve_amends_ids=amend_obj.search(cr,uid,[('name','=',obj.bom_id.name),('state','=','approved')])		
		approve_rec = amend_obj.browse(cr,uid,approve_amends_ids[0])		
		if approve_amends_ids:
			approve_vals = {
				'state': 'expire',
				'active': False,				
				'expire_user_id': uid,
				'expire_date': time.strftime('%Y-%m-%d %H:%M:%S')
				
			}
		self.pool.get('kg.bom').write(cr,uid,approve_rec.id,approve_vals)
		if obj.bom_id.id:		
						
			vals = {	
			
						'name':obj.bom_id.name,
						'pump_model_id' : obj.pump_model_id.id, 
						'uom': obj.uom,
						'qty': obj.qty,
						'type': 'amendment',
						'remarks': obj.remarks,
						'remark': obj.remark,
						'notes': obj.notes,
						'state': 'approved',						
						'revision' : obj.revision,
						'confirm_user_id': uid,
						'update_user_id': uid,
						'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),
						'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),
						'ap_rej_user_id': uid,
						'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S'),
					}
			
			new_bom = self.pool.get('kg.bom').create(cr,uid,vals,context=None)			
			amend_id = obj.id	
			amend_foundry_line_obj = self.pool.get('ch.bom.line')
			bom_foundry_lines=obj.line_ids
			
			amend_machineshop_line_obj = self.pool.get('ch.machineshop.details')
			bom_machineshop_lines=obj.line_ids_a			
			
			amend_bot_line_obj = self.pool.get('ch.bot.details')
			bom_bot_lines=obj.line_ids_b
			
		
			
			amend_consu_line_obj = self.pool.get('ch.consu.details')
			bom_consu_lines=obj.line_ids_c		
			for bom_foundry_line in bom_foundry_lines:				
				amend_foundry_line_id = amend_foundry_line_obj.create(cr,uid,
					{
						'header_id':new_bom,
						'pos_no': bom_foundry_line.pos_no,
						'pattern_id': bom_foundry_line.pattern_id.id,
						'pattern_name':bom_foundry_line.pattern_name,
						'remarks':bom_foundry_line.remarks,
						'qty': bom_foundry_line.qty,
						'state' : bom_foundry_line.state,
					})
					
			for bom_machineshop_line in bom_machineshop_lines:	
				
				amend_machineshop_line_id = amend_machineshop_line_obj.create(cr,uid,
					{
						'header_id':new_bom,
						'ms_id': bom_machineshop_line.ms_id.id,
						'name': bom_machineshop_line.name,
						'qty':bom_machineshop_line.qty,
						'remarks':bom_machineshop_line.remarks,
						
					})	
			for bom_bot_line in bom_bot_lines:			
				
				amend_bot_line_id = amend_bot_line_obj.create(cr,uid,
					{
						'header_id':new_bom,
						'product_temp_id': bom_bot_line.product_temp_id.id,
						'code': bom_bot_line.code,
						'qty':bom_bot_line.qty,
						'remarks':bom_bot_line.remarks,
						
					})	
					
		
					
			for bom_consu_line in bom_consu_lines:	
				
				amend_consu_line_id = amend_consu_line_obj.create(cr,uid,
					{
						'header_id':new_bom,
						'product_temp_id': bom_consu_line.product_temp_id.id,
						'code': bom_consu_line.code,
						'qty':bom_consu_line.qty,
						'remarks':bom_consu_line.remarks,						
					})	
		self.write(cr, uid, ids, {'state': 'approved',
					'ap_user_id': uid,
					'update_user_id': uid,
					'ap_date': time.strftime('%Y-%m-%d %H:%M:%S'),
					'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),		
				})	
		
		return True

	def create(self, cr, uid, vals, context=None):
		return super(kg_bom_amendment, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		
		return super(kg_bom_amendment, self).write(cr, uid, ids, vals, context)
	
kg_bom_amendment()



class ch_bom_line_amendment(osv.osv):
	
	_name = 'ch.bom.line.amendment'
	
	
	_columns = {
		
		
		'header_id':fields.many2one('kg.bom.amendment', 'BOM Entry', required=True, ondelete='cascade'),	
		'pos_no': fields.integer('Position No'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No', required=True,domain="[('state','=','approved')]"), 
		'pattern_name': fields.char('Pattern Name', required=True), 
		'remarks':fields.text('Remarks'),
		'qty': fields.integer('Qty',required=True,),
		'state':fields.selection([('draft','Draft'),('approve','Approved')],'Status'),
		
		
	}
	
	
	_defaults = {
	
	'state':'draft',
	'qty': 1,
	  
	}
	
	
	
	def onchange_pattern_name(self, cr, uid, ids, pattern_id, context=None):
		
		value = {'pattern_name': ''}
		if pattern_id:
			pro_rec = self.pool.get('kg.pattern.master').browse(cr, uid, pattern_id, context=context)
			value = {'pattern_name': pro_rec.pattern_name}
			
		return {'value': value}
		
		
	def create(self, cr, uid, vals, context=None):
		pattern_obj = self.pool.get('kg.pattern.master')
		if vals.get('pattern_id'):		  
			pattern_rec = pattern_obj.browse(cr, uid, vals.get('pattern_id') )
			pattern_name = pattern_rec.pattern_name
			vals.update({'pattern_name': pattern_name})
		return super(ch_bom_line_amendment, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		pattern_obj = self.pool.get('kg.pattern.master')
		if vals.get('pattern_id'):
			pattern_rec = pattern_obj.browse(cr, uid, vals.get('pattern_id') )
			pattern_name = pattern_rec.pattern_name
			vals.update({'pattern_name': pattern_name})
		return super(ch_bom_line_amendment, self).write(cr, uid, ids, vals, context)  
		
	

	
ch_bom_line_amendment()


class ch_machineshop_details_amendment(osv.osv):

	_name = "ch.machineshop.details.amendment"
	_description = "BOM machineshop Details Amendment"
	
	
	_columns = {
	
		'header_id':fields.many2one('kg.bom.amendment', 'BOM', ondelete='cascade',required=True),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', ondelete='cascade',required=True),
		'name':fields.char('Item Name', size=128),	  
		'qty': fields.integer('Qty', required=True),
		'remarks':fields.text('Remarks'),   
	
	}   
	
	def onchange_machineshop_name(self, cr, uid, ids, ms_id, context=None):
		
		value = {'name': ''}
		if ms_id:
			pro_rec = self.pool.get('kg.machine.shop').browse(cr, uid, ms_id, context=context)
			value = {'name': pro_rec.name}
			
		return {'value': value}
		
	def create(self, cr, uid, vals, context=None):	  
		ms_obj = self.pool.get('kg.machine.shop')
		if vals.get('ms_id'):		   
			ms_rec = ms_obj.browse(cr, uid, vals.get('ms_id') )
			ms_name = ms_rec.name		   
			vals.update({'name':ms_name })
		return super(ch_machineshop_details_amendment, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		ms_obj = self.pool.get('kg.machine.shop')
		if vals.get('ms_id'):		   
			ms_rec = ms_obj.browse(cr, uid, vals.get('ms_id') )
			ms_name = ms_rec.name		   
			vals.update({'name':ms_name })
		return super(ch_machineshop_details_amendment, self).write(cr, uid, ids, vals, context)   

ch_machineshop_details_amendment()

class ch_bot_details_amendment(osv.osv):
	
	_name = "ch.bot.details.amendment"
	_description = "BOM BOT Details Amendment"  
	
	_columns = {
	
		'header_id':fields.many2one('kg.bom.amendment', 'BOM', ondelete='cascade',required=True),
		'product_temp_id':fields.many2one('product.product', 'Item Name',domain = [('type','=','bot')], ondelete='cascade',required=True),
		'code':fields.char('Item Code', size=128),	  
		'qty': fields.integer('Qty', required=True),
		'remarks':fields.text('Remarks'),   
	
	}
	
	def onchange_bot_code(self, cr, uid, ids, product_temp_id, context=None):	   
		value = {'code': ''}
		if product_temp_id:
			pro_rec = self.pool.get('product.product').browse(cr, uid, product_temp_id, context=context)
			value = {'code': pro_rec.product_code}		  
		return {'value': value}
		
	def create(self, cr, uid, vals, context=None):	  
		product_obj = self.pool.get('product.product')
		if vals.get('product_temp_id'):		 
			product_rec = product_obj.browse(cr, uid, vals.get('product_temp_id') )
			product_code = product_rec.product_code		 
			vals.update({'code':product_code })
		return super(ch_bot_details_amendment, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		product_obj = self.pool.get('product.product')
		if vals.get('product_temp_id'):		 
			product_rec = product_obj.browse(cr, uid, vals.get('product_temp_id') )
			product_code = product_rec.product_code
			vals.update({'code':product_code })
		return super(ch_bot_details_amendment, self).write(cr, uid, ids, vals, context)   

ch_bot_details_amendment()

class ch_consu_details_amendment(osv.osv):
	
	_name = "ch.consu.details.amendment"
	_description = "BOM Consumable Details Amendment"   
	
	_columns = {
	
		'header_id':fields.many2one('kg.bom.amendment', 'BOM', ondelete='cascade',required=True),
		'product_temp_id':fields.many2one('product.product', 'Item Name',domain = [('type','=','consu')], ondelete='cascade',required=True),
		'code':fields.char('Item Code', size=128),  
		'qty': fields.integer('Qty',required=True), 
		'remarks':fields.text('Remarks'),
	
	}
	
	def onchange_consu_code(self, cr, uid, ids, product_temp_id, context=None):
		
		value = {'code': ''}
		if product_temp_id:
			pro_rec = self.pool.get('product.product').browse(cr, uid, product_temp_id, context=context)
			value = {'code': pro_rec.product_code}
			
		return {'value': value}
		
	def create(self, cr, uid, vals, context=None):	  
		product_obj = self.pool.get('product.product')
		if vals.get('product_temp_id'):		 
			product_rec = product_obj.browse(cr, uid, vals.get('product_temp_id') )
			product_code = product_rec.product_code		 
			vals.update({'code':product_code })
		return super(ch_consu_details_amendment, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		product_obj = self.pool.get('product.product')
		if vals.get('product_temp_id'):		 
			product_rec = product_obj.browse(cr, uid, vals.get('product_temp_id') )
			product_code = product_rec.product_code
			vals.update({'code':product_code })
		return super(ch_consu_details_amendment, self).write(cr, uid, ids, vals, context) 

ch_consu_details_amendment()

