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

class kg_depmaster(osv.osv):

	_name = "kg.depmaster"
	_description = "Department Master"
	_rec_name = 'dep_name' 
	
	#~ def _get_modify(self, cr, uid, ids, field_name, arg, context=None):
		#~ res={}
		#~ ser_obj = self.pool.get('kg.service.order')
		#~ dep_is_obj = self.pool.get('kg.department.issue')
		#~ for h in self.browse(cr, uid, ids, context=None):
			#~ res[h.id] = 'no'
			#~ ser_ids = ser_obj.search(cr,uid,[('dep_name','=',h.id)])
			#~ dep_is_ids = dep_is_obj.search(cr,uid,[('department_id','=',h.id)])
			#~ if ser_ids or dep_is_ids:
				#~ res[h.id] = 'yes'
		#~ print"eeeeeeeeeeeeeeee",res
		#~ return res
	
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
				as sam  """ %('kg_depmaster'))
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
		
		## Basic Info
		
		'name': fields.char('Dep.Code', size=4, required=True,readonly=False,states={'approved':[('readonly',True)]}),
		'dep_name': fields.char('Dep.Name', size=64, required=True, translate=True,readonly=False,states={'approved':[('readonly',True)]}),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes',readonly=False,states={'approved':[('readonly',True)]}),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=3),
		
		## Module Requirement Info
		
		'consumerga': fields.many2one('account.account', 'Consumer GL/AC', size=64, translate=True, select=2),
		'cost': fields.many2one('account.account','Cost Centre', size=64, translate=True, select=2),
		'stock_location': fields.many2one('stock.location', 'Dep.Stock Location', size=64, translate=True, 
					select=True, domain=[('usage','<>','view')],readonly=False,states={'approved':[('readonly',True)]}),
		'main_location': fields.many2one('stock.location', 'Main Stock Location', size=64, translate=True, 
					select=True, domain=[('usage','<>','view')],readonly=False,states={'approved':[('readonly',True)]}),
		'used_location': fields.many2one('stock.location', 'Used Stock Location', size=64, translate=True, 
					select=True, domain=[('usage','<>','view')],readonly=False,states={'approved':[('readonly',True)]}),
		'product_id': fields.many2many('product.product', 'product_deparment', 'depmaster_id', 'product_depid', 'Product'),
		'issue_period': fields.selection([('weekly','Weekly'), ('15th','15th Once'), ('monthly', 'Monthly')], 'Stock Issue Period'),
		'issue_date': fields.float('Stock Issue Days'),
		'sub_indent': fields.boolean("Sub.Store.Ind"),		
		'is_parent': fields.boolean('Is Parent',readonly=False,states={'approved':[('readonly',True)]}),
		'parent_dept': fields.many2one('kg.depmaster','Parent Department',domain="[('is_parent','=',True)]",readonly=False,states={'approved':[('readonly',True)]}),
		'item_request': fields.boolean('Item Request Applicable',readonly=False,states={'approved':[('readonly',True)]}),
		
		# Entry Info
		
		'active': fields.boolean("Active"),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'creation_date':fields.datetime('Created Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Approved By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'reject_date': fields.datetime('Rejected Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		
	}


	_defaults = {
	
		'creation_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.depmaster', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'modify': 'no',
		'item_request': True,
		
	}
	
	_sql_constraints = [
		('name_uniq', 'unique(dep_name)', 'Department name must be unique !'),
		('code_uniq', 'unique(name)', 'Department Code must be unique !'),
	]
	
	def create(self, cr, uid, vals, context=None):
		v_name = None 
		#~ if vals.get('dep_name'): 
			#~ v_name = vals['dep_name'].strip() 
			#~ vals['dep_name'] = v_name.capitalize() 
		if len(vals.get('name')) <= 4:
			pass
		else:
			raise osv.except_osv(_('Warning!'),
				_('Please Specify 4 Digit !!'))
		order =  super(kg_depmaster, self).create(cr, uid, vals, context=context) 
		return order
		
	def write(self, cr, uid, ids, vals, context=None):
		v_name = None 
		#~ if vals.get('dep_name'): 
			#~ v_name = vals['dep_name'].strip() 
			#~ vals['dep_name'] = v_name.capitalize()
		if len(vals.get('name')) <= 4:
			pass
		else:
			raise osv.except_osv(_('Warning!'),
				_('Please Specify 4 Digit !!'))
		order =  super(kg_depmaster, self).write(cr, uid, ids, vals, context=context) 
		return order
	
	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			self.write(cr, uid, ids, {'state': 'confirmed','conf_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			if rec.item_request == True:
				dup_obj = self.pool.get('stock.location').search(cr,uid,[('name','=',rec.dep_name)])
				if dup_obj:
					pass
				else:
					stock_location_id = self.pool.get('stock.location').create(cr,uid,{'name':rec.dep_name,'usage':'internal','location_type':'sub','custom':True,'entry_mode':'auto','state':'approved'})
					self.write(cr,uid,ids,{'stock_location':stock_location_id})
					stock_obj = self.pool.get('stock.location').search(cr,uid,[('location_type','=','main')])
					if stock_obj:
						stock_rec = self.pool.get('stock.location').browse(cr,uid,stock_obj[0])
						self.write(cr,uid,ids,{'main_location':stock_rec.id})
					con_stock_obj = self.pool.get('stock.location').search(cr,uid,[('usage','=','consumption')])
					if con_stock_obj:
						con_stock_rec = self.pool.get('stock.location').browse(cr,uid,con_stock_obj[0])
						self.write(cr,uid,ids,{'used_location':con_stock_rec.id})
			self.write(cr, uid, ids, {'state': 'approved','app_user_id': uid, 'approve_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
	def entry_draft(self,cr,uid,ids,context=None):
		if rec.state == 'approved':
			self.write(cr, uid, ids, {'state': 'draft'})
		return True
		
	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			if rec.remark:
				self.write(cr, uid, ids, {'state': 'reject','rej_user_id': uid, 'reject_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Rejection remark is must !!'),
					_('Enter rejection remark in remark field !!'))
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
			
	def write(self, cr, uid, ids, vals, context=None):	  
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_depmaster, self).write(cr, uid, ids, vals, context)
	
	def _Validation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		name_special_char = ''.join( c for c in flds.dep_name if  c in '!@#$%^~*{}?+/=' )		
		if name_special_char:
			return False		
		return True	
		
	def _CodeValidation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])	
		if flds.name:		
			code_special_char = ''.join( c for c in flds.name if  c in '!@#$%^~*{}?+/=' )		
			if code_special_char:
				return False
		return True		
		
	def _name_dup_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.name:
			division_name = rec.dep_name
			name=division_name.upper()			
			cr.execute(""" select upper(dep_name) from kg_depmaster where upper(dep_name)  = '%s' """ %(name))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
			
	def _code_dup_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.name:
			division_code = rec.name
			code=division_code.upper()			
			cr.execute(""" select upper(name) from kg_depmaster where upper(name)  = '%s' """ %(code))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res	
						
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	_constraints = [
	
		(_Validation, 'Special Character Not Allowed!', ['Check Name']),
		(_CodeValidation, 'Special Character Not Allowed!', ['Check Code']),
		(_name_dup_validate, 'Division name must be unique!', ['name']),		
		(_code_dup_validate, 'Division code must be unique!', ['code']),		
		
	]

kg_depmaster()

class custom_sequence_generate_det(osv.osv):
	
	_name = 'custom.sequence.generate.det'
	_order = 'name'
	_columns = {
		'name': fields.char('Name',size=64),
		'ir_sequence_id': fields.many2one('ir.sequence', 'Sequence'),
		'seq_month' : fields.integer('Sequence Month'),
		'seq_year' : fields.integer('Sequence Year'),
		'seq_next_number' : fields.integer('Sequence Next Number'),
		'fiscal_year_code' : fields.char('Fiscal Year Code',size=64),
		'fiscal_year_id' : fields.integer('Fiscal Year ID'),
	}
	
custom_sequence_generate_det()
