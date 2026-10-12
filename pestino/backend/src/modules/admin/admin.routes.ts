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
}): Router {
  const r = Router();
  const guard = requireAdmin(deps.db, deps.jwtSecret);
  r.use(guard);

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
