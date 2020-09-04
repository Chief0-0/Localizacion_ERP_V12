# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

#from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsxAbstract


class AccountReportGeneralLedger(models.TransientModel):
    _inherit = "account.common.account.report"
    _name = "account.report.general.daily"
    _description = "Libro Diario Report"

    initial_balance = fields.Boolean(string='Include Initial Balances',
                                    help='If you selected date, this field allow you to add a row to display the amount of debit/credit/balance that precedes the filter you\'ve set.')
    sortby = fields.Selection([('sort_date', 'Date'), ('sort_journal_partner', 'Journal & Partner')], string='Sort by', required=True, default='sort_date')
    journal_ids = fields.Many2many('account.journal', 'account_report_general_daily_journal_rel', 'account_id', 'journal_id', string='Journals', required=True)        

    
    def _print_report(self, data):

        
        context = self._context
        data = self.pre_print_report(data)
        data['form'].update(self.read(['initial_balance', 'sortby'])[0])
        if data['form'].get('initial_balance') and not data['form'].get('date_from'):
            raise UserError(_("You must define a Start Date"))
        records = self.env[data['model']].browse(data.get('ids', []))

        if context.get('xls_export'):            
            return {'type': 'ir.actions.report.xml',
                    'report_name': 'l10n_ve_account_report.report_generaldaily.xlsx',
                    'datas': data,
                    'name': 'Libro Diario'
                    }

        #return self.env.ref('l10n_ve_account_report.report_generaldaily').report_action(self, data=data)
        return {'type': 'ir.actions.report','report_name': 'l10n_ve_account_report.report_generaldaily','report_type':"qweb-pdf",'data': data}