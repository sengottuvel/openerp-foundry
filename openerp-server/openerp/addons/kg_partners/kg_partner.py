from functools import partial
import logging
from lxml import etree
from lxml.builder import E

import openerp
from openerp import SUPERUSER_ID
from openerp import pooler, tools
import openerp.exceptions
from openerp.osv import fields,osv
from openerp.osv.orm import browse_record
from openerp.tools.translate import _


class kg_partner(osv.osv):

	_name = "res.partner"
	_inherit = "res.partner"
	_description = "Partner Managment"
	
	_columns = {
	
	'city_id' : fields.many2one('res.city', 'City'),
		
	}
		
kg_partner()
