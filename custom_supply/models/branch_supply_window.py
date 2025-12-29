# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, datetime, time, timedelta
import pytz

def get_date_for_weekday(weekday, week_offset=0):
    """
    week_offset=0 for current week, 1 for next week, etc.
    weekday: 0=Monday ... 6=Sunday
    """
    today = date.today()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    return monday + timedelta(days=weekday)

class BranchSupplyWindow(models.Model):
    _name = "custom_supply.branch_supply_window"
    _description = "Weekly Supply Window For Branch"

    branch_id = fields.Many2one(
        "custom_supply.branch", string="Branch", required=True, ondelete="cascade"
    )
    supply_day_id = fields.Many2one("custom_supply.supply_day", string="Day", required=True)
    start_time = fields.Float(string="Start Time")
    end_time = fields.Float(string="End Time")

    start_datetime = fields.Datetime(compute="_compute_start_datetime", store=True)
    end_datetime = fields.Datetime(compute="_compute_end_datetime", store=True)

    name = fields.Char(compute="_compute_name", store=True)
    color = fields.Integer(related="branch_id.color", store=True)

    start_datetime_display = fields.Datetime(string="Start for Calendar", compute="_compute_display_datetime", store=True)
    end_datetime_display = fields.Datetime(string="End for Calendar",compute="_compute_display_datetime",store=True)

    @api.depends("start_datetime", "end_datetime")
    def _compute_display_datetime(self):
        # جلب فرق التوقيت ديناميكياً
        user_tz = self.env.user.tz or 'UTC'
        local_tz = pytz.timezone(user_tz)
        now_utc = datetime.utcnow().replace(tzinfo=pytz.UTC)
        now_local = now_utc.astimezone(local_tz)
        tz_offset_hours = (now_local - now_utc).total_seconds() / 3600

        for rec in self:
            if rec.start_datetime:
                # نطرح الفرق بين UTC و TimeZone المستخدم + 3 ساعات
                rec.start_datetime_display = rec.start_datetime - timedelta(hours=tz_offset_hours + 3)
            else:
                rec.start_datetime_display = False

            if rec.end_datetime:
                rec.end_datetime_display = rec.end_datetime - timedelta(hours=tz_offset_hours + 3)
            else:
                rec.end_datetime_display = False

    @api.onchange("branch_id")
    def _onchange_branch_id_color(self):
        if self.branch_id:
            self.color = self.branch_id.color

    @api.depends("branch_id")
    def _compute_name(self):
        for rec in self:
            rec.name = rec.branch_id.name if rec.branch_id else "Unknown Branch"

    # ==============================
    # COMPUTE DATETIMES (UTC only)
    # ==============================
    @api.depends("start_time", "supply_day_id")
    def _compute_start_datetime(self):
        for rec in self:
            if rec.supply_day_id:
                base_date = get_date_for_weekday(rec.supply_day_id.day_of_week)
                h = int(rec.start_time)
                m = int((rec.start_time - h) * 60)
                naive_dt = datetime.combine(base_date, time(h, m))
                # خزّن بدون أي تحويل، Odoo سيحوّل تلقائياً للـ Calendar حسب TZ المستخدم
                rec.start_datetime = fields.Datetime.to_string(naive_dt)
            else:
                rec.start_datetime = False

    @api.depends("end_time", "supply_day_id")
    def _compute_end_datetime(self):
        for rec in self:
            if rec.supply_day_id:
                base_date = get_date_for_weekday(rec.supply_day_id.day_of_week)
                h = int(rec.end_time)
                m = int((rec.end_time - h) * 60)
                naive_dt = datetime.combine(base_date, time(h, m))
                rec.end_datetime = fields.Datetime.to_string(naive_dt)
            else:
                rec.end_datetime = False

    # ==============================
    # VALIDATION
    # ==============================
    @api.constrains('start_time', 'end_time')
    def _check_time_valid(self):
        for rec in self:
            if rec.start_time >= rec.end_time:
                raise ValidationError("Start Time must be less than End Time.")
            if not (0 <= rec.start_time < 24) or not (0 < rec.end_time <= 24):
                raise ValidationError("Time must be between 0 and 24 hours.")
