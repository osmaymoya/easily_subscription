# -*- coding: utf-8 -*-

# Developer: Osmay Moya Miranda
# odoo_royal/__manifest__.py
{
    'name': 'Easilyflow subscription Odoo 17',
    'description': '',
    'summary': '',
    'version': '17.0.1.0',
    'category': 'Uncategorized',
    'license': 'LGPL-3',
    'author': 'Dream Project',
    'depends': ['base', 'website'],
    'data': [
        'security/security.xml',
        'views/signup_form_template.xml'
    ],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
}
