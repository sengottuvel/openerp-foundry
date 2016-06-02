from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
from itertools import groupby

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')


class kg_pouring_log(osv.osv):

	_name = "kg.pouring.log"
	_description = "Pouring Log"
	_order = "entry_date desc"
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Pouring No.', size=128,select=True),
		'entry_date': fields.datetime('Pouring Date',required=True),
		'melting_id': fields.many2one('kg.melting','Heat No.',domain="[('active','=','t')]"),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		'line_ids':fields.one2many('ch.pouring.details', 'header_id', "Pouring Details"),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('approve','Approved')],'Status'),
		'remark': fields.text('Remarks'),
		'note': fields.text('Notes'),
		'shift_id': fields.many2one('kg.shift.master','Shift'),
		'supervisor': fields.char('Supervisor', size=128),
		'pour_close_team': fields.char('Pouring Closing Team', size=128),

		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'approve_user_id': fields.many2one('res.users', 'Approved By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),		
		
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_pouring_log', context=c),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'entry_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft'
		
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = datetime.today()
		entry_date = rec.entry_date
		entry_date = str(entry_date)
		entry_date = datetime.strptime(entry_date, '%Y-%m-%d %H:%M:%S')
		if entry_date > today:
			return False
		return True
		
	_constraints = [		
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
		
	   ]
	

	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def entry_approve(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr,uid,ids[0])
		
		for line_item in entry.line_ids:
			#### Pouring Updation When User Gives Work Order ###
			
			if line_item.order_line_id and line_item.order_line_id.id != False:
				rem_qty = line_item.qty
				cr.execute(''' select id,order_priority,qty,pour_qty from kg_production
					
					where
					pattern_id = %s and
					moc_id = %s and
					state in ('mould_com') and
					mould_state in ('done') and
					pour_state in ('pending','partial') and
					order_line_id = %s
					
					''',[line_item.production_id.pattern_id.id,entry.moc_id.id,line_item.order_line_id.id ])
				wo_production_ids = cr.dictfetchall()
				if wo_production_ids:
					for wo_produc_item in wo_production_ids:
						if wo_produc_item['pour_qty'] == None:
							pour_qty = 0
						else:
							pour_qty = wo_produc_item['pour_qty']
							
						woc_production_qty = wo_produc_item['qty'] - pour_qty
						if woc_production_qty > rem_qty:
							pouring_qty = rem_qty
						else:
							pouring_qty = woc_production_qty
						tot_pour_qty = pour_qty + pouring_qty
						if tot_pour_qty < wo_produc_item['qty']:
							pour_status = 'partial'
							status = 'mould_com'
						if tot_pour_qty == wo_produc_item['qty']:
							pour_status = 'done'
							status = 'pour_com'
							
						production_obj.write(cr, uid, [wo_produc_item['id']], 
						{
						'pour_qty': tot_pour_qty,
						'pour_heat_id': entry.melting_id.id,
						'pour_weight': line_item.weight,
						'pour_state': pour_status,
						'state':status,
						'pour_remarks':line_item.remarks
						})
						if pour_status == 'done' and status == 'pour_com':
							### Fettling Process Creation ###
							production_obj.fettling_inward_update(cr, uid, [wo_produc_item['id']])
						
						if pouring_qty > rem_qty:
							rem_qty = pouring_qty - rem_qty
						else:
							rem_qty = rem_qty - pouring_qty
							
						if rem_qty > 0:
							foundry_stock_obj = self.pool.get('kg.foundry.stock')
							foundry_stock_vals = {
							'pattern_id':line_item.production_id.pattern_id.id,
							'moc_id':entry.moc_id.id,
							'qty':rem_qty,
							'type':'IN',
							'pouring_id':entry.id,
							'pouring_line_id':line_item.id
							
							}
							foundry_stock_id = foundry_stock_obj.create(cr, uid, foundry_stock_vals)
						
			else:
			
				rem_qty = line_item.qty
				### First Priority ###
				cr.execute(''' select id,order_priority,qty,pour_qty from kg_production
						
						where
						pattern_id = %s and
						moc_id = %s and
						state in ('mould_com') and
						mould_state in ('done') and
						pour_state in ('pending','partial') and
						order_priority = '1'
						
						''',[line_item.production_id.pattern_id.id,entry.moc_id.id ])
				msnc_production_ids = cr.dictfetchall()
				if msnc_production_ids:
					for msnc_item in msnc_production_ids:
						if msnc_item['pour_qty'] == None:
							pour_qty = 0
						else:
							pour_qty = msnc_item['pour_qty']
							
						msnc_production_qty = msnc_item['qty'] - pour_qty
						if msnc_production_qty > rem_qty:
							pouring_qty = rem_qty
						else:
							pouring_qty = msnc_production_qty
						tot_pour_qty = pour_qty + pouring_qty
						if tot_pour_qty < msnc_item['qty']:
							pour_status = 'partial'
							status = 'mould_com'
						if tot_pour_qty == msnc_item['qty']:
							pour_status = 'done'
							status = 'pour_com'
							
						production_obj.write(cr, uid, [msnc_item['id']], 
						{
						'pour_qty': tot_pour_qty,
						'pour_heat_id': entry.melting_id.id,
						'pour_weight': line_item.weight,
						'pour_state': pour_status,
						'state':status,
						'pour_remarks':line_item.remarks
						})
						if pour_status == 'done' and status == 'pour_com':
							### Fettling Process Creation ###
							production_obj.fettling_inward_update(cr, uid, [msnc_item['id']])
						if pouring_qty > rem_qty:
							rem_qty = pouring_qty - rem_qty
						else:
							rem_qty = rem_qty - pouring_qty
						
				### Second Priority ###
				if rem_qty > 0:
					cr.execute(''' select id,order_priority,qty,pour_qty from kg_production
						
						where
						pattern_id = %s and
						moc_id = %s and
						state in ('mould_com') and
						mould_state in ('done') and
						pour_state in ('pending','partial') and
						order_priority = '2'
						
						''',[line_item.production_id.pattern_id.id,entry.moc_id.id ])
					nc_production_ids = cr.dictfetchall()
					if nc_production_ids:
						for nc_item in nc_production_ids:
							if nc_item['pour_qty'] == None:
								pour_qty = 0
							else:
								pour_qty = nc_item['pour_qty']
							nc_production_qty = nc_item['qty'] - pour_qty
							if nc_production_qty > rem_qty:
								pouring_qty = rem_qty
							else:
								pouring_qty = nc_production_qty
							tot_pour_qty = pour_qty + pouring_qty
							if tot_pour_qty < nc_item['qty']:
								pour_status = 'partial'
								status = 'mould_com'
							if tot_pour_qty == nc_item['qty']:
								pour_status = 'done'
								status = 'pour_com'
								
							production_obj.write(cr, uid, [nc_item['id']], 
							{
							'pour_qty': tot_pour_qty,
							'pour_heat_id': entry.melting_id.id,
							'pour_weight': line_item.weight,
							'pour_state': pour_status,
							'state':status,
							'pour_remarks':line_item.remarks
							})
							if pour_status == 'done' and status == 'pour_com':
								### Fettling Process Creation ###
								production_obj.fettling_inward_update(cr, uid, [nc_item['id']])
							if pouring_qty > rem_qty:
								rem_qty = pouring_qty - rem_qty
							else:
								rem_qty = rem_qty - pouring_qty
								
				### Third Priority ###
				if rem_qty > 0:
					cr.execute(''' select id,order_priority,qty,pour_qty from kg_production
						
						where
						pattern_id = %s and
						moc_id = %s and
						state in ('mould_com') and
						mould_state in ('done') and
						pour_state in ('pending','partial') and
						order_priority = '3'
						
						''',[line_item.production_id.pattern_id.id,entry.moc_id.id ])
					service_production_ids = cr.dictfetchall()
					if service_production_ids:
						for service_item in service_production_ids:
							if service_item['pour_qty'] == None:
								pour_qty = 0
							else:
								pour_qty = service_item['pour_qty']
							service_production_qty = service_item['qty'] - pour_qty
							if service_production_qty > rem_qty:
								pouring_qty = rem_qty
							else:
								pouring_qty = service_production_qty
							tot_pour_qty = pour_qty + pouring_qty
							if tot_pour_qty < service_item['qty']:
								pour_status = 'partial'
								status = 'mould_com'
							if tot_pour_qty == service_item['qty']:
								pour_status = 'done'
								status = 'pour_com'
								
							production_obj.write(cr, uid, [service_item['id']], 
							{
							'pour_qty': tot_pour_qty,
							'pour_heat_id': entry.melting_id.id,
							'pour_weight': line_item.weight,
							'pour_state': pour_status,
							'state':status,
							'pour_remarks':line_item.remarks
							})
							if pour_status == 'done' and status == 'pour_com':
								### Fettling Process Creation ###
								production_obj.fettling_inward_update(cr, uid, [service_item['id']])
							if pouring_qty > rem_qty:
								rem_qty = pouring_qty - rem_qty
							else:
								rem_qty = rem_qty - pouring_qty
								
				### Fourth Priority ###
				if rem_qty > 0:
					cr.execute(''' select id,order_priority,qty,pour_qty from kg_production
						
						where
						pattern_id = %s and
						moc_id = %s and
						state in ('mould_com') and
						mould_state in ('done') and
						pour_state in ('pending','partial') and
						order_priority = '4'
						
						''',[line_item.production_id.pattern_id.id,entry.moc_id.id ])
					emer_production_ids = cr.dictfetchall()
					if emer_production_ids:
						for emer_item in emer_production_ids:
							if emer_item['pour_qty'] == None:
								pour_qty = 0
							else:
								pour_qty = emer_item['pour_qty']
							print "vvvvvvvvvvvvvvvvvvv",emer_item,emer_item['pour_qty'],pour_qty
							emer_production_qty = emer_item['qty'] - pour_qty
							if emer_production_qty > rem_qty:
								pouring_qty = rem_qty
							else:
								pouring_qty = emer_production_qty
							tot_pour_qty = pour_qty + pouring_qty
							if tot_pour_qty < emer_item['qty']:
								pour_status = 'partial'
								status = 'mould_com'
							if tot_pour_qty == emer_item['qty']:
								pour_status = 'done'
								status = 'pour_com'
								
							production_obj.write(cr, uid, [emer_item['id']], 
							{
							'pour_qty': tot_pour_qty,
							'pour_heat_id': entry.melting_id.id,
							'pour_weight': line_item.weight,
							'pour_state': pour_status,
							'state':status,
							'pour_remarks':line_item.remarks
							})
							if pour_status == 'done' and status == 'pour_com':
								### Fettling Process Creation ###
								production_obj.fettling_inward_update(cr, uid, [emer_item['id']])
							if pouring_qty > rem_qty:
								rem_qty = pouring_qty - rem_qty
							else:
								rem_qty = rem_qty - pouring_qty
								
				### Fifth Priority ###
				if rem_qty > 0:
					cr.execute(''' select id,order_priority,qty,pour_qty from kg_production
						
						where
						pattern_id = %s and
						moc_id = %s and
						state in ('mould_com') and
						mould_state in ('done') and
						pour_state in ('pending','partial') and
						order_priority = '5'
						
						''',[line_item.production_id.pattern_id.id,entry.moc_id.id ])
					spare_production_ids = cr.dictfetchall()
					if spare_production_ids:
						for spare_item in spare_production_ids:
							if spare_item['pour_qty'] == None:
								pour_qty = 0
							else:
								pour_qty = spare_item['pour_qty']
							spare_production_qty = spare_item['qty'] - pour_qty
							if spare_production_qty > rem_qty:
								pouring_qty = rem_qty
							else:
								pouring_qty = spare_production_qty
							tot_pour_qty = pour_qty + pouring_qty
							if tot_pour_qty < spare_item['qty']:
								pour_status = 'partial'
								status = 'mould_com'
							if tot_pour_qty == spare_item['qty']:
								pour_status = 'done'
								status = 'pour_com'
								
							print "ggggggggggggggggggggggggggggggggggg",tot_pour_qty
								
							production_obj.write(cr, uid, [spare_item['id']], 
							{
							'pour_qty': tot_pour_qty,
							'pour_heat_id': entry.melting_id.id,
							'pour_weight': line_item.weight,
							'pour_state': pour_status,
							'state':status,
							'pour_remarks':line_item.remarks
							})
							if pour_status == 'done' and status == 'pour_com':
								### Fettling Process Creation ###
								production_obj.fettling_inward_update(cr, uid, [spare_item['id']])
							if pouring_qty > rem_qty:
								rem_qty = pouring_qty - rem_qty
							else:
								rem_qty = rem_qty - pouring_qty
								
				### Sixth Priority ###
				if rem_qty > 0:
					cr.execute(''' select id,order_priority,qty,pour_qty from kg_production
						
						where
						pattern_id = %s and
						moc_id = %s and
						state in ('mould_com') and
						mould_state in ('done') and
						pour_state in ('pending','partial') and
						order_priority = '6'
						
						''',[line_item.production_id.pattern_id.id,entry.moc_id.id ])
					normal_production_ids = cr.dictfetchall()
					if normal_production_ids:
						for normal_item in normal_production_ids:
							if normal_item['pour_qty'] == None:
								pour_qty = 0
							else:
								pour_qty = normal_item['pour_qty']
							
							normal_production_qty = normal_item['qty'] - pour_qty
							if normal_production_qty > rem_qty:
								pouring_qty = rem_qty
							else:
								pouring_qty = normal_production_qty
							tot_pour_qty = pour_qty + pouring_qty
							if tot_pour_qty < normal_item['qty']:
								pour_status = 'partial'
								status = 'mould_com'
							if tot_pour_qty == normal_item['qty']:
								pour_status = 'done'
								status = 'pour_com'
								
							production_obj.write(cr, uid, [normal_item['id']], 
							{
							'pour_qty': tot_pour_qty,
							'pour_heat_id': entry.melting_id.id,
							'pour_weight': line_item.weight,
							'pour_state': pour_status,
							'state':status,
							'pour_remarks':line_item.remarks
							})
							if pour_status == 'done' and status == 'pour_com':
								### Fettling Process Creation ###
								production_obj.fettling_inward_update(cr, uid, [normal_item['id']])
							if pouring_qty > rem_qty:
								rem_qty = pouring_qty - rem_qty
							else:
								rem_qty = rem_qty - pouring_qty
				if rem_qty > 0:
					foundry_stock_obj = self.pool.get('kg.foundry.stock')
					foundry_stock_vals = {
					'pattern_id':line_item.production_id.pattern_id.id,
					'moc_id':entry.moc_id.id,
					'qty':rem_qty,
					'type':'IN',
					'pouring_id':entry.id,
					'pouring_line_id':line_item.id
					
					}
					foundry_stock_id = foundry_stock_obj.create(cr, uid, foundry_stock_vals)
					
		### Pour Log Number ###
		pour_name = ''	
		pour_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pouring.log')])
		rec = self.pool.get('ir.sequence').browse(cr,uid,pour_seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s',now()::date) """%(pour_seq_id[0],rec.code))
		pour_name = cr.fetchone();
		self.write(cr, uid, ids, {'name': pour_name[0],'state': 'approve','approve_user_id': uid, 'approve_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_pouring_log, self).write(cr, uid, ids, vals, context)
		
		
kg_pouring_log()

class ch_pouring_details(osv.osv):
	
	_name = "ch.pouring.details"
	_description = "Pouring Log Details"
	
	
	_columns = {
			
		'header_id':fields.many2one('kg.pouring.log', 'Pouring Log', required=True, ondelete='cascade'),
		'melting_id': fields.related('header_id','melting_id', type='many2one', relation='kg.melting', string='Heat No.', store=True, readonly=True),
		'order_line_id':fields.many2one('ch.work.order.details','WO No.',domain="[('state','=','confirmed')]"),
		'moc_id': fields.related('header_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),		
		### Reference table as kg_production bcoz mould completed pattern only want to display
		'production_id': fields.many2one('kg.production','Pattern No', required=True,domain="[('state','=','mould_com'),('moc_id','=',moc_id)]"),			
		'pattern_name':fields.char('Pattern Name'),
		'qty':fields.integer('Qty'),
		'weight':fields.float('Weight(Kgs)'),
		'remarks':fields.text('Remarks'),
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		return context
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty == 0 or entry.qty < 0:
			return False
		if entry.weight < 0:
			return False 
		return True
		
		
	_constraints = [		
			  
		(_check_values, 'System not allow to save with zero and less than zero qty .!!',['Quantity,Weight(Kgs)']),
		
	   ]
	
	def onchange_pattern_name(self, cr, uid, ids, order_line_id,production_id, context=None):
		value = {'pattern_name': ''}
		pour_qty = 0
		if production_id:
			production_rec = self.pool.get('kg.production').browse(cr, uid, production_id, context=context)
			if order_line_id != False:
				if production_rec.order_line_id.id == order_line_id:
					pour_qty = production_rec.qty	
			else:
				pour_qty = 0
			value = {'qty':pour_qty,'pattern_name': production_rec.pattern_name}
		return {'value': value}
		
	def create(self, cr, uid, vals, context=None):
		production_obj = self.pool.get('kg.production')
		if vals.get('production_id'):		  
			production_rec = production_obj.browse(cr, uid, vals.get('production_id') )
			pattern_name = production_rec.pattern_name
			vals.update({'pattern_name': pattern_name})
		return super(ch_pouring_details, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		production_obj = self.pool.get('kg.production')
		if vals.get('production_id'):		  
			production_rec = production_obj.browse(cr, uid, vals.get('production_id') )
			pattern_name = production_rec.pattern_name
			vals.update({'pattern_name': pattern_name})
		return super(ch_pouring_details, self).write(cr, uid, ids, vals, context)  
		
ch_pouring_details()



