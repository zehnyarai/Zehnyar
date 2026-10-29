import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, TextInput, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as DocumentPicker from 'expo-document-picker';
import { colors, fonts, gradients, radius, spacing } from '../theme';
import { useDirection, useI18n } from '../i18n';
import { Button, Card, Pill, PressableScale, ScrollScreen, SectionTitle, Text } from '../components/ui';
import { groupThousands, toPersianDigits } from '../core/format';
import { checkRequest, getApiBase, getOfflinePaymentConfig, loadPaymentPanel, submitReceipt } from '../core/paymentApi';

const PACKAGES = [
  { sku: 'assessment_1', credits: 1, priceToman: 600000, discountPercent: 0, label: 'single' },
  { sku: 'assessment_3', credits: 3, priceToman: 1500000, discountPercent: 17, label: 'three' },
  { sku: 'assessment_6', credits: 6, priceToman: 2700000, discountPercent: 25, label: 'six' },
  { sku: 'assessment_12', credits: 12, priceToman: 4800000, discountPercent: 33, label: 'twelve' },
];

function amount(value, lang, t) {
  const separator = lang === 'fa' ? String.fromCharCode(0x066c) : ',';
  const formatted = groupThousands(value).replace(/,/g, separator);
  return `${lang === 'fa' ? toPersianDigits(formatted) : formatted} ${t('payments.toman')}`;
}

function discountLabel(value, lang, t) {
  const number = lang === 'fa' ? toPersianDigits(String(value)) : String(value);
  const sign = lang === 'fa' ? String.fromCharCode(0x066a) : '%';
  return `${t('payments.discount')} ${number}${sign}`;
}

function visibleBankLabel(value, lang) {
  if (value.trim() === 'سامان' && lang === 'en') return 'Saman Bank';
  return lang === 'fa' && /[A-Za-z]/.test(value) ? '—' : value;
}

export default function PaymentsScreen({ navigation }) {
  const { t, lang, pick } = useI18n();
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

  const refresh = useCallback(async () => {
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
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

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

  useEffect(() => {
    if (!onlineMode || !request?.id || request.status !== 'pending') return undefined;
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
  }, [onlineMode, request?.id, request?.status, t]);

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
          <SectionTitle title={t('payments.packages')} subtitle={t('payments.pricesIntro')} />
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
                        {item.discountPercent > 0 ? <Pill label={discountLabel(item.discountPercent, lang, t)} tone="sky" /> : null}
                      </View>
                      <Text variant="micro" color={colors.ink50} style={{ marginTop: 3, textAlign: dir.text }}>
                        {amount(Math.round(item.priceToman / item.credits), lang, t)} {t('payments.perAssessment')}
                      </Text>
                    </View>
                    <Text variant="h3" style={{ color: active ? colors.teal700 : colors.ink70 }}>{amount(item.priceToman, lang, t)}</Text>
                  </View>
                </PressableScale>
              );
            })}
          </View>
        </Card>

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


        {request ? (
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
