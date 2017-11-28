from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime
import base64
from itertools import groupby
import re

from PIL import Image

import StringIO
import base64
import string
try:
	import xlwt
except:
   raise osv.except_osv('Warning !','Please download python xlwt module from\nhttp://pypi.python.org/packages/source/x/xlwt/xlwt-0.7.2.tar.gz\nand install it')

record={}
wbk = xlwt.Workbook()
style_mast_header = xlwt.easyxf('font: height 320;font: bold off;align: wrap on;align: wrap off, vert bottom, horiz center;border: top thin, bottom thin, left thin, right thin;')
style_header1 = xlwt.easyxf('font: bold on,height 200;align: wrap off, vert bottom, horiz center;border: top thin, bottom thin, left thin, right thin;')
style_center = xlwt.easyxf('font: height 180,name Calibri;align: wrap off, vert bottom, horiz center;border: top thin, bottom thin, left thin, right thin;')		
style_left_header = xlwt.easyxf('font: bold on,height 220,color_index 0X36;align: wrap off, vert center, horiz left;border: top thin, bottom thin, left thin, right thin;')			
style_left = xlwt.easyxf('font: height 180,name Calibri;align: wrap off, vert bottom, horiz left;border: top thin, bottom thin, left thin, right thin;')
style_right = xlwt.easyxf('font: height 180,name Calibri;align: wrap off, vert bottom, horiz right;border: top thin, bottom thin, left thin, right thin;',num_format_str='#,##,##0.00')             		
style_sub_left = xlwt.easyxf('font: height 180,underline on,bold on,name Calibri;align: wrap off, vert bottom, horiz left;border: top thin, bottom thin, left thin, right thin;')		
style_highlight = xlwt.easyxf('font: height 180,bold on,name Calibri,color_index black;align: wrap off, vert bottom, horiz left;border: top thin, bottom thin, left thin, right thin;')		
style_right_header = xlwt.easyxf('font: height 180,bold on,name Calibri,color_index black;align: wrap off, vert bottom, horiz right;border: top thin, bottom thin, left thin, right thin;')     
style_center_header = xlwt.easyxf('font: height 180,bold on,name Calibri,color_index black;align: wrap off, vert bottom, horiz center;border: top thin, bottom thin, left thin, right thin;')
style1 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz center;''borders: left thin, right thin, top thin, bottom thin')
style2 = xlwt.easyxf('font: height 200,color_index black;' 'align: horiz right;''borders: left thin, right thin, top thin, bottom thin')
style3 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz right;''borders: left thin, right thin, top thin, bottom thin')
style41 = xlwt.easyxf('font: height 200,bold on,color_index black;' 'align: horiz center;''borders: left thin, right thin, top thin, bottom thin')		
style4 = xlwt.easyxf('font: height 200,color_index black;' 'align: horiz center;''borders: left thin, right thin, top thin, bottom thin')



CALL_TYPE_SELECTION = [
	('service','Service'),
	('new_enquiry','New Enquiry')
]
PURPOSE_SELECTION = [
	('pump','Pump'),('spare','Spare'),('access','Accessories'),('prj','Project'),('pump_spare','Pump With Spare'),('in_development','New Development')
]
STATE_SELECTION = [
	('draft','Draft'),('moved_to_offer','Confirmed'),('wfa_md','WFA MD'),('approved_md','Approved MD'),('call','Call Back'),('quote','Quote Process'),('wo_created','WO Created'),('wo_released','WO Released'),('reject','Rejected'),('revised','Revised')
]
MARKET_SELECTION = [
	('cp','CP'),('ip','IP')
]

