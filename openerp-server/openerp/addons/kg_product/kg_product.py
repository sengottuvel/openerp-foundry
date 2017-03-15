# -*- coding: utf-8 -*-
##############################################################################
#
#   OpenERP, Open Source Management Solution
#   Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).

#
##############################################################################
import math
import re
from _common import rounding
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

UOM_CONVERSATION = [
    ('one_dimension','One Dimension'),('two_dimension','Two Dimension')
]

class kg_product(osv.osv):
	
	_name = "product.product"
	_inherit = "product.product"
	
	_columns = {
		
		#'minor_name': fields.many2one('kg.minormaster', 'Minor Name'),
		
		'capital': fields.boolean('Capital Goods'),
		'abc': fields.boolean('ABC Analysis'),
		'po_uom_coeff': fields.float('PO Coeff', digits=(16,10), required=True, help="One Purchase Unit of Measure = Value of(PO Coeff)UOM"),
		'product_type': fields.selection([('raw','Foundry Raw Materials'),('ms','MS Item'),('bot','BOT'),('consu', 'Consumables'),
											('capital','Capitals and Asset'),('service','Service Items'),('coupling','Coupling'),
											('mechanical_seal','Mechanical Seal')], 'Product Type',required=True),
		'remark': fields.text('Approve/Reject Remarks',readonly=False,states={'approved':[('readonly',True)]}),
		'cancel_remark': fields.text('Cancel Remarks'),
		#'moc_id': fields.many2one('kg.moc.master','MOC'),
		'od': fields.float('OD'),
		'breadth': fields.float('Breadth'),
		'length': fields.float('Length'),
		'thickness': fields.float('Thickness'),
		'weight': fields.float('Weight'),
		'po_uom_in_kgs': fields.float('PO UOM in kgs',digits=(16,10)),
		'uom_conversation_factor': fields.selection(UOM_CONVERSATION,'UOM Conversation Factor',required=True),
		'coupling_type': fields.selection([('rss','RRS'),('sw','SW'),('rrl','RRL'),('swq','SWQ'),('rst','RST'),('l','L'),('lm','LM'),('lmk','LMK'),('lbc','LBC'),('f','F'),('f_0','F-0'),('sm','SM'),('bc','BC'),('ph_spacer','PH SPACER'),('ph_non_spacer','PH NON SPACER'),('metaflex_series_80','METAFLEX SERIES 80'),('e','E'),('em','EM'),('sam','SAM'),('a','A')],'Coupling Type'),
		'service_factor': fields.float('Service Factor'),
		'power_kw': fields.float('Power in KW'),
		'speed_in_rpm': fields.float('Speed In RPM'),
		'max_bore': fields.float('MAX Bore'),
		'coupling_size': fields.float('Coupling Size'),
		'spacer_length': fields.float('Spacer Length'),
		'liquid_id': fields.many2one('kg.fluid.master','Liquid'),
		'mechanical_type': fields.char('Type'),
		'operating_condition': fields.char('Operating Condition'),
		'face_combination': fields.char('Face Combination'),
		'api_plan': fields.char('API Plan'),
		'gland_placement': fields.char('Gland Placement'),
		'gland_plate': fields.selection([('w_gland_plate','With Gland Plate'),('wo_gland_plate','Without Gland Plate')],'Gland Plate'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'sleeve_dia': fields.char('Sleeve dia(MM)'),
		'coupling_make': fields.many2one('kg.brand.master','Coupling Make'),
		
		#~ 'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		# Entry Info
		
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Approved By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'reject_date': fields.datetime('Rejected Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		
	}
	
	_defaults = {
	
		#~ 'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'product.product', context=c),
		'po_uom_coeff': 0.00,
		'user_id': lambda obj, cr, uid, context: uid,
		
	}
	
	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			self.write(cr, uid, ids, {'state': 'confirm','conf_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
	   
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.state == 'confirm':
			access_obj = self.pool.get('kg.accessories.master')
			ch_access_obj = self.pool.get('ch.kg.accessories.master')
			
			if rec.is_accessories == True:
				
				ac_id = access_obj.search(cr,uid,[('product_id','=',rec.id)])
				
				if ac_id:
					old_obj = access_obj.search(cr,uid,[('product_id','=',rec.id),('state','!=','reject')])
					if old_obj:
						old_rec = access_obj.browse(cr,uid,old_obj[0])
						access_obj.write(cr,uid,old_rec.id,{'name':rec.name})
					
					old_rej_obj = access_obj.search(cr,uid,[('product_id','=',rec.id),('state','=','reject')])
					if old_rej_obj:
						old_rej_rec = access_obj.browse(cr,uid,old_rej_obj[0])
						access_id = access_obj.create(cr,uid,{'access_type':'new',
															  'name': rec.name,
															  'entry_mode': 'auto',
															  'product_id': rec.id,
															 })
						print"access_idaccess_idaccess_id",access_id
						if access_id:
							ch_access_obj.create(cr,uid,{'header_id': access_id,
														 'product_id': rec.id,
														 'qty': 1,
														 'uom_id': rec.uom_po_id.id,
														 'uom_conversation_factor':rec.uom_conversation_factor,
														 'entry_mode': 'auto',
														})			
				else:
					access_id = access_obj.create(cr,uid,{'access_type':'new',
														  'name': rec.name,
														  'entry_mode': 'auto',
														  'product_id': rec.id,
														 })
					print"access_idaccess_idaccess_id",access_id
					if access_id:
						ch_access_obj.create(cr,uid,{'header_id': access_id,
													 'product_id': rec.id,
													 'qty': 1,
													 'uom_id': rec.uom_po_id.id,
													 'uom_conversation_factor':rec.uom_conversation_factor,
													 'entry_mode': 'auto',
													})			  
			self.write(cr, uid, ids, {'state': 'approved','app_user_id': uid, 'approve_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		   
		return True
		
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			if rec.cancel_remark:
				self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Cancel remark is must !!'),
					_('Enter the remarks in Cancel remarks field !!'))
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			self.write(cr, uid, ids, {'state': 'draft'})
		return True
		
	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirm':
			if rec.remark:
				self.write(cr, uid, ids, {'state': 'reject','rej_user_id': uid, 'reject_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Rejection remark is must !!'),
					_('Enter rejection remark in remark field !!'))
		return True
	
	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
					   
		return res 
	
	def _spl_name(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.name:
			name_special_char = ''.join(c for c in rec.name if c in '!@#$%^~*{}?+/=')
			if name_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Name!'))
			
			return True
		else:
			return True
		return False
	
	def _po_coeff(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.uom_id != rec.uom_po_id and rec.po_uom_coeff == 0 and rec.state != 'approved':
			raise osv.except_osv(_('Warning!'),
				_('Please check and update PO Coeff for %s in product master !'%(rec.name)))
		if rec.tolerance_applicable == True and rec.tolerance_plus <= 0 and rec.state != 'approved':
			raise osv.except_osv(_('Warning!'),
				_('Please check and update tolerance for %s in product master !'%(rec.name)))
		return True
	
	#~ def write(self, cr, uid, ids, vals, context=None):
		#~ vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		#~ return super(kg_product, self).write(cr, uid, ids, vals, context)	 
	
	_constraints = [
		
		(_name_validate, 'product name must be unique !!', ['name']),
		#~ (_spl_name, 'Special Character Not Allowed!', ['']),
		#~ (_po_coeff, 'System should not be accept zero value!', ['']),
	   
		#(fields_validation, 'Please Enter the valid Format',['Invalid Format']),
	]	   
	""" 
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []	 
		for rec in self.browse(cr,uid,ids): 
			if rec.state != 'draft' and rec.state != 'reject':		  
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	""" 
	
	def write(self,cr,uid,ids,vals,context={}):
		#if 'default_code' in vals:
		#	 raise osv.except_osv(_('Warning !'),_('You can not modify Product code'))
			 
		#if 'name' in vals:
		#	 raise osv.except_osv(_('Warning !'),_('You can not modify Product Name'))	
		
		if 'tolerance_applicable' in vals:
			if vals['tolerance_applicable'] == True:
				if 'tolerance_plus' in vals:
					if vals['tolerance_plus'] <= 0.00:
						raise osv.except_osv(_('Check Tolerance(+) Value !!'),
							_('Please enter greater than zero !!'))	
					else:
						pass
				else:
					pass
				#if 'tolerance_minus' in vals:
				#	if vals['tolerance_minus'] <= 0.00:
				#		raise osv.except_osv(_('Check Tolerance(-) Value !!'),
				#			_('Please enter greater than zero !!'))	
				#	else:
				#		pass
				#else:
				#	pass
			else:
				pass
		return super(kg_product, self).write(cr, uid, ids,vals, context)
	
kg_product()

class kg_product_category(osv.osv):
	
	_name = "product.category"
	_inherit = "product.category"
	
	_columns = {
		
		'account_id': fields.many2one('account.account','Ledger Name'),
		
	}
	
	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.state == 'confirm':
			
			## Account master creation process start
			ac_obj = self.pool.get('account.account')
			old_acc_ids = ac_obj.search(cr,uid,[('master_id','=',rec.id)])
			if old_acc_ids:
				old_acc_rec = ac_obj.browse(cr,uid,old_acc_ids[0])
				ac_obj.write(cr,uid,old_acc_rec.id,{'name': rec.name})
			acc_ids = ac_obj.search(cr,uid,[('name','=',rec.name)])
			if not acc_ids:
				account_id = ac_obj.account_creation(cr,uid,rec.name,rec.id,'auto','other','New Product Category Added',context=context)
				self.write(cr, uid, ids, {'account_id':account_id})
			## Account master creation process end
			
			self.write(cr, uid, ids, {'state': 'approved','app_user_id': uid, 'approve_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
kg_product_category()
