 # -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import time
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)

class QaqcAssayPile(models.Model):
	_name = "qaqc.assay.pile"
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_order = "id desc"

	READONLY_STATES = {
        'draft': [('readonly', False)],
        'cancel': [('readonly', True)],
        'confirm': [('readonly', True)],
        'done': [('readonly', True)],
    }
	name = fields.Char(string="Name", size=100 , required=True, readonly=True, default="NEW")
	date = fields.Date('Report Date', help='',  default=fields.Datetime.now, states=READONLY_STATES  )

	employee_id	= fields.Many2one('hr.employee', string='Responsible', required=True, states=READONLY_STATES )
	
	lot_id = fields.Many2one(
        'stock.production.lot', 'Lot',
		required=True, 
		states=READONLY_STATES,
		)
	product_id = fields.Many2one(
		'product.product', 
		'Material', 
		domain=[('type', 'in', ['product', 'consu']) ], 
		related="lot_id.product_id",
		readonly=True
		)

	curr_quantity = fields.Float( string="Current Quantity (WMT)", default=0, digits=dp.get_precision('QAQC'), readonly=True, compute="_compute_curr_quantity" )

	layer_type = fields.Selection([
        ( "limonite" , 'Limonite'),
        ( "saprolite" , 'Saprolite'),
        ] , string='Type', index=True, 
		store=True )

	element_specs = fields.One2many(
        'qaqc.element.spec',
        'assay_pile_id',
        string='Elements Specifications',
		copy=True,
        states=READONLY_STATES )
	state = fields.Selection([
        ('draft', 'Draft'), 
		('cancel', 'Cancelled'),
		('confirm', 'Confirmed'),
		('done', 'Done'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
	user_id = fields.Many2one('res.users', string='User', index=True, track_visibility='onchange', default=lambda self: self.env.user)
	active = fields.Boolean(
        'Active', default=True,
        help="If unchecked, it will allow you to hide the rule without removing it.")

	@api.onchange( 'warehouse_id' )	
	def _change_wh(self):
		for order in self:
			return {
				'domain':{
					'location_id':[('location_id','=',order.warehouse_id.view_location_id.id )] ,
					} 
				}
	@api.onchange( 'lot_id' )	
	def _change_wh(self):
		for order in self:
			order.product_id = order.lot_id.product_id.id

	@api.depends( "product_id", "lot_id" )
	def _compute_curr_quantity(self):
		for order in self:
			if( order.product_id ):
				product_qty = order.product_id.with_context({'lot_id' : order.lot_id.id })
				order.curr_quantity = product_qty.qty_available

	@api.model
	def create(self, values):
		AssayPile = self.env['qaqc.assay.pile']
		assay_piles = AssayPile.search([ ( "lot_id", "=", values["lot_id"] ), ( "active", "=", True ) ])
		for assay_pile in assay_piles:
			if assay_pile.state == "cancel" :
				continue
			if assay_pile.state != "done" :
				raise UserError(_('Cannot create this file because there is similar file with same location and lot ( %s ).') % (assay_pile.name))
			assay_pile.write({'active': False})

		seq = self.env['ir.sequence'].next_by_code('qaqc_pile')
		values["name"] = seq
		res = super(QaqcAssayPile, self ).create(values)
		return res

	@api.multi
	def action_confirm(self):
		for record in self:
			record.state = 'confirm'

	@api.multi
	def action_done(self):
		for record in self:
			record.write({'state': 'done'})

	@api.multi
	def action_reload(self):
		for order in self:
			order._compute_curr_quantity( )

	@api.multi
	def action_draft(self):
		for record in self:
			record.write({'state': 'draft'})

	@api.multi
	def action_cancel(self):
		for record in self:
			record.write({'state': 'cancel'})

	@api.multi
	def unlink(self):
		for record in self:
			if record.state == 'done':
				raise UserError(_('Unable to Delete record %s in State Done.') % (record.name))
		return super(QaqcAssayPile, self ).unlink()