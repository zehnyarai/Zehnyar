jest.mock('expo-constants', () => ({
  __esModule: true,
  default: {
    expoConfig: {
      extra: {
        apiBaseUrl: 'https://payments.example',
        paymentCard: { number: '1234567890123456', holder: '', bank: 'سامان' },
      },
    },
  },
}));

jest.mock('../src/core/paymentCard.generated', () => ({
  __esModule: true,
  default: { number: '6543210987654321', holder: '', bank: 'سامان' },
}));
jest.mock('expo-crypto', () => ({ randomUUID: () => 'install-test-id' }));
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(async () => null),
  setItemAsync: jest.fn(async () => {}),
  deleteItemAsync: jest.fn(async () => {}),
}));
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock'));

import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';
import * as SecureStore from 'expo-secure-store';
import { consumeAssessmentCredit, hasAssessmentAccess, loadPaymentPanel, submitReceipt } from '../src/core/paymentApi';

const originalFetch = global.fetch;

describe('payment panel static card configuration', () => {
  beforeEach(async () => {
    await AsyncStorage.clear();
    global.fetch = jest.fn();
    SecureStore.getItemAsync.mockResolvedValue(null);
    Constants.expoConfig.extra.apiBaseUrl = '';
    Constants.expoConfig.extra.paymentCard = { number: '1234567890123456', holder: '', bank: 'سامان' };
  });

  afterEach(() => {
    global.fetch = originalFetch;
    jest.restoreAllMocks();
  });

  it('shows the embedded card without waiting for or overriding from the API', async () => {
    const panel = await loadPaymentPanel();

    expect(panel.config.offlineMode).toBe(true);
    expect(panel.config.enabled).toBe(true);
    expect(panel.config.card).toEqual({ number: '1234567890123456', holder: '', bank: 'سامان' });
    expect(panel.config.canSubmitReceipt).toBe(false);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('uses the generated native fallback if Expo runtime config omits the card', async () => {
    Constants.expoConfig.extra.paymentCard = {};

    const panel = await loadPaymentPanel();

    expect(panel.config.enabled).toBe(true);
    expect(panel.config.card).toEqual({ number: '6543210987654321', holder: '', bank: 'سامان' });
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('posts a device-selected receipt and transfer details to the admin review route', async () => {
    Constants.expoConfig.extra.apiBaseUrl = 'https://payments.example';
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({ requestId: 'request-test-id', status: 'pending', credits: 1 }) });

    const result = await submitReceipt({
      sku: 'assessment_1',
      transferDate: '1405/08/05',
      trackingCode: 'TRX-12345',
      phone: '09123456789',
      receipt: { uri: 'file:///receipt.png', fileName: 'receipt.png', mimeType: 'image/png' },
    });

    expect(result.status).toBe('pending');
    expect(global.fetch).toHaveBeenCalledWith('https://payments.example/api/payments/requests', expect.objectContaining({ method: 'POST' }));
  });

  it('grants manager access only after validating the secure server session', async () => {
    Constants.expoConfig.extra.apiBaseUrl = 'https://payments.example';
    SecureStore.getItemAsync.mockResolvedValue('secure-admin-token');
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({ authenticated: true, username: 'owner' }) });

    expect(await hasAssessmentAccess()).toBe(true);
    expect(global.fetch).toHaveBeenCalledWith('https://payments.example/api/admin/auth/me', {
      headers: { Authorization: 'Bearer secure-admin-token' },
    });
  });

  it('sends a validated manager token to the server without consuming a user credit', async () => {
    Constants.expoConfig.extra.apiBaseUrl = 'https://payments.example';
    SecureStore.getItemAsync.mockResolvedValue('secure-admin-token');
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({ consumed: 'admin', freeRemaining: 2, paidCredits: 0 }) });

    const result = await consumeAssessmentCredit();

    expect(result.consumed).toBe('admin');
    expect(global.fetch).toHaveBeenCalledWith('https://payments.example/api/payments/consume/install-test-id', {
      method: 'POST',
      headers: { Authorization: 'Bearer secure-admin-token' },
    });
  });

  it('keeps the local card but enables manual receipt submission when an API is configured', async () => {
    Constants.expoConfig.extra.apiBaseUrl = 'https://payments.example';
    global.fetch.mockImplementation(async (url) => ({
      ok: true,
      json: async () => (url.endsWith('/config')
        ? { enabled: false, card: null, packages: [] }
        : { freeRemaining: 1, paidCredits: 0 }),
    }));

    const panel = await loadPaymentPanel();

    expect(panel.config.offlineMode).toBe(true);
    expect(panel.config.canSubmitReceipt).toBe(true);
    expect(panel.config.card.number).toBe('1234567890123456');
    expect(global.fetch).toHaveBeenCalledTimes(2);
  });
});
