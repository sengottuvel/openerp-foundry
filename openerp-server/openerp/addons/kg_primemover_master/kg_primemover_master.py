from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
import base64

class kg_primemover_master(osv.osv):

	_name = "kg.primemover.master"
	_description = "Prime Mover Master"
	
	def _get_modify(self, cr, uid, ids, field_name, arg,  context=None):
		res={}
		if field_name == 'modify':
			for h in self.browse(cr, uid, ids, context=None):	
				res[h.id] = 'no'
				cr.execute(""" select * from
				(SELECT tc.table_schema, tc.constraint_name, tc.table_name, kcu.column_name, ccu.table_name
				AS foreign_table_name, ccu.column_name AS foreign_column_name
				FROM information_schema.table_constraints tc
				JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
				JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
				WHERE constraint_type = 'FOREIGN KEY'
				AND ccu.table_name='%s')
				as sam  """ %('kg_primemover_master'))
				data = cr.dictfetchall()	
				if data:
					for var in data:
						data = var
						chk_sql = 'Select COALESCE(count(*),0) as cnt from '+str(data['table_name'])+' where '+data['column_name']+' = '+str(ids[0])
						cr.execute(chk_sql)			
						out_data = cr.dictfetchone()
						if out_data:
							if out_data['cnt'] > 0:
								res[h.id] = 'yes'
		return res
		
	_columns = {
		
		## Basic Info
		
		'name': fields.char('Name', size=128, required=True, select=True),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		
		## Module Requirement Info
		
		'manufacturer': fields.many2one('kg.brand.master','Manufacturer'),
		'frequency': fields.selection([('50','50'),('60','60')],'Frequency(Hz)'),
		'effclass': fields.char('Effclass'),
		'pole': fields.integer('Pole'),
		'series': fields.char('Series'),
		'framesize': fields.char('Framesize'),
		'moc_id': fields.many2one('kg.moc.master','MOC'),
		'mounting': fields.char('Mounting'),
		'terminal_box_loc': fields.selection([('front','FRONT'),('top','TOP'),('behind','BEHIND')],'Terminal Box Location'),
		'efficiency': fields.integer('Efficiency'),
		'power_kw': fields.float('Power(Kw)'),
		'power_hp': fields.float('PowerHp(Hp)'),
		'speed': fields.integer('Speed(Rpm)'),
		'specification': fields.char('Specification'),
		'gd2': fields.char('Gd2'),
		'noise_level': fields.char('Noise level (DB)'),
		'primemover_type': fields.selection([('motor','MOTOR'),('engine','ENGINE')],'Prime Mover Type'),
		'weight': fields.float('Weight'),
		'article_no': fields.char('Article No'),
		'price': fields.float('Price'),
		'space_heater': fields.char('Space Heater'),
		'radiator_mtg': fields.char('Radiator Mtg'),
		'characteristics': fields.char('Characteristics'),
		'shaft_dia': fields.float('Shaft Dia'),
		'ambient_temp': fields.float('Ambient Temp'),
		'temprise_class': fields.char('TempRise Class'),
		'primemover_categ': fields.selection([('engine','Engine'),('motor','Motor')],'Primemover Category'),
		'product_id': fields.many2one('product.product','Item Name',domain="[('product_type','not in',('raw','capital','service'))]"),
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),
		
		## Entry Info
		
		'active': fields.boolean('Active'),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'crt_date': fields.datetime('Created Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'ap_rej_date': fields.datetime('Approved/Rejected Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Rejected By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.primemover.master', context=c),
		'active': True,		
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),	
		'modify': 'no',
		'entry_mode': 'manual',
		
	}

	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.name:
			prime_name = rec.name
			name=prime_name.upper()			
			cr.execute(""" select upper(name) from kg_primemover_master where upper(name)  = '%s' """ %(name))
			data = cr.dictfetchall()			
			if len(data) > 1:
				raise osv.except_osv(_('Warning!'),
					_('Name already exists !'))
		return True
		
	def _validations(self, cr, uid, ids, context=None):		
		rec = self.browse(cr, uid, ids[0])
		if rec.pole <= 0:
			raise osv.except_osv(_('Warning!'),
					_('Pole should be greater than zero !'))			
		if rec.power_kw <= 0:
			raise osv.except_osv(_('Warning!'),
					_('Power(Kw) should be greater than zero !'))
		if rec.efficiency <= 0:
			raise osv.except_osv(_('Warning!'),
					_('Efficiency should be greater than zero !'))	
		if rec.speed <= 0:
			raise osv.except_osv(_('Warning!'),
					_('Speed(Rpm) should be greater than zero !'))	
		if rec.power_hp <= 0:
			raise osv.except_osv(_('Warning!'),
					_('PowerHp(Hp) should be greater than zero !'))
		if rec.price<= 0:
			raise osv.except_osv(_('Warning!'),
					_('Price should be greater than zero !'))
		if rec.ambient_temp <= 0:
			raise osv.except_osv(_('Warning!'),
					_('Ambient Temp should be greater than zero !'))
		if rec.shaft_dia <= 0:
			raise osv.except_osv(_('Warning!'),
					_('Shaft Dia should be greater than zero !'))
		return True	

	_constraints = [
		
		(_name_validate, 'Primemover name must be unique !!', ['name']),		
		(_validations, ' ', ['name']),		
		
	]
		
	## Basic Needs
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			if rec.cancel_remark:
				self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Cancel remark is must !!'),
					_('Enter the remarks in Cancel remarks field !!'))
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'draft':
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.remark:
			self.write(cr, uid, ids, {'state': 'reject','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Rejection remark is must !!'),
				_('Enter the remarks in rejection remark field !!'))
		return True
		
	def unlink(self,cr,uid,ids,context=None):
		unlink_ids = []		
		for rec in self.browse(cr,uid,ids):	
			if rec.state not in ('draft','cancel'):				
				raise osv.except_osv(_('Warning!'),
						_('You can not delete this entry !!'))
			else:
				unlink_ids.append(rec.id)
		return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		vals.update({'update_date': time.strftime('%Y-%m-%d %H:%M:%S'),'update_user_id':uid})
		return super(kg_primemover_master, self).write(cr, uid, ids, vals, context)
	
	def send_to_dms(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		res_rec=self.pool.get('res.users').browse(cr,uid,uid)		
		rec_user = str(res_rec.login)
		rec_pwd = str(res_rec.password)
		rec_code = str(rec.name)		
		encoded_user = base64.b64encode(rec_user)
		encoded_pwd = base64.b64encode(rec_pwd)
			
		url = 'http://192.168.1.7/sam-dms/login.html?xmxyypzr='+encoded_user+'&mxxrqx='+encoded_pwd+'&prime_mover='+rec_code


		return {
					  'name'	 : 'Go to website',
					  'res_model': 'ir.actions.act_url',
					  'type'	 : 'ir.actions.act_url',
					  'target'   : 'current',
					  'url'	  : url
			   }
	
kg_primemover_master()
