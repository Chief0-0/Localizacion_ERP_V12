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


class libro_compras(models.TransientModel):
    _name = "account.wizard.libro.compras"
    
    facturas_ids = fields.Many2many('account.invoice', string='Facturas', store=True)
    tax_ids = fields.Many2many('account.invoice.tax', string='Facturas_1', store=True)
    #line_tax_ids = fields.Many2many('account.invoice.line.tax', string='Facturas_2', store=True)
    line_ids = fields.Many2many('account.invoice.line', string='Facturas_3', store=True)


    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')

    # fields for download xls
    state = fields.Selection([('choose', 'choose'), ('get', 'get')],default='choose')
    report = fields.Binary('Prepared file', filters='.xls', readonly=True)
    name =  fields.Char('File Name', size=32)
    handler = fields.Char('Handler', compute='count_handler', default='0')
    company_id = fields.Many2one('res.company','Company',default=lambda self: self.env.user.company_id.id)
    #iva_quest = fields.Many2one('account.invoce.tax', 'Iva quest', default=lambda self: self.env.)
    #exentos_iva = fields.Many2one('account.invoce.tax', 'Exento de IVA', default=lambda self: self.env.)
    #account_ids = fields.Many2one('account.invoce.tax', 'Ids de Account', default=lambda self: self.env.invoice_id.id)

    #

    def get_invoice(self):
        self.facturas_ids = self.env['account.invoice'].search([('date','>=',self.date_from),('date','<=', self.date_to),('type','!=','out_invoice'),('type','!=','out_refund'),('state','!=','draft')], order = 'date asc')
        _logger.info("\n\n\n {} \n\n\n".format(self.facturas_ids))


    @api.multi
    def print_facturas(self):
        self.get_invoice()
        return {'type': 'ir.actions.report','report_name': 'libro_compras.libro_factura_proveedores','report_type':"qweb-pdf"}



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
        ws1.write_merge(row,row, 2, 6, "Libro de Compras", header_content_style)
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
        ws1.write(row, col+2, datetime.strftime(datetime.strptime(self.date_from,DEFAULT_SERVER_DATE_FORMAT),"%d/%m/%Y"), sub_header_content_style)
        row += 1
        ws1.write(row, col+1, "Hasta :", sub_header_style)
        ws1.write(row, col+2, datetime.strftime(datetime.strptime(self.date_to,DEFAULT_SERVER_DATE_FORMAT),"%d/%m/%Y"), sub_header_content_style)
        row += 2
        ws1.write_merge(row, row, 5, 6, "Comprobante de retencion", sub_header_style)
        ws1.write_merge(row, row, 16, 17, "Compras sin derecho a debito fiscal", sub_header_style)
        ws1.write_merge(row, row, 18, 22, "Compras Internas / Importaciones", sub_header_style)
        row += 1
        ws1.write(row,col+1,"#",sub_header_style)
        ws1.write(row,col+2,"Fecha Documento",sub_header_style)
        ws1.write(row,col+3,"RIF",sub_header_style)
        ws1.write(row,col+4,"Razon Social",sub_header_style)
        ws1.write(row,col+5,"Numero",sub_header_style)
        ws1.write(row,col+6,"Fecha",sub_header_style)
        ws1.write(row,col+7,"Nro Planilla de Importacion (C80-C81)",sub_header_style)
        ws1.write(row,col+8,"Fecha Planilla Importacion",sub_header_style)
        ws1.write(row,col+9,"Nro Expediente Importacion",sub_header_style)
        ws1.write(row,col+10,"Nro de Factura",sub_header_style)
        ws1.write(row,col+11,"Nro de control",sub_header_style)
        ws1.write(row,col+12,"Nro de nota de debito",sub_header_style)
        ws1.write(row,col+13,"Nro de credito",sub_header_style)
        ws1.write(row,col+14,"Nro de factura afectada",sub_header_style)
        ws1.write(row,col+15,"Total compras con IVA",sub_header_style)
        ws1.write(row,col+16,"Exentas",sub_header_style)
        ws1.write(row,col+17,"Exoneradas",sub_header_style)
        ws1.write(row,col+18,"Base Imponible",sub_header_style) 
        ws1.write(row,col+19,"'%'Alic",sub_header_style)
        ws1.write(row,col+20,"Impuesto IVA",sub_header_style)
        ws1.write(row,col+21,"'%'Ret.",sub_header_style)
        ws1.write(row,col+22,"IVA Retenido (Vendedor)",sub_header_style)
        row += 1
        #Searching for customer invoices
        invoices = self.env['account.invoice'].search([('date','>=',self.date_from),('date','<=', self.date_to),('type','!=','out_invoice'),('type','!=','out_refund'),('state','!=','draft'),('state','!=','cancel')], order = 'date ASC') # order sirve para ordenar de manera ascendente o descendete los valores de una variable  (ASC o DEC))
        #invoices.sorted(key=lambda r: r.date_invoice, reverse=False)

        #tax_exentos = self.env['account.invoice.tax'].search([])
        #ids_line_taxs = self.env['account.invoice.line.tax'].search([])
        #ids_lines = self.env['account.invoice.line'].search([])

        all_inv_total = 0
        num = 0
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

        #Nuevas variables
        tot_exentas = 0
        base_genel_mas_adicional = 0
        tax_genel_mas_adicional = 0
        ret_general = 0
        ret_reducido = 0
        ret_genel_mas_adicional =0

        for invoice in invoices:
            num += 1

            ## traer datos del iva para saber el orden de cada producto de las factura con su montos
            exent_p_fac = 0
            post_exectas = 0

            base_16 = 0 
            tax_16 = 0  
            tot_comp_p_iva_16 = 0  # base + iva  
            ret_16 = 0  
            cont_16 = 0

            base_12 = 0
            tax_12 = 0
            tot_comp_p_iva_12 = 0  # base + iva  
            ret_12 = 0
            cont_12 = 0

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

            base_27 = 0
            tax_27 = 0
            tot_comp_p_iva_27 = 0  # base + iva  
            ret_27 = 0
            cont_27 = 0

            ids_accounts = invoice.id

            for l in invoice.invoice_line_ids:
                if l.invoice_id.id == ids_accounts:
                    if l.invoice_line_tax_ids.amount or l.invoice_line_tax_ids.amount == 0:
                        
                        if invoice.origin == 0:                     # Si una factura es reembolsada
                            if l.invoice_line_tax_ids.amount == 0:

                               #Exectas
                                exent_p_fac += l.price_subtotal
                               
                               # % alicuota 
                                por_ali_0 = l.invoice_line_tax_ids.amount
                               
                                #Total de Exentas
                                tot_exentas += l.price_subtotal

                                post_exectas = 1

                            elif l.invoice_line_tax_ids.amount != 0:

                                # Calculo de IVA
                                amount_iva = ((l.price_subtotal*l.invoice_line_tax_ids.amount)/100)

                                # Calculos de Retencion
                                reten_iva = ((amount_iva * invoice.retiva_id.porc_ret) / 100)
                                
                                # calculo total compras con iva por producto de cada factura
                                comp_iva = (l.price_subtotal + amount_iva)
                                
                                # Iva General

                                if l.invoice_line_tax_ids.amount == 16:
                                    por_ali_16 = l.invoice_line_tax_ids.amount  # % de IVA
                                    base_16 += l.price_subtotal                 # base imponible
                                    tax_16 += amount_iva                        # iva
                                    tot_comp_p_iva_16 += comp_iva               # base + iva
                                    por_reten_16 = invoice.retiva_id.porc_ret   # % de Retencion de iva
                                    ret_16 += reten_iva  # retencion

                                    cont_16 = 1

                                    base_general += l.price_subtotal  # total base general
                                    tax_general += amount_iva  # Iva total general
                                    ret_general += reten_iva  # Retencion total general

                                elif l.invoice_line_tax_ids.amount == 12:
                                    por_ali_12 = l.invoice_line_tax_ids.amount  # % de IVA
                                    base_12 += l.price_subtotal  # base imponible
                                    tax_12 += amount_iva  # iva
                                    tot_comp_p_iva_12 += comp_iva  # base + iva
                                    por_reten_12 = invoice.retiva_id.porc_ret  # % de Retencion de iva
                                    ret_12 += reten_iva  # retencion

                                    cont_12 = 1

                                    base_general += l.price_subtotal            # total base general
                                    tax_general += amount_iva                   # Iva total general
                                    ret_general += reten_iva                    # Retencion total general
                                    
                                # Iva Reducido
                                elif l.invoice_line_tax_ids.amount == 8:
                                    por_ali_8 = l.invoice_line_tax_ids.amount   # % de IVA
                                    base_8 += l.price_subtotal                  # base imponible
                                    tax_8 += amount_iva                         # iva
                                    tot_comp_p_iva_8 += comp_iva                # base + iva  
                                    por_reten_8 = invoice.retiva_id.porc_ret    # % de Retencion de iva
                                    ret_8 += reten_iva                          # retencion

                                    cont_8 = 1
                                    
                                    base_reducido += l.price_subtotal           # total base reducida
                                    tax_reducido += amount_iva                  # total iva reducida
                                    ret_reducido += reten_iva                   # total reten reducida

                                # Iva general + adicional 16% + 15%
                                elif l.invoice_line_tax_ids.amount == 31:
                                    por_ali_31 = l.invoice_line_tax_ids.amount  # % de IVA
                                    base_31 += l.price_subtotal                 # base imponible
                                    tax_31 += amount_iva                        # iva
                                    tot_comp_p_iva_31 += comp_iva               # base + iva
                                    por_reten_31 = invoice.retiva_id.porc_ret   # % de Retencion de iva
                                    ret_31 += reten_iva                         # retencion

                                    cont_31 = 1

                                    base_genel_mas_adicional += l.price_subtotal
                                    tax_genel_mas_adicional += amount_iva
                                    ret_genel_mas_adicional += reten_iva

                                elif l.invoice_line_tax_ids.amount == 27:
                                    por_ali_27 = l.invoice_line_tax_ids.amount  # % de IVA
                                    base_27 += l.price_subtotal  # base imponible
                                    tax_27 += amount_iva  # iva
                                    tot_comp_p_iva_27 += comp_iva  # base + iva
                                    por_reten_27 = invoice.retiva_id.porc_ret  # % de Retencion de iva
                                    ret_27 += reten_iva  # retencion

                                    cont_27 = 1
                                    
                                    base_genel_mas_adicional += l.price_subtotal
                                    tax_genel_mas_adicional += amount_iva
                                    ret_genel_mas_adicional += reten_iva

                                # Total de todas las compras con IVA
                                total_con_IVA += comp_iva

                                # total Base Imponible
                                total_imponible += l.price_subtotal

                                # Total Impuesto IVA
                                total_iva += amount_iva

                                #Total de Retenciones de IVA
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
                                    tot_comp_p_iva_16 -= comp_iva  # base - iva
                                    por_reten_16 = invoice.retiva_id.porc_ret  # % de Retencion de iva
                                    ret_16 -= reten_iva  # retencion

                                    cont_16 = 1

                                    base_general -= l.price_subtotal  # total base general
                                    tax_general -= amount_iva  # Iva total general
                                    ret_general -= reten_iva  # Retencion total general


                                elif l.invoice_line_tax_ids.amount == 12:
                                    por_ali_12 = l.invoice_line_tax_ids.amount  # % de IVA
                                    base_12 -= l.price_subtotal  # base imponible
                                    tax_12 -= amount_iva  # iva
                                    tot_comp_p_iva_12 -= comp_iva  # base - iva
                                    por_reten_12 = invoice.retiva_id.porc_ret  # % de Retencion de iva
                                    ret_12 -= reten_iva  # retencion

                                    cont_12 = 1

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
                                    tot_comp_p_iva_31 -= comp_iva  # base - iva
                                    por_reten_31 = invoice.retiva_id.porc_ret  # % de Retencion de iva
                                    ret_31 -= reten_iva  # retencion

                                    cont_31 = 1

                                    base_genel_mas_adicional -= l.price_subtotal
                                    tax_genel_mas_adicional -= amount_iva
                                    ret_genel_mas_adicional -= reten_iva


                                elif l.invoice_line_tax_ids.amount == 27:
                                    por_ali_27 = l.invoice_line_tax_ids.amount  # % de IVA
                                    base_27 -= l.price_subtotal  # base imponible
                                    tax_27 -= amount_iva  # iva
                                    tot_comp_p_iva_27 -= comp_iva  # base - iva
                                    por_reten_27 = invoice.retiva_id.porc_ret  # % de Retencion de iva
                                    ret_27 -= reten_iva  # retencion

                                    cont_27 = 1

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
                        
            cont_impri = cont_8 +cont_12+ cont_16 + cont_27 + cont_31 + post_exectas
                        
            # ==========================================================================================================
                        
            for p in range(cont_impri):
        
                ws1.write(row, col + 1, num, line_content_style)
                ws1.write(row, col + 2, invoice.date_invoice, line_content_style)  # Fecha documento
                ws1.write(row, col + 3, invoice.vat, line_content_style)  # RIF
                ws1.write(row, col + 4, invoice.partner_id.name, line_content_style)  # razon social

                ws1.write(row, col + 5, invoice.number_retiva,line_content_style)  # comprobante de retencion(Numero) #PREGUNTAR

                ws1.write(row, col + 6, invoice.date,line_content_style)  # comprobante de retencion(Fecha) #PREGUNTAR

                ws1.write(row, col + 7, "", line_content_style)  # Nro Planilla de Importacion (C80-C81) #PREGUNTAR
                ws1.write(row, col + 8, "", line_content_style)  # Fecha Planilla Importacion #PREGUNTAR
                ws1.write(row, col + 9, "", line_content_style)  # Nro Expediente Importacion #PREGUNTAR

                if (invoice.origin == 0):
                    ws1.write(row, col + 10, invoice.supplier_control_number, line_content_style)  # Numero de Factura
                else:
                    ws1.write(row, col + 10, "", line_content_style)

                ws1.write(row, col + 11, invoice.invoice_sequence, line_content_style)  # Numero de control

                ws1.write(row, col + 12, "", line_content_style)  # Nro de nota de debito

                if (invoice.origin == 0):  # Nro de credito
                    ws1.write(row, col + 13, "", line_content_style)
                else:
                    ws1.write(row, col + 13, invoice.move_id.name, line_content_style)

                if (invoice.origin == 0):
                    ws1.write(row, col + 14, "", line_content_style)  # Nro de factura afectada
                else:
                    ws1.write(row, col + 14, invoice.supplier_control_number, line_content_style)

                if post_exectas == 1:                     # Si una factura es reembolsada
                            
                   # Total compras con IVA
                    ws1.write(row, col + 15, 0, line_content_style)

                   #Exectas
                    ws1.write(row, col + 16, exent_p_fac, line_content_style)
                   
                   # Exoneradas
                    ws1.write(row, col + 17, 0, line_content_style)

                   # Base Imponible
                    ws1.write(row, col + 18, 0, line_content_style)

                   # % Alicuota
                    ws1.write(row, col + 19, por_ali_0, line_content_style)

                   # Impuesto IVA
                    ws1.write(row, col + 20,0, line_content_style)

                   # % de Retencion de IVA
                    ws1.write(row, col + 21, 0, line_content_style)

                   # Retencion de IVA
                    ws1.write(row, col + 22, 0, line_content_style)

                    post_exectas = 0

                elif cont_16 == 1:

                    # Total compras con IVA
                    ws1.write(row, col + 15, tot_comp_p_iva_16, line_content_style)

                    # Exectas
                    ws1.write(row, col + 16, 0, line_content_style)

                    # Exoneradas
                    ws1.write(row, col + 17, 0, line_content_style)

                    # Base Imponible
                    ws1.write(row, col + 18, base_16, line_content_style)

                    # % Alicuota
                    ws1.write(row, col + 19, por_ali_16, line_content_style)

                    # Impuesto IVA
                    ws1.write(row, col + 20, tax_16, line_content_style)

                    # % de Retencion de IVA
                    ws1.write(row, col + 21, por_reten_16, line_content_style)

                    # Retencion de IVA
                    ws1.write(row, col + 22, ret_16, line_content_style)

                    cont_16 = 0

                elif cont_12 == 1:
                    # Total compras con IVA
                    ws1.write(row, col + 15, tot_comp_p_iva_12, line_content_style)

                    # Exectas
                    ws1.write(row, col + 16, 0, line_content_style)

                    # Exoneradas
                    ws1.write(row, col + 17, 0, line_content_style)

                    # Base Imponible
                    ws1.write(row, col + 18, base_12, line_content_style)

                    # % Alicuota
                    ws1.write(row, col + 19, por_ali_12, line_content_style)

                    # Impuesto IVA
                    ws1.write(row, col + 20, tax_12, line_content_style)

                    # % de Retencion de IVA
                    ws1.write(row, col + 21, por_reten_12, line_content_style)

                    # Retencion de IVA
                    ws1.write(row, col + 22, ret_12, line_content_style)

                    cont_12 = 0

                elif cont_8 == 1:

                    # Total compras con IVA
                    ws1.write(row, col + 15, tot_comp_p_iva_8, line_content_style)

                    # Exectas
                    ws1.write(row, col + 16, 0, line_content_style)

                    # Exoneradas
                    ws1.write(row, col + 17, 0, line_content_style)

                    # Base Imponible
                    ws1.write(row, col + 18, base_8, line_content_style)

                    # % Alicuota
                    ws1.write(row, col + 19, por_ali_8, line_content_style)

                    # Impuesto IVA
                    ws1.write(row, col + 20, tax_8, line_content_style)

                    # % de Retencion de IVA
                    ws1.write(row, col + 21, por_reten_8, line_content_style)

                    # Retencion de IVA
                    ws1.write(row, col + 22, ret_8, line_content_style)

                    cont_8 = 0
                
                elif cont_31 == 1:

                    # Total compras con IVA
                    ws1.write(row, col + 15, tot_comp_p_iva_31, line_content_style)

                    # Exectas
                    ws1.write(row, col + 16, 0, line_content_style)

                    # Exoneradas
                    ws1.write(row, col + 17, 0, line_content_style)

                    # Base Imponible
                    ws1.write(row, col + 18, base_31, line_content_style)

                    # % Alicuota
                    ws1.write(row, col + 19, por_ali_31, line_content_style)

                    # Impuesto IVA
                    ws1.write(row, col + 20, tax_31, line_content_style)

                    # % de Retencion de IVA
                    ws1.write(row, col + 21, por_reten_31, line_content_style)

                    # Retencion de IVA
                    ws1.write(row, col + 22, ret_31, line_content_style)

                    cont_31 = 0

                elif cont_27 == 1:

                    # Total compras con IVA
                    ws1.write(row, col + 15, tot_comp_p_iva_27, line_content_style)

                    # Exectas
                    ws1.write(row, col + 16, 0, line_content_style)

                    # Exoneradas
                    ws1.write(row, col + 17, 0, line_content_style)

                    # Base Imponible
                    ws1.write(row, col + 18, base_27, line_content_style)

                    # % Alicuota
                    ws1.write(row, col + 19, por_ali_27, line_content_style)

                    # Impuesto IVA
                    ws1.write(row, col + 20, tax_27, line_content_style)

                    # % de Retencion de IVA
                    ws1.write(row, col + 21, por_reten_27, line_content_style)

                    # Retencion de IVA
                    ws1.write(row, col + 22, ret_27, line_content_style)

                    cont_27 = 0

                row +=1

        row +=1

        ws1.write(row,col+12,"TOTALES:",sub_header_style)
        ws1.write(row,col+15,total_con_IVA,sub_header_style)
        ws1.write(row,col+16,tot_exentas,sub_header_style)
        ws1.write(row,col+17,0,sub_header_style)
        ws1.write(row,col+18,total_imponible,sub_header_style)
        #ws1.write(row,col+19,'0',sub_header_style)
        ws1.write(row,col+20,total_iva,sub_header_style)
        ws1.write(row,col+22,reten_iva_total,sub_header_style)
        
        
        row +=2
        ws1.write(row,col+17,"Base Imponible",sub_header_style)
        ws1.write(row,col+18,"Debito Fiscal",sub_header_style)
        ws1.write_merge(row, row, 19, 20,"IVA retenido por Vendedor.",sub_header_style)
        row+=1

        ws1.write_merge(row, row, 12, 16,"Compras Internas Gravadas por Alicuota General",sub_header_style)
        ws1.write(row, col + 17, base_general, line_content_style)
        ws1.write(row, col + 18, tax_general, line_content_style)
        ws1.write(row, col + 19, ret_general, line_content_style)
        row+=1

        ws1.write_merge(row, row, 12, 16,"Compras Internas Gravadas por Alicuota Reducida",sub_header_style)
        ws1.write(row, col + 17, base_reducido, line_content_style)
        ws1.write(row, col + 18, tax_reducido, line_content_style)
        ws1.write(row, col + 19, ret_reducido, line_content_style)
        row+=1
        ws1.write_merge(row, row, 12, 16,"Compras Internas Gravadas por Alicuota General mas Alicuota Adicional",sub_header_style)
        ws1.write(row, col + 17, base_genel_mas_adicional, line_content_style)
        ws1.write(row, col + 18, tax_genel_mas_adicional, line_content_style)
        ws1.write(row, col + 19, ret_genel_mas_adicional, line_content_style)
        row+=1
        ws1.write_merge(row, row, 12, 16,"Compras Internas no Gravadas y/o sin Derecho a debito fiscal",sub_header_style)
        ws1.write(row, col + 17, tot_exentas, line_content_style)
        ws1.write(row, col + 18, 0, line_content_style)
        ws1.write(row, col + 19, 0, line_content_style)
        row+=1
        ws1.write_merge(row, row, 12, 16,"Importaciones gravadas por Alicuota General",sub_header_style)
        row+=1
        ws1.write_merge(row, row, 12, 16,"Importaciones gravadas por Alicutoa Reducida",sub_header_style)
        row+=1
        ws1.write_merge(row, row, 12, 16,"Importaciones Gravadas por Alicuota General mas Alicuta adicional",sub_header_style)
        row+=1
        ws1.write_merge(row, row, 12, 16,"Importaciones Compras no Gravadas y/o sin Derecho a debito fiscal",sub_header_style)
        row+=1
        ws1.write_merge(row, row, 12, 16,"Total",sub_header_style)
        ws1.write(row, col + 17,(base_general+base_reducido+tot_exentas), line_content_style)
        ws1.write(row, col + 18,(tax_general+tax_reducido+tax_genel_mas_adicional), line_content_style)
        ws1.write(row, col + 19,(ret_general+ret_reducido+ret_genel_mas_adicional), line_content_style)

        wb1.save(fp)
        out = base64.encodestring(fp.getvalue())
        self.write({'state': 'get', 'report': out, 'name':'invoices_detail.xls'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.wizard.libro.compras',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
   

