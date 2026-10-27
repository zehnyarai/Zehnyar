const expo = require('./app.json').expo;

const onlyAsciiDigits = (value) => String(value || '').replace(/[^0-9]/g, '');
const rawCardNumber = onlyAsciiDigits(process.env.VISAYAR_PAYMENT_CARD_NUMBER);
const paymentCard = rawCardNumber.length === 16
  ? {
      number: rawCardNumber,
      holder: String(process.env.VISAYAR_PAYMENT_CARD_HOLDER || '').trim(),
      bank: String(process.env.VISAYAR_PAYMENT_BANK_NAME || '').trim(),
    }
  : { number: '', holder: '', bank: '' };

module.exports = {
  ...expo,
  extra: {
    ...expo.extra,
    paymentCard,
  },
};
