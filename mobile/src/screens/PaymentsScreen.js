import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, TextInput, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as DocumentPicker from 'expo-document-picker';
import { colors, fonts, gradients, radius, spacing } from '../theme';
import { useDirection, useI18n } from '../i18n';
import { useAppState } from '../core/appState';
import { Button, Card, Pill, PressableScale, ScrollScreen, SectionTitle, Text } from '../components/ui';
import { groupThousands, toPersianDigits } from '../core/format';
import { checkRequest, flushBazaarPurchaseRecords, flushMyketPurchaseRecords, getApiBase, getInstallId, getOfflinePaymentConfig, grantBazaarPurchaseLocally, grantMyketPurchaseLocally, loadCreditBalance, loadPaymentPanel, localCreditBalance, queueBazaarPurchaseRecord, queueMyketPurchaseRecord, submitReceipt } from '../core/paymentApi';
import { getCafeBazaarBilling, isBazaarIabBuild, BAZAAR_RSA_PUBLIC_KEY } from '../core/bazaarBilling';
import { getMyketBilling, getMyketRsaPublicKey, isMyketIabBuild } from '../core/myketBilling';

const PACKAGES = [
  { sku: 'assessment_1', credits: 1, priceToman: 600000, discountPercent: 0, label: 'single' },
  { sku: 'assessment_3', credits: 3, priceToman: 1200000, discountPercent: 33.3, label: 'three' },
  { sku: 'assessment_6', credits: 6, priceToman: 2500000, discountPercent: 30.6, label: 'six' },
  { sku: 'assessment_12', credits: 12, priceToman: 4500000, discountPercent: 37.5, label: 'twelve' },
];

function amount(value, lang, t) {
  const separator = lang === 'fa' ? String.fromCharCode(0x066c) : ',';
  const formatted = groupThousands(value).replace(/,/g, separator);
  return `${lang === 'fa' ? toPersianDigits(formatted) : formatted} ${t('payments.toman')}`;
}

function discountLabel(value, lang, t) {
  const rawNumber = String(value);
  const number = lang === 'fa' ? toPersianDigits(rawNumber).replace('.', '٫') : rawNumber;
  const sign = lang === 'fa' ? String.fromCharCode(0x066a) : '%';
  return `${t('payments.discount')} ${number}${sign}`;
}

function visibleBankLabel(value, lang) {
  if (value.trim() === 'سامان' && lang === 'en') return 'Saman Bank';
  return lang === 'fa' && /[A-Za-z]/.test(value) ? '—' : value;
}

function localizedBazaarPrice(value, lang, t) {
  const latinDigits = String(value || '').replace(/[\u06f0-\u06f9\u0660-\u0669]/g, (digit) => {
    const code = digit.charCodeAt(0);
    return String(code >= 0x06f0 ? code - 0x06f0 : code - 0x0660);
  }).replace(/[\u066c\u060c]/g, ',');
  const tomanFa = String.fromCharCode(0x062a, 0x0648, 0x0645, 0x0627, 0x0646);
  const rialFa = String.fromCharCode(0x0631, 0x06cc, 0x0627, 0x0644);
  if (lang === 'fa') {
    return toPersianDigits(latinDigits)
      .replace(/,/g, String.fromCharCode(0x066c))
      .replace(/\bToman\b/gi, t('payments.toman'))
      .replace(/\bRial\b/gi, t('payments.rial'))
      .replace(/\bIRR\b/gi, t('payments.rial'))
      .replace(/\bIRT\b/gi, t('payments.toman'));
  }
  return latinDigits
    .replace(new RegExp(tomanFa, 'g'), t('payments.toman'))
    .replace(new RegExp(rialFa, 'g'), t('payments.rial'));
}

