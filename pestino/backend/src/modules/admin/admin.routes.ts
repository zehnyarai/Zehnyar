import { Router } from 'express';
import { z } from 'zod';
import type { Db } from '../../db/pool.js';
import { AppError } from '../../lib/errors.js';
import { requireAuth } from '../../middleware/auth.js';
import { validateBody, validateQuery } from '../../middleware/validate.js';
import type { AiSettingsService } from '../ai/ai-settings.service.js';
import { isAiFeatureKey } from '../ai/ai-features.js';
import type { GeminiVisionClient } from '../ai/gemini.client.js';
import type { RequestHandler } from 'express';
import rateLimit from 'express-rate-limit';
import { AdminAuthService } from './admin-auth.service.js';

const GEMINI_KEY_RE = /^[A-Za-z0-9_-]{20,200}$/;
const MODEL_RE = /^[a-z0-9][a-z0-9.\-]{2,79}$/i;

const settingsPatchSchema = z
  .object({
    apiKey: z.string().trim().regex(GEMINI_KEY_RE, 'Invalid API key format').optional(),
    clearApiKey: z.boolean().optional(),
    defaultModel: z.string().trim().regex(MODEL_RE).nullable().optional(),
    timeoutMs: z.number().int().min(5000).max(120000).nullable().optional(),
    aiEnabled: z.boolean().optional(),
  })
  .strict()
  .refine((v) => !(v.apiKey && v.clearApiKey), { message: 'Use either apiKey or clearApiKey' });

const featurePatchSchema = z
  .object({
    enabled: z.boolean().optional(),
    model: z.string().trim().regex(MODEL_RE).nullable().optional(),
    systemPrompt: z.string().trim().min(20).max(4000).nullable().optional(),
    maxOutputTokens: z.number().int().min(128).max(8192).optional(),
    temperature: z.number().min(0).max(1).optional(),
    dailyLimitFree: z.number().int().min(0).max(1000).optional(),
    dailyLimitPremium: z.number().int().min(0).max(10000).optional(),
  })
  .strict();

const adminLoginSchema = z.object({
  phone: z.string().min(9).max(20),
  password: z.string().min(1).max(200),
});

const usersQuerySchema = z.object({
  q: z.string().trim().max(40).optional(),
  limit: z.coerce.number().int().min(1).max(100).default(50),
});

const userPatchSchema = z.object({ isActive: z.boolean() }).strict();

const usageQuerySchema = z.object({ days: z.coerce.number().int().min(1).max(90).default(7) });
const auditQuerySchema = z.object({ limit: z.coerce.number().int().min(1).max(200).default(50) });

/**
 * Admin-only middleware. The role is re-read from the database on every request,
 * so revoking admin takes effect immediately, without waiting for the access token to expire.
 */
export function requireAdmin(db: Db, jwtSecret: string): RequestHandler[] {
  return [
    requireAuth(jwtSecret),
    async (req, _res, next) => {
      try {
        const res = await db.query<{ role: string; is_active: boolean }>(
          'SELECT role, is_active FROM users WHERE id = $1',
          [req.auth!.userId],
        );
        const user = res.rows[0];
        if (!user || !user.is_active || user.role !== 'admin') {
          return next(AppError.forbidden('ADMIN_REQUIRED', 'Admin access required'));
        }
        next();
      } catch (err) {
        next(err);
      }
    },
  ];
}

/**
 * Admin API for the web admin panel (mounted under /admin).
 * Secrets are write-only: the Gemini key can be set or cleared, never read back.
 */
