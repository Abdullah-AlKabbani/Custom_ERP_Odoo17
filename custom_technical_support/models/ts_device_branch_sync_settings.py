# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TsDeviceBranchSyncSettings(models.TransientModel):
    _name = "ts.device.branch.sync.settings"
    _description = "Device Branch Sync Settings"

    branch_ids = fields.Many2many(
        'custom_supply.branch',
        'ts_device_branch_sync_branch_rel',
        'settings_id',
        'branch_id',
        string="Branches",
        help="Select branches to sync (leave empty for all active branches)"
    )

    device_ids = fields.Many2many(
        'ts.device',
        'ts_device_branch_sync_device_rel',
        'settings_id',
        'device_id',
        string="Devices",
        help="Select devices to sync (leave empty for all active devices)"
    )

    def manual_sync(self):
        """
        Sync devices with branches.
        """
        DeviceBranch = self.env['ts.device.branch']

        # =========================
        # Determine branches
        # =========================
        if self.branch_ids:
            branches = self.branch_ids
        else:
            branches = self.env['custom_supply.branch'].search([
                ('state', '=', 'active')
            ])

        # =========================
        # Determine devices
        # =========================
        if self.device_ids:
            devices = self.device_ids
        else:
            devices = self.env['ts.device'].search([
                ('active', '=', True)
            ])

        created_count = 0

        # =========================
        # Sync Logic
        # =========================
        for branch in branches:
            for device in devices:
                exists = DeviceBranch.search([
                    ('branch_id', '=', branch.id),
                    ('device_id', '=', device.id)
                ], limit=1)

                if not exists:
                    DeviceBranch.create({
                        'branch_id': branch.id,
                        'device_id': device.id,
                        'current_qty': 0,
                        'active': True,
                        'note': '',
                    })
                    created_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Device Branch Sync',
                'message': f'{created_count} device-branch records created.',
                'type': 'success',
                'sticky': False,
            }
        }
