import React, { useState } from 'react';
import { Linking, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, fonts, radius, spacing } from '../theme';
import { useDirection, useI18n } from '../i18n';
import { money, num, percent, scorePair } from '../core/format';
import { formatVerifiedDate } from '../core/data';
import { Card, Chip, Pill, PressableScale, Text, TrustBadge, Button, Divider, KeyValue } from './ui';
import { CriteriaBar, MiniBar, ScoreArc } from './charts';

export function CountryCard({ item, onPress, showChance = true }) {
  const { t, lang, pick } = useI18n();
  const dir = useDirection();
  const best = item.best;
  const chance = best ? best.chance : null;
  const tone = chance === null ? colors.ink : chance >= 70 ? colors.success : chance >= 45 ? colors.gold : colors.danger;

  return (
    <PressableScale onPress={onPress}>
      <Card style={{ marginBottom: spacing.sm }} padded={false}>
        <View style={{ padding: spacing.md }}>
          <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.sm }}>
            <View style={styles.flagWrap}>
              <Text style={{ fontSize: 22 }}>{item.flag}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text variant="h3" color={colors.ink} style={{ textAlign: dir.text }}>
                {pick(item.nameFa, item.nameEn)}
              </Text>
              <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text }} numberOfLines={1}>
                {best ? pick(best.visaNameFa, best.visaNameEn) : `${item.visaCount || item.visas.length} ${t('nav.explore')}`}
              </Text>
            </View>
            {showChance && best ? (
              <View style={{ alignItems: 'center' }}>
                <Text variant="h3" style={{ color: tone }}>{percent(chance, lang)}</Text>
                <Text variant="micro" color={colors.ink35}>{t('results.chanceLabel')}</Text>
              </View>
            ) : null}
            <Ionicons name={dir.isRtl ? 'chevron-back' : 'chevron-forward'} size={16} color={colors.ink35} />
          </View>

          {best ? (
            <>
              <View style={{ marginTop: spacing.sm }}>
                <MiniBar value={chance} tone={tone} />
              </View>
              <View style={{ flexDirection: dir.row, alignItems: 'center', gap: 6, marginTop: spacing.sm, flexWrap: 'wrap' }}>
                {best.eligible ? (
                  <Pill label={t('results.eligible')} tone="success" icon="checkmark-circle" />
                ) : (
                  <Pill label={t('results.needsFix')} tone="warn" icon="alert-circle" />
                )}
                <Pill label={pick(best.bandFa, best.bandEn)} tone="sky" />
                <Pill label={`${t('country.yourScore')} ${scorePair(best.achieved, best.maxPoints, lang)}`} tone="neutral" />
              </View>
            </>
          ) : (
            <View style={{ flexDirection: dir.row, gap: 6, marginTop: spacing.sm, flexWrap: 'wrap' }}>
              {Array.from(new Set(item.visas.map((visa) => visa.type))).slice(0, 3).map((type) => (
                <Pill key={type} label={t(`visaTypes.${type}`)} tone="teal" />
              ))}
              <Pill label={`${num(item.visas.length, lang)} ${t('country.visas')}`} tone="neutral" />
            </View>
          )}
        </View>
        {best ? (
          <View style={styles.cardFooter}>
            <TrustBadge label={t('country.lastVerified')} value={formatVerifiedDate(item.lastVerified, lang)} />
            <Text variant="micro" color={colors.teal700} style={{ fontFamily: fonts.semibold }}>
              {t('results.roadmapTitle')}
            </Text>
          </View>
        ) : null}
      </Card>
    </PressableScale>
  );
}

export function FeaturedCountry({ country, onPress }) {
  const { pick, t, lang } = useI18n();
  const dir = useDirection();
  return (
    <PressableScale onPress={onPress}>
      <Card padded={false} style={{ width: 208, marginRight: spacing.sm }}>
        <View style={styles.featuredTop}>
          <Text style={{ fontSize: 26 }}>{country.flag}</Text>
          <Pill label={num(country.visas.length, lang)} tone="teal" icon="documents-outline" />
        </View>
        <View style={{ padding: spacing.md, paddingTop: spacing.sm }}>
          <Text variant="h3" color={colors.ink} style={{ textAlign: dir.text }}>
            {pick(country.nameFa, country.nameEn)}
          </Text>
          <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text, marginTop: 2 }} numberOfLines={2}>
            {pick(country.summaryFa, country.summaryEn)}
          </Text>
          <View style={{ flexDirection: dir.row, alignItems: 'center', gap: 4, marginTop: spacing.sm }}>
            <Ionicons name="shield-checkmark" size={11} color={colors.gold} />
            <Text variant="micro" color={colors.ink50}>{t('country.officialBadge')}</Text>
          </View>
        </View>
      </Card>
    </PressableScale>
  );
}

