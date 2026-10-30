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
const apiBaseUrl = String(process.env.VISAYAR_API_BASE_URL || '').trim().replace(/\/$/, '');
const hasSecureApi = /^https:\/\/[^/]+(?:\/.*)?$/.test(apiBaseUrl);
if (apiBaseUrl && !hasSecureApi) {
  console.error('VISAYAR_API_BASE_URL is not a valid HTTPS URL.');
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
if (bundles.length === 0) {
  console.error('No Android JavaScript bundle was found; refusing to publish the APK.');
  process.exit(1);
}

const contents = bundles.map((file) => fs.readFileSync(file));
if (hasSecureApi && !contents.some((bundle) => bundle.includes(apiBaseUrl))) {
  console.error('The secure API URL was not embedded in the Android bundle; refusing to publish the APK.');
  process.exit(1);
}
if (!hasSecureApi && number.length !== 16) {
  console.error('Provide a secure HTTPS API URL, or a valid 16-digit card secret for offline mode.');
  process.exit(1);
}
if (number.length === 16 && !contents.some((bundle) => bundle.includes(number))) {
  console.error('The configured card is missing from the Android bundle; refusing to publish the APK.');
  process.exit(1);
}

if (hasSecureApi) console.log('Configured secure API URL is present in the Android bundle; value withheld.');
if (number.length === 16) console.log('Configured card is present in the Android bundle; value withheld.');
else console.log('No static card was embedded; server-side card settings will be used.');
