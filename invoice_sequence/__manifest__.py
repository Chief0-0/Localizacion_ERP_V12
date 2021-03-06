# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
# Generated by the Odoo plugin for Dia !

{
    'name': 'invoice_sequence',
    'version': '12',
    'summary': """Añade secuencias a las facturas""",
    'description': """Añade secuencias a las facturas""",
    'author': 'Softw & Hardw Solutions SSH',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://solutionssh.com/',
    'category': 'Contabilidad',
    'depends': ['base','account','mail'],
    'license': 'AGPL-3',
    'data': [
        'views/invoice_sequence.xml',
        'data/seq_invoice.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}