class kg_crm_offer(osv.osv):
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		pump_net_amount = spare_net_amount = access_net_amount = offer_net_amount = component_net_amount = supervision_amount = 0.00
		offer_sam_ratio_tot = offer_dealer_discount_tot = offer_spl_discount_tot = offer_p_f_tot = offer_insurance_tot = offer_freight_tot = offer_tax_tot = offer_customer_discount_tot = offer_prime_cost_tot = sam_ratio_tot = 0.00
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'pump_net_amount': 0.0,
				'spare_net_amount': 0.0,
				'access_net_amount': 0.0,
				'offer_net_amount': 0.0,
				'component_net_amount': 0.0,
				'supervision_amount': 0.0,
				'offer_prime_cost_tot': 0.0,
			}
			
			#~ cur = order.customer_id.property_product_pricelist_purchase.currency_id
			
			for line in order.line_pump_ids:
				pump_net_amount += line.net_amount
				print"pump_net_amount",pump_net_amount
				supervision_amount += line.supervision_amount
				offer_sam_ratio_tot += line.r_sam_ratio_tot
				print"pump_offer_sam_ratio_tot-------------------",offer_sam_ratio_tot
				offer_prime_cost_tot += line.prime_cost
				offer_dealer_discount_tot += line.r_dealer_discount_tot
				offer_spl_discount_tot += line.r_spl_discount_tot
				offer_p_f_tot += line.r_p_f_tot
				offer_insurance_tot += line.r_insurance_tot
				offer_freight_tot += line.r_freight_tot
				offer_tax_tot += line.r_tax_tot
				offer_customer_discount_tot += line.r_customer_discount_tot
				offer_net_amount += line.r_net_amt_tot
			for line in order.line_spare_ids:
				spare_net_amount += line.net_amount
				print"spare_net_amount",spare_net_amount
				supervision_amount += line.supervision_amount
				offer_sam_ratio_tot += line.r_sam_ratio_tot
				print"sasasasaoffer_sam_ratio_tot",offer_sam_ratio_tot
				offer_prime_cost_tot += line.prime_cost
				offer_dealer_discount_tot += line.r_dealer_discount_tot
				offer_spl_discount_tot += line.r_spl_discount_tot
				offer_p_f_tot += line.r_p_f_tot
				offer_insurance_tot += line.r_insurance_tot
				offer_freight_tot += line.r_freight_tot
				offer_tax_tot += line.r_tax_tot
				offer_customer_discount_tot += line.r_customer_discount_tot
				offer_net_amount += line.r_net_amt_tot
			for line in order.line_accessories_ids:
				access_net_amount += line.net_amount
				print"access_net_amount",access_net_amount
				offer_sam_ratio_tot += line.r_sam_ratio_tot
				print"acacaoffer_sam_ratio_tot",offer_sam_ratio_tot
				offer_prime_cost_tot += line.prime_cost
				offer_dealer_discount_tot += line.r_dealer_discount_tot
				offer_spl_discount_tot += line.r_spl_discount_tot
				offer_p_f_tot += line.r_p_f_tot
				offer_insurance_tot += line.r_insurance_tot
				offer_freight_tot += line.r_freight_tot
				offer_tax_tot += line.r_tax_tot
				offer_customer_discount_tot += line.r_customer_discount_tot
				offer_net_amount += line.r_net_amt_tot
			for line in order.line_component_ids:
				component_net_amount += line.net_amount
				print"component_net_amount",component_net_amount
				
			res[order.id]['pump_net_amount'] = round(pump_net_amount)
			res[order.id]['spare_net_amount'] = round(spare_net_amount)
			res[order.id]['access_net_amount'] = round(access_net_amount)
			print"pump_net_amount",pump_net_amount
			print"access_net_amount",access_net_amount
			#~ res[order.id]['offer_net_amount'] = pump_net_amount + spare_net_amount + access_net_amount
			sam_ratio_tot = round((offer_sam_ratio_tot / (offer_prime_cost_tot or 1)),2)
			res[order.id]['sam_ratio_tot'] = sam_ratio_tot
			res[order.id]['offer_prime_cost_tot'] = round(offer_prime_cost_tot)
			res[order.id]['offer_sam_ratio_tot'] = round(offer_sam_ratio_tot)
			res[order.id]['offer_dealer_discount_tot'] = round(offer_dealer_discount_tot)
			res[order.id]['offer_spl_discount_tot'] = round(offer_spl_discount_tot)
			res[order.id]['offer_p_f_tot'] = round(offer_p_f_tot)
			res[order.id]['offer_insurance_tot'] = round(offer_insurance_tot)
			res[order.id]['offer_freight_tot'] = round(offer_freight_tot)
			res[order.id]['offer_tax_tot'] = round(offer_tax_tot)
			res[order.id]['offer_customer_discount_tot'] = round(offer_customer_discount_tot)
			res[order.id]['offer_net_amount'] = round(offer_net_amount)
			print"res[order.id]['offer_net_amount']--------------",res[order.id]['offer_net_amount']
			
			res[order.id]['component_net_amount'] = round(component_net_amount)
			res[order.id]['supervision_amount'] = round(supervision_amount)
			
		return res
	
	_name = "kg.crm.offer"
	_description = "CRM Offer Entry"
	_order = "enquiry_date desc"
	
	_columns = {
		
		## Basic Info
		
		'name': fields.char('Offer No', size=128,select=True,readonly=True, states={'draft':[('readonly',False)]}),
		'note': fields.char('Notes'),
		'offer_date': fields.date('Offer Date',required=True),
		'remarks': fields.text('Remarks'),
		'cancel_remark': fields.text('Cancel Remarks'),
		'state': fields.selection(STATE_SELECTION,'Status', readonly=True),
		
		## Module Requirement Info
		
		'enquiry_id': fields.many2one('kg.crm.enquiry','Enquiry No.'),
		'enquiry_no': fields.char('Enquiry No.'),
		'schedule_no': fields.char('Schedule No', size=128,select=True),
		'enquiry_date': fields.related('enquiry_id','offer_date', type='date', string='Enquiry Date', store=True,required=True),
		'customer_id': fields.related('enquiry_id','customer_id', type='many2one', relation="res.partner", string='Customer Name', store=True),
		'del_date': fields.date('Expected Delivery Date',readonly=True,states={'draft':[('readonly',False)],'moved_to_offer':[('readonly',False)]}),
		'due_date': fields.date('Due Date',readonly=True,states={'draft':[('readonly',False)],'moved_to_offer':[('readonly',False)]}),
		'md_approved_date': fields.date('MD Approved Date',readonly=True),
		'service_det': fields.char('Service Details'),
		'location': fields.selection([('ipd','IPD'),('ppd','PPD'),('export','Export')],'Location'),
		'dom_freight': fields.selection([('topay','To pay'),('paid','Paid'),('paid_reimburse','Paid & reimbursement')],'Freight',readonly=False,states={'wo_created':[('readonly',True)]}),
		'freight': fields.selection([('topay','Topay'),('paid','Paid')],'Freight',readonly=False,states={'wo_created':[('readonly',True)]}),
		'offer_copy': fields.char('Offer Copy'),
		'term_copy': fields.char('Terms Copy'),
		'customer_po_no': fields.char('Customer PO No.',readonly=True,states={'draft':[('readonly',False)],'moved_to_offer':[('readonly',False)],'approved_md':[('readonly',False)]}),
		'cust_po_date': fields.date('Customer PO Date',readonly=True,states={'draft':[('readonly',False)],'moved_to_offer':[('readonly',False)],'approved_md':[('readonly',False)]}),
		'cpo_del': fields.char('Delivery as per C.P.O',readonly=True,states={'draft':[('readonly',False)],'moved_to_offer':[('readonly',False)]}),
		'dealer_po_no': fields.char('Dealer PO No.',readonly=True,states={'draft':[('readonly',False)],'moved_to_offer':[('readonly',False)]}),
		'deal_po_date': fields.date('Dealer PO Date',readonly=True,states={'draft':[('readonly',False)],'moved_to_offer':[('readonly',False)]}),
		'sam_del': fields.char('Delivery consider by SAM',readonly=True,states={'draft':[('readonly',False)],'moved_to_offer':[('readonly',False)]}),
		'revision': fields.integer('Revision'),
		'wo_flag': fields.boolean('WO Flag'),
		'load_term': fields.boolean('Terms Applicable',readonly=True, states={'draft':[('readonly',False)],'moved_to_offer':[('readonly',False)]}),
		'revision_remarks': fields.text('Revision Remarks'),
		
		#~ 'ch_line_ids': fields.one2many('ch.kg.crm.pumpmodel', 'header_id', "Pump/Spare Details"),
		'due_date': fields.date('Due Date',required=True),
		'call_type': fields.selection(CALL_TYPE_SELECTION,'Call Type', required=True),
		'ref_mode': fields.selection([('direct','Direct'),('dealer','Dealer')],'Reference Mode', required=True),
		'market_division': fields.selection(MARKET_SELECTION,'Marketing Division'),
		'division_id': fields.many2one('kg.division.master','Division',domain="[('state','not in',('reject','cancel'))]",required=True),
		'division_code': fields.char('Division Code',readonly=True,required=True),
		'ref_no': fields.char('Reference Number'),
		'segment': fields.selection([('dom','Domestic'),('exp','Export')],'Segment', required=True),
		'dealer_id': fields.many2one('res.partner','Dealer Name',domain=[('dealer','=',True),('contact','=',False)]),
		'industry_id': fields.many2one('kg.industry.master','Sector'),
		'expected_value': fields.float('Expected Value'),
		'del_date': fields.date('Expected Del Date'),
		'reminder_date': fields.date('Reminder Date',readonly=True, states={'draft':[('readonly',False)]}),
		'purpose': fields.selection(PURPOSE_SELECTION,'Purpose'),
		'chemical_id': fields.many2one('kg.chemical.master','Chemical',domain=[('purpose','=','general')]),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Name'),
		's_no': fields.char('Serial Number'),
		'wo_no': fields.char('WO Number'),
		'requirements': fields.text('Requirements'),
		'is_zero_offer': fields.boolean('Is Zero Value Offer'),
		'flag_data_bank': fields.boolean('Is Data WO',readonly=True, states={'draft':[('readonly',False)]}),
		
		'scope_of_supply': fields.selection([('bare_pump','Bare Pump'),('pump_with_acces','Pump With Accessories'),('pump_with_acces_motor','Pump With Accessories And Motor')],'Scope of Supply'),
		'pump': fields.selection([('gld_packing','Gland Packing'),('mc_seal','M/C Seal'),('dynamic_seal','Dynamic seal')],'Shaft Sealing', required=True),
		'drive': fields.selection([('motor','Motor'),('vfd','VFD'),('engine','Engine')],'Drive'),
		'transmision': fields.selection([('cpl','Coupling'),('belt','Belt Drive'),('fc','Fluid Coupling'),('gear_box','Gear Box'),('fc_gear_box','Fluid Coupling With Gear Box')],'Transmision', required=True),
		'acces': fields.selection([('yes','Yes'),('no','No')],'Accessories'),
		'excise_duty': fields.selection([('inclusive','Inclusive'),('extra','Extra'),('exemted','Exemted - Export'),('pac','PAC'),('sez','SEZ'),('ct1','CT1'),('ct3','CT3')],'EXCISE DUTY',readonly=True, states={'draft':[('readonly',False)],'moved_to_offer':[('readonly',False)]}),
		'drawing_approval': fields.selection([('yes','Yes'),('no','No')],'Drawing approval',readonly=True, states={'draft':[('readonly',False)],'moved_to_offer':[('readonly',False)]}),
		'road_permit': fields.selection([('yes','Yes'),('no','No')],'Road Permit',readonly=True, states={'draft':[('readonly',False)],'moved_to_offer':[('readonly',False)]}),
		'inspection': fields.selection([('yes','Yes'),('no','No'),('tpi','TPI'),('customer','Customer'),('consultant','Consultant'),('stagewise','Stage wise')],'Inspection',readonly=True, states={'draft':[('readonly',False)],'moved_to_offer':[('readonly',False)]}),
		'l_d_clause': fields.char('L. D. CLAUSE / Penalty',readonly=True, states={'draft':[('readonly',False)],'moved_to_offer':[('readonly',False)]}),
		#~ 'l_d_clause': fields.selection([('5_1','0.5 - 1.0% of total order value'),('1_10','1 to 10% of total order value'),('nill','Nill')],'L. D. CLAUSE / Penalty',readonly=True, states={'draft':[('readonly',False)],'moved_to_offer':[('readonly',False)]}),
		'pump_per_flag': fields.boolean('Pump',readonly=True, states={'draft':[('readonly',False)]}),
		'spare_per_flag': fields.boolean('Spare',readonly=True, states={'draft':[('readonly',False)]}),
		'access_per_flag': fields.boolean('Accessories',readonly=True, states={'draft':[('readonly',False)]}),
		'super_per_flag': fields.boolean('Supervision',readonly=True, states={'draft':[('readonly',False)]}),
		'o_sam_ratio': fields.float('Sam Ratio',readonly=True, states={'draft':[('readonly',False)]}),
		'o_dealer_discount': fields.float('Dealer Discount(%)',readonly=True, states={'draft':[('readonly',False)]}),
		'o_special_discount': fields.float('Special Discount(%)',readonly=True, states={'draft':[('readonly',False)]}),
		'o_p_f': fields.float('P&F(%)',readonly=True, states={'draft':[('readonly',False)]}),
		'o_freight': fields.float('Freight(%)',readonly=True, states={'draft':[('readonly',False)]}),
		'o_insurance': fields.float('Insurance(%)',readonly=True, states={'draft':[('readonly',False)]}),
		'o_p_f_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'P&F',readonly=True, states={'draft':[('readonly',False)]}),
		'o_freight_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Freight',readonly=True, states={'draft':[('readonly',False)]}),
		'o_insurance_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Insurance',readonly=True, states={'draft':[('readonly',False)]}),
		'o_tax_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Tax',readonly=True, states={'draft':[('readonly',False)]}),
		'o_ed_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'ED',readonly=True, states={'draft':[('readonly',False)]}),
		'o_customer_discount': fields.float('Mark-Up(%)',readonly=True, states={'draft':[('readonly',False)]}),
		'o_tax': fields.float('Tax(%)',readonly=True, states={'draft':[('readonly',False)]}),
		'o_ed': fields.float('ED(%)',readonly=True, states={'draft':[('readonly',False)]}),
		'o_agent_com': fields.float('Agent Commission(%)',readonly=True, states={'draft':[('readonly',False)]}),
		'off_status': fields.selection([('on_hold','On Hold'),('closed','Closed'),('to_be_follow','To be Followed')],'Offer Status',readonly=False,states={'wo_created':[('readonly',True)],'wo_released':[('readonly',True)]}),
		'dummy_flag': fields.boolean('Dummy Flag'),
		'annexure_1': fields.html('Annexure 1',readonly=True, states={'draft':[('readonly',False)]}),
		'prj_name': fields.char('Project Name',readonly=True, states={'draft':[('readonly',False)]}),
		'del_term': fields.selection([('ex_works','Ex-Works'),('fob','FOB'),('cfr','CFR'),('cif','CIF'),('cpt','CPT')],'Delivery Term',readonly=True, states={'draft':[('readonly',False)]}),
		'mode_of_dispatch': fields.selection([('sea','Sea Worthy'),('air','Air Worthy')],'Mode Of Dispatch',readonly=True, states={'draft':[('readonly',False)]}),
		'zone': fields.selection([('north','North'),('south','South'),('east','East'),('west','West'),('mines','Mines')],'Zone',readonly=True, states={'draft':[('readonly',False)]}),
		
		'r_o_dealer_discount': fields.float('Dealer Discount(%)',readonly=True, states={'draft':[('readonly',False)]}),
		'r_o_special_discount': fields.float('Special Discount(%)',readonly=True, states={'draft':[('readonly',False)]}),
		'r_o_p_f': fields.float('P&F(%)',readonly=True, states={'draft':[('readonly',False)]}),
		'r_o_freight': fields.float('Freight(%)',readonly=True, states={'draft':[('readonly',False)]}),
		'r_o_insurance': fields.float('Insurance(%)',readonly=True, states={'draft':[('readonly',False)]}),
		'r_o_p_f_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'P&F',readonly=True, states={'draft':[('readonly',False)]}),
		'r_o_freight_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Freight',readonly=True, states={'draft':[('readonly',False)]}),
		'r_o_insurance_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Insurance',readonly=True, states={'draft':[('readonly',False)]}),
		'r_o_customer_discount': fields.float('Customer Discount(%)',readonly=True, states={'draft':[('readonly',False)]}),
		'r_o_cust_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Customer Discount',readonly=True, states={'draft':[('readonly',False)]}),
		
		# Pump Offer Fields
		'offer_prime_cost_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Primecost',multi="sums",store=True),
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
		
		'offer_sam_ratio_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Works Value',multi="sums",store=True),
		'sam_ratio_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Sam Ratio',multi="sums",store=True),
		'offer_dealer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Dsicount',multi="sums",store=True),
		'offer_spl_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Special Discount',multi="sums",store=True),
		'offer_p_f_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F',multi="sums",store=True),
		'offer_insurance_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),
		'offer_freight_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),
		'offer_tax_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='GST',multi="sums",store=True),
		'offer_customer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount',multi="sums",store=True),
		'offer_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Offer Amount',multi="sums",store=True),
		'component_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Component Charge',multi="sums",store=True),
		'supervision_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Supervision Charge',multi="sums",store=True),
		
		## Child Tables Declaration
		
		'line_pump_ids': fields.one2many('ch.pump.offer', 'header_id', "Pump Offer"),
		'line_spare_ids': fields.one2many('ch.spare.offer', 'header_id', "Spare Offer"),
		'line_component_ids': fields.one2many('ch.crm.component.offer', 'header_id', "Component Offer"),
		'line_accessories_ids': fields.one2many('ch.accessories.offer', 'header_id', "Accessories Offer"),
		'line_supervision_ids': fields.one2many('ch.supervision.offer', 'header_id', "Supervision Charge"),
		'line_term_ids': fields.one2many('ch.term.offer', 'header_id', "Term Offer"),
		'line_remark_ids': fields.one2many('ch.crm.off.remark', 'header_id', "Remarks",readonly=True, states={'draft':[('readonly',False)]}),
		'line_attach_ids': fields.one2many('ch.crm.off.attachments', 'header_id', "Attachments",readonly=True, states={'draft':[('readonly',False)]}),
		
		## Entry Info
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'crt_date': fields.datetime('Created Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),	   
		
		## Offer Copy 
		
		'rep_data':fields.binary("Offer Copy",readonly=True),
		'term_data':fields.binary("Terms Copy",readonly=True),
		
		### Spare Reports Purpose
		
		'spare_reg_data':fields.binary("Spare Regular Copy",readonly=True),
		'spare_bud_data':fields.binary("Spare Budgetary Copy",readonly=True),
		'spare_reg_copy': fields.char('Spare Regular Copy'),
		'spare_bud_copy': fields.char('Spare Budgetary Copy'),
		
	}
	
	_defaults = {
		
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg_crm_offer', context=c),
		'enquiry_date': lambda * a: time.strftime('%Y-%m-%d'),
		'offer_date': lambda * a: time.strftime('%Y-%m-%d'),
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date': time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',
		'pump': 'gld_packing',
		'transmision': 'cpl',
		'ref_mode': 'direct',
		'call_type': 'new_enquiry',
		'active': True,
		'wo_flag': False,
	#	'division_id':_get_default_division,
		'due_date': lambda * a: time.strftime('%Y-%m-%d'),
		'revision': 0,
		'is_zero_offer': False,
		'flag_data_bank': False,
		'off_status': 'to_be_follow',
		'r_o_cust_in_ex':'inclusive',
	}
	
	def _supervision(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.line_supervision_ids:
			if len(rec.line_supervision_ids) > 1:
				raise osv.except_osv(_('Warning!'),_('Supervision more than one not allowed!!'))
		if rec.off_status in ('on_hold','closed'):
			if not rec.line_remark_ids:
				raise osv.except_osv(_('Warning!'),_('You cannot save without Remarks'))
			for item in rec.line_remark_ids:
				name_special_char = ''.join(c for c in item.remarks if c in '!@#$%^~*{}?+/=')
				if name_special_char:
					raise osv.except_osv(_('Warning!'),_('Special Character Not Allowed in Remarks!'))
		return True
	
	def _line_validations(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.name:
			cr.execute(""" select upper(name) from kg_crm_offer where upper(name)  = '%s' and state != 'revised' """ %(rec.name.upper()))
			data = cr.dictfetchall()
			if rec.revision_remarks:
				if len(data) > 2:
					raise osv.except_osv(_('Warning'), _('Offer No. must be unique !!'))
			elif len(data) > 1:
				raise osv.except_osv(_('Warning'), _('Offer No. must be unique !!'))
			else:
				pass
		if rec.line_pump_ids:
			for item in rec.line_pump_ids:
				if item.hsn_no.id:
					print"item.hsn_no.id",item.hsn_no.id
					sql_check = """ select hsn_id from hsn_no_product where hsn_id = %s and pump_id = %s """ %(item.hsn_no.id,item.pump_id.id)
					cr.execute(sql_check)
					data = cr.dictfetchall()
					if not data:
						sql_check_1 = """ select hsn_id from hsn_no_product where hsn_id != %s and pump_id = %s""" %(item.hsn_no.id,item.pump_id.id)
						cr.execute(sql_check_1)
						data_1 = cr.dictfetchall()
						hsn = ''
						for ele in data_1:
							hsn_rec = self.pool.get('kg.hsn.master').browse(cr,uid,ele['hsn_id'])
							hsn = str(hsn_rec.name) + ',' + hsn
						raise osv.except_osv(_('Warning!'),_('You can choose only HSN %s'%(hsn)))
		#~ if rec.is_zero_offer != True:
			#~ if rec.line_pump_ids:
				#~ for item in rec.line_pump_ids:
					#~ if item.cpo_quote_cust == 'quoted' and item.net_amount == 0.00:
						#~ raise osv.except_osv(_('Warning!'),_('Pump %s Kindly verify quoted price is zero!'%(item.pump_id.name)))
			#~ if rec.line_spare_ids:
				#~ for item in rec.line_spare_ids:
					#~ if item.cpo_quote_cust == 'quoted' and item.net_amount == 0.00:
						#~ raise osv.except_osv(_('Warning!'),_('Sapre %s %s Kindly verify quoted price is zero!'%(item.pump_id.name,item.item_name)))
			#~ if rec.line_accessories_ids:
				#~ for item in rec.line_accessories_ids:
					#~ if item.cpo_quote_cust == 'quoted' and item.net_amount == 0.00:
						#~ raise osv.except_osv(_('Warning!'),_('Accessories %s %s Kindly verify quoted price is zero!'%(item.pump_id.name,item.access_id.name)))
		return True
	
	def _exceed_discount(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.customer_id:
			if rec.o_customer_discount:
				if rec.o_customer_discount > rec.customer_id.max_cust_discount:
					raise osv.except_osv(_('Warning!'),_('Customer discount is more than maximum limit configured'))
			if rec.o_special_discount:
				if rec.o_special_discount > rec.customer_id.max_spl_discount:
					raise osv.except_osv(_('Warning!'),_('Special discount is more than maximum limit configured'))
			if rec.line_pump_ids:
				for item in rec.line_pump_ids:
					if item.customer_discount > rec.customer_id.max_cust_discount:
						raise osv.except_osv(_('Warning!'),
							_('%s Customer discount is more than maximum limit configured'%(item.pump_id.name)))
					if item.special_discount > rec.customer_id.max_spl_discount:
						raise osv.except_osv(_('Warning!'),
							_('%s Special discount is more than maximum limit configured'%(item.pump_id.name)))
			if rec.line_spare_ids:
				for item in rec.line_spare_ids:
					if item.customer_discount > rec.customer_id.max_cust_discount:
						raise osv.except_osv(_('Warning!'),
							_('%s - %s spare customer discount is more than maximum limit configured'%(item.pump_id.name,item.item_name)))
					if item.special_discount > rec.customer_id.max_spl_discount:
						raise osv.except_osv(_('Warning!'),
							_('%s - %s spare special discount is more than maximum limit configured'%(item.pump_id.name,item.item_name)))
			if rec.line_accessories_ids:
				for item in rec.line_accessories_ids:
					if item.customer_discount > rec.customer_id.max_cust_discount:
						raise osv.except_osv(_('Warning!'),
							_('%s customer discount is more than maximum limit configured'%(item.access_id.name)))
					if item.special_discount > rec.customer_id.max_spl_discount:
						raise osv.except_osv(_('Warning!'),
							_('%s special discount is more than maximum limit configured'%(item.access_id.name)))
			if rec.line_supervision_ids:
				for item in rec.line_supervision_ids:
					if item.customer_discount > rec.customer_id.max_cust_discount:
						raise osv.except_osv(_('Warning!'),_('Supervision customer discount is more than maximum limit configured'))
					if item.special_discount > rec.customer_id.max_spl_discount:
						raise osv.except_osv(_('Warning!'),_('Supervision special discount is more than maximum limit configured'))
		if rec.dealer_id:
			if rec.o_dealer_discount:
				if rec.o_dealer_discount > rec.dealer_id.max_deal_discount:
					raise osv.except_osv(_('Warning!'),_('Dealer discount is more than maximum limit configured'))
			if rec.line_pump_ids:
				for item in rec.line_pump_ids:
					if item.dealer_discount > rec.dealer_id.max_deal_discount:
						raise osv.except_osv(_('Warning!'),
							_('%s Dealer discount is more than maximum limit configured'%(item.pump_id.name)))
			if rec.line_spare_ids:
				for item in rec.line_spare_ids:
					if item.dealer_discount > rec.dealer_id.max_deal_discount:
						raise osv.except_osv(_('Warning!'),
							_('%s - %s dealer discount is more than maximum limit configured'%(item.pump_id.name,item.item_name)))
			if rec.line_accessories_ids:
				for item in rec.line_accessories_ids:
					if item.dealer_discount > rec.dealer_id.max_deal_discount:
						raise osv.except_osv(_('Warning!'),
							_('%s dealer discount is more than maximum limit configured'%(item.access_id.name)))
			if rec.line_supervision_ids:
				for item in rec.line_supervision_ids:
					if item.dealer_discount > rec.dealer_id.max_deal_discount:
						raise osv.except_osv(_('Warning!'),_('Supervision dealer discount is more than maximum limit configured'))
		return True
	
	_constraints = [
		(_supervision, 'Supervision more than one not allowed!', ['']),
		(_line_validations, 'Kindly check Line details!', ['']),
		#~ (_exceed_discount, 'Discount more than confirgured not allowed!', ['']),
		]
	
	def onchange_delaer_discount(self, cr, uid, ids, o_dealer_discount):
		value = {'r_o_dealer_discount':0}
		if o_dealer_discount:
			value = {'r_o_dealer_discount': o_dealer_discount}
		return {'value': value}
	
	def onchange_special_discount(self, cr, uid, ids, o_special_discount):
		value = {'r_o_special_discount':0}
		if o_special_discount:
			value = {'r_o_special_discount': o_special_discount}
		return {'value': value}
	
	def onchange_p_f(self, cr, uid, ids, o_p_f, o_p_f_in_ex):
		value = {'r_o_p_f':0,'r_o_p_f_in_ex':''}
		if o_p_f and o_p_f_in_ex:
			value = {'r_o_p_f': o_p_f,'r_o_p_f_in_ex': o_p_f_in_ex}
		return {'value': value}
	
	def onchange_freight(self, cr, uid, ids, o_freight, o_freight_in_ex):
		value = {'r_o_freight':0,'r_o_freight_in_ex':''}
		if o_freight and o_freight_in_ex:
			value = {'r_o_freight': o_freight,'r_o_freight_in_ex': o_freight_in_ex}
		return {'value': value}
	
	def onchange_insurance(self, cr, uid, ids, o_insurance, o_insurance_in_ex):
		value = {'r_o_insurance':0,'r_o_insurance_in_ex':''}
		if o_insurance and o_insurance_in_ex:
			value = {'r_o_insurance': o_insurance,'r_o_insurance_in_ex': o_insurance_in_ex}
		return {'value': value}
	
	def get_offer_reminder_data(self,cr,uid,ids,context=None):
		off_data = []
		cr.execute("""select
					(case when enq.name is not null then enq.name else ' ' end) as enq_no,
					(case when offer.name is not null then offer.name else ' ' end) as offer_no,
					cust.name as customer,
					to_char(offer.reminder_date, 'dd/mm/yyyy') as reminder_date

					from kg_crm_offer offer

					left join kg_crm_enquiry enq on(enq.id=offer.enquiry_id)
					left join res_partner cust on(cust.id=offer.customer_id)
					where offer.reminder_date = current_date and offer.off_status = 'to_be_follow' """)
		off_data = cr.fetchall();
		print"off_dataoff_data",off_data
		return off_data
	
	def send_by_email(self, cr, uid, ids, context=None):
		'''
		This function opens a window to compose an email, with the edi purchase template message loaded by default
		'''
		ir_model_data = self.pool.get('ir.model.data')
		try:
			template_id = ir_model_data.get_object_reference(cr, uid, 'purchase', 'email_template_edi_purchase')[1]
		except ValueError:
			template_id = False
		try:
			compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
		except ValueError:
			compose_form_id = False 
		ctx = dict(context)
		print"template_idtemplate_id",template_id,type(template_id)
		print"compose_form_idcompose_form_id",compose_form_id
		
		ctx.update({
			'default_model': 'kg.crm.offer',
			'default_res_id': ids[0],
			'default_use_template': bool(8),
			'default_template_id': 8,
			'default_composition_mode': 'comment',
		})
		return {
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'mail.compose.message',
			'views': [(compose_form_id, 'form')],
			'view_id': compose_form_id,
			'target': 'new',
			'context': ctx,
		}
	
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []	 
		for rec in self.browse(cr,uid,ids): 
			if rec.state != 'draft':			
				raise osv.except_osv(_('Warning!'),_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_crm_offer, self).write(cr, uid, ids, vals, context)
	
	def update_percentage(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state in ('draft','moved_to_offer'):
			#~ if entry.o_sam_ratio > 0 or entry.o_dealer_discount > 0 or entry.o_special_discount > 0 or entry.o_p_f > 0 or entry.o_freight > 0 or entry.o_insurance > 0 or entry.o_customer_discount > 0:
			print"entry.pump_per_flag",entry.pump_per_flag
			if entry.pump_per_flag == True:
				if entry.line_pump_ids:
					obj = self.pool.get('ch.pump.offer')
					line_ids = entry.line_pump_ids
					self.update_to_all(cr,uid,entry,obj,line_ids)
			if entry.spare_per_flag == True:
				if entry.line_spare_ids:
					obj = self.pool.get('ch.spare.offer')
					line_ids = entry.line_spare_ids
					self.update_to_all(cr,uid,entry,obj,line_ids)
			if entry.access_per_flag == True:
				if entry.line_accessories_ids:
					obj = self.pool.get('ch.accessories.offer')
					line_ids = entry.line_accessories_ids
					self.update_to_all(cr,uid,entry,obj,line_ids)
			self.write(cr,uid,ids,{'dummy_flag':True})
		return True
	
	def update_to_all(self,cr,uid,entry,obj,line_ids,context=None):
		for item in line_ids:
			if entry.o_sam_ratio:
				sam_ratio_flag = True
			else:
				sam_ratio_flag = False
			obj.write(cr,uid,item.id,{'sam_ratio':entry.o_sam_ratio,
									  'sam_ratio_flag':sam_ratio_flag,
									  'works_value':entry.o_sam_ratio*item.prime_cost,
									  'dealer_discount':entry.o_dealer_discount,
									  'special_discount':entry.o_special_discount,
									  'p_f':entry.o_p_f,
									  'p_f_in_ex':entry.o_p_f_in_ex,
									  'freight':entry.o_freight,
									  'freight_in_ex':entry.o_freight_in_ex,
									  'insurance':entry.o_insurance,
									  'agent_com':entry.o_agent_com,
									  'insurance_in_ex':entry.o_insurance_in_ex,
									  'tax_in_ex':entry.o_tax_in_ex,
									  'ed_in_ex':entry.o_ed_in_ex,
									  'customer_discount':entry.o_customer_discount,
									  'tax':entry.o_tax,
									  'ed':entry.o_ed,
									  
									  'r_dealer_discount':entry.r_o_dealer_discount,
									  'r_special_discount':entry.r_o_special_discount,
									  'r_p_f':entry.r_o_p_f,
									  'r_p_f_in_ex':entry.r_o_p_f_in_ex,
									  'r_freight':entry.r_o_freight,
									  'r_freight_in_ex':entry.r_o_freight_in_ex,
									  'r_insurance':entry.r_o_insurance,
									  'r_insurance_in_ex':entry.r_o_insurance_in_ex,
									  'r_customer_discount':entry.r_o_customer_discount,
									  'r_cust':entry.r_o_cust_in_ex,
									  
									  })
		return True
	
	def entry_confirm(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'draft':
			#~ if entry.is_zero_offer == True:
				#~ pass
			#~ else:
				#~ if entry.dummy_flag != True:
					#~ raise osv.except_osv(_('Warning'),_('Kindly update values for Ratio,Discount'))
			#~ for line in entry.line_pump_ids:
			#~ if not entry.name:
				#~ off_no = ''	
				#~ seq_id = self.pool.get('ir.sequence').search(cr,uid,[('code','=','kg.crm.offer')])
				#~ rec = self.pool.get('ir.sequence').browse(cr,uid,seq_id[0])
				#~ cr.execute("""select generatesequenceno(%s,'%s','%s') """%(seq_id[0],rec.code,entry.offer_date))
				#~ off_no = cr.fetchone();
				#~ off_no = off_no[0]
			#~ else:
			off_no = entry.name
			#~ self.wo_creation(cr,uid,entry)
			
			self.write(cr, uid, ids, {
										'name':off_no,
										'state': 'moved_to_offer',
										'confirm_user_id': uid, 
										'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')
									})
		return True
	
	def entry_wfa_md(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'moved_to_offer':
			self.write(cr, uid, ids, {'state': 'wfa_md'})
		return True
	
	def entry_approved_md(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'wfa_md':
			user_obj = self.pool.get('res.users').search(cr,uid,[('id','=',uid)])
			if user_obj:
				user_rec = self.pool.get('res.users').browse(cr,uid,user_obj[0])
				if user_rec.special_approval == True:
					self.write(cr, uid, ids, {'state': 'approved_md','md_approved_date':time.strftime('%Y-%m-%d')})
				else:
					raise osv.except_osv(_('Warning'),_('It should be approved by special approver'))
		return True
	
	def entry_reject_md(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state == 'wfa_md':
			self.write(cr, uid, ids, {'state': 'draft'})
		return True
	
	def entry_revision(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state in ('moved_to_offer','wo_created'):
			revision = 0
			print"entry.is_zero_offer",entry.is_zero_offer
			if entry.is_zero_offer != True:
				wo_obj = self.pool.get('kg.work.order')
				#~ wo_id = wo_obj.search(cr,uid,[('offer_id','=',entry.id),('state','not in',('draft','cancel'))])
				wo_id = wo_obj.search(cr,uid,[('offer_no','=',entry.name),('state','not in',('draft','cancel'))])
				if wo_id:
					raise osv.except_osv(_('Warning!'),_('You can not delete this entry because WO confirmed!'))
			
			if entry.wo_flag == False:
				revision = entry.revision + 1
				print"revisionrevisionrevisionaaaaaaaa",revision
				vals = {
						'state' : 'draft',
						'revision' : revision,
						'revision_remarks' : '',
						}
				offer_id = self.copy(cr,uid,entry.id,vals,context) 
				print"offer_idoffer_idoffer_id",offer_id
				self.write(cr, uid, ids, {
										  'state': 'revised',
										})
			if entry.wo_flag == True and entry.is_zero_offer == True:
				revision = entry.revision + 1
				print"revisionrevisionrevisionbbbbbbbbbbb",revision
				vals = {
						'state' : 'draft',
						'revision' : revision,
						'revision_remarks' : '',
						}
				offer_id = self.copy(cr,uid,entry.id,vals,context) 
				print"offer_idoffer_idoffer_id",offer_id
				
				self.write(cr, uid, ids, {
										  'state': 'revised',
										})
		return True
	
	def wo_creation(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.state in ('moved_to_offer','approved_md') and entry.revision == 0 and entry.purpose not in ('in_development'):
			if not entry.customer_po_no:
				raise osv.except_osv(_('Warning!'),_('Update Customer PO No.'))
			if entry.ref_mode == 'dealer':
				if not entry.dealer_po_no:
					raise osv.except_osv(_('Warning!'),_('Update Dealer PO No.'))
			
			wo_id = self.pool.get('kg.work.order').create(cr,uid,{'order_category': entry.purpose,
																  'name': '',
																  'order_priority': '',
																  'enquiry_no': entry.enquiry_id.name,
																  'offer_no': entry.name,
																  'project_name': entry.prj_name,
																  'division_id': entry.division_id.id,
																  'dealer_id': entry.dealer_id.id,
																  #~ 'location': entry.location,
																  'entry_mode': 'auto',
																  'partner_id': entry.customer_id.id,
																  'order_value': entry.offer_net_amount,
																  'excise_duty': entry.excise_duty,
																  'drawing_approval': entry.drawing_approval,
																  'road_permit': entry.road_permit,
																  'inspection': entry.inspection,
																  'l_d_clause': entry.l_d_clause,
																  'flag_data_bank': entry.flag_data_bank,
																	})
			print"wo_idwo_id",wo_id
			if wo_id:
				if entry.line_pump_ids:
					groups = []
					#~ for item in entry.line_spare_ids:
					for key, group in groupby(entry.line_pump_ids, lambda x: x.enquiry_line_id.id):
						groups.append(map(lambda r:r,group))
					for key,group in enumerate(groups):
						enquiry_line_id = group[0].enquiry_line_id.id
						off_line_id = group[0]
						print"enquiry_line_idenquiry_line_id",enquiry_line_id
						print"off_line_idoff_line_id",off_line_id
						purpose = 'pump'
						if group[0].enquiry_line_id.purpose_categ not in ('in_development'):
							pump_vals = self._prepare_pump_details(cr,uid,wo_id,entry,enquiry_line_id,off_line_id,purpose)
							if pump_vals:
								wo_line_id = self.pool.get('ch.work.order.details').create(cr, uid, pump_vals, context=context)
								self.pool.get('ch.pump.offer').write(cr,uid,off_line_id.id,{'wo_line_id':wo_line_id})
								if wo_line_id:
									item = self.pool.get('ch.kg.crm.pumpmodel').browse(cr,uid,enquiry_line_id)
									if item:
										self.prepare_bom(cr,uid,wo_line_id,item,off_line_id,purpose,context=context)
										## Accessories creation
										acc_off_obj = self.pool.get('ch.accessories.offer').search(cr,uid,[('enquiry_line_id','=',enquiry_line_id)])
										for li in acc_off_obj:
											off_line_id = acc_off_obj
										purpose='access'
										self.prepare_bom(cr,uid,wo_line_id,item,off_line_id,purpose,context=context)
				
				if entry.line_spare_ids:
					groups = []
					#~ for item in entry.line_spare_ids:
					for key, group in groupby(entry.line_spare_ids, lambda x: x.enquiry_line_id.id):
						groups.append(map(lambda r:r,group))
					for key,group in enumerate(groups):
						enquiry_line_id = group[0].enquiry_line_id.id
						off_line_id = group[0]
						spa_off_obj = self.pool.get('ch.spare.offer').search(cr,uid,[('enquiry_line_id','=',enquiry_line_id)])
						print"spa_off_obj",spa_off_obj
						print"enquiry_line_idenquiry_line_id*************************",enquiry_line_id
						print"enquiry_line_idenquiry_line_id********off_line_id*****************",off_line_id
						purpose = 'spare'
						pump_vals = self._prepare_pump_details(cr,uid,wo_id,entry,enquiry_line_id,off_line_id,purpose)
						if pump_vals:
							wo_line_id = self.pool.get('ch.work.order.details').create(cr, uid, pump_vals, context=context)
							self.pool.get('ch.spare.offer').write(cr,uid,off_line_id.id,{'wo_line_id':wo_line_id})
							if wo_line_id:
								item = self.pool.get('ch.kg.crm.pumpmodel').browse(cr,uid,enquiry_line_id)
								if item:
									for li in spa_off_obj:
										print"liliii",li
										off_line_id = spa_off_obj
									self.prepare_bom(cr,uid,wo_line_id,item,off_line_id,purpose,context=context)
									## Accessories creation
									acc_off_obj = self.pool.get('ch.accessories.offer').search(cr,uid,[('enquiry_line_id','=',enquiry_line_id)])
									for li in acc_off_obj:
										off_line_id = acc_off_obj
									purpose='access'
									self.prepare_bom(cr,uid,wo_line_id,item,off_line_id,purpose,context=context)
								
								## Spare BOM creation start
									
								if group[0].enquiry_line_id.line_ids_spare_bom:
									print"aaaaaaaaaaaaaaaaaaaaaa"
									self.prepare_spare_bom(cr,uid,wo_line_id,item,off_line_id,purpose,context=context)
				
				if entry.line_accessories_ids:
					groups = []
					for key, group in groupby(entry.line_accessories_ids, lambda x: x.enquiry_line_id.id):
						groups.append(map(lambda r:r,group))
					print"ffffffffffffffffffff",groups
					for key,group in enumerate(groups):
						access_data = [x for x in group if x.enquiry_line_id.purpose_categ == 'access']
						print"access_dataaccess_dataaccess_data",access_data
						for ch_acc in access_data:
							enquiry_line_id = ch_acc.enquiry_line_id.id
							print"enquiry_line_idenquiry_line_id",enquiry_line_id
							#~ if group[0].enquiry_line_id.purpose_categ == 'access':
							off_line_id = group[0]
							acc_off_obj = self.pool.get('ch.accessories.offer').search(cr,uid,[('enquiry_line_id','=',enquiry_line_id)])
							purpose = 'access'
							pump_vals = self._prepare_pump_details(cr,uid,wo_id,entry,enquiry_line_id,off_line_id,purpose)
							if pump_vals:
								wo_line_id = self.pool.get('ch.work.order.details').create(cr, uid, pump_vals, context=context)
								if wo_line_id:
									item = self.pool.get('ch.kg.crm.pumpmodel').browse(cr,uid,enquiry_line_id)
									if item:
										for li in acc_off_obj:
											print"liliii",li
											off_line_id = acc_off_obj
										self.prepare_bom(cr,uid,wo_line_id,item,off_line_id,purpose,context=context)
						
			print"wo_idwo_idwo_id",wo_id
			if wo_id:
				self.write(cr, uid, ids, {'wo_flag': True,'state':'wo_created'})
				self.pool.get('kg.crm.enquiry').write(cr,uid,entry.enquiry_id.id,{'wo_flag':True,'state':'wo_created'})
		
		if entry.state in ('moved_to_offer','approved_md') and entry.revision > 0:
			wo_obj = self.pool.get('kg.work.order')
			wo_ids = wo_obj.search(cr,uid,[('offer_no','=',entry.name),('state','!=','cancel')])
			if wo_ids:
				wo_rec = wo_obj.browse(cr,uid,wo_ids[0])
				wo_id = wo_rec.id
				if entry.line_pump_ids:
					groups = []
					#~ for item in entry.line_spare_ids:
					for key, group in groupby(entry.line_pump_ids, lambda x: x.enquiry_line_id.id):
						groups.append(map(lambda r:r,group))
					for key,group in enumerate(groups):
						enquiry_line_id = group[0].enquiry_line_id.id
						off_line_id = group[0]
						print"enquiry_line_idenquiry_line_id",enquiry_line_id
						print"off_line_idoff_line_id",off_line_id
						wo_line_id = self.pool.get('ch.pump.offer').browse(cr,uid,off_line_id)
						purpose = 'pump'
						
						wo_line_id = off_line_id.wo_line_id.id
						print"wo_line_id",wo_line_id
						print"off_line_id.id",off_line_id.id
						self.pool.get('ch.work.order.details').write(cr,uid,wo_line_id,{'pump_offer_line_id':off_line_id.id})
						#~ if wo_line_id:
							#~ item = self.pool.get('ch.kg.crm.pumpmodel').browse(cr,uid,enquiry_line_id)
							#~ if item:
								#~ self.prepare_bom_revision(cr,uid,wo_line_id,item,off_line_id,purpose,context=context)
				if entry.line_spare_ids:
					groups = []
					for key, group in groupby(entry.line_spare_ids, lambda x: x.pump_id.id):
						groups.append(map(lambda r:r,group))
					for key,group in enumerate(groups):
						enquiry_line_id = group[0].enquiry_line_id.id
						off_line_id = group[0]
						off_ids = self.pool.get('kg.crm.offer').search(cr,uid,[('enquiry_no','=',entry.enquiry_no),('state','!=','revised')])
						off_rec = self.pool.get('kg.crm.offer').browse(cr,uid,off_ids[0])
						spa_off_obj = self.pool.get('ch.spare.offer').search(cr,uid,[('header_id','=',off_rec.id),('enquiry_line_id','=',enquiry_line_id)])
						print"off_line_idoff_line_id++++++++++++++++++++++++",off_line_id.id
						wo_line_id = self.pool.get('ch.spare.offer').browse(cr,uid,off_line_id.id)
						print"wo_line_idwo_line_id",wo_line_id.spare_offer_line_id.id
						
						purpose = 'spare'
						print"off_line_idoff_line_id",off_line_id
						#~ stop
						#~ wo_line_id = off_line_id.wo_line_id.id
						#~ 
						#~ self.pool.get('ch.work.order.details').write(cr,uid,wo_line_id,{'pump_offer_line_id':0})
						if wo_line_id:
							item = self.pool.get('ch.kg.crm.pumpmodel').browse(cr,uid,enquiry_line_id)
							if item:
								for li in spa_off_obj:
									print"liliii",li
									off_line_id = spa_off_obj
								self.prepare_bom_revision(cr,uid,wo_line_id,item,off_line_id,purpose,context=context)
								
			self.write(cr, uid, ids, {'wo_flag': True,'state':'wo_created'})
			self.pool.get('kg.crm.enquiry').write(cr,uid,entry.enquiry_id.id,{'wo_flag':True,'state':'wo_created'})			
		
		return True
	
	def _prepare_pump_details(self,cr,uid,wo_id,entry,enquiry_line_id,off_line_id,purpose,context=None):	
		print"iteiteitieiteitieit",enquiry_line_id
		item = self.pool.get('ch.kg.crm.pumpmodel').browse(cr,uid,enquiry_line_id)
		#~ purpose = item.purpose_categ
		qty = 1
		moc_const_id = m_power = setting_height = works_value = 0
		pump_model_type = speed_in_rpm = rpm = bush_bearing = shaft_sealing = lubrication = lubrication_type = rpm = qap_plan_id = drawing_approval = inspection = ''
		pump_model_type = item.pump_model_type
		suction_spool = item.suction_spool
		works_value = 0
		if item.push_bearing == 'grease_bronze':
			 bush_bearing = 'grease'
		elif item.push_bearing == 'cft':
			 bush_bearing = 'cft_self'
		elif item.push_bearing == 'cut':
			 bush_bearing = 'cut_less_rubber'
		if item.shaft_sealing == 'gld_packing_tiga':
			 shaft_sealing = 'g_p'
		elif item.shaft_sealing == 'mc_seal':
			 shaft_sealing = 'm_s'
		elif item.shaft_sealing == 'dynamic_seal':
			 shaft_sealing = 'd_s'
		elif item.shaft_sealing == 'f_s':
			 shaft_sealing = 'f_s'
		if item.lubrication_type == 'grease':
			 lubrication_type = 'grease'
		if item.bush_bearing_lubrication == 'grease':
			 lubrication = 'grease'
		elif item.bush_bearing_lubrication == 'external':
			 lubrication = 'cft_ext'
		elif item.bush_bearing_lubrication == 'self':
			 lubrication = 'cft_self'
		elif item.bush_bearing_lubrication == 'ex_pressure':
			 lubrication = 'cut_less_rubber'
		if item.rpm:
			rpm = item.rpm
		setting_height = item.setting_height
		if purpose == 'pump':
			qty = item.qty
			moc_const_id = item.moc_const_id.id
			drawing_approval = off_line_id.drawing_approval
			inspection = off_line_id.inspection
			m_power = item.motor_kw
			qap_plan_id = item.qap_plan_id.id
		elif purpose == 'spare':
			purpose == 'spare'
			moc_const_id = item.moc_const_id.id
			qap_plan_id = item.qap_plan_id.id
			drawing_approval = entry.drawing_approval
			inspection = entry.inspection
		elif purpose == 'access':
			purpose == 'access'
			if item.purpose_categ == 'pump':
				moc_const_id = item.moc_const_id.id
			elif item.purpose_categ in ('spare','access'):
				moc_const_id = item.moc_const_id.id
		pump_id = item.pump_id.id
		pump_off_ids = self.pool.get('ch.pump.offer').search(cr,uid,[('enquiry_line_id','=',enquiry_line_id)])
		if pump_off_ids:
			for ele in pump_off_ids:
				pump_off_rec = self.pool.get('ch.pump.offer').browse(cr,uid,ele)
				wrk_val = pump_off_rec.r_sam_ratio_tot
				works_value += wrk_val
		spare_off_ids = self.pool.get('ch.spare.offer').search(cr,uid,[('enquiry_line_id','=',enquiry_line_id)])
		if spare_off_ids:
			for ele in spare_off_ids:
				spare_off_rec = self.pool.get('ch.spare.offer').browse(cr,uid,ele)
				wrk_val = spare_off_rec.r_sam_ratio_tot
				works_value += wrk_val
		access_off_ids = self.pool.get('ch.accessories.offer').search(cr,uid,[('enquiry_line_id','=',enquiry_line_id)])
		if access_off_ids:
			for ele in access_off_ids:
				access_off_rec = self.pool.get('ch.accessories.offer').browse(cr,uid,ele)
				wrk_val = access_off_rec.r_sam_ratio_tot
				works_value += wrk_val
		
		pump_vals = {
			
			'header_id': wo_id,
			'pump_model_id': pump_id,
			'order_summary': item.order_summary,
			'flange_standard': item.flange_standard.id,
			'qap_plan_id': qap_plan_id,
			'order_category': purpose,
			'moc_construction_id': moc_const_id,
			'qty': qty,
			'flag_load_bom': True,
			'delivery_date': item.header_id.del_date,
			'enquiry_line_id': enquiry_line_id,
			'pump_offer_line_id': off_line_id,
			'pump_model_type': pump_model_type,
			'rpm': rpm,
			'bush_bearing': bush_bearing,
			'm_power': m_power,
			'setting_height': setting_height,
			'suction_spool': suction_spool,
			'shaft_sealing': shaft_sealing,
			#~ 'lubrication_type': lubrication_type,
			'lubrication': lubrication,
			'rpm': rpm,
			'flag_offer': True,
			'drawing_approval': drawing_approval,
			'inspection': inspection,
			'delivery_pipe_size': item.del_pipe_size,
			'motor_power': item.motor_power,
			'flag_standard': item.flag_standard,
			'framesize': item.motor_power,
			'pumpseries_id': item.pumpseries_id.id,
			'unit_price': works_value,
			'size_suctionx': item.size_suctionx,
			'consistency': item.consistency,
			}
		
		return pump_vals
	
	def prepare_bom_revision(self,cr,uid,wo_line_id,item,off_line_id,purpose,context=None):
		
		if purpose in ('pump','spare'):
			if item.purpose_categ in ('pump','spare'):
				arr = of_li_id = 0
				if item.line_ids:
					for ele in item.line_ids:
						if ele.is_applicable == True:
							print"ele.position_id.idele.position_id.id",ele.position_id.id
							if purpose == 'spare':
								print"off_line_idoff_line_idoff_line_id0000000000000000",off_line_id
								of_li_id = off_line_id[arr]
								if ele.spare_offer_line_id > 0:
									fou_ids = self.pool.get('ch.order.bom.details').search(cr,uid,[('spare_offer_line_id','=',ele.spare_offer_line_id)])
									print"fou_idsfou_idsfou_ids------------",fou_ids
									if fou_ids:
										fou_rec = self.pool.get('ch.order.bom.details').browse(cr,uid,fou_ids[0])
										print"fou_re///////////////////cfou_rec",fou_rec.id
										self.pool.get('ch.order.bom.details').write(cr,uid,fou_rec.id,{'spare_offer_line_id':of_li_id})
										self.pool.get('ch.kg.crm.foundry.item').write(cr,uid,ele.id,{'spare_offer_line_id':of_li_id})
							arr = arr+1
						else:
							if purpose == 'spare':
								of_li_id = 0
				if item.line_ids_a:
					for ele in item.line_ids_a:
						if ele.is_applicable == True:
							if purpose == 'spare':
								print"off_line_idoff_line_idoff_line_id0000000000000000",off_line_id
								of_li_id = off_line_id[arr]
								if ele.spare_offer_line_id > 0:
									ms_ids = self.pool.get('ch.order.machineshop.details').search(cr,uid,[('spare_offer_line_id','=',ele.spare_offer_line_id)])
									print"ms_idsms_idsms_ids------------",ms_ids
									if ms_ids:
										ms_rec = self.pool.get('ch.order.machineshop.details').browse(cr,uid,ms_ids[0])
										print"ms_rec///////////////////ms_rec",ms_rec.id
										self.pool.get('ch.order.machineshop.details').write(cr,uid,ms_rec.id,{'spare_offer_line_id':of_li_id})
										self.pool.get('ch.kg.crm.machineshop.item').write(cr,uid,ele.id,{'spare_offer_line_id':of_li_id})
							arr = arr+1
						else:
							if purpose == 'spare':
								of_li_id = 0
				if item.line_ids_b:
					for ele in item.line_ids_b:
						if ele.is_applicable == True:
							if purpose == 'spare':
								print"off_line_idoff_line_idoff_line_id0000000000000000",off_line_id
								of_li_id = off_line_id[arr]
								if ele.spare_offer_line_id > 0:
									bot_ids = self.pool.get('ch.order.bot.details').search(cr,uid,[('spare_offer_line_id','=',ele.spare_offer_line_id)])
									print"bot_idsbot_idsbot_ids------------",bot_ids
									if bot_ids:
										bot_rec = self.pool.get('ch.order.bot.details').browse(cr,uid,bot_ids[0])
										print"bot_rec///////////////////bot_rec",bot_rec.id
										self.pool.get('ch.order.bot.details').write(cr,uid,bot_rec.id,{'spare_offer_line_id':of_li_id})
										self.pool.get('ch.kg.crm.bot').write(cr,uid,ele.id,{'spare_offer_line_id':of_li_id})
							arr = arr+1
						else:
							if purpose == 'spare':
								of_li_id = 0
		#~ if purpose == 'access':
			#~ prime_cost = 0
			#~ print"ddddddddddddddddddddddddddddD",prime_cost
			#~ if item.acces == 'yes':
				#~ arr = of_li_id = 0
				#~ if item.line_ids_access_a:
					#~ for line in item.line_ids_access_a:
						#~ of_li_id = off_line_id[arr]
						#~ print"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",of_li_id
						#~ wo_access_id = self.pool.get('ch.wo.accessories').create(cr,uid,{'header_id':wo_line_id,
																						 #~ 'access_id':line.access_id.id,
																						 #~ 'moc_id':line.moc_id.id,
																						 #~ 'qty':line.qty,
																						 #~ 'load_access':line.load_access,
																						 #~ 'access_offer_line_id': of_li_id,
																						#~ })
						#~ arr = arr+1
						#~ if wo_access_id:
							#~ if line.line_ids:
								#~ for ele in line.line_ids:
									#~ if ele.is_applicable == True:
										#~ fou_line = self.pool.get('ch.wo.accessories.foundry').create(cr,uid,{'header_id': wo_access_id,
																										#~ 'is_applicable': True,
																										#~ 'qty': ele.qty,
																										#~ 'position_id': ele.position_id.id,
																										#~ 'pattern_id': ele.pattern_id.id,
																										#~ 'material_code': ele.material_code,
																										#~ 'prime_cost': ele.prime_cost,
																										#~ 'moc_id': ele.moc_id.id,
																										#~ 'access_offer_line_id': off_line_id,
																										#~ })
										#~ prime_cost += ele.prime_cost
							#~ if line.line_ids_a:
								#~ for ele in line.line_ids_a:
									#~ if ele.is_applicable == True:
										#~ fou_line = self.pool.get('ch.wo.accessories.ms').create(cr,uid,{'header_id': wo_access_id,
																										#~ 'is_applicable': True,
																										#~ 'qty': ele.qty,
																										#~ 'indent_qty': ele.qty,
																										#~ 'position_id': ele.position_id.id,
																										#~ 'position_id': ele.material_code,
																										#~ 'ms_id': ele.ms_id.id,
																										#~ 'prime_cost': ele.prime_cost,
																										#~ 'moc_id': ele.moc_id.id,
																										#~ 'access_offer_line_id': off_line_id,
																										#~ })
										#~ prime_cost += ele.prime_cost
							#~ if line.line_ids_b:
								#~ for ele in line.line_ids_b:
									#~ if ele.is_applicable == True:
										#~ fou_line = self.pool.get('ch.wo.accessories.bot').create(cr,uid,{'header_id': wo_access_id,
																										#~ 'is_applicable': True,
																										#~ 'qty': ele.qty,
																										#~ 'position_id': ele.position_id.id,
																										#~ 'position_id': ele.material_code,
																										#~ 'csd_no': ele.csd_no,
																										#~ 'ms_id': ele.ms_id.id,
																										#~ 'prime_cost': ele.prime_cost,
																										#~ 'moc_id': ele.moc_id.id,
																										#~ 'access_offer_line_id': off_line_id,
																										#~ })
										#~ prime_cost += ele.prime_cost
							#~ self.pool.get('ch.wo.accessories').write(cr,uid,wo_access_id,{'mar_prime_cost':prime_cost})
							#~ prime_cost = 0.00
							#~ off_access_obj = self.pool.get('ch.accessories.offer').search(cr,uid,[('enquiry_line_id','=',item.id),('pump_id','=',item.pump_id.id)])
							#~ if off_access_obj:
								#~ print"off_access_obj",off_access_obj
								#~ for line in off_access_obj:
									#~ print"linelelelelelle",line
									#~ off_access_rec = self.pool.get('ch.accessories.offer').browse(cr,uid,line)
									#~ prime_cost += off_access_rec.net_amount
								#~ print"*************************************************",prime_cost
								#~ self.pool.get('ch.work.order.details').write(cr,uid,wo_line_id,{'unit_price':prime_cost})
		
		return True
	
	def prepare_spare_bom(self,cr,uid,wo_line_id,item,off_line_id,purpose,context=None):
		
		if item.line_ids_spare_bom:
			for ele in item.line_ids_spare_bom:
				spare_bom_id = self.pool.get('ch.wo.spare.bom').create(cr,uid,{'header_id': wo_line_id,
																		   'moc_const_id': ele.moc_const_id.id,
																		   'bom_id': ele.bom_id.id,
																		   'qty': ele.qty,
																		   'off_name': ele.off_name,
																		   'load_bom': ele.load_bom,
																		   'prime_cost': ele.prime_cost,
																		})
				if spare_bom_id:
					if ele.line_ids:
						for fou in ele.line_ids:
							spare_fou_id = self.pool.get('ch.wo.spare.foundry').create(cr,uid,{'header_id': spare_bom_id,
																		   'oth_spec': fou.oth_spec,
																		   'position_id': fou.position_id.id,
																		   'qty': fou.qty,
																		   'off_name': fou.off_name,
																		   'csd_no': fou.csd_no,
																		   'pattern_name': fou.pattern_name,
																		   'pattern_id': fou.pattern_id.id,
																		   'is_applicable': fou.is_applicable,
																		   'load_bom': fou.load_bom,
																		   'moc_id': fou.moc_id.id,
																		   'moc_name': fou.moc_name,
																		   'moc_changed_flag': fou.moc_changed_flag,
																		   'prime_cost': fou.prime_cost,
																		   'material_code': fou.material_code,
																		   'flag_pattern_check': fou.flag_pattern_check,
																		   'purpose_categ': fou.purpose_categ,
																		   'spare_offer_line_id': off_line_id,
																		})
					if ele.line_ids_a:
						for fou in ele.line_ids_a:
							spare_ms_id = self.pool.get('ch.wo.spare.ms').create(cr,uid,{'header_id': spare_bom_id,
																		   'position_id': fou.position_id.id,
																		   'qty': fou.qty,
																		   'off_name': fou.off_name,
																		   'bom_id': fou.bom_id.id,
																		   'csd_no': fou.csd_no,
																		   'ms_id': fou.ms_id.id,
																		   'moc_id': fou.moc_id.id,
																		   'is_applicable': fou.is_applicable,
																		   'load_bom': fou.load_bom,
																		   'moc_id': fou.moc_id.id,
																		   'moc_name': fou.moc_name,
																		   'moc_changed_flag': fou.moc_changed_flag,
																		   'prime_cost': fou.prime_cost,
																		   'material_code': fou.material_code,
																		   'purpose_categ': fou.purpose_categ,
																		   'length': fou.length,
																		   'spare_offer_line_id': off_line_id,
																		})
							if spare_ms_id:
								for raw_line in fou.line_ids:
									ms_raw_line_id = self.pool.get('ch.wo.spare.ms.raw').create(cr,uid,{'header_id': spare_ms_id,
																				 'remarks': raw_line.remarks,
																				 'product_id': raw_line.product_id.id,
																				 'uom': raw_line.uom.id,
																				 'od': raw_line.od,
																				 'length': raw_line.length,
																				 'breadth': raw_line.breadth,
																				 'thickness': raw_line.thickness,
																				 'weight': raw_line.weight,
																				 'uom_conversation_factor': raw_line.uom_conversation_factor,
																				 'temp_qty': raw_line.temp_qty,
																				 'qty': raw_line.qty,
																				 })
					if ele.line_ids_b:
						for fou in ele.line_ids_b:
							spare_bot_id = self.pool.get('ch.wo.spare.bot').create(cr,uid,{'header_id': spare_bom_id,
																		   'product_temp_id': fou.product_temp_id.id,
																		   'position_id': fou.position_id.id,
																		   'qty': fou.qty,
																		   'off_name': fou.off_name,
																		   'bom_id': fou.bom_id.id,
																		   'code': fou.code,
																		   'ms_id': fou.ms_id.id,
																		   'moc_id': fou.moc_id.id,
																		   'brand_id': fou.brand_id.id,
																		   'is_applicable': fou.is_applicable,
																		   'load_bom': fou.load_bom,
																		   'flag_is_bearing': fou.flag_is_bearing,
																		   'moc_id': fou.moc_id.id,
																		   'moc_name': fou.moc_name,
																		   'moc_changed_flag': fou.moc_changed_flag,
																		   'prime_cost': fou.prime_cost,
																		   'material_code': fou.material_code,
																		   'purpose_categ': fou.purpose_categ,
																		   'spare_offer_line_id': off_line_id,
																		})
							
		
		
		return True
	
	def prepare_bom(self,cr,uid,wo_line_id,item,off_line_id,purpose,context=None):	
		prime_cost = 0
		if purpose in ('pump','spare'):
			if item.purpose_categ in ('pump','spare'):
				arr = of_li_id = 0
				if item.line_ids:
					#~ spa_off_obj = self.pool.get('ch.spare.offer').search(cr,uid,[('enquiry_line_id','=',enquiry_line_id)])
					#~ print"spa_off_obj",spa_off_obj
					print"off_line_idoff_line_idoff_line_idoff_line_idoff_line_id",off_line_id
					for ele in item.line_ids:
						if ele.is_applicable == True:
							if purpose == 'spare':
								of_li_id = off_line_id[arr]
								print"of_li_id",of_li_id
							print"ele.position_id.idele.position_id.id",ele.position_id.name
							fou_line = self.pool.get('ch.order.bom.details').create(cr,uid,{'header_id': wo_line_id,
																							'flag_applicable': True,
																							'flag_standard': True,
																							'qty': ele.qty,
																							'position_id': ele.position_id.id,
																							'pattern_id': ele.pattern_id.id,
																							'pattern_name': ele.pattern_name,
																							'off_name': ele.off_name,
																							'material_code': ele.material_code,
																							'flag_pattern_check': ele.flag_pattern_check,
																							'unit_price': ele.prime_cost,
																							'mar_prime_cost': ele.prime_cost,
																							'moc_id': ele.moc_id.id,
																							'entry_mode': 'auto',
																							'spare_offer_line_id': of_li_id,
																							})
							self.pool.get('ch.kg.crm.foundry.item').write(cr,uid,ele.id,{'spare_offer_line_id':of_li_id})
							prime_cost += ele.prime_cost
							print"aaaaaaaaaaaaa",prime_cost
							arr = arr+1
						else:
							if purpose == 'spare':
								of_li_id = 0
				if item.line_ids_a:
					for ele in item.line_ids_a:
						if ele.is_applicable == True:
							if purpose == 'spare':
								of_li_id = off_line_id[arr]
								print"of_li_id",of_li_id
							ms_line = self.pool.get('ch.order.machineshop.details').create(cr,uid,{'header_id': wo_line_id,
																							'flag_applicable': True,
																							'flag_standard': True,
																							'qty': ele.qty,
																							'indent_qty': ele.qty,
																							'position_id': ele.position_id.id,
																							'ms_id': ele.ms_id.id,
																							'off_name': ele.off_name,
																							'material_code': ele.material_code,
																							'unit_price': ele.prime_cost,
																							'mar_prime_cost': ele.prime_cost,
																							'moc_id': ele.moc_id.id,
																							'entry_mode': 'auto',
																							'spare_offer_line_id': of_li_id,
																							})
							if ms_line and ele.line_ids:
								for raw_line in ele.line_ids:
									ms_raw_line_id = self.pool.get('ch.wo.ms.raw').create(cr,uid,{'header_id': ms_line,
																				 'remarks': raw_line.remarks,
																				 'product_id': raw_line.product_id.id,
																				 'uom': raw_line.uom.id,
																				 'od': raw_line.od,
																				 'length': raw_line.length,
																				 'breadth': raw_line.breadth,
																				 'thickness': raw_line.thickness,
																				 'weight': raw_line.weight,
																				 'uom_conversation_factor': raw_line.uom_conversation_factor,
																				 'temp_qty': raw_line.temp_qty,
																				 'qty': raw_line.qty,
																				 })
							self.pool.get('ch.kg.crm.machineshop.item').write(cr,uid,ele.id,{'spare_offer_line_id':of_li_id})
							prime_cost += ele.prime_cost
							print"bbbbbbbbbbbbbb",prime_cost
							arr = arr+1
						else:
							if purpose == 'spare':
								of_li_id = 0
				if item.line_ids_b:
					for ele in item.line_ids_b:
						if ele.is_applicable == True:
							if purpose == 'spare':
								of_li_id = off_line_id[arr]
								print"of_li_id",of_li_id
							bot_line = self.pool.get('ch.order.bot.details').create(cr,uid,{'header_id': wo_line_id,
																							'flag_applicable': True,
																							'flag_standard': True,
																							'qty': ele.qty,
																							'position_id': ele.position_id.id,
																							'bot_id': ele.ms_id.id,
																							'off_name': ele.off_name,
																							'material_code': ele.material_code,
																							'unit_price': ele.prime_cost,
																							'mar_prime_cost': ele.prime_cost,
																							'moc_id': ele.moc_id.id,
																							'entry_mode': 'auto',
																							'spare_offer_line_id': of_li_id,
																							'brand_id': ele.brand_id.id,
																							})
							self.pool.get('ch.kg.crm.bot').write(cr,uid,ele.id,{'spare_offer_line_id':of_li_id})
							prime_cost += ele.prime_cost
							print"ccccccccccccccccc",prime_cost
							arr = arr+1
						else:
							if purpose == 'spare':
								of_li_id = 0
				self.pool.get('ch.work.order.details').write(cr,uid,wo_line_id,{'mar_prime_cost':prime_cost})
				prime_cost = 0.00
				#~ if item.purpose_categ == 'pump':
					#~ self.pool.get('ch.work.order.details').write(cr,uid,wo_line_id,{'unit_price':off_line_id.works_val})
				#~ elif item.purpose_categ == 'spare':
					#~ off_spare_obj = self.pool.get('ch.spare.offer').search(cr,uid,[('enquiry_line_id','=',item.id),('pump_id','=',item.pump_id.id)])
					#~ if off_spare_obj:
						#~ print"off_spare_obj",off_spare_obj
						#~ for line in off_spare_obj:
							#~ print"linelelelelelle",line
							#~ off_spare_rec = self.pool.get('ch.spare.offer').browse(cr,uid,line)
							#~ prime_cost += off_spare_rec.works_value
						#~ self.pool.get('ch.work.order.details').write(cr,uid,wo_line_id,{'unit_price':prime_cost})
		if purpose == 'access':
			prime_cost = 0
			print"ddddddddddddddddddddddddddddD",prime_cost
			if item.acces == 'yes':
				arr = of_li_id = 0
				if item.line_ids_access_a:
					for line in item.line_ids_access_a:
						of_li_id = off_line_id[arr]
						print"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",of_li_id
						wo_access_id = self.pool.get('ch.wo.accessories').create(cr,uid,{'header_id':wo_line_id,
																						 'access_id':line.access_id.id,
																						 'off_name':line.off_name,
																						 'moc_const_id':line.moc_const_id.id,
																						 #~ 'moc_id':line.moc_id.id,
																						 'qty':line.qty,
																						 'load_access':line.load_access,
																						 'access_offer_line_id': of_li_id,
																						})
						arr = arr+1
						if wo_access_id:
							if line.line_ids:
								for ele in line.line_ids:
									if ele.is_applicable == True:
										fou_line = self.pool.get('ch.wo.accessories.foundry').create(cr,uid,{'header_id': wo_access_id,
																										'is_applicable': True,
																										'qty': ele.qty,
																										'position_id': ele.position_id.id,
																										'pattern_id': ele.pattern_id.id,
																										'material_code': ele.material_code,
																										'prime_cost': ele.prime_cost,
																										'moc_id': ele.moc_id.id,
																										#~ 'access_offer_line_id': off_line_id,
																										})
										prime_cost += ele.prime_cost
							if line.line_ids_a:
								for ele in line.line_ids_a:
									if ele.is_applicable == True:
										fou_line = self.pool.get('ch.wo.accessories.ms').create(cr,uid,{'header_id': wo_access_id,
																										'is_applicable': True,
																										'qty': ele.qty,
																										'indent_qty': ele.qty,
																										'position_id': ele.position_id.id,
																										'material_code': ele.material_code,
																										'ms_id': ele.ms_id.id,
																										'prime_cost': ele.prime_cost,
																										'moc_id': ele.moc_id.id,
																										#~ 'access_offer_line_id': off_line_id,
																										})
										prime_cost += ele.prime_cost
							if line.line_ids_b:
								for ele in line.line_ids_b:
									if ele.is_applicable == True:
										fou_line = self.pool.get('ch.wo.accessories.bot').create(cr,uid,{'header_id': wo_access_id,
																										'is_applicable': True,
																										'qty': ele.qty,
																										'position_id': ele.position_id.id,
																										'material_code': ele.material_code,
																										'csd_no': ele.csd_no,
																										'ms_id': ele.ms_id.id,
																										'prime_cost': ele.prime_cost,
																										'moc_id': ele.moc_id.id,
																										#~ 'access_offer_line_id': off_line_id,
																										})
										prime_cost += ele.prime_cost
							self.pool.get('ch.wo.accessories').write(cr,uid,wo_access_id,{'mar_prime_cost':prime_cost})
							prime_cost = 0.00
							#~ off_access_obj = self.pool.get('ch.accessories.offer').search(cr,uid,[('enquiry_line_id','=',item.id),('pump_id','=',item.pump_id.id)])
							#~ if off_access_obj:
								#~ print"off_access_obj",off_access_obj
								#~ for line in off_access_obj:
									#~ print"linelelelelelle",line
									#~ off_access_rec = self.pool.get('ch.accessories.offer').browse(cr,uid,line)
									#~ prime_cost += off_access_rec.works_value
								#~ print"*************************************************",prime_cost
								#~ self.pool.get('ch.work.order.details').write(cr,uid,wo_line_id,{'unit_price':prime_cost})
						
		print"prime_costprime_cost",prime_cost
		return True
	
	def offer_copy(self,cr,uid,ids,context=None):
		import StringIO
		import base64
		import string
		try:
			import xlwt
		except:
		   raise osv.except_osv('Warning !','Please download python xlwt module from\nhttp://pypi.python.org/packages/source/x/xlwt/xlwt-0.7.2.tar.gz\nand install it')
		record={}
		wbk = xlwt.Workbook()
		style_mast_header = xlwt.easyxf('font: height 320;font: bold off;align: wrap on;align: wrap off, vert bottom, horiz center;border: top thin, bottom thin, left thin, right thin;')
		style_header1 = xlwt.easyxf('font: bold on,height 200;align: wrap off, vert bottom, horiz center;border: top thin, bottom thin, left thin, right thin;')
		style_center = xlwt.easyxf('font: height 180,name Calibri;align: wrap off, vert bottom, horiz center;border: top thin, bottom thin, left thin, right thin;')		
		style_left_header = xlwt.easyxf('font: bold on,height 220,color_index 0X36;align: wrap off, vert center, horiz left;border: top thin, bottom thin, left thin, right thin;')			
		style_left = xlwt.easyxf('font: height 180,name Calibri;align: wrap off, vert bottom, horiz left;border: top thin, bottom thin, left thin, right thin;')		
		style_sub_left = xlwt.easyxf('font: height 180,underline on,bold on,name Calibri;align: wrap off, vert bottom, horiz left;border: top thin, bottom thin, left thin, right thin;')		
		style_highlight = xlwt.easyxf('font: height 180,bold on,name Calibri,color_index black;align: wrap off, vert bottom, horiz left;border: top thin, bottom thin, left thin, right thin;')		
		style1 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz center;''borders: left thin, right thin, top thin, bottom thin')
		style2 = xlwt.easyxf('font: height 200,color_index black;' 'align: horiz right;''borders: left thin, right thin, top thin, bottom thin')
		style3 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz right;''borders: left thin, right thin, top thin, bottom thin')
		style41 = xlwt.easyxf('font: height 200,bold on,color_index black;' 'align: horiz center;''borders: left thin, right thin, top thin, bottom thin')		
		style4 = xlwt.easyxf('font: height 200,color_index black;' 'align: horiz center;''borders: left thin, right thin, top thin, bottom thin')
		cmp_obj = self.pool.get('res.company')
		rec =self.browse(cr,uid,ids[0])
		enq_ids = self.pool.get('kg.crm.enquiry').search(cr,uid,[('name','=',rec.enquiry_no),('state','!=','revised')])
		if enq_ids:
			enq_rec = self.pool.get('kg.crm.enquiry').browse(cr,uid,enq_ids[0])
		else:
			raise osv.except_osv(_('Warning!'),_('You cannot get offer copy'))
		pass_id = enq_ids
		pass_param = '(' +",".join([str(s) for s in list(pass_id)])+ ')'
		rpt_type = ['horizontal','vertical','others']
		hz_dictn = {
		'01#Item Details:':[('Equipment No','item_eqno'),('Description','item_desc'),('Quantity in No','item_qty')],
		'02#Liquid Specifications:': [('Liquid Handled','lspec_lqd'),('Temperature in C','lspec_temp'),('Specific Gravity - Liquid','lspec_sgvt'),('PH value','lspec_ph'),('Viscosity in cp/cst','lspec_viscst'),('Viscosity correction factors - kq/kh/kn ','lspec_visfact'),('Solid Concentration in % /Max Size-mm','lspec_solid'),('Slurry Correction in - kq/kh/kn ','lspec_slur'),('Suction Condition','lspec_suct')],
		'03#Duty Parameters:':[('Capacity in M3/hr','duty_cap'),('Head in Mtr','duty_water_head')],
		'04#Pump Specification:':[('Pump Type','pump_pmodtype'), ('Pump Model','pump_pmodel'), ('Number of stages','pump_stgno'), ('Size-SuctionX Delivery- in mm','pump_sizex'), ('Flange Standard','pump_flange'), ('Efficiency in % Wat/Liq','pump_eff'), ('BKW  Water	 ','pump_water_bkw'),('BKW  Liquid   ','pump_liquid_bkw'), ('End of the curve - KW(Rated)','pump_eoc'), ('Motor KW ','pump_motor_kw'), ('Speed in RPM- Motor','pump_rpm_motor'),('Speed in RPM- Pump','pump_rpm_pump'), ('Type of Drive','pump_tod'), ('NPSH R - M','pump_npsh'), ('Impeller Type','pump_impeller_type'), ('Impeller Dia Rated / Max / Min - mm','pump_impeller_dia'), ('Maximum Allowable Soild Size - MM','pump_max_solid'), ('Hydrostatic Test Pressure - Kg/cm2','pump_hydro'), ('Shut off Head in M','pump_shut'), ('Minimum Contionuous Flow - M3/hr','pump_mini'), ('Impeller Tip Speed -M/Sec','pump_impeller_tip'), ('Sealing Water Requirement-Pressure','pump_seal_press'), ('Sealing Water Capcity- m3/hr','pump_seal_cap')],
		'05#Material of Construction: ':[('Purpose','purp_categ')],
		'06#Mechanical Seal: Make: Eagle / Flowserve / Leak Proof / Hifab: ':[('Type / Face combination','mech_type_face'),('Gland Plate / API Plan','mech_gld_api')],
		'07#Motor: Make: KEC / ABB / CGL :':[('Type / Mounting','mot_type_mount'),('Insulation / Protection','mot_ins_prot'),('Voltage / Phase / Frequency','mot_volt_ph_frq')],
		'08#Scope of Supply / Price per each in Rs:':[('Bare Pump','bare_pump'),('All Accessories','acces'),('Spares','spare')]
		}
		vz_dictn = {
		'01#Item Details:':[('Equipment No','item_eqno'),('Description','item_desc'),('Quantity in No','item_qty')],
		'02#Liquid Specifications:': [('Liquid Handled','lspec_lqd'),('Temperature in C','lspec_temp'),('Specific Gravity ','lspec_sgvt'),('PH value','lspec_ph'),('Viscosity in cp/cst','lspec_viscst'),('Viscosity correction factors - kq/kh/kn ','lspec_visfact'),('Solid Concentration in % /Max Size-mm','lspec_solid'),('Suction Condition','lspec_suct')],
		'03#Duty Parameters:':[('Capacity in M3/hr','duty_cap'),('Head in Mtr','duty_water_head'),('Suction Condition','duty_suct')],
		'04#Pump Specification:':[('Pump Type','pump_pmodtype'), ('Pump Model','pump_pmodel'), ('Number of stages','pump_stgno'), ('Size-SuctionX Delivery- in mm','pump_sizex'), ('Flange Standard','pump_flange'), ('Efficiency in % Wat/Liq','pump_eff'), ('BKW  Water	 ','pump_water_bkw'),('BKW  Liquid   ','pump_liquid_bkw'), ('End of the curve - KW(Rated)','pump_eoc'), ('Motor KW ','pump_motor_kw'), ('Speed in RPM- Motor','pump_rpm_motor'),('Speed in RPM- Pump','pump_rpm_pump'), ('Type of Drive','pump_tod'), ('NPSH R - M','pump_npsh'), ('Impeller Type','pump_impeller_type'), ('Impeller Dia Rated / Max / Min - mm','pump_impeller_dia'), ('Maximum Allowable Soild Size - MM','pump_max_solid'), ('Hydrostatic Test Pressure - Kg/cm2','pump_hydro'), ('Shut off Head in M','pump_shut'), ('Minimum Contionuous Flow - M3/hr','pump_mini'), ('Setting Height in MM ','pump_setting_height'), ('Sump Depth in MM','pump_sump_depth')],
		'05#Material of Construction: ':[('Purpose','purp_categ')],
		'06#Mechanical Seal: Make: Eagle / Flowserve / Leak Proof / Hifab: ':[('Type / Face combination','mech_type_face'),('Gland Plate / API Plan','mech_gld_api')],
		'07#Motor: Make: KEC / ABB / CGL :':[('Type / Mounting','mot_type_mount'),('Insulation / Protection','mot_ins_prot'),('Voltage / Phase / Frequency','mot_volt_ph_frq')],
		'08#Scope of Supply / Price per each in Rs:':[('Bare Pump','bare_pump'),('All Accessories','acces'),('Spares','spare')]
		}
		self_obj = self.pool.get('ch.kg.crm.pumpmodel')
		sqltwo = """ select 
		coalesce(item_eqno,'-') as item_eqno,coalesce(item_desc,'-') as item_desc,coalesce(item_qty,0) as item_qty,
		coalesce(lspec_lqd,'-') as lspec_lqd,coalesce(lspec_temp,'-') as lspec_temp,coalesce(lspec_sgvt,0) as lspec_sgvt,coalesce(lspec_ph,'-') as lspec_ph,coalesce(lspec_viscst,0) as lspec_viscst,coalesce(lspec_visfact,'-') as lspec_visfact,
		coalesce(lspec_solid,'-') as lspec_solid,
		coalesce(lspec_slur,0) as lspec_slur,
		coalesce(lspec_suct,'-') as lspec_suct,
		coalesce(duty_cap,'-') as duty_cap,coalesce(duty_head,'-') as duty_head,
		duty_water_head,duty_liquid_head,
		coalesce(duty_suct,'-') as duty_suct,coalesce(pump_pmodtype,'-') as pump_pmodtype,
		coalesce(pump_pmodel,'-') as pump_pmodel,coalesce(pump_stgno,0) as pump_stgno,
		coalesce(pump_sizex,'-') as pump_sizex,coalesce(pump_flange,'-') as pump_flange,
		coalesce(pump_eff,0) as pump_eff,

		coalesce(pump_water_bkw,'-') as pump_water_bkw, -- Testing
		coalesce(pump_liquid_bkw,'-') as pump_liquid_bkw, -- Testing
		---coalesce(pump_bkw,'-') as pump_bkw,
		
		coalesce(pump_eoc,0) as pump_eoc,coalesce(pump_motor_kw,0) as pump_motor_kw,
		
		coalesce(pump_rpm_pump,'-') as pump_rpm_pump, -- Testing
		coalesce(pump_rpm_motor,'-') as pump_rpm_motor, -- Testing
		
		--- coalesce(pump_speed,'-') as pump_speed,
		
		coalesce(pump_tod1,'-') as pump_tod,
		coalesce(pump_npsh1,0) as pump_npsh,coalesce(pump_impeller_type,'-') as pump_impeller_type,
		coalesce(pump_impeller_dia,'-') as pump_impeller_dia,
		coalesce(pump_max_solid,0) as pump_max_solid,coalesce(pump_hydro,0) as pump_hydro,
		coalesce(pump_shut,0) as pump_shut,coalesce(pump_setting_height,0) as pump_setting_height,
		coalesce(pump_sump_depth,'-') as pump_sump_depth,
		coalesce(pump_mini,0) as pump_mini,coalesce(pump_belt,0) as pump_belt,
		coalesce(pump_motor_kw,0) as pump_motor_kw1,coalesce(pump_speed1,'-') as pump_speed1,
		coalesce(pump_tod1,'-') as pump_tod1,coalesce(pump_impeller_tip,0) as pump_impeller_tip,
		coalesce(pump_seal_press,0) as pump_seal_press,coalesce(pump_seal_cap,0) as pump_seal_cap,
		acces,coalesce(mech_type_face,'-') as mech_type_face,coalesce(mech_gld_api,'-') as mech_gld_api,
		coalesce(mot_type_mount,'-') as mot_type_mount,coalesce(mot_ins_prot,'-') as mot_ins_prot,
		coalesce(mot_volt_ph_frq,'-') as mot_volt_ph_frq,'bare_pump'::text as bare_pump,'spare'::text as spare from (
		select
		item_eqno,item_desc,item_qty,lspec_lqd,lspec_temp,lspec_sgvt,lspec_ph,lspec_viscst,lspec_visfact,
		case when ((solid_concern_vol is not null and solid_concern_vol != '') and 
		(solid_concern is not null and solid_concern != '')) then 
		(solid_concern_vol::text||'$'||solid_concern)
		else ( case when ((solid_concern_vol is not null and solid_concern_vol != '') or 
		(solid_concern is not null and solid_concern != '')) then 
		(solid_concern_vol::text||'$'||solid_concern::text) else '-' end ) end as lspec_solid,
		lspec_slur,lspec_suct,
		
		case when (duty_cap_lqd is not null and duty_cap_lqd >0) then duty_cap_lqd::text else '-' end as duty_cap, -- Testing
		/*case when ((duty_cap_wat is not null and duty_cap_wat >0) and 
		(duty_cap_lqd is not null and duty_cap_lqd >0)) then 
		(duty_cap_wat::text||'$'||duty_cap_lqd)
		else ( case when ((duty_cap_wat is not null and duty_cap_wat >0) or 
		(duty_cap_lqd is not null and duty_cap_lqd >0)) then 
		(duty_cap_wat::text||'$'||duty_cap_lqd::text) else '-' end ) end as duty_cap,*/
		
		
		case when (duty_head_wat is not null and duty_head_wat >0) then duty_head_wat::text else '-' end as duty_water_head, -- Testing
		case when (duty_head_lqd is not null and duty_head_lqd >0) then duty_head_lqd::text else '-' end as duty_liquid_head, -- Testing
		case when ((duty_head_wat is not null and duty_head_wat >0) and 
		(duty_head_lqd is not null and duty_head_lqd >0)) then 
		(duty_head_wat::text||'$'||duty_head_lqd)
		else ( case when ((duty_head_wat is not null and duty_head_wat >0) or 
		(duty_head_lqd is not null and duty_head_lqd >0)) then 
		(duty_head_wat::text||'$'||duty_head_lqd::text) else '-' end ) end as duty_head,
		duty_suct,pump_pmodtype,pump_pmodel,pump_stgno,pump_sizex,pump_flange,pump_eff,
		
		case when (pump_bkw_water is not null and pump_bkw_water != '') then pump_bkw_water else '-' end as pump_water_bkw, -- Testing
		case when (pump_bkw_liq is not null and pump_bkw_liq != '') then pump_bkw_liq else '-' end as pump_liquid_bkw, -- Testing
		
		/*case when ((pump_bkw_water is not null and pump_bkw_water != '') and 
		(pump_bkw_liq is not null and pump_bkw_liq != '')) then 
		(pump_bkw_water::text||'$'||pump_bkw_liq)
		else ( case when ((pump_bkw_water is not null and pump_bkw_water != '') or 
		(pump_bkw_liq is not null and pump_bkw_liq != '')) then 
		(pump_bkw_water::text||'$'||pump_bkw_liq::text) else '-' end ) end as pump_bkw,*/
		pump_eoc,pump_motor_kw,
		
		/* case when (pump_full_load_rpm is not null and pump_full_load_rpm != '') then pump_full_load_rpm::text else '-' end as pump_rpm_pump, -- Testing 
		*/
		case when (motor_speed is not null and motor_speed != '') then motor_speed::text else '-' end as pump_rpm_motor, -- Testing
		case when (pump_speed_in_rpm is not null and pump_speed_in_rpm != '') then pump_speed_in_rpm::text else '-' end as pump_rpm_pump, -- Testing
		
		/*case when ((pump_full_load_rpm is not null and pump_full_load_rpm != '') and 
		(pump_speed_in_rpm is not null and pump_speed_in_rpm != '')) then 
		(pump_full_load_rpm::text||'$'||pump_speed_in_rpm)
		else ( case when ((pump_full_load_rpm is not null and pump_full_load_rpm != '') or 
		(pump_speed_in_rpm is not null and pump_speed_in_rpm != '')) then 
		(pump_full_load_rpm::text||'$'||pump_speed_in_rpm::text) else '-' end ) end as pump_speed,*/
		pump_tod,pump_npsh,pump_impeller_type,
		case when ((pump_imp_dia_rate is not null and pump_imp_dia_rate > 0) and 
		(pump_impeller_dia_max is not null and pump_impeller_dia_max != '') and (pump_impeller_dia_min is not null and pump_impeller_dia_min != '')) then 
		(pump_imp_dia_rate::text||'$'||pump_impeller_dia_max||'$'||pump_impeller_dia_min::text)
		else ( case when ((pump_imp_dia_rate is not null and pump_imp_dia_rate > 0) and 
		(pump_impeller_dia_max is not null and pump_impeller_dia_max != '') or (pump_impeller_dia_min is not null or  pump_impeller_dia_min != '')) then 
		(pump_imp_dia_rate::text||'$'||pump_impeller_dia_max||'$'||pump_impeller_dia_min) else '-' end ) 
		end as  pump_impeller_dia,
		pump_max_solid,pump_hydro,pump_shut,pump_setting_height,pump_sump_depth,
		pump_mini,pump_belt,pump_motor_kw as pump_motor_kw1,
		case when ((pump_full_load_rpm is not null and pump_full_load_rpm != '') and 
		(pump_speed_in_rpm is not null and pump_speed_in_rpm != '')) then 
		(pump_full_load_rpm::text||'$'||pump_speed_in_rpm)
		else ( case when ((pump_full_load_rpm is not null and pump_full_load_rpm != '') or 
		(pump_speed_in_rpm is not null and pump_speed_in_rpm != '')) then 
		(pump_full_load_rpm::text||'$'||pump_speed_in_rpm::text) else '-' end ) end as pump_speed1,
		pump_tod,pump_npsh as pump_npsh1,pump_impeller_type as pump_impeller_type1,
		pump_tod as pump_tod1,pump_impeller_tip,pump_seal_press,pump_seal_cap,acces,
		(coalesce(mech_type,'-')::text||'$'||coalesce(mech_face,'-')::text) as mech_type_face,
		(coalesce(mech_gland_plate,'-')::text||'$'||coalesce(mech_api_plan,'-')::text) as mech_gld_api,
		case when ((motor_type is not null and motor_type != '') and 
		(motor_mounting is not null and motor_mounting != '')) then 
		(motor_type::text||'$'||motor_mounting::text)
		else ( case when ((motor_type is not null and motor_type != '') or 
		(motor_mounting is not null and motor_mounting != '')) then 
		(motor_type::text||'$'||motor_mounting::text) else '-' end ) end as  mot_type_mount,
		case when ((motor_insulation is not null and motor_insulation != '') and 
		(motor_protection is not null and motor_protection != '')) then 
		(motor_insulation::text||'$'||motor_protection::text)
		else ( case when ((motor_insulation is not null and motor_insulation != '') or 
		(motor_protection is not null and motor_protection != '')) then 
		(motor_insulation::text||'$'||motor_protection::text) else '-' end ) end as mot_ins_prot,
		case when ((motor_voltage is not null and motor_voltage != '') and 
		(motor_phase is not null and motor_phase != '') and 
		(motor_Frequency is not null and motor_Frequency != '')) then 
		(motor_voltage::text||'$'||motor_phase::text)
		else ( case when ((motor_voltage is not null and motor_voltage != '') and 
		(motor_phase is not null and motor_phase != '') and 
		(motor_Frequency is not null and motor_Frequency != '')) then 
		(motor_voltage::text||'$'||motor_phase::text||'$'||motor_Frequency::text) else '-' end ) end as mot_volt_ph_frq,
		'bare_pump'::text as bare_pump,
		'spare'::text as spare from (	
		"""
		sqlone_query = """ select crm_id,pump_mod_type,purp_categ,
		item_eqno,item_desc, item_qty,lspec_lqd,lspec_temp, lspec_sgvt,lspec_ph,lspec_viscst,lspec_visfact,solid_concern_vol,solid_concern,
		lspec_slur,lspec_suct,duty_cap_wat,duty_cap_lqd,duty_head_wat,duty_head_lqd,
		duty_suct,pump_pmodtype,pump_pmodel,pump_stgno,pump_sizex,pump_flange,pump_eff,
		pump_bkw_water,pump_bkw_liq,pump_eoc,pump_motor_kw,pump_full_load_rpm,pump_speed_in_rpm,pump_speed_in_motor,pump_tod,pump_npsh,
		pump_impeller_type,
		pump_imp_dia_rate,pump_impeller_dia_max,pump_impeller_dia_min,pump_max_solid,pump_hydro,pump_shut,pump_setting_height,pump_sump_depth,
		pump_mini,pump_belt,pump_motor_kw as pump_motor_kw1,pump_impeller_tip,pump_seal_press,pump_seal_cap,acces,
		mech_type,mech_face,mech_gland_plate,mech_api_plan,motor_type,motor_mounting,motor_insulation,motor_protection,
		motor_voltage,motor_phase,motor_Frequency,'bare_pump'::text as bare_pump,
		'spare'::text as spare
		from (
		select id as crm_id,pump_model_type as pump_mod_type,purpose_categ as purp_categ,
		---- Item Details Starts Here
		equipment_no as item_eqno,description as item_desc,qty as item_qty,
		---- Item Details Ends Here
		---- Liquid Specifications Starts Here
		(select name from kg_fluid_master where id = fluid_id) as lspec_lqd,
		temperature_in_c as lspec_temp,
		specific_gravity as lspec_sgvt,
		ph_value as lspec_ph,
		viscosity as lspec_viscst,
		viscosity_crt_factor as lspec_visfact,
		case when solid_concen_vol>0 then solid_concen_vol::text else ''::text end as solid_concern_vol,
		case when solid_concen>0 then solid_concen::text else ''::text end as solid_concern,
		slurry_correction_in as lspec_slur, --- not for vertical
		
		case when suction_condition = 'positive' then 'Positive' else
		(case when suction_condition = 'negative' then 'Negative' else
		(case when suction_condition = 'flooded' then 'Flooded' else
		(case when suction_condition = 'sub_merged' then 'Submerged' else
		(case when suction_condition = 'suction_lift' then 'Suction' else '' end) end) end) end) end as lspec_suct,
		---- Liquid Specifications Ends Here
		---- Duty Parameters Starts Here
		capacity_in as duty_cap_wat,
		capacity_in_liquid as duty_cap_lqd,
		head_in_liquid as duty_head_lqd,
		head_in as duty_head_wat,
		suction_pressure as duty_suct, -- *v
		---- Duty Parameters Ends Here
		---- Pump Specification Starts Here
		pump_model_type as pump_pmodtype,
		(select name from kg_pumpmodel_master where id = pump_id) as pump_pmodel,
		number_of_stages as pump_stgno,
		size_suctionx as pump_sizex,
		(select name from ch_pumpseries_flange where id = flange_standard) as pump_flange,
		efficiency_in as pump_eff,
		case when bkw_liq>0 then bkw_liq::text else ''::text end as pump_bkw_liq,
		case when bkw_water>0 then bkw_water::text else ''::text end as pump_bkw_water,
		end_of_the_curve as pump_eoc,
		motor_kw as pump_motor_kw,
		case when full_load_rpm>0 then full_load_rpm::text else ''::text end as pump_full_load_rpm,
		case when speed_in_rpm>0 then speed_in_rpm::text else ''::text end as pump_speed_in_rpm,
		case when speed_in_motor>0 then speed_in_motor::text else ''::text end as pump_speed_in_motor,
		npsh_r_m as pump_npsh,
		impeller_type as pump_impeller_type,
		
		case when type_of_drive = 'motor_direct' then ('Direct') else
		(case when type_of_drive = 'belt_drive' then ('Belt drive') else
		(case when type_of_drive = 'fc_gb' then ('Fluid Coupling Gear Box') else
		(case when type_of_drive = 'vfd' then ('VFD') else '' end) end) end ) end as pump_tod,
		
		impeller_dia_rated as pump_imp_dia_rate,
		case when impeller_dia_min>0 then impeller_dia_min::text else ''::text end as pump_impeller_dia_min,
		case when impeller_dia_max>0 then impeller_dia_max::text else ''::text end as pump_impeller_dia_max,
		maximum_allowable_soild as pump_max_solid,
		hydrostatic_test_pressure as pump_hydro,
		shut_off_head as pump_shut,
		setting_height as pump_setting_height,
		sump_depth as pump_sump_depth,			
		minimum_contionuous as pump_mini,
		belt_loss_in_kw as pump_belt,
		impeller_tip_speed as pump_impeller_tip,
		sealing_water_pressure as pump_seal_press,
		sealing_water_capacity as pump_seal_cap,
		---- Pump Specification Ends Here
		---- MOC Starts Here
		acces as acces,
		---- MOC Ends Here
		---- Mech Specification Starts Here
		seal_type as mech_type,
		face_combination as mech_face,
		gland_plate as mech_gland_plate,
		api_plan as mech_api_plan,
		---- Mech Specification Ends Here
		---- Motor Specification Starts Here
		
		case when motor_type = 'eff_1' then 'EFF-1' else
		(case when motor_type = 'eff_2' then 'EFF-2' else
		(case when motor_type = 'eff_3' then 'EFF-3' else '' end) end) end as motor_type,
		
		case when motor_mounting = 'foot' then 'Foot' else
		(case when motor_mounting = 'flange' then 'Flange' else ''
		end) end as motor_mounting,
		
		insulation as motor_insulation,
		protection as motor_protection,
		voltage as motor_voltage,
		phase as motor_phase,
		frequency as motor_Frequency
		---- Motor Specification Ends Here
		"""
		sql_twoend = """ ) as sample ) as sample"""
		for report in rpt_type:
			crm_line_obj = self.pool.get('ch.kg.crm.pumpmodel')
			count_sql = """ select 
			(select name from kg_pumpmodel_master where id = pump_id) as pump_name,
			id as crm_id,purpose_categ as purpose_categ,
			count(*) OVER () from ch_kg_crm_pumpmodel where header_id in %s and pump_model_type = '%s' order by pump_model_type,purpose_categ,id """%(pass_param,report)
			cr.execute(count_sql)
			count_data = cr.dictfetchone()
			if not count_data:
				pass
			else:
				if report in ('horizontal','others'):
					sheet1 = wbk.add_sheet('Horizontal', cell_overwrite_ok=True)
					dictn = hz_dictn
				elif report == 'vertical':
					sheet1 = wbk.add_sheet('Vertical', cell_overwrite_ok=True)			
					dictn = vz_dictn
				count = count_data['count']
				pump_sql = count_sql
				cr.execute(pump_sql)
				pump_data = cr.dictfetchall()
				s1 = 0
				c1=0
				s2 = s1+1	
				c2 = c1+count				
				sheet1.col(0).width = 20000
				cmp_ids = cmp_obj.browse(cr, uid, 1)
				sheet1.write_merge(s2, s2, c1, c2,"SAM TURBO INDUSTRY PRIVATE LIMITED",style1)
				sheet1.row(0).height = 400
				s2 = s2+1
				sheet1.write_merge(s2, s2, c1, c2,"Avinashi Road, Neelambur, Coimbatore - 641062",style4)
				s2 = s2+1
				sheet1.write_merge(s2, s2, c1, c2,"Tel:3053555, 3053556,Fax : 0422-3053535",style4)				
				s2 = s2+1
				sheet1.write_merge(s2, s2, c1, c2, report.upper()+' SLURRY-CENTRIFUGAL PUMP OFFER SHEET', style41)
				s2 = s2+1
				sheet1.write_merge(s2, s2, c1, c2, 'Offer No: '+str(rec.name or '-'), style_highlight)
				s2 = s2+1
				offer_date = datetime.strptime(rec.offer_date,'%Y-%m-%d')
				offer_date = offer_date.strftime('%d/%m/%Y')
				sheet1.write_merge(s2, s2, c1, c2-1, 'Customer : '+str(rec.customer_id.name or '-'), style_highlight)
				sheet1.write_merge(s2, s2, c2, c2, 'Date : '+ str(offer_date or '-'), style_highlight)
				sheet1.insert_bitmap('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_crm_offer/img/sam.bmp',0,0)
				sheet1.row(0).height = 400
				sheet1.insert_bitmap('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_crm_offer/img/TUV_NORD.bmp',0,c2)
				for key in sorted(dictn):
					s2 = s2+1
					c1 = c1+1
					c1 = 0
					sheet1.write_merge(s2, s2, c1, c1+count, key.split('#')[1], style_left_header)
					for var in (dictn[key]):
						s2 = s2+1
						c1 = c1+1
						c1 = 0
						if var[0] == 'Purpose':
							moc_com_query = """ select crm.id as crm_id,
							moc.offer_id,moc.moc_id,--moc.seq_no,
							(select name from kg_offer_materials where id = moc.offer_id) as moc_offer_name,
							(select name from kg_moc_master where id = moc.moc_id) as moc_offer_value
							from ch_moc_construction moc 
							left outer join ch_kg_crm_pumpmodel crm on crm.id = moc.header_id """
							moc_cond = """where crm.header_id in  %s and crm.pump_model_type = '%s' """%(pass_param,report)
							moc_query = """ select distinct offer_id,moc_offer_name from ( """+moc_com_query + moc_cond +""" ) as sample """
							cr.execute(moc_query)
							moc_cond = """where crm.header_id in  %s and crm.pump_model_type = '%s' """%(pass_param,report)
							moc_query = """ select distinct offer_id,moc_offer_name from ( """+moc_com_query + moc_cond +""" ) as sample """
							cr.execute(moc_query)
							moc_query_data = cr.dictfetchall()
							if not moc_query_data:
								sheet1.write_merge(s2, s2, c1, c2, '-', style_center)
								s2 += 1
							for moc in moc_query_data:
								sheet1.write_merge(s2, s2, c1, c1, moc['moc_offer_name'], style_left)
								if pump_data:
									for pump in pump_data:
										c1 += 1
										moc_pump_query = moc_com_query+ """where crm.header_id in  %s and crm.pump_model_type = '%s' and crm.id = %s and moc.offer_id = %s """%(pass_param,report,pump['crm_id'],moc['offer_id'])
										cr.execute(moc_pump_query)
										moc_pump_data = cr.dictfetchall()
										if moc_pump_data:
											for moc_val in moc_pump_data:
												sheet1.write_merge(s2, s2, c1, c1, moc_val['moc_offer_value'], style_left)
										else:
											sheet1.write_merge(s2, s2, c1, c1, '-', style_left)
								s2 += 1
								c1 = 0
							s2 = s2-1
						elif var[0] == 'All Accessories':
							access_one_query_st =  """  select 
							array_to_string(array_agg(access_name), ',') as access_name,
							array_to_string(array_agg(comb), ';') as line_amt ,
							array_to_string(array_agg(line_amt), ',') as ref_line_amt 
							from ( """
							acc_sub_one = """ 
							select 
							access_name,enquiry_line_id,enquiry_line_id||'#'||line_amt as comb,line_amt
							from (
							select distinct access_name,enquiry_line_id,line_amt,gnd_amt from (
							select access_name,enquiry_line_id,
							sum(net_amount) OVER (PARTITION by enquiry_line_id) as line_amt,
							sum(net_amount) OVER () as gnd_amt from (
							select
							access_offer.off_name as access_name,
							access_offer.enquiry_line_id,
							case when (access_offer.qty > 0 and access_offer.r_net_amt_tot > 0) then 
							(access_offer.r_net_amt_tot/access_offer.qty) else 0.00 end as net_amount							
							from ch_accessories_offer access_offer
							left join kg_accessories_master acc on(acc.id=access_offer.access_id)
							left join kg_accessories_category categ on(categ.id=acc.access_cate_id)
							left join kg_hsn_master hsn on(hsn.id=access_offer.hsn_no)
							left join account_tax tax on(tax.id=access_offer.gst) """
							access_cond_query = """ where access_offer.enquiry_line_id in (select id from ch_kg_crm_pumpmodel where header_id in %s and pump_model_type = '%s') """%(pass_param,report)
							access_two_query = """ ) as sam
							) as sam_ref
							) as test """
							access_one_query_ed = """) as ref """
							access_query = access_one_query_st+acc_sub_one+access_cond_query+access_two_query+access_one_query_ed
							access_cnt_query = """ select access_name,count(access_name) from ( """ + access_query + """ )  as sql_access group by 1 """
							cr.execute(access_cnt_query)
							access_cnt_data = cr.dictfetchone()
							access_cnt = 0
							acc_name = ''
							if access_cnt_data:
								acc_name = access_cnt_data['access_name']
								access_cnt = access_cnt_data['count']
							acc_name = acc_name
							if access_cnt > 0 :
								sheet1.write_merge(s2, s2, c1, c1+count, var[0], style_sub_left)
							else:
								s2 = s2-1
							pump_cnt = 1
							if access_cnt > 0 :
								if pump_data:
									s2 = s2
									s2 = s2+1
									sheet1.write_merge(s2, s2, 0, 0, acc_name, style_left)
									for pump in pump_data:
										c1 += 1
										acc_sub_val_st = """ select enquiry_line_id,max(line_amt) as sum_line_amt from ( """
										acc_sub_val_ed = """ ) as sample group by 1 """
										acc_cond = """and  /* $$$$$$ */
										access_offer.enquiry_line_id = %s """%(pump['crm_id'])
										access_pump_query = acc_sub_val_st+acc_sub_one+access_cond_query+acc_cond+access_two_query+acc_sub_val_ed
										cr.execute(access_pump_query)
										access_pump_data = cr.dictfetchall()
										if access_pump_data:
											for access in access_pump_data:
												ref_val = access['sum_line_amt']
												acc = ref_val
												sheet1.write_merge(s2, s2, pump_cnt, pump_cnt, acc, style_left)
										else:
											sheet1.write_merge(s2, s2, pump_cnt, pump_cnt, '-', style_left)
										pump_cnt += 1
						elif var[0] == 'Spares':
							spare_query = """ select
							spare_offer.item_name ||' ('|| case when hsn.name is not null then hsn.name else '-' end ||')'||'('|| tax.name||')' as spare_name,
							pmm.name as pump_name,
							---spare_offer.net_amount as net_amount
							case when (spare_offer.qty > 0 and spare_offer.r_net_amt_tot > 0) then 
							(spare_offer.r_net_amt_tot/spare_offer.qty) else 0.00 end as net_amount
							from ch_spare_offer spare_offer
							left join kg_pumpmodel_master pmm on(pmm.id=spare_offer.pump_id)
							left join kg_hsn_master hsn on(hsn.id=spare_offer.hsn_no)
							left join account_tax tax on(tax.id=spare_offer.gst) """
							spare_cond_query = """ where spare_offer.enquiry_line_id in (select id from ch_kg_crm_pumpmodel where header_id in %s and pump_model_type = '%s') """%(pass_param,report)
							spare_cnt_query = """ select count(*) from ( """ + spare_query + spare_cond_query + """ )  as sql_spare """
							cr.execute(spare_cnt_query)
							spare_cnt_data = cr.dictfetchone()
							spare_cnt = 0
							if spare_cnt_data:
								spare_cnt = spare_cnt_data['count']
							if spare_cnt > 0 :
								sheet1.write_merge(s2, s2, c1, c1+count, var[0], style_sub_left)
								s2 += 1
							else:
								s2 = s2
							pump_cnt = 1
							if pump_data:
								for pump in pump_data:
									c1 += 1
									spare_count = 0
									spa_cond = """where spare_offer.enquiry_line_id = %s"""%(pump['crm_id'])
									spare_pump_query = spare_query+spa_cond
									cr.execute(spare_pump_query)
									spare_pump_data = cr.dictfetchall()
									spare_cnt = """ select count(*) from ( """+spare_pump_query+""" )  as sample"""
									cr.execute(spare_cnt)
									spare_cnt = cr.dictfetchone()
									spare_count = int(spare_cnt['count'])
									if spare_pump_data:
										for i in range(0,spare_count):
											head_s2 = s2+i
											spa = ''
											spare = spare_pump_data[i]
											if spare['spare_name']:
												spa = spare['spare_name']
											sheet1.write_merge(head_s2, head_s2, 0, 0, spa, style_left)											
											sheet1.write_merge(head_s2, head_s2, pump_cnt, pump_cnt, spare['net_amount'], style_left)									
											for c in range(1,count+1):
												if (c != pump_cnt and c != 0):
													sheet1.write_merge(head_s2, head_s2, c, c, 0.00, style_left)
									if spare_count > 0:
										s2 = s2 + spare_count-1
									else:
										s2 = s2
									
									pump_cnt += 1   
						else:
							sheet1.write_merge(s2, s2, c1, c1, var[0], style_left)
						if pump_data:
							for pump in pump_data:
 
								c1 += 1
								if var[1] in ('purp_categ','acces','spare'):
									pass
								elif var[1] == 'bare_pump':
									bare_pump_query = """ select
									---pump_offer.tot_price as tot_price
									case when (pump_offer.qty > 0 and pump_offer.r_net_amt_tot > 0) then 
									round(((pump_offer.r_net_amt_tot/pump_offer.qty)),0) else 0.00 end as tot_price								 
									from ch_pump_offer pump_offer
									left join kg_hsn_master hsn on(hsn.id=pump_offer.hsn_no)
									left join account_tax tax on(tax.id=pump_offer.gst)
									where pump_offer.enquiry_line_id = %s """%(pump['crm_id'])
									cr.execute(bare_pump_query)
									bare_pump_data = cr.dictfetchone()
									bare_pump = 0.00
									if bare_pump_data:
										bare_pump = bare_pump_data['tot_price']								 
									sheet1.write_merge(s2, s2, c1, c1, bare_pump, style_left)
								else:
									sqltwo_query = """
									from ch_kg_crm_pumpmodel where header_id in %s and pump_model_type = '%s' and id = %s
									) as sql_all  """%(pass_param,report,pump['crm_id'])
									sql_query = sqltwo+sqlone_query+sqltwo_query+sql_twoend
									cr.execute(sql_query)
									sql_query_data = cr.dictfetchall()
									if sql_query_data:
										for loop in sql_query_data:
											if loop[var[1]] != '-':
												replace_str = str(loop[var[1]])
												values = string.replace(replace_str, '$', '/')
												if var[1] == 'pump_pmodtype':
													ref_value = dict(self_obj._columns['pump_model_type'].selection)
													values = str(ref_value[loop[var[1]]])
												if var[1] == 'pump_impeller_type':
													ref_value = dict(self_obj._columns['impeller_type'].selection)
													if loop[var[1]] != '-':
														values = str(ref_value[loop[var[1]]])
											else:
												values = loop[var[1]]
											if var[1] == 'pump_pmodel':
												sheet1.write_merge(s2, s2, c1, c1, values, style_highlight)
											else:
												sheet1.write_merge(s2, s2, c1, c1, values, style_left)
									else:
										sheet1.write_merge(s2, s2, c1, c1, '', style_left)
									s2 = s2
				if pump_data:
					s1 = 5
					c1 = 0
					for pump in pump_data:
						c1 += 1
						sheet1.col(c1).width = 3000
				sheet1.write_merge(s2+1, s2+3, 0, c2, 'For SAM TURBO INDUSTRY PRIVATE LIMITED', style_right_header)
		"""Parsing data as string """
		file_data=StringIO.StringIO()
		o=wbk.save(file_data)		
		"""string encode of data in wksheet"""		
		out=base64.encodestring(file_data.getvalue())
		"""returning the output xls as binary"""
		report_name = 'Offer Copy' + '.' + 'xls'
		
		return self.write(cr, uid, ids, {'rep_data':out,'offer_copy':report_name},context=context)
	
	def spare_regular_copy(self,cr,uid,ids,context=None):
		pump_sql = """ 
		select offer_ref_id,enquiry_line_id,
		coalesce((line_tot),0.00) as ref_tot,		
		trim(TO_CHAR((coalesce((line_tot),0.00)), '999G999G99G999G99G99G990D99')) as line_tot_txt,
		company_name,to_char(CURRENT_TIMESTAMP, 'DD-MM-YYYY HH12:MI:SS AM') AS New_Date,
		pump_id,offer_ref,offer_date,customer,pump_name,serial_no from (
		select distinct spare.enquiry_line_id, offer.id as offer_ref_id,company.name as company_name,
		spare.pump_id as pump_id,offer.name as offer_ref,to_char(offer.offer_date::date,'dd-mm-YYYY') as offer_date,
		partner.name as customer,pump.name as pump_name,enquiry.s_no as serial_no,		
		case when offer.id is not null then
		(select coalesce((sum(coalesce(r_net_amt_tot::numeric,0.00))),0.00) as gnd_tot from
		(select r_net_amt_tot from ch_spare_offer 
		where header_id = offer.id ) as sub ) else 0.00 end as line_tot from kg_crm_offer offer
		left join ch_spare_offer spare on(spare.header_id = offer.id)
		left join kg_pumpmodel_master pump on(pump.id = spare.pump_id)
		left join ch_kg_crm_pumpmodel enquiry on(enquiry.id = spare.enquiry_line_id)
		left join res_partner partner on(partner.id=offer.customer_id)
		left join res_company company on(company.id=offer.company_id) 
		where offer.id=%s and offer.state != 'draft' and spare.enquiry_line_id is not null
		) as sample		
		"""%(ids[0])
		cr.execute(pump_sql)
		pump_data = cr.dictfetchall()
		pass_id = []
		cmp_obj = self.pool.get('res.company')
		wbk = xlwt.Workbook()
		sheet1 = wbk.add_sheet('Spare Regular Copy')
		report_name = 'Spare Regular Copy' + '.' + 'xls'
		s1 = 0
		c1=0
		s2 = s1+1	
		count = 9		
		if pump_data:
			gnd_tot = []
			cmp_ids = cmp_obj.browse(cr, uid, 1)
			c2 = c1+count				
			sheet1.write_merge(s2, s2, c1, c2,"SAM TURBO INDUSTRY PRIVATE LIMITED",style1)
			sheet1.row(0).height = 400
			s2 = s2+1
			sheet1.write_merge(s2, s2, c1, c2,"Avinashi Road, Neelambur, Coimbatore - 641062",style4)
			s2 = s2+1
			sheet1.write_merge(s2, s2, c1, c2,"Tel:3053555, 3053556,Fax : 0422-3053535",style4)				
			s2 = s2+1
			sheet1.write_merge(s2, s2, c1, c2, 'SPARE REGULAR COPY', style41)
			s2 = s2+1			
			sheet1.col(0).width = sheet1.col(3).width = sheet1.col(6).width = sheet1.col(7).width = 3000
			sheet1.col(1).width = sheet1.col(2).width = 5000
			sheet1.col(4).width = sheet1.col(5).width = 7000
			sheet1.col(8).width = sheet1.col(9).width = 4000			
			for pump in pump_data:				
				if pump_data.index(pump) == 0:
					sheet1.write_merge(s2, s2, c1, c1+4, 'CUSTOMER : ', style_highlight)
					sheet1.write_merge(s2, s2, c1+4+1, count, pump['customer'], style_highlight)
					s2 = s2+1					
				sheet1.write_merge(s2, s2, c1, c1+4, 'PUMP MODEL : ', style_highlight)
				sheet1.write_merge(s2, s2, c1+4+1, count, pump['pump_name'], style_highlight)
				s2 = s2+1
				sheet1.write_merge(s2, s2, c1, c1+4, 'EARLIER PUMP SERIAL NO : ', style_highlight)
				sheet1.write_merge(s2, s2, c1+4+1, count, pump['serial_no'], style_highlight)
				s2 = s2+1
				sheet1.write_merge(s2, s2, 0, 0, 'ITEM NO', style_highlight)
				sheet1.write_merge(s2, s2, 1, 1, 'MATERIAL CODE', style_highlight)
				sheet1.write_merge(s2, s2, 2, 2, 'HSN Code', style_highlight)
				sheet1.write_merge(s2, s2, 3, 3, 'GST %', style_highlight)
				sheet1.write_merge(s2, s2, 4, 4, 'PART NAME / PART NO', style_highlight)
				sheet1.write_merge(s2, s2, 5, 5, 'MATERIAL', style_highlight)
				sheet1.write_merge(s2, s2, 6, 6, 'QTY', style_right_header)
				sheet1.write_merge(s2, s2, 7, 7, 'UNIT', style_highlight)
				sheet1.write_merge(s2, s2, 8, 8, 'PRICE /EACH IN Rs.', style_right_header)
				sheet1.write_merge(s2, s2, 9, 9, 'TOTAL PRICE', style_right_header)
				s2 = s2+1
				det_sql = """ select
				coalesce(spare.material_code,'-') as material_code,coalesce(spare.off_name,'-') as off_name,
				pattern.name as pattern_no,moc.name as moc_name,spare.qty as qty,case when uom.name is not null then uom.name else 'No' end as unit,'A' as type,
				coalesce(hsn.name::text,'-') as hsn_code,coalesce(tax.description,'-') as tax_per,
				trim(TO_CHAR((coalesce(spare.r_net_amt_tot / spare.qty,0.00)), '999G999G99G999G99G99G990D99')) as each_price_txt,
				trim(TO_CHAR((coalesce(spare.r_net_amt_tot,0.00)), '999G999G99G999G99G99G990D99')) as total_price_txt
				from ch_spare_offer spare
				left join kg_pattern_master pattern on (pattern.id = spare.pattern_id)
				left join kg_hsn_master hsn on (hsn.id = spare.hsn_no)
				left join product_uom uom on (uom.id = spare.uom_id)
				left join account_tax tax on (tax.id = hsn.igst_id)
				left join kg_moc_master moc on (moc.id = spare.moc_id)
				left join kg_moc_construction moc_const on (moc_const.id = spare.moc_const_id)
				where spare.enquiry_line_id=%s """%(pump['enquiry_line_id'])
				cr.execute(det_sql)
				det_data = cr.dictfetchall()
				if det_data:
					sno = 1
					for var in det_data:
						sheet1.write_merge(s2, s2, 0, 0, sno, style_left)
						sheet1.write_merge(s2, s2, 1, 1, var['material_code'], style_left)
						sheet1.write_merge(s2, s2, 2, 2, var['hsn_code'], style_left)
						sheet1.write_merge(s2, s2, 3, 3, var['tax_per'], style_left)
						sheet1.write_merge(s2, s2, 4, 4, var['off_name'], style_left)
						sheet1.write_merge(s2, s2, 5, 5, var['moc_name'], style_left)
						sheet1.write_merge(s2, s2, 6, 6, var['qty'], style_right)
						sheet1.write_merge(s2, s2, 7, 7, var['unit'], style_left)
						sheet1.write_merge(s2, s2, 8, 8, var['each_price_txt'], style_right)
						sheet1.write_merge(s2, s2, 9, 9, var['total_price_txt'], style_right)
						s2 = s2+1
						sno = sno + 1
			data_sql = pump_sql
			cr.execute(data_sql)
			pump_one_data = cr.dictfetchone()
			pump_one_tot = 0.00
			if pump_one_data:
				pump_one_tot = pump_one_data['line_tot_txt']
			user_rec = self.pool.get('res.users').browse(cr,uid,uid)
			sheet1.write_merge(s2, s2, 0, count-1,"Total",style_center_header)
			sheet1.write_merge(s2, s2, count, count,pump_one_tot,style_right_header)
			s2 = s2+2
			sheet1.write_merge(s2, s2, 6, count,"FOR SAM TURBO INDUSTRY PVT LTD",style_center_header)
			s2 = s2+3
			sheet1.write_merge(s2, s2, 6, count,user_rec.name,style_center_header)
			s2 = s2+1
			sheet1.write_merge(s2, s2, 6, count,"Authorized Signature",style_center_header)
			s2 = s2+1
			#~ sheet1.insert_bitmap('/OPENERP/Sam_Turbo/sam_turbo_dev/openerp-server/openerp/addons/kg_crm_offer/img/sam.bmp',0,0)
			#~ sheet1.row(0).height = 400
			#~ sheet1.insert_bitmap('/OPENERP/Sam_Turbo/sam_turbo_dev/openerp-server/openerp/addons/kg_crm_offer/img/TUV_NORD.bmp',0,c2)
		else:
			sheet1.write_merge(0, s2, 0, count, 'No record Exists', xlwt.easyxf('font: height 220,name Calibri;font: bold on;align: wrap on, horiz center;border: top thin, bottom thin, left thin, right thin;'))
		"""Parsing data as string """
		file_data=StringIO.StringIO()
		o=wbk.save(file_data)		
		"""string encode of data in wksheet"""		
		out=base64.encodestring(file_data.getvalue())
		"""returning the output xls as binary"""
		print "fffff",report_name
		return self.write(cr, uid, ids, {'spare_reg_data':out,'spare_reg_copy':report_name},context=context)
		
	def spare_budgetary_copy(self,cr,uid,ids,context=None):
		pump_sql = """ 
		select offer_ref_id,enquiry_line_id,
		coalesce((line_tot),0.00) as ref_tot,		
		trim(TO_CHAR((coalesce((line_tot),0.00)), '999G999G99G999G99G99G990D99')) as line_tot_txt,		
		company_name,to_char(CURRENT_TIMESTAMP, 'DD-MM-YYYY HH12:MI:SS AM') AS New_Date,
		pump_id,offer_ref,offer_date,customer,pump_name,serial_no from (
		select distinct spare.enquiry_line_id, offer.id as offer_ref_id,company.name as company_name,
		spare.pump_id as pump_id,offer.name as offer_ref,to_char(offer.offer_date::date,'dd-mm-YYYY') as offer_date,
		partner.name as customer,pump.name as pump_name,enquiry.s_no as serial_no,
		case when offer.id is not null then
		(select coalesce((sum(coalesce(r_net_amt_tot::numeric,0.00))),0.00) as gnd_tot from
		(select r_net_amt_tot from ch_spare_offer 
		where header_id = offer.id ) as sub ) else 0.00 end as line_tot from kg_crm_offer offer
		left join ch_spare_offer spare on(spare.header_id = offer.id)
		left join kg_pumpmodel_master pump on(pump.id = spare.pump_id)
		left join ch_kg_crm_pumpmodel enquiry on(enquiry.id = spare.enquiry_line_id)
		left join res_partner partner on(partner.id=offer.customer_id)
		left join res_company company on(company.id=offer.company_id) 
		where offer.id=%s and offer.state != 'draft' and spare.enquiry_line_id is not null
		) as sample		
		"""%(ids[0])
		cr.execute(pump_sql)
		pump_data = cr.dictfetchall()
		pass_id = []
		cmp_obj = self.pool.get('res.company')
		wbk = xlwt.Workbook()
		sheet1 = wbk.add_sheet('Spare Budgetary Copy')
		report_name = 'Spare Budgetary Copy' + '.' + 'xls'
		s1 = 0
		c1=0
		s2 = s1+1	
		count = 6	
		if pump_data:
			gnd_tot = []
			cmp_ids = cmp_obj.browse(cr, uid, 1)
			c2 = c1+count				
			sheet1.write_merge(s2, s2, c1, c2,"SAM TURBO INDUSTRY PRIVATE LIMITED",style1)
			sheet1.row(0).height = 400
			s2 = s2+1
			sheet1.write_merge(s2, s2, c1, c2,"Avinashi Road, Neelambur, Coimbatore - 641062",style4)
			s2 = s2+1
			sheet1.write_merge(s2, s2, c1, c2,"Tel:3053555, 3053556,Fax : 0422-3053535",style4)				
			s2 = s2+1
			sheet1.write_merge(s2, s2, c1, c2, 'SPARE REGULAR COPY', style41)
			s2 = s2+1			
			sheet1.col(0).width = sheet1.col(3).width = 3000
			sheet1.col(1).width = sheet1.col(2).width = 5000
			sheet1.col(4).width = 7000
			sheet1.col(5).width = sheet1.col(6).width = 6000			
			for pump in pump_data:				
				if pump_data.index(pump) == 0:
					sheet1.write_merge(s2, s2, c1, c1+4, 'CUSTOMER : ', style_highlight)
					sheet1.write_merge(s2, s2, c1+4+1, count, pump['customer'], style_highlight)
					s2 = s2+1					
				sheet1.write_merge(s2, s2, c1, c1+4, 'PUMP MODEL : ', style_highlight)
				sheet1.write_merge(s2, s2, c1+4+1, count, pump['pump_name'], style_highlight)
				s2 = s2+1
				sheet1.write_merge(s2, s2, c1, c1+4, 'EARLIER PUMP SERIAL NO : ', style_highlight)
				sheet1.write_merge(s2, s2, c1+4+1, count, pump['serial_no'], style_highlight)
				s2 = s2+1
				sheet1.write_merge(s2, s2, 0, 0, 'ITEM NO', style_highlight)
				sheet1.write_merge(s2, s2, 1, 1, 'MATERIAL CODE', style_highlight)
				sheet1.write_merge(s2, s2, 2, 2, 'HSN Code', style_highlight)
				sheet1.write_merge(s2, s2, 3, 3, 'GST %', style_highlight)
				sheet1.write_merge(s2, s2, 4, 4, 'PART NAME', style_highlight)
				sheet1.write_merge(s2, s2, 5, 5, 'MATERIAL', style_highlight)
				sheet1.write_merge(s2, s2, 6, 6, 'PRICE /EACH IN Rs.', style_right_header)
				s2 = s2+1
				det_sql = """ select
				coalesce(spare.material_code,'-') as material_code,coalesce(spare.off_name,'-') as off_name,
				pattern.name as pattern_no,moc.name as moc_name,spare.qty as qty,case when uom.name is not null then uom.name else 'No' end as unit,'A' as type,
				coalesce(hsn.name::text,'-') as hsn_code,coalesce(tax.description,'-') as tax_per,
				trim(TO_CHAR((coalesce(spare.r_net_amt_tot / spare.qty,0.00)), '999G999G99G999G99G99G990D99')) as each_price_txt,
				trim(TO_CHAR((coalesce(spare.r_net_amt_tot,0.00)), '999G999G99G999G99G99G990D99')) as total_price_txt
				from ch_spare_offer spare
				left join kg_pattern_master pattern on (pattern.id = spare.pattern_id)
				left join kg_hsn_master hsn on (hsn.id = spare.hsn_no)
				left join product_uom uom on (uom.id = spare.uom_id)
				left join account_tax tax on (tax.id = hsn.igst_id)
				left join kg_moc_master moc on (moc.id = spare.moc_id)
				left join kg_moc_construction moc_const on (moc_const.id = spare.moc_const_id)
				where spare.enquiry_line_id=%s """%(pump['enquiry_line_id'])
				cr.execute(det_sql)
				det_data = cr.dictfetchall()
				if det_data:
					sno = 1
					for var in det_data:
						sheet1.write_merge(s2, s2, 0, 0, sno, style_left)
						sheet1.write_merge(s2, s2, 1, 1, var['material_code'], style_left)
						sheet1.write_merge(s2, s2, 2, 2, var['hsn_code'], style_left)
						sheet1.write_merge(s2, s2, 3, 3, var['tax_per'], style_left)
						sheet1.write_merge(s2, s2, 4, 4, var['off_name'], style_left)
						sheet1.write_merge(s2, s2, 5, 5, var['moc_name'], style_left)
						sheet1.write_merge(s2, s2, 6, 6, var['each_price_txt'], style_right)
						s2 = s2+1
						sno = sno + 1
			data_sql = pump_sql
			cr.execute(data_sql)
			pump_one_data = cr.dictfetchone()
			pump_one_tot = 0.00
			if pump_one_data:
				pump_one_tot = pump_one_data['line_tot_txt']
			user_rec = self.pool.get('res.users').browse(cr,uid,uid)
			#~ sheet1.write_merge(s2, s2, 0, count-1,"Total",style_center_header)
			#~ sheet1.write_merge(s2, s2, count, count,pump_one_tot,style_right_header)
			s2 = s2+2
			sheet1.write_merge(s2, s2, 5, count,"FOR SAM TURBO INDUSTRY PVT LTD",style_center_header)
			s2 = s2+3
			sheet1.write_merge(s2, s2, 5, count,user_rec.name,style_center_header)
			s2 = s2+1
			sheet1.write_merge(s2, s2, 5, count,"Authorized Signature",style_center_header)
			s2 = s2+1
			#~ sheet1.insert_bitmap('/OPENERP/Sam_Turbo/sam_turbo_dev/openerp-server/openerp/addons/kg_crm_offer/img/sam.bmp',0,0)
			#~ sheet1.row(0).height = 400
			#~ sheet1.insert_bitmap('/OPENERP/Sam_Turbo/sam_turbo_dev/openerp-server/openerp/addons/kg_crm_offer/img/TUV_NORD.bmp',0,c2)
		else:
			sheet1.write_merge(0, s2, 0, count, 'No record Exists', xlwt.easyxf('font: height 220,name Calibri;font: bold on;align: wrap on, horiz center;border: top thin, bottom thin, left thin, right thin;'))
		"""Parsing data as string """
		file_data=StringIO.StringIO()
		o=wbk.save(file_data)		
		"""string encode of data in wksheet"""		
		out=base64.encodestring(file_data.getvalue())
		"""returning the output xls as binary"""
		return self.write(cr, uid, ids, {'spare_bud_data':out,'spare_bud_copy':report_name},context=context)
	
	def onchange_term(self, cr, uid, ids, load_term,line_term_ids):
		term_vals=[]
		if line_term_ids:
			cr.execute('''delete from ch_term_offer where header_id = %s '''%(line_term_ids[0][0]))
		if load_term == True:
			term_ids = self.pool.get('kg.offer.term').search(cr, uid, [('state','not in',('reject','cancel'))])
			if term_ids:
				for item in term_ids:
					term_rec = self.pool.get('kg.offer.term').browse(cr, uid, item)
					term_vals.append({
									'term_id': term_rec.id,
									'term': term_rec.term,
									})
		return {'value': {'line_term_ids': term_vals}}
	
	def term_copy(self, cr, uid, ids, context={}):
		import StringIO
		import base64
		try:
			import xlwt
		except:
		   raise osv.except_osv('Warning !','Please download python xlwt module from\nhttp://pypi.python.org/packages/source/x/xlwt/xlwt-0.7.2.tar.gz\nand install it')
		   
		rec =self.browse(cr,uid,ids[0])
		
		record={}
		sno=0
		wbk = xlwt.Workbook()
		style1 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz center;''borders: left thin, right thin, top thin') 
		style2 = xlwt.easyxf('font: height 200,color_index black;' 'align: wrap on, vert centre, horiz left;''borders: left thin, right thin, top thin, bottom thin') 
		style4 = xlwt.easyxf('font: height 200,color_index black;' 'align: wrap on, vert centre, horiz center;''borders: left thin, right thin, top thin, bottom thin') 
		style3 = xlwt.easyxf('font: height 200,color_index black;' 'align: wrap on, vert centre, horiz right;') 
		
		s1=0
		"""adding a worksheet along with name"""
		sheet1 = wbk.add_sheet('Terms Copy')
		s2=6
		sheet1.col(0).width = 1500
		sheet1.col(1).width = 8000
		sheet1.col(2).width = 13000
		
		""" writing field headings """
		sheet1.write_merge(s1, 0, 0, 2,"SAM TURBO INDUSTRY PRIVATE LIMITED",style1)
		sheet1.row(0).height = 400
		sheet1.write_merge(1, 1, 0, 2,"Avinashi Road, Neelambur, Coimbatore - 641062",style4)
		sheet1.write_merge(2, 2, 0, 2,"Tel:3053555, 3053556,Fax : 0422-3053535",style4)
		
		sheet1.write_merge(3,3,0,1,'Offer No: '+str(rec.name),style2)
		offer_date = datetime.strptime(rec.offer_date, '%Y-%m-%d').strftime('%d/%m/%Y')
		sheet1.write_merge(3,3,2,2,'Offer Date: '+str(offer_date),style2)
		sheet1.write_merge(4,4,0,2,'Customer Name: '+str(rec.customer_id.name),style2)
		sheet1.write_merge(5,5,0,2,"TERMS & CONDITIONS",style1)
		sheet1.row(5).height = 350
		"""writing data according to query and filteration in worksheet"""
		sno=1
		
		if rec.line_term_ids:
			for item in rec.line_term_ids:
				sheet1.write_merge(s2,s2,0,0,str(sno),style2)
				sheet1.write_merge(s2,s2,1,1,str(item.term_id.name),style2)
				sheet1.write_merge(s2,s2,2,2,str(item.term),style2)
				s2+=1
				sno = sno + 1
		s2 = s2 + 2
		sheet1.write_merge(s2,s2,2,2,"Authorised Signatory",style3)
		"""Parsing data as string """
		file_data=StringIO.StringIO()
		o=wbk.save(file_data)		
		"""string encode of data in wksheet"""		
		out=base64.encodestring(file_data.getvalue())
		"""returning the output xls as binary"""
		report_name = 'Terms Copy' + '.' + 'xls'
		
		return self.write(cr, uid, ids, {'term_data':out, 'term_copy':report_name},context=context)
	
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_code = str(rec.name)		
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
			
		url = 'http://192.168.1.7/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&Offer='+rec_code


		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
	
kg_crm_offer()


class ch_pump_offer(osv.osv):
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		sam_ratio_tot = dealer_discount_tot = customer_discount_tot = spl_discount_tot = tax_tot = p_f_tot = freight_tot = insurance_tot = pump_price_tot = supervision_tot = tot_price = net_amount = 0
		i_tot = k_tot = m_tot = p_tot = r_tot = prime_cost = r_dealer_discount = r_net_amt_tot = 0
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
				'prime_cost': 0.0,
				
			}
			
			print"line.prime_cost",line.prime_cost
			print"line.sam_ratio",line.sam_ratio
			sam_ratio_tot = round(line.prime_cost * line.sam_ratio,2)
			print"sam_ratio_totsam_ratio_tot",sam_ratio_tot
			dealer_discount = round(sam_ratio_tot / (1-line.dealer_discount/100.00),2)
			dealer_discount_tot = round(dealer_discount - sam_ratio_tot,2)
			print"dealer_discount_totdealer_discount_tot",dealer_discount_tot
			spl_discount = round(dealer_discount / (1-line.special_discount/100.00),2)
			spl_discount_tot = round(spl_discount - dealer_discount,2)
			print"spl_discount_totspl_discount_tot",spl_discount_tot
			if line.p_f_in_ex == 'inclusive':
				p_f = round(spl_discount / (1-line.p_f/100.00),2)
			else:
				p_f = spl_discount
			p_f_tot = round(p_f - spl_discount,2)
			print"p_f_totp_f_tot",p_f_tot
			if line.freight_in_ex == 'inclusive':
				insurance = round(p_f / (1-line.insurance/100.00),2)
			else:
				insurance = p_f
			insurance_tot = round(insurance - p_f,2)
			print"insurance_tot",insurance_tot
			if line.freight_in_ex == 'inclusive':
				freight = round(insurance / (1-line.freight/100.00),2)
			else:
				freight = insurance
			freight_tot = round(freight - insurance,2)
			print"freight_tot",freight_tot
			pump_price_tot = freight
			print"pump_price_tot",pump_price_tot
			customer_discount = round(pump_price_tot / (1-line.customer_discount/100.00),2)
			customer_discount_tot = round(customer_discount - pump_price_tot,2)
			print"customer_discount_tot",customer_discount_tot
			if line.gst:
				tax = round(customer_discount / (1-(line.gst.amount*100)/100.00),2)
			else:
				tax = customer_discount
			print"tax",tax
			tax_tot = round(tax - customer_discount,2)
			print"tax_tottax_tot",tax_tot
			#~ supervision_tot = round(tax + line.supervision_amount,2)
			#~ print"supervision_tot",supervision_tot
			tot_price = round(customer_discount)
			#~ tot_price = tax
			print"tot_price",tot_price
			
			#~ r_customer_discount_tot = round((tot_price * line.r_customer_discount) / 100.00,2)
			r_customer_discount_tot = round((line.r_cpo_amount * line.r_customer_discount) / 100.00)
			print"r_customer_discount_tot",r_customer_discount_tot
			r_pump_price_tot = round(line.r_cpo_amount - r_customer_discount_tot)
			print"r_pump_price_tot",r_pump_price_tot
			if line.gst:
				r_tax_tot = round(((r_pump_price_tot + line.r_p_f_ex_tot)*(line.gst.amount*100))/100.00)
			else:
				r_tax_tot = 0 
			print"r_tax_tot",r_tax_tot
			if line.r_freight_in_ex == 'inclusive':
				r_freight_tot = round((r_pump_price_tot*line.r_freight)/100.00)
				r_freight_ex_tot = 0
			elif line.r_freight_in_ex == 'exclusive':
				r_freight_ex_tot = round((r_pump_price_tot*line.r_freight)/100.00)
				r_freight_tot = 0
			else:
				r_freight_tot = 0
				r_freight_ex_tot = 0
			print"r_freight_tot",r_freight_tot
			if line.r_insurance_in_ex == 'inclusive':
				r_insurance_tot = round((r_pump_price_tot*line.r_insurance)/100.00)
			else:
				r_insurance_tot = 0
			print"r_insurance_tot",r_insurance_tot
			if line.r_p_f_in_ex == 'inclusive':
				r_p_f_tot = round((r_pump_price_tot*line.r_p_f)/100.00)
				r_p_f_ex_tot = 0
			elif line.r_p_f_in_ex == 'exclusive':
				r_p_f_ex_tot = round((r_pump_price_tot*line.r_p_f)/100.00)
				r_p_f_tot = 0
			else:
				r_p_f_tot = 0
				r_p_f_ex_tot = 0
			print"r_p_f_tot",r_p_f_tot
			r_spl_discount_tot = round((r_pump_price_tot*line.r_special_discount) / 100.00)
			print"r_spl_discount_tot",r_spl_discount_tot
			r_spl_discount = r_pump_price_tot - r_spl_discount_tot - r_freight_tot - r_insurance_tot - r_p_f_tot
			print"r_spl_discount",r_spl_discount
			r_dealer_discount = r_spl_discount
			print"r_dealer_discount",r_dealer_discount
			r_dealer_discount_tot = round((r_dealer_discount*line.r_dealer_discount) / 100.00)
			print"r_dealer_discount_tot",r_dealer_discount_tot
			r_sam_ratio_tot = r_pump_price_tot - r_spl_discount_tot - r_dealer_discount_tot - r_p_f_tot - r_insurance_tot - r_freight_tot
			print"r_sam_ratio_tot",r_sam_ratio_tot
			print"line.prime_costline.prime_cost",line.prime_cost
			r_sam_ratio = r_sam_ratio_tot / line.prime_cost
			print"r_sam_ratio",r_sam_ratio
			
			r_net_amt_tot =  line.r_cpo_amount_tot - r_customer_discount_tot
			
			res[line.id]['sam_ratio_tot'] = sam_ratio_tot
			res[line.id]['dealer_discount_tot'] = dealer_discount_tot
			res[line.id]['spl_discount_tot'] = spl_discount_tot
			res[line.id]['p_f_tot'] = p_f_tot
			res[line.id]['insurance_tot'] = insurance_tot
			res[line.id]['freight_tot'] = freight_tot
			res[line.id]['pump_price_tot'] = pump_price_tot
			res[line.id]['customer_discount_tot'] = customer_discount_tot
			res[line.id]['tax_tot'] = tax_tot
			res[line.id]['supervision_tot'] = line.supervision_amount
			res[line.id]['tot_price'] = tot_price
			res[line.id]['net_amount'] = tot_price
			
			res[line.id]['r_sam_ratio'] = r_sam_ratio
			res[line.id]['r_works_value'] = r_sam_ratio_tot
			res[line.id]['r_sam_ratio_tot'] = r_sam_ratio_tot
			res[line.id]['r_dealer_discount_val'] = r_dealer_discount
			res[line.id]['r_dealer_discount_tot'] = r_dealer_discount_tot
			res[line.id]['r_spl_discount_tot'] = r_spl_discount_tot
			res[line.id]['r_p_f_tot'] = r_p_f_tot
			res[line.id]['r_p_f_ex_tot'] = r_p_f_ex_tot
			res[line.id]['r_insurance_tot'] = r_insurance_tot
			res[line.id]['r_freight_tot'] = r_freight_tot
			res[line.id]['r_freight_ex_tot'] = r_freight_ex_tot
			res[line.id]['r_pump_price_tot'] = r_pump_price_tot
			res[line.id]['r_customer_discount_tot'] = r_customer_discount_tot
			res[line.id]['r_net_amt_tot'] = r_net_amt_tot
			res[line.id]['r_tax_tot'] = r_tax_tot
			#~ res[line.id]['r_tot_price'] = tot_price
			if line.cust_in_ex == 'inclusive':
				res[line.id]['r_net_amount'] = r_pump_price_tot + r_p_f_ex_tot + r_tax_tot
			else:
				res[line.id]['r_net_amount'] = r_pump_price_tot + r_customer_discount_tot + r_p_f_ex_tot + r_tax_tot
			res[line.id]['prime_cost'] = (line.per_pump_prime_cost * line.qty) + line.additional_cost
			print"line.r_cpo_amount",line.r_cpo_amount
			enq_no = line.header_id.enquiry_no
			print"enq_noenq_no",enq_no
			enq_ids = self.pool.get('kg.crm.enquiry').search(cr,uid,[('name','=',enq_no),('state','!=','revised')])
			print"enq_ids",enq_ids
			if enq_ids:
				enq_rec = self.pool.get('kg.crm.enquiry').browse(cr,uid,enq_ids[0])
				print"enq_recenq_rec",enq_rec.state
			#~ if line.r_cpo_amount == 0.00 and not enq_rec.state == 'draft':
				#~ print"tot_pricetot_price",tot_price
				#~ cr.execute('''update ch_pump_offer set r_cpo_amount = %s where id = %s ''',(tot_price,line.id))
			print"tot_pricetot_price",tot_price
			if line.cpo_quote_cust == 'quoted':
				cr.execute('''update ch_pump_offer set r_cpo_amount = %s,r_cpo_amount_tot = %s where id = %s ''',(tot_price,tot_price,line.id))
			elif line.cpo_quote_cust == 'cust_po':
				cr.execute('''update ch_pump_offer set r_cpo_amount = %s,r_cpo_amount_tot = %s where id = %s ''',(line.r_cpo_amount,line.r_cpo_amount,line.id))
		
		return res
	
	_name = "ch.pump.offer"
	_description = "Ch Pump Offer"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('kg.crm.offer', 'Offer', ondelete='cascade'),
		
		## Module Requirement Fields
		
		'offer_id':fields.many2one('kg.crm.offer','Offer'),
		'customer_id':fields.many2one('res.partner','Customer Name'),
		'qty':fields.integer('Quantity'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),
		'hsn_no': fields.many2one('kg.hsn.master','HSN No.'),
		'gst': fields.many2one('account.tax','GST Tax'),
		'pumpseries_id': fields.many2one('kg.pumpseries.master','Pump Series'),
		'moc_const_id': fields.many2one('kg.moc.construction','MOC'),
		'drawing_approval': fields.selection([('yes','Yes'),('no','No')],'Drawing approval'),
		'purpose_categ': fields.selection([('pump','Pump'),('in_development','New Development')],'Purpose Categ'),
		'inspection': fields.selection([('yes','Yes'),('no','No'),('tpi','TPI'),('customer','Customer'),('consultant','Consultant'),('stagewise','Stage wise')],'Inspection'),
		#~ 'prime_cost': fields.float('Prime Cost'),
		'additional_cost': fields.float('Additional Cost'),
		'additional_cost_remark': fields.text('Additional Cost Remark'),
		'prime_cost': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Prime Cost',multi="sums",store=True),
		'per_pump_prime_cost': fields.float('Per Pump Prime Cost'),
		'sam_ratio': fields.float('Sam Ratio'),
		'dealer_discount': fields.float('Dealer Discount(%)'),
		'customer_discount': fields.float('Mark-Up(%)'),
		'special_discount': fields.float('Special Discount(%)'),
		'tax': fields.float('Tax(%)'),
		'p_f': fields.float('P&F(%)'),
		'freight': fields.float('Freight(%)'),
		'insurance': fields.float('Insurance(%)'),
		'p_f_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'P&F'),
		'freight_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Freight'),
		'insurance_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Insurance'),
		'tax_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Tax'),
		'ed_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'ED'),
		'ed': fields.float('ED(%)'),
		'agent_com': fields.float('Agent Commission(%)'),
		'supervision_amount': fields.float('Supervision(Rs.)'),
		'works_value': fields.float('Works Value'),
		'works_value_flag': fields.boolean('Works Value Flag'),
		'sam_ratio_flag': fields.boolean('Sam Ratio Flag'),
		'total_price': fields.float('Total Price(%)'),
		'wo_line_id': fields.many2one('ch.work.order.details','WO Line'),
		'order_summary': fields.char('Order Summary'),
		
		'r_agent_com': fields.float('Agent Commission(%)'),
		'r_dealer_discount': fields.float('Dealer Discount(%)'),
		'r_customer_discount': fields.float('Customer Discount(%)'),
		'cust_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Customer Discount'),
		'r_special_discount': fields.float('Special Discount(%)'),
		'r_p_f': fields.float('P&F(%)'),
		'r_freight': fields.float('Freight(%)'),
		'r_insurance': fields.float('Insurance(%)'),
		'r_p_f_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'P&F'),
		'r_freight_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Freight'),
		'r_insurance_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Insurance'),
		'r_supervision_amount': fields.float('Supervision(Rs.)'),
		'r_additional_cost': fields.float('Additional Cost'),
		'r_cpo_amount': fields.float('CPO(Total Qty)'),
		'r_cpo_amount_tot': fields.float('CPO',readonly=True),
		'cpo_quote_cust': fields.selection([('quoted','Quoted price'),('cust_po','Customer price')],'CPO Value'),
		
		'tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Price',multi="sums",store=True),
		'sam_ratio_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Works Value',multi="sums",store=True),
		'dealer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),
		'customer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),
		'spl_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Special Discount Value',multi="sums",store=True),
		'tax_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='GST',multi="sums",store=True),
		'p_f_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F',multi="sums",store=True),
		'freight_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),
		'insurance_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),
		'supervision_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Supervision Price',multi="sums",store=True),
		'pump_price_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Pump Price',multi="sums",store=True),
		'net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Quoted Value(GST Extra)',multi="sums",store=True),
		
		#~ 'r_tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Price',multi="sums",store=True),
		'r_sam_ratio': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Sam Ratio(%)',multi="sums",store=True),
		'r_works_value': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Works Value',multi="sums",store=True),
		'r_sam_ratio_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Works Value',multi="sums",store=True),
		'r_dealer_discount_val': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value Consider',multi="sums",store=True),
		'r_dealer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),
		'r_customer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),
		'r_spl_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Special Discount Value',multi="sums",store=True),
		'r_tax_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='GST',multi="sums",store=True),
		'r_p_f_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F(Inc)',multi="sums",store=True),
		'r_p_f_ex_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F(Exc)',multi="sums",store=True),
		'r_freight_ex_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight Ex',multi="sums",store=True),
		'r_freight_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),
		'r_insurance_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),
		'r_pump_price_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Pump Price',multi="sums",store=True),
		'r_net_amt_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),
		'r_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Grand Total',multi="sums",store=True),
		
		## Child Tables Declaration
		
		'enquiry_line_id': fields.many2one('ch.kg.crm.pumpmodel','Enquiry Line'),
		'off_fou_id': fields.related('enquiry_line_id','line_ids', type='one2many', relation='ch.kg.crm.foundry.item', string='Foundry Items'),
		'off_ms_id': fields.related('enquiry_line_id','line_ids_a', type='one2many', relation='ch.kg.crm.machineshop.item', string='MS Items'),
		'off_bot_id': fields.related('enquiry_line_id','line_ids_b', type='one2many', relation='ch.kg.crm.bot', string='BOT Items'),
		'line_development_ids': fields.one2many('ch.pump.offer.development', 'header_id', "Pump Offer Development"),
		'spl_remark': fields.related('enquiry_line_id','spl_remark',type='html',string="Special Remark",store=True),
		
	}
	
	_defaults = {
		
		#~ 'temperature': 'normal',
		#~ 'flange_type': 'standard',
		#~ 'load_bom':False,
		#~ 'r_cpo_amount':0.00,
		'cpo_quote_cust':'quoted',
		'cust_in_ex':'inclusive',
		
	}
	
	def onchange_sam_ratio(self, cr, uid, ids, prime_cost, works_value, works_value_flag, sam_ratio, sam_ratio_flag, context=None):
		value = {'works_value':'','sam_ratio':''}
		if works_value_flag == True and works_value:
			value = {'sam_ratio': float(works_value)/float(prime_cost),'r_sam_ratio':float(works_value)/float(prime_cost)}
		elif sam_ratio_flag == True and sam_ratio:
			value = {'works_value': prime_cost * sam_ratio,'r_sam_ratio':sam_ratio}
		return {'value': value}
	
	def onchange_delaer_discount(self, cr, uid, ids, delaer_discount):
		value = {'r_delaer_discount':0}
		if delaer_discount:
			value = {'r_dealer_discount': delaer_discount}
		return {'value': value}
	
	def onchange_special_discount(self, cr, uid, ids, special_discount):
		value = {'r_special_discount':0}
		if special_discount:
			value = {'r_special_discount': special_discount}
		return {'value': value}
	
	def onchange_p_f(self, cr, uid, ids, p_f, p_f_in_ex):
		value = {'r_p_f':0,'r_p_f_in_ex':''}
		if p_f and p_f_in_ex:
			value = {'r_p_f': p_f,'r_p_f_in_ex': p_f_in_ex}
		return {'value': value}
	
	def onchange_freight(self, cr, uid, ids, freight, freight_in_ex):
		value = {'r_freight':0,'r_freight_in_ex':''}
		if freight and freight_in_ex:
			value = {'r_freight': freight,'r_freight_in_ex': freight_in_ex}
		return {'value': value}
	
	def onchange_insurance(self, cr, uid, ids, insurance, insurance_in_ex):
		value = {'r_insurance':0,'r_insurance_in_ex':''}
		if insurance and insurance_in_ex:
			value = {'r_insurance': insurance,'r_insurance_in_ex': insurance_in_ex}
		return {'value': value}
	
	def onchange_supervision(self, cr, uid, ids, supervision_amount):
		value = {'r_supervision_amount':0}
		if supervision_amount:
			value = {'r_supervision_amount': supervision_amount}
		return {'value': value}
	
	def onchange_additional_cost(self, cr, uid, ids, additional_cost):
		value = {'r_additional_cost':0}
		if additional_cost:
			value = {'r_additional_cost': additional_cost}
		return {'value': value}
	
	def onchange_gst(self, cr, uid, ids, hsn_no):
		value = {'gst':''}
		if hsn_no:
			hsn_rec = self.pool.get('kg.hsn.master').browse(cr,uid,hsn_no)
			value = {'gst': hsn_rec.igst_id.id}
		return {'value': value}
	
	def onchange_cust_in_ex(self, cr, uid, ids, r_customer_discount):
		value = {'cust_in_ex':''}
		if r_customer_discount > 0.00:
			value = {'cust_in_ex': 'inclusive'}
		return {'value': value}
	
	def entry_update(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		self.write(cr, uid, ids, {
									'sam_ratio':entry.sam_ratio,
									#~ 'r_cpo_amount':entry.sam_ratio,
									
								})
		return True
		
	#~ def onchange_gst(self, cr, uid, ids, pump_id,hsn_no, gst, context=None):
		#~ value = {'hsn_no': '','gst': ''}
		#~ pump_rec = self.pool.get('kg.pumpmodel.master').browse(cr,uid,pump_id)
		#~ 
		#~ sql_check = """ select hsn_id from hsn_no_product where hsn_id = %s and pump_id = %s""" %(hsn_no,pump_id)
		#~ cr.execute(sql_check)
		#~ data = cr.dictfetchall()
		#~ print"datadata",data
		#~ if data:
			#~ pass
		#~ else:
			#~ sql_check_1 = """ select hsn_id from hsn_no_product where hsn_id != %s and pump_id = %s""" %(hsn_no,pump_id)
			#~ cr.execute(sql_check_1)
			#~ data_1 = cr.dictfetchall()
			#~ print"data_1data_1",data_1
			#~ hsn = ''
			#~ for item in data_1:
				#~ print"item['hsn_id']",item['hsn_id']
				#~ hsn_rec = self.pool.get('kg.hsn.master').browse(cr,uid,item['hsn_id'])
				#~ hsn = hsn + ',' +str(hsn_rec.name)
				#~ print"hsnhsnhsn**********",hsn
			#~ raise osv.except_osv(_('Warning!'),_('You can choose only HSN %s'%(hsn)))
			#~ if hsn_no:
				#~ hsn_rec = self.pool.get('kg.hsn.master').browse(cr,uid,hsn_no)
				#~ if gst == hsn_rec.igst_id.id:
					#~ pass
				#~ else:
					#~ raise osv.except_osv(_('Warning!'),_('You can choose only %s '%(hsn_rec.igst_id.name)))
				#~ value = {'gst': hsn_rec.igst_id.id}
		#~ return {'value': value}
	
ch_pump_offer()

class ch_pump_offer_development(osv.osv):
		
	_name = "ch.pump.offer.development"
	_description = "Ch Pump Offer Development"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('ch.pump.offer', 'Pump Offer', ondelete='cascade'),
		
		## Module Requirement Fields
		
		'position_no': fields.char('Position No.'),
		'pattern_no': fields.char('Pattern No.'),
		'pattern_name': fields.char('Pattern Name'),
		'material_code': fields.char('Material Code'),
		'moc_id': fields.many2one('kg.moc.master','MOC',domain="[('state','not in',('reject','cancel'))]"),
		'csd_no': fields.char('CSD No.', size=128),
		'qty':fields.integer('Quantity'),
		'is_applicable': fields.boolean('Is Applicable'),
		'prime_cost': fields.float('Prime Cost'),
		
	}
	
