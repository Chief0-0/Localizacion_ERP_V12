# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from datetime import datetime, timedelta

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
import openerp.addons.decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

import logging

import io
from io import BytesIO
from io import StringIO

import xlsxwriter
import shutil
import base64
import csv

_logger = logging.getLogger(__name__)

class resumen_iva(models.TransientModel):
    _name = "account.wizard.resumen.iva" ## = nombre de la carpeta.nombre del archivo deparado con puntos

    facturas_ids = fields.Many2many('account.invoice', string='Facturas', store=True) ##Relacion con el modelo de la vista de la creacion de facturas
    retiva_ids = fields.Many2many('snc.retiva.partners.lines', string='Retiva', store=True)

    date_from = fields.Date('Date From') # creacion de campo de fecha de entrada
    date_to = fields.Date('Date To') # creacion de campo de fecha de salida

    item_21_inic = fields.Integer('Exedente Creditos Fiscales de la Semana Anterior')
    item_33_inic = fields.Integer('Retenciones IVA Acumulados por Descontar')


    # fields for download xls
    state = fields.Selection([('choose', 'choose'), ('get', 'get')],default='choose') ##Genera los botones de exportar xls y pdf como tambien el de cancelar
    report = fields.Binary('Prepared file', filters='.xls', readonly=True)
    name = fields.Char('File Name', size=32)
    company_id = fields.Many2one('res.company','Company',default=lambda self: self.env.user.company_id.id)

    #resumen_ids = fields.Many2many('datos.resumen.declaracion.iva', string='Resumen')

    tot_execto_mes_v = fields.Char('tot_execto_mes_v')

    # Calculos de Ventas item 1 - 9 DÉBITOS FISCALES
    # Ventas Internas no Gravadas item 1

    # Ventas Internas Gravadas por Alicuota General item 3
    tot_alicu_general_base_v = fields.Char('tot_alicu_general_b,ase_v')
    tot_alicu_general_debi_v = fields.Char('tot_alicu_general_debi_v')
    tot_alicu_general_reten_v = fields.Char('tot_alicu_general_reten_v')

    # Ventas Internas Gravadas por Alicuota General más Adicional item 4
    tot_alicu_gener_adic_base_v = fields.Char('tot_alicu_gener_adic_base_v')
    tot_alicu_gener_adic_debi_v = fields.Char('tot_alicu_gener_adic_debi_v')
    tot_alicu_gener_adic_reten_v = fields.Char('tot_alicu_gener_adic_reten_v')

    # Ventas Internas Gravadas por Alicuota Reducida item 5
    tot_alicu_reducida_base_v = fields.Char('tot_alicu_reducida_base_v')
    tot_alicu_reducida_debi_v = fields.Char('tot_alicu_reducida_debi_v')
    tot_alicu_reducida_reten_v = fields.Char('tot_alicu_reducida_reten_v')

    # Total Ventas y Debitos Fiscales para Efectos de Determinación item 6   # item para el item 9
    tot_vet_efect_determ_base = fields.Char('tot_vet_efect_determ_base')
    tot_vet_efect_determ_debi = fields.Char('tot_vet_efect_determ_debi')

    # Calculos de Compras item 10 - 26 CRÉDITOS FISCALES
    # Compras no Gravadas y/o sin Derecho a Credito Fiscal item 10
    tot_execto_mes_c = fields.Char('tot_execto_mes_c')
    # Compras Gravadas por Alicuota General item 14
    tot_alicu_general_base_c = fields.Char('tot_alicu_general_base_c')
    tot_alicu_general_debi_c = fields.Char('tot_alicu_general_debi_c')
    tot_alicu_general_reten_c = fields.Char('tot_alicu_general_reten_c')

    # Compras Gravadas por Alicuota General más Alicuota Adicional item 15
    tot_alicu_gener_adic_base_c = fields.Char('tot_alicu_gener_adic_base_c')
    tot_alicu_gener_adic_debi_c = fields.Char('tot_alicu_gener_adic_debi_c')
    tot_alicu_gener_adic_reten_c = fields.Char('tot_alicu_gener_adic_reten_c')

    # Compras Gravadas por Alicuota Reducida item 16
    tot_alicu_reducida_base_c = fields.Char('tot_alicu_reducida_base_c')
    tot_alicu_reducida_debi_c = fields.Char('tot_alicu_reducida_debi_c')
    tot_alicu_reducida_reten_c = fields.Char('tot_alicu_reducida_reten_c')

    # Total Compras y Créditos Fiscales del Período item 17
    tot_comp_fisc_periodo_base = fields.Char('tot_comp_fisc_periodo_base')
    tot_comp_fisc_periodo_debi = fields.Char('tot_comp_fisc_periodo_debi')

    # Créditos Fiscales Producto de la Aplicación del Porcentaje de la Prorrata item 19

    # Total Créditos Fiscales Deducibles item item 20 -> (item 18 - item 19)falta
    tot_credi_fisc_deduc = fields.Char('tot_credi_fisc_deduc ')

    # Exedente Créditos Fiscales del Mes Anterior item 21 -> Total del item 28 del mes anterior
    tot_exed_credi_fisc_m_ant = fields.Char('tot_exed_credi_fisc_m_ant')  # falta

    # Total Creditos Fiscales item 26 -> Total del item 20 al 25
    tot_credi_fiscales = fields.Char('tot_credi_fiscales')  # faltan

    ## AUTOLIQUIDACIÓN

    # Total Cuota Tributaria del Período item 27 -> resta el item 9 con el item 26, solo si 9 es mayor que el item 26
    tot_cuot_trib_periodo = fields.Char('tot_cuot_trib_periodo')

    # Exedente de Crédito Fiscal para el mes Siguiente item 28 -> resta del item 26 con el item 9, solo si 26 es mayor que el item 26
    exedente_credi_fiscal = fields.Char('exedente_credi_fiscal')

    # Sub- Total Impuesto a Pagar item 32 -> total de item 27
    sub_tot_autoliq = fields.Char('sub_tot_autoliq')

    ## RETENCIONES IVA
    # Retenciones IVA Acumuladas por Descontar item 33 ->  total de item 39 del mes anterior
    reten_iva_acumul_desc = fields.Char('reten_iva_acumul_desc')

    # Retenciones del IVA del Periodo item 34 -> retencion de iva de las ventas del mes
    tot_reten_iva_periodo = fields.Char('tot_reten_iva_periodo')

    # Total Retenciones del IVA item 37 -> suma de iten 33 al 36
    tot_reten_iva = fields.Char('tot_reten_iva')

    # Retenciones del IVA Soportadas y Descontadas item 38 -> colocar monto de items 32 si dicho monto es menor a items 37. Si items 32 es mayor a items 37 colocar monto de items 37
    reten_iva_soport_descont = fields.Char('reten_iva_soport_descont')

    # Saldo Retenciones del IVA no Aplicado item 39 -> item 37 - 38
    sald_reten_iva_no_apli = fields.Char('sald_reten_iva_no_apli')
    # Sub- Total Impuesto a Pagar item 40 -> resta de item 32 con 38
    sub_tot_reten_iva = fields.Char('sub_tot_reten_iva')

    ##PERCEPCIÓN
    # Saldo de Percepciones en Aduanas no Aplicado item 47
    sal_percep_adu_no_apli = fields.Char('sal_percep_adu_no_apli')

    # Total a Pagar item 48 -> resta del item 40 con 47
    total_a_pag_percepcion = fields.Char('total_a_pag_percepcion')

    fech_inic = fields.Char('Fecha Inicio')

    fech_fin = fields.Char('Fecha Fin')


    def cal_general(self):

        # Validacion de mes
        date_from = str(self.date_from)

        fech_inic = datetime.strftime(datetime.strptime(date_from,DEFAULT_SERVER_DATE_FORMAT),"%d-%m-%Y")
        fech_fin = datetime.strftime(datetime.strptime(date_from,DEFAULT_SERVER_DATE_FORMAT),"%d-%m-%Y")

        dia_inic = datetime.strftime(datetime.strptime(date_from,DEFAULT_SERVER_DATE_FORMAT),"%d")
        dia_fin = datetime.strftime(datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT), "%d")

        mes_inic = datetime.strftime(datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT), "%m")
        mes_fin = datetime.strftime(datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT), "%m")

        anno_inic = datetime.strftime(datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT), "%Y")
        anno_fin = datetime.strftime(datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT), "%Y")

        #Configuracion de la semana anterior

        #   En Fe Mz Ab My Jn Jl Ag Sp Oc Nv Dc
        l = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        gi = "-"

        dia_inic = int(dia_inic)
        dia_fin = int(dia_fin)

        mes_inic = int(mes_inic)
        mes_fin = int(mes_fin)

        anno_inic = int(anno_inic)
        anno_fin = int(anno_fin)

        anno_inic = int(anno_inic)
        anno_fin = int(anno_fin)
        mes_inic = int(mes_inic)
        mes_fin = int(mes_fin)
        dia_inic = int(dia_inic)
        dia_fin = int(dia_fin)

        # calcular la cantidad de dias

        if mes_inic == mes_fin:
            dias = dia_fin - dia_inic + 1
        else:
            dia_m = dia_fin
            dmf = l[mes_inic - 1]
            if dia_inic == dmf:
                dia_m_2 = 1
            else:
                dia_m_2 = dmf - dia_inic + 1
            dias = dia_m + dia_m_2

        # calcular semana anterior

        # fecha final de la semana anterior

        if dia_inic - 1 != 0:
            dia_fin_sem = dia_inic - 1
            mes_fin_sem = mes_inic
            sem_ant_fin = ('{}{}{}{}{}'.format(dia_fin_sem, gi, mes_inic, gi, anno_inic))
            # prueba = "14-07-2014"
            sem_ant_fin = datetime.strptime(sem_ant_fin, '%d-%m-%Y')
        else:
            mes_fin_sem = mes_inic - 1
            dia_fin_sem = l[mes_fin_sem]
            sem_ant_fin = ('{}{}{}{}{}'.format(dia_fin_sem, gi, mes_fin_sem, gi, anno_inic))
            # prueba = "14-07-2014"
            sem_ant_fin = datetime.strptime(str(sem_ant_fin), '%d-%m-%Y')

        dia_inic_sem = dia_fin_sem
        mes_inic_sem = mes_fin_sem
        # semana inicial del mes anterior

        for i in range(0, 5):
            dia_inic_sem = dia_inic_sem - 1
            if dia_inic_sem == 1:
                mes_inic_sem = mes_inic_sem - 1
                dia_inic_sem = l[mes_inic_sem]

        sem_ant_inic = ('{}{}{}{}{}'.format(dia_inic_sem, gi, mes_inic_sem, gi, anno_inic))
        # prueba = "14-07-2014"
        sem_ant_inic = datetime.strptime(str(sem_ant_inic), '%d-%m-%Y')

        #sem_ant_inic = datetime.strftime(datetime.strptime(sem_ant_inic,DEFAULT_SERVER_DATE_FORMAT),"%d-%m-%Y")
        #sem_ant_fin = datetime.strftime(datetime.strptime(sem_ant_fin,DEFAULT_SERVER_DATE_FORMAT),"%d-%m-%Y")


        #Calculos de la semana anterior

        invoices_v = self.env['account.invoice'].search([('date_invoice', '>=', sem_ant_inic), ('date_invoice', '<=', sem_ant_fin), ('type', '!=', 'in_invoice'),('type', '!=', 'in_refund'), ('state', '!=', 'draft'), ('state', '!=', 'cancel')])

        invoices_c = self.env['account.invoice'].search([('date', '>=', sem_ant_inic), ('date', '<=', sem_ant_fin), ('type', '!=', 'out_invoice'),('type', '!=', 'out_refund'), ('state', '!=', 'draft'), ('state', '!=', 'cancel')])

        tot_execto_mes_v = 0

        tot_alicu_general_base_v = 0
        tot_alicu_general_debi_v = 0
        tot_alicu_general_reten_v = 0

        tot_alicu_reducida_base_v = 0
        tot_alicu_reducida_debi_v = 0
        tot_alicu_reducida_reten_v = 0

        tot_alicu_gener_adic_base_v = 0
        tot_alicu_gener_adic_debi_v = 0
        tot_alicu_gener_adic_reten_v = 0

        # Calculos de Ventas item 1 - 9 DÉBITOS FISCALES
        for invoice_v in invoices_v:

            ids_accounts = invoice_v.id
            for l in invoice_v.invoice_line_ids:
                if l.invoice_id.id == ids_accounts:

                    if invoice_v.origin == 0:
                        if l.invoice_line_tax_ids.amount == 0:

                            # Ventas Internas no Gravadas item 1
                            tot_execto_mes_v += l.price_subtotal

                        elif l.invoice_line_tax_ids.amount != 0:

                            # Calculos de Alicuaotas
                            alicuota_v = ((l.price_subtotal * l.invoice_line_tax_ids.amount) / 100)

                            # Calculos de Retencion
                            reten_iva_v = ((alicuota_v * invoice_v.retiva_id.porc_ret) / 100)

                            # Ventas Internas Gravadas por Alicuota General item 3
                            # Iva General
                            if l.invoice_line_tax_ids.amount == 16 or l.invoice_line_tax_ids.amount == 12:
                                tot_alicu_general_base_v += l.price_subtotal  # Base imponible
                                tot_alicu_general_debi_v += alicuota_v  # DÉBITO FISCAL
                                tot_alicu_general_reten_v += reten_iva_v

                            # Ventas Internas Gravadas por Alicuota General más Adicional item 4
                            # Iva general + adicional 16% + 15%
                            elif l.invoice_line_tax_ids.amount == 31:
                                tot_alicu_gener_adic_base_v += l.price_subtotal  # Base imponible
                                tot_alicu_gener_adic_debi_v += alicuota_v  # DÉBITO FISCAL
                                tot_alicu_gener_adic_reten_v += reten_iva_v

                            # Ventas Internas Gravadas por Alicuota Reducida item 5
                            # Iva Reducido
                            elif l.invoice_line_tax_ids.amount == 8:
                                tot_alicu_reducida_base_v += l.price_subtotal  # Base imponible
                                tot_alicu_reducida_debi_v += alicuota_v  # DÉBITO FISCAL
                                tot_alicu_reducida_reten_v += reten_iva_v

                    else:
                        if l.invoice_line_tax_ids.amount == 0:

                            tot_execto_mes_v -= l.price_subtotal

                        elif l.invoice_line_tax_ids.amount != 0:

                            # Calculos de Alicuaotas
                            alicuota_v = ((l.price_subtotal * l.invoice_line_tax_ids.amount) / 100)

                            # Calculos de Retencion
                            reten_iva_v = ((alicuota_v * invoice_v.retiva_id.porc_ret) / 100)

                            # Ventas Internas Gravadas por Alicuota General item 3
                            # Iva General
                            if l.invoice_line_tax_ids.amount == 16 or l.invoice_line_tax_ids.amount == 12:
                                tot_alicu_general_base_v -= l.price_subtotal  # Base imponible
                                tot_alicu_general_debi_v -= alicuota_v  # DÉBITO FISCAL
                                tot_alicu_general_reten_v -= reten_iva_v

                            # Ventas Internas Gravadas por Alicuota General más Adicional item 4
                            # Iva general + adicional 16% + 15%
                            elif l.invoice_line_tax_ids.amount == 31:
                                tot_alicu_gener_adic_base_v -= l.price_subtotal  # Base imponible
                                tot_alicu_gener_adic_debi_v -= alicuota_v  # DÉBITO FISCAL
                                tot_alicu_gener_adic_reten_v -= reten_iva_v

                            # Ventas Internas Gravadas por Alicuota Reducida item 5
                            # Iva Reducido
                            elif l.invoice_line_tax_ids.amount == 8:
                                tot_alicu_reducida_base_v -= l.price_subtotal  # Base imponible
                                tot_alicu_reducida_debi_v -= alicuota_v  # DÉBITO FISCAL
                                tot_alicu_reducida_reten_v -= reten_iva_v

        # Total Ventas y Debitos Fiscales para Efectos de Determinación item 6   # item para el item 9
        tot_vet_efect_determ_base = (
                    tot_execto_mes_v + tot_alicu_general_base_v + tot_alicu_gener_adic_base_v + tot_alicu_reducida_base_v)
        tot_vet_efect_determ_debi = (
                    tot_alicu_general_debi_v + tot_alicu_gener_adic_debi_v + tot_alicu_reducida_debi_v)  # item para el item 9

        # Calculos de Compras item 10 - 26 CRÉDITOS FISCALES

        tot_execto_mes_c = 0

        tot_alicu_general_base_c = 0
        tot_alicu_general_debi_c = 0
        tot_alicu_general_reten_c = 0

        tot_alicu_reducida_base_c = 0
        tot_alicu_reducida_debi_c = 0
        tot_alicu_reducida_reten_c = 0

        tot_alicu_gener_adic_base_c = 0
        tot_alicu_gener_adic_debi_c = 0
        tot_alicu_gener_adic_reten_c = 0

        tot_cuot_trib_periodo = 0
        exedente_credi_fiscal = 0
        reten_iva_soport_descont = 0

        for invoice_c in invoices_c:

            ids_accounts = invoice_c.id

            for l in invoice_c.invoice_line_ids:
                if l.invoice_id.id == ids_accounts:
                    if l.invoice_line_tax_ids.amount == 0:

                        # Compras no Gravadas y/o sin Derecho a Credito Fiscal item 10
                        tot_execto_mes_c += l.price_subtotal

                    elif l.invoice_line_tax_ids.amount != 0:

                        # Calculos de Alicuaotas
                        alicuota_c = ((l.price_subtotal * l.invoice_line_tax_ids.amount) / 100)

                        # Calculos de Retencion
                        reten_iva_c = ((alicuota_c * invoice_c.retiva_id.porc_ret) / 100)

                        # Compras Gravadas por Alicuota General item 14
                        # Iva General
                        if l.invoice_line_tax_ids.amount == 16 or l.invoice_line_tax_ids.amount == 12:
                            tot_alicu_general_base_c += l.price_subtotal  # Base imponible
                            tot_alicu_general_debi_c += alicuota_c  # DÉBITO FISCAL
                            # tot_alicu_general_reten_c += reten_iva_c

                        # Compras Gravadas por Alicuota General más Alicuota Adicional item 15
                        # Iva general + adicional 16% + 15%
                        elif l.invoice_line_tax_ids.amount == 31:
                            tot_alicu_gener_adic_base_c += l.price_subtotal  # Base imponible
                            tot_alicu_gener_adic_debi_c += alicuota_c  # DÉBITO FISCAL
                            # tot_alicu_gener_adic_reten_c += reten_iva_c

                        # Compras Gravadas por Alicuota Reducida item 16
                        # Iva Reducido
                        elif l.invoice_line_tax_ids.amount == 8:
                            tot_alicu_reducida_base_c += l.price_subtotal  # Base imponible
                            tot_alicu_reducida_debi_c += alicuota_c  # DÉBITO FISCAL
                            # tot_alicu_reducida_reten_c += reten_iva_c

                else:

                    if l.invoice_line_tax_ids.amount == 0:

                        tot_execto_mes_c -= l.price_subtotal

                    elif l.invoice_line_tax_ids.amount != 0:

                        # Calculos de Alicuaotas
                        alicuota_c = ((l.price_subtotal * l.invoice_line_tax_ids.amount) / 100)

                        # Calculos de Retencion
                        reten_iva_c = ((alicuota_c * invoice_c.retiva_id.porc_ret) / 100)

                        # Compras Gravadas por Alicuota General item 14
                        # Iva General
                        if l.invoice_line_tax_ids.amount == 16 or l.invoice_line_tax_ids.amount == 12:
                            tot_alicu_general_base_c -= l.price_subtotal  # Base imponible
                            tot_alicu_general_debi_c -= alicuota_c  # DÉBITO FISCAL
                            # tot_alicu_general_reten_c -= reten_iva_c

                        # Compras Gravadas por Alicuota General más Alicuota Adicional item 15
                        # Iva general + adicional 16% + 15%
                        elif l.invoice_line_tax_ids.amount == 31:
                            tot_alicu_gener_adic_base_c -= l.price_subtotal  # Base imponible
                            tot_alicu_gener_adic_debi_c -= alicuota_c  # DÉBITO FISCAL
                            # tot_alicu_gener_adic_reten_c -= reten_iva_c

                        # Compras Gravadas por Alicuota Reducida item 16
                        # Iva Reducido
                        elif l.invoice_line_tax_ids.amount == 8:
                            tot_alicu_reducida_base_c -= l.price_subtotal  # Base imponible
                            tot_alicu_reducida_debi_c -= alicuota_c  # DÉBITO FISCAL
                            # tot_alicu_reducida_reten_c -= reten_iva_c

        # Total Compras y Créditos Fiscales del Período item 17
        tot_comp_fisc_periodo_base = (
                    tot_execto_mes_c + tot_alicu_general_base_c + tot_alicu_gener_adic_base_c + tot_alicu_reducida_base_c)
        tot_comp_fisc_periodo_debi = (
                    tot_alicu_general_debi_c + tot_alicu_gener_adic_debi_c + tot_alicu_reducida_debi_c)  # Creditos Fiscales Totalmente Deducibles item 18

        # Créditos Fiscales Producto de la Aplicación del Porcentaje de la Prorrata

        # Total Créditos Fiscales Deducibles item item 20 -> (item 18 - item 19)falta
        tot_credi_fisc_deduc = tot_comp_fisc_periodo_debi

        # Exedente Créditos Fiscales del Mes Anterior item 21 -> Total del item 28 del mes anterior
        tot_exed_credi_fisc_m_ant = 0  # falta

        # Total Creditos Fiscales item 26 -> Total del item 20 al 25
        tot_credi_fiscales = (tot_credi_fisc_deduc + tot_exed_credi_fisc_m_ant)  # faltan

        ## AUTOLIQUIDACIÓN

        # Total Cuota Tributaria del Período item 27 -> resta el item 9 con el item 26, solo si 9 es mayor que el item 26
        if tot_vet_efect_determ_debi > tot_credi_fiscales:
            tot_cuot_trib_periodo = tot_vet_efect_determ_debi - tot_credi_fiscales
        else:
            tot_cuot_trib_periodo = 0

        # Exedente de Crédito Fiscal para el mes Siguiente item 28 -> resta del item 26 con el item 9, solo si 26 es mayor que el item 26
        if tot_credi_fiscales > tot_vet_efect_determ_debi:
            exedente_credi_fiscal = tot_credi_fiscales - tot_vet_efect_determ_debi
        else:
            exedente_credi_fiscal = 0

        # Sub- Total Impuesto a Pagar item 32 -> total de item 27
        sub_tot_autoliq = tot_cuot_trib_periodo

        ## RETENCIONES IVA

        # Retenciones IVA Acumuladas por Descontar item 33 ->  total de item 39 del mes anterior
        reten_iva_acumul_desc = 0

        # Retenciones del IVA del Periodo item 34 -> retencion de iva de las ventas del mes
        tot_reten_iva_periodo = (tot_alicu_general_reten_v + tot_alicu_gener_adic_reten_v + tot_alicu_reducida_reten_v)

        # Total Retenciones del IVA item 37 -> suma de iten 33 al 36
        tot_reten_iva = (reten_iva_acumul_desc + tot_reten_iva_periodo)

        # Retenciones del IVA Soportadas y Descontadas item 38 -> colocar monto de items 32 si dicho monto es menor a items 37. Si items 32 es mayor a items 37 colocar monto de items 37
        if tot_reten_iva > sub_tot_autoliq:  # item37 - 32
            reten_iva_soport_descont = sub_tot_autoliq

        elif sub_tot_autoliq > tot_reten_iva:  # item 32 - 37
            reten_iva_soport_descont = tot_reten_iva

        # Saldo Retenciones del IVA no Aplicado item 39 -> item 37 - 38
        sald_reten_iva_no_apli = (tot_reten_iva - reten_iva_soport_descont)

        # Valores que se tomaran para el resumen de la semana actual

        # Item 28 de la semana anterior para el item 21 actual
        exedente_credi_fiscal_sem_ant = exedente_credi_fiscal

        ### Item 39 de la semana anterior para el item 33 actual
        sald_reten_iva_no_apli_sem_ant = sald_reten_iva_no_apli



        validacion = self.env['account.wizard.resumen.iva'].search([('fech_inic', '=', sem_ant_inic), ('fech_fin', '=', sem_ant_fin)])

        if validacion:
            exedente_credi_fiscal_sem_ant = validacion.exedente_credi_fiscal
            sald_reten_iva_no_apli_sem_ant = validacion.sald_reten_iva_no_apli

        else:
            if self.item_21_inic != 0 or self.item_33_inic != 0:
                exedente_credi_fiscal_sem_ant = self.item_21_inic
                sald_reten_iva_no_apli_sem_ant = self.item_33_inic

                self.exedente_credi_fiscal = exedente_credi_fiscal_sem_ant
                self.sald_reten_iva_no_apli = sald_reten_iva_no_apli_sem_ant




        # Searching for customer invoices Actual
        invoices_v = self.env['account.invoice'].search([('date_invoice', '<=', self.date_to), ('date_invoice', '>=', self.date_from), ('type', '!=', 'in_invoice'),('type', '!=', 'in_refund'), ('state', '!=', 'draft'), ('state', '!=', 'cancel')])

        invoices_c = self.env['account.invoice'].search([('date', '<=', self.date_to), ('date', '>=', self.date_from),('type', '!=', 'out_invoice'), ('type', '!=', 'out_refund'), ('state', '!=', 'draft'),('state', '!=', 'cancel')])

        tot_execto_mes_v = 0

        tot_alicu_general_base_v = 0
        tot_alicu_general_debi_v = 0
        tot_alicu_general_reten_v = 0

        tot_alicu_reducida_base_v = 0
        tot_alicu_reducida_debi_v = 0
        tot_alicu_reducida_reten_v = 0

        tot_alicu_gener_adic_base_v = 0
        tot_alicu_gener_adic_debi_v = 0
        tot_alicu_gener_adic_reten_v = 0

        # Calculos de Ventas item 1 - 9 DÉBITOS FISCALES
        for invoice_v in invoices_v:

            ids_accounts = invoice_v.id
            for l in invoice_v.invoice_line_ids:
                if l.invoice_id.id == ids_accounts:

                        if invoice_v.origin == 0:
                            if l.invoice_line_tax_ids.amount == 0:

                                # Ventas Internas no Gravadas item 1
                                tot_execto_mes_v += l.price_subtotal

                            elif l.invoice_line_tax_ids.amount != 0:

                                # Calculos de Alicuaotas
                                alicuota_v = ((l.price_subtotal * l.invoice_line_tax_ids.amount) / 100)

                                # Calculos de Retencion
                                reten_iva_v = ((alicuota_v * invoice_v.retiva_id.porc_ret) / 100)

                                # Ventas Internas Gravadas por Alicuota General item 3
                                # Iva General
                                if l.invoice_line_tax_ids.amount == 16 or l.invoice_line_tax_ids.amount == 12:
                                    tot_alicu_general_base_v += l.price_subtotal  # Base imponible
                                    tot_alicu_general_debi_v += alicuota_v  # DÉBITO FISCAL
                                    tot_alicu_general_reten_v += reten_iva_v

                                # Ventas Internas Gravadas por Alicuota General más Adicional item 4
                                # Iva general + adicional 16% + 15%
                                elif l.invoice_line_tax_ids.amount == 31:
                                    tot_alicu_gener_adic_base_v += l.price_subtotal  # Base imponible
                                    tot_alicu_gener_adic_debi_v += alicuota_v  # DÉBITO FISCAL
                                    tot_alicu_gener_adic_reten_v += reten_iva_v

                                # Ventas Internas Gravadas por Alicuota Reducida item 5
                                # Iva Reducido
                                elif l.invoice_line_tax_ids.amount == 8:
                                    tot_alicu_reducida_base_v += l.price_subtotal  # Base imponible
                                    tot_alicu_reducida_debi_v += alicuota_v  # DÉBITO FISCAL
                                    tot_alicu_reducida_reten_v += reten_iva_v

                        else:
                            if l.invoice_line_tax_ids.amount == 0:

                                tot_execto_mes_v -= l.price_subtotal

                            elif l.invoice_line_tax_ids.amount != 0:

                                # Calculos de Alicuaotas
                                alicuota_v = ((l.price_subtotal * l.invoice_line_tax_ids.amount) / 100)

                                # Calculos de Retencion
                                reten_iva_v = ((alicuota_v * invoice_v.retiva_id.porc_ret) / 100)

                                # Ventas Internas Gravadas por Alicuota General item 3
                                # Iva General
                                if l.invoice_line_tax_ids.amount == 16 or l.invoice_line_tax_ids.amount == 12:
                                    tot_alicu_general_base_v -= l.price_subtotal  # Base imponible
                                    tot_alicu_general_debi_v -= alicuota_v  # DÉBITO FISCAL
                                    tot_alicu_general_reten_v -= reten_iva_v

                                # Ventas Internas Gravadas por Alicuota General más Adicional item 4
                                # Iva general + adicional 16% + 15%
                                elif l.invoice_line_tax_ids.amount == 31:
                                    tot_alicu_gener_adic_base_v -= l.price_subtotal  # Base imponible
                                    tot_alicu_gener_adic_debi_v -= alicuota_v  # DÉBITO FISCAL
                                    tot_alicu_gener_adic_reten_v -= reten_iva_v

                                # Ventas Internas Gravadas por Alicuota Reducida item 5
                                # Iva Reducido
                                elif l.invoice_line_tax_ids.amount == 8:
                                    tot_alicu_reducida_base_v -= l.price_subtotal  # Base imponible
                                    tot_alicu_reducida_debi_v -= alicuota_v  # DÉBITO FISCAL
                                    tot_alicu_reducida_reten_v -= reten_iva_v

        # Total Ventas y Debitos Fiscales para Efectos de Determinación item 6 al 8  # item para el item 9
        tot_vet_efect_determ_base = (tot_execto_mes_v + tot_alicu_general_base_v + tot_alicu_gener_adic_base_v + tot_alicu_reducida_base_v)
        tot_vet_efect_determ_debi = (tot_alicu_general_debi_v + tot_alicu_gener_adic_debi_v + tot_alicu_reducida_debi_v)  # item para el item 9

        # Calculos de Compras item 10 - 26 CRÉDITOS FISCALES

        tot_execto_mes_c = 0

        tot_alicu_general_base_c = 0
        tot_alicu_general_debi_c = 0
        tot_alicu_general_reten_c = 0

        tot_alicu_reducida_base_c = 0
        tot_alicu_reducida_debi_c = 0
        tot_alicu_reducida_reten_c = 0

        tot_alicu_gener_adic_base_c = 0
        tot_alicu_gener_adic_debi_c = 0
        tot_alicu_gener_adic_reten_c = 0

        tot_cuot_trib_periodo = 0
        exedente_credi_fiscal = 0
        reten_iva_soport_descont = 0


        for invoice_c in invoices_c:

            ids_accounts = invoice_c.id

            for l in invoice_c.invoice_line_ids:
                if l.invoice_id.id == ids_accounts:
                    if l.invoice_line_tax_ids.amount == 0:

                        # Compras no Gravadas y/o sin Derecho a Credito Fiscal item 10
                        tot_execto_mes_c += l.price_subtotal

                    elif l.invoice_line_tax_ids.amount != 0:

                        # Calculos de Alicuaotas
                        alicuota_c = ((l.price_subtotal * l.invoice_line_tax_ids.amount) / 100)

                        # Calculos de Retencion
                        reten_iva_c = ((alicuota_c * invoice_c.retiva_id.porc_ret) / 100)

                        # Compras Gravadas por Alicuota General item 14
                        # Iva General
                        if l.invoice_line_tax_ids.amount == 16 or l.invoice_line_tax_ids.amount == 12:
                            tot_alicu_general_base_c += l.price_subtotal  # Base imponible
                            tot_alicu_general_debi_c += alicuota_c  # DÉBITO FISCAL
                            # tot_alicu_general_reten_c += reten_iva_c

                        # Compras Gravadas por Alicuota General más Alicuota Adicional item 15
                        # Iva general + adicional 16% + 15%
                        elif l.invoice_line_tax_ids.amount == 31:
                            tot_alicu_gener_adic_base_c += l.price_subtotal  # Base imponible
                            tot_alicu_gener_adic_debi_c += alicuota_c  # DÉBITO FISCAL
                            # tot_alicu_gener_adic_reten_c += reten_iva_c

                        # Compras Gravadas por Alicuota Reducida item 16
                        # Iva Reducido
                        elif l.invoice_line_tax_ids.amount == 8:
                            tot_alicu_reducida_base_c += l.price_subtotal  # Base imponible
                            tot_alicu_reducida_debi_c += alicuota_c  # DÉBITO FISCAL
                            # tot_alicu_reducida_reten_c += reten_iva_c

                else:

                    if l.invoice_line_tax_ids.amount == 0:

                        tot_execto_mes_c -= l.price_subtotal

                    elif l.invoice_line_tax_ids.amount != 0:

                        # Calculos de Alicuaotas
                        alicuota_c = ((l.price_subtotal * l.invoice_line_tax_ids.amount) / 100)

                        # Calculos de Retencion
                        reten_iva_c = ((alicuota_c * invoice_c.retiva_id.porc_ret) / 100)

                        # Compras Gravadas por Alicuota General item 14
                        # Iva General
                        if l.invoice_line_tax_ids.amount == 16 or l.invoice_line_tax_ids.amount == 12:
                            tot_alicu_general_base_c -= l.price_subtotal  # Base imponible
                            tot_alicu_general_debi_c -= alicuota_c  # DÉBITO FISCAL
                            # tot_alicu_general_reten_c -= reten_iva_c

                        # Compras Gravadas por Alicuota General más Alicuota Adicional item 15
                        # Iva general + adicional 16% + 15%
                        elif l.invoice_line_tax_ids.amount == 31:
                            tot_alicu_gener_adic_base_c -= l.price_subtotal  # Base imponible
                            tot_alicu_gener_adic_debi_c -= alicuota_c  # DÉBITO FISCAL
                            # tot_alicu_gener_adic_reten_c -= reten_iva_c

                        # Compras Gravadas por Alicuota Reducida item 16
                        # Iva Reducido
                        elif l.invoice_line_tax_ids.amount == 8:
                            tot_alicu_reducida_base_c -= l.price_subtotal  # Base imponible
                            tot_alicu_reducida_debi_c -= alicuota_c  # DÉBITO FISCAL
                            # tot_alicu_reducida_reten_c -= reten_iva_c

        # Total Compras y Créditos Fiscales del Período item 17
        tot_comp_fisc_periodo_base = (tot_execto_mes_c + tot_alicu_general_base_c + tot_alicu_gener_adic_base_c + tot_alicu_reducida_base_c)
        tot_comp_fisc_periodo_debi = (tot_alicu_general_debi_c + tot_alicu_gener_adic_debi_c + tot_alicu_reducida_debi_c)  # Creditos Fiscales Totalmente Deducibles item 18

        # Créditos Fiscales Producto de la Aplicación del Porcentaje de la Prorrata

        # Total Créditos Fiscales Deducibles item item 20 -> (item 18 - item 19)falta
        tot_credi_fisc_deduc = tot_comp_fisc_periodo_debi

        # Exedente Créditos Fiscales del Mes Anterior item 21 -> Total del item 28 del mes anterior
        tot_exed_credi_fisc_m_ant = exedente_credi_fiscal_sem_ant  # falta

        # Total Creditos Fiscales item 26 -> Total del item 20 al 25
        tot_credi_fiscales = (tot_credi_fisc_deduc + tot_exed_credi_fisc_m_ant)  # faltan

        ## AUTOLIQUIDACIÓN

        # Total Cuota Tributaria del Período item 27 -> resta el item 9 con el item 26, solo si 9 es mayor que el item 26
        if tot_vet_efect_determ_debi > tot_credi_fiscales:
            tot_cuot_trib_periodo = tot_vet_efect_determ_debi - tot_credi_fiscales
        else:
            tot_cuot_trib_periodo = 0

        # Exedente de Crédito Fiscal para el mes Siguiente item 28 -> resta del item 26 con el item 9, solo si 26 es mayor que el item 26
        if tot_credi_fiscales > tot_vet_efect_determ_debi:
            exedente_credi_fiscal = tot_credi_fiscales - tot_vet_efect_determ_debi
        else:
            exedente_credi_fiscal = 0


        # Sub- Total Impuesto a Pagar item 32 -> total de item 27
        sub_tot_autoliq = tot_cuot_trib_periodo

        ## RETENCIONES IVA

        # Retenciones IVA Acumuladas por Descontar item 33 ->  total de item 39 del mes anterior
        reten_iva_acumul_desc = sald_reten_iva_no_apli_sem_ant

        # Retenciones del IVA del Periodo item 34 -> retencion de iva de las ventas del mes
        tot_reten_iva_periodo = (tot_alicu_general_reten_v + tot_alicu_gener_adic_reten_v + tot_alicu_reducida_reten_v)

        # Total Retenciones del IVA item 37 -> suma de iten 33 al 36
        tot_reten_iva = (reten_iva_acumul_desc + tot_reten_iva_periodo)

        # Retenciones del IVA Soportadas y Descontadas item 38 -> colocar monto de items 32 si dicho monto es menor a items 37. Si items 32 es mayor a items 37 colocar monto de items 37
        if tot_reten_iva > sub_tot_autoliq:  # item37 - 32
            reten_iva_soport_descont = sub_tot_autoliq

        elif sub_tot_autoliq > tot_reten_iva:  # item 32 - 37
            reten_iva_soport_descont = tot_reten_iva

        # Saldo Retenciones del IVA no Aplicado item 39 -> item 37 - 38
        sald_reten_iva_no_apli = (tot_reten_iva - reten_iva_soport_descont)

        # Sub- Total Impuesto a Pagar item 40 -> resta de item 32 con 38
        sub_tot_reten_iva = (sub_tot_autoliq - reten_iva_soport_descont)

        ##PERCEPCIÓN

        # Saldo de Percepciones en Aduanas no Aplicado item 47
        sal_percep_adu_no_apli = 0

        # Total a Pagar item 48 -> resta del item 40 con 47
        total_a_pag_percepcion = sub_tot_reten_iva - sal_percep_adu_no_apli

        #variables a guardar
        self.tot_execto_mes_v = tot_execto_mes_v

        # Calculos de Ventas item 1 - 9 DÉBITOS FISCALES
        # Ventas Internas no Gravadas item 1

        # Ventas Internas Gravadas por Alicuota General item 3
        self.tot_alicu_general_base_v = tot_alicu_general_base_v
        self.tot_alicu_general_debi_v = tot_alicu_general_debi_v
        self.tot_alicu_general_reten_v = tot_alicu_general_reten_v

        # Ventas Internas Gravadas por Alicuota General más Adicional item 4
        self.tot_alicu_gener_adic_base_v = tot_alicu_gener_adic_base_v
        self.tot_alicu_gener_adic_debi_v = tot_alicu_gener_adic_debi_v
        self.tot_alicu_gener_adic_reten_v = tot_alicu_gener_adic_reten_v

        # Ventas Internas Gravadas por Alicuota Reducida item 5
        self.tot_alicu_reducida_base_v = tot_alicu_reducida_base_v
        self.tot_alicu_reducida_debi_v = tot_alicu_reducida_debi_v
        self.tot_alicu_reducida_reten_v = tot_alicu_reducida_reten_v

        # Total Ventas y Debitos Fiscales para Efectos de Determinación item 6   # item para el item 9
        self.tot_vet_efect_determ_base = tot_vet_efect_determ_base
        self.tot_vet_efect_determ_debi = tot_vet_efect_determ_debi

        # Calculos de Compras item 10 - 26 CRÉDITOS FISCALES
        # Compras no Gravadas y/o sin Derecho a Credito Fiscal item 10
        self.tot_execto_mes_c = tot_execto_mes_c
        # Compras Gravadas por Alicuota General item 14
        self.tot_alicu_general_base_c = tot_alicu_general_base_c
        self.tot_alicu_general_debi_c = tot_alicu_general_debi_c
        self.tot_alicu_general_reten_c = tot_alicu_general_reten_c

        # Compras Gravadas por Alicuota General más Alicuota Adicional item 15
        self.tot_alicu_gener_adic_base_c = tot_alicu_gener_adic_base_c
        self.tot_alicu_gener_adic_debi_c = tot_alicu_gener_adic_debi_c
        self.tot_alicu_gener_adic_reten_c = tot_alicu_gener_adic_reten_c

        # Compras Gravadas por Alicuota Reducida item 16
        self.tot_alicu_reducida_base_c = tot_alicu_reducida_base_c
        self.tot_alicu_reducida_debi_c = tot_alicu_reducida_debi_c
        self.tot_alicu_reducida_reten_c = tot_alicu_reducida_reten_c

        # Total Compras y Créditos Fiscales del Período item 17
        self.tot_comp_fisc_periodo_base = tot_comp_fisc_periodo_base
        self.tot_comp_fisc_periodo_debi = tot_comp_fisc_periodo_debi

        # Créditos Fiscales Producto de la Aplicación del Porcentaje de la Prorrata item 19

        # Total Créditos Fiscales Deducibles item item 20 -> (item 18 - item 19)falta
        self.tot_credi_fisc_deduc = tot_credi_fisc_deduc

        # Exedente Créditos Fiscales del Mes Anterior item 21 -> Total del item 28 del mes anterior
        self.tot_exed_credi_fisc_m_ant = tot_exed_credi_fisc_m_ant  # falta

        # Total Creditos Fiscales item 26 -> Total del item 20 al 25
        self.tot_credi_fiscales = tot_credi_fiscales  # faltan

        ## AUTOLIQUIDACIÓN

        # Total Cuota Tributaria del Período item 27 -> resta el item 9 con el item 26, solo si 9 es mayor que el item 26
        self.tot_cuot_trib_periodo = tot_cuot_trib_periodo

        # Exedente de Crédito Fiscal para el mes Siguiente item 28 -> resta del item 26 con el item 9, solo si 26 es mayor que el item 26
        self.exedente_credi_fiscal = exedente_credi_fiscal

        # Sub- Total Impuesto a Pagar item 32 -> total de item 27
        self.sub_tot_autoliq = sub_tot_autoliq

        ## RETENCIONES IVA
        # Retenciones IVA Acumuladas por Descontar item 33 ->  total de item 39 del mes anterior
        self.reten_iva_acumul_desc = reten_iva_acumul_desc

        # Retenciones del IVA del Periodo item 34 -> retencion de iva de las ventas del mes
        self.tot_reten_iva_periodo = tot_reten_iva_periodo

        # Total Retenciones del IVA item 37 -> suma de iten 33 al 36
        self.tot_reten_iva = tot_reten_iva

        # Retenciones del IVA Soportadas y Descontadas item 38 -> colocar monto de items 32 si dicho monto es menor a items 37. Si items 32 es mayor a items 37 colocar monto de items 37
        self.reten_iva_soport_descont = reten_iva_soport_descont

        # Saldo Retenciones del IVA no Aplicado item 39 -> item 37 - 38
        self.sald_reten_iva_no_apli = sald_reten_iva_no_apli
        # Sub- Total Impuesto a Pagar item 40 -> resta de item 32 con 38
        self.sub_tot_reten_iva = sub_tot_reten_iva

        ##PERCEPCIÓN
        # Saldo de Percepciones en Aduanas no Aplicado item 47
        self.sal_percep_adu_no_apli = sal_percep_adu_no_apli

        # Total a Pagar item 48 -> resta del item 40 con 47
        self.total_a_pag_percepcion = total_a_pag_percepcion

        self.fech_inic = fech_inic
        self.fech_fin = fech_fin


    def get_invoice(self):
         self.resumen_ids = self.env['account.wizard.resumen.iva'].search([('fech_inic', '>=', self.date_from),('fech_fin', '<=', self.date_to)])
         _logger.info("\n\n\n {} \n\n\n".format(self.resumen_ids))


    @api.multi
    def print_facturas(self):
        self.cal_general()
        self.get_invoice()
        return {'type': 'ir.actions.report','report_name': 'resumen_declaracion_iva.libro_resumen_iva','report_type':"qweb-pdf"}


    @api.multi
    def cont_row(self):
        row = 0
        for record in self.facturas_ids:
            row +=1
        return row
