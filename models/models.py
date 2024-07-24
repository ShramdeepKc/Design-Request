# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class design_request(models.Model):
    _name = 'design_request.design_request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    design_name = fields.Char(string='Design Name')
    customer_id = fields.Many2one('res.partner', string='Customer')
    customer_email = fields.Char(string='Customer Email')
    description = fields.Text(string='Description')
    design_image = fields.Image(string='Design Image', attachment=True)
    price_unit = fields.Float(string='Price')
    assigned_employees = fields.Many2one('hr.employee', string='Assigned Employees',
                                         domain="[('department_id.name', '=', 'Designing Team')]")
    video_file = fields.Binary(string='Video File')
    video_filename = fields.Char(string='Video Filename')
    completed_design = fields.Image(string='Completed Design', attachment=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('ready_for_quotation', 'Ready for Quotation'),
        ('generate_quotation', 'Generate Quotation'),
        ('cancelled', 'Cancelled')
    ], default='draft', track_visibility='onchange')

    @api.model
    def create(self, vals):
        # Create the record
        record = super(design_request, self).create(vals)

        # Change state to 'in_progress' if initially 'draft'
        if record.state == 'draft' and record.assigned_employees:
            record.write({'state': 'in_progress'})

        return record

    def write(self, vals):
        res = super(design_request, self).write(vals)

        # Change state to 'in_progress' if currently 'draft' and assigned_employee is set
        if self.state == 'draft' and self.assigned_employees:
            self.write({'state': 'in_progress'})

        return res

    # def action_start(self):
    #     for record in self:
    #         if record.state in ['done', 'ready_for_quotation']:
    #             raise UserError("Cannot move to 'In Progress' from 'Done' or 'Ready for Quotation'.")
    #         record.write({'state': 'in_progress'})

    def action_ready_for_quotation(self):
        for record in self:
            if record.state == 'generate_quotation':
                raise UserError("Cannot move to 'in_progress' once it is 'Ready for Quotation'.")
            record.write({'state': 'ready_for_quotation'})

    def action_generate_quotation(self):
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
            product = self.env['product.product'].search([('name', '=', record.design_name)], limit=1)
            if not product:
                # Optionally handle the case where no product is found
                product = self.env['product.product'].create({
                    'name': record.design_name,
                    'list_price': record.price_unit,  # Use the correct price unit
                })

            # Create a sales quotation
            quotation = self.env['sale.order'].create({
                'partner_id': partner.id,
                'design_request_id': record.id,

                'order_line': [(0, 0, {
                    'name': record.design_name,
                    'product_id': product.id,  # Use the product's ID
                    'product_uom_qty': 1,  # Specify quantity
                    'product_uom': product.uom_id.id,  # Specify unit of measure
                    'price_unit': record.price_unit,  # Correctly use price_unit
                })],
                'state': 'draft',
            })

            # Change the state of the design request
            record.state = 'generate_quotation'

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

    def action_cancel(self):
        for record in self:
            if record.state in ['generate_quotation']:
                raise UserError("Cannot move to 'Cancelled' once quotation is generated.")
            record.write({'state': 'cancelled'})

    def action_send_mail(self):
        template = self.env.ref('design_request.design_request_in_progress_email_template')
        if not template:
            _logger.error("Email template not found")
            return

        for record in self:
            if record.customer_email:
                try:
                    # Ensure the email template is sent to the correct record
                    template.send_mail(record.id, force_send=True)
                    _logger.info(f"Email successfully sent to {record.customer_email}")
                except Exception as e:
                    _logger.error(f"Failed to send email to {record.customer_email}: {str(e)}")
            else:
                _logger.warning(f"No customer email provided for record {record.id}")
