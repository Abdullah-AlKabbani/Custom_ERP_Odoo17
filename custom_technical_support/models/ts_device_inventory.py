from odoo import models, fields
from odoo.exceptions import ValidationError

class TsDeviceInventory(models.Model):
    _name = 'ts.device.inventory'
    _description = 'Device Inventory Adjustment'
    _order = 'date desc'

    device_id = fields.Many2one('ts.device', required=True)
    branch_id = fields.Many2one('custom_supply.branch', required=True)
    counted_qty = fields.Integer(required=True)
    system_qty = fields.Integer(readonly=True)
    date = fields.Datetime(default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, readonly=True)
    note = fields.Text(string='Notes')

    def action_validate_inventory(self):
        """Create inventory move for difference"""
        for rec in self:
            device_branch = self.env['ts.device.branch'].search([
                ('device_id','=',rec.device_id.id),
                ('branch_id','=',rec.branch_id.id)
            ], limit=1)

            if not device_branch:
                raise ValidationError('No device record found for this branch.')

            rec.system_qty = device_branch.current_qty
            diff = rec.counted_qty - device_branch.current_qty

            if diff == 0:
                raise ValidationError('No difference found. Inventory not required.')

            move_type = 'inventory'
            qty = abs(diff)

            # create move
            move = self.env['ts.device.move'].create({
                'device_id': rec.device_id.id,
                'branch_id': rec.branch_id.id,
                'move_type': move_type,
                'qty': qty,
                'note': f'Inventory adjustment from {device_branch.current_qty} to {rec.counted_qty}',
                'reference_type': 'Inventory',
                'reference_id': rec.id
            })

            move.action_done()
