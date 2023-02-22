{
    'name': 'Wompi Payment Acquirer El Salvador',
    'author': 'Coraventas',
    'category': 'Accounting/Payment',
    'summary': 'Payment Acquirer: Wompi Colombia Implementation',
    'description': """Wompi Colombia payment acquirer""",
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_wompicol_templates.xml',
        'views/template_modify.xml',
        'data/payment_acquirer_data.xml',
    ],
    'post_init_hook': 'create_missing_journal_for_acquirers',
}
