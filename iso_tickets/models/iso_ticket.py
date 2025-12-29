from odoo import models, fields, api, _
from odoo.exceptions import AccessError

class IsoSection(models.Model):
    _name = "iso.section"
    _description = "ISO Section (fixed)"

    name = fields.Char(required=True)
    code = fields.Selection([
        ("supply", "Supply"),
        ("quality", "Quality"),
        ("maintenance", "Maintenance"),
        ("sales", "Sales"),
        ("tech", "Tech"),
        ("hr", "HR"),
        ("finance", "Finance"),
    ], required=True)

    _sql_constraints = [
        ("iso_section_code_uniq", "unique(code)", "Section code must be unique."),
    ]

class IsoBranch(models.Model):
    _name = "iso.branch"
    _description = "ISO Branch"

    name = fields.Char(required=True)
    location = fields.Char()
    manager_name = fields.Char(help="Default manager name shown on the public form (optional).")

class IsoTicket(models.Model):
    _name = "iso.ticket"
    _description = "ISO Ticket (per section submission)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(default="/", copy=False, readonly=True)
    section_id = fields.Many2one("iso.section", required=True, index=True)
    branch_id = fields.Many2one("iso.branch", required=True)
    shift_id = fields.Many2one("iso.shift", string="Shift")
    public_manager_name = fields.Char(string="Branch Manager (entered on form)")
    date = fields.Date(required=True)
    status = fields.Selection([("pending", "Pending"), ("done", "Done")], default="pending", tracking=True, required=True)
    public_notes = fields.Text(string="Overall Notes")
    line_ids = fields.One2many("iso.ticket.line", "ticket_id", string="Lines")

    @api.model
    def create(self, vals):
        if vals.get("name", "/") == "/":
            vals["name"] = self.env["ir.sequence"].next_by_code("iso.ticket") or "/"
        return super().create(vals)

    def _check_section_access(self):
        user = self.env.user
        if user.has_group("iso_tickets.group_iso_manager"):
            return
        code2group = {
            "supply": "iso_tickets.group_iso_supply",
            "quality": "iso_tickets.group_iso_quality",
            "maintenance": "iso_tickets.group_iso_maintenance",
            "sales": "iso_tickets.group_iso_sales",
            "tech": "iso_tickets.group_iso_tech",
            "hr": "iso_tickets.group_iso_hr",
            "finance": "iso_tickets.group_iso_finance",
        }
        for rec in self:
            code = rec.section_id.code
            gid = code2group.get(code)
            if not gid or not user.has_group(gid):
                raise AccessError(_("You don't have access to this section's tickets."))

    def write(self, vals):
        self._check_section_access()
        return super().write(vals)

    def unlink(self):
        self._check_section_access()
        return super().unlink()

    def action_set_pending(self):
        self._check_section_access()
        for rec in self:
            rec.status = "pending"
            try:
                rec.message_post(body=_("Status set to Pending"))
            except Exception:
                pass
        return True

    def action_set_done(self):
        self._check_section_access()
        for rec in self:
            rec.status = "done"
            try:
                rec.message_post(body=_("Status set to Done"))
            except Exception:
                pass
        return True

class IsoTicketLine(models.Model):
    _name = "iso.ticket.line"
    _description = "ISO Ticket Line"

    ticket_id = fields.Many2one("iso.ticket", required=True, ondelete="cascade")
    statement_id = fields.Many2one("iso.statement", required=True)
    section_id = fields.Many2one(related="statement_id.section_id", store=True)
    selection = fields.Selection([("exist", "Exist"), ("not_exist", "Not Exist")], required=True)
    quantity = fields.Float(digits=(16,2))
    notes = fields.Text()
    manager_name = fields.Char()
