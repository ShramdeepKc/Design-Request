# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal as CustomerPortal
from odoo.http import request, route
import base64

class CustomerPortalHome(CustomerPortal):
    @http.route(['/my/designs'], type='http', auth="user", website=True)
    def lists(self, **kw):
        design_requests = request.env['design_request.design_request'].sudo().search([])
        values = {'design_requests': design_requests, 'page_name': 'design_lists'}
        return request.render("design_request.design_lists", values)

    @http.route(['/my/create-design'], type='http', auth="user", website=True)
    def create_design(self, **kw):
        values = {'page_name': 'create_design'}
        return request.render("design_request.create_design_template", values)

    @http.route('/my/create-design/submit', type='http', auth="user", methods=['POST'], website=True, csrf=True)
    def submit_design(self, **kw):
        
        # Extract form data
        design_name = kw.get('design_name')
        customer_email = kw.get('customer_email')
        design_image = request.httprequest.files.get('design_image')
        # Check if design_name is provided to prevent empty submissions
        if design_name and design_image:
            # Handle file upload
            # design_image_data = design_image.read()
            
            # Create a new design request record
            request.env['design_request.design_request'].sudo().create({
                'design_name': design_name,
                'customer_email': customer_email,
                'design_image': base64.b64encode(design_image.read()),
            })
            
            # Optionally, you can add further processing or validation here
            
            # Redirect to a success page or return a response
            return request.redirect('/my/designs')
        else:
            print("design_name is not provided")
        # Handle case where design_name is not provided (if needed)
        # You can customize this behavior based on your requirements
        return request.redirect('/my/create-design')


