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
	
		'name': fields.char('Amendment No', size=128,select=True,readonly=True),
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
		'category_type': fields.selection([('pump_bom','Pump BOM'),('part_list_bom','Part list BOM')],'Category'),	
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True), 	
		
		### Entry Info ###
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),	
		'ap_date': fields.datetime('Approved/Reject Date', readonly=True),
		'ap_user_id': fields.many2one('res.users', 'Approved/Reject By', readonly=True),	
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		
		## Child declaration
		'line_ids': fields.one2many('ch.bom.line.amendment', 'header_id', "BOM Line"),	  
		'line_ids_a':fields.one2many('ch.machineshop.details.amendment', 'header_id', "Machine Shop Line"),
		'line_ids_b':fields.one2many('ch.bot.details.amendment', 'header_id', "BOT Line"),
		'line_ids_d':fields.one2many('ch.base.plate.amendment', 'header_id', "Base Plate"),
		
	}
	
	_defaults = {
	
	'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.bom.amendment', context=c),
	'entry_date': lambda * a: time.strftime('%Y-%m-%d'),
	'active': True,  
	'load_bom': False,  	
	'state': 'draft',
	'entry_mode': 'manual',
	
	}
	
	def _validations (self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		bom_obj = self.pool.get('kg.bom.amendment')		
		bom_foundry_lines=rec.line_ids			 
		machine_shop_lines=rec.line_ids_a			 
		bot_lines=rec.line_ids_b
		 
		if bom_foundry_lines:
			for bom_foundry_item in bom_foundry_lines:			
				if bom_foundry_item.qty <= 0:
					raise osv.except_osv(
						_('Warning !'),
						_('Quantity in Foundry Item (%s) should be greater than zero !!')%(bom_foundry_item.pattern_id.pattern_name)) 		
		if machine_shop_lines:
			for machine_shop_item in machine_shop_lines:			
				if machine_shop_item.qty <= 0:
					raise osv.except_osv(
						_('Warning !'),
						_('Quantity in Machine Shop Item (%s) should be greater than zero !!')%(bom_foundry_item.pattern_id.pattern_name))
		if bot_lines:
			for bot_item in bot_lines:			
				if bot_item.qty <= 0:
					raise osv.except_osv(
						_('Warning !'),
						_('Quantity in BOT Item (%s) should be greater than zero !!')%(bom_foundry_item.pattern_id.pattern_name))
						
		draft_amends=bom_obj.search(cr,uid,[('bom_id','=',rec.bom_id.id),('state','!=','confirmed')])
		if len(draft_amends) > 1:
			raise osv.except_osv(
						_('Warning !'),
						_('BOM Amendment (%s) already exists in draft state,delete it to proceed  !!')%(rec.bom_id.name))
		return True
	
	_constraints = [
		
		(_validations, ' ', ['Quantity']),		
		
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
						
						'bom_id': bom.id,
						'pump_model_id' : bom.pump_model_id.id, 
						'uom': bom.uom,
						'qty': bom.qty,
						'entry_date': obj.entry_date,
						'remarks': bom.remarks,
						'remark': bom.remark,
						'category_type': bom.category_type,
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
			amend_conus_line_obj = self.pool.get('ch.base.plate.amendment')
			bom_conus_lines=bom.line_ids_d
			
			for bom_foundry_line in bom_foundry_lines:				
				amend_foundry_line_id = amend_foundry_line_obj.create(cr,uid,
					{
						'header_id':obj.id,
						'position_id': bom_foundry_line.position_id.id,
						'csd_no': bom_foundry_line.csd_no,
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
						'position_id': bom_machineshop_line.position_id.id,
						'csd_no': bom_machineshop_line.csd_no,
						'ms_id': bom_machineshop_line.ms_id.id,
						'name': bom_machineshop_line.name,
						'qty':bom_machineshop_line.qty,
						'remarks':bom_machineshop_line.remarks,
					})	
			for bom_bot_line in bom_bot_lines:		
				amend_bot_line_id = amend_bot_line_obj.create(cr,uid,
					{
						'header_id':obj.id,
						'pos_no': bom_bot_line.pos_no,
						'position_id': bom_bot_line.position_id.id,
						'bot_id': bom_bot_line.bot_id.id,
						'name': bom_bot_line.name,
						'qty':bom_bot_line.qty,
						'remarks':bom_bot_line.remarks,
					})	
			for bom_conus_line in bom_conus_lines:		
				bom_conus_line_id = amend_conus_line_obj.create(cr,uid,
					{
						'header_id':obj.id,
						'limitation': bom_conus_line.limitation,
						'partlist_id': bom_conus_line.partlist_id.id,						
						'remarks':bom_conus_line.remarks,
					})	
					
			
		
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):		
		entry_rec = self.browse(cr,uid,ids[0])
		if entry_rec.state == 'draft':
			if len(entry_rec.line_ids) == 0 and len(entry_rec.line_ids_a) == 0 and len(entry_rec.line_ids_b) == 0:
				raise osv.except_osv(
							_('Warning !'),
							_('Please Check Line empty values not allowed!! !!'))	
			amend_name = ''	
			amend_name_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.bom.amendment')])			
			rec = self.pool.get('ir.sequence').browse(cr,uid,amend_name_seq_id[0])			
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(amend_name_seq_id[0],rec.code,entry_rec.entry_date))
			amend_name = cr.fetchone();
			
			self.write(cr, uid, ids, {'name': amend_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid,'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),	})
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
						'category_type': obj.category_type,
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
			
			amend_base_plate_line_obj = self.pool.get('ch.base.plate')
			bom_base_plate_lines=obj.line_ids_d
			
				
			for bom_foundry_line in bom_foundry_lines:				
				amend_foundry_line_id = amend_foundry_line_obj.create(cr,uid,
					{
						'header_id':new_bom,
						'position_id': bom_foundry_line.position_id.id,
						'pattern_id': bom_foundry_line.pattern_id.id,
						'pattern_name':bom_foundry_line.pattern_name,
						'remarks':bom_foundry_line.remarks,
						'csd_no':bom_foundry_line.csd_no,
						'qty': bom_foundry_line.qty,
						'state' : bom_foundry_line.state,
					})
					
			for bom_machineshop_line in bom_machineshop_lines:	
				print"bom_machineshop_line.csd_no",bom_machineshop_line.csd_no
				amend_machineshop_line_id = amend_machineshop_line_obj.create(cr,uid,
					{
						'header_id':new_bom,
						'position_id': bom_machineshop_line.position_id.id,
						'ms_id': bom_machineshop_line.ms_id.id,
						'name': bom_machineshop_line.name,
						'qty':bom_machineshop_line.qty,
						'csd_no':bom_machineshop_line.csd_no,
						'remarks':bom_machineshop_line.remarks,
						
					})	
			for bom_bot_line in bom_bot_lines:			
				
				amend_bot_line_id = amend_bot_line_obj.create(cr,uid,
					{
						'header_id':new_bom,
						'position_id': bom_bot_line.position_id.id,
						'bot_id': bom_bot_line.bot_id.id,
						'name': bom_bot_line.name,
						'qty':bom_bot_line.qty,
						'remarks':bom_bot_line.remarks,
						
					})	
					
			for bom_base_plate_line in bom_base_plate_lines:			
				
				amend_bot_line_id = amend_base_plate_line_obj.create(cr,uid,
					{
						'header_id':new_bom,
						'limitation': bom_base_plate_line.limitation,
						'partlist_id': bom_base_plate_line.partlist_id.id,						
						'remarks':bom_base_plate_line.remarks,
						
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
	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state not in ('draft','cancel'):				
				raise osv.except_osv(_('Delete access denied !'), _('Unable to delete. Draft entry only you can delete !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)

		
kg_bom_amendment()

class ch_bom_line_amendment(osv.osv):
	
	_name = 'ch.bom.line.amendment'
	
	_columns = {
		
		'header_id':fields.many2one('kg.bom.amendment', 'BOM Entry', required=True, ondelete='cascade'),	
		'position_id': fields.many2one('kg.position.number','Position No', required=True,domain="[('active','=','t')]"), 	
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No', required=True,domain="[('active','=','t')]"), 	
		'csd_no': fields.char('CSD No.', size=128),	
		'pattern_name': fields.char('Pattern Name', required=True),
		'remarks':fields.text('Remarks'),
		'qty': fields.integer('Qty',required=True,),
		'state':fields.selection([('draft','Draft'),('approve','Approved')],'Status'),		
		
	}
	
	_defaults = {
	
	'state':'draft',
	'qty': 1,
	  
	}
	
	def _check_line_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute('''select id from ch_bom_line_amendment where position_id = %s and pattern_id = %s and id != %s and header_id = %s ''',[entry.position_id.id,entry.pattern_id.id,entry.id,entry.header_id.id])
		duplicate_id = cr.fetchone()
		if duplicate_id:
			if duplicate_id[0] != None:
				raise osv.except_osv(_('Warning'), _('Pattern Name (%s) must be unique !!')%(entry.pattern_id.pattern_name))	
		if entry.qty <= 0:			
			raise osv.except_osv(_('Warning'), _('Foundry items Qty Zero and negative not accept for (%s) ')%(entry.pattern_id.pattern_name))	
		return True 
	
	def onchange_pattern_name(self, cr, uid, ids, pattern_id, context=None):		
		value = {'pattern_name': '','csd_no':''}
		if pattern_id:
			pro_rec = self.pool.get('kg.pattern.master').browse(cr, uid, pattern_id, context=context)
			value = {'pattern_name': pro_rec.pattern_name,'csd_no':pro_rec.csd_code}			
		return {'value': value}	
		
	def create(self, cr, uid, vals, context=None):
		pattern_obj = self.pool.get('kg.pattern.master')
		if vals.get('pattern_id'):		  
			pattern_rec = pattern_obj.browse(cr, uid, vals.get('pattern_id') )
			pattern_name = pattern_rec.pattern_name
			vals.update({'pattern_name': pattern_name,'csd_no':pattern_rec.csd_code})
		return super(ch_bom_line_amendment, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		pattern_obj = self.pool.get('kg.pattern.master')
		if vals.get('pattern_id'):
			pattern_rec = pattern_obj.browse(cr, uid, vals.get('pattern_id') )
			pattern_name = pattern_rec.pattern_name
			vals.update({'pattern_name': pattern_name,'csd_no':pattern_rec.csd_code})		
		return super(ch_bom_line_amendment, self).write(cr, uid, ids, vals, context)    
		
	_constraints = [
		
		(_check_line_duplicates, ' ', ['Pattern Name and Qty']),	   
		
	]
		
ch_bom_line_amendment()

class ch_machineshop_details_amendment(osv.osv):

	_name = "ch.machineshop.details.amendment"
	_description = "BOM machineshop Details Amendment"
	
	_columns = {
	
		'header_id':fields.many2one('kg.bom.amendment', 'BOM', ondelete='cascade',required=True),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code',domain = [('type','=','ms')], ondelete='cascade',required=True),				
		'position_id': fields.many2one('kg.position.number','Position No', required=True,domain="[('active','=','t')]"), 
		'csd_no': fields.char('CSD No.'),			
		'name':fields.char('Item Name', size=128),	  
		'qty': fields.integer('Qty', required=True),
		'remarks':fields.text('Remarks'),   
	
	}  
	
	_defaults = {	
	
	'qty': 1,
	  
	} 
	
	def onchange_machineshop_name(self, cr, uid, ids, ms_id, context=None):		
		value = {'name': '','csd_no':''}
		if ms_id:
			pro_rec = self.pool.get('kg.machine.shop').browse(cr, uid, ms_id, context=context)
			value = {'name': pro_rec.name,'csd_no':pro_rec.csd_code}			
		return {'value': value}
	
	def _check_line_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute('''select id from ch_machineshop_details_amendment where position_id = %s and ms_id = %s and id != %s and header_id = %s ''',[entry.position_id.id,entry.ms_id.id,entry.id,entry.header_id.id])
		duplicate_id = cr.fetchone()
		if duplicate_id:
			if duplicate_id[0] != None:
				raise osv.except_osv(_('Warning'), _('MS Name (%s) must be unique !!')%(entry.ms_id.name))	
		if entry.qty <= 0:			
			raise osv.except_osv(_('Warning'), _('Machine Shop items Qty Zero and negative not accept for (%s) ')%(entry.ms_id.name))	
		return True 	
		
	def create(self, cr, uid, vals, context=None):	  
		ms_obj = self.pool.get('kg.machine.shop')
		if vals.get('ms_id'):		   
			ms_rec = ms_obj.browse(cr, uid, vals.get('ms_id') )
			ms_name = ms_rec.name		   
			csd_no = ms_rec.csd_code		   
			vals.update({'name':ms_name ,'csd_no':csd_no})
		return super(ch_machineshop_details_amendment, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		ms_obj = self.pool.get('kg.machine.shop')
		if vals.get('ms_id'):		   
			ms_rec = ms_obj.browse(cr, uid, vals.get('ms_id') )
			ms_name = ms_rec.name
			csd_no = ms_rec.csd_code		   		   
			vals.update({'name':ms_name,'csd_no':csd_no })
		return super(ch_machineshop_details_amendment, self).write(cr, uid, ids, vals, context)
	_constraints = [
		
		(_check_line_duplicates, '', ['MS Name and Qty']),	   
		
	]   
ch_machineshop_details_amendment()

class ch_bot_details_amendment(osv.osv):
	
	_name = "ch.bot.details.amendment"
	_description = "BOM BOT Details Amendment"  
	
	_columns = {
	
		'header_id':fields.many2one('kg.bom.amendment', 'BOM', ondelete='cascade',required=True),
		'bot_id':fields.many2one('kg.machine.shop', 'Item Code',domain = [('type','=','bot')], ondelete='cascade',required=True),
		'pos_no': fields.integer('Position No'),
		'position_id': fields.many2one('kg.position.number','Position No',domain="[('active','=','t')]"), 
		'name':fields.char('Item Name', size=128),						
		'qty': fields.integer('Qty', required=True),
		'remarks':fields.text('Remarks'),   
	
	}
	
	_defaults = {	
	
		'qty': 1,
	  
	} 
	
	def onchange_bot_name(self, cr, uid, ids, bot_id, context=None):	   
		value = {'name': ''}
		if bot_id:
			pro_rec = self.pool.get('kg.machine.shop').browse(cr, uid, bot_id, context=context)
			value = {'name': pro_rec.name}		  
		return {'value': value}
		
	def create(self, cr, uid, vals, context=None):	  
		product_obj = self.pool.get('product.product')
		if vals.get('product_temp_id'):		 
			product_rec = product_obj.browse(cr, uid, vals.get('product_temp_id') )
			vals.update({'code':product_rec.product_code })
		return super(ch_bot_details_amendment, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		product_obj = self.pool.get('product.product')
		if vals.get('product_temp_id'):		 
			product_rec = product_obj.browse(cr, uid, vals.get('product_temp_id') )
			vals.update({'code':product_rec.product_code })
		return super(ch_bot_details_amendment, self).write(cr, uid, ids, vals, context)   
	
	def _check_line_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute('''select id from ch_bot_details_amendment where position_id = %s and bot_id = %s and id != %s and header_id = %s ''',[entry.position_id.id,entry.bot_id.id,entry.id,entry.header_id.id])
		duplicate_id = cr.fetchone()
		if duplicate_id:
			if duplicate_id[0] != None:
				raise osv.except_osv(_('Warning'), _('BOT Name (%s) must be unique !!')%(entry.bot_id.name))	
		if entry.qty <= 0:			
			raise osv.except_osv(_('Warning'), _('BOT items Qty Zero and negative not accept for (%s) ')%(entry.bot_id.name))	
		return True 
		
	_constraints = [
		
		(_check_line_duplicates, ' ', ['BOT Name and Qty']),	   
		
	]	

ch_bot_details_amendment()


class ch_base_plate_amendment(osv.osv):
	
	_name = "ch.base.plate.amendment"
	_description = "BOM Base Plate Details" 
	
	_columns = {
	
		'header_id':fields.many2one('kg.bom.amendment', 'BOM', ondelete='cascade',required=True),
		'limitation':fields.selection([('upto_2999','Upto 2999'),('above_3000','Above 3000')],'Limitation',required=True),		
		'partlist_id':fields.many2one('kg.bom', 'Partlist',domain = [('category_type','=','part_list_bom')], ondelete='cascade',required=True),		
		'remarks':fields.text('Remarks'),
	
	}	
	
	def _check_same_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(""" select limitation from ch_base_plate_amendment where limitation ='%s' and header_id = '%s' """ %(entry.limitation,entry.header_id.id))
		data = cr.dictfetchall()			
		if len(data) > 1:		
			raise osv.except_osv(_('Warning'), _('Limitation (%s) must be unique !!')%(entry.limitation))
		return True	
		
	_constraints = [					  		
		(_check_same_values, '  ',['Limitation']),			
	   ]

ch_base_plate_amendment()

