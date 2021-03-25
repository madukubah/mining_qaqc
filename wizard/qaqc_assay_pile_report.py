# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from calendar import monthrange
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class QaqcAssayPileReport(models.TransientModel):
    _name = 'qaqc.assay.pile.report'

    @api.model
    def _default_elements(self):
        chemical_elements = self.env['qaqc.chemical.element'].sudo().search([ ] )
        return chemical_elements.ids 

    @api.model
    def _default_product(self):
        ProductionConfig = self.env['production.config'].sudo()
        production_config = ProductionConfig.search([ ( "active", "=", True ) ]) 
        if not production_config :
            raise UserError(_('Please Set Configuration file') )
        return production_config[0].main_product_id

    element_ids = fields.Many2many('qaqc.chemical.element', 'qaqc_assay_pile_element_rel', 'qaqc_assay_pile_id', 'element_id', 'Element To Show', default=_default_elements )
    type = fields.Selection([
        ( "detail" , 'Detail'),
        ( "summary" , 'Summary'),
        ], default="detail", string='Type', index=True, required=True )
    product_id = fields.Many2one(
		'product.product', 
		'Material', default=_default_product )
    warehouse_id = fields.Many2one(
            'stock.warehouse', 'Warehouse',
            required=True )
    is_all = fields.Boolean(string="All Location", Default=False )
    location_ids = fields.Many2many('stock.location', 'qaqc_assay_pile_report_location_rel', 'qaqc_assay_pile_id', 'location_id', 'Location' )

    @api.onchange('is_all')
    def action_reload(self):
        for record in self: 
            if record.is_all :
                location_ids = self.env['stock.location'].sudo( ).search( [ ('location_id','=',record.warehouse_id.view_location_id.id ) ] )
                record.location_ids = location_ids
            else :
                record.location_ids = []

    @api.multi
    def action_print(self):  
        element_names = [ element_id.name for element_id in self.element_ids ]
        # locations = self.env['stock.quant'].sudo( ).search( [ ("id", "in", self.location_ids.ids ) ] )
        loc_coa_dict = {}
        waiting = {}
        waiting["summary"] = {
                "location_name" : "Waiting Assay Result",
                "quantity" : 0,
            }
        for element_id in self.element_ids:
            waiting["summary"][ element_id.name ] = 0

        for location in self.location_ids :
            loc_coa_dict[ location.name ] = {}
            loc_coa_dict[ location.name ]["list"] = []
            loc_coa_dict[ location.name ]["summary"] = {
                "location_name" : location.name,
                "quantity" : 0,
            }
            for element_id in self.element_ids:
                loc_coa_dict[ location.name ]["summary"][ element_id.name+"_ton" ] = 0

            lot_qty_dict = {}
            quants = self.env['stock.quant'].sudo().search([ ('location_id','=', location.id ), ('product_id','=', self.product_id.id ) ])
            for quant in quants :
                if not quant.lot_id : continue
                if lot_qty_dict.get( quant.lot_id.id, False ):
                    lot_qty_dict[ quant.lot_id.id ] += quant.qty
                else:
                    lot_qty_dict[ quant.lot_id.id ] = quant.qty

            for lot_id, qty in lot_qty_dict.items() :
                assay_piles = self.env['qaqc.assay.pile'].search([ ("lot_id", "=", lot_id ) ], limit=1)
                if not assay_piles : 
                    waiting["summary"]["quantity"] += qty
                    row = {}
                    row["date"] = assay_pile.date
                    row["lot_name"] = "[waiting] "+assay_pile.lot_id.name
                    row["quantity"] = qty
                    loc_coa_dict[ location.name ]["summary"]["quantity"] += row["quantity"]
                    row["layer_type"] = "waiting"
                    for element_id in self.element_ids:
                        row[ element_id.name ] = 0
                        row[ element_id.name+"_ton" ] = 0
                    loc_coa_dict[ location.name ]["list"] += [row]

                for assay_pile in assay_piles :
                    row = {}
                    row["date"] = assay_pile.date
                    row["lot_name"] = assay_pile.lot_id.name
                    row["quantity"] = qty
                    loc_coa_dict[ location.name ]["summary"]["quantity"] += row["quantity"]

                    row["layer_type"] = assay_pile.layer_type
                    # set elem as column
                    for element_id in self.element_ids:
                        row[ element_id.name ] = 0
                        row[ element_id.name+"_ton" ] = 0
                    for element_spec in assay_pile.element_specs:
                        row[ element_spec.element_id.name ] = element_spec.spec
                        row[ element_spec.element_id.name+"_ton" ] = element_spec.spec * row["quantity"]
                        loc_coa_dict[ location.name ]["summary"][ element_spec.element_id.name+"_ton" ] += element_spec.spec * row["quantity"]

                    loc_coa_dict[ location.name ]["list"] += [row]
            
            for element_id in self.element_ids:
                loc_coa_dict[ location.name ]["summary"][ element_id.name ] = 0
                if loc_coa_dict[ location.name ]["summary"]["quantity"] :
                    assay = loc_coa_dict[ location.name ]["summary"][ element_id.name+"_ton" ] / loc_coa_dict[ location.name ]["summary"]["quantity"]
                    loc_coa_dict[ location.name ]["summary"][ element_id.name ] = round(assay, 2)

        if self.type == "summary":
            loc_coa_dict["Waiting Assay Result"] = waiting
            
        final_dict = loc_coa_dict
        datas = {
            'ids': self.ids,
            'model': 'qaqc.assay.pile.report',
            'type': self.type,
            'form': final_dict,
            'element_names': element_names,
        }
        return self.env['report'].with_context( landscape=(len( element_names ) > 3) ).get_action(self,'mining_qaqc.qaqc_assay_pile_temp', data=datas)
