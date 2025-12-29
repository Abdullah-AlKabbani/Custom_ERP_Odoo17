# models/visit_report.py
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

POS_STATUS = [("working", "Working"), ("not_working", "Not Working")]
OS_STATUS = [("activated", "Activated"), ("not_activated", "Not Activated")]
REPORT_STATE = [("draft", "Draft"), ("authorized", "Authorized")]


class HelpdeskVisitReport(models.Model):
    _name = "helpdesk.visit.report"
    _description = "Help Desk Visit Report"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    # Header
    name = fields.Char(required=True, tracking=True, default="Help Desk Visit")
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    # Branch Information
    branch_id = fields.Many2one("helpdesk.branch", string="Branch", required=True, tracking=True)
    branch_responsible = fields.Char(string="Responsible Person", tracking=True)

    # Visit Status
    visit_type_id = fields.Many2one("helpdesk.visit.type", string="Visit Type", required=True, tracking=True)
    visit_datetime = fields.Datetime(string="Visit Date & Time", required=True, tracking=True)
    is_urgent = fields.Selection([("yes", "Yes"), ("no", "No")], default="no", required=True, tracking=True)

    # Ticket
    ticket_number = fields.Char(
        string="Ticket Number",
        readonly=True,
        copy=False,
        index=True,
        default="New",  # clearer than '/'
        help="Auto-generated like 01VN, 02VN…",
        tracking=True,
    )
    request_method_id = fields.Many2one("helpdesk.ticket.method", string="Method of Request", required=True, tracking=True)

    # Details
    details = fields.Text(string="Detailed Work & Notes")

    # POS
    pos_overall_status = fields.Selection(POS_STATUS, string="POS Overall Status", tracking=True)
    pos_hdd_usage = fields.Float(string="POS HDD Usage (%)")
    pos_cpu_usage = fields.Float(string="POS CPU Usage (%)")
    pos_os_status = fields.Selection(OS_STATUS, string="POS OS Status")
    pos_ram = fields.Char(string="POS RAM")

    # Other Devices (ordered)
    device_line_ids = fields.One2many(
        "helpdesk.visit.device.line", "report_id",
        string="Other Devices",
        order="sequence,id",
    )

    # Backup
    backup_status = fields.Char(string="Status of Last Backup")
    backup_date = fields.Date(string="Backup Date")
    backup_notes = fields.Text(string="Backup Notes")

    # State
    state = fields.Selection(REPORT_STATE, default="draft", tracking=True)

    @api.constrains("pos_hdd_usage", "pos_cpu_usage")
    def _check_percentages(self):
        for rec in self:
            for val in (rec.pos_hdd_usage, rec.pos_cpu_usage):
                if val and (val < 0 or val > 100):
                    raise ValidationError(_("Percentages must be between 0 and 100."))

    def action_authorize(self):
        self.write({"state": "authorized"})

    def action_set_draft(self):
        self.write({"state": "draft"})

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records.sudo():
            if not rec.ticket_number or rec.ticket_number in ("/", "New"):
                seq = self.env["ir.sequence"].next_by_code("helpdesk.visit.report.ticket")
                if not seq:
                    # Fallback to keep it monotonic even if the sequence record is missing
                    last = self.search([], order="create_date desc", limit=1)
                    try:
                        cur = int((last.ticket_number or "0").rstrip("VN")) if (last and last.ticket_number and last.ticket_number.endswith("VN")) else 0
                    except Exception:
                        cur = 0
                    seq = str(cur + 1)
                rec.ticket_number = f"{int(seq):02d}VN"
            rec.message_post(body=_("Ticket created from website."))
        return records


class HelpdeskVisitDeviceLine(models.Model):
    _name = "helpdesk.visit.device.line"
    _description = "Help Desk Visit Report - Device Line"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    report_id = fields.Many2one("helpdesk.visit.report", ondelete="cascade", required=True)
    device_id = fields.Many2one("helpdesk.device", string="Device", required=True)
    overall_status = fields.Selection(POS_STATUS, string="Overall Status", required=True)
    notes = fields.Char(string="Notes")
