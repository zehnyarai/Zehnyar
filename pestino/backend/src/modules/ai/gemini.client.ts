import { AppError } from '../../lib/errors.js';
import { logger } from '../../lib/logger.js';
import { aiReportSchema, geminiResponseSchema, type AiReport } from './report.schema.js';

export interface VisionRequest {
  image: Buffer;
  mimeType: 'image/jpeg' | 'image/png' | 'image/webp';
  systemPrompt: string;
  userPrompt: string;
  /** Overrides the runtime model for this call (per-feature admin setting). */
  model?: string;
  maxOutputTokens?: number;
  temperature?: number;
}

export interface TextRequest {
  systemPrompt: string;
  userPrompt: string;
  model?: string;
  maxOutputTokens: number;
  temperature: number;
}

export interface TextResult {
  text: string;
  model: string;
  latencyMs: number;
  inputTokens: number | null;
  outputTokens: number | null;
}

export interface VisionResult {
  report: AiReport;
  model: string;
  latencyMs: number;
  inputTokens: number | null;
  outputTokens: number | null;
}

export type FetchLike = (input: string, init: RequestInit) => Promise<Response>;

/** Runtime settings resolved on every call (admin-managed, falling back to environment). */
export interface GeminiRuntime {
  apiKey: string;
  model: string;
  timeoutMs: number;
}

export interface GeminiClientOptions {
  apiKey: string;
  model: string;
  timeoutMs: number;
  /** Injected in tests. */
  fetchImpl?: FetchLike;
  baseUrl?: string;
  /** When provided, replaces the static apiKey/model/timeoutMs on every call (admin-managed settings). */
  runtime?: () => Promise<GeminiRuntime>;
}

const DEFAULT_BASE = 'https://generativelanguage.googleapis.com/v1beta';

interface UpstreamResult {
  text: string;
  model: string;
  latencyMs: number;
  inputTokens: number | null;
  outputTokens: number | null;
}

export class GeminiVisionClient {
  private readonly fetchImpl: FetchLike;

  constructor(private readonly opts: GeminiClientOptions) {
    this.fetchImpl = opts.fetchImpl ?? ((url, init) => fetch(url, init));
  }

  private async resolveRuntime(): Promise<GeminiRuntime> {
    if (this.opts.runtime) return this.opts.runtime();
    return { apiKey: this.opts.apiKey, model: this.opts.model, timeoutMs: this.opts.timeoutMs };
  }

  async analyze(req: VisionRequest): Promise<VisionResult> {
    const started = Date.now();
    const maxAttempts = 2; // one retry when the model returns malformed JSON
    let lastError: unknown;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      const up = await this.generate(req, attempt);
      try {
        const parsed = aiReportSchema.parse(JSON.parse(stripCodeFence(up.text)));
        return {
          report: parsed,
          model: up.model,
          latencyMs: Date.now() - started,
          inputTokens: up.inputTokens,
          outputTokens: up.outputTokens,
        };
      } catch (err) {
        lastError = err;
        logger.warn('gemini returned invalid report', { attempt, error: (err as Error).message });
      }
    }
    throw new AppError(502, 'AI_INVALID_OUTPUT', 'The AI response could not be understood. Please try again.', {
      reason: lastError instanceof Error ? lastError.message : 'unknown',
    });
  }

  /** Plain-text generation (used for field assistance and explanations). */
  async generateText(req: TextRequest): Promise<TextResult> {
    const up = await this.send({
      systemInstruction: req.systemPrompt,
      parts: [{ text: req.userPrompt }],
      model: req.model,
      generationConfig: { temperature: req.temperature, topP: 0.8, maxOutputTokens: req.maxOutputTokens },
    });
    return { text: up.text, model: up.model, latencyMs: up.latencyMs, inputTokens: up.inputTokens, outputTokens: up.outputTokens };
  }

  private async generate(req: VisionRequest, attempt: number): Promise<UpstreamResult> {
    return this.send({
      systemInstruction: req.systemPrompt,
      parts: [
        { inline_data: { mime_type: req.mimeType, data: req.image.toString('base64') } },
        { text: req.userPrompt },
      ],
      model: req.model,
      generationConfig: {
        responseMimeType: 'application/json',
        responseSchema: geminiResponseSchema,
        temperature: req.temperature ?? (attempt === 1 ? 0.2 : 0.1),
        topP: 0.8,
        maxOutputTokens: req.maxOutputTokens ?? 4096,
      },
      safetySettings: [{ category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_LOW_AND_ABOVE' }],
    });
  }

  private async send(input: {
    systemInstruction: string;
    parts: Array<Record<string, unknown>>;
    model?: string;
    generationConfig: Record<string, unknown>;
    safetySettings?: Array<Record<string, unknown>>;
  }): Promise<UpstreamResult> {
    const rt = await this.resolveRuntime();
    const model = input.model || rt.model;
    const started = Date.now();
    const url = `${this.opts.baseUrl ?? DEFAULT_BASE}/models/${encodeURIComponent(model)}:generateContent`;
    const body = {
      systemInstruction: { parts: [{ text: input.systemInstruction }] },
      contents: [{ role: 'user', parts: input.parts }],
      generationConfig: input.generationConfig,
      ...(input.safetySettings ? { safetySettings: input.safetySettings } : {}),
    };

    let res: Response;
    try {
      res = await this.fetchImpl(url, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          // The key is sent in a header only; it is never logged or returned to clients.
          'x-goog-api-key': rt.apiKey,
        },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(rt.timeoutMs),
      });
    } catch (err) {
      logger.error('gemini request failed', { error: (err as Error).name });
      throw AppError.upstream();
    }

    if (!res.ok) {
      const errText = await res.text().catch(() => '');
      logger.error('gemini http error', { status: res.status, body: errText.slice(0, 300) });
      throw AppError.upstream();
    }

    const data = (await res.json()) as GeminiResponse;
    const usage = { i: data.usageMetadata?.promptTokenCount ?? null, o: data.usageMetadata?.candidatesTokenCount ?? null };
    if (data.promptFeedback?.blockReason) {
      throw new AppError(422, 'AI_BLOCKED', 'The request could not be processed. Please try different input.');
    }
    const parts = data.candidates?.[0]?.content?.parts ?? [];
    const text = parts.map((p) => p.text ?? '').join('').trim();
    if (!text) {
      throw AppError.upstream();
    }
    return { text, model, latencyMs: Date.now() - started, inputTokens: usage.i, outputTokens: usage.o };
  }
}

interface GeminiResponse {
  candidates?: Array<{ content?: { parts?: Array<{ text?: string }> }; finishReason?: string }>;
  promptFeedback?: { blockReason?: string };
  usageMetadata?: { promptTokenCount?: number; candidatesTokenCount?: number };
}

/** Some model versions wrap JSON in ```json fences despite the MIME setting. */
export function stripCodeFence(text: string): string {
  const trimmed = text.trim();
  const fenced = /^```(?:json)?\s*([\s\S]*?)\s*```$/i.exec(trimmed);
  return fenced ? fenced[1] : trimmed;
}
