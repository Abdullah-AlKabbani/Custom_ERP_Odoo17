from email.policy import default
from importlib.resources import files

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Tag(models.Model):
    _name = 'tag'

    name = fields.Char(required=1, default='Tag Name', size=12)
