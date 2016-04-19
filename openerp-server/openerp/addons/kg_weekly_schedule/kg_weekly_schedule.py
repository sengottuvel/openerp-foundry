from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')


class kg_weekly_schedule(osv.osv):

	_name = "kg.weekly.schedule"
	_description = "Weekly Schedule Entry"
	_order = "entry_date desc"
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Work Order No.', size=128,select=True,required=True),
		'schedule_no': fields.char('Schedule No', size=128,select=True),
		
	}
		
kg_weekly_schedule()






