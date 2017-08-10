from kg_reports import JasperDataParser
from jasper_reports import jasper_report
import pooler
import time, datetime
import calendar
import base64
import netsvc
from osv import osv, fields
from tools.translate import _
from osv.orm import browse_record, browse_null
import os
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

class jasper_supplied_order_report_print(JasperDataParser.JasperDataParser):
	def __init__(self, cr, uid, ids, data, context):		
		super(jasper_supplied_order_report_print, self).__init__(cr, uid, ids, data, context)

	def generate_data_source(self, cr, uid, ids, data, context):
		return 'records'

	def generate_ids(self, cr, uid, ids, data, context):
		return {}

	def generate_properties(self, cr, uid, ids, data, context):
		return {}
		
	def generate_parameters(self, cr, uid, ids, data, context):
		val={}
		print"data...........",data			
		wiz_id = data['form']['id']									
		printed = data['form']['printed_by'][1]
		from_date = data['form']['from_date']
		to_date = data['form']['to_date']
		
		p_user= str(printed)		
		printed_date = data['form']['print_date']		
		date_print =  printed_date.encode('utf-8')
		date_fo =  from_date.encode('utf-8')
		date_to =  to_date.encode('utf-8')
		
		d1 = datetime.strptime(date_print,'%Y-%m-%d %H:%M:%S')
		s1 = datetime.strptime(date_fo,'%Y-%m-%d')
		s2 = datetime.strptime(date_to,'%Y-%m-%d')
		p_date = d1.strftime( '%d-%m-%Y %H:%M:%S')	
		date_form = s1.strftime( '%d-%m-%Y')	
		date_to = s2.strftime( '%d-%m-%Y')	
			
		val['user_id'] = uid		
		val['printed_by'] = str(printed)	
		val['print_date'] = p_date
		val['from_date'] = str(from_date)
		val['to_date'] = str(to_date)
		
		val['wiz_id'] = wiz_id				
		val['date_from'] = str(date_form)
		val['date_to'] = str(date_to)
		
		
		return val

	def generate_records(self, cr, uid, ids, data, context):		
		pool= pooler.get_pool(cr.dbname)
		return {}

jasper_report.report_jasper('report.jasper_supplied_order_report', 'kg.supplied.order.print', parser=jasper_supplied_order_report_print, )

