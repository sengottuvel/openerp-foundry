from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_sale_dr_note(osv.osv):

	_name = "kg.sale.dr.note"
	_description = "Sales DR Note"
	
	### Version 0.1
	
	def _get_modify(self, cr, uid, ids, field_name, arg,  context=None):
		res={}		
		if field_name == 'modify':
			for h in self.browse(cr, uid, ids, context=None):
				res[h.id] = 'no'
				if h.state == 'approved':
					cr.execute(""" select * from 
					(SELECT tc.table_schema, tc.constraint_name, tc.table_name, kcu.column_name, ccu.table_name
					AS foreign_table_name, ccu.column_name AS foreign_column_name
					FROM information_schema.table_constraints tc
					JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
					JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
					WHERE constraint_type = 'FOREIGN KEY'
					AND ccu.table_name='%s')
					as sam  """ %('kg_sale_dr_note'))
					data = cr.dictfetchall()	
					if data:
						for var in data:
							data = var
							chk_sql = 'Select COALESCE(count(*),0) as cnt from '+str(data['table_name'])+' where '+data['column_name']+' = '+str(ids[0])							
							cr.execute(chk_sql)			
							out_data = cr.dictfetchone()
							if out_data:								
								if out_data['cnt'] > 0:
									res[h.id] = 'no'
									return res
								else:
									res[h.id] = 'yes'
				else:
					res[h.id] = 'no'	
		return res	
		
		### Version 0.2
	
	def _amount_line_tax(self, cr, uid, line, context=None):
		val = 0.0
		qty = 1
		tot_discount_per = 0
		for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id,
			line.amount * (1-(tot_discount_per or 0.0)/100.0), qty, 0,
			 line.header_id.customer_id)['taxes']:
			val += c.get('amount', 0.0)
		return val
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		val = untaxed_amt = tax_amt = round_off_amt = net_amt = 0.00
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'untaxed_amt': 0.0,
				'tax_amt': 0.0,
				'round_off_amt': 0.0,
				'net_amt': 0.0,				
			}						
			for line in order.line_id:
				untaxed_amt += line.amount
				val += self._amount_line_tax(cr, uid, line, context=context)	
			res[order.id]['untaxed_amt'] = untaxed_amt
			res[order.id]['tax_amt'] = val or 0.00
			res[order.id]['net_amt'] = untaxed_amt + val+ order.round_off_amt
		return res
	
	def _get_order(self, cr, uid, ids, context=None):
		result = {}
		for line in self.pool.get('ch.sale.dr.note').browse(cr, uid, ids, context=context):
			result[line.header_id.id] = True
		return result.keys()
	
	def button_dummy(self, cr, uid, ids, context=None):
		return True 
			
	_columns = {
	
		### Basic Info
			
		'name': fields.char('Debit Note No', size=128, required=True, select=True),	
		'code': fields.char('Code', size=4, required=False),		
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),


		### Entry Info ###
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
		'debit_note_date':fields.date('Debit Note Date'),	
		'invoice_id':fields.many2one('kg.sale.invoice','Invoice No',domain=[('state','=','approved')]),	
		'customer_id':fields.many2one('res.partner','Customer Name'),	
		'dealer_id':fields.many2one('res.partner','Dealer Name'),	
		'work_order_id': fields.many2one('kg.work.order','WO No.'),
		'dealer_po_no':fields.char('Dealer PO No'),	
		'untaxed_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
			store={
				'kg.sale.dr.note': (lambda self, cr, uid, ids, c={}: ids, ['line_id'], 10),
				'ch.sale.dr.note': (_get_order, ['amount', 'tax_id',0, 1], 10),
			}, multi="sums", help="Untaxed amount"),
		'tax_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax Amount',
			store={
				'kg.sale.dr.note': (lambda self, cr, uid, ids, c={}: ids, ['line_id'], 10),
				'ch.sale.dr.note': (_get_order, ['amount', 'tax_id', 0,1], 10),
			}, multi="sums", help="Tax amount"),
		'net_amt': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',
			store=True,multi="sums",help="The total amount"),
		'round_off_amt': fields.float('Round off(+/-)' ),
		
		## Child Tables Declaration		
		
		'line_id':fields.one2many('ch.sale.dr.note', 'header_id', "Debit Note Line"),		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.sale.dr.note', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		'debit_note_date' : lambda * a: time.strftime('%Y-%m-%d'),
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Name must be unique for a Debit Note !!'),
	]
	
	### Basic Needs
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'state': 'reject','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter the remarks in rejection remark field !!'))
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state not in ('draft','cancel'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_sale_dr_note, self).write(cr, uid, ids, vals, context)
	
	####### Validations ############
	
	def _check_lineitems(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if not entry.line_id:
			raise osv.except_osv(_('Warning!'),
						_('Line Details should not be empty !!'))
		if entry.line_id:
			line_description = [ line.description for line in entry.line_id]
			print "line_descriptionline_descriptionline_description",line_description
			a= [line_description.count(i) for i in line_description ]
			for j in a:
				if j > 1:
					raise osv.except_osv(_('Warning!'),
								_('Duplicate of %s are not allowed !!'%(line_description[0])))
		for lines in entry.line_id:
			if lines.amount <= 0.00:
				raise osv.except_osv(_('Warning!'),
						_('Amount Entered for %s should not be less than or equal to zero !!'%(lines.description)))
			
		return True
		
	
	_constraints = [
			 (_check_lineitems, 'System not allow to save with empty Concrete Details !!',['']),
       
		
	]
	
	## Module Requirement
	
	def onchange_invoice_id(self, cr, uid, ids, invoice_id):
		sale_invoice_rec = self.pool.get('kg.sale.invoice').browse(cr,uid,invoice_id)
		work_order_rec = self.pool.get('kg.work.order').browse(cr,uid,[x.id for x in sale_invoice_rec.work_order_ids])
		if work_order_rec[0].offer_no:
			offer_id = self.pool.get('kg.crm.offer').search(cr,uid,[('name','=',work_order_rec[0].offer_no)])
			if offer_id:
				offer_rec = self.pool.get('kg.crm.offer').browse(cr,uid,offer_id[0])
				dealer_id = offer_rec.dealer_id.id
				dealer_po_no = offer_rec.dealer_po_no
		else:
			dealer_id = ''
			dealer_po_no = ''					
		return {'value': {
			'customer_id' : sale_invoice_rec.customer_id.id,
			'work_order_id':work_order_rec[0].id,
			'dealer_id':dealer_id,
			'dealer_po_no':dealer_po_no,
			}}
		return True
	
kg_sale_dr_note()

class ch_sale_dr_note(osv.osv):

	_name = "ch.sale.dr.note"
	_description = "Debit note line"
	
	def _get_total_amt(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		ed_total_val = 0
		ed_total = 0
		sale_total = 0
		service_total = 0
		
		for entry in self.browse(cr, uid, ids, context=context):
			total_value = entry.amount		
			amount = entry.amount
			tax_total= 0.00		
			for item in [x.id for x in entry.tax_id]:				
				tax_rec = self.pool.get('account.tax').browse(cr,uid,item)											
				tax_amt = (amount/100.00)*(tax_rec.amount*100.00)
				tax_total += tax_amt
				print"tax_total",tax_total					
			if tax_total:						
				total_value += tax_total
					
			else:
				pass
			
			result[entry.id] = total_value
		return result
	
	
		
	_columns = {
	
		'header_id':fields.many2one('kg.sale.dr.note', 'Header_id', ondelete='cascade'),
		'description' : fields.char('Description'),
		'amount': fields.float('Value'),
		'tax_id': fields.many2many('account.tax', 'debit_note_tax', 'note_id', 'tax_id', 'Tax' ,domain=[('active','=','t')]),
		'sub_total': fields.function(_get_total_amt, string='Total Amount',digits=(16,2), method=True, store=True, type='float'),
		
		
	}
	
ch_sale_dr_note()
