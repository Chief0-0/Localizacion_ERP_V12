# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    rif = fields.Char(string='rif', required=True, readonly=True, related='partner_id.vat')

