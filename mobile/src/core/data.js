import AsyncStorage from '@react-native-async-storage/async-storage';
import bundledDataset from '../data/dataset.json';
import { getApiBase } from './paymentApi';

const DATA_CACHE_KEY = 'visayar.reference-data.v1';
const active = { dataset: bundledDataset };
const datasetListeners = new Set();
const syncListeners = new Set();
const RULE_KINDS = new Set([
  'age_band', 'education_rank', 'language_skills', 'language_best', 'experience_band',
  'flag', 'salary_band', 'funds_ratio', 'adaptability', 'spouse', 'numeric_band',
]);
const GATE_KINDS = new Set([
  'age_gate', 'language_gate', 'experience_gate', 'points_gate', 'funds_gate',
  'education_gate', 'flag_gate', 'salary_gate', 'investment_gate', 'remote_income_gate',
  'custom_points',
]);
let syncStatus = {
  status: 'idle',
  source: 'bundle',
  updated: false,
  version: bundledDataset.meta.version,
};

export function subscribeDataset(listener) {
  datasetListeners.add(listener);
  return () => datasetListeners.delete(listener);
}

export function getDatasetSyncStatus() {
  return { ...syncStatus };
}

export function subscribeDatasetSync(listener) {
  syncListeners.add(listener);
  return () => syncListeners.delete(listener);
}

function setDatasetSyncStatus(next) {
  syncStatus = { ...syncStatus, ...next };
  syncListeners.forEach((listener) => listener(getDatasetSyncStatus()));
}

// These named exports are kept for static consumers and fixtures. Runtime app
// code should use the getters so a server update is visible without a reinstall.
export const dataset = bundledDataset;
export const countries = bundledDataset.countries;
export const occupations = bundledDataset.occupations;
export const languageTests = bundledDataset.languageTests;
export const educationLevels = bundledDataset.educationLevels;
export const meta = bundledDataset.meta;

export function getDataset() { return active.dataset; }
export function getCountries() { return active.dataset.countries; }
export function getOccupations() { return active.dataset.occupations; }
export function getLanguageTests() { return active.dataset.languageTests; }
export function getEducationLevels() { return active.dataset.educationLevels; }
export function getMeta() { return active.dataset.meta; }

export function getTotals() {
  const current = active.dataset;
  return {
    countries: current.countries.length,
    visas: current.countries.reduce((sum, country) => sum + country.visas.length, 0),
    occupations: current.occupations.length,
  };
}

export function getAllVisaTypes() {
  return Array.from(new Set(getCountries().flatMap((country) => country.visas.map((visa) => visa.type))));
}

function isValidIsoDate(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}

function isNotFutureDate(value) {
  return isValidIsoDate(value) && value <= new Date().toISOString().slice(0, 10);
}

