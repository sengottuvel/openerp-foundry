from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import base64

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')


class kg_melting(osv.osv):

	_name = "kg.melting"
	_description = "Melting Log"
	_order = "entry_date desc"
	
	def _get_various_amt(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		melt_cost = 0
		grand_total = 0
		various_formula = 0
		for entry in self.browse(cr, uid, ids, context=context):			
			for line in entry.line_ids:				
				melt_cost += line.total_amount			
				grand_total += line.total_weight	
			if grand_total != 0:
				
				various_formula = (grand_total - entry.total_weight_metal)/((grand_total + entry.total_weight_metal)/2)*100								
				#various_formula = ((entry.total_weight_metal/grand_total)/grand_total)	* 100
			else:
				pass
			
			result[entry.id] = various_formula
		return result
		
	def _get_melting_cost(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		melt_cost = 0		
		melting_total_rate = 0
		for entry in self.browse(cr, uid, ids, context=context):
			for line in entry.line_ids:			
				melt_cost += line.total_amount					
			melting_total_rate = melt_cost + entry.amount
			result[entry.id] = melting_total_rate
		return result
	
	_columns = {
	
		### Header Details ####
		
		'name': fields.char('Heat No.', size=128,required=True),	
		'entry_date': fields.datetime('Entry Date',required=True),	
		'remark': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('approved','Approved'),('cancel','Cancelled'),('reject','Rejected')],'Status', readonly=True),
		
		'line_ids':fields.one2many('ch.melting.charge.details', 'header_id', "Charge Details"),
		'line_ids_a':fields.one2many('ch.melting.chemistry.details', 'header_id', "Chemistry Details"),
		'line_ids_b':fields.one2many('ch.mechanical.properties', 'header_id', "Mechanical Properties"),
		
		## Furnace Log Book Start
		'moc_id': fields.many2one('kg.moc.master','MOC', required=True,domain="[('state','=','approved')]"),
		'ladle_id': fields.many2one('kg.ladle.master','Ladle', required=True,domain="[('state','=','approved')]"),
		'furnace_id': fields.many2one('kg.furnace.master','Furnace', required=True,domain="[('state','=','approved')]"),	
		'lining_age': fields.char('Lining Age', size=128,required=True),	
		'melting_hrs': fields.float('Total Melting Hours',required=True),		
		'time': fields.float('Time',required=True),
		'time_type': fields.selection([('am','AM'),('pm','PM')],'Time Type', required=True),
		'input_volt': fields.float('Input Volt',required=True),	
		'frequency': fields.float('Frequency',required=True),	
		'kw': fields.float('KW',required=True),	
		'output_volt': fields.float('Output Volt',required=True),	
		'final_reading': fields.float('Final Reading',required=True),
		'final_reading_type': fields.selection([('unit','Units'),('ton','Ton')],'Final Reading Type'),	
		'initial_reading': fields.float('Initial Reading',required=True),
		'initial_reading_type': fields.selection([('unit','Units'),('ton','Ton')],'Initial Reading Type'),	
		
		'total_units': fields.float('Total Units',readonly=True),		
		'amount': fields.float('Amount',readonly=True , help="total_value = total_reading * rate_rec.value"),		
		
		'pouring_temp': fields.float('Pouring Temp',required=True),
		'pouring_hrs': fields.float('Pouring Hours',required=True),
		'pouring_hrs_type': fields.selection([('am','AM'),('pm','PM')],'Pouring Hr Type', required=True),
		'ret': fields.char('Return Metal',required=True),			
		'tapping_temp': fields.float('Tepping Temp',required=True),	
		'pouring_finished': fields.float('Pouring Finished at',required=True),
		'pouring_finished_time_type': fields.selection([('am','AM'),('pm','PM')],'Time Type', required=True),
		'liquid_metal_wt': fields.float('Liquid Metal Wt.',required=True,digits=(16,3)),	
		'ingot_wt': fields.float('Ingot Wt.',required=True,digits=(16,3)),	
		'total_weight_metal': fields.float('Total Weight',digits=(16,3)),	
		
		
		'various': fields.function(_get_various_amt, string='Melting loss(%)',digits=(16,3), method=True, store=True, type='float' , help="Total = (Grand total weight - Total Weight)/((Grand total weight + Total Weight)/2)*100"),		
		'melt_cost': fields.function(_get_melting_cost, string='Melting Cost(Rs.)', method=True, store=True, type='float'),
		
		
		
		##### Worker Details ####
		'supervisor_name': fields.many2one('res.partner','Supervisor Name',domain="[('contractor','=','t'),('partner_state','=','approve')]"),
		'done_by': fields.selection([('company_employee','Company Employee'),('contractor','Contractor')],'Done By'),		
		'employee_id': fields.many2many('hr.employee', 'm2m_moc_employee_details', 'melting_emp_id', 'employee_id','Employee Name',domain="[('status','=','approved')]"),
		'helper_count': fields.float('Helper Count'),	
		'contractor_id': fields.many2one('res.partner','Contractor Name',domain="[('contractor','=','t'),('partner_state','=','approve')]"),
		
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		
		'ap_date': fields.datetime('Approved Date', readonly=True),
		'ap_user_id': fields.many2one('res.users', 'Approved By', readonly=True),	
		
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),		
		
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_melting', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft',
		
		
		
		
	}
	
	_sql_constraints = [
        ('name_uniq', 'unique(name)', 'Heat No. must be unique !!'),
    ]
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])			
		if entry.initial_reading > entry.final_reading :
			raise osv.except_osv(_('Warning!'),
						_('Initial Reading should not be less than Final Reading check the values !!'))
		if entry.time > 13.00:
			raise osv.except_osv(_('Warning!'),
						_('Start Time Should not Exceed 12 Hours for Power Control Details !!'))
		if entry.pouring_hrs > 13.00:
			raise osv.except_osv(_('Warning!'),
						_('Start Time Should not Exceed 12 Hours for Pouring Temp !!'))
		if entry.pouring_finished > 13.00:
			raise osv.except_osv(_('Warning!'),
						_('Start Time Should not Exceed 12 Hours for Pouring Finished !!'))
		
		return True
	
	
	### Added by Sangeetha ###
	def onchange_reading(self,cr, uid, ids, initial_reading,final_reading, context=None):
		if initial_reading > 0 and final_reading > 0:
			total_reading = (final_reading - initial_reading) * 1000
			rate_obj = self.pool.get('kg.consumable.rate')
			rate_ids = rate_obj.search(cr, uid, [('category','=','power'),('state','=','approved')])
			rate_rec = rate_obj.browse(cr, uid, rate_ids[0])			
			total_value = total_reading * rate_rec.value
		else:
			total_reading = 0.00
			total_value = 0.00
		return {'value': {'total_units': total_reading,'amount':total_value}}
	### Ends Here ###
	
	def onchange_weight(self,cr, uid, ids, liquid_metal_wt,ingot_wt, context=None):
		
		total_weight = liquid_metal_wt + ingot_wt
		
		return {'value': {'total_weight_metal': total_weight}}
	
	
	def onchange_moc_details(self, cr, uid, ids, moc_id,context=None):			
		chemistry_details_vals=[]
		raw_material_vals=[]
		mech_details_vals=[]
		moc_obj=self.pool.get('kg.moc.master')			
		if moc_id:					
			moc_obj_ids=moc_obj.search(cr,uid,[('id','=',moc_id)])
			moc_rec = moc_obj.browse(cr,uid,moc_obj_ids[0])
			raw_material_line_obj = self.pool.get('ch.melting.charge.details')
			raw_material_lines=moc_rec.line_ids	
			
			chemistry_details_line_obj = self.pool.get('ch.melting.chemistry.details')
			chemistry_details_lines=moc_rec.line_ids_a	
			
			mech_details_line_obj = self.pool.get('ch.mechanical.properties')
			mech_details_lines=moc_rec.line_ids_b	
			
			for raw_material_line in raw_material_lines:	
				raw_material_vals.append({
						
						'product_id': raw_material_line.product_id.id,
						'moc_id':moc_id		
					})
			
			for chemistry_details_line in chemistry_details_lines:					
				chemistry_details_vals.append({
						
						'chemistry_id': chemistry_details_line.chemical_id.id,
						'required_chemistry': chemistry_details_line.min,
						'required_chemistry_max': chemistry_details_line.max,
												
					})			
					
			for mech_details_line in mech_details_lines:	
				
				mech_details_vals.append({
						
						'mechanical_id': mech_details_line.mechanical_id.id,
						'uom': mech_details_line.uom,
						'min': mech_details_line.min,
						'max': mech_details_line.max,
						'moc_id': moc_rec.id,
												
					})
		return {'value': {'line_ids': raw_material_vals,'line_ids_a': chemistry_details_vals,'line_ids_b': mech_details_vals}}
	
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])	
		if entry.state == 'draft':	
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		
		return True
	
	def entry_approve(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])	
		if entry.state == 'confirmed':	
			line_ids =entry.line_ids
			grand_total =0.00
			melt_cost =0.00
			for entry in entry.line_ids_b:
				print"entry.mech_value,entry.mech_value,entry.mech_value,entry.mpa_value,entry.mpa_value,entry.mpa_value,entry.moc_id.id,entry.mechanical_id.id",entry.mech_value,entry.mech_value,entry.mech_value,entry.mpa_value,entry.mpa_value,entry.mpa_value,entry.moc_id.id,entry.mechanical_id.id
				cr.execute(''' select moc_line.header_id from 

										ch_mechanical_chart as moc_line
										left join kg_mechanical_master mech on mech.id = moc_line.mechanical_id
										where 
										case when mech.value_limit = 'based_on_value' then
										(case when moc_line.range_flag = 't' then 
										%s >= moc_line.min
										when moc_line.range_flag = 'f' then
										%s >= moc_line.min and
										%s <= moc_line.max
										end)
										else
										(case when moc_line.range_flag = 't' then 
										%s >= moc_line.min
										when moc_line.range_flag = 'f' then
										%s >= moc_line.min and
										%s <= moc_line.max
										end) end 
										

										and
										moc_line.header_id = %s and moc_line.mechanical_id = %s
								  ''',[entry.mech_value,entry.mech_value,entry.mech_value,entry.mpa_value,entry.mpa_value,entry.mpa_value,entry.moc_id.id,entry.mechanical_id.id])
				values= cr.fetchone()			
				if values:
					pass
				else:
					raise osv.except_osv(_('Mechanical Chart'),
							_('Specified Mechanical Properties getting mismatch with MOC master configuration !!'))
			
			
			for line in line_ids:			
				melt_cost += line.total_amount			
				grand_total += line.total_weight	
			if entry.total_weight_metal > 0.00 and grand_total > 0.00:	
				print"wwwwwww"
				#various_formula = ((entry.total_weight_metal/grand_total)/grand_total)	* 100
				various_formula = (grand_total - entry.total_weight_metal)/((grand_total + entry.total_weight_metal)/2)*100		
			else:
				various_formula = 0.00
			melting_total_rate = melt_cost + entry.amount
			
			if various_formula > 3.000:	
				if entry.remark == False:
					raise osv.except_osv(_('Warning!'),
							_('Various above 3% Remarks is must !!'))			
			self.write(cr, uid, ids, {'state': 'approved','ap_user_id': uid, 'ap_date': time.strftime('%Y-%m-%d %H:%M:%S'),
			'various': various_formula,'melt_cost': melting_total_rate})		
		
		return True
	
		
	def entry_cancel(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.cancel_remark == False:
			raise osv.except_osv(_('Warning!'),
						_('Cancellation Remarks is must !!'))
		self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S'),'transac_state':'cancel'})
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):
			if rec.state == 'confirmed':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_melting, self).write(cr, uid, ids, vals, context)
	
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_code = str(rec.name)		
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
			
		url = 'http://192.168.1.7/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&melting_log='+rec_code

		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
	
	_constraints = [		
			  
		(_check_values, ' Initial Reading should not be less than Final Reading check the values !!',['Reading Details']),		
	   ]
	
	
