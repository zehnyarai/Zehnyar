import AsyncStorage from '@react-native-async-storage/async-storage';

const KEYS = {
  profile: 'zehnyar.profile.v2',
  lang: 'zehnyar.lang',
  result: 'zehnyar.result.v2',
  checklist: 'zehnyar.checklist.v2',
  onboarded: 'zehnyar.onboarded.v2',
};

export async function saveProfile(profile) {
  try {
    await AsyncStorage.setItem(KEYS.profile, JSON.stringify(profile));
  } catch (error) {
    // Offline-first: a failed write must never block the user.
  }
}

export async function loadProfile() {
  try {
    const raw = await AsyncStorage.getItem(KEYS.profile);
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    return null;
  }
}

export async function saveResult(result) {
  try {
    await AsyncStorage.setItem(KEYS.result, JSON.stringify({
      savedAt: new Date().toISOString(),
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
    const raw = await AsyncStorage.getItem(KEYS.result);
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    return null;
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
    const raw = await AsyncStorage.getItem(KEYS.checklist);
    const all = raw ? JSON.parse(raw) : {};
    all[visaId] = items;
    await AsyncStorage.setItem(KEYS.checklist, JSON.stringify(all));
  } catch (error) {
    // ignored
  }
}

export async function loadChecklist(visaId) {
  try {
    const raw = await AsyncStorage.getItem(KEYS.checklist);
    const all = raw ? JSON.parse(raw) : {};
    return all[visaId] || [];
  } catch (error) {
    return [];
  }
}

export async function clearAll() {
  try {
    await AsyncStorage.multiRemove([KEYS.profile, KEYS.result, KEYS.checklist, KEYS.onboarded]);
  } catch (error) {
    // ignored
  }
}

export { KEYS };
