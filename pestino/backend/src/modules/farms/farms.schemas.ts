import { z } from 'zod';

export const IRRIGATION_METHODS = ['drip', 'flood', 'sprinkler', 'micro_sprinkler', 'rainfed', 'other'] as const;
export type IrrigationMethod = (typeof IRRIGATION_METHODS)[number];

const optionalText = (max: number) =>
  z
    .string()
    .trim()
    .max(max)
    .nullish()
    .transform((v) => (v === '' ? null : v ?? null));

export const farmInputSchema = z
  .object({
    name: z.string().trim().min(2, 'Farm name is too short').max(120),
    province: z.string().trim().min(2).max(80),
    city: z.string().trim().min(2).max(80),
    latitude: z.number().min(-90).max(90).nullish().transform((v) => v ?? null),
    longitude: z.number().min(-180).max(180).nullish().transform((v) => v ?? null),
    areaHectares: z.number().nonnegative().max(100_000).nullish().transform((v) => v ?? null),
    pistachioVariety: optionalText(80),
    averageTreeAge: z.number().int().min(0).max(150).nullish().transform((v) => v ?? null),
    irrigationMethod: z.enum(IRRIGATION_METHODS).nullish().transform((v) => v ?? null),
    soilType: optionalText(40),
    soilNotes: optionalText(1000),
  })
  .strict();

export const farmUpdateSchema = farmInputSchema.partial();

export type FarmInput = z.infer<typeof farmInputSchema>;

export const treeInputSchema = z
  .object({
    label: z.string().trim().min(1).max(80),
    plantedYear: z.number().int().min(1300).max(1500).nullish().transform((v) => v ?? null),
    variety: optionalText(80),
  })
  .strict();

export const idParamSchema = z.string().uuid('Invalid id');
