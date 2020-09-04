# -*- coding: utf-8 -*-
# Copyright 2019 Yan Chirino <ychirino@intechmultiservicios.com>

{
    "name": "ISLR Venezuela",
    "summary": """This module allows the inclusion of the income tax
        in Venezuela""",
    "category": "Localization",
    "author": "Softnetcorp - Yan Chirino",
    "website": "https://softnetcorp.net",
    "license": "Other proprietary",
    "depends": ["l10n_ve", "sale_management", "sale", "purchase", "contacts", "report_xml", "l10n_ve_retiva_softnetcorp"],
    "external_dependencies": {"python": [], "bin": []},
    "data": [
        "security/ir.model.access.csv",
        "data/account_tax_group_data.xml",
        "data/income_tax_sale_data.xml",
        "data/income_tax_purchase_data.xml",
        "views/tributary_unit_view.xml",
        "views/account_tax_inherit_views.xml",
        "views/income_tax.xml",
        "views/res_partner_inherit_view.xml",
        "views/account_invoice_inherit_view.xml",
        "views/sales_isrl_views.xml",
        "views/income_tax_withholding_declaration_views.xml",
        "reports/retention_receipt.xml",
        "reports/set_withholdings_isrl.xml",
    ],
    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,
    "uninstall_hook": None,
    "auto_install": False,
    "application": False,
    "installable": True,
    "description": """This module allows the inclusion of the income tax in
    venezuela, adding characteristics in purchase invoices and sales invoices,
    also allows the registration of the value of the tax unit.

    """,
}
