# -*- coding: utf-8 -*-

{
    'name': 'LT India Approvals',
    'license': 'LGPL-3',
    'category': 'other',
    'sequence': 2,
    'summary': 'Custom Subscription Module For LT India',
    'version': '1.0',
    'depends': ['base', 'web', 'product', 'quick_create_disable'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/menu_items.xml',
        'views/approval.xml',
        'report/4m_approval_document.xml',
        'data/mail_templates.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'ltindia_approvals/static/src/scss/approval.scss',
            'ltindia_approvals/static/src/js/approval_list_dash_board.js',
        ],
        'web.assets_frontend': [
        ],
        'web.assets_qweb': [
            'ltindia_approvals/static/src/xml/**/*',
        ],
    },
    'installable': True,
    'application': False,
}
