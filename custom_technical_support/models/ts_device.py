from odoo import models, fields, api
from odoo.exceptions import ValidationError, AccessError


class TsDevice(models.Model):
    _name = 'ts.device'
    _description = 'Technical Device'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, index=True, tracking=True)
    brand_id = fields.Many2one('ts.device.brand',string='Brand',domain="[('category_id', '=', category_id)]")
    device_model = fields.Many2one('ts.device.model',string='Model',domain="[('brand_id', '=', brand_id)]")
    image_1920 = fields.Image(string="Image")
    note = fields.Text(string="Notes")
    category_id = fields.Many2one('ts.device.category',string='Category',ondelete='restrict')
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], default='active', tracking=True)

    # ======== Device Capabilities ========
    has_ip = fields.Boolean(string='Has IP')
    has_serial = fields.Boolean(string='Has Serial Number')
    has_password = fields.Boolean(string='Has Password')

    ip_address = fields.Char(string='IP Address', tracking=True)
    serial_number = fields.Char(string='Serial Number')
    password = fields.Char(string='Password')

    # ======== SQL Constraints ========
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Device Name must be unique!'),
        ('serial_number_unique', 'unique(serial_number)', 'Serial Number must be unique!')
    ]

    # ======== Optional: helper to display properties ========
    def name_get(self):
        result = []
        for rec in self:
            name = rec.name or ''
            if rec.brand_id and rec.brand_id.exists():
                name = f'{rec.brand_id.display_name} {name}'
            if rec.device_model:
                name += f' ({rec.device_model.display_name})'
            if rec.serial_number:
                name += f' [{rec.serial_number}]'
            result.append((rec.id, name))
        return result

    # ====== Sync State ======
    @api.onchange('state')
    def _onchange_state(self):
        for rec in self:
            rec.active = rec.state == 'active'

    # ====== Privacy / Access Protection ======
    @api.constrains('category_id')
    def _check_category(self):
        for rec in self:
            if not rec.category_id:
                raise ValidationError("Device must have a category.")

    def _check_sensitive_access(self):
        user = self.env.user
        if not user.has_group('custom_technical_support.group_ts_manager'):
            raise AccessError('Only Manager can modify IP, Serial Number, or Password.')

    def show_password(self):
        self.ensure_one()
        if not self.env.user.has_group('custom_technical_support.group_ts_manager'):
            raise AccessError("Only Manager can view password.")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Device Password',
                'message': f'{self.password}',
                'sticky': False,
            }
        }

    def check_access_rights(self, operation, raise_exception=True):
        if self.env.user.has_group('custom_technical_support.group_ts_readonly'):
            if operation != 'read':
                if raise_exception:
                    raise AccessError("You are not allowed to modify devices.")
                return False
        return super().check_access_rights(operation, raise_exception)

    @api.model
    def create(self, vals):
        device = super().create(vals)
        branches = self.env['custom_supply.branch'].search([...])

        for branch in branches:
            self.env['ts.device.branch'].create({
                'branch_id': branch.id,
                'device_id': device.id,
            })
        return device

    def write(self, vals):
        password_changed = 'password' in vals

        res = super().write(vals)

        if password_changed:
            for rec in self:
                rec.message_post(
                    body="🔒 Password Updated.",
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )

        return res

    def unlink(self):
        return super().unlink()

    @api.constrains('has_ip', 'ip_address', 'has_serial', 'serial_number', 'has_password', 'password')
    def _check_device_properties(self):
        for rec in self:
            if rec.has_ip and not rec.ip_address:
                raise ValidationError('Device marked as "Has IP" but IP Address is empty.')
            if rec.has_serial and not rec.serial_number:
                raise ValidationError('Device marked as "Has Serial" but Serial Number is empty.')
            if rec.has_password and not rec.password:
                raise ValidationError('Device marked as "Has Password" but Password is empty.')