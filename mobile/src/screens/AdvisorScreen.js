import React from 'react';
import { View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, fonts, gradients, radius, spacing } from '../theme';
import { useDirection, useI18n } from '../i18n';
import { useAppState } from '../core/appState';
import { Button, Card, EmptyState, Pill, PressableScale, ScrollScreen, SectionTitle, Text } from '../components/ui';
import { num, percent } from '../core/format';

const EFFORT_TONE = { easy: 'success', medium: 'warn', hard: 'danger', locked: 'neutral' };

export default function AdvisorScreen({ navigation }) {
  const { t, lang, pick } = useI18n();
  const dir = useDirection();
  const { result, hasAssessment } = useAppState();

  if (!hasAssessment || !result) {
    return (
      <ScrollScreen>
        <View style={{ padding: spacing.xl, paddingTop: spacing.xxxl }}>
          <EmptyState
            icon="chatbubbles-outline"
            title={t('advisor.title')}
            body={t('advisor.noAssessment')}
            actionLabel={t('advisor.startNow')}
            onAction={() => navigation.navigate('Wizard')}
          />
        </View>
      </ScrollScreen>
    );
  }

  const top = result.countries[0];
  const actions = top.roadmap;
  const weeks = [0, 1, 2, 3].map((index) => actions.slice(index, index + 1)).filter((item) => item.length);

  return (
    <ScrollScreen>
      <LinearGradient colors={gradients.hero} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
        <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.sm }}>
          <View style={styles.icon}>
            <Ionicons name="sparkles" size={18} color={colors.teal800} />
          </View>
          <View style={{ flex: 1 }}>
            <Text variant="h1" color={colors.white} style={{ textAlign: dir.text }}>{t('advisor.title')}</Text>
            <Text variant="micro" style={{ color: 'rgba(255,255,255,0.75)', textAlign: dir.text }}>{t('advisor.subtitle')}</Text>
          </View>
        </View>
        <View style={{ marginTop: spacing.md, flexDirection: dir.row, gap: spacing.sm }}>
          <View style={styles.metric}>
            <Text variant="h2" color={colors.white}>{percent(top.best.chance, lang)}</Text>
            <Text variant="micro" style={{ color: 'rgba(255,255,255,0.7)' }}>{t('results.chanceLabel')}</Text>
          </View>
          <View style={styles.metric}>
            <Text variant="h2" color={colors.white}>{percent(top.best.readiness, lang)}</Text>
            <Text variant="micro" style={{ color: 'rgba(255,255,255,0.7)' }}>{t('results.readinessLabel')}</Text>
          </View>
          <View style={styles.metric}>
            <Text variant="h2" color={colors.white}>{num(result.summary.eligibleCountries, lang)}</Text>
            <Text variant="micro" style={{ color: 'rgba(255,255,255,0.7)' }}>{t('results.filterEligible')}</Text>
          </View>
        </View>
      </LinearGradient>

      <View style={{ padding: spacing.md, gap: spacing.md }}>
        <Card>
          <SectionTitle title={t('advisor.narrativeTitle')} />
          <Text variant="small" color={colors.ink70} style={{ marginTop: spacing.xs, textAlign: dir.text }}>
            {t('advisor.narrativeBody')}
          </Text>
          <View style={{ marginTop: spacing.sm, flexDirection: dir.row, gap: 6, flexWrap: 'wrap' }}>
            <Pill label={`${pick(top.nameFa, top.nameEn)} • ${percent(top.best.chance, lang)}`} tone="teal" icon="flag" />
            <Pill label={pick(top.best.bandFa, top.best.bandEn)} tone="sky" />
          </View>
        </Card>

        <View>
          <SectionTitle title={t('advisor.topActions')} subtitle={t('results.roadmapSubtitle')} />
          <View style={{ gap: spacing.xs, marginTop: spacing.sm }}>
            {actions.map((item, index) => (
              <Card key={`${item.id}-${index}`} level={0} padded={false}>
                <View style={{ flexDirection: dir.row, gap: spacing.sm, padding: spacing.md }}>
                  <View style={styles.actionIcon}>
                    <Ionicons
                      name={item.priority === 1 ? 'alert-circle-outline' : 'trending-up-outline'}
                      size={16}
                      color={item.priority === 1 ? colors.danger : colors.teal700}
                    />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text variant="bodyStrong" color={colors.ink} style={{ textAlign: dir.text }}>{pick(item.labelFa, item.labelEn)}</Text>
                    <Text variant="micro" color={colors.ink50} style={{ marginTop: 2, textAlign: dir.text }}>
                      {pick(item.actionFa, item.actionEn)}
                    </Text>
                    <View style={{ flexDirection: dir.row, gap: 6, marginTop: 6, flexWrap: 'wrap' }}>
                      <Pill label={`${t('advisor.effortLabel')}: ${t(`advisor.effort.${item.effort}`)}`} tone={EFFORT_TONE[item.effort] || 'neutral'} />
                      {item.gain > 0 ? <Pill label={`${t('advisor.gainLabel')} +${num(item.gain, lang)}`} tone="success" /> : null}
                    </View>
                  </View>
                </View>
              </Card>
            ))}
          </View>
        </View>

        <View>
          <SectionTitle title={t('advisor.weekPlan')} />
          <View style={{ gap: spacing.xs, marginTop: spacing.sm }}>
            {weeks.map((chunk, index) => {
              const item = chunk[0];
              return (
                <Card key={`week-${index}`} level={0}>
                  <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.sm }}>
                    <View style={styles.weekBadge}>
                      <Text variant="micro" style={{ color: colors.teal700, fontFamily: fonts.bold }}>{num(index + 1, lang)}</Text>
                    </View>
                    <Text variant="bodyStrong" color={colors.ink} style={{ flex: 1, textAlign: dir.text }}>
                      {t(`advisor.week${index + 1}`)}
                    </Text>
                  </View>
                  <Text variant="small" color={colors.ink70} style={{ marginTop: 4, textAlign: dir.text }}>
                    {pick(item.actionFa, item.actionEn)}
                  </Text>
                </Card>
              );
            })}
          </View>
        </View>

        <View>
          <SectionTitle title={t('advisor.topCountries')} subtitle={t('results.rankingSubtitle')} />
          <View style={{ gap: spacing.xs, marginTop: spacing.sm }}>
            {result.recommendations.map((item) => (
              <PressableScale key={item.code} onPress={() => navigation.navigate('CountryDetail', { code: item.code })}>
                <Card level={0} padded={false}>
                  <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.sm, padding: spacing.md }}>
                    <Text style={{ fontSize: 22 }}>{item.flag}</Text>
                    <View style={{ flex: 1 }}>
                      <Text variant="bodyStrong" color={colors.ink} style={{ textAlign: dir.text }}>{pick(item.nameFa, item.nameEn)}</Text>
                      <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text }} numberOfLines={2}>
                        {pick(item.reasonFa, item.reasonEn)}
                      </Text>
                    </View>
                    <Text variant="h3" color={colors.teal700}>{percent(item.chance, lang)}</Text>
                  </View>
                </Card>
              </PressableScale>
            ))}
          </View>
        </View>

        <Card style={{ backgroundColor: colors.sky50, borderColor: colors.sky300 }}>
          <View style={{ flexDirection: dir.row, gap: spacing.sm }}>
            <Ionicons name="shield-checkmark-outline" size={18} color={colors.sky700} />
            <View style={{ flex: 1 }}>
              <Text variant="h3" color={colors.sky700} style={{ textAlign: dir.text }}>{t('advisor.trustTitle')}</Text>
              <Text variant="small" color={colors.ink70} style={{ marginTop: 2, textAlign: dir.text }}>{t('advisor.trustBody')}</Text>
            </View>
          </View>
        </Card>

        <Button label={t('results.assessAgain')} icon="create-outline" variant="outline" onPress={() => navigation.navigate('Wizard', { from: 'advisor' })} />
      </View>
    </ScrollScreen>
  );
}

const styles = {
  hero: {
    paddingTop: spacing.xxl,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.lg,
    borderBottomLeftRadius: radius.xxl,
    borderBottomRightRadius: radius.xxl,
  },
  icon: {
    width: 40, height: 40, borderRadius: 13, backgroundColor: colors.goldSoft,
    alignItems: 'center', justifyContent: 'center',
  },
  metric: {
    flex: 1, alignItems: 'center', paddingVertical: spacing.sm,
    backgroundColor: 'rgba(255,255,255,0.12)', borderRadius: radius.md,
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.16)',
  },
  actionIcon: {
    width: 32, height: 32, borderRadius: 10, backgroundColor: colors.canvasAlt,
    alignItems: 'center', justifyContent: 'center',
  },
  weekBadge: {
    width: 26, height: 26, borderRadius: 8, backgroundColor: colors.teal100,
    alignItems: 'center', justifyContent: 'center',
  },
};
