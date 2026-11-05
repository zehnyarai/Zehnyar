const expo = require('./app.json').expo;
const testBuild = process.env.VISAYAR_TEST_BUILD === '1';
const bazaarIab = !testBuild && process.env.VISAYAR_CAFEBAZAAR_IAB === '1';
const myketBuild = !testBuild && String(process.env.VISAYAR_STORE || '').toLowerCase() === 'myket';
const apiBaseUrl = testBuild ? '' : String(process.env.VISAYAR_API_BASE_URL || expo.extra.apiBaseUrl || '').trim().replace(/\/$/, '');
if (bazaarIab) {
  let apiUrl;
  try { apiUrl = new URL(apiBaseUrl); } catch (error) { apiUrl = null; }
  if (!apiUrl || apiUrl.protocol !== 'https:' || !apiUrl.hostname || apiUrl.username || apiUrl.password || apiUrl.search || apiUrl.hash || apiUrl.pathname !== '/') {
    throw new Error('Cafe Bazaar IAB release requires a clean HTTPS API origin in VISAYAR_API_BASE_URL.');
  }
}
const blockedPermissions = new Set(expo.android.blockedPermissions || []);
if (testBuild) blockedPermissions.add('android.permission.INTERNET');
if (myketBuild) blockedPermissions.add('com.farsitel.bazaar.permission.PAY_THROUGH_BAZAAR');
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
    blockedPermissions: [...blockedPermissions],
    ...(testBuild ? { versionCode: 1 } : {}),
  },
  extra: {
    ...expo.extra,
    apiBaseUrl,
    paymentCard: testBuild ? { number: '', holder: '', bank: '' } : paymentCard,
    testBuild,
    bazaarIab,
    myketBuild,
  },
};
