from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
from itertools import groupby

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')


class kg_pattern_issue(osv.osv):

	_name = "kg.pattern.issue"
	_description = "Pattern Issue"
	_order = "entry_date desc"
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Issue No.', size=128,select=True),
		'entry_date': fields.date('Issue Date',required=True),
		'note': fields.text('Notes'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('open','Open'),('issue','Issued'),('receive','Received')],'Status'),
		
		'request_id': fields.many2one('kg.pattern.request', 'Request No.'),
		'request_date': fields.date('Requested Date'),
		
		'request_line_id': fields.many2one('ch.pattern.request.line', 'Request Line Id'),
		
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No.',domain="[('state','=','approved'), ('active','=','t')]"),
		'pattern_name': fields.char('Pattern Name'),
		
		'order_ref_no': fields.related('request_line_id','order_ref_no', type='char', string='Work Order No.', store=True),
		'order_type': fields.related('request_line_id','order_type', type='char', string='Order Type', store=True),
		'pump_model_id': fields.related('request_line_id','pump_model_id', type='many2one', relation='kg.pumpmodel.master', string='Pump Model', store=True),
		'moc_id': fields.related('request_line_id','moc_id', type='many2one', relation='kg.moc.master', string='MOC', store=True),
		
		'requested_qty': fields.integer('Requested Qty'),
		'remark': fields.text('Remarks'),
		
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'issue_date': fields.datetime('Issued Date', readonly=True),
		'issue_user_id': fields.many2one('res.users', 'Issued By', readonly=True),
		
		'receive_date': fields.datetime('Received Date', readonly=True),
		'receive_user_id': fields.many2one('res.users', 'Received By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),		
		
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_pattern_issue', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'open'
		
		
	}
	

	def pattern_issue(self,cr,uid,ids,context=None):
		"""
		if not ids:
			raise osv.except_osv(_('Warning!'),
						_('Kindly select Entries to proceed Further !!'))
		entry = self.browse(cr,uid,ids[0])
		if not remark and entry.remark == False:
			remarks = False
		if entry.remark != False:
			remarks = entry.remark
		if remark and entry.remark == False:
			remarks = remark
		if entry.state == 'open':
			core_obj = self.pool.get('kg.core.log')
			core_vals = {
						
				'name': self.pool.get('ir.sequence').get(cr, uid, 'kg.core.log'),
				'issue_id': entry.id,
				'issue_date': entry.entry_date,
				'pattern_id':entry.pattern_id.id,
				'pattern_name':entry.pattern_id.pattern_name,
				'order_ref_no':entry.order_ref_no,
				'pump_model_id':entry.pump_model_id.id,
				'moc_id':entry.moc_id.id,
				'state': 'draft',
			}
						
			core_id = core_obj.create(cr, uid,core_vals)
			
			moulding_obj = self.pool.get('kg.moulding.log')
			
			mould_vals = {
					
				'name': self.pool.get('ir.sequence').get(cr, uid, 'kg.moulding.log'),
				'issue_id': entry.id,
				'issue_date': entry.entry_date,
				'pattern_id':entry.pattern_id.id,
				'pattern_name':entry.pattern_id.pattern_name,
				'order_ref_no':entry.order_ref_no,
				'pump_model_id':entry.pump_model_id.id,
				'moc_id':entry.moc_id.id,
				'state': 'draft',
			}
					
			mould_id = moulding_obj.create(cr, uid,mould_vals)
			"""
			entry = self.browse(cr,uid,ids[0])
			self.write(cr, uid, ids, {'remark':entry.remark,'state': 'issue','issue_user_id': uid, 'issue_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def pattern_receive(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		self.write(cr, uid, ids, {'state': 'receive','receive_user_id': uid, 'receive_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):
			if rec.state in ('open','issue','receive'):
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_pattern_issue, self).write(cr, uid, ids, vals, context)
		
		
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		entry_date = rec.entry_date
		entry_date = str(entry_date)
		entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
		if entry_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),   
		
	   ]
		
	
	
	
