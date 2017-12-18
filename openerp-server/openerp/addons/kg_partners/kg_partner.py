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
import re
import base64

class kg_partner(osv.osv):
	
	_name = "res.partner"
	_inherit = "res.partner"
	_description = "Partner Management"
	
	def _get_modify(self, cr, uid, ids, field_name, arg,  context=None):
		res={}
		if field_name == 'modify':
			for h in self.browse(cr, uid, ids, context=None):	
				res[h.id] = 'no'
				cr.execute(""" select * from
				(SELECT tc.table_schema, tc.constraint_name, tc.table_name, kcu.column_name, ccu.table_name
				AS foreign_table_name, ccu.column_name AS foreign_column_name
				FROM information_schema.table_constraints tc
				JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
				JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
				WHERE constraint_type = 'FOREIGN KEY'
				AND ccu.table_name='%s')
				as sam  """ %('res_partner'))
				data = cr.dictfetchall()	
				if data:
					for var in data:
						data = var
						chk_sql = 'Select COALESCE(count(*),0) as cnt from '+str(data['table_name'])+' where '+data['column_name']+' = '+str(ids[0])
						cr.execute(chk_sql)			
						out_data = cr.dictfetchone()
						if out_data:
							if out_data['cnt'] > 0:
								res[h.id] = 'yes'
		return res
	
	_columns = {
	
	'city_id' : fields.many2one('res.city', 'City'),
	'tin_no' : fields.char('TIN',size=15),
	'vat_no' : fields.char('VAT',size=12),
	'pan_no' : fields.char('PAN',size=12),
	'tan_no' : fields.char('TAN',size=12),
	'cst_no' : fields.char('CST',size=12),
	'gst_no' : fields.char('GST'),
	'gs_tin_no' : fields.char('GS TIN NO.',size=15),
	'supply_type': fields.selection([('material','Material'),('service','Service'),('contractor','Contractor'),('labour','Labour'),('all','All')],'Supply Type'),
	'company_type': fields.selection([('individual','Individual'),('company','Company'),('trust','Trust')],'Type'),
	'tds': fields.selection([('yes','Yes'),('no','No')],'TDS Applicable'),
	'grade': fields.selection([('a','A'),('b','B'),('c','C')],'Grade'),
	'payment_id': fields.many2one('kg.payment.master','Payment Terms'),
	'language': fields.selection([('tamil', 'Tamil'),('english', 'English'),('hindi', 'Hindi'),('malayalam', 'Malayalam'),('others','Others')],'Preferred Language'),
	'region': fields.selection([('north','North'),('east','East'),('west','West'),('south','South')],'Region'),
	'cheque_in_favour': fields.char('Cheque in Favor Of'),
	'advance_limit': fields.float('Credit Limit'),
	'transport_id': fields.many2one('kg.transport','Transport'),
	'contact_person': fields.char('Contact Person', size=128),
	'landmark': fields.char('Landmark', size=128),
	'group_flag': fields.boolean('Is Group Company'),
	'delivery_id': fields.many2one('kg.delivery.master','Delivery Type'),
	'con_designation': fields.char('Designation'),
	'con_whatsapp': fields.char('Whatsapp No'),
	'delivery_ids':fields.one2many('kg.delivery.address', 'src_id', 'Delivery Address'),
	'billing_ids':fields.one2many('kg.billing.address', 'bill_id', 'Billing Address'),
	'consult_ids':fields.one2many('kg.consultant.fee', 'consult_id', 'Consultant Fees'),
	'dealer': fields.boolean('Dealer'),
	'economic_category': fields.selection([('budget','Budget'),('loyalty','Loyalty')],'Economic Category'),
	'sector': fields.selection([('cp','CP'),('ip','IP'),('both','Both')],'Marketing Division'),
	'industry_id': fields.many2one('kg.industry.master','Sector'),
	'dealer_id': fields.many2one('res.partner','Dealer Name',domain=[('dealer','=',True)]),
	'remark': fields.text('Approve/Reject'),
	'cancel_remark': fields.text('Cancel Remarks'),
	'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=3),
	'user_ref_id': fields.many2one('res.users','User Name'),
	'adhar_id': fields.char('Adhar ID',size=16),
	'contractor': fields.boolean('Contractor'),
	'tin_flag': fields.boolean('TIN Flag'),
	'mobile_2': fields.char('Mobile2',size=12),
	'email_applicable': fields.selection([('yes','Yes'),('no','No')],'Email Applicable'),
	'sms_applicable': fields.selection([('yes','Yes'),('no','No')],'SMS Applicable'),
	'max_deal_discount': fields.float('Max.Dealer Discount(%)'),
	'max_cust_discount': fields.float('Max.Customer Discount(%)'),
	'max_spl_discount': fields.float('Max.Special Discount(%)'),
	'con_category_id': fields.many2one('kg.contractor.category', 'Contractor category'),
	
	## Entry Info
	
	'creation_date': fields.datetime('Created Date',readonly=True),
	'created_by': fields.many2one('res.users', 'Created by',readonly=True),
	'confirmed_date': fields.datetime('Confirmed Date',readonly=True),
	'confirmed_by': fields.many2one('res.users','Confirmed By',readonly=True),
	'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
	'reject_date': fields.datetime('Reject Date', readonly=True),
	'approved_date': fields.datetime('Approved Date',readonly=True),
	'approved_by': fields.many2one('res.users','Approved By',readonly=True),
	'cancel_date': fields.datetime('Cancelled Date', readonly=True),
	'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
	'updated_date': fields.datetime('Last Updated Date',readonly=True),
	'updated_by': fields.many2one('res.users','Last Updated By',readonly=True),	
	
	}
	
	_defaults = {
	  
		'is_company': True,
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'created_by': lambda obj, cr, uid, context: uid,
		'partner_state': 'draft',
		'modify': 'no',
		'tin_flag': False,
		'company_type': 'company',
		
	}
	
	def onchange_city(self, cr, uid, ids, city_id, context=None):
		if city_id:
			city_rec = self.pool.get('res.city').browse(cr, uid, city_id, context)		
			return {'value':{'state_id':city_rec.state_id.id,'country_id':city_rec.country_id.id}}
		else:
			pass
		return {}
	
	def onchange_zip(self,cr,uid,ids,zip,context=None):
		if len(str(zip)) in range(6,8):
			value = {'zip':zip}
		else:
			raise osv.except_osv(_('Invalid Zip code !!'),_(' Enter your correct 6-8 digits zip code !!'))
		if zip.isdigit() == False:
			raise osv.except_osv(_('Check zip number !!'),_('Please enter numeric values !!'))
		return {'value': value}
	
	def confirm_partner(self, cr, uid, ids, context=None): 
		rec = self.browse(cr, uid, ids[0])
		if rec.partner_state == 'draft':
			self.write(cr, uid, ids, {'partner_state': 'confirm','confirmed_by':uid,'confirmed_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
	def reject_partner(self, cr, uid, ids, context=None): 
		rec = self.browse(cr, uid, ids[0])
		if rec.partner_state == 'confirm':
			if rec.remark:
				self.write(cr, uid, ids, {'partner_state': 'reject','update_user_id':uid,'reject_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Rejection remark is must !!'),_('Enter rejection remark in remark field !!'))
		return True
	
	def approve_partner(self, cr, uid, ids, context=None): 
		rec = self.browse(cr, uid, ids[0])
		if rec.partner_state == 'confirm':
			## Account master creation process start
			
			internal_type = note = account_receivable_id = account_payable_id =  ''
			entry_mode = 'auto'
			account_payable_id = ''
			ac_obj = self.pool.get('account.account')
			old_acc_ids = ac_obj.search(cr,uid,[('master_id','=',rec.id)])
			if old_acc_ids:
				old_acc_rec = ac_obj.browse(cr,uid,old_acc_ids[0])
				ac_obj.write(cr,uid,old_acc_rec.id,{'name': rec.name})
			acc_ids = ac_obj.search(cr,uid,[('name','=',rec.name)])
			ac_type = ''
			if not acc_ids:
				if rec.customer == True:
					ac_type_ids = self.pool.get('account.account.type').search(cr,uid,[('name','=','Asset')])
					if ac_type_ids:
						ac_type_rec = self.pool.get('account.account.type').browse(cr,uid,ac_type_ids[0])
						ac_type = ac_type_rec.id
					internal_type = 'receivable'
					note = 'New Customer Added'
					account_receivable_id = ac_obj.account_creation(cr,uid,rec.name,ac_type,rec.id,entry_mode,internal_type,note,context=context)
				if rec.supplier == True:
					internal_type = 'payable'
					note = 'New Supplier Added'
				if rec.dealer == True:
					internal_type = 'payable'
					note = 'New Delear Added'
				if rec.contractor == True:
					internal_type = 'payable'
					note = 'New Contractor Added'
				if rec.supplier == True or rec.dealer == True or rec.contractor == True:
					ac_type_ids = self.pool.get('account.account.type').search(cr,uid,[('name','=','Liability')])
					if ac_type_ids:
						ac_type_rec = self.pool.get('account.account.type').browse(cr,uid,ac_type_ids[0])
						ac_type = ac_type_rec.id
					account_payable_id = ac_obj.account_creation(cr,uid,rec.name,ac_type,rec.id,entry_mode,internal_type,note,context=context)
				
				self.write(cr, uid, ids, {'property_account_receivable':account_receivable_id,'property_account_payable':account_payable_id})
			
			## Account master creation process end
			
			self.write(cr, uid, ids, {'partner_state': 'approve','approved_by':uid,'approved_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		
		return True
	
	def entry_draft(self,cr,uid,ids,context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.partner_state == 'approve':
			self.write(cr, uid, ids, {'partner_state': 'draft'})
		return True
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.partner_state == 'approve':
			if rec.cancel_remark:
				self.write(cr, uid, ids, {'partner_state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Cancel remark is must !!'),_('Enter the remarks in Cancel remarks field !!'))
		return True
	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.partner_state != 'draft':			
				raise osv.except_osv(_('Delete access denied!'),_('Unable to delete. Draft entry only you can delete !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)	
	
	def write(self, cr, uid, ids, vals, context=None):		
		vals.update({'updated_date': time.strftime('%Y-%m-%d %H:%M:%S'),'updated_by':uid})
		return super(kg_partner, self).write(cr, uid, ids, vals, context)
	
	def _validations(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.zip:
			if len(str(rec.zip)) not in range(6,8) and rec.zip.isdigit() != True:
				raise osv.except_osv(_('Invalid Zip code !!'),_('Enter your correct 6-8 digits zip code !!'))
		if rec.gs_tin_no:
			if len(str(rec.gs_tin_no)) != 15:
				raise osv.except_osv(_('Warning !!'),_('GS TIN No. should contain 15 letters. Else system not allow to save. !!'))
		if rec.cst_no:
			if len(str(rec.cst_no)) != 11 and rec.cst_no.isdigit() != True:
				raise osv.except_osv(_('Warning !!'),_('Enter your correct 11 digits GS TIN No. !!'))
		if rec.vat_no:
			if len(str(rec.vat_no)) != 15:
				raise osv.except_osv(_('Warning !!'),_('Enter your correct 15 letters VAT No. !!'))
		if rec.phone:
			if len(str(rec.phone)) not in range(8,15) and rec.phone.isdigit() != True:
				raise osv.except_osv(_('Warning !!'),_('Enter your correct 8-15 digit numerics. Phone No. !!'))
		if rec.email != False:
			if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", rec.email) == None:
				raise osv.except_osv(_('Invalid Email !!'),_('Enter a valid email address !!'))
		if rec.website != False:
			#~ if re.match('www?.(?:www)?(?:[\w-]{2,255}(?:\.\w{2,6}){1,2})(?:/[\w&%?#-]{1,300})?',rec.website):
			if not re.match('www.(?:www)?(?:[\w-]{2,255}(?:\.\w{2,6}){1,2})(?:/[\w&%?#-]{1,300})?',rec.website):
				raise osv.except_osv(_('Invalid Email !!'),_('Enter a valid Website !!'))
		if rec.bank_ids:
			for item in rec.bank_ids:
				if item.bank_bic:
					if len(str(item.bank_bic)) != 11:
						raise osv.except_osv(_('Warning !!'),_('IFSC should contain 11 letters. !!'))
		if rec.bank_ids:
			for item in rec.bank_ids:
				if item.acc_number:
					if len(str(item.acc_number)) not in range(6,18) and item.acc_number.isdigit() != True:
						raise osv.except_osv(_('Warning !!'),_('Enter your correct 6-18 digit numerics. A/C No. !!'))
		if rec.mobile:
			if len(str(rec.mobile)) not in range(10,12) and rec.mobile.isdigit() != True:
				raise osv.except_osv(_('Warning !!'),_('Enter your correct 10-12 digit numerics. Mobile No. !!'))
		
		if rec.max_deal_discount > 100 and rec.dealer == True:
			raise osv.except_osv(_('Warning!'),_('Max dealer discount(%) should not be accept above 100!'))
		if rec.max_cust_discount > 100 and rec.customer == True:
			raise osv.except_osv(_('Warning!'),_('Max customer discount(%) should not be accept above 100!'))
		if rec.max_spl_discount > 100 and rec.customer == True:
			raise osv.except_osv(_('Warning!'),_('Max special discount(%) should not be accept above 100!'))
		
		if rec.delivery_ids:
			ser_dups = self.pool.get('kg.delivery.address').search(cr,uid,[('src_id','=',rec.id),('default','=','t')])
			if len(ser_dups) > 1:
				raise osv.except_osv(_('Warning!'),_('More than one default Delivery address is not allowed !! '))
				
		if rec.billing_ids:
			ser_dups = self.pool.get('kg.billing.address').search(cr,uid,[('bill_id','=',rec.id),('default','=','t')])
			if len(ser_dups) > 1:
				raise osv.except_osv(_('Warning!'),_('More than one default Billing address is not allowed !! '))
	
		return True
	
	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		data=''
		if rec.name:
			partner_name = rec.name
			name=partner_name.upper()
			if rec.customer == True:
				cr.execute(""" select upper(name) from res_partner where upper(name) = '%s' and customer = True """ %(name))
				data = cr.dictfetchall()
			elif rec.supplier == True:
				cr.execute(""" select upper(name) from res_partner where upper(name) = '%s' and supplier = True """ %(name))
				data = cr.dictfetchall()
			elif rec.dealer == True:
				cr.execute(""" select upper(name) from res_partner where upper(name) = '%s' and dealer = True """ %(name))
				data = cr.dictfetchall()
			elif rec.contractor == True:
				cr.execute(""" select upper(name) from res_partner where upper(name) = '%s' and contractor = True """ %(name))
				data = cr.dictfetchall()
			if len(data) > 1:
				res = False
			else:
				res = True
		return res
	
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_code = str(rec.name)		
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
		
		if rec.customer == True:
			url = 'http://10.100.9.32/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&customer='+rec_code

		if rec.dealer == True:
			url = 'http://10.100.9.32/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&dealer='+rec_code

		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
	
	_constraints = [
		
		(_validations,' ',[' ']),
		#~ (_name_validate, ' ', [' ']),
				
		]
	
kg_partner()


class kg_delivery_address(osv.osv):
	
	_name = "kg.delivery.address"
	_description = "Delivery Address"
	
	_columns = {
	
	'name': fields.char('Name'),
	'src_id': fields.many2one('res.partner', 'Partner Master'),
	'street': fields.char('Street', size=128,select=True),
	'street1': fields.char('Street 1', size=128,select=True),
	'landmark': fields.char('Landmark',size=128),
	'city_id': fields.many2one('res.city', 'City',select=True),
	'state_id': fields.many2one('res.country.state', 'State'),
	'country_id': fields.many2one('res.country', 'Country'),	
	'contact_no': fields.char('Contact No', size=12),
	'zip': fields.char('ZIP', size=8),
	'date': fields.date('Creation Date'),
	'default': fields.boolean('Default'),
	
	}
	
	_defaults = {
	
	'date' : lambda * a: time.strftime('%Y-%m-%d'),
	
	}
	
	def onchange_city(self, cr, uid, ids, city_id, context=None):
		if city_id:
			city_rec = self.pool.get('res.city').browse(cr, uid, city_id, context)		
			return {'value':{'state_id':city_rec.state_id.id,'country_id':city_rec.country_id.id}}
		else:
			pass
		return {}

kg_delivery_address()

class kg_billing_address(osv.osv):
	
	_name = "kg.billing.address"
	_description = "Billing Address"
	
	_columns = {
	
	'name': fields.char('Name'),
	'bill_id': fields.many2one('res.partner', 'Partner Master'),
	'street': fields.char('Street', size=128,select=True),
	'street1': fields.char('Street 1', size=128,select=True),
	'landmark': fields.char('Landmark',size=128),
	'city_id': fields.many2one('res.city', 'City',select=True),
	'state_id': fields.many2one('res.country.state', 'State'),
	'country_id': fields.many2one('res.country', 'Country'),	
	'contact_no': fields.char('Contact No', size=12),
	'zip': fields.char('ZIP', size=8),
	'date': fields.date('Creation Date'),
	'default': fields.boolean('Default'),
	
	}
	
	_defaults = {
	
	'date' : lambda * a: time.strftime('%Y-%m-%d'),
	
	} 
	
	def onchange_city(self, cr, uid, ids, city_id, context=None):
		if city_id:
			city_rec = self.pool.get('res.city').browse(cr, uid, city_id, context)		
			return {'value':{'state_id':city_rec.state_id.id,'country_id':city_rec.country_id.id}}
		else:
			pass
		return {}
		
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
	
kg_consultant_fee()

class ch_bank_details(osv.osv):
	
	_name = "res.partner.bank"
	_description = "Bank Details"
	_inherit = 'res.partner.bank'
	
	_columns = {
	
	'city_id': fields.many2one('res.city', 'City'),
	
	}
	
	def onchange_city(self, cr, uid, ids, city_id, context=None):
		if city_id:
			city_rec = self.pool.get('res.city').browse(cr, uid, city_id, context)		
			return {'value':{'state_id':city_rec.state_id.id,'country_id':city_rec.country_id.id}}
		else:
			pass
		return {}
	

ch_bank_details()
