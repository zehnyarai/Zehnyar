import type { Env } from '../../config/env.js';
import type { Db } from '../../db/pool.js';
import { AppError } from '../../lib/errors.js';
import { logger } from '../../lib/logger.js';
import { decryptSecret, encryptSecret } from '../../lib/secretbox.js';
import type { GeminiRuntime, GeminiVisionClient } from './gemini.client.js';
import { AI_FEATURES, AI_FEATURE_KEYS, type AiFeatureDefinition, type AiFeatureKey } from './ai-features.js';
export type UsageStatus = 'ok' | 'error' | 'blocked' | 'unsafe_replaced';

export interface AiSettingsView {
  keySource: 'database' | 'environment' | 'none';
  keyConfigured: boolean;
  keyHint: string | null;
  defaultModel: string;
  defaultModelOverride: string | null;
  timeoutMs: number;
  aiEnabled: boolean;
  keyEncryptionConfigured: boolean;
}

export interface AiFeatureView {
  key: AiFeatureKey;
  titleFa: string;
  descriptionFa: string;
  kind: 'vision' | 'text';
  enabled: boolean;
  model: string | null;
  editablePrompt: boolean;
  systemPrompt: string | null;
  maxOutputTokens: number;
  temperature: number;
  dailyLimitFree: number;
  dailyLimitPremium: number;
  version: number;
  updatedAt: string | null;
}

export interface ResolvedFeature {
  key: AiFeatureKey;
  enabled: boolean;
  model: string | null;
  systemPrompt: string | null;
  maxOutputTokens: number;
  temperature: number;
  dailyLimitFree: number;
  dailyLimitPremium: number;
}

interface SettingsRow {
  gemini_api_key_enc: string | null;
  gemini_api_key_hint: string | null;
  default_model: string | null;
  timeout_ms: number | null;
  ai_enabled: boolean;
}

interface FeatureRow {
  feature_key: string;
  enabled: boolean;
  model: string | null;
  system_prompt: string | null;
  max_output_tokens: number;
  temperature: string;
  daily_limit_free: number;
  daily_limit_premium: number;
  version: number;
  updated_at: Date;
}

export interface FeaturePatch {
  enabled?: boolean;
  model?: string | null;
  systemPrompt?: string | null;
  maxOutputTokens?: number;
  temperature?: number;
  dailyLimitFree?: number;
  dailyLimitPremium?: number;
}

export interface SettingsPatch {
  apiKey?: string;
  clearApiKey?: boolean;
  defaultModel?: string | null;
  timeoutMs?: number | null;
  aiEnabled?: boolean;
}

/**
 * Admin-managed AI configuration with environment fallbacks.
 * Every Gemini call resolves the key, model and kill-switch through this service,
 * so changes made in the admin panel take effect immediately without a redeploy.
 */
export class AiSettingsService {
  constructor(
    private readonly db: Db,
    private readonly env: Pick<Env, 'GEMINI_API_KEY' | 'GEMINI_MODEL' | 'GEMINI_TIMEOUT_MS' | 'AI_SETTINGS_ENCRYPTION_KEY'>,
  ) {}

  // ---------------------------------------------------------------------------
  // Runtime (used by GeminiVisionClient on every call)
  // ---------------------------------------------------------------------------

  async resolveRuntime(): Promise<GeminiRuntime> {
    const row = await this.loadSettingsRow();
    if (!row.ai_enabled) {
      throw new AppError(503, 'AI_DISABLED', 'AI features are temporarily disabled.');
    }
    const apiKey = this.readApiKey(row);
    if (!apiKey) {
      throw new AppError(503, 'AI_NOT_CONFIGURED', 'AI service is not configured.');
    }
    return {
      apiKey,
      model: row.default_model ?? this.env.GEMINI_MODEL,
      timeoutMs: row.timeout_ms ?? this.env.GEMINI_TIMEOUT_MS,
    };
  }

