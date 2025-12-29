# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class IsoWebsite(http.Controller):

    @http.route(['/iso/form'], type='http', auth='public', website=True, sitemap=True)
    def iso_form(self, **kw):
        icp = request.env['ir.config_parameter'].sudo()
        default_shift_id = icp.get_param('iso_tickets.default_shift_id')
        default_shift = False
        if default_shift_id:
            try:
                default_shift = request.env['iso.shift'].sudo().browse(int(default_shift_id))
            except Exception:
                default_shift = False

        Section = request.env['iso.section'].sudo()
        Branch = request.env['iso.branch'].sudo()
        Shift = request.env['iso.shift'].sudo()
        Statement = request.env['iso.statement'].sudo()

        sections = Section.search([])
        branches = Branch.search([])
        shifts = Shift.search([])

        # Build payload: each section + its active statements
        sections_payload = []
        active_statements = Statement.search([('active', '=', True)])
        # index by section for fast grouping
        stmt_by_sec = {}
        for s in active_statements:
            stmt_by_sec.setdefault(s.section_id.id, []).append(s)

        for sec in sections:
            sections_payload.append({
                'section': sec,
                'statements': stmt_by_sec.get(sec.id, []),
            })

        values = {
            'sections_payload': sections_payload,
            'branches': branches,
            'shifts': shifts,
            'default_shift': default_shift,
            'default_shift_id': int(default_shift_id) if default_shift_id else False,
        }
        return request.render('iso_tickets.iso_public_form', values)

    @http.route(['/iso/submit'], type='http', auth='public', website=True, csrf=False)
    def iso_submit(self, **post):
        # Common fields for all tickets
        branch_id = int(post.get('branch_id', 0)) or False
        shift_id = int(post.get('shift_id', 0)) or False
        date_str = post.get('date')
        manager_name = post.get('manager_name') or False
        notes = post.get('notes') or False

        if not (branch_id and date_str):
            return request.redirect('/iso/form?error=missing')

        # 1) Collect statement selections
        #    Keys are like: statement_selection_<ID>
        selection_by_stmt = {}  # stmt_id -> {'selection': 'exist'|'not_exist', 'qty': float, 'note': str}
        stmt_ids = []
        for key, val in post.items():
            if key.startswith('statement_selection_'):
                try:
                    stmt_id = int(key.replace('statement_selection_', ''))
                except Exception:
                    continue
                selection = val
                qty = post.get(f'statement_qty_{stmt_id}', '0') or '0'
                note = post.get(f'statement_note_{stmt_id}', '') or ''

                # safe qty parse
                try:
                    qty_val = float(qty)
                except Exception:
                    qty_val = 0.0

                selection_by_stmt[stmt_id] = {
                    'selection': selection,
                    'qty': qty_val,
                    'note': note,
                }
                stmt_ids.append(stmt_id)

        if not stmt_ids:
            # Nothing selected; bounce back gracefully
            return request.redirect('/iso/form?error=nostatements')

        # 2) Group selected statements by their section
        Statement = request.env['iso.statement'].sudo()
        stmt_records = Statement.browse(stmt_ids).exists()
        # map statement_id -> section_id
        sec_by_stmt = {s.id: s.section_id.id for s in stmt_records}

        grouped = {}  # section_id -> list of (stmt_id, payload)
        for sid, payload in selection_by_stmt.items():
            sec_id = sec_by_stmt.get(sid)
            if not sec_id:
                continue
            grouped.setdefault(sec_id, []).append((sid, payload))

        # 3) Create one ticket per section, and its lines
        Ticket = request.env['iso.ticket'].sudo()
        Line = request.env['iso.ticket.line'].sudo()

        for sec_id, lines in grouped.items():
            # Create the ticket WITH the required section_id
            ticket = Ticket.create({
                'section_id': sec_id,
                'branch_id': branch_id,
                'shift_id': shift_id or False,
                'date': date_str,
                'public_manager_name': manager_name,
                'public_notes': notes,
            })

            # Create its lines
            for stmt_id, payload in lines:
                try:
                    Line.create({
                        'ticket_id': ticket.id,
                        'statement_id': stmt_id,
                        'selection': payload['selection'],
                        'quantity': payload['qty'],
                        'notes': payload['note'],
                        'manager_name': manager_name,
                    })
                except Exception as e:
                    request.env['ir.logging'].sudo().create({
                        'name': 'ISO Ticket Line Error',
                        'type': 'server',
                        'dbname': request.env.cr.dbname,
                        'level': 'error',
                        'message': str(e),
                        'path': 'iso.submit',
                        'func': 'iso_submit',
                        'line': 0,
                    })

        return request.redirect('/iso/thanks')

    @http.route(['/iso/thanks'], type='http', auth='public', website=True)
    def iso_thanks(self, **kw):
        return request.render('iso_tickets.iso_public_thanks', {})
