from email.policy import default
from importlib.resources import files

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Violations(models.Model):
    _name = 'violations'

    name = fields.Char(required=1, default='Violation Name', size=12)
