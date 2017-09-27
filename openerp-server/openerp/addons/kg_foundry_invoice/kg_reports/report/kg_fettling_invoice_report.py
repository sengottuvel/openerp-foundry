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

class jasper_fettling_invoice_report_print(JasperDataParser.JasperDataParser):
	def __init__(self, cr, uid, ids, data, context):		
		super(jasper_fettling_invoice_report_print, self).__init__(cr, uid, ids, data, context)

	def generate_data_source(self, cr, uid, ids, data, context):
		return 'records'

	def generate_ids(self, cr, uid, ids, data, context):
		return {}

	def generate_properties(self, cr, uid, ids, data, context):
		return {}
		
	def generate_parameters(self, cr, uid, ids, data, context):
		val={}
		print"data...........",data			
		print"data...........",data			
		wiz_id = data['form']['id']									
		printed = data['form']['printed_by'][1]
		from_date = data['form']['from_date']		
		to_date = data['form']['to_date']		
		
		p_user= str(printed)		
		printed_date = data['form']['print_date']		
		date_print =  printed_date.encode('utf-8')
		date_form =  from_date.encode('utf-8')			
		date_to =  to_date.encode('utf-8')			
		d1 = datetime.strptime(date_print,'%Y-%m-%d %H:%M:%S')
		s1 = datetime.strptime(date_form,'%Y-%m-%d')		
		s2 = datetime.strptime(date_to,'%Y-%m-%d')		
		p_date = d1.strftime( '%d-%m-%Y %H:%M:%S')	
		date_from_form = s1.strftime( '%Y-%m-%d')	
		date_to_form = s2.strftime( '%Y-%m-%d')	
		display_from_date = s1.strftime( '%d-%m-%Y')	
		display_to_date = s2.strftime( '%d-%m-%Y')	
		
			
		val['user_id'] = uid		
		val['printed_by'] = str(printed)	
		val['print_date'] = p_date		
		val['wiz_id'] = wiz_id				
		val['from_date'] = str(date_from_form)
		val['to_date'] = str(date_to_form)
		val['display_from_date'] = str(display_from_date)	
		val['display_to_date'] = str(display_to_date)	
		
		return val

	def generate_records(self, cr, uid, ids, data, context):		
		pool= pooler.get_pool(cr.dbname)
		return {}

jasper_report.report_jasper('report.jasper_fettling_invoice_report', 'kg.fettling.invoice.print', parser=jasper_fettling_invoice_report_print, )

