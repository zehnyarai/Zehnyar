/**
 * End-to-end tests: real Express app + real PostgreSQL, Gemini mocked.
 * Requires TEST_DATABASE_URL (a dedicated, disposable database). Skipped otherwise.
 */
import { test, before, after, describe } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import type { Server } from 'node:http';
import { loadEnv, type Env } from '../src/config/env.js';
import { createPool, type Db } from '../src/db/pool.js';
import { migrate } from '../src/db/migrate.js';
import { createApp } from '../src/app.js';
import { DevLogSmsSender } from '../src/lib/sms.js';
import { GeminiVisionClient, type FetchLike } from '../src/modules/ai/gemini.client.js';
import { LocalImageStorage } from '../src/lib/storage.js';
import { seedKnowledge } from '../src/modules/knowledge/knowledge.seed.js';

const TEST_DB = process.env.TEST_DATABASE_URL;
const skip = TEST_DB ? false : 'TEST_DATABASE_URL not set';

const JPEG = Buffer.concat([Buffer.from([0xff, 0xd8, 0xff, 0xe0]), Buffer.alloc(200, 7)]);

const validReport = {
  imageQuality: { usable: true, issues: [] },
  detectedSubject: 'برگ پسته',
  diagnosis: { knowledgeSlug: 'pistachio-psylla', title: 'شپشک پسته', isHealthy: false, confidence: 100 },
  observedSymptoms: ['پیچیدگی برگ', 'ترشح شیره شیرین', 'پوره زیر برگ'],
  alternatives: [{ knowledgeSlug: 'pistachio-mites', title: 'کنه پسته', confidence: 40, reason: 'نقاط ریز' }],
  recommendedActions: [
    { text: 'پایش زیر برگ‌ها در سه نقطه باغ', priority: 'immediate' },
    { text: 'روی درخت ۵ لیتر سم بریزید', priority: 'immediate' },
  ],
  additionalInfoNeeded: ['عکس پشت برگ'],
  summary: 'نشانه‌ها با آلودگی شپشک پسته سازگار است؛ پایش و تأیید کارشناس توصیه می‌شود.',
};

function geminiOk(text: string): Response {
  return new Response(JSON.stringify({ candidates: [{ content: { parts: [{ text }] }, finishReason: 'STOP' }] }), {
    status: 200,
    headers: { 'content-type': 'application/json' },
  });
}

