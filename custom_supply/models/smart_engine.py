# -*- coding: utf-8 -*-
import math
from collections import deque

from odoo import models, api, fields


class SmartEngine(models.Model):
    _name = "custom_supply.smart_engine"
    _description = "Smart Suggestion Engine (learn from supply_qty + current_qty history)"
    _transient = True

    @api.model
    def _fetch_history_lines(self, branch_product, last_n=10):
        if not branch_product:
            return self.env['custom_supply.supply_request_line']

        SupplyLine = self.env['custom_supply.supply_request_line']
        domain = [
            ('branch_product_id', '=', branch_product.id),
            ('supply_qty', '!=', False),
        ]
        lines = SupplyLine.search(domain, limit=last_n * 5)  # زيادة المؤقتة قبل الفرز

        # ترتيب بالبايثون حسب request_date و create_date
        lines_sorted = sorted(
            lines,
            key=lambda l: (
                l.request_id.request_date if l.request_id else fields.Date.today(),
                l.create_date or fields.Datetime.now()
            )
        )

        # إرجاع آخر n أسطر بعد الفرز (الأقدم → الأحدث)
        return list(lines_sorted[-last_n:])

    @api.model
    def _median(self, values):
        """Return median of list."""
        if not values:
            return 0.0
        s = sorted(values)
        n = len(s)
        mid = n // 2
        if n % 2 == 0:
            return (s[mid - 1] + s[mid]) / 2.0
        else:
            return s[mid]

    @api.model
    def _compute_basic_stats(self, values):
        """
        Compute mean, std, trend, count.
        Trend = newest - previous
        """
        n = len(values)
        if n == 0:
            return {'count': 0, 'mean': 0.0, 'std': 0.0, 'trend': 0.0}

        mean = self._median(values)

        if n > 1:
            variance = sum((v - mean) ** 2 for v in values) / n
            std = math.sqrt(variance)
            trend = values[-1] - values[-2]
        else:
            std = 0.0
            trend = 0.0

        return {'count': n, 'mean': mean, 'std': std, 'trend': trend}

    @api.model
    def _weighted_recent_average(self, values, decay=0.75):
        """
        Compute weighted average favoring recent values.
        values: chronological oldest->newest
        """
        if not values:
            return 0.0
        weights = []
        w = 1.0
        for _ in reversed(values):
            weights.append(w)
            w *= decay
        weights = list(reversed(weights))
        total = sum(weights)
        if total == 0:
            return sum(values) / len(values)
        return sum(v * wt for v, wt in zip(values, weights)) / total

    @api.model
    def compute_ideal_and_suggestion(self, branch_product, current_qty=None, last_n=10, min_history=5):
        """
        Compute suggested supply quantity based on history of approved quantities (supply_qty + current_qty).
        Ignores min/max if zero. Applies outlier handling, dynamic weights, past suggestions, and dynamic safety stock.
        """
        try:
            bp = branch_product
            if not bp:
                return {}
        except Exception:
            return {}

        cur_qty = float(current_qty) if current_qty is not None else float(getattr(bp, 'current_quantity', 0.0) or 0.0)

        # fetch history lines
        lines = self._fetch_history_lines(bp, last_n=last_n)
        values = []
        past_suggestions = []
        for l in lines:
            try:
                supply = float(l.supply_qty or 0.0)
                if supply <= 0:
                    continue

                cur_hist = float(l.current_qty or 0.0)

                # actual_qty = supply_qty + current_qty
                actual_qty = supply + cur_hist

                values.append(actual_qty)

                if l.suggested_qty_training is not None:
                    past_suggestions.append(float(l.suggested_qty_training or 0.0))

            except Exception:
                values.append(0.0)

        stats = self._compute_basic_stats(values)
        weighted = self._weighted_recent_average(values, decay=0.65) if values else 0.0

        # Integrate past suggestions into weighted average if available
        if past_suggestions:
            past_weighted = self._weighted_recent_average(past_suggestions, decay=0.65)
            weighted = 0.5 * weighted + 0.5 * past_weighted

        # fallback path: insufficient history
        if stats['count'] < int(min_history):
            max_q = float(getattr(bp, 'max_quantity', 0.0) or 0.0)
            fallback_qty = max(0.0, max_q - cur_qty) if max_q > 0 else 0.0
            return {
                'suggested_qty': float(round(fallback_qty, 3)),
                'daily_consumption': None,
                'cv': None,
                'alpha': None,
                'bias': None,
                'sensitivity': None,
                'base_ideal': None,
                'ideal_stock': None,
                'max_quantity': max_q,
                'min_required': 0.0,
                'current_quantity_used': cur_qty,
                'used_intervals': stats['count'],
                'daily_rates': [],
                'diagnostics': {
                    'count': stats['count'],
                    'mean': stats['mean'],
                    'std': stats['std'],
                    'trend': stats['trend'],
                    'weighted_recent': weighted,
                },
                'active': False,
                'method': 'fallback_insufficient_history',
            }

        # Enough data: compose suggestion
        mean = stats['mean']
        std = stats['std']
        count = stats['count']

        trend = (values[-1] - values[-3]) / 2 if count >= 3 else stats['trend']
        cv = (std / mean) if mean > 0 else 0

        # Dynamic weights based on CV
        w_recent = min(0.4, 0.2 + 0.2 * cv)
        w_mean = 1.0 - w_recent - 0.1
        w_trend = 0.1

        suggested = (w_recent * weighted) + (w_mean * mean) + (w_trend * max(trend, 0.0))

        extra = mean * 0.2 if cv > 0.4 else 0
        suggested += extra

        if count >= 3 and values[-1] > mean and values[-2] > mean and values[-3] > mean:
            suggested *= 1.1

        suggested = max(0.0, suggested)

        # --- Dynamic Safety Stock calculation ---
        z_value = 1.65  # 95% confidence
        safety_stock = z_value * std
        min_req = max(0.0, safety_stock - cur_qty)

        # Apply soft cap only if max_quantity >0
        max_q = float(getattr(bp, 'max_quantity', 0.0) or 0.0)
        soft_cap = max_q * 1.5 if max_q > 0 else None
        if soft_cap is not None:
            suggested = min(suggested, soft_cap)

        # Ensure suggested is at least safety stock
        suggested = max(suggested, min_req)
        suggested_qty = float(round(suggested))

        diagnostics = {
            'count': count,
            'mean': mean,
            'std': std,
            'trend': trend,
            'weighted_recent': weighted,
        }

        return {
            'suggested_qty': suggested_qty,
            'daily_consumption': None,
            'cv': cv,
            'alpha': None,
            'bias': None,
            'sensitivity': None,
            'base_ideal': None,
            'ideal_stock': None,
            'max_quantity': max_q,
            'min_required': min_req,
            'current_quantity_used': cur_qty,
            'used_intervals': count,
            'daily_rates': values,
            'diagnostics': diagnostics,
            'active': True,
            'method': 'history_weighted_recent_mean_trend_with_safety_stock',
        }