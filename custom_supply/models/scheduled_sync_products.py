# custom_supply/models/scheduled_sync_products.py
import pymssql
import logging
from odoo import models, fields, api
from datetime import datetime

_logger = logging.getLogger(__name__)

class ProductSyncScheduler(models.Model):
    _name = "product.sync.scheduler"
    _description = "Scheduled sync with external SQL Server database"

    last_sync = fields.Datetime(string="Last Sync Time")

    @api.model
    def sync_products_from_sqlserver(self):
        """Connect to SQL Server and import products/categories if not exist."""
        SERVER = "192.168.2.238"
        DATABASE = "Shami2025"
        USER = "userapp"
        PASSWORD = "Userapp@1924"

        try:
            conn = pymssql.connect(
                server=SERVER,
                user=USER,
                password=PASSWORD,
                database=DATABASE,
                login_timeout=10
            )
            cursor = conn.cursor(as_dict=True)
            cursor.execute("SELECT ProductName, GroupName FROM View_Mat")
            rows = cursor.fetchall()
        except Exception as e:
            raise Exception(f"❌ فشل الاتصال بقاعدة SQL Server: {e}")

        Product = self.env["product.product"]
        Category = self.env["product.category"]

        created_products = 0
        created_categories = 0

        for row in rows:
            product_name = row.get("ProductName", "").strip()
            group_name = row.get("GroupName", "Uncategorized").strip()

            if not product_name:
                continue

            # البحث عن الفئة أو إنشاؤها
            category = Category.search([("name", "=", group_name)], limit=1)
            if not category:
                category = Category.create({"name": group_name})
                created_categories += 1

            # البحث عن المنتج أو إنشاؤه
            product = Product.search([("name", "=", product_name)], limit=1)
            if not product:
                Product.create({
                    "name": product_name,
                    "categ_id": category.id,
                })
                created_products += 1

        conn.close()

        # تحديث وقت آخر مزامنة
        existing = self.search([], limit=1)
        if existing:
            existing.write({"last_sync": datetime.now()})
        else:
            self.create({"last_sync": datetime.now()})

        # تسجيل في سجل Odoo
        _logger.info("✅ تمت مزامنة %s منتج و %s فئة من SQL Server.", created_products, created_categories)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sync Completed ✅',
                'message': f'تمت مزامنة {created_products} منتج و {created_categories} فئة بنجاح من SQL Server.',
                'type': 'success',
                'sticky': False,
            }
        }