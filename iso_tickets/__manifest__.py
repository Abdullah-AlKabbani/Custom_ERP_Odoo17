# -*- coding: utf-8 -*-
{
    "name": "ISO Tickets",
    "version": "17.0.1.0.1",
    "author": "You",
    "category": "Operations",
    "summary": "ISO tickets with website form and reporting",
    "depends": ["base", "mail", "website", "web"],
    "data": [
        "security/iso_security.xml",
        "security/iso_rules.xml",
        "security/ir.model.access.csv",


        # Core model views
        "views/branch_views.xml",
        "views/section_views.xml",
        "views/shift_views.xml",
        "views/statement_views.xml",
        "views/ticket_search_view.xml",
        "views/ticket_views.xml",

        # Make sure the ROOT backend menu exists before anything references it
        "views/menu.xml",                 # ⬅️ move this up

        # Reporting (now safe to reference the root menu)
        "views/reporting_views.xml",

        # Data / sequences
        "data/iso_ticket_sequences.xml",
        "data/iso_default_shifts.xml",
        # "data/iso_sections.xml",

        # Website
        "views/website_templates.xml",
        "views/website_menu.xml",
    ],
    # "post_init_hook": "post_init_create_default_sections",
    "assets": {},
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
