import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Alert, Modal, TextInput, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, fonts, gradients, radius, spacing } from '../theme';
import { useDirection, useI18n } from '../i18n';
import { countries } from '../core/data';
import { deleteExperience, getApiBase, listExperiences, reportExperience, submitExperience } from '../core/paymentApi';
import { Button, Card, Chip, Pill, PressableScale, ScrollScreen, SectionTitle, Text } from '../components/ui';

const STAGES = ['planning', 'applied', 'approved', 'refused', 'moved', 'living'];
const REPORT_REASONS = ['privacy', 'misleading', 'abuse', 'spam'];

function whenLabel(value, lang) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(lang === 'fa' ? 'fa-IR' : 'en-GB', { dateStyle: 'medium' });
}

export default function ExperiencesScreen() {
  const { t, lang, pick } = useI18n();
  const dir = useDirection();
  const [items, setItems] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [reportTarget, setReportTarget] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [destinationFilter, setDestinationFilter] = useState('');
  const [stageFilter, setStageFilter] = useState('');
  const [form, setForm] = useState({ title: '', body: '', destination: '', visaRoute: '', stage: 'planning', displayName: '' });

  const destination = useMemo(() => countries.find((item) => item.code === form.destination), [form.destination]);

  const refresh = useCallback(async () => {
    setLoading(true);
    setLoadError(false);
    try {
      const result = await listExperiences({ destination: destinationFilter || undefined, stage: stageFilter || undefined });
      setItems(result.items || []);
      setCount(result.count || 0);
    } catch (error) {
      setItems([]);
      setCount(0);
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  }, [destinationFilter, stageFilter]);

  useEffect(() => { refresh(); }, [refresh]);

  const loadMore = async () => {
    if (loadingMore || items.length >= count) return;
    setLoadingMore(true);
    try {
      const result = await listExperiences({ destination: destinationFilter || undefined, stage: stageFilter || undefined, offset: items.length });
      setItems((current) => [...current, ...(result.items || [])]);
    } catch (error) {
      Alert.alert(t('common.dismiss'), t('experiences.submitError'));
    } finally {
      setLoadingMore(false);
    }
  };

  const updateForm = (patch) => setForm((current) => ({ ...current, ...patch }));

  const send = async () => {
    if (form.title.trim().length < 8 || form.body.trim().length < 80 || !form.destination) {
      Alert.alert(t('common.dismiss'), t('experiences.formValidation'));
      return;
    }
    setSubmitting(true);
    try {
      await submitExperience({ ...form, title: form.title.trim(), body: form.body.trim(), visaRoute: form.visaRoute.trim(), displayName: form.displayName.trim() });
      setForm({ title: '', body: '', destination: '', visaRoute: '', stage: 'planning', displayName: '' });
      setShowForm(false);
      await refresh();
      Alert.alert(t('experiences.submittedTitle'), t('experiences.submittedBody'));
    } catch (error) {
      Alert.alert(t('common.dismiss'), error.status === 429 ? t('experiences.rateLimit') : t('experiences.submitError'));
    } finally {
      setSubmitting(false);
    }
  };

  const sendReport = async (reason) => {
    if (!reportTarget) return;
    const item = reportTarget;
    setReportTarget(null);
    try {
      await reportExperience(item.id, reason);
      Alert.alert(t('common.dismiss'), t('experiences.reportThanks'));
    } catch (error) {
      Alert.alert(t('common.dismiss'), error.status === 409 ? t('experiences.reportDuplicate') : t('experiences.reportError'));
    }
  };

  const remove = (item) => Alert.alert(t('experiences.deleteTitle'), t('experiences.deleteBody'), [
    { text: t('common.cancel'), style: 'cancel' },
    { text: t('common.delete'), style: 'destructive', onPress: () => deleteExperience(item.id).then(refresh).catch(() => Alert.alert(t('common.dismiss'), t('experiences.deleteError'))) },
  ]);

  const countryName = (code) => {
    const match = countries.find((item) => item.code === code);
    return match ? pick(match.nameFa, match.nameEn) : code;
  };

  return (
    <>
    <ScrollScreen contentStyle={{ paddingBottom: 128 }}>
      <LinearGradient colors={gradients.hero} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
        <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.sm }}>
          <View style={styles.heroIcon}><Ionicons name="chatbubbles" size={22} color={colors.teal700} /></View>
          <View style={{ flex: 1 }}>
            <Text variant="h1" color={colors.white} style={{ textAlign: dir.text }}>{t('experiences.title')}</Text>
            <Text variant="small" style={{ color: 'rgba(255,255,255,0.8)', marginTop: 4, textAlign: dir.text }}>{t('experiences.subtitle')}</Text>
          </View>
        </View>
        <Button label={showForm ? t('experiences.closeForm') : t('experiences.share')} icon={showForm ? 'close-outline' : 'create-outline'} variant="light" onPress={() => setShowForm((value) => !value)} style={{ marginTop: spacing.md }} />
      </LinearGradient>

      <View style={{ padding: spacing.md, gap: spacing.md }}>
        <Card style={{ backgroundColor: colors.goldSoft, borderColor: '#E8D9AE' }}>
          <View style={{ flexDirection: dir.row, gap: spacing.xs, alignItems: 'flex-start' }}>
            <Ionicons name="information-circle-outline" size={18} color={colors.gold} />
            <Text variant="micro" color={colors.ink70} style={{ flex: 1, textAlign: dir.text }}>{t('experiences.notice')}</Text>
          </View>
        </Card>

        {!getApiBase() ? (
          <Card><Text variant="small" color={colors.warn} style={{ textAlign: dir.text }}>{t('experiences.serverUnavailable')}</Text></Card>
        ) : null}

        {showForm ? (
          <Card>
            <SectionTitle title={t('experiences.formTitle')} subtitle={t('experiences.moderationNote')} />
            <Text variant="micro" color={colors.ink60} style={{ textAlign: dir.text, marginTop: spacing.md }}>{t('experiences.destination')}</Text>
            <View style={[styles.chips, { flexDirection: dir.row }]}>
              {countries.map((item) => <Chip key={item.code} label={pick(item.nameFa, item.nameEn)} active={form.destination === item.code} onPress={() => updateForm({ destination: item.code })} />)}
            </View>
            <Text variant="micro" color={colors.ink60} style={{ textAlign: dir.text, marginTop: spacing.md }}>{t('experiences.stage')}</Text>
            <View style={[styles.chips, { flexDirection: dir.row }]}>
              {STAGES.map((stage) => <Chip key={stage} label={t(`experiences.stages.${stage}`)} active={form.stage === stage} onPress={() => updateForm({ stage })} />)}
            </View>
            <TextInput value={form.visaRoute} onChangeText={(visaRoute) => updateForm({ visaRoute })} maxLength={80} placeholder={t('experiences.routePlaceholder')} placeholderTextColor={colors.ink35} style={[styles.input, { textAlign: dir.text, writingDirection: dir.writing, marginTop: spacing.md }]} />
            <TextInput value={form.title} onChangeText={(title) => updateForm({ title })} maxLength={100} placeholder={t('experiences.titlePlaceholder')} placeholderTextColor={colors.ink35} style={[styles.input, { textAlign: dir.text, writingDirection: dir.writing }]} />
            <TextInput value={form.body} onChangeText={(body) => updateForm({ body })} multiline maxLength={3000} placeholder={t('experiences.bodyPlaceholder')} placeholderTextColor={colors.ink35} style={[styles.input, styles.bodyInput, { textAlign: dir.text, writingDirection: dir.writing }]} />
            <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text }}>{form.body.length}/3000</Text>
            <TextInput value={form.displayName} onChangeText={(displayName) => updateForm({ displayName })} maxLength={32} placeholder={t('experiences.namePlaceholder')} placeholderTextColor={colors.ink35} style={[styles.input, { textAlign: dir.text, writingDirection: dir.writing }]} />
            <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text }}>{t('experiences.anonymousNote')}</Text>
            <Button label={t('experiences.submit')} icon="send-outline" loading={submitting} disabled={!destination || submitting} onPress={send} style={{ marginTop: spacing.md }} />
          </Card>
        ) : null}

        <Card>
          <SectionTitle title={t('experiences.feedTitle')} subtitle={`${count} ${t('experiences.publishedCount')}`} />
          <Text variant="micro" color={colors.ink60} style={{ textAlign: dir.text, marginTop: spacing.md }}>{t('experiences.filterDestination')}</Text>
          <View style={[styles.chips, { flexDirection: dir.row }]}>
            <Chip label={t('common.all')} active={!destinationFilter} onPress={() => setDestinationFilter('')} />
            {countries.map((item) => <Chip key={item.code} label={pick(item.nameFa, item.nameEn)} active={destinationFilter === item.code} onPress={() => setDestinationFilter(destinationFilter === item.code ? '' : item.code)} />)}
          </View>
          <View style={[styles.chips, { flexDirection: dir.row, marginTop: spacing.sm }]}>
            <Chip label={t('common.all')} active={!stageFilter} onPress={() => setStageFilter('')} />
            {STAGES.map((stage) => <Chip key={stage} label={t(`experiences.stages.${stage}`)} active={stageFilter === stage} onPress={() => setStageFilter(stageFilter === stage ? '' : stage)} />)}
          </View>
          <Button label={t('experiences.refresh')} variant="outline" size="sm" icon="refresh-outline" onPress={refresh} loading={loading} style={{ marginTop: spacing.md }} />
        </Card>

        {loading ? <ActivityIndicator color={colors.teal700} /> : null}
        {!loading && items.length === 0 ? <Card><Text variant="small" color={loadError ? colors.warn : colors.ink60} style={{ textAlign: dir.text }}>{t(loadError ? 'experiences.serverUnavailable' : 'experiences.empty')}</Text></Card> : null}
        {items.map((item) => (
          <Card key={item.id}>
            <View style={{ flexDirection: dir.row, alignItems: 'flex-start', justifyContent: 'space-between', gap: spacing.xs }}>
              <View style={{ flex: 1 }}>
                <Text variant="bodyStrong" color={colors.ink} style={{ textAlign: dir.text }}>{item.title}</Text>
                <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text, marginTop: 4 }}>{countryName(item.destination)} · {t(`experiences.stages.${item.stage}`)} · {whenLabel(item.createdAt, lang)}</Text>
                {item.moderationStatus !== 'approved' ? <Pill label={t(`experiences.moderation.${item.moderationStatus}`)} tone={item.moderationStatus === 'rejected' ? 'danger' : 'warn'} /> : null}
              </View>
              <Pill label={item.displayName || t('experiences.anonymous')} tone="teal" />
            </View>
            {item.visaRoute ? <Text variant="micro" color={colors.teal700} style={{ textAlign: dir.text, marginTop: spacing.sm }}>{t('experiences.route')}: {item.visaRoute}</Text> : null}
            <Text variant="small" color={colors.ink70} style={{ textAlign: dir.text, marginTop: spacing.sm, lineHeight: 24 }}>{item.body}</Text>
            <View style={[styles.cardActions, { flexDirection: dir.row }]}>
              <PressableScale onPress={() => setReportTarget(item)} style={[styles.textAction, { flexDirection: dir.row }]}>
                <Ionicons name="flag-outline" size={15} color={colors.ink50} /><Text variant="micro" color={colors.ink50}>{t('experiences.report')}</Text>
              </PressableScale>
              {item.canDelete ? <PressableScale onPress={() => remove(item)} style={[styles.textAction, { flexDirection: dir.row }]}><Ionicons name="trash-outline" size={15} color={colors.danger} /><Text variant="micro" color={colors.danger}>{t('common.delete')}</Text></PressableScale> : null}
            </View>
          </Card>
        ))}
        {!loading && items.length < count ? <Button label={t('experiences.loadMore')} variant="outline" icon="chevron-down-outline" loading={loadingMore} onPress={loadMore} /> : null}
      </View>
    </ScrollScreen>
    <Modal visible={!!reportTarget} transparent animationType="fade" onRequestClose={() => setReportTarget(null)}>
      <View style={styles.modalBackdrop}>
        <Card style={styles.modalCard}>
          <SectionTitle title={t('experiences.reportTitle')} subtitle={t('experiences.reportBody')} />
          <View style={{ gap: spacing.xs, marginTop: spacing.md }}>
            {REPORT_REASONS.map((reason) => <Button key={reason} label={t(`experiences.reportReasons.${reason}`)} variant="outline" size="sm" onPress={() => sendReport(reason)} />)}
            <Button label={t('common.cancel')} variant="ghost" size="sm" onPress={() => setReportTarget(null)} />
          </View>
        </Card>
      </View>
    </Modal>
    </>
  );
}

