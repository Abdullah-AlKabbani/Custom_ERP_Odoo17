# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    branch_id = fields.Many2one(
        'custom_supply.branch',
        string="Branch",
        compute='_compute_branch_id',
        inverse='_inverse_branch_id',
    )

    # ==============================
    # COMPUTE
    # ==============================
    def _compute_branch_id(self):
        """ربط المستخدم بالفرع الذي يحتويه في user_id"""
        Branch = self.env['custom_supply.branch'].sudo()
        for user in self:
            branch = Branch.search([('user_id', '=', user.id)], limit=1)
            user.branch_id = branch if branch else False

    # ==============================
    # INVERSE
    # ==============================
    def _inverse_branch_id(self):
        """تحديث الفرع عندما يتم تغيير branch_id من جهة المستخدم"""
        for user in self:
            if user.branch_id:
                # تأكد من إزالة أي مستخدم قديم لهذا الفرع
                if user.branch_id.user_id and user.branch_id.user_id.id != user.id:
                    user.branch_id.user_id = False
                user.branch_id.sudo().user_id = user
            else:
                # إزالة العلاقة إن لم يعد هناك فرع
                branches = self.env['custom_supply.branch'].sudo().search([('user_id', '=', user.id)])
                if branches:
                    branches.user_id = False


    # ==============================
    # CREATE
    # ==============================
    @api.model
    def create(self, vals):
        # إنشاء المستخدم أولاً
        user = super(ResUsers, self).create(vals)

        # الحصول على مجموعة الـ Viewer
        group_viewer = self.env.ref('company_branch.group_branch_viewer')

        # إضافة المستخدم للمجموعة تلقائيًا إذا لم يكن موجودًا
        if group_viewer and user.id not in group_viewer.users.ids:
            group_viewer.sudo().users = [(4, user.id)]

        return user
