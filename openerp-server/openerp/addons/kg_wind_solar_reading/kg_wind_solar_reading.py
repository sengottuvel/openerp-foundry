from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_wind_solar_reading(osv.osv):

	_name = "kg.wind.solar.reading"
	_description = "Wind/Solar Reading"
	
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
					as sam  """ %('kg_wind_solar_reading'))
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
	
		### Basic Info
			
		'name': fields.char('Name', size=128, required=False, select=True),	
		'code': fields.char('Code', size=4, required=False),		
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
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
		'date':fields.date('Date'),
		
		## Child Tables Declaration	
		
		'line_id':fields.one2many('ch.wind.solar.reading', 'header_id', "Debit Note Line"),	
		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.wind.solar.reading', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		'date' : lambda * a: time.strftime('%Y-%m-%d'),
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Name must be unique per Company !!'),
	]
	
	### Basic Needs	
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
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
		return super(kg_wind_solar_reading, self).write(cr, uid, ids, vals, context)

	## Module Requirement
	
	####### Validations ############
	
	def _check_lineitems(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		ser_dups = self.pool.get('kg.wind.solar.reading').search(cr,uid,[('date','=',entry.date)])
		if len(ser_dups) > 1:
			raise osv.except_osv(_('Warning!'),
				_('Entry has been created already for this date !!'))
		if not entry.line_id:
			raise osv.except_osv(_('Warning!'),
						_('Line Details should not be empty !!'))
		if entry.line_id:
			wind_ids = [ line.wind_solar_id for line in entry.line_id]
			a= [wind_ids.count(i) for i in wind_ids ]
			for j in a:
				if j > 1:
					raise osv.except_osv(_('Warning!'),
								_('Duplicate of %s are not allowed !!'%(wind_ids[0].name)))
		for lines in entry.line_id:
			if lines.units <= 0.00:
				raise osv.except_osv(_('Warning!'),
						_('Units Entered for %s should not be less than or equal to zero !!'%(lines.wind_solar_id.name)))
			
		return True
		
	
	_constraints = [
			 (_check_lineitems, 'System not allow to save with empty Concrete Details !!',['']),
       
		
	]
	
kg_wind_solar_reading()


class ch_wind_solar_reading(osv.osv):

	_name = "ch.wind.solar.reading"
	_description = "Wind/Solar Reading"
	
	_columns = {
	
		'header_id':fields.many2one('kg.wind.solar.reading', 'Header_id', ondelete='cascade'),
		'type' : fields.selection([('wind','Wind'),('solar','Solar')],'Type'),
		'wind_solar_id': fields.many2one('kg.wind.solar.master','Machinery / Unit',domain="[('state','=','approved'),('type','=',type)]"),
		'units': fields.float('Units Acquired'),
		'remarks': fields.text('Remarks'),
		
	}
	
ch_wind_solar_reading()
