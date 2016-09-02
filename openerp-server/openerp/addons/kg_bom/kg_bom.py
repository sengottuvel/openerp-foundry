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
					as sam  """ %('kg_bom'))
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
		'category_type': fields.selection([('pump_bom','Pump BOM'),('part_list_bom','Part list BOM')],'Category', required=True),	
		
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
		
	def _pump_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.name:
			pump_name = rec.pump_model_id
			if rec.category_type =='pump_bom':									
				cr.execute(""" select * from kg_bom where pump_model_id  = '%s' and state != '%s' """ %(pump_name.id,'reject'))
				data = cr.dictfetchall()			
				if len(data) > 1:
					res = False
			else:
				res = True				
		return res

	def entry_confirm(self,cr,uid,ids,context=None):		
		rec = self.browse(cr,uid,ids[0])
		bom_obj = self.pool.get('kg.bom')
		bom_foundry_lines=rec.line_ids			 
		machine_shop_lines=rec.line_ids_a			 
		bot_lines=rec.line_ids_b			 
		consu_lines=rec.line_ids_c			
		if len(rec.line_ids) == 0  and len(rec.line_ids_a) == 0 and len(rec.line_ids_b) == 0:
			raise osv.except_osv(
					_('Warning !!!'),
					_('Please Check Line empty values not allowed!!'))		
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
		#~ if old_ids:
			#~ bom_rec = bom_obj.browse(cr, uid, old_ids[0])			  
			#~ if rec.name == bom_rec.name and rec.type != 'amendment':
				#~ raise osv.except_osv(_('Warning !'), _('BOM Name must be uniqe!!'))	
				
		### Check Duplicates Foundry Items  start ###
		
		if rec.bom_type == 'copy_bom':
			
			cr.execute('''select 

					bom_line.pattern_id,
					bom_line.pos_no,
					bom_line.qty

					from ch_bom_line bom_line 

					left join kg_bom header on header.id  = bom_line.header_id

					where header.bom_type = 'copy_bom' and header.id = %s''',[rec.id])
			
			source_bom_ids = cr.fetchall()
			
			source_bom_len = len(source_bom_ids)
			
			
			
			cr.execute('''select 

					bom_line.pattern_id,
					bom_line.pos_no,
					bom_line.qty

					from ch_bom_line bom_line 

					where bom_line.header_id  = %s''',[rec.source_bom.id])
			
			source_old_bom_ids = cr.fetchall()
			
			source_old_bom_len = len(source_old_bom_ids)
							
			cr.execute('''select 

					bom_line.pattern_id,
					bom_line.pos_no,
					bom_line.qty

					from ch_bom_line bom_line 

					left join kg_bom header on header.id  = bom_line.header_id

					where header.bom_type = 'copy_bom' and header.id = %s

					INTERSECT

					select 

					bom_line.pattern_id,
					bom_line.pos_no,
					bom_line.qty

					from ch_bom_line bom_line 

					where bom_line.header_id  = %s ''',[rec.id,rec.source_bom.id])
			repeat_ids = cr.fetchall()
			
			new_bom_len = len(repeat_ids)
			
			### Check Duplicates Foundry Items end.... ###
			
			
			
			### Check Duplicates Machine Shop Items  start ###
			
			cr.execute('''select 

					machine_line.ms_id,
					machine_line.pos_no,
					machine_line.qty

					from ch_machineshop_details machine_line 

					left join kg_bom header on header.id  = machine_line.header_id

					where header.bom_type = 'copy_bom' and header.id = %s''',[rec.id])
			
			ms_new_bom_ids = cr.fetchall()
			
			ms_new_bom_len = len(ms_new_bom_ids)
			
			cr.execute('''select 

					machine_line.ms_id,
					machine_line.pos_no,
					machine_line.qty

					from ch_machineshop_details machine_line 

					where machine_line.header_id  = %s''',[rec.source_bom.id])
			
			ms_old_bom_ids = cr.fetchall()
			
			ms_old_bom_len = len(ms_old_bom_ids)
							
			cr.execute('''select 

					machine_line.ms_id,
					machine_line.pos_no,
					machine_line.qty

					from ch_machineshop_details machine_line 

					left join kg_bom header on header.id  = machine_line.header_id

					where header.bom_type = 'copy_bom' and header.id = %s

					INTERSECT

					select 

					machine_line.ms_id,
					machine_line.pos_no,
					machine_line.qty

					from ch_machineshop_details machine_line 

					where machine_line.header_id  = %s ''',[rec.id,rec.source_bom.id])
			ms_repeat_ids = cr.fetchall()
			
			ms_join_bom_len = len(ms_repeat_ids)
			
			### Check Duplicates Machine Shop end.... ###
			
			
			
			### Check Duplicates BOT Items  start ###
			
			
			
			cr.execute('''select 

					bot_line.bot_id,
					bot_line.pos_no,
					bot_line.qty

					from ch_bot_details bot_line 

					left join kg_bom header on header.id  = bot_line.header_id

					where header.bom_type = 'copy_bom' and header.id = %s''',[rec.id])
			
			bot_new_bom_ids = cr.fetchall()
			
			bot_new_bom_len = len(bot_new_bom_ids)
			
			cr.execute('''select 

					bot_line.bot_id,
					bot_line.pos_no,
					bot_line.qty

					from ch_bot_details bot_line 

					where bot_line.header_id  = %s ''',[rec.source_bom.id])
			
			bot_old_bom_ids = cr.fetchall()
			
			bot_old_bom_len = len(bot_old_bom_ids)
							
			cr.execute('''select 

					bot_line.bot_id,
					bot_line.pos_no,
					bot_line.qty

					from ch_bot_details bot_line 

					left join kg_bom header on header.id  = bot_line.header_id

					where header.bom_type = 'copy_bom' and header.id = %s

					INTERSECT

					select 

					bot_line.bot_id,
					bot_line.pos_no,
					bot_line.qty

					from ch_bot_details bot_line 

					where bot_line.header_id  = %s ''',[rec.id,rec.source_bom.id])
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
								_('Same BOM Details are already exist !!'))
		
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
	def convert_partlist_bom(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		print"rec.pump_model_id",rec.pump_model_id
		if rec.pump_model_id:							   
			self.write(cr, uid, ids, {'state': 'draft','category_type': 'pump_bom'})
		else:
			raise osv.except_osv(_('Pump Model is must !!'),
				_('Enter the pump model field !!'))
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
		
	_constraints = [
		
		(_pump_validate, 'Pump Model name must be unique !!', ['Pump Name']),			
		
	]
	
kg_bom()



class ch_bom_line(osv.osv):
	
	_name = 'ch.bom.line'
	
	
	_columns = {
		
		'header_id':fields.many2one('kg.bom', 'BOM Name', required=True, ondelete='cascade'),  
		'pos_no': fields.integer('Position No'),
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
		
	def _check_line_qty(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])		
		if entry.qty <= 0:			
			return False
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
		return super(ch_bom_line, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		pattern_obj = self.pool.get('kg.pattern.master')
		if vals.get('pattern_id'):
			pattern_rec = pattern_obj.browse(cr, uid, vals.get('pattern_id') )
			pattern_name = pattern_rec.pattern_name
			vals.update({'pattern_name': pattern_name,'csd_no':pattern_rec.csd_code})		
		return super(ch_bom_line, self).write(cr, uid, ids, vals, context)  
		
	_constraints = [
		
		(_check_line_qty, 'Foundry Items Qty Zero and negative not accept', ['Qty']),	   
		
	]

	
ch_bom_line()


class ch_machineshop_details(osv.osv):

	_name = "ch.machineshop.details"
	_description = "BOM machineshop Details"
	
	
	_columns = {
	
		'header_id':fields.many2one('kg.bom', 'BOM', ondelete='cascade',required=True),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code',domain = [('type','=','ms')], ondelete='cascade',required=True),		
		'pos_no': fields.integer('Position No'),
		'position_id': fields.many2one('kg.position.number','Position No', required=True,domain="[('active','=','t')]"), 	
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
	
	def _check_line_qty(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])		
		if entry.qty <= 0:			
			return False
		return True
		
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
	_constraints = [
		
		(_check_line_qty, 'Machine Shop items Qty Zero and negative not accept', ['Qty']),	   
		
	]   

ch_machineshop_details()

class ch_bot_details(osv.osv):
	
	_name = "ch.bot.details"
	_description = "BOM BOT Details"	
	
	_columns = {
	
		'header_id':fields.many2one('kg.bom', 'BOM', ondelete='cascade',required=True),
		'bot_id':fields.many2one('kg.machine.shop', 'Item Code',domain = [('type','=','bot')], ondelete='cascade',required=True),
		'pos_no': fields.integer('Position No'),
		'position_id': fields.many2one('kg.position.number','Position No',domain="[('active','=','t')]"), 		
		'name':fields.char('Item Name', size=128),	  
		'qty': fields.integer('Qty', required=True),
		'remarks':fields.text('Remarks'),   
	
	}
	
	def onchange_bot_name(self, cr, uid, ids, bot_id, context=None):	   
		value = {'name': ''}
		if bot_id:
			pro_rec = self.pool.get('kg.machine.shop').browse(cr, uid, bot_id, context=context)
			value = {'name': pro_rec.name}		  
		return {'value': value}
		
	def create(self, cr, uid, vals, context=None):	  
		product_obj = self.pool.get('kg.machine.shop')
		if vals.get('bot_id'):		 
			product_rec = product_obj.browse(cr, uid, vals.get('bot_id') )
			product_code = product_rec.name		 
			vals.update({'name':product_code })
		return super(ch_bot_details, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		product_obj = self.pool.get('kg.machine.shop')
		if vals.get('bot_id'):		 
			product_rec = product_obj.browse(cr, uid, vals.get('bot_id') )
			product_code = product_rec.name
			vals.update({'name':product_code })
		return super(ch_bot_details, self).write(cr, uid, ids, vals, context) 
		
	def _check_line_qty(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])		
		if entry.qty <= 0:			
			return False
		return True 
	_constraints = [
		
		(_check_line_qty, 'BOT Items Qty Zero and negative not accept', ['Qty']),	   
		
	]
	
	
ch_bot_details()

class ch_consu_details(osv.osv):
	
	_name = "ch.consu.details"
	_description = "BOM Consumable Details" 
	
	_columns = {
	
		'header_id':fields.many2one('kg.bom', 'BOM', ondelete='cascade',required=True),
		'product_temp_id':fields.many2one('product.product', 'Item Name',domain = [('product_type','=','consu')], ondelete='cascade',required=True),		
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


