from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import base64

from PIL import Image

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

CALL_TYPE_SELECTION = [
    ('service','Service'),
    ('new_enquiry','New Enquiry')
]
PURPOSE_SELECTION = [
    ('pump','Pump'),('spare','Spare'),('prj','Project'),('pump_spare','Pump With Spare')
]
STATE_SELECTION = [
    ('draft','Draft'),('moved_to_offer','Moved To Offer'),('call','Call Back'),('quote','Quote Process'),('wo_released','WO Released'),('reject','Rejected')
]
MARKET_SELECTION = [
	('cp','CP'),('ip','IP')
]

class kg_crm_offer(osv.osv):
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		pump_net_amount = spare_net_amount = access_net_amount = offer_net_amount = 0.00
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'pump_net_amount': 0.0,
				'spare_net_amount': 0.0,
				'access_net_amount': 0.0,
				'offer_net_amount': 0.0,
			
			}
			
			cur = order.customer_id.property_product_pricelist_purchase.currency_id
			
			for line in order.line_pump_ids:
				pump_net_amount += line.net_amount
				print"pump_net_amount",pump_net_amount	
				
			for line in order.line_spare_ids:
				spare_net_amount += line.net_amount
				print"spare_net_amount",spare_net_amount	
				
			for line in order.line_accessories_ids:
				access_net_amount += line.net_amount
				print"access_net_amount",access_net_amount	
				
			res[order.id]['pump_net_amount'] = pump_net_amount
			res[order.id]['spare_net_amount'] = spare_net_amount
			res[order.id]['access_net_amount'] = access_net_amount
			res[order.id]['offer_net_amount'] = pump_net_amount + spare_net_amount + access_net_amount
			
		return res
		
	_name = "kg.crm.offer"
	_description = "CRM Offer Entry"
	_order = "enquiry_date desc"

	_columns = {
	
		### Header Details ####
		'name': fields.char('Offer No', size=128,select=True),
		'enquiry_id': fields.many2one('kg.crm.enquiry','Enquiry No.'),
		'schedule_no': fields.char('Schedule No', size=128,select=True),
		'enquiry_date': fields.date('Enquiry Date',required=True),
		'offer_date': fields.date('Offer Date',required=True),
		'note': fields.char('Notes'),
		'service_det': fields.char('Service Details'),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'active': fields.boolean('Active'),
		'state': fields.selection(STATE_SELECTION,'Status', readonly=True),
		'offer_copy': fields.char('Offer Copy'),
		
		'line_pump_ids': fields.one2many('ch.pump.offer', 'header_id', "Pump Offer"),
		'line_spare_ids': fields.one2many('ch.spare.offer', 'header_id', "Spare Offer"),
		'line_accessories_ids': fields.one2many('ch.accessories.offer', 'header_id', "Accessories Offer"),
		
		#~ 'ch_line_ids': fields.one2many('ch.kg.crm.pumpmodel', 'header_id', "Pump/Spare Details"),
		'due_date': fields.date('Due Date',required=True),
		'call_type': fields.selection(CALL_TYPE_SELECTION,'Call Type', required=True),
		'ref_mode': fields.selection([('direct','Direct'),('dealer','Dealer')],'Reference Mode', required=True),
		'market_division': fields.selection(MARKET_SELECTION,'Marketing Division', required=True),
		'ref_no': fields.char('Reference Number'),
		'segment': fields.selection([('dom','Domestic'),('exp','Export')],'Segment', required=True),
		'customer_id': fields.many2one('res.partner','Customer Name',domain=[('customer','=',True),('contact','=',False)]),
		'dealer_id': fields.many2one('res.partner','Dealer Name',domain=[('dealer','=',True),('contact','=',False)]),
		'industry_id': fields.many2one('kg.industry.master','Sector'),
		'expected_value': fields.float('Expected Value'),
		'del_date': fields.date('Expected Del Date'),
		'purpose': fields.selection(PURPOSE_SELECTION,'Purpose'),
		'chemical_id': fields.many2one('kg.chemical.master','Chemical',domain=[('purpose','=','general')]),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Name'),
		's_no': fields.char('Serial Number'),
		'wo_no': fields.char('WO Number'),
		'requirements': fields.text('Requirements'),
		
		'enquiry_no': fields.char('Enquiry No.', size=128,select=True),
		'scope_of_supply': fields.selection([('bare_pump','Bare Pump'),('pump_with_acces','Pump With Accessories'),('pump_with_acces_motor','Pump With Accessories And Motor')],'Scope of Supply'),
		'pump': fields.selection([('gld_packing','Gland Packing'),('mc_seal','M/C Seal'),('dynamic_seal','Dynamic seal')],'Shaft Sealing', required=True),
		'drive': fields.selection([('motor','Motor'),('vfd','VFD'),('engine','Engine')],'Drive'),
		'transmision': fields.selection([('cpl','Coupling'),('belt','Belt Drive'),('fc','Fluid Coupling'),('gear_box','Gear Box'),('fc_gear_box','Fluid Coupling With Gear Box')],'Transmision', required=True),
		'acces': fields.selection([('yes','Yes'),('no','No')],'Accessories'),
		
		# Pump Offer Fields
		'pump_tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Price',multi="sums",store=True),	
		'pump_sam_ratio': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Sam Ratio',multi="sums",store=True),	
		'pump_dealer_discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),	
		'pump_customer_discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),	
		'pump_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax',multi="sums",store=True),	
		'pump_p_f': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F',multi="sums",store=True),	
		'pump_freight': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),	
		'pump_insurance': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),	
		'pump_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),	
		
		# Spare Offer Fields
		'spare_tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Price',multi="sums",store=True),	
		'spare_sam_ratio': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Sam Ratio',multi="sums",store=True),	
		'spare_dealer_discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),	
		'spare_customer_discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),	
		'spare_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax',multi="sums",store=True),	
		'spare_p_f': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F',multi="sums",store=True),	
		'spare_freight': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),	
		'spare_insurance': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),	
		'spare_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),	
		
		# Accessories Offer Fields
		'access_tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Price',multi="sums",store=True),	
		'access_sam_ratio': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Sam Ratio',multi="sums",store=True),	
		'access_dealer_discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),	
		'access_customer_discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),	
		'access_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax',multi="sums",store=True),	
		'access_p_f': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F',multi="sums",store=True),	
		'access_freight': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),	
		'access_insurance': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),	
		'access_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),	
		
		'offer_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Offer Amount',multi="sums",store=True),
		
		### Entry Info ####
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),	   
		
		# Offer Copy 
		
		'rep_data':fields.binary("Offer Copy",readonly=True),
		
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_crm_offer', context=c),
		'enquiry_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'offer_date' : lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',
		'pump': 'gld_packing',
		'transmision': 'cpl',
		'ref_mode': 'direct',
		'call_type': 'new_enquiry',
		'active': True,
	#	'division_id':_get_default_division,
		'due_date' : lambda * a: time.strftime('%Y-%m-%d'),
		
	}
	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []	 
		for rec in self.browse(cr,uid,ids): 
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_crm_offer, self).write(cr, uid, ids, vals, context)
	
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		
		#~ for line in entry.line_pump_ids:
		
		off_no = ''	
		seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.crm.offer')])
		rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
		cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],rec.code,entry.offer_date))
		off_no = cr.fetchone();
		self.write(cr, uid, ids, {
									'name':off_no[0],
									'state': 'moved_to_offer',
									'confirm_user_id': uid, 
									'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')
								})
		return True
		
	def offer_copy(self,cr,uid,ids,context=None):
		import StringIO
		import base64
		
		try:
			import xlwt
		except:
		   raise osv.except_osv('Warning !','Please download python xlwt module from\nhttp://pypi.python.org/packages/source/x/xlwt/xlwt-0.7.2.tar.gz\nand install it')
		   
		rec =self.browse(cr,uid,ids[0])
		print"recrec",rec
		
		#######
		line_sql = """
			(select pump.pump_id
			from ch_pump_offer pump
			left join kg_pumpmodel_master pmm on(pmm.id=pump.pump_id)
			where header_id = """+ str(rec.id) +""" order by pump.pump_id)
			union 
			(select pump.pump_id
			from ch_spare_offer pump
			left join kg_pumpmodel_master pmm on(pmm.id=pump.pump_id)
			where header_id = """+ str(rec.id) +""" order by pump.pump_id)
			union 
			(select pump.pump_id
			from ch_accessories_offer pump
			left join kg_pumpmodel_master pmm on(pmm.id=pump.pump_id)
			where header_id = """+ str(rec.id) +""" order by pump.pump_id)

			"""
		cr.execute(line_sql)		
		line_data = cr.dictfetchall()
		print"line_dataline_data",line_data
		enq_line_data = []
		enq_line_data = line_data
		for item in line_data:
			pump_off_obj = self.pool.get('ch.pump.offer').search(cr,uid,[('header_id','=',rec.id),('pump_id','=',item['pump_id'])])
			
			if pump_off_obj:
				off_pump_line_rec = self.pool.get('ch.pump.offer').browse(cr,uid,pump_off_obj[0])
				pump_enq_line_id = off_pump_line_rec.enquiry_line_id.id
				item['enquiry_line_id'] = pump_enq_line_id
				item['name'] = off_pump_line_rec.pump_id.name
				item['id'] = off_pump_line_rec.id
				print"item['enquiry_line_id']",item['enquiry_line_id']
			spare_off_obj = self.pool.get('ch.spare.offer').search(cr,uid,[('header_id','=',rec.id),('pump_id','=',item['pump_id'])])
			if spare_off_obj:
				spare_pump_line_rec = self.pool.get('ch.spare.offer').browse(cr,uid,spare_off_obj[0])
				spr_enq_line_id = spare_pump_line_rec.enquiry_line_id.id
				item['enquiry_line_id'] = spr_enq_line_id
				print"item['enquiry_line_id']",item['enquiry_line_id']
				item['name'] = spare_pump_line_rec.pump_id.name
				item['id'] = spare_pump_line_rec.id
			access_off_obj = self.pool.get('ch.accessories.offer').search(cr,uid,[('header_id','=',rec.id),('pump_id','=',item['pump_id'])])
			if access_off_obj:
				access_pump_line_rec = self.pool.get('ch.accessories.offer').browse(cr,uid,access_off_obj[0])
				acc_enq_line_id = access_pump_line_rec.enquiry_line_id.id
				item['enquiry_line_id'] = acc_enq_line_id
				print"item['enquiry_line_id']",item['enquiry_line_id']
				item['name'] = access_pump_line_rec.pump_id.name
				item['id'] = access_pump_line_rec.id
		
		print"line_data",line_data
		
		print"line_dataline_data",len(line_data)
		
		len_col = 0
		if line_data:
			if len(line_data):
				if len(line_data) <= 1:
					len_col = len(line_data) 
				elif len(line_data) <= 3 or len(line_data) > 3:
					len_col = len(line_data)
		print"len_collen_collen_col",len_col
		
		line_data.sort(key=lambda line_data: line_data['pump_id'])
		record={}
		sno=0
		wbk = xlwt.Workbook()
		style1 = xlwt.easyxf('font: bold on,height 240,color_index red;' 'align: horiz center;''borders: left thin, right thin, top thin, bottom thin') 
		style2 = xlwt.easyxf('font: bold on,height 240,color_index black;' 'align: horiz center;''borders: left thin, right thin, top thin, bottom thin') 
		style3 = xlwt.easyxf('font: height 200,color_index black;' 'align: horiz center;''borders: left thin, right thin, top thin, bottom thin') 
		style4 = xlwt.easyxf('font: height 200,color_index black;' 'align: horiz left;''borders: left thin, right thin, top thin, bottom thin') 
		style5 = xlwt.easyxf('font: bold on,height 200,color_index black;' 'align: horiz left;''borders: left thin, right thin, top thin, bottom thin;''font: underline on;') 
		style6 = xlwt.easyxf('font: height 200,color_index black;' 'align: vert centre, horiz center;''borders: left thin, right thin, top thin, bottom thin') 
		style7 = xlwt.easyxf('font: height 200,color_index black;' 'align: wrap on, vert centre, horiz left;''borders: left thin, right thin, top thin, bottom thin') 
		
		
		img = Image.open('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_crm_offer/img/sam.png')
		r, g, b, a = img.split()
		img = Image.merge("RGB", (r, g, b))
		img.save('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_crm_offer/img/sam.bmp')
		img = Image.open('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_crm_offer/img/TUV_NORD.png')
		img.save('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_crm_offer/img/TUV_NORD.bmp')
		
		#~ r, g, b, a = img.split()
		#~ img = Image.merge("RGB", (r, g, b))
		s1=8
		
		"""adding a worksheet along with name"""
		
		sheet1 = wbk.add_sheet('Offer Copy')
		
		s2=9
		if line_data:
			if len_col <= 1:
				sheet1.col(0).width = 8000
				sheet1.col(1).width = 12000
			elif len_col <= 2:
				sheet1.col(0).width = 8000
				sheet1.col(1).width = 7000
				sheet1.col(2).width = 7000
			elif len_col >= 3:
				sheet1.col(0).width = 8000
				sheet1.col(1).width = 7000
				sheet1.col(2).width = 7000
				sheet1.col(3).width = 7000
		else:
			sheet1.col(0).width = 8000
			sheet1.col(1).width = 5000
			sheet1.col(2).width = 5000
		sheet1.col(len_col+1).width = 5000
		sheet1.col(len_col+2).width = 5000
		sheet1.col(len_col+3).width = 5000
		sheet1.col(len_col+4).width = 5000
		sheet1.col(len_col+5).width = 5000
		sheet1.col(len_col+6).width = 5000
		sheet1.col(len_col+7).width = 5000
		
		sheet1.write_merge(0, 0, 0, len_col,"SAM TURBO INDUSTRY PRIVATE LIMITED",style2)
		sheet1.row(0).height = 450
		sheet1.write_merge(1, 1, 0, len_col,"Avinashi Road, Neelambur, Coimbatore - 641062",style3)
		sheet1.write_merge(2, 2, 0, len_col,"Tel:3053555, 3053556,Fax : 0422-3053535",style3)
		sheet1.write_merge(3, 3, 0, len_col,"TECHNICAL CUM PRICED OFFER",style2)
		sheet1.row(3).height = 300
		to = "To : " + str(rec.customer_id.name)
		sheet1.write_merge(4, 4, 0, 0, to, style4)
		enq_ref = "Enquiry Ref : " + str(rec.enquiry_no)
		sheet1.write_merge(4, 4, 1, len_col, enq_ref, style4)
		sheet1.row(4).height = 450
		off_ref_no = "Offer Ref : " + str(rec.name)
		sheet1.write_merge(5, 5, 0, 0, off_ref_no or "-", style4)
		offer_date = rec.offer_date
		offer_date = datetime.strptime(offer_date, '%Y-%m-%d').strftime('%d/%m/%Y')
		date = "Date : " + offer_date
		sheet1.write_merge(5, 5, 1, len_col, date, style4)
		sheet1.row(5).height = 400
		sheet1.write_merge(6, 6, 0, len_col, 'Item Details:', style5)
		sheet1.row(6).height = 400
		sheet1.write_merge(7, 7, 0, 0, 'Application', style4)
		sheet1.write_merge(7, 7, 1, len_col, 'List Of Horizontal Centrifugal pump for Heavy Water Upgradation Plant', style6)
		sheet1.write_merge(13, 13, 0, len_col, 'Liquid details given by the customer:', style5)
		sheet1.row(13).height = 400
		sheet1.write_merge(25, 25, 0, len_col, 'Pump Specification:', style5)
		sheet1.row(25).height = 400
		sheet1.write_merge(46, 46, 0, len_col, 'Material of construction:', style5)
		sheet1.row(46).height = 400
		########
		
		col_1 = ''
		col_no = 1
		logo_size = 0
		for item in line_data:
			""" writing field headings """
			col_1 = item['name']
			#~ sheet1.insert_bitmap('/OPENERP/Sam_Turbo/sam_turbo_dev/openerp-server/openerp/addons/kg_crm_offer/img/sam.bmp',0,0)
			#~ sheet1.insert_bitmap('/OPENERP/Sam_Turbo/sam_turbo_dev/openerp-server/openerp/addons/kg_crm_offer/img/TUV_NORD.bmp',0,len_col,120)
			if len_col == 1:
				logo_size = 250
			elif len_col <= 3:
				logo_size = 120
			elif len_col >= 4:
				logo_size = 100
			sheet1.insert_bitmap('/OpenERP/Sam_Turbo/openerp-foundryopenerp-server/openerp/addons/kg_crm_offer/img/sam.bmp',0,0)
			sheet1.insert_bitmap('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_crm_offer/img/TUV_NORD.bmp',0,len_col,logo_size)
			print"col_1",col_1
			sheet1.write(s1,col_no,str(col_1),style1)
			col_no = col_no + 1

		"""writing data according to query and filteration in worksheet"""
		
		sheet1.write(s2,0,"Sr.No",style6)
		sheet1.write(s2+1,0,"Tag No",style6)
		sheet1.write(s2+2,0,"Description",style6)
		sheet1.write(s2+3,0,"Quantity in nos",style6)
		sheet1.write(s2+5,0,"Liquid Handled",style6)
		sheet1.write(s2+6,0,"Temperature in C",style6)
		sheet1.write(s2+7,0,"Specific Gravity",style6)
		sheet1.write(s2+8,0,"Capacity in LPM",style6)
		sheet1.write(s2+9,0,"Capacity in M 3 / hr",style6)
		sheet1.write(s2+10,0,"Head in M",style6)
		sheet1.write(s2+11,0,"Shut off Head(Rated Impeller)-M",style6)
		sheet1.write(s2+12,0,"% of Shut off head",style6)
		sheet1.write(s2+13,0,"Min. Continuous Flow in M3/hr.",style6)
		sheet1.write(s2+14,0,"Design pressure in Kg/cm2",style6)
		sheet1.write(s2+15,0,"Hydro Test Pressure in kg/cm2",style6)
		sheet1.write(s2+17,0,"Pump Type",style6)
		sheet1.row(s2+17).height = 490
		sheet1.write(s2+18,0,"Pump Model",style6)
		sheet1.write(s2+19,0,"Size in mm",style6)
		sheet1.write(s2+20,0,"Flange Standard",style6)
		sheet1.write(s2+21,0,"Efficiency in % ",style6)
		sheet1.write(s2+22,0,"BKW",style6)
		sheet1.write(s2+23,0,"End of curve power-KW Rated.Imp",style6)
		sheet1.write(s2+24,0,"Motor KW ",style6)
		sheet1.write(s2+25,0,"Pump Speed in RPM",style6)
		sheet1.write(s2+26,0,"Type of Drive",style6)
		sheet1.write(s2+27,0,"NPSH R - M",style6)
		sheet1.write(s2+28,0,"Impeller Type",style6)
		sheet1.write(s2+29,0,"Max.Allowable Solid Size In mm",style6)
		sheet1.write(s2+30,0,"Type of Bearing(DE+NDE)",style6)
		sheet1.write(s2+31,0,"Max Noise Level",style6)
		sheet1.write(s2+32,0,"Vibration Limit",style6)
		sheet1.write(s2+33,0,"Weight of Pump + Acc",style6)
		sheet1.write(s2+34,0,"Weight of Motor",style6)
		sheet1.write(s2+35,0,"Reducer required at",style6)
		sheet1.write(s2+36,0,"Balancing device",style6)
		
		if line_data:
			coln_no = 1
			s_no = 1
			for item in line_data:
				item_sql = """
					select 
					enq_line.equipment_no as equipment_no,
					enq_line.description as description,
					enq_line.qty as qty,
					liquid.name as liquid_name,
					enq_line.temperature_in_c as temperature_in_c,
					enq_line.specific_gravity as specific_gravity,
					enq_line.capacity_in_liquid as capacity_in_liquid,
					enq_line.head_in_liquid as head_in_liquid,
					enq_line.shut_off_head as shut_off_head,
					enq_line.minimum_contionuous as minimum_contionuous,
					enq_line.hydrostatic_test_pressure as hydrostatic_test_pressure,
					psf.name as flange_standard,
					enq_line.efficiency_in as efficiency_in,
					enq_line.motor_kw as motor_kw,
					enq_line.speed_in_pump as speed_in_pump,
					enq_line.type_of_drive as type_of_drive,
					enq_line.npsh_r_m as npsh_r_m,
					enq_line.impeller_type as impeller_type,
					enq_line.maximum_allowable_soild as maximum_allowable_soild,
					enq_line.bearing_number_nde as bearing_number_nde
					
					from ch_kg_crm_pumpmodel enq_line
					
					left join kg_fluid_master liquid on(liquid.id=enq_line.fluid_id)
					left join ch_pumpseries_flange psf on(psf.id=enq_line.flange_standard)
					where enq_line.id = """+ str(item['enquiry_line_id']) +""" and enq_line.pump_id = """+ str(item['pump_id']) + """ order by enq_line.pump_id
					"""
				cr.execute(item_sql)		
				item_data = cr.dictfetchall()
				print"item_dataitem_data",item_data
				if item_data:
					for ele in item_data:
						sheet1.write(s2,coln_no,s_no,style6)
						sheet1.write(s2+1,coln_no,ele['equipment_no'] or "-",style6)
						sheet1.write(s2+2,coln_no,ele['description'] or "-",style6)
						sheet1.write(s2+3,coln_no,ele['qty'] or "-",style6)
						sheet1.write(s2+5,coln_no,ele['liquid_name'] or "-",style6)
						sheet1.write(s2+6,coln_no,ele['temperature_in_c'] or "-",style6)
						sheet1.write(s2+7,coln_no,ele['specific_gravity'] or "-",style6)
						sheet1.write(s2+8,coln_no,ele['specific_gravity'] or "-",style6)
						sheet1.write(s2+9,coln_no,ele['capacity_in_liquid'] or "-",style6)
						sheet1.write(s2+10,coln_no,ele['head_in_liquid'] or "-",style6)
						sheet1.write(s2+11,coln_no,ele['shut_off_head'] or "-",style6)
						sheet1.write(s2+12,coln_no,ele['shut_off_head'] or "-",style6)
						sheet1.write(s2+13,coln_no,ele['minimum_contionuous'] or "-",style6)
						sheet1.write(s2+14,coln_no,ele['hydrostatic_test_pressure'] or "-",style6)
						sheet1.write(s2+15,coln_no,ele['hydrostatic_test_pressure'] or "-",style6)
						sheet1.write(s2+17,coln_no,"Horizontal Centrifual Front pull out Design Pump" or "-",style7)
						sheet1.row(s2+17).height = 490
						sheet1.write(s2+18,coln_no,item['name'] or "-",style1)
						sheet1.write(s2+19,coln_no,item['name'] or "-",style6)	
						sheet1.write(s2+20,coln_no,ele['flange_standard'] or "-",style6)
						sheet1.write(s2+21,coln_no,ele['efficiency_in'] or "-",style6)
						sheet1.write(s2+22,coln_no,ele['efficiency_in'] or "-",style6)
						sheet1.write(s2+23,coln_no,ele['efficiency_in'] or "-",style6)
						sheet1.write(s2+24,coln_no,ele['motor_kw'] or "-",style6)
						sheet1.write(s2+25,coln_no,ele['speed_in_pump'] or "-",style6)
						sheet1.write(s2+26,coln_no,ele['type_of_drive'] or "-",style6)
						sheet1.write(s2+27,coln_no,ele['npsh_r_m'] or "-",style6)
						sheet1.write(s2+28,coln_no,ele['impeller_type'] or "-",style6)
						sheet1.write(s2+29,coln_no,ele['maximum_allowable_soild'] or "-",style6)
						sheet1.write(s2+30,coln_no,ele['bearing_number_nde'] or "-",style6)
						sheet1.write(s2+31,coln_no,ele['bearing_number_nde'] or "-",style6)
						sheet1.write(s2+32,coln_no,ele['bearing_number_nde'] or "-",style6)
						sheet1.write(s2+33,coln_no,ele['bearing_number_nde'] or "-",style6)
						sheet1.write(s2+34,coln_no,ele['bearing_number_nde'] or "-",style6)
						sheet1.write(s2+35,coln_no,ele['bearing_number_nde'] or "-",style6)
						sheet1.write(s2+36,coln_no,ele['bearing_number_nde'] or "-",style6)
						
						s_no = s_no + 1
					coln_no = coln_no + 1
				else:
					sheet1.write(s2+1,coln_no,"-",style6)
					sheet1.write(s2+2,coln_no,"-",style6)
					sheet1.write(s2+3,coln_no,"-",style6)
					sheet1.write(s2+5,coln_no,"-",style6)
					sheet1.write(s2+6,coln_no,"-",style6)
					sheet1.write(s2+7,coln_no,"-",style6)
					sheet1.write(s2+8,coln_no,"-",style6)
					sheet1.write(s2+9,coln_no,"-",style6)
					sheet1.write(s2+10,coln_no,"-",style6)
					sheet1.write(s2+11,coln_no,"-",style6)
					sheet1.write(s2+12,coln_no,"-",style6)
					sheet1.write(s2+13,coln_no,"-",style6)
					sheet1.write(s2+14,coln_no,"-",style6)
					sheet1.write(s2+15,coln_no,"-",style6)
					sheet1.write(s2+17,coln_no,"-",style6)
					sheet1.row(s2+17).height = 490
					sheet1.write(s2+18,coln_no,"-",style1)
					sheet1.write(s2+19,coln_no,"-",style6)	
					sheet1.write(s2+20,coln_no,"-",style6)
					sheet1.write(s2+21,coln_no,"-",style6)
					sheet1.write(s2+22,coln_no,"-",style6)
					sheet1.write(s2+23,coln_no,"-",style6)
					sheet1.write(s2+24,coln_no,"-",style6)
					sheet1.write(s2+25,coln_no,"-",style6)
					sheet1.write(s2+26,coln_no,"-",style6)
					sheet1.write(s2+27,coln_no,"-",style6)
					sheet1.write(s2+28,coln_no,"-",style6)
					sheet1.write(s2+29,coln_no,"-",style6)
					sheet1.write(s2+30,coln_no,"-",style6)
					sheet1.write(s2+31,coln_no,"-",style6)
					sheet1.write(s2+32,coln_no,"-",style6)
					sheet1.write(s2+33,coln_no,"-",style6)
					sheet1.write(s2+34,coln_no,"-",style6)
					sheet1.write(s2+35,coln_no,"-",style6)
					sheet1.write(s2+36,coln_no,"-",style6)
					coln_no = coln_no + 1
					
		if line_data:
			em_col = 1
			for item in line_data:
				mat_sql = """
							select 
							omat.name as mat_name,
							moc.name as moc

							from ch_kg_crm_pumpmodel enq_line
							
							join ch_moc_construction mocc on(mocc.header_id=enq_line.id)
							left join kg_offer_materials omat on(omat.id=mocc.offer_id)
							left join kg_moc_master moc on(moc.id=mocc.moc_id)
							where enq_line.id = """+ str(item['enquiry_line_id']) +""" and enq_line.pump_id = """+ str(item['pump_id']) + """ order by enq_line.pump_id
							"""
				cr.execute(mat_sql)		
				mat_data = cr.dictfetchall()
				print"mat_data",mat_data
				row_no = s2+38
				
				if mat_data:
					for item_1 in mat_data:
						if item_1['mat_name'] or item_1['moc']:
							m_col_no = 0
							sheet1.write(row_no,m_col_no,item_1['mat_name'])
							sheet1.write(row_no,em_col,item_1['moc'] or "-",style6)
							row_no = row_no+1
				else:
					m_col_no = 0
					sheet1.write(row_no,em_col,"-",style6)
					row_no = row_no+1
				em_col = em_col + 1 
		print"row_norow_norow_norow_no",row_no
		
		sheet1.write_merge(row_no, row_no, 0, len_col, 'Mechanical Seal Details : Eagle Burgmann / Flow Serve / Leak Proof:', style5)
		sheet1.row(row_no).height = 400
		row_no = row_no + 1
		
		sheet1.write_merge(row_no, row_no, 0, 0, 'Seal Type / Face Combination', style4)
		print"row_norow_norow_nosssssssssS",row_no
		print"row_norow_norow_nolen_collen_collen_col",len_col
		sheet1.write_merge(row_no+1, row_no+1, 0, 0, 'Gland Plate / API Plan', style4)
		if line_data:
			em_col = 1
			for item in line_data:
				mech_sql = """
							select 
							enq_line.shaft_sealing as shaft_sealing,
							enq_line.shaft_sealing as gland
							
							from ch_kg_crm_pumpmodel enq_line
							
							where enq_line.id = """+ str(item['enquiry_line_id']) +""" and enq_line.pump_id = """+ str(item['pump_id']) + """
							"""
				cr.execute(mech_sql)		
				mech_data = cr.dictfetchall()
				print"mech_data",mech_data
				if mech_data:
					s = 1
					for item_1 in mech_data:
						if item_1['shaft_sealing'] or item_1['gland']:
							m_col_no = 1
							sheet1.write(row_no,em_col,item_1['shaft_sealing'],style6)
							sheet1.write(row_no+1,em_col,item_1['gland'],style6)
							m_col_no = m_col_no+1
						else:
							m_col_no = 1
							sheet1.write(row_no,em_col,"-",style6)
							sheet1.write(row_no+1,em_col,"-",style6)
							m_col_no = m_col_no+1
						s = s + 1
						em_col = em_col + 1
						print"sssssssssssss",s
				else:
					sheet1.write(row_no,em_col,"-",style6)
					sheet1.write(row_no+1,em_col,"-",style6)
					em_col = em_col + 1
					
			print"row_norow_nodddddD",row_no
			row_no = row_no + s
		
		sheet1.write_merge(row_no, row_no, 0, len_col, 'Motor Make Details:', style5)
		sheet1.row(row_no).height = 400
		row_no = row_no + 1
		
		sheet1.write_merge(row_no, row_no, 0, 0, 'Type / Mounting', style4)
		sheet1.write_merge(row_no+1, row_no+1, 0, 0, 'Insulation / protection', style4)
		sheet1.write_merge(row_no+2, row_no+2, 0, 0, 'Voltage / Phase / Frequency', style4)
		if line_data:
			em_col = 1
			for item in line_data:
				mm_sql = """
							select 
							enq_line.shaft_sealing as shaft_sealing,
							enq_line.qty as qty,
							enq_line.qty as qty
							
							from ch_kg_crm_pumpmodel enq_line
							
							where enq_line.id = """+ str(item['enquiry_line_id']) +""" and enq_line.pump_id = """+ str(item['pump_id']) + """ """
				cr.execute(mm_sql)		
				mm_data = cr.dictfetchall()
				print"mm_data",mm_data
				s = 1
				if mm_data:
					for item_1 in mm_data:
						if item_1['shaft_sealing'] or item_1['qty']:
							sheet1.write(row_no,em_col,item_1['shaft_sealing'] or "-",style6)
							sheet1.write(row_no+1,em_col,item_1['qty'] or "-",style6)
							sheet1.write(row_no+2,em_col,item_1['qty'] or "-",style6)
						else:
							sheet1.write(row_no,em_col,"-",style6)
							sheet1.write(row_no+1,em_col,"-",style6)
							sheet1.write(row_no+2,em_col,"-",style6)
						s = s + 2
						em_col = em_col + 1
				else:
					sheet1.write(row_no,em_col,"-",style6)
					sheet1.write(row_no+1,em_col,"-",style6)
					sheet1.write(row_no+2,em_col,"-",style6)
					em_col = em_col + 1
		row_no = row_no + s
		
		sheet1.write_merge(row_no, row_no, 0, len_col, 'Scope Of Supply / Price per Each in Rs.', style5)
		sheet1.row(row_no).height = 400
		row_no = row_no + 1
		
		sheet1.write_merge(row_no, row_no, 0, 0, 'Bare Pump', style4)
		
		if line_data:
			em_col = 1
			for item in line_data:
				ss_sql = """
							select 
							pump_offer.net_amount as net_amount
							
							from ch_pump_offer pump_offer
							
							where pump_offer.header_id = """+ str(rec.id) +""" and pump_offer.pump_id = """+ str(item['pump_id']) + """ """
				cr.execute(ss_sql)		
				ss_data = cr.dictfetchall()
				print"ss_data",ss_data
				if ss_data:
					for item_1 in ss_data:
						if item_1['net_amount']:
							sheet1.write(row_no,em_col,item_1['net_amount'] or "-",style6)
						else:
							sheet1.write(row_no,em_col,"-",style6)
						em_col = em_col + 1
				else:
					sheet1.write(row_no,em_col,"-",style6)
					em_col = em_col + 1
		row_no = row_no
		print"eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",row_no
		sheet1.write_merge(row_no+1, row_no+1, 0, len_col, 'Accessories', style5)
		sheet1.row(row_no+1).height = 400
		row_no = row_no + 1
		
		if line_data:
			em_col = 1
			for item in line_data:
				access_sql = """
							select 
							acc.name as access_name,
							access_offer.net_amount as net_amount
							
							from ch_accessories_offer access_offer
							left join kg_accessories_master acc on(acc.id=access_offer.access_id)
							where access_offer.header_id = """+ str(rec.id) +""" and access_offer.pump_id = """+ str(item['pump_id']) + """ order by access_offer.pump_id """
				cr.execute(access_sql)		
				access_data = cr.dictfetchall()
				print"access_data",access_data
				if access_data:
					for item_1 in access_data:
						if item_1['net_amount'] or item_1['access_name']:
							sheet1.write(row_no+1,0,item_1['access_name'],style6)
							sheet1.write(row_no+1,em_col,item_1['net_amount'] or "-",style6)
							row_no = row_no+1
					em_col = em_col + 1
				else:
					sheet1.write(row_no+1,em_col,"-",style6)
					em_col = em_col + 1
		row_no = row_no
		
		sheet1.write_merge(row_no+2, row_no+2, 0, len_col, 'Spares:', style5)
		sheet1.row(row_no+1).height = 400
		row_no = row_no + 1
		
		if line_data:
			em_col = 1
			for item in line_data:
				spare_sql = """
							select 
							spare_offer.item_name as spare_name,
							pmm.name as pump_name,
							spare_offer.net_amount as net_amount
							
							from ch_spare_offer spare_offer
							left join kg_pumpmodel_master pmm on(pmm.id=spare_offer.pump_id)
							where spare_offer.header_id = """+ str(rec.id) +""" and spare_offer.pump_id = """+ str(item['pump_id']) + """ order by spare_offer.pump_id """
				cr.execute(spare_sql)		
				spare_data = cr.dictfetchall()
				print"spare_data",spare_data
				if spare_data:
					for item_1 in spare_data:
						if item_1['spare_name'] or item_1['net_amount']:
							m_col_no = 1
							sheet1.write(row_no+2,0,item_1['spare_name'],style6)
							sheet1.write(row_no+2,em_col,item_1['net_amount'] or "-",style6)
							row_no = row_no+1
				else:
					sheet1.write(row_no+2,em_col,"-",style6)
					em_col = em_col + 1
		row_no = row_no
		print"row_norow_norow_norow_norow_norow_no",row_no
				
		"""Parsing data as string """
		file_data=StringIO.StringIO()
		
		sheet1.set_protect(True)
		sheet1.set_password('secret')
		
		o=wbk.save(file_data)		
		"""string encode of data in wksheet"""		
		out=base64.encodestring(file_data.getvalue())
		"""returning the output xls as binary"""
		report_name = 'Offer Copy' + '.' + 'xls'
		
		return self.write(cr, uid, ids, {'rep_data':out,'offer_copy':report_name},context=context)
		
		
