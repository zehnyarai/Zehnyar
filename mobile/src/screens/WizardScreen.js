import React, { useMemo, useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, TextInput, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { colors, fonts, gradients, radius, spacing } from '../theme';
import { localiseNumber, money } from '../core/format';
import { useDirection, useI18n } from '../i18n';
import { useAppState } from '../core/appState';
import { findOccupation, getDataset } from '../core/data';
import {
  Button, Card, Chip, Divider, Field, IconButton, MoneyField, OptionCard, Pill,
  PressableScale, ProgressBar, ScrollScreen, Sheet, Stepper, Text, ToggleRow,
} from '../components/ui';
import { GoalTile } from '../components/cards';

const STEPS = ['goal', 'profile', 'education', 'language', 'work', 'funds', 'adaptability', 'review'];
const CEFR = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];
const SKILL_KEYS = ['listening', 'reading', 'writing', 'speaking'];

export default function WizardScreen({ navigation }) {
  const { t, lang, pick } = useI18n();
  const dir = useDirection();
  const { profile, updateProfile, updateNested, setProfile, compute } = useAppState();
  const [step, setStep] = useState(0);
  const [occupationSheet, setOccupationSheet] = useState(false);
  const [testSheet, setTestSheet] = useState(false);
  const [search, setSearch] = useState('');
  const [computing, setComputing] = useState(false);
  const { educationLevels, languageTests, occupations } = getDataset();

  const stepKey = STEPS[step];
  const progress = ((step + 1) / STEPS.length) * 100;

  const filteredOccupations = useMemo(() => {
    const needle = search.trim().toLowerCase();
    if (!needle) return occupations;
    return occupations.filter((item) => item.titleFa.includes(search.trim())
      || item.titleEn.toLowerCase().includes(needle)
      || item.noc.includes(needle));
  }, [occupations, search]);

  const addLanguage = (testId) => {
    const test = languageTests.find((item) => item.id === testId);
    const entry = { testId, skills: {}, cefr: test && test.kind === 'cefr' ? 'B2' : undefined };
    setProfile((current) => ({ ...current, languages: [...current.languages, entry] }));
    setTestSheet(false);
  };

  const updateLanguage = (index, patch) => {
    setProfile((current) => {
      const languages = current.languages.map((item, i) => (i === index ? { ...item, ...patch } : item));
      return { ...current, languages };
    });
  };

  const updateSkill = (index, skill, raw) => {
    const numeric = raw === '' ? null : Number(raw.replace(/[^0-9.]/g, ''));
    setProfile((current) => {
      const languages = current.languages.map((item, i) => (
        i === index ? { ...item, skills: { ...item.skills, [skill]: Number.isFinite(numeric) ? numeric : null } } : item
      ));
      return { ...current, languages };
    });
  };

  const removeLanguage = (index) => {
    setProfile((current) => ({ ...current, languages: current.languages.filter((_, i) => i !== index) }));
  };

  const goNext = async () => {
    if (computing) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    if (step === STEPS.length - 2) {
      setComputing(true);
      try {
        const computed = await compute(t);
        if (!computed) {
          navigation.navigate('Payments');
          return;
        }
        navigation.replace('Results');
      } finally {
        setComputing(false);
      }
      return;
    }
    setStep((current) => Math.min(STEPS.length - 1, current + 1));
  };

  const goBack = () => {
    if (step === 0) {
      navigation.goBack();
      return;
    }
    setStep((current) => Math.max(0, current - 1));
  };

  return (
    <View style={{ flex: 1, backgroundColor: colors.canvas }}>
      <LinearGradient colors={gradients.hero} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.header}>
        <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.sm }}>
          <IconButton icon={dir.isRtl ? 'close' : 'close'} onPress={() => navigation.goBack()} bg="rgba(255,255,255,0.14)" color={colors.white} size={38} />
          <View style={{ flex: 1 }}>
            <Text variant="micro" style={{ color: 'rgba(255,255,255,0.7)', textAlign: dir.text }}>
              {`${t('wizard.stepLabel')} ${localiseNumber(step + 1, lang)} ${t('common.of')} ${localiseNumber(STEPS.length, lang)}`}
            </Text>
            <Text variant="h2" color={colors.white} style={{ textAlign: dir.text }}>
              {t(`wizard.steps.${stepKey}.title`)}
            </Text>
          </View>
        </View>
        <View style={{ marginTop: spacing.sm }}>
          <ProgressBar value={progress} barColors={[colors.teal300, colors.sky400]} track="rgba(255,255,255,0.18)" />
        </View>
        <Text variant="micro" style={{ color: 'rgba(255,255,255,0.72)', marginTop: 6, textAlign: dir.text }}>
          {t(`wizard.steps.${stepKey}.subtitle`)}
        </Text>
      </LinearGradient>

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={{ padding: spacing.md, paddingBottom: 150 }} keyboardShouldPersistTaps="handled">
          {stepKey === 'goal' ? (
            <View style={{ gap: spacing.sm }}>
              <View style={{ flexDirection: dir.row, gap: spacing.sm }}>
                {['work', 'study'].map((goal) => (
                  <GoalTile key={goal} goalId={goal} active={profile.goal === goal} onPress={() => updateProfile({ goal })} />
                ))}
              </View>
              <View style={{ flexDirection: dir.row, gap: spacing.sm }}>
                {['startup', 'investment'].map((goal) => (
                  <GoalTile key={goal} goalId={goal} active={profile.goal === goal} onPress={() => updateProfile({ goal })} />
                ))}
              </View>
              <GoalTile goalId="selfsponsored" active={profile.goal === 'selfsponsored'} onPress={() => updateProfile({ goal: 'selfsponsored' })} />
            </View>
          ) : null}

          {stepKey === 'profile' ? (
            <View style={{ gap: spacing.md }}>
              <Card>
                <Stepper
                  label={t('wizard.ageLabel')}
                  value={profile.age}
                  onChange={(value) => updateProfile({ age: Math.round(value) })}
                  min={16}
                  max={70}
                  suffix={t('common.years')}
                />
                <Text variant="micro" color={colors.ink35} style={{ marginTop: 4, textAlign: dir.text }}>
                  {t('wizard.ageHint')}
                </Text>
              </Card>

              <Card>
                <Text variant="bodyStrong" color={colors.ink} style={{ textAlign: dir.text, marginBottom: spacing.sm }}>
                  {t('wizard.maritalLabel')}
                </Text>
                <View style={{ flexDirection: dir.row, flexWrap: 'wrap', gap: spacing.xs }}>
                  {['single', 'married', 'divorced', 'widowed'].map((status) => (
                    <Chip
                      key={status}
                      label={t(`wizard.marital.${status}`)}
                      active={profile.maritalStatus === status}
                      onPress={() => updateProfile({ maritalStatus: status })}
                    />
                  ))}
                </View>
              </Card>

              {profile.maritalStatus === 'married' ? (
                <Card>
                  <Text variant="h3" color={colors.ink} style={{ textAlign: dir.text }}>{t('wizard.spouseTitle')}</Text>
                  <Text variant="micro" color={colors.ink35} style={{ textAlign: dir.text, marginBottom: spacing.sm }}>
                    {t('wizard.spouseHint')}
                  </Text>
                  <Text variant="bodyStrong" color={colors.ink} style={{ textAlign: dir.text, marginBottom: 6 }}>
                    {t('wizard.spouseEducation')}
                  </Text>
                  <View style={{ gap: spacing.xs }}>
                    {educationLevels.map((level) => (
                      <PressableScale
                        key={level.id}
                        onPress={() => updateNested('spouse', { educationId: level.id })}
                      >
                        <View style={[styles.levelRow, profile.spouse.educationId === level.id && styles.levelRowActive, { flexDirection: dir.row }]}>
                          <Ionicons
                            name={profile.spouse.educationId === level.id ? 'radio-button-on' : 'radio-button-off'}
                            size={16}
                            color={profile.spouse.educationId === level.id ? colors.teal700 : colors.ink35}
                          />
                          <Text variant="small" color={colors.ink} style={{ flex: 1, textAlign: dir.text }}>
                            {pick(level.fa, level.en)}
                          </Text>
                        </View>
                      </PressableScale>
                    ))}
                  </View>
                  <Divider style={{ marginVertical: spacing.sm }} />
                  <Stepper
                    label={t('wizard.spouseLanguage')}
                    value={profile.spouse.languageClb || 0}
                    onChange={(value) => updateNested('spouse', { languageClb: value })}
                    min={0}
                    max={10}
                    suffix={lang === 'fa' ? 'سطح' : 'level'}
                  />
                  <Divider style={{ marginVertical: spacing.sm }} />
                  <Stepper
                    label={t('wizard.spouseWork')}
                    value={profile.spouse.workYears || 0}
                    onChange={(value) => updateNested('spouse', { workYears: value })}
                    min={0}
                    max={40}
                    suffix={t('common.years')}
                  />
                </Card>
              ) : null}
            </View>
          ) : null}

          {stepKey === 'education' ? (
            <View style={{ gap: spacing.sm }}>
              {educationLevels.slice().reverse().map((level) => (
                <PressableScale key={level.id} onPress={() => updateProfile({ educationId: level.id })}>
                  <View style={[styles.levelRow, profile.educationId === level.id && styles.levelRowActive, { flexDirection: dir.row }]}>
                    <View style={styles.levelIcon}>
                      <Ionicons name="school-outline" size={16} color={profile.educationId === level.id ? colors.white : colors.teal700} />
                    </View>
                    <Text variant="bodyStrong" color={colors.ink} style={{ flex: 1, textAlign: dir.text }}>
                      {pick(level.fa, level.en)}
                    </Text>
                    {profile.educationId === level.id ? <Ionicons name="checkmark-circle" size={18} color={colors.teal700} /> : null}
                  </View>
                </PressableScale>
              ))}
              <Card style={{ marginTop: spacing.xs }}>
                <ToggleRow
                  icon="flask-outline"
                  label={t('wizard.stemLabel')}
                  hint={t('wizard.stemHint')}
                  value={profile.educationStem}
                  onValueChange={(value) => updateProfile({ educationStem: value })}
                />
                <Divider />
                <ToggleRow
                  icon="ribbon-outline"
                  label={t('wizard.eca')}
                  value={profile.adaptability.eca}
                  onValueChange={(value) => updateNested('adaptability', { eca: value })}
                />
                <Divider />
                <ToggleRow
                  icon="school"
                  label={t('wizard.recentGraduate')}
                  value={profile.recentGraduate}
                  onValueChange={(value) => updateProfile({ recentGraduate: value })}
                />
                <Divider />
                <ToggleRow
                  icon="document-text-outline"
                  label={t('wizard.studyOffer')}
                  value={profile.studyOffer}
                  onValueChange={(value) => updateProfile({ studyOffer: value })}
                />
              </Card>
            </View>
          ) : null}

          {stepKey === 'language' ? (
            <View style={{ gap: spacing.sm }}>
              {profile.languages.length === 0 ? (
                <Card style={{ alignItems: 'center', paddingVertical: spacing.xl }}>
                  <View style={styles.emptyIcon}>
                    <Ionicons name="language-outline" size={24} color={colors.teal600} />
                  </View>
                  <Text variant="small" color={colors.ink50} style={{ marginTop: spacing.sm, textAlign: 'center' }}>
                    {t('wizard.noLanguage')}
                  </Text>
                </Card>
              ) : null}

              {profile.languages.map((entry, index) => {
                const test = languageTests.find((item) => item.id === entry.testId);
                const isCefr = test && test.kind === 'cefr';
                const isOverall = test && test.overallOnly;
                const skillKeys = isOverall ? ['overall'] : SKILL_KEYS;
                return (
                  <Card key={`${entry.testId}-${index}`}>
                    <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.xs }}>
                      <View style={{ flex: 1 }}>
                        <Text variant="h3" color={colors.ink} style={{ textAlign: dir.text }}>
                          {t(`tests.${entry.testId}`)}
                        </Text>
                        <Text variant="micro" color={colors.ink35} style={{ textAlign: dir.text }}>
                          {test && test.scale ? pick(test.scale.labelFa, test.scale.labelEn) : t('wizard.cefrLevel')}
                        </Text>
                      </View>
                      <IconButton icon="trash-outline" size={34} onPress={() => removeLanguage(index)} bg={colors.dangerSoft} color={colors.danger} />
                    </View>

                    {isCefr ? (
                      <View style={{ flexDirection: dir.row, flexWrap: 'wrap', gap: spacing.xs, marginTop: spacing.sm }}>
                        {CEFR.map((level) => (
                          <Chip
                            key={level}
                            label={level}
                            active={entry.cefr === level}
                            onPress={() => updateLanguage(index, { cefr: level })}
                          />
                        ))}
                      </View>
                    ) : (
                      <View style={{ marginTop: spacing.sm, gap: spacing.sm }}>
                        {skillKeys.map((skill) => (
                          <Field
                            key={skill}
                            label={t(`wizard.skills.${skill}`)}
                            value={entry.skills && entry.skills[skill] !== null && entry.skills[skill] !== undefined ? String(entry.skills[skill]) : ''}
                            onChangeText={(raw) => updateSkill(index, skill, raw)}
                            keyboardType="decimal-pad"
                            placeholder="0"
                          />
                        ))}
                      </View>
                    )}
                  </Card>
                );
              })}

              <Button label={t('wizard.addLanguage')} icon="add-circle-outline" variant="outline" onPress={() => setTestSheet(true)} />
              <Text variant="micro" color={colors.ink35} style={{ textAlign: dir.text }}>{t('wizard.languageHint')}</Text>
            </View>
          ) : null}

          {stepKey === 'work' ? (
            <View style={{ gap: spacing.md }}>
              <Card>
                <Text variant="bodyStrong" color={colors.ink} style={{ textAlign: dir.text }}>{t('wizard.occupation')}</Text>
                <Pressable onPress={() => setOccupationSheet(true)}>
                  <View style={[styles.occupationBox, { flexDirection: dir.row }]}>
                    <View style={{ flex: 1 }}>
                      {profile.work.occupationCode ? (
                        <>
                          <Text variant="h3" color={colors.ink} style={{ textAlign: dir.text }}>
                            {pick(findOccupation(profile.work.occupationCode)?.titleFa, findOccupation(profile.work.occupationCode)?.titleEn)}
                          </Text>
                          <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text }}>
                            {`${t('wizard.noc')} ${findOccupation(profile.work.occupationCode)?.noc} • ${t('wizard.teer')} ${findOccupation(profile.work.occupationCode)?.teer}`}
                          </Text>
                        </>
                      ) : (
                        <Text variant="small" color={colors.ink35} style={{ textAlign: dir.text }}>{t('wizard.occupationNone')}</Text>
                      )}
                    </View>
                    <Ionicons name="search" size={18} color={colors.teal700} />
                  </View>
                </Pressable>
                <Text variant="micro" color={colors.ink35} style={{ marginTop: 6, textAlign: dir.text }}>
                  {t('wizard.occupationHint')}
                </Text>
              </Card>

              <Card>
                <Stepper label={t('wizard.yearsTotal')} value={profile.work.totalYears} onChange={(value) => updateNested('work', { totalYears: value })} min={0} max={45} suffix={t('common.years')} />
                <Divider style={{ marginVertical: spacing.sm }} />
                <Stepper label={t('wizard.yearsOverseas')} value={profile.work.overseasYears} onChange={(value) => updateNested('work', { overseasYears: value })} min={0} max={45} suffix={t('common.years')} />
                <Divider style={{ marginVertical: spacing.sm }} />
                <Stepper label={t('wizard.yearsInCountry')} value={profile.work.inCountryYears} onChange={(value) => updateNested('work', { inCountryYears: value })} min={0} max={45} suffix={t('common.years')} />
              </Card>

              <Card>
                <ToggleRow icon="briefcase-outline" label={t('wizard.jobOffer')} hint={t('wizard.jobOfferHint')} value={profile.work.jobOffer} onValueChange={(value) => updateNested('work', { jobOffer: value })} />
                <Divider />
                <ToggleRow icon="shield-outline" label={t('wizard.licensing')} value={profile.work.licensing} onValueChange={(value) => updateNested('work', { licensing: value })} />
                <Divider />
                <ToggleRow icon="sparkles-outline" label={t('wizard.achievement')} value={profile.achievement} onValueChange={(value) => updateProfile({ achievement: value })} />
                <Divider />
                <ToggleRow icon="rocket-outline" label={t('wizard.startupBacking')} value={profile.startupBacking} onValueChange={(value) => updateProfile({ startupBacking: value })} />
              </Card>

              <Card>
                <MoneyField
                  label={t('wizard.salaryLabel')}
                  hint={t('wizard.salaryHint')}
                  value={profile.work.salaryAnnualLocal !== null && profile.work.salaryAnnualLocal !== undefined ? String(profile.work.salaryAnnualLocal) : ''}
                  onChangeText={(raw) => updateNested('work', { salaryAnnualLocal: raw === '' ? null : Number(raw.replace(/[^0-9]/g, '')) })}
                  currencyLabel={profile.work.salaryCurrency}
                  placeholder="0"
                />
                <View style={{ flexDirection: dir.row, flexWrap: 'wrap', gap: spacing.xs, marginTop: spacing.sm }}>
                  {['USD', 'EUR', 'CAD', 'AUD', 'GBP', 'AED'].map((currency) => (
                    <Chip key={currency} label={currency} active={profile.work.salaryCurrency === currency} onPress={() => updateNested('work', { salaryCurrency: currency })} />
                  ))}
                </View>
              </Card>
            </View>
          ) : null}

          {stepKey === 'funds' ? (
            <View style={{ gap: spacing.md }}>
              <Card>
                <MoneyField
                  label={t('wizard.fundsLabel')}
                  hint={t('wizard.fundsHint')}
                  value={profile.funds.availableUsd ? String(profile.funds.availableUsd) : ''}
                  onChangeText={(raw) => updateNested('funds', { availableUsd: raw === '' ? 0 : Number(raw.replace(/[^0-9]/g, '')) })}
                  currencyLabel="USD"
                  placeholder="0"
                />
                <View style={{ flexDirection: dir.row, flexWrap: 'wrap', gap: spacing.xs, marginTop: spacing.sm }}>
                  {[10000, 25000, 50000, 100000].map((amount) => (
                    <Chip key={amount} label={`$${amount / 1000}k`} onPress={() => updateNested('funds', { availableUsd: amount })} />
                  ))}
                </View>
                <Divider style={{ marginVertical: spacing.md }} />
                <MoneyField
                  label={t('wizard.cashLabel')}
                  value={profile.funds.cashUsd ? String(profile.funds.cashUsd) : ''}
                  onChangeText={(raw) => updateNested('funds', { cashUsd: raw === '' ? 0 : Number(raw.replace(/[^0-9]/g, '')) })}
                  currencyLabel="USD"
                  placeholder="0"
                />
                <Divider style={{ marginVertical: spacing.md }} />
                <MoneyField
                  label={t('wizard.assetsLabel')}
                  value={profile.funds.assetsUsd ? String(profile.funds.assetsUsd) : ''}
                  onChangeText={(raw) => updateNested('funds', { assetsUsd: raw === '' ? 0 : Number(raw.replace(/[^0-9]/g, '')) })}
                  currencyLabel="USD"
                  placeholder="0"
                />
              </Card>

              <Card>
                <MoneyField
                  label={t('wizard.investmentLabel')}
                  value={profile.investmentUsd ? String(profile.investmentUsd) : ''}
                  onChangeText={(raw) => updateProfile({ investmentUsd: raw === '' ? 0 : Number(raw.replace(/[^0-9]/g, '')) })}
                  currencyLabel="USD"
                  placeholder="0"
                />
                <Divider style={{ marginVertical: spacing.md }} />
                <MoneyField
                  label={t('wizard.remoteIncomeLabel')}
                  value={profile.remoteIncomeUsd ? String(profile.remoteIncomeUsd) : ''}
                  onChangeText={(raw) => updateProfile({ remoteIncomeUsd: raw === '' ? 0 : Number(raw.replace(/[^0-9]/g, '')) })}
                  currencyLabel="USD"
                  placeholder="0"
                />
              </Card>

              <Card>
                <Stepper
                  label={t('wizard.familySize')}
                  value={profile.familySize}
                  onChange={(value) => updateProfile({ familySize: value })}
                  min={1}
                  max={9}
                  suffix={lang === 'fa' ? 'نفر' : 'people'}
                />
              </Card>
            </View>
          ) : null}

          {stepKey === 'adaptability' ? (
            <View style={{ gap: spacing.md }}>
              <Card>
                <ToggleRow icon="people-outline" label={t('wizard.relative')} value={profile.adaptability.relativeInCountry} onValueChange={(value) => updateNested('adaptability', { relativeInCountry: value })} />
                <Divider />
                <ToggleRow icon="book-outline" label={t('wizard.priorStudy')} value={profile.adaptability.priorStudyInCountry} onValueChange={(value) => updateNested('adaptability', { priorStudyInCountry: value })} />
                <Divider />
                <ToggleRow icon="hammer-outline" label={t('wizard.priorWork')} value={profile.adaptability.priorWorkInCountry} onValueChange={(value) => updateNested('adaptability', { priorWorkInCountry: value })} />
              </Card>
              <Card style={{ backgroundColor: colors.sky50 }}>
                <Text variant="small" color={colors.ink70} style={{ textAlign: dir.text }}>
                  {t('wizard.summaryHint')}
                </Text>
              </Card>
            </View>
          ) : null}

          {stepKey === 'review' ? (
            <View style={{ gap: spacing.sm }}>
              <ReviewRow label={t('wizard.summaryGoal')} value={t(`goals.${profile.goal}.label`)} icon="flag-outline" />
              <ReviewRow label={t('wizard.summaryAge')} value={`${localiseNumber(profile.age, lang)} ${t('common.years')}`} icon="calendar-outline" />
              <ReviewRow label={t('wizard.summaryEducation')} value={t(`types.${profile.educationId}`)} icon="school-outline" />
              <ReviewRow
                label={t('wizard.summaryLanguage')}
                value={profile.languages.length ? profile.languages.map((item) => t(`tests.${item.testId}`)).join('، ') : t('common.notSet')}
                icon="language-outline"
              />
              <ReviewRow
                label={t('wizard.summaryWork')}
                value={`${localiseNumber(profile.work.totalYears, lang)} ${t('common.years')}${profile.work.occupationCode ? ` • ${pick(findOccupation(profile.work.occupationCode)?.titleFa, findOccupation(profile.work.occupationCode)?.titleEn)}` : ''}`}
                icon="briefcase-outline"
              />
              <ReviewRow label={t('wizard.summaryFunds')} value={money(profile.funds.availableUsd, lang, 'USD')} icon="wallet-outline" />
              <ReviewRow label={t('wizard.summaryFamily')} value={localiseNumber(profile.familySize, lang)} icon="people-outline" />
              <Card style={{ backgroundColor: colors.teal100, borderColor: colors.teal300, marginTop: spacing.xs }}>
                <View style={{ flexDirection: dir.row, gap: spacing.sm, alignItems: 'center' }}>
                  <Ionicons name="shield-checkmark" size={18} color={colors.teal700} />
                  <Text variant="small" color={colors.teal800} style={{ flex: 1, textAlign: dir.text }}>
                    {t('wizard.summaryHint')}
                  </Text>
                </View>
              </Card>
            </View>
          ) : null}
        </ScrollView>

        <View style={styles.footer}>
          <View style={{ flexDirection: dir.row, gap: spacing.sm }}>
            <Button label={t('common.back')} variant="outline" onPress={goBack} style={{ flex: 1 }} />
            <Button
              label={step === STEPS.length - 2 ? t('wizard.calculate') : t('common.next')}
              icon={step === STEPS.length - 2 ? 'sparkles' : dir.isRtl ? 'arrow-back' : 'arrow-forward'}
              onPress={goNext}
              loading={computing}
              style={{ flex: 1.6 }}
            />
          </View>
        </View>
      </KeyboardAvoidingView>

      <Sheet visible={testSheet} onClose={() => setTestSheet(false)} title={t('wizard.testType')} height="62%">
        <ScrollView showsVerticalScrollIndicator={false}>
          {languageTests.map((test) => (
            <PressableScale key={test.id} onPress={() => addLanguage(test.id)}>
              <View style={[styles.pickerRow, { flexDirection: dir.row }]}>
                <View style={styles.pickerIcon}>
                  <Ionicons name="language" size={16} color={colors.teal700} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text variant="h3" color={colors.ink} style={{ textAlign: dir.text }}>{t(`tests.${test.id}`)}</Text>
                  <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text }}>
                    {test.kind === 'cefr' ? t('wizard.cefrLevel') : pick(test.scale.labelFa, test.scale.labelEn)}
                  </Text>
                </View>
                <Pill label={test.group.toUpperCase()} tone="sky" />
              </View>
            </PressableScale>
          ))}
        </ScrollView>
      </Sheet>

      <Sheet visible={occupationSheet} onClose={() => setOccupationSheet(false)} title={t('wizard.occupationPicker')} height="82%">
        <View style={[styles.searchBox, { flexDirection: dir.row }]}>
          <Ionicons name="search" size={16} color={colors.ink35} />
          <TextInput
            value={search}
            onChangeText={setSearch}
            placeholder={t('wizard.occupationSearch')}
            placeholderTextColor={colors.ink35}
            style={[styles.searchInput, { textAlign: dir.text, writingDirection: dir.writing }]}
          />
        </View>
        <ScrollView showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
          {filteredOccupations.map((item) => (
            <PressableScale
              key={item.noc}
              onPress={() => {
                updateNested('work', { occupationCode: item.noc });
                setOccupationSheet(false);
                setSearch('');
              }}
            >
              <View style={[styles.pickerRow, { flexDirection: dir.row }]}>
                <View style={{ flex: 1 }}>
                  <Text variant="bodyStrong" color={colors.ink} style={{ textAlign: dir.text }}>{pick(item.titleFa, item.titleEn)}</Text>
                  <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text }}>
                    {`${t('wizard.noc')} ${item.noc} • ${t('wizard.teer')} ${item.teer}`}
                  </Text>
                </View>
                {item.inDemand.length ? (
                  <Pill label={`${item.inDemand.length}`} tone="teal" icon="trending-up" />
                ) : null}
              </View>
            </PressableScale>
          ))}
        </ScrollView>
      </Sheet>
    </View>
  );
}

