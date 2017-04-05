from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import datetime
import re
import math
from datetime import date, datetime, timedelta
import calendar
from dateutil import relativedelta as rdelta
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')
today = date.today()

class kg_weekly_attendance(osv.osv):

	_name = "kg.weekly.attendance"
	_description = "Weekly Attendance"
	
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
					as sam  """ %('kg_weekly_attendance'))
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
		
	def _paid_amt(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		for rec in self.browse(cr, uid, ids, context=context):
			res[rec.id] = {
				'tot_wage_days': 0.0,
			}
			var = rec.ot_days+rec.present_days
			res[rec.id]['tot_wage_days'] = var
		return res
		
		
	
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
		
		'start_date':fields.date('Start Date'),
		'end_date':fields.date('End Date'),
		'labour_id':fields.many2one('kg.labour.master','Labour'),
		'labour_code':fields.char('Code'),
		'labour_categ':fields.selection([('individual','Individual'),('contract','Contract')],'Category'),
		'present_days':fields.float('Present Days'),
		'ot_days':fields.float('OT Days'),
		'tot_wage_days':fields.float('Total Wage Days'),
		'tot_wage_days': fields.function(_paid_amt, string='Total Wage Days',multi="sums",store=True),
		'total_days':fields.float('Total Days'),
	
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.weekly.attendance', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		
	}
	
	####Validations####
	
	def  _validations (self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.end_date <= rec.start_date:
			raise osv.except_osv(_('Warning !!'),
				_('End Date should not be less than or equal to Start Date !!'))
		if rec.present_days <= 0.00:
			raise osv.except_osv(_('Warning !!'),
				_('Present Days should not be less than or equal to zero !!'))
		if rec.present_days > rec.total_days:
			raise osv.except_osv(_('Warning !!'),
				_('Present Days should not exceed Total Days !!'))
		if rec.ot_days > rec.total_days:
			raise osv.except_osv(_('Warning !!'),
				_('OT Days should not exceed Total Days !!'))
		if rec.present_days+rec.ot_days != rec.total_days:
			raise osv.except_osv(_('Warning !!'),
				_('OT and Present Days are mismatched !!'))
		if rec.ot_days < 0.00:
			raise osv.except_osv(_('Warning !!'),
				_('OT Days should not be less than !!'))
				
		src_att = self.search(cr,uid,[('end_date','>',rec.start_date),('id','!=',rec.id),('labour_id','=',rec.labour_id.id)])
		print "------------------------------------------",src_att
		if src_att:
			raise osv.except_osv(_('Warning!'),
					_('Weekly Attendance are already generated for the given Start and End date'))
		return True
						
	_constraints = [

		(_validations, 'validations', [' ']),		
		
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
		return super(kg_weekly_attendance, self).write(cr, uid, ids, vals, context)	
	
	
	## Module Requirement
	
	def on_change_lab(self,cr,uid,ids,labour_id,labour_code,context=None):
		labour_rec = self.pool.get('kg.labour.master').browse(cr,uid,labour_id)
		value = {'labour_code':labour_rec.code,'labour_categ':labour_rec.type}
		return {'value': value}
		
	def onchange_end_date(self, cr, uid, ids,start_date,end_date,context=None):
		value = {'start_date':'','end_date':''}
		d1 =  datetime.strptime(start_date, "%Y-%m-%d")
		d2 =  datetime.strptime(end_date, "%Y-%m-%d")
		rd = rdelta.relativedelta(d2,d1)
		delta = d1 - d2
		no_of_days= delta.days
		if no_of_days=='0':
			value = {
				'total_days':1,
				}
		else:
			value = {
				'total_days':delta.days+1,
				}
		return {'value': value}

kg_weekly_attendance()


