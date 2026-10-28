import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Image, TextInput, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, gradients, radius, spacing } from '../theme';
import { useDirection, useI18n } from '../i18n';
import { Button, Card, Pill, PressableScale, ScrollScreen, SectionTitle, Text } from '../components/ui';
import { toPersianDigits } from '../core/format';
import { adminListPayments, adminLogin, adminLogout, adminReviewPayment, getAdminSession, getAdminToken, getApiBase } from '../core/paymentApi';

function amount(value, lang) {
  const formatted = Number(value || 0).toLocaleString(lang === 'fa' ? 'fa-IR' : 'en-US');
  return `${formatted} ${lang === 'fa' ? 'تومان' : 'toman'}`;
}

export default function AdminScreen({ navigation }) {
  const { t, lang } = useI18n();
  const dir = useDirection();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [session, setSession] = useState(null);
  const [items, setItems] = useState([]);
  const [imageRequest, setImageRequest] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const current = await getAdminSession();
      setSession(current);
      if (!current.authenticated) {
        setToken(null);
        setItems([]);
        return;
      }
      setToken(await getAdminToken());
      const result = await adminListPayments('pending');
      setItems(result.items || []);
    } catch (error) {
      if (error.status === 401) setSession({ authenticated: false });
      else Alert.alert(t('common.dismiss'), t('admin.loadError'));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => { refresh(); }, [refresh]);

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
    setItems([]);
    setImageRequest(null);
  };

  const review = async (item, decision) => {
    const proceed = () => {
      setBusyId(item.id);
      adminReviewPayment(item.id, decision, t('admin.rejectReason'))
        .then(() => {
          setImageRequest(null);
          return refresh();
        })
        .catch(() => Alert.alert(t('common.dismiss'), t('admin.reviewError')))
        .finally(() => setBusyId(null));
    };
    if (decision === 'approve') {
      Alert.alert(t('admin.approveTitle'), t('admin.approveBody'), [
        { text: t('common.cancel'), style: 'cancel' },
        { text: t('admin.approve'), onPress: proceed },
      ]);
    } else {
      Alert.alert(t('admin.rejectTitle'), t('admin.rejectBody'), [
        { text: t('common.cancel'), style: 'cancel' },
        { text: t('admin.reject'), style: 'destructive', onPress: proceed },
      ]);
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
                  <SectionTitle title={t('admin.queueTitle')} subtitle={`${lang === 'fa' ? toPersianDigits(String(items.length)) : items.length} ${t('admin.requests')}`} />
                </View>
                <Button label={t('admin.logout')} variant="outline" size="sm" icon="log-out-outline" onPress={signOut} />
              </View>
              <Button label={t('admin.refresh')} variant="outline" size="sm" icon="refresh-outline" onPress={refresh} style={{ marginTop: spacing.sm }} />
            </Card>
            {imageRequest && receiptUrl ? (
              <Card>
                <SectionTitle title={t('admin.receiptPreview')} />
                <Image source={{ uri: receiptUrl, headers: { Authorization: `Bearer ${token}` } }} resizeMode="contain" style={styles.receiptImage} />
                <Button label={t('admin.closeReceipt')} variant="outline" size="sm" onPress={() => setImageRequest(null)} style={{ marginTop: spacing.sm }} />
              </Card>
            ) : null}
            {items.map((item) => (
              <Card key={item.id}>
                <View style={{ flexDirection: dir.row, alignItems: 'center', justifyContent: 'space-between', gap: spacing.sm }}>
                  <Text variant="bodyStrong" color={colors.ink}>{t(`payments.${item.sku === 'assessment_1' ? 'single' : item.sku === 'assessment_3' ? 'three' : item.sku === 'assessment_6' ? 'six' : 'twelve'}`)}</Text>
                  <Pill label={t('admin.pending')} tone="warn" />
                </View>
                <Text variant="small" color={colors.ink70} style={{ marginTop: spacing.sm, textAlign: dir.text }}>{amount(item.priceToman, lang)} · {lang === 'fa' ? toPersianDigits(String(item.credits)) : item.credits} {t('admin.credits')}</Text>
                <Text variant="micro" color={colors.ink50} style={{ marginTop: 4, textAlign: dir.text }}>{t('admin.transferDate')}: {item.transferDate || t('admin.notProvided')}</Text>
                <Text variant="micro" color={colors.ink50} style={{ marginTop: 4, textAlign: dir.text }}>{t('admin.tracking')}: {item.trackingCode}</Text>
                <View style={[styles.actions, { flexDirection: dir.row }]}>
                  <Button label={t('admin.viewReceipt')} variant="outline" size="sm" icon="image-outline" onPress={() => setImageRequest(item.id)} />
                  <Button label={t('admin.approve')} size="sm" icon="checkmark-circle-outline" loading={busyId === item.id} onPress={() => review(item, 'approve')} />
                  <Button label={t('admin.reject')} variant="outline" size="sm" icon="close-circle-outline" loading={busyId === item.id} onPress={() => review(item, 'reject')} />
                </View>
              </Card>
            ))}
            {!loading && items.length === 0 ? (
              <Card><Text variant="small" color={colors.ink70} style={{ textAlign: dir.text }}>{t('admin.empty')}</Text></Card>
            ) : null}
            {loading ? <ActivityIndicator color={colors.teal700} /> : null}
          </>
        )}
      </View>
    </ScrollScreen>
  );
}

const styles = {
  hero: { paddingTop: spacing.xxl, paddingHorizontal: spacing.lg, paddingBottom: spacing.lg, borderBottomLeftRadius: radius.xxl, borderBottomRightRadius: radius.xxl },
  back: { width: 40, height: 40, borderRadius: 14, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,.15)' },
  form: { gap: spacing.sm, marginTop: spacing.md },
  input: { minHeight: 48, borderWidth: 1, borderColor: colors.border, borderRadius: radius.md, paddingHorizontal: spacing.md, color: colors.ink, backgroundColor: colors.canvas },
  actions: { gap: spacing.xs, flexWrap: 'wrap', marginTop: spacing.md, justifyContent: 'flex-start' },
  receiptImage: { width: '100%', height: 320, marginTop: spacing.sm, backgroundColor: colors.canvas, borderRadius: radius.md },
};
