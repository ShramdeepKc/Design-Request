# -*- coding: utf-8 -*-

from odoo import models, fields, api


class design_request(models.Model):
    _name = 'design_request.design_request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    design_name = fields.Char(string='Design Name')
    customer_email = fields.Char(string='Customer Email')
    design_image = fields.Image(string='Design Image', attachment=True, max_width=100, max_height=100)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('ready_for_quotation', 'Ready for Quotation')
    ], default='draft', track_visibility='onchange')

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_ready_for_quotation(self):
        for record in self:
            # Find the customer by email
            partner = self.env['res.partner'].search([('email', '=', record.customer_email)], limit=1)

