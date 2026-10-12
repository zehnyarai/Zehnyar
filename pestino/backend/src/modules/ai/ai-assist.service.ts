import type { Env } from '../../config/env.js';
import type { Db } from '../../db/pool.js';
import { AppError } from '../../lib/errors.js';
import { resolvePlan } from '../subscriptions/plans.js';
import type { AiSettingsService } from './ai-settings.service.js';
import { DEFAULT_TEXT_PROMPTS, TEXT_SAFETY_RULES_FA, type AiFeatureKey } from './ai-features.js';
import type { GeminiVisionClient } from './gemini.client.js';
import { SAFETY_DISCLAIMER_FA } from './prompt.js';
import { SAFE_CHEMICAL_ADVICE_FA, isUnsafeAdvice } from './safety.js';

export type TextAssistFeature = Extract<AiFeatureKey, 'farm_form_help' | 'report_explain'>;

export interface AssistInput {
  feature: TextAssistFeature;
  field: string;
  value: string;
  context?: {
    province?: string | null;
    city?: string | null;
    pistachioVariety?: string | null;
    treeAgeYears?: number | null;
    irrigationMethod?: string | null;
    soilType?: string | null;
  };
}

export interface AssistResult {
  feature: TextAssistFeature;
  text: string;
  model: string;
  disclaimer: string;
  flags: string[];
  remainingToday: number | null;
}

/**
 * Text-only AI assistance for the app (field hints, report explanations).
 * Enforces the admin feature switch, per-plan daily limits, the non-removable safety rules,
 * and a post-generation filter that replaces any pesticide dosage or dangerous instruction.
 */
export class AiAssistService {
  constructor(
    private readonly deps: {
      db: Db;
      env: Pick<Env, 'FREE_MONTHLY_ANALYSES' | 'FREE_MAX_FARMS'>;
      settings: AiSettingsService;
      gemini: GeminiVisionClient;
    },
  ) {}

  async assist(userId: string, input: AssistInput): Promise<AssistResult> {
    const { settings, gemini, db, env } = this.deps;
    const feature = await settings.resolveFeature(input.feature);

    const plan = await resolvePlan(db, userId, env);
    const limit = plan.code === 'premium' ? feature.dailyLimitPremium : feature.dailyLimitFree;
    const used = await settings.countUserCallsLast24h(userId, input.feature);
    if (used >= limit) {
      throw new AppError(402, 'AI_QUOTA_EXCEEDED', `You have reached the daily limit of ${limit} requests for this feature.`);
    }

    const base = feature.systemPrompt?.trim() || DEFAULT_TEXT_PROMPTS[input.feature];
    const systemPrompt = `${base}\n\n${TEXT_SAFETY_RULES_FA}`;
    const userPrompt = buildAssistPrompt(input);

    let out;
    try {
      out = await gemini.generateText({
        systemPrompt,
        userPrompt,
        model: feature.model ?? undefined,
        maxOutputTokens: feature.maxOutputTokens,
        temperature: feature.temperature,
      });
    } catch (err) {
      await settings.recordUsage({
        userId,
        feature: input.feature,
        model: feature.model ?? 'default',
        status: err instanceof AppError && err.code === 'AI_BLOCKED' ? 'blocked' : 'error',
        inputTokens: null,
        outputTokens: null,
        latencyMs: 0,
        errorCode: err instanceof AppError ? err.code : 'UNKNOWN',
      });
      throw err;
    }

    let text = out.text;
    let status: 'ok' | 'unsafe_replaced' = 'ok';
    const flags: string[] = [];
    if (isUnsafeAdvice(text)) {
      text = SAFE_CHEMICAL_ADVICE_FA;
      status = 'unsafe_replaced';
      flags.push('UNSAFE_ADVICE_REPLACED');
    }

    await settings.recordUsage({
      userId,
      feature: input.feature,
      model: out.model,
      status,
      inputTokens: out.inputTokens,
      outputTokens: out.outputTokens,
      latencyMs: out.latencyMs,
    });

    return {
      feature: input.feature,
      text,
      model: out.model,
      disclaimer: SAFETY_DISCLAIMER_FA,
      flags,
      remainingToday: Math.max(0, limit - used - 1),
    };
  }
}

/** Builds the user turn. Free text is wrapped and labelled so it is treated as data, not instructions. */
export function buildAssistPrompt(input: AssistInput): string {
  const lines = [`فیلد: ${input.field}`, `مقدار وارد شده (داده کاربر): «${input.value}»`];
  const c = input.context ?? {};
  if (c.province || c.city) lines.push(`موقعیت: ${[c.province, c.city].filter(Boolean).join('، ')}`);
  if (c.pistachioVariety) lines.push(`رقم: ${c.pistachioVariety}`);
  if (c.treeAgeYears != null) lines.push(`سن درخت: ${c.treeAgeYears} سال`);
  if (c.irrigationMethod) lines.push(`آبیاری: ${c.irrigationMethod}`);
  if (c.soilType) lines.push(`خاک: ${c.soilType}`);
  return lines.join('\n');
}
