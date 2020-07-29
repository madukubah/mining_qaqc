 # -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class Partner(models.Model):
    _inherit = "res.partner"

    is_surveyor	=  fields.Boolean(string="Is Surveyor", store=True, default=False )
    surveyor = fields.Selection([
        ('intertek', 'Intertek'), 
		('carsurin', 'Carsurin'),
		('internal', 'Internal')
        ], string='Surveyor', copy=False, index=True, store=True )
