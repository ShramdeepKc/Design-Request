# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class design_request(models.Model):
#     _name = 'design_request.design_request'
#     _description = 'design_request.design_request'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

