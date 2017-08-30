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
	
	def _get_default_division(self, cr, uid, context=None):
		res = self.pool.get('kg.division.master').search(cr, uid, [('code','=','SAM'),('state','=','approved'), ('active','=','t')], context=context)
		return res and res[0] or False
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Inward No', size=128,select=True,readonly=True),
		'entry_date': fields.date('Inward Date',required=True),
		'division_id': fields.many2one('kg.division.master','Division',readonly=True,required=True,domain="[('state','=','approved'), ('active','=','t')]"),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location'),
		'note': fields.text('Notes'),
		'remarks': fields.text('Remarks'),
		
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')],'Status', readonly=True),
		'line_ids': fields.one2many('ch.stock.inward.details', 'header_id', "Inward Details"),
		
		'total_value': fields.float('Total Value'),
		
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
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',		
		'active': True,
		'division_id':_get_default_division,
		
		
		
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
        #(_check_lineitems, 'System not allow to save with empty Inward Details !!',['']),
       
        
       ]
       

	def entry_confirm(self,cr,uid,ids,context=None):
		inward_line_obj = self.pool.get('ch.stock.inward.details')
		
		today = date.today()
		today = str(today)
		
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			for line_item in entry.line_ids:
				
				if line_item.serial_no != False:
					cr.execute(''' select id from ch_stock_inward_details where
						serial_no = %s and id != %s ''',[line_item.serial_no, line_item.id])
					duplicate_id = cr.fetchone()
					if duplicate_id:
						raise osv.except_osv(_('Warning!'),
						_('Serial No. must be Unique. Kindly check !!'))
				
				inward_line_obj.write(cr, uid, [line_item.id], {'available_qty':line_item.qty})
						
				#### Stock Updation Block Ends Here ###
				
				
			### Total Value ###
			cr.execute(''' select sum(total_value) from ch_stock_inward_details where header_id = %s ''',[ids[0]])
			inward_total = cr.fetchone()
			if inward_total[0] != None:
				total = inward_total[0]
			else:
				total = 0.00
				
			### Sequence Number Generation  ###
			inward_name = ''
			if not entry.name:		
				inward_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.stock.inward')])
				rec = self.pool.get('ir.sequence').browse(cr,uid,inward_id[0])
				cr.execute("""select generatesequenceno(%s,'%s','%s') """%(inward_id[0],rec.code,entry.entry_date))
				inward_name = cr.fetchone();
				inward_name = inward_name[0]
			else:
				inward_name = entry.name
			
			self.write(cr, uid, ids, {'name':inward_name,'total_value':total,'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			cr.execute(''' update ch_stock_inward_details set state = 'confirmed' where header_id = %s ''',[ids[0]])
		else:
			pass
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
		
	def create(self, cr, uid, vals, context=None):
		return super(kg_stock_inward, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_stock_inward, self).write(cr, uid, ids, vals, context)
		
	_sql_constraints = [
	
		('name', 'unique(name)', 'Stock Inward No. must be Unique !!'),
	]
	
	
kg_stock_inward()


class ch_stock_inward_details(osv.osv):

	_name = "ch.stock.inward.details"
	_description = "Inward Details"
	
	_columns = {
	
		### Inward Details ####
		'header_id':fields.many2one('kg.stock.inward', 'Stock Inward', required=1, ondelete='cascade'),
		'inward_date': fields.related('header_id','entry_date', type='date', string='Date', store=True, readonly=True),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD')],'Location'),
		'stock_type':fields.selection([('pump','Pump'),('pattern','Part')],'Type', required=True),
		'pump_model_id': fields.many2one('kg.pumpmodel.master','Pump Model',domain="[('active','=','t')]"),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern Number',domain="[('active','=','t')]"),
		'pattern_name': fields.char('Pattern Name'),
		#'part_name_id': fields.many2one('product.product','Part Name', required=True,domain="[('state','=','approved'), ('active','=','t')]"),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('active','=','t')]"),
		'stage_id': fields.many2one('kg.stage.master','Stage',domain="[('active','=','t')]"),
		'qty': fields.integer('Stock Qty'),
		'unit_price': fields.float('Material Amount'),
		'each_wgt': fields.float('Each Weight'),
		'total_wgt': fields.float('Total Weight'),
		'total_value': fields.float('Total Value'),
		'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('approve','Approved'),('cancel','Cancelled')],'Status'),
		'active': fields.boolean('Active'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'serial_no': fields.char('Serial No', size=128),
		'stock_no': fields.char('Stock No', size=128),
		'heat_no': fields.char('Heat No', size=128),
		'moc_construction_id':fields.many2one('kg.moc.construction','MOC Construction',domain="[('active','=','t')]"),
		'stock_mode': fields.selection([('manual','Manual'),('excess','Excess')],'Stock Mode'),
		'foundry_stock_state': fields.selection([('foundry_inprogress','Foundry In Progress'),('ready_for_ms','Ready for MS'),('reject','Rejected')],'Status'),
		'available_qty': fields.integer('Stock Qty'),
		'stock_item': fields.selection([('foundry_item','Foundry'),('ms_item','MS Item')],'MS Item'),
		'ms_stock_state': fields.selection([('operation_inprogress','Operation In Progress'),('ready_for_ass','Ready for Assembly'),('reject','Rejected')],'Status'),
		'item_code': fields.char('Item Code', size=128),
		'item_name': fields.char('Item Name', size=128),
		'stock_location_id': fields.many2one('stock.location','Stock Location',domain="[('usage','=','production')]"),
		'fettling_id': fields.integer('Fettling ID'),
		
		'order_id': fields.integer('Work Order No.'),
		'ms_finish_qty': fields.integer('MS Finish Qty'),
		'position_id':fields.many2one('kg.position.number','Position No.'),
		'remarks': fields.text('Remarks'),
	
	}
	
	
	_defaults = {
	
		'state': 'draft',				
		'active': True,
		'stock_mode': 'manual',
		'foundry_stock_state': 'ready_for_ms',
		'stock_item': 'foundry_item' 
		
	}
		
	def onchange_stock_qty(self, cr, uid, ids, pattern_id,moc_id,qty,each_wgt,unit_price,stock_type,total_value, context=None):
		mat_amt = 0.00
		pattern_name = False
		
		if stock_type == 'pump':
			stock_qty = 1.0
		else:
			stock_qty = qty
		print "stock_qty-----------------------",stock_qty
		if pattern_id != False:
			pattern_rec = self.pool.get('kg.pattern.master').browse(cr, uid, pattern_id, context=context)
			pattern_name = pattern_rec.pattern_name
		if moc_id != False:
			moc_rec = self.pool.get('kg.moc.master').browse(cr, uid, moc_id, context=context)
			mat_amt = moc_rec.rate or 0.00
		else:
			mat_amt = unit_price
		if stock_type == 'pattern':				
			total_weight = stock_qty * each_wgt or 0.00
			total_value = total_weight * mat_amt
		else:
			total_weight = stock_qty * each_wgt or 0.00
			total_value = total_value 
		value = {
		'pattern_name': pattern_name,
		'unit_price': mat_amt,
		'total_wgt': total_weight,
		'total_value': total_value,
		'qty': stock_qty
		
		}
		print"valuevalue",value
		return {'value': value}
		
	def entry_approve(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		self.write(cr, uid, ids, {'state':'approve','foundry_stock_state':'ready_for_ms'})
		return True
		
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.qty == 0 or entry.qty <= 0 or entry.each_wgt <= 0.00 or entry.unit_price <= 0.00:
			return False
		return True
		
	def _check_line_duplicates(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(''' select id from ch_stock_inward_details where pattern_id = %s  and
			moc_id = %s and id != %s and header_id = %s ''',[entry.pattern_id.id,
			entry.moc_id.id, entry.id, entry.header_id.id,])
		duplicate_id = cr.fetchone()
		if duplicate_id:
			return False
		return True
		
	
	def create(self, cr, uid, vals, context=None):
		inward_obj = self.pool.get('kg.stock.inward')
		pattern_name = False
		pattern_obj = self.pool.get('kg.pattern.master')
		moc_obj = self.pool.get('kg.moc.master')
		
		if vals.get('moc_id') > 0:
			moc_rec = moc_obj.browse(cr, uid, vals.get('moc_id') )
			mat_amt = moc_rec.rate or 0.00
		else:
			mat_amt = vals.get('unit_price') or 0.00
		qty = vals.get('qty')
		each_weight = vals.get('each_wgt')
		if vals.get('stock_type') == 'pattern':
			total_weight = qty * each_weight
			total_value = total_weight * mat_amt or 0.00
		else:
			total_weight = qty * each_weight
			total_value = vals.get('total_value')
		vals.update({
		
		'each_wgt': each_weight,
		'unit_price': mat_amt,
		'total_wgt': total_weight,
		'total_value': total_value
		
		})
		inward_rec = inward_obj.browse(cr, uid, vals.get('header_id'))
		inward_obj.write(cr, uid, vals.get('header_id'),{'total_value':inward_rec.total_value + total_value})
		return super(ch_stock_inward_details, self).create(cr, uid, vals, context=context)
		
		
	def write(self, cr, uid, ids, vals, context=None):
		pattern_name = False
		pattern_obj = self.pool.get('kg.pattern.master')
		moc_obj = self.pool.get('kg.moc.master')
		inward_obj = self.pool.get('kg.stock.inward')
		print "ids----------------------------",ids
		if type(ids) is list:
			entry_rec = self.browse(cr, uid, ids[0] )
		else:
			entry_rec = self.browse(cr, uid, ids )
		if entry_rec.stock_type == 'pattern':
			if vals.get('moc_id') == None or vals.get('moc_id') == False: 
				moc_rec = moc_obj.browse(cr, uid, entry_rec.moc_id.id )
				mat_amt = moc_rec.rate
			else:
				moc_rec = moc_obj.browse(cr, uid, vals.get('moc_id') )
				mat_amt = moc_rec.rate
		
		if entry_rec.stock_type == 'pump':
			if vals.get('unit_price'):
				mat_amt = vals.get('unit_price')
			else:
				mat_amt = entry_rec.unit_price

		if vals.get('qty') == None: 
			qty = entry_rec.qty
		else:
			qty = vals.get('qty')
			
		if vals.get('each_wgt') == None: 
			each_weight = entry_rec.each_wgt
		else:
			each_weight = vals.get('each_wgt')
			
		if entry_rec.stock_type == 'pattern':	
			total_weight = qty * each_weight
			total_value = total_weight * mat_amt
		else:
			total_weight = qty * each_weight
			total_value = vals.get('total_value')
		
		vals.update({
		
		'each_wgt': each_weight,
		'unit_price': mat_amt,
		'total_wgt': total_weight,
		'total_value': total_value
		
		})
		if type(ids) is list:
			cr.execute(''' select sum(total_value) from ch_stock_inward_details where header_id = %s and id != %s ''',[entry_rec.header_id.id, ids[0]])
			inward_total = cr.fetchone()
		else:
			cr.execute(''' select sum(total_value) from ch_stock_inward_details where header_id = %s and id != %s ''',[entry_rec.header_id.id, ids])
			inward_total = cr.fetchone()
		if inward_total[0] != None:
			total = inward_total[0]
		else:
			total = 0.00
		inward_obj.write(cr, uid, entry_rec.header_id.id,{'total_value':total + total_value})
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
              
        #~ (_check_values, 'System not allow to save with zero and less than zero qty .!!',['Quantity']),
        #(_check_line_duplicates, 'Inward Details are duplicate. Kindly check !! ', ['']),
        
        
       ]
	
ch_stock_inward_details()










