from openerp.osv import osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp import pooler

from osv import fields, osv

class kg_ms_partlist_wiz(osv.osv_memory):
	"""
	This wizard will confirm the all the selected draft inward
	"""

	_name = "kg.ms.partlist.wiz"
	_description = "MS Batch Accepted"
	
	_columns = {
		
		'remark': fields.char('Remarks'),
		
		}
				
	def ms_received_confirm(self, cr, uid, ids, context=None):
		rec = self.browse(cr,uid,ids[0])
		wf_service = netsvc.LocalService('workflow')
		if context is None:
			context = {}
		pool_obj = pooler.get_pool(cr.dbname)
		ms_ids = pool_obj.get('kg.ms.stores').read(cr, uid, context['active_ids'], ['accept_state'], context=context)
		ms_obj = self.pool.get('kg.ms.stores')
		for record in ms_ids:			
			s = record.get('id')
			print"sssssssssssssssss",s
			
			ms_rec = ms_obj.entry_accept(cr,uid,[s])
			
		
		return {'type': 'ir.actions.act_window_close'}

kg_ms_partlist_wiz()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
