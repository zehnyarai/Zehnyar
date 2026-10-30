import AsyncStorage from '@react-native-async-storage/async-storage';
import bundledDataset from '../data/dataset.json';
import { getApiBase } from './paymentApi';

const DATA_CACHE_KEY = 'visayar.reference-data.v1';
const active = { dataset: bundledDataset };
const datasetListeners = new Set();

export function subscribeDataset(listener) {
  datasetListeners.add(listener);
  return () => datasetListeners.delete(listener);
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

export function isValidDataset(value) {
  if (!value || typeof value !== 'object' || !value.meta || value.meta.schemaVersion !== 1) return false;
  if (typeof value.meta.version !== 'string' || !/^\d+\.\d+\.\d+$/.test(value.meta.version)) return false;
  if (!Array.isArray(value.countries) || value.countries.length < 1 || value.countries.length > 50) return false;
  if (!Array.isArray(value.occupations) || !Array.isArray(value.languageTests)
      || !Array.isArray(value.educationLevels) || !value.fx || typeof value.fx !== 'object') return false;
  if (!isNotFutureDate(value.meta.lastVerified)) return false;
  return value.countries.every((country) => (
    typeof country.code === 'string'
    && country.official
    && isNotFutureDate(country.official.lastVerified)
    && Array.isArray(country.visas)
    && country.visas.length > 0
    && country.visas.every((visa) => (
      typeof visa.id === 'string'
      && typeof visa.officialUrl === 'string'
      && visa.officialUrl.startsWith('https://')
      && Array.isArray(visa.criteria)
      && Array.isArray(visa.gates)
      && Array.isArray(visa.fees)
    ))
  ));
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
  const cache = await readCache();
  if (cache) useDataset(cache.dataset);
  return { source: cache ? 'cache' : 'bundle', dataset: active.dataset };
}

function secureApiBase(base) {
  if (!base) return false;
  if (/^https:\/\//i.test(base)) return true;
  return /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/i.test(base);
}

/**
 * Load a validated local snapshot first, then revalidate it against the API.
 * A failed request never removes the last good snapshot or blocks offline use.
 */
export async function syncDataset(options = {}) {
  const cache = await readCache();
  if (cache) useDataset(cache.dataset);

  const base = options.apiBase === undefined ? getApiBase() : options.apiBase;
  const fetcher = options.fetchImpl || (typeof fetch === 'function' ? fetch : null);
  if (!secureApiBase(base) || !fetcher) {
    return { source: cache ? 'cache' : 'bundle', updated: false, dataset: active.dataset };
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
      return { source: 'cache', updated: false, dataset: active.dataset };
    }
    if (!response.ok) throw new Error(`DATASET_HTTP_${response.status}`);
    const next = await response.json();
    if (!isValidDataset(next)) throw new Error('INVALID_REMOTE_DATASET');

    const changed = cache?.etag !== (response.headers?.get?.('ETag') || null);
    useDataset(next);
    try {
      await AsyncStorage.setItem(DATA_CACHE_KEY, JSON.stringify({
        etag: response.headers?.get?.('ETag') || null,
        dataset: next,
      }));
    } catch (error) {
      // Keep the validated server response for this session even if persistence fails.
    }
    return { source: 'network', updated: changed, dataset: active.dataset };
  } catch (error) {
    return { source: cache ? 'cache' : 'bundle', updated: false, dataset: active.dataset };
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
