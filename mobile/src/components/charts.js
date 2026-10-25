import React from 'react';
import { View, StyleSheet } from 'react-native';
import Svg, { Circle, Defs, G, LinearGradient as SvgGradient, Line, Path, Polygon, Stop, Text as SvgText } from 'react-native-svg';
import { colors, fonts, spacing } from '../theme';
import { useI18n } from '../i18n';
import { percent, toPersianDigits } from '../core/format';
import { Text } from './ui';

const CATEGORY_ORDER = ['age', 'education', 'language', 'experience', 'funds', 'adaptability'];

/**
 * Six-axis radar of the file's strengths. A soft 100% guide polygon sits behind
 * the achieved polygon so the visual "shape" of the profile is immediate.
 */
export function RadarChart({ radar, size = 248, stroke = colors.teal600 }) {
  const { t, lang } = useI18n();
  const labels = CATEGORY_ORDER.filter((key) => radar && radar[key]);
  const count = labels.length || 6;
  const center = size / 2;
  const radius = size * 0.34;
  const angleFor = (index) => (Math.PI * 2 * index) / count - Math.PI / 2;

  const point = (index, ratio) => {
    const angle = angleFor(index);
    return [center + Math.cos(angle) * radius * ratio, center + Math.sin(angle) * radius * ratio];
  };

  const guidePoints = Array.from({ length: count }, (_, index) => point(index, 1).join(',')).join(' ');
  const midPoints = Array.from({ length: count }, (_, index) => point(index, 0.66).join(',')).join(' ');
  const outerPoints = Array.from({ length: count }, (_, index) => point(index, 0.33).join(',')).join(' ');
  const dataPoints = labels
    .map((key, index) => {
      const value = Math.max(0.06, Math.min(1, (radar[key].percent || 0) / 100));
      return point(index, value).join(',');
    })
    .join(' ');

  return (
    <View style={{ alignItems: 'center' }}>
      <Svg width={size} height={size}>
        <Defs>
          <SvgGradient id="radarFill" x1="0" y1="0" x2="1" y2="1">
            <Stop offset="0" stopColor={colors.teal500} stopOpacity="0.45" />
            <Stop offset="1" stopColor={colors.sky400} stopOpacity="0.35" />
          </SvgGradient>
        </Defs>
        <Polygon points={guidePoints} fill={colors.sky50} stroke={colors.border} strokeWidth={1.2} />
        <Polygon points={midPoints} fill="none" stroke={colors.sky100} strokeWidth={1} />
        <Polygon points={outerPoints} fill="none" stroke={colors.sky100} strokeWidth={1} />
        {Array.from({ length: count }, (_, index) => {
          const [x, y] = point(index, 1);
          return <Line key={`axis-${index}`} x1={center} y1={center} x2={x} y2={y} stroke={colors.border} strokeWidth={1} />;
        })}
        <Polygon points={dataPoints} fill="url(#radarFill)" stroke={stroke} strokeWidth={2.2} strokeLinejoin="round" />
        {labels.map((key, index) => {
          const value = Math.max(0.06, Math.min(1, (radar[key].percent || 0) / 100));
          const [x, y] = point(index, value);
          return <Circle key={`dot-${key}`} cx={x} cy={y} r={3.4} fill={colors.white} stroke={stroke} strokeWidth={1.8} />;
        })}
        {labels.map((key, index) => {
          const [x, y] = point(index, 1.2);
          const label = t(`categories.${key}`);
          return (
            <SvgText
              key={`label-${key}`}
              x={x}
              y={y + 4}
              fill={colors.ink50}
              fontSize={9.5}
              fontFamily={fonts.medium}
              textAnchor="middle"
            >
              {label}
            </SvgText>
          );
        })}
      </Svg>
      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: colors.teal600 }]} />
          <Text variant="micro" color={colors.ink50}>{t('country.criteria')}</Text>
        </View>
        <WebLegend label={percent(100, lang)} />
      </View>
    </View>
  );
}

function WebLegend({ label }) {
  return (
    <View style={styles.legendItem}>
      <View style={[styles.legendDot, { backgroundColor: colors.sky100, borderWidth: 1, borderColor: colors.border }]} />
      <Text variant="micro" color={colors.ink35}>{label}</Text>
    </View>
  );
}

