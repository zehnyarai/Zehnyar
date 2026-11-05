import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

const KEYS = {
  profile: 'zehnyar.profile.v2',
  lang: 'zehnyar.lang',
  result: 'zehnyar.result.v2',
  checklist: 'zehnyar.checklist.v2',
  privacyConsent: 'zehnyar.privacy-consent.v1',
  onboarded: 'zehnyar.onboarded.v2',
};

const PROTECTED_KEYS = new Set([KEYS.profile, KEYS.result, KEYS.checklist, KEYS.privacyConsent]);
const appExtra = Constants.expoConfig?.extra || Constants.manifest2?.extra?.expoClient?.extra || Constants.manifest?.extra || {};
const bazaarIabStorage = appExtra.bazaarIab === true;
export const PRIVACY_POLICY_VERSION = bazaarIabStorage ? 'bazaar-iab-privacy-v1' : 'direct-privacy-v1';

async function getProtectedItem(key) {
  if (Platform.OS === 'web' || !bazaarIabStorage) return AsyncStorage.getItem(key);
  try {
    const protectedValue = await SecureStore.getItemAsync(key);
    if (protectedValue !== null) return protectedValue;
  } catch (error) {
    // Continue with a one-time migration of values saved by older app versions.
  }

  let legacyValue = null;
  try { legacyValue = await AsyncStorage.getItem(key); } catch (error) { return null; }
  if (legacyValue !== null) {
    try {
      await SecureStore.setItemAsync(key, legacyValue);
      await AsyncStorage.removeItem(key);
    } catch (error) {
      // Do not delete the legacy copy unless the encrypted write succeeded.
    }
  }
  return legacyValue;
}

async function setProtectedItem(key, value) {
  if (Platform.OS === 'web' || !bazaarIabStorage) return AsyncStorage.setItem(key, value);
  return SecureStore.setItemAsync(key, value);
}

async function removeProtectedItem(key) {
  if (Platform.OS === 'web' || !bazaarIabStorage) return AsyncStorage.removeItem(key);
  try { await SecureStore.deleteItemAsync(key); } catch (error) { /* continue removing legacy data */ }
  try { await AsyncStorage.removeItem(key); } catch (error) { /* best effort */ }
}

export async function saveProfile(profile) {
  try {
    await setProtectedItem(KEYS.profile, JSON.stringify(profile));
  } catch (error) {
    // Offline-first: a failed write must never block the user.
  }
}

export async function loadProfile() {
  try {
    const raw = await getProtectedItem(KEYS.profile);
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    return null;
  }
}

export function profileFingerprint(profile) {
  if (!profile) return null;
  const serialized = JSON.stringify(profile);
  // A small local cache key, not an authentication or integrity mechanism.
  let hash = 2166136261;
  for (let index = 0; index < serialized.length; index += 1) {
    hash ^= serialized.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return `${serialized.length}:${(hash >>> 0).toString(16)}`;
}

export async function saveResult(result, profile) {
  try {
    if (bazaarIabStorage) {
      // Persist only a completion marker and profile fingerprint; scores are
      // recomputed locally on restart instead of storing inferred outcomes.
      await setProtectedItem(KEYS.result, JSON.stringify({
        savedAt: new Date().toISOString(),
        hasResult: !!result,
        profileFingerprint: profileFingerprint(profile),
      }));
      return;
    }
    // Keep the existing direct/Myket build's local result format unchanged.
    await setProtectedItem(KEYS.result, JSON.stringify({
      savedAt: new Date().toISOString(),
      profileFingerprint: profileFingerprint(profile),
      summary: result.summary,
      countries: result.countries.map((country) => ({
        code: country.code,
        nameFa: country.nameFa,
        nameEn: country.nameEn,
        flag: country.flag,
        chance: country.best.chance,
        readiness: country.best.readiness,
        eligible: country.best.eligible,
        visaNameFa: country.best.visaNameFa,
        visaNameEn: country.best.visaNameEn,
      })),
    }));
  } catch (error) {
    // ignored on purpose
  }
}

export async function loadResult() {
  try {
    const raw = await getProtectedItem(KEYS.result);
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    return null;
  }
}

export async function loadPrivacyConsent() {
  try {
    const raw = await getProtectedItem(KEYS.privacyConsent);
    const record = raw ? JSON.parse(raw) : null;
    return !!record && record.accepted === true && record.version === PRIVACY_POLICY_VERSION;
  } catch (error) {
    return false;
  }
}

export async function savePrivacyConsent() {
  try {
    await setProtectedItem(KEYS.privacyConsent, JSON.stringify({
      accepted: true,
      version: PRIVACY_POLICY_VERSION,
    }));
    return true;
  } catch (error) {
    // The app must not treat a failed secure write as consent.
    return false;
  }
}

export async function saveLanguage(lang) {
  try {
    await AsyncStorage.setItem(KEYS.lang, lang);
  } catch (error) {
    // ignored
  }
}

export async function loadLanguage() {
  try {
    return await AsyncStorage.getItem(KEYS.lang);
  } catch (error) {
    return null;
  }
}

export async function saveChecklist(visaId, items) {
  try {
    const raw = await getProtectedItem(KEYS.checklist);
    const all = raw ? JSON.parse(raw) : {};
    all[visaId] = items;
    await setProtectedItem(KEYS.checklist, JSON.stringify(all));
  } catch (error) {
    // ignored
  }
}

export async function loadChecklist(visaId) {
  try {
    const raw = await getProtectedItem(KEYS.checklist);
    const all = raw ? JSON.parse(raw) : {};
    return all[visaId] || [];
  } catch (error) {
    return [];
  }
}

export async function clearAll() {
  try {
    await Promise.all([
      ...Array.from(PROTECTED_KEYS, (key) => removeProtectedItem(key)),
      AsyncStorage.removeItem(KEYS.onboarded),
    ]);
  } catch (error) {
    // ignored
  }
}

export { KEYS };
