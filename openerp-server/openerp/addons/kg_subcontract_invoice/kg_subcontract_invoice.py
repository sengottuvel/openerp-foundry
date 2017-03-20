from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
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
   ('project','Project')
]

	


class kg_subcontract_invoice(osv.osv):

	_name = "kg.subcontract.invoice"
	_description = "Subcontract Invoice"
	_order = "entry_date desc"
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		
		for order in self.browse(cr, uid, ids, context=context):
			
			res[order.id] = {
				'amount_untaxed': 0.0,
				'total_discount': 0.0,
				'amount_tax': 0.0,
				'total_amt' : 0.0,
				'amount_total':0.0,
				'payable_amt':0.0,
			}
			tax_amt = discount_value = 0.00			
			if order.discount > 0.00:
				amt_to_per = (order.discount / (order.invoice_amt or 1.0 )) * 100
				kg_discount_per = order.discount_per
				tot_discount_per = amt_to_per
			else:
				tot_discount_per = order.discount_per
			val = 0.00 
			print"tot_discount_pertot_discount_per",tot_discount_per
			for c in self.pool.get('account.tax').compute_all(cr, uid, order.tax_id,
				order.invoice_amt * (1-(tot_discount_per or 0.0)/100.0), 1, 1,
				 order.contractor_id)['taxes']:
				val += c.get('amount', 0.0)
				print"valvalval",val
				tax_amt = val	
			
			if order.discount_per > 0.00:					
				discount_value = (order.invoice_amt /100.00) * order.discount_per	
			else:
				discount_value = order.discount
			
			res[order.id]['amount_untaxed'] = order.invoice_amt - tax_amt
			res[order.id]['total_discount'] = discount_value 
			res[order.id]['amount_tax'] = tax_amt
			res[order.id]['total_amt'] = order.invoice_amt + tax_amt
			res[order.id]['amount_total'] = (order.invoice_amt + tax_amt + order.round_off_amt) - discount_value 
			res[order.id]['payable_amt'] = (order.invoice_amt + tax_amt + order.round_off_amt) - discount_value 	
		return res	
	_columns = {
	
		## Version 0.1
	
		## Basic Info
				
		'name': fields.char('Invoice No', size=24,select=True,readonly=True),
		'entry_date': fields.date('Invoice Date',required=True),		
		'note': fields.text('Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled'),('approved','AC ACK Pending'),('done','AC ACK Done')],'Status', readonly=True),
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
		'ap_rej_date': fields.datetime('Approved Date', readonly=True),
		'done_date': fields.datetime('Done Date', readonly=True),
		'done_user_id': fields.many2one('res.users', 'Done By', readonly=True),	
		'ap_rej_user_id': fields.many2one('res.users', 'Approved By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),	
		
		'cancel_remark': fields.text('Cancel'),			
		'reject_remark': fields.text('Reject'),			
		
		## Module Requirement Info	
		
		'contractor_id': fields.many2one('res.partner','Subcontractor',required=True,domain="[('contractor','=','t')]"),		
		'phone': fields.char('Phone',size=64),
		'contact_person': fields.char('Contact Person', size=128),
				
		'inward_subcontract_line_ids': fields.many2many('ch.subcontract.inward.line','m2m_invoice_details' , 'order_id', 'sc_id', 'SC Items',
			domain="[('state','in',('pending','partial')),('contractor_id','=',contractor_id)]"),	 			
		
		
		'flag_invoice': fields.boolean('Flag Invoice'),	
		
		## Calculation process Start now 
		
		'con_invoice_no': fields.char('Contractor Invoice No', size=128,required=True),
		'invoice_date': fields.date('Invoice Date',required=True),
		'due_date': fields.date('Due Date',required=True),
		'invoice_amt': fields.float('Invoice Amount',required=True),
		'invoice_copy':fields.binary('Invoice Copy'),
		'tax_id': fields.many2many('account.tax', 'subcontract_invoice_taxes', 'invoice_id', 'tax_id', 'Taxes'),
		'discount': fields.float('Discount Amount'),	
		'discount_per': fields.float('Discount(%)'),
		'discount_flag': fields.boolean('Discount Flag'),
		'discount_per_flag': fields.boolean('Discount Amount Flag'),
		
		# Invoice Total and Tax amount calculation	
		'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',store=True,multi="sums",help="Untaxed Amount"),
		'total_discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Discount Amount(-)',store=True,multi="sums",help="Discount Amount"),
		'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax Amount',store=True,multi="sums",help="Tax Amount"),
		'total_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Amount',store=True,multi="sums",help="Total Amount"),
		'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',store=True,multi="sums",help="Net Amount"),
		'payable_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Payable Amount',store=True,multi="sums",help="Payable Amount"),
		
		'round_off_amt': fields.float('Round off(+/-)'),
				
		
		## Child Tables Declaration 
				
		'line_ids': fields.one2many('ch.subcontract.invoice.line', 'header_id', "Line Details"),
		
				
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
	
	
	def onchange_invoice_amt(self,cr,uid,ids,invoice_amt,discount_per,context = None):
		discount = 0.00
		if invoice_amt >0.00 and discount_per > 0.00:
			discount = (invoice_amt * discount_per) / 100.0
		return {'value':{'discount':(round(discount,2))}}
		
	
	
	def onchange_discount_value(self, cr, uid, ids, invoice_amt,discount_per):		
		discount_value =  invoice_amt * discount_per / 100.00
		if discount_value:
			return {'value': {'discount_flag':True }}
		else:
			return {'value': {'discount_flag':False }}
			
	def onchange_discount_percent(self,cr,uid,ids,invoice_amt,discount):		
		if discount:
			discount = discount + 0.00
			amt_to_per = (discount / (invoice_amt or 1.0 )) * 100.00
			return {'value': {'discount_per_flag':True}}
		else:
			return {'value': {'discount_per_flag':False}}	
	
	
	def button_dummy(self, cr, uid, ids, context=None):
		return True
	
		
	#~ def onchange_discount_percent(self,cr,uid,ids,invoice_amt,discount,context = None):
		#~ discount_percent = 0.00
		#~ discount_per_flag = False
		#~ if discount > 0.00:
			#~ discount_percent = (100.00/invoice_amt)*(round(discount,2))
			#~ discount_per_flag = True
		#~ return {'value':{'discount_per_flag':discount_per_flag}}
		#~ 
	#~ def onchange_discount_value(self,cr,uid,ids,invoice_amt,discount_per,context = None):
		#~ discount_value = 0.00
		#~ discount_flag = False
		#~ if discount_per > 0.00:
			#~ discount_value = (invoice_amt /100.00)*discount_per
			#~ discount_flag = True
		#~ return {'value':{'discount_flag':discount_flag}}
	#~ 
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		entry_date = rec.entry_date
		entry_date = str(entry_date)
		entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
		if entry_date > today or entry_date < today:
			return False
		return True
			
		
	#~ def _check_lineitems(self, cr, uid, ids, context=None):
		#~ entry = self.browse(cr,uid,ids[0])
		#~ if not entry.line_ids:
			#~ return False
		#~ return True
			
	
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future and past date. !!',['Invoice Date']),
		#~ (_check_lineitems, 'System not allow to save with empty Details !!',['']),
	   
		
	   ]
	   
	def onchange_contractor(self, cr, uid, ids, contractor_id):
		if contractor_id:
			contractor_rec = self.pool.get('res.partner').browse(cr, uid, contractor_id)
		return {'value': {'contact_person':contractor_rec.contact_person,'phone':contractor_rec.phone  }}
		
	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		invoice_line_obj = self.pool.get('ch.subcontract.invoice.line')
			
		del_sql = """ delete from ch_subcontract_invoice_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		for item in entry.inward_subcontract_line_ids:			
			
			
			vals = {
			
				'header_id': entry.id,
				'sc_id':item.sc_id.id,
				'qty':item.qty,								
				'actual_qty':item.actual_qty,		
				'wo_line_id':item.wo_line_id.id,		
				'com_weight':item.com_weight,					
				'sc_inward_line_id':item.id,	
				'operation_id':[(6, 0, [x.id for x in item.com_operation_id])],
				
			}
			
			in_line_id = invoice_line_obj.create(cr, uid,vals)		
			
			
		self.write(cr, uid, ids, {'flag_invoice': True})
		
			
		return True
	   

	def entry_confirm(self,cr,uid,ids,context=None):
		
		entry = self.browse(cr,uid,ids[0])		
		
		### Sequence Number Generation  ###
		
		if entry.state == 'draft':		
			sc_inward_line_obj = self.pool.get('ch.subcontract.inward.line')
			if len(entry.line_ids) == 0:
				raise osv.except_osv(_('Warning!'),
								_('System not allow to without line items !!'))
			for line_item in entry.line_ids:				
				if line_item.qty < 0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save negative values !!'))
								
				if line_item.qty == 0:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to save Zero values !!'))	
				
				if (line_item.sc_inward_line_id.sc_invoice_qty + line_item.qty) > line_item.sc_inward_line_id.qty:
					raise osv.except_osv(_('Warning!'),
								_('System not allow to invoice Qty Exceed !!'))						
									
									
				if (line_item.sc_inward_line_id.sc_invoice_qty + line_item.qty) == line_item.sc_inward_line_id.qty:
					invoice_state = 'done'
				if (line_item.sc_inward_line_id.sc_invoice_qty + line_item.qty) < line_item.sc_inward_line_id.qty:
					invoice_state = 'partial'			
				
										
				sc_inward_line_obj.write(cr, uid, line_item.sc_inward_line_id.id, 
							{'sc_invoice_qty': line_item.sc_inward_line_id.sc_invoice_qty + line_item.qty,'state': invoice_state,'pending_qty':line_item.sc_inward_line_id.pending_qty - line_item.qty})				
				
				
												
			if entry.name == '' or entry.name == False:
				sc_invoice_name = ''	
				sc_invoice_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.subcontract.invoice')])
				rec = self.pool.get('ir.sequence').browse(cr,uid,sc_invoice_seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(sc_invoice_seq_id[0],rec.code,entry.entry_date))
				sc_invoice_name = cr.fetchone();
				sc_invoice_name = sc_invoice_name[0]				
			else:
				sc_invoice_name = entry.name		
											
			self.write(cr, uid, ids, {'state': 'confirmed','name':sc_invoice_name,'confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})								
								
		return True
		
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True
		
	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			if rec.reject_remark:
				self.write(cr, uid, ids, {'state': 'confirmed','update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Reject remark is must !!'),
					_('Enter the remarks in Reject remarks field !!'))
			return True
		
	def entry_approved(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass		
		return True
		
	def entry_accept(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':			
			self.write(cr, uid, ids, {'state': 'done','done_user_id': uid, 'done_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
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
		return super(kg_subcontract_invoice, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_subcontract_invoice, self).write(cr, uid, ids, vals, context)
		
	_sql_constraints = [
	
		('name', 'unique(name)', 'No must be Unique !!'),
	]	
	
kg_subcontract_invoice()


class ch_subcontract_invoice_line(osv.osv):

	_name = "ch.subcontract.invoice.line"
	_description = "Subcontract Invoice Line"
	
	def _get_oper_value(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		total_value = 0.00
		value = 0.00
		for entry in self.browse(cr, uid, ids, context=context):
			for line in entry.wo_op_id:
				print"entry.qty",entry.qty
				print"line.op_rate",line.op_rate
				total_value= entry.qty * line.op_rate * entry.com_weight			
				value += total_value
			print"total_value",value
			result[entry.id] = value
		return result
	
	_columns = {
	
		### Basic Info
		
		'header_id':fields.many2one('kg.subcontract.invoice', 'Transaction', required=1, ondelete='cascade'),
		'remark': fields.text('Remarks'),
		'active': fields.boolean('Active'),			
		
		### Module Requirement Fields
		'sc_id': fields.many2one('kg.subcontract.process','Subcontractor List Id'),
		'sc_inward_line_id': fields.many2one('ch.subcontract.inward.line','Subcontractor Inward List Id'),
		'ms_id': fields.related('sc_id','ms_id', type='many2one', relation='kg.machineshop', string='MS Id', store=True, readonly=True),
		'production_id': fields.related('sc_id','production_id', type='many2one', relation='kg.production', string='Production No.', store=True, readonly=True),
		'position_id': fields.related('sc_id','position_id', type='many2one', relation='kg.position.number', string='Position No.', store=True, readonly=True),
		'order_id': fields.related('sc_id','order_id', type='many2one', relation='kg.work.order', string='Work Order', store=True, readonly=True),
		'order_line_id': fields.related('sc_id','order_line_id', type='many2one', relation='ch.work.order.details', string='Order Line', store=True, readonly=True),
		'order_no': fields.related('sc_id','order_no', type='char', string='WO No.', store=True, readonly=True),
		'order_delivery_date': fields.related('sc_id','order_delivery_date', type='date', string='Delivery Date', store=True, readonly=True),

		'order_category': fields.related('sc_id','order_category', type='selection', selection=ORDER_CATEGORY, string='Category', store=True, readonly=True),
		'order_priority': fields.related('sc_id','order_priority', type='selection', selection=ORDER_PRIORITY, string='Priority', store=True, readonly=True),
		'pump_model_id': fields.related('sc_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True, readonly=True),
		'pattern_id': fields.related('sc_id','pattern_id', type='many2one', relation='kg.pattern.master', string='Pattern Number', store=True, readonly=True),
		'pattern_code': fields.related('sc_id','pattern_code', type='char', string='Pattern Code', store=True, readonly=True),
		'pattern_name': fields.related('sc_id','pattern_name', type='char', string='Pattern Name', store=True, readonly=True),
		'item_code': fields.related('sc_id','item_code', type='char', string='Item Code', store=True, readonly=True),
		'item_name': fields.related('sc_id','item_name', type='char', string='Item Name', store=True, readonly=True),
		'moc_id': fields.related('sc_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True, readonly=True),
		'ms_type': fields.related('sc_id','ms_type', type='selection', selection=[('foundry_item','Foundry Item'),('ms_item','MS Item')], string='Item Type', store=True, readonly=True),
		'wo_line_id': fields.many2one('ch.subcontract.wo.line','Subcontract Workorder Id'),
		
		'operation_id': fields.many2many('ch.kg.position.number', 'm2m_invoice_operation_details', 'in_operation_id', 'in_sub_id','Operation', domain="[('header_id','=',position_id)]"),
		
		'actual_qty': fields.integer('Actual Qty',readonly=True),
		'qty': fields.integer('Quantity'),
		'value': fields.float('Unit Price'),		
		'total_value': fields.function(_get_oper_value, string='Total Value', method=True, store=True, type='float'),
		'com_weight': fields.float('Completed weight'),				
		
		'state': fields.selection([('pending','Pending'),('partial','Partial'),('done','Done')],'Status', readonly=True),
		
		## Child Tables Declaration 
		'wo_op_id': fields.related('wo_line_id','line_ids', type='one2many', relation='ch.wo.operation.details', string='Operation Items'),		
		
	}
		
	_defaults = {
	
		'active': True,
		'state': 'pending',
		
	}
	def onchange_total_value(self, cr, uid, ids, qty,value):
		if qty:			
			total_value = qty * value
		return {'value': {'total_value': total_value}}
		
ch_subcontract_invoice_line()
