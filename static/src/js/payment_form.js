odoo.define('payment_wompi.payment_form', function(require) {
    "use strict";

    var ajax = require('web.ajax');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var Widget = require('web.Widget');
    var PaymentForm = require('payment.payment_form');

    var _t = core._t;

    PaymentForm.include({
        events: _.extend({}, PaymentForm.prototype.events, {
            'click #o_payment_form_pay': '_onWompiPayClick',
        }),

        /**
         * @override
         */
        init: function() {
            this._super.apply(this, arguments);
            this.wompiData = {
                public_key: this.wompiPublicKey,
                reference: this.reference,
                amount: this.amount,
                currency: this.currency,
                redirect_url: this.returnUrl,
                error_url: this.cancelUrl,
                lang: this.lang,
                shipping_address: this.partnerShipping,
                billing_address: this.partnerBilling,
            };
        },

        /**
         * Handles the click event of the Wompi pay button
         * @param {Event} event
         * @private
         */
        _onWompiPayClick: function(event) {
            event.preventDefault();

            // Disable pay button to prevent multiple clicks
            this.$('#o_payment_form_pay').prop('disabled', true);

            // Get the Wompi checkout URL
            this._getWompiCheckoutUrl()
                .then(url => window.location.href = url)
                .catch(error => {
                    this.$('#o_payment_form_pay').prop('disabled', false);
                    Dialog.alert(this, _t('An error occurred: ') + error.message);
                });
        },

        /**
         * Sends the payment data to the server to get the Wompi checkout URL
         * @returns {Promise<string>} The Wompi checkout URL
         * @private
         */
        _getWompiCheckoutUrl: function() {
            return ajax.jsonRpc('/payment/wompi/checkout', 'call', {
                acquirer_id: this.acquirerId,
                amount: this.amount,
                currency: this.currency,
                reference: this.reference,
                partner_id: this.partnerId,
                partner_name: this.partnerName,
                partner_email: this.partnerEmail,
                partner_phone: this.partnerPhone,
                partner_document_type: this.partnerDocumentType,
                partner_document_number: this.partnerDocumentNumber,
                lang: this.lang,
            });
        },
    });

    return PaymentForm;
});