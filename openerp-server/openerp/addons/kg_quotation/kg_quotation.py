from datetime import *
import time
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import decimal_precision as dp
from itertools import groupby
from datetime import datetime, timedelta,date
import smtplib
import socket
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from collections import OrderedDict
from tools import number_to_text_convert_india
import urllib
import urllib2
import base64
import re
import logging
logger = logging.getLogger('server')

class kg_rfq_vendor_selection(osv.osv):
	
	_name = "kg.rfq.vendor.selection"
	_description = "RFQ Vendor Selection"
	_order = 'name desc'
	
	_columns = {
		
		## Basic Info
		
		'name': fields.char('RFQ No', size=32),
		'state': fields.selection([('draft','Draft'),('confirm','WFA'),('approved','RFQ Generated'),('rfq_approved','RFQ Approved'),('comparison_confirmed','Compared'),('comparison_approved','Quotation Comparision Approved'),('reject','Rejected'),('cancel','Cancelled')],'State',readonly=True),
		'cancel_remark': fields.text('Cancel Remark'),
		'reject_remark': fields.text('Reject Remark'),
		
		## Module Requirement Info
		
		'rfq_name': fields.char('Alias Name', size=64),
		'rfq_type': fields.selection([('direct','Direct'),('from_pi','From PI')],'RFQ Type',required=True),
		'quotation_date': fields.date('RFQ Date'),
		'quote_submission_date': fields.date('Due Date'),
		'user_id': fields.many2one('res.users', 'Requested By'),
		#~ 'requisition_line_ids': fields.many2many('purchase.requisition.line', 'kg_rfq_pi_lines','quote_id','requisition_id','Purchase Indent Lines',domain="[('pending_qty','>','0'), '&',('line_state','=','process'), '&',('draft_flag','=', False)]",),
		'requisition_line_ids': fields.many2many('purchase.requisition.line', 'kg_rfq_pi_lines','quote_id','requisition_id','Purchase Indent Lines',domain="['&',('requisition_id.state','=','approved'),('src_type','in',('direct','frompi'))]"),
		'visible_quote': fields.boolean('Quote Visible'),
		'line_flag': fields.boolean('Line Flag'),
		
		## Child Tables Declaration
		
		'line_id': fields.one2many('kg.rfq.vendor.selection.line', 'header_id', 'Entries'),
		'vendor_ids': fields.one2many('kg.rfq.vendor.list', 'header_id', 'Vendors' ),
		
		## Entry Info
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'created_by': fields.many2one('res.users','Created By',readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'ap_rej_date': fields.datetime('Approved/Rejected Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Rejected By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date' : fields.datetime('Last Updated Date',readonly=True),
		'update_user_id' : fields.many2one('res.users','Last Updated By',readonly=True),
		
	}
	
	_defaults = {
		
		'name': '/',
		'visible_quote': False,
		'state': 'draft',
		'quotation_date': lambda *a: time.strftime('%Y-%m-%d'),
		'user_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
		'created_by': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
		'crt_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.rfq.vendor.selection', context=c),
		'active': True,
		'line_flag': False,
		
	}
	
	def _line_validations(self,cr,uid,ids,context = None):
		entry = self.browse(cr,uid,ids[0])
		quote_ven_obj = self.pool.get('kg.rfq.vendor.list')
		if entry.rfq_type == 'from_pi':
			if not entry.requisition_line_ids:
				raise osv.except_osv(_('Warning !'),_('You cannot Confirm the record without Indent details !!'))
		if entry.vendor_ids:
			vendor_line_ids = quote_ven_obj.search(cr, uid, [('header_id','=',entry.id)])
			if len(vendor_line_ids) > 5:
				raise osv.except_osv(_('Warning !'),_('Select only five Vendors for comparision !!'))
			for line in entry.vendor_ids:
				dup_ids = self.pool.get('kg.rfq.vendor.list').search(cr,uid,[('partner_id','=',line.partner_id.id),('header_id','=',entry.id)])
				if dup_ids:
					if len(dup_ids) > 1:
						raise osv.except_osv(_('Warning !'),_('Vendor (%s) duplicate not accepted !!'%(line.partner_id.name)))
		return True
	
	_constraints = [
		(_line_validations, 'You cannot Confirm the record without line entry !', ['']),
	]
	
	def line_validations(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if not entry.line_id:
			raise osv.except_osv(_('Warning !'),_('You cannot Confirm the record without Quotation details !!'))
		if not entry.vendor_ids:
			raise osv.except_osv(_('Warning !'),_('You cannot Confirm the record without Vendor details !!'))
		for line in entry.line_id:
			print"line.product_uom_id.id",line.product_uom_id.name
			print"line.uom_po_id.id",line.product_id.uom_po_id.id
			print"line.uom_id.id",line.product_id.uom_id.id
			if line.product_uom_id.id == line.product_id.uom_po_id.id or line.product_uom_id.id == line.product_id.uom_id.id:
				pass
			else:
				raise osv.except_osv(_('UOM Mismatching Error !'),
					_('You choosed wrong UOM and you can choose either %s or %s for %s !!') % (line.product_id.uom_id.name,line.product_id.uom_po_id.name,line.product_id.name))			
			if line.quotation_qty <= 0:
				raise osv.except_osv(_('Warning !'),_('Product (%s) RFQ Qty should be greater than Zero !!'%(line.product_id.name)))
		return True
	
	def proceed(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			pi_line_obj = self.pool.get('purchase.requisition.line')
			line_obj = self.pool.get('kg.rfq.vendor.selection.line')
			vendor_obj = self.pool.get('kg.rfq.vendor.list')
			for quote in self.browse(cr, uid, ids, context=context):
				tmp_ids = []
				del_sql = """ delete from kg_rfq_vendor_selection_line where header_id = %s """ %(ids[0])
				cr.execute(del_sql)
				ven_sql = """ delete from kg_rfq_vendor_list where header_id = %s """ %(ids[0])
				cr.execute(ven_sql)
				cr.execute("""select requisition_id from kg_rfq_pi_lines where quote_id = %s"""%(quote.id))
				data = cr.dictfetchall()
				for pi_lines in data:
					line_ids = pi_lines['requisition_id']
					tree = pi_line_obj.browse(cr, uid, line_ids, context)
					for item in tree.product_id.pro_seller_ids:
						vendor_line_ids = self.pool.get('kg.rfq.vendor.list').search(cr,uid,[('header_id','=',rec.id),('partner_id','=',item.name.id)])
						tot_add = (item.name.street or '')+ ' ' + (item.name.street2 or '') + '\n'+(item.name.city_id.name or '')+ ',' +(item.name.state_id.name or '') + '-' +(item.name.zip or '') + '\nPh:' + (item.name.phone or '')+ '\n' +(item.name.mobile or '')
						if vendor_line_ids:
							pass
						else:
							vendor_ids = vendor_obj.create(cr,uid,{'partner_id':item.name.id,'header_id':rec.id,'partner_address':tot_add,'entry_mode':'auto'})
					pi_line_obj.write(cr, uid, pi_lines['requisition_id'], {'src_type':'fromquote'})
					name = 'name'
					cr.execute(''' insert into kg_rfq_vendor_selection_line (create_date,create_uid,name,state,purchase_requisition_id,header_id,quotation_qty,product_uom_id,purchase_requisition_line_id,product_id,brand_id,moc_id_temp,moc_id,requested_qty,product_name,due_date,rfq_type)
					values(now(),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',[uid,name, 'draft',tree.requisition_id.id,quote.id,tree.product_qty,tree.product_uom_id.id,tree.id,tree.product_id.id,tree.brand_id.id,tree.moc_id_temp.id,tree.moc_id.id,tree.product_qty,tree.product_id.name,rec.quote_submission_date,rec.rfq_type])	
			self.write(cr,uid,ids,{'line_flag':True})
		return True
	
	def confirm_rfq(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			
			self.line_validations(cr,uid,ids)
			
			self.write(cr,uid,rec.id,{'state':'confirm',
									  'line_flag':False,
									  'confirm_date':time.strftime('%m/%d/%Y %H:%M:%S'),
									  'confirm_user_id':uid
									  })
		return True
	
	def approve_rfq(self, cr, uid, ids, context=None):
		vendor = []
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirm':
			
			self.line_validations(cr,uid,ids)
			
			rfq_pi_obj = self.pool.get('kg.rfq.vendor.selection.line')
			quote_pi_obj = self.pool.get('kg.quote.pi.line')
			quote_ven_obj = self.pool.get('kg.rfq.vendor.list')
			quote_header_obj = self.pool.get('kg.quotation.requisition.header')
			quote_line_obj = self.pool.get('kg.quotation.requisition.line')
			
			seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.rfq.vendor.selection')])
			seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,rec.quotation_date))
			seq_name = cr.fetchone();
			duplicate_ids = quote_header_obj.search(cr, uid, [('rfq_no_id','=',rec.id)])
			
			if duplicate_ids == []:
				header_vals = {
					'quotation_date': rec.quotation_date,
					'user_id': rec.user_id.id,
					'state': 'draft',
					'rfq_no_id': rec.id,
				}
				quote_header_id = quote_header_obj.create(cr, uid, header_vals)
				if quote_header_id:
					ven_list = []
					vendor_line_ids = quote_ven_obj.search(cr, uid, [('header_id','=',rec.id)])
					for lines in vendor_line_ids:
						ven_rec = quote_ven_obj.browse(cr, uid, lines, context)
						quote_ven_obj.write(cr, uid, [ven_rec.id], {'state':'approved'})
						name_ref = seq_name[0]
						line_vals = {
							'header_id': quote_header_id,
							'user_id': rec.user_id.id,
							'partner_id': ven_rec.partner_id.id,
							'user_ref_id': ven_rec.partner_id.user_ref_id.id,
							'partner_address': ven_rec.partner_address,
							'name': name_ref,
							'rfq_ven_id': rec.id,
							'state': 'draft',
							'rfq_date': rec.quotation_date,
							'due_date': rec.quote_submission_date,
						}
						
						quote_line_id = quote_line_obj.create(cr, uid, line_vals)
						
						for line in rec.line_id:
							rfq_pi_obj.write(cr, uid, line.id, {'state':'approved'})
							line_vals = {
								'name': 'name',
								'rfq_no_id': rec.id ,
								'header_id': quote_line_id,
								'user_id': rec.user_id.id,
								'product_id': line.product_id.id,
								'product_name': line.product_name,
								'brand_id': line.brand_id.id,
								'moc_id_temp': line.moc_id_temp.id,
								'moc_id': line.moc_id.id,
								'product_uom_id': line.product_uom_id.id,
								'requested_qty': line.requested_qty,
								'quotation_qty': line.quotation_qty,
								'state': 'draft',
								'rfq_date': rec.quotation_date,
								'partner_id':ven_rec.partner_id.id,
								'partner_address': ven_rec.partner_address,
								'partner_name': ven_rec.partner_name,	
								'vendors_price': 1,
								'ven_del_date': rec.quote_submission_date,
							}
							quote_pi_id = quote_pi_obj.create(cr, uid, line_vals)
						ven_list.append(ven_rec.partner_id.id)
					tmp_list = list(set(ven_list))
					if len(tmp_list) != len(vendor_line_ids):
						raise osv.except_osv(_('Warning !'),_('Vendor shoud be unique !!'))
			
			self.write(cr, uid, ids, {'state': 'rfq_approved', 
									  'name': seq_name[0],
									  'ap_rej_date': time.strftime('%m/%d/%Y %H:%M:%S'),
									  'ap_rej_user_id': uid,
									})
		
		return True
	
	def reject_rfq(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirm':
			if not rec.reject_remark:
				raise osv.except_osv(_('Warning !'),_('Enter Reject Remark !!'))
			self.write(cr,uid,rec.id,{'state':'draft','ap_rej_date':time.strftime('%m/%d/%Y %H:%M:%S'),'ap_rej_user_id':uid})
		return True
	
	def cancel_rfq(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'rfq_approved':
			self.write(cr,uid,rec.id,{'state':'cancel','cancel_date':time.strftime('%m/%d/%Y %H:%M:%S'),'cancel_user_id':uid})
		return True
	
	def write(self, cr, uid, ids, vals, context=None):		
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_rfq_vendor_selection, self).write(cr, uid, ids, vals, context)
		
kg_rfq_vendor_selection() 

class kg_rfq_vendor_list(osv.osv):
	
	_name = "kg.rfq.vendor.list"
	_order = 'partner_name asc'
	
	_columns = {
		
		## Basic Info
		
		'header_id': fields.many2one('kg.rfq.vendor.selection','Header Id',required=True,ondelete='cascade'),
		'state': fields.selection([('draft','Draft'),('approved','Approved')],'Status'),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode',readonly=True),
		## Module Requirement Info
		
		'partner_id': fields.many2one('res.partner','Vendor',domain="[('supplier','=',1)]",required=True),
		'partner_address': fields.char('Vendor Address',size=200, ),
		'partner_name': fields.related('partner_id','name',type='char',string="Vendor Name",size=200,store=True),
		
		## Entry Info
		
		'active': fields.boolean('Active'),
		
	}
	
	_defaults = {
		
		'active':True,
		'state':'draft',
		'entry_mode':'manual',
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		return context
	
	def onchange_partner_id(self, cr, uid, ids, partner_id):
		partner = self.pool.get('res.partner')
		if partner_id:
			supplier_address = partner.address_get(cr, uid, [partner_id], ['default'])
			supplier = partner.browse(cr, uid, partner_id)
			tot_add = (supplier.street or '')+ ' ' + (supplier.street2 or '') + '\n'+(supplier.city_id.name or '')+ ',' +(supplier.state_id.name or '') + '-' +(supplier.zip or '') + '\nPh:' + (supplier.phone or '')+ '\n' +(supplier.mobile or '')		
			return {'value': {
				'partner_address' : tot_add or False
				}}
	
kg_rfq_vendor_list()

class kg_rfq_vendor_selection_line(osv.osv):
	
	_name = 'kg.rfq.vendor.selection.line'
	
	_columns = {
		
		## Basic Info
		
		'name': fields.char('Name',size=128),
		'state': fields.selection([('draft','Draft'),('approved','Approved')],'Status',readonly=True),
		'rfq_type': fields.selection([('direct','Direct'),('from_pi','From PI')],'RFQ Type'),
		'remarks': fields.text('Remarks'),
		
		## Module Requirement Info
		
		'product_id': fields.many2one('product.product', 'Product'),
		'product_name': fields.related('product_id', 'name', type='char', string='Product Name', store=True, size=300),
		'product_uom_id': fields.related('product_id','uom_id',type='many2one',relation='product.uom',string='Product UOM', store=True),
		'requested_qty': fields.float('Purchase Indent Approved Qty', digits=(16,3)),
		'quotation_qty': fields.float('RFQ Qty', digits=(16,3), ),
		'header_id': fields.many2one('kg.rfq.vendor.selection', 'Header', ondelete="cascade", ),
		'purchase_requisition_id': fields.many2one('purchase.requisition', 'Material Requisition No.', ),
		'purchase_requisition_line_id': fields.many2one('purchase.requisition.line', 'Material Requisition No.'),
		'vendor_ids': fields.one2many('kg.rfq.vendor.list','header_id','Vendors'),
		'due_date': fields.date('Due Date'),
		'brand_id': fields.many2one('kg.brand.master','Brand',domain="[('product_ids','in',(product_id)),('state','in',('draft','confirmed','approved'))]"),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'moc_id_temp': fields.many2one('ch.brandmoc.rate.details','MOC',domain="[('brand_id','=',brand_id),('header_id.product_id','=',product_id),('header_id.state','in',('draft','confirmed','approved'))]"),
		'revised_flag': fields.boolean('Revised Button Flag'),
		
	}
	
	_defaults = {
		
		'name': '/',
		'state': 'draft',
		'revised_flag': False,
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		print"contextcontextcontextcontext",context
		return context
	
	def create(self, cr, uid, vals, context=None):
		return super(kg_rfq_vendor_selection_line, self).create(cr, uid, vals, context=context)
	
	def onchange_uom_id(self, cr, uid, ids, product_id, product_uom_id, context=None):
		value = {'product_uom_id': ''}
		if product_id and product_uom_id:
			pro_rec = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			if product_uom_id == pro_rec.uom_id.id or product_uom_id == pro_rec.uom_po_id.id:
				pass
			else:
				raise osv.except_osv(_('UOM Mismatching Error !'),
					_('You choosed wrong UOM and you can choose either %s or %s for %s !!') % (pro_rec.uom_id.name,pro_rec.uom_po_id.name,pro_rec.name))
			value = {'product_uom_id':product_uom_id}
		return {'value': value}
	
	def onchange_moc(self, cr, uid, ids, moc_id_temp):
		value = {'moc_id':''}
		if moc_id_temp:
			rate_rec = self.pool.get('ch.brandmoc.rate.details').browse(cr,uid,moc_id_temp)
			value = {'moc_id': rate_rec.moc_id.id}
		return {'value': value}
	
	def onchange_product_name(self, cr, uid, ids, product_id):
		value = {'product_name':'','brand_id':'','moc_id_temp':'','product_uom_id':''}
		if product_id:
			prod_rec = self.pool.get('product.product').browse(cr,uid,product_id)
			value = {'product_name': prod_rec.name,'brand_id':'','moc_id_temp':'','product_uom_id':''}
		return {'value': value}
	
kg_rfq_vendor_selection_line()

class kg_quotation_requisition_header(osv.osv):
	
	_name = 'kg.quotation.requisition.header'
	
	_columns = {
		
		## Basic Info
		
		'name': fields.char('Quotation Reference',size=32,readonly=True),
		'revision_remarks': fields.text('Reveision Remarks'),
		'reject_remarks': fields.text('Reject Remarks'),
		'quotation_date': fields.date('RFQ Date', readonly=True),
		'state': fields.selection([('draft', 'Draft'),('approved', 'Approved'),('reject', 'Rejected'),('revised', 'Revised')], 'State',readonly=True),
		
		## Module Requirement Info
		
		'revision': fields.integer('Revision'),
		'user_id': fields.many2one('res.users','Requested By',readonly=True),
		'rfq_no_id': fields.many2one('kg.rfq.vendor.selection','No.',required=True,),		
		'revised_flag': fields.boolean('Revised Button Flag'),
		
		## Child Tables Declaration
		
		'line_ids': fields.one2many('kg.quotation.requisition.line','header_id','RFQ Lines',readonly=False,states={'approved':[('readonly',True)],'reject':[('readonly',True)]}),
		
		## Entry Info
		
		'active': fields.boolean('Active'),
		
	}
	_defaults = {
		
		'user_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
		'quotation_date': lambda *a: time.strftime('%Y-%m-%d'),
		'state': 'draft',
		'name': '/',
		'active': True,
		'revised_flag': False,
		
	}
	
	_order = 'id desc'
	
	def line_validations(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		for lines in rec.line_ids:
			if not lines.freight_type:
				raise osv.except_osv(_('Warning !'),
					_('(%s) Freight should be select for this Vendor (%s) !!'%(lines.name,lines.partner_id.name)))
			if not lines.other_charges:
				raise osv.except_osv(_('Warning !'),
					_('(%s) Other Charges should be select for this Vendor (%s) !!'%(lines.name,lines.partner_id.name)))
			if not lines.tax_type:
				raise osv.except_osv(_('Warning !'),
					_('(%s) Tax should be select for this Vendor (%s) !!'%(lines.name,lines.partner_id.name)))
			if lines.pi_line_ids:
				for quotes in lines.pi_line_ids:
					if quotes.vendors_price <= 0:
						raise osv.except_osv(_('Warning !'),
							_('(%s) Unit Price should be greater than Zero for this Vendor (%s) !!'%(quotes.product_id.name,lines.partner_id.name)))
		return True
	
	def create_revision1(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			if not rec.revision_remarks:
				raise osv.except_osv(_('Warning !'),_('Enter Revision Remarks !!'))
			self.write(cr, uid, ids[0], {'state': 'revised'})
			var = rec.revision + 1
			vals = {
					'state': 'draft',
					'revision': var,
					}
			new_rec = self.copy(cr, uid, ids[0], vals, context)
		return True
	
	def app_quotation(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			
			self.line_validations(cr,uid,ids)
			
			rfq_ven_obj = self.pool.get('kg.rfq.vendor.selection')
			rfq_ven_lin_obj = self.pool.get('kg.rfq.vendor.selection.line')
			line_obj = self.pool.get('kg.quotation.requisition.line')
			quo_lin_obj = self.pool.get('kg.quote.pi.line')
			for lines in rec.line_ids:
				if lines.pi_line_ids:
					for quotes in lines.pi_line_ids:
						quo_lin_obj.write(cr,uid,quotes.id,{'state':'approved'})
				line_obj.write(cr,uid,lines.id,{'state':'approved'})
			rfq_ven_rec = rfq_ven_obj.browse(cr, uid, rec.rfq_no_id.id)
			rfq_ven_obj.write(cr, uid, [rec.rfq_no_id.id], {'state':'rfq_approved'})
			self.write(cr, uid, ids, {'state':'approved'})
		
		return True
	
	def rej_quotation(self, cr, uid, ids, context=None):
		for custom in self.browse(cr, uid, ids, context):
			if not custom.reject_remarks:
				raise osv.except_osv(_('Warning !'),_('Enter Reject Remarks !!'))
			self.write(cr, uid, ids, {'state':'reject'})
		return True	
	
	def _lines_check(self,cr,uid,ids,context = None):
		quote_pi_obj = self.pool.get('kg.quote.pi.line')
		entry = self.browse(cr,uid,ids[0])
		if entry.state != 'draft':
			if not entry.line_ids:
				return False
			for loop in entry.line_ids:
				if loop.cmp_flag == True:
					if not loop.pi_line_ids:
						raise osv.except_osv(_('Warning !'),_('In Supplier details Product detail is must for this RFQ No. (%s) product (%s) !!'%(loop.name,items.product_id.name)))
					for items in loop.pi_line_ids:
						if items.vendors_price <= 0:
							raise osv.except_osv(_('Warning !'),_('Unit Price should be greater than Zero for this (%s) !!'%(items.product_id.name)))
		return True
	
	_constraints = [
			(_lines_check, 'Supplier Detail is must !!', ['']),
		]
	
kg_quotation_requisition_header()

class kg_quotation_requisition_line(osv.osv):
	
	_name = 'kg.quotation.requisition.line'
	_order = 'id desc'
	
	_columns = {
		
		## Basic Info
		
		'header_id': fields.many2one('kg.quotation.requisition.header', 'Quotation Header'),
		'name': fields.char('RFQ No', size=32, readonly=True),
		'rfq_date': fields.date('RFQ Date', readonly=True),
		'state': fields.selection([('draft', 'Draft'),('approved', 'Submitted')], 'State',readonly=True),
		'note': fields.text('Notes'),
		'remarks': fields.text('RFQ Remarks'),
		
		## Module Requirement Info
		
		'rfq_ven_id': fields.many2one('kg.rfq.vendor.selection', 'RFQ No.'),
		'due_date': fields.date('Due Date', readonly=True),
		'user_id': fields.many2one('res.users', 'Requested By'),
		'user_ref_id': fields.many2one('res.users', 'Ref User'),
		'partner_id':fields.many2one('res.partner','Vendor',size=120,readonly=True,),
		'partner_address': fields.char('Vendor Address',size=200, readonly=True, ),
		'email':fields.char('Email', size=128,readonly=True,),
		'mail_flag': fields.boolean('Vendor Mail'),
		'cmp_flag': fields.boolean('Allow Vendor For Comparison'),
		'freight_type':fields.selection([('Inclusive','Inclusive'),('Extra','Extra'),('To Pay','To Pay'),('Paid','Paid'),('Extra at our Cost','Extra at our Cost')], 'Freight'), 		
		'tax_type': fields.selection([('inclusive', 'Inclusive'),('exclusive', 'Exclusive'),], 'Tax'),
		'other_charges': fields.selection([('applicable', 'Applicable'),('notapplicable', 'Not Applicable'),], 'Other Charges'),		
		'line_state': fields.selection([('pending','Pending'),('submit','Submitted')],'Status',readonly=True),
		
		## Child Tables Declaration
		
		'pi_line_ids': fields.one2many('kg.quote.pi.line', 'header_id', 'PI Lines', readonly=True, states={'draft':[('readonly',False)]}),
		
		## Entry Info
		
		'active': fields.boolean('Active'),
		
	}
	
	_defaults = {
		
		'line_state': 'pending',
		'user_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
		'rfq_date': lambda *a: time.strftime('%Y-%m-%d'),
		'state': 'draft',
		'cmp_flag': True,
		'active': True,
		'name': '/',
		
		}
	
	def _email_check(self,cr,uid,ids,context = None):
		entry = self.browse(cr,uid,ids[0])
		if entry.email:
			if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", entry.email) != None:
				return True
			else:
				raise osv.except_osv(_('Warning !'),_('Please enter a valid email address for this (%s) !!'%(entry.partner_id.name)))
		else:
			return True
		return True
	
	_constraints = [
			(_email_check, 'Please enter valid email', ['']),
		]
	
	def create_revision(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		quote_lines_ids = self.pool.get('kg.quote.pi.line').search(cr, uid, [('header_id','=',rec.id)], context=context)
		self.write(cr, uid, ids[0], {'state': 'revised'})
		var = rec.revision + 1
		vals = {
				'state': 'draft',
				'revision': var,
				}
		new_rec = self.copy(cr, uid, ids[0], vals, context)
		return True	
	
	def entry_submit(self, cr, uid, ids, context=None):
		rfq_ven_obj = self.pool.get('kg.rfq.vendor.selection')
		rfq_ven_lin_obj = self.pool.get('kg.rfq.vendor.selection.line')
		line_obj = self.pool.get('kg.quotation.requisition.line')
		quo_lin_obj = self.pool.get('kg.quote.pi.line')
		total = 0
		for custom in self.browse(cr, uid, ids, context):
			if custom.pi_line_ids:
				for quotes in custom.pi_line_ids:
					quo_lin_obj.write(cr,uid,quotes.id,{'state':'approved'})
			self.write(cr, uid, ids, {'state':'approved'})		
			self_rec = self.search(cr,uid,[('rfq_ven_id','=',custom.rfq_ven_id.id)])
			app_rec = self.search(cr,uid,[('rfq_ven_id','=',custom.rfq_ven_id.id),('state','=','approved')])
			if len(self_rec) == len(app_rec):			
				rfq_ven_obj.write(cr, uid, quotes.rfq_no_id.id, {'state':'rfq_approved'})
				quote_header_obj = self.pool.get('kg.quotation.requisition.header').search(cr,uid,[('rfq_no_id','=',custom.rfq_ven_id.id)])
				quote_header_rec = self.pool.get('kg.quotation.requisition.header').browse(cr,uid,quote_header_obj[0])
				self.pool.get('kg.quotation.requisition.header').write(cr,uid,quote_header_rec.id,{'state':'approved'})
			else:
				pass
			
			self.write(cr, uid, ids, {'state':'approved','line_state':'submit'})			
		
		return True	
		
kg_quotation_requisition_line()

class kg_quote_pi_line(osv.osv):
	
	_name = 'kg.quote.pi.line'
	_order = 'id desc'
	
	def _value_calculation(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		for entry in self.browse(cr, uid, ids, context=context):
			res[entry.id] = {
				'vendors_value': 0.0,
			}
			res[entry.id]['vendors_value']= (round((entry.quotation_qty * entry.vendors_price),0))
		return res
	
	_columns = {
		
		## Basic Info
		
		'header_id': fields.many2one('kg.quotation.requisition.line', 'Quotation Line'),
		'name': fields.char('RFQ No', size=32, readonly=True),
		'state': fields.selection([('draft', 'Draft'),('approved', 'Approved'),('revised', 'Revised'),], 'State'),
		
		## Module Requirement Info
		
		'rfq_no_id': fields.many2one('kg.rfq.vendor.selection', 'rfq no'),
		'revision': fields.integer('Revision'),
		'product_id': fields.many2one('product.product', 'Product', readonly=True),
		'product_name': fields.related('product_id', 'name', type='char', string='Product Name', readonly=True, store=True, size=300),
		'product_uom_id': fields.related('product_id','uom_id', type='many2one', relation='product.uom', string='Product UOM', store=True,readonly=True),
		'requested_qty': fields.float('Purchase Indent Approved Qty', digits=(16,3),readonly=True),
		'quotation_qty': fields.float('RFQ Qty', digits=(16,3),readonly=True),
		'partner_id':fields.many2one('res.partner','Vendor',size=120,readonly=True,),
		'partner_address': fields.char('Partner Address',size=200, readonly=True, ),
		'partner_name': fields.related('partner_id','name',type='char', string="Vendor Name", size=200, store=True),
		'vendors_price':fields.float('Unit Price',required=True),
		'brand_id': fields.many2one('kg.brand.master','Brand', readonly=True),
		'moc_id': fields.many2one('kg.moc.master','MOC',readonly=True),
		'moc_id_temp': fields.many2one('ch.brandmoc.rate.details','MOC',domain="[('brand_id','=',brand_id),('header_id.product_id','=',product_id),('header_id.state','in',('draft','confirmed','approved'))]",readonly=True),
		'del_date': fields.date('Delivery Date', readonly=True),
		'ven_del_date': fields.date('Vendor Delivery Date'),
		'vendors_value': fields.function(_value_calculation,  string='Delivery Charges', multi="sums", help="The amount without tax", type='float',store=True,track_visibility='always'),
		
	}
	
	_defaults = {
		
		'state': 'draft',
		'name': '/',
		
	}
	
	def _check_price(self,cr,uid,ids,context = None):
		rec = self.browse(cr,uid,ids[0])
		if rec.vendors_price <= 0.00:
			raise osv.except_osv(_('Warning !'),_('System not allow to save with Unit Price as Zero for this (%s) !!'%(rec.product_id.name)))
		else:
			return True
			
	_constraints = [        
		
        (_check_price, 'System not allow to save with Unit Price as Zero !',['Unit Price']),
        
       ]
	
	def onchange_price(self, cr, uid, ids, quotation_qty,vendors_price,vendors_value):
		val = {'vendors_value':''}
		qty = quotation_qty
		price = vendors_price
		tot = qty * price
		val = {'vendors_value':tot}
		return {'val': val}	
	
	#~ def write(self, cr, uid, ids, vals, context=None):	
		#~ value = 0 
		#~ value = vals['quotation_qty'] * vals['vendors_price']
		#~ vals.update({'vendors_value': value})
		#~ return super(kg_quote_pi_line, self).write(cr, uid, ids, vals, context)
	
kg_quote_pi_line()

class kg_quotation_entry_header(osv.osv):
	
	_name = 'kg.quotation.entry.header'
	_order = 'id desc'
	
	_columns = {
		
		## Basic Info
		
		'name': fields.char('Quotation No.', size=500,readonly=True),
		'state': fields.selection([('draft', 'Draft'),('confirmed', 'WFA'),('approved', 'Approved'),('cancel', 'Cancel'),('po_generate', 'PO Generated'),], 'State',readonly=True),
		'comparison_remarks': fields.text('Remarks'),
		'remarks': fields.text('Approve/Reject Remarks'),
		
		## Module Requirement Info
		
		'rfq_name': fields.char('Alias Name', size=500),
		'comparision_date':fields.date('Comparison Date', readonly=True),
		'rfq_date':fields.date('RFQ Date'),
		'user_id': fields.many2one('res.users', 'Requested By'),
		'rfq_no_id':fields.many2one('kg.rfq.vendor.selection', 'RFQ No', domain="[('state','=','rfq_approved'), ('visible_quote','=',0)]",required=True, ), 
		'product_id': fields.related('line_ids','product_id', type='many2one', relation='product.product', string='Product', domain="[('defaultproduct','!=',1),('new_state','=','approved')]"),		
		'quote_list_flag': fields.boolean('Quote List Flag'),
		'vendor_1_id': fields.many2one('res.partner', 'Vendor 1' , readonly=True),
		'vendor_2_id': fields.many2one('res.partner', 'Vendor 2' , readonly=True),
		'vendor_3_id': fields.many2one('res.partner', 'Vendor 3' , readonly=True),
		'vendor_4_id': fields.many2one('res.partner', 'Vendor 4' , readonly=True),
		'vendor_5_id': fields.many2one('res.partner', 'Vendor 5' , readonly=True),
		'vendor_1_name': fields.char('Vendor One Name', size=500, ),
		'vendor_2_name': fields.char('Vendor Two Name', size=500, ),
		'vendor_3_name': fields.char('Vendor Three Name', size=500, ),
		'vendor_4_name': fields.char('Vendor Four Name', size=500, ),
		'vendor_5_name': fields.char('Vendor Five Name', size=500, ),
		'vendor_1_flag': fields.boolean('Vendor Flag 1'),
		'vendor_2_flag': fields.boolean('Vendor Flag 2'),
		'vendor_3_flag': fields.boolean('Vendor Flag 3'),
		'vendor_4_flag': fields.boolean('Vendor Flag 4'),
		'vendor_5_flag': fields.boolean('Vendor Flag 5'),
		
		'generate_po_flag': fields.boolean('PO Flag'),
		
		'vendor_1_freight': fields.char('Vendor Freight Type.', size=30, readonly=True, states={'draft':[('readonly',True)]}),
		'vendor_2_freight': fields.char('Vendor Freight Type.', size=30, readonly=True, states={'draft':[('readonly',True)]}),
		'vendor_3_freight': fields.char('Vendor Freight Type.', size=30, readonly=True, states={'draft':[('readonly',True)]}),
		'vendor_4_freight': fields.char('Vendor Freight Type.', size=30, readonly=True, states={'draft':[('readonly',True)]}),
		'vendor_5_freight': fields.char('Vendor Freight Type.', size=30, readonly=True, states={'draft':[('readonly',True)]}),
		
		'vendor_1_tax': fields.char('Vendor Tax Type.', size=30, readonly=True, states={'draft':[('readonly',True)]}),
		'vendor_2_tax': fields.char('Vendor Tax Type.', size=30, readonly=True, states={'draft':[('readonly',True)]}),
		'vendor_3_tax': fields.char('Vendor Tax Type.', size=30, readonly=True, states={'draft':[('readonly',True)]}),
		'vendor_4_tax': fields.char('Vendor Tax Type.', size=30, readonly=True, states={'draft':[('readonly',True)]}),
		'vendor_5_tax': fields.char('Vendor Tax Type.', size=30, readonly=True, states={'draft':[('readonly',True)]}),
		
		'vendor_1_others': fields.char('Vendor Others.', size=30, readonly=True, states={'draft':[('readonly',True)]}),
		'vendor_2_others': fields.char('Vendor Others.', size=30, readonly=True, states={'draft':[('readonly',True)]}),
		'vendor_3_others': fields.char('Vendor Others.', size=30, readonly=True, states={'draft':[('readonly',True)]}),
		'vendor_4_others': fields.char('Vendor Others.', size=30, readonly=True, states={'draft':[('readonly',True)]}),
		'vendor_5_others': fields.char('Vendor Others.', size=30, readonly=True, states={'draft':[('readonly',True)]}),
		'vendor_reference_no_vendor_1': fields.char('Vendor Reference No.', size=30, readonly=True, states={'draft':[('readonly',False)]}),
		'vendor_reference_no_vendor_2': fields.char('Vendor Reference No.', size=30, readonly=True, states={'draft':[('readonly',False)]}),
		'vendor_reference_no_vendor_3': fields.char('Vendor Reference No.', size=30, readonly=True, states={'draft':[('readonly',False)]}),
		'vendor_reference_no_vendor_4': fields.char('Vendor Reference No.', size=30, readonly=True, states={'draft':[('readonly',False)]}),
		'vendor_reference_no_vendor_5': fields.char('Vendor Reference No.', size=30, readonly=True, states={'draft':[('readonly',False)]}),
		
		'vendor_reference_date_vendor_1': fields.date('Vendor Reference Date', readonly=True, states={'draft':[('readonly',False)]}),
		'vendor_reference_date_vendor_2': fields.date('Vendor Reference Date', readonly=True, states={'draft':[('readonly',False)]}),
		'vendor_reference_date_vendor_3': fields.date('Vendor Reference Date', readonly=True, states={'draft':[('readonly',False)]}),
		'vendor_reference_date_vendor_4': fields.date('Vendor Reference Date', readonly=True, states={'draft':[('readonly',False)]}),
		'vendor_reference_date_vendor_5': fields.date('Vendor Reference Date', readonly=True, states={'draft':[('readonly',False)]}),
		
		'quotation_validity_vendor_1': fields.integer('Quotation Validity', readonly=True, states={'draft':[('readonly',False)]}),
		'quotation_validity_vendor_2': fields.integer('Quotation Validity', readonly=True, states={'draft':[('readonly',False)]}),
		'quotation_validity_vendor_3': fields.integer('Quotation Validity', readonly=True, states={'draft':[('readonly',False)]}),
		'quotation_validity_vendor_4': fields.integer('Quotation Validity', readonly=True, states={'draft':[('readonly',False)]}),
		'quotation_validity_vendor_5': fields.integer('Quotation Validity', readonly=True, states={'draft':[('readonly',False)]}),
		
		'enquiry_type_vendor_1': fields.selection([('phone','Phone'),('email','Email'),('fax','Fax'),('others','Others')],'Enquiry Type', readonly=True, states={'draft':[('readonly',False)]}),
		'enquiry_type_vendor_2': fields.selection([('phone','Phone'),('email','Email'),('fax','Fax'),('others','Others')],'Enquiry Type', readonly=True, states={'draft':[('readonly',False)]}),
		'enquiry_type_vendor_3': fields.selection([('phone','Phone'),('email','Email'),('fax','Fax'),('others','Others')],'Enquiry Type', readonly=True, states={'draft':[('readonly',False)]}),
		'enquiry_type_vendor_4': fields.selection([('phone','Phone'),('email','Email'),('fax','Fax'),('others','Others')],'Enquiry Type', readonly=True, states={'draft':[('readonly',False)]}),
		'enquiry_type_vendor_5': fields.selection([('phone','Phone'),('email','Email'),('fax','Fax'),('others','Others')],'Enquiry Type', readonly=True, states={'draft':[('readonly',False)]}),
		
		## Child Tables Declaration
		
		'line_ids': fields.one2many('kg.quotation.entry.lines', 'header_id', string='quotes',readonly=True),
		'line_ids_vendor1': fields.one2many('kg.quotation.entry.lines', 'header_id', string='quotes',),
		'line_ids_vendor2': fields.one2many('kg.quotation.entry.lines', 'header_id', string='quotes',),
		'line_ids_vendor3': fields.one2many('kg.quotation.entry.lines', 'header_id', string='quotes',),
		'line_ids_vendor4': fields.one2many('kg.quotation.entry.lines', 'header_id', string='quotes',),
		'line_ids_vendor5': fields.one2many('kg.quotation.entry.lines', 'header_id', string='quotes',),
		
		## Entry Info
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Approved By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		
	}
	
	_defaults = {
		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.quotation.entry.header', context=c),
		'user_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
		'comparision_date': lambda *a: time.strftime('%Y-%m-%d'),
		'state': 'draft',
		'vendor_1_name': 'Vendor One',
		'vendor_2_name': 'Vendor Two',
		'vendor_3_name': 'Vendor Three',
		'vendor_4_name': 'Vendor Four',
		'vendor_5_name': 'Vendor Five',
		'quote_list_flag': False,
		'vendor_1_flag': True,
		'vendor_2_flag': False,
		'vendor_3_flag': False,
		'vendor_4_flag': False,
		'vendor_5_flag': False,
		'active': True,
		
	}
	
	def select_vendor_1(self, cr, uid, ids, context=None):
		for hdr in self.browse(cr, uid, ids, context):
			cr.execute('''update kg_quotation_entry_lines set 
			vendor_1_select=%s,vendor_2_select=%s,vendor_3_select=%s,vendor_4_select=%s,vendor_5_select=%s
			where header_id = %s''',(True,False,False,False,False,hdr.id))
		return True
	
	def select_vendor_2(self, cr, uid, ids, context=None):
		for hdr in self.browse(cr, uid, ids, context):
			cr.execute('''update kg_quotation_entry_lines set 
			vendor_1_select=%s,vendor_2_select=%s,vendor_3_select=%s,vendor_4_select=%s,vendor_5_select=%s
			where header_id = %s''',(False,True,False,False,False,hdr.id))
		return True
		
	def select_vendor_3(self, cr, uid, ids, context=None):
		for hdr in self.browse(cr, uid, ids, context):
			cr.execute('''update kg_quotation_entry_lines set 
			vendor_1_select=%s,vendor_2_select=%s,vendor_3_select=%s,vendor_4_select=%s,vendor_5_select=%s
			where header_id = %s''',(False,False,True,False,False,hdr.id))
		return True
	
	def select_vendor_4(self, cr, uid, ids, context=None):
		for hdr in self.browse(cr, uid, ids, context):
			cr.execute('''update kg_quotation_entry_lines set 
			vendor_1_select=%s,vendor_2_select=%s,vendor_3_select=%s,vendor_4_select=%s,vendor_5_select=%s
			where header_id = %s''',(False,False,False,True,False,hdr.id))
		return True
	
	def select_vendor_5(self, cr, uid, ids, context=None):
		for hdr in self.browse(cr, uid, ids, context):
			cr.execute('''update kg_quotation_entry_lines set 
			vendor_1_select=%s,vendor_2_select=%s,vendor_3_select=%s,vendor_4_select=%s,vendor_5_select=%s
			where header_id = %s''',(False,False,False,False,True,hdr.id))
		return True	
	
	def onchange_partner_id(self, cr, uid, ids, rfq_no_id):
		rfq_par_obj = self.pool.get('kg.rfq.vendor.selection')
		if rfq_no_id:
			rfq_par_rec = rfq_par_obj.browse(cr, uid, rfq_no_id)
			return {
					'value': 
					{
					'rfq_name' : rfq_par_rec.rfq_name,
					'rfq_date' : rfq_par_rec.quotation_date,
					}
					}
					
	def list_quotations(self, cr, uid, ids, context=None):
		rfq_ven_lin_obj = self.pool.get('kg.rfq.vendor.selection.line')
		rfq_ven_list_obj = self.pool.get('kg.rfq.vendor.list')
		line_obj = self.pool.get('kg.quotation.entry.lines')
		quote_pi_line_obj = self.pool.get('kg.quote.pi.line')
		qline_obj = self.pool.get('kg.quotation.requisition.line')
		q_obj = self.pool.get('kg.quotation.requisition.header')
		quote_obj = self.pool.get('kg.rfq.vendor.selection')
		vendor_1_id = vendor_2_id = vendor_3_id = vendor_4_id = vendor_5_id = quote_1_id = quote_2_id = quote_3_id = quote_4_id = quote_5_id = 0
		vendor_1 = vendor_2 = vendor_3 = vendor_4 = vendor_5 = ''
		ven_1_qty = ven_2_qty = ven_3_qty = ven_4_qty = ven_5_qty = ven_1_price = ven_2_price = ven_3_price = ven_4_price = ven_5_price = ven_1_val = ven_2_val = ven_3_val = ven_4_val = ven_5_val = 0.00
		ven_1_flag = True
		ven_2_flag = ven_3_flag = ven_4_flag = ven_5_flag = False		
		
		price_sample = []
		value_sample = []
		partners_list = []		
		d = {}
		
		for entry in self.browse(cr, uid, ids, context):
			del_sql = """ delete from kg_quotation_entry_lines where header_id=%s """ %(ids[0])
			cr.execute(del_sql)
			rfq_ven_lin_ids = rfq_ven_lin_obj.search(cr, uid, [('header_id','=',entry.rfq_no_id.id)])
			rfq_ven_list_ids = rfq_ven_list_obj.search(cr, uid, [('header_id','=',entry.rfq_no_id.id)])
			q_ids = q_obj.search(cr, uid, [('rfq_no_id','=',entry.rfq_no_id.id)])
			qline_ids = qline_obj.search(cr, uid, [('header_id','=',q_ids[0]),('cmp_flag','=',True)])
			for loop in qline_ids:
				record = qline_obj.browse(cr,uid,loop)
				price_sub_list = []
				value_sub_list = []
				sub_partners_list = []		
				for lines in record.pi_line_ids:
					price_sub_list.append(lines.vendors_price)
					value_sub_list.append(lines.vendors_value)
					sub_partners_list.append(lines.partner_id.id)
				result = list(set(sub_partners_list))
				sub_partners_list = result
				price_sample.append(price_sub_list)
				value_sample.append(value_sub_list)
				partners_list.append(sub_partners_list)
			for rfq_lin in rfq_ven_lin_ids:
				indx_0 = 0
				indx_1 = 0
				indx_2 = 0
				indx_3 = 0
				indx_4 = 0
				indx = rfq_ven_lin_ids.index(rfq_lin)
				rec_lin = rfq_ven_lin_obj.browse(cr,uid,rfq_lin)
				cmp_list = []
				for num in range(0,len(price_sample)):
					dump = sum(value_sample[num])
					cmp_list.append(dump)
				list1 = partners_list
				list2 = cmp_list
				if len(list2)==1:
					indx_0 = 0
				if len(list2)==2:
					indx_0 = 0
					indx_1 = 1
				if len(list2)==3:
					indx_0 = 0
					indx_1 = 1
					indx_2 = 2
				if len(list2)==4:
					indx_0 = 0
					indx_1 = 1
					indx_2 = 2
					indx_3 = 3
				if len(list2)==5:
					indx_0 = 0																				
					indx_1 = 1
					indx_2 = 2																				
					indx_3 = 3																				
					indx_4 = 4																				
				for i in range(0,len(cmp_list)):
					a = list1[i][0]
					d[a] = list2[i]
				for k, v in d.items():
					k, v
				d_sorted_by_value = sorted(d.items(), key=lambda x: x[1])
				d_len = len(d_sorted_by_value)
				if (d_len-(d_len-indx_0))==0:
					rec_ven = rfq_ven_list_obj.browse(cr,uid,rfq_ven_list_ids[0])
					vendor_1_id = d_sorted_by_value[0][0]
					quote_pi_line_ids = quote_pi_line_obj.search(cr, uid, [('rfq_no_id','=',entry.rfq_no_id.id),('product_id','=',rec_lin.product_id.id),('partner_id','=',vendor_1_id)])
					if quote_pi_line_ids:
						quote_pi_line_rec = quote_pi_line_obj.browse(cr,uid,quote_pi_line_ids[0])
						vendor_1 = quote_pi_line_rec.partner_name
						ven_1_flag = True
						ven_1_qty = quote_pi_line_rec.quotation_qty
						ven_1_price = quote_pi_line_rec.vendors_price
						ven_1_val = quote_pi_line_rec.vendors_value
				if (d_len-(d_len-indx_1))==1:
					rec_ven = rfq_ven_list_obj.browse(cr,uid,rfq_ven_list_ids[1])
					vendor_2_id = d_sorted_by_value[1][0]
					quote_pi_line_ids = quote_pi_line_obj.search(cr, uid, [('rfq_no_id','=',entry.rfq_no_id.id),('product_id','=',rec_lin.product_id.id),('partner_id','=',vendor_2_id)])
					if quote_pi_line_ids:
						quote_pi_line_rec = quote_pi_line_obj.browse(cr,uid,quote_pi_line_ids[0])
						vendor_2 = quote_pi_line_rec.partner_name
						ven_2_flag = True
						ven_2_qty = quote_pi_line_rec.quotation_qty
						ven_2_price = quote_pi_line_rec.vendors_price
						ven_2_val = quote_pi_line_rec.vendors_value
				if (d_len-(d_len-indx_2))==2:
					rec_ven = rfq_ven_list_obj.browse(cr,uid,rfq_ven_list_ids[2])
					vendor_3_id = d_sorted_by_value[2][0]
					quote_pi_line_ids = quote_pi_line_obj.search(cr, uid, [('rfq_no_id','=',entry.rfq_no_id.id),('product_id','=',rec_lin.product_id.id),('partner_id','=',vendor_3_id)])
					if quote_pi_line_ids:
						quote_pi_line_rec = quote_pi_line_obj.browse(cr,uid,quote_pi_line_ids[0])
						vendor_3 = quote_pi_line_rec.partner_name
						ven_3_flag = True
						ven_3_qty = quote_pi_line_rec.quotation_qty
						ven_3_price = quote_pi_line_rec.vendors_price
						ven_3_val = quote_pi_line_rec.vendors_value
				if (d_len-(d_len-indx_3))==3:
					rec_ven = rfq_ven_list_obj.browse(cr,uid,rfq_ven_list_ids[3])
					vendor_4_id = d_sorted_by_value[3][0]
					quote_pi_line_ids = quote_pi_line_obj.search(cr, uid, [('rfq_no_id','=',entry.rfq_no_id.id),('product_id','=',rec_lin.product_id.id),('partner_id','=',vendor_4_id)])
					if quote_pi_line_ids:
						quote_pi_line_rec = quote_pi_line_obj.browse(cr,uid,quote_pi_line_ids[0])
						vendor_4 = quote_pi_line_rec.partner_name
						ven_4_flag = True
						ven_4_qty = quote_pi_line_rec.quotation_qty
						ven_4_price = quote_pi_line_rec.vendors_price
						ven_4_val = quote_pi_line_rec.vendors_value
				if (d_len-(d_len-indx_4))==4:
					rec_ven = rfq_ven_list_obj.browse(cr,uid,rfq_ven_list_ids[4])
					vendor_5_id = d_sorted_by_value[4][0]
					quote_pi_line_ids = quote_pi_line_obj.search(cr, uid, [('rfq_no_id','=',entry.rfq_no_id.id),('product_id','=',rec_lin.product_id.id),('partner_id','=',vendor_5_id)])
					if quote_pi_line_ids:
						quote_pi_line_rec = quote_pi_line_obj.browse(cr,uid,quote_pi_line_ids[0])
						vendor_5 = quote_pi_line_rec.partner_name
						ven_5_flag = True
						ven_5_qty = quote_pi_line_rec.quotation_qty
						ven_5_price = quote_pi_line_rec.vendors_price
						ven_5_val = quote_pi_line_rec.vendors_value
				self.write(cr, uid, ids, 
					{
					'rfq_date' : entry.rfq_date,
					'rfq_name' : entry.rfq_name,
					'vendor_1_id': vendor_1_id,
					'vendor_2_id': vendor_2_id,
					'vendor_3_id': vendor_3_id,
					'vendor_4_id': vendor_4_id,
					'vendor_5_id': vendor_5_id,
					'vendor_1_name': vendor_1,
					'vendor_2_name': vendor_2,
					'vendor_3_name': vendor_3,
					'vendor_4_name': vendor_4,
					'vendor_5_name': vendor_5,
					'vendor_1_flag': ven_1_flag,
					'vendor_2_flag': ven_2_flag,
					'vendor_3_flag': ven_3_flag,
					'vendor_4_flag': ven_4_flag,
					'vendor_5_flag': ven_5_flag,
					'quote_list_flag': True,
					}
					)				
				vals = {
					'header_id': entry.id,
					'rfq_no_line_id':rec_lin.id,
					'product_id': rec_lin.product_id.id,
					'product_name': rec_lin.product_name,
					'brand_id': rec_lin.brand_id.id,
					'moc_id_temp': rec_lin.moc_id_temp.id,
					'moc_id': rec_lin.moc_id.id,
					'vendor_1_id': vendor_1_id,
					'vendor_2_id': vendor_2_id,
					'vendor_3_id': vendor_3_id,
					'vendor_4_id': vendor_4_id,
					'vendor_5_id': vendor_5_id,
					'vendor_1_name': vendor_1,
					'vendor_2_name': vendor_2,
					'vendor_3_name': vendor_3,
					'vendor_4_name': vendor_4,
					'vendor_5_name': vendor_5,
					'vendor_1_select': False,
					'vendor_1_quantity':ven_1_qty,
					'vendor_1_price_input':ven_1_price,
					'vendor_1_value':ven_1_val,
					'vendor_2_select': False,
					'vendor_2_quantity':ven_2_qty,
					'vendor_2_price_input':ven_2_price,
					'vendor_2_value':ven_2_val,
					'vendor_3_select': False,
					'vendor_3_quantity':ven_3_qty,
					'vendor_3_price_input':ven_3_price,
					'vendor_3_value':ven_3_val,
					'vendor_4_select': False,
					'vendor_4_quantity':ven_4_qty,
					'vendor_4_price_input':ven_4_price,
					'vendor_4_value':ven_4_val,
					'vendor_5_select': False,
					'vendor_5_quantity':ven_5_qty,
					'vendor_5_price_input':ven_5_price,
					'vendor_5_value':ven_5_val,
					'state': 'draft',
					'requested_qty': rec_lin.requested_qty,
					'quotation_qty': rec_lin.quotation_qty,
				}
				line_id = line_obj.create(cr, uid, vals)
			for loop in qline_ids:
				record = qline_obj.browse(cr,uid,loop)
				ref = record.partner_id.id
				for key, value in vals.items():
					if ref == value:
						key_name = key
						key_name = key_name.replace("_", " ")
						key_name = [int(s) for s in key_name.split() if s.isdigit()]
						if key_name[0] == 1:
							freight_vendor_1 = record.freight_type
							tax_vendor_1 = record.tax_type
							other_vendor_1 = record.other_charges
							line_ids = line_obj.search(cr, uid, [('vendor_1_id', '=', ref)])
							self.write(cr, uid,ids, {'vendor_1_freight':freight_vendor_1,'vendor_1_tax':tax_vendor_1,'vendor_1_others':other_vendor_1})							
						if key_name[0] == 2:
							freight_vendor_2 = record.freight_type
							tax_vendor_2 = record.tax_type
							other_vendor_2 = record.other_charges
							line_ids = line_obj.search(cr, uid, [('vendor_2_id', '=', ref)])
							self.write(cr, uid, ids, {'vendor_2_freight':freight_vendor_2,'vendor_2_tax':tax_vendor_2,'vendor_2_others':other_vendor_2})									
						if key_name[0] == 3:
							freight_vendor_3 = record.freight_type
							tax_vendor_3 = record.tax_type
							other_vendor_3 = record.other_charges
							line_ids = line_obj.search(cr, uid, [('vendor_3_id', '=', ref)])
							self.write(cr, uid, ids, {'vendor_3_freight':freight_vendor_3,'vendor_3_tax':tax_vendor_3,'vendor_3_others':other_vendor_3})												
						if key_name[0] == 4:
							freight_vendor_4 = record.freight_type
							tax_vendor_4 = record.tax_type
							other_vendor_4 = record.other_charges
							line_ids = line_obj.search(cr, uid, [('vendor_4_id', '=', ref)])
							self.write(cr, uid, ids, {'vendor_4_freight':freight_vendor_4,'vendor_4_tax':tax_vendor_4,'vendor_4_others':other_vendor_4})											
						if key_name[0] == 5:
							freight_vendor_5 = record.freight_type
							tax_vendor_5 = record.tax_type
							other_vendor_5 = record.other_charges
							line_ids = line_obj.search(cr, uid, [('vendor_5_id', '=', ref)])
							self.write(cr, uid, ids, {'vendor_5_freight':freight_vendor_5,'vendor_5_tax':tax_vendor_5,'vendor_5_others':other_vendor_5})													
			for lines in entry.line_ids:
				count = 0
				value = 0.0
				if lines.vendor_1_value > 0.0:
					count = 1
					price = lines.vendor_1_value
				if count > 0 and lines.vendor_2_value < price and lines.vendor_2_value > 0.0:
					count = 2
					price = lines.vendor_2_value
				elif count <= 0 and lines.vendor_2_value > 0.0:
					count = 2
					price = lines.vendor_2_value
				if count > 0 and lines.vendor_3_value < price and lines.vendor_3_value > 0.0:
					count = 3
					price = lines.vendor_3_value
				elif count <= 0 and lines.vendor_3_value > 0.0:
					count = 3
					price = lines.vendor_3_value
				if count > 0 and lines.vendor_4_value < price and lines.vendor_4_value > 0.0:
					count = 4
					price = lines.vendor_4_value
				elif count <= 0 and lines.vendor_4_value > 0.0:
					count = 4
					price = lines.vendor_4_value
				if count > 0 and lines.vendor_5_value < price and lines.vendor_5_value > 0.0:
					count = 5
					price = lines.vendor_5_value
				elif count <= 0 and lines.vendor_5_value > 0.0:
					count = 5
					price = lines.vendor_5_value
				if count > 0:
					cr.execute('''update kg_quotation_entry_lines set color_highlight_vendor_%s = %s,vendor_%s_select=%s
					where id = %s''',(count,'highlight',count,True,lines.id))
			quote_obj.write(cr,uid, entry.rfq_no_id.id, {'visible_quote' : True})
		return True					
		
	def create(self, cr, uid, vals, context=None):			
		rfq_par_obj = self.pool.get('kg.rfq.vendor.selection')
		rfq_par_rec = rfq_par_obj.browse(cr, uid, vals.get('rfq_no_id'))
		vals.update({'rfq_name': rfq_par_rec.rfq_name,'rfq_date':rfq_par_rec.quotation_date})
		return super(kg_quotation_entry_header, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		for quo in self.browse(cr, uid, ids, context=context):
			vals.update({'rfq_name': quo.rfq_name,'rfq_date':quo.rfq_date,'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_quotation_entry_header, self).write(cr, uid, ids, vals, context)				
	
	def send_for_approval(self, cr, uid, ids, context=None):
		count_list = []
		rec = self.browse(cr, uid, ids[0])
		if rec.state == 'draft':
			line_obj = self.pool.get('kg.quotation.entry.lines')
			quote_obj = self.pool.get('kg.rfq.vendor.selection')
			line_ids = line_obj.search(cr, uid, [('header_id','=',rec.id)], context=context)
			for i in range(1,6):
				cr.execute("""select count(*) from kg_quotation_entry_lines where vendor_%s_select = 't' and header_id = %s """%(i,ids[0]))
				result = cr.fetchone()
				if result[0]>0:
					count_list.append(result[0])
			tmp_list = []
			for i in range(1,6):
				cr.execute('''select id from kg_quotation_entry_header where vendor_%s_flag = %s and id = %s''',(i,True,ids[0],))
				resultant = cr.fetchall()
				if resultant!=[]:
					tmp_list.append(i)
			if tmp_list !=[]:
				for loop in tmp_list:
					cr.execute('''select quotation_validity_vendor_%s from kg_quotation_entry_header where vendor_%s_flag = %s and id = %s''',(loop,loop,True,ids[0]))
					result = cr.fetchone()
					if result[0] == 0:
						raise osv.except_osv(_('Warning'),_('Quotation Validity Days should be Greater than Zero'))
			#~ if rec.comparison_remarks == False:
				#~ raise osv.except_osv(_('Warning'),_('Please enter Comparision Remarks'))
			if len(line_ids) != sum(count_list):
				raise osv.except_osv(_('Warning'),_('Please Select All Line Items to Proceed'))
			for loop in line_ids:
				line_obj.write(cr, uid, loop, {'state':'approved'}, context=context)
			quote_obj.write(cr,uid, rec.rfq_no_id.id, {'visible_quote' : True})
			self.write(cr, uid, ids, {'state':'confirmed','confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'confirm_user_id':uid})
			ven_sel_obj = self.pool.get('kg.rfq.vendor.selection').search(cr,uid,[('id','=',rec.rfq_no_id.id)])
			ven_sel_rec = self.pool.get('kg.rfq.vendor.selection').browse(cr,uid,ven_sel_obj[0])
			self.pool.get('kg.rfq.vendor.selection').write(cr,uid,ven_sel_rec.id,{'state': 'comparison_confirmed'})
		return True
	
	def approve_quote(self, cr, uid, ids, context=None):
		rec= self.browse(cr,uid,ids[0])
		#~ if rec.remarks == False:
			#~ raise osv.except_osv(_('Warning'),_('Please enter Approve/Reject Remarks'))
		if rec.state == 'confirmed':
			quote_header = self.pool.get('kg.quotation.requisition.header')
			ven_sel_obj = self.pool.get('kg.rfq.vendor.selection')
			self.write(cr, uid, ids, {'state':'approved','approve_date':time.strftime('%Y-%m-%d %H:%M:%S'),'app_user_id':uid})
			ven_sel_ids = ven_sel_obj.search(cr,uid,[('id','=',rec.rfq_no_id.id),('state','!=','revised')])
			if ven_sel_ids:
				ven_sel_rec = ven_sel_obj.browse(cr,uid,ven_sel_ids[0])
				ven_sel_obj.write(cr,uid,ven_sel_rec.id,{'state': 'comparison_approved'})
			q_ids = quote_header.search(cr, uid, [('rfq_no_id','=',rec.rfq_no_id.id),('state','=','approved')])
			if q_ids:
				q_rec = quote_header.browse(cr, uid, q_ids[0])
				quote_header.write(cr, uid, q_rec.id,{'revised_flag':True})
		return True
	
	def po_record_create(self, cr, uid, ids, vendor_id, vendor_count, context=None):
		quo_obj = self.pool.get('kg.rfq.vendor.selection')
		quo_line_obj = self.pool.get('kg.rfq.vendor.selection.line')
		po_obj = self.pool.get('purchase.order')
		po_lin_obj = self.pool.get('purchase.order.line')
		ven_obj = self.pool.get('res.partner')
		line_obj = self.pool.get('kg.quotation.entry.lines')
		for quo in self.browse(cr, uid, ids, context):
			cr.execute('''
			select 
			vendor_%s_id as vendor_id, vendor_%s_value as vendor_value,
			rfq_no_line_id from kg_quotation_entry_lines where header_id=%s  
			and vendor_%s_select = %s 
			 and id in (
			select id from kg_quotation_entry_lines 
			where header_id=%s group by id having sum(case when vendor_1_select then 1 else 0 end+case when vendor_2_select then 1 else 0 end+case when 
			vendor_3_select then 1 else 0 end+case when vendor_4_select then 1 else 0 end+case when vendor_5_select then 1 else 0 end)=1 ) ''',(vendor_count,vendor_count,quo.id,vendor_count,True,quo.id,))
			res = cr.dictfetchall()
			if res:
				res = res[0]
				quo_rec = quo_obj.browse(cr, uid, quo.rfq_no_id.id)
				cr.execute('''select rfq_no_id,vendor_%s_freight as vendor_freight,vendor_%s_tax as vendor_tax from kg_quotation_entry_header where id = (
				select distinct header_id from kg_quotation_entry_lines where vendor_%s_select = %s  and id in (
				select id from kg_quotation_entry_lines where header_id=%s group by id having sum(case when vendor_1_select then 1 else 0 end+case when vendor_2_select then 1 else 0 end+case when 
				vendor_3_select then 1 else 0 end+case when vendor_4_select then 1 else 0 end+case when vendor_5_select then 1 else 0 end)=1 ) )''',(vendor_count,vendor_count,vendor_count,True,quo.id,))
				result = cr.dictfetchall()
				result = result[0]
				user_obj = self.pool.get('res.users')
				user_rec = user_obj.browse(cr,uid,uid)
				dep_rec = user_rec.dep_name
				location = dep_rec.main_location.id
				print"location",location
				print"res['vendor_id']",res['vendor_id']
				po_vals = {
					'partner_id': res['vendor_id'],
					'term_price': result['vendor_tax'],
					'term_freight': result['vendor_freight'],
					'quot_ref_no': quo_rec.name,
					'location_id': location,
					'payment_mode': 1,
					'delivery_mode': 1,
					'amount_untaxed': res['vendor_value'],
					'amount_total': res['vendor_value'],
					'pricelist_id': 2,
					'po_type': 'fromquote',
					'company_id': 1,
					'state': 'draft',
					'entry_mode': 'auto',
					'amend_flag': False,
					'po_flag': True,
					'grn_flag': False,
					'bill_flag': False,
				}
				po_id = po_obj.create(cr, uid, po_vals)	
				print"po_iddddd",po_id
				if po_id:
					cr.execute('''select product_id as product_id,brand_id as brand_id,moc_id as moc_id,moc_id_temp as moc_id_temp,uom as product_uom_id,vendor_%s_price_input as price_unit,vendor_%s_id as partner_id,quotation_qty as group_qty,
					case when rfq_no_line_id is not null then
					(select purchase_requisition_line_id from kg_rfq_vendor_selection_line where id = rfq_no_line_id)
					end as pi_line_id,
					quotation_qty as received_qty,requested_qty as pi_qty,quotation_qty as pending_qty,quotation_qty as product_qty
					from kg_quotation_entry_lines where vendor_%s_select = %s and header_id = %s''',(vendor_count,vendor_count,vendor_count,True,quo.id,))
					resultant = cr.dictfetchall()
					print "eeeeeeeeeeeeeeeee",resultant
					
					for items in resultant:
						if items['pi_line_id']:
							pi_line_id = items['pi_line_id']
						else:
							pi_line_id = False
						po_line_vals = {
							'product_id': items['product_id'],
							'brand_id': items['brand_id'],
							'moc_id': items['moc_id'],
							'moc_id_temp': items['moc_id_temp'],
							'product_uom_id': items['product_uom_id'],
							'order_id': po_id,
							'price_unit': items['price_unit'],
							'partner_id': items['partner_id'],
							'invoice': False,
							'company_id': 1,
							'state': 'draft',
							'group_qty': items['group_qty'],
							'line_bill': False,
							'pi_line_id': pi_line_id,
							'received_qty': items['received_qty'],
							'group_flag': False,
							'pi_qty': items['pi_qty'],
							'line_state':'draft',
							'pending_qty': items['pending_qty'],
							'cancel_flag': False,
							'line_flag': False,
							'product_qty': items['product_qty'],
						}
						po_line_id = po_lin_obj.create(cr, uid, po_line_vals)
						if quo.rfq_no_id.rfq_type == 'from_pi':
							cr.execute('insert into kg_poindent_po_line(po_order_id,piline_id) values(%s,%s)', (po_id,pi_line_id))	
		return True
	
	def po_generate(self, cr, uid, ids, context=None):
		for quo in self.browse(cr, uid, ids, context):
			for loop in quo.line_ids:
				count = 0
				if loop.vendor_1_select == True:
					count = count+1
				if loop.vendor_2_select == True:
					count = count+1
				if loop.vendor_3_select == True:
					count = count+1
				if loop.vendor_4_select == True:
					count = count+1
				if loop.vendor_5_select == True:
					count = count+1
				if count>1:
					raise osv.except_osv(_('Invalid action !'), _('Selection of same product against different vednors is not allowed!!!'))
			self.po_record_create(cr, uid, ids, quo.vendor_1_id.id, 1)
			self.po_record_create(cr, uid, ids, quo.vendor_2_id.id, 2)
			self.po_record_create(cr, uid, ids, quo.vendor_3_id.id, 3)
			self.po_record_create(cr, uid, ids, quo.vendor_4_id.id, 4)
			self.po_record_create(cr, uid, ids, quo.vendor_5_id.id, 5)
			self.write(cr, uid, ids, {'state':'po_generate'})
			
	def approve_po_quote(self, cr, uid, ids, context=None):
		for quo in self.browse(cr, uid, ids, context):
			for loop in quo.line_ids:
				count = 0
				if loop.vendor_1_select == True:
					count = count+1
				if loop.vendor_2_select == True:
					count = count+1
				if loop.vendor_3_select == True:
					count = count+1
				if loop.vendor_4_select == True:
					count = count+1
				if loop.vendor_5_select == True:
					count = count+1
				if count>1:
					raise osv.except_osv(_('Invalid action !'), _('Selection of same product against different vednors is not allowed!!!'))
			self.po_record_create(cr, uid, ids, quo.vendor_1_id.id, 1)
			self.po_record_create(cr, uid, ids, quo.vendor_2_id.id, 2)
			self.po_record_create(cr, uid, ids, quo.vendor_3_id.id, 3)
			self.po_record_create(cr, uid, ids, quo.vendor_4_id.id, 4)
			self.po_record_create(cr, uid, ids, quo.vendor_5_id.id, 5)
			self.write(cr, uid, ids, {'state':'po_generate'})
			
		
		return True	
	
	def reject_quote(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			if not rec.remarks:
				raise osv.except_osv(_('Warning !'),_('Enter Approve/Reject Remarks !!'))
			self.write(cr, uid, ids, {'state':'draft'})
		return True
		
kg_quotation_entry_header()


class kg_quotation_entry_lines(osv.osv):
	
	_name = 'kg.quotation.entry.lines'
	
	_columns = {
		
		## Basic Info
		
		'header_id': fields.many2one('kg.quotation.entry.header', 'Quo Header Id', required=True, ondelete='cascade'),
		'state': fields.selection([('draft', 'Draft'),('confirmed', 'Waiting For Approval'),('approved', 'Approved'),], 'State'),
		
		## Module Requirement Info
		
		'rfq_no_line_id':fields.many2one('kg.rfq.vendor.selection.line', 'RFQ', readonly=True),
		'product_id':fields.many2one('product.product', 'ProductDetails', readonly=True),
		'product_name': fields.related('product_id', 'name', type='char', string='Product Name', readonly=True, store=True, size=300),
		'brand_id': fields.many2one('kg.brand.master','Brand', readonly=True),
		'moc_id': fields.many2one('kg.moc.master','MOC',readonly=True),
		'moc_id_temp': fields.many2one('ch.brandmoc.rate.details','MOC',domain="[('brand_id','=',brand_id),('header_id.product_id','=',product_id),('header_id.state','in',('draft','confirmed','approved'))]",readonly=True),
		'uom': fields.related('product_id', 'uom_id', type='many2one', relation='product.uom', string='UOM', readonly=True, store=True),'vendor_1_id': fields.many2one('res.partner', 'Vendor 1' , readonly=True),
		'vendor_1_select':fields.boolean('Select'),
		'vendor_1_quantity':fields.float('Qty', readonly=True, digits=(16,3)),
		'vendor_1_price_input':fields.float('Rate', readonly=True, digits=(16,3)),
		'vendor_1_value':fields.float('Value', readonly=True, digits=(16,3)),
		'vendor_2_id': fields.many2one('res.partner', 'Vendor 2', readonly=True),
		'vendor_2_select':fields.boolean('Select'),
		'vendor_2_quantity':fields.float('Qty', readonly=True, digits=(16,3)),
		'vendor_2_price_input':fields.float('Rate', readonly=True, digits=(16,3)),
		'vendor_2_value':fields.float('Value', readonly=True, digits=(16,3)),
		'vendor_3_id': fields.many2one('res.partner', 'Vendor 3', readonly=True),
		'vendor_3_select':fields.boolean('Select'),
		'vendor_3_quantity':fields.float('Qty', readonly=True, digits=(16,3)),
		'vendor_3_price_input':fields.float('Rate', readonly=True, digits=(16,3)),
		'vendor_3_value':fields.float('Value', readonly=True, digits=(16,3)),
		'vendor_4_id': fields.many2one('res.partner', 'Vendor 4', readonly=True),
		'vendor_4_select':fields.boolean('Select'),
		'vendor_4_quantity':fields.float('Qty', readonly=True, digits=(16,3)),
		'vendor_4_price_input':fields.float('Rate', readonly=True, digits=(16,3)),
		'vendor_4_value':fields.float('Value', readonly=True, digits=(16,3)),
		'vendor_5_id': fields.many2one('res.partner', 'Vendor 5', readonly=True),
		'vendor_5_select':fields.boolean('Select'),
		'vendor_5_quantity':fields.float('Qty', readonly=True, digits=(16,3)),
		'vendor_5_price_input':fields.float('Rate', readonly=True, digits=(16,3)),
		'vendor_5_value':fields.float('Value', readonly=True, digits=(16,3)),
		'requested_qty': fields.related('rfq_no_line_id', 'requested_qty', store=True, type='float', string='MRN Approved Qty', readonly=True),
		'quotation_qty': fields.related('rfq_no_line_id', 'quotation_qty', store=True, type='float', string='RFQ Qty', readonly=True),
		'color_highlight_vendor_1': fields.selection([('dont_highlight', 'Dont Highlight'),('highlight', 'Highlight'),], 'Color Highlight for Least Value'),
		'color_highlight_vendor_2': fields.selection([('dont_highlight', 'Dont Highlight'),('highlight', 'Highlight'),], 'Color Highlight for Least Value'),
		'color_highlight_vendor_3': fields.selection([('dont_highlight', 'Dont Highlight'),('highlight', 'Highlight'),], 'Color Highlight for Least Value'),
		'color_highlight_vendor_4': fields.selection([('dont_highlight', 'Dont Highlight'),('highlight', 'Highlight'),], 'Color Highlight for Least Value'),
		'color_highlight_vendor_5': fields.selection([('dont_highlight', 'Dont Highlight'),('highlight', 'Highlight'),], 'Color Highlight for Least Value'),
		'approved_date':fields.date('Approved Date'),
		'freight_vendor_1': fields.char('Freight Vendor 1' , size=64, required=True),
		'freight_vendor_2': fields.char('Freight Vendor 2' , size=64, required=True),
		'freight_vendor_3': fields.char('Freight Vendor 3' , size=64, required=True),
		'freight_vendor_4': fields.char('Freight Vendor 4' , size=64, required=True),
		'freight_vendor_5': fields.char('Freight Vendor 5' , size=64, required=True),
		'tax_vendor_1': fields.char('Tax Vendor 1' , size=64, required=True),
		'tax_vendor_2': fields.char('Tax Vendor 2' , size=64, required=True),
		'tax_vendor_3': fields.char('Tax Vendor 3' , size=64, required=True),
		'tax_vendor_4': fields.char('Tax Vendor 4' , size=64, required=True),
		'tax_vendor_5': fields.char('Tax Vendor 5' , size=64, required=True),
		'others_vendor_1': fields.char('Others Vendor 1' , size=64, required=True),
		'others_vendor_2': fields.char('Others Vendor 2' , size=64, required=True),
		'others_vendor_3': fields.char('Others Vendor 3' , size=64, required=True),
		'others_vendor_4': fields.char('Others Vendor 4' , size=64, required=True),
		'others_vendor_5': fields.char('Others Vendor 5' , size=64, required=True),
		
	}
	
	_defaults = {
		
		'state':'draft',
		'color_highlight_vendor_1':'dont_highlight',
		'color_highlight_vendor_2':'dont_highlight',
		'color_highlight_vendor_3':'dont_highlight',
		'color_highlight_vendor_4':'dont_highlight',
		'color_highlight_vendor_5':'dont_highlight',
		'freight_vendor_1':'',
		'freight_vendor_2':'',
		'freight_vendor_3':'',
		'freight_vendor_4':'',
		'freight_vendor_5':'',
		'tax_vendor_1':'',
		'tax_vendor_2':'',
		'tax_vendor_3':'',
		'tax_vendor_4':'',
		'tax_vendor_5':'',
		'others_vendor_1':'',
		'others_vendor_2':'',
		'others_vendor_3':'',
		'others_vendor_4':'',
		'others_vendor_5':'',
		
	}
	
kg_quotation_entry_lines()
