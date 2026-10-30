const expo = require('./app.json').expo;
const testBuild = process.env.VISAYAR_TEST_BUILD === '1';
const apiBaseUrl = testBuild ? '' : String(process.env.VISAYAR_API_BASE_URL || expo.extra.apiBaseUrl || '').trim().replace(/\/$/, '');
const digitMap = { '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4', '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9', '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4', '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9' };
const cardNumber = String(process.env.VISAYAR_PAYMENT_CARD_NUMBER || '').replace(/[۰-۹٠-٩]/g, (digit) => digitMap[digit]).replace(/\D/g, '');
const cardNumberAllowed = cardNumber.length === 16;
const paymentCard = {
  number: cardNumberAllowed ? cardNumber : '',
  holder: String(process.env.VISAYAR_PAYMENT_CARD_HOLDER || '').trim(),
  bank: String(process.env.VISAYAR_PAYMENT_BANK_NAME || 'سامان').trim(),
};

module.exports = {
  ...expo,
  name: testBuild ? 'ویزایار آزمایشی' : expo.name,
  android: {
    ...expo.android,
    package: testBuild ? `${expo.android.package}.test` : expo.android.package,
    ...(testBuild ? {
      versionCode: 1,
      blockedPermissions: [...new Set([...(expo.android.blockedPermissions || []), 'android.permission.INTERNET'])],
    } : {}),
  },
  extra: {
    ...expo.extra,
    apiBaseUrl,
    paymentCard: testBuild ? { number: '', holder: '', bank: '' } : paymentCard,
    testBuild,
  },
};
