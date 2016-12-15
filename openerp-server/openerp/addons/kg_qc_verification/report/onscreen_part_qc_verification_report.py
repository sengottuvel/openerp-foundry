# -*- encoding: utf-8 -*-
##############################################################################
#
#	OpenERP, Open Source Management Solution
#	Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#	$Id$
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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
from datetime import datetime
from openerp import tools
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re 

class onscreen_part_qc_verification_report(JasperDataParser.JasperDataParser):
	def __init__(self, cr, uid, ids, data, context):
		
		super(onscreen_part_qc_verification_report, self).__init__(cr, uid, ids, data, context)

	def generate_data_source(self, cr, uid, ids, data, context):
		return 'records'

	def generate_ids(self, cr, uid, ids, data, context):
		return {}

	def generate_properties(self, cr, uid, ids, data, context):
		return {}
		
	def generate_parameters(self, cr, uid, ids, data, context):
		val={}	
		qc_ids = ids
		qc_rec = self.pool.get('kg.qc.verification').browse(cr,uid,ids[0])
		print"sssssssssssssssssssss", qc_rec.stock_type 		
		if qc_rec.stock_type == 'pump':
			return {'value':{},'warning':{'title':'warning','message':'Your message'}}
		if len(qc_ids) == 1:			
			list_ids = qc_ids[0]
			val['id'] = list_ids			
		else:
			list_ids = ''
			for item in qc_ids:
				list_ids = str(list_ids) + str(item) + ","			
			val['id'] = list_ids[:-1]			
		print_date = datetime.now().strftime('%d-%m-%Y %H:%M:%S')		
		user_rec = self.pool.get('res.users').browse(cr,uid,uid)		
		val['printed_by'] = str(user_rec.name)	
		val['print_date'] = print_date	
		val['id'] = str(val['id'])				
		return val

	def generate_records(self, cr, uid, ids, data, context):
		pool= pooler.get_pool(cr.dbname)		
		return {}

jasper_report.report_jasper('report.onscreen_part_qc_verification_report', 'kg.qc.verification', parser=onscreen_part_qc_verification_report)