kg_pattern_issue()

class ch_pattern_batch_issue(osv.osv):

	_name = "ch.pattern.batch.issue"
	_description = "Pattern Batch Issue"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Batch No.', size=128,select=True),
		'entry_date': fields.date('Batch Date',required=True),
		'note': fields.text('Notes'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('issue','Issued')],'Status', readonly=True),

		'issue_line_ids':fields.many2many('kg.pattern.issue','m2m_pattern_batch_issue_details' , 'batch_id', 'issue_id', 'Issue Lines',
			domain="[('state','=','open')]"),
			
		'line_ids': fields.one2many('ch.pattern.batch.line', 'header_id', "Request Line Details"),
		
		'flag_issueline':fields.boolean('Issue Line Created'),

		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Issued Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Issued By', readonly=True),		
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),	
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'ch_pattern_batch_issue', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft'
		
		
	}	

	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])		
		issue_obj = self.pool.get('kg.pattern.issue')
		issue_line_obj = self.pool.get('ch.pattern.batch.line')
		
		del_sql = """ delete from ch_pattern_request_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		
		if entry.issue_line_ids:
		
			for item in entry.issue_line_ids:
				
				
				vals = {
				
					'header_id': entry.id,
					'issue_id':item.id,
					'issue_date':item.entry_date,
					'request_id':item.request_id.id,
					'request_date':item.request_date,
					'pattern_id':item.pattern_id.id,
					'pattern_name':item.pattern_id.pattern_name,
					'requested_qty':item.requested_qty,
					'remark':item.remark,
				}
				
				issue_line_id = issue_line_obj.create(cr, uid,vals)
				
			self.write(cr, uid, ids, {'flag_issueline': True})
			
		return True
		
	def entry_issue(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		issue_obj = self.pool.get('kg.pattern.issue')		
		if not entry.line_ids:
			raise osv.except_osv(_('Warning!'),
						_('System not allow to confirm without Issue Items !!'))
						
						
		### Issue Creation against Pattern Issue ###
		
		for req_item in entry.line_ids:			
			issue_ids=issue_obj.search(cr,uid,[('name','=',req_item.issue_id.name)])		
			vals = {				
					'remark': req_item.remark,				
				}
				
			remark = req_item.remark
			issue_obj.pattern_issue(cr, uid, issue_ids, remark)
		
			self.pool.get('kg.pattern.issue').write(cr,uid,issue_ids,vals)
			
		self.write(cr, uid, ids, {'name':self.pool.get('ir.sequence').get(cr, uid, 'ch.pattern.batch.issue'),'state': 'issue','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id': uid, 'update_date': time.strftime('%Y-%m-%d %H:%M:%S')})
	
		return True
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(ch_pattern_batch_issue, self).write(cr, uid, ids, vals, context)
	
ch_pattern_batch_issue()


class ch_pattern_batch_line(osv.osv):

	_name = "ch.pattern.batch.line"
	_description = "Pattern Batch Line"
	
	_columns = {
	
		'header_id':fields.many2one('ch.pattern.batch.issue', 'Pattern Batch Issue', required=1, ondelete='cascade'),		
		
		'request_id': fields.many2one('kg.pattern.request', 'Request No.'),
		'request_date': fields.date('Requested Date'),
		
		'issue_id': fields.many2one('kg.pattern.issue', 'Issue No.'),
		'issue_date': fields.date('Issue Date'),
		
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No.',domain="[('state','=','approved'), ('active','=','t')]"),
		'pattern_name': fields.char('Pattern Name'),
		
		'requested_qty': fields.integer('Requested Qty'),
		'remark': fields.text('Remarks'),	
		
		
	}
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_pattern_batch_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_pattern_batch_line, self).write(cr, uid, ids, vals, context)
		
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.requested_qty == 0 or entry.requested_qty < 0:
			return False
		return True
		
		
	_constraints = [		
			  
		(_check_values, 'System not allow to save with zero and less than zero qty .!!',['Quantity']),
		
	   
		
	   ]
	
ch_pattern_batch_line()

