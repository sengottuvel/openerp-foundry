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

class jasper_allotted_components_report_print(JasperDataParser.JasperDataParser):
	def __init__(self, cr, uid, ids, data, context):		
		super(jasper_allotted_components_report_print, self).__init__(cr, uid, ids, data, context)

	def generate_data_source(self, cr, uid, ids, data, context):
		return 'records'

	def generate_ids(self, cr, uid, ids, data, context):
		return {}

	def generate_properties(self, cr, uid, ids, data, context):
		return {}
		
	def generate_parameters(self, cr, uid, ids, data, context):
		val={}		
		date_from = data['form']['date_from']
		date_to = data['form']['date_to']
		if data['form']['division_id']:				
			division_id = data['form']['division_id'][0]
			division_name = data['form']['division_id'][1] 
			print"division_name",division_name								
		printed = data['form']['printed_by'][1]
		p_user= str(printed)		
		printed_date = data['form']['print_date']
		
		date_print =  printed_date.encode('utf-8')
		d1 = datetime.strptime(date_print,'%Y-%m-%d %H:%M:%S')
		p_date = d1.strftime( '%d-%m-%Y %H:%M:%S')
		
		to_date =  date_to.encode('utf-8')
		to_d1 = datetime.strptime(to_date,'%Y-%m-%d')
		to_d2 = datetime.strftime(to_d1, '%d-%m-%Y')		
		from_date =  date_from.encode('utf-8')
		from_d1 = datetime.strptime(from_date,'%Y-%m-%d')
		from_d2 = datetime.strftime(from_d1, '%d-%m-%Y')	
		
		val['to_date_range'] = to_d2
		val['from_date_range'] = from_d2
		
		val['date_from'] = date_from
		val['date_to'] = date_to		
		val['user_id'] = uid		
		val['printed_by'] = str(printed)	
		val['print_date'] = p_date
		if data['form']['division_id']:	
			val['division_id'] = division_id
			val['division_name'] = division_name
		else:
			val['division_id'] = 0
			val['division_name'] = 'ALL'
			pass	
		
		return val

	def generate_records(self, cr, uid, ids, data, context):		
		pool= pooler.get_pool(cr.dbname)
		return {}

jasper_report.report_jasper('report.jasper_allotted_components_report', 'kg.allotted.components', parser=jasper_allotted_components_report_print, )
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