export default function PaymentsScreen({ navigation }) {
  const { t, lang, pick } = useI18n();
  const { privacyConsent, acceptPrivacyConsent } = useAppState();
  const bazaarIab = isBazaarIabBuild();
  const dir = useDirection();
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [panel, setPanel] = useState(null);
  const [selected, setSelected] = useState(PACKAGES[0].sku);
  const [transferDate, setTransferDate] = useState('');
  const [trackingCode, setTrackingCode] = useState('');
  const [phone, setPhone] = useState('');
  const [receipt, setReceipt] = useState(null);
  const [request, setRequest] = useState(null);
  const [balance, setBalance] = useState(null);
  const [bazaarPrices, setBazaarPrices] = useState({});
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [bazaarError, setBazaarError] = useState('');
  const myketIab = isMyketIabBuild();
  const [myketPrices, setMyketPrices] = useState({});
  const [myketCatalogLoading, setMyketCatalogLoading] = useState(false);
  const [myketError, setMyketError] = useState('');

  const refresh = useCallback(async () => {
    if ((bazaarIab || myketIab) && !privacyConsent) {
      setPanel(null);
      setRequest(null);
      setBalance(null);
      setLoading(false);
      return;
    }
    if (bazaarIab || myketIab) {
      setPanel(null);
      setRequest(null);
      setLoading(true);
      const local = await localCreditBalance();
      setBalance(local);
      setLoading(false);
      // The server merge is best-effort: the on-device ledger is the source of
      // truth for Bazaar credits, so a dead server must never block the screen.
      loadCreditBalance().then(setBalance).catch(() => { /* keep the local balance */ });
      (bazaarIab ? flushBazaarPurchaseRecords() : flushMyketPurchaseRecords()).catch(() => { /* best-effort record sync */ });
      return;
    }
    const fallback = getOfflinePaymentConfig();
    setPanel(fallback.enabled ? { ...fallback, canSubmitReceipt: !!getApiBase() } : null);
    setBalance(fallback.enabled ? { freeRemaining: 2, paidCredits: 0 } : null);
    setLoading(!fallback.enabled);
    try {
      const result = await loadPaymentPanel();
      setPanel(result.config);
      setBalance(result.balance);
      setRequest(result.request);
    } catch (error) {
      setPanel(fallback.enabled ? { ...fallback, canSubmitReceipt: !!getApiBase() } : null);
      setRequest(null);
    } finally {
      setLoading(false);
    }
  }, [bazaarIab, myketIab, privacyConsent]);

  useEffect(() => { refresh(); }, [refresh]);

  useEffect(() => {
    if (!bazaarIab || !privacyConsent) return undefined;
    let active = true;
    const loadBazaarCatalog = async () => {
      const billing = getCafeBazaarBilling();
      if (!billing) {
        setBazaarError(t('payments.bazaarUnavailable'));
        return;
      }
      setCatalogLoading(true);
      setBazaarError('');
      try {
        await billing.connect({ rsaPublicKey: BAZAAR_RSA_PUBLIC_KEY });
        const details = await billing.getInAppSkuDetails(PACKAGES.map((item) => item.sku));
        if (!active) return;
        const prices = Object.fromEntries((details || []).map((item) => [item.sku, item.price]).filter(([sku, price]) => sku && price));
        setBazaarPrices(prices);
        if (Object.keys(prices).length < PACKAGES.length) setBazaarError(t('payments.bazaarProductsUnavailable'));
      } catch (error) {
        if (active) setBazaarError(t('payments.bazaarUnavailable'));
      } finally {
        try { await billing.disconnect(); } catch (error) { /* no active connection to release */ }
        if (active) setCatalogLoading(false);
      }
    };
    loadBazaarCatalog();
    return () => { active = false; };
  }, [bazaarIab, privacyConsent, t]);

  useEffect(() => {
    if (!myketIab || !privacyConsent) return undefined;
    let active = true;
    const loadMyketCatalog = async () => {
      const billing = getMyketBilling();
      if (!billing) {
        setMyketError(`${t('payments.myketUnavailable')} (MODULE_MISSING)`);
        return;
      }
      setMyketCatalogLoading(true);
      setMyketError('');
      let stage = 'CONNECT';
      try {
        const rsaPublicKey = getMyketRsaPublicKey();
        if (!rsaPublicKey) throw new Error('RSA_KEY_MISSING');
        await billing.connect({ rsaPublicKey });
        stage = 'PRODUCTS';
        const details = await billing.getInAppSkuDetails(PACKAGES.map((item) => item.sku));
        if (!active) return;
        const prices = Object.fromEntries((details || []).map((item) => [item.sku, item.price]).filter(([sku, price]) => sku && price));
        setMyketPrices(prices);
        // Recover purchases on screen entry, not only before another purchase.
        stage = 'RECOVERY';
        const pending = await billing.getPurchasedProducts();
        for (const purchase of pending || []) {
          if (!active) break;
          await settleMyketPurchase(billing, purchase);
        }
        if (active) setBalance(await localCreditBalance());
        if (Object.keys(prices).length < PACKAGES.length) setMyketError(t('payments.myketProductsUnavailable'));
      } catch (error) {
        if (active) {
          // Diagnostic for internal APK testing: never print the RSA key or purchase data.
          const code = String(error?.code || error?.message || 'UNKNOWN').slice(0, 100);
          setMyketError(`${t('payments.myketUnavailable')} [${stage}: ${code}]`);
        }
      } finally {
        try { await billing.disconnect(); } catch (error) { /* no active connection to release */ }
        if (active) setMyketCatalogLoading(false);
      }
    };
    loadMyketCatalog();
    return () => { active = false; };
  }, [myketIab, privacyConsent, t]);

  const applyCreditDelta = (creditsAdded) => {
    if (!(creditsAdded > 0)) return;
    setBalance((prev) => (prev
      ? { ...prev, paidCredits: prev.paidCredits + creditsAdded }
      : { freeRemaining: 0, paidCredits: creditsAdded }));
  };

  // Completes a Bazaar purchase the way Bazaar's own guide prescribes: the SDK
  // already verified the purchase signature (SecurityCheck.Enable), so we grant
  // the credits on-device (idempotent per purchase token), consume the purchase
  // through the Bazaar app, and only then record the order on our server in the
  // background for support/refund bookkeeping. No step may depend on our server.
  const settleBazaarPurchase = async (billing, purchase) => {
    if (!purchase?.purchaseToken || !purchase?.originalJson || !purchase?.dataSignature) {
      throw new Error('INVALID_BAZAAR_PURCHASE_PROOF');
    }
    const sku = purchase.productId || purchase.sku;
    const pkg = PACKAGES.find((item) => item.sku === sku);
    if (!pkg) return null;
    const grant = await grantBazaarPurchaseLocally(purchase, pkg.credits);
    try {
      await billing.consumePurchase(purchase.purchaseToken);
    } catch (error) {
      // Keep the purchase pending on Bazaar's side; the next settle retries the
      // consume without granting the credits again.
    }
    queueBazaarPurchaseRecord(purchase, pkg.credits);
    return { creditsAdded: grant.creditsAdded, consumed: true };
  };

  const buyWithBazaar = async () => {
    if (bazaarIab && !privacyConsent) {
      Alert.alert(t('common.dismiss'), t('profile.acceptForOnline'));
      return;
    }
    const billing = getCafeBazaarBilling();
    if (!billing) {
      Alert.alert(t('common.dismiss'), t('payments.bazaarUnavailable'));
      return;
    }
    if (!bazaarPrices[selected]) {
      Alert.alert(t('common.dismiss'), t('payments.bazaarProductsUnavailable'));
      return;
    }
    setSending(true);
    setBazaarError('');
    try {
      await billing.connect({ rsaPublicKey: BAZAAR_RSA_PUBLIC_KEY });
      // Retry any purchase left unconsumed by an app close/interruption before
      // starting a new order. Recovery is best-effort: a broken recovery must
      // not block the purchase itself.
      const pending = await billing.getPurchasedProducts().catch(() => []);
      let recoveredCredits = 0;
      for (const purchase of pending || []) {
        const recovered = await settleBazaarPurchase(billing, purchase);
        if (recovered) {
          recoveredCredits += recovered.creditsAdded;
          applyCreditDelta(recovered.creditsAdded);
        }
      }
      if (recoveredCredits > 0) {
        Alert.alert(t('payments.bazaarPurchaseSuccess'));
        return;
      }
      const installId = await getInstallId();
      const purchase = await billing.purchaseProduct(selected, { developerPayload: installId });
      const result = await settleBazaarPurchase(billing, purchase);
      if (!result) throw new Error('INVALID_BAZAAR_PRODUCT');
      applyCreditDelta(result.creditsAdded);
      Alert.alert(t('payments.bazaarPurchaseSuccess'));
    } catch (error) {
      const message = t('payments.bazaarPurchaseError');
      setBazaarError(message);
      Alert.alert(t('common.dismiss'), message);
    } finally {
      try { await billing.disconnect(); } catch (error) { /* billing may already have disconnected */ }
      setSending(false);
    }
  };

  // Completes a Myket purchase per Myket's own guide: the SDK verifies the
  // purchase signature client-side (RSA public key), so we grant credits
  // on-device (idempotent per purchase token), consume the purchase through
  // the Myket app, and only then record the order on our server in the
  // background for support/refund bookkeeping. No step may depend on our server.
  const settleMyketPurchase = async (billing, purchase) => {
    if (!purchase?.token || !purchase?.originalJson || !purchase?.signature) {
      throw new Error('INVALID_MYKET_PURCHASE_PROOF');
    }
    const sku = purchase.sku;
    const pkg = PACKAGES.find((item) => item.sku === sku);
    if (!pkg) return null;
    const grant = await grantMyketPurchaseLocally(purchase, pkg.credits);
    let consumed = false;
    try {
      await billing.consumePurchase(purchase.token);
      consumed = true;
    } catch (error) {
      // Purchase remains pending; recovery retries without granting twice.
    }
    await queueMyketPurchaseRecord(purchase, pkg.credits);
    return { creditsAdded: grant.creditsAdded, consumed };
  };

  const buyWithMyket = async () => {
    if (myketIab && !privacyConsent) {
      Alert.alert(t('common.dismiss'), t('profile.acceptForOnline'));
      return;
    }
    const billing = getMyketBilling();
    if (!billing) {
      Alert.alert(t('common.dismiss'), t('payments.myketUnavailable'));
      return;
    }
    if (!myketPrices[selected]) {
      Alert.alert(t('common.dismiss'), t('payments.myketProductsUnavailable'));
      return;
    }
    setSending(true);
    setMyketError('');
    try {
      await billing.connect({ rsaPublicKey: getMyketRsaPublicKey() });
      // Retry any purchase left unconsumed by an app close/interruption before
      // starting a new order. Recovery is best-effort.
      const pending = await billing.getPurchasedProducts().catch(() => []);
      let recoveredCredits = 0;
      for (const purchase of pending || []) {
        const recovered = await settleMyketPurchase(billing, purchase);
        if (recovered) {
          recoveredCredits += recovered.creditsAdded;
          applyCreditDelta(recovered.creditsAdded);
        }
      }
      if (recoveredCredits > 0) {
        Alert.alert(t('payments.myketPurchaseSuccess'));
        return;
      }
      const installId = await getInstallId();
      const purchase = await billing.purchaseProduct(selected, { developerPayload: installId });
      const result = await settleMyketPurchase(billing, purchase);
      if (!result) throw new Error('INVALID_MYKET_PRODUCT');
      applyCreditDelta(result.creditsAdded);
      if (!result.consumed) throw new Error('MYKET_CONSUME_PENDING');
      Alert.alert(t('payments.myketPurchaseSuccess'));
    } catch (error) {
      const message = t('payments.myketPurchaseError');
      setMyketError(message);
      Alert.alert(t('common.dismiss'), message);
    } finally {
      try { await billing.disconnect(); } catch (error) { /* billing may already have disconnected */ }
      setSending(false);
    }
  };

  const chooseReceipt = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['image/jpeg', 'image/png', 'image/webp'],
        copyToCacheDirectory: true,
        multiple: false,
      });
      const asset = !result.canceled ? result.assets?.[0] : null;
      if (!asset) return;
      if (asset.size && asset.size > 5 * 1024 * 1024) {
        Alert.alert(t('payments.receipt'), t('payments.receiptTooLarge'));
        return;
      }
      setReceipt({ ...asset, fileName: asset.name || 'receipt.jpg', mimeType: asset.mimeType || 'image/jpeg' });
    } catch (error) {
      Alert.alert(t('payments.receipt'), t('payments.receiptSelectError'));
    }
  };

  const send = async () => {
    if (bazaarIab && !privacyConsent) {
      Alert.alert(t('common.dismiss'), t('profile.acceptForOnline'));
      return;
    }
    if (!transferDate.trim()) return Alert.alert(t('payments.noTransferDate'));
    if (trackingCode.trim().length < 4) return Alert.alert(t('payments.noTracking'));
    if (!receipt) return Alert.alert(t('payments.noReceipt'));
    setSending(true);
    try {
      const result = await submitReceipt({ sku: selected, transferDate: transferDate.trim(), trackingCode: trackingCode.trim(), phone: phone.trim(), receipt });
      setRequest({ id: result.requestId, status: 'pending', credits: result.credits });
      Alert.alert(t('payments.requestSent'));
      await refresh();
    } catch (error) {
      Alert.alert(t('common.dismiss'), error.message === 'API_NOT_CONFIGURED'
        ? t('payments.network')
        : t('payments.submitError'));
    } finally {
      setSending(false);
    }
  };

  const poll = async () => {
    if (!request?.id) return refresh();
    try {
      const result = await checkRequest(request.id);
      setRequest(result.request);
      setBalance(result.balance);
      if (result.request.status === 'approved') Alert.alert(t('payments.approved'));
    } catch (error) {
      Alert.alert(t('payments.statusError'));
    }
  };

  const activePackage = PACKAGES.find((item) => item.sku === selected) || PACKAGES[0];
  const onlineMode = !!getApiBase();
  const bazaarDisplayedPrice = bazaarPrices[selected]
    ? localizedBazaarPrice(bazaarPrices[selected], lang, t)
    : null;
  const bazaarBuyLabel = `${t('payments.bazaarBuy')} · ${t(`payments.${activePackage.label}`)}${bazaarDisplayedPrice ? ` · ${bazaarDisplayedPrice}` : ''}`;
  const myketDisplayedPrice = myketPrices[selected]
    ? localizedBazaarPrice(myketPrices[selected], lang, t)
    : null;
  const myketBuyLabel = `${t('payments.myketBuy')} · ${t(`payments.${activePackage.label}`)}${myketDisplayedPrice ? ` · ${myketDisplayedPrice}` : ''}`;

  useEffect(() => {
    if (bazaarIab || !onlineMode || !request?.id || request.status !== 'pending') return undefined;
    let active = true;
    const refreshPending = async () => {
      try {
        const result = await checkRequest(request.id);
        if (!active) return;
        setRequest(result.request);
        setBalance(result.balance);
        if (result.request.status === 'approved') Alert.alert(t('payments.approved'));
      } catch (error) {
        // Keep the pending state; the next poll or manual refresh can retry.
      }
    };
    const timer = setInterval(refreshPending, 8000);
    refreshPending();
    return () => { active = false; clearInterval(timer); };
  }, [bazaarIab, onlineMode, request?.id, request?.status, t]);

  const acceptOnlinePrivacy = async () => {
    const saved = await acceptPrivacyConsent();
    if (!saved) Alert.alert(t('common.dismiss'), t('profile.consentSaveError'));
  };

  if ((bazaarIab || myketIab) && !privacyConsent) {
    return (
      <ScrollScreen contentStyle={{ paddingBottom: 36 }}>
        <LinearGradient colors={gradients.hero} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
          <Text variant="h2" color={colors.white} style={{ textAlign: dir.text }}>{t('profile.consentTitle')}</Text>
        </LinearGradient>
        <View style={{ padding: spacing.md, gap: spacing.md }}>
          <Card>
            <Text variant="small" color={colors.ink70} style={{ textAlign: dir.text }}>
              {t(myketIab ? 'profile.privacyBodyMyket' : bazaarIab ? 'profile.privacyBodyBazaar' : 'profile.privacyBody')}
            </Text>
          </Card>
          <Button label={t('profile.acceptForOnline')} onPress={acceptOnlinePrivacy} />
          <Button label={t('profile.decline')} variant="outline" onPress={() => navigation.goBack()} />
          <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text }}>{t('profile.declineNote')}</Text>
        </View>
      </ScrollScreen>
    );
  }

  const card = panel?.card;
  const canShowCard = !!panel?.enabled && !!card;
  const receiptUploadAvailable = onlineMode && !!panel?.canSubmitReceipt;

  return (
    <ScrollScreen contentStyle={{ paddingBottom: 36 }}>
      <LinearGradient colors={gradients.hero} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
        <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.sm }}>
          <PressableScale onPress={() => navigation.goBack()} style={styles.back}>
            <Ionicons name={dir.isRtl ? 'arrow-forward' : 'arrow-back'} size={20} color={colors.white} />
          </PressableScale>
          <View style={{ flex: 1 }}>
            <Text variant="h2" color={colors.white} style={{ textAlign: dir.text }}>{t('payments.title')}</Text>
            <Text variant="small" style={{ color: 'rgba(255,255,255,0.8)', textAlign: dir.text, marginTop: 4 }}>{t('payments.subtitle')}</Text>
          </View>
        </View>
        <View style={[styles.balance, { flexDirection: dir.row }]}>
          <View style={styles.balanceIcon}><Ionicons name="sparkles" size={18} color={colors.teal700} /></View>
          <View style={{ flex: 1 }}>
            <Text variant="micro" style={{ color: 'rgba(255,255,255,.72)', textAlign: dir.text }}>{t('payments.remaining')}</Text>
            <Text variant="h3" color={colors.white} style={{ textAlign: dir.text }}>
              {lang === 'fa' ? toPersianDigits(String(balance?.freeRemaining ?? 2)) : String(balance?.freeRemaining ?? 2)}
              {'  ·  '}
              {t('payments.credits')}: {lang === 'fa' ? toPersianDigits(String(balance?.paidCredits ?? 0)) : String(balance?.paidCredits ?? 0)}
            </Text>
          </View>
        </View>
      </LinearGradient>

      <View style={{ padding: spacing.md, gap: spacing.md }}>
        <Card>
          <SectionTitle title={t('payments.packages')} subtitle={t(bazaarIab ? 'payments.bazaarCatalogIntro' : myketIab ? 'payments.myketCatalogIntro' : 'payments.pricesIntro')} />
          <View style={{ gap: spacing.xs, marginTop: spacing.md }}>
            {PACKAGES.map((item) => {
              const active = selected === item.sku;
              return (
                <PressableScale key={item.sku} onPress={() => setSelected(item.sku)}>
                  <View style={[styles.package, active && styles.packageActive]}>
                    <View style={[styles.radio, active && styles.radioActive]}>{active ? <View style={styles.radioDot} /> : null}</View>
                    <View style={{ flex: 1 }}>
                      <View style={{ flexDirection: dir.row, alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                        <Text variant="bodyStrong" style={{ color: colors.ink }}>{t(`payments.${item.label}`)}</Text>
                        {!bazaarIab && !myketIab && item.discountPercent > 0 ? <Pill label={discountLabel(item.discountPercent, lang, t)} tone="sky" /> : null}
                      </View>
                      {!bazaarIab && !myketIab ? (
                        <Text variant="micro" color={colors.ink50} style={{ marginTop: 3, textAlign: dir.text }}>
                          {amount(Math.round(item.priceToman / item.credits), lang, t)} {t('payments.perAssessment')}
                        </Text>
                      ) : null}
                    </View>
                    <Text variant="h3" style={{ color: active ? colors.teal700 : colors.ink70 }}>{bazaarIab ? (bazaarPrices[item.sku] ? localizedBazaarPrice(bazaarPrices[item.sku], lang, t) : (catalogLoading ? t('payments.priceLoading') : '—')) : myketIab ? (myketPrices[item.sku] ? localizedBazaarPrice(myketPrices[item.sku], lang, t) : (myketCatalogLoading ? t('payments.priceLoading') : '—')) : amount(item.priceToman, lang, t)}</Text>
                  </View>
                </PressableScale>
              );
            })}
          </View>
        </Card>

        {bazaarIab ? (
          <Card>
            <SectionTitle title={t('payments.bazaarPurchaseTitle')} subtitle={t('payments.bazaarPurchaseHint')} />
            {bazaarError ? (
              <View style={styles.notice}>
                <Ionicons name="information-circle-outline" size={22} color={colors.warn} />
                <Text variant="small" color={colors.ink70} style={{ flex: 1, textAlign: dir.text }}>{bazaarError}</Text>
              </View>
            ) : null}
            <Button
              label={sending ? t('payments.bazaarProcessing') : bazaarBuyLabel}
              icon="cart-outline"
              loading={sending || catalogLoading}
              disabled={sending || catalogLoading || !bazaarPrices[selected] || !onlineMode}
              onPress={buyWithBazaar}
              style={{ marginTop: spacing.md }}
            />
            {!onlineMode ? <Text variant="micro" color={colors.ink50} style={{ marginTop: spacing.sm, textAlign: dir.text }}>{t('payments.bazaarNeedsServer')}</Text> : null}
            <Text variant="micro" color={colors.ink50} style={{ marginTop: spacing.sm, textAlign: dir.text }}>{t('payments.bazaarPrivacy')}</Text>
          </Card>
        ) : myketIab ? (
          <Card>
            <SectionTitle title={t('payments.myketPurchaseTitle')} subtitle={t('payments.myketPurchaseHint')} />
            {myketError ? (
              <View style={styles.notice}>
                <Ionicons name="information-circle-outline" size={22} color={colors.warn} />
                <Text variant="small" color={colors.ink70} style={{ flex: 1, textAlign: dir.text }}>{myketError}</Text>
              </View>
            ) : null}
            <Button
              label={sending ? t('payments.myketProcessing') : myketBuyLabel}
              icon="cart-outline"
              loading={sending || myketCatalogLoading}
              disabled={sending || myketCatalogLoading || !myketPrices[selected]}
              onPress={buyWithMyket}
              style={{ marginTop: spacing.md }}
            />
            <Text variant="micro" color={colors.ink50} style={{ marginTop: spacing.sm, textAlign: dir.text }}>{t('payments.myketPrivacy')}</Text>
          </Card>
        ) : (
          <>
        <Card>
          <SectionTitle
            title={t('payments.transferTitle')}
            subtitle={canShowCard ? t(receiptUploadAvailable ? 'payments.transferHint' : 'payments.staticTransferHint') : undefined}
          />
          {loading && !panel ? (
            <ActivityIndicator color={colors.teal700} style={{ marginTop: spacing.md }} />
          ) : !canShowCard ? (
            <View style={styles.notice}>
              <Ionicons name="information-circle-outline" size={22} color={colors.warn} />
              <Text variant="small" color={colors.ink70} style={{ flex: 1, textAlign: dir.text }}>{t('payments.cardMissing')}</Text>
            </View>
          ) : (
            <>
              <View style={styles.cardDetails}>
                <View style={{ flexDirection: dir.row, justifyContent: 'space-between' }}>
                  <Text variant="micro" color={colors.ink50}>{t('payments.bank')}</Text>
                  <Text variant="small" color={colors.ink}>{visibleBankLabel(card.bank, lang)}</Text>
                </View>
                {card.holder ? (
                  <View style={{ flexDirection: dir.row, justifyContent: 'space-between', marginTop: 8 }}>
                    <Text variant="micro" color={colors.ink50}>{t('payments.cardHolder')}</Text>
                    <Text variant="small" color={colors.ink}>{visibleBankLabel(card.holder, lang)}</Text>
                  </View>
                ) : null}
                <View style={{ marginTop: 8 }}>
                  <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text }}>{t('payments.cardNumber')}</Text>
                  <Text selectable variant="h3" style={{ textAlign: 'center', color: colors.teal800, letterSpacing: 1.5, marginTop: 4 }}>
                    {lang === 'fa' ? toPersianDigits(card.number.replace(/\s/g, ' ')) : card.number}
                  </Text>
                </View>
              </View>
              <Text variant="micro" color={colors.ink50} style={{ marginTop: spacing.sm, textAlign: dir.text }}>{t('payments.cardTransferInstructions')}</Text>
            </>
          )}
          {canShowCard ? (
            <Text variant="micro" color={colors.ink50} style={{ marginTop: spacing.sm, textAlign: dir.text }}>{t(receiptUploadAvailable ? 'payments.privacy' : 'payments.staticCardPrivacy')}</Text>
          ) : null}
        </Card>

        <Card>
          <SectionTitle title={t('payments.uploadReceiptTitle')} subtitle={t('payments.uploadReceiptSubtitle')} />
          <View style={styles.form}>
            <Text variant="small" color={colors.ink70} style={{ textAlign: dir.text }}>{t('payments.selected')}: {t(`payments.${activePackage.label}`)}</Text>
            <Text variant="small" color={colors.ink70} style={{ textAlign: dir.text }}>{t('payments.amountLabel')}: {amount(activePackage.priceToman, lang, t)}</Text>
            <TextInput value={phone} onChangeText={setPhone} keyboardType="phone-pad" autoComplete="tel" placeholder={t('payments.phoneOptional')} placeholderTextColor={colors.ink35} style={[styles.input, { textAlign: dir.text }]} />
            <TextInput value={transferDate} onChangeText={setTransferDate} placeholder={t('payments.transferDatePlaceholder')} placeholderTextColor={colors.ink35} style={[styles.input, { textAlign: dir.text }]} />
            <TextInput value={trackingCode} onChangeText={setTrackingCode} autoCapitalize="none" placeholder={t('payments.tracking')} placeholderTextColor={colors.ink35} style={[styles.input, { textAlign: dir.text }]} />
            <Button label={receipt ? t('payments.receiptSelected') : t('payments.pickReceipt')} variant="outline" icon="document-attach-outline" onPress={chooseReceipt} />
            <Button label={t('payments.uploadReceiptTitle')} icon="cloud-upload-outline" loading={sending} disabled={!receiptUploadAvailable || sending} onPress={send} />
          </View>
          {!receiptUploadAvailable ? (
            <View style={[styles.notice, { marginTop: spacing.sm }]}>
              <Ionicons name="information-circle-outline" size={22} color={colors.warn} />
              <Text variant="small" color={colors.ink70} style={{ flex: 1, textAlign: dir.text }}>{t('payments.uploadNeedsServer')}</Text>
            </View>
          ) : (
            <Text variant="micro" color={colors.ink50} style={{ marginTop: spacing.sm, textAlign: dir.text }}>{t('payments.privacy')}</Text>
          )}
        </Card>


        </>
        )}

        {!bazaarIab && request ? (
          <Card>
            <SectionTitle title={t('payments.statusTitle')} />
            <View style={[styles.statusLine, { flexDirection: dir.row }]}>
              <Pill label={t(`payments.${request.status === 'approved' ? 'approved' : request.status === 'rejected' ? 'rejected' : 'pending'}`)} tone={request.status === 'approved' ? 'success' : request.status === 'rejected' ? 'danger' : 'warn'} />
              {lang === 'en' ? <Text variant="micro" color={colors.ink50} style={{ flex: 1, textAlign: dir.text }}>{request.id}</Text> : null}
            </View>
            {request.status === 'rejected' && request.rejectionReason ? (
              <Text variant="small" color={colors.ink70} style={{ marginTop: spacing.sm, textAlign: dir.text }}>{request.rejectionReason}</Text>
            ) : null}
            <Button label={t('payments.refresh')} variant="outline" size="sm" icon="refresh-outline" onPress={poll} style={{ marginTop: spacing.sm }} />
          </Card>
        ) : null}

        {loading ? <ActivityIndicator color={colors.teal700} /> : null}
      </View>
    </ScrollScreen>
  );
}

