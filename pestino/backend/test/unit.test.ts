import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { normalizeIranianMobile, toAsciiDigits } from '../src/lib/phone.js';
import { detectImageMime } from '../src/lib/storage.js';
import { applySafetyRules, isUnsafeAdvice, SAFE_CHEMICAL_ADVICE_FA, confidenceLabelFa } from '../src/modules/ai/safety.js';
import { aiReportSchema, type AiReport } from '../src/modules/ai/report.schema.js';
import { stripCodeFence } from '../src/modules/ai/gemini.client.js';
import { loadEnv } from '../src/config/env.js';
import { hmac, safeEqual, sha256, generateOtpCode } from '../src/lib/crypto.js';
import { currentQuotaWindowStart, planCatalog } from '../src/modules/subscriptions/plans.js';
import { verifyAccessToken, signAccessToken } from '../src/modules/auth/tokens.js';
import { buildStoredReport } from '../src/modules/analyses/analyses.service.js';
import { loadKnowledgeFiles } from '../src/modules/knowledge/knowledge.seed.js';

const baseReport = (): AiReport =>
  aiReportSchema.parse({
    imageQuality: { usable: true, issues: [] },
    diagnosis: { knowledgeSlug: 'pistachio-psylla', title: 'شپشک پسته', isHealthy: false, confidence: 95 },
    observedSymptoms: ['پیچیدگی برگ', 'عسلک روی برگ', 'پوره زیر برگ'],
    alternatives: [{ knowledgeSlug: 'pistachio-mites', title: 'کنه', confidence: 90, reason: 'نقاط ریز' }],
    recommendedActions: [{ text: 'پایش زیر برگ‌ها', priority: 'immediate' }],
    additionalInfoNeeded: [],
    summary: 'احتمال آلودگی به شپشک پسته وجود دارد و نیاز به پایش دارد.',
  });

describe('phone normalization', () => {
  test('accepts common Iranian formats', () => {
    assert.equal(normalizeIranianMobile('09121234567'), '09121234567');
    assert.equal(normalizeIranianMobile('9121234567'), '09121234567');
    assert.equal(normalizeIranianMobile('+989121234567'), '09121234567');
    assert.equal(normalizeIranianMobile('00989121234567'), '09121234567');
    assert.equal(normalizeIranianMobile('۰۹۱۲ ۱۲۳ ۴۵۶۷'), '09121234567');
    assert.equal(normalizeIranianMobile('0912-123-4567'), '09121234567');
  });
  test('rejects invalid numbers', () => {
    assert.equal(normalizeIranianMobile('0212345678'), null);
    assert.equal(normalizeIranianMobile('091212345'), null);
    assert.equal(normalizeIranianMobile('abc'), null);
    assert.equal(toAsciiDigits('۱۲۳'), '123');
  });
});

describe('image type detection', () => {
  test('detects by magic bytes, not by extension', () => {
    assert.equal(detectImageMime(Buffer.from([0xff, 0xd8, 0xff, 0xe0, 0, 0])), 'image/jpeg');
    assert.equal(detectImageMime(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0])), 'image/png');
    const webp = Buffer.concat([Buffer.from('RIFF'), Buffer.from([0, 0, 0, 0]), Buffer.from('WEBP')]);
    assert.equal(detectImageMime(webp), 'image/webp');
    assert.equal(detectImageMime(Buffer.from('<html>not an image</html>')), null);
    assert.equal(detectImageMime(Buffer.from('%PDF-1.4')), null);
  });
});

describe('AI safety rules', () => {
  test('flags pesticide dosage and dangerous practices', () => {
    assert.equal(isUnsafeAdvice('از ۲ لیتر سم حشره‌کش در هر هکتار استفاده کنید'), true);
    assert.equal(isUnsafeAdvice('سم را با سم دیگر مخلوط کنید'), true);
    assert.equal(isUnsafeAdvice('در صورت لزوم با کارشناس برای انتخاب سم مشورت کنید'), false);
    assert.equal(isUnsafeAdvice('آبیاری را در ساعات خنک انجام دهید'), false);
  });

  test('replaces unsafe actions with referral text', () => {
    const r = baseReport();
    r.recommendedActions.push({ text: 'روی برگ ۵ کیلوگرم سم اسپری کنید', priority: 'immediate' });
    const { report, flags } = applySafetyRules(r);
    assert.ok(flags.includes('UNSAFE_ADVICE_REPLACED'));
    assert.equal(report.recommendedActions[1].text, SAFE_CHEMICAL_ADVICE_FA);
  });

  test('never allows 100% confidence', () => {
    const r = baseReport();
    r.diagnosis.confidence = 100;
    const { report, flags } = applySafetyRules(r);
    assert.ok(report.diagnosis.confidence <= 90);
    assert.ok(flags.includes('CONFIDENCE_CAPPED'));
  });

  test('caps confidence when evidence is thin', () => {
    const r = baseReport();
    r.observedSymptoms = ['پیچیدگی برگ'];
    r.diagnosis.confidence = 88;
    const { report, flags } = applySafetyRules(r);
    assert.equal(report.diagnosis.confidence, 60);
    assert.ok(flags.includes('LOW_EVIDENCE_CAP'));
  });

  test('unusable images cap confidence and ask for retake', () => {
    const r = baseReport();
    r.imageQuality = { usable: false, issues: ['تار'] };
    const { report } = applySafetyRules(r);
    assert.ok(report.diagnosis.confidence <= 30);
    assert.ok(report.additionalInfoNeeded[0].includes('عکس'));
  });

  test('confidence labels', () => {
    assert.equal(confidenceLabelFa(80), 'اطمینان بالا');
    assert.equal(confidenceLabelFa(55), 'اطمینان متوسط');
    assert.equal(confidenceLabelFa(10), 'اطمینان پایین');
  });

  test('stored report contains disclaimer and integer confidence', () => {
    const { report } = applySafetyRules(baseReport());
    const stored = buildStoredReport(report, {
      model: 'm',
      promptVersion: 'v',
      category: 'leaf',
      season: 'spring',
      primarySlug: 'pistachio-psylla',
      references: [],
      safetyFlags: [],
      latencyMs: 1,
    });
    assert.match(stored.disclaimer, /جایگزین/);
    assert.equal(Number.isInteger(stored.diagnosis.confidence), true);
    assert.equal(stored.category.label, 'برگ');
  });
});

