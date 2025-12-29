from odoo import models, fields

class PurchaseOffer(models.Model):
    _name = 'purchase.offer'
    _description = 'Vendor Price Offer'

    vendor_id = fields.Many2one('res.partner', string='Vendor', domain=[('supplier_rank', '>', 0)], required=True)
    price = fields.Float(string='Price', required=True)
    description = fields.Text(string='Description')
    document = fields.Binary(string='Attach Document')
    request_id = fields.Many2one('purchase.request', string='Purchase Request')
    is_selected = fields.Boolean(string="Best Offer")