export function adminRoutes(deps: {
  db: Db;
  jwtSecret: string;
  settings: AiSettingsService;
  gemini: GeminiVisionClient;
  adminAuth: AdminAuthService;
}): Router {
  const r = Router();

  // Public: admin password login. Strict per-IP limit on top of the per-account lockout.
  const loginLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    limit: 20,
    standardHeaders: 'draft-7',
    legacyHeaders: false,
    handler: (_req, _res, next) => next(AppError.tooMany('RATE_LIMITED', 'Too many login attempts. Try again later.')),
  });
  r.post('/auth/login', loginLimiter, validateBody(adminLoginSchema), async (req, res) => {
    const body = req.body as z.infer<typeof adminLoginSchema>;
    const session = await deps.adminAuth.login(body.phone, body.password, {
      userAgent: req.get('user-agent') ?? undefined,
      ip: req.ip,
    });
    res.json(session);
  });

  const guard = requireAdmin(deps.db, deps.jwtSecret);
  r.use(guard);

  r.get('/stats', async (_req, res) => {
    const q = await deps.db.query<Record<string, string>>(`
      SELECT
        (SELECT count(*) FROM users)::text AS users_total,
        (SELECT count(*) FROM users WHERE created_at > now() - interval '7 days')::text AS users_new_7d,
        (SELECT count(*) FROM analyses WHERE created_at > now() - interval '24 hours')::text AS analyses_24h,
        (SELECT count(*) FROM analyses WHERE created_at > now() - interval '7 days')::text AS analyses_7d,
        (SELECT count(*) FROM analyses WHERE status = 'failed' AND created_at > now() - interval '7 days')::text AS analyses_failed_7d,
        (SELECT count(*) FROM subscriptions WHERE plan = 'premium' AND status = 'active'
            AND (expires_at IS NULL OR expires_at > now()))::text AS premium_active,
        (SELECT count(*) FROM ai_usage_logs WHERE created_at > now() - interval '7 days')::text AS ai_calls_7d,
        (SELECT count(*) FROM ai_usage_logs WHERE status = 'error' AND created_at > now() - interval '7 days')::text AS ai_errors_7d,
        (SELECT coalesce(sum(input_tokens + output_tokens), 0) FROM ai_usage_logs WHERE created_at > now() - interval '7 days')::text AS ai_tokens_7d
    `);
    const r0 = q.rows[0];
    const n = (k: string) => Number(r0[k]);
    res.json({
      stats: {
        users: { total: n('users_total'), newLast7Days: n('users_new_7d') },
        analyses: { last24Hours: n('analyses_24h'), last7Days: n('analyses_7d'), failedLast7Days: n('analyses_failed_7d') },
        subscriptions: { premiumActive: n('premium_active') },
        ai: { callsLast7Days: n('ai_calls_7d'), errorsLast7Days: n('ai_errors_7d'), tokensLast7Days: n('ai_tokens_7d') },
      },
    });
  });

  r.get('/users', validateQuery(usersQuerySchema), async (_req, res) => {
    const q = res.locals.query as z.infer<typeof usersQuerySchema>;
    const params: unknown[] = [];
    let where = 'TRUE';
    if (q.q) {
      params.push(`%${q.q.replace(/[%_]/g, '')}%`);
      where = `(phone LIKE $1 OR full_name ILIKE $1)`;
    }
    params.push(q.limit);
    const rows = await deps.db.query<{
      id: string; phone: string; full_name: string | null; role: string; is_active: boolean; created_at: Date; last_login_at: Date | null;
    }>(
      `SELECT id, phone, full_name, role, is_active, created_at, last_login_at
         FROM users WHERE ${where} ORDER BY created_at DESC LIMIT $${params.length}`,
      params,
    );
    res.json({
      items: rows.rows.map((u) => ({
        id: u.id,
        phone: u.phone,
        fullName: u.full_name,
        role: u.role,
        isActive: u.is_active,
        createdAt: u.created_at.toISOString(),
        lastLoginAt: u.last_login_at?.toISOString() ?? null,
      })),
    });
  });

  r.patch('/users/:userId', validateBody(userPatchSchema), async (req, res) => {
    const userId = String(req.params.userId);
    if (!/^[0-9a-f-]{36}$/i.test(userId)) throw AppError.badRequest('INVALID_ID', 'Invalid user id');
    const actorId = req.auth!.userId;
    const body = req.body as z.infer<typeof userPatchSchema>;
    if (userId === actorId && !body.isActive) {
      throw AppError.badRequest('SELF_DEACTIVATION', 'You cannot deactivate your own admin account');
    }
    const updated = await deps.db.query<{ id: string; is_active: boolean; role: string }>(
      `UPDATE users SET is_active = $2, updated_at = now() WHERE id = $1 RETURNING id, is_active, role`,
      [userId, body.isActive],
    );
    if (!updated.rows[0]) throw AppError.notFound('USER_NOT_FOUND', 'User not found');
    if (!body.isActive) {
      // Ends sessions at the next refresh. Access tokens expire within their short TTL.
      await deps.db.query('UPDATE refresh_tokens SET revoked_at = now() WHERE user_id = $1 AND revoked_at IS NULL', [userId]);
    }
    await deps.db.query(
      'INSERT INTO admin_audit_logs (actor_id, action, target, details) VALUES ($1,$2,$3,$4)',
      [actorId, body.isActive ? 'user.activate' : 'user.deactivate', `user:${userId}`, '{}'],
    );
    res.json({ user: { id: updated.rows[0].id, isActive: updated.rows[0].is_active, role: updated.rows[0].role } });
  });

  r.get('/ai/settings', async (_req, res) => {
    res.json({ settings: await deps.settings.getSettings() });
  });

  r.put('/ai/settings', validateBody(settingsPatchSchema), async (req, res) => {
    const settings = await deps.settings.updateSettings(req.auth!.userId, req.body);
    res.json({ settings });
  });

  r.post('/ai/settings/test', async (req, res) => {
    res.json({ result: await deps.settings.testConnection(req.auth!.userId, deps.gemini) });
  });

  r.get('/ai/features', async (_req, res) => {
    res.json({ items: await deps.settings.listFeatures() });
  });

  r.patch('/ai/features/:key', validateBody(featurePatchSchema), async (req, res) => {
    const key = String(req.params.key);
    if (!isAiFeatureKey(key)) throw AppError.notFound('AI_FEATURE_NOT_FOUND', 'Unknown AI feature');
    const body = req.body as z.infer<typeof featurePatchSchema>;
    const item = await deps.settings.updateFeature(req.auth!.userId, key, body);
    res.json({ item });
  });

  r.get('/ai/usage', validateQuery(usageQuerySchema), async (_req, res) => {
    const q = res.locals.query as z.infer<typeof usageQuerySchema>;
    res.json({ days: q.days, items: await deps.settings.usageSummary(q.days) });
  });

  r.get('/audit', validateQuery(auditQuerySchema), async (_req, res) => {
    const q = res.locals.query as z.infer<typeof auditQuerySchema>;
    res.json({ items: await deps.settings.recentAudit(q.limit) });
  });

  return r;
}
