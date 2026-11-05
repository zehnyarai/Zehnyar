import React from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import { act, create } from 'react-test-renderer';
import { AppStateProvider } from '../src/core/appState';
import { Button } from '../src/components/ui';
import { GoalTile } from '../src/components/cards';
import { I18nProvider } from '../src/i18n';
import WizardScreen from '../src/screens/WizardScreen';
import {
  clearAll,
  KEYS,
  loadPrivacyConsent,
  loadProfile,
  profileFingerprint,
  savePrivacyConsent,
  saveProfile,
  saveResult,
} from '../src/core/storage';

jest.mock('expo-constants', () => ({
  __esModule: true,
  default: { expoConfig: { extra: { bazaarIab: true } } },
}));
jest.mock('expo-font', () => ({
  useFonts: () => [true],
  loadAsync: jest.fn(() => Promise.resolve()),
  isLoaded: jest.fn(() => true),
  isLoading: jest.fn(() => false),
  processFontFamily: jest.fn((family) => family),
}));
jest.mock('expo-haptics', () => ({
  impactAsync: jest.fn(() => Promise.resolve()),
  ImpactFeedbackStyle: { Light: 'light' },
}));
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('expo-linear-gradient', () => ({ LinearGradient: ({ children }) => children }));
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock'));
jest.mock('expo-secure-store', () => {
  const values = new Map();
  return {
    getItemAsync: jest.fn(async (key) => (values.has(key) ? values.get(key) : null)),
    setItemAsync: jest.fn(async (key, value) => values.set(key, value)),
    deleteItemAsync: jest.fn(async (key) => values.delete(key)),
    __clear: () => values.clear(),
  };
});

const profile = {
  age: 34,
  educationId: 'master',
  work: { totalYears: 8 },
  funds: { availableUsd: 50000 },
};

describe('Cafe Bazaar privacy storage', () => {
  beforeEach(async () => {
    await clearAll();
    await AsyncStorage.clear();
    SecureStore.__clear();
  });

  it('migrates an existing profile from plain storage to Android secure storage', async () => {
    const raw = JSON.stringify(profile);
    await AsyncStorage.setItem(KEYS.profile, raw);

    expect(await loadProfile()).toEqual(profile);
    expect(await SecureStore.getItemAsync(KEYS.profile)).toBe(raw);
    expect(await AsyncStorage.getItem(KEYS.profile)).toBeNull();
  });

  it('stores no assessment scores or country list in the persistent result marker', async () => {
    const result = {
      summary: { score: 78 },
      countries: [{ code: 'CA', best: { chance: 78, readiness: 70, eligible: true } }],
    };
    await saveResult(result, profile);

    const saved = JSON.parse(await SecureStore.getItemAsync(KEYS.result));
    expect(saved).toEqual(expect.objectContaining({
      hasResult: true,
      profileFingerprint: profileFingerprint(profile),
    }));
    expect(saved).not.toHaveProperty('countries');
    expect(saved).not.toHaveProperty('summary');
  });

  it('persists consent securely and removes it when assessment data is erased', async () => {
    expect(await loadPrivacyConsent()).toBe(false);
    expect(await savePrivacyConsent()).toBe(true);
    expect(await loadPrivacyConsent()).toBe(true);

    await clearAll();
    expect(await loadPrivacyConsent()).toBe(false);
  });

  it('blocks assessment fields until the user explicitly accepts the Bazaar privacy notice', async () => {
    let tree;
    act(() => {
      tree = create(
        <I18nProvider initialLang="fa">
          <AppStateProvider initialProfile={profile}>
            <WizardScreen navigation={{ goBack: jest.fn(), navigate: jest.fn(), replace: jest.fn() }} />
          </AppStateProvider>
        </I18nProvider>,
      );
    });

    expect(JSON.stringify(tree.toJSON())).toContain('حریم خصوصی و اطلاعات ارزیابی');
    expect(tree.root.findAllByType(GoalTile)).toHaveLength(0);
    const accept = tree.root.findAllByType(Button).find((button) => button.props.label === 'می‌پذیرم و ادامه می‌دهم');
    await act(async () => accept.props.onPress());
    expect(await loadPrivacyConsent()).toBe(true);
    expect(tree.root.findAllByType(GoalTile)).toHaveLength(5);
    await act(async () => tree.unmount());
  });
});
