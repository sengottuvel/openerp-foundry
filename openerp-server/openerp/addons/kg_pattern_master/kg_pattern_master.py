from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
import time
from datetime import date
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

class kg_pattern_master(osv.osv):

	_name = "kg.pattern.master"
	_description = "SAM Pattern Master"
	
	
	def _get_modify(self, cr, uid, ids, field_name, arg, context=None):
		res={}
		bom_line_obj = self.pool.get('ch.bom.line')
		bom_line_amend_obj = self.pool.get('ch.bom.line.amendment')		
		for item in self.browse(cr, uid, ids, context=None):
			res[item.id] = 'no'
			bom_line_ids = bom_line_obj.search(cr,uid,[('pattern_id','=',item.id)])
			bom_line_amend_ids = bom_line_amend_obj.search(cr,uid,[('pattern_id','=',item.id)])
					
			if bom_line_ids or bom_line_amend_ids:
				res[item.id] = 'yes'		
		return res
	
	_columns = {
			
		'name': fields.char('Part/Pattern No', size=128, required=True),
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'box_id': fields.many2one('kg.box.master','Box',readonly=True,domain="[('active','=','t')]"),		
		'pattern_name': fields.char('Part/Pattern Name', size=128,required=True),
		'code': fields.char('Customer Code No.', size=128),
		'active': fields.boolean('Active'),
		'pcs_weight': fields.float('SS Weight(kgs)'),
		'ci_weight': fields.float('CI Weight(kgs)'),
		'mould_rate': fields.float('Mould Rate(Rs)'),
		'location': fields.char('Physical Location', required=True),
		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'pattern_state': fields.selection([('active','Active'),('hold','Hold'),('rework','Rework'),('reject','Rejected'),('new_develop','New Development')],'Pattern Status',required=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'line_ids':fields.one2many('ch.mocwise.rate', 'header_id', "MOC Wise Rate"),
		'line_ids_a':fields.one2many('ch.pattern.attachment', 'header_id', "Attachments"),
		'line_ids_b':fields.one2many('ch.pattern.history', 'header_id', "Pattern History"),	
		'line_ids_c':fields.one2many('ch.latest.weight', 'header_id', "Latest Weight details", readonly=True),	
		
		'offer_info': fields.boolean('Offer Info'),
		'dynamic_length': fields.boolean('Dynamic Length'),	
		'corless_pattern': fields.boolean('Corless Pattern'),
		'length_type': fields.selection([('single_column_pipe','Single Column Pipe'),('single_shaft','Single Shaft'),('delivery_pipe','Delivery Pipe'),('drive_column_pipe','Drive Column Pipe'),('pump_column_pipe','Pump Column Pipe'),('pump_shaft','Pump Shaft'),('drive_shaft','Drive Shaft')],'Length Type'),		
		
		'tolerance': fields.float('Tolerance(-%)'),
		'nonferous_weight': fields.float('Non-Ferrous Weight(kgs)'),		
		'alias_name': fields.char('Alias Name', size=128),
		'make_by': fields.char('Make By', size=128),
		'delivery_lead': fields.integer('Delivery Lead Time(Weeks)', size=128),
		'csd_code': fields.char('CSD Code No.', size=128),
		'making_cost': fields.float('Pattern Making Cost'),
		'moc_const_type': fields.many2many('kg.construction.type', 'm2m_moc_rate_details', 'moc_const_id', 'const_type_id','Type', domain="[('active','=','t')]"),
		'moc_id': fields.many2one('kg.moc.master','Default MOC',domain="[('active','=','t')]" ),	
		
		
		'pattern_type': fields.selection([('new_pattern','New Pattern'),('copy_pattern','Copy Pattern')],'Type', required=True),	
		'source_pattern': fields.many2one('kg.pattern.master', 'Source Pattern',domain="[('active','=','t')]"),
		'copy_flag':fields.boolean('Copy Flag'),		
		
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
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.pattern.master', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':fields.datetime.now,	
		'delivery_lead':8,	
		'modify': 'no',
		'pattern_state': 'active',
		'copy_flag' : False,
		'pattern_type':'new_pattern',
	}
	
	
	def _Validation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])
		special_char = ''.join( c for c in flds.name if  c in '!@#$%^~*{}?+/=' )
		if special_char:
			return False
		return True
	
	def _CodeValidation(self, cr, uid, ids, context=None):
		flds = self.browse(cr , uid , ids[0])		
		if flds.code:	
			code_special_char = ''.join( c for c in flds.code if  c in '!@#$%^~*{}?+/=' )		
			if code_special_char:
				return False
		return True		
		
	def _name_validate(self, cr, uid,ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		res = True
		if rec.name:
			division_name = rec.name
			name=division_name.upper()			
			cr.execute(""" select upper(name) from kg_pattern_master where upper(name)  = '%s' """ %(name))
			data = cr.dictfetchall()
			
			if len(data) > 1:
				res = False
			else:
				res = True				
		return res
			
	def list_moc(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.moc_const_type:				
			moc_type_ids = []
			for moc_type in rec.moc_const_type:	
				moc_type_ids.append(moc_type.id)			
			moc_const_obj = self.pool.get('kg.moc.construction').search(cr,uid,([('constuction_type_id','in',moc_type_ids)]))
		else:
			moc_const_obj = self.pool.get('kg.moc.construction').search(cr,uid,([('active','=',True)]))				
		cr.execute(""" delete from ch_mocwise_rate where header_id  = %s """ %(ids[0]))
		for item in moc_const_obj:			
			moc_const_rec = self.pool.get('kg.moc.construction').browse(cr,uid,item)				
			line = self.pool.get('ch.mocwise.rate').create(cr,uid,{
			       'header_id':rec.id,
				   'moc_id':rec.moc_id.id,
				   'code':moc_const_rec.code,
				   'rate':rec.moc_id.rate,
				   'pro_cost':rec.moc_id.pro_cost})				
		return True
		
		
	def copy_pattern(self, cr, uid, ids, context=None):
		
		ch_mocwise_rate,ch_pattern_history,ch_pattern_attachment
		rec = self.browse(cr,uid,ids[0])
		moc_rate_line_obj = self.pool.get('ch.mocwise.rate')
		pattern_attach_line_obj = self.pool.get('ch.pattern.attachment')
		pattern_history_line_obj = self.pool.get('ch.pattern.history')		
				
		cr.execute(""" delete from ch_mocwise_rate where header_id  = %s """ %(ids[0]))
		cr.execute(""" delete from ch_pattern_attachment where header_id  = %s """ %(ids[0]))
		cr.execute(""" delete from ch_pattern_history where header_id  = %s """ %(ids[0]))		
				
		for moc_rate_line_item in rec.source_pattern.line_ids:			
			vals = {
				'header_id' : ids[0]
				}			
			copy_rec = moc_rate_line_obj.copy(cr, uid, moc_rate_line_item.id,vals, context) 
			
		for pattern_attach_line_item in rec.source_pattern.line_ids_a:			
			vals = {
				'header_id' : ids[0]
				}			
			copy_rec = pattern_attach_line_obj.copy(cr, uid, pattern_attach_line_item.id,vals, context) 		
			
		for pattern_history_line_item in rec.source_pattern.line_ids_b:			
			vals = {
				'header_id' : ids[0]
				}			
			copy_rec = pattern_history_line_obj.copy(cr, uid, pattern_history_line_item.id,vals, context) 	
		
		
		self.write(cr, uid, ids[0], {'copy_flag': True,'alias_name':rec.source_pattern.alias_name,
									'make_by':rec.source_pattern.make_by,
									'box_id':rec.source_pattern.box_id.id,
									'code':rec.source_pattern.code,
									'csd_code':rec.source_pattern.csd_code,
									'making_cost':rec.source_pattern.making_cost,
									'pcs_weight':rec.source_pattern.pcs_weight,
									'ci_weight':rec.source_pattern.ci_weight,
									'delivery_lead':rec.source_pattern.delivery_lead,
									'nonferous_weight':rec.source_pattern.nonferous_weight,
									'tolerance':rec.source_pattern.tolerance,
									'notes':rec.source_pattern.notes,
									
									'moc_id':rec.source_pattern.moc_id.id,											
									'moc_const_type':[(6, 0, [x.id for x in rec.source_pattern.moc_const_type])], })		
		return True
		
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
		if rec.pattern_type == 'copy_pattern':
			
			### Check Duplicates MOC Construction and Rate Details Items start ###
			
			cr.execute('''select 
					      
					rate_line.moc_id,
					rate_line.code,
					rate_line.rate,
					rate_line.amount,
					rate_line.pro_cost,
					rate_line.remarks

					from ch_mocwise_rate rate_line 

					left join kg_pattern_master header on header.id  = rate_line.header_id

					where header.pattern_type = 'copy_pattern' and header.id = %s''',[rec.id])
			
			source_rate_ids = cr.fetchall()		
			source_rate_len = len(source_rate_ids)	
			
			cr.execute('''select 

					rate_line.moc_id,
					rate_line.code,
					rate_line.rate,
					rate_line.amount,
					rate_line.pro_cost,
					rate_line.remarks

					from ch_mocwise_rate rate_line 

					where rate_line.header_id  = %s''',[rec.source_pattern.id])
			
			source_old_rate_ids = cr.fetchall()
			
			source_old_rate_len = len(source_old_rate_ids)
							
			cr.execute('''select 

					rate_line.code,
					rate_line.rate
					

					from ch_mocwise_rate rate_line 

					left join kg_pattern_master header on header.id  = rate_line.header_id

					where header.pattern_type = 'copy_pattern' and header.id = %s

					INTERSECT

					select 

					rate_line.code,
					rate_line.rate

					from ch_mocwise_rate rate_line 

					where rate_line.header_id  = %s ''',[rec.id,rec.source_pattern.id])
			repeat_rates_ids = cr.fetchall()			
			new_rate_len = len(repeat_rates_ids)			
			### Check Duplicates MOC Construction and Rate Details Items end.... ###
			
			
			### Check Duplicates Attachments Items start ###
			
			cr.execute('''select 
					 
					attach_line.date,
					attach_line.attach_file
					

					from ch_pattern_attachment attach_line 

					left join kg_pattern_master header on header.id  = attach_line.header_id

					where header.pattern_type = 'copy_pattern' and header.id = %s''',[rec.id])
			
			source_attach_ids = cr.fetchall()		
			source_attach_len = len(source_attach_ids)	
			
			cr.execute('''select 

					attach_line.date,
					attach_line.attach_file

					from ch_pattern_attachment attach_line 

					where attach_line.header_id  = %s''',[rec.source_pattern.id])
			
			source_old_attach_ids = cr.fetchall()
			
			source_old_attach_len = len(source_old_attach_ids)
							
			cr.execute('''select 

					attach_line.date,
					attach_line.attach_file

					from ch_pattern_attachment attach_line 

					left join kg_pattern_master header on header.id  = attach_line.header_id

					where header.pattern_type = 'copy_pattern' and header.id = %s

					INTERSECT

					select 

					attach_line.date,
					attach_line.attach_file

					from ch_pattern_attachment attach_line 

					where attach_line.header_id  = %s ''',[rec.id,rec.source_pattern.id])
			repeat_attach_ids = cr.fetchall()			
			new_attach_len = len(repeat_attach_ids)			
			### Check Duplicates Attachments Items end.... ###
			
			### Check Duplicates Pattern History Items start ###
			
			cr.execute('''select 
					   
					history_line.s_no,
					history_line.date,
					history_line.reason,
					history_line.remarks

					from ch_pattern_history history_line 

					left join kg_pattern_master header on header.id  = history_line.header_id

					where header.pattern_type = 'copy_pattern' and header.id = %s''',[rec.id])
			
			source_history_ids = cr.fetchall()		
			source_history_len = len(source_history_ids)	
			
			cr.execute('''select 

					history_line.s_no,
					history_line.date,
					history_line.reason,
					history_line.remarks

					from ch_pattern_history history_line 

					where history_line.header_id  = %s''',[rec.source_pattern.id])
			
			source_old_history_ids = cr.fetchall()
			
			source_old_history_len = len(source_old_history_ids)
							
			cr.execute('''select 

					history_line.s_no,
					history_line.date,
					history_line.reason,
					history_line.remarks

					from ch_pattern_history history_line 

					left join kg_pattern_master header on header.id  = history_line.header_id

					where header.pattern_type = 'copy_pattern' and header.id = %s

					INTERSECT

					select 

					history_line.s_no,
					history_line.date,
					history_line.reason,
					history_line.remarks

					from ch_pattern_history history_line 

					where history_line.header_id  = %s ''',[rec.id,rec.source_pattern.id])
			repeat_history_ids = cr.fetchall()			
			new_history_len = len(repeat_history_ids)			
			### Check Duplicates Pattern History Items end.... ###
			
			
			rate_dup = attach_dup = history_dup =  ''		
			if new_rate_len == source_rate_len == source_old_rate_len:			
				rate_dup = 'yes'		
			if new_attach_len == source_attach_len == source_old_attach_len:			
				attach_dup = 'yes'	
			if new_history_len == source_history_len == source_old_history_len:			
				history_dup = 'yes'			
			
			if rate_dup == 'yes' and attach_dup == 'yes' and history_dup == 'yes':			
				raise osv.except_osv(_('Warning!'),
								_('Same Pattern Details are already exist !!'))
						
		self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])				
		moc_rate_lines=rec.line_ids	
		moc_obj=self.pool.get('kg.moc.master')	
		for moc_rate_item in moc_rate_lines:			
			moc_rate_ids=moc_obj.search(cr,uid,[('name','=',moc_rate_item.moc_id.name),('active','=',True)])					
			moc_rec = moc_obj.browse(cr,uid,moc_rate_ids[0])						
			if moc_rec.weight_type == 'ci':			
				amount=rec.ci_weight * moc_rate_item.rate
				vals = {
				'amount': amount,				
					}
				self.pool.get('ch.mocwise.rate').write(cr,uid,moc_rate_item.id,vals)	
			elif moc_rec.weight_type == 'ss':				
				amount=rec.pcs_weight * moc_rate_item.rate
				vals = {
				'amount': amount,				
					}
				self.pool.get('ch.mocwise.rate').write(cr,uid,moc_rate_item.id,vals)	
			elif moc_rec.weight_type == 'non_ferrous':				
				amount=rec.nonferous_weight * moc_rate_item.rate
				vals = {
				'amount': amount,				
					}
				self.pool.get('ch.mocwise.rate').write(cr,uid,moc_rate_item.id,vals)	
			else:
				pass	
		self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True
	
	def entry_draft(self,cr,uid,ids,context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
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
		return super(kg_pattern_master, self).write(cr, uid, ids, vals, context)
		
	
	_constraints = [
		(_Validation, 'Special Character Not Allowed !!!', ['name']),
		(_CodeValidation, 'Special Character Not Allowed !!!', ['Check Code']),
		(_name_validate, 'Pattern No must be unique !!', ['no']),		
		
	]
	
kg_pattern_master()


class ch_mocwise_rate(osv.osv):
	
	_name = "ch.mocwise.rate"
	_description = "MOC Wise Rate"
	
	_columns = {
			
		'header_id':fields.many2one('kg.pattern.master', 'Pattern Entry', required=True, ondelete='cascade'),	
		'moc_id': fields.many2one('kg.moc.master','MOC', required=True,domain="[('active','=','t')]" ),		
		'code':fields.char('MOC Construction Code'),
		'rate':fields.float('Design Rate(Rs)',required=True),
		'amount':fields.float('Design Amount(Rs)'),
		'pro_cost':fields.float('Production Cost(Rs)'),
		'remarks':fields.text('Remarks'),
		
	}
	
	
	   
	def onchange_rate(self, cr, uid, ids, moc_id, context=None):
		
		value = {'rate': '','pro_cost':''}
		if moc_id:
			moc_rec = self.pool.get('kg.moc.master').browse(cr, uid, moc_id, context=context)
			value = {'rate': moc_rec.rate,'pro_cost':moc_rec.pro_cost}			
		return {'value': value}
		
	def create(self, cr, uid, vals, context=None):
		moc_obj = self.pool.get('kg.moc.master')
		if vals.get('moc_id'):		  
			moc_rec = moc_obj.browse(cr, uid, vals.get('moc_id') )
			moc_name = moc_rec.rate
			pro_cost = moc_rec.pro_cost
			vals.update({'rate': moc_name,'pro_cost':pro_cost})
		return super(ch_mocwise_rate, self).create(cr, uid, vals, context=context)
		
	def write(self, cr, uid, ids, vals, context=None):
		moc_obj = self.pool.get('kg.moc.master')
		if vals.get('moc_id'):
			moc_rec = moc_obj.browse(cr, uid, vals.get('moc_id') )
			moc_name = moc_rec.rate
			pro_cost = moc_rec.pro_cost
			vals.update({'rate': moc_name,'pro_cost':pro_cost})
		return super(ch_mocwise_rate, self).write(cr, uid, ids, vals, context)  
		
ch_mocwise_rate()



class ch_pattern_history(osv.osv):
	
	_name = "ch.pattern.history"
	_description = "Pattern History"
	
	_columns = {   
			
		'header_id':fields.many2one('kg.pattern.master', 'Pattern Entry', required=True, ondelete='cascade'),	
		's_no': fields.integer('S.No.', required=True),			
		'date':fields.date('Date',required=True),
		'reason':fields.text('Reason for Rework',required=True),
		'remarks':fields.text('Remarks'),
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		entry_date = rec.date
		entry_date = str(entry_date)
		entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
		if entry_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),   
		
		
	   ]
