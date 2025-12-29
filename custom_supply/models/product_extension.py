from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = "Product Template with Chatter"

    # 🔹 هل المنتج مخصص للتوريد؟
    product_for_supply = fields.Boolean(
        string="Product For Supply ?",
        default=False,
        help="Enable this if the product is allowed to be handled by the supply department."
    )

    custom_supply_field_1 = fields.Selection(
        [('basic', 'Basic'), ('secondary', 'Secondary')],
        string="Supply Type",
        default='secondary',
        help="Define if the product is Basic or Secondary for Supply Requests"
    )

    custom_supply_field_2 = fields.Char(
        string="Additional Info",
        help="Optional field for extra information"
    )

    branch_product_ids = fields.One2many(
        'custom_supply.branch_product',
        'product_id',
        string="Branch Products"
    )

    # 🔹 حقل Many2one للوحدة، مرتبط بالوحدات المعرفة في custom_supply.unit
    supply_unit_id = fields.Many2one(
        'custom_supply.unit',
        string="Supply Unit",
        help="Select the unit used for supply (e.g., Carton, Bag, Box, Piece, etc.)",
        tracking=True
    )

    # ===========================
    # سجل تغييرات الوحدة في Chatter
    # ===========================
    def write(self, vals):
        for rec in self:
            if 'supply_unit_id' in vals:
                old_unit = rec.supply_unit_id.name if rec.supply_unit_id else 'N/A'
                new_unit = self.env['custom_supply.unit'].browse(vals['supply_unit_id']).name
                rec.message_post(
                    body=f"Supply Unit changed from '{old_unit}' to '{new_unit}' by {self.env.user.name}."
                )

        # 2️⃣ تنفيذ الكتابة الأصلية
        res = super(ProductTemplate, self).write(vals)

        # 3️⃣ التحقق من تغيير حالة المنتج للتوريد
        if 'product_for_supply' in vals and vals['product_for_supply']:
            # المنتج أصبح صالح للتوريد
            branch_model = self.env['custom_supply.branch']
            branch_product_model = self.env['custom_supply.branch_product']

            branches = branch_model.search([])

            # جمع معرفات الفروع الموجودة لكل سجل branch_product
            existing_pairs = branch_product_model.search([('product_id', 'in', self.ids)]).mapped(
                lambda bp: (bp.branch_id.id, bp.product_id.id))

            to_create = []
            for branch in branches:
                for product in self:
                    pair = (branch.id, product.id)
                    if pair not in existing_pairs:
                        to_create.append({
                            'branch_id': branch.id,
                            'product_id': product.id,
                            'min_quantity': 0.0,
                            'max_quantity': 0.0,
                            'current_quantity': 0.0,
                            'activate': True,
                        })

            if to_create:
                branch_product_model.create(to_create)

            if 'product_for_supply' in vals:
                self.env['custom_supply.branch'].sync_branch_products()

        return res


class SupplyUnit(models.Model):
    _name = "custom_supply.unit"
    _description = "Supply Unit"

    name = fields.Char(string="Unit Name", required=True)

    _sql_constraints = [
        ('unique_unit_name', 'unique(name)', 'This supply unit name already exists.')
    ]
