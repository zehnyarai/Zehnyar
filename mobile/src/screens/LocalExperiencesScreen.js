import React, { useEffect, useState } from 'react';
import { Alert, TextInput, View } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';
import { colors, fonts, radius, spacing } from '../theme';
import { useDirection, useI18n } from '../i18n';
import { getCountries } from '../core/data';
import { Button, Card, Chip, ScrollScreen, SectionTitle, Text } from '../components/ui';

const STORAGE_KEY = 'visayar.private-experiences.v1';
const STAGES = ['planning', 'applied', 'approved', 'refused', 'moved', 'living'];
const blank = () => ({ title: '', body: '', destination: '', visaRoute: '', stage: 'planning' });

export default function LocalExperiencesScreen() {
  const { t, pick, lang } = useI18n();
  const dir = useDirection();
  const countries = getCountries();
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(blank);
  const [editing, setEditing] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [readFailed, setReadFailed] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let alive = true;
    AsyncStorage.getItem(STORAGE_KEY).then((raw) => {
      const parsed = raw ? JSON.parse(raw) : [];
      if (alive) setItems(Array.isArray(parsed) ? parsed : []);
    }).catch(() => {
      if (alive) { setReadFailed(true); Alert.alert(t('common.dismiss'), t('experiences.localReadError')); }
    }).finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, []);

  const save = async () => {
    if (saving || loading || readFailed) return;
    if (!form.destination || form.title.trim().length < 8 || form.body.trim().length < 80) {
      Alert.alert(t('common.dismiss'), t('experiences.formValidation'));
      return;
    }
    const normalized = {
      ...form, title: form.title.trim(), body: form.body.trim(), visaRoute: form.visaRoute.trim(),
    };
    const next = editing
      ? items.map((item) => item.id === editing ? { ...item, ...normalized } : item)
      : [{ ...normalized, id: `${Date.now()}-${Math.random().toString(36).slice(2)}`, createdAt: new Date().toISOString() }, ...items];
    setSaving(true);
    try {
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      setItems(next);
      setForm(blank());
      setEditing(null);
      setShowForm(false);
      Alert.alert(t('experiences.submittedTitle'), t('experiences.localSaved'));
    } catch (error) {
      Alert.alert(t('common.dismiss'), t('experiences.localSaveError'));
    } finally { setSaving(false); }
  };

  const remove = (id) => Alert.alert(t('experiences.deleteTitle'), t('experiences.localDeleteConfirm'), [
    { text: t('common.cancel'), style: 'cancel' },
    { text: t('common.delete'), style: 'destructive', onPress: async () => {
      const next = items.filter((item) => item.id !== id);
      try {
        await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        setItems(next);
        if (editing === id) { setEditing(null); setForm(blank()); setShowForm(false); }
      } catch (error) { Alert.alert(t('common.dismiss'), t('experiences.localSaveError')); }
    } },
  ]);

  const inputStyle = [styles.input, { textAlign: dir.text, writingDirection: dir.writing }];
  const countryName = (code) => {
    const country = countries.find((item) => item.code === code);
    return country ? pick(country.nameFa, country.nameEn) : code;
  };
  return (
    <ScrollScreen contentStyle={{ padding: spacing.md, paddingBottom: 128, gap: spacing.md }}>
      <Card>
        <SectionTitle title={t('experiences.title')} subtitle={t('experiences.localSubtitle')} />
        <Text variant="small" color={colors.ink70} style={{ textAlign: dir.text, marginTop: spacing.sm }}>{t('experiences.localNotice')}</Text>
        <Button label={showForm ? t('experiences.closeForm') : t('experiences.share')} icon={showForm ? 'close-outline' : 'create-outline'} onPress={() => { setShowForm(!showForm); setEditing(null); setForm(blank()); }} style={{ marginTop: spacing.md }} />
      </Card>
      {showForm ? <Card>
        <SectionTitle title={editing ? t('experiences.localEdit') : t('experiences.formTitle')} />
        <Text variant="small" color={colors.ink70} style={{ textAlign: dir.text, marginTop: spacing.md }}>{t('experiences.destination')}</Text>
        <View style={[styles.chips, { flexDirection: dir.row }]}>{countries.map((item) => <Chip key={item.code} label={pick(item.nameFa, item.nameEn)} active={form.destination === item.code} onPress={() => setForm((current) => ({ ...current, destination: item.code }))} />)}</View>
        <Text variant="small" color={colors.ink70} style={{ textAlign: dir.text, marginTop: spacing.md }}>{t('experiences.stage')}</Text>
        <View style={[styles.chips, { flexDirection: dir.row }]}>{STAGES.map((stage) => <Chip key={stage} label={t(`experiences.stages.${stage}`)} active={form.stage === stage} onPress={() => setForm((current) => ({ ...current, stage }))} />)}</View>
        <TextInput value={form.visaRoute} onChangeText={(visaRoute) => setForm((current) => ({ ...current, visaRoute }))} maxLength={80} placeholder={t('experiences.routePlaceholder')} placeholderTextColor={colors.ink35} style={inputStyle} />
        <TextInput value={form.title} onChangeText={(title) => setForm((current) => ({ ...current, title }))} maxLength={100} placeholder={t('experiences.titlePlaceholder')} placeholderTextColor={colors.ink35} style={inputStyle} />
        <TextInput value={form.body} onChangeText={(body) => setForm((current) => ({ ...current, body }))} maxLength={3000} multiline placeholder={t('experiences.bodyPlaceholder')} placeholderTextColor={colors.ink35} style={[...inputStyle, styles.body]} />
        <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text }}>{form.body.length}/3000</Text>
        <Button label={t('experiences.localSave')} icon="save-outline" loading={saving} disabled={saving || loading || readFailed} onPress={save} style={{ marginTop: spacing.md }} />
      </Card> : null}
      <Card><SectionTitle title={t('experiences.localList')} subtitle={`${items.length}`} /></Card>
      {!loading && items.length === 0 ? <Card><Text variant="small" color={colors.ink70}>{t('experiences.localEmpty')}</Text></Card> : null}
      {items.map((item) => <Card key={item.id}>
        <Text variant="bodyStrong" color={colors.ink} style={{ textAlign: dir.text }}>{item.title}</Text>
        <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text }}>{countryName(item.destination)} · {t(`experiences.stages.${item.stage}`)} · {new Date(item.createdAt).toLocaleDateString(lang === 'fa' ? 'fa-IR' : 'en-GB')}</Text>
        {item.visaRoute ? <Text variant="small" color={colors.ink70} style={{ textAlign: dir.text }}>{item.visaRoute}</Text> : null}
        <Text variant="small" color={colors.ink70} style={{ textAlign: dir.text, marginTop: spacing.sm }}>{item.body}</Text>
        <View style={[styles.actions, { flexDirection: dir.row }]}>
          <Button label={t('experiences.localEdit')} size="sm" variant="outline" icon="create-outline" onPress={() => { setForm({ title: item.title, body: item.body, destination: item.destination, visaRoute: item.visaRoute, stage: item.stage }); setEditing(item.id); setShowForm(true); }} />
          <Button label={t('common.delete')} size="sm" variant="outline" icon="trash-outline" onPress={() => remove(item.id)} />
        </View>
      </Card>)}
    </ScrollScreen>
  );
}

const styles = {
  chips: { flexWrap: 'wrap', gap: spacing.xs, marginTop: spacing.xs },
  input: { minHeight: 48, borderWidth: 1, borderColor: colors.border, borderRadius: radius.md, backgroundColor: colors.canvas, paddingHorizontal: spacing.sm, paddingVertical: spacing.sm, color: colors.ink, fontFamily: fonts.medium, fontSize: 14, marginTop: spacing.sm },
  body: { minHeight: 150, textAlignVertical: 'top' },
  actions: { gap: spacing.sm, marginTop: spacing.md, flexWrap: 'wrap' },
};
