import time
from report import report_sxw
from osv import osv
from reportlab.pdfbase.pdfmetrics import stringWidth
from operator import itemgetter
import tools
from osv import fields, osv
import time, datetime
from datetime import *
import logging
import locale
import netsvc
logger = logging.getLogger('server')

class kg_product_reg_report(report_sxw.rml_parse):
	
	_name = 'kg.product.reg.report'
	
	
	def __init__(self, cr, uid, name, context=None):
		if context is None:
			context = {}
		super(kg_product_reg_report, self).__init__(cr, uid, name, context=context)
		self.query = ""
		self.period_sql = ""
		self.localcontext.update( {
			'time': time,
			'get_filter': self._get_filter,
			'get_start_date':self._get_start_date,
			'get_end_date':self._get_end_date,
			'get_data':self.get_data,
			'locale':locale
			
			
			
		})
		self.context = context

	def get_data(self,form):
		res = {}
		where_sql = []
		product = []
		pr_type = []
		
		if form['product']:
			for ids1 in form['product']:
				product.append("pro.id = %s"%(ids1)) 
				
		if product:
			product = ' and '+' or '.join(product)
		else:
			product=''
		
		if form['type']:
			
			pr_type.append("pro.type ='%s'"%(form['type']))
			
		if pr_type:
			pr_type = 'and ('+' or '.join(pr_type)
			pr_type =  pr_type+')'
		else:
			pr_type = ''
		
		print "--------------------------------->",pr_type			
		
		self.cr.execute('''
				
				SELECT 
				
				pro.id as product_id,
				pro.name_template as product_name,
				uom.name as product_uom,
				categ.name as pro_category
				
				FROM  product_product pro
				
				
				left join product_template temp on (pro.product_tmpl_id = temp.id)
				left join product_uom uom on (temp.uom_id=uom.id)	
				left join product_category categ on (temp.categ_id = categ.id)			
				
				
				
				where pro.active = 't' '''+ product + pr_type + '''
				order by pro.name_template ''')
				
				
		data = self.cr.dictfetchall()
		print "Data ABBBBBBBBBBBBBBBBBBBBBBBBBBBBBB", data
		
		
		for item in data:
			print item['product_id']
			purchase_sql = """ select pol.id,
			pol.product_id,
			pol.product_qty,
			pol.price_unit,
			to_char(po.date_order,'dd/mm/yyyy') AS date_order
			
			from purchase_order_line pol
							LEFT JOIN purchase_order po ON (pol.order_id=po.id)
							where pol.product_id = %s
							order by po.date_order desc """%(item['product_id'])
			self.cr.execute(purchase_sql)			
			purchase_data = self.cr.dictfetchone()
			print "purchase_data...........................", purchase_data
			if purchase_data:
				item['purchase_date'] = purchase_data['date_order']
				item['purchase_qty'] = purchase_data['product_qty']
				item['purchase_rate'] = purchase_data['price_unit']
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
 
report_sxw.report_sxw('report.kg.product.reg.report','product.product','addons/kg_store_reports/report/kg_product_reg_report.rml',
						parser=kg_product_reg_report, header= False)
