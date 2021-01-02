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
	surveyor_id	= fields.Many2one('res.partner', string='Surveyor', related="coa_order_id.surveyor_id", domain=[ ('is_surveyor','=',True)], store=True )
	location_id = fields.Many2one(
		'stock.location', 'Location',
		related="coa_order_id.location_id",
		store=True,copy=True,
		ondelete="restrict" )
	spec = fields.Float( string="Spec", required=True, default=0, digits=dp.get_precision('QAQC') )