ch_pump_offer_development()

class ch_supervision_offer(osv.osv):
	
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
				#~ 'pump_price': 0.0,
				#~ 'tot_price': 0.0,
				
			}
			print"line.prime_cost",line.prime_cost
			print"line.sam_ratio",line.sam_ratio
			sam_ratio_tot = line.header_id.supervision_amount * line.sam_ratio
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
			net_amount = tot_price
			print"net_amountnet_amount",net_amount
			
			res[line.id]['sam_ratio_tot'] = sam_ratio_tot
			res[line.id]['dealer_discount_tot'] = dealer_discount_tot
			res[line.id]['customer_discount_tot'] = customer_discount_tot
			res[line.id]['spl_discount_tot'] = spl_discount_tot
			res[line.id]['tax_tot'] = tax_tot
			res[line.id]['p_f_tot'] = p_f_tot
			res[line.id]['freight_tot'] = freight_tot
			res[line.id]['insurance_tot'] = insurance_tot
			#~ res[line.id]['pump_price_tot'] = pump_price_tot
			#~ res[line.id]['tot_price'] = tot_price
			res[line.id]['net_amount'] = net_amount
			
		return res
	
	_name = "ch.supervision.offer"
	_description = "Ch Supervision Offer"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('kg.crm.offer', 'Offer No.', ondelete='cascade'),
		
		## Module Requirement Fields
		
		'offer_id':fields.many2one('kg.crm.offer', 'Offer'),
		'prime_cost': fields.float('Supervision Amount'),
		'per_pump_prime_cost': fields.float('Per Pump Prime Cost'),
		'sam_ratio': fields.float('Sam Ratio'),
		'dealer_discount': fields.float('Dealer Discount(%)'),
		'customer_discount': fields.float('Customer Discount(%)'),
		'special_discount': fields.float('Special Discount(%)'),
		'tax': fields.float('Tax(%)'),
		'p_f': fields.float('P&F(%)'),
		'freight': fields.float('Freight(%)'),
		'insurance': fields.float('Insurance(%)'),
		'ed': fields.float('ED(%)'),
		'agent_com': fields.float('Agent Commission(%)'),
		'supervision_amount': fields.float('Supervision(Rs.)'),
		'wo_line_id': fields.many2one('ch.work.order.details','WO Line'),
		#~ 'total_price': fields.float('Total Price(%)'),
		
		'tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Price',multi="sums",store=True),	
		'sam_ratio_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Sam Ratio',multi="sums",store=True),	
		'dealer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),	
		'customer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),	
		'spl_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Special Discount Value',multi="sums",store=True),	
		'tax_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Tax',multi="sums",store=True),	
		'p_f_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F',multi="sums",store=True),	
		'freight_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),	
		'insurance_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),	
		#~ 'pump_price_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Pump Price',multi="sums",store=True),	
		'net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),	
		
	}
	
	def default_get(self, cr, uid, fields, context=None):
		return context
	
