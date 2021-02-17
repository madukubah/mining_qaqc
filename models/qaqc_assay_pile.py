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
	warehouse_id = fields.Many2one(
            'stock.warehouse', 'Origin Warehouse',
			store=True,copy=True,
			required=True, 
			states=READONLY_STATES,
            ondelete="restrict" )
	location_id = fields.Many2one(
            'stock.location', 'Location',
			store=True,copy=True,
			required=True, 
			states=READONLY_STATES,
            ondelete="restrict" )
	lot_id = fields.Many2one(
        'stock.production.lot', 'Lot',
		required=True, 
		states=READONLY_STATES,
		)
	product_id = fields.Many2one(
		'product.product', 
		'Material', 
		domain=[('type', 'in', ['product', 'consu']) ], 
		required=True, 
		states=READONLY_STATES
		)
	quantity = fields.Float( string="Actual Quantity (WMT)", required=True, default=0, digits=dp.get_precision('QAQC'), states=READONLY_STATES, store=True )
	curr_quantity = fields.Float( string="Current Quantity (WMT)", store=True, default=0, digits=dp.get_precision('QAQC'), readonly=True, compute="_compute_curr_quantity" )
	
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
	inventory_ids = fields.One2many('stock.inventory', "assay_pile_id", string='Inventory', copy=False)	
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

	@api.depends("location_id", "product_id" )
	def _compute_curr_quantity(self):
		for order in self:
			if( order.location_id and order.product_id ):
				product_qty = order.product_id.with_context({'location' : order.location_id.id, 'lot_id' : order.lot_id.id })
				order.curr_quantity = product_qty.qty_available
				order.quantity = order.curr_quantity

	@api.model
	def create(self, values):
		AssayPile = self.env['qaqc.assay.pile']
		assay_piles = AssayPile.search([ ( "location_id", "=", values["location_id"] ), ( "lot_id", "=", values["lot_id"] ), ( "active", "=", True ) ])
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
			if( record.product_id.type not in ['product', 'consu'] ) :
				raise UserError(_('Stockable product Only') )
			record._create_inv_adjust()
			record.state = 'confirm'

	@api.multi
	def action_done(self):
		for record in self:
			for inventory in record.inventory_ids:
				if inventory.state == 'confirm':
					inventory.action_done()
		
			record.write({'state': 'done'})

	@api.multi
	def action_reload(self):
		for order in self:
			order._compute_curr_quantity( )

	@api.multi
	def action_draft(self):
		for record in self:
			record.remove_inv_ids()
			record.write({'state': 'draft'})

	@api.multi
	def action_cancel(self):
		for record in self:
			record.remove_inv_ids()
			record.write({'state': 'cancel'})

	@api.multi
	def unlink(self):
		for record in self:
			record.remove_inv_ids()
		return super(QaqcAssayPile, self ).unlink()

	def remove_inv_ids(self):
		for record in self:
			for inventory in record.inventory_ids:
				if inventory.state == 'done':
					raise UserError(_('Unable to cancel record %s as some receptions have already been done.') % (record.name))

			for inventory in record.inventory_ids.filtered(lambda r: r.state != 'cancel'):
				inventory.action_cancel_draft()
				inventory.unlink()

	# suspend
	# TODO implement it when _create_inv_adjust call
	@api.multi
	def _prepare_inventory_lines(self):
		line_ids = []
		product = self.product_id.with_context(location=self.location_id.id, lot_id=self.lot_id.id)
		th_qty = product.qty_available
		line_ids.append( (0, 0, 
			{
				'product_qty': self.quantity,
				'location_id': self.location_id.id,
				'product_id': self.product_id.id,
				'product_uom_id': self.product_id.uom_id.id,
				'theoretical_qty': th_qty,
				'prod_lot_id': self.lot_id.id,
			}
		) )
		return line_ids
		
	@api.multi
	def _create_inv_adjust(self):
		""" Changes the Product Quantity by making a Physical Inventory. """
		Inventory = self.env['stock.inventory']
		InventoryLine = self.env['stock.inventory.line']
		ProductionConfig = self.env['production.config'].sudo()

		production_config = ProductionConfig.search([ ( "active", "=", True ) ]) 
		if not production_config :
			raise UserError(_('Please Set Default Lot In Configuration file Mining Production') )

		for record in self:
			# product = record.product_id.with_context(location=record.location_id.id, lot_id=record.lot_id.id)
			# line_ids = []
			inventory = Inventory.create({
				'name': _('INV: %s/%s') % (record.name, record.product_id.name),
				'filter': 'product',
				'assay_pile_id': record.id,
				'product_id': record.product_id.id,
				'location_id': record.location_id.id,
			})
			inventory.onchange_filter()
			inventory.prepare_inventory()
			for line in inventory.line_ids:
				if line.prod_lot_id.id == production_config[0].lot_id.id :
					line.product_qty = line.theoretical_qty - record.quantity if ( line.theoretical_qty - record.quantity ) >= 0 else 0
					if line.prod_lot_id.id == record.lot_id.id :
						line.unlink()
				else :
					line.unlink()

			product = record.product_id.with_context(location=record.location_id.id, lot_id=record.lot_id.id)
			th_qty = product.qty_available
			InventoryLine.create({
				'inventory_id': inventory.id,
				'product_qty': record.quantity,
				'location_id': record.location_id.id,
				'product_id': record.product_id.id,
				'product_uom_id': record.product_id.uom_id.id,
				'theoretical_qty': th_qty,
				'prod_lot_id': record.lot_id.id,
			})