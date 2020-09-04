from datetime import datetime, timedelta
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
import openerp.addons.decimal_precision as dp
import logging

import io
from io import BytesIO

import xlsxwriter
import shutil
import base64
import csv
import xlwt

_logger = logging.getLogger(__name__)


class libro_ventas(models.TransientModel):
    _name = "account.wizard.libro.ventas" ## = nombre de la carpeta.nombre del archivo deparado con puntos

    facturas_ids = fields.Many2many('account.invoice', string='Facturas', store=True) ##Relacion con el modelo de la vista de la creacion de facturas
    retiva_ids = fields.Many2many('snc.retiva.partners.lines', string='Retiva', store=True) ## Malo

    tax_ids = fields.Many2many('account.invoice.tax', string='Facturas_1', store=True)

    #line_tax_ids = fields.Many2many('account.invoice.line.tax', string='Facturas_2', store=True)
    line_ids = fields.Many2many('account.invoice.line', string='Facturas_3', store=True)
    #invoice_ids = fields.Char(string="idss", related='facturas_ids.id')

    date_from = fields.Date('Date From') # creacion de campo de fecha de entrada
    date_to = fields.Date('Date To') # creacion de campo de fecha de salida

    # fields for download xls
    state = fields.Selection([('choose', 'choose'), ('get', 'get')],default='choose') ##Genera los botones de exportar xls y pdf como tambien el de cancelar
    report = fields.Binary('Prepared file', filters='.xls', readonly=True)
    name = fields.Char('File Name', size=32)
    company_id = fields.Many2one('res.company','Company',default=lambda self: self.env.user.company_id.id)

    def get_invoice(self):
        self.facturas_ids = self.env['account.invoice'].search([('date_invoice','>=',self.date_from),('date_invoice','<=', self.date_to),('type','!=','in_invoice'),('type','!=','in_refund'),('state','!=','draft'),('state','!=','cancel')], order = 'date_invoice ASC')
        _logger.info("\n\n\n {} \n\n\n".format(self.facturas_ids))

        self.retiva_ids = self.env['snc.retiva.partners.lines'].search([('monto_sujeto', '!=', 0)])
        _logger.info("\n\n\n {} \n\n\n".format(self.retiva_ids))


    @api.multi
    def print_facturas(self):
        self.get_invoice()
        return self.env.ref('libro_ventas.libro_factura_clientes').report_action(self)



    @api.multi
    def cont_row(self):
        row = 0
        for record in self.facturas_ids:
            row +=1
        return row


    @api.multi
    @api.depends('company_id')
    def generate_xls_report(self):

        self.ensure_one()

        wb1 = xlwt.Workbook(encoding='utf-8')
        ws1 = wb1.add_sheet('Invoices Details')
        fp = BytesIO()


        #Content/Text style
        header_content_style = xlwt.easyxf("font: name Helvetica size 20 px, bold 1, height 170;")
        sub_header_style = xlwt.easyxf("font: name Helvetica size 10 px, bold 1, height 170; borders: left thin, right thin, top thin, bottom thin;")
        sub_header_content_style = xlwt.easyxf("font: name Helvetica size 10 px, height 170;")
        line_content_style = xlwt.easyxf("font: name Helvetica, height 170;")
        row = 1
        col = 0
        ws1.row(row).height = 500
        ws1.write_merge(row,row, 2, 6, "Libro de Ventas", header_content_style)
        row += 2
        ws1.write_merge(row, row, 1, 2, "Razon Social :", sub_header_style)
        ws1.write_merge(row, row, 3, 5,  str(self.company_id.name), sub_header_content_style)
        row+=1
        ws1.write_merge(row, row, 1, 2, "RIF:", sub_header_style)
        ws1.write_merge(row, row, 3, 5,  str(self.company_id.vat), sub_header_content_style)
        row+=1
        ws1.write_merge(row, row, 1, 2, "Direccion Fiscal:", sub_header_style)
        ws1.write_merge(row, row, 3, 6, str(self.company_id.street), sub_header_content_style)
        row +=1
        ws1.write(row, col+1, "Desde :", sub_header_style)
        fec_desde = datetime.strftime(datetime.strptime(self.date_from,DEFAULT_SERVER_DATE_FORMAT),"%d/%m/%Y")
        ws1.write(row, col+2, fec_desde, sub_header_content_style)
        row += 1
        ws1.write(row, col+1, "Hasta :", sub_header_style)
        fec_hasta = datetime.strftime(datetime.strptime(self.date_to,DEFAULT_SERVER_DATE_FORMAT),"%d/%m/%Y")
        ws1.write(row, col+2, fec_hasta, sub_header_content_style)
        row += 2
        ws1.write_merge(row, row, 14, 16,"Ventas Internas o Exportacion Gravadas",sub_header_style)
        row += 1
        ws1.write(row,col+1,"#",sub_header_style)
        ws1.write(row,col+2,"Fecha Documento",sub_header_style)
        ws1.write(row,col+3,"RIF",sub_header_style)
        ws1.write(row,col+4,"Nombre Razon Social",sub_header_style)
        ws1.write(row,col+5,"Numero de Planilla de exportacion",sub_header_style)
        ws1.write(row,col+6,"Nro Factura / Entrega",sub_header_style)
        ws1.write(row,col+7,"Nro de Control",sub_header_style)
        ws1.write(row,col+8,"Numero de nota de credito ",sub_header_style)
        ws1.write(row,col+9,"Nro de nota de debito",sub_header_style)
        ws1.write(row,col+10,"Nro Factura Afectada",sub_header_style)
        ws1.write(row,col+11,"Ventas Incluyendo el IVA",sub_header_style)
        ws1.write(row,col+12,"Ventas internas o exoneraciones no gravadas",sub_header_style)
        ws1.write(row,col+13,"Ventas internas o exportaciones exoneradas",sub_header_style)
        ws1.write(row,col+14,"Base Imponible",sub_header_style)
        ws1.write(row,col+15,"'%'Alicuota",sub_header_style)
        ws1.write(row,col+16,"Impuesto IVA",sub_header_style)
        ws1.write(row,col+17,"IVA Retenido Comprador",sub_header_style)
        ws1.write(row,col+18,"Nro. Comprobante de Retencion",sub_header_style)
        ws1.write(row,col+19,"Fecha comp",sub_header_style)


        row += 1
        #Searching for customer invoices
        self.invoices = self.env['account.invoice'].search([('date_invoice','>=',self.date_from),('date_invoice','<=', self.date_to),('type','!=','in_invoice'),('type','!=','in_refund'),('state','!=','draft'),('state', '!=', 'cancel')], order = 'date_invoice ASC')
        _logger.info("\n\n\n {} \n\n\n".format(self.invoices))


        all_inv_total = 0
        num2 = 0
        total_internas = 0
        total_iva = 0
        total_imponible = 0
        total_con_IVA = 0
        reten_iva_total = 0
        alicuota = 0
        alicuota_reten = 0
        alicuota_porcent = ''
        alicuota_porcent_reten = ''
        tax_general = 0
        tax_reducido = 0
        base_general = 0
        base_reducido = 0
        cont_execto = 0
        t_retenido=0

        # Nuevas variables
        tot_exentas = 0
        base_genel_mas_adicional = 0
        tax_genel_mas_adicional = 0
        ret_general = 0
        ret_reducido = 0
        ret_genel_mas_adicional = 0


        for invoice in self.invoices:
            num2 += 1

            ## traer datos del iva para saber el orden de cada producto de las factura con su montos
            exent_p_fac = 0
            post_exectas = 0

            base_16 = 0
            tax_16 = 0
            tot_comp_p_iva_16 = 0  # base + iva
            ret_16 = 0
            cont_16 = 0

            base_8 = 0
            tax_8 = 0
            tot_comp_p_iva_8 = 0  # base + iva
            ret_8 = 0
            cont_8 = 0

            base_31 = 0
            tax_31 = 0
            tot_comp_p_iva_31 = 0  # base + iva
            ret_31 = 0
            cont_31 = 0

            ids_accounts = invoice.id

            for l in invoice.invoice_line_ids:
                if l.invoice_id.id == ids_accounts:
                    if l.invoice_line_tax_ids.amount or l.invoice_line_tax_ids.amount == 0:

                        if invoice.origin == 0:  # Si una factura es reembolsada
                            if l.invoice_line_tax_ids.amount == 0:

                                # Exectas
                                exent_p_fac += l.price_subtotal

                                # % alicuota
                                por_ali_0 = l.invoice_line_tax_ids.amount

                                # Total de Exentas
                                tot_exentas += l.price_subtotal

                                post_exectas = 1

                            elif l.invoice_line_tax_ids.amount != 0:

                                # Calculo de IVA
                                amount_iva = ((l.price_subtotal * l.invoice_line_tax_ids.amount) / 100)

                                # Calculos de Retencion
                                reten_iva = ((amount_iva * invoice.retiva_id.porc_ret) / 100)

                                # calculo total compras con iva por producto de cada factura
                                comp_iva = (l.price_subtotal + amount_iva)

                                # Iva General
                                if l.invoice_line_tax_ids.amount == 16:
                                    por_ali_16 = l.invoice_line_tax_ids.amount  # % de IVA
                                    base_16 += l.price_subtotal  # base imponible
                                    tax_16 += amount_iva  # iva
                                    tot_comp_p_iva_16 += comp_iva  # base + iva
                                    por_reten_16 = invoice.retiva_id.porc_ret  # % de Retencion de iva
                                    ret_16 += reten_iva  # retencion

                                    cont_16 = 1

                                    base_general += l.price_subtotal  # total base general
                                    tax_general += amount_iva  # Iva total general
                                    ret_general += reten_iva  # Retencion total general

                                # Iva Reducido
                                elif l.invoice_line_tax_ids.amount == 8:
                                    por_ali_8 = l.invoice_line_tax_ids.amount  # % de IVA
                                    base_8 += l.price_subtotal  # base imponible
                                    tax_8 += amount_iva  # iva
                                    tot_comp_p_iva_8 += comp_iva  # base + iva
                                    por_reten_8 = invoice.retiva_id.porc_ret  # % de Retencion de iva
                                    ret_8 += reten_iva  # retencion

                                    cont_8 = 1

                                    base_reducido += l.price_subtotal  # total base reducida
                                    tax_reducido += amount_iva  # total iva reducida
                                    ret_reducido += reten_iva  # total reten reducida

                                # Iva general + adicional 16% + 15%
                                elif l.invoice_line_tax_ids.amount == 31:
                                    por_ali_31 = l.invoice_line_tax_ids.amount  # % de IVA
                                    base_31 += l.price_subtotal  # base imponible
                                    tax_31 += amount_iva  # iva
                                    tot_comp_p_iva_31 += comp_iva  # base + iva
                                    por_reten_31 = invoice.retiva_id.porc_ret  # % de Retencion de iva
                                    ret_31 += reten_iva  # retencion

                                    cont_31 = 1

                                    base_genel_mas_adicional += l.price_subtotal
                                    tax_genel_mas_adicional += amount_iva
                                    ret_genel_mas_adicional += reten_iva

                                # Total de todas las compras con IVA
                                total_con_IVA += comp_iva

                                # total Base Imponible
                                total_imponible += l.price_subtotal

                                # Total Impuesto IVA
                                total_iva += amount_iva

                                # Total de Retenciones de IVA
                                reten_iva_total += reten_iva

                        else:
                            if l.invoice_line_tax_ids.amount == 0:

                                # Exectas
                                exent_p_fac -= l.price_subtotal

                                # Total de Exentas
                                tot_exentas -= l.price_subtotal

                                post_exectas = 1

                            elif l.invoice_line_tax_ids.amount != 0:

                                # Calculo de IVA
                                amount_iva = ((l.price_subtotal * l.invoice_line_tax_ids.amount) / 100)

                                # Calculos de Retencion
                                reten_iva = ((amount_iva * invoice.retiva_id.porc_ret) / 100)

                                # calculo total compras con iva por producto de cada factura
                                comp_iva = (l.price_subtotal + amount_iva)

                                # Iva General
                                if l.invoice_line_tax_ids.amount == 16:
                                    por_ali_16 = l.invoice_line_tax_ids.amount  # % de IVA
                                    base_16 -= l.price_subtotal  # base imponible
                                    tax_16 -= amount_iva  # iva
                                    tot_comp_p_iva_16 -= comp_iva  # base + iva
                                    por_reten_16 = invoice.retiva_id.porc_ret  # % de Retencion de iva
                                    ret_16 -= reten_iva  # retencion

                                    cont_16 = 1

                                    base_general -= l.price_subtotal  # total base general
                                    tax_general -= amount_iva  # Iva total general
                                    ret_general -= reten_iva  # Retencion total general

                                # Iva Reducido
                                elif l.invoice_line_tax_ids.amount == 8:
                                    por_ali_8 = l.invoice_line_tax_ids.amount  # % de IVA
                                    base_8 -= l.price_subtotal  # base imponible
                                    tax_8 -= amount_iva  # iva
                                    tot_comp_p_iva_8 -= comp_iva  # base + iva
                                    por_reten_8 = invoice.retiva_id.porc_ret  # % de Retencion de iva
                                    ret_8 -= reten_iva  # retencion

                                    cont_8 = 1

                                    base_reducido -= l.price_subtotal  # total base reducida
                                    tax_reducido -= amount_iva  # total iva reducida
                                    ret_reducido -= reten_iva  # total reten reducida

                                # Iva general + adicional 16% + 15%
                                elif l.invoice_line_tax_ids.amount == 31:
                                    por_ali_31 = l.invoice_line_tax_ids.amount  # % de IVA
                                    base_31 -= l.price_subtotal  # base imponible
                                    tax_31 -= amount_iva  # iva
                                    tot_comp_p_iva_31 -= comp_iva  # base + iva
                                    por_reten_31 = invoice.retiva_id.porc_ret  # % de Retencion de iva
                                    ret_31 -= reten_iva  # retencion

                                    cont_31 = 1

                                    base_genel_mas_adicional -= l.price_subtotal
                                    tax_genel_mas_adicional -= amount_iva
                                    ret_genel_mas_adicional -= reten_iva

                                # Total de todas las compras con IVA
                                total_con_IVA -= comp_iva

                                # total Base Imponible
                                total_imponible -= l.price_subtotal

                                # Total Impuesto IVA
                                total_iva -= amount_iva

                                # Total de Retenciones de IVA
                                reten_iva_total -= reten_iva

            # ==================== Fin de calculos =====================================================================

            cont_impri = cont_8 + cont_16 + cont_31 + post_exectas

            # ==========================================================================================================

            for p in range(cont_impri):

                ws1.write(row, col + 1, num2, line_content_style)  # contador

               # Fecha del documento
                fech_doc = datetime.strftime(datetime.strptime(invoice.date_invoice, DEFAULT_SERVER_DATE_FORMAT), "%d/%m/%Y")

                ws1.write(row, col + 2, fech_doc, line_content_style)  # fecha de documento
                ws1.write(row, col + 3, invoice.vat, line_content_style)  # rif
                ws1.write(row, col + 4, invoice.partner_id.name, line_content_style)  # Nombre Razon social
                ws1.write(row, col + 5, "", line_content_style)  # numero de planilla de exportacion

                if (invoice.origin == 0):
                    ws1.write(row, col+6, invoice.move_id.name, line_content_style)  # Numero de Factura
                else:
                    ws1.write(row, col + 6, "", line_content_style)

                ws1.write(row, col + 7, invoice.invoice_sequence, line_content_style)  # Numero de control


                ws1.write(row, col + 8, invoice.supplier_control_number,line_content_style)  # nro de nota de debito

                if (invoice.origin == 0):
                    ws1.write(row, col + 9, "", line_content_style)  # nro de nota de credito
                else:
                    ws1.write(row, col + 9, invoice.move_id.name, line_content_style)

                if (invoice.origin == 0):
                    ws1.write(row, col + 10, "", line_content_style)  # nro factura afectada
                else:
                    ws1.write(row, col + 10, invoice.origin, line_content_style)


                if post_exectas == 1:  # Si una factura es reembolsada

                    # Total compras con IVA
                    ws1.write(row, col + 11, 0, line_content_style)

                    # Exectas
                    ws1.write(row, col + 12, exent_p_fac, line_content_style)

                    # Exoneradas
                    ws1.write(row, col + 13, 0, line_content_style)

                    # Base Imponible
                    ws1.write(row, col + 14, 0, line_content_style)

                    # % Alicuota
                    ws1.write(row, col + 15, por_ali_0, line_content_style)

                    # Impuesto IVA
                    ws1.write(row, col + 16, 0, line_content_style)

                    # Retencion de IVA
                    ws1.write(row, col + 17, 0, line_content_style)

                    ## traer datos retencion de iva de otra tabla=============

                    self.retivas = self.env['snc.retiva.partners.lines'].search([('invoice_id', '=', ids_accounts)])

                    n_comprob = self.retivas.retiva_partner_id.name
                    fec_comprob = self.retivas.retiva_partner_id.fecha_contabilizacion

                    # =========================================================

                    # Nro. Comprobante de Retencion
                    ws1.write(row, col + 18, n_comprob, line_content_style)

                    # Fecha comp
                    ws1.write(row, col + 19, fec_comprob, line_content_style)

                    post_exectas = 0

                elif cont_16 == 1:

                    # Total compras con IVA
                    ws1.write(row, col + 11, tot_comp_p_iva_16, line_content_style)

                    # Exectas
                    ws1.write(row, col + 12, 0, line_content_style)

                    # Exoneradas
                    ws1.write(row, col + 13, 0, line_content_style)

                    # Base Imponible
                    ws1.write(row, col + 14, base_16, line_content_style)

                    # % Alicuota
                    ws1.write(row, col + 15, por_ali_16, line_content_style)

                    # Impuesto IVA
                    ws1.write(row, col + 16, tax_16, line_content_style)

                    # Retencion de IVA
                    ws1.write(row, col + 17, ret_16, line_content_style)

                    ## traer datos retencion de iva de otra tabla=============

                    self.retivas = self.env['snc.retiva.partners.lines'].search([('invoice_id', '=', ids_accounts)])

                    n_comprob = self.retivas.retiva_partner_id.name
                    fec_comprob = self.retivas.retiva_partner_id.fecha_contabilizacion

                    # =========================================================

                    # Nro. Comprobante de Retencion
                    ws1.write(row, col + 18, n_comprob, line_content_style)

                    # Fecha comp
                    ws1.write(row, col + 19, fec_comprob, line_content_style)

                    cont_16 = 0

                elif cont_8 == 1:

                    # Total compras con IVA
                    ws1.write(row, col + 11, tot_comp_p_iva_8, line_content_style)

                    # Exectas
                    ws1.write(row, col + 12, 0, line_content_style)

                    # Exoneradas
                    ws1.write(row, col + 13, 0, line_content_style)

                    # Base Imponible
                    ws1.write(row, col + 14, base_8, line_content_style)

                    # % Alicuota
                    ws1.write(row, col + 15, por_ali_8, line_content_style)

                    # Impuesto IVA
                    ws1.write(row, col + 16, tax_8, line_content_style)

                    # Retencion de IVA
                    ws1.write(row, col + 17, ret_8, line_content_style)

                    ## traer datos retencion de iva de otra tabla=============

                    self.retivas = self.env['snc.retiva.partners.lines'].search([('invoice_id', '=', ids_accounts)])

                    n_comprob = self.retivas.retiva_partner_id.name
                    fec_comprob = self.retivas.retiva_partner_id.fecha_contabilizacion

                    # =========================================================

                    # Nro. Comprobante de Retencion
                    ws1.write(row, col + 18, n_comprob, line_content_style)

                    # Fecha comp
                    ws1.write(row, col + 19, fec_comprob, line_content_style)

                    cont_8 = 0

                elif cont_31 == 1:

                    # Total compras con IVA
                    ws1.write(row, col + 11, tot_comp_p_iva_31, line_content_style)

                    # Exectas
                    ws1.write(row, col + 12, 0, line_content_style)

                    # Exoneradas
                    ws1.write(row, col + 13, 0, line_content_style)

                    # Base Imponible
                    ws1.write(row, col + 14, base_31, line_content_style)

                    # % Alicuota
                    ws1.write(row, col + 15, por_ali_31, line_content_style)

                    # Impuesto IVA
                    ws1.write(row, col + 16, tax_31, line_content_style)

                    # Retencion de IVA
                    ws1.write(row, col + 17, ret_31, line_content_style)

                    ## traer datos retencion de iva de otra tabla=============

                    self.retivas = self.env['snc.retiva.partners.lines'].search([('invoice_id', '=', ids_accounts)])

                    n_comprob = self.retivas.retiva_partner_id.name
                    fec_comprob = self.retivas.retiva_partner_id.fecha_contabilizacion

                    # =========================================================

                    # Nro. Comprobante de Retencion
                    ws1.write(row, col + 18, n_comprob, line_content_style)

                    # Fecha comp
                    ws1.write(row, col + 19, fec_comprob, line_content_style)

                    cont_31 = 0

                row += 1


        row +=1
        ws1.write(row,col+9,"TOTALES:",sub_header_style)
        ws1.write(row,col+11,total_con_IVA,sub_header_style) #Total con IVA
        ws1.write(row,col+12,tot_exentas,sub_header_style) # EXONERADAS NO AGRAVADAS
        ws1.write(row,col+13,0,sub_header_style) # exoneradas
        ws1.write(row,col+14,total_imponible,sub_header_style)# base imponible
        ws1.write(row,col+16,total_iva,sub_header_style) #iva
        ws1.write(row,col+17,reten_iva_total,sub_header_style) #retencion de iva


        row +=2
        ws1.write(row,col+16,"Base Imponible",sub_header_style)
        ws1.write(row,col+17,"Debito Fiscal",sub_header_style)
        ws1.write_merge(row, row, 18, 19,"IVA retenido por comp.",sub_header_style)
        row+=1
        ws1.write_merge(row, row, 11, 15,"Ventas de Exportacion",sub_header_style)
        row+=1
        ws1.write_merge(row, row, 11, 15,"Ventas Internas Afectadas solo Alicuota General",sub_header_style)
        ws1.write(row, col + 16, base_general, line_content_style)
        ws1.write(row, col + 17, tax_general, line_content_style)
        ws1.write(row, col + 18, ret_general, line_content_style)
        row+=1
        ws1.write_merge(row, row, 11, 15,"Ventas Internas Afectadas solo Alicuota General + Adicional",sub_header_style)
        ws1.write(row, col + 16, base_genel_mas_adicional, line_content_style)
        ws1.write(row, col + 17, tax_genel_mas_adicional, line_content_style)
        ws1.write(row, col + 18, ret_genel_mas_adicional, line_content_style)
        row+=1
        ws1.write_merge(row, row, 11, 15,"Ventas Internas Afectadas solo Alicuota Reducida",sub_header_style)
        ws1.write(row, col + 16, base_reducido, line_content_style)
        ws1.write(row, col + 17, tax_reducido, line_content_style)
        ws1.write(row, col + 18, ret_reducido, line_content_style)
        row+=1
        ws1.write_merge(row, row, 11, 15,"Ventas Internas Exoneradas",sub_header_style)
        row+=1
        ws1.write_merge(row, row, 11, 15,"Ventas Internas No Gravadas",sub_header_style)
        ws1.write(row, col + 16, tot_exentas, line_content_style)
        ws1.write(row, col + 17, '', line_content_style)
        ws1.write(row, col + 18, '', line_content_style)
        row+=1
        ws1.write_merge(row, row, 11, 15,"Total",sub_header_style)
        ws1.write(row, col + 16, (base_general+base_reducido+tot_exentas), line_content_style)
        ws1.write(row, col + 17, (tax_general+tax_reducido+tax_genel_mas_adicional), line_content_style)
        ws1.write(row, col + 18, (ret_general+ret_reducido+ret_genel_mas_adicional), line_content_style)

        wb1.save(fp)
        out = base64.encodestring(fp.getvalue())
        self.write({'state': 'get', 'report': out, 'name':'Libro_de_Ventas.xls'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.wizard.libro.ventas',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
