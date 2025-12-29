from odoo import fields, models

class HelpdeskBranch(models.Model):
    _name = "helpdesk.branch"
    _description = "Helpdesk Branch"

    name = fields.Char(required=True)
    location = fields.Char()


class HelpdeskVisitType(models.Model):
    _name = "helpdesk.visit.type"
    _description = "Helpdesk Visit Type"

    name = fields.Char(required=True)


class HelpdeskTicketMethod(models.Model):
    _name = "helpdesk.ticket.method"
    _description = "Helpdesk Ticket Request Method"

    name = fields.Char(required=True)


class HelpdeskDevice(models.Model):
    _name = "helpdesk.device"
    _description = "Helpdesk Device"

    name = fields.Char(required=True)
