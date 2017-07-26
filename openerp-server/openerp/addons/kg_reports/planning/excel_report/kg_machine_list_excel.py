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


class kg_machine_list_excel(osv.osv):

	_name = 'kg.machine.list.excel'
	_order = "date desc"

	_columns = {	
		
		'order_id': fields.many2one('ch.work.order.details','WO No' ,domain="[('state','=','confirmed')]"),
		'order_category': fields.selection([('pump','Pump'),('spare','Spare'),('access','Accessories')],'Purpose', required=True),
		
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
	}
	  
		
	def produce_xls(self, cr, uid, ids, context={}):
		
		import StringIO
		import base64
		
		try:
			import xlwt
		except:
		   raise osv.except_osv('Warning !','Please download python xlwt module from\nhttp://pypi.python.org/packages/source/x/xlwt/xlwt-0.7.2.tar.gz\nand install it')
		
		excel_rec =self.browse(cr,uid,ids[0])
		print"excel_rec..",excel_rec.order_id
		print"excel_rec.iddddddddd.",excel_rec.order_id.id
		work_rec = self.pool.get('ch.work.order.details').browse(cr,uid,excel_rec.order_id.id)	
		print"work_recwork_rec",work_rec.order_no
		print"trimming_diatrimming_dia",work_rec.trimming_dia
		print"flange_nameflange_name",work_rec.flange_standard.name
		print"pump_type...",work_rec.pump_model_id.name
		print"motor_power...",work_rec.motor_power
		
		if excel_rec.order_category == 'pump':
			category = 'pump'
			header_cate = "MACHINING LIST - (PUMP)"
		elif excel_rec.order_category == 'spare':
			category = 'spare'
			header_cate = "MACHINING LIST - (SPARE)"
		elif excel_rec.order_category == 'access':
			category = 'access'
			header_cate = "MACHINING LIST - (Accessories)"
		print"category",category
		if work_rec.flange_standard.name is None:
			flange_standard_data = ""
		else:
			flange_standard_data = work_rec.flange_standard.name
		if work_rec.trimming_dia is False:
			trimming_dia_data = ""
		else:
			trimming_dia_data = work_rec.trimming_dia
		if work_rec.motor_power is False:
			motor_power_data = ""
		else:
			motor_power_data = work_rec.motor_power
		order_ref = "ORDER REF : " + str(work_rec.order_no)
		pump_model = "PUMP MODEL: " + str(work_rec.pump_model_id.name)
		flage = "FLANGE STANDARD: " + str(flange_standard_data)
		trimming_dia = "TRIM DIA : " + str(trimming_dia_data)
		motor_power = "MOTOR FRAME : " + str(motor_power_data)
		cur_date = datetime.strptime(excel_rec.date, '%Y-%m-%d').strftime('%d-%m-%Y')
		date = "Date: " + str(cur_date)
		if work_rec.cc_drill == 'basic_design':
			cc_drill = "BASIC DESIGN"
		elif work_rec.cc_drill == 'basic_design_a':
			cc_drill = "BASIC DESIGN+A"
		elif work_rec.cc_drill == 'basic_design_c':
			cc_drill = "BASIC DESIGN+C"
		elif work_rec.cc_drill == 'nill':
			cc_drill = "NILL"
		else:
			cc_drill = ""
			
		cc_drill = "C.C.DRILL DETAILS : " + str(cc_drill)
		wbk = xlwt.Workbook()		
		style1 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz center;''borders: left thin, right thin, top thin') 
		style2 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz center;''borders: left thin, right thin, top thin, bottom thin') 
		style3 = xlwt.easyxf('borders: left thin, right thin, bottom thin')
		style9 = xlwt.easyxf('align: horiz right;''borders: left thin, right thin, bottom thin')
		style4 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz left;')
		style5 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz center;')
		style6 = xlwt.easyxf('font: height 200,color_index black;' 'align: vert centre, horiz left;''borders: left thin, right thin, top thin, bottom thin') 
		style7 = xlwt.easyxf('font: height 200,color_index black;' 'align: wrap on, vert centre, horiz left;''borders: left thin, right thin, top thin, bottom thin') 
		style8 = xlwt.easyxf('font: height 200,color_index black;' 'align: wrap on, vert centre, horiz centre;''borders: left thin, right thin, top thin, bottom thin') 
		
		if excel_rec.order_id.id:
			if excel_rec.order_category == 'access':		
				
				report_name = 'Accessories_List_Rpt.xls'	
			
				s1=7
				
				"""adding a worksheet along with name"""	
				
				sheet1 = wbk.add_sheet('Accessories List Copy')	
				
				s2=8
				
				k1=5
				sheet1.col(0).width = 8000
				sheet1.col(1).width = 12000
				sheet1.col(2).width = 12000
				sheet1.col(3).width = 12000
				
				
				sheet1.write_merge(0, 0, 0, 4,"SAM TURBO INDUSTRY PRIVATE LIMITED",style2)
				sheet1.row(0).height = 450
				sheet1.write_merge(1, 1, 0, 4,"Avinashi Road, Neelambur, Coimbatore - 641062",style8)
				sheet1.write_merge(2, 2, 0, 4,"Tel:3053555, 3053556,Fax : 0422-3053535",style8)
				sheet1.write_merge(3, 3, 0, 4,header_cate,style2)
				
				sheet1.write_merge(5, 5, 0, 2,order_ref,style3)
				sheet1.write_merge(5, 5, 3, 4,date,style3)
				
				
				sheet1.write_merge(6, 6, 0, 2, pump_model ,style3)
				sheet1.write_merge(6, 6, 3, 4,motor_power,style3)				
				
				s1=8
				
				sql = """		
							SELECT
							count(*) OVER (),
							row_number() OVER (),
							company.name as company_name,
							to_char(CURRENT_DATE::date,'dd-mm-YYYY') as date,
							work_order.order_no as wo_no,
							pump_type.name as pump_type,
							work_order.motor_power as moter_power,
							accessories.code as accessories_code,
							accessories.name as accessories_name,
							moc.name as moc_name,
							ch_access.qty::integer as qty,
							primemover.shaft_dia as prime_shaft_dia,
							accessories.is_coupling_flag as is_coupling,
							pump_type.pump_shaft_dia_at as pump_shaft_dia,
							case
							when accessories.is_coupling_flag = True then (coalesce(accessories.name,'-')||' - Shaft dia -'||coalesce(primemover.shaft_dia::text,'-')||'- Pump Shaft Dia - '||coalesce(pump_type.pump_shaft_dia_at::text,''))
							else '-' end as acc_name

							FROM ch_work_order_details work_order

							left join ch_wo_accessories ch_access on (ch_access.header_id = work_order.id)
							left join kg_accessories_master accessories on (accessories.id = ch_access.access_id)
							left join kg_pumpmodel_master pump_type on (pump_type.id = work_order.pump_model_id)
							left join kg_moc_master moc on (moc.id = ch_access.moc_id)
							left join res_company company on (company.id = accessories.company_id)
							left join ch_kg_crm_pumpmodel enq_line on (enq_line.id = work_order.enquiry_line_id)left join kg_primemover_master primemover on (primemover.id = enq_line.primemover_id)

							where
							ch_access.qty > 0

							and							 
							work_order.id = %s"""%(excel_rec.order_id.id)
				
				cr.execute(sql)		
				data = cr.dictfetchall()
					
				if data == []:
					raise osv.except_osv(_('Warning!'),_('No Data Found'))
				else:
				
					sheet1.col(0).width = 6000
					sheet1.col(1).width = 6000
					sheet1.col(2).width = 6000
					sheet1.col(3).width = 4000
					sheet1.col(4).width = 5000
					
					
					
					sheet1.write(s1,0,"Accessory Name",style1)
					sheet1.write(s1,1,"Accessory Code",style1)
					sheet1.write(s1,2,"Part Name",style1)
					sheet1.write(s1,3,"QTY",style1)
					sheet1.write(s1,4,"MOC",style1)
					
					
					s2=9
					for ele in data:							
								
						sheet1.write(s2,0,ele['acc_name'])
						sheet1.write(s2,1,ele['accessories_code'])
						sheet1.write(s2,2,ele['accessories_name'])
						sheet1.write(s2,3,ele['qty'])
						sheet1.write(s2,4,ele['moc_name'])
						
						s2+=1
					"""Parsing data as string """
					cur_mon = time.strftime('%Y-%B')
					file_data=StringIO.StringIO()
					o=wbk.save(file_data)		
					"""string encode of data in wksheet"""		
					out=base64.encodestring(file_data.getvalue())
					"""returning the output xls as binary"""
				return self.write(cr, uid, ids, {'rep_data':out, 'name': 'Acc_Machine_List'+'.xls','state': 'done'})
			else:
				report_name = 'Machine_List_Rpt.xls'	
			
				s1=7
				
				"""adding a worksheet along with name"""	
				
				sheet1 = wbk.add_sheet('Machine List Copy')	
				
				s2=8
				
				k1=5
				sheet1.col(0).width = 8000
				sheet1.col(1).width = 12000
				sheet1.col(2).width = 12000
				sheet1.col(3).width = 12000				
				
				sheet1.write_merge(0, 0, 0, 7,"SAM TURBO INDUSTRY PRIVATE LIMITED",style2)
				sheet1.row(0).height = 450
				sheet1.write_merge(1, 1, 0, 7,"Avinashi Road, Neelambur, Coimbatore - 641062",style8)
				sheet1.write_merge(2, 2, 0, 7,"Tel:3053555, 3053556,Fax : 0422-3053535",style8)
				sheet1.write_merge(3, 3, 0, 7,header_cate,style2)
				
				sheet1.write_merge(5, 5, 0, 2,order_ref,style3)
				sheet1.write_merge(5, 5, 3, 7,date,style3)
				
				
				sheet1.write_merge(6, 6, 0, 2, pump_model ,style3)
				sheet1.write_merge(6, 6, 3, 7,flage,style3)
				
				sheet1.write_merge(7, 7, 3, 7,trimming_dia,style3)
				sheet1.write_merge(8, 8, 3, 7,cc_drill,style3)
				
				s1=10				
				sql = """		
						SELECT

						case when (ROW_NUMBER()OVER(PARTITION By wo_no)=COUNT(wo_no)OVER(PARTITION By wo_no)) then 'stop' else '' end as brkneed,

						max(row_number) OVER (PARTITION by wo_no ORDER BY wo_no),
						* from (
						SELECT id,
						row_number() OVER (PARTITION BY wo_no ORDER by wo_no),
						dense_rank() OVER (ORDER by wo_no),category,
						company_name,date,wo_no,pump_type,trimming_dia,cc_drill,flange_name,position_no,pattern_no,pattern_name,moc_name,per_qty,qty,uom,remarks
						FROM (

						SELECT
						work_order.id as id,
						(CASE WHEN '%s' = 'pump'
						THEN '(PUMP)'
						WHEN '%s' = 'spare'
						THEN '(SPARE)'
						ELSE '-'
						end ) as category,
						company.name as company_name,
						to_char(CURRENT_DATE::date,'dd-mm-YYYY') as date,
						work_order.order_no as wo_no,
						pump_type.name as pump_type,
						work_order.trimming_dia as trimming_dia,
						(CASE WHEN work_order.cc_drill = 'basic_design'
						THEN 'BASIC DESIGN'
						WHEN work_order.cc_drill = 'basic_design_a'
						THEN 'BASIC DESIGN+A'
						WHEN work_order.cc_drill = 'basic_design_c'
						THEN 'BASIC DESIGN+C'
						WHEN work_order.cc_drill = 'nill'
						THEN 'NILL'
						ELSE ''
						end ) as cc_drill,
						flange.name as flange_name,

						position_num.name as position_no,
						pattern.name as pattern_no,
						pattern.pattern_name as pattern_name,
						moc.name as moc_name,


						(CASE WHEN '%s' = 'pump'
						THEN (ch_bom.qty/work_order.qty)::char
						WHEN '%s' = 'spare'
						THEN '-'
						ELSE '-'
						end ) as per_qty,
						ch_bom.qty as qty,
						'Nos' as uom,
						ch_bom.add_spec as remarks

						FROM ch_work_order_details work_order

						left join ch_order_bom_details ch_bom on (ch_bom.header_id = work_order.id)
						left join ch_pumpseries_flange flange on (flange.id = work_order.flange_standard)
						left join kg_pattern_master pattern on (pattern.id = ch_bom.pattern_id)
						left join kg_position_number position_num on (position_num.id = ch_bom.position_id)
						left join kg_pumpmodel_master pump_type on (pump_type.id = work_order.pump_model_id)
						left join kg_moc_master moc on (moc.id = ch_bom.moc_id)
						left join res_company company on (company.id = pattern.company_id)

						where ch_bom.flag_applicable = True and

						work_order.id = %s

						and work_order.order_category = '%s'

						UNION

						SELECT

						work_order.id as id,
						(CASE WHEN '%s' = 'pump'
						THEN '(PUMP)'
						WHEN '%s' = 'spare'
						THEN '(SPARE)'
						ELSE '-'
						end ) as category,
						company.name as company_name,
						to_char(CURRENT_DATE::date,'dd-mm-YYYY') as date,
						work_order.order_no as wo_no,
						pump_type.name as pump_type,
						work_order.trimming_dia as trimming_dia,
						(CASE WHEN work_order.cc_drill = 'basic_design'
						THEN 'BASIC DESIGN'
						WHEN work_order.cc_drill = 'basic_design_a'
						THEN 'BASIC DESIGN+A'
						WHEN work_order.cc_drill = 'basic_design_c'
						THEN 'BASIC DESIGN+C'
						WHEN work_order.cc_drill = 'nill'
						THEN 'NILL'
						ELSE ''
						end ) as cc_drill,
						flange.name as flange_name,
						position_num.name as position_no,
						machine.code as pattern_no,
						machine.name as pattern_name,
						moc.name as moc_name,

						(CASE WHEN '%s' = 'pump'
						THEN (ch_machineshop.qty/work_order.qty)::char
						WHEN '%s' = 'spare'
						THEN '-'
						ELSE '-'
						end ) as per_qty,

						ch_machineshop.qty as qty,
						'Nos' as uom,
						ch_machineshop.remarks as remarks

						FROM ch_work_order_details work_order

						left join ch_order_machineshop_details ch_machineshop on (ch_machineshop.header_id = work_order.id)
						left join kg_machine_shop machine on (machine.id = ch_machineshop.ms_id)
						left join ch_pumpseries_flange flange on (flange.id = work_order.flange_standard)
						left join kg_position_number position_num on (position_num.id = ch_machineshop.position_id)
						left join kg_pumpmodel_master pump_type on (pump_type.id = work_order.pump_model_id)
						left join kg_moc_master moc on (moc.id = ch_machineshop.moc_id)
						left join res_company company on (company.id = machine.company_id)


						where ch_machineshop.flag_applicable = True and

						work_order.id = %s

						and work_order.order_category = '%s'

						order by wo_no
						) AS SAMPLE
						) AS TEST"""%(category,category,category,category,excel_rec.order_id.id,category,category,category,category,category,excel_rec.order_id.id,category)
			
				cr.execute(sql)		
				data = cr.dictfetchall()
				
				if data == []:
					raise osv.except_osv(_('Warning!'),_('No Data Found'))
				else:
				
					sheet1.col(0).width = 4000
					sheet1.col(1).width = 5000
					sheet1.col(2).width = 5000
					sheet1.col(3).width = 5000
					sheet1.col(4).width = 5000
					sheet1.col(5).width = 5000
					sheet1.col(6).width = 5000
					sheet1.col(7).width = 5000
					
					
					sheet1.write(s1,0,"POSI NO",style1)
					sheet1.write(s1,1,"PAT.NO",style1)
					sheet1.write(s1,2,"PART NAME",style1)
					sheet1.write(s1,3,"MOC",style1)
					sheet1.write(s1,4,"QTY / P",style1)
					sheet1.write(s1,5,"Req. Qty",style1)
					sheet1.write(s1,6,"UOM",style1)
					sheet1.write(s1,7,"Remarks",style1)					
					s2=11
					for ele in data:								
						sheet1.write(s2,0,ele['position_no'],style9)
						sheet1.write(s2,1,ele['pattern_no'],style3)
						sheet1.write(s2,2,ele['pattern_name'],style3)
						sheet1.write(s2,3,ele['moc_name'],style3)
						sheet1.write(s2,4,ele['per_qty'],style9)
						sheet1.write(s2,5,ele['qty'],style9)
						sheet1.write(s2,6,ele['uom'],style3)
						sheet1.write(s2,7,ele['remarks'],style3)
						s2+=1
					"""Parsing data as string """
					cur_mon = time.strftime('%Y-%B')
					file_data=StringIO.StringIO()
					o=wbk.save(file_data)		
					"""string encode of data in wksheet"""		
					out=base64.encodestring(file_data.getvalue())
					"""returning the output xls as binary"""
				return self.write(cr, uid, ids, {'rep_data':out, 'name': 'Machine_List'+'.xls','state': 'done'})
		else:
			raise osv.except_osv(_('Warning!'),_('Work Order is must'))
		
		
		
		
	def unlink(self, cr, uid, ids,context=None):
		for rec in self.browse(cr, uid, ids):
			if rec.state == 'done':
				raise osv.except_osv(_('Unale to Delete !'),_('You can not delete Done state reports !!'))
		return super(kg_machine_list_excel, self).unlink(cr, uid, ids, context)
	
	
	
kg_machine_list_excel()
