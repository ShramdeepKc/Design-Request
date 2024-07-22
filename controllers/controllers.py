# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal as CustomerPortal
from odoo.http import request, route

class CustomerPortalHome(CustomerPortal):
    @route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        values = self._prepare_portal_layout_values()
        return request.render("design_request.design_home", values)

    @route(['/my/designs'], type='http', auth="user", website=True)
    def lists(self, **kw):
        values = self._prepare_portal_layout_values()
        return request.render("design_request.design_lists", values)

    @http.route(['/my/create-design'], type='http', auth="user", website=True)
    def create_design(self, **kw):
        return request.render("design_request.create_design_template", {})

    @http.route(['/my/create-design/submit'], type='http', auth="user", methods=['POST'], website=True, csrf=True)
    def submit_design(self, **kw):
        design_name = kw.get('design_name')
        if design_name:
            request.env['design_request.design_request'].sudo().create({
                'design_name': design_name,
            })
        return request.redirect('/my/designs')