ch_supervision_offer()


class ch_spare_offer(osv.osv):
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		sam_ratio_tot = dealer_discount_tot = customer_discount_tot = spl_discount_tot = tax_tot = p_f_tot = freight_tot = insurance_tot = pump_price_tot = supervision_tot = tot_price = net_amount = 0
		i_tot = k_tot = m_tot = p_tot = r_tot = prime_cost = r_dealer_discount = r_net_amt_tot = r_freight_ex_tot = 0
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
				'prime_cost': 0.0,
				
			}
			
			print"line.prime_cost",line.prime_cost
			print"line.sam_ratio",line.sam_ratio
			sam_ratio_tot = round(line.prime_cost * line.sam_ratio,2)
			print"sam_ratio_totsam_ratio_tot",sam_ratio_tot
			dealer_discount = round(sam_ratio_tot / (1-line.dealer_discount/100.00),2)
			dealer_discount_tot = round(dealer_discount - sam_ratio_tot,2)
			print"dealer_discount_totdealer_discount_tot",dealer_discount_tot
			spl_discount = round(dealer_discount / (1-line.special_discount/100.00),2)
			spl_discount_tot = round(spl_discount - dealer_discount,2)
			print"spl_discount_totspl_discount_tot",spl_discount_tot
			if line.p_f_in_ex == 'inclusive':
				p_f = round(spl_discount / (1-line.p_f/100.00),2)
			else:
				p_f = spl_discount
			p_f_tot = round(p_f - spl_discount,2)
			print"p_f_totp_f_tot",p_f_tot
			if line.freight_in_ex == 'inclusive':
				insurance = round(p_f / (1-line.insurance/100.00),2)
			else:
				insurance = p_f
			insurance_tot = round(insurance - p_f,2)
			print"insurance_tot",insurance_tot
			if line.freight_in_ex == 'inclusive':
				freight = round(insurance / (1-line.freight/100.00),2)
			else:
				freight = insurance
			freight_tot = round(freight - insurance,2)
			print"freight_tot",freight_tot
			pump_price_tot = freight
			print"pump_price_tot",pump_price_tot
			customer_discount = round(pump_price_tot / (1-line.customer_discount/100.00),2)
			customer_discount_tot = round(customer_discount - pump_price_tot,2)
			print"customer_discount_tot",customer_discount_tot
			if line.gst:
				tax = round(customer_discount / (1-(line.gst.amount*100)/100.00),2)
			else:
				tax = customer_discount
			print"tax",tax
			tax_tot = round(tax - customer_discount,2)
			print"tax_tottax_tot",tax_tot
			tot_price = round(customer_discount)
			#~ tot_price = tax
			print"tot_price",tot_price
			
			#~ r_customer_discount_tot = round((tot_price * line.r_customer_discount) / 100.00,2)
			r_customer_discount_tot = round((line.r_cpo_amount * line.r_customer_discount) / 100.00)
			print"r_customer_discount_tot",r_customer_discount_tot
			r_pump_price_tot = round(line.r_cpo_amount - r_customer_discount_tot)
			print"r_pump_price_tot",r_pump_price_tot
			if line.gst:
				r_tax_tot = round(((r_pump_price_tot + line.r_p_f_ex_tot)*(line.gst.amount*100))/100.00)
			else:
				r_tax_tot = 0 
			print"r_tax_tot",r_tax_tot
			if line.r_freight_in_ex == 'inclusive':
				r_freight_tot = round((r_pump_price_tot*line.r_freight)/100.00)
				r_freight_ex_tot = 0
			elif line.r_freight_in_ex == 'exclusive':
				r_freight_ex_tot = round((r_pump_price_tot*line.r_freight)/100.00)
				r_freight_tot = 0
			else:
				r_freight_tot = 0
				r_freight_ex_tot = 0
			print"r_freight_tot",r_freight_tot
			if line.r_insurance_in_ex == 'inclusive':
				r_insurance_tot = round((r_pump_price_tot*line.r_insurance)/100.00)
			else:
				r_insurance_tot = 0
			print"r_insurance_tot",r_insurance_tot
			if line.r_p_f_in_ex == 'inclusive':
				r_p_f_tot = round((r_pump_price_tot*line.r_p_f)/100.00)
				r_p_f_ex_tot = 0
			elif line.r_p_f_in_ex == 'exclusive':
				r_p_f_ex_tot = round((r_pump_price_tot*line.r_p_f)/100.00)
				r_p_f_tot = 0
			else:
				r_p_f_tot = 0
				r_p_f_ex_tot = 0
			print"r_p_f_tot",r_p_f_tot
			r_spl_discount_tot = round((r_pump_price_tot*line.r_special_discount) / 100.00)
			print"r_spl_discount_tot",r_spl_discount_tot
			r_spl_discount = r_pump_price_tot - r_spl_discount_tot - r_freight_tot - r_insurance_tot - r_p_f_tot
			print"r_spl_discount",r_spl_discount
			r_dealer_discount = r_spl_discount
			print"r_dealer_discount",r_dealer_discount
			r_dealer_discount_tot = round((r_dealer_discount*line.r_dealer_discount) / 100.00)
			print"r_dealer_discount_tot",r_dealer_discount_tot
			r_sam_ratio_tot = r_pump_price_tot - r_spl_discount_tot - r_dealer_discount_tot - r_p_f_tot - r_insurance_tot - r_freight_tot
			print"r_sam_ratio_tot",r_sam_ratio_tot
			print"line.prime_costline.prime_cost",line.prime_cost
			r_sam_ratio = r_sam_ratio_tot / (line.prime_cost or 1)
			print"r_sam_ratio",r_sam_ratio
			
			r_net_amt_tot =  line.r_cpo_amount_tot - r_customer_discount_tot
			
			res[line.id]['sam_ratio_tot'] = sam_ratio_tot
			res[line.id]['dealer_discount_tot'] = dealer_discount_tot
			res[line.id]['spl_discount_tot'] = spl_discount_tot
			res[line.id]['p_f_tot'] = p_f_tot
			res[line.id]['insurance_tot'] = insurance_tot
			res[line.id]['freight_tot'] = freight_tot
			res[line.id]['pump_price_tot'] = pump_price_tot
			res[line.id]['customer_discount_tot'] = customer_discount_tot
			res[line.id]['tax_tot'] = tax_tot
			res[line.id]['supervision_tot'] = line.supervision_amount
			res[line.id]['tot_price'] = tot_price
			res[line.id]['net_amount'] = tot_price
			
			res[line.id]['r_sam_ratio'] = r_sam_ratio
			res[line.id]['r_works_value'] = r_sam_ratio_tot
			res[line.id]['r_sam_ratio_tot'] = r_sam_ratio_tot
			res[line.id]['r_dealer_discount_val'] = r_dealer_discount
			res[line.id]['r_dealer_discount_tot'] = r_dealer_discount_tot
			res[line.id]['r_spl_discount_tot'] = r_spl_discount_tot
			res[line.id]['r_p_f_tot'] = r_p_f_tot
			res[line.id]['r_p_f_ex_tot'] = r_p_f_ex_tot
			res[line.id]['r_insurance_tot'] = r_insurance_tot
			res[line.id]['r_freight_tot'] = r_freight_tot
			res[line.id]['r_freight_ex_tot'] = r_freight_ex_tot
			res[line.id]['r_pump_price_tot'] = r_pump_price_tot
			res[line.id]['r_net_amt_tot'] = r_net_amt_tot
			res[line.id]['r_customer_discount_tot'] = r_customer_discount_tot
			res[line.id]['r_tax_tot'] = r_tax_tot
			#~ res[line.id]['r_tot_price'] = tot_price
			if line.cust_in_ex == 'inclusive':
				res[line.id]['r_net_amount'] = r_pump_price_tot + r_p_f_ex_tot + r_tax_tot
			else:
				res[line.id]['r_net_amount'] = r_pump_price_tot + r_customer_discount_tot + r_p_f_ex_tot + r_tax_tot
			res[line.id]['prime_cost'] = (line.per_spare_prime_cost * line.qty) + line.additional_cost
			print"line.r_cpo_amount",line.r_cpo_amount
			enq_no = line.header_id.enquiry_no
			print"enq_noenq_no",enq_no
			enq_ids = self.pool.get('kg.crm.enquiry').search(cr,uid,[('name','=',enq_no),('state','!=','revised')])
			print"enq_ids",enq_ids
			if enq_ids:
				enq_rec = self.pool.get('kg.crm.enquiry').browse(cr,uid,enq_ids[0])
				print"enq_recenq_rec",enq_rec.state
			print"tot_pricetot_price",tot_price
			if line.cpo_quote_cust == 'quoted':
				cr.execute('''update ch_spare_offer set r_cpo_amount = %s,r_cpo_amount_tot = %s where id = %s ''',(tot_price,tot_price,line.id))
			elif line.cpo_quote_cust == 'cust_po':
				cr.execute('''update ch_spare_offer set r_cpo_amount = %s,r_cpo_amount_tot = %s where id = %s ''',(line.r_cpo_amount,line.r_cpo_amount,line.id))
		
		return res
	"""
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		sam_ratio_tot = dealer_discount_tot = customer_discount_tot = spl_discount_tot = tax_tot = p_f_tot = freight_tot = insurance_tot = pump_price_tot = tot_price = net_amount = 0
		i_tot = k_tot = m_tot = p_tot = r_tot = prime_cost = 0
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
				'prime_cost': 0.0,
				
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
			tax_tot = (m_tot / 100) * (line.gst.amount or 0 *100)
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
			tot_price = pump_price_tot / line.qty
			print"tot_pricetot_price",tot_price
			#~ net_amount = tot_price * 1
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
			res[line.id]['prime_cost'] = (line.per_spare_prime_cost * line.qty) + line.additional_cost
			
		return res"""
	
	_name = "ch.spare.offer"
	_description = "Ch Spare Offer"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('kg.crm.offer', 'Offer', ondelete='cascade'),
		
		## Module Requirement Fields
		
		'offer_id':fields.many2one('kg.crm.offer', 'Offer'),
		'uom_id':fields.many2one('product.uom','UOM'),
		'qty':fields.integer('Quantity'),
		'item_code': fields.char('Item Code'),
		'item_name': fields.char('Item Name'),
		'hsn_no': fields.many2one('kg.hsn.master','HSN No.'),
		'gst': fields.many2one('account.tax','GST Tax'),
		'customer_id':fields.many2one('res.partner','Customer Name'),
		'moc_id': fields.many2one('kg.moc.master','MOC Name'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No'),
		'ms_id': fields.many2one('kg.machine.shop','MS Name'),
		'bot_id': fields.many2one('kg.machine.shop','BOT Name'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),
		'pumpseries_id': fields.many2one('kg.pumpseries.master','Pump Series'),
		'moc_const_id': fields.many2one('kg.moc.construction','MOC Construction'),
		'per_spare_prime_cost': fields.float('Per Spare Prime Cost'),
		'additional_cost': fields.float('Additional Cost'),
		'additional_cost_remark': fields.text('Additional Cost Remark'),
		'prime_cost': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Prime Cost',multi="sums",store=True),
		#~ 'prime_cost': fields.float('Prime Cost'),
		'sam_ratio': fields.float('Sam Ratio'),
		'dealer_discount': fields.float('Dealer Discount(%)'),
		'customer_discount': fields.float('Customer Discount(%)'),
		'special_discount': fields.float('Special Discount(%)'),
		'tax': fields.float('Tax(%)'),
		'p_f': fields.float('P&F(%)'),
		'freight': fields.float('Freight(%)'),
		'insurance': fields.float('Insurance(%)'),
		'p_f_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'P&F'),
		'freight_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Freight'),
		'insurance_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Insurance'),
		'tax_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Tax'),
		'ed_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'ED'),
		'ed': fields.float('ED(%)'),
		'agent_com': fields.float('Agent Commission(%)'),
		'supervision_amount': fields.float('Supervision(Rs.)'),
		'works_value': fields.float('Works Value'),
		'works_value_flag': fields.boolean('Works Value Flag'),
		'sam_ratio_flag': fields.boolean('Sam Ratio Flag'),
		'total_price': fields.float('Total Price'),
		'spare_offer_line_id': fields.many2one('ch.spare.offer','Spare Offer Line Id'),
		'moc_changed_flag': fields.boolean('MOC Changed'),
		'off_name': fields.char('Offer Name'),
		'material_code': fields.char('Material Code'),
		
		'r_agent_com': fields.float('Agent Commission(%)'),
		'r_dealer_discount': fields.float('Dealer Discount(%)'),
		'r_customer_discount': fields.float('Customer Discount(%)'),
		'cust_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Customer Discount'),
		'r_special_discount': fields.float('Special Discount(%)'),
		'r_p_f': fields.float('P&F(%)'),
		'r_freight': fields.float('Freight(%)'),
		'r_insurance': fields.float('Insurance(%)'),
		'r_p_f_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'P&F'),
		'r_freight_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Freight'),
		'r_insurance_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Insurance'),
		'r_supervision_amount': fields.float('Supervision(Rs.)'),
		'r_additional_cost': fields.float('Additional Cost'),
		'r_cpo_amount': fields.float('CPO(Total Qty)'),
		'r_cpo_amount_tot': fields.float('CPO',readonly=True),
		'cpo_quote_cust': fields.selection([('quoted','Quoted price'),('cust_po','Customer price')],'CPO Value'),
		
		'tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Price',multi="sums",store=True),	
		'sam_ratio_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Works Value',multi="sums",store=True),	
		'dealer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),	
		'customer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),	
		'spl_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Special Discount Value',multi="sums",store=True),	
		'tax_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='GST',multi="sums",store=True),	
		'p_f_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F',multi="sums",store=True),	
		'freight_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),	
		'insurance_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),	
		'pump_price_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Pump Price',multi="sums",store=True),	
		'net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Quoted Value(GST Extra)',multi="sums",store=True),	
		
		'r_sam_ratio': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Sam Ratio(%)',multi="sums",store=True),
		'r_works_value': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Works Value',multi="sums",store=True),
		'r_sam_ratio_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Works Value',multi="sums",store=True),
		'r_dealer_discount_val': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value Consider',multi="sums",store=True),
		'r_dealer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),
		'r_customer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),
		'r_spl_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Special Discount Value',multi="sums",store=True),
		'r_tax_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='GST',multi="sums",store=True),
		'r_p_f_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F(Inc)',multi="sums",store=True),
		'r_p_f_ex_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F(Exc)',multi="sums",store=True),
		'r_freight_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),
		'r_freight_ex_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight Ex',multi="sums",store=True),
		'r_insurance_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),
		'r_pump_price_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Pump Price',multi="sums",store=True),
		'r_net_amt_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),
		'r_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Grand Total',multi="sums",store=True),
		
		## Child Tables Declaration
		
		'enquiry_line_id': fields.many2one('ch.kg.crm.pumpmodel','Enquiry Line'),
		'off_fou_id': fields.related('enquiry_line_id','line_ids', type='one2many', relation='ch.kg.crm.foundry.item', string='Foundry Items'),
		'off_ms_id': fields.related('enquiry_line_id','line_ids_a', type='one2many', relation='ch.kg.crm.machineshop.item', string='MS Items'),
		'off_bot_id': fields.related('enquiry_line_id','line_ids_b', type='one2many', relation='ch.kg.crm.bot', string='BOT Items'),
		
	}
	
	_defaults = {
		
		'cpo_quote_cust':'quoted',
		'cust_in_ex':'inclusive',
		
	}
	
	def onchange_sam_ratio(self, cr, uid, ids, prime_cost, works_value, works_value_flag, sam_ratio, sam_ratio_flag, context=None):
		value = {'works_value':'','sam_ratio':''}
		if works_value_flag == True and works_value:
			value = {'sam_ratio': float(works_value)/float(prime_cost),'r_sam_ratio':float(works_value)/float(prime_cost)}
		elif sam_ratio_flag == True and sam_ratio:
			value = {'works_value': prime_cost * sam_ratio,'r_sam_ratio':sam_ratio}
		return {'value': value}
	
	def onchange_delaer_discount(self, cr, uid, ids, delaer_discount):
		value = {'r_delaer_discount':0}
		if delaer_discount:
			value = {'r_dealer_discount': delaer_discount}
		return {'value': value}
	
	def onchange_special_discount(self, cr, uid, ids, special_discount):
		value = {'r_special_discount':0}
		if special_discount:
			value = {'r_special_discount': special_discount}
		return {'value': value}
	
	def onchange_p_f(self, cr, uid, ids, p_f, p_f_in_ex):
		value = {'r_p_f':0,'r_p_f_in_ex':''}
		if p_f and p_f_in_ex:
			value = {'r_p_f': p_f,'r_p_f_in_ex': p_f_in_ex}
		return {'value': value}
	
	def onchange_freight(self, cr, uid, ids, freight, freight_in_ex):
		value = {'r_freight':0,'r_freight_in_ex':''}
		if freight and freight_in_ex:
			value = {'r_freight': freight,'r_freight_in_ex': freight_in_ex}
		return {'value': value}
	
	def onchange_insurance(self, cr, uid, ids, insurance, insurance_in_ex):
		value = {'r_insurance':0,'r_insurance_in_ex':''}
		if insurance and insurance_in_ex:
			value = {'r_insurance': insurance,'r_insurance_in_ex': insurance_in_ex}
		return {'value': value}
	
	def onchange_supervision(self, cr, uid, ids, supervision_amount):
		value = {'r_supervision_amount':0}
		if supervision_amount:
			value = {'r_supervision_amount': supervision_amount}
		return {'value': value}
	
	def onchange_additional_cost(self, cr, uid, ids, additional_cost):
		value = {'r_additional_cost':0}
		if additional_cost:
			value = {'r_additional_cost': additional_cost}
		return {'value': value}
	
	def onchange_gst(self, cr, uid, ids, hsn_no):
		value = {'gst':''}
		if hsn_no:
			hsn_rec = self.pool.get('kg.hsn.master').browse(cr,uid,hsn_no)
			value = {'gst': hsn_rec.igst_id.id}
		return {'value': value}
	
	def onchange_cust_in_ex(self, cr, uid, ids, r_customer_discount):
		value = {'cust_in_ex':''}
		if r_customer_discount > 0.00:
			value = {'cust_in_ex': 'inclusive'}
		return {'value': value}
	
	def entry_update(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		self.write(cr, uid, ids, {
									'sam_ratio':entry.sam_ratio,
									#~ 'r_cpo_amount':entry.sam_ratio,
									
								})
		return True
	
ch_spare_offer()

class ch_accessories_offer(osv.osv):
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		sam_ratio_tot = dealer_discount_tot = customer_discount_tot = spl_discount_tot = tax_tot = p_f_tot = freight_tot = insurance_tot = pump_price_tot = supervision_tot = tot_price = net_amount = 0
		i_tot = k_tot = m_tot = p_tot = r_tot = prime_cost = r_dealer_discount = r_net_amt_tot = r_freight_ex_tot = 0
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
				'prime_cost': 0.0,
				
			}
			
			print"line.prime_cost",line.prime_cost
			print"line.sam_ratio",line.sam_ratio
			sam_ratio_tot = round(line.prime_cost * line.sam_ratio,2)
			print"sam_ratio_totsam_ratio_tot",sam_ratio_tot
			dealer_discount = round(sam_ratio_tot / (1-line.dealer_discount/100.00),2)
			dealer_discount_tot = round(dealer_discount - sam_ratio_tot,2)
			print"dealer_discount_totdealer_discount_tot",dealer_discount_tot
			spl_discount = round(dealer_discount / (1-line.special_discount/100.00),2)
			spl_discount_tot = round(spl_discount - dealer_discount,2)
			print"spl_discount_totspl_discount_tot",spl_discount_tot
			if line.p_f_in_ex == 'inclusive':
				p_f = round(spl_discount / (1-line.p_f/100.00),2)
			else:
				p_f = spl_discount
			p_f_tot = round(p_f - spl_discount,2)
			print"p_f_totp_f_tot",p_f_tot
			if line.freight_in_ex == 'inclusive':
				insurance = round(p_f / (1-line.insurance/100.00),2)
			else:
				insurance = p_f
			insurance_tot = round(insurance - p_f,2)
			print"insurance_tot",insurance_tot
			if line.freight_in_ex == 'inclusive':
				freight = round(insurance / (1-line.freight/100.00),2)
			else:
				freight = insurance
			freight_tot = round(freight - insurance,2)
			print"freight_tot",freight_tot
			pump_price_tot = freight
			print"pump_price_tot",pump_price_tot
			customer_discount = round(pump_price_tot / (1-line.customer_discount/100.00),2)
			customer_discount_tot = round(customer_discount - pump_price_tot,2)
			print"customer_discount_tot",customer_discount_tot
			if line.gst:
				tax = round(customer_discount / (1-(line.gst.amount*100)/100.00),2)
			else:
				tax = customer_discount
			print"tax",tax
			tax_tot = round(tax - customer_discount,2)
			print"tax_tottax_tot",tax_tot
			tot_price = round(customer_discount)
			#~ tot_price = tax
			print"tot_price",tot_price
			
			#~ r_customer_discount_tot = round((tot_price * line.r_customer_discount) / 100.00,2)
			r_customer_discount_tot = round((line.r_cpo_amount * line.r_customer_discount) / 100.00)
			print"r_customer_discount_tot",r_customer_discount_tot
			r_pump_price_tot = round(line.r_cpo_amount - r_customer_discount_tot)
			print"r_pump_price_tot",r_pump_price_tot
			if line.gst:
				r_tax_tot = round(((r_pump_price_tot + line.r_p_f_ex_tot)*(line.gst.amount*100))/100.00)
			else:
				r_tax_tot = 0 
			print"r_tax_tot",r_tax_tot
			if line.r_freight_in_ex == 'inclusive':
				r_freight_tot = round((r_pump_price_tot*line.r_freight)/100.00)
				r_freight_ex_tot = 0
			elif line.r_freight_in_ex == 'exclusive':
				r_freight_ex_tot = round((r_pump_price_tot*line.r_freight)/100.00)
				r_freight_tot = 0
			else:
				r_freight_tot = 0
				r_freight_ex_tot = 0
			print"r_freight_tot",r_freight_tot
			if line.r_insurance_in_ex == 'inclusive':
				r_insurance_tot = round((r_pump_price_tot*line.r_insurance)/100.00)
			else:
				r_insurance_tot = 0
			print"r_insurance_tot",r_insurance_tot
			if line.r_p_f_in_ex == 'inclusive':
				r_p_f_tot = round((r_pump_price_tot*line.r_p_f)/100.00)
				r_p_f_ex_tot = 0
			elif line.r_p_f_in_ex == 'exclusive':
				r_p_f_ex_tot = round((r_pump_price_tot*line.r_p_f)/100.00)
				r_p_f_tot = 0
			else:
				r_p_f_tot = 0
				r_p_f_ex_tot = 0
			print"r_p_f_tot",r_p_f_tot
			r_spl_discount_tot = round((r_pump_price_tot*line.r_special_discount) / 100.00)
			print"r_spl_discount_tot",r_spl_discount_tot
			r_spl_discount = r_pump_price_tot - r_spl_discount_tot - r_freight_tot - r_insurance_tot - r_p_f_tot
			print"r_spl_discount",r_spl_discount
			r_dealer_discount = r_spl_discount
			print"r_dealer_discount",r_dealer_discount
			r_dealer_discount_tot = round((r_dealer_discount*line.r_dealer_discount) / 100.00)
			print"r_dealer_discount_tot",r_dealer_discount_tot
			r_sam_ratio_tot = r_pump_price_tot - r_spl_discount_tot - r_dealer_discount_tot - r_p_f_tot - r_insurance_tot - r_freight_tot
			print"r_sam_ratio_tot",r_sam_ratio_tot
			print"line.prime_costline.prime_cost",line.prime_cost
			r_sam_ratio = r_sam_ratio_tot / (line.prime_cost or 1)
			print"r_sam_ratio",r_sam_ratio
			
			r_net_amt_tot =  line.r_cpo_amount_tot - r_customer_discount_tot
			
			res[line.id]['sam_ratio_tot'] = sam_ratio_tot
			res[line.id]['dealer_discount_tot'] = dealer_discount_tot
			res[line.id]['spl_discount_tot'] = spl_discount_tot
			res[line.id]['p_f_tot'] = p_f_tot
			res[line.id]['insurance_tot'] = insurance_tot
			res[line.id]['freight_tot'] = freight_tot
			res[line.id]['pump_price_tot'] = pump_price_tot
			res[line.id]['customer_discount_tot'] = customer_discount_tot
			res[line.id]['tax_tot'] = tax_tot
			res[line.id]['supervision_tot'] = line.supervision_amount
			res[line.id]['tot_price'] = tot_price
			res[line.id]['net_amount'] = tot_price
			
			res[line.id]['r_sam_ratio'] = r_sam_ratio
			res[line.id]['r_works_value'] = r_sam_ratio_tot
			res[line.id]['r_sam_ratio_tot'] = r_sam_ratio_tot
			res[line.id]['r_dealer_discount_val'] = r_dealer_discount
			res[line.id]['r_dealer_discount_tot'] = r_dealer_discount_tot
			res[line.id]['r_spl_discount_tot'] = r_spl_discount_tot
			res[line.id]['r_p_f_tot'] = r_p_f_tot
			res[line.id]['r_p_f_ex_tot'] = r_p_f_ex_tot
			res[line.id]['r_insurance_tot'] = r_insurance_tot
			res[line.id]['r_freight_tot'] = r_freight_tot
			res[line.id]['r_freight_ex_tot'] = r_freight_ex_tot
			res[line.id]['r_pump_price_tot'] = r_pump_price_tot
			res[line.id]['r_net_amt_tot'] = r_net_amt_tot
			res[line.id]['r_customer_discount_tot'] = r_customer_discount_tot
			res[line.id]['r_tax_tot'] = r_tax_tot
			#~ res[line.id]['r_tot_price'] = tot_price
			if line.cust_in_ex == 'inclusive':
				res[line.id]['r_net_amount'] = r_pump_price_tot + r_p_f_ex_tot + r_tax_tot
			else:
				res[line.id]['r_net_amount'] = r_pump_price_tot + r_customer_discount_tot + r_p_f_ex_tot + r_tax_tot
			res[line.id]['prime_cost'] = (line.per_access_prime_cost * line.qty) + line.additional_cost
			print"line.r_cpo_amount",line.r_cpo_amount
			enq_no = line.header_id.enquiry_no
			print"enq_noenq_no",enq_no
			enq_ids = self.pool.get('kg.crm.enquiry').search(cr,uid,[('name','=',enq_no),('state','!=','revised')])
			print"enq_ids",enq_ids
			if enq_ids:
				enq_rec = self.pool.get('kg.crm.enquiry').browse(cr,uid,enq_ids[0])
				print"enq_recenq_rec",enq_rec.state
			print"tot_pricetot_price",tot_price
			if line.cpo_quote_cust == 'quoted':
				cr.execute('''update ch_accessories_offer set r_cpo_amount = %s,r_cpo_amount_tot = %s where id = %s ''',(tot_price,tot_price,line.id))
			elif line.cpo_quote_cust == 'cust_po':
				cr.execute('''update ch_accessories_offer set r_cpo_amount = %s,r_cpo_amount_tot = %s where id = %s ''',(line.r_cpo_amount,line.r_cpo_amount,line.id))
		
		return res
	"""
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		sam_ratio_tot = dealer_discount_tot = customer_discount_tot = spl_discount_tot = tax_tot = p_f_tot = freight_tot = insurance_tot = pump_price_tot = tot_price = net_amount = 0
		i_tot = k_tot = m_tot = p_tot = r_tot = prime_cost = 0
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
				'prime_cost': 0.0,
				
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
			tax_tot = (m_tot / 100) * (line.gst.amount or 0 *100)
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
			tot_price = pump_price_tot / line.qty
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
			res[line.id]['prime_cost'] = (line.per_access_prime_cost * line.qty) + line.additional_cost
			
		return res"""
	
	_name = "ch.accessories.offer"
	_description = "Ch Accessories Offer"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('kg.crm.offer', 'Offer', ondelete='cascade'),
		
		## Module Requirement Fields
		
		'offer_id':fields.many2one('kg.crm.offer', 'Offer'),
		'enquiry_line_id': fields.many2one('ch.kg.crm.pumpmodel','Enquiry Line'),
		'access_id':fields.many2one('kg.accessories.master', 'Item Name'),
		'hsn_no': fields.many2one('kg.hsn.master','HSN No.'),
		'gst': fields.many2one('account.tax','GST Tax'),
		'customer_id':fields.many2one('res.partner','Customer Name'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),
		'moc_id':fields.many2one('kg.moc.master', 'MOC'),
		'qty':fields.integer('Quantity'),
		#~ 'prime_cost': fields.float('Prime Cost'),
		'additional_cost': fields.float('Additional Cost'),
		'additional_cost_remark': fields.text('Additional Cost Remark'),
		'prime_cost': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Prime Cost',multi="sums",store=True),
		'per_access_prime_cost': fields.float('Per Access Prime Cost'),
		'sam_ratio': fields.float('Sam Ratio'),
		'dealer_discount': fields.float('Dealer Discount(%)'),
		'customer_discount': fields.float('Customer Discount(%)'),
		'special_discount': fields.float('Special Discount(%)'),
		'tax': fields.float('Tax(%)'),
		'p_f': fields.float('P&F(%)'),
		'freight': fields.float('Freight(%)'),
		'insurance': fields.float('Insurance(%)'),
		'p_f_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'P&F'),
		'freight_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Freight'),
		'insurance_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Insurance'),
		'tax_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Tax'),
		'ed_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'ED'),
		'ed': fields.float('ED(%)'),
		'agent_com': fields.float('Agent Commission(%)'),
		'supervision_amount': fields.float('Supervision(Rs.)'),
		'works_value': fields.float('Works Value'),
		'works_value_flag': fields.boolean('Works Value Flag'),
		'sam_ratio_flag': fields.boolean('Sam Ratio Flag'),
		'pump_price': fields.float('Pump Price'),
		'total_price': fields.float('Total Price'),
		'moc_changed_flag': fields.boolean('MOC Changed'),
		'off_name': fields.char('Offer Name'),
		
		'r_agent_com': fields.float('Agent Commission(%)'),
		'r_dealer_discount': fields.float('Dealer Discount(%)'),
		'r_customer_discount': fields.float('Customer Discount(%)'),
		'cust_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Customer Discount'),
		'r_special_discount': fields.float('Special Discount(%)'),
		'r_p_f': fields.float('P&F(%)'),
		'r_freight': fields.float('Freight(%)'),
		'r_insurance': fields.float('Insurance(%)'),
		'r_p_f_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'P&F'),
		'r_freight_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Freight'),
		'r_insurance_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Insurance'),
		'r_supervision_amount': fields.float('Supervision(Rs.)'),
		'r_additional_cost': fields.float('Additional Cost'),
		'r_cpo_amount': fields.float('CPO(Total Qty)'),
		'r_cpo_amount_tot': fields.float('CPO',readonly=True),
		'cpo_quote_cust': fields.selection([('quoted','Quoted price'),('cust_po','Customer price')],'CPO Value'),
		
		'tot_price': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total Price',multi="sums",store=True),
		'sam_ratio_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Works Value',multi="sums",store=True),
		'dealer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),
		'customer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),
		'spl_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Special Discount Value',multi="sums",store=True),
		'tax_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='GST',multi="sums",store=True),
		'p_f_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F',multi="sums",store=True),
		'freight_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),
		'insurance_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),
		'pump_price_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Pump Price',multi="sums",store=True),
		'net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Quoted Value(GST Extra)',multi="sums",store=True),
		
		'r_sam_ratio': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Sam Ratio(%)',multi="sums",store=True),
		'r_works_value': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Works Value',multi="sums",store=True),
		'r_sam_ratio_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Works Value',multi="sums",store=True),
		'r_dealer_discount_val': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value Consider',multi="sums",store=True),
		'r_dealer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Dealer Discount Value',multi="sums",store=True),
		'r_customer_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Customer Discount Value',multi="sums",store=True),
		'r_spl_discount_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Special Discount Value',multi="sums",store=True),
		'r_tax_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='GST',multi="sums",store=True),
		'r_p_f_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F(Inc)',multi="sums",store=True),
		'r_p_f_ex_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='P&F(Exc)',multi="sums",store=True),
		'r_freight_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight',multi="sums",store=True),
		'r_freight_ex_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Freight Ex',multi="sums",store=True),
		'r_insurance_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Insurance',multi="sums",store=True),
		'r_pump_price_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Pump Price',multi="sums",store=True),		
		'r_net_amt_tot': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Net Amount',multi="sums",store=True),
		'r_net_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Grand Total',multi="sums",store=True),
		
		## Child Tables Declaration
		
		'enquiry_line_access_id': fields.many2one('ch.kg.crm.accessories','Enquiry Line'),
		'off_fou_id': fields.related('enquiry_line_access_id','line_ids', type='one2many', relation='ch.crm.access.fou', string='Foundry Items'),
		'off_ms_id': fields.related('enquiry_line_access_id','line_ids_a', type='one2many', relation='ch.crm.access.ms', string='MS Items'),
		'off_bot_id': fields.related('enquiry_line_access_id','line_ids_b', type='one2many', relation='ch.crm.access.bot', string='BOT Items'),
		
	}
	
	_defaults = {
		
		'cpo_quote_cust':'quoted',
		'cust_in_ex':'inclusive',
		
	}
	
	def onchange_sam_ratio(self, cr, uid, ids, prime_cost, works_value, works_value_flag, sam_ratio, sam_ratio_flag, context=None):
		value = {'works_value':'','sam_ratio':''}
		if works_value_flag == True and works_value:
			value = {'sam_ratio': float(works_value)/float(prime_cost),'r_sam_ratio':float(works_value)/float(prime_cost)}
		elif sam_ratio_flag == True and sam_ratio:
			value = {'works_value': prime_cost * sam_ratio,'r_sam_ratio':sam_ratio}
		return {'value': value}
	
	def onchange_delaer_discount(self, cr, uid, ids, delaer_discount):
		value = {'r_delaer_discount':0}
		if delaer_discount:
			value = {'r_dealer_discount': delaer_discount}
		return {'value': value}
	
	def onchange_special_discount(self, cr, uid, ids, special_discount):
		value = {'r_special_discount':0}
		if special_discount:
			value = {'r_special_discount': special_discount}
		return {'value': value}
	
	def onchange_p_f(self, cr, uid, ids, p_f, p_f_in_ex):
		value = {'r_p_f':0,'r_p_f_in_ex':''}
		if p_f and p_f_in_ex:
			value = {'r_p_f': p_f,'r_p_f_in_ex': p_f_in_ex}
		return {'value': value}
	
	def onchange_freight(self, cr, uid, ids, freight, freight_in_ex):
		value = {'r_freight':0,'r_freight_in_ex':''}
		if freight and freight_in_ex:
			value = {'r_freight': freight,'r_freight_in_ex': freight_in_ex}
		return {'value': value}
	
	def onchange_insurance(self, cr, uid, ids, insurance, insurance_in_ex):
		value = {'r_insurance':0,'r_insurance_in_ex':''}
		if insurance and insurance_in_ex:
			value = {'r_insurance': insurance,'r_insurance_in_ex': insurance_in_ex}
		return {'value': value}
	
	def onchange_supervision(self, cr, uid, ids, supervision_amount):
		value = {'r_supervision_amount':0}
		if supervision_amount:
			value = {'r_supervision_amount': supervision_amount}
		return {'value': value}
	
	def onchange_additional_cost(self, cr, uid, ids, additional_cost):
		value = {'r_additional_cost':0}
		if additional_cost:
			value = {'r_additional_cost': additional_cost}
		return {'value': value}
	
	def onchange_gst(self, cr, uid, ids, hsn_no):
		value = {'gst':''}
		if hsn_no:
			hsn_rec = self.pool.get('kg.hsn.master').browse(cr,uid,hsn_no)
			value = {'gst': hsn_rec.igst_id.id}
		return {'value': value}
	
	def onchange_cust_in_ex(self, cr, uid, ids, r_customer_discount):
		value = {'cust_in_ex':''}
		if r_customer_discount > 0.00:
			value = {'cust_in_ex': 'inclusive'}
		return {'value': value}
	
	def entry_update(self,cr,uid,ids,context=None):
		entry = self.browse(cr,uid,ids[0])
		self.write(cr, uid, ids, {
									'sam_ratio':entry.sam_ratio,
									#~ 'r_cpo_amount':entry.sam_ratio,
									
								})
		return True
	
