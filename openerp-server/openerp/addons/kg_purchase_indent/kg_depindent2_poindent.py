import math
import re
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import kg_depindent
from itertools import groupby
import openerp.addons.decimal_precision as dp

class kg_depindent2_poindent(osv.osv):
	
	_name = "purchase.requisition"
	_inherit = "purchase.requisition"

	_columns = {
	
	'kg_depindent_lines':fields.many2many('kg.depindent.line','kg_depindent_pi_line' , 'pi_id', 'depindent_line_id', 'DepIndent Lines',
			domain="[('indent_id.state','=','approved'), '&', ('pending_qty','>','0'), '&', ('issue_pending_qty','>','0'), '&', ('line_state','!=', 'process')]", 
			readonly=True, states={'draft': [('readonly', False)]}),
			
		}

	def update_pil(self,cr,uid,ids,product_id,context=False):
		print "callled update_pil from KG"
		obj =  self.browse(cr,uid,ids[0])
		if obj.state in ('draft','in_progress'):
			"""
			Purchase indent line should be created from dep indent while click on update to purchase indent button
			"""
			depindent_line_obj = self.pool.get('kg.depindent.line')
			pi_line_obj = self.pool.get('purchase.requisition.line')
			prod_obj = self.pool.get('product.product')
			prod_rec=prod_obj.browse(cr,uid,ids)
			user_obj = self.pool.get('res.users')
			line_ids = []			   
			res={}
			line_ids = []
			res['line_ids'] = []
			res['pi_flag'] = True
			
			user_rec = obj.user_id
			user = user_rec.id
			if obj.line_ids:
				for line in obj.line_ids:
					di_line = line.depindent_line_id
					di_line.write({'line_state' : 'noprocess'})			
				line_ids = map(lambda x:x.id,obj.line_ids)
				del_sql = """ delete from purchase_requisition_line where requisition_id=%s """ %(ids[0])
				cr.execute(del_sql)
			if obj.kg_depindent_lines:
				depindent_line_ids = map(lambda x:x.id,obj.kg_depindent_lines)
				depindent_line_browse = depindent_line_obj.browse(cr,uid,depindent_line_ids)
				depindent_line_browse = sorted(depindent_line_browse, key=lambda k: k.product_id.id)
				groups = []
				for key, group in groupby(depindent_line_browse, lambda x: x.product_id.id):
					for key,group in groupby(group,lambda x: x.brand_id.id):
						groups.append(map(lambda r:r,group))
				for key,group in enumerate(groups):
					qty = sum(map(lambda x:float(x.po_qty),group))
					pending_qty = sum(map(lambda x:float(x.pending_qty),group)) #TODO: qty
					depindent_line_ids = map(lambda x:x.id,group)
					if len(depindent_line_ids) > 1:
						flag = True
					else:
						flag = False
					indent = group[0].indent_id
					dep = indent.dep_name.id
					prod_browse = group[0].product_id
					brand_id = group[0].brand_id.id			
					uom = group[0].uom.id or False
					po_uom = prod_browse.uom_po_id.id or False
					depindent_id= group[0].id
					po_qty = group[0].po_qty
					#pending_qty = group[0].pending_qty
					remark = group[0].note
					cur_qty=prod_browse.qty_available
					pending_qty = pending_qty / prod_browse.po_uom_coeff
					stock_sql = """ select sum(pending_qty) from stock_production_lot where product_id = %s group by product_id """%(prod_browse.id)
					cr.execute(stock_sql)		
					stock_data = cr.dictfetchall()
					stock_qty = 0.00
					if stock_data:
						stock_qty = stock_data[0]
						stock_qty = stock_qty.values()[0]
					else:
						stock_qty = 0.00	
					
					vals = {
					
					'product_id': prod_browse.id,
					'brand_id': brand_id,
					'product_uom_id': po_uom,
					'product_qty': qty,
					'current_qty': cur_qty,
					'pending_qty': qty,
					'dep_indent_qty': pending_qty,
					'depindent_line_id': depindent_id,
					'po_uom_qty': qty,
					'default_uom_id': uom,
					'group_flag': flag,
					'line_flag': False,
					'note': remark,
					'dep_id': dep,
					'user_id' : user,
					'stock_qty': stock_qty,
					'moc_id': group[0].moc_id.id,
					'moc_id_temp': group[0].moc_id_temp.id,
					'requisition_id': obj.id,
					'indent_type': obj.indent_type,
					
					}
					print "vals :", vals
					if pending_qty == 0:
						depindent_line_obj.write(cr,uid,depindent_id,{'line_state' : 'process'})
					if ids:
						#~ self.write(cr,uid,ids[0],{'line_ids':[(0,0,vals)]})
						line_id = self.pool.get('purchase.requisition.line').create(cr,uid,vals)
						for wo in group[0].line_id:
							self.pool.get('ch.purchase.indent.wo').create(cr,uid,{'header_id':line_id,'wo_id':wo.wo_id,'w_order_id':wo.w_order_id.id,'w_order_line_id':wo.w_order_line_id.id,'qty':wo.qty})
							
				"""	
				if ids:
					if obj.line_ids:
						line_ids = map(lambda x:x.id,obj.line_ids)
						for line_id in line_ids:
							self.write(cr,uid,ids,{'line_ids':[]})
							"""
			self.write(cr,uid,ids,res)			
		return True		
		
	def update_product_group(self,cr,uid,ids,line,context=None):		
		pi_rec = self.browse(cr, uid, ids[0])
		line_obj = self.pool.get('purchase.requisition.line')
		dep_line_obj = self.pool.get('kg.depindent.line')
		product_obj = self.pool.get('product.product')
		cr.execute(""" select depindent_line_id from kg_depindent_pi_line where pi_id = %s """ %(str(ids[0])))
		data = cr.dictfetchall()
		val = [d['depindent_line_id'] for d in data if 'depindent_line_id' in d] 
		product_id = line.product_id.id
		product_record = product_obj.browse(cr, uid, product_id)
		list_line = dep_line_obj.search(cr,uid,[('id', 'in', val), ('product_id', '=', product_id)],context=context)
		depindent_line_id=line.depindent_line_id
		pi_qty = line.product_qty
		
		for i in list_line:
			bro_record = dep_line_obj.browse(cr, uid,i)
			orig_depindent_qty = bro_record.pending_qty
			po_uom_qty = bro_record.po_qty
			pi_used_qty = pi_qty
			uom = bro_record.uom.id
			po_uom = bro_record.po_uom.id
			if uom != po_uom:
				if pi_used_qty <= po_uom_qty:
					pending_po_depindent_qty =  po_uom_qty - pi_used_qty
					pending_stock_depindent_qty = orig_depindent_qty - (pi_used_qty * product_record.po_uom_coeff)
					sql = """ update kg_depindent_line set po_qty=%s, pending_qty=%s where id = %s"""%(pending_po_depindent_qty,
						pending_stock_depindent_qty,bro_record.id)
					cr.execute(sql)
					#dep_line_obj.write(cr,uid, bro_record.id, {'line_state' : 'noprocess'})
					break
				else:
					remain_qty = pi_used_qty - po_uom_qty
					pi_qty = remain_qty
					pending_po_depindent_qty =  0.0
					pending_stock_depindent_qty = 0.0
					sql = """ update kg_depindent_line set po_qty=%s, pending_qty=%s where id = %s"""%(pending_po_depindent_qty,
						pending_stock_depindent_qty,bro_record.id)
					cr.execute(sql)
					#dep_line_obj.write(cr,uid, bro_record.id, {'line_state' : 'noprocess'})
					if remain_qty < 0:
						break			
			else:
				if pi_used_qty <= po_uom_qty:
					pending_po_depindent_qty =  po_uom_qty - pi_used_qty
					pending_stock_depindent_qty = po_uom_qty - pi_used_qty 
					sql = """ update kg_depindent_line set po_qty=%s, pending_qty=%s where id = %s"""%(pending_po_depindent_qty,
						pending_stock_depindent_qty,bro_record.id)
					cr.execute(sql)
					#dep_line_obj.write(cr,uid, bro_record.id, {'line_state' : 'noprocess'})
					break
				else:
					remain_qty = pi_used_qty - po_uom_qty
					pi_qty = remain_qty
					pending_po_depindent_qty =  0.0
					pending_stock_depindent_qty = 0.0
					sql = """ update kg_depindent_line set po_qty=%s, pending_qty=%s where id = %s"""%(pending_po_depindent_qty,
						pending_stock_depindent_qty,bro_record.id)
					cr.execute(sql)
					#dep_line_obj.write(cr,uid, bro_record.id, {'line_state' : 'noprocess'})
					if remain_qty < 0:
						break		
		return True			
		
kg_depindent2_poindent()
