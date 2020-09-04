# -*- coding: utf-8 -*-
# Copyright 2019 Yan Chirino <ychirino@intechmultiservicios.com>

from odoo import fields, models


class AccountTaxInherit(models.Model):
    _inherit = "account.tax"

    person_type = fields.Selection(
        selection=(
            [
                ("PNR", "Resident Natural Person"),
                ("PNNR", "Non-Resident Natural Person"),
                ("LPD", "Legal Person Domiciled"),
                ("LPND", "Legal Person Not Domiciled"),
            ]
        ),
        string="Person Type",
        help="Select the type of person if the group of taxes is withholdings",
    )
