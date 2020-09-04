# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
    
    _inherit = 'res.partner'

    retiva_id = fields.Many2one('snc.retiva',string='Retencion de IVA')
