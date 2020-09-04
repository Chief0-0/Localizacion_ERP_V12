# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from odoo.exceptions import UserError, RedirectWarning, ValidationError

import odoo.addons.decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    retiva_id = fields.Many2one('snc.retiva',string='Retencion de IVA')
    amount_retiva = fields.Monetary(string='Iva Retenido',
        store=True, readonly=True, compute='_compute_amount')
    number_retiva = fields.Char('Comprobante Numero',size=14)
    input_retiva = fields.Monetary(string='Iva Retenido',readonly=True, default=0.00)
    retiva_sent = fields.Boolean(readonly=True, default=False, copy=False,
        help="It indicates that the ret. i.v.a. has been sent.")
    retiva_excluye = fields.Boolean(string='Excluir Retencion IVA', default=False, readonly=True, states={'draft': [('readonly', False)]})
    total_iva = fields.Monetary(string='total con iva', compute='get_total_carga')

    @api.one
    def get_total_carga(self):
        total = 0
        total = total + self.amount_untaxed
        total = total + self.total_taxes
        self.total_iva = total

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice','input_retiva')
    def _compute_amount(self):
        super(AccountInvoice,self)._compute_amount()
        if self.type in ['in_invoice','in_refund']:
            self.amount_tax = sum(line.amount if line.amount>0 else 0 for line in self.tax_line_ids)
            if not self.retiva_excluye:
                self.amount_retiva = sum(line.amount if line.amount<0 else 0 for line in self.tax_line_ids)
        if self.type in ['out_invoice','out_refund']:
            self.amount_retiva = self.input_retiva

    @api.onchange('retiva_excluye')
    def _onchange_retiva_excluye(self):
        if self.retiva_excluye:
            values = {
                        'retiva_id': False,
                    }
        else:
            values = {
                'retiva_id': self.partner_id.retiva_id and self.partner_id.retiva_id.id or False,
            }
        self.update(values)
        print ('Values:',values,self.retiva_excluye)
        self._onchange_partner_id()

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        super(AccountInvoice,self)._onchange_partner_id()
        if self.retiva_excluye:
            values = {
                        'retiva_id': False,
                    }
        else:
            values = {
                'retiva_id': self.partner_id.retiva_id and self.partner_id.retiva_id.id or False,
            }
        self.update(values)

    @api.onchange('invoice_line_ids','retiva_excluye')
    def _onchange_invoice_line_ids(self):
        taxes_grouped = self.get_taxes_values()
        tax_lines = self.tax_line_ids.browse([])
        for tax in taxes_grouped.values():
            tax_lines += tax_lines.new(tax)
        self.tax_line_ids = tax_lines
        return


    @api.multi
    def compute_taxes(self):
        ctx = dict(self._context)
        for invoice in self:
            # Delete non-manual tax lines Ret. IVA
            self._cr.execute("DELETE FROM account_invoice_tax WHERE invoice_id=%s AND manual is True and retiva_id not is False", (invoice.id,))
        return super(AccountInvoice,self).compute_taxes()

    def _prepare_retiva_line_vals(self, base_imponible):
        """ Prepare values to create an account.invoice.tax line

        The line parameter is an account.invoice.line, and the
        tax parameter is the output of account.tax.compute_all().
        """
        base = amount = 0
        retiva = self.retiva_id
        if not retiva:
            retiva = self.partner_id.retiva_id
        base, amount = retiva.get_retencion(base_imponible)

        vals = {
            'invoice_id': self.id,
            'name': retiva.name,
            'retiva_id': retiva.id,
            'amount': amount,
            'base': base,
            'manual': True,
            'sequence': 99,
            'account_analytic_id': False,
            'account_id': self.type in ('out_invoice', 'in_invoice') and (retiva.account_id.id) or (retiva.account_refund_id.id),
        }

        return vals

    @api.multi
    def get_taxes_values(self):
        tax_grouped = super(AccountInvoice,self).get_taxes_values()
        if not self.retiva_excluye:
            if self.type in ['in_invoice','in_refund']:
                monto_sujeto = 0
                for key in tax_grouped:
                    monto_sujeto += tax_grouped[key]['amount']
                if monto_sujeto != 0.00:
                    vals = self._prepare_retiva_line_vals(monto_sujeto)
                    key = '%s-%s-%s'%(vals['retiva_id'],vals['account_id'],vals['manual'])
                    if vals['amount'] != 0:
                        if key not in tax_grouped:
                            tax_grouped[key] = vals
                        else:
                            tax_grouped[key]['amount'] = vals['amount']
                            tax_grouped[key]['base'] = vals['base']
        return tax_grouped

    @api.multi
    def action_retiva_create(self):
        if self.type in ['in_invoice','in_refund']:
            for invoice in self:
                if invoice.partner_id.retiva_id:
                    if not invoice.partner_id.retiva_id.sequence_id:
                        raise UserError(_('Please define sequence on the retenencion de iva.'))
                    retiva = invoice.partner_id.retiva_id
                    sequence = retiva.sequence_id
                    new_name = sequence.with_context(ir_sequence_date=invoice.date_invoice).next_by_id()
                    invoice.number_retiva = new_name
                    invoice.retiva_id = invoice.partner_id.retiva_id.id

    #@api.multi
    def action_move_create(self):
        self.action_retiva_create()
        result = super(AccountInvoice,self).action_move_create()
        return result

    @api.multi
    def retiva_print(self):

        self.ensure_one()
        self.retiva_sent = True
        return self.env.ref('l10n_ve_retiva_softnetcorp.snc_account_invoices_retiva').report_action(self)



    @api.multi
    def action_retiva_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        template = self.env.ref('l10n_ve_retiva_softnetcorp.email_template_edi_retiva', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='account.invoice',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            custom_layout="l10n_ve_retiva_softnetcorp.mail_template_data_notification_email_account_retiva"
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }
    
class AccountInvoiceTax(models.Model):
    _inherit = "account.invoice.tax"

    @api.depends('date_retiva')
    def get_periodo(self):
        self.periodo = '%s%s'%(self.invoice_id.date.year,self.invoice_id.date.month)

    retiva_id = fields.Many2one('snc.retiva',string='Retencion de IVA')
    number_retiva = fields.Char('Comprobante Numero',related='invoice_id.number_retiva', store=True, readonly=True)
    date_retiva = fields.Date(string='Fecha de Comprobante',related="invoice_id.date", store=True, readonly=True)
    partner_id = fields.Many2one(string='Proveedor',related="invoice_id.partner_id", store=True, readonly=True)
    rif = fields.Char(string='Rif',related="partner_id.vat", store=True, readonly=True)
    total_factura = fields.Monetary(string='Total Factura',related="invoice_id.amount_total", store=True, readonly=True)
    impuesto_iva = fields.Monetary(string='Total IVA',related="invoice_id.amount_tax", store=True, readonly=True)
    base_imponible = fields.Monetary(string='Base Imponible',related="invoice_id.amount_untaxed", store=True, readonly=True)
    tipo = fields.Selection([
            ('in_invoice','01'),
            ('in_refund','03'),
        ], string='Tipo',related="invoice_id.type", store=True, readonly=True)
    periodo = fields.Char('Periodo',compute='_get_periodo', store=True, readonly=True)
    #currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id', store=True, readonly=True)
