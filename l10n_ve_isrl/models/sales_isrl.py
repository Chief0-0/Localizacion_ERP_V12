# -*- coding: utf-8 -*-
# Copyright 2019 Yan Chirino <ychirino@intechmultiservicios.com>

from odoo import _, api, fields, models  # noqa
from odoo.exceptions import ValidationError


class SalesISLR(models.Model):
    _name = "sales.isrl"
    _description = "Income Tax for Sales in Venezuela (ISLR)"

    def _filter_domain(self):
        invoices = self.env["account.invoice"].search(
            [("state", "=", "open"), ("type", "=", "out_invoice")]
        )
        selection = []
        for invoice in invoices:
            selection.append((invoice.partner_id.id))

        return [("id", "in", selection)]

    name = fields.Many2one(
        "res.partner",
        domain=_filter_domain,
        string="Retention Agent",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    company = fields.Many2one(
        "res.company",
        related="name.company_id",
        string="Retained Subject",
        store=True,
        readonly=True,
    )

    voucher_date = fields.Date(
        string="Voucher Date",
        default=fields.Date.today,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    posting_date = fields.Date(
        string="Posting Date",
        default=fields.Date.today,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    state = fields.Selection(
        [("draft", "Draft"), ("done", "Done")],
        string="Status",
        index=True,
        readonly=True,
        default="draft",
        track_visibility="onchange",
        copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and "
        "unconfirmed Invoice.\n * The 'Done' status is used when the user has "
        "validated and registered the tax in the accounting entry of the "
        "associated invoice",
    )

    income_tax_line_ids = fields.One2many(
        "income.tax.line",
        "res_id",
        string="Tax Lines:",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=True,
    )

    base_field = fields.Float(related="income_tax_line_ids.base")
    total = fields.Float(string="Total withholding")
    amount_total = fields.Float(related="total", readonly=True)

    @api.onchange("income_tax_line_ids")
    def _compute_total(self):

        total = 0.0
        for line in self.income_tax_line_ids:
            total += line.amount
        self.total = total

    @api.onchange("name")
    def set_data(self):
        taxes = self.name.income_tax
        result = []
        for tax in taxes:
            if tax.type_tax_use == "sale":
                invoices = self.env["account.invoice"].search(
                    [("type", "=", "out_invoice"), ("partner_id", "=", self.name.id)]
                )
                for invoice in invoices:
                    result.append(
                        (
                            0,
                            0,
                            {
                                "res_id": self.id,
                                "invoice_id": invoice,
                                "name": tax,
                                "partner_id": self.name,
                                "account_id": tax.account_id,
                                "amount": self._tax_withholdings(
                                    tax, invoice.amount_untaxed
                                ),
                                "base": invoice.amount_untaxed,
                            },
                        )
                    )

        self.income_tax_line_ids = result


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
    def validate(self):
        move_line = self.env["account.move.line"]
        lines = self.income_tax_line_ids
        partner_account = self.name.property_account_receivable_id

        if not partner_account:
            raise ValidationError(
                _(
                    "No account receivable has been set up for this contact \n"
                    "'%s'" % self.name.name
                )
            )

        for line in lines:
            amount = line.amount
            move_id = line.invoice_id.move_id.id
            if amount < 0:
                amount = -amount
            move_line.with_context(check_move_validity=False).create(
                {
                    "name": line.name.name,
                    "quantity": 1,
                    "debit": amount,
                    "account_id": line.account_id.id,
                    "move_id": move_id,
                    "ref": line.invoice_id.number,
                    "date": self.posting_date,
                    "company_id": line.company_id.id,
                    "invoice_id": line.invoice_id.id,
                    "partner_id": line.partner_id.id,
                }
            )
            move_line.with_context(check_move_validity=False).create(
                {
                    "name": "Importe Retenido",
                    "quantity": 1,
                    "credit": amount,
                    "account_id": partner_account.id,
                    "move_id": move_id,
                    "ref": line.invoice_id.number,
                    "date": self.posting_date,
                    "company_id": line.company_id.id,
                    "invoice_id": line.invoice_id.id,
                    "partner_id": line.partner_id.id,
                }
            )

        self.state = "done"


class IncomeTaxLines(models.Model):
    _name = "income.tax.line"
    _description = "Income Tax Lines for Sales in Venezuela (ISLR)"

    name = fields.Many2one(
        "account.tax",
        string="Tax Description",
        required=True,
        domain=[("tax_group_id", "=", "Withholdings"),
                ("type_tax_use", "=", "sale")])

    invoice_id = fields.Many2one(
        "account.invoice",
        string="Invoice",
        ondelete="cascade",
        index=True,
        domain=[("state", "=", "open"), ("type", "=", "out_invoice")],
    )

    res_id = fields.Char(string="RES ID")

    account_id = fields.Many2one(
        "account.account",
        string="Tax Account",
        required=True,
        domain=[("deprecated", "=", False)],
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Retention Agent",
        related="invoice_id.partner_id",
        store=True,
        readonly=True,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Retained Subject",
        related="account_id.company_id",
        store=True,
        readonly=True,
    )

    base = fields.Float(string="Subject Amount")

    amount = fields.Float("Retained Amount")
    line_amount = fields.Float(related="amount", readonly=True)

    @api.onchange('base')
    def re_compute_amount(self):

        obj_isrl = self.env["sales.isrl"]
        amount = obj_isrl._tax_withholdings(self.name, self.base)
        self.amount = amount