kg_crm_offer()


class ch_pump_offer(osv.osv):
	

	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		sam_ratio_tot = dealer_discount_tot = customer_discount_tot = spl_discount_tot = tax_tot = p_f_tot = freight_tot = insurance_tot = pump_price_tot = tot_price = net_amount = 0
		i_tot = k_tot = m_tot = p_tot = r_tot = 0
		for line in self.browse(cr, uid, ids, context=context):
			print"linelineline",line
			res[line.id] = {
				
				'sam_ratio_tot': 0.0,
				'dealer_discount_tot': 0.0,
				'customer_discount_tot' : 0.0,
				'spl_discount_tot' : 0.0,
				'tax_tot': 0.0,
				'p_f_tot': 0.0,
				'freight_tot': 0.0,
				'insurance_tot': 0.0,
				'pump_price': 0.0,
				'tot_price': 0.0,
				
			}
			print"line.prime_cost",line.prime_cost
			print"line.sam_ratio",line.sam_ratio
			sam_ratio_tot = line.prime_cost * line.sam_ratio
			print"sam_ratio_totsam_ratio_tot",sam_ratio_tot
			dealer_discount_tot = sam_ratio_tot / (( 100 - line.dealer_discount ) / 100.00 ) - sam_ratio_tot
			print"dealer_discount_totdealer_discount_tot",dealer_discount_tot
			i_tot = sam_ratio_tot + dealer_discount_tot
			customer_discount_tot = i_tot / (( 100 - line.customer_discount ) / 100.00 ) - i_tot
			print"customer_discount_totcustomer_discount_tot",customer_discount_tot
			k_tot = i_tot + customer_discount_tot
			spl_discount_tot = k_tot / (( 100 - line.special_discount ) / 100.00 ) - k_tot
			print"spl_discount_totspl_discount_tot",spl_discount_tot
			m_tot = k_tot + spl_discount_tot
			tax_tot = (m_tot / 100) * line.tax
			print"tax_tottax_tot",tax_tot
			p_f_tot = ( m_tot + tax_tot ) / 100.00 * line.p_f
			print"p_f_totp_f_tot",p_f_tot
			p_tot = m_tot + tax_tot + p_f_tot
			freight_tot = p_tot / (( 100 - line.freight ) / 100.00 ) - p_tot
			print"freight_totfreight_tot",freight_tot
			r_tot = p_tot + freight_tot
			insurance_tot = r_tot / (( 100 - line.insurance ) / 100.00 ) - r_tot
			print"insurance_totinsurance_tot",insurance_tot
			pump_price_tot = r_tot + insurance_tot
			print"pump_price_totpump_price_tot",pump_price_tot
			tot_price = pump_price_tot
			print"tot_pricetot_price",tot_price
			net_amount = tot_price * line.qty
			print"net_amountnet_amount",net_amount
			
			res[line.id]['sam_ratio_tot'] = sam_ratio_tot
			res[line.id]['dealer_discount_tot'] = dealer_discount_tot
			res[line.id]['customer_discount_tot'] = customer_discount_tot
			res[line.id]['spl_discount_tot'] = spl_discount_tot
			res[line.id]['tax_tot'] = tax_tot
			res[line.id]['p_f_tot'] = p_f_tot
			res[line.id]['freight_tot'] = freight_tot
			res[line.id]['insurance_tot'] = insurance_tot
			res[line.id]['pump_price_tot'] = pump_price_tot
			res[line.id]['tot_price'] = tot_price
			res[line.id]['net_amount'] = net_amount
			
		return res
		
	_name = "ch.pump.offer"
	_description = "Ch Pump Offer"
	
	_columns = {
	
		### Pump Details ####
		'header_id':fields.many2one('kg.crm.offer', 'Offer', ondelete='cascade'),
		'offer_id':fields.many2one('kg.crm.offer', 'Offer'),
		'qty':fields.integer('Quantity'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),
		'pumpseries_id': fields.many2one('kg.pumpseries.master','Pump Series'),
		'moc_const_id': fields.many2one('kg.moc.construction','MOC'),
		'prime_cost': fields.float('Prime Cost'),
		'per_pump_prime_cost': fields.float('Per Pump Prime Cost'),
		'sam_ratio': fields.float('Sam Ratio(%)'),
		'dealer_discount': fields.float('Dealer Discount(%)'),
		'customer_discount': fields.float('Customer Discount(%)'),
		'special_discount': fields.float('Special Discount(%)'),
		'tax': fields.float('Tax(%)'),
		'p_f': fields.float('P&F(%)'),
		'freight': fields.float('Freight(%)'),
		'insurance': fields.float('Insurance(%)'),
		'total_price': fields.float('Total Price(%)'),
		
		'tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Price',multi="sums",store=True),	
		'sam_ratio_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Sam Ratio',multi="sums",store=True),	
		'dealer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),	
		'customer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),	
		'spl_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Special Discount Value',multi="sums",store=True),	
		'tax_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax',multi="sums",store=True),	
		'p_f_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F',multi="sums",store=True),	
		'freight_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),	
		'insurance_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),	
		'pump_price_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Pump Price',multi="sums",store=True),	
		'net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),	
		
		'enquiry_line_id': fields.many2one('ch.kg.crm.pumpmodel','Enquiry Line'),
		'off_fou_id': fields.related('enquiry_line_id','line_ids', type='one2many', relation='ch.kg.crm.foundry.item', string='Foundry Items'),
		'off_ms_id': fields.related('enquiry_line_id','line_ids_a', type='one2many', relation='ch.kg.crm.machineshop.item', string='MS Items'),
		'off_bot_id': fields.related('enquiry_line_id','line_ids_b', type='one2many', relation='ch.kg.crm.bot', string='BOT Items'),
		
		
	}
	
	#~ _defaults = {
		#~ 
		#~ 'temperature': 'normal',
		#~ 'flange_type': 'standard',
		#~ 'load_bom':False,
		#~ 
	#~ }

