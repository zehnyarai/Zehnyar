import { Router } from 'express';
import { z } from 'zod';
import { requireAuth } from '../../middleware/auth.js';
import { validateQuery } from '../../middleware/validate.js';
import { KNOWLEDGE_KINDS, KnowledgeService } from './knowledge.service.js';

const listSchema = z.object({
  kind: z.enum(KNOWLEDGE_KINDS).optional(),
  q: z.string().trim().max(80).optional(),
});

export function knowledgeRoutes(deps: { knowledge: KnowledgeService; jwtSecret: string }): Router {
  const r = Router();
  r.use(requireAuth(deps.jwtSecret));

  r.get('/', validateQuery(listSchema), async (_req, res) => {
    const q = res.locals.query as z.infer<typeof listSchema>;
    res.json({ items: await deps.knowledge.list(q) });
  });

  r.get('/:slug', async (req, res) => {
    if (!/^[a-z0-9-]{3,80}$/.test(req.params.slug)) {
      return res.status(400).json({ error: { code: 'INVALID_SLUG', message: 'Invalid slug' } });
    }
    res.json({ article: await deps.knowledge.get(req.params.slug) });
  });

  return r;
}