function ReviewRow({ label, value, icon }) {
  const dir = useDirection();
  return (
    <Card level={0} padded={false}>
      <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.sm, padding: spacing.md }}>
        <View style={styles.reviewIcon}>
          <Ionicons name={icon} size={15} color={colors.teal700} />
        </View>
        <Text variant="small" color={colors.ink50} style={{ textAlign: dir.text }}>{label}</Text>
        <Text variant="bodyStrong" color={colors.ink} style={{ flex: 1, textAlign: dir.textOpposite }} numberOfLines={2}>
          {value}
        </Text>
      </View>
    </Card>
  );
}

const styles = {
  header: {
    paddingTop: spacing.xxl,
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.md,
    borderBottomLeftRadius: radius.xl,
    borderBottomRightRadius: radius.xl,
  },
  footer: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    padding: spacing.md,
    paddingBottom: spacing.xxl,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  levelRow: {
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: 11,
    paddingHorizontal: spacing.sm,
    borderRadius: radius.md,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  levelRowActive: { borderColor: colors.teal600, backgroundColor: colors.teal100 },
  levelIcon: {
    width: 30, height: 30, borderRadius: 9, backgroundColor: colors.canvasAlt,
    alignItems: 'center', justifyContent: 'center',
  },
  emptyIcon: {
    width: 52, height: 52, borderRadius: 18, backgroundColor: colors.teal100,
    alignItems: 'center', justifyContent: 'center',
  },
  occupationBox: {
    alignItems: 'center',
    gap: spacing.sm,
    marginTop: spacing.xs,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1.5,
    borderStyle: 'dashed',
    borderColor: colors.teal300,
    backgroundColor: colors.sky50,
  },
  pickerRow: {
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  pickerIcon: {
    width: 32, height: 32, borderRadius: 10, backgroundColor: colors.teal100,
    alignItems: 'center', justifyContent: 'center',
  },
  searchBox: {
    alignItems: 'center',
    gap: spacing.xs,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1.5,
    borderColor: colors.border,
    paddingHorizontal: spacing.sm,
    height: 46,
    marginVertical: spacing.sm,
  },
  searchInput: { flex: 1, fontFamily: fonts.medium, fontSize: 14, color: colors.ink, paddingVertical: 0 },
  reviewIcon: {
    width: 30, height: 30, borderRadius: 9, backgroundColor: colors.teal100,
    alignItems: 'center', justifyContent: 'center',
  },
};
