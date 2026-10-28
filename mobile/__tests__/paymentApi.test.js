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

jest.mock('expo-crypto', () => ({ randomUUID: () => 'install-test-id' }));
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock'));

import AsyncStorage from '@react-native-async-storage/async-storage';
import { loadPaymentPanel } from '../src/core/paymentApi';

const originalFetch = global.fetch;

describe('payment panel card fallback', () => { 
  beforeEach(async () => {
    await AsyncStorage.clear();
    global.fetch = jest.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ enabled: true, card: null }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ freeRemaining: 2, paidCredits: 0 }) });
  });

  afterEach(() => {
    global.fetch = originalFetch;
    jest.restoreAllMocks();
  });

  it('keeps the embedded static card visible when the server has no usable card', async () => {
    const panel = await loadPaymentPanel();

    expect(panel.config.offlineMode).toBe(true);
    expect(panel.config.enabled).toBe(true);
    expect(panel.config.card).toEqual({ number: '1234567890123456', holder: '', bank: 'سامان' });
  });
});
