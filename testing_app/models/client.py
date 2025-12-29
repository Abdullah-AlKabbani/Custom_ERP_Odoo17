
from importlib.resources import files
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Client(models.Model):
    _name='client'
    _inherit='owner'
