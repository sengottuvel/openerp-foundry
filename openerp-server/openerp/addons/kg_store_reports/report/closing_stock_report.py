import time
from report import report_sxw
from reportlab.pdfbase.pdfmetrics import stringWidth
import locale
from datetime import date
import datetime

class closing_stock_report(report_sxw.rml_parse):
	
	_name = 'closing.stock.report'
	_inherit='stock.picking'   

	def __init__(self, cr, uid, name, context=None):
		if context is None:
			context = {}
		super(closing_stock_report, self).__init__(cr, uid, name, context=context)
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
		data=[]
		
		if form['location_dest_id']:
			location = form['location_dest_id'][0]
			where_sql.append("sm.location_dest_id = %s" %(location))
		
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
				product.append(ids2) 
				
		
			
		if form['product_type']:
				pro_type.append("pt.type= '%s' "%form['product_type'])
				
		if pro_type:
			pro_type = ' and '+' or '.join(pro_type)
		else:
			pro_type=''
			
		product_search = self.pool.get('product.product').search(self.cr,self.uid,[('state','=','approved'),('sale_ok','=',True)])	
		
		
		if product:
			
			product_list = product
			
		else:
			
			product_list = 	product_search
					
		location = self.pool.get('stock.location').search(self.cr, self.uid, [('name', '=', 'Sales location')])
		
		loc = self.pool.get('stock.location').search(self.cr, self.uid, [('name', '=', 'KG_Consumption_Store')])
		
		
		gr_total = 0.0
		
		for prod in product_list:
			ans = {}
			product_rec = self.pool.get('product.product').browse(self.cr,self.uid,prod)
			uom_rec = self.pool.get('product.uom').browse(self.cr,self.uid,product_rec.uom_id.id)
			stock_move = self.pool.get('stock.move').search(self.cr, self.uid, [('product_id', '=', prod)])
					
			out_sql = """ select product_id,sum(product_qty) as qty from stock_move where product_id=%s and move_type='out' and state='done' and location_dest_id = %s and date <= '%s' group by product_id """%(prod,location[0],form['date'])
			self.cr.execute(out_sql)			
			out_data = self.cr.dictfetchall()
			
			out_sql1 = """ select product_id,sum(product_qty) as qty from stock_move where product_id=%s and move_type='cons' and state='done' and location_dest_id = %s and date <= '%s' group by product_id """%(prod,loc[0],form['date'])
			self.cr.execute(out_sql1)			
			out_data1 = self.cr.dictfetchall()
			
			if out_data and out_data1:
				
				diff = out_data[0]['qty'] - out_data1[0]['qty']
				
				if diff > 0 :
					
					move_rec = self.pool.get('stock.move').browse(self.cr, self.uid, stock_move[-1])
					
					ans['product_name'] = product_rec.name_template
					ans['uom'] = uom_rec.name
					ans['close_qty'] = diff
					ans['closing_value'] = diff * move_rec.price_unit
					
					gr_total += ans['closing_value']
					
					ans['gr_total'] = gr_total
					
					data.append(ans)
		
		return data
			
			   

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
  

report_sxw.report_sxw('report.closing.stock.wizard', 'stock.picking', 
			'addons/kg_store_reports/report/closing_stock_report.rml', 
			parser=closing_stock_report, header = False)
			
			
