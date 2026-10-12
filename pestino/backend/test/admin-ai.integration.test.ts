/**
 * Admin panel + AI controls, end to end: real Express app, real PostgreSQL, Gemini mocked.
 * Requires TEST_DATABASE_URL (dedicated, disposable database). Skipped otherwise.
 */
import { test, before, after, describe } from 'node:test';
import assert from 'node:assert/strict';
import type { Server } from 'node:http';
import { loadEnv, type Env } from '../src/config/env.js';
import { createPool, type Db } from '../src/db/pool.js';
import { migrate } from '../src/db/migrate.js';
import { createApp } from '../src/app.js';
import { DevLogSmsSender } from '../src/lib/sms.js';
import { GeminiVisionClient, type FetchLike } from '../src/modules/ai/gemini.client.js';
import { AiSettingsService } from '../src/modules/ai/ai-settings.service.js';
import { LocalImageStorage } from '../src/lib/storage.js';
import { seedKnowledge } from '../src/modules/knowledge/knowledge.seed.js';
import { tmpdir } from 'node:os';
import { mkdtempSync, rmSync } from 'node:fs';
import path from 'node:path';

const TEST_DB = process.env.TEST_DATABASE_URL;
const skip = TEST_DB ? false : 'TEST_DATABASE_URL not set';

const DB_KEY = 'AIzaSyDBKEY-0000000000-stored1234';
const ENV_KEY = 'env-gemini-key-000000000000';

