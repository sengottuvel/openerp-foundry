import time
from lxml import etree
from osv import fields, osv
from tools.translate import _
import pooler
import logging
import netsvc
import datetime as lastdate
import datetime as lastdate
from datetime import datetime
from datetime import timedelta
from datetime import date
from dateutil import relativedelta
import datetime
import calendar
from datetime import datetime
	
logger = logging.getLogger('server')

class kg_excel_po_register(osv.osv):

	_name = 'kg.excel.po.register'

	_columns = {
		
		'creation_date': fields.date('Creation Date', readonly=True),
		'product_id':fields.many2many('product.product','kg_ex_po_rep_wiz','report_id','product_id','Product Name'),
		'supplier':fields.many2many('res.partner','kg_ex_po_rep_sup','report_id','supplier_id','Supplier'),
		'date_from': fields.date("Start Date",required=True),
		'date_to': fields.date("End Date",required=True),		
		'status': fields.selection([('approved', 'Approved'),('cancelled','Cancelled'),('pending','Pending')], "Status"),
		'dep_project':fields.many2one('kg.project.master','Dept/Project Name'),
		"rep_data":fields.binary("File",readonly=True),
		'state': fields.selection([('draft', 'Draft'),('done','Done')], 'Status', readonly=True),
		'company_id': fields.many2one('res.company', 'Company'),
		'name': fields.char("Report Name"),
		
		}
	
	#~ def _get_month_first(self, cr, uid,ids, context=None):
		#~ today = datetime.date.today()
		#~ first = datetime.date(day=1, month=today.month, year=today.year)
		#~ res = first.strftime('%Y-%m-%d')
		#~ return res
			
	_defaults = {
		
		'state': 'draft',
		'creation_date' : fields.date.context_today,
		#~ 'date_from' : _get_month_first,
		'date_from' : lambda * a: time.strftime('%Y-%m-%d'),
		'date_to' : lambda * a: time.strftime('%Y-%m-%d'),
		
		}
		
	def produce_xls(self, cr, uid, ids, context={}):
		
		import StringIO
		import base64
		
		try:
			import xlwt
		except:
		   raise osv.except_osv('Warning !','Please download python xlwt module from\nhttp://pypi.python.org/packages/source/x/xlwt/xlwt-0.7.2.tar.gz\nand install it')
		   
		rec =self.browse(cr,uid,ids[0])
		
		where_sql = []
		product=[]
		supplier = []
		
		if rec.status == 'approved':
			po_state = "'"+'approved'+"'"
		elif rec.status == 'cancelled':
			po_state = "'"+'cancel'+"'"
		else:
			po_state = "'"+'approved'+"'"
			
		if rec.supplier:
			sup = [x.id for x in rec.supplier]
			supplier_ids = ",".join(str(x) for x in sup)
			supplier.append("po.partner_id in (%s)"%(supplier_ids))
		
		if rec.product_id:
			prod = [x.id for x in rec.product_id]
			product_ids = ",".join(str(x) for x in prod)
			product.append("pol.product_id in (%s)"%(product_ids))
		
		if supplier:
			supplier = 'and '+' or '.join(supplier)
			supplier =  supplier+' '
		else:
			supplier = ''
		
		if product:
			product = 'and '+' or '.join(product)
			product =  product+' '
		else:
			product = ''
		
		date_from = "'"+rec.date_from+"'"
		date_to = 	"'"+rec.date_to+"'"
		
		if not rec.status or rec.status == 'approved' or rec.status == 'cancelled':	
			sql = """		
				SELECT
					  po.id AS po_id,
					  po.name AS po_no,
					  to_char(po.date_order,'dd/mm/yyyy') AS po_date,
					  po.date_order AS date,
					  po.note AS remark,
					  po.amount_total as total,
					  po.add_text as address,
					  po.amount_tax as taxamt,
					  pol.id as pol_id,
					  pol.product_qty AS qty,
					  pol.pending_qty AS pending_qty,
					  pol.price_unit as rate,
					  pol.kg_discount_per as disc1,
					  pol.kg_disc_amt_per as disc2,	
					  po_ad.advance_amt as po_ad_amt,				  
					  uom.name AS uom,
					  pt.name AS pro_name,
					  res.name AS su_name,
					  res.street AS str1,
					  res.zip as zip,
					  city.name as city,
					  state.name as state,
					  brand.name as brand_name,
					  po.quot_ref_no as quot_ref_no,
					  moc.name as moc
								  
					  FROM  purchase_order po
								  
					  JOIN res_partner res ON (res.id=po.partner_id)
					  left join res_city city on(city.id=res.city_id)
					  left join res_country_state state on(state.id=res.state_id)
					  JOIN purchase_order_line pol ON (pol.order_id=po.id)
					  JOIN product_product prd ON (prd.id=pol.product_id)
					  JOIN product_template pt ON (pt.id=prd.product_tmpl_id)
					  JOIN product_uom uom ON (uom.id=pol.product_uom)
					  left JOIN kg_brand_master brand ON (pol.brand_id = brand.id)
					  left JOIN kg_project_master project ON (po.dep_project = project.id)
					  left JOIN kg_po_advance po_ad ON (po_ad.po_id = po.id)
					  left JOIN kg_moc_master moc ON (moc.id=pol.moc_id)
					  where po.state = """+po_state+""" and po.date_order >="""+date_from+""" and po.date_order <="""+date_to+' '+""" """+ supplier +""" """+ product+ """
					  """
		elif rec.status == 'pending':
			sql = """		
				SELECT
				  po.id AS po_id,
				  po.name AS po_no,
				  to_char(po.date_order,'dd/mm/yyyy') AS po_date,
				  po.date_order AS date,
				  po.note AS remark,
				  po.amount_total as total,
				  po.add_text as address,
				  po.amount_tax as taxamt,
				  pol.id as pol_id,
				  pol.product_qty AS qty,
				  pol.pending_qty AS pending_qty,
				  pol.price_unit as rate,
				  pol.kg_discount_per as disc1,
				  pol.kg_disc_amt_per as disc2,	
				  po_ad.advance_amt as po_ad_amt,			  
				  uom.name AS uom,
				  pt.name AS pro_name,
				  res.name AS su_name,
				  res.street AS str1,
				  res.zip as zip,
				  city.name as city,
				  state.name as state,
				  brand.name as brand_name,
				  po.quot_ref_no as quot_ref_no,
				  moc.name as moc
						  
				  FROM  purchase_order po
							  
				  JOIN res_partner res ON (res.id=po.partner_id)
				  left join res_city city on(city.id=res.city_id)
				  left join res_country_state state on(state.id=res.state_id)
				  JOIN purchase_order_line pol ON (pol.order_id=po.id)
				  JOIN product_product prd ON (prd.id=pol.product_id)
				  JOIN product_template pt ON (pt.id=prd.product_tmpl_id)
				  JOIN product_uom uom ON (uom.id=pol.product_uom)
				  left JOIN kg_brand_master brand ON (pol.brand_id = brand.id)
				  left JOIN kg_project_master project ON (po.dep_project = project.id)
				  left JOIN kg_po_advance po_ad ON (po_ad.po_id = po.id)
				  left JOIN kg_moc_master moc ON (moc.id=pol.moc_id)
				  where po.state='approved' and pol.pending_qty > 0 and po.date_order >="""+date_from+""" and po.date_order <="""+date_to+' '+""" """+ supplier +""" """+ product+ """
					  """
		cr.execute(sql)		
		data = cr.dictfetchall()
		
		data.sort(key=lambda data: data['po_date'])
		
		record={}
		sno=1
		wbk = xlwt.Workbook()
		style1 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz center;''borders: left thin, right thin, top thin') 
		s1=0
		
		"""adding a worksheet along with name"""
		
		sheet1 = wbk.add_sheet('Customer Details')
		s2=1
		sheet1.col(0).width = 2000
		sheet1.col(1).width = 6000
		sheet1.col(2).width = 3000
		sheet1.col(3).width = 2500
		sheet1.col(4).width = 3000
		sheet1.col(5).width = 8000
		sheet1.col(6).width = 4000
		sheet1.col(7).width = 4000
		sheet1.col(8).width = 3000
		sheet1.col(9).width = 3000
		sheet1.col(10).width = 4000
		sheet1.col(11).width = 4000
		sheet1.col(12).width = 3000
		sheet1.col(13).width = 3000
		sheet1.col(14).width = 3000
		sheet1.col(15).width = 3500
		sheet1.col(16).width = 4000
		sheet1.col(17).width = 4000
		
		""" writing field headings """
		
		sheet1.write(s1,0,"S No",style1)
		sheet1.write(s1,1,"Supplier Name",style1)
		sheet1.write(s1,2,"PO No",style1)
		sheet1.write(s1,3,"PO Date",style1)
		sheet1.write(s1,4,"Quote Ref",style1)
		sheet1.write(s1,5,"Product",style1)
		sheet1.write(s1,6,"MOC",style1)
		sheet1.write(s1,7,"Brand",style1)
		sheet1.write(s1,8,"UOM",style1)
		sheet1.write(s1,9,"Order Qty",style1)
		sheet1.write(s1,10,"Received Qty",style1)
		sheet1.write(s1,11,"Pending Qty",style1)
		sheet1.write(s1,12,"Rate(Rs)",style1)
		sheet1.write(s1,13,"Disc%",style1)
		sheet1.write(s1,14,"Tax%",style1)
		sheet1.write(s1,15,"TAT",style1)
		sheet1.write(s1,16,"Advance Amt",style1)
		sheet1.write(s1,17,"Net Amount",style1)
		
		new_data = []
		count = 0
		gr_tot = 0
		gr_total = 0
		ad_amt = 0
		gr_order_qty_total = 0
		gr_rec_qty_total = 0
		gr_pending_qty_total = 0
		gr_rate_total = 0
		pol_obj = self.pool.get('purchase.order.line')
		for pos1, item1 in enumerate(data):
			if item1['disc1'] == None:
				item1['disc1'] = 0.00
			else:
				item1['disc1'] = item1['disc1']
			if item1['disc2'] == None:
				item1['disc2'] = 0.00
			else:
				item1['disc2'] = item1['disc2']							
			delete_items = []
			po_no = item1['po_no']
			order_id = item1['po_id']
			po_date = item1['date']
			fmt = '%Y-%m-%d'
			from_date = po_date    
			to_date = date.today()
			to_date = str(to_date)
			d1 = datetime.strptime(from_date, fmt)
			d2 = datetime.strptime(to_date, fmt)
			daysDiff = str((d2-d1).days)
			item1['pending_days'] = daysDiff
			pol_rec = pol_obj.browse(cr, uid,item1['pol_id'])
			taxes = pol_rec.taxes_id
			if taxes and len(taxes) !=1:				
				tax_name = []
				for tax in taxes:
					name = tax.name
					tax_name.append(name)
					a = (', '.join('"' + item + '"' for item in tax_name))
					tax = [ item.encode('ascii') for item in ast.literal_eval(a) ]
					po_tax = ', '.join(tax)
					item1['tax'] = po_tax
			else:
				if taxes:						
					po_tax = taxes[0].name
					item1['tax'] = po_tax
			
			gr_total += item1['total']
			#ad_amt = item1['po_ad_amt']
			ad_amt = 0
			gr_order_qty_total += item1['qty']
			received_qty = item1['qty'] - item1['pending_qty']
			gr_rec_qty_total += received_qty
			gr_pending_qty_total += item1['pending_qty']
			gr_rate_total += item1['rate']
			
			for pos2, item2 in enumerate(data):
				if not pos1 == pos2:
					if item1['po_id'] == item2['po_id'] and item1['su_name'] == item2['su_name']:												
						if count == 0:
							new_data.append(item1)
							count = count + 1
						item2_2 = item2
						item2_2['su_name'] = ''
						item2_2['str1'] = ''
						item2_2['zip'] = ''
						item2_2['city'] = ''
						item2_2['state'] = ''
						item2_2['po_no'] = ''
						item2_2['po_date'] = ''
						item2_2['address']=''
						item2_2['po_ad_amt']=0
						item2_2['total']=0
						item2_2['pending_days']=0
						#~ item2_2['tax']=item1['tax']
						new_data.append(item2_2)
						delete_items.append(item2)
				
				else:
					print "Few PO have one line"
			#~ item1['po_ad_amt'] = ad_amt
		
		for ele in data:
			#~ ele['tax'] = 0
			#~ ele['po_ad_amt'] = 0
			ele['received_qty'] = ele['qty'] - ele['pending_qty']
			sheet1.write(s2,0,sno)
			sheet1.write(s2,1,ele['su_name'])
			sheet1.write(s2,2,ele['po_no'])
			sheet1.write(s2,3,ele['po_date'])
			sheet1.write(s2,4,ele['quot_ref_no'])
			sheet1.write(s2,5,ele['pro_name'])
			sheet1.write(s2,6,ele['moc'])
			sheet1.write(s2,7,ele['brand_name'])
			sheet1.write(s2,8,ele['uom'])
			sheet1.write(s2,9,ele['qty'])
			sheet1.write(s2,10,ele['received_qty'])
			sheet1.write(s2,11,ele['pending_qty'])
			sheet1.write(s2,12,ele['rate'])
			sheet1.write(s2,13,ele['disc1'])
			sheet1.write(s2,14,ele['taxamt'])
			sheet1.write(s2,15,ele['pending_days'])
			sheet1.write(s2,16,ele['po_ad_amt'])
			sheet1.write(s2,17,ele['total'])
																	
			s2+=1
			sno = sno + 1
			
			if ele['total']:	
				gr_tot += ele['total']
			else:
				pass
				
		sheet1.write(s2,3,"Total",style1)
		sheet1.write(s2,16,gr_tot,style1)
		#~ sheet1.write(s2,16,gr_tot_qty,style1)
		#~ sheet1.write(s2,18,gr_com_amt,style1)
		#~ sheet1.write(s2,19,gr_se_com_amt,style1)

		"""Parsing data as string """
		file_data=StringIO.StringIO()
		o=wbk.save(file_data)		
		"""string encode of data in wksheet"""		
		out=base64.encodestring(file_data.getvalue())
		"""returning the output xls as binary"""
		report_name = 'PO_Register_Report' + '.' + 'xls'
		
		return self.write(cr, uid, ids, {'rep_data':out, 'name':report_name,'state': 'done'},context=context)
		
kg_excel_po_register()
