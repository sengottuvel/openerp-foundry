from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
from itertools import groupby

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')


class kg_pattern_request(osv.osv):

	_name = "kg.pattern.request"
	_description = "Pattern Request"
	_order = "entry_date desc"
	

	_columns = {
	
		### Header Details ####
		'name': fields.char('Request No.', size=128,select=True),
		'entry_date': fields.date('Request Date',required=True),
		'note': fields.text('Notes'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		
		'production_line_ids':fields.many2many('kg.production','m2m_pattern_request_details' , 'request_id', 'production_id', 'Production Lines',
			domain="[('state','=','draft')]"),
			
		'line_ids': fields.one2many('ch.pattern.request.line', 'header_id', "Request Line Details"),
		
		'flag_reqline':fields.boolean('Request Line Created'),
		
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),		
		
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_pattern_request', context=c),
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'active': True,
		'state':'draft'
		
		
	}
	
	def onchange_production_ids(self, cr, uid, ids, production_line_ids):
		new_ids = production_line_ids[0][2]
		if ids:
			if new_ids != []:
				cr.execute(''' 
						select request_id,request_line_id,production_id from tmp_pattern_request_details 
						where production_id not in %s and request_id = %s

						''',[tuple(new_ids),ids[0]])
				deleted_ids = cr.dictfetchall()
				if deleted_ids:
					for item in deleted_ids:
						
						cr.execute(''' 
							select count(request_line_id) from tmp_pattern_request_details where 
							request_line_id = %s and request_id = %s

						''',[item['request_line_id'],ids[0]])
						req_line_count = cr.fetchone()
					
						if req_line_count[0] == 1:
						
							del_sql = """ delete from ch_pattern_request_line where header_id=%s and id = %s """ %(ids[0],item['request_line_id'])
							cr.execute(del_sql)
						
						del_sql = """ delete from tmp_pattern_request_details where request_id=%s and production_id = %s and request_line_id = %s """ %(ids[0],item['production_id'],item['request_line_id'])
						cr.execute(del_sql)
			
			if new_ids == []:
				del_sql = """ delete from ch_pattern_request_line where header_id=%s """ %(ids[0])
				cr.execute(del_sql)
						
				del_sql = """ delete from tmp_pattern_request_details where request_id=%s """ %(ids[0])
				cr.execute(del_sql)
				
		return True
	
	def update_line_items(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		
		production_obj = self.pool.get('kg.production')
		request_line_obj = self.pool.get('ch.pattern.request.line')
		
		del_sql = """ delete from ch_pattern_request_line where header_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		del_sql = """ delete from tmp_pattern_request_details where request_id=%s """ %(ids[0])
		cr.execute(del_sql)
		
		if entry.production_line_ids:
		
			produc_line_ids = map(lambda x:x.id,entry.production_line_ids)
			produc_line_browse = production_obj.browse(cr,uid,produc_line_ids)
			produc_line_browse = sorted(produc_line_browse, key=lambda k: k.pattern_id.id)
			groups = []
			
			for key, group in groupby(produc_line_browse, lambda x: x.pattern_id.id):
				groups.append(map(lambda r:r,group))
			for key,group in enumerate(groups):
				
				vals = {
				
					'header_id': entry.id,
					'pattern_id':group[0].pattern_id.id,
					'pattern_name':group[0].pattern_id.pattern_name,
					
				}
				
				request_line_id = request_line_obj.create(cr, uid,vals)
				
				for item in group:
					
					cr.execute(''' insert into tmp_pattern_request_details(request_id,request_line_id,production_id,creation_date)
						values(%s,%s,%s,now())
						''',[entry.id,request_line_id,item.id])	  
			self.write(cr, uid, ids, {'flag_reqline': True})

		return True
	
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		issue_obj = self.pool.get('kg.pattern.issue')
		if not entry.line_ids:
			raise osv.except_osv(_('Warning!'),
						_('System not allow to confirm without Request Items !!'))
						
						
		### Issue Creation against Pattern Request ###
		
		for req_item in entry.line_ids:
			
			vals = {
					
					'name': self.pool.get('ir.sequence').get(cr, uid, 'kg.pattern.issue'),
					'request_id': entry.id,
					'request_date': entry.entry_date,
					'request_line_id': req_item.id,
					'pattern_id':req_item.pattern_id.id,
					'pattern_name':req_item.pattern_id.pattern_name,
					'requested_qty':req_item.qty,
					'state': 'open',
				}
					
			issue_id = issue_obj.create(cr, uid,vals)
		
		self.write(cr, uid, ids, {'name':self.pool.get('ir.sequence').get(cr, uid, 'kg.pattern.request'),'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		cr.execute(''' update ch_pattern_request_line set state = 'confirmed' where header_id = %s ''',[ids[0]])
		return True
		
	def entry_cancel(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.cancel_remark == False:
			raise osv.except_osv(_('Warning!'),
						_('Cancellation Remarks is must !!'))
		self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S'),'transac_state':'cancel'})
		cr.execute(''' update ch_pattern_request_line set state = 'cancel' where header_id = %s ''',[ids[0]])
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):
			if rec.state == 'confirmed':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
		return osv.osv.unlink(self, cr, uid, ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_pattern_request, self).write(cr, uid, ids, vals, context)
		
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
	
	
kg_pattern_request()

class ch_pattern_request_line(osv.osv):

	_name = "ch.pattern.request.line"
	_description = "Pattern Request Line"
	
	_columns = {
	
		'header_id':fields.many2one('kg.pattern.request', 'Pattern Request', required=1, ondelete='cascade'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No',domain="[('state','=','approved'), ('active','=','t')]"),
		'pattern_name': fields.char('Pattern Name'),
		'qty': fields.integer('Requested Qty'),
		'remark': fields.text('Remarks'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		
	}
	
	
	_defaults = {
		
		
		'state': 'draft',
		'qty':1
	}
	
	
	
	def create(self, cr, uid, vals, context=None):
		return super(ch_pattern_request_line, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_pattern_request_line, self).write(cr, uid, ids, vals, context)
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):
			#### Deleting Many2Many Relational table ####
			
			cr.execute(''' delete from m2m_pattern_request_details where request_id=%s
				and production_id in (select production_id from tmp_pattern_request_details where request_id = %s
				and request_line_id = %s) ''',[rec.header_id.id,rec.header_id.id,rec.id])
			
			### Deleting Temp Patter req detail table ####
			
			cr.execute(''' delete from tmp_pattern_request_details where request_id=%s and
				request_line_id = %s ''',[rec.header_id.id,rec.id])
			
		return osv.osv.unlink(self, cr, uid, ids, context=context)
		
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty == 0 or entry.qty < 0:
			return False
		return True
		
		
	_constraints = [		
			  
		(_check_values, 'System not allow to save with zero and less than zero qty .!!',['Quantity']),
		
	   
		
	   ]
	
ch_pattern_request_line()









