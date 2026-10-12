import type { AiReport } from './report.schema.js';

/** Words indicating a pesticide/chemical context. */
const PESTICIDE_WORD =
  /(سم|سموم|حشره[\s‌-]?کش|قارچ[\s‌-]?کش|کنه[\s‌-]?کش|علف[\s‌-]?کش|pesticide|insecticide|fungicide|acaricide|herbicide|spray|oprysk|اسپری|سم‌پاشی|سمپاشی)/i;

/** Quantities / concentrations (e.g. "۲ لیتر", "5 ml", "در ۱۰۰ لیتر آب", "%0.5"). */
const DOSAGE =
  /((\d|[۰-۹])+([.,/٫]\d+)?\s*(cc|ml|میلی[\s‌]?لیتر|لیتر|lit|liter|l\b|گرم|گ\b|کیلوگرم|kg|g\b|درصد|%|گرم در لیتر|cc\/?l))|(در\s*(هر\s*)?(\d|[۰-۹])+\s*لیتر\s*آب)|(\d+\s*(?:ppm|pp m))/i;

/** Dangerous practices that must never be recommended. */
const DANGEROUS_PRACTICE =
  /(مخلوط\s*(کردن|کنید)|ترکیب\s*(سموم|کنید)|دو\s*برابر|چند\s*برابر|بیشتر\s*از\s*توصیه|بدون\s*(ماسک|دستکش|لباس\s*محافظ)|روی\s*میوه\s*سم|mix\s+(the\s+)?(chemicals|pesticides)|double\s+the\s+dose)/i;

export const SAFE_CHEMICAL_ADVICE_FA =
  'در صورت لزوم کنترل شیمیایی، انتخاب سم، زمان‌بندی و دوز مجاز را فقط با نظر کارشناس گیاه‌پزشکی یا مرکز خدمات جهاد کشاورزی تعیین کنید و دستورالعمل روی برچسب سم و فاصله زمانی برداشت را رعایت نمایید.';

/** Returns true when a text contains pesticide dosage or a dangerous practice. */
export function isUnsafeAdvice(text: string): boolean {
  if (DANGEROUS_PRACTICE.test(text)) return true;
  return PESTICIDE_WORD.test(text) && DOSAGE.test(text);
}

/**
 * Applies deterministic safety rules on top of the model output:
 *  - confidence is capped (never 100, lower without enough evidence)
 *  - unsafe chemical advice is replaced by a safe referral sentence
 *  - unusable images always ask for a retake
 */
export function applySafetyRules(report: AiReport): { report: AiReport; flags: string[] } {
  const flags: string[] = [];
  const r: AiReport = structuredClone(report);

  const evidenceCount = r.observedSymptoms.length;
  let cap = 90;
  if (!r.diagnosis.isHealthy && evidenceCount < 2) {
    cap = Math.min(cap, 60);
    flags.push('LOW_EVIDENCE_CAP');
  }
  if (!r.imageQuality.usable) {
    cap = Math.min(cap, 30);
    flags.push('IMAGE_UNUSABLE');
  }
  if (r.diagnosis.confidence > cap) {
    r.diagnosis.confidence = cap;
    flags.push('CONFIDENCE_CAPPED');
  }
  r.alternatives = r.alternatives.map((a) => ({ ...a, confidence: Math.min(a.confidence, cap) }));

  r.recommendedActions = r.recommendedActions.map((action) => {
    if (isUnsafeAdvice(action.text)) {
      flags.push('UNSAFE_ADVICE_REPLACED');
      return { ...action, text: SAFE_CHEMICAL_ADVICE_FA, priority: 'soon' as const };
    }
    return action;
  });

  if (!r.imageQuality.usable && !r.additionalInfoNeeded.some((s) => s.includes('عکس'))) {
    r.additionalInfoNeeded = [
      'عکس واضح‌تر و نزدیک‌تر از نمونه مورد نظر، در نور طبیعی روز',
      ...r.additionalInfoNeeded,
    ].slice(0, 5);
  }
  return { report: r, flags };
}

/** Human-readable label for the confidence value. */
export function confidenceLabelFa(confidence: number): string {
  if (confidence >= 75) return 'اطمینان بالا';
  if (confidence >= 50) return 'اطمینان متوسط';
  return 'اطمینان پایین';
}
