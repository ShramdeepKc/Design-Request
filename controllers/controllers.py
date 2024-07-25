# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal as CustomerPortal

from odoo.exceptions import UserError
from odoo.http import request
from PIL import UnidentifiedImageError
import base64
import logging

# Set up the logger
_logger = logging.getLogger(__name__)


class CustomerPortalHome(CustomerPortal):
    @http.route(['/my/designs'], type='http', auth="user", website=True)
    def lists(self, **kw):
        design_requests = request.env['design_request.design_request'].sudo().search([])

        state_mapping = {
            'draft': 'Draft',
            'in_progress': 'In Progress',
            'done': 'Done',
            'generate_quotation': 'Quotation Generated',
            'ready_for_quotation': 'Ready for Quotation',
            'send_for_client_review': 'Quotation Review',
            'cancelled': 'Cancelled',
            'sale': 'Sale Order Confirmed',
        }

        # Create a dictionary to map design IDs to their respective states
        design_states = {}

        for design in design_requests:
            sale_orders = request.env['sale.order'].sudo().search([
                ('design_request_id', '=', design.id)
            ])
            # Determine if any related sale orders are confirmed
            if sale_orders.filtered(lambda o: o.state == 'sale'):
                design_states[design.id] = 'sale'
            else:
                design_states[design.id] = design.state  # Keep original state if no sale orders are confirmed

        values = {
            'design_requests': design_requests,
            'page_name': 'design_lists',
            'state_mapping': state_mapping,
            'design_states': design_states
        }

        return request.render("design_request.design_lists", values)

    @http.route(['/my/create-design'], type='http', auth="user", website=True)
    def create_design(self, **kw):
        user = request.env.user
        values = {'page_name': 'create_design', 'customer_email': user.email or "", 'customer_id': user.id,
                  'errors': {"design_name": "", "customer_email": "", "design_image": ""}}
        return request.render("design_request.create_design_template", values)

    @http.route('/my/create-design/submit', type='http', auth="user", methods=['POST'], website=True, csrf=True)
    def submit_design(self, **kw):
        values = {'page_name': 'create_design'}
        errors = {"design_name": "", "customer_email": "", "design_image": ""}
        # Extract form data
        design_name = kw.get('design_name')
        customer_id = kw.get('customer_id')
        customer_email = kw.get('customer_email')
        description = kw.get('description')
        design_image = request.httprequest.files.get('design_image')
        if not design_name:
            errors["design_name"] = "Please enter design name"
        if not customer_email:
            errors["customer_email"] = "Please enter customer email"
        if not design_image:
            errors["design_image"] = "Please upload a design image"

        if errors['design_name'] == "" and errors['customer_email'] == "" and errors['design_image'] == "":
            try:
                allowed_extensions = ['jpg', 'jpeg', 'png', 'webp']
                file_extension = design_image.filename.split('.')[-1].lower()
                if file_extension not in allowed_extensions:
                    raise UnidentifiedImageError("Invalid image type")

                encoded_image = base64.b64encode(design_image.read())
                request.env['design_request.design_request'].sudo().create({
                    'design_name': design_name,
                    'customer_id': customer_id,
                    'customer_email': customer_email,
                    'description': description,
                    'design_image': encoded_image,
                })
                return request.redirect('/my/designs')
            except UnidentifiedImageError as e:
                errors["design_image"] = "Invalid image type"
            except Exception as e:
                errors["design_image"] = f"Error processing design image: {e}"

        values = {'page_name': 'create_design', 'errors': errors}
        return request.render("design_request.create_design_template", values)

    @http.route('/my/designs/<model("design_request.design_request"):design>/', type='http', auth='user',
                website=True)
    def design_details(self, design, **kw):
        # Check if the design exists
        if not design.exists():
            return request.not_found()  # Return 404 if design does not exist

        # Ensure the design state is 'send_for_client_review' before fetching related sale orders
        sale_orders = []
        if design.state == 'send_for_client_review':
            # Fetch the related sale orders for the design request
            sale_orders = request.env['sale.order'].sudo().search([
                ('design_request_id', '=', design.id),
                ('state', 'in', ['draft', 'sale'])  # Adjust the states as needed
            ])

            # Print or log the sale orders
            _logger.info("Sale Orders for Design Request ID %s: %s", design.id, sale_orders)
            print("Sale Orders for Design Request ID {}: {}".format(design.id, sale_orders))

        values = {'page_name': 'design_details', 'design': design, 'sale_orders': sale_orders}
        # Pass the specific design request to the template
        return request.render('design_request.design_details_template', values)

    @http.route('/my/designs/<int:design_id>/accept_quotation', type='http', auth='user', website=True,
                methods=['POST'])
    def accept_quotation(self, design_id, **kw):
        # Fetch the design request
        design = request.env['design_request.design_request'].sudo().browse(design_id)

        if not design.exists():
            return request.not_found()  # Return 404 if design does not exist

        # Ensure the design state is 'send_for_client_review' before processing
        if design.state != 'send_for_client_review':
            return request.redirect('/my/designs/%d/?message=invalid_state' % design.id)

        # Fetch the related sale orders
        sale_orders = request.env['sale.order'].sudo().search([
            ('design_request_id', '=', design.id)
        ])

        # Check if any sale order is already confirmed
        confirmed_orders = sale_orders.filtered(lambda order: order.state in ['sale', 'done'])

        if confirmed_orders:
            return request.redirect('/my/designs/%d/?message=already_confirmed' % design.id)

        # Confirm draft sale orders
        draft_orders = sale_orders.filtered(lambda order: order.state == 'draft')
        for order in draft_orders:
            order.action_confirm()  # Confirm the sale order, changing its state to 'sale'

        # Redirect back to the design details page with success message
        return request.redirect('/my/designs/%d/?message=confirmation_success' % design.id)
