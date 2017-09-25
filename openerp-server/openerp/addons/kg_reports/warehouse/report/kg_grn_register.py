from kg_purchase_order import JasperDataParser
from jasper_reports import jasper_report
import pooler
from datetime import date
from datetime import datetime
from datetime import timedelta
import base64
import netsvc
from osv import osv, fields
from tools.translate import _
from osv.orm import browse_record, browse_null
import os
import re
from HTMLParser import HTMLParser

class kg_grn_register(JasperDataParser.JasperDataParser):
	def __init__(self, cr, uid, ids, data, context):
		super(kg_grn_register, self).__init__(cr, uid, ids, data, context)

	def generate_data_source(self, cr, uid, ids, data, context):
		return 'records'

	def generate_ids(self, cr, uid, ids, data, context):
		return {}

	def generate_properties(self, cr, uid, ids, data, context):
		return {}
		
	def generate_parameters(self, cr, uid, ids, data, context):
		val={}
		
		where_sql = []
		po_partner = []
		gen_partner = []
		inward_type = []
		product=[]
		user_obj = self.pool.get('res.users').search(self.cr, self.uid, [('id','=',uid)])
		user_id = self.pool.get('res.users').browse(self.cr,self.uid,user_obj[0])
		user_rec = user_id.login
		
		val['dep_id']=''
		val['product']=''
		val['t_date']=''
		val['account_id']=0
		val['company_name']=1
		val['company_add']=''
		frm_rec = data['form']['from_date']
		printed_by = data['form']['printed_by']
		current_time = datetime.now()
		ist_time = current_time + timedelta(minutes = 308)
		crt_time = ist_time.strftime('%d/%m/%Y %H:%M:%S')	
		t_rec = data['form']['to_date']
		to_date =  t_rec.encode('utf-8')
		t_d1 = datetime.strptime(to_date,'%Y-%m-%d')
		t_d2 = datetime.strftime(t_d1, '%d/%m/%Y')
		#~ frm_rec =  datetime.strptime(frm_rec, '%Y-%m-%d').strftime('%d/%m/%Y')
		#~ t_rec =  datetime.strptime(t_rec, '%Y-%m-%d').strftime('%d/%m/%Y')
		val['from_date'] = frm_rec
		val['to_date'] = t_rec
		val['wiz_id'] = data['form']['id']
		val['print_date'] = crt_time
		#~ val['printed_by'] = printed_by.name
		self.cr.execute(""" (select  id  from po_grn_line where po_grn_id in (select id from kg_po_grn where grn_date >='%s' and grn_date <='%s') 
		union 
		select  id  from kg_general_grn_line where grn_id in (select id from kg_general_grn where grn_date >='%s' and grn_date <= '%s'))""" %(frm_rec,t_rec,frm_rec,t_rec))
		grn_ids = self.cr.dictfetchall()
		print "_____________________________________________________________________________",grn_ids
		if grn_ids:
			for i in grn_ids:
				print '+++++++++++++++++++++++++++++++++++++++++',i['id']
				#~ line_sub_total = self.pool.get('po.grn.line').search(cr,uid,[('id','=',i['id'])])
				line_sub_total = self.pool.get('po.grn.line').browse(cr, uid, i['id'], context=context)
				#~ print "(((((((((((((((((((((((((((((((((((((((((((((((((((((9",line_sub_total.price_subtotal
		
		return val

	def generate_records(self, cr, uid, ids, data, context):
		pool= pooler.get_pool(cr.dbname)
		return {}

jasper_report.report_jasper('report.jasper_kg_grn_register', ('kg.po.grn'), parser=kg_grn_register)

class kg_grn_register_summary(JasperDataParser.JasperDataParser):
	def __init__(self, cr, uid, ids, data, context):
		super(kg_grn_register_summary, self).__init__(cr, uid, ids, data, context)

	def generate_data_source(self, cr, uid, ids, data, context):
		return 'records'

	def generate_ids(self, cr, uid, ids, data, context):
		return {}

	def generate_properties(self, cr, uid, ids, data, context):
		return {}
		
	def generate_parameters(self, cr, uid, ids, data, context):
		val={}
		
		where_sql = []
		po_partner = []
		gen_partner = []
		inward_type = []
		product=[]
		user_obj = self.pool.get('res.users').search(self.cr, self.uid, [('id','=',uid)])
		user_id = self.pool.get('res.users').browse(self.cr,self.uid,user_obj[0])
		user_rec = user_id.login
		
		val['dep_id']=''
		val['product']=''
		val['t_date']=''
		val['account_id']=0
		val['company_name']=1
		val['company_add']=''
		frm_rec = data['form']['from_date']
		printed_by = data['form']['printed_by']
		current_time = datetime.now()
		ist_time = current_time + timedelta(minutes = 308)
		crt_time = ist_time.strftime('%d/%m/%Y %H:%M:%S')	
		t_rec = data['form']['to_date']
		to_date =  t_rec.encode('utf-8')
		t_d1 = datetime.strptime(to_date,'%Y-%m-%d')
		t_d2 = datetime.strftime(t_d1, '%d/%m/%Y')
		#~ frm_rec =  datetime.strptime(frm_rec, '%Y-%m-%d').strftime('%d/%m/%Y')
		#~ t_rec =  datetime.strptime(t_rec, '%Y-%m-%d').strftime('%d/%m/%Y')
		val['from_date'] = frm_rec
		val['to_date'] = t_rec
		val['wiz_id'] = data['form']['id']
		val['print_date'] = crt_time
		#~ val['printed_by'] = printed_by.name
		self.cr.execute(""" (select  id  from po_grn_line where po_grn_id in (select id from kg_po_grn where grn_date >='%s' and grn_date <='%s') 
		union 
		select  id  from kg_general_grn_line where grn_id in (select id from kg_general_grn where grn_date >='%s' and grn_date <= '%s'))""" %(frm_rec,t_rec,frm_rec,t_rec))
		grn_ids = self.cr.dictfetchall()
		print "_____________________________________________________________________________",grn_ids
		if grn_ids:
			for i in grn_ids:
				print '+++++++++++++++++++++++++++++++++++++++++',i['id']
				#~ line_sub_total = self.pool.get('po.grn.line').search(cr,uid,[('id','=',i['id'])])
				line_sub_total = self.pool.get('po.grn.line').browse(cr, uid, i['id'], context=context)
				#~ print "(((((((((((((((((((((((((((((((((((((((((((((((((((((9",line_sub_total.price_subtotal
		
		return val
	
	def generate_records(self, cr, uid, ids, data, context):
		print"datadata----------",data
		pool= pooler.get_pool(cr.dbname)
		return {}

jasper_report.report_jasper('report.jasper_kg_grn_register_summary', ('kg.po.grn'), parser=kg_grn_register_summary)
