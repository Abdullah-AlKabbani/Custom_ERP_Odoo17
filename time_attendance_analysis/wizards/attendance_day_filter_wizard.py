from odoo import models, fields, api
from datetime import date

class AttendanceDayFilterWizard(models.TransientModel):
    _name = 'attendance.day.filter.wizard'
    _description = 'Select a date to list employees who did not attend'

    target_date = fields.Date(string="Date", default=lambda self: date.today(), required=True)

    def action_open_not_attending(self):
        self.ensure_one()
        # Call the helper on hr.employee to build the action with the right domain
        return self.env['hr.employee'].action_not_attended_on_date(self.target_date)
