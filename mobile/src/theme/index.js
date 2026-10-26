import { Platform } from 'react-native';

/**
 * Visayar design language: "نیلگون" teal paired with a soft "آسمانی" sky blue,
 * warm ivory surfaces and a single restrained gold accent for official marks.
 */
export const colors = {
  teal900: '#052E2A',
  teal800: '#064238',
  teal700: '#0B6E63',
  teal600: '#0E8577',
  teal500: '#16A08C',
  teal300: '#7FCFC1',
  teal100: '#DCF2ED',

  sky700: '#2E7FA6',
  sky600: '#4FA9CE',
  sky400: '#7CC6E8',
  sky300: '#A9DCF2',
  sky100: '#E4F4FB',
  sky50: '#F0FAFE',

  gold: '#C2A24C',
  goldSoft: '#F3E7C6',

  ink: '#0A201E',
  ink70: '#3A5551',
  ink50: '#5F7C79',
  ink35: '#8AA5A2',
  ink15: '#C8DAD7',

  surface: '#FFFFFF',
  canvas: '#F3FAF9',
  canvasAlt: '#E8F5F7',
  border: '#DDEDEA',
  borderStrong: '#C4DEDA',

  success: '#1E9E76',
  successSoft: '#DFF4EC',
  warn: '#C97C1E',
  warnSoft: '#FBEEDC',
  danger: '#C6484A',
  dangerSoft: '#FBE6E6',

  white: '#FFFFFF',
  overlay: 'rgba(5,46,42,0.55)',
};

export const gradients = {
  hero: ['#064238', '#0B6E63', '#2E7FA6'],
  heroSoft: ['#0E8577', '#4FA9CE'],
  mint: ['#F3FAF9', '#E4F4FB'],
  card: ['#FFFFFF', '#F6FCFB'],
  gold: ['#D8BC6B', '#B4913C'],
  success: ['#1E9E76', '#16A08C'],
  sky: ['#7CC6E8', '#4FA9CE'],
};

export const spacing = {
  xxs: 4,
  xs: 8,
  sm: 12,
  md: 16,
  lg: 20,
  xl: 26,
  xxl: 34,
  xxxl: 46,
};

export const radius = {
  sm: 10,
  md: 14,
  lg: 20,
  xl: 26,
  xxl: 34,
  pill: 999,
};

export const fonts = {
  regular: 'Vazirmatn-Regular',
  medium: 'Vazirmatn-Medium',
  semibold: 'Vazirmatn-SemiBold',
  bold: 'Vazirmatn-Bold',
};

export const type = {
  display: { fontFamily: fonts.bold, fontSize: 32, lineHeight: 46 },
  h1: { fontFamily: fonts.bold, fontSize: 24, lineHeight: 36 },
  h2: { fontFamily: fonts.semibold, fontSize: 19, lineHeight: 30 },
  h3: { fontFamily: fonts.semibold, fontSize: 16, lineHeight: 26 },
  body: { fontFamily: fonts.regular, fontSize: 14.5, lineHeight: 25 },
  bodyStrong: { fontFamily: fonts.medium, fontSize: 14.5, lineHeight: 25 },
  small: { fontFamily: fonts.regular, fontSize: 12.5, lineHeight: 21 },
  micro: { fontFamily: fonts.medium, fontSize: 11, lineHeight: 17 },
  number: { fontFamily: fonts.bold, fontSize: 30, lineHeight: 40, letterSpacing: 0.4 },
};

export function shadow(level = 1) {
  if (level === 0) return {};
  const config = Platform.select({
    android: {
      1: { elevation: 2 },
      2: { elevation: 5 },
      3: { elevation: 9 },
    },
    default: {
      1: { shadowColor: '#063F39', shadowOpacity: 0.06, shadowRadius: 8, shadowOffset: { width: 0, height: 3 } },
      2: { shadowColor: '#063F39', shadowOpacity: 0.1, shadowRadius: 16, shadowOffset: { width: 0, height: 8 } },
      3: { shadowColor: '#063F39', shadowOpacity: 0.16, shadowRadius: 26, shadowOffset: { width: 0, height: 14 } },
    },
  });
  return config[level] || config[1];
}

export const hitslop = { top: 8, bottom: 8, left: 8, right: 8 };
