import React, { useMemo, useState } from 'react';
import { TextInput, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, fonts, gradients, radius, spacing } from '../theme';
import { useDirection, useI18n } from '../i18n';
import { useAppState } from '../core/appState';
import { allVisaTypes, countries, totals } from '../core/data';
import { Card, Chip, Pill, ScrollScreen, SectionTitle, Text } from '../components/ui';
import { CountryCard, FeaturedCountry } from '../components/cards';

export default function ExploreScreen({ navigation }) {
  const { t, pick, lang } = useI18n();
  const dir = useDirection();
  const { result } = useAppState();
  const [query, setQuery] = useState('');
  const [type, setType] = useState(null);

  const list = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return countries.filter((country) => {
      const matchesQuery = !needle
        || country.nameFa.includes(query.trim())
        || country.nameEn.toLowerCase().includes(needle)
        || country.code.toLowerCase().includes(needle);
      const matchesType = !type || country.visas.some((visa) => visa.type === type);
      return matchesQuery && matchesType;
    });
  }, [query, type]);

  const withResults = useMemo(() => {
    if (!result) return [];
    const map = new Map(result.countries.map((country) => [country.code, country]));
    return countries.map((country) => map.get(country.code) || country);
  }, [result]);

  return (
    <ScrollScreen>
      <LinearGradient colors={gradients.hero} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
        <Text variant="h1" color={colors.white} style={{ textAlign: dir.text }}>{t('explore.title')}</Text>
        <Text variant="small" style={{ color: 'rgba(255,255,255,0.78)', marginTop: 2, textAlign: dir.text }}>
          {t('explore.subtitle')}
        </Text>
        <View style={[styles.search, { flexDirection: dir.row }]}>
          <Ionicons name="search" size={17} color={colors.ink35} />
          <TextInput
            value={query}
            onChangeText={setQuery}
            placeholder={t('explore.searchPlaceholder')}
            placeholderTextColor={colors.ink35}
            style={[styles.input, { textAlign: dir.text, writingDirection: dir.writing }]}
          />
        </View>
        <View style={{ flexDirection: dir.row, gap: spacing.xs, marginTop: spacing.sm, flexWrap: 'wrap' }}>
          <Pill label={`${totals.countries} ${t('explore.countLabel')}`} tone="gold" icon="earth" />
          <Pill label={`${totals.visas} ${t('home.statsVisas')}`} tone="sky" icon="documents" />
          <Pill label={`${totals.occupations} ${t('home.statsOccupations')}`} tone="teal" icon="briefcase" />
        </View>
      </LinearGradient>

      <View style={{ padding: spacing.md }}>
        <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text, marginBottom: 6 }}>
          {t('explore.filters')}
        </Text>
        <View style={{ flexDirection: dir.row, flexWrap: 'wrap', gap: spacing.xs }}>
          <Chip label={t('common.all')} active={!type} onPress={() => setType(null)} />
          {allVisaTypes.map((item) => (
            <Chip key={item} label={t(`visaTypes.${item}`)} active={type === item} onPress={() => setType(type === item ? null : item)} />
          ))}
        </View>
      </View>

      {withResults.length ? (
        <View style={{ marginBottom: spacing.sm }}>
          <View style={{ paddingHorizontal: spacing.md }}>
            <SectionTitle title={t('home.featuredTitle')} subtitle={t('home.featuredSubtitle')} />
          </View>
          <ScrollScreen horizontal showsHorizontalScrollIndicator={false} contentStyle={{ padding: spacing.md, paddingBottom: spacing.xs }} style={{ maxHeight: 210 }}>
            {withResults.slice(0, 8).map((country) => (
              <FeaturedCountry key={country.code} country={country} onPress={() => navigation.navigate('CountryDetail', { code: country.code })} />
            ))}
          </ScrollScreen>
        </View>
      ) : null}

      <View style={{ paddingHorizontal: spacing.md }}>
        <SectionTitle title={t('nav.explore')} subtitle={`${list.length} ${t('explore.countLabel')}`} />
        <View style={{ marginTop: spacing.sm }}>
          {list.map((country) => {
            const assessed = result ? result.countries.find((item) => item.code === country.code) : null;
            return (
              <CountryCard
                key={country.code}
                item={assessed || country}
                onPress={() => navigation.navigate('CountryDetail', { code: country.code })}
              />
            );
          })}
          {!list.length ? (
            <Card>
              <Text variant="small" color={colors.ink50} style={{ textAlign: 'center' }}>{t('explore.noResult')}</Text>
            </Card>
          ) : null}
        </View>
      </View>

      <View style={{ padding: spacing.md }}>
        <Text variant="micro" color={colors.ink35} style={{ textAlign: dir.text }}>
          {lang === 'fa' ? 'همه مقصدها به درگاه رسمی و تاریخ استعلام پیوند دارند.' : 'Every destination links to its official portal and verification date.'}
        </Text>
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
  search: {
    alignItems: 'center',
    gap: spacing.xs,
    marginTop: spacing.md,
    backgroundColor: colors.white,
    borderRadius: radius.md,
    paddingHorizontal: spacing.sm,
    height: 48,
  },
  input: { flex: 1, fontFamily: fonts.medium, fontSize: 14, color: colors.ink, paddingVertical: 0 },
};
