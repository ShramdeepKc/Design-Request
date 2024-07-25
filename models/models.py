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
        ('send_for_client_review', 'Client Review'),
        ('cancelled', 'Cancelled')
    ], default='draft', track_visibility='onchange')

    @api.model
    def create(self, vals):
        record = super(design_request, self).create(vals)
        if record.state == 'draft' and record.assigned_employees:
            record.state = 'in_progress'
        return record

    def write(self, vals):
        res = super(design_request, self).write(vals)
        if 'state' not in vals and self.state == 'draft' and self.assigned_employees:
            self.state = 'in_progress'
        return res

    def action_ready_for_quotation(self):
        for record in self:
            # Ensure the record is saved
            if not record.id:
                raise UserError("Record must be saved before changing its state.")

            # Ensure the record is in 'In Progress'
            if record.state != 'in_progress':
                raise UserError("Cannot move to 'Ready for Quotation' unless the record is 'In Progress' or state is "
                                "changed to in_progress.")

            # Ensure the record is not in restricted states
            if record.state in ['generate_quotation', 'send_for_client_review']:
                raise UserError(
                    "Cannot move to 'Ready for Quotation' from 'Generate Quotation' or 'Send for Client Review'.")

            # Manually update the state
            record.state = 'ready_for_quotation'

            # Optionally, you can use the write method if you want to ensure the state change is committed
            # record.write({'state': 'ready_for_quotation'})

    def action_generate_quotation(self):
        for record in self:
            if record.state != 'ready_for_quotation':
                raise UserError("You cannot generate a quotation until the state is 'Ready for Quotation or once the "
                                "quotation is generated'.")

            partner = self.env['res.partner'].search([('email', '=', record.customer_email)], limit=1)
            if not partner:
                partner = self.env['res.partner'].create({
                    'name': 'Default Customer',
                    'email': record.customer_email,
                })

            product = self.env['product.product'].search([('name', '=', record.design_name)], limit=1)
            if not product:
                product = self.env['product.product'].create({
                    'name': record.design_name,
                    'list_price': record.price_unit,
                })

            quotation = self.env['sale.order'].create({
                'partner_id': partner.id,
                'design_request_id': record.id,
                'order_line': [(0, 0, {
                    'name': record.design_name,
                    'product_id': product.id,
                    'product_uom_qty': 1,
                    'product_uom': product.uom_id.id,
                    'price_unit': record.price_unit,
                })],
                'state': 'draft',
            })

            record.state = 'generate_quotation'
            quotation.message_post(body="Sales Quotation has been successfully generated for the design request.",
                                   subtype_xmlid='mail.mt_note')

            return {
                'type': 'ir.actions.act_window',
                'name': 'Sales Quotation',
                'res_model': 'sale.order',
                'res_id': quotation.id,
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'current',
            }

    def action_send_for_client_review(self):
        for record in self:
            if record.state != 'generate_quotation':
                raise UserError("Cannot send for client review until a quotation is generated.")
            record.state = 'send_for_client_review'

    def action_cancel(self):
        for record in self:
            if record.state in ['generate_quotation', 'send_for_client_review']:
                raise UserError("Cannot move to 'Cancelled' once a quotation is generated or sent for client review.")
            record.state = 'cancelled'

    def action_send_mail(self):
        template = self.env.ref('design_request.design_request_in_progress_email_template')
        if not template:
            _logger.error("Email template not found")
            return

        for record in self:
            if record.customer_email:
                try:
                    template.send_mail(record.id, force_send=True)
                    _logger.info("Email successfully sent to %s", record.customer_email)
                except Exception as e:
                    _logger.error("Failed to send email to %s: %s", record.customer_email, str(e))
            else:
                _logger.warning("No customer email provided for record %s", record.id)
