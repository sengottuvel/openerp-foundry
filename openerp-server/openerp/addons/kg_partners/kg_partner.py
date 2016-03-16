from functools import partial
import logging
from lxml import etree
from lxml.builder import E
import openerp
import time
from openerp import SUPERUSER_ID
from openerp import pooler, tools
import openerp.exceptions
from openerp.osv import fields,osv
from openerp.osv.orm import browse_record
from openerp.tools.translate import _


class kg_partner(osv.osv):

	_name = "res.partner"
	_inherit = "res.partner"
	_description = "Partner Managment"
	
	def _get_modify(self, cr, uid, ids, field_name, arg, context=None):
		res={}
		po_obj = self.pool.get('purchase.order')
		po_amd_obj = self.pool.get('kg.purchase.amendment')
		so_obj = self.pool.get('kg.service.order')
		po_adv_obj = self.pool.get('kg.po.advance')
		so_adv_obj = self.pool.get('kg.so.advance')
		ser_inv_obj = self.pool.get('kg.service.invoice')
		gen_grn_obj = self.pool.get('kg.general.grn')
		po_grn_obj = self.pool.get('kg.po.grn')
		com_grn_obj = self.pool.get('kg.common.grn')
		gate_pass_obj = self.pool.get('kg.gate.pass')
		pur_inv_obj = self.pool.get('kg.purchase.invoice')
		con_inw_obj = self.pool.get('kg.contractor.inward')
		po_man_obj = self.pool.get('kg.po.manual.closing')
		so_man_obj = self.pool.get('kg.so.manual.closing')
		for h in self.browse(cr, uid, ids, context=None):
			res[h.id] = 'no'
			po_ids = po_obj.search(cr,uid,[('partner_id','=',h.id)])
			po_amd_ids = po_amd_obj.search(cr,uid,[('partner_id_amend','=',h.id)])
			so_ids = so_obj.search(cr,uid,[('partner_id','=',h.id)])
			po_adv_ids = po_adv_obj.search(cr,uid,[('supplier_id','=',h.id)])
			so_adv_ids = so_adv_obj.search(cr,uid,[('supplier_id','=',h.id)])
			ser_inv_ids = ser_inv_obj.search(cr,uid,[('partner_id','=',h.id)])
			gen_grn_ids = gen_grn_obj.search(cr,uid,[('supplier_id','=',h.id)])
			po_grn_ids = po_grn_obj.search(cr,uid,[('supplier_id','=',h.id)])
			com_grn_ids = com_grn_obj.search(cr,uid,[('supplier_id','=',h.id)])
			gate_pass_ids = gate_pass_obj.search(cr,uid,[('partner_id','=',h.id)])
			pur_inv_ids = pur_inv_obj.search(cr,uid,[('supplier_id','=',h.id)])
			con_inw_ids = con_inw_obj.search(cr,uid,[('supplier_id','=',h.id)])
			po_man_ids = po_man_obj.search(cr,uid,[('partner_id','=',h.id)])
			so_man_ids = so_man_obj.search(cr,uid,[('partner_id','=',h.id)])
			if po_ids or po_amd_ids or so_ids or po_adv_ids or so_adv_ids or ser_inv_ids or gen_grn_ids or po_grn_ids or com_grn_ids or gate_pass_ids or pur_inv_ids or con_inw_ids or so_man_ids:
				res[h.id] = 'yes'
		return res
		
	_columns = {
	
	'city_id' : fields.many2one('res.city', 'City'),
	'tin_no' : fields.char('TIN'),
	'pan_no' : fields.char('PAN'),
	'tan_no' : fields.char('TAN'),
	'cst_no' : fields.char('CST'),
	'gst_no' : fields.char('GST'),
	'supply_type': fields.selection([('material','Material'),('service','Service'),('contractor','Contractor'),('labour','Labour'),('all','All')],'Supply Type'),
	'company_type': fields.selection([('individual','Individual'),('company','Company'),('trust','Trust')],'Type'),
	'tds': fields.selection([('yes','Yes'),('no','No')],'TDS Applicable'),
	'grade': fields.selection([('a','A'),('b','B'),('c','C')],'Grade'),
	'payment_id': fields.many2one('kg.payment.master','Payment Terms'),
	'language': fields.selection([('tamil', 'Tamil'),('english', 'English'),('hindi', 'Hindi'),('malayalam', 'Malayalam'),('others','Others')],'Preferred Language'),
	'cheque_in_favour': fields.char('Cheque in Favor Of'),
	'advance_limit': fields.float('Credit Limit'),
	'transport_id': fields.many2one('kg.transport','Transport'),
	'contact_person': fields.char('Contact Person', size=128),
	'landmark': fields.char('Landmark', size=128),
	'partner_state': fields.selection([('draft','Draft'),('approve','Approved'),('cancel','Cancelled')],'Status'),
	'group_flag': fields.boolean('Is Group Company'),
	'delivery_id': fields.many2one('kg.delivery.master','Delivery Type'),
	#'child_ids': fields.one2many('res.partner', 'parent_id', 'Contacts', domain=[('active','=',True)]),
	'creation_date': fields.datetime('Creation Date',readonly=True),
	'created_by': fields.many2one('res.users', 'Created by',readonly=True),
	'confirmed_date': fields.datetime('Confirmed Date',readonly=True),
	'confirmed_by': fields.many2one('res.users','Confirmed By',readonly=True),
	'approved_date': fields.datetime('Approved Date',readonly=True),
	'approved_by': fields.many2one('res.users','Approved By',readonly=True),
	'cancel_date': fields.datetime('Cancelled Date', readonly=True),
	'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
	'updated_date': fields.datetime('Last Update Date',readonly=True),
	'updated_by': fields.many2one('res.users','Last Updated By',readonly=True),
	'con_designation': fields.char('Designation'),
	'con_whatsapp': fields.char('Whatsapp No'),
	'acc_number': fields.char('Whatsapp No'),
	'bank_name': fields.char('Whatsapp No'),
	'bank_bic': fields.char('Whatsapp No'),
	'delivery_ids':fields.one2many('kg.delivery.address', 'src_id', 'Delivery Address'),
	'billing_ids':fields.one2many('kg.billing.address', 'bill_id', 'Billing Address'),
	'consult_ids':fields.one2many('kg.consultant.fee', 'consult_id', 'Consultant Fees'),
	'dealer': fields.boolean('Dealer'),
	'economic_category': fields.selection([('budget','Budget'),('loyalty','Loyalty')],'Economic Category'),
	'sector': fields.selection([('cp','CP'),('ip','IP'),('both','Both')],'Sector'),
	'dealer_id': fields.many2one('res.partner','Dealer Name',domain=[('dealer','=',True)]),
	'remark': fields.text('Approve'),
	'cancel_remark': fields.text('Cancel Remarks'),
	'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=3),
	
	
	}
	
	_defaults = {
	  
	  'is_company': True,
	  'creation_date': fields.datetime.now,
	  'created_by': lambda obj, cr, uid, context: uid,
	  'partner_state': 'draft',
	  'modify': 'no',
		 
	}

	def onchange_city(self, cr, uid, ids, city_id, context=None):
		if city_id:
			state_id = self.pool.get('res.city').browse(cr, uid, city_id, context).state_id.id
			return {'value':{'state_id':state_id}}
		return {}
	
	def onchange_zip(self,cr,uid,ids,zip,context=None):
		if len(str(zip)) == 6:
			value = {'zip':zip}
		else:
			raise osv.except_osv(_('Check zip number !!'),
				_('Please enter six digit number !!'))
		
		return {'value': value}
			
	def approve_partner(self, cr, uid, ids, context=None): 
		rec = self.browse(cr, uid, ids[0])
		self.write(cr, uid, ids, {'partner_state': 'approve','approved_by':uid,'approved_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		
		return True

	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'partner_state': 'draft'})
		return True
		
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		self.write(cr, uid, ids, {'partner_state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		
		return True
				
	def write(self, cr, uid, ids, vals, context=None):
		print"valsssssS",vals
		#if len(str(vals['zip'])) == 6:
		#	pass
		#else:
		#	raise osv.except_osv(_('Check zip number !!'),
		#		_('Please enter six digit number !!'))
		vals.update({'updated_date': time.strftime('%Y-%m-%d %H:%M:%S'),'updated_by':uid})
		return super(kg_partner, self).write(cr, uid, ids, vals, context)
		
kg_partner()



class kg_delivery_address(osv.osv):

	_name = "kg.delivery.address"
	_description = "Delivery Address"
	
	_columns = {

	'src_id': fields.many2one('res.partner', 'Partner Master'),
	'street': fields.char('Street', size=128,select=True),
	'street1': fields.char('Street 1', size=128,select=True),
	'landmark': fields.char('Landmark',size=128),
	'city_id': fields.many2one('res.city', 'City',select=True),
	'state_id': fields.many2one('res.country.state', 'State'),
	'country_id': fields.many2one('res.country', 'Country'),	
	'contact_no': fields.char('Contact No', size=128),
	'zip': fields.char('ZIP', size=128),
	'date': fields.date('Creation Date'),
	'default': fields.boolean('Default'),
	
	}

	_defaults = {

	'date' : fields.date.context_today,

	} 
	
kg_delivery_address()

class kg_billing_address(osv.osv):

	_name = "kg.billing.address"
	_description = "Billing Address"
	
	_columns = {

	'bill_id': fields.many2one('res.partner', 'Partner Master'),
	'street': fields.char('Street', size=128,select=True),
	'street1': fields.char('Street 1', size=128,select=True),
	'landmark': fields.char('Landmark',size=128),
	'city_id': fields.many2one('res.city', 'City',select=True),
	'state_id': fields.many2one('res.country.state', 'State'),
	'country_id': fields.many2one('res.country', 'Country'),	
	'contact_no': fields.char('Contact No', size=128),
	'zip': fields.char('ZIP', size=128),
	'date': fields.date('Creation Date'),
	'default': fields.boolean('Default'),
	
	}

	_defaults = {

	'date' : fields.date.context_today,

	} 

kg_billing_address()


class kg_consultant_fee(osv.osv):

	_name = "kg.consultant.fee"
	_description = "Consultant Fees"
	
	_columns = {

	'consult_id': fields.many2one('res.partner', 'Partner Master'),
	'effective_date': fields.date('Effective Date'),
	'value': fields.float('Value (%)'),
	'state': fields.selection([('active','Active'),('expire','Expired')],'Status'),
	'read_flag': fields.boolean('Read Flag'),
	
	}

	_defaults = {

	'state' : 'active',
	'read_flag': False,
	
	} 
	
	def create(self, cr, uid, vals, context=None):
		new_id = super(kg_consultant_fee, self).create(cr, uid, vals, context=context)
		partner = self.browse(cr, uid, new_id, context=context)
		
		obj = self.search(cr,uid,([('consult_id','=',vals['consult_id'])]))
		if obj:
			for item in obj:
				self.write(cr,uid,item,{'state':'expire','read_flag':True})
			self.write(cr,uid,obj[-1],{'state':'active','read_flag':False})
		
		return new_id
		
kg_billing_address()
