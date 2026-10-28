import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';
import * as Crypto from 'expo-crypto';
import paymentCardFallback from './paymentCard.generated';
import { verifyOfflineVoucher } from './offlineVouchers';

const INSTALL_KEY = 'visayar.install.id';
const LOCAL_FREE_KEY = 'visayar.free.assessments.used.v1';
const SERVER_FREE_SYNCED_KEY = 'visayar.free.assessments.server-synced.v1';
const LAST_REQUEST_KEY = 'visayar.payment.request.v1';
const OFFLINE_PAID_STATE_KEY = 'visayar.offline-paid-state.v1';

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

export async function loadPaymentPanel() {
  const [installId, requestId, local] = await Promise.all([
    getInstallId(),
    AsyncStorage.getItem(LAST_REQUEST_KEY),
    localBalance(),
  ]);
  const config = getOfflinePaymentConfig();
  // The requested product mode is static card display. Use the embedded card
  // immediately, regardless of an unrelated or unavailable API configuration.
  if (config.enabled || !getApiBase()) {
    return { installId, requestId: null, config, balance: local, request: null };
  }
  try {
    const serverConfig = await api('/api/payments/config');
    const serverBalance = await api(`/api/payments/credits/${installId}`);
    const request = requestId && !requestId.startsWith('manual:')
      ? await api(`/api/payments/requests/${requestId}?install_id=${installId}`)
      : null;
    const serverCardNumber = String(serverConfig.card?.number || '').replace(/\D/g, '');
    const hasUsableServerCard = serverConfig.enabled && serverCardNumber.length === 16 && !!String(serverConfig.card?.bank || '').trim();
    return {
      installId,
      requestId,
      config: hasUsableServerCard ? serverConfig : config,
      balance: { ...serverBalance, paidCredits: serverBalance.paidCredits + local.paidCredits },
      request,
    };
  } catch (error) {
    return { installId, requestId, config, balance: local, request: null };
  }
}

export async function submitReceipt({ sku, transferDate, trackingCode, receipt }) {
  const installId = await getInstallId();
  const body = new FormData();
  body.append('install_id', installId);
  body.append('sku', sku);
  body.append('phone', '');
  body.append('transfer_date', transferDate || '');
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