const styles = {
  hero: { paddingTop: spacing.xxl, paddingHorizontal: spacing.lg, paddingBottom: spacing.lg, borderBottomLeftRadius: radius.xxl, borderBottomRightRadius: radius.xxl },
  heroIcon: { width: 44, height: 44, borderRadius: 15, backgroundColor: colors.white, alignItems: 'center', justifyContent: 'center' },
  chips: { flexWrap: 'wrap', gap: spacing.xs, marginTop: spacing.xs },
  input: { minHeight: 48, borderWidth: 1, borderColor: colors.border, borderRadius: radius.md, backgroundColor: colors.canvas, paddingHorizontal: spacing.sm, paddingVertical: spacing.sm, color: colors.ink, fontFamily: fonts.medium, fontSize: 14, marginTop: spacing.sm },
  bodyInput: { minHeight: 170, textAlignVertical: 'top', lineHeight: 22 },
  cardActions: { alignItems: 'center', justifyContent: 'flex-end', gap: spacing.md, marginTop: spacing.md, paddingTop: spacing.sm, borderTopWidth: 1, borderTopColor: colors.border },
  textAction: { alignItems: 'center', gap: 4, padding: 4 },
  modalBackdrop: { flex: 1, backgroundColor: 'rgba(10,25,35,0.52)', alignItems: 'center', justifyContent: 'center', padding: spacing.md },
  modalCard: { width: '100%', maxWidth: 520 },
};
