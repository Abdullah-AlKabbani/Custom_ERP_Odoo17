# custom_technical_support/models/ts_device_move.py

from odoo import models, fields, api
from odoo.exceptions import ValidationError, AccessError


class TsDeviceMove(models.Model):
    _name = 'ts.device.move'
    _description = 'Device Movement / Audit Trail'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    # =================================================
    # Core Fields
    # =================================================
    device_id = fields.Many2one('ts.device', required=True, index=True, tracking=True)
    branch_id = fields.Many2one('custom_supply.branch', required=True, index=True, tracking=True)
    move_type = fields.Selection(
        [
            ('in', 'Input'),
            ('out', 'Output'),
            ('scrap', 'Scrap')
        ],required=True,tracking=True,group_expand='_group_expand_move_type')

    qty = fields.Integer(string='Quantity',required=True,tracking=True)
    qty_before = fields.Integer(string='Quantity Before',readonly=True)
    current_qty = fields.Integer(string='Current Quantity',readonly=True)
    branch_device_id = fields.Many2one('ts.device.branch',string='Device in Branch',compute='_compute_branch_device',store=True)
    reference_type = fields.Char()
    reference_id = fields.Integer()
    date = fields.Datetime(default=fields.Datetime.now,required=True,tracking=True)
    operation_date = fields.Datetime(string="Operation Date",required=True,default=fields.Datetime.now,tracking=True)
    user_id = fields.Many2one('res.users',default=lambda self: self.env.user,readonly=True,tracking=True)
    note = fields.Text()

    # =================================================
    # Scrap
    # =================================================
    is_scrap = fields.Boolean(string="Is Scrap",compute='_compute_is_scrap',store=True)
    scrap_reason_id = fields.Many2one('ts.device.scrap.reason',string='Scrap Reason',tracking=True)

    # =================================================
    # State
    # =================================================
    active_move = fields.Boolean(string="Active Move",default=True,tracking=True)
    is_editable = fields.Boolean(string='Is Editable',compute='_compute_is_editable',store=False)

    # =================================================
    # Helpers
    # =================================================
    def _group_expand_move_type(self, statuses, domain, order):
        return ['in', 'out', 'scrap']

    # -------------------------------------------------
    # Computes
    # -------------------------------------------------
    @api.depends('move_type')
    def _compute_is_scrap(self):
        for rec in self:
            rec.is_scrap = rec.move_type == 'scrap'

    def _compute_is_editable(self):
        for rec in self:
            rec.is_editable = not bool(rec.id)

    def _compute_branch_device(self):
        for rec in self:
            if not rec.device_id or not rec.branch_id:
                rec.branch_device_id = False
                continue

            device_branch = self.env['ts.device.branch'].search(
                [
                    ('device_id', '=', rec.device_id.id),
                    ('branch_id', '=', rec.branch_id.id)
                ],
                limit=1
            )
            rec.branch_device_id = device_branch.id if device_branch else False

    # =================================================
    # Validations
    # =================================================
    @api.constrains('qty')
    def _check_qty_positive(self):
        for rec in self:
            if rec.qty <= 0:
                raise ValidationError('Quantity must be greater than zero.')

    # =================================================
    # Access Rights
    # =================================================
    def check_access_rights(self, operation, raise_exception=True):
        user = self.env.user

        if user.has_group('custom_technical_support.group_ts_super_admin'):
            return super().check_access_rights(operation, raise_exception)

        if operation in ('create', 'write'):
            if not user.has_group('custom_technical_support.group_ts_team_leader'):
                if raise_exception:
                    raise AccessError(
                        'You do not have permission to modify device moves.'
                    )
                return False

        return super().check_access_rights(operation, raise_exception)

    # =================================================
    # Internal Quantity Logic
    # =================================================
    def _get_or_create_branch_device(self):
        self.ensure_one()

        device_branch = self.env['ts.device.branch'].search(
            [
                ('device_id', '=', self.device_id.id),
                ('branch_id', '=', self.branch_id.id)
            ],
            limit=1
        )

        if not device_branch:
            device_branch = self.env['ts.device.branch'].create({
                'device_id': self.device_id.id,
                'branch_id': self.branch_id.id,
                'current_qty': 0
            })

        return device_branch

    def _apply_qty_logic(self, base_qty):
        self.ensure_one()

        if self.move_type == 'in':
            return base_qty + self.qty
        else:
            return base_qty - self.qty

    # =================================================
    # Create / Write / Delete
    # =================================================
    @api.model
    def create(self, vals):
        self.check_access_rights('create')
        rec = super().create(vals)

        device_branch = rec._get_or_create_branch_device()

        # Snapshot BEFORE
        rec.qty_before = device_branch.current_qty

        # Apply operation
        if rec.active_move:
            new_qty = rec._apply_qty_logic(device_branch.current_qty)
            if new_qty < 0:
                raise ValidationError('Negative quantity not allowed.')

            device_branch.current_qty = new_qty
            device_branch.last_move_date = rec.date

            # Snapshot AFTER
            rec.current_qty = new_qty
        else:
            rec.current_qty = device_branch.current_qty

        rec.message_post(
            body=f'Move created by {rec.env.user.name}'
        )
        return rec

    def write(self, vals):
        self.check_access_rights('write')

        blocked_fields = [
            'device_id', 'branch_id',
            'move_type', 'qty',
            'date', 'operation_date'
        ]

        for field in blocked_fields:
            if field in vals:
                raise ValidationError(
                    f'Field "{field}" cannot be modified after creation.'
                )

        res = super().write(vals)

        if 'active_move' in vals:
            for rec in self:
                rec._toggle_move_effect()
                rec.message_post(
                    body=f'Move {"activated" if rec.active_move else "deactivated"} '
                         f'by {self.env.user.name}'
                )
        return res

    def unlink(self):
        user = self.env.user
        if not user.has_group('custom_technical_support.group_ts_super_admin'):
            raise AccessError('Only Super Admin can delete device moves.')

        for rec in self:
            device_branch = rec.branch_device_id
            if not device_branch:
                continue

            # ✅ إذا كانت الحركة مفعّلة → نلغي أثرها قبل الحذف
            if rec.active_move:
                if rec.move_type == 'in':
                    # undo input
                    new_qty = device_branch.current_qty - rec.qty
                else:
                    # undo out / scrap
                    new_qty = device_branch.current_qty + rec.qty

                if new_qty < 0:
                    raise ValidationError(
                        'Cannot delete this move because it would result in negative quantity.'
                    )

                device_branch.current_qty = new_qty
                device_branch.last_move_date = fields.Datetime.now()

        return super().unlink()

    # =================================================
    # Toggle Logic
    # =================================================
    def _toggle_move_effect(self):
        for rec in self:
            device_branch = rec._get_or_create_branch_device()

            if rec.active_move:
                # APPLY
                new_qty = rec._apply_qty_logic(device_branch.current_qty)
            else:
                # REVERSE
                if rec.move_type == 'in':
                    new_qty = device_branch.current_qty - rec.qty
                else:
                    new_qty = device_branch.current_qty + rec.qty

            if new_qty < 0:
                raise ValidationError('Negative quantity not allowed.')

            device_branch.current_qty = new_qty
            device_branch.last_move_date = fields.Datetime.now()

            rec.current_qty = new_qty

    # =================================================
    # UI Dynamic Preview (No DB Effect)
    # =================================================
    @api.onchange('device_id', 'branch_id', 'move_type', 'qty')
    def _onchange_preview_quantities(self):
        if not self.device_id or not self.branch_id or not self.qty:
            self.qty_before = 0
            self.current_qty = 0
            return

        device_branch = self.env['ts.device.branch'].search(
            [
                ('device_id', '=', self.device_id.id),
                ('branch_id', '=', self.branch_id.id)
            ],
            limit=1
        )

        base_qty = device_branch.current_qty if device_branch else 0
        self.qty_before = base_qty

        if self.move_type == 'in':
            self.current_qty = base_qty + self.qty
        else:
            self.current_qty = base_qty - self.qty

    # =================================================
    # Button
    # =================================================
    def action_toggle_move(self):
        for rec in self:
            rec.active_move = not rec.active_move
            rec._toggle_move_effect()
            rec.message_post(
                body=f'Move {"activated" if rec.active_move else "deactivated"} '
                     f'by {self.env.user.name}'
            )
