from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    management_name = fields.Char(string='Management Name')
    circuit_name = fields.Char(string='Circuit Name')
    replacement_employee_id = fields.Many2one(
        'hr.employee',
        string='Replacement Employee',
        domain="[('id', '!=', id)]"
    )
    place = fields.Char(string='Place', related='country_id.name', readonly=False)
    driving_certificate_no = fields.Char(string='Driving Certificate No')
    driving_certificate_date = fields.Date(string='Date of Driving Certificate')
    driving_certificate_end_date = fields.Date(string='End of Driving Certificate')
    driving_certificate_file = fields.Binary(string='Driving Certificate File')
    smoker = fields.Boolean(string='Smoker')
