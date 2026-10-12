import { Router } from 'express';
import { z } from 'zod';
import { requireAuth } from '../../middleware/auth.js';
import { validateBody } from '../../middleware/validate.js';
import { AiAssistService } from './ai-assist.service.js';
import type { AiSettingsService } from './ai-settings.service.js';

const assistSchema = z.object({
  feature: z.enum(['farm_form_help', 'report_explain']),
  field: z.string().trim().min(1).max(60),
  value: z.string().trim().min(1).max(500),
  context: z
    .object({
      province: z.string().trim().max(80).nullable().optional(),
      city: z.string().trim().max(80).nullable().optional(),
      pistachioVariety: z.string().trim().max(80).nullable().optional(),
      treeAgeYears: z.number().int().min(0).max(300).nullable().optional(),
      irrigationMethod: z.string().trim().max(80).nullable().optional(),
      soilType: z.string().trim().max(80).nullable().optional(),
    })
    .optional(),
});

/**
 * User-facing AI endpoints.
 * - GET  /ai/features  which AI helpers are currently on (for the UI to show or hide buttons)
 * - POST /ai/assist    field help or report explanation (text only, never a raw model passthrough)
 */
export function aiRoutes(deps: {
  assist: AiAssistService;
  settings: AiSettingsService;
  jwtSecret: string;
}): Router {
  const r = Router();
  r.use(requireAuth(deps.jwtSecret));

  r.get('/features', async (_req, res) => {
    const items = (await deps.settings.listFeatures())
      .filter((f) => f.kind === 'text')
      .map((f) => ({ key: f.key, titleFa: f.titleFa, enabled: f.enabled }));
    res.json({ items });
  });

  r.post('/assist', validateBody(assistSchema), async (req, res) => {
    res.json(await deps.assist.assist(req.auth!.userId, req.body as z.infer<typeof assistSchema>));
  });

  return r;
}
