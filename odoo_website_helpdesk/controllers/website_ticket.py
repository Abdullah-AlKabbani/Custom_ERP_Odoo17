from odoo import http
from odoo.http import request


class WebsiteDesk(http.Controller):
    @http.route(['/helpdesk_ticket'], type='http', auth="public", website=True, sitemap=True)
    def helpdesk_ticket(self, **kwargs):
        """
        Display the helpdesk ticket creation form (public).
        No email required/used on the form.
        """
        types = request.env['helpdesk.type'].sudo().search([])
        categories = request.env['helpdesk.category'].sudo().search([])
        product = request.env['product.template'].sudo().search([])  # kept if you reuse it later

        values = {
            'types': types,
            'categories': categories,
            'product_website': product,
        }
        return request.render('odoo_website_helpdesk.ticket_form', values)

    @http.route(['/rating/<int:ticket_id>'], type='http', auth="public", website=True, sitemap=True)
    def rating(self, ticket_id):
        """
        Show rating form for a specific ticket (public route is fine if your rating page is public).
        """
        ticket = request.env['ticket.helpdesk'].sudo().browse(ticket_id)
        data = {
            'ticket': ticket.id,
        }
        return request.render('odoo_website_helpdesk.rating_form', data)

    @http.route(['/rating/<int:ticket_id>/submit'], type='http', auth="user", website=True, csrf=False, sitemap=True)
    def rating_backend(self, ticket_id, **post):
        """
        Persist rating; requires authenticated user.
        """
        ticket = request.env['ticket.helpdesk'].sudo().browse(ticket_id)
        ticket.write({
            'customer_rating': post.get('rating'),
            'review': post.get('message'),
        })
        return request.render('odoo_website_helpdesk.rating_thanks')
