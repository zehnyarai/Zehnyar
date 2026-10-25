import React, { useRef } from 'react';
import {
  ActivityIndicator,
  Animated,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text as RawText,
  TextInput,
  View,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, fonts, gradients, hitslop, radius, shadow, spacing, type } from '../theme';
import { useDirection, useI18n } from '../i18n';
import { percent } from '../core/format';

export function Screen({ children, style, edges = true, bg = colors.canvas }) {
  return <View style={[styles.screen, { backgroundColor: bg }, style]}>{children}</View>;
}

export function ScrollScreen({ children, contentStyle, ...rest }) {
  return (
    <ScrollView
      showsVerticalScrollIndicator={false}
      contentContainerStyle={[styles.scrollContent, contentStyle]}
      {...rest}
    >
      {children}
    </ScrollView>
  );
}

export function Text({ children, style, variant = 'body', color, align, numberOfLines }) {
  return (
    <RawText
      style={[type[variant] || type.body, color ? { color } : null, align ? { textAlign: align } : null, style]}
      numberOfLines={numberOfLines}
    >
      {children}
    </RawText>
  );
}

export function Card({ children, style, padded = true, level = 1 }) {
  return <View style={[styles.card, shadow(level), padded && { padding: spacing.lg }, style]}>{children}</View>;
}

export function PressableScale({ children, onPress, style, disabled, accessibilityLabel }) {
  const scale = useRef(new Animated.Value(1)).current;
  const animate = (to) => Animated.spring(scale, { toValue: to, useNativeDriver: true, speed: 40, bounciness: 4 }).start();
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      disabled={disabled}
      onPressIn={() => !disabled && animate(0.97)}
      onPressOut={() => animate(1)}
      onPress={onPress}
      hitSlop={hitslop}
    >
      <Animated.View style={[{ transform: [{ scale }] }, disabled && { opacity: 0.45 }, style]}>{children}</Animated.View>
    </Pressable>
  );
}

export function Button({ label, onPress, variant = 'primary', icon, style, disabled, loading, size = 'md' }) {
  const height = size === 'sm' ? 42 : 54;
  const content = (
    <View style={[styles.buttonInner, { height }, size === 'sm' && { paddingHorizontal: spacing.md }]}>
      {loading ? (
        <ActivityIndicator color={variant === 'primary' ? colors.white : colors.teal700} />
      ) : (
        <>
          {icon ? <Ionicons name={icon} size={18} color={variant === 'primary' ? colors.white : colors.teal700} /> : null}
          <Text
            variant="h3"
            style={[
              styles.buttonLabel,
              variant === 'primary' ? { color: colors.white } : { color: colors.teal700 },
            ]}
          >
            {label}
          </Text>
        </>
      )}
    </View>
  );
  return (
    <PressableScale onPress={onPress} disabled={disabled || loading} style={style}>
      {variant === 'light' ? (
        <View style={[styles.buttonLight, { height, borderRadius: radius.lg }, shadow(1)]}>{content}</View>
      ) : variant === 'primary' ? (
        <LinearGradient
          colors={gradients.hero}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={[styles.button, shadow(2), { borderRadius: radius.lg }]}
        >
          {content}
        </LinearGradient>
      ) : variant === 'ghost' ? (
        <View style={[styles.buttonGhost, { height, borderRadius: radius.lg }]}>{content}</View>
      ) : (
        <View style={[styles.buttonOutline, { height, borderRadius: radius.lg }, shadow(0)]}>{content}</View>
      )}
    </PressableScale>
  );
}

export function IconButton({ icon, onPress, color = colors.teal700, bg = colors.surface, size = 42, style }) {
  return (
    <PressableScale onPress={onPress} style={style}>
      <View style={[styles.iconButton, { width: size, height: size, backgroundColor: bg }]}>
        <Ionicons name={icon} size={size * 0.45} color={color} />
      </View>
    </PressableScale>
  );
}

export function Chip({ label, active, onPress, icon, tone = 'teal' }) {
  const palette = active
    ? { bg: colors.teal700, fg: colors.white, border: colors.teal700 }
    : { bg: colors.surface, fg: colors.ink70, border: colors.border };
  return (
    <PressableScale onPress={onPress} style={{ alignSelf: 'flex-start' }}>
      <View style={[styles.chip, { backgroundColor: palette.bg, borderColor: palette.border }]}>
        {icon ? <Ionicons name={icon} size={13} color={palette.fg} /> : null}
        <Text variant="micro" style={{ color: palette.fg, fontFamily: fonts.semibold }}>
          {label}
        </Text>
      </View>
    </PressableScale>
  );
}

