from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')
	
class kg_dispatch_update(osv.osv):

	_name = "kg.dispatch.update"
	_description = "Dispatch Update"
	_order = "entry_date desc"
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		
		for order in self.browse(cr, uid, ids, context=context):
			
			res[order.id] = {
				'amount_untaxed': 0.0,
				'total_transport': 0.0,
				'total_discount': 0.0,
				'amount_tax': 0.0,
				'total_amt' : 0.0,
				'amount_total':0.0,
				'payable_amt':0.0,
				'additional_charges':0.0,
			}
			tax_amt = discount_value = final_other_charges = 0.00
			total_value_amt = 0.00
			for line in order.line_ids:
				total_value_amt += line.total_value					
			if order.discount > 0:
				discount = order.discount
			else:
				discount = (total_value_amt * order.discount_per) / 100			
			price_amt_val = total_value_amt	- discount	
			val = 0.00 
			for c in self.pool.get('account.tax').compute_all(cr, uid, order.tax_id,
				price_amt_val, 1, 1,
				 order.customer_id)['taxes']:
				val += c.get('amount', 0.0)
				print"valvalval",val
				tax_amt = val	
			
			if order.discount_per > 0.00:					
				discount_value = (total_value_amt /100.00) * order.discount_per	
			else:
				discount_value = order.discount	
			
			res[order.id]['amount_untaxed'] = total_value_amt
			res[order.id]['total_transport'] = order.transport_amt
			res[order.id]['total_discount'] = discount_value
			res[order.id]['amount_tax'] = tax_amt
			res[order.id]['additional_charges'] = final_other_charges
			res[order.id]['total_amt'] = final_other_charges + total_value_amt + tax_amt + order.transport_amt
			res[order.id]['amount_total'] = (final_other_charges + total_value_amt + tax_amt + order.transport_amt + order.round_off_amt) - discount_value
			res[order.id]['payable_amt'] = (final_other_charges + total_value_amt + tax_amt + order.transport_amt + order.round_off_amt) - discount_value
		return res	
	_columns = {
	
		## Version 0.1
	
		## Basic Info
				
		'name': fields.char('DC No', size=24,select=True,readonly=True),
		'entry_date': fields.date('DC Date',required=True),		
		'note': fields.text('Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_sms': fields.boolean('SMS Notification'),
		'flag_email': fields.boolean('Email Notification'),
		'flag_spl_approve': fields.boolean('Special Approval'),
		'narration': fields.char('Narration'),	
		
		### Entry Info ####
			
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),	
		'active': fields.boolean('Active'),	
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),				
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),	
		
		'cancel_remark': fields.text('Cancel'),			
		
		
		## Module Requirement Info	
		
		'customer_id': fields.many2one('res.partner','Customer',required=True,domain="[('customer','=','t')]"),			
		'flag_invoice': fields.boolean('Flag Invoice'),
		'division_id': fields.many2one('kg.division.master', 'Division',required=True),		
		
		## Module process Start now 
		
		'con_note_no': fields.char('Consignment Note No.', size=128,required=True),
		'despatch_date': fields.date('Despatch Date',required=True),
		'consignee_address': fields.char('Consignee Address',required=True),
		'del_address': fields.char('Delivery Address',required=True),
		'no_of_packages': fields.float('No. of Packages',required=True),
		'total_wgt': fields.float('Total Weight',required=True),
		'transport_amt': fields.float('Transport Amount',required=True),		
		'payment_type': fields.selection([('cash','Cash'),('credit','Credit')],'Payment Type', required=True),
		'transport_id': fields.many2one('kg.transport', 'Transporter Name'),	
		'payment_id': fields.many2one('kg.payment.master', 'Payment Term',required=True),	
		'transport_copy':fields.binary('Transport Copy'),
		'filename':fields.char('File Name'),
		'tax_id': fields.many2many('account.tax', 'dispatch_update_taxes', 'dispatch_id', 'tax_id', 'Taxes'),
		'discount': fields.float('Discount Amount'),	
		'discount_per': fields.float('Discount(%)'),
		'discount_flag': fields.boolean('Discount Flag'),
		'discount_per_flag': fields.boolean('Discount Amount Flag'),
		
		# Invoice Total and Tax amount calculation	
		'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',store=True,multi="sums",help="Untaxed Amount"),
		'total_transport': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Transport',store=True,multi="sums",help="Total Transport"),
		'total_discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Discount Amount(-)',store=True,multi="sums",help="Discount Amount"),
		'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax Amount',store=True,multi="sums",help="Tax Amount"),
		'total_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Amount',store=True,multi="sums",help="Total Amount"),
		'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',store=True,multi="sums",help="Net Amount"),
		'payable_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Payable Amount',store=True,multi="sums",help="Payable Amount"),
		'additional_charges': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Additional Charges',store=True,multi="sums",help="Additional Charges"),
		'round_off_amt': fields.float('Round off(+/-)'),
				
		
		
		'invoice_ids': fields.many2many('kg.sale.invoice', 'invoice_order_ids', 'invoice_id','invoice_order_id', 'Invoice No.', delete=False,
			 domain="[('customer_id','=',customer_id),'&',('state','=','invoice')]"),
		## Child Tables Declaration 
				
		'line_ids': fields.one2many('ch.dispatch.update.line', 'header_id', "Line Details"),
		
				
	}
		
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_subcontract_invoice', context=c),			
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',		
		'active': True,
		'entry_mode': 'manual',			
		'flag_sms': False,		
		'flag_email': False,		
		'flag_spl_approve': False,	
		'discount_flag': False,
		'discount_per_flag': False,	
		
	}
	
	
	def onchange_discount_value(self, cr, uid, ids ,discount_per):	
		rec = self.browse(cr,uid,ids[0])
		invoice_amt = 0.00
		for line in rec.line_ids:
			invoice_amt += 	line.total_value
			discount_value =  invoice_amt * discount_per / 100.00
		if discount_per:
			return {'value': {'discount_flag':True }}
		else:
			return {'value': {'discount_flag':False }}
			
	def onchange_discount_percent(self,cr,uid,ids,discount):	
		rec = self.browse(cr,uid,ids[0])
		invoice_amt = 0.00
		for line in rec.line_ids:
			invoice_amt += 	line.total_value	
		if discount:
			discount = discount + 0.00
			amt_to_per = (discount / (invoice_amt or 1.0 )) * 100.00
			return {'value': {'discount_per_flag':True}}
		else:
			return {'value': {'discount_per_flag':False}}		   
	
	def button_dummy(self, cr, uid, ids, context=None):
		return True
		
	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		dispatch_line_obj = self.pool.get('ch.dispatch.update.line')			
		del_sql = """ delete from ch_dispatch_update_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)		
		for item in entry.invoice_ids:			
			if item.line_ids:
				for pump in item.line_ids:					
					if pump.pending_qty > 0:
						vals = {			
							'header_id': entry.id,
							'invoice_id':item.id,
							'pump_line_id':pump.id,
							'pump_id':pump.pump_model_id.id,								
							'order_category':'pump',		
							'actual_qty':pump.qty,		
							'qty':pump.pending_qty,					
							'value':pump.unit_price,							
						}
						
						dispatch_line_id = dispatch_line_obj.create(cr, uid,vals)
			if item.line_ids_a:
				for spare in item.line_ids_a:					
					if spare.pending_qty > 0:
						vals = {			
							'header_id': entry.id,
							'invoice_id':item.id,
							'spare_line_id':spare.id,
							'pump_id':spare.pump_id.id,								
							'order_category':'spare',		
							'actual_qty':spare.qty,		
							'qty':spare.pending_qty,					
							'value':spare.unit_price,
							
						}
						
						dispatch_line_id = dispatch_line_obj.create(cr, uid,vals)
			if item.line_ids_b:
				for access in item.line_ids_b:					
					if access.pending_qty > 0:
						vals = {			
							'header_id': entry.id,
							'invoice_id':item.id,
							'acc_line_id':access.id,
							'pump_id':access.pump_id.id,								
							'order_category':'access',		
							'actual_qty':access.qty,		
							'qty':access.pending_qty,					
							'value':access.unit_price,							
						}						
						dispatch_line_id = dispatch_line_obj.create(cr, uid,vals)				
		return True
	   

	def entry_confirm(self,cr,uid,ids,context=None):
		
		entry = self.browse(cr,uid,ids[0])	
		pump_obj = self.pool.get('ch.pumpspare.invoice')
		spare_obj = self.pool.get('ch.spare.invoice')
		access_obj = self.pool.get('ch.accessories.invoice')
		
		
		### Sequence Number Generation  ###
		
		if entry.state == 'draft':
			if len(entry.line_ids) == 0:		
				raise osv.except_osv(_('Invoice details is must !!'),
					_('Enter the proceed button!!'))	
				
			for line_item in entry.line_ids:
				if line_item.order_category == 'pump':													
					if line_item.pump_line_id.pending_qty > line_item.qty:
						raise osv.except_osv(_('Warning!'),
							_('System not allow to save Excess qty values !!'))					
					if line_item.qty <= 0.00:
						raise osv.except_osv(_('Warning!'),
							_('System not allow to save Zero and negative qty values !!'))										
					pump_obj.write(cr, uid, line_item.pump_line_id.id,{'pending_qty':line_item.pump_line_id.pending_qty - line_item.qty})
					
				if line_item.order_category == 'spare':													
					if line_item.spare_line_id.pending_qty > line_item.qty:
						raise osv.except_osv(_('Warning!'),
							_('System not allow to save Excess qty values !!'))					
					if line_item.qty <= 0.00:
						raise osv.except_osv(_('Warning!'),
							_('System not allow to save Zero and negative qty values !!'))										
					spare_obj.write(cr, uid, line_item.spare_line_id.id,{'pending_qty':line_item.spare_line_id.pending_qty - line_item.qty})
					
				if line_item.order_category == 'access':													
					if line_item.acc_line_id.pending_qty > line_item.qty:
						raise osv.except_osv(_('Warning!'),
							_('System not allow to save Excess qty values !!'))					
					if line_item.qty <= 0.00:
						raise osv.except_osv(_('Warning!'),
							_('System not allow to save Zero and negative qty values !!'))										
					access_obj.write(cr, uid, line_item.acc_line_id.id,{'pending_qty':line_item.acc_line_id.pending_qty - line_item.qty})				
				
				
												
			if entry.name == '' or entry.name == False:
				dc_name = ''	
				sc_invoice_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.dispatch.update')])
				rec = self.pool.get('ir.sequence').browse(cr,uid,sc_invoice_seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(sc_invoice_seq_id[0],rec.code,entry.entry_date))
				dc_name = cr.fetchone();
				dc_name = dc_name[0]				
			else:
				dc_name = entry.name	
				
				
			## Direct Expence Creation 
			
			direct_obj = self.pool.get('direct.entry.expense')
			direct_line_obj = self.pool.get('direct.entry.expense.line')
			
			if entry.transport_amt > 0.00:				
				vals = {							
							
							'invoice_no':dc_name,
							'expense_date':entry.entry_date,
							'invoice_date':entry.entry_date,								
							'supplier_id':entry.customer_id.id,		
							'payment_type':'freight_invoice',		
							'entry_mode':'auto',					
							'division_id':entry.division_id.id,					
							'notes':'Transport Charges',
							
						}						
				direct_exp_id = direct_obj.create(cr, uid,vals)
						
				vals = {							
						'header_id':direct_exp_id,
						'expense_id':1,
						'total_amt':entry.transport_amt,							
					}						
				direct_exp_line_id = direct_line_obj.create(cr, uid,vals)	
									
				self.pool.get('direct.entry.expense').entry_confirm(cr, uid, [direct_exp_id])								
				self.pool.get('direct.entry.expense').entry_approve(cr, uid, [direct_exp_id])								
			self.write(cr, uid, ids, {'state': 'confirmed','name':dc_name,'confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})								
								
		return True
		
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
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
		return super(kg_dispatch_update, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_dispatch_update, self).write(cr, uid, ids, vals, context)
		
	_sql_constraints = [
	
		('name', 'unique(name)', 'No must be Unique !!'),
	]	
	
kg_dispatch_update()


class ch_dispatch_update_line(osv.osv):

	_name = "ch.dispatch.update.line"
	_description = "Dispatch Update Line"
	
	def _get_oper_value(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		total_value = 0.00
		value = 0.00
		for entry in self.browse(cr, uid, ids, context=context):
			value = entry.qty * entry.value			
			result[entry.id] = value
		return result
	
	_columns = {
	
		### Basic Info
		
		'header_id':fields.many2one('kg.dispatch.update', 'Transaction', required=1, ondelete='cascade'),
		'remark': fields.text('Remarks'),
		'active': fields.boolean('Active'),			
		
		### Module Requirement Fields
		'invoice_id': fields.many2one('kg.sale.invoice','Invoice No.'),
		'order_line_id': fields.many2one('ch.work.order.details','Order Line'),
		'pump_line_id': fields.many2one('ch.pumpspare.invoice','Pump ID'),
		'spare_line_id': fields.many2one('ch.spare.invoice','Spare ID'),
		'acc_line_id': fields.many2one('ch.accessories.invoice','Accessories ID'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),
		'order_category': fields.selection([('pump','Pump'),('spare','Spare'),('access','Accessories')],'Purpose'),	
		
		'pump_serial_ids': fields.many2many('kg.assembly.inward', 'pump_serial_nos', 'dispatch_id','pump_serial_id', 'Serial No.',
			 domain="[('pump_model_id','=',pump_id),'&',('order_line_id','=',order_line_id)]"),
		
		'actual_qty': fields.integer('Actual Qty',readonly=True),		
		'qty': fields.integer('Quantity'),
		'value': fields.float('Unit Price'),	
		'total_value': fields.function(_get_oper_value, string='Total Value', method=True, store=True, type='float'),		
		
	}
		
	_defaults = {
	
		'active': True,
		
		
	}	
		
ch_dispatch_update_line()
