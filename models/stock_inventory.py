# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_utils


class Inventory(models.Model):
    _inherit = "stock.inventory"
    
    assay_pile_id = fields.Many2one("qaqc.assay.pile",
        'Assay Pile', ondelete='set null', index=True, readonly=True )