export function VisaCard({ visa, best, expanded, onToggle }) {
  const { t, lang, pick } = useI18n();
  const dir = useDirection();
  const tone = visa.chance >= 70 ? colors.success : visa.chance >= 45 ? colors.gold : colors.danger;

  return (
    <Card style={{ marginBottom: spacing.sm }} padded={false}>
      <PressableScale onPress={onToggle}>
        <View style={{ padding: spacing.md }}>
          <View style={{ flexDirection: dir.row, alignItems: 'flex-start', gap: spacing.sm }}>
            <ScoreArc percent={visa.readiness} />
            <View style={{ flex: 1 }}>
              <View style={{ flexDirection: dir.row, alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                <Text variant="h3" color={colors.ink} style={{ textAlign: dir.text, flexShrink: 1 }}>
                  {pick(visa.visaNameFa, visa.visaNameEn)}
                </Text>
                {best ? <Pill label={t('results.bestTitle')} tone="gold" icon="star" /> : null}
              </View>
              <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text, marginTop: 2 }} numberOfLines={2}>
                {pick(visa.taglineFa, visa.taglineEn)}
              </Text>
              <View style={{ flexDirection: dir.row, gap: 6, marginTop: spacing.xs, flexWrap: 'wrap' }}>
                <Pill label={t(`visaTypes.${visa.visaType}`)} tone="teal" />
                <Pill label={`${t('results.chanceLabel')} ${percent(visa.chance, lang)}`} tone={visa.chance >= 60 ? 'success' : visa.chance >= 35 ? 'warn' : 'danger'} />
                {visa.eligible ? <Pill label={t('results.eligible')} tone="success" icon="checkmark" /> : <Pill label={t('results.needsFix')} tone="warn" icon="alert" />}
              </View>
            </View>
          </View>
          <View style={{ marginTop: spacing.sm }}>
            <CriteriaBar value={visa.achieved} max={visa.maxPoints} />
            <View style={{ flexDirection: dir.row, justifyContent: 'space-between', marginTop: 4 }}>
              <Text variant="micro" color={colors.ink35}>{`${t('country.yourScore')}: ${num(visa.achieved, lang)}`}</Text>
              <Text variant="micro" color={colors.ink35}>{`${t('country.passMark')}: ${num(visa.passMark, lang)}`}</Text>
              <Text variant="micro" color={colors.ink35}>{`${t('country.maxPoints')}: ${num(visa.maxPoints, lang)}`}</Text>
            </View>
          </View>
        </View>
      </PressableScale>

      {expanded ? (
        <View style={{ paddingHorizontal: spacing.md, paddingBottom: spacing.md }}>
          <Divider style={{ marginBottom: spacing.sm }} />
          {visa.blockers.length ? (
            <View style={{ marginBottom: spacing.sm }}>
              <Text variant="h3" color={colors.danger} style={{ textAlign: dir.text, marginBottom: 4 }}>
                {t('results.blockerTitle')}
              </Text>
              {visa.blockers.map((blocker, index) => (
                <View key={`${blocker.kind}-${index}`} style={{ flexDirection: dir.row, gap: 6, marginBottom: 4 }}>
                  <Ionicons name="alert-circle" size={13} color={colors.danger} style={{ marginTop: 3 }} />
                  <Text variant="small" color={colors.ink70} style={{ flex: 1, textAlign: dir.text }}>
                    {pick(blocker.messageFa, blocker.messageEn)}
                  </Text>
                </View>
              ))}
            </View>
          ) : null}

          <Text variant="h3" color={colors.ink} style={{ textAlign: dir.text, marginBottom: 6 }}>{t('country.criteria')}</Text>
          {visa.criteria.map((crit) => (
            <View key={crit.id} style={{ marginBottom: 8 }}>
              <View style={{ flexDirection: dir.row, justifyContent: 'space-between', gap: spacing.sm }}>
                <Text variant="small" color={colors.ink70} style={{ flex: 1, textAlign: dir.text }} numberOfLines={2}>
                  {pick(crit.labelFa, crit.labelEn)}
                </Text>
                <Text variant="micro" style={{ color: crit.score > 0 ? colors.teal700 : colors.ink35, fontFamily: fonts.semibold }}>
                  {scorePair(crit.score, crit.max, lang)}
                </Text>
              </View>
              <View style={{ marginTop: 3 }}>
                <CriteriaBar value={crit.score} max={crit.max} />
              </View>
            </View>
          ))}

          <View style={{ marginTop: spacing.sm }}>
            <KeyValue label={t('country.processing')} value={pick(visa.processingTimeFa, visa.processingTimeEn) || '-'} />
            <KeyValue label={t('country.settlement')} value={money(visa.settlementRequiredUsd, lang, 'USD')} />
          </View>

          <Button
            label={t('country.openPortal')}
            icon="open-outline"
            variant="outline"
            size="sm"
            style={{ marginTop: spacing.sm }}
            onPress={() => Linking.openURL(visa.officialUrl)}
          />
        </View>
      ) : null}
    </Card>
  );
}

