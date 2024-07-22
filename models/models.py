# -*- coding: utf-8 -*-

from odoo import models, fields, api


class design_request(models.Model):
    _name = 'design_request.design_request'
    _description = 'design_request.design_request'

    design_name = fields.Char(string='Design Name')
    customer_email = fields.Char(string='Customer Email')
    design_image = fields.Image(string='Design Image', attachment=True, max_width=100, max_height=100)

