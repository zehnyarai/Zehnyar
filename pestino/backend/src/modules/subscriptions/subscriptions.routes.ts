import { Router } from 'express';
import type { Env } from '../../config/env.js';
import type { Db } from '../../db/pool.js';
import { requireAuth } from '../../middleware/auth.js';
import { AppError } from '../../lib/errors.js';
import { planCatalog, resolvePlan } from './plans.js';

/**
 * Subscription endpoints.
 * - GET  /subscriptions/plans   public plan catalogue (for paywall UI)
 * - GET  /subscriptions/me      effective plan of the current user
 * - POST /subscriptions/checkout  reserved for the payment gateway (ZarinPal / IDPay)
 *                                or in-app purchase verification (Bazaar, Myket, Google Play, App Store).
 *                                Returns 501 until a provider adapter is configured.
 */
export function subscriptionsRoutes(deps: { db: Db; env: Pick<Env, 'FREE_MONTHLY_ANALYSES' | 'FREE_MAX_FARMS' | 'JWT_ACCESS_SECRET'> }): Router {
  const r = Router();

  r.get('/plans', (_req, res) => {
    res.json({ items: Object.values(planCatalog(deps.env)) });
  });

  r.use(requireAuth(deps.env.JWT_ACCESS_SECRET));

  r.get('/me', async (req, res) => {
    const plan = await resolvePlan(deps.db, req.auth!.userId, deps.env);
    res.json({ plan });
  });

  r.post('/checkout', (_req, _res, next) => {
    next(AppError.notImplemented('PAYMENT_NOT_CONFIGURED', 'Payment provider is not configured yet'));
  });

  return r;
}
