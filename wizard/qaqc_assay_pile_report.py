# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models
from calendar import monthrange
_logger = logging.getLogger(__name__)

class QaqcAssayPileReport(models.TransientModel):
    _name = 'qaqc.assay.pile.report'

    @api.model
    def _default_elements(self):
        chemical_elements = self.env['qaqc.chemical.element'].sudo().search([ ] )
        return chemical_elements.ids 

    element_ids = fields.Many2many('qaqc.chemical.element', 'qaqc_assay_pile_element_rel', 'qaqc_assay_pile_id', 'element_id', 'Element To Show', default=_default_elements )

    @api.multi
    def action_print(self):       
        assay_piles = self.env['qaqc.assay.pile'].search([ ( 'active', '=', True ), ( 'state', 'in', ['confirm', 'done' ] ) ])
        element_names = []
        for element_id in self.element_ids:
            element_names += [ element_id.name ]

        final_dict = {}
        loc_coa_dict = {}
        for assay_pile in assay_piles:
            row = {}
            row["date"] = assay_pile.date
            row["doc_name"] = assay_pile.name
            row["location_name"] = assay_pile.location_id.name
            row["lot_name"] = assay_pile.lot_id.name
            row["quantity"] = assay_pile.quantity
            row["state"] = assay_pile.state
            # set elem as column
            for element_id in self.element_ids:
                row[ element_id.name ] = 0
            for element_spec in assay_pile.element_specs:
                row[ element_spec.element_id.name ] = element_spec.spec

            # grouping
            if loc_coa_dict.get( assay_pile.location_id.name , False):
                loc_coa_dict[ assay_pile.location_id.name ] += [row]
            else :
                loc_coa_dict[ assay_pile.location_id.name ] = [row]

        final_dict = loc_coa_dict
        datas = {
            'ids': self.ids,
            'model': 'qaqc.assay.pile.report',
            'form': final_dict,
            'element_names': element_names,
        }
        return self.env['report'].get_action(self,'mining_qaqc.qaqc_assay_pile_temp', data=datas)