export function Pill({ label, tone = 'neutral', icon }) {
  const tones = {
    neutral: { bg: colors.canvasAlt, fg: colors.ink70 },
    teal: { bg: colors.teal100, fg: colors.teal700 },
    sky: { bg: colors.sky100, fg: colors.sky700 },
    gold: { bg: colors.goldSoft, fg: '#7A5F19' },
    success: { bg: colors.successSoft, fg: colors.success },
    warn: { bg: colors.warnSoft, fg: colors.warn },
    danger: { bg: colors.dangerSoft, fg: colors.danger },
  };
  const palette = tones[tone] || tones.neutral;
  return (
    <View style={[styles.pill, { backgroundColor: palette.bg }]}>
      {icon ? <Ionicons name={icon} size={11} color={palette.fg} /> : null}
      <Text variant="micro" style={{ color: palette.fg }}>{label}</Text>
    </View>
  );
}

export function SectionTitle({ title, subtitle, actionLabel, onAction, style }) {
  const dir = useDirection();
  return (
    <View style={[{ flexDirection: dir.row, alignItems: 'flex-end', justifyContent: 'space-between' }, style]}>
      <View style={{ flex: 1 }}>
        <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.xs }}>
          <View style={styles.accentBar} />
          <Text variant="h2" color={colors.ink}>{title}</Text>
        </View>
        {subtitle ? (
          <Text variant="small" color={colors.ink50} style={{ marginTop: 2, textAlign: dir.text }}>
            {subtitle}
          </Text>
        ) : null}
      </View>
      {actionLabel && onAction ? (
        <Pressable onPress={onAction} hitSlop={hitslop}>
          <Text variant="micro" style={{ color: colors.teal700, fontFamily: fonts.semibold }}>{actionLabel}</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

export function ProgressBar({ value, max = 100, height = 8, barColors = [colors.teal500, colors.sky600], track = colors.canvasAlt }) {
  const ratio = Math.max(0, Math.min(1, max ? value / max : 0));
  return (
    <View style={{ height, borderRadius: height, backgroundColor: track, overflow: 'hidden' }}>
      <LinearGradient
        colors={barColors}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 0 }}
        style={{ height, width: `${ratio * 100}%`, borderRadius: height }}
      />
    </View>
  );
}

export function StatTile({ value, label, tone = 'teal', icon }) {
  const palette = tone === 'gold' ? { bg: colors.goldSoft, fg: '#7A5F19' } : { bg: colors.teal100, fg: colors.teal700 };
  return (
    <View style={[styles.statTile]}>
      {icon ? <Ionicons name={icon} size={16} color={palette.fg} style={{ marginBottom: 4 }} /> : null}
      <Text variant="h2" style={{ color: palette.fg }}>{value}</Text>
      <Text variant="micro" color={colors.ink50} style={{ textAlign: 'center' }}>{label}</Text>
    </View>
  );
}

export function TrustBadge({ label, value }) {
  const dir = useDirection();
  return (
    <View style={[styles.trustBadge, { flexDirection: dir.row }]}>
      <Ionicons name="shield-checkmark" size={13} color={colors.gold} />
      <Text variant="micro" style={{ color: '#6B5416' }}>{label}</Text>
      <View style={styles.trustDot} />
      <Text variant="micro" style={{ color: '#6B5416', fontFamily: fonts.bold }}>{value}</Text>
    </View>
  );
}

export function Divider({ style }) {
  return <View style={[{ height: 1, backgroundColor: colors.border }, style]} />;
}

export function EmptyState({ icon = 'compass-outline', title, body, actionLabel, onAction }) {
  return (
    <View style={styles.empty}>
      <View style={styles.emptyIcon}>
        <Ionicons name={icon} size={30} color={colors.teal600} />
      </View>
      <Text variant="h3" color={colors.ink} style={{ textAlign: 'center', marginTop: spacing.md }}>{title}</Text>
      <Text variant="small" color={colors.ink50} style={{ textAlign: 'center', marginTop: spacing.xs }}>{body}</Text>
      {actionLabel ? (
        <Button label={actionLabel} onPress={onAction} style={{ marginTop: spacing.lg, alignSelf: 'stretch' }} />
      ) : null}
    </View>
  );
}

export function OptionCard({ label, description, icon, active, onPress, badge }) {
  const dir = useDirection();
  return (
    <PressableScale onPress={onPress} style={{ flex: 1 }}>
      <View
        style={[
          styles.optionCard,
          { borderColor: active ? colors.teal600 : colors.border, backgroundColor: active ? colors.teal100 : colors.surface },
        ]}
      >
        <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.sm }}>
          <View style={[styles.optionIcon, { backgroundColor: active ? colors.teal700 : colors.canvasAlt }]}>
            <Ionicons name={icon} size={17} color={active ? colors.white : colors.teal700} />
          </View>
          <Text variant="h3" style={{ color: active ? colors.teal800 : colors.ink, flex: 1 }} numberOfLines={2}>
            {label}
          </Text>
        </View>
        {description ? (
          <Text variant="small" color={colors.ink50} style={{ marginTop: spacing.xs, textAlign: dir.text }}>
            {description}
          </Text>
        ) : null}
        {badge ? <View style={{ marginTop: spacing.xs }}>{badge}</View> : null}
      </View>
    </PressableScale>
  );
}

