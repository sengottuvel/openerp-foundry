# -*- coding: utf-8 -*-
##############################################################################
#	
#	OpenERP, Open Source Management Solution
#	Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU Affero General Public License as
#	published by the Free Software Foundation, either version 3 of the
#	License, or (at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU Affero General Public License for more details.
#
#	You should have received a copy of the GNU Affero General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.	 
#
##############################################################################

from openerp.osv import fields, osv
import time
from datetime import date

def location_name_search(self, cr, user, name='', args=None, operator='ilike',
						 context=None, limit=100):
	if not args:
		args = []

	ids = []
	if len(name) == 2:
		ids = self.search(cr, user, [('code', 'ilike', name)] + args,
						  limit=limit, context=context)

	search_domain = [('name', operator, name)]
	if ids: search_domain.append(('id', 'not in', ids))
	ids.extend(self.search(cr, user, search_domain + args,
						   limit=limit, context=context))

	locations = self.name_get(cr, user, ids, context)
	return sorted(locations, key=lambda (id, name): ids.index(id))

class Country(osv.osv):
	_name = 'res.country'
	_description = 'Country'
	_columns = {
		'name': fields.char('Country Name', size=64,
			help='The full name of the country.', required=True, translate=True),
		'code': fields.char('Country Code', size=2,
			help='The ISO country code in two chars.\n'
			'You can use this field for quick search.'),
		'address_format': fields.text('Address Format', help="""You can state here the usual format to use for the \
addresses belonging to this country.\n\nYou can use the python-style string patern with all the field of the address \
(for example, use '%(street)s' to display the field 'street') plus
			\n%(state_name)s: the name of the state
			\n%(state_code)s: the code of the state
			\n%(country_name)s: the name of the country
			\n%(country_code)s: the code of the country"""),
		'currency_id': fields.many2one('res.currency', 'Currency'),
	}
	_sql_constraints = [
		('name_uniq', 'unique (name)',
			'The name of the country must be unique !'),
		('code_uniq', 'unique (code)',
			'The code of the country must be unique !')
	]
	_defaults = {
		'address_format': "%(street)s\n%(street2)s\n%(city)s %(state_code)s %(zip)s\n%(country_name)s",
	}
	_order='name'

	name_search = location_name_search

	def create(self, cursor, user, vals, context=None):
		if vals.get('code'):
			vals['code'] = vals['code'].upper()
		return super(Country, self).create(cursor, user, vals,
				context=context)

	def write(self, cursor, user, ids, vals, context=None):
		if 'code' in vals:
			vals['code'] = vals['code'].upper()
		return super(Country, self).write(cursor, user, ids, vals,
				context=context)


class CountryState(osv.osv):
	_description="Country state"
	_name = 'res.country.state'
	_columns = {
		
		'country_id': fields.many2one('res.country', 'Country',
			required=True),
		'name': fields.char('State Name', size=64, required=True, 
							help='Administrative divisions of a country. E.g. Fed. State, Departement, Canton'),
		'code': fields.char('State Code', size=3,
			help='The state code in max. three chars.', required=True),
		 'creation_date':fields.datetime('Creation Date',readonly=True),
		'active': fields.boolean('Active'),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Approved By', readonly=True),
		'confirm_date': fields.datetime('Confirm Date', readonly=True),
		'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'reject_date': fields.datetime('Reject Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		   
	}
	_order = 'code'
	
	_defaults = {
	   
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active':True,
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'res.country.state', context=c),
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		
	}
	
	name_search = location_name_search
	
	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'confirmed','conf_user_id': uid, 'confirm_date': dt_time})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'approved','app_user_id': uid, 'approve_date': dt_time})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'state': 'reject','rej_user_id': uid, 'reject_date': dt_time})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter rejection remark in remark field !!'))
		return True
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': dt_time})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True
		
	def write(self, cr, uid, ids, vals, context=None):	  
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(CountryState, self).write(cr, uid, ids, vals, context)
	
	def unlink(self,cr,uid,ids,context=None):
		raise osv.except_osv(_('Warning!'),
				_('You can not delete Entry !!'))
				
class res_city(osv.osv):
	_name = 'res.city'
	_description = 'city'
	_columns = {
	
		'country_id': fields.many2one('res.country','Country',required=True),
		'state_id': fields.many2one('res.country.state','State',required=True),
		'name':fields.char('City',size=125, required=True),
		'creation_date':fields.datetime('Creation Date',readonly=True),
		'active': fields.boolean('Active'),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Approved By', readonly=True),
		'confirm_date': fields.datetime('Confirm Date', readonly=True),
		'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'reject_date': fields.datetime('Reject Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		
	}
	
	_sql_constraints = [
	
		('name_uniq', 'unique (name)',
			'The name of the city must be unique !'),
		
	]
	
	_defaults = {
	   
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active':True,
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'res.city', context=c),
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		
	}
	
	def create(self, cursor, user, vals, context=None):
		if vals.get('name'):
			vals['name'] = vals['name'].capitalize()
	   
		return super(res_city, self).create(cursor, user, vals,
				context=context)

	def write(self, cursor, user, ids, vals, context=None):
		if vals.get('name'):
			vals['name'] = vals['name'].capitalize()

		return super(res_city, self).write(cursor, user, ids, vals,
				context=context)
				
	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'confirmed','conf_user_id': uid, 'confirm_date': dt_time})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'approved','app_user_id': uid, 'approve_date': dt_time})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'state': 'reject','rej_user_id': uid, 'reject_date': dt_time})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter rejection remark in remark field !!'))
		return True
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': dt_time})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True
		
	def write(self, cr, uid, ids, vals, context=None):	  
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(res_city, self).write(cr, uid, ids, vals, context)
	
	def unlink(self,cr,uid,ids,context=None):
		raise osv.except_osv(_('Warning!'),
				_('You can not delete Entry !!'))
				
				
res_city()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