  /** Feature switch and overrides. Throws when the feature is off so no upstream call is made. */
  async resolveFeature(key: AiFeatureKey): Promise<ResolvedFeature> {
    const def = AI_FEATURES[key];
    const res = await this.db.query<FeatureRow>('SELECT * FROM ai_feature_configs WHERE feature_key = $1', [key]);
    const row = res.rows[0];
    const resolved: ResolvedFeature = {
      key,
      enabled: row?.enabled ?? true,
      model: row?.model ?? null,
      systemPrompt: row?.system_prompt ?? null,
      maxOutputTokens: row?.max_output_tokens ?? def.defaults.maxOutputTokens,
      temperature: row ? Number(row.temperature) : def.defaults.temperature,
      dailyLimitFree: row?.daily_limit_free ?? def.defaults.dailyLimitFree,
      dailyLimitPremium: row?.daily_limit_premium ?? def.defaults.dailyLimitPremium,
    };
    if (!resolved.enabled) {
      throw new AppError(403, 'AI_FEATURE_DISABLED', 'This AI feature is currently disabled.');
    }
    return resolved;
  }

  // ---------------------------------------------------------------------------
  // Admin: settings
  // ---------------------------------------------------------------------------

  async getSettings(): Promise<AiSettingsView> {
    const row = await this.loadSettingsRow();
    const dbKey = row.gemini_api_key_enc ? this.tryReadDbKey(row.gemini_api_key_enc) : null;
    const keySource: AiSettingsView['keySource'] = dbKey ? 'database' : this.env.GEMINI_API_KEY ? 'environment' : 'none';
    return {
      keySource,
      keyConfigured: keySource !== 'none',
      keyHint: keySource === 'database' ? row.gemini_api_key_hint : keySource === 'environment' ? maskHint(this.env.GEMINI_API_KEY) : null,
      defaultModel: row.default_model ?? this.env.GEMINI_MODEL,
      defaultModelOverride: row.default_model,
      timeoutMs: row.timeout_ms ?? this.env.GEMINI_TIMEOUT_MS,
      aiEnabled: row.ai_enabled,
      keyEncryptionConfigured: Boolean(this.env.AI_SETTINGS_ENCRYPTION_KEY),
    };
  }

  async updateSettings(actorId: string, patch: SettingsPatch): Promise<AiSettingsView> {
    const sets: string[] = [];
    const values: unknown[] = [];
    const push = (col: string, value: unknown) => {
      values.push(value);
      sets.push(`${col} = $${values.length}`);
    };

    if (patch.apiKey !== undefined) {
      if (!this.env.AI_SETTINGS_ENCRYPTION_KEY) {
        throw AppError.badRequest(
          'ENCRYPTION_NOT_CONFIGURED',
          'AI_SETTINGS_ENCRYPTION_KEY must be configured on the server before storing an API key.',
        );
      }
      push('gemini_api_key_enc', encryptSecret(patch.apiKey, this.env.AI_SETTINGS_ENCRYPTION_KEY));
      push('gemini_api_key_hint', patch.apiKey.slice(-4));
    }
    if (patch.clearApiKey) {
      push('gemini_api_key_enc', null);
      push('gemini_api_key_hint', null);
    }
    if (patch.defaultModel !== undefined) push('default_model', patch.defaultModel);
    if (patch.timeoutMs !== undefined) push('timeout_ms', patch.timeoutMs);
    if (patch.aiEnabled !== undefined) push('ai_enabled', patch.aiEnabled);

    if (sets.length) {
      values.push(actorId);
      sets.push(`updated_by = $${values.length}`, 'updated_at = now()');
      await this.db.query(`UPDATE ai_settings SET ${sets.join(', ')} WHERE id = 1`, values);
      await this.audit(actorId, 'ai_settings.update', 'ai_settings', {
        changed: Object.keys(patch).filter((k) => k !== 'apiKey'),
        apiKeyChanged: patch.apiKey !== undefined || Boolean(patch.clearApiKey),
      });
    }
    return this.getSettings();
  }

  /** Sends a minimal prompt with the effective configuration. Returns status and latency only. */
  async testConnection(actorId: string, client: GeminiVisionClient): Promise<{ ok: boolean; model: string; latencyMs: number; errorCode?: string }> {
    const rt = await this.resolveRuntime();
    const started = Date.now();
    try {
      const out = await client.generateText({
        systemPrompt: 'Reply with one word.',
        userPrompt: 'سلام',
        maxOutputTokens: 16,
        temperature: 0,
      });
      await this.recordUsage({ userId: actorId, feature: 'admin_connection_test', model: out.model, status: 'ok', inputTokens: out.inputTokens, outputTokens: out.outputTokens, latencyMs: out.latencyMs });
      await this.audit(actorId, 'ai_settings.test', 'ai_settings', { ok: true });
      return { ok: true, model: out.model, latencyMs: out.latencyMs };
    } catch (err) {
      const code = err instanceof AppError ? err.code : 'UNKNOWN';
      await this.recordUsage({ userId: actorId, feature: 'admin_connection_test', model: rt.model, status: 'error', inputTokens: null, outputTokens: null, latencyMs: Date.now() - started, errorCode: code });
      await this.audit(actorId, 'ai_settings.test', 'ai_settings', { ok: false, code });
      return { ok: false, model: rt.model, latencyMs: Date.now() - started, errorCode: code };
    }
  }