export function ToggleRow({ label, hint, value, onValueChange, icon }) {
  const dir = useDirection();
  return (
    <Pressable onPress={() => onValueChange(!value)} style={[styles.toggleRow, { flexDirection: dir.row }]}>
      <View style={{ flex: 1 }}>
        <View style={{ flexDirection: dir.row, alignItems: 'center', gap: spacing.xs }}>
          {icon ? <Ionicons name={icon} size={15} color={colors.teal600} /> : null}
          <Text variant="bodyStrong" color={colors.ink} style={{ flex: 1, textAlign: dir.text }}>{label}</Text>
        </View>
        {hint ? <Text variant="micro" color={colors.ink35} style={{ marginTop: 2, textAlign: dir.text }}>{hint}</Text> : null}
      </View>
      <View style={[styles.switch, { backgroundColor: value ? colors.teal600 : colors.ink15 }]}>
        <View style={[styles.switchKnob, value ? { alignSelf: 'flex-end' } : { alignSelf: 'flex-start' }]} />
      </View>
    </Pressable>
  );
}

export function Stepper({ value, onChange, min = 0, max = 80, step = 1, suffix, label }) {
  const dir = useDirection();
  const clamp = (next) => Math.max(min, Math.min(max, next));
  return (
    <View style={{ flexDirection: dir.row, alignItems: 'center', justifyContent: 'space-between', gap: spacing.sm }}>
      <View style={{ flex: 1 }}>
        {label ? <Text variant="bodyStrong" color={colors.ink} style={{ textAlign: dir.text }}>{label}</Text> : null}
        <Text variant="h2" color={colors.teal700} style={{ textAlign: dir.text }}>
          {value}
          {suffix ? <Text variant="small" color={colors.ink50}>{` ${suffix}`}</Text> : null}
        </Text>
      </View>
      <View style={{ flexDirection: 'row', gap: spacing.xs }}>
        <IconButton icon="remove" size={40} onPress={() => onChange(clamp(Number(value) - step))} bg={colors.canvasAlt} />
        <IconButton icon="add" size={40} onPress={() => onChange(clamp(Number(value) + step))} bg={colors.teal100} />
      </View>
    </View>
  );
}

export function MoneyField({ label, hint, value, onChangeText, currencyLabel, placeholder }) {
  const dir = useDirection();
  return (
    <View style={{ gap: spacing.xs }}>
      {label ? <Text variant="bodyStrong" color={colors.ink} style={{ textAlign: dir.text }}>{label}</Text> : null}
      <View style={[styles.inputRow, { flexDirection: dir.row }]}>
        <TextInput
          value={value}
          onChangeText={onChangeText}
          keyboardType="numeric"
          placeholder={placeholder}
          placeholderTextColor={colors.ink35}
          style={[styles.input, { textAlign: dir.text, writingDirection: dir.writing }]}
        />
        <View style={styles.currencyTag}>
          <Text variant="micro" color={colors.teal700}>{currencyLabel}</Text>
        </View>
      </View>
      {hint ? <Text variant="micro" color={colors.ink35} style={{ textAlign: dir.text }}>{hint}</Text> : null}
    </View>
  );
}

export function Field({ label, hint, value, onChangeText, placeholder, keyboardType = 'default', suffix }) {
  const dir = useDirection();
  return (
    <View style={{ gap: spacing.xs }}>
      {label ? <Text variant="bodyStrong" color={colors.ink} style={{ textAlign: dir.text }}>{label}</Text> : null}
      <View style={[styles.inputRow, { flexDirection: dir.row }]}>
        <TextInput
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={colors.ink35}
          keyboardType={keyboardType}
          style={[styles.input, { textAlign: dir.text, writingDirection: dir.writing }]}
        />
        {suffix ? <Text variant="small" color={colors.ink50}>{suffix}</Text> : null}
      </View>
      {hint ? <Text variant="micro" color={colors.ink35} style={{ textAlign: dir.text }}>{hint}</Text> : null}
    </View>
  );
}

export function Sheet({ visible, onClose, title, children, height = '78%' }) {
  const dir = useDirection();
  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.sheetBackdrop}>
        <Pressable style={{ flex: 1 }} onPress={onClose} />
        <View style={[styles.sheet, { height }]}>
          <View style={styles.sheetHandle} />
          <View style={[styles.sheetHeader, { flexDirection: dir.row }]}>
            <Text variant="h2" color={colors.ink} style={{ flex: 1, textAlign: dir.text }}>{title}</Text>
            <IconButton icon="close" onPress={onClose} bg={colors.canvasAlt} size={36} />
          </View>
          <View style={{ flex: 1 }}>{children}</View>
        </View>
      </View>
    </Modal>
  );
}