function isText(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

function isFiniteNonNegative(value) {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0;
}

function hasUniqueValues(items, keyOf) {
  const keys = items.map(keyOf);
  return keys.every((key) => key !== undefined && key !== null && key !== '')
    && new Set(keys).size === keys.length;
}

function isHttpsUrl(value) {
  return typeof value === 'string' && /^https:\/\/[a-z0-9.-]+(?::\d+)?(?:\/[^\s]*)?$/i.test(value);
}

function isValidRoute(visa, fx) {
  if (!visa || !/^[a-z0-9_]+$/.test(visa.id || '')) return false;
  if (!isText(visa.type) || !isText(visa.nameFa) || !isText(visa.nameEn)
      || !isText(visa.descriptionFa) || !isText(visa.descriptionEn)) return false;
  if (!isHttpsUrl(visa.officialUrl)) return false;
  if (!Array.isArray(visa.criteria) || visa.criteria.length < 1 || visa.criteria.length > 30) return false;
  if (!hasUniqueValues(visa.criteria, (item) => item.id)) return false;
  if (!visa.criteria.every((item) => (
    isText(item.labelFa)
    && isText(item.labelEn)
    && typeof item.max === 'number' && Number.isFinite(item.max) && item.max > 0
    && item.rule && RULE_KINDS.has(item.rule.kind)
  ))) return false;
  if (!Array.isArray(visa.gates) || visa.gates.length > 30
      || !visa.gates.every((gate) => gate && GATE_KINDS.has(gate.kind))) return false;
  if (!Array.isArray(visa.fees) || !visa.fees.every((fee) => (
    fee && isText(fee.labelFa) && isText(fee.labelEn)
    && isFiniteNonNegative(fee.amount)
    && isText(fee.currency) && !!fx[fee.currency]
    && typeof fee.verified === 'boolean'
  ))) return false;
  if (!isFiniteNonNegative(visa.maxPoints) || visa.maxPoints <= 0
      || !isFiniteNonNegative(visa.passMark) || visa.passMark > visa.maxPoints) return false;
  const criteriaMax = visa.criteria.reduce((sum, item) => sum + item.max, 0);
  if (Math.abs(criteriaMax - visa.maxPoints) > 0.01) return false;
  if (visa.settlement) {
    if (!isText(visa.settlement.currency) || !fx[visa.settlement.currency]
        || !Array.isArray(visa.settlement.byFamilySize)
        || !visa.settlement.byFamilySize.every(isFiniteNonNegative)) return false;
  }
  return true;
}

export function isValidDataset(value) {
  if (!value || typeof value !== 'object' || !value.meta || value.meta.schemaVersion !== 1) return false;
  if (typeof value.meta.version !== 'string' || !/^\d+\.\d+\.\d+$/.test(value.meta.version)) return false;
  if (!isNotFutureDate(value.meta.lastVerified)
      || !Number.isInteger(value.meta.reviewIntervalDays) || value.meta.reviewIntervalDays < 1
      || !Number.isInteger(value.meta.staleAfterDays) || value.meta.staleAfterDays < value.meta.reviewIntervalDays) return false;
  if (!Array.isArray(value.countries) || value.countries.length < 1 || value.countries.length > 50) return false;
  if (!Array.isArray(value.occupations) || value.occupations.length < 1 || value.occupations.length > 10000
      || !Array.isArray(value.languageTests) || value.languageTests.length < 1
      || !Array.isArray(value.educationLevels) || value.educationLevels.length < 1
      || !value.fx || typeof value.fx !== 'object' || Array.isArray(value.fx)) return false;

  const fxCodes = Object.keys(value.fx);
  if (fxCodes.length < 1 || !fxCodes.every((code) => (
    /^[A-Z]{3}$/.test(code)
    && value.fx[code]
    && isFiniteNonNegative(value.fx[code].rate)
    && value.fx[code].rate > 0
    && isText(value.fx[code].fa)
    && isText(value.fx[code].en)
    && isText(value.fx[code].symbol)
    && (() => {
      const entry = value.fx[code];
      const hasDatedQuote = entry.usdToLocal !== undefined || entry.asOf !== undefined || entry.source !== undefined;
      if (!hasDatedQuote) return true;
      return isFiniteNonNegative(entry.usdToLocal)
        && entry.usdToLocal > 0
        && isNotFutureDate(entry.asOf)
        && isHttpsUrl(entry.source)
        && Math.abs(entry.rate * entry.usdToLocal - 1) <= 0.1;
    })()
  ))) return false;

  if (!hasUniqueValues(value.countries, (country) => country.code)
      || !hasUniqueValues(value.occupations, (item) => item.noc)
      || !hasUniqueValues(value.languageTests, (item) => item.id)
      || !hasUniqueValues(value.educationLevels, (item) => item.id)) return false;
  if (!value.occupations.every((item) => isText(item.titleFa) && isText(item.titleEn))) return false;
  if (!value.languageTests.every((item) => isText(item.group) && isText(item.fa) && isText(item.en))) return false;
  if (!value.educationLevels.every((item) => Number.isInteger(item.rank) && item.rank > 0
      && isText(item.fa) && isText(item.en))) return false;

  const visaIds = new Set();
  return value.countries.every((country) => {
    if (!country || !/^[A-Z]{2,3}$/.test(country.code || '')
        || !isText(country.nameFa) || !isText(country.nameEn)
        || !isText(country.currency) || !value.fx[country.currency]
        || !country.official || !isText(country.official.authorityFa)
        || !isText(country.official.authorityEn) || !isHttpsUrl(country.official.portal)
        || !isNotFutureDate(country.official.lastVerified)
        || !Array.isArray(country.visas) || country.visas.length < 1 || country.visas.length > 30) return false;
    return country.visas.every((visa) => {
      if (!isValidRoute(visa, value.fx) || visaIds.has(visa.id)) return false;
      visaIds.add(visa.id);
      return true;
    });
  });
}

function useDataset(value) {
  if (!isValidDataset(value)) return false;
  active.dataset = value;
  datasetListeners.forEach((listener) => listener(value));
  return true;
}

async function readCache() {
  try {
    const raw = await AsyncStorage.getItem(DATA_CACHE_KEY);
    const parsed = raw ? JSON.parse(raw) : null;
    if (parsed && isValidDataset(parsed.dataset)) return parsed;
  } catch (error) {
    // A corrupt/unavailable cache is ignored; the bundled dataset is safe.
  }
  return null;
}

export async function loadCachedDataset() {
  let cache = await readCache();
  if (cache && !isCacheCompatible(cache.dataset, active.dataset)) {
    cache = null;
    AsyncStorage.removeItem(DATA_CACHE_KEY).catch(() => {});
  }
  if (cache) useDataset(cache.dataset);
  return { source: cache ? 'cache' : 'bundle', dataset: active.dataset };
}

function secureApiBase(base) {
  if (!base) return false;
  if (/^https:\/\//i.test(base)) return true;
  return /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/i.test(base);
}

function compareVersions(left, right) {
  const a = left.split('.').map(Number);
  const b = right.split('.').map(Number);
  for (let index = 0; index < 3; index += 1) {
    if (a[index] !== b[index]) return a[index] > b[index] ? 1 : -1;
  }
  return 0;
}

function isCacheCompatible(candidate, current) {
  const versionOrder = compareVersions(candidate.meta.version, current.meta.version);
  if (versionOrder < 0) return false;
  return versionOrder > 0 || JSON.stringify(candidate) === JSON.stringify(current);
}

/**
 * Load a validated local snapshot first, then revalidate it against the API.
 * A failed request never removes the last good snapshot or blocks offline use.
 */
export async function syncDataset(options = {}) {
  let cache = await readCache();
  if (cache && !isCacheCompatible(cache.dataset, active.dataset)) {
    cache = null;
    AsyncStorage.removeItem(DATA_CACHE_KEY).catch(() => {});
  }
  if (cache) useDataset(cache.dataset);
  setDatasetSyncStatus({ status: 'checking', source: cache ? 'cache' : 'bundle', updated: false, version: active.dataset.meta.version });

  const base = options.apiBase === undefined ? getApiBase() : options.apiBase;
  const fetcher = options.fetchImpl || (typeof fetch === 'function' ? fetch : null);
  if (!secureApiBase(base) || !fetcher) {
    const result = { source: cache ? 'cache' : 'bundle', updated: false, dataset: active.dataset };
    setDatasetSyncStatus({ status: 'offline', source: result.source, updated: false, version: active.dataset.meta.version });
    return result;
  }

  const headers = {};
  if (cache && typeof cache.etag === 'string' && cache.etag) headers['If-None-Match'] = cache.etag;
  const controller = typeof AbortController === 'function' ? new AbortController() : null;
  const timeout = controller ? setTimeout(() => controller.abort(), options.timeoutMs || 3500) : null;
  try {
    const response = await fetcher(`${base.replace(/\/$/, '')}/api/dataset`, {
      method: 'GET',
      headers,
      cache: 'no-cache',
      ...(controller ? { signal: controller.signal } : {}),
    });
    if (response.status === 304 && cache) {
      const result = { source: 'cache', updated: false, dataset: active.dataset };
      setDatasetSyncStatus({ status: 'current', source: 'cache', updated: false, version: active.dataset.meta.version });
      return result;
    }
    if (!response.ok) throw new Error(`DATASET_HTTP_${response.status}`);
    const next = await response.json();
    if (!isValidDataset(next)) throw new Error('INVALID_REMOTE_DATASET');
    if (compareVersions(next.meta.version, active.dataset.meta.version) < 0) {
      throw new Error('REMOTE_DATASET_ROLLBACK');
    }

    const changed = JSON.stringify(next) !== JSON.stringify(active.dataset);
    if (changed && next.meta.version === active.dataset.meta.version) {
      throw new Error('REMOTE_DATASET_VERSION_NOT_ADVANCED');
    }
    if (changed && !useDataset(next)) throw new Error('INVALID_REMOTE_DATASET');
    const etag = response.headers?.get?.('ETag') || null;
    try {
      await AsyncStorage.setItem(DATA_CACHE_KEY, JSON.stringify({ etag, dataset: next }));
    } catch (error) {
      // Keep the validated server response for this session even if persistence fails.
    }
    const result = { source: 'network', updated: changed, dataset: active.dataset };
    setDatasetSyncStatus({ status: changed ? 'updated' : 'current', source: 'network', updated: changed, version: active.dataset.meta.version });
    return result;
  } catch (error) {
    const result = { source: cache ? 'cache' : 'bundle', updated: false, dataset: active.dataset };
    setDatasetSyncStatus({ status: 'offline', source: result.source, updated: false, version: active.dataset.meta.version });
    return result;
  } finally {
    if (timeout) clearTimeout(timeout);
  }
}

export function findCountry(code) {
  return getCountries().find((country) => country.code === code) || null;
}

export function findVisa(visaId) {
  for (const country of getCountries()) {
    const visa = country.visas.find((item) => item.id === visaId);
    if (visa) return { country, visa };
  }
  return null;
}

export function findOccupation(code) {
  return getOccupations().find((item) => item.noc === code) || null;
}

export function visaTypeLabelKey(type) {
  return `visaTypes.${type}`;
}

// Static defaults retained for older callers; use getAllVisaTypes/getTotals for
// UI that must reflect a newly synchronized dataset.
export const allVisaTypes = Array.from(new Set(countries.flatMap((country) => country.visas.map((visa) => visa.type))));
export const totals = {
  countries: countries.length,
  visas: countries.reduce((sum, country) => sum + country.visas.length, 0),
  occupations: occupations.length,
};

export function formatVerifiedDate(isoDate, lang = 'en') {
  if (!isoDate || !/^\d{4}-\d{2}-\d{2}$/.test(isoDate)) return '—';
  const parsed = new Date(`${isoDate}T12:00:00Z`);
  if (Number.isNaN(parsed.getTime())) return '—';
  return new Intl.DateTimeFormat(lang === 'fa' ? 'fa-IR' : 'en-GB', {
    year: 'numeric', month: 'long', timeZone: 'UTC',
  }).format(parsed);
}

export function getDatasetFreshness(today = new Date()) {
  const current = active.dataset;
  const lastVerified = current.meta.lastVerified;
  const reviewIntervalDays = Number(current.meta.reviewIntervalDays || 30);
  const staleAfterDays = Number(current.meta.staleAfterDays || 45);
  const records = [
    { code: 'dataset', lastVerified },
    ...current.countries.map((country) => ({ code: country.code, lastVerified: country.official.lastVerified })),
  ];
  const todayUtc = Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate());
  const ages = records.map((record) => {
    const verifiedAt = new Date(`${record.lastVerified}T00:00:00Z`);
    if (Number.isNaN(verifiedAt.getTime()) || verifiedAt > today) return null;
    return Math.floor((todayUtc - verifiedAt.getTime()) / 86400000);
  });
  if (ages.some((age) => age === null)) {
    return { status: 'invalid', ageDays: null, lastVerified, reviewIntervalDays, staleAfterDays };
  }
  const ageDays = Math.max(...ages);
  const oldestRecord = records[ages.indexOf(ageDays)];
  const status = ageDays > staleAfterDays ? 'stale' : ageDays >= reviewIntervalDays ? 'review_due' : 'current';
  return { status, ageDays, lastVerified, oldestLastVerified: oldestRecord.lastVerified, oldestCountry: oldestRecord.code, reviewIntervalDays, staleAfterDays };
}

export function isDatasetStale(today = new Date()) {
  const { status } = getDatasetFreshness(today);
  return status === 'stale' || status === 'invalid';
}
