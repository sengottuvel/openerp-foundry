from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_pump_vs_material(osv.osv):

	_name = "kg.pump.vs.material"
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
				pump_cost += line.prime_cost
			for line in order.line_ids_a:
				pump_cost += line.prime_cost
			for line in order.line_ids_b:
				pump_cost += line.prime_cost
			
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
		
		'pump_id': fields.many2one('kg.pumpmodel.master', 'Pump Model'),
		'qty': fields.integer('Qty'),
		'moc_const_id': fields.many2one('kg.moc.construction', 'MOC Construction'),
		'load_bom': fields.boolean('Load BOM'),
		'pump_cost': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Pump Cost',multi="sums",store=True),	
		'total_cost': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Cost',multi="sums",store=True),	
		
		## Child Tables Declaration 
				
		'line_ids': fields.one2many('ch.pump.vs.material.fou', 'header_id', "Fou Details"),
		'line_ids_a': fields.one2many('ch.pump.vs.material.ms', 'header_id', "MS Details"),
		'line_ids_b': fields.one2many('ch.pump.vs.material.bot', 'header_id', "BOT Details"),
		
	}
		
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_pump_vs_material', context=c),			
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
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
					raise osv.except_osv(
						_('Warning!'),
						_('Pattern Name %s You cannot save without MOC'%(line.pattern_id.pattern_name)))
		if entry.line_ids_a:
			for line in entry.line_ids:
				if line.is_applicable == True and not line.moc_id:
					raise osv.except_osv(
						_('Warning!'),
						_('Item Name %s You cannot save without MOC'%(line.ms_id.name)))
		if entry.line_ids_b:
			for line in entry.line_ids:
				if line.is_applicable == True and not line.moc_id:
					raise osv.except_osv(
						_('Warning!'),
						_('Item Name %s You cannot save without MOC'%(line.bot_id.name)))
					
		return True
			
	_constraints = [        
              
        (_future_entry_date_check, 'System not allow to save with future date. !!',['']),
        (_check_is_applicable, 'Kindly select anyone is appli !!',['']),
        #~ (_check_lineitems, 'System not allow to save with empty Details !!',['']),
       
       ]
	
	def onchange_bom(self, cr, uid, ids, load_bom,pump_id,moc_const_id):
		fou_vals=[]
		ms_vals=[]
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
									'qty': item.qty,
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
								ms_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',cons_rec.code),('header_id','=',ms_rec.id)])
								if ms_line_obj:
									ms_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,ms_line_obj[0])
									moc_id = ms_line_rec.moc_id.id
						ms_vals.append({
										'position_id': item.position_id.id,
										'ms_name': item.name,
										'ms_id': item.ms_id.id,
										'moc_id': moc_id,
										'qty': item.qty,
										'load_bom': True,
										'is_applicable': True,
										'active': True,
										#~ 'remarks': item.remarks,
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
								bot_line_obj = self.pool.get('ch.machine.mocwise').search(cr,uid,[('code','=',cons_rec.code),('header_id','=',bot_rec.id)])
								if bot_line_obj:
									bot_line_rec = self.pool.get('ch.machine.mocwise').browse(cr,uid,bot_line_obj[0])
									moc_id = bot_line_rec.moc_id.id
						bot_vals.append({
										'position_id': item.position_id.id,
										'bot_name': item_name,
										'bot_id': item.bot_id.id,
										'moc_id': moc_id,
										'qty': item.qty,
										'load_bom': True,
										'is_applicable': True,
										'active': True,
										#~ 'remarks': item.remarks,
										})
			
		return {'value': {'line_ids': fou_vals,'line_ids_a': ms_vals,'line_ids_b': bot_vals}}
		
	def entry_update(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		total_cost = pump_cost = fou_cost = ms_cost = bot_cost = 0
		if entry.line_ids:
			item = entry.line_ids
			categ = 'fou'
			primecost_vals = 0.00
			primecost_vals = self._prepare_primecost(cr,uid,item,categ,entry)
		if entry.line_ids_a:
			item = entry.line_ids_a
			categ = 'ms'
			primecost_vals = 0.00
			primecost_vals = self._prepare_primecost(cr,uid,item,categ,entry)
		if entry.line_ids_b:
			item = entry.line_ids_b
			categ = 'bot'
			primecost_vals = 0.00
			primecost_vals = self._prepare_primecost(cr,uid,item,categ,entry)
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
						
						self.pool.get('ch.pump.vs.material.fou').write(cr,uid,fou_line.id,{'prime_cost': design_rate * qty})
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
											if raw_line.uom.id == brandmoc_rec.uom_id.id:
												qty = raw_line.qty
											elif raw_line.uom.id != brandmoc_rec.uom_id.id:
												qty = raw_line.weight
										elif raw_line.product_id.uom_conversation_factor == 'two_dimension':
											qty = raw_line.weight
										#~ self.pool.get('ch.pump.vs.material.ms').write(cr,uid,ms_line.id,{'prime_cost':design_rate * qty * ms_line.qty})
										price = design_rate * qty
									tot_price += price
					ms_price += tot_price * ms_line.qty
					self.pool.get('ch.pump.vs.material.ms').write(cr,uid,ms_line.id,{'prime_cost': ms_price})
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
										tot_price += price
						bot_price += tot_price * bot_line.qty
						self.pool.get('ch.pump.vs.material.bot').write(cr,uid,bot_line.id,{'prime_cost': bot_price})
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
			seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pump.vs.material')])
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
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def create(self, cr, uid, vals, context=None):
		return super(kg_pump_vs_material, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_pump_vs_material, self).write(cr, uid, ids, vals, context)
		
	_sql_constraints = [
	
		('name', 'unique(name)', 'No must be Unique !!'),
	]	
	
kg_pump_vs_material()

class ch_pump_vs_material_fou(osv.osv):

	_name = "ch.pump.vs.material.fou"
	_description = "Child Foundry Item Details"
	
	_columns = {
	
		### Basic Info
		
		'header_id':fields.many2one('kg.pump.vs.material', 'Pump Material', ondelete='cascade'),
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
		
		## Child Tables Declaration 
		
		'load_bom': fields.boolean('Load BOM'),
		
	}
	
	_defaults = {
		
		'is_applicable': False,
		'load_bom': False,
		'active': True,
		
	}
	
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_pump_vs_material_fou, self).write(cr, uid, ids, vals, context)
		
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
	
ch_pump_vs_material_fou()

class ch_pump_vs_material_ms(osv.osv):

	_name = "ch.pump.vs.material.ms"
	_description = "Child MS Item Details"
	
	_columns = {
		
		### Basic Info
		
		'header_id':fields.many2one('kg.pump.vs.material', 'Pump Material', ondelete='cascade'),
		'remarks': fields.char('Remarks'),
		'active': fields.boolean('Active'),	
		
		### Module Requirement
		
		'qty': fields.integer('Qty', required=True),
		'position_id': fields.many2one('kg.position.number','Position No'),
		'ms_id':fields.many2one('kg.machine.shop', 'Item Code', domain=[('type','=','ms')], ondelete='cascade',required=True),
		'ms_name': fields.related('ms_id','name', type='char',size=128,string='Item Name', store=True),
		'is_applicable': fields.boolean('Is Applicable'),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		'prime_cost': fields.float('Prime Cost'),
		
		## Child Tables Declaration 
		
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
		
ch_pump_vs_material_ms()

class ch_pump_vs_material_bot(osv.osv):

	_name = "ch.pump.vs.material.bot"
	_description = "Child BOT Item Details"
	
	_columns = {
	
		### Basic Info
		
		'header_id':fields.many2one('kg.pump.vs.material', 'Pump Material', ondelete='cascade'),
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
		
		## Child Tables Declaration 
		
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
		
ch_pump_vs_material_bot()
