# -*- coding: utf-8 -*-
# Copyright 2019 Yan Chirino <ychirino@intechmultiservicios.com>

from odoo import fields, models  # noqa


class TributaryUnit(models.Model):
    _name = "tributary.unit"
    _description = "Tributary Unit in Venezuela"

    name = fields.Char(string="Official Gazette Nº")
    date = fields.Date(string="Gazette Date")
    amount = fields.Float(string="Amount")
