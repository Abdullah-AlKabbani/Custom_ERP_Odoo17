from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class Gps(models.Model):
    _name = 'gps'

    license_plate_id = fields.Many2one('fleet.vehicle', string="License Plate", required=True)
    supervisor_id = fields.Many2one(
        'hr.employee',
        string="Supervisor",
        domain="[('job_id.name',  'ilike', 'مشرف')]")

    driver_position = fields.Many2one(
        'hr.job',
        string="Driver's Position",
        domain="[('name', 'ilike', 'مندوب')]"
    )

    driver_id = fields.Many2one(
        'hr.employee',
        string="Driver",
        domain="[('job_id.name', 'ilike', 'مندوب')]"
    )

    date_field = fields.Date(string="Date", required=True ,  driver_id = fields.Many2one('hr.employee', string="Driver"))
    time_going_to_company = fields.Datetime(string="Going to Company")
    time_access_company = fields.Datetime(string="Access to Company")
    time_going_out_work = fields.Datetime(string="Going Out to Work")
    time_enter_line = fields.Datetime(string="Enter Line")
    time_exit_line = fields.Datetime(string="Exit Line")

    full_working_time = fields.Float(
        string="Full Working Time (Hours)", compute="_compute_full_working_time", store=True, readonly=True
    )
    working_hours_on_line = fields.Float(
        string="Working Hours on Line", compute="_compute_working_hours_on_line", store=True, readonly=True
    )
    overnight_hours = fields.Datetime(string="Overnight Hours")

    @api.depends('time_going_to_company', 'time_exit_line')
    def _compute_full_working_time(self):
        for record in self:
            if record.time_going_to_company and record.time_exit_line:
                duration = record.time_exit_line - record.time_going_to_company
                record.full_working_time = duration.total_seconds() / 3600  # Convert to hours
            else:
                record.full_working_time = 0.0

    @api.depends('time_enter_line', 'time_exit_line')
    def _compute_working_hours_on_line(self):
        for record in self:
            if record.time_enter_line and record.time_exit_line:
                duration = record.time_exit_line - record.time_enter_line
                record.working_hours_on_line = duration.total_seconds() / 3600  # Convert to hours
            else:
                record.working_hours_on_line = 0.0

    # Group 3: Additional Information
    work_area = fields.Text(string="Work Area")
    violations_id = fields.Many2many('violations', string='Violations')
    violation_notes = fields.Text(string="Notes on Violations")
    accommodation_area = fields.Text(string="Accommodation Area")
    itinerary = fields.Text(string="Itinerary")
    kilometers_traveled = fields.Float(string="Kilometers Traveled During the Day")
    highest_speed = fields.Float(string="Highest Speed")
    fuel_consumption = fields.Float(string="Fuel Consumption")
    gps_jamming = fields.Boolean(string="GPS Jamming")
    sales_supervisor_note = fields.Text(string="Sales Supervisor Note")
    fuel_type = fields.Selection([
        ('Gasoline', 'gasoline'), ('Electric', 'electric'), ('Diesel', 'diesel'),
    ], default='Gasoline')

    @api.model_create_multi
    def create(self, vals_list):
        res = super(Gps, self).create(vals_list)
        # Additional logic can be added here if needed
        return res

    def write(self, vals):
        res = super(Gps, self).write(vals)  # Use 'write' to update the record
        # Additional logic can be added here if needed
        return res

    def unlink(self):
        res = super(Gps, self).unlink()  # Use 'unlink' to delete the record
        # Additional logic can be added here if needed
        return res
