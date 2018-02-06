from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta
import openerp.addons.decimal_precision as dp

class kg_scheduler(osv.osv):

	_name = "kg.scheduler"
	_description = "Scheduler Time Master"
	
	#~ def planning_vs_production_register_scheduler_mail(self,cr,uid,ids=0,context = None):		
		#~ cr.execute("""select all_daily_scheduler_mails('Planning Vs Production')""")
		#~ data = cr.fetchall();
		#~ print "data<<<<<<<<<", data
		#~ if data[0][0] is None:
			#~ return False		
		#~ if data[0][0] is not None:	
			#~ maildet = (str(data[0])).rsplit('~');
			#~ cont = data[0][0].partition('UNWANTED.')		
			#~ email_from = maildet[1]	
			#~ if maildet[2]:	
				#~ email_to = [maildet[2]]
			#~ else:
				#~ email_to = ['']			
			#~ if maildet[3]:
				#~ email_cc = [maildet[3]]	
			#~ else:
				#~ email_cc = ['']		
			#~ ir_mail_server = self.pool.get('ir.mail_server')			
			#~ if maildet[4] != '':
				#~ msg = ir_mail_server.build_email(
					#~ email_from = email_from,
					#~ email_to = email_to,
					#~ subject = maildet[4],
					#~ body = cont[0],
					#~ email_cc = email_cc,
					#~ object_id = ids and ('%s-%s' % (ids, 'kg.mail.settings')),
					#~ subtype = 'html',
					#~ subtype_alternative = 'plain')
				#~ res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
			#~ else:
				#~ pass
			#~ return True
		#~ 
	#~ def daily_stock_statement_scheduler_mail(self,cr,uid,ids=0,context = None):
	#~ 
		#~ cr.execute("""select all_daily_scheduler_mails('Daily Stock Statement')""")
		#~ data = cr.fetchall();		
		#~ if data[0][0] is None:
			#~ return False
		#~ if data[0][0] is not None:
			#~ maildet = (str(data[0])).rsplit('~');
			#~ cont = data[0][0].partition('UNWANTED.')		
			#~ email_from = maildet[1]		
			#~ if maildet[2]:	
				#~ email_to = [maildet[2]]
			#~ else:
				#~ email_to = ['']	
			#~ if maildet[3]:
				#~ email_cc = [maildet[3]]	
			#~ else:
				#~ email_cc = ['']		
			#~ ir_mail_server = self.pool.get('ir.mail_server')
			#~ if maildet[4] != '':
				#~ msg = ir_mail_server.build_email(
					#~ email_from = email_from,
					#~ email_to = email_to,
					#~ subject = maildet[4],
					#~ body = cont[0],
					#~ email_cc = email_cc,
					#~ object_id = ids and ('%s-%s' % (ids, 'kg.mail.settings')),
					#~ subtype = 'html',
					#~ subtype_alternative = 'plain')
				#~ res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
			#~ else:
				#~ pass
			#~ return True
				#~ 
			#~ 
	#~ def transaction_summary_list_scheduler_mail(self,cr,uid,ids=0,context = None):		
		#~ cr.execute("""select all_daily_scheduler_mails('Transaction Summary List')""")
		#~ data = cr.fetchall();
		#~ print "data<<<<<<<<<", data
		#~ 
		#~ 
		#~ if data[0][0] is None:
			#~ return False
		#~ if data[0][0] is not None:	
			#~ maildet = (str(data[0])).rsplit('~');
			#~ cont = data[0][0].partition('UNWANTED.')		
			#~ email_from = maildet[1]	
			#~ if maildet[2]:	
				#~ email_to = [maildet[2]]
			#~ else:
				#~ email_to = ['']			
			#~ if maildet[3]:
				#~ email_cc = [maildet[3]]	
			#~ else:
				#~ email_cc = ['']		
			#~ ir_mail_server = self.pool.get('ir.mail_server')
			#~ if maildet[4] != '':
				#~ msg = ir_mail_server.build_email(
					#~ email_from = email_from,
					#~ email_to = email_to,
					#~ subject = maildet[4],
					#~ body = cont[0],
					#~ email_cc = email_cc,
					#~ object_id = ids and ('%s-%s' % (ids, 'kg.mail.settings')),
					#~ subtype = 'html',
					#~ subtype_alternative = 'plain')
				#~ res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
			#~ else:
				#~ pass
			#~ return True
			
			
	def userwise_summary_list_scheduler_mail(self,cr,uid,ids=0,context = None):		
		cr.execute("""select all_daily_scheduler_mails('Daily Userwise Summary List')""")
		data = cr.fetchall();
		print "data<<<<<<<<<", data
		
		
		if data[0][0] is None:
			return False
		if data[0][0] is not None:	
			maildet = (str(data[0])).rsplit('~');
			cont = data[0][0].partition('UNWANTED.')		
			email_from = maildet[1]	
			if maildet[2]:	
				email_to = [maildet[2]]
			else:
				email_to = ['']			
			if maildet[3]:
				email_cc = [maildet[3]]	
			else:
				email_cc = ['']		
			ir_mail_server = self.pool.get('ir.mail_server')
			if maildet[4] != '':
				msg = ir_mail_server.build_email(
					email_from = email_from,
					email_to = email_to,
					subject = maildet[4],
					body = cont[0],
					email_cc = email_cc,
					object_id = ids and ('%s-%s' % (ids, 'kg.mail.settings')),
					subtype = 'html',
					subtype_alternative = 'plain')
				res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
			else:
				pass
			return True
	
	def daily_approved_po_grn_summary(self,cr,uid,ids=0,context = None):		
		
		cr.execute("""select sch_approved_po_grn('approved po and grn')""")
		data = cr.fetchall();
		print "data<<<<<<<<<", data
		
		if data[0][0] is None:
			return False
		if data[0][0] is not None:	
			maildet = (str(data[0])).rsplit('~');
			cont = data[0][0].partition('UNWANTED.')		
			email_from = maildet[1]	
			if maildet[2]:	
				email_to = [maildet[2]]
			else:
				email_to = ['']			
			if maildet[3]:
				email_cc = [maildet[3]]	
			else:
				email_cc = ['']		
			ir_mail_server = self.pool.get('ir.mail_server')
			if maildet[4] != '':
				msg = ir_mail_server.build_email(
					email_from = email_from,
					email_to = email_to,
					subject = maildet[4],
					body = cont[0],
					email_cc = email_cc,
					object_id = ids and ('%s-%s' % (ids, 'kg.mail.settings')),
					subtype = 'html',
					subtype_alternative = 'plain')
				res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
			else:
				pass
			return True
	
	## Fiscal Year Opening Stock Creation Process Start
	
	def opening_stock_new(self, cr, uid, ids,location_type,context=None):
		
		if location_type =='main':
			main_location = self.pool.get('stock.location').search(cr, uid, [('location_type','=','main')])
		else:
			main_location = self.pool.get('stock.location').search(cr, uid, [('location_type','!=','view')])

		stock_obj = self.pool.get('stock.move')
		physical_ids = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'transit')])
		module_obj = self.pool.get('ir.module.module').search(cr, uid, [('name','=','kg_physical_stock'),('state','=','installed')])

	   
		##fiscal year start date checking process--Starting
		
		last_year_date = (datetime.now() - relativedelta(years=1)).date()
		today = date.today()
	
		pre_fis_obj = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start','<=',last_year_date),('date_stop','>=',last_year_date)])
		pre_fis_id = self.pool.get('account.fiscalyear').browse(cr,uid,pre_fis_obj[0])
	  
		cur_fis_obj = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start','<=',today),('date_stop','>=',today)])
		cur_fis_id = self.pool.get('account.fiscalyear').browse(cr,uid,cur_fis_obj[0])
		fiscal_year = cur_fis_id.name
		
		##fiscal year start date checking process--Ending
		main_location_browse = self.pool.get('stock.location').browse(cr, uid, filter(lambda x: x not in physical_ids, main_location))
   
		for location in main_location_browse:
			cr.execute("""select count(*) as count from stock_move where flag_opening='t' and location_dest_id = %s and notes like '%s'"""%(location.id,'%'+fiscal_year+'%'))
			data = cr.fetchall();
			if data[0][0] == 0:
				location_id = location.id
				if location.location_type == 'main':
					move_type = 'in'
					location_type = 'main'
				else:
					move_type = 'out'
					location_type = 'sub'
				### product selection starts here###
				my_plist = []
				
				psql1 = """select distinct product_id from stock_move where location_dest_id=%s or location_id=%s"""%(location_id,location_id)	
				cr.execute(psql1)
				pdata = cr.dictfetchall()
			
				if pdata:
					for items in pdata:
						my_plist.append(items['product_id'])
					
				### product selection ends here###  

				### Getting details from Stock Move --- Starting ###	
					
				sql1="""select product_id as a_product_id, 
					case when product_id is not null then
					(select name_template from product_product where id = product_id) end as product,
					case when product_id is not null then
					(select uom_id from product_template where id = product_id) end as uom,
				  
					 (in_qty - out_qty) as close_qty

					from 

					(select distinct product_id,

					Sum(case when location_dest_id = %s and date::date <= '2017-03-31'
					then product_qty else 0 end) over(partition by product_id) as in_qty,

					Sum(case when location_id = %s  and date::date <= '2017-03-31'
					then product_qty else 0 end) over(partition by product_id) as out_qty

					from stock_move ) as sub_query
	
					"""%(location_id,location_id)   
				
				### Getting details from Stock Move --- Ending ### 
				
				if len(my_plist) >0:
					if len(tuple(my_plist)) == 1:
						liststr = str(tuple(my_plist)).replace(",", "")
					else:
						liststr = str(tuple(my_plist))  
					sql3 = """ where product_id in  %s """%(liststr)
				else:
					sql3 = """ """
				sql2 = """ order by 2"""
				sql = sql1+sql3+sql2
			   
				cr.execute(sql)
				data = cr.dictfetchall()		
				data.sort(key=lambda data: data['a_product_id'])
				
				### Physical Stock Entry Creation--- Starting###
				if module_obj and my_plist:
					physical_vals = {
							'name': 'Opening Entry - '+fiscal_year + ' - ' + location.name,
							'location_id': location_id,
							'state': 'approved',
											
							}
					physical_id = self.pool.get('kg.physical.stock').create(cr, uid, physical_vals, context=context)
				### Physical Stock Entry Creation--- Ending###  
				sno = 1
				
				if my_plist:
					for item in data:
						self.averageprice_calculation(cr,uid,0,item['a_product_id'],cur_fis_id.date_stop,context = None)
	
						avg_price_sql = """ select round(COALESCE(avg_price::numeric,0),2) as avg_price from ch_product_yearly_average_price where fiscal_id = %s and product_id = %s """%(cur_fis_id.id,item['a_product_id'])
						cr.execute(avg_price_sql)		  
						price_data = cr.dictfetchone()
						if price_data:
							avg_price = price_data['avg_price']
						else:
							avg_price = 0.00
							
							
						### Physical Stock Line Creation--- Starting###
						if module_obj:
							
							line_vals = {
								'sno':sno,
								'product_id':item['a_product_id'],
						
								'brand':' ',
								'uom':item['uom'],
								'qty':item['close_qty'],
								'physical_stock':item['close_qty'],
								'stock_pid':physical_id,
								'stock_type':location_type,
								'entry_mode':'auto',			
								'location_id':location_id,
								}
							if line_vals:
								common_line = self.pool.get('kg.physical.stock.line').create(cr,uid,line_vals,context=None)
							sno = sno + 1   
						
						### Physical Stock Line Creation--- Ending###	   
							
							
							
						### stock move creation--- Starting###
						
						if item['close_qty'] > 0 :  
			
							self.pool.get('ch.product.yearly.average.price').create(cr,uid,{'product_id':item['a_product_id'],
													'fiscal_id':cur_fis_id.id,
													'avg_price':avg_price or 0.00})
							vals = {
								'product_id': item['a_product_id'],
								'name':item['product'],
								'product_qty':item['close_qty'],
								'product_uos_qty':item['close_qty'],
								'po_to_stock_qty':item['close_qty'],
								'stock_uom':item['uom'],
								'product_uom': item['uom'],
								'location_id': physical_ids[0],
								'location_dest_id': location_id,
								'move_type': move_type,
								'state': 'done',
								'price_unit': avg_price,
								'price_tax': avg_price,
								'stock_rate':avg_price,
								'notes':'Opening Entry - '+fiscal_year + ' - ' + location.name,
							
								'transaction_type':'Opening Entry - '+fiscal_year + ' - ' + location.name,
								'flag_opening':True,
								'brand_id':False,			  
								}
							
							stock_obj.create(cr, uid, vals, context=context)
						### stock move creation--- Ending###
						
		return True
	
	def averageprice_calculation(self, cr, uid, ids,product_id,entry_date,context=None):
		fis_obj = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start','<=',entry_date),('date_stop','>=',entry_date)])
		fis_rec = self.pool.get('account.fiscalyear').browse(cr,uid,fis_obj[0])
		avg_obj = self.pool.get('ch.product.yearly.average.price')
		product_rec = self.pool.get('product.product').browse(cr,uid,product_id)
		avg_price1 = 0.00
		price = 0.00
		avg_price = []
		inv_line_obj = self.pool.get('ch.invoice.line').search(cr, uid, [('product_id','=',product_id)])
		inv_line_rec = self.pool.get('ch.invoice.line').browse(cr, uid, inv_line_obj)
		for item in inv_line_rec:
			inv_obj = self.pool.get('kg.purchase.invoice').search(cr, uid, [('id','=',item.header_id.id),('invoice_date','>=',fis_rec.date_start),('invoice_date','<=',fis_rec.date_stop)])
			if inv_obj:
				tax_price = item.price_subtotal / item.rec_qty
				avg_price1 = tax_price +(item.header_id.other_charge / (sum(map(lambda c:c.rec_qty or 1.0,item.header_id.line_ids))))
				avg_price.append(avg_price1)
		if len(avg_price) > 0:
			price = sum(avg_price)/len(avg_price)
		if product_rec.avg_line_ids:
			for item in product_rec.avg_line_ids:
				if item.fiscal_id.id == fis_rec.id:
					avg_obj.write(cr,uid,item.id,{'avg_price':price})
				else:
					avg_obj.create(cr,uid,{'product_id':product_id,
											'fiscal_id':fis_rec.id,
											'avg_price':price})
		else:
			avg_obj.create(cr,uid,{'product_id':product_id,
				'fiscal_id':fis_rec.id,
				'avg_price':price})
		
		return True
		
	def opening_stock_entry_creation(self, cr, uid, ids=0,context=None):
		
		self.opening_stock_new(cr,uid,0,'main',context = None)
		
		return True
	
	def sechedular_email_ids(self,cr,uid,ids,reg_string,context = None):
		email_from = []
		email_to = []
		email_cc = []
		val = {'email_from':'','email_to':'','email_cc':''}
		ir_model = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		mail_form_ids = self.pool.get('kg.mail.settings').search(cr,uid,[('active','=',True)])
		for ids in mail_form_ids:
			mail_form_rec = self.pool.get('kg.mail.settings').browse(cr,uid,ids)
			if mail_form_rec.sch_type == 'scheduler':
				s = mail_form_rec.sch_name
				if s == reg_string:
					email_sub = mail_form_rec.subject
					email_from.append(mail_form_rec.name)
					mail_line_id = self.pool.get('ch.mail.settings.line').search(cr,uid,[('header_id','=',ids)])
					for mail_id in mail_line_id:
						mail_line_rec = self.pool.get('ch.mail.settings.line').browse(cr,uid,mail_id)
						if mail_line_rec.to_address:
							email_to.append(mail_line_rec.mail_id)
						if mail_line_rec.cc_address:
							email_cc.append(mail_line_rec.mail_id)
				else:
					pass
			
		val['email_from'] = email_from
		val['email_to'] = email_to
		val['email_cc'] = email_cc
		return val
	
	def opening_stock_mail_creation(self, cr, uid, ids=0,context=None):
		today = date.today()
		cur_fis_obj = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start','<=',today),('date_stop','>=',today)])
		cur_fis_id = self.pool.get('account.fiscalyear').browse(cr,uid,cur_fis_obj[0])
		main_location = self.pool.get('stock.location').search(cr, uid, [('location_type','=','main')])
		for location in main_location:
			cr.execute("""select opening_stock_creation_scheduler_mails('Opening Stock Register',%s)"""%(location))
			data = cr.fetchall();
			location_rec = self.pool.get('stock.location').browse(cr, uid,location)
			vals = self.sechedular_email_ids(cr,uid,ids,reg_string = 'Opening Stock Register',context = context)
			if (not vals['email_to']) and (not vals['email_cc']):
				pass
			else:
				subject = cur_fis_id.company_id.name+"  :  Opening Stock for  "+ location_rec.name +"  -   "+ cur_fis_id.name
				print"subjectsubject",subject
				
				ir_mail_server = self.pool.get('ir.mail_server')
				msg = ir_mail_server.build_email(
					  email_from = vals['email_from'][0],
					  email_to = vals['email_to'],
					  subject = subject,
					  body = data[0][0],
					  email_cc = vals['email_cc'],
					  object_id = ids and ('%s-%s' % (ids, 'kg.scheduler')),
					  subtype = 'html',
					  subtype_alternative = 'plain')
				res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1,  context=context)
		
		return True
	
	## Fiscal Year Opening Stock Creation Process End	
	
	## Minimum stock qty atuo indent creation process start
	
	def auto_purchase_indent(self, cr, uid, ids=0, context=None):
		
		flag = 0
		product_obj = self.pool.get('product.product')
		product_ids = """ select id from product_product where flag_minqty_rule = 't'  and state = 'approved' """
		cr.execute(product_ids)
		product_data = cr.dictfetchall()
		print"product_data",product_data
		for i in list(product_data):
			value = i['id']
			product_id_val = self.pool.get('product.product').browse(cr, uid, value)
			print"product_id_valproduct_id_val",product_id_val
			lot_sql = """select COALESCE((select sum(pending_qty) from stock_production_lot where product_id=%s),0) + 
							COALESCE((select sum(pending_qty) from kg_depindent_line where product_id =%s),0) +
							COALESCE((select sum(pending_qty) from purchase_requisition_line where product_id=%s),0) +
							COALESCE((select sum(pending_qty) from purchase_order_line where product_id =%s),0) - 
							COALESCE((select minimum_qty from product_product where id=%s),0)
							as result"""%(value,value,value,value,value)
			cr.execute(lot_sql)
			lot_data = cr.dictfetchall()
			print"lot_datalot_datalot_data",lot_data
			if lot_data[0]['result'] < 0:
				flag = 1
		
		if flag == 1:
			dep_obj = self.pool.get('kg.depmaster')
			kg_purchase_id = self.pool.get('purchase.requisition')
			kg_purchase_line_id = self.pool.get('purchase.requisition.line')
			exp_date_sql= """ select current_date+7 as date """
			cr.execute(exp_date_sql)
			exp_date = cr.dictfetchall()
			dep_ids = dep_obj.search(cr,uid,[('name','=','DP52')])
			if dep_ids:
				dep_rec = dep_obj.browse(cr,uid,dep_ids[0])
			
			indent_ids = kg_purchase_id.create(cr,uid,
					{
					'dep_name': dep_rec.id,
					'indent_type': 'direct',
					'entry_mode': 'auto',
					'state': 'draft',
					'pi_flag': True,
					'note': 'This indent for full-fill the minimum stock level of inventory',
					})
			print"indent_idsindent_ids",indent_ids
			for j in list(product_data):
				value1 = j['id']
				product_id_val = self.pool.get('product.product').browse(cr, uid, value1)
				lot_sq = """select COALESCE((select sum(pending_qty) from stock_production_lot where product_id=%s),0) + 
							COALESCE((select sum(pending_qty) from kg_depindent_line where product_id =%s),0) +
							COALESCE((select sum(pending_qty) from purchase_requisition_line where product_id=%s),0) +
							COALESCE((select sum(pending_qty) from purchase_order_line where product_id =%s),0) - 
							COALESCE((select minimum_qty from product_product where id=%s),0)
							as result"""%(value1,value1,value1,value1,value1)
				cr.execute(lot_sq)
				lot_dat = cr.dictfetchall()
				print"lot_datlot_dat",lot_dat
				if lot_dat[0]['result'] < 0:
					cr.execute("""select reorder_qty from product_product where id =%s"""%(value1)) 
					reorder_qty = cr.dictfetchall()
					cr.execute("""select sum(pending_qty) from stock_production_lot where product_id=%s"""%(value1)) 
					curr_qty = cr.dictfetchall()
					cur_date_sql= """ select current_date"""
					cr.execute(cur_date_sql)
					cur_date = cr.dictfetchall()
					pi_line_id = kg_purchase_line_id.create(cr,uid,
						{
						'requisition_id':indent_ids,
						'product_id':value1,
						'product_uom_id':product_id_val.uom_po_id.id,
						'product_qty':reorder_qty[0]['reorder_qty'],
						'pending_qty':reorder_qty[0]['reorder_qty'],
						'stock_qty':curr_qty[0]['sum'] or 0,
						'line_state':'noprocess',
						'name':'PILINE',
						'line_date':cur_date[0]['date'],
						'note':'This indent for full-fill the minimum stock level of inventory ',
						})
					print"pi_line_idpi_line_id",pi_line_id
		
		return
	
	## Minimum stock qty atuo indent creation process end
	
	
	def auto_scheduler_pouring_date(self,cr,uid,ids=0,context = None):		
		cr.execute("""select auto_scheduler_foundry('Pouring_Date')""")
		data = cr.fetchall();
		print "data<<<<<<<<<", data
		return True
	
	def auto_scheduler_cc_date(self,cr,uid,ids=0,context = None):		
		cr.execute("""select auto_scheduler_foundry('CC_Date')""")
		data = cr.fetchall();
		print "data<<<<<<<<<", data
		return True
	
	def auto_scheduler_id_date(self,cr,uid,ids=0,context = None):		
		cr.execute("""select auto_scheduler_foundry('ID_Date')""")
		data = cr.fetchall();
		print "data<<<<<<<<<", data
		return True
	def auto_scheduler_in_house_date(self,cr,uid,ids=0,context = None):		
		cr.execute("""select auto_scheduler_foundry('inhouse_Date')""")
		data = cr.fetchall();
		print "data<<<<<<<<<", data
		return True
	def auto_scheduler_sc_wo_date(self,cr,uid,ids=0,context = None):		
		cr.execute("""select auto_scheduler_foundry('sc_wo_Date')""")
		data = cr.fetchall();
		print "data<<<<<<<<<", data
		return True
	def auto_scheduler_rm_date(self,cr,uid,ids=0,context = None):		
		cr.execute("""select auto_scheduler_foundry('RM_Date')""")
		data = cr.fetchall();
		print "data<<<<<<<<<", data
		return True
	
	## Weekly once primecostview entry delete start
	
	def auto_primecost_delete(self, cr, uid, ids=0, context=None):
		
		cr.execute(''' delete from kg_primecost_view where entry_date < (current_date - interval '7' day)::date ''')
		
		return True
	
	## Weekly once primecostview entry delete end
	
	### Below function deletes the past 7 days records daily starts ###
	
	def weekly_excel_report_deletion(self,cr,uid,ids=0,context = None):
		cr.execute("""select excel_deletion()""")
		data = cr.fetchall();
		return True
	
	### Below function deletes the past 7 days records daily ends ###
	
	def approved_po_mail(self,cr,uid,ids=0,context=None):
		cr.execute("""select trans_po_approved('approved po')""")
		data = cr.fetchall();
		if (data[0][0] is None) and (data[0][0] != ''):	
			return False
		if (data[0][0] is not None) and (data[0][0] != ''):	
			maildet = (str(data[0])).rsplit('~');
			cont = data[0][0].partition('UNWANTED.')		
			email_from = maildet[1]	
			if maildet[2]:	
				email_to = [maildet[2]]
			else:
				email_to = ['']			
			if maildet[3]:
				email_cc = [maildet[3]]	
			else:
				email_cc = ['']		
			ir_mail_server = self.pool.get('ir.mail_server')
			if maildet[4] != '':
				msg = ir_mail_server.build_email(
					email_from = email_from,
					email_to = email_to,
					subject = maildet[4],
					body = cont[0],
					email_cc = email_cc,
					object_id = ids and ('%s-%s' % (ids, 'kg.mail.settings')),
					subtype = 'html',
					subtype_alternative = 'plain')
				res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
			else:
				pass
		
		return True
		
	def create_sch_indent(self,cr,uid,ids=0,context=None):
			

		#### Department Indent Creation for MOC Raw materials  ###
			
		### Foundry Items ###
		
		### Foundry item only ##
		
		cr.execute(''' select schedule_id,entry_date,id from kg_indent_queue where state = 'pending' ''')
					
		schedule_ids = cr.fetchall();
		
		if schedule_ids:
			for entry in schedule_ids:
				print"entry",entry[0]
				print"entry",entry[1]
				
		
				indent_id = 0
				
				cr.execute("""
					select order_line_id,pump_model_id,sum(indent_qty) as indent_qty from 

						(

						select (raw.qty * order_bom.qty) as indent_qty,raw.product_id,order_bom.header_id as order_line_id,
						wo_line.pump_model_id
						from ch_moc_raw_material as raw
						left join ch_order_bom_details order_bom on raw.header_id = order_bom.moc_id
						left join ch_work_order_details wo_line on order_bom.header_id = wo_line.id
						where order_bom.flag_applicable = 't' and order_bom.header_id in (select order_line_id from 
						ch_schedule_details where header_id = %s and qty > 0
						)
						)
						as sub_query
						group by order_line_id,pump_model_id"""%(entry[0]))
				foundry_pumpmodel_details = cr.dictfetchall();
				if foundry_pumpmodel_details:
				
					for foundry_pm_item in foundry_pumpmodel_details:
						
						### Getting Pump Model Qty ###
						order_line_rec = self.pool.get('ch.work.order.details').browse(cr, uid, foundry_pm_item['order_line_id'])
						
						for indent_header in range(order_line_rec.pump_rem_qty): 
						
							### Creation of Department Indent Header ###
						
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP15')])
							
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry[1]))
							seq_name = cr.fetchone();

							dep_indent_obj = self.pool.get('kg.depindent')
							foundry_dep_indent_vals = {
								'name':'',
								'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
								'dep_name':dep_id[0],
								'entry_mode':'auto',
								'state': 'approved',
								'indent_type': 'production',
								'name': seq_name[0],
								'order_id': order_line_rec.header_id.id,
								'order_line_id': order_line_rec.id,
								'src_location_id': location.main_location.id,
								'dest_location_id': location.stock_location.id
								}
								
							#~ indent_id = dep_indent_obj.create(cr, uid, foundry_dep_indent_vals)
						
							cr.execute("""
								select type,order_line_id,product_id,pump_model_id,pattern_id,position_id,moc_id,sum(indent_qty) as indent_qty from 

									(

									select (raw.qty * order_bom.qty) as indent_qty,raw.product_id,wo_line.pump_model_id,order_bom.pattern_id,
									order_bom.header_id as order_line_id,order_bom.position_id as position_id,order_bom.moc_id as moc_id,'foun'::text as type
									from ch_moc_raw_material as raw
									left join ch_order_bom_details order_bom on raw.header_id = order_bom.moc_id
									left join ch_work_order_details wo_line on order_bom.header_id = wo_line.id
									where order_bom.flag_applicable = 't' and order_bom.header_id in (select distinct order_line_id 
									from ch_schedule_details  where header_id = %s and qty > 0
									)								

									)

									as sub_query
									where pump_model_id = %s  and
									order_line_id = %s
									group by type,order_line_id,product_id,pump_model_id,pattern_id,position_id,moc_id """%(entry[0],foundry_pm_item['pump_model_id'],order_line_rec.id))
							foundry_product_details = cr.dictfetchall();
							
							for foundry_indent_item in foundry_product_details:
								dep_indent_line_obj = self.pool.get('kg.depindent.line')
								product_rec = self.pool.get('product.product').browse(cr, uid, foundry_indent_item['product_id'])
								
								pattern_obj = self.pool.get('kg.pattern.master')
								pattern_rec = pattern_obj.browse(cr, uid, foundry_indent_item['pattern_id'])
								
								if foundry_indent_item['type'] == 'foun':
									indent_qty = foundry_indent_item['indent_qty']/order_line_rec.qty
								else:
									indent_qty = foundry_indent_item['indent_qty']
								
								foundry_dep_indent_line_vals = {
									'indent_id':indent_id,
									'product_id':foundry_indent_item['product_id'],
									'dep_id':dep_id[0],
									'line_state':'noprocess',
									'line_date':entry[1],
									'pattern_id':foundry_indent_item['pattern_id'],
									'uom':product_rec.uom_id.id,
									'qty': indent_qty,
									'pending_qty': indent_qty,
									'issue_pending_qty': indent_qty,
									'fns_item_name':pattern_rec.pattern_name,
									'position_id': foundry_indent_item['position_id'],
									'moc_id': foundry_indent_item['moc_id'],
								}
								
								#~ indent_line_id = dep_indent_line_obj.create(cr, uid, foundry_dep_indent_line_vals)

				## Accessories Foundry Item Only ##
				
				cr.execute("""
					select acc_line_id,order_line_id,pump_model_id,sum(indent_qty) as indent_qty from 

						(					

						select (raw.qty * acc_order_bom.qty) as indent_qty,raw.product_id,wo_acc_line.header_id 
						as order_line_id,wo_line.pump_model_id,wo_acc_line.id as acc_line_id
						from ch_moc_raw_material as raw
						left join ch_wo_accessories_foundry acc_order_bom on raw.header_id = acc_order_bom.moc_id
						left join ch_wo_accessories wo_acc_line on acc_order_bom.header_id = wo_acc_line.id
						left join ch_work_order_details wo_line on wo_acc_line.header_id = wo_line.id
						where acc_order_bom.is_applicable = 't' and wo_acc_line.header_id in (select order_line_id from 
						ch_schedule_details where header_id = %s and qty > 0
						)

						)
						as sub_query
						group by acc_line_id,order_line_id,pump_model_id"""%(entry[0]))
				acc_pumpmodel_details = cr.dictfetchall();
				if acc_pumpmodel_details:
				
					for acc_pm_item in acc_pumpmodel_details:
						
						### Getting Pump Model Qty ###
						order_line_rec = self.pool.get('ch.work.order.details').browse(cr, uid, acc_pm_item['order_line_id'])
						acc_line_rec = self.pool.get('ch.wo.accessories').browse(cr, uid, acc_pm_item['acc_line_id'])
						acc_qty = int(acc_line_rec.qty)		
						for indent_header in range(acc_qty): 
						
							### Creation of Department Indent Header ###
						
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP15')])
							
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry[1]))
							seq_name = cr.fetchone();

							dep_indent_obj = self.pool.get('kg.depindent')
							acc_dep_indent_vals = {
								'name':'',
								'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
								'dep_name':dep_id[0],
								'entry_mode':'auto',
								'state': 'approved',
								'indent_type': 'production',
								'name': seq_name[0],
								'order_id': order_line_rec.header_id.id,
								'order_line_id': order_line_rec.id,
								'src_location_id': location.main_location.id,
								'dest_location_id': location.stock_location.id
								}
								
							#~ indent_id = dep_indent_obj.create(cr, uid, acc_dep_indent_vals)
						
							cr.execute("""
								select type,order_line_id,product_id,pump_model_id,pattern_id,position_id,moc_id,sum(indent_qty) as indent_qty from 

									(								

									select (raw.qty * acc_order_bom.qty) as indent_qty,raw.product_id,wo_line.pump_model_id,acc_order_bom.pattern_id,
									wo_acc_line.header_id as order_line_id,acc_order_bom.position_id as position_id,acc_order_bom.moc_id as moc_id,'acc'::text as type
									from ch_moc_raw_material as raw
									left join ch_wo_accessories_foundry acc_order_bom on raw.header_id = acc_order_bom.moc_id
									left join ch_wo_accessories wo_acc_line on acc_order_bom.header_id = wo_acc_line.id
									left join ch_work_order_details wo_line on wo_acc_line.header_id = wo_line.id
									where acc_order_bom.is_applicable = 't' and wo_acc_line.header_id in (select order_line_id from 
									ch_schedule_details where header_id = %s and qty > 0
									)

									)

									as sub_query
									where pump_model_id = %s  and
									order_line_id = %s
									group by type,order_line_id,product_id,pump_model_id,pattern_id,position_id,moc_id """%(entry[0],acc_pm_item['pump_model_id'],order_line_rec.id))
							acc_product_details = cr.dictfetchall();
							
							for acc_indent_item in acc_product_details:
								dep_indent_line_obj = self.pool.get('kg.depindent.line')
								product_rec = self.pool.get('product.product').browse(cr, uid, acc_indent_item['product_id'])
								
								pattern_obj = self.pool.get('kg.pattern.master')
								pattern_rec = pattern_obj.browse(cr, uid, acc_indent_item['pattern_id'])
								
								if acc_indent_item['type'] == 'foun':
									indent_qty = acc_indent_item['indent_qty']/order_line_rec.qty
								else:
									indent_qty = acc_indent_item['indent_qty']
								
								acc_dep_indent_line_vals = {
									'indent_id':indent_id,
									'product_id':acc_indent_item['product_id'],
									'dep_id':dep_id[0],
									'line_state':'noprocess',
									'line_date':entry[1],
									'pattern_id':acc_indent_item['pattern_id'],
									'uom':product_rec.uom_id.id,
									'qty': indent_qty,
									'pending_qty': indent_qty,
									'issue_pending_qty': indent_qty,
									'fns_item_name':pattern_rec.pattern_name,
									'position_id': acc_indent_item['position_id'],
									'moc_id': acc_indent_item['moc_id'],
								}
								
								#~ indent_line_id = dep_indent_line_obj.create(cr, uid, acc_dep_indent_line_vals)
						
				#### Fabrication False Machine shop Items only ###		
						
				cr.execute("""
					select pump_model_id,order_line_id,sum(indent_qty) as indent_qty from 

						(
						select raw.qty as indent_qty,raw.product_id,wo_line.pump_model_id,
						order_ms.header_id as order_line_id
						from ch_wo_ms_raw as raw
						left join ch_order_machineshop_details order_ms on raw.header_id = order_ms.id
						left join kg_machine_shop ms_master on ms_master.id = order_ms.ms_id
						left join ch_work_order_details wo_line on order_ms.header_id = wo_line.id
						where ms_master.flag_fabrication = 'f' and order_ms.flag_applicable = 't' and order_ms.header_id in (select distinct order_line_id
						from ch_schedule_details where header_id = %s
						)					
						)
						as sub_query
						group by order_line_id,pump_model_id"""%(entry[0]))
				ms_pumpmodel_details = cr.dictfetchall();
				
				if ms_pumpmodel_details:
					
					for ms_pm_item in ms_pumpmodel_details:
						
						### Getting Pump Model Qty ###
						order_line_rec = self.pool.get('ch.work.order.details').browse(cr, uid, ms_pm_item['order_line_id'])
						
						for indent_header in range(order_line_rec.pump_rem_qty): 
							### Creation of Department Indent Header ###
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP2')])
							
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry[1]))
							seq_name = cr.fetchone();
							
							dep_indent_obj = self.pool.get('kg.depindent')
							if ms_pm_item['indent_qty'] > 0:
								ms_dep_indent_vals = {
									'name':'',
									'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
									'dep_name':dep_id[0],
									'entry_mode':'auto',
									'state': 'approved',
									'indent_type': 'production',
									'name': seq_name[0],
									'order_id': order_line_rec.header_id.id,
									'order_line_id': order_line_rec.id,
									'src_location_id': location.main_location.id,
									'dest_location_id': location.stock_location.id
									}
									
								indent_id = dep_indent_obj.create(cr, uid, ms_dep_indent_vals)
								
								cr.execute("""
									select type,pump_model_id,ms_item,product_id,uom,order_line_id,order_ms_id,position_id,moc_id,sum(indent_qty) as indent_qty from 

										(
										select raw.qty as indent_qty,raw.product_id,raw.uom,wo_line.pump_model_id,
										order_ms.header_id as order_line_id, raw.id as ms_item, order_ms.id as order_ms_id,
										order_ms.position_id as position_id,order_ms.moc_id as moc_id,'foun'::text as type
										from ch_wo_ms_raw as raw
										left join ch_order_machineshop_details order_ms on raw.header_id = order_ms.id
										left join kg_machine_shop ms_master on ms_master.id = order_ms.ms_id
										left join ch_work_order_details wo_line on order_ms.header_id = wo_line.id
										where ms_master.flag_fabrication = 'f' and order_ms.flag_applicable = 't' and order_ms.header_id in (select distinct order_line_id 
										from ch_schedule_details  where header_id = %s)							
										
										
										)

										as sub_query
										where pump_model_id = %s and order_line_id = %s
										group by type,order_line_id,pump_model_id,ms_item,product_id,uom,order_ms_id,position_id,moc_id """%(entry[0],ms_pm_item['pump_model_id'],order_line_rec.id))
								ms_product_details = cr.dictfetchall();
								
								for ms_indent_item in ms_product_details:
									dep_indent_line_obj = self.pool.get('kg.depindent.line')
									product_rec = self.pool.get('product.product').browse(cr, uid, ms_indent_item['product_id'])
									
									if ms_indent_item['type'] == 'foun':
										ms_raw_obj = self.pool.get('ch.wo.ms.raw')
										ms_raw_rec = ms_raw_obj.browse(cr, uid, ms_indent_item['ms_item'])
										ms_bot_id = ms_raw_rec.header_id.ms_id.id
										fns_item_name = ms_raw_rec.header_id.name
										
										ms_order_obj = self.pool.get('ch.order.machineshop.details')
										ms_order_rec = ms_order_obj.browse(cr, uid, ms_indent_item['order_ms_id'])
										if ms_order_rec.header_id.pump_model_type == 'horizontal':
											length = ms_raw_rec.length
										else:
											length = ms_order_rec.length
											if length == 0:
												length = ms_raw_rec.length
										
									elif ms_indent_item['type'] == 'acc':
										ms_raw_obj = self.pool.get('ch.ms.raw.material')
										ms_raw_rec = ms_raw_obj.browse(cr, uid, ms_indent_item['ms_item'])
										ms_bot_id = ms_raw_rec.header_id.id
										fns_item_name = ms_raw_rec.header_id.code
										ms_acc_obj = self.pool.get('ch.wo.accessories.ms')
										ms_order_rec = ms_acc_obj.browse(cr, uid, ms_indent_item['order_ms_id'])
										length = ms_raw_rec.length
									else:
										indent_qty = ms_indent_item['indent_qty']
										cutting_qty = 0
										
									if length > 0:
										
										if ms_raw_rec.uom_conversation_factor == 'one_dimension':	
											if product_rec.uom_id.id == product_rec.uom_po_id.id:
												indent_qty = ms_indent_item['indent_qty']
												cutting_qty = ms_indent_item['indent_qty']
											else:				
												indent_qty =  (length * ms_raw_rec.temp_qty)
												cutting_qty = ms_raw_rec.temp_qty
										if ms_raw_rec.uom_conversation_factor == 'two_dimension':
											indent_qty = (length * ms_raw_rec.breadth * ms_raw_rec.temp_qty)
											cutting_qty = ms_raw_rec.temp_qty
									else:
										if ms_indent_item['indent_qty'] == None:
											indent_qty = 0
										else:
											indent_qty = ms_indent_item['indent_qty']
										cutting_qty = 0											
										
											
									#~ ### Cutting qty division by qty ###
									if ms_indent_item['type'] == 'foun':
										if order_line_rec.order_category in ('pump','access'):
											cutting_qty = cutting_qty/order_line_rec.qty
											indent_qty = indent_qty/order_line_rec.qty
										else:
											cutting_qty = cutting_qty
											indent_qty = indent_qty
									else:
										cutting_qty = cutting_qty
										indent_qty = indent_qty
										
									ms_dep_indent_line_vals = {
										'indent_id':indent_id,
										'product_id':ms_indent_item['product_id'],
										'uom':ms_indent_item['uom'],
										'dep_id':dep_id[0],
										'line_state':'noprocess',
										'line_date':entry[1],
										'qty':indent_qty,
										'pending_qty':indent_qty,
										'issue_pending_qty':indent_qty,
										'cutting_qty': cutting_qty,
										'ms_bot_id':ms_bot_id,
										'fns_item_name':fns_item_name,
										'position_id': ms_indent_item['position_id'],
										'moc_id': ms_indent_item['moc_id'],
										'length': length,
										'breadth': ms_raw_rec.breadth,										
										'uom_conversation_factor': ms_raw_rec.uom_conversation_factor,
									}
									
									indent_line_id = dep_indent_line_obj.create(cr, uid, ms_dep_indent_line_vals)
										
				#### Fabrication True Machine shop Items only ###		
						
				cr.execute("""
					select pump_model_id,order_line_id,sum(indent_qty) as indent_qty from 

						(
						select raw.qty as indent_qty,raw.product_id,wo_line.pump_model_id,
						order_ms.header_id as order_line_id
						from ch_wo_ms_raw as raw
						left join ch_order_machineshop_details order_ms on raw.header_id = order_ms.id
						left join kg_machine_shop ms_master on ms_master.id = order_ms.ms_id
						left join ch_work_order_details wo_line on order_ms.header_id = wo_line.id
						where ms_master.flag_fabrication = 't' and order_ms.flag_applicable = 't' and order_ms.header_id in (select distinct order_line_id
						from ch_schedule_details where header_id = %s
						)					
						)
						as sub_query
						group by order_line_id,pump_model_id"""%(entry[0]))
				ms_pumpmodel_details = cr.dictfetchall();
				
				if ms_pumpmodel_details:
					
					for ms_pm_item in ms_pumpmodel_details:
						
						### Getting Pump Model Qty ###
						order_line_rec = self.pool.get('ch.work.order.details').browse(cr, uid, ms_pm_item['order_line_id'])
						
						for indent_header in range(order_line_rec.pump_rem_qty): 
							### Creation of Department Indent Header ###
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP25')])
							
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry[1]))
							seq_name = cr.fetchone();
							
							dep_indent_obj = self.pool.get('kg.depindent')
							if ms_pm_item['indent_qty'] > 0:
								ms_dep_indent_vals = {
									'name':'',
									'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
									'dep_name':dep_id[0],
									'entry_mode':'auto',
									'state': 'approved',
									'indent_type': 'production',
									'name': seq_name[0],
									'order_id': order_line_rec.header_id.id,
									'order_line_id': order_line_rec.id,
									'src_location_id': location.main_location.id,
									'dest_location_id': location.stock_location.id
									}
									
								indent_id = dep_indent_obj.create(cr, uid, ms_dep_indent_vals)
								
								cr.execute("""
									select type,pump_model_id,ms_item,product_id,uom,order_line_id,order_ms_id,position_id,moc_id,sum(indent_qty) as indent_qty from 

										(
										select raw.qty as indent_qty,raw.product_id,raw.uom,wo_line.pump_model_id,
										order_ms.header_id as order_line_id, raw.id as ms_item, order_ms.id as order_ms_id,
										order_ms.position_id as position_id,order_ms.moc_id as moc_id,'foun'::text as type
										from ch_wo_ms_raw as raw
										left join ch_order_machineshop_details order_ms on raw.header_id = order_ms.id
										left join kg_machine_shop ms_master on ms_master.id = order_ms.ms_id
										left join ch_work_order_details wo_line on order_ms.header_id = wo_line.id
										where ms_master.flag_fabrication = 't' and order_ms.flag_applicable = 't' and order_ms.header_id in (select distinct order_line_id 
										from ch_schedule_details  where header_id = %s)							
										
										
										)

										as sub_query
										where pump_model_id = %s and order_line_id = %s
										group by type,order_line_id,pump_model_id,ms_item,product_id,uom,order_ms_id,position_id,moc_id """%(entry[0],ms_pm_item['pump_model_id'],order_line_rec.id))
								ms_product_details = cr.dictfetchall();
								
								for ms_indent_item in ms_product_details:
									dep_indent_line_obj = self.pool.get('kg.depindent.line')
									product_rec = self.pool.get('product.product').browse(cr, uid, ms_indent_item['product_id'])
									
									if ms_indent_item['type'] == 'foun':
										ms_raw_obj = self.pool.get('ch.wo.ms.raw')
										ms_raw_rec = ms_raw_obj.browse(cr, uid, ms_indent_item['ms_item'])
										ms_bot_id = ms_raw_rec.header_id.ms_id.id
										fns_item_name = ms_raw_rec.header_id.name
										
										ms_order_obj = self.pool.get('ch.order.machineshop.details')
										ms_order_rec = ms_order_obj.browse(cr, uid, ms_indent_item['order_ms_id'])
										if ms_order_rec.header_id.pump_model_type == 'horizontal':
											length = ms_raw_rec.length
										else:
											length = ms_order_rec.length
											if length == 0:
												length = ms_raw_rec.length
										
									elif ms_indent_item['type'] == 'acc':
										ms_raw_obj = self.pool.get('ch.ms.raw.material')
										ms_raw_rec = ms_raw_obj.browse(cr, uid, ms_indent_item['ms_item'])
										ms_bot_id = ms_raw_rec.header_id.id
										fns_item_name = ms_raw_rec.header_id.code
										ms_acc_obj = self.pool.get('ch.wo.accessories.ms')
										ms_order_rec = ms_acc_obj.browse(cr, uid, ms_indent_item['order_ms_id'])
										length = ms_raw_rec.length
									else:
										indent_qty = ms_indent_item['indent_qty']
										cutting_qty = 0
										
									if length > 0:
										
										if ms_raw_rec.uom_conversation_factor == 'one_dimension':	
											if product_rec.uom_id.id == product_rec.uom_po_id.id:
												indent_qty = ms_indent_item['indent_qty']
												cutting_qty = ms_indent_item['indent_qty']
											else:				
												indent_qty =  (length * ms_raw_rec.temp_qty)
												cutting_qty = ms_raw_rec.temp_qty
										if ms_raw_rec.uom_conversation_factor == 'two_dimension':
											indent_qty = (length * ms_raw_rec.breadth * ms_raw_rec.temp_qty)
											cutting_qty = ms_raw_rec.temp_qty
									else:
										if ms_indent_item['indent_qty'] == None:
											indent_qty = 0
										else:
											indent_qty = ms_indent_item['indent_qty']
										cutting_qty = 0
									
									
											
									#~ ### Cutting qty division by qty ###
									if ms_indent_item['type'] == 'foun':
										if order_line_rec.order_category in ('pump','access'):
											cutting_qty = cutting_qty/order_line_rec.qty
											indent_qty = indent_qty/order_line_rec.qty
										else:
											cutting_qty = cutting_qty
											indent_qty = indent_qty
									else:
										cutting_qty = cutting_qty
										indent_qty = indent_qty
										
									
									ms_dep_indent_line_vals = {
										'indent_id':indent_id,
										'product_id':ms_indent_item['product_id'],
										'uom':ms_indent_item['uom'],
										'dep_id':dep_id[0],
										'line_state':'noprocess',
										'line_date':entry[1],
										'qty':indent_qty,
										'pending_qty':indent_qty,
										'issue_pending_qty':indent_qty,
										'cutting_qty': cutting_qty,
										'ms_bot_id':ms_bot_id,
										'fns_item_name':fns_item_name,
										'position_id': ms_indent_item['position_id'],
										'moc_id': ms_indent_item['moc_id'],
										'length': length,
										'breadth': ms_raw_rec.breadth,										
										'uom_conversation_factor': ms_raw_rec.uom_conversation_factor,
									}
									
									indent_line_id = dep_indent_line_obj.create(cr, uid, ms_dep_indent_line_vals)
			
				### Fabrication True Machine Shop Item only, Create for line item
				
				cr.execute("""
					select 
					wo_line.header_id as order_id,wo_line.id as order_line_id, order_ms.id as order_ms_id,order_ms.qty as qty,
					order_ms.ms_id as ms_id,order_ms.moc_id as moc_id


					from ch_order_machineshop_details as order_ms

					left join kg_machine_shop ms_master on ms_master.id = order_ms.ms_id
					left join ch_work_order_details wo_line on order_ms.header_id = wo_line.id
					where ms_master.flag_fabrication = 't' and order_ms.flag_applicable = 't' and order_ms.header_id in (select distinct order_line_id 
					from ch_schedule_details  where header_id = %s)"""%(entry[0]))
				
				flag_fabrication_details = cr.dictfetchall();
				
				if flag_fabrication_details:
					
					for flag_fabrication_item in flag_fabrication_details:
						fabrication_obj = self.pool.get('kg.fabrication.process')							
						fabrication_vals = {
							'order_id':flag_fabrication_item['order_id'],
							'order_line_id':flag_fabrication_item['order_line_id'],
							'ms_line_id':flag_fabrication_item['order_ms_id'],
							'ms_id':flag_fabrication_item['ms_id'],
							'moc_id':flag_fabrication_item['moc_id'],
							'schedule_qty':flag_fabrication_item['qty'],							
							'qty':flag_fabrication_item['qty'],							
							'entry_mode':'auto',
							'state': 'pending',
							
							}
							
						fabrication_id = fabrication_obj.create(cr, uid, fabrication_vals)
					
						
				### Fabrication False Accessories Machine Shop Item only
				
				cr.execute("""
				select acc_line_id,pump_model_id,order_line_id,sum(indent_qty) as indent_qty from 
						(
						select raw.qty as indent_qty,raw.product_id,wo_line.pump_model_id,
						wo_acc_line.header_id as order_line_id,wo_acc_line.id as acc_line_id
						from ch_ms_raw_material as raw
						left join ch_wo_accessories_ms acc_order_ms on raw.header_id = acc_order_ms.ms_id
						left join kg_machine_shop ms_master on ms_master.id = acc_order_ms.ms_id
						left join ch_wo_accessories wo_acc_line on acc_order_ms.header_id = wo_acc_line.id
						left join ch_work_order_details wo_line on wo_acc_line.header_id = wo_line.id
						where ms_master.flag_fabrication = 'f' and acc_order_ms.is_applicable = 't' and wo_acc_line.header_id in (select distinct order_line_id 
						from ch_schedule_details  where header_id = %s
						)						
						)
						as sub_query
						group by acc_line_id,order_line_id,pump_model_id"""%(entry[0]))
				acc_ms_pumpmodel_details = cr.dictfetchall();
				
				if acc_ms_pumpmodel_details:
					
					for acc_ms_pm_item in acc_ms_pumpmodel_details:
						
						### Getting Pump Model Qty ###
						order_line_rec = self.pool.get('ch.work.order.details').browse(cr, uid, acc_ms_pm_item['order_line_id'])
						acc_line_rec = self.pool.get('ch.wo.accessories').browse(cr, uid, acc_ms_pm_item['acc_line_id'])
						acc_qty = int(acc_line_rec.qty)						
						for indent_header in range(acc_qty): 
							### Creation of Department Indent Header ###
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP2')])
							
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry[1]))
							seq_name = cr.fetchone();
							
							dep_indent_obj = self.pool.get('kg.depindent')
							if acc_ms_pm_item['indent_qty'] > 0:
								acc_ms_dep_indent_vals = {
									'name':'',
									'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
									'dep_name':dep_id[0],
									'entry_mode':'auto',
									'state': 'approved',
									'indent_type': 'production',
									'name': seq_name[0],
									'order_id': order_line_rec.header_id.id,
									'order_line_id': order_line_rec.id,
									'src_location_id': location.main_location.id,
									'dest_location_id': location.stock_location.id
									}
									
								indent_id = dep_indent_obj.create(cr, uid, acc_ms_dep_indent_vals)
								
								cr.execute("""
									select type,pump_model_id,ms_item,product_id,uom,order_line_id,order_ms_id,position_id,moc_id,sum(indent_qty) as indent_qty from 

										(
										select raw.qty as indent_qty,raw.product_id,raw.uom,wo_line.pump_model_id,
										wo_acc_line.header_id as order_line_id, raw.id as ms_item, acc_order_ms.id as order_ms_id,
										acc_order_ms.position_id as position_id,acc_order_ms.moc_id as moc_id,'acc'::text as type
										from ch_ms_raw_material as raw
										left join ch_wo_accessories_ms acc_order_ms on raw.header_id = acc_order_ms.ms_id
										left join kg_machine_shop ms_master on ms_master.id = acc_order_ms.ms_id
										left join ch_wo_accessories wo_acc_line on acc_order_ms.header_id = wo_acc_line.id
										left join ch_work_order_details wo_line on wo_acc_line.header_id = wo_line.id
										where ms_master.flag_fabrication = 'f' and acc_order_ms.is_applicable = 't' and wo_acc_line.header_id in (select distinct order_line_id 
										from ch_schedule_details  where header_id = %s
										)										
										)
										as sub_query
										where pump_model_id = %s and order_line_id = %s
										group by type,order_line_id,pump_model_id,ms_item,product_id,uom,order_ms_id,position_id,moc_id """%(entry[0],acc_ms_pm_item['pump_model_id'],order_line_rec.id))
								acc_ms_product_details = cr.dictfetchall();
								
								for acc_ms_indent_item in acc_ms_product_details:
									dep_indent_line_obj = self.pool.get('kg.depindent.line')
									product_rec = self.pool.get('product.product').browse(cr, uid, acc_ms_indent_item['product_id'])
									
									if acc_ms_indent_item['type'] == 'foun':
										ms_raw_obj = self.pool.get('ch.wo.ms.raw')
										ms_raw_rec = ms_raw_obj.browse(cr, uid, acc_ms_indent_item['ms_item'])
										ms_bot_id = ms_raw_rec.header_id.ms_id.id
										fns_item_name = ms_raw_rec.header_id.name
										
										ms_order_obj = self.pool.get('ch.order.machineshop.details')
										ms_order_rec = ms_order_obj.browse(cr, uid, acc_ms_indent_item['order_ms_id'])
										if ms_order_rec.header_id.pump_model_type == 'horizontal':
											length = ms_raw_rec.length
										else:
											length = ms_order_rec.length
											if length == 0:
												length = ms_raw_rec.length
										
									elif acc_ms_indent_item['type'] == 'acc':
										ms_raw_obj = self.pool.get('ch.ms.raw.material')
										ms_raw_rec = ms_raw_obj.browse(cr, uid, acc_ms_indent_item['ms_item'])
										ms_bot_id = ms_raw_rec.header_id.id
										fns_item_name = ms_raw_rec.header_id.code
										ms_acc_obj = self.pool.get('ch.wo.accessories.ms')
										ms_order_rec = ms_acc_obj.browse(cr, uid, acc_ms_indent_item['order_ms_id'])
										length = ms_raw_rec.length
									else:
										indent_qty = acc_ms_indent_item['indent_qty']
										cutting_qty = 0
										
								
									if length > 0:
										
										if ms_raw_rec.uom_conversation_factor == 'one_dimension':	
											if product_rec.uom_id.id == product_rec.uom_po_id.id:
												indent_qty = acc_ms_indent_item['indent_qty']
												cutting_qty = acc_ms_indent_item['indent_qty']
											else:				
												indent_qty =  (length * ms_raw_rec.temp_qty)
												cutting_qty = ms_raw_rec.temp_qty
										if ms_raw_rec.uom_conversation_factor == 'two_dimension':
											indent_qty = (length * ms_raw_rec.breadth * ms_raw_rec.temp_qty)
											cutting_qty = ms_raw_rec.temp_qty
									else:
										if acc_ms_indent_item['indent_qty'] == None:
											indent_qty = 0
										else:
											indent_qty = acc_ms_indent_item['indent_qty']
										cutting_qty = 0
									
									
											
									#~ ### Cutting qty division by qty ###
									if acc_ms_indent_item['type'] == 'foun':
										if order_line_rec.order_category in ('pump','access'):
											cutting_qty = cutting_qty/order_line_rec.qty
											indent_qty = indent_qty/order_line_rec.qty
										else:
											cutting_qty = cutting_qty
											indent_qty = indent_qty
									else:
										cutting_qty = cutting_qty
										indent_qty = indent_qty
										
									
									ms_acc_obj = self.pool.get('ch.wo.accessories.ms')
									ms_order_rec = ms_acc_obj.browse(cr, uid, acc_ms_indent_item['order_ms_id'])
										
									indent_create_qty = ms_order_rec.qty / acc_line_rec.qty 
									
									print"acc_ms_indent_item['product_id']",acc_ms_indent_item['product_id']	
									print"indent_qty",indent_qty	
									print"cutting_qty",cutting_qty	
									print"indent_create_qty",indent_create_qty	
									print"ms_order_recms_order_rec",ms_order_rec.qty	
									
									acc_ms_dep_indent_line_vals = {
										'indent_id':indent_id,
										'product_id':acc_ms_indent_item['product_id'],
										'uom':acc_ms_indent_item['uom'],
										'dep_id':dep_id[0],
										'line_state':'noprocess',
										'line_date':entry[1],
										'qty':indent_qty * indent_create_qty,
										'pending_qty':indent_qty * indent_create_qty,
										'issue_pending_qty':indent_qty * indent_create_qty,
										'cutting_qty': cutting_qty * indent_create_qty,
										'ms_bot_id':ms_bot_id,
										'fns_item_name':fns_item_name,
										'position_id': acc_ms_indent_item['position_id'],
										'moc_id': acc_ms_indent_item['moc_id'],
										'length': length,
										'breadth': ms_raw_rec.breadth,										
										'uom_conversation_factor': ms_raw_rec.uom_conversation_factor,
									}
									
									indent_line_id = dep_indent_line_obj.create(cr, uid, acc_ms_dep_indent_line_vals)
			
				### Fabrication True Accessories Machine Shop Item only
				
				cr.execute("""
				select acc_line_id,pump_model_id,order_line_id,sum(indent_qty) as indent_qty from 
						(
						select raw.qty as indent_qty,raw.product_id,wo_line.pump_model_id,
						wo_acc_line.header_id as order_line_id,wo_acc_line.id as acc_line_id
						from ch_ms_raw_material as raw
						left join ch_wo_accessories_ms acc_order_ms on raw.header_id = acc_order_ms.ms_id
						left join kg_machine_shop ms_master on ms_master.id = acc_order_ms.ms_id
						left join ch_wo_accessories wo_acc_line on acc_order_ms.header_id = wo_acc_line.id
						left join ch_work_order_details wo_line on wo_acc_line.header_id = wo_line.id
						where ms_master.flag_fabrication = 't' and acc_order_ms.is_applicable = 't' and wo_acc_line.header_id in (select distinct order_line_id 
						from ch_schedule_details  where header_id = %s
						)						
						)
						as sub_query
						group by acc_line_id,order_line_id,pump_model_id"""%(entry[0]))
				acc_ms_pumpmodel_details = cr.dictfetchall();
				
				if acc_ms_pumpmodel_details:
					
					for acc_ms_pm_item in acc_ms_pumpmodel_details:
						
						### Getting Pump Model Qty ###
						order_line_rec = self.pool.get('ch.work.order.details').browse(cr, uid, acc_ms_pm_item['order_line_id'])
						acc_line_rec = self.pool.get('ch.wo.accessories').browse(cr, uid, acc_ms_pm_item['acc_line_id'])
						acc_qty = int(acc_line_rec.qty)						
						for indent_header in range(acc_qty): 
							### Creation of Department Indent Header ###
							
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP25')])
							
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry[1]))
							seq_name = cr.fetchone();
							
							dep_indent_obj = self.pool.get('kg.depindent')
							if acc_ms_pm_item['indent_qty'] > 0:
								acc_ms_dep_indent_vals = {
									'name':'',
									'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
									'dep_name':dep_id[0],
									'entry_mode':'auto',
									'state': 'approved',
									'indent_type': 'production',
									'name': seq_name[0],
									'order_id': order_line_rec.header_id.id,
									'order_line_id': order_line_rec.id,
									'src_location_id': location.main_location.id,
									'dest_location_id': location.stock_location.id
									}
									
								indent_id = dep_indent_obj.create(cr, uid, acc_ms_dep_indent_vals)
								
								cr.execute("""
									select type,pump_model_id,ms_item,product_id,uom,order_line_id,order_ms_id,position_id,moc_id,sum(indent_qty) as indent_qty from 

										(
										select raw.qty as indent_qty,raw.product_id,raw.uom,wo_line.pump_model_id,
										wo_acc_line.header_id as order_line_id, raw.id as ms_item, acc_order_ms.id as order_ms_id,
										acc_order_ms.position_id as position_id,acc_order_ms.moc_id as moc_id,'acc'::text as type
										from ch_ms_raw_material as raw
										left join ch_wo_accessories_ms acc_order_ms on raw.header_id = acc_order_ms.ms_id
										left join kg_machine_shop ms_master on ms_master.id = acc_order_ms.ms_id
										left join ch_wo_accessories wo_acc_line on acc_order_ms.header_id = wo_acc_line.id
										left join ch_work_order_details wo_line on wo_acc_line.header_id = wo_line.id
										where ms_master.flag_fabrication = 't' and acc_order_ms.is_applicable = 't' and wo_acc_line.header_id in (select distinct order_line_id 
										from ch_schedule_details  where header_id = %s
										)										
										)
										as sub_query
										where pump_model_id = %s and order_line_id = %s
										group by type,order_line_id,pump_model_id,ms_item,product_id,uom,order_ms_id,position_id,moc_id """%(entry[0],acc_ms_pm_item['pump_model_id'],order_line_rec.id))
								acc_ms_product_details = cr.dictfetchall();
								
								for acc_ms_indent_item in acc_ms_product_details:
									dep_indent_line_obj = self.pool.get('kg.depindent.line')
									product_rec = self.pool.get('product.product').browse(cr, uid, acc_ms_indent_item['product_id'])
									
									if acc_ms_indent_item['type'] == 'foun':
										ms_raw_obj = self.pool.get('ch.wo.ms.raw')
										ms_raw_rec = ms_raw_obj.browse(cr, uid, acc_ms_indent_item['ms_item'])
										ms_bot_id = ms_raw_rec.header_id.ms_id.id
										fns_item_name = ms_raw_rec.header_id.name
										
										ms_order_obj = self.pool.get('ch.order.machineshop.details')
										ms_order_rec = ms_order_obj.browse(cr, uid, acc_ms_indent_item['order_ms_id'])
										if ms_order_rec.header_id.pump_model_type == 'horizontal':
											length = ms_raw_rec.length
										else:
											length = ms_order_rec.length
											if length == 0:
												length = ms_raw_rec.length
										
									elif acc_ms_indent_item['type'] == 'acc':
										ms_raw_obj = self.pool.get('ch.ms.raw.material')
										ms_raw_rec = ms_raw_obj.browse(cr, uid, acc_ms_indent_item['ms_item'])
										ms_bot_id = ms_raw_rec.header_id.id
										fns_item_name = ms_raw_rec.header_id.code
										ms_acc_obj = self.pool.get('ch.wo.accessories.ms')
										ms_order_rec = ms_acc_obj.browse(cr, uid, acc_ms_indent_item['order_ms_id'])
										length = ms_raw_rec.length
									else:
										indent_qty = acc_ms_indent_item['indent_qty']
										cutting_qty = 0
										
									if length > 0:
										
										if ms_raw_rec.uom_conversation_factor == 'one_dimension':	
											if product_rec.uom_id.id == product_rec.uom_po_id.id:
												indent_qty = acc_ms_indent_item['indent_qty']
												cutting_qty = acc_ms_indent_item['indent_qty']
											else:				
												indent_qty =  (length * ms_raw_rec.temp_qty)
												cutting_qty = ms_raw_rec.temp_qty
										if ms_raw_rec.uom_conversation_factor == 'two_dimension':
											indent_qty = (length * ms_raw_rec.breadth * ms_raw_rec.temp_qty)
											cutting_qty = ms_raw_rec.temp_qty
									else:
										if acc_ms_indent_item['indent_qty'] == None:
											indent_qty = 0
										else:
											indent_qty = acc_ms_indent_item['indent_qty']
										cutting_qty = 0
									
									
									
											
									#~ ### Cutting qty division by qty ###
									if acc_ms_indent_item['type'] == 'foun':
										if order_line_rec.order_category in ('pump','access'):
											cutting_qty = cutting_qty/order_line_rec.qty
											indent_qty = indent_qty/order_line_rec.qty
										else:
											cutting_qty = cutting_qty
											indent_qty = indent_qty
									else:
										cutting_qty = cutting_qty
										indent_qty = indent_qty
									
									ms_acc_obj = self.pool.get('ch.wo.accessories.ms')
									ms_order_rec = ms_acc_obj.browse(cr, uid, acc_ms_indent_item['order_ms_id'])
										
									indent_create_qty = ms_order_rec.qty / acc_line_rec.qty 	
									
									acc_ms_dep_indent_line_vals = {
										'indent_id':indent_id,
										'product_id':acc_ms_indent_item['product_id'],
										'uom':acc_ms_indent_item['uom'],
										'dep_id':dep_id[0],
										'line_state':'noprocess',
										'line_date':entry[1],
										'qty':indent_qty * indent_create_qty,
										'pending_qty':indent_qty * indent_create_qty,
										'issue_pending_qty':indent_qty * indent_create_qty,
										'cutting_qty': cutting_qty * indent_create_qty,
										'ms_bot_id':ms_bot_id,
										'fns_item_name':fns_item_name,
										'position_id': acc_ms_indent_item['position_id'],
										'moc_id': acc_ms_indent_item['moc_id'],
										'length': length,
										'breadth': ms_raw_rec.breadth,										
										'uom_conversation_factor': ms_raw_rec.uom_conversation_factor,
									}
									
									indent_line_id = dep_indent_line_obj.create(cr, uid, acc_ms_dep_indent_line_vals)
			
				
				### Fabrication True Accessories Machine Shop Item only, Create for line item
				
				cr.execute("""
					select wo_line.header_id as order_id,wo_line.id as order_line_id, acc_order_ms.id as order_ms_id,acc_order_ms.qty as qty,
					acc_order_ms.ms_id as ms_id,acc_order_ms.moc_id as moc_id
					
					from ch_wo_accessories_ms as acc_order_ms
					left join kg_machine_shop ms_master on ms_master.id = acc_order_ms.ms_id
					left join ch_wo_accessories wo_acc_line on acc_order_ms.header_id = wo_acc_line.id
					left join ch_work_order_details wo_line on wo_acc_line.header_id = wo_line.id
					where ms_master.flag_fabrication = 't' and acc_order_ms.is_applicable = 't' and wo_acc_line.header_id in (select distinct order_line_id 
					from ch_schedule_details  where header_id = %s)"""%(entry[0]))
				
				flag_fabrication_details = cr.dictfetchall();
				
				if flag_fabrication_details:
					
					for flag_fabrication_item in flag_fabrication_details:
						fabrication_obj = self.pool.get('kg.fabrication.process')
							
						fabrication_vals = {
							'order_id':flag_fabrication_item['order_id'],
							'order_line_id':flag_fabrication_item['order_line_id'],
							'acc_ms_line_id':flag_fabrication_item['order_ms_id'],
							'ms_id':flag_fabrication_item['ms_id'],
							'moc_id':flag_fabrication_item['moc_id'],
							'schedule_qty':flag_fabrication_item['qty'],							
							'qty':flag_fabrication_item['qty'],							
							'entry_mode':'auto',
							'state': 'pending',
							
							}
							
						fabrication_id = fabrication_obj.create(cr, uid, fabrication_vals)
				
				
				### BOT Items Only ###
						
				cr.execute("""
					select order_line_id,pump_model_id,sum(indent_qty) as indent_qty from 

						(

						select (raw.qty * order_bot.qty) as indent_qty,raw.product_id,
						order_bot.header_id as order_line_id,wo_line.pump_model_id
						from ch_ms_raw_material as raw
						left join ch_order_bot_details order_bot on raw.header_id = order_bot.bot_id
						left join ch_work_order_details wo_line on order_bot.header_id = wo_line.id
						where order_bot.flag_applicable = 't' and order_bot.header_id in (select distinct order_line_id 
						from ch_schedule_details  where header_id = %s 
						)
						
						)

						as sub_query
						group by order_line_id,pump_model_id
						 """%(entry[0]))
				bot_pumpmodel_details = cr.dictfetchall();
				if bot_pumpmodel_details:
					
					for bot_pm_item in bot_pumpmodel_details:
						
						### Getting Pump Model Qty ###
						order_line_rec = self.pool.get('ch.work.order.details').browse(cr, uid, bot_pm_item['order_line_id'])
						for indent_header in range(order_line_rec.pump_rem_qty): 
				
							### Creation of Department Indent Header ###
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP3')])
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry[1]))
							seq_name = cr.fetchone();
							
							dep_indent_obj = self.pool.get('kg.depindent')
							bot_dep_indent_vals = {
								'name':'',
								'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
								'dep_name':dep_id[0],
								'entry_mode':'auto',
								'state': 'approved',
								'indent_type': 'production',
								'name': seq_name[0],
								'order_id': order_line_rec.header_id.id,
								'order_line_id': order_line_rec.id,
								'src_location_id': location.main_location.id,
								'dest_location_id': location.stock_location.id
								}
						
							indent_id = dep_indent_obj.create(cr, uid, bot_dep_indent_vals)
							
							cr.execute("""
								select type,order_bot_id,order_line_id,pump_model_id,bot_item,product_id,uom,moc_id,sum(indent_qty) as indent_qty from 

									(

									select (raw.qty * order_bot.qty) as indent_qty,raw.product_id,raw.uom,
									order_bot.header_id as order_line_id,wo_line.pump_model_id,order_bot.id as order_bot_id,
									raw.id as bot_item,order_bot.moc_id as moc_id,'foun'::text as type
									from ch_ms_raw_material as raw
									left join ch_order_bot_details order_bot on raw.header_id = order_bot.bot_id
									left join ch_work_order_details wo_line on order_bot.header_id = wo_line.id
									where order_bot.flag_applicable = 't' and order_bot.header_id in (select distinct order_line_id 
									from ch_schedule_details  where header_id = %s
									)

									)

									as sub_query
									where pump_model_id = %s and order_line_id = %s
									group by type,order_bot_id,order_line_id,pump_model_id,bot_item,product_id,uom,moc_id
									 """%(entry[0],bot_pm_item['pump_model_id'],order_line_rec.id))
							bot_product_details = cr.dictfetchall();
							
							for bot_indent_item in bot_product_details:
								dep_indent_line_obj = self.pool.get('kg.depindent.line')
								product_rec = self.pool.get('product.product').browse(cr, uid, bot_indent_item['product_id'])
								
								ms_raw_obj = self.pool.get('ch.ms.raw.material')
								ms_raw_rec = ms_raw_obj.browse(cr, uid, bot_indent_item['bot_item'])

								if bot_indent_item['type'] == 'foun':

									bot_order_obj = self.pool.get('ch.order.bot.details')
									bot_order_rec = bot_order_obj.browse(cr, uid, bot_indent_item['order_bot_id'])
									ms_bot_id = bot_order_rec.bot_id.id
									fns_item_name = bot_order_rec.bot_id.code
									brand_id = bot_order_rec.brand_id.id
								
								if bot_indent_item['type'] == 'acc':

									bot_order_obj = self.pool.get('ch.wo.accessories.bot')
									bot_order_rec = bot_order_obj.browse(cr, uid, bot_indent_item['order_bot_id']) 
									ms_bot_id = bot_order_rec.ms_id.id
									fns_item_name = bot_order_rec.ms_id.code
									brand_id = False
								
								if bot_indent_item['type'] == 'foun':
									indent_qty = bot_indent_item['indent_qty']/order_line_rec.qty
								else:
									indent_qty = bot_indent_item['indent_qty']
								
								### Cutting qty calculation for Two dimensional product ###
								length = 0
								breadth = 0
								cutting_qty = 0
								if ms_raw_rec.uom_conversation_factor == 'two_dimension':
									length = ms_raw_rec.length
									breadth = ms_raw_rec.breadth
									cutting_qty = ms_raw_rec.temp_qty
								
								bot_dep_indent_line_vals = {
									'indent_id':indent_id,
									'product_id':bot_indent_item['product_id'],
									'uom':bot_indent_item['uom'],
									'dep_id':dep_id[0],
									'line_state':'noprocess',
									'line_date':entry[1],
									'qty': indent_qty,
									'pending_qty': indent_qty,
									'issue_pending_qty': indent_qty,
									'ms_bot_id':ms_bot_id,
									'fns_item_name':fns_item_name,
									'brand_id':brand_id,
									'moc_id': bot_indent_item['moc_id'],
									'cutting_qty': cutting_qty,
									'length': length,
									'breadth': ms_raw_rec.breadth,
									'uom_conversation_factor': ms_raw_rec.uom_conversation_factor,
								}
								
								indent_line_id = dep_indent_line_obj.create(cr, uid, bot_dep_indent_line_vals)
				
				
				### Accessories BOT Items ###
						
				cr.execute("""
					select acc_line_id,order_line_id,pump_model_id,sum(indent_qty) as indent_qty from 

						(	

						select (raw.qty * acc_order_bot.qty) as indent_qty,raw.product_id,
						wo_line.id as order_line_id,wo_line.pump_model_id,wo_acc_line.id as acc_line_id
						
						from ch_ms_raw_material as raw
						left join ch_wo_accessories_bot acc_order_bot on raw.header_id = acc_order_bot.ms_id
						left join ch_wo_accessories wo_acc_line on acc_order_bot.header_id = wo_acc_line.id
						left join ch_work_order_details wo_line on wo_acc_line.header_id = wo_line.id
						where acc_order_bot.is_applicable = 't' and wo_acc_line.header_id in (select distinct order_line_id 
						from ch_schedule_details  where header_id = %s
						)

						)

						as sub_query
						group by acc_line_id,order_line_id,pump_model_id
						 """%(entry[0]))
				acc_bot_pumpmodel_details = cr.dictfetchall();
				if acc_bot_pumpmodel_details:
					
					for acc_bot_pm_item in acc_bot_pumpmodel_details:
						
						### Getting Pump Model Qty ###
						order_line_rec = self.pool.get('ch.work.order.details').browse(cr, uid, acc_bot_pm_item['order_line_id'])
						acc_line_rec = self.pool.get('ch.wo.accessories').browse(cr, uid, acc_bot_pm_item['acc_line_id'])
						acc_qty = int(acc_line_rec.qty)	
						for indent_header in range(acc_qty): 
				
							### Creation of Department Indent Header ###
							dep_id = self.pool.get('kg.depmaster').search(cr, uid, [('name','=','DP3')])
							location = self.pool.get('kg.depmaster').browse(cr, uid, dep_id[0], context=context)
							
							seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.depindent')])
							seq_rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
							cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],seq_rec.code,entry[1]))
							seq_name = cr.fetchone();
							
							dep_indent_obj = self.pool.get('kg.depindent')
							acc_bot_dep_indent_vals = {
								'name':'',
								'ind_date':time.strftime('%Y-%m-%d %H:%M:%S'),
								'dep_name':dep_id[0],
								'entry_mode':'auto',
								'state': 'approved',
								'indent_type': 'production',
								'name': seq_name[0],
								'order_id': order_line_rec.header_id.id,
								'order_line_id': order_line_rec.id,
								'src_location_id': location.main_location.id,
								'dest_location_id': location.stock_location.id
								}
						
							indent_id = dep_indent_obj.create(cr, uid, acc_bot_dep_indent_vals)
							
							cr.execute("""
								select type,order_bot_id,order_line_id,pump_model_id,bot_item,product_id,uom,moc_id,sum(indent_qty) as indent_qty from 

									(								

									select (raw.qty * acc_order_bot.qty) as indent_qty,raw.product_id,raw.uom,
									wo_acc_line.header_id as order_line_id,wo_line.pump_model_id,acc_order_bot.id as order_bot_id,
									raw.id as bot_item,acc_order_bot.moc_id as moc_id,'acc'::text as type
									from ch_ms_raw_material as raw
									left join ch_wo_accessories_bot acc_order_bot on raw.header_id = acc_order_bot.ms_id
									left join ch_wo_accessories wo_acc_line on acc_order_bot.header_id = wo_acc_line.id
									left join ch_work_order_details wo_line on wo_acc_line.header_id = wo_line.id
									where acc_order_bot.is_applicable = 't' and wo_acc_line.header_id in (select distinct order_line_id 
									from ch_schedule_details  where header_id = %s
									)

									)

									as sub_query
									where pump_model_id = %s and order_line_id = %s
									group by type,order_bot_id,order_line_id,pump_model_id,bot_item,product_id,uom,moc_id
									 """%(entry[0],acc_bot_pm_item['pump_model_id'],order_line_rec.id))
							acc_bot_product_details = cr.dictfetchall();
							
							for acc_bot_indent_item in acc_bot_product_details:
								dep_indent_line_obj = self.pool.get('kg.depindent.line')
								product_rec = self.pool.get('product.product').browse(cr, uid, acc_bot_indent_item['product_id'])
								
								ms_raw_obj = self.pool.get('ch.ms.raw.material')
								ms_raw_rec = ms_raw_obj.browse(cr, uid, acc_bot_indent_item['bot_item'])

								if acc_bot_indent_item['type'] == 'foun':

									bot_order_obj = self.pool.get('ch.order.bot.details')
									bot_order_rec = bot_order_obj.browse(cr, uid, acc_bot_indent_item['order_bot_id'])
									ms_bot_id = bot_order_rec.bot_id.id
									fns_item_name = bot_order_rec.bot_id.code
									brand_id = bot_order_rec.brand_id.id
								
								if acc_bot_indent_item['type'] == 'acc':

									bot_order_obj = self.pool.get('ch.wo.accessories.bot')
									bot_order_rec = bot_order_obj.browse(cr, uid, acc_bot_indent_item['order_bot_id']) 
									ms_bot_id = bot_order_rec.ms_id.id
									fns_item_name = bot_order_rec.ms_id.code
									brand_id = False
								
								if acc_bot_indent_item['type'] == 'foun':
									indent_qty = acc_bot_indent_item['indent_qty']/order_line_rec.qty
								else:
									indent_qty = acc_bot_indent_item['indent_qty']
								
								### Cutting qty calculation for Two dimensional product ###
								length = 0
								breadth = 0
								cutting_qty = 0
								if ms_raw_rec.uom_conversation_factor == 'two_dimension':
									length = ms_raw_rec.length
									breadth = ms_raw_rec.breadth
									cutting_qty = ms_raw_rec.temp_qty
								
								acc_bot_dep_indent_line_vals = {
									'indent_id':indent_id,
									'product_id':acc_bot_indent_item['product_id'],
									'uom':acc_bot_indent_item['uom'],
									'dep_id':dep_id[0],
									'line_state':'noprocess',
									'line_date':entry[1],
									'qty': indent_qty,
									'pending_qty': indent_qty,
									'issue_pending_qty': indent_qty,
									'ms_bot_id':ms_bot_id,
									'fns_item_name':fns_item_name,
									'brand_id':brand_id,
									'moc_id': acc_bot_indent_item['moc_id'],
									'cutting_qty': cutting_qty,
									'length': length,
									'breadth': ms_raw_rec.breadth,
									'uom_conversation_factor': ms_raw_rec.uom_conversation_factor,
								}
								
								indent_line_id = dep_indent_line_obj.create(cr, uid, acc_bot_dep_indent_line_vals)
				
				self.pool.get('kg.indent.queue').write(cr,uid,entry[2],{'state':'completed','completed_time':time.strftime('%Y-%m-%d %H:%M:%S')})
						
		return True
		
	def duplicate_checking(self,cr,uid,ids=0,context = None):
		cr.execute("""select fn_alert_duplicates()""")
		data = cr.fetchall();		
		if (data[0][0] is None) and (data[0][0] != ''):	
			return False
		if (data[0][0] is not None) and (data[0][0] != ''):	
			maildet = (str(data[0])).rsplit('~');
			cont = data[0][0].partition('.UNWANTED.')		
			email_from = 'iaskgisl@gmail.com'	
			if maildet[2]:	
				email_to = [maildet[1]]
			else:
				email_to = ['']			
			if maildet[3]:
				email_cc = [maildet[2]]
				print"email_cc",email_cc
			else:
				email_cc = ['']								
			ir_mail_server = self.pool.get('ir.mail_server')
			if maildet[4] == 'pass':
				msg = ir_mail_server.build_email(
					email_from = email_from,
					email_to = email_to,
					subject = maildet[3],
					body = cont[0],
					email_cc = email_cc,
					object_id = ids and ('%s-%s' % (ids, 'kg.mail.settings')),
					subtype = 'html',
					subtype_alternative = 'plain')
				res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
			else:
				pass
		return True
	
kg_scheduler()
