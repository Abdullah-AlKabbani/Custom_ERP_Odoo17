import datetime
import logging
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from pytz import timezone
_logger = logging.getLogger(__name__)

try:
    from zk import ZK, const
except ImportError:
    _logger.error("Please Install pyzk library.")


class BiometricDeviceDetails(models.Model):
    """Model for configuring and connect the biometric device with odoo"""
    _name = 'biometric.device.details'
    _description = 'Biometric Device Details'

    name = fields.Char(string='Name', required=True, help='Record Name')
    device_ip = fields.Char(string='Device IP', required=True,
                            help='The IP address of the Device')
    port_number = fields.Integer(string='Port Number', required=True,
                                 help="The Port Number of the Device")
    address_id = fields.Many2one('res.partner', string='Working Address',
                                 help='Working address of the partner')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id.id,
                                 help='Current Company')

    def device_connect(self, zk):
        """Function for connecting the device with Odoo"""
        try:
            conn = zk.connect()
            return conn
        except Exception:
            return False

    def action_test_connection(self):
        """Checking the connection status"""
        zk = ZK(self.device_ip, port=self.port_number, timeout=30,
                password=False, ommit_ping=False)
        try:
            if zk.connect():
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'Successfully Connected',
                        'type': 'success',
                        'sticky': False
                    }
                }
        except Exception as error:
            raise ValidationError(f'{error}')

    def action_clear_attendance(self):
        """Method to clear record from the zk.machine.attendance model and from the device"""
        for info in self:
            try:
                machine_ip = info.device_ip
                zk_port = info.port_number
                try:
                    # Connecting with the device
                    zk = ZK(machine_ip, port=zk_port, timeout=30,
                            password=0, force_udp=False, ommit_ping=False)
                except NameError:
                    raise UserError(_("Please install it with 'pip3 install pyzk'."))

                conn = self.device_connect(zk)
                if conn:
                    conn.enable_device()
                    clear_data = zk.get_attendance()
                    if clear_data:
                        # Clearing data in the device
                        conn.clear_attendance()
                        # Clearing data from attendance log
                        self._cr.execute("""delete from zk_machine_attendance""")
                        conn.disconnect()
                    else:
                        raise UserError(_('Unable to clear Attendance log. Are you sure attendance log is not empty.'))
                else:
                    raise UserError(_('Unable to connect to Attendance Device. Please use Test Connection button to verify.'))
            except Exception as error:
                raise ValidationError(f'{error}')

    @api.model
    def cron_download(self):
        machines = self.env['biometric.device.details'].search([])
        for machine in machines:
            machine.action_download_attendance()

    def action_download_attendance(self):
        """Function to download attendance records from the device."""
        _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
        zk_attendance = self.env['zk.machine.attendance']
        hr_attendance = self.env['hr.attendance']

        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number

            try:
                # Connect to the biometric device
                zk = ZK(machine_ip, port=zk_port, timeout=15,
                        password=0, force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(_("Pyzk module not Found. Please install it with 'pip3 install pyzk.'"))

            conn = self.device_connect(zk)

            if conn:
                conn.disable_device()  # Device cannot be used during processing
                users = conn.get_users()
                attendance_records = conn.get_attendance()

                if attendance_records:
                    for each in attendance_records:
                        # Original timestamp from the device
                        atten_time = each.timestamp

                        # Timezone handling
                        damascus_tz = timezone('Asia/Damascus')  # Damascus timezone
                        utc_tz = pytz.utc

                        # Convert device time to Damascus timezone, then to UTC
                        local_time = damascus_tz.localize(atten_time, is_dst=None)
                        utc_time = local_time.astimezone(utc_tz)
                        atten_time = fields.Datetime.to_string(utc_time)  # Convert to Odoo-compatible format

                        # Log time conversions for debugging
                        _logger.info(f"Device Time: {each.timestamp}")
                        _logger.info(f"Localized to Damascus Timezone: {local_time}")
                        _logger.info(f"Converted to UTC: {utc_time}")
                        _logger.info(f"Stored Time (UTC): {atten_time}")

                        # Log attendance information for each employee
                        _logger.info(f"Processing Attendance Log for Employee ID: {each.user_id}")
                        _logger.info(f"Employee: {each.user_id}, Attendance Status: {each.status}, Punch Type: {each.punch}")

                        for user in users:
                            if user.user_id == each.user_id:
                                # Find employee linked to the device ID
                                employee = self.env['hr.employee'].search([('device_id_num', '=', each.user_id)], limit=1)

                                if employee:
                                    # Avoid duplicate entries
                                    duplicate_atten_ids = zk_attendance.search([
                                        ('device_id_num', '=', each.user_id),
                                        ('punching_time', '=', atten_time)
                                    ])

                                    if not duplicate_atten_ids:
                                        zk_attendance.create({
                                            'employee_id': employee.id,
                                            'device_id_num': each.user_id,
                                            'attendance_type': str(each.status),
                                            'punch_type': str(each.punch),
                                            'punching_time': atten_time,
                                            'address_id': info.address_id.id
                                        })

                                        # Check-in or check-out logic
                                        open_attendance = hr_attendance.search([
                                            ('employee_id', '=', employee.id),
                                            ('check_out', '=', False)
                                        ], limit=1)

                                        if each.punch == 0:  # Check-in
                                            if open_attendance:
                                                # Close the open check-in with the current time as check-out
                                                open_attendance.write({'check_out': atten_time})
                                            # Create a new check-in
                                            hr_attendance.create({
                                                'employee_id': employee.id,
                                                'check_in': atten_time
                                            })
                                        elif each.punch == 1:  # Check-out
                                            if open_attendance:
                                                # Close the open check-in
                                                open_attendance.write({'check_out': atten_time})
                                            else:
                                                _logger.warning(f"No open check-in found for employee {employee.name} at {atten_time}")
                                else:
                                    # If no employee is found, create a new one
                                    new_employee = self.env['hr.employee'].create({
                                        'device_id_num': each.user_id,
                                        'name': user.name
                                    })
                                    zk_attendance.create({
                                        'employee_id': new_employee.id,
                                        'device_id_num': each.user_id,
                                        'attendance_type': str(each.status),
                                        'punch_type': str(each.punch),
                                        'punching_time': atten_time,
                                        'address_id': info.address_id.id
                                    })

                                    hr_attendance.create({
                                        'employee_id': new_employee.id,
                                        'check_in': atten_time
                                    })

                    conn.disconnect()  # Disconnect device after processing
                    return True
                else:
                    raise UserError(_('Unable to get the attendance log, please try again later.'))
            else:
                raise UserError(_('Unable to connect, please check the parameters and network connections.'))

    def action_restart_device(self):
        """For restarting the device"""
        zk = ZK(self.device_ip, port=self.port_number, timeout=15,
                password=0, force_udp=False, ommit_ping=False)
        self.device_connect(zk).restart()
