import { z } from 'zod';

export const analysisCategories = ['leaf', 'fruit_cluster', 'trunk', 'pest', 'soil'] as const;
export const analysisSeasons = ['spring', 'summer', 'autumn', 'winter'] as const;
export type AnalysisCategory = (typeof analysisCategories)[number];
export type AnalysisSeason = (typeof analysisSeasons)[number];

/** Fields submitted as multipart/form-data alongside the image. */
export const analysisFieldsSchema = z.object({
  category: z.enum(analysisCategories, { errorMap: () => ({ message: 'Invalid category' }) }),
  season: z.enum(analysisSeasons, { errorMap: () => ({ message: 'Invalid season' }) }),
  farmId: z.string().uuid().optional().or(z.literal('').transform(() => undefined)),
  treeAgeYears: z
    .union([z.string(), z.undefined()])
    .transform((v) => (v === undefined || v === '' ? undefined : Number(v)))
    .pipe(z.number().int().min(0).max(150).optional()),
  location: z.string().trim().max(200).optional().transform((v) => (v ? v : undefined)),
  userNotes: z.string().trim().max(1000).optional().transform((v) => (v ? v : undefined)),
});

export const listQuerySchema = z.object({
  limit: z.coerce.number().int().min(1).max(50).default(20),
  cursor: z.string().datetime().optional(),
  farmId: z.string().uuid().optional(),
});
