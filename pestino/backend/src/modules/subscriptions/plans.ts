import type { Env } from '../../config/env.js';
import type { Db } from '../../db/pool.js';

/**
 * Plan catalogue. Limits are the single source of truth for entitlements;
 * the mobile app only mirrors them for display.
 */
export type PlanCode = 'free' | 'premium';

export interface PlanLimits {
  code: PlanCode;
  nameFa: string;
  /** null = unlimited */
  monthlyAnalyses: number | null;
  /** null = unlimited */
  maxFarms: number | null;
  advancedReports: boolean;
  pdfExport: boolean;
}

export function planCatalog(env: Pick<Env, 'FREE_MONTHLY_ANALYSES' | 'FREE_MAX_FARMS'>): Record<PlanCode, PlanLimits> {
  return {
    free: {
      code: 'free',
      nameFa: 'رایگان',
      monthlyAnalyses: env.FREE_MONTHLY_ANALYSES,
      maxFarms: env.FREE_MAX_FARMS,
      advancedReports: false,
      pdfExport: false,
    },
    premium: {
      code: 'premium',
      nameFa: 'حرفه‌ای',
      monthlyAnalyses: null,
      maxFarms: 50,
      advancedReports: true,
      pdfExport: true,
    },
  };
}

/** Resolves the user's effective plan: an active, unexpired premium subscription or free. */
export async function resolvePlan(
  db: Db,
  userId: string,
  env: Pick<Env, 'FREE_MONTHLY_ANALYSES' | 'FREE_MAX_FARMS'>,
): Promise<PlanLimits> {
  const catalog = planCatalog(env);
  const res = await db.query<{ plan: PlanCode }>(
    `SELECT plan FROM subscriptions
      WHERE user_id = $1 AND status = 'active' AND plan = 'premium'
        AND (expires_at IS NULL OR expires_at > now())
      ORDER BY created_at DESC LIMIT 1`,
    [userId],
  );
  return res.rows[0] ? catalog.premium : catalog.free;
}

/** Start of the current calendar month in UTC (quota window). */
export function currentQuotaWindowStart(now: Date = new Date()): Date {
  return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1));
}