ch_pattern_history()



class ch_pattern_attachment(osv.osv):
	
	_name = "ch.pattern.attachment"
	_description = "Pattern Attachments"
	
	_columns = {  
			
		'header_id':fields.many2one('kg.pattern.master', 'Pattern Entry', required=True, ondelete='cascade'),			
		'date':fields.date('Date',required=True),
		'attach_file': fields.binary('Attachment'),
		
	}
	
	def _future_entry_date_check(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		today = date.today()
		today = str(today)
		today = datetime.strptime(today, '%Y-%m-%d')
		entry_date = rec.date
		entry_date = str(entry_date)
		entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
		if entry_date > today:
			return False
		return True
		
	_constraints = [		
			  
		
		(_future_entry_date_check, 'System not allow to save with future date. !!',['']),   
		
		
	   ]
ch_pattern_attachment()


class ch_latest_weight(osv.osv):
	
	_name = "ch.latest.weight"
	_description = "Latest Weight details"
	
	_columns = {  
			
		'header_id':fields.many2one('kg.pattern.master', 'Latest Weight details', required=True, ondelete='cascade'),	
		'weight_type': fields.selection([('ci','CI'),('ss','SS'),('non_ferrous','Non-Ferrous')],'Family Type'),	
		'pouring_weight': fields.float('Pouring weight'),	
		'casting_weight': fields.float('Casting weight'),	
		'finished_casting_weight': fields.float('Finished Casting Weight'),	
		
	}
	
	
ch_latest_weight()


