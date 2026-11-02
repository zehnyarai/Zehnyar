import { Platform } from 'react-native';
import Constants from 'expo-constants';

// Cafe Bazaar's app-specific RSA public key (not a private key or account secret).
export const BAZAAR_RSA_PUBLIC_KEY = 'MIHNMA0GCSqGSIb3DQEBAQUAA4G7ADCBtwKBrwCwOm/60Tk9soJsn5U7KkXc0bZ4dLPRsk2od6Z9yhSAF9KTAl+LupPEBd12tGT+Km3nGv1Te/a3vJqLYXf7mqJrJmVr/ZTYc2VDPujKUbAncaxVHD5vkZbz0Joavblm3MLyqsEwemw5wIVyL+4+f7tk4y6gMBbpMIiuKITEO/Uaoc1/5ycKuhELR0xJcsVAJoR3HPAckKMQXqx4/C4oPIePH+qv/3WsES8mPSJoyskCAwEAAQ==';

function appExtra() {
  return Constants.expoConfig?.extra
    || Constants.manifest2?.extra?.expoClient?.extra
    || Constants.manifest?.extra
    || {};
}

export function isBazaarIabBuild() {
  return appExtra().bazaarIab === true;
}

export function getCafeBazaarBilling() {
  if (Platform.OS !== 'android') return null;
  try {
    return require('expo-cafebazaar-billing').default || null;
  } catch (error) {
    return null;
  }
}
