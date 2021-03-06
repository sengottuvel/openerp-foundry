from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import math

def roundPartial (value, resolution):
	return round (value / resolution) * resolution

class kg_primecost_view(osv.osv):
	
	_name = "kg.primecost.view"
	_description = "Statndard Transaction"
	_order = "entry_date desc"
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		pump_cost = total_cost = 0.00
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'pump_cost': 0.0,
				'total_cost': 0.0,
			}
			if order.line_ids:
				for line in order.line_ids:
					if line.is_applicable == True:
						pump_cost += line.prime_cost
			if order.line_ids_a:
				for line in order.line_ids_a:
					if line.is_applicable == True:
						pump_cost += line.prime_cost
			if order.line_ids_b:
				for line in order.line_ids_b:
					if line.is_applicable == True:
						pump_cost += line.prime_cost
			if order.line_ids_c:
				for line in order.line_ids_c:
					if line.line_ids:
						for a in line.line_ids:
							pump_cost += a.prime_cost
					if line.line_ids_a:
						for a in line.line_ids_a:
							pump_cost += a.prime_cost
					if line.line_ids_b:
						for a in line.line_ids_b:
							pump_cost += a.prime_cost
			if order.line_ids_spare_bom:
				for line in order.line_ids_spare_bom:
					pump_cost += line.prime_cost
			
			pump_cost = pump_cost / order.qty
			total_cost = pump_cost * order.qty
			res[order.id]['pump_cost'] = pump_cost
			res[order.id]['total_cost'] = total_cost
		
		return res
	
	_columns = {
		
		## Version 0.1
		
		## Basic Info
		
		'name': fields.char('No', size=12,select=True,readonly=True),
		'entry_date': fields.date('Entry Date',required=True),		
		'note': fields.text('Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_sms': fields.boolean('SMS Notification'),
		'flag_email': fields.boolean('Email Notification'),
		'flag_spl_approve': fields.boolean('Special Approval'),
		
		## Entry Info
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),	
		'active': fields.boolean('Active'),	
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
		
		'pump_id': fields.many2one('kg.pumpmodel.master', 'Pump Model'),
		'qty': fields.integer('Qty'),
		'moc_const_id': fields.many2one('kg.moc.construction', 'MOC Construction'),
		'load_bom': fields.boolean('Load BOM',readonly=True, states={'draft':[('readonly',False)]}),
		'pump_cost': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Pump Cost',multi="sums",store=True),	
		'total_cost': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Cost',multi="sums",store=True),	
		
		'pump_model_type':fields.selection([('vertical','Vertical'),('horizontal','Horizontal')], 'Pump Type',readonly=True, states={'draft':[('readonly',False)]}),
		'speed_in_rpm': fields.float('Speed in RPM - Pump',readonly=True, states={'draft':[('readonly',False)]}),
		'rpm': fields.selection([('1450','1450'),('2900','2900')],'RPM',readonly=True, states={'draft':[('readonly',False)]}),
		'motor_power': fields.selection([('90','90'),('100','100'),('112','112'),('132','132'),('160','160'),('180','180'),('200','200'),('225','225'),
				('250','250'),('280','280'),('315','315'),('315_l','315L')],'Motor Frame size',readonly=True, states={'draft':[('readonly',False)]}),
		'setting_height': fields.float('Setting Height (MM)'),
		'del_pipe_size': fields.selection([('32','32'),('40','40'),('50','50'),('65','65'),('80','80'),('100','100'),('125','125'),('150','150'),('200','200'),('250','250'),('300','300')],'Delivery Pipe Size(MM)',readonly=True, states={'draft':[('readonly',False)]}),
		'shaft_sealing': fields.selection([('g_p','Gland Packing'),('m_s','Mechanical Seal'),('f_s','Felt Seal'),('d_s','Dynamic Seal')],'Shaft Sealing',readonly=True, states={'draft':[('readonly',False)]}),
		'bush_bearing': fields.selection([('grease','Bronze'),('cft_self','CFT'),('cut_less_rubber','Cut less Rubber')],'Bush Bearing',readonly=True, states={'draft':[('readonly',False)]}),
		'bush_bearing_lubrication':fields.selection([('grease','Grease'),('external','External'),('self','Self'),('ex_pressure','External Under Pressure')], 'Bush Bearing Lubrication',readonly=True, states={'draft':[('readonly',False)]}),
		'motor_kw': fields.float('Motor KW',readonly=True, states={'draft':[('readonly',False)]}),
		'moc_construction_name': fields.char('MOC Construction Name',readonly=True),
		'purpose_categ': fields.selection([('pump','Pump'),('spare','Spare')],'Purpose'),
		
		## Child Tables Declaration 
		
		'line_ids': fields.one2many('ch.primecost.view.fou', 'header_id', "Fou Details",readonly=True, states={'draft':[('readonly',False)]}),
		'line_ids_a': fields.one2many('ch.primecost.view.ms', 'header_id', "MS Details",readonly=True, states={'draft':[('readonly',False)]}),
		'line_ids_b': fields.one2many('ch.primecost.view.bot', 'header_id', "BOT Details",readonly=True, states={'draft':[('readonly',False)]}),
		'line_ids_spare_bom': fields.one2many('ch.primecost.view.spare.bom', 'header_id', "Spare BOM",readonly=True, states={'draft':[('readonly',False)]}),
		'line_ids_c': fields.one2many('ch.primecost.view.access', 'header_id', "Accessories",readonly=True, states={'draft':[('readonly',False)]}),
		
	}
	
	_defaults = {
		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.primecost.view', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',
		'active': True,
		'entry_mode': 'manual',
		'flag_sms': False,
		'flag_email': False,
		'flag_spl_approve': False,
		'qty': 1,
		
	}	
		
	def _check_lineitems(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if not entry.line_ids:
			return False
		return True
	
	def _check_is_applicable(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.line_ids:
			for line in entry.line_ids:
				if line.is_applicable == True and not line.moc_id:
					raise osv.except_osv(_('Warning!'),_('Pattern Name %s You cannot save without MOC'%(line.pattern_id.name)))
		if entry.line_ids_a:
			for line in entry.line_ids_a:
				if line.is_applicable == True and not line.moc_id:
					raise osv.except_osv(_('Warning!'),_('Item Name %s You cannot save without MOC'%(line.ms_id.name)))
		if entry.line_ids_b:
			for line in entry.line_ids_b:
				if line.is_applicable == True and not line.moc_id:
					raise osv.except_osv(_('Warning!'),_('Item Name %s You cannot save without MOC'%(line.bot_id.name)))
		if entry.line_ids_spare_bom:
			for item in entry.line_ids_spare_bom:
				if item.line_ids:
					for line in item.line_ids:
						if line.is_applicable == True and not line.moc_id:
							raise osv.except_osv(_('Warning!'),_('Spare BOM Pattern Name %s You cannot save without MOC'%(line.pattern_id.name)))
				if item.line_ids_a:
					for line in item.line_ids_a:
						if line.is_applicable == True and not line.moc_id:
							raise osv.except_osv(_('Warning!'),_('Spare BOM Item Name %s You cannot save without MOC'%(line.ms_id.name)))
				if item.line_ids_b:
					for line in item.line_ids_b:
						if line.is_applicable == True and not line.moc_id:
							raise osv.except_osv(_('Warning!'),_('Spare BOM Item Name %s You cannot save without MOC'%(line.ms_id.name)))
		
		return True
	
	def _duplicate_removed(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.load_bom != True:
			cr.execute(''' delete from ch_primecost_view_fou where header_id = %s '''%(rec.id))
			cr.execute(''' delete from ch_primecost_view_ms where header_id = %s '''%(rec.id))
			cr.execute(''' delete from ch_primecost_view_bot where header_id = %s '''%(rec.id))
		return True
	
	def _ms_raw_length_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.line_ids_a and rec.pump_model_type == 'vertical':
			for item in rec.line_ids_a:
				length = 0
				if item.line_ids:
					length = sum(ele.length for ele in item.line_ids)
					if item.length < length:
						raise osv.except_osv(_('Warning!'),_('%s %s Mapped raw material length exceeds'%(rec.pump_id.name,item.ms_name)))
		return True
	
	_constraints = [        
            
			(_check_is_applicable, 'Kindly select anyone is appli !!',['']),		
			(_duplicate_removed, 'Duplicates removed !',['']),
		
       ]
       
	
	def onchange_moc_const(self, cr, uid, ids, moc_const_id):
		value = {'moc_construction_name':''}
		if moc_const_id:
			moc_rec = self.pool.get('kg.moc.construction').browse(cr,uid,moc_const_id)
			value = {'moc_construction_name':moc_rec.name}
		return {'value': value}
	
	def onchange_bom(self, cr, uid, ids, load_bom,pump_id,moc_const_id,qty,speed_in_rpm,rpm,setting_height,shaft_sealing,
					motor_power,bush_bearing,del_pipe_size,bush_bearing_lubrication,purpose_categ):
		delivery_pipe_size = del_pipe_size
		lubrication = bush_bearing_lubrication
		if qty <= 0:
			raise osv.except_osv(_('Warning!'),_('Quantity should be greater than zero'))
		if lubrication:
			if lubrication == 'external':
				lubrication = 'cft_ext'
			elif lubrication == 'self':
				lubrication = 'cft_self'
			elif lubrication == 'ex_pressure':
				lubrication = 'cut_less_rubber'
		
		pump_model_id = pump_id		
		rpm = rpm
		moc_construction_id = moc_const_id		
		fou_vals=[]
		ms_vals=[]
		ch_ms_vals = []
		bot_vals=[]
		data_rec = ''
		if load_bom == True and pump_id:
				bom_obj = self.pool.get('kg.bom').search(cr, uid, [('pump_model_id','=',pump_id),('state','in',('draft','confirmed','approved')),('category_type','=','pump_bom')])
				if bom_obj:
					data_rec = self.pool.get('kg.bom').browse(cr, uid, bom_obj[0])
		if data_rec:
			if data_rec.line_ids:
				for item in data_rec.line_ids:
					moc_id = ''
					pat_obj = self.pool.get('kg.pattern.master').search(cr,uid,[('id','=',item.pattern_id.id)])
					if pat_obj:
						pat_rec = self.pool.get('kg.pattern.master').browse(cr,uid,pat_obj[0])
						if pat_rec.line_ids:
							pat_line_obj = self.pool.get('ch.mocwise.rate').search(cr,uid,[('code','=',moc_const_id),('header_id','=',pat_rec.id)])
							if pat_line_obj:
								pat_line_rec = self.pool.get('ch.mocwise.rate').browse(cr,uid,pat_line_obj[0])
								moc_id = pat_line_rec.moc_id.id
					if purpose_categ == 'pump':
						is_applicable = True
					else:
						is_applicable = False
					fou_vals.append({
									'position_id': item.position_id.id,
									'pattern_id': item.pattern_id.id,
									'pattern_name': item.pattern_name,
									'moc_id': moc_id,
									'qty': item.qty * qty,
									'load_bom': True,
									'active': True,
									'is_applicable': is_applicable,
									'purpose_categ': purpose_categ,
									})
			if data_rec.line_ids_a:
				for item in data_rec.line_ids_a:
					moc_id = ''
					ch_ms_vals = []
					ms_obj = self.pool.get('kg.machine.shop').search(cr,uid,[('id','=',item.ms_id.id)])
					if ms_obj:
						ms_rec = self.pool.get('kg.machine.shop').browse(cr,uid,ms_obj[0])
						if ms_rec.line_ids_a:
							if moc_const_id:
								cons_rec = self.pool.get('kg.moc.construction').browse(cr,uid,moc_const_id)
								ms_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',cons_rec.id),('header_id','=',ms_rec.id)])
								if ms_line_obj:
									ms_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,ms_line_obj[0])
									moc_id = ms_line_rec.moc_id.id
						if ms_rec.line_ids:
							for raw in ms_rec.line_ids:
								ch_ms_vals.append([0, 0,{
										'product_id': raw.product_id.id,
										'uom': raw.uom.id,
										'od': raw.od,
										'length': raw.length,
										'breadth': raw.breadth,
										'thickness': raw.thickness,
										'weight': raw.weight * item.qty * qty,
										'uom_conversation_factor': raw.uom_conversation_factor,
										'temp_qty': raw.temp_qty * item.qty * qty,
										'qty': raw.qty * item.qty * qty,
										'remarks': raw.remarks,
										}])
							if purpose_categ == 'pump':
								is_applicable = True
							else:
								is_applicable = False
							ms_vals.append({
										'position_id': item.position_id.id,
										'ms_name': item.name,
										'ms_id': item.ms_id.id,
										'moc_id': moc_id,
										'qty': item.qty * qty,
										'load_bom': True,
										'is_applicable': is_applicable,
										'active': True,
										'purpose_categ': purpose_categ,
										'line_ids': ch_ms_vals,
										})
			if data_rec.line_ids_b:
				for item in data_rec.line_ids_b:
					moc_id = ''
					item_name = item.name
					bot_obj = self.pool.get('kg.machine.shop').search(cr,uid,[('id','=',item.bot_id.id)])
					if bot_obj:
						bot_rec = self.pool.get('kg.machine.shop').browse(cr,uid,bot_obj[0])
						if bot_rec.line_ids_a:
							if moc_const_id:
								cons_rec = self.pool.get('kg.moc.construction').browse(cr,uid,moc_const_id)
								bot_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',cons_rec.id),('header_id','=',bot_rec.id)])
								if bot_line_obj:
									bot_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,bot_line_obj[0])
									moc_id = bot_line_rec.moc_id.id
						if purpose_categ == 'pump':
							is_applicable = True
						else:
							is_applicable = False
						bot_vals.append({
										'position_id': item.position_id.id,
										'bot_name': item_name,
										'bot_id': item.bot_id.id,
										'moc_id': moc_id,
										'qty': item.qty * qty,
										'load_bom': True,
										'is_applicable': is_applicable,
										'active': True,
										'flag_is_bearing': bot_rec.is_bearing,
										'purpose_categ': purpose_categ,
										})
			
			if rpm != False:
				
				if shaft_sealing != False and motor_power != False and bush_bearing != False and setting_height > 0 and delivery_pipe_size != False and lubrication != False:
					
					#### Load Foundry Items ####
					
					if setting_height < 3000:
						limitation = 'upto_3000'
					if setting_height >= 3000:
						limitation = 'above_3000'
					
					### For Base Plate ###
					if setting_height < 3000:
						base_limitation = 'upto_2999'
					if setting_height >= 3000:
						base_limitation = 'above_3000'
					
					cr.execute('''
					
						-- Bed Assembly ----
						select bom.id,
						bom.header_id,
						bom.pattern_id,
						bom.pattern_name,
						bom.qty, 
						bom.pos_no,
						bom.position_id,
						pattern.pcs_weight, 
						pattern.ci_weight,
						pattern.nonferous_weight

						from ch_bom_line as bom

						LEFT JOIN kg_pattern_master pattern on pattern.id = bom.pattern_id

						where bom.header_id = 
						(
						select id from kg_bom 
						where id = (select partlist_id from ch_bed_assembly 
						where limitation = %s and packing = %s and header_id = 

						( select vo_id from ch_vo_mapping
						where rpm = %s and header_id = %s))
						and active='t'
						) 
						
						union all

						--- Motor Assembly ---
						select bom.id,
						bom.header_id,
						bom.pattern_id,
						bom.pattern_name,
						bom.qty, 
						bom.pos_no,
						bom.position_id,
						pattern.pcs_weight, 
						pattern.ci_weight,
						pattern.nonferous_weight

						from ch_bom_line as bom

						LEFT JOIN kg_pattern_master pattern on pattern.id = bom.pattern_id

						where bom.header_id = 
						(
						select id from kg_bom 
						where id = (select partlist_id from ch_motor_assembly 
						where value = %s and header_id = 

						( select vo_id from ch_vo_mapping
						where rpm = %s and header_id = %s ))
						and active='t'
						) 
						
						union all

						-- Column Pipe ------

						select bom.id,
						bom.header_id,
						bom.pattern_id,
						bom.pattern_name,
						bom.qty, 
						bom.pos_no,
						bom.position_id,
						pattern.pcs_weight, 
						pattern.ci_weight,
						pattern.nonferous_weight

						from ch_bom_line as bom

						LEFT JOIN kg_pattern_master pattern on pattern.id = bom.pattern_id

						where bom.header_id = 
						(
						select id from kg_bom 
						where id = (select partlist_id from ch_columnpipe_assembly 
						where pipe_type = %s and star = (select star from ch_power_series 
						where %s BETWEEN min AND max and %s <= max
						
						and header_id = ( select vo_id from ch_vo_mapping
						where rpm = %s and header_id = %s)
						
						) and header_id = 

						( select vo_id from ch_vo_mapping
						where rpm = %s and header_id = %s ))
						and active='t'
						)
						
						union all

						-- Delivery Pipe ------

						select bom.id,
						bom.header_id,
						bom.pattern_id,
						bom.pattern_name,
						bom.qty, 
						bom.pos_no,
						bom.position_id,
						pattern.pcs_weight, 
						pattern.ci_weight,
						pattern.nonferous_weight

						from ch_bom_line as bom

						LEFT JOIN kg_pattern_master pattern on pattern.id = bom.pattern_id

						where bom.header_id = 
						(
						select id from kg_bom 
						where id = (select partlist_id from ch_deliverypipe_assembly 
						where size = %s and star = (select star from ch_power_series 
						where %s BETWEEN min AND max and %s <= max
						
						and header_id = ( select vo_id from ch_vo_mapping
						where rpm = %s and header_id = %s)
						
						) and header_id = 

						( select vo_id from ch_vo_mapping
						where rpm = %s and header_id = %s))
						and active='t'
						) 
						
						union all

						-- Lubrication ------

						select bom.id,
						bom.header_id,
						bom.pattern_id,
						bom.pattern_name,
						bom.qty, 
						bom.pos_no,
						bom.position_id,
						pattern.pcs_weight, 
						pattern.ci_weight,
						pattern.nonferous_weight

						from ch_bom_line as bom

						LEFT JOIN kg_pattern_master pattern on pattern.id = bom.pattern_id

						where bom.header_id = 
						(
						select id from kg_bom 
						where id = (select partlist_id from ch_lubricant 
						where type = %s and star = (select star from ch_power_series 
						where %s BETWEEN min AND max and %s <= max
						
						and header_id = ( select vo_id from ch_vo_mapping
						where rpm = %s and header_id = %s)
						
						) and header_id = 

						( select vo_id from ch_vo_mapping
						where rpm = %s and header_id = %s))
						and active='t'
						) 
						
						union all
							
						-- Base Plate --
								
						select bom.id,
						bom.header_id,
						bom.pattern_id,
						bom.pattern_name,
						bom.qty, 
						bom.pos_no,
						bom.position_id,
						pattern.pcs_weight, 
						pattern.ci_weight,
						pattern.nonferous_weight

						from ch_bom_line as bom

						LEFT JOIN kg_pattern_master pattern on pattern.id = bom.pattern_id

						where bom.header_id = 
						(
						select id from kg_bom 
						where id = (select partlist_id from ch_base_plate
						where limitation = %s and header_id = (select id from kg_bom where pump_model_id = %s and active='t' and category_type = 'pump_bom'))
						and active='t'
						)
						
						  ''',[limitation,shaft_sealing,rpm,pump_model_id,motor_power,rpm,pump_model_id,
						  bush_bearing,setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,delivery_pipe_size,
						  setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,lubrication,setting_height,setting_height,
						  rpm,pump_model_id,rpm,pump_model_id,base_limitation,pump_model_id])
					vertical_foundry_details = cr.dictfetchall()					
					
					for vertical_foundry in vertical_foundry_details:						
							
						### Loading MOC from MOC Construction
						
						if moc_construction_id != False:
							
							cr.execute(''' select pat_moc.moc_id
								from ch_mocwise_rate pat_moc
								LEFT JOIN kg_moc_construction const on const.id = pat_moc.code
								where pat_moc.header_id = %s and const.id = %s
								  ''',[vertical_foundry['pattern_id'],moc_construction_id])
							const_moc_id = cr.fetchone()
							if const_moc_id != None:
								moc_id = const_moc_id[0]
							else:
								moc_id = False
						else:
							moc_id = False
						wgt = 0.00	
						if moc_id != False:
							moc_rec = self.pool.get('kg.moc.master').browse(cr, uid, moc_id)
							if moc_rec.weight_type == 'ci':
								wgt =  vertical_foundry['ci_weight']
							if moc_rec.weight_type == 'ss':
								wgt = vertical_foundry['pcs_weight']
							if moc_rec.weight_type == 'non_ferrous':
								wgt = vertical_foundry['nonferous_weight']
								
						
						bom_qty = vertical_foundry['qty']
						
						if vertical_foundry['position_id'] == None:
							raise osv.except_osv(_('Warning!'),
							_('Kindly Configure Position No. in Foundry Items for respective Pump Bom and proceed further !!'))
						if purpose_categ == 'pump':
							is_applicable = True
						else:
							is_applicable = False
						fou_vals.append({
							
							'pattern_id': vertical_foundry['pattern_id'],
							'pattern_name': vertical_foundry['pattern_name'],						
							'position_id': vertical_foundry['position_id'],			  
							'qty' : bom_qty * qty,
							'moc_id': moc_id,
							'is_applicable': is_applicable,
							'active': True,
							'load_bom': True,							
							'purpose_categ': purpose_categ,
							
							})
								
					#### Load Machine Shop Items ####
					
					cr.execute(''' 
								
								-- Bed Assembly ----
								select id,pos_no,position_id,ms_id,name,qty,header_id as bom_id
								from ch_machineshop_details
								where header_id = 
								(
								select id from kg_bom 
								where id = (select partlist_id from ch_bed_assembly 
								where limitation = %s and packing = %s and header_id = 

								( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s))
								and active='t'
								) 
								
								union all

								--- Motor Assembly ---
								select id,pos_no,position_id,ms_id,name,qty,header_id as bom_id
								from ch_machineshop_details
								where header_id =  
								(
								select id from kg_bom 
								where id = (select partlist_id from ch_motor_assembly 
								where value = %s and header_id = 

								( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s ))
								and active='t'
								) 
								
								union all

								-- Column Pipe ------

								select id,pos_no,position_id,ms_id,name,qty,header_id as bom_id
								from ch_machineshop_details
								where header_id = 
								(
								select id from kg_bom 
								where id = (select partlist_id from ch_columnpipe_assembly 
								where pipe_type = %s and star = (select star from ch_power_series 
								where %s BETWEEN min AND max and %s <= max
								
								and header_id = ( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s)
								
								) and header_id = 

								( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s))
								and active='t'
								)
						
								union all

								-- Delivery Pipe ------

								select id,pos_no,position_id,ms_id,name,qty,header_id as bom_id
								from ch_machineshop_details
								where header_id =  
								(
								select id from kg_bom 
								where id = (select partlist_id from ch_deliverypipe_assembly 
								where size = %s and star = (select star from ch_power_series 
								where %s BETWEEN min AND max and %s <= max
								
								and header_id = ( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s)
								
								) and header_id = 

								( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s))
								and active='t'
								) 
								
								union all

								-- Lubrication ------

								select id,pos_no,position_id,ms_id,name,qty,header_id as bom_id
								from ch_machineshop_details
								where header_id = 
								(
								select id from kg_bom 
								where id = (select partlist_id from ch_lubricant 
								where type = %s and star = (select star from ch_power_series 
								where %s BETWEEN min AND max and %s <= max
								
								and header_id = ( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s)
								
								) and header_id = 

								( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s ))
								and active='t'
								) 
								
								union all
								
								-- Base Plate --
								
								select id,pos_no,position_id,ms_id,name,qty,header_id as bom_id
								from ch_machineshop_details
								where header_id = 
								(
								select id from kg_bom 
								where id = (select partlist_id from ch_base_plate 
								where limitation = %s and header_id = (select id from kg_bom where pump_model_id = %s and active='t' and category_type = 'pump_bom') )
								and active='t'
								)
								
						  ''',[limitation,shaft_sealing,rpm,pump_model_id,motor_power,rpm,pump_model_id,
						  bush_bearing,setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,delivery_pipe_size,
						  setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,lubrication,setting_height,setting_height,
						  rpm,pump_model_id,rpm,pump_model_id,base_limitation,pump_model_id])
					vertical_ms_details = cr.dictfetchall()
					for vertical_ms_details in vertical_ms_details:
						
						### Loading MOC from MOC Construction
				
						if moc_construction_id != False:
							
							cr.execute(''' select machine_moc.moc_id
								from ch_machine_mocwise machine_moc
								LEFT JOIN kg_moc_construction const on const.id = machine_moc.code
								where machine_moc.header_id = %s and const.id = %s ''',[vertical_ms_details['ms_id'],moc_construction_id])
							const_moc_id = cr.fetchone()
							if const_moc_id != None:
								moc_id = const_moc_id[0]
							else:
								moc_id = False
						else:
							moc_id = False
							
						if vertical_ms_details['pos_no'] == None:
							pos_no = 0
						else:
							pos_no = vertical_ms_details['pos_no']
							
							
						### Dynamic Length Calculation ###
						length = 0.00
						a_value = 0.00
						a1_value = 0.00
						a2_value = 0.00
						star_value = 0
						ms_rec = self.pool.get('kg.machine.shop').browse(cr, uid, vertical_ms_details['ms_id'])
						if ms_rec.dynamic_length == True and ms_rec.length_type != False:
							
							### Getting Alpha Values from Pump Model ###
							cr.execute(''' select alpha_type,alpha_value
									from ch_alpha_value
									where header_id = %s ''',[pump_model_id])
							alpha_val = cr.dictfetchall()
							
							if alpha_val:
								for alpha_item in alpha_val:
									
									if alpha_item['alpha_type'] == 'a':
										a_value = alpha_item['alpha_value']
									elif alpha_item['alpha_type'] == 'a1':
										a1_value = alpha_item['alpha_value']
									elif alpha_item['alpha_type'] == 'a2':
										a2_value = alpha_item['alpha_value']
									else:
										a_value = 0.00
										a1_value = 0.00
										a2_value = 0.00
							else:
								a_value = 0.00
								a1_value = 0.00
								a2_value = 0.00
							
							### Getting No of Star Support from VO ###
							
							cr.execute(''' select (case when star = 'nil' then '0' else star end)::int as star from ch_power_series 
								where %s BETWEEN min AND max and %s <= max
								and header_id = ( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s) ''',[setting_height,setting_height,rpm,pump_model_id])
							star_val = cr.fetchone()
							star_value = star_val[0]
							
							
							### Getting ABOVE BP(H),BEND from pump model ###
							cr.execute(''' select h_value,b_value from ch_delivery_pipe
								where header_id = %s and delivery_size = %s ''',[pump_model_id,delivery_pipe_size])
							h_b_val = cr.dictfetchone()
							
							if h_b_val:
								h_value = h_b_val['h_value']
								b_value = h_b_val['b_value']
							else:
								h_value = 0.00
								b_value = 0.00
							
							if ms_rec.length_type == 'single_column_pipe':
								
								if star_value == 0:
								 
									### Formula ###
									#3.5+BP+SETTING HEIGHT-A1
									###
									length = 3.5 + bp + setting_height - a1_value
									
							### Getting BP and Shaft Ext from VO Master ###
							cr.execute('''
				
								 (select bp,shaft_ext from ch_bed_assembly 
								where limitation = %s and packing = %s and header_id = 

								( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s))
								
								
								  ''',[limitation,shaft_sealing,rpm,pump_model_id])
							bed_ass_details = cr.dictfetchone()
							if not bed_ass_details:
								bp = 0
								shaft_ext = 0
							else:
								if bed_ass_details['bp'] == None:
									bp = 0
								else:
									bp = bed_ass_details['bp']
								if bed_ass_details['shaft_ext'] == None:
									shaft_ext = 0
								else:
									shaft_ext = bed_ass_details['shaft_ext']
							
							### Getting Star Value ###
							cr.execute('''
							
								select star,lcp,ls from kg_vo_master 
								where id in 

								( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s)
								
								
								  ''',[rpm,pump_model_id])
							vo_star_value = cr.dictfetchone()
							
								
							if ms_rec.length_type == 'single_shaft':
								
								if star_value == 0:
								
									### Formula ###
									#SINGLE COL.PIPE+A2-3.5+SHAFT EXT
									###
									### Getting Single Column Pipe Length ###
									single_colpipe_length = 3.5 + bp + setting_height - a1_value
									length = single_colpipe_length + a2_value -3.5 + shaft_ext
								
							if ms_rec.length_type == 'delivery_pipe':
								if star_value == 0.0:
									### Formula ###
									#ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-1.5
									###
									length = h_value + bp + setting_height - a_value - b_value - 1.5
									number_dec = str(length-int(length))[1:]
									if number_dec >= 0.25:
										length = roundPartial (length, 0.50)
									else:
										length = length
								
								if star_value == 1:
									### Formula ###
									#(ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-3)/2
									###
									print "ddddddddddddddd",h_value, bp, setting_height, a_value, b_value
									length = (h_value + bp + setting_height - a_value - b_value - 3)/2
									number_dec = str(length-int(length))[1:]
									if number_dec >= 0.25:
										length = roundPartial (length, 0.50)
									else:
										length = length
								
								if star_value > 1:
									### Formula ###
									#(ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-1.5)-(NO OF STAR SUPPORT*1.5)/NO OF STAR SUPPORT+1
									###
									length = ((h_value+bp+setting_height-a_value-b_value-1.5)-(star_value*1.5))/(star_value+1)
									number_dec = str(length-int(length))[1:]
									if number_dec >= 0.25:
										length = roundPartial (length, 0.50)
									else:
										length = length
							
							if ms_rec.length_type == 'delivery_pipe_middle':
								if star_value == 0.0:
									### Formula ###
									#ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-1.5
									###
									length = h_value + bp + setting_height - a_value - b_value - 1.5
									number_dec = str(length-int(length))[1:]
									if number_dec >= 0.25 and number_dec <= 0.75:
										length = round(length, 0)
									if number_dec >= 0.75:
										length = round(length, 0)
										frac, whole = math.modf(length)
										if frac >= 0.5:
											length = (whole+0.5)
										elif frac < 0.5:
											length = (whole+0.0)
									else:
										length = length
									
								if star_value == 1:
									### Formula ###
									#(ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-3)/2
									###
									length = (h_value + bp + setting_height - a_value - b_value - 3)/2
									number_dec = str(length-int(length))[1:]
									if number_dec >= 0.25 and number_dec < 0.75:
										length = round(length, 0)
									if number_dec >= 0.75:
										frac, whole = math.modf(length)
										if frac >= 0.5:
											length = (whole+0.5)
										elif frac < 0.5:
											length = (whole+0.0)
									else:
										length = length
									
								if star_value > 1:
									### Formula ###
									#(ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-1.5)-(NO OF STAR SUPPORT*1.5)/NO OF STAR SUPPORT+1
									###
									length = ((h_value+bp+setting_height-a_value-b_value-1.5)-(star_value*1.5))/(star_value+1)
									number_dec = str(length-int(length))[1:]
									if number_dec >= 0.25 and number_dec < 0.75:
										length = round(length, 0)
									if number_dec >= 0.75:
										frac, whole = math.modf(length)
										if frac >= 0.5:
											length = (whole+0.5)
										elif frac < 0.5:
											length = (whole+0.0)
									else:
										length = length
							
							if ms_rec.length_type == 'drive_column_pipe':
								
								if star_value == 1:
									### Formula ###
									#(3.5+bp+setting height-a1-no of star support)/2
									###
									length = (3.5+bp+setting_height-a1_value-vo_star_value['star'])/2
									number_dec = str(length-int(length))[1:]
									if number_dec >= 0.25:
										length = roundPartial (length, 0.50)
									else:
										length = length
								
								if star_value > 1:
									### Formula ###
									#(3.5+bp+setting height-a1-(No. of star support * star support value)-((No. Of star support-1) * LINE COLUMN PIPE value))/2
									###
									### Calculating Line Column Pipe ###
									### Formula = Standard Length ###
									line_column_pipe = vo_star_value['lcp']
									length = (3.5+bp+setting_height-a1_value-(star_value * vo_star_value['star'])-((star_value-1)*line_column_pipe))/2
									number_dec = str(length-int(length))[1:]
									if number_dec >= 0.25:
										length = roundPartial (length, 0.50)
									else:
										length = length
							
							if ms_rec.length_type == 'pump_column_pipe':
								
								if star_value == 1:
									### Formula ###
									#(3.5+bp+setting height-a1-no of star support)/2
									###
									length = (3.5+bp+setting_height-a1_value-vo_star_value['star'])/2
									number_dec = str(length-int(length))[1:]
									if number_dec >= 0.25 and number_dec < 0.75:
										length = round(length, 0)
									if number_dec >= 0.75:
										frac, whole = math.modf(length)
										if frac >= 0.5:
											length = (whole+0.5)
										elif frac < 0.5:
											length = (whole+0.0)
									else:
										length = length
								
								if star_value > 1:
									### Formula ###
									#(3.5+bp+setting height-a1-no of star support-NO OF LINE COLUMN PIPE)/2
									###
									### Calculating Line Column Pipe ###
									### Formula = Standard Length ###
									line_column_pipe = vo_star_value['lcp']
									length = (3.5+bp+setting_height-a1_value-(star_value * vo_star_value['star'])-((star_value-1)*line_column_pipe))/2
									number_dec = str(length-int(length))[1:]
									if number_dec >= 0.25 and number_dec < 0.75:
										length = round(length, 0)
									if number_dec >= 0.75:
										frac, whole = math.modf(length)
										if frac >= 0.5:
											length = (whole+0.5)
										elif frac < 0.5:
											length = (whole+0.0)
									else:
										length = length
							
							if ms_rec.length_type == 'pump_shaft':
								
								if star_value == 1:
									### Formula ###
									#(STAR SUPPORT/2-1)+PUMP COLOUMN PIPE+A2
									###
									pump_column_pipe = (3.5+bp+setting_height-a1_value-vo_star_value['star'])/2
									number_dec = str(length-int(pump_column_pipe))[1:]
									if number_dec >= 0.25 and number_dec < 0.75:
										pump_column_pipe = round(pump_column_pipe, 0)
									if number_dec >= 0.75:
										frac, whole = math.modf(pump_column_pipe)
										if frac >= 0.5:
											pump_column_pipe = (whole+0.5)
										elif frac < 0.5:
											pump_column_pipe = (whole+0.0)
									else:
										pump_column_pipe = pump_column_pipe
									length = (star_value/2-1)+pump_column_pipe+a2_value
									
									
								if star_value > 1:
									### Formula ###
									#(STAR SUPPORT/2-1)+PUMP COLOUMN PIPE+A2
									###
									line_column_pipe = vo_star_value['lcp']
									pump_column_pipe = (3.5+bp+setting_height-a1_value-(star_value * vo_star_value['star'])-((star_value-1)*line_column_pipe))/2
									number_dec = str(length-int(pump_column_pipe))[1:]
									if number_dec >= 0.25 and number_dec < 0.75:
										pump_column_pipe = round(pump_column_pipe, 0)
									if number_dec >= 0.75:
										frac, whole = math.modf(pump_column_pipe)
										if frac >= 0.5:
											pump_column_pipe = (whole+0.5)
										elif frac < 0.5:
											pump_column_pipe = (whole+0.0)
									else:
										pump_column_pipe = pump_column_pipe
									length = ((vo_star_value['star']/2)-1)+pump_column_pipe+a2_value
									
							if ms_rec.length_type == 'drive_shaft':
								
								if star_value == 1:
									### Formula ###
									#(STAR SUPPORT/2-1)+DRIVE COLOUMN PIPE-3.5+SHAFT EXT
									###
									drive_col_pipe = (3.5+bp+setting_height-a1_value-vo_star_value['star'])/2
									number_dec = str(length-int(drive_col_pipe))[1:]
									if number_dec >= 0.25:
										drive_col_pipe = roundPartial (drive_col_pipe, 0.50)
									else:
										drive_col_pipe = drive_col_pipe
									length = (star_value/2-1)+drive_col_pipe-3.5+shaft_ext
									
								if star_value > 1:
									### Formula ###
									#(STAR SUPPORT/2-1)+DRIVE COLOUMN PIPE-3.5+SHAFT EXT
									###
									line_column_pipe = vo_star_value['lcp']
									drive_col_pipe = (3.5+bp+setting_height-a1_value-(star_value * vo_star_value['star'])-((star_value-1)*line_column_pipe))/2
									number_dec = str(length-int(drive_col_pipe))[1:]
									if number_dec >= 0.25:
										drive_col_pipe = roundPartial (drive_col_pipe, 0.50)
									else:
										drive_col_pipe = drive_col_pipe
									length = ((vo_star_value['star']/2)-1)+drive_col_pipe-3.5+shaft_ext
						
						
						if length > 0:
							ms_bom_qty = round(length,0)
						else:
							ms_bom_qty = 0						
						
						vertical_ms_qty = ms_bom_qty					
						
						if vertical_ms_details['position_id'] == None:
							raise osv.except_osv(_('Warning!'),
							_('Kindly Configure Position No. in MS Items for respective Pump Bom and proceed further !!'))
						
						if vertical_ms_details['ms_id']:
							ms_rec = self.pool.get('kg.machine.shop').browse(cr,uid,vertical_ms_details['ms_id'])
							ms_raw_rec = self.pool.get('ch.machineshop.details').browse(cr,uid,vertical_ms_details['id'])
							if ms_rec.line_ids_a:
								if ms_rec.line_ids:
									ch_ms_vals = []
									for raw in ms_rec.line_ids:
										ch_ms_vals.append([0, 0,{
												'product_id': raw.product_id.id,
												'uom': raw.uom.id,
												'od': raw.od,
												'length': raw.length,
												'breadth': raw.breadth,
												'thickness': raw.thickness,
												'weight': raw.weight * ms_raw_rec.qty * qty,
												'uom_conversation_factor': raw.uom_conversation_factor,
												'temp_qty': raw.temp_qty * ms_raw_rec.qty * qty,
												'qty': raw.qty * ms_raw_rec.qty * qty,
												'remarks': raw.remarks,
												}])
						if purpose_categ == 'pump':
							is_applicable = True
						else:
							is_applicable = False
						ms_vals.append({
							
							'position_id':vertical_ms_details['position_id'],
							'ms_id': vertical_ms_details['ms_id'],
							'qty': vertical_ms_details['qty'] * qty,
							'ms_name': vertical_ms_details['name'],
							'length': vertical_ms_qty,
							'load_bom': True,
							'is_applicable': is_applicable,
							'active': True,
							'moc_id': moc_id,
							'purpose_categ': purpose_categ,
							'line_ids': ch_ms_vals,						
																  
							})					
							
							
					#### Load BOT Items ####
					
					bom_bot_obj = self.pool.get('ch.machineshop.details')
					cr.execute(''' 
								
								-- Bed Assembly ----
								select id,bot_id,qty,position_id,header_id as bom_id
								from ch_bot_details
								where header_id =
								(
								select id from kg_bom 
								where id = (select partlist_id from ch_bed_assembly 
								where limitation = %s and packing = %s and header_id = 

								( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s))
								and active='t'
								) 
								
								union all

								--- Motor Assembly ---
								select id,bot_id,qty,position_id,header_id as bom_id
								from ch_bot_details
								where header_id =
								(
								select id from kg_bom 
								where id = (select partlist_id from ch_motor_assembly 
								where value = %s and header_id = 

								( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s))
								and active='t'
								) 
								
								union all

								-- Column Pipe ------

								select id,bot_id,qty,position_id,header_id as bom_id
								from ch_bot_details
								where header_id =
								(
								select id from kg_bom 
								where id = (select partlist_id from ch_columnpipe_assembly 
								where pipe_type = %s and star = (select star from ch_power_series 
								where %s BETWEEN min AND max and %s <= max
								and header_id = ( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s)
								
								) and header_id = 

								( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s))
								and active='t'
								)
								
								union all

								-- Delivery Pipe ------

								select id,bot_id,qty,position_id,header_id as bom_id
								from ch_bot_details
								where header_id =  
								(
								select id from kg_bom 
								where id = (select partlist_id from ch_deliverypipe_assembly 
								where size = %s and star = (select star from ch_power_series 
								where %s BETWEEN min AND max and %s <= max
								
								and header_id = ( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s)
								
								)and header_id = 

								( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s))
								and active='t'
								) 
								
								union all

								-- Lubrication ------

								select id,bot_id,qty,position_id,header_id as bom_id
								from ch_bot_details
								where header_id =
								(
								select id from kg_bom 
								where id = (select partlist_id from ch_lubricant 
								where type = %s and star = (select star from ch_power_series 
								where %s BETWEEN min AND max and %s <= max
								
								and header_id = ( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s)
								
								)and header_id = 

								( select vo_id from ch_vo_mapping
								where rpm = %s and header_id = %s))
								and active='t'
								) 
								
								union all
									
								-- Base Plate --
								
								select id,bot_id,qty,position_id,header_id as bom_id
								from ch_bot_details
								where header_id =
								(
								select id from kg_bom 
								where id = (select partlist_id from ch_base_plate 
								where limitation = %s and header_id = (select id from kg_bom where pump_model_id = %s and active='t' and category_type = 'pump_bom') )
								and active='t'
								)
								
						  ''',[limitation,shaft_sealing,rpm,pump_model_id,motor_power,rpm,pump_model_id,
						  bush_bearing,setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,delivery_pipe_size,
						  setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,lubrication,setting_height,setting_height,
						  rpm,pump_model_id,rpm,pump_model_id,base_limitation,pump_model_id])
					vertical_bot_details = cr.dictfetchall()
					
					for vertical_bot_details in vertical_bot_details:
						
						### Loading MOC from MOC Construction
				
						if moc_construction_id != False:
							
							cr.execute(''' select bot_moc.moc_id
								from ch_machine_mocwise bot_moc
								LEFT JOIN kg_moc_construction const on const.id = bot_moc.code
								where bot_moc.header_id = %s and const.id = %s ''',[vertical_bot_details['bot_id'],moc_construction_id])
							const_moc_id = cr.fetchone()
							if const_moc_id != None:
								moc_id = const_moc_id[0]
							else:
								moc_id = False
						else:
							moc_id = False
							
						vertical_bot_qty = vertical_bot_details['qty']
						bot_obj = self.pool.get('kg.machine.shop')
						bot_rec = bot_obj.browse(cr, uid, vertical_bot_details['bot_id'])
						if purpose_categ == 'pump':
							is_applicable = True
						else:
							is_applicable = False
						bot_vals.append({						
							
							'bot_id': vertical_bot_details['bot_id'],
							'position_id': vertical_bot_details['position_id'] or False,
							'qty': vertical_bot_qty * qty,
							'load_bom': True,
							'is_applicable': is_applicable,
							'active': True,
							'flag_is_bearing': bot_rec.is_bearing,
							'moc_id': moc_id,
							'purpose_categ': purpose_categ,
							})						
							
							
		return {'value': {'line_ids': fou_vals,'line_ids_a': ms_vals,'line_ids_b': bot_vals}}
	
	def prime_cost_update(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			prime_cost = 0.0
			crm_obj = self.pool.get('kg.crm.enquiry')
			if entry.line_ids:
				prime_cost = 0
				for foundry_item in entry.line_ids:
					if foundry_item.is_applicable == True:
						fou_prime_cost = crm_obj._prime_cost_calculation(cr,uid,'foundry',foundry_item.pattern_id.id,
						0,0,0,entry.moc_const_id.id,foundry_item.moc_id.id,0)
						self.pool.get('ch.primecost.view.fou').write(cr,uid,foundry_item.id,{'prime_cost':fou_prime_cost * foundry_item.qty })
						prime_cost += fou_prime_cost * foundry_item.qty
						
			if entry.line_ids_a:
				prime_cost = 0
				for ms_item in entry.line_ids_a:
					if ms_item.is_applicable == True:
						ms_prime_cost = crm_obj._prime_cost_calculation(cr,uid,'ms',0,
						ms_item.ms_id.id,ms_item,0,entry.moc_const_id.id,ms_item.moc_id.id,0)
						self.pool.get('ch.primecost.view.ms').write(cr,uid,ms_item.id,{'prime_cost':ms_prime_cost })
						prime_cost += ms_prime_cost 
						
			if entry.line_ids_b:
				prime_cost = 0
				for bot_item in entry.line_ids_b:
					if bot_item.is_applicable == True:
						if bot_item.flag_is_bearing == True:
							if not bot_item.brand_id:
								raise osv.except_osv(_('Warning!'),_('%s You cannot save without Brand'%(bot_item.bot_id.code)))
						bot_prime_cost = crm_obj._prime_cost_calculation(cr,uid,'bot',0,
						0,0,bot_item.bot_id.id,entry.moc_const_id.id,bot_item.moc_id.id,bot_item.brand_id.id)
						self.pool.get('ch.primecost.view.bot').write(cr,uid,bot_item.id,{'prime_cost':bot_prime_cost * bot_item.qty})
						prime_cost += bot_prime_cost * bot_item.qty
						
			## Spare BOM primecost start
			if entry.line_ids_spare_bom:
				for item in entry.line_ids_spare_bom:
					pump_prime_cost = 0
					if item.line_ids:
						prime_cost = 0
						for foundry_item in item.line_ids:
							if foundry_item.is_applicable == True:
								fou_prime_cost = crm_obj._prime_cost_calculation(cr,uid,'foundry',foundry_item.pattern_id.id,
								0,0,0,entry.moc_const_id.id,foundry_item.moc_id.id,0)
								self.pool.get('ch.primecost.view.spare.fou').write(cr,uid,foundry_item.id,{'prime_cost':fou_prime_cost * foundry_item.qty })
								prime_cost += fou_prime_cost * foundry_item.qty
						pump_prime_cost += prime_cost		
					if item.line_ids_a:
						prime_cost = 0
						for ms_item in item.line_ids_a:
							if ms_item.is_applicable == True:
								ms_prime_cost = crm_obj._prime_cost_calculation(cr,uid,'ms',0,
								ms_item.ms_id.id,ms_item,0,entry.moc_const_id.id,ms_item.moc_id.id,0)
								self.pool.get('ch.primecost.view.spare.ms').write(cr,uid,ms_item.id,{'prime_cost':ms_prime_cost })
								prime_cost += ms_prime_cost 
						pump_prime_cost += prime_cost
					if item.line_ids_b:
						prime_cost = 0
						for bot_item in item.line_ids_b:
							if bot_item.is_applicable == True:
								if bot_item.flag_is_bearing == True:
									if not bot_item.brand_id:
										raise osv.except_osv(_('Warning!'),_('%s You cannot save without Brand'%(bot_item.ms_id.code)))
								bot_prime_cost = crm_obj._prime_cost_calculation(cr,uid,'bot',0,
								0,0,bot_item.ms_id.id,entry.moc_const_id.id,bot_item.moc_id.id,bot_item.brand_id.id)
								self.pool.get('ch.primecost.view.spare.bot').write(cr,uid,bot_item.id,{'prime_cost':bot_prime_cost * bot_item.qty})
								prime_cost += bot_prime_cost * bot_item.qty
						pump_prime_cost += prime_cost
					spare_bom_prime_cost = pump_prime_cost
					self.pool.get('ch.primecost.view.spare.bom').write(cr,uid,item.id,{'prime_cost':spare_bom_prime_cost})
							
			## Spare BOM primecost end
			
			## Accessories primecost starts
			if entry.line_ids_c:
				crm_obj.access_creation(cr,uid,0,entry,'primecost_view')
			
			#~ if entry.line_ids_c:
				#~ for access in entry.line_ids_c:
					#~ prime_cost = 0
					#~ access_rec = self.pool.get('kg.accessories.master').browse(cr,uid,access.access_id.id)
					#~ if access_rec.line_ids_b:
						#~ for acc_fou_item in access_rec.line_ids_b:
							#~ acc_fou_prime_cost = crm_obj._prime_cost_calculation(cr,uid,'foundry',acc_fou_item.pattern_id.id,
							#~ 0,0,0,0,access.moc_id.id,0)
							#~ prime_cost += acc_fou_prime_cost * acc_fou_item.qty
					#~ if access_rec.line_ids_a:
						#~ for acc_ms_item in access_rec.line_ids_a:
							#~ acc_ms_prime_cost = crm_obj._prime_cost_calculation(cr,uid,'ms',0,
							#~ acc_ms_item.ms_id.id,1,0,0,access.moc_id.id,0)
							#~ prime_cost += acc_ms_prime_cost
					#~ if access_rec.line_ids:
						#~ for acc_bot_item in access_rec.line_ids:
							#~ acc_bot_prime_cost = crm_obj._prime_cost_calculation(cr,uid,'bot',0,
							#~ 0,0,acc_bot_item.ms_id.id,0,access.moc_id.id,0)
							#~ prime_cost += acc_bot_prime_cost * acc_bot_item.qty
			## Accessories primecost ends
			
			self.write(cr, uid, ids, {'confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
	def entry_update(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			total_cost = pump_cost = fou_cost = ms_cost = bot_cost = 0
			
			item = entry
			catg='non_acc'
			bom = 'prime'
			purpose_categ = 'pump'
			offer_id = 0
						
			primecost_vals = self.pool.get('kg.crm.enquiry')._prepare_primecost(cr,uid,item,catg,bom,purpose_categ,offer_id)
						
			self.write(cr, uid, ids, {'confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		
		return True
	
	def _prepare_primecost(self,cr,uid,item,categ,entry,context=None):
		
		bom_line_id = bom_ms_line_id = bom_bot_line_id = moc_id = 0
		design_rate = moc_rate = brandmoc_rate = h_brandmoc_rate = pat_amt = prime_cost = prime_cost_1 = qty = price = ms_price = tot_price =  0.00
		tot_price = bot_price = price_1 = price_2 =  0.00
		
		if categ == 'fou':
			bom_line_id = item
		if categ == 'ms':
			bom_ms_line_id = item
		if categ == 'bot':
			bom_bot_line_id = item		
				
		# FOU Item
		if bom_line_id > 0:
			for fou_line in bom_line_id:
				if fou_line.is_applicable == True:
					moc_id = 0
					pattern_rec = self.pool.get('kg.pattern.master').browse(cr,uid,fou_line.pattern_id.id)
					if not fou_line.moc_id:
						pattern_line_id = pattern_rec.line_ids
						if pattern_line_id:
							item_moc_const_id = entry.moc_const_id.id
							pat_line_obj = self.pool.get('ch.mocwise.rate').search(cr,uid,[('code','=',item_moc_const_id),('header_id','=',pattern_rec.id)])
							if pat_line_obj:
								pat_line_rec = self.pool.get('ch.mocwise.rate').browse(cr,uid,pat_line_obj[0])
								moc_id = pat_line_rec.moc_id.id
					else:
						moc_id = fou_line.moc_id.id
					if moc_id > 0:
						moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
						if moc_rec.weight_type == 'ci':
							qty = fou_line.qty * pattern_rec.ci_weight
						elif moc_rec.weight_type == 'ss':
							qty = fou_line.qty * pattern_rec.pcs_weight
						elif moc_rec.weight_type == 'non_ferrous':
							qty = fou_line.qty * pattern_rec.nonferous_weight
						else:
							qty = 0
						moc_line_id = moc_rec.line_ids
						design_rate = moc_rec.rate
						
						self.pool.get('ch.primecost.view.fou').write(cr,uid,fou_line.id,{'prime_cost': design_rate * qty})
						pat_amt += design_rate * qty
						
			prime_cost_1 = pat_amt 
			
			prime_cost += prime_cost_1
			
		
		# MS Item 
		elif bom_ms_line_id > 0:
			ms_price = 0.00
			for ms_line in bom_ms_line_id:
				if ms_line.is_applicable == True:
					moc_id = 0
					tot_price = 0.00
					ms_rec = self.pool.get('kg.machine.shop').browse(cr,uid,ms_line.ms_id.id)
					if not ms_line.moc_id:
						item_moc_const_id = entry.moc_const_id.code
						ms_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',item_moc_const_id),('header_id','=',ms_rec.id)])
						if ms_line_obj:
							ms_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,ms_line_obj[0])
							moc_id = ms_line_rec.moc_id.id
					else:
						moc_id = ms_line.moc_id.id
					if moc_id >0:	
						if ms_rec.line_ids:
							for raw_line in ms_rec.line_ids:
								brandmoc_obj = self.pool.get('kg.brandmoc.rate').search(cr,uid,[('product_id','=',raw_line.product_id.id),('state','=','approved')])
								if brandmoc_obj:
									brandmoc_rec = self.pool.get('kg.brandmoc.rate').browse(cr,uid,brandmoc_obj[0])
									brandmoc_line_sql = """ select rate from ch_brandmoc_rate_details where moc_id =  %s and header_id = %s order by rate desc limit 1"""%(moc_id,brandmoc_rec.id)
									cr.execute(brandmoc_line_sql)		
									brandmoc_line_data = cr.dictfetchall()
									if brandmoc_line_data:
										design_rate = brandmoc_line_data[0]['rate']
										if raw_line.product_id.uom_conversation_factor == 'one_dimension':
											if entry.pump_model_type == 'vertical':
												if ms_rec.dynamic_length == True:
													if raw_line.uom.id == brandmoc_rec.uom_id.id:
														qty = ms_line.length * raw_line.temp_qty
													elif raw_line.uom.id != brandmoc_rec.uom_id.id:
														qty = ms_line.length * raw_line.temp_qty * raw_line.product_id.po_uom_in_kgs
												else:
													if raw_line.uom.id == brandmoc_rec.uom_id.id:
														qty = raw_line.qty
													elif raw_line.uom.id != brandmoc_rec.uom_id.id:
														qty = raw_line.weight
													
											elif entry.pump_model_type == 'horizontal':
												if raw_line.uom.id == brandmoc_rec.uom_id.id:
													qty = raw_line.qty
												elif raw_line.uom.id != brandmoc_rec.uom_id.id:
													qty = raw_line.weight
										elif raw_line.product_id.uom_conversation_factor == 'two_dimension':
											qty = raw_line.weight
										
										price = design_rate * qty
									tot_price += price
									self.pool.get('ch.primecost.view.ms').write(cr,uid,ms_line.id,{'prime_cost': tot_price * ms_line.qty})
					ms_price += tot_price * ms_line.qty 				
		
		# BOT Item 
		elif bom_bot_line_id > 0:
			bot_price = 0.00
			for bot_line in bom_bot_line_id:
				if bot_line.is_applicable == True:
					moc_id = 0
					tot_price = 0.00
					ms_obj = self.pool.get('kg.machine.shop').search(cr,uid,[('id','=',bot_line.bot_id.id)])
					if ms_obj:
						ms_rec = self.pool.get('kg.machine.shop').browse(cr,uid,ms_obj[0])
						if not bot_line.bot_id:
							item_moc_const_id = entry.moc_const_id.code
							ms_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',item_moc_const_id),('header_id','=',ms_rec.id)])
							if ms_line_obj:
								ms_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,ms_line_obj[0])
								moc_id = ms_line_rec.moc_id.id
						else:
							moc_id = bot_line.moc_id.id
						if moc_id > 0:
							if ms_rec.line_ids:
								for raw_line in ms_rec.line_ids:
									brandmoc_obj = self.pool.get('kg.brandmoc.rate').search(cr,uid,[('product_id','=',raw_line.product_id.id),('state','=','approved')])
									if brandmoc_obj:
										brandmoc_rec = self.pool.get('kg.brandmoc.rate').browse(cr,uid,brandmoc_obj[0])
										if bot_line.brand_id.id:
											brandmoc_line_sql = """ select rate from ch_brandmoc_rate_details where moc_id =  %s and header_id = %s and brand_id = %s order by rate desc limit 1"""%(moc_id,brandmoc_rec.id,bot_line.brand_id.id)
											cr.execute(brandmoc_line_sql)		
											brandmoc_line_data = cr.dictfetchall()
										else:
											brandmoc_line_sql = """ select rate from ch_brandmoc_rate_details where moc_id =  %s and header_id = %s order by rate desc limit 1"""%(moc_id,brandmoc_rec.id)
											cr.execute(brandmoc_line_sql)		
											brandmoc_line_data = cr.dictfetchall()
										if brandmoc_line_data:
											design_rate = brandmoc_line_data[0]['rate']
											if raw_line.product_id.uom_conversation_factor == 'one_dimension':
												if raw_line.uom.id == brandmoc_rec.uom_id.id:
													qty = raw_line.qty
												elif raw_line.uom.id != brandmoc_rec.uom_id.id:
													qty = raw_line.weight
											elif raw_line.product_id.uom_conversation_factor == 'two_dimension':
												qty = raw_line.weight
											
											
											price = design_rate * qty
										else:
											qty = design_rate = price = 0
											
										tot_price += price
										self.pool.get('ch.primecost.view.bot').write(cr,uid,bot_line.id,{'prime_cost': tot_price * bot_line.qty})
						bot_price += tot_price * bot_line.qty						
				
		
		d= prime_cost + ms_price + bot_price		
		primecost_tot = (prime_cost + ms_price + bot_price) 
		primecost_vals = primecost_tot	
		return primecost_vals
	
	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])		
		### Sequence Number Generation  ###
		if rec.name == '' or rec.name == False:
			seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.primecost.view')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_obj_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_obj_id[0],seq_rec.code,rec.entry_date))
			entry_name = cr.fetchone();
			entry_name = entry_name[0]
		else:
			entry_name = rec.name		
		self.write(cr, uid, ids, {'name':entry_name,'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
	def entry_approve(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
	def entry_cancel(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_primecost_view, self).write(cr, uid, ids, vals, context)
	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)	
	
	_sql_constraints = [
		
		('name', 'unique(name)', 'No must be Unique !!'),
	]
	
kg_primecost_view()

class ch_primecost_view_fou(osv.osv):
	
	_name = "ch.primecost.view.fou"
	_description = "Child Foundry Item Details"
	
	_columns = {
		
		### Basic Info
		
		'header_id':fields.many2one('kg.primecost.view', 'Pump Material', ondelete='cascade'),
		'remarks': fields.char('Remarks'),
		'active': fields.boolean('Active'),	
		
		### Module Requirement
		
		'qty':fields.integer('Quantity'),
		'position_id': fields.many2one('kg.position.number','Position No'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No'),
		'pattern_name': fields.related('pattern_id','pattern_name', type='char', string='Pattern Name', store=True),
		'is_applicable': fields.boolean('Is Applicable'),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		'prime_cost': fields.float('Prime Cost'),
		'material_code': fields.char('Material Code'),
		'purpose_categ': fields.selection([('pump','Pump'),('spare','Spare')],'Purpose'),
		
		## Child Tables Declaration 
		
		'load_bom': fields.boolean('Load BOM'),
		
	}
	
	_defaults = {
		
		'is_applicable': False,
		'load_bom': False,
		'active': True,
		
	}
	
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_primecost_view_fou, self).write(cr, uid, ids, vals, context)
	
	def onchange_pattern_name(self, cr, uid, ids, pattern_code,pattern_name):
		value = {'pattern_name':''}
		pattern_obj = self.pool.get('kg.pattern.master').search(cr,uid,([('id','=',pattern_code)]))
		if pattern_obj:
			pattern_rec = self.pool.get('kg.pattern.master').browse(cr,uid,pattern_obj[0])
			value = {'pattern_name':pattern_rec.pattern_name}
		return {'value': value}
	
ch_primecost_view_fou()

class ch_primecost_view_ms(osv.osv):
	
	_name = "ch.primecost.view.ms"
	_description = "Child MS Item Details"
	
	_columns = {
		
		### Basic Info
		
		'header_id':fields.many2one('kg.primecost.view', 'Pump Material', ondelete='cascade'),
		'remarks': fields.char('Remarks'),
		'active': fields.boolean('Active'),	
		
		### Module Requirement
		
		'qty': fields.integer('Qty', required=True),
		'position_id': fields.many2one('kg.position.number','Position No'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','ms')], ondelete='cascade',required=True),
		'ms_name': fields.related('ms_id','name', type='char',size=128,string='Item Name', store=True),
		'is_applicable': fields.boolean('Is Applicable'),
		'length': fields.float('Length'),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		'prime_cost': fields.float('Prime Cost'),
		'material_code': fields.char('Material Code'),
		'purpose_categ': fields.selection([('pump','Pump'),('spare','Spare')],'Purpose'),
		
		## Child Tables Declaration 
		
		'line_ids': fields.one2many('ch.pc.view.ms', 'header_id', "Fou Details"),
		'load_bom': fields.boolean('Load BOM'),
		
	}
	
	_defaults = {
		
		'is_applicable': False,
		'load_bom': False,
		'active': True,
		
	}
	
	 
ch_primecost_view_ms()

class ch_pc_view_ms(osv.osv):
	
	_name = "ch.pc.view.ms"
	_description = "Child PC MS Item Details"
	
	_columns = {
		
		### Basic Info
		
		'header_id':fields.many2one('ch.primecost.view.ms', 'MS', ondelete='cascade'),
		'remarks': fields.char('Remarks'),
		'active': fields.boolean('Active'),	
		
		### Module Requirement
		
		'product_id': fields.many2one('product.product','Raw Material', required=True, domain="[('product_type','in',['ms','bot','consu','coupling'])]"),			
		'uom':fields.many2one('product.uom','UOM',size=128 ,required=True),
		'od': fields.float('OD'),
		'length': fields.float('Length'),
		'breadth': fields.float('Breadth'),
		'thickness': fields.float('Thickness'),
		'weight': fields.float('Weight' ,digits=(16,5)),
		'uom_conversation_factor': fields.selection([('one_dimension','One Dimension'),('two_dimension','Two Dimension')],'UOM Conversation Factor'),		
		'temp_qty':fields.float('Qty'),
		'qty':fields.float('Testing Qty',readonly=True),
		
	}
	
	_defaults = {
		
		'active': True,
		
	}
	
	def onchange_length(self, cr, uid, ids, length,breadth,qty,temp_qty,uom_conversation_factor,product_id, context=None):		
		value = {'qty':0,'weight':0}
		qty = 0
		weight = 0
		prod_rec = self.pool.get('product.product').browse(cr,uid,product_id)
		if uom_conversation_factor:
			if uom_conversation_factor == 'one_dimension':
				qty = length * temp_qty
				if length == 0.00:
					qty = temp_qty
				weight = qty * prod_rec.po_uom_in_kgs
			if uom_conversation_factor == 'two_dimension':
				qty = length * breadth * temp_qty				
				weight = qty * prod_rec.po_uom_in_kgs
		value = {'qty': qty,'weight': weight}			
		return {'value': value}
	
	def onchange_weight(self, cr, uid, ids, uom_conversation_factor,length,breadth,temp_qty,product_id, context=None):		
		value = {'qty': '','weight': '',}
		prod_rec = self.pool.get('product.product').browse(cr,uid,product_id)
		qty_value = 0.00
		weight=0.00
		if uom_conversation_factor == 'one_dimension':	
			if prod_rec.uom_id.id == prod_rec.uom_po_id.id:
				qty_value = length * temp_qty
				weight = 0.00
			if length == 0.00:
				qty_value = temp_qty
			else:				
				qty_value = length * temp_qty			
				weight = qty_value * prod_rec.po_uom_in_kgs
		if uom_conversation_factor == 'two_dimension':
			qty_value = length * breadth * temp_qty				
			weight = qty_value * prod_rec.po_uom_in_kgs		
		value = {'qty': qty_value,'weight':weight}			
		return {'value': value}
	
ch_pc_view_ms()

class ch_primecost_view_bot(osv.osv):
	
	_name = "ch.primecost.view.bot"
	_description = "Child BOT Item Details"
	
	_columns = {
		
		### Basic Info
		
		'header_id':fields.many2one('kg.primecost.view', 'Pump Material', ondelete='cascade'),
		'remarks': fields.char('Remarks'),
		'active': fields.boolean('Active'),	
		
		### Module Requirement
		
		'position_id': fields.many2one('kg.position.number','Position No'),
		'bot_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','bot')], ondelete='cascade',required=True),
		'bot_name': fields.related('bot_id','name', type='char', size=128, string='Item Name', store=True, readonly=True),
		'qty': fields.integer('Qty', required=True),
		'is_applicable': fields.boolean('Is Applicable'),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		'prime_cost': fields.float('Prime Cost'),
		'brand_id': fields.many2one('kg.brand.master','Brand '),
		'flag_is_bearing': fields.boolean('Is Bearing'),
		'material_code': fields.char('Material Code'),
		'purpose_categ': fields.selection([('pump','Pump'),('spare','Spare')],'Purpose'),
		
		## Child Tables Declaration 
		
		'load_bom': fields.boolean('Load BOM'),
		
	}
	
	_defaults = {
		
		'is_applicable': False,
		'load_bom': False,
		'flag_is_bearing': False,
		'active': True,
		
	}	
	
ch_primecost_view_bot()

class ch_primecost_view_spare_bom(osv.osv):
	
	_name = "ch.primecost.view.spare.bom"
	_description = "Child Spare Foundry Item Details"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('kg.primecost.view', 'Primecost Id', ondelete='cascade'),
		'remarks': fields.char('Remarks'),
		
		## Module Requirement Fields
		
		'pump_id':fields.many2one('kg.pumpmodel.master','Pumpmodel'),
		'moc_const_id':fields.many2one('kg.moc.construction','MOC Construction'),
		'bom_id':fields.many2one('kg.bom','BOM Name',domain="[('pump_model_id','=',parent.pump_id),('category_type','=','part_list_bom')]"),
		'qty':fields.integer('Qty'),
		'off_name':fields.char('Offer Name'),
		'load_bom':fields.boolean('Load BOM'),
		'prime_cost': fields.float('Prime Cost'),
		
		## Child Tables Declaration
		
		'line_ids': fields.one2many('ch.primecost.view.spare.fou', 'header_id', "FOU"),
		'line_ids_a': fields.one2many('ch.primecost.view.spare.ms', 'header_id', "MS"),
		'line_ids_b': fields.one2many('ch.primecost.view.spare.bot', 'header_id', "BOT"),
		
		}	
	
	def default_get(self, cr, uid, fields, context=None):		
		return context
	
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_primecost_view_spare_bom, self).write(cr, uid, ids, vals, context)	
	
	def _duplicate_removed(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.load_bom != True:
			cr.execute(''' delete from ch_primecost_view_spare_fou where header_id = %s '''%(rec.id))
			cr.execute(''' delete from ch_primecost_view_spare_ms where header_id = %s '''%(rec.id))
			cr.execute(''' delete from ch_primecost_view_spare_bot where header_id = %s '''%(rec.id))
			if rec.line_ids_a:
				for item in rec.line_ids_a:
					cr.execute(''' delete from ch_pc_view_spare_ms where header_id = %s '''%(item.id))
		return True
	
	_constraints = [
			
		(_duplicate_removed,'Duplicates removed !',['']),
		
		]
	
	def onchange_spare_off_name(self, cr, uid, ids, bom_id):
		value = {'off_name':'','qty':0}
		if bom_id:
			bom_obj = self.pool.get('kg.bom').search(cr,uid,([('id','=',bom_id)]))
			if bom_obj:
				bom_rec = self.pool.get('kg.bom').browse(cr,uid,bom_obj[0])
				value = {'off_name':bom_rec.name,'qty':bom_rec.qty}
		return {'value': value}
	
	def onchange_spare_bom(self, cr, uid, ids, bom_id,off_name,moc_const_id,qty):
		fou_vals=[]
		ms_vals=[]
		bot_vals=[]
		if bom_id:
			bom_obj = self.pool.get('kg.bom').search(cr,uid,([('id','=',bom_id),('name','=',off_name),('category_type','=','part_list_bom')]))
			if bom_obj:
				bom_rec = self.pool.get('kg.bom').browse(cr,uid,bom_obj[0])
				moc_name = ''
				moc_changed_flag = False
				if bom_rec.line_ids:
					for item in bom_rec.line_ids:
						moc_id = ''
						pat_obj = self.pool.get('kg.pattern.master').search(cr,uid,[('id','=',item.pattern_id.id)])
						if pat_obj:
							pat_rec = self.pool.get('kg.pattern.master').browse(cr,uid,pat_obj[0])
							if pat_rec.line_ids:
								pat_line_obj = self.pool.get('ch.mocwise.rate').search(cr,uid,[('code','=',moc_const_id),('header_id','=',pat_rec.id)])
								if pat_line_obj:
									pat_line_rec = self.pool.get('ch.mocwise.rate').browse(cr,uid,pat_line_obj[0])
									moc_id = pat_line_rec.moc_id.id
						if moc_id:
							moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
							moc_changed_flag = True
							moc_name = moc_rec.name
						fou_vals.append({
									'position_id': item.position_id.id,
									'pattern_id': item.pattern_id.id,
									'pattern_name': item.pattern_id.pattern_name,
									'off_name': item.pattern_id.pattern_name,
									'moc_id': moc_id,
									'moc_name': moc_name,
									'moc_changed_flag': moc_changed_flag,
									'qty': item.qty * qty,
									'load_bom': True,
									'is_applicable': True,
									
									})
				
				if bom_rec.line_ids_a:
					for item in bom_rec.line_ids_a:
						ch_ms_vals = []
						moc_id = ''
						ms_obj = self.pool.get('kg.machine.shop').search(cr,uid,[('id','=',item.ms_id.id)])
						print"ms_objms_obj",ms_obj
						if ms_obj:
							ms_rec = self.pool.get('kg.machine.shop').browse(cr,uid,ms_obj[0])
							if ms_rec.line_ids_a:
								#~ for ele in ms_rec.line_ids_a:
								cons_rec = self.pool.get('kg.moc.construction').browse(cr,uid,moc_const_id)
								ms_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',cons_rec.id),('header_id','=',ms_rec.id)])
								if ms_line_obj:
									ms_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,ms_line_obj[0])
									moc_id = ms_line_rec.moc_id.id
							if ms_rec.line_ids:
								for raw in ms_rec.line_ids:
									ch_ms_vals.append([0, 0,{
											'product_id': raw.product_id.id,
											'uom': raw.uom.id,
											'od': raw.od,
											'length': raw.length,
											'breadth': raw.breadth,
											'thickness': raw.thickness,
											'weight': raw.weight * item.qty * qty,
											'uom_conversation_factor': raw.uom_conversation_factor,
											'temp_qty': raw.temp_qty * item.qty * qty,
											'qty': raw.qty * item.qty * qty,
											'remarks': raw.remarks,
											}])
						if moc_id:
							moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
							moc_changed_flag = True
							moc_name = moc_rec.name
						ms_vals.append({
										'name': item.name,
										'off_name': item.name,
										'position_id': item.position_id.id,							
										'ms_id': item.ms_id.id,
										'moc_id': moc_id,
										'moc_name': moc_name,
										'moc_changed_flag': moc_changed_flag,
										'qty': item.qty * qty,
										'load_bom': True,
										'is_applicable': True,
										'line_ids': ch_ms_vals,
									
										})
				
				
				if bom_rec.line_ids_b:
					for item in bom_rec.line_ids_b:
						moc_id = ''
						item_name = item.name
						bot_obj = self.pool.get('kg.machine.shop').search(cr,uid,[('id','=',item.bot_id.id)])
						if bot_obj:
							bot_rec = self.pool.get('kg.machine.shop').browse(cr,uid,bot_obj[0])
							is_bearing = bot_rec.is_bearing
							if bot_rec.line_ids_a:
								cons_rec = self.pool.get('kg.moc.construction').browse(cr,uid,moc_const_id)
								bot_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',cons_rec.id),('header_id','=',bot_rec.id)])
								if bot_line_obj:
									bot_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,bot_line_obj[0])
									moc_id = bot_line_rec.moc_id.id
						if moc_id:
							moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
							moc_changed_flag = True
							moc_name = moc_rec.name
						bot_vals.append({
										'item_name': item_name,
										'off_name': item_name,
										'ms_id': item.bot_id.id,
										'moc_id': moc_id,
										'moc_name': moc_name,
										'moc_changed_flag': moc_changed_flag,
										'qty': item.qty * qty,
										'load_bom': True,
										'flag_is_bearing': is_bearing,
										'is_applicable': True,									
										'position_id': item.position_id.id,
										
										})
										
		return {'value': {'line_ids': fou_vals,'line_ids_a': ms_vals,'line_ids_b': bot_vals}}
	
