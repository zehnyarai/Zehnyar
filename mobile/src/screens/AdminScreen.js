import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Alert, Image, Linking, Modal, TextInput, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, gradients, radius, spacing } from '../theme';
import { useDirection, useI18n } from '../i18n';
import { Button, Card, Pill, PressableScale, ScrollScreen, SectionTitle, Text } from '../components/ui';
import { toPersianDigits } from '../core/format';
import { adminListPayments, adminLogin, adminLogout, adminReviewPayment, getAdminSession, getAdminToken, getApiBase } from '../core/paymentApi';

const FILTERS = ['pending', 'approved', 'rejected', 'all'];

function amount(value, lang) {
  const formatted = Number(value || 0).toLocaleString(lang === 'fa' ? 'fa-IR' : 'en-US');
  return `${formatted} ${lang === 'fa' ? 'تومان' : 'toman'}`;
}

function dateLabel(value, lang) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(lang === 'fa' ? 'fa-IR' : 'en-GB', { dateStyle: 'medium', timeStyle: 'short' });
}

function statusTone(status) {
  if (status === 'approved') return 'success';
  if (status === 'rejected') return 'danger';
  return 'warn';
}

export default function AdminScreen({ navigation }) {
  const { t, lang } = useI18n();
  const dir = useDirection();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [session, setSession] = useState(null);
  const [allItems, setAllItems] = useState([]);
  const [filter, setFilter] = useState('pending');
  const [search, setSearch] = useState('');
  const [imageRequest, setImageRequest] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);
  const [rejectTarget, setRejectTarget] = useState(null);
  const [rejectReason, setRejectReason] = useState('');

  const loadQueue = useCallback(async () => {
    const result = await adminListPayments('all');
    setAllItems(result.items || []);
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const current = await getAdminSession();
      setSession(current);
      if (!current.authenticated) {
        setToken(null);
        setAllItems([]);
        return;
      }
      setToken(await getAdminToken());
      await loadQueue();
    } catch (error) {
      if (error.status === 401) setSession({ authenticated: false });
      else Alert.alert(t('common.dismiss'), t('admin.loadError'));
    } finally {
      setLoading(false);
    }
  }, [loadQueue, t]);

  useEffect(() => { refresh(); }, [refresh]);

  const counts = useMemo(() => ({
    pending: allItems.filter((item) => item.status === 'pending').length,
    approved: allItems.filter((item) => item.status === 'approved').length,
    rejected: allItems.filter((item) => item.status === 'rejected').length,
    all: allItems.length,
  }), [allItems]);

  const visibleItems = useMemo(() => {
    const needle = search.trim().toLocaleLowerCase();
    return allItems.filter((item) => {
      const matchesFilter = filter === 'all' || item.status === filter;
      const haystack = `${item.trackingCode || ''} ${item.phone || ''} ${item.sku || ''}`.toLocaleLowerCase();
      return matchesFilter && (!needle || haystack.includes(needle));
    });
  }, [allItems, filter, search]);

  const signIn = async () => {
    if (!username.trim() || !password) {
      Alert.alert(t('common.dismiss'), t('admin.credentialsRequired'));
      return;
    }
    setLoading(true);
    try {
      await adminLogin(username.trim(), password);
      setPassword('');
      await refresh();
    } catch (error) {
      Alert.alert(t('common.dismiss'), error.status === 401 ? t('admin.loginFailed') : t('admin.loginUnavailable'));
    } finally {
      setLoading(false);
    }
  };

  const signOut = async () => {
    try { await adminLogout(); } catch (error) { /* local credentials are cleared regardless */ }
    setSession({ authenticated: false });
    setToken(null);
    setAllItems([]);
    setImageRequest(null);
  };

  const approve = (item) => {
    Alert.alert(t('admin.approveTitle'), t('admin.approveBody'), [
      { text: t('common.cancel'), style: 'cancel' },
      {
        text: t('admin.approve'),
        onPress: () => {
          setBusyId(item.id);
          adminReviewPayment(item.id, 'approve')
            .then(loadQueue)
            .catch(() => Alert.alert(t('common.dismiss'), t('admin.reviewError')))
            .finally(() => setBusyId(null));
        },
      },
    ]);
  };

  const beginReject = (item) => {
    setRejectTarget(item);
    setRejectReason('');
  };

  const reject = async () => {
    if (!rejectTarget || rejectReason.trim().length < 3) {
      Alert.alert(t('common.dismiss'), t('admin.reasonRequired'));
      return;
    }
    const item = rejectTarget;
    setBusyId(item.id);
    try {
      await adminReviewPayment(item.id, 'reject', rejectReason.trim());
      setRejectTarget(null);
      setRejectReason('');
      await loadQueue();
    } catch (error) {
      Alert.alert(t('common.dismiss'), t('admin.reviewError'));
    } finally {
      setBusyId(null);
    }
  };

  const receiptUrl = imageRequest && getApiBase()
    ? `${getApiBase()}/api/admin/payments/${encodeURIComponent(imageRequest)}/receipt`
    : null;

  return (
    <ScrollScreen contentStyle={{ paddingBottom: 36 }}>
      <LinearGradient colors={gradients.hero} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
        <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.sm }}>
          <PressableScale onPress={() => navigation.goBack()} style={styles.back}>
            <Ionicons name={dir.isRtl ? 'arrow-forward' : 'arrow-back'} size={20} color={colors.white} />
          </PressableScale>
          <View style={{ flex: 1 }}>
            <Text variant="h2" color={colors.white} style={{ textAlign: dir.text }}>{t('admin.title')}</Text>
            <Text variant="small" style={{ color: 'rgba(255,255,255,0.8)', textAlign: dir.text, marginTop: 4 }}>{t('admin.subtitle')}</Text>
          </View>
        </View>
      </LinearGradient>

      <View style={{ padding: spacing.md, gap: spacing.md }}>
        {loading && !session?.authenticated ? <ActivityIndicator color={colors.teal700} /> : null}
        {!session?.authenticated ? (
          <Card>
            <SectionTitle title={t('admin.loginTitle')} subtitle={t('admin.secureNote')} />
            <View style={styles.form}>
              <TextInput value={username} onChangeText={setUsername} autoCapitalize="none" autoCorrect={false} placeholder={t('admin.username')} placeholderTextColor={colors.ink35} style={[styles.input, { textAlign: dir.text }]} />
              <TextInput value={password} onChangeText={setPassword} secureTextEntry autoCapitalize="none" placeholder={t('admin.password')} placeholderTextColor={colors.ink35} style={[styles.input, { textAlign: dir.text }]} />
              <Button label={t('admin.login')} icon="lock-closed-outline" loading={loading} onPress={signIn} />
            </View>
          </Card>
        ) : (
          <>
            <Card>
              <View style={{ flexDirection: dir.row, alignItems: 'center', justifyContent: 'space-between', gap: spacing.sm }}>
                <View style={{ flex: 1 }}>
                  <SectionTitle title={t('admin.dashboardTitle')} subtitle={t('admin.dashboardSubtitle')} />
                </View>
                <Button label={t('admin.logout')} variant="outline" size="sm" icon="log-out-outline" onPress={signOut} />
              </View>
              <View style={[styles.metrics, { flexDirection: dir.row }]}>
                {FILTERS.slice(0, 3).map((key) => (
                  <View key={key} style={styles.metric}>
                    <Text variant="h3" style={{ color: key === 'pending' ? colors.warn : key === 'approved' ? colors.success : colors.danger }}>
                      {lang === 'fa' ? toPersianDigits(String(counts[key])) : String(counts[key])}
                    </Text>
                    <Text variant="micro" color={colors.ink60} style={{ textAlign: 'center' }}>{t(`admin.filter.${key}`)}</Text>
                  </View>
                ))}
              </View>
              <View style={[styles.actions, { flexDirection: dir.row }]}>
                <Button label={t('admin.refresh')} variant="outline" size="sm" icon="refresh-outline" loading={loading} onPress={refresh} />
                {getApiBase() ? <Button label={t('admin.openFullPanel')} variant="outline" size="sm" icon="open-outline" onPress={() => Linking.openURL(`${getApiBase()}/admin/payments`).catch(() => Alert.alert(t('common.dismiss'), t('admin.openPanelError')))} /> : null}
              </View>
            </Card>

            <Card>
              <SectionTitle title={t('admin.queueTitle')} subtitle={`${lang === 'fa' ? toPersianDigits(String(visibleItems.length)) : visibleItems.length} ${t('admin.requests')}`} />
              <TextInput value={search} onChangeText={setSearch} autoCapitalize="none" autoCorrect={false} placeholder={t('admin.search')} placeholderTextColor={colors.ink35} style={[styles.input, { textAlign: dir.text, marginTop: spacing.sm }]} />
              <View style={[styles.filters, { flexDirection: dir.row }]}>
                {FILTERS.map((key) => (
                  <PressableScale key={key} onPress={() => setFilter(key)} style={[styles.filter, filter === key && styles.filterActive]}>
                    <Text variant="micro" style={{ color: filter === key ? colors.white : colors.ink70 }}>
                      {t(`admin.filter.${key}`)} · {lang === 'fa' ? toPersianDigits(String(counts[key])) : String(counts[key])}
                    </Text>
                  </PressableScale>
                ))}
              </View>
            </Card>

            {imageRequest && receiptUrl ? (
              <Card>
                <SectionTitle title={t('admin.receiptPreview')} />
                <Image source={{ uri: receiptUrl, headers: { Authorization: `Bearer ${token}` } }} resizeMode="contain" style={styles.receiptImage} />
                <Button label={t('admin.closeReceipt')} variant="outline" size="sm" onPress={() => setImageRequest(null)} style={{ marginTop: spacing.sm }} />
              </Card>
            ) : null}

            {visibleItems.map((item) => (
              <Card key={item.id}>
                <View style={{ flexDirection: dir.row, alignItems: 'center', justifyContent: 'space-between', gap: spacing.sm }}>
                  <Text variant="bodyStrong" color={colors.ink}>{t(`payments.${item.sku === 'assessment_1' ? 'single' : item.sku === 'assessment_3' ? 'three' : item.sku === 'assessment_6' ? 'six' : 'twelve'}`)}</Text>
                  <Pill label={t(`admin.filter.${item.status}`)} tone={statusTone(item.status)} />
                </View>
                <Text variant="small" color={colors.ink70} style={{ marginTop: spacing.sm, textAlign: dir.text }}>{amount(item.priceToman, lang)} · {lang === 'fa' ? toPersianDigits(String(item.credits)) : item.credits} {t('admin.credits')}</Text>
                <View style={[styles.details, { flexDirection: dir.row }]}>
                  <Text variant="micro" color={colors.ink50} style={{ flex: 1, textAlign: dir.text }}>{t('admin.transferDate')}: {item.transferDate ? toPersianDigits(item.transferDate) : t('admin.notProvided')}</Text>
                  <Text variant="micro" color={colors.ink50} style={{ flex: 1, textAlign: dir.text }}>{t('admin.receivedAt')}: {dateLabel(item.createdAt, lang)}</Text>
                </View>
                {item.phone ? <Text variant="micro" color={colors.ink50} style={{ marginTop: 4, textAlign: dir.text }}>{t('admin.phone')}: {toPersianDigits(item.phone)}</Text> : null}
                <Text variant="micro" color={colors.ink50} style={{ marginTop: 4, textAlign: dir.text }}>{t('admin.tracking')}: {item.trackingCode}</Text>
                {item.status === 'rejected' && item.rejectionReason ? <Text variant="micro" color={colors.danger} style={{ marginTop: 6, textAlign: dir.text }}>{t('admin.rejectionReason')}: {item.rejectionReason}</Text> : null}
                <View style={[styles.actions, { flexDirection: dir.row }]}>
                  <Button label={t('admin.viewReceipt')} variant="outline" size="sm" icon="image-outline" onPress={() => setImageRequest(item.id)} />
                  {item.status === 'pending' ? <>
                    <Button label={t('admin.approve')} size="sm" icon="checkmark-circle-outline" loading={busyId === item.id} onPress={() => approve(item)} />
                    <Button label={t('admin.reject')} variant="outline" size="sm" icon="close-circle-outline" loading={busyId === item.id} onPress={() => beginReject(item)} />
                  </> : null}
                </View>
              </Card>
            ))}
            {!loading && visibleItems.length === 0 ? (
              <Card><Text variant="small" color={colors.ink70} style={{ textAlign: dir.text }}>{search ? t('admin.noSearchResults') : t('admin.empty')}</Text></Card>
            ) : null}
            {loading ? <ActivityIndicator color={colors.teal700} /> : null}
          </>
        )}
      </View>

      <Modal visible={!!rejectTarget} transparent animationType="fade" onRequestClose={() => setRejectTarget(null)}>
        <View style={styles.modalBackdrop}>
          <Card style={styles.modalCard}>
            <SectionTitle title={t('admin.rejectTitle')} subtitle={t('admin.rejectBody')} />
            <TextInput value={rejectReason} onChangeText={setRejectReason} multiline maxLength={240} placeholder={t('admin.reasonPlaceholder')} placeholderTextColor={colors.ink35} style={[styles.input, styles.reasonInput, { textAlign: dir.text }]} />
            <View style={[styles.actions, { flexDirection: dir.row }]}>
              <Button label={t('common.cancel')} variant="outline" size="sm" onPress={() => setRejectTarget(null)} />
              <Button label={t('admin.reject')} variant="outline" size="sm" loading={busyId === rejectTarget?.id} onPress={reject} />
            </View>
          </Card>
        </View>
      </Modal>
    </ScrollScreen>
  );
}