ch_pump_offer()


class ch_spare_offer(osv.osv):

	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		sam_ratio_tot = dealer_discount_tot = customer_discount_tot = spl_discount_tot = tax_tot = p_f_tot = freight_tot = insurance_tot = pump_price_tot = tot_price = net_amount = 0
		i_tot = k_tot = m_tot = p_tot = r_tot = 0
		for line in self.browse(cr, uid, ids, context=context):
			print"linelineline",line
			res[line.id] = {
				
				'sam_ratio_tot': 0.0,
				'dealer_discount_tot': 0.0,
				'customer_discount_tot' : 0.0,
				'spl_discount_tot' : 0.0,
				'tax_tot': 0.0,
				'p_f_tot': 0.0,
				'freight_tot': 0.0,
				'insurance_tot': 0.0,
				'pump_price': 0.0,
				'tot_price': 0.0,
				
			}
			print"line.prime_cost",line.prime_cost
			print"line.sam_ratio",line.sam_ratio
			sam_ratio_tot = line.prime_cost * line.sam_ratio
			print"sam_ratio_totsam_ratio_tot",sam_ratio_tot
			dealer_discount_tot = sam_ratio_tot / (( 100 - line.dealer_discount ) / 100.00 ) - sam_ratio_tot
			print"dealer_discount_totdealer_discount_tot",dealer_discount_tot
			i_tot = sam_ratio_tot + dealer_discount_tot
			customer_discount_tot = i_tot / (( 100 - line.customer_discount ) / 100.00 ) - i_tot
			print"customer_discount_totcustomer_discount_tot",customer_discount_tot
			k_tot = i_tot + customer_discount_tot
			spl_discount_tot = k_tot / (( 100 - line.special_discount ) / 100.00 ) - k_tot
			print"spl_discount_totspl_discount_tot",spl_discount_tot
			m_tot = k_tot + spl_discount_tot
			tax_tot = (m_tot / 100) * line.tax
			print"tax_tottax_tot",tax_tot
			p_f_tot = ( m_tot + tax_tot ) / 100.00 * line.p_f
			print"p_f_totp_f_tot",p_f_tot
			p_tot = m_tot + tax_tot + p_f_tot
			freight_tot = p_tot / (( 100 - line.freight ) / 100.00 ) - p_tot
			print"freight_totfreight_tot",freight_tot
			r_tot = p_tot + freight_tot
			insurance_tot = r_tot / (( 100 - line.insurance ) / 100.00 ) - r_tot
			print"insurance_totinsurance_tot",insurance_tot
			pump_price_tot = r_tot + insurance_tot
			print"pump_price_totpump_price_tot",pump_price_tot
			tot_price = pump_price_tot 
			print"tot_pricetot_price",tot_price
			net_amount = tot_price * 1
			print"net_amountnet_amount",net_amount
			
			res[line.id]['sam_ratio_tot'] = sam_ratio_tot
			res[line.id]['dealer_discount_tot'] = dealer_discount_tot
			res[line.id]['customer_discount_tot'] = customer_discount_tot
			res[line.id]['spl_discount_tot'] = spl_discount_tot
			res[line.id]['tax_tot'] = tax_tot
			res[line.id]['p_f_tot'] = p_f_tot
			res[line.id]['freight_tot'] = freight_tot
			res[line.id]['insurance_tot'] = insurance_tot
			res[line.id]['pump_price_tot'] = pump_price_tot
			res[line.id]['tot_price'] = tot_price
			res[line.id]['net_amount'] = net_amount
			
		return res
		
	_name = "ch.spare.offer"
	_description = "Ch Spare Offer"
	
	_columns = {
	
		### Pump Details ####
		'header_id':fields.many2one('kg.crm.offer', 'Offer', ondelete='cascade'),
		'offer_id':fields.many2one('kg.crm.offer', 'Offer'),
		'qty':fields.integer('Quantity'),
		'item_code': fields.char('Item Code'),
		'item_name': fields.char('Item Name'),
		'moc_id': fields.many2one('kg.moc.master','MOC Name'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No'),
		'ms_id': fields.many2one('kg.machine.shop','MS Name'),
		'bot_id': fields.many2one('kg.machine.shop','BOT Name'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),
		'pumpseries_id': fields.many2one('kg.pumpseries.master','Pump Series'),
		'moc_const_id': fields.many2one('kg.moc.construction','MOC'),
		'prime_cost': fields.float('Prime Cost'),
		'sam_ratio': fields.float('Sam Ratio(%)'),
		'dealer_discount': fields.float('Dealer Discount(%)'),
		'customer_discount': fields.float('Customer Discount(%)'),
		'special_discount': fields.float('Special Discount(%)'),
		'tax': fields.float('Tax(%)'),
		'p_f': fields.float('P&F(%)'),
		'freight': fields.float('Freight(%)'),
		'insurance': fields.float('Insurance(%)'),
		'total_price': fields.float('Total Price'),
		
		'tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Price',multi="sums",store=True),	
		'sam_ratio_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Sam Ratio',multi="sums",store=True),	
		'dealer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),	
		'customer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),	
		'spl_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Special Discount Value',multi="sums",store=True),	
		'tax_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax',multi="sums",store=True),	
		'p_f_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F',multi="sums",store=True),	
		'freight_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),	
		'insurance_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),	
		'pump_price_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Pump Price',multi="sums",store=True),	
		'net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),	
		
		'enquiry_line_id': fields.many2one('ch.kg.crm.pumpmodel','Enquiry Line'),
		'off_fou_id': fields.related('enquiry_line_id','line_ids', type='one2many', relation='ch.kg.crm.foundry.item', string='Foundry Items'),
		'off_ms_id': fields.related('enquiry_line_id','line_ids_a', type='one2many', relation='ch.kg.crm.machineshop.item', string='MS Items'),
		'off_bot_id': fields.related('enquiry_line_id','line_ids_b', type='one2many', relation='ch.kg.crm.bot', string='BOT Items'),
		
		
	}
	

