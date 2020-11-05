# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2017-Today Sitaram
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

import logging
from odoo import api, fields, models
import datetime

_logger = logging.getLogger(__name__)


class ReportMining_qaqc_qaqc_assay_pile_Temp(models.AbstractModel):
    _name = 'report.mining_qaqc.qaqc_assay_pile_temp'

    @api.model
    def render_html(self, docids, data=None):
        docargs =  {
            'doc_ids': data.get('ids'),
            'doc_model': data.get('model'),
            'data': data['form'],
            'element_names': data['element_names'],
            'date': datetime.datetime.now().strftime("%d/%m/%Y"),

        }
        # print "===================docargs",docargs
        # _logger.warning( docargs )
        return self.env['report'].render('mining_qaqc.qaqc_assay_pile_temp', docargs)
