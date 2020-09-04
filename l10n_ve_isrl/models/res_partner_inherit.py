# -*- coding: utf-8 -*-
# Copyright 2019 Yan Chirino <ychirino@intechmultiservicios.com>

from odoo import api, fields, models  # noqa


class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    income_tax = fields.Many2many("account.tax", string="Retention of ISLR")

    @api.onchange("company_type")
    def onchange_company_type(self):
        if self.company_type == "person":
            return {
                "domain": {"income_tax": [("person_type", "in", ["PNR", "PNNR"])]}
            }  # noqa
        else:
            return {
                "domain": {"income_tax": [("person_type", "in", ["LPD", "LPND"])]}
            }  # noqa
