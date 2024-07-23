# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal as CustomerPortal
from odoo.http import request
from PIL import UnidentifiedImageError
import base64


class CustomerPortalHome(CustomerPortal):
    @http.route(['/my/designs'], type='http', auth="user", website=True)
    def lists(self, **kw):
        design_requests = request.env['design_request.design_request'].sudo().search([])

        state_mapping = {
            'draft': 'Draft',
            'in_progress': 'In Progress',
            'done': 'Done',
            'ready_for_quotation': 'Ready for Quotation'
        }
            
        values = {'design_requests': design_requests, 'page_name': 'design_lists', 'state_mapping': state_mapping}
        return request.render("design_request.design_lists", values)

    @http.route(['/my/create-design'], type='http', auth="user", website=True)
    def create_design(self, **kw):
        user = request.env.user
        values = {'page_name': 'create_design', 'customer_email': user.email or "", 'customer_id': user.id, 'errors': {"design_name": "", "customer_email": "", "design_image": ""}}
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
        
        if errors['design_name']=="" and errors['customer_email']=="" and errors['design_image']=="":
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

    @http.route('/my/designs/<model("design_request.design_request"):design>/', type='http', auth='user', website=True)
    def design_details(self, design, **kw):
        # Check if the design exists
        if not design.exists():
            return request.not_found()  # Return 404 if design does not exist

        values = {'page_name': 'design_details', 'design': design}
        # Pass the specific design request to the template
        return request.render('design_request.design_details_template', values)
