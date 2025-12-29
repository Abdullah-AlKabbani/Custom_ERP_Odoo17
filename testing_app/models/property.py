from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class Property(models.Model):
    _name = 'property'
    _description = 'A New Property Has been Created.'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, default='A Name', size=10)
    description = fields.Text(tracking=1)
    postcode = fields.Char()
    data_availability = fields.Date(tracking=1)
    expected_price = fields.Float()
    selling_price = fields.Float()
    diff = fields.Float(compute="_compute_diff", store=1, readonly=1)
    bedrooms = fields.Integer()
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Selection([
        ('North', 'north'), ('South', 'south'), ('East', 'east'), ('West', 'west')
    ], default='North')
    owner_id = fields.Many2one('owner', string="Owner")
    tag_id = fields.Many2many('tag', string='Tag')
    state = fields.Selection([('draft', 'Draft'), ('pending', 'Pending'), ('sold', 'Sold')], default='draft')
    owner_address = fields.Char(related='owner_id.address', readonly=0, stored=1)
    owner_phone = fields.Char(related='owner_id.phone', readonly=0, stored=1)
    line_ids=fields.One2many('property.line','property_id')
    active = fields.Boolean(defult=True)
    _sql_constraints = [
        ('unique_name', 'unique(name)', 'The Name already exists!')
    ]

    @api.constrains("bedrooms")
    def _check_bedrooms_greater_zero(self):
        for rec in self:
            if rec.bedrooms <= 0:
                raise ValidationError('Please add a valid number of bedrooms greater than zero.')

    def action_draft(self):
        for rec in self:
            # logic
            rec.state = 'draft'

    def action_pending(self):
        for rec in self:
            # logic
            rec.state = 'pending'

    def action_sold(self):
        for rec in self:
            # logic
            rec.state = 'sold'

    @api.depends('expected_price', 'selling_price', 'owner_id.phone')
    def _compute_diff(self):
        for rec in self:
            # logic
            rec.diff = rec.expected_price - rec.selling_price

    @api.onchange('expected_price')
    def _onchange_expected_price(self):
        for rec in self:
            if rec.expected_price < 0:
                _logger.warning("Negative value detected for expected_price.")
                return {
                    'warning': {
                        'title': 'Warning',
                        'message': 'Negative Number.'
                    }
                }

    # # CRUD Operations
    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super(Property, self).create(vals_list)
    #     # Additional logic can be added here if needed
    #     return res
    #
    # def write(self, vals):
    #     res = super(Property, self).write(vals)  # Use 'write' to update the record
    #     # Additional logic can be added here if needed
    #     return res
    #
    # def unlink(self):
    #     res = super(Property, self).unlink()  # Use 'unlink' to delete the record
    #     # Additional logic can be added here if needed
    #     return res


class PropertyLine(models.Model):
    _name = 'property.line'

    property_id=fields.Many2one('property')
    area = fields.Float()
    description = fields.Char()
