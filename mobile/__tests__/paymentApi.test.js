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
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock'));

import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';
import { loadPaymentPanel } from '../src/core/paymentApi';

const originalFetch = global.fetch;

describe('payment panel static card configuration', () => {
  beforeEach(async () => {
    await AsyncStorage.clear();
    global.fetch = jest.fn();
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
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('uses the generated native fallback if Expo runtime config omits the card', async () => {
    Constants.expoConfig.extra.paymentCard = {};

    const panel = await loadPaymentPanel();

    expect(panel.config.enabled).toBe(true);
    expect(panel.config.card).toEqual({ number: '6543210987654321', holder: '', bank: 'سامان' });
    expect(global.fetch).not.toHaveBeenCalled();
  });
});
