from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_depreciation(osv.osv):
	
	_name = "kg.depreciation"
	_description = "Depreciation"
	_order = "entry_date desc"
	
	_columns = {
		
		## Basic Info
		
		'name': fields.char('No', size=12,select=True,readonly=True),
		'entry_date': fields.date('Date',required=True),
		'note': fields.text('Notes'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		'flag_sms': fields.boolean('SMS Notification'),
		'flag_email': fields.boolean('Email Notification'),
		'flag_spl_approve': fields.boolean('Special Approval'),
		
		## Module Requirement Info
		
		'product_code': fields.char('Product Code',readonly=True),
		'product_id': fields.many2one('product.product','Product Name',readonly=True,required=True),
		'grn_no': fields.char('GRN No',readonly=True),
		'grn_id': fields.many2one('kg.po.grn','GRN No',readonly=True),
		'grn_date': fields.date('GRN Date',readonly=True,required=True),
		'qty': fields.float('Quantity',readonly=True,required=True),
		'each_val_actual': fields.float('Each Value(Actual)',readonly=True,required=True),
		'tot_val_actual': fields.float('Tot Value(Actual)',readonly=True,required=True),
		'each_val_crnt': fields.float('Each Value(Current)',readonly=True,required=True),
		'tot_val_crnt': fields.float('Tot Value(Current)',readonly=True,required=True),
		'salvage_val': fields.float('Salvage value'),
		'depreciation_val': fields.float('Depreciation Value/year'),
		'depreciation_val_year': fields.integer('Depreciation Years'),
		
		## Entry Info
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),	
		'active': fields.boolean('Active'),
		'crt_date': fields.datetime('Created Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'ap_rej_date': fields.datetime('Approved/Rejected Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Rejected By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		
	}
	
	_defaults = {
		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_depreciation', context=c),			
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',		
		'active': True,
		'entry_mode': 'manual',
		'flag_sms': False,		
		'flag_email': False,		
		'flag_spl_approve': False,		
		
	}
	
	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])		
		### Sequence Number Generation  ###
		if rec.state == 'draft':		
			if rec.name == '' or rec.name == False:
				seq_obj_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depreciation')])
				seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_obj_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_obj_id[0],seq_rec.code,rec.entry_date))
				entry_name = cr.fetchone();
				entry_name = entry_name[0]
			else:
				entry_name = rec.name		
			self.write(cr, uid, ids, {'name':entry_name,'state': 'confirmed','confirm_user_id': uid, 'confirm_date': dt_time})
		else:
			pass
		return True
	
	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': dt_time})
		else:
			pass
		return True
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': dt_time})
		else:
			pass
		return True
	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
	def create(self, cr, uid, vals, context=None):
		return super(kg_depreciation, self).create(cr, uid, vals, context=context)
	
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': dt_time,'update_user_id':uid})
		return super(kg_depreciation, self).write(cr, uid, ids, vals, context)
	
kg_depreciation()
