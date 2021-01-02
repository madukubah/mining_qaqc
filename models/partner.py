 # -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class Partner(models.Model):
    _inherit = "res.partner"

    is_surveyor	=  fields.Boolean(string="Is Surveyor", store=True, default=False )
    code_name = fields.Char(string="Code Name", size=100 , default="-", store=True )
    surveyor = fields.Selection([
        ('main', 'Main'), 
        ('other', 'Others'),
        ], string='Surveyor', copy=True, index=True, store=True )
