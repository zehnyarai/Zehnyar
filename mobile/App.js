import React, { useCallback, useEffect, useState } from 'react';
import { Pressable, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import * as SplashScreen from 'expo-splash-screen';
import { useFonts } from 'expo-font';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider, useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

import { colors, fonts, radius, shadow, spacing } from './src/theme';
import { I18nProvider, useDirection, useI18n } from './src/i18n';
import { AppStateProvider } from './src/core/appState';
import { Text } from './src/components/ui';

import HomeScreen from './src/screens/HomeScreen';
import ExploreScreen from './src/screens/ExploreScreen';
import AdvisorScreen from './src/screens/AdvisorScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import PaymentsScreen from './src/screens/PaymentsScreen';
import AdminScreen from './src/screens/AdminScreen';
import WizardScreen from './src/screens/WizardScreen';
import ResultsScreen from './src/screens/ResultsScreen';
import CountryDetailScreen from './src/screens/CountryDetailScreen';

SplashScreen.preventAutoHideAsync().catch(() => {});

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

const TAB_ICONS = {
  Home: ['home', 'home-outline'],
  Explore: ['earth', 'earth-outline'],
  Advisor: ['sparkles', 'sparkles-outline'],
  Profile: ['person-circle', 'person-circle-outline'],
};

function CustomTabBar({ state, navigation }) {
  const { t } = useI18n();
  const dir = useDirection();
  const insets = useSafeAreaInsets();
  const labels = { Home: t('nav.home'), Explore: t('nav.explore'), Advisor: t('nav.advisor'), Profile: t('nav.profile') };

  return (
    <View style={[styles.tabBar, { paddingBottom: Math.max(insets.bottom, 10) }]}>
      <View style={[styles.tabRow, { flexDirection: dir.row }]}>
        {state.routes.map((route, index) => {
          const focused = state.index === index;
          const [activeIcon, inactiveIcon] = TAB_ICONS[route.name] || ['ellipse', 'ellipse-outline'];
          return (
            <Pressable
              key={route.key}
              accessibilityRole="button"
              accessibilityLabel={labels[route.name]}
              onPress={() => {
                const event = navigation.emit({ type: 'tabPress', target: route.key, canPreventDefault: true });
                if (!focused && !event.defaultPrevented) navigation.navigate(route.name);
              }}
              style={{ flex: 1, alignItems: 'center' }}
            >
              <View style={[styles.tabInner, focused && styles.tabInnerActive]}>
                <Ionicons name={focused ? activeIcon : inactiveIcon} size={19} color={focused ? colors.teal700 : colors.ink35} />
                <Text variant="micro" style={{ color: focused ? colors.teal700 : colors.ink35, fontFamily: focused ? fonts.bold : fonts.medium }}>
                  {labels[route.name]}
                </Text>
              </View>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

function Tabs() {
  return (
    <Tab.Navigator screenOptions={{ headerShown: false, lazy: false }} tabBar={(props) => <CustomTabBar {...props} />}>
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Explore" component={ExploreScreen} />
      <Tab.Screen name="Advisor" component={AdvisorScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

const navTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    background: colors.canvas,
    card: colors.surface,
    text: colors.ink,
    primary: colors.teal700,
    border: colors.border,
  },
};

function Root() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.canvas },
        animation: 'slide_from_left',
      }}
    >
      <Stack.Screen name="Tabs" component={Tabs} />
      <Stack.Screen name="Wizard" component={WizardScreen} options={{ animation: 'slide_from_bottom' }} />
      <Stack.Screen name="Results" component={ResultsScreen} />
      <Stack.Screen name="CountryDetail" component={CountryDetailScreen} />
      <Stack.Screen name="Payments" component={PaymentsScreen} options={{ animation: 'slide_from_right' }} />
      <Stack.Screen name="Admin" component={AdminScreen} options={{ animation: 'slide_from_right' }} />
    </Stack.Navigator>
  );
}

export default function App() {
  const [fontsLoaded] = useFonts({
    'Vazirmatn-Regular': require('./src/assets/Vazirmatn-Regular.ttf'),
    'Vazirmatn-Medium': require('./src/assets/Vazirmatn-Medium.ttf'),
    'Vazirmatn-SemiBold': require('./src/assets/Vazirmatn-SemiBold.ttf'),
    'Vazirmatn-Bold': require('./src/assets/Vazirmatn-Bold.ttf'),
  });
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (fontsLoaded) {
      const timer = setTimeout(() => {
        SplashScreen.hideAsync().catch(() => {});
        setReady(true);
      }, 120);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [fontsLoaded]);

  if (!ready) return <View style={{ flex: 1, backgroundColor: colors.canvas }} />;

  return (
    <SafeAreaProvider>
      <I18nProvider initialLang="fa">
        <AppStateProvider>
          <StatusBar style="light" />
          <NavigationContainer theme={navTheme}>
            <Root />
          </NavigationContainer>
        </AppStateProvider>
      </I18nProvider>
    </SafeAreaProvider>
  );
}

const styles = {
  tabBar: {
    position: 'absolute',
    left: spacing.md,
    right: spacing.md,
    bottom: spacing.xs,
    backgroundColor: colors.surface,
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: colors.border,
    paddingTop: 8,
    paddingHorizontal: 6,
    ...shadow(2),
  },
  tabRow: { alignItems: 'center' },
  tabInner: {
    alignItems: 'center',
    gap: 3,
    paddingHorizontal: spacing.sm,
    paddingVertical: 5,
    borderRadius: radius.md,
  },
  tabInnerActive: { backgroundColor: colors.teal100 },
};
