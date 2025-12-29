
from importlib.resources import files

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Owner(models.Model):
    _name = 'owner'

    name=fields.Char(required=1,default='Owner Name', size=12)
    phone = fields.Char(size=12)
    address = fields.Char()


    # هاد الحقل غير محفوظ بقاعدة البيانات  البراميتر التاني هو الفورن كي بالفيلد التاني

    property_ids=fields.One2many('property','owner_id')