const styles = {
  hero: { paddingTop: spacing.xxl, paddingHorizontal: spacing.lg, paddingBottom: spacing.lg, borderBottomLeftRadius: radius.xxl, borderBottomRightRadius: radius.xxl },
  back: { width: 40, height: 40, borderRadius: 14, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,.15)' },
  form: { gap: spacing.sm, marginTop: spacing.md },
  input: { minHeight: 48, borderWidth: 1, borderColor: colors.border, borderRadius: radius.md, paddingHorizontal: spacing.md, color: colors.ink, backgroundColor: colors.canvas },
  metrics: { gap: spacing.xs, marginTop: spacing.md },
  metric: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 3, minHeight: 64, borderRadius: radius.md, backgroundColor: colors.canvas },
  filters: { gap: 6, flexWrap: 'wrap', marginTop: spacing.sm },
  filter: { paddingHorizontal: 10, paddingVertical: 7, borderRadius: radius.pill, backgroundColor: colors.canvas },
  filterActive: { backgroundColor: colors.teal700 },
  details: { gap: spacing.xs, marginTop: spacing.sm, flexWrap: 'wrap' },
  actions: { gap: spacing.xs, flexWrap: 'wrap', marginTop: spacing.md, justifyContent: 'flex-start' },
  receiptImage: { width: '100%', height: 320, marginTop: spacing.sm, backgroundColor: colors.canvas, borderRadius: radius.md },
  modalBackdrop: { flex: 1, justifyContent: 'center', padding: spacing.md, backgroundColor: 'rgba(10,30,30,.55)' },
  modalCard: { width: '100%', maxWidth: 520, alignSelf: 'center' },
  reasonInput: { minHeight: 100, textAlignVertical: 'top', paddingTop: spacing.sm, marginTop: spacing.md },
};
