import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';
import * as Crypto from 'expo-crypto';
import * as SecureStore from 'expo-secure-store';
import paymentCardFallback from './paymentCard.generated';
import { verifyOfflineVoucher } from './offlineVouchers';

const INSTALL_KEY = 'visayar.install.id';
const LOCAL_FREE_KEY = 'visayar.free.assessments.used.v1';
const SERVER_FREE_SYNCED_KEY = 'visayar.free.assessments.server-synced.v1';
const LAST_REQUEST_KEY = 'visayar.payment.request.v1';
const OFFLINE_PAID_STATE_KEY = 'visayar.offline-paid-state.v1';
const ADMIN_TOKEN_KEY = 'visayar.admin.session.v1';

export async function getInstallId() {
  let id = await AsyncStorage.getItem(INSTALL_KEY);
  if (!id) {
    id = Crypto.randomUUID();
    await AsyncStorage.setItem(INSTALL_KEY, id);
  }
  return id;
}

function appExtra() {
  return Constants.expoConfig?.extra
    || Constants.manifest2?.extra?.expoClient?.extra
    || Constants.manifest?.extra
    || {};
}

export function getApiBase() {
  const configured = appExtra().apiBaseUrl || '';
  if (configured) return configured.replace(/\/$/, '');
  if (typeof window !== 'undefined' && window.location?.origin) return window.location.origin;
  return '';
}

export function getOfflinePaymentConfig() {
  const candidates = [appExtra().paymentCard, paymentCardFallback];
  const source = candidates.find((candidate) => String(candidate?.number || '').replace(/\D/g, '').length === 16) || {};
  const number = String(source.number || '').replace(/\D/g, '');
  const holder = String(source.holder || '').trim();
  const bank = String(source.bank || '').trim();
  const enabled = number.length === 16 && !!bank;
  return { enabled, offlineMode: true, freeAssessments: 2, card: enabled ? { number, holder, bank } : null };
}

async function readOfflinePaidState() {
  try {
    const raw = await AsyncStorage.getItem(OFFLINE_PAID_STATE_KEY);
    const state = raw ? JSON.parse(raw) : {};
    return {
      credits: Math.max(0, Number(state.credits) || 0),
      voucherIds: Array.isArray(state.voucherIds) ? state.voucherIds : [],
    };
  } catch (error) {
    return { credits: 0, voucherIds: [] };
  }
}

async function localBalance() {
  const used = Number(await AsyncStorage.getItem(LOCAL_FREE_KEY) || 0);
  const paid = await readOfflinePaidState();
  return { freeRemaining: Math.max(0, 2 - used), paidCredits: paid.credits };
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

async function readAdminToken() {
  try { return await SecureStore.getItemAsync(ADMIN_TOKEN_KEY); } catch (error) { return null; }
}

async function clearAdminToken() {
  try { await SecureStore.deleteItemAsync(ADMIN_TOKEN_KEY); } catch (error) { /* unsupported platforms have no secure storage */ }
}

async function adminApi(path, options = {}) {
  const token = await readAdminToken();
  if (!token) {
    const error = new Error('ADMIN_LOGIN_REQUIRED');
    error.status = 401;
    throw error;
  }
  const headers = { ...(options.headers || {}), Authorization: `Bearer ${token}` };
  return api(path, { ...options, headers });
}

export async function getAdminSession() {
  try {
    const result = await adminApi('/api/admin/auth/me');
    return { authenticated: true, username: result.username };
  } catch (error) {
    if (error.status === 401) await clearAdminToken();
    return { authenticated: false };
  }
}

export async function adminLogin(username, password) {
  const result = await api('/api/admin/auth/mobile-login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  await SecureStore.setItemAsync(ADMIN_TOKEN_KEY, result.accessToken);
  return { authenticated: true, username: result.username };
}

export async function adminLogout() {
  try {
    await adminApi('/api/admin/auth/logout', { method: 'POST' });
  } finally {
    await clearAdminToken();
  }
}

export async function adminListPayments(status = 'pending') {
  return adminApi(`/api/admin/payments?status=${encodeURIComponent(status)}`);
}

export async function adminReviewPayment(requestId, decision, reason = '') {
  const path = `/api/admin/payments/${encodeURIComponent(requestId)}/${decision}`;
  const options = decision === 'reject'
    ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reason }) }
    : { method: 'POST' };
  return adminApi(path, options);
}

export async function getAdminToken() {
  return readAdminToken();
}