ch_primecost_view_spare_bom()

class ch_primecost_view_spare_fou(osv.osv):
	
	_name = "ch.primecost.view.spare.fou"
	_description = "Child Spare Foundry Item Details"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('ch.primecost.view.spare.bom', 'Pump Id', ondelete='cascade'),
		'remarks': fields.char('Remarks'),
		
		## Module Requirement Fields
		
		'qty':fields.integer('Quantity'),
		'oth_spec':fields.char('Other Specification'),
		'position_id': fields.many2one('kg.position.number','Position No.'),
		'csd_no': fields.char('CSD No.', size=128),
		'pattern_name': fields.char('Pattern Name'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No.'),
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'moc_name': fields.char('MOC Name'),
		'moc_changed_flag': fields.boolean('MOC Changed'),
		'prime_cost': fields.float('Prime Cost'),
		'purpose_categ': fields.selection([('pump','Pump'),('spare','Spare'),('access','Accessories')],'Purpose Category'),
		'material_code': fields.char('Material Code'),
		'spare_offer_line_id': fields.integer('Spare Offer Line Id'),
		'off_name': fields.char('Offer Name'),
		
	}
	
	_defaults = {
		
		'is_applicable': False,
		'load_bom': False,
		
	}
	
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_primecost_view_spare_fou, self).write(cr, uid, ids, vals, context)
			
	
	def onchange_pattern_name(self, cr, uid, ids, pattern_code,pattern_name):
		value = {'pattern_name':''}
		pattern_obj = self.pool.get('kg.pattern.master').search(cr,uid,([('id','=',pattern_code)]))
		if pattern_obj:
			pattern_rec = self.pool.get('kg.pattern.master').browse(cr,uid,pattern_obj[0])
			value = {'pattern_name':pattern_rec.pattern_name}
		return {'value': value}
	
	def onchange_moc(self,cr,uid,ids,moc_id,moc_name, context=None):
		value = {'moc_changed_flag':''}
		if moc_id:
			moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
			if moc_rec.name == moc_name:
				pass
			else:
				value = {'moc_changed_flag': True}
		return {'value': value}
	
