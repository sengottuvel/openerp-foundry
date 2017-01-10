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
		'mobile': fields.char('Mobile', size=128),
		'phone': fields.char('Phone', size=128),
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
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Transport name must be unique per Company !!'),
	]
	
	#~ def _code_validate(self, cr, uid,ids, context=None):
		#~ rec = self.browse(cr,uid,ids[0])
		#~ res = True
		#~ if rec.code:
			#~ trans_code = rec.code
			#~ code = trans_code.upper()			
			#~ cr.execute(""" select upper(code) from kg_transport where upper(code) = '%s' """ %(code))
			#~ data = cr.dictfetchall()			
			#~ if len(data) > 1:
				#~ res = False
			#~ else:
				#~ res = True				
		#~ return res
	
	def _check_zip(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.zip:
			if len(str(rec.zip)) in (6,7,8) and rec.zip.isdigit() == True:
				return True
		else:
			return True
		return False
	
	def  _validate_email(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0]) 
		if rec.email==False:
			return True
		else:
			if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", rec.email) != None:
				return True
			else:
				raise osv.except_osv('Invalid Email', 'Please enter a valid email address')  
				
	def _check_website(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.website != False:
			if re.match('www.(?:www)?(?:[\w-]{2,255}(?:\.\w{2,6}){1,2})(?:/[\w&%?#-]{1,300})?',rec.website):
				return True
			else:
				return False
		return True
	
	def _check_mobile_no(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.mobile:
			if len(str(rec.mobile)) in (10,11,12) and rec.mobile.isdigit() == True:
				return True
			else:
				raise osv.except_osv(_('Warning!'),
					_('Mobile No. should contain 10-12 digit numerics. Else system not allow to save.!'))
		if rec.phone:
			if len(str(rec.phone)) in (10,11,12) and rec.phone.isdigit() == True:
				return True
			else:
				raise osv.except_osv(_('Warning!'),
					_('Phone No. should contain 10-12 digit numerics. Else system not allow to save.!'))
		return True
	
	def _spl_name(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.name:
			name_special_char = ''.join(c for c in rec.name if c in '!@#$%^~*{}?+/=')
			if name_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Name!'))
		if rec.address:
			address_special_char = ''.join(c for c in rec.address if c in '!@#$%^~*{}?+/=')
			if address_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Address!'))
		if rec.contact_person:
			person_special_char = ''.join(c for c in rec.contact_person if c in '!@#$%^~*{}?+/=')
			if person_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Contact Person!'))
		
		return True
		
	_constraints = [
	
		#~ (_code_validate, 'Code must be unique !!', ['Code']),		
		(_check_zip,'ZIP should contain 6-8 digit numerics. Else system not allow to save.',['ZIP']),
		(_validate_email,'Enter a correct Email !',['Email']),
		(_check_website,'Enter a correct Website !',['Website']),
		(_check_mobile_no,'Mobile No. should contain 10-12 digit numerics. Else system not allow to save.',['']),
		(_spl_name, 'Special Character Not Allowed!', ['']),
		
	]
	
	def onchange_zip(self,cr,uid,ids,zip,context=None):
		print"fffffffffffffFFFF"
		if len(str(zip)) in (6,7,8):
			value = {'zip':zip}
		else:
			raise osv.except_osv(_('Check zip number !!'),
				_('zip should contain 6-8 digit numerics. Else system not allow to save. !!'))
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
				
	#~ def create(self, cr, uid, vals,context=None):		
		#~ if vals.get('code','/')=='/':
			#~ vals['code'] = self.pool.get('ir.sequence').get(cr, uid, 'kg.transport') or '/'
		#~ order =  super(kg_transport, self).create(cr, uid, vals, context=context)
		#~ return order
		
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
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_transport, self).write(cr, uid, ids, vals, context)
				
	"""			   
	def delete_transport(self,cr,uid,ids,context = None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			de = self.pool.get('res.users').browse(cr,uid,uid)
			user_name = de.name
			if user_name != 'Md':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				cr.execute('''		
				delete from kg_transport where id = %s '''%(ids[0]))
		return True
				   
	def unlink(self,cr,uid,ids,context=None):
		raise osv.except_osv(_('Warning!'),
				_('You can not delete Entry !!'))	
	"""	
	
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
	
	def _check_mobile_no(self, cr, uid, ids, context=None):		
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
		
	def _spl_name(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.name:
			name_special_char = ''.join(c for c in rec.name if c in '!@#$%^~*{}?+/=')
			if name_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Contact Name!'))
		if rec.position:
			position_special_char = ''.join(c for c in rec.position if c in '!@#$%^~*{}?+/=')
			if position_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Job Position!'))
		if rec.branch:
			branch_special_char = ''.join(c for c in rec.branch if c in '!@#$%^~*{}?+/=')
			if branch_special_char:
				raise osv.except_osv(_('Warning!'),
					_('Special Character Not Allowed in Branch!'))
		return True
	
	_constraints = [
		
		(_check_mobile_no,'Mobile No. should contain 10-12 digit numerics. Else system not allow to save.',['']),
		(_spl_name, 'Special Character Not Allowed!', ['']),
		
	]
		
kg_transport_line()
