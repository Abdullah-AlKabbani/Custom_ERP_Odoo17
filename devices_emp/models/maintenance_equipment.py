from odoo import models, fields

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    contract_image = fields.Binary(string="Contract Image", help="Upload the contract image.")
