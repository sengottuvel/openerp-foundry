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

class jasper_workorder_report_print(JasperDataParser.JasperDataParser):
	def __init__(self, cr, uid, ids, data, context):		
		super(jasper_workorder_report_print, self).__init__(cr, uid, ids, data, context)

	def generate_data_source(self, cr, uid, ids, data, context):
		return 'records'

	def generate_ids(self, cr, uid, ids, data, context):
		return {}

	def generate_properties(self, cr, uid, ids, data, context):
		return {}
		
	def generate_parameters(self, cr, uid, ids, data, context):
		val={}
		
		#~ print"data...........",data			
		#~ wiz_id = data['form']['id']									
		printed = data['form']['user_id'][1]		
		p_user= str(printed)		
		val['user_id'] = uid		
		val['printed_by'] = p_user
		if data['form']['attachment']:
			val['attach_1'] = 'attachment_1.png'
		else:
			val['attach_1'] = ''
		if data['form']['attachment_1']:
			val['attach_2'] = 'attachment_2.png'
		else:
			val['attach_2'] = ''
		print "data['form']['wo_id'][0]]",data['form']['wo_id'][0]
		## Getting Work Order ids ###
		
		val['wo_line_ids'] = data['form']['wo_id'][0]
				
		return val

	def generate_records(self, cr, uid, ids, data, context):		
		pool= pooler.get_pool(cr.dbname)
		return {}

jasper_report.report_jasper('report.jasper_workorder_report', 'kg.workorder.report', parser=jasper_workorder_report_print, )

