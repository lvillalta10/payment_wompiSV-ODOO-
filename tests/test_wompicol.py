import unittest
from wompico import WompiCo

class TestWompiCoElSalvador(unittest.TestCase):

    def setUp(self):
        self.wompi = WompiCo(api_key='test_api_key', test=True, country='SV')

    def test_create_payment(self):
        payment_data = {
            'amount_in_cents': 200000,
            'currency': 'USD',
            'reference': 'TEST_PAYMENT'
        }
        payment_response = self.wompi.create_payment(payment_data)
        self.assertIsNotNone(payment_response.get('id'))

    def test_retrieve_payment(self):
        payment_data = {
            'amount_in_cents': 200000,
            'currency': 'USD',
            'reference': 'TEST_PAYMENT'
        }
        payment_response = self.wompi.create_payment(payment_data)
        payment_id = payment_response.get('id')

        retrieved_payment = self.wompi.retrieve_payment(payment_id)
        self.assertEqual(retrieved_payment.get('status'), 'APPROVED')

    def test_create_token(self):
        token_data = {
            'card_number': '4111111111111111',
            'card_holder': 'JOHN DOE',
            'expiration_year': '2025',
            'expiration_month': '12',
            'cvc': '123'
        }
        token_response = self.wompi.create_token(token_data)
        self.assertIsNotNone(token_response.get('id'))
