
import time
from report import report_sxw
from reportlab.pdfbase.pdfmetrics import stringWidth
import locale
from datetime import datetime, date
import ast


class kg_so_bill_register(report_sxw.rml_parse):
	
	_name = 'kg.so.bill.register'
	

	def __init__(self, cr, uid, name, context=None):
		if context is None:
			context = {}
		super(kg_so_bill_register, self).__init__(cr, uid, name, context=context)
		self.query = ""
		self.period_sql = ""
		self.localcontext.update( {
			'time': time,
			'get_filter': self._get_filter,
			'get_start_date':self._get_start_date,
			'get_end_date':self._get_end_date,
			'get_data':self.get_data,
			'locale':locale,
			#'get_data_line':self.get_data_line,

		})
		self.context = context
		
	def get_data(self,form):
		
		res = {}
		where_sql = []
		partner = []
		product = []
			
		if form['supplier']:
			for ids1 in form['supplier']:
				partner.append("pi.supplier_id = %s"%(ids1))
		
		if form['product_id']:
			for ids2 in form['product_id']:
				product.append("pil.product_id = %s"%(ids2))		
				

		if partner:
			partner = 'and ('+' or '.join(partner)
			partner =  partner+')'
			print "partner -------------------------->>>>", partner
		else:
			partner = ''
			
		if product:
			product = 'and ('+' or '.join(product)
			product =  product+')'
			print "product -------------------------->>>>", product
		else:
			product = ''
			
			
		if form['status'] == 'approved':
			so_state = 'approved'
		elif form['status'] == 'cancelled':
			so_state = 'cancel'
		else:
			so_state = 'approved'

			
		self.cr.execute('''
		
			  SELECT
			  res.name AS su_name,
			  pi.id AS pi_id,
			  pi.name AS inv_no,
			  pi.invoice_date AS inv_date,
			  pi.sup_invoice_no AS sup_inv_no,
			  pi.sup_invoice_date AS sup_inv_date,
			  uom.name AS uom,
			  pt.name AS pro_name,
			  pil.po_so_qty as qty,
			  pil.id as pil_id,
			  pil.price_unit as price,
			  res.street AS str1,
			  res.zip as zip,
			  city.name as city,
			  state.name as state,
			  pi.discount_amt as dis,			  
			  pi.tax_amt as tax,			  
			  pi.total_amt as total,			  
			  pi.net_amt as net			  
			  FROM  kg_purchase_invoice pi
			  			  
			  JOIN res_partner res ON (res.id=pi.supplier_id)
			  left join res_city city on(city.id=res.city)
			  left join res_country_state state on(state.id=res.state_id)
			  JOIN kg_pogrn_purchase_invoice_line pil ON (pil.invoice_header_id=pi.id)
			  JOIN product_product prd ON (prd.id=pil.product_id)
			  JOIN product_template pt ON (pt.id=prd.product_tmpl_id)
			  JOIN product_uom uom ON (uom.id=pil.uom_id)

			  where pi.state=%s and pi.type='from_so' and pi.invoice_date >=%s and pi.invoice_date <=%s '''+ product + partner + '''
			  
			  
			 
			  ''',(so_state,form['date_from'],form['date_to']))
			   
		data=self.cr.dictfetchall()
		#print "data ::::::::::::::=====>>>>", data
		
		if data:									
			new_data = []
			count = 0
			gr_total = 0
			ad_amt = 0
			gr_order_qty_total = 0
			gr_rec_qty_total = 0
			gr_pending_qty_total = 0
			gr_rate_total = 0
			pil_obj = self.pool.get('kg.poadvance.purchase.invoice.line')
			for pos1, item1 in enumerate(data):
					
				delete_items = []
				inv_no = item1['inv_no']
				print "inv_no,,,,,,,,,,,,,,",inv_no
				order_id = item1['pi_id']
				pi_date = item1['inv_date']
				print "date,,,,,,,,,,,,,,,",pi_date
				fmt = '%Y-%m-%d'
				
				pil_rec = pil_obj.browse(self.cr, self.uid,item1['pil_id'])
				gr_total += item1['total']
				gr_order_qty_total += item1['qty']
				gr_rate_total += item1['price']
				print "gr_total.........................>>>",gr_total
				
				for pos2, item2 in enumerate(data):
					if not pos1 == pos2:
						if item1['pi_id'] == item2['pi_id'] and item1['su_name'] == item2['su_name']:												
							if count == 0:
								new_data.append(item1)
								print "new_data.............",new_data
								count = count + 1
							item2_2 = item2
							item2_2['su_name'] = ''
							item2_2['str1'] = ''
							item2_2['zip'] = ''
							item2_2['city'] = ''
							item2_2['state'] = ''
							item2_2['inv_no'] = ''
							item2_2['sup_inv_no'] = ''
							item2_2['inv_date'] = ''
							item2_2['sup_inv_date'] = ''
							item2_2['address']=''
							item2_2['total']=0
							item2_2['tax']=0
							item2_2['net']=0
							new_data.append(item2_2)
							print "new_data2.............>",new_data
							delete_items.append(item2)
					
					else:
						print "Few so have one line"
						
			item1['po_ad_amt'] = ad_amt
			item1['gr_total'] = gr_total
			item1['gr_ordqty_total'] = gr_order_qty_total
			
			item1['gr_ratetotal'] = gr_rate_total
			
		else:
			print "No Data"
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
  

report_sxw.report_sxw('report.kg.so.bill.register', 'purchase.order', 
			'addons/kg_po_reports/report/kg_so_bill_register.rml', 
			parser=kg_so_bill_register, header = False)
