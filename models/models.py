# -*- coding: utf-8 -*-

from odoo import models, fields, api


class design_request(models.Model):
    _name = 'design_request.design_request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    design_name = fields.Char(string='Design Name')
    customer_id = fields.Many2one('res.partner', string='Customer')
    customer_email = fields.Char(string='Customer Email')
    description = fields.Text(string='Description')
    design_image = fields.Image(string='Design Image', attachment=True)
    assigned_to = fields.Many2one('res.users', string='Assigned To')
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

            if not partner:
                # Handle the case where no partner is found
                partner = self.env['res.partner'].create({
                    'name': 'Default Customer',
                    'email': record.customer_email,
                })

            # Find a product for the sales order line
            product = self.env['product.product'].search([('name', '=', 'Default Product')], limit=1)
            if not product:
                # Optionally handle the case where no product is found
                product = self.env['product.product'].create({
                    'name': 'Default Product',
                    'list_price': 100.0,  # Replace with your actual price
                })

            # Create a sales quotation
            quotation = self.env['sale.order'].create({
                'partner_id': partner.id,
                'order_line': [(0, 0, {
                    'name': record.design_name,
                    'product_id': product.id,
                    'product_uom_qty': 1,  # Specify quantity
                    'product_uom': product.uom_id.id,  # Specify unit of measure
                    'price_unit': 100.0,  # Replace with your actual price or calculation
                })],
                'state': 'draft',
            })

            # Change the state of the design request
            record.state = 'ready_for_quotation'

            # Post a message to the sales quotation
            quotation.message_post(body="Sales Quotation has been successfully generated for the design request.",
                                   subtype_xmlid='mail.mt_note')

            # Optionally, open the created quotation form view
            return {
                'type': 'ir.actions.act_window',
                'name': 'Sales Quotation',
                'res_model': 'sale.order',
                'res_id': quotation.id,
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'current',
            }

