import { z } from 'zod';

/**
 * Schema of the JSON the model must return. Every field is validated before
 * it reaches the database or the mobile client – model output is untrusted.
 */
export const aiReportSchema = z.object({
  imageQuality: z.object({
    usable: z.boolean(),
    issues: z.array(z.string().max(200)).max(6).default([]),
  }),
  detectedSubject: z.string().max(120).default('نامشخص'),
  diagnosis: z.object({
    knowledgeSlug: z.string().max(80).nullable().default(null),
    title: z.string().min(2).max(160),
    isHealthy: z.boolean().default(false),
    confidence: z.number().min(0).max(100),
  }),
  observedSymptoms: z.array(z.string().min(2).max(240)).max(10).default([]),
  alternatives: z
    .array(
      z.object({
        knowledgeSlug: z.string().max(80).nullable().default(null),
        title: z.string().min(2).max(160),
        confidence: z.number().min(0).max(100),
        reason: z.string().min(2).max(300),
      }),
    )
    .max(3)
    .default([]),
  recommendedActions: z
    .array(
      z.object({
        text: z.string().min(4).max(400),
        priority: z.enum(['immediate', 'soon', 'monitor']).default('soon'),
      }),
    )
    .max(8)
    .default([]),
  additionalInfoNeeded: z.array(z.string().min(4).max(240)).max(5).default([]),
  summary: z.string().min(10).max(800),
});

export type AiReport = z.infer<typeof aiReportSchema>;

/** JSON schema (OpenAPI subset) sent to Gemini via responseSchema to constrain output shape. */
export const geminiResponseSchema = {
  type: 'OBJECT',
  required: ['imageQuality', 'diagnosis', 'observedSymptoms', 'alternatives', 'recommendedActions', 'additionalInfoNeeded', 'summary'],
  properties: {
    imageQuality: {
      type: 'OBJECT',
      required: ['usable', 'issues'],
      properties: {
        usable: { type: 'BOOLEAN' },
        issues: { type: 'ARRAY', items: { type: 'STRING' } },
      },
    },
    detectedSubject: { type: 'STRING' },
    diagnosis: {
      type: 'OBJECT',
      required: ['title', 'isHealthy', 'confidence'],
      properties: {
        knowledgeSlug: { type: 'STRING', nullable: true },
        title: { type: 'STRING' },
        isHealthy: { type: 'BOOLEAN' },
        confidence: { type: 'NUMBER' },
      },
    },
    observedSymptoms: { type: 'ARRAY', items: { type: 'STRING' } },
    alternatives: {
      type: 'ARRAY',
      items: {
        type: 'OBJECT',
        required: ['title', 'confidence', 'reason'],
        properties: {
          knowledgeSlug: { type: 'STRING', nullable: true },
          title: { type: 'STRING' },
          confidence: { type: 'NUMBER' },
          reason: { type: 'STRING' },
        },
      },
    },
    recommendedActions: {
      type: 'ARRAY',
      items: {
        type: 'OBJECT',
        required: ['text', 'priority'],
        properties: {
          text: { type: 'STRING' },
          priority: { type: 'STRING', enum: ['immediate', 'soon', 'monitor'] },
        },
      },
    },
    additionalInfoNeeded: { type: 'ARRAY', items: { type: 'STRING' } },
    summary: { type: 'STRING' },
  },
} as const;
