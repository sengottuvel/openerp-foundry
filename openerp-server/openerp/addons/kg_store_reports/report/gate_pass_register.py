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

class gate_pass_register(report_sxw.rml_parse):
	_name = 'gate.pass.register'   

	def __init__(self, cr, uid, name, context=None):
		if context is None:
			context = {}
		super(gate_pass_register, self).__init__(cr, uid, name, context=context)
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
				department.append("pass.dep_id = %s "%(ids1))
		
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
		
		if form['status'] == 'delivered':
			pass_state = 'done'
		elif form['status'] == 'cancelled':
			pass_state = 'cancel'
		else:
			pass_state = 'done'
			
		if not form['status'] or form['status'] == 'delivered' or form['status'] == 'cancelled':
		
			self.cr.execute('''
			
				  SELECT			  
				  pass.id AS pass_id,
				  to_char(pass.date,'dd/mm/yyyy') AS pass_date,
				  pass.name AS pass_number,
				  dep.dep_name AS dep_name,
				  prd.name_template AS product_name,
				  uom.name AS uom,
				  pass_line.qty AS qty,
				 
				  pass_line.ser_no AS ser_no,
				  pass_line.id AS pass_line_id,
				  out.name AS out_type,
				  ser_ind_line.service_id AS indent,
				  ser_ind.name As ser_ind_name,
				  to_char(ser_ind.date, 'dd/mm/yyyy') AS ser_ind_date,
				  partner.name as supplier_name,
				  pass.partner_id as supplier_id,
				  brand.name as brand_name
							  
				  FROM  kg_gate_pass pass

				  LEFT JOIN res_partner partner ON (pass.partner_id=partner.id)
				  LEFT JOIN kg_gate_pass_line pass_line ON (pass_line.gate_id=pass.id)
				  LEFT JOIN kg_depmaster dep ON (dep.id=pass.dep_id)
				  LEFT JOIN product_uom uom ON (uom.id=pass_line.uom)
				  LEFT JOIN product_product prd ON (prd.id=pass_line.product_id)
				  LEFT JOIN kg_outwardmaster out ON (out.id = pass.out_type)
				  LEFT JOIN kg_service_indent_line ser_ind_line ON (ser_ind_line.id = pass_line.si_line_id)
				  LEFT JOIN kg_service_indent ser_ind ON (ser_ind.id = ser_ind_line.service_id)
				  LEFT JOIN kg_brand_master brand ON (pass_line.brand_id = brand.id)

				  where pass.state=%s and pass.date >=%s and pass.date <=%s'''+ department + product + '''
				  order by pass.date''',(pass_state,form['date_from'],form['date_to']))			   
		
		elif form['status'] == 'pending': 
			self.cr.execute('''
			
				  SELECT			  
				  pass.id AS pass_id,
				  to_char(pass.date,'dd/mm/yyyy') AS pass_date,
				  pass.name AS pass_number,
				  dep.dep_name AS dep_name,
				  prd.name_template AS product_name,
				  uom.name AS uom,
				  pass_line.qty AS qty,
				 
				  pass_line.ser_no AS ser_no,
				  pass_line.id AS pass_line_id,
				  out.name AS out_type,
				  ser_ind_line.service_id AS indent,
				  ser_ind.name As ser_ind_name,
				  to_char(ser_ind.date, 'dd/mm/yyyy') AS ser_ind_date,
				  partner.name as supplier_name,
				  pass.partner_id as supplier_id,
				  brand.name as brand_name
							  
				  FROM  kg_gate_pass pass

				  LEFT JOIN res_partner partner ON (pass.partner_id=partner.id)
				  LEFT JOIN kg_gate_pass_line pass_line ON (pass_line.gate_id=pass.id)
				  LEFT JOIN kg_depmaster dep ON (dep.id=pass.dep_id)
				  LEFT JOIN product_uom uom ON (uom.id=pass_line.uom)
				  LEFT JOIN product_product prd ON (prd.id=pass_line.product_id)
				  LEFT JOIN kg_outwardmaster out ON (out.id = pass.out_type)
				  LEFT JOIN kg_service_indent_line ser_ind_line ON (ser_ind_line.id = pass_line.si_line_id)
				  LEFT JOIN kg_service_order so ON (so.gp_id = pass.id)
				  LEFT JOIN kg_service_indent ser_ind ON (ser_ind.id = ser_ind_line.service_id)
				  LEFT JOIN kg_brand_master brand ON (pass_line.brand_id = brand.id)

				  where pass.state='done' and so.gp_id is not NULL and pass.date >=%s and pass.date <=%s '''+ department + product + '''
				  order by pass.date''',(form['date_from'],form['date_to']))	
				  
		elif form['status'] == 'closed': 
			self.cr.execute('''
			
				  SELECT			  
				  pass.id AS pass_id,
				  to_char(pass.date,'dd/mm/yyyy') AS pass_date,
				  pass.name AS pass_number,
				  dep.dep_name AS dep_name,
				  prd.name_template AS product_name,
				  uom.name AS uom,
				  pass_line.qty AS qty,
				 
				  pass_line.ser_no AS ser_no,
				  pass_line.id AS pass_line_id,
				  out.name AS out_type,
				  ser_ind_line.service_id AS indent,
				  ser_ind.name As ser_ind_name,
				  to_char(ser_ind.date, 'dd/mm/yyyy') AS ser_ind_date,
				  partner.name as supplier_name,
				  pass.partner_id as supplier_id,
				  brand.name as brand_name
							  
				  FROM  kg_gate_pass pass

				  LEFT JOIN res_partner partner ON (pass.partner_id=partner.id)
				  LEFT JOIN kg_gate_pass_line pass_line ON (pass_line.gate_id=pass.id)
				  LEFT JOIN kg_depmaster dep ON (dep.id=pass.dep_id)
				  LEFT JOIN product_uom uom ON (uom.id=pass_line.uom)
				  LEFT JOIN product_product prd ON (prd.id=pass_line.product_id)
				  LEFT JOIN kg_outwardmaster out ON (out.id = pass.out_type)
				  LEFT JOIN kg_service_indent_line ser_ind_line ON (ser_ind_line.id = pass_line.si_line_id)
				  LEFT JOIN kg_service_order so ON (so.gp_id = pass.id)
				  LEFT JOIN kg_service_indent ser_ind ON (ser_ind.id = ser_ind_line.service_id)
				  LEFT JOIN kg_brand_master brand ON (pass_line.brand_id = brand.id)

				  where pass.state='done' and so.state='inv' and so.gp_id is not NULL and pass.date >=%s and pass.date <=%s '''+ department + product + '''
				  order by pass.date''',(form['date_from'],form['date_to']))
		data=self.cr.dictfetchall()
		print "data ::::::::::::::=====>>>>", data
		
		
		new_data = []
		count = 0
		gr_total = 0.0
		qty_total = 0.0
		rate_total = 0.0
		for pos1, item1 in enumerate(data):
			delete_items = []
			
			qty_total += item1['qty']
			item1['gr_qty_total'] = qty_total		
			
			for pos2, item2 in enumerate(data):
				if not pos1 == pos2:
					if item1['pass_id'] == item2['pass_id'] and item1['pass_date'] == item2['pass_date']:			
						if count == 0:
							new_data.append(item1)
							print "new_data -------------------------------->>>>", new_data
							count = count + 1
						item2_2 = item2
						item2_2['pass_number'] = ''
						item2_2['pass_date'] = ''
						item2_2['supplier_name'] = ''

						
						new_data.append(item2_2)
						print "new_data 2222222222222222", new_data
						delete_items.append(item2)
						print "delete_items _____________________>>>>>", delete_items
				else:
					print "Few Gate Pass have one line"
					
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
  

report_sxw.report_sxw('report.gate.pass.register', 'kg.gate.pass', 
			'addons/kg_store_reports/report/gate_pass_register.rml', 
			parser=gate_pass_register, header = False)
			
