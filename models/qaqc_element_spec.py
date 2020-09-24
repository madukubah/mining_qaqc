 # -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import time
from odoo.addons import decimal_precision as dp

class QaqcElementSpec(models.Model):
	_name = "qaqc.element.spec"

	coa_order_id = fields.Many2one("qaqc.coa.order", string="Assay Barge", ondelete="restrict" )
	assay_pile_id = fields.Many2one("qaqc.assay.pile", string="Assay Pile", ondelete="restrict" )
	element_id = fields.Many2one("qaqc.chemical.element", required=True, string="Element", ondelete="restrict" )
	spec = fields.Float( string="Spec", required=True, default=0, digits=dp.get_precision('QAQC') )