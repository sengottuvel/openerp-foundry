from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import re
from operator import itemgetter
from itertools import groupby

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import calendar
today = datetime.now()
#import MySQLdb
a = datetime.now()
dt_time = a.strftime('%m/%d/%Y %H:%M:%S')

class kg_purchase_invoice(osv.osv):
	
	
	def _get_domain(self, cr, uid, ids, service_order_id,po_id, arg, context=None):
		record_id = ids[0] 
		
		return True

	_name = "kg.purchase.invoice"
	_order = "invoice_date desc"
	_description = "Purchase Invoice"
	_columns = {
	
		'created_by' : fields.many2one('res.users', 'Created By', readonly=True),
		'creation_date':fields.datetime('Creation Date',required=True,readonly=True),
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),	
		
		'name':fields.char('Invoice No',readonly=True),
		'invoice_date':fields.date('Invoice Date',readonly=True,required=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		
		'type': fields.selection([('from_po', 'Product'), ('from_so', 'Service'),('from_gp','Gate Pass')], 'Product/Service',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'purpose': fields.selection([('consu', 'Consumables'), ('project', 'Project'), ('asset', 'Asset')], 'Purpose',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		
		'grn_type': fields.selection([('from_po_grn', 'PO/SO GRN'), ('from_general_grn', 'General GRN'), ('others', 'Others')], 'GRN Type',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		
		'state': fields.selection([('draft','Draft'),('confirmed','Waiting for approval'),('approved','Approved'),
				('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True,track_visibility='onchange',select=True),
				
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),		
		
		'approved_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Apprved By', readonly=True),
		
		'confirmed_date': fields.datetime('Confirmed Date', readonly=True),
		'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		
		'reject_date': fields.datetime('Rejected Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		
		'cancel_date': fields.datetime('Canceled Date', readonly=True),
		'can_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		
		'confirm_flag':fields.boolean('Confirm Flag'),
		'approve_flag':fields.boolean('Expiry Flag'),
		
		'domain_field': fields.function(_get_domain, type='char', size=255, method=True, string="Domain"),

		## Vendor Information ##
		
		'supplier_id':fields.many2one('res.partner','Supplier',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'sup_address':fields.text('Supplier Address',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		
		'sup_invoice_no':fields.char('Supplier Invoice No',size=200,readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'sup_invoice_date':fields.date('Supplier Invoice Date',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		
		'payment_id':fields.many2one('kg.payment.master','Payment Terms',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'payment_due_date':fields.date('Payment Due Date',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		
		'remarks': fields.text('Remarks',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		
		'payment_type': fields.selection([('cash', 'Cash'), ('credit', 'Credit')], 'Payment Type',readonly=True),
		
		
				 
		### PO Details ###
		
		'po_id': fields.many2one('purchase.order','PO NO',select=True, readonly=True,states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]},domain="[('partner_id','=',supplier_id), '&', ('state','=','approved')]"),
		
		'po_date':fields.date('PO Date',readonly=True),
		
		### SO Details ###
		'service_order_id':fields.many2one('kg.service.order','Service Order No', readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]},domain="[('partner_id','=',supplier_id), '&', ('state','=','approved')]"),
		
		'service_order_date':fields.date('Service Order Date', readonly=True),
		
		
		'order_no': fields.char('Order NO',readonly=True),
        
        'order_date': fields.char('Order Date',readonly=True),
        
        'grn_no': fields.char('GRN NO',readonly=True),
		
		
		#### GRN Search #######
		
		'po_grn_ids': fields.many2many('kg.po.grn', 'purchase_invoice_grn_ids', 'invoice_id','grn_id', 'GRN', delete=False,
			 domain="[('state','=','done'),'&',('supplier_id','=',supplier_id),'&',('grn_type','=',type),'&',('billing_status','=','applicable')]"),
				 
			 
		'general_grn_ids': fields.many2many('kg.general.grn', 'purchase_invoice_general_grn_ids', 'invoice_id','grn_id', 'GRN', delete=False,
			 domain="[('supplier_id','=',supplier_id), '&', ('state','=','done'), '&', ('bill','=','applicable')]"),
			 
		'labour_ids': fields.many2many('kg.service.invoice', 'service_invoice_grn_ids', 'invoice_id','service_id', 'GRN', delete=False,domain="[('state','=','approved'),'&',('partner_id','=',supplier_id)]"),
		
		
		### LINE IDS #####
		
		'pogrn_line_ids':fields.one2many('kg.pogrn.purchase.invoice.line','invoice_header_id','POGRN Line Id',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		
		'gengrn_line_ids':fields.one2many('kg.gengrn.purchase.invoice.line','invoice_header_id','POGRN Line Id',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		
		'service_line_ids':fields.one2many('kg.grn.service.invoice.line','invoice_header_id','POGRN Line Id',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		
		'poadvance_line_ids':fields.one2many('kg.poadvance.purchase.invoice.line','invoice_header_id','POAdvance Line Id',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		
		'soadvance_line_ids':fields.one2many('kg.soadvance.purchase.invoice.line','invoice_header_id','SOAdvance Line Id',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		
		### Value Calculation ###
		
		'total_amt': fields.float('Total Amount',readonly=True),
		'discount_amt': fields.float('Discount(-)',readonly=True),
		'tax_amt': fields.float('Tax(+)',readonly=True),
		'other_charges_amt': fields.float('Other Charges',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'actual_amt': fields.float('Actual Amount',readonly=True),
		'round_off_amt': fields.float('Round off(+/-)',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'advance_adjusted_amt': fields.float('Advanced Adjustment Amount(-)',readonly=True),
		'invoice_amt': fields.float('Invoice Amount',readonly=True),
		'net_amt': fields.float('Net Amount',readonly=True),
		
		### Flags ##
		
		'load_items_flag':fields.boolean('load_items_flag'),
		
		'active': fields.boolean('Active'),
		
		'specification': fields.text('Specification',readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'dep_project':fields.many2one('kg.project.master','Dept/Project Name',readonly=True,states={'draft': [('readonly', False)],'confirmed':[('readonly',False)]}),	
		'po_so_name': fields.char('PO/SO NO',readonly=True,states={'draft': [('readonly', False)],'confirmed':[('readonly',False)]}),
		
		'po_so_date': fields.char('PO/SO Date',readonly=True,states={'draft': [('readonly', False)],'confirmed':[('readonly',False)]}),
		'helpdesk_flag':fields.boolean('HelpDesk Flag'),
		
	}
	
	_defaults = {
		
		'created_by': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'invoice_date': fields.date.context_today,
		#'sup_invoice_date': fields.date.context_today,
		'payment_due_date': fields.date.context_today,
		'load_items_flag': False,
		'state':'draft',
		'name':'',
		'active': True,
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_purchase_invoice', context=c),
		'helpdesk_flag':False,

	}
	
	
	def sechedular_email_ids(self,cr,uid,ids,context = None):
		email_from = []
		email_to = []
		email_cc = []
		val = {'email_from':'','email_to':'','email_cc':''}
		ir_model = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		mail_form_ids = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		for ids in mail_form_ids:
			mail_form_rec = self.pool.get('kg.mail.settings').browse(cr,uid,ids)
			if mail_form_rec.sch_type == 'scheduler':
				s = mail_form_rec.sch_name
				s = s.lower()
				if s == 'unaccounted credit register':
					email_sub = mail_form_rec.subject
					email_from.append(mail_form_rec.name)
					mail_line_id = self.pool.get('kg.mail.settings.line').search(cr,uid,[('line_entry','=',ids)])
					for mail_id in mail_line_id:
						mail_line_rec = self.pool.get('kg.mail.settings.line').browse(cr,uid,mail_id)
						if mail_line_rec.to_address:
							email_to.append(mail_line_rec.mail_id)
						if mail_line_rec.cc_address:
							email_cc.append(mail_line_rec.mail_id)
				else:
					pass
		val['email_from'] = email_from
		val['email_to'] = email_to
		val['email_cc'] = email_cc
		return val
	
	def _future_date_check(self,cr,uid,ids,contaxt=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		invoice_date = rec.invoice_date
		sup_invoice_date = rec.sup_invoice_date
		invoice_date = str(invoice_date)
		sup_invoice_date = str(sup_invoice_date)
		invoice_date = datetime.strptime(invoice_date, '%Y-%m-%d')
		sup_invoice_date = datetime.strptime(sup_invoice_date, '%Y-%m-%d')
		if invoice_date > today:
			return False
		if sup_invoice_date > today:
			return False
		return True
		
	_constraints = [		
					  
		(_future_date_check, 'System not allow to save with future date. !!',['price']),
		
	   ]
	
	###  Onchange for Supplier Address ###
	
	def onchange_supplier_id(self, cr, uid, ids, supplier_id):
		partner = self.pool.get('res.partner')
		supplier_address = partner.address_get(cr, uid, [supplier_id], ['default'])
		supplier = partner.browse(cr, uid, supplier_id)
		tot_add = (supplier.street or '')+ ' ' + (supplier.street2 or '') + '\n'+(supplier.city.name or '')+ ',' +(supplier.state_id.name or '') + '-' +(supplier.zip or '') + '\nPh:' + (supplier.phone or '')+ '\n' +(supplier.mobile or '')
		return {'value': {
			'sup_address' : tot_add or False
			}}
			
	def onchange_po_id(self, cr, uid, ids, po_id, context=None):
		value = {'po_date': '','service_order_id':''}
		if po_id:
			po_rec = self.pool.get('purchase.order').browse(cr, uid, po_id, context=context)
			value = {'po_date': po_rec.date_order,'service_order_id': ''}
		return {'value': value}
		
	# Onchange SO Date #
		
	def onchange_so_id(self, cr, uid, ids, service_order_id, context=None):
		value = {'service_order_date': '','po_id':''}
		if service_order_id:
			so_rec = self.pool.get('kg.service.order').browse(cr, uid, service_order_id, context=context)
			value = {'service_order_date': so_rec.date,'po_id':''}
		return {'value': value}
		
	def load_advance(self, cr, uid, ids,context=None):
		invoice_rec = self.browse(cr,uid,ids[0])
		po_adv_obj = self.pool.get('kg.po.advance')
		so_adv_obj = self.pool.get('kg.so.advance')
		po_grn_obj = self.pool.get('kg.po.grn')
		po_grn_line_obj = self.pool.get('po.grn.line')
		po_inadv_obj = self.pool.get('kg.poadvance.purchase.invoice.line')
		so_inadv_obj = self.pool.get('kg.soadvance.purchase.invoice.line')
		cr.execute(""" select grn_id from purchase_invoice_grn_ids where invoice_id = %s """ %(invoice_rec.id))
		grn_data = cr.dictfetchall()
		for item in grn_data:
			grn_id = item['grn_id']
			grn_record = po_grn_obj.browse(cr, uid, grn_id)
			if grn_record.grn_type == 'from_po':
				if invoice_rec.poadvance_line_ids:
					del_sql = """delete from kg_poadvance_purchase_invoice_line where invoice_header_id=%s"""%(ids[0])
					cr.execute(del_sql)
				print "grn_record.po_idsgrn_record.po_ids",grn_record.po_ids
				stop
				for element in grn_record.po_ids:
					adv_search = self.pool.get('kg.po.advance').search(cr, uid, [('po_id','=',element.id)])
					cr.execute(""" select * from kg_po_advance where po_id = %s and bal_adv > 0 and state='approved'""" %(element.id))
					grn_data = cr.dictfetchall()
					for inv in grn_data:
						po_inadv_obj.create(cr,uid,{
							'po_id' : inv['po_id'],
							'po_advance_id' : inv['id'],
							'po_advance_date' : inv['advance_date'],
							'tot_advance_amt' : inv['advance_amt'],
							'balance_amt' : inv['bal_adv'],
							'current_adv_amt' : 0.0,
							'invoice_header_id' : invoice_rec.id,
							})
			if grn_record.grn_type == 'from_so':
				if invoice_rec.soadvance_line_ids:
					del_sql = """delete from kg_soadvance_purchase_invoice_line where invoice_header_id=%s"""%(ids[0])
					cr.execute(del_sql)
				for element in grn_record.po_ids:
					adv_search = self.pool.get('kg.so.advance').search(cr, uid, [('so_id','=',element.id)])
					cr.execute(""" select * from kg_so_advance where so_id = %s and bal_adv > 0 and state='approved'""" %(element.id))
					grn_data = cr.dictfetchall()
					for inv in grn_data:
						so_inadv_obj.create(cr,uid,{
							'so_id' : inv['po_id'],
							'so_advance_id' : inv['id'],
							'so_advance_date' : inv['advance_date'],
							'tot_advance_amt' : inv['advance_amt'],
							'balance_amt' : inv['bal_adv'],
							'already_adjusted_amt' : inv['advance_amt'] - inv['bal_adv'],
							'current_adv_amt' : 0.0,
							'invoice_header_id' : invoice_rec.id,
							})		
		return True
		
	def load_details(self, cr, uid, ids,context=None):
		invoice_rec = self.browse(cr,uid,ids[0])
		po_grn_obj = self.pool.get('kg.po.grn')
		po_grn_line_obj = self.pool.get('po.grn.line')
		general_grn_obj = self.pool.get('kg.general.grn')
		general_grn_line_obj = self.pool.get('kg.general.grn.line')
		pogrn_invoice_line_obj = self.pool.get('kg.pogrn.purchase.invoice.line')
		gengrn_invoice_line_obj = self.pool.get('kg.gengrn.purchase.invoice.line')
		service_invoice_line_obj = self.pool.get('kg.grn.service.invoice.line')
		service_grn_line_obj = self.pool.get('kg.service.invoice.line')
		service_grn_obj = self.pool.get('kg.service.invoice')
		po_name = ''
		po_date = ''
		po_list = []
		podate_list = []
		so_list = []
		sodate_list = []
		gp_list = []
		gpdate_list = []
		if invoice_rec.grn_type == 'from_po_grn':
			self.write(cr, uid, ids[0], {'load_items_flag' : True})
			cr.execute(""" select grn_id from purchase_invoice_grn_ids where invoice_id = %s """ %(invoice_rec.id))
			grn_data = cr.dictfetchall()
			line_ids = map(lambda x:x.id,invoice_rec.pogrn_line_ids)
			pogrn_invoice_line_obj.unlink(cr,uid,line_ids)
			for item in grn_data:
				grn_id = item['grn_id']
				grn_record = po_grn_obj.browse(cr, uid, grn_id)
				self.write(cr, uid, ids[0], {'payment_type' : grn_record.payment_type})
				cr.execute(""" select id from po_grn_line where po_grn_id = %s and billing_type='cost' order by id """ %(grn_id))
				grn_line_data = cr.dictfetchall()
				for line_item in grn_line_data:
					val = 0.00
					net_amount = 0.00
					tot_amt = 0.00
					grn_line_record = po_grn_line_obj.browse(cr, uid, line_item['id'])
					if grn_record.grn_type == 'from_po':
						if grn_line_record.po_line_id.order_id.name not in po_list:
							po_list.append(grn_line_record.po_line_id.order_id.name)
							date_order = grn_line_record.po_line_id.order_id.date_order
							date_order = datetime.strptime(date_order, '%Y-%m-%d')
							date_order = date_order.strftime('%d/%m/%Y')
							
							podate_list.append(date_order)
						po_name = ", ".join(po_list)
						
						po_date = ", ".join(podate_list)
						po_so_name = grn_line_record.po_line_id.order_id.name
						po_so_qty = grn_line_record.po_qty
					if grn_record.grn_type == 'from_gp':
						if grn_line_record.gp_line_id.gate_id.name not in gp_list:
							gp_list.append(grn_line_record.gp_line_id.gate_id.name)
							date_order = grn_line_record.gp_line_id.gate_id.date
							date_order = datetime.strptime(date_order, '%Y-%m-%d')
							date_order = date_order.strftime('%d/%m/%Y')
							gpdate_list.append(date_order)
						po_name = ", ".join(gp_list)
						po_date = ", ".join(gpdate_list)
						po_so_name = grn_line_record.gp_line_id.gate_id.name
						po_so_qty = grn_line_record.po_qty	
					elif grn_record.grn_type == 'from_so':
						if grn_line_record.so_line_id.service_id.name not in so_list:
							so_list.append(grn_line_record.so_line_id.service_id.name)
							date_order = grn_line_record.so_line_id.service_id.date
							date_order = datetime.strptime(date_order, '%Y-%m-%d')
							date_order = date_order.strftime('%d/%m/%Y')
							sodate_list.append(date_order)
						po_so_name = grn_line_record.so_line_id.service_id.name
						po_so_qty = grn_line_record.so_qty
						po_name = ",".join(so_list)
						po_date = ",".join(sodate_list)
						
					#### Net Amount Calculation ####
					
					amt_to_per = (grn_line_record.kg_discount / (grn_line_record.po_grn_qty * grn_line_record.price_unit or 1.0 )) * 100
					kg_discount_per = grn_line_record.kg_discount_per
					tot_discount_per = amt_to_per + kg_discount_per
					for c in self.pool.get('account.tax').compute_all(cr, uid, grn_line_record.grn_tax_ids,
						grn_line_record.price_unit * (1-(tot_discount_per or 0.0)/100.0), grn_line_record.po_grn_qty, grn_line_record.product_id,
						grn_record.supplier_id)['taxes']:
						val += c.get('amount', 0.0)
					tot_amt = grn_line_record.po_grn_qty * (grn_line_record.price_unit * (1-(tot_discount_per or 0.0)/100.0))
					net_amount = tot_amt + val
					po_grn_invoice_line_vals = {
							'invoice_header_id':invoice_rec.id,
							'po_grn_id': grn_record.id,
							'dc_no': grn_record.dc_no,
							'po_so_no':po_so_name,
							'po_id': grn_record.po_id.id,
							'so_id': grn_record.so_id.id,
							'product_id': grn_line_record.product_id.id,
							'po_so_qty':po_so_qty,
							'tot_rec_qty':grn_line_record.po_grn_qty,
							'uom_id': grn_line_record.uom_id.id,
							'price_unit': grn_line_record.price_unit,
							'total_amt': grn_line_record.po_grn_qty * grn_line_record.price_unit,
							'discount': grn_line_record.kg_discount,
							'kg_discount_per': grn_line_record.kg_discount_per,
							'invoice_tax_ids': [(6, 0, [x.id for x in grn_line_record.grn_tax_ids])],
							'net_amt': net_amount,
							'grn_type':'from_po_grn',
						}
					print "po_grn_invoice_line_valspo_grn_invoice_line_valspo_grn_invoice_line_vals",po_grn_invoice_line_vals
					pogrn_invoice_line_obj.create(cr, uid, po_grn_invoice_line_vals)
			self.write(cr, uid, ids[0], {'po_so_name' :po_name ,'po_so_date':po_date})			
		if invoice_rec.grn_type == 'from_general_grn':
			self.write(cr, uid, ids[0], {'load_items_flag' : True})
			cr.execute(""" select grn_id from purchase_invoice_general_grn_ids where invoice_id = %s """ %(invoice_rec.id))
			general_grn_data = cr.dictfetchall()
			line_ids = map(lambda x:x.id,invoice_rec.gengrn_line_ids)
			gengrn_invoice_line_obj.unlink(cr,uid,line_ids)
			for item in general_grn_data:
				grn_id = item['grn_id']
				grn_record = general_grn_obj.browse(cr, uid, grn_id)
				self.write(cr, uid, ids[0], {'payment_type' : grn_record.payment_type})
				cr.execute(""" select id from kg_general_grn_line where grn_id = %s order by id """ %(grn_id))
				grn_line_data = cr.dictfetchall()
				for line_item in grn_line_data:
					val = 0.00
					net_amount = 0.00
					tot_amt = 0.00
					grn_line_record = general_grn_line_obj.browse(cr, uid, line_item['id'])
					#### Net Amount Calculation ####
					amt_to_per = (grn_line_record.kg_discount / (grn_line_record.grn_qty * grn_line_record.price_unit or 1.0 )) * 100
					kg_discount_per = grn_line_record.kg_discount_per
					tot_discount_per = amt_to_per + kg_discount_per
					for c in self.pool.get('account.tax').compute_all(cr, uid, grn_line_record.grn_tax_ids,
						grn_line_record.price_unit * (1-(tot_discount_per or 0.0)/100.0), grn_line_record.grn_qty, grn_line_record.product_id,
						grn_record.supplier_id)['taxes']:
						val += c.get('amount', 0.0)
					tot_amt = grn_line_record.grn_qty * (grn_line_record.price_unit * (1-(tot_discount_per or 0.0)/100.0))
					net_amount = tot_amt + val
					gengrn_invoice_line_obj.create(cr, uid, {
							'invoice_header_id':invoice_rec.id,
							'general_grn_id': grn_record.id,
							'dc_no': grn_record.dc_no,
							'product_id': grn_line_record.product_id.id,
							'tot_rec_qty':grn_line_record.grn_qty,
							'uom_id': grn_line_record.uom_id.id,
							'price_unit': grn_line_record.price_unit,
							'total_amt': grn_line_record.grn_qty * grn_line_record.price_unit,
							'discount': grn_line_record.kg_discount,
							'kg_discount_per': grn_line_record.kg_discount_per,
							'invoice_tax_ids': [(6, 0, [x.id for x in grn_line_record.grn_tax_ids])],
							'net_amt': net_amount,
							'grn_type':'from_general_grn',
							
						})
		if invoice_rec.grn_type == 'others':
			self.write(cr, uid, ids[0], {'load_items_flag' : True})
			cr.execute(""" select service_id from service_invoice_grn_ids where invoice_id = %s """ %(invoice_rec.id))
			service_grn_data = cr.dictfetchall()
			line_ids = map(lambda x:x.id,invoice_rec.service_line_ids)
			service_invoice_line_obj.unlink(cr,uid,line_ids)
			for item in service_grn_data:
				service_id = item['service_id']
				service_record = service_grn_obj.browse(cr, uid, service_id)
				self.write(cr, uid, ids[0], {'payment_type' : service_record.payment_type})
				cr.execute(""" select id from kg_service_invoice_line where service_id = %s order by id """ %(service_id))
				service_line_data = cr.dictfetchall()
				for line_item in service_line_data:
					val = 0.00
					net_amount = 0.00
					tot_amt = 0.00
					service_line_record = service_grn_line_obj.browse(cr, uid, line_item['id'])
					#### Net Amount Calculation ####
					amt_to_per = (service_line_record.kg_discount / (service_line_record.product_qty * service_line_record.price_unit or 1.0 )) * 100
					kg_discount_per = service_line_record.kg_discount_per
					tot_discount_per = amt_to_per + kg_discount_per
					for c in self.pool.get('account.tax').compute_all(cr, uid, service_line_record.taxes_id,
						service_line_record.price_unit * (1-(tot_discount_per or 0.0)/100.0), service_line_record.product_qty, service_line_record.product_id,
						service_record.partner_id)['taxes']:
						val += c.get('amount', 0.0)
					tot_amt = service_line_record.product_qty * (service_line_record.price_unit * (1-(tot_discount_per or 0.0)/100.0))
					net_amount = tot_amt + val
					service_invoice_line_obj.create(cr, uid, {
							'invoice_header_id':invoice_rec.id,
							'soi_id': service_record.id,
							'so_id': service_record.service_order_id.id,
							'dc_no': '',
							'product_id': service_line_record.product_id.id,
							'tot_rec_qty':service_line_record.product_qty,
							'uom_id': service_line_record.product_uom.id,
							'price_unit': service_line_record.price_unit,
							'total_amt': service_line_record.product_qty * service_line_record.price_unit,
							'discount': service_line_record.kg_discount,
							'kg_discount_per': service_line_record.kg_discount_per,
							'invoice_tax_ids': [(6, 0, [x.id for x in service_line_record.taxes_id])],
							'net_amt': net_amount,
							'grn_type':'others',
						})				
		return True
		
	def update_actual_values(self, cr, uid, ids,context=None):
		invoice_rec = self.browse(cr,uid,ids[0])
		pogrn_invoice_line_obj = self.pool.get('kg.pogrn.purchase.invoice.line')
		gengrn_invoice_line_obj = self.pool.get('kg.gengrn.purchase.invoice.line')
		service_invoice_line_obj = self.pool.get('kg.grn.service.invoice.line')
		val = 0.00
		other_charges = final_net_amt = final_net_value = total_net_value = total_amount = final_total_amount = total_discount = final_tot_discount = total_tax = final_tax = final_other_charges = final_adj_amt=0.00
		if invoice_rec.grn_type == 'from_po_grn':
			### Adjustment Amount ###
			if invoice_rec.type == 'from_po':
				if invoice_rec.poadvance_line_ids:
					for adv_line in invoice_rec.poadvance_line_ids:
						cur_adv_amt = adv_line.current_adv_amt
						final_adj_amt += cur_adv_amt
			if invoice_rec.type == 'from_so':
				if invoice_rec.soadvance_line_ids:
					for adv_line in invoice_rec.soadvance_line_ids:
						cur_adv_amt = adv_line.current_adv_amt
						final_adj_amt += cur_adv_amt
			for line in invoice_rec.pogrn_line_ids:
				if invoice_rec.type == 'from_po':
					other_charges = line.po_id.other_charge
				if invoice_rec.type == 'from_so':
					other_charges = line.so_id.other_charge
				amt_to_per = (line.discount / (line.tot_rec_qty * line.price_unit or 1.0 )) * 100
				kg_discount_per = line.kg_discount_per
				tot_discount_per = amt_to_per + kg_discount_per
				val = 0.00
				for c in self.pool.get('account.tax').compute_all(cr, uid, line.invoice_tax_ids,
					line.price_unit * (1-(tot_discount_per or 0.0)/100.0), line.tot_rec_qty, line.product_id)['taxes']:
					val += c.get('amount', 0.0)
				tot_amt = line.tot_rec_qty * (line.price_unit * (1-(tot_discount_per or 0.0)/100.0))
				net_amount = tot_amt + val
				### Total Amount ###
				line_total = line.tot_rec_qty * line.price_unit
				final_total_amount += line_total
				final_net_amt += net_amount
				## Total Discount###
				tot_disc = ((line_total * tot_discount_per)/100)
				total_discount = tot_disc
				final_tot_discount += total_discount
				### Tax Amount ###
				final_tax += val
				### Other Charges ###
				if other_charges != None:
					final_other_charges += other_charges 
				### Net Amount, Actual Amount, Invoice Amount ####
				total_net_value += line.net_amt
				final_net_value = (total_net_value + final_other_charges) - final_adj_amt
				pogrn_invoice_line_obj.write(cr, uid, line.id,{'total_amt': line_total,'net_amt':net_amount})
		if invoice_rec.grn_type == 'from_general_grn':
			for line in invoice_rec.gengrn_line_ids:
				val = 0.00
				other_charges = line.general_grn_id.other_charge
				amt_to_per = (line.discount / (line.tot_rec_qty * line.price_unit or 1.0 )) * 100
				kg_discount_per = line.kg_discount_per
				tot_discount_per = amt_to_per + kg_discount_per
				for c in self.pool.get('account.tax').compute_all(cr, uid, line.invoice_tax_ids,
					line.price_unit * (1-(tot_discount_per or 0.0)/100.0), line.tot_rec_qty, line.product_id)['taxes']:
					val += c.get('amount', 0.0)
				tot_amt = line.tot_rec_qty * (line.price_unit * (1-(tot_discount_per or 0.0)/100.0))
				net_amount = tot_amt + val
				### Total Amount ###
				line_total = line.tot_rec_qty * line.price_unit
				final_total_amount += line_total
				final_net_amt += net_amount
				## Total Discount###
				tot_disc = ((line_total * tot_discount_per)/100)
				total_discount = tot_disc
				final_tot_discount += total_discount
				### Tax Amount ###
				final_tax += val
				### Other Charges ###
				if other_charges != None:
					final_other_charges += other_charges
				### Net Amount, Actual Amount, Invoice Amount ####
				total_net_value += line.net_amt
				final_net_value = total_net_value + final_other_charges
				gengrn_invoice_line_obj.write(cr, uid, line.id,{'total_amt': line_total,'net_amt':net_amount})
		if invoice_rec.grn_type == 'others':
			if invoice_rec.type == 'from_so':
				if invoice_rec.soadvance_line_ids:
					for adv_line in invoice_rec.soadvance_line_ids:
						cur_adv_amt = adv_line.current_adv_amt
						final_adj_amt += cur_adv_amt
			for line in invoice_rec.service_line_ids:
				val = 0.00
				if invoice_rec.type == 'from_so':
					other_charges = line.so_id.other_charge
				amt_to_per = (line.discount / (line.tot_rec_qty * line.price_unit or 1.0 )) * 100
				kg_discount_per = line.kg_discount_per
				tot_discount_per = amt_to_per + kg_discount_per
				for c in self.pool.get('account.tax').compute_all(cr, uid, line.invoice_tax_ids,
					line.price_unit * (1-(tot_discount_per or 0.0)/100.0), line.tot_rec_qty, line.product_id)['taxes']:
					val += c.get('amount', 0.0)
				tot_amt = line.tot_rec_qty * (line.price_unit * (1-(tot_discount_per or 0.0)/100.0))
				net_amount = tot_amt + val
				
				### Total Amount ###
				
				line_total = line.tot_rec_qty * line.price_unit
				final_total_amount += line_total
				final_net_amt += net_amount
				## Total Discount###
				
				tot_disc = ((line_total * tot_discount_per)/100)
				total_discount = tot_disc
				
				final_tot_discount += total_discount
				
				### Tax Amount ###
				
				final_tax += val
				
				### Other Charges ###
				
				if other_charges != None:
					final_other_charges += other_charges 
					
					
				### Net Amount, Actual Amount, Invoice Amount ####
				
				total_net_value += line.net_amt
				total_net_value = total_net_value 
				#total_net_value = total_net_value + final_tax
				
				final_net_value = (total_net_value + final_other_charges) - final_adj_amt
				
				
				service_invoice_line_obj.write(cr, uid,line.id, {'total_amt': line_total,'net_amt':net_amount})
				
		self.write(cr, uid, ids[0], {
					'total_amt': final_total_amount,
					'discount_amt': final_tot_discount,
					'tax_amt':final_tax,
					'other_charges_amt':final_other_charges,
					'actual_amt' : final_net_amt, 
					'invoice_amt': final_net_amt, 
					'advance_adjusted_amt': final_adj_amt or 0.00, 
					'net_amt': final_net_amt})
			

		return True
		
	def compute_values(self, cr, uid, ids,context=None):
		
		invoice_rec = self.browse(cr,uid,ids[0])
		
		val = 0.00
		final_net_value = total_net_value = final_actual_amount = line_total = total_amount = final_total_amount = total_discount = final_tot_discount = total_tax = final_tax = final_other_charges = final_adj_amt=0.00
		
		if invoice_rec.grn_type == 'from_po_grn':
			
			for line in invoice_rec.pogrn_line_ids:
				val = 0.00		
				amt_to_per = (line.discount / (line.tot_rec_qty * line.price_unit or 1.0 )) * 100
				kg_discount_per = line.kg_discount_per
				tot_discount_per = amt_to_per + kg_discount_per
				for c in self.pool.get('account.tax').compute_all(cr, uid, line.invoice_tax_ids,
					line.price_unit * (1-(tot_discount_per or 0.0)/100.0), line.tot_rec_qty, line.product_id)['taxes']:
					val += c.get('amount', 0.0)
				
				
				### Total Amount ###
				
				line_total = line.tot_rec_qty * line.price_unit
				final_total_amount += line_total
				
				## Total Discount###
				
				tot_disc = ((line_total * tot_discount_per)/100)
				total_discount = tot_disc
				
				final_tot_discount += total_discount
				
				### Tax Amount ###
				
				final_tax += val
				
				### Other Charges ###
				
				final_other_charges = invoice_rec.other_charges_amt

					
				### Net Amount, Actual Amount, Invoice Amount ####
				
				total_net_value += line.net_amt
				
				final_net_value = ((total_net_value + final_other_charges) - invoice_rec.advance_adjusted_amt) + invoice_rec.round_off_amt
				
				final_actual_amount = total_net_value + final_other_charges
				
				
	
				
		if invoice_rec.grn_type == 'from_general_grn':
			
			
			for line in invoice_rec.gengrn_line_ids:
				
				val = 0.00
					
				other_charges = line.general_grn_id.other_charge
						
				amt_to_per = (line.discount / (line.tot_rec_qty * line.price_unit or 1.0 )) * 100
				kg_discount_per = line.kg_discount_per
				tot_discount_per = amt_to_per + kg_discount_per
				for c in self.pool.get('account.tax').compute_all(cr, uid, line.invoice_tax_ids,
					line.price_unit * (1-(tot_discount_per or 0.0)/100.0), line.tot_rec_qty, line.product_id)['taxes']:
					
				 
					val += c.get('amount', 0.0)
					
					
				tot_amt = line.tot_rec_qty * (line.price_unit * (1-(tot_discount_per or 0.0)/100.0))
				
				net_amount = tot_amt + val	
					
				## Writing values into invoice lines ###
				
				
				line_total = line.tot_rec_qty * line.price_unit
				
				line.write({'total_amt':line_total,'net_amt':net_amount})
				
				
				### Total Amount ###
				
				
				final_total_amount += line_total
				
				## Total Discount###
			
				tot_disc = ((line_total * tot_discount_per)/100)
				total_discount = tot_disc
				
				final_tot_discount += total_discount
				
				
				### Tax Amount ###
				
				final_tax += val
				
				### Other Charges ###
				

				final_other_charges = invoice_rec.other_charges_amt
	
				### Net Amount, Actual Amount, Invoice Amount ####
				
				final_net_value = ((final_total_amount + final_tax + final_other_charges) - invoice_rec.discount_amt) + invoice_rec.round_off_amt
				
				final_actual_amount = ((final_total_amount + final_tax + final_other_charges) - invoice_rec.discount_amt)
				
		
		if invoice_rec.grn_type == 'others':
			
			for line in invoice_rec.service_line_ids:
				val = 0.00		
				amt_to_per = (line.discount / (line.tot_rec_qty * line.price_unit or 1.0 )) * 100
				kg_discount_per = line.kg_discount_per
				tot_discount_per = amt_to_per + kg_discount_per
				for c in self.pool.get('account.tax').compute_all(cr, uid, line.invoice_tax_ids,
					line.price_unit * (1-(tot_discount_per or 0.0)/100.0), line.tot_rec_qty, line.product_id)['taxes']:
					val += c.get('amount', 0.0)
				
				
				### Total Amount ###
				
				line_total = line.tot_rec_qty * line.price_unit
				final_total_amount += line_total
				
				## Total Discount###
				
				tot_disc = ((line_total * tot_discount_per)/100)
				total_discount = tot_disc
				
				final_tot_discount += total_discount
				
				### Tax Amount ###
				
				final_tax += val
				
				### Other Charges ###
				
				final_other_charges = invoice_rec.other_charges_amt

					
				### Net Amount, Actual Amount, Invoice Amount ####
				
				total_net_value += line.net_amt
				total_net_value = total_net_value 
				
				final_net_value = ((total_net_value + final_other_charges) - invoice_rec.advance_adjusted_amt) + invoice_rec.round_off_amt
				
				final_actual_amount = total_net_value + final_other_charges
				
				
				
		self.write(cr, uid, ids[0], {
					'total_amt': final_total_amount,
					'discount_amt': final_tot_discount,
					'tax_amt':final_tax,
					'other_charges_amt':final_other_charges,
					'actual_amt' : final_actual_amount, 
					'invoice_amt': final_net_value, 
					'advance_adjusted_amt': final_adj_amt or 0.00, 
					'net_amt': final_net_value})
			

		return True
		
		
		
	def entry_confirm(self, cr, uid, ids,context=None):
		invoice_rec = self.browse(cr,uid,ids[0])
		
		self.compute_values(cr,uid,ids,context = context)
		
		### Checking Advance date ###
		
		today_date = today.strftime('%Y-%m-%d')
		
		if invoice_rec.invoice_date > today_date:
			raise osv.except_osv(
					_('Warning!'),
					_('Invoice Date should not be greater than current date'))
					
		if invoice_rec.sup_invoice_date > today_date:
			raise osv.except_osv(
					_('Warning!'),
					_('Supplier Invoice Date should not be greater than current date'))
			
		
		### Check Advance Amount greater than Zero ###
		
		if invoice_rec.grn_type == 'from_po_grn':
			
			
			if not invoice_rec.pogrn_line_ids:
				
				raise osv.except_osv(
						_('Warning!'),
						_('You cannot confirm the entry without Invoice Line'))
						
			else:
				
		
				for line in invoice_rec.pogrn_line_ids:
				
				
			
					if line.price_unit == 0.00:
						raise osv.except_osv(
							_('Price Unit Cannot be zero!'),
							_('You cannot process Invoice with Price Unit Zero for Product %s.' %(line.product_id.name)))
							
							
		if invoice_rec.grn_type == 'from_general__grn':
			
			
			if not invoice_rec.gengrn_line_ids:
				
				raise osv.except_osv(
						_('Warning!'),
						_('You cannot confirm the entry without Invoice Line'))
						
			else:
				
		
				for line in invoice_rec.gengrn_line_ids:
				
				
			
					if line.price_unit == 0.00:
						raise osv.except_osv(
							_('Price Unit Cannot be zero!'),
							_('You cannot process Invoice with Price Unit Zero for Product %s.' %(line.product_id.name)))
					
		self.write(cr,uid,ids[0],{'state':'confirmed',
								  'confirm_flag':'True',
								  'conf_user_id':uid,
								  'confirmed_date':dt_time,
								  'name': self.pool.get('ir.sequence').get(cr, uid, 'kg.purchase.invoice') or '',
								   })
		
		
		return True
		
	def entry_approve(self, cr, uid, ids,context=None):
		invoice_rec = self.browse(cr,uid,ids[0])
		po_advance_obj = self.pool.get('kg.po.advance')
		so_advance_obj = self.pool.get('kg.so.advance')
		
		
		po_advance_line_obj = self.pool.get('kg.po.advance.line')
		so_advance_line_obj = self.pool.get('kg.so.advance.line')
		
		#if invoice_rec.conf_user_id.id == uid:
		#	raise osv.except_osv(
		#			_('Warning'),
		#			_('Approve cannot be done by Confirmed user'))
		
		if invoice_rec.type == 'from_po':
			
			
			if invoice_rec.grn_type == 'from_po_grn':
				
				cr.execute(""" select grn_id from purchase_invoice_grn_ids where invoice_id = %s """ %(invoice_rec.id))
				grn_data = cr.dictfetchall()
				
				for item in grn_data:
					
				
					
					grn_sql = """ update kg_po_grn set state='inv' where id = %s  """ %(item['grn_id'])
					cr.execute(grn_sql)
					
			if invoice_rec.grn_type == 'from_general_grn':
				
				
				cr.execute(""" select grn_id from purchase_invoice_general_grn_ids where invoice_id = %s """ %(invoice_rec.id))
				grn_data = cr.dictfetchall()
				
				for item in grn_data:
										
					grn_sql = """ update kg_general_grn set state='inv' where id = %s  """ %(item['grn_id'])
					cr.execute(grn_sql)
				

			if invoice_rec.poadvance_line_ids:
				
				for adv_line in invoice_rec.poadvance_line_ids:
					if adv_line.current_adv_amt > 0:
						
						sql = """select id from kg_po_advance where id=%s and po_id=%s"""%(adv_line.po_advance_id.id,adv_line.po_id.id)
						cr.execute(sql)
						data = cr.dictfetchall()
						
						po_advance_line_rec = self.pool.get('kg.po.advance').browse(cr, uid, data[0]['id'])
						
						po_advance_bal_amt = po_advance_line_rec.bal_adv - adv_line.current_adv_amt
					
						if data:
					
							po_advance_line_rec.write({'bal_adv':po_advance_bal_amt})
						
		if invoice_rec.type == 'from_so':
				
			if invoice_rec.soadvance_line_ids:
				
				for adv_line in invoice_rec.soadvance_line_ids:

					if adv_line.current_adv_amt > 0:
						
						
						sql = """select id from kg_so_advance where id=%s and so_id=%s"""%(adv_line.so_advance_id.id,adv_line.so_id.id)
						cr.execute(sql)
						data = cr.dictfetchall()
						
						so_advance_line_rec = self.pool.get('kg.so.advance').browse(cr, uid, data[0]['id'])
						
						so_advance_bal_amt = so_advance_line_rec.bal_adv - adv_line.current_adv_amt
					
						if data:
					
							so_advance_line_rec.write({'bal_adv':so_advance_bal_amt})
							
		self.write(cr,uid,ids[0],{'state':'approved',
								  'approve_flag':'True',
								  'app_user_id':uid,
								  'approved_date':dt_time,
								   })	
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
		
	def invoice_to_helpdesk(self,cr,uid,ids = 0 ,context = None):
		my_db = MySQLdb.connect("10.100.1.125","erp_user","kgisl","helpdesk" ) # Live
		cursor = my_db.cursor()
		cur_date = datetime.now()+ timedelta(minutes = 328)
		cur_date = cur_date.strftime('%Y-%m-%d %H:%M:%S')
		cr.execute(""" SELECT current_database();""")
		db = cr.dictfetchall()
		if db[0]['current_database'] == 'Empereal-KGDS':
			db[0]['current_database'] = 'KGDSL'
		elif db[0]['current_database'] == 'FSL':
			db[0]['current_database'] = 'KGFSL'
		elif db[0]['current_database'] == 'IIM':
			db[0]['current_database'] = 'KGISLIIM'
		elif db[0]['current_database'] == 'IIM_HOSTEL':
			db[0]['current_database'] = 'KGISL IIM Hostel'
		elif db[0]['current_database'] == 'KGISL-SD':
			db[0]['current_database'] = 'KGISL'
		elif db[0]['current_database'] == 'CHIL':
			db[0]['current_database'] = 'CHIL'
		elif db[0]['current_database'] == 'KGCAS':
			db[0]['current_database'] = 'KGCAS'
		elif db[0]['current_database'] == 'KGISL':
			db[0]['current_database'] = 'KGISL'
		elif db[0]['current_database'] == 'KITE':
			db[0]['current_database'] = 'KITE'
		elif db[0]['current_database'] == 'TRUST':
			db[0]['current_database'] = 'TRUST'
		else:
			db[0]['current_database'] = 'Others'
		cr.execute("""
						select inv.id as inv_id,
						part.name as supplier_name,
						inv.sup_invoice_no as inv_no,
						usr_part.name as created_by,
						usr_part.email as create_email,
						to_char(inv.sup_invoice_date,'dd-mm-yyyy') as invoice_date,
						round(inv.net_amt::numeric,2) as inv_amt,
						to_char(inv.payment_due_date,'dd-mm-yyyy') as payment_due_date

						from kg_purchase_invoice inv 
						left join res_partner part on (inv.supplier_id = part.id)
						left join res_users usr on (inv.conf_user_id = usr.id)
						left join res_partner usr_part on (usr_part.id = usr.partner_id)
						where inv.helpdesk_flag = 'f' and inv.state = 'approved'""")
						
		helpdesk_data = cr.dictfetchall()
		if helpdesk_data:
			for item in helpdesk_data:
				
				short_desc = item['supplier_name']+'-'+item['inv_no']
				desc = 'Supplier Name:'+item['supplier_name']+'<br> Invoice Number:'+item['inv_no']+'<br> Invoice Date:'+item['invoice_date']+'<br> Invoice Amount:'+str(item['inv_amt'])+'<br> Payment due date as per PO:'+item['payment_due_date']
				sql = """ INSERT INTO `erp_invoices`(`supplier_name`, `short_description`,`description`, `invoice_no`, `invoice_amt`, 
						`created_by`, `created_at`, `invoice_date`,`category`) VALUES ('%s','%s','%s','%s','%s','%s',
						'%s','%s','%s')"""%(item['supplier_name'],short_desc,desc,item['inv_no'],item['inv_amt'],item['create_email'],cur_date,item['invoice_date'],db[0]['current_database'])
				try:
					cursor.execute(sql)
					my_db.commit()   
					cr.execute("""update kg_purchase_invoice set helpdesk_flag = 't' where id = %s"""%(item['inv_id']))
				except:
				   my_db.rollback()		   
			my_db.close()
		else:
			pass				

	def unaccounted_grn_credit_register_scheduler(self,cr,uid,ids=0,context = None):
		cr.execute(""" SELECT current_database();""")
		db = cr.dictfetchall()
		if db[0]['current_database'] == 'Empereal-KGDS':
			db[0]['current_database'] = 'Empereal-KGDS'
		elif db[0]['current_database'] == 'FSL':
			db[0]['current_database'] = 'FSL'
		elif db[0]['current_database'] == 'IIM':
			db[0]['current_database'] = 'IIM'
		elif db[0]['current_database'] == 'IIM_HOSTEL':
			db[0]['current_database'] = 'IIM Hostel'
		elif db[0]['current_database'] == 'KGISL-SD':
			db[0]['current_database'] = 'KGISL'
		elif db[0]['current_database'] == 'CHIL':
			db[0]['current_database'] = 'CHIL'
		elif db[0]['current_database'] == 'KGCAS':
			db[0]['current_database'] = 'KGCAS'
		elif db[0]['current_database'] == 'KGISL':
			db[0]['current_database'] = 'KGISL'
		elif db[0]['current_database'] == 'KITE':
			db[0]['current_database'] = 'KITE'
		elif db[0]['current_database'] == 'TRUST':
			db[0]['current_database'] = 'TRUST'
		elif db[0]['current_database'] == 'CANTEEN':
			db[0]['current_database'] = 'CANTEEN'
		else:
			db[0]['current_database'] = 'Others'
			
			
		cr.execute(""" select pg.id from kg_po_grn pg where pg.state = 'done' and pg.approved_date::date='%s' and pg.billing_status = 'applicable' and
						pg.payment_type = 'credit'
					   union
					   select gg.id from kg_general_grn gg where gg.state ='done' and gg.approved_date::date='%s' and gg.bill = 'applicable' and
						gg.payment_type = 'credit'"""
					    %(time.strftime('%Y-%m-%d'),time.strftime('%Y-%m-%d')))
		grn_data = cr.dictfetchall()	
		
		
		print "--------------------------------------->",grn_data
		
		if grn_data:	
			
			
			cr.execute("""select all_daily_auto_scheduler_mails('Unaccount Goods Receipt Credit Register')""")
			data = cr.fetchall();
			cr.execute("""select (select sum(total) from ((select kg_po_grn.amount_total as total
							from kg_po_grn
							left join res_partner on res_partner.id = kg_po_grn.supplier_id
							left join purchase_invoice_grn_ids on purchase_invoice_grn_ids.grn_id = kg_po_grn.id
							left join kg_purchase_invoice on kg_purchase_invoice.id = purchase_invoice_grn_ids.invoice_id
							where kg_po_grn.billing_status = 'applicable' and
							kg_po_grn.payment_type = 'credit' and
							kg_po_grn.state in ('done') and kg_purchase_invoice.state = 'confirmed'
							group by 1 )
						union
							(select 
							kg_general_grn.amount_total as total
							from kg_general_grn
							left join res_partner on res_partner.id = kg_general_grn.supplier_id
							left join purchase_invoice_general_grn_ids on purchase_invoice_general_grn_ids.grn_id=kg_general_grn.id
							left join kg_purchase_invoice on kg_purchase_invoice.id=purchase_invoice_general_grn_ids.invoice_id
							where kg_general_grn.bill = 'applicable' and
							kg_general_grn.payment_type = 'credit' and
							kg_general_grn.state in ('done') and kg_purchase_invoice.state = 'confirmed'
							group by 1 )) as p1)
						+
						(select sum(total) from ((select kg_po_grn.amount_total as total
								from kg_po_grn
								left join res_partner on res_partner.id = kg_po_grn.supplier_id
								left join purchase_invoice_grn_ids on purchase_invoice_grn_ids.grn_id = kg_po_grn.id
								left join kg_purchase_invoice on kg_purchase_invoice.id = purchase_invoice_grn_ids.invoice_id
								where kg_po_grn.billing_status = 'applicable' and
								kg_po_grn.payment_type = 'credit' and
								 
								kg_po_grn.state in ('done') and kg_purchase_invoice.state = 'draft'
								group by 1) 
						union
								(select	kg_general_grn.amount_total as total
								from kg_general_grn
								left join res_partner on res_partner.id = kg_general_grn.supplier_id
								left join purchase_invoice_general_grn_ids on purchase_invoice_general_grn_ids.grn_id=kg_general_grn.id
								left join kg_purchase_invoice on kg_purchase_invoice.id=purchase_invoice_general_grn_ids.invoice_id
								where 
								kg_general_grn.bill = 'applicable' and
								kg_general_grn.payment_type = 'credit' and
								
								kg_general_grn.state in ('done') and kg_purchase_invoice.state = 'draft'
								group by 1		)) as pp1)
								+
						(select sum(total) from ((select kg_po_grn.amount_total as total
								from kg_po_grn
								left join res_partner on res_partner.id = kg_po_grn.supplier_id
								left join purchase_order on purchase_order.id = kg_po_grn.po_id
								left join kg_service_order on kg_service_order.id = kg_po_grn.so_id
								left join kg_pogrn_purchase_invoice_line on kg_pogrn_purchase_invoice_line.so_id != kg_service_order.id
								left join kg_purchase_invoice on kg_purchase_invoice.id != kg_pogrn_purchase_invoice_line.invoice_header_id
								left join purchase_invoice_grn_ids on kg_purchase_invoice.id = purchase_invoice_grn_ids.invoice_id
								where kg_po_grn.billing_status = 'applicable' and
								kg_po_grn.payment_type = 'credit' and
								to_char(kg_po_grn.approved_date,'dd-mm-yyyy') = '%s' and 
								kg_po_grn.state in ('done') and 
								kg_po_grn.id not in (select grn_id from purchase_invoice_grn_ids)
								group by 1)
							union
								(select 
								kg_general_grn.amount_total as total
								from kg_general_grn
								left join res_partner on res_partner.id = kg_general_grn.supplier_id
								left join purchase_order on purchase_order.id = kg_general_grn.po_id
								left join kg_gengrn_purchase_invoice_line on kg_gengrn_purchase_invoice_line.general_grn_id != kg_general_grn.id
								left join kg_purchase_invoice on kg_purchase_invoice.id != kg_gengrn_purchase_invoice_line.invoice_header_id
								left join purchase_invoice_general_grn_ids on kg_purchase_invoice.id = purchase_invoice_general_grn_ids.invoice_id
								where 
								kg_general_grn.bill = 'applicable' and
								kg_general_grn.payment_type = 'credit' and
								to_char(kg_general_grn.approved_date,'dd-mm-yyyy') = '%s' and
								kg_general_grn.state in ('done') and 
								kg_general_grn.id not in (select grn_id from purchase_invoice_general_grn_ids)
								group by 1)) as pp2 )as total"""%(time.strftime('%d-%m-%Y'),time.strftime('%d-%m-%Y')))
			total_sum = cr.dictfetchall();
			
			db = db[0]['current_database'].encode('utf-8')
			total_sum = str(total_sum[0]['total'])
			vals = self.sechedular_email_ids(cr,uid,ids,context = context)
			if (not vals['email_to']) and (not vals['email_cc']):
				pass
			else:
				ir_mail_server = self.pool.get('ir.mail_server')
				msg = ir_mail_server.build_email(
						email_from = vals['email_from'][0],
						email_to = vals['email_to'],
						subject = "ERP Unaccounted GRN - Credit for "+db +' as on '+time.strftime('%d-%m-%Y')+'. Total Amount (Rs.):' + total_sum,
						body = data[0][0],
						email_cc = vals['email_cc'],
						object_id = ids and ('%s-%s' % (ids, 'kg.purchase.invoice')),
						subtype = 'html',
						subtype_alternative = 'plain')
				res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
				
		else:
			pass		
				
		return True
	
	
kg_purchase_invoice()


class kg_pogrn_purchase_invoice_line(osv.osv):

	_name = "kg.pogrn.purchase.invoice.line"
	_description = "PO GRN Purchase Invoice Line"
	_columns = {
	
		'po_grn_id' : fields.many2one('kg.po.grn', 'GRN NO.'),		
		'dc_no' : fields.char('VENDOR DC NO.'),
		'po_so_no' : fields.char('PO/SO NO.'),
		'po_id' : fields.many2one('purchase.order','Purchase Order'),
		'so_id' : fields.many2one('kg.service.order','Service Order'),
		'product_id' : fields.many2one('product.product','PRODUCT'),
		'po_so_qty': fields.float('PO/SO QTY'),
		'tot_rec_qty': fields.float('RECEIVED QTY'),
		'uom_id': fields.many2one('product.uom','RECEIVED UOM'),
		'price_unit': fields.float('RATE'),
		'total_amt': fields.float('TOTAL AMOUNT'),
		'discount': fields.float('DISCOUNT(-)'),
		'kg_discount_per': fields.float('DISCOUNT%(-)'),
		'invoice_tax_ids': fields.many2many('account.tax', 'pogrn_purchase_invoice_tax', 'pogrn_invoice_line_id', 'taxes_id', 'Taxes(+)'),
		'net_amt': fields.float('NET AMOUNT'),
		
		'invoice_header_id' : fields.many2one('kg.purchase.invoice', 'Header ID'),
		'po_grn_line_id':fields.many2one('po.grn.line','PO GRN Entry Line'),
		'po_line_id':fields.many2one('purchase.order.line','PO Line'),
		'so_line_id':fields.many2one('kg.service.order.line','SO Line'),
		'brand_id':fields.many2one('kg.brand.master','Brand'),
	}
	
	

	
kg_pogrn_purchase_invoice_line()


class kg_grn_service_invoice_line(osv.osv):

	_name = "kg.grn.service.invoice.line"
	_description = "GRN Service Invoice Line"
	_columns = {
	
		'soi_id' : fields.many2one('kg.service.invoice', 'Service Invoice No.'),		
		'so_id' : fields.many2one('kg.service.order','Service Order'),
		'product_id' : fields.many2one('product.product','PRODUCT'),
		'po_so_qty': fields.float('PO/SO QTY'),
		'dc_no' : fields.char('VENDOR DC NO.'),
		'tot_rec_qty': fields.float('RECEIVED QTY'),
		'uom_id': fields.many2one('product.uom','RECEIVED UOM'),
		'price_unit': fields.float('RATE'),
		'total_amt': fields.float('TOTAL AMOUNT'),
		'discount': fields.float('DISCOUNT(-)'),
		'kg_discount_per': fields.float('DISCOUNT%(-)'),
		'invoice_tax_ids': fields.many2many('account.tax', 'service_purchase_invoice_tax', 'service_invoice_line_id', 'taxes_id', 'Taxes(+)'),
		'net_amt': fields.float('NET AMOUNT'),
		
		'invoice_header_id' : fields.many2one('kg.purchase.invoice', 'Header ID'),
		
		
	}
	
	

	
kg_grn_service_invoice_line()


class kg_gengrn_purchase_invoice_line(osv.osv):

	_name = "kg.gengrn.purchase.invoice.line"
	_description = "General GRN Purchase Invoice Line"
	_columns = {
	
		'general_grn_id' : fields.many2one('kg.general.grn', 'GRN NO.'),
		'general_grn_line_id' : fields.many2one('kg.general.grn.line', 'GRN Line NO.'),			
		'dc_no' : fields.char('VENDOR DC NO.'),
		'product_id' : fields.many2one('product.product','PRODUCT'),
		'tot_rec_qty': fields.float('RECEIVED QTY'),
		'uom_id': fields.many2one('product.uom','RECEIVED UOM'),
		'price_unit': fields.float('RATE'),
		'total_amt': fields.float('TOTAL AMOUNT'),
		'discount': fields.float('DISCOUNT Amt(-)'),
		'kg_discount_per': fields.float('DISCOUNT%(-)'),
		'invoice_tax_ids': fields.many2many('account.tax', 'gengrn_purchase_invoice_tax', 'gengrn_invoice_line_id', 'taxes_id', 'Taxes(+)'),
		'net_amt': fields.float('NET AMOUNT'),
		
		'invoice_header_id' : fields.many2one('kg.purchase.invoice', 'Header ID'),
		
		
	}
	

	
kg_gengrn_purchase_invoice_line()


class kg_poadvance_purchase_invoice_line(osv.osv):

	_name = "kg.poadvance.purchase.invoice.line"
	_description = "PO Advance Purchase Invoice Line"
	_columns = {
	
		'po_advance_id' : fields.many2one('kg.po.advance', 'PO Advance No', readonly=True),
		'po_advance_date': fields.date('PO Advance Date'),
		'po_advance_line_id' : fields.many2one('kg.po.advance.line', 'PO Advance Line', readonly=True),		
		'po_id': fields.many2one('purchase.order','PO No'),		
		'po_amt': fields.float('PO Amount', readonly=True),
		'tot_advance_amt': fields.float('Total Advance Amount', readonly=True),
		'already_adjusted_amt': fields.float('Already Adjusted Advance Amount', readonly=True),
		'balance_amt': fields.float('Balance Advance to be adjusted', readonly=True),
		'current_adv_amt': fields.float('Current Adjustment Amount',required=True),
		'invoice_header_id' : fields.many2one('kg.purchase.invoice', 'Header ID'),
		
		
	}
	
	def onchange_po_id(self, cr, uid, ids, po_id):
		poadvance_obj = self.pool.get('kg.po.advance.line')
		poadvance_ids = poadvance_obj.search(cr, uid, [('po_id','=',po_id)])
		if poadvance_ids:
			poadvance_rec = poadvance_obj.browse(cr, uid, poadvance_ids[0])
			return {'value': {
				'po_advance_id' : poadvance_rec.advance_header_id.id,
				'po_advance_date' : poadvance_rec.advance_date,
				'po_amt' : poadvance_rec.net_amt,
				'tot_advance_amt' : poadvance_rec.advance_amt,
				'already_adjusted_amt' : poadvance_rec.advance_amt - poadvance_rec.balance_advance_amt,
				'balance_amt' : poadvance_rec.balance_advance_amt,
				}}
		else:
			return True
			
	
	

	
kg_poadvance_purchase_invoice_line()



class kg_soadvance_purchase_invoice_line(osv.osv):

	_name = "kg.soadvance.purchase.invoice.line"
	_description = "SO Advance Purchase Invoice Line"
	_columns = {
	
		'so_advance_id' : fields.many2one('kg.so.advance', 'SO Advance No', readonly=True),
	    'so_advance_date': fields.date('SO Advance Date'),
		'so_advance_line_id' : fields.many2one('kg.so.advance.line', 'PO Advance Line', readonly=True),	
		'so_id': fields.many2one('kg.service.order','SO No'),
		'so_amt': fields.float('SO Amount', readonly=True),
		'tot_advance_amt': fields.float('Total Advance Amount', readonly=True),
		'already_adjusted_amt': fields.float('Already Adjusted Advance Amount', readonly=True),
		'balance_amt': fields.float('Balance Advance to be adjusted', readonly=True),
		'current_adv_amt': fields.float('Current Adjustment Amount', required=True),
		'invoice_header_id' : fields.many2one('kg.purchase.invoice', 'Header ID'),
		
		
	}
	
	def onchange_so_id(self, cr, uid, ids, so_id):
		soadvance_obj = self.pool.get('kg.so.advance.line')
		soadvance_ids = soadvance_obj.search(cr, uid, [('so_id','=',so_id)])
		if soadvance_ids:
			soadvance_rec = soadvance_obj.browse(cr, uid, soadvance_ids[0])
			return {'value': {
				'so_advance_id' : soadvance_rec.advance_header_id.id,
				'so_advance_date' : soadvance_rec.advance_date,
				'so_advance_line_id' : soadvance_rec.id,
				'so_amt' : soadvance_rec.net_amt,
				'tot_advance_amt' : soadvance_rec.advance_amt,
				'already_adjusted_amt' : soadvance_rec.advance_amt - soadvance_rec.balance_advance_amt,
				'balance_amt' : soadvance_rec.balance_advance_amt,
				}}
		else:
			return True
			
	

	
kg_soadvance_purchase_invoice_line()
