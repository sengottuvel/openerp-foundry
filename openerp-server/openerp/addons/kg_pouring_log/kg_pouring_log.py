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
		'melting_id': fields.many2one('kg.melting','Heat No.',domain="[('state','!=','draft')]"),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		'line_ids':fields.one2many('ch.pouring.details', 'header_id', "Pouring Details"),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('approve','Approved')],'Status'),
		'remark': fields.text('Remarks'),
		'note': fields.text('Notes'),
		'shift_id': fields.many2one('kg.shift.master','Shift',domain="[('state','=','approved')]"),
		'supervisor': fields.char('Supervisor', size=128),
		'pour_close_team': fields.char('Pouring Closing Team', size=128),
		
		'type': fields.selection([('pour','Pour'),('mould','Mould')],'Type'),
		
		### For Mould Update ###
		'mould_date': fields.date('Date'),
		'mould_shift_id':fields.many2one('kg.shift.master','Shift',domain="[('state','=','approved')]"),
		'mould_contractor':fields.many2one('res.partner','Contractor',domain="[('contractor','=','t'),('partner_state','=','approve')]"),
		'mould_moulder': fields.integer('Moulder'),
		#~ 'mould_box_id': fields.related('pattern_id','box_id', type='many2one', relation='kg.box.master', string='Box Size', store=True),
		'mould_helper': fields.integer('Helper'),
		'mould_operator': fields.many2one('hr.employee','Operator'),
		'mould_hardness': fields.char('Mould Hardness'),
		'mould_by': fields.selection([('comp_employee','Company Employee'),('contractor','Contractor')],'Done By'),
		'mould_pan_no':fields.char('PAN No.', size=128),
		'mould_remarks': fields.text('Remarks'),
		'line_ids_a':fields.one2many('ch.mould.details', 'header_id', "Mould Details"),
		
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
		'mould_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft'
		
		
	}
	
	def onchange_melting_id(self, cr, uid, ids, melting_id, context=None):
		value = {'moc_id': False}
		if melting_id:
			melting_rec = self.pool.get('kg.melting').browse(cr, uid, melting_id, context=context)
			value = {
			'moc_id': melting_rec.moc_id.id,
			'entry_date': melting_rec.entry_date,
			'type': 'pour'
			
			} 
		return {'value': value}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = datetime.today()
		entry_date = rec.entry_date
		entry_date = str(entry_date)
		entry_date = datetime.strptime(entry_date, '%Y-%m-%d %H:%M:%S')
		if entry_date > today:
			return False
		mould_date = rec.mould_date
		mould_date = str(mould_date)
		mould_date = datetime.strptime(mould_date, '%Y-%m-%d')
		if mould_date > today:
			return False
		return True
		
	_constraints = [		
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),
		
	   ]
	   
	def fettling_inward_update(self,cr,uid,ids,production_id,pour_id,pour_line_id,pour_qty,context=None):
		
		production_rec = self.pool.get('kg.production').browse(cr, uid, production_id)
		### Fettling Process Creation ###
		fettling_obj = self.pool.get('kg.fettling')

		### Sequence Number Generation ###
		fettling_name = ''  
		fettling_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.fettling.inward')])
		seq_rec = self.pool.get('ir.sequence').browse(cr,uid,fettling_seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(fettling_seq_id[0],seq_rec.code))
		fettling_name = cr.fetchone();
		
		if pour_qty > 0:
		
			fettling_vals = {
			'name': fettling_name[0],
			'location':production_rec.location,
			'schedule_id':production_rec.schedule_id.id,
			'schedule_date':production_rec.schedule_date,
			'schedule_line_id':production_rec.schedule_line_id.id,
			'order_bomline_id':production_rec.order_bomline_id.id,
			'order_id':production_rec.order_id.id,
			'order_line_id':production_rec.order_line_id.id,
			'order_no':production_rec.order_no,
			'order_delivery_date':production_rec.order_delivery_date,
			'order_date':production_rec.order_date,
			'order_category':production_rec.order_category,
			'order_priority':production_rec.order_priority,
			'pump_model_id':production_rec.pump_model_id.id,
			'pattern_id':production_rec.pattern_id.id,
			'pattern_code':production_rec.pattern_code,
			'pattern_name':production_rec.pattern_name,
			'moc_id':production_rec.moc_id.id,
			'schedule_qty':production_rec.schedule_qty,
			'production_id':production_rec.id,
			'pour_qty':pour_qty,
			'inward_accept_qty':pour_qty,
			'state':'waiting',
			'pour_id': pour_id,
			'pour_line_id': pour_line_id
			
			
			}
		   
			fettling_id = fettling_obj.create(cr, uid, fettling_vals)

		return True
	

	def mould_entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			for line_item in entry.line_ids_a:
				
				if line_item.order_line_id and line_item.order_line_id.id != False:
					### Checking pattern is available for that Work Order ###
					cr.execute(""" select id from kg_production
						where
						order_line_id = %s and mould_state in ('pending','partial') and mould_rem_qty > 0 
						and pattern_id = %s
						"""%(line_item.order_line_id.id,line_item.production_id.pattern_id.id))
					production_id = cr.fetchone();
					print"production_idproduction_id",production_id
					if production_id is None:
						raise osv.except_osv(_('Warning!'),
								_(' Selected Pattern %s does not assigned for WO No. %s !!')%(line_item.production_id.pattern_code,line_item.order_line_id.order_no))
					mould_qty = line_item.production_id.mould_rem_qty
					if mould_qty == 0:
						raise osv.except_osv(_('Warning!'),
								_(' There is no Mould Pending qty for pattern %s !!')%(line_item.production_id.pattern_code))
					
					#~ if line_item.qty > mould_qty:
						#~ raise osv.except_osv(_('Warning!'),
								#~ _('Mould qty should not be exceed than Mould pending qty for pattern  %s, You can mould upto %s qty !!')%(line_item.production_id.pattern_code,mould_qty))
			
				else:
					print "line_item.production_id.pattern_id.id,line_item.production_id.moc_id.id",line_item.production_id.pattern_id.id,line_item.production_id.moc_id.id
					cr.execute(""" select sum(mould_rem_qty) from kg_production
						where
						pattern_id = %s and
						moc_id = %s and
						mould_state in ('partial','pending') """%(line_item.production_id.pattern_id.id,line_item.production_id.moc_id.id))
					tot_mould_qty = cr.fetchone();
					
					if tot_mould_qty[0] == 0:
						raise osv.except_osv(_('Warning!'),
								_(' There is no Mould Pending qty for pattern %s !!')%(line_item.production_id.pattern_code))
				
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
			
	def priority_wise_updation(self,cr,uid,ids,mould_line_item,production_ids,rem_qty,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr,uid,ids[0])
		mould_done_qty = 0
		print "mould_line_item,production_ids,rem_qty",mould_line_item,production_ids,rem_qty
		for new_item in production_ids:
			print "new_item",new_item
			if rem_qty > 0:
				### Checking if there is mould pending qty ###
				if new_item['mould_rem_qty'] > 0:
					mould_done_qty = new_item['mould_rem_qty'] - rem_qty
					### Calculating mould pending qty and mould completed qty for that item ###
					if mould_done_qty <= 0:
						mould_completed_qty = new_item['mould_rem_qty']
						mould_pending_qty = 0
					if mould_done_qty > 0:
						mould_completed_qty = rem_qty
						mould_pending_qty = mould_done_qty
					### Finding the status of that item ###
					if mould_pending_qty > 0:
						mould_status = 'partial'
						produc_state = new_item['state']
					if mould_pending_qty == 0:
						mould_status = 'done'
						produc_state = 'mould_com'
						
					### Updating the values to that item ###
					production_obj.write(cr, uid, [new_item['id']], 
						{
						'mould_qty': mould_pending_qty,
						'total_mould_qty': ( new_item['total_mould_qty'] or 0 ) + mould_completed_qty,
						'mould_rem_qty': mould_pending_qty,
						'mould_state': mould_status,
						'state': produc_state,
						'mould_date': entry.mould_date,
						'mould_shift_id': entry.mould_shift_id.id,
						'mould_contractor': entry.mould_contractor.id,
						'mould_moulder': entry.mould_moulder,
						'mould_helper': entry.mould_helper,
						'mould_operator': entry.mould_operator.id,
						'mould_hardness': entry.mould_hardness,
						'mould_remarks': entry.mould_remarks,
						'mould_mc_flag': 't',
						})
						
					## Calculating rem qty for next priority wise update ##
					if mould_done_qty <= 0:
						rem_qty = rem_qty - new_item['mould_rem_qty']
					else:
						rem_qty = 0
						
		print "rem_qty",rem_qty		
		
		return rem_qty
		
	
		
	def mould_entry_approve(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'confirmed':
			rem_qty = 0
			for line_item in entry.line_ids_a:
				#### Pouring Updation When User Gives Work Order ###
				if line_item.order_line_id and line_item.order_line_id.id != False:
		
					rem_qty = line_item.qty
					
					cr.execute(''' select id,order_priority,qty,schedule_qty,pour_qty,total_mould_qty,mould_rem_qty,state from kg_production
						
						where
						pattern_id = %s and						
						mould_state in ('partial','pending') and
						order_line_id = %s
						
						''',[line_item.production_id.pattern_id.id,line_item.order_line_id.id ])
					wo_production_ids = cr.dictfetchall()
					if wo_production_ids:
						for wo_produc_item in wo_production_ids:							
							excess_tol_qty = line_item.qty + wo_produc_item['total_mould_qty']  - wo_produc_item['schedule_qty']
							print"rem_qty",rem_qty							
							print"rem_qty",excess_tol_qty							
							if rem_qty > 0:
								### Checking if there is mould pending qty ###
								if wo_produc_item['mould_rem_qty'] > 0:
									mould_done_qty = wo_produc_item['mould_rem_qty'] - rem_qty
									print "mould_done_qty",mould_done_qty
									### Calculating mould pending qty and mould completed qty for that item ###
									if mould_done_qty <= 0:
										mould_completed_qty = wo_produc_item['mould_rem_qty']
										mould_pending_qty = 0
									if mould_done_qty > 0:
										mould_completed_qty = rem_qty
										mould_pending_qty = mould_done_qty
									### Finding the status of that item ###
									if mould_pending_qty > 0:
										mould_status = 'partial'
										produc_state = wo_produc_item['state']
									if mould_pending_qty == 0:
										mould_status = 'done'
										produc_state = 'mould_com'
									print "mould_pending_qty",mould_pending_qty
									print "mould_completed_qty",mould_completed_qty
									print "wo_produc_item['total_mould_qty']",wo_produc_item['total_mould_qty']
									
									
									
									### Updating the values to that item ###
									production_obj.write(cr, uid, [wo_produc_item['id']], 
										{
										'mould_qty': mould_pending_qty,
										'total_mould_qty': (wo_produc_item['total_mould_qty'] or 0) + mould_completed_qty,
										'mould_rem_qty': mould_pending_qty,
										'mould_state': mould_status,
										'state': produc_state,
										'mould_date': entry.mould_date,
										'mould_shift_id': entry.mould_shift_id.id,
										'mould_contractor': entry.mould_contractor.id,
										'mould_moulder': entry.mould_moulder,
										'mould_helper': entry.mould_helper,
										'mould_operator': entry.mould_operator.id,
										'mould_hardness': entry.mould_hardness,
										'mould_remarks': entry.mould_remarks,
										'mould_mc_flag': 't',
										})
							
							if excess_tol_qty > 0:								
							
								
								### Production Number ###
								produc_name = ''	
								produc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.production')])
								rec = self.pool.get('ir.sequence').browse(cr,uid,produc_seq_id[0])
								cr.execute("""select generatesequenceno(%s,'%s','%s') """%(produc_seq_id[0],rec.code,entry.entry_date))
								produc_name = cr.fetchone();
								
								### Issue Number ###
								issue_name = ''	
								issue_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pattern.issue')])
								rec = self.pool.get('ir.sequence').browse(cr,uid,issue_seq_id[0])
								cr.execute("""select generatesequenceno(%s,'%s','%s') """%(issue_seq_id[0],rec.code,entry.entry_date))
								issue_name = cr.fetchone();
								
								### Core Log Number ###
								core_name = ''	
								core_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.log')])
								rec = self.pool.get('ir.sequence').browse(cr,uid,core_seq_id[0])
								cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_seq_id[0],rec.code,entry.entry_date))
								core_name = cr.fetchone();
								
								### Mould Log Number ###
								mould_name = ''	
								mould_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.log')])
								rec = self.pool.get('ir.sequence').browse(cr,uid,mould_seq_id[0])
								cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_seq_id[0],rec.code,entry.entry_date))
								mould_name = cr.fetchone();
								
								### Getting STK WO ###
								stk_wo_id = self.pool.get('kg.work.order').search(cr,uid,[('name','=','STK WO'),('flag_for_stock','=',True)])
								stk_wo_line_id = self.pool.get('ch.work.order.details').search(cr,uid,[('order_no','=','STK WO'),('flag_for_stock','=',True)])
								
								stk_wo_rec = self.pool.get('kg.work.order').browse(cr,uid,stk_wo_id[0])
								stk_wo_line_rec = self.pool.get('ch.work.order.details').browse(cr,uid,stk_wo_line_id[0])
								
								production_rec = self.pool.get('kg.production').browse(cr,uid,wo_produc_item['id'])	
								
								
								
								production_vals = {
														
									'name': produc_name[0],
									'schedule_id': production_rec.schedule_id.id,
									'schedule_date': production_rec.schedule_date,
									'division_id': production_rec.division_id.id,
									'location' : production_rec.location,
									'schedule_line_id': production_rec.schedule_line_id.id,
									'order_id': stk_wo_id[0],
									'order_line_id': stk_wo_line_id[0],
									'order_bomline_id': production_rec.order_bomline_id.id,
									'qty' : excess_tol_qty,			  
									'schedule_qty' : excess_tol_qty,			  
									'state' : 'mould_com',
									'order_category':'spare',
									'order_priority':'8',
									'pattern_id' : production_rec.pattern_id.id,
									'pattern_name' : production_rec.pattern_name,	
									'moc_id' : production_rec.moc_id.id,
									'sch_remarks': production_rec.order_bomline_id.add_spec,
									'request_state': 'done',
									'issue_no': issue_name[0],
									'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
									'issue_qty': 1,
									'issue_state': 'issued',
									'core_no': core_name[0],
									'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
									'core_qty': excess_tol_qty,
									'core_rem_qty': excess_tol_qty,
									'core_state': 'pending',
									
									'mould_no': mould_name[0],
									'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
									'mould_qty': excess_tol_qty,
									'mould_rem_qty': excess_tol_qty,
									'total_mould_qty': excess_tol_qty,
									'mould_state': 'done',
									'mould_mc_flag': 't',
									
								}
								
								
						
								production_id = production_obj.create(cr, uid, production_vals)
							
							
								### Stock Inward Creation ###
								inward_obj = self.pool.get('kg.stock.inward')
								inward_line_obj = self.pool.get('ch.stock.inward.details')
								
								inward_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.stock.inward')])
								rec = self.pool.get('ir.sequence').browse(cr,uid,inward_id[0])
								cr.execute("""select generatesequenceno(%s,'%s','%s') """%(inward_id[0],rec.code,entry.entry_date))
								inward_name = cr.fetchone();
								inward_name = inward_name[0]
								
								inward_vals = {
									'name':inward_name,
									'location': production_rec.location,
									'state': 'confirmed',
									
								}
								
								inward_id = inward_obj.create(cr, uid, inward_vals)
								
								inward_line_vals = {
									'header_id': inward_id,
									'location': production_rec.location,
									'stock_type': 'pattern',
									#~ 'pump_model_id': production_rec.pump_model_id.id,
									'pattern_id': production_rec.pattern_id.id,
									'pattern_name': production_rec.pattern_name,
									'moc_id': production_rec.moc_id.id,						
									'qty': excess_tol_qty,
									'available_qty': excess_tol_qty,
									'each_wgt': production_rec.each_weight,
									'total_weight': production_rec.total_weight,
									'stock_mode': 'excess',
									'foundry_stock_state': 'foundry_inprogress',
									'stock_item': 'foundry_item',					
									
								}
								
								inward_line_id = inward_line_obj.create(cr, uid, inward_line_vals)
							
								
				else:
					
					#### Getting all production ids for excess qty updation ###
					cr.execute(''' select id,order_priority,qty,pour_qty,total_mould_qty,mould_rem_qty,state from kg_production
							
							where
							pattern_id = %s and
							moc_id = %s and
							mould_state in ('partial','pending') and
							mould_rem_qty > 0
							order by id desc
							limit 1
							''',[line_item.production_id.pattern_id.id,line_item.production_id.moc_id.id ])
					excess_production_ids = cr.dictfetchall()
							
					rem_qty = line_item.qty
					### First Priority ###
					cr.execute(''' select id,order_priority,qty,pour_qty,total_mould_qty,mould_rem_qty,state from kg_production
							
							where
							pattern_id = %s and
							moc_id = %s and
							mould_state in ('partial','pending') and
							order_priority = '1'and
							mould_rem_qty > 0
							order by id asc
							''',[line_item.production_id.pattern_id.id,line_item.production_id.moc_id.id ])
					msnc_production_ids = cr.dictfetchall()
					if msnc_production_ids:
						rem_qty = self.priority_wise_updation(cr, uid, ids,line_item,msnc_production_ids,rem_qty)
						
							
					### Second Priority ###
					if rem_qty > 0:
						cr.execute(''' select id,order_priority,qty,pour_qty,total_mould_qty,mould_rem_qty,state from kg_production
							
							where
							pattern_id = %s and
							moc_id = %s and
							mould_state in ('partial','pending') and
							order_priority = '2' and
							mould_rem_qty > 0
							order by id asc
							''',[line_item.production_id.pattern_id.id,line_item.production_id.moc_id.id ])
						bd_production_ids = cr.dictfetchall()
						print "bd_production_ids",bd_production_ids
						
						if bd_production_ids:
							rem_qty = self.priority_wise_updation(cr, uid, ids,line_item,bd_production_ids,rem_qty)
							print "bdrem_qty",rem_qty
								
					### Third Priority ###
					if rem_qty > 0:
						cr.execute(''' select id,order_priority,pour_pending_qty as qty,pour_qty,total_mould_qty,mould_rem_qty,state from kg_production
							
							where
							pattern_id = %s and
							moc_id = %s and
							mould_state in ('partial','pending') and
							order_priority = '3' and
							mould_rem_qty > 0
							
							order by id asc
							
							''',[line_item.production_id.pattern_id.id,line_item.production_id.moc_id.id ])
						emer_production_ids = cr.dictfetchall()
						if emer_production_ids:
							rem_qty = self.priority_wise_updation(cr, uid, ids,line_item,emer_production_ids,rem_qty)
							
								
					### Fourth Priority ###
					if rem_qty > 0:
						cr.execute(''' select id,order_priority,qty,pour_qty,total_mould_qty,mould_rem_qty,state from kg_production
							
							where
							pattern_id = %s and
							moc_id = %s and
							mould_state in ('partial','pending') and
							order_priority = '4' and
							mould_rem_qty > 0
							order by id asc
							''',[line_item.production_id.pattern_id.id,line_item.production_id.moc_id.id ])
						service_production_ids = cr.dictfetchall()
						if service_production_ids:
							rem_qty = self.priority_wise_updation(cr, uid, ids,line_item,service_production_ids,rem_qty)
									
					### Fifth Priority ###
					if rem_qty > 0:
						cr.execute(''' select id,order_priority,qty,pour_qty,total_mould_qty,mould_rem_qty,state from kg_production
							
							where
							pattern_id = %s and
							moc_id = %s and
							mould_state in ('partial','pending') and
							order_priority = '5' and
							mould_rem_qty > 0
							order by id asc
							''',[line_item.production_id.pattern_id.id,line_item.production_id.moc_id.id ])
						fdync_production_ids = cr.dictfetchall()
						if fdync_production_ids:
							rem_qty = self.priority_wise_updation(cr, uid, ids,line_item,fdync_production_ids,rem_qty)
									
					### Sixth Priority ###
					
					if rem_qty > 0:
						cr.execute(''' select id,order_priority,qty,pour_qty,total_mould_qty,mould_rem_qty,state from kg_production
							
							where
							pattern_id = %s and
							moc_id = %s and
							mould_state in ('partial','pending') and
							order_priority = '6' and
							mould_rem_qty > 0
							order by id asc
							''',[line_item.production_id.pattern_id.id,line_item.production_id.moc_id.id ])
						spare_production_ids = cr.dictfetchall()
						if spare_production_ids:
							rem_qty = self.priority_wise_updation(cr, uid, ids,line_item,spare_production_ids,rem_qty)
							
					### Seventh Priority ###
					
					if rem_qty > 0:
						cr.execute(''' select id,order_priority,qty,pour_qty,total_mould_qty,mould_rem_qty,state from kg_production
							
							where
							pattern_id = %s and
							moc_id = %s and
							mould_state in ('partial','pending') and
							order_priority = '7'and
							mould_rem_qty > 0
							order by id asc
							''',[line_item.production_id.pattern_id.id,line_item.production_id.moc_id.id ])
						urgent_production_ids = cr.dictfetchall()
						if urgent_production_ids:
							rem_qty = self.priority_wise_updation(cr, uid, ids,line_item,urgent_production_ids,rem_qty)
							
					### Eighth Priority ###
					print rem_qty
					if rem_qty > 0:
						cr.execute(''' select id,order_priority,qty,pour_qty,total_mould_qty,mould_rem_qty,state from kg_production
							
							where
							pattern_id = %s and
							moc_id = %s and
							mould_state in ('partial','pending') and
							order_priority = '8' and
							mould_rem_qty > 0
							order by id asc
							''',[line_item.production_id.pattern_id.id,line_item.production_id.moc_id.id ])
						normal_production_ids = cr.dictfetchall()
						if normal_production_ids:
							rem_qty = self.priority_wise_updation(cr, uid, ids,line_item,normal_production_ids,rem_qty)
						
						### Excess qty updation ###
						print "rem_qty",rem_qty
						
						if rem_qty > 0:	
							for excess_produc_item in excess_production_ids:
								print "excess_production_ids",excess_production_ids
								production_rec = production_obj.browse(cr,uid,excess_produc_item['id'])
								
								### Production Number ###
								produc_name = ''	
								produc_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.production')])
								rec = self.pool.get('ir.sequence').browse(cr,uid,produc_seq_id[0])
								cr.execute("""select generatesequenceno(%s,'%s','%s') """%(produc_seq_id[0],rec.code,entry.entry_date))
								produc_name = cr.fetchone();
								
								### Issue Number ###
								issue_name = ''	
								issue_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pattern.issue')])
								rec = self.pool.get('ir.sequence').browse(cr,uid,issue_seq_id[0])
								cr.execute("""select generatesequenceno(%s,'%s','%s') """%(issue_seq_id[0],rec.code,entry.entry_date))
								issue_name = cr.fetchone();
								
								### Core Log Number ###
								core_name = ''	
								core_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.core.log')])
								rec = self.pool.get('ir.sequence').browse(cr,uid,core_seq_id[0])
								cr.execute("""select generatesequenceno(%s,'%s','%s') """%(core_seq_id[0],rec.code,entry.entry_date))
								core_name = cr.fetchone();
								
								### Mould Log Number ###
								mould_name = ''	
								mould_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.mould.log')])
								rec = self.pool.get('ir.sequence').browse(cr,uid,mould_seq_id[0])
								cr.execute("""select generatesequenceno(%s,'%s','%s') """%(mould_seq_id[0],rec.code,entry.entry_date))
								mould_name = cr.fetchone();
								
								### Getting STK WO ###
								stk_wo_id = self.pool.get('kg.work.order').search(cr,uid,[('name','=','STK WO'),('flag_for_stock','=',True)])
								stk_wo_line_id = self.pool.get('ch.work.order.details').search(cr,uid,[('order_no','=','STK WO'),('flag_for_stock','=',True)])
								
								stk_wo_rec = self.pool.get('kg.work.order').browse(cr,uid,stk_wo_id[0])
								stk_wo_line_rec = self.pool.get('ch.work.order.details').browse(cr,uid,stk_wo_line_id[0])
								
								
								production_vals = {
														
									'name': produc_name[0],
									'schedule_id': production_rec.schedule_id.id,
									'schedule_date': production_rec.schedule_date,
									'division_id': production_rec.division_id.id,
									'location' : production_rec.location,
									'schedule_line_id': production_rec.schedule_line_id.id,
									'order_id': stk_wo_id[0],
									'order_line_id': stk_wo_line_id[0],
									'order_bomline_id': production_rec.order_bomline_id.id,
									'qty' : rem_qty,			  
									'schedule_qty' : rem_qty,			  
									'state' : 'mould_com',
									'order_category':'spare',
									'order_priority':'8',
									'pattern_id' : production_rec.pattern_id.id,
									'pattern_name' : production_rec.pattern_name,	
									'moc_id' : production_rec.moc_id.id,
									'sch_remarks': production_rec.order_bomline_id.add_spec,
									'request_state': 'done',
									'issue_no': issue_name[0],
									'issue_date': time.strftime('%Y-%m-%d %H:%M:%S'),
									'issue_qty': 1,
									'issue_state': 'issued',
									'core_no': core_name[0],
									'core_date': time.strftime('%Y-%m-%d %H:%M:%S'),
									'core_qty': rem_qty,
									'core_rem_qty': rem_qty,
									'core_state': 'pending',
									
									'mould_no': mould_name[0],
									'mould_date': time.strftime('%Y-%m-%d %H:%M:%S'),
									'mould_qty': rem_qty,
									'mould_rem_qty': rem_qty,
									'total_mould_qty': rem_qty,
									'mould_state': 'done',
									'mould_mc_flag': 't',
									
								}
								
								
						
								production_id = production_obj.create(cr, uid, production_vals)
							
							
								### Stock Inward Creation ###
								inward_obj = self.pool.get('kg.stock.inward')
								inward_line_obj = self.pool.get('ch.stock.inward.details')
								
								inward_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.stock.inward')])
								rec = self.pool.get('ir.sequence').browse(cr,uid,inward_id[0])
								cr.execute("""select generatesequenceno(%s,'%s','%s') """%(inward_id[0],rec.code,entry.entry_date))
								inward_name = cr.fetchone();
								inward_name = inward_name[0]
								
								inward_vals = {
									'name':inward_name,
									'location': production_rec.location,
									'state': 'confirmed',
									
								}
								
								inward_id = inward_obj.create(cr, uid, inward_vals)
								
								inward_line_vals = {
									'header_id': inward_id,
									'location': production_rec.location,
									'stock_type': 'pattern',
									#~ 'pump_model_id': production_rec.pump_model_id.id,
									'pattern_id': production_rec.pattern_id.id,
									'pattern_name': production_rec.pattern_name,
									'moc_id': production_rec.moc_id.id,						
									'qty': rem_qty,
									'available_qty': rem_qty,
									'each_wgt': production_rec.each_weight,
									'total_weight': production_rec.total_weight,
									'stock_mode': 'excess',
									'foundry_stock_state': 'foundry_inprogress',
									'stock_item': 'foundry_item',					
									
								}
								
								inward_line_id = inward_line_obj.create(cr, uid, inward_line_vals)							
				
			
			self.write(cr, uid, ids, {'state': 'approve','approve_user_id': uid, 'approve_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def pour_entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			for line_item in entry.line_ids:				
				if line_item.order_line_id and line_item.order_line_id.id != False:
					pour_qty = line_item.production_id.total_mould_qty						
					if (line_item.production_id.total_mould_qty - line_item.production_id.pour_qty)  < line_item.qty:
						raise osv.except_osv(_('Warning!'),
							_('Excess Qty not allowed, Kindly check total mould qty and total pour qty !!'))						
					if pour_qty == 0:
						raise osv.except_osv(_('Warning!'),
								_(' There is no Mould completed qty for pattern %s !!')%(line_item.production_id.pattern_code))
					
					if line_item.qty > pour_qty:
						raise osv.except_osv(_('Warning!'),
								_('Pouring qty should not be exceed than Mould Qty for pattern  %s, You can pour upto %s qty !!')%(line_item.production_id.pattern_code,pour_qty))
				
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def pour_entry_approve(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'confirmed':
			rem_qty = 0
			for line_item in entry.line_ids:
				production_rec = self.pool.get('kg.production').browse(cr, uid, line_item.production_id.id)
				### Checking whether it is excess qty ###
				excess_qty = line_item.production_id.qty - (line_item.production_id.pour_qty + line_item.qty)
				
				if (production_rec.total_mould_qty - production_rec.pour_qty) < line_item.qty:
					raise osv.except_osv(_('Warning!'),
						_('Excess Qty not allowed, Kindly check total mould qty and total pour qty !!'))	
				
				else:
					
					### Fettling creation for that item ###
					self.fettling_inward_update(cr, uid, ids, production_rec.id,entry.id,line_item.id,line_item.qty)
					tot_pour_qty = production_rec.pour_qty + line_item.qty				
						
					pending_qty = production_rec.pour_pending_qty - tot_pour_qty
					if pending_qty > 0:					
						pour_status = 'partial'
						status = 'pour_pending'					
					else:
						pour_status = 'done'
						status = 'fettling_inprogress'
						
					if (production_rec.pour_qty + line_item.qty) == production_rec.total_mould_qty:
						mould_mc_flag = 'f'
					if (production_rec.pour_qty + line_item.qty) != production_rec.total_mould_qty:
						mould_mc_flag = 't'
					
					production_obj.write(cr,uid,production_rec.id,{'mould_mc_flag':mould_mc_flag,'pour_qty':tot_pour_qty,'pour_state':pour_status,'state':status,'pour_date':time.strftime('%Y-%m-%d %H:%M:%S'),})
					
			### Pour Log Number ###
			pour_name = ''  
			pour_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pouring.log')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,pour_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s',now()::date) """%(pour_seq_id[0],rec.code))
			pour_name = cr.fetchone();
			self.write(cr, uid, ids, {'state': 'approve','approve_user_id': uid, 'approve_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
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
		'production_id': fields.many2one('kg.production','Pattern No', required=True,
		 domain="[('mould_state','in',('partial','done')),('pour_state','in',('pending','partial')),('moc_id','=',moc_id),('pour_pending_qty','>',0)]"),
		'pattern_id': fields.related('production_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_state': fields.related('pattern_id','pattern_state', type='char', string='Pattern State', store=True, readonly=True),		  
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
	
	def _duplicate_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.order_line_id:
			print"order_line_id",rec.order_line_id					
			print"production_id",rec.production_id					
			print"qty",rec.qty					
			cr.execute(""" select order_line_id from ch_pouring_details where order_line_id  = '%s' and production_id = '%s' and qty = '%s' and header_id =%s """ %(rec.order_line_id.id,rec.production_id.id,rec.qty,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
		
	_constraints = [		
			  
		(_check_values, 'System not allow to save with zero and less than zero qty .!!',['Quantity,Weight(Kgs)']),
		(_duplicate_validate, 'Please Check Same Work Order,Pattern,Qty Not allowed !!!',['Pourning Details']),
		
	   ]
	
	def onchange_pattern_name(self, cr, uid, ids, order_line_id,production_id, context=None):
		value = {'pattern_name': ''}
		pour_qty = 0
		if production_id:
			production_rec = self.pool.get('kg.production').browse(cr, uid, production_id, context=context)			
			pour_qty = production_rec.total_mould_qty - production_rec.pour_qty 
			value = {'qty':pour_qty,'pattern_state':production_rec.pattern_id.pattern_state,'pattern_name': production_rec.pattern_name,'order_line_id': production_rec.order_line_id.id}
		return {'value': value}
		
	def create(self, cr, uid, vals, context=None):
		production_obj = self.pool.get('kg.production')
		print "melting_id",vals.get('production_id')
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


class ch_mould_details(osv.osv):
	
	_name = "ch.mould.details"
	_description = "Mould Log Details"
	
	
	_columns = {
			
		'header_id':fields.many2one('kg.pouring.log', 'Pouring Log', required=True, ondelete='cascade'),
		'order_line_id':fields.many2one('ch.work.order.details','WO No.',domain="[('state','=','confirmed')]"),
		### Reference table as kg_production bcoz mould completed pattern only want to display
		'production_id': fields.many2one('kg.production','Pattern No', required=True,
		 domain="[('mould_state','in',('partial','pending'))]"),		  
		'pattern_name':fields.char('Pattern Name'),
		'qty':fields.integer('Qty'),
		'weight':fields.float('Weight(Kgs)'),
		'remarks':fields.text('Remarks'),
		'flag_pattern_check': fields.boolean('Pattern Check'),
		
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
		mould_qty = 0
		pattern_name = ''
		flag_pattern_check = False
		if production_id:
			production_rec = self.pool.get('kg.production').browse(cr, uid, production_id, context=context)
			if order_line_id != False:
				if production_rec.order_line_id.id == order_line_id:
					mould_qty = production_rec.mould_rem_qty
					pattern_name = production_rec.pattern_name
					flag_pattern_check = production_rec.flag_pattern_check
			else:
				mould_qty = production_rec.mould_rem_qty
				pattern_name = production_rec.pattern_name
				flag_pattern_check = production_rec.flag_pattern_check
		else:
			mould_qty = 0
		value = {'qty':mould_qty,'pattern_name': pattern_name,'flag_pattern_check': flag_pattern_check}
		
		return {'value': value}
		
	def create(self, cr, uid, vals, context=None):
		production_obj = self.pool.get('kg.production')
		if vals.get('production_id'):		
			production_rec = production_obj.browse(cr, uid, vals.get('production_id') )
			pattern_name = production_rec.pattern_name
			vals.update({'pattern_name': pattern_name})
		return super(ch_mould_details, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		production_obj = self.pool.get('kg.production')
		if vals.get('production_id'):		
			production_rec = production_obj.browse(cr, uid, vals.get('production_id') )
			pattern_name = production_rec.pattern_name
			vals.update({'pattern_name': pattern_name})
		return super(ch_mould_details, self).write(cr, uid, ids, vals, context)  
		
ch_mould_details()



