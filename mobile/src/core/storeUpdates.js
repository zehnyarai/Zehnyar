import { Linking, Platform } from 'react-native';
import Constants from 'expo-constants';

const MYKET_UPDATE_URL = 'myket://check-update?id=ai.visayar.app';

// The documented Myket intent opens a dialog only when an update exists.
// Failure (e.g. Myket absent) must never block startup. Bazaar uses a different
// native service and is deliberately not routed through this intent.
export async function checkMyketUpdate({
  platform = Platform.OS,
  extra = Constants.expoConfig?.extra || {},
  openURL = Linking.openURL,
} = {}) {
  if (platform !== 'android' || extra.myketBuild !== true) return 'skipped';
  try {
    await openURL(MYKET_UPDATE_URL);
    return 'requested';
  } catch (_) {
    return 'unavailable';
  }
}
