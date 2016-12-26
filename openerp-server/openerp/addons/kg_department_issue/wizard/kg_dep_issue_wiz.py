from openerp.osv import osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp import pooler

from osv import fields, osv

class kg_dep_issue_wiz(osv.osv_memory):
	"""
	This wizard will confirm the all the selected draft inward
	"""

	_name = "kg.dep.issue.wiz"
	_description = "Confirm the selected issue"
	
	_columns = {
		
		'remark': fields.char('Remarks'),
		
		}
				
	def dep_issue_confirm(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		wf_service = netsvc.LocalService('workflow')
		if context is None:
			context = {}
		pool_obj = pooler.get_pool(cr.dbname)
		data_inv = pool_obj.get('kg.department.issue.line').read(cr, uid, context['active_ids'], ['state'], context=context)
		issue_line_obj = self.pool.get('kg.department.issue.line')
		for record in data_inv:
			#~ if record['state'] not in ('draft'):
				#~ raise osv.except_osv(_('Warning!'), _("Selected invoice(s) cannot be confirmed as they are not in 'Draft' or 'Pro-Forma' state."))
			s = record.get('id')
			print"sssssssssssssssss",s
			#~ issue_line_rec = issue_line_obj.browse(cr,uid,s)
			issue_line_rec = issue_line_obj.action_process(cr,uid,[s])
			#~ issue_line_obj.write(cr,uid,issue_line_rec.id,{'state':'confirmed','remark':rec.remark})
			#wf_service.trg_validate(uid, 'kg.inwardmaster', record['id'], 'confirmed', cr)
		
		return {'type': 'ir.actions.act_window_close'}

kg_dep_issue_wiz()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
