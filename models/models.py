# -*- coding: utf-8 -*-

from odoo import models, fields, api


class design_request(models.Model):
    _name = 'design_request.design_request'
    _description = 'design_request.design_request'

    design_name = fields.Char()


