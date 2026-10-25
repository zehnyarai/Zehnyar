import React, { useEffect, useMemo, useState } from 'react';
import { Linking, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, fonts, gradients, radius, spacing } from '../theme';
import { useDirection, useI18n } from '../i18n';
import { useAppState } from '../core/appState';
import { dataset, findCountry } from '../core/data';
import engine from '../core/engine';
import { loadChecklist, saveChecklist } from '../core/storage';
import {
  Button, Card, Chip, Divider, KeyValue, Pill, PressableScale, ProgressBar,
  ScrollScreen, SectionTitle, Stepper, Text, TrustBadge,
} from '../components/ui';
import { ChanceDial } from '../components/charts';
import { ChecklistItem, FeeList, VisaCard } from '../components/cards';
import { money, num, percent, scorePair } from '../core/format';

const TABS = ['overview', 'visas', 'costs', 'documents'];

function baseDocuments() {
  return [
    { id: 'doc_passport', fa: 'گذرنامه معتبر با اعتبار دست‌کم شش ماه', en: 'Valid passport with at least six months validity' },
    { id: 'doc_photo', fa: 'عکس بیومتریک مطابق استاندارد سفارت', en: 'Biometric photograph to embassy standard' },
    { id: 'doc_form', fa: 'فرم درخواست تکمیل‌شده', en: 'Completed application form' },
    { id: 'doc_police', fa: 'گواهی عدم سوءپیشینه کیفری', en: 'Police clearance certificate' },
    { id: 'doc_medical', fa: 'گواهی سلامت و آزمایش‌های پزشکی', en: 'Medical examination and health certificate' },
  ];
}

