 # -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import time
from odoo.addons import decimal_precision as dp

class QaqcCoa(models.Model):
	_name = "qaqc.coa.order"
	_order = "id desc"

	READONLY_STATES = {
        'final': [('readonly', True)],
        'draft': [('readonly', False)],
        'done': [('readonly', True)],
    }
	name = fields.Char(string="Name", size=100 , required=True, states=READONLY_STATES )
	date = fields.Date('Report Date', help='',  default=time.strftime("%Y-%m-%d"), states=READONLY_STATES  )
	initial_date = fields.Date('Date of Initial', help='', required=True, states=READONLY_STATES  )
	final_date = fields.Date('Date of Final', help='', required=True, states=READONLY_STATES  )
	location_id = fields.Many2one(
            'stock.location', 'Location',
			domain=[ ('usage','=',"internal")  ],
            ondelete="restrict", required=True, states=READONLY_STATES)
	product_id = fields.Many2one('product.product', 'Material', required=True, states=READONLY_STATES )
	product_uom = fields.Many2one(
            'product.uom', 'Product Unit of Measure', 
			# related='product_id.uom_id',
            required=True,
			domain=[ ('category_id.name','=',"Mining")  ],
            default=lambda self: self._context.get('product_uom', False), states=READONLY_STATES)
	quantity = fields.Float( string="Quantity (WMT)", default=0, digits=dp.get_precision('QAQC'), states=READONLY_STATES, store=True, compute="_compute_quantity" )
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
		self.state = 'final'

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


	@api.onchange("location_id" )
	def _set_name(self):
		for rec in self:
			if( rec.location_id ):
				rec.name = rec.location_id.name
				
				if rec.surveyor_id :
					rec.name = rec.name + "/" + rec.surveyor_id.surveyor.upper()
				
	@api.onchange("location_id", "product_id" )
	def _compute_quantity(self):
		for rec in self:
			if( rec.location_id and rec.product_id ):
				StockQuantSudo = self.env['stock.quant'].sudo()
				stock_quants = StockQuantSudo.search([ ("product_id", '=', rec.product_id.id ), ("location_id", '=', rec.location_id.id ) ])
				# qty = self.product_uom_id._compute_quantity(self.product_qty, self.product_id.uom_id)
				rec.quantity = sum([ stock_quant.qty for stock_quant in stock_quants ])
	
	@api.onchange("product_uom")
	def _compute_ton_p_rit(self):
		for rec in self:
			if( rec.product_uom ):
				rec.rit = rec.product_id.uom_id._compute_quantity( rec.quantity , rec.product_uom ) 
				rec.rit = rec.rit if rec.rit else 1
				rec.ton_p_rit = rec.quantity / rec.rit
				

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
		# '''
    	# This function returns an action that display existing picking orders of given purchase order ids.
        # When only one found, show the picking immediately.
        # '''
		# action = self.env.ref('stock.action_picking_tree')
		# result = action.read()[0]

        # #override the context to get rid of the default filtering on picking type
		# result.pop('id', None)
		# result['context'] = {}
		# pick_ids = sum([order.picking_ids.ids for order in self], [])
        # #choose the view_mode accordingly
		# if len(pick_ids) > 1:
		# 	result['domain'] = "[('id','in',[" + ','.join(map(str, pick_ids)) + "])]"
		# elif len(pick_ids) == 1:
		# 	res = self.env.ref('stock.view_picking_form', False)
		# 	result['views'] = [(res and res.id or False, 'form')]
		# 	result['res_id'] = pick_ids and pick_ids[0] or False
		# return result

class QaqcElementSpec(models.Model):
	_name = "qaqc.element.spec"

	coa_order_id = fields.Many2one("qaqc.coa.order", string="COA", ondelete="restrict" )
	element_id = fields.Many2one("qaqc.chemical.element", required=True, string="Element", ondelete="restrict" )
	spec = fields.Float( string="Spec", required=True, default=0, digits=dp.get_precision('QAQC') )