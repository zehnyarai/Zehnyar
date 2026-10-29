#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const digits = {
  '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
  '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
  '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
  '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
};
const number = String(process.env.VISAYAR_PAYMENT_CARD_NUMBER || '')
  .replace(/[۰-۹٠-٩]/g, (character) => digits[character])
  .replace(/\D/g, '');
const apiBaseUrl = String(process.env.VISAYAR_API_BASE_URL || '').trim();
const hasSecureApi = /^https:\/\/[^/]+(?:\/.*)?$/.test(apiBaseUrl);
if (number.length !== 16 && (number.length > 0 || !hasSecureApi)) {
  console.error('Provide a valid 16-digit card secret for offline mode, or a secure HTTPS API URL for server mode.');
  process.exit(1);
}

const paymentCard = {
  number,
  holder: String(process.env.VISAYAR_PAYMENT_CARD_HOLDER || '').trim(),
  bank: String(process.env.VISAYAR_PAYMENT_BANK_NAME || 'سامان').trim(),
};
const output = path.join(__dirname, '..', 'mobile', 'src', 'core', 'paymentCard.generated.js');
fs.writeFileSync(output, `// Generated from Actions secrets; never commit this build output.\nexport default ${JSON.stringify(paymentCard)};\n`);
console.log('Native runtime card fallback generated; card data withheld.');
