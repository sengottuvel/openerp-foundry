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
		rec = self.pool.get('kg.work.order').browse(cr,uid,data['form']['wo_id'][0])
		common_file = '/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_reports/planning/images/'
		myfile = common_file+'attachment_1.png'
		if os.path.isfile(myfile) == True:
			os.remove(myfile)
		else:
			pass
		myfile = common_file+'attachment_2.png'
		if os.path.isfile(myfile) == True:
			os.remove(myfile)
		else:
			pass
		myfile = common_file+'attachment_3.png'
		if os.path.isfile(myfile) == True:
			os.remove(myfile)
		else:
			pass			
		
		if rec.id:
			for wo_line in rec.line_ids:					
				if wo_line.pump_model_id.id:							
					if wo_line.pump_model_id.attach_oad:
						
						filepath = os.path.join('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_reports/planning/images', 'attachment_1.png')
						f = open(filepath, "a")
						f.write(wo_line.pump_model_id.attach_oad.decode('base64'))
					else:
						pass	
														
				if wo_line.moc_construction_id:						
					for csd in wo_line.pump_model_id.line_ids_e:
						if wo_line.moc_construction_id.id == csd.moc_const_id.id:
							if csd.flag_attach_gad:
								
								filepath = os.path.join('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_reports/planning/images', 'attachment_2.png')
								f = open(filepath, "a")
								f.write(csd.flag_attach_gad.decode('base64'))
							else:
								pass
						else:
							pass
				if wo_line.enquiry_line_id:
					enq_line_obj = self.pool.get('ch.kg.crm.pumpmodel')  
					enq_line_rec = enq_line_obj.browse(cr,uid,wo_line.enquiry_line_id)
					for gad in wo_line.pump_model_id.line_ids_c:
						if gad.primemover_id.id == enq_line_rec.primemover_id.id:
							if gad.flag_attach_gad:
								filepath = os.path.join('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_reports/planning/images', 'attachment_3.png')
								f = open(filepath, "a")
								f.write(gad.flag_attach_gad.decode('base64'))
							else:
								pass
						else:
							pass	
		
		common_file = '/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_reports/planning/images/'
		if os.path.isfile(common_file+'attachment_1.png') == True:
			val['attach_1'] = 'attachment_1.png'
		else:
			val['attach_1'] = ''
		if os.path.isfile(common_file+'attachment_2.png') == True:
			val['attach_2'] = 'attachment_2.png'
		else:
			val['attach_2'] = ''
		if os.path.isfile(common_file+'attachment_3.png') == True:
			val['attach_3'] = 'attachment_3.png'
		else:
			val['attach_3'] = ''
		printed = data['form']['user_id'][1]		
		p_user= str(printed)		
		val['user_id'] = uid		
		val['printed_by'] = p_user
		## Getting Work Order ids ###
		
		val['wo_line_ids'] = data['form']['wo_id'][0]
		print "vvaavv",val
			
		return val

	def generate_records(self, cr, uid, ids, data, context):		
		pool= pooler.get_pool(cr.dbname)
		return {}

jasper_report.report_jasper('report.jasper_workorder_report', 'kg.workorder.report', parser=jasper_workorder_report_print, )

