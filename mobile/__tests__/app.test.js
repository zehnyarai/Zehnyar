import React from 'react';
import { act, create } from 'react-test-renderer';

import App from '../App';
import { I18nProvider } from '../src/i18n';
import { AppStateProvider } from '../src/core/appState';
import { dataset } from '../src/core/data';
import engine from '../src/core/engine';

import HomeScreen from '../src/screens/HomeScreen';
import ExploreScreen from '../src/screens/ExploreScreen';
import AdvisorScreen from '../src/screens/AdvisorScreen';
import ProfileScreen from '../src/screens/ProfileScreen';
import PaymentsScreen from '../src/screens/PaymentsScreen';
import WizardScreen from '../src/screens/WizardScreen';
import ResultsScreen from '../src/screens/ResultsScreen';
import CountryDetailScreen from '../src/screens/CountryDetailScreen';
import { Button } from '../src/components/ui';

jest.mock('expo-font', () => ({
  useFonts: () => [true],
  loadAsync: jest.fn(() => Promise.resolve()),
  isLoaded: jest.fn(() => true),
  isLoading: jest.fn(() => false),
  processFontFamily: jest.fn((family) => family),
}));
jest.mock('expo-splash-screen', () => ({
  preventAutoHideAsync: jest.fn(() => Promise.resolve()),
  hideAsync: jest.fn(() => Promise.resolve()),
}));
jest.mock('expo-haptics', () => ({
  impactAsync: jest.fn(() => Promise.resolve()),
  notificationAsync: jest.fn(() => Promise.resolve()),
  selectionAsync: jest.fn(() => Promise.resolve()),
  ImpactFeedbackStyle: { Light: 'light', Medium: 'medium', Heavy: 'heavy' },
  NotificationFeedbackType: { Success: 'success', Warning: 'warning', Error: 'error' },
}));
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock'));
jest.mock('react-native-share', () => ({ __esModule: true, default: { open: jest.fn() } }));

const navigation = {
  navigate: jest.fn(),
  goBack: jest.fn(),
  replace: jest.fn(),
  setOptions: jest.fn(),
};

const baseProfile = {
  ...engine.emptyProfile(),
  age: 31,
  educationId: 'master',
  languages: [{ testId: 'ielts', skills: { listening: 8, reading: 7.5, writing: 7, speaking: 7.5 } }],
  work: { ...engine.emptyProfile().work, totalYears: 6, overseasYears: 6, occupationCode: '21231' },
  funds: { availableUsd: 40000, cashUsd: 20000, assetsUsd: 20000 },
  adaptability: { relativeInCountry: false, priorStudyInCountry: false, priorWorkInCountry: false, eca: true },
  familySize: 2,
};

const assessed = engine.assess(dataset, baseProfile);

function renderWithProviders(element, { profile = baseProfile, result = null } = {}) {
  let tree;
  act(() => {
    tree = create(
      <I18nProvider initialLang="fa">
        <AppStateProvider initialProfile={profile} initialResult={result}>
          {element}
        </AppStateProvider>
      </I18nProvider>,
    );
  });
  return tree;
}

describe('Visayar app', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.clearAllMocks();
  });

  it('deep renders the whole application shell in Persian', () => {
    let tree;
    act(() => {
      tree = create(<App />);
    });
    act(() => {
      jest.advanceTimersByTime(400);
    });
    expect(tree.toJSON()).toBeTruthy();
  });

  it('renders the home screen with the trust badge and calls to action', () => {
    const tree = renderWithProviders(<HomeScreen navigation={navigation} />);
    const text = JSON.stringify(tree.toJSON());
    expect(text).toContain('ویزایار');
    expect(text).toContain('آخرین استعلام رسمی');
    expect(text).toContain('هدف شما چیست؟');
    expect(text).toContain('ادامه ارزیابی من');
  });

  it('renders every tab screen without crashing', () => {
    renderWithProviders(<ExploreScreen navigation={navigation} />);
    renderWithProviders(<ProfileScreen navigation={navigation} />);
    renderWithProviders(<AdvisorScreen navigation={navigation} />);
    renderWithProviders(<ExploreScreen navigation={navigation} profile={baseProfile} result={assessed} />);
    renderWithProviders(<AdvisorScreen navigation={navigation} profile={baseProfile} result={assessed} />);
  });

  it('renders the manual payment panel and all discounted assessment bundles', () => {
    const tree = renderWithProviders(<PaymentsScreen navigation={navigation} />);
    const text = JSON.stringify(tree.toJSON());
    expect(text).toContain('اعتبار ارزیابی');
    expect(text).toContain('۶۰۰٬۰۰۰ تومان');
    expect(text).toContain('دوازده ارزیابی');
    expect(text).toContain('پرداخت هنوز در این نسخه فعال نیست');
  });

  it('walks through all eight wizard steps', () => {
    let tree;
    act(() => {
      tree = create(
        <I18nProvider initialLang="fa">
          <AppStateProvider initialProfile={baseProfile}>
            <WizardScreen navigation={navigation} />
          </AppStateProvider>
        </I18nProvider>,
      );
    });
    for (let step = 0; step < 6; step += 1) {
      const buttons = tree.root.findAllByType(Button);
      const next = buttons[buttons.length - 1];
      act(() => {
        next.props.onPress();
      });
    }
    const text = JSON.stringify(tree.toJSON());
    expect(text).toContain('محاسبه شانس قبولی');
  });

  it('renders the results screen with a radar chart and country ranking', () => {
    const tree = renderWithProviders(<ResultsScreen navigation={navigation} />, {
      profile: baseProfile,
      result: assessed,
    });
    const text = JSON.stringify(tree.toJSON());
    expect(text).toContain('نتیجه ارزیابی');
    expect(text).toContain('نمودار قوت و ضعف پرونده');
    expect(text).toContain('کانادا');
  });

  it('renders the country detail for every destination', () => {
    dataset.countries.forEach((country) => {
      const tree = renderWithProviders(
        <CountryDetailScreen navigation={navigation} route={{ params: { code: country.code } }} />,
        { profile: baseProfile, result: assessed },
      );
      expect(tree.toJSON()).toBeTruthy();
      tree.unmount();
    });
  });

  it('shows an empty state before any assessment exists', () => {
    const tree = renderWithProviders(<ResultsScreen navigation={navigation} />, { profile: engine.emptyProfile() });
    const text = JSON.stringify(tree.toJSON());
    expect(text).toContain('هنوز ارزیابی‌ای ثبت نشده است');
  });
});
