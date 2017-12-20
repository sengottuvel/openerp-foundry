import re
from _common import rounding
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import base64

UOM_CONVERSATION = [

    ('one_dimension','One Dimension'),('two_dimension','Two Dimension')
]

class kg_product(osv.osv):
	
	_name = "product.product"
	_inherit = "product.product"
	
	_columns = {
		
		'capital': fields.boolean('Capital Goods'),
		'abc': fields.boolean('ABC Analysis'),
		'po_uom_coeff': fields.float('PO Coeff', digits=(16,10), required=True, help="One Purchase Unit of Measure = Value of(PO Coeff)UOM"),
		'product_type': fields.selection([('raw','Foundry Raw Materials'),('ms','MS Item'),('bot','BOT'),('consu', 'Consumables'),
											('capital','Capitals and Asset'),('service','Service Items'),('coupling','Coupling'),
											('mechanical_seal','Mechanical Seal'),('primemover','Prime mover')], 'Product Type',required=True,readonly=False,states={'approved':[('readonly',True)]}),
		'remark': fields.text('Approve/Reject Remarks',readonly=False,states={'approved':[('readonly',True)]}),
		'cancel_remark': fields.text('Cancel Remarks'),
		'od': fields.float('OD'),
		'breadth': fields.float('Breadth'),
		'length': fields.float('Length'),
		'thickness': fields.float('Thickness'),
		'weight': fields.float('Weight'),
		'po_uom_in_kgs': fields.float('PO UOM in kgs',digits=(16,10),readonly=False,states={'approved':[('readonly',True)]}),
		'uom_conversation_factor': fields.selection(UOM_CONVERSATION,'UOM Conversation Factor',required=True,readonly=False,states={'approved':[('readonly',True)]}),
		'price_type': fields.selection([('po_uom','PO UOM'),('per_kg','Per Kg')],'Price Type'),
		'coupling_type': fields.selection([('rss','RRS'),('sw','SW'),('rrl','RRL'),('swq','SWQ'),('rst','RST'),('l','L'),('lm','LM'),('lmk','LMK'),('lbc','LBC'),('f','F'),('f_0','F-0'),('sm','SM'),('bc','BC'),('ph_spacer','PH SPACER'),('ph_non_spacer','PH NON SPACER'),('metaflex_series_80','METAFLEX SERIES 80'),('e','E'),('em','EM'),('sam','SAM'),('a','A')],'Coupling Type'),
		'service_factor': fields.float('Service Factor'),
		'power_kw': fields.float('Power in KW'),
		'speed_in_rpm': fields.float('Speed In RPM'),
		'max_bore': fields.float('MAX Bore'),
		'coupling_size': fields.float('Coupling Size'),
		'spacer_length': fields.float('Spacer Length'),
		'liquid_id': fields.many2one('kg.fluid.master','Liquid'),
		'mechanical_type': fields.char('Type'),
		'operating_condition': fields.char('Operating Condition'),
		'face_combination': fields.char('Face Combination'),
		'api_plan': fields.char('API Plan'),
		'gland_placement': fields.char('Gland Placement'),
		'gland_plate': fields.selection([('w_gland_plate','With Gland Plate'),('wo_gland_plate','Without Gland Plate')],'Gland Plate'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'sleeve_dia': fields.char('Sleeve dia(MM)'),
		'coupling_make': fields.many2one('kg.brand.master','Coupling Make'),
		'is_depreciation': fields.boolean('Is Depreciation'),
		'hsn_no': fields.many2one('kg.hsn.master','HSN No.',domain="[('state','=','approved')]",readonly=False,states={'approved':[('readonly',True)]}),
		'primemover_id': fields.many2one('kg.primemover.master','Prime mover',readonly=False,states={'approved':[('readonly',True)]}),
		
		'po_copy_uom': fields.many2one('product.uom','PO Copy UOM'),
		'uom_code': fields.related('uom_id','code', type='char', string='Store UOM Code'),
		
		## Child
		
		'avg_line_ids':fields.one2many('ch.product.yearly.average.price','product_id','Line Entry'),
		
		# Entry Info
		
		'approve_date': fields.datetime('Approved Date', readonly=True),
		'app_user_id': fields.many2one('res.users', 'Approved By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'conf_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'reject_date': fields.datetime('Rejected Date', readonly=True),
		'rej_user_id': fields.many2one('res.users', 'Rejected By', readonly=True),
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		
	}
	
	_defaults = {
		
		'po_uom_coeff': 0.00,
		'user_id': lambda obj, cr, uid, context: uid,
		'entry_mode': 'manual',
		
	}
	
	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			self.write(cr, uid, ids, {'state': 'confirm','conf_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.state == 'confirm':
			access_obj = self.pool.get('kg.accessories.master')
			ch_access_obj = self.pool.get('ch.kg.accessories.master')
			if rec.is_accessories == True:
				ac_id = access_obj.search(cr,uid,[('product_id','=',rec.id)])
				if ac_id:
					old_obj = access_obj.search(cr,uid,[('product_id','=',rec.id),('state','!=','reject')])
					if old_obj:
						old_rec = access_obj.browse(cr,uid,old_obj[0])
						access_obj.write(cr,uid,old_rec.id,{'name':rec.name})
					old_rej_obj = access_obj.search(cr,uid,[('product_id','=',rec.id),('state','=','reject')])
				if old_rej_obj or not ac_id :
					old_rej_rec = access_obj.browse(cr,uid,old_rej_obj[0])
					access_id = access_obj.create(cr,uid,{'access_type':'new',
															  'name': rec.name,
															  'entry_mode': 'auto',
															  'product_id': rec.id,
														 })
					if access_id:
						ch_access_obj.create(cr,uid,{'header_id': access_id,
													 'product_id': rec.id,
													 'qty': 1,
													 'uom_id': rec.uom_po_id.id,
													 'uom_conversation_factor':rec.uom_conversation_factor,
													 'entry_mode': 'auto',
													})
			else:
				pass
			
			## Brand MOC Rate master creation process starts
			brand_moc_obj = self.pool.get('kg.brandmoc.rate')
			old_brand_moc_ids = brand_moc_obj.search(cr,uid,[('product_id','=',rec.id),('state','in',('draft','confirmed','approved'))])
		
			if rec.price_type == 'po_uom':
				uom = rec.uom_po_id.id
			elif rec.price_type == 'per_kg':
				uom_id = self.pool.get('product.uom').search(cr,uid,[('code','=','Kg')])
				uom = uom_id[0]
			if not old_brand_moc_ids:
				brand_moc_obj.create(cr,uid,{
										'product_id': rec.id,
										'name': rec.name,
										'brand_type': 'new_brand',
										'uom_id': uom,
										'category_type': rec.rate_type,
								 })
			 ## Brand MOC Rate master creation process ends
			self.write(cr, uid, ids, {'state': 'approved','app_user_id': uid, 'approve_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			if rec.cancel_remark:
				self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Warning !'),_('Enter the remarks in Cancel remarks field !!'))
		return True
	
	def entry_draft(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			self.write(cr, uid, ids, {'state': 'draft'})
		return True
	
	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirm':
			if rec.remark:
				self.write(cr, uid, ids, {'state': 'reject','rej_user_id': uid, 'reject_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Warning !'),_('Enter rejection remark in remark field !!'))
		return True
	
	def _primemover_validation(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.product_type == 'primemover':
			if rec.uom_conversation_factor != 'one_dimension':
				raise osv.except_osv(_('Warning !'),_('Kindly Configure One Dimension in UOM Conversation Factor !!'))
			if rec.uom_id.code != 'Nos' or rec.uom_po_id.code != 'Nos':
				raise osv.except_osv(_('Warning !'),_('Kindly Configure Nos in Store UOM and PO UOM !!'))
		return True
	
	def _po_coeff(self, cr, uid, ids, context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.uom_id != rec.uom_po_id and rec.po_uom_coeff == 0 and rec.state != 'approved':
			raise osv.except_osv(_('Warning !'),_('Please check and update PO Coeff for %s in product master !!'%(rec.name)))
		if rec.uom_id == rec.uom_po_id and rec.po_uom_coeff != 1:
			raise osv.except_osv(_('Warning !'),_('Both UOM is same so configure PO Coff as 1 for %s !!'%(rec.name)))
		return True	
	
	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.price_type:
			if rec.price_type == 'per_kg' and rec.po_uom_in_kgs <= 0.00:
				raise osv.except_osv(_('Warning!'),_('Configure PO UOM in kgs in (%s) !!'%(rec.name)))
		if rec.uom_id.id != rec.uom_po_id.id and rec.po_uom_coeff <= 0.00:
			raise osv.except_osv(_('Warning!'),_('Configure PO Coeff in (%s) !!'%(rec.name)))
		if rec.uom_id.code == 'Kg' and rec.po_uom_in_kgs <= 0.00:
			raise osv.except_osv(_('Warning!'),_('Configure PO UOM in kgs in (%s) !!'%(rec.name)))
		if rec.uom_id.id == rec.uom_po_id.id and rec.po_uom_coeff <= 0.00:
			raise osv.except_osv(_('Warning!'),_('Configure PO Coeff in (%s) !!'%(rec.name)))
		if rec.tolerance_applicable == True and rec.tolerance_plus <= 0:
			raise osv.except_osv(_('Warning!'),_('Tolerance(+) should be greater than zero in (%s) !!'%(rec.name)))
		if rec.price_type == 'per_kg':
			if rec.uom_po_id.code != 'Kg' and rec.uom_id.code != 'Kg':
				raise osv.except_osv(_('Warning !'),_('If price type is Per Kg select Kgs either Store UOM or PO UOM !!'))
			if rec.po_uom_in_kgs <= 0:
				raise osv.except_osv(_('Warning !'),_('PO UOM in kgs should be greater than Zero !!'))
			if rec.uom_po_id.code == 'Kg':
				raise osv.except_osv(_('Warning !'),_('Select PO UOM in Price Type !!'))
		if rec.pro_seller_ids:
			for line in rec.pro_seller_ids:
				cr.execute(""" select id from product_supplierinfo where name = %s and product_id = %s """ %(line.name.id,rec.id))
				data = cr.dictfetchall()
				if len(data) > 1:
					raise osv.except_osv(_('Warning !'),_('Supplier (%s) must be unique !!')%(line.name.name))
		res = True
		return res 
	
	_constraints = [
		
		(_name_validate, 'product name must be unique !!', ['name']),	
		(_primemover_validation, 'Kindly Configure Proper configurations', ['']),
		
	]
	
	def write(self,cr,uid,ids,vals,context={}):
		if 'tolerance_applicable' in vals:
			if vals['tolerance_applicable'] == True:
				if 'tolerance_plus' in vals:
					if vals['tolerance_plus'] <= 0.00:
						raise osv.except_osv(_('Check Tolerance(+) Value !!'),_('Please enter greater than zero !!'))
					else:
						pass
				else:
					pass
			else:
				pass
		return super(kg_product, self).write(cr, uid, ids,vals, context)
	
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_code = str(rec.name)		
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
		
		if rec.product_type in ('consu','capital','service','coupling','mechanical_seal'):
			url = 'http://10.100.9.32/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'product_master_purchase='+rec_code
		else:

			url = 'http://10.100.9.32/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&product_master_design='+rec_code

		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
	
kg_product()

class kg_product_category(osv.osv):
	
	_name = "product.category"
	_inherit = "product.category"
	
	_columns = {
		
		'account_id': fields.many2one('account.account','Ledger Name'),
		
	}
	
	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr, uid, ids[0])
		if rec.state == 'confirm':
			
			## Account master creation process start
			
			ac_obj = self.pool.get('account.account')
			ac_type_ids = self.pool.get('account.account.type').search(cr,uid,[('name','=','Expense')])
			ac_type = ''
			if ac_type_ids:
				ac_type_rec = self.pool.get('account.account.type').browse(cr,uid,ac_type_ids[0])
				ac_type = ac_type_rec.id
			#old_acc_ids = ac_obj.search(cr,uid,[('master_id','=',rec.id)])
			#if old_acc_ids:
				#old_acc_rec = ac_obj.browse(cr,uid,old_acc_ids[0])
				#ac_obj.write(cr,uid,old_acc_rec.id,{'name': rec.name})
			acc_ids = ac_obj.search(cr,uid,[('name','=',rec.name)])
			if not acc_ids:
				account_id = ac_obj.account_creation(cr,uid,rec.name,ac_type,rec.id,'auto','other','New Product Category Added',context=context)
				self.write(cr, uid, ids, {'account_id':account_id})
			## Account master creation process end
			
			self.write(cr, uid, ids, {'state': 'approved','app_user_id': uid, 'approve_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
kg_product_category()

class ch_product_yearly_average_price(osv.osv):
	
    _name = "ch.product.yearly.average.price"
	
    _columns = {
		
        'avg_price': fields.float('Average Price', required=True),
        'product_id': fields.many2one('product.product', 'Product'),
        'fiscal_id': fields.many2one('account.fiscalyear', 'Fiscal year'),
       
    }
    
    _defaults = {
		
        'avg_price' : 0.00,
		
    }
    
ch_product_yearly_average_price()
