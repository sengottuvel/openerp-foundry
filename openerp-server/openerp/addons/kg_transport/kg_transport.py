from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import datetime
import openerp.addons.decimal_precision as dp
import re

class kg_transport(osv.osv):
	
	_name = "kg.transport"
	_description = "KG Transport"
	
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
				as sam  """ %('kg_transport'))
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
		
		'code': fields.char('Code',readonly=True),
		'name': fields.char('Name', size=128, required=True, select=True,readonly=True, states={'draft':[('readonly',False)]}),
		'contact_person': fields.char('Contact Person', size=128, required=True, readonly=True, states={'draft':[('readonly',False)]}, select=True),
		'address': fields.char('Address', size=128),
		'address1': fields.char('Address1', size=128),
		'city_id': fields.many2one('res.city','City', size=128),
		'zip': fields.integer('Zip', size=8),
		'mobile': fields.char('Mobile', size=12),
		'phone': fields.char('Phone', size=15),
		'website': fields.char('Website', size=128),
		'email': fields.char('Email', size=128),
		'state_id': fields.many2one('res.country.state', 'State'),
		'country_id': fields.many2one('res.country', 'Country'),
		'int_notes': fields.text('Internal Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'transport_user_id': fields.many2one('res.users','Transport User'),
		'rules': fields.text('Notes'),
		'line_id': fields.one2many('kg.transport.line','header_id', 'Transport Line'),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=3),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		
		# Entry Info
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'created_by': fields.many2one('res.users', 'Created By', readonly=True),
		'creation_date': fields.datetime('Creatied Date', readonly=True),
		'confirm_by': fields.many2one('res.users','Confirmed By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'approve_by': fields.many2one('res.users','Approved By', readonly=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		'reject_date': fields.datetime('Rejected Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		
	}
	
	_defaults = {
		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.transport', context=c),
		'active': True,
		'state': 'draft',
		'created_by': lambda obj, cr, uid, context: uid,
		'creation_date' : lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Transport name must be unique per Company !!'),
	]
	
	def _validation(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.zip:
			if len(str(rec.zip)) not in range(6,8) and rec.zip.isdigit() != True:
				raise osv.except_osv(_('Warning'), _('ZIP should contain 6-8 digit numerics !!'))
		
		if rec.email==False:
			return True
		else:
			if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", rec.email) != None:
				return True
			else:
				raise osv.except_osv(_('Warning'), _('Invalid Email', 'Please enter a valid email address !!'))
		
		if rec.website != False:
			if re.match('www.(?:www)?(?:[\w-]{2,255}(?:\.\w{2,6}){1,2})(?:/[\w&%?#-]{1,300})?',rec.website):
				return True
			else:
				raise osv.except_osv(_('Warning'), _('Enter a correct Website !!'))
		
		if rec.mobile:
			if len(str(rec.mobile)) not in range(10,12) and rec.mobile.isdigit() != True:
				raise osv.except_osv(_('Warning!'),
					_('Mobile No. should contain 10-12 digit numerics !!'))
		
		if rec.phone:
			if len(str(rec.phone)) not in range(10,12) and rec.phone.isdigit() != True:
				raise osv.except_osv(_('Warning!'),
					_('Phone No. should contain 10-12 digit numerics !!'))
			
		return True
	
	_constraints = [
		
		(_validation,' ',['ZIP']),
		
	]
	
	def onchange_zip(self,cr,uid,ids,zip,context=None):
		if len(str(zip)) in (6,7,8):
			value = {'zip':zip}
		else:
			raise osv.except_osv(_('Warning !!'),
				_('zip should contain 6-8 digit numerics !!'))
		return {'value': value}
	
	def onchange_city(self, cr, uid, ids, city_id, context=None):
		if city_id:
			state_id = self.pool.get('res.city').browse(cr, uid, city_id, context).state_id.id
			return {'value':{'state_id':state_id}}
		return {}
	
	def onchange_state(self, cr, uid, ids, state_id, context=None):
		if state_id:
			country_id = self.pool.get('res.country.state').browse(cr, uid, state_id, context).country_id.id
			return {'value':{'country_id':country_id}}
		return {}
	
	def confirm_transport(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			if not rec.code:
				seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.transport')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
				cr.execute("""select generatesequenceno(%s,'%s',now()::date) """%(seq_id[0],seq_rec.code))
				seq_name = cr.fetchone();
				seq_code = seq_name[0]
			else:
				seq_code = rec.code
			self.write(cr,uid,ids,{'state': 'confirmed','confirm_by': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'code': seq_code})
		return True
	
	def approve_transport(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			self.write(cr,uid,ids,{'state': 'approved','approve_by': uid, 'approve_date': time.strftime('%Y-%m-%d %H:%M:%S')})
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
	
	def entry_draft(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			self.write(cr, uid, ids, {'state': 'draft'})
		return True
	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':			
				raise osv.except_osv(_('Delete access denied !'), _('Unable to delete. Draft entry only you can delete !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_transport, self).write(cr, uid, ids, vals, context)
	
kg_transport()


class kg_transport_line(osv.osv):
	
	_name = "kg.transport.line"
	_description = "KG Transport Line"
	
	_columns = {
		
		'header_id': fields.many2one('kg.transport','Transport'),
		'name': fields.char('Contact Name', size=128,required=True),
		'position': fields.char('Job Position', size=128),
		'branch': fields.char('Branch', size=128),
		'phone': fields.char('Phone'),
		'mobile': fields.char('Mobile',required=True),
		
	}
	
	def _validations(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.mobile:
			if len(str(rec.mobile)) in (12) and rec.mobile.isdigit() == True:
				return True
			else:
				raise osv.except_osv(_('Warning!'),
					_('Mobile No. should contain 10-12 digit numerics. Else system not allow to save.!'))
		if rec.phone:
			if len(str(rec.phone)) in (12) and rec.phone.isdigit() == True:
				return True
			else:
				raise osv.except_osv(_('Warning!'),
					_('Phone No. should contain 10-12 digit numerics. Else system not allow to save.!'))
		return True
	
	_constraints = [
		
		(_validations,' ',['Mobile No.']),
		
	]
		
kg_transport_line()
