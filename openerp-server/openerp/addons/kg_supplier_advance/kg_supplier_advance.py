from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_supplier_advance(osv.osv):
	
	_name = "kg.supplier.advance"
	_description = "Supplier Advance"
	_order = "entry_date desc"
	
	def _balance_amount_value(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		bal_value = bal_pay_amt = 0.00
		for entry in self.browse(cr, uid, ids, context=context):
			result[entry.id] = {
				'balance_amt': 0.0,
				'bal_pay_amt': 0.0,
			}
			bal_value = entry.advance_amt - entry.adjusted_amt
			bal_pay_amt = entry.advance_amt - entry.paid_amt
			print"bal_valuebal_value",bal_value
			print"bal_pay_amtbal_pay_amt",bal_pay_amt
			result[entry.id]['balance_amt'] = bal_value or 0.00
			result[entry.id]['bal_pay_amt'] = bal_pay_amt or 0.00
			print"result[entry.id]['balance_amt']",result[entry.id]['balance_amt'] 
			print"result[entry.id]['bal_pay_amt']",result[entry.id]['bal_pay_amt'] 
			
		return result
	
	_columns = {
		
		## Basic Info
		
		'name': fields.char('Advance No', size=24,select=True,readonly=True),
		'entry_date': fields.date('Advance Date',required=True),
		'note': fields.text('Notes'),
		'reject_remark': fields.text('Reject'),
		'cancel_remark': fields.text('Cancel'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('ac_ack_pending','AC ACK Pending'),('approve','AC Accepted'),('cancel','Cancelled')],'Status', readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_sms': fields.boolean('SMS Notification'),
		'flag_email': fields.boolean('Email Notification'),
		'flag_spl_approve': fields.boolean('Special Approval'),
		
		## Entry Info
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'crt_date': fields.datetime('Created Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'ap_rej_date': fields.datetime('Approved/Rejected Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Rejected By', readonly=True),
		'ac_ap_date': fields.datetime('AC Approved Date', readonly=True),
		'ac_ap_user_id': fields.many2one('res.users', 'AC Approved By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		
		## Module Requirement Info
		
		'supplier_id': fields.many2one('res.partner', 'Supplier Name', domain = "['|',('contractor','=',True),('supplier','=',True)]"),
		'order_category': fields.selection([('purchase','Purchase'),('service','Service')],'Order Category', readonly=True),
		'po_id':fields.many2one('purchase.order','PO No',domain="[('state','=','approved'), '&', ('adv_flag','=',False), '&', ('partner_id','=',supplier_id), '&', ('order_line.line_state','!=','cancel'),'&', ('bill_type','=','advance')]"),
		'so_id':fields.many2one('kg.service.order','SO No',domain="[('state','=','approved'), '&', ('adv_flag','=',False), '&', ('partner_id','=',supplier_id),'&', ('payment_type','=','advance')]"),
	    'advance': fields.float('Current Advance(%)'),
	    'allowed_advance': fields.float('Eligible Advance(%)',readonly=True),
	    'advance_amt': fields.float('Advance Amount'),
		'order_value': fields.float('Order Value'),
		'adjusted_amt': fields.float('Adjusted Amount'),
		'balance_amt': fields.function(_balance_amount_value, digits_compute= dp.get_precision('Account'),string='Balance Amount',store=True, type='float',multi="sums"),
		'order_no': fields.char('Order NO',readonly=True),				
		'bal_advance_amt': fields.float('Balance Advance Amount'),
		'paid_amt': fields.float('Paid Amount'),
		'bal_pay_amt': fields.function(_balance_amount_value, digits_compute= dp.get_precision('Account'),string='Balance Payable Amount',store=True, type='float',multi="sums"),
		
		## Child Tables Declaration
		
		'line_ids': fields.one2many('ch.advance.line', 'header_id', "Line Details"),		
		
	}
	
	_defaults = {
		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_supplier_advance', context=c),			
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date': time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',		
		'active': True,
		'entry_mode': 'manual',		
		'flag_sms': False,		
		'flag_email': False,		
		'flag_spl_approve': False,					
		
	}
	
	def onchange_order_value(self, cr, uid, ids, po_id, so_id, context=None):
		value = {'order_value':0.00}		
		total_value = bal_adv_amt = adv_amt = bal_advance = allowed_advance = eligible_adv = 0.00
		order_no = ''
		sup_adv_obj = self.pool.get('kg.supplier.advance')
		if po_id:
			order_rec = self.pool.get('purchase.order').browse(cr,uid,po_id)
			total_value = order_rec.amount_total
			order_no = order_rec.name
			allowed_advance = order_rec.advance_amt
			eligible_advance = order_rec.advance_amt
			adv_ids = sup_adv_obj.search(cr,uid,[('po_id','=',po_id),('state','=','approve')])
		if so_id:
			order_rec = self.pool.get('kg.service.order').browse(cr,uid,so_id)
			total_value += order_rec.amount_total
			order_no = order_rec.name
			allowed_advance = order_rec.advance_amt
			eligible_advance = order_rec.advance_amt
			adv_ids = sup_adv_obj.search(cr,uid,[('po_id','=',po_id),('state','=','approve')])
		if adv_ids:
			eligible_advance = 0.00
			for item in adv_ids:
				adv_rec = sup_adv_obj.browse(cr,uid,item)
				adv_amt += adv_rec.advance_amt
				bal_advance += adv_rec.advance
				bal_adv_amt = ((order_rec.amount_total/100) * order_rec.advance_amt) - adv_amt
				eligible_adv += adv_rec.advance
				eligible_advance = order_rec.advance_amt - eligible_adv
		
		return {'value': {'order_value' : total_value,'order_no':order_no,'bal_advance_amt':bal_adv_amt,'advance':eligible_advance,'allowed_advance':allowed_advance}}
	
	def onchange_supplier_id(self, cr, uid, ids, supplier_id, context=None):
		value = {}		
		sup_ids = self.pool.get('kg.supplier.advance').search(cr,uid,[('supplier_id','=',supplier_id),('state','=','approve')])		
		adv_line_vals=[]
		if sup_ids:
			for ele in sup_ids:
				adv_rec = self.pool.get('kg.supplier.advance').browse(cr,uid,ele)
				adv_line_vals.append({
							   'advance_no':adv_rec.name,
							   'advance_date':adv_rec.entry_date,
							   'order_no':adv_rec.order_no,
							   'advance_amt':adv_rec.advance_amt,
							   'adjusted_amt':adv_rec.adjusted_amt,
							   'balance_amt':adv_rec.balance_amt,
								})
				value['line_ids'] = adv_line_vals
		else:
			value['line_ids'] = adv_line_vals			
		return {'value': value}
	
	def onchange_advance(self,cr,uid,ids,advance,order_category,po_id,so_id,context=None):
		value = {'advance_amt':0.00}
		advance_amt = pre_advance = 0.00
		#~ if advance > 100:
			#~ raise osv.except_osv(_('Warning!'),
				#~ _('Advance(%) should not be greater than 100!'))
		if advance > 0 and advance <= 100:
			if order_category == 'purchase' and po_id:
				order_ids = self.pool.get('purchase.order').search(cr,uid,[('id','=',po_id),('state','=','approved')])
				if order_ids:
					order_rec = self.pool.get('purchase.order').browse(cr,uid,order_ids[0])
					if advance > order_rec.advance_amt:
						raise osv.except_osv(_('Warning!'),
							_('Advance(%) should not be greater than PO advance!'))
					adv_ids = self.search(cr,uid,[('po_id','=',po_id),('state','=','approve')])
					if adv_ids:
						for item in adv_ids:
							adv_rec = self.browse(cr,uid,item)
							pre_advance += adv_rec.advance
			elif order_category == 'service' and so_id:
				order_ids = self.pool.get('service.order').search(cr,uid,[('id','=',so_id),('state','=','approved')])
				if order_ids:
					order_rec = self.pool.get('service.order').browse(cr,uid,order_ids[0])
					if advance > order_rec.advance_amt:
						raise osv.except_osv(_('Warning!'),
							_('Advance(%) should not be greater than SO advance!'))
					adv_ids = self.search(cr,uid,[('so_id','=',po_id),('state','=','approve')])
					if adv_ids:
						for item in adv_ids:
							adv_rec = self.browse(cr,uid,item)
							pre_advance += adv_rec.advance
			else:
				pass
			if order_rec:
				advance_amt = (order_rec.amount_total / 100.00) * advance
				if (pre_advance+advance) <= order_rec.advance_amt:
					pass
				else:
					if order_category == 'purchase':
						raise osv.except_osv(_('Warning!'),
							_('Advacne Exceeds from PO advance(%)!'))
					elif order_category == 'service':
						raise osv.except_osv(_('Warning!'),
							_('Advacne Exceeds from SO advance(%)!'))
			value['advance_amt'] = advance_amt			
		return {'value': value}
	
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
	
	def _past_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.entry_mode == 'manual':
			today = date.today()
			today = str(today)
			today = datetime.strptime(today, '%Y-%m-%d')
			entry_date = rec.entry_date
			entry_date = str(entry_date)
			entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
			if entry_date < today:
				return False
		return True		
	
	def _check_adv_amt(self,cr,uid,ids,context = None):
		rec = self.browse(cr,uid,ids[0])
		total = 0.00
		for line in rec.line_ids:
			if rec.order_no == line.order_no:
				total += line.balance_amt
		total_amt = rec.advance_amt + total
		if rec.advance > 100:
			raise osv.except_osv(_('Warning!'),
				_('Advance amount do not exceed "100 %"'))
		if rec.advance_amt <= 0.00 or total_amt > rec.order_value:
			return False
		else:
			return True
	
	def _duplicate_entry(self,cr,uid,ids,context = None):
		rec = self.browse(cr,uid,ids[0])
		if rec.order_category == 'purchase':
			po_obj = self.search(cr,uid,[('state','=','draft'),('po_id','=',rec.po_id.id)])
			if len(po_obj) > 1:
				raise osv.except_osv(_('Warning!'),
					_('Mentioned PO Advance entry is already in DRAFT state.'))
		if rec.order_category == 'service':
			so_obj = self.search(cr,uid,[('state','=','draft'),('so_id','=',rec.so_id.id)])
			if len(so_obj) > 1:
				raise osv.except_osv(_('Warning!'),
					_('Mentioned SO Advance entry is already in DRAFT state.'))
		return True
	
	_constraints = [                   
        
        (_future_entry_date_check, 'System not allow to save with future date!',['Advance Date']), 
        (_past_entry_date_check, 'System not allow to save with past date!',['Advance Date']), 
        (_check_adv_amt, 'Please Check the advance amount. Advance amount should not be allow zero,negative and greater than Order Value amount!',['Advance amount']),       
        (_duplicate_entry, 'Mentioned Order Advance entry is already in DRAFT state.',['']), 
         
       ]
    
	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			### Sequence Number Generation  ###
			if rec.order_category == 'purchase':
				if rec.name == '' or rec.name == False:
					seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.supplier.advance')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_obj_id[0])
					cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_obj_id[0],seq_rec.code,rec.entry_date))
					entry_name = cr.fetchone();
					entry_name = entry_name[0]
				else:
					entry_name = rec.name
			if rec.order_category == 'service':
				if rec.name == '' or rec.name == False:
					seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','ch.advance.line')])
					seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_obj_id[0])
					cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_obj_id[0],seq_rec.code,rec.entry_date))
					entry_name = cr.fetchone();
					entry_name = entry_name[0]
				else:
					entry_name = rec.name
			
			self.confirmation_validation(cr,uid,rec)
			
			self.write(cr, uid, ids, {'name':entry_name,'state':'confirmed','confirm_user_id':uid,'confirm_date':dt_time})
		
		return True
	
	def confirmation_validation(self,cr,uid,rec,context=None):
		pre_total = po_advance = cur_adv = 0
		if rec.order_category == 'purchase':
			order_id = rec.po_id
			order_obj = self.pool.get('purchase.order')
			obj = self.search(cr,uid,[('state','=','approve'),('po_id','=',order_id.id)])
		if rec.order_category == 'service':
			order_id = rec.so_id
			order_obj = self.pool.get('kg.service.order')
			obj = self.search(cr,uid,[('state','=','approve'),('so_id','=',order_id.id)])
		if obj:
			for item in obj:
				pre_rec = self.browse(cr,uid,item)
				pre_total += pre_rec.advance
		print"pre_totalpre_total",pre_total
		po_advance = order_id.advance_amt
		print"po_advance_amt",po_advance
		if (pre_total+rec.advance) <= po_advance:
			if po_advance == rec.advance + pre_total:
				order_obj.write(cr,uid,order_id.id,{'adv_flag':True})
		else:
			if rec.order_category == 'purchase':
				raise osv.except_osv(_('Warning!'),
					_('Advance(%) should not be greater than PO advance!'))
			elif rec.order_category == 'service':
				raise osv.except_osv(_('Warning!'),
					_('Advance(%) should not be greater than SO advance!'))
			else:
				pass
		return True
	
	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state =='ac_ack_pending':
			if not rec.reject_remark:
				raise osv.except_osv(_('Remarks Needed !!'),
					_('Enter Remark in Remarks ....'))
			self.write(cr, uid, ids, {'state':'confirmed','ac_ap_user_id':uid,'ac_ap_date':dt_time})
		return True
	
	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state =='confirmed':
			self.confirmation_validation(cr,uid,rec)
			self.write(cr, uid, ids, {'paid_amt':rec.advance_amt,'state':'ac_ack_pending','ap_rej_user_id':uid,'ap_rej_date':dt_time})
		return True
	
	def entry_ac_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state =='ac_ack_pending':
			self.write(cr, uid, ids, {'state':'approve','ac_ap_user_id':uid,'ac_ap_date':dt_time})
		return True
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state =='confirmed':
			if rec.state == 'entry_cancel':
				if rec.cancel_remark:
					self.write(cr, uid, ids, {'state':'cancel','cancel_user_id':uid,'cancel_date':dt_time})
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
				if rec.order_category == 'purchase':
					inv_obj = self.pool.get('ch.poadvance.purchase.invoice.line').search(cr,uid,[('sup_advance_id','=',rec.id)])
					if inv_obj:
						raise osv.except_osv(_('Warning!'),
							_('You can not delete this entry because mapped in Invoice!'))
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
	def create(self, cr, uid, vals, context=None):
		return super(kg_supplier_advance, self).create(cr, uid, vals, context=context)
	
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date':dt_time,'update_user_id':uid})
		return super(kg_supplier_advance, self).write(cr, uid, ids, vals, context)
	
	_sql_constraints = [
		
		('name', 'unique(name)', 'No must be Unique !!'),
	]	
	
kg_supplier_advance()


class ch_advance_line(osv.osv):
	
	_name = "ch.advance.line"
	_description = "Advance History"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('kg.supplier.advance', 'Advance', required=1, ondelete='cascade'),
		'remark': fields.text('Remarks'),
		'active': fields.boolean('Active'),			
		
		## Module Requirement
		
		'advance_no':fields.char('Advance No',readonly=True),
		'advance_date':fields.date('Advance Date'),		
		'order_no': fields.char('Order NO',readonly=True),
		'advance_amt': fields.float('Advance Amount',required=True),		
		'adjusted_amt': fields.float('Adjusted Amount',readonly=True),		
		'balance_amt': fields.float('Balance Amount',readonly=True),		
		
		## Child Tables Declaration
		
	}
	
	_defaults = {
		
		'active': True,
		
	}
	
ch_advance_line()
