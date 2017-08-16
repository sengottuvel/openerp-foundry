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

class kg_weekly_wages(osv.osv):

	_name = "kg.weekly.wages"
	_description = "Weekly Wages"
	
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
		
	def _tot_wage_amt(self, cr, uid, ids, field_name, arg, context=None):		
		res = {}
		tot_val = 0
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'tot_val': 0.0,
			}
			for item in order.line_id:
				tot_val += item.total_wages
				print "tot_valtot_valtot_valtot_valtot_val",tot_val
			else:
				tot_val = 0
			res[order.id]['tot_val'] = tot_val or 0.00
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
		'labour_categ':fields.selection([('individual','Individual'),('contract','Contract')],'Category'),
		'total_days':fields.float('Total Days'),
		'contractor_id':fields.many2one('res.partner','Contractor',domain=[('partner_state','=','approved'),('contractor','=',True)]),
		'tot_val':fields.function(_tot_wage_amt, string='Total Value',multi="sums",store=True),
		##Child Declaration
		
		'line_id': fields.one2many('ch.weekly.wages', 'header_id','Line Id'),
	
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
		if rec.total_days != 7.00:
			raise osv.except_osv(_('Warning !!'),
				_('End Date should not be less than or equal to Start Date !!'))
		
		return True
						
	_constraints = [

		#~ (_validations, 'validations', [' ']),		
		
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
		return super(kg_weekly_wages, self).write(cr, uid, ids, vals, context)	
	
	
	## Module Requirement
		
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
		
	def generate_wages(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		labour_obj = self.pool.get('kg.labour.master')
		weekly_att_obj = self.pool.get('kg.weekly.attendance')
		cr.execute('''select id from kg_labour_master where active='t' and contractor_id is null ''')
		data = cr.fetchall()
		src_wages = self.search(cr,uid,[('start_date','<=',rec.start_date),('end_date','>=',rec.end_date),('id','!=',rec.id)])
		if src_wages:
			raise osv.except_osv(_('Warning!'),
					_('Weekly Wages are already generated for the given Start and End date'))
		if rec.line_id:
			cr.execute('''delete from ch_weekly_wages where header_id=%s'''%(rec.id))
		if rec.labour_categ == 'individual':
			for i in data:
				labour_rec = labour_obj.browse(cr,uid,i[0])
				src_att = weekly_att_obj.search(cr,uid,[('labour_id','=',i[0]),('start_date','>=',rec.start_date),('end_date','<=',rec.end_date)])
				if src_att:
					att_rec = weekly_att_obj.browse(cr,uid,src_att[0])
					wage_per_day = labour_rec.shift_hrs * labour_rec.rate_per_hr
					total_wages = att_rec.tot_wage_days * wage_per_day
					print "total_wagestotal_wagestotal_wages",type(total_wages)
					self.pool.get('ch.weekly.wages').create(cr,uid,
							{
								'header_id':rec.id,
								'labour_id':i[0],
								'labour_code':labour_rec.code,
								'wage_days':att_rec.tot_wage_days,
								'wage_per_day':wage_per_day,
								'total_wages':total_wages,
							})
				else:
					pass
					#~ raise osv.except_osv(_('Warning!'),
							#~ _('Weekly Attendance is not generated for %s for the given start and end date'%(labour_rec.name)))
		else:
			src_labs = labour_obj.search(cr,uid,[('contractor_id','=',rec.contractor_id.id),('active','=','t')])
			print "sssssssssssssssssssssssssssssssssssssssssss",src_labs
			for labs in src_labs:
				labour_rec = labour_obj.browse(cr,uid,labs)
				src_att = weekly_att_obj.search(cr,uid,[('labour_id','=',labs),('start_date','=',rec.start_date),('end_date','=',rec.end_date)])
				if src_att:
					att_rec = weekly_att_obj.browse(cr,uid,src_att[0])
					wage_per_day = labour_rec.shift_hrs * labour_rec.rate_per_hr
					total_wages = att_rec.tot_wage_days * wage_per_day
					print "total_wagestotal_wagestotal_wages",type(total_wages)
					self.pool.get('ch.weekly.wages').create(cr,uid,
							{
								'header_id':rec.id,
								'labour_id':labs,
								'labour_code':labour_rec.code,
								'wage_days':att_rec.tot_wage_days,
								'wage_per_day':wage_per_day,
								'total_wages':total_wages,
							})
				else:
					pass
					#~ raise osv.except_osv(_('Warning!'),
							#~ _('Weekly Attendance is not generated for %s for the given start and end date'%(labour_rec.name)))
		return True
	
	
kg_weekly_wages()

class ch_weekly_wages(osv.osv):
	
	_name = 'ch.weekly.wages'
	
	_columns ={
		
		'header_id': fields.many2one('kg.weekly.wages','Header_id'),
		'labour_id':fields.many2one('kg.labour.master','Name'),
		'labour_code':fields.char('Code'),
		'wage_days':fields.float('Wage Days'),
		'wage_per_day':fields.float('Wage Per Day'),
		'total_wages':fields.float('Total Wages'),

	}
	
ch_weekly_wages()


