# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools
from odoo.exceptions import ValidationError


class Company(models.Model):
    _inherit = "res.company"

    tipo = fields.Selection(string='Tipo', selection=[('V', 'V'), ('E', 'E'), ('P', 'P'), ('J', 'J'), ('G', 'G'), ('M', 'M'), ('C', 'C')], required=True, default='V')

    @api.constrains("vat")
    def check_vat(self):

        if len(self.vat) > 20 or len(self.vat) < 4:
            raise ValidationError("Ingrese un campo identificacion válido")
            return False