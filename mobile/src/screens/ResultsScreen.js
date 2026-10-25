import React, { useMemo, useState } from 'react';
import { View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, fonts, gradients, radius, spacing } from '../theme';
import { useDirection, useI18n } from '../i18n';
import { useAppState } from '../core/appState';
import { Button, Card, Chip, EmptyState, Pill, PressableScale, ScrollScreen, SectionTitle, Text } from '../components/ui';
import { ChanceDial, RadarChart } from '../components/charts';
import { CountryCard } from '../components/cards';
import { percent } from '../core/format';

const FILTERS = ['all', 'eligible', 'goal'];

export default function ResultsScreen({ navigation }) {
  const { t, lang, pick } = useI18n();
  const dir = useDirection();
  const { result, hasAssessment } = useAppState();
  const [filter, setFilter] = useState('all');

  const ranked = useMemo(() => {
    if (!result) return [];
    if (filter === 'eligible') return result.countries.filter((country) => country.best.eligible);
    if (filter === 'goal') return result.countries.filter((country) => country.goalMatch);
    return result.countries;
  }, [result, filter]);

  if (!hasAssessment || !result) {
    return (
      <ScrollScreen>
        <View style={{ padding: spacing.xl, paddingTop: spacing.xxxl }}>
          <EmptyState
            icon="analytics-outline"
            title={t('results.emptyTitle')}
            body={t('results.emptyBody')}
            actionLabel={t('home.ctaStart')}
            onAction={() => navigation.navigate('Wizard')}
          />
        </View>
      </ScrollScreen>
    );
  }

  const best = result.countries[0];

  return (
    <ScrollScreen>
      <LinearGradient colors={gradients.hero} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
        <Text variant="micro" style={{ color: 'rgba(255,255,255,0.72)', textAlign: dir.text }}>
          {t('results.title')}
        </Text>
        <Text variant="h1" color={colors.white} style={{ textAlign: dir.text }}>{t('results.bestTitle')}</Text>

        <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.md, marginTop: spacing.md }}>
          <ChanceDial value={best.best.chance} size={142} strokeWidth={11} sublabel={t('results.chanceLabel')} />
          <View style={{ flex: 1, gap: 6 }}>
            <View style={{ flexDirection: dir.row, alignItems: 'center', gap: 6 }}>
              <Text style={{ fontSize: 24 }}>{best.flag}</Text>
              <Text variant="h2" color={colors.white} style={{ textAlign: dir.text }}>{pick(best.nameFa, best.nameEn)}</Text>
            </View>
            <Text variant="small" style={{ color: 'rgba(255,255,255,0.85)', textAlign: dir.text }} numberOfLines={2}>
              {pick(best.best.visaNameFa, best.best.visaNameEn)}
            </Text>
            <View style={{ flexDirection: dir.row, gap: 6, flexWrap: 'wrap' }}>
              <Pill label={pick(best.best.bandFa, best.best.bandEn)} tone="gold" />
              {best.best.eligible
                ? <Pill label={t('results.eligible')} tone="success" icon="checkmark-circle" />
                : <Pill label={t('results.needsFix')} tone="warn" icon="alert-circle" />}
            </View>
            <Text variant="micro" style={{ color: 'rgba(255,255,255,0.65)', textAlign: dir.text }}>
              {`${t('results.readinessLabel')}: ${percent(best.best.readiness, lang)}`}
            </Text>
          </View>
        </View>

        <View style={{ marginTop: spacing.lg, flexDirection: dir.row, gap: spacing.sm }}>
          <Button
            label={t('country.visas')}
            variant="light"
            icon="compass-outline"
            onPress={() => navigation.navigate('CountryDetail', { code: best.code })}
            style={{ flex: 1 }}
          />
          <Button
            label={t('results.assessAgain')}
            variant="ghost"
            icon="create-outline"
            onPress={() => navigation.navigate('Wizard', { from: 'results' })}
            style={{ flex: 1 }}
          />
        </View>
        <Text variant="micro" style={{ color: 'rgba(255,255,255,0.6)', marginTop: spacing.sm, textAlign: dir.text }}>
          {t('results.disclaimer')}
        </Text>
      </LinearGradient>

      <View style={{ padding: spacing.md }}>
        <Card>
          <SectionTitle title={t('results.radarTitle')} subtitle={t('results.radarSubtitle')} />
          <View style={{ marginTop: spacing.sm }}>
            <RadarChart radar={best.radar} />
          </View>
          <View style={{ flexDirection: dir.row, gap: spacing.xs, marginTop: spacing.sm, flexWrap: 'wrap' }}>
            {Object.keys(best.radar).map((key) => (
              <Pill key={key} label={`${t(`categories.${key}`)} ${percent(best.radar[key].percent, lang)}`} tone={best.radar[key].percent >= 70 ? 'success' : best.radar[key].percent >= 40 ? 'teal' : 'warn'} />
            ))}
          </View>
        </Card>
      </View>

      <View style={{ paddingHorizontal: spacing.md }}>
        <SectionTitle title={t('results.roadmapTitle')} subtitle={t('results.roadmapSubtitle')} />
        <View style={{ gap: spacing.xs, marginTop: spacing.sm }}>
          {best.roadmap.slice(0, 5).map((item, index) => (
            <Card key={`${item.id}-${index}`} level={0} padded={false}>
              <View style={{ flexDirection: dir.row, alignItems: 'flex-start', gap: spacing.sm, padding: spacing.md }}>
                <View style={styles.rankBadge}>
                  <Text variant="micro" style={{ color: colors.teal700, fontFamily: fonts.bold }}>{percent(index + 1, lang).replace('٪', '')}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text variant="bodyStrong" color={colors.ink} style={{ textAlign: dir.text }}>{pick(item.labelFa, item.labelEn)}</Text>
                  <Text variant="micro" color={colors.ink50} style={{ marginTop: 2, textAlign: dir.text }}>
                    {pick(item.actionFa, item.actionEn)}
                  </Text>
                </View>
                {item.gain > 0 ? (
                  <Pill label={`+${percent(item.gain, lang).replace('٪', '')}`} tone="success" icon="trending-up" />
                ) : (
                  <Pill label={t('results.blockerTitle')} tone="danger" icon="alert" />
                )}
              </View>
            </Card>
          ))}
        </View>
      </View>

      <View style={{ padding: spacing.md }}>
        <SectionTitle title={t('results.rankingTitle')} subtitle={t('results.rankingSubtitle')} />
        <View style={{ flexDirection: dir.row, gap: spacing.xs, marginTop: spacing.sm, marginBottom: spacing.sm, flexWrap: 'wrap' }}>
          {FILTERS.map((item) => (
            <Chip key={item} label={t(`results.filter${item.charAt(0).toUpperCase()}${item.slice(1)}`)} active={filter === item} onPress={() => setFilter(item)} />
          ))}
        </View>
        <View style={{ flexDirection: dir.row, gap: spacing.sm, marginBottom: spacing.sm }}>
          <View style={styles.summaryTile}>
            <Text variant="h2" color={colors.teal700}>{percent(best.best.readiness, lang)}</Text>
            <Text variant="micro" color={colors.ink50}>{t('results.readinessLabel')}</Text>
          </View>
          <View style={styles.summaryTile}>
            <Text variant="h2" color={colors.sky700}>{result.summary.eligibleCountries}</Text>
            <Text variant="micro" color={colors.ink50}>{t('results.filterEligible')}</Text>
          </View>
          <View style={styles.summaryTile}>
            <Text variant="h2" color={colors.gold}>{result.summary.countries}</Text>
            <Text variant="micro" color={colors.ink50}>{t('home.statsCountries')}</Text>
          </View>
        </View>
        {ranked.map((country) => (
          <CountryCard
            key={country.code}
            item={country}
            onPress={() => navigation.navigate('CountryDetail', { code: country.code })}
          />
        ))}
        {!ranked.length ? (
          <Card>
            <Text variant="small" color={colors.ink50} style={{ textAlign: 'center' }}>{t('explore.noResult')}</Text>
          </Card>
        ) : null}
      </View>

      <View style={{ padding: spacing.md }}>
        <PressableScale onPress={() => navigation.navigate('Advisor')}>
          <Card style={{ backgroundColor: colors.sky50, borderColor: colors.sky300 }}>
            <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.sm }}>
              <View style={styles.advisorIcon}>
                <Ionicons name="chatbubbles-outline" size={18} color={colors.sky700} />
              </View>
              <View style={{ flex: 1 }}>
                <Text variant="h3" color={colors.sky700} style={{ textAlign: dir.text }}>{t('advisor.title')}</Text>
                <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text }}>{t('advisor.subtitle')}</Text>
              </View>
              <Ionicons name={dir.isRtl ? 'chevron-back' : 'chevron-forward'} size={16} color={colors.sky700} />
            </View>
          </Card>
        </PressableScale>
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
  rankBadge: {
    width: 28, height: 28, borderRadius: 9, backgroundColor: colors.teal100,
    alignItems: 'center', justifyContent: 'center',
  },
  summaryTile: {
    flex: 1, alignItems: 'center', paddingVertical: spacing.sm,
    backgroundColor: colors.surface, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.border,
  },
  advisorIcon: {
    width: 38, height: 38, borderRadius: 12, backgroundColor: colors.white,
    alignItems: 'center', justifyContent: 'center',
  },
};
