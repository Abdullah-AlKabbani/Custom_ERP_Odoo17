# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import models, fields, api, tools
from odoo.exceptions import UserError
from lxml import etree
import logging

_logger = logging.getLogger(__name__)

LATE_DELAY = timedelta(hours=24)

class SupplyRequest(models.Model):
    _name = "custom_supply.supply_request"
    _description = "Supply Request from Branch"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    # ============================
    # Fields
    # ============================
    name = fields.Char(string="Request Number", required=True, copy=False, readonly=True, default='New')
    request_date = fields.Datetime( string="Request Date", readonly=True, default=fields.Datetime.now)
    branch_id = fields.Many2one('custom_supply.branch',string="Branch",required=True,default=lambda self: self._default_branch())
    status = fields.Selection([
        ('InBranch', 'In Branch'),
        ('Supply', 'In Supply'),
        ('InWarehouse', 'In Warehouse'),
        ('OnRoad', 'On Road'),
        ('Done', 'Done')
    ], string="Status", default='InBranch', tracking=True, group_expand='_group_expand_status')

    line_ids = fields.One2many('custom_supply.supply_request_line','request_id',string="Request Lines")
    supply_manager_id = fields.Many2one('res.users', string="Supply Manager", readonly=True)
    warehouse_user_id = fields.Many2one('res.users', string="Warehouse User", readonly=True)
    received_user_id = fields.Many2one('res.users', string="Received By", readonly=True)
    supply_confirm_date = fields.Datetime("Supply Confirmed On", readonly=True)
    warehouse_export_date = fields.Datetime("Exported On", readonly=True)
    received_date = fields.Datetime(string="Received On", readonly=True)

    late_icon_display = fields.Char(string="Late Icon Display",compute="_compute_late_status",store=True,readonly = True)

    late_supply = fields.Boolean(store=True)
    late_warehouse = fields.Boolean(store=True)
    late_overall = fields.Boolean(store=True)
    late_delivery = fields.Boolean(compute="_compute_late_status", store=True)

    last_supply_late_notify = fields.Datetime(string="Last Supply Notification")
    last_warehouse_late_notify = fields.Datetime(string="Last Warehouse Notification")
    delivery_late_notified = fields.Boolean(string="Delivery Late Notified", default=False)
    expected_delivery_date = fields.Datetime(string="Expected Delivery Date",compute="_compute_expected_delivery_date",store=True)

    # ============================
    # Expected Delivery Date
    # ============================
    @api.depends('branch_id', 'request_date')
    def _compute_expected_delivery_date(self):
        now = fields.Datetime.now()
        for rec in self:
            rec.expected_delivery_date = False
            if not rec.branch_id:
                continue

            # جلب كل النوافذ للفرع الحالي
            windows = self.env['custom_supply.branch_supply_window'].search([
                ('branch_id', '=', rec.branch_id.id)
            ])

            # تحويل start_datetime_display إلى datetime object
            future_windows = []
            for w in windows:
                if w.start_datetime_display:
                    dt = fields.Datetime.from_string(w.start_datetime_display)
                    if dt >= now:
                        future_windows.append((dt, w.end_datetime_display))

            if future_windows:
                # اختيار أول نافذة مستقبلية
                future_windows.sort(key=lambda x: x[0])
                rec.expected_delivery_date = future_windows[0][0]

    # ============================
    # Compute Late Status
    # ============================
    @api.depends('request_date','supply_confirm_date','warehouse_export_date','received_date','status')
    def _compute_late_status(self):
        now = fields.Datetime.now()

        for rec in self:
            late_supply = False
            late_warehouse = False
            late_delivery = False

            # ----------------------------------------
            # 1️⃣ Late Supply
            # ----------------------------------------
            if rec.request_date:
                if rec.supply_confirm_date:
                    if rec.supply_confirm_date - rec.request_date >= LATE_DELAY:
                        late_supply = True
                else:
                    if now - rec.request_date >= LATE_DELAY:
                        late_supply = True

            # ----------------------------------------
            # 2️⃣ Late Warehouse
            # ----------------------------------------
            if rec.supply_confirm_date:
                if rec.warehouse_export_date:
                    if rec.warehouse_export_date - rec.supply_confirm_date >= LATE_DELAY:
                        late_warehouse = True
                else:
                    if now - rec.supply_confirm_date >= LATE_DELAY:
                        late_warehouse = True

            # ----------------------------------------
            # 3️⃣ Late Delivery (Day + Time Window)
            # ----------------------------------------
            if rec.status in ['OnRoad', 'Done'] and rec.warehouse_export_date and rec.received_date:

                received_weekday = rec.received_date.weekday()

                windows = self.env['custom_supply.branch_supply_window'].search([
                    ('branch_id', '=', rec.branch_id.id)
                ])

                allowed_days = windows.mapped('supply_day_id.day_of_week')

                if received_weekday not in allowed_days:
                    late_delivery = True
                else:
                    todays_windows = windows.filtered(
                        lambda w: w.supply_day_id.day_of_week == received_weekday
                    )
                    match = todays_windows.filtered(
                        lambda w: w.start_datetime_display <= rec.received_date <= w.end_datetime_display
                    )
                    if not match:
                        late_delivery = True


            # ----------------------------------------
            # 4️⃣ Build Icons
            # ----------------------------------------
            icons = ""
            if late_supply:
                icons += "🔴"
            if late_warehouse:
                icons += "🟡"
            if late_delivery:
                icons += "🚚"

            if not icons:
                icons = "🟢"

            # ----------------------------------------
            # 5️⃣ Apply updates dynamically
            # ----------------------------------------
            rec.with_context(bypass_order_tracking_check=True).update({
                'late_supply': late_supply,
                'late_warehouse': late_warehouse,
                'late_delivery': late_delivery,
                'late_overall': late_supply or late_warehouse or late_delivery,
                'late_icon_display': icons,
            })

    @api.model
    def cron_check_late_requests(self):
        """
        Cron job that sends late notifications for:
        1) Supply delay
        2) Warehouse delay
        3) Delivery delay
        With extensive debug logging.
        """

        _logger.warning("===== CRON START: cron_check_late_requests =====")

        now = fields.Datetime.now()
        delay = LATE_DELAY
        db_name = self._cr.dbname

        _logger.warning(f"[CRON] Current time: {now}, Delay threshold: {delay}")

        # Special safe context for cron
        cron_ctx = {
            "skip_branch_filter": True,
            "bypass_order_tracking_check": True,
            "mail_create_nolog": True,
            "mail_notrack": True,
            "tracking_disable": True,
        }

        # ============================================================
        # 1) SUPPLY LATE
        # ============================================================
        _logger.warning("----- Checking SUPPLY late requests -----")

        supply_recs = self.with_context(cron_ctx).search([('status', '=', 'Supply')])
        _logger.warning(f"[SUPPLY] Found {len(supply_recs)} records in Supply status.")

        for rec in supply_recs:

            _logger.warning(f"[SUPPLY] Checking record {rec.id} ({rec.name})")

            if not rec.request_date:
                _logger.warning(f"[SUPPLY] Missing request_date → skipping record {rec.id}")
                continue

            late = (now - rec.request_date) >= delay
            _logger.warning(f"[SUPPLY] now - request_date = {now - rec.request_date}, late={late}")

            if late and not rec.supply_confirm_date:
                last = rec.last_supply_late_notify
                must_notify = (not last) or ((now - last) >= delay)

                _logger.warning(
                    f"[SUPPLY] late={late}, last_notify={last}, must_notify={must_notify}"
                )

                if must_notify:
                    try:
                        _logger.warning(f"[SUPPLY] Posting chatter message for {rec.id}")
                        rec.with_context(cron_ctx).message_post(
                            body=f"⚠️ Supply Request {rec.name} from {rec.branch_id.name} is late in Supply Dept."
                        )

                        rec.with_context(cron_ctx).write({
                            "last_supply_late_notify": now
                        })

                        _logger.warning(f"[SUPPLY] Notification SENT + last_notify updated.")

                    except Exception as e:
                        _logger.error(f"[SUPPLY] FAILED to send notification: {e}")

        # ============================================================
        # 2) WAREHOUSE LATE
        # ============================================================
        _logger.warning("----- Checking WAREHOUSE late requests -----")

        warehouse_recs = self.with_context(cron_ctx).search([
            ('status', '=', 'InWarehouse'),
            ('supply_confirm_date', '<=', now - delay),
            ('warehouse_export_date', '=', False),
        ])

        _logger.warning(f"[WAREHOUSE] Found {len(warehouse_recs)} records.")

        for rec in warehouse_recs:

            _logger.warning(f"[WAREHOUSE] Checking record {rec.id} ({rec.name})")

            last = rec.last_warehouse_late_notify
            must_notify = (not last) or ((now - last) >= delay)

            _logger.warning(
                f"[WAREHOUSE] last_notify={last}, must_notify={must_notify}"
            )

            if must_notify:

                message = (
                    f"Supply Request {rec.name} from {rec.branch_id.name} is late "
                    f"in the Warehouse Department."
                )

                try:
                    _logger.warning(f"[WAREHOUSE] Posting chatter message...")

                    rec.with_context(cron_ctx).message_post(body=f"⚠️ {message}")

                    if rec.warehouse_user_id:
                        _logger.warning(f"[WAREHOUSE] Scheduling activity → user {rec.warehouse_user_id.id}")
                        rec.activity_schedule(
                            'mail.activity_data_warning',
                            user_id=rec.warehouse_user_id.id,
                            summary=message,
                            note="Request delayed in warehouse beyond allowed threshold.",
                        )

                        _logger.warning("[WAREHOUSE] Sending BUS notification...")
                        self.env['bus.bus'].sendmany(
                            (db_name, 'custom_supply_notification'),
                            {
                                'partner_id': rec.warehouse_user_id.partner_id.id,
                                'title': 'Late Warehouse Request',
                                'message': message,
                            }
                        )

                    rec.with_context(cron_ctx).write({
                        "last_warehouse_late_notify": now
                    })

                    _logger.warning(f"[WAREHOUSE] Notification SENT + last_notify updated.")

                except Exception as e:
                    _logger.error(f"[WAREHOUSE] FAILED to send notification: {e}")

        _logger.warning("===== CRON END: cron_check_late_requests =====")

    # ============================
    # _group_expand_status
    # ============================
    def _group_expand_status(self, status, domain, order):
        #desired_order = ['InBranch', 'Supply', 'InWarehouse', 'OnRoad', 'Done']
        desired_order = ['Done', 'OnRoad', 'InWarehouse', 'Supply', 'InBranch']
        return desired_order

    # ============================
    # DEFAULT branch helper
    # ============================
    @api.model
    def _default_branch(self):
        user = self.env.user
        if getattr(user, 'branch_id', False):
            return user.branch_id.id
        branch = self.env['custom_supply.branch'].search([('user_id', '=', user.id)], limit=1)
        return branch.id if branch else False

    # ============================
    # Default_get
    # ============================
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'name' in fields_list and (res.get('name') in (False, 'New')):
            seq_code = 'custom_supply.supply_request'
            try:
                res['name'] = self.env['ir.sequence'].next_by_code(seq_code) or 'New'
            except Exception as e:
                _logger.exception("Failed to generate sequence in default_get: %s", e)
                res['name'] = 'New'
        if 'branch_id' in fields_list and not res.get('branch_id'):
            branch_id = self._default_branch()
            if branch_id:
                res['branch_id'] = branch_id
        return res

    # ============================
    # Create
    # ============================
    @api.model_create_multi
    def create(self, vals_list):
        seq_code = 'custom_supply.supply_request'
        seq = self.env['ir.sequence'].search([('code', '=', seq_code)], limit=1)
        if not seq:
            try:
                seq = self.env['ir.sequence'].create({
                    'name': 'Supply Request',
                    'code': seq_code,
                    'prefix': 'SR',
                    'padding': 4,
                    'implementation': 'standard',
                })
            except Exception as e:
                _logger.exception("Failed to create sequence: %s", e)
                seq = False

        current_user = self.env.user
        user_branch = getattr(current_user, 'branch_id', False)

        for vals in vals_list:
            if vals.get('name', 'New') in ('New', False):
                try:
                    vals['name'] = self.env['ir.sequence'].next_by_code(seq_code) or 'New'
                except Exception as e:
                    _logger.exception("Failed to generate sequence number: %s", e)
                    vals['name'] = 'New'
            if not vals.get('branch_id') and user_branch:
                vals['branch_id'] = user_branch.id
            if not vals.get('request_date'):
                vals['request_date'] = fields.Datetime.now()

        requests = super().create(vals_list)

        for request in requests:
            try:
                if not request.line_ids and request.branch_id:
                    request._fill_basic_products_lines()
                request.message_post(
                    body=f"Supply Request '{request.name}' created for branch '{request.branch_id.name if request.branch_id else 'N/A'}'."
                )
            except Exception as e:
                _logger.exception("Post-create process failed: %s", e)

        return requests

    # ============================
    # Onchange branch
    # ============================
    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        if not self.branch_id:
            self.line_ids = [(5, 0, 0)]
            return
        if not self.line_ids:
            self._fill_basic_products_lines()

    # ============================
    # Fill basic product lines
    # ============================
    def _fill_basic_products_lines(self):
        self.ensure_one()
        try:
            # جلب منتجات الفرع
            branch_products = getattr(self.branch_id, 'product_ids', False) or \
                              self.env['custom_supply.branch_product'].search([('branch_id', '=', self.branch_id.id)])
            if not branch_products:
                return

            # تصفية المنتجات الأساسية
            filtered_bps = branch_products.filtered(
                lambda bp: bp.product_id and getattr(bp.product_id.product_tmpl_id, 'custom_supply_field_1', '') == 'basic'
            )

            lines = []
            product_ids = [bp.product_id.id for bp in filtered_bps]
            products = self.env['product.product'].browse(product_ids)
            product_map = {p.id: p for p in products}

            for bp in filtered_bps:
                prod = product_map.get(bp.product_id.id)
                lines.append((0, 0, {
                    'product_id': bp.product_id.id,
                    'current_qty': float(bp.current_quantity or -1.0),
                    'suggested_qty': getattr(bp, 'max_quantity', 0.0) or 0.0,
                    'requested_qty': 0.0,
                    'branch_product_id': bp.id,
                    'unit_name': prod.product_tmpl_id.supply_unit_id.name if prod and prod.product_tmpl_id.supply_unit_id else '',
                }))

            # ترتيب الأسطر حسب Category → Name
            lines_sorted = sorted(
                lines,
                key=lambda x: (
                    product_map.get(x[2]['product_id']).categ_id.id if x[2]['product_id'] else 0,
                    product_map.get(x[2]['product_id']).name if x[2]['product_id'] else ''
                )
            )

            self.line_ids = lines_sorted

        except Exception as e:
            _logger.exception("Failed to fill basic products lines: %s", e)


    # ================================================================
    # Smart
    # ================================================================
    # def _fill_basic_products_lines(self):
    #     self.ensure_one()
    #     try:
    #         # جلب منتجات الفرع
    #         branch_products = getattr(self.branch_id, 'product_ids', False) or \
    #                           self.env['custom_supply.branch_product'].search([('branch_id', '=', self.branch_id.id)])
    #         if not branch_products:
    #             return
    #
    #         # تصفية المنتجات الأساسية
    #         filtered_bps = branch_products.filtered(
    #             lambda bp: bp.product_id and getattr(bp.product_id.product_tmpl_id, 'custom_supply_field_1',
    #                                                  '') == 'basic'
    #         )
    #
    #         if not filtered_bps:
    #             return
    #
    #         lines = []
    #         product_ids = [bp.product_id.id for bp in filtered_bps]
    #         products = self.env['product.product'].browse(product_ids)
    #         product_map = {p.id: p for p in products}
    #
    #         # استدعاء SmartEngine مرة واحدة
    #         engine = self.env['custom_supply.smart_engine']
    #
    #         for bp in filtered_bps:
    #             prod = product_map.get(bp.product_id.id)
    #
    #             # استدعاء SmartEngine للحصول على الاقتراح الذكي
    #             result = engine.compute_ideal_and_suggestion(
    #                 branch_product=bp,
    #                 current_qty=float(bp.current_quantity or 0.0),
    #                 last_n=10,
    #                 min_history=5
    #             )
    #
    #             engine_value = float(result.get('suggested_qty', 0.0) or 0.0)
    #             final_suggestion = max(0.0, engine_value - float(bp.current_quantity or 0.0))
    #
    #             lines.append((0, 0, {
    #                 'product_id': bp.product_id.id,
    #                 'current_qty': float(bp.current_quantity or 0.0),
    #                 'suggested_qty_training': engine_value,
    #                 'suggested_qty': final_suggestion,
    #                 'requested_qty': 0.0,
    #                 'branch_product_id': bp.id,
    #                 'unit_name': prod.product_tmpl_id.supply_unit_id.name if prod and prod.product_tmpl_id.supply_unit_id else '',
    #             }))
    #
    #         # ترتيب الأسطر حسب Category → Name
    #         lines_sorted = sorted(
    #             lines,
    #             key=lambda x: (
    #                 product_map.get(x[2]['product_id']).categ_id.id if x[2]['product_id'] else 0,
    #                 product_map.get(x[2]['product_id']).name if x[2]['product_id'] else ''
    #             )
    #         )
    #
    #         # ملء line_ids بالأسطر الجديدة
    #         self.line_ids = lines_sorted
    #
    #     except Exception as e:
    #         _logger.exception("Failed to fill basic products lines: %s", e)


    # ============================
    # Actions
    # ============================
    def action_submit_request(self):
        for rec in self:
            _logger.info("Export START for request %s (id=%s). lines_before=%s", rec.name, rec.id, len(rec.line_ids))
            if self.env.context.get('from_order_tracking'):
                raise UserError("This action is disabled in Order Tracking view.")

            if rec.status != 'InBranch':
                continue

            if rec.status == 'InBranch':
                for line in rec.line_ids:
                    line._compute_suggested_qty()
                    line.supply_qty = line.suggested_qty or 0.0

            if not self.env.user.has_group('custom_supply.group_branch_employee'):
                raise UserError("Only Branch Employee can submit this request.")
            if not rec.line_ids:
                raise UserError("Cannot submit an empty request. Please add products before submitting.")

            # تغيير الحالة باستخدام write مع context
            rec.with_context(allow_status_change=True).write({'status': 'Supply'})
            rec.message_post(body=f"Supply Request '{rec.name}' submitted by {self.env.user.name}.")
            _logger.info("Export END for request %s (id=%s). lines_after=%s", rec.name, rec.id, len(rec.line_ids))
        return True

    def action_mark_in_warehouse(self):
        for rec in self:
            if self.env.context.get('from_order_tracking'):
                raise UserError("This action is disabled in Order Tracking view.")

            if rec.status != 'Supply':
                continue

            if not self.env.user.has_group('custom_supply.group_supply_manager'):
                raise UserError("Only Supply Manager can confirm this stage.")

            # ============================================================
            # 1️⃣ تنظيف القيم قبل الانتقال للمرحلة التالية
            # ============================================================
            for line in rec.line_ids:
                if line._origin.id is False:
                    line.current_qty = self.PRIMITIVE_CURRENT_QTY
                elif line.current_qty is None:
                    line.current_qty = self.PRIMITIVE_CURRENT_QTY

                if line._origin.id is False:
                    line.requested_qty = 0.0
                elif line.requested_qty is None:
                    line.requested_qty = 0.0

                if line.supply_qty is None:
                    line.supply_qty = line.suggested_qty or 0.0

            # ============================================================
            # 2️⃣ حذف الأسطر المهملة
            #     الشروط: current_qty = -1 AND supply_qty = 0
            # ============================================================
            lines_to_delete = rec.line_ids.filtered(
                lambda l: l.supply_qty == 0 or l.supply_qty is False
            )
            if lines_to_delete:
                lines_to_delete.unlink()

            # ============================================================
            # 3️⃣ متابعة العملية المعتادة
            # ============================================================
            rec.with_context(allow_status_change=True).write({'status': 'InWarehouse'})
            rec.supply_manager_id = self.env.user.id
            rec.supply_confirm_date = fields.Datetime.now()

            rec.message_post(
                body=f"Supply Request '{rec.name}' sent to Warehouse by {self.env.user.name}."
            )

        return True

    def action_export(self):
        # SmartEngine = self.env['custom_supply.smart_engine']
        #
        # for request in self:
        #     for line in request.line_ids:
        #
        #         # إيجاد branch_product
        #         branch_product = self.env['custom_supply.branch_product'].search([
        #             ('branch_id', '=', request.branch_id.id),
        #             ('product_id', '=', line.product_id.id)
        #         ], limit=1)
        #
        #         if not branch_product:
        #             continue
        #
        #         # استدعاء المحرك للحصول على min_required
        #         try:
        #             result = SmartEngine.compute_ideal_and_suggestion(
        #                 branch_product=branch_product,
        #                 current_qty=branch_product.current_quantity,
        #                 last_n=10,
        #                 min_history=5
        #             )
        #
        #             new_min = result.get("min_required", 0.0)
        #
        #             # تحديث الحد الأدنى
        #             branch_product.min_quantity = new_min
        #
        #         except Exception as e:
        #             # في حال حدث خطأ لا نوقف العملية
        #             pass
        #
        # # أخيراً
        # self.write({"state": "done"})

        for rec in self:
            if self.env.context.get('from_order_tracking'):
                raise UserError("This action is disabled in Order Tracking view.")

            if rec.status != 'InWarehouse':
                continue
            if not self.env.user.has_group('custom_supply.group_warehouse_employee'):
                raise UserError("Only Warehouse Employee can export this request.")

            rec.warehouse_user_id = self.env.user.id
            rec.warehouse_export_date = fields.Datetime.now()

            # تغيير الحالة باستخدام write مع context
            rec.with_context(allow_status_change=True).write({'status': 'OnRoad'})

            rec.message_post(body=f"Supply Request '{rec.name}' exported by {self.env.user.name} and marked as On Road.")
        return True

    def action_order_received(self):
        user = self.env.user

        for rec in self:
            # --------------------------
            # Validation checks
            # --------------------------
            if self.env.context.get('from_order_tracking'):
                raise UserError("This action is disabled in Order Tracking view.")

            if rec.status != 'OnRoad':
                continue

            if not user.has_group('custom_supply.group_branch_employee'):
                raise UserError("Only Branch Employee can submit this request.")

            if not rec.line_ids:
                raise UserError("Cannot submit an empty request. Please add products before submitting.")

            if rec.branch_id != getattr(user, 'branch_id', False):
                raise UserError("You cannot receive orders for another branch.")

            # --------------------------
            # 1) Apply received info
            # --------------------------
            rec.received_user_id = user.id
            rec.received_date = fields.Datetime.now()

            # Change status
            rec.with_context(allow_status_change=True).write({'status': 'Done'})

            # Log standard message
            rec.message_post(
                body=f"Supply Request '{rec.name}' received by {user.name} and marked as Done."
            )

            # --------------------------
            # 2) Late Delivery Check (same logic as compute method)
            # --------------------------
            late_delivery = False
            received_dt = rec.received_date

            windows = rec.env['custom_supply.branch_supply_window'].search([
                ('branch_id', '=', rec.branch_id.id)
            ])

            if not windows:
                # If no defined windows: treat as late
                late_delivery = True
            else:
                received_weekday = received_dt.weekday()
                allowed_days = windows.mapped('supply_day_id.day_of_week')

                if received_weekday not in allowed_days:
                    late_delivery = True
                else:
                    todays_windows = windows.filtered(
                        lambda w: w.supply_day_id.day_of_week == received_weekday
                    )
                    match = todays_windows.filtered(
                        lambda w: w.start_datetime_display <= received_dt <= w.end_datetime_display
                    )
                    if not match:
                        late_delivery = True

            # --------------------------
            # 3) If late → send chatter notification ONCE
            # --------------------------
            if late_delivery and not rec.delivery_late_notified:

                # Build allowed windows description
                day_windows = windows.filtered(
                    lambda w: w.supply_day_id.day_of_week == received_dt.weekday()
                )

                if day_windows:
                    win_desc = ", ".join([
                        f"{w.start_datetime_display} → {w.end_datetime_display}"
                        for w in day_windows
                    ])
                else:
                    win_desc = "No allowed delivery window for this day."

                # Chatter message from System (OdooBot)
                message = (
                    f"🚚⚠️ Delivery Delay: Request {rec.name} for branch {rec.branch_id.name} "
                    f"was received at {received_dt}, which is outside the allowed window: {win_desc}."
                )


                # Get OdooBot / System user
                odoo_bot = self.env.ref('base.user_root')  # غالبًا OdooBot / System User

                # Post message as OdooBot
                rec.sudo().with_context(
                    mail_create_nosubscribe=True,
                    mail_notrack=True
                ).message_post(
                    body=message,
                    author_id=odoo_bot.id
                )

                rec.delivery_late_notified = True
            return True

    def print_warehouse_request_pdf(self):
        """
        Method to print Supply Request PDF for Warehouse Employees
        """
        return self.env.ref('custom_supply.action_report_supply_request_pdf').report_action(self)

    # ============================
    # Domains for Tabs with Roles
    # ============================
    def _domain_for_tab(self, tab, user):
        """
        Return a domain list appropriate for the given tab and user role.
        """
        if not tab:
            return []

        branch = getattr(user, 'branch_id', False)

        # Identify roles
        is_branch = user.has_group('custom_supply.group_branch_employee')
        is_supply = user.has_group('custom_supply.group_supply_manager')
        is_warehouse = user.has_group('custom_supply.group_warehouse_employee')
        is_high = user.has_group('custom_supply.group_high_manager')

        # =============== Branch Employee ==================
        if is_branch:
            if tab == 'supply_request':
                return [('branch_id', '=', branch.id if branch else 0), ('status', '=', 'InBranch')]
            elif tab == 'order_tracking':
                return [('branch_id', '=', branch.id if branch else 0), ('status', 'in', ['Supply', 'InWarehouse', 'Done'])]
            else:
                return [('id', '=', 0)]

        # =============== Supply Manager ==================
        if is_supply:
            if tab == 'supply_request':
                return [('status', '=', 'Supply')]
            elif tab == 'order_tracking':
                return [('status', 'in', ['InWarehouse', 'Done'])]
            else:
                return [('id', '=', 0)]

        # =============== Warehouse Employee ==================
        if is_warehouse:
            if tab == 'supply_request':
                return [('status', '=', 'InWarehouse')]
            elif tab == 'order_tracking':
                return [('status', '=', 'Done')]
            else:
                return [('id', '=', 0)]

        # =============== High Manager ==================
        if is_high:
            if tab == 'order_tracking':
                return [('status', 'in', ['Supply', 'InWarehouse', 'Done'])]
            else:
                return [('id', '=', 0)]

        _logger.info("_domain_for_tab called: user=%s, tab=%s", user.name, tab)
        # fallback: deny if role not matched
        return [('id', '=', 0)]

    # ============================
    # Unified Branch Filter Method
    # ============================
    def _apply_branch_filter(self, domain=None):
        domain = domain or []
        context = self._context or {}
        user = self.env.user

        if context.get("skip_branch_filter"):
            return domain

        # 🔹 إذا اليوزر Branch Employee
        if user.has_group('custom_supply.group_branch_employee'):
            branch_id = getattr(user, 'branch_id', False)
            if branch_id:
                # تطبيق الفلترة على الطلبات حسب الفرع
                domain += [('branch_id', '=', branch_id.id)]
            else:
                domain += [('id', '=', 0)]  # لا يعرض أي طلب إذا لا يوجد فرع

        return domain

    # ============================
    # Override all search/read_group methods
    # ============================
    @api.model
    def search(self, args, offset=0, limit=None, order=None):
        args = self._apply_branch_filter(args)
        return super().search(args, offset=offset, limit=limit, order=order)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain = self._apply_branch_filter(domain)
        return super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        domain = self._apply_branch_filter(domain)
        return super().search_read(domain, fields, offset=offset, limit=limit, order=order)

    @api.model
    def web_read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain = self._apply_branch_filter(domain)
        return super().web_read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    @api.model
    def web_search_read(self, count_limit=0, domain=None, limit=None, offset=0, order=None, specification=None):
        domain = self._apply_branch_filter(domain)
        return super().web_search_read(count_limit=count_limit, domain=domain, limit=limit, offset=offset, order=order, specification=specification)

    # ============================
    # fields_view_get - Optional XML domain adjustment
    # ============================
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        context = self.env.context or {}
        user = self.env.user
        if context.get("from_order_tracking") and user.has_group("custom_supply.group_branch_employee"):
            branch_id = user.branch_id.id if user.branch_id else False
            if branch_id:
                doc = etree.XML(res['arch'])
                if view_type in ('kanban', 'tree'):
                    existing_domain = doc.get("domain")
                    forced_domain = "[('branch_id','=',%d)]" % branch_id
                    if existing_domain:
                        final_domain = "[('branch_id','=',%d)] & %s" % (branch_id, existing_domain)
                    else:
                        final_domain = forced_domain
                    doc.set("domain", final_domain)
                res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    def write(self, vals):
        # Allow bypass for computed fields, chatter, and late_icon_display
        bypass = self.env.context.get('bypass_order_tracking_check', False)
        allow_status = self.env.context.get('allow_status_change', False)
        allowed_in_order_tracking = ['message_ids', 'message_follower_ids', 'activity_ids', 'late_icon_display']

        if self.env.context.get('from_order_tracking') and not bypass:
            # Ignore all computed fields that are automatically updated
            non_allowed_fields = [k for k in vals if k not in allowed_in_order_tracking]
            if non_allowed_fields:
                if all(f == 'status' for f in non_allowed_fields) and allow_status:
                    pass
                else:
                    # Instead of raising error, just log warning and skip
                    _logger.warning("Attempt to write forbidden fields from Order Tracking: %s", non_allowed_fields)
                    # Remove forbidden fields to allow write to proceed
                    for f in non_allowed_fields:
                        vals.pop(f)

        # منع تعديل status بدون allow_status
        if 'status' in vals and not allow_status:
            raise UserError("You cannot change the status of a supply request manually.")

        if self.env.context.get('from_order_tracking'):
            if 'status' in vals:
                raise UserError("You cannot change the status of a supply request manually.")

        return super().write(vals)

    def unlink(self):
        if self.env.context.get('from_order_tracking'):
            raise UserError("Cannot delete records from Order Tracking (read-only).")
        return super(SupplyRequest, self).unlink()