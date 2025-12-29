# controllers/website_form.py
import logging
from itertools import zip_longest
from odoo import http, _
from odoo.http import request
from odoo import Command
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

MODULE_KEY = "helpdesk_visits_report"


def _to_int(v):
    try:
        return int(v) if v not in (None, "", False) else False
    except Exception:
        return False


def _to_float(v):
    try:
        return float(v) if v not in (None, "", False) else False
    except Exception:
        return False


def _normalize_dt(v):
    """Convert HTML datetime-local (YYYY-MM-DDTHH:MM) -> 'YYYY-MM-DD HH:MM:SS'."""
    if not v:
        return False
    v = v.strip().replace("T", " ")
    if len(v) == 16:  # 'YYYY-MM-DD HH:MM'
        v = f"{v}:00"
    return v


def _getlist(form, key):
    """Support both 'field[]' and 'field' naming."""
    return form.getlist(key) or form.getlist(key.rstrip("[]")) or []


class HelpdeskWebsiteForm(http.Controller):

    @http.route(['/helpdesk/visit/report'], type='http', auth='public', website=True)
    def form_page(self, **kwargs):
        branches = request.env['helpdesk.branch'].sudo().search([])
        types = request.env['helpdesk.visit.type'].sudo().search([])
        methods = request.env['helpdesk.ticket.method'].sudo().search([])
        devices = request.env['helpdesk.device'].sudo().search([])
        return request.render(f"{MODULE_KEY}.template_helpdesk_visit_form", {
            "branches": branches,
            "types": types,
            "methods": methods,
            "devices": devices,
            "error": kwargs.get("error"),
        })

    @http.route(
        ['/helpdesk/visit/report/submit'],
        type='http', auth='public', website=True, csrf=True, methods=['POST']
    )
    def submit_form(self, **post):
        try:
            form = request.httprequest.form

            # Build O2M lines first (atomic create)
            device_ids = _getlist(form, 'device_id[]')
            device_statuses = _getlist(form, 'device_status[]')
            device_notes = _getlist(form, 'device_note[]')

            line_commands = []
            seq = 10
            for dev_raw, st_raw, note_raw in zip_longest(device_ids, device_statuses, device_notes, fillvalue=''):
                dev_id = _to_int(dev_raw)
                if not dev_id:
                    continue
                line_commands.append(Command.create({
                    "sequence": seq,
                    "device_id": dev_id,
                    "overall_status": (st_raw or "working"),
                    "notes": (note_raw or "").strip() or False,
                }))
                seq += 10

            vals = {
                # Header
                "name": (post.get("name") or "Help Desk Visit").strip(),

                # Branch Information
                "branch_id": _to_int(post.get("branch_id")),
                "branch_responsible": (post.get("branch_responsible") or "").strip() or False,

                # Visit Status
                "visit_type_id": _to_int(post.get("visit_type_id")),
                "visit_datetime": _normalize_dt(post.get("visit_datetime")),
                "is_urgent": post.get("is_urgent") or "no",

                # Ticket
                "request_method_id": _to_int(post.get("request_method_id")),

                # Details
                "details": (post.get("details") or "").strip() or False,

                # POS Device
                "pos_overall_status": post.get("pos_overall_status") or False,
                "pos_hdd_usage": _to_float(post.get("pos_hdd_usage")),
                "pos_cpu_usage": _to_float(post.get("pos_cpu_usage")),
                "pos_os_status": post.get("pos_os_status") or False,
                "pos_ram": (post.get("pos_ram") or "").strip() or False,

                # Backup
                "backup_status": (post.get("backup_status") or "").strip() or False,
                "backup_date": post.get("backup_date") or False,
                "backup_notes": (post.get("backup_notes") or "").strip() or False,

                # Other Devices (O2M)
                "device_line_ids": line_commands,
            }

            # Create everything atomically with sudo (public website)
            report = request.env["helpdesk.visit.report"].sudo().create(vals)

        except ValidationError as e:
            _logger.warning("Validation error during Helpdesk submit: %s", e)
            return self.form_page(error=str(e))
        except Exception:
            _logger.exception("Unexpected error during Helpdesk submit")
            return self.form_page(error="Could not submit the report. Please review the fields and try again.")

        return request.redirect(f"/helpdesk/visit/report/thanks?tn={report.ticket_number or ''}")
