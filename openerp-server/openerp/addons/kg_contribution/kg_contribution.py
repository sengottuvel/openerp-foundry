from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
import datetime
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_contribution(osv.osv):

	_name = "kg.contribution"
	_description = "Contribution Master"
	
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
					as sam  """ %('kg_contribution'))
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
		
		'pf_max_amt':fields.integer('PF Max Limit',states={'draft':[('readonly',False)]}),
		'esi_slab':fields.float('ESI Applicable Upto', states={'draft':[('readonly',False)]}),
		'expiry_date':fields.date('Expiry Date', states={'draft':[('readonly',False)]}),
		
		
		## Child Tables Declaration
		
		'line_id':fields.one2many('ch.contribution','header_id','Line id',readonly=True, states={'draft':[('readonly',False)]}),
		
				
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
	
	####Validations####
	
	def  _validations (self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if not rec.line_id:
			raise osv.except_osv(_('Warning!'),
				_('Contributions Should not be empty !!'))
			return False
		
		if rec.pf_max_amt == 0:
			raise osv.except_osv(_('Warning!'),
				_('PF Max Limit should not be Zero !!'))
		elif rec.esi_slab == 0.00:
			raise osv.except_osv(_('Warning!'),
				_('ESI Applicable Upto should not be Zero !!'))
			return False
			
		if rec.line_id:
			line_cont = [ line.cont_heads for line in rec.line_id ]
			a= [line_cont.count(i) for i in line_cont ]
			for j in a:
				if j > 1:
					raise osv.except_osv(_('Warning!'),
								_('Duplicate Contribution Heads are not allowed !!'))
					return False
			for line in rec.line_id:
				if line.cont_heads != 'vda':
					if line.cont_type == 'percent':
						if line.emp_cont_value == 0.00 or line.emp_cont_value > 15:
							raise osv.except_osv(_('Warning!'),
									_('Employee Value should not be Zero or greater then 15 % !!'))
						if line.emplr_cont_value == 0.00 or line.emplr_cont_value > 15:
							raise osv.except_osv(_('Warning!'),
									_('Employer Value should not be Zero or greater then 15 % !!'))
					if line.cont_type == 'fixed_amt':
						if line.emp_cont_value == 0.00 or line.emp_cont_value > 4000:
							raise osv.except_osv(_('Warning!'),
									_('Employee Value should not be Zero or greater then 4000 !!'))
						if line.emplr_cont_value == 0.00 or line.emplr_cont_value > 4000:
							raise osv.except_osv(_('Warning!'),
									_('Employer Value should not be Zero or greater then 4000 !!'))
				else:
					pass
					
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
		entry_obj = self.pool.get('kg.contribution')
		crt_date = rec.crt_date
		duplicate_ids= entry_obj.search(cr, uid, [('id' ,'!=', rec.id)])
		if duplicate_ids:
			dup_rec = entry_obj.browse(cr,uid,duplicate_ids[0])
			today_date = datetime.datetime.today()
			dup_rec.write({'active': False})
			dup_rec.write({'expiry_date':today_date})		
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
		return super(kg_contribution, self).write(cr, uid, ids, vals, context)	
	
	
	## Module Requirement
	
kg_contribution()

class ch_contribution(osv.osv):
	
	_name = "ch.contribution"
	_description = "Contribution Line"
	
	_columns = {

	'header_id':fields.many2one('kg.contribution','Header id'),
	'cont_heads':fields.selection([('pf','PF'),('esi','ESI'),('vda','VDA')],'Contribution Heads',required = True),
	'cont_type':fields.selection([('fixed_amt','Fixed Amount'),('percent','Percentage')],'Type',required=True),
	'emp_cont_value':fields.float('Employee Value',required=True),
	'emplr_cont_value':fields.float('Employer Value',required=True),
	
	}
	
ch_contribution()	
