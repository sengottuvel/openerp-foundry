from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_machine_shop(osv.osv):

	_name = "kg.machine.shop"
	_description = "SAM MOC Master"
	_rec_name = 'code'
	
	
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
					as sam  """ %('kg_machine_shop'))
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
			
		'name': fields.char('Name', size=128, required=True, select=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'code': fields.char('Code', size=128, required=True),		
		'uom_id': fields.many2one('product.uom', 'Unit of Measure', domain="[('dummy_state','=','approved'), ('active','=','t')]"),
		'hsn_no': fields.many2one('kg.hsn.master', 'HSN No.', domain="[('state','=','approved')]", required=True),
		'active': fields.boolean('Active'),	
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'line_ids':fields.one2many('ch.ms.raw.material', 'header_id', "Raw Materials"),
		'line_ids_a':fields.one2many('ch.machine.mocwise', 'header_id', "Machine Shop MOC Wise"),
		
		'csd_code': fields.char('CSD Code No.', size=128),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		'type': fields.selection([('ms','MS Item'),('bot','BOT')],'Type'),
		'od': fields.float('OD'),
		'length': fields.float('Length'),
		'breadth': fields.float('Breadth'),
		'thickness': fields.float('Thickness'),
		'weight': fields.float('Weight'),
		'painting_cost': fields.float('Painting Cost'),	
		
		'dynamic_length': fields.boolean('Dynamic Length'),			
		'is_bearing': fields.boolean('Is Bearing'),			
		'flag_heat_no': fields.boolean('Heat No. Required'),			
		'length_type': fields.selection([('single_column_pipe','Single Column Pipe'),('single_shaft','Single Shaft'),('delivery_pipe','Delivery Pipe'),('drive_column_pipe','Drive Column Pipe'),('pump_column_pipe','Pump Column Pipe'),('pump_shaft','Pump Shaft'),('drive_shaft','Drive Shaft')],'Length Type'),		
		
		'moc_const_type': fields.many2many('kg.construction.type', 'm2m_moc_construction_details', 'moc_const_id', 'const_type_id','Type', domain="[('active','=','t')]"),
		'moc_id': fields.many2one('kg.moc.master','Default MOC', domain="[('active','=','t')]" ),	
		
		
		'ms_type': fields.selection([('new_item','New Item'),('copy_item','Copy Item')],'Type', required=True),	
		'source_item': fields.many2one('kg.machine.shop', 'Source Item',domain="[('type','=',type),('active','=','t')]"),
		'copy_flag':fields.boolean('Copy Flag'),
		'list_moc_flag':fields.boolean('List MOC Flag'),
		
		### Entry Info ###
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
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.machine.shop', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),	
		'modify': 'no',
		'copy_flag' : False,
		'flag_heat_no' : False,
		'ms_type':'new_item', 
		
	}
	
	_sql_constraints = [	
		
		('code', 'unique(code)', 'Code must be unique per Company !!'),
	]	
	
	def _Validation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])				
		if flds.name:
			name_char = ''.join( c for c in flds.name if  c in '!@#$%^~*{}?+=' )
			if name_char:
				return False	
		if flds.code:
			code_char = ''.join( c for c in flds.code if  c in '!@#$%^~*{}?+=' )
			if code_char:
				return False
		if flds.csd_code:
			csd_code_char = ''.join( c for c in flds.csd_code if  c in '!@#$%^~*{}?+=' )
			if csd_code_char:
				return False				
		return True	
			
	def _code_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.code:
			division_code = rec.code
			code=division_code.upper()			
			cr.execute(""" select upper(code) from kg_machine_shop where upper(code)  = '%s' """ %(code))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res	
		
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True
		
	def list_moc(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.moc_const_type:				
			moc_type_ids = []
			for moc_type in rec.moc_const_type:	
				moc_type_ids.append(moc_type.id)			
			moc_const_obj = self.pool.get('kg.moc.construction').search(cr,uid,([('constuction_type_id','in',moc_type_ids)]))
		else:
			moc_const_obj = self.pool.get('kg.moc.construction').search(cr,uid,([('active','=',True)]))		
		#~ cr.execute(""" delete from ch_machine_mocwise where header_id  = %s """ %(ids[0]))		
		for item in moc_const_obj:			
			moc_const_rec = self.pool.get('kg.moc.construction').browse(cr,uid,item)
			sql_check = """ select code from ch_machine_mocwise where code=%s and header_id  = %s """ %(moc_const_rec.id,ids[0])
			cr.execute(sql_check)
			data = cr.dictfetchall()
			if data == []:					
				line = self.pool.get('ch.machine.mocwise').create(cr,uid,{
					   'header_id':rec.id,
					   'moc_id':rec.moc_id.id,
					   'code':moc_const_rec.id,
							})	
			else:
				pass
		self.write(cr, uid, ids, {'list_moc_flag': True})			
		return True	
		
		
	def copy_item(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		ms_raw_line_obj = self.pool.get('ch.ms.raw.material')
		machine_mocwise_line_obj = self.pool.get('ch.machine.mocwise')		
		cr.execute(""" delete from ch_ms_raw_material where header_id  = %s """ %(ids[0]))
		cr.execute(""" delete from ch_machine_mocwise where header_id  = %s """ %(ids[0]))			
		for ms_raw_line_item in rec.source_item.line_ids:			
			vals = {
				'header_id' : ids[0]
				}			
			copy_rec = ms_raw_line_obj.copy(cr, uid, ms_raw_line_item.id,vals, context) 
			
		for machine_mocwise_line_item in rec.source_item.line_ids_a:			
			vals = {
				'header_id' : ids[0]
				}			
			copy_rec = machine_mocwise_line_obj.copy(cr, uid, machine_mocwise_line_item.id,vals, context) 		
		
		self.write(cr, uid, ids[0], {'copy_flag': True,'csd_code':rec.source_item.csd_code,
									'od':rec.source_item.od,
									'breadth':rec.source_item.breadth,
									'length':rec.source_item.length,
									'thickness':rec.source_item.thickness,
									'weight':rec.source_item.weight,
									'notes':rec.source_item.notes,
									'moc_id':rec.source_item.moc_id.id,											
									'moc_const_type':[(6, 0, [x.id for x in rec.source_item.moc_const_type])], })		
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':	
			if rec.list_moc_flag == False:
				raise osv.except_osv(_('List MOC Construction !!'),
					_('Click the List MOC Construction Button !!'))
			for item in rec.line_ids:
				prod = self.pool.get('product.product').browse(cr, uid, item.product_id.id, context=context)	
				print"item.uom.id",item.uom.id				
				print"prod.uom_po_id.id",prod.uom_po_id.id	
				qty_value = 0.00			
				weight = 0.00			
				if item.uom.id != prod.uom_id.id:
					if item.uom.id  != prod.uom_po_id.id:				 			
						raise osv.except_osv(
							_('UOM Mismatching Error !'),
							_('You choosed wrong UOM and you can choose either %s or %s for %s !!!') % (prod.uom_id.name,prod.uom_po_id.name,prod.name))
									
				if item.uom_conversation_factor == 'one_dimension':	
					if prod.uom_id.id == prod.uom_po_id.id:
						qty_value = item.temp_qty
						weight = 0.00
					if item.length == 0.00:
						qty_value = item.temp_qty
						weight = 0.00
					else:				
						qty_value = item.length * item.temp_qty			
						weight = qty_value * prod.po_uom_in_kgs
				if item.uom_conversation_factor == 'two_dimension':
					if item.length == 0.00 or item.breadth == 0.00:
						qty_value = item.temp_qty
						weight = 0.00
					else:
						qty_value = item.temp_qty
						weight = 0.00
					qty_value = item.length * item.breadth * item.temp_qty				
					weight = qty_value * prod.po_uom_in_kgs	
					
				self.pool.get('ch.ms.raw.material').write(cr,uid,item.id,{'qty':qty_value,'weight':weight})			
			
			if rec.ms_type == 'copy_item':
				
				### Check Duplicates Raw Materials Items start ###
				
				cr.execute('''select 

						raw_line.product_id,
						raw_line.uom,
						raw_line.qty

						from ch_ms_raw_material raw_line 

						left join kg_machine_shop header on header.id  = raw_line.header_id

						where header.ms_type = 'copy_item' and header.id = %s''',[rec.id])
				
				source_raw_ids = cr.fetchall()		
				source_raw_len = len(source_raw_ids)	
				
				cr.execute('''select 

						raw_line.product_id,
						raw_line.uom,
						raw_line.qty

						from ch_ms_raw_material raw_line 

						where raw_line.header_id  = %s''',[rec.source_item.id])
				
				source_old_raw_ids = cr.fetchall()
				
				source_old_raw_len = len(source_old_raw_ids)
								
				cr.execute('''select 

						raw_line.product_id,
						raw_line.uom,
						raw_line.qty

						from ch_ms_raw_material raw_line 

						left join kg_machine_shop header on header.id  = raw_line.header_id

						where header.ms_type = 'copy_item' and header.id = %s

						INTERSECT

						select 

						raw_line.product_id,
						raw_line.uom,
						raw_line.qty

						from ch_ms_raw_material raw_line 

						where raw_line.header_id  = %s ''',[rec.id,rec.source_item.id])
				repeat_ids = cr.fetchall()			
				new_raw_len = len(repeat_ids)			
				### Check Duplicates Raw Materials Items end.... ###
				
				
				### Check Duplicates MOC Construction and Rate Details Items start ###
				
				cr.execute('''select 

						machine_line.moc_id,
						machine_line.code,
						machine_line.remarks

						from ch_machine_mocwise machine_line 

						left join kg_machine_shop header on header.id  = machine_line.header_id

						where header.ms_type = 'copy_item' and header.id = %s''',[rec.id])
				
				source_machine_ids = cr.fetchall()		
				source_machine_len = len(source_machine_ids)	
				
				cr.execute('''select 

						machine_line.moc_id,
						machine_line.code,
						machine_line.remarks

						from ch_machine_mocwise machine_line 

						where machine_line.header_id  = %s''',[rec.source_item.id])
				
				source_old_machine_ids = cr.fetchall()
				
				source_old_machine_len = len(source_old_machine_ids)
								
				cr.execute('''select 

						machine_line.moc_id,
						machine_line.code,
						machine_line.remarks

						from ch_machine_mocwise machine_line 

						left join kg_machine_shop header on header.id  = machine_line.header_id

						where header.ms_type = 'copy_item' and header.id = %s

						INTERSECT

						select 

						machine_line.moc_id,
						machine_line.code,
						machine_line.remarks

						from ch_machine_mocwise machine_line 

						where machine_line.header_id  = %s ''',[rec.id,rec.source_item.id])
				repeat_ids = cr.fetchall()			
				new_machine_len = len(repeat_ids)			
				### Check Duplicates MOC Construction and Rate Details Items end.... ###
				
				
				raw_dup = machine_dup = ''		
				if new_raw_len == source_raw_len == source_old_raw_len:			
					raw_dup = 'yes'		
				if new_machine_len == source_machine_len == source_old_machine_len:			
					machine_dup = 'yes'			
				
				
				if raw_dup == 'yes' and machine_dup == 'yes':			
					raise osv.except_osv(_('Warning!'),
									_('Same Details are already exist !!'))
				
				
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
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
		return super(kg_machine_shop, self).write(cr, uid, ids, vals, context)
		
	
	_constraints = [
		(_Validation, 'Special Character Not Allowed !!!', ['Check']),
		(_code_validate, 'MOC code must be unique !!', ['code']),	
	]
	
kg_machine_shop()



class ch_ms_raw_material(osv.osv):
	
	_name = "ch.ms.raw.material"
	_description = "MS Raw Materials Master"
	
	_columns = {
			
		'header_id':fields.many2one('kg.machine.shop', 'MS Entry', required=True, ondelete='cascade'),	
		'product_id': fields.many2one('product.product','Raw Material', required=True, domain="[('product_type','in',['ms','bot','consu','coupling'])]"),			
		'uom':fields.many2one('product.uom','UOM',size=128 ,required=True),
		'od': fields.float('OD'),
		'length': fields.float('Length'),
		'breadth': fields.float('Breadth'),
		'thickness': fields.float('Thickness'),
		'weight': fields.float('Weight' ,digits=(16,5)),
		'uom_conversation_factor': fields.selection([('one_dimension','One Dimension'),('two_dimension','Two Dimension')],'UOM Conversation Factor'),		
		'temp_qty':fields.float('Qty'),
		'qty':fields.float('Testing Qty',readonly=True),
		'remarks':fields.text('Remarks'),		
	}
	
	_defaults = {
	
		
		'length': 1.00,
	
		
	}
	
	def onchange_product_uom(self, cr, uid, ids, product_id, uom_id,  context=None):		
		prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)		
		if uom_id != prod.uom_id.id:
			if uom_id != prod.uom_po_id.id:				 			
				raise osv.except_osv(
					_('UOM Mismatching Error !'),
					_('You choosed wrong UOM and you can choose either %s or %s for %s !!!') % (prod.uom_id.name,prod.uom_po_id.name,prod.name))	

		return True	
	
	def onchange_uom(self, cr, uid, ids, product_id, context=None):
		
		value = {'uom': '','uom_conversation_factor':''}
		if product_id:
			uom_rec = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			value = {'uom_conversation_factor':uom_rec.uom_conversation_factor}
			
		return {'value': value}
		
	def onchange_weight(self, cr, uid, ids, uom_conversation_factor,length,breadth,temp_qty,product_id, context=None):		
		value = {'qty': '','weight': '',}
		prod_rec = self.pool.get('product.product').browse(cr,uid,product_id)
		qty_value = 0.00
		weight=0.00
		if uom_conversation_factor == 'one_dimension':	
			if prod_rec.uom_id.id == prod_rec.uom_po_id.id:
				qty_value = length * temp_qty
				weight = 0.00
			if length == 0.00:
				qty_value = temp_qty
			else:				
				qty_value = length * temp_qty			
				weight = qty_value * prod_rec.po_uom_in_kgs
			
		if uom_conversation_factor == 'two_dimension':
			qty_value = length * breadth * temp_qty				
			weight = qty_value * prod_rec.po_uom_in_kgs		
		value = {'qty': qty_value,'weight':weight}			
		return {'value': value}
		
	
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		cr.execute(""" select product_id from ch_ms_raw_material where product_id  = '%s' and length = '%s' and breadth = '%s' and header_id = '%s' """ %(entry.product_id.id,entry.length,entry.breadth,entry.header_id.id))
		data = cr.dictfetchall()			
		if len(data) > 1:		
			return False
		return True	
		
	def _check_one_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		prod_rec = self.pool.get('product.product').browse(cr,uid,entry.product_id.id)
		if entry.uom_conversation_factor =='one_dimension':
			if prod_rec.uom_id.id == prod_rec.uom_po_id.id:
				if entry.qty == 0:				
					return False
				return True	
			else:
				if entry.qty == 0 or entry.length == 0:				
					return False				
				return True				
		return True
		
	def _check_two_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.uom_conversation_factor =='two_dimension':
			if entry.length == 0 or entry.qty == 0 or entry.breadth == 0:				
				return False
			return True
		return True
		
	def _check_uom_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		prod = self.pool.get('product.product').browse(cr, uid, entry.product_id.id)		
		print"item.uom.id",entry.uom.id				
		print"prod.uom_po_id.id",prod.uom_po_id.id				
		if entry.uom.id != prod.uom_id.id:
			if entry.uom.id  != prod.uom_po_id.id:
				return False			
		return True	
		
	_constraints = [		
			  
		(_check_one_values, 'Check the zero values not allowed..!!',['Qty or Length']),	
		(_check_two_values, 'Check the zero values not allowed..!!',['Breadth or Length or Qty']),
		(_check_values, 'Please Check the same Raw Material not allowed..!!',['Raw Material']),	
		(_check_uom_values, 'UOM Mismatching Error, You choosed wrong UOM !!!',['UOM']),	
		
	   ]
	
ch_ms_raw_material()


class ch_machine_mocwise(osv.osv):
	
	_name = "ch.machine.mocwise"
	_description = "Machine Shop MOC Wise"
	
	_columns = {
			
		'header_id':fields.many2one('kg.machine.shop', 'Pattern Entry', required=True, ondelete='cascade'),	
		'moc_id': fields.many2one('kg.moc.master','MOC', required=True,domain="[('active','=','t')]" ),	
		'code':fields.many2one('kg.moc.construction','MOC Construction Code'),			
		'remarks':fields.text('Remarks'),
		
	}
	
	
	
		
ch_machine_mocwise()

