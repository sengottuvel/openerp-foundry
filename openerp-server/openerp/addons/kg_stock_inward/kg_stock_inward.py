from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')


class kg_stock_inward(osv.osv):

	_name = "kg.stock.inward"
	_description = "Stock Inward Entry"
	_order = "entry_date desc"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Inward No', size=128,select=True,readonly=True),
		'entry_date': fields.date('Inward Date',required=True),
		
		'division_id': fields.many2one('kg.division.master','Division',domain="[('state','=','approved'), ('active','=','t')]",required=True),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location', required=True),
		'note': fields.text('Notes'),
		'remarks': fields.text('Remarks'),
		
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'line_ids': fields.one2many('ch.stock.inward.details', 'header_id', "Inward Details"),
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),		
		
		
	}
	

	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_stock_inward', context=c),			
		'entry_date' : fields.date.context_today,
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',		
		'active': True,
		
		
		
	}
	

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
			
		
	def _check_lineitems(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if not entry.line_ids:
			return False
		return True
			
	
	_constraints = [        
              
        
        (_future_entry_date_check, 'System not allow to save with future date. !!',['']),
        (_check_lineitems, 'System not allow to save with empty Inward Details !!',['']),
       
        
       ]
       

	def entry_confirm(self,cr,uid,ids,context=None):
		today = date.today()
		today = str(today)
		
		entry = self.browse(cr,uid,ids[0])
		for line_item in entry.line_ids:
			#### Stock Updation Block Starts Here ###
							
			cr.execute(''' insert into kg_foundry_stock(company_id,division_id,location,pump_model_id,pattern_id,part_name_id,
			moc_id,stage_id,stock_inward_id,qty,alloc_qty,type,creation_date)
			
			values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0.00,'IN',%s)
			''',[entry.company_id.id,entry.division_id.id or None,entry.location,line_item.pump_model_id.id, line_item.pattern_id.id,line_item.part_name_id.id,
			line_item.moc_id.id,line_item.stage_id.id,line_item.id,line_item.qty,entry.entry_date])
					
			#### Stock Updation Block Ends Here ###
		
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'),
			'name' :self.pool.get('ir.sequence').get(cr, uid, 'kg.stock.inward') or '/'})
		cr.execute(''' update ch_stock_inward_details set state = 'confirmed' where header_id = %s ''',[ids[0]])
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
		return super(kg_stock_inward, self).write(cr, uid, ids, vals, context)
	
	
kg_stock_inward()


class ch_stock_inward_details(osv.osv):

	_name = "ch.stock.inward.details"
	_description = "Inward Details"
	
	_columns = {
	
		### Inward Details ####
		'header_id':fields.many2one('kg.stock.inward', 'Stock Inward', required=1, ondelete='cascade'),
		'inward_date': fields.related('header_id','entry_date', type='date', string='Date', store=True, readonly=True),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model', required=True,domain="[('state','=','approved'), ('active','=','t')]"),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern Number', required=True,domain="[('state','=','approved'), ('active','=','t')]"),
		'part_name_id': fields.many2one('product.product','Part Name', required=True,domain="[('state','=','approved'), ('active','=','t')]"),
		'moc_id': fields.many2one('kg.moc.master','MOC',required=True,domain="[('state','=','approved'), ('active','=','t')]"),
		'stage_id': fields.many2one('kg.stage.master','Stage',required=True,domain="[('state','=','approved'), ('active','=','t')]"),
		'qty': fields.float('Stock Qty', size=100, required=True),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'active': fields.boolean('Active'),
		'cancel_remark': fields.text('Cancel Remarks'),
		
		
	
	}
	
	
	_defaults = {
	
		'state': 'draft',				
		'active': True,
		
	}
		
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty == 0.00 or entry.qty < 0.00:
			return False
		return True
		
	def _check_line_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(''' select id from ch_stock_inward_details where  pump_model_id = %s and pattern_id = %s and part_name_id = %s and
			stage_id = %s and moc_id = %s and id != %s and header_id = %s ''',[entry.pump_model_id.id, entry.pattern_id.id, entry.part_name_id.id,
			entry.stage_id.id, entry.moc_id.id, entry.id, entry.header_id.id,])
		duplicate_id = cr.fetchone()
		if duplicate_id:
			return False
		return True
		
		
	def create(self, cr, uid, vals, context=None):	
		return super(ch_stock_inward_details, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		return super(ch_stock_inward_details, self).write(cr, uid, ids, vals, context)
		
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []
		for rec in self.browse(cr,uid,ids):	
			if rec.state != 'draft':
				raise osv.except_osv(_('Warning!'),
						_('You can not delete Inward Details after confirmation !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	
	
	_constraints = [        
              
        (_check_values, 'System not allow to save with zero and less than zero qty .!!',['Quantity']),
        (_check_line_duplicates, 'Inward Details are duplicate. Kindly check !! ', ['']),
        
        
       ]
	
ch_stock_inward_details()






