# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models
from calendar import monthrange
_logger = logging.getLogger(__name__)

class QaqcCoaOrderReport(models.TransientModel):
    _name = 'qaqc.coa.order.report'

    @api.model
    def _default_elements(self):
        chemical_elements = self.env['qaqc.chemical.element'].sudo().search([ ] )
        return chemical_elements.ids 

    element_ids = fields.Many2many('qaqc.chemical.element', 'qaqc_coa_element_rel', 'qaqc_coa_id', 'element_id', 'Element To Show', default=_default_elements )

    @api.multi
    def action_print(self):       
        coa_orders = self.env['qaqc.coa.order'].search([ ( 'active', '=', True ), ( 'state', 'in', ['confirm', 'done', 'draft' ] ) ])
        element_names = []
        for element_id in self.element_ids:
            element_names += [ element_id.name ]

        final_dict = {}
        loc_coa_dict = {}
        for coa_order in coa_orders:
            row = {}
            row["date"] = coa_order.date
            row["doc_name"] = coa_order.name
            row["location_name"] = coa_order.location_id.name
            row["surveyor_name"] = coa_order.surveyor_id.name
            row["quantity"] = coa_order.quantity
            row["state"] = coa_order.state
            # set elem as column
            for element_id in self.element_ids:
                row[ element_id.name ] = 0
            for element_spec in coa_order.element_specs:
                # if row.get( element_spec.element_id.name , False):
                row[ element_spec.element_id.name ] = element_spec.spec

            if loc_coa_dict.get( coa_order.location_id.name , False):
                loc_coa_dict[ coa_order.location_id.name ] += [row]
            else :
                loc_coa_dict[ coa_order.location_id.name ] = [row]

        final_dict = loc_coa_dict
        datas = {
            'ids': self.ids,
            'model': 'qaqc.coa.order.report',
            'form': final_dict,
            'element_names': element_names,
        }
        return self.env['report'].get_action(self,'mining_qaqc.qaqc_coa_order_temp', data=datas)
