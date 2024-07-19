# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request, route

class CustomerPortalHome(CustomerPortal):

    @route(['/my/designs'], type='http', auth="user", website=True)
    def lists(self, **kw):
        values = {'values': self._prepare_portal_layout_values(), 'page_name': 'design_lists'}
        return request.render("design_request.design_lists", values)


