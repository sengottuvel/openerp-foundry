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
	
kg_scheduler()