describe('AI output parsing', () => {
  test('strips markdown code fences', () => {
    assert.equal(stripCodeFence('```json\n{"a":1}\n```'), '{"a":1}');
    assert.equal(stripCodeFence('  {"a":1}  '), '{"a":1}');
  });
  test('rejects reports missing required fields', () => {
    assert.throws(() => aiReportSchema.parse({ diagnosis: { title: 'x', confidence: 10 } }));
  });
  test('rejects out-of-range confidence', () => {
    const bad = { ...baseReport(), diagnosis: { title: 'ab', confidence: 150 } };
    assert.throws(() => aiReportSchema.parse(bad));
  });
});

describe('knowledge base files', () => {
  test('all 18 articles load, every reference key resolves, categories are complete', async () => {
    const { articles, refs } = await loadKnowledgeFiles();
    assert.equal(articles.length, 18);
    assert.ok(refs.length >= 9);
    const kinds = new Set(articles.map((a) => a.kind));
    assert.deepEqual([...kinds].sort(), ['disease', 'environmental', 'nutrient', 'pest']);
    assert.equal(articles.filter((a) => a.kind === 'pest').length, 5);
    assert.equal(articles.filter((a) => a.kind === 'nutrient').length, 5);
    assert.equal(articles.filter((a) => a.kind === 'environmental').length, 4);
    for (const a of articles) assert.ok(a.referenceKeys.length > 0, a.slug);
  });
});

describe('environment validation', () => {
  const good = {
    DATABASE_URL: 'postgres://u:p@localhost:5432/db',
    JWT_ACCESS_SECRET: 'a'.repeat(40),
    OTP_HMAC_SECRET: 'b'.repeat(40),
    GEMINI_API_KEY: 'k'.repeat(20),
  };
  test('applies defaults', () => {
    const env = loadEnv(good);
    assert.equal(env.PORT, 8080);
    assert.equal(env.FREE_MONTHLY_ANALYSES, 5);
    assert.equal(env.OTP_DEV_ECHO, false);
  });
  test('rejects weak secrets', () => {
    assert.throws(() => loadEnv({ ...good, JWT_ACCESS_SECRET: 'short' }), /JWT_ACCESS_SECRET/);
  });
  test('refuses OTP echo in production', () => {
    assert.throws(() => loadEnv({ ...good, NODE_ENV: 'production', OTP_DEV_ECHO: 'true' }), /OTP_DEV_ECHO/);
  });
  test('parses CORS origins list', () => {
    const env = loadEnv({ ...good, CORS_ORIGINS: 'https://a.ir, https://b.ir' });
    assert.deepEqual(env.CORS_ORIGINS, ['https://a.ir', 'https://b.ir']);
  });
});

describe('crypto & tokens', () => {
  test('hmac is deterministic and keyed', () => {
    assert.equal(hmac('k1', 'x'), hmac('k1', 'x'));
    assert.notEqual(hmac('k1', 'x'), hmac('k2', 'x'));
    assert.equal(sha256('abc').length, 64);
    assert.equal(safeEqual('abc', 'abc'), true);
    assert.equal(safeEqual('abc', 'abd'), false);
  });
  test('OTP is 6 digits', () => {
    for (let i = 0; i < 50; i++) assert.match(generateOtpCode(), /^\d{6}$/);
  });
  test('access token round trip and tamper detection', () => {
    const secret = 's'.repeat(40);
    const t = signAccessToken({ id: '11111111-1111-1111-1111-111111111111', role: 'farmer' }, { secret, ttlSeconds: 60 });
    assert.equal(verifyAccessToken(t, secret).sub, '11111111-1111-1111-1111-111111111111');
    assert.throws(() => verifyAccessToken(t, 'x'.repeat(40)));
    assert.throws(() => verifyAccessToken(t.slice(0, -2) + 'AA', secret));
  });
  test('quota window starts at the first day of the UTC month', () => {
    const d = currentQuotaWindowStart(new Date('2026-10-12T10:00:00Z'));
    assert.equal(d.toISOString(), '2026-10-01T00:00:00.000Z');
  });
  test('plan catalogue: free is limited, premium is unlimited', () => {
    const c = planCatalog({ FREE_MONTHLY_ANALYSES: 5, FREE_MAX_FARMS: 1 });
    assert.equal(c.free.monthlyAnalyses, 5);
    assert.equal(c.premium.monthlyAnalyses, null);
    assert.equal(c.free.pdfExport, false);
    assert.equal(c.premium.pdfExport, true);
  });
});
