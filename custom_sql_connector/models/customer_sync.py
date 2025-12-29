import pyodbc
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)

class CustomerSync(models.Model):
    _name = 'customer.sync'
    _description = 'SQL Server Customer Sync'

    @api.model
    def sync_customers(self):
        # SQL Server connection details
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=192.168.100.2\\sqlexpress;"
            "DATABASE=Attar2024;"
            "UID=sa;"
            "PWD=Att@r1924;"
            "Trusted_Connection=no;"
            "MARS_Connection=yes;"
        )

        query = """SELECT
            cu.[CustomerName],
            cu.[Phone1],
            cu.[Phone2],
            cu.[Mobile],
            ac.[Code],
            cu.[CheckDate]
        FROM [Attar2024].[dbo].[cu000] AS cu
        INNER JOIN [Attar2024].[dbo].[ac000] AS ac
            ON cu.[AccountGUID] = ac.[GUID]
        WHERE TRY_CONVERT(float, cu.[CustomerName]) IS NULL
        ORDER BY cu.[CheckDate] DESC;
        """  # Filter numeric names in SQL query

        try:
            # Connect to SQL Server
            connection = pyodbc.connect(conn_str)
            cursor = connection.cursor()
            cursor.execute(query)
            customers = cursor.fetchall()

            # Sync to Odoo
            for customer in customers:
                CustomerName, Phone1, Phone2, Mobile, Code, _ = customer

                # Check if customer already exists in Odoo
                existing_contact = self.env['res.partner'].search([
                    ('company_registry', '=', Code)
                ], limit=1)

                if existing_contact:
                    _logger.info(f"Customer with code {Code} already exists. Skipping.")
                    continue

                # Create new contact in Odoo
                new_contact = self.env['res.partner'].create({
                    'name': CustomerName,
                    'company_registry': Code,
                    'phone': f'{Phone1}/{Phone2}' if Phone1 or Phone2 else None,
                    'mobile': Mobile,
                })
                _logger.info(f"Customer {CustomerName} (Company ID: {Code}) added to Odoo.")

                # Send notification
                self.env['mail.message'].create({
                    'subject': f"New Customer Added: {CustomerName}",
                    'body': f"A new customer, {CustomerName}, has been fetched and added to Odoo.",
                    'message_type': 'notification',
                    'subtype_id': self.env.ref('mail.mt_note').id,
                    'model': 'res.partner',
                    'res_id': new_contact.id,
                    'partner_ids': [(4, partner_id) for partner_id in self.env.user.partner_id.ids],
                })

        except Exception as e:
            _logger.error(f"Error syncing customers: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
