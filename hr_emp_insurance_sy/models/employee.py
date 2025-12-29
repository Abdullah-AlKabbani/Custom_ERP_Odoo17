# hr_emp_insurance_sy/models/employee.py
from odoo import models, fields

class Employee(models.Model):

    _inherit = 'hr.employee'
    insurance_number = fields.Char(string="Insurance Number")
    insurance_salary = fields.Integer(string="Insurance Salary")
    insurance_date=fields.Date(string="Insurance Contract Date")
    end_insurance_date = fields.Date(string=" End Insurance Contract Date")
    contract_image = fields.Binary(string="Contract Image", attachment=True, help="Upload the contract image.")
    id_card_image = fields.Binary(string="Id Card  Image", attachment=True, help="Upload the ID Card image.")
    cv_file = fields.Binary(string="CV File",  help="Upload the CV File.")
    mother_name=fields.Char(string="Mother Name")