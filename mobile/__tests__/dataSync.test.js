jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock'));
jest.mock('../src/core/paymentApi', () => ({ getApiBase: () => '' }));

import AsyncStorage from '@react-native-async-storage/async-storage';
import bundledDataset from '../src/data/dataset.json';
import {
  getDataset,
  getDatasetFreshness,
  getDatasetSyncStatus,
  isValidDataset,
  syncDataset,
} from '../src/core/data';

beforeEach(async () => {
  await AsyncStorage.clear();
});

describe('mobile reference-data delivery', () => {
  it('distinguishes the monthly review due date from the stale threshold', () => {
    expect(getDatasetFreshness(new Date('2026-11-24T12:00:00Z')).status).toBe('review_due');
    expect(getDatasetFreshness(new Date('2026-12-10T12:00:00Z')).status).toBe('stale');
  });

  it('accepts the bundled schema and rejects unsupported or incomplete data', () => {
    expect(isValidDataset(bundledDataset)).toBe(true);
    expect(isValidDataset({ ...bundledDataset, meta: { ...bundledDataset.meta, schemaVersion: 2 } })).toBe(false);
    expect(isValidDataset({ ...bundledDataset, countries: [] })).toBe(false);
  });

  it('ignores a stale cache older than the bundled dataset', async () => {
    const stale = { ...bundledDataset, meta: { ...bundledDataset.meta, version: '2.0.2' } };
    await AsyncStorage.setItem('visayar.reference-data.v1', JSON.stringify({ etag: '"stale"', dataset: stale }));
    const result = await syncDataset({ apiBase: '', fetchImpl: jest.fn() });

    expect(result.source).toBe('bundle');
    expect(result.dataset.meta.version).toBe(bundledDataset.meta.version);
    expect(await AsyncStorage.getItem('visayar.reference-data.v1')).toBeNull();

    const sameVersionDifferentContent = {
      ...bundledDataset,
      countries: bundledDataset.countries.map((country, index) => (index === 0
        ? { ...country, nameEn: `${country.nameEn} Stale` }
        : country)),
    };
    await AsyncStorage.setItem('visayar.reference-data.v1', JSON.stringify({ etag: '"same-version-stale"', dataset: sameVersionDifferentContent }));
    const sameVersionResult = await syncDataset({ apiBase: '', fetchImpl: jest.fn() });
    expect(sameVersionResult.source).toBe('bundle');
    expect(sameVersionResult.dataset).toEqual(bundledDataset);
    expect(await AsyncStorage.getItem('visayar.reference-data.v1')).toBeNull();
  });

  it('requires a dataset-version increment when remote content changes', async () => {
    const changedContent = {
      ...bundledDataset,
      countries: bundledDataset.countries.map((country, index) => (index === 0
        ? { ...country, nameEn: `${country.nameEn} Updated` }
        : country)),
    };
    const result = await syncDataset({
      apiBase: 'https://api.example.test',
      fetchImpl: jest.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: { get: () => '"same-version-changed-content"' },
        json: async () => changedContent,
      }),
    });

    expect(result.source).toBe('bundle');
    expect(result.dataset).toEqual(bundledDataset);
    expect(await AsyncStorage.getItem('visayar.reference-data.v1')).toBeNull();
  });

  it('rejects duplicate route ids and unsupported scoring rules', () => {
    const firstRouteId = bundledDataset.countries[0].visas[0].id;
    const duplicate = {
      ...bundledDataset,
      countries: bundledDataset.countries.map((country, index) => (index === 1
        ? { ...country, visas: country.visas.map((visa, visaIndex) => (visaIndex === 0 ? { ...visa, id: firstRouteId } : visa)) }
        : country)),
    };
    expect(isValidDataset(duplicate)).toBe(false);

    const unsupportedRule = {
      ...bundledDataset,
      countries: bundledDataset.countries.map((country, index) => (index === 0
        ? { ...country, visas: country.visas.map((visa, visaIndex) => (visaIndex === 0
          ? { ...visa, criteria: visa.criteria.map((criterion, criterionIndex) => (criterionIndex === 0
            ? { ...criterion, rule: { ...criterion.rule, kind: 'unknown_rule' } }
            : criterion)) }
          : visa)) }
        : country)),
    };
    expect(isValidDataset(unsupportedRule)).toBe(false);
  });

  it('downloads, validates and persists a changed dataset', async () => {
    const updated = {
      ...bundledDataset,
      meta: { ...bundledDataset.meta, version: '2.0.4' },
    };
    const fetchImpl = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: (name) => (name.toLowerCase() === 'etag' ? '"revision-1"' : null) },
      json: async () => updated,
    });

    const result = await syncDataset({ apiBase: 'https://api.example.test', fetchImpl });
    expect(fetchImpl).toHaveBeenCalledWith(
      'https://api.example.test/api/dataset',
      expect.objectContaining({ method: 'GET', headers: {} }),
    );
    expect(result.source).toBe('network');
    expect(result.dataset.meta.version).toBe('2.0.4');
    expect(getDataset().meta.version).toBe('2.0.4');

    const cache = JSON.parse(await AsyncStorage.getItem('visayar.reference-data.v1'));
    expect(cache.etag).toBe('"revision-1"');
    expect(cache.dataset.meta.version).toBe('2.0.4');
  });

  it('keeps the last valid cached dataset available without a network', async () => {
    const saved = { ...bundledDataset, meta: { ...bundledDataset.meta, version: '2.0.4' } };
    await AsyncStorage.setItem('visayar.reference-data.v1', JSON.stringify({ etag: '"revision-2"', dataset: saved }));
    const result = await syncDataset({ apiBase: '', fetchImpl: jest.fn() });

    expect(result.source).toBe('cache');
    expect(result.dataset.meta.version).toBe('2.0.4');
    expect(getDataset().meta.version).toBe('2.0.4');
  });

  it('never replaces a newer bundled dataset with an older saved cache or server response', async () => {
    const newer = { ...bundledDataset, meta: { ...bundledDataset.meta, version: '2.0.4' } };
    const fetchNewer = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: () => '"newer"' },
      json: async () => newer,
    });
    await syncDataset({ apiBase: 'https://api.example.test', fetchImpl: fetchNewer });
    await AsyncStorage.setItem('visayar.reference-data.v1', JSON.stringify({ etag: '"older"', dataset: bundledDataset }));

    const offline = await syncDataset({ apiBase: '', fetchImpl: jest.fn() });
    expect(offline.source).toBe('bundle');
    expect(offline.dataset.meta.version).toBe('2.0.4');
    expect(await AsyncStorage.getItem('visayar.reference-data.v1')).toBeNull();

    const olderResponse = { ...bundledDataset, meta: { ...bundledDataset.meta, version: '2.0.3' } };
    const rollback = await syncDataset({
      apiBase: 'https://api.example.test',
      fetchImpl: jest.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: { get: () => '"rollback"' },
        json: async () => olderResponse,
      }),
    });
    expect(rollback.dataset.meta.version).toBe('2.0.4');
    expect(getDatasetSyncStatus().status).toBe('offline');
  });

  it('sends a conditional request and reuses cache on HTTP 304', async () => {
    const cachedDataset = { ...bundledDataset, meta: { ...bundledDataset.meta, version: '2.0.4' } };
    await AsyncStorage.setItem('visayar.reference-data.v1', JSON.stringify({ etag: '"revision-3"', dataset: cachedDataset }));
    const fetchImpl = jest.fn().mockResolvedValue({ status: 304, ok: false });
    const result = await syncDataset({ apiBase: 'https://api.example.test', fetchImpl });

    expect(fetchImpl.mock.calls[0][1].headers).toEqual({ 'If-None-Match': '"revision-3"' });
    expect(result.source).toBe('cache');
    expect(result.dataset).toEqual(cachedDataset);
  });

  it('does not accept an invalid server response and retains the bundled copy', async () => {
    const fetchImpl = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: () => '"bad"' },
      json: async () => ({ meta: { schemaVersion: 99 } }),
    });
    const result = await syncDataset({ apiBase: 'https://api.example.test', fetchImpl });
    expect(result.source).toBe('bundle');
    expect(isValidDataset(result.dataset)).toBe(true);
    expect(await AsyncStorage.getItem('visayar.reference-data.v1')).toBeNull();
  });
});
