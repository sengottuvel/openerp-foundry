from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math

class kg_ms_sc_debit_note(osv.osv):

	_name = "kg.ms.sc.debit.note"
	_description = "MS SC Debit Note"
	
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
					as sam  """ %('kg_ms_sc_debit_note'))
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
	
	def _total_amt(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		for rec in self.browse(cr, uid, ids, context=context):
			res[rec.id] = {
				'total_cost': 0.0,
			}
			tot_amt = 0.00
			for line_id in rec.line_ids:
				tot_amt += line_id.total_amt
			print "tot_amt00000000000000000000000000000",tot_amt
			var = tot_amt + rec.additional_cost
			res[rec.id]['total_cost'] = var
		return res	
		
		
	
	_columns = {
	
		### Basic Info
			
		'name': fields.char('SC Dr. Note No.', size=128, required=False, select=True),	
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
		'entry_date': fields.date('Date',readonly=True),
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
		
		'contractor_id': fields.many2one('res.partner','Subcontractor',domain="[('contractor','=','t'),('partner_state','=','approve')]"),
		'sc_invoice_id':fields.many2one('kg.subcontract.invoice','SC Invoice No.',domain="[('contractor_id','=',contractor_id),('state','=','confirmed')]"),
		'additional_cost':fields.float('Additional Cost'),
		'total_cost': fields.function(_total_amt, string='Total Cost',multi="sums",store=True,readonly="1"),		
		'list_flag': fields.boolean('list Flag'),		
		
		## Child Tables Declaration		
		
		'line_ids': fields.one2many('ch.ms.sc.debit.note','header_id','MS SC Debit Note Line'),   
		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.ms.sc.debit.note', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		'entry_date': lambda * a: time.strftime('%Y-%m-%d'),
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Name must be unique per Company !!'),
	]
	
	### Basic Needs

	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		ser_invoice_ids  = self.pool.get('ch.sc.kg.debit.note').search(cr,uid,[('header_id','=',rec.sc_invoice_id.id),('sc_debit_id','=',rec.id)])
		if ser_invoice_ids:
			cr.execute('delete from ch_sc_kg_debit_note where id =%s'%(ser_invoice_ids[0]))
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if not entry.line_ids:
			raise osv.except_osv(_('Warning!'),
						_('Item Details should not be empty !!'))
		if entry.total_cost == 0.00:
			raise osv.except_osv(_('Warning!'),
						_('Total Cost should not be zero !!'))
		if entry.state == 'draft':
			if not entry.name:
				seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.ms.sc.debit.note')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry.entry_date))
				seq_name = cr.fetchone();
				self.write(cr,uid,ids[0],{'name':seq_name[0]})
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'confirmed':
			inv_obj = self.pool.get('ch.sc.kg.debit.note')
			debit_vals = {
			
						'header_id':entry.sc_invoice_id.id,
						'sc_debit_id':entry.id,
						'debit_date':entry.entry_date,
						'subcontract_id':entry.contractor_id.id,
						'debit_amt':entry.total_cost,
			
			}
			debit_rec_creation = inv_obj.create(cr,uid,debit_vals)
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'state': 'draft','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
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
		return super(kg_ms_sc_debit_note, self).write(cr, uid, ids, vals, context)
		
	
	_constraints = [
	
		
	]
	
	## Module Requirement
	
	def list_items(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		invoice_rec = self.pool.get('kg.subcontract.invoice')
		sc_rejection_rec = self.pool.get('kg.ms.sc.rejection.list')
		if rec.line_ids:
			cr.execute('''delete from ch_ms_sc_debit_note where header_id = %s'''%(rec.id))
		
		
		
		invoice_id = invoice_rec.browse(cr,uid,rec.sc_invoice_id.id)
		
		for invoice_line in invoice_id.line_ids:
			print "item name----------------------------------------",invoice_line.item_name
			print "WO Name----------------------------------------",invoice_line.order_id.id
			print "MOC Id----------------------------------------",invoice_line.moc_id.id
			
			rejection_id = sc_rejection_rec.search(cr,uid,[('item_name','=',invoice_line.item_name),('order_id','=',invoice_line.order_id.id),('moc_id','=',invoice_line.moc_id.id),
			('subcontractor_id','=',rec.contractor_id.id)])
			
			if rejection_id:
				print "rejection_idrejection_idrejection_idrejection_idrejection_idrejection_id",rejection_id
				weight = 0.00
				for rej_ids in rejection_id:
					ms_sc_rej_obj = sc_rejection_rec.browse(cr,uid,rej_ids)
					grinding_id = self.pool.get('kg.fettling').search(cr,uid,[('order_id','=',ms_sc_rej_obj.order_id.id),('moc_id','=',ms_sc_rej_obj.moc_id.id),('pattern_name','=',ms_sc_rej_obj.item_name)])
					if grinding_id:
						grinding_rec = self.pool.get('kg.fettling').browse(cr,uid,grinding_id[0])
						weight = grinding_rec.finish_grinding_weight
					else:
						weight = 0.00
					
					moc_id_rec = self.pool.get('kg.moc.master').browse(cr,uid,ms_sc_rej_obj.moc_id.id)
						
					rejection_ms_vals = {
															'header_id':rec.id,
															'sub_wo_id': ms_sc_rej_obj.sub_wo_id.id,
															'sub_wo_date': ms_sc_rej_obj.sub_wo_date,
															'order_id': ms_sc_rej_obj.order_id.id,
															'item_code': ms_sc_rej_obj.item_code,
															'item_name': ms_sc_rej_obj.item_name,
															'moc_id': ms_sc_rej_obj.moc_id.id,
															'rejected_qty': ms_sc_rej_obj.rejected_qty,
															'rejection_remarks': ms_sc_rej_obj.rejection_remarks,
															'weight': weight,
															'rate': ms_sc_rej_obj.moc_id.rate,
															'total_amt': (ms_sc_rej_obj.moc_id.rate*weight),
															
															}

					rejection_creation = self.pool.get('ch.ms.sc.debit.note').create(cr, uid,rejection_ms_vals)
		self.write(cr,uid,ids,{'list_flag': True})
			#~ else:
				#~ raise osv.except_osv(_('Warning!'),
						#~ _('Items are not rejected for this invoice !!'))
		
		return True
	
	######### Validations #############
	
	def _validations(self, cr, uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		cr.execute('''select sc_invoice_id from kg_ms_sc_debit_note where sc_invoice_id = %s'''%(rec.sc_invoice_id.id))
		data = cr.fetchall()
		if len(data) > 1:
			raise osv.except_osv(_('Warning!'),
						_('Debit Note for this invoice is already raised !!'))
		
		return True
	
	_constraints = [
		
		(_validations, ' ',['']),		
		] 

kg_ms_sc_debit_note()


class ch_ms_sc_debit_note(osv.osv):
	
	_name = "ch.ms.sc.debit.note"
	_description = "MS SC Debit Note Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.ms.sc.debit.note','Header Id'),
		'sub_wo_id': fields.many2one('kg.subcontract.wo','SC WO No'),
		'sub_wo_date': fields.date('SC WO Date.'),
		'order_id': fields.many2one('kg.work.order','Work Order', readonly=True),
		'wo_date': fields.date('WO Date'),	
		'item_code': fields.char('Item Code'),	
		'item_name': fields.char('Item Name'),	
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'rejected_qty': fields.float('Rejected Qty'),
		'weight': fields.float('Weight'),
		'rate': fields.float('Rate/Kg'),
		'total_amt': fields.float('Total'),
		'rejection_remarks': fields.text('Rejection Remarks'),
		
	}

ch_ms_sc_debit_note()



class ch_ms_sc_kg_debit_note(osv.osv):
	
	_name = 'ch.sc.kg.debit.note'
	_inherit = 'ch.sc.kg.debit.note'
	_description = 'This module is about the details of Debit note'
	
	_columns = {
		
		'sc_debit_id':fields.many2one('kg.ms.sc.debit.note','Debit Note No'),
		
	}

ch_ms_sc_kg_debit_note()