describe('Pestino API (integration)', { skip }, () => {
  let env: Env;
  let db: Db;
  let server: Server;
  let base = '';
  let geminiMode: 'ok' | 'invalid' | 'down' = 'ok';
  let geminiCalls = 0;
  let tmpDir = '';

  const mockFetch: FetchLike = async (url, init) => {
    geminiCalls++;
    assert.match(url, /generativelanguage\.googleapis\.com/);
    const headers = init.headers as Record<string, string>;
    assert.ok(headers['x-goog-api-key'], 'API key must be sent in header');
    const body = JSON.parse(String(init.body));
    assert.equal(body.contents[0].parts[0].inline_data.mime_type, 'image/jpeg');
    if (geminiMode === 'down') return new Response('boom', { status: 503 });
    if (geminiMode === 'invalid') return geminiOk('this is not json at all');
    return geminiOk(JSON.stringify(validReport));
  };

  async function api(method: string, p: string, opts: { token?: string; json?: unknown; form?: FormData } = {}) {
    const headers: Record<string, string> = {};
    if (opts.token) headers.authorization = `Bearer ${opts.token}`;
    let body: BodyInit | undefined;
    if (opts.json !== undefined) {
      headers['content-type'] = 'application/json';
      body = JSON.stringify(opts.json);
    } else if (opts.form) {
      body = opts.form;
    }
    const res = await fetch(base + p, { method, headers, body });
    const text = await res.text();
    let json: any = null;
    try {
      json = text ? JSON.parse(text) : null;
    } catch {
      json = text;
    }
    return { status: res.status, json, headers: res.headers };
  }

  async function login(phone: string) {
    // Tests share numbers across cases; clear OTP history so the resend cooldown does not interfere.
    await db.query('DELETE FROM otp_codes WHERE phone = $1', [phone]);
    const req = await api('POST', '/api/v1/auth/otp/request', { json: { phone } });
    assert.equal(req.status, 202);
    const code = req.json.devCode as string;
    assert.match(code, /^\d{6}$/);
    const ver = await api('POST', '/api/v1/auth/otp/verify', { json: { phone, code } });
    assert.equal(ver.status, 200, JSON.stringify(ver.json));
    return { token: ver.json.tokens.accessToken as string, refresh: ver.json.tokens.refreshToken as string, user: ver.json.user, otp: code };
  }

  before(async () => {
    env = loadEnv({
      NODE_ENV: 'test',
      DATABASE_URL: TEST_DB!,
      JWT_ACCESS_SECRET: 'test_access_secret_0123456789abcdefghij',
      OTP_HMAC_SECRET: 'test_otp_secret_0123456789abcdefghijklmn',
      OTP_DEV_ECHO: 'true',
      GEMINI_API_KEY: 'test-gemini-key-123456',
      FREE_MONTHLY_ANALYSES: '2',
      FREE_MAX_FARMS: '1',
      TRUST_PROXY: '0',
      AUTH_RATE_LIMIT_PER_15MIN: '1000',
      GLOBAL_RATE_LIMIT_PER_15MIN: '5000',
    });
    db = createPool(env);
    await db.query('DROP SCHEMA public CASCADE; CREATE SCHEMA public;');
    await migrate(db);
    await seedKnowledge(db);

    tmpDir = mkdtempSync(path.join(tmpdir(), 'pestino-test-'));
    const app = createApp({
      env,
      db,
      sms: new DevLogSmsSender(),
      ai: new GeminiVisionClient({ apiKey: env.GEMINI_API_KEY, model: env.GEMINI_MODEL, timeoutMs: 5000, fetchImpl: mockFetch }),
      storage: new LocalImageStorage(tmpDir),
    });
    await new Promise<void>((resolve) => {
      server = app.listen(0, '127.0.0.1', () => resolve());
    });
    const port = (server.address() as { port: number }).port;
    base = `http://127.0.0.1:${port}`;
  });

  after(async () => {
    await new Promise<void>((resolve) => server?.close(() => resolve()));
    await db?.end();
    if (tmpDir) rmSync(tmpDir, { recursive: true, force: true });
  });

  test('health endpoint reports database status', async () => {
    const res = await api('GET', '/health');
    assert.equal(res.status, 200);
    assert.equal(res.json.db, 'ok');
  });

  test('OTP: wrong code is rejected, correct code logs in and creates user', async () => {
    const phone = '09121110001';
    const req = await api('POST', '/api/v1/auth/otp/request', { json: { phone } });
    assert.equal(req.status, 202);
    const wrong = req.json.devCode === '000000' ? '111111' : '000000';
    const bad = await api('POST', '/api/v1/auth/otp/verify', { json: { phone, code: wrong } });
    assert.equal(bad.status, 400);
    assert.equal(bad.json.error.code, 'OTP_INVALID');

    const good = await api('POST', '/api/v1/auth/otp/verify', { json: { phone, code: req.json.devCode } });
    assert.equal(good.status, 200);
    assert.equal(good.json.isNewUser, true);
    assert.equal(good.json.user.phone, phone);
    assert.equal(good.json.user.passwordHash, undefined);
  });

  test('OTP: resend cooldown is enforced', async () => {
    const res = await api('POST', '/api/v1/auth/otp/request', { json: { phone: '09121110001' } });
    assert.equal(res.status, 429);
    assert.equal(res.json.error.code, 'OTP_COOLDOWN');
  });

  test('OTP: invalid phone numbers are rejected before any DB work', async () => {
    const res = await api('POST', '/api/v1/auth/otp/request', { json: { phone: '0212345678' } });
    assert.equal(res.status, 400);
    assert.equal(res.json.error.code, 'INVALID_PHONE');
  });

  test('protected routes require a valid bearer token', async () => {
    assert.equal((await api('GET', '/api/v1/me')).status, 401);
    const bad = await api('GET', '/api/v1/me', { token: 'abc.def.ghi' });
    assert.equal(bad.status, 401);
    assert.equal(bad.json.error.code, 'TOKEN_INVALID');
  });

  test('farm management and free-plan farm limit', async () => {
    const owner = await login('09121110002');
    const created = await api('POST', '/api/v1/farms', {
      token: owner.token,
      json: { name: 'باغ شماره یک', province: 'کرمان', city: 'رفسنجان', areaHectares: 12.5, pistachioVariety: 'اوحدی', averageTreeAge: 18, irrigationMethod: 'drip', soilType: 'loam' },
    });
    assert.equal(created.status, 201, JSON.stringify(created.json));
    assert.equal(created.json.farm.areaHectares, 12.5);

    const second = await api('POST', '/api/v1/farms', {
      token: owner.token,
      json: { name: 'باغ دوم', province: 'کرمان', city: 'زرند' },
    });
    assert.equal(second.status, 402);
    assert.equal(second.json.error.code, 'FARM_LIMIT_REACHED');

    const invalid = await api('POST', '/api/v1/farms', { token: owner.token, json: { name: 'x', province: 'k', city: 'c', hack: true } });
    assert.equal(invalid.status, 400);

    const patched = await api('PATCH', `/api/v1/farms/${created.json.farm.id}`, { token: owner.token, json: { city: 'کرمان' } });
    assert.equal(patched.json.farm.city, 'کرمان');

    const trees = await api('POST', `/api/v1/farms/${created.json.farm.id}/trees`, { token: owner.token, json: { label: 'درخت ۱', plantedYear: 1380 } });
    assert.equal(trees.status, 201);
  });

  test('farms are private: another user gets 404', async () => {
    const owner = await login('09121110002');
    const list = await api('GET', '/api/v1/farms', { token: owner.token });
    const farmId = list.json.items[0].id as string;
    const intruder = await login('09121110003');
    const res = await api('GET', `/api/v1/farms/${farmId}`, { token: intruder.token });
    assert.equal(res.status, 404);
    assert.equal(res.json.error.code, 'FARM_NOT_FOUND');
  });

  test('image analysis: validates file, calls Gemini, stores safe report and enforces quota', async () => {
    const user = await login('09121110002');
    const farmId = (await api('GET', '/api/v1/farms', { token: user.token })).json.items[0].id as string;

    const form = new FormData();
    form.append('image', new Blob([JPEG], { type: 'image/jpeg' }), 'leaf.jpg');
    form.append('category', 'leaf');
    form.append('season', 'spring');
    form.append('farmId', farmId);
    form.append('treeAgeYears', '18');

    geminiMode = 'ok';
    const before = geminiCalls;
    const res = await api('POST', '/api/v1/analyses', { token: user.token, form });
    assert.equal(res.status, 201, JSON.stringify(res.json));
    assert.equal(geminiCalls, before + 1);

    const a = res.json.analysis;
    assert.equal(a.status, 'completed');
    assert.equal(a.primaryIssueSlug, 'pistachio-psylla');
    assert.ok(a.confidence <= 90, 'confidence must never be 100');
    assert.equal(a.report.diagnosis.knowledgeSlug, 'pistachio-psylla');
    assert.ok(a.report.references.length > 0, 'references come from the knowledge base');
    assert.ok(a.report.disclaimer.includes('جایگزین'));
    const actions = a.report.recommendedActions.map((x: { text: string }) => x.text).join(' | ');
    assert.ok(!actions.includes('۵ لیتر سم'), 'dangerous dosage must be sanitized');
    assert.ok(a.report.meta.safetyFlags.includes('UNSAFE_ADVICE_REPLACED'));
    assert.equal(a.report.meta.promptVersion.length > 0, true);

    // Image is only available to the owner.
    const img = await fetch(`${base}/api/v1/analyses/${a.id}/image`, { headers: { authorization: `Bearer ${user.token}` } });
    assert.equal(img.status, 200);
    assert.equal(img.headers.get('content-type'), 'image/jpeg');
    const stranger = await login('09121110003');
    const denied = await api('GET', `/api/v1/analyses/${a.id}`, { token: stranger.token });
    assert.equal(denied.status, 404);

    // Unsupported file type is rejected by magic bytes before any AI call.
    const fake = new FormData();
    fake.append('image', new Blob(['<html>x</html>'], { type: 'image/jpeg' }), 'x.jpg');
    fake.append('category', 'leaf');
    fake.append('season', 'spring');
    const badFile = await api('POST', '/api/v1/analyses', { token: user.token, form: fake });
    assert.equal(badFile.status, 400);
    assert.equal(badFile.json.error.code, 'UNSUPPORTED_IMAGE');
    assert.equal(geminiCalls, before + 1, 'no AI call for rejected files');

    // Second analysis uses the last free slot; third is blocked.
    const second = await api('POST', '/api/v1/analyses', { token: user.token, form: makeForm('trunk') });
    assert.equal(second.status, 201);
    const usage = await api('GET', '/api/v1/analyses/usage', { token: user.token });
    assert.equal(usage.json.usage.used, 2);
    assert.equal(usage.json.usage.remaining, 0);

    const third = await api('POST', '/api/v1/analyses', { token: user.token, form: makeForm('soil') });
    assert.equal(third.status, 402);
    assert.equal(third.json.error.code, 'QUOTA_EXCEEDED');

    const history = await api('GET', '/api/v1/analyses?limit=10', { token: user.token });
    assert.equal(history.json.items.length, 2);
  });

  test('failed AI calls do not consume quota', async () => {
    const user = await login('09121110004');
    geminiMode = 'down';
    const res = await api('POST', '/api/v1/analyses', { token: user.token, form: makeForm('leaf') });
    assert.equal(res.status, 502);
    assert.equal(res.json.error.code, 'AI_UPSTREAM_ERROR');

    geminiMode = 'invalid';
    const invalid = await api('POST', '/api/v1/analyses', { token: user.token, form: makeForm('leaf') });
    assert.equal(invalid.status, 502);
    assert.equal(invalid.json.error.code, 'AI_INVALID_OUTPUT');

    geminiMode = 'ok';
    const usage = await api('GET', '/api/v1/analyses/usage', { token: user.token });
    assert.equal(usage.json.usage.used, 0);
  });

  test('refresh tokens rotate, and reuse of an old token revokes the session family', async () => {
    const user = await login('09121110005');
    const first = await api('POST', '/api/v1/auth/refresh', { json: { refreshToken: user.refresh } });
    assert.equal(first.status, 200);
    const rotated = first.json.tokens.refreshToken as string;
    assert.notEqual(rotated, user.refresh);

    // Re-using the already-rotated token is treated as theft.
    const reuse = await api('POST', '/api/v1/auth/refresh', { json: { refreshToken: user.refresh } });
    assert.equal(reuse.status, 401);
    assert.equal(reuse.json.error.code, 'REFRESH_REUSED');

    const afterTheft = await api('POST', '/api/v1/auth/refresh', { json: { refreshToken: rotated } });
    assert.equal(afterTheft.status, 401, 'the whole family must be revoked');
  });

  test('logout revokes the refresh token', async () => {
    const user = await login('09121110006');
    const out = await api('POST', '/api/v1/auth/logout', { json: { refreshToken: user.refresh } });
    assert.equal(out.status, 204);
    const after = await api('POST', '/api/v1/auth/refresh', { json: { refreshToken: user.refresh } });
    assert.equal(after.status, 401);
  });

  test('profile update and knowledge base endpoints', async () => {
    const user = await login('09121110007');
    const me = await api('PATCH', '/api/v1/me', { token: user.token, json: { fullName: 'علی محمدی', province: 'کرمان', city: 'رفسنجان' } });
    assert.equal(me.status, 200);
    assert.equal(me.json.user.fullName, 'علی محمدی');

    const pests = await api('GET', '/api/v1/knowledge?kind=pest', { token: user.token });
    assert.equal(pests.json.items.length, 5);

    const search = await api('GET', `/api/v1/knowledge?q=${encodeURIComponent('شوری')}`, { token: user.token });
    assert.ok(search.json.items.some((i: { slug: string }) => i.slug === 'soil-salinity'));

    const article = await api('GET', '/api/v1/knowledge/gummosis-root-rot', { token: user.token });
    assert.equal(article.status, 200);
    assert.equal(article.json.article.kind, 'disease');
    assert.ok(article.json.article.references.length > 0);
    assert.match(article.json.article.attributes.pathogen, /Phytophthora/);

    assert.equal((await api('GET', '/api/v1/knowledge/does-not-exist', { token: user.token })).status, 404);
    assert.equal((await api('GET', '/api/v1/knowledge/..%2Fsecret', { token: user.token })).status, 400);
  });

  test('subscriptions: public catalogue and payment placeholder', async () => {
    const plans = await api('GET', '/api/v1/subscriptions/plans');
    assert.equal(plans.json.items.length, 2);
    const user = await login('09121110008');
    const me = await api('GET', '/api/v1/subscriptions/me', { token: user.token });
    assert.equal(me.json.plan.code, 'free');
    const checkout = await api('POST', '/api/v1/subscriptions/checkout', { token: user.token, json: {} });
    assert.equal(checkout.status, 501);
  });

  function makeForm(category: string) {
    const f = new FormData();
    f.append('image', new Blob([JPEG], { type: 'image/jpeg' }), 'p.jpg');
    f.append('category', category);
    f.append('season', 'summer');
    return f;
  }
});
