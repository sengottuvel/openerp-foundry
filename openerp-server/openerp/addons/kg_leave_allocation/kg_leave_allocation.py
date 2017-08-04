from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
from dateutil import relativedelta
from dateutil import relativedelta as rdelta
today = datetime.now()
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_leave_allocation(osv.osv):

	_name = "kg.leave.allocation"
	_description = "Leave Allocation"
	
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
					as sam  """ %('kg_leave_allocation'))
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
		
		### Version 0.2
		
		
	
	_columns = {
	
		## Basic Info
			
		
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),

		## Entry Info
		
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
		
		'emp_code': fields.char('Code', size=10, required=True),		
		'employee_id':fields.many2one('hr.employee','Employee Name',required=True),
		'emp_categ_id':fields.many2one('kg.employee.category','Employee Category',required=True),
		'valid_from':fields.date('Valid From'),
		'valid_to':fields.date('Valid till'),
		'emp_categ_id':fields.many2one('kg.employee.category','Category'),
		'division_id':fields.many2one('kg.division.master','Division'),
	
		## Child Tables Declaration
		
		'line_id_1': fields.one2many('ch.leave.allocation', 'header_id_1','Leave Allocation'),
		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.master', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Name must be unique per Company !!'),
		('code', 'unique(code)', 'Code must be unique per Company !!'),
	]
	
	## Basic Needs	
	
	def entry_cancel(self,cr,uid,ids,context=None):
		
		rec = self.browse(cr,uid,ids[0])
		
		if rec.state == 'approved':
						
			if rec.cancel_remark:
				self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Cancel remark is must !!'),
					_('Enter the remarks in Cancel remarks field !!'))
		else:
			pass
			
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		
		rec = self.browse(cr,uid,ids[0])
		
		if rec.state == 'draft':
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		
		else:
			pass
			
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		
		rec = self.browse(cr,uid,ids[0])
		
		if rec.state == 'approved':			
			self.write(cr, uid, ids, {'state': 'draft'})
		else:
			pass
			
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		
		rec = self.browse(cr,uid,ids[0])
		
		if rec.state == 'confirmed':
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			
		else:
			pass
			
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
			pass
			
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
		return super(kg_leave_allocation, self).write(cr, uid, ids, vals, context)	
	
	
	## Module Requirement
	
	def _validate_valid_from(self, cr, uid, ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today_date = str(today.year)+'-'+str(today.month)+'-'+str(today.day)
		d1 =  datetime.strptime(rec.valid_from, "%Y-%m-%d")
		d2 =  datetime.strptime(today_date, "%Y-%m-%d")
		rd = rdelta.relativedelta(d2,d1)
		delta = d2 - d1
		no_of_days= delta.days
		print "no_of_daysno_of_daysno_of_daysno_of_days",no_of_days
		if no_of_days > 35:
			raise osv.except_osv(_('Warning!'),
						_('Only 35 days back can be selected !!'))
		if rec.valid_from > rec.valid_to:
			raise osv.except_osv(_('Warning!'),
						_('Valid From date should be greater than Valid Till date !!'))
		return True
	
	_constraints = [        
              
            (_validate_valid_from, 'System not allow to save with empty Concrete Details !!',['']),
       
        
       ]
	
	
	
	
kg_leave_allocation()

class ch_leave_allocation(osv.osv):
	
	_name='ch.leave.allocation'
	_description = "Leave Allocation Line"
	
	_columns = {
	
		'header_id_1': fields.many2one('kg.leave.allocation','Header_id_1'),
		'leave_type_id': fields.many2one('hr.holidays.status', 'Leave Type'),
		'no_of_days': fields.float('No Of Days'),	
		'used_days': fields.float('Used Days'),	
		'balc_days': fields.float('Balance Days'),
		}
	
		
	def onchange_no_of_days(self, cr, uid, ids, no_of_days,balc_days,context=None):
		value = {'balc_days': '',}
		value = {'balc_days': no_of_days}
		return {'value': value}	
		
ch_leave_allocation()
