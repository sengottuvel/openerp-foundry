import time
from report import report_sxw
from osv import osv
from reportlab.pdfbase.pdfmetrics import stringWidth
from operator import itemgetter
import tools
from osv import fields, osv
import time, datetime
from datetime import *
import logging
import locale
import netsvc
logger = logging.getLogger('server')

class kg_supplier_reg_report(report_sxw.rml_parse):
	
	_name = 'kg.supplier.reg.report'
	
	
	def __init__(self, cr, uid, name, context=None):
		if context is None:
			context = {}
		super(kg_supplier_reg_report, self).__init__(cr, uid, name, context=context)
		self.query = ""
		self.period_sql = ""
		self.localcontext.update( {
			'time': time,
			'get_filter': self._get_filter,
			'get_start_date':self._get_start_date,
			'get_end_date':self._get_end_date,
			'get_data':self.get_data,
			'locale':locale
			
			
			
		})
		self.context = context

	def get_data(self,form):
		res = {}
		where_sql = []
		supplier = []
		
		if form['suppliers']:
			for ids1 in form['suppliers']:
				supplier.append("pat.id = %s"%(ids1)) 
				
		if supplier:
			supplier = ' and '+' or '.join(supplier)
		else:
			supplier=''
		

			
		print "supplier.............................", supplier
		
		
		
		self.cr.execute('''
				
				select pat.name as supplier_name,
				pat.street as street,
				pat.street2 as street2,
				city.name as city,
				state.name as state,
				country.name as country,
				pat.zip as zip,
				pat.email as email,
				pat.phone as phone,
				pat.mobile as mobile
				
				from res_partner pat
				
				left join res_city city on (pat.city_id = city.id)
				left join res_country_state state on (pat.state_id = state.id)
				left join res_country country on (pat.country_id = country.id)
				where supplier='t' '''+ supplier + '''
				order by pat.name ''')
				
		data = self.cr.dictfetchall()
		print "Data ABBBBBBBBBBBBBBBBBBBBBBBBBBBBBB", data
		
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
 
report_sxw.report_sxw('report.kg.supplier.reg.report','res.partner','addons/kg_store_reports/report/kg_supplier_report.rml',
						parser=kg_supplier_reg_report, header= False)