  // ---------------------------------------------------------------------------
  // Admin: features
  // ---------------------------------------------------------------------------

  async listFeatures(): Promise<AiFeatureView[]> {
    const res = await this.db.query<FeatureRow>('SELECT * FROM ai_feature_configs');
    const byKey = new Map(res.rows.map((r) => [r.feature_key, r]));
    return AI_FEATURE_KEYS.map((key) => toFeatureView(AI_FEATURES[key], byKey.get(key) ?? null));
  }

  async updateFeature(actorId: string, key: AiFeatureKey, patch: FeaturePatch): Promise<AiFeatureView> {
    const def = AI_FEATURES[key];
    if (patch.systemPrompt !== undefined && patch.systemPrompt !== null && !def.editablePrompt) {
      throw AppError.badRequest('PROMPT_NOT_EDITABLE', 'The system prompt of this feature is managed by the platform.');
    }
    const current = await this.db.query<FeatureRow>('SELECT * FROM ai_feature_configs WHERE feature_key = $1', [key]);
    const base = current.rows[0] ?? null;
    const merged = toFeatureView(def, base);

    const next = {
      enabled: patch.enabled ?? merged.enabled,
      model: patch.model !== undefined ? patch.model : merged.model,
      system_prompt: patch.systemPrompt !== undefined ? patch.systemPrompt : merged.systemPrompt,
      max_output_tokens: patch.maxOutputTokens ?? merged.maxOutputTokens,
      temperature: patch.temperature ?? merged.temperature,
      daily_limit_free: patch.dailyLimitFree ?? merged.dailyLimitFree,
      daily_limit_premium: patch.dailyLimitPremium ?? merged.dailyLimitPremium,
    };

    const res = await this.db.query<FeatureRow>(
      `INSERT INTO ai_feature_configs
         (feature_key, enabled, model, system_prompt, max_output_tokens, temperature, daily_limit_free, daily_limit_premium, version, updated_by, updated_at)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8, 1, $9, now())
       ON CONFLICT (feature_key) DO UPDATE SET
         enabled = EXCLUDED.enabled, model = EXCLUDED.model, system_prompt = EXCLUDED.system_prompt,
         max_output_tokens = EXCLUDED.max_output_tokens, temperature = EXCLUDED.temperature,
         daily_limit_free = EXCLUDED.daily_limit_free, daily_limit_premium = EXCLUDED.daily_limit_premium,
         version = ai_feature_configs.version + 1, updated_by = EXCLUDED.updated_by, updated_at = now()
       RETURNING *`,
      [key, next.enabled, next.model, next.system_prompt, next.max_output_tokens, next.temperature, next.daily_limit_free, next.daily_limit_premium, actorId],
    );
    await this.audit(actorId, 'ai_feature.update', key, { changed: Object.keys(patch), promptChanged: patch.systemPrompt !== undefined });
    return toFeatureView(def, res.rows[0]);
  }

  // ---------------------------------------------------------------------------
  // Usage & audit
  // ---------------------------------------------------------------------------

  async recordUsage(e: {
    userId: string | null;
    feature: string;
    model: string;
    status: UsageStatus;
    inputTokens: number | null;
    outputTokens: number | null;
    latencyMs: number;
    errorCode?: string;
  }): Promise<void> {
    try {
      await this.db.query(
        `INSERT INTO ai_usage_logs (user_id, feature_key, model, status, input_tokens, output_tokens, latency_ms, error_code)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8)`,
        [e.userId, e.feature, e.model.slice(0, 80), e.status, e.inputTokens, e.outputTokens, e.latencyMs, e.errorCode ?? null],
      );
    } catch (err) {
      // Metering must never break the user's request.
      logger.warn('ai usage log failed', { error: (err as Error).message });
    }
  }

