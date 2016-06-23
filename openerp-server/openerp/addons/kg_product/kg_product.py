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
a = datetime.now()
dt_time = a.strftime('%m/%d/%Y %H:%M:%S')
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp


class kg_product(osv.osv):
	
	_name = "product.product"
	_inherit = "product.product"
	_columns = {
	
		#'minor_name': fields.many2one('kg.minormaster', 'Minor Name'),

		'capital': fields.boolean('Capital Goods'),
		'abc': fields.boolean('ABC Analysis'),
		'po_uom_coeff': fields.float('PO Coeff', digits=(16,4),  required=True, help="One Purchase Unit of Measure = Value of(PO Coeff)UOM"),
		'product_type': fields.selection([('raw','Foundry Raw Materials'),('ms','MS Item'),('bot','BOT'),('consu', 'Consumables'),('capital','Capitals and Asset'),('service','Service Items')], 'Product Type', 
				required=True),
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Apprved By', readonly=True),
		'confirm_date': fields.datetime('Confirm Date', readonly=True),
		'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'reject_date': fields.datetime('Reject Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'remark': fields.text('Remarks',readonly=False,states={'approved':[('readonly',True)]}),
		'cancel_remark': fields.text('Cancel Remarks'),
		#'moc_id': fields.many2one('kg.moc.master','MOC'),
		'od': fields.float('OD'),
		'breadth': fields.float('Breadth'),
		'length': fields.float('Length'),
		'thickness': fields.float('Thickness'),
		'weight': fields.float('Weight'),
		'po_uom_in_kgs': fields.float('PO UOM in kgs'),
		
	}
	
	_defaults = {
	
		'po_uom_coeff' : 1.00,
		'crt_date':fields.datetime.now,	
		'user_id': lambda obj, cr, uid, context: uid,
		
	}
	
	def email_ids(self,cr,uid,ids,context = None):
		email_from = []
		email_to = []
		email_cc = []
		val = {'email_from':'','email_to':'','email_cc':''}
		ir_model = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		mail_form_ids = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		for ids in mail_form_ids:
			mail_form_rec = self.pool.get('kg.mail.settings').browse(cr,uid,ids)
			if mail_form_rec.doc_name.model == 'product.product':
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
	
	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'confirm','conf_user_id': uid, 'confirm_date': dt_time})
	   
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		obj = self.browse(cr, uid, ids[0])		
		self.write(cr, uid, ids, {'state': 'approved','app_user_id': uid, 'approve_date': dt_time})
	   
		return True
		
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': dt_time})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True
		
	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'state': 'reject','rej_user_id': uid, 'reject_date': dt_time})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter rejection remark in remark field !!'))
		return True
		
	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
					   
		return res 
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_product, self).write(cr, uid, ids, vals, context)	 
	
	_constraints = [
		
		(_name_validate, 'product name must be unique !!', ['name']),
	   
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


	

