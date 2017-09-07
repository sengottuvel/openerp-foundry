import time
from report import report_sxw
from reportlab.pdfbase.pdfmetrics import stringWidth
import locale
from datetime import date
import datetime

class mains_closing_stock_report(report_sxw.rml_parse):
	
	_name = 'mains.closing.stock.report'
	_inherit='stock.picking'   
	
	def __init__(self, cr, uid, name, context=None):
		if context is None:
			context = {}
		super(mains_closing_stock_report, self).__init__(cr, uid, name, context=context)
		self.query = ""
		self.period_sql = ""
		self.localcontext.update( {
			'time': time,
			'get_filter': self._get_filter,
			'get_start_date':self._get_start_date,
			'get_end_date':self._get_end_date,
			'get_data':self.get_data,
			'locale':locale,
		})
		self.context = context
	
	def get_data(self,form):
		res = {}
		
		where_sql = []
		major = []
		product=[]
		pro_type=[]
		
		if form['location_dest_id']:
			location = form['location_dest_id'][0]
			where_sql.append("a.location_dest_id = %s" %(location))
		if where_sql:
			where_sql = ' and '+' or '.join(where_sql)
		else:
			where_sql=''
		
		if form['major_name']:
			majorwise = form['major_name'][0]
			major.append("pt.categ_id = %s" %(majorwise))
		if major:
			major = ' and '+' or '.join(major)
		else:
			major=''
		
		if form['product']:
			for ids2 in form['product']:
				product.append("a.product_id = %s"%(ids2))	
		if product:
			product = ' and '+' or '.join(product)
		else:
			product=''
		
		if form['product_type']:
			pro_type.append("pt.type= '%s' "%form['product_type'])
		
		if pro_type:
			pro_type = ' and '+' or '.join(pro_type)
		else:
			pro_type=''
		
		print "date............"	, type(form['date'])
		location_rec = self.pool.get('stock.location').browse(self.cr,self.uid,location)
		print "location_rec.........................", location_rec, location_rec.location_type
		
		if location_rec.location_type == 'main':
			lo_type = 'in'
		else:
			lo_type = 'out'
		
		#~ self.cr.execute('''		
			   #~ SELECT 
					#~ sm.product_id as in_pro_id,
					#~ sum(product_qty) as in_qty
			   #~ 
			   #~ FROM stock_move sm
			   #~ 
			   #~ left JOIN product_template pt ON (pt.id=sm.product_id)
			   #~ left JOIN product_category pc ON (pc.id=pt.categ_id)
			   #~ 
			   #~ where sm.product_qty != 0 and sm.state=%s and sm.move_type =%s and sm.date::date <=%s '''+ where_sql + major + product + pro_type +'''
			   #~ group by sm.product_id''',('done',lo_type,form['date']))
		#~ 
		#~ data=self.cr.dictfetchall()
		self.cr.execute('''
			   select sum(a.product_qty) -
				(select (case when sum(b.product_qty) is not null then sum(b.product_qty) else 0 end) from stock_move b where b.move_type = 'out'
				and b.product_id = a.product_id and b.brand_id = a.brand_id and a.moc_id = b.moc_id and b.date <= %s and b.location_id = %s) as stock_uom_close,
				(case when a.uom_conversation_factor = 'two_dimension' then
				(sum(a.product_qty * a.length * a.breadth) -
				(select (case when sum(b.product_qty) is not null then sum(b.product_qty) else 0 end) from stock_move b where b.move_type = 'out'
				and b.product_id = a.product_id and b.brand_id = a.brand_id and a.moc_id = b.moc_id and b.date <= %s and b.location_id = %s)) / prod.po_uom_in_kgs / a.length / a.breadth
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
				a.length as length,
				a.breadth as breadth,
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
			   group by 3,4,5,6,7,8,9,10,11,12,13,14,15,16,17 order by prod.name_template ''',(form['date'],location,form['date'],location,form['date'],location,form['date'],'done',location))
		
		data=self.cr.dictfetchall()
		print "in_data ::::::::::::::=====>>>>", data
		data_new = []
		gr_total=0.0
		if data:
			for item in data:
				if item['product_id']:
					proc_rec = self.pool.get('product.product').browse(self.cr,self.uid,item['product_id'])
					item['suom'] = proc_rec.uom_id.name
					item['puom'] = proc_rec.uom_po_id.name
				if item['stock_uom_close'] > 0:
					self.cr.execute('''
							   SELECT
								line.price_unit as price,
								line.price_type as price_type,
								line.length as length,
								line.breadth as breadth,
								line.product_qty as product_qty
								
								FROM purchase_order_line line
								
								JOIN purchase_order po ON (po.id=line.order_id)
								
								where po.state='approved' and line.product_id = %s and line.brand_id = %s
								and line.moc_id = %s  and po.approved_date::date <= %s
								order by po.date_order desc limit 1''',(item['product_id'],item['brand_id'],item['moc_id'],form['date']))
					
					lot_data = self.cr.dictfetchall()
					print"lot_datalot_datalot_data--------------",lot_data
					if lot_data:
						closing_value = lot_data[0]['price']
						item['po_price'] = lot_data[0]['price']
						print"item['uom_conversation_factor']",item['uom_conversation_factor']
						if item['uom_conversation_factor'] == 'two_dimension':
							print"aaaaaaaaaaaaaa"
							if lot_data[0]['price_type'] == 'po_uom':
								print"popopopopopopopo"
								item['closing_value'] = item['stock_uom_close'] * ((lot_data[0]['price'] * lot_data[0]['product_qty'])/(lot_data[0]['length'] or 1 * lot_data[0]['breadth'] or 1 * lot_data[0]['product_qty'] or 1 * item['po_uom_in_kgs'] or 1))
							elif lot_data[0]['price_type'] == 'per_kg':
								print"per_kgper_kgper_kgper_kgper_kg"
								item['closing_value'] = item['stock_uom_close'] * lot_data[0]['price']
						elif item['uom_conversation_factor'] == 'one_dimension':
							print"bbbbbbbbbbbbbbbbbbbbb"
							if lot_data[0]['price_type'] == 'po_uom':
								print"popopopopopopopo"
								item['closing_value'] = item['stock_uom_close'] * ((lot_data[0]['price'] * lot_data[0]['product_qty'])/(lot_data[0]['product_qty'] * item['po_uom_coeff']))
							elif lot_data[0]['price_type'] == 'per_kg':
								print"per_kgper_kgper_kgper_kgper_kg"
								item['closing_value'] = item['stock_uom_close'] * lot_data[0]['price']
						else:
							item['closing_value'] = 0
					else:
						item['po_price'] = 0
						item['closing_value'] = 0
					print"item['po_price']item['po_price']item['po_price']",item['po_price']
					print"item['closing_value']item['closing_value']item['closing_value']",item['closing_value']
					gr_total += item['closing_value']
					item['grand_total'] = int(gr_total)
					
					data_new.append(item)
		
				else:
					pass
		print "*******************************************************************************",data_new
		return data_new
	
	def _get_filter(self, data):
		if data.get('form', False) and data['form'].get('filter', False):
			if data['form']['filter'] == 'filter_date':
				return _('Date')
		return _('No Filter')
	
	def _get_start_date(self, data):
		if data.get('form', False) and data['form'].get('date_from', False):
			return data['form']['date_from']
		return ''
	
	def _get_end_date(self, data):
		if data.get('form', False) and data['form'].get('date_to', False):
			return data['form']['date_to']
		return ''
	
report_sxw.report_sxw('report.mains.closing.stock.report', 'stock.picking', 
			'addons/kg_reports/warehouse/report/mains_closing_stock_report.rml', 
			parser=mains_closing_stock_report, header = False)
