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

class onscreen_spare_budgetary_report(JasperDataParser.JasperDataParser):
	def __init__(self, cr, uid, ids, data, context):
		
		super(onscreen_spare_budgetary_report, self).__init__(cr, uid, ids, data, context)
	
	def generate_data_source(self, cr, uid, ids, data, context):
		return 'records'
	
	def generate_ids(self, cr, uid, ids, data, context):
		return {}
	
	def generate_properties(self, cr, uid, ids, data, context):
		return {}
	
	def generate_parameters(self, cr, uid, ids, data, context):
		val={}	
		user_rec = self.pool.get('res.users').browse(cr,uid,uid)
		
		if user_rec.signature:
			signature = user_rec.signature
			myfile = '/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_crm_offer/img/SIGN.jpg'
			if os.path.isfile(myfile) == True:
				os.remove(myfile)
			else:
				pass
			filepath = os.path.join('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_crm_offer/img','SIGN.jpg')
			f = open(filepath, "a")
			f.write(signature.decode('base64'))
			val['sign'] = '/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_crm_offer/img/SIGN.jpg'
		else:
			val['sign'] = ''
			
		val['offer_id'] = ids[0]
		val['printed_by'] = user_rec.name
		print "val....................", val
		
		return val
	
	def generate_records(self, cr, uid, ids, data, context):
		pool= pooler.get_pool(cr.dbname)		
		return {}
	
jasper_report.report_jasper('report.onscreen_spare_budgetary_report', 'kg.crm.offer', parser=onscreen_spare_budgetary_report)
