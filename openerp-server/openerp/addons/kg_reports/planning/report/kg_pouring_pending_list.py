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

class jasper_pouring_pending_list_report_print(JasperDataParser.JasperDataParser):
	def __init__(self, cr, uid, ids, data, context):		
		super(jasper_pouring_pending_list_report_print, self).__init__(cr, uid, ids, data, context)

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
		as_date = data['form']['as_on_date']
		if data['form']['category'] :
			pro_category = data['form']['category']
		else:
			pro_category = 'all'
		p_user= str(printed)		
		printed_date = data['form']['print_date']		
		date_print =  printed_date.encode('utf-8')
		date_fo =  as_date.encode('utf-8')
		d1 = datetime.strptime(date_print,'%Y-%m-%d %H:%M:%S')
		s1 = datetime.strptime(date_fo,'%Y-%m-%d')
		p_date = d1.strftime( '%d-%m-%Y %H:%M:%S')	
		date_form = s1.strftime( '%d-%m-%Y')	
			
		val['user_id'] = uid		
		val['printed_by'] = str(printed)	
		val['print_date'] = p_date
		val['as_on_date'] = str(as_date)
		val['category'] = str(pro_category)		
		val['wiz_id'] = wiz_id				
		val['date_form'] = str(date_form)				
		return val

	def generate_records(self, cr, uid, ids, data, context):		
		pool= pooler.get_pool(cr.dbname)
		return {}

jasper_report.report_jasper('report.jasper_pouring_pending_report', 'kg.pouring.pending.print', parser=jasper_pouring_pending_list_report_print, )

