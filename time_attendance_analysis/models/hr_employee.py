from odoo import models, api
from datetime import datetime, time

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def action_not_attended_on_date(self, target_date=None):
        """
        Return an action showing employees who did NOT check-in on target_date.
        target_date: Python date object (if None, uses today).
        """
        if not target_date:
            target_date = self.env.context.get('target_date')

        if not target_date:
            target_date = self.env.user.tz and datetime.now().date() or datetime.utcnow().date()

        start = datetime.combine(target_date, time.min)
        end = datetime.combine(target_date, time.max)

        # Employees who attended on that date
        attended_ids = self.env['hr.attendance'].search([
            ('check_in', '>=', start),
            ('check_in', '<=', end),
        ]).mapped('employee_id.id')

        return {
            'type': 'ir.actions.act_window',
            'name': 'Not Attending on %s' % target_date.strftime('%Y-%m-%d'),
            'res_model': 'hr.employee',
            'view_mode': 'tree',
            'domain': [('id', 'not in', attended_ids)],
            'view_id': self.env.ref('time_attendance_analysis.view_not_attending_today_tree').id,
            'context': {
                'default_target_date': target_date.strftime('%Y-%m-%d'),
            },
        }