/** Circular confidence dial with a gradient arc. */
export function ChanceDial({ value, size = 168, strokeWidth = 13, label, sublabel }) {
  const { lang, t } = useI18n();
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const ratio = Math.max(0, Math.min(100, value)) / 100;
  const dash = circumference * ratio;
  const center = size / 2;

  const tone = value >= 70 ? colors.success : value >= 45 ? colors.gold : colors.danger;

  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <Svg width={size} height={size} style={StyleSheet.absoluteFill}>
        <Defs>
          <SvgGradient id="dialArc" x1="0" y1="0" x2="1" y2="1">
            <Stop offset="0" stopColor={colors.teal600} />
            <Stop offset="0.55" stopColor={colors.teal500} />
            <Stop offset="1" stopColor={colors.sky400} />
          </SvgGradient>
        </Defs>
        <G rotation={-90} origin={`${center}, ${center}`}>
          <Circle cx={center} cy={center} r={radius} stroke={colors.canvasAlt} strokeWidth={strokeWidth} fill="none" />
          <Circle
            cx={center}
            cy={center}
            r={radius}
            stroke="url(#dialArc)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={`${dash} ${circumference}`}
            fill="none"
          />
        </G>
      </Svg>
      <Text variant="number" style={{ color: colors.teal800, fontSize: size * 0.24, lineHeight: size * 0.3 }}>
        {percent(value, lang, value % 1 === 0 ? 0 : 1)}
      </Text>
      <Text variant="micro" color={tone} style={{ textAlign: 'center' }}>
        {sublabel || t('results.chanceLabel')}
      </Text>
      {label ? <Text variant="micro" color={colors.ink35}>{label}</Text> : null}
    </View>
  );
}

/** Compact horizontal bar used in rankings. */
export function MiniBar({ value, tone }) {
  const ratio = Math.max(0, Math.min(1, value / 100));
  return (
    <View style={styles.miniTrack}>
      <View style={[styles.miniFill, { width: `${ratio * 100}%`, backgroundColor: tone || colors.teal600 }]} />
    </View>
  );
}

/** Readiness arc used inside visa cards. */
export function ScoreArc({ percent: value, size = 54, strokeWidth = 5.5 }) {
  const { lang } = useI18n();
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const dash = (circumference * Math.max(0, Math.min(100, value))) / 100;
  const center = size / 2;
  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <Svg width={size} height={size} style={StyleSheet.absoluteFill}>
        <G rotation={-90} origin={`${center}, ${center}`}>
          <Circle cx={center} cy={center} r={radius} stroke={colors.canvasAlt} strokeWidth={strokeWidth} fill="none" />
          <Circle
            cx={center}
            cy={center}
            r={radius}
            stroke={colors.teal600}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={`${dash} ${circumference}`}
            fill="none"
          />
        </G>
      </Svg>
      <Text variant="micro" style={{ fontFamily: fonts.bold, color: colors.teal700 }}>
        {lang === 'fa' ? toPersianDigits(Math.round(value)) : Math.round(value)}
      </Text>
    </View>
  );
}

/** Tiny sparkline-style gauge for criteria rows. */
export function CriteriaBar({ value, max }) {
  const ratio = max ? Math.max(0, Math.min(1, value / max)) : 0;
  const tone = ratio >= 0.85 ? colors.success : ratio >= 0.5 ? colors.teal500 : ratio > 0 ? colors.gold : colors.ink15;
  return (
    <View style={styles.criteriaTrack}>
      <View style={[styles.criteriaFill, { width: `${ratio * 100}%`, backgroundColor: tone }]} />
    </View>
  );
}

export function DonutBreakdown({ items, size = 132, thickness = 16 }) {
  const total = items.reduce((sum, item) => sum + item.value, 0) || 1;
  let offset = 0;
  const radius = (size - thickness) / 2;
  const circumference = 2 * Math.PI * radius;
  return (
    <Svg width={size} height={size}>
      <G rotation={-90} origin={`${size / 2}, ${size / 2}`}>
        {items.map((item) => {
          const dash = (item.value / total) * circumference;
          const circle = (
            <Circle
              key={item.key}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              stroke={item.color}
              strokeWidth={thickness}
              strokeDasharray={`${dash} ${circumference - dash}`}
              strokeDashoffset={-offset}
              fill="none"
              strokeLinecap="butt"
            />
          );
          offset += dash;
          return circle;
        })}
      </G>
    </Svg>
  );
}

const styles = StyleSheet.create({
  legend: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.xs, justifyContent: 'center' },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  legendDot: { width: 8, height: 8, borderRadius: 4 },
  miniTrack: { height: 7, borderRadius: 4, backgroundColor: colors.canvasAlt, overflow: 'hidden', flex: 1 },
  miniFill: { height: 7, borderRadius: 4 },
  criteriaTrack: { height: 6, borderRadius: 3, backgroundColor: colors.canvasAlt, overflow: 'hidden' },
  criteriaFill: { height: 6, borderRadius: 3 },
});
