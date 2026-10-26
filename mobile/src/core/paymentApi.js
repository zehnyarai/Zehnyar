import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';
import * as Crypto from 'expo-crypto';

const INSTALL_KEY = 'visayar.install.id';
const LOCAL_FREE_KEY = 'visayar.free.assessments.used.v1';
const SERVER_FREE_SYNCED_KEY = 'visayar.free.assessments.server-synced.v1';
const LAST_REQUEST_KEY = 'visayar.payment.request.v1';


export async function getInstallId() {
  let id = await AsyncStorage.getItem(INSTALL_KEY);
  if (!id) {
    id = Crypto.randomUUID();
    await AsyncStorage.setItem(INSTALL_KEY, id);
  }
  return id;
}

export function getApiBase() {
  const configured = Constants.expoConfig?.extra?.apiBaseUrl || '';
  if (configured) return configured.replace(/\/$/, '');
  if (typeof window !== 'undefined' && window.location?.origin) return window.location.origin;
  return '';
}

async function api(path, options = {}) {
  const base = getApiBase();
  if (!base) throw new Error('API_NOT_CONFIGURED');
  const response = await fetch(`${base}${path}`, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data.detail || `HTTP ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return data;
}

export async function loadPaymentPanel() {
  const [installId, requestId] = await Promise.all([
    getInstallId(),
    AsyncStorage.getItem(LAST_REQUEST_KEY),
  ]);
  let config = null;
  let balance = null;
  let request = null;
  try {
    config = await api('/api/payments/config');
    balance = await api(`/api/payments/credits/${installId}`);
    if (requestId) request = await api(`/api/payments/requests/${requestId}?install_id=${installId}`);
  } catch (error) {
    // Keep package display available offline; purchases require server configuration.
  }
  return { installId, requestId, config, balance, request };
}

export async function submitReceipt({ sku, phone, trackingCode, receipt }) {
  const installId = await getInstallId();
  const body = new FormData();
  body.append('install_id', installId);
  body.append('sku', sku);
  body.append('phone', phone);
  body.append('tracking_code', trackingCode);
  if (receipt.file) body.append('receipt', receipt.file, receipt.fileName || 'receipt.jpg');
  else body.append('receipt', { uri: receipt.uri, name: receipt.fileName || 'receipt.jpg', type: receipt.mimeType || 'image/jpeg' });
  const result = await api('/api/payments/requests', { method: 'POST', body });
  await AsyncStorage.setItem(LAST_REQUEST_KEY, result.requestId);
  return result;
}

export async function checkRequest(requestId) {
  const installId = await getInstallId();
  const result = await api(`/api/payments/requests/${requestId}?install_id=${installId}`);
  const balance = await api(`/api/payments/credits/${installId}`);
  return { request: result, balance };
}

export async function hasAssessmentAccess() {
  const installId = await getInstallId();
  const used = Number(await AsyncStorage.getItem(LOCAL_FREE_KEY) || 0);
  try {
    const balance = await api(`/api/payments/credits/${installId}`);
    const remainingFree = Math.min(balance.freeRemaining, Math.max(0, 2 - used));
    return remainingFree + balance.paidCredits > 0;
  } catch (error) {
    return used < 2;
  }
}

export async function consumeAssessmentCredit() {
  const installId = await getInstallId();
  let used = Number(await AsyncStorage.getItem(LOCAL_FREE_KEY) || 0);
  let synced = Number(await AsyncStorage.getItem(SERVER_FREE_SYNCED_KEY) || 0);
  try {
    // Carry offline free uses to the server before asking it for another credit.
    while (synced < used && synced < 2) {
      const caughtUp = await api(`/api/payments/consume/${installId}`, { method: 'POST' });
      if (caughtUp.consumed !== 'free') break;
      synced += 1;
      await AsyncStorage.setItem(SERVER_FREE_SYNCED_KEY, String(synced));
    }
    const result = await api(`/api/payments/consume/${installId}`, { method: 'POST' });
    if (result.consumed === 'free') {
      used = Math.min(2, used + 1);
      await AsyncStorage.setItem(LOCAL_FREE_KEY, String(used));
      await AsyncStorage.setItem(SERVER_FREE_SYNCED_KEY, String(2 - result.freeRemaining));
    } else if (result.consumed === 'paid') {
      await AsyncStorage.setItem(SERVER_FREE_SYNCED_KEY, '2');
    }
    return result;
  } catch (error) {
    if (error.status === 402) return null;
    // Exactly two offline assessments are available on a fresh installation.
    if (used >= 2) return null;
    await AsyncStorage.setItem(LOCAL_FREE_KEY, String(used + 1));
    return { consumed: 'free-offline', freeRemaining: Math.max(0, 1 - used), paidCredits: 0 };
  }
}
