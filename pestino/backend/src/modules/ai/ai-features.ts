import { SAFETY_DISCLAIMER_FA } from './prompt.js';

/**
 * Catalogue of AI features. Feature keys are the only values the admin panel may configure.
 * `editablePrompt` = the admin may replace the system prompt. Safety rules are always appended in code,
 * so a prompt edit can never remove them.
 */
export interface AiFeatureDefinition {
  key: 'image_analysis' | 'farm_form_help' | 'report_explain';
  titleFa: string;
  descriptionFa: string;
  kind: 'vision' | 'text';
  editablePrompt: boolean;
  defaults: { maxOutputTokens: number; temperature: number; dailyLimitFree: number; dailyLimitPremium: number };
}

export const AI_FEATURES: Record<AiFeatureDefinition['key'], AiFeatureDefinition> = {
  image_analysis: {
    key: 'image_analysis',
    titleFa: 'تحلیل تصویر',
    descriptionFa: 'تشخیص آفت، بیماری و کمبود عناصر از روی عکس. سهمیه ماهانه پلن جداگانه اعمال می‌شود.',
    kind: 'vision',
    editablePrompt: false,
    defaults: { maxOutputTokens: 4096, temperature: 0.2, dailyLimitFree: 1000, dailyLimitPremium: 1000 },
  },
  farm_form_help: {
    key: 'farm_form_help',
    titleFa: 'کمک هوشمند فرم مزرعه',
    descriptionFa: 'راهنمای کوتاه و اعتبارسنجی یک فیلد فرم مزرعه (رقم، سن درخت، آبیاری، خاک).',
    kind: 'text',
    editablePrompt: true,
    defaults: { maxOutputTokens: 512, temperature: 0.2, dailyLimitFree: 5, dailyLimitPremium: 100 },
  },
  report_explain: {
    key: 'report_explain',
    titleFa: 'توضیح ساده گزارش',
    descriptionFa: 'بازنویسی بخش‌های فنی گزارش به فارسی ساده برای کشاورز.',
    kind: 'text',
    editablePrompt: true,
    defaults: { maxOutputTokens: 768, temperature: 0.2, dailyLimitFree: 3, dailyLimitPremium: 60 },
  },
};

export type AiFeatureKey = AiFeatureDefinition['key'];

export const AI_FEATURE_KEYS = Object.keys(AI_FEATURES) as AiFeatureDefinition['key'][];

/** Non-removable rules appended to every text feature's system prompt. */
export const TEXT_SAFETY_RULES_FA = `
قوانین ایمنی غیرقابل تغییر:
- هرگز دستور ساخت، ترکیب، مخلوط کردن، دوز، غلظت یا روش مصرف سم ننویس.
- اگر سؤال درباره سم یا دوز است، فقط بگو انتخاب و دوز سم باید با نظر کارشناس گیاه‌پزشکی یا مرکز خدمات جهاد کشاورزی و بر اساس برچسب سم تعیین شود.
- هرگز ادعای قطعیت ۱۰۰٪ نکن. از عبارت‌هایی مانند «احتمالاً» و «بررسی شود» استفاده کن.
- جایگزین کارشناس نباش. منبع علمی یا DOI نساز.
- پاسخ فارسی، کوتاه و ساده باشد.
- ${SAFETY_DISCLAIMER_FA}
`.trim();

export const DEFAULT_TEXT_PROMPTS: Record<'farm_form_help' | 'report_explain', string> = {
  farm_form_help:
    'تو دستیار فرم مزرعه‌ی پسته هستی. کاربر یک فیلد را وارد کرده است. اگر مقدار با زمینه‌ی ارسالی سازگار نیست یا ناقص است، یک هشدار کوتاه بده و یک پیشنهاد کاربردی ارائه کن.',
  report_explain:
    'تو مترجم گزارش‌های فنی گیاه‌پزشکی پسته به فارسی ساده هستی. متن فنی ارسالی را برای یک کشاورز بی‌تجربه در حداکثر ۵ جمله ساده بازنویسی کن و اصطلاح علمی را در پرانتز بیاور.',
};

export function isAiFeatureKey(value: string): value is AiFeatureDefinition['key'] {
  return (AI_FEATURE_KEYS as string[]).includes(value);
}
