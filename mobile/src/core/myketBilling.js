import { Platform } from 'react-native';
import Constants from 'expo-constants';

// Myket's app-specific RSA public key (not a private key or account secret).
// Obtain from Myket developer panel → In-app products → Public key.
// Value is injected at build time via app.config.js extra.myketRsaPublicKey.
export function getMyketRsaPublicKey() {
  return appExtra().myketRsaPublicKey || '';
}

function appExtra() {
  return Constants.expoConfig?.extra
    || Constants.manifest2?.extra?.expoClient?.extra
    || Constants.manifest?.extra
    || {};
}

export function isMyketIabBuild() {
  return appExtra().myketIab === true;
}

export function getMyketBilling() {
  if (Platform.OS !== 'android') return null;
  try {
    return require('expo-myket-billing').default || null;
  } catch (error) {
    return null;
  }
}
