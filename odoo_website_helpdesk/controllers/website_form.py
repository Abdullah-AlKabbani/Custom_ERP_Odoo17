import base64
import json
from psycopg2 import IntegrityError
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.addons.website.controllers.form import WebsiteForm


class HelpdeskProduct(http.Controller):
    """ JSON endpoint to fetch products (unchanged). """
    @http.route('/product', auth='public', type='json')
    def product(self):
        prols = []
        acc = request.env['product.template'].sudo().search([])
        for i in acc:
            prols.append({'name': i['name'], 'id': i['id']})
        return prols


class WebsiteFormInherit(WebsiteForm):
    """
    Handle the public website form submission for helpdesk tickets without email.
    - No email lookup/requirement
    - Uses logged-in user's partner if available
    - Else creates a lightweight partner with name/phone/company only (no email)
    - Creates ticket with sudo and attaches uploaded files
    """

    def _handle_website_form(self, model_name, **kwargs):
        # Only special-case our ticket model; fallback to default handler for other models
        if model_name != 'ticket.helpdesk':
            model_record = request.env['ir.model'].sudo().search([('model', '=', model_name)])
            if not model_record:
                return json.dumps({'error': _("The form's specified model does not exist")})
            try:
                data = self.extract_data(model_record, request.params)
            except ValidationError as e:
                return json.dumps({'error_fields': e.args[0]})
            try:
                id_record = self.insert_record(request, model_record, data['record'], data['custom'], data.get('meta'))
                if id_record:
                    self.insert_attachment(model_record, id_record, data['attachments'])
                    if model_name == 'mail.mail':
                        request.env[model_name].sudo().browse(id_record).send()
            except IntegrityError:
                return json.dumps(False)
            request.session['form_builder_model_model'] = model_record.model
            request.session['form_builder_model'] = model_record.name
            request.session['form_builder_id'] = id_record
            return json.dumps({'id': id_record})

        # -------- ticket.helpdesk custom handling (NO EMAIL) --------
        # 1) Determine initial stage (lowest sequence)
        lowest_stage = None
        stages = request.env['ticket.stage'].sudo().search([])
        if stages:
            min_seq = min(stages.mapped('sequence') or [0])
            lowest = stages.filtered(lambda s: s.sequence == min_seq)
            if lowest:
                lowest_stage = lowest[0]
        if not lowest_stage:
            return json.dumps({'error': "No stage found with the lowest sequence."})

        # 2) Resolve/prepare partner (NO EMAIL REQUIRED)
        customer_name = (kwargs.get('customer_name') or '').strip()
        company = (kwargs.get('company') or '').strip()
        phone = (kwargs.get('phone') or '').strip()

        # If the visitor is an internal/portal *non-public* user, use their partner.
        # If it's the website public user, DO NOT use that partner (we'll create/find a real one).
        partner = False
        if request.env.user and not request.env.user._is_public() and request.env.user.partner_id:
            partner = request.env.user.sudo().partner_id

        if not partner:
            # Try to reuse an existing partner by phone (fallback by exact name+company)
            Partner = request.env['res.partner'].sudo()
            candidate = False
            if phone:
                candidate = Partner.search([('phone', '=', phone)], limit=1)
            if not candidate and customer_name and company:
                candidate = Partner.search([
                    ('name', '=', customer_name),
                    ('company_name', '=', company)
                ], limit=1)

            if candidate:
                partner = candidate
                # update missing fields if we have better data
                vals_to_update = {}
                if company and not partner.company_name:
                    vals_to_update['company_name'] = company
                if phone and not partner.phone:
                    vals_to_update['phone'] = phone
                if vals_to_update:
                    partner.write(vals_to_update)
            else:
                partner = Partner.create({
                    'name': customer_name or _('Website Visitor'),
                    'company_name': company or False,
                    'phone': phone or False,
                    # no email on purpose
                    'type': 'contact',
                })

            # Link the current website visitor to this partner (helps future requests)
            visitor = request.env['website.visitor']._get_visitor_from_request()
            if visitor and not visitor.partner_id:
                visitor.sudo().write({'partner_id': partner.id})

        # 3) Build ticket values (NO email fields)
        products = kwargs.get('product')
        ticket_vals = {
            'customer_name': customer_name,
            'subject': kwargs.get('subject'),
            'description': kwargs.get('description'),
            'phone': phone,
            'priority': kwargs.get('priority'),
            'stage_id': lowest_stage.id,
            'customer_id': partner.id,  # <<< important
            'ticket_type_id': kwargs.get('ticket_type_id'),
            'category_id': kwargs.get('category'),
        }

        # Optional product M2M/JSON field handling (kept if you still use it)
        if products:
            try:
                product_list = [int(i) for i in products.split(',')]
                ticket_vals['product_ids'] = product_list
            except Exception:
                # ignore malformed products input
                pass

        # 4) Create ticket with sudo
        ticket = request.env['ticket.helpdesk'].sudo().create(ticket_vals)

        # 5) DO NOT send any confirmation email (email removed by requirement)

        # 6) Save ticket info to session (for the thank-you page)
        request.session['ticket_number'] = ticket.name
        request.session['ticket_id'] = ticket.id

        # 7) Attach uploaded files (same keys as your form)
        attachments = []
        idx = 0
        while f"ticket_attachment[0][{idx}]" in kwargs:
            key = f"ticket_attachment[0][{idx}]"
            attachments.append(kwargs[key])
            idx += 1

        for attachment in attachments:
            try:
                content = attachment.read()
                request.env['ir.attachment'].sudo().create({
                    'name': attachment.filename,
                    'res_model': 'ticket.helpdesk',
                    'res_id': ticket.id,
                    'type': 'binary',
                    'datas': base64.encodebytes(content),
                })
            except Exception:
                # silently ignore any single bad file to not block the ticket creation
                continue

        # 8) Return webform JSON response
        model_record = request.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)
        request.session['form_builder_model_model'] = model_record.model if model_record else model_name
        request.session['form_builder_model'] = model_record.name if model_record else model_name
        request.session['form_builder_id'] = ticket.id
        return json.dumps({'id': ticket.id})
