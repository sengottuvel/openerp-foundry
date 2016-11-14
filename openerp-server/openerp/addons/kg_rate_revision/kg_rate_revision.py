from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_rate_revision(osv.osv):

	_name = "kg.rate.revision"
	_description = "Rate Revision"
	
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
					as sam  """ %('kg_rate_revision'))
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
	
	_columns = {
	
	
			
		'name': fields.char('Revision No', size=128, readonly=True, select=True),
		'entry_date': fields.date('Date',required=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),		
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),	
		
		'line_ids':fields.one2many('ch.rate.revision.details', 'header_id', "Rate Revision Details"),
		'line_product_id': fields.related('line_ids','product_id', type='many2one', relation='product.product', string='Product'),
		
		'product_id': fields.many2many('kg.brandmoc.rate', 'm2m_brand_rate_revision_details', 'revision_id', 'brand_product_id','Product Name', domain="[('state','=','approved')]"),	
		'category_type': fields.selection([('purchase_item','Purchase Item'),('design_item','Design Item'),('both','Both')],'Category',required=True),
		'revision_mode': fields.selection([('all','All'),('individual','Individual')],'Revision Mode',required=True),
		'value_type': fields.selection([('fixed_amt','Fixed Amount'),('per','Percentage')],'Value Type'),
		'rate':fields.float('Value'),
		
		### Entry Info ###
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'ap_rej_date': fields.datetime('Approved/Reject Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Reject By', readonly=True),	
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.rate.revision', context=c),
		'active': True,
		'entry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'category_type': 'both',
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Name must be unique per Company !!'),
		
	]		
	
	
	def load_item(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.revision_mode == 'all':
			if rec.rate <= 0.00:
					raise osv.except_osv(_('Value'),
					_('System not allow to Load negative and zero values..!!'))		
		if rec.product_id == []:		
			if rec.category_type == 'purchase_item':
				brand_moc_rec = self.pool.get('kg.brandmoc.rate').search(cr,uid,([('category_type','=','purchase_item'),('state','=','approved')]))	
			if rec.category_type == 'design_item':
				brand_moc_rec = self.pool.get('kg.brandmoc.rate').search(cr,uid,([('category_type','=','design_item'),('state','=','approved')]))	
			if rec.category_type == 'both':
				brand_moc_rec = self.pool.get('kg.brandmoc.rate').search(cr,uid,([('state','=','approved')]))				
			cr.execute(""" delete from ch_rate_revision_details where header_id  = %s """ %(ids[0]))
			for item in brand_moc_rec:					
				brand_rec = self.pool.get('kg.brandmoc.rate').browse(cr,uid,item)
				brand_moc_line_rec = self.pool.get('ch.brandmoc.rate.details').search(cr,uid,([('header_id','=',item)]))				
				for line in brand_moc_line_rec:
					brand_moc_lines = self.pool.get('ch.brandmoc.rate.details').browse(cr,uid,line)
					if rec.revision_mode == 'all' :
						if rec.value_type == 'fixed_amt':
							design_rate_value = brand_moc_lines.rate + rec.rate
							revision_mode='all'
						if rec.value_type == 'per':
							design_per_value = ((brand_moc_lines.rate * rec.rate) / 100)
							design_rate_value = design_per_value + brand_moc_lines.rate
							revision_mode='all'
					else:
						design_rate_value = 0.00
						revision_mode='individual'
						
					line = self.pool.get('ch.rate.revision.details').create(cr,uid,{
						   'header_id':rec.id,
						   'moc_id':brand_moc_lines.moc_id.id,
						   'brand_line_ids':brand_moc_lines.id,
						   'product_id':brand_rec.product_id.id,
						   'brand_id':brand_moc_lines.brand_id.id,
						   'revision_mode':revision_mode,
						   'design_rate':brand_moc_lines.rate,
						   'new_design_rate':design_rate_value})	
			
		else:			
			product_ids = []
			for ele in rec.product_id:				
				product_ids.append(ele.product_id.id)	
			cr.execute(""" delete from ch_rate_revision_details where header_id  = %s """ %(ids[0]))						
			brand_moc_rec = self.pool.get('kg.brandmoc.rate').search(cr,uid,[('product_id','=',product_ids)])			
			for item in brand_moc_rec:					
				brand_rec = self.pool.get('kg.brandmoc.rate').browse(cr,uid,item)
				brand_moc_line_rec = self.pool.get('ch.brandmoc.rate.details').search(cr,uid,([('header_id','=',item)]))					
				for line in brand_moc_line_rec:
					brand_moc_lines = self.pool.get('ch.brandmoc.rate.details').browse(cr,uid,line)
					if rec.revision_mode == 'all' :
						if rec.value_type == 'fixed_amt':
							design_rate_value = brand_moc_lines.rate + rec.rate
							revision_mode='all'
						if rec.value_type == 'per':
							design_per_value = ((brand_moc_lines.rate * rec.rate) / 100)
							design_rate_value = design_per_value + brand_moc_lines.rate
							revision_mode='all'
					else:
						design_rate_value = 0.00
						revision_mode='individual'
						
					line = self.pool.get('ch.rate.revision.details').create(cr,uid,{
						   'header_id':rec.id,
						   'moc_id':brand_moc_lines.moc_id.id,
						   'brand_line_ids':brand_moc_lines.id,
						   'product_id':brand_rec.product_id.id,
						   'brand_id':brand_moc_lines.brand_id.id,
						   'revision_mode':revision_mode,
						   'design_rate':brand_moc_lines.rate,
						   'new_design_rate':design_rate_value})								
			
		return True


	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])	
		if entry.state == 'draft':	
			for line in entry.line_ids:
				if line.new_design_rate <= 0.00:
					raise osv.except_osv(_('New Design Rate'),
						_('System not allow to save negative and zero values..!!'))
			revision_name = ''	
			revision_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.rate.revision')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,revision_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(revision_seq_id[0],rec.code,entry.entry_date))
			revision_name = cr.fetchone();
			self.write(cr, uid, ids, {'name':revision_name[0],'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	def entry_approve(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'confirmed':	
			for line in entry.line_ids:					
				self.pool.get('ch.brandmoc.rate.details').write(cr,uid,line.brand_line_ids.id,{'rate':line.new_design_rate})
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
			if rec.state not in ('draft'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_rate_revision, self).write(cr, uid, ids, vals, context)	
	
	
	
kg_rate_revision()




class ch_rate_revision_details(osv.osv):
	
	_name = "ch.rate.revision.details"
	_description = "Brand MOC Rate Revision Details"
	
	_columns = {
		
		
		'header_id':fields.many2one('kg.rate.revision', 'Rate Revision Entry', required=True, ondelete='cascade'),	
		'product_id': fields.many2one('product.product','Product Name'),
		'brand_line_ids':fields.many2one('ch.brandmoc.rate.details', 'Brand Rate Line Ids', ondelete='cascade'),	
		'brand_id': fields.many2one('kg.brand.master','Brand'),			
		'moc_id':fields.many2one('kg.moc.master','MOC'),	
		'design_rate':fields.float('Current Design Rate(Rs)'),
		'revision_mode': fields.selection([('all','All'),('individual','Individual')],'Revision Mode'),
		'new_design_rate':fields.float('New Design Rate(Rs)'),		
		'remarks':fields.text('Remarks'),		
	}
	
		
	   
ch_rate_revision_details()
