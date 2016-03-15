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

class kg_bom(osv.osv):
	
	_name = 'kg.bom'	
	
	
	def _get_modify(self, cr, uid, ids, field_name, arg, context=None):
		res={}
		bom_amend_obj = self.pool.get('kg.bom.amendment')				
		for item in self.browse(cr, uid, ids, context=None):
			res[item.id] = 'no'
			bom_amend_ids = bom_amend_obj.search(cr,uid,[('bom_id','=',item.id)])			
			if bom_amend_ids:
				res[item.id] = 'yes'		
		return res
	
	_columns = {
		'name': fields.char('BOM Name', size=128, required=True, select=True),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled'),('expire','Expired')],'Status', readonly=True),   
		'line_ids': fields.one2many('ch.bom.line', 'header_id', "BOM Line"),		
		'line_ids_a':fields.one2many('ch.machineshop.details', 'header_id', "Machine Shop Line"),
		'line_ids_b':fields.one2many('ch.bot.details', 'header_id', "BOT Line"),
		'line_ids_c':fields.one2many('ch.consu.details', 'header_id', "Consumable Line"),		
		'type': fields.selection([('new','New'),('copy','Copy'),('amendment','Amendment')],'Type', required=True),
		'bom_type': fields.selection([('new_bom','New BOM'),('copy_bom','Copy BOM')],'Type', required=True),
		'source_bom': fields.many2one('kg.bom', 'Source BOM',domain="[('state','=','approved'), ('active','=','t')]"),
		'copy_flag':fields.boolean('Copy Flag'),
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model',domain="[('active','=','t')]"),   
		'uom': fields.char('Unit of Measure', readonly=True,required=True), 
		'remarks':fields.text('Remarks'),
		'qty': fields.integer('Qty', size=128,required=True,readonly=True),
		'active':fields.boolean('Active'),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'revision': fields.integer('Revision'),
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
		'expire_date':fields.datetime('Expired Date', readonly=True),
		'expire_user_id': fields.many2one('res.users', 'Expired By', readonly=True),		
	
		
	}
	
	_defaults = {
	  
	  'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.bom', context=c),
	  'active': True,
	  'state': 'draft',
	  'qty': 1,
	  'user_id': lambda obj, cr, uid, context: uid,
	  'crt_date':fields.datetime.now,   
	  'type':'new', 
	  'bom_type':'new_bom', 
	  'uom':'Nos', 
	  'revision' : 0, 
	  'copy_flag' : False, 
	  'modify': 'no',
	  
	}
	
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True
	def copy_bom(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])		
		foundry_line_obj = self.pool.get('ch.bom.line')
		machine_line_obj = self.pool.get('ch.machineshop.details')
		bot_line_obj = self.pool.get('ch.bot.details')		
		consu_line_obj = self.pool.get('ch.consu.details')
		cr.execute(""" delete from ch_bom_line where header_id  = %s """ %(ids[0]))
		cr.execute(""" delete from ch_machineshop_details where header_id  = %s """ %(ids[0]))
		cr.execute(""" delete from ch_bot_details where header_id  = %s """ %(ids[0]))
		cr.execute(""" delete from ch_consu_details where header_id  = %s """ %(ids[0]))	
		for foundry_line_item in rec.source_bom.line_ids:			
			vals = {
				'header_id' : ids[0]
				}			
			copy_rec = foundry_line_obj.copy(cr, uid, foundry_line_item.id,vals, context) 
			
		for machine_line_item in rec.source_bom.line_ids_a:			
			vals = {
				'header_id' : ids[0]
				}			
			copy_rec = machine_line_obj.copy(cr, uid, machine_line_item.id,vals, context) 
			
		for bot_line_item in rec.source_bom.line_ids_b:			
			vals = {
				'header_id' : ids[0]
				}			
			copy_rec = bot_line_obj.copy(cr, uid, bot_line_item.id,vals, context) 			
	
			
		for consu_line_item in rec.source_bom.line_ids_c:			
			vals = {
				'header_id' : ids[0]
				}			
			copy_rec = consu_line_obj.copy(cr, uid, consu_line_item.id,vals, context)	
						
		self.write(cr, uid, ids[0], {'copy_flag': True})		
		return True

	def entry_confirm(self,cr,uid,ids,context=None):		
		rec = self.browse(cr,uid,ids[0])
		bom_obj = self.pool.get('kg.bom')
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
		old_ids = self.search(cr,uid,[('state','=','approved'),('name','=',rec.name)])
		if old_ids:
			bom_rec = bom_obj.browse(cr, uid, old_ids[0])			  
			if rec.name == bom_rec.name and rec.type != 'amendment':
				raise osv.except_osv(_('Warning !'), _('BOM Name must be uniqe!!'))	 
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])		
		old_ids = self.search(cr,uid,[('state','=','approved'),('name','=',rec.name)])	  
		if old_ids:		 
			self.write(cr, uid, old_ids[0], {'state': 'expire','expire_user_id': uid, 'expire_date': time.strftime('%Y-%m-%d %H:%M:%S')})		   
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
		
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
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
		
	def create(self, cr, uid, vals, context=None):
		"""if vals.get('qty'):
			qty = vals.get('qty')
			vals.update({'qty': qty,'planning_qty':qty})	"""
		return super(kg_bom, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):	  
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_bom, self).write(cr, uid, ids, vals, context)
	
kg_bom()



