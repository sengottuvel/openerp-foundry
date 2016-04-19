from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from datetime import date
import openerp.addons.decimal_precision as dp
from datetime import datetime

dt_time = time.strftime('%m/%d/%Y %H:%M:%S')


class kg_daily_planning(osv.osv):

	_name = "kg.daily.planning"
	_description = "Planning (BOM)"
	_order = "entry_date desc"
	
	
	_columns = {
	
		### Header Details ####
		'name': fields.char('Schedule No', size=128,select=True,readonly=True),
		'entry_date': fields.date('Schedule Date',required=True),
		
	}
	
kg_daily_planning()
