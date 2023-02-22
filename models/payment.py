import logging
import pprint

import requests

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

   def _wompiels_form_get_tx_from_data(self, data):
    reference, txn_id = data.get('reference'), data.get('transaction_uuid')
    if not reference or not txn_id:
        error_msg = 'Wompi El Salvador: received data with missing reference (%s) or txn_id (%s)' % (reference, txn_id)
        _logger.info(error_msg)
        raise ValidationError(error_msg)
    txs = self.env['payment.transaction'].search([('reference', '=', reference)])
    if not txs or len(txs) > 1:
        error_msg = 'Wompi El Salvador: received data for reference %s, no transaction found' % (reference)
        if txs:
            error_msg += ' (found %d)' % len(txs)
        _logger.info(error_msg)
        raise ValidationError(error_msg)
    return txs

def _wompiels_form_get_invalid_parameters(self, data):
    invalid_parameters = []
    if self.state == 'enabled':
        if float(data.get('amount_in_cents', 0)) != float_round(self.amount * 100, 2):
            invalid_parameters.append(('Amount', data.get('amount_in_cents'), '%.2f' % (self.amount * 100)))
        if data.get('currency') != self.currency_id.name:
            invalid_parameters.append(('Currency', data.get('currency'), self.currency_id.name))
        if data.get('public_key') != self.wompiels_public_key:
            invalid_parameters.append(('Wompi El Salvador Public Key', data.get('public_key'), self.wompiels_public_key))
    return invalid_parameters

def _wompiels_form_validate(self, data):
    status = data['status']
    result = {
        'acquirer_reference': data.get('id'),
        'date': fields.datetime.now(),
    }
    if status == 'APPROVED':
        result.update(state='done', state_message=data['status_message'], date_validate=data['created_at'])
    elif status in ['CREATED', 'PENDING']:
        result.update(state='pending', state_message=data['status_message'], date_validate=data['created_at'])
    else:
        result.update(state='error', state_message=data['status_message'])
    return self.write(result)

def _wompiels_s2s_validate_response(self, data):
    status = data['data']['status']
    result = {
        'acquirer_reference': data['data'].get('id'),
        'date': fields.datetime.now(),
    }
    if status == 'APPROVED':
        result.update(state='done', state_message=data['data']['status_message'], date_validate=data['data']['created_at'])
    elif status in ['CREATED', 'PENDING']:
        result.update(state='pending', state_message=data['data']['status_message'], date_validate=data['data']['created_at'])
    else:
        result.update(state='error', state_message=data['data']['status_message'])
    return self.write(result)

def _wompiels_s2s_get_invalid_parameters(self, **kwargs):
    invalid_parameters = []
    if float(kwargs.get('amount', '0')) != float_round(self.amount * (10 ** self.currency_id.decimal_places), 2):
        invalid_parameters.append(('Amount', kwargs.get('amount'), '%.2f' % self.amount))
    if kwargs.get('currency') != self.currency_id.name:
        invalid_parameters.append(('Currency', kwargs.get('currency'), self.currency_id.name))
    return invalid_parameters

def _wompiels_s2s_get_tx_from_data(self, data):
        reference, amount, currency_name, acquirer_id = data.get('reference'), data.get('amount'), data.get('currency_name'), data.get('acquirer_id')
        if not all([reference, amount, currency_name, acquirer_id]):
            return None
        currency = self.env['res.currency'].search([('name', '=', currency_name)], limit=1)
        if not currency:
            return None
        return self.search([('reference', '=', reference), ('amount', '=', amount), ('currency_id', '=', currency.id), ('acquirer_id', '=', acquirer_id)], limit=1)

    def _wompiels_s2s_validate_tree(self, tree):
        error = None
        if tree.get('data', {}).get('status') == 'REJECTED':
            error = tree.get('data', {}).get('error_message') or _('Wompiels: Payment was refused by Wompi')
        if not error and tree.get('status') != 'APPROVED':
            error = _('Wompiels: unrecognized status %s in Wompi response') % tree.get('status')
        if not error:
            tx = self._wompiels_s2s_get_tx_from_data(tree.get('data'))
            if not tx:
                error = _('Wompiels: received data for reference %s; no order found') % (tree.get('data').get('reference'))
        if error:
            _logger.warning(error)
        return error or True