class ch_bom_line(osv.osv):
	
	_name = 'ch.bom.line'
	
	
	_columns = {
		
		'header_id':fields.many2one('kg.bom', 'BOM Name', required=True, ondelete='cascade'),  
		'pos_no': fields.integer('Position No'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No', required=True,domain="[('active','=','t')]"), 
		'moc_id':fields.many2one('kg.moc.master','MOC',required=True,domain="[('active','=','t')]"),
		'pattern_name': fields.char('Pattern Name', required=True), 
		'remarks':fields.text('Remarks'),
		'qty': fields.integer('Qty',required=True,),
		'state':fields.selection([('draft','Draft'),('approve','Approved')],'Status'),
		
		
	}
	
	
	_defaults = {
	
	'state':'draft',
	'qty': 1,
	  
	}
	
	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.name:
			division_name = rec.name
			name=division_name.upper()		  
			cr.execute(""" select upper(name) from kg_stage_master where upper(name)  = '%s' """ %(name))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True			  
		return res
	
	def _check_line_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute('''select id from ch_bom_line where pattern_id = %s and id != %s and header_id = %s ''',[entry.pattern_id.id,entry.id,entry.header_id.id])
		duplicate_id = cr.fetchone()
		if duplicate_id:
			if duplicate_id[0] != None:
				return False
		return True 

	
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
		return super(ch_bom_line, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		pattern_obj = self.pool.get('kg.pattern.master')
		if vals.get('pattern_id'):
			pattern_rec = pattern_obj.browse(cr, uid, vals.get('pattern_id') )
			pattern_name = pattern_rec.pattern_name
			vals.update({'pattern_name': pattern_name})
		return super(ch_bom_line, self).write(cr, uid, ids, vals, context)  
		
	"""_constraints = [
		
		(_check_line_duplicates, 'Pattern Name must be unique !!', ['Pattern Name']),	   
		
	]"""

	
ch_bom_line()


class ch_machineshop_details(osv.osv):

	_name = "ch.machineshop.details"
	_description = "BOM machineshop Details"
	
	
	_columns = {
	
		'header_id':fields.many2one('kg.bom', 'BOM', ondelete='cascade',required=True),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', ondelete='cascade',required=True),
		'moc_id':fields.many2one('kg.moc.master','MOC',required=True,domain="[('active','=','t')]"),
		'pos_no': fields.integer('Position No'),
		'csd_no': fields.char('CSD No.'),
		'name':fields.char('Item Name', size=128),	  
		'qty': fields.integer('Qty', required=True),
		'remarks':fields.text('Remarks'),   
	
	}   
	
	def onchange_machineshop_name(self, cr, uid, ids, ms_id, context=None):
		
		value = {'name': '','csd_no':''}
		if ms_id:
			pro_rec = self.pool.get('kg.machine.shop').browse(cr, uid, ms_id, context=context)
			value = {'name': pro_rec.name,'csd_no':pro_rec.csd_code}
			
		return {'value': value}
		
	def create(self, cr, uid, vals, context=None):	  
		ms_obj = self.pool.get('kg.machine.shop')
		if vals.get('ms_id'):		   
			ms_rec = ms_obj.browse(cr, uid, vals.get('ms_id') )
			ms_name = ms_rec.name		   
			csd_no = ms_rec.csd_code		   
			vals.update({'name':ms_name ,'csd_no':csd_no})
		return super(ch_machineshop_details, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		ms_obj = self.pool.get('kg.machine.shop')
		if vals.get('ms_id'):		   
			ms_rec = ms_obj.browse(cr, uid, vals.get('ms_id') )
			ms_name = ms_rec.name
			csd_no = ms_rec.csd_code		   		   
			vals.update({'name':ms_name,'csd_no':csd_no })
		return super(ch_machineshop_details, self).write(cr, uid, ids, vals, context)   

ch_machineshop_details()

class ch_bot_details(osv.osv):
	
	_name = "ch.bot.details"
	_description = "BOM BOT Details"	
	
	_columns = {
	
		'header_id':fields.many2one('kg.bom', 'BOM', ondelete='cascade',required=True),
		'product_temp_id':fields.many2one('product.product', 'Item Name',domain = [('type','=','bot')], ondelete='cascade',required=True),
		'moc_id':fields.many2one('kg.moc.master','MOC',required=True,domain="[('active','=','t')]"),
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
		return super(ch_bot_details, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		product_obj = self.pool.get('product.product')
		if vals.get('product_temp_id'):		 
			product_rec = product_obj.browse(cr, uid, vals.get('product_temp_id') )
			product_code = product_rec.product_code
			vals.update({'code':product_code })
		return super(ch_bot_details, self).write(cr, uid, ids, vals, context)   

ch_bot_details()

class ch_consu_details(osv.osv):
	
	_name = "ch.consu.details"
	_description = "BOM Consumable Details" 
	
	_columns = {
	
		'header_id':fields.many2one('kg.bom', 'BOM', ondelete='cascade',required=True),
		'product_temp_id':fields.many2one('product.product', 'Item Name',domain = [('type','=','consu')], ondelete='cascade',required=True),
		'moc_id':fields.many2one('kg.moc.master','MOC',required=True,domain="[('active','=','t')]"),
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
		return super(ch_consu_details, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		product_obj = self.pool.get('product.product')
		if vals.get('product_temp_id'):		 
			product_rec = product_obj.browse(cr, uid, vals.get('product_temp_id') )
			product_code = product_rec.product_code
			vals.update({'code':product_code })
		return super(ch_consu_details, self).write(cr, uid, ids, vals, context) 

ch_consu_details()


