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

class onscreen_purchase_order_report(JasperDataParser.JasperDataParser):
	
	def __init__(self, cr, uid, ids, data, context):
		super(onscreen_purchase_order_report, self).__init__(cr, uid, ids, data, context)
	
	def generate_data_source(self, cr, uid, ids, data, context):
		return 'records'
	
	def generate_ids(self, cr, uid, ids, data, context):
		return {}
	
	def generate_properties(self, cr, uid, ids, data, context):
		return {}
	
	def generate_parameters(self, cr, uid, ids, data, context):
		val={}
		rec = self.pool.get('purchase.order').browse(cr,uid,ids[0])

		
		if rec.state == 'confirmed':
			if rec.confirmed_by.signature:
				confirmed_signature = rec.confirmed_by.scaned_signature
				myfile = '/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_purchase_order/images/Confirmed.jpg'
				if os.path.isfile(myfile) == True:
					os.remove(myfile)
				else:
					pass
				filepath = os.path.join('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_purchase_order/images','Confirmed.jpg')
				f = open(filepath, "a")
				f.write(confirmed_signature.decode('base64'))
			else:
				pass
		elif rec.state == 'verified':
			if rec.confirmed_by.signature:
				confirmed_signature = rec.confirmed_by.scaned_signature
				myfile = '/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_purchase_order/images/Confirmed.jpg'
				if os.path.isfile(myfile) == True:
					os.remove(myfile)
				else:
					pass
				filepath = os.path.join('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_purchase_order/images','Confirmed.jpg')
				f = open(filepath, "a")
				f.write(confirmed_signature.decode('base64'))
			else:
				pass
			if rec.verified_by.signature:
				verified_signature = rec.verified_by.scaned_signature
				myfile = '/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_purchase_order/images/Verified.jpg'
				if os.path.isfile(myfile) == True:
					os.remove(myfile)
				else:
					pass
				filepath = os.path.join('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_purchase_order/images','Verified.jpg')
				f = open(filepath, "a")
				f.write(verified_signature.decode('base64'))
			else:
				pass
		elif rec.state == 'approved':
			if rec.confirmed_by.signature:
				confirmed_signature = rec.confirmed_by.scaned_signature
				myfile = '/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_purchase_order/images/Confirmed.jpg'
				if os.path.isfile(myfile) == True:
					os.remove(myfile)
				else:
					pass
				filepath = os.path.join('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_purchase_order/images','Confirmed.jpg')
				f = open(filepath, "a")
				f.write(confirmed_signature.decode('base64'))
			else:
				pass
			if rec.verified_by.signature and rec.approval_flag == True:
				verified_signature = rec.verified_by.scaned_signature
				myfile = '/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_purchase_order/images/Verified.jpg'
				if os.path.isfile(myfile) == True:
					os.remove(myfile)
				else:
					pass
				filepath = os.path.join('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_purchase_order/images','Verified.jpg')
				f = open(filepath, "a")
				f.write(verified_signature.decode('base64'))
			else:
				pass
			if rec.approved_by.signature:
				approved_signature = rec.approved_by.scaned_signature
				myfile = '/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_purchase_order/images/MD.jpg'
				if os.path.isfile(myfile) == True:
					os.remove(myfile)
				else:
					pass
				filepath = os.path.join('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_purchase_order/images','MD.jpg')
				f = open(filepath, "a")
				f.write(approved_signature.decode('base64'))
			else:
				pass
		
		val['po_id'] = ids[0]
		
		return val
	
	def generate_records(self, cr, uid, ids, data, context):
		pool= pooler.get_pool(cr.dbname)
		return {}
	
jasper_report.report_jasper('report.onscreen_purchase_order_report', 'purchase.order', parser=onscreen_purchase_order_report)
