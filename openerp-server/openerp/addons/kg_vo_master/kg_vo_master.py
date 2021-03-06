from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_vo_master(osv.osv):

	_name = "kg.vo.master"
	_description = "VO Master"
	
	def _get_modify(self, cr, uid, ids, field_name, arg,  context=None):
		res={}		
		if field_name == 'modify':
			for h in self.browse(cr, uid, ids, context=None):
				res[h.id] = 'no'
				if h.state == 'approved':
					cr.execute(""" select * from 
					(SELECT tc.table_schema, tc.constraint_name, tc.table_name, kcu.column_name, ccu.table_name
					AS foreign_table_name, ccu.column_name AS foreign_column_name
					FROM information_schema.table_constraints tc
					JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
					JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
					WHERE constraint_type = 'FOREIGN KEY'
					AND ccu.table_name='%s')
					as sam  """ %('kg_vo_master'))
					data = cr.dictfetchall()	
					if data:
						for var in data:
							data = var
							chk_sql = 'Select COALESCE(count(*),0) as cnt from '+str(data['table_name'])+' where '+data['column_name']+' = '+str(ids[0])							
							cr.execute(chk_sql)			
							out_data = cr.dictfetchone()
							if out_data:								
								if out_data['cnt'] > 0:
									res[h.id] = 'no'
									return res
								else:
									res[h.id] = 'yes'
				else:
					res[h.id] = 'no'	
		return res	
	
	_columns = {
			
		'name': fields.char('Name', size=128, required=True, select=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'code': fields.char('Code', size=128, required=True),
		'active': fields.boolean('Active'),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		
		'shaft_above':fields.float('Shaft Ext.above BP'),		
		'star':fields.float('Star'),		
		'lcp':fields.float('LCP'),		
		'ls':fields.float('LS'),		
		'base_upto':fields.float('Base Plate upto 3000'),		
		'base_above':fields.float('Base Plate above 3000'),		
		
		
		
		
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),	
		'line_ids':fields.one2many('ch.power.series', 'header_id', "Power Series"),	
		'line_ids_a':fields.one2many('ch.bed.assembly', 'header_id', "Bed Assembly"),	
		'line_ids_b':fields.one2many('ch.motor.assembly', 'header_id', "Motor Assembly"),	
		'line_ids_c':fields.one2many('ch.columnpipe.assembly', 'header_id', "Columnpipe Assembly"),	
		'line_ids_d':fields.one2many('ch.deliverypipe.assembly', 'header_id', "Deliverypipe Assembly"),	
		'line_ids_e':fields.one2many('ch.casing.assembly', 'header_id', "Casing Assembly"),	
		'line_ids_f':fields.one2many('ch.lubricant', 'header_id', "Lubricant Assembly"),	
		
		
		### Entry Info ###
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'ap_rej_date': fields.datetime('Approved/Reject Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Reject By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.vo.master', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		
	}
	
	_sql_constraints = [
	
		('name', 'unique(name)', 'Name must be unique per Company !!'),
		('code', 'unique(code)', 'Code must be unique per Company !!'),
	]
	
	
		
	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.name:
			vo_name = rec.name
			name=vo_name.upper()			
			cr.execute(""" select upper(name) from kg_vo_master where upper(name)  = '%s' """ %(name))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
			
	def _code_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.code:
			vo_code = rec.code
			code=vo_code.upper()			
			cr.execute(""" select upper(code) from kg_vo_master where upper(code)  = '%s' """ %(code))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res	
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.cancel_remark:
			self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			raise osv.except_osv(_('Cancel remark is must !!'),
				_('Enter the remarks in Cancel remarks field !!'))
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if len(rec.line_ids) == 0  or len(rec.line_ids_a) == 0 or len(rec.line_ids_b) == 0 or len(rec.line_ids_c) == 0 or len(rec.line_ids_d) == 0 or len(rec.line_ids_e) == 0 or len(rec.line_ids_e) == 0:
			raise osv.except_osv(
						_('Warning !!!'),
						_('Please Check Line empty values not allowed!!'))
		if rec.state == 'draft':
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
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
		return super(kg_vo_master, self).write(cr, uid, ids, vals, context)
		
	
	_constraints = [		
		(_name_validate, 'VO name must be unique !!', ['name']),		
		(_code_validate, 'VO code must be unique !!', ['code']),		
		
	]
	
kg_vo_master()



class ch_power_series(osv.osv):
	
	_name = "ch.power.series"
	_description = "Power Series"
	
	_columns = {
			
		'header_id':fields.many2one('kg.vo.master', 'VO Entry', required=True, ondelete='cascade'),		
		'min':fields.float('Setting Height MIN',required=True),		
		'max':fields.float('Setting Height MAX',required=True),	
		'star': fields.selection([('nil','Nil'),('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),('7','7')],'Star (in No)',required=True),
		'part_list_id': fields.many2one('kg.bom', 'Part List Name',domain = [('category_type','=','part_list_bom')]),
		'remarks':fields.text('Remarks'),		
	}
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		if entry.min < 0.00 or entry.max <= 0.00:
			raise osv.except_osv(_('Warning'), _('Max Value (%s) of Star (%s) should be greater than zero')%(entry.max,entry.star))
		if entry.min > entry.max:
			raise osv.except_osv(_('Warning'), _('Min Value (%s) should not be greater than Max Value (%s) of Star (%s)')%(entry.min,entry.max,entry.star))
		if entry.min:				
			cr.execute(""" select min from ch_power_series where star = '%s' and header_id =%s 
				and %s BETWEEN min AND max and %s <= max
			""" %(entry.star,entry.header_id.id,entry.min,entry.min))
			data = cr.dictfetchall()			
			if len(data) > 1:
				raise osv.except_osv(_('Warning'), _('Duplicate of Star (%s) with Min Value (%s) and Max Value (%s) is not allowed')%(entry.min,entry.max,entry.star))
		return True

	_constraints = [		
			  
		(_check_values, ' ',['Power Series']),
		
	   ]
	
ch_power_series()




class ch_bed_assembly(osv.osv):
	
	_name = "ch.bed.assembly"
	_description = "Bed Assembly"
	
	_columns = {
			
		'header_id':fields.many2one('kg.vo.master', 'VO Entry', required=True, ondelete='cascade'),		
		'limitation':fields.selection([('upto_3000','Upto 2999'),('above_3000','Above 3000')],'Limitation',required=True),		
		'value': fields.float('Value'),
		'bp': fields.float('BP',required=True),
		'shaft_ext': fields.float('Shaft Ext',required=True),
		'packing': fields.selection([('g_p','G.P'),('m_s','M.S'),('f_s','F.S')],'Packing',required=True),
		'partlist_id': fields.many2one('kg.bom', 'Part list Name',required=True,domain="[('category_type','=','part_list_bom')]"),
		'remarks':fields.text('Remarks'),		
	}
	
	def _bed_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.limitation:	
			if rec.limitation == 'upto_3000':
				limitation = 'Upto 2999'
			elif rec.limitation == 'above_3000':
				limitation = 'Above 3000'
			else:
				limitation = ''
			if rec.packing == 'g_p':
				packing = 'G.P'
			elif rec.packing == 'm_s':
				packing = 'M.S'
			elif rec.packing == 'f_s':
				packing = 'F.S'
			else:
				packing = ''
			cr.execute(""" select limitation from ch_bed_assembly where limitation  = '%s' and packing  = '%s' and header_id =%s """ %(rec.limitation,rec.packing,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				raise osv.except_osv(_('Warning'), _('Duplicate of Limitation (%s) and Packing (%s) is not allowed')%(limitation,packing))				
		return res
		
	_constraints = [
	
		
		(_bed_validate, ' ',['Bed Tab']),	
		
		]
	
	
	
ch_bed_assembly()



class ch_motor_assembly(osv.osv):
	
	_name = "ch.motor.assembly"
	_description = "Motor Assembly"
	
	_columns = {
			
		'header_id':fields.many2one('kg.vo.master', 'VO Entry', required=True, ondelete='cascade'),			
		'value': fields.selection([('90','90'),('100','100'),('112','112'),('132','132'),('160','160'),('180','180'),('200','200'),('225','225'),('250','250'),('280','280'),('315','315'),('315_l','315L')],'Motor Frame Size',required=True),	
		'partlist_id': fields.many2one('kg.bom', 'Part list Name',required=True,domain="[('category_type','=','part_list_bom')]"),
		'remarks':fields.text('Remarks'),		
	}
	
	def _motor_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.value:					
			cr.execute(""" select value from ch_motor_assembly where value  = '%s' and header_id =%s """ %(rec.value,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				raise osv.except_osv(_('Warning'), _('Duplicate of Motor Frame Size (%s) is not allowed')%(rec.value))		
		return True
		
	_constraints = [

		(_motor_validate, ' ',['Motor Tab']),	
		
		]
	
	
	
ch_motor_assembly()



class ch_columnpipe_assembly(osv.osv):
	
	_name = "ch.columnpipe.assembly"
	_description = "ColumnPipe Assembly"
	
	_columns = {
			
		'header_id':fields.many2one('kg.vo.master', 'VO Entry', required=True, ondelete='cascade'),				
		'pipe_type': fields.selection([('grease','Bronze/Grease'),('cft_self','CFT'),('cut_less_rubber','Cut less Rubber')],'Type',required=True),
		'star': fields.selection([('nil','Nil'),('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),('7','7')],'Star (in No)',required=True),
		'partlist_id': fields.many2one('kg.bom', 'Part list Name',required=True,domain="[('category_type','=','part_list_bom')]"),
		'remarks':fields.text('Remarks'),		
	}
	
	def _columnpipe_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.pipe_type:
			if rec.pipe_type == 'grease':
				pipe_type = 'Bronze/Grease'				
			elif rec.pipe_type == 'cft_self':
				pipe_type = 'CFT'				
			elif rec.pipe_type == 'cut_less_rubber':
				pipe_type = 'Cut less Rubber'	
			else:
				pipe_type = ''			
			cr.execute(""" select pipe_type from ch_columnpipe_assembly where pipe_type = '%s' and star = '%s' and header_id =%s """ %(rec.pipe_type,rec.star,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				raise osv.except_osv(_('Warning'), _('Duplicate of Check Type (%s) Star (in No) is not allowed')%(pipe_type))				
		return True
		
	_constraints = [
	
		
		(_columnpipe_validate, ' ',['Column Pipe Tab']),	
		
		]
	
	
ch_columnpipe_assembly()



class ch_deliverypipe_assembly(osv.osv):
	
	_name = "ch.deliverypipe.assembly"
	_description = "DeliveryPipe Assembly"
	
	_columns = {
			
		'header_id':fields.many2one('kg.vo.master', 'VO Entry', required=True, ondelete='cascade'),			
		'size': fields.selection([('32','32'),('40','40'),('50','50'),('65','65'),('80','80'),('100','100'),('125','125'),('150','150'),('200','200'),('250','250'),('300','300')],'Size',required=True),
		'partlist_id': fields.many2one('kg.bom', 'Part list Name',required=True,domain="[('category_type','=','part_list_bom')]"),
		'star': fields.selection([('nil','Nil'),('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),('7','7')],'Star (in No)',required=True),
		'remarks':fields.text('Remarks'),		
	}
	
	def _deliverypipe_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.size:					
			cr.execute(""" select size from ch_deliverypipe_assembly where size = '%s' and star = '%s' and header_id =%s """ %(rec.size,rec.star,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				raise osv.except_osv(_('Warning'), _('Duplicate of Check Size (%s) Star (in No) is not allowed')%(rec.size))		
		return res
		
	_constraints = [
	
		
		(_deliverypipe_validate, ' ',['DeliveryPipe Tab']),	
		
		]
	
	
	
ch_deliverypipe_assembly()


class ch_casing_assembly(osv.osv):
	
	_name = "ch.casing.assembly"
	_description = "Casing Assembly"
	
	_columns = {
			
		'header_id':fields.many2one('kg.vo.master', 'VO Entry', required=True, ondelete='cascade'),		
		'product_id': fields.many2one('kg.pumpmodel.master', 'Product model',required=True,domain="[('active','=','t')]"),
		'partlist_id': fields.many2one('kg.bom', 'Part list Name',required=True,domain="[('category_type','=','part_list_bom')]"),		
		'remarks':fields.text('Remarks'),		
	}
	
	def _casing_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.product_id:					
			cr.execute(""" select product_id from ch_casing_assembly where product_id = '%s' and header_id =%s """ %(rec.product_id.id,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				raise osv.except_osv(_('Warning'), _('Duplicate of Check Product model (%s) is not allowed')%(rec.product_id.name))		
		return res
		
	_constraints = [
		
		(_casing_validate, 'Please Check Product model should be unique!!!',['Casing Tab']),	
		
		]
	
	
ch_casing_assembly()


class ch_lubricant(osv.osv):
	
	_name = "ch.lubricant"
	_description = "Lubricant"
	
	_columns = {
			
		'header_id':fields.many2one('kg.vo.master', 'VO Entry', required=True, ondelete='cascade'),		
		'type': fields.selection([('grease','Grease'),('cft_ext','CFT-EXT'),('cft_self','CFT-SELF'),('cut_less_rubber','Cut less Rubber')],'Type',required=True),
		'partlist_id': fields.many2one('kg.bom', 'Part list Name',required=True,domain="[('category_type','=','part_list_bom')]"),
		'star': fields.selection([('nil','Nil'),('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),('7','7')],'Star (in No)',required=True),
		'remarks':fields.text('Remarks'),		
	}
	
	def _lubricant_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.type:
			if rec.type == 'grease':
				lu_type = 'Grease'	
			elif rec.type == 'cft_ext':
				lu_type = 'CFT-EXT'	
			elif rec.type == 'cft_self':
				lu_type = 'CFT-SELF'	
			elif rec.type == 'cut_less_rubber':
				lu_type = 'Cut less Rubber'	
			else:
				lu_type = ''
			cr.execute(""" select type from ch_lubricant where type = '%s' and star = '%s' and header_id =%s """ %(rec.type,rec.star,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				raise osv.except_osv(_('Warning'), _('Duplicate of Check Type (%s) is not allowed')%(lu_type))		
		return True
		
	_constraints = [
	
		(_lubricant_validate, ' ',['Lubricant Tab']),	
		
		]
	
ch_lubricant()



class ch_vo_mapping(osv.osv):
	
	_name = "ch.vo.mapping"
	_description = "VO Mapping"
	
	_columns = {
			
		'header_id':fields.many2one('kg.pumpmodel.master', 'VO Mapping Entry', required=True, ondelete='cascade'),							
		'rpm': fields.selection([('1450','1450'),('2900','2900')],'RPM', required=True),
		'vo_id': fields.many2one('kg.vo.master','VO Name',required=True,domain="[('active','=','t')]"),	
		'remarks':fields.text('Remarks'),	
	}
	
	def _rpm_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.rpm:					
			cr.execute(""" select rpm from ch_vo_mapping where rpm  = '%s' and header_id =%s """ %(rec.rpm,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
		
	_constraints = [
	
		
		(_rpm_validate, 'Please Check RPM should be unique!!!',['VO Mapping Tab']),	
		
		]
	
ch_vo_mapping()


class ch_coupling_config(osv.osv):
	
	_name = "ch.coupling.config"
	_description = "Coupling Configuration"
	
	_columns = {
			
		'header_id':fields.many2one('kg.pumpmodel.master', 'Coupling Configuration', required=True, ondelete='cascade'),	
		'primemover_id': fields.many2one('kg.primemover.master','Prime Mover',required=True),
		'power_kw': fields.float('Motor Power',readonly=True),
		'speed': fields.integer('Motor Speed',readonly=True),
		'brand_id': fields.many2one('kg.brand.master','Coupling Brand',required=True,domain="[('state','=','approved')]"),
		'coupling_type_id': fields.many2one('kg.coupling.type','Coupling type ',required=True),
		'coupling_ser_factor': fields.selection([('1_0','1.0'),('1_2','1.2'),('1_5','1.5'),('2_0','2.0')],'Coupling service factor',required=True),			
		'coupling_access_id': fields.many2one('kg.accessories.master','Coupling',required=True,domain="[('state','not in',('reject','cancel')),('accessories_type','=','coupling')]"),
		'baseplate_id': fields.many2one('kg.accessories.master','Baseplate',required=True,domain="[('state','not in',('reject','cancel')),('accessories_type','=','base_plate')]"),
		'foundation_bolt_id': fields.many2one('kg.accessories.master','Foundation Bolt',required=True,domain="[('state','not in',('reject','cancel')),('accessories_type','=','foundation_bolt')]"),
		'coupling_guard_id': fields.many2one('kg.accessories.master','Coupling guard',required=True,domain="[('state','not in',('reject','cancel')),('accessories_type','=','coupling_guard')]"),
		
		'flag_attach_gad': fields.binary('GAD Drawing'),
		'remarks':fields.text('Remarks'),	
		
	}
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		res = True
		if entry.primemover_id:
			cr.execute(""" select primemover_id from ch_coupling_config where primemover_id  = '%s' and power_kw = '%s' and speed = '%s' and brand_id = '%s' and coupling_type_id = '%s' and coupling_ser_factor = '%s' and coupling_access_id = '%s' and header_id = '%s' """ %
			(entry.primemover_id.id,entry.power_kw,entry.speed,entry.brand_id.id,entry.coupling_type_id.id,entry.coupling_ser_factor,entry.coupling_access_id.id,entry.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:		
				res = False
			else:
				res = True
		return res	
		
	_constraints = [		
		(_check_values, 'Please Check the same Motor Power and Motor Speed not allowed..!!',['Coupling Configuration']),			
	   ]
	
	def onchange_primee(self, cr, uid, ids, primemover_id, context=None):
		value = {'power_kw': '','speed':''}
		if primemover_id:
			primemover_rec = self.pool.get('kg.primemover.master').browse(cr, uid, primemover_id, context=context)
			value = {'power_kw': primemover_rec.power_kw,'speed': primemover_rec.speed}
		return {'value': value}
	
ch_coupling_config()



class ch_accessories_config(osv.osv):
	
	_name = "ch.accessories.config"
	_description = "Accessories Configuration"
	
	_columns = {
			
		'header_id':fields.many2one('kg.pumpmodel.master', 'Coupling Configuration', required=True, ondelete='cascade'),	
		'primemover_id': fields.many2one('kg.primemover.master','Prime Mover',required=True),
		'power_kw': fields.float('Motor Power',readonly=True),
		'speed': fields.integer('Motor Speed',readonly=True),
		'framesize': fields.char('Motor Frame size',readonly=True),
		'pump_speed': fields.integer('Pump Speed',required=True),
		'pump_pulley_access_id': fields.many2one('kg.accessories.master','Pump Pulley',required=True,domain="[('state','not in',('reject','cancel')),('accessories_type','=','pump_pulley')]"),
		'motor_pulley_access_id': fields.many2one('kg.accessories.master','Motor Pulley',required=True,domain="[('state','not in',('reject','cancel')),('accessories_type','=','motor_pulley')]"),
		'slide_rail_access_id': fields.many2one('kg.accessories.master','Slide Rail/Base plate',required=True,domain="[('state','not in',('reject','cancel')),('accessories_type','=','slide_rail')]"),
		'belt_access_id': fields.many2one('kg.accessories.master','Belt',required=True,domain="[('state','not in',('reject','cancel')),('accessories_type','=','belt')]"),
		'belt_guard_access_id': fields.many2one('kg.accessories.master','Belt Guard',required=True,domain="[('state','not in',('reject','cancel')),('accessories_type','=','belt_guard')]"),
		'remarks':fields.text('Remarks'),	
		
	}
	
	def _check_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])
		res = True
		if entry.primemover_id:
			cr.execute(""" select primemover_id from ch_accessories_config where primemover_id  = '%s' and power_kw = '%s' and speed = '%s' and header_id = '%s' """ %
			(entry.primemover_id.id,entry.power_kw,entry.speed,entry.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:		
				res = False
			else:
				res = True
		return res	

	_constraints = [		
		(_check_values, 'Please Check the same Motor Power and Motor Speed not allowed..!!',['Accessories Configuration']),			
	   ]
	
	def onchange_primee(self, cr, uid, ids, primemover_id, context=None):
		value = {'power_kw': '','speed':'','framesize':''}
		if primemover_id:
			primemover_rec = self.pool.get('kg.primemover.master').browse(cr, uid, primemover_id, context=context)
			value = {'power_kw': primemover_rec.power_kw,'speed': primemover_rec.speed,'framesize':primemover_rec.framesize}
		return {'value': value}
	
ch_accessories_config()


class ch_csd_drawing(osv.osv):
	
	_name = "ch.csd.drawing"
	_description = "CSD Drawing Attachment"
	
	_columns = {
			
		'header_id':fields.many2one('kg.pumpmodel.master', 'CSD Drawing Attachment', required=True, ondelete='cascade'),	
		'moc_const_id': fields.many2one('kg.moc.construction','MOC Construction'),
		'flag_attach_gad': fields.binary('CSD Drawing'),
		'remarks':fields.text('Remarks'),	
		
	}
	
	def _moc_const_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.moc_const_id:					
			cr.execute(""" select moc_const_id from ch_csd_drawing where moc_const_id  = '%s' and header_id =%s """ %(rec.moc_const_id.id,rec.header_id.id))
			data = cr.dictfetchall()			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
	
	
	def _check_attach_values(self, cr, uid, ids, context=None):
		entry = self.browse(cr,uid,ids[0])				
		if entry.moc_const_id:			
			if entry.flag_attach_gad is False:
				return False			
		return True	
		
	_constraints = [		
			  
		(_check_attach_values, 'Check the CSD Drawing Empty values not allowed..!!',['CSD Drawing']),	
		(_moc_const_validate, 'Please Check MOC Construction should be unique!!!',['CSD Drawing Attachment Tab']),	
		
	   ]
	
ch_csd_drawing()

class kg_pumpmodel_master_inherit(osv.osv):
	
	_name = "kg.pumpmodel.master"
	_inherit = "kg.pumpmodel.master"
	
	_columns = {
			
		'line_ids':fields.one2many('ch.vo.mapping', 'header_id', "VO Mapping"),
		'line_ids_c':fields.one2many('ch.coupling.config', 'header_id', "Coupling Configuration"),		
		'line_ids_d':fields.one2many('ch.accessories.config', 'header_id', "Accessories Configuration"),		
		'line_ids_e':fields.one2many('ch.csd.drawing', 'header_id', "CSD Drawing Attachment"),
		
	}
	
	
kg_pumpmodel_master_inherit()








