 # -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import time

class QaqcChemicalElement(models.Model):
	_name = "qaqc.chemical.element"
	_order = "id desc"

	name = fields.Char(string="Name", size=100 , required=True )
	code = fields.Char(string="Code", size=10 , required=True )
	