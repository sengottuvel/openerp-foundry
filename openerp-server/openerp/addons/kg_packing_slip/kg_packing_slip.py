from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import base64

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')


ORDER_PRIORITY = [
   ('1','MS NC'),
   ('2','NC'),
   ('3','Service'),
   ('4','Emergency'),
   ('5','Spare'),
   ('6','Normal'),
  
]

ORDER_CATEGORY = [
   ('pump','Pump'),
   ('spare','Spare'),
   ('pump_spare','Pump and Spare'),
   ('service','Service'),
   ('project','Project'),
   ('access','Accessories')
]

class kg_packing_slip(osv.osv):

	_name = "kg.packing.slip"
	_description = "Packing Slip Entry"
	_order = "entry_date desc"
	
	def _get_default_division(self, cr, uid, context=None):
		res = self.pool.get('kg.division.master').search(cr, uid, [('code','=','SAM'),('state','=','approved'), ('active','=','t')], context=context)
		return res and res[0] or False
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Slip No.', size=128,select=True),
		'entry_date': fields.date('Date',required=True),
		'note': fields.text('Notes'),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([
			('draft','Draft'),
			('confirm','Confirmed'),
			('cancel','Cancelled'),
			],'Status', readonly=True),
		
		### Work Order Details ###
		
		'division_id': fields.related('order_id','division_id', type='many2one', relation='kg.division.master', string='Division', store=True, readonly=True),
		'location': fields.related('order_id','location', type='selection', selection=[('ipd','IPD'),('ppd','PPD'),('export','Export')], string='Location', store=True, readonly=True),
		'order_no': fields.related('order_line_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('order_line_id','delivery_date', type='date', string='Delivery Date', store=True, readonly=True),
		'order_date': fields.related('order_id','entry_date', type='date', string='Order Date', store=True, readonly=True),
		'order_category': fields.related('order_line_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'pump_model_id': fields.related('order_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'moc_construction_id': fields.related('order_line_id','moc_construction_id', type='many2one', relation='kg.moc.construction', string='MOC Construction Code', store=True, readonly=True),
		'entry_mode': fields.selection([('manual','Manual'),('auto','Auto')],'Entry Mode'),
		'line_ids': fields.one2many('ch.packing.default.details', 'header_id', "Default Item Details"),
		'line_ids_a': fields.one2many('ch.packing.foundry.details', 'header_id', "Foundry Details"),
		'line_ids_b': fields.one2many('ch.packing.ms.details', 'header_id', "MS Details"),
		'line_ids_c': fields.one2many('ch.packing.bot.details', 'header_id', "BOT Details"),
		'line_ids_d': fields.one2many('ch.packing.accessories', 'header_id', "Accessories Details"),
		'line_ids_e': fields.one2many('ch.packing.checklist', 'header_id', "Checklist Details"),
		
		### Packing slip details ###
		'packing_type': fields.selection([('pump','Pump'),('spare','Spare'),('access','Accessories')],'Type'),
		'assembly_id': fields.many2one('kg.assembly.inward', 'Pump Serial No.' ,domain="[('pump_serial_no','!=',False)]"),
		'order_id': fields.many2one('kg.work.order','Work Order'),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line',domain="[('order_category','=',packing_type)]"),
		'pump_model_type': fields.related('order_line_id','pump_model_type', type='selection', selection=[('vertical','Vertical'),('horizontal','Horizontal'),('others','Others')], string='Pump Type', store=True, readonly=True),
		'box_no': fields.char('Box No.',size=50),
		'flag_load_bom': fields.boolean('Load BOM'),
		
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_packing_slip', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',
		'active': True,
		'division_id':_get_default_division,
		'entry_mode': 'manual',
		
	
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
		
	def onchange_assembly_id(self, cr, uid, ids, assembly_id):
		value = {'order_id':False,'order_line_id':False}
		if assembly_id:
			ass_rec = self.pool.get('kg.assembly.inward').browse(cr,uid,assembly_id)	
			value = {'order_id': ass_rec.order_id.id,'order_line_id': ass_rec.order_line_id.id,
			'pump_model_type':ass_rec.order_line_id.pump_model_type}

		return {'value': value}
		
		
	def onchange_pump_serial(self, cr, uid, ids, assembly_id,packing_type,order_line_id):
		value = {'order_id':False,'order_line_id':False}
		default_items = []
		tag_no = ''
		api_plan = ''
		shaft_sealing = ''
		print "assembly_id",assembly_id
		print "order_line_id",order_line_id
		
		
		if order_line_id:
			order_rec = self.pool.get('ch.work.order.details').browse(cr,uid,order_line_id)
			if order_rec.flange_standard.name:
				flange_standard = order_rec.flange_standard.name
			else:
				flange_standard = ''
			if order_rec.enquiry_line_id:
				enq_rec = self.pool.get('ch.kg.crm.pumpmodel').browse(cr,uid,order_rec.enquiry_line_id)
				tag_no = enq_rec.equipment_no
				api_plan = enq_rec.api_plan
			### Default Line Items ###
			#### Pump ###
			default_items.append({
														
				'order_line_id': order_rec.id,
				'enquiry_line_id': order_rec.enquiry_line_id,
				'packing_type' : packing_type,
				'description': 'Pump',
				'value': 1,  
				})
			#### Shaft sealing ###
			('g_p','Gland packing'),('m_s','Mechanical Seal'),('f_s','Felt Seal'),('d_s','Dynamic seal')
			if order_rec.shaft_sealing == 'g_p':
				shaft_sealing = 'Gland packing'
			if order_rec.shaft_sealing == 'm_s':
				shaft_sealing = 'Mechanical Seal'
			if order_rec.shaft_sealing == 'f_s':
				shaft_sealing = 'Felt Seal'
			if order_rec.shaft_sealing == 'd_s':
				shaft_sealing = 'Dynamic seal'
			default_items.append({
														
				'order_line_id': order_rec.id,
				'enquiry_line_id': order_rec.enquiry_line_id,
				'packing_type': packing_type,
				'description': 'Shaft sealing',
				'value': shaft_sealing,  
				})
			#### Flange standard ###
			default_items.append({
														
				'order_line_id': order_rec.id,
				'enquiry_line_id': order_rec.enquiry_line_id,
				'packing_type': packing_type,
				'description': 'Flange standard',
				'value': flange_standard,  
				})
			#### Tag no./item code ###
			default_items.append({
														
				'order_line_id': order_rec.id,
				'enquiry_line_id': order_rec.enquiry_line_id,
				'packing_type': packing_type,
				'description': 'Tag no./item code',
				'value': tag_no,  
				})
			#### API plan ###
			default_items.append({
														
				'order_line_id': order_rec.id,
				'enquiry_line_id': order_rec.enquiry_line_id,
				'packing_type': packing_type,
				'description': 'API plan',
				'value': api_plan,  
				})
			#### Manual Book ###
			default_items.append({
														
				'order_line_id': order_rec.id,
				'enquiry_line_id': order_rec.enquiry_line_id,
				'packing_type': packing_type,
				'description': 'Manual Book',
				'value': 1,  
				})
			value = {'order_id': order_rec.header_id.id,'order_line_id': order_rec.id,
			'pump_model_type':order_rec.pump_model_type,'line_ids':default_items}
		

		return {'value': value}
		
	def load_bom(self, cr, uid, ids, context=None):
		entry_rec = self.browse(cr,uid,ids[0])
		order_line_id = entry_rec.order_line_id.id
		value = {}
		foundry_vals = []
		ms_vals = []
		bot_vals = []
		acc_vals = []
		cr.execute(''' delete from ch_packing_foundry_details where header_id = %s ''',[entry_rec.id])
		cr.execute(''' delete from ch_packing_ms_details where header_id = %s ''',[entry_rec.id])
		cr.execute(''' delete from ch_packing_bot_details where header_id = %s ''',[entry_rec.id])
		cr.execute(''' delete from ch_packing_accessories where header_id = %s ''',[entry_rec.id])
		### Loading Foundry Items ###
		cr.execute(''' select id,pattern_name,moc_id,material_code,qty from ch_order_bom_details where flag_applicable = 't' and header_id=%s ''',[order_line_id])
		foundry_items = cr.dictfetchall()
		for foundry_item in foundry_items:
			### Checking the packed qty ###
			cr.execute(''' select sum(qty) as packed_qty from ch_packing_foundry_details 
				where order_line_id = %s and order_bom_id=%s and header_id != %s ''',[order_line_id,foundry_item['id'],entry_rec.id])
			packed_qty = cr.fetchone()
			print "packed_qty",packed_qty
			
			if packed_qty[0] != None:
				print "ssssssssssssssssssssssss"
				if packed_qty[0] < foundry_item['qty']:
					self.pool.get('ch.packing.foundry.details').create(cr,uid,{
					'header_id': entry_rec.id,
					'order_line_id':order_line_id,
					'order_bom_id':foundry_item['id'],
					'description': foundry_item['pattern_name'],
					'moc_id': foundry_item['moc_id'],
					'material_code': foundry_item['material_code'] or '',
					'total_qty': foundry_item['qty'],
					'packed_qty': packed_qty[0]
					})
			if packed_qty[0] == None:
				print "dddddddddddddddddddddddddddd"
				self.pool.get('ch.packing.foundry.details').create(cr,uid,{
				'header_id': entry_rec.id,
				'order_line_id':order_line_id,
				'order_bom_id':foundry_item['id'],
				'description': foundry_item['pattern_name'],
				'moc_id': foundry_item['moc_id'],
				'material_code': foundry_item['material_code'] or '',
				'total_qty': foundry_item['qty'],
				})
		#stop		
		### Loading MS Items ###
		cr.execute(''' select id,name,moc_id,material_code,qty from ch_order_machineshop_details where flag_applicable = 't' and header_id=%s ''',[order_line_id])
		ms_items = cr.dictfetchall()
		for ms_item in ms_items:
			### Checking the packed qty ###
			cr.execute(''' select sum(qty) as packed_qty from ch_packing_ms_details 
				where order_line_id = %s and order_bom_id=%s and header_id != %s ''',[order_line_id,ms_item['id'],entry_rec.id])
			packed_qty = cr.fetchone()
			print "packed_qty",packed_qty
			if packed_qty[0] != None:
				print "ssssssssssssssssssssssss"
				if packed_qty[0] < ms_item['qty']:
					self.pool.get('ch.packing.ms.details').create(cr,uid,{
					'header_id': entry_rec.id,
					'order_line_id':order_line_id,
					'order_bom_id':ms_item['id'],
					'description': ms_item['name'],
					'moc_id': ms_item['moc_id'],
					'material_code': ms_item['material_code'] or '',
					'total_qty': ms_item['qty'],
					'packed_qty': packed_qty[0]
					})
			if packed_qty[0] == None:
				self.pool.get('ch.packing.ms.details').create(cr,uid,{
					'header_id': entry_rec.id,
					'order_line_id':order_line_id,
					'order_bom_id':ms_item['id'],
					'description': ms_item['name'],
					'moc_id': ms_item['moc_id'],
					'material_code': ms_item['material_code'] or '',
					'total_qty': ms_item['qty'],
					})
		### Loading BOT Items ###
		cr.execute(''' select id,item_name,moc_id,material_code,qty from ch_order_bot_details where flag_applicable = 't' and header_id=%s ''',[order_line_id])
		bot_items = cr.dictfetchall()
		for bot_item in bot_items:
			
			### Checking the packed qty ###
			cr.execute(''' select sum(qty) as packed_qty from ch_packing_bot_details 
				where order_line_id = %s and order_bom_id=%s and header_id != %s ''',[order_line_id,bot_item['id'],entry_rec.id])
			packed_qty = cr.fetchone()
			print "packed_qty",packed_qty
			if packed_qty[0] != None:
				print "ssssssssssssssssssssssss"
				if packed_qty[0] < bot_item['qty']:
					self.pool.get('ch.packing.bot.details').create(cr,uid,{
					'header_id': entry_rec.id,
					'order_line_id':order_line_id,
					'order_bom_id':bot_item['id'],
					'description': bot_item['item_name'],
					'moc_id': bot_item['moc_id'],
					'material_code': bot_item['material_code'] or '',
					'total_qty': bot_item['qty'],
					'packed_qty': packed_qty[0]
					
					})
					
			if packed_qty[0] == None:
				self.pool.get('ch.packing.bot.details').create(cr,uid,{
					'header_id': entry_rec.id,
					'order_line_id':order_line_id,
					'order_bom_id':bot_item['id'],
					'description': bot_item['item_name'],
					'moc_id': bot_item['moc_id'],
					'material_code': bot_item['material_code'] or '',
					'total_qty': bot_item['qty'],
					
					})
		
		print "order_line_idorder_line_id",order_line_id
		### Loading Accessories Items ###
		cr.execute(''' select id,access_id,moc_id,qty from ch_wo_accessories where header_id=%s ''',[order_line_id])
		acc_items = cr.dictfetchall()
		for acc_item in acc_items:
			acc_id = self.pool.get('ch.packing.accessories').create(cr,uid,{
			'header_id': entry_rec.id,
			'order_line_id': order_line_id,
			'wo_access_id':acc_item['id'],
			'access_id': acc_item['access_id'],
			'moc_id': acc_item['moc_id'],
			'qty': acc_item['qty']
			})
			acc_foundry_vals = []
			acc_ms_vals = []
			acc_bot_vals = []
			### Loading Foundry Items ###
			cr.execute(''' select id,pattern_name,moc_id,material_code,qty from ch_wo_accessories_foundry where is_applicable = 't' and header_id=%s ''',[acc_item['id']])
			foundry_items = cr.dictfetchall()
			for foundry_item in foundry_items:
				### Checking the packed qty ###
				cr.execute(''' select sum(qty) as packed_qty from ch_packing_accessories_foundry 
					where order_line_id = %s and order_bom_id=%s and header_id != %s ''',[order_line_id,foundry_item['id'],entry_rec.id])
				packed_qty = cr.fetchone()
				print "packed_qty",packed_qty
				if packed_qty[0] != None:
					print "ssssssssssssssssssssssss"
					if packed_qty[0] < foundry_item['qty']:
						self.pool.get('ch.packing.accessories.foundry').create(cr,uid,{
						'header_id': acc_id,
						'order_bom_id':foundry_item['id'],
						'description': foundry_item['pattern_name'],
						'moc_id': foundry_item['moc_id'],
						'material_code': foundry_item['material_code'] or '',
						'total_qty': foundry_item['qty'],
						'packed_qty': packed_qty[0]
						})
				if packed_qty[0] == None:
					self.pool.get('ch.packing.accessories.foundry').create(cr,uid,{
						'header_id': acc_id,
						'order_bom_id':foundry_item['id'],
						'description': foundry_item['pattern_name'],
						'moc_id': foundry_item['moc_id'],
						'material_code': foundry_item['material_code'] or '',
						'total_qty': foundry_item['qty'],
						})
					
			### Loading MS Items ###
			cr.execute('''  select id,name,moc_id,material_code,qty from ch_wo_accessories_ms   where is_applicable = 't' and header_id=%s ''',[acc_item['id']])
			ms_items = cr.dictfetchall()
			for ms_item in ms_items:
				### Checking the packed qty ###
				cr.execute(''' select sum(qty) as packed_qty from ch_packing_accessories_ms
					where order_line_id = %s and order_bom_id=%s and header_id != %s ''',[order_line_id,ms_item['id'],entry_rec.id])
				packed_qty = cr.fetchone()
				print "packed_qty",packed_qty
				if packed_qty[0] != None:
					print "ssssssssssssssssssssssss"
					if packed_qty[0] < ms_item['qty']:
						self.pool.get('ch.packing.accessories.ms').create(cr,uid,{
						'header_id': acc_id,
						'order_bom_id':ms_item['id'],
						'description': ms_item['name'],
						'moc_id': ms_item['moc_id'],
						'material_code': ms_item['material_code'] or '',
						'total_qty': ms_item['qty'],
						'packed_qty': packed_qty[0]
						})
				if packed_qty[0] == None:
					self.pool.get('ch.packing.accessories.ms').create(cr,uid,{
						'header_id': acc_id,
						'order_bom_id':ms_item['id'],
						'description': ms_item['name'],
						'moc_id': ms_item['moc_id'],
						'material_code': ms_item['material_code'] or '',
						'total_qty': ms_item['qty'],
						})
			### Loading BOT Items ###
			cr.execute(''' select id,item_name,moc_id,material_code,qty from ch_wo_accessories_bot where is_applicable = 't' and header_id=%s ''',[acc_item['id']])
			bot_items = cr.dictfetchall()
			for bot_item in bot_items:
				### Checking the packed qty ###
				cr.execute(''' select sum(qty) as packed_qty from ch_packing_accessories_bot
					where order_line_id = %s and order_bom_id=%s and header_id != %s ''',[order_line_id,bot_item['id'],entry_rec.id])
				packed_qty = cr.fetchone()
				print "packed_qty",packed_qty
				
				if packed_qty[0] != None:
					print "ssssssssssssssssssssssss"
					if packed_qty[0] < bot_item['qty']:
						self.pool.get('ch.packing.accessories.bot').create(cr,uid,{
						'header_id': acc_id,
						'order_bom_id':bot_item['id'],
						'description': bot_item['item_name'],
						'moc_id': bot_item['moc_id'],
						'material_code': bot_item['material_code'] or '',
						'total_qty': bot_item['qty'],
						'packed_qty': packed_qty[0]
						})
				if packed_qty[0] == None:
					self.pool.get('ch.packing.accessories.bot').create(cr,uid,{
						'header_id': acc_id,
						'order_bom_id':bot_item['id'],
						'description': bot_item['item_name'],
						'moc_id': bot_item['moc_id'],
						'material_code': bot_item['material_code'] or '',
						'total_qty': bot_item['qty'],
						})
		return True
		
		
		
		
	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr,uid,ids,{'state':'confirm'})
		return True
		
	
	_constraints = [		
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',[''])
		
	   ]
	   
	   
	
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
		return super(kg_packing_slip, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_packing_slip, self).write(cr, uid, ids, vals, context)
		
kg_packing_slip()


class ch_packing_default_details(osv.osv):
	
	_name = "ch.packing.default.details"
	_description = "Packing Default Item details"	
	
	_columns = {
	
		'header_id':fields.many2one('kg.packing.slip', 'Packing Slip', required=1, ondelete='cascade'),
		'order_line_id': fields.related('header_id','order_line_id', type='many2one',relation='ch.work.order.details', string='WO', store=True, readonly=True),
		'enquiry_line_id': fields.integer('Enquiry Line Id'),
		'packing_type': fields.related('header_id','packing_type', type='selection',selection=[('pump','Pump'),('spare','Spare'),('access','Accessories')], string='Type', store=True, readonly=True),
		'description': fields.char('Item Description'),
		'value': fields.char('Value/Qty'),
		'flag_is_applicable': fields.boolean('Is applicable'),
		
	
	}
	
	_defaults = {
	
		'flag_is_applicable': False,
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		return context
	

ch_packing_default_details()



class ch_packing_foundry_details(osv.osv):

	_name = "ch.packing.foundry.details"
	_description = "Packing Foundry Details"
	
	_columns = {
	
		'header_id':fields.many2one('kg.packing.slip', 'Packing Slip', required=1, ondelete='cascade'),
		'order_line_id': fields.related('header_id','order_line_id', type='many2one',relation='ch.work.order.details', string='WO', store=True, readonly=True),
		'order_bom_id': fields.many2one('ch.order.bom.details','Foundry Item'),
		'description': fields.related('order_bom_id','pattern_name', type='char', string='Item Description', store=True, readonly=True),
		'moc_id': fields.related('order_bom_id','moc_id', type='many2one',relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'qty': fields.integer('Value/Qty'),
		'material_code': fields.related('order_bom_id','material_code', type='char', string='Material Code', store=True, readonly=True),
		'remarks': fields.text('Remarks'),
		'flag_is_applicable': fields.boolean('Is applicable'),
		'total_qty': fields.integer('Total Qty'),
		'packed_qty': fields.integer('Packed Qty'),
		
	
	}
	
	_defaults = {
	
		'flag_is_applicable': False,
		
	}
	
	
	def default_get(self, cr, uid, fields, context=None):
		return context
		
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.flag_is_applicable == True:
			if rec.qty <= 0.00:
				return False
			if rec.qty > rec.total_qty:
				return False
			
		return True
		
	def _check_flag_applicable(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.flag_is_applicable == False and rec.qty > 0.00:
			return False
			
		return True
	
	_constraints = [
	
		(_check_qty,'Kindly check the qty in Foundry Details !',['Qty']),
		(_check_flag_applicable,'Kindly Check Is applicable provision for qty greater than zero !',['Qty']),
		
	]
		
	
ch_packing_foundry_details()

class ch_packing_ms_details(osv.osv):

	_name = "ch.packing.ms.details"
	_description = "Packing MS Details"
	
	_columns = {
	
		'header_id':fields.many2one('kg.packing.slip', 'Packing Slip', required=1, ondelete='cascade'),
		'order_line_id': fields.related('header_id','order_line_id', type='many2one',relation='ch.work.order.details', string='WO', store=True, readonly=True),
		'order_bom_id': fields.many2one('ch.order.machineshop.details','MS Item'),
		'description': fields.related('order_bom_id','name', type='char', string='Item Description', store=True, readonly=True),
		'moc_id': fields.related('order_bom_id','moc_id', type='many2one',relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'qty': fields.integer('Value/Qty'),
		'material_code': fields.related('order_bom_id','material_code', type='char', string='Material Code', store=True, readonly=True),
		'remarks': fields.text('Remarks'),
		'flag_is_applicable': fields.boolean('Is applicable'),
		'total_qty': fields.integer('Total Qty'),
		'packed_qty': fields.integer('Packed Qty'),
		
	
	}
	
	_defaults = {
	
		'flag_is_applicable': False,
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		return context
		
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.flag_is_applicable == True:
			if rec.qty <= 0.00:
				return False
			if rec.qty > rec.total_qty:
				return False
		
		return True
		
	def _check_flag_applicable(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.flag_is_applicable == False and rec.qty > 0.00:
			return False
			
		return True
	
	_constraints = [
	
		(_check_qty,'Kindly check the qty in MS Details !',['Qty']),
		(_check_flag_applicable,'Kindly Check Is applicable provision for qty greater than zero !',['Qty']),
		
	]
		
	
ch_packing_ms_details()

class ch_packing_bot_details(osv.osv):

	_name = "ch.packing.bot.details"
	_description = "Packing Bot Details"
	
	_columns = {
	
		'header_id':fields.many2one('kg.packing.slip', 'Packing Slip', required=1, ondelete='cascade'),
		'order_line_id': fields.related('header_id','order_line_id', type='many2one',relation='ch.work.order.details', string='WO', store=True, readonly=True),
		'order_bom_id': fields.many2one('ch.order.bot.details','BOT Item'),
		'description': fields.related('order_bom_id','item_name', type='char', string='Item Description', store=True, readonly=True),
		'moc_id': fields.related('order_bom_id','moc_id', type='many2one',relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'qty': fields.integer('Value/Qty'),
		'material_code': fields.related('order_bom_id','material_code', type='char', string='Material Code', store=True, readonly=True),
		'remarks': fields.text('Remarks'),
		'flag_is_applicable': fields.boolean('Is applicable'),
		'total_qty': fields.integer('Total Qty'),
		'packed_qty': fields.integer('Packed Qty'),
		
	
	}
	
	_defaults = {
	
		'flag_is_applicable': False,
		
	}
		
	
	
	def default_get(self, cr, uid, fields, context=None):
		return context
		
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.flag_is_applicable == True:
			if rec.qty <= 0.00:
				return False
			if rec.qty > rec.total_qty:
				return False
		
		return True
		
	def _check_flag_applicable(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.flag_is_applicable == False and rec.qty > 0.00:
			return False
			
		return True
	
	_constraints = [
	
		(_check_qty,'Kindly check the qty in BOT Details !',['Qty']),
		(_check_flag_applicable,'Kindly Check Is applicable provision for qty greater than zero !',['Qty']),
		
	]
		
	
ch_packing_ms_details()

class ch_packing_accessories(osv.osv):

	_name = "ch.packing.accessories"
	_description = "Ch Packing Accessories"
	
	
	_columns = {
	
		
		'header_id':fields.many2one('kg.packing.slip', 'Header Id', ondelete='cascade'),
		'order_line_id': fields.related('header_id','order_line_id', type='many2one',relation='ch.work.order.details', string='WO', store=True, readonly=True),
		'wo_access_id':fields.many2one('ch.wo.accessories', 'WO Accessories Id'),
		'access_id': fields.related('wo_access_id','access_id', type='many2one',relation='kg.accessories.master', string='Accessories', store=True, readonly=True),
		'moc_id': fields.related('wo_access_id','moc_id', type='many2one',relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'qty': fields.related('wo_access_id','qty', type='integer', string='Qty', store=True),
		
		'line_ids': fields.one2many('ch.packing.accessories.foundry', 'header_id', 'Accessories Foundry'),
		'line_ids_a': fields.one2many('ch.packing.accessories.ms', 'header_id', 'Accessories MS'),
		'line_ids_b': fields.one2many('ch.packing.accessories.bot', 'header_id', 'Accessories BOT'),
		
		
	}
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_packing_accessories, self).create(cr, uid, vals, context=context)
	

	def default_get(self, cr, uid, fields, context=None):
		return context
	
	
		
ch_packing_accessories()


class ch_packing_accessories_foundry(osv.osv):

	_name = "ch.packing.accessories.foundry"
	_description = "Packing Accessories Foundry Details"
	
	_columns = {
	
		### Foundry Item Details ####
		'header_id':fields.many2one('ch.packing.accessories', 'Header Id', ondelete='cascade'),
		
		'order_bom_id': fields.many2one('ch.wo.accessories.foundry','Foundry Item'),
		'description': fields.related('order_bom_id','pattern_name', type='char', string='Item Description', store=True, readonly=True),
		'moc_id': fields.related('order_bom_id','moc_id', type='many2one',relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'qty': fields.integer('Value/Qty'),
		'material_code': fields.related('order_bom_id','material_code', type='char', string='Material Code', store=True, readonly=True),
		'remarks': fields.text('Remarks'),
		'flag_is_applicable': fields.boolean('Is applicable'),
		'total_qty': fields.integer('Total Qty'),
		'packed_qty': fields.integer('Packed Qty'),
		
	
	}
	
	_defaults = {
	
		'flag_is_applicable': False,
		
	}
	
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.flag_is_applicable == True:
			if rec.qty <= 0.00:
				return False
			if rec.qty > rec.total_qty:
				return False
		
		return True
		
	def _check_flag_applicable(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.flag_is_applicable == False and rec.qty > 0.00:
			return False
			
		return True
	
	_constraints = [
	
		(_check_qty,'Kindly check the qty in Foundry Details !',['Qty']),
		(_check_flag_applicable,'Kindly Check Is applicable provision for qty greater than zero !',['Qty']),
		
	]
	
ch_packing_accessories_foundry()

class ch_packing_accessories_ms(osv.osv):

	_name = "ch.packing.accessories.ms"
	_description = "packing Accessories MS"
	
	_columns = {
	
		### machineshop Item Details ####
		'header_id':fields.many2one('ch.packing.accessories', 'Header Id', ondelete='cascade'),
		
		'order_bom_id': fields.many2one('ch.wo.accessories.ms','MS Item'),
		'description': fields.related('order_bom_id','name', type='char', string='Item Description', store=True, readonly=True),
		'moc_id': fields.related('order_bom_id','moc_id', type='many2one',relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'qty': fields.integer('Value/Qty'),
		'material_code': fields.related('order_bom_id','material_code', type='char', string='Material Code', store=True, readonly=True),
		'remarks': fields.text('Remarks'),
		'flag_is_applicable': fields.boolean('Is applicable'),
		'total_qty': fields.integer('Total Qty'),
		'packed_qty': fields.integer('Packed Qty'),
		
	
	}
	
	_defaults = {
	
		'flag_is_applicable': False,
		
	}
	
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.flag_is_applicable == True:
			if rec.qty <= 0.00:
				return False
			if rec.qty > rec.total_qty:
				return False
		
		return True
		
	def _check_flag_applicable(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.flag_is_applicable == False and rec.qty > 0.00:
			return False
			
		return True
	
	_constraints = [
	
		(_check_qty,'Kindly check the qty in MS Details !',['Qty']),
		(_check_flag_applicable,'Kindly Check Is applicable provision for qty greater than zero !',['Qty']),
		
	]

ch_packing_accessories_ms()

class ch_packing_accessories_bot(osv.osv):

	_name = "ch.packing.accessories.bot"
	_description = "packing Accessories BOT"
	
	_columns = {
	
		### BOT Item Details ####
		'header_id':fields.many2one('ch.packing.accessories', 'Header Id', ondelete='cascade'),
		'order_bom_id': fields.many2one('ch.wo.accessories.bot','BOT Item'),
		'description': fields.related('order_bom_id','item_name', type='char', string='Item Description', store=True, readonly=True),
		'moc_id': fields.related('order_bom_id','moc_id', type='many2one',relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'qty': fields.integer('Value/Qty'),
		'material_code': fields.related('order_bom_id','material_code', type='char', string='Material Code', store=True, readonly=True),
		'remarks': fields.text('Remarks'),
		'flag_is_applicable': fields.boolean('Is applicable'),
		'total_qty': fields.integer('Total Qty'),
		'packed_qty': fields.integer('Packed Qty'),
		
	
	}
	
	_defaults = {
	
		'flag_is_applicable': False,
		
	}
	
	def _check_qty(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.flag_is_applicable == True:
			if rec.qty <= 0.00:
				return False
			if rec.qty > rec.total_qty:
				return False
		
		return True
		
	def _check_flag_applicable(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.flag_is_applicable == False and rec.qty > 0.00:
			return False
			
		return True
	
	_constraints = [
	
		(_check_qty,'Kindly check the qty in BOT Details !',['Qty']),
		(_check_flag_applicable,'Kindly Check Is applicable provision for qty greater than zero !',['Qty']),
		
	]
	
ch_packing_accessories_bot()


class ch_packing_checklist(osv.osv):

	_name = "ch.packing.checklist"
	_description = "Packing Check list"
	
	_columns = {
	
		### Item Details ####
		'header_id':fields.many2one('kg.packing.slip', 'Header Id', ondelete='cascade'),
		'checklist_id': fields.many2one('kg.packing.checklist','Item Description'),
		'value': fields.char('Value/Qty'),
		'remarks': fields.text('Remarks'),
		'flag_is_applicable': fields.boolean('Is applicable'),
		
	
	}
	
	_defaults = {
	
		'flag_is_applicable': False,
		
	}
	
ch_packing_checklist()
