#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const digitMap = {
  '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
  '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
  '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
  '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
};
const number = String(process.env.VISAYAR_PAYMENT_CARD_NUMBER || '')
  .replace(/[۰-۹٠-٩]/g, (character) => digitMap[character])
  .replace(/\D/g, '');
const apiBaseUrl = String(process.env.VISAYAR_API_BASE_URL || '').trim();
const hasSecureApi = /^https:\/\/[^/]+(?:\/.*)?$/.test(apiBaseUrl);
if (number.length !== 16) {
  if (!number && hasSecureApi) {
    console.log('Secure server mode configured; no card number is embedded in the Android bundle.');
    process.exit(0);
  }
  console.error('Provide a valid card secret, or a secure HTTPS API URL for server mode.');
  process.exit(1);
}

function findBundles(directory) {
  if (!fs.existsSync(directory)) return [];
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const file = path.join(directory, entry.name);
    if (entry.isDirectory()) return findBundles(file);
    return entry.isFile() && /\.bundle$/.test(entry.name) ? [file] : [];
  });
}

const root = process.env.ANDROID_BUILD_DIR || path.join(__dirname, '..', 'mobile', 'android', 'app', 'build');
const bundles = findBundles(root);
if (!bundles.some((file) => fs.readFileSync(file).includes(number))) {
  console.error('The built Android JavaScript bundle does not contain the configured card; refusing to publish the APK.');
  process.exit(1);
}
console.log('Configured card is present in the Android JavaScript bundle; value withheld.');
