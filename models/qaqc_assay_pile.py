 # -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import time
from odoo.addons import decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

class QaqcAssayPile(models.Model):
	_name = "qaqc.assay.pile"
	_order = "id desc"

	READONLY_STATES = {
        'draft': [('readonly', False)],
        'cancel': [('readonly', True)],
        'confirm': [('readonly', True)],
        'done': [('readonly', True)],
    }
	name = fields.Char(string="Name", size=100 , required=True, readonly=True, default="NEW")
	date = fields.Date('Report Date', help='',  default=time.strftime("%Y-%m-%d"), states=READONLY_STATES  )

	employee_id	= fields.Many2one('hr.employee', string='Responsible', states=READONLY_STATES )
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
	block_id = fields.Many2one('production.block', string='Block', ondelete="restrict", states=READONLY_STATES )
	product_id = fields.Many2one('product.product', 'Material', required=True, states=READONLY_STATES )
	lot_id = fields.Many2one(
        'stock.production.lot', 'Lot',
		required=True, 
		states=READONLY_STATES,
        domain="[('product_id', '=', product_id)]")
	quantity = fields.Float( string="Actual Quantity (WMT)", required=True, default=0, digits=dp.get_precision('QAQC'), states=READONLY_STATES, store=True )
	# curr_quantity = fields.Float( string="Qurrent Quantity (WMT)", default=0, digits=dp.get_precision('QAQC'), readonly=True, compute="_compute_curr_quantity" )
	element_specs = fields.One2many(
        'qaqc.element.spec',
        'assay_pile_id',
        string='Elements Specifications',
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
	def button_confirm(self):
		self._create_inv_adjust()
		self.state = 'confirm'

	@api.multi
	def button_done(self):
		for record in self:
			for inventory in record.inventory_ids:
				if inventory.state == 'confirm':
					inventory.action_done()
		
		self.write({'state': 'done'})

	@api.multi
	def button_draft(self):
		for record in self:
			for inventory in record.inventory_ids:
				if inventory.state == 'done':
					raise UserError(_('Unable to cancel record %s as some receptions have already been done.') % (record.name))

			for inventory in record.inventory_ids.filtered(lambda r: r.state != 'cancel'):
				inventory.action_cancel_draft()
				inventory.unlink()

		self.write({'state': 'draft'})

	@api.multi
	def button_cancel(self):
		for record in self:
			for inventory in record.inventory_ids:
				if inventory.state == 'done':
					raise UserError(_('Unable to cancel record %s as some receptions have already been done.') % (record.name))

			for inventory in record.inventory_ids.filtered(lambda r: r.state != 'cancel'):
				inventory.action_cancel_draft()
				inventory.unlink()

		self.write({'state': 'cancel'})

	@api.multi
	def _prepare_inventory_lines(self):
		line_ids = []
		no_lot_product = self.product_id.with_context(location=self.location_id.id, lot_id=None )
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
		for record in self:
			# product = record.product_id.with_context(location=record.location_id.id, lot_id=record.lot_id.id)
			# line_ids = []
			inventory = Inventory.create({
				'name': _('INV: Assay/1/%s') % (record.product_id.name),
				'filter': 'product',
				'assay_pile_id': record.id,
				'product_id': record.product_id.id,
				'location_id': record.location_id.id,
			})
			inventory.onchange_filter()
			inventory.prepare_inventory()
			for line in inventory.line_ids:
				if not line.prod_lot_id :
					line.product_qty = line.theoretical_qty - record.quantity if ( line.theoretical_qty - record.quantity ) >= 0 else 0
				if line.prod_lot_id :
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