ch_accessories_offer()


class ch_crm_component_offer(osv.osv):
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		sam_ratio_tot = dealer_discount_tot = customer_discount_tot = spl_discount_tot = tax_tot = p_f_tot = freight_tot = insurance_tot = pump_price_tot = tot_price = net_amount = 0
		i_tot = k_tot = m_tot = p_tot = r_tot = prime_cost = 0
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
				'prime_cost': 0.0,
				
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
			tax_tot = (m_tot / 100) * (line.gst.amount or 0 *100)
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
			tot_price = pump_price_tot / line.qty
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
			res[line.id]['prime_cost'] = (line.per_spare_prime_cost * line.qty) + line.additional_cost
			
		return res
	
	_name = "ch.crm.component.offer"
	_description = "Ch CRM Component Offer"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('kg.crm.offer', 'Offer', ondelete='cascade'),
		
		## Module Requirement Fields
		
		'offer_id':fields.many2one('kg.crm.offer', 'Offer'),
		'qty':fields.integer('Quantity'),
		'item_code': fields.char('Item Code'),
		'item_name': fields.char('Item Name'),
		'hsn_no': fields.many2one('kg.hsn.master','HSN No.'),
		'gst': fields.many2one('account.tax','GST Tax'),
		'customer_id':fields.many2one('res.partner','Customer Name'),
		'moc_id': fields.many2one('kg.moc.master','MOC Name'),
		'pattern_id': fields.many2one('kg.pattern.master','Pattern No'),
		'ms_id': fields.many2one('kg.machine.shop','MS Name'),
		'bot_id': fields.many2one('kg.machine.shop','BOT Name'),
		'pump_id': fields.many2one('kg.pumpmodel.master','Pump Type'),
		'pumpseries_id': fields.many2one('kg.pumpseries.master','Pump Series'),
		'moc_const_id': fields.many2one('kg.moc.construction','MOC Construction'),
		'per_spare_prime_cost': fields.float('Per Spare Prime Cost'),
		'additional_cost': fields.float('Additional Cost'),
		'additional_cost_remark': fields.text('Additional Cost Remark'),
		'prime_cost': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Prime Cost',multi="sums",store=True),
		#~ 'prime_cost': fields.float('Prime Cost'),
		'sam_ratio': fields.float('Sam Ratio'),
		'dealer_discount': fields.float('Dealer Discount(%)'),
		'customer_discount': fields.float('Customer Discount(%)'),
		'special_discount': fields.float('Special Discount(%)'),
		'tax': fields.float('Tax(%)'),
		'p_f': fields.float('P&F(%)'),
		'freight': fields.float('Freight(%)'),
		'insurance': fields.float('Insurance(%)'),
		'p_f_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'P&F'),
		'freight_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Freight'),
		'insurance_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Insurance'),
		'tax_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'Tax'),
		'ed_in_ex': fields.selection([('inclusive','Inclusive'),('exclusive','Exclusive')],'ED'),
		'ed': fields.float('ED(%)'),
		'agent_com': fields.float('Agent Commission(%)'),
		'supervision_amount': fields.float('Supervision(Rs.)'),
		'works_value': fields.float('Works Value'),
		'works_value_flag': fields.boolean('Works Value Flag'),
		'sam_ratio_flag': fields.boolean('Sam Ratio Flag'),
		'total_price': fields.float('Total Price'),
		'spare_offer_line_id': fields.many2one('ch.spare.offer','Spare Offer Line Id'),
		'moc_changed_flag': fields.boolean('MOC Changed'),
		'off_name': fields.char('Offer Name'),
		
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
		
		## Child Tables Declaration
		
		#~ 'enquiry_id': fields.many2one('kg.crm.enquiry','Enquiry No.'),
		#~ 'off_fou_id': fields.related('enquiry_id','ch_line_ids_b', type='one2many', relation='ch.crm.component.fou', string='Foundry Items',store=True),
		#~ 'off_ms_id': fields.related('enquiry_id','ch_line_ids_c', type='one2many', relation='ch.crm.component.ms', string='MS Items',store=True),
		#~ 'off_bot_id': fields.related('enquiry_id','ch_line_ids_d', type='one2many', relation='ch.crm.component.bot', string='BOT Items',store=True),
		#~ 'off_access_id': fields.related('enquiry_id','ch_line_ids_e', type='one2many', relation='ch.crm.component.access', string='Accessories Items',store=True),
		
	}
	
	def onchange_sam_ratio(self, cr, uid, ids, prime_cost, works_value, works_value_flag, sam_ratio, sam_ratio_flag, context=None):
		value = {'works_value':'','sam_ratio':''}
		if works_value_flag == True and works_value:
			value = {'sam_ratio': float(works_value)/float(prime_cost)}
		elif sam_ratio_flag == True and sam_ratio:
			value = {'works_value': prime_cost * sam_ratio}
		return {'value': value}
	
