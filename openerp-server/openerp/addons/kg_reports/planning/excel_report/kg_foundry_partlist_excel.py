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


class kg_foundry_partlist_excel(osv.osv):

	_name = 'kg.foundry.partlist.excel'

	_columns = {	
		
		'order_type': fields.selection([('schedule_wise','Schedule Wise'),('wo_wise','WO Wise')],'Type',required=True),
		'order_id': fields.many2one('kg.work.order','WO No' ,domain="[('state','=','confirmed')]"),
		'schedule_id': fields.many2one('kg.schedule', 'Schedule No', domain="[('state','=','confirmed')]"),
		
		
		'company_id': fields.many2one('res.company', 'Company'),
		'print_date': fields.datetime('print Date', readonly=True),
		'printed_by': fields.many2one('res.users','Printed By',readonly=True),  
		
		"rep_data":fields.binary("File",readonly=True),
		"name":fields.char("Filename",25,readonly=True),
		'state': fields.selection([('draft', 'Draft'),('done','Done')], 'Status', readonly=True),
		'date': fields.date('Creation Date'),
		
		}	
	
		
		
	_defaults = {
	
		'date': time.strftime('%Y-%m-%d'),
		'state': 'draft',
		'order_type': 'wo_wise',
	}
	  
		
	def produce_xls(self, cr, uid, ids, context={}):
		
		import StringIO
		import base64
		
		try:
			import xlwt
		except:
		   raise osv.except_osv('Warning !','Please download python xlwt module from\nhttp://pypi.python.org/packages/source/x/xlwt/xlwt-0.7.2.tar.gz\nand install it')
		
		excel_rec =self.browse(cr,uid,ids[0])
		
		order_id = excel_rec.order_id.id		
		schedule_id = excel_rec.schedule_id.id	
		
		if order_id is False:
			order_id = 0
		if schedule_id is False:
			schedule_id = 0	
		
		sql = """		
					select
						company.name as company_name,
						to_char(wo_order.entry_date::date,'dd-mm-YYYY') as wo_date,
						wo_order.name as wo_no,
						(CASE WHEN wo_order.order_priority = 'normal'
						THEN 'Normal'
						WHEN wo_order.order_priority = 'emergency'
						THEN 'Emergency'
						ELSE ''
						end ) as priority,
						order_details.order_no as order_no,
						pump.name as pump_name,
						pattern.name as pattern_no,
						pattern.pattern_name as pattern_name,
						moc.name as moc,
						(CASE WHEN foundry.flag_pattern_check = False
						THEN 'No'
						WHEN foundry.flag_pattern_check = True
						THEN 'Yes'
						ELSE ''
						end ) as pattern_check,
						foundry.add_spec as other_spec,
						foundry.qty as required_qty,
						sch.stock_qty as stock_qty,
						case when (foundry.qty - sch.stock_qty) < 0 then 0 else (foundry.qty - sch.stock_qty) end  as pouring_qty,
						(CASE WHEN moc.weight_type = 'ci'
						THEN pattern.ci_weight
						WHEN moc.weight_type = 'ss'
						THEN pattern.pcs_weight
						WHEN moc.weight_type = 'non_ferrous'
						THEN pattern.nonferous_weight
						ELSE '0.00'
						end ) as each_wight,
						(case when (foundry.qty - sch.stock_qty) < 0 then 0 else (foundry.qty - sch.stock_qty) end   * (CASE WHEN moc.weight_type = 'ci'
						THEN pattern.ci_weight
						WHEN moc.weight_type = 'ss'
						THEN pattern.pcs_weight
						WHEN moc.weight_type = 'non_ferrous'
						THEN pattern.nonferous_weight
						ELSE '0.00'
						end ) ) as total_weight,
						schedule.name as schedule_no

						from

						ch_schedule_details  sch
						left join kg_schedule schedule on (schedule.id = sch.header_id)
						left join kg_work_order wo_order on (wo_order.id = sch.order_id)
						left join ch_work_order_details order_details on (order_details.id = sch.order_line_id)
						left join ch_order_bom_details foundry on (foundry.id = sch.order_bomline_id)
						left join kg_pumpmodel_master pump on (pump.id = order_details.pump_model_id)
						left join kg_moc_master moc on (moc.id = foundry.moc_id)
						left join kg_pattern_master pattern on (pattern.id = sch.pattern_id)
						left join res_company company on (company.id = wo_order.company_id)

						where

						sch.order_id = %s
						 or 
						sch.header_id = %s"""%(order_id,schedule_id)
				
		cr.execute(sql)		
		data = cr.dictfetchall()
		
		if data == []:
			raise osv.except_osv(_('Warning!'),_('No Data Found'))
		else:
			order_ref = "WO No : " + str(data[0]['wo_no'])
			order_date = "WO Date : " + str(data[0]['wo_date'])
			order_priority = "Priority : " + str(data[0]['priority'])
			
			
			wbk = xlwt.Workbook()		
			style1 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz center;''borders: left thin, right thin, top thin') 
			style2 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz center;''borders: left thin, right thin, top thin, bottom thin') 
			style3 = xlwt.easyxf('borders: left thin, right thin, bottom thin')
			style4 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz left;')
			style5 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz center;')
			style6 = xlwt.easyxf('font: height 200,color_index black;' 'align: vert centre, horiz left;''borders: left thin, right thin, top thin, bottom thin') 
			style7 = xlwt.easyxf('font: height 200,color_index black;' 'align: wrap on, vert centre, horiz left;''borders: left thin, right thin, top thin, bottom thin') 
			style8 = xlwt.easyxf('font: height 200,color_index black;' 'align: wrap on, vert centre, horiz centre;''borders: left thin, right thin, top thin, bottom thin') 
			
				
					
			report_name = 'Foundry_Partlist_Rpt.xls'	
		
			s1=7
			
			"""adding a worksheet along with name"""	
			
			sheet1 = wbk.add_sheet('Foundry Partlist Copy')	
			
			s2=8
			
			k1=5
			sheet1.col(0).width = 8000
			sheet1.col(1).width = 12000
			sheet1.col(2).width = 12000
			sheet1.col(3).width = 12000
			
			
			sheet1.write_merge(0, 0, 0, 12,"SAM TURBO INDUSTRY PRIVATE LIMITED",style2)
			sheet1.row(0).height = 450				
			sheet1.write_merge(1, 1, 0, 12,"Foundry Part List - Work Order",style2)
			
			sheet1.write_merge(3, 3, 0, 5,order_ref,style3)
			sheet1.write_merge(4, 4, 0, 5,order_date,style3)		
			
			sheet1.write_merge(4, 4, 7, 12,order_priority,style3)				
			
			s1=6		
			
			
			
			sheet1.col(0).width = 6000
			sheet1.col(1).width = 6000
			sheet1.col(2).width = 6000
			sheet1.col(3).width = 4000
			sheet1.col(4).width = 5000
			sheet1.col(5).width = 5000
			sheet1.col(6).width = 5000
			sheet1.col(7).width = 5000
			sheet1.col(8).width = 5000
			sheet1.col(9).width = 5000
			sheet1.col(10).width = 5000
			sheet1.col(11).width = 5000
			sheet1.col(12).width = 5000
			
			
			
			sheet1.write(s1,0,"Schedule No",style1)
			sheet1.write(s1,1,"WO. No",style1)
			sheet1.write(s1,2,"Pump Model",style1)
			sheet1.write(s1,3,"Patten Number",style1)
			sheet1.write(s1,4,"Pattern Name",style1)
			sheet1.write(s1,5,"MOC",style1)
			sheet1.write(s1,6,"Pattern Check",style1)
			sheet1.write(s1,7,"Other Spec",style1)
			sheet1.write(s1,8,"Reqd. Qty",style1)
			sheet1.write(s1,9,"Stock Allocated",style1)
			sheet1.write(s1,10,"Pouring Qty",style1)
			sheet1.write(s1,11,"Each Weight",style1)
			sheet1.write(s1,12,"Total Weight",style1)
			
			
			s2=7
			for ele in data:							
						
				sheet1.write(s2,0,ele['schedule_no'])
				sheet1.write(s2,1,ele['order_no'])
				sheet1.write(s2,2,ele['pump_name'])
				sheet1.write(s2,3,ele['pattern_no'])
				sheet1.write(s2,4,ele['pattern_name'])
				sheet1.write(s2,5,ele['moc'])
				sheet1.write(s2,6,ele['pattern_check'])
				sheet1.write(s2,7,ele['other_spec'])
				sheet1.write(s2,8,ele['required_qty'])
				sheet1.write(s2,9,ele['stock_qty'])
				sheet1.write(s2,10,ele['pouring_qty'])
				sheet1.write(s2,11,ele['each_wight'])
				sheet1.write(s2,12,ele['total_weight'])
				
				s2+=1
			"""Parsing data as string """
			cur_mon = time.strftime('%Y-%B')
			file_data=StringIO.StringIO()
			o=wbk.save(file_data)		
			"""string encode of data in wksheet"""		
			out=base64.encodestring(file_data.getvalue())
			"""returning the output xls as binary"""
		return self.write(cr, uid, ids, {'rep_data':out, 'name': 'Foundry_Partlist'+'.xls','state': 'done'})	
		
		
	def unlink(self, cr, uid, ids,context=None):
		for rec in self.browse(cr, uid, ids):
			if rec.state == 'done':
				raise osv.except_osv(_('Unale to Delete !'),_('You can not delete Done state reports !!'))
		return super(kg_foundry_partlist_excel, self).unlink(cr, uid, ids, context)
	
	
	
kg_foundry_partlist_excel()
