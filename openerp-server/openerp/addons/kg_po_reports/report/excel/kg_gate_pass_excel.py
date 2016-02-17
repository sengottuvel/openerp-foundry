import time
from lxml import etree
from osv import fields, osv
from tools.translate import _
import pooler
import logging
import netsvc
import datetime as lastdate
import calendar
import base64
from osv import fields,osv
from tools.translate import _
import time
import xlwt 
  
import cStringIO
from web.controllers.main import ExcelExport
from web.controllers.main import Export
logger = logging.getLogger('server')


class kg_gate_pass_excel(osv.osv):
		
	_name = 'kg.gate.pass.excel'
	_columns = {
		
		'dep_id':fields.many2many('kg.depmaster','gate_pass_regg','wiz_id','dep_id','Department Name'),
		'product_type': fields.selection([('consu', 'Consumable Items'),('cap','Capital Goods'),('service','Service Items')], 'Product Type'),				
		'product':fields.many2many('product.product','gate_pass_reg_productt','product_wiz_id','product_dep_id','Product'),
		'company_id': fields.many2one('res.company', 'Company Name'),
		'print_date': fields.datetime('Creation Date', readonly=True),
		'printed_by': fields.many2one('res.users','Printed By',readonly=True),
		'status': fields.selection([('delivered', 'Delivered'),('cancelled','Cancelled')], "Status"),
		'date_from': fields.date("Start Date"),
		'date_to': fields.date("End Date"),
		'rep_data':fields.binary("File"),	
		'state': fields.selection([('draft', 'Draft'),('done','Done')], 'Status', readonly=True),
		'data': fields.char('Data', readonly=True),
		"name":fields.char("Filename",64,readonly=True),
	}
	
	_defaults = {
		
		'state':'draft',
		'date_from': time.strftime('%Y-%m-%d'),
		'date_to': time.strftime('%Y-%m-%d'),
		
	}
	def gate_pass_xls(self, cr, uid, ids, context=None):
		
		import StringIO
		import base64
		
		try:
			import xlwt
		except:
		   raise osv.except_osv('Warning !','Please download python xlwt module from\nhttp://pypi.python.org/packages/source/x/xlwt/xlwt-0.7.2.tar.gz\nand install it')
		rec = self.browse(cr,uid,ids[0])
		
		department = []
		product = []
		where_sql = []
		if rec.dep_id:
			sql = """select dep_id from gate_pass_regg where wiz_id=%s"""%(rec.id)
			cr.execute(sql)
			dep = cr.dictfetchall()
			print "-------------------------->",dep
			
			for ids1 in dep:
				department.append("pass.dep_id = %s "%(ids1['dep_id']))			
		if rec.product:
			sql = """select product_dep_id from gate_pass_reg_productt where product_wiz_id=%s"""%(rec.id)
			cr.execute(sql)
			pro = cr.dictfetchall()
			print "-------------------------->",pro
			for ids2 in pro:
				product.append("prd.id = %s"%(ids2['product_dep_id']))
		print "---------------product>",product	
		if department:
			department = 'and ('+' or '.join(department)
			department =  department+')'
			
		else:
			department = ''
			
		if product:
			
			product = 'and ('+' or '.join(product)
			product =  product+')'
		else:
			product=''			
		
		
		
		date_frm = rec.date_from
		date_t = rec.date_to
		date_from = "'"+date_frm+"'"
		date_to = 	"'"+date_t+"'"
			
		print "date_from...........",date_from
		print "date_to.........",date_to	
		
		if rec.status == 'delivered':
			pass_state = 'done'
		elif rec.status == 'cancelled':
			pass_state = 'cancel'
		else:
			pass_state = 'done'	
		print "date_from...........",type(date_from)
		print "date_to.........",type(date_to)
		print "date_to.........",type(pass_state)
			
		if not rec.status or rec.status == 'delivered' or rec.status == 'cancelled':
		
			sql="""
			
				  SELECT			  
				  pass.id AS pass_id,
				  to_char(pass.date,'dd/mm/yyyy') AS pass_date,
				  pass.name AS pass_number,
				  dep.dep_name AS dep_name,
				  prd.name_template AS product_name,
				  uom.name AS uom,
				  pass_line.qty AS qty,
				 
				  pass_line.ser_no AS ser_no,
				  pass_line.id AS pass_line_id,
				  out.name AS out_type,
				  ser_ind_line.service_id AS indent,
				  ser_ind.name As ser_ind_name,
				  to_char(ser_ind.date, 'dd/mm/yyyy') AS ser_ind_date,
				  partner.name as supplier_name,
				  pass.partner_id as supplier_id,
				  brand.name as brand_name
							  
				  FROM  kg_gate_pass pass

				  LEFT JOIN res_partner partner ON (pass.partner_id=partner.id)
				  LEFT JOIN kg_gate_pass_line pass_line ON (pass_line.gate_id=pass.id)
				  LEFT JOIN kg_depmaster dep ON (dep.id=pass.dep_id)
				  LEFT JOIN product_uom uom ON (uom.id=pass_line.uom)
				  LEFT JOIN product_product prd ON (prd.id=pass_line.product_id)
				  LEFT JOIN kg_outwardmaster out ON (out.id = pass.out_type)
				  LEFT JOIN kg_service_indent_line ser_ind_line ON (ser_ind_line.id = pass_line.si_line_id)
				  LEFT JOIN kg_service_indent ser_ind ON (ser_ind.id = ser_ind_line.service_id)
				  LEFT JOIN kg_brand_master brand ON (pass_line.brand_id = brand.id)

				  where pass.state= '"""+pass_state+"""' and pass.date >= """+date_from+""" and pass.date <="""+date_to+""" """+ department + product + """
				  order by pass.date"""  
			
		elif rec.status == 'pending': 
			sql="""
			
				  SELECT			  
				  pass.id AS pass_id,
				  to_char(pass.date,'dd/mm/yyyy') AS pass_date,
				  pass.name AS pass_number,
				  dep.dep_name AS dep_name,
				  prd.name_template AS product_name,
				  uom.name AS uom,
				  pass_line.qty AS qty,
				 
				  pass_line.ser_no AS ser_no,
				  pass_line.id AS pass_line_id,
				  out.name AS out_type,
				  ser_ind_line.service_id AS indent,
				  ser_ind.name As ser_ind_name,
				  to_char(ser_ind.date, 'dd/mm/yyyy') AS ser_ind_date,
				  partner.name as supplier_name,
				  pass.partner_id as supplier_id,
				  brand.name as brand_name
							  
				  FROM  kg_gate_pass pass

				  LEFT JOIN res_partner partner ON (pass.partner_id=partner.id)
				  LEFT JOIN kg_gate_pass_line pass_line ON (pass_line.gate_id=pass.id)
				  LEFT JOIN kg_depmaster dep ON (dep.id=pass.dep_id)
				  LEFT JOIN product_uom uom ON (uom.id=pass_line.uom)
				  LEFT JOIN product_product prd ON (prd.id=pass_line.product_id)
				  LEFT JOIN kg_outwardmaster out ON (out.id = pass.out_type)
				  LEFT JOIN kg_service_indent_line ser_ind_line ON (ser_ind_line.id = pass_line.si_line_id)
				  LEFT JOIN kg_service_order so ON (so.gp_id = pass.id)
				  LEFT JOIN kg_service_indent ser_ind ON (ser_ind.id = ser_ind_line.service_id)
				  LEFT JOIN kg_brand_master brand ON (pass_line.brand_id = brand.id)

				  where pass.state='done' and so.gp_id is not NULL and pass.date >= """+date_from+""" and pass.date <="""+date_to+""" """+ department + product + """
				  order by pass.date"""
		elif rec.status == 'closed': 
			sql="""
			
				  SELECT			  
				  pass.id AS pass_id,
				  to_char(pass.date,'dd/mm/yyyy') AS pass_date,
				  pass.name AS pass_number,
				  dep.dep_name AS dep_name,
				  prd.name_template AS product_name,
				  uom.name AS uom,
				  pass_line.qty AS qty,
				 
				  pass_line.ser_no AS ser_no,
				  pass_line.id AS pass_line_id,
				  out.name AS out_type,
				  ser_ind_line.service_id AS indent,
				  ser_ind.name As ser_ind_name,
				  to_char(ser_ind.date, 'dd/mm/yyyy') AS ser_ind_date,
				  partner.name as supplier_name,
				  pass.partner_id as supplier_id,
				  brand.name as brand_name
							  
				  FROM  kg_gate_pass pass

				  LEFT JOIN res_partner partner ON (pass.partner_id=partner.id)
				  LEFT JOIN kg_gate_pass_line pass_line ON (pass_line.gate_id=pass.id)
				  LEFT JOIN kg_depmaster dep ON (dep.id=pass.dep_id)
				  LEFT JOIN product_uom uom ON (uom.id=pass_line.uom)
				  LEFT JOIN product_product prd ON (prd.id=pass_line.product_id)
				  LEFT JOIN kg_outwardmaster out ON (out.id = pass.out_type)
				  LEFT JOIN kg_service_indent_line ser_ind_line ON (ser_ind_line.id = pass_line.si_line_id)
				  LEFT JOIN kg_service_order so ON (so.gp_id = pass.id)
				  LEFT JOIN kg_service_indent ser_ind ON (ser_ind.id = ser_ind_line.service_id)
				  LEFT JOIN kg_brand_master brand ON (pass_line.brand_id = brand.id)

				  where pass.state='done' and so.state='approved' and so.gp_id is not NULL and pass.date >= """+date_from+""" and pass.date <="""+date_to+""" """+ department + product + """
				  order by pass.date"""
		cr.execute(sql)
		data = cr.dictfetchall()
		print "data ::::::::::::::=====>>>>", data
				
		record={}
		
		wbk = xlwt.Workbook()
		style1 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz center;''borders: left thin, right thin, top thin') 
		s1=0
		
		"""adding a worksheet along with name"""
		
		sheet1 = wbk.add_sheet('Gate Pass Register')
		s2=1
		sheet1.col(0).width = 2000
		sheet1.col(1).width = 5000
		sheet1.col(2).width = 8000
		sheet1.col(3).width = 12000
		sheet1.col(4).width = 3000
		sheet1.col(5).width = 4000
		sheet1.col(6).width = 3000
		sheet1.col(7).width = 3000
		sheet1.col(8).width = 5000
		sheet1.col(9).width = 5000
		sheet1.col(10).width = 5000
	
		
			
		
		
		""" writing field headings """
		
		sheet1.write(s1,0,"S.No",style1)
		sheet1.write(s1,1,"Pass No-Date",style1)
		sheet1.write(s1,2,"Supplier",style1)
		sheet1.write(s1,3,"Item Name ",style1)
		sheet1.write(s1,4,"Serial No",style1)
		sheet1.write(s1,5,"Brand",style1)
		sheet1.write(s1,6,"UOM",style1)
		sheet1.write(s1,7,"Quantity",style1)
		sheet1.write(s1,8,"Indent No-Date",style1)
		sheet1.write(s1,9,"Department Name",style1)
		sheet1.write(s1,10,"Outward Type",style1)
		
		
		
		"""writing data according to query and filteration in worksheet"""
		
		new_data = []
		count = 0
		gr_total = 0.0
		qty_total = 0.0
		rate_total = 0.0
		sno=1
		for pos1, item1 in enumerate(data):
			delete_items = []
			
			qty_total += item1['qty']
			item1['gr_qty_total'] = qty_total		
			
			for pos2, item2 in enumerate(data):
				if not pos1 == pos2:
					if item1['pass_id'] == item2['pass_id'] and item1['pass_date'] == item2['pass_date']:			
						if count == 0:
							new_data.append(item1)
							print "new_data -------------------------------->>>>", new_data
							count = count + 1
						item2_2 = item2
						item2_2['pass_number'] = ''
						item2_2['pass_date'] = ''
						item2_2['supplier_name'] = ''

						
						new_data.append(item2_2)
						print "new_data 2222222222222222", new_data
						delete_items.append(item2)
						print "delete_items _____________________>>>>>", delete_items
				else:
					print "Few Gate Pass have one line"
					
		for item in data:
			if item['pass_number'] and item['pass_date']:
				
				a=item['pass_number'] +' '+'-' + ' '+ item['pass_date'] 
			else:
				a=''
			
			if item['ser_ind_name']	and item['ser_ind_date']:
				
				b=item['ser_ind_name']+' '+'-' + ' '+ item['ser_ind_date'] 
				
			else:
				b=''	
				
			sheet1.write(s2,0,sno)
			sheet1.write(s2,1,a)
			sheet1.write(s2,2,item['supplier_name'])
			sheet1.write(s2,3,item['product_name'])
			sheet1.write(s2,4,item['ser_no'])
			sheet1.write(s2,5,item['brand_name'])
			sheet1.write(s2,6,item['uom'])
			sheet1.write(s2,7,item['qty'])
			sheet1.write(s2,8,b)
			sheet1.write(s2,9,item['dep_name'])
			sheet1.write(s2,10,item['out_type'])
																											
			s2+=1
			sno = sno + 1	
			
		
		"""Parsing data as string """
		file_data=StringIO.StringIO()
		o=wbk.save(file_data)		
		"""string encode of data in wksheet"""		
		out=base64.encodestring(file_data.getvalue())
		"""returning the output xls as binary"""
		
		report_name = 'Gatepass_Register' + '.' + 'xls'
		return self.write(cr, uid, ids, {'rep_data':out, 'name':report_name,'state': 'done'},context=context)
		



		
	def unlink(self, cr, uid, ids,context=None):
		for rec in self.browse(cr, uid, ids):
			if rec.state == 'done':
				raise osv.except_osv(_('Unable to Delete !'),_('You can not delete Done state reports !!'))
		return super(kg_partner_list, self).unlink(cr, uid, ids, context)
	
			
kg_gate_pass_excel()
