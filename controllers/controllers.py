# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal as CustomerPortal
from odoo.http import request, route
import base64


class CustomerPortalHome(CustomerPortal):
    @http.route(['/my/designs'], type='http', auth="user", website=True)
    def lists(self, **kw):
        design_requests = request.env['design_request.design_request'].sudo().search([])
        values = {'design_requests': design_requests, 'page_name': 'design_lists', 'success':{}}
        return request.render("design_request.design_lists", values)

    @http.route(['/my/create-design'], type='http', auth="user", website=True)
    def create_design(self, **kw):
        values = {'page_name': 'create_design', 'errors': {"design_name": "", "customer_email": "", "design_image": ""}}
        return request.render("design_request.create_design_template", values)

    @http.route('/my/create-design/submit', type='http', auth="user", methods=['POST'], website=True, csrf=True)
    def submit_design(self, **kw):
        values = {'page_name': 'create_design'}
        errors = {"design_name": "", "customer_email": "", "design_image": ""}
        # Extract form data
        design_name = kw.get('design_name')
        customer_email = kw.get('customer_email')
        design_image = request.httprequest.files.get('design_image')
        if not design_name:
            errors["design_name"] = "Please enter design name"
        if not customer_email:
            errors["customer_email"] = "Please enter customer email"
        if not design_image:
            errors["design_image"] = "Please upload a design image"
        
        if errors['design_name']=="" and errors['customer_email']=="" and errors['design_image']=="":
            try:
                # Create a new design request records if there is no error
                request.env['design_request.design_request'].sudo().create({
                    'design_name': design_name,
                    'customer_email': customer_email,
                    'design_image': base64.b64encode(design_image.read()),
                })
                return request.redirect('/my/designs')
            except Exception as e:
                errors["design_image"] = "Error processing design image: %s" % e
            
        values = {'page_name': 'create_design', 'errors': errors}
        return request.render("design_request.create_design_template", values)

    @http.route('/my/designs/<model("design_request.design_request"):design>/', type='http', auth='user', website=True)
    def design_details(self, design, **kw):
        # Check if the design exists
        if not design.exists():
            return request.not_found()  # Return 404 if design does not exist

        values = {'page_name': 'design_details', 'design': design}
        # Pass the specific design request to the template
        return request.render('design_request.design_details_template', values)