ch_crm_component_offer()

class ch_term_offer(osv.osv):
	
	_name = "ch.term.offer"
	_description = "Ch Term Offer"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('kg.crm.offer', 'Offer', ondelete='cascade'),
		
		## Module Requirement Fields
		
		'term_id': fields.many2one('kg.offer.term','Name',domain="[('state','not in',('reject','cancel'))]"),
		'remark': fields.char('Remarks'),
		'term': fields.text('Terms'),
		
	}
	
	def onchange_term(self, cr, uid, ids, term_id, context=None):
		value = {'term':''}
		if term_id:
			term_obj = self.pool.get('kg.offer.term').search(cr,uid,[('id','=',term_id)])
			if term_obj:
				term_rec = self.pool.get('kg.offer.term').browse(cr,uid,term_obj[0])
				value = {'term': term_rec.term}
		return {'value': value}
	
ch_term_offer()


class kg_mail_compose_message(osv.osv):
	
	_name = "mail.compose.message"
	_inherit = "mail.compose.message"
	_description = "Email composition wizard"
	
	_columns = {
		
		'cc_mail' : fields.char('Cc'),
		
	}
	
	def send_mail_offer(self, cr, uid, ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		offer_id = rec.res_id
		to_mails = []
		cc_mails = []
		attachments = []
		partner_ids = rec.partner_ids
		for email in partner_ids:
			to_mails.append(email.email)
		if rec.cc_mail:
			if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", rec.cc_mail) != None:
				pass
			else:
				raise osv.except_osv('Invalid Email', 'Please enter a valid Cc mail address')
			cc_mails = [rec.cc_mail]
		template = self.pool.get('email.template').browse(cr, uid,8)
		ir_attachment_obj = self.pool.get('ir.attachment')
		attachment_ids = [attach.id for attach in rec.attachment_ids]
		if attachment_ids:
			for attach_id in attachment_ids:
				attach_rec = ir_attachment_obj.browse(cr,uid,attach_id)
				attachments.append((str(attach_rec.datas_fname), base64.b64decode(attach_rec.db_datas)))
		
		off_rec = self.pool.get('kg.crm.offer').browse(cr,uid,offer_id)
		
		res_ids = ids
		
		for res_id in res_ids:
			if off_rec.term_data:
				attachments.append(('Terms Copy.xls', base64.b64decode(off_rec.term_data)))
			if off_rec.rep_data:
				attachments.append(('Offer Copy.xls', base64.b64decode(off_rec.rep_data)))
			
			ir_mail_server = self.pool.get('ir.mail_server')
			msg = ir_mail_server.build_email(
					email_from = 'erpreport@kgcloud.org',
					email_to = to_mails,
					subject = rec.subject,
					body = rec.body,
					email_cc = cc_mails,
					attachments = attachments,
					object_id = res_id and ('%s-%s' % (res_id, 'kg.crm.offer')),
					subtype = 'html',
					subtype_alternative = 'plain')
			
			res = ir_mail_server.send_email(cr, uid, msg,mail_server_id=1, context=context)
			print "Offer Copy and Term Copy Mail Seccessfully Sent TO ---->>> ::",to_mails 
		
		return True
	
kg_mail_compose_message()

class ch_crm_off_remark(osv.osv):
	
	_name = "ch.crm.off.remark"
	_description = "Ch CRM Off Remark"
	
	_columns = {
		
		## Basic Info
		
		'header_id':fields.many2one('kg.crm.offer', 'Offer No.', ondelete='cascade'),
		'remarks':fields.text('Remarks'),
		
	}
	
ch_crm_off_remark()

class ch_crm_off_attachments(osv.osv):
	
	_name = "ch.crm.off.attachments"
	_description = "Ch CRM Off Attachments"
	
	_columns = {
		
		## Basic Info
		
		'header_id': fields.many2one('kg.crm.offer', 'Offer No.', ondelete='cascade'),
		'description': fields.char('Description'),
		'file': fields.binary('File'),
		
	}
	
ch_crm_off_attachments()
