# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    design_request_id = fields.Many2one('design_request.design_request')
