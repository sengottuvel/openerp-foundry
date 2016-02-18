from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import datetime
import openerp.addons.decimal_precision as dp

class kg_transport(osv.osv):

	_name = "kg.transport"
	_description = "KG Transport"
	
	_columns = {
		
		'created_by': fields.many2one('res.users', 'Created By', readonly=True),
		'creation_date': fields.datetime('Creation Date', readonly=True),
		'code': fields.char('Code',required=True,readonly=False, states={'draft':[('readonly',False)]}),
		'name': fields.char('Transport Name', size=128, required=True, select=True,readonly=True, states={'draft':[('readonly',False)]}),
		'company_id': fields.many2one('res.company', 'Company Name'),
		'contact_person': fields.char('Contact Person', size=128, required=True, readonly=True, states={'draft':[('readonly',False)]}, select=True),
		'address': fields.char('Address', size=128),
		'address1': fields.char('Address1', size=128),
		'city': fields.char('City', size=128),
		'zip': fields.char('Zip', size=128),
		'mobile': fields.char('Mobile', size=128),
		'phone': fields.char('Phone', size=128),
		'email': fields.char('Email', size=128),
		'state_id': fields.many2one('res.country.state', 'State'),
		'country_id': fields.many2one('res.country', 'Country'),
		'active': fields.boolean('Active'),
		'int_notes': fields.text('Internal Notes'),
		'state': fields.selection([('draft','Draft'),('confirm','Confirmed'),('approve','Approved')],'Status',required=True,readonly=True),
		'confirm_by': fields.many2one('res.users','Confirmed By'),
		'confirm_date': fields.datetime('Confirmed Date'),
		'approve_by': fields.many2one('res.users','Approved By'),
		'approve_date': fields.datetime('Approve Date'),
		'transport_user_id': fields.many2one('res.users','Transport User'),
		'rules': fields.text('Rules'),
		'line_id': fields.one2many('kg.transport.line','header_id', 'Transport Line'),
		
	}
	
	_defaults = {
		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.transport', context=c),
		'active': True,
		'code': '/',
		'state': 'draft',
		'created_by': lambda obj, cr, uid, context: uid,
		'creation_date' :  fields.datetime.now,
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Transport name must be unique per Company !!'),
	]
	
	#_sql_constraints = [
	
	#	('code', 'unique(code)', 'Transport Code must be unique per Company !!'),
	#]
	
	def create(self, cr, uid, vals,context=None):		
		if vals.get('code','/')=='/':
			vals['code'] = self.pool.get('ir.sequence').get(cr, uid, 'kg.transport') or '/'
		order =  super(kg_transport, self).create(cr, uid, vals, context=context)
		return order
		
	def confirm_transport(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		cur_date = datetime.datetime.now()
		self.write(cr,uid,ids,{'state': 'confirm','confirm_by': uid, 'confirm_date': cur_date})
		return True
		
	def approve_transport(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		cur_date = datetime.datetime.now()
		self.write(cr,uid,ids,{'state': 'approve','approve_by': uid, 'approve_date': cur_date})
		return True
	
	def unlink(self,cr,uid,ids,context = None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
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
		'name': fields.char('Contact Name', size=128),
		'position': fields.char('Job Position', size=128),
		'branch': fields.char('Branch', size=128),
		'phone': fields.char('Phone'),
		'mobile': fields.char('Mobile'),
	
		
	}
	
	def call_from_device(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if not rec.mobile:
			raise osv.except_osv(_('Please Check Mobile Number !!!'),
				_('Please Enter Mobile Number For The Transport !!'))
		else:
			mob_no = str(rec.mobile)
			mob_no = mob_no.split('/', 1 )
			mob_no = str(mob_no[0])
			user_rec = self.pool.get('res.users').browse(cr,uid,uid)
			exe_no = str(user_rec.ext_no)		
			#url = 'http://192.168.1.150/pbxclick2call.php?exten='+exe_no+'&phone='+mob_no
			url = 'http://192.168.1.150:81/pbxclick2call.php?exten='+exe_no+'&phone='+mob_no
			#url = 'http://cloud.kgisl.com/gayathri_click_to_call.php?id=123&date=2014-12-29&time=21:30&ioflag=IN&macno=01'	
			print "url..................................", url
			
			return {
						  'name'     : 'Go to website',
						  'res_model': 'ir.actions.act_url',
						  'type'     : 'ir.actions.act_url',
						  'target'   : 'current',
						  'url'      : url
				   }
	
	def call_from_device_hardphone(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if not rec.mobile:
			raise osv.except_osv(_('Please Check Mobile Number !!!'),
				_('Please Enter Mobile Number For The Transport !!'))
		else:
			mob_no = str(rec.mobile)
			mob_no = mob_no.split('/', 1 )
			mob_no = str(mob_no[0])
			user_rec = self.pool.get('res.users').browse(cr,uid,uid)
			exe_no = str(user_rec.ext_no2)		
			#url = 'http://192.168.1.150/pbxclick2call.php?exten='+exe_no+'&phone='+mob_no
			url = 'http://192.168.1.150:81/pbxclick2call.php?exten='+exe_no+'&phone='+mob_no
			#url = 'http://cloud.kgisl.com/gayathri_click_to_call.php?id=123&date=2014-12-29&time=21:30&ioflag=IN&macno=01'	
			print "url..................................", url
			
			return {
						  'name'     : 'Go to website',
						  'res_model': 'ir.actions.act_url',
						  'type'     : 'ir.actions.act_url',
						  'target'   : 'current',
						  'url'      : url
				   }

kg_transport_line()