ch_primecost_view_spare_fou()

class ch_primecost_view_spare_ms(osv.osv):
	
	_name = "ch.primecost.view.spare.ms"
	_description = "Macine Shop Item Details"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('ch.primecost.view.spare.bom', 'Pump Id', ondelete='cascade'),
		'remarks':fields.text('Remarks'),
		
		## Module Requirement Fields
		
		'pos_no': fields.related('position_id','name', type='char', string='Position No.', store=True),
		'position_id': fields.many2one('kg.position.number','Position No.'),
		'csd_no': fields.char('CSD No.'),
		'bom_id': fields.many2one('kg.bom','BOM'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','ms')], ondelete='cascade',required=True),
		'name': fields.related('ms_id','name', type='char',size=128,string='Item Name', store=True),

		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),

		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'moc_name': fields.char('MOC Name'),
		'moc_changed_flag': fields.boolean('MOC Changed'),
		'prime_cost': fields.float('Prime Cost'),
		'purpose_categ': fields.selection([('pump','Pump'),('spare','Spare'),('access','Accessories')],'Purpose Category'),
		'length': fields.float('Length'),
		'material_code': fields.char('Material Code'),
		'spare_offer_line_id': fields.integer('Spare Offer Line Id'),
		'off_name': fields.char('Offer Name'),
		
		## Child Tables Declaration 
		
		'line_ids': fields.one2many('ch.pc.view.spare.ms', 'header_id', "Raw Details"),
		
	}
	
	_defaults = {
		
		'is_applicable': False,
		'load_bom': False,
		
	}
	
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_primecost_view_spare_ms, self).write(cr, uid, ids, vals, context)
	
	
	def onchange_moc(self,cr,uid,ids,moc_id,moc_name, context=None):
		value = {'moc_changed_flag':''}
		if moc_id:
			moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
			if moc_rec.name == moc_name:
				pass
			else:
				value = {'moc_changed_flag': True}
		return {'value': value}
	
		