export function KeyValue({ label, value, tone }) {
  const dir = useDirection();
  return (
    <View style={{ flexDirection: dir.row, alignItems: 'flex-start', justifyContent: 'space-between', gap: spacing.md, paddingVertical: 7 }}>
      <Text variant="small" color={colors.ink50} style={{ flexShrink: 1, textAlign: dir.text }}>{label}</Text>
      <Text variant="small" color={tone || colors.ink} style={{ fontFamily: fonts.semibold, flexShrink: 1, textAlign: dir.textOpposite }}>
        {value}
      </Text>
    </View>
  );
}

export function ScoreChip({ chance, label }) {
  const { lang } = useI18n();
  const tone = chance >= 70 ? colors.success : chance >= 45 ? colors.warn : colors.danger;
  const bg = chance >= 70 ? colors.successSoft : chance >= 45 ? colors.warnSoft : colors.dangerSoft;
  return (
    <View style={[styles.scoreChip, { backgroundColor: bg }]}>
      <Text variant="h3" style={{ color: tone }}>{percent(chance, lang)}</Text>
      {label ? <Text variant="micro" color={colors.ink50}>{label}</Text> : null}
    </View>
  );
}

export function Loading({ label }) {
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.sm }}>
      <ActivityIndicator color={colors.teal600} size="large" />
      {label ? <Text variant="small" color={colors.ink50}>{label}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  scrollContent: { paddingBottom: 132 },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  button: { alignItems: 'center', justifyContent: 'center' },
  buttonInner: {
    paddingHorizontal: spacing.xl,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
  },
  buttonLabel: { color: colors.white },
  buttonOutline: {
    borderWidth: 1.5,
    borderColor: colors.teal600,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonGhost: { backgroundColor: 'transparent', alignItems: 'center', justifyContent: 'center' },
  buttonLight: { backgroundColor: colors.white, alignItems: 'center', justifyContent: 'center' },
  iconButton: {
    borderRadius: radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: spacing.sm,
    paddingVertical: 7,
    borderRadius: radius.pill,
    borderWidth: 1,
  },
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 9,
    paddingVertical: 4,
    borderRadius: radius.pill,
    alignSelf: 'flex-start',
  },
  accentBar: { width: 4, height: 18, borderRadius: 2, backgroundColor: colors.teal600 },
  statTile: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.xs,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  trustBadge: {
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: spacing.sm,
    paddingVertical: 6,
    borderRadius: radius.pill,
    backgroundColor: colors.goldSoft,
    alignSelf: 'flex-start',
  },
  trustDot: { width: 3, height: 3, borderRadius: 2, backgroundColor: '#B79A48' },
  empty: { alignItems: 'center', padding: spacing.xl },
  emptyIcon: {
    width: 64, height: 64, borderRadius: 32, alignItems: 'center', justifyContent: 'center',
    backgroundColor: colors.teal100,
  },
  optionCard: {
    borderRadius: radius.md,
    borderWidth: 1.5,
    padding: spacing.sm,
    minHeight: 96,
  },
  optionIcon: { width: 32, height: 32, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  toggleRow: {
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.sm,
  },
  switch: { width: 46, height: 27, borderRadius: 999, padding: 3, justifyContent: 'center' },
  switchKnob: { width: 21, height: 21, borderRadius: 999, backgroundColor: colors.white },
  inputRow: {
    alignItems: 'center',
    gap: spacing.xs,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    height: 52,
  },
  input: { flex: 1, fontFamily: fonts.medium, fontSize: 15, color: colors.ink, paddingVertical: 0 },
  currencyTag: { backgroundColor: colors.teal100, paddingHorizontal: 8, paddingVertical: 3, borderRadius: radius.sm },
  sheetBackdrop: { flex: 1, backgroundColor: colors.overlay, justifyContent: 'flex-end' },
  sheet: {
    backgroundColor: colors.canvas,
    borderTopLeftRadius: radius.xxl,
    borderTopRightRadius: radius.xxl,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.lg,
  },
  sheetHandle: {
    width: 42, height: 4, borderRadius: 2, backgroundColor: colors.ink15,
    alignSelf: 'center', marginTop: spacing.sm, marginBottom: spacing.xs,
  },
  sheetHeader: { alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.sm },
  scoreChip: { paddingHorizontal: spacing.sm, paddingVertical: 6, borderRadius: radius.md, alignItems: 'center' },
});

export const uiStyles = styles;
