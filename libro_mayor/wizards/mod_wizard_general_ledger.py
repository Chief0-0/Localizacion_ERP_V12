# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
import openerp.addons.decimal_precision as dp
import logging

import io
from io import BytesIO
from io import StringIO

import xlsxwriter
import shutil
import base64
import csv


class AccountReportGeneralLedger(models.TransientModel):
    _inherit = "account.report.general.ledger"
    _description = "General Ledger Report"

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update(self.read(['initial_balance', 'sortby'])[0])
        if data['form'].get('initial_balance') and not data['form'].get('date_from'):
            raise UserError(_("You must define a Start Date"))
        records = self.env[data['model']].browse(data.get('ids', []))

        return #self.env('accounting_pdf_reports.report_generalledger').report_action(records, data=data)
       # return self.env['report'].get_action(records, 'accounting_pdf_reports.report_generalledger', data=data)
