import math
import re
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
import netsvc
import datetime
import calendar
from datetime import date
import re
import urllib
import urllib2
import logging
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import calendar
a = datetime.now()
dt_time = a.strftime('%m/%d/%Y %H:%M:%S')
today = datetime.now()

class kg_holiday_master(osv.osv):

	_name = "kg.holiday.master"
	_description = 'Enables you to View The Gvt Holidays'
	_columns = {
	
				'date': fields.datetime('Creation Date', readonly=True)	,
				'user_id': fields.many2one('res.users','Created By', readonly=True),	
				'from_date':fields.date('Valid From',readonly=True, states={'draft':[('readonly',False)]}),
				'to_date':fields.date('Valid Till',readonly=True, states={'draft':[('readonly',False)]}),
				'active':fields.boolean('Active'),
				'expiry_date':fields.date('Expiry Date'),
				'state': fields.selection([('draft','Draft'),('confirm','Waiting for approval'),('approved','Approved'),
					('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True,track_visibility='onchange',select=True),
				'approve_date': fields.datetime('Approved Date', readonly=True),
				'app_user_id': fields.many2one('res.users', 'Approved By', readonly=True),
				'confirm_date': fields.datetime('Confirm Date', readonly=True),
				'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
				'reject_date': fields.datetime('Reject Date', readonly=True),
				'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
				'cancel_date': fields.datetime('Cancel Date', readonly=True),
				'can_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
				'line_id':fields.one2many('kg.holiday.master.line','line_entry','Line id',readonly=True, states={'draft':[('readonly',False)]}),
				'company_id': fields.many2one('res.company', 'Company Name',readonly=True),	
				'remark': fields.text('Remarks',readonly=False,states={'approved':[('readonly',True)]}),
				}

	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_holiday_master', context=c),
		'date':fields.datetime.now,		
		'state': 'draft',		
		'active': True,
		'user_id': lambda obj, cr, uid, context: uid,
		
				}
	
	
	def approve_entry(self, cr, uid, ids,context=None):		
		self.write(cr,uid,ids,{'state':'approved','app_user_id':uid,'approve_date':today})
		return True
		
	def confirm_entry(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		print "entry-----------",entry
		entry_obj = self.pool.get('kg.holiday.master')
		start_date = entry.from_date
		end_date = entry.to_date
		entry_id=entry.id	
		duplicate_ids= entry_obj.search(cr, uid, [('from_date','=',start_date),('to_date','=',end_date),('id' ,'!=', entry_id)])
		print "du[plicate..............",duplicate_ids
		if duplicate_ids:
			dup_rec = entry_obj.browse(cr,uid,duplicate_ids[0])
			print "dup_rec...............",dup_rec
			today_date = today
			print "today_date....................",today_date
			dup_rec.write({'active': False})
			dup_rec.write({'expiry_date':today_date})
		self.write(cr,uid,ids,{'state':'confirm','conf_user_id':uid,'confirm_date':today})	
		return True
	def draft_entry(self, cr, uid, ids, context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True
		
	def _check_entry_line(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if not entry.line_id:
			return False
		else:
			for line in entry.line_id:
				if line.leave_date == '':
					return False
		return True
	
	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'state': 'reject','rej_user_id': uid, 'reject_date': dt_time})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter rejection remark in remark field !!'))
		return True
		
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
		
		(_check_entry_line, 'Line entry can not be empty !!',['Line Entry']),
				
		]

kg_holiday_master()

class kg_holiday_master_line(osv.osv):
	
	_name = "kg.holiday.master.line"
	_description = "Holiday Master Line"
	
	_columns = {

	'line_entry':fields.many2one('kg.holiday.master','Line Entry'),
	'leave_date':fields.date('Date'),
	'note':fields.text('Description')
	
	}
	
kg_holiday_master_line()	

