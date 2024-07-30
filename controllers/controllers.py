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
    @http.route(["/my/designs"], type="http", auth="user", website=True)
    def lists(self, **kw):
        design_requests = (
            request.env["design_request.design_request"]
            .sudo()
            .search([("customer_id", "=", request.env.user.id)])
        )

        state_mapping = {
            "draft": "Pending",
            "in_progress": "In Progress",
            "ready_for_quotation": "In Progress",
            "generate_quotation": "In Progress",
            "send_for_client_review": "Quotation Review",
            "cancelled": "Cancelled",
            "completed": "Completed",
            "sale": "Sale Order Confirmed",
        }

        # Create a dictionary to map design IDs to their respective states
        design_states = {}

        for design in design_requests:
            sale_orders = (
                request.env["sale.order"]
                .sudo()
                .search([("design_request_id", "=", design.id)])
            )
            # Determine if any related sale orders are confirmed
            if sale_orders.filtered(lambda o: o.state == "sale"):
                design_states[design.id] = "sale"
            else:
                design_states[design.id] = (
                    design.state
                )  # Keep original state if no sale orders are confirmed

        values = {
            "design_requests": design_requests,
            "page_name": "design_lists",
            "state_mapping": state_mapping,
            "design_states": design_states,
        }

        return request.render("design_request.design_lists", values)

    @http.route(["/my/create-design"], type="http", auth="user", website=True)
    def create_design(self, **kw):
        user = request.env.user
        values = {
            "page_name": "create_design",
            "customer_email": "",
            "customer_id": user.id,
            "errors": {"design_name": "", "customer_email": "", "design_image": ""},
        }
        return request.render("design_request.create_design_template", values)

    @http.route(
        "/my/create-design/submit",
        type="http",
        auth="user",
        methods=["POST"],
        website=True,
        csrf=True,
    )
    def submit_design(self, **kw):
        values = {"page_name": "create_design"}
        errors = {"design_name": "", "customer_email": "", "design_image": ""}
        # Extract form data
        design_name = kw.get("design_name")
        customer_id = kw.get("customer_id")
        customer_email = kw.get("customer_email")
        description = kw.get("description")
        design_image = request.httprequest.files.getlist("design_image")

        if not design_name:
            errors["design_name"] = "Please enter design name"
        if not customer_email:
            errors["customer_email"] = "Please enter customer email"
        if not design_image:
            errors["design_image"] = "Please upload at least one design image"

        if (
            errors["design_name"] == ""
            and errors["customer_email"] == ""
            and errors["design_image"] == ""
        ):
            try:
                allowed_extensions = ["jpg", "jpeg", "png", "webp"]
                image_ids = []
                for image in design_image:
                    file_extension = image.filename.split(".")[-1].lower()
                    if file_extension not in allowed_extensions:
                        raise UnidentifiedImageError("Invalid image type")
                    encoded_image = base64.b64encode(image.read())
                    attachment = request.env["ir.attachment"].sudo().create(
                        {
                            "name": image.filename,
                            "datas": encoded_image,
                            "res_model": "design_request.design_request",
                            "res_id": 0,
                            "mimetype": image.content_type,
                        }
                    )
                    image_ids.append(attachment.id)

                request.env["design_request.design_request"].sudo().create(
                    {
                        "design_name": design_name,
                        "customer_id": customer_id,
                        "customer_email": customer_email,
                        "client_email": request.env.user.email,
                        "description": description,
                        "design_image": [(6, 0, image_ids)],
                    }
                )

                # TODO: Send emails asynchronously
                design_team = (
                    request.env["hr.employee"]
                    .sudo()
                    .search([("department_id.name", "=", "Designing Team")])
                )

                # Post a message to each member of the design team
                subject = "New Design Request Notification"
                body = f"Dear {{}},<br/><br/>We have received a new design request: <b>{design_name}</b>.<br/><br/>Best regards,<br/>Nova Design Team"
                for member in design_team:
                    email_values = {
                        "subject": subject,
                        "body_html": body.format(member.name),
                        "email_to": member.work_email,  # Assuming each member has a work_email field
                    }
                    mail = request.env["mail.mail"].sudo().create(email_values)
                    # Send the email
                    mail.send()

                return request.redirect("/my/designs")
            except UnidentifiedImageError as e:
                errors["design_image"] = "Invalid image type"
            except Exception as e:
                errors["design_image"] = f"Error : {e}"

        values = {"page_name": "create_design", "errors": errors}
        return request.render("design_request.create_design_template", values)

    @http.route(
        '/my/designs/<model("design_request.design_request"):design>/',
        type="http",
        auth="user",
        website=True,
    )
    def design_details(self, design, **kw):
        # Check if the design exists
        if not design.exists():
            return request.not_found()  # Return 404 if design does not exist

        # Decode the images
        images = []
        for attachment in design.design_image:
            try:
                image_data = attachment.datas
                images.append({'id': attachment.id, 'data': image_data})
            except Exception as e:
                _logger.error(f"Error reading image {attachment.id}: {e}")
        print(f"Images: {images}")
        print(f"Images: {design.design_image}")
        values = {
            "page_name": "design_details",
            "design": design,
            "images": images,
        }
        # Pass the specific design request to the template
        return request.render("design_request.design_details_template", values)

    @http.route(
        "/my/designs/<int:design_id>/send-to-customer",
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def send_to_client(self, design_id, **kw):
        design = request.env["design_request.design_request"].sudo().browse(design_id)
        if not design.exists():
            return request.not_found()  # Return 404 if design does not exist

        if design.state != "send_for_client_review":
            return request.redirect("/my/designs/%d/?message=invalid_state" % design.id)

        try:
            # Prepare the email content
            subject = "New Design Request Notification"
            body = (
                f"Dear Customer,<br/><br/>Here is a review for the design (<b>{design.design_name}</b>) you have submitted. "
                f"You can send your response at {design.customer_email}.<br/><br/>"
                f"Best regards,<br/>Nova Design Team"
            )

            # Create the email
            email_values = {
                "subject": subject,
                "body_html": body,
                "email_to": design.customer_email,
                "attachment_ids": [],
            }

            # Attach the image if it exists
            completed_image_base64 = design.completed_design
            if completed_image_base64:
                try:
                    # Decode the base64 image to check if it's valid
                    image_data = base64.b64decode(completed_image_base64)
                    attachment_values = {
                        "name": "completed_design.png",
                        "type": "binary",
                        "datas": base64.b64encode(image_data),
                        "mimetype": "image/png",
                    }
                    attachment = request.env["ir.attachment"].create(attachment_values)
                    email_values["attachment_ids"] = [(6, 0, [attachment.id])]
                except Exception as e:
                    _logger.error(f"Error decoding or attaching image: {e}")

            # Send the email
            mail = request.env["mail.mail"].sudo().create(email_values)
            mail.send()
            return request.redirect("/my/designs/%d/?message=email_sent" % design.id)
        except Exception as e:
            _logger.error(f"Error sending email: {e}")
            return request.redirect("/my/designs/%d/?message=email_error" % design.id)

    @http.route(
        "/my/designs/<int:design_id>/accept_quotation",
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def accept_quotation(self, design_id, **kw):
        # Fetch the design request
        design = request.env["design_request.design_request"].sudo().browse(design_id)

        if not design.exists():
            return request.not_found()  # Return 404 if design does not exist

        # Ensure the design state is 'send_for_client_review' before processing
        if design.state != "send_for_client_review":
            return request.redirect("/my/designs/%d/?message=invalid_state" % design.id)

        # Fetch the related sale orders
        sale_orders = (
            request.env["sale.order"]
            .sudo()
            .search([("design_request_id", "=", design.id)])
        )

        # Check if any sale order is already confirmed
        confirmed_orders = sale_orders.filtered(
            lambda order: order.state in ["sale", "done"]
        )

        if confirmed_orders:
            return request.redirect(
                "/my/designs/%d/quotations?message=already_confirmed" % design.id
            )

        # Confirm draft sale orders
        draft_orders = sale_orders.filtered(lambda order: order.state == "draft")
        for order in draft_orders:
            order.action_confirm()  # Confirm the sale order, changing its state to 'sale'

        # Set the design state to 'completed'
        design.state = "completed"

        # Redirect back to the design quotations page with success message
        return request.redirect(
            "/my/designs/%d/quotations?message=confirmation_success" % design.id
        )


    @http.route(
        '/my/designs/<model("design_request.design_request"):design>/quotations',
        type="http",
        auth="user",
        website=True,
    )
    def view_quotations(self, design, **kw):
        if not design.exists():
            return request.not_found()  # Return 404 if design does not exist

        # Ensure the design state is 'send_for_client_review' before fetching related sale orders
        sale_orders = []
        if design.state == "send_for_client_review" or design.state == "completed":
            # Fetch the related sale orders for the design request
            sale_orders = (
                request.env["sale.order"]
                .sudo()
                .search(
                    [
                        ("design_request_id", "=", design.id),
                        (
                            "state",
                            "in",
                            ["draft", "sale"],
                        ),  # Adjust the states as needed
                    ]
                )
            )

            # Print or log the sale orders
            _logger.info(
                "Sale Orders for Design Request ID %s: %s", design.id, sale_orders
            )
            print(
                "Sale Orders for Design Request ID {}: {}".format(
                    design.id, sale_orders
                )
            )

        values = {
            "page_name": "design_details",
            "design": design,
            "sale_orders": sale_orders,
        }
        return request.render("design_request.view_quotations_template", values)

    @http.route(
        "/my/designs/<int:design_id>/reject_quotation",
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def reject_quotation(self, design_id, **kw):
        # Fetch the design request
        design = request.env["design_request.design_request"].sudo().browse(design_id)

        if not design.exists():
            return request.not_found()  # Return 404 if design does not exist

        # Ensure the design state is 'send_for_client_review' before processing
        if design.state != "send_for_client_review":
            return request.redirect("/my/designs/%d/?message=invalid_state" % design.id)

        # Update the state to 'in_progress'
        design.write({'state': 'in_progress'})

        # Redirect back to the design quotations page with success message
        return request.redirect("/my/designs/%d/quotations?message=rejection_success" % design.id)