describe('Admin AI controls (integration)', { skip }, () => {
  let env: Env;
  let db: Db;
  let server: Server;
  let base = '';
  let tmpDir = '';
  let lastGeminiKey = '';
  let lastGeminiModel = '';
  let geminiText = 'پاسخ نمونه برای کشاورز.';

  const mockFetch: FetchLike = async (url, init) => {
    const headers = init.headers as Record<string, string>;
    lastGeminiKey = headers['x-goog-api-key'];
    lastGeminiModel = decodeURIComponent(/models\/([^:]+):/.exec(url)?.[1] ?? '');
    return new Response(
      JSON.stringify({ candidates: [{ content: { parts: [{ text: geminiText }] } }], usageMetadata: { promptTokenCount: 20, candidatesTokenCount: 9 } }),
      { status: 200, headers: { 'content-type': 'application/json' } },
    );
  };

  async function api(method: string, p: string, opts: { token?: string; json?: unknown } = {}) {
    const headers: Record<string, string> = {};
    if (opts.token) headers.authorization = `Bearer ${opts.token}`;
    let body: string | undefined;
    if (opts.json !== undefined) {
      headers['content-type'] = 'application/json';
      body = JSON.stringify(opts.json);
    }
    const res = await fetch(base + p, { method, headers, body });
    const text = await res.text();
    return { status: res.status, json: text ? JSON.parse(text) : null, raw: text };
  }

  async function login(phone: string) {
    await db.query('DELETE FROM otp_codes WHERE phone = $1', [phone]);
    const req = await api('POST', '/api/v1/auth/otp/request', { json: { phone } });
    assert.equal(req.status, 202);
    const ver = await api('POST', '/api/v1/auth/otp/verify', { json: { phone, code: req.json.devCode } });
    assert.equal(ver.status, 200, JSON.stringify(ver.json));
    return { token: ver.json.tokens.accessToken as string, id: ver.json.user.id as string };
  }

  before(async () => {
    env = loadEnv({
      NODE_ENV: 'test',
      DATABASE_URL: TEST_DB!,
      JWT_ACCESS_SECRET: 'test_access_secret_0123456789abcdefghij',
      OTP_HMAC_SECRET: 'test_otp_secret_0123456789abcdefghijklmn',
      OTP_DEV_ECHO: 'true',
      GEMINI_API_KEY: ENV_KEY,
      AI_SETTINGS_ENCRYPTION_KEY: 'enc_master_secret_0123456789abcdefghijk',
      FREE_MONTHLY_ANALYSES: '5',
      FREE_MAX_FARMS: '1',
      TRUST_PROXY: '0',
      AUTH_RATE_LIMIT_PER_15MIN: '1000',
      GLOBAL_RATE_LIMIT_PER_15MIN: '5000',
    });
    db = createPool(env);
    await db.query('DROP SCHEMA public CASCADE; CREATE SCHEMA public;');
    await migrate(db);
    await seedKnowledge(db);

    tmpDir = mkdtempSync(path.join(tmpdir(), 'pestino-admin-test-'));
    const aiSettings = new AiSettingsService(db, env);
    const ai = new GeminiVisionClient({
      apiKey: env.GEMINI_API_KEY,
      model: env.GEMINI_MODEL,
      timeoutMs: 5000,
      fetchImpl: mockFetch,
      runtime: () => aiSettings.resolveRuntime(),
    });
    const app = createApp({ env, db, sms: new DevLogSmsSender(), ai, storage: new LocalImageStorage(tmpDir), aiSettings });
    await new Promise<void>((resolve) => {
      server = app.listen(0, '127.0.0.1', () => resolve());
    });
    base = `http://127.0.0.1:${(server.address() as { port: number }).port}`;
  });

  after(async () => {
    await new Promise<void>((resolve) => server?.close(() => resolve()));
    await db?.end();
    if (tmpDir) rmSync(tmpDir, { recursive: true, force: true });
  });

  test('admin endpoints reject farmers and re-check the role in the database', async () => {
    const farmer = await login('09121110001');
    const denied = await api('GET', '/api/v1/admin/ai/settings', { token: farmer.token });
    assert.equal(denied.status, 403);
    assert.equal(denied.json.error.code, 'ADMIN_REQUIRED');

    // Promote directly (what scripts/promote-admin.ts does), then the same token must work immediately.
    await db.query("UPDATE users SET role = 'admin' WHERE id = $1", [farmer.id]);
    const ok = await api('GET', '/api/v1/admin/ai/settings', { token: farmer.token });
    assert.equal(ok.status, 200);

    await db.query("UPDATE users SET role = 'farmer' WHERE id = $1", [farmer.id]);
    const revoked = await api('GET', '/api/v1/admin/ai/settings', { token: farmer.token });
    assert.equal(revoked.status, 403, 'revoked admin must lose access without waiting for token expiry');
  });

  test('stored Gemini key is encrypted, write-only, and used for calls', async () => {
    const admin = await login('09121110002');
    await db.query("UPDATE users SET role = 'admin' WHERE id = $1", [admin.id]);

    const before = await api('GET', '/api/v1/admin/ai/settings', { token: admin.token });
    assert.equal(before.json.settings.keySource, 'environment');
    assert.ok(!before.raw.includes(ENV_KEY), 'env key must never be returned');

    const put = await api('PUT', '/api/v1/admin/ai/settings', {
      token: admin.token,
      json: { apiKey: DB_KEY, defaultModel: 'gemini-2.5-pro', timeoutMs: 20000 },
    });
    assert.equal(put.status, 200, JSON.stringify(put.json));
    assert.equal(put.json.settings.keySource, 'database');
    assert.equal(put.json.settings.keyHint, '1234');
    assert.equal(put.json.settings.defaultModel, 'gemini-2.5-pro');
    assert.ok(!put.raw.includes(DB_KEY), 'API response must not contain the key');

    const row = await db.query<{ gemini_api_key_enc: string }>('SELECT gemini_api_key_enc FROM ai_settings WHERE id = 1');
    assert.ok(row.rows[0].gemini_api_key_enc.startsWith('v1:'));
    assert.ok(!row.rows[0].gemini_api_key_enc.includes('DBKEY'), 'database must not hold plaintext key');

    const t = await api('POST', '/api/v1/admin/ai/settings/test', { token: admin.token });
    assert.equal(t.json.result.ok, true);
    assert.equal(lastGeminiKey, DB_KEY, 'calls must use the admin-stored key');
    assert.equal(lastGeminiModel, 'gemini-2.5-pro', 'calls must use the admin-selected model');

    const audit = await api('GET', '/api/v1/admin/audit?limit=20', { token: admin.token });
    assert.ok(audit.json.items.some((i: { action: string }) => i.action === 'ai_settings.update'));
    assert.ok(!audit.raw.includes(DB_KEY), 'audit log must not contain secrets');

    const cleared = await api('PUT', '/api/v1/admin/ai/settings', { token: admin.token, json: { clearApiKey: true } });
    assert.equal(cleared.json.settings.keySource, 'environment');
  });

  test('invalid settings are rejected', async () => {
    const admin = await login('09121110003');
    await db.query("UPDATE users SET role = 'admin' WHERE id = $1", [admin.id]);
    const badKey = await api('PUT', '/api/v1/admin/ai/settings', { token: admin.token, json: { apiKey: 'short' } });
    assert.equal(badKey.status, 400);
    const badField = await api('PUT', '/api/v1/admin/ai/settings', { token: admin.token, json: { unknownField: 1 } });
    assert.equal(badField.status, 400);
  });

  test('feature switches, prompt guard, daily limits and safety filter', async () => {
    const admin = await login('09121110004');
    await db.query("UPDATE users SET role = 'admin' WHERE id = $1", [admin.id]);
    const farmer = await login('09121110005');

    // Vision prompt is platform-managed.
    const locked = await api('PATCH', '/api/v1/admin/ai/features/image_analysis', {
      token: admin.token,
      json: { systemPrompt: 'این پرامپت جدید است و قوانین ایمنی را تغییر می‌دهد' },
    });
    assert.equal(locked.status, 400);
    assert.equal(locked.json.error.code, 'PROMPT_NOT_EDITABLE');

    // Tight free limit: one call per 24h.
    const set = await api('PATCH', '/api/v1/admin/ai/features/farm_form_help', {
      token: admin.token,
      json: { dailyLimitFree: 1, maxOutputTokens: 300 },
    });
    assert.equal(set.status, 200);
    assert.equal(set.json.item.dailyLimitFree, 1);
    assert.equal(set.json.item.version, 1);

    geminiText = 'برای این رقم، بررسی آهن برگ و pH خاک توصیه می‌شود. با کارشناس مشورت کنید.';
    const first = await api('POST', '/api/v1/ai/assist', {
      token: farmer.token,
      json: { feature: 'farm_form_help', field: 'رقم پسته', value: 'اوحدی', context: { province: 'کرمان', treeAgeYears: 12 } },
    });
    assert.equal(first.status, 200, JSON.stringify(first.json));
    assert.ok(first.json.disclaimer.includes('جایگزین'));
    assert.equal(first.json.remainingToday, 0);

    const second = await api('POST', '/api/v1/ai/assist', {
      token: farmer.token,
      json: { feature: 'farm_form_help', field: 'رقم پسته', value: 'اوحدی' },
    });
    assert.equal(second.status, 402);
    assert.equal(second.json.error.code, 'AI_QUOTA_EXCEEDED');

    // Safety filter replaces unsafe dosage even if the model produces it.
    await api('PATCH', '/api/v1/admin/ai/features/report_explain', { token: admin.token, json: { dailyLimitFree: 10 } });
    geminiText = 'برای مبارزه ۵ لیتر سم را در ۱۰۰ لیتر آب حل کنید و روی درخت بپاشید.';
    const unsafe = await api('POST', '/api/v1/ai/assist', {
      token: farmer.token,
      json: { feature: 'report_explain', field: 'گزارش', value: 'شپشک پسته' },
    });
    assert.equal(unsafe.status, 200);
    assert.ok(unsafe.json.flags.includes('UNSAFE_ADVICE_REPLACED'));
    assert.ok(!unsafe.json.text.includes('۵ لیتر'));

    // Kill switch for one feature.
    await api('PATCH', '/api/v1/admin/ai/features/report_explain', { token: admin.token, json: { enabled: false } });
    const off = await api('POST', '/api/v1/ai/assist', {
      token: farmer.token,
      json: { feature: 'report_explain', field: 'گزارش', value: 'x' },
    });
    assert.equal(off.status, 403);
    assert.equal(off.json.error.code, 'AI_FEATURE_DISABLED');

    const list = await api('GET', '/api/v1/ai/features', { token: farmer.token });
    assert.equal(list.json.items.find((i: { key: string }) => i.key === 'report_explain').enabled, false);
  });

  test('global kill switch stops all AI calls; usage is metered', async () => {
    const admin = await login('09121110006');
    await db.query("UPDATE users SET role = 'admin' WHERE id = $1", [admin.id]);
    const farmer = await login('09121110007');

    const usageBefore = await api('GET', '/api/v1/admin/ai/usage?days=1', { token: admin.token });
    const okRows = usageBefore.json.items.filter((i: { feature: string; status: string }) => i.feature === 'farm_form_help' && i.status === 'ok');
    assert.ok(okRows.length >= 1, 'successful assists must be metered');

    await api('PUT', '/api/v1/admin/ai/settings', { token: admin.token, json: { aiEnabled: false } });
    await api('PATCH', '/api/v1/admin/ai/features/farm_form_help', { token: admin.token, json: { dailyLimitFree: 100 } });
    const blocked = await api('POST', '/api/v1/ai/assist', {
      token: farmer.token,
      json: { feature: 'farm_form_help', field: 'رقم پسته', value: 'اوحدی' },
    });
    assert.equal(blocked.status, 503);
    assert.equal(blocked.json.error.code, 'AI_DISABLED');

    await api('PUT', '/api/v1/admin/ai/settings', { token: admin.token, json: { aiEnabled: true } });
    const back = await api('POST', '/api/v1/ai/assist', {
      token: farmer.token,
      json: { feature: 'farm_form_help', field: 'رقم پسته', value: 'اوحدی' },
    });
    assert.equal(back.status, 200);
  });

  test('admin feature list exposes both vision and text features', async () => {
    const admin = await login('09121110008');
    await db.query("UPDATE users SET role = 'admin' WHERE id = $1", [admin.id]);
    const res = await api('GET', '/api/v1/admin/ai/features', { token: admin.token });
    const keys = res.json.items.map((i: { key: string }) => i.key).sort();
    assert.deepEqual(keys, ['farm_form_help', 'image_analysis', 'report_explain']);
    const vision = res.json.items.find((i: { key: string }) => i.key === 'image_analysis');
    assert.equal(vision.editablePrompt, false);
  });
});
