import { createHash } from 'node:crypto';
import type { Env } from '../../config/env.js';
import type { Db } from '../../db/pool.js';
import { AppError } from '../../lib/errors.js';
import { logger } from '../../lib/logger.js';
import { detectImageMime, type LocalImageStorage } from '../../lib/storage.js';
import { FarmsService } from '../farms/farms.service.js';
import { resolvePlan, currentQuotaWindowStart } from '../subscriptions/plans.js';
import { KnowledgeService } from '../knowledge/knowledge.service.js';
import { GeminiVisionClient } from '../ai/gemini.client.js';
import { buildSystemPrompt, buildUserPrompt, PROMPT_VERSION, SAFETY_DISCLAIMER_FA, SEASON_FA, CATEGORY_FA } from '../ai/prompt.js';
import { applySafetyRules, confidenceLabelFa } from '../ai/safety.js';
import type { AiReport } from '../ai/report.schema.js';
import type { AiSettingsService } from '../ai/ai-settings.service.js';
import type { AnalysisCategory, AnalysisSeason } from './analyses.schemas.js';

export interface CreateAnalysisInput {
  userId: string;
  file: Buffer;
  category: AnalysisCategory;
  season: AnalysisSeason;
  farmId?: string | null;
  treeAgeYears?: number | null;
  location?: string | null;
  userNotes?: string | null;
}

interface AnalysisRow {
  id: string;
  category: AnalysisCategory;
  season: AnalysisSeason;
  status: 'pending' | 'completed' | 'failed';
  farm_id: string | null;
  image_id: string;
  tree_age_years: number | null;
  location_text: string | null;
  user_notes: string | null;
  primary_issue_slug: string | null;
  primary_title_fa: string | null;
  confidence: number | null;
  result: unknown;
  error_message: string | null;
  created_at: Date;
  completed_at: Date | null;
}

export const toAnalysisDto = (r: AnalysisRow, includeResult: boolean) => ({
  id: r.id,
  category: r.category,
  season: r.season,
  status: r.status,
  farmId: r.farm_id,
  imageId: r.image_id,
  treeAgeYears: r.tree_age_years,
  location: r.location_text,
  userNotes: r.user_notes,
  primaryIssueSlug: r.primary_issue_slug,
  primaryTitle: r.primary_title_fa,
  confidence: r.confidence,
  confidenceLabel: r.confidence === null ? null : confidenceLabelFa(r.confidence),
  errorMessage: r.status === 'failed' ? r.error_message : null,
  createdAt: new Date(r.created_at).toISOString(),
  completedAt: r.completed_at ? new Date(r.completed_at).toISOString() : null,
  ...(includeResult ? { report: r.result } : {}),
});

export interface AnalysisDeps {
  db: Db;
  env: Pick<Env, 'FREE_MONTHLY_ANALYSES' | 'FREE_MAX_FARMS' | 'GEMINI_MODEL' | 'MAX_UPLOAD_MB'>;
  storage: LocalImageStorage;
  knowledge: KnowledgeService;
  farms: FarmsService;
  ai: GeminiVisionClient;
  aiSettings: AiSettingsService;
}

export class AnalysesService {
  constructor(private readonly deps: AnalysisDeps) {}

