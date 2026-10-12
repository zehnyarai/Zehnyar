import { Router } from 'express';
import { requireAuth } from '../../middleware/auth.js';
import { validateBody } from '../../middleware/validate.js';
import { AppError } from '../../lib/errors.js';
import { FarmsService } from './farms.service.js';
import { farmInputSchema, farmUpdateSchema, idParamSchema, treeInputSchema } from './farms.schemas.js';

function parseId(raw: string | string[] | undefined): string {
  const parsed = idParamSchema.safeParse(Array.isArray(raw) ? raw[0] : raw);
  if (!parsed.success) throw AppError.badRequest('INVALID_ID', 'Invalid id');
  return parsed.data;
}

export function farmsRoutes(deps: { farms: FarmsService; jwtSecret: string }): Router {
  const r = Router();
  r.use(requireAuth(deps.jwtSecret));
  const uid = (req: { auth?: { userId: string } }) => req.auth!.userId;

  r.get('/', async (req, res) => {
    res.json({ items: await deps.farms.list(uid(req)) });
  });

  r.post('/', validateBody(farmInputSchema), async (req, res) => {
    res.status(201).json({ farm: await deps.farms.create(uid(req), req.body) });
  });

  r.get('/:farmId', async (req, res) => {
    res.json({ farm: await deps.farms.get(uid(req), parseId(req.params.farmId)) });
  });

  r.patch('/:farmId', validateBody(farmUpdateSchema), async (req, res) => {
    res.json({ farm: await deps.farms.update(uid(req), parseId(req.params.farmId), req.body) });
  });

  r.delete('/:farmId', async (req, res) => {
    await deps.farms.remove(uid(req), parseId(req.params.farmId));
    res.status(204).end();
  });

  r.get('/:farmId/trees', async (req, res) => {
    res.json({ items: await deps.farms.listTrees(uid(req), parseId(req.params.farmId)) });
  });

  r.post('/:farmId/trees', validateBody(treeInputSchema), async (req, res) => {
    const tree = await deps.farms.addTree(uid(req), parseId(req.params.farmId), req.body);
    res.status(201).json({ tree });
  });

  r.delete('/:farmId/trees/:treeId', async (req, res) => {
    await deps.farms.removeTree(uid(req), parseId(req.params.farmId), parseId(req.params.treeId));
    res.status(204).end();
  });

  return r;
}
