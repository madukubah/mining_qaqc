 # -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import time
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_round
import logging
_logger = logging.getLogger( __name__ )

class QaqcCoa(models.Model):
	_name = "qaqc.coa.order"
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_order = "id desc"

	@api.multi
	def _check_quantity(self):
		for order in self:
			if order.surveyor_id.surveyor != "main" :
				return
			order._compute_curr_quantity()
			product_qty = order.product_id.with_context({'location' : order.location_id.id})
			if ( order.quantity > product_qty.qty_available ) :
				raise UserError(_("Actual Quantity Cannot Bigger Than Qty on Location ( Qty on Location is %s )" % product_qty.qty_available ) )	

	READONLY_STATES = {
        'draft': [('readonly', False)],
        'confirm': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }
	name = fields.Char(string="Name", size=100 , required=True, states=READONLY_STATES )
	date = fields.Date('Report Date', help='',  default=fields.Datetime.now , states=READONLY_STATES  )
	initial_date = fields.Date('Date of Initial', help='', required=True, states=READONLY_STATES  )
	final_date = fields.Date('Date of Final', help='', required=True, states=READONLY_STATES  )
	barge_id = fields.Many2one('shipping.barge', string='Barge', states=READONLY_STATES, domain=[ ('active','=',True)], required=True, change_default=True, index=True, track_visibility='always')

	warehouse_id = fields.Many2one(
            'stock.warehouse', 'Origin Warehouse',
			# readonly=True,
			store=True,copy=True,
			compute="_onchange_barge_id",
            ondelete="restrict" )
	location_id = fields.Many2one(
            'stock.location', 'Location',
			# readonly=True,
			store=True,copy=True,
			compute="_onchange_barge_id",
            ondelete="restrict" )
	product_id = fields.Many2one('product.product', 'Material', domain=[('type', 'in', ['product', 'consu'])], required=True, states=READONLY_STATES )
	product_uom = fields.Many2one(
            'product.uom', 'Product Unit of Measure', 
            required=True,
			domain=[ ('category_id.name','=',"Mining")  ],
            default=lambda self: self._context.get('product_uom', False), states=READONLY_STATES)
	quantity = fields.Float( string="Actual Quantity (WMT)", default=0, digits=dp.get_precision('QAQC'), states=READONLY_STATES, store=True )
	curr_quantity = fields.Float( string="Current Quantity (WMT)", store=True, default=0, digits=dp.get_precision('QAQC'), readonly=True, compute="_compute_curr_quantity" )

	rit = fields.Float( string="Rit", default=0, digits=0, states=READONLY_STATES, compute="_compute_ton_p_rit" )
	ton_p_rit = fields.Float( string="Ton/Rit", default=0, digits=0, states=READONLY_STATES, compute="_compute_ton_p_rit" )
	surveyor_id	= fields.Many2one('res.partner', string='Surveyor', required=True, domain=[ ('is_surveyor','=',True)], states=READONLY_STATES )
	main_surveyor	= fields.Boolean( string='Is Main Surveyor', default=False, compute="compute_main_surveyor", help="Technical field" )
	element_specs = fields.One2many(
        'qaqc.element.spec',
        'coa_order_id',
        string='Elements Specifications',
        copy=True, states=READONLY_STATES )
	state = fields.Selection([
        ('draft', 'Draft'), 
		('cancel', 'Cancelled'),
		('confirm', 'Final'),
		('done', 'Done'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
	user_id = fields.Many2one('res.users', string='User', index=True, track_visibility='onchange', default=lambda self: self.env.user)
	active = fields.Boolean(
        'Active', default=True,
        help="If unchecked, it will allow you to hide the rule without removing it.")

	
	def compute_main_surveyor(self):
		for order in self:
			order.main_surveyor = order.surveyor_id.surveyor == "main"
	@api.multi
	def action_confirm(self):
		for order in self:
			order._check_quantity()
			order.state = 'confirm'

	@api.multi
	def action_done(self):
		for order in self:
			if order.state == 'done' :
				continue
			if order.state != 'confirm':
				raise UserError(_("Please Set Assay Result Barge To Final First") )
			order.state = 'done'

	@api.multi
	def action_draft(self):
		for order in self:
			order.state = 'draft'

	@api.multi
	def action_cancel(self):
		for order in self:
			if order.state == 'done':
				raise UserError(_('Unable to cancel order %s as some receptions have already been done.') % (order.name))
			order.state = 'cancel'

	@api.multi
	def action_reload(self):
		for order in self:
			order._compute_curr_quantity( )

	@api.model
	def create(self, values):
		CoaOrder = self.env['qaqc.coa.order']
		barge = self.env['shipping.barge'].search([ ( "id", "=", values["barge_id"] ) ])
		coa_orders = []
		# if values.get("location_id", False) :
		coa_orders = CoaOrder.search([ ( "location_id", "=", barge.location_id.id ), ( "surveyor_id", "=", values["surveyor_id"] ), ( "product_id", "=", values["product_id"] ), ( "active", "=", True ) ])
		for coa_order in coa_orders:
			if coa_order.state == "cancel" :
				continue
			if coa_order.state != "done" :
					raise UserError(_('Cannot create this file because there is similar file with same location, material and surveyor ( %s ).') % (coa_order.name))
			coa_order.write({'active': False})

		seq = self.env['ir.sequence'].next_by_code('qaqc_barge')
		values["name"] = seq + "/" + values["name"]
		res = super(QaqcCoa, self ).create(values)
		return res

	@api.depends("barge_id" )
	def _onchange_barge_id(self):
		for order in self:
			if( order.barge_id ):
				order.location_id = order.barge_id.location_id
				order.warehouse_id = order.barge_id.warehouse_id
				

	@api.onchange("location_id" )
	def _set_name(self):
		for order in self:
			if( order.location_id ):
				order.name = order.location_id.name
				
				if order.surveyor_id :
					order.name = order.name + "/" + order.surveyor_id.code_name.upper()
				
	@api.depends("location_id", "product_id" )
	def _compute_curr_quantity(self):
		for order in self:
			if( order.location_id and order.product_id ):
				product_qty = order.product_id.with_context({'location' : order.location_id.id})
				order.curr_quantity = product_qty.qty_available
	
	@api.depends("product_uom", "curr_quantity")
	def _compute_ton_p_rit(self):
		for order in self:
			if( order.product_uom ):
				order.rit = order.product_id.uom_id._compute_quantity( order.curr_quantity , order.product_uom ) 
				order.ton_p_rit = order.curr_quantity / ( order.rit if order.rit else 1 )
				

	@api.onchange("surveyor_id" )
	def _surveyor_change(self):
		for order in self:
			if( order.location_id and order.surveyor_id ):
				order.name = order.location_id.name
				order.name = order.name + "/" + order.surveyor_id.code_name.upper()

	@api.multi
	def action_view_change_product_quantity(self):
		if self.surveyor_id.surveyor != "main" :
			raise UserError(_('Only Main Surveyor Can Change Product Qty') )
		if( self.state != "draft" ):
			raise UserError(_('Only Change Product Qty in Draft State') )

		if( self.product_id.type not in ['product', 'consu'] ) :
			raise UserError(_('Stockable product Only') )

		return {    
			'name': _("Update Qty On Hand"),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'stock.change.product.qty',
			'view_id': self.env.ref( "stock.view_change_product_quantity" ).id,
			'target': 'new',
			'context': { 
				'default_product_id': self.product_id.id, 
				"default_product_tmpl_id" : self.product_id.product_tmpl_id.id,
				"default_location_id" : self.location_id.id,
				"default_new_quantity" : self.quantity,
				 }
		}

	@api.multi
	def unlink(self):
		for order in self:
			if order.state != "draft" :
				raise UserError(_("Only Delete data in Draft State") )
		
		return super(QaqcCoa, self ).unlink()