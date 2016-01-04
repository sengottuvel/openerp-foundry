from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
import netsvc
import time
import openerp.exceptions
import datetime
from datetime import date

class kg_bom(osv.osv):
	
	_name = 'kg.bom'	
	
	
	_columns = {
		'name': fields.char('BOM No', size=128, required=True, select=True),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled'),('expire','Expired')],'Status', readonly=True),	
		'line_ids': fields.one2many('ch.bom.line', 'header_id', "BOM Line"),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True,domain="[('state','=','approved'), ('active','=','t')]"),	
		'uom_id': fields.many2one('product.uom', 'Unit of Measure', required=True, help="Default Unit of Measure used for all stock operation.", domain="[('state','=','approved'), ('active','=','t')]"),	
		'remarks':fields.text('Remarks'),
		'qty': fields.float('Qty', size=128,required=True,),
		'active':fields.boolean('Active'),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		
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
		'expire_date':fields.date('Expired Date'),
		'expire_user_id': fields.many2one('res.users', 'Expired By', readonly=True),		
	
		
	}
	
	_defaults = {
	  
	  'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.bom', context=c),
	  'active': True,
	  'state': 'draft',
	  'qty': 1.00,
	  'user_id': lambda obj, cr, uid, context: uid,
	  'crt_date':fields.datetime.now,	
	  
	}

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
		return super(kg_pattern_master, self).write(cr, uid, ids, vals, context)
	
kg_bom()



class ch_bom_line(osv.osv):
	
	_name = 'ch.bom.line'
	
	
	_columns = {
		
		'header_id':fields.many2one('kg.bom', 'BOM Entry', required=1, ondelete='cascade'),	
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No', required=True,domain="[('state','=','approved')]"),	
		'pattern_name': fields.char('Pattern Name', required=True),	
		'remarks':fields.text('Remarks'),
		'qty': fields.float('Qty', size=128,required=True,),
		'state':fields.selection([('draft','Draft'),('approve','Approved')],'Status'),
		
		
	}
	
	
	_defaults = {
	
	'state':'draft',
	  
	}
	
	def onchange_pattern_name(self, cr, uid, ids, pattern_id, context=None):
		
		value = {'pattern_name': ''}
		if pattern_id:
			pro_rec = self.pool.get('kg.pattern.master').browse(cr, uid, pattern_id, context=context)
			value = {'pattern_name': pro_rec.pattern_name}
			
		return {'value': value}	

	
ch_bom_line()









