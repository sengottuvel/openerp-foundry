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

class kg_partner(osv.osv):

	_name = "res.partner"
	_inherit = "res.partner"
	_description = "Partner Managment"
	
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
	'tin_no' : fields.char('TIN'),
	'vat_no' : fields.char('VAT'),
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
	#~ 'partner_state': fields.selection([('draft','Draft'),('confirm','WFA'),('approve','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status'),
	'group_flag': fields.boolean('Is Group Company'),
	'delivery_id': fields.many2one('kg.delivery.master','Delivery Type'),
	#'child_ids': fields.one2many('res.partner', 'parent_id', 'Contacts', domain=[('active','=',True)]),
	'creation_date': fields.datetime('Creation Date',readonly=True),
	'created_by': fields.many2one('res.users', 'Created by',readonly=True),
	'confirmed_date': fields.datetime('Confirmed Date',readonly=True),
	'confirmed_by': fields.many2one('res.users','Confirmed By',readonly=True),
	'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
	'reject_date': fields.datetime('Reject Date', readonly=True),
	'approved_date': fields.datetime('Approved Date',readonly=True),
	'approved_by': fields.many2one('res.users','Approved By',readonly=True),
	'cancel_date': fields.datetime('Cancelled Date', readonly=True),
	'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
	'updated_date': fields.datetime('Last Update Date',readonly=True),
	'updated_by': fields.many2one('res.users','Last Updated By',readonly=True),
	'con_designation': fields.char('Designation'),
	'con_whatsapp': fields.char('Whatsapp No'),
	#~ 'acc_number': fields.char('Whatsapp No'),
	#~ 'bank_name': fields.char('Whatsapp No'),
	#~ 'bank_bic': fields.char('Whatsapp No'),
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
	'adhar_id': fields.char('Adhar ID'),
	'contractor': fields.boolean('Contractor'),
	'tin_flag': fields.boolean('TIN Flag'),
	'mobile_2': fields.char('Mobile2'),
	
	}
	
	_defaults = {
	  
	  'is_company': True,
	  'creation_date': fields.datetime.now,
	  'created_by': lambda obj, cr, uid, context: uid,
	  'partner_state': 'draft',
	  'modify': 'no',
	  'tin_flag': False,
		 
	}

	def onchange_city(self, cr, uid, ids, city_id, context=None):
		if city_id:
			state_id = self.pool.get('res.city').browse(cr, uid, city_id, context).state_id.id
			return {'value':{'state_id':state_id}}
		return {}
	
	def onchange_zip(self,cr,uid,ids,zip,context=None):
		if len(str(zip)) in (6,7,8):
			value = {'zip':zip}
		else:
			raise osv.except_osv(_('Check zip number !!'),
				_('zip should contain 6-8 digit numerics. Else system not allow to save. !!'))
		if zip.isdigit() == False:
			raise osv.except_osv(_('Check zip number !!'),
				_('Please enter numeric values !!'))
		return {'value': value}
			
	#~ def onchange_tin_cst(self,cr,uid,ids,tin_no,cst_no,context=None):
		#~ if tin_no:
			#~ if len(str(tin_no)) == 11:
				#~ value = {'tin_no':tin_no}
			#~ else:
				#~ raise osv.except_osv(_('Check TIN number !!'),
					#~ _('Please enter 11 digit number !!'))
		#~ if cst_no:
			#~ if len(str(cst_no)) == 11:
				#~ value = {'cst_no':cst_no}
			#~ else:
				#~ raise osv.except_osv(_('Check CST number !!'),
					#~ _('Please enter 11 digit number !!'))
		#~ return {'value': value}
			
	def confirm_partner(self, cr, uid, ids, context=None): 
		rec = self.browse(cr, uid, ids[0])
		self.write(cr, uid, ids, {'partner_state': 'confirm','confirmed_by':uid,'confirmed_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		
		return True
		
	def reject_partner(self, cr, uid, ids, context=None): 
		rec = self.browse(cr, uid, ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'partner_state': 'reject','update_user_id':uid,'reject_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter rejection remark in remark field !!'))
		return True
		
	def approve_partner(self, cr, uid, ids, context=None): 
		rec = self.browse(cr, uid, ids[0])
		self.write(cr, uid, ids, {'partner_state': 'approve','approved_by':uid,'approved_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		
		return True

	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'partner_state': 'draft'})
		return True
		
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'partner_state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
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
	
	def _check_zip(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.zip:
			if len(str(rec.zip)) in (6,7,8) and rec.zip.isdigit() == True:
				return True
		else:
			return True
		return False
		
	def _check_tin(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.tin_no:
			if len(str(rec.tin_no)) == 11 and rec.tin_no.isdigit() == True:
				return True
		else:
			return True
		return False
		
	def _check_cst(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.cst_no:
			if len(str(rec.cst_no)) == 11 and rec.cst_no.isdigit() == True:
				return True
		else:
			return True
		return False
		
	def _check_vat(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.vat_no:
			if len(str(rec.vat_no)) == 15:
				return True
		else:
			return True
		return False
	
	def _check_phone(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.phone:
			if len(str(rec.phone)) in (8,9,10,11,12,13,14,15) and rec.phone.isdigit() == True:
				return True
		else:
			return True
		return False
	
	def _check_website(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.website != False:
			#~ if re.match('www?.(?:www)?(?:[\w-]{2,255}(?:\.\w{2,6}){1,2})(?:/[\w&%?#-]{1,300})?',rec.website):
			if re.match('www.(?:www)?(?:[\w-]{2,255}(?:\.\w{2,6}){1,2})(?:/[\w&%?#-]{1,300})?',rec.website):
				return True
			else:
				return False
		return True

	def _check_ifsc(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.bank_ids:
			for item in rec.bank_ids:
				if item.bank_bic:
					if len(str(item.bank_bic)) == 11:
						return True
				else:
					return True
		else:
			return True
		return False
			
	def _check_acc_no(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.bank_ids:
			for item in rec.bank_ids:
				if item.acc_number:
					if len(str(item.acc_number)) in (6,7,8,9,10,11,12,13,14,15,16,17,18) and item.acc_number.isdigit() == True:
						return True
				else:
					return True
		else:
			return True
		return False
		
	def _check_mobile_no(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.mobile:
			if len(str(rec.mobile)) in (10,11,12) and rec.mobile.isdigit() == True:
				return True
		else:
			return True
		return False
	
	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.name:
			partner_name = rec.name
			name=partner_name.upper()
			data=''
			if rec.customer == True:
				cr.execute(""" select upper(name) from res_partner where upper(name) = '%s' and customer = True """ %(name))
				data = cr.dictfetchall()
			elif rec.supplier == True:
				cr.execute(""" select upper(name) from res_partner where upper(name) = '%s' and supplier = True """ %(name))
				data = cr.dictfetchall()
			elif rec.dealer == True:
				cr.execute(""" select upper(name) from res_partner where upper(name) = '%s' and dealer = True """ %(name))
				data = cr.dictfetchall()
			if len(data) > 1:
				res = False
			else:
				res = True
		return res
				
	_constraints = [
	
		(_check_zip,'ZIP should contain 6-8 digit numerics. Else system not allow to save.',['ZIP']),
		(_check_tin,'TIN No. should contain 11 digit numerics. Else system not allow to save.',['TIN']),
		(_check_cst,'CST No. should contain 11 digit numerics. Else system not allow to save.',['CST']),
		(_check_vat,'VAT No. should contain 15 letters. Else system not allow to save.',['VAT']),
		(_check_website,'Check Website !',['Website']),
		(_check_phone,'Phone No. should contain 8-15 digit numerics. Else system not allow to save.',['Phone']),
		(_check_ifsc,'IFSC should contain 11 letters. Else system not allow to save.',['IFSC']),
		(_check_acc_no,'A/C No. should contain 6-18 digit numerics. Else system not allow to save.',['A/C No.']),
		(_check_mobile_no,'Mobile No. should contain 10-12 digit numerics. Else system not allow to save.',['Mobile']),
		(_name_validate, 'Name must be unique !!', ['Name']),		
		
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
	
	'name': fields.char('Name'),
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
		
kg_consultant_fee()
