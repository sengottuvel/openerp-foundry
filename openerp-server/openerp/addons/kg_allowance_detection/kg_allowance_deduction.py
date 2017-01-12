from lxml import etree
import openerp.addons.decimal_precision as dp
import openerp.exceptions
from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import datetime
import calendar
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_allowance_deduction(osv.osv):

	_name = "kg.allowance.detection"
	_description = "Allowance and Detection"
	
	
	
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
					WHERE constraint_type = 'FOREIGN KEY' and tc.table_name not in ('ch_kg_allowance_deduction')
					AND ccu.table_name='%s')
					as sam  """ %('kg_allowance_deduction'))
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
	
		### Basic Info
			
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10,store=True),		
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),


		### Entry Info ###
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'active': fields.boolean('Active'),
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
		
		## Module Requirement Info
		'start_date': fields.date('Month Start Date'),
		'end_date': fields.date('Month End Date'),
		'allow_type':fields.selection([('ALW','Allowance'),('DED','Deduction')], 'Type'),
		'pay_type':fields.many2one('hr.salary.rule', 'Earning/ Deduction'),
		#~ 'employee_id': fields.related('ch.kg.allowance.deduction','employee_id', type='many2one', relation='hr.employee', string='Employee' ,store=True),	
		
		## Child Tables Declaration		
		
		'line_id':fields.one2many('ch.kg.allowance.deduction','header_id','Line Id Ref'),	
				
	}
	
	
	
	
	
	### Basic Needs
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			if rec.cancel_remark:
				self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Cancel remark is must !!'),
					_('Enter the remarks in Cancel remarks field !!'))
		else:
			raise osv.except_osv(_('Warning!!!'),
					_('Confirm the record to proceed further'))
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state ==  'draft':
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Warning!!!'),
					_('The Record is not in draft !!!!!!'))
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			self.write(cr, uid, ids, {'state': 'draft'})
		else:
			raise osv.except_osv(_('Warning!!!'),
					_('Confirm the record to proceed further'))
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Warning!!!'),
					_('Confirm the record to proceed further'))
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			if rec.remark:
				self.write(cr, uid, ids, {'state': 'reject','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Rejection remark is must !!'),
					_('Enter the remarks in rejection remark field !!'))
		else:
			raise osv.except_osv(_('Warning!!!'),
					_('Confirm the record to proceed further'))
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state not in ('draft','cancel'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_allowance_deduction, self).write(cr, uid, ids, vals, context)
		
	
	_constraints = [
	
		#~ (_Validation, 'Special Character Not Allowed !!!', ['Check Name']),
		
		
	]
	
	## Module Requirement
	
	def _get_last_month_first(self, cr, uid, context=None):
		today = datetime.date.today()
		
		first = datetime.date(day=1, month=today.month, year=today.year)
		mon = today.month - 1
		if mon == 0:
			mon = 12
		else:
			mon = mon
		tot_days = calendar.monthrange(today.year,mon)[1]
		test = first - datetime.timedelta(days=tot_days)
		res = test.strftime('%Y-%m-%d')

		return res
		
	def _get_last_month_end(self, cr, uid, context=None):
		today = datetime.date.today()
		first = datetime.date(day=1, month=today.month, year=today.year)
		last = first - datetime.timedelta(days=1)
		res = last.strftime('%Y-%m-%d')
		return res
		
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.master', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		'start_date': _get_last_month_first,
		'end_date': _get_last_month_end,
		
	}	
	
kg_allowance_deduction()

class ch_kg_allowance_deduction(osv.osv):
	
	_name = "ch.kg.allowance.deduction"
	_description = "Monthly Allowance & Deduction Entry Line"	
	
	_columns = {

	'header_id': fields.many2one('kg.allowance.detection', 'Header ID', required=True, ondelete='cascade'),
	'employee_id': fields.many2one('hr.employee', 'Employee', required=True),	
	'code': fields.char('Code', size=128, readonly=True),
	'amount': fields.float('Amount', required=True),
	
	}
	
	def onchange_employee_code(self, cr, uid, ids, employee_id,code, context=None):
		value = {'code': ''}
		if employee_id:
			emp = self.pool.get('hr.employee').browse(cr, uid, employee_id, context=context)
			value = {'code': emp.code}
		return {'value': value}
		
	def _duplicate_entry(self, cr, uid, ids, context=None):
		obj = self.pool.get('ch.kg.allowance.deduction')
		record = self.browse(cr, uid, ids[0])
		emp_id = record.employee_id.id
		dup_ids = obj.search(cr, uid,[('employee_id','=',emp_id)])
		if len(dup_ids) > 1:
			return False
		return True
		
	def create(self, cr, uid, vals,context=None):
		if vals.has_key('employee_id') and vals['employee_id']:
			emp_rec = self.pool.get('hr.employee').browse(cr,uid,vals['employee_id'])
			if emp_rec:
				vals.update({'code':emp_rec.code})		
		order =  super(ch_kg_allowance_deduction, self).create(cr, uid, vals, context=context)
		return order
	
	_constraints = [
		
		#~ (_duplicate_entry, 'System not allowed to enter employee name more than one time!!',['Duplication']),
		
		]
	
ch_kg_allowance_deduction()	
