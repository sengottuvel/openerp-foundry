# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2005-2006 CamptoCamp
# Copyright (c) 2006-2010 OpenERP S.A
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import time
from report import report_sxw
from reportlab.pdfbase.pdfmetrics import stringWidth
import locale

class dep_issue_register(report_sxw.rml_parse):
	_name = 'report.dep.issue.register'
	_inherit='stock.picking'   

	def __init__(self, cr, uid, name, context=None):
		if context is None:
			context = {}
		super(dep_issue_register, self).__init__(cr, uid, name, context=context)
		self.query = ""
		self.period_sql = ""
		self.localcontext.update( {
			'time': time,
			'get_filter': self._get_filter,
			'get_start_date':self._get_start_date,
			'get_end_date':self._get_end_date,
			'get_data':self.get_data,
			'locale':locale,
		})
		self.context = context
		
	def get_data(self,form):
		res = {}
		
		where_sql = []
		department = []
		product =[]
		
		if form['dep_id']:
			for ids1 in form['dep_id']:
				department.append("issue.department_id = %s "%(ids1))
		
		if form['product_type']:
				where_sql.append("pt.type= '%s' "%form['product_type'])
				
		if form['product']:
			for ids2 in form['product']:
				product.append("prd.id = %s"%(ids2))
			
		if department:
			department = 'and ('+' or '.join(department)
			department =  department+')'
		else:
			department = ''
			
		if product:
			product = ' and '+' or '.join(product)
		else:
			product=''			
		

		print "department --------------------------->>>", department
		
		if form['status'] == 'approved':
			issue_state = 'done'
		elif form['status'] == 'cancelled':
			issue_state = 'cancel'
		else:
			issue_state = 'done'
		
		self.cr.execute('''
		
			  SELECT			  
			  issue.id AS issue_id,
			  issue.type AS type,
			  to_char(issue.issue_date,'dd/mm/yyyy') AS issue_date,
			  issue.name AS issue_number,
			  dep.dep_name AS dep_name,
			  prd.name_template AS product_name,
 			  uom.name AS uom,
			  issue_line.issue_qty AS qty,
			  issue_line.id AS issue_line_id,
			  issue_line.price_unit AS rate,
			  out.name AS out_type,
			  line.indent_id AS indent,
			  ind.name AS dp_name,
			  to_char(ind.date, 'dd/mm/yyyy') AS dp_date,
			  ser_ind.name As ser_ind_name,
			  to_char(ser_ind.date, 'dd/mm/yyyy') AS ser_ind_date,
			  issue.created_by AS created_by
			  			  
			  FROM  kg_department_issue issue

			  LEFT JOIN kg_department_issue_line issue_line ON (issue_line.issue_id=issue.id)
			  LEFT JOIN kg_depmaster dep ON (dep.id=issue.department_id)
			  LEFT JOIN product_uom uom ON (uom.id=issue_line.uom_id)
			  LEFT JOIN product_product prd ON (prd.id=issue_line.product_id)
			  LEFT JOIN kg_outwardmaster out ON (out.id = issue.outward_type)
			  LEFT JOIN kg_depindent_line line ON (line.id = issue_line.indent_line_id)
			  LEFT JOIN kg_depindent ind ON (ind.id = line.indent_id)
			  LEFT JOIN kg_service_indent_line ser_ind_line ON (ser_ind_line.id = issue_line.service_indent_line_id)
			  LEFT JOIN kg_service_indent ser_ind ON (ser_ind.id = ser_ind_line.service_id)

			  where issue.type=%s and issue.state=%s and issue.issue_date >=%s and issue.issue_date <=%s'''+ department + product + '''
			   order by issue.issue_date''',('out',issue_state,form['date_from'],form['date_to']))			   
		
		data=self.cr.dictfetchall()
		print "data ::::::::::::::=====>>>>", data
		
		# Issue NO and Supplier should be blank if a Issue have more than one line
		
		new_data = []
		count = 0
		gr_total = 0.0
		qty_total = 0.0
		rate_total = 0.0
		for pos1, item1 in enumerate(data):
			delete_items = []
			
			if item1['rate'] is None:
				item1['rate'] = 0.0
			else:
				item1['rate'] = item1['rate']
				
			val = item1['qty'] * item1['rate']
			gr_total += val
			qty_total += item1['qty']
			rate_total += item1['rate']
			item1['total'] = gr_total			
			item1['gr_qty_total'] = qty_total		
			item1['gr_rate_total'] = rate_total		
			
			for pos2, item2 in enumerate(data):
				if not pos1 == pos2:
					if item1['issue_id'] == item2['issue_id'] and item1['issue_date'] == item2['issue_date']:			
						if count == 0:
							new_data.append(item1)
							print "new_data -------------------------------->>>>", new_data
							count = count + 1
						item2_2 = item2
						item2_2['issue_number'] = ''
						item2_2['issue_date'] = ''
						item2_2['issue_total'] = ''
						
						new_data.append(item2_2)
						print "new_data 2222222222222222", new_data
						delete_items.append(item2)
						print "delete_items _____________________>>>>>", delete_items
				else:
					print "Few GRN have one line"
					
		return data					   

	def _get_filter(self, data):
		if data.get('form', False) and data['form'].get('filter', False):
			if data['form']['filter'] == 'filter_date':
				return _('Date')
			
		return _('No Filter')
		
	def _get_start_date(self, data):
		if data.get('form', False) and data['form'].get('date_from', False):
			return data['form']['date_from']
		return ''
		
	def _get_end_date(self, data):
		if data.get('form', False) and data['form'].get('date_to', False):
			return data['form']['date_to']
		return ''		   
  

report_sxw.report_sxw('report.dep.issue.register', 'stock.picking', 
			'addons/kg_store_reports/report/dep_issue_register.rml', 
			parser=dep_issue_register, header = False)
			
			
# GRN NO and Supplier should be blank if a picking have more than one line
"""
new_data=[]
count = 0
for pos1, item1 in enumerate(data):
	delete_items = []
	match_found = False
	for pos2, item2 in enumerate(data):
		if not pos1 == pos2:
			if item1['grn_number'] == item2['grn_number'] and item1['part_name'] == item2['part_name']:
				match_found = True
				if count == 0:
					new_data.append(item1)
					count = count + 1
				item2_2 = item2
				item2_2['grn_number'] = ''
				item2_2['part_name'] = ''
				item2_2['date'] = ''
				new_data.append(item2_2)
				delete_items.append(item2)
	if not match_found:
		new_data.append(item1)
	for ele in delete_items:
		data.remove(ele)
data = new_data
for d in data:
	seq = 0.0
	if d['grn_number'] != '' and d['part_name'] != '':
		seq = seq + 1
		d['sequence'] = seq
		"""
		
	
					
					
