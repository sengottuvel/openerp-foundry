import math
import re
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import openerp.addons.decimal_precision as dp
dt_time = datetime.now()

class kg_physical_stock(osv.osv):

	_name = "kg.physical.stock"
	_description = "Physical Stock Entry"
	_order = "date desc"
	
	_columns = {
		
		## Basic Info
		
		'name': fields.char('Reference No', size=64, readonly=True),
		'date': fields.date('Stock Entry Date',readonly=True,states={'draft':[('readonly',False)]}),
		'state': fields.selection([('load','Load'),('draft', 'Draft'),('confirm','Waiting For Approval'),('approved','Approved'),('cancel','Cancel')], 'Status', track_visibility='onchange',states={'draft':[('readonly',False)]}),
		'remark': fields.text('Remarks',states={'cancel':[('readonly',True)]}),
		
		## Module Requirement Info
		
		'product_id': fields.many2many('product.product', 'physical_stock_product_ids', 'kg_stock_id', 'product_id', 'Product Name',domain=[('state', 'in', ('approved','confirm')),('type', '!=', 'service'),('sale_ok', '=', True)]),
		'load': fields.boolean('Load'),
		'stock_type': fields.selection([('main','Main'),('counter', 'Counter')], 'Location Type',readonly=True),
		'location_id' : fields.many2one('stock.location', 'Store Name', readonly=False,select=True, domain="[('location_type','=','main')]"),
		
		## Child Tables Declaration
		
		'stock_line': fields.one2many('kg.physical.stock.line', 'stock_pid','Physical Stock Lines',readonly=True),
		
		## Entry Info
		
		'active': fields.boolean('Active'),
		'company_id':fields.many2one('res.company','Company',readonly=True),
		'user_id' : fields.many2one('res.users', 'Created By', readonly=True),
		'creation_date':fields.datetime('Created Date',readonly=True),
		'confirmed_by' : fields.many2one('res.users', 'Confirmed By', readonly=False,select=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'approved_by' : fields.many2one('res.users', 'Approved By', readonly=False,select=True),
		'approve_date': fields.datetime('Approved Date', readonly=True),
	   	'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'reject_date': fields.datetime('Rejected Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		
	}
	
	_sql_constraints = [('code_uniq','unique(name)', 'Indent number must be unique!')]

	_defaults = {
		
		'state' 		: 'load',
		'active' 		: 'True',
		'load' 			: True,
		'date' 			: lambda * a: time.strftime('%Y-%m-%d'),
		'stock_type'	: 'main',
		'user_id'		: lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
		'creation_date' : lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'company_id' 	: lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.general.grn', context=c),

	}
	
	def load_stock(self, cr, uid, ids = 0,context=None):
		rec  = self.browse(cr,uid,ids[0])
		loc_id = rec.location_id.id
		my_plist = []
		if rec.product_id:
			psql1 = """select product_id from physical_stock_product_ids where kg_stock_id = %s"""%(ids[0])
			cr.execute(psql1)
			pdata = cr.dictfetchall()
			if pdata:
				for items in pdata:
					my_plist.append(items['product_id'])
		else:
			pass
		sql1 = """select id from kg_physical_stock where state='load' and id != %s"""%(ids[0])
		cr.execute(sql1)
		data1 = cr.dictfetchall()
		if data1:
			sql = """delete from kg_physical_stock where state='load' and id != %s"""%(ids[0])
			cr.execute(sql)		
		self.write(cr,uid,ids,{
			'stock_type':'main',
			'state':'draft',
			})
		
		##### Added For Testing Starts Here 
		where_sql = []
		major = []
		product=[]
		pro_type=[]
		if rec.location_id.id:
			where_sql.append("a.location_dest_id = %s" %(rec.location_id.id))
		if where_sql:
			where_sql = ' and '+' or '.join(where_sql)
		else:
			where_sql=''
		major=''
		
		if rec.product_id:
			for ids2 in rec.product_id:
				product.append("a.product_id = %s"%(ids2))	
		if product:
			product = ' and ('+' or '.join(product)
			product = product +')'
		else:
			product=''
		
		pro_type=''
		location_rec = self.pool.get('stock.location').browse(cr,uid,rec.location_id.id)
		if location_rec.location_type == 'main':
			lo_type = 'in'
		else:
			lo_type = 'out'
		
		cr.execute('''
			   select sum(a.product_qty) -
				(select (case when sum(b.product_qty) is not null then sum(b.product_qty) else 0 end) from stock_move b where b.move_type = 'out'
				and b.product_id = a.product_id and b.brand_id = a.brand_id and a.moc_id = b.moc_id and b.date <= %s and b.location_id = %s) as stock_uom_close,
				(case when a.uom_conversation_factor = 'two_dimension' then
				(sum(a.product_qty) -
				(select (case when sum(b.product_qty) is not null then sum(b.product_qty) else 0 end) from stock_move b where b.move_type = 'out'
				and b.product_id = a.product_id and b.brand_id = a.brand_id and a.moc_id = b.moc_id and b.date <= %s and b.location_id = %s)) / prod.po_uom_in_kgs
				else
				(sum(a.product_qty) -
				(select (case when sum(b.product_qty) is not null then sum(b.product_qty) else 0 end) from stock_move b where b.move_type = 'out'
				and b.product_id = a.product_id and b.brand_id = a.brand_id and a.moc_id = b.moc_id and b.date <= %s and b.location_id = %s)) / prod.po_uom_coeff
				end) as po_uom_close,
				a.product_id as product_id,
				prod.name_template as product,
				a.brand_id as brand_id,
				a.moc_id as moc_id,
				brand.name as brand,
				moc.name as moc,
				a.stock_uom as stock_uom,
				a.product_uom as product_uom,
				suom.name as suom,
				puom.name as puom,
				prod.po_uom_in_kgs as po_uom_in_kgs,
				a.uom_conversation_factor as uom_conversation_factor,
				prod.po_uom_coeff as po_uom_coeff
				
				from stock_move a
				
				left join kg_brand_master brand on(brand.id=a.brand_id)
				left join kg_moc_master moc on(moc.id=a.moc_id)
				left join product_product prod on(prod.id=a.product_id)
				left join product_uom suom on(suom.id=a.stock_uom)
				left join product_uom puom on(puom.id=a.product_uom)
				left JOIN product_template pt ON (pt.id=a.product_id)
				left join product_category pc on(pc.id=pt.categ_id)
				
			   where a.move_type = 'in' and a.date <= %s and a.state=%s and a.location_dest_id = %s'''+ major + product + pro_type +'''
			   group by 3,4,5,6,7,8,9,10,11,12,13,14,15 order by prod.name_template ''',(rec.date,rec.location_id.id,rec.date,rec.location_id.id,rec.date,rec.location_id.id,rec.date,'done',rec.location_id.id))
		
		data=cr.dictfetchall()
		data_new = []
		gr_total=0.0
		s_no = 0
		if data:
			for item in data:
				if item['product_id']:
					proc_rec = self.pool.get('product.product').browse(cr,uid,item['product_id'])
					item['suom'] = proc_rec.uom_id.name
					item['puom'] = proc_rec.uom_po_id.name
				if item['stock_uom_close'] > 0:
					s_no = s_no + 1
					item['s_no'] = s_no
					cr.execute('''
							   SELECT
								line.price_unit as price,
								line.price_type as price_type,
								line.length as length,
								line.breadth as breadth,
								line.product_qty as product_qty,
								line.product_uom as product_uom
								FROM purchase_order_line line
								JOIN purchase_order po ON (po.id=line.order_id)
								where po.state='approved' and line.product_id = %s and line.brand_id = %s
								and line.moc_id = %s  and po.approved_date::date <= %s
								order by po.date_order desc limit 1''',(item['product_id'],item['brand_id'],item['moc_id'],rec.date))
					
					lot_data = cr.dictfetchall()
					if lot_data:
						closing_value = lot_data[0]['price']
						item['po_price'] = lot_data[0]['price']
						print"item['uom_conversation_factor']",item['uom_conversation_factor']
						if item['uom_conversation_factor'] == 'two_dimension':
							if lot_data[0]['price_type'] == 'po_uom':
								if lot_data[0]['product_uom'] == item['product_uom']:
									item['closing_value'] = item['stock_uom_close'] * ((lot_data[0]['price'] * lot_data[0]['product_qty'])/(lot_data[0]['length'] or 1 * lot_data[0]['breadth'] or 1 * lot_data[0]['product_qty'] or 1 * item['po_uom_in_kgs'] or 1))
								else:
									item['closing_value'] = item['stock_uom_close'] * lot_data[0]['price']
							elif lot_data[0]['price_type'] == 'per_kg':
								item['closing_value'] = item['stock_uom_close'] * lot_data[0]['price']
						elif item['uom_conversation_factor'] == 'one_dimension':
							if lot_data[0]['price_type'] == 'po_uom':
								if lot_data[0]['product_uom'] == item['product_uom']:
									item['closing_value'] = item['stock_uom_close'] * ((lot_data[0]['price'] * lot_data[0]['product_qty'])/(lot_data[0]['product_qty'] * item['po_uom_coeff']))
								else:
									item['closing_value'] = item['stock_uom_close'] * lot_data[0]['price']
							elif lot_data[0]['price_type'] == 'per_kg':
								item['closing_value'] = item['stock_uom_close'] * lot_data[0]['price']
						else:
							item['closing_value'] = 0
					else:
						item['po_price'] = 0
						item['closing_value'] = 0
					gr_total += item['closing_value']
					item['grand_total'] = int(gr_total)
					
					data_new.append(item)
		
				else:
					pass
		print "*******************************************************************************",data_new
		sno = 1
		for item in data_new:
			line_vals = {
			'sno':sno,
			'product_id':item['product_id'],
			'brand':item['brand'] or '',
			'brand_id':item['brand_id'] or False,			
			'uom':item['product_uom'],
			'moc':item['moc'] or '',
			'moc_id':item['moc_id'] or False,		
			'qty':item['stock_uom_close'],
			'physical_stock':item['stock_uom_close'],
			'po_rate':item['po_price'],
			'sale_rate':item['po_price'],			
			'stock_pid':rec.id,
			'stock_type':rec.stock_type,
			'entry_mode':'auto',
			'location_id':rec.location_id.id,			
			
			}
			sno = sno+1
			if line_vals:
				common_line = self.pool.get('kg.physical.stock.line').create(cr,uid,line_vals,context=None)		
		#~ return data_new		
		
		##### Added For Testing Ends Here 
		
		#~ sql1="""select 
			#~ pd_id as in_pro_id,
			#~ (1/(select coalesce(po_uom_coeff,0.00) from product_product where id = pd_id)) as pd_coeff,
			#~ COALESCE(pp.sales_price,0.00) as sale_rate,
			#~ case when pd_id is not null then 
			#~ (select po_ref from ( 
			#~ SELECT price||'$'||price_type as po_ref
			#~ from (
			#~ SELECT
						#~ line.price_unit as price,
						#~ line.price_type as price_type,
						#~ case when line.length > 0 then line.length else 1 end as length,
						#~ case when line.breadth > 0 then line.breadth else 1 end as breadth,
						#~ line.product_qty as product_qty,
						#~ line.product_uom as product_uom
						#~ FROM purchase_order_line line
						#~ JOIN purchase_order po ON (po.id=line.order_id)
						#~ where po.state='approved' and line.product_id =  pd_id and line.brand_id = sm_brand_id
						#~ and line.moc_id = sm_moc_id  and po.approved_date::date <= current_date
						#~ order by po.date_order desc limit 1
			#~ ) as sub_one
			#~ ) as sub_two) else '-' end as po_rate,
			#~ --case when pd_id is not null then 
			#~ --0.00 end as po_rate,
			#~ brand.name as brand,
			#~ sm_moc_name as moc,
			#~ sm_moc_id,
			#~ sm_brand_id,
			#~ uom.id as uom,'bakery'::text as purpose,pp.name_template as product,
			#~ COALESCE((COALESCE(op_qty,0.00)+COALESCE(in_qty,0.00)),0.00)-COALESCE(out_qty,0.00) as in_qty
			#~ from 
			#~ (select pd_id, 
			#~ case when pd_id is not null then
			#~ (select distinct brand_id from stock_move where product_id = pd_id and brand_id is not null limit 1)
			#~ end as sm_brand_id,
			#~ case when pd_id is not null then
			#~ (select distinct moc_id from stock_move where product_id = pd_id and moc_id is not null limit 1)
			#~ end as sm_moc_id,
			#~ case when pd_id is not null then
			#~ (select name from kg_moc_master where id = (select distinct moc_id from stock_move where product_id = pd_id and moc_id is not null limit 1))
			#~ end as sm_moc_name,
			#~ case when pd_id is not null then 
			#~ (select COALESCE(sum(product_qty),0.00) from stock_move where location_dest_id = %s and product_id = pd_id and name like '%%Openin%%') else 0.00 end as op_qty, 
			#~ case when pd_id is not null then (select COALESCE(sum(product_qty),0.00) from stock_move where location_dest_id = %s and product_id = pd_id and name not like '%%Openin%%') else 0.00 end as in_qty, case when pd_id is not null then (select COALESCE(sum(product_qty),0.00) from stock_move where location_id = %s and product_id = pd_id) else 0.00 end as out_qty 
			#~ from 
			#~ 
			 #~ """%(loc_id,loc_id,loc_id)
		#~ if len(my_plist) >0:
			#~ if len(tuple(my_plist)) == 1:
				#~ liststr = str(tuple(my_plist)).replace(",", "")
			#~ else:
				#~ liststr = str(tuple(my_plist))
			#~ sql3 = """ (select id as pd_id from product_product where id in %s ) """%(liststr)
		#~ else:
			#~ sql3 = """ (select id as pd_id from product_product where id in (
			#~ select product_id as pd_id from (
			#~ select distinct product_id from stock_move where location_dest_id = %s
			#~ union
			#~ select distinct product_id from stock_move where location_id = %s) as subone)) """%(loc_id,loc_id)
		#~ sql2 = """ as sam ) as sample
			#~ left outer join product_product pp on pp.id = pd_id
			#~ left outer join product_template pt on pt.id = pd_id
			#~ left outer join product_uom uom on uom.id = pt.uom_id
			#~ left outer join kg_brand_master brand on brand.id = sm_brand_id
			#~ ---- where pt.sale_ok = 't' and pp.no_stock_check = 't' and in_qty!=0
			#~ order by 8"""
		#~ sql = sql1+sql3+sql2
		#~ print"sssssssssssssssss",sql
		#~ cr.execute(sql)
		#~ data = cr.dictfetchall()
		#~ data.sort(key=lambda data: data['product'])
		#~ sno = 1
		#~ for item in data:
			#~ tran_price = 0.00
			#~ po_uom_rate = 0.00			
			#~ if item['po_rate']:
				#~ if '$' in item['po_rate']:
					#~ if item['po_rate'].split('$')[1] == 'po_uom':
						#~ tran_price = float(item['po_rate'].split('$')[0])
						#~ if item['pd_coeff'] > 0:
							#~ print "trtrrr",type(item['pd_coeff']),"\t",item['pd_coeff']
							#~ po_uom_rate = round(float((item['pd_coeff'])*tran_price),2)
						#~ else:
							#~ po_uom_rate = round((1*tran_price),2)
					#~ else:
						#~ tran_price = float(item['po_rate'].split('$')[0])
						#~ po_uom_rate = round((1*tran_price),2)

			
			#~ line_vals = {
			#~ 'sno':sno,
			#~ 'product_id':item['in_pro_id'],
			#~ 'brand':item['brand'] or '',
			#~ 'brand_id':item['sm_brand_id'] or False,			
			#~ 'uom':item['uom'],
			#~ 'moc':item['moc'] or '',
			#~ 'moc_id':item['sm_moc_id'] or False,		
			#~ 'uom':item['uom'],
			#~ 'qty':item['in_qty'],
			#~ 'physical_stock':item['in_qty'],
			#~ 'po_rate':po_uom_rate,
			#~ 'sale_rate':item['sale_rate'],			
			#~ 'stock_pid':rec.id,
			#~ 'stock_type':rec.stock_type,
			#~ 'entry_mode':'auto',
			#~ 'location_id':loc_id,			
			#~ 
			#~ }
			#~ sno = sno+1
			#~ if line_vals:
				#~ common_line = self.pool.get('kg.physical.stock.line').create(cr,uid,line_vals,context=None)
		return True
	
	def load_sale_stock(self, cr, uid, ids,context=None):
		rec  = self.browse(cr,uid,ids[0])
		my_plist = []
		if rec.product_id:
			psql1 = """select product_id from physical_stock_product_ids where kg_stock_id = %s"""%(ids[0])
			cr.execute(psql1)
			pdata = cr.dictfetchall()
			if pdata:
				for items in pdata:
					my_plist.append(items['product_id'])
		else:
			pass
		location_id = rec.location_id.id
		stock_obj = self.pool.get('stock.location')
		stock_rec = stock_obj.browse(cr,uid,rec.location_id.id)
		location_name = stock_rec.name
		sql1 = """select id from kg_physical_stock where state='load' and id != %s"""%(ids[0])
		cr.execute(sql1)
		data1 = cr.dictfetchall()
		if data1:
			sql = """delete from kg_physical_stock where state='load' and id != %s"""%(ids[0])
			cr.execute(sql)	
		self.write(cr,uid,ids,{
			'stock_type':'counter',
			'state':'draft',
			})
		sql1="""select pd_id as a_product_id,
		COALESCE(pp.sales_price,0.00) as sale_rate,
		0.00 as po_rate,
		pp.name_template as product,uom.id as uom,
		brand_id,brand.name as brand,((COALESCE(op_qty,0.00)+COALESCE(in_qty,0.00))-(COALESCE(out_qty,0.00)+COALESCE(sale_qty,0.00))) as close_qty
		from (
		select pd_id,
		case when pd_id is not null then
		(select distinct brand_id from stock_move where product_id = pd_id and brand_id is not null limit 1)
		end as brand_id,
		case when pd_id is not null then
		(select COALESCE(sum(product_qty),0.00) from stock_move where location_dest_id = %s and product_id = pd_id and name like '%%Openin%%' )
		else 0.00 end as op_qty,
		case when pd_id is not null then (select COALESCE(sum(product_qty),0.00) from stock_move where location_dest_id = %s and product_id = pd_id and name not like '%%Openin%%' )
		else 0.00 end as in_qty,
		case when pd_id is not null then (select COALESCE(sum(product_qty),0.00) from stock_move where move_type !='cons' and location_id = %s and product_id = pd_id  ) else 0.00 end as out_qty,
		case when pd_id is not null then (select COALESCE(sum(product_uom_qty),0.00) from sale_order_line where src_stock_location = %s and product_id = pd_id and bill_no !='/' and state != 'cancel')
		else 0.00 end as sale_qty from
		"""%(location_id,location_id,location_id,location_id)
		
		if len(my_plist) >0:
			if len(tuple(my_plist)) == 1:
				liststr = str(tuple(my_plist)).replace(",", "")
			else:
				liststr = str(tuple(my_plist))
			sql3 = """ (select id as pd_id from product_product where id in %s ) """%(liststr)		
		else:
			sql3 = """ (select id as pd_id from product_product where id in (
			select product_id as pd_id from (
			select distinct product_id from stock_move where location_dest_id = %s
			union
			select distinct product_id from stock_move where location_id = %s) as subone)) """%(location_id,location_id)		
		sql2 = """ as sam order by 2 
			) as sample
			left outer join product_product pp on pp.id = pd_id
			left outer join product_template pt on pt.id = pd_id
			left outer join product_uom uom on uom.id = pt.uom_id
			left outer join kg_brand_master brand on brand.id = sm_brand_id
			/*where pp.no_stock_check = 'f' and pt.sale_ok='t' and 
			((COALESCE(op_qty,0.00)+COALESCE(in_qty,0.00))-(COALESCE(out_qty,0.00)+COALESCE(sale_qty,0.00))) !=0*/"""
		sql = sql1+sql3+sql2
		cr.execute(sql)
		data = cr.dictfetchall()		
		data.sort(key=lambda data: data['product'])
		sno = 1
		for item in data:
			line_vals = {
			'sno':sno,
			'product_id':item['a_product_id'],
			'brand':item['brand'] or '',
			'brand_id':item['brand_id'] or False,
			'uom':item['uom'],
			'qty':item['close_qty'],
			'physical_stock':item['close_qty'],
			'po_rate':item['po_rate'],
			'po_total':0.00,
			'sale_rate':item['sale_rate'],
			'sale_total':0.00,
			'stock_pid':rec.id,
			'stock_type':rec.stock_type,
			'entry_mode':'auto',			
			'location_id':location_id,
			}
			sno = sno+1
			if line_vals:
				common_line = self.pool.get('kg.physical.stock.line').create(cr,uid,line_vals,context=None)
		return True 		
	
	def write(self, cr, uid, ids, vals, context=None): 
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		result = super(kg_physical_stock,self).write(cr, uid, ids, vals, context=context) 
		return result	
	
	def confirm_stock_bk(self, cr, uid, ids,context=None):
		rec  = self.browse(cr,uid,ids[0])
		if not rec.stock_line:
			raise osv.except_osv(_('Warning'),_('Line item cannot be empty'))
		for line in rec.stock_line:
			if rec.stock_type == 'main':
				if line.move_type != False:
					insql = """ select COALESCE(sum(product_qty),0.00) as in_qty from stock_move where product_id = %s and location_dest_id = %s and move_type = 'in' """%(line.product_id.id,rec.location_id.id)
					cr.execute(insql)
					indata = cr.dictfetchone()
					if indata:
						in_qty = indata['in_qty']
					else:
						in_qty = 0.00
					outsql = """ select COALESCE(sum(product_qty),0.00) as out_qty from stock_move where product_id = %s and location_id = %s and move_type = 'out' """%(line.product_id.id,rec.location_id.id)
					cr.execute(outsql)
					outdata = cr.dictfetchone()
					if outdata:
						out_qty = outdata['out_qty']
					else:
						out_qty = 0.00
					move_qty = in_qty-out_qty
					if line.qty != move_qty:
						raise osv.except_osv(_('Warning!'),
											_('Please Contact Administrator for stock adjustment of %s.') % (line.product_id.name))
					if line.diff_qty <0:
						if not (line.move_type in ('274') or line.move_type == False):
							raise osv.except_osv(_('Invalid Return To!'), _('Please select Store or Counter for %s !!' %(line.product_id.name)))
				if line.move_type == False and line.diff_qty <0:
					raise osv.except_osv(_('Invalid Return To!'), _('Please select Store or Counter for %s !!' %(line.product_id.name)))
				if line.diff_qty >0:
					if not ((line.move_type == False) and line.diff_qty >0):
						raise osv.except_osv(_('Invalid Return To!'), _('Please Make Adjustment Entry or Contact Administrator for %s !!' %(line.product_id.name)))
			if line.diff_qty == 0:
				if line.move_type == False:
					pass
				else:
					raise osv.except_osv(_('Error!'),_('Move Type can be blank only for Zero Differece Qty %s.') % (line.product_id.name))
			if rec.stock_type == 'counter':
				if line.move_type != False:
					if line.diff_qty <0:
						if not line.move_type in ('274') :
							raise osv.except_osv(_('Invalid Return To!'), _('Please select Store or Counter for %s !!' %(line.product_id.name)))
					if line.diff_qty >0:
						if not line.move_type in ('273') :
							raise osv.except_osv(_('Invalid Return To!'), _('Please select Wastage for %s !!' %(line.product_id.name)))
				else:
					if line.diff_qty<>0:
						raise osv.except_osv(_('Invalid Return To!'), _('Please Choose Return To for %s !!' %(line.product_id.name)))	   
		self.write(cr,uid,ids,{
			'state': 'confirm',
			'confirmed_by':uid,
			'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S'), 
			})
		return True
	
	def confirm_stock(self,cr,uid,ids,contaxt=None):
		obj = self.browse(cr,uid,ids[0])		
		self.write(cr,uid,ids,{'state':'confirm','confirmed_by':uid,'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
	def approve_stock(self,cr,uid,ids,contaxt=None):
		obj = self.browse(cr,uid,ids[0])		
		phy_no = '/'
		if obj.name != '' or obj.name != False: 
			phy_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.physical.stock')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,phy_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(phy_seq_id[0],rec.code,dt_time.date()))
			phy_name = cr.fetchone();
			phy_no = phy_name[0]
		self.write(cr,uid,ids,{'state':'approved','approved_by':uid,'approve_date': time.strftime('%Y-%m-%d %H:%M:%S'),'name':phy_no})
		return True
	
	def approve_stock_bk(self, cr, uid, ids,context=None):
		obj = self.browse(cr,uid,ids[0])
		brand_obj = self.pool.get('kg.brand.master')
		phy_no = '/'
		if obj.name != '' or obj.name != False: 
			phy_seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.physical.stock')])
			rec = self.pool.get('ir.sequence').browse(cr,uid,phy_seq_id[0])
			cr.execute("""select generatesequenceno(%s,'%s','%s') """%(phy_seq_id[0],rec.code,dt_time.date()))
			phy_name = cr.fetchone();
			phy_no = phy_name[0]		
		location_id = obj.location_id.id
		lot_obj = self.pool.get('stock.production.lot')
		cons_obj = self.pool.get('kg.stock.consumption')
		physical_stock_loc = 5
		stock_obj = self.pool.get('stock.move')
		sale_obj = self.pool.get('sale.order')
		dep_obj = self.pool.get('kg.depmaster')
		dep_ids = dep_obj.search(cr, uid, [('stock_location', '=', obj.location_id.id)])
		if dep_ids:
			dep_rec = dep_obj.browse(cr,uid,dep_ids[0])
			main_loc = dep_rec.main_location
		else:
			main_loc = obj.location_id.id
		
		counter_loc = obj.location_id.id
		if obj.stock_type == 'counter':
			for line in obj.stock_line:
				avg_price_sql = """ select round(COALESCE(avg(price_unit),0),2) as avg_price from stock_move where price_unit > 0 and product_id = %s """%(line.product_id.id)
				cr.execute(avg_price_sql)			
				price_data = cr.dictfetchone()
				if price_data:
					avg_price = price_data['avg_price']
				else:
					avg_price = 0.00
				if line.diff_qty < 0 and line.move_type != False:
					diff_qty = line.diff_qty*-1
					vals = {
						'product_id': line.product_id.id,
						'name':line.product_id.name,
						'product_qty':diff_qty,
						'po_to_stock_qty':diff_qty,
						'stock_uom':line.uom.id,
						'product_uom': line.uom.id,
						'location_id': int(line.move_type),
						'location_dest_id': counter_loc,
						'move_type': 'out',
						'state': 'done',
						'price_unit': avg_price,
						'stock_rate':avg_price,
						'notes':'Physical Stock Entry',
						'trans_type':'phy_return',
						'phy_id':obj.id,
						}
					cons_id = cons_obj.search(cr, uid, [('location_id', '=', counter_loc),('product_id', '=', line.product_id.id)], context=context)
					if len(cons_id) > 0:
						out_sql = """ select coalesce(sum(product_qty),0) as out_qty from stock_move where product_id=%s and move_type='out' and state='done' and location_dest_id = %s group by product_id """%(line.product_id.id,counter_loc)
						cr.execute(out_sql)			
						out_data = cr.dictfetchall()
						if out_data:
							out_data = out_data[0]
							out_data = out_data['out_qty']
							cr.execute("""update kg_stock_consumption set stock_qty = (%s+%s) where id = %s """,(out_data,diff_qty,tuple(cons_id)))
						cons_sql = """ select coalesce(sum(product_qty),0) as cons_qty from stock_move where product_id=%s and state='done' and location_id = %s group by product_id """%(line.product_id.id,counter_loc)
						cr.execute(cons_sql)			
						cons_data = cr.dictfetchall()				
						if cons_data:
							cons_data = cons_data[0]
							cons_data = cons_data['cons_qty']
							cr.execute("""update kg_stock_consumption set cons_qty = %s where id = %s """,(cons_data,tuple(cons_id)))
					stock_obj.create(cr, uid, vals, context=context)
				elif line.diff_qty > 0 and line.move_type != False:
					vals = {
						'product_id': line.product_id.id,
						'name':line.product_id.name,
						'product_qty': line.diff_qty,
						'po_to_stock_qty':line.diff_qty,
						'stock_uom':line.uom.id,
						'product_uom': line.uom.id,
						'location_id': counter_loc,
						'location_dest_id': int(line.move_type),
						'move_type': 'cons',
						'state': 'done',
						'price_unit': avg_price,
						'stock_rate':avg_price,
						'notes':'Damage / Sale Entry',
						'trans_type':'phy_waste',
						'phy_id':obj.id,						
						}
					cons_id = cons_obj.search(cr, uid, [('location_id', '=', counter_loc),('product_id', '=', line.product_id.id)], context=context)
					my_cons = []
					if len(cons_id) > 0:
						my_cons.append(cons_id)
						out_sql = """ select coalesce(sum(product_qty),0) as out_qty from stock_move where product_id=%s and move_type='out' and state='done' and location_dest_id = %s group by product_id """%(line.product_id.id,counter_loc)
						cr.execute(out_sql)			
						out_data = cr.dictfetchall()
						if out_data:
							out_data = out_data[0]
							out_data = out_data['out_qty']
							cr.execute("""update kg_stock_consumption set stock_qty = %s where id = %s """, (out_data,tuple(cons_id)))
						cons_sql = """ select coalesce(sum(product_qty),0) as cons_qty from stock_move where product_id=%s and state='done' and location_id = %s group by product_id """%(line.product_id.id,counter_loc)
						cr.execute(cons_sql)			
						cons_data = cr.dictfetchall()				
						if cons_data:
							cons_data = cons_data[0]
							cons_data = cons_data['cons_qty']
							cr.execute("""update kg_stock_consumption set cons_qty = (%s+%s) where id = %s """,(cons_data,line.diff_qty,tuple(cons_id)))
					stock_obj.create(cr,uid,vals)
		if obj.stock_type == 'main':
			for line in obj.stock_line:
				avg_price_sql = """ select round(COALESCE(avg(price_unit),0),2) as avg_price from stock_move where price_unit > 0 and product_id = %s """%(line.product_id.id)
				cr.execute(avg_price_sql)		   
				price_data = cr.dictfetchone()
				if price_data:
					avg_price = price_data['avg_price']
				else:
					avg_price = 0.00
				if line.diff_qty < 0 and line.move_type != False:
					diff_qty = line.diff_qty*-1
					vals = {
						'product_id': line.product_id.id,
						'name':line.product_id.name,
						'product_qty':diff_qty,
						'po_to_stock_qty':diff_qty,
						'stock_uom':line.uom.id,
						'product_uom': line.uom.id,
						'location_id': int(line.move_type),
						'location_dest_id': counter_loc,
						'move_type': 'in',
						'state': 'done',
						'price_unit': avg_price,
						'stock_rate':avg_price,
						'notes':'Physical Stock Entry - Main',
						'trans_type':'phy_return',
						'phy_id':obj.id,						
						}
					stock_obj.create(cr, uid, vals, context=context)
					lotvals ={
								'batch_no':phy_no,
								'product_id':line.product_id.id,
								'brand_id':line.brand_id.id,
								'product_uom':line.uom.id,
								'product_qty':diff_qty,
								'pending_qty':diff_qty,
								'issue_qty':diff_qty,
								'batch_no':line.stock_pid.name,
								'price_unit':avg_price or 0.0,
								'po_uom':line.uom.id,
								'source_loc_id':counter_loc,
								'grn_type':'material',
								'lot_type':'in'
							}
					lot_obj.create(cr, uid, lotvals, context=context)
				elif line.diff_qty > 0:
					if line.move_type == False:
						line.write({'note': 'Please make the Adjustmend Entry!!'})
					else:
						pass
		self.write(cr,uid,ids,{'state':'approved','approved_by':uid,'approve_date': time.strftime('%Y-%m-%d %H:%M:%S'),'name':phy_no})
		return True
	
	def cancel_stock(self, cr, uid, ids, context=None):
		rec  = self.browse(cr,uid,ids[0])
		if rec.remark == None or rec.remark == False:
			raise osv.except_osv(_('Invalid action !'), _('Enter remarks to cancel!!'))

		self.write(cr, uid,ids,{'state' : 'cancel','rej_user_id': uid, 'reject_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
	def unlink(self, cr, uid, ids, context=None):
		physical_stock = self.read(cr, uid, ids, ['state'], context=context)
		unlink_ids = []
		for s in physical_stock:
			if s['state'] in ['draft']:
				unlink_ids.append(s['id'])
			else:
				raise osv.except_osv(_('Invalid Action!'), _('System Allow to delete only Draft Entries !'))
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
	def _check_lineitem(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		prd_obj = self.pool.get('product.product')
		p_list = []
		pd_list = []
		p_list = [lines.product_id.id for lines in rec.stock_line]
		tmp = list(set(p_list))
		for item in set(p_list):
			if p_list.count(item) > 1:
				prd_rec = prd_obj.browse(cr,uid,item)
				pd_name = prd_rec.name_template
				pd_list.append(pd_name)
		if pd_list!=[]:
			raise osv.except_osv(_('Warning!'), _('Duplicate Items Found \n %s !!'%([str(num) for num in pd_list])))				
		return True	
	
kg_physical_stock()

class kg_physical_stock_line(osv.osv):
	
	_name = "kg.physical.stock.line"
	_description = "Physical Stock Line"
	
	def onchange_product_id(self, cr, uid, ids, product_id,uom,stock_type,location_id,entry_mode, context=None):
		
		value = {'uom': ''}
		sys_qty = 0.00
		if entry_mode == 'manual':
			if stock_type == 'main':
				sql = """SELECT 
				distinct spl.product_id as in_pro_id,
				brand.name as brand,
				/*spl.moc_id as moc_id,
				spl.brand_id as brand_id,*/
				spl.product_uom as uom,
				pp.type as purpose,
				pp.name_template as product,
				sum(pending_qty) as in_qty
				FROM stock_production_lot spl
				left JOIN product_product pp ON (pp.id=spl.product_id)
				left JOIN kg_brand_master brand ON (brand.id=spl.brand_id)
				where --- spl.pending_qty > 0 and 
				spl.lot_type = 'in'
				and spl.product_id = %s 
				and spl.source_loc_id = %s
				   group by spl.product_id,brand.name,spl.product_uom,
				   ----spl.brand_id,spl.moc_id,
				   pp.type,pp.name_template
				"""%(product_id,location_id)
				cr.execute(sql)
				data = cr.dictfetchall()
				if data:
					data = data[0]
					sys_qty = data['in_qty']
			if stock_type == 'counter':
				sql = """select COALESCE((out_qty - cons_qty),0.00) as close_qty
				from 
				(select distinct product_id,brand_id,
				Sum(case when move_type = 'out' and location_dest_id = %s
				then product_qty else 0 end) over(partition by product_id,brand_id) as out_qty,
				Sum(case when location_id = %s
				then product_qty else 0 end) over(partition by product_id,brand_id) as cons_qty
				from stock_move ) as sub_query
				where  --- (out_qty - cons_qty) > 0 and
				(select no_stock_check from product_product where id = product_id) = 'f'
				and product_id = %s
				"""%(location_id,location_id,product_id)
				cr.execute(sql)
				data = cr.dictfetchall()				
				if data:
					data = data[0]
					sys_qty = data['close_qty']
			if product_id:
				prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
				value = {'uom': prod.uom_id.id,'qty':sys_qty}
		
		return {'value': value}
	
	_columns = {
	
	'stock_pid': fields.many2one('kg.physical.stock', 'Stock No', required=False, ondelete='cascade'),
	'product_id': fields.many2one('product.product', 'Product', required=False,domain = [('state','=','approved'),('active','=','t')]),
	'uom': fields.many2one('product.uom', 'UOM', required=False, domain = [('dummy_state','=','approved'),('active','=','t')]),
	'stock_type': fields.selection([('main','Main'),('counter', 'Counter')], 'Location Type',readonly=False),
	'brand': fields.char('Brand', required=False),
	'brand_id': fields.many2one('kg.brand.master', 'Brand Id', required=False , domain = [('state','=','approved'),('active','=','t')]),	
	'moc': fields.char('MOC', required=False),
	'moc_id': fields.many2one('kg.moc.master', 'Moc Id', required=False , domain = [('state','=','approved'),('active','=','t')]),	
	'qty': fields.float('System Stock Qty', required=True),
	'physical_stock':fields.float('Physical Stock Qty'),
	'diff_qty':fields.float('Diff Qty'),
	'note': fields.text('Remarks'),	
	'line_state': fields.selection([('process','Processing'),('noprocess','NoProcess'),('pi_done','PI-Done'),('done','Done')], 'Status'),
	'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')], 'Entry Mode'),	
	'move_type': fields.selection([('273','Wastage'),('274','Store or Counter')], 'Return To'),
	'location_id': fields.many2one('stock.location', 'Location', required=False , domain = [('dummy_state','=','approved'),('active','=','t')]),
	'line_date': fields.date('Indent Date'),
	'sno': fields.integer('S.No'),	
	'price_unit':fields.float('Unit Price'),
	'po_rate':fields.float('PO Rate'),
	'po_total':fields.float('PO Total'),
	'sale_rate':fields.float('Sale Rate'),
	'sale_total':fields.float('Sale Total'),		
	
	}
	
	def default_get(self, cr, uid, fields, context=None):
		return context	
	
	def onchange_physicalqty(self, cr, uid, ids, qty,physical_stock,po_rate,sale_rate):
		value = {'physical_stock':'','diff_qty':''}
		difference_qty = physical_stock - qty
		po_total = difference_qty*po_rate
		sale_total = difference_qty*sale_rate
		value = {'diff_qty': difference_qty,'po_total':po_total,'sale_total':sale_total}
		return {'value': value}
	
	def onchange_diffqty(self, cr, uid, ids, diff_qty,stock_type):
		value = {'move_type':''}
		move_type = ''
		if stock_type == 'counter':
			if diff_qty < 0:
				move_type = '274'
			elif diff_qty > 0:
				move_type = '273'
		elif stock_type == 'main':
			if diff_qty < 0:
				move_type = '274'
		value = {'move_type': move_type}
		return {'value': value}
	
	_defaults = {
		
		'line_date' : lambda * a: time.strftime('%Y-%m-%d'),
		
	}

kg_physical_stock_line()	