ch_primecost_view_spare_ms()

class ch_pc_view_spare_ms(osv.osv):
	
	_name = "ch.pc.view.spare.ms"
	_description = "Child PC Spare MS Item Details"
	
	_columns = {
		
		### Basic Info
		
		'header_id':fields.many2one('ch.primecost.view.spare.ms','MS',ondelete='cascade'),
		'remarks': fields.char('Remarks'),
		'active': fields.boolean('Active'),	
		
		### Module Requirement
		
		'product_id': fields.many2one('product.product','Raw Material', required=True, domain="[('product_type','in',['ms','bot','consu','coupling'])]"),			
		'uom':fields.many2one('product.uom','UOM',size=128 ,required=True),
		'od': fields.float('OD'),
		'length': fields.float('Length'),
		'breadth': fields.float('Breadth'),
		'thickness': fields.float('Thickness'),
		'weight': fields.float('Weight' ,digits=(16,5)),
		'uom_conversation_factor': fields.selection([('one_dimension','One Dimension'),('two_dimension','Two Dimension')],'UOM Conversation Factor'),		
		'temp_qty':fields.float('Qty'),
		'qty':fields.float('Testing Qty',readonly=True),
		
	}
	
	_defaults = {
		
		'active': True,
		
	}
	
	def onchange_length(self, cr, uid, ids, length,breadth,qty,temp_qty,uom_conversation_factor,product_id, context=None):		
		value = {'qty':0,'weight':0}
		qty = 0
		weight = 0
		prod_rec = self.pool.get('product.product').browse(cr,uid,product_id)
		if uom_conversation_factor:
			if uom_conversation_factor == 'one_dimension':
				qty = length * temp_qty
				if length == 0.00:
					qty = temp_qty
				weight = qty * prod_rec.po_uom_in_kgs
			if uom_conversation_factor == 'two_dimension':
				qty = length * breadth * temp_qty				
				weight = qty * prod_rec.po_uom_in_kgs
		value = {'qty': qty,'weight': weight}			
		return {'value': value}
	
	def onchange_weight(self, cr, uid, ids, uom_conversation_factor,length,breadth,temp_qty,product_id, context=None):		
		value = {'qty': '','weight': '',}
		prod_rec = self.pool.get('product.product').browse(cr,uid,product_id)
		qty_value = 0.00
		weight=0.00
		if uom_conversation_factor == 'one_dimension':	
			if prod_rec.uom_id.id == prod_rec.uom_po_id.id:
				qty_value = length * temp_qty
				weight = 0.00
			if length == 0.00:
				qty_value = temp_qty
			else:				
				qty_value = length * temp_qty			
				weight = qty_value * prod_rec.po_uom_in_kgs
		if uom_conversation_factor == 'two_dimension':
			qty_value = length * breadth * temp_qty				
			weight = qty_value * prod_rec.po_uom_in_kgs		
		value = {'qty': qty_value,'weight':weight}			
		return {'value': value}
	
	
