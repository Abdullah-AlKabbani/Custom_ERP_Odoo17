# __manifest__.py
{
    "name": "Time & Attendance Analysis",
    "version": "17.0.1.0.0",
    "summary": "List employees who did not attend on a selected date.",
    "category": "Human Resources/Employees",
    "author": "Your Company",
    "license": "LGPL-3",
    "depends": ["hr", "hr_attendance"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/employee_views.xml",                  # <-- forward slashes
        "wizards/attendance_day_filter_wizard_views.xml",
        "views/menu_views.xml"
    ],
    "installable": True,
    "application": True
}
