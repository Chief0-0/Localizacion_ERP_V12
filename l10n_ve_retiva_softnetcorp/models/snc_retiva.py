# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SncRetiva(models.Model):
    _name = "snc.retiva"
    
    _description = "Retencion IVA"
    
    name = fields.Char(string='Nombre del Impuesto')
    ambito = fields.Selection([
        ('compras', 'Compras'),
        ('ventas', 'Ventas')
    ], required=True, default='compras',
        string='Ambito del Impuesto',
        help="Seleccionar: compras o ventas")    
    porc_ret = fields.Float(string='Base',help='Porcentaje a Retener de la base (la base es el IVA de la factura)')
    formula = fields.Text(string='Cálculo del Impuesto',help='Formula a aplicar en facturas: Porcentaje sobre IVA Ej: 6.000,00 x 75% = -4.500,00')
    account_id = fields.Many2one('account.account',string='Cuenta de Impuesto',help="Seleccionar cuenta contable que ira a asiento en contabilidad")
    account_refund_id = fields.Many2one('account.account',string='Cuenta de Impuesto en Devoluciones',help="Seleccionar cuenta contable que ira a asiento en contabilidad")
    sequence_id = fields.Many2one('ir.sequence', string='Secuencia de Comprobantes',
        help="Consecutivo para Comprobantes de retencion. Puede usarse para varios tipos de retencion.", copy=False)    
    reten_base = fields.Float(string='Porcentaje a Retener')

    @api.model
    def get_retencion(self, monto_sujeto):
        base = 0
        amount = 0
        for lin in self:
            base = (monto_sujeto * lin.porc_ret/100)
            amount = -(eval(lin.formula))
        return base,amount