ch_pc_view_spare_ms()

class ch_primecost_view_spare_bot(osv.osv):
	
	_name = "ch.primecost.view.spare.bot"
	_description = "BOT Details"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('ch.primecost.view.spare.bom', 'Pump Id', ondelete='cascade'),
		'remarks':fields.text('Remarks'),
		
		## Module Requirement Fields
		
		'product_temp_id':fields.many2one('product.product', 'Product Name',domain = [('type','=','bot')], ondelete='cascade'),
	
		'position_id': fields.many2one('kg.position.number','Position No.'),
		'bom_id': fields.many2one('kg.bom','BOM'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','bot')], ondelete='cascade',required=True),
		'item_name': fields.related('ms_id','name', type='char', size=128, string='Item Name', store=True, readonly=True),
		'code':fields.char('Item Code', size=128),	  
		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
	
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'moc_name': fields.char('MOC Name'),
		'moc_changed_flag': fields.boolean('MOC Changed'),
		'prime_cost': fields.float('Prime Cost'),
		'brand_id': fields.many2one('kg.brand.master','Brand '),
		'flag_is_bearing': fields.boolean('Is Bearing'),
		'purpose_categ': fields.selection([('pump','Pump'),('spare','Spare'),('access','Accessories')],'Purpose Category'),
		'material_code': fields.char('Material Code'),
		'spare_offer_line_id': fields.integer('Spare Offer Line Id'),
		'off_name': fields.char('Offer Name'),
		
	}
	
	_defaults = {
		
		'is_applicable': False,
		'load_bom': False,
		'flag_is_bearing': False,
		
	}
	
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_primecost_view_spare_bot, self).write(cr, uid, ids, vals, context)
	
	
	def onchange_moc(self,cr,uid,ids,moc_id,moc_name, context=None):
		value = {'moc_changed_flag':''}
		if moc_id:
			moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
			if moc_rec.name == moc_name:
				pass
			else:
				value = {'moc_changed_flag': True}
		return {'value': value}
	
	
