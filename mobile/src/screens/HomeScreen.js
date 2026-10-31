import React from 'react';
import { Image, ScrollView, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import Constants from 'expo-constants';
import * as Haptics from 'expo-haptics';
import { colors, fonts, gradients, radius, shadow, spacing } from '../theme';
import { useDirection, useI18n } from '../i18n';
import { useAppState } from '../core/appState';
import { formatVerifiedDate, getCountries, getDatasetFreshness, getMeta, getTotals } from '../core/data';
import { Button, Card, PressableScale, ScrollScreen, SectionTitle, Text, TrustBadge } from '../components/ui';
import { FeaturedCountry, GoalTile } from '../components/cards';
import { localiseNumber, percent } from '../core/format';

const GOALS = ['work', 'study', 'startup', 'investment', 'selfsponsored'];
const REASONS = [
  { key: 'why1', icon: 'layers-outline' },
  { key: 'why2', icon: 'shield-checkmark-outline' },
  { key: 'why3', icon: 'map-outline' },
];

export default function HomeScreen({ navigation }) {
  const { t, lang, pick, toggleLanguage } = useI18n();
  const dir = useDirection();
  const { profile, updateProfile, hasAssessment, result } = useAppState();
  const countries = getCountries();
  const totals = getTotals();
  const dataMeta = getMeta();
  const testBuild = Constants.expoConfig?.extra?.testBuild === true;
  const verifiedDate = formatVerifiedDate(dataMeta.lastVerified, lang);
  const freshness = getDatasetFreshness();
  const freshnessMessage = freshness.status === 'stale' || freshness.status === 'invalid'
    ? t('home.dataStale')
    : freshness.status === 'review_due' ? t('home.dataReviewDue') : null;

  const draft = profile.languages.length > 0 || profile.work.totalYears > 0 || profile.investmentUsd > 0;
  const best = result ? result.countries[0] : null;
  const featured = [...countries].sort((a, b) => a.priority - b.priority).slice(0, 6);

  const startAssessment = (goal) => {
    if (goal) updateProfile({ goal });
    navigation.navigate('Wizard', { from: 'home' });
  };

  return (
    <ScrollScreen>
      <LinearGradient
        colors={gradients.hero}
        start={{ x: 0.05, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.hero}
      >
        <View style={styles.heroGlow} />
        <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.sm }}>
          <Image source={require('../assets/icon.png')} style={styles.logoMark} accessibilityLabel={t('appName')} />
          <View style={{ flex: 1 }}>
            <Text variant="h3" color={colors.white} style={{ textAlign: dir.text }}>{t('appName')}</Text>
            <Text variant="micro" style={{ color: 'rgba(255,255,255,0.72)', textAlign: dir.text }}>{t('appTagline')}</Text>
          </View>
          <PressableScale
            accessibilityLabel={t('profile.language')}
            onPress={() => {
              Haptics.selectionAsync().catch(() => {});
              toggleLanguage();
            }}
          >
            <View style={styles.langPill}>
              <Text variant="micro" style={{ color: colors.white, fontFamily: fonts.bold }}>
                {lang === 'fa' ? 'EN' : 'فا'}
              </Text>
            </View>
          </PressableScale>
        </View>

        <Text variant="display" color={colors.white} style={{ marginTop: spacing.lg, textAlign: dir.text }}>
          {t('home.heroTitle')}
        </Text>
        <Text variant="small" style={{ color: 'rgba(255,255,255,0.82)', marginTop: spacing.xs, textAlign: dir.text }}>
          {t('home.heroSubtitle')}
        </Text>
        {testBuild ? (
          <View style={{ marginTop: spacing.sm, padding: spacing.sm, borderRadius: radius.md, backgroundColor: 'rgba(255,255,255,0.16)' }}>
            <Text variant="micro" style={{ color: colors.goldSoft, textAlign: dir.text, fontFamily: fonts.bold }}>
              {t('home.testBuildNotice')}
            </Text>
          </View>
        ) : null}

        <View style={{ marginTop: spacing.md }}>
          <View style={styles.glassBadge}>
            <Ionicons name="shield-checkmark" size={12} color={colors.goldSoft} />
            <Text variant="micro" style={{ color: colors.goldSoft }}>{t('home.verified')}</Text>
            <Text variant="micro" style={{ color: colors.white, fontFamily: fonts.bold }}>{verifiedDate}</Text>
          </View>
        </View>
        {freshnessMessage ? (
          <Text variant="micro" style={{ color: '#FFE0B2', marginTop: spacing.xs, textAlign: dir.text }}>
            {freshnessMessage}
          </Text>
        ) : null}

        <View style={{ marginTop: spacing.lg, gap: spacing.xs }}>
          <Button
            label={hasAssessment ? t('home.ctaResult') : draft ? t('home.ctaContinue') : t('home.ctaStart')}
            icon={hasAssessment ? 'analytics-outline' : 'sparkles-outline'}
            onPress={() => (hasAssessment ? navigation.navigate('Results') : startAssessment())}
            variant="light"
          />
          <View style={{ flexDirection: dir.row, alignItems: 'center', justifyContent: 'center', gap: 6, marginTop: 2 }}>
            <Ionicons name="lock-closed" size={10} color="rgba(255,255,255,0.65)" />
            <Text variant="micro" style={{ color: 'rgba(255,255,255,0.7)', textAlign: 'center' }}>
              {t('home.privacyNote')}
            </Text>
          </View>
        </View>

        <View style={[styles.statsRow, { flexDirection: dir.row }]}>
          <Stat value={totals.countries} label={t('home.statsCountries')} />
          <View style={styles.statDivider} />
          <Stat value={totals.visas} label={t('home.statsVisas')} />
          <View style={styles.statDivider} />
          <Stat value={totals.occupations} label={t('home.statsOccupations')} />
        </View>
      </LinearGradient>

      {best ? (
        <PressableScale onPress={() => navigation.navigate('Results')} style={{ marginTop: spacing.lg, marginHorizontal: spacing.md }}>
          <Card padded={false}>
            <LinearGradient colors={gradients.mint} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.resultStrip}>
              <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.sm }}>
                <Text style={{ fontSize: 26 }}>{best.flag}</Text>
                <View style={{ flex: 1 }}>
                  <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text }}>{t('results.bestTitle')}</Text>
                  <Text variant="h3" color={colors.ink} style={{ textAlign: dir.text }}>{pick(best.nameFa, best.nameEn)}</Text>
                  <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text }} numberOfLines={1}>
                    {pick(best.best.visaNameFa, best.best.visaNameEn)}
                  </Text>
                </View>
                <View style={{ alignItems: 'center' }}>
                  <Text variant="h2" color={colors.teal700}>{percent(best.best.chance, lang)}</Text>
                  <Text variant="micro" color={colors.ink35}>{t('results.chanceLabel')}</Text>
                </View>
              </View>
            </LinearGradient>
          </Card>
        </PressableScale>
      ) : null}

      <View style={{ paddingHorizontal: spacing.md, marginTop: spacing.xl }}>
        <SectionTitle title={t('home.goalsTitle')} subtitle={t('home.goalsSubtitle')} />
        <View style={{ gap: spacing.sm, marginTop: spacing.md }}>
          <View style={{ flexDirection: dir.row, gap: spacing.sm }}>
            {GOALS.slice(0, 2).map((goal) => (
              <GoalTile key={goal} goalId={goal} active={profile.goal === goal} onPress={() => startAssessment(goal)} />
            ))}
          </View>
          <View style={{ flexDirection: dir.row, gap: spacing.sm }}>
            {GOALS.slice(2, 4).map((goal) => (
              <GoalTile key={goal} goalId={goal} active={profile.goal === goal} onPress={() => startAssessment(goal)} />
            ))}
          </View>
          <View style={{ flexDirection: dir.row, gap: spacing.sm }}>
            <GoalTile goalId="selfsponsored" active={profile.goal === 'selfsponsored'} onPress={() => startAssessment('selfsponsored')} />
            <PressableScale onPress={() => navigation.navigate('Explore')} style={{ flex: 1 }}>
              <View style={styles.exploreTile}>
                <Ionicons name="earth-outline" size={18} color={colors.teal700} />
                <Text variant="h3" color={colors.teal800} style={{ textAlign: dir.text, marginTop: 6 }}>
                  {t('nav.explore')}
                </Text>
                <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text, marginTop: 2 }}>
                  {pick('۱۵ مقصد با درگاه رسمی', '15 destinations with official portals')}
                </Text>
              </View>
            </PressableScale>
          </View>
        </View>
      </View>

      <View style={{ marginTop: spacing.xl }}>
        <View style={{ paddingHorizontal: spacing.md }}>
          <SectionTitle
            title={t('home.featuredTitle')}
            subtitle={t('home.featuredSubtitle')}
            actionLabel={t('common.viewAll')}
            onAction={() => navigation.navigate('Explore')}
          />
        </View>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={{ paddingHorizontal: spacing.md, paddingTop: spacing.md, paddingBottom: spacing.xs }}
        >
          {featured.map((country) => (
            <FeaturedCountry
              key={country.code}
              country={country}
              onPress={() => navigation.navigate('CountryDetail', { code: country.code })}
            />
          ))}
        </ScrollView>
      </View>

      <View style={{ paddingHorizontal: spacing.md, marginTop: spacing.lg }}>
        <Card style={{ backgroundColor: colors.goldSoft, borderColor: '#E8D9AE' }}>
          <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.sm }}>
            <View style={styles.insightIcon}>
              <Ionicons name="bulb-outline" size={17} color="#7A5F19" />
            </View>
            <Text variant="h3" color="#6B5416" style={{ flex: 1, textAlign: dir.text }}>{t('home.insightTitle')}</Text>
          </View>
          <Text variant="small" color="#6B5416" style={{ marginTop: spacing.xs, textAlign: dir.text }}>
            {t('home.insightBody')}
          </Text>
        </Card>
      </View>

      <View style={{ paddingHorizontal: spacing.md, marginTop: spacing.xl }}>
        <SectionTitle title={t('home.whyTitle')} />
        <View style={{ gap: spacing.sm, marginTop: spacing.md }}>
          {REASONS.map((reason) => (
            <Card key={reason.key} level={0} style={{ borderColor: colors.border }}>
              <View style={{ flexDirection: dir.row, gap: spacing.sm, alignItems: 'flex-start' }}>
                <View style={styles.reasonIcon}>
                  <Ionicons name={reason.icon} size={17} color={colors.teal700} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text variant="h3" color={colors.ink} style={{ textAlign: dir.text }}>{t(`home.${reason.key}Title`)}</Text>
                  <Text variant="small" color={colors.ink50} style={{ marginTop: 2, textAlign: dir.text }}>
                    {t(`home.${reason.key}Body`)}
                  </Text>
                </View>
              </View>
            </Card>
          ))}
        </View>
      </View>

      <View style={{ paddingHorizontal: spacing.md, marginTop: spacing.lg }}>
        <TrustBadge label={t('home.trusted')} value={verifiedDate} />
        <Text variant="micro" color={colors.ink35} style={{ marginTop: spacing.sm, textAlign: dir.text }}>
          {t('results.disclaimer')}
        </Text>
      </View>
    </ScrollScreen>
  );
}

