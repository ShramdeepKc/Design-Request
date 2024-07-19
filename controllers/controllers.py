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

