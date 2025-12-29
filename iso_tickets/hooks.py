# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

DEFAULT_SECTIONS = [
    ("Supply", "supply"),
    ("Quality", "quality"),
    ("Maintenance", "maintenance"),
    ("Sales", "sales"),
    ("Tech", "tech"),
    ("HR", "hr"),
    ("Finance", "finance"),
]

def _get_or_create_section(env, name, code):
    Section = env["iso.section"].with_context(active_test=False)
    rec = Section.search([("code", "=", code)], limit=1)
    if rec:
        # keep the name synced if you like
        if rec.name != name:
            rec.name = name
        return rec
    return Section.create({"name": name, "code": code})

def post_init_create_default_sections(cr, registry):
    """Called once after install/upgrade."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    for name, code in DEFAULT_SECTIONS:
        _get_or_create_section(env, name, code)