ch_primecost_view_spare_bot()

class ch_primecost_view_access(osv.osv):
	
	_name = "ch.primecost.view.access"
	_description = "Ch Primecost View Accessories"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('kg.primecost.view','Primecost',ondelete='cascade'),
		
		## Module Requirement Fields
		
		'access_categ_id': fields.many2one('kg.accessories.category','Accessories Categ',domain="[('state','not in',('reject','cancel'))]"),
		'access_id': fields.many2one('kg.accessories.master','Accessories',domain="[('state','not in',('reject','cancel')),('access_cate_id','=',access_categ_id)]"),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('state','not in',('reject','cancel'))]"),
		'qty': fields.float('Qty'),
		'oth_spec': fields.char('Other Specification'),
		'load_access': fields.boolean('Load BOM'),
		'prime_cost': fields.float('Prime Cost'),
		'is_selectable_all': fields.boolean('Select All'),
		'off_name': fields.char('Offer Name'),
		'accessories_type': fields.selection([('base_plate','Base Plate'),('coupling','Coupling'),('coupling_guard','Coupling Guard'),
		('foundation_bolt','Foundation Bolt'),('pump_pulley','Pump Pulley'),('motor_pulley','Motor Pulley'),
		('slide_rail','Slide Rail'),('belt','Belt'),('belt_guard','Belt Guard'),('others','Others')],'Accessories type'),
		'moc_const_id':fields.many2one('kg.moc.construction', 'MOC Construction'),
		'flag_standard': fields.boolean('Non Standarad'),
		
		## Child Tables Declaration
		
		'line_ids': fields.one2many('ch.primecost.access.fou', 'header_id', 'Access FOU'),
		'line_ids_a': fields.one2many('ch.primecost.access.ms', 'header_id', 'Access MS'),
		'line_ids_b': fields.one2many('ch.primecost.access.bot', 'header_id', 'Access BOT'),
		
	}
	
	_defaults = {
		
		'is_selectable_all':True,
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		## if len(context)>7:
		if not context['moc_const_id']:
			raise osv.except_osv(_('Warning!'),_('Kindly Configure MOC Construction !!'))
		return context
	
	def onchange_access_id(self, cr, uid, ids, access_categ_id,access_id):
		value = {'access_id':access_id,'off_name':''}
		if access_categ_id:
			acc_rec = self.pool.get('kg.accessories.category').browse(cr,uid,access_categ_id)
			value = {'access_id':'','off_name':acc_rec.name}
		else:
			raise osv.except_osv(_('Warning!'),_('System should allow without accessories category!'))
		return {'value': value}
	
	def onchange_load_access(self,cr,uid,ids,load_access,flag_standard,access_id,moc_const_id,qty,is_selectable_all):
		fou_vals=[]
		ms_vals=[]
		bot_vals=[]
		data_rec = ''
		moc_changed_flag = False
		if load_access == True and access_id:
			if qty == 0:
				raise osv.except_osv(_('Warning!'),_('Kindly Configure Qty'))
			access_obj = self.pool.get('kg.accessories.master').search(cr, uid, [('id','=',access_id)])
			if access_obj:
				data_rec = self.pool.get('kg.accessories.master').browse(cr, uid, access_obj[0])
		moc_id = ''
		moc_name = ''
		if data_rec:
			if data_rec.line_ids_b:
				for item in data_rec.line_ids_b:
					moc_id = ''
					pat_obj = self.pool.get('kg.pattern.master').search(cr,uid,[('id','=',item.pattern_id.id)])
					if pat_obj:
						pat_rec = self.pool.get('kg.pattern.master').browse(cr,uid,pat_obj[0])
						if pat_rec.line_ids:
							pat_line_obj = self.pool.get('ch.mocwise.rate').search(cr,uid,[('code','=',moc_const_id),('header_id','=',pat_rec.id)])
							if pat_line_obj:
								pat_line_rec = self.pool.get('ch.mocwise.rate').browse(cr,uid,pat_line_obj[0])
								moc_id = pat_line_rec.moc_id.id
					if moc_id:
						moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
						moc_changed_flag = True
						moc_name = moc_rec.name
					if is_selectable_all == True:
						is_selectable_all = True
					else:
						is_selectable_all = False
					fou_vals.append({
									'position_id': item.position_id.id,
									'pattern_id': item.pattern_id.id,
									'pattern_name': item.pattern_name,
									'moc_id': moc_id,
									'moc_name': moc_name,
									'moc_changed_flag': moc_changed_flag,
									'qty': item.qty * qty,
									'load_bom': True,
									'is_applicable': is_selectable_all,
									'csd_no': item.csd_no,
									'remarks': item.remarks,
									'flag_standard': flag_standard,
									})
			if data_rec.line_ids_a:
				for item in data_rec.line_ids_a:
					moc_id = ''
					ms_obj = self.pool.get('kg.machine.shop').search(cr,uid,[('id','=',item.ms_id.id)])
					if ms_obj:
						ms_rec = self.pool.get('kg.machine.shop').browse(cr,uid,ms_obj[0])
						if ms_rec.line_ids_a:
							cons_rec = self.pool.get('kg.moc.construction').browse(cr,uid,moc_const_id)
							ms_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',cons_rec.id),('header_id','=',ms_rec.id)])
							if ms_line_obj:
								ms_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,ms_line_obj[0])
								moc_id = ms_line_rec.moc_id.id
					if moc_id:
						moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
						moc_changed_flag = True
						moc_name = moc_rec.name
					if is_selectable_all == True:
						is_selectable_all = True
					else:
						is_selectable_all = False
					ms_vals.append({
									'name': item.name,
									'position_id': item.position_id.id,							
									'ms_id': item.ms_id.id,
									'moc_id': moc_id,
									'moc_name': moc_name,
									'moc_changed_flag': moc_changed_flag,
									'qty': item.qty * qty,
									'load_bom': True,
									'is_applicable': is_selectable_all,
									'csd_no': item.csd_no,
									'remarks': item.remarks,
									'flag_standard': flag_standard,
									})
			if data_rec.line_ids:
				for item in data_rec.line_ids:
					moc_id = ''
					bot_obj = self.pool.get('kg.machine.shop').search(cr,uid,[('id','=',item.ms_id.id)])
					if bot_obj:
						bot_rec = self.pool.get('kg.machine.shop').browse(cr,uid,bot_obj[0])
						is_bearing = bot_rec.is_bearing
						if bot_rec.line_ids_a:
							cons_rec = self.pool.get('kg.moc.construction').browse(cr,uid,moc_const_id)
							bot_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',cons_rec.id),('header_id','=',bot_rec.id)])
							if bot_line_obj:
								bot_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,bot_line_obj[0])
								moc_id = bot_line_rec.moc_id.id
					if moc_id:
						moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
						moc_changed_flag = True
						moc_name = moc_rec.name
					if is_selectable_all == True:
						is_selectable_all = True
					else:
						is_selectable_all = False
					bot_vals.append({
									
									'name': item.item_name,
									'position_id': item.position_id.id,							
									'ms_id': item.ms_id.id,
									'moc_id': moc_id,
									'moc_name': moc_name,
									'moc_changed_flag': moc_changed_flag,
									'qty': item.qty * qty,
									'load_bom': True,
									'is_applicable': is_selectable_all,
									'csd_no': item.csd_no,
									'remarks': item.remark,
									'flag_standard': flag_standard,
									})
		return {'value': {'line_ids': fou_vals,'line_ids_a': ms_vals,'line_ids_b': bot_vals}}
	