export default function CountryDetailScreen({ route, navigation }) {
  const { code } = route.params || {};
  const { t, lang, pick } = useI18n();
  const dir = useDirection();
  const { result } = useAppState();
  const [tab, setTab] = useState('overview');
  const [familySize, setFamilySize] = useState(1);
  const [expandedVisa, setExpandedVisa] = useState(null);
  const [selectedVisaId, setSelectedVisaId] = useState(null);
  const [checked, setChecked] = useState([]);

  const country = useMemo(() => findCountry(code), [code]);
  const assessed = useMemo(() => (result ? result.countries.find((item) => item.code === code) : null), [result, code]);
  const bestVisaId = assessed ? assessed.best.visaId : country && country.visas[0] ? country.visas[0].id : null;

  useEffect(() => {
    if (!selectedVisaId) setSelectedVisaId(bestVisaId);
  }, [bestVisaId, selectedVisaId]);

  useEffect(() => {
    if (!selectedVisaId) return;
    loadChecklist(selectedVisaId).then((items) => setChecked(items));
  }, [selectedVisaId]);

  if (!country) {
    return (
      <ScrollScreen>
        <View style={{ padding: spacing.xl }}>
          <Text variant="h3">{t('explore.noResult')}</Text>
        </View>
      </ScrollScreen>
    );
  }

  const selectedVisa = country.visas.find((visa) => visa.id === selectedVisaId) || country.visas[0];
  const costs = engine.visaCosts(dataset, selectedVisa, familySize, 'USD');
  const scoredSelected = assessed ? assessed.visas.find((visa) => visa.visaId === selectedVisa.id) : null;

  const documents = [
    ...baseDocuments(),
    ...selectedVisa.requirementsFa.map((item, index) => ({
      id: `req_${selectedVisa.id}_${index}`,
      fa: item,
      en: selectedVisa.requirementsEn[index] || '',
    })),
  ];

  const toggleDoc = (id) => {
    const next = checked.includes(id) ? checked.filter((item) => item !== id) : [...checked, id];
    setChecked(next);
    saveChecklist(selectedVisa.id, next);
  };

  return (
    <ScrollScreen>
      <LinearGradient colors={gradients.hero} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
        <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.sm }}>
          <Text style={{ fontSize: 34 }}>{country.flag}</Text>
          <View style={{ flex: 1 }}>
            <Text variant="h1" color={colors.white} style={{ textAlign: dir.text }}>{pick(country.nameFa, country.nameEn)}</Text>
            <Text variant="micro" style={{ color: 'rgba(255,255,255,0.72)', textAlign: dir.text }} numberOfLines={2}>
              {pick(country.summaryFa, country.summaryEn)}
            </Text>
          </View>
        </View>

        {scoredSelected ? (
          <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.md, marginTop: spacing.md }}>
            <ChanceDial value={scoredSelected.chance} size={124} strokeWidth={10} sublabel={t('results.chanceLabel')} />
            <View style={{ flex: 1, gap: 6 }}>
              <Text variant="h3" color={colors.white} style={{ textAlign: dir.text }}>
                {pick(country.visas.find((v) => v.id === scoredSelected.visaId).nameFa, country.visas.find((v) => v.id === scoredSelected.visaId).nameEn)}
              </Text>
              <Text variant="micro" style={{ color: 'rgba(255,255,255,0.75)', textAlign: dir.text }}>
                {`${t('results.readinessLabel')}: ${percent(scoredSelected.readiness, lang)}`}
              </Text>
              <View style={{ flexDirection: dir.row, gap: 6, flexWrap: 'wrap' }}>
                {scoredSelected.eligible
                  ? <Pill label={t('results.eligible')} tone="success" icon="checkmark-circle" />
                  : <Pill label={t('results.needsFix')} tone="warn" icon="alert-circle" />}
                <Pill label={scorePair(scoredSelected.achieved, scoredSelected.maxPoints, lang)} tone="sky" />
              </View>
            </View>
          </View>
        ) : (
          <View style={{ flexDirection: dir.row, gap: 6, marginTop: spacing.sm, flexWrap: 'wrap' }}>
            {Array.from(new Set(country.visas.map((visa) => visa.type))).map((type) => (
              <Pill key={type} label={t(`visaTypes.${type}`)} tone="sky" />
            ))}
          </View>
        )}

        <View style={{ marginTop: spacing.md, flexDirection: dir.row, gap: spacing.xs }}>
          {TABS.map((item) => (
            <PressableScale key={item} onPress={() => setTab(item)} style={{ flex: 1 }}>
              <View style={[styles.tab, tab === item && styles.tabActive]}>
                <Text variant="micro" style={{ color: tab === item ? colors.teal800 : 'rgba(255,255,255,0.8)', fontFamily: fonts.semibold }}>
                  {t(`country.${item}`)}
                </Text>
              </View>
            </PressableScale>
          ))}
        </View>
      </LinearGradient>

      <View style={{ padding: spacing.md, gap: spacing.md }}>
        {tab === 'overview' ? (
          <>
            <Card>
              <SectionTitle title={t('country.officialBadge')} />
              <View style={{ marginTop: spacing.xs }}>
                <KeyValue label={t('country.authority')} value={pick(country.official.authorityFa, country.official.authorityEn)} />
                <KeyValue label={t('country.lastVerified')} value={lang === 'fa' ? 'مهر ۱۴۰۵' : 'October 2026'} tone={colors.success} />
                <KeyValue label={t('country.prPath')} value={pick(country.prPathFa, country.prPathEn)} />
                <KeyValue label={t('country.costOfLiving')} value={pick(country.costOfLivingFa, country.costOfLivingEn)} />
                <KeyValue label={t('country.timezone')} value={pick(country.timezoneFa, country.timezoneEn)} />
              </View>
              <Button
                label={t('country.openPortal')}
                icon="open-outline"
                variant="outline"
                size="sm"
                style={{ marginTop: spacing.sm }}
                onPress={() => Linking.openURL(country.official.portal)}
              />
            </Card>

            <Card>
              <SectionTitle title={t('country.visaTypesTitle')} />
              <View style={{ gap: spacing.sm, marginTop: spacing.sm }}>
                {country.visas.map((visa) => {
                  const scored = assessed ? assessed.visas.find((item) => item.visaId === visa.id) : null;
                  return (
                    <PressableScale
                      key={visa.id}
                      onPress={() => {
                        setSelectedVisaId(visa.id);
                        setTab('visas');
                      }}
                    >
                      <View style={[styles.visaRow, { flexDirection: dir.row }]}>
                        <View style={styles.visaIcon}>
                          <Ionicons name="document-text-outline" size={16} color={colors.teal700} />
                        </View>
                        <View style={{ flex: 1 }}>
                          <Text variant="bodyStrong" color={colors.ink} style={{ textAlign: dir.text }}>{pick(visa.nameFa, visa.nameEn)}</Text>
                          <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text }} numberOfLines={1}>
                            {pick(visa.taglineFa, visa.taglineEn)}
                          </Text>
                        </View>
                        {scored ? <Pill label={percent(scored.chance, lang)} tone={scored.eligible ? 'success' : 'warn'} /> : null}
                      </View>
                    </PressableScale>
                  );
                })}
              </View>
            </Card>

            <Card>
              <SectionTitle title={t('country.requirements')} />
              <View style={{ gap: 6, marginTop: spacing.sm }}>
                {selectedVisa.requirementsFa.map((item, index) => (
                  <View key={`${selectedVisa.id}-req-${index}`} style={{ flexDirection: dir.row, gap: 6 }}>
                    <Ionicons name="checkmark-circle-outline" size={14} color={colors.teal600} style={{ marginTop: 3 }} />
                    <Text variant="small" color={colors.ink70} style={{ flex: 1, textAlign: dir.text }}>{item}</Text>
                  </View>
                ))}
              </View>
            </Card>

            <Card style={{ backgroundColor: colors.goldSoft, borderColor: '#E8D9AE' }}>
              <View style={{ flexDirection: dir.row, gap: spacing.sm }}>
                <Ionicons name="information-circle-outline" size={18} color="#7A5F19" />
                <View style={{ flex: 1 }}>
                  <Text variant="h3" color="#6B5416" style={{ textAlign: dir.text }}>{t('country.notes')}</Text>
                  {selectedVisa.notesFa.map((note, index) => (
                    <Text key={`note-${index}`} variant="small" color="#6B5416" style={{ marginTop: 4, textAlign: dir.text }}>
                      {`• ${note}`}
                    </Text>
                  ))}
                </View>
              </View>
            </Card>

            <TrustBadge label={t('country.lastVerified')} value={lang === 'fa' ? 'مهر ۱۴۰۵' : 'Oct 2026'} />
            <Text variant="micro" color={colors.ink35} style={{ textAlign: dir.text }}>{t('results.disclaimer')}</Text>
          </>
        ) : null}

        {tab === 'visas' ? (
          <>
            <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text }}>{t('country.selectVisa')}</Text>
            {country.visas.map((visa) => {
              const scored = assessed ? assessed.visas.find((item) => item.visaId === visa.id) : null;
              const isBest = assessed ? assessed.best.visaId === visa.id : false;
              return (
                <VisaCard
                  key={visa.id}
                  visa={scored || {
                    visaId: visa.id,
                    visaNameFa: visa.nameFa,
                    visaNameEn: visa.nameEn,
                    taglineFa: visa.taglineFa,
                    taglineEn: visa.taglineEn,
                    visaType: visa.type,
                    chance: 0,
                    readiness: 0,
                    achieved: 0,
                    maxPoints: visa.maxPoints,
                    passMark: visa.passMark,
                    eligible: false,
                    blockers: [],
                    criteria: [],
                    processingTimeFa: visa.processingTimeFa,
                    processingTimeEn: visa.processingTimeEn,
                    settlementRequiredUsd: 0,
                    officialUrl: visa.officialUrl,
                  }}
                  best={isBest}
                  expanded={expandedVisa === visa.id}
                  onToggle={() => {
                    setExpandedVisa(expandedVisa === visa.id ? null : visa.id);
                    setSelectedVisaId(visa.id);
                  }}
                />
              );
            })}
            {!assessed ? (
              <Button
                label={t('home.ctaStart')}
                icon="sparkles-outline"
                onPress={() => navigation.navigate('Wizard', { from: 'country' })}
                style={{ marginTop: spacing.sm }}
              />
            ) : null}
          </>
        ) : null}

        {tab === 'costs' ? (
          <>
            <Card>
              <Text variant="h3" color={colors.ink} style={{ textAlign: dir.text }}>{t('country.fees')}</Text>
              <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text, marginBottom: spacing.sm }} numberOfLines={2}>
                {pick(selectedVisa.nameFa, selectedVisa.nameEn)}
              </Text>
              <Stepper label={t('wizard.familySize')} value={familySize} onChange={setFamilySize} min={1} max={9} />
              <Divider style={{ marginVertical: spacing.sm }} />
              <FeeList costs={costs} lang={lang} />
            </Card>

            <Card>
              <KeyValue label={t('country.applicant')} value={money(costs.applicantTotalUsd, lang, 'USD')} />
              <KeyValue label={t('country.employer')} value={money(costs.employerTotalUsd, lang, 'USD')} />
              <KeyValue label={t('country.settlement')} value={money(costs.settlementUsd, lang, 'USD')} />
              <Divider style={{ marginVertical: spacing.xs }} />
              <KeyValue label={t('country.totalForFamily')} value={money(costs.grandTotalUsd, lang, 'USD')} tone={colors.teal800} />
              <View style={{ marginTop: spacing.sm }}>
                <Text variant="micro" color={colors.ink35} style={{ textAlign: dir.text }}>
                  {t('results.disclaimer')}
                </Text>
              </View>
            </Card>

            <Card>
              <Text variant="h3" color={colors.ink} style={{ textAlign: dir.text }}>{t('country.settlement')}</Text>
              <Text variant="small" color={colors.ink70} style={{ marginTop: 4, textAlign: dir.text }}>
                {selectedVisa.settlement
                  ? pick(selectedVisa.settlement.noteFa || '', selectedVisa.settlement.noteEn || '')
                  : pick('این مسیر جدول تمکن مالی اختصاصی ندارد.', 'This route has no dedicated settlement table.')}
              </Text>
              {selectedVisa.settlement ? (
                <View style={{ marginTop: spacing.sm }}>
                  <ProgressBar
                    value={Math.min(100, (costs.settlementUsd ? 60 : 0))}
                    barColors={[colors.sky400, colors.teal500]}
                  />
                  <Text variant="micro" color={colors.ink35} style={{ marginTop: 4, textAlign: dir.text }}>
                    {`${t('country.settlement')}: ${money(costs.settlementUsd, lang, 'USD')}`}
                  </Text>
                </View>
              ) : null}
            </Card>
          </>
        ) : null}

        {tab === 'documents' ? (
          <>
            <Card>
              <View style={{ flexDirection: dir.row, alignItems: 'center', justifyContent: 'space-between' }}>
                <View>
                  <Text variant="h3" color={colors.ink} style={{ textAlign: dir.text }}>{t('country.documents')}</Text>
                  <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text }}>{t('country.checklistHint')}</Text>
                </View>
                <Pill label={scorePair(checked.length, documents.length, lang)} tone="teal" icon="checkmark-done" />
              </View>
              <View style={{ marginTop: spacing.sm }}>
                <ProgressBar value={checked.length} max={documents.length} />
              </View>
              <View style={{ marginTop: spacing.xs }}>
                {documents.map((item) => (
                  <ChecklistItem
                    key={item.id}
                    item={item}
                    checked={checked.includes(item.id)}
                    onToggle={() => toggleDoc(item.id)}
                  />
                ))}
              </View>
            </Card>
            {selectedVisa.notesFa.length ? (
              <Card>
                <Text variant="h3" color={colors.ink} style={{ textAlign: dir.text }}>{t('country.notes')}</Text>
                {selectedVisa.notesFa.map((note, index) => (
                  <Text key={`doc-note-${index}`} variant="small" color={colors.ink50} style={{ marginTop: 4, textAlign: dir.text }}>
                    {`• ${note}`}
                  </Text>
                ))}
              </Card>
            ) : null}
          </>
        ) : null}
      </View>
    </ScrollScreen>
  );
}

const styles = {
  hero: {
    paddingTop: spacing.xxl,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
    borderBottomLeftRadius: radius.xxl,
    borderBottomRightRadius: radius.xxl,
  },
  tab: {
    alignItems: 'center',
    paddingVertical: 8,
    borderRadius: radius.pill,
    backgroundColor: 'rgba(255,255,255,0.12)',
  },
  tabActive: { backgroundColor: colors.white },
  visaRow: {
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: 9,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  visaIcon: {
    width: 32, height: 32, borderRadius: 10, backgroundColor: colors.teal100,
    alignItems: 'center', justifyContent: 'center',
  },
};
