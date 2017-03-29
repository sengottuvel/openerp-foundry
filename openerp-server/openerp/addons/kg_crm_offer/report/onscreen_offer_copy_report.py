from kg_purchase_order import JasperDataParser
from jasper_reports import jasper_report
import pooler
import time, datetime
import base64
import netsvc
from osv import osv, fields
from tools.translate import _
from osv.orm import browse_record, browse_null
import os

class onscreen_offer_copy_report(JasperDataParser.JasperDataParser):
	def __init__(self, cr, uid, ids, data, context):
		
		super(onscreen_offer_copy_report, self).__init__(cr, uid, ids, data, context)
	
	def generate_data_source(self, cr, uid, ids, data, context):
		return 'records'
	
	def generate_ids(self, cr, uid, ids, data, context):
		return {}
	
	def generate_properties(self, cr, uid, ids, data, context):
		return {}
	
	def generate_parameters(self, cr, uid, ids, data, context):
		val={}		
		val['offer_id'] = ids[0]
		print "val....................", val
		
		return val
	
	def generate_records(self, cr, uid, ids, data, context):
		pool= pooler.get_pool(cr.dbname)		
		return {}
	
jasper_report.report_jasper('report.onscreen_offer_copy_report', 'kg.crm.offer', parser=onscreen_offer_copy_report)
