# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _inherit = 'res.partner'

    tipo = fields.Selection(string='Tipo', selection=[('V', 'V'), ('E', 'E'), ('P', 'P'), ('J', 'J'), ('G', 'G'), ('M', 'M'), ('C', 'C')], required=True, default='V')

    is_company = fields.Boolean(string='Is a Company', default=False, help="Check if the contact is a company, otherwise it is a person")
    company_type = fields.Selection(string='Company Type', selection=[('person', 'Individual'), ('company', 'Company')], compute='_compute_company_type', inverse='_write_company_type')


    @api.constrains("vat")
    def check_vat(self):

        if len(self.vat) > 20 or len(self.vat) < 4:
            raise ValidationError("Ingrese un campo identificacion válido")
            return False