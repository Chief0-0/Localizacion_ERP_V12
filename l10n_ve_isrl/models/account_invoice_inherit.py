# -*- coding: utf-8 -*-
# Copyright 2019 Yan Chirino <ychirino@intechmultiservicios.com>

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountInvoiceTaxInherit(models.Model):
    _inherit = "account.invoice.tax"

    subject_amount = fields.Float(string="Subject Amount")

    subject_amount_total = fields.Float(related="subject_amount", readonly=True)
    withholding = fields.Boolean(string="Withholdings", default=False)
    date = fields.Date(string="Date")


class AccountInvoiceLineInherit(models.Model):
    _inherit = "account.invoice.line"

    income_tax = fields.Many2many("account.tax", string="Retenciones")

    @api.onchange("product_id")
    def onchange_product_id(self):
        partner_taxes = self.partner_id.income_tax
        if partner_taxes:
            withholdings = []
            for tax in partner_taxes:
                if tax.type_tax_use == "purchase":
                    withholdings.append(tax.id)
            return {"domain": {"income_tax": [("id", "in", withholdings)]}}  # noqa


class AccountInvoiceInherit(models.Model):
    _inherit = "account.invoice"

    tax_withholdings = fields.Monetary(
        compute="set_income_taxes", string="Tax withholdings"
    )

    total_taxes = fields.Monetary(compute="set_income_taxes", string="Tax")
    total_retiva = fields.Monetary(compute="set_income_taxes", string="IVA Retenido")

    @api.onchange("invoice_line_ids")
    def set_income_taxes(self):
        taxes_grouped = self.get_taxes_values()

        invoice_lines = self.invoice_line_ids
        result = []
        withholding_total = []
        total_taxes = []
        retiva = []
        for line in invoice_lines:
            for tax in line.income_tax:
                amount = -self._tax_withholdings(tax, line.price_subtotal)
                withholding_total.append(amount)
                result.append(
                    (
                        0,
                        0,
                        {
                            "invoice_id": self.id,
                            "name": tax.name,
                            "tax_id": tax.id,
                            "amount": amount,
                            "subject_amount": line.price_subtotal,
                            "base": line.price_subtotal,
                            "manual": False,
                            "account_analytic_id": line.account_analytic_id.id or False,
                            "account_id": tax.account_id.id,
                            "withholding": "True",
                            "date": self.date,
                        },
                    )
                )


        self.tax_line_ids = result

        self.tax_withholdings = sum(withholding_total)
        #self.total_taxes = sum(total_taxes)
        #self.total_retiva = sum(retiva)
        return

    def _tax_withholdings(self, tax, base):
        if tax.person_type == "PNR":
            factor = 83.3334
            try:
                uvt = self.env["tributary.unit"].search([], order="date desc")[0].amount
            except BaseException:
                raise ValidationError(
                    _("No value has been " "configured for the tax unit (UVT)")
                )
            retention_percentage = tax.amount
            subtract = uvt * (retention_percentage / 100) * factor
            isrl = base * (retention_percentage / 100) - subtract
            if isrl < 0:
                isrl = -isrl
            return isrl

        else:
            retention_percentage = tax.amount
            isrl = base * (retention_percentage / 100)
            return isrl

    @api.multi
    def print_isrl_retention(self):
        if self.tax_withholdings >= 0:
            raise UserError(_("Nothing to print."))

        return (
            self.env['report'].get_action(self, 'l10n_ve_isrl.report_isrl_document')
        )
