# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
import time
from datetime import datetime
import base64
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class Bank(osv.osv):
    _description='Bank'
    _name = 'res.bank'
    _order = 'name'
    
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
                    as sam  """ %('kg_holiday_master'))
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
            
    _columns = {
        'name': fields.char('Name', size=128, required=True),
        'street': fields.char('Street', size=128),
        'street2': fields.char('Street2', size=128),
        'zip': fields.char('Zip', change_default=True, size=8),
        'city': fields.char('City', size=128),
        'state': fields.many2one("res.country.state", 'Fed. State',
            domain="[('country_id', '=', country)]"),
        'country': fields.many2one('res.country', 'Country'),
        'email': fields.char('Email', size=64),
        'phone': fields.char('Phone', size=15),
        'fax': fields.char('Fax', size=10),
        'active': fields.boolean('Active'),
        'bic': fields.char('Bank Identifier Code', size=64,
            help="Sometimes called BIC or Swift."),
            
         
        ## Basic Info
            
        'status': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
        'notes': fields.text('Notes'),
        'remark': fields.text('Approve/Reject'),
        'cancel_remark': fields.text('Cancel'),
        'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),     
        'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),

        ## Entry Info
        
        'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
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
    }
    _defaults = {
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.master', context=c),
        'active': lambda *a: 1,
        'status': 'draft',
        'user_id': lambda obj, cr, uid, context: uid,
        'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'modify': 'no',
        'entry_mode': 'manual',
    }
    def name_get(self, cr, uid, ids, context=None):
        result = []
        for bank in self.browse(cr, uid, ids, context):
            result.append((bank.id, (bank.bic and (bank.bic + ' - ') or '') + bank.name))
        return result
    
    ## Basic Needs  
    
    def entry_cancel(self,cr,uid,ids,context=None):
        
        rec = self.browse(cr,uid,ids[0])
        
        if rec.status == 'approved':
                        
            if rec.cancel_remark:
                self.write(cr, uid, ids, {'status': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
            else:
                raise osv.except_osv(_('Cancel remark is must !!'),
                    _('Enter the remarks in Cancel remarks field !!'))
        else:
            pass
            
        return True

    def entry_confirm(self,cr,uid,ids,context=None):
        
        rec = self.browse(cr,uid,ids[0])
        
        if rec.status == 'draft':
            self.write(cr, uid, ids, {'status': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        
        else:
            pass
            
        return True
        
    def entry_draft(self,cr,uid,ids,context=None):
        
        rec = self.browse(cr,uid,ids[0])
        
        if rec.status == 'approved':         
            self.write(cr, uid, ids, {'status': 'draft'})
        else:
            pass
            
        return True

    def entry_approve(self,cr,uid,ids,context=None):
        
        rec = self.browse(cr,uid,ids[0])
        
        if rec.status == 'confirmed':
            self.write(cr, uid, ids, {'status': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
            
        else:
            pass
            
        return True

    def entry_reject(self,cr,uid,ids,context=None):
        
        rec = self.browse(cr,uid,ids[0])
        
        if rec.status == 'confirmed':
            
            if rec.remark:
                self.write(cr, uid, ids, {'status': 'reject','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
            else:
                raise osv.except_osv(_('Rejection remark is must !!'),
                    _('Enter the remarks in rejection remark field !!'))
                    
        else:
            pass
            
        return True
        
    def unlink(self,cr,uid,ids,context=None):
        unlink_ids = []     
        for rec in self.browse(cr,uid,ids): 
            if rec.status not in ('draft','cancel'):             
                raise osv.except_osv(_('Warning!'),
                        _('You can not delete this entry !!'))
            else:
                unlink_ids.append(rec.id)
        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
        
        
    def write(self, cr, uid, ids, vals, context=None):
        vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
        return super(Bank, self).write(cr, uid, ids, vals, context)    
	
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_code = str(rec.name)		
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
			
		url = 'http://192.168.1.7/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&Bank_Master='+rec_code


		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
        
    _sql_constraints = [
		('name_uniq', 'unique(name)', 'Bank name must be unique !'),
	]     
    

Bank()


class res_partner_bank_type(osv.osv):
    _description='Bank Account Type'
    _name = 'res.partner.bank.type'
    _order = 'name'
    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'code': fields.char('Code', size=64, required=True),
        'field_ids': fields.one2many('res.partner.bank.type.field', 'bank_type_id', 'Type Fields'),
        'format_layout': fields.text('Format Layout', translate=True)
    }
    _defaults = {
        'format_layout': lambda *args: "%(bank_name)s: %(acc_number)s"
    }
res_partner_bank_type()

class res_partner_bank_type_fields(osv.osv):
    _description='Bank type fields'
    _name = 'res.partner.bank.type.field'
    _order = 'name'
    _columns = {
        'name': fields.char('Field Name', size=64, required=True, translate=True),
        'bank_type_id': fields.many2one('res.partner.bank.type', 'Bank Type', required=True, ondelete='cascade'),
        'required': fields.boolean('Required'),
        'readonly': fields.boolean('Readonly'),
        'size': fields.integer('Max. Size'),
    }
res_partner_bank_type_fields()


class res_partner_bank(osv.osv):
    '''Bank Accounts'''
    _name = "res.partner.bank"
    _rec_name = "acc_number"
    _description = __doc__
    _order = 'sequence'

    def _bank_type_get(self, cr, uid, context=None):
        bank_type_obj = self.pool.get('res.partner.bank.type')

        result = []
        type_ids = bank_type_obj.search(cr, uid, [])
        bank_types = bank_type_obj.browse(cr, uid, type_ids, context=context)
        for bank_type in bank_types:
            result.append((bank_type.code, bank_type.name))
        return result

    def _default_value(self, cursor, user, field, context=None):
        if context is None: context = {}
        if field in ('country_id', 'state_id'):
            value = False
        else:
            value = ''
        if not context.get('address'):
            return value

        for address in self.pool.get('res.partner').resolve_2many_commands(
            cursor, user, 'address', context['address'], ['type', field], context=context):

            if address.get('type') == 'default':
                return address.get(field, value)
            elif not address.get('type'):
                value = address.get(field, value)
        return value

    _columns = {
        'name': fields.char('Bank Account', size=64), # to be removed in v6.2 ?
        'acc_number': fields.char('Account Number', size=64, required=True),
        'bank': fields.many2one('res.bank', 'Bank'),
        'bank_bic': fields.char('IFSC Code', size=16),
        'bank_name': fields.char('Bank Name', size=32),
        'owner_name': fields.char('Account Owner Name', size=128),
        'street': fields.char('Street', size=128),
        'zip': fields.char('Zip', change_default=True, size=24),
        'city': fields.char('City', size=128),
        'country_id': fields.many2one('res.country', 'Country',
            change_default=True),
        'state_id': fields.many2one("res.country.state", 'Fed. State',
            change_default=True, domain="[('country_id','=',country_id)]"),
        'company_id': fields.many2one('res.company', 'Company',
            ondelete='cascade', help="Only if this bank account belong to your company"),
        'partner_id': fields.many2one('res.partner', 'Account Owner', required=False,
            ondelete='cascade', select=True),
        'state': fields.selection(_bank_type_get, 'Bank Account Type', required=False,
            change_default=True),
        'sequence': fields.integer('Sequence'),
        'footer': fields.boolean("Display on Reports", help="Display this bank account on the footer of printed documents like invoices and sales orders.")
    }

    _defaults = {
        'owner_name': lambda obj, cursor, user, context: obj._default_value(
            cursor, user, 'name', context=context),
        'street': lambda obj, cursor, user, context: obj._default_value(
            cursor, user, 'street', context=context),
        'city': lambda obj, cursor, user, context: obj._default_value(
            cursor, user, 'city', context=context),
        'zip': lambda obj, cursor, user, context: obj._default_value(
            cursor, user, 'zip', context=context),
        'country_id': lambda obj, cursor, user, context: obj._default_value(
            cursor, user, 'country_id', context=context),
        'state_id': lambda obj, cursor, user, context: obj._default_value(
            cursor, user, 'state_id', context=context),
        'name': '/'
    }

    def fields_get(self, cr, uid, allfields=None, context=None):
        res = super(res_partner_bank, self).fields_get(cr, uid, allfields=allfields, context=context)
        bank_type_obj = self.pool.get('res.partner.bank.type')
        type_ids = bank_type_obj.search(cr, uid, [])
        types = bank_type_obj.browse(cr, uid, type_ids)
        for type in types:
            for field in type.field_ids:
                if field.name in res:
                    res[field.name].setdefault('states', {})
                    res[field.name]['states'][type.code] = [
                            ('readonly', field.readonly),
                            ('required', field.required)]
        return res

    def _prepare_name_get(self, cr, uid, bank_dicts, context=None):
        """ Format the name of a res.partner.bank.
            This function is designed to be inherited to add replacement fields.
            :param bank_dicts: a list of res.partner.bank dicts, as returned by the method read()
            :return: [(id, name), ...], as returned by the method name_get()
        """
        # prepare a mapping {code: format_layout} for all bank types
        bank_type_obj = self.pool.get('res.partner.bank.type')
        bank_types = bank_type_obj.browse(cr, uid, bank_type_obj.search(cr, uid, []), context=context)
        bank_code_format = dict((bt.code, bt.format_layout) for bt in bank_types)

        res = []
        for data in bank_dicts:
            name = data['acc_number']
            if data['state'] and bank_code_format.get(data['state']):
                try:
                    if not data.get('bank_name'):
                        data['bank_name'] = _('BANK')
                    name = bank_code_format[data['state']] % data
                except Exception:
                    raise osv.except_osv(_("Formating Error"), _("Invalid Bank Account Type Name format."))
            res.append((data.get('id', False), name))
        return res

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        bank_dicts = self.read(cr, uid, ids, context=context)
        return self._prepare_name_get(cr, uid, bank_dicts, context=context)

    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        result = {}
        if company_id:
            c = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
            if c.partner_id:
                r = self.onchange_partner_id(cr, uid, ids, c.partner_id.id, context=context)
                r['value']['partner_id'] = c.partner_id.id
                r['value']['footer'] = 1
                result = r
        return result

    def onchange_bank_id(self, cr, uid, ids, bank_id, context=None):
        result = {}
        if bank_id:
            bank = self.pool.get('res.bank').browse(cr, uid, bank_id, context=context)
            result['bank_name'] = bank.name
            result['bank_bic'] = bank.bic
        return {'value': result}


    def onchange_partner_id(self, cr, uid, id, partner_id, context=None):
        result = {}
        if partner_id:
            part = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            result['owner_name'] = part.name
            result['street'] = part.street or False
            result['city'] = part.city or False
            result['zip'] =  part.zip or False
            result['country_id'] =  part.country_id.id
            result['state_id'] = part.state_id.id
        return {'value': result}

res_partner_bank()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
