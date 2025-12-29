from odoo import fields, models, tools


class DailyAttendance(models.Model):
    """Model to hold data from the biometric device"""
    _name = 'daily.attendance'
    _description = 'Daily Attendance Report'
    _auto = False
    _order = 'punching_day desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', help='Employee Name')

    punching_day = fields.Datetime(string='Date', help='Date of punching')
    address_id = fields.Many2one('res.partner', string='Working Address', help='Working address of the employee')
    attendance_type = fields.Selection(
        [('1', 'Finger'), ('15', 'Face'), ('2', 'Type_2'), ('3', 'Password'), ('4', 'Card')],
        string='Category', help='Attendance detecting methods'
    )
    punch_type = fields.Selection(
        [('0', 'Check In'), ('1', 'Check Out'), ('2', 'Break Out'), ('3', 'Break In'), ('4', 'Overtime In'),
         ('5', 'Overtime Out')],
        string='Punching Type', help='The Punching Type of attendance'
    )
    punching_time = fields.Datetime(string='Punching Time', help='Punching time in the device')

    def init(self):
        """Retrieve the data for attendance report"""
        tools.drop_view_if_exists(self._cr, 'daily_attendance')
        query = """
            CREATE OR REPLACE VIEW daily_attendance AS (
                SELECT
                    MIN(z.id) AS id,
                    z.employee_id AS employee_id,
                    z.write_date AS punching_day,
                    z.address_id AS address_id,
                    z.attendance_type AS attendance_type,
                    z.punching_time AS punching_time,
                    z.punch_type AS punch_type
                FROM zk_machine_attendance z
                JOIN hr_employee e ON (z.employee_id = e.id)
                GROUP BY
                    z.employee_id,
                    z.write_date,
                    z.address_id,
                    z.attendance_type,
                    z.punch_type,
                    z.punching_time
            )
        """
        self._cr.execute(query)

        # Add INSTEAD OF DELETE trigger to the view
        trigger_query = """
            CREATE OR REPLACE FUNCTION delete_from_zk_machine_attendance() RETURNS TRIGGER AS $$
            BEGIN
                DELETE FROM zk_machine_attendance
                WHERE id = OLD.id; -- Ensure unique identifier is used
                RETURN OLD;
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER trigger_delete_daily_attendance
            INSTEAD OF DELETE ON daily_attendance
            FOR EACH ROW
            EXECUTE FUNCTION delete_from_zk_machine_attendance();
        """
        self._cr.execute(trigger_query)
