# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2015 Therp BV <http://therp.nl>.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import SUPERUSER_ID
from odoo.api import Environment


def post_init_hook(cr, pool):
    env = Environment(cr, SUPERUSER_ID, {})
    adjust_retiva_partners_post(env)


def adjust_retiva_partners_post(env):
    retiva_id = env.ref('l10n_ve_retiva_softnetcorp.snc_retiva_c75')
    print ('retiva_id:',retiva_id)
    suppliers = env['res.partner'].search([('supplier','=',True)])
    for supplier in suppliers:
        supplier.write({'retiva_id':retiva_id.id})