kg_melting()


class ch_melting_charge_details(osv.osv):
	
	_name = "ch.melting.charge.details"
	_description = "Charge Details"
	
	_columns = {
			
		'header_id':fields.many2one('kg.melting', 'Melting Entry', required=True, ondelete='cascade'),							
		'product_id': fields.many2one('product.product','Raw Materials', required=True,domain="[('active','=','t'),('product_type','in',('raw','ms','bot'))]"),	
		'first_addition':fields.float('First Addition',digits=(16,3)),
		'second_addition':fields.float('Second Addition',digits=(16,3)),
		'total_weight':fields.float('Total Weight(kg.)',digits=(16,3)),
		'total_amount':fields.float('Amount',digits=(16,3)),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'remarks':fields.text('Remarks'),	
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		return context
	
	def onchange_purchase_rate(self,cr, uid, ids, product_id,moc_id,first_addition,second_addition, context=None):		
		cr.execute(''' select line.purchase_price from kg_brandmoc_rate as header
						left join ch_brandmoc_rate_details line on line.header_id = header.id
						where header.product_id = %s and line.moc_id = %s and header.state != 'expire' order by line.id desc limit 1
								  ''',[product_id,moc_id])
		purchase_price= cr.fetchone()		
		if purchase_price is not None:
			if purchase_price[0]:
				purchase_price = purchase_price[0]
			else:
				purchase_price =0
		else:
			cr.execute(''' select line.purchase_price from kg_brandmoc_rate as header
						left join ch_brandmoc_rate_details line on line.header_id = header.id
						where header.product_id = %s and header.state != 'expire' order by line.id desc limit 1
								  ''',[product_id])
			purchase_price= cr.fetchone()
			
			if purchase_price is None:
				purchase_price = 0.00		
			else:				
				purchase_price = purchase_price[0]
			
		
		total = first_addition + second_addition
		
		amount = total * purchase_price
		
		
		return {'value': {'total_weight': total,'total_amount':amount}}
		
	def onchange_addition(self,cr, uid, ids, first_addition,second_addition, context=None):
		
		total = first_addition + second_addition
		
		return {'value': {'total_weight': total}}
	
	
ch_melting_charge_details()

class ch_melting_chemistry_details(osv.osv):
	
	_name = "ch.melting.chemistry.details"
	_description = "Chemistry Details"
	
	_columns = {
			
		'header_id':fields.many2one('kg.melting', 'Chemistry Entry', required=True, ondelete='cascade'),							
		'chemistry_id': fields.many2one('kg.chemical.master','Name', required=True,domain="[('state','=','approved')]"),	
		'required_chemistry':fields.float('Required Chemistry Min',digits_compute=dp.get_precision('Required Chemistry')),
		'required_chemistry_max':fields.float('Required Chemistry Max',digits_compute=dp.get_precision('Required Chemistry')),
		'bath_1':fields.float('Bath 1',digits=(16,3)),
		'bath_2':fields.float('Bath 2',digits=(16,3)),
		'final':fields.float('Final',digits=(16,3)),
		'remarks':fields.text('Remarks'),	
		
	}
	
	
ch_melting_chemistry_details()

class ch_mechanical_properties(osv.osv):
	
	_name = "ch.mechanical.properties"
	_description = "Mechanical Properties"
	
	_columns = {
			
		'header_id':fields.many2one('kg.melting', 'Melting Entry', required=True, ondelete='cascade'),
		'uom': fields.char('UOM',size=128),						
		'mechanical_id': fields.many2one('kg.mechanical.master','Name', required=True,domain="[('state','=','approved')]"),	
		'mech_value':fields.float('Value',required=True),
		'min':fields.float('Min'),
		'max':fields.float('Max'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'mpa_value':fields.float('MPA Value',readonly=True),		
		
	}
	def default_get(self, cr, uid, fields, context=None):
		return context
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
						
		cr.execute(''' select moc_line.header_id from 

									ch_mechanical_chart as moc_line
									left join kg_mechanical_master mech on mech.id = moc_line.mechanical_id
									where 
									case when mech.value_limit = 'based_on_value' then
									(case when moc_line.range_flag = 't' then 
									%s >= moc_line.min
									when moc_line.range_flag = 'f' then
									%s >= moc_line.min and
									%s <= moc_line.max
									end)
									else
									(case when moc_line.range_flag = 't' then 
									%s >= moc_line.min
									when moc_line.range_flag = 'f' then
									%s >= moc_line.min and
									%s <= moc_line.max
									end) end 
									

									and
									moc_line.header_id = %s and moc_line.mechanical_id = %s
							  ''',[entry.mech_value,entry.mech_value,entry.mech_value,entry.mpa_value,entry.mpa_value,entry.mpa_value,entry.moc_id.id,entry.mechanical_id.id])
		values= cr.fetchone()			
		if values:
			return True
		else:
			return False
		
	def onchange_uom_name(self, cr, uid, ids, mechanical_id, context=None):
		
		value = {'uom': ''}
		if mechanical_id:
			uom_rec = self.pool.get('kg.mechanical.master').browse(cr, uid, mechanical_id, context=context)
			value = {'uom': uom_rec.uom.name}
			
		return {'value': value}
		
	def onchange_mpa_value(self, cr, uid, ids, mech_value, context=None):
		
		value = {'mpa_value': ''}
		if value:
			print"mech_value",mech_value
			mpa = mech_value * 9.8067
			print"mpa",mpa		
			value = {'mpa_value': mpa}
			print"value_mpa",value				
		return {'value': value}
		
	def create(self, cr, uid, vals, context=None):		
		mech_obj = self.pool.get('kg.mechanical.master')
		if vals.get('mechanical_id'):		  
			uom_rec = mech_obj.browse(cr, uid, vals.get('mechanical_id') )
			uom_name = uom_rec.uom.name			
			vals.update({'uom': uom_name})
		return super(ch_mechanical_properties, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):		
		mech_obj = self.pool.get('kg.mechanical.master')
		if vals.get('mechanical_id'):
			uom_rec = mech_obj.browse(cr, uid, vals.get('mechanical_id') )
			uom_name = uom_rec.uom.name			
			vals.update({'uom': uom_name})
		return super(ch_mechanical_properties, self).write(cr, uid, ids, vals, context)  
		
	_constraints = [		
			  
		#(_check_values, 'Specified Mechanical Properties has not available in MOC Master and check the values !!',['Mechanical Chart']),		
	   ]
	
ch_mechanical_properties()









