from odoo import models, fields, api
from odoo.exceptions import UserError


class OvertimeRequest(models.Model):
    _name = 'overtime.request'
    _description = 'Overtime Request'

    # Fields
    name = fields.Char(string="Request Name", required=True)
    department_id = fields.Many2one('hr.department', string="Department")
    employee_ids = fields.Many2many('hr.employee', string="Employees")
    description = fields.Text(string="Description")
    hours = fields.Float(string="Overtime Hours")
    state = fields.Selection([
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('refused', 'Refused')
    ], string="Status", default='requested', tracking=True)

    # Overriding the create method
    @api.model
    def create(self, vals):
        # Create the overtime request record
        res = super(OvertimeRequest, self).create(vals)

        # Update each employee's working hours
        for employee in res.employee_ids:
            if hasattr(employee, 'working_hours'):
                employee.sudo().write({'working_hours': employee.working_hours + res.hours})
            else:
                raise AttributeError("The 'working_hours' field does not exist for this employee.")
        return res

    # Action method for approving overtime requests
    def action_approve(self):
        for record in self:
            if record.state == 'approved':
                raise UserError('This request is already approved.')
            record.state = 'approved'

    # Action method for refusing overtime requests
    def action_refuse(self):
        for record in self:
            if record.state == 'refused':
                raise UserError('This request is already refused.')
            record.state = 'refused'

    # Action method for resetting the state to 'requested'
    def action_request(self):
        for record in self:
            if record.state == 'requested':
                raise UserError('This request is already in requested state.')
            record.state = 'requested'


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    # Adding a new field 'working_hours' to track total working hours of the employee
    working_hours = fields.Float(string="Working Hours", default=0.0)