export async function loadPaymentPanel() {
  const [installId, requestId, local] = await Promise.all([
    getInstallId(),
    AsyncStorage.getItem(LAST_REQUEST_KEY),
    localBalance(),
  ]);
  const offlineConfig = getOfflinePaymentConfig();
  if (!getApiBase()) {
    return { installId, requestId: null, config: { ...offlineConfig, canSubmitReceipt: false }, balance: local, request: null };
  }
  try {
    const [serverConfig, serverBalance] = await Promise.all([
      api('/api/payments/config'),
      api(`/api/payments/credits/${installId}`),
    ]);
    const request = requestId
      ? await api(`/api/payments/requests/${requestId}?install_id=${installId}`).catch(() => null)
      : null;
    const serverCardNumber = String(serverConfig.card?.number || '').replace(/\D/g, '');
    const hasUsableServerCard = serverConfig.enabled && serverCardNumber.length === 16 && !!String(serverConfig.card?.bank || '').trim();
    return {
      installId,
      requestId,
      config: offlineConfig.enabled
        ? { ...offlineConfig, canSubmitReceipt: true }
        : { ...serverConfig, enabled: hasUsableServerCard, canSubmitReceipt: true },
      balance: { ...serverBalance, paidCredits: serverBalance.paidCredits + local.paidCredits },
      request,
    };
  } catch (error) {
    return {
      installId,
      requestId,
      config: { ...offlineConfig, canSubmitReceipt: true },
      balance: local,
      request: null,
    };
  }
}

export async function submitReceipt({ sku, transferDate, trackingCode, phone = '', receipt }) {
  const installId = await getInstallId();
  const body = new FormData();
  body.append('install_id', installId);
  body.append('sku', sku);
  body.append('phone', phone);
  body.append('transfer_date', transferDate || '');
  body.append('tracking_code', trackingCode);
  const fileName = receipt.fileName || receipt.name || 'receipt.jpg';
  const extension = fileName.toLowerCase().split('.').pop();
  const mimeType = receipt.mimeType || ({ png: 'image/png', webp: 'image/webp', jpg: 'image/jpeg', jpeg: 'image/jpeg' }[extension] || 'image/jpeg');
  if (receipt.file) body.append('receipt', receipt.file, fileName);
  else body.append('receipt', { uri: receipt.uri, name: fileName, type: mimeType });
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

export async function redeemOfflineVoucher(code) {
  const installId = await getInstallId();
  const payload = verifyOfflineVoucher(code, installId);
  const state = await readOfflinePaidState();
  if (state.voucherIds.includes(payload.id)) throw new Error('VOUCHER_ALREADY_USED');
  state.credits += payload.credits;
  state.voucherIds = [...state.voucherIds, payload.id];
  await AsyncStorage.setItem(OFFLINE_PAID_STATE_KEY, JSON.stringify(state));
  return { creditsAdded: payload.credits, paidCredits: state.credits };
}

async function consumeLocalCredit(used) {
  if (used < 2) {
    const nextUsed = Math.min(2, used + 1);
    await AsyncStorage.setItem(LOCAL_FREE_KEY, String(nextUsed));
    return { consumed: 'free-offline', freeRemaining: Math.max(0, 2 - nextUsed), paidCredits: (await readOfflinePaidState()).credits };
  }
  const state = await readOfflinePaidState();
  if (state.credits < 1) return null;
  state.credits -= 1;
  await AsyncStorage.setItem(OFFLINE_PAID_STATE_KEY, JSON.stringify(state));
  return { consumed: 'paid-offline', freeRemaining: 0, paidCredits: state.credits };
}

export async function hasAssessmentAccess() {
  const installId = await getInstallId();
  const used = Number(await AsyncStorage.getItem(LOCAL_FREE_KEY) || 0);
  const local = await readOfflinePaidState();
  if (await readAdminToken()) {
    const session = await getAdminSession();
    if (session.authenticated) return true;
  }
  try {
    const balance = await api(`/api/payments/credits/${installId}`);
    const remainingFree = Math.min(balance.freeRemaining, Math.max(0, 2 - used));
    return remainingFree + balance.paidCredits + local.credits > 0;
  } catch (error) {
    return used < 2 || local.credits > 0;
  }
}

export async function consumeAssessmentCredit() {
  const installId = await getInstallId();
  let used = Number(await AsyncStorage.getItem(LOCAL_FREE_KEY) || 0);
  let synced = Number(await AsyncStorage.getItem(SERVER_FREE_SYNCED_KEY) || 0);
  const adminToken = await readAdminToken();
  if (adminToken) {
    try {
      const result = await api(`/api/payments/consume/${installId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${adminToken}` },
      });
      if (result.consumed === 'admin') return result;
    } catch (error) {
      if (error.status === 401) await clearAdminToken();
      else return null;
    }
  }
  if (!getApiBase()) return consumeLocalCredit(used);
  try {
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
    if (error.status === 402) return consumeLocalCredit(Math.max(used, 2));
    return consumeLocalCredit(used);
  }
}