function Stat({ value, label }) {
  const { lang } = useI18n();
  return (
    <View style={{ flex: 1, alignItems: 'center' }}>
      <Text variant="h2" color={colors.white}>{localiseNumber(value, lang)}</Text>
      <Text variant="micro" style={{ color: 'rgba(255,255,255,0.72)', textAlign: 'center' }}>{label}</Text>
    </View>
  );
}

const styles = {
  hero: {
    paddingTop: spacing.xxl,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.lg,
    borderBottomLeftRadius: radius.xxl,
    borderBottomRightRadius: radius.xxl,
    overflow: 'hidden',
  },
  heroGlow: {
    position: 'absolute',
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: 'rgba(124,198,232,0.22)',
    top: -90,
    right: -70,
  },
  logoMark: {
    width: 40, height: 40, borderRadius: 13, backgroundColor: colors.goldSoft,
    alignItems: 'center', justifyContent: 'center',
  },
  langPill: {
    paddingHorizontal: 10, paddingVertical: 6, borderRadius: radius.pill,
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.35)', backgroundColor: 'rgba(255,255,255,0.12)',
  },
  glassBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 5, alignSelf: 'flex-start',
    paddingHorizontal: spacing.sm, paddingVertical: 5, borderRadius: radius.pill,
    backgroundColor: 'rgba(255,255,255,0.14)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.2)',
  },
  statsRow: {
    marginTop: spacing.lg, alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: radius.lg,
    paddingVertical: spacing.sm, borderWidth: 1, borderColor: 'rgba(255,255,255,0.14)',
  },
  statDivider: { width: 1, height: 26, backgroundColor: 'rgba(255,255,255,0.18)' },
  resultStrip: { borderRadius: radius.lg, padding: spacing.md },
  exploreTile: {
    flex: 1, borderRadius: radius.md, borderWidth: 1.5, borderColor: colors.border,
    backgroundColor: colors.sky50, padding: spacing.sm, minHeight: 118,
  },
  insightIcon: {
    width: 32, height: 32, borderRadius: 10, backgroundColor: 'rgba(255,255,255,0.55)',
    alignItems: 'center', justifyContent: 'center',
  },
  reasonIcon: {
    width: 34, height: 34, borderRadius: 11, backgroundColor: colors.teal100,
    alignItems: 'center', justifyContent: 'center',
  },
};
