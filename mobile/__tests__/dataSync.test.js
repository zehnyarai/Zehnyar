jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock'));
jest.mock('../src/core/paymentApi', () => ({ getApiBase: () => '' }));

import AsyncStorage from '@react-native-async-storage/async-storage';
import bundledDataset from '../src/data/dataset.json';
import {
  getDataset,
  getDatasetFreshness,
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

  it('downloads, validates and persists a changed dataset', async () => {
    const updated = {
      ...bundledDataset,
      meta: { ...bundledDataset.meta, version: '2.0.2' },
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
    expect(result.dataset.meta.version).toBe('2.0.2');
    expect(getDataset().meta.version).toBe('2.0.2');

    const cache = JSON.parse(await AsyncStorage.getItem('visayar.reference-data.v1'));
    expect(cache.etag).toBe('"revision-1"');
    expect(cache.dataset.meta.version).toBe('2.0.2');
  });

  it('keeps the last valid cached dataset available without a network', async () => {
    const saved = { ...bundledDataset, meta: { ...bundledDataset.meta, version: '2.0.2' } };
    await AsyncStorage.setItem('visayar.reference-data.v1', JSON.stringify({ etag: '"revision-2"', dataset: saved }));
    const result = await syncDataset({ apiBase: '', fetchImpl: jest.fn() });

    expect(result.source).toBe('cache');
    expect(result.dataset.meta.version).toBe('2.0.2');
    expect(getDataset().meta.version).toBe('2.0.2');
  });

  it('sends a conditional request and reuses cache on HTTP 304', async () => {
    await AsyncStorage.setItem('visayar.reference-data.v1', JSON.stringify({ etag: '"revision-3"', dataset: bundledDataset }));
    const fetchImpl = jest.fn().mockResolvedValue({ status: 304, ok: false });
    const result = await syncDataset({ apiBase: 'https://api.example.test', fetchImpl });

    expect(fetchImpl.mock.calls[0][1].headers).toEqual({ 'If-None-Match': '"revision-3"' });
    expect(result.source).toBe('cache');
    expect(result.dataset).toEqual(bundledDataset);
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