ch_primecost_view_access()

class ch_primecost_access_fou(osv.osv):
	
	_name = "ch.primecost.access.fou"
	_description = "Ch Primecost Access Fou"
	
	_columns = {
		
		## Basic Info
		
		'header_id': fields.many2one('ch.primecost.view.access', 'Access Id', ondelete='cascade'),
		'remarks': fields.char('Remarks'),
		
		## Module Requirement Fields
		
		'pump_id': fields.many2one('kg.pumpmodel.master', 'Pump'),
		'qty': fields.integer('Quantity'),
		'oth_spec': fields.char('Other Specification'),
		'position_id': fields.many2one('kg.position.number','Position No.'),
		'csd_no': fields.char('CSD No.', size=128,readonly=True),
		'pattern_name': fields.char('Pattern Name'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No.'),
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'moc_name': fields.char('MOC Name'),
		'moc_changed_flag': fields.boolean('MOC Changed'),
		'prime_cost': fields.float('Prime Cost'),
		'material_code': fields.char('Material Code'),
		'flag_standard': fields.boolean('Non Standarad'),
		
	}
	
	def onchange_moc(self,cr,uid,ids,moc_id,moc_name, context=None):
		value = {'moc_changed_flag':''}
		if moc_id:
			moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
			if moc_rec.name == moc_name:
				pass
			else:
				value = {'moc_changed_flag': True}
		return {'value': value}
	
ch_primecost_access_fou()

class ch_primecost_access_ms(osv.osv):
	
	_name = "ch.primecost.access.ms"
	_description = "Ch Primecost Access MS"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('ch.primecost.view.access', 'Access Id', ondelete='cascade'),
		'remarks': fields.text('Remarks'),
		
		## Module Requirement Fields
		
		'pos_no': fields.related('position_id','name', type='char', string='Position No.', store=True),
		'position_id': fields.many2one('kg.position.number','Position No.'),
		'csd_no': fields.char('CSD No.'),
		'bom_id': fields.many2one('kg.bom','BOM'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','ms')], ondelete='cascade',required=True),
		'name': fields.related('ms_id','name', type='char',size=128,string='Item Name', store=True),
		'name':fields.char('Item Name', size=128),	  
		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'moc_name': fields.char('MOC Name'),
		'moc_changed_flag': fields.boolean('MOC Changed'),
		'prime_cost': fields.float('Prime Cost'),
		'material_code': fields.char('Material Code'),
		'flag_standard': fields.boolean('Non Standarad'),
		
	}
	
	def onchange_moc(self,cr,uid,ids,moc_id,moc_name, context=None):
		value = {'moc_changed_flag':''}
		if moc_id:
			moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
			if moc_rec.name == moc_name:
				pass
			else:
				value = {'moc_changed_flag': True}
		return {'value': value}
	
	_defaults = {
		
		'is_applicable':False,
		'load_bom':False,
		
	}
	
ch_primecost_access_ms()

class ch_primecost_access_bot(osv.osv):
	
	_name = "ch.primecost.access.bot"
	_description = "Ch Primecost Access BOT"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('ch.primecost.view.access', 'Access Id', ondelete='cascade'),
		'remarks':fields.text('Remarks'),
		
		## Module Requirement Fields
		
		'position_id': fields.many2one('kg.position.number','Position No.'),
		'csd_no': fields.char('CSD No.'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','bot')], ondelete='cascade',required=True),
		'name': fields.related('ms_id','name', type='char',size=128,string='Item Name', store=True),
		'qty': fields.integer('Qty', required=True),
		'flag_applicable': fields.boolean('Is Applicable'),
		'is_applicable': fields.boolean('Is Applicable'),
		'load_bom': fields.boolean('Load BOM'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'moc_name': fields.char('MOC Name'),
		'moc_changed_flag': fields.boolean('MOC Changed'),
		'prime_cost': fields.float('Prime Cost'),
		'brand_id': fields.many2one('kg.brand.master','Brand'),
		'material_code': fields.char('Material Code'),
		'flag_standard': fields.boolean('Non Standarad'),
		
	}
	
	def onchange_moc(self,cr,uid,ids,moc_id,moc_name, context=None):
		value = {'moc_changed_flag':''}
		if moc_id:
			moc_rec = self.pool.get('kg.moc.master').browse(cr,uid,moc_id)
			if moc_rec.name == moc_name:
				pass
			else:
				value = {'moc_changed_flag': True}
		return {'value': value}
	
ch_primecost_access_bot()