  /** Usage for the current month against the plan limit. */
  async usage(userId: string) {
    const plan = await resolvePlan(this.deps.db, userId, this.deps.env);
    const used = await this.countThisMonth(userId);
    return {
      plan: plan.code,
      planName: plan.nameFa,
      monthlyLimit: plan.monthlyAnalyses,
      used,
      remaining: plan.monthlyAnalyses === null ? null : Math.max(0, plan.monthlyAnalyses - used),
      resetsAt: new Date(Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth() + 1, 1)).toISOString(),
    };
  }

  private async countThisMonth(userId: string): Promise<number> {
    const res = await this.deps.db.query<{ c: string }>(
      `SELECT count(*) AS c FROM analyses
        WHERE user_id = $1 AND status <> 'failed' AND created_at >= $2`,
      [userId, currentQuotaWindowStart()],
    );
    return Number(res.rows[0].c);
  }

  /**
   * Full analysis pipeline:
   *   quota check → store image → pending record → Gemini Vision → validate + safety → persist report.
   * Failed AI calls do not consume quota (failed rows are excluded from the count).
   */
  async create(input: CreateAnalysisInput) {
    const { db, env } = this.deps;

    const maxBytes = env.MAX_UPLOAD_MB * 1024 * 1024;
    if (input.file.length > maxBytes) throw AppError.payloadTooLarge(`Image must be smaller than ${env.MAX_UPLOAD_MB} MB`);
    const mime = detectImageMime(input.file);
    if (!mime) throw AppError.badRequest('UNSUPPORTED_IMAGE', 'Only JPEG, PNG or WEBP images are accepted');

    const plan = await resolvePlan(db, input.userId, env);
    if (plan.monthlyAnalyses !== null) {
      const used = await this.countThisMonth(input.userId);
      if (used >= plan.monthlyAnalyses) {
        throw AppError.quotaExceeded(
          `You have used all ${plan.monthlyAnalyses} analyses of your ${plan.nameFa} plan this month.`,
        );
      }
    }
    // Admin switches: the feature may be disabled, or use an admin-selected model. Throws before any upstream call.
    const aiFeature = await this.deps.aiSettings.resolveFeature('image_analysis');
    const dailyLimit = plan.code === 'premium' ? aiFeature.dailyLimitPremium : aiFeature.dailyLimitFree;
    if ((await this.deps.aiSettings.countUserCallsLast24h(input.userId, 'image_analysis')) >= dailyLimit) {
      throw new AppError(402, 'AI_QUOTA_EXCEEDED', `You have reached the daily limit of ${dailyLimit} analyses.`);
    }

    const farm = input.farmId ? await this.deps.farms.getOwned(input.userId, input.farmId) : null;

    const storageKey = await this.deps.storage.save(input.userId, input.file, mime);
    const sha = createHash('sha256').update(input.file).digest('hex');
    const image = await db.query<{ id: string }>(
      `INSERT INTO images (user_id, storage_key, mime_type, size_bytes, sha256)
       VALUES ($1,$2,$3,$4,$5) RETURNING id`,
      [input.userId, storageKey, mime, input.file.length, sha],
    );
    const analysis = await db.query<AnalysisRow>(
      `INSERT INTO analyses (user_id, farm_id, image_id, category, season, tree_age_years, location_text, user_notes, status, model, prompt_version)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,'pending',$9,$10) RETURNING *`,
      [
        input.userId,
        farm?.id ?? null,
        image.rows[0].id,
        input.category,
        input.season,
        input.treeAgeYears ?? farm?.average_tree_age ?? null,
        input.location ?? (farm ? `${farm.province}، ${farm.city}` : null),
        input.userNotes ?? null,
        env.GEMINI_MODEL,
        PROMPT_VERSION,
      ],
    );
    const row = analysis.rows[0];

    const started = Date.now();
    try {
      const catalog = await this.deps.knowledge.catalogForPrompt();
      const { report, model, inputTokens, outputTokens, latencyMs: aiLatency } = await this.deps.ai.analyze({
        image: input.file,
        mimeType: mime,
        model: aiFeature.model ?? undefined,
        maxOutputTokens: aiFeature.maxOutputTokens,
        temperature: aiFeature.temperature,
        systemPrompt: buildSystemPrompt(),
        userPrompt: buildUserPrompt({
          category: input.category,
          season: input.season,
          treeAgeYears: row.tree_age_years,
          location: row.location_text,
          userNotes: input.userNotes,
          farm: farm
            ? {
                name: farm.name,
                province: farm.province,
                city: farm.city,
                pistachioVariety: farm.pistachio_variety,
                irrigationMethod: farm.irrigation_method,
                soilType: farm.soil_type,
                soilNotes: farm.soil_notes,
              }
            : null,
          catalog,
        }),
      });

      await this.deps.aiSettings.recordUsage({
        userId: input.userId,
        feature: 'image_analysis',
        model,
        status: 'ok',
        inputTokens,
        outputTokens,
        latencyMs: aiLatency,
      });

      const { report: safe, flags } = applySafetyRules(report);
      const knownSlugs = new Set(catalog.map((c) => c.slug));
      const primarySlug = safe.diagnosis.knowledgeSlug && knownSlugs.has(safe.diagnosis.knowledgeSlug)
        ? safe.diagnosis.knowledgeSlug
        : null;
      const references = primarySlug ? await this.referencesFor(primarySlug) : [];

      const result = buildStoredReport(safe, {
        model,
        promptVersion: PROMPT_VERSION,
        category: input.category,
        season: input.season,
        primarySlug,
        references,
        safetyFlags: flags,
        latencyMs: Date.now() - started,
      });

      const updated = await db.query<AnalysisRow>(
        `UPDATE analyses SET status = 'completed', primary_issue_slug = $2, primary_title_fa = $3,
           confidence = $4, result = $5, latency_ms = $6, completed_at = now()
         WHERE id = $1 RETURNING *`,
        [
          row.id,
          primarySlug,
          safe.diagnosis.title,
          Math.round(safe.diagnosis.confidence),
          JSON.stringify(result),
          Date.now() - started,
        ],
      );
      return toAnalysisDto(updated.rows[0], true);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'unknown error';
      await this.deps.aiSettings.recordUsage({
        userId: input.userId,
        feature: 'image_analysis',
        model: aiFeature.model ?? env.GEMINI_MODEL,
        status: err instanceof AppError && err.code === 'AI_BLOCKED' ? 'blocked' : 'error',
        inputTokens: null,
        outputTokens: null,
        latencyMs: Date.now() - started,
        errorCode: err instanceof AppError ? err.code : 'UNKNOWN',
      });
      await db.query(
        `UPDATE analyses SET status = 'failed', error_message = $2, latency_ms = $3, completed_at = now() WHERE id = $1`,
        [row.id, message.slice(0, 500), Date.now() - started],
      );
      logger.error('analysis failed', { analysisId: row.id, error: message });
      throw err;
    }
  }

  private async referencesFor(slug: string) {
    const article = await this.deps.knowledge.get(slug);
    return article.references;
  }

  async list(userId: string, opts: { limit: number; cursor?: string; farmId?: string }) {
    const params: unknown[] = [userId];
    let where = `user_id = $1 AND deleted_at IS NULL`;
    if (opts.farmId) {
      params.push(opts.farmId);
      where += ` AND farm_id = $${params.length}`;
    }
    if (opts.cursor) {
      params.push(new Date(opts.cursor));
      where += ` AND created_at < $${params.length}`;
    }
    params.push(opts.limit + 1);
    const res = await this.deps.db.query<AnalysisRow>(
      `SELECT * FROM analyses WHERE ${where} ORDER BY created_at DESC LIMIT $${params.length}`,
      params,
    );
    const hasMore = res.rows.length > opts.limit;
    const rows = res.rows.slice(0, opts.limit);
    return {
      items: rows.map((r) => toAnalysisDto(r, false)),
      nextCursor: hasMore ? new Date(rows[rows.length - 1].created_at).toISOString() : null,
    };
  }

  async get(userId: string, analysisId: string) {
    const row = await this.loadOwned(userId, analysisId);
    return toAnalysisDto(row, true);
  }

  async remove(userId: string, analysisId: string): Promise<void> {
    await this.loadOwned(userId, analysisId);
    await this.deps.db.query('UPDATE analyses SET deleted_at = now() WHERE id = $1', [analysisId]);
  }

  /** Returns the stored image bytes and MIME type for the owner only. */
  async imageFor(userId: string, analysisId: string): Promise<{ data: Buffer; mime: string }> {
    const row = await this.loadOwned(userId, analysisId);
    const img = await this.deps.db.query<{ storage_key: string; mime_type: string }>(
      'SELECT storage_key, mime_type FROM images WHERE id = $1',
      [row.image_id],
    );
    const data = await this.deps.storage.read(img.rows[0].storage_key);
    return { data, mime: img.rows[0].mime_type };
  }

  private async loadOwned(userId: string, analysisId: string): Promise<AnalysisRow> {
    const res = await this.deps.db.query<AnalysisRow>(
      'SELECT * FROM analyses WHERE id = $1 AND user_id = $2 AND deleted_at IS NULL',
      [analysisId, userId],
    );
    if (!res.rows[0]) throw AppError.notFound('ANALYSIS_NOT_FOUND', 'Analysis not found');
    return res.rows[0];
  }
}

