from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class Building(models.Model):
    _name = 'building'
    _description = 'A New building Has been Created.'
    _rec_name='code'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    no=fields.Integer()
    code=fields.Char()
    description=fields.Text()
    name=fields.Char()
    active=fields.Boolean(defult=True)


