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
	
	def onchange_melting_id(self, cr, uid, ids, melting_id, context=None):
		value = {'moc_id': False}
		if melting_id:
			melting_rec = self.pool.get('kg.melting').browse(cr, uid, melting_id, context=context)
			value = {
			'moc_id': melting_rec.moc_id.id,
			'entry_date': melting_rec.entry_date,
			
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
	

	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			for line_item in entry.line_ids:
				
				if line_item.order_line_id and line_item.order_line_id.id != False:
					pour_qty = line_item.production_id.total_mould_qty - line_item.production_id.pour_qty
					
					if pour_qty == 0:
						raise osv.except_osv(_('Warning!'),
								_(' There is no Mould completed qty for pattern %s !!')%(line_item.production_id.pattern_code))
					
					if line_item.qty > pour_qty:
						raise osv.except_osv(_('Warning!'),
								_('Pouring qty should not be exceed than Mould Qty for pattern  %s, You can pour upto %s qty !!')%(line_item.production_id.pattern_code,pour_qty))
			
				else:
					print "line_item.production_id.pattern_id.id,line_item.production_id.moc_id.id",line_item.production_id.pattern_id.id,line_item.production_id.moc_id.id
					cr.execute(""" select sum((total_mould_qty - pour_qty)) from kg_production
						where
						pattern_id = %s and
						moc_id = %s and
						mould_state in ('partial','done') and
						pour_state in ('pending','partial') """%(line_item.production_id.pattern_id.id,line_item.production_id.moc_id.id))
					tot_mould_qty = cr.fetchone();
					
					if line_item.qty > tot_mould_qty[0]:
						raise osv.except_osv(_('Warning!'),
								_('Pouring qty should not be exceed than Mould Qty for pattern  %s, You can pour upto %s qty !!')%(line_item.production_id.pattern_code,tot_mould_qty[0]))
				
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
			
	def priority_wise_updation(self,cr,uid,ids,line_item,new_production_ids,old_item,rem_qty,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr,uid,ids[0])
		
		for new_item in new_production_ids:
			
			if rem_qty > 0 and new_item['qty'] > 0:
				print "old_item",old_item
				print "new_item['id']",new_item['id']
				
				if old_item == new_item['id']:
					new_item_rec = production_obj.browse(cr, uid, new_item['id'])
					old_item_rec = production_obj.browse(cr, uid, old_item)
					if new_item_rec.pour_qty < new_item_rec.qty:
						
						print "sssssssssssssssssssss_rem_qty",rem_qty
						print "sssssssssssssssssssss_new_item['qty']",new_item['qty']
						print "sssssssssssssssssssss_new_item['pour_qty']",new_item['pour_qty']
						if new_item['pour_qty'] == None:
							pour_qty = 0
						else:
							pour_qty = new_item['pour_qty']
						print "sssssssssssssssssssss_pour_qty",pour_qty
						new_production_qty = new_item['total_mould_qty'] - pour_qty
						print "sssssssssssssssssssss_new_production_qty",new_production_qty
						if new_production_qty > rem_qty:
							pouring_qty = rem_qty
						else:
							pouring_qty = new_production_qty
							
						print "sssssssssssssssssssss_pouring_qty",pouring_qty
						tot_pour_qty = pour_qty + pouring_qty
						print "sssssssssssssssssssss_tot_pour_qty",tot_pour_qty
						
						if new_item['mould_rem_qty'] > 0:
							pour_status = 'partial'
							status = 'issue_done'
						if new_item['mould_rem_qty'] == 0:
						
							if tot_pour_qty < new_item['total_mould_qty']:
								pour_status = 'partial'
								status = 'mould_com'
							if tot_pour_qty == new_item['total_mould_qty']:
								pour_status = 'done'
								status = 'fettling_inprogress'
						print "pour_status",pour_status
						print "status",status
						
						if pour_status in ('partial','done') and status in ('mould_com','fettling_inprogress','issue_done'):
							if pour_status == 'partial':
								production_status = 'pour_pending'
							if pour_status == 'done':
								production_status = 'fettling_inprogress' 
							### Fettling Process Creation ###
							#~ production_obj.fettling_inward_update(cr, uid, [new_item['id']])
							
							real_poured_qty = new_item['qty'] - pour_qty
							if real_poured_qty > rem_qty:
								real_poured_qty = rem_qty
							else:
								real_poured_qty = real_poured_qty
							print "real_poured_qty",real_poured_qty
							
							if real_poured_qty > 0:
								self.fettling_inward_update(cr, uid, ids, new_item['id'],entry.id,line_item.id,real_poured_qty)
								production_obj.write(cr, uid, [new_item['id']], {'state': production_status})
								
						production_obj.write(cr, uid, [new_item['id']], 
						{
						'pour_qty': real_poured_qty + pour_qty,
						'pour_heat_id': entry.melting_id.id,
						'pour_weight': line_item.weight,
						'pour_state': pour_status,
						'state':status,
						'pour_remarks':line_item.remarks,
						'pour_date':entry.entry_date
						})
						
						print "aaaaaaaaaaaaaaaaaaaaaaaaaa",tot_pour_qty
						print "aaaaaaaaaaaaaaaaaaaaaaaaaa",new_item_rec.qty
						if tot_pour_qty > new_item_rec.qty:
							poured_qty = real_poured_qty
						else:
							poured_qty = pouring_qty
						
					else:
						poured_qty = 0
				
				
				if old_item != new_item['id']:
					
					new_item_rec = production_obj.browse(cr, uid, new_item['id'])
					old_item_rec = production_obj.browse(cr, uid, old_item)
					
					### Changes in New Item ###
					
					### Changes in Core Qty and its Status ###
					
					#### Finding the poured Qty ###
					print "rem_qty---------------------------------------",rem_qty
					print "new_item_rec.pour_qty---------------------------------------",new_item_rec.pour_qty
					print "new_item_rec.pour_pending_qty---------------------------------------",new_item_rec.pour_pending_qty
					if rem_qty < new_item_rec.pour_pending_qty:
						poured_qty = rem_qty
					elif rem_qty >= new_item_rec.pour_pending_qty:
						poured_qty = new_item_rec.pour_pending_qty
					
					print "poured_qty---------------------------------------",poured_qty
					
					if poured_qty > 0:
						if new_item_rec.total_core_qty < new_item_rec.qty and new_item_rec.core_state != 'done':
							new_core_qty = new_item_rec.core_qty - poured_qty
							new_total_core_qty = new_item_rec.total_core_qty + poured_qty
							new_core_rem_qty = new_item_rec.qty - new_total_core_qty

							if new_core_rem_qty < 0:
								new_core_rem_qty = 0
							else:
								new_core_rem_qty = new_core_rem_qty
								
							if new_total_core_qty >= new_item_rec.qty:
								new_core_state = 'done'
							if new_total_core_qty < new_item_rec.qty:
								new_core_state = 'partial'
							if new_total_core_qty == 0:
								new_core_state = 'pending'
						
						
						if new_item_rec.total_core_qty >= new_item_rec.qty and new_item_rec.core_state == 'done':
							new_core_qty = new_item_rec.core_qty
							new_total_core_qty = new_item_rec.total_core_qty
							new_core_rem_qty = new_item_rec.core_rem_qty
							new_core_state =  new_item_rec.core_state
						
						### Changes in Mould Qty and its Status ###
						
						if new_item_rec.total_mould_qty < new_item_rec.qty and new_item_rec.mould_state != 'done':
							new_mould_qty = new_item_rec.mould_qty - poured_qty
							new_total_mould_qty = new_item_rec.total_mould_qty + poured_qty
							new_mould_rem_qty = new_item_rec.qty - new_total_mould_qty

							if new_mould_rem_qty < 0:
								new_mould_rem_qty = 0
							else:
								new_mould_rem_qty = new_mould_rem_qty
								
							if new_total_mould_qty >= new_item_rec.qty:
								new_mould_state = 'done'
							if new_total_mould_qty < new_item_rec.qty:
								new_mould_state = 'partial'
							if new_total_mould_qty == 0:
								new_mould_state = 'pending'
								
						if new_item_rec.total_mould_qty >= new_item_rec.qty and new_item_rec.mould_state == 'done':
							new_mould_qty = new_item_rec.mould_qty
							new_total_mould_qty = new_item_rec.total_mould_qty
							new_mould_rem_qty = new_item_rec.mould_rem_qty
							new_mould_state =  new_item_rec.mould_state
							
						### Changes in Pour Qty and its Status ###
						print "new_item_rec.pour_qty",new_item_rec.pour_qty
						print "new_total_mould_qty",new_total_mould_qty
						print "new_mould_rem_qty",new_mould_rem_qty
						print "new_item_rec.pour_state",new_item_rec.pour_state
						if new_item_rec.pour_qty < (new_total_mould_qty + new_mould_rem_qty)  and new_item_rec.pour_state != 'done':
							
							new_pour_qty = new_item_rec.pour_qty + poured_qty
							new_pour_pending_qty = new_item_rec.pour_pending_qty - poured_qty
							print "new_pour_qty",new_pour_qty
							print "(new_total_mould_qty + new_mould_rem_qty)",(new_total_mould_qty + new_mould_rem_qty)
							if new_pour_qty == (new_total_mould_qty + new_mould_rem_qty):
								new_pour_state = 'done'
							if new_pour_qty < (new_total_mould_qty + new_mould_rem_qty):
								new_pour_state = 'partial'
							if new_pour_qty == 0:
								new_pour_state = 'pending'
								
						if new_item_rec.pour_qty == (new_total_mould_qty + new_mould_rem_qty) and new_item_rec.pour_state == 'done':
							new_pour_qty = new_item_rec.pour_qty
							new_pour_pending_qty = new_item_rec.pour_pending_qty
							new_pour_state = new_item_rec.pour_state
					
						### Production Status Updation ###
						if new_pour_state in ('partial','pending'):
							new_production_status = 'pour_pending'
						if new_pour_state == 'done':
							new_production_status = 'fettling_inprogress'
						print "new_pour_state",new_pour_state
						
						new_production_vals = {
							'core_qty': new_core_qty,
							'total_core_qty': new_total_core_qty,
							'core_rem_qty': new_core_rem_qty,
							'core_state': new_core_state,
							'mould_qty':new_mould_rem_qty,
							'total_mould_qty':new_total_mould_qty,
							'mould_rem_qty': new_mould_rem_qty,
							'mould_state':new_mould_state,
							'pour_qty':new_pour_qty,
							'pour_pending_qty':new_pour_pending_qty,
							'pour_state':new_pour_state,
							'state':new_production_status,
							
							
							}
							
						print "new_production_vals",new_production_vals
						
						
						   
						production_obj.write(cr, uid, [new_item['id']], 
							{
							'core_qty': new_core_qty,
							'total_core_qty': new_total_core_qty,
							'core_rem_qty': new_core_rem_qty,
							'core_state': new_core_state,
							'mould_qty':new_mould_rem_qty, 
							'total_mould_qty':new_total_mould_qty,
							'mould_rem_qty': new_mould_rem_qty,
							'mould_state':new_mould_state,
							'pour_qty':new_pour_qty,
							'pour_pending_qty':new_pour_pending_qty,
							'pour_state':new_pour_state,
							'state':new_production_status,
							
							
							})
							
						### Fettling Inward Creation for Poured Qty ###
						if poured_qty > 0:
							self.fettling_inward_update(cr, uid, ids, new_item['id'],entry.id,line_item.id,poured_qty)
							
						
						### Changes in Old Item ###
						
						### Changes in Core Qty and its Status ###
						
						
						
						old_total_core_qty = old_item_rec.total_core_qty - poured_qty
						if old_total_core_qty >= 0:
							old_total_core_qty = old_total_core_qty
						else:
							old_total_core_qty = 0
						old_core_rem_qty = old_item_rec.qty - old_total_core_qty

						if old_core_rem_qty < 0:
							old_core_rem_qty = 0
						else:
							old_core_rem_qty = old_core_rem_qty
							
						if old_total_core_qty >= old_item_rec.qty:
							old_core_state = 'done'
						if old_total_core_qty < old_item_rec.qty:
							old_core_state = 'partial'
						if old_total_core_qty == 0:
							old_core_state = 'pending'
							
						
						### Changes in Mould Qty and its Status ###
						
						
						old_total_mould_qty = old_item_rec.total_mould_qty - poured_qty
						old_mould_rem_qty = old_item_rec.qty - old_total_mould_qty
					
						
						if old_mould_rem_qty < 0:
							old_mould_rem_qty = 0
						else:
							old_mould_rem_qty = old_mould_rem_qty
							
						if old_total_mould_qty >= old_item_rec.qty:
							old_mould_state = 'done'
						if old_total_mould_qty < old_item_rec.qty:
							old_mould_state = 'partial'
						if old_total_mould_qty == 0:
							old_mould_state = 'pending'
						
					

						### Changes in Pour Qty and its Status ###
						
						
						if old_item_rec.pour_qty == 0:
							old_pour_qty = 0
						else:
							old_pour_qty = old_item_rec.pour_qty - rem_qty
						
						old_pour_pending_qty = old_item_rec.pour_pending_qty - old_pour_qty
						
						if old_pour_qty == (old_total_mould_qty + old_mould_rem_qty):
							old_pour_state = 'done'
						if old_pour_qty < (old_total_mould_qty + old_mould_rem_qty):
							old_pour_state = 'partial'
						if old_pour_qty == 0:
							old_pour_state = 'pending'
						
						
						### Production Status Updation ###
						if old_pour_state == 'pending':
							if old_mould_state == 'done':
								old_production_status = 'pour_pending'
							else:
								old_production_status = 'issue_done'
						if old_pour_state == 'partial':
							old_production_status = 'pour_pending'
						if old_pour_state == 'done':
							old_production_status = 'fettling_inprogress'
						
						allocated_wo = ''   
						
						if old_item_rec.allocated_wo == False:
							allocated_wo = new_item_rec.order_no+'('+str(poured_qty)+')'
						else:
							allocated_wo = old_item_rec.allocated_wo + ',' +new_item_rec.order_no+'('+str(poured_qty)+')'
						
						
						old_pppp = {
							'core_qty': old_core_rem_qty,
							'total_core_qty': old_total_core_qty,
							'core_rem_qty': old_core_rem_qty,
							'core_state': old_core_state,
							'mould_qty':old_mould_rem_qty,
							'total_mould_qty':old_total_mould_qty,
							'mould_rem_qty': old_mould_rem_qty,
							'mould_state':old_mould_state,
							'pour_qty':old_pour_qty,
							'pour_pending_qty':old_pour_pending_qty,
							'pour_state':old_pour_state,
							'state':old_production_status,
							'allocated_wo': allocated_wo
							
						}
							
						print "old_pppp",old_pppp
						
						production_obj.write(cr, uid, [old_item], 
							{
							'core_qty': old_core_rem_qty,
							'total_core_qty': old_total_core_qty,
							'core_rem_qty': old_core_rem_qty,
							'core_state': old_core_state,
							'mould_qty':old_mould_rem_qty,
							'total_mould_qty':old_total_mould_qty,
							'mould_rem_qty': old_mould_rem_qty,
							'mould_state':old_mould_state,
							'pour_qty':old_pour_qty,
							'pour_pending_qty':old_pour_pending_qty,
							'pour_state':old_pour_state,
							'state':old_production_status,
							'allocated_wo': allocated_wo
							
							})
					
				print "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",rem_qty
				print "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",poured_qty
				rem_qty = rem_qty - poured_qty  
			
			
			
			
		return rem_qty
		
	
		
	def entry_approve(self,cr,uid,ids,context=None):
		production_obj = self.pool.get('kg.production')
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'confirmed':
			rem_qty = 0
			for line_item in entry.line_ids:
				#### Pouring Updation When User Gives Work Order ###
				if line_item.order_line_id and line_item.order_line_id.id != False:
		
					rem_qty = line_item.qty
					
					cr.execute(''' select id,order_priority,qty,pour_qty,total_mould_qty,mould_rem_qty from kg_production
						
						where
						pattern_id = %s and
						moc_id = %s and
						mould_state in ('partial','done') and
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
								
							woc_production_qty = wo_produc_item['total_mould_qty'] - pour_qty
							
							if woc_production_qty > rem_qty:
								pouring_qty = rem_qty
							else:
								pouring_qty = woc_production_qty
							
							tot_pour_qty = pour_qty + pouring_qty
							
							
							if wo_produc_item['mould_rem_qty'] > 0:
								pour_status = 'partial'
								status = 'issue_done'
							if wo_produc_item['mould_rem_qty'] == 0:
								if tot_pour_qty < wo_produc_item['total_mould_qty']:
									pour_status = 'partial'
									status = 'mould_com'
								if tot_pour_qty == wo_produc_item['total_mould_qty']:
									pour_status = 'done'
									status = 'fettling_inprogress'
							
							
							if pour_status in ('partial','done') and status in ('mould_com','fettling_inprogress','issue_done'):
								if pour_status == 'partial':
									production_status = 'pour_pending'
								if pour_status == 'done':
									production_status = 'fettling_inprogress' 
								### Fettling Process Creation ###
								real_poured_qty = wo_produc_item['qty'] - pour_qty
								if real_poured_qty > rem_qty:
									real_poured_qty = rem_qty
								else:
									real_poured_qty = real_poured_qty
								
								self.fettling_inward_update(cr, uid, ids, wo_produc_item['id'],entry.id,line_item.id,real_poured_qty)
								production_obj.write(cr, uid, [wo_produc_item['id']], {'state': production_status})
							
							
							production_obj.write(cr, uid, [wo_produc_item['id']], 
							{
							'pour_qty': real_poured_qty + pour_qty,
							'pour_heat_id': entry.melting_id.id,
							'pour_weight': line_item.weight,
							'pour_state': pour_status,
							'state':status,
							'pour_remarks':line_item.remarks,
							'pour_date':entry.entry_date,
							})
							
							if real_poured_qty > rem_qty:
								rem_qty = real_poured_qty - rem_qty
							else:
								rem_qty = rem_qty - real_poured_qty
							
							if rem_qty > 0:
								
								### Excess Qty Updation ###
								
								
								production_rec = self.pool.get('kg.production').browse(cr, uid, line_item.production_id.id)
								### Fettling Process Creation ###
								fettling_obj = self.pool.get('kg.fettling')

								### Sequence Number Generation ###
								fettling_name = ''  
								fettling_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.fettling.inward')])
								seq_rec = self.pool.get('ir.sequence').browse(cr,uid,fettling_seq_id[0])
								cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(fettling_seq_id[0],seq_rec.code))
								fettling_name = cr.fetchone();
								
								### Getting STK WO ###
								stk_wo_id = self.pool.get('kg.work.order').search(cr,uid,[('name','=','STK WO'),('flag_for_stock','=',True)])
								stk_wo_line_id = self.pool.get('ch.work.order.details').search(cr,uid,[('order_no','=','STK WO'),('flag_for_stock','=',True)])
								
								stk_wo_rec = self.pool.get('kg.work.order').browse(cr,uid,stk_wo_id[0])
								stk_wo_line_rec = self.pool.get('ch.work.order.details').browse(cr,uid,stk_wo_line_id[0])
								
								fettling_vals = {
									'name': fettling_name[0],
									'location':production_rec.location,
									'schedule_id':production_rec.schedule_id.id,
									'schedule_date':production_rec.schedule_date,
									'schedule_line_id':production_rec.schedule_line_id.id,
									'order_id': stk_wo_id[0],
									'order_line_id': stk_wo_line_id[0],
									'order_no': 'STK WO',
									'order_category': 'spare',
									'order_priority': '6',
									'pump_model_id':stk_wo_line_rec.pump_model_id.id,
									'pattern_id':production_rec.pattern_id.id,
									'pattern_code':production_rec.pattern_code,
									'pattern_name':production_rec.pattern_name,
									'moc_id':production_rec.moc_id.id,
									'schedule_qty':rem_qty,
									'production_id':production_rec.id,
									'pour_qty':rem_qty,
									'inward_accept_qty':rem_qty,
									'state':'waiting',
									'pour_id': entry.id,
									'pour_line_id': line_item.id
									
									
								}
									
								fettling_id = fettling_obj.create(cr, uid, fettling_vals)
								
								tot_pour_qty = production_rec.pour_qty + rem_qty
								if tot_pour_qty < production_rec.total_mould_qty:
									pour_status = 'partial'
									status = 'mould_com'
								if tot_pour_qty == production_rec.total_mould_qty:
									pour_status = 'done'
									status = 'fettling_inprogress'

								production_obj.write(cr,uid,production_rec.id,{'pour_qty':tot_pour_qty,'pour_state':pour_status,'state':status})
								
								### Stock Inward Creation ###
								inward_obj = self.pool.get('kg.stock.inward')
								inward_line_obj = self.pool.get('ch.stock.inward.details')
								
								inward_vals = {
									'location': production_rec.location
								}
								
								inward_id = inward_obj.create(cr, uid, inward_vals)
								
								inward_line_vals = {
									'header_id': inward_id,
									'location': production_rec.location,
									'stock_type': 'pattern',
									'pump_model_id': production_rec.pump_model_id.id,
									'pattern_id': production_rec.pattern_id.id,
									'pattern_name': production_rec.pattern_name,
									'moc_id': production_rec.moc_id.id,
									#~ 'stage_id': production_rec.stage_id.id,
									'qty': rem_qty,
									'available_qty': rem_qty,
									'each_wgt': production_rec.each_weight,
									'total_weight': production_rec.total_weight,
									'stock_mode': 'excess',
									'foundry_stock_state': 'foundry_inprogress',
									'stock_item': 'foundry_item',
									'fettling_id': fettling_id,
									'heat_no': entry.melting_id.name
								}
								
								inward_line_id = inward_line_obj.create(cr, uid, inward_line_vals)
							
				
				else:
					
					#### Finding the OLD WO ###
					cr.execute(""" select id,(total_mould_qty - pour_qty) as total_mould_qty from kg_production
						where
						pattern_id = %s and
						moc_id = %s and
						mould_state in ('partial','done') and
						pour_state in ('pending','partial') order by id asc """%(line_item.production_id.pattern_id.id,line_item.production_id.moc_id.id))
					old_sch_list = cr.dictfetchall();
					
					print "old_sch_list",old_sch_list
					
					rem_pour_qty = line_item.qty
					
					print "rem_pour_qty",rem_pour_qty
					
					for old_item in old_sch_list:
					
						if rem_pour_qty > 0:
						
							if old_item['total_mould_qty'] < rem_pour_qty:
								rem_qty = old_item['total_mould_qty']
							if old_item['total_mould_qty'] >= rem_pour_qty:
								rem_qty = rem_pour_qty
							if rem_pour_qty == 0:
								rem_qty = old_item['total_mould_qty']
							
							
							### First Priority ###
							cr.execute(''' select id,order_priority,qty,pour_qty,total_mould_qty,mould_rem_qty from kg_production
									
									where
									pattern_id = %s and
									moc_id = %s and
									pour_state in ('pending','partial') and
									order_priority = '1'and
									pour_pending_qty > 0
									order by id asc
									''',[line_item.production_id.pattern_id.id,entry.moc_id.id ])
							msnc_production_ids = cr.dictfetchall()
							if msnc_production_ids:
								rem_qty = self.priority_wise_updation(cr, uid, ids,line_item,msnc_production_ids,old_item['id'],rem_qty)
								
									
							### Second Priority ###
							if rem_qty > 0:
								cr.execute(''' select id,order_priority,qty,pour_qty,total_mould_qty,mould_rem_qty from kg_production
									
									where
									pattern_id = %s and
									moc_id = %s and
								   
									pour_state in ('pending','partial') and
									order_priority = '2'and
									pour_pending_qty > 0
									order by id asc
									''',[line_item.production_id.pattern_id.id,entry.moc_id.id ])
								nc_production_ids = cr.dictfetchall()
								if nc_production_ids:
									rem_qty = self.priority_wise_updation(cr, uid, ids,line_item,nc_production_ids,old_item['id'],rem_qty)
											
							### Third Priority ###
							if rem_qty > 0:
								cr.execute(''' select id,order_priority,pour_pending_qty as qty,pour_qty,total_mould_qty,mould_rem_qty from kg_production
									
									where
									pattern_id = %s and
									moc_id = %s and
								   
									pour_state in ('pending','partial') and
									order_priority = '3' and
									pour_pending_qty > 0
									
									order by id asc
									
									''',[line_item.production_id.pattern_id.id,entry.moc_id.id ])
								service_production_ids = cr.dictfetchall()
								if service_production_ids:
									rem_qty = self.priority_wise_updation(cr, uid, ids,line_item,service_production_ids,old_item['id'],rem_qty)
									
									
									
										
							### Fourth Priority ###
							if rem_qty > 0:
								cr.execute(''' select id,order_priority,qty,pour_qty,total_mould_qty,mould_rem_qty from kg_production
									
									where
									pattern_id = %s and
									moc_id = %s and
								   
									pour_state in ('pending','partial') and
									order_priority = '4'and
									pour_pending_qty > 0
									order by id asc
									''',[line_item.production_id.pattern_id.id,entry.moc_id.id ])
								emer_production_ids = cr.dictfetchall()
								if emer_production_ids:
									rem_qty = self.priority_wise_updation(cr, uid, ids,line_item,emer_production_ids,old_item['id'],rem_qty)
											
							### Fifth Priority ###
							if rem_qty > 0:
								cr.execute(''' select id,order_priority,qty,pour_qty,total_mould_qty,mould_rem_qty from kg_production
									
									where
									pattern_id = %s and
									moc_id = %s and
								   
									pour_state in ('pending','partial') and
									order_priority = '5'and
									pour_pending_qty > 0
									order by id asc
									''',[line_item.production_id.pattern_id.id,entry.moc_id.id ])
								spare_production_ids = cr.dictfetchall()
								if spare_production_ids:
									rem_qty = self.priority_wise_updation(cr, uid, ids,line_item,spare_production_ids,old_item['id'],rem_qty)
											
							### Sixth Priority ###
							
							if rem_qty > 0:
								cr.execute(''' select id,order_priority,qty,pour_qty,total_mould_qty,mould_rem_qty from kg_production
									
									where
									pattern_id = %s and
									moc_id = %s and
									
									pour_state in ('pending','partial') and
									order_priority = '6'and
									pour_pending_qty > 0
									order by id asc
									''',[line_item.production_id.pattern_id.id,entry.moc_id.id ])
								normal_production_ids = cr.dictfetchall()
								if normal_production_ids:
									rem_qty = self.priority_wise_updation(cr, uid, ids,line_item,normal_production_ids,old_item['id'],rem_qty)
							
							
							rem_pour_qty = rem_pour_qty - old_item['total_mould_qty']
					
					
					if rem_qty == 0:
						rem_qty = rem_pour_qty
					else:
						rem_qty = rem_qty
					print "rem_qtyrem_qtyrem_qtyrem_qtyrem_qtyrem_qtyrem_qtyrem_qtyrem_qty",rem_qty
					
					production_rec = self.pool.get('kg.production').browse(cr, uid, line_item.production_id.id)
					print "qty",production_rec.qty
					print "total_mould_qty",production_rec.total_mould_qty
					print "pour_qty",production_rec.pour_qty
					print "pour_pending_qty",production_rec.pour_pending_qty
					print "pour_state",production_rec.pour_state
					print "state",production_rec.state
					
					if rem_qty > 0 :
						
						### Excess Qty Updation ###
								
						
						production_rec = self.pool.get('kg.production').browse(cr, uid, line_item.production_id.id)
						### Fettling Process Creation ###
						fettling_obj = self.pool.get('kg.fettling')

						### Sequence Number Generation ###
						fettling_name = ''  
						fettling_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.fettling.inward')])
						seq_rec = self.pool.get('ir.sequence').browse(cr,uid,fettling_seq_id[0])
						cr.execute("""select generatesequenceno(%s,'%s', now()::date ) """%(fettling_seq_id[0],seq_rec.code))
						fettling_name = cr.fetchone();
						
						### Getting STK WO ###
						stk_wo_id = self.pool.get('kg.work.order').search(cr,uid,[('name','=','STK WO'),('flag_for_stock','=',True)])
						stk_wo_line_id = self.pool.get('ch.work.order.details').search(cr,uid,[('order_no','=','STK WO'),('flag_for_stock','=',True)])
						
						stk_wo_rec = self.pool.get('kg.work.order').browse(cr,uid,stk_wo_id[0])
						stk_wo_line_rec = self.pool.get('ch.work.order.details').browse(cr,uid,stk_wo_line_id[0])
						
						
						fettling_vals = {
							'name': fettling_name[0],
							'location':production_rec.location,
							'schedule_id':production_rec.schedule_id.id,
							'schedule_date':production_rec.schedule_date,
							'schedule_line_id':production_rec.schedule_line_id.id,
							'order_id': stk_wo_id[0],
							'order_line_id': stk_wo_line_id[0],
							'order_no': 'STK WO',
							'order_category': 'spare',
							'order_priority': '6',
							'pump_model_id':stk_wo_line_rec.pump_model_id.id,
							'pattern_id':production_rec.pattern_id.id,
							'pattern_code':production_rec.pattern_code,
							'pattern_name':production_rec.pattern_name,
							'moc_id':production_rec.moc_id.id,
							'schedule_qty':rem_qty,
							'production_id':production_rec.id,
							'pour_qty':rem_qty,
							'inward_accept_qty':rem_qty,
							'state':'waiting',
							'pour_id': entry.id,
							'pour_line_id': line_item.id
							
							
						}
							
						fettling_id = fettling_obj.create(cr, uid, fettling_vals)
						tot_pour_qty = production_rec.pour_qty + rem_qty
						print "production_rec.pour_qty",production_rec.pour_qty
						print "rem_qty",rem_qty
						print "tot_pour_qty",tot_pour_qty
						print "production_rec.total_mould_qty",production_rec.total_mould_qty
						if tot_pour_qty < production_rec.total_mould_qty:
							pour_status = 'partial'
							status = 'mould_com'
						if tot_pour_qty >= production_rec.total_mould_qty:
							pour_status = 'done'
							status = 'fettling_inprogress'
						print "pour_status",pour_status
						print "status",status
						production_obj.write(cr,uid,production_rec.id,{'pour_qty':tot_pour_qty,'pour_state':pour_status,'state':status})
						
						### Stock Inward Creation ###
						inward_obj = self.pool.get('kg.stock.inward')
						inward_line_obj = self.pool.get('ch.stock.inward.details')
						
						inward_vals = {
							'location': production_rec.location
						}
						
						inward_id = inward_obj.create(cr, uid, inward_vals)
						
						inward_line_vals = {
							'header_id': inward_id,
							'location': production_rec.location,
							'stock_type': 'pattern',
							'pump_model_id': production_rec.pump_model_id.id,
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
							'fettling_id': fettling_id
						}
						
						inward_line_id = inward_line_obj.create(cr, uid, inward_line_vals)
					
			
			
			#~ ### Pour Log Number ###
			pour_name = ''  
			pour_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.pouring.log')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,pour_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s',now()::date) """%(pour_seq_id[0],rec.code))
			pour_name = cr.fetchone();
			self.write(cr, uid, ids, {'name': pour_name[0],'state': 'approve','approve_user_id': uid, 'approve_date': time.strftime('%Y-%m-%d %H:%M:%S')})
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
		 domain="[('mould_state','in',('partial','done')),('pour_state','in',('pending','partial')),('moc_id','=',moc_id)]"),		  
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
					pour_qty = production_rec.total_mould_qty - production_rec.pour_qty
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



