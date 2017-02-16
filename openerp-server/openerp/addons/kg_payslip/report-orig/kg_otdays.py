import time
from report import report_sxw
from reportlab.pdfbase.pdfmetrics import stringWidth
import locale


class kg_otdays(report_sxw.rml_parse):
	
	_name = 'kg.otdays'
	_inherit='hr.payslip'   

	def __init__(self, cr, uid, name, context=None):
		if context is None:
			context = {}
		super(kg_otdays, self).__init__(cr, uid, name, context=context)
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
		dep = []		
				
		if form['dep_id']:
			for ids2 in form['dep_id']:
				where_sql.append("emp.department_id = %s"%(ids2))		
		
				
		if where_sql:
			where_sql = ' and '+' or '.join(where_sql)
		else:
			where_sql=''
					
		
		print "where_sql --------------------------->>>", where_sql	
		
		self.cr.execute('''
		
			  SELECT distinct on (emp.id)
				slip.id AS sl_id,
				slip.att_id AS att_id,
				slip.dep_id AS dep_id,
				emp.id as emp_id,
				emp.emp_code as code,
				emp.name_related as emp_name,
				con.wage AS basic,
				dep.name as dep_name,
				att.ot as ot_day

				FROM  hr_payslip slip
					
				JOIN hr_employee emp ON (emp.id=slip.employee_id)
				JOIN hr_contract con ON(con.employee_id=slip.employee_id)
				JOIN hr_department dep ON(dep.id=slip.dep_id)
				JOIN kg_monthly_attendance att ON(att.id=slip.att_id)			 		 			  

			  where slip.state=%s and slip.date_from >=%s and slip.date_to <=%s'''+ where_sql + '''
			   order by emp.id''',('done', form['date_from'],form['date_to']))
			   
		data=self.cr.dictfetchall()
		data.sort(key=lambda data: data['dep_id'])
		print "data_sort ------------------------>>>.........", data		
		data_emp_grouped = []
				
		for pos, sm in enumerate(data):
			data_emp_grouped.insert(pos, [sm])
			rem_list = []
			for pos1, sm1 in enumerate(data):
				if not pos == pos1:
					if sm['dep_id'] == sm1['dep_id']:
						data_emp_grouped[pos].append(sm1)
						rem_list.append(sm1)
			for item in rem_list:
				data.remove(item)
						
		data_new = []
		print "data_emp_grouped...........................",data_emp_grouped
		for item in data_emp_grouped:
			data_new += item					
		print "data_new **************************...",data_new
				
		data_renew = []	
		ser_no=1
		sub_tot = 0.00
		gr_tot = 0.00
		for position1, item1 in enumerate(data_new):
			data_renew.append({'dep_name':item1['dep_name'],'type':1})
			data_renew.append(item1)
			item1['ser_no']=ser_no
			item1['dep_name'] = " "
			ot_day= item1['ot_day']
			item1['ot'] = ot_day
			basic_sal = item1['basic']
			one_day_basic = basic_sal / 26
			ear_sal = one_day_basic * ot_day
			item1['ear'] = ear_sal
			sub_tot = item1['ear']
			remove_item_list = []
			for position2, item2 in enumerate(data_new):
				if position1 != position2:
					if item1['dep_id'] == item2['dep_id']:
						item2['dep_name'] = " "
						item2['ser_no']=ser_no+1
						data_renew.append(item2)
						ot_day= item2['ot_day']
						item2['ot'] = ot_day
						basic_sal = item2['basic']
						one_day_basic = basic_sal / 26
						ear_sal = one_day_basic * ot_day
						item2['ear'] = ear_sal
						remove_item_list.append(item2)
						ser_no+=1
						sub_tot += item2['ear']				
												
			ser_no+=1
			data_renew.append({'code': 'Sub Total', 'sub_tot': sub_tot,})			
			gr_tot += sub_tot				
			for entry in remove_item_list:
				data_new.remove(entry)					
		data_renew.append({'code': 'Grand Total', 'sub_tot': gr_tot,})										
		return data_renew
	
		
		
	

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
  

report_sxw.report_sxw('report.kg.otdays', 'hr.payslip', 
			'addons/kg_payslip/report/kg_otdays.rml', 
			parser=kg_otdays, header = False)


"""
data=self.cr.dictfetchall()
		print "data ::::::::::::::=====>>>>", data
		gran_tot = 0.0		
		for val in data:
			emp_id = val['emp_id']
			att_rec = self.pool.get('kg.monthly.attendance').browse(self.cr, self.uid, val['att_id'])
			ot_day = att_rec.ot
			val['ot'] = ot_day
			basic_sal = val['basic']
			one_day_basic = basic_sal / 26
			ear_sal = one_day_basic * ot_day
			val['ear'] = ear_sal
			gran_tot += ear_sal
			val['total'] = gran_tot		
					
		return data	
		
		"""