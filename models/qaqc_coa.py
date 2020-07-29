 # -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import time

class QaqcCoa(models.Model):
	_name = "qaqc.coa"
	_order = "id desc"

	name = fields.Char(string="Name", size=100 , required=True, readonly=True, states={'draft': [('readonly', False)]})
	date = fields.Date('Report Date', help='',  default=time.strftime("%Y-%m-%d"), readonly=True, states={'draft': [('readonly', False)]} )
	initial_date = fields.Date('Date of Initial', help='', required=True, readonly=True, states={'draft': [('readonly', False)]} )
	final_date = fields.Date('Date of Final', help='', required=True, readonly=True, states={'draft': [('readonly', False)]} )

	shipping_id = fields.Many2one("shipping.shipping", string="Shipping", required=True, store=True, ondelete="restrict", domain=[ ('state','=',"approve")], readonly=True, states={'draft': [('readonly', False)]}  )
	
	loading_port = fields.Many2one("shipping.port", related="shipping_id.loading_port", string="Loading Port", readonly=True, store=True, ondelete="restrict" )
	discharging_port = fields.Many2one("shipping.port", related="shipping_id.discharging_port", string="Discharging Port", readonly=True, store=True, ondelete="restrict" )
	quantity = fields.Float( string="Quantity (WMT)", related="shipping_id.quantity", required=True, default=0, digits=0, store=True, readonly=True )

	surveyor_id	= fields.Many2one('res.partner', string='Surveyor', required=True, domain=[ ('is_surveyor','=',True)], readonly=True, states={'draft': [('readonly', False)]} )

	mc_spec = fields.Float( string="MC (%)", required=True, default=0, digits=0, readonly=True, states={'draft': [('readonly', False)]} )
	ni_spec = fields.Float( string="Ni (%)", required=True, default=0, digits=0, readonly=True, states={'draft': [('readonly', False)]} )
	fe_spec = fields.Float( string="Fe (%)", required=True, default=0, digits=0, readonly=True, states={'draft': [('readonly', False)]} )
	co_spec = fields.Float( string="Co (%)", required=True, default=0, digits=0, readonly=True, states={'draft': [('readonly', False)]} )
	p_spec = fields.Float( string="P (%)", required=True, default=0, digits=0, readonly=True, states={'draft': [('readonly', False)]} )
	s_spec = fields.Float( string="S (%)", required=True, default=0, digits=0, readonly=True, states={'draft': [('readonly', False)]} )
	sio2_spec = fields.Float( string="SiO2 (%)", required=True, default=0, digits=0, readonly=True, states={'draft': [('readonly', False)]} )
	mgo_spec = fields.Float( string="MgO (%)", required=True, default=0, digits=0, readonly=True, states={'draft': [('readonly', False)]} )
	al2o3_spec = fields.Float( string="Al2O3 (%)", required=True, default=0, digits=0, readonly=True, states={'draft': [('readonly', False)]} )
	cao_spec = fields.Float( string="CaO (%)", required=True, default=0, digits=0, readonly=True, states={'draft': [('readonly', False)]} )
	cr2o3_spec = fields.Float( string="Cr2O3 (%)", required=True, default=0, digits=0, readonly=True, states={'draft': [('readonly', False)]} )
	mno_spec = fields.Float( string="MnO (%)", required=True, default=0, digits=0, readonly=True, states={'draft': [('readonly', False)]} )
	# moisture_spec = fields.Float( string="Moisture (%)", required=True, default=0, digits=0, readonly=True, states={'draft': [('readonly', False)]} )
	

	state = fields.Selection([
        ('draft', 'Draft'), 
		('final', 'Final'),
		('done', 'Done'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')


	@api.multi
	def button_final(self):
		if not self.env.user.has_group('sale_qaqc.qaqc_group_manager') :
			raise UserError(_("You are not manager") )
		self.state = 'final'

	@api.multi
	def button_done(self):
		if not self.env.user.has_group('sale_qaqc.qaqc_group_manager') :
			raise UserError(_("You are not manager") )
		self.state = 'done'

	@api.multi
	def button_draft(self):
		if not self.env.user.has_group('sale_qaqc.qaqc_group_manager') :
			raise UserError(_("You are not manager") )

		self.state = 'draft'
		

	@api.onchange("shipping_id" )
	def _set_shipping(self):
		for rec in self:
			if( rec.shipping_id ):
				rec.name = rec.shipping_id.name
				rec.loading_port = rec.shipping_id.loading_port
				rec.discharging_port = rec.shipping_id.discharging_port
				rec.quantity = rec.shipping_id.quantity
	