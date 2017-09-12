import time
from lxml import etree
from osv import fields, osv
from tools.translate import _
import pooler
import logging
import netsvc
import datetime as lastdate
import calendar
import openerp
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
logger = logging.getLogger('server')


class kg_pouring_pending_excel(osv.osv):

	_name = 'kg.pouring.pending.excel'
	_order = 'date desc'

	_columns = {
		
		## Basic Info
		'as_on_date': fields.date("As On Date",required=True),		
		'company_id': fields.many2one('res.company', 'Company'),
		'print_date': fields.datetime('print Date', readonly=True),
		'printed_by': fields.many2one('res.users','Printed By',readonly=True),  
		"rep_data":fields.binary("File",readonly=True),
		"name":fields.char("Filename",25,readonly=True),
		'state': fields.selection([('draft', 'Draft'),('done','Done')], 'Status', readonly=True),
		'date': fields.date('Creation Date'),
		
		## If any filter it should be many2many only. Don't use many2one filter unless it's must	
		'pattern_id': fields.many2many('kg.pattern.master', 'm2m_pour_pen_pattern_master_details', 'pour_wiz_id', 'pattern_id','Pattern No', domain="[('active','=','t')]"),
		'schedule_id': fields.many2many('kg.schedule', 'm2m_pour_pen_schedule_details', 'sche_wiz_id', 'schedule_id','Schedule No', domain="[('state','=','confirmed')]"),
		'moc_id': fields.many2many('kg.moc.master', 'm2m_pour_pen_moc_master_details', 'pour_wiz_id', 'moc_id','MOC', domain="[('active','=','t')]"),
		'category': fields.selection([('1','MS NC'),('2','NC'),('3','Service'),('4','Emergency'),('5','Spare'),('6','Normal')],'Category'),
	}
	
		
	_defaults = {
		'as_on_date': time.strftime('%Y-%m-%d'),		
		'date' : fields.date.context_today,
		'print_date': time.strftime('%Y-%m-%d %H:%M:%S'),
		'printed_by': lambda obj, cr, uid, context: uid,		
		'state': 'draft',	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.pouring.pending.excel', context=c),
	 }
	  
		
	def produce_xls(self, cr, uid, ids, context={}):
		
		import StringIO
		import base64
		
		try:
			import xlwt
		except:
		   raise osv.except_osv('Warning !','Please download python xlwt module from\nhttp://pypi.python.org/packages/source/x/xlwt/xlwt-0.7.2.tar.gz\nand install it')
		
		excel_rec =self.browse(cr,uid,ids[0])
		
		schedule = []
		pattern = []
		moc = []
		category = []
		
		if excel_rec.as_on_date:
			as_on_date = "'"+excel_rec.as_on_date+"'"
		
		if excel_rec.schedule_id:
			sch = [x.id for x in excel_rec.schedule_id]
			schedule_ids = ",".join(str(x) for x in sch)
			schedule.append("pro.schedule_id in (%s)"%(schedule_ids))
			
		if excel_rec.pattern_id:
			patt = [x.id for x in excel_rec.pattern_id]
			pattern_ids = ",".join(str(x) for x in patt)
			pattern.append("pro.pattern_id in (%s)"%(pattern_ids))
			
		if excel_rec.moc_id:
			mocc = [x.id for x in excel_rec.moc_id]
			moc_ids = ",".join(str(x) for x in mocc)
			moc.append("pro.moc_id in (%s)"%(moc_ids))
			
		if excel_rec.category:
			categ = [x for x in excel_rec.category]
			categories = ",".join("'"+str(x)+"'" for x in categ)
			category.append("pro.order_priority in (%s)"%(categories))
		
		if schedule:
			schedule = 'and '+' or '.join(schedule)
			schedule =  schedule+' '
			
		else:
			schedule = ''
			
		if pattern:
			pattern = 'and '+' or '.join(pattern)
			pattern =  pattern+' '
			
		else:
			pattern = ''
			
		if moc:
			moc = 'and '+' or '.join(moc)
			moc =  moc+' '
			
		else:
			moc = ''
			
		if category:
			category = 'and '+' or '.join(category)
			category =  category+' '
			
		else:
			category = ''
		
		sql = """		
								select
			company.name as company_name,
			(CASE WHEN pro.order_priority = '1'
			THEN 'MS NC'
			WHEN pro.order_priority = '2'
			THEN 'NC'
			WHEN pro.order_priority = '3'
			THEN 'Service'
			WHEN pro.order_priority = '4'
			THEN 'Emergency'
			WHEN pro.order_priority = '5'
			THEN 'Spare'
			WHEN pro.order_priority = '6'
			THEN 'Normal'
			ELSE ''
			end ) as order_priority,
			pro.order_priority as ref_order_priority,
			to_char(pro.order_date::date,'dd-mm-YYYY') as order_date,
			pro.order_no as order_no,
			pro.pattern_code as pattern_no,
			pro.pattern_name as pattern_name,
			moc.name as moc,
			pro.qty as qty,
			pro.each_weight as unit_weight,
			(pro.qty * pro.each_weight) as total_weight,
			pro.pour_remarks as reason,
			schedule.name as name

			from kg_production pro
			left join kg_schedule schedule on (schedule.id = pro.schedule_id)
			left join kg_moc_master moc on (moc.id = pro.moc_id)
			left join res_company company on (company.id = pro.company_id)

			where to_char(pro.order_delivery_date::date,'yyyy-mm-dd') <= """+as_on_date+""" and pro.pour_state !='done' """+schedule+""""""+pattern+""""""+moc+""""""+category+"""

			order by ref_order_priority,order_date,order_no,pattern_no"""
				
		cr.execute(sql)		
		data = cr.dictfetchall()
		
		if data == []:
			raise osv.except_osv(_('Warning!'),_('No Data Found'))
		else:
			
			wbk = xlwt.Workbook()		
			style1 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz center, vert centre;''borders: left thin, right thin, top thin') 
			style2 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz center, vert centre;''borders: left thin, right thin, top thin, bottom thin') 
			style3 = xlwt.easyxf('borders: left thin, right thin, bottom thin')
			style4 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz left;')
			style5 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz center;')
			style6 = xlwt.easyxf('font: height 200,color_index black;' 'align: vert centre, horiz left;''borders: left thin, right thin, top thin, bottom thin') 
			style7 = xlwt.easyxf('font: height 200,color_index black;' 'align: wrap on, vert centre, horiz left;''borders: left thin, right thin, top thin, bottom thin') 
			style8 = xlwt.easyxf('font: height 200,color_index black;' 'align: wrap on, vert centre, horiz centre;''borders: left thin, right thin, top thin, bottom thin') 

			report_name = 'Foundry_Partlist_Rpt.xls'	
		
			s1=7
			
			"""adding a worksheet along with name"""	
			
			sheet1 = wbk.add_sheet('Pouring Pending List')	
			
			s2=8
			
			k1=5
			sheet1.col(0).width = 8000
			sheet1.col(1).width = 12000
			sheet1.col(2).width = 12000
			sheet1.col(3).width = 12000
			
			as_on_date = datetime.strptime(excel_rec.as_on_date, '%Y-%m-%d').strftime('%d/%m/%Y')
			sheet1.write_merge(0, 0, 0,9,"SAM TURBO INDUSTRY PRIVATE LIMITED",style2)
			sheet1.row(0).height = 450				
			sheet1.write_merge(1, 1, 0, 9,"Pouring Pending List of "+as_on_date,style2)	
			sheet1.row(1).height = 400				
			
			s1=2		

			sheet1.col(0).width = 6000
			sheet1.col(1).width = 3200
			sheet1.col(2).width = 5000
			sheet1.col(3).width = 6000
			sheet1.col(4).width = 8000
			sheet1.col(5).width = 7000
			sheet1.col(6).width = 2000
			sheet1.col(7).width = 5000
			sheet1.col(8).width = 4000
			sheet1.col(9).width = 5000

			sheet1.write(s1,0,"Schedule No",style1)
			sheet1.write(s1,1,"Order Date",style1)
			sheet1.write(s1,2,"Order No",style1)
			sheet1.write(s1,3,"Patten No",style1)
			sheet1.write(s1,4,"Pattern Name",style1)
			sheet1.write(s1,5,"MOC",style1)
			sheet1.write(s1,6,"Qty",style1)
			sheet1.write(s1,7,"Unit Weight(Kgs)",style1)
			sheet1.write(s1,8,"Total Weight",style1)
			sheet1.write(s1,9,"Reason",style1)
			s2=3
			categ_list = []
			for ele in data:							
				if ele['order_priority'] in categ_list:					
					sheet1.write(s2,0,ele['name'],style3)
					sheet1.write(s2,1,ele['order_date'],style3)
					sheet1.write(s2,2,ele['order_no'],style3)
					sheet1.write(s2,3,ele['pattern_no'],style3)
					sheet1.write(s2,4,ele['pattern_name'],style3)
					sheet1.write(s2,5,ele['moc'],style3)
					sheet1.write(s2,6,ele['qty'],style3)
					sheet1.write(s2,7,ele['unit_weight'],style3)
					sheet1.write(s2,8,ele['total_weight'],style3)
					sheet1.write(s2,9,ele['reason'],style3)
					
				else:
					
					categ_list.append(ele['order_priority'])
					sheet1.write_merge(s2,s2, 0,9,ele['order_priority'],style2)
					s2=s2+1
					sheet1.write(s2,0,ele['name'],style3)
					sheet1.write(s2,1,ele['order_date'],style3)
					sheet1.write(s2,2,ele['order_no'],style3)
					sheet1.write(s2,3,ele['pattern_no'],style3)
					sheet1.write(s2,4,ele['pattern_name'],style3)
					sheet1.write(s2,5,ele['moc'],style3)
					sheet1.write(s2,6,ele['qty'],style3)
					sheet1.write(s2,7,ele['unit_weight'],style3)
					sheet1.write(s2,8,ele['total_weight'],style3)
					sheet1.write(s2,9,ele['reason'],style3)
					
				s2+=1
				"""Parsing data as string """
				cur_mon = time.strftime('%Y-%B')
				file_data=StringIO.StringIO()
				o=wbk.save(file_data)		
				"""string encode of data in wksheet"""		
				out=base64.encodestring(file_data.getvalue())
			"""returning the output xls as binary"""
		return self.write(cr, uid, ids, {'rep_data':out, 'name': 'Pouring_Pending'+'.xls','state':'done'})	

	def unlink(self, cr, uid, ids,context=None):
		for rec in self.browse(cr, uid, ids):
			if rec.state == 'done':
				raise osv.except_osv(_('Unable to Delete !'),_('You can not delete Done state reports !!'))
		return super(kg_pouring_pending_excel, self).unlink(cr, uid, ids, context)

kg_pouring_pending_excel()
