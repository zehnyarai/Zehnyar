import type { KnowledgeKind } from '../knowledge/knowledge.service.js';

/** Bump when the instructions change; stored with every analysis for auditability. */
export const PROMPT_VERSION = '2026.10.1';

export const SAFETY_DISCLAIMER_FA =
  'این گزارش توسط هوش مصنوعی و صرفاً برای راهنمایی اولیه تولید شده است و جایگزین بازدید و تشخیص کارشناس گیاه‌پزشکی یا مرکز خدمات جهاد کشاورزی نیست. پیش از هر اقدام شیمیایی، با کارشناس مشورت کنید.';

export interface PromptContext {
  category: 'leaf' | 'fruit_cluster' | 'trunk' | 'pest' | 'soil';
  season: 'spring' | 'summer' | 'autumn' | 'winter';
  treeAgeYears?: number | null;
  location?: string | null;
  farm?: {
    name: string;
    province: string;
    city: string;
    pistachioVariety?: string | null;
    irrigationMethod?: string | null;
    soilType?: string | null;
    soilNotes?: string | null;
  } | null;
  userNotes?: string | null;
  catalog: Array<{ slug: string; kind: KnowledgeKind; titleFa: string; symptoms: string[] }>;
}

export const CATEGORY_FA: Record<PromptContext['category'], string> = {
  leaf: 'برگ',
  fruit_cluster: 'خوشه میوه',
  trunk: 'تنه یا شاخه اصلی',
  pest: 'آفت (نمای نزدیک)',
  soil: 'خاک',
};

export const SEASON_FA: Record<PromptContext['season'], string> = {
  spring: 'بهار',
  summer: 'تابستان',
  autumn: 'پاییز',
  winter: 'زمستان',
};

/** System instruction: role, scope, safety constraints and output contract. */
export function buildSystemPrompt(): string {
  return `
تو یک متخصص ارشد گیاه‌پزشکی و بوم‌شناسی پسته (Pistacia vera) با دانش علمی به‌روز هستی.
وظیفه: تحلیل تصویر ارسالی کشاورز و تشخیص احتمالی آفت، بیماری، کمبود عناصر غذایی، تنش آبی، تنش گرمایی/سرمایی، شوری خاک یا آسیب محیطی.

قواعد اجباری:
1. فقط بر اساس شواهد قابل مشاهده در تصویر و اطلاعات زمینه استدلال کن. اگر تصویر ناکافی یا تار است، usable=false بگذار و درخواست عکس بهتر بده.
2. هرگز ادعای قطعیت ۱۰۰٪ نکن. confidence عددی بین ۰ تا ۹۰ باشد. بدون حداقل ۲ نشانه مشهود، confidence بالای ۶۰ نده.
3. هیچ‌گاه دستور ساخت، ترکیب یا مخلوط کردن سموم، دوز، غلظت، یا روش مصرف خطرناک نده. در بخش اقدامات فقط اصول مدیریت تلفیقی آفات (IPM)، پایش، بهداشت باغ، آبیاری، تغذیه و "مشورت با کارشناس برای انتخاب و دوز سم" را پیشنهاد بده.
4. جایگزین کارشناس نباش. اگر خطر جدی (مثلاً بیماری گسترده، ریزش کل محصول) محتمل است، صریح به بازدید کارشناس اشاره کن.
5. knowledgeSlug را فقط از فهرست «دانش‌نامه» انتخاب کن؛ اگر موردی مطابق نبود null بگذار. نام مرجع یا DOI تولید نکن.
6. تمام متن‌ها فارسی روان و ساده برای کشاورز باشند. نام علمی را در پرانتز بیاور.
7. خروجی فقط یک شیء JSON معتبر مطابق اسکیمای درخواستی باشد؛ هیچ متن اضافه‌ای خارج از JSON ننویس.
`.trim();
}

export function buildUserPrompt(ctx: PromptContext): string {
  const lines: string[] = [];
  lines.push(`نوع نمونه: ${CATEGORY_FA[ctx.category]}`);
  lines.push(`فصل: ${SEASON_FA[ctx.season]}`);
  if (ctx.treeAgeYears != null) lines.push(`سن تقریبی درخت: ${ctx.treeAgeYears} سال`);
  if (ctx.location) lines.push(`موقعیت: ${ctx.location}`);
  if (ctx.farm) {
    lines.push(`باغ: ${ctx.farm.name} – ${ctx.farm.province}، ${ctx.farm.city}`);
    if (ctx.farm.pistachioVariety) lines.push(`رقم پسته: ${ctx.farm.pistachioVariety}`);
    if (ctx.farm.irrigationMethod) lines.push(`روش آبیاری: ${ctx.farm.irrigationMethod}`);
    if (ctx.farm.soilType) lines.push(`نوع خاک: ${ctx.farm.soilType}`);
    if (ctx.farm.soilNotes) lines.push(`یادداشت خاک: ${ctx.farm.soilNotes}`);
  }
  if (ctx.userNotes) lines.push(`یادداشت کشاورز: ${ctx.userNotes}`);

  const catalog = ctx.catalog
    .map((c) => `- ${c.slug} (${c.kind}): ${c.titleFa}؛ نشانه‌ها: ${c.symptoms.join('، ')}`)
    .join('\n');

  return `
اطلاعات زمینه:
${lines.join('\n')}

دانش‌نامه (فقط از این slugها استفاده کن):
${catalog}

تصویر را تحلیل کن و گزارش JSON را برگردان. اگر تصویر برای تشخیص قطعی کافی نیست، در additionalInfoNeeded دقیقاً بگو چه عکسی لازم است (مثلاً پشت برگ، نمای نزدیک، تنه با زخم، خاک از عمق ۳۰ سانتی‌متری).
`.trim();
}