export function FeeList({ costs, lang }) {
  const { t, pick } = useI18n();
  const dir = useDirection();
  return (
    <View>
      {costs.lines.map((line, index) => (
        <View key={`${line.labelEn}-${index}`} style={{ paddingVertical: 9, borderBottomWidth: index === costs.lines.length - 1 ? 0 : 1, borderBottomColor: colors.border }}>
          <View style={{ flexDirection: dir.row, justifyContent: 'space-between', gap: spacing.sm }}>
            <Text variant="small" color={colors.ink} style={{ flex: 1, textAlign: dir.text }}>
              {pick(line.labelFa, line.labelEn)}
            </Text>
            <Text variant="small" style={{ fontFamily: fonts.semibold, color: colors.teal800 }}>
              {money(line.usd, lang, 'USD')}
            </Text>
          </View>
          <View style={{ flexDirection: dir.row, alignItems: 'center', gap: 6, marginTop: 3, flexWrap: 'wrap' }}>
            <Pill
              label={line.verified ? t('country.verifiedFee') : t('country.referenceFee')}
              tone={line.verified ? 'success' : 'warn'}
              icon={line.verified ? 'shield-checkmark' : 'information-circle'}
            />
            {line.payer === 'employer' ? <Pill label={t('country.employer')} tone="sky" /> : null}
            {line.count > 1 ? <Pill label={`${num(line.count, lang)}×`} tone="neutral" /> : null}
          </View>
        </View>
      ))}
    </View>
  );
}

export function ChecklistItem({ item, checked, onToggle }) {
  const { pick } = useI18n();
  const dir = useDirection();
  return (
    <PressableScale onPress={onToggle}>
      <View style={{ flexDirection: dir.row, alignItems: 'flex-start', gap: spacing.sm, paddingVertical: 9 }}>
        <View
          style={{
            width: 22, height: 22, borderRadius: 7, borderWidth: 1.5,
            borderColor: checked ? colors.teal600 : colors.border,
            backgroundColor: checked ? colors.teal600 : colors.surface,
            alignItems: 'center', justifyContent: 'center', marginTop: 1,
          }}
        >
          {checked ? <Ionicons name="checkmark" size={14} color={colors.white} /> : null}
        </View>
        <Text
          variant="small"
          color={checked ? colors.ink35 : colors.ink70}
          style={{ flex: 1, textAlign: dir.text, textDecorationLine: checked ? 'line-through' : 'none' }}
        >
          {pick(item.fa, item.en)}
        </Text>
      </View>
    </PressableScale>
  );
}

export function GoalTile({ goalId, active, onPress }) {
  const { t } = useI18n();
  const dir = useDirection();
  const icons = {
    work: 'briefcase-outline',
    study: 'school-outline',
    startup: 'rocket-outline',
    investment: 'trending-up-outline',
    selfsponsored: 'globe-outline',
  };
  return (
    <PressableScale onPress={onPress} style={{ flex: 1 }}>
      <View style={[styles.goalTile, { borderColor: active ? colors.teal600 : colors.border, backgroundColor: active ? colors.teal100 : colors.surface }]}>
        <View style={[styles.goalIcon, { backgroundColor: active ? colors.teal700 : colors.canvasAlt }]}>
          <Ionicons name={icons[goalId]} size={16} color={active ? colors.white : colors.teal700} />
        </View>
        <Text variant="h3" color={active ? colors.teal800 : colors.ink} style={{ textAlign: dir.text, marginTop: 6 }} numberOfLines={2}>
          {t(`goals.${goalId}.label`)}
        </Text>
        <Text variant="micro" color={colors.ink50} style={{ textAlign: dir.text, marginTop: 2 }} numberOfLines={2}>
          {t(`goals.${goalId}.desc`)}
        </Text>
      </View>
    </PressableScale>
  );
}

const styles = {
  flagWrap: {
    width: 44, height: 44, borderRadius: 14, backgroundColor: colors.canvas,
    alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: colors.border,
  },
  cardFooter: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.md, paddingVertical: spacing.sm,
    borderTopWidth: 1, borderTopColor: colors.border, backgroundColor: colors.sky50,
    borderBottomLeftRadius: radius.lg, borderBottomRightRadius: radius.lg,
  },
  featuredTop: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    padding: spacing.md, paddingBottom: 0,
  },
  goalTile: {
    borderRadius: radius.md, borderWidth: 1.5, padding: spacing.sm, minHeight: 118,
  },
  goalIcon: { width: 30, height: 30, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
};
