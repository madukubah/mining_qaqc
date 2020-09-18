 # -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import time
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_round
import logging
_logger = logging.getLogger(__name__)

class QaqcCoa(models.Model):
	_name = "qaqc.coa.order"
	_order = "id desc"

	@api.multi
	def _check_quantity(self):
		for rec in self:
			product_qty = rec.product_id.with_context({'location' : rec.location_id.id})
			if ( rec.quantity != product_qty.qty_available ) :
				return False	
		return True

	READONLY_STATES = {
        'final': [('readonly', True)],
        'draft': [('readonly', False)],
        'done': [('readonly', True)],
    }
	name = fields.Char(string="Name", size=100 , required=True, states=READONLY_STATES )
	date = fields.Date('Report Date', help='',  default=time.strftime("%Y-%m-%d"), states=READONLY_STATES  )
	initial_date = fields.Date('Date of Initial', help='', required=True, states=READONLY_STATES  )
	final_date = fields.Date('Date of Final', help='', required=True, states=READONLY_STATES  )
	barge_id = fields.Many2one('shipping.barge', string='Barge', states=READONLY_STATES, domain=[ ('active','=',True)], required=True, change_default=True, index=True, track_visibility='always')

	warehouse_id = fields.Many2one(
            'stock.warehouse', 'Origin Warehouse',
			readonly=True,
			store=True,copy=True,
			compute="_onchange_barge_id",
            ondelete="restrict" )
	location_id = fields.Many2one(
            'stock.location', 'Location',
			readonly=True,
			store=True,copy=True,
			compute="_onchange_barge_id",
            ondelete="restrict" )
	product_id = fields.Many2one('product.product', 'Material', required=True, states=READONLY_STATES )
	product_uom = fields.Many2one(
            'product.uom', 'Product Unit of Measure', 
            required=True,
			domain=[ ('category_id.name','=',"Mining")  ],
            default=lambda self: self._context.get('product_uom', False), states=READONLY_STATES)
	quantity = fields.Float( string="Actual Quantity (WMT)", default=0, digits=dp.get_precision('QAQC'), states=READONLY_STATES, store=True )
	curr_quantity = fields.Float( string="Qurrent Quantity (WMT)", default=0, digits=dp.get_precision('QAQC'), readonly=True, store=True, compute="_compute_curr_quantity" )

	rit = fields.Float( string="Rit", default=0, digits=0, states=READONLY_STATES )
	ton_p_rit = fields.Float( string="Ton/Rit", default=0, digits=0, states=READONLY_STATES )
	surveyor_id	= fields.Many2one('res.partner', string='Surveyor', required=True, domain=[ ('is_surveyor','=',True)], states=READONLY_STATES )
	element_specs = fields.One2many(
        'qaqc.element.spec',
        'coa_order_id',
        string='Elements Specifications',
        copy=True, states=READONLY_STATES )
	state = fields.Selection([
        ('draft', 'Draft'), 
		('final', 'Final'),
		('done', 'Done'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')


	@api.multi
	def button_final(self):
		if self._check_quantity() :
			self.state = 'final'
		else :
			raise UserError(_("Please Update Quantity First as same as Actual Quantity") )

	@api.multi
	def button_done(self):
		self.state = 'done'

	@api.multi
	def button_draft(self):
		self.state = 'draft'

	@api.model
	def create(self, values):
		seq = self.env['ir.sequence'].next_by_code('qaqc_barge')
		values["name"] = seq + "/" + values["name"]
		res = super(QaqcCoa, self ).create(values)
		return res

	@api.depends("barge_id" )
	def _onchange_barge_id(self):
		for rec in self:
			if( rec.barge_id ):
				rec.location_id = rec.barge_id.location_id
				rec.warehouse_id = rec.barge_id.warehouse_id
				

	@api.onchange("location_id" )
	def _set_name(self):
		for rec in self:
			if( rec.location_id ):
				rec.name = rec.location_id.name
				
				if rec.surveyor_id :
					rec.name = rec.name + "/" + rec.surveyor_id.surveyor.upper()
				
	@api.depends("location_id", "product_id" )
	def _compute_curr_quantity(self):
		for rec in self:
			if( rec.location_id and rec.product_id ):
				product_qty = rec.product_id.with_context({'location' : rec.location_id.id})
				rec.curr_quantity = product_qty.qty_available
	
	@api.onchange("product_uom")
	def _compute_ton_p_rit(self):
		for rec in self:
			if( rec.product_uom ):
				rec.rit = rec.product_id.uom_id._compute_quantity( rec.curr_quantity , rec.product_uom ) 
				rec.rit = rec.rit if rec.rit else 1
				rec.ton_p_rit = rec.curr_quantity / rec.rit
				

	@api.onchange("surveyor_id" )
	def _surveyor_change(self):
		for rec in self:
			if( rec.location_id and rec.surveyor_id ):
				rec.name = rec.location_id.name
				rec.name = rec.name + "/" + rec.surveyor_id.surveyor.upper()

	@api.multi
	def action_view_change_product_quantity(self):
		if( self.state != "draft" ):
			raise UserError(_('Only Change Product Qty in Draft State') )


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
	
class QaqcElementSpec(models.Model):
	_name = "qaqc.element.spec"

	coa_order_id = fields.Many2one("qaqc.coa.order", string="COA", ondelete="restrict" )
	element_id = fields.Many2one("qaqc.chemical.element", required=True, string="Element", ondelete="restrict" )
	spec = fields.Float( string="Spec", required=True, default=0, digits=dp.get_precision('QAQC') )