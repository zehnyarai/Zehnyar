import React from 'react';
import { Alert, Linking, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, spacing } from '../theme';
import { useDirection, useI18n } from '../i18n';
import { Button, Card, Pill, ScrollScreen, SectionTitle, Text } from '../components/ui';
import { researchSources } from '../data/researchSources';

const groups = [
  { id: 'law', tone: 'teal', icon: 'document-text-outline' },
  { id: 'statistics', tone: 'sky', icon: 'stats-chart-outline' },
  { id: 'jobs', tone: 'gold', icon: 'briefcase-outline' },
  { id: 'humanitarian', tone: 'warn', icon: 'heart-outline' },
];

export default function ResearchSourcesScreen() {
  const { t, lang } = useI18n();
  const dir = useDirection();
  const isFa = lang === 'fa';

  const openSource = async (url) => {
    if (!url) return;
    try {
      await Linking.openURL(url);
    } catch {
      Alert.alert(t('sources.openError'));
    }
  };

  return (
    <ScrollScreen>
      <View style={styles.hero}>
        <View style={[styles.heroIcon, { alignSelf: dir.align }]}>
          <Ionicons name="library-outline" size={23} color={colors.teal700} />
        </View>
        <Text variant="h1" style={{ textAlign: dir.text }}>{t('sources.title')}</Text>
        <Text variant="small" color={colors.ink70} style={{ marginTop: spacing.xs, textAlign: dir.text }}>
          {t('sources.subtitle')}
        </Text>
      </View>

      <View style={{ padding: spacing.md, gap: spacing.md }}>
        <Card style={styles.notice}>
          <View style={{ flexDirection: dir.row, alignItems: 'flex-start', gap: spacing.xs }}>
            <Ionicons name="information-circle-outline" size={20} color={colors.teal700} />
            <Text variant="small" color={colors.ink70} style={{ flex: 1, textAlign: dir.text }}>
              {t('sources.notice')}
            </Text>
          </View>
        </Card>

        {groups.map((group) => {
          const items = researchSources.filter((source) => source.category === group.id);
          if (!items.length) return null;
          return (
            <View key={group.id} style={{ gap: spacing.sm }}>
              <SectionTitle title={t(`sources.category.${group.id}`)} />
              {items.map((source) => (
                <Card key={source.id} style={styles.sourceCard}>
                  <View style={{ flexDirection: dir.row, alignItems: 'flex-start', gap: spacing.sm }}>
                    <View style={[styles.sourceIcon, { backgroundColor: group.id === 'humanitarian' ? colors.warnSoft : colors.teal100 }]}>
                      <Ionicons name={group.icon} size={19} color={group.id === 'humanitarian' ? colors.warn : colors.teal700} />
                    </View>
                    <View style={{ flex: 1, gap: 4 }}>
                      <Text variant="h3" style={{ textAlign: dir.text }}>{isFa ? source.nameFa : source.nameEn}</Text>
                      <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text }}>
                        {isFa ? source.ownerFa : source.ownerEn}
                      </Text>
                    </View>
                  </View>
                  <Text variant="small" color={colors.ink70} style={{ marginTop: spacing.sm, textAlign: dir.text }}>
                    {isFa ? source.coverageFa : source.coverageEn}
                  </Text>
                  <View style={{ marginTop: spacing.sm, flexDirection: dir.row, alignItems: 'center', justifyContent: 'space-between', gap: spacing.xs, flexWrap: 'wrap' }}>
                    <Pill label={isFa ? source.dateFa : source.dateEn} tone={group.tone} icon="time-outline" />
                    {source.url ? (
                      <Button
                        label={t('sources.open')}
                        icon="open-outline"
                        variant="outline"
                        size="sm"
                        onPress={() => openSource(source.url)}
                      />
                    ) : null}
                  </View>
                </Card>
              ))}
            </View>
          );
        })}
        <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text, paddingHorizontal: spacing.xs }}>
          {t('sources.footer')}
        </Text>
      </View>
    </ScrollScreen>
  );
}

const styles = {
  hero: {
    paddingTop: spacing.xxl,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
    gap: spacing.xs,
    backgroundColor: colors.surface,
    borderBottomLeftRadius: radius.xxl,
    borderBottomRightRadius: radius.xxl,
  },
  heroIcon: {
    width: 46,
    height: 46,
    borderRadius: radius.lg,
    backgroundColor: colors.teal100,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.xs,
  },
  notice: { borderColor: colors.borderStrong, backgroundColor: colors.canvasAlt },
  sourceCard: { gap: 0 },
  sourceIcon: {
    width: 38,
    height: 38,
    borderRadius: radius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
};
