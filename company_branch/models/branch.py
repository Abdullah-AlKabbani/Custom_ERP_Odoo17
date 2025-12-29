# -*- coding: utf-8 -*-
import random
import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re

_logger = logging.getLogger(__name__)

class Branch(models.Model):
    _name = "custom_supply.branch"
    _description = "Company Branch"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"
    _order = "write_date desc"

    # ======== Basic Info ========
    name = fields.Char(string="Branch Name", required=True, tracking=True)
    user_id = fields.Many2one('res.users', string="Branch User", tracking=True)
    branch_type_id = fields.Many2one('custom_supply.branch.type',string="Branch Type",required=True,ondelete='restrict')
    color = fields.Integer(string="Color", default=lambda self: random.randint(1, 11))
    last_updated = fields.Datetime(string="Last Updated", compute="_compute_last_updated", store=True)

    # ======== Location Info ========
    country_id = fields.Many2one('custom_supply.country', string="Country", tracking=True)
    city_id = fields.Many2one('custom_supply.city', string="City", tracking=True, domain="[('country_id','=',country_id)]")
    area = fields.Char(string="Area", tracking=True)
    location = fields.Char(string="Google Maps Link", tracking=True)
    latitude = fields.Float(string="Latitude", compute="_compute_coordinates", store=True)
    longitude = fields.Float(string="Longitude", compute="_compute_coordinates", store=True)

    # ======== Lifecycle ========
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('closed', 'Closed'),
    ], default='draft', tracking=True)
    previous_state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string="Previous State", copy=False)
    opened_date = fields.Date(tracking=True)
    closed_date = fields.Date(tracking=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Branch name must be unique!'),
    ]

    # ======== Compute Last Updated ========
    @api.depends("write_date")
    def _compute_last_updated(self):
        for rec in self:
            rec.last_updated = rec.write_date

    # ======== Compute Coordinates ========
    @api.depends('location')
    def _compute_coordinates(self):
        for rec in self:
            rec.latitude = 0.0
            rec.longitude = 0.0
            if rec.location:
                match = re.search(r'@([-0-9.]+),([-0-9.]+)', rec.location)
                if match:
                    rec.latitude = float(match.group(1))
                    rec.longitude = float(match.group(2))

    # ======== State Buttons ========
    def action_activate(self):
        for rec in self:
            if rec.state in ['draft', 'inactive']:
                rec.state = 'active'
                rec.last_updated = fields.Datetime.now()

    def action_inactive(self):
        for rec in self:
            if rec.state == 'active':
                rec.state = 'inactive'
                rec.last_updated = fields.Datetime.now()

    def action_close(self):
        for rec in self:
            if rec.state != 'closed':
                rec.previous_state = rec.state
                rec.closed_date = fields.Date.today()
                rec.state = 'closed'
                rec.last_updated = fields.Datetime.now()

    def action_reopen(self):
        for rec in self:
            if rec.state == 'closed':
                rec.state = 'active'
                rec.previous_state = False
                rec.closed_date = False
                rec.last_updated = fields.Datetime.now()

    # ======== Unique User Validation ========
    @api.constrains('user_id')
    def _check_unique_user(self):
        for rec in self:
            if rec.user_id:
                count = self.search_count([
                    ('user_id', '=', rec.user_id.id),
                    ('id', '!=', rec.id)
                ])
                if count:
                    raise ValidationError("This user is already assigned to another branch.")

    # ======== Create / Write Overrides ========
    @api.model
    def create(self, vals):
        if 'color' not in vals:
            last = self.search([], order="color desc", limit=1)
            vals['color'] = (last.color % 11) + 1 if last else 1
        branch = super().create(vals)
        if branch.user_id:
            old = self.search([('user_id', '=', branch.user_id.id), ('id', '!=', branch.id)], limit=1)
            if old:
                old.user_id = False
            branch.user_id.sudo().branch_id = branch

        devices = self.env['ts.device'].search([('active', '=', True)])
        for device in devices:
            self.env['ts.device.branch'].create({
                'branch_id': branch.id,
                'device_id': device.id,
            })

        return branch

    def write(self, vals):
        res = super().write(vals)
        if 'user_id' in vals:
            for branch in self:
                if branch.user_id:
                    old = self.search([('user_id', '=', branch.user_id.id), ('id', '!=', branch.id)], limit=1)
                    if old:
                        old.user_id = False
                    branch.user_id.sudo().branch_id = branch
        return res
