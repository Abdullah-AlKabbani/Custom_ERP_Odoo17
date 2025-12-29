from odoo import models, fields, api
from datetime import datetime, date, timedelta, time

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    late_time_str = fields.Char(string="Total Late (H:MM)", compute="compute_lateness_overtime")
    extra_time_str = fields.Char(string="Total Extra (H:MM)", compute="compute_lateness_overtime")

    @api.depends('attendance_ids.check_in', 'attendance_ids.check_out')
    def compute_lateness_overtime(self):
        today = date.today()
        start_month = today.replace(day=1)

        for employee in self:
            total_late = timedelta()
            total_extra = timedelta()

            # Filter attendances from this month for the employee
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', datetime.combine(start_month, time.min)),
                ('check_in', '<=', datetime.combine(today, time.max)),
                ('check_out', '!=', False)
            ])

            for att in attendances:
                check_in = att.check_in
                check_out = att.check_out

                # Define working hours with tolerance
                official_start = datetime.combine(check_in.date(), time(8, 0)) + timedelta(minutes=20)
                official_end = datetime.combine(check_in.date(), time(16, 0)) + timedelta(minutes=10)

                if check_in > official_start:
                    total_late += (check_in - official_start)

                if check_out > official_end:
                    total_extra += (check_out - official_end)

            # Convert to H:MM format
            employee.late_time_str = f"{int(total_late.total_seconds() // 3600)}:{int((total_late.total_seconds() % 3600) // 60):02}"
            employee.extra_time_str = f"{int(total_extra.total_seconds() // 3600)}:{int((total_extra.total_seconds() % 3600) // 60):02}"

    @api.model
    def action_not_attended_today(self):
        today = datetime.today().date()
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)

        # Get all employees who checked in today
        attended_ids = self.env['hr.attendance'].search([
            ('check_in', '>=', start),
            ('check_in', '<=', end),
        ]).mapped('employee_id.id')

        # Return action to show not-attending employees
        return {
            'type': 'ir.actions.act_window',
            'name': 'Not Attending Today',
            'res_model': 'hr.employee',
            'view_mode': 'tree',
            'domain': [('id', 'not in', attended_ids)],
            'view_id': self.env.ref('time_attendance_analysis.view_not_attending_today_tree').id,
        }
