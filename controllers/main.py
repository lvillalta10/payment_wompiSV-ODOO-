import logging

from odoo import api, fields, models, tools
from odoo.exceptions import UserError
from odoo.tools import float_round

_logger = logging.getLogger(__name__)

class PaymentAcquirerWompi(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('wompiels', 'Wompi El Salvador')])
    wompiels_public_key = fields.Char(string='Wompi El Salvador Public Key', required_if_provider='wompiels', groups='base.group_user')
    wompiels_private_key = fields.Char(string='Wompi El Salvador Private Key', required_if_provider='wompiels', groups='base.group_user')
    wompiels_test_public_key = fields.Char(string='Wompi El Salvador Test Public Key', required_if_provider='wompiels', groups='base.group_user')
    wompiels_test_private_key = fields.Char(string='Wompi El Salvador Test Private Key', required_if_provider='wompiels', groups='base.group_user')

    @api.model
    def _get_wompiels_urls(self, environment):
        """ Wompi El Salvador URLs"""
        if environment == 'prod':
            return {
                'wompiels_form_url': 'https://checkout.wompi.sv/v1/checkouts/',
                'wompiels_api_url': 'https://api.wompi.sv'
            }
        else:
            return {
                'wompiels_form_url': 'https://sandbox.wompi.sv/v1/checkouts/',
                'wompiels_api_url': 'https://sandbox.wompi.sv'
            }

    def _get_wompiels_api_headers(self, environment):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        if environment == 'prod':
            headers['Authorization'] = f'Bearer {self.wompiels_private_key}'
        else:
            headers['Authorization'] = f'Bearer {self.wompiels_test_private_key}'
        return headers

    def wompiels_form_generate_values(self, values):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        wompiels_tx_values = dict(values)
        wompiels_tx_values.update({
            'public_key': self.wompiels_public_key,
            'amount_in_cents': int(wompiels_tx_values['amount'] * 100),
            'currency': 'USD',
            'reference': values['reference'],
            'redirect_url': '%s' % (base_url),
        })
        return wompiels_tx_values

    def wompiels_get_form_action_url(self):
        return self._get_wompiels_urls(self.state)['wompiels_form_url']

    def _wompiels_generate_tx_values(self, order, acquirer):
        partner = order.partner_id.commercial_partner_id
        tx_values = {
            'amount': order.amount_total,
            'currency': 'USD',
            'reference': order.name,
            'description': order.name,
            'payer_email': partner.email,
            'payer_name': partner.name,
            'redirect_url': '%s' % (acquirer.return_url),
            'cancel_url': '%s' % (acquirer.cancel_url),
            'test': 'yes' if acquirer.state == 'test' else 'no',
        }
        return tx_values

    def wompiels_get_api_url(self):
        return self
