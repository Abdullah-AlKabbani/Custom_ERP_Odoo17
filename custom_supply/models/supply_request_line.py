# -*- coding: utf-8 -*-
import traceback
import logging

from odoo import models, fields, api
from odoo.exceptions import UserError

class SupplyRequestLine(models.Model):
    _name = "custom_supply.supply_request_line"
    _description = "Supply Request Line"

    PRIMITIVE_CURRENT_QTY = -1.0

    # ==============================================================
    # Basic Fields
    # ==============================================================

    request_id = fields.Many2one('custom_supply.supply_request',string="Request",ondelete='cascade')
    branch_id = fields.Many2one(string='Branch',related='request_id.branch_id',store=True,readonly=True)
    request_date = fields.Datetime(related="request_id.request_date",store=True,readonly=True)
    request_name = fields.Char(string="Request Number",related="request_id.name",store=True,readonly=True)
    allowed_product_ids = fields.Many2many('product.product',string='Allowed Products',compute='_compute_allowed_products',store=True)
    product_id = fields.Many2one('product.product',string="Product",required=True,)
    category_id = fields.Many2one('product.category',string="Category",related='product_id.categ_id',store=True,readonly=True)
    unit_name = fields.Char(string="Unit", readonly=True, store=True)
    display_unit_name = fields.Char(string="Unit", readonly=True, store=True)
    current_qty = fields.Float(string="Current Quantity",required=True, default=PRIMITIVE_CURRENT_QTY, store=True)
    suggested_qty = fields.Float(string="Suggested Quantity",compute="_compute_suggested_qty",store=True)
    suggested_qty_training = fields.Float(string="Suggested Qty For Training",help="Quantity used by the smart engine for machine learning instead of suggested_qty.")
    requested_qty = fields.Float(string="Requested Quantity",required=True,default=0.0)
    received_qty = fields.Float(string="Received Quantity", default=0.0)
    received_note = fields.Text(string="Receiving Note")
    note = fields.Text(string="Note / Reason")
    branch_product_id = fields.Many2one( 'custom_supply.branch_product',string="Branch Product Link")
    supply_qty = fields.Float(string="Supply Quantity", help="Quantity approved by Supply Manager")
    supply_note = fields.Text(string="Supply Note", help="Note / reason from Supply Manager")

    export_qty = fields.Float(string="Export Quantity",help="Quantity actually exported by Warehouse")
    warehouse_note = fields.Text(string="Warehouse Note",help="Note / reason from Warehouse")

    hide_lines = fields.Boolean(compute="_compute_hide_lines",store=False,)


    # ==============================================================
    # Hide Lines
    # ==============================================================
    @api.depends('current_qty', 'supply_qty', 'request_id.status')
    def _compute_hide_lines(self):
        for line in self:
            # إظهار الأسطر فقط في مراحل InBranch & Supply
            if line.request_id.state in ("in_branch", "supply"):
                line.hide_lines = False
            else:
                # خارج هاتين المرحلتين يتم إخفاء الأسطر غير الجاهزة
                line.hide_lines = (
                    line.current_qty == -1 and line.supply_qty == 0
                )

    # ==============================================================
    # Compute Allowed Products per Branch
    # ==============================================================
    @api.depends('request_id.branch_id')
    def _compute_allowed_products(self):
        Product = self.env['product.product']
        for rec in self:
            branch = rec.request_id.branch_id if rec.request_id else self.env.context.get('branch_id')
            if branch:
                rec.allowed_product_ids = branch.product_ids.filtered('activate').mapped('product_id') or Product
            else:
                rec.allowed_product_ids = Product

    @api.onchange('request_id')
    def _onchange_request_id(self):
        for rec in self:
            branch = rec.request_id.branch_id if rec.request_id else self.env.context.get('branch_id')
            if branch:
                rec.allowed_product_ids = branch.product_ids.filtered('activate').mapped('product_id')
            else:
                rec.allowed_product_ids = self.env['product.product']


    # ==============================================================
    # Compute Unit Name
    # ==============================================================

    def _get_unit_name_for_product(self, product):
        if product and product.product_tmpl_id.supply_unit_id:
            return product.product_tmpl_id.supply_unit_id.name
        return ''

    @api.onchange('product_id')
    def _onchange_product_id_fill_unit(self):
        """Fill unit_name immediately in the form/tree when choosing product"""
        if self.product_id and self.product_id.product_tmpl_id.supply_unit_id:
            self.unit_name = self.product_id.product_tmpl_id.supply_unit_id.name
        else:
            self.unit_name = ''

    # ==============================================================
    # Compute Suggested Quantity
    # ==============================================================

    @api.depends('product_id', 'current_qty', 'request_id.branch_id')
    def _compute_suggested_qty(self):
        for line in self:
            # أي قيمة سالبة → تحويلها إلى القيمة البدائية
            if line.current_qty < 0:
                line.current_qty = self.PRIMITIVE_CURRENT_QTY

            # الحقل فارغ بالقيمة البدائية → اقتراح 0.0
            if line.current_qty == self.PRIMITIVE_CURRENT_QTY:
                line.suggested_qty = 0.0
                continue

            # إذا لم يتم تحديد المنتج أو الفرع → اقتراح 0.0
            if not line.product_id or not line.request_id or not line.request_id.branch_id:
                line.suggested_qty = 0.0
                continue

            branch_product = self.env['custom_supply.branch_product'].search([
                ('branch_id', '=', line.request_id.branch_id.id),
                ('product_id', '=', line.product_id.id)
            ], limit=1)

            if branch_product:
                max_q = branch_product.max_quantity or 0.0
                line.suggested_qty = max(0.0, max_q - line.current_qty)
            else:
                line.suggested_qty = 0.0

    # =================================================================
    # Compute Suggested Quantity with Smart Engine
    # =================================================================
    #
    # @api.depends('product_id', 'current_qty', 'request_id.branch_id')
    # def _compute_suggested_qty(self):
    #     SmartEngine = self.env['custom_supply.smart_engine']
    #
    #     for line in self:
    #         # لو المعلومات غير مكتملة → صفر
    #         if not line.product_id or not line.request_id or not line.request_id.branch_id:
    #             line.suggested_qty = 0.0
    #             line.suggested_qty_training = 0.0
    #             continue
    #
    #         # الحصول على branch_product
    #         branch_product = self.env['custom_supply.branch_product'].search([
    #             ('branch_id', '=', line.request_id.branch_id.id),
    #             ('product_id', '=', line.product_id.id)
    #         ], limit=1)
    #
    #         if not branch_product:
    #             line.suggested_qty = 0.0
    #             line.suggested_qty_training = 0.0
    #             continue
    #
    #         # استدعاء المحرك وتمرير current_qty
    #         try:
    #             result = SmartEngine.compute_ideal_and_suggestion(
    #                 branch_product=branch_product,
    #                 current_qty=line.current_qty,
    #                 last_n=10,
    #                 min_history=5
    #             )
    #
    #             # القيمة التي يقترحها SmartEngine قبل أي تعديل
    #             engine_value = float(result.get('suggested_qty', 0.0) or 0.0)
    #
    #             # حفظها في حقل التدريب
    #             line.suggested_qty_training = engine_value
    #
    #             # القيمة النهائية = المقترح - current_qty
    #             final_suggestion = engine_value - float(line.current_qty or 0.0)
    #
    #             # لا نسمح للقيمة بأن تكون سالبة
    #             line.suggested_qty = max(0.0, final_suggestion)
    #
    #         except Exception:
    #             # fallback عند الخطأ
    #             line.suggested_qty = 0.0
    #             line.suggested_qty_training = 0.0

    # ==============================================================
    # CREATE rules for SupplyRequestLine
    # ==============================================================
    @api.model
    def create(self, vals):
        request = self.env['custom_supply.supply_request'].browse(vals.get('request_id'))
        user = self.env.user

        # ==========================
        # 1️⃣ التحقق من حالة الطلب
        # ==========================
        if request and request.status not in ('InBranch', 'Supply'):
            raise UserError("You cannot add new lines when the request is not in 'InBranch' or 'Supply' status.")

        # ==========================
        # 2️⃣ التحقق من صلاحيات المستخدم
        # ==========================
        if request:
            if request.status == 'InBranch' and not user.has_group('custom_supply.group_branch_employee'):
                raise UserError("Only Branch Employee can add lines in 'InBranch' status.")
            if request.status == 'Supply' and not user.has_group('custom_supply.group_supply_manager'):
                raise UserError("Only Supply Manager can add lines in 'Supply' status.")

        # ==========================
        # 3️⃣ التحقق من صلاحية المنتج للفرع
        # ==========================
        product_id = vals.get('product_id')
        branch_product_id = vals.get('branch_product_id')

        if request and product_id:
            bp = self.env['custom_supply.branch_product'].search([
                ('branch_id', '=', request.branch_id.id),
                ('product_id', '=', product_id)
            ], limit=1)

            if not bp:
                raise UserError(f"Cannot add product not defined in branch '{request.branch_id.name}'")

            if not bp.activate:
                raise UserError(f"Product '{bp.product_id.name}' is disabled in branch '{request.branch_id.name}' and cannot be added.")

            if not branch_product_id:
                vals['branch_product_id'] = bp.id

        # ==========================
        # 4️⃣ ملء current_qty تلقائياً
        # ==========================
        primitive = self.PRIMITIVE_CURRENT_QTY
        current_qty_val = vals.get('current_qty')

        if current_qty_val is None:
            # لم يدخل المستخدم أي قيمة → ضع القيمة البدائية
            if request and product_id:
                bp = self.env['custom_supply.branch_product'].search([
                    ('branch_id', '=', request.branch_id.id),
                    ('product_id', '=', product_id)
                ], limit=1)
                vals['current_qty'] = bp.current_quantity if bp else primitive
            else:
                vals['current_qty'] = primitive
        else:
            # إذا أدخل المستخدم قيمة سالبة → حولها للقيمة البدائية
            if current_qty_val < 0:
                vals['current_qty'] = primitive

        # ==========================
        # 5️⃣ ملء unit_name مرة واحدة
        # ==========================
        if product_id:
            product = self.env['product.product'].browse(product_id)
            vals['unit_name'] = product.product_tmpl_id.supply_unit_id.name if product.product_tmpl_id.supply_unit_id else ''

        # ==========================
        # 6️⃣ منع الإنشاء من Order Tracking
        # ==========================
        if self.env.context.get('from_order_tracking'):
            raise UserError("Cannot create request lines from Order Tracking (read-only).")

        # ==========================
        #  7️⃣ ضمان عدم وجود قيم فارغة
        # ==========================
        vals.setdefault('current_qty', primitive)
        vals.setdefault('requested_qty', 0.0)

        # ==========================
        #  8️⃣ إنشاء السطر
        # ==========================
        line = super(SupplyRequestLine, self).create(vals)

        # ==========================
        # 🔹 ترتيب جميع الأسطر بعد الإضافة
        # ==========================
        if request:
            # استرجاع كل الأسطر بعد الإنشاء، وترتيبها بدون الكتابة مباشرة على line_ids
            sorted_lines = request.line_ids.sorted(
                key=lambda l: (
                    l.product_id.categ_id.id if l.product_id else 0,
                    l.product_id.name if l.product_id else ''
                )
            )
            # استخدام write بدلاً من إعادة assignment مباشر
            if sorted_lines.ids != request.line_ids.ids:
                request.write({'line_ids': [(6, 0, sorted_lines.ids)]})

        return line

    # ==============================================================
    # Unlink logging
    # ==============================================================

    def unlink(self):
        _logger = logging.getLogger(__name__)
        for rec in self:
            _logger.warning(
                "Attempting to unlink supply_request_line id=%s by user=%s (uid=%s). Stack:\n%s",
                rec.id, self.env.user.name, self.env.uid,
                ''.join(traceback.format_stack())
            )
        return super(SupplyRequestLine, self).unlink()

    # ==============================================================
    # WRITE rules (نهائية)
    # ==============================================================
    def write(self, vals):
        """Write method simplified:
        - No backend field-level restriction for Supply Manager.
        - Branch Employee and Warehouse Employee restrictions remain.
        - Supply Manager can write any fields; front-end will handle allowed fields.
        """
        user = self.env.user

        for rec in self:
            request = rec.request_id
            status = request.status

            if status == 'Done':
                raise UserError("You cannot modify lines after done.")

            # Branch Employee restrictions
            if user.has_group('custom_supply.group_branch_employee'):
                if status not in ['InBranch', 'OnRoad']:
                    raise UserError("Branch Employee can only modify lines in 'InBranch or OnRoad'.")

            # Warehouse Employee restrictions
            if user.has_group('custom_supply.group_warehouse_employee'):
                if status == 'InWarehouse':
                    allowed_fields = ['export_qty', 'warehouse_note']
                    for field, value in vals.items():
                        if field not in allowed_fields and hasattr(rec, field):
                            current_value = getattr(rec, field)
                            field_type = rec._fields[field].type
                            # تحويل النوع قبل المقارنة
                            if field_type in ['float', 'monetary']:
                                current_value = float(current_value or 0.0)
                                value = float(value or 0.0)
                            elif field_type == 'integer':
                                current_value = int(current_value or 0)
                                value = int(value or 0)
                            elif field_type == 'boolean':
                                current_value = bool(current_value)
                                value = bool(value)
                            if current_value != value:
                                raise UserError(f"Warehouse Employee can only modify: {allowed_fields}")
                else:
                    raise UserError("Warehouse Employee cannot modify lines in this status.")

        if self.env.context.get('from_order_tracking'):
            raise UserError("Cannot modify lines from Order Tracking (read-only).")

        return super().write(vals)