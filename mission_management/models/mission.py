from odoo import models, fields, api
from odoo.exceptions import UserError


class MissionManagement(models.Model):
    _name = 'mission.management'
    _description = 'Mission Management'

    # Mission Information Group
    reference = fields.Many2one('hr.employee', string='Reference of the Mission', required=True)
    mission_type_id = fields.Many2one('mission.type', string='Type of the Mission', required=True)
    objective_id = fields.Many2one('mission.objective', string='Objective of the Mission', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    address = fields.Char(string='Address of the Mission', required=True)
    partner_id = fields.Many2one('hr.employee', string='Partner of the Mission', required=True)
    partner_manager_id = fields.Many2one('hr.employee', string='Manager of the Partner', required=True)
    budget = fields.Float(string='Budget', digits=(10, 2), required=True)

    # Mission Status
    mission_status = fields.Selection([
        ('requested', 'Requested'),
        ('refused', 'Refused'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('finished', 'Finished'),
    ], string='Status of the Mission', default='requested', required=True)


    # Notes and Targets (Group 2)
    notes = fields.Text(string='Notes')
    target = fields.Text(string='Target', required=True)





class MissionType(models.Model):
    _name = 'mission.type'
    _description = 'Mission Type'

    name = fields.Char(string='Mission Type', required=True)


class MissionObjective(models.Model):
    _name = 'mission.objective'
    _description = 'Mission Objective'

    name = fields.Char(string='Mission Objective', required=True)
