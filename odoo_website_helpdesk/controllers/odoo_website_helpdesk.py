import datetime as DT
from odoo import http
from odoo.http import request


class HelpDeskDashboard(http.Controller):
    """Controller for handling Help Desk dashboard requests."""

    @http.route(['/helpdesk_dashboard'], type='json', auth="public")
    def helpdesk_dashboard(self):
        """Retrieves statistics for tickets in different stages."""
        stage_names = ['Inbox', 'Draft', 'In Progress', 'Canceled', 'Done', 'Closed']
        stage_ids = {name: request.env['ticket.stage'].search([('name', '=', name)], limit=1).id
                     for name in stage_names}

        new_stages = [stage_ids.get('Inbox'), stage_ids.get('Draft')]

        def get_ticket_data(stage_id_list):
            tickets = request.env["ticket.helpdesk"].sudo().search([('stage_id', 'in', stage_id_list)])
            return len(tickets), [ticket.id for ticket in tickets]

        dashboard_values = {
            'new': get_ticket_data(new_stages)[0],
            'new_id': get_ticket_data(new_stages)[1],
            'in_progress': get_ticket_data([stage_ids.get('In Progress')])[0],
            'in_progress_id': get_ticket_data([stage_ids.get('In Progress')])[1],
            'canceled': get_ticket_data([stage_ids.get('Canceled')])[0],
            'canceled_id': get_ticket_data([stage_ids.get('Canceled')])[1],
            'done': get_ticket_data([stage_ids.get('Done')])[0],
            'done_id': get_ticket_data([stage_ids.get('Done')])[1],
            'closed': get_ticket_data([stage_ids.get('Closed')])[0],
            'closed_id': get_ticket_data([stage_ids.get('Closed')])[1],
        }
        return dashboard_values

    def helpdesk_dashboard_week(self):
        """ Retrieves statistics for tickets created in the past week. """
        today = DT.date.today()
        week_ago = str(today - DT.timedelta(days=7)) + ' '
        stage_names = ['Inbox', 'Draft', 'In Progress', 'Canceled', 'Done', 'Closed']
        stages = {name: request.env['ticket.stage'].search([('name', '=', name)], limit=1).id for name in stage_names}
        stage_ids = [stages.get('Inbox'), stages.get('Draft')]

        def get_ticket_data(stage_id):
            count = request.env["ticket.helpdesk"].sudo().search_count([('stage_id', '=', stage_id), ('create_date', '>', week_ago)])
            ids = request.env["ticket.helpdesk"].sudo().search([('stage_id', '=', stage_id), ('create_date', '>', week_ago)]).ids
            return count, ids

        new_count, new_ids = get_ticket_data(stage_ids)
        in_progress_count, in_progress_ids = get_ticket_data(stages.get('In Progress'))
        canceled_count, canceled_ids = get_ticket_data(stages.get('Canceled'))
        done_count, done_ids = get_ticket_data(stages.get('Done'))
        closed_count, closed_ids = get_ticket_data(stages.get('Closed'))

        dashboard_values = {
            'new': new_count,
            'in_progress': in_progress_count,
            'canceled': canceled_count,
            'done': done_count,
            'closed': closed_count,
            'new_id': new_ids,
            'in_progress_id': in_progress_ids,
            'canceled_id': canceled_ids,
            'done_id': done_ids,
            'closed_id': closed_ids,
        }
        return dashboard_values

    @http.route(['/helpdesk_dashboard_month'], type='json', auth="public")
    def helpdesk_dashboard_month(self):
        """Retrieves statistics for tickets created in the past month."""
        today = DT.date.today()
        month_ago = today - DT.timedelta(days=30)
        week_ago = str(month_ago) + ' '

        stages = request.env['ticket.stage'].sudo().search([('name', 'in', ['Inbox', 'Draft', 'In Progress', 'Canceled', 'Done', 'Closed'])])
        stage_ids = {stage.name: stage.id for stage in stages}

        def get_stage_data(names):
            ids_list = [stage_ids.get(name) for name in names if stage_ids.get(name)]
            tickets = request.env["ticket.helpdesk"].sudo().search([('stage_id', 'in', ids_list), ('create_date', '>', week_ago)])
            return len(tickets), [ticket.id for ticket in tickets]

        new_count, new_ids = get_stage_data(['Inbox', 'Draft'])
        in_progress_count, in_progress_ids = get_stage_data(['In Progress'])
        canceled_count, canceled_ids = get_stage_data(['Canceled'])
        done_count, done_ids = get_stage_data(['Done'])
        closed_count, closed_ids = get_stage_data(['Closed'])

        dashboard_values = {
            'new': new_count,
            'in_progress': in_progress_count,
            'canceled': canceled_count,
            'done': done_count,
            'closed': closed_count,
            'new_id': new_ids,
            'in_progress_id': in_progress_ids,
            'canceled_id': canceled_ids,
            'done_id': done_ids,
            'closed_id': closed_ids,
        }
        return dashboard_values

    @http.route(['/helpdesk_dashboard_year'], type='json', auth="public")
    def helpdesk_dashboard_year(self):
        """Retrieves statistics for tickets created in the past year."""
        today = DT.date.today()
        year_ago = today - DT.timedelta(days=360)
        stages = ['Inbox', 'Draft', 'In Progress', 'Canceled', 'Done', 'Closed']
        stage_ids = {stage: request.env['ticket.stage'].sudo().search([('name', '=', stage)], limit=1).id for stage in stages}

        def get_ticket_data(stage_name):
            stage_id = stage_ids.get(stage_name)
            tickets = request.env["ticket.helpdesk"].sudo().search([('stage_id', '=', stage_id), ('create_date', '>', year_ago)])
            return len(tickets), [ticket.id for ticket in tickets]

        dashboard_values = {}
        for stage in stages:
            count, ids = get_ticket_data(stage)
            key = stage.lower()
            dashboard_values[key] = count
            dashboard_values[f'{key}_id'] = ids
        return dashboard_values
