# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo import models, fields, api, _

from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp
import logging



class SncRetivaPartners(models.Model):
    _name = "snc.retiva.partners"

    _description = "Retencion IVA de clientes"

    def _filter_domain(self):
        invoices = self.env["account.invoice"].search(
            [("state", "=", "open"), ("type", "=", "out_invoice")]
        )
        selection = []
        for invoice in invoices:
            selection.append((invoice.partner_id.id))

        return [("id", "in", selection)]

    name = fields.Char(string='Numero de Comprobante',size=14, required=True)
    partner_id = fields.Many2one('res.partner',string='Agente de Retención', domain=_filter_domain,)

    fecha_comprobante = fields.Date(string='Fecha de Comprobante', default=lambda *a:datetime.now().strftime('%Y-%m-%d'))
    fecha_contabilizacion = fields.Date(string='Fecha de Contabilizacion', default=lambda *a:datetime.now().strftime('%Y-%m-%d'))
    retiva_line = fields.One2many('snc.retiva.partners.lines','retiva_partner_id',string='Lineas de Comprobante')
    move_id = fields.Many2one('account.move',string='Asiento')
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




    @api.multi
    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            if not (len(self.name)==14):
                raise UserError(_('La longitud de campo numero de comprobante debe ser 14 caracteres'))
            val = self.name
            if not val.isdigit():
                raise UserError(_('El campo numero de comprobante solo puede contener caracteres numericos'))


    @api.multi
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id.retiva_id:
            inv = self.env['account.invoice'].search([('partner_id', '=', self.partner_id.id),('type', 'in', ['out_invoice','out_refund']),('retiva_id','=',False),('state','=','open')])
            facturas = []
            for fac in inv:
                base_imponible = fac.amount_tax
                if base_imponible != 0:
                    retiva = self.partner_id.retiva_id
                    monto_sujeto, importe_retenido = retiva.get_retencion(base_imponible)
                    porc_retener = 0
                    if monto_sujeto>0:
                        porc_retener = round(importe_retenido/monto_sujeto*100,2)
                    datos = {'invoice_id':fac.id,
                             'retiva_id':retiva.id}
                    facturas.append((0, 0, datos))
                #facturas.append(lin.id)
            #retiva_line = [(6, 0, facturas)]
            if facturas:
                self.retiva_line = facturas
                values = {
                    'retiva_line': facturas,
                }
            #self.update(values)

    @api.model
    def _set_journal(self):
        inv_type = self._context.get('type', 'out_invoice')
        inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            ('type', 'in', filter(None, map(TYPE2JOURNAL.get, inv_types))),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)
    @api.multi
    def validate(self):
        move_line = self.env["account.move.line"]
        lines = self.retiva_line
        partner_account = self.partner_id

        for line in lines:
            amount = line.monto_sujeto
            move_id = line.invoice_id.move_id.id
            if amount < 0:
                amount = -amount
            move_line.with_context(check_move_validity=False).create(
                {
                    "name": line.name.name,
                    "quantity": 2,
                    "debit": amount,
                    "account_id": line.account_id.id,
                    "move_id": move_id,
                    "ref": line.invoice_id.number,
                    "date": self.fecha_comprobante,
                    "company_id": line.company_id.id,
                    "invoice_id": line.invoice_id.id,
                    "partner_id": line.retiva_partner_id.id,
                }
            )
            move_line.with_context(check_move_validity=False).create(
                {
                    "name": "Importe Retenido IVA",
                    "quantity": 2,
                    "credit": amount,
                    "account_id": line.company_id.id,
                    "move_id": move_id,
                    "ref": line.invoice_id.number,
                    "date": self.fecha_comprobante,
                    "company_id": line.company_id.id,
                    "invoice_id": line.invoice_id.id,
                    "partner_id": line.retiva_partner_id.id,
                }
            )

        self.state = "done"

class SncRetivaPartnersLines(models.Model):
    _name = "snc.retiva.partners.lines"

    _description = "Retencion IVA de clientes facturas"

    @api.one
    @api.depends('retiva_id', 'invoice_id')
    def _compute_retiva(self):
        base_imponible = self.invoice_id.amount_tax
        retiva = self.retiva_id
        if retiva:
            monto_sujeto, importe_retenido = retiva.get_retencion(base_imponible)
            porc_retener = 0
            if monto_sujeto != 0:
                porc_retener = round(abs(importe_retenido/monto_sujeto*100),2)
            self.monto_sujeto = monto_sujeto
            self.porc_retener = porc_retener
            self.importe_retenido = importe_retenido
            if self.invoice_id.type=='out_invoice':
                self.account_id = retiva.account_id
            else:
                self.account_id = retiva.account_refund_id

    name = fields.Many2one(
        "account.tax",
        string="Tax Description",
        required=True,
        domain=[("tax_group_id", "=", "Withholdings"),
                ("type_tax_use", "=", "sale")])
    retiva_partner_id = fields.Many2one('snc.retiva.partners')
    invoice_id = fields.Many2one(
        "account.invoice",
        string="Invoice",
        ondelete="cascade",
        index=True,
        domain=[("state", "=", "open"), ("type", "=", "out_invoice")],
    )

    monto_sujeto = fields.Float(string='Monto Sujeto',
        store=True, readonly=True, compute='_compute_retiva')

    #account_id = fields.Many2one(
    #    "account.account",
    #    string="Tax Account",
    #    required=True,
    #    domain=[("deprecated", "=", False)],
    #)
    company_id = fields.Many2one(
        "res.company",
        string="Retained Subject",
        related="account_id.company_id",
        store=True,
        readonly=True,
    )

    porc_retener = fields.Float(string='Porcentaje a Retener')
    importe_retenido = fields.Float(string='Importe Retenido',
        store=True, readonly=True, compute='_compute_retiva')
    retiva_id = fields.Many2one('snc.retiva',string='Retencion de IVA')
    account_id = fields.Many2one('account.account',compute='_compute_retiva',string='Cuenta de Impuesto',help="Seleccionar cuenta contable que ira a asiento en contabilidad")
