import { AppError } from '../../lib/errors.js';
import { logger } from '../../lib/logger.js';
import { aiReportSchema, geminiResponseSchema, type AiReport } from './report.schema.js';

export interface VisionRequest {
  image: Buffer;
  mimeType: 'image/jpeg' | 'image/png' | 'image/webp';
  systemPrompt: string;
  userPrompt: string;
}

export interface VisionResult {
  report: AiReport;
  model: string;
  latencyMs: number;
}

export type FetchLike = (input: string, init: RequestInit) => Promise<Response>;

export interface GeminiClientOptions {
  apiKey: string;
  model: string;
  timeoutMs: number;
  /** Injected in tests. */
  fetchImpl?: FetchLike;
  baseUrl?: string;
}

const DEFAULT_BASE = 'https://generativelanguage.googleapis.com/v1beta';

/**
 * Thin client for the Gemini `generateContent` REST API with a vision input.
 * The API key is sent in a header and never leaves the backend.
 */
export class GeminiVisionClient {
  private readonly fetchImpl: FetchLike;

  constructor(private readonly opts: GeminiClientOptions) {
    this.fetchImpl = opts.fetchImpl ?? ((url, init) => fetch(url, init));
  }

  async analyze(req: VisionRequest): Promise<VisionResult> {
    const started = Date.now();
    const maxAttempts = 2; // one retry when the model returns malformed JSON
    let lastError: unknown;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      const text = await this.generate(req, attempt);
      try {
        const parsed = aiReportSchema.parse(JSON.parse(stripCodeFence(text)));
        return { report: parsed, model: this.opts.model, latencyMs: Date.now() - started };
      } catch (err) {
        lastError = err;
        logger.warn('gemini returned invalid report', { attempt, error: (err as Error).message });
      }
    }
    throw new AppError(502, 'AI_INVALID_OUTPUT', 'The AI response could not be understood. Please try again.', {
      reason: lastError instanceof Error ? lastError.message : 'unknown',
    });
  }

  private async generate(req: VisionRequest, attempt: number): Promise<string> {
    const url = `${this.opts.baseUrl ?? DEFAULT_BASE}/models/${encodeURIComponent(this.opts.model)}:generateContent`;
    const body = {
      systemInstruction: { parts: [{ text: req.systemPrompt }] },
      contents: [
        {
          role: 'user',
          parts: [
            { inline_data: { mime_type: req.mimeType, data: req.image.toString('base64') } },
            { text: req.userPrompt },
          ],
        },
      ],
      generationConfig: {
        responseMimeType: 'application/json',
        responseSchema: geminiResponseSchema,
        temperature: attempt === 1 ? 0.2 : 0.1,
        topP: 0.8,
        maxOutputTokens: 4096,
      },
      safetySettings: [
        { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_LOW_AND_ABOVE' },
      ],
    };

    let res: Response;
    try {
      res = await this.fetchImpl(url, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'x-goog-api-key': this.opts.apiKey,
        },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(this.opts.timeoutMs),
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
    if (data.promptFeedback?.blockReason) {
      throw new AppError(422, 'AI_BLOCKED', 'The image could not be analyzed. Please send a different photo.');
    }
    const parts = data.candidates?.[0]?.content?.parts ?? [];
    const text = parts.map((p) => p.text ?? '').join('').trim();
    if (!text) throw AppError.upstream();
    return text;
  }
}

interface GeminiResponse {
  candidates?: Array<{ content?: { parts?: Array<{ text?: string }> }; finishReason?: string }>;
  promptFeedback?: { blockReason?: string };
}

/** Some model versions wrap JSON in ```json fences despite the MIME setting. */
export function stripCodeFence(text: string): string {
  const trimmed = text.trim();
  const fenced = /^```(?:json)?\s*([\s\S]*?)\s*```$/i.exec(trimmed);
  return fenced ? fenced[1] : trimmed;
}
