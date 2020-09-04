# -*- coding: utf-8 -*-
from odoo import http

# class L10nVeRetivaSoftnetcorp/(http.Controller):
#     @http.route('/l10n_ve_retiva_softnetcorp//l10n_ve_retiva_softnetcorp//', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_ve_retiva_softnetcorp//l10n_ve_retiva_softnetcorp//objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_ve_retiva_softnetcorp/.listing', {
#             'root': '/l10n_ve_retiva_softnetcorp//l10n_ve_retiva_softnetcorp/',
#             'objects': http.request.env['l10n_ve_retiva_softnetcorp/.l10n_ve_retiva_softnetcorp/'].search([]),
#         })

#     @http.route('/l10n_ve_retiva_softnetcorp//l10n_ve_retiva_softnetcorp//objects/<model("l10n_ve_retiva_softnetcorp/.l10n_ve_retiva_softnetcorp/"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_ve_retiva_softnetcorp/.object', {
#             'object': obj
#         })