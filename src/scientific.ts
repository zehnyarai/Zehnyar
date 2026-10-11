/** Educational decision support, NOT a diagnostic model or a fertilizer prescription. */
export type LabKind = 'soil' | 'water'
export type LabValues = Record<string, number>
export interface LabField {
  key: string
  label: string
  unit: string
  max: number
}
export const SOIL_FIELDS: LabField[] = [
  { key: 'ph', label: 'pH', unit: '', max: 14 },
  { key: 'ec', label: 'EC', unit: 'dS/m', max: 100 },
  { key: 'nitrogen', label: 'نیتروژن', unit: 'mg/kg (ppm)', max: 100000 },
  { key: 'phosphorus', label: 'فسفر', unit: 'mg/kg (ppm)', max: 100000 },
  { key: 'potassium', label: 'پتاسیم', unit: 'mg/kg (ppm)', max: 100000 },
  { key: 'calcium', label: 'کلسیم', unit: 'mg/kg (ppm)', max: 100000 },
  { key: 'magnesium', label: 'منیزیم', unit: 'mg/kg (ppm)', max: 100000 },
  { key: 'iron', label: 'آهن', unit: 'mg/kg (ppm)', max: 100000 },
  { key: 'zinc', label: 'روی', unit: 'mg/kg (ppm)', max: 100000 },
  { key: 'boron', label: 'بُر', unit: 'mg/kg (ppm)', max: 100000 },
  { key: 'organic', label: 'ماده آلی', unit: '%', max: 100 },
  { key: 'sar', label: 'SAR گزارش آزمایشگاه', unit: '', max: 1000 },
]
export const WATER_FIELDS: LabField[] = [
  { key: 'ph', label: 'pH', unit: '', max: 14 },
  { key: 'ec', label: 'EC', unit: 'dS/m', max: 100 },
  { key: 'tds', label: 'مواد جامد محلول (TDS)', unit: 'mg/L', max: 100000 },
  { key: 'sodium', label: 'سدیم', unit: 'mg/L', max: 100000 },
  { key: 'calcium', label: 'کلسیم', unit: 'mg/L', max: 100000 },
  { key: 'magnesium', label: 'منیزیم', unit: 'mg/L', max: 100000 },
  { key: 'chloride', label: 'کلراید', unit: 'mg/L', max: 100000 },
  { key: 'boron', label: 'بُر', unit: 'mg/L', max: 100000 },
  { key: 'bicarbonate', label: 'بی‌کربنات', unit: 'mg/L', max: 100000 },
  { key: 'carbonate', label: 'کربنات', unit: 'mg/L', max: 100000 },
  { key: 'nitrate', label: 'نیترات (NO₃)', unit: 'mg/L', max: 100000 },
  { key: 'sar', label: 'SAR گزارش آزمایشگاه', unit: '', max: 1000 },
]
export const LAB_SOURCES = [
  {
    title: 'FAO — Water Quality for Agriculture',
    url: 'https://www.fao.org/4/t0234e/t0234e00.htm',
    scope: 'چارچوب عمومی کیفیت آب آبیاری؛ حدود، آستانه اختصاصی پسته در ایران نیستند.',
  },
  {
    title: 'UC Davis — Pistachio',
    url: 'https://fruitsandnuts.ucdavis.edu/pistachio',
    scope: 'مرجع آموزشی پسته؛ تطبیق با رقم، پایه و اقلیم ایران ضروری است.',
  },
]
export interface LabFinding {
  title: string
  text: string
  tone: 'neutral' | 'caution'
  basis: string
}
export interface LabInterpretation {
  findings: LabFinding[]
  calculations: { label: string; value: number; formula: string }[]
  next: string[]
  limitations: string[]
}
export function parseLabValues(kind: LabKind, inputs: Record<string, string>): LabValues {
  const values: LabValues = {}
  for (const field of kind === 'soil' ? SOIL_FIELDS : WATER_FIELDS) {
    const raw = inputs[field.key]?.trim()
    if (!raw) continue // Missing is not zero.
    const value = Number(raw)
    if (!Number.isFinite(value) || value < 0 || value > field.max)
      throw new Error(`مقدار ${field.label} معتبر نیست؛ واحد آزمایشگاه را بررسی کنید.`)
    values[field.key] = value
  }
  if (!Object.keys(values).length) throw new Error('حداقل یک مقدار واقعی از برگه آزمایش وارد کنید.')
  return values
}
export function interpretLab(kind: LabKind, values: LabValues, method: string): LabInterpretation {
  for (const [key, value] of Object.entries(values)) {
    const field = (kind === 'soil' ? SOIL_FIELDS : WATER_FIELDS).find((f) => f.key === key)
    if (!field || !Number.isFinite(value) || value < 0 || value > field.max)
      throw new Error('مقادیر یا واحدهای آزمایش معتبر نیستند.')
  }
  const findings: LabFinding[] = [],
    calculations: LabInterpretation['calculations'] = []
  if (values.ec !== undefined) {
    if (kind === 'water')
      findings.push({
        title: 'شوری آب آبیاری',
        tone: values.ec >= 0.7 ? 'caution' : 'neutral',
        text:
          values.ec < 0.7
            ? 'در چارچوب عمومی FAO، محدودیت شوری آب معمولاً کم است؛ این عدد به‌تنهایی سلامت خاک یا ایمنی آبیاری را ثابت نمی‌کند.'
            : values.ec <= 3
              ? 'در چارچوب عمومی FAO، محدودیت شوری خفیف تا متوسط است. بافت خاک، زهکشی، پایه، بارندگی و شوری خاک هم بررسی شوند.'
              : 'در چارچوب عمومی FAO، محدودیت شوری شدید است. برای ارزیابی پسته، آب و خاک را با کارشناس محلی بررسی کنید؛ آبشویی بدون زهکشی و محاسبه توصیه نمی‌شود.',
        basis: 'FAO Table 1 — ECw: <0.7 / 0.7–3 / >3 dS/m؛ عمومی، نه آستانه اختصاصی پسته.',
      })
    else if (method === 'saturated')
      findings.push({
        title: 'شوری عصاره اشباع خاک (ECe)',
        tone: values.ec >= 4 ? 'caution' : 'neutral',
        text:
          values.ec >= 4
            ? 'ECe واردشده نیازمند بررسی شوری پروفیل ریشه و زهکشی است. تحمل پسته به پایه، سن، مرحله رشد و یون‌ها وابسته است؛ از این عدد نمی‌توان درصد افت محصول را تعیین کرد.'
            : 'ECe ثبت شد؛ پایین‌بودن آن، کمبود غذایی یا نبود تنش در تمام عمق ریشه را ثابت نمی‌کند.',
        basis: 'عدد ۴ dS/m معیار عمومی طبقه‌بندی خاک شور است؛ آستانه افت محصول پسته نیست.',
      })
    else
      findings.push({
        title: 'روش سنجش EC مشخص نیست',
        tone: 'caution',
        text: 'EC عصاره ۱:۵ یا ۱:۲٫۵ را نباید مستقیماً با ECe مقایسه کرد. روش و دمای مرجع را از آزمایشگاه بگیرید؛ فعلاً طبقه‌بندی شوری انجام نشده است.',
        basis: 'تفاوت روش استخراج؛ تبدیل ثابت و عمومی معتبر نیست.',
      })
  }
  if (values.ph !== undefined)
    findings.push({
      title: 'واکنش خاک / آب',
      tone: values.ph < 6.5 || values.ph > 8.5 ? 'caution' : 'neutral',
      text:
        kind === 'water'
          ? 'pH آب به‌تنهایی شاخص شوری یا نیاز به اسید نیست. قلیائیت، بی‌کربنات، سازگاری تجهیزات و بررسی تخصصی لازم‌اند.'
          : 'pH فقط بخشی از ارزیابی است. در pH بالا، قابلیت جذب برخی عناصر ممکن است کاهش یابد، اما کمبود یا مقدار کود با pH تنها تعیین نمی‌شود.',
      basis: 'تفسیر آموزشی؛ بدون تجویز اصلاح‌کننده، اسید، گچ یا کود.',
    })
  if (
    kind === 'water' &&
    values.sodium !== undefined &&
    values.calcium !== undefined &&
    values.magnesium !== undefined
  ) {
    const ca = values.calcium / 20.039,
      mg = values.magnesium / 12.1525,
      na = values.sodium / 22.9898
    if (ca + mg > 0) {
      calculations.push({
        label: 'SAR محاسبه‌شده',
        value: na / Math.sqrt((ca + mg) / 2),
        formula: 'Na / √((Ca + Mg) / 2)؛ پس از تبدیل mg/L به meq/L',
      })
      findings.push({
        title: 'سدیمی‌شدن و نفوذپذیری',
        tone: 'caution',
        text: 'SAR باید همراه EC آب، بافت و کلسیم خاک تفسیر شود. عدد SAR تنها برای تعیین نیاز به گچ یا مناسب‌بودن آب کافی نیست.',
        basis: 'FAO — اثر ترکیبی ECw و SAR بر نفوذپذیری.',
      })
      if (values.bicarbonate !== undefined && values.carbonate !== undefined)
        calculations.push({
          label: 'RSC محاسبه‌شده',
          value: values.bicarbonate / 61.0168 + values.carbonate / 30.0045 - ca - mg,
          formula: '(HCO₃ + CO₃) − (Ca + Mg)، بر حسب meq/L؛ مقدار منفی معتبر است.',
        })
    } else
      findings.push({
        title: 'SAR قابل محاسبه نیست',
        tone: 'caution',
        text: 'جمع کلسیم و منیزیم صفر است. واحد و حد تشخیص آزمایشگاه را بررسی کنید.',
        basis: 'مخرج صفر؛ عدد بی‌نهایت یا برآورد ساختگی تولید نشده.',
      })
  }
  if (
    kind === 'soil' &&
    ['nitrogen', 'phosphorus', 'potassium', 'iron', 'zinc', 'boron', 'calcium', 'magnesium'].some(
      (k) => values[k] !== undefined
    )
  )
    findings.push({
      title: 'نیاز غذایی و کمبود عناصر',
      tone: 'neutral',
      text: 'مقادیر عناصر ثبت شدند؛ بدون روش استخراج، زمان و عمق نمونه‌برداری و آزمایش برگ، برچسب کمبود یا برنامه کوددهی تولید نمی‌شود. نیتروژن کل با نیتروژن نیتراتی یکسان نیست.',
      basis: 'Olsen / DTPA / سایر روش‌ها باید مشخص باشند؛ واحد mg/kg با mg/L متفاوت است.',
    })
  if (
    kind === 'water' &&
    ['boron', 'chloride', 'tds', 'nitrate'].some((k) => values[k] !== undefined)
  )
    findings.push({
      title: 'یون‌ها و سمیت اختصاصی',
      tone: 'neutral',
      text: 'اعداد ثبت شدند؛ اثر بُر، کلراید و سدیم به پایه، شیوه آبیاری و تجمع در خاک و برگ وابسته است. مقدار کود یا کاهش عملکرد از این اعداد به‌تنهایی محاسبه نمی‌شود.',
      basis: 'FAO — specific ion toxicity؛ نیاز به تفسیر محلی.',
    })
  if (!findings.length)
    findings.push({
      title: 'مقادیر ثبت شدند',
      tone: 'neutral',
      text: 'برای این داده‌ها، بدون اطلاعات تکمیلی تفسیر عددی قابل اتکا ارائه نمی‌شود.',
      basis: 'داده ناکافی به جای نتیجه ساختگی.',
    })
  return {
    findings,
    calculations,
    next: [
      'روش استخراج، واحد و تاریخ نمونه‌برداری را با برگه اصلی کنترل کنید.',
      'نمونه‌های نماینده از درخت سالم و علامت‌دار و عمق‌های مناسب ریشه با نظر آزمایشگاه تهیه کنید.',
      'آزمایش برگِ استاندارد فصل، سابقه آبیاری و رقم/پایه را برای برنامه تغذیه کنار این نتایج قرار دهید.',
    ],
    limitations: [
      'این خروجی تفسیر آموزشی مقادیر واردشده است، نه تحلیل عکس، تشخیص قطعی یا نسخه کود و سم.',
      'داده‌های واردشده و محاسبات آزمایشگاه مستقلاً تأیید نشده‌اند؛ محتوای آموزشی هنوز تأیید متخصص محلی ندارد.',
    ],
  }
}
export const SYMPTOMS = [
  {
    id: 'yellowing',
    label: 'زردی یا رنگ‌پریدگی برگ',
    guides: ['nutrition', 'salinity', 'irrigation'],
  },
  { id: 'sticky', label: 'چسبندگی، عسلک یا حشره روی برگ', guides: ['psylla', 'scale', 'mites'] },
  { id: 'spots', label: 'لکه، سوختگی یا ریزش برگ', guides: ['alternaria', 'salinity', 'frost'] },
  {
    id: 'wilting',
    label: 'پژمردگی یا خشکیدگی',
    guides: ['verticillium', 'phytophthora', 'irrigation'],
  },
  {
    id: 'fruit',
    label: 'آسیب، سوراخ یا ریزش میوه',
    guides: ['stinkbugs', 'fruitborers', 'harvest'],
  },
  {
    id: 'wood',
    label: 'صمغ، آسیب طوقه یا سرشاخه',
    guides: ['phytophthora', 'twigborer', 'botryosphaeria'],
  },
  {
    id: 'yield',
    label: 'پوکی، افت محصول یا افت کیفیت',
    guides: ['pollination', 'nutrition', 'harvest', 'pruning'],
  },
]
export interface DiagnosticContext {
  province: string
  cultivar: string
  stage: string
  age: string
  duration: string
  distribution: string
  affected_percent: string
  irrigation: string
  recent_inputs: string
  symptoms: string[]
  goal: string
}
export const EMPTY_CONTEXT: DiagnosticContext = {
  province: '',
  cultivar: '',
  stage: '',
  age: '',
  duration: '',
  distribution: '',
  affected_percent: '',
  irrigation: '',
  recent_inputs: '',
  symptoms: [],
  goal: 'سلامت درخت و کیفیت محصول',
}
export function validateContext(value: unknown): DiagnosticContext {
  if (!value || typeof value !== 'object' || Array.isArray(value))
    throw new Error('اطلاعات زمینه باغ معتبر نیست.')
  const v = value as Record<string, unknown>
  const result = { ...EMPTY_CONTEXT }
  for (const key of Object.keys(EMPTY_CONTEXT).filter((k) => k !== 'symptoms') as (keyof Omit<
    DiagnosticContext,
    'symptoms'
  >)[]) {
    if (
      typeof v[key] !== 'string' ||
      (v[key] as string).length > (key === 'recent_inputs' ? 1000 : 160)
    )
      throw new Error('اطلاعات زمینه باغ معتبر نیست.')
    result[key] = (v[key] as string).trim()
  }
  if (
    !Array.isArray(v.symptoms) ||
    v.symptoms.length > SYMPTOMS.length ||
    v.symptoms.some((s) => !SYMPTOMS.some((x) => x.id === s))
  )
    throw new Error('نشانه‌های انتخابی معتبر نیستند.')
  result.symptoms = [...new Set(v.symptoms as string[])]
  for (const [key, max] of [
    ['age', 150],
    ['duration', 3650],
    ['affected_percent', 100],
  ] as const)
    if (
      result[key] &&
      (!Number.isFinite(Number(result[key])) ||
        Number(result[key]) < 0 ||
        Number(result[key]) > max)
    )
      throw new Error('سن، مدت علائم یا درصد درگیری معتبر نیست.')
  return result
}
export function careChecklist(context: DiagnosticContext) {
  return {
    guides: [
      ...new Set([
        'sampling',
        ...context.symptoms.flatMap((id) => SYMPTOMS.find((s) => s.id === id)?.guides ?? []),
        'irrigation',
        'pollination',
        'harvest',
      ]),
    ],
    immediate: [
      'پیش از هر اقدام، چند درخت سالم و علامت‌دار را در نقاط مختلف باغ مقایسه و تاریخ/پراکندگی را ثبت کنید.',
      'پشت و روی برگ، نمای نزدیک علامت با مقیاس و نمای کامل تاج را در نور طبیعی عکاسی کنید؛ ریشه را برای عکس‌برداری زخمی نکنید.',
      'تا شناسایی عامل و تأیید کارشناس، سم‌پاشی تقویمی و اضافه‌کردن کود بر اساس ظاهر را شروع نکنید.',
    ],
    ipm: [
      'حشره، مرحله رشد آن و شدت درگیری را با ذره‌بین و نمونه‌برداری میدانی بررسی کنید؛ خسارت محیطی می‌تواند شبیه آفت باشد.',
      'آبیاری و بهداشت باغ، دشمنان طبیعی و پایش منظم را در مدیریت تلفیقی مقدم بدانید.',
      'اگر مداخله لازم شد، روش و فرآورده ثبت‌شده برای پسته در ایران، دوز برچسب، فاصله برداشت، تجهیزات حفاظت و تناوب گروه اثر را کارشناس تعیین کند.',
    ],
    yield: [
      'هم‌زمانی گل‌دهی نر و ماده، پراکندگی گرده‌دهنده و سرما/باد دوره گل را ثبت کنید؛ پوکی فقط یک علت ندارد.',
      'برنامه آب را بر پایه رطوبت عمق ریشه، یکنواختی شبکه، زهکشی، مرحله رشد و کیفیت آب تنظیم کنید.',
      'تغذیه را با آزمایش خاک، برگ و آب و بار واقعی درخت تنظیم کنید؛ هرس شدید یا کود بیشتر الزاماً محصول بیشتر نمی‌دهد.',
      'برداشت به‌موقع، جداسازی میوه آسیب‌دیده، پوست‌گیری و خشک‌کردن مناسب برای کیفیت مهم‌اند؛ آفلاتوکسین از روی عکس قابل تشخیص نیست.',
    ],
    tests: [
      'در زردی/سوختگی: آزمایش برگ، خاک و آب و سابقه مصرف مواد.',
      'در صمغ/خشکیدگی: بازدید طوقه و ریشه و نمونه‌برداری آزمایشگاهی توسط کارشناس.',
      'در آفت مشکوک: نمونه حشره، پشت برگ، شمارش و الگوی درگیری، نه عکس منفرد.',
    ],
  }
}
