# -*- coding: utf-8 -*-
{
    'name': "Reporte Libro Diario",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "DSA Software SG, C.A.",
    'website': "http://www.dsasoftware.com.ve",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Account',
    'version': '0.1',

    # any module necessary for this one to work correctly
    "depends" : ['base','account', 'report_xlsx', 'report_xml'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/report_general_daily.xml',
        'views/account_report.xml',        
        'wizard/account_report_general_daily_view.xml',        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
