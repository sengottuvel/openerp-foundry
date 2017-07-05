from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

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
			
			for line in order.line_ids:
				if line.is_applicable == True:
					pump_cost += line.prime_cost
			for line in order.line_ids_a:
				if line.is_applicable == True:
					pump_cost += line.prime_cost
			for line in order.line_ids_b:
				if line.is_applicable == True:
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
		
		### Entry Info ####
		
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
		'load_bom': fields.boolean('Load BOM'),
		'pump_cost': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Pump Cost',multi="sums",store=True),	
		'total_cost': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Cost',multi="sums",store=True),	
		
		'pump_model_type':fields.selection([('vertical','Vertical'),('horizontal','Horizontal')], 'Pump Type'),
		'speed_in_rpm': fields.float('Speed in RPM - Pump'),
		'rpm': fields.selection([('1450','1450'),('2900','2900')],'RPM'),
		'motor_power': fields.selection([('90','90'),('100','100'),('112','112'),('132','132'),('160','160'),('180','180'),('200','200'),('225','225'),
				('250','250'),('280','280'),('315','315'),('315_l','315L')],'Motor Frame size'),
		'setting_height': fields.float('Setting Height (MM)'),
		'del_pipe_size': fields.selection([('32','32'),('40','40'),('50','50'),('65','65'),('80','80'),('100','100'),('125','125'),('150','150'),('200','200'),('250','250'),('300','300')],'Delivery Pipe Size(MM)'),
		'shaft_sealing': fields.selection([('g_p','Gland Packing'),('m_s','Mechanical Seal'),('f_s','Felt Seal'),('d_s','Dynamic Seal')],'Shaft Sealing'),
		'bush_bearing': fields.selection([('grease','Bronze'),('cft_self','CFT'),('cut_less_rubber','Cut less Rubber')],'Bush Bearing'),
		'bush_bearing_lubrication':fields.selection([('grease','Grease'),('external','External'),('self','Self'),('ex_pressure','External Under Pressure')], 'Bush Bearing Lubrication'),
		'motor_kw': fields.float('Motor KW'),
		'moc_construction_name': fields.char('MOC Construction Name',readonly=True),
		
		## Child Tables Declaration 
		
		'line_ids': fields.one2many('ch.primecost.view.fou', 'header_id', "Fou Details"),
		'line_ids_a': fields.one2many('ch.primecost.view.ms', 'header_id', "MS Details"),
		'line_ids_b': fields.one2many('ch.primecost.view.bot', 'header_id', "BOT Details"),
		
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
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		entry_date = rec.entry_date
		entry_date = str(entry_date)
		entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
		if entry_date > today:
			return False
		return True
	
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
					raise osv.except_osv(_('Warning!'),_('Pattern Name %s You cannot save without MOC'%(line.pattern_id.pattern_name)))
		if entry.line_ids_a:
			for line in entry.line_ids:
				if line.is_applicable == True and not line.moc_id:
					raise osv.except_osv(_('Warning!'),_('Item Name %s You cannot save without MOC'%(line.ms_id.name)))
		if entry.line_ids_b:
			for line in entry.line_ids:
				if line.is_applicable == True and not line.moc_id:
					raise osv.except_osv(_('Warning!'),_('Item Name %s You cannot save without MOC'%(line.bot_id.name)))
		return True
	
	def _duplicate_removed(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.load_bom != True:
			cr.execute(''' delete from ch_primecost_view_fou where header_id = %s '''%(rec.id))
			cr.execute(''' delete from ch_primecost_view_ms where header_id = %s '''%(rec.id))
			cr.execute(''' delete from ch_primecost_view_bot where header_id = %s '''%(rec.id))
		return True
	
	_constraints = [        
            
			(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
			(_check_is_applicable, 'Kindly select anyone is appli !!',['']),
			#~ (_check_lineitems, 'System not allow to save with empty Details !!',['']),
			(_duplicate_removed, 'Duplcates removed !',['']),
			
       ]
	
	def onchange_moc_const(self, cr, uid, ids, moc_const_id):
		value = {'moc_construction_name':''}
		if moc_const_id:
			moc_rec = self.pool.get('kg.moc.construction').browse(cr,uid,moc_const_id)
			value = {'moc_construction_name':moc_rec.name}
		return {'value': value}
	
	def onchange_bom(self, cr, uid, ids, load_bom,pump_id,moc_const_id,qty,speed_in_rpm,rpm,setting_height,shaft_sealing,
					motor_power,bush_bearing,del_pipe_size,bush_bearing_lubrication):
		delivery_pipe_size = del_pipe_size
		lubrication = bush_bearing_lubrication
		if qty <= 0:
			raise osv.except_osv(_('Warning!'),_('System sholud not be accept without Quantity'))
		if lubrication:
			if lubrication == 'external':
				lubrication = 'cft_ext'
			elif lubrication == 'self':
				lubrication = 'cft_self'
			elif lubrication == 'ex_pressure':
				lubrication = 'cut_less_rubber'
		
		pump_model_id = pump_id
		#~ rpm = speed_in_rpm
		rpm = rpm
		moc_construction_id = moc_const_id
		#~ if rpm:
			#~ if rpm <= 1450:
				#~ rpm = '1450'
			#~ elif rpm > 1450 and rpm <= 2900:
				#~ rpm = '2900'
		fou_vals=[]
		ms_vals=[]
		ch_ms_vals = []
		bot_vals=[]
		data_rec = ''
		if load_bom == True and pump_id:
				bom_obj = self.pool.get('kg.bom').search(cr, uid, [('pump_model_id','=',pump_id),('state','in',('draft','confirmed','approved'))])
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
							
					fou_vals.append({
									'position_id': item.position_id.id,
									'pattern_id': item.pattern_id.id,
									'pattern_name': item.pattern_name,
									'moc_id': moc_id,
									'qty': item.qty * qty,
									'load_bom': True,
									'active': True,
									'is_applicable': True,
									#~ 'remarks': item.remarks,
									})
			if data_rec.line_ids_a:
				for item in data_rec.line_ids_a:
					moc_id = ''
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
							ch_ms_vals = []
							for raw in ms_rec.line_ids:
								ch_ms_vals.append([0, 0,{
										'product_id': raw.product_id.id,
										'uom': raw.uom.id,
										'od': raw.od,
										'length': raw.length,
										'breadth': raw.breadth,
										'thickness': raw.thickness,
										'weight': raw.weight,
										'uom_conversation_factor': raw.uom_conversation_factor,
										'temp_qty': raw.temp_qty,
										'qty': raw.qty,
										'remarks': raw.remarks,
										}])
							ms_vals.append({
										'position_id': item.position_id.id,
										'ms_name': item.name,
										'ms_id': item.ms_id.id,
										'moc_id': moc_id,
										'qty': item.qty * qty,
										'load_bom': True,
										'is_applicable': True,
										'active': True,
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
						bot_vals.append({
										'position_id': item.position_id.id,
										'bot_name': item_name,
										'bot_id': item.bot_id.id,
										'moc_id': moc_id,
										'qty': item.qty * qty,
										'load_bom': True,
										'is_applicable': True,
										'active': True,
										'flag_is_bearing': bot_rec.is_bearing,
										#~ 'remarks': item.remarks,
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
						where limitation = %s and header_id = (select id from kg_bom where pump_model_id = %s and active='t'))
						and active='t'
						)
						
						  ''',[limitation,shaft_sealing,rpm,pump_model_id,motor_power,rpm,pump_model_id,
						  bush_bearing,setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,delivery_pipe_size,
						  setting_height,setting_height,rpm,pump_model_id,rpm,pump_model_id,lubrication,setting_height,setting_height,
						  rpm,pump_model_id,rpm,pump_model_id,base_limitation,pump_model_id])
					vertical_foundry_details = cr.dictfetchall()
					
					#~ if order_category == 'pump' :
					for vertical_foundry in vertical_foundry_details:
						
						#~ if order_category == 'pump' :
							#~ applicable = True
						#~ if order_category in ('spare','pump_spare'):
							#~ applicable = False
							
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
						
						fou_vals.append({
							
							'pattern_id': vertical_foundry['pattern_id'],
							'pattern_name': vertical_foundry['pattern_name'],						
							'position_id': vertical_foundry['position_id'],			  
							'qty' : bom_qty * qty,
							'moc_id': moc_id,
							'is_applicable': True,
							'active': True,
							'load_bom': True,
							#~ 'bom_id': vertical_foundry['header_id'],
							#~ 'bom_line_id': vertical_foundry['id'],	
							#~ 'weight': wgt or 0.00,								  
							#~ 'pos_no': vertical_foundry['pos_no'],		   
							#~ 'schedule_qty' : bom_qty,				  
							#~ 'production_qty' : 0,				   
							#~ 'flag_applicable' : applicable,
							#~ 'order_category':	order_category,
							#~ 'flag_standard':flag_standard,
							#~ 'entry_mode':'auto',
							
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
								where limitation = %s and header_id = (select id from kg_bom where pump_model_id = %s and active='t') )
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
									
								if star_value == 1:
									### Formula ###
									#(ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-3)/2
									###
									print "ddddddddddddddd",h_value, bp, setting_height, a_value, b_value
									length = (h_value + bp + setting_height - a_value - b_value - 3)/2
									
								if star_value > 1:
									### Formula ###
									#(ABOVE BP(H)+BP+SETTING HEIGHT-A-BEND-1.5)-(NO OF STAR SUPPORT*1.5)/NO OF STAR SUPPORT+1
									###
									length = ((h_value+bp+setting_height-a_value-b_value-1.5)-(star_value*1.5))/(star_value+1)
									
							if ms_rec.length_type == 'drive_column_pipe':
								
								if star_value == 1:
									### Formula ###
									#(3.5+bp+setting height-a1-no of star support)/2
									###
									length = (3.5+bp+setting_height-a1_value-vo_star_value['star'])/2
									
									
								if star_value > 1:
									### Formula ###
									#(3.5+bp+setting height-a1-(No. of star support * star support value)-((No. Of star support-1) * LINE COLUMN PIPE value))/2
									###
									### Calculating Line Column Pipe ###
									### Formula = Standard Length ###
									line_column_pipe = vo_star_value['lcp']
									length = (3.5+bp+setting_height-a1_value-(star_value * vo_star_value['star'])-((star_value-1)*line_column_pipe))/2
									
									
							if ms_rec.length_type == 'pump_column_pipe':
								
								if star_value == 1:
									### Formula ###
									#(3.5+bp+setting height-a1-no of star support)/2
									###
									length = (3.5+bp+setting_height-a1_value-vo_star_value['star'])/2
									
									
								if star_value > 1:
									### Formula ###
									#(3.5+bp+setting height-a1-no of star support-NO OF LINE COLUMN PIPE)/2
									###
									### Calculating Line Column Pipe ###
									### Formula = Standard Length ###
									line_column_pipe = vo_star_value['lcp']
									length = (3.5+bp+setting_height-a1_value-(star_value * vo_star_value['star'])-((star_value-1)*line_column_pipe))/2
									
									
							if ms_rec.length_type == 'pump_shaft':
								
								if star_value == 1:
									### Formula ###
									#(STAR SUPPORT/2-1)+PUMP COLOUMN PIPE+A2
									###
									pump_column_pipe = (3.5+bp+setting_height-a1_value-vo_star_value['star'])/2
									length = (star_value/2-1)+pump_column_pipe+a2_value
									
									
								if star_value > 1:
									### Formula ###
									#(STAR SUPPORT/2-1)+PUMP COLOUMN PIPE+A2
									###
									line_column_pipe = vo_star_value['lcp']
									pump_column_pipe = (3.5+bp+setting_height-a1_value-(star_value * vo_star_value['star'])-((star_value-1)*line_column_pipe))/2
									length = ((vo_star_value['star']/2)-1)+pump_column_pipe+a2_value
									
							if ms_rec.length_type == 'drive_shaft':
								
								if star_value == 1:
									### Formula ###
									#(STAR SUPPORT/2-1)+DRIVE COLOUMN PIPE-3.5+SHAFT EXT
									###
									drive_col_pipe = (3.5+bp+setting_height-a1_value-vo_star_value['star'])/2
									length = (star_value/2-1)+drive_col_pipe-3.5+shaft_ext
									
								if star_value > 1:
									### Formula ###
									#(STAR SUPPORT/2-1)+DRIVE COLOUMN PIPE-3.5+SHAFT EXT
									###
									line_column_pipe = vo_star_value['lcp']
									drive_col_pipe = (3.5+bp+setting_height-a1_value-(star_value * vo_star_value['star'])-((star_value-1)*line_column_pipe))/2
									length = ((vo_star_value['star']/2)-1)+drive_col_pipe-3.5+shaft_ext
						
						print "length---------------------------->>>>",length
						if length > 0:
							ms_bom_qty = round(length,0)
						else:
							ms_bom_qty = 0
						print "ms_bom_qty---------------------------->>>>",ms_bom_qty
						#~ if qty == 0:
							#~ vertical_ms_qty = vertical_ms_details['qty']
						#~ if qty > 0
						vertical_ms_qty = ms_bom_qty
							
						print "vertical_ms_qty---------------------------->>>>",vertical_ms_qty
						
						if vertical_ms_details['position_id'] == None:
							raise osv.except_osv(_('Warning!'),
							_('Kindly Configure Position No. in MS Items for respective Pump Bom and proceed further !!'))
						
						if vertical_ms_details['ms_id']:
							ms_rec = self.pool.get('kg.machine.shop').browse(cr,uid,vertical_ms_details['ms_id'])
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
												'weight': raw.weight,
												'uom_conversation_factor': raw.uom_conversation_factor,
												'temp_qty': raw.temp_qty,
												'qty': raw.qty,
												'remarks': raw.remarks,
												}])
						
						ms_vals.append({
							
							'position_id':vertical_ms_details['position_id'],
							'ms_id': vertical_ms_details['ms_id'],
							'qty': vertical_ms_details['qty'] * qty,
							'ms_name': vertical_ms_details['name'],
							'length': vertical_ms_qty,
							'load_bom': True,
							'is_applicable': True,
							'active': True,
							'moc_id': moc_id,
							'line_ids': ch_ms_vals,
							
							#~ 'pos_no':pos_no,
							#~ 'ms_line_id': vertical_ms_details['id'],
							#~ 'bom_id': vertical_ms_details['bom_id'],
							#~ 'name': vertical_ms_details['name'],
							#~ 'length': vertical_ms_qty,
							#~ 'flag_applicable' : applicable,
							#~ 'flag_standard':flag_standard,
							#~ 'entry_mode':'auto',
							#~ 'order_category':order_category,
									  
							})
							
							#~ 'moc_id': moc_id,
							
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
								where limitation = %s and header_id = (select id from kg_bom where pump_model_id = %s and active='t') )
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
					
						bot_vals.append({
							
							#~ 'bot_line_id': vertical_bot_details['id'],
							#~ 'bom_id': vertical_bot_details['bom_id'],							
							#~ 'flag_applicable' : applicable,
							#~ 'flag_standard':flag_standard,
							#~ 'entry_mode':'auto',
							#~ 'order_category':	order_category,
							'bot_id': vertical_bot_details['bot_id'],
							'position_id': vertical_bot_details['position_id'] or False,
							'qty': vertical_bot_qty * qty,
							'load_bom': True,
							'is_applicable': True,
							'active': True,
							'flag_is_bearing': bot_rec.is_bearing,
							'moc_id': moc_id,
							
							})
							
							#~ 'position_id': item.position_id.id,
							#~ 'bot_name': item_name,
							#~ 'moc_id': moc_id,
							
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
						self.pool.get('ch.primecost.view.ms').write(cr,uid,ms_item.id,{'prime_cost':ms_prime_cost * ms_item.qty})
						prime_cost += ms_prime_cost * ms_item.qty
						
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
				
			self.write(cr, uid, ids, {'confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
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
			
			print"primecost_vals",primecost_vals
			
			#~ if entry.line_ids:
				#~ item = entry.line_ids
				#~ categ = 'fou'
				#~ primecost_vals = 0.00
				#~ primecost_vals = self._prepare_primecost(cr,uid,item,categ,entry)
			#~ elif entry.line_ids_a:
				#~ item = entry.line_ids_a
				#~ categ = 'ms'
				#~ primecost_vals = 0.00
				#~ primecost_vals = self._prepare_primecost(cr,uid,item,categ,entry)
			#~ elif entry.line_ids_b:
				#~ item = entry.line_ids_b
				#~ categ = 'bot'
				#~ primecost_vals = 0.00
				#~ primecost_vals = self._prepare_primecost(cr,uid,item,categ,entry)
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
		
		#~ bom_line_ids = item.line_ids
		#~ bom_ms_line_ids = item.line_ids_a
		#~ bom_bot_line_ids = item.line_ids_b
		#~ bom_line_id = []
		#~ bom_ms_line_id = []
		#~ bom_bot_line_id = []
		#~ for bm_line in bom_line_ids:
			#~ if bm_line.is_applicable == True:
				#~ bom_line_rec = self.pool.get('ch.kg.crm.foundry.item').browse(cr,uid,bm_line.id)
				#~ bom_line_id.append(bom_line_rec)
		#~ for ms_line in bom_ms_line_ids:
			#~ if ms_line.is_applicable == True:
				#~ ms_line_rec = self.pool.get('ch.kg.crm.machineshop.item').browse(cr,uid,ms_line.id)
				#~ bom_ms_line_id.append(ms_line_rec)
		#~ for bt_line in bom_bot_line_ids:
			#~ if bt_line.is_applicable == True:
				#~ bot_line_rec = self.pool.get('ch.kg.crm.bot').browse(cr,uid,bt_line.id)
				#~ bom_bot_line_id.append(bot_line_rec)
		
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
						print"pat_amtpat_amtpat_amt",pat_amt
			prime_cost_1 = pat_amt 
			print"vvvvvvvvvvvvvvvvvvvvvvvvvvv",prime_cost_1
			prime_cost += prime_cost_1
			print"prime_costprime_costprime_cost",prime_cost
		
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
													#~ qty = raw_line.length * raw_line.qty * raw_line.product_id.po_uom_in_kgs
											elif entry.pump_model_type == 'horizontal':
												if raw_line.uom.id == brandmoc_rec.uom_id.id:
													qty = raw_line.qty
												elif raw_line.uom.id != brandmoc_rec.uom_id.id:
													qty = raw_line.weight
										elif raw_line.product_id.uom_conversation_factor == 'two_dimension':
											qty = raw_line.weight
										#~ self.pool.get('ch.pump.vs.material.ms').write(cr,uid,ms_line.id,{'prime_cost':design_rate * qty * ms_line.qty})
										price = design_rate * qty
									tot_price += price
									self.pool.get('ch.primecost.view.ms').write(cr,uid,ms_line.id,{'prime_cost': tot_price * ms_line.qty})
					ms_price += tot_price * ms_line.qty 
					#~ self.pool.get('ch.pump.vs.material.ms').write(cr,uid,ms_line.id,{'prime_cost': design_rate * qty * ms_line.qty})
				print"ms_pricems_price",ms_price
		
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
											#~ self.pool.get('ch.pump.vs.material.bot').write(cr,uid,bot_line.id,{'prime_cost':design_rate * qty * bot_line.qty})
											
											price = design_rate * qty
										else:
											qty = design_rate = price = 0
											
										tot_price += price
										self.pool.get('ch.primecost.view.bot').write(cr,uid,bot_line.id,{'prime_cost': tot_price * bot_line.qty})
						bot_price += tot_price * bot_line.qty
						#~ self.pool.get('ch.primecost.view.bot').write(cr,uid,bot_line.id,{'prime_cost': design_rate * qty * bot_line.qty})
						print"bot_pricebot_price",bot_price
				
		print"prime_cost",prime_cost
		print"ms_price",ms_price
		print"bot_price",bot_price
		d= prime_cost + ms_price + bot_price
		print"ddddddddddddddddddddddDD",d
		primecost_tot = (prime_cost + ms_price + bot_price) 
		primecost_vals = primecost_tot
		print"primecost_valsprimecost_vals",primecost_vals
		
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
	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
	#~ def create(self, cr, uid, vals, context=None):
		#~ return super(kg_primecost_view, self).create(cr, uid, vals, context=context)
	
	#~ def write(self, cr, uid, ids, vals, context=None):
		#~ vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		#~ return super(kg_primecost_view, self).write(cr, uid, ids, vals, context)
	
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
	
	#~ def _check_qty(self, cr, uid, ids, context=None):
		#~ rec = self.browse(cr, uid, ids[0])
		#~ if rec.qty <= 0.00:
			#~ return False
		#~ return True
	
	_constraints = [
		
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
	
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
		
		## Child Tables Declaration 
		
		'line_ids': fields.one2many('ch.pc.view.ms', 'header_id', "Fou Details"),
		'load_bom': fields.boolean('Load BOM'),
		
	}
	
	_defaults = {
		
		'is_applicable': False,
		'load_bom': False,
		'active': True,
		
	}
	
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False
		return True
	
	_constraints = [
		
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
	 
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
	
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False
		return True
	
	_constraints = [
		
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
	
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
		
		## Child Tables Declaration 
		
		'load_bom': fields.boolean('Load BOM'),
		
	}
	
	_defaults = {
		
		'is_applicable': False,
		'load_bom': False,
		'flag_is_bearing': False,
		'active': True,
		
	}
	
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.qty <= 0.00:
			return False
		return True
	
	_constraints = [
		
		#~ (_check_qty,'You cannot save with zero qty !',['Qty']),
		
		]
	
ch_primecost_view_bot()
