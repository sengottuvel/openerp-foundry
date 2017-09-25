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
import ast
logger = logging.getLogger('server')

class kg_excel_po_register(osv.osv):
	
	_name = 'kg.excel.po.register'
	_order = 'creation_date desc'
	
	_columns = {
		
		'creation_date': fields.date('Creation Date', readonly=True),
		'product_id':fields.many2many('product.product','kg_ex_po_rep_wiz','report_id','product_id','Product Name'),
		'supplier':fields.many2many('res.partner','kg_ex_po_rep_sup','report_id','supplier_id','Supplier'),
		'date_from': fields.date("Start Date",required=True),
		'date_to': fields.date("End Date",required=True),		
		'status': fields.selection([('approved', 'Approved'),('cancelled','Cancelled'),('pending','Pending')], "Status"),
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
					  distinct po.id AS po_id,
					  po.name AS po_no,
					  to_char(po.date_order,'dd/mm/yyyy') AS po_date,
					  po.date_order AS date,
					  po.note AS remark,
					  po.amount_total as total,
					  po.add_text as address,
					  pol.product_tax_amt as taxamt,
					  pol.id as pol_id,
					  pol.product_qty AS qty,
					  pol.pending_qty AS pending_qty,
					  pol.price_unit * pol.product_qty as rate,
					  case when pol.kg_discount_per = 0 then pol.kg_discount else (pol.price_unit * pol.product_qty)*pol.kg_discount_per/100 end as discount,
					  pol.kg_discount_per as disc1,
					  pol.kg_discount as disc2,	
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
					  left JOIN kg_moc_master moc ON (moc.id=pol.moc_id)
					  where po.state = """+po_state+""" and po.date_order >="""+date_from+""" and po.date_order <="""+date_to+' '+""" """+ supplier +""" """+ product+ """
					  order by po.date_order """
		elif rec.status == 'pending':
			sql = """
				SELECT
				  distinct po.id AS po_id,
				  po.name AS po_no,
				  to_char(po.date_order,'dd/mm/yyyy') AS po_date,
				  po.date_order AS date,
				  po.note AS remark,
				  po.amount_total as total,
				  po.add_text as address,
				  pol.product_tax_amt as taxamt,
				  pol.id as pol_id,
				  pol.product_qty AS qty,
				  pol.pending_qty AS pending_qty,
				  pol.price_unit * pol.product_qty as rate,
				  case when pol.kg_discount_per = 0 then pol.kg_discount else (pol.price_unit * pol.product_qty)*pol.kg_discount_per/100 end as discount,
				  pol.kg_discount_per as disc1,
				  pol.kg_discount as disc2,	
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
				  left JOIN kg_moc_master moc ON (moc.id=pol.moc_id)
				  where po.state='approved' and pol.pending_qty > 0 and po.date_order >="""+date_from+""" and po.date_order <="""+date_to+' '+""" """+ supplier +""" """+ product+ """
				  order by po.date_order  """
		cr.execute(sql)		
		data = cr.dictfetchall()
		
		data.sort(key=lambda data: data['date'])		
		record={}
		sno=1
		wbk = xlwt.Workbook()
		style1 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz center,vertical center;''borders: left thin, right thin, top thin, bottom thin')
		style2 = xlwt.easyxf('font: height 200,color_index black;' 'align: horiz left;''borders: left thin, right thin, top thin, bottom thin')
		style3 = xlwt.easyxf('font: height 200,color_index black;' 'align: horiz right;''borders: left thin, right thin, top thin, bottom thin')
		style4 = xlwt.easyxf('font: bold on,height 240,color_index 0x95;' 'align: horiz center,vertical center;''borders: left thin, right thin, top thin ,bottom thin') 
		style5 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz right,vertical center;''borders: left thin, right thin, top thin, bottom thin')

		s1=0
		
		"""adding a worksheet along with name"""
		
		sheet1 = wbk.add_sheet('PO Register')
		s2=5
		sheet1.col(0).width = 1500
		sheet1.col(1).width = 3000
		sheet1.col(2).width = 2500
		sheet1.col(3).width = 3000
		sheet1.col(4).width = 15000
		sheet1.col(5).width = 9000
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
		
		date_from = datetime.strptime(rec.date_from, '%Y-%m-%d').strftime('%d/%m/%Y')
		date_to = datetime.strptime(rec.date_to, '%Y-%m-%d').strftime('%d/%m/%Y')
		
		sheet1.write_merge(0, 3, 0, 16,"SAM TURBO INDUSTRY PRIVATE LIMITED \n Avinashi Road, Neelambur,\n Coimbatore - 641062 \n Tel:3053555, 3053556,Fax : 0422-3053535",style4)
		sheet1.row(0).height = 450
		sheet1.write_merge(4, 4, 0, 16,"PO REGISTER - "+ date_from + " "+ "TO "+date_to,style4)
		sheet1.insert_bitmap('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_crm_offer/img/sam.bmp',0,4)
		
		""" writing field headings """
		
		sheet1.write(s2,0,"S No",style1)
		sheet1.write(s2,1,"PO No",style1)
		sheet1.write(s2,2,"PO Date",style1)
		sheet1.write(s2,3,"Quote Ref",style1)
		sheet1.write(s2,4,"Supplier Name",style1)
		sheet1.write(s2,5,"Product",style1)
		sheet1.write(s2,6,"MOC",style1)
		sheet1.write(s2,7,"Brand",style1)
		sheet1.write(s2,8,"UOM",style1)
		sheet1.write(s2,9,"Order Qty",style1)
		sheet1.write(s2,10,"Received Qty",style1)
		sheet1.write(s2,11,"Pending Qty",style1)
		sheet1.write(s2,12,"Unit Price",style1)
		sheet1.write(s2,13,"Discount",style1)
		sheet1.write(s2,14,"GST",style1)
		sheet1.write(s2,15,"Net Amount",style1)
		sheet1.write(s2,16,"TAT",style1)
		
		new_data = []
		count = 0
		gr_tot = 0
		gr_tax_tot = 0
		gr_total = 0
		ad_amt = 0
		gr_order_qty_total = 0
		gr_rec_qty_total = 0
		gr_pending_qty_total = 0
		gr_rate_total = 0
		disc_amt = 0
		pol_obj = self.pool.get('purchase.order.line')
		for pos1, item1 in enumerate(data):
			if item1['disc1'] == None:
				disc_amt = 0.00
			else:
				disc_amt = (item1['rate']*item1['disc1'])/100
			if item1['disc2'] == None:
				disc_amt = 0.00
			else:
				disc_amt = item1['disc2']							
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
			s2+=1	
			print "disc_amtdisc_amtdisc_amtdisc_amtdisc_amtdisc_amtdisc_amt",disc_amt
			ele['received_qty'] = ele['qty'] - ele['pending_qty']
			sheet1.write(s2,0,sno,style2)
			sheet1.write(s2,1,ele['po_no'],style2)
			sheet1.write(s2,2,ele['po_date'],style2)
			sheet1.write(s2,3,ele['quot_ref_no'],style2)
			sheet1.write(s2,4,ele['su_name'],style2)
			sheet1.write(s2,5,ele['pro_name'],style2)
			sheet1.write(s2,6,ele['moc'],style2)
			sheet1.write(s2,7,ele['brand_name'],style2)
			sheet1.write(s2,8,ele['uom'],style2)
			sheet1.write(s2,9,ele['qty'],style3)
			sheet1.write(s2,10,ele['received_qty'],style3)
			sheet1.write(s2,11,ele['pending_qty'],style3)
			sheet1.write(s2,12,ele['rate'],style3)
			sheet1.write(s2,13,ele['discount'],style3)
			sheet1.write(s2,14,ele['taxamt'],style3)
			sheet1.write(s2,15,ele['total'],style3)
			sheet1.write(s2,16,ele['pending_days'],style3)
			
			
			sno = sno + 1
			
			if ele['total']:	
				gr_tot += ele['total']
			else:
				pass
			if ele['taxamt']:
				gr_tax_tot += ele['taxamt']
			else:
				pass
		
		s2=s2+1
		sheet1.write_merge(s2, s2, 0, 13,"Total  ",style5)
		sheet1.write(s2,14,gr_tax_tot,style3)
		sheet1.write(s2,15,gr_tot,style3)
		sheet1.write(s2,16,"",style3)
		
		
		"""Parsing data as string """
		file_data=StringIO.StringIO()
		o=wbk.save(file_data)		
		"""string encode of data in wksheet"""		
		out=base64.encodestring(file_data.getvalue())
		"""returning the output xls as binary"""
		report_name = 'PO_Register_Report' + '.' + 'xls'
		
		return self.write(cr, uid, ids, {'rep_data':out, 'name':report_name,'state':'done'},context=context)
		
kg_excel_po_register()
