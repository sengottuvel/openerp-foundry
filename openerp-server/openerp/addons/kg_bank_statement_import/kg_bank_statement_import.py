from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
import math
import struct 
import base64
import codecs
import StringIO
import csv
import psycopg2
dt_time = time.strftime('%m/%d/%Y %H:%M:%S')

from xlrd import open_workbook

class kg_bank_statement_import(osv.osv):
	
	_name = "kg.bank.statement.import"
	_description = "Bank Statement Import"
	
	### Version 0.1
	
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
					as sam  """ %('kg_bank_statement_import'))
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
		
		### Version 0.2
		
	_columns = {
	
		## Basic Info

		'state': fields.selection([('draft','Draft'),('confirmed','WFA'),('approved','Approved'),('reject','Rejected'),('cancel','Cancelled')],'Status', readonly=True),
		'notes': fields.text('Notes'),
		'remark': fields.text('Approve/Reject'),
		'cancel_remark': fields.text('Cancel'),
		'modify': fields.function(_get_modify, string='Modify', method=True, type='char', size=10),		
		'entry_mode': fields.selection([('auto','Auto'),('manual','Manual')],'Entry Mode', readonly=True),

		## Entry Info
		
		'company_id': fields.many2one('res.company', 'Company Name',readonly=True),
		'active': fields.boolean('Active'),
		'crt_date': fields.datetime('Creation Date',readonly=True),
		'user_id': fields.many2one('res.users', 'Created By', readonly=True),
		'confirm_date': fields.datetime('Confirmed Date', readonly=True),
		'confirm_user_id': fields.many2one('res.users', 'Confirmed By', readonly=True),
		'ap_rej_date': fields.datetime('Approved/Rejected Date', readonly=True),
		'ap_rej_user_id': fields.many2one('res.users', 'Approved/Rejected By', readonly=True),	
		'cancel_date': fields.datetime('Cancelled Date', readonly=True),
		'cancel_user_id': fields.many2one('res.users', 'Cancelled By', readonly=True),
		'update_date': fields.datetime('Last Updated Date', readonly=True),
		'update_user_id': fields.many2one('res.users', 'Last Updated By', readonly=True),
		
		## Module Requirement Info
		'acc_journal_id':fields.many2one('account.journal','Bank Account'),
		'from_date':fields.date('From Date'),
		'to_date':fields.date('To Date'),
		'file_type':fields.selection([('excel','Excel'),('csv','CSV')],'File Type'),
		'file_data':fields.binary('Choose File (Excel/CSV)'),
		'filename':fields.char('Filename'),
		
		## Child Tables Declaration
		
		'line_id':fields.one2many('ch.bank.statement.import','header_id','Line id'),
		
				
	}
	
	_defaults = {
	
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kg.bank.statement', context=c),
		'active': True,
		'state': 'draft',
		'user_id': lambda obj, cr, uid, context: uid,
		'crt_date':lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'modify': 'no',
		'entry_mode': 'manual',
		
	}

	
	## Basic Needs	
	
	def entry_cancel(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':
			if rec.cancel_remark:
				self.write(cr, uid, ids, {'state': 'cancel','cancel_user_id': uid, 'cancel_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Cancel remark is must !!'),
					_('Enter the remarks in Cancel remarks field !!'))
		else:
			pass
		return True

	def entry_confirm(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.to_date < rec.from_date:
			raise osv.except_osv(_('Warning !!'),
				_('From and To Date should not be less than From Date !!'))
		if not rec.line_id:
			raise osv.except_osv(_('Warning!'),
				_('Bank Statement Details should not be empty !!'))
		for line_ids in rec.line_id:
			trns_date = datetime.strptime(line_ids.trans_date,'%Y-%m-%d')
			if line_ids.trans_date < rec.from_date:
				raise osv.except_osv(_('Warning!'),
					_('Transaction Date %s is less than the From Date !!'%(trns_date.strftime('%d-%m-%Y'))))
			if line_ids.trans_date > rec.to_date:
				trns_date = datetime.strptime(line_ids.trans_date,'%Y-%m-%d')
				raise osv.except_osv(_('Warning!'),
					_('Transaction Date %s is greater than the To Date !!'%(trns_date.strftime('%d-%m-%Y'))))
			if (line_ids.debit == 0.00 and line_ids.credit == 0.00):
				raise osv.except_osv(_('Warning!'),
					_('Debit and credit should not be zero for Transaction Date %s !!'%(trns_date.strftime('%d-%m-%Y'))))
			elif (line_ids.debit != 0.00 and line_ids.credit != 0.00):
				raise osv.except_osv(_('Warning!'),
					_('Both Debit and credit should not contain value for Transaction Date %s !!'%(trns_date.strftime('%d-%m-%Y'))))
		if rec.state == 'draft':
			from itertools import groupby
			total_dates = [line_ids.trans_date for line_ids in rec.line_id]
			src_dups_bnk_entry = self.pool.get('kg.bank.statement').search(cr,uid,[('bnk_imp_id','=',rec.id)])
			if src_dups_bnk_entry:
				cr.execute('''delete from kg_bank_statement where bnk_imp_id = '%d' '''%(rec.id))
			else:
				pass
			for dates in list(set(total_dates)):
				self.pool.get('kg.bank.statement').create(cr,uid,
						{
							'clear_date':dates,
							'acc_journal_id':rec.acc_journal_id.id,
							'bnk_imp_id':rec.id,
							'entry_mode':'auto'
						})
				src_bank_entry = self.pool.get('kg.bank.statement').search(cr,uid,[('clear_date','=',dates),('bnk_imp_id','=',rec.id)])
				bank_ent_rec = self.pool.get('kg.bank.statement').browse(cr,uid,src_bank_entry[0])
				src_line_ids = self.pool.get('ch.bank.statement.import').search(cr,uid,[('trans_date','=',dates),('header_id','=',rec.id)])
				for idss in src_line_ids:
					src_rec = self.pool.get('ch.bank.statement.import').browse(cr,uid,idss)
					self.pool.get('ch.bank.statement').create(cr,uid,
						{
							'cheque_no':src_rec.ref_no,
							'header_id':bank_ent_rec.id,
							'narration':src_rec.narration,
							'debit':src_rec.debit,
							'credit':src_rec.credit,
						})
			self.write(cr, uid, ids, {'state': 'confirmed','confirm_user_id': uid, 'confirm_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True
		
	def entry_draft(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'approved':			
			self.write(cr, uid, ids, {'state': 'draft'})
		else:
			pass
		return True

	def entry_approve(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			self.write(cr, uid, ids, {'state': 'approved','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
		else:
			pass
		return True

	def entry_reject(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		if rec.state == 'confirmed':
			if rec.remark:
				self.write(cr, uid, ids, {'state': 'reject','ap_rej_user_id': uid, 'ap_rej_date': time.strftime('%Y-%m-%d %H:%M:%S')})
			else:
				raise osv.except_osv(_('Rejection remark is must !!'),
					_('Enter the remarks in rejection remark field !!'))
		else:
			pass
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
		return super(kg_bank_statement_import, self).write(cr, uid, ids, vals, context)	
	
	## Module Requirement
	
	def file_import(self,cr,uid,ids,context=None):
		rec = self.browse(cr,uid,ids[0])
		my_string = str(rec.filename)
		print my_string.split(".",1)[1]
		if rec.line_id:
			cr.execute('''delete from ch_bank_statement_import where header_id=%s'''%(rec.id))
		else:
			pass
		try:
			if my_string.split(".",1)[1] == 'csv':
				attachments = []
				attachments.append(base64.b64decode(rec.file_data))
				dd = [i.split('\n') for i in attachments]
				ee = [i.split(';') for i in dd[0]]
				num=0
				for num in range(1,(len(ee)-1)):
					cr.execute('''insert into ch_bank_statement_import (header_id,trans_date,ref_no,debit,credit,narration) values ('%s','%s','%s','%s','%s','%s')'''%(rec.id,ee[num][0],ee[num][1],ee[num][2],ee[num][3],ee[num][4]))
					num = num +1
			else:
				bin_file = rec.file_data
				f = open("/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_bank_statement_import/temp_bank_state.xls", "wb")
				f.write(bin_file.decode('base64'))
				f.close()
				wb = open_workbook('/OpenERP/Sam_Turbo/openerp-foundry/openerp-server/openerp/addons/kg_bank_statement_import/temp_bank_state.xls')
				for s in wb.sheets():
					values = []
					for row in range(1,s.nrows):
						col_value = []
						for col in range(s.ncols):
							value  = (s.cell(row,col).value)
							try : value = str(int(value))
							except : pass
							col_value.append(value)
						values.append(col_value)
				if values:
					for row in values:
						cr.execute('''insert into ch_bank_statement_import (header_id,trans_date,ref_no,debit,credit,narration) values ('%s','%s','%s','%s','%s','%s')'''%(rec.id,str(row[0]),str(row[1]),row[2],row[3],str(row[4])))
		except:
			raise osv.except_osv(_('Warning!'),
				_('Incorrect File Type !!'))
		return True

kg_bank_statement_import()

class ch_bank_statement_import(osv.osv):
	
	_name = "ch.bank.statement.import"
	_description = "Bank Statement Import Line"
	_order='trans_date'
	_columns = {

	'header_id':fields.many2one('kg.bank.statement.import','Header id'),
	'trans_date':fields.date('Transaction Date'),
	'ref_no':fields.char('Ref No'),
	'debit':fields.float('Debit'),
	'credit':fields.float('Credit'),
	'narration':fields.text('Narration')
	
	}
	
ch_bank_statement_import()	
