from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

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
				various_formula = ((entry.total_weight_metal/grand_total)/grand_total)	* 100
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
		'entry_date': fields.date('Entry Date',required=True),	
		'remark': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled'),('reject','Rejected')],'Status', readonly=True),
		
		'line_ids':fields.one2many('ch.melting.charge.details', 'header_id', "Charge Details"),
		'line_ids_a':fields.one2many('ch.melting.chemistry.details', 'header_id', "Chemistry Details"),
		'line_ids_b':fields.one2many('ch.mechanical.properties', 'header_id', "Mechanical Properties"),
		
		## Furnace Log Book Start
		'moc_id': fields.many2one('kg.moc.master','MOC', required=True,domain="[('active','=','t')]"),
		'ladle_id': fields.many2one('kg.ladle.master','Ladle', required=True,domain="[('active','=','t')]"),
		'furnace_id': fields.many2one('kg.furnace.master','Furnace', required=True,domain="[('active','=','t')]"),	
		'lining_age': fields.char('Lining Age', size=128,required=True),	
		'melting_hrs': fields.float('Total Melting Hours',required=True),		
		'time': fields.float('Time',required=True),
		'time_type': fields.selection([('am','AM'),('pm','PM')],'Time Type', required=True),
		'input_volt': fields.float('Input Volt',required=True),	
		'frequency': fields.float('Frequency',required=True),	
		'kw': fields.float('KW',required=True),	
		'output_volt': fields.float('Output Volt',required=True),	
		'final_reading': fields.float('Final Reading',required=True),
		'final_reading_type': fields.selection([('unit','Units'),('ton','Ton')],'Final Reading Type', required=True),	
		'initial_reading': fields.float('Initial Reading',required=True),
		'initial_reading_type': fields.selection([('unit','Units'),('ton','Ton')],'Initial Reading Type', required=True),	
		
		'total_units': fields.float('Total Units',readonly=True),		
		'amount': fields.float('Amount',readonly=True),		
		
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
		
		
		'various': fields.function(_get_various_amt, string='Various(kg)',digits=(16,3), method=True, store=True, type='float'),		
		'melt_cost': fields.function(_get_melting_cost, string='Melting Cost(Rs.)', method=True, store=True, type='float'),
		
		'load_item': fields.boolean('Load Item'),
		
		##### Worker Details ####
		'supervisor_name': fields.many2one('res.partner','Supervisor Name', domain="[('active','=','t')]"),
		'done_by': fields.selection([('company_employee','Company Employee'),('contractor','Contractor')],'Done By'),		
		'employee_id': fields.many2many('res.partner', 'm2m_moc_employee_details', 'melting_emp_id', 'employee_id','Name'),
		'helper_count': fields.float('Helper Count'),	
		'contractor_id': fields.many2one('res.partner','Contractor Name'),
		
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),		
		
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_melting', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft',
		
		
		
		
	}
	
	_sql_constraints = [
        ('name_uniq', 'unique(name)', 'Heat No. must be unique !!'),
    ]
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])			
		if entry.initial_reading < entry.final_reading :
			return True
		else:
			return False
	
	
	### Added by Sangeetha ###
	def onchange_reading(self,cr, uid, ids, initial_reading,final_reading, context=None):
		if initial_reading > 0 and final_reading > 0:
			total_reading = final_reading - initial_reading
			total_value = total_reading * 6.25
		else:
			total_reading = 0.00
			total_value = 0.00
		return {'value': {'total_units': total_reading,'amount':total_value}}
	### Ends Here ###
	
	def onchange_weight(self,cr, uid, ids, liquid_metal_wt,ingot_wt, context=None):
		
		total_weight = liquid_metal_wt + ingot_wt
		
		return {'value': {'total_weight_metal': total_weight}}
	
	
	def load_item(self, cr, uid, ids, context=None):		
		
		rec = self.browse(cr,uid,ids[0])	
		moc = rec.moc_id	
		moc_obj=self.pool.get('kg.moc.master')			
		moc_obj_ids=moc_obj.search(cr,uid,[('id','=',rec.moc_id.id)])
		
		if rec.moc_id.id:						
						
			melting_id = rec.id			
			raw_material_line_obj = self.pool.get('ch.melting.charge.details')
			raw_material_lines=moc.line_ids	
			
			chemistry_details_line_obj = self.pool.get('ch.melting.chemistry.details')
			chemistry_details_lines=moc.line_ids_a	
			cr.execute(""" delete from ch_melting_charge_details where header_id  = %s """ %(ids[0]))
			for raw_material_line in raw_material_lines:	
				raw_material_line_id = raw_material_line_obj.create(cr,uid,
					{
						'header_id':rec.id,
						'product_id': raw_material_line.product_id.id,
						'moc_id':rec.moc_id.id			
					})
			cr.execute(""" delete from ch_melting_chemistry_details where header_id  = %s """ %(ids[0]))	
			for chemistry_details_line in chemistry_details_lines:					
				chemistry_details_line_id = chemistry_details_line_obj.create(cr,uid,
					{
						'header_id':rec.id,
						'chemistry_id': chemistry_details_line.chemical_id.id,
												
					})	
		self.write(cr, uid, ids, {'load_item': True})
		return True
	
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])		
		line_ids =entry.line_ids
		grand_total =0.00
		melt_cost =0.00
		for line in line_ids:			
			melt_cost += line.total_amount			
			grand_total += line.total_weight	
				
		various_formula = ((entry.total_weight_metal/grand_total)/grand_total)	* 100
		melting_total_rate = melt_cost + entry.amount
		
		if various_formula > 3.000:	
			if entry.remark == False:
				raise osv.except_osv(_('Warning!'),
						_('Various above 3% Remarks is must !!'))			
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),
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
						where header.product_id = %s and line.moc_id = %s
								  ''',[product_id,moc_id])
		purchase_price= cr.fetchone()		
		if purchase_price is not None:
			if purchase_price[0]:
				purchase_price = purchase_price[0]
			else:
				purchase_price =0
		else:
			purchase_price =0
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
		'chemistry_id': fields.many2one('kg.chemical.master','Name', required=True,domain="[('active','=','t')]"),	
		'required_chemistry':fields.float('Required Chemistry',digits_compute=dp.get_precision('Required Chemistry')),
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
		'mechanical_id': fields.many2one('kg.mechanical.master','Name', required=True,domain="[('active','=','t')]"),	
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
		print "entry.mech_value,entry.mech_value,entry.moc_id.id,entry.mechanical_id.id]",entry.mech_value,entry.mech_value,entry.moc_id.id,entry.mechanical_id.id					
		cr.execute(''' select name,header_id from ch_mechanical_chart 
						where case 
						when range_flag = 't' then
						%s >= min
						when range_flag = 'f' then
						%s >= min and
						%s <= max
						end

						and
						header_id = %s and mechanical_id = %s	
	 
							  ''',[entry.mech_value,entry.mech_value,entry.mech_value,entry.moc_id.id,entry.mechanical_id.id])
		values= cr.fetchone()
		print "values",values		
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
			  
		(_check_values, 'Specified Mechanical Properties has not available in MOC Master and check the values !!',['Mechanical Chart']),		
	   ]
	
ch_mechanical_properties()
