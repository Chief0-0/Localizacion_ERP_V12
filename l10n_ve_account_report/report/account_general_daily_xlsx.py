# -*- coding: utf-8 -*-
##############################################################################
#
#
##############################################################################
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsxAbstract
from odoo import fields
import datetime
from time import gmtime, strftime
from odoo import _

class ReportGeneralDailytXls(ReportXlsxAbstract):
    
    def _get_account_move_entry(self, accounts, init_balance, sortby, display_account):
        """
        :param:
                accounts: the recordset of accounts
                init_balance: boolean value of initial_balance
                sortby: sorting by date or partner and journal
                display_account: type of account(receivable, payable and both)

        Returns a dictionary of accounts with following key and value {
                'code': account code,
                'name': account name,
                'debit': sum of total debit amount,
                'credit': sum of total credit amount,
                'balance': total balance,
                'amount_currency': sum of amount_currency,
                'move_lines': list of move line
        }
        """
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = dict(map(lambda x: (x, []), accounts.ids))

        # Prepare initial sql query and Get the initial move lines
        if init_balance:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=self.env.context.get('date_from'), date_to=False, initial_bal=True)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
            sql = ("""SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, NULL AS amount_currency, '' AS lref, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, '' AS lpartner_id,\
                '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                NULL AS currency_id,\
                '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                '' AS partner_name\
                FROM account_move_line l\
                LEFT JOIN account_move m ON (l.move_id=m.id)\
                LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                LEFT JOIN account_invoice i ON (m.id =i.move_id)\
                JOIN account_journal j ON (l.journal_id=j.id)\
                WHERE l.account_id IN %s""" + filters + ' GROUP BY l.account_id')
            params = (tuple(accounts.ids),) + tuple(init_where_params)
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                move_lines[row.pop('account_id')].append(row)

        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'

        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = MoveLine._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')

        # Get move lines base on sql query and Calculate the total balance of move lines
        sql = ('''SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id, l.amount_currency, l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,\
            m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name\
            FROM account_move_line l\
            JOIN account_move m ON (l.move_id=m.id)\
            LEFT JOIN res_currency c ON (l.currency_id=c.id)\
            LEFT JOIN res_partner p ON (l.partner_id=p.id)\
            JOIN account_journal j ON (l.journal_id=j.id)\
            JOIN account_account acc ON (l.account_id = acc.id) \
            WHERE l.account_id IN %s ''' + filters + ''' GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name ORDER BY ''' + sql_sort)
        params = (tuple(accounts.ids),) + tuple(where_params)
        cr.execute(sql, params)

        for row in cr.dictfetchall():
            balance = 0
            for line in move_lines.get(row['account_id']):
                balance += line['debit'] - line['credit']
            row['balance'] += balance
            move_lines[row.pop('account_id')].append(row)

        # Calculate the debit, credit and balance for Accounts
        account_res = []
        for account in accounts:
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['code'] = account.code
            res['name'] = account.name
            res['move_lines'] = move_lines[account.id]
            for line in res.get('move_lines'):
                res['debit'] += line['debit']
                res['credit'] += line['credit']
                res['balance'] = line['balance']
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)

        return account_res    

    def generate_xlsx_report(self, workbook, data, obj):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))

        init_balance = data['form'].get('initial_balance', True)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in self.env['account.journal'].search([('id', 'in', data['form']['journal_ids'])])]

        accounts = docs if self.model == 'account.account' else self.env['account.account'].search([])
        accounts_res = self._get_account_move_entry(accounts, init_balance, sortby, display_account)        
                
        report_name = "Libro Diario"
        current_date = strftime("%d-%m-%Y %H:%M:%S", gmtime())
        current_date = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M %p"))
        #current_date = context_timestamp(datetime.datetime.now()).strftime('%Y-%m-%d %H:%M')
        #date_doen = datetime.date.today()
        #current_date = datetime.strptime(date_done, "%d-%m-%Y %H:%M:%S")
        
        logged_users = self.env['res.users'].browse(1)
        logged_company = self.env['res.partner'].browse(1)
        sheet = workbook.add_worksheet(report_name)
        format1 = workbook.add_format({'font_size': 22, 'bg_color': '#D3D3D3'})
        format4 = workbook.add_format({'font_size': 22})
        format2 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3'})
        format22 = workbook.add_format({'font_size': 14})
        format23 = workbook.add_format({'font_size': 14, 'bold': True})
        format3 = workbook.add_format({'font_size': 10})
        format5 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
        format7 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
        format6 = workbook.add_format({'font_size': 22, 'bg_color': '#FFFFFF'})
        format66 = workbook.add_format({'font_size': 22, 'bg_color': '#FFFFFF'})
        format7.set_align('center')
        format66.set_align('center')
        sheet.write('A1', current_date, format3)
        vat = logged_company.company_id.vat if logged_company.company_id.vat else ''
        sheet.merge_range('B1:C1', logged_company.company_id.name, format66)
        sheet.merge_range('B2:C2', 'RIF:'+vat, format7)
        sheet.write('A3:A3', report_name, format6)
        if data['form']['date_from']:
            date_start = 'Desde: %s'%data['form']['date_from']
        else:
            date_start = 'Desde: '
        if data['form']['date_to']:
            date_end = data['form']['date_to']
        else:
            date_end = ""    
        sheet.write('A4', 'Periodo', format23)
        sheet.write('B4', date_start, format23)
        sheet.write('C4', 'Hasta:', format23)
        sheet.write('D4', date_end, format23)
        sheet.write('A6', _("Code"), format22)
        sheet.set_column('A:A', 15)
        sheet.write('B6', _("Descriptions"), format22)
        sheet.set_column('B:B', 55)
        sheet.write('C6', _("Debit"), format22)
        sheet.set_column('C:C', 20)
        sheet.write('D6', _("Credit"), format22)
        sheet.set_column('D:D', 20)
        row_initial = 6
        row_number = row_initial
        col_number = 0
        data_format1 = workbook.add_format({'bg_color': '#eaf4ff','font_size': 10})
        data_format2 = workbook.add_format({'bg_color': '#ffffff','font_size': 10})
        for values in accounts_res:         
            if row_number%2 == 0:
                sheet.set_row(row_number, cell_format=data_format1)
                format3 = data_format1
                money = workbook.add_format({'bg_color': '#eaf4ff','font_size': 10,'num_format': '#,##0.00'})
            else:
                sheet.set_row(row_number, cell_format=data_format2)
                format3 = data_format2
                money = workbook.add_format({'bg_color': '#ffffff','font_size': 10,'num_format': '#,##0.00'})
            sheet.write(row_number, col_number, values['code'], format3)
            sheet.write(row_number, col_number + 1, values['name'], format3)
            sheet.write(row_number, col_number + 2, values['debit'], money)
            sheet.write(row_number, col_number + 3, values['credit'], money)                   
            row_number += 1
        sheet.set_row(row_number, cell_format=format3,height=3)
        sheet.write(row_number, col_number, '', format3)
        money = workbook.add_format({'font_size': 10,'num_format': '#,##0.00', 'bold': True})
        sheet.write(row_number+1,col_number + 1, 'TOTAL', format3)          
        sheet.write(row_number+1,col_number + 2, '=SUM(C'+str(row_initial+1) +':C'+ str(row_number) + ')', money)
        sheet.write(row_number+1,col_number + 3, '=SUM(D'+str(row_initial+1) +':D'+ str(row_number) + ')', money)
        workbook.close()        
    

ReportGeneralDailytXls('report.l10n_ve_account_report.report_generaldaily.xlsx', 'account.report.general.daily')