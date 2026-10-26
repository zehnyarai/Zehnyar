import React from 'react';
import { Alert, View } from 'react-native';
import Constants from 'expo-constants';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, fonts, gradients, radius, spacing } from '../theme';
import { useDirection, useI18n } from '../i18n';
import { useAppState } from '../core/appState';
import { totals, meta } from '../core/data';
import { Button, Card, Divider, KeyValue, Pill, PressableScale, ScrollScreen, SectionTitle, Text, TrustBadge } from '../components/ui';

const appVersion = (Constants.expoConfig && Constants.expoConfig.version) || '2.1.0';

export default function ProfileScreen({ navigation }) {
  const { t, lang, pick, setLanguage } = useI18n();
  const dir = useDirection();
  const { resetAll, hasAssessment } = useAppState();

  const confirmReset = () => {
    Alert.alert(
      t('profile.resetTitle'),
      t('profile.resetBody'),
      [
        { text: t('common.cancel'), style: 'cancel' },
        {
          text: t('profile.resetAction'),
          style: 'destructive',
          onPress: async () => {
            await resetAll();
            Alert.alert(t('profile.resetDone'));
          },
        },
      ],
    );
  };

  return (
    <ScrollScreen>
      <LinearGradient colors={gradients.hero} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
        <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.sm }}>
          <View style={styles.avatar}>
            <Ionicons name="person-outline" size={22} color={colors.teal800} />
          </View>
          <View style={{ flex: 1 }}>
            <Text variant="h2" color={colors.white} style={{ textAlign: dir.text }}>{t('profile.title')}</Text>
            <Text variant="micro" style={{ color: 'rgba(255,255,255,0.72)', textAlign: dir.text }}>
              {hasAssessment ? t('results.title') : t('home.quickAssess')}
            </Text>
          </View>
        </View>
        <View style={{ marginTop: spacing.md }}>
          <View style={styles.glass}>
            <View style={{ flexDirection: dir.row, alignItems: 'center', justifyContent: 'space-between' }}>
              <Text variant="small" color={colors.white} style={{ textAlign: dir.text }}>{t('profile.language')}</Text>
              <View style={{ flexDirection: 'row', gap: 6 }}>
                {['fa', 'en'].map((code) => (
                  <PressableScale key={code} onPress={() => setLanguage(code)}>
                    <View style={[styles.langChip, lang === code && styles.langChipActive]}>
                      <Text variant="micro" style={{ color: lang === code ? colors.teal800 : colors.white, fontFamily: fonts.semibold }}>
                        {code === 'fa' ? t('profile.persian') : t('profile.english')}
                      </Text>
                    </View>
                  </PressableScale>
                ))}
              </View>
            </View>
            <Text variant="micro" style={{ color: 'rgba(255,255,255,0.6)', marginTop: 4, textAlign: dir.text }}>
              {t('profile.languageHint')}
            </Text>
          </View>
        </View>
      </LinearGradient>

      <View style={{ padding: spacing.md, gap: spacing.md }}>
        <Card>
          <SectionTitle title={t('payments.title')} subtitle={t('payments.subtitle')} />
          <Button label={t('payments.packages')} icon="card-outline" onPress={() => navigation.navigate('Payments')} style={{ marginTop: spacing.sm }} />
        </Card>
        <Card>
          <SectionTitle title={t('profile.dataTitle')} />
          <View style={{ marginTop: spacing.xs }}>
            <KeyValue label={t('profile.dataVersion')} value={meta.version} />
            <KeyValue label={t('profile.verifiedAt')} value={lang === 'fa' ? 'مهر ۱۴۰۵ / اکتبر ۲۰۲۶' : 'October 2026'} tone={colors.success} />
            <KeyValue label={t('profile.coverage')} value={`${totals.countries} • ${totals.visas} • ${totals.occupations}`} />
            <KeyValue label={t('profile.developer')} value={appVersion} />
          </View>
          <View style={{ marginTop: spacing.sm }}>
            <TrustBadge label={t('home.trusted')} value={t('home.verifiedValue')} />
          </View>
        </Card>

        <Card>
          <SectionTitle title={t('profile.aboutTitle')} />
          <Text variant="small" color={colors.ink70} style={{ marginTop: spacing.xs, textAlign: dir.text }}>
            {t('profile.aboutBody')}
          </Text>
          <Divider style={{ marginVertical: spacing.sm }} />
          <View style={{ flexDirection: dir.row, gap: 6, flexWrap: 'wrap' }}>
            <Pill label={pick('ارزیابی چندلایه', 'Multi-layer scoring')} tone="teal" icon="layers" />
            <Pill label={pick('منبع رسمی', 'Official sources')} tone="gold" icon="shield-checkmark" />
            <Pill label={pick('کاملاً آفلاین', 'Fully offline')} tone="sky" icon="cloud-offline" />
          </View>
        </Card>

        <Card>
          <SectionTitle title={t('profile.privacyTitle')} />
          <Text variant="small" color={colors.ink70} style={{ marginTop: spacing.xs, textAlign: dir.text }}>
            {t('profile.privacyBody')}
          </Text>
          <Divider style={{ marginVertical: spacing.sm }} />
          <SectionTitle title={t('profile.disclaimerTitle')} />
          <Text variant="small" color={colors.ink70} style={{ marginTop: spacing.xs, textAlign: dir.text }}>
            {t('profile.disclaimerBody')}
          </Text>
        </Card>

        <Card style={{ borderColor: colors.dangerSoft }}>
          <SectionTitle title={t('profile.resetTitle')} />
          <Text variant="small" color={colors.ink70} style={{ marginTop: spacing.xs, textAlign: dir.text }}>
            {t('profile.resetBody')}
          </Text>
          <Button label={t('profile.resetAction')} icon="trash-outline" variant="outline" onPress={confirmReset} style={{ marginTop: spacing.sm }} />
        </Card>
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
  avatar: {
    width: 44, height: 44, borderRadius: 15, backgroundColor: colors.goldSoft,
    alignItems: 'center', justifyContent: 'center',
  },
  glass: {
    backgroundColor: 'rgba(255,255,255,0.12)',
    borderRadius: radius.md,
    padding: spacing.sm,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.16)',
  },
  langChip: {
    paddingHorizontal: 10, paddingVertical: 5, borderRadius: radius.pill,
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.3)',
  },
  langChipActive: { backgroundColor: colors.white, borderColor: colors.white },
};
