# -*- coding: utf-8 -*-
# Copyright 2019 Yan Chirino <ychirino@intechmultiservicios.com>

from odoo import _, fields, models  # noqa
from odoo.exceptions import UserError


class IncomeTaxWithholdingDeclaration(models.TransientModel):
    _name = "income.tax.withholding.declaration"
    _description = "Income Tax Withholding Declaration in Venezuela (ISLR)"

    date_from = fields.Date(string="Date from")
    date_to = fields.Date(string="Date to")

    def _check_values(self):
        if self.date_from > self.date_to:
            raise UserError(_("The start date can not be longer than the end date."))

        return True

    def print_isrl_xml_report(self):

        if self._check_values():
            tax_group_id = (
                self.env["account.tax.group"].search([("name", "=", "Withholdings")]).id
            )
            ids = (
                self.env["account.invoice.tax"]
                .search(
                    [
                        ("tax_id.tax_group_id", "=", tax_group_id),
                        ("create_date", ">=", self.date_from),
                        ("create_date", "<=", self.date_to),
                    ]
                )
                .ids
            )

            if ids:
                return (
                    self.env["report"]
                    .with_context(active_ids=ids, active_model="account.invoice.tax")
                    .get_action([], "l10n_ve_isrl.set_withholdings_isrl_report")
                )

            raise UserError(_("Nothing to print."))
