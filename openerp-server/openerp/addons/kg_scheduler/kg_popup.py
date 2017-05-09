from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
import openerp.addons.decimal_precision as dp
import netsvc
import datetime
import openerp
from datetime import date
import urllib
import urllib2
import logging
import base64
logger = logging.getLogger('server')

class kg_popup(osv.osv):
	
	_name = "kg.popup"
	_description = "Popup Details"
	
	_columns = {
		
		## Version 0.1
		
		## Basic Info
		
		'name': fields.char('Name',size=12,select=True),
		
		}
	
	def get_product_expiry_reminder_data(self,cr,uid,ids,context=None):
		
		final_data = []
		
		cr.execute("""select lot.grn_no as grn_no,prod.name_template as product,uom.name as uom,to_char(lot.expiry_date, 'dd/mm/yyyy') as expiry_date,lot.pending_qty as pending_qty,lot.batch_no as batch_no
						
						from stock_production_lot lot
						
						left join product_product prod on(prod.id=lot.product_id)
						left join product_uom uom on(uom.id=lot.product_uom)
						
						where lot.pending_qty >0 and lot.product_id in (select id from product_product where flag_expiry_alert='t') 
						and lot.expiry_date-interval'5' day <= current_date and lot.expiry_date > current_date order by expiry_date""")
		final_data = cr.fetchall();
		
		#~ cr.execute('''select grn_no,product_id,product_uom,expiry_date from stock_production_lot 
					  #~ where pending_qty >0 and product_id in (select id from product_product where flag_expiry_alert='t') and expiry_date <= 
					  #~ (select current_date+interval'5' day) order by expiry_date''')
		#~ 
		#~ final_data=cr.dictfetchall()
		
		print"datadatadata",final_data
		
		return final_data

kg_popup()