  /** Calls made by a user for a feature in the last 24 hours (rolling window). */
  async countUserCallsLast24h(userId: string, feature: string): Promise<number> {
    const res = await this.db.query<{ n: string }>(
      `SELECT count(*)::text AS n FROM ai_usage_logs
        WHERE user_id = $1 AND feature_key = $2 AND created_at > now() - interval '24 hours'
          AND status IN ('ok', 'unsafe_replaced')`,
      [userId, feature],
    );
    return Number(res.rows[0].n);
  }

  async usageSummary(days: number) {
    const res = await this.db.query<{
      feature_key: string;
      status: string;
      calls: string;
      input_tokens: string | null;
      output_tokens: string | null;
      avg_latency_ms: string | null;
    }>(
      `SELECT feature_key, status, count(*)::text AS calls,
              sum(input_tokens)::text AS input_tokens, sum(output_tokens)::text AS output_tokens,
              round(avg(latency_ms))::text AS avg_latency_ms
         FROM ai_usage_logs
        WHERE created_at > now() - ($1 || ' days')::interval
        GROUP BY feature_key, status
        ORDER BY feature_key, status`,
      [String(days)],
    );
    return res.rows.map((r) => ({
      feature: r.feature_key,
      status: r.status,
      calls: Number(r.calls),
      inputTokens: Number(r.input_tokens ?? 0),
      outputTokens: Number(r.output_tokens ?? 0),
      avgLatencyMs: Number(r.avg_latency_ms ?? 0),
    }));
  }

  async audit(actorId: string | null, action: string, target: string | null, details: Record<string, unknown>) {
    await this.db.query(
      'INSERT INTO admin_audit_logs (actor_id, action, target, details) VALUES ($1,$2,$3,$4)',
      [actorId, action, target, JSON.stringify(details)],
    );
  }

  async recentAudit(limit: number) {
    const res = await this.db.query<{ id: string; actor_id: string | null; action: string; target: string | null; details: unknown; created_at: Date }>(
      'SELECT id, actor_id, action, target, details, created_at FROM admin_audit_logs ORDER BY id DESC LIMIT $1',
      [limit],
    );
    return res.rows.map((r) => ({ id: Number(r.id), actorId: r.actor_id, action: r.action, target: r.target, details: r.details, createdAt: r.created_at.toISOString() }));
  }

  // ---------------------------------------------------------------------------
  // Internals
  // ---------------------------------------------------------------------------

  private async loadSettingsRow(): Promise<SettingsRow> {
    const res = await this.db.query<SettingsRow>(
      'SELECT gemini_api_key_enc, gemini_api_key_hint, default_model, timeout_ms, ai_enabled FROM ai_settings WHERE id = 1',
    );
    return res.rows[0];
  }

  private tryReadDbKey(payload: string): string | null {
    if (!this.env.AI_SETTINGS_ENCRYPTION_KEY) return null;
    try {
      return decryptSecret(payload, this.env.AI_SETTINGS_ENCRYPTION_KEY);
    } catch {
      logger.error('stored Gemini key could not be decrypted; check AI_SETTINGS_ENCRYPTION_KEY');
      return null;
    }
  }

  /** Database key wins over environment. An unreadable stored key is an error, not a silent fallback. */
  private readApiKey(row: SettingsRow): string | null {
    if (row.gemini_api_key_enc) {
      const key = this.tryReadDbKey(row.gemini_api_key_enc);
      if (!key) throw new AppError(503, 'AI_KEY_UNREADABLE', 'AI service is not configured correctly.');
      return key;
    }
    return this.env.GEMINI_API_KEY || null;
  }
}

function toFeatureView(def: AiFeatureDefinition, row: FeatureRow | null): AiFeatureView {
  return {
    key: def.key,
    titleFa: def.titleFa,
    descriptionFa: def.descriptionFa,
    kind: def.kind,
    enabled: row?.enabled ?? true,
    model: row?.model ?? null,
    editablePrompt: def.editablePrompt,
    systemPrompt: row?.system_prompt ?? null,
    maxOutputTokens: row?.max_output_tokens ?? def.defaults.maxOutputTokens,
    temperature: row ? Number(row.temperature) : def.defaults.temperature,
    dailyLimitFree: row?.daily_limit_free ?? def.defaults.dailyLimitFree,
    dailyLimitPremium: row?.daily_limit_premium ?? def.defaults.dailyLimitPremium,
    version: row?.version ?? 0,
    updatedAt: row?.updated_at ? row.updated_at.toISOString() : null,
  };
}

function maskHint(key: string): string {
  return key.slice(-4);
}