ch_spare_offer()

class ch_accessories_offer(osv.osv):
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		sam_ratio_tot = dealer_discount_tot = customer_discount_tot = spl_discount_tot = tax_tot = p_f_tot = freight_tot = insurance_tot = pump_price_tot = tot_price = net_amount = 0
		i_tot = k_tot = m_tot = p_tot = r_tot = 0
		for line in self.browse(cr, uid, ids, context=context):
			print"linelineline",line
			res[line.id] = {
				
				'sam_ratio_tot': 0.0,
				'dealer_discount_tot': 0.0,
				'customer_discount_tot' : 0.0,
				'spl_discount_tot' : 0.0,
				'tax_tot': 0.0,
				'p_f_tot': 0.0,
				'freight_tot': 0.0,
				'insurance_tot': 0.0,
				'pump_price': 0.0,
				'tot_price': 0.0,
				
			}
			print"line.prime_cost",line.prime_cost
			print"line.sam_ratio",line.sam_ratio
			sam_ratio_tot = line.prime_cost * line.sam_ratio
			print"sam_ratio_totsam_ratio_tot",sam_ratio_tot
			dealer_discount_tot = sam_ratio_tot / (( 100 - line.dealer_discount ) / 100.00 ) - sam_ratio_tot
			print"dealer_discount_totdealer_discount_tot",dealer_discount_tot
			i_tot = sam_ratio_tot + dealer_discount_tot
			customer_discount_tot = i_tot / (( 100 - line.customer_discount ) / 100.00 ) - i_tot
			print"customer_discount_totcustomer_discount_tot",customer_discount_tot
			k_tot = i_tot + customer_discount_tot
			spl_discount_tot = k_tot / (( 100 - line.special_discount ) / 100.00 ) - k_tot
			print"spl_discount_totspl_discount_tot",spl_discount_tot
			m_tot = k_tot + spl_discount_tot
			tax_tot = (m_tot / 100) * line.tax
			print"tax_tottax_tot",tax_tot
			p_f_tot = ( m_tot + tax_tot ) / 100.00 * line.p_f
			print"p_f_totp_f_tot",p_f_tot
			p_tot = m_tot + tax_tot + p_f_tot
			freight_tot = p_tot / (( 100 - line.freight ) / 100.00 ) - p_tot
			print"freight_totfreight_tot",freight_tot
			r_tot = p_tot + freight_tot
			insurance_tot = r_tot / (( 100 - line.insurance ) / 100.00 ) - r_tot
			print"insurance_totinsurance_tot",insurance_tot
			pump_price_tot = r_tot + insurance_tot
			print"pump_price_totpump_price_tot",pump_price_tot
			tot_price = pump_price_tot 
			print"tot_pricetot_price",tot_price
			net_amount = tot_price * line.qty
			print"net_amountnet_amount",net_amount
			
			res[line.id]['sam_ratio_tot'] = sam_ratio_tot
			res[line.id]['dealer_discount_tot'] = dealer_discount_tot
			res[line.id]['customer_discount_tot'] = customer_discount_tot
			res[line.id]['spl_discount_tot'] = spl_discount_tot
			res[line.id]['tax_tot'] = tax_tot
			res[line.id]['p_f_tot'] = p_f_tot
			res[line.id]['freight_tot'] = freight_tot
			res[line.id]['insurance_tot'] = insurance_tot
			res[line.id]['pump_price_tot'] = pump_price_tot
			res[line.id]['tot_price'] = tot_price
			res[line.id]['net_amount'] = net_amount
			
		return res
		
	_name = "ch.accessories.offer"
	_description = "Ch Accessories Offer"
	
	_columns = {
	
		### Spare Details ####
		'header_id':fields.many2one('kg.crm.offer', 'Offer', ondelete='cascade'),
		'offer_id':fields.many2one('kg.crm.offer', 'Offer'),
		'enquiry_line_id': fields.many2one('ch.kg.crm.pumpmodel','Enquiry Line'),
		'access_id':fields.many2one('kg.accessories.master', 'Item Name'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),
		'moc_id':fields.many2one('kg.moc.master', 'MOC'),
		'qty':fields.integer('Quantity'),
		'prime_cost': fields.float('Prime Cost'),
		'per_access_prime_cost': fields.float('Per Access Prime Cost'),
		'sam_ratio': fields.float('Sam Ratio(%)'),
		'dealer_discount': fields.float('Dealer Discount(%)'),
		'customer_discount': fields.float('Customer Discount(%)'),
		'special_discount': fields.float('Special Discount(%)'),
		'tax': fields.float('Tax(%)'),
		'p_f': fields.float('P&F(%)'),
		'freight': fields.float('Freight(%)'),
		'insurance': fields.float('Insurance(%)'),
		'pump_price': fields.float('Pump Price'),
		'total_price': fields.float('Total Price'),
		
		'tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Price',multi="sums",store=True),	
		'sam_ratio_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Sam Ratio',multi="sums",store=True),	
		'dealer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),	
		'customer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),	
		'spl_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Special Discount Value',multi="sums",store=True),	
		'tax_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax',multi="sums",store=True),	
		'p_f_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F',multi="sums",store=True),	
		'freight_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),	
		'insurance_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),	
		'pump_price_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Pump Price',multi="sums",store=True),	
		'net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),	
		
		'enquiry_line_access_id': fields.many2one('ch.kg.crm.accessories','Enquiry Line'),
		'off_fou_id': fields.related('enquiry_line_access_id','line_ids', type='one2many', relation='ch.crm.access.fou', string='Foundry Items'),
		'off_ms_id': fields.related('enquiry_line_access_id','line_ids_a', type='one2many', relation='ch.crm.access.ms', string='MS Items'),
		'off_bot_id': fields.related('enquiry_line_access_id','line_ids_b', type='one2many', relation='ch.crm.access.bot', string='BOT Items'),
		
		
	}
	
ch_accessories_offer()

