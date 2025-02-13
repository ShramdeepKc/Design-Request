# -*- coding: utf-8 -*-
{
    'name': "design_request",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Portal',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'portal', 'mail', 'sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/views.xml',
        'views/portalviews.xml',
        'data/mail_template.xml',

    ],
    'assets': {
        'web.assets_frontend': [
            'design_request/static/src/css/custom_styles.css',

        ],

    },
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': True,

}
