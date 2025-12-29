from odoo import models, fields, api
from odoo.exceptions import ValidationError, AccessError


class TsDeviceBranch(models.Model):
    _name = 'ts.device.branch'
    _description = 'Device Quantity per Branch'
    _rec_name = 'device_id'
    _order = 'last_move_date desc'

    branch_id = fields.Many2one('custom_supply.branch',string="Branch",required=True,ondelete='cascade',index=True)
    device_id = fields.Many2one('ts.device',string="Device",required=True,ondelete='cascade',index=True)
    category_id = fields.Many2one(related='device_id.category_id',store=True,readonly=True)

    # =========================
    # Device Status in Branch
    # =========================
    active = fields.Boolean(string="Active in Branch",default=True)
    note = fields.Text(string="Branch Notes")
    branch_user_id = fields.Many2one(related='branch_id.user_id',string="Branch User",store=True,readonly=True)
    current_qty = fields.Integer(string="Current Quantity",default=0)
    last_move_date = fields.Datetime(string="Last Update",default=fields.Datetime.now,readonly=True)

    # =========================
    # SQL Constraints
    # =========================
    _sql_constraints = [
        (
            'unique_device_branch',
            'unique(branch_id, device_id)',
            'This device is already assigned to this branch.'
        )
    ]

    def check_access_rights(self, operation, raise_exception=True):
        user = self.env.user
        if user.has_group('custom_technical_support.group_ts_super_admin'):
            return super().check_access_rights(operation, raise_exception)

        if operation in ('create', 'write', 'unlink') and not user.has_group(
                'custom_technical_support.group_ts_team_leader'
        ):
            if raise_exception:
                raise AccessError('You do not have permission to modify branch quantities.')
            return False

        return super().check_access_rights(operation, raise_exception)

    @api.constrains('current_qty')
    def _check_qty_not_negative(self):
        for rec in self:
            if rec.current_qty < 0:
                raise ValidationError('Device quantity cannot be negative.')

    def update_quantity(self, qty_change, move_date):
        self.check_access_rights('write')
        for rec in self:
            new_qty = rec.current_qty + qty_change
            if new_qty < 0:
                raise ValidationError('Resulting quantity cannot be negative.')
            rec.current_qty = new_qty
            rec.last_move_date = move_date

    def create(self, vals):
        self.check_access_rights('create')
        device = super().create(vals)
        return device

    def write(self, vals):
        self.check_access_rights('write')
        vals['last_move_date'] = fields.Datetime.now()
        return super().write(vals)

    def unlink(self):
        self.check_access_rights('unlink')
        return super().unlink()
