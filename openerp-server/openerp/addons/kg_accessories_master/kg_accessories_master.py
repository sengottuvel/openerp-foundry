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

class kg_accessories_master(osv.osv):

	_name = "kg.accessories.master"
	_description = "Accessories Master"
	
	### Version 0.1
	
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
					as sam  """ %('kg_accessories_master'))
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
		
		### Version 0.2
	
	_columns = {
	
		## Basic Info	
			
		'name': fields.char('Name', required=True, select=True),		
		'code': fields.char('Code', size=128),		
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),	
		
		
		### Entry Info ###
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'active': fields.boolean('Active'),
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
		
		
		## Module Requirement Info
		'access_type': fields.selection([('new','NEW'),('copy','COPY')],'Type',required=True),		
		'access_cate_id': fields.many2one('kg.accessories.category','Accessories Category',domain="[('state','=','approved')]"),
		'access_id': fields.many2one('kg.accessories.master','Source Accessories',domain="[('state','=','approved')]"),
		'copy_flag':fields.boolean('Copy Flag'),		
		'product_id': fields.many2one('product.product','Item Name'), 
		'is_coupling_flag': fields.boolean('Is Coupling'),		
		'is_pump_acc_flag': fields.boolean('Is Pump Accessories'),
		
		'accessories_type': fields.selection([('base_plate','Base Plate'),('coupling','Coupling'),('coupling_guard','Coupling Guard'),
		('foundation_bolt','Foundation Bolt'),
		('pump_pulley','Pump Pulley'),('motor_pulley','Motor Pulley'),('slide_rail','Slide Rail'),('belt','Belt'),('belt_guard','Belt Guard'),('others','Others')],'Accessories type',required=True),				
		
		##Invisible fields ticket no:4947 start
		'primemover_id': fields.many2one('kg.primemover.master','Prime Mover'),
		'framesize': fields.char('Framesize'),		
		'pump_id':fields.many2one('kg.pumpmodel.master','Pumpmodel'),
		'coupling_id': fields.many2one('kg.accessories.master','Coupling',  domain="[('accessories_type','in',['coupling'])]"),	
		##Invisible fields ticket no:4947 End
		
				
		'hsn_no': fields.many2one('kg.hsn.master', 'HSN No.', domain="[('state','=','approved')]", required=True),		
		
		'flag_fabrication': fields.boolean('Is Fabrication'),
		## Child Tables Declaration	 
		
		'line_ids': fields.one2many('ch.kg.accessories.master','header_id','BOT Line Details',readonly=False,states={'approved':[('readonly',True)]}),
		'line_ids_a':fields.one2many('ch.accessories.ms', 'header_id', "Machine Shop Line",readonly=False,states={'approved':[('readonly',True)]}),
		'line_ids_b':fields.one2many('ch.accessories.fou', 'header_id', "FOU Line",readonly=False,states={'approved':[('readonly',True)]}),
		'line_ids_c':fields.one2many('ch.foundation.bolt', 'header_id', "Foundation Bolt Configuration Line",readonly=False,states={'approved':[('readonly',True)]}),
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.accessories.master', context=c),
		'active': True,		
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'access_type': 'new',
		'copy_flag' : False,
		'modify': 'yes',
		'entry_mode': 'manual',
		'is_pump_acc_flag': 'False',
		
	}
		
		
	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.name:
			dispatch_name = rec.name
			name=dispatch_name.upper()			
			cr.execute(""" select upper(name) from kg_accessories_master where upper(name)  = '%s' """ %(name))
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
			cr.execute(""" select upper(code) from kg_accessories_master where upper(code)  = '%s' """ %(code))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res	
	
	## Basic Needs
	
	
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			if rec.cancel_remark:
				for item in rec.line_ids:
					if item.entry_mode == 'auto' and item.product_id.is_accessories == True:
						self.pool.get('product.product').write(cr,uid,item.product_id.id,{'state':'cancel','remark':'Cancelled from Accessories Master'})
				self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Cancel remark is must !!'),
					_('Enter the remarks in Cancel remarks field !!'))
		return True
	
	def copy_accessories(self, cr, uid, ids, context=None):		
		rec = self.browse(cr,uid,ids[0])	
		line_obj = self.pool.get('ch.kg.accessories.master')				
		line_obj_ms = self.pool.get('ch.accessories.ms')				
		line_obj_fou = self.pool.get('ch.accessories.fou')				
		cr.execute(""" delete from ch_kg_accessories_master where header_id  = %s """ %(ids[0]))
				
		for line_item in rec.access_id.line_ids:	
			vals = {
				'header_id' : ids[0]
				}			
			copy_rec = line_obj.copy(cr, uid, line_item.id, vals, context) 			
			
		for line_item in rec.access_id.line_ids_b:	
			vals = {
				'header_id' : ids[0]
				}			
			copy_rec = line_obj_fou.copy(cr, uid, line_item.id, vals, context) 		
				
		for line_item in rec.access_id.line_ids_a:	
			vals = {
				'header_id' : ids[0]
				}			
			copy_rec = line_obj_ms.copy(cr, uid, line_item.id, vals, context) 			
		
		if rec.name == rec.access_id.name:
			raise osv.except_osv(_('Warning !!'),
				_('Kindly Change Accessories !!'))
			
		self.write(cr, uid, ids[0], {
									'copy_flag': True,									
									'notes':rec.access_id.notes,									
									})		
									
		return True
		
	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			if len(rec.line_ids) == 0  and len(rec.line_ids_a) == 0 and len(rec.line_ids_b) == 0:			
				raise osv.except_osv(_('Warning !!'),
					_('Either foundry,MS or BOT item should be mapped to confirm !!'))					
			if rec.access_type == 'copy':				
				cr.execute('''select 
						bom_line.pattern_id,
						bom_line.position_id,
						bom_line.qty
						from ch_accessories_fou bom_line
						left join kg_accessories_master header on header.id  = bom_line.header_id
						where header.access_type = 'copy' and header.id = %s''',[rec.id])
				
				source_bom_ids = cr.fetchall()				
				source_bom_len = len(source_bom_ids)				
				
				cr.execute('''select 
						bom_line.pattern_id,
						bom_line.position_id,
						bom_line.qty
						from ch_accessories_fou bom_line 
						where bom_line.header_id  = %s''',[rec.access_id.id])
				
				source_old_bom_ids = cr.fetchall()				
				source_old_bom_len = len(source_old_bom_ids)
								
				cr.execute('''select 
						bom_line.pattern_id,
						bom_line.position_id,
						bom_line.qty
						from ch_accessories_fou bom_line 
						left join kg_accessories_master header on header.id  = bom_line.header_id
						where header.access_type = 'copy' and header.id = %s
						INTERSECT
						select 
						bom_line.pattern_id,
						bom_line.position_id,
						bom_line.qty
						from ch_accessories_fou bom_line 
						where bom_line.header_id  = %s ''',[rec.id,rec.access_id.id])
						
				repeat_ids = cr.fetchall()				
				new_bom_len = len(repeat_ids)
				
				### Check Duplicates Foundry Items end.... ###				
				
				### Check Duplicates Machine Shop Items  start ###
				
				cr.execute('''select 
						machine_line.ms_id,
						machine_line.position_id,
						machine_line.qty
						from ch_accessories_ms machine_line 
						left join kg_accessories_master header on header.id  = machine_line.header_id
						where header.access_type = 'copy' and header.id = %s''',[rec.id])
				
				ms_new_bom_ids = cr.fetchall()				
				ms_new_bom_len = len(ms_new_bom_ids)
				
				cr.execute('''select 
						machine_line.ms_id,
						machine_line.position_id,
						machine_line.qty
						from ch_accessories_ms machine_line 
						where machine_line.header_id  = %s''',[rec.access_id.id])
				
				ms_old_bom_ids = cr.fetchall()				
				ms_old_bom_len = len(ms_old_bom_ids)
								
				cr.execute('''select 
						machine_line.ms_id,
						machine_line.position_id,
						machine_line.qty
						from ch_accessories_ms machine_line 
						left join kg_accessories_master header on header.id  = machine_line.header_id
						where header.access_type = 'copy' and header.id = %s
						INTERSECT
						select 
						machine_line.ms_id,
						machine_line.position_id,
						machine_line.qty
						from ch_accessories_ms machine_line 
						where machine_line.header_id  = %s ''',[rec.id,rec.access_id.id])
						
				ms_repeat_ids = cr.fetchall()				
				ms_join_bom_len = len(ms_repeat_ids)
				
				### Check Duplicates Machine Shop end.... ###			
				
				### Check Duplicates BOT Items  start ###				
				
				cr.execute('''select 
						bot_line.ms_id,
						bot_line.position_id,
						bot_line.qty
						from ch_kg_accessories_master bot_line 
						left join kg_accessories_master header on header.id  = bot_line.header_id
						where header.access_type = 'copy' and header.id = %s''',[rec.id])
				
				bot_new_bom_ids = cr.fetchall()				
				bot_new_bom_len = len(bot_new_bom_ids)
				
				cr.execute('''select 
						bot_line.ms_id,
						bot_line.position_id,
						bot_line.qty
						from ch_kg_accessories_master bot_line 
						where bot_line.header_id  = %s ''',[rec.access_id.id])
				
				bot_old_bom_ids = cr.fetchall()				
				bot_old_bom_len = len(bot_old_bom_ids)
								
				cr.execute('''select 
						bot_line.ms_id,
						bot_line.position_id,
						bot_line.qty
						from ch_kg_accessories_master bot_line 
						left join kg_accessories_master header on header.id  = bot_line.header_id
						where header.access_type = 'copy' and header.id = %s
						INTERSECT
						select 
						bot_line.ms_id,
						bot_line.position_id,
						bot_line.qty
						from ch_kg_accessories_master bot_line 
						where bot_line.header_id  = %s ''',[rec.id,rec.access_id.id])
						
				bot_repeat_ids = cr.fetchall()				
				bot_join_bom_len = len(bot_repeat_ids)
				
				### Check Duplicates BOT end.... ###	
				
				bom_dup = ms_dup = bot_dup = ''		
				if new_bom_len == source_bom_len == source_old_bom_len:			
					bom_dup = 'yes'		
				if ms_new_bom_len == ms_join_bom_len == ms_old_bom_len:			
					ms_dup = 'yes'		
				if bot_new_bom_len == bot_join_bom_len == bot_old_bom_len:
					bot_dup = 'yes'				
				
				if bom_dup == 'yes' and ms_dup == 'yes' and bot_dup == 'yes':			
					raise osv.except_osv(_('Warning!'),
									_('Same Accessories Details are already exist !!'))	
			
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])				
		if rec.state == 'confirmed':
			if len(rec.line_ids) == 0  and len(rec.line_ids_a) == 0 and len(rec.line_ids_b) == 0:			
				raise osv.except_osv(_('Warning !!'),
					_('Either foundry,MS or BOT item should be mapped to confirm !!'))					
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
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
		return super(kg_accessories_master, self).write(cr, uid, ids, vals, context)
	
	def _check_line(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if not rec.line_ids:			
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
			
		url = 'http://192.168.1.7/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&Accessories='+rec_code


		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
	
	_constraints = [
		(_name_validate, 'Accessories Name must be unique !!', ['Name']),		
		(_code_validate, 'Accessories code must be unique !!', ['code']),			
		
	]
	
kg_accessories_master()


class ch_accessories_fou(osv.osv):
	
	_name = 'ch.accessories.fou'
	
	_columns = {
		
		'header_id':fields.many2one('kg.accessories.master', 'Access',ondelete='cascade'),
		'pos_no': fields.integer('Position No'),
		'position_id': fields.many2one('kg.position.number','Position No', required=True), 	
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No', required=True), 	
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
		cr.execute('''select id from ch_accessories_fou where position_id = %s and pattern_id = %s and id != %s and header_id = %s ''',[entry.position_id.id,entry.pattern_id.id,entry.id,entry.header_id.id])
		duplicate_id = cr.fetchone()
		if duplicate_id:
			if duplicate_id[0] != None:
				raise osv.except_osv(_('Warning'), _('Duplicate of Check Pattern No (%s) is not allowed')%(entry.pattern_id.pattern_name))
		if entry.qty <= 0:			
			raise osv.except_osv(_('Warning'), _('Qty should be greater than zero for (%s) ')%(entry.pattern_id.pattern_name))
		return True 	
	
	def onchange_pattern_name(self, cr, uid, ids, pattern_id, context=None):
		value = {'pattern_name': '','csd_no':''}
		if pattern_id:
			pro_rec = self.pool.get('kg.pattern.master').browse(cr, uid, pattern_id, context=context)
			value = {'pattern_name': pro_rec.pattern_name,'csd_no':pro_rec.csd_code}
		return {'value': value}
		
	_constraints = [
		
		(_check_line_duplicates, ' ', ['Qty']),	   		
	]

	
ch_accessories_fou()


class ch_accessories_ms(osv.osv):

	_name = "ch.accessories.ms"
	_description = "Accessories Machineshop Details"
	
	_columns = {
	
		'header_id':fields.many2one('kg.accessories.master', 'Access', ondelete='cascade',required=True),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code',domain = [('type','=','ms')], ondelete='cascade',required=True),		
		'pos_no': fields.integer('Position No'),
		'position_id': fields.many2one('kg.position.number','Position No', required=True), 	
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
		cr.execute('''select id from ch_accessories_ms where position_id = %s and ms_id = %s and id != %s and header_id = %s ''',[entry.position_id.id,entry.ms_id.id,entry.id,entry.header_id.id])
		duplicate_id = cr.fetchone()
		if duplicate_id:
			if duplicate_id[0] != None:
				raise osv.except_osv(_('Warning'), _('Duplicate of Check Item Name (%s) is not allowed')%(entry.ms_id.name))
		if entry.qty <= 0:			
			raise osv.except_osv(_('Warning'), _('Qty should be greater than zero for (%s) ')%(entry.ms_id.name))
		return True 	
	
	_constraints = [
		
		(_check_line_duplicates, ' ', ['Qty']),	 		
	]   

ch_accessories_ms()


class ch_kg_accessories_master(osv.osv):
	
	_name = 'ch.kg.accessories.master'
	
	_columns = {		
		
		'header_id':fields.many2one('kg.accessories.master', 'Accessories No', required=True, ondelete='cascade'),
		'position_id': fields.many2one('kg.position.number','Position No'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','bot'),('state','not in',('reject','cancel'))], ondelete='cascade',required=True),
		'item_name': fields.related('ms_id','name', type='char', size=128, string='Item Name', store=True, readonly=True),
		'code':fields.char('Item Code', size=128),	  
		'qty': fields.integer('Qty', required=True),
		'remark': fields.text('Remarks'),
		'csd_no': fields.char('CSD No.'),
		
		}
	
	_defaults = {	
	
		'qty': 1,
	  
	} 
				
	def onchange_product_uom(self, cr, uid, ids, product_id, uom_id,  context=None):		
		prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)		
		if uom_id != prod.uom_id.id:
			if uom_id != prod.uom_po_id.id:				 			
				raise osv.except_osv(
					_('UOM Mismatching Error !'),
					_('You choosed wrong UOM and you can choose either %s or %s for %s !!!') % (prod.uom_id.name,prod.uom_po_id.name,prod.name))	

		return True	
	
	def onchange_uom(self, cr, uid, ids, product_id, context=None):
		
		value = {'uom_id': '','uom_conversation_factor':''}
		if product_id:
			uom_rec = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			value = {'uom_conversation_factor':uom_rec.uom_conversation_factor}
			
		return {'value': value}
		
	def onchange_weight(self, cr, uid, ids, uom_conversation_factor,length,breadth,temp_qty,product_id, context=None):		
		value = {'qty': '','weight': '',}
		prod_rec = self.pool.get('product.product').browse(cr,uid,product_id)
		qty_value = 0.00
		weight=0.00
		if uom_conversation_factor == 'one_dimension':	
			if prod_rec.uom_id.id == prod_rec.uom_po_id.id:
				qty_value = temp_qty
				weight = 0.00
			else:				
				qty_value = length * temp_qty			
				weight = qty_value * prod_rec.po_uom_in_kgs
		if uom_conversation_factor == 'two_dimension':
			qty_value = length * breadth * temp_qty				
			weight = qty_value * prod_rec.po_uom_in_kgs		
		value = {'qty': qty_value,'weight':weight}			
		return {'value': value}
		
	
	
	def _check_line_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute('''select id from ch_kg_accessories_master where ms_id = %s and id != %s and header_id = %s ''',[entry.ms_id.id,entry.id,entry.header_id.id])
		duplicate_id = cr.fetchone()
		if duplicate_id:
			if duplicate_id[0] != None:
				raise osv.except_osv(_('Warning'), _('Duplicate of Check Item Name (%s) is not allowed')%(entry.ms_id.name))
		if entry.qty <= 0:			
			raise osv.except_osv(_('Warning'), _('Qty should be greater than zero for (%s) ')%(entry.ms_id.name))
		return True 	
		
	_constraints = [		
			  
		(_check_line_duplicates, ' ',['Qty or Length']),	
				
	   ]
			
ch_kg_accessories_master()





class ch_foundation_bolt(osv.osv):

	_name = "ch.foundation.bolt"
	_description = "Foundation Bolt Configuration Details"
	
	_columns = {
	
		'header_id':fields.many2one('kg.accessories.master', 'Foundation Bolt Configuration', ondelete='cascade',required=True),
		'access_id': fields.many2one('kg.accessories.master','Foundation Bolt',domain="[('state','not in',('reject','cancel')),('accessories_type','=','foundation_bolt')]"),
		'remarks':fields.text('Remarks'),   
	
	}
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(""" select access_id from ch_foundation_bolt where access_id  = '%s' and header_id = '%s' """ %(entry.access_id.id,entry.header_id.id))
		data = cr.dictfetchall()			
		if len(data) > 1:		
			return False
		return True	
		
	_constraints = [		
		(_check_values, 'Please Check the same Foundation Bolt not allowed..!!',['Foundation Bolt']),			
	   ]

ch_foundation_bolt()