const styles = {
  hero: { paddingTop: spacing.xxl, paddingHorizontal: spacing.lg, paddingBottom: spacing.lg, borderBottomLeftRadius: radius.xxl, borderBottomRightRadius: radius.xxl },
  back: { width: 40, height: 40, borderRadius: 14, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,.15)' },
  balance: { marginTop: spacing.md, padding: spacing.sm, gap: 10, alignItems: 'center', borderRadius: radius.lg, backgroundColor: 'rgba(255,255,255,.13)' },
  balanceIcon: { width: 36, height: 36, borderRadius: 13, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.white },
  package: { flexDirection: 'row', gap: 10, alignItems: 'center', borderWidth: 1, borderColor: colors.border, borderRadius: radius.lg, padding: spacing.sm, backgroundColor: colors.surface },
  packageActive: { borderColor: colors.teal500, backgroundColor: colors.teal100 },
  radio: { width: 19, height: 19, borderRadius: 10, borderWidth: 1.5, borderColor: colors.ink35, alignItems: 'center', justifyContent: 'center' },
  radioActive: { borderColor: colors.teal700 },
  radioDot: { width: 9, height: 9, borderRadius: 5, backgroundColor: colors.teal700 },
  notice: { flexDirection: 'row', gap: 8, alignItems: 'center', padding: spacing.sm, marginTop: spacing.sm, borderRadius: radius.md, backgroundColor: colors.warnSoft },
  cardDetails: { backgroundColor: colors.canvas, borderRadius: radius.lg, padding: spacing.md, marginTop: spacing.md, borderWidth: 1, borderColor: colors.border },
  form: { marginTop: spacing.md, gap: spacing.sm },
  input: { minHeight: 48, borderWidth: 1, borderColor: colors.border, borderRadius: radius.md, paddingHorizontal: 12, color: colors.ink, backgroundColor: colors.surface, fontFamily: fonts.regular },
  statusLine: { alignItems: 'center', gap: 8, marginTop: spacing.sm },
};
