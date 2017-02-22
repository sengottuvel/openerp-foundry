from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_shift_master(osv.osv):

	_name = "kg.shift.master"
	_description = "Shift Master"

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
					as sam  """ %('kg_shift_master'))
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
			
		'name': fields.char('Name', size=128, required=True, select=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'code': fields.char('Code', size=128, required=True),
		'start_time': fields.float('Start Time', required=True),
		'end_time': fields.float('End Time', required=True),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		
		### Entry Info ###
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
		
		'grace_period': fields.integer('Grace Period(minutes)', required=False),
		'rotation': fields.boolean('Rotation'),
		'sequence': fields.integer('Sequence',),
		'shift_hours': fields.float('Shift Hours'),
		'min_ot_hours': fields.float('Minimum OT Hours'),
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.shift.master', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),	
		'modify': 'no',
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Name must be unique per Company !!'),
		('code', 'unique(code)', 'Code must be unique per Company !!'),
	]
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])		
		if rec.start_time <= 0.0 or rec.end_time <= 0.0:		
			raise osv.except_osv(_('System should not be allow zero values!!'),
			 _('Kindly check Start time and End time!!'))				
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		sql = """ select max(sequence) from kg_shift_master """
		cr.execute(sql)
		data = cr.dictfetchall()
		print "@@@@@@@@@@@@@@@@@@@@",data[0]['max']
		if data[0]['max'] is None:
			sequence = 0
		else:
			sequence = data[0]['max']
		self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S'),'sequence':(sequence+1)})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'state': 'reject','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter the remarks in rejection remark field !!'))
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
		return super(kg_shift_master, self).write(cr, uid, ids, vals, context)
	
	def onchange_end_time(self, cr, uid, ids, start_time,end_time, context=None):
		value = {'start_time':'','end_time':'','shift_hours':''}
		if end_time <= 13.00:
			shf_tme = 24.00 - start_time + end_time
		else:
			shf_tme = end_time - start_time
		print "*************************************",shf_tme
		if shf_tme < 0:
			shf_tme = -(shf_tme)
		value = {
				'shift_hours': shf_tme,
				}
		return {'value': value}
		 
		
	###Validations
		
	def val_negative(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.start_time <= 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values and Zeros are not allowed in Start Time !!'))
		if rec.start_time > 24.00:
			raise osv.except_osv(_('Warning!'),
						_('Start Time Should not Exceed 24 Hours !!'))
		if rec.end_time <= 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values are not allowed in End Time !!'))
		if rec.end_time > 24.00:
			raise osv.except_osv(_('Warning!'),
						_('End Time Should not Exceed 24 Hours !!'))
		if rec.grace_period < 0:
			raise osv.except_osv(_('Warning!'),
						_('Negative Values are not allowed in Grace Period !!'))
		if rec.grace_period > 30:
			raise osv.except_osv(_('Warning!'),
						_('Grace Period should not exceed 30 Minutes !!'))
		#~ if rec.end_time < rec.start_time:
			#~ raise osv.except_osv(_('Warning!'),
						#~ _('End Time should not be less than Start Time !!'))
		if rec.end_time == rec.start_time:
			raise osv.except_osv(_('Warning!'),
						_('End Time and Start Time should not be same !!'))
		
		if rec.sequence:
				add_ids = self.pool.get('kg.shift.master').search(cr,uid,[('sequence','=',rec.sequence)])
				if len(add_ids) > 1:
					raise osv.except_osv(_('Warning!'),
						_('This Sequence is assigned to other Shift !!'))
					return False

		return True
		
	_constraints = [	
		(val_negative, 'Shift name must be unique !!', ['name']),		
		
	]
	
kg_shift_master()
