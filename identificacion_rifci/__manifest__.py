# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'identificacion_rifci',
    'version' : '12',
    'summary': 'Agrega el campo de CI y Rif a Clientes, Proveedores,Compania y Factura',

    'description': """

    """,
    'author': 'Softw & Hardw Solutions SSH',
    'collaborator': 'Softw & Hardw Solutions SSH',
    'category': 'Identificacion',
    'website': 'https://solutionssh.com',
    'depends' : ['base','account'],
    'data': [
        'views/res_partner_view.xml',
	    'views/res_company_view.xml',
	    'views/account_invoice_view.xml'
    ],

    'installable': True,
    'application': True,
    'auto_install': False,

}