/** Builds the final, client-ready report object persisted in analyses.result. */
export function buildStoredReport(
  r: AiReport,
  meta: {
    model: string;
    promptVersion: string;
    category: AnalysisCategory;
    season: AnalysisSeason;
    primarySlug: string | null;
    references: Array<{ citation: string; url: string | null; doi: string | null; year: number | null; verified: boolean }>;
    safetyFlags: string[];
    latencyMs: number;
  },
) {
  return {
    schemaVersion: 1,
    summary: r.summary,
    category: { code: meta.category, label: CATEGORY_FA[meta.category] },
    season: { code: meta.season, label: SEASON_FA[meta.season] },
    imageQuality: r.imageQuality,
    detectedSubject: r.detectedSubject,
    diagnosis: {
      title: r.diagnosis.title,
      knowledgeSlug: meta.primarySlug,
      isHealthy: r.diagnosis.isHealthy,
      confidence: Math.round(r.diagnosis.confidence),
      confidenceLabel: confidenceLabelFa(r.diagnosis.confidence),
    },
    observedSymptoms: r.observedSymptoms,
    alternatives: r.alternatives.map((a) => ({ ...a, confidence: Math.round(a.confidence) })),
    recommendedActions: r.recommendedActions,
    additionalInfoNeeded: r.additionalInfoNeeded,
    references: meta.references,
    disclaimer: SAFETY_DISCLAIMER_FA,
    meta: {
      model: meta.model,
      promptVersion: meta.promptVersion,
      safetyFlags: meta.safetyFlags,
      latencyMs: meta.latencyMs,
      generatedAt: new Date().toISOString(),
    },
  };
}

