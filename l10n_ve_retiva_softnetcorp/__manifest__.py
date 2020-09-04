# -*- coding: utf-8 -*-
{
    'name': "Retencion IVA Venezuela",

    'summary': """
        Retencion IVA
        """,

    'description': """
        Retencion IVA
    """,

    'author': "Softw & Hardw Solutions SSH",
    'website': "https://solutionssh.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'account',

    # any module necessary for this one to work correctly
    'depends': ['base','identificacion_rifci', 'invoice_sequence'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/snc_retiva_views.xml',
        'views/snc_retiva_partners_views.xml',
        'views/res_partner_views.xml',
        'views/account_invoice_views.xml',
        'data/snc_retiva_data.xml',
        'wizards/wizard_generar_txt_view.xml',
        'views/snc_external_layout.xml',
        'views/snc_footer.xml',
        'views/account_invoice_retiva_template.xml',
        'report/account_invoice_report.xml',
        'data/snc_retiva_action_data.xml'        
    ],
    "post_init_hook": "post_init_hook",    
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
}