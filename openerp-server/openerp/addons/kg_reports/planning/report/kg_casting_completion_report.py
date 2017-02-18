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

class jasper_casting_completion_report_print(JasperDataParser.JasperDataParser):
	def __init__(self, cr, uid, ids, data, context):		
		super(jasper_casting_completion_report_print, self).__init__(cr, uid, ids, data, context)

	def generate_data_source(self, cr, uid, ids, data, context):
		return 'records'

	def generate_ids(self, cr, uid, ids, data, context):
		return {}

	def generate_properties(self, cr, uid, ids, data, context):
		return {}
		
	def generate_parameters(self, cr, uid, ids, data, context):
		val={}
		print"data...........",data			
		from_date = data['form']['from_date']									
		to_date = data['form']['to_date']									
		printed = data['form']['printed_by'][1]		
		p_user= str(printed)		
		printed_date = data['form']['print_date']		
		date_print =  printed_date.encode('utf-8')		
		d1 = datetime.strptime(date_print,'%Y-%m-%d %H:%M:%S')	
		p_date = d1.strftime( '%d-%m-%Y %H:%M:%S')
		#~ from_pre_date = from_date.strftime( '%Y-%m-%d')
		#~ to_pre_date = to_date.strftime( '%Y-%m-%d')
		print"from_datefrom_date",from_date
		print"to_dateto_date",to_date
		print"from_pre_datefrom_pre_date",from_date,type(from_date)
		print"to_pre_dateto_pre_date",to_date,type(to_date)
		
					
			
		val['user_id'] = uid		
		val['printed_by'] = str(printed)	
		val['print_date'] = p_date			
		val['from_date'] = str(from_date)	
		val['to_date'] = str(to_date)
		
		print"val['from_date']val['from_date']",val['from_date']			
					
		return val

	def generate_records(self, cr, uid, ids, data, context):		
		pool= pooler.get_pool(cr.dbname)
		return {}

jasper_report.report_jasper('report.jasper_casting_completion_report', 'kg.casting.completion', parser=jasper_casting_completion_